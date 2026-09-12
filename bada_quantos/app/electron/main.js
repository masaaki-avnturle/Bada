/*
 * main.js — Bada QuantOS (擬似量子OS) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (擬似量子カーネル + トポロジー写像機構 + 生成AIカーネル +
 *  電話 / SMS / メール / カメラ / 時計 / 電卓 / メモ / ファイル / 連絡先)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 * デスクトップには電話回線が無いため、tel:/sms: はアプリ内で
 * 「発行予定のインテント」を表示し、mailto: は既定メールアプリへ、
 * http(s) は既定ブラウザへ委譲します。
 * 連絡先・メモ・写真などは localStorage (Electron の userData 配下) に
 * 永続化されます。
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
    title: "Bada QuantOS",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。外部プロトコルは OS へ委譲、その他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) {
      e.preventDefault();
      if (/^(mailto|tel|sms):/i.test(url)) { shell.openExternal(url).catch(() => {}); }
    }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
