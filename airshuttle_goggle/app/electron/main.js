/*
 * main.js — エアシャトル・ゴーグル (AirShuttle Goggle) の Electron ラッパー
 *          (Windows 10/11 EXE / Linux AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (ゴーグル HUD 上の実写映像を、空中で手をかき分けて巻き戻し・早送りするスクラブ卓)。
 *
 * ・ハンド認識に Web カメラを使うため、file:// のページに対して
 *   media パーミッションを明示的に許可します (映像は端末内処理のみ・送信なし)
 * ・外部 URL への遷移は一切許可しません (完全オフラインアプリ)
 */
const { app, BrowserWindow, session, shell } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  // カメラ (media) のみ許可。それ以外の権限要求はすべて拒否する。
  session.defaultSession.setPermissionRequestHandler((wc, permission, callback) => {
    callback(permission === "media" || permission === "fullscreen");
  });
  if (session.defaultSession.setPermissionCheckHandler) {
    session.defaultSession.setPermissionCheckHandler((wc, permission) => permission === "media");
  }

  const win = new BrowserWindow({
    width: 1280,
    height: 900,
    backgroundColor: "#04060b",
    title: "エアシャトル・ゴーグル — AirShuttle Goggle",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  // 外部リンクは開かない (このアプリはネットワークを使いません)
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });
  // HUD の全画面表示 (⛶ ボタン) に追随
  win.webContents.on("enter-html-full-screen", () => win.setFullScreen(true));
  win.webContents.on("leave-html-full-screen", () => win.setFullScreen(false));

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
