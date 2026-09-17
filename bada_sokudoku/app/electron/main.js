/*
 * main.js — Bada 瞬読 (速読スタジオ) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (Sauvola 適応二値化 + パッチ埋め込み + 窓自己注意 (Swin 型) + 注意ロールアウト +
 *  行と固まりの投影分割 + XY-cut の読み順 + 速読スケジューラ + canvas 録画)。
 * ここではデスクトップウィンドウとして読み込むだけです。ネットワークは一切使いません。
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
    width: 1240,
    height: 940,
    backgroundColor: "#0b0e14",
    title: "Bada 瞬読",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。外部リンクは OS の既定ブラウザへ委譲、その他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
