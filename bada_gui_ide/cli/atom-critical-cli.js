#!/usr/bin/env node
/* ============================================================================
 * atom-critical-cli.js — ACPI コマンドライン版
 *   原子の臨界期の強度シミュレータ (Atomic Critical-Period Intensity)
 *
 *   node cli/atom-critical-cli.js run    [opts]        # 要約を表示
 *   node cli/atom-critical-cli.js csv    <out.csv>     # 時系列を CSV 出力
 *   node cli/atom-critical-cli.js json   <out.json>    # 全結果を JSON 出力
 *   node cli/atom-critical-cli.js sweep  [opts]        # I0 を対数掃引
 *   node cli/atom-critical-cli.js scan   [opts]        # 全元素を一括比較
 *   node cli/atom-critical-cli.js elements             # 元素表
 *   node cli/atom-critical-cli.js selftest             # 既知の物理値と照合
 *
 * オプション:
 *   -e --element  Ar      元素記号            -I --intensity 6e14  ピーク強度 [W/cm^2]
 *   -l --lambda   800     波長 [nm]           -f --fwhm      8     パルス幅 FWHM [fs]
 *      --shape    gaussian|sech2|flattop         --cep       0     CEP [rad]
 *      --stage    1       電離段数               --charge    1     残留電荷 Z_c
 *      --steps    8000    時間ステップ数         --zeta-order 3    ζ/Euler 次数 n
 *      --kauffman-a 1.0699  Kauffman ループ変数
 *      --from/--to/--points   sweep の範囲・点数
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const AC = require("../www/atom_critical.js");

/* ------------------------------ 引数解析 ------------------------------- */
const ALIAS = { e: "element", I: "intensity", l: "lambda", f: "fwhm", o: "out", h: "help" };
const NUM = ["intensity", "lambda", "fwhm", "cep", "stage", "charge", "steps",
             "zeta-order", "kauffman-a", "from", "to", "points"];

function parseArgs(argv) {
  const o = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    let a = argv[i];
    if (a === "--") { o._.push(...argv.slice(i + 1)); break; }
    if (a.startsWith("--")) {
      let k = a.slice(2), v;
      const eq = k.indexOf("=");
      if (eq >= 0) { v = k.slice(eq + 1); k = k.slice(0, eq); }
      else if (i + 1 < argv.length && !argv[i + 1].startsWith("-")) v = argv[++i];
      else v = "true";
      o[k] = NUM.includes(k) ? Number(v) : v;
    } else if (a.startsWith("-") && a.length > 1 && !/^-\d/.test(a)) {
      const k = ALIAS[a.slice(1)] || a.slice(1);
      let v = (i + 1 < argv.length && !argv[i + 1].startsWith("-")) ? argv[++i] : "true";
      o[k] = NUM.includes(k) ? Number(v) : v;
    } else o._.push(a);
  }
  return o;
}

function toParams(a) {
  const p = {};
  if (a.element) p.element = a.element;
  if (isFinite(a.intensity)) p.intensity = a.intensity;
  if (isFinite(a.lambda)) p.lambdaNm = a.lambda;
  if (isFinite(a.fwhm)) p.fwhmFs = a.fwhm;
  if (a.shape) p.shape = a.shape;
  if (isFinite(a.cep)) p.cep = a.cep;
  if (isFinite(a.stage)) p.stage = a.stage;
  if (isFinite(a.charge)) p.charge = a.charge;
  if (isFinite(a.steps)) p.steps = a.steps;
  if (isFinite(a["zeta-order"])) p.zetaOrder = a["zeta-order"];
  if (isFinite(a["kauffman-a"])) p.kauffmanA = a["kauffman-a"];
  return p;
}

function usage() {
  console.error(fs.readFileSync(__filename, "utf8")
    .split("\n").slice(2, 26).map(s => s.replace(/^ \*\s?/, "")).join("\n"));
}

function pad(s, n, right) {
  s = String(s);
  /* 全角を 2 幅で数える簡易版 */
  let w = 0;
  for (const ch of s) w += /[　-鿿＀-￯]/.test(ch) ? 2 : 1;
  const sp = " ".repeat(Math.max(0, n - w));
  return right ? sp + s : s + sp;
}
const sci = (v, d) => (isFinite(v) ? Number(v).toExponential(d === undefined ? 3 : d) : "–");

/* ------------------------------ 各コマンド ----------------------------- */
function cmdRun(a) {
  const res = AC.simulate(toParams(a));
  console.log("================================================================");
  console.log("ACPI " + AC.VERSION + " — 原子の臨界期の強度 (Atomic Critical-Period Intensity)");
  console.log("================================================================");
  console.log(AC.summary(res));
  console.log("================================================================");
  return res;
}

function cmdCsv(a) {
  const out = a._[1] || a.out;
  if (!out) { console.error("出力ファイル名を指定してください: csv <out.csv>"); process.exit(2); }
  const res = AC.simulate(toParams(a));
  fs.writeFileSync(out, AC.toCSV(res));
  console.error("wrote " + out + "  (" + res.series.t.length + " 行, 臨界期 "
    + res.critical.durationFs.toFixed(4) + " fs)");
}

function cmdJson(a) {
  const out = a._[1] || a.out;
  const res = AC.simulate(toParams(a));
  const o = {
    version: res.version, params: res.params, atom: res.atom, scales: res.scales,
    critical: res.critical, omega: res.omega, result: res.result, series: {}
  };
  for (const k of Object.keys(res.series)) o.series[k] = Array.from(res.series[k]);
  const txt = JSON.stringify(o, null, 2);
  if (out) { fs.writeFileSync(out, txt); console.error("wrote " + out); }
  else console.log(txt);
}

function cmdSweep(a) {
  const p = toParams(a);
  const el = AC.element(p.element || AC.DEFAULTS.element);
  const Icr = AC.criticalIntensity(el.Ip[(p.stage || 1) - 1], p.charge || 1);
  const from = isFinite(a.from) ? a.from : Icr / 30;
  const to = isFinite(a.to) ? a.to : Icr * 300;
  const pts = isFinite(a.points) ? a.points : 30;
  const sw = AC.sweep(Object.assign({ steps: 3000 }, p), { from, to, points: pts });
  console.log("# ACPI 強度スイープ — " + el.sym + " 第 " + (p.stage || 1) + " 電離, λ = "
    + (p.lambdaNm || AC.DEFAULTS.lambdaNm) + " nm, FWHM = " + (p.fwhmFs || AC.DEFAULTS.fwhmFs) + " fs");
  console.log("# I_cr = " + sci(Icr) + " W/cm^2 (障壁抑制強度)");
  console.log([pad("I0 [W/cm^2]", 13), pad("I0/I_cr", 10, 1), pad("gamma_K", 9, 1),
               pad("臨界期 [fs]", 13, 1), pad("窓", 4, 1), pad("ON [fs]", 10, 1),
               pad("電離", 10, 1), pad("E(sigma)", 12, 1)].join(" "));
  for (const q of sw.points) {
    console.log([pad(sci(q.intensity, 3), 13), pad(q.overcritical.toFixed(3), 10, 1),
                 pad(q.gammaK.toFixed(4), 9, 1), pad(q.durationFs.toFixed(4), 13, 1),
                 pad(q.windows, 4, 1), pad(q.totalOnFs.toFixed(4), 10, 1),
                 pad((q.ionization * 100).toFixed(4) + "%", 10, 1),
                 pad(sci(q.Esigma, 4), 12, 1)].join(" "));
  }
}

function cmdScan(a) {
  const p = toParams(a);
  const I0 = p.intensity || AC.DEFAULTS.intensity;
  const lam = p.lambdaNm || AC.DEFAULTS.lambdaNm;
  console.log("# ACPI 元素スキャン — I0 = " + sci(I0) + " W/cm^2, λ = " + lam
    + " nm, FWHM = " + (p.fwhmFs || AC.DEFAULTS.fwhmFs) + " fs, 第 1 電離");
  console.log([pad("元素", 6), pad("I_p [eV]", 10, 1), pad("I_cr [W/cm^2]", 14, 1),
               pad("I0/I_cr", 9, 1), pad("gamma_K", 9, 1), pad("臨界期 [fs]", 13, 1),
               pad("窓", 4, 1), pad("平均窓 [as]", 12, 1), pad("電離", 10, 1),
               pad("E(sigma)", 12, 1)].join(" "));
  for (const el of AC.ELEMENTS) {
    const r = AC.simulate(Object.assign({}, p, { element: el.sym, stage: 1, charge: 1 }));
    console.log([pad(el.sym, 6), pad(r.atom.IpEV.toFixed(4), 10, 1),
                 pad(sci(r.scales.Icr, 3), 14, 1), pad(r.scales.overcritical.toFixed(3), 9, 1),
                 pad(r.scales.gammaK.toFixed(4), 9, 1),
                 pad(r.critical.exists ? r.critical.durationFs.toFixed(4) : "—", 13, 1),
                 pad(r.critical.count, 4, 1),
                 pad(r.critical.count ? r.critical.meanWindowAs.toFixed(1) : "—", 12, 1),
                 pad((r.result.ionization * 100).toFixed(4) + "%", 10, 1),
                 pad(sci(r.omega.Esigma, 4), 12, 1)].join(" "));
  }
}

function cmdElements() {
  console.log(pad("元素", 6) + pad("名称", 14) + pad("Z", 4, 1) + pad("l", 3, 1)
    + "  逐次イオン化エネルギー I_p [eV] / 障壁抑制強度 I_cr [W/cm^2]");
  for (const el of AC.ELEMENTS) {
    const ips = el.Ip.map((ip, i) => ip.toFixed(3) + " (" + sci(AC.criticalIntensity(ip, i + 1), 2) + ")").join("  ");
    console.log(pad(el.sym, 6) + pad(el.name, 14) + pad(el.Z, 4, 1) + pad(el.l, 3, 1) + "  " + ips);
  }
}

function cmdSelfTest() {
  let bad = 0;
  const t = (name, got, want, tol) => {
    const ok = Math.abs(got - want) <= Math.abs(want) * tol;
    console.log((ok ? "ok   " : "FAIL ") + pad(name, 34) + pad(sci(got, 6), 16, 1)
      + (ok ? "" : "   want " + sci(want, 6)));
    if (!ok) bad++;
  };
  t("I_a [W/cm^2]", AC.CONST.I_AU, 3.5094e16, 1e-4);
  t("H  I_cr [W/cm^2]", AC.criticalIntensity(13.5984, 1), 1.37e14, 0.01);
  t("Ar I_cr [W/cm^2]", AC.criticalIntensity(15.7596, 1), 2.47e14, 0.01);
  t("Xe I_cr [W/cm^2]", AC.criticalIntensity(12.1298, 1), 8.66e13, 0.01);
  const ap = AC.adkParams(13.5984, 1, 0);
  t("H ADK w(F=0.05) [a.u.]", AC.adkRate(0.05, ap), (4 / 0.05) * Math.exp(-2 / 0.15), 0.02);
  t("H ADK w(F=0.08) [a.u.]", AC.adkRate(0.08, ap), (4 / 0.08) * Math.exp(-2 / 0.24), 0.02);
  t("U_p (800nm, 2e14) [eV]", AC.ponderomotive(2e14, 800), 11.95, 0.01);
  t("gamma_K (Ar, 800nm, 2e14)", AC.keldysh(15.7596, 2e14, 800), 0.812, 0.01);
  t("Kauffman 1 交差 (A=1.3)", AC.kauffmanBracket(AC.braidDiagram(1), 1.3), -Math.pow(1.3, -3), 1e-9);
  t("beta(2,3) = 1/12", AC.betaFn(2, 3), 1 / 12, 1e-9);
  t("Gamma(5) = 24", AC.gammaFn(5), 24, 1e-9);
  t("pi_20 (Leibniz)", AC.piApprox(20), Math.PI, 0.03);
  t("e_20", AC.eApprox(20), Math.E, 1e-12);
  const r = AC.simulate({ element: "Ar", intensity: 6e14, fwhmFs: 8, steps: 8000 });
  console.log((r.critical.exists ? "ok   " : "FAIL ") + "Ar 6e14 -> 臨界期 "
    + r.critical.durationFs.toFixed(4) + " fs / " + r.critical.count + " 窓 / 電離 "
    + (r.result.ionization * 100).toFixed(3) + " %");
  if (!r.critical.exists || r.result.ionization < 0.9) bad++;
  const s = AC.simulate({ element: "Ar", intensity: 1e13, fwhmFs: 8, steps: 4000 });
  console.log((!s.critical.exists ? "ok   " : "FAIL ") + "Ar 1e13 (亜臨界) -> 臨界期なし");
  if (s.critical.exists) bad++;
  console.log(bad ? "\nselftest FAILED (" + bad + ")" : "\nselftest OK");
  process.exit(bad ? 1 : 0);
}

/* -------------------------------- main --------------------------------- */
function main() {
  const a = parseArgs(process.argv.slice(2));
  if (a.help) { usage(); return; }
  const cmd = a._[0] || "run";
  switch (cmd) {
    case "run": cmdRun(a); break;
    case "csv": cmdCsv(a); break;
    case "json": cmdJson(a); break;
    case "sweep": cmdSweep(a); break;
    case "scan": cmdScan(a); break;
    case "elements": cmdElements(); break;
    case "selftest": cmdSelfTest(); break;
    case "version": console.log("ACPI " + AC.VERSION); break;
    default: console.error("unknown command: " + cmd + "\n"); usage(); process.exit(2);
  }
}
main();
