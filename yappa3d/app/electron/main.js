/*
 * main.js — Yappa 3D (Bada 3D デザインアプリ) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (自前 WebGL レンダラ + プリミティブ配置 + シーンツリー/インスペクタ +
 *  OBJ/MTL 書き出し + Undo/Redo)。ここではデスクトップウィンドウとして
 * 読み込むだけで、外部リンクは OS の既定ブラウザへ渡します。
 * シーンの自動保存は localStorage (Electron の userData 配下) に永続化されます。
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
    width: 1360,
    height: 860,
    backgroundColor: "#0b0d12",
    title: "Yappa 3D",
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
