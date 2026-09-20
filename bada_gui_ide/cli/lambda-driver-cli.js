#!/usr/bin/env node
/* ============================================================================
 * lambda-driver-cli.js — LÆVATEIN コマンドライン版
 *   Λ ドライバ無力化シミュレータ (暴走エネルギーの熱収支)
 *
 *   node cli/lambda-driver-cli.js run      [opts]      # 要約
 *   node cli/lambda-driver-cli.js csv      <out.csv>   # 時系列を CSV
 *   node cli/lambda-driver-cli.js json     [out.json]  # 全結果を JSON
 *   node cli/lambda-driver-cli.js gamma    [opts]      # Γ 部分積分層の表
 *   node cli/lambda-driver-cli.js sweep    [opts]      # 深さ x を掃引
 *   node cli/lambda-driver-cli.js cooling  [opts]      # LED 冷却の成立範囲
 *   node cli/lambda-driver-cli.js selftest             # 実在物理と照合
 *
 * 主なオプション:
 *   --p0 1e6         初期出力 [W]          --doubling 10   倍加時間 [ns]
 *   --emax 4.184e12  総エネルギー [J]      --horizon 600   観測時間 [ns]
 *   --x 30           部分積分の深さ        --s 2.5         不完全ガンマの s
 *   --crossings 14   Λ 場の交差数          --ops 1e18      演算速度 [ops/s]
 *   --temp 300       制御系温度 [K]        --led-nm 450    LED 波長 [nm]
 *   --bias 0.1       順方向バイアス [V]    --eqe 0.7       外部量子効率
 *   --current 1e-3   素子電流 [A]          --count 1e12    素子数
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const LD = require("../www/lambda_driver.js");

const NUM = ["p0","doubling","emax","horizon","x","s","crossings","ops","temp",
             "led-nm","bias","eqe","current","count","steps","from","to","points"];

function parseArgs(argv) {
  const o = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    let a = argv[i];
    if (a.startsWith("--")) {
      let k = a.slice(2), v;
      const eq = k.indexOf("=");
      if (eq >= 0) { v = k.slice(eq + 1); k = k.slice(0, eq); }
      else if (i + 1 < argv.length && !/^--/.test(argv[i + 1])) v = argv[++i];
      else v = "true";
      o[k] = NUM.includes(k) ? Number(v) : v;
    } else o._.push(a);
  }
  return o;
}
function toParams(a) {
  const m = { p0: "p0W", doubling: "doublingNs", emax: "emaxJ", horizon: "horizonNs",
              x: "depthX", s: "gammaS", crossings: "crossings", ops: "opsRate",
              temp: "tempK", "led-nm": "ledLambdaNm", bias: "ledBiasV",
              eqe: "ledEQE", current: "ledCurrentA", count: "ledCount", steps: "steps" };
  const p = {};
  for (const k in m) if (isFinite(a[k])) p[m[k]] = a[k];
  return p;
}
const sci = (v, d) => (isFinite(v) ? Number(v).toExponential(d === undefined ? 3 : d)
                                   : (v > 0 ? "inf" : "-inf"));
function pad(s, n, right) {
  s = String(s);
  let w = 0; for (const ch of s) w += /[　-鿿＀-￯]/.test(ch) ? 2 : 1;
  const sp = " ".repeat(Math.max(0, n - w));
  return right ? sp + s : s + sp;
}
function usage() {
  console.error(fs.readFileSync(__filename, "utf8").split("\n").slice(2, 26)
    .map(s => s.replace(/^ \*\s?/, "")).join("\n"));
}

function cmdRun(a) {
  const r = LD.simulate(toParams(a));
  console.log("================================================================");
  console.log("LÆVATEIN " + LD.VERSION + " — Λ ドライバ無力化シミュレータ");
  console.log("================================================================");
  console.log(LD.summary(r));
  console.log("================================================================");
  return r;
}

function cmdGamma(a) {
  const p = toParams(a);
  const g = LD.gammaManifold(p.gammaS || LD.DEFAULTS.gammaS, p.depthX || LD.DEFAULTS.depthX);
  console.log("# Γ 大域的部分積分多様体  s = " + g.s + ", x = " + g.x);
  console.log("# 最適打ち切り k* = " + g.optimalTruncation + " (理論位置 s+x = " + g.predictedTruncation
    + "),  最小項 = " + sci(g.minTerm, 4) + ",  漏れ比 ρ = " + sci(g.leakFraction, 4));
  console.log([pad("k", 5), pad("a_k", 16, 1), pad("|a_k|", 14, 1), pad("印", 6, 1)].join(" "));
  for (const L of g.layers) {
    const mark = L.k === g.optimalTruncation ? "← k*" : "";
    console.log([pad(L.k, 5), pad(sci(L.term, 6), 16, 1), pad(sci(L.abs, 4), 14, 1), pad(mark, 6, 1)].join(" "));
  }
}

function cmdSweep(a) {
  const base = toParams(a);
  const from = isFinite(a.from) ? a.from : 5;
  const to = isFinite(a.to) ? a.to : 100;
  const pts = isFinite(a.points) ? a.points : 20;
  console.log("# 部分積分の深さ x を掃引 (他は既定)");
  console.log([pad("x", 6), pad("k*", 6, 1), pad("最小項", 13, 1), pad("漏れ比 ρ", 13, 1),
               pad("漏れ [J]", 13, 1), pad("排熱要求 [W]", 14, 1), pad("判定", 10, 1)].join(" "));
  for (let i = 0; i < pts; i++) {
    const x = Math.round(from + (to - from) * i / (pts - 1));
    const r = LD.simulate(Object.assign({}, base, { depthX: x, steps: 400 }));
    console.log([pad(x, 6), pad(r.gamma.optimalTruncation, 6, 1),
                 pad(sci(r.gamma.minTerm, 3), 13, 1), pad(sci(r.budget.leakFraction, 3), 13, 1),
                 pad(sci(r.budget.eLeakJ, 3), 13, 1), pad(sci(r.budget.loadW, 3), 14, 1),
                 pad(r.verdict.limiting || "closes", 10, 1)].join(" "));
  }
}

function cmdCooling(a) {
  const p = toParams(a);
  const lam = p.ledLambdaNm || LD.DEFAULTS.ledLambdaNm;
  const eta = p.ledEQE !== undefined ? p.ledEQE : LD.DEFAULTS.ledEQE;
  const hw = LD.photonEnergyEV(lam);
  console.log("# 青色 LED 電界発光冷却の成立範囲   λ = " + lam + " nm  (ħω = " + hw.toFixed(4) + " eV), η = " + eta);
  console.log("# 冷却条件: η > qV/ħω  →  V < η·ħω/q = " + (eta * hw).toFixed(4) + " V");
  console.log([pad("V [V]", 9), pad("qV/ħω", 10, 1), pad("吸熱/電子 [eV]", 16, 1),
               pad("COP", 10, 1), pad("冷却", 8, 1)].join(" "));
  for (const V of [0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 1.5, 2.0, 2.5, 2.7, 3.0]) {
    const el = LD.elCooling({ lambdaNm: lam, biasV: V, eqe: eta, currentA: 1 });
    console.log([pad(V.toFixed(2), 9), pad(el.etaThreshold.toFixed(5), 10, 1),
                 pad(el.perElectronEV.toFixed(5), 16, 1),
                 pad(isFinite(el.cop) ? el.cop.toFixed(3) : "-", 10, 1),
                 pad(el.cools ? "する" : "しない", 8, 1)].join(" "));
  }
  console.log("");
  console.log("実証済みの電界発光冷却は " + sci(LD.CONST.EL_COOLING_DEMONSTRATED_W, 1)
    + " W/素子 のオーダー (Santhanam et al. 2012, PRL 108, 097403)。");
  console.log("室温の青色 InGaN での正味電界発光冷却は未実証。低バイアス域では非発光再結合が EQE を潰す。");
}

function cmdSelfTest() {
  let bad = 0;
  const t = (name, got, want, tol) => {
    const ok = Math.abs(got - want) <= Math.abs(want) * tol;
    console.log((ok ? "ok   " : "FAIL ") + pad(name, 36) + pad(sci(got, 6), 16, 1)
      + (ok ? "" : "   want " + sci(want, 6)));
    if (!ok) bad++;
  };
  const as = (name, cond, detail) => {
    console.log((cond ? "ok   " : "FAIL ") + pad(name, 36) + (detail || ""));
    if (!cond) bad++;
  };
  t("450nm 光子 [eV]", LD.photonEnergyEV(450), 2.7552, 1e-4);
  t("Landauer @300K [J/bit]", LD.CONST.K_B * 300 * Math.LN2, 2.8710e-21, 1e-3);
  t("Landauer @77K [J/bit]", LD.CONST.K_B * 77 * Math.LN2, 7.369e-22, 1e-3);
  {
    const el = LD.elCooling({ lambdaNm: 450, biasV: 0.1, eqe: 0.7, currentA: 1 });
    t("冷却しきい EQE = qV/ħω", el.etaThreshold, 0.1 / 2.7552, 1e-4);
    t("吸熱/電子 [eV]", el.perElectronEV, 0.7 * 2.7552 - 0.1, 1e-4);
    as("η > qV/ħω で冷却する", el.cools === true);
    as("η < qV/ħω で冷却しない",
      LD.elCooling({ lambdaNm: 450, biasV: 2.6, eqe: 0.7, currentA: 1 }).cools === false);
  }
  t("Kauffman 1 交差 (A=1.3)", LD.kauffmanBracket(LD.braidDiagram(1), 1.3).value,
    -Math.pow(1.3, -3), 1e-9);
  t("Λ(e) = e^e", LD.dalanversian(Math.E), Math.exp(Math.E), 1e-12);
  for (const x of [20, 30, 50]) {
    const g = LD.gammaManifold(2.5, x);
    as("最適打ち切り k* ≈ s+x (x=" + x + ")", Math.abs(g.optimalTruncation - (2.5 + x)) <= 2,
      "k*=" + g.optimalTruncation);
  }
  as("x 増加で漏れ ρ 減少",
    LD.gammaManifold(2.5, 40).leakFraction < LD.gammaManifold(2.5, 20).leakFraction);
  {
    const r = LD.simulate({});
    as("既定で収支が閉じない", r.verdict.result === "fails");
    as("律速は冷却能力", r.verdict.limiting === "cooling-power", "(" + r.verdict.limiting + ")");
    as("現実との差 > 20 桁", r.led.realityGapOrders > 20, "10^" + r.led.realityGapOrders.toFixed(1));
    as("制御計算は間に合う", r.jones.computeCloses === true);
  }
  as("遅い制御系では compute が律速",
    LD.simulate({ crossings: 22, opsRate: 1e9 }).verdict.limiting === "control-compute");
  as("EQE 不足では el-cooling-condition が律速",
    LD.simulate({ ledEQE: 0.01 }).verdict.limiting === "el-cooling-condition");
  console.log(bad ? "\nselftest FAILED (" + bad + ")" : "\nselftest OK");
  process.exit(bad ? 1 : 0);
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (a.help) { usage(); return; }
  const cmd = a._[0] || "run";
  switch (cmd) {
    case "run": cmdRun(a); break;
    case "gamma": cmdGamma(a); break;
    case "sweep": cmdSweep(a); break;
    case "cooling": cmdCooling(a); break;
    case "selftest": cmdSelfTest(); break;
    case "version": console.log("LAEVATEIN " + LD.VERSION); break;
    case "csv": {
      const out = a._[1];
      if (!out) { console.error("出力先を指定してください: csv <out.csv>"); process.exit(2); }
      const r = LD.simulate(toParams(a));
      fs.writeFileSync(out, LD.toCSV(r));
      console.error("wrote " + out + "  (" + r.series.t.length + " 行)");
      break;
    }
    case "json": {
      const r = LD.simulate(toParams(a));
      const o = { version: r.version, params: r.params, runaway: r.runaway,
        gamma: { s: r.gamma.s, x: r.gamma.x, optimalTruncation: r.gamma.optimalTruncation,
                 predictedTruncation: r.gamma.predictedTruncation, minTerm: r.gamma.minTerm,
                 capacity: r.gamma.capacity, signedSum: r.gamma.signedSum,
                 leakFraction: r.gamma.leakFraction, gammaAsym: r.gamma.gammaAsym },
        lambda: r.lambda, jones: r.jones, budget: r.budget, led: r.led, verdict: r.verdict,
        series: {} };
      for (const k of Object.keys(r.series)) o.series[k] = Array.from(r.series[k]);
      const txt = JSON.stringify(o, null, 2);
      if (a._[1]) { fs.writeFileSync(a._[1], txt); console.error("wrote " + a._[1]); }
      else console.log(txt);
      break;
    }
    default: console.error("unknown command: " + cmd + "\n"); usage(); process.exit(2);
  }
}
main();
