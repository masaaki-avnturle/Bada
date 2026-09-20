#!/usr/bin/env node
/* ============================================================================
 * build-lambda-driver.js — LÆVATEIN (Λ ドライバ無力化シミュレータ) を
 * 単一の自己完結 HTML としてビルドする。
 *
 * 出力: ../dist/lambda-driver.html
 *   www/lambda_driver.js を www/lambda-driver.page.html の
 *   <<LAMBDA_DRIVER_CORE>> 位置へ inline するだけ。外部依存なし。
 *
 * ビルド前に、実在の物理量に対するセルフチェックを走らせる。
 * 架空の部分 (Λ ドライバ) は検証できないが、実在の部分 —
 * 光子エネルギー・Landauer 限界・電界発光冷却の条件・Kauffman ブラケット・
 * 不完全ガンマの最適打ち切り — はすべて既知の値と突き合わせる。
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");

const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

const LD = require(path.join(WWW, "lambda_driver.js"));

let failed = 0;
function check(name, got, want, tol) {
  const ok = Math.abs(got - want) <= Math.abs(want) * tol;
  console.log((ok ? "  ok   " : "  FAIL ") + name + " = " + got + (ok ? "" : "  (want " + want + " ±" + tol * 100 + "%)"));
  if (!ok) failed++;
}
function assert(name, cond, detail) {
  console.log((cond ? "  ok   " : "  FAIL ") + name + (detail ? "  " + detail : ""));
  if (!cond) failed++;
}

console.log("self-check (実在の物理量との照合):");

/* --- 光子エネルギー: hc/λ --- */
check("450nm 光子 [eV]", LD.photonEnergyEV(450), 2.7552, 1e-4);
check("1000nm 光子 [eV]", LD.photonEnergyEV(1000), 1.239842, 1e-5);

/* --- Landauer 限界 k_B T ln2 --- */
check("Landauer @300K [J/bit]", LD.CONST.K_B * 300 * Math.LN2, 2.8710e-21, 1e-3);

/* --- 電界発光冷却の条件と収支 --- */
{
  const el = LD.elCooling({ lambdaNm: 450, biasV: 0.1, eqe: 0.7, currentA: 1 });
  check("冷却しきい EQE = qV/ħω", el.etaThreshold, 0.1 / 2.7552, 1e-4);
  check("1 電子あたり吸熱 [eV]", el.perElectronEV, 0.7 * 2.7552 - 0.1, 1e-4);
  check("COP = η·ħω/(qV) − 1", el.cop, 0.7 * 2.7552 / 0.1 - 1, 1e-4);
  assert("η > qV/ħω なら冷却する", el.cools === true);
  const warm = LD.elCooling({ lambdaNm: 450, biasV: 2.6, eqe: 0.7, currentA: 1 });
  assert("η < qV/ħω なら冷却しない", warm.cools === false,
    "(V=2.6V で しきい " + warm.etaThreshold.toFixed(3) + " > η=0.7)");
}

/* --- Kauffman ブラケット: 1 交差の閉ブレイドは -A^{-3} --- */
{
  const r = LD.kauffmanBracket(LD.braidDiagram(1), 1.3);
  check("Kauffman 1 交差 (A=1.3)", r.value, -Math.pow(1.3, -3), 1e-9);
  assert("操作数が数えられている", r.ops > 0, "(" + r.ops + " ops)");
}

/* --- Γ 大域的部分積分多様体 ---
   Γ(s,x) の漸近級数は k ≈ s+x で最小になる (最適打ち切り)。
   最小項は指数的に小さく、x を増やすと漏れ比 ρ は単調に減る。        */
{
  for (const x of [20, 30, 50]) {
    const g = LD.gammaManifold(2.5, x);
    const near = Math.abs(g.optimalTruncation - (2.5 + x)) <= 2;
    assert("最適打ち切り k* ≈ s+x  (x=" + x + ")", near,
      "k*=" + g.optimalTruncation + " vs s+x=" + (2.5 + x).toFixed(1));
    assert("最小項 < e^{-x/2}  (x=" + x + ")", g.minTerm < Math.exp(-x / 2),
      "min=" + g.minTerm.toExponential(2));
  }
  const a = LD.gammaManifold(2.5, 20).leakFraction;
  const b = LD.gammaManifold(2.5, 40).leakFraction;
  assert("x を増やすと漏れ ρ が減る", b < a,
    "ρ(20)=" + a.toExponential(2) + " → ρ(40)=" + b.toExponential(2));
  /* Γ(s,x) の漸近評価を Simpson 則の数値積分と突き合わせる。
     最適打ち切りなので誤差は最小項の桁 (x=25 で ~1e-13 相対) に収まるはず。 */
  const s = 2.5, x = 25, n = 200000, hi = x + 250, h = (hi - x) / n;
  const f = (t) => Math.pow(t, s - 1) * Math.exp(-t);
  let num = f(x) + f(hi);
  for (let i = 1; i < n; i++) num += f(x + i * h) * (i % 2 ? 4 : 2);
  num *= h / 3;
  check("Γ(2.5,25) 漸近 vs Simpson 積分", LD.gammaManifold(s, x).gammaAsym, num, 1e-8);
}

/* --- Λ (Dalanversian) --- */
check("Λ(e) = e^{e·ln e} = e^e", LD.dalanversian(Math.E), Math.exp(Math.E), 1e-12);
assert("Λ(1) = 1", Math.abs(LD.dalanversian(1) - 1) < 1e-12);

/* --- 全体: 既定条件では冷却が律速になる --- */
{
  const r = LD.simulate({});
  assert("既定条件で収支が閉じない", r.verdict.result === "fails");
  assert("律速は冷却能力", r.verdict.limiting === "cooling-power", "(" + r.verdict.limiting + ")");
  assert("Γ 抑制は効いている (ρ < 1e-10)", r.budget.leakFraction < 1e-10,
    "ρ=" + r.budget.leakFraction.toExponential(2));
  assert("制御計算は間に合う", r.jones.computeCloses === true,
    "(" + r.jones.computeS.toExponential(2) + " s)");
  assert("現実との差が 20 桁以上", r.led.realityGapOrders > 20,
    "10^" + r.led.realityGapOrders.toFixed(1));
  console.log("  ..   既定: 排熱要求 " + r.budget.loadW.toExponential(3)
    + " W / 冷却 " + r.led.totalW.toExponential(3) + " W / 差 10^"
    + r.led.realityGapOrders.toFixed(1));
  /* 交差数を上げると制御計算が律速に変わる */
  const slow = LD.simulate({ crossings: 22, opsRate: 1e9 });
  assert("遅い制御系では compute が律速", slow.verdict.limiting === "control-compute",
    "(" + slow.verdict.limiting + ")");
}

if (failed) { console.error("self-check failed: " + failed + " 件"); process.exit(1); }
console.log("self-check OK\n");

/* -------------------------------- build --------------------------------- */
const core = fs.readFileSync(path.join(WWW, "lambda_driver.js"), "utf8");
const page = fs.readFileSync(path.join(WWW, "lambda-driver.page.html"), "utf8");
const MARK = "/*<<LAMBDA_DRIVER_CORE>>*/";
if (page.indexOf(MARK) < 0) { console.error("marker " + MARK + " not found"); process.exit(1); }

const banner =
  "/* LÆVATEIN " + LD.VERSION + " — Λ ドライバ無力化シミュレータ (single-file build)\n" +
  " * masaaki-avnturle/Bada · bada_gui_ide/tools/build-lambda-driver.js が生成\n" +
  " * 編集は www/lambda_driver.js と www/lambda-driver.page.html を直接。 */\n";

const html = page.replace(MARK, banner + core);
const outFile = path.join(DIST, "lambda-driver.html");
fs.writeFileSync(outFile, html);

const ext = html.match(/<(?:script|link|img)\b[^>]*\b(?:src|href)\s*=\s*["'](?!#)[^"']+["']/gi);
if (ext) { console.error("外部参照が残っています:\n" + ext.join("\n")); process.exit(1); }

console.log("built " + path.relative(IDE, outFile) + "  (" + (html.length / 1024).toFixed(1) + " KB, 自己完結)");

/* ネイティブ アプリ (Windows EXE / Ubuntu AppImage・deb / Android APK) の
   www/index.html としても配置する。 */
const APPWWW = path.join(IDE, "laevatein-app", "www");
if (fs.existsSync(path.join(IDE, "laevatein-app"))) {
  fs.mkdirSync(APPWWW, { recursive: true });
  fs.writeFileSync(path.join(APPWWW, "index.html"), html);
  console.log("staged laevatein-app/www/index.html (Electron / Cordova)");
}
