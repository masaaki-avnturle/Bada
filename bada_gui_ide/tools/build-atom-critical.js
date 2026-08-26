#!/usr/bin/env node
/* ============================================================================
 * build-atom-critical.js — ACPI (原子の臨界期の強度シミュレータ) を
 * 単一の自己完結 HTML ファイルとしてビルドする。
 *
 * 出力: ../dist/atom-critical.html
 *   www/atom_critical.js (モデルコア) を www/atom-critical.page.html の
 *   <<ATOM_CRITICAL_CORE>> 位置へ inline するだけ。外部依存は一切なく、
 *   1 ファイルをダウンロードしてブラウザで開けばオフラインで動作する。
 *
 * ビルド前に、既知の物理値に対するセルフチェックを実行する:
 *   - 原子単位の強度       I_a  = 3.5094e16 W/cm^2
 *   - 水素の障壁抑制強度   I_cr = 1.37e14  W/cm^2
 *   - 水素の ADK 率        w(F) = (4/F) e^{-2/(3F)} の 2 % 以内
 *   - Kauffman ブラケット  1 交差の閉ブレイド -> -A^{-3}
 *   - Ar/800nm/2e14 の U_p = 11.95 eV, gamma_K = 0.81
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");

const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

const AC = require(path.join(WWW, "atom_critical.js"));

/* ------------------------------ self-check ------------------------------ */
let failed = 0;
function check(name, got, want, tol) {
  const ok = Math.abs(got - want) <= Math.abs(want) * tol;
  console.log((ok ? "  ok   " : "  FAIL ") + name + " = " + got + (ok ? "" : "  (want " + want + " ±" + tol * 100 + "%)"));
  if (!ok) failed++;
}
console.log("self-check (既知の物理値との照合):");
check("I_a [W/cm^2]", AC.CONST.I_AU, 3.5094e16, 1e-4);
check("H  I_cr [W/cm^2]", AC.criticalIntensity(13.5984, 1), 1.37e14, 0.01);
check("Ar I_cr [W/cm^2]", AC.criticalIntensity(15.7596, 1), 2.47e14, 0.01);
{
  const ap = AC.adkParams(13.5984, 1, 0), F = 0.05;
  check("H  ADK w(0.05) [a.u.]", AC.adkRate(F, ap), (4 / F) * Math.exp(-2 / (3 * F)), 0.02);
}
check("Kauffman <1-crossing>(A=1.3)", AC.kauffmanBracket(AC.braidDiagram(1), 1.3), -Math.pow(1.3, -3), 1e-9);
check("U_p (Ar, 800nm, 2e14) [eV]", AC.ponderomotive(2e14, 800), 11.95, 0.01);
check("gamma_K (Ar, 800nm, 2e14)", AC.keldysh(15.7596, 2e14, 800), 0.812, 0.01);
{
  const r = AC.simulate({ element: "Ar", intensity: 6e14, lambdaNm: 800, fwhmFs: 8, steps: 8000 });
  console.log("  ..   Ar 6e14/800nm/8fs -> 臨界期 " + r.critical.durationFs.toFixed(3) + " fs, "
    + r.critical.count + " 窓, 電離 " + (r.result.ionization * 100).toFixed(3) + " %");
  if (!r.critical.exists) { console.log("  FAIL 臨界期が検出されない"); failed++; }
  if (!(r.result.ionization > 0.9)) { console.log("  FAIL 6e14 W/cm^2 で Ar がほぼ完全電離しない"); failed++; }
  const sub = AC.simulate({ element: "Ar", intensity: 1e13, lambdaNm: 800, fwhmFs: 8, steps: 4000 });
  if (sub.critical.exists) { console.log("  FAIL 亜臨界 (1e13) なのに臨界期が出る"); failed++; }
  else console.log("  ok   Ar 1e13 (亜臨界) -> 臨界期なし");
}
if (failed) { console.error("self-check failed: " + failed + " 件"); process.exit(1); }
console.log("self-check OK\n");

/* -------------------------------- build --------------------------------- */
const core = fs.readFileSync(path.join(WWW, "atom_critical.js"), "utf8");
const page = fs.readFileSync(path.join(WWW, "atom-critical.page.html"), "utf8");
const MARK = "/*<<ATOM_CRITICAL_CORE>>*/";
if (page.indexOf(MARK) < 0) { console.error("marker " + MARK + " not found in atom-critical.page.html"); process.exit(1); }

const banner =
  "/* ACPI " + AC.VERSION + " — 原子の臨界期の強度シミュレータ (single-file build)\n" +
  " * masaaki-avnturle/Bada · bada_gui_ide/tools/build-atom-critical.js が生成\n" +
  " * 編集は www/atom_critical.js と www/atom-critical.page.html を直接。 */\n";

const html = page.replace(MARK, banner + core);
const outFile = path.join(DIST, "atom-critical.html");
fs.writeFileSync(outFile, html);

/* 生成物のサニティ: <script src=…> / <link href=…> の外部参照がないこと */
const ext = html.match(/<(?:script|link|img)\b[^>]*\b(?:src|href)\s*=\s*["'](?!#)[^"']+["']/gi);
if (ext) { console.error("外部参照が残っています:\n" + ext.join("\n")); process.exit(1); }

console.log("built " + path.relative(IDE, outFile) + "  (" + (html.length / 1024).toFixed(1) + " KB, 自己完結)");
