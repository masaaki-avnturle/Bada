/*
 * main.js — Bada QuantumCrypto の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html + www/qcrypto.js に完全自己完結しています
 * (Jones 多項式鍵導出・Bell 対 QKD・ChaCha20/HMAC AEAD をページ内で実装、
 * 通信は一切行いません)。ここではデスクトップ ウィンドウとして読み込み、
 * 暗号化/復号結果のダウンロードには保存ダイアログを出します。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function wwwPath(f) {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", f)
    : path.join(__dirname, "..", "www", f);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 980,
    height: 860,
    backgroundColor: "#04060a",
    title: "Bada QuantumCrypto",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* <a download> による保存は常に保存ダイアログを表示する */
  win.webContents.session.on("will-download", (event, item) => {
    item.setSaveDialogOptions({ title: "保存先を選択", defaultPath: item.getFilename() });
  });

  /* 外部 http(s) リンクは OS の既定ブラウザへ、それ以外の遷移は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) {
      e.preventDefault();
      if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    }
  });

  win.loadFile(wwwPath("index.html"));
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
