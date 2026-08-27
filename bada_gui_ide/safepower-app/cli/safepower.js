#!/usr/bin/env node
/* ============================================================================
 * safepower.js — SafePower command-line tool.
 *
 *   node safepower.js safe-off    # sync + hibernate  (状態をディスク保存→電源断: 突然の電源断でも安全)
 *   node safepower.js suspend     # サスペンド (RAM保存)
 *   node safepower.js shutdown    # sync + クリーン シャットダウン
 *   node safepower.js rehalt      # 再起動せずに OS を再ロード (Linux: systemctl soft-reboot / kexec)
 *   node safepower.js <action> --dry-run   # 実行せずコマンドだけ表示
 *
 * これはあなた自身の PC を対象にした操作です。実行には権限(Linux は polkit/
 * sudo、Windows は管理者)が必要な場合があります。--dry-run で内容を確認できます。
 * ============================================================================ */
"use strict";
const { spawnSync } = require("child_process");

const action = process.argv[2] || "";
const dry = process.argv.includes("--dry-run") || process.argv.includes("-n");
const yes = process.argv.includes("--yes") || process.argv.includes("-y");

function cmd(a) {
  const p = process.platform;
  if (p === "linux") return ({
    "safe-off": "sync && systemctl hibernate",
    "suspend":  "sync && systemctl suspend",
    "shutdown": "sync && systemctl poweroff",
    "rehalt":   "systemctl soft-reboot || systemctl kexec || systemctl reboot"
  })[a];
  if (p === "win32") return ({
    "safe-off": "shutdown /h",
    "suspend":  "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
    "shutdown": "shutdown /s /t 0",
    "rehalt":   "taskkill /f /im explorer.exe & start explorer.exe"
  })[a];
  if (p === "darwin") return ({
    "safe-off": "sync && pmset -a hibernatemode 25 && pmset sleepnow",
    "suspend":  "pmset sleepnow",
    "shutdown": "sync && osascript -e 'tell app \"System Events\" to shut down'",
    "rehalt":   "osascript -e 'tell app \"System Events\" to restart'"
  })[a];
  return undefined;
}

const ACTIONS = ["safe-off", "suspend", "shutdown", "rehalt"];
if (!ACTIONS.includes(action)) {
  console.error("usage: node safepower.js <" + ACTIONS.join("|") + "> [--dry-run] [--yes]");
  process.exit(1);
}
const sh = cmd(action);
if (!sh) { console.error("この OS (" + process.platform + ") では未対応のアクションです"); process.exit(2); }

console.log("[SafePower] action : " + action);
console.log("[SafePower] command: " + sh);
if (dry) { console.log("[SafePower] --dry-run: 実行しません。"); process.exit(0); }

if (!yes && process.stdin.isTTY) {
  process.stdout.write("この操作を実行しますか? [y/N] ");
  const buf = Buffer.alloc(8);
  let n = 0;
  try { const fs = require("fs"); n = fs.readSync(0, buf, 0, 8, null); } catch (e) { n = 0; }
  const ans = buf.slice(0, n).toString().trim().toLowerCase();
  if (ans !== "y" && ans !== "yes") { console.log("中止しました。"); process.exit(0); }
}

const r = process.platform === "win32"
  ? spawnSync("cmd.exe", ["/c", sh], { stdio: "inherit" })
  : spawnSync("/bin/sh", ["-c", sh], { stdio: "inherit" });
process.exit(r.status == null ? 1 : r.status);
