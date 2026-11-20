/*
 * main.js — Bada Search (SourceTree 付属 PDF・ソースコード検索エンジン)
 *           Windows 10/11 向け Electron ラッパー
 *
 * SourceTree の「カスタム操作」からパラメータ $REPO 付きで起動されると、
 * そのリポジトリを即インデックスして検索画面を開きます。
 * 単体起動時はフォルダ選択から。インデックス/検索は core/searchcore.js
 * (Node 標準モジュールのみ) が行い、renderer とは IPC で通信します。
 */
const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const path = require("path");
const fs = require("fs");
const core = require(path.join(__dirname, "core", "searchcore.js"));

let win = null;
let index = null;
let vocab = null;

/* SourceTree カスタム操作: 引数の最後にリポジトリパスが渡る ($REPO) */
function argvRepo(){
  const args = process.argv.slice(app.isPackaged ? 1 : 2);
  for (let i = args.length - 1; i >= 0; i--){
    const a = args[i];
    if (a && !a.startsWith("-")){
      try { if (fs.statSync(a).isDirectory()) return a; } catch (e){}
    }
  }
  return null;
}

function createWindow(){
  win = new BrowserWindow({
    width: 1280,
    height: 860,
    backgroundColor: "#000000",
    title: "Bada Search — SourceTree 付属 単語補完検索 (論文・ソースコード)",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(function(d){
    if (/^https?:\/\//i.test(d.url)) shell.openExternal(d.url);
    return { action: "deny" };
  });
  /* 既定は広島大学病院の薬剤検索風の黒い大画面 (単語補完 + ポップアップメニュー)。
     従来の詳細ビューは www/index.html (画面内のリンクから行き来できる)。 */
  win.loadFile(path.join(__dirname, "www", "complete.html"));
}

ipcMain.handle("choose-folder", async function(){
  const r = await dialog.showOpenDialog(win, { properties: ["openDirectory"], title: "検索するリポジトリ/フォルダを選択" });
  if (r.canceled || !r.filePaths.length) return null;
  return r.filePaths[0];
});
ipcMain.handle("build-index", function(ev, dir){
  index = core.buildIndex(dir);
  vocab = null;                                   /* 語彙は次の build-vocab で作り直す */
  return {
    root: index.root, files: index.files.length, scanned: index.scanned,
    langs: index.langs, errors: index.errors.slice(0, 20), builtAt: index.builtAt
  };
});
ipcMain.handle("build-vocab", function(){
  if (!index) return { error: "先にフォルダをインデックスしてください" };
  vocab = core.buildVocab(index, {});
  return { size: vocab.size, builtAt: vocab.builtAt };
});
ipcMain.handle("complete", function(ev, prefix, opts){
  if (!vocab) return { items: [], total: 0 };
  try { return core.complete(vocab, prefix, opts || {}); }
  catch (e){ return { items: [], total: 0, error: e.message }; }
});
ipcMain.handle("search", function(ev, query, opts){
  if (!index) return { error: "先にフォルダをインデックスしてください" };
  try { return core.search(index, query, opts || {}); }
  catch (e){ return { error: e.message }; }
});
ipcMain.handle("file-text", function(ev, p){
  /* まず索引済みの本文 (PDF 抽出テキスト含む) を使い、無ければディスクから読む */
  if (index){
    var f = index.files.find(function(x){ return x.path === p; });
    if (f) return { name: f.rel, lines: f.lines, lang: f.lang, readonly: f.lang === "PDF" };
  }
  try {
    var buf = fs.readFileSync(p);
    if (buf.includes(0)) return { error: "バイナリファイルは開けません" };
    return { name: path.basename(p), lines: buf.toString("utf8").split(/\r?\n/), lang: core.langOf(p) || "Text", readonly: false };
  } catch (e){ return { error: e.message }; }
});
/* 書き込みは「索引したフォルダの中」に限定する (renderer から任意パスへ書かせない) */
function insideRoot(p){
  if (!index || !index.root || typeof p !== "string") return false;
  const root = path.resolve(index.root), full = path.resolve(p);
  return full === root || full.startsWith(root + path.sep);
}
function indexed(p){ return index ? index.files.find(function(x){ return x.path === p; }) : null; }
ipcMain.handle("save-file", function(ev, p, text){
  if (!insideRoot(p)) return { error: "索引したフォルダの外には保存できません" };
  if (core.langOf(p) === "PDF") return { error: "PDF はページ表示で編集してください" };
  try {
    fs.writeFileSync(p, text, "utf8");
    const f = indexed(p);                       /* 編集内容をすぐ検索に反映 */
    if (f){ f.lines = String(text).split(/\r?\n/); f.size = Buffer.byteLength(text, "utf8"); }
    return { ok: true };
  }
  catch (e){ return { error: e.message }; }
});
/* PDF のページ表示用に生バイトを渡す / 注釈を書き込んだ PDF を保存する */
ipcMain.handle("file-bytes", function(ev, p){
  if (!insideRoot(p)) return { error: "索引したフォルダの外は開けません" };
  try {
    const st = fs.statSync(p);
    if (st.size > 64 * 1024 * 1024) return { error: "PDF が大きすぎます (64MB 超)" };
    return { bytes: new Uint8Array(fs.readFileSync(p)) };
  } catch (e){ return { error: e.message }; }
});
ipcMain.handle("save-bytes", function(ev, p, bytes){
  if (!insideRoot(p)) return { error: "索引したフォルダの外には保存できません" };
  if (core.langOf(p) !== "PDF") return { error: "PDF 以外はバイナリ保存できません" };
  try {
    const buf = Buffer.from(bytes);
    if (buf.slice(0, 5).toString("latin1") !== "%PDF-") return { error: "PDF として不正なデータです" };
    let note = "";
    const bak = p + ".bak";                      /* 初回だけ元の PDF を退避 */
    if (fs.existsSync(p) && !fs.existsSync(bak)){ fs.copyFileSync(p, bak); note = "元の PDF は " + path.basename(bak) + " に退避"; }
    const tmp = p + ".badatmp";                  /* 一時ファイルに書いてから置換 (途中で壊さない) */
    fs.writeFileSync(tmp, buf);
    fs.renameSync(tmp, p);
    const f = indexed(p);
    if (f){
      try { const t = core.extractPdfText(buf); if (t.trim()) f.lines = t.split(/\r?\n/); f.size = buf.length; } catch (e2){}
    }
    return { ok: true, note: note };
  } catch (e){ return { error: e.message }; }
});
ipcMain.handle("open-file", function(ev, p){ return shell.openPath(p); });
ipcMain.handle("reveal-file", function(ev, p){ shell.showItemInFolder(p); return true; });
ipcMain.handle("startup-repo", function(){ return argvRepo(); });
ipcMain.handle("app-path", function(){ return process.execPath; });

app.whenReady().then(createWindow);
app.on("window-all-closed", function(){ if (process.platform !== "darwin") app.quit(); });
app.on("activate", function(){ if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
