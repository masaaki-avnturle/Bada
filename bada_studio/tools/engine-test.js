/*
 * engine-test.js — Bada Studio (音楽制作スタジオ) のエンジン単体テスト
 *
 *   node bada_studio/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブして
 * 純ロジック部分を検証します:
 *   1. 音律 — noteToFreq (A4=440Hz / オクターブで 2 倍 / 平均律)
 *   2. シーケンサー時間 — secondsPerStep (16 分音符長、BPM クランプ)
 *   3. 波形 — oscSample (サイン / ノコギリ / 矩形 / 三角、位相の折り返し)
 *   4. ノイズ — makeNoiseArray (LCG の決定論性と値域)
 *   5. エンベロープ / キックスイープ — decayEnv, kickFreq
 *   6. パターン — patternIndex, defaultPattern (4 つ打ち + バックビート + 8 分ハット)
 *   7. PC キー配列 — keyToNote
 *   8. WAV エンコーダ — encodeWav (RIFF ヘッダ / PCM16 値 / クランプ)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

function stubEl() {
  return new Proxy({ style: { setProperty() {} }, classList: { add() {}, remove() {}, toggle() {} },
                     value: "", textContent: "", innerHTML: "", checked: false,
                     children: [], width: 1280, height: 720 }, {
    get(t, p) {
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function () { return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement" ||
          p === "getContext" || p === "removeChild" || p === "replaceChildren" ||
          p === "setAttribute" || p === "getAttribute" || p === "setPointerCapture") {
        return function () { return stubEl(); };
      }
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus" ||
          p === "getBoundingClientRect") {
        return function () { return { left: 0, top: 0, width: 1280, height: 720 }; };
      }
      return function () { return stubEl(); };
    },
    set(t, p, v) { t[p] = v; return true; }
  });
}

const sandbox = {
  console, Math, Proxy, String, Number, Object, Array, JSON, Date,
  parseFloat, parseInt, isNaN, isFinite,
  setTimeout: function () { return 0; }, clearTimeout: function () {},
  setInterval: function () { return 0; }, clearInterval: function () {},
  requestAnimationFrame: function () {},
  alert: function () {},
  document: {
    getElementById() { return stubEl(); }, createElement() { return stubEl(); },
    querySelectorAll() { return []; }, addEventListener() {}, removeEventListener() {},
    body: stubEl(), documentElement: stubEl()
  },
  navigator: {},
  window: { addEventListener() {}, removeEventListener() {} }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

const G = function (name) { return vm.runInContext(name, sandbox); };
function assert(cond, msg) { if (!cond) { console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }
function near(a, b, eps) { return Math.abs(a - b) <= (eps || 1e-9); }

/* 1. 音律 */
const noteToFreq = G("noteToFreq");
assert(near(noteToFreq(69), 440, 1e-12), "noteToFreq: A4 (69) = 440 Hz");
assert(near(noteToFreq(81), 880, 1e-9), "noteToFreq: 1 オクターブ上 (81) で 2 倍 = 880 Hz");
assert(near(noteToFreq(57), 220, 1e-9), "noteToFreq: 1 オクターブ下 (57) で 1/2 = 220 Hz");
assert(near(noteToFreq(60), 261.6255653, 1e-6), "noteToFreq: C4 (60) ≈ 261.63 Hz (平均律)");
assert(near(noteToFreq(70) / noteToFreq(69), Math.pow(2, 1 / 12), 1e-12),
       "noteToFreq: 半音比は 2^(1/12)");

/* 2. シーケンサー時間 */
const secondsPerStep = G("secondsPerStep");
assert(near(secondsPerStep(120), 0.125, 1e-12), "secondsPerStep: BPM120 の 16 分音符 = 0.125 s");
assert(near(secondsPerStep(60), 0.25, 1e-12), "secondsPerStep: BPM60 = 0.25 s");
assert(near(secondsPerStep(0), secondsPerStep(120), 1e-12), "secondsPerStep: 不正値は 120 BPM にフォールバック");
assert(near(secondsPerStep(10), secondsPerStep(30), 1e-12), "secondsPerStep: 下限 30 BPM にクランプ");
assert(near(secondsPerStep(9999), secondsPerStep(300), 1e-12), "secondsPerStep: 上限 300 BPM にクランプ");

/* 3. 波形 */
const oscSample = G("oscSample");
assert(near(oscSample("sine", 0.25), 1, 1e-12), "oscSample: sine は位相 1/4 で +1");
assert(near(oscSample("sine", 0), 0, 1e-12), "oscSample: sine は位相 0 で 0");
assert(near(oscSample("sawtooth", 0), -1, 1e-12) && near(oscSample("sawtooth", 0.5), 0, 1e-12),
       "oscSample: sawtooth は -1 → 0 → +1 の直線");
assert(oscSample("square", 0.25) === 1 && oscSample("square", 0.75) === -1,
       "oscSample: square は前半 +1 / 後半 -1");
assert(near(oscSample("triangle", 0.5), 1, 1e-12) && near(oscSample("triangle", 0), -1, 1e-12),
       "oscSample: triangle は 0→-1, 1/2→+1");
assert(near(oscSample("sine", 1.25), oscSample("sine", 0.25), 1e-12),
       "oscSample: 位相は周期 1 で折り返す");
assert(oscSample("unknown", 0.3) === 0, "oscSample: 未知の波形は 0 (無音)");

/* 4. ノイズ (LCG) */
const makeNoiseArray = G("makeNoiseArray");
const n1 = makeNoiseArray(512, 0xBADA5EED);
const n2 = makeNoiseArray(512, 0xBADA5EED);
const n3 = makeNoiseArray(512, 1);
assert(n1.length === 512, "makeNoiseArray: 要求長の配列を返す");
let same = true, inRange = true, differs = false;
for (let i = 0; i < 512; i++) {
  if (n1[i] !== n2[i]) same = false;
  if (!(n1[i] >= -1 && n1[i] < 1)) inRange = false;
  if (n1[i] !== n3[i]) differs = true;
}
assert(same, "makeNoiseArray: 同一シードで決定論的に一致");
assert(inRange, "makeNoiseArray: 値域は [-1, 1)");
assert(differs, "makeNoiseArray: シードが違えば系列も違う");

/* 5. エンベロープ / キックスイープ */
const decayEnv = G("decayEnv");
assert(near(decayEnv(0, 0.3), 1, 1e-12), "decayEnv: t=0 で 1");
assert(near(decayEnv(0.3, 0.3), Math.exp(-1), 1e-12), "decayEnv: t=τ で 1/e");
assert(decayEnv(0.1, 0.3) > decayEnv(0.2, 0.3), "decayEnv: 単調減衰");
const kickFreq = G("kickFreq");
assert(near(kickFreq(0), 160, 1e-9), "kickFreq: t=0 で 160 Hz");
assert(kickFreq(0.05) < 160 && kickFreq(0.05) > 45, "kickFreq: スイープ中は 45〜160 Hz");
assert(near(kickFreq(10), 45, 1e-6), "kickFreq: 十分時間が経つと 45 Hz へ収束");

/* 6. パターン */
const patternIndex = G("patternIndex");
const defaultPattern = G("defaultPattern");
const STEPS = G("STEPS");
const TRACKS = G("TRACKS");
assert(STEPS === 16 && TRACKS === 3, "STEPS=16, TRACKS=3");
assert(patternIndex(0, 0) === 0 && patternIndex(1, 0) === 16 && patternIndex(2, 15) === 47,
       "patternIndex: トラック行 x 16 の 1 次元配置");
const pat = defaultPattern();
assert(pat.length === 48, "defaultPattern: 長さ 48 (3x16)");
let kicks = 0, snares = 0, hats = 0;
for (let s = 0; s < 16; s++) {
  if (pat[patternIndex(0, s)]) kicks++;
  if (pat[patternIndex(1, s)]) snares++;
  if (pat[patternIndex(2, s)]) hats++;
}
assert(kicks === 4 && pat[patternIndex(0, 0)] && pat[patternIndex(0, 4)] &&
       pat[patternIndex(0, 8)] && pat[patternIndex(0, 12)],
       "defaultPattern: キックは 4 つ打ち (0,4,8,12)");
assert(snares === 2 && pat[patternIndex(1, 4)] && pat[patternIndex(1, 12)],
       "defaultPattern: スネアはバックビート (4,12)");
assert(hats === 8 && pat[patternIndex(2, 0)] && !pat[patternIndex(2, 1)],
       "defaultPattern: ハイハットは 8 分 (偶数ステップ)");

/* 7. PC キー配列 */
const keyToNote = G("keyToNote");
assert(keyToNote("a", 4) === 60, "keyToNote: A キー = C4 (60)");
assert(keyToNote("w", 4) === 61, "keyToNote: W キー = C#4 (61)");
assert(keyToNote("k", 4) === 72, "keyToNote: K キー = 1 オクターブ上のド (72)");
assert(keyToNote("a", 5) === 72, "keyToNote: オクターブ +1 で 12 半音上がる");
assert(keyToNote("z", 4) === null, "keyToNote: 未割り当てキーは null");

/* 8. WAV エンコーダ */
const encodeWav = G("encodeWav");
const L = new Float32Array([0, 0.5, -0.5, 2.0]);   // 2.0 はクランプ対象
const R = new Float32Array([1, -1, 0.25, -3.0]);   // -3.0 はクランプ対象
const wav = encodeWav([L, R], 44100);
const dv = new DataView(wav);
function str4(off) {
  return String.fromCharCode(dv.getUint8(off), dv.getUint8(off + 1), dv.getUint8(off + 2), dv.getUint8(off + 3));
}
assert(wav.byteLength === 44 + 4 * 2 * 2, "encodeWav: 44 バイトヘッダ + 4 フレーム x 2ch x 16bit");
assert(str4(0) === "RIFF" && str4(8) === "WAVE" && str4(12) === "fmt " && str4(36) === "data",
       "encodeWav: RIFF/WAVE/fmt/data チャンク");
assert(dv.getUint32(4, true) === 36 + 16 && dv.getUint32(40, true) === 16,
       "encodeWav: チャンクサイズが正しい");
assert(dv.getUint16(20, true) === 1 && dv.getUint16(22, true) === 2 &&
       dv.getUint32(24, true) === 44100 && dv.getUint16(34, true) === 16,
       "encodeWav: PCM / 2ch / 44100Hz / 16bit");
assert(dv.getUint32(28, true) === 44100 * 4 && dv.getUint16(32, true) === 4,
       "encodeWav: byteRate と blockAlign");
assert(dv.getInt16(44, true) === 0 && dv.getInt16(46, true) === 32767,
       "encodeWav: フレーム 0 は L=0, R=+1 (32767)");
assert(dv.getInt16(48, true) === Math.floor(0.5 * 32767) && dv.getInt16(50, true) === -32768,
       "encodeWav: フレーム 1 は L=+0.5, R=-1 (-32768)");
assert(dv.getInt16(56, true) === 32767 && dv.getInt16(58, true) === -32768,
       "encodeWav: 範囲外の入力は ±1 にクランプ");

/* clamp01 */
const clamp01 = G("clamp01");
assert(clamp01(-0.5) === 0 && clamp01(0.5) === 0.5 && clamp01(1.5) === 1,
       "clamp01: [0,1] にクランプ");

console.log("");
console.log("Bada Studio engine tests: ALL PASSED");
