/*
 * smoke-ui.js — Bada Search + BadaCineVim (PDF 表示・編集) の実ブラウザ スモークテスト
 *   node sourcetree_search/tools/smoke-ui.js [--shots <dir>]
 *
 * Playwright (Chromium) が必要です。ブラウザ/APK と同じ Web ブリッジで
 *   索引 → 検索 → PDF をページ表示 → ヒットへジャンプ → マーカー/ペン/メモ → :w 保存
 *   → 保存した PDF を別実装で検証 → 開き直して再編集 → .tex / ソースを編集して保存
 * までを通しで確認します。フォルダ上書き保存 (File System Access API) は OPFS を
 * 使って検証し、最後に file:// でも PDF が描画できることを確かめます。
 */
"use strict";
var path = require("path"), fs = require("fs"), os = require("os"), http = require("http");
var { chromium } = require("playwright");
var WWW = path.join(__dirname, "..", "app", "www");
var L = require(path.join(WWW, "vendor", "pdf-lib", "pdf-lib.min.js"));
var Edit = require(path.join(WWW, "pdfedit.js"));

var shotDir = null, ai = process.argv.indexOf("--shots");
if (ai > 0) { shotDir = path.resolve(process.argv[ai + 1]); fs.mkdirSync(shotDir, { recursive: true }); }

var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }

var MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".bcmap": "application/octet-stream",
             ".ttf": "font/ttf", ".pfb": "application/octet-stream", ".css": "text/css" };
function serve(){
  return new Promise(function(resolve){
    var srv = http.createServer(function(req, res){
      var rel = decodeURIComponent(req.url.split("?")[0]);
      var file = path.join(WWW, rel);
      if (!file.startsWith(WWW) || !fs.existsSync(file) || fs.statSync(file).isDirectory()){ res.writeHead(404); res.end(); return; }
      res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" });
      fs.createReadStream(file).pipe(res);
    });
    srv.listen(0, "127.0.0.1", function(){ resolve(srv); });
  });
}

async function makeFixture(dir){
  fs.mkdirSync(path.join(dir, "paper"), { recursive: true });
  fs.mkdirSync(path.join(dir, "src"), { recursive: true });
  var doc = await L.PDFDocument.create();
  var font = await doc.embedFont(L.StandardFonts.Helvetica);
  for (var i = 1; i <= 3; i++){
    var pg = doc.addPage([420, 560]);
    pg.drawText("Knot theory notes - page " + i, { x: 40, y: 500, size: 16, font: font });
    pg.drawText(i === 2 ? "The Kauffman bracket gives the Jones polynomial." : "Background material on diagrams.",
                { x: 40, y: 460, size: 12, font: font });
  }
  fs.writeFileSync(path.join(dir, "paper", "jones.pdf"), await doc.save());
  fs.writeFileSync(path.join(dir, "paper", "jones.tex"), "\\documentclass{article}\n\\begin{document}\nThe Kauffman bracket gives the Jones polynomial.\n\\end{document}\n");
  fs.writeFileSync(path.join(dir, "src", "qcrypto.py"), "def jonesKey(seed):\n    return kauffman_bracket(seed)\n");
  return ["paper/jones.pdf", "paper/jones.tex", "src/qcrypto.py"].map(function(r){ return path.join(dir, r); });
}

async function indexAndSearch(page, files, term){
  await page.setInputFiles("#filepick", files);          /* webkitdirectory: フォルダのパスを渡す */
  await page.waitForFunction(function(){ return /索引完了/.test(document.getElementById("status").textContent); }, null, { timeout: 30000 });
  await search(page, term);
}
async function search(page, term){
  await page.fill("#q", term);
  await page.press("#q", "Escape");
  await page.press("#q", "Enter");
  await page.waitForFunction(function(t){ return document.getElementById("status").textContent.indexOf("「" + t + "」") >= 0; }, term);
}
function fileButton(page, rel){
  return page.locator('.rfile:has(.rel:has-text("' + rel + '")) button[data-cine]');
}
async function cmd(page, line){ for (var i = 0; i < line.length; i++) await page.keyboard.press(line[i] === " " ? "Space" : line[i]); await page.keyboard.press("Enter"); }
async function typeKeys(page, s){ for (var i = 0; i < s.length; i++) await page.keyboard.press(s[i] === " " ? "Space" : s[i]); }
async function pvState(page){
  return page.evaluate(function(){
    var s = window.BadaPdfView.current.state;
    return { n: s.annots.length, types: s.annots.map(function(a){ return a.type; }).join(","), dirty: s.dirty, cur: s.cur,
             pages: s.pages.length, hits: s.hitCount, hitPages: s.hitPages.join(","), editable: s.editable, tool: s.tool, status: s.status };
  });
}
async function inkPixels(page){
  return page.evaluate(function(){
    var c = document.querySelector(".badapdf-overlay .pv-page.ready canvas");
    if (!c || !c.width) return -1;
    var d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data, n = 0;
    for (var i = 0; i < d.length; i += 4) if (d[i] < 140 && d[i + 1] < 140 && d[i + 2] < 140) n++;
    return n;
  });
}

(async function(){
  var tmp = fs.mkdtempSync(path.join(os.tmpdir(), "badasearch-smoke-"));
  var files = await makeFixture(tmp);
  var srv = await serve(), origin = "http://127.0.0.1:" + srv.address().port;
  var browser = await chromium.launch();
  var errors = [];

  /* ══ 1. ブラウザ/APK 相当 (ファイル選択 → ダウンロード保存) ══ */
  var ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  await ctx.addInitScript(function(){ try { delete window.showDirectoryPicker; } catch (e) {} window.showDirectoryPicker = undefined; });
  var page = await ctx.newPage();
  page.on("pageerror", function(e){ errors.push(String(e)); });
  page.on("console", function(m){ if (m.type() === "error") errors.push(m.text()); });
  await page.goto(origin + "/complete.html");
  await indexAndSearch(page, tmp, "Kauffman");
  var label = await fileButton(page, "jones.pdf").textContent();
  ok(/PDF/.test(label), "PDF hit offers the page viewer button — " + label);

  await fileButton(page, "jones.pdf").click();
  await page.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 30000 });
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.hitCount > 0; }, null, { timeout: 30000 });
  var s = await pvState(page);
  ok(s.pages === 3, "PDF opens as real pages (3 pages) — got " + s.pages);
  ok(s.hits === 1 && s.hitPages === "1", "search hit located on page 2 — hits=" + s.hits + " pages=" + s.hitPages);
  ok(s.cur === 1, "viewer jumped to the page with the hit — cur=" + s.cur);
  ok(await page.locator(".badapdf-overlay .pv-hit").count() === 1, "hit is highlighted on the page");
  ok(s.editable, "PDF is editable in the browser/APK bridge (not read-only)");
  await page.keyboard.press("g"); await page.keyboard.press("g");
  await page.waitForFunction(function(){ return window.BadaPdfView.current.state.cur === 0; });
  ok(await inkPixels(page) > 200, "page canvas actually contains rendered text pixels");
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "1-pdf-view.png") });

  /* マーカー (m + ドラッグ) */
  var box = await page.locator('.pv-page[data-i="0"] svg').boundingBox();
  await page.keyboard.press("m");
  await page.mouse.move(box.x + 40, box.y + 50); await page.mouse.down();
  await page.mouse.move(box.x + 300, box.y + 80, { steps: 5 }); await page.mouse.up();
  /* ペン (p + ドラッグ) */
  await cmd(page, ":pen");
  await page.mouse.move(box.x + 60, box.y + 200); await page.mouse.down();
  await page.mouse.move(box.x + 120, box.y + 260, { steps: 6 }); await page.mouse.move(box.x + 200, box.y + 210, { steps: 6 }); await page.mouse.up();
  /* メモ (i + クリック + 入力 + Enter) — 日本語 */
  await cmd(page, ":note");
  await page.mouse.click(box.x + 80, box.y + 330);
  await page.waitForSelector(".pv-noteedit");
  await page.keyboard.type("量子メモ check");
  await page.keyboard.press("Enter");
  s = await pvState(page);
  ok(s.types === "highlight,ink,note" && s.dirty, "marker + pen + note added — " + s.types);
  ok(s.tool === "select", "tool returns to select after a note");
  ok((await page.locator(".badapdf-overlay .cv-flag").textContent()).indexOf("[+]") >= 0, "title shows [+] while unsaved");
  await page.keyboard.press("u"); s = await pvState(page);
  ok(s.n === 2, "u undoes the last annotation — n=" + s.n);
  await cmd(page, ":note");
  await page.mouse.click(box.x + 80, box.y + 330);
  await page.waitForSelector(".pv-noteedit");
  await page.keyboard.type("量子メモ check");
  await page.keyboard.press("Enter");
  /* 未保存の :q は閉じない */
  await typeKeys(page, ":q"); await page.keyboard.press("Enter");
  ok(await page.locator(".badapdf-overlay").count() === 1 && /未保存/.test((await pvState(page)).status), ":q with unsaved annotations is refused");
  if (shotDir) await page.screenshot({ path: path.join(shotDir, "2-pdf-annotated.png") });

  /* :w → ダウンロードとして保存 → 中身を別実装で検証 */
  var dl = page.waitForEvent("download");
  await typeKeys(page, ":w"); await page.keyboard.press("Enter");
  var d = await dl, saved = new Uint8Array(fs.readFileSync(await d.path()));
  ok(d.suggestedFilename() === "jones.pdf", ":w saves the PDF — " + d.suggestedFilename());
  await page.waitForFunction(function(){ return !window.BadaPdfView.current.state.dirty; });
  var back = await Edit.extractAnnotations(L, saved);
  ok(back.annots.length === 3 && back.annots.map(function(a){ return a.type; }).join(",") === "highlight,ink,note", "saved PDF contains the 3 annotations (verified with pdf-lib in Node)");
  var note = back.annots[2];
  ok(note.text === "量子メモ check" && note.page === 0, "note text and page survive — " + JSON.stringify(note.text));
  ok(/保存しました/.test((await pvState(page)).status), "status reports the save");

  /* テキスト表示へ: 抽出テキスト (RO) にメモが反映され、検索にも出る */
  await page.keyboard.press("t");
  await page.waitForSelector(".cinevim-overlay:not(.badapdf-overlay) .cv-text");
  var txt = await page.locator(".cinevim-overlay .cv-text").textContent();
  ok(txt.indexOf("〔注釈〕 量子メモ check") >= 0, "text mode shows the saved note as a 〔注釈〕 line");
  ok((await page.locator(".cinevim-overlay .cv-flag").textContent()).indexOf("[RO]") >= 0, "extracted PDF text stays read-only (edit on the page view)");
  var acts = await page.locator(".cinevim-overlay .cv-act").allTextContents();
  ok(acts.join("|") === "📄 PDF 表示|📝 .tex を編集", "text mode offers PDF view and the sibling .tex — " + acts.join("|"));

  /* PDF 表示へ戻る: 保存済み注釈が編集できる形で復元される → 1 つ削除 */
  await page.locator(".cinevim-overlay .cv-act", { hasText: "PDF 表示" }).click();
  await page.waitForSelector(".badapdf-overlay .pv-page.ready");
  await page.waitForFunction(function(){ var c = window.BadaPdfView.current; return c && c.state.pages.length === 3 && c.state.annots.length === 3; }, null, { timeout: 30000 });
  s = await pvState(page);
  ok(s.n === 3 && !s.dirty && s.editable, "re-opened PDF restores 3 editable annotations");
  await page.keyboard.press("g"); await page.keyboard.press("g");
  await page.locator(".pv-a.pv-note").first().click();
  await page.keyboard.press("x");
  s = await pvState(page);
  ok(s.types === "highlight,ink" && s.dirty, "select + x deletes the note — " + s.types);
  dl = page.waitForEvent("download");
  await typeKeys(page, ":w"); await page.keyboard.press("Enter");
  var saved2 = new Uint8Array(fs.readFileSync(await (await dl).path()));
  ok((await Edit.extractAnnotations(L, saved2)).annots.length === 2, "second save replaces annotations (2 left, no duplicates)");
  await page.waitForFunction(function(){ return !window.BadaPdfView.current.state.dirty; });

  /* 📝 .tex を編集 → CineVim で編集して保存 */
  await page.locator(".badapdf-overlay .cv-act", { hasText: ".tex" }).click();
  await page.waitForSelector(".cinevim-overlay:not(.badapdf-overlay) .cv-text");
  ok((await page.locator(".cinevim-overlay .cv-name").textContent()).indexOf("jones.tex") >= 0, ".tex source of the PDF opens in CineVim");
  ok((await page.locator(".cinevim-overlay .cv-flag").textContent()).indexOf("[RO]") < 0, ".tex is editable in the browser/APK bridge");
  await typeKeys(page, "ggO"); await page.keyboard.type("% zetaedit"); await page.keyboard.press("Escape");
  dl = page.waitForEvent("download");
  await typeKeys(page, ":w"); await page.keyboard.press("Enter");
  d = await dl;
  var tex = fs.readFileSync(await d.path(), "utf8");
  ok(d.suggestedFilename() === "jones.tex" && tex.split("\n")[0] === "% zetaedit", ":w saves the edited .tex — first line " + JSON.stringify(tex.split("\n")[0]));
  await page.keyboard.press("u");
  await typeKeys(page, ":q"); await page.keyboard.press("Enter");
  ok(await page.locator(".cinevim-overlay").count() === 1, ":q refuses to close a modified buffer");
  await typeKeys(page, ":q!"); await page.keyboard.press("Enter");
  ok(await page.locator(".cinevim-overlay").count() === 0, ":q! closes");

  /* 日本語入力: IME / ソフトキーボード相当 (キーイベントなしの文字入力) と変換確定 */
  await search(page, "documentclass");
  await fileButton(page, "jones.tex").click();
  await page.waitForSelector(".cinevim-overlay .cv-text");
  await typeKeys(page, "Go");
  await page.keyboard.insertText("量子多項式");                       /* input イベントのみ (keydown なし) */
  await page.waitForFunction(function(){ var r = document.querySelectorAll(".cinevim-overlay .cv-row"); return r[r.length - 1].textContent.indexOf("量子多項式") === 0; });
  var cdp = await ctx.newCDPSession(page);
  await cdp.send("Input.imeSetComposition", { text: "けつび", selectionStart: 3, selectionEnd: 3 });
  ok(await page.locator(".cinevim-overlay .cv-ime.on").count() === 1, "IME composition is shown at the cursor while converting");
  await cdp.send("Input.insertText", { text: "結び目" });            /* 変換確定 */
  await page.waitForFunction(function(){ var r = document.querySelectorAll(".cinevim-overlay .cv-row"); return r[r.length - 1].textContent.indexOf("結び目") > 0; });
  await page.keyboard.press("Escape");
  var lastLine = await page.evaluate(function(){ var rows = document.querySelectorAll(".cinevim-overlay .cv-row"); return rows[rows.length - 1].textContent; });
  ok(lastLine === "量子多項式結び目", "Japanese typed via IME / soft keyboard lands in the buffer once — " + JSON.stringify(lastLine));
  await page.keyboard.press("/"); await page.keyboard.insertText("多項式");
  await page.waitForFunction(function(){ return document.querySelector(".cinevim-overlay .cv-cmd").textContent === "/多項式"; });
  await page.keyboard.press("Enter");
  var smsg = await page.locator(".cinevim-overlay .cv-msg").textContent();
  ok(/\/多項式/.test(smsg), "Japanese / search works through the same input path — " + JSON.stringify(smsg));
  await page.evaluate(function(){ var dt = new DataTransfer(); dt.setData("text", "rm -rf\n:q!"); document.querySelector(".cv-ime").dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true })); });
  ok(await page.locator(".cinevim-overlay").count() === 1 && /挿入モード/.test(await page.locator(".cinevim-overlay .cv-msg").textContent()), "pasting in NORMAL mode never executes the text as commands");
  await typeKeys(page, ":q!"); await page.keyboard.press("Enter");

  /* 編集内容はすぐ検索に反映される */
  await search(page, "zetaedit");
  ok(await fileButton(page, "jones.tex").count() === 1, "the edit is searchable immediately (index updated on save)");
  await search(page, "量子メモ");
  ok(await fileButton(page, "jones.pdf").count() === 0, "a deleted PDF note is no longer searchable");

  /* ソースコードも編集可 */
  await search(page, "jonesKey");
  await fileButton(page, "qcrypto.py").click();
  await page.waitForSelector(".cinevim-overlay .cv-text");
  ok((await page.locator(".cinevim-overlay .cv-flag").textContent()).indexOf("[RO]") < 0, "source file is editable (was read-only in browser/APK before)");
  await typeKeys(page, ":q"); await page.keyboard.press("Enter");
  await ctx.close();

  /* ══ 2. フォルダを読み書き可で開く (File System Access API を OPFS で代用) → 上書き保存 + .bak ══ */
  var ctx2 = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await ctx2.addInitScript(function(){
    window.showDirectoryPicker = async function(){ var root = await navigator.storage.getDirectory(); return root.getDirectoryHandle("repo"); };
  });
  var page2 = await ctx2.newPage();
  page2.on("pageerror", function(e){ errors.push(String(e)); });
  await page2.goto(origin + "/complete.html");
  var pdfB64 = fs.readFileSync(files[0]).toString("base64");
  await page2.evaluate(async function(b64){
    var root = await navigator.storage.getDirectory();
    try { await root.removeEntry("repo", { recursive: true }); } catch (e) {}
    var repo = await root.getDirectoryHandle("repo", { create: true });
    async function put(dir, name, data){ var h = await dir.getFileHandle(name, { create: true }); var w = await h.createWritable(); await w.write(data); await w.close(); }
    var paper = await repo.getDirectoryHandle("paper", { create: true });
    await put(paper, "jones.pdf", Uint8Array.from(atob(b64), function(c){ return c.charCodeAt(0); }));
    await put(repo, "notes.md", "# notes\nkauffman memo\n");
    var git = await repo.getDirectoryHandle(".git", { create: true });
    await put(git, "config.txt", "kauffman should be skipped");
  }, pdfB64);
  await page2.click("#pick");
  await page2.waitForFunction(function(){ return /索引完了/.test(document.getElementById("status").textContent); }, null, { timeout: 30000 });
  var st2 = await page2.locator("#status").textContent();
  ok(/2 ファイル/.test(st2) && /上書き保存/.test(st2), "folder opened read/write, .git skipped — " + st2.slice(0, 60));
  await search(page2, "kauffman");
  await fileButton(page2, "notes.md").click();
  await page2.waitForSelector(".cinevim-overlay .cv-text");
  await typeKeys(page2, "Go"); await page2.keyboard.type("overwritten line"); await page2.keyboard.press("Escape");
  await typeKeys(page2, ":wq"); await page2.keyboard.press("Enter");
  await page2.waitForFunction(function(){ return !document.querySelector(".cinevim-overlay"); });
  var md = await page2.evaluate(async function(){ var r = await (await navigator.storage.getDirectory()).getDirectoryHandle("repo"); return (await (await r.getFileHandle("notes.md")).getFile()).text(); });
  ok(md === "# notes\nkauffman memo\n\noverwritten line", ":wq overwrites the file inside the opened folder — " + JSON.stringify(md));
  await fileButton(page2, "jones.pdf").click();
  await page2.waitForSelector(".badapdf-overlay .pv-page.ready");
  await page2.waitForFunction(function(){ return window.BadaPdfView.current.state.hitCount > 0; });
  await page2.keyboard.press("M");
  ok((await pvState(page2)).types === "highlight", "M turns the search hits of the page into a marker");
  /* PDF 内検索のコマンドラインは本物の入力欄 (日本語変換でも打てる) */
  await page2.keyboard.press("/");
  ok(await page2.evaluate(function(){ return document.activeElement.className === "pv-cmdin"; }), "/ opens a real input field for the in-PDF search");
  await page2.keyboard.insertText("polynomial");
  await page2.waitForFunction(function(){ return document.querySelector(".pv-cmdin").value === "/polynomial"; });
  await page2.keyboard.press("Enter");
  await page2.waitForFunction(function(){ return /polynomial/.test(window.BadaPdfView.current.state.status) && /箇所/.test(window.BadaPdfView.current.state.status); });
  ok((await pvState(page2)).hits === 1, "in-PDF search finds the new term");
  await typeKeys(page2, ":w"); await page2.keyboard.press("Enter");
  await page2.waitForFunction(function(){ return !window.BadaPdfView.current.state.dirty && /保存しました/.test(window.BadaPdfView.current.state.status); }, null, { timeout: 30000 });
  var disk = await page2.evaluate(async function(){
    var r = await (await navigator.storage.getDirectory()).getDirectoryHandle("repo"), p = await r.getDirectoryHandle("paper"), names = [];
    for await (var k of p.keys()) names.push(k);
    var buf = new Uint8Array(await (await (await p.getFileHandle("jones.pdf")).getFile()).arrayBuffer());
    var bak = names.indexOf("jones.pdf.bak") >= 0 ? (await (await p.getFileHandle("jones.pdf.bak")).getFile()).size : -1;
    return { names: names.sort().join(","), pdf: Array.from(buf), bak: bak };
  });
  ok(disk.names === "jones.pdf,jones.pdf.bak", "PDF overwritten in place, original kept once as .bak — " + disk.names);
  ok(disk.bak === fs.statSync(files[0]).size, ".bak is the untouched original");
  var b3 = await Edit.extractAnnotations(L, new Uint8Array(disk.pdf));
  ok(b3.annots.length === 1 && b3.annots[0].type === "highlight" && b3.annots[0].page === 1, "overwritten PDF holds the marker on page 2");
  if (shotDir) await page2.screenshot({ path: path.join(shotDir, "3-folder-overwrite.png") });
  await ctx2.close();

  /* ══ 3. file:// (EXE/ダブルクリックと同じ読み込み方) でも PDF が描画できる ══ */
  var ctx3 = await browser.newContext({ viewport: { width: 1100, height: 800 } });
  await ctx3.addInitScript(function(){ window.showDirectoryPicker = undefined; });
  var page3 = await ctx3.newPage();
  page3.on("pageerror", function(e){ errors.push("file:// " + String(e)); });
  await page3.goto("file://" + path.join(WWW, "complete.html"));
  await indexAndSearch(page3, tmp, "Kauffman");
  await fileButton(page3, "jones.pdf").click();
  await page3.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 30000 });
  await page3.keyboard.press("g"); await page3.keyboard.press("g");
  await page3.waitForFunction(function(){ return window.BadaPdfView.current.state.cur === 0; });
  ok(await inkPixels(page3) > 200, "file:// — PDF pages render without a web server");
  await ctx3.close();

  /* ══ 4. 詳細ビュー (index.html) からも同じビューアが開く ══ */
  var ctx4 = await browser.newContext({ viewport: { width: 1100, height: 800 } });
  await ctx4.addInitScript(function(){ window.showDirectoryPicker = undefined; });
  var page4 = await ctx4.newPage();
  page4.on("pageerror", function(e){ errors.push("index.html " + String(e)); });
  await page4.goto(origin + "/index.html");
  await page4.setInputFiles("#filepick", tmp);
  await page4.waitForFunction(function(){ return !document.getElementById("q").disabled; });
  await page4.fill("#q", "Kauffman"); await page4.press("#q", "Enter");
  await page4.locator('button[data-cine]:has-text("PDF")').first().click();
  await page4.waitForSelector(".badapdf-overlay .pv-page.ready", { timeout: 30000 });
  ok(true, "detail view (index.html) opens the PDF viewer too");
  await ctx4.close();

  await browser.close(); srv.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  ok(errors.length === 0, "no page errors — " + (errors.slice(0, 3).join(" | ") || "none"));
  console.log(failed ? ("\n" + failed + " CHECK(S) FAILED") : "\nALL UI SMOKE CHECKS PASSED");
  process.exit(failed ? 1 : 0);
})().catch(function(e){ console.error(e); process.exit(1); });
