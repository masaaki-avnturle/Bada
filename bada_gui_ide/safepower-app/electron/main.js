/*
 * main.js — SafePower の Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 実際の OS 電源操作を「確認後のみ」実行します。ここが唯一のネイティブ経路で、
 * ブラウザ単体や Android では実行できません(表示のみ)。
 *
 * 対応アクション:
 *   safe-off   : sync でバッファを書き出してからハイバネート(状態をディスク保存
 *                して電源断)。突然の電源断でも安全。
 *   suspend    : サスペンド(RAM保存)。省電力だが電源を切ると失われる。
 *   shutdown   : sync してからクリーン シャットダウン。
 *   rehalt     : 再起動せずに OS を再ロード。Linux は systemctl soft-reboot
 *                (カーネル維持), フォールバックで kexec。Windows はシェル再起動。
 */
const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

/* platform command map — each entry is [cmd, args, human-readable string] */
function commandFor(action) {
  const p = process.platform;
  if (p === "linux") {
    switch (action) {
      case "safe-off":  return { sh: "sync && systemctl hibernate", note: "sync → systemctl hibernate" };
      case "suspend":   return { sh: "sync && systemctl suspend",   note: "sync → systemctl suspend" };
      case "shutdown":  return { sh: "sync && systemctl poweroff",  note: "sync → systemctl poweroff" };
      case "rehalt":    return { sh: "systemctl soft-reboot || systemctl kexec || systemctl reboot",
                                 note: "systemctl soft-reboot (fallback: kexec / reboot)" };
    }
  } else if (p === "win32") {
    switch (action) {
      case "safe-off":  return { sh: "shutdown /h",                 note: "shutdown /h (ハイバネート)" };
      case "suspend":   return { sh: "rundll32.exe powrprof.dll,SetSuspendState 0,1,0", note: "SetSuspendState (スリープ)" };
      case "shutdown":  return { sh: "shutdown /s /t 0",            note: "shutdown /s /t 0" };
      case "rehalt":    return { sh: "taskkill /f /im explorer.exe & start explorer.exe",
                                 note: "explorer 再起動 (シェル/セッション再ロード)" };
    }
  } else if (p === "darwin") {
    switch (action) {
      case "safe-off":  return { sh: "sync && pmset -a hibernatemode 25 && pmset sleepnow", note: "sync → hibernate → sleep" };
      case "suspend":   return { sh: "pmset sleepnow",              note: "pmset sleepnow" };
      case "shutdown":  return { sh: "sync && osascript -e 'tell app \"System Events\" to shut down'", note: "sync → shut down" };
      case "rehalt":    return { sh: "osascript -e 'tell app \"System Events\" to restart'", note: "restart" };
    }
  }
  return null;
}

function run(sh) {
  return new Promise((resolve) => {
    const p = process.platform === "win32"
      ? spawn("cmd.exe", ["/c", sh], { windowsHide: true })
      : spawn("/bin/sh", ["-c", sh]);
    let out = "", err = "";
    p.stdout.on("data", d => out += d);
    p.stderr.on("data", d => err += d);
    p.on("error", e => resolve({ ok: false, code: -1, out, err: String(e) }));
    p.on("close", code => resolve({ ok: code === 0, code, out, err }));
  });
}

/* the renderer must have confirmed; main just maps + runs */
ipcMain.handle("safepower:preview", (_e, action) => {
  const c = commandFor(action);
  return c ? { platform: process.platform, command: c.sh, note: c.note } : { platform: process.platform, command: null };
});
ipcMain.handle("safepower:run", async (_e, action) => {
  const c = commandFor(action);
  if (!c) return { ok: false, err: "この OS では未対応のアクションです" };
  const r = await run(c.sh);
  return { ...r, command: c.sh };
});

function createWindow() {
  const win = new BrowserWindow({
    width: 760, height: 720, backgroundColor: "#04060a",
    title: "SafePower — 安全オフ / rehalt",
    webPreferences: { contextIsolation: true, nodeIntegration: false, preload: path.join(__dirname, "preload.js") }
  });
  win.setMenuBarVisibility(false);
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    return { action: "deny" };
  });
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
