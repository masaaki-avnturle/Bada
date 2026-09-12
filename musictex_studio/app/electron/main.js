/*
 * main.js — MusicTeX Studio の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (MusixTeX エディタ + テンプレート + ライブ楽譜プレビュー +
 *  Web Audio 試聴 + .tex 書き出し)。ここではデスクトップウィンドウとして
 * 読み込むだけで、外部リンクは OS の既定ブラウザへ渡します。
 * 「⬇ .tex 保存」は Electron 標準のダウンロード処理で保存ダイアログが開きます。
 * 印刷用 PDF は texlive-music の `musixtex -p score.tex` で組版してください。
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
    width: 1280,
    height: 860,
    backgroundColor: "#0b0e14",
    title: "MusicTeX Studio",
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
