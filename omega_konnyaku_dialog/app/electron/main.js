/*
 * main.js — こんにゃく照合器 の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (4 つの箱の方程式と絵 + 入力ダイアログ + 形と数値のエントロピー照合 +
 *  同値類 ≡ + こんにゃく弾力性・優しさ・カインの門 +
 *  ハッシュ連鎖のアカシックレコード)。
 * ここではデスクトップウィンドウとして読み込むだけで、
 * 外部リンクは OS の既定ブラウザへ渡します。
 * 入力と台帳は localStorage (Electron の userData 配下) に永続化されます。
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
    width: 1180,
    height: 900,
    backgroundColor: "#0b0f14",
    title: "こんにゃく照合器",
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
