/*
 * main.js — Bada UltraNetwork の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (HD-PLC ウェーブレット OFDM 物理層 + NTT 回線写像 φ + 音声帯 16-QAM
 *  モデム + zone:// P2P リング DHT + Jones 多項式量子暗号 + LINE /
 *  Instagram メッセージ多重化 + AT&T ベル研究所式 STREAMS)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 *
 * デスクトップには電話回線が無いため、写像した NTT 番号への tel: は
 * OS の既定ハンドラへ委譲し、http(s) は既定ブラウザへ渡します。
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
    height: 900,
    backgroundColor: "#0b0e14",
    title: "Bada UltraNetwork",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。外部プロトコルは OS へ委譲、その他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^(https?|mailto|tel|sms):/i.test(url)) { shell.openExternal(url).catch(() => {}); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) {
      e.preventDefault();
      if (/^(https?|mailto|tel|sms):/i.test(url)) { shell.openExternal(url).catch(() => {}); }
    }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
