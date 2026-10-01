/*
 * main.js — Contact Transporter Studio の Electron ラッパー
 *          (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html (tools/build.js が生成する自己完結 HTML)。
 * 書き出し (アプリ・APK・deb・PDF・STL など) は OS の「ダウンロード」フォルダへ保存します。
 */
const { app, BrowserWindow, shell } = require("electron");
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

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
