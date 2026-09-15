/*
 * engine-test.js — Bada AudioForge (オーディオエディタ) のエンジン単体テスト
 *
 *   node audio_editor/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分 (音声編集エンジン) を検証します:
 *   1. 整形        — fmtTime / fmtBytes / fmtDb / sanitizeName / baseName
 *   2. dB 変換     — dbToLin / linToDb / clampSample
 *   3. Clip 基本   — makeClip / cloneClip / secToSample / normRange
 *   4. 編集        — sliceClip / deleteRange / insertClip / mixClip /
 *                    insertSilence / repeatRange / matchChannels
 *   5. リサンプル  — resampleChannel / resampleTo / changeSpeed
 *   6. 振幅        — peakOf / rmsOf / applyGainRange / normalizeRange
 *   7. エフェクト  — fadeGain / fadeRange / silenceRange / reverseRange /
 *                    removeDcOffset / panRange / toMono
 *   8. フィルタ    — onePoleCoef / filterRange / echoRange
 *   9. 解析        — trimSilenceRange / findZeroCrossing
 *  10. 描画補助    — channelPeaks / niceTimeStep
 *  11. WAV 入出力 — encodeWav / parseWav (16/24/32bit ラウンドトリップ)
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
  console,
  window: { __ENGINE_TEST__: true },
  document: undefined,
  navigator: {},
  requestAnimationFrame: function () { return 0; },
  cancelAnimationFrame: function () {},
  setTimeout: function () { return 0; },
  URL: { createObjectURL: function () { return "blob:stub"; }, revokeObjectURL: function () {} }
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "audioforge-inline.js" });

const E = sandbox;                       /* エンジンの公開関数 */
/* 型付き配列はサンドボックス側の実体を使う (レルムをまたがないため) */
const F32 = vm.runInContext("Float32Array", sandbox);
const U8 = vm.runInContext("Uint8Array", sandbox);

/* ── テストハーネス ── */
let pass = 0, fail = 0;
function ok(cond, name) {
  if (cond) { pass++; console.log("  ✔ " + name); }
  else { fail++; console.error("  ✘ " + name); }
}
function eq(a, b, name) {
  ok(Object.is(a, b), name + "  [" + JSON.stringify(a) + " === " + JSON.stringify(b) + "]");
}
function near(a, b, name, tol) {
  const t = tol == null ? 1e-5 : tol;
  ok(Math.abs(a - b) <= t, name + "  [" + a + " ≈ " + b + " ±" + t + "]");
}
function arrEq(arr, expected, name, tol) {
  const t = tol == null ? 1e-6 : tol;
  let good = arr.length === expected.length;
  if (good) for (let i = 0; i < expected.length; i++) {
    if (Math.abs(arr[i] - expected[i]) > t) { good = false; break; }
  }
  ok(good, name + "  [" + Array.from(arr).map(v => +v.toFixed(4)).join(",") +
     " ≈ " + expected.join(",") + "]");
}

/* ── テスト用 Clip の生成 ── */
function clipOf(rate, ...channels) {
  return E.makeClip(rate, channels.map(a => F32.from(a)));
}

/* ══════════ 1. 整形 ══════════ */
console.log("1. 整形 (fmtTime / fmtBytes / fmtDb / sanitizeName)");
eq(E.fmtTime(0), "0:00.000", "fmtTime(0)");
eq(E.fmtTime(1.5), "0:01.500", "fmtTime(1.5)");
eq(E.fmtTime(65.025), "1:05.025", "fmtTime(65.025) ミリ秒ゼロ詰め");
eq(E.fmtTime(65.007), "1:05.007", "fmtTime(65.007) ミリ秒 3 桁");
eq(E.fmtTime(3599.999), "59:59.999", "fmtTime(3599.999)");
eq(E.fmtTime(-5), "0:00.000", "fmtTime(負値)");
eq(E.fmtTime(NaN), "0:00.000", "fmtTime(NaN)");
eq(E.fmtBytes(500), "500 B", "fmtBytes(500)");
eq(E.fmtBytes(2048), "2.0 KB", "fmtBytes(2 KB)");
eq(E.fmtBytes(5 * 1024 * 1024), "5.0 MB", "fmtBytes(5 MB)");
eq(E.fmtBytes(3 * 1024 * 1024 * 1024), "3.00 GB", "fmtBytes(3 GB)");
eq(E.fmtDb(0), "+0.0 dB", "fmtDb(0)");
eq(E.fmtDb(-6.02), "-6.0 dB", "fmtDb(-6.02)");
eq(E.fmtDb(-120), "-∞ dB", "fmtDb(下限)");
eq(E.sanitizeName('a<b>:c/"d"?*|e'), "abcde", "sanitizeName 不正文字除去");
eq(E.sanitizeName("   "), "audio", "sanitizeName 空 → audio");
eq(E.sanitizeName("夜に駆ける"), "夜に駆ける", "sanitizeName 日本語はそのまま");
eq(E.baseName("song.mp3"), "song", "baseName 拡張子除去");
eq(E.baseName("my.track.final.wav"), "my.track.final", "baseName 最後の拡張子のみ");
eq(E.baseName("noext"), "noext", "baseName 拡張子なし");

/* ══════════ 2. dB 変換 ══════════ */
console.log("2. dB 変換 (dbToLin / linToDb / clampSample)");
near(E.dbToLin(0), 1, "dbToLin(0 dB) = 1");
near(E.dbToLin(6.0206), 2, "dbToLin(+6 dB) = 2", 1e-3);
near(E.dbToLin(-6.0206), 0.5, "dbToLin(-6 dB) = 0.5", 1e-3);
near(E.linToDb(1), 0, "linToDb(1) = 0 dB");
near(E.linToDb(0.5), -6.0206, "linToDb(0.5) = -6 dB", 1e-3);
eq(E.linToDb(0), -120, "linToDb(0) = 下限 -120");
near(E.linToDb(-0.5), -6.0206, "linToDb は絶対値で評価", 1e-3);
eq(E.clampSample(1.5), 1, "clampSample(+過大)");
eq(E.clampSample(-1.5), -1, "clampSample(-過大)");
eq(E.clampSample(0.3), 0.3, "clampSample(範囲内)");

/* ══════════ 3. Clip 基本 ══════════ */
console.log("3. Clip 基本 (makeClip / cloneClip / secToSample / normRange)");
let c1 = clipOf(8000, [0, 0.5, -0.5, 1]);
eq(c1.length, 4, "length");
eq(c1.numberOfChannels, 1, "numberOfChannels");
eq(c1.sampleRate, 8000, "sampleRate");
near(E.clipDuration(c1), 4 / 8000, "clipDuration");
eq(E.clipDuration(E.emptyClip(44100, 2, 44100)), 1, "emptyClip 1 秒");
let c1b = E.cloneClip(c1);
c1b.channels[0][0] = 0.9;
eq(c1.channels[0][0], 0, "cloneClip は元を書き換えない");
eq(E.secToSample(clipOf(1000, new Array(1000).fill(0)), 0.5), 500, "secToSample(0.5s)");
eq(E.secToSample(c1, 999), 4, "secToSample は length で頭打ち");
eq(E.secToSample(c1, -9), 0, "secToSample は 0 で下限");
let r = E.normRange(c1, 3, 1);
eq(r.start, 1, "normRange 逆順を入れ替え (start)");
eq(r.end, 3, "normRange 逆順を入れ替え (end)");
eq(r.len, 2, "normRange len");
r = E.normRange(c1, -5, 99);
eq(r.start + "/" + r.end, "0/4", "normRange は範囲外をクランプ");

/* ══════════ 4. 編集 ══════════ */
console.log("4. 編集 (slice / delete / insert / mix / silence / repeat / channels)");
let base = clipOf(8000, [0, 1, 2, 3, 4]);
arrEq(E.sliceClip(base, 1, 3).channels[0], [1, 2], "sliceClip [1,3)");
eq(E.sliceClip(base, 1, 3).length, 2, "sliceClip length");
arrEq(E.deleteRange(base, 1, 3).channels[0], [0, 3, 4], "deleteRange [1,3)");
eq(E.deleteRange(base, 2, 2).length, 5, "deleteRange 空範囲は無変更");
arrEq(base.channels[0], [0, 1, 2, 3, 4], "編集は非破壊 (元の Clip は不変)");
arrEq(E.insertClip(clipOf(8000, [0, 1, 2]), clipOf(8000, [9, 9]), 1).channels[0],
      [0, 9, 9, 1, 2], "insertClip 位置 1");
arrEq(E.insertClip(clipOf(8000, [0, 1]), clipOf(8000, [9]), 99).channels[0],
      [0, 1, 9], "insertClip 範囲外の位置は末尾");
arrEq(E.mixClip(clipOf(8000, [0, 0, 0]), clipOf(8000, [1, 1]), 1).channels[0],
      [0, 1, 1], "mixClip 重ね合わせ");
arrEq(E.mixClip(clipOf(8000, [0.8]), clipOf(8000, [0.5]), 0).channels[0],
      [1], "mixClip はクリップされる");
eq(E.mixClip(clipOf(8000, [0, 0]), clipOf(8000, [1, 1, 1]), 1).length, 4,
   "mixClip は必要なら伸びる");
let sil = E.insertSilence(clipOf(1000, [1, 1]), 1, 0.003);
arrEq(sil.channels[0], [1, 0, 0, 0, 1], "insertSilence 3 サンプル");
arrEq(E.repeatRange(clipOf(8000, [0, 1, 2, 3]), 1, 3, 3).channels[0],
      [0, 1, 2, 1, 2, 1, 2, 3], "repeatRange ×3");
eq(E.repeatRange(base, 1, 3, 1).length, 5, "repeatRange ×1 は無変更");
let st = clipOf(8000, [1, 1], [0, 0]);
arrEq(E.matchChannels(st, 1).channels[0], [0.5, 0.5], "matchChannels 2ch→1ch ダウンミックス");
eq(E.matchChannels(clipOf(8000, [1]), 2).numberOfChannels, 2, "matchChannels 1ch→2ch");
arrEq(E.matchChannels(clipOf(8000, [0.7]), 2).channels[1], [0.7], "matchChannels 複製内容");
/* サンプルレートの違う素材の挿入は自動リサンプル */
let ins = E.insertClip(E.emptyClip(44100, 1, 10), E.emptyClip(22050, 1, 10), 0);
eq(ins.length, 30, "insertClip はサンプルレートを自動整合 (10+20)");

/* ══════════ 5. リサンプル ══════════ */
console.log("5. リサンプル (resampleChannel / resampleTo / changeSpeed)");
arrEq(E.resampleChannel(F32.from([0, 1]), 3), [0, 0.5, 1], "resampleChannel 線形補間");
arrEq(E.resampleChannel(F32.from([0, 1, 2]), 2), [0, 2], "resampleChannel 縮小は端点を保つ");
eq(E.resampleChannel(F32.from([]), 4).length, 4, "resampleChannel 空入力");
arrEq(E.resampleChannel(F32.from([0.25]), 3), [0.25, 0.25, 0.25], "resampleChannel 1 サンプル入力");
let rs = E.resampleTo(E.emptyClip(44100, 2, 44100), 22050);
eq(rs.length, 22050, "resampleTo 44.1k→22.05k で半分の長さ");
eq(rs.sampleRate, 22050, "resampleTo サンプルレート更新");
eq(E.resampleTo(rs, 22050).length, 22050, "resampleTo 同一レートは素通し");
eq(E.changeSpeed(E.emptyClip(8000, 1, 100), 2).length, 50, "changeSpeed ×2 で半分");
eq(E.changeSpeed(E.emptyClip(8000, 1, 100), 0.5).length, 200, "changeSpeed ×0.5 で倍");
eq(E.changeSpeed(E.emptyClip(8000, 1, 100), 2).sampleRate, 8000, "changeSpeed はレート据え置き");
eq(E.changeSpeed(base, 1).length, 5, "changeSpeed ×1 は無変更");

/* ══════════ 6. 振幅 ══════════ */
console.log("6. 振幅 (peakOf / rmsOf / applyGainRange / normalizeRange)");
let amp = clipOf(8000, [0.1, -0.6, 0.25, 0.6]);
near(E.peakOf(amp, 0, 4), 0.6, "peakOf 全体");
near(E.peakOf(amp, 0, 2), 0.6, "peakOf は絶対値");
near(E.peakOf(amp, 2, 3), 0.25, "peakOf 部分範囲");
near(E.rmsOf(clipOf(8000, [0.5, -0.5, 0.5, -0.5]), 0, 4), 0.5, "rmsOf 矩形波");
eq(E.rmsOf(amp, 2, 2), 0, "rmsOf 空範囲は 0");
arrEq(E.applyGainRange(clipOf(8000, [0.1, 0.2, 0.3]), 1, 3, 2).channels[0],
      [0.1, 0.4, 0.6], "applyGainRange 範囲のみ 2 倍");
arrEq(E.applyGainRange(clipOf(8000, [0.8]), 0, 1, 4).channels[0], [1],
      "applyGainRange はクリップされる");
near(E.peakOf(E.normalizeRange(clipOf(8000, [0.25, -0.5]), 0, 2, 0), 0, 2), 1,
     "normalizeRange 0 dB でピーク 1", 1e-4);
near(E.peakOf(E.normalizeRange(clipOf(8000, [0.25, -0.5]), 0, 2, -6.0206), 0, 2), 0.5,
     "normalizeRange -6 dB でピーク 0.5", 1e-3);
arrEq(E.normalizeRange(E.emptyClip(8000, 1, 3), 0, 3, 0).channels[0], [0, 0, 0],
      "normalizeRange 無音は無変更 (0 除算なし)");

/* ══════════ 7. エフェクト ══════════ */
console.log("7. エフェクト (fade / silence / reverse / DC / pan / mono)");
eq(E.fadeGain(0.5, "linear"), 0.5, "fadeGain リニア");
eq(E.fadeGain(0.5, "exp"), 0.25, "fadeGain 指数");
near(E.fadeGain(0.5, "scurve"), 0.5, "fadeGain S カーブ 中点");
near(E.fadeGain(0.25, "scurve"), 0.14645, "fadeGain S カーブ 1/4 点", 1e-4);
eq(E.fadeGain(-1, "linear"), 0, "fadeGain 下限クランプ");
eq(E.fadeGain(9, "linear"), 1, "fadeGain 上限クランプ");
arrEq(E.fadeRange(clipOf(8000, [1, 1, 1, 1, 1]), 0, 5, "in", "linear").channels[0],
      [0, 0.25, 0.5, 0.75, 1], "fadeRange フェードイン(リニア)");
arrEq(E.fadeRange(clipOf(8000, [1, 1, 1, 1, 1]), 0, 5, "out", "linear").channels[0],
      [1, 0.75, 0.5, 0.25, 0], "fadeRange フェードアウト(リニア)");
arrEq(E.fadeRange(clipOf(8000, [1, 1, 1, 1]), 2, 4, "out", "linear").channels[0],
      [1, 1, 1, 0], "fadeRange 範囲のみ適用");
arrEq(E.silenceRange(clipOf(8000, [1, 1, 1]), 0, 2).channels[0], [0, 0, 1], "silenceRange");
arrEq(E.reverseRange(clipOf(8000, [1, 2, 3]), 0, 3).channels[0], [3, 2, 1], "reverseRange 全体");
arrEq(E.reverseRange(clipOf(8000, [1, 2, 3, 4]), 1, 3).channels[0], [1, 3, 2, 4],
      "reverseRange 範囲のみ");
arrEq(E.removeDcOffset(clipOf(8000, [0.5, 0.5, 0.5]), 0, 3).channels[0], [0, 0, 0],
      "removeDcOffset 直流成分を 0 に");
arrEq(E.removeDcOffset(clipOf(8000, [0.6, 0.4]), 0, 2).channels[0], [0.1, -0.1],
      "removeDcOffset 平均を差し引く");
let pan = E.panRange(clipOf(8000, [1, 1], [1, 1]), 0, 2, 0);
near(pan.channels[0][0], 1, "panRange 中央は左ユニティ");
near(pan.channels[1][0], 1, "panRange 中央は右ユニティ");
let panL = E.panRange(clipOf(8000, [1, 1], [1, 1]), 0, 2, -1);
near(panL.channels[1][0], 0, "panRange 左端で右チャンネル無音");
near(panL.channels[0][0], 1, "panRange 左端で左チャンネル最大");
eq(E.panRange(clipOf(8000, [1]), 0, 1, 1).numberOfChannels, 1, "panRange モノラルは無変更");
let mono = E.toMono(clipOf(8000, [1, 1], [0, 0]));
eq(mono.numberOfChannels, 1, "toMono チャンネル数");
arrEq(mono.channels[0], [0.5, 0.5], "toMono 平均値");

/* ══════════ 8. フィルタ / エコー ══════════ */
console.log("8. フィルタ / エコー (onePoleCoef / filterRange / echoRange)");
ok(E.onePoleCoef(1000, 44100) > 0 && E.onePoleCoef(1000, 44100) < 1, "onePoleCoef は 0〜1");
ok(E.onePoleCoef(100, 44100) > E.onePoleCoef(5000, 44100),
   "onePoleCoef 低いカットオフほど係数が大きい");
let dc = clipOf(8000, new Array(64).fill(1));
near(E.filterRange(dc, 0, 64, "lowpass", 1000).channels[0][63], 1,
     "ローパスは直流をそのまま通す");
near(E.filterRange(dc, 0, 64, "highpass", 1000).channels[0][63], 0,
     "ハイパスは直流を落とす");
/* ナイキスト近傍の交番信号: ローパスで減衰する */
let alt = clipOf(8000, Array.from({ length: 64 }, (_, i) => (i % 2 ? -1 : 1)));
ok(Math.abs(E.filterRange(alt, 0, 64, "lowpass", 200).channels[0][63]) < 0.3,
   "ローパスは高周波を減衰させる");
ok(Math.abs(E.filterRange(alt, 0, 64, "highpass", 200).channels[0][63]) > 0.7,
   "ハイパスは高周波を通す");
let imp = clipOf(10, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
let ec = E.echoRange(imp, 0, 10, 0.2, 0.5);           /* 遅延 2 サンプル */
near(ec.channels[0][2], 0.5, "echoRange 1 回目の反射 0.5");
near(ec.channels[0][4], 0.25, "echoRange 2 回目の反射 0.25 (フィードバック)");
eq(ec.channels[0][1], 0, "echoRange 遅延外は無音のまま");
arrEq(E.echoRange(imp, 0, 10, 0.2, 0).channels[0], imp.channels[0], "echoRange 減衰 0 は無変更");

/* ══════════ 9. 解析 ══════════ */
console.log("9. 解析 (trimSilenceRange / findZeroCrossing)");
let tr = E.trimSilenceRange(clipOf(8000, [0, 0, 0.5, 0.5, 0, 0]), -50);
eq(tr.start, 2, "trimSilenceRange 開始");
eq(tr.end, 4, "trimSilenceRange 終了");
let trAll = E.trimSilenceRange(E.emptyClip(8000, 1, 10), -50);
eq(trAll.start + "/" + trAll.end, "0/10", "trimSilenceRange 全部無音なら全体を返す");
let trNone = E.trimSilenceRange(clipOf(8000, [1, 1, 1]), -50);
eq(trNone.start + "/" + trNone.end, "0/3", "trimSilenceRange 無音なしは全体");
let zc = clipOf(8000, [1, 0.5, -0.5, -1, -0.5, 0.5, 1]);
eq(E.findZeroCrossing(zc, 2, 8), 2, "findZeroCrossing その場が交差点");
eq(E.findZeroCrossing(zc, 3, 8), 2, "findZeroCrossing 近い交差点へ");
eq(E.findZeroCrossing(zc, 4, 8), 5, "findZeroCrossing 後方の交差点へ");
eq(E.findZeroCrossing(E.emptyClip(8000, 1, 0), 0, 8), 0, "findZeroCrossing 空 Clip");
eq(E.findZeroCrossing(clipOf(8000, [1, 1, 1]), 1, 1), 1,
   "findZeroCrossing 見つからなければ元の位置");

/* ══════════ 10. 描画補助 ══════════ */
console.log("10. 描画補助 (channelPeaks / niceTimeStep)");
let pk = E.channelPeaks(F32.from([0, 1, -1, 0.5]), 0, 4, 2);
eq(pk.length, 4, "channelPeaks 長さ = buckets × 2");
near(pk[0], 0, "channelPeaks bucket0 min");
near(pk[1], 1, "channelPeaks bucket0 max");
near(pk[2], -1, "channelPeaks bucket1 min");
near(pk[3], 0.5, "channelPeaks bucket1 max");
let pk2 = E.channelPeaks(F32.from([0.2, 0.4]), 0, 2, 4);
eq(pk2.length, 8, "channelPeaks 拡大時もバケット数どおり");
arrEq(E.channelPeaks(F32.from([1, 1]), 0, 0, 2), [0, 0, 0, 0], "channelPeaks 空範囲は 0");
eq(E.niceTimeStep(10, 8), 2, "niceTimeStep 10 秒 → 2 秒刻み");
eq(E.niceTimeStep(0.05, 8), 0.01, "niceTimeStep 50 ms → 10 ms 刻み");
eq(E.niceTimeStep(60, 8), 10, "niceTimeStep 60 秒 → 10 秒刻み");
eq(E.niceTimeStep(1e9, 8), 3600, "niceTimeStep 上限は 1 時間刻み");
ok(E.niceTimeStep(37, 8) >= 37 / 8, "niceTimeStep は目標間隔以上");

/* ══════════ 11. WAV 入出力 ══════════ */
console.log("11. WAV 入出力 (encodeWav / parseWav / estimateWavSize)");
const wavStr = (b, o, n) => Array.from(b.slice(o, o + n)).map(x => String.fromCharCode(x)).join("");
const u32 = (b, o) => b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] * 0x1000000);
const u16 = (b, o) => b[o] | (b[o + 1] << 8);

let wsrc = clipOf(44100, [0, 0.5, -0.5, 1, -1], [0.25, -0.25, 0, 0.75, -0.75]);
let w16 = E.encodeWav(wsrc, 16);
eq(wavStr(w16, 0, 4), "RIFF", "WAV ヘッダ RIFF");
eq(wavStr(w16, 8, 4), "WAVE", "WAV ヘッダ WAVE");
eq(wavStr(w16, 12, 4), "fmt ", "WAV fmt チャンク");
eq(wavStr(w16, 36, 4), "data", "WAV data チャンク");
eq(u16(w16, 20), 1, "WAV フォーマット = PCM(1)");
eq(u16(w16, 22), 2, "WAV チャンネル数 = 2");
eq(u32(w16, 24), 44100, "WAV サンプルレート = 44100");
eq(u32(w16, 28), 44100 * 4, "WAV バイト/秒 = rate × blockAlign");
eq(u16(w16, 32), 4, "WAV blockAlign = 4 (16bit ステレオ)");
eq(u16(w16, 34), 16, "WAV ビット深度 = 16");
eq(u32(w16, 40), 5 * 4, "WAV data サイズ");
eq(u32(w16, 4), 36 + 5 * 4, "WAV RIFF サイズ");
eq(w16.length, 44 + 5 * 4, "WAV 全長 = 44 + data");
eq(w16.length, E.estimateWavSize(wsrc, 16), "estimateWavSize(16bit) が実サイズと一致");
eq(E.encodeWav(wsrc, 24).length, E.estimateWavSize(wsrc, 24), "estimateWavSize(24bit)");
eq(E.encodeWav(wsrc, 32).length, E.estimateWavSize(wsrc, 32), "estimateWavSize(32bit)");

let back16 = E.parseWav(w16);
eq(back16.sampleRate, 44100, "parseWav サンプルレート");
eq(back16.numberOfChannels, 2, "parseWav チャンネル数");
eq(back16.length, 5, "parseWav サンプル数");
arrEq(back16.channels[0], [0, 0.5, -0.5, 1, -1], "parseWav 16bit L ラウンドトリップ", 1e-4);
arrEq(back16.channels[1], [0.25, -0.25, 0, 0.75, -0.75], "parseWav 16bit R ラウンドトリップ", 1e-4);

let back24 = E.parseWav(E.encodeWav(wsrc, 24));
arrEq(back24.channels[0], [0, 0.5, -0.5, 1, -1], "parseWav 24bit ラウンドトリップ", 1e-6);
eq(u16(E.encodeWav(wsrc, 24), 34), 24, "24bit ヘッダのビット深度");

let w32 = E.encodeWav(wsrc, 32);
eq(u16(w32, 20), 3, "32bit float はフォーマット 3 (IEEE float)");
let back32 = E.parseWav(w32);
arrEq(back32.channels[0], [0, 0.5, -0.5, 1, -1], "parseWav 32bit float は完全一致", 0);
arrEq(back32.channels[1], [0.25, -0.25, 0, 0.75, -0.75], "parseWav 32bit float R も完全一致", 0);

let monoW = E.parseWav(E.encodeWav(clipOf(16000, [0.5, -0.5]), 16));
eq(monoW.numberOfChannels, 1, "モノラル WAV ラウンドトリップ (ch)");
eq(monoW.sampleRate, 16000, "モノラル WAV ラウンドトリップ (rate)");
eq(u16(E.encodeWav(wsrc, 99), 34), 16, "未知のビット深度は 16bit にフォールバック");
arrEq(E.parseWav(E.encodeWav(clipOf(8000, [2, -2]), 32)).channels[0], [1, -1],
      "書き出し時に -1〜1 へクリップされる", 0);
ok((() => { try { E.parseWav(new U8([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])); return false; }
            catch (e) { return true; } })(), "parseWav 非 WAV は例外");

/* 編集 → 書き出しの通し確認 */
let pipeline = E.encodeWav(
  E.normalizeRange(
    E.fadeRange(E.deleteRange(clipOf(8000, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]), 0, 2),
                0, 4, "in", "linear"),
    0, 4, -6.0206), 16);
let pipeBack = E.parseWav(pipeline);
eq(pipeBack.length, 4, "通し処理: 削除で 6→4 サンプル");
near(E.peakOf(pipeBack, 0, 4), 0.5, "通し処理: ノーマライズで -6 dB (ピーク 0.5)", 1e-3);
eq(pipeBack.channels[0][0], 0, "通し処理: フェードイン先頭は無音");

/* ══════════ 結果 ══════════ */
console.log("\n──────────────────────────────");
console.log("  成功 " + pass + " / 失敗 " + fail);
console.log("──────────────────────────────");
if (fail) { console.error("エンジンテスト失敗"); process.exit(1); }
console.log("Bada AudioForge エンジンテスト: すべて成功 ✅");
