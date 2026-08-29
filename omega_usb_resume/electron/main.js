/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * Ω-USB Resume: 死んだUSBポートを複素回転体・可積分系の n進数ズレ訂正で蘇生する
 * 概念シミュレーション UI。このウィンドウはホストPCの実USBコントローラには触れません。
 * 実機での再認可・再列挙は Linux 版 CLI (bin/bada usb --apply) が行います。
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
    title: "Ω-USB Resume",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
