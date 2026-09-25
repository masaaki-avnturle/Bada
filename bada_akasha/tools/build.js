#!/usr/bin/env node
/*
 * build.js — Bada Akasha の自己完結 index.html を組み立てる
 *
 *   node bada_akasha/tools/build.js          # index.html を書き出す
 *   node bada_akasha/tools/build.js --check  # 書き出し済みの index.html が最新か確かめる (CI 用)
 *
 * src/app.html の 3 つの差し込み口に
 *   @@BADA_JS@@     ← bada_gui_ide/www/bada.js (Bada インタープリタ本体)
 *   @@AKASHA_BADA@@ ← src/akasha.bada (Bada で書いたエンジン。JS 文字列として)
 *   @@CORPUS@@      ← src/corpus.json (論文集の段落)
 * を埋め込みます。</script> が文字列に現れないよう "</" は "<\/" にします。
 */
"use strict";
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const safe = (s) => s.replace(/<\//g, "<\\/");

function build(){
  const tpl = read("src/app.html");
  const bada = read("../bada_gui_ide/www/bada.js");
  if (/<\/script/i.test(bada)) throw new Error("bada.js contains </script>");
  const engine = read("src/akasha.bada");
  const corpus = JSON.parse(read("src/corpus.json"));
  const parts = { "/*@@BADA_JS@@*/": bada, "/*@@AKASHA_BADA@@*/": safe(JSON.stringify(engine)), "/*@@CORPUS@@*/": safe(JSON.stringify(corpus)) };
  let out = tpl;
  for (const [k, v] of Object.entries(parts)){
    if (out.split(k).length !== 2) throw new Error("placeholder " + k + " must appear exactly once");
    out = out.split(k).join(v);
  }
  return out;
}

const html = build();
const dest = path.join(root, "index.html");
if (process.argv.includes("--check")){
  const cur = fs.existsSync(dest) ? fs.readFileSync(dest, "utf8") : "";
  if (cur !== html){ console.error("bada_akasha/index.html is out of date — run: node bada_akasha/tools/build.js"); process.exit(1); }
  console.log("index.html is up to date (" + html.length + " chars)");
} else {
  fs.writeFileSync(dest, html);
  console.log("wrote " + path.relative(process.cwd(), dest) + " (" + (Buffer.byteLength(html) / 1024).toFixed(0) + " KB)");
}
