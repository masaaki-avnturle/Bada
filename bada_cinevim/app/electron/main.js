/*
 * main.js — Bada CineVim (量子言語 Bada の映画的 VIM エディタ) の
 *           Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (VIM エンジン + 多段落の文章ビュー + 拡大鏡ポインタ
 *  + シネマフォーカス + イベント処理のフラッシュ効果
 *  + 映画のカウントダウン + 量子 Bada ランタイム)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 *   :w  → Electron 標準の保存ダイアログ
 *   :e  → ファイル選択ダイアログ
 * メニューバーは VIM のキー操作を邪魔しないよう隠しています
 * (F11 で全画面、Ctrl+Shift+I で開発者ツール)。
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
    height: 940,
    minWidth: 720,
    minHeight: 480,
    backgroundColor: "#05070c",
    title: "Bada CineVim",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);
  win.setAutoHideMenuBar(true);

  /* VIM の :q は画面内メッセージで完結させ、ウィンドウは閉じません。
     外部リンクだけ既定ブラウザへ逃がし、それ以外の遷移は抑止します。 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://") && !url.startsWith("blob:")) {
      e.preventDefault();
    }
  });

  /* F11 = 全画面 (映画のどアップを最大化するため) */
  win.webContents.on("before-input-event", (e, input) => {
    if (input.type === "keyDown" && input.key === "F11") {
      win.setFullScreen(!win.isFullScreen());
      e.preventDefault();
    }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
