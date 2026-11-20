/*
 * smoke-pdf.js — Bada CineVim の PDF ページ表示・編集を実ブラウザで通し確認
 *   node bada_cinevim/tools/smoke-pdf.js [--shots <dir>]      (Playwright / Chromium が必要)
 *
 * EXE や「index.html をダブルクリック」と同じ file:// で開き、
 *   PDF を開く → ページとして表示 (日本語の実 PDF) → マーカー / ペン / 日本語メモ →
 *   :w で PDF に保存 → 保存した PDF を検証 → テキスト表示と行き来 (注釈は保持) →
 *   VIM のキーがページ表示中は本文に漏れない → テキストファイルは :w でその場に上書き
 * を確認します。
 */
"use strict";
var path = require("path"), fs = require("fs"), os = require("os");
var { chromium } = require("playwright");
var APP = path.join(__dirname, "..");
var L = require(path.join(APP, "pdf", "pdf-lib.min.js"));
var Edit = require(path.join(APP, "pdf", "pdfedit.js"));

var shotDir = null, ai = process.argv.indexOf("--shots");
if (ai > 0) { shotDir = path.resolve(process.argv[ai + 1]); fs.mkdirSync(shotDir, { recursive: true }); }
var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }
async function keys(page, s){ for (var i = 0; i < s.length; i++) await page.keyboard.press(s[i]); }
function pv(page){
  return page.evaluate(function(){
    var c = window.BadaPdfView && window.BadaPdfView.current; if (!c) return null;
    var s = c.state;
    return { pages: s.pages.length, n: s.annots.length, types: s.annots.map(function(a){ return a.type; }).join(","),
             dirty: s.dirty, editable: s.editable, status: s.status, hits: s.hitCount };
  });
}

(async function(){
  var tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cinevim-pdf-"));
  var doc = await L.PDFDocument.create(), font = await doc.embedFont(L.StandardFonts.Helvetica);
  for (var i = 1; i <= 2; i++) doc.addPage([420, 560]).drawText("Knot theory page " + i + " Kauffman bracket", { x: 40, y: 500, size: 14, font: font });
  var pdfPath = path.join(tmp, "jones.pdf");
  fs.writeFileSync(pdfPath, await doc.save());
  var realPdf = path.join(APP, "..", "Bada#.pdf");

  var browser = await chromium.launch(), errors = [];
  var ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  await ctx.addInitScript(function(){ window.showOpenFilePicker = undefined; window.showSaveFilePicker = undefined; });
  var page = await ctx.newPage();
  page.on("pageerror", function(e){ errors.push(String(e)); });
  page.on("console", function(m){ if (m.type() === "error") errors.push(m.text()); });
  await page.goto("file://" + path.join(APP, "index.html"));

  /* ── PDF を開いていないとき ── */
  await page.click("#btnPages");
  ok(/PDF を開いていません/.test(await page.locator("#msg").textContent()), ":page without a PDF explains what to do");

  /* ── PDF を開く → ページ表示が出る ── */
  await page.setInputFiles("#fileIn", pdfPath);
  await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 60000 });
  var s = await pv(page);
  ok(s.pages === 2 && s.editable, "opening a PDF shows it as real, editable pages — " + JSON.stringify(s));
  ok(/jones\.txt/.test(await page.locator("#fname").textContent()), "the text of the PDF is also loaded into the VIM buffer underneath");
  var frame = await page.evaluate(function(){ var r = document.querySelector(".badapdf-overlay .cv-frame").getBoundingClientRect(); return r.width > 600 && r.height > 400 && getComputedStyle(document.querySelector(".badapdf-overlay")).position === "fixed"; });
  ok(frame, "the viewer frame is laid out (styles are self-contained in the standalone app)");

  /* VIM のキーが下の本文に漏れない */
  var before = await page.evaluate(function(){ return document.getElementById("pos").textContent; });
  await keys(page, "jjj"); await page.keyboard.press("x");
  ok(await page.evaluate(function(){ return document.getElementById("pos").textContent; }) === before, "keys typed in the page view do not reach the VIM buffer");

  /* マーカー / ペン / 日本語メモ */
  await keys(page, "gg");
  var box = await page.locator('.pv-page[data-i="0"] svg').boundingBox();
  await page.keyboard.press("m");
  await page.mouse.move(box.x + 50, box.y + 70); await page.mouse.down(); await page.mouse.move(box.x + 300, box.y + 100, { steps: 4 }); await page.mouse.up();
  await page.keyboard.press("p");
  await page.mouse.move(box.x + 60, box.y + 200); await page.mouse.down(); await page.mouse.move(box.x + 160, box.y + 260, { steps: 6 }); await page.mouse.up();
  await page.keyboard.press("i");
  await page.mouse.click(box.x + 80, box.y + 330);
  await page.waitForSelector(".pv-noteedit");
  await page.keyboard.insertText("量子メモ");
  await page.waitForFunction(function(){ return document.querySelector(".pv-noteedit").value === "量子メモ"; });
  await page.keyboard.press("Enter");
  s = await pv(page);
  ok(s.types === "highlight,ink,note" && s.dirty, "marker + pen + Japanese note added — " + s.types);
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "cinevim-pdf.png") });

  /* PDF 専用の編集ツール: ページを回転 → 文章ビューと行き来しても保たれ、u で戻せる */
  ok(await page.locator('.badapdf-overlay .pv-edit [data-tool="textedit"]').count() === 1, "the PDF edit toolbar (text correction / erase / pages / flatten) is available");
  await page.keyboard.press("R");
  await page.waitForFunction(function(){ var s = window.BadaPdfView.current.state; return !s.busy && s.pages.length === 2 && s.pages[0].page.rotate === 90; }, null, { timeout: 30000 });
  await page.keyboard.press("t");
  await page.waitForFunction(function(){ return !document.querySelector(".badapdf-overlay"); });
  await keys(page, ":page"); await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ var c = window.BadaPdfView && window.BadaPdfView.current; return c && !c.state.busy && c.state.pages.length === 2; }, null, { timeout: 60000 });
  ok(await page.evaluate(function(){ var s = window.BadaPdfView.current.state; return s.pages[0].page.rotate === 90 && s.annots.length === 3 && s.dirty; }), "a page rotation survives leaving and re-entering the page view");
  await page.evaluate(function(){ return window.BadaPdfView.current.rotatePage(); });
  await page.evaluate(function(){ return window.BadaPdfView.current.rotatePage(); });
  await page.evaluate(function(){ return window.BadaPdfView.current.rotatePage(); });
  await page.waitForFunction(function(){ var s = window.BadaPdfView.current.state; return !s.busy && s.pages.length === 2 && s.pages[0].page.rotate === 0; }, null, { timeout: 30000 });

  /* テキスト表示へ (注釈は捨てない) → VIM が効く → :page で続きから */
  await page.keyboard.press("t");
  await page.waitForFunction(function(){ return !document.querySelector(".badapdf-overlay"); });
  ok(/未保存/.test(await page.locator("#msg").textContent()), "leaving the page view keeps unsaved annotations and says so");
  await keys(page, "G");
  ok(await page.evaluate(function(){ return document.getElementById("pos").textContent; }) !== before, "back in the text view the VIM keys work again");
  await keys(page, ":page"); await page.keyboard.press("Enter");
  await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 60000 });
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.pages.length === 2; });
  s = await pv(page);
  ok(s.n === 3 && s.dirty, ":page reopens with the same 3 annotations still pending — " + JSON.stringify(s));

  /* :w → PDF に保存 (保存ダイアログの無い環境ではダウンロード) */
  var dl = page.waitForEvent("download");
  await keys(page, ":w"); await page.keyboard.press("Enter");
  var d = await dl, saved = new Uint8Array(fs.readFileSync(await d.path()));
  var back = await Edit.extractAnnotations(L, saved);
  ok(d.suggestedFilename() === "jones.pdf" && back.annots.length === 3, ":w saves a PDF containing the 3 annotations — " + back.annots.map(function(a){ return a.type; }).join(","));
  ok(back.annots[2].text === "量子メモ", "the Japanese note is stored as Unicode");
  await page.waitForFunction(function(){ return !window.BadaPdfView.current.state.dirty; });
  await keys(page, ":q"); await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ return !document.querySelector(".badapdf-overlay"); });
  ok(/文章ビューに戻りました/.test(await page.locator("#msg").textContent()), ":q returns to the text view");

  /* 保存した PDF を開き直すと、注釈を編集できる形で復元する */
  var savedPath = path.join(tmp, "saved.pdf"); fs.writeFileSync(savedPath, saved);
  await page.setInputFiles("#fileIn", savedPath);
  await page.waitForFunction(function(){ var c = window.BadaPdfView && window.BadaPdfView.current; return c && c.state.pages.length === 2 && c.state.annots.length === 3; }, null, { timeout: 60000 });
  s = await pv(page);
  ok(s.n === 3 && !s.dirty, "re-opening the saved PDF restores its annotations for further editing");
  await keys(page, ":q"); await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ return !document.querySelector(".badapdf-overlay"); });

  /* 日本語の実 PDF (フォント非埋め込み) がページとして描画される */
  if (fs.existsSync(realPdf)) {
    await page.setInputFiles("#fileIn", realPdf);
    await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 60000 });
    await page.waitForFunction(function(){ return window.BadaPdfView.current.state.pages.length === 22; }, null, { timeout: 60000 });
    await page.waitForTimeout(700);
    var dark = await page.evaluate(function(){
      var c = document.querySelector('.pv-page[data-i="0"] canvas'), d = c.getContext("2d").getImageData(0, Math.floor(c.height * 0.45), c.width, Math.floor(c.height * 0.4)).data, n = 0;
      for (var i = 0; i < d.length; i += 4) if (d[i] < 120) n++;
      return n;
    });
    ok(dark > 5000, "real Japanese paper renders as pages over file:// — dark px " + dark);
    if (shotDir) await page.screenshot({ path: path.join(shotDir, "cinevim-real.png") });
    await keys(page, ":q"); await page.keyboard.press("Enter");
    await page.waitForFunction(function(){ return !document.querySelector(".badapdf-overlay"); });
  }
  await ctx.close();

  /* ── 保存ダイアログ / ファイルハンドルのある環境: PDF は選んだ先へ、テキストはその場に上書き ── */
  var ctx2 = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  var srv = require("http").createServer(function(req, res){
    var f = path.join(APP, decodeURIComponent(req.url.split("?")[0]));
    if (!f.startsWith(APP) || !fs.existsSync(f) || fs.statSync(f).isDirectory()){ res.writeHead(404); res.end(); return; }
    res.writeHead(200, { "Content-Type": /\.html$/.test(f) ? "text/html; charset=utf-8" : "text/javascript; charset=utf-8" });
    fs.createReadStream(f).pipe(res);
  });
  await new Promise(function(r){ srv.listen(0, "127.0.0.1", r); });
  await ctx2.addInitScript(function(){
    /* OPFS のファイルで File System Access API のダイアログを代用する */
    async function dir(){ return (await navigator.storage.getDirectory()).getDirectoryHandle("cv", { create: true }); }
    window.showOpenFilePicker = async function(){ return [await (await dir()).getFileHandle("memo.txt")]; };
    window.showSaveFilePicker = async function(o){ window.__saveAsked = (window.__saveAsked || 0) + 1; return (await dir()).getFileHandle(o.suggestedName, { create: true }); };
  });
  var p2 = await ctx2.newPage();
  p2.on("pageerror", function(e){ errors.push(String(e)); });
  await p2.goto("http://127.0.0.1:" + srv.address().port + "/index.html");
  await p2.evaluate(async function(){
    var d = await (await navigator.storage.getDirectory()).getDirectoryHandle("cv", { create: true });
    var h = await d.getFileHandle("memo.txt", { create: true }), w = await h.createWritable(); await w.write("first line\n"); await w.close();
  });
  await p2.click("#btnOpen");
  await p2.waitForFunction(function(){ return /memo\.txt/.test(document.getElementById("fname").textContent); });
  await keys(p2, "A"); await p2.keyboard.type(" edited"); await p2.keyboard.press("Escape");
  await keys(p2, ":w"); await p2.keyboard.press("Enter");
  await p2.waitForFunction(function(){ return /上書き保存しました/.test(document.getElementById("msg").textContent); });
  var memo = await p2.evaluate(async function(){ var d = await (await navigator.storage.getDirectory()).getDirectoryHandle("cv"); return (await (await d.getFileHandle("memo.txt")).getFile()).text(); });
  ok(memo === "first line edited\n", ":w overwrites the opened text file in place — " + JSON.stringify(memo));

  await p2.setInputFiles("#fileIn", pdfPath);
  await p2.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 60000 });
  await p2.evaluate(function(){ window.BadaPdfView.current.addAnnot({ type: "note", page: 1, x: 60, y: 300, text: "saved via dialog" }); });
  for (var r = 0; r < 2; r++) {
    await keys(p2, ":w"); await p2.keyboard.press("Enter");
    await p2.waitForFunction(function(){ var st = window.BadaPdfView.current.state; return !st.dirty && /保存しました/.test(st.status); });
    if (r === 0) await p2.evaluate(function(){ window.BadaPdfView.current.addAnnot({ type: "highlight", page: 0, rects: [[40, 490, 200, 515]] }); });
  }
  var out = await p2.evaluate(async function(){
    var d = await (await navigator.storage.getDirectory()).getDirectoryHandle("cv");
    return { bytes: Array.from(new Uint8Array(await (await (await d.getFileHandle("jones.pdf")).getFile()).arrayBuffer())), asked: window.__saveAsked };
  });
  var b2 = await Edit.extractAnnotations(L, new Uint8Array(out.bytes));
  ok(b2.annots.length === 2 && out.asked === 1, "PDF saved to the chosen file; the save dialog is asked once, later saves reuse it — annots " + b2.annots.length + ", asked " + out.asked);
  await ctx2.close(); srv.close();

  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  ok(errors.length === 0, "no page errors — " + (errors.slice(0, 3).join(" | ") || "none"));
  console.log(failed ? ("\n" + failed + " CHECK(S) FAILED") : "\nALL CINEVIM PDF SMOKE CHECKS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
