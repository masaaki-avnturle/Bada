/*
 * main.js — Migemogram Media の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 本体は www/index.html に完全自己完結しています。ここではデスクトップ
 * ウィンドウとして読み込みます。Google OAuth(Drive/Photos 連携)は
 * file:// では動かないため、ローカルの http サーバ(127.0.0.1:<port>)で
 * 配信し、その生成元(http://127.0.0.1:PORT)を読み込みます。この生成元を
 * Google Cloud Console の「承認済みの JavaScript 生成元」に登録すると
 * サインインが有効になります。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const http = require("http");
const fs = require("fs");

function wwwDir() {
  return app.isPackaged ? path.join(process.resourcesPath, "www") : path.join(__dirname, "..", "www");
}
var MIME = { ".html":"text/html; charset=utf-8", ".js":"text/javascript", ".css":"text/css", ".json":"application/json",
             ".png":"image/png", ".jpg":"image/jpeg", ".svg":"image/svg+xml", ".ico":"image/x-icon" };

/* A fixed port makes it practical to register the OAuth origin
 * (http://127.0.0.1:8713) in Google Cloud Console once; if it's busy we fall
 * back to a random port (register that one, or free 8713 and relaunch). */
const FIXED_PORT = 8713;
function serve(root) {
  return http.createServer((req, res) => {
    let p = decodeURIComponent((req.url || "/").split("?")[0]);
    if (p === "/" || p === "") p = "/index.html";
    const fp = path.join(root, path.normalize(p).replace(/^([/\\])+/, ""));
    if (!fp.startsWith(root)) { res.writeHead(403); res.end("forbidden"); return; }
    fs.readFile(fp, (err, buf) => {
      if (err) { res.writeHead(404); res.end("not found"); return; }
      res.writeHead(200, { "Content-Type": MIME[path.extname(fp).toLowerCase()] || "application/octet-stream" });
      res.end(buf);
    });
  });
}
function startServer() {
  return new Promise((resolve) => {
    const root = wwwDir();
    const server = serve(root);
    server.once("error", () => {
      const s2 = serve(root);
      s2.listen(0, "127.0.0.1", () => resolve("http://127.0.0.1:" + s2.address().port + "/"));
    });
    server.listen(FIXED_PORT, "127.0.0.1", () => resolve("http://127.0.0.1:" + FIXED_PORT + "/"));
  });
}

function createWindow(url) {
  const win = new BrowserWindow({
    width: 1200, height: 860, backgroundColor: "#04060a",
    title: "Migemogram Media",
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    return { action: "deny" };
  });
  win.loadURL(url);
}

app.whenReady().then(() => startServer().then((url) => createWindow(url)));
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) startServer().then((url) => createWindow(url)); });
