/*
 * test-pdfedit.js — BadaCineVim PDF 編集エンジン (pdfedit.js) の自己検査
 *   node sourcetree_search/tools/test-pdfedit.js
 *
 * 同梱の pdf-lib で PDF を作り、注釈 (マーカー / ペン / メモ) を書き込んで、
 *   ・読み戻しが無損失であること (再編集できる)
 *   ・別実装の PDF リーダー (同梱の pdf.js) が標準の注釈として認識すること
 *   ・検索エンジン (searchcore) がメモを索引し、外観ストリームを本文と誤認しないこと
 *   ・実在の PDF (リポジトリの Bada#.pdf) でも壊さず往復できること
 * を検証します。
 */
"use strict";
var path = require("path"), fs = require("fs");
var WWW = path.join(__dirname, "..", "app", "www");
var L = require(path.join(WWW, "vendor", "pdf-lib", "pdf-lib.min.js"));
var Edit = require(path.join(WWW, "pdfedit.js"));
var Core = require(path.join(__dirname, "..", "core", "searchcore.js"));
var pdfjs = require(path.join(WWW, "vendor", "pdfjs", "pdf.min.js"));
pdfjs.GlobalWorkerOptions.workerSrc = path.join(WWW, "vendor", "pdfjs", "pdf.worker.min.js");

var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }
function near(a, b){ return Math.abs(a - b) < 0.02; }

async function makePdf(){
  var doc = await L.PDFDocument.create();
  var font = await doc.embedFont(L.StandardFonts.Helvetica);
  var p1 = doc.addPage([400, 300]);
  p1.drawText("Jones polynomial via the Kauffman bracket", { x: 30, y: 250, size: 14, font: font });
  var p2 = doc.addPage([400, 300]);
  p2.drawText("Second page about quantum knots", { x: 30, y: 250, size: 14, font: font });
  return doc.save();
}
async function annotsOf(bytes){
  var pdf = await pdfjs.getDocument({ data: new Uint8Array(bytes), isEvalSupported: false, verbosity: 0 }).promise;
  var out = [];
  for (var i = 1; i <= pdf.numPages; i++){
    var list = await (await pdf.getPage(i)).getAnnotations();
    out.push(list);
  }
  await pdf.destroy();
  return out;
}

(async function(){
  var base = await makePdf();
  ok(!Edit.hasMarker(base), "a fresh PDF has no BadaCineVim marker");

  var annots = [
    { type: "highlight", page: 0, rects: [[30, 245, 150, 262]], color: "#ffe14a" },
    { type: "ink", page: 0, paths: [[40, 100, 80, 140, 120, 100]], color: "#ff3b5c", width: 2 },
    { type: "note", page: 0, x: 200, y: 200, text: "check this (bracket)", size: 12, color: "#102030" },
    { type: "note", page: 1, x: 60, y: 180, text: "量子メモ\n二行目", size: 12, color: "#102030" }
  ];
  var saved = await Edit.applyAnnotations(L, base, annots);
  ok(saved instanceof Uint8Array && String.fromCharCode.apply(null, saved.slice(0, 5)) === "%PDF-", "applyAnnotations returns a PDF");
  ok(Edit.hasMarker(saved), "saved PDF carries the BadaCineVim marker (plain, not in an object stream)");

  /* ── 無損失の読み戻し ── */
  var back = await Edit.extractAnnotations(L, saved);
  ok(back.annots.length === 4, "extractAnnotations reads all 4 annotations back — got " + back.annots.length);
  ok(JSON.stringify(back.annots) === JSON.stringify(annots.map(Edit.normalize)), "round-trip is lossless (same model, same order, same pages)");
  ok(!Edit.hasMarker(back.bytes), "stripped base no longer contains BadaCineVim annotations");
  var base2 = await annotsOf(back.bytes);
  ok(base2[0].length === 0 && base2[1].length === 0, "stripped base has no annotations at all");

  /* ── 別実装 (pdf.js) が標準注釈として認識 ── */
  var seen = await annotsOf(saved);
  var sub0 = seen[0].map(function(a){ return a.subtype; }).sort().join(",");
  ok(sub0 === "FreeText,Highlight,Ink", "page 1 has Highlight + Ink + FreeText as standard annotations — got " + sub0);
  ok(seen[1].length === 1 && seen[1][0].subtype === "FreeText", "page 2 has the Japanese FreeText note");
  var hl = seen[0].filter(function(a){ return a.subtype === "Highlight"; })[0];
  ok(near(hl.rect[0], 30) && near(hl.rect[1], 245) && near(hl.rect[2], 150) && near(hl.rect[3], 262), "highlight /Rect matches the model");
  ok(hl.hasAppearance === true, "highlight has an appearance stream (renders in other viewers)");
  var jp = seen[1][0];
  ok(jp.contentsObj && jp.contentsObj.str === "量子メモ\n二行目", "Japanese note /Contents survives as Unicode — got " + JSON.stringify(jp.contentsObj && jp.contentsObj.str));
  ok(seen[0].every(function(a){ return a.titleObj && a.titleObj.str === "BadaCineVim"; }), "every annotation is tagged /T (BadaCineVim)");

  /* ── 再保存しても重複しない (常に全置換) ── */
  var again = await Edit.applyAnnotations(L, saved, annots.slice(0, 2));
  var seen2 = await annotsOf(again);
  ok(seen2[0].length === 2 && seen2[1].length === 0, "re-saving replaces, never duplicates (2 kept, notes removed)");
  var cleared = await Edit.applyAnnotations(L, saved, []);
  ok(!Edit.hasMarker(cleared), "saving with no annotations removes them all");

  /* ── 検索エンジンとの連携 ── */
  var text = Core.extractPdfText(Buffer.from(saved));
  ok(/Kauffman bracket/.test(text) && /quantum knots/.test(text), "original body text is still extracted after editing");
  ok(text.indexOf("〔注釈〕 量子メモ") >= 0 && text.indexOf("〔注釈〕 二行目") >= 0, "Japanese note is indexed as 〔注釈〕 lines");
  ok(text.indexOf("〔注釈〕 check this (bracket)") >= 0, "ASCII note (with parentheses) is indexed");
  ok((text.match(/check this/g) || []).length === 1, "note text is indexed once (appearance stream is not double-counted)");
  ok(text.indexOf("BadaCineVim") < 0 && !/\{"type"/.test(text), "internal marker / model JSON do not leak into the index");
  var idx = { files: [{ path: "p.pdf", rel: "p.pdf", lang: "PDF", lines: text.split("\n") }] };
  ok(Core.search(idx, "量子メモ", {}).total === 1, "the note is searchable through searchcore.search");

  /* ── 不正な入力は書き込まない ── */
  ok(Edit.normalize({ type: "note", page: 0, x: 1, y: 2, text: "   " }) === null, "empty note is rejected");
  ok(Edit.normalize({ type: "highlight", page: 0, rects: [[1, 2, NaN, 4]] }) === null, "highlight with NaN is rejected");
  ok(Edit.normalize({ type: "bogus" }) === null && Edit.normalize(null) === null, "unknown / null annotations are rejected");
  var flip = Edit.normalize({ type: "highlight", page: 0, rects: [[50, 60, 10, 20]] });
  ok(flip.rects[0].join(",") === "10,20,50,60", "highlight rectangle is normalised (min/max)");
  var oob = await Edit.applyAnnotations(L, base, [{ type: "note", page: 9, x: 1, y: 1, text: "x" }]);
  ok(!Edit.hasMarker(oob), "annotation on a non-existent page is ignored");

  /* ══ PDF 専用の編集ツール ══ */
  async function pageTexts(bytes){
    var pdf = await pdfjs.getDocument({ data: new Uint8Array(bytes), isEvalSupported: false, verbosity: 0 }).promise, out = [];
    for (var i = 1; i <= pdf.numPages; i++){
      var pg = await pdf.getPage(i), tc = await pg.getTextContent();
      out.push({ text: tc.items.map(function(it){ return it.str; }).join(" "), rotate: pg.rotate, w: Math.round(pg.view[2]), ops: (await pg.getOperatorList()).fnArray.length });
    }
    await pdf.destroy();
    return out;
  }
  /* ── 文字修正 / 消去 ── */
  var edits = [
    { type: "textedit", page: 0, x: 30, y: 250, text: "Alexander polynomial", size: 14, color: "#000000", font: "serif", cover: [28, 246, 330, 264], bg: "#ffffff" },
    { type: "textedit", page: 1, x: 40, y: 120, text: "追記の一行", size: 12, color: "#000000", font: "sans", cover: null, bg: "#ffffff" },
    { type: "erase", page: 1, rects: [[30, 240, 300, 265]], color: "#ffffff" }
  ];
  var es = await Edit.applyAnnotations(L, base, edits);
  var eb = await Edit.extractAnnotations(L, es);
  ok(JSON.stringify(eb.annots) === JSON.stringify(edits.map(Edit.normalize)), "text-edit / erase round-trip losslessly");
  var eseen = await annotsOf(es);
  ok(eseen[0][0].subtype === "FreeText" && eseen[0][0].contentsObj.str === "Alexander polynomial", "text edit is a standard FreeText annotation carrying the new text");
  ok(eseen[1].map(function(a){ return a.subtype; }).sort().join(",") === "FreeText,Square", "erase is a filled Square annotation");
  ok(Edit.normalize({ type: "textedit", page: 0, x: 1, y: 2, text: "", cover: null }) === null, "text edit with neither text nor cover is rejected");
  ok(Edit.normalize({ type: "textedit", page: 0, x: 1, y: 2, text: "", cover: [1, 2, 30, 40] }).cover.join(",") === "1,2,30,40", "text edit with only a cover = deleting the original text");
  var tb = Edit.textBox({ x: 10, y: 100, text: "ab\ncd", size: 10 });
  ok(tb[0] === 10 && tb[3] > 100 && tb[1] < 100 - 10, "textBox covers ascender of line 1 down to the last line");

  /* ── 焼き込み ── */
  var before = await pageTexts(base);
  var flat = await Edit.flatten(L, base, edits);
  var fseen = await annotsOf(flat);
  ok(fseen[0].length === 0 && fseen[1].length === 0 && !Edit.hasMarker(flat), "flatten leaves no annotations behind");
  var after = await pageTexts(flat);
  ok(after[0].ops > before[0].ops && after[1].ops > before[1].ops, "flatten draws the edits into the page content itself");
  ok(/Alexander polynomial/.test(after[0].text), "flattened replacement text is part of the page text");
  ok((await Edit.extractAnnotations(L, flat)).annots.length === 0, "a flattened PDF has nothing left to re-edit");

  /* ── ページ操作 ── */
  var three = await (async function(){
    var d = await L.PDFDocument.create(), f = await d.embedFont(L.StandardFonts.Helvetica);
    ["AAA", "BBB", "CCC"].forEach(function(t, i){ d.addPage([300 + i * 10, 300]).drawText("page " + t, { x: 20, y: 250, size: 14, font: f }); });
    return d.save();
  })();
  function order(list){ return list.map(function(p){ return (/page (\w+)/.exec(p.text) || [0, "-"])[1]; }).join(","); }
  var r1 = await Edit.pageOp(L, three, { op: "rotate", page: 1, delta: 90 });
  var t1 = await pageTexts(r1.bytes);
  ok(t1[1].rotate === 90 && t1[0].rotate === 0 && order(t1) === "AAA,BBB,CCC", "rotate turns only that page");
  var r1b = await Edit.pageOp(L, r1.bytes, { op: "rotate", page: 1, delta: -90 });
  ok((await pageTexts(r1b.bytes))[1].rotate === 0, "rotating back restores the page");
  var r2 = await Edit.pageOp(L, three, { op: "delete", page: 0 });
  ok(order(await pageTexts(r2.bytes)) === "BBB,CCC", "delete removes the page");
  var r3 = await Edit.pageOp(L, three, { op: "move", page: 0, to: 2 });
  ok(order(await pageTexts(r3.bytes)) === "BBB,CCC,AAA", "move reorders pages (first → last)");
  var r3b = await Edit.pageOp(L, three, { op: "move", page: 2, to: 0 });
  ok(order(await pageTexts(r3b.bytes)) === "CCC,AAA,BBB", "move reorders pages (last → first)");
  var r4 = await Edit.pageOp(L, three, { op: "blank", at: 1 });
  var t4 = await pageTexts(r4.bytes);
  ok(order(t4) === "AAA,-,BBB,CCC" && t4[1].w === 300, "blank page inserted at the position, sized like its neighbour");
  var r5 = await Edit.pageOp(L, three, { op: "merge", bytes: saved });
  var t5 = await pageTexts(r5.bytes);
  ok(t5.length === 5 && r5.added === 2 && /Kauffman/.test(t5[3].text), "merge appends the other PDF's pages");
  ok(r5.annots.length === 4 && r5.annots[0].page === 3 && r5.annots[3].page === 4 && !Edit.hasMarker(r5.bytes), "merge carries over the other PDF's annotations onto the new page numbers");
  var one = await Edit.pageOp(L, r2.bytes, { op: "delete", page: 0 });
  var threw = false; try { await Edit.pageOp(L, one.bytes, { op: "delete", page: 0 }); } catch (e) { threw = true; }
  ok(threw, "the last remaining page cannot be deleted");

  function pagesOf(list){ return list.map(function(a){ return a.page; }).join(","); }
  function mk(){ return [0, 1, 2, 3].map(function(p){ return { type: "erase", page: p, rects: [[0, 0, 1, 1]] }; }); }
  ok(pagesOf(Edit.remapAnnots(mk(), { op: "delete", page: 1 })) === "0,1,2", "remap: deleting a page drops its annotations and shifts the rest");
  ok(pagesOf(Edit.remapAnnots(mk(), { op: "move", page: 0, to: 2 })) === "2,0,1,3", "remap: moving a page forward");
  ok(pagesOf(Edit.remapAnnots(mk(), { op: "move", page: 3, to: 1 })) === "0,2,3,1", "remap: moving a page backward");
  ok(pagesOf(Edit.remapAnnots(mk(), { op: "blank", at: 2 })) === "0,1,3,4", "remap: inserting a blank page shifts later pages");
  ok(pagesOf(Edit.remapAnnots(mk(), { op: "rotate", page: 1 })) === "0,1,2,3", "remap: rotation keeps page numbers");

  /* ── 実在の PDF で往復 ── */
  var real = path.join(__dirname, "..", "..", "Bada#.pdf");
  if (fs.existsSync(real)){
    var rb = new Uint8Array(fs.readFileSync(real));
    var beforeReal = Core.extractPdfText(Buffer.from(rb));
    var rs = await Edit.applyAnnotations(L, rb, [{ type: "note", page: 0, x: 72, y: 700, text: "Bada 注釈テスト", size: 12 },
                                                 { type: "highlight", page: 0, rects: [[72, 600, 300, 620]] }]);
    var rseen = await annotsOf(rs);
    ok(rseen[0].filter(function(a){ return a.titleObj && a.titleObj.str === "BadaCineVim"; }).length === 2, "real-world PDF (Bada#.pdf): 2 annotations written and readable");
    var after = Core.extractPdfText(Buffer.from(rs));
    ok(after.indexOf("〔注釈〕 Bada 注釈テスト") >= 0, "real-world PDF: note is indexed");
    var rback = await Edit.extractAnnotations(L, rs);
    var restored = Core.extractPdfText(Buffer.from(rback.bytes));
    ok(rback.annots.length === 2 && restored === beforeReal, "real-world PDF: stripping annotations restores the exact original text");
    var rflat = await Edit.flatten(L, rb, [{ type: "textedit", page: 0, x: 72, y: 700, text: "修正後の題名", size: 14, cover: [70, 695, 300, 715] }]);
    var rrot = await Edit.pageOp(L, rflat, { op: "move", page: 0, to: 1 });
    var rt = await pageTexts(rrot.bytes);
    ok(rt.length === 22 && /Artificial/.test(rt[1].text), "real-world PDF: flatten + page move keep all 22 pages readable");
  } else {
    console.log("SKIP  real-world PDF (Bada#.pdf not found)");
  }

  console.log(failed ? ("\n" + failed + " TEST(S) FAILED") : "\nALL PDFEDIT TESTS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
