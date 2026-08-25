/*
 * main.js — ZoneBrowser の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * ZoneBrowser 本体は www/index.html に完全自己完結しています
 * (Bada 言語コア + zone:// ランタイム + サイトを同梱)。ここでは
 * デスクトップ ウィンドウとして読み込み、ページ内の zone:// リンクを
 * アプリ内ナビゲーションに閉じ込め、外部 http(s):// リンクだけを
 * OS の既定ブラウザへ渡します。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 840,
    backgroundColor: "#04060a",
    title: "ZoneBrowser — ultra-network zone://",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* zone:// はアプリ内で処理する(ページ内 JS が担う)。外部 http(s) の
     new-window / target=_blank だけを OS の既定ブラウザへ委譲する。 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    /* file:// の初回ロード以外の遷移は抑止(SPA 内ナビは pushState を使わない) */
    if (!url.startsWith("file://")) e.preventDefault();
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
