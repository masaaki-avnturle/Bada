/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-MorphoForge: 形態形成場 × 電磁ドリフト × カタストロフ分岐（概念シミュレーション）。
 * 非医療。実在の細胞・薬剤・iPS 樹立プロトコルは含まれません。
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
    width: 960, height: 820, backgroundColor: "#04060a",
    title: "Ω-MorphoForge",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
