/*
 * main.js — Bada Contrapunctus (未完のフーガ × 祈るカミーユ 動画工房) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (調性解析 + 位相ボコーダ移調 + 畳み込み残響 + オルガン/オーケストラ合成 +
 *  平行ミックス作曲 + Canvas 筆致レンダリング + MediaRecorder 録画)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 * 動画 / WAV / MIDI / プロジェクトはアプリ内の保存ボタンから保存されます
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
    width: 1460,
    height: 960,
    backgroundColor: "#0e0c10",
    title: "Bada Contrapunctus",
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
