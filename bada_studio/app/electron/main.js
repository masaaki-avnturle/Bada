/*
 * main.js — Bada Studio の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (ポリフォニックシンセ + 16 ステップ ドラムシーケンサー +
 *  ミキサー / ディレイ / リバーブ + マスターバス録音 → WAV)。
 * ここではデスクトップウィンドウとして読み込むだけで、
 * 外部リンクは OS の既定ブラウザへ渡します。
 * 録音した WAV の <a download> は Electron 既定のダウンロード動作で
 * ユーザーのダウンロードフォルダへ保存されます。
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
    width: 1180,
    height: 900,
    backgroundColor: "#0d0e14",
    title: "Bada Studio — 音楽制作スタジオ",
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
