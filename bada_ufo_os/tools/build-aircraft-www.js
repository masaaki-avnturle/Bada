#!/usr/bin/env node
/*
 * build-aircraft-www.js
 * ---------------------------------------------------------------------------
 * 反重力発生器 航空機アプリ (Artifact 版, app/antigravity_aircraft_3d.html) を、
 * ネイティブ アプリ (Electron / Cordova) に同梱できる完全自己完結・オフライン
 * 動作の www/index.html へ変換する。
 *
 *   - Artifact 版は Three.js を cdnjs から読み込むが、ネイティブ版はオフライン
 *     で動く必要があるため、同梱の ./three.min.js (r128, npm three@0.128.0)
 *     への参照に差し替える。
 *   - Artifact 版は publish 時に <!doctype>/<head> が補われる断片なので、ここで
 *     完全な HTML 文書 (charset / viewport / [hidden] リセット) にラップする。
 *
 * 使い方:  node tools/build-aircraft-www.js   (bada_ufo_os/ で実行)
 * 出力:    aircraft-app/www/index.html        (ビルド生成物, git 管理外)
 * 前提:    aircraft-app/www/three.min.js      (vendored, git 管理)
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");                       // bada_ufo_os/
const SRC = path.join(ROOT, "app", "antigravity_aircraft_3d.html");
const OUTDIR = path.join(ROOT, "aircraft-app", "www");
const OUT = path.join(OUTDIR, "index.html");
const VENDOR = path.join(OUTDIR, "three.min.js");

function main() {
  if (!fs.existsSync(SRC)) throw new Error("source not found: " + SRC);
  if (!fs.existsSync(VENDOR)) throw new Error("vendored three.min.js not found: " + VENDOR);

  let body = fs.readFileSync(SRC, "utf8");

  // 1) cdnjs の Three.js を同梱ローカルへ差し替え (どの版数 r1xx でも一致)
  const cdnRe = /<script\s+src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/three\.js\/[^"]+"><\/script>/i;
  if (!cdnRe.test(body)) throw new Error("CDN three.js <script> tag not found in source");
  body = body.replace(cdnRe, '<script src="./three.min.js"></script>');

  if (/cdnjs\.cloudflare\.com/.test(body)) {
    throw new Error("residual cdnjs reference remains after rewrite");
  }

  // 2) 完全な HTML 文書にラップ (Artifact skeleton 相当の最小 head + reset)
  const doc = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark">
<style>
  html,body{margin:0}
  img{max-width:100%}
  [hidden]{display:none!important}
</style>
</head>
<body>
${body}
</body>
</html>
`;

  fs.mkdirSync(OUTDIR, { recursive: true });
  fs.writeFileSync(OUT, doc, "utf8");

  // 3) セルフチェック
  const written = fs.readFileSync(OUT, "utf8");
  const checks = [
    ['./three.min.js reference', written.includes('src="./three.min.js"')],
    ['no cdnjs', !written.includes("cdnjs.cloudflare.com")],
    ['has <title>', /<title>[^<]+<\/title>/.test(written)],
    ['has app markup', written.includes('id="view3d"') && written.includes('反重力発生器')],
    ['has physics core', written.includes("antigravCoupling") && written.includes("cosh")],
    ['doctype', written.startsWith("<!doctype html>")],
  ];
  let ok = true;
  for (const [name, pass] of checks) {
    console.log((pass ? "  ok  " : " FAIL ") + name);
    if (!pass) ok = false;
  }
  if (!ok) throw new Error("self-check failed");

  const kb = (Buffer.byteLength(doc, "utf8") / 1024).toFixed(1);
  const vkb = (fs.statSync(VENDOR).size / 1024).toFixed(0);
  console.log(`\nwrote ${path.relative(ROOT, OUT)} (${kb} KB) + vendored three.min.js (${vkb} KB) — offline ready`);
}

main();
