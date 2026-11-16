#!/usr/bin/env node
/*
 * chat.js -- 対話ドライバ (I/O のみ)。
 *
 * エンジン本体は zeta_shannon.bada (純 Bada)。このスクリプトは標準入力の 1 行を
 * Bada の文 (Ask / Learn / Speak) に変換して、量子 Bada インタープリタ
 * (../bada_gui_ide/www/bada.js) のセッションで評価するだけです。
 *
 *   node chat.js                 対話モード
 *   echo "質問" | node chat.js   パイプ入力
 *
 *   /learn <文>      事実を台帳に追記
 *   /speak <書き出し> 文章を生成
 *   /zeta <σ> <t>    ζ(σ+it) と ζ_NS(σ+it) を計算
 *   /trace on|off    標識・確信度・エントロピーの表示切替
 *   /quit            終了
 */
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");
const Bada = require(path.join(__dirname, "..", "bada_gui_ide", "www", "bada.js"));

const source = fs.readFileSync(path.join(__dirname, "zeta_shannon.bada"), "utf8");
const library = source.split("# ==== MAIN ====")[0]; /* 定義と索引構築のみ */

const session = Bada.createSession({ maxSteps: 1e15 });
function run(code) {
  const r = session.eval(code);
  if (r.errors.length) console.error(r.errors.join("\n"));
  if (r.output) console.log(r.output);
}
/* Bada の文字列リテラルに安全に埋め込む */
function lit(text) {
  return '"' + text.replace(/\\/g, "＼").replace(/"/g, "”").replace(/[\r\n]+/g, " ") + '"';
}

run(library);
console.log("ゼータ・シャノン言語エンジン (Bada " + Bada.VERSION + ") -- /learn /speak /zeta /trace /quit");

function handle(line) {
  const text = line.trim();
  if (!text) return true;
  if (text === "/quit" || text === "/exit") return false;
  let m;
  if ((m = text.match(/^\/learn\s+(.+)$/))) run("Learn " + lit(m[1]));
  else if ((m = text.match(/^\/speak\s*(.*)$/))) run("Speak " + lit(m[1]));
  else if ((m = text.match(/^\/trace\s+(on|off)$/))) run("VERBOSE[0] = " + (m[1] === "on" ? 1 : 0));
  else if ((m = text.match(/^\/zeta\s+(-?[\d.]+)\s+(-?[\d.]+)$/))) {
    const sig = Number(m[1]), t = Number(m[2]);
    if (!isFinite(sig) || !isFinite(t) || sig <= 0 || Math.abs(t) > 40 || (sig === 1 && t === 0)) {
      console.log("範囲外です (0 < σ, |t| <= 40, s ≠ 1)。");
    } else {
      const neg = (x) => (x < 0 ? "(0 - " + Math.abs(x) + ")" : String(x));
      run(
        "zz := zeta(" + neg(sig) + ", " + neg(t) + ")\n" +
        "zn := zeta_ns(" + neg(sig) + ", " + neg(t) + ", 0.7)\n" +
        'print("zeta    = (" + fix(zz[0], 8) + ", " + fix(zz[1], 8) + " i)   |zeta|    = " + fix(c_abs(zz), 8))\n' +
        'print("zeta_NS = (" + fix(zn[0], 8) + ", " + fix(zn[1], 8) + " i)   |zeta_NS| = " + fix(c_abs(zn), 8))'
      );
    }
  } else if (text.startsWith("/")) console.log("コマンド: /learn <文>  /speak <書き出し>  /zeta <σ> <t>  /trace on|off  /quit");
  else run("Ask " + lit(text));
  return true;
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: process.stdin.isTTY });
rl.setPrompt(process.stdin.isTTY ? "あなた> " : "");
rl.prompt();
rl.on("line", (line) => {
  if (!handle(line)) { rl.close(); return; }
  rl.prompt();
});
rl.on("close", () => {
  console.log("(台帳 " + session.ledgerLen() + " 件 -- 追記専用)");
  process.exit(0);
});
