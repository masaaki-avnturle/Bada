#!/usr/bin/env node
/* zeta_shannon.bada の定義部 + unknown_prior_paper.bada を連結して実行し、
   出力を run_output.txt に保存する (Bada にモジュール読み込みは無いため連結する)。 */
"use strict";
const fs = require("fs"), path = require("path");
const Bada = require(path.join(__dirname, "..", "..", "bada_gui_ide", "www", "bada.js"));
const lib = fs.readFileSync(path.join(__dirname, "..", "zeta_shannon.bada"), "utf8").split("# ==== MAIN ====")[0];
const prog = fs.readFileSync(path.join(__dirname, "unknown_prior_paper.bada"), "utf8");
const r = Bada.run(lib + "\n" + prog, { maxSteps: 1e12 });
if (r.parseErrors.length) console.error(r.parseErrors.join("\n"));
if (r.error) console.error("[runtime error] " + r.error);
fs.writeFileSync(path.join(__dirname, "run_output.txt"), r.output + "\n");
console.log(r.output);
process.exit(r.ok ? 0 : 1);
