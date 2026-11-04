#!/usr/bin/env node
/*
 * build-linear-www.js — 反重力リニア 3D シミュレータ (Artifact 版,
 * app/badalinear_3d.html) を、Electron / Cordova に同梱できるオフライン自己完結の
 * linear-app/www/index.html へ変換する (cdnjs の Three.js → 同梱 ./three.min.js、
 * 完全な HTML 文書へラップ)。   使い方: node tools/build-linear-www.js (bada_linear_os/ で)
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "app", "badalinear_3d.html");
const OUTDIR = path.join(ROOT, "linear-app", "www"), OUT = path.join(OUTDIR, "index.html");
const VENDOR = path.join(OUTDIR, "three.min.js");
if (!fs.existsSync(SRC)) throw new Error("source not found: " + SRC);
if (!fs.existsSync(VENDOR)) throw new Error("vendored three.min.js not found: " + VENDOR);
let body = fs.readFileSync(SRC, "utf8");
const cdnRe = /<script\s+src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/three\.js\/[^"]+"><\/script>/i;
if (!cdnRe.test(body)) throw new Error("CDN three.js <script> tag not found");
body = body.replace(cdnRe, '<script src="./three.min.js"></script>');
if (/cdnjs\.cloudflare\.com/.test(body)) throw new Error("residual cdnjs reference");
const doc = `<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="color-scheme" content="dark">\n<style>html,body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n${body}\n</body>\n</html>\n`;
fs.mkdirSync(OUTDIR, { recursive: true }); fs.writeFileSync(OUT, doc, "utf8");
const w = fs.readFileSync(OUT, "utf8");
const checks = [["./three.min.js", w.includes('src="./three.min.js"')], ["no cdnjs", !w.includes("cdnjs.cloudflare.com")],
  ["title", /<title>[^<]+<\/title>/.test(w)], ["app markup", w.includes('id="view3d"') && w.includes("反重力リニア")],
  ["physics", w.includes("sigma") && w.includes("cosh")], ["doctype", w.startsWith("<!doctype html>")]];
let ok = true; for (const [n, p] of checks) { console.log((p ? "  ok  " : " FAIL ") + n); ok = ok && p; }
if (!ok) throw new Error("self-check failed");
console.log(`\nwrote ${path.relative(ROOT, OUT)} (${(Buffer.byteLength(doc) / 1024).toFixed(1)} KB) + three.min.js — offline ready`);
