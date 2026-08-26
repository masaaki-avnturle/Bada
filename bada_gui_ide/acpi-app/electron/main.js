/*
 * main.js — ACPI (原子の臨界期の強度シミュレータ) の Electron ラッパー
 *           (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * ACPI 本体は www/index.html に完全自己完結しています (モデルコア
 * www/atom_critical.js を inline 済み)。ここではデスクトップ ウィンドウ
 * として読み込み、CSV / JSON / PNG のダウンロードを「名前を付けて保存」
 * ダイアログに繋ぎ、外部 http(s):// リンクだけを OS の既定ブラウザへ渡します。
 */
const { app, BrowserWindow, shell, dialog } = require("electron");
const path = require("path");
const fs = require("fs");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 920,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#04060a",
    title: "ACPI — 原子の臨界期の強度シミュレータ",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* CSV / JSON / PNG の書き出しは「名前を付けて保存」で受ける */
  win.webContents.session.on("will-download", (e, item) => {
    const to = dialog.showSaveDialogSync(win, {
      title: "ACPI — 出力を保存",
      defaultPath: path.join(app.getPath("downloads"), item.getFilename())
    });
    if (!to) { item.cancel(); return; }
    item.setSavePath(to);
    item.once("done", (_e, state) => {
      if (state === "completed" && fs.existsSync(to)) {
        win.webContents.executeJavaScript(
          "console.log(" + JSON.stringify("saved: " + to) + ")"
        ).catch(() => {});
      }
    });
  });

  /* 外部 http(s) リンクのみ OS の既定ブラウザへ委譲 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
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
