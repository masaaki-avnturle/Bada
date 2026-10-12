/*
 * main.js — Electron ラッパー (Windows 10/11 EXE + Linux)
 * BadaGPT 改良版 — 思考入力からアプリ/PDF/ソースコードを生成するスタジオ。
 * 生成物は雛形/概念実証。思考入力は概念版 Ω-Telepathy のテキスト(実際の読心ではない)。
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
    width: 1040, height: 820, backgroundColor: "#0b0e14",
    title: "BadaGPT 改良版",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
