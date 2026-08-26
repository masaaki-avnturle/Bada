/*
 * main.js — Electron ラッパー (Windows 10/11 EXE, Ubuntu AppImage/deb)
 * Ω-Suite: Bada リポジトリの概念シミュレーション7種。
 * 非医療。実在の医療機器・薬剤・治療方針とは無関係です。
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
    width: 980, height: 860, backgroundColor: "#04060a",
    title: "Ω-Suite",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
