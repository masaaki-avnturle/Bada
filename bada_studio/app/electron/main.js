/*
 * main.js — BADA Studio (音・映像・作曲スタジオ) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (音源・映像の読み込みと編集、対位法エンジン、オーケストラの多段コード進行、Web Audio 合成、書き出し)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 * WAV / MIDI / 動画 / score.json / プロジェクトの保存は、アプリ内のボタンから
 * 標準の保存ダイアログ (File System Access API) で行われます。
 */
const { app, BrowserWindow, shell, session } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 940,
    backgroundColor: "#0b0e14",
    title: "BADA Studio — 音・映像・作曲スタジオ",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* マイク録音の許可 (アプリ内の 🎙) */
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => {
    cb(permission === "media" || permission === "audioCapture");
  });

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
