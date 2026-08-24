/*
 * main.js — Electron ラッパー (Windows 10/11 EXE)
 * BadaGPT — Bada言語 ζ-Entropy 未知事前予知エンジン。
 * PDF/ソースコード投稿 → Claude API キー入力 → 解答生成 → PDF/ソースコードでダウンロード。
 * 概念シミュレーション / 研究アート・非医療。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 980, height: 820, backgroundColor: "#04060a",
    title: "BadaGPT — ζ-Entropy",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  // 外部リンクは既定ブラウザで開く
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    return { action: "allow" };
  });
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
