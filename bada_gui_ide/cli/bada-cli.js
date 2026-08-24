#!/usr/bin/env node
/*
 * bada-cli.js — Bada コマンドライン ドライバ (Node.js)
 *
 * GUI IDE と同じ言語コア (www/bada.js) を使う CLI。C リファレンスの
 * `bada` 実行ファイルと同じサブコマンドを提供します:
 *
 *   node bada-cli.js run    <file.bada>          # インタープリタ実行
 *   node bada-cli.js build  <file.bada> [-o out] # Bada -> C -> gcc でネイティブ化
 *   node bada-cli.js emit   <file.bada> [-o c]   # C を出力するだけ
 *   node bada-cli.js tokens <file.bada>          # トークン列を表示
 *   node bada-cli.js ast    <file.bada>          # AST を表示
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const Bada = require(path.join(__dirname, "..", "www", "bada.js"));

function usage() {
  console.error(
    "Bada -- the Unknown-Prior Engine language (GUI IDE core, CLI driver)\n" +
    "usage:\n" +
    "  bada-cli run    <file.bada>          # interpret\n" +
    "  bada-cli build  <file.bada> [-o out] # compile to C and gcc-build a binary\n" +
    "  bada-cli emit   <file.bada> [-o c]   # emit C only\n" +
    "  bada-cli tokens <file.bada>          # dump token stream\n" +
    "  bada-cli ast    <file.bada>          # dump AST"
  );
}

const argv = process.argv.slice(2);
if (argv.length < 2) { usage(); process.exit(1); }
const cmd = argv[0];
const file = argv[1];
let out = null;
for (let i = 2; i < argv.length - 1; i++) if (argv[i] === "-o") out = argv[i + 1];

let src;
try { src = fs.readFileSync(file, "utf8"); }
catch (e) { console.error("cannot open " + file); process.exit(1); }

if (cmd === "tokens") {
  console.log(Bada.tokens(src));
} else if (cmd === "ast") {
  const a = Bada.ast(src);
  if (a.errors.length) console.error(a.errors.join("\n"));
  console.log(a.text);
} else if (cmd === "run") {
  const r = Bada.run(src, { out: (s) => console.log(s) });
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
  const cmdline = `gcc -O2 -o ${o} ${cfile} -lm`;
  console.error("[bada build] " + cmdline);
  const rc = spawnSync("gcc", ["-O2", "-o", o, cfile, "-lm"], { stdio: "inherit" });
  if (rc.status === 0) console.error("[bada build] ok -> " + o);
  else { console.error("[bada build] gcc failed (rc=" + rc.status + ")"); process.exit(1); }
} else {
  usage();
  process.exit(1);
}
