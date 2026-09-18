/*
 * build-bada.js — Bada UltraNetwork の Bada ソースを 1 本にまとめて検証する
 *
 *   node ultra_network/tools/build-bada.js
 *
 * ultra_network/bada/ のモジュールを順に連結し、
 *
 *   dist/ultra-full.bada      01-09 + 10_main      (デモ本体)
 *   dist/ultra-selftest.bada  01-09 + 11_selftest  (自己診断)
 *
 * を作る。どちらも実際に走らせ、出力に決められた印が揃うまで
 * ファイルを書き出さない (bada_gui_ide/tools/build-zone-browser.js と
 * 同じ流儀)。
 *
 * Bada の既定ステップ上限は 2000 万で、この全層プログラムはそれを
 * 超える (SHA-256 と HMAC をソフトウェアのビット演算で回すため)。
 * ここでは上限を上げて走らせる。bada-cli から直接走らせたいときは
 *   node ultra_network/tools/run-bada.js <file.bada>
 * を使う。
 */
"use strict";
const fs = require("fs");
const path = require("path");

const Bada = require(path.join(__dirname, "..", "..", "bada_gui_ide", "www", "bada.js"));

const BADA_DIR = path.join(__dirname, "..", "bada");
const DIST_DIR = path.join(__dirname, "..", "dist");
const MAX_STEPS = 800000000;

/* 連結の順序。下の層から上へ積む。 */
const LIB = ["01_core.bada", "02_sha256.bada", "03_jones.bada", "04_zone.bada",
             "05_ntt.bada", "06_plc.bada", "07_json.bada", "08_msgmux.bada",
             "09_streams.bada"];

const TARGETS = [
  {
    out: "ultra-full.bada",
    parts: LIB.concat(["10_main.bada"]),
    title: "デモ本体",
    must: [
      "BADA ULTRA NETWORK -- done",
      "STATUS 200 zone-delivered",
      "STATUS 409 zone-guard-reject",
      "STATUS 495 quantum-channel-compromised",
      "STATUS 503 plc-pb-crc",
      "inverse ok: true"
    ]
  },
  {
    out: "ultra-selftest.bada",
    parts: LIB.concat(["11_selftest.bada"]),
    title: "自己診断",
    must: ["SELFTEST-RESULT"]
  }
];

function banner(name, parts) {
  return [
    "# ==============================================================",
    "#  " + name,
    "#  Bada UltraNetwork — 自動生成。編集しないこと。",
    "#  元は ultra_network/bada/ の各モジュール:",
  ].concat(parts.map((p) => "#    " + p)).concat([
    "#  作り直すには: node ultra_network/tools/build-bada.js",
    "# ==============================================================",
    ""
  ]).join("\n");
}

let failed = 0;

for (const t of TARGETS) {
  const parts = t.parts.map((f) => {
    const p = path.join(BADA_DIR, f);
    if (!fs.existsSync(p)) { console.error("missing module: " + f); process.exit(1); }
    return fs.readFileSync(p, "utf8");
  });
  const src = banner(t.out, t.parts) + parts.join("\n");

  let out = "";
  const t0 = Date.now();
  const r = Bada.run(src, { maxSteps: MAX_STEPS, out: (s) => { out += s + "\n"; } });
  const ms = Date.now() - t0;

  const lines = src.split("\n").length;
  console.log("── " + t.out + "  (" + t.title + ")");
  console.log("   モジュール " + t.parts.length + " 本 / " + lines + " 行 / " +
              src.length.toLocaleString() + " 文字");

  if (r.parseErrors && r.parseErrors.length) {
    console.error("   構文エラー " + r.parseErrors.length + " 件:");
    r.parseErrors.slice(0, 10).forEach((e) => console.error("     " + e));
    failed++;
    continue;
  }
  if (!r.ok || r.error) {
    console.error("   実行に失敗: " + (r.error || "(ステップ上限か)"));
    failed++;
    continue;
  }

  let missing = t.must.filter((m) => out.indexOf(m) < 0);
  if (missing.length) {
    console.error("   出力に必要な印が無い:");
    missing.forEach((m) => console.error("     " + m));
    failed++;
    continue;
  }

  /* 自己診断は合否の数まで見る */
  const m = out.match(/SELFTEST-RESULT (\d+) (\d+)/);
  if (m) {
    const passed = parseInt(m[1], 10), total = parseInt(m[2], 10);
    if (passed !== total) {
      console.error("   自己診断が不合格: " + passed + " / " + total);
      out.split("\n").filter((l) => l.indexOf("FAIL") >= 0).forEach((l) => console.error("     " + l));
      failed++;
      continue;
    }
    console.log("   自己診断 " + passed + " / " + total + " 合格");
  }

  fs.mkdirSync(DIST_DIR, { recursive: true });
  fs.writeFileSync(path.join(DIST_DIR, t.out), src);
  fs.writeFileSync(path.join(DIST_DIR, t.out.replace(/\.bada$/, ".out.txt")), out);
  console.log("   台帳 " + r.ledgerLen + " 件 / 実行 " + ms + " ms");
  console.log("   -> dist/" + t.out + "  (出力は dist/" + t.out.replace(/\.bada$/, ".out.txt") + ")");
  console.log("");
}

if (failed) { console.error("ビルド失敗: " + failed + " 件"); process.exit(1); }
console.log("Bada UltraNetwork — Bada ソースのビルドと検証 OK");
