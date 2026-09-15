/*
 * engine-test.js — Bada Music Studio (DAW) のエンジン単体テスト
 *
 *   node music_studio/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM / Web Audio をスタブした
 * 状態で「純ロジック」部分を検証します。ここが正しければ、再生・書き出し・
 * MIDI 出力の三者は同じスケジュールを共有しているので必ず一致します。
 *
 *   1. 整形        fmtTime / fmtBBT / fmtBytes / sanitizeName
 *   2. 音楽計算    noteToFreq / noteName / nameToNote / scaleNotes / chordNotes
 *   3. グリッド    snap / quantize / applySwing
 *   4. ゲイン      dbToGain / gainToDb / panGains / velocityCurve / adsrAt
 *   5. モデル      newProject / songLengthBeats / soloMask
 *   6. スケジュール buildEvents (クリップ反復・ミュート・スウィング・切り詰め)
 *   7. WAV         wavBytes (16/24/32bit ヘッダとサンプル) / normalizeGain
 *   8. MIDI        encodeVLQ / decodeVLQ / midiBytes / midiParse 往復
 *   9. 保存復元    serializeProject / parseProject (欠損・壊れた値の補正)
 *  10. 画面座標    prY / prN / prX / prB / b2x / x2b の往復
 *  11. デモ曲      demoProject の整合性
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

/* ── サンドボックス (boot は __ENGINE_TEST__ で抑止) ── */
const sandbox = {
  console, Math, Date, JSON, Object, Array, String, Number, Boolean, RegExp, Error,
  isFinite, isNaN, parseInt, parseFloat,
  Uint8Array, Int16Array, Float32Array, ArrayBuffer, DataView,
  setTimeout, clearTimeout, setInterval, clearInterval,
  window: { __ENGINE_TEST__: true },
  document: undefined,
  navigator: {},
  requestAnimationFrame: function () { return 0; }
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "musicstudio-inline.js" });
const E = sandbox;

/* ── テストハーネス ── */
let pass = 0, fail = 0;
function ok(cond, name) {
  if (cond) { pass++; console.log("  ✔ " + name); }
  else { fail++; console.error("  ✘ " + name); }
}
function eq(a, b, name) {
  ok(a === b, name + "  [" + JSON.stringify(a) + " === " + JSON.stringify(b) + "]");
}
function near(a, b, tol, name) {
  ok(Math.abs(a - b) <= tol, name + "  [" + a + " ≈ " + b + " ±" + tol + "]");
}

/* ══ 1. 整形 ══ */
console.log("1. 整形 (fmtTime / fmtBBT / fmtBytes / sanitizeName)");
eq(E.fmtTime(0), "0:00.0", "fmtTime(0)");
eq(E.fmtTime(65.24), "1:05.2", "fmtTime(65.24)");
eq(E.fmtTime(65.25), "1:05.3", "fmtTime(端数は四捨五入)");
eq(E.fmtTime(-3), "0:00.0", "fmtTime(負値)");
eq(E.fmtTime(NaN), "0:00.0", "fmtTime(NaN)");
eq(E.fmtBBT(0, 4), "001.1.000", "fmtBBT(先頭)");
eq(E.fmtBBT(4, 4), "002.1.000", "fmtBBT(2 小節目の頭)");
eq(E.fmtBBT(5.5, 4), "002.2.480", "fmtBBT(2 小節 2 拍 半)");
eq(E.fmtBBT(3, 3), "002.1.000", "fmtBBT(3/4 拍子)");
eq(E.fmtBBT(-1, 4), "001.1.000", "fmtBBT(負値は先頭へ)");
eq(E.fmtBytes(512), "512 B", "fmtBytes(512)");
eq(E.fmtBytes(2048), "2.0 KB", "fmtBytes(2KB)");
eq(E.fmtBytes(5 * 1048576), "5.0 MB", "fmtBytes(5MB)");
eq(E.sanitizeName("my/song:01?"), "my_song_01_", "sanitizeName(禁止文字)");
eq(E.sanitizeName("   "), "bada-session", "sanitizeName(空 → 既定名)");
eq(E.sanitizeName("../../etc/passwd"), "_.._etc_passwd", "sanitizeName(パス脱出を無害化)");
ok(E.sanitizeName("x".repeat(200)).length <= 80, "sanitizeName(長さ制限)");

/* <a download> は非 ASCII 名をまるごと無視する環境があるため、保存名は ASCII に落とす。
   このとき拡張子だけは絶対に失わないこと (失うと OS が開けなくなる) */
eq(E.asciiFileName("Bada Demo - Aurora.wav"), "Bada Demo - Aurora.wav", "asciiFileName(ASCII はそのまま)");
ok(/^bada-[a-z0-9]+\.mid$/.test(E.asciiFileName("\u65e5\u672c\u8a9e\u306e\u66f2.mid")), "asciiFileName(全角のみ → 代替名 + 拡張子)");
eq(E.asciiFileName("\u65e5\u672c\u8a9e\u306e\u66f2.mid"), E.asciiFileName("\u65e5\u672c\u8a9e\u306e\u66f2.mid"), "asciiFileName(同じ曲名なら同じファイル名)");
ok(E.asciiFileName("\u66f2A.mid") !== E.asciiFileName("\u66f2B.mid"), "asciiFileName(別の曲名なら別ファイル名 = 上書き事故を防ぐ)");
eq(E.asciiFileName("\u30c7\u30e2 Demo.badaproj"), "Demo.badaproj", "asciiFileName(混在 → ASCII 部分を残す)");
eq(E.asciiFileName("a\u2014b.wav"), "a_b.wav", "asciiFileName(em ダッシュを _ に)");
ok(/\.mid$/.test(E.asciiFileName("   .mid")), "asciiFileName(空白のみでも拡張子を保持)");
eq(E.asciiFileName("noext"), "noext", "asciiFileName(拡張子なし)");
eq(E.asciiFileName(""), "bada-session", "asciiFileName(空文字)");
["\u65e5\u672c\u8a9e.wav", "\u2014.mid", "x.badaproj", "Song \u2605 1.mid"].forEach(function (n) {
  const out = E.asciiFileName(n);
  if (!/^[\x20-\x7e]+$/.test(out)) { ok(false, "asciiFileName(ASCII のみ): " + n); }
  if (n.indexOf(".") > 0 && out.slice(out.lastIndexOf(".")) !== n.slice(n.lastIndexOf("."))) {
    ok(false, "asciiFileName(拡張子保持): " + n);
  }
});
ok(true, "asciiFileName(常に ASCII のみ / 拡張子を保持)");

/* ══ 2. 音楽計算 ══ */
console.log("2. 音楽計算 (音程 / 音名 / スケール / コード)");
near(E.noteToFreq(69), 440, 1e-9, "noteToFreq(A4) = 440Hz");
near(E.noteToFreq(81), 880, 1e-9, "noteToFreq(A5) = 880Hz");
near(E.noteToFreq(57), 220, 1e-9, "noteToFreq(A3) = 220Hz");
near(E.noteToFreq(60), 261.6255653, 1e-4, "noteToFreq(C4) ≈ 261.63Hz");
eq(E.noteName(60), "C4", "noteName(60)");
eq(E.noteName(69), "A4", "noteName(69)");
eq(E.noteName(0), "C-1", "noteName(0)");
eq(E.noteName(127), "G9", "noteName(127)");
eq(E.nameToNote("C4"), 60, "nameToNote(C4)");
eq(E.nameToNote("A4"), 69, "nameToNote(A4)");
eq(E.nameToNote("Bb3"), 58, "nameToNote(Bb3)");
eq(E.nameToNote("F#5"), 78, "nameToNote(F#5)");
eq(E.nameToNote("H9"), null, "nameToNote(不正)");
for (let n = 0; n <= 127; n++) {
  if (E.nameToNote(E.noteName(n)) !== n) { ok(false, "音名往復 " + n); break; }
  if (n === 127) ok(true, "音名往復 (0〜127 全音)");
}
eq(JSON.stringify(E.scaleNotes(0, "major")), "[0,2,4,5,7,9,11]", "scaleNotes(C メジャー)");
eq(JSON.stringify(E.scaleNotes(9, "minor")), "[0,2,4,5,7,9,11]", "scaleNotes(A マイナー = 白鍵)");
eq(E.scaleNotes(0, "minorPentatonic").length, 5, "scaleNotes(ペンタは 5 音)");
ok(E.inScale(60, 0, "major"), "inScale(C は C メジャー内)");
ok(!E.inScale(61, 0, "major"), "inScale(C# は C メジャー外)");
ok(E.inScale(61, 0, "chromatic"), "inScale(クロマチックは全部内)");
eq(JSON.stringify(E.chordNotes(60, "maj")), "[60,64,67]", "chordNotes(C)");
eq(JSON.stringify(E.chordNotes(57, "min")), "[57,60,64]", "chordNotes(Am)");
eq(JSON.stringify(E.chordNotes(60, "maj7")), "[60,64,67,71]", "chordNotes(CM7)");
eq(JSON.stringify(E.chordNotes(60, "unknown")), "[60]", "chordNotes(未知 → 単音)");
const tr = E.transpose([{ b: 0, d: 1, n: 60, v: 100 }, { b: 1, d: 1, n: 126, v: 90 }], 4);
eq(tr.length, 1, "transpose(127 超は除外)");
eq(tr[0].n, 64, "transpose(+4 半音)");

/* ══ 3. グリッド / クオンタイズ / スウィング ══ */
console.log("3. グリッド (snap / quantize / applySwing)");
eq(E.snap(0.26, 0.25), 0.25, "snap(1/16 グリッド)");
eq(E.snap(0.4, 0.5), 0.5, "snap(1/8 グリッド)");
eq(E.snap(1.3, 0), 1.3, "snap(グリッド off はそのまま)");
const q = E.quantize([{ b: 0.07, d: 0.5, n: 60, v: 100 }, { b: 1.94, d: 0.5, n: 62, v: 100 }], 0.5, 1);
eq(q[0].b, 0, "quantize(0.07 → 0)");
eq(q[1].b, 2, "quantize(1.94 → 2)");
const qh = E.quantize([{ b: 0.10, d: 0.5, n: 60, v: 100 }], 0.5, 0.5);
near(qh[0].b, 0.05, 1e-6, "quantize(強さ 50%)");
eq(E.applySwing(0, 0.5, 0.5), 0, "applySwing(表拍は動かない)");
near(E.applySwing(0.5, 0.5, 0.5), 0.625, 1e-9, "applySwing(裏拍が後ろへ)");
eq(E.applySwing(0.5, 0, 0.5), 0.5, "applySwing(0% はそのまま)");
eq(E.applySwing(0.37, 0.5, 0.5), 0.37, "applySwing(グリッド外は対象外)");

/* ══ 4. ゲイン / パン / エンベロープ ══ */
console.log("4. ゲイン / パン / エンベロープ");
near(E.dbToGain(0), 1, 1e-9, "dbToGain(0dB) = 1.0");
near(E.dbToGain(-6), 0.5011872, 1e-6, "dbToGain(-6dB) ≈ 0.501");
eq(E.dbToGain(-70), 0, "dbToGain(-70dB) = 無音");
near(E.gainToDb(1), 0, 1e-9, "gainToDb(1.0) = 0dB");
near(E.gainToDb(E.dbToGain(-12)), -12, 1e-6, "dB 往復");
const pc = E.panGains(0);
near(pc.l, pc.r, 1e-9, "panGains(中央は左右同値)");
near(pc.l * pc.l + pc.r * pc.r, 1, 1e-9, "panGains(等パワー)");
near(E.panGains(-1).l, 1, 1e-9, "panGains(左端)");
near(E.panGains(1).r, 1, 1e-9, "panGains(右端)");
eq(E.velocityCurve(0), 0, "velocityCurve(0)");
near(E.velocityCurve(127), 1, 1e-9, "velocityCurve(127) = 1.0");
ok(E.velocityCurve(64) < 0.5, "velocityCurve(中間は 0.5 未満 = 聴感カーブ)");
const env = { a: 0.1, d: 0.2, s: 0.5, r: 0.4 };
eq(E.adsrAt(env, 0, 10), 0, "adsrAt(発音直後は 0)");
near(E.adsrAt(env, 0.1, 10), 1, 1e-9, "adsrAt(アタック終端 = ピーク)");
near(E.adsrAt(env, 0.3, 10), 0.5, 1e-9, "adsrAt(ディケイ後 = サステイン)");
near(E.adsrAt(env, 1.0, 10), 0.5, 1e-9, "adsrAt(サステイン保持)");
near(E.adsrAt(env, 1.2, 1.0), 0.25, 1e-3, "adsrAt(リリース半分)");
eq(E.adsrAt(env, 1.5, 1.0), 0, "adsrAt(リリース完了 = 0)");

/* ══ 5. プロジェクトモデル ══ */
console.log("5. プロジェクトモデル");
const proj = E.newProject("Test");
eq(proj.bpm, 120, "newProject(既定 BPM)");
eq(proj.sig, 4, "newProject(既定 4/4)");
eq(proj.tracks.length, 0, "newProject(トラックなし)");
eq(E.songLengthBeats(proj), 32, "songLengthBeats(8 小節 = 32 拍)");
eq(E.beatsToSec(4, 120), 2, "beatsToSec(120BPM で 1 小節 = 2 秒)");
eq(E.secToBeats(2, 120), 4, "secToBeats(逆変換)");
const dp = E.newDrumPattern("D", 1, 4, 4);
eq(dp.steps.kick.length, 16, "newDrumPattern(1 小節 1/16 = 16 ステップ)");
eq(E.DRUM_KIT.length, 10, "ドラムキットは 10 音源");
eq(E.drumById("kick").gm, 36, "drumById(kick の GM 番号)");
eq(E.drumById("nope"), null, "drumById(未知)");
const ms = [{ mute: false, solo: false }, { mute: true, solo: false }, { mute: false, solo: false }];
eq(JSON.stringify(E.soloMask(ms)), "[true,false,true]", "soloMask(ミュートのみ)");
const ms2 = [{ mute: false, solo: false }, { mute: false, solo: true }, { mute: false, solo: false }];
eq(JSON.stringify(E.soloMask(ms2)), "[false,true,false]", "soloMask(ソロ優先)");
const ms3 = [{ mute: true, solo: true }, { mute: false, solo: true }];
eq(JSON.stringify(E.soloMask(ms3)), "[false,true]", "soloMask(ソロ中のミュートは無音)");

/* ══ 6. スケジュール生成 ══ */
console.log("6. スケジュール生成 (buildEvents)");
function fixture() {
  const p = E.newProject("Fixture");
  p.bpm = 120; p.sig = 4; p.bars = 2;
  const np = E.newNotePattern("N", 1, 4);          /* 長さ 4 拍 */
  np.notes.push({ b: 0, d: 1, n: 60, v: 100 });
  np.notes.push({ b: 2, d: 1, n: 64, v: 80 });
  const dpx = E.newDrumPattern("D", 1, 4, 4);
  dpx.steps.kick[0] = 110; dpx.steps.kick[8] = 90;
  dpx.steps.hhc[2] = 60;
  p.patterns.push(np, dpx);
  const t1 = E.newTrack("inst", "Synth", 0);
  t1.clips.push({ id: "c1", patternId: np.id, start: 0, length: 8 });   /* 2 回反復 */
  const t2 = E.newTrack("drum", "Drums", 1);
  t2.clips.push({ id: "c2", patternId: dpx.id, start: 0, length: 4 });
  p.tracks.push(t1, t2);
  return p;
}
const F = fixture();
const ev = E.buildEvents(F);
eq(ev.filter(e => e.type === "note").length, 4, "buildEvents(4 拍パターンを 8 拍分 = 2 反復)");
eq(ev.filter(e => e.type === "drum").length, 3, "buildEvents(ドラム 3 打)");
eq(ev[0].t, 0, "buildEvents(時間順にソート)");
const noteTimes = ev.filter(e => e.type === "note").map(e => e.t);
eq(JSON.stringify(noteTimes), "[0,2,4,6]", "buildEvents(反復の絶対位置)");
const kicks = ev.filter(e => e.drum === "kick").map(e => e.t);
eq(JSON.stringify(kicks), "[0,2]", "buildEvents(1/16 ステップ 0 と 8 = 0 拍と 2 拍)");
eq(ev.find(e => e.drum === "kick").vel, 110, "buildEvents(ステップのベロシティを保持)");

const F2 = fixture();
F2.tracks[0].mute = true;
eq(E.buildEvents(F2).filter(e => e.type === "note").length, 0, "buildEvents(ミュートは除外)");
eq(E.buildEvents(F2, { includeMuted: true }).filter(e => e.type === "note").length, 4, "buildEvents(includeMuted で復帰)");
const F3 = fixture();
F3.tracks[1].solo = true;
eq(E.buildEvents(F3).filter(e => e.type === "note").length, 0, "buildEvents(ソロで他が無音)");
const F4 = fixture();
eq(E.buildEvents(F4, { onlyTrack: F4.tracks[1].id }).every(e => e.type === "drum"), true, "buildEvents(onlyTrack = ステム用)");

const F5 = fixture();
F5.tracks[0].clips[0].length = 3;                 /* パターンより短いクリップ */
const short = E.buildEvents(F5).filter(e => e.type === "note");
eq(short.length, 2, "buildEvents(クリップ長で切り詰め)");
eq(short[1].t + short[1].dur <= 3, true, "buildEvents(末尾ノートがクリップ外へはみ出さない)");

const F6 = fixture();
F6.swing = 50;
F6.patterns[1].steps.hhc[1] = 60;                  /* 1/16 の裏 (奇数ステップ) */
const swHats = E.buildEvents(F6).filter(e => e.drum === "hhc").map(e => e.t);
near(swHats[0], 0.3125, 1e-9, "buildEvents(裏の 1/16 がスウィングで後ろへ)");
eq(swHats[1], 0.5, "buildEvents(表の 1/16 は動かない)");
eq(E.buildEvents(fixture()).filter(e => e.drum === "hhc")[0].t, 0.5, "buildEvents(スウィング 0% は素の位置)");

eq(JSON.stringify(E.metroTicks(0, 4, 4).map(t => t.t)), "[0,1,2,3]", "metroTicks(4 拍)");
eq(E.metroTicks(0, 4, 4)[0].accent, true, "metroTicks(小節頭はアクセント)");
eq(E.metroTicks(1, 4, 4)[0].accent, false, "metroTicks(2 拍目はアクセントなし)");

/* ══ 7. WAV エンコーダ ══ */
console.log("7. WAV エンコーダ");
function str4(u8, off) { return String.fromCharCode(u8[off], u8[off + 1], u8[off + 2], u8[off + 3]); }
function rdU32(u8, off) { return u8[off] | (u8[off + 1] << 8) | (u8[off + 2] << 16) | (u8[off + 3] * 16777216); }
function rdU16(u8, off) { return u8[off] | (u8[off + 1] << 8); }
const L = new Float32Array([0, 0.5, -0.5, 1, -1]);
const R = new Float32Array([0, -0.5, 0.5, -1, 1]);
const w16 = E.wavBytes([L, R], 44100, 16);
eq(str4(w16, 0), "RIFF", "wav(RIFF マジック)");
eq(str4(w16, 8), "WAVE", "wav(WAVE)");
eq(str4(w16, 12), "fmt ", "wav(fmt チャンク)");
eq(str4(w16, 36), "data", "wav(data チャンク)");
eq(rdU16(w16, 20), 1, "wav(16bit は PCM フォーマット 1)");
eq(rdU16(w16, 22), 2, "wav(2 チャンネル)");
eq(rdU32(w16, 24), 44100, "wav(サンプルレート)");
eq(rdU32(w16, 28), 44100 * 2 * 2, "wav(バイトレート)");
eq(rdU16(w16, 32), 4, "wav(ブロックアライン)");
eq(rdU16(w16, 34), 16, "wav(ビット深度)");
eq(rdU32(w16, 40), 5 * 2 * 2, "wav(data サイズ)");
eq(w16.length, 44 + 5 * 2 * 2, "wav(総バイト数)");
eq(rdU32(w16, 4), 36 + 5 * 2 * 2, "wav(RIFF サイズ)");
const dv16 = new DataView(w16.buffer, w16.byteOffset, w16.byteLength);
eq(dv16.getInt16(44, true), 0, "wav(サンプル 0)");
eq(dv16.getInt16(44 + 4, true), Math.round(0.5 * 32767), "wav(サンプル +0.5)");
eq(dv16.getInt16(44 + 12, true), 32767, "wav(サンプル +1.0 が最大値)");
eq(dv16.getInt16(44 + 16, true), -32767, "wav(サンプル -1.0)");
const w24 = E.wavBytes([L, R], 48000, 24);
eq(rdU16(w24, 34), 24, "wav24(ビット深度)");
eq(w24.length, 44 + 5 * 2 * 3, "wav24(総バイト数)");
const w32 = E.wavBytes([L, R], 44100, 32);
eq(rdU16(w32, 20), 3, "wav32(IEEE float フォーマット 3)");
eq(new DataView(w32.buffer, w32.byteOffset).getFloat32(44 + 8, true), 0.5, "wav32(float 値をそのまま格納)");
const clipped = E.wavBytes([new Float32Array([5, -5, NaN])], 44100, 16);
const dvc = new DataView(clipped.buffer, clipped.byteOffset);
eq(dvc.getInt16(44, true), 32767, "wav(範囲外 +5 をクリップ)");
eq(dvc.getInt16(46, true), -32767, "wav(範囲外 -5 をクリップ)");
eq(dvc.getInt16(48, true), 0, "wav(NaN を 0 に)");
eq(E.wavBytes([L], 44100, 16).length, 44 + 5 * 2, "wav(モノラル)");
near(E.normalizeGain([new Float32Array([0.5, -0.25])], -0.3), E.dbToGain(-0.3) / 0.5, 1e-9, "normalizeGain(ピーク基準)");
eq(E.normalizeGain([new Float32Array([0, 0])], -0.3), 1, "normalizeGain(無音は 1.0)");

/* ══ 8. MIDI ══ */
console.log("8. MIDI エンコーダ / デコーダ");
eq(JSON.stringify(E.encodeVLQ(0)), "[0]", "encodeVLQ(0)");
eq(JSON.stringify(E.encodeVLQ(127)), "[127]", "encodeVLQ(127)");
eq(JSON.stringify(E.encodeVLQ(128)), "[129,0]", "encodeVLQ(128 = 0x81 0x00)");
eq(JSON.stringify(E.encodeVLQ(16383)), "[255,127]", "encodeVLQ(16383 = 0xFF 0x7F)");
eq(JSON.stringify(E.encodeVLQ(1048576)), "[192,128,0]", "encodeVLQ(0x100000)");
[0, 1, 127, 128, 8192, 16383, 100000, 1048576, 134217727].forEach(function (v) {
  const b = E.encodeVLQ(v);
  if (E.decodeVLQ(b, 0).value !== v) { ok(false, "VLQ 往復 " + v); }
});
ok(true, "VLQ 往復 (境界値 9 種)");

const mb = E.midiBytes(F);
eq(str4(mb, 0), "MThd", "midi(MThd ヘッダ)");
eq((mb[8] << 8) | mb[9], 1, "midi(format 1)");
eq((mb[10] << 8) | mb[11], 3, "midi(コンダクタ + 2 トラック)");
eq((mb[12] << 8) | mb[13], 480, "midi(480 ticks/quarter)");
eq(str4(mb, 14), "MTrk", "midi(最初のトラックチャンク)");
const parsed = E.midiParse(mb);
eq(parsed.tpq, 480, "midiParse(分解能)");
eq(parsed.bpm, 120, "midiParse(テンポ)");
eq(parsed.tracks.length, 2, "midiParse(音のあるトラック数)");
eq(parsed.tracks[0].notes.length, 4, "midiParse(ノート数が一致)");
eq(parsed.tracks[0].notes[0].n, 60, "midiParse(音高)");
eq(parsed.tracks[0].notes[0].v, 100, "midiParse(ベロシティ)");
near(parsed.tracks[0].notes[0].d, 1, 1e-6, "midiParse(音長 1 拍)");
eq(JSON.stringify(parsed.tracks[0].notes.map(n => n.b)), "[0,2,4,6]", "midiParse(発音位置)");
ok(parsed.tracks[1].isDrum, "midiParse(ドラムは ch.10 として識別)");
eq(parsed.tracks[1].notes[0].n, 36, "midiParse(キック = GM 36)");
const tempo180 = fixture(); tempo180.bpm = 180;
eq(E.midiParse(E.midiBytes(tempo180)).bpm, 180, "midi(テンポ往復 180BPM)");
let threw = false;
try { E.midiParse(new Uint8Array([1, 2, 3])); } catch (e) { threw = true; }
ok(threw, "midiParse(壊れたファイルは例外)");

/* ══ 9. 保存 / 復元 ══ */
console.log("9. 保存 / 復元 (serializeProject / parseProject)");
const json = E.serializeProject(F);
ok(json.length > 100, "serializeProject(JSON を生成)");
const back = E.parseProject(json);
eq(back.name, F.name, "parseProject(名前)");
eq(back.bpm, F.bpm, "parseProject(BPM)");
eq(back.tracks.length, F.tracks.length, "parseProject(トラック数)");
eq(back.patterns.length, F.patterns.length, "parseProject(パターン数)");
eq(E.buildEvents(back).length, E.buildEvents(F).length, "parseProject(同じスケジュールを再現)");
eq(JSON.stringify(E.buildEvents(back).map(e => e.t)), JSON.stringify(E.buildEvents(F).map(e => e.t)), "parseProject(発音位置が完全一致)");
const minimal = E.parseProject('{"name":"Min"}');
eq(minimal.bpm, 120, "parseProject(欠損 BPM を既定値で補完)");
eq(minimal.tracks.length, 0, "parseProject(トラックなしでも動く)");
const dirty = E.parseProject(JSON.stringify({
  name: "Dirty", bpm: 9999, sig: 0, swing: 500, masterVol: 99,
  patterns: [{ id: "p1", type: "note", name: "P", length: 4, notes: [{ b: -5, d: 0, n: 999, v: 999 }, null, { n: "x" }] }],
  tracks: [{ id: "t1", type: "weird", name: "T", vol: 999, pan: 9, clips: [{ patternId: "p1", start: -3, length: 0 }] }]
}));
eq(dirty.bpm, 300, "parseProject(BPM の上限でクランプ)");
eq(dirty.swing, 90, "parseProject(スウィングの上限)");
eq(dirty.masterVol, 12, "parseProject(マスター音量の上限)");
eq(dirty.patterns[0].notes.length, 1, "parseProject(壊れたノートを破棄)");
eq(dirty.patterns[0].notes[0].n, 127, "parseProject(音高をクランプ)");
eq(dirty.patterns[0].notes[0].b, 0, "parseProject(負の位置を 0 に)");
ok(dirty.patterns[0].notes[0].d > 0, "parseProject(長さ 0 を最小値に)");
eq(dirty.tracks[0].type, "inst", "parseProject(未知のトラック種別を inst に)");
eq(dirty.tracks[0].vol, 12, "parseProject(トラック音量をクランプ)");
eq(dirty.tracks[0].pan, 1, "parseProject(パンをクランプ)");
eq(dirty.tracks[0].clips[0].start, 0, "parseProject(クリップ位置を 0 に)");
let threw2 = false;
try { E.parseProject("null"); } catch (e) { threw2 = true; }
ok(threw2, "parseProject(不正な入力は例外)");

/* ══ 10. 画面座標の逆変換 ══ */
console.log("10. 画面座標 (ピアノロール / アレンジ)");
/* prY は行の上端、prN はその逆。行内のどこを指しても同じ音高に戻ること */
let coordBad = 0;
for (let n = E.PR_LO; n <= E.PR_HI; n++) {
  for (const off of [0.1, 0.5, 0.9]) {
    const y = E.prY(n) + E.UI.keyH * off;
    if (E.prN(y) !== n) { coordBad++; }
  }
}
eq(coordBad, 0, "prY / prN(行内のどこを指しても同じ音高)");
eq(E.prN(E.prY(60)), 60, "prN(行の上端 = その音)");
eq(E.prN(E.prY(60) + E.UI.keyH - 0.01), 60, "prN(行の下端 = まだその音)");
eq(E.prN(E.prY(60) + E.UI.keyH), 59, "prN(次の行は半音下)");
eq(E.prN(E.prY(60) - 0.01), 61, "prN(ひとつ上の行は半音上)");
near(E.prB(E.prX(2.5)), 2.5, 1e-9, "prX / prB 往復");
near(E.prB(E.prX(0)), 0, 1e-9, "prX(0) は鍵盤幅のちょうど右");
near(E.x2b(E.b2x(7.25)), 7.25, 1e-9, "b2x / x2b 往復 (アレンジ)");

/* ══ 11. プリセット / デモ曲 ══ */
console.log("11. プリセット / デモ曲");
const names = E.presetNames();
ok(names.length >= 12, "プリセットが 12 種以上 (" + names.length + " 種)");
names.forEach(function (n) {
  const p = E.loadPreset(n);
  if (!p || !p.osc1 || !p.aenv || !p.filter) { ok(false, "プリセット " + n + " の構造"); }
});
ok(true, "全プリセットが必須フィールドを持つ");
eq(E.loadPreset("存在しない").name, "Init", "loadPreset(未知 → Init)");
const demo = E.demoProject();
eq(demo.tracks.length, 5, "デモ曲のトラック数");
eq(demo.patterns.length, 6, "デモ曲のパターン数");
eq(E.songLengthBeats(demo), 32, "デモ曲は 8 小節 (32 拍)");
const dev = E.buildEvents(demo);
ok(dev.length > 200, "デモ曲のイベント数 (" + dev.length + " 音)");
ok(dev.every(e => e.t >= 0 && e.t < 32), "デモ曲の全イベントがソング内に収まる");
ok(dev.every(e => e.vel > 0 && e.vel <= 127), "デモ曲のベロシティが有効範囲");
ok(dev.every(e => e.type !== "note" || (e.midi >= 0 && e.midi <= 127)), "デモ曲の音高が有効範囲");
const demoBack = E.parseProject(E.serializeProject(demo));
eq(E.buildEvents(demoBack).length, dev.length, "デモ曲の保存 / 復元往復");
ok(E.midiBytes(demo).length > 1000, "デモ曲の MIDI 書き出し");

/* ── 結果 ── */
console.log("");
console.log("─".repeat(58));
console.log("  合格 " + pass + " / 失敗 " + fail);
console.log("─".repeat(58));
process.exit(fail ? 1 : 0);
