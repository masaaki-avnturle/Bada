/*
 * engine-test.js — Bada Contrapunctus (未完のフーガ × 祈るカミーユ 動画工房) のエンジン単体テスト
 *
 *   node bach_monet_film/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で純ロジック部分を検証します:
 *   1. fft — 正弦波のピーク位置と逆変換の復元
 *   2. 調性解析 — 合成クロマ / 合成和音の波形から Krumhansl–Schmuckler で調を当てる
 *   3. chooseTransposition — 短調 → D 短調、長調 → F 長調(−6..+5 半音)
 *   4. 位相ボコーダ + 再標本化 — 長さを保って正しい半音数だけ移調される
 *   5. makeCathedralIR — 減衰・長さ・正規化
 *   6. planScore — 主題提示の順序、未完の断ち切り(cutoff 以降に音が無い)
 *   7. energyEnvelope / encodeWav / decodeWav / decodeAiff — 往復
 *   8. コード進行 — parseChord / parseProgression / chordAt / autoProgression
 *   9. 役割 — generateRoleNotes(pad / arpeggio / bass / pulse / melody)が和声音のみを置く
 *  10. MIDI — encodeMidi → decodeMidi の往復(テンポ・音符数・音高)
 *  11. 整形・録画形式・ビットレート
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
  console, Math, TextDecoder, Float32Array, Float64Array, Int16Array, Uint8Array, Int8Array, ArrayBuffer, DataView, Array,
  window: { __ENGINE_TEST__: true },
  document: undefined, navigator: {}, location: { search: "" },
  requestAnimationFrame: function () { return 0; }, cancelAnimationFrame: function () {}, setTimeout: function () { return 0; },
  URL: { createObjectURL: function () { return "blob:stub"; }, revokeObjectURL: function () {} },
  btoa: function (s) { return Buffer.from(s, "binary").toString("base64"); }, atob: function (s) { return Buffer.from(s, "base64").toString("binary"); }
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "contrapunctus-inline.js" });
const E = sandbox;

let pass = 0, fail = 0;
function ok(cond, name) { if (cond) { pass++; console.log("  ✔ " + name); } else { fail++; console.error("  ✘ " + name); } }
function eq(a, b, name) { ok(a === b, name + "  [" + JSON.stringify(a) + " === " + JSON.stringify(b) + "]"); }
function near(a, b, tol, name) { ok(Math.abs(a - b) <= tol, name + "  [" + a + " ≈ " + b + " ±" + tol + "]"); }
function sine(freq, sr, secs, amp) { const n = Math.floor(sr * secs), x = new Float32Array(n); for (let i = 0; i < n; i++) x[i] = (amp || 0.5) * Math.sin(2 * Math.PI * freq * i / sr); return x; }
function peakFreq(x, sr) {                                  /* 4096 点 FFT のピーク周波数 */
  const N = 4096, re = new Float32Array(N), im = new Float32Array(N), w = E.hann(N), off = Math.floor(x.length / 2) - N / 2;
  for (let i = 0; i < N; i++) { re[i] = x[off + i] * w[i]; im[i] = 0; }
  E.fft(re, im, false);
  let best = 1, bv = 0; for (let k = 1; k < N / 2; k++) { const v = re[k] * re[k] + im[k] * im[k]; if (v > bv) { bv = v; best = k; } }
  /* 隣接ビンで放物線補間 */
  const a = Math.sqrt(re[best - 1] ** 2 + im[best - 1] ** 2), b = Math.sqrt(bv), c = Math.sqrt(re[best + 1] ** 2 + im[best + 1] ** 2);
  const d = 0.5 * (a - c) / (a - 2 * b + c);
  return (best + (isFinite(d) ? d : 0)) * sr / N;
}

/* ── 1. fft ── */
console.log("1. fft");
{
  const N = 1024, sr = 8000, re = new Float32Array(N), im = new Float32Array(N);
  for (let i = 0; i < N; i++) re[i] = Math.sin(2 * Math.PI * 500 * i / sr);
  const orig = Float32Array.from(re);
  E.fft(re, im, false);
  let best = 0, bv = 0; for (let k = 0; k < N / 2; k++) { const v = re[k] * re[k] + im[k] * im[k]; if (v > bv) { bv = v; best = k; } }
  eq(best, Math.round(500 * N / sr), "fft: 500 Hz のピークビン");
  E.fft(re, im, true);
  let err = 0; for (let i = 0; i < N; i++) err = Math.max(err, Math.abs(re[i] - orig[i]));
  ok(err < 1e-4, "fft: 逆変換で元に戻る (max err " + err.toExponential(2) + ")");
}

/* ── 2. 調性解析 ── */
console.log("2. 調性解析");
{
  const dm = new Array(12).fill(0.02); [2, 5, 9, 0, 7, 10, 4].forEach((pc, i) => { dm[pc] += [0.30, 0.18, 0.16, 0.09, 0.08, 0.06, 0.04][i]; });
  const k = E.keyFromChroma(dm);
  eq(k.tonic + ":" + k.mode, "2:minor", "keyFromChroma: D 短調のクロマ → D minor");
  const fmaj = new Array(12).fill(0.02); [5, 9, 0, 7, 2, 10, 4].forEach((pc, i) => { fmaj[pc] += [0.30, 0.16, 0.18, 0.09, 0.08, 0.06, 0.04][i]; });
  const k2 = E.keyFromChroma(fmaj);
  eq(k2.tonic + ":" + k2.mode, "5:major", "keyFromChroma: F 長調のクロマ → F major");
  /* 波形から: A 短調のアルペジオ(A C E + G B D) */
  const sr = 22050, notes = [57, 60, 64, 69, 62, 67, 71, 64, 57, 60, 64, 69], x = new Float32Array(sr * 6);
  notes.forEach((mn, i) => { const f = E.midiFreq(mn); for (let j = 0; j < sr * 0.5; j++) x[i * sr * 0.5 + j] += 0.4 * Math.sin(2 * Math.PI * f * j / sr) + 0.15 * Math.sin(2 * Math.PI * 2 * f * j / sr); });
  const k3 = E.detectKey(x, sr);
  eq(k3.tonic, 9, "detectKey: A 短調のアルペジオ波形 → 主音 A");
  eq(k3.mode, "minor", "detectKey: … 短調");
  eq(E.keyName(k3), "A minor", "keyName");
  eq(E.keyNameJa(k3), "イ短調", "keyNameJa");
}

/* ── 3. chooseTransposition ── */
console.log("3. chooseTransposition");
eq(E.chooseTransposition({ tonic: 5, mode: "minor" }), -3, "F minor → D minor = −3");
eq(E.chooseTransposition({ tonic: 2, mode: "minor" }), 0, "D minor → 0");
eq(E.chooseTransposition({ tonic: 5, mode: "major" }), 0, "F major → 0");
eq(E.chooseTransposition({ tonic: 0, mode: "major" }), 5, "C major → F major = +5");
eq(E.chooseTransposition({ tonic: 8, mode: "minor" }), -6, "G♯ minor → D minor = −6 (下へ)");
eq(E.chooseTransposition({ tonic: 11, mode: "major" }), -6, "B major → F major = −6");
eq(E.chooseTransposition({ tonic: 9, mode: "minor" }), 5, "A minor → D minor = +5");

/* ── 4. 位相ボコーダ + 再標本化 ── */
console.log("4. pitchShift / timeStretch / resample");
{
  const sr = 22050, x = sine(440, sr, 1.5);
  const y = E.pitchShift(x, sr, -3);
  eq(y.length, x.length, "pitchShift: 長さを保つ");
  near(peakFreq(y, sr), 440 * Math.pow(2, -3 / 12), 3, "pitchShift −3: 440 → 369.99 Hz");
  const z = E.pitchShift(x, sr, 5);
  near(peakFreq(z, sr), 440 * Math.pow(2, 5 / 12), 4, "pitchShift +5: 440 → 587.33 Hz");
  const s = E.timeStretch(x, 1.5, 2048);
  near(s.length / x.length, 1.5, 0.01, "timeStretch 1.5: 長さ 1.5 倍");
  near(peakFreq(s, sr), 440, 2, "timeStretch: 音高は変わらない");
  const r = E.resample(x, 2);
  eq(r.length, Math.round(x.length / 2), "resample 2: 長さ半分");
  near(peakFreq(r, sr), 880, 3, "resample 2: 音高 2 倍");
  eq(E.pitchShift(x, sr, 0).length, x.length, "pitchShift 0: コピー");
}

/* ── 5. makeCathedralIR ── */
console.log("5. makeCathedralIR");
{
  const sr = 8000, ir = E.makeCathedralIR(sr, 3, 7);
  eq(ir.length, 2, "IR: 2 ch");
  eq(ir[0].length, sr * 3, "IR: 3 s");
  let pk = 0; for (let i = 0; i < ir[0].length; i++) pk = Math.max(pk, Math.abs(ir[0][i]));
  near(pk, 1, 1e-6, "IR: ピーク 1 に正規化");
  const rms = (a, b) => { let s = 0; for (let i = a; i < b; i++) s += ir[0][i] * ir[0][i]; return Math.sqrt(s / (b - a)); };
  ok(rms(sr * 0.3, sr * 0.6) > rms(sr * 2.4, sr * 2.9) * 5, "IR: 時間と共に減衰する");
  ok(ir[0][10] === 0, "IR: プリディレイの間は無音");
  const ir2 = E.makeCathedralIR(sr, 3, 7);
  ok(ir[1][12345] === ir2[1][12345], "IR: 同じ種で決定的");
}

/* ── 6. planScore ── */
console.log("6. planScore");
{
  const p = E.planScore(74, { tempo: 72 });
  near(p.cutoff, 66.6, 0.01, "planScore: cutoff = 90 %");
  eq(p.entries[0].subj, 1, "最初の入りは第 1 主題");
  eq(p.entries[0].voice, "アルト", "最初の入りはアルト");
  eq(p.entries[1].voice, "ソプラノ", "2 番目はソプラノ(応答)");
  ok(p.entries.some(e => e.subj === 2) && p.entries.some(e => e.subj === 3), "第 2・第 3 主題 (B–A–C–H) の入りがある");
  ok(p.notes.every(n => n.t + n.dur <= p.cutoff + 1e-9), "未完: cutoff 以降に鳴る音が無い");
  ok(p.notes.some(n => n.t + n.dur > p.cutoff - 1e-6), "未完: 最後の音は cutoff で断ち切られている");
  const answer = p.notes.find(n => n.voice === "ソプラノ");
  const subject = p.notes.find(n => n.voice === "アルト");
  eq(answer.midi - subject.midi, 7, "応答は 5 度上");
  const q = E.planScore(74, { tempo: 72, unfinished: false });
  eq(q.cutoff, 74, "unfinished:false → 断ち切らない");
  ok(E.subjectBeats(E.SUBJECTS[0]) === 20, "第 1 主題は 20 拍");
  ok(E.SUBJECT_3.slice(0, 4).map(n => n[0]).join(",") === "8,7,10,9", "第 3 主題は B♭–A–C–H で始まる");
}

/* ── 7. energyEnvelope / WAV / AIFF ── */
console.log("7. energyEnvelope / encodeWav / decodeWav / decodeAiff");
{
  const sr = 8000, x = new Float32Array(sr * 2);
  for (let i = sr; i < sr * 2; i++) x[i] = 0.5 * Math.sin(i * 0.3);
  const env = E.energyEnvelope(x, sr, 10);
  eq(env.length, 20, "envelope: 2 s × 10 fps = 20");
  ok(env[3] < 0.01 && env[19] > 0.8, "envelope: 無音は 0、音がある所は 1 に近づく");
  const L = Float32Array.from([0, 0.5, -0.5, 1, -1]), R = Float32Array.from([0.25, 0, 0, 0, 0]);
  const wav = E.encodeWav([L, R], 8000);
  eq(wav.byteLength, 44 + 5 * 2 * 2, "encodeWav: サイズ");
  const dec = E.decodeWav(wav);
  eq(dec.sampleRate, 8000, "decodeWav: sampleRate");
  eq(dec.channels.length, 2, "decodeWav: 2 ch");
  near(dec.channels[0][1], 0.5, 1e-4, "decodeWav: L[1] = 0.5");
  near(dec.channels[1][0], 0.25, 1e-4, "decodeWav: R[0] = 0.25");
  near(dec.channels[0][4], -1, 1e-4, "decodeWav: L[4] = −1");
  ok(E.decodeWav(new ArrayBuffer(10)) === null, "decodeWav: 壊れたデータは null");
  /* AIFF を手で組み立てる(16-bit BE, 1 ch, 8000 Hz, 3 frames) */
  const frames = [0.5, -0.5, 1]; const ssnd = 8 + frames.length * 2, total = 4 + 8 + 18 + 8 + ssnd;
  const ab = new ArrayBuffer(8 + total), dv = new DataView(ab), u = new Uint8Array(ab);
  const tag = (o, s) => { for (let i = 0; i < 4; i++) u[o + i] = s.charCodeAt(i); };
  tag(0, "FORM"); dv.setUint32(4, total, false); tag(8, "AIFF");
  tag(12, "COMM"); dv.setUint32(16, 18, false); dv.setUint16(20, 1, false); dv.setUint32(22, frames.length, false); dv.setUint16(26, 16, false);
  dv.setUint16(28, 16383 + 12, false); dv.setUint32(30, 8000 << 19, false); dv.setUint32(34, 0, false);      /* 80-bit float 8000 */
  tag(38, "SSND"); dv.setUint32(42, ssnd, false); dv.setUint32(46, 0, false); dv.setUint32(50, 0, false);
  frames.forEach((v, i) => dv.setInt16(54 + i * 2, Math.round(v * 32767), false));
  const ai = E.decodeAiff(ab);
  ok(ai && ai.sampleRate === 8000, "decodeAiff: 80-bit 浮動小数のサンプルレート 8000");
  near(ai.channels[0][0], 0.5, 1e-3, "decodeAiff: [0] = 0.5");
  near(ai.channels[0][1], -0.5, 1e-3, "decodeAiff: [1] = −0.5");
  /* 24-bit BE */
  dv.setUint16(26, 24, false); dv.setUint32(42, 8 + 3 * 3, false);
  const ab24 = new ArrayBuffer(54 + 9); new Uint8Array(ab24).set(new Uint8Array(ab, 0, 54)); const d24 = new DataView(ab24), u24 = new Uint8Array(ab24);
  d24.setUint32(4, ab24.byteLength - 8, false);
  [0.5, -0.5, 1].forEach((v, i) => { const n = Math.round(v * 8388607); u24[54 + i * 3] = (n >> 16) & 255; u24[55 + i * 3] = (n >> 8) & 255; u24[56 + i * 3] = n & 255; });
  const ai24 = E.decodeAiff(ab24);
  near(ai24.channels[0][0], 0.5, 1e-5, "decodeAiff 24-bit: [0] = 0.5");
  near(ai24.channels[0][1], -0.5, 1e-5, "decodeAiff 24-bit: [1] = −0.5");
  /* 24-bit WAV */
  const w24 = new ArrayBuffer(44 + 6), wd = new DataView(w24), wu = new Uint8Array(w24);
  const ws = (o, str) => { for (let i = 0; i < str.length; i++) wu[o + i] = str.charCodeAt(i); };
  ws(0, "RIFF"); wd.setUint32(4, 36 + 6, true); ws(8, "WAVE"); ws(12, "fmt "); wd.setUint32(16, 16, true); wd.setUint16(20, 1, true); wd.setUint16(22, 1, true);
  wd.setUint32(24, 8000, true); wd.setUint32(28, 24000, true); wd.setUint16(32, 3, true); wd.setUint16(34, 24, true); ws(36, "data"); wd.setUint32(40, 6, true);
  [0.5, -0.5].forEach((v, i) => { const n = Math.round(v * 8388607); wu[44 + i * 3] = n & 255; wu[45 + i * 3] = (n >> 8) & 255; wu[46 + i * 3] = (n >> 16) & 255; });
  const dw24 = E.decodeWav(w24);
  near(dw24.channels[0][0], 0.5, 1e-5, "decodeWav 24-bit: [0] = 0.5");
  near(dw24.channels[0][1], -0.5, 1e-5, "decodeWav 24-bit: [1] = −0.5");
}

/* ── 8. コード進行 ── */
console.log("8. parseChord / parseProgression / chordAt / autoProgression");
{
  const c = E.parseChord("Dm"); eq(c.root + ":" + c.intervals.join(","), "2:0,3,7", "Dm");
  eq(E.parseChord("B♭maj7").intervals.join(","), "0,4,7,11", "B♭maj7");
  eq(E.parseChord("Bb").root, 10, "Bb の根音");
  eq(E.parseChord("F#dim").intervals.join(","), "0,3,6", "F#dim");
  eq(E.parseChord("A7").intervals.join(","), "0,4,7,10", "A7");
  eq(E.parseChord("Gsus4").intervals.join(","), "0,5,7", "Gsus4");
  eq(E.parseChord("C/E").bass, 4, "C/E のベース");
  ok(E.parseChord("xyz") === null && E.parseChord("") === null, "無効な記号は null");
  const bars = E.parseProgression("Dm | Gm A7 | | zz | Bb");
  eq(bars.length, 3, "parseProgression: 有効な小節だけ 3");
  eq(bars[1].length, 2, "小節内の 2 コード");
  eq(E.chordAt(bars, 0).name, "Dm", "chordAt 0 拍 = Dm");
  eq(E.chordAt(bars, 5).name, "Gm", "chordAt 5 拍 = Gm(2 小節目前半)");
  eq(E.chordAt(bars, 7).name, "A7", "chordAt 7 拍 = A7(2 小節目後半)");
  eq(E.chordAt(bars, 12).name, "Dm", "chordAt 12 拍 = 繰り返し");
  ok(E.chordAt([], 0) === null, "chordAt 進行なし = null");
  eq(E.autoProgression({ tonic: 2, mode: "minor" }), "Dm | Gm | A | Dm | Bb | Gm | A7 | Dm", "autoProgression D minor");
  eq(E.autoProgression({ tonic: 5, mode: "major" }), "F | Bb | C | F | Dm | Gm | C7 | F", "autoProgression F major");
  eq(E.voicing(E.parseChord("Dm"), 62).join(","), "62,65,69", "voicing Dm @62");
}

/* ── 9. 役割 ── */
console.log("9. generateRoleNotes");
{
  const bars = E.parseProgression("Dm | Gm | A | Dm"), ctx = { beats: 16, bars, seed: 1 };
  const chordTones = (b) => { const ch = E.chordAt(bars, b); return ch.intervals.map(i => (ch.root + i) % 12); };
  const inTones = (notes) => notes.every(n => chordTones(n.t).indexOf(((n.midi % 12) + 12) % 12) >= 0);
  const pad = E.generateRoleNotes({ name: "s", instrument: "strings", role: "pad", chords: "" }, ctx);
  eq(pad.length, 12, "pad: 4 小節 × 3 声 = 12 音");
  ok(pad.every(n => n.d === 4), "pad: 各音は 4 拍");
  ok(inTones(pad), "pad: 和声音のみ");
  const arp = E.generateRoleNotes({ name: "c", instrument: "cembalo", role: "arpeggio", chords: "" }, ctx);
  eq(arp.length, 32, "arpeggio: 16 拍 × 2 = 32 音");
  ok(inTones(arp), "arpeggio: 和声音のみ");
  const bass = E.generateRoleNotes({ name: "b", instrument: "contrabass", role: "bass", chords: "" }, ctx);
  eq(bass.length, 8, "bass: 小節ごとに 2 音");
  ok(bass.every(n => n.midi < 55), "bass: 低い音域");
  ok(inTones(bass), "bass: 和声音のみ");
  const pulse = E.generateRoleNotes({ name: "t", instrument: "timpani", role: "pulse", chords: "" }, ctx);
  ok(pulse.length >= 4 && pulse.every(n => n.t % 4 === 0 || n.t % 4 === 2), "pulse: 1 拍目(と 3 拍目)だけ");
  const mel = E.generateRoleNotes({ name: "f", instrument: "flute", role: "melody", chords: "" }, ctx);
  ok(mel.length > 6 && inTones(mel), "melody: 和声音の歩み");
  const mel2 = E.generateRoleNotes({ name: "f", instrument: "flute", role: "melody", chords: "" }, ctx);
  eq(JSON.stringify(mel), JSON.stringify(mel2), "melody: 同じ種で決定的");
  const own = E.generateRoleNotes({ name: "s", instrument: "strings", role: "pad", chords: "C" }, ctx);
  ok(own.every(n => [0, 4, 7].indexOf(n.midi % 12) >= 0), "トラック固有のコード進行(平行)が優先される");
  eq(E.generateRoleNotes({ name: "x", instrument: "strings", role: "manual", chords: "" }, ctx).length, 0, "manual: 生成しない");
  eq(E.defaultTracks().length, 11, "既定は 11 行の平行トラック");
  ok(E.defaultTracks().filter(t => t.kind === "fugue").length === 4, "うちバッハの声部 4 行");
}

/* ── 10. MIDI ── */
console.log("10. encodeMidi / decodeMidi");
{
  const tracks = [
    { kind: "audio", name: "a", notes: [] },
    { kind: "synth", name: "Strings", instrument: "strings", notes: [{ t: 0, d: 2, midi: 62, vel: 90 }, { t: 2, d: 1, midi: 65, vel: 70 }] },
    { kind: "synth", name: "Timp", instrument: "timpani", notes: [{ t: 0, d: 1, midi: 38, vel: 100 }] }
  ];
  const bytes = E.encodeMidi(tracks, 72);
  eq(String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3]), "MThd", "MIDI ヘッダ");
  const dec = E.decodeMidi(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
  eq(dec.tempo, 72, "テンポ 72 が往復する");
  eq(dec.notes.length, 3, "音符 3 つ");
  eq(dec.notes[0].midi, 62, "最初の音は D4");
  eq(dec.notes.find(n => n.midi === 65).t, 2, "F4 は 2 拍目から");
  near(dec.notes[0].d, 2, 1e-6, "長さ 2 拍");
  eq(dec.duration, 3, "全体 3 拍");
  ok(E.decodeMidi(new ArrayBuffer(4)) === null, "壊れたデータは null");
  const ch = E.chromaOfNotes(dec.notes);
  near(ch[2], 3 / 4, 1e-9, "chromaOfNotes: D の重み(2 拍 + 1 拍)/4");
}

/* ── 11. 整形・録画形式・ビットレート ── */
console.log("11. fmtTime / fmtBytes / parseTrackMeta / sanitizeName / pickRecorderMime / videoBitrate");
eq(E.fmtTime(65), "1:05", "fmtTime(65)");
eq(E.fmtTime(NaN), "0:00", "fmtTime(NaN)");
eq(E.fmtBytes(5 * 1024 * 1024), "5.0 MB", "fmtBytes(5 MB)");
eq(E.parseTrackMeta("Bach - Contrapunctus.mp3").artist, "Bach", "parseTrackMeta artist");
eq(E.sanitizeName('a<b>:c/"d"?*|e'), "abcde", "sanitizeName");
eq(E.pickRecorderMime(mime => /webm/.test(mime) && /vp9/.test(mime)).ext, "webm", "pickRecorderMime → webm");
eq(E.pickRecorderMime(() => true).ext, "mp4", "pickRecorderMime → mp4 優先");
eq(E.videoBitrate(1280, 720, 30), 2211840, "videoBitrate 720p30");
eq(E.mulberry32(1)(), E.mulberry32(1)(), "mulberry32: 決定的");

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
