/*
 * main.js — Bada GUI IDE の Electron ラッパー (Windows 10/11 EXE / Ubuntu AppImage・deb)
 *
 * ドロップされた .bada は www/ の IDE が処理します。ここではデスクトップ専用の
 * ネイティブ経路 (生成 C を gcc/cc/clang でコンパイル&リンクして実行) と
 * ファイル保存ダイアログを IPC で提供します。
 */
const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const fs = require("fs");
const os = require("os");
const { spawnSync } = require("child_process");

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "www", "index.html")
    : path.join(__dirname, "..", "www", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 840,
    backgroundColor: "#04060a",
    title: "Bada GUI IDE",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}

/* 使用可能な C コンパイラを探す (gcc → cc → clang, Windows は gcc/MinGW) */
function findCompiler() {
  const candidates = process.platform === "win32"
    ? ["gcc", "cc", "clang"]
    : ["gcc", "cc", "clang"];
  for (const c of candidates) {
    const probe = spawnSync(c, ["--version"], { encoding: "utf8", timeout: 8000, shell: false });
    if (probe.status === 0) return c;
  }
  return null;
}

ipcMain.handle("bada:buildAndRun", (_ev, cSource) => {
  const cc = findCompiler();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bada-build-"));
  const cFile = path.join(dir, "program.gen.c");
  const exe = path.join(dir, process.platform === "win32" ? "program.exe" : "program");
  fs.writeFileSync(cFile, cSource, "utf8");

  if (!cc) {
    return {
      ok: false,
      command: "(C compiler not found)",
      compileLog: "",
      error:
        "gcc / cc / clang が見つかりません。\n" +
        (process.platform === "win32"
          ? "Windows では MinGW-w64 (https://www.mingw-w64.org/) をインストールして PATH に追加してください。\n"
          : "Ubuntu では:  sudo apt install build-essential\n") +
        "生成された C は保存できます: " + cFile
    };
  }

  const args = ["-O2", "-o", exe, cFile, "-lm"];
  const command = cc + " " + args.join(" ");
  const build = spawnSync(cc, args, { encoding: "utf8", timeout: 60000, shell: false });
  if (build.status !== 0) {
    return {
      ok: false,
      command,
      compileLog: (build.stdout || "") + (build.stderr || ""),
      error: "コンパイル&リンクに失敗しました (exit " + build.status + ")"
    };
  }
  const run = spawnSync(exe, [], { encoding: "utf8", timeout: 30000, shell: false });
  return {
    ok: true,
    command,
    compileLog: (build.stdout || "") + (build.stderr || ""),
    exePath: exe,
    runOutput: (run.stdout || "") + (run.stderr || "")
  };
});

ipcMain.handle("bada:saveFile", async (_ev, name, text) => {
  const win = BrowserWindow.getFocusedWindow();
  const r = await dialog.showSaveDialog(win, { defaultPath: name });
  if (r.canceled || !r.filePath) return { ok: false };
  fs.writeFileSync(r.filePath, text, "utf8");
  return { ok: true, path: r.filePath };
});

ipcMain.handle("bada:exportBinary", async (_ev, srcPath) => {
  const win = BrowserWindow.getFocusedWindow();
  const base = path.basename(srcPath);
  const r = await dialog.showSaveDialog(win, { defaultPath: base });
  if (r.canceled || !r.filePath) return { ok: false };
  fs.copyFileSync(srcPath, r.filePath);
  if (process.platform !== "win32") fs.chmodSync(r.filePath, 0o755);
  return { ok: true, path: r.filePath };
});

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
