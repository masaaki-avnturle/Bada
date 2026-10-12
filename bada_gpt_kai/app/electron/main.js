/*
 * main.js — BadaGPT改 の Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています。ここではデスクトップ
 * ウィンドウとして読み込み、カメラ・マイク (心拍・呼吸の測定) の許可だけを
 * 与えます。外部リンク (GitHub のコミット・Actions・Releases) は既定ブラウザへ
 * 渡し、ZIP / PDF の保存は Electron 標準の保存ダイアログで行います。
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
    height: 880,
    backgroundColor: "#0b0e14",
    title: "BadaGPT改",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });

  win.loadFile(indexPath());
}

app.whenReady().then(() => {
  /* 自分の file:// ページからのカメラ・マイク要求 (心拍・呼吸・音声入力) だけを許可 */
  session.defaultSession.setPermissionRequestHandler((wc, permission, callback, details) => {
    const own = (details.requestingUrl || "").startsWith("file://");
    callback(own && (permission === "media" || permission === "clipboard-sanitized-write"));
  });
  createWindow();
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
