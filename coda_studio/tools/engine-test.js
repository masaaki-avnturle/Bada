/*
 * engine-test.js — Coda Studio v2 スペクトル・コード・エンジンの単体テスト (Node で実行)
 *
 *   node coda_studio/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. 音律 — noteToFreq
 *   2. コード — chordNotes のヴォイシング
 *   3. 多段階スペクトル・ヴォイシング — chordVoicing (段階 1〜4)
 *   4. シーケンサー — chordGridToEvents のタイミングとスウィング
 *   5. WAV エンコード — RIFF ヘッダとサイズ
 *   6. リバーブ インパルス — 決定性と減衰
 *   7. おまかせ生成 — 決定性・段階範囲・密度
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* ── DOM スタブ ── */
function stubEl(){
  return new Proxy({
    style: {}, dataset: {},
    classList: { add(){}, remove(){}, toggle(){}, contains(){ return false; } },
    value: "", textContent: "", innerHTML: "", className: "", width: 940, height: 120
  }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "closest") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus" ||
          p === "click" || p === "remove") return function(){};
      if (p === "getAttribute") return function(){ return "0"; };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const els = {};
const sandbox = {
  console, Math, Function, Date,
  Float32Array, Uint8Array, ArrayBuffer, DataView, Array, Object, JSON,
  setTimeout: function(fn){ fn(); }, setInterval: function(){ return 0; },
  clearInterval: function(){}, alert: function(){},
  URL: { createObjectURL(){ return "blob:x"; }, revokeObjectURL(){} },
  Blob: function(){},
  window: { addEventListener(){}, removeEventListener(){} },
  document: {
    getElementById(id){ if (!els[id]) els[id] = stubEl(); return els[id]; },
    createElement(){ return stubEl(); },
    querySelectorAll(){ return []; },
    body: stubEl(),
    addEventListener(){}, removeEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

/* ── テストハーネス ── */
let passed = 0, failed = 0;
function ok(cond, name){
  if (cond) { passed++; console.log("  ok  " + name); }
  else { failed++; console.error("  FAIL " + name); }
}
function near(a, b, eps){ return Math.abs(a - b) <= (eps || 1e-6); }

/* 1. 音律 */
console.log("1. 音律 noteToFreq");
ok(near(sandbox.noteToFreq(69), 440), "A4 (midi 69) = 440 Hz");
ok(near(sandbox.noteToFreq(60), 261.6255653, 1e-4), "C4 (midi 60) ≈ 261.63 Hz");
ok(near(sandbox.noteToFreq(81), 880), "A5 = 880 Hz (1 オクターブで 2 倍)");

/* 2. コード */
console.log("2. chordNotes — ヴォイシング");
ok(JSON.stringify(sandbox.chordNotes(60, "maj9")) === JSON.stringify([60,64,67,71,74]), "Cmaj9");
ok(JSON.stringify(sandbox.chordNotes(57, "m7")) === JSON.stringify([57,60,64,67]), "Am7");
ok(JSON.stringify(sandbox.chordNotes(62, "sus2")) === JSON.stringify([62,64,69]), "Dsus2");
ok(sandbox.chordNotes(60, "unknown").length === 4, "未知タイプは maj7 にフォールバック");

/* 3. 多段階スペクトル・ヴォイシング */
console.log("3. chordVoicing — 4 段階のスペクトル");
const v1 = sandbox.chordVoicing(60, "maj9", 1);
const v2 = sandbox.chordVoicing(60, "maj9", 2);
const v3 = sandbox.chordVoicing(60, "maj9", 3);
const v4 = sandbox.chordVoicing(60, "maj9", 4);
ok(JSON.stringify(v1.notes) === JSON.stringify([48, 67]), "段階1 = 深部: 低ルート + 5度");
ok(JSON.stringify(v2.notes) === JSON.stringify([48, 60, 64, 67]), "段階2 = 中域: + 基本 3 音");
ok(JSON.stringify(v3.notes) === JSON.stringify([48, 60, 64, 67, 71, 74]), "段階3 = 上音: テンション全開");
ok(JSON.stringify(v4.notes) === JSON.stringify([48, 60, 64, 67, 71, 74, 86]), "段階4 = 輝き: 最上音をオクターブ重ね");
ok(v1.vel < v2.vel && v2.vel < v3.vel && v3.vel < v4.vel, "段階が深いほど音量が上がる");
ok(JSON.stringify(sandbox.chordVoicing(60, "maj9", 0).notes) === JSON.stringify(v1.notes) &&
   JSON.stringify(sandbox.chordVoicing(60, "maj9", 9).notes) === JSON.stringify(v4.notes),
   "段階は 1〜4 にクランプされる");

/* 4. シーケンサー */
console.log("4. chordGridToEvents — タイミングとスウィング");
const ROWS = 8, STEPS = 16;
const grid = [];
for (let r = 0; r < ROWS; r++) grid.push(new Array(STEPS).fill(0));
grid[0][0] = 3; grid[2][1] = 1; grid[5][8] = 4;
const chords = [
  { root:57, type:"maj9" }, { root:62, type:"maj7" }, { root:66, type:"m9" },
  { root:64, type:"sus2" }, { root:61, type:"m7" },  { root:59, type:"m11" },
  { root:57, type:"six9" }, { root:55, type:"maj7" }
];
const res = sandbox.chordGridToEvents(grid, chords, 120, 0);
ok(res.events.length === 3, "置いた 3 コードがイベントになる");
ok(near(res.stepDur, 0.125), "BPM120 の 16 分音符 = 0.125 s");
ok(near(res.loopLen, 2.0), "1 ループ = 2.0 s");
ok(near(res.events[0].time, 0) && res.events[0].level === 3, "step0: 時刻 0・段階 3");
ok(res.events[0].midis.length === 6, "段階 3 は 6 音 (低ルート + maj9 全音)");
ok(res.events[1].midis.length === 2 && res.events[1].midis[0] === 66 - 12, "段階 1 は 2 音・低ルートから");
ok(near(res.events[2].time, 1.0) && res.events[2].midis.length === 8, "step8: 1.0 s・段階 4 の m11 は 8 音");
const sw = sandbox.chordGridToEvents(grid, chords, 120, 0.5);
ok(near(sw.events[1].time, 0.125 + 0.5 * 0.125), "奇数ステップにスウィングが乗る");
ok(near(sw.events[0].time, 0) && near(sw.events[2].time, 1.0), "偶数ステップは動かない");

/* 5. WAV エンコード */
console.log("5. encodeWav — RIFF/WAVE ヘッダ");
const n = 1000, L = new Float32Array(n), R = new Float32Array(n);
for (let i = 0; i < n; i++){ L[i] = Math.sin(i / 10) * 0.5; R[i] = -L[i]; }
const wav = sandbox.encodeWav(L, R, 44100);
const s4 = (o) => String.fromCharCode(wav[o], wav[o+1], wav[o+2], wav[o+3]);
ok(wav.length === 44 + n * 4, "サイズ = 44 + n*4 バイト");
ok(s4(0) === "RIFF" && s4(8) === "WAVE" && s4(36) === "data", "RIFF / WAVE / data マーカー");
const dv = new DataView(wav.buffer);
ok(dv.getUint32(24, true) === 44100, "サンプルレート 44100");
ok(dv.getUint16(22, true) === 2 && dv.getUint16(34, true) === 16, "ステレオ 16bit");
ok(dv.getUint32(40, true) === n * 4, "data チャンク長");
const clip = sandbox.encodeWav(new Float32Array([2, -2]), new Float32Array([0, 0]), 44100);
const cdv = new DataView(clip.buffer);
ok(cdv.getInt16(44, true) === 32767 && cdv.getInt16(48, true) === -32768, "±1 でクリップ");

/* 6. インパルス */
console.log("6. impulseData — 決定性と減衰");
const ir1 = sandbox.impulseData(0.5, 2.0, 8000, 7);
const ir2 = sandbox.impulseData(0.5, 2.0, 8000, 7);
const ir3 = sandbox.impulseData(0.5, 2.0, 8000, 11);
ok(ir1.length === 4000, "長さ = 秒 × サンプルレート");
ok(ir1.every((v, i) => v === ir2[i]), "同じ種なら同一 (決定的)");
ok(ir3.some((v, i) => v !== ir1[i]), "異なる種なら異なる");
const head = ir1.slice(0, 400).reduce((a, v) => a + Math.abs(v), 0) / 400;
const tail = ir1.slice(3600).reduce((a, v) => a + Math.abs(v), 0) / 400;
ok(tail < head * 0.2, "末尾が減衰している");

/* 7. おまかせ生成 */
console.log("7. demoPattern — 決定性・段階範囲・密度");
const p1 = sandbox.demoPattern(8, 16, 12345);
const p2 = sandbox.demoPattern(8, 16, 12345);
ok(JSON.stringify(p1) === JSON.stringify(p2), "同じ種なら同一パターン");
ok(p1.length === 8 && p1.every(r => r.length === 16), "8 行 × 16 ステップ");
ok(p1.flat().every(v => v >= 0 && v <= 4), "全セルが段階 0〜4 の範囲");
ok(p1[0][0] >= 1, "トニックで始まる");
const count = p1.flat().filter(v => v > 0).length;
ok(count >= 3 && count <= 24, "密度が疎 (アンビエント向き): " + count + " コード");

/* 8. アプリ層の存在確認 */
console.log("8. アプリ層 — シンセ/バス/プレイヘッド/スペクトラム関数の存在");
["synthVoice", "buildBus", "renderEvents", "exportWav", "startSeq", "stopSeq",
 "drawSpectrum", "animate", "chordSymbol"].forEach(fn =>
  ok(typeof sandbox[fn] === "function", fn + " が定義されている"));

console.log("");
console.log(passed + " passed, " + failed + " failed");
process.exit(failed ? 1 : 0);
