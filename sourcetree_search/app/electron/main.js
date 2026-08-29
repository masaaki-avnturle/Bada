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
    width: 1060,
    height: 780,
    backgroundColor: "#0b0e14",
    title: "Bada Search — SourceTree 付属 PDF・ソースコード検索",
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
  win.loadFile(path.join(__dirname, "www", "index.html"));
}

ipcMain.handle("choose-folder", async function(){
  const r = await dialog.showOpenDialog(win, { properties: ["openDirectory"], title: "検索するリポジトリ/フォルダを選択" });
  if (r.canceled || !r.filePaths.length) return null;
  return r.filePaths[0];
});
ipcMain.handle("build-index", function(ev, dir){
  index = core.buildIndex(dir);
  return {
    root: index.root, files: index.files.length, scanned: index.scanned,
    langs: index.langs, errors: index.errors.slice(0, 20), builtAt: index.builtAt
  };
});
ipcMain.handle("search", function(ev, query, opts){
  if (!index) return { error: "先にフォルダをインデックスしてください" };
  try { return core.search(index, query, opts || {}); }
  catch (e){ return { error: e.message }; }
});
ipcMain.handle("open-file", function(ev, p){ return shell.openPath(p); });
ipcMain.handle("reveal-file", function(ev, p){ shell.showItemInFolder(p); return true; });
ipcMain.handle("startup-repo", function(){ return argvRepo(); });
ipcMain.handle("app-path", function(){ return process.execPath; });

app.whenReady().then(createWindow);
app.on("window-all-closed", function(){ if (process.platform !== "darwin") app.quit(); });
app.on("activate", function(){ if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
