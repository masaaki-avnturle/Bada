/*
 * main.js — Contact Transporter Studio の Electron ラッパー
 *          (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html (tools/build.js が生成する自己完結 HTML)。
 * 書き出し (STL / OBJ / DXF / SVG / PNG / JSON) は保存ダイアログで保存します。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

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
  // <a download> → 保存ダイアログ
  win.webContents.session.on("will-download", (_e, item) => {
    item.setSaveDialogOptions({ defaultPath: path.join(app.getPath("documents"), item.getFilename()) });
  });
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
