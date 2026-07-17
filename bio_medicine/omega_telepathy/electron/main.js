/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-Telepathy: 概念BCI「思考タイピング」シミュレータ。
 * 非医療・非読心。思考の読取/送信は行いません。Neuralink社と無関係。
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
    width: 700, height: 900, backgroundColor: "#04060a",
    title: "Ω-Telepathy",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
