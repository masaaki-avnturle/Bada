/*
 * main.js — InstantOn の Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 「電源を切ると状態をディスクに保存し、次の電源投入で通常ブートを飛ばして
 * いきなり前回の状態から立ち上がる」よう設定します(= 復帰起動 / 高速スタート
 * アップ)。実際の設定・実行は「確認後のみ」ここで行います。
 *
 * アクション:
 *   status         : 現在の休止(ハイバネート/高速起動)設定を表示。
 *   enable         : インスタントオンを有効化(ハイバネート on + 電源オフ=休止 +
 *                    Windows は高速スタートアップ=ハイブリッドブートを有効)。
 *   hibernate-now  : いま休止(次回の電源投入で即復帰)。
 *   disable        : インスタントオンを無効化(通常のシャットダウン/起動へ戻す)。
 */
const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function commandFor(action) {
  const p = process.platform;
  if (p === "linux") {
    switch (action) {
      case "status":  return { sh: "echo 'power states:'; cat /sys/power/state 2>/dev/null; echo; echo 'swap (needed for hibernate/resume):'; swapon --show 2>/dev/null; echo; systemctl show systemd-logind -p HandlePowerKey 2>/dev/null", note: "休止状態 / swap / 電源キー動作を表示" };
      case "enable":  return { sh: "sudo sh -c 'mkdir -p /etc/systemd/logind.conf.d && printf \"[Login]\\nHandlePowerKey=hibernate\\nHandleLidSwitch=hibernate\\n\" > /etc/systemd/logind.conf.d/90-instanton.conf && systemctl restart systemd-logind'", note: "電源キー/フタ閉じ=ハイバネートに設定(要 sudo)" };
      case "hibernate-now": return { sh: "sync && systemctl hibernate", note: "sync → systemctl hibernate" };
      case "disable": return { sh: "sudo sh -c 'rm -f /etc/systemd/logind.conf.d/90-instanton.conf && systemctl restart systemd-logind'", note: "設定を削除して通常動作へ(要 sudo)" };
    }
  } else if (p === "win32") {
    switch (action) {
      case "status":  return { sh: "powercfg /a & reg query \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power\" /v HiberbootEnabled", note: "利用可能なスリープ状態 / 高速起動フラグを表示" };
      case "enable":  return { sh: "powercfg /hibernate on & reg add \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power\" /v HiberbootEnabled /t REG_DWORD /d 1 /f & powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2 & powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2 & powercfg -SETACTIVE SCHEME_CURRENT", note: "ハイバネート on + 高速スタートアップ on + 電源ボタン=休止(要 管理者)" };
      case "hibernate-now": return { sh: "shutdown /h", note: "shutdown /h" };
      case "disable": return { sh: "reg add \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power\" /v HiberbootEnabled /t REG_DWORD /d 0 /f", note: "高速スタートアップ off(要 管理者)" };
    }
  } else if (p === "darwin") {
    switch (action) {
      case "status":  return { sh: "pmset -g | grep -E 'hibernatemode|standby'", note: "hibernatemode を表示" };
      case "enable":  return { sh: "sudo pmset -a hibernatemode 25", note: "純ハイバネート(要 sudo)" };
      case "hibernate-now": return { sh: "sync && pmset sleepnow", note: "sync → sleep" };
      case "disable": return { sh: "sudo pmset -a hibernatemode 3", note: "既定のセーフスリープへ(要 sudo)" };
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

ipcMain.handle("instanton:preview", (_e, action) => {
  const c = commandFor(action);
  return c ? { platform: process.platform, command: c.sh, note: c.note } : { platform: process.platform, command: null };
});
ipcMain.handle("instanton:run", async (_e, action) => {
  const c = commandFor(action);
  if (!c) return { ok: false, err: "この OS では未対応のアクションです" };
  const r = await run(c.sh);
  return { ...r, command: c.sh };
});

function createWindow() {
  const win = new BrowserWindow({
    width: 780, height: 760, backgroundColor: "#04060a",
    title: "InstantOn — 瞬間起動",
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
