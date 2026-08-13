/*
 * main.js — Electron wrapper for Ω-Vim (Windows 10/11 EXE, Linux AppImage/deb).
 *
 * Ω-Vim: a Bada-language modal editor with a grammar checker, parser completion,
 * indent completion, and the complex-rotation spinning-top code fix. The whole
 * editor engine runs inside the bundled web page (www/) — no server, no Ruby.
 */
const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1040,
    height: 760,
    backgroundColor: "#04060a",
    title: "Ω-Vim",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  Menu.setApplicationMenu(null);
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
