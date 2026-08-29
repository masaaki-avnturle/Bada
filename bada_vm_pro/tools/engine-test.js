/*
 * engine-test.js — Bada VM Pro のエンジン単体テスト (Node で実行)
 *
 *   node bada_vm_pro/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM/localStorage を
 * スタブした上で純ロジック部分を検証します:
 *   1. 量子 Bada インタープリタ — ベル状態の振幅と相関測定
 *   2. トランスフォーマー — 学習後の次トークン予測 / attention 行の正規化
 *   3. Bada on Rails — scaffold 生成と CRUD
 *   4. 合い言葉 — silent talk 完全一致 / 音声あいまい照合 / 不一致の拒否
 *   5. OS update / upgrade — BadaGPT が使うバージョン台帳
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* ── DOM / localStorage スタブ ── */
function stubEl(){
  return new Proxy({ style: {}, classList: { add(){}, remove(){} }, value: "", textContent: "", innerHTML: "" }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus") return function(){};
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console: console,
  Math: Math,
  Function: Function,
  setTimeout: function(fn){ fn(); },
  setInterval: function(){ return 0; },
  clearInterval: function(){},
  alert: function(){},
  localStorage: { _d: {}, getItem(k){ return k in this._d ? this._d[k] : null; }, setItem(k, v){ this._d[k] = String(v); } },
  window: {},
  document: {
    getElementById(){ return stubEl(); },
    createElement(){ return stubEl(); },
    querySelectorAll(){ return []; },
    addEventListener(){}, removeEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

function get(name){ return vm.runInContext(name, sandbox); }
function assert(cond, msg){ if (!cond){ console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }

/* 1. 量子ベル状態 */
const bell = get("badaInterpret")("qubit q0 q1\nH q0\nCNOT q0 q1\nstate\nmeasure");
assert(/\|00⟩ 0\.707/.test(bell) && /\|11⟩ 0\.707/.test(bell), "bell state amplitudes 1/√2 (|00⟩+|11⟩)");
assert(/measure → \|(00|11)⟩/.test(bell), "measurement collapses to correlated |00⟩ or |11⟩");
const err = get("badaInterpret")("H q9");
assert(/!!/.test(err), "interpreter reports errors for undeclared qubits");

/* 2. トランスフォーマー */
get("tfTrain")("qubit q0 q1\nH q0\nCNOT q0 q1\nmeasure");
const p = get("transformerPredict")("qubit q0 q1 H", 5);
assert(p.preds[0].w === "q0", "after training, H → q0 is the top next-token prediction");
let sum = 0; for (const x of p.preds) sum += x.p;
assert(sum > 0 && sum <= 1.0001, "prediction probabilities form a sub-distribution");
for (const row of p.attn){
  const t = row.reduce(function(a, b){ return a + b; }, 0);
  assert(Math.abs(t - 1) < 1e-9, "attention row sums to 1 (softmax)");
}

/* 3. Bada on Rails */
const r = get("railsScaffold")("Post", ["title:string", "body:text"]);
assert(/model Post/.test(r.code) && /resources :post/.test(r.code), "scaffold generates model/controller/routes code");
get("railsCreateRow")("post", { title: "hello", body: "world" });
assert(get("railsDB")().resources.post.rows.length === 1, "rails create adds a row");
get("railsDeleteRow")("post", 1);
assert(get("railsDB")().resources.post.rows.length === 0, "rails destroy removes the row");

/* 4. 合い言葉 (silent talk = 決定論的 / 音声 = あいまい照合) */
const m1 = get("matchPassphrase")("バダ、起動 ターミナル");
assert(m1.ok && m1.cmd && m1.cmd.url === "bada://terminal", "silent talk exact passphrase+command matches deterministically");
const m2 = get("matchPassphrase")("パダ起動 ターミナル");
assert(m2.ok && m2.cmd && m2.cmd.url === "bada://terminal", "voice-style mishearing (バ→パ) still matches via similarity");
const m3 = get("matchPassphrase")("こんにちは ターミナル");
assert(!m3.ok, "a wrong passphrase is rejected");

/* 5. OS update / upgrade (BadaGPT の台帳) */
const v0 = get("osVersion")();
get("osUpdate")("update");
assert(get("osVersion")().split(".")[2] === String(Number(v0.split(".")[2]) + 1), "os update bumps the patch version");
get("osUpdate")("upgrade");
const vu = get("osVersion")().split(".");
assert(vu[1] === "0" && vu[2] === "0", "os upgrade bumps the major version and resets minor/patch");

/* 6. シェル経由の scaffold */
const sh = get("runShell")("rails scaffold Book title:string");
assert(/bada:\/\/rails\/book/.test(sh), "CUI shell can run rails scaffold");

/* 7. Ubuntu ユーザーランド — apt / 事前インストール */
const aptList = get("runShell")("apt list --installed");
for (const p of ["bash", "vim", "emacs", "openssh-client", "xinetd", "texlive-full", "screen", "fcitx-mozc", "xterm", "x-terminal-emulator", "terminal"]){
  assert(aptList.includes(p + "/badable"), "preinstalled package: " + p);
}
assert(/はすでに最新バージョン/.test(get("runShell")("apt install vim")), "apt install of a preinstalled package is a no-op");
assert(/を設定しています/.test(get("runShell")("apt install cowsay")), "apt install adds a new package");
assert(get("runShell")("apt list --installed").includes("cowsay/badable"), "newly installed package appears in apt list");
assert(/essential/.test(get("runShell")("apt remove bash")), "essential package bash cannot be removed");

/* 8. VFS — echo リダイレクト / cat / ls */
const ctxMk = get("shellCtx");
const runShell = get("runShell");
const ctx = ctxMk();
runShell("echo konnichiwa > /home/user/greet.txt", ctx);
assert(runShell("cat /home/user/greet.txt", ctx).trim() === "konnichiwa", "echo > file then cat round-trips through the VFS");
assert(runShell("ls /home/user", ctx).includes("greet.txt"), "ls shows the new file");
runShell("cd /etc", ctx);
assert(ctx.cwd === "/etc" && runShell("pwd", ctx) === "/etc", "cd changes the shell cwd");

/* 9. ssh — 既知ホストへ接続してプロンプトが変わり、exit で戻る */
const sshOut = runShell("ssh user@bada.or.jp", ctx);
assert(/QKD/.test(sshOut) && /Welcome to bada\.or\.jp/.test(sshOut), "ssh connects with a Bell-pair QKD handshake banner");
assert(ctx.host === "bada.or.jp", "ssh switches the shell host");
assert(/closed/.test(runShell("exit", ctx)), "exit closes the ssh connection");
assert(ctx.host === "badavm", "after exit the shell is local again");
assert(/Could not resolve/.test(runShell("ssh nowhere.example", ctx)), "unknown ssh host is rejected");

/* 10. xinetd / texlive / fcitx-mozc コマンド */
assert(/active \(running\)/.test(runShell("xinetd status", ctx)), "xinetd reports active with managed services");
assert(/echo/.test(runShell("xinetd status", ctx)), "xinetd lists /etc/xinetd.d services");
assert(/TeX Live 2024/.test(runShell("pdflatex --version", ctx)), "texlive-full provides pdflatex");
const texOut = runShell("pdflatex /home/user/letter.tex", ctx);
assert(/Output written on letter\.pdf/.test(texOut), "pdflatex compiles letter.tex to letter.pdf");
assert(/%PDF/.test(runShell("cat /home/user/letter.pdf", ctx)), "compiled PDF exists in the VFS");
assert(/Ctrl\+Space/.test(runShell("fcitx-mozc status", ctx)), "fcitx-mozc explains Japanese input toggling");

/* 11. fcitx-mozc ローマ字→かな変換 (端末の日本語入力) */
const r2k = get("romajiToKana");
assert(r2k("nihongo") === "にほんご", "romaji nihongo → にほんご");
assert(r2k("kyouto") === "きょうと", "romaji kyouto → きょうと (拗音)");
assert(r2k("gakkou") === "がっこう", "romaji gakkou → がっこう (促音)");
assert(r2k("shinbun") === "しんぶん", "romaji shinbun → しんぶん (ん)");
assert(get("kanaToKatakana")("たみなる") === "タミナル", "hiragana → katakana conversion (F7)");

/* 12. 不明コマンドは bash 風エラー */
assert(/command not found/.test(runShell("no-such-cmd", ctx)), "unknown command reports bash-style error");

console.log("\nALL ENGINE TESTS PASSED");
