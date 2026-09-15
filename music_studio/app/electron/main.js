/*
 * main.js — Bada Music Studio (音楽制作ソフト / DAW) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (シンセ + ドラム音源 + シーケンサ + ミキサー + WAV/MIDI 書き出し)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 *
 * ・書き出した WAV / MIDI / .badaproj は Electron 標準の保存ダイアログで保存されます。
 * ・マイク録音のためにメディアデバイスの許可要求を通します
 *   (音声入力のみ。それ以外の権限要求はすべて拒否します)。
 */
const { app, BrowserWindow, shell, session } = require("electron");
const path = require("path");

/* 音声の途切れを防ぐため省電力スロットリングを無効化 */
app.commandLine.appendSwitch("disable-renderer-backgrounding");
app.commandLine.appendSwitch("disable-background-timer-throttling");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 1024,
    minHeight: 680,
    backgroundColor: "#0b0e14",
    title: "Bada Music Studio",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。外部リンクは既定ブラウザへ、その他の遷移は抑止 */
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

app.whenReady().then(() => {
  /* マイク録音のみ許可。カメラ・位置情報などは拒否する */
  session.defaultSession.setPermissionRequestHandler((wc, permission, callback) => {
    callback(permission === "media" || permission === "audioCapture");
  });
  createWindow();
});

app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
