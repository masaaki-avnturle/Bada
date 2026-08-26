#!/usr/bin/env node
/*
 * bada-cli.js — Bada コマンドライン アプリケーション
 *
 * 量子プログラミング言語 Bada (Unknown-Prior Engine 言語) の CLI。
 * GUI IDE と同じ言語コア (www/bada.js) を使い、C リファレンスの `bada`
 * 実行ファイルと同じサブコマンド + 対話 REPL を提供します。
 *
 *   bada-cli run      <file.bada>          # インタープリタ実行
 *   bada-cli build    <file.bada> [-o out] # Bada -> C -> gcc でネイティブ化
 *   bada-cli emit     <file.bada> [-o c]   # C を出力するだけ
 *   bada-cli tokens   <file.bada>          # トークン列を表示
 *   bada-cli ast      <file.bada>          # AST を表示
 *   bada-cli repl                          # 対話モード (量子ゲート/@reviser も使用可)
 *   bada-cli examples [name] [-o dir]      # 同梱サンプルの一覧表示 / 書き出し
 *   bada-cli version                       # バージョン表示
 *
 * Node.js で `node bada-cli.js …` として実行できるほか、GitHub Actions が
 * Node SEA (Single Executable Application) で単一実行ファイル
 * (bada-cli.exe / bada-cli-linux-x64) にパッケージして Release へ添付します。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { spawnSync } = require("child_process");
/* 静的 require — esbuild バンドル (単一バイナリ化) のため動的パス不可 */
const Bada = require("../www/bada.js");
const EXAMPLES = require("../www/examples.js");
const { ffi } = require("./bada-ffi.js");

function usage() {
  console.error(
    "Bada -- the Unknown-Prior Engine quantum language (CLI " + Bada.VERSION + ")\n" +
    "usage:\n" +
    "  bada-cli run      <file.bada>          # interpret\n" +
    "  bada-cli build    <file.bada> [-o out] # compile to C and gcc-build a binary\n" +
    "  bada-cli emit     <file.bada> [-o c]   # emit C only\n" +
    "  bada-cli tokens   <file.bada>          # dump token stream\n" +
    "  bada-cli ast      <file.bada>          # dump AST\n" +
    "  bada-cli repl                          # interactive session (quantum gates, @reviser)\n" +
    "  bada-cli examples [name] [-o dir]      # list / extract built-in samples\n" +
    "  bada-cli version                       # print version"
  );
}

function readSource(file) {
  try {
    return fs.readFileSync(file, "utf8");
  } catch (e) {
    console.error("cannot open " + file);
    process.exit(1);
  }
}

/* ---------------- REPL ---------------- */
function repl() {
  const session = Bada.createSession({ ffi });
  console.log("Bada " + Bada.VERSION + " -- quantum REPL on the Unknown-Prior Engine");
  console.log('型: dist / phase / tuplespace / qubit.  例: reg := H(qubit(1)) ; Measure(reg)');
  console.log('@reviser : grammar { rule ... } で文法も拡張できます。exit / quit で終了。');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: process.stdin.isTTY });
  let buffer = "";
  const PROMPT1 = "bada> ";
  const PROMPT2 = "....> ";
  function balanced(src) {
    /* コメント/文字列を除いた括弧の釣り合いで複数行入力を判定 */
    let depth = 0, i = 0, q = null;
    while (i < src.length) {
      const c = src[i];
      if (q) {
        if (c === "\\") i++;
        else if (c === q) q = null;
      } else if (c === '"' || c === "'") q = c;
      else if (c === "#") { while (i < src.length && src[i] !== "\n") i++; }
      else if (c === "{" || c === "[" || c === "(") depth++;
      else if (c === "}" || c === "]" || c === ")") depth--;
      i++;
    }
    return depth <= 0;
  }
  function prompt() { rl.setPrompt(buffer ? PROMPT2 : PROMPT1); rl.prompt(); }
  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (!buffer && (trimmed === "exit" || trimmed === "quit")) { rl.close(); return; }
    buffer += (buffer ? "\n" : "") + line;
    if (!balanced(buffer)) { prompt(); return; }
    const src = buffer;
    buffer = "";
    if (src.trim()) {
      const r = session.eval(src);
      if (r.errors.length) for (const e of r.errors) console.error(e);
      if (r.output) console.log(r.output);
      if (r.value !== null && r.value !== undefined) console.log(r.value);
    }
    prompt();
  });
  rl.on("close", () => {
    console.log("(ledger: " + session.ledgerLen() + " facts, rules: [" + session.rules().join(", ") + "])");
    process.exit(0);
  });
  prompt();
}

/* ---------------- examples ---------------- */
function examplesCmd(name, outDir) {
  const names = Object.keys(EXAMPLES);
  if (!name) {
    console.log("built-in examples: " + names.join(", "));
    console.log("  bada-cli examples <name>          # print to stdout");
    console.log("  bada-cli examples all -o <dir>    # write all as .bada files");
    return;
  }
  const targets = name === "all" ? names : [name];
  for (const n of targets) {
    if (!EXAMPLES[n]) { console.error("unknown example: " + n + " (available: " + names.join(", ") + ")"); process.exit(1); }
    if (outDir) {
      fs.mkdirSync(outDir, { recursive: true });
      const p = path.join(outDir, n + ".bada");
      fs.writeFileSync(p, EXAMPLES[n]);
      console.error("wrote " + p);
    } else {
      process.stdout.write(EXAMPLES[n]);
    }
  }
}

/* ---------------- main ---------------- */
const argv = process.argv.slice(2);
const cmd = argv[0];

if (!cmd || cmd === "help" || cmd === "--help" || cmd === "-h") { usage(); process.exit(cmd ? 0 : 1); }
if (cmd === "version" || cmd === "--version" || cmd === "-v") {
  console.log("bada-cli " + Bada.VERSION + " (Bada language core " + Bada.VERSION + ", node " + process.version + ")");
  process.exit(0);
}
if (cmd === "repl") { repl(); }
else if (cmd === "examples") {
  let out = null;
  for (let i = 1; i < argv.length - 1; i++) if (argv[i] === "-o") out = argv[i + 1];
  const name = argv[1] && argv[1] !== "-o" ? argv[1] : null;
  examplesCmd(name, out);
} else if (cmd === "run" || cmd === "build" || cmd === "emit" || cmd === "tokens" || cmd === "ast") {
  const file = argv[1];
  if (!file) { usage(); process.exit(1); }
  let out = null;
  for (let i = 2; i < argv.length - 1; i++) if (argv[i] === "-o") out = argv[i + 1];
  const src = readSource(file);

  if (cmd === "tokens") {
    console.log(Bada.tokens(src));
  } else if (cmd === "ast") {
    const a = Bada.ast(src);
    if (a.errors.length) console.error(a.errors.join("\n"));
    console.log(a.text);
  } else if (cmd === "run") {
    const r = Bada.run(src, { out: (s) => console.log(s), ffi });
    if (r.parseErrors.length) console.error(r.parseErrors.join("\n"));
    process.exit(r.ok ? 0 : 1);
  } else if (cmd === "emit") {
    const r = Bada.emitC(src);
    const o = out || "out.c";
    fs.writeFileSync(o, r.c);
    if (r.errors.length) console.error(r.errors.join("\n"));
    console.error("emitted C -> " + o);
  } else if (cmd === "build") {
    const r = Bada.emitC(src);
    if (r.errors.length) { console.error(r.errors.join("\n")); process.exit(1); }
    const o = out || "a.out";
    const cfile = o + ".gen.c";
    fs.writeFileSync(cfile, r.c);
    console.error("[bada build] gcc -O2 -o " + o + " " + cfile + " -lm");
    const rc = spawnSync("gcc", ["-O2", "-o", o, cfile, "-lm"], { stdio: "inherit" });
    if (rc.error || rc.status !== 0) {
      console.error("[bada build] gcc failed" + (rc.error ? " (" + rc.error.message + ")" : " (rc=" + rc.status + ")"));
      console.error("gcc が見つからない場合: Ubuntu は `sudo apt install build-essential`, Windows は MinGW-w64 を PATH に追加してください。");
      process.exit(1);
    }
    console.error("[bada build] ok -> " + o);
  }
} else {
  usage();
  process.exit(1);
}
