#!/usr/bin/env node
/* build.js — src/ui.html に engine.js と chat.js を埋め込み、自己完結の index.html を作る。
 *   node bada_gpt/tools/build.js          書き出す
 *   node bada_gpt/tools/build.js --check  index.html が最新かだけ確認する (CI 用) */
"use strict";
const fs = require("fs"), path = require("path");
const root = path.join(__dirname, "..");
const read = f => fs.readFileSync(path.join(root, "src", f), "utf8");
const html = read("ui.html")
  .replace("/*__ENGINE__*/", () => read("engine.js"))
  .replace("/*__CHAT__*/", () => read("chat.js"));
const out = path.join(root, "index.html");
if (process.argv.includes("--check")) {
  if (!fs.existsSync(out) || fs.readFileSync(out, "utf8") !== html) {
    console.error("index.html が古い: node bada_gpt/tools/build.js を実行してください"); process.exit(1);
  }
  console.log("index.html は最新");
} else { fs.writeFileSync(out, html); console.log("wrote " + out + " (" + html.length + " bytes)"); }
