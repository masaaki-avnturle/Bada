#!/usr/bin/env node
/*
 * bridge.js -- 他言語からエンジンを使うための JSON Lines ブリッジ。
 *
 * 標準入力の 1 行 = 1 リクエスト (JSON)、標準出力の 1 行 = 1 レスポンス (JSON)。
 * エンジン本体は zeta_shannon.bada (純 Bada)。プロセスが生きている間、学習した事実と
 * 会話の信念は保持される。Ruby 側の Bada::ZetaShannon (バージョン台帳の local 段) が使う。
 *
 *   {"op":"ask","text":"…"}    -> {"ok":true,"status":"検証済","topic":"…","confidence":0.92,
 *                                  "entropy_bits":0.53,"grover":0.996,"abstained":false,"text":"…"}
 *   {"op":"learn","text":"…"}  -> {"ok":true,"facts":76,"withheld":false}
 *   {"op":"ping"}              -> {"ok":true,"engine":"zeta-shannon","bada":"1.2.0","facts":75}
 *
 * 起動直後に {"ready":true,…} を 1 行出力する。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");
const Bada = require(path.join(__dirname, "..", "bada_gui_ide", "www", "bada.js"));

const library = fs.readFileSync(path.join(__dirname, "zeta_shannon.bada"), "utf8").split("# ==== MAIN ====")[0];
const session = Bada.createSession({ maxSteps: 1e15 });

function evalBada(code) {
  const r = session.eval(code);
  if (r.errors.length) throw new Error(r.errors.join("; "));
  return r.output;
}
/* Bada の文字列リテラルに安全に埋め込む */
function lit(text) {
  return '"' + String(text).replace(/\\/g, "＼").replace(/"/g, "”").replace(/[\r\n]+/g, " ") + '"';
}
function factCount() { return Number(evalBada("print(len(KB))")); }

function handle(req) {
  if (req.op === "ping") return { ok: true, engine: "zeta-shannon", bada: Bada.VERSION, facts: factCount() };
  if (typeof req.text !== "string" || !req.text.trim()) return { ok: false, error: "text required" };
  if (req.op === "learn") {
    evalBada("VERBOSE[0] = 0\nKB <- [" + lit(req.text) + ', len(TOPICS) - 1, "学習"]\nindex_fact(len(KB) - 1)\n' + lit(req.text) + " >> tuplespace");
    /* withheld: 罪悪感の回路がこの文を口にしないと判定したか */
    return { ok: true, facts: factCount(), withheld: evalBada("print(nogo(GUILT_F[len(KB) - 1]))") === "true" };
  }
  if (req.op === "ask") {
    const out = evalBada(
      "bridge_r := zs_reply(" + lit(req.text) + ")\n" +
      "print(bridge_r[1])\nprint(bridge_r[2])\nprint(fix(bridge_r[3], 4))\nprint(fix(bridge_r[4], 4))\nprint(fix(bridge_r[5], 4))\nprint(bridge_r[0])"
    ).split("\n");
    return {
      ok: true, status: out[0], topic: out[1], confidence: Number(out[2]), entropy_bits: Number(out[3]),
      grover: Number(out[4]), abstained: out[0] === "無知", text: out.slice(5).join(" "),
    };
  }
  return { ok: false, error: "unknown op" };
}

evalBada(library);
process.stdout.write(JSON.stringify({ ready: true, engine: "zeta-shannon", bada: Bada.VERSION, facts: factCount() }) + "\n");

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on("line", (line) => {
  if (!line.trim()) return;
  let res;
  try { res = handle(JSON.parse(line)); } catch (e) { res = { ok: false, error: String(e && e.message ? e.message : e) }; }
  process.stdout.write(JSON.stringify(res) + "\n");
});
rl.on("close", () => process.exit(0));
