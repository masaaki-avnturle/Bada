/*
 * main.js — クリアキャスト東京 (ClearCast Tokyo) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (東京のテレビ・ラジオを公式デジタル配信で視聴するクリーン視聴アプリ:
 *  在京キー局の公式 YouTube ライブ埋め込み + TVer/NHKプラス/ABEMA/radiko/
 *  らじる★らじる への公式リンク + 回線診断エンジン)。
 *
 * ・ページ内の公式 YouTube 埋め込み (iframe) はアプリ内でそのまま再生
 * ・TVer / radiko などの外部リンクは OS の既定ブラウザへ渡す
 *   (DRM 付き配信は各公式サイト/アプリ側で最良に再生されるため)
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
    title: "クリアキャスト東京 — ClearCast Tokyo",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  // 外部リンク (target=_blank / window.open) は既定ブラウザへ
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    return { action: "deny" };
  });
  // トップレベルのページ遷移は禁止 (iframe 内の遷移は対象外なので埋め込み再生は動く)
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) { e.preventDefault(); shell.openExternal(url); }
  });
  // 埋め込みプレーヤーの全画面を許可
  win.webContents.on("enter-html-full-screen", () => win.setFullScreen(true));
  win.webContents.on("leave-html-full-screen", () => win.setFullScreen(false));

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
