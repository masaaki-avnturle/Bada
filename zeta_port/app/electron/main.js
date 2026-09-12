/*
 * main.js — ゼータ・ポート (ZetaPort) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (Bada 言語コア + zeta_port.bada を内蔵。Riemann–Siegel Z(t) の走査、
 *  関数等式の形のエントロピー S(t)、□·□⁻ = 1 ゲート検出、
 *  ポート開閉時刻表と port:// 住所・天球座標の計算はすべて Bada 側)。
 * ここではデスクトップウィンドウとして読み込むだけで、
 * 外部リンクは OS の既定ブラウザへ渡します。
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
    height: 860,
    backgroundColor: "#04060a",
    title: "ゼータ・ポート — 異次元ポート開閉時刻表",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

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
