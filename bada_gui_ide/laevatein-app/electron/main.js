/*
 * main.js — LÆVATEIN (Λ ドライバ無力化シミュレータ) の Electron ラッパー
 *           (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 本体は www/index.html に完全自己完結しています (モデルコア
 * www/lambda_driver.js を inline 済み)。ここではデスクトップ ウィンドウ
 * として読み込み、CSV / JSON のダウンロードを「名前を付けて保存」
 * ダイアログに繋ぎ、外部 http(s):// リンクだけを OS の既定ブラウザへ渡します。
 */
const { app, BrowserWindow, shell, dialog } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#04060a",
    title: "LÆVATEIN — Λ ドライバ無力化シミュレータ",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* CSV / JSON の書き出しは「名前を付けて保存」で受ける */
  win.webContents.session.on("will-download", (e, item) => {
    const to = dialog.showSaveDialogSync(win, {
      title: "LÆVATEIN — 出力を保存",
      defaultPath: path.join(app.getPath("downloads"), item.getFilename())
    });
    if (!to) { item.cancel(); return; }
    item.setSavePath(to);
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
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
