/*
 * main.js — Bada Baumkuchen (優しさのソース検索・蓄積) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (検索・値札・DNA スイッチ・種数・後ろからの逆走査・Canvas 描画)。
 * ここではデスクトップウィンドウとして読み込むだけです。
 *
 * 蓄積は localStorage に入ります。file:// のままだと Chromium が
 * localStorage を拒むことがあるため、www/ を app:// という独自スキームで
 * 配信し、安定した origin (app://baumkuchen) を与えています。
 * これで OS を再起動しても層が残ります。
 * JSON / CSV の書き出しはアプリ内のボタンから、Electron 標準の
 * ダウンロード保存として行われます。
 */
const { app, BrowserWindow, shell, protocol, net } = require("electron");
const path = require("path");
const url = require("url");

const SCHEME = "app";
const HOST = "baumkuchen";

function wwwRoot() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www")
    : path.join(__dirname, "..", "www");
}

/* app:// を「標準スキーム」として登録する (localStorage 等が使えるようになる) */
protocol.registerSchemesAsPrivileged([
  {
    scheme: SCHEME,
    privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true }
  }
]);

function registerProtocol() {
  protocol.handle(SCHEME, (request) => {
    const { pathname } = new URL(request.url);
    const rel = decodeURIComponent(pathname === "/" || pathname === "" ? "/index.html" : pathname);
    /* www/ の外へ出る参照は拒否する */
    const target = path.join(wwwRoot(), path.normalize(rel));
    if (!target.startsWith(wwwRoot())) {
      return new Response("forbidden", { status: 403 });
    }
    return net.fetch(url.pathToFileURL(target).toString());
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 940,
    backgroundColor: "#0b0e14",
    title: "Bada Baumkuchen",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。外部リンクは既定ブラウザへ、その他は抑止 */
  win.webContents.setWindowOpenHandler(({ url: target }) => {
    if (/^https?:/i.test(target)) { shell.openExternal(target); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, target) => {
    if (!target.startsWith(SCHEME + "://") && !target.startsWith("blob:")) {
      e.preventDefault();
    }
  });

  win.loadURL(SCHEME + "://" + HOST + "/index.html");
}

app.whenReady().then(() => {
  registerProtocol();
  createWindow();
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
