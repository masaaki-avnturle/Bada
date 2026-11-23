#!/usr/bin/env node
/* build.js — src/ から自己完結の index.html を作る。  --check: index.html が最新か確認する (CI 用)
 * SHA-256 は bada_gpt/src/engine.js (BadaGPT のエンジン) のものを使う。 */
"use strict";
const fs = require("fs"), path = require("path");
const root = path.join(__dirname, "..");
const rd = f => fs.readFileSync(path.join(root, "src", f), "utf8");
const libs = [fs.readFileSync(path.join(root, "..", "bada_gpt", "src", "engine.js"), "utf8"), rd("entropy.js"), rd("agents.js"), rd("meeting.js"), rd("thought.js"), rd("net.js")].join("\n");
if (/<\/script/i.test(libs)) throw new Error("libs must not contain </script");
const html = rd("ui.html").replace("/*__LIBS__*/", () => libs);
const out = path.join(root, "index.html");
if (process.argv.includes("--check")) {
  if (!fs.existsSync(out) || fs.readFileSync(out, "utf8") !== html) { console.error("index.html が古い: node bada_meeting/tools/build.js を実行してください"); process.exit(1); }
  console.log("index.html は最新");
} else { fs.writeFileSync(out, html); console.log("wrote index.html (" + (html.length / 1024).toFixed(0) + " KB)"); }
