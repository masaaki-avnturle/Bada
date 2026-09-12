/*
 * engine-test.js — Coda Studio 音楽エンジンの単体テスト (Node で実行)
 *
 *   node coda_studio/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. 音律 — noteToFreq / noteName
 *   2. スケール構築 — メジャー / マイナー / 都節 / 琉球
 *   3. コード — chordNotes のヴォイシング
 *   4. シーケンサー — seqToEvents のタイミングとスウィング
 *   5. WAV エンコード — RIFF ヘッダとサイズ
 *   6. リバーブ インパルス — 決定性と減衰
 *   7. おまかせ生成 — 決定性と密度
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
    value: "", textContent: "", innerHTML: "", className: ""
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
  Float32Array, ArrayBuffer, DataView, Uint8Array, Array, Object, JSON,
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
console.log("1. 音律 noteToFreq / noteName");
ok(near(sandbox.noteToFreq(69), 440), "A4 (midi 69) = 440 Hz");
ok(near(sandbox.noteToFreq(60), 261.6255653, 1e-4), "C4 (midi 60) ≈ 261.63 Hz");
ok(near(sandbox.noteToFreq(81), 880), "A5 = 880 Hz (1 オクターブで 2 倍)");
ok(sandbox.noteName(60) === "C4", "noteName(60) = C4");
ok(sandbox.noteName(69) === "A4", "noteName(69) = A4");

/* 2. スケール */
console.log("2. buildScale — スケール構築");
const maj = sandbox.buildScale(60, "major", 8);
ok(maj.length === 8, "要求した音数を返す");
ok(maj[0] === 60 && maj[7] === 72, "メジャー: ルートで始まり 8 音目がオクターブ上");
ok(JSON.stringify(maj.slice(0, 7)) === JSON.stringify([60,62,64,65,67,69,71]), "メジャーの音程列");
const miyako = sandbox.buildScale(57, "miyako", 6);
ok(JSON.stringify(miyako) === JSON.stringify([57,58,62,64,65,69]), "都節音階 (0,1,5,7,8) + オクターブ");
const ryu = sandbox.buildScale(60, "ryukyu", 5);
ok(JSON.stringify(ryu) === JSON.stringify([60,64,65,67,71]), "琉球音階 (0,4,5,7,11)");
const asc = sandbox.buildScale(45, "minor", 13);
ok(asc.every((v, i) => i === 0 || v > asc[i-1]), "13 音が単調増加");

/* 3. コード */
console.log("3. chordNotes — ヴォイシング");
ok(JSON.stringify(sandbox.chordNotes(60, "maj9")) === JSON.stringify([60,64,67,71,74]), "Cmaj9");
ok(JSON.stringify(sandbox.chordNotes(57, "m7")) === JSON.stringify([57,60,64,67]), "Am7");
ok(JSON.stringify(sandbox.chordNotes(62, "sus2")) === JSON.stringify([62,64,69]), "Dsus2");
ok(sandbox.chordNotes(60, "unknown").length === 4, "未知タイプは maj7 にフォールバック");

/* 4. シーケンサー */
console.log("4. seqToEvents — タイミングとスウィング");
const rows = 13, steps = 16;
const grid = [];
for (let r = 0; r < rows; r++) grid.push(new Array(steps).fill(0));
grid[0][0] = 1; grid[4][1] = 1; grid[2][8] = 1;
const scale = sandbox.buildScale(45, "minor", rows);
const res = sandbox.seqToEvents(grid, scale, 120, 0);
ok(res.events.length === 3, "置いた 3 音がイベントになる");
ok(near(res.stepDur, 0.125), "BPM120 の 16 分音符 = 0.125 s");
ok(near(res.loopLen, 2.0), "1 ループ = 2.0 s");
ok(near(res.events[0].time, 0) && res.events[0].midi === scale[0], "step0 はルート・時刻 0");
ok(near(res.events[2].time, 1.0), "step8 は 1.0 s");
const sw = sandbox.seqToEvents(grid, scale, 120, 0.5);
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
console.log("7. demoPattern — 決定性と密度");
const p1 = sandbox.demoPattern(13, 16, 12345);
const p2 = sandbox.demoPattern(13, 16, 12345);
ok(JSON.stringify(p1) === JSON.stringify(p2), "同じ種なら同一パターン");
ok(p1.length === 13 && p1.every(r => r.length === 16), "13 行 × 16 ステップ");
ok(p1[0][0] === 1, "ルートで始まる");
const count = p1.flat().reduce((a, v) => a + v, 0);
ok(count >= 4 && count <= 40, "密度が疎 (アンビエント向き): " + count + " 音");

/* 8. アプリ層の存在確認 */
console.log("8. アプリ層 — シンセ/バス/書き出し関数の存在");
["synthVoice", "buildBus", "renderEvents", "exportWav", "startSeq", "stopSeq"].forEach(fn =>
  ok(typeof sandbox[fn] === "function", fn + " が定義されている"));

console.log("");
console.log(passed + " passed, " + failed + " failed");
process.exit(failed ? 1 : 0);
