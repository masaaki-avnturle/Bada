/*
 * main.js — Bada VM Pro の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * OS 本体は www/index.html に完全自己完結しています
 * (ブラウザーデザインのシェル + BadaGPT カーネル + Bada on Rails +
 *  量子 Bada インタープリタ + 合い言葉コマンド + Transformer +
 *  GUI/CUI プログラミング)。ここではデスクトップウィンドウとして
 * 読み込むだけで、外部リンクは OS の既定ブラウザへ渡します。
 * 状態 (OS バージョン・Rails DB・GUI フォーム等) は localStorage
 * (Electron の userData 配下) に永続化されます。
 */
const { app, BrowserWindow, shell, session } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1360,
    height: 880,
    backgroundColor: "#0b0e14",
    title: "Bada VM Pro",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* 合い言葉の音声モード: マイク許可のみ自動許可 */
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => {
    cb(permission === "media");
  });

  /* OS は自己完結。new-window / 外部遷移は既定ブラウザへ委譲または抑止 */
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
