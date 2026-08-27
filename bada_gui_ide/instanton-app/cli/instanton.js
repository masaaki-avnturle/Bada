#!/usr/bin/env node
/* ============================================================================
 * instanton.js — InstantOn command-line tool.
 *
 * 電源を切ると状態をディスクに保存し、次の電源投入で通常ブートを飛ばして
 * 前回の状態から即復帰するよう設定します(= 復帰起動 / 高速スタートアップ)。
 *
 *   node instanton.js status         # 現在の設定を表示
 *   node instanton.js enable         # インスタントオンを有効化 (要 sudo/管理者)
 *   node instanton.js hibernate-now  # いま休止(次回の電源投入で即復帰)
 *   node instanton.js disable        # 無効化(通常のシャットダウン/起動へ)
 *   ... --dry-run でコマンド表示のみ / --yes で確認省略
 *
 * あなた自身の PC が対象です。設定には権限が必要な場合があります。
 * ============================================================================ */
"use strict";
const { spawnSync } = require("child_process");

const action = process.argv[2] || "";
const dry = process.argv.includes("--dry-run") || process.argv.includes("-n");
const yes = process.argv.includes("--yes") || process.argv.includes("-y");

function cmd(a) {
  const p = process.platform;
  if (p === "linux") return ({
    "status": "echo 'power states:'; cat /sys/power/state 2>/dev/null; echo; echo 'swap:'; swapon --show 2>/dev/null; echo; systemctl show systemd-logind -p HandlePowerKey 2>/dev/null",
    "enable": "sudo sh -c 'mkdir -p /etc/systemd/logind.conf.d && printf \"[Login]\\nHandlePowerKey=hibernate\\nHandleLidSwitch=hibernate\\n\" > /etc/systemd/logind.conf.d/90-instanton.conf && systemctl restart systemd-logind'",
    "hibernate-now": "sync && systemctl hibernate",
    "disable": "sudo sh -c 'rm -f /etc/systemd/logind.conf.d/90-instanton.conf && systemctl restart systemd-logind'"
  })[a];
  if (p === "win32") return ({
    "status": "powercfg /a & reg query \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power\" /v HiberbootEnabled",
    "enable": "powercfg /hibernate on & reg add \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power\" /v HiberbootEnabled /t REG_DWORD /d 1 /f & powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2 & powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2 & powercfg -SETACTIVE SCHEME_CURRENT",
    "hibernate-now": "shutdown /h",
    "disable": "reg add \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power\" /v HiberbootEnabled /t REG_DWORD /d 0 /f"
  })[a];
  if (p === "darwin") return ({
    "status": "pmset -g | grep -E 'hibernatemode|standby'",
    "enable": "sudo pmset -a hibernatemode 25",
    "hibernate-now": "sync && pmset sleepnow",
    "disable": "sudo pmset -a hibernatemode 3"
  })[a];
  return undefined;
}

const ACTIONS = ["status", "enable", "hibernate-now", "disable"];
if (!ACTIONS.includes(action)) {
  console.error("usage: node instanton.js <" + ACTIONS.join("|") + "> [--dry-run] [--yes]");
  process.exit(1);
}
const sh = cmd(action);
if (!sh) { console.error("この OS (" + process.platform + ") では未対応です"); process.exit(2); }

console.log("[InstantOn] action : " + action);
console.log("[InstantOn] command: " + sh);
if (dry) { console.log("[InstantOn] --dry-run: 実行しません。"); process.exit(0); }

const destructive = action !== "status";
if (destructive && !yes && process.stdin.isTTY) {
  process.stdout.write("この操作を実行しますか? [y/N] ");
  const buf = Buffer.alloc(8); let n = 0;
  try { n = require("fs").readSync(0, buf, 0, 8, null); } catch (e) { n = 0; }
  const ans = buf.slice(0, n).toString().trim().toLowerCase();
  if (ans !== "y" && ans !== "yes") { console.log("中止しました。"); process.exit(0); }
}

const r = process.platform === "win32"
  ? spawnSync("cmd.exe", ["/c", sh], { stdio: "inherit" })
  : spawnSync("/bin/sh", ["-c", sh], { stdio: "inherit" });
process.exit(r.status == null ? 1 : r.status);
