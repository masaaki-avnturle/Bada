/*
 * main.js — Bada Akasha の Electron ラッパー (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (論文集コーパス + Bada インタープリタ + akasha.bada エンジンを同梱)。
 * 端末内で完結するアプリなので、file:// 以外への通信はすべて遮断します。
 */
const { app, BrowserWindow, session } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 900,
    backgroundColor: "#0f0e14",
    title: "Bada Akasha",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  win.webContents.on("will-navigate", (e, url) => { if (!url.startsWith("file://")) e.preventDefault(); });
  win.loadFile(indexPath());
}

app.whenReady().then(() => {
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
    const ok = /^(file|data|devtools):/i.test(details.url);
    callback({ cancel: !ok });
  });
  createWindow();
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
