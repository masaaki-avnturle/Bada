#!/usr/bin/env node
/*
 * build_single.js — Ω-Whispered を「1 ファイルの HTML」にまとめるビルドスクリプト
 * Masaaki Yamaguchi / Bada — bio_medicine/omega_whispered
 *
 * www/index.html の <script src="..."> をすべて実体で埋め込み、
 * どこにでも置けて・オフラインでも動く単一ファイル download/omega-whispered.html を出力する。
 *
 *   node build_single.js            # 生成
 *   node build_single.js --check    # 生成物が最新かどうかだけ検査(CI 用, 差異があれば exit 1)
 *
 * 依存ゼロ(Node 18+)。
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const SRC = path.join(ROOT, "www", "index.html");
const OUT_DIR = path.join(ROOT, "download");
const OUT = path.join(OUT_DIR, "omega-whispered.html");
const CHECK = process.argv.includes("--check");

function build() {
  let html = fs.readFileSync(SRC, "utf8");
  const inlined = [];

  html = html.replace(/[ \t]*<script src="([^"]+)"><\/script>\r?\n?/g, (m, src) => {
    const file = path.join(ROOT, "www", src);
    if (!fs.existsSync(file)) throw new Error("script not found: " + src);
    let js = fs.readFileSync(file, "utf8");
    /* HTML 中に埋め込むため、終了タグに見える並びだけ無害化する */
    js = js.replace(/<\/script>/gi, "<\\/script>");
    inlined.push(src + " (" + js.length.toLocaleString() + " bytes)");
    return "<script>\n/* ===== inlined: www/" + src + " ===== */\n" + js + "\n</script>\n";
  });

  if (!inlined.length) throw new Error("no <script src> found — index.html の構成が変わっていませんか");

  const banner =
    "<!--\n" +
    "  Ω-Whispered — 単一ファイル版 (自動生成)\n" +
    "  このファイルは bio_medicine/omega_whispered/build_single.js が\n" +
    "  www/index.html と www/*.js から生成したものです。直接編集しないでください。\n" +
    "  ダウンロードしてブラウザで開くだけで動作します(インターネット接続・インストール不要)。\n" +
    "  再生成: node build_single.js\n" +
    "-->\n";
  html = html.replace(/^<!DOCTYPE html>\r?\n/i, "<!DOCTYPE html>\n" + banner);

  return { html, inlined };
}

const built = build();
fs.mkdirSync(OUT_DIR, { recursive: true });

if (CHECK) {
  const current = fs.existsSync(OUT) ? fs.readFileSync(OUT, "utf8") : "";
  if (current !== built.html) {
    console.error("✗ download/omega-whispered.html が www/ の内容と一致しません。");
    console.error("  `node bio_medicine/omega_whispered/build_single.js` を実行してコミットしてください。");
    process.exit(1);
  }
  console.log("✓ download/omega-whispered.html は最新です");
  process.exit(0);
}

fs.writeFileSync(OUT, built.html);
console.log("埋め込み:");
built.inlined.forEach((s) => console.log("  - " + s));
console.log("出力: " + path.relative(process.cwd(), OUT) +
            " (" + built.html.length.toLocaleString() + " bytes)");
