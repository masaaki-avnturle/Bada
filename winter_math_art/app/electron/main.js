/*
 * main.js — Bada 冬景 (Winter Math Music Visualizer) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (β–ζ 方程式群の数学核 + 音楽解析 + Canvas 冬景色レンダラ + MediaRecorder 録画)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 * 書き出した動画はアプリ内の「💾 動画を保存」から保存されます
 * (Electron 標準の保存ダイアログが開きます)。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

/* 録画は canvas.captureStream + MediaRecorder のリアルタイム録画のため、
   バックグラウンドでのタイマー抑制を切っておく */
app.commandLine.appendSwitch("disable-background-timer-throttling");
app.commandLine.appendSwitch("disable-renderer-backgrounding");
app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    backgroundColor: "#070b12",
    title: "Bada 冬景 — Winter Math Music Visualizer",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false,
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
