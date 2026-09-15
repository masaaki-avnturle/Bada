/*
 * main.js — Bada QCrypt (量子暗号ソフト) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (Bada 量子言語インタープリタ + BB84 量子鍵配送 + ワンタイムパッド +
 *  量子金庫 + 量子検疫室 + Bada プログラム室)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 * 鍵はメモリ内のみ、金庫と封印は localStorage (Electron の userData 配下)
 * に暗号文だけが保存されます。通信は一切行いません。
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
    width: 1100,
    height: 860,
    backgroundColor: "#0b0e14",
    title: "Bada QCrypt",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結・オフライン。外部 URL は既定ブラウザへ委譲し、他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) { e.preventDefault(); }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
