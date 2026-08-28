/*
 * main.js — BadaVM Pro の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 本体は www/index.html に完全自己完結しています:
 *   ① BadaVM Pro   — 量子ハイパーバイザ (VMware Workstation Pro 風オマージュ)
 *   ② BadaOS 12.0  — NetBSD 風ベース + Ubuntu 風 apt のゲスト OS
 *                    (sysinst 風インストーラ / 実ディスク RDM / LILO→MBR+GRUB)
 *   ③ BadaX Server — ASTEC-X 風 X サーバー (JONES-KNOT-COOKIE-1 + Bell対QKD)
 * 3 つとも量子プログラミング言語 Bada で書かれ、同梱の Bada 言語コア
 * (bada.js) がすべてのキー入力を Bada プログラムとして実行します。
 * ここではデスクトップウィンドウとして読み込むだけで、外部リンクは OS の
 * 既定ブラウザへ渡します。ゲストのイベント台帳は localStorage
 * (Electron の userData 配下) に永続化されます。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    backgroundColor: "#1e1f22",
    title: "BadaVM Pro — 量子ハイパーバイザ",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。new-window / 外部遷移は既定ブラウザへ委譲または抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
