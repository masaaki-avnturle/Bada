#!/usr/bin/env node
/*
 * build.js — Bada PatchGuard の組み立て
 *
 *   node bada_patchguard/tools/build.js          # index.html と dist/badapatchguard.js (CLI 単一ファイル版)
 *   node bada_patchguard/tools/build.js --check  # index.html が src と一致するか検査
 *
 * Bada 処理系は BadaClaude と共有します (../bada_claude/src/engine.js)。
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const rd = f => fs.readFileSync(path.join(ROOT, f), "utf8");
const ENGINE = path.join(ROOT, "..", "bada_claude", "src", "engine.js");

function readTree(dir) {
  const out = {};
  (function walk(d, rel) {
    for (const e of fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name < b.name ? -1 : 1)) {
      if (e.isDirectory()) walk(path.join(d, e.name), rel + e.name + "/");
      else out[rel + e.name] = fs.readFileSync(path.join(d, e.name), "utf8");
    }
  })(dir, "");
  return out;
}

function noScriptClose(name, s) { if (/<\/script/i.test(s)) throw new Error(name + " must not contain </script"); return s; }

function buildHtml() {
  const ex = p => readTree(path.join(ROOT, "examples", p));
  const examples = { base: ex("base"), risky: [ex("after_risky")], safe: [ex("after_safe")], fold: [ex("fold_step1"), ex("fold_step2")] };
  const parts = {
    "/*__EXAMPLES__*/": JSON.stringify(examples).replace(/<\//g, "<\\/").replace(/<!--/g, "<\\!--"),
    "/*__GUARD__*/": noScriptClose("guard.bada", rd("src/guard.bada")),
    "/*__ENGINE__*/": noScriptClose("engine.js", fs.readFileSync(ENGINE, "utf8")),
    "/*__PHP__*/": noScriptClose("php.js", rd("src/php.js")),
    "/*__DIFF__*/": noScriptClose("diff.js", rd("src/diff.js")),
    "/*__CORE__*/": noScriptClose("core.js", rd("src/core.js")),
    "/*__APP__*/": noScriptClose("app.js", rd("src/app.js"))
  };
  let html = rd("src/ui.html");
  for (const [k, v] of Object.entries(parts)) {
    if (!html.includes(k)) throw new Error("marker missing: " + k);
    html = html.replace(k, () => v);
  }
  return html;
}

/* CLI を依存なしの 1 ファイルに (サーバーへ置いてそのまま node で動く) */
function buildCli() {
  const mod = (name, src) => `${JSON.stringify(name)}: function (module, exports) {\n${src}\n}`;
  const mods = [
    mod("engine", fs.readFileSync(ENGINE, "utf8")), mod("php", rd("src/php.js")),
    mod("diff", rd("src/diff.js")), mod("core", rd("src/core.js"))
  ].join(",\n");
  const cli = rd("cli.js").replace(/^#!.*\n/, "");
  return `#!/usr/bin/env node
/* badapatchguard.js — Bada Reviser PatchGuard CLI (単一ファイル版 / tools/build.js が生成) */
"use strict";
const __PG_BUNDLE__ = (function () {
  const defs = {
${mods}
  };
  const cache = {};
  const req = n => { if (!cache[n]) { const m = { exports: {} }; defs[n].call(m.exports, m, m.exports); cache[n] = m.exports; } return cache[n]; };
  return { Engine: req("engine"), PHP: req("php"), Diff: req("diff"), Core: req("core"), guardSrc: ${JSON.stringify(rd("src/guard.bada"))} };
})();
${cli}`;
}

const out = path.join(ROOT, "index.html");
const html = buildHtml();
if (process.argv.includes("--check")) {
  const cur = fs.existsSync(out) ? fs.readFileSync(out, "utf8") : "";
  if (cur !== html) { console.error("bada_patchguard/index.html is stale — run: node bada_patchguard/tools/build.js"); process.exit(1); }
  console.log("index.html is up to date");
} else {
  fs.writeFileSync(out, html);
  fs.mkdirSync(path.join(ROOT, "dist"), { recursive: true });
  const cliOut = path.join(ROOT, "dist", "badapatchguard.js");
  fs.writeFileSync(cliOut, buildCli(), { mode: 0o755 });
  console.log(`wrote ${path.relative(process.cwd(), out)} (${(html.length / 1024).toFixed(0)} KB) and ${path.relative(process.cwd(), cliOut)}`);
}
