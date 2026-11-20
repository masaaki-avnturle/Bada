/*
 * smoke-electron.js — EXE と同じ構成 (Electron 実機) での通し確認
 *   xvfb-run -a node sourcetree_search/tools/smoke-electron.js <electron 実行ファイル> [--shots <dir>]
 *
 * CI と同じ手順で core/ と www/ を electron/ に組み込んだアプリを一時フォルダに作り、
 * SourceTree のカスタム操作と同じく「リポジトリのパス」を引数にして起動します。
 * 索引 → 検索 → PDF をページ表示 (日本語 PDF の描画込み) → マーカー → :w で上書き保存
 * (.bak 退避) → ソースを CineVim で編集して :w、までを実ファイルで検証します。
 */
"use strict";
var path = require("path"), fs = require("fs"), os = require("os");
var { _electron } = require("playwright");
var ROOT = path.join(__dirname, "..");
var L = require(path.join(ROOT, "app", "www", "vendor", "pdf-lib", "pdf-lib.min.js"));
var Edit = require(path.join(ROOT, "app", "www", "pdfedit.js"));
var exe = process.argv[2];
if (!exe || !fs.existsSync(exe)) { console.error("usage: node smoke-electron.js <path to electron binary> [--shots dir]"); process.exit(1); }
var shotDir = null, ai = process.argv.indexOf("--shots");
if (ai > 0) { shotDir = path.resolve(process.argv[ai + 1]); fs.mkdirSync(shotDir, { recursive: true }); }

var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }

(async function(){
  var tmp = fs.mkdtempSync(path.join(os.tmpdir(), "badasearch-el-"));
  var appDir = path.join(tmp, "app"), repo = path.join(tmp, "repo");
  fs.cpSync(path.join(ROOT, "app", "electron"), appDir, { recursive: true, filter: function(p){ return !/node_modules|[\\/]dist$/.test(p); } });
  fs.cpSync(path.join(ROOT, "core"), path.join(appDir, "core"), { recursive: true });
  fs.cpSync(path.join(ROOT, "app", "www"), path.join(appDir, "www"), { recursive: true });
  fs.mkdirSync(path.join(repo, "src"), { recursive: true });
  var real = path.join(ROOT, "..", "Bada#.pdf"), pdfPath = path.join(repo, "paper.pdf");
  fs.copyFileSync(real, pdfPath);
  var original = fs.readFileSync(pdfPath);
  var srcPath = path.join(repo, "src", "tuple.py");
  fs.writeFileSync(srcPath, "class TupleSpace:\n    pass\n");

  var app = await _electron.launch({ executablePath: exe, args: [appDir, "--no-sandbox", repo] });
  var page = await app.firstWindow();
  var errors = [];
  page.on("pageerror", function(e){ errors.push(String(e)); });
  page.on("console", function(m){ if (m.type() === "error") errors.push(m.text()); });
  await page.waitForFunction(function(){ return /索引完了/.test(document.getElementById("status").textContent); }, null, { timeout: 60000 });
  ok(/2 ファイル/.test(await page.locator("#status").textContent()), "started with the repo path argument ($REPO) and indexed it");

  await page.fill("#q", "TupleSpace"); await page.press("#q", "Escape"); await page.press("#q", "Enter");
  await page.waitForFunction(function(){ return document.getElementById("status").textContent.indexOf("「TupleSpace」") >= 0; });
  await page.locator('.rfile:has(.rel:has-text("paper.pdf")) button[data-cine]').click();
  await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 60000 });
  await page.waitForFunction(function(){ return /箇所/.test(window.BadaPdfView.current.state.status); }, null, { timeout: 60000 });
  var s = await page.evaluate(function(){ var st = window.BadaPdfView.current.state; return { pages: st.pages.length, hits: st.hitCount, editable: st.editable, cur: st.cur }; });
  ok(s.pages === 22 && s.hits > 10 && s.editable, "real paper opens as 22 editable pages with hits located — " + JSON.stringify(s));
  /* 日本語本文 (非埋め込み CID フォント) が描画されている = 同梱 CMap が EXE で読めている */
  await page.waitForTimeout(600);
  var dark = await page.evaluate(function(){
    var c = document.querySelector('.pv-page[data-i="0"] canvas'), d = c.getContext("2d").getImageData(0, Math.floor(c.height * 0.45), c.width, Math.floor(c.height * 0.4)).data, n = 0;
    for (var i = 0; i < d.length; i += 4) if (d[i] < 120) n++;
    return n;
  });
  ok(dark > 5000, "Japanese body text is rendered in the EXE (bundled CMaps load over file://) — dark px " + dark);
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "electron-pdf.png") });

  await page.keyboard.press("M");
  await page.keyboard.press(":"); await page.keyboard.type("w"); await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ return /保存しました/.test(window.BadaPdfView.current.state.status); }, null, { timeout: 60000 });
  ok(/paper\.pdf\.bak/.test(await page.evaluate(function(){ return window.BadaPdfView.current.state.status; })), "status reports the .bak backup");
  ok(fs.existsSync(pdfPath + ".bak") && fs.readFileSync(pdfPath + ".bak").equals(original), "original PDF kept as paper.pdf.bak on disk");
  var back = await Edit.extractAnnotations(L, new Uint8Array(fs.readFileSync(pdfPath)));
  ok(back.annots.length === 1 && back.annots[0].type === "highlight" && back.annots[0].rects.length >= 1, ":w wrote the marker into the PDF on disk");
  await page.keyboard.press(":"); await page.keyboard.type("q"); await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ return !document.querySelector(".badapdf-overlay"); });

  await page.locator('.rfile:has(.rel:has-text("tuple.py")) button[data-cine]').click();
  await page.waitForSelector(".cinevim-overlay .cv-text");
  for (var k of ["G", "o"]) await page.keyboard.press(k);
  await page.keyboard.type("    # edited in the EXE");
  await page.keyboard.press("Escape");
  for (var k2 of [":", "w", "q"]) await page.keyboard.press(k2);
  await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ return !document.querySelector(".cinevim-overlay"); });
  /* 末尾改行のあるファイルは最後に空行があるので、G o はその下に行を開く (Vim と同じ) */
  ok(fs.readFileSync(srcPath, "utf8") === "class TupleSpace:\n    pass\n\n    # edited in the EXE", ":wq wrote the edited source to disk — " + JSON.stringify(fs.readFileSync(srcPath, "utf8")));

  await app.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  ok(errors.length === 0, "no renderer errors — " + (errors.slice(0, 3).join(" | ") || "none"));
  console.log(failed ? ("\n" + failed + " CHECK(S) FAILED") : "\nALL ELECTRON SMOKE CHECKS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
