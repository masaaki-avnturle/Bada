/*
 * main.js — Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 * 音色リストア (Sound Restore Studio): 変調された声・楽器の録音を元の質音へ逆変換。
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
    width: 960,
    height: 840,
    backgroundColor: "#04060a",
    title: "Sound Restore Studio",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  // マイク録音を許可(ローカルアプリのため)
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => {
    cb(permission === "media");
  });
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
