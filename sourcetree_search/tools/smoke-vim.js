/*
 * smoke-vim.js — PDF を Vim の NORMAL / INSERT / COMMAND モードで編集できることを実ブラウザで確認
 *   node sourcetree_search/tools/smoke-vim.js [--shots <dir>]      (Playwright / Chromium が必要)
 *
 *   NORMAL  : h j k l / w b / 0 $ でページ上の文字にカーソルを動かす、x dd D yy p u
 *   INSERT  : i a A o cc でその場に入力し Esc で確定 (日本語入力も)
 *   COMMAND : :s/旧/新/  :%s/旧/新/g  :d  :note 文  :hl  ツール切り替え
 * 最後に :w で保存した PDF を読み直し、編集がそのまま入っていることを検証します。
 */
"use strict";
var path = require("path"), fs = require("fs"), os = require("os");
var { chromium } = require("playwright");
var WWW = path.join(__dirname, "..", "app", "www");
var L = require(path.join(WWW, "vendor", "pdf-lib", "pdf-lib.min.js"));
var Edit = require(path.join(WWW, "pdfedit.js"));

var shotDir = null, ai = process.argv.indexOf("--shots");
if (ai > 0) { shotDir = path.resolve(process.argv[ai + 1]); fs.mkdirSync(shotDir, { recursive: true }); }
var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }
async function keys(page, s){ for (var i = 0; i < s.length; i++) await page.keyboard.press(s[i] === " " ? "Space" : s[i]); }
async function cmd(page, line){
  await page.keyboard.press(line[0]);
  await page.waitForFunction(function(){ return document.activeElement.className === "pv-cmdin"; });
  await page.keyboard.insertText(line.slice(1));
  await page.waitForFunction(function(v){ return document.querySelector(".pv-cmdin").value === v; }, line);
  await page.keyboard.press("Enter");
}
function st(page){
  return page.evaluate(function(){
    var s = window.BadaPdfView.current.state, v = s.vc, ln = s.vcLine;
    return { page: v ? v.page : -1, k: v ? v.k : -1, c: v ? v.c : -1, line: ln ? ln.text : null, mode: s.mode, status: s.status,
             annots: s.annots.map(function(a){ return a.type + "@" + a.page; }).join(","), n: s.annots.length, dirty: s.dirty,
             modeLabel: document.querySelector(".badapdf-overlay .cv-mode").textContent };
  });
}
/* カーソルが (page,k,c) に来る / 行の文字が text になるのを待つ */
function waitCur(page, want){
  return page.waitForFunction(function(w){
    var s = window.BadaPdfView.current.state, v = s.vc, ln = s.vcLine;
    if (!v || !ln || s.mode !== "normal") return false;
    return (w.page == null || v.page === w.page) && (w.k == null || v.k === w.k) && (w.c == null || v.c === w.c) && (w.text == null || ln.text === w.text);
  }, want, { timeout: 15000 });
}
/* INSERT モードに入る → 文字を打つ → Esc で確定 */
async function insert(page, key, text, expectValue){
  await keys(page, key);
  await page.waitForSelector(".pv-noteedit");
  var info = await page.evaluate(function(){ var t = document.querySelector(".pv-noteedit"); return { value: t.value, caret: t.selectionStart, label: document.querySelector(".badapdf-overlay .cv-mode").textContent }; });
  await page.keyboard.insertText(text);
  await page.waitForFunction(function(v){ return document.querySelector(".pv-noteedit").value === v; }, expectValue);
  await page.keyboard.press("Escape");
  await page.waitForFunction(function(){ return !document.querySelector(".pv-noteedit") && window.BadaPdfView.current.state.mode === "normal"; });
  return info;
}
var LINE = "The Kauffman bracket gives the Jones polynomial.";

(async function(){
  var tmp = fs.mkdtempSync(path.join(os.tmpdir(), "badasearch-vim-")), repo = path.join(tmp, "repo");
  fs.mkdirSync(repo);
  var doc = await L.PDFDocument.create(), font = await doc.embedFont(L.StandardFonts.TimesRoman);
  ["AAA", "BBB", "CCC"].forEach(function(t){
    var pg = doc.addPage([420, 560]);
    pg.drawText("Section " + t, { x: 40, y: 500, size: 18, font: font });
    pg.drawText(LINE, { x: 40, y: 460, size: 12, font: font });
    pg.drawText("Closing remark " + t + ".", { x: 40, y: 430, size: 12, font: font });
  });
  fs.writeFileSync(path.join(repo, "paper.pdf"), await doc.save());

  var browser = await chromium.launch(), errors = [];
  var ctx = await browser.newContext({ viewport: { width: 1280, height: 940 }, acceptDownloads: true });
  await ctx.addInitScript(function(){ window.showDirectoryPicker = undefined; });
  var page = await ctx.newPage();
  page.on("pageerror", function(e){ errors.push(String(e)); });
  page.on("console", function(m){ if (m.type() === "error") errors.push(m.text()); });
  await page.goto("file://" + path.join(WWW, "complete.html"));
  await page.setInputFiles("#filepick", repo);
  await page.waitForFunction(function(){ return /索引完了/.test(document.getElementById("status").textContent); });
  await page.fill("#q", "Jones"); await page.press("#q", "Escape"); await page.press("#q", "Enter");
  await page.locator("button[data-cine]").first().click();
  await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 30000 });

  /* ── NORMAL: 検索ヒットの行・文字にカーソルが載る ── */
  await waitCur(page, { page: 0, k: 1, c: LINE.indexOf("Jones") });
  var s = await st(page);
  ok(s.line === LINE && s.modeLabel === "NORMAL", "opens in NORMAL mode with the cursor on the search hit — line " + s.k + " col " + s.c);
  ok(await page.locator(".badapdf-overlay .pv-vimcur").count() === 1, "a block cursor is drawn on the page text");

  await keys(page, "gg"); await waitCur(page, { page: 0, k: 0, c: 0, text: "Section AAA" });
  await keys(page, "j");  await waitCur(page, { k: 1, c: 0 });
  await keys(page, "lll"); await waitCur(page, { k: 1, c: 3 });
  await keys(page, "h");  await waitCur(page, { c: 2 });
  await keys(page, "$");  await waitCur(page, { c: LINE.length - 1 });
  await keys(page, "0");  await waitCur(page, { c: 0 });
  await keys(page, "w");  await waitCur(page, { k: 2, c: 0, text: "Closing remark AAA." });
  await keys(page, "j");  await waitCur(page, { page: 1, k: 0, text: "Section BBB" });
  ok(true, "j at the last line continues onto the next page");
  await keys(page, "k");  await waitCur(page, { page: 0, k: 2 });
  await keys(page, "b");  await waitCur(page, { k: 1, c: 0 });
  ok(true, "h j k l / w b / 0 $ / gg move the cursor over the PDF text");

  /* ── INSERT: i (カーソル位置に挿入) ── */
  await keys(page, "llll");  await waitCur(page, { c: 4 });
  var info = await insert(page, "i", "great ", "The great Kauffman bracket gives the Jones polynomial.");
  ok(info.value === LINE && info.caret === 4 && info.label === "-- 挿入 --", "i enters INSERT mode on the line with the caret at the cursor — caret " + info.caret + " label " + info.label);
  await waitCur(page, { k: 1, text: "The great Kauffman bracket gives the Jones polynomial." });
  s = await st(page);
  ok(s.annots === "textedit@0" && s.dirty && s.modeLabel === "NORMAL", "Esc commits the typed text and returns to NORMAL — " + s.annots);

  /* a / A (日本語入力) */
  await insert(page, "A", " 量子不変量。", "The great Kauffman bracket gives the Jones polynomial. 量子不変量。");
  await waitCur(page, { text: "The great Kauffman bracket gives the Jones polynomial. 量子不変量。" });
  ok((await st(page)).n === 1, "A appends at the end of the line (Japanese typed through the IME path); still one edit for that line");

  /* x / u / D */
  await keys(page, "0"); await waitCur(page, { c: 0 });
  await keys(page, "x"); await waitCur(page, { text: "he great Kauffman bracket gives the Jones polynomial. 量子不変量。" });
  await keys(page, "u"); await waitCur(page, { text: "The great Kauffman bracket gives the Jones polynomial. 量子不変量。" });
  ok(true, "x deletes the character under the cursor and u undoes it");
  await keys(page, "$"); await keys(page, "hhhhh");
  await waitCur(page, { c: "The great Kauffman bracket gives the Jones polynomial. 量子不変量。".length - 6 });
  await keys(page, "D"); await waitCur(page, { text: "The great Kauffman bracket gives the Jones polynomial." });
  ok(true, "D deletes from the cursor to the end of the line");

  /* o (下に新しい行) → dd で消える */
  await insert(page, "o", "追加した行です", "追加した行です");
  await waitCur(page, { text: "追加した行です" });
  s = await st(page);
  ok(s.annots === "textedit@0,textedit@0" && s.k === 2, "o opens a new line below and the cursor moves onto it — k " + s.k);
  await keys(page, "dd");
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.annots.length === 1; });
  ok(true, "dd on an added line removes it");
  await keys(page, "u");
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.annots.length === 2; });

  /* cc (行を打ち直す) */
  await keys(page, "gg"); await waitCur(page, { k: 0, text: "Section AAA" });
  info = await insert(page, "cc", "Chapter One", "Chapter One");
  ok(info.value === "", "cc starts the line empty");
  await waitCur(page, { k: 0, text: "Chapter One" });

  /* yy / p */
  await keys(page, "yy"); await keys(page, "p");
  await page.waitForFunction(function(){ var s = window.BadaPdfView.current.state; return s.annots.length === 4 && s.vcLine && s.vcLine.text === "Chapter One" && s.vc.k === 1; });
  ok(true, "yy / p copy the line below");
  await keys(page, "u");
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.annots.length === 3; });
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "vim-1-normal.png") });

  /* ── COMMAND: :s (カーソル行) ── */
  await keys(page, "gg"); await keys(page, "j"); await waitCur(page, { k: 1 });
  await cmd(page, ":s/Jones/HOMFLY/");
  await waitCur(page, { text: "The great Kauffman bracket gives the HOMFLY polynomial." });
  ok(/1 行を置換/.test((await st(page)).status), ":s/Jones/HOMFLY/ substitutes on the cursor line");
  await cmd(page, ":s/great //");
  await waitCur(page, { text: "The Kauffman bracket gives the HOMFLY polynomial." });
  await cmd(page, ":s/HOMFLY/Jones/");
  await waitCur(page, { text: LINE });
  ok((await st(page)).annots === "textedit@0,textedit@0", "editing a line back to its original text drops the correction (nothing left to cover) — " + (await st(page)).annots);

  /* :%s (全ページ) — 1 回の u でまとめて戻る */
  var before = (await st(page)).n;
  await cmd(page, ":%s/Closing remark (\\w+)/Summary of \\1/");
  await page.waitForFunction(function(){ return /3 行を置換しました \(3 ページ\)/.test(window.BadaPdfView.current.state.status); });
  s = await st(page);
  ok(s.n === before + 3, ":%s/…/…/ substitutes on every page, with \\1 back-references — " + s.annots);
  var p3 = await page.evaluate(async function(){ return (await window.BadaPdfView.current.linesOf(2)).map(function(l){ return l.text; }); });
  ok(p3[2] === "Summary of CCC.", "page 3 now reads “Summary of CCC.” — " + JSON.stringify(p3[2]));
  await keys(page, "u");
  await page.waitForFunction(function(n){ return window.BadaPdfView.current.state.annots.length === n; }, before);
  ok(true, "one u undoes the whole :%s");
  await cmd(page, ":%s/Closing remark (\\w+)/Summary of \\1/");
  await page.waitForFunction(function(n){ return window.BadaPdfView.current.state.annots.length === n + 3; }, before);
  await cmd(page, ":s/nothing-here/x/");
  await page.waitForFunction(function(){ return /パターンが見つかりません/.test(window.BadaPdfView.current.state.status); });
  ok((await st(page)).n === before + 3, "a pattern that matches nothing changes nothing");

  /* :note / :hl / :d / ツール切り替え */
  await cmd(page, ":note 要確認: 出典");
  await page.waitForFunction(function(){ return /メモを付けました/.test(window.BadaPdfView.current.state.status); });
  await cmd(page, ":hl");
  await page.waitForFunction(function(){ return /マーカーを引きました/.test(window.BadaPdfView.current.state.status); });
  s = await st(page);
  ok(/note@0/.test(s.annots) && /highlight@0/.test(s.annots), ":note <text> and :hl annotate the cursor line — " + s.annots);
  await page.keyboard.press("Escape"); await keys(page, "j"); await waitCur(page, { k: 2, text: "追加した行です" });
  await keys(page, "j"); await waitCur(page, { k: 3, text: "Summary of AAA." });
  await cmd(page, ":d");
  await waitCur(page, { k: 3, text: "" });
  ok(true, ":d deletes the cursor line");
  await cmd(page, ":pen");
  ok(await page.evaluate(function(){ return window.BadaPdfView.current.state.tool; }) === "ink", ":pen switches to the pen tool");
  await cmd(page, ":select");
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "vim-2-command.png") });

  /* ── :w → 保存した PDF を検証 ── */
  var dl = page.waitForEvent("download");
  await cmd(page, ":w");
  var saved = new Uint8Array(fs.readFileSync(await (await dl).path()));
  var back = await Edit.extractAnnotations(L, saved);
  var texts = back.annots.filter(function(a){ return a.type === "textedit"; }).map(function(a){ return a.page + ":" + a.text; }).sort();
  ok(texts.join(" | ") === ["0:", "0:Chapter One", "0:追加した行です", "1:Summary of BBB.", "2:Summary of CCC."].sort().join(" | "),
     "the saved PDF carries every Vim edit — " + texts.join(" | "));
  ok(back.annots.filter(function(a){ return a.type === "note"; })[0].text === "要確認: 出典", "the :note text is saved");

  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  ok(errors.length === 0, "no page errors — " + (errors.slice(0, 3).join(" | ") || "none"));
  console.log(failed ? ("\n" + failed + " CHECK(S) FAILED") : "\nALL VIM MODE SMOKE CHECKS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
