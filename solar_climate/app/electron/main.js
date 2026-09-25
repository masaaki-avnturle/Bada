/*
 * main.js — Bada SolarCast の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています。
 * file:// から NOAA SWPC / Open-Meteo の公開 API を fetch するため、
 * その 2 系統のホストに限って CORS 応答ヘッダを補います
 * (API 側が CORS を返さない場合でもデスクトップ版が動くように)。
 */
const { app, BrowserWindow, shell, session } = require("electron");
const path = require("path");

const API_HOSTS = [
  "https://services.swpc.noaa.gov/*",
  "https://api.open-meteo.com/*",
  "https://archive-api.open-meteo.com/*",
  "https://ensemble-api.open-meteo.com/*",
  "https://geocoding-api.open-meteo.com/*"
];

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 900,
    backgroundColor: "#0d1117",
    title: "Bada SolarCast",
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
    if (!url.startsWith("file://")) { e.preventDefault(); shell.openExternal(url); }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(() => {
  session.defaultSession.webRequest.onHeadersReceived({ urls: API_HOSTS }, (details, callback) => {
    const headers = Object.assign({}, details.responseHeaders);
    for (const k of Object.keys(headers)) {
      if (k.toLowerCase() === "access-control-allow-origin") delete headers[k];
    }
    headers["Access-Control-Allow-Origin"] = ["*"];
    callback({ responseHeaders: headers });
  });
  createWindow();
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
