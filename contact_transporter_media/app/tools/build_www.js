#!/usr/bin/env node
/*
 * build_www.js — 各アプリの www を組み立てる。
 *   node app/tools/build_www.js <transporter|chatgpt|ufo> [outDir]
 * 出力: <outDir>/index.html (エンジン + アプリ + mp4-muxer + データを 1 つの <script> に内包)
 *       <outDir>/fonts/ipag.ttf (IPA ゴシック, IPA Font License v1.0)
 */
"use strict";
const fs = require("fs");
const path = require("path");

const APP = process.argv[2];
const APPS = ["transporter", "chatgpt", "ufo"];
if (!APPS.includes(APP)) {
  console.error("usage: build_www.js <" + APPS.join("|") + "> [outDir]");
  process.exit(2);
}
const ROOT = path.resolve(__dirname, "..");
const MEDIA = path.resolve(ROOT, "..");
const out = path.resolve(process.argv[3] || path.join(ROOT, "www-" + APP));

function read(p) { return fs.readFileSync(path.join(ROOT, p), "utf8"); }

/* 方程式レジストリ: [id, status, 先頭タグ, 式] */
const reg = JSON.parse(fs.readFileSync(path.join(MEDIA, "data", "equations.json"), "utf8"));
let registry = reg.map(e => [e.id, e.status, (e.tags && e.tags[0]) || "OTHER", e.eq]);
if (APP === "ufo") registry = registry.filter(r => r[0].startsWith("UFO."));
if (APP === "chatgpt") registry = [];

const parts = [
  "/* mp4-muxer (MIT) — vendor/mp4-muxer.LICENSE */",
  read("vendor/mp4-muxer.js"),
  "window.BP_REGISTRY = " + JSON.stringify(registry) + ";",
  read("src/engine.js"),
  read("src/" + APP + ".js"),
];
const script = parts.join("\n;\n").replace(/<\/script/gi, "<\\/script");
let html = read("src/index.html").replace("<!--SCRIPTS-->", () => "<script>\n" + script + "\n</script>");

fs.mkdirSync(path.join(out, "fonts"), { recursive: true });
fs.writeFileSync(path.join(out, "index.html"), html);
fs.copyFileSync(path.join(ROOT, "fonts", "ipag.ttf"), path.join(out, "fonts", "ipag.ttf"));
fs.copyFileSync(path.join(ROOT, "fonts", "IPA_Font_License.txt"), path.join(out, "fonts", "IPA_Font_License.txt"));
fs.copyFileSync(path.join(ROOT, "vendor", "mp4-muxer.LICENSE"), path.join(out, "mp4-muxer.LICENSE"));
console.log("built", APP, "→", out, "(" + (html.length / 1024).toFixed(0) + " KB, registry " + registry.length + ")");
