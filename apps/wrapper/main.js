/*
 * main.js — 汎用 Electron ラッパー (Windows 10/11 EXE + Ubuntu AppImage/deb)
 * apps/apps.json の各アプリ (自己完結 HTML) を www/ として同梱して起動します。
 * ウィンドウ設定はビルド時に生成される app.json から読み込みます。
 */
const { app, BrowserWindow } = require("electron");
const path = require("path");

let cfg = { title: "Bada Omega App", width: 1100, height: 780, background: "#04060a" };
try {
  cfg = Object.assign(cfg, require("./app.json"));
} catch (_) {
  /* app.json なしでも既定値で動作 */
}

function indexPath() {
  // パッケージ時は extraResources(resources/www)、開発時は ./www
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: cfg.width,
    height: cfg.height,
    backgroundColor: cfg.background,
    title: cfg.title,
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
