/*
 * main.js — Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 * 動画リストア (Video Restore Studio): 編集された動画を逆補正して元の映像へ近づける。
 * すべて端末内処理・非送信。
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
    width: 1080,
    height: 820,
    backgroundColor: "#04060a",
    title: "Video Restore Studio",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => {
    cb(permission === "media");
  });
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
