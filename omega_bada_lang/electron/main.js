/*
 * main.js — Electron ラッパー (Windows 10/11 EXE, Ubuntu/Linux AppImage + deb)
 * Ω-Bada Studio: Bada 言語のコンパイラ＋インタープリタ＋量子バックエンド(状態ベクトル
 * シミュレータ + OpenQASM)。全部このアプリ内で動きます（外部依存なし）。
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
    width: 1180, height: 840, backgroundColor: "#04060a",
    title: "Ω-Bada Studio",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
