/*
 * dsp.js の単体テスト。 node voice_restore/test/dsp.test.mjs で実行。
 * Web Audio に依存しない純粋関数のみを検証する。
 */
import {
  fft, pitchShift, formantShift, restoreVoice,
  estimateMedianF0, semitonesBetween, encodeWav, resampleLinear,
} from "../www/dsp.js";

let passed = 0, failed = 0;
function ok(name, cond, extra = "") {
  if (cond) { passed++; console.log(`  ✓ ${name}`); }
  else { failed++; console.log(`  ✗ ${name}  ${extra}`); }
}

const SR = 16000;

function sine(freq, dur, sr = SR, amp = 0.6) {
  const n = Math.round(dur * sr);
  const x = new Float32Array(n);
  for (let i = 0; i < n; i++) x[i] = amp * Math.sin((2 * Math.PI * freq * i) / sr);
  return x;
}

/**
 * 基本周波数を測る(テスト検証用)。最もエネルギーの大きい 4096 サンプル窓で
 * 自己相関を取り、最初の明確なピーク(直前の谷を超えて立ち上がる極大)を採る。
 */
function measureFreq(x, sr = SR, fmin = 50, fmax = 2000) {
  const W = Math.min(4096, x.length);
  // 最大エネルギー窓を探す
  let bestStart = 0, bestE = -1;
  for (let s = 0; s + W <= x.length; s += W / 2) {
    let e = 0; for (let i = 0; i < W; i++) e += x[s + i] * x[s + i];
    if (e > bestE) { bestE = e; bestStart = s; }
  }
  const seg = x.subarray(bestStart, bestStart + W);
  let e0 = 0; for (let i = 0; i < W; i++) e0 += seg[i] * seg[i];
  const minLag = Math.floor(sr / fmax), maxLag = Math.floor(sr / fmin);
  // 探索帯域内の正規化自己相関の最大ラグを基本周期とみなす
  let bestLag = -1, best = -1;
  for (let lag = minLag; lag <= maxLag; lag++) {
    let s = 0; for (let i = 0; i + lag < W; i++) s += seg[i] * seg[i + lag];
    const nrm = s / e0;
    if (nrm > best) { best = nrm; bestLag = lag; }
  }
  return bestLag > 0 ? sr / bestLag : 0;
}

/** 母音風(基本周波数 f0 + 3フォルマント)の合成信号 */
function vowel(f0, dur, formants = [700, 1200, 2600]) {
  const n = Math.round(dur * SR);
  const x = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0;
    for (let h = 1; h * f0 < SR / 2; h++) {
      const fh = h * f0;
      let g = 0.05;
      for (const F of formants) g += Math.exp(-Math.pow((fh - F) / 220, 2));
      s += g * Math.sin((2 * Math.PI * fh * i) / SR);
    }
    x[i] = 0.15 * s;
  }
  return x;
}

function rms(x) { let s = 0; for (let i = 0; i < x.length; i++) s += x[i] * x[i]; return Math.sqrt(s / x.length); }
function hasNaN(x) { for (let i = 0; i < x.length; i++) if (!Number.isFinite(x[i])) return true; return false; }

console.log("FFT");
{
  // 既知の信号でFFT/IFFT往復が元に戻る
  const n = 16;
  const re = new Float64Array(n), im = new Float64Array(n);
  for (let i = 0; i < n; i++) re[i] = Math.sin((2 * Math.PI * 2 * i) / n);
  const re0 = Float64Array.from(re);
  fft(re, im, false);
  fft(re, im, true);
  let maxErr = 0;
  for (let i = 0; i < n; i++) maxErr = Math.max(maxErr, Math.abs(re[i] - re0[i]));
  ok("FFT→IFFT が元信号に戻る", maxErr < 1e-9, `maxErr=${maxErr}`);
}

console.log("resampleLinear");
{
  const x = sine(200, 0.2);
  const y = resampleLinear(x, 0.5);
  ok("factor=0.5 で長さ半分", Math.abs(y.length - x.length / 2) <= 1, `len=${y.length}`);
}

console.log("pitchShift");
{
  const x = sine(200, 0.6);
  const up = pitchShift(x, 12); // +1オクターブ → 約400Hz
  ok("出力にNaNが無い", !hasNaN(up));
  ok("長さが概ね維持される", Math.abs(up.length - x.length) < x.length * 0.05, `len=${up.length}/${x.length}`);
  const f = measureFreq(up);
  ok("+12半音で周波数が約2倍(≈400Hz)", Math.abs(f - 400) < 25, `measured=${f.toFixed(1)}Hz`);

  const down = pitchShift(x, -12); // -1オクターブ → 約100Hz
  const fd = measureFreq(down);
  ok("-12半音で周波数が約半分(≈100Hz)", Math.abs(fd - 100) < 15, `measured=${fd.toFixed(1)}Hz`);

  const same = pitchShift(x, 0);
  ok("0半音は入力をそのまま返す", same.length === x.length && !hasNaN(same));
}

console.log("formantShift");
{
  // 基本周波数150Hz + フォルマント倍音構造をもつ疑似母音
  const dur = 0.6, n = Math.round(dur * SR);
  const x = new Float32Array(n);
  const f0 = 150;
  const formants = [500, 1500, 2500];
  for (let i = 0; i < n; i++) {
    let s = 0;
    for (let h = 1; h * f0 < 4000; h++) {
      const fh = h * f0;
      let g = 0;
      for (const F of formants) g += Math.exp(-Math.pow((fh - F) / 250, 2));
      s += g * Math.sin((2 * Math.PI * fh * i) / SR);
    }
    x[i] = 0.2 * s;
  }
  const shifted = formantShift(x, 1.3);
  ok("出力にNaNが無い", !hasNaN(shifted));
  ok("長さが概ね維持される", Math.abs(shifted.length - x.length) < x.length * 0.05);
  // フォルマントを動かしても基本周波数(ピッチ)は保たれる
  const f0After = measureFreq(shifted, SR, 80, 400);
  ok("フォルマントシフトでピッチが保たれる(≈150Hz)", Math.abs(f0After - f0) < 12, `measured=${f0After.toFixed(1)}Hz`);
  const r = rms(shifted);
  ok("出力が無音でない", r > 0.01, `rms=${r.toFixed(4)}`);
}

console.log("estimateMedianF0 / semitonesBetween");
{
  const x = sine(120, 1.0);
  const f0 = estimateMedianF0(x, SR);
  ok("120Hz サイン波のF0推定が近い", Math.abs(f0 - 120) < 6, `f0=${f0.toFixed(1)}`);
  const st = semitonesBetween(240, 120);
  ok("240→120Hz は -12半音", Math.abs(st + 12) < 1e-6, `st=${st}`);
}

console.log("restoreVoice");
{
  // 母音風信号を 変調(+7半音, フォルマント1.25倍) → 復元(-7半音, 1/1.25)
  const orig = vowel(140, 0.8);
  const modulated = restoreVoice(orig, 7, 1.25);     // ここでは「変調」として使う
  const restored = restoreVoice(modulated, -7, 1 / 1.25);
  ok("復元出力にNaNが無い", !hasNaN(restored));
  const fOrig = measureFreq(orig, SR, 80, 400);
  const fMod = measureFreq(modulated, SR, 80, 600);
  const fRestored = measureFreq(restored, SR, 80, 400);
  ok("変調でピッチが上がる(+7半音≈1.5倍)", fMod > fOrig * 1.3, `orig=${fOrig.toFixed(1)} mod=${fMod.toFixed(1)}`);
  ok("復元後のピッチが元へ戻る", Math.abs(fOrig - fRestored) < 12, `orig=${fOrig.toFixed(1)} restored=${fRestored.toFixed(1)}`);
}

console.log("encodeWav");
{
  const ch = new Float32Array([0, 0.5, -0.5, 1, -1]);
  const buf = encodeWav([ch], SR);
  const dv = new DataView(buf);
  const riff = String.fromCharCode(dv.getUint8(0), dv.getUint8(1), dv.getUint8(2), dv.getUint8(3));
  ok("RIFFヘッダを持つ", riff === "RIFF");
  ok("サイズが 44 + 2*サンプル数", buf.byteLength === 44 + ch.length * 2, `bytes=${buf.byteLength}`);
  ok("サンプルレートが書かれている", dv.getUint32(24, true) === SR);
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
