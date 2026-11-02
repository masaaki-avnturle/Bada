/*
 * main.js — Bada PatchGuard の Electron ラッパー
 *          (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (Bada 処理系 + guard.bada + PHP 解析 + 差分 + UI)。ここではデスクトップ
 * ウィンドウとして読み込むだけです。ネットワークは一切使わず、
 * 検査するソースは端末の外に出ません。
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
    width: 1240,
    height: 880,
    minWidth: 360,
    backgroundColor: "#151816",
    title: "Bada PatchGuard",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* 外部リンクは OS の既定ブラウザへ委譲、ページ遷移は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
