/*
 * main.js — Bada 映画カウントダウンエディタ の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html + www/countdown.js に完全自己完結
 * (フィルムリーダー生成・プレビュー・WebM/PNG/JSON/HTML 書き出しを
 * ページ内で実装、通信は一切行いません)。
 */
const { app, BrowserWindow, shell, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");

function wwwPath(f) {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", f)
    : path.join(__dirname, "..", "www", f);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 820,
    backgroundColor: "#07090d",
    title: "Bada 映画カウントダウンエディタ",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* <a download> (PNG/WebM/JSON/HTML 書き出し) は保存ダイアログを表示 */
  win.webContents.session.on("will-download", (event, item) => {
    item.setSaveDialogOptions({ title: "保存先を選択", defaultPath: item.getFilename() });
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) { e.preventDefault(); if (/^https?:\/\//i.test(url)) shell.openExternal(url); }
  });

  win.loadFile(wwwPath("index.html"));
}

/* 単体HTMLプレーヤー書き出しにエンジン本体を同梱するため、ソースを読んで渡す */
ipcMain.handle("engine-source", () => {
  try { return fs.readFileSync(wwwPath("countdown.js"), "utf8"); }
  catch (e) { return { error: e.message }; }
});

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
