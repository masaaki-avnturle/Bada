/*
 * test-electron-ipc.js — EXE (Electron メインプロセス) の IPC ハンドラの自己検査
 *   node sourcetree_search/tools/test-electron-ipc.js
 *
 * Electron 本体は起動せず、electron モジュールを差し替えて main.js を読み込み、
 * 登録された IPC ハンドラを直接呼びます。索引 → PDF の読み出し → 注釈入り PDF の保存
 * (.bak 退避・索引更新) → テキスト保存、そして「索引フォルダの外には書けない」ことを検証。
 */
"use strict";
var Module = require("module"), path = require("path"), fs = require("fs"), os = require("os");
var ROOT = path.join(__dirname, "..");
var handlers = {};
var fakeElectron = {
  app: { isPackaged: false, whenReady: function(){ return new Promise(function(){}); }, on: function(){}, quit: function(){} },
  BrowserWindow: function(){}, dialog: {}, shell: {},
  ipcMain: { handle: function(name, fn){ handlers[name] = fn; } }
};
var origLoad = Module._load;
Module._load = function(request, parent, isMain){
  if (request === "electron") return fakeElectron;
  /* ビルド時は core/ が electron/ の中へコピーされる。テストではリポジトリの core/ を使う */
  if (/[\\/]electron[\\/]core[\\/]searchcore\.js$/.test(request)) return origLoad(path.join(ROOT, "core", "searchcore.js"), parent, isMain);
  return origLoad(request, parent, isMain);
};
require(path.join(ROOT, "app", "electron", "main.js"));
Module._load = origLoad;

var L = require(path.join(ROOT, "app", "www", "vendor", "pdf-lib", "pdf-lib.min.js"));
var Edit = require(path.join(ROOT, "app", "www", "pdfedit.js"));
var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }
function call(name){ return Promise.resolve(handlers[name].apply(null, [{}].concat([].slice.call(arguments, 1)))); }

(async function(){
  var tmp = fs.mkdtempSync(path.join(os.tmpdir(), "badasearch-ipc-"));
  var repo = path.join(tmp, "repo"), outside = path.join(tmp, "outside.txt");
  fs.mkdirSync(path.join(repo, "paper"), { recursive: true });
  var doc = await L.PDFDocument.create(), font = await doc.embedFont(L.StandardFonts.Helvetica);
  doc.addPage([300, 300]).drawText("Kauffman bracket", { x: 20, y: 250, size: 14, font: font });
  var pdfPath = path.join(repo, "paper", "jones.pdf"), original = Buffer.from(await doc.save());
  fs.writeFileSync(pdfPath, original);
  var src = path.join(repo, "a.py");
  fs.writeFileSync(src, "x = 1\n");
  fs.writeFileSync(outside, "keep");

  ok((await call("file-bytes", pdfPath)).error, "file-bytes refuses before anything is indexed");
  var info = await call("build-index", repo);
  ok(info.files === 2, "build-index indexes the PDF and the source — " + info.files);

  var ft = await call("file-text", pdfPath);
  ok(ft.readonly === true && ft.lang === "PDF", "PDF text is read-only (it is edited on the page view)");
  var fb = await call("file-bytes", pdfPath);
  ok(fb.bytes instanceof Uint8Array && Buffer.from(fb.bytes).equals(original), "file-bytes returns the PDF bytes for the viewer");

  var edited = await Edit.applyAnnotations(L, fb.bytes, [{ type: "note", page: 0, x: 30, y: 200, text: "量子メモ", size: 12 }]);
  var sv = await call("save-bytes", pdfPath, edited);
  ok(sv.ok === true && /jones\.pdf\.bak/.test(sv.note), "save-bytes writes the PDF and reports the backup — " + JSON.stringify(sv));
  ok(fs.readFileSync(pdfPath + ".bak").equals(original), ".bak keeps the untouched original");
  ok(Buffer.from(edited).equals(fs.readFileSync(pdfPath)) && !fs.existsSync(pdfPath + ".badatmp"), "PDF replaced atomically (no temp file left)");
  var hit = await call("search", "量子メモ", {});
  ok(hit.total === 1 && hit.hits[0].rel === "paper/jones.pdf", "the saved note is searchable without re-indexing");

  var edited2 = await Edit.applyAnnotations(L, edited, []);
  await call("save-bytes", pdfPath, edited2);
  ok(fs.readFileSync(pdfPath + ".bak").equals(original), "a second save never overwrites the first backup");
  ok((await call("search", "量子メモ", {})).total === 0, "removing the note removes it from search");

  ok((await call("save-bytes", pdfPath, new Uint8Array([1, 2, 3]))).error, "save-bytes rejects data that is not a PDF");
  ok((await call("save-bytes", src, edited)).error, "save-bytes rejects non-PDF targets");
  ok((await call("save-bytes", path.join(tmp, "evil.pdf"), edited)).error && !fs.existsSync(path.join(tmp, "evil.pdf")), "save-bytes cannot write outside the indexed folder");
  ok((await call("save-bytes", path.join(repo, "..", "evil2.pdf"), edited)).error && !fs.existsSync(path.join(tmp, "evil2.pdf")), "save-bytes rejects ../ traversal");

  ok((await call("save-file", src, "x = 2\ny = zeta\n")).ok === true && fs.readFileSync(src, "utf8") === "x = 2\ny = zeta\n", "save-file writes the edited source");
  ok((await call("search", "zeta", {})).total === 1, "the edit is searchable without re-indexing");
  ok((await call("save-file", outside, "pwned")).error && fs.readFileSync(outside, "utf8") === "keep", "save-file cannot write outside the indexed folder");
  ok((await call("save-file", pdfPath, "text")).error, "save-file refuses to overwrite a PDF with text");
  ok((await call("file-bytes", outside)).error, "file-bytes cannot read outside the indexed folder");

  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(failed ? ("\n" + failed + " TEST(S) FAILED") : "\nALL ELECTRON IPC TESTS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
