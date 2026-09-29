#!/usr/bin/env node
/*
 * build.js — src/ を 1 枚の自己完結 HTML (dist/<アプリ>/www/index.html) にまとめる
 *
 *   node tools/build.js [contactgpt|transporter|ufo|studio|all]   (既定: all)
 *   アプリの定義 (名前・ID・含めるタブ) は apps.json。
 *   方程式 2111 本 (data/equations.json) と ContactGPT の学習済み重み
 *   (data/contactgpt_weights.json) も埋め込むので、オフラインで動きます。
 *   Bada ソース (bada/ 以下の .bada) も仮想ファイル表として埋め込みます。
 *   このファイルを Android (Cordova) / Windows・Linux (Electron) が同梱します。
 */
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), SRC = path.join(ROOT, "src"), DATA = path.join(ROOT, "data");
const APPS = JSON.parse(fs.readFileSync(path.join(ROOT, "apps.json"), "utf8"));
const which = process.argv[2] || "all";
if (which !== "all" && !APPS[which]) { console.error(`unknown app ${which} (${Object.keys(APPS).join(" / ")} / all)`); process.exit(1); }
const ORDER = ["physics.js", "gpt.js", "cad.js", "drafting.js", "viewer.js", "chat.js", "bada.js", "badalib.js", "app.js"];

const read = (p) => fs.readFileSync(p, "utf8");
const safe = (s) => s.replace(/<\/(script)/gi, "<\\/$1").replace(/<!--/g, "<\\!--");
const pkg = JSON.parse(read(path.join(ROOT, "app", "electron", "package.json")));
const wPath = path.join(DATA, "contactgpt_weights.json");
const weights = fs.existsSync(wPath) ? read(wPath) : "null";
if (weights === "null") console.warn("warning: data/contactgpt_weights.json がありません (ContactGPT は生成なしで動作)");

const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function build(key) {
  const A = APPS[key];
  let html = read(path.join(SRC, "index.html"));
  // String.prototype.split/join ではなく関数置換で $ を安全に扱う
  function put(key, val) { const k = `/*@@${key}@@*/`; const i = html.indexOf(k); if (i < 0) throw new Error("placeholder " + key); html = html.slice(0, i) + val + html.slice(i + k.length); }
  put("STYLE", read(path.join(SRC, "style.css")));
  put("GPT_SRC", safe(read(path.join(SRC, "gpt.js"))));
  put("EQUATIONS", safe(read(path.join(DATA, "equations.json")).replace(/\n/g, "")));
  put("WEIGHTS", A.weights ? safe(weights) : "null");
  // Bada ソース (apps / lib / examples) を仮想ファイル表として埋め込む
  const badaFiles = {};
  (function walk(d) {
    for (const f of fs.readdirSync(d).sort()) {
      const p = path.join(d, f);
      if (fs.statSync(p).isDirectory()) walk(p);
      else if (f.endsWith(".bada")) badaFiles[path.relative(path.join(ROOT, "bada"), p).split(path.sep).join("/")] = read(p);
    }
  })(path.join(ROOT, "bada"));
  put("BADA", safe(JSON.stringify(badaFiles)));
  put("BUILD", JSON.stringify({ version: pkg.version, date: new Date().toISOString().slice(0, 10) }));
  put("APP", JSON.stringify(Object.assign({ key }, A)));
  html = html.split("@@APP_TITLE@@").join(esc(A.title)).split("@@APP_SUBTITLE@@").join(esc(A.subtitle));
  put("SCRIPTS", ORDER.map((f) => `\n/* ---- ${f} ---- */\n` + safe(read(path.join(SRC, f)))).join("\n"));

  const OUT = path.join(ROOT, "dist", key, "www");
  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, "index.html"), html);
  console.log(`dist/${key}/www/index.html  ${(html.length / 1024).toFixed(0)} KB  (${A.name}: ${A.tabs.join(", ")})`);
}
for (const key of which === "all" ? Object.keys(APPS) : [which]) build(key);
