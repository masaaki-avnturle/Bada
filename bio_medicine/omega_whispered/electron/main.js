/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-Whispered: 数学記号 × 方程式意味解析のウィスパード適性検査。
 * 非公式ファン・オマージュ / 学習・娯楽目的。実在の能力を診断するものではありません。
 */
const { app, BrowserWindow } = require("electron");
const path = require("path");
function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}
function createWindow() {
  const win = new BrowserWindow({
    width: 1180, height: 860, backgroundColor: "#04060a",
    title: "Omega-Whispered",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
