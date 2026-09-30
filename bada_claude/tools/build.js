#!/usr/bin/env node
/*
 * build.js — src/ から単一 HTML (bada_claude/index.html) を組み立てる
 *
 *   node bada_claude/tools/build.js          # index.html を生成
 *   node bada_claude/tools/build.js --check  # index.html が src と一致するか検査
 *
 * 知識ベース (src/kb.json) は tools/build_kb.py が sources/*.pdf から作ります。
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const rd = f => fs.readFileSync(path.join(ROOT, "src", f), "utf8");

function build() {
  const kb = JSON.stringify(JSON.parse(rd("kb.json"))).replace(/<\//g, "<\\/");
  const brain = rd("brain.bada");
  if (/<\/script/i.test(brain)) throw new Error("brain.bada must not contain </script");
  const engine = rd("engine.js"), app = rd("app.js");
  for (const [n, s] of [["engine.js", engine], ["app.js", app]]) if (/<\/script/i.test(s)) throw new Error(n + " must not contain </script");
  return rd("ui.html")
    .replace("/*__KB__*/", () => kb)
    .replace("/*__BRAIN__*/", () => brain)
    .replace("/*__ENGINE__*/", () => engine)
    .replace("/*__APP__*/", () => app);
}

const out = path.join(ROOT, "index.html");
const html = build();
if (process.argv.includes("--check")) {
  const cur = fs.existsSync(out) ? fs.readFileSync(out, "utf8") : "";
  if (cur !== html) { console.error("bada_claude/index.html is stale — run: node bada_claude/tools/build.js"); process.exit(1); }
  console.log("index.html is up to date");
} else {
  fs.writeFileSync(out, html);
  console.log(`wrote ${path.relative(process.cwd(), out)} (${(html.length / 1024).toFixed(0)} KB)`);
}
