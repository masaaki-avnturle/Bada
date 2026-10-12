/*
 * main.js — BadaGPT電信 の Electron ラッパー
 *          (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (電信エンジン + 全体把握 + アプリ生成 + 検証 + 論文 + FSK 音響モデム)。
 * ここではデスクトップウィンドウとして読み込み、
 *   - 生成アプリ / ZIP / PDF のダウンロードは保存ダイアログで受け、
 *   - 「スマホから電信で受信」のためマイクの使用を許可し、
 *   - 外部リンクは OS の既定ブラウザへ渡します。
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
    width: 1200,
    height: 900,
    backgroundColor: "#080b14",
    title: "BadaGPT電信",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });

  win.loadFile(indexPath());
}

app.whenReady().then(() => {
  /* FSK 受信 (マイク) だけを許可し、それ以外の権限要求は断る */
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb, details) => {
    const audioOnly = permission === "media" && (details.mediaTypes || []).every((t) => t === "audio");
    cb(audioOnly);
  });
  createWindow();
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
