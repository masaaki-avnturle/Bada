/*
 * engine-test.js — Bada 冬景 (Winter Math Music Visualizer) のエンジン単体テスト
 *
 *   node winter_math_art/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. 数学核 — β–ζ 論文の方程式群 (定理1 / 系1 / 系2 / 定理3 / 定理4 / 定理5 / 定理6)
 *      論文の 30 桁検証表の数値と照合
 *   2. 多様体エントロピー不変量 Ξ
 *   3. 音楽解析 — 合成音の音符 / コード / 調 / テンポ
 *   4. 音楽 → 数学 の写像、録画形式の選択、整形
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

const sandbox = {
  console, Math, Float32Array, Float64Array, Int8Array, Blob: function () {},
  window: { __ENGINE_TEST__: true },
  document: { createElement: function () { return { getContext: function () { return {}; } }; } },
  navigator: {}, performance: { now: () => 0 },
  requestAnimationFrame: () => 0, setTimeout: () => 0
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "fuyukei-inline.js" });
const E = sandbox;

let pass = 0, fail = 0;
function ok(cond, msg) { if (cond) { pass++; } else { fail++; console.error("  ✗ " + msg); } }
function near(a, b, tol, msg) { ok(Math.abs(a - b) <= tol, msg + " (got " + a + ", want " + b + ")"); }

/* ── 1. 数学核 ── */
console.log("1. 数学核 (β–ζ 論文の方程式群)");
near(E.gammaR(5), 24, 1e-9, "Γ(5) = 24");
near(E.gammaR(0.5), Math.sqrt(Math.PI), 1e-9, "Γ(½) = √π");
near(E.betaR(2, 3), 1 / 12, 1e-12, "β(2,3) = 1/12");
near(E.betaR(5, 7), 4.329004329e-4, 1e-12, "β(5,7) = 4.329e-4 (論文 定理2)");
near(E.betaR(2, 2), 1 / 6, 1e-12, "β(2,2) = 1/6 (論文 定理2 の最大値)");
near(E.betaDiag(0.25), Math.PI / Math.sin(Math.PI / 4), 1e-12, "β(s,1−s) = π/sin(πs) 式(3)");
near(E.betaR(0.25, 0.75), E.betaDiag(0.25), 1e-9, "β(¼,¾) と相反公式の一致");

/* 論文 定理3 の表 */
near(E.zetaR(1.1), 10.5844484650, 1e-8, "ζ(1.1)");
near(E.zetaR(1.5), 2.6123753487, 1e-8, "ζ(1.5)");
near(E.zetaR(2), 1.6449340668, 1e-8, "ζ(2) = π²/6");
near(E.zetaR(3), 1.2020569032, 1e-8, "ζ(3)");
near(E.zetaR(5), 1.0369277551, 1e-8, "ζ(5)");

/* 定理1: 関数等式 (β 明示形) が負の側で ζ を再現する */
near(E.zetaR(-1), -1 / 12, 1e-9, "ζ(−1) = −1/12 (定理1 で解析接続)");
near(E.zetaR(-3), 1 / 120, 1e-9, "ζ(−3) = 1/120");
near(E.zetaR(0), -0.5, 1e-12, "ζ(0) = −½");
near(E.theorem1RHS(2.5), E.zetaR(2.5), 1e-8, "定理1: s=2.5 で左右一致");
near(E.theorem1RHS(-1.5), E.zetaR(-1.5), 1e-8, "定理1: s=−1.5 で左右一致");
/* 系1: 自明な零点 */
for (const n of [1, 2, 3, 4]) near(E.zetaR(-2 * n), 0, 1e-15, "系1: ζ(−" + 2 * n + ") = 0");
/* 系2: 臨界線上の零点 (Hardy Z の符号変化) */
ok(E.hardyZ(14.0) * E.hardyZ(14.3) < 0, "系2: Z(t) が t=14.1347 (第1零点) で符号変化");
ok(E.hardyZ(20.9) * E.hardyZ(21.2) < 0, "系2: Z(t) が t=21.0220 (第2零点) で符号変化");
ok(E.hardyZ(24.9) * E.hardyZ(25.2) < 0, "系2: Z(t) が t=25.0109 (第3零点) で符号変化");
near(Math.abs(E.hardyZ(18)), 2.3, 0.3, "|Z(18)| ≈ 2.3 (Riemann–Siegel)");

/* Lambert W */
near(E.lambertW(1), 0.5671432904097838, 1e-12, "W(1) = Ω");
near(E.lambertW(Math.E), 1, 1e-12, "W(e) = 1");
near(E.lambertW(-0.3), -0.4894022271802149, 1e-9, "W(−0.3)");
/* 定理3 の表: x(s) = e^{W(ζ(s))} */
for (const [s, x] of [[1.1, 5.9403940741], [1.5, 2.6650664246], [2, 2.1495344893], [3, 1.8893441080], [5, 1.7866873848]]) {
  const xs = E.entropyX(E.zetaR(s));
  near(xs, x, 1e-7, "定理3: x(" + s + ")");
  near(E.xLogX(xs), E.zetaR(s), 1e-9, "定理3: x log x = ζ(s) at s=" + s);
}
near(E.entropyX(1), 1.7632228343518967, 1e-10, "x(∞) → e^{W(1)} = 1.7632…");
/* 定理4: p(s), s* */
near(E.S_STAR, 1.39425321984488839, 1e-7, "s* = 1.394253… (ζ(s*) = π)");
near(E.pOfS(1.1), 0.0959235125, 1e-7, "定理4: p(1.1)");
near(E.pOfS(1.05), 0.04877957, 1e-6, "定理4: p(1.05)");
ok(isNaN(E.pOfS(2)), "定理4: s=2 > s* では解なし");
/* 定理6 / 7.4: 連鎖 ζ(s) = β(p,1−p) = x log x */
for (const [s, common] of [[1.05, 20.58084430], [1.10, 10.58444846]]) {
  const c = E.commonCoordinate(s);
  near(c.zeta, common, 1e-6, "連鎖: ζ(" + s + ")");
  near(c.beta, common, 1e-6, "連鎖: β(p(s),1−p(s)) at s=" + s);
  near(c.xlogx, common, 1e-6, "連鎖: x log x at s=" + s);
}
/* 定理5 の表: x(p,q) = e^{W(β(p,q))} (素数引数) */
for (const [p, q, x] of [[2, 2, 1.155201688400], [2, 3, 1.080199998311], [3, 5, 1.009479024850], [5, 7, 1.000432806786], [2, 7, 1.017701389588]]) {
  const xs = E.xOfPQ(p, q);
  near(xs, x, 1e-9, "定理5: x(" + p + "," + q + ")");
  near(E.betaR(p, q) / E.xLogX(xs), 1, 1e-9, "定理5: β/(x log x) = 1 at (" + p + "," + q + ")");
}

/* ── 2. Ξ ── */
console.log("2. 多様体エントロピー不変量 Ξ");
const inv = E.manifoldInvariant([1, 1, 1, 1]);
near(inv.H, 2, 1e-12, "一様 4 元: H = 2 bit");
ok(inv.M > 0 && inv.M < 1, "0 < M < 1");
near(inv.xi, E.betaR(3, inv.M + 1), 1e-12, "Ξ = β(H+1, M+1)");
near(E.xLogX(inv.x), inv.xi, 1e-10, "x_Ξ log x_Ξ = Ξ (定理5 の修正正規化)");
const inv0 = E.manifoldInvariant([0, 0, 0]);
near(inv0.xi, 1, 1e-12, "無音: Ξ = β(1,1) = 1");

/* ── 3. 音楽解析 ── */
console.log("3. 音楽解析 (合成音)");
const SR = 22050;
function tone(freqs, seconds) {
  const n = Math.floor(SR * seconds), out = new Float32Array(n);
  for (let i = 0; i < n; i++) { let v = 0; for (const f of freqs) v += Math.sin(2 * Math.PI * f * i / SR); out[i] = 0.3 * v / freqs.length; }
  return out;
}
near(E.midiToFreq(69), 440, 1e-9, "A4 = 440 Hz");
near(E.freqToMidi(261.6256), 60, 1e-3, "C4 = MIDI 60");
ok(E.midiName(60) === "C4" && E.midiName(70) === "A#4", "midiName");
/* FFT: 純音のピーク */
{
  const N = 1024, re = new Float64Array(N), im = new Float64Array(N);
  for (let i = 0; i < N; i++) re[i] = Math.sin(2 * Math.PI * 64 * i / N);
  E.fftInPlace(re, im);
  let best = 0; for (let k = 1; k < N / 2; k++) if (Math.hypot(re[k], im[k]) > Math.hypot(re[best], im[best])) best = k;
  ok(best === 64, "FFT: ビン 64 にピーク (got " + best + ")");
}
/* コード検出 */
{
  const c = new Float32Array(12); c[11] = 1; c[2] = 0.9; c[6] = 0.8;    /* B D F# = Bm */
  ok(E.detectChord(c).name === "Bm", "detectChord: Bm (got " + E.detectChord(c).name + ")");
  const g = new Float32Array(12); g[7] = 1; g[11] = 0.9; g[2] = 0.8;    /* G B D */
  ok(E.detectChord(g).name === "G", "detectChord: G (got " + E.detectChord(g).name + ")");
  ok(E.detectChord(new Float32Array(12)) === null, "detectChord: 無音 → null");
}
/* 調推定 */
{
  const prof = new Float32Array(12);
  [11, 1, 2, 4, 6, 7, 9].forEach((pc, i) => prof[pc] = [6, 2, 3.5, 2.5, 4, 3, 3][i]); /* ロ短調の音階 */
  prof[2] = 4.5; prof[6] = 4.5;
  const k = E.estimateKey(prof);
  ok(k.minor && k.tonic === 11, "estimateKey: ロ短調 (got " + k.nameJa + ")");
}
/* テンポ: 120 BPM のクリック列 */
{
  const hop = 1 / 30, n = 600, flux = new Float64Array(n);
  for (let i = 0; i < n; i++) if (i % 15 === 0) flux[i] = 1;             /* 0.5 秒ごと */
  const t = E.estimateTempo(Array.from(flux), hop);
  near(t.bpm, 120, 1.5, "estimateTempo: 120 BPM");
}
/* 音符 + 解析全体 */
{
  const a = tone([E.midiToFreq(62)], 1.0), b = tone([E.midiToFreq(69)], 1.0);
  const all = new Float32Array(a.length + b.length); all.set(a); all.set(b, a.length);
  const an = E.analyzeAll(all, SR, { fps: 30 });
  near(an.duration, 2.0, 0.01, "duration");
  const midis = an.notes.map(n => n.midi);
  ok(midis.includes(62), "音符: D4 検出 (" + midis.join(",") + ")");
  ok(midis.includes(69), "音符: A4 検出");
  ok(an.notes.length <= 4, "音符数が妥当 (" + an.notes.length + ")");
  ok(an.noteLo <= 62 && an.noteHi >= 69 && an.noteHi - an.noteLo >= 36, "音域 " + an.noteLo + "–" + an.noteHi);
  const F = an.frames[E.frameIndexAt(an, 0.5)];
  ok(F.energy > 0.3, "0.5s のエネルギー > 0.3");
  const bar = E.barAt(an, 0);
  ok(bar.bar === 1 && bar.total >= 1, "barAt");
  const ms = E.mathState(an, 0.5);
  ok(ms.s > 1 && isFinite(ms.zeta) && ms.x > 1, "mathState: s>1, ζ 有限, x>1");
  ok(ms.pq.length === 2 && E.PRIMES12.includes(ms.pq[0]), "mathState: 素数対");
  near(E.xLogX(ms.x), ms.zeta, 1e-8, "mathState: x(s) log x(s) = ζ(s)");
  near(E.xLogX(ms.xPQ), ms.betaPQ, 1e-10, "mathState: x(p,q) log x = β(p,q)");
}
/* 音楽 → s の写像 */
ok(E.musicS(1) > 1 && E.musicS(1) < E.S_STAR, "最大音量 → s < s* (オーロラ可解域)");
ok(E.musicS(0) > E.S_STAR, "無音 → s > s* (オーロラ消灯)");
ok(E.primePair(0)[0] === 2 && E.primePair(0)[1] === 19, "primePair(C) = (2, 19)");
/* デモ曲 */
{
  const d = E.synthDemo(SR, 4);
  let peak = 0; for (let i = 0; i < d.length; i++) peak = Math.max(peak, Math.abs(d[i]));
  near(peak, 0.8, 1e-6, "synthDemo: ピーク正規化 0.8");
  const an = E.analyzeAll(d, SR, { fps: 30 });
  ok(an.notes.length > 0, "synthDemo: 音符検出 " + an.notes.length);
  ok(an.frames.some(f => f.chord && f.chord.name === "Bm"), "synthDemo: Bm 検出");
}

/* ── 4. 補助 ── */
console.log("4. 補助 (録画形式 / 整形)");
ok(E.pickRecorderMime(() => true).ext === "mp4", "pickRecorderMime: MP4 優先");
ok(E.pickRecorderMime(mm => /webm/.test(mm)).ext === "webm", "pickRecorderMime: WebM フォールバック");
ok(E.pickRecorderMime(() => false).ext === "webm", "pickRecorderMime: 未対応 → webm");
ok(E.videoBitrate(1280, 720, 30) >= 1500000 && E.videoBitrate(1920, 1080, 60) <= 24000000, "videoBitrate 範囲");
ok(E.fmtTime(263) === "4:23" && E.fmtTime(-1) === "0:00", "fmtTime");
ok(E.sanitizeName('a/b:c?"d') === "a_b_c_d" && E.sanitizeName("") === "fuyukei", "sanitizeName");
ok(E.parseResolution("1080x1920").h === 1920 && E.parseResolution("x").w === 1280, "parseResolution");
{ const r = E.mulberry32(1); const a = r(), b = r(); ok(a !== b && a >= 0 && a < 1, "mulberry32"); }

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
