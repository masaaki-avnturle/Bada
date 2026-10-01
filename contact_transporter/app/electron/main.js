/*
 * main.js — Contact Transporter Studio の Electron ラッパー
 *          (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html (tools/build.js が生成する自己完結 HTML)。
 * 書き出し (アプリ・APK・deb・PDF・STL など) は OS の「ダウンロード」フォルダへ保存します。
 * ファイルの取り込み (論文 PDF・Bada ソース・設計値 JSON・重み) は OS 標準の「開く」ダイアログ
 * (dialog.showOpenDialog) で行い、preload.js の window.ctNative から呼びます。
 */
const { app, BrowserWindow, shell, dialog, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "..", "dist", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    backgroundColor: "#070b14",
    title: "Contact Transporter Studio",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });
  // <a download> → OS の「ダウンロード」フォルダへ直接保存 (同名があれば (1), (2) … を付ける)
  win.webContents.session.on("will-download", (_e, item) => {
    const dir = app.getPath("downloads"), name = item.getFilename();
    const ext = path.extname(name), stem = name.slice(0, name.length - ext.length);
    let target = path.join(dir, name);
    for (let k = 1; fs.existsSync(target); k++) target = path.join(dir, `${stem} (${k})${ext}`);
    item.setSavePath(target);
    item.once("done", (_ev, state) => {
      if (state === "completed") win.webContents.executeJavaScript(`window.dispatchEvent(new CustomEvent("ct-saved", { detail: ${JSON.stringify(target)} }))`).catch(() => {});
    });
  });
  win.loadFile(indexPath());
}

// ファイルを開く: OS 標準のダイアログ → {name, data (Uint8Array)}。取り消しは null
ipcMain.handle("ct-open-file", async (e, opts) => {
  opts = opts || {};
  const win = BrowserWindow.fromWebContents(e.sender);
  const filters = [];
  if (opts.extensions && opts.extensions.length) filters.push({ name: opts.name || "ファイル", extensions: opts.extensions });
  filters.push({ name: "すべてのファイル", extensions: ["*"] });
  const r = await dialog.showOpenDialog(win, { title: opts.title || "ファイルを開く", defaultPath: app.getPath("downloads"), properties: ["openFile"], filters });
  if (r.canceled || !r.filePaths.length) return null;
  const f = r.filePaths[0];
  return { name: path.basename(f), path: f, data: new Uint8Array(fs.readFileSync(f)) };
});
// ダウンロード フォルダ (保存先) をエクスプローラー / ファイル マネージャーで開く
ipcMain.handle("ct-show-downloads", async (_e, file) => {
  if (file && fs.existsSync(file)) { shell.showItemInFolder(file); return true; }
  const err = await shell.openPath(app.getPath("downloads"));
  return !err;
});

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
