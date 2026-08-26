/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-GlucoGate Forge: 形態形成場によるドーパミン作動性「糖取り込み薬剤」製造装置シミュレータ。
 * 概念シミュレーション・非医療。実在の医薬品を設計/製造/評価するものではありません。
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
    title: "Ω-GlucoGate Forge",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
