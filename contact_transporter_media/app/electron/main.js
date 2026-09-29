/*
 * main.js — Blueprint Studio の Electron ラッパー (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * 輸送機設計図作成ソフト / ChatGPT 設計図作成ソフト / UFO 設計図作成ソフト で共通。
 * アプリ本体は www/index.html (自己完結: 3D 描画・設計図 PDF・WebCodecs による mp4 書き出し)。
 * 表示名は package.json の "blueprint.displayName" を使う。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const pkg = require("./package.json");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 940,
    backgroundColor: "#0b2447",
    title: (pkg.blueprint && pkg.blueprint.displayName) || pkg.productName,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://") && !url.startsWith("blob:")) e.preventDefault();
  });
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
