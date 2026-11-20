/*
 * smoke-pdftools.js — PDF 専用の編集ツールを実ブラウザで通し確認
 *   node sourcetree_search/tools/smoke-pdftools.js [--shots <dir>]     (Playwright / Chromium が必要)
 *
 * ✏ 文字修正 (既存の文字の書き換え・文字の追加・再編集) / ⬜ 消去 /
 * ページの回転・並べ替え・空白ページ・削除・別 PDF の結合 / 📌 焼き込み / u での取り消し
 * を操作し、:w で保存した PDF を別実装 (pdf.js) で読んで結果を検証します。
 */
"use strict";
var path = require("path"), fs = require("fs"), os = require("os");
var { chromium } = require("playwright");
var WWW = path.join(__dirname, "..", "app", "www");
var L = require(path.join(WWW, "vendor", "pdf-lib", "pdf-lib.min.js"));
var Edit = require(path.join(WWW, "pdfedit.js"));
var pdfjs = require(path.join(WWW, "vendor", "pdfjs", "pdf.min.js"));
pdfjs.GlobalWorkerOptions.workerSrc = path.join(WWW, "vendor", "pdfjs", "pdf.worker.min.js");

var shotDir = null, ai = process.argv.indexOf("--shots");
if (ai > 0) { shotDir = path.resolve(process.argv[ai + 1]); fs.mkdirSync(shotDir, { recursive: true }); }
var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }
async function keys(page, s){ for (var i = 0; i < s.length; i++) await page.keyboard.press(s[i]); }
function st(page){
  return page.evaluate(function(){
    var s = window.BadaPdfView.current.state;
    return { pages: s.pages.length, cur: s.cur, dirty: s.dirty, busy: s.busy, status: s.status, tool: s.tool,
             annots: s.annots.map(function(a){ return a.type + "@" + a.page; }).join(","),
             rot: s.pages.map(function(P){ return P.page.rotate; }).join(",") };
  });
}
function idle(page){ return page.waitForFunction(function(){ var s = window.BadaPdfView.current.state; return !s.busy && s.pages.length > 0 && s.pages.length === s.pdf.numPages; }, null, { timeout: 30000 }); }
/* ページ i の文字 needle の画面上の中心座標 */
function locate(page, i, needle){
  return page.evaluate(async function(a){
    var P = window.BadaPdfView.current.state.pages[a.i], tc = await P.page.getTextContent();
    var it = tc.items.filter(function(x){ return x.str.indexOf(a.needle) >= 0; })[0];
    if (!it) return null;
    var v = P.viewport.convertToViewportPoint(it.transform[4] + it.width / 2, it.transform[5] + it.height * 0.3), r = P.svg.getBoundingClientRect();
    return { x: r.left + v[0], y: r.top + v[1], str: it.str };
  }, { i: i, needle: needle });
}
async function readPdf(bytes){
  var pdf = await pdfjs.getDocument({ data: new Uint8Array(bytes), isEvalSupported: false, verbosity: 0 }).promise, out = [];
  for (var i = 1; i <= pdf.numPages; i++){
    var pg = await pdf.getPage(i), tc = await pg.getTextContent();
    out.push({ text: tc.items.map(function(x){ return x.str; }).join(" "), rotate: pg.rotate, annots: (await pg.getAnnotations()).length });
  }
  await pdf.destroy();
  return out;
}

(async function(){
  var tmp = fs.mkdtempSync(path.join(os.tmpdir(), "badasearch-tools-")), repo = path.join(tmp, "repo");
  fs.mkdirSync(repo);
  var doc = await L.PDFDocument.create(), font = await doc.embedFont(L.StandardFonts.TimesRoman);
  ["AAA", "BBB", "CCC"].forEach(function(t){
    var pg = doc.addPage([420, 560]);
    pg.drawText("Section " + t, { x: 40, y: 500, size: 18, font: font });
    pg.drawText("The Kauffman bracket gives the Jones polynomial.", { x: 40, y: 460, size: 12, font: font });
  });
  fs.writeFileSync(path.join(repo, "paper.pdf"), await doc.save());
  var extra = await L.PDFDocument.create(), f2 = await extra.embedFont(L.StandardFonts.Helvetica);
  extra.addPage([420, 560]).drawText("Appendix ZZZ", { x: 40, y: 500, size: 18, font: f2 });
  var extraPath = path.join(tmp, "appendix.pdf");
  fs.writeFileSync(extraPath, await extra.save());

  var browser = await chromium.launch(), errors = [];
  var ctx = await browser.newContext({ viewport: { width: 1280, height: 940 }, acceptDownloads: true });
  await ctx.addInitScript(function(){ window.showDirectoryPicker = undefined; });
  var page = await ctx.newPage();
  page.on("pageerror", function(e){ errors.push(String(e)); });
  page.on("console", function(m){ if (m.type() === "error") errors.push(m.text()); });
  await page.goto("file://" + path.join(WWW, "complete.html"));
  await page.setInputFiles("#filepick", repo);
  await page.waitForFunction(function(){ return /索引完了/.test(document.getElementById("status").textContent); });
  await page.fill("#q", "Kauffman"); await page.press("#q", "Escape"); await page.press("#q", "Enter");
  await page.locator("button[data-cine]").first().click();
  await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 30000 });
  await idle(page);
  await keys(page, "gg");
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.cur === 0; });
  ok(await page.locator('.badapdf-overlay .pv-edit [data-tool="textedit"]').count() === 1 &&
     await page.locator('.badapdf-overlay .pv-edit [data-act="flatten"]').count() === 1, "the dedicated PDF edit toolbar is shown");

  /* ── ✏ 文字修正: 既存の文字を書き換える ── */
  await keys(page, ":text"); await page.keyboard.press("Enter");
  var at = await locate(page, 0, "Kauffman");
  await page.mouse.click(at.x, at.y);
  await page.waitForSelector(".pv-noteedit");
  ok(await page.locator(".pv-noteedit").inputValue() === at.str, "clicking a word opens its text for editing — " + JSON.stringify(at.str));
  await page.keyboard.insertText("The Alexander polynomial is older.");
  await page.waitForFunction(function(){ return document.querySelector(".pv-noteedit").value === "The Alexander polynomial is older."; });
  await page.keyboard.press("Enter");
  var s = await st(page);
  ok(s.annots === "textedit@0" && s.dirty, "the original text is replaced (text edit recorded) — " + s.annots);
  var model = await page.evaluate(function(){ return window.BadaPdfView.current.state.annots[0]; });
  ok(model.cover && model.font === "serif" && Math.abs(model.size - 12) < 1.5 && model.bg === "#ffffff", "replacement keeps position, size and serif face, and covers the old text with the page colour — size " + model.size + " font " + model.font + " bg " + model.bg);

  /* 変えずに確定 → 何も起きない */
  var at2 = await locate(page, 0, "Section");
  await page.mouse.click(at2.x, at2.y);
  await page.waitForSelector(".pv-noteedit");
  await page.keyboard.press("Enter");
  ok((await st(page)).annots === "textedit@0", "confirming without a change edits nothing");

  /* 何もない所 → 文字を追加 (日本語) */
  var box = await page.locator('.pv-page[data-i="0"] svg').boundingBox();
  await page.mouse.click(box.x + 120, box.y + 420);
  await page.waitForSelector(".pv-noteedit");
  await page.keyboard.insertText("追記: 量子群との関係");
  await page.waitForFunction(function(){ return document.querySelector(".pv-noteedit").value.indexOf("量子群") > 0; });
  await page.keyboard.press("Enter");
  ok((await st(page)).annots === "textedit@0,textedit@0", "clicking empty space adds new text");

  /* 再編集 (選択ツールでダブルクリック) */
  await page.keyboard.press("v");
  await page.locator(".pv-a.pv-textedit").first().dblclick();
  await page.waitForSelector(".pv-noteedit");
  await page.keyboard.insertText("The Alexander polynomial (1923).");
  await page.waitForFunction(function(){ return document.querySelector(".pv-noteedit").value === "The Alexander polynomial (1923)."; });
  await page.keyboard.press("Enter");
  ok(await page.evaluate(function(){ return window.BadaPdfView.current.state.annots[0].text; }) === "The Alexander polynomial (1923).", "double-click re-edits a corrected text");

  /* ── ⬜ 消去 ── */
  await keys(page, ":erase"); await page.keyboard.press("Enter");
  var sec = await locate(page, 0, "Section");
  await page.mouse.move(sec.x - 60, sec.y - 16); await page.mouse.down(); await page.mouse.move(sec.x + 70, sec.y + 12, { steps: 4 }); await page.mouse.up();
  s = await st(page);
  ok(s.annots === "textedit@0,textedit@0,erase@0", "erase tool blanks out a region — " + s.annots);
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "tools-1-textedit.png") });

  /* ── ページ操作 ── */
  await page.keyboard.press("v");
  await page.keyboard.press("R"); await idle(page);
  s = await st(page);
  ok(s.rot === "90,0,0" && s.cur === 0, "R rotates the current page — " + s.rot);
  await page.keyboard.press("u"); await idle(page);
  ok((await st(page)).rot === "0,0,0", "u undoes the rotation");
  await page.keyboard.press(">"); await idle(page);
  s = await st(page);
  ok(s.annots === "textedit@1,textedit@1,erase@1" && s.cur === 1, "> moves the page back by one and its edits travel with it — " + s.annots);
  await keys(page, ":blank"); await page.keyboard.press("Enter"); await idle(page);
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.pages.length === 4; });
  s = await st(page);
  ok(s.pages === 4 && s.cur === 2, ":blank inserts a blank page after the current one — pages " + s.pages + " cur " + s.cur);
  await keys(page, ":delpage"); await page.keyboard.press("Enter");
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.pages.length === 3; }); await idle(page);
  ok((await st(page)).pages === 3, ":delpage deletes the current (blank) page");
  await page.setInputFiles(".badapdf-overlay .pv-mergein", extraPath); 
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.pages.length === 4; }, null, { timeout: 30000 });
  await idle(page);
  s = await st(page);
  ok(s.pages === 4 && s.cur === 3 && /結合/.test(s.status), "📎 merges another PDF at the end and jumps to it — " + s.status);
  await keys(page, ":move 1"); await page.keyboard.press("Enter"); await idle(page);
  await page.waitForFunction(function(){ return /移動しました/.test(window.BadaPdfView.current.state.status); });
  s = await st(page);
  ok(s.cur === 0 && s.annots === "textedit@2,textedit@2,erase@2", ":move 1 brings the appendix to the front; edits shift accordingly — " + s.annots);
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "tools-2-pages.png") });

  /* ── 📌 焼き込み (取り消せる) ── */
  await page.keyboard.press("F"); await idle(page);
  await page.waitForFunction(function(){ return /焼き込みました/.test(window.BadaPdfView.current.state.status); });
  ok((await st(page)).annots === "", "F flattens the edits into the pages (no annotations left)");
  await page.keyboard.press("u"); await idle(page);
  ok((await st(page)).annots === "textedit@2,textedit@2,erase@2", "u undoes the flatten and the edits are editable again");
  await page.keyboard.press("F"); await idle(page);
  await page.waitForFunction(function(){ return /焼き込みました/.test(window.BadaPdfView.current.state.status); });

  /* ── 保存して中身を検証 ── */
  var dl = page.waitForEvent("download");
  await keys(page, ":w"); await page.keyboard.press("Enter");
  var saved = new Uint8Array(fs.readFileSync(await (await dl).path()));
  var out = await readPdf(saved);
  ok(out.length === 4, "saved PDF has 4 pages");
  ok(/Appendix ZZZ/.test(out[0].text) && /BBB/.test(out[1].text) && /CCC/.test(out[3].text), "page order is appendix, BBB, (edited AAA), CCC");
  ok(/The Alexander polynomial \(1923\)\./.test(out[2].text), "the corrected sentence is part of the page — " + JSON.stringify(out[2].text.slice(0, 90)));
  ok(out.every(function(p){ return p.annots === 0; }) && !Edit.hasMarker(saved), "flattened: the saved PDF contains no annotations");
  ok(out.every(function(p){ return p.rotate === 0; }), "the undone rotation was not saved");

  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  ok(errors.length === 0, "no page errors — " + (errors.slice(0, 3).join(" | ") || "none"));
  console.log(failed ? ("\n" + failed + " CHECK(S) FAILED") : "\nALL PDF TOOL SMOKE CHECKS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
