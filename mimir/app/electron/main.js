/*
 * main.js — Mimir の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (ARグラス・コンシェルジュ「ミーミル」+ 特殊相対論の光路差反射システム +
 *  単眼ミラー / 両眼 SBS 投影 + 画像・文章の HUD 投影)。
 * ここではデスクトップウィンドウとして読み込むだけで、
 * 外部リンクは OS の既定ブラウザへ渡します。
 * 「別ウィンドウ投影」(about:blank の HUD ウィンドウ) は子ウィンドウとして
 * 許可し、AR グラス側ディスプレイへ移動できるようにします。
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
    backgroundColor: "#05070d",
    title: "Mimir — ARグラス・コンシェルジュ",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    // HUD 投影用の空ウィンドウ (window.open("")) は許可
    if (url === "about:blank" || url === "") {
      return {
        action: "allow",
        overrideBrowserWindowOptions: {
          backgroundColor: "#000000",
          autoHideMenuBar: true,
          title: "Mimir HUD",
          webPreferences: { contextIsolation: true, nodeIntegration: false }
        }
      };
    }
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
