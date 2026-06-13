#!/usr/bin/env node
/*
 * codegen_cli.js — Ω-Apriori コード生成 CLI
 *
 * 未知事前エンジン(ゲノム)を各言語ソースに表出し、量子囲碁/量子将棋から FPGA を生成する。
 *
 *   node codegen_cli.js emit  <spec.json> <verilog|c|python|js> [out]
 *   node codegen_cli.js quantum <go|shogi> <seed> [out_prefix]   # 量子ゲーム→ゲノム→Verilog/C
 *
 * spec.json: { "cfg":{inbits,layers,width,outbits}, "genome_hex":"..." }
 *
 * ⚠ 概念実証・教育用。
 */
"use strict";
const fs = require("fs");
const cg = require("./codegen.js");
const QG = require("./quantum_games.js");

function emit(specPath, target, out) {
  const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
  const by = cg.hexToBytes(spec.genome_hex);
  const t = (target || "verilog").toLowerCase();
  let code;
  if (t === "verilog" || t === "v") code = cg.toVerilog(spec.cfg, by);
  else if (t === "c") code = cg.toC(spec.cfg, by);
  else if (t === "python" || t === "py") code = cg.toPython(spec.cfg, by);
  else if (t === "js") code = cg.toJS(spec.cfg, by);
  else throw new Error("unknown target: " + target);
  if (out) { fs.writeFileSync(out, code); console.log("wrote", out, "(" + code.split("\n").length + " lines)"); }
  else console.log(code);
}

function quantum(kind, seed, prefix) {
  const cfg = { inbits: 6, layers: 3, width: 8, outbits: 3 };
  const r = (kind === "shogi" ? QG.quantumShogi : QG.quantumGo)({ cfg, seed: seed || (kind + "-1"), qubits: 9, shots: 256 });
  console.log(r.summary);
  console.log("top states:", JSON.stringify(r.top_states));
  console.log("board:", JSON.stringify(r.board));
  const by = cg.hexToBytes(r.genome_hex);
  const name = "quantum_" + kind + "_fpga";
  const ver = cg.toVerilog(cfg, by, name);
  prefix = prefix || ("quantum_" + kind);
  fs.writeFileSync(prefix + ".v", ver);
  fs.writeFileSync(prefix + ".c", cg.toC(cfg, by));
  fs.writeFileSync(prefix + ".spec.json", JSON.stringify({ cfg, genome_hex: r.genome_hex, source: "quantum_" + kind, seed: r.seed }, null, 1));
  console.log("→ generated FPGA:", prefix + ".v", "(" + ver.split("\n").length + " lines),", prefix + ".c,", prefix + ".spec.json");
}

const [cmd, ...a] = process.argv.slice(2);
try {
  if (cmd === "emit") emit(a[0], a[1], a[2]);
  else if (cmd === "quantum") quantum(a[0], a[1], a[2]);
  else { console.log("usage:\n  node codegen_cli.js emit <spec.json> <verilog|c|python|js> [out]\n  node codegen_cli.js quantum <go|shogi> <seed> [out_prefix]"); process.exit(1); }
} catch (e) { console.error("error:", e.message); process.exit(1); }
