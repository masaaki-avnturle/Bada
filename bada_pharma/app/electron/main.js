/*
 * main.js — Bada Pharma (薬剤製造装置) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (計測取込 + 標的同定 + 分子設計 + 逆合成の収率計画 + 製剤化 +
 *  薬物動態 + 品質管理 + 製造記録の 8 段)。
 * ここではデスクトップウィンドウとして読み込むだけで、外部通信は行いません。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function indexPath(){
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow(){
  const win = new BrowserWindow({
    width: 1280,
    height: 900,
    backgroundColor: "#080a10",
    title: "Bada Pharma",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。http(s)/mailto だけ OS の既定アプリへ委譲し、他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")){
      e.preventDefault();
      if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url).catch(() => {}); }
    }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
