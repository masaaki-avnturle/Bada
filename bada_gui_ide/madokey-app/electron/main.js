/*
 * main.js — MadoKey (窓使いのキー) の Electron ラッパー
 *           (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * 設定エディタ (www/index.html) を表示し、そこで編集したキーバインドを
 * Electron の globalShortcut で「本物のグローバル ホットキー」として登録します。
 * ホットキーが押されると、前面のアプリ (Word / Excel / LibreOffice Writer /
 * Calc) を判定して、ルビ・合計・コピー・任意コマンドを送り込みます。
 *
 * 実行方式 (OS 別・追加インストール不要の範囲で動作):
 *   copy/cut/paste/keys/text/sum(Excel) : キー送出
 *      - Windows : PowerShell SendKeys
 *      - Linux   : xdotool  (X11。Wayland は制限あり)
 *   mso <IdMso> / ruby(Word,Excel)      : Windows PowerShell COM ExecuteMso
 *   uno <.uno:Cmd> / sum(Calc) / ruby(Writer):
 *      起動中の LibreOffice に接続 (python3-uno があれば dispatch。無ければ通知)
 *
 * すべて best-effort。対象アプリが無い/接続できない場合も落ちません。
 */
const { app, BrowserWindow, globalShortcut, ipcMain, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

/* ---- combo (ctrl+alt+r) -> Electron accelerator (Ctrl+Alt+R) ---- */
function toAccelerator(combo) {
  const parts = String(combo).split("+").map(s => s.trim()).filter(Boolean);
  const map = { ctrl: "Control", control: "Control", alt: "Alt", shift: "Shift",
                win: "Super", super: "Super", cmd: "Super", meta: "Super" };
  const mods = [], keys = [];
  for (const p of parts) {
    const low = p.toLowerCase();
    if (map[low]) mods.push(map[low]);
    else keys.push(p.length === 1 ? p.toUpperCase() : (p[0].toUpperCase() + p.slice(1)));
  }
  if (!keys.length) return null;
  return mods.concat(keys).join("+");
}

/* ---- run a shell command, resolve without throwing ---- */
function run(cmd, args) {
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { windowsHide: true });
    let out = "", err = "";
    if (p.stdout) p.stdout.on("data", d => out += d);
    if (p.stderr) p.stderr.on("data", d => err += d);
    p.on("error", e => resolve({ ok: false, out, err: String(e) }));
    p.on("close", code => resolve({ ok: code === 0, code, out, err }));
  });
}
function pwsh(script) { return run("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script]); }

/* ---- foreground app -> word/excel/writer/calc/other ---- */
async function detectApp() {
  if (process.platform === "win32") {
    const r = await pwsh(
      "Add-Type 'using System;using System.Runtime.InteropServices;using System.Text;" +
      "public class W{[DllImport(\"user32.dll\")]public static extern IntPtr GetForegroundWindow();" +
      "[DllImport(\"user32.dll\")]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);}';" +
      "$b=New-Object System.Text.StringBuilder 512;[void][W]::GetWindowText([W]::GetForegroundWindow(),$b,512);$b.ToString()");
    const t = (r.out || "").toLowerCase();
    if (t.includes("word")) return "word";
    if (t.includes("excel")) return "excel";
    if (t.includes("calc")) return "calc";
    if (t.includes("writer")) return "writer";
    return "other";
  }
  // Linux / X11
  const r = await run("xdotool", ["getactivewindow", "getwindowname"]);
  const t = (r.out || "").toLowerCase();
  if (t.includes("calc")) return "calc";
  if (t.includes("writer")) return "writer";
  if (t.includes("word")) return "word";
  if (t.includes("excel")) return "excel";
  return "other";
}

/* ---- key emission ---- */
function sendKeysWin(seq) {
  // seq like 'ctrl+c' / 'alt+=' -> SendKeys '^c' / '%='
  const parts = seq.split("+").map(s => s.trim().toLowerCase());
  let pre = "", key = "";
  for (const p of parts) {
    if (p === "ctrl" || p === "control") pre += "^";
    else if (p === "alt") pre += "%";
    else if (p === "shift") pre += "+";
    else if (p === "win" || p === "super") pre += "^"; // no direct Win in SendKeys
    else key = p.length === 1 ? p : "{" + p.toUpperCase() + "}";
  }
  const send = (pre + key).replace(/'/g, "''");
  return pwsh("[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');" +
    "[System.Windows.Forms.SendKeys]::SendWait('" + send + "')");
}
function sendKeysLinux(seq) {
  // 'ctrl+c' -> xdotool key ctrl+c ; 'alt+=' -> alt+equal
  const x = seq.toLowerCase().replace(/\bwin\b|\bsuper\b/g, "super")
              .replace(/=/g, "equal").replace(/\s+/g, "");
  return run("xdotool", ["key", "--clearmodifiers", x]);
}
function emitKeys(seq) { return process.platform === "win32" ? sendKeysWin(seq) : sendKeysLinux(seq); }
function typeText(s) {
  if (process.platform === "win32") {
    const esc = s.replace(/([+^%~(){}])/g, "{$1}").replace(/'/g, "''");
    return pwsh("[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');" +
      "[System.Windows.Forms.SendKeys]::SendWait('" + esc + "')");
  }
  return run("xdotool", ["type", "--clearmodifiers", s]);
}

/* ---- Office automation ---- */
function msoWin(idmso) {
  return pwsh(
    "$a=$null;foreach($p in 'Word.Application','Excel.Application'){try{$a=[Runtime.InteropServices.Marshal]::GetActiveObject($p);break}catch{}};" +
    "if($a){try{$a.CommandBars.ExecuteMso('" + idmso.replace(/'/g, "''") + "')}catch{}}");
}
function unoDispatch(cmd) {
  // best-effort via python3-uno; requires soffice started with --accept socket
  const py =
    "import uno\n" +
    "from com.sun.star.beans import PropertyValue\n" +
    "ctx=uno.getComponentContext()\n" +
    "r=ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',ctx)\n" +
    "c=r.resolve('uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext')\n" +
    "sm=c.ServiceManager\n" +
    "d=sm.createInstanceWithContext('com.sun.star.frame.Desktop',c)\n" +
    "m=d.getCurrentComponent();f=m.getCurrentController().getFrame()\n" +
    "h=sm.createInstanceWithContext('com.sun.star.frame.DispatchHelper',c)\n" +
    "h.executeDispatch(f,'" + cmd.replace(/'/g, "\\'") + "','',0,())\n";
  return run(process.platform === "win32" ? "python" : "python3", ["-c", py]);
}

async function execute(bind) {
  const [combo, appScope, action, arg] = bind;
  const appNow = await detectApp();
  try {
    if (action === "copy") return emitKeys("ctrl+c");
    if (action === "cut") return emitKeys("ctrl+x");
    if (action === "paste") return emitKeys("ctrl+v");
    if (action === "keys") return emitKeys(arg || "");
    if (action === "text") return typeText(arg || "");
    if (action === "run") { spawn(arg, { shell: true, detached: true }).unref(); return; }
    if (action === "mso") return process.platform === "win32" ? msoWin(arg) : null;
    if (action === "uno") return unoDispatch(arg);
    if (action === "reload") { win && win.reload(); return; }
    if (action === "quit") { app.quit(); return; }
    if (action === "ruby") {
      if (appNow === "word") return process.platform === "win32" ? msoWin("PhoneticGuide") : null;
      if (appNow === "excel") return process.platform === "win32" ? msoWin("PhoneticShowOrHide") : null;
      if (appNow === "writer") return unoDispatch(".uno:RubyDialog");
      return;
    }
    if (action === "sum") {
      if (appNow === "excel") return emitKeys("alt+=");
      if (appNow === "calc") return unoDispatch(".uno:AutoSum");
      return;
    }
  } catch (e) { /* never crash on a hotkey */ }
}

/* ---- (re)register the current binds as global shortcuts ---- */
let CURRENT = [];
function registerBinds(binds) {
  globalShortcut.unregisterAll();
  CURRENT = Array.isArray(binds) ? binds : [];
  // group binds by accelerator; on trigger pick the one matching the focused app
  const byAcc = {};
  for (const b of CURRENT) {
    const acc = toAccelerator(b[0]);
    if (!acc) continue;
    (byAcc[acc] = byAcc[acc] || []).push(b);
  }
  let n = 0;
  for (const acc of Object.keys(byAcc)) {
    const group = byAcc[acc];
    const ok = globalShortcut.register(acc, async () => {
      const appNow = await detectApp();
      let pick = group.find(b => (b[1] || "any") === appNow);
      if (!pick) pick = group.find(b => (b[1] || "any") === "any");
      if (!pick) pick = group[0];
      execute(pick);
    });
    if (ok) n++;
  }
  return n;
}
ipcMain.handle("madokey:setBinds", (_e, binds) => ({ registered: registerBinds(binds), platform: process.platform }));

/* ---- window ---- */
let win = null;
function createWindow() {
  win = new BrowserWindow({
    width: 1000, height: 820, backgroundColor: "#04060a",
    title: "MadoKey — 窓使いのキー",
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
app.on("will-quit", () => globalShortcut.unregisterAll());
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
