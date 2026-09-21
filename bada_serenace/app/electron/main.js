/*
 * main.js — Bada Serenace (病気予防機構の解明) の Electron ラッパー
 *          (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * アプリ本体は www/index.html に完全自己完結しています
 * (Γ 大域的部分積分多様体の熱感知 + Kauffman/Jones 不変量 + 積み木の真逆 +
 *  DNA 暗号 + 病識モデル + 思考漏洩チャネル + RNA 干渉設計 + 受容体占有モデル)。
 * ここではデスクトップウィンドウとして読み込むだけで、外部通信は行いません。
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

function indexPath(){
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow(){
  const win = new BrowserWindow({
    width: 1240,
    height: 880,
    backgroundColor: "#070b12",
    title: "Bada Serenace",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);

  /* アプリは自己完結。http(s)/mailto だけ OS の既定アプリへ委譲し、他は抑止 */
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url); }
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")){
      e.preventDefault();
      if (/^(https?|mailto):/i.test(url)) { shell.openExternal(url).catch(() => {}); }
    }
  });

  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
