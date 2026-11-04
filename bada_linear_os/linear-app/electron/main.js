/* main.js — 反重力リニア BadaLinear の Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 * 本体は www/index.html に完全自己完結 (WebGL 3D 運行シミュレータ + 設計図 + BadaLinear-OS 物理コア + 同梱 three.min.js)。 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const indexPath = () => app.isPackaged ? path.join(process.resourcesPath, "www", "index.html") : path.join(__dirname, "..", "www", "index.html");
function createWindow() {
  const win = new BrowserWindow({ width: 1280, height: 860, backgroundColor: "#0a2748", title: "反重力リニア — BadaLinear",
    webPreferences: { contextIsolation: true, nodeIntegration: false, preload: path.join(__dirname, "preload.js") } });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:\/\//i.test(url)) shell.openExternal(url); return { action: "deny" }; });
  win.webContents.on("will-navigate", (e, url) => { if (!url.startsWith("file://")) e.preventDefault(); });
  win.loadFile(indexPath());
}
app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
