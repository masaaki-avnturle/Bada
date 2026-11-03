/*
 * main.js — Bada QuantumShield の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html + www/qshield.js + www/qcrypto.js に
 * 完全自己完結しています (量子鍵同期のクレデンシャル・ローテーションを
 * ページ内で実装、通信は一切行いません — 防御の概念シミュレーション)。
 * ここではデスクトップ ウィンドウとして読み込みます。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function wwwPath(f) {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", f)
    : path.join(__dirname, "..", "www", f);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1040,
    height: 880,
    backgroundColor: "#04060a",
    title: "Bada QuantumShield",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* 外部 http(s) リンクは OS の既定ブラウザへ、それ以外の遷移は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) {
      e.preventDefault();
      if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    }
  });

  win.loadFile(wwwPath("index.html"));
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
