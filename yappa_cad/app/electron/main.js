/*
 * main.js — Yappa CAD (近未来ビークル CAD · Bada 拡張) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (自前 WebGL レンダラ + ビークルテンプレート + 機能設計スペック計算 +
 *  Bada 言語インタープリタ)。ここではデスクトップウィンドウとして
 * 読み込むだけで、外部リンクは OS の既定ブラウザへ渡します。
 * シーン / Bada ソース / マクロの自動保存は localStorage
 * (Electron の userData 配下) に永続化されます。
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
    width: 1440,
    height: 900,
    backgroundColor: "#0b0d12",
    title: "Yappa CAD",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。new-window / 外部遷移は既定ブラウザへ委譲または抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); }
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
