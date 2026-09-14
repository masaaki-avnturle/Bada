/*
 * main.js — Bada SoundFilm (MP3 → 動画 変換スタジオ) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (ID3 タグ解析 + Canvas ビジュアライザ + Web Audio + MediaRecorder 録画)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 * 変換した動画はアプリ内の「💾 動画を保存」からダウンロード保存されます
 * (Electron 標準の保存ダイアログが開きます)。
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
    width: 1360,
    height: 900,
    backgroundColor: "#0b0e14",
    title: "Bada SoundFilm",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。外部リンクは既定ブラウザへ、その他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://") && !url.startsWith("blob:")) {
      e.preventDefault();
    }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
