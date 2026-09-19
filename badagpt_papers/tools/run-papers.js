#!/usr/bin/env node
/*
 * run-papers.js — BadaGPT 未知事前エンジン論文集 (量子 Bada 版) の実行器
 *
 *   node badagpt_papers/tools/run-papers.js            # 全巻を実行・検査
 *   node badagpt_papers/tools/run-papers.js 02         # 第二巻だけ
 *   node badagpt_papers/tools/run-papers.js 02 05 10   # 複数巻
 *   node badagpt_papers/tools/run-papers.js --quiet    # 出力を抑え判定だけ
 *
 * Bada にはモジュール読み込みの仕組みが無いので、各巻の .bada を共通核
 * (bada/00_prelude.bada) と連結して 1 本にし、bada_gui_ide/www/bada.js の
 * インタープリタで走らせる。連結した全文は dist/NN_*.full.bada に、実行
 * 出力は dist/NN_*.out.txt に書き出す (bada-cli でも dist の .full.bada を
 * そのまま実行できるが、既定のステップ上限 2000 万を超える巻があるので、
 * 本スクリプトは上限を 40 億に上げている)。
 *
 * 各巻は末尾で verdict("@@PAPER-NN-OK") を呼び、全検査が通ったときだけ
 * その完走センチネルを出力する。本スクリプトはそれを検査し、1 巻でも
 * 落ちれば非零で終了する。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const Bada = require("../../bada_gui_ide/www/bada.js");

const ROOT = path.join(__dirname, "..");
const BADA_DIR = path.join(ROOT, "bada");
const DIST = path.join(ROOT, "dist");
const MAX_STEPS = 4e9;

const args = process.argv.slice(2);
const quiet = args.includes("--quiet");
const wanted = args.filter((a) => !a.startsWith("--"));

const prelude = fs.readFileSync(path.join(BADA_DIR, "00_prelude.bada"), "utf8");
const papers = fs.readdirSync(BADA_DIR)
  .filter((f) => /^\d\d_.*\.bada$/.test(f) && !f.startsWith("00_"))
  .sort()
  .filter((f) => wanted.length === 0 || wanted.some((w) => f.startsWith(w) || f.includes(w)));

if (papers.length === 0) {
  console.error("no paper matched: " + wanted.join(" "));
  process.exit(2);
}

fs.mkdirSync(DIST, { recursive: true });
let failed = 0;
const summary = [];
for (const file of papers) {
  const num = file.slice(0, 2);
  const src = fs.readFileSync(path.join(BADA_DIR, file), "utf8");
  const full = "# ---- generated: 00_prelude.bada + " + file + " (tools/run-papers.js) ----\n" +
    prelude + "\n\n# ================= " + file + " =================\n" + src;
  const t0 = Date.now();
  const r = Bada.run(full, { maxSteps: MAX_STEPS });
  const ms = Date.now() - t0;
  const sentinel = "@@PAPER-" + num + "-OK";
  const ok = r.ok && r.parseErrors.length === 0 && r.output.split("\n").includes(sentinel);
  const base = file.replace(/\.bada$/, "");
  fs.writeFileSync(path.join(DIST, base + ".full.bada"), full);
  fs.writeFileSync(path.join(DIST, base + ".out.txt"), r.output + "\n");
  if (!quiet) {
    console.log(r.output);
    if (r.parseErrors.length) console.log(r.parseErrors.join("\n"));
  }
  const line = (ok ? "PASS" : "FAIL") + "  " + file + "  (" + ms + " ms, ledger " + r.ledgerLen + " facts)";
  summary.push(line);
  if (!ok) {
    failed++;
    if (quiet) {
      console.log(r.output.split("\n").filter((l) => /\[NG\]|error|Error/.test(l)).join("\n"));
      if (r.parseErrors.length) console.log(r.parseErrors.join("\n"));
    }
  }
}
console.log("\n==== badagpt_papers summary ====");
console.log(summary.join("\n"));
console.log(failed === 0 ? "ALL PASS (" + papers.length + " papers)" : failed + " paper(s) FAILED");
process.exit(failed === 0 ? 0 : 1);
