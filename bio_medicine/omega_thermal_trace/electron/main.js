/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-Thermal Trace: Γ多様体による体内/脳の熱エネルギー流トレース（概念シミュレーション）。
 * 非医療。実在の人体温度は計測しません。
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
    width: 900, height: 760, backgroundColor: "#04060a",
    title: "Ω-Thermal Trace",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
