/*
 * run-bada.js — .bada を上限を上げて走らせる
 *
 *   node ultra_network/tools/run-bada.js ultra_network/dist/ultra-full.bada
 *   node ultra_network/tools/run-bada.js <file.bada> [ステップ上限]
 *
 * bada-cli の run は既定の 2000 万ステップで打ち切る。この全層プログラムは
 * SHA-256 と HMAC をソフトウェアのビット演算で回すためそれを超えるので、
 * 上限を上げて走らせるための小さなラッパ。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const Bada = require(path.join(__dirname, "..", "..", "bada_gui_ide", "www", "bada.js"));

const file = process.argv[2];
if (!file) {
  console.error("usage: node ultra_network/tools/run-bada.js <file.bada> [maxSteps]");
  process.exit(1);
}
const maxSteps = parseInt(process.argv[3] || "800000000", 10);
const src = fs.readFileSync(file, "utf8");
const r = Bada.run(src, { maxSteps: maxSteps, out: (s) => console.log(s) });
if (r.parseErrors && r.parseErrors.length) {
  console.error(r.parseErrors.join("\n"));
}
if (r.error) { console.error("[error] " + r.error); }
process.exit(r.ok && !r.error && !(r.parseErrors || []).length ? 0 : 1);
