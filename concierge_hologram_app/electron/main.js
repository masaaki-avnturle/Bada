/*
 * main.js — Electron ラッパー (Windows 10/11 EXE, Ubuntu AppImage/deb)
 * まちしおり — ホログラム・コンシェルジュ。
 * カメラ(風景の透過)・位置情報を使う案内アプリ。デスクトップでは
 * Webカメラがあれば風景として使い、無ければ空景で動作します。
 */
const { app, BrowserWindow, session } = require("electron");
const path = require("path");

function indexPath() {
  // パッケージ時は extraResources(resources/www)、開発時は ../www
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  // カメラ / 位置情報の許可を通す
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => {
    cb(["media", "geolocation", "camera"].includes(permission));
  });

  const win = new BrowserWindow({
    width: 480,
    height: 900,
    minWidth: 360,
    minHeight: 640,
    backgroundColor: "#04060a",
    title: "まちしおり — ホログラム・コンシェルジュ",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
