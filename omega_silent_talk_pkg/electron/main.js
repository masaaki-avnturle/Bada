/*
 * main.js — Electron ラッパー (Windows 10/11 EXE + Ubuntu AppImage/deb)
 * Ω Silent-Talk: ガンマ関数 大域的部分積分多様体 思考入力シミュレータ。
 * 非医療・非読心。実際の脳計測/思考読取は行いません(合成信号のシミュレーション)。
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
    width: 780, height: 980, backgroundColor: "#04060a",
    title: "Ω Silent-Talk",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
