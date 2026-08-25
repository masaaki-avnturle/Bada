/*
 * main.js — NGN Quantum Grid の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 本体は www/index.html に完全自己完結しています(Bada 言語コア +
 * zone:// ランタイム + NGN/HDD/エンタングル拡張)。ここでは
 * デスクトップ ウィンドウとして読み込み、外部 http(s):// リンクだけを
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
    height: 860,
    backgroundColor: "#04060a",
    title: "NGN Quantum Grid — zone:// over NTT NGN",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
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
