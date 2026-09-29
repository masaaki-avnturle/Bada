/*
 * main.js — Electron ラッパー (Windows 10/11 EXE, Linux AppImage/deb)
 * Ω-Junishi DNA: DNA 配列の k-mer 照合による十二支の動物の DNA 検査 ＋ Γ×Jones 熱エネルギー概念ビュー。
 * 非医療・研究/教育用。
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
    width: 1080, height: 820, backgroundColor: "#04060a",
    title: "Ω-Junishi DNA",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
