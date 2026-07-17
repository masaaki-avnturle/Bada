/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-Biofeedback Oracle: 生成的バイオフィードバック・サウンドアート。
 * 娯楽/非医療/非予知。アカシックレコードへのアクセスも未来予知も行いません。
 */
const { app, BrowserWindow } = require("electron");
const path = require("path");

function indexPath() {
  // パッケージ時は extraResources(resources/www)、開発時は ../www
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 480,
    height: 860,
    backgroundColor: "#04060a",
    title: "Ω-Biofeedback Oracle",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
