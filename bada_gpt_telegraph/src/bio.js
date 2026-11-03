/*
 * bio.js — BadaGPT電信「体のサイン (感覚入力・バイオフィードバック)」
 *
 * 利用者が **自分の** 指先をカメラに当てて得る脈波 (PPG) から心拍数と心拍変動
 * (RMSSD) を、マイクの音量包絡から呼吸数を推定し、落ち着き指数にまとめる。
 * 結果はサイレント・トークの latent に **気分のヒント (tone アトム) としてだけ**
 * 加わる。BadaGPT改 (bada_gpt_kai) の信号処理を移植したもの。
 *
 * 正直な範囲 (重要):
 *   - 心拍・呼吸は「体の状態」であり、思考の内容は読み取れない。本モジュールが
 *     アプリの中身 (モジュール・項目・対象) を決めることはなく、調子 (静か /
 *     軽やか / 勢い) だけを latent に添える。
 *   - 赤外線カメラや温度計で他人の思考を読む機能ではない。通常のカメラで、
 *     利用者本人が自分の指先を当てて測る (同意が前提の自己計測)。
 *   - 皮膚温・赤外線から言語や思考を推定することは科学的にできない。
 */
"use strict";

function movingAverage(xs, w) {
  var out = new Array(xs.length), s = 0, q = [];
  for (var i = 0; i < xs.length; i++) {
    q.push(xs[i]); s += xs[i];
    if (q.length > w) s -= q.shift();
    out[i] = s / q.length;
  }
  return out;
}

function median(xs) {
  if (!xs.length) return NaN;
  var a = xs.slice().sort(function (p, q) { return p - q; }), m = a.length >> 1;
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

/* samples: [{t: 秒, v: 輝度}] (指先をカメラに当てた PPG) → { bpm, rmssd, peaks } */
function ppgAnalyze(samples) {
  if (!samples || samples.length < 30) return { bpm: NaN, rmssd: NaN, peaks: [] };
  var dur = samples[samples.length - 1].t - samples[0].t;
  if (dur < 4) return { bpm: NaN, rmssd: NaN, peaks: [] };
  var fs = (samples.length - 1) / dur;
  /* 血液は光を吸収するので輝度を反転し、ゆっくりした変動を除いて平滑化 */
  var v = samples.map(function (s) { return -s.v; });
  var base = movingAverage(v, Math.max(3, Math.round(fs * 1.0)));
  var d = v.map(function (x, i) { return x - base[i]; });
  var sm = movingAverage(d, Math.max(1, Math.round(fs * 0.12)));
  var sd = Math.sqrt(sm.reduce(function (a, x) { return a + x * x; }, 0) / sm.length) || 1;
  var minGap = 0.33, peaks = [];
  for (var i = 2; i < sm.length - 2; i++) {
    if (sm[i] > 0.3 * sd && sm[i] >= sm[i - 1] && sm[i] >= sm[i - 2] && sm[i] > sm[i + 1] && sm[i] >= sm[i + 2]) {
      var t = samples[i].t;
      if (peaks.length && t - peaks[peaks.length - 1].t < minGap) {
        if (sm[i] > peaks[peaks.length - 1].a) peaks[peaks.length - 1] = { t: t, a: sm[i] };
      } else peaks.push({ t: t, a: sm[i] });
    }
  }
  var ibis = [];
  for (var k = 1; k < peaks.length; k++) {
    var ibi = peaks[k].t - peaks[k - 1].t;
    if (ibi >= 0.33 && ibi <= 1.5) ibis.push(ibi);
  }
  if (ibis.length < 3) return { bpm: NaN, rmssd: NaN, peaks: peaks };
  var med = median(ibis);
  /* 中央値から大きく外れた拍間隔 (誤検出) を除外 */
  var good = ibis.filter(function (x) { return Math.abs(x - med) < 0.25 * med; });
  /* 平均を使う (中央値だとフレーム周期 1/30 秒に量子化された値に張り付く) */
  var bpm = 60 / (good.reduce(function (a, x) { return a + x; }, 0) / good.length);
  var diffs = [];
  for (var j = 1; j < good.length; j++) diffs.push(Math.pow((good[j] - good[j - 1]) * 1000, 2));
  var rmssd = diffs.length ? Math.sqrt(diffs.reduce(function (a, x) { return a + x; }, 0) / diffs.length) : NaN;
  return { bpm: bpm, rmssd: rmssd, peaks: peaks };
}

/* samples: [{t: 秒, v: マイク音量 (RMS)}] → 呼吸数 (回/分)。
 * 包絡を 0.6 秒で平滑化し 8 秒の基線を引いて、ヒステリシス付きの上向き交差を数える。 */
function breathAnalyze(samples) {
  if (!samples || samples.length < 30) return NaN;
  var dur = samples[samples.length - 1].t - samples[0].t;
  if (dur < 12) return NaN;
  var fs = (samples.length - 1) / dur;
  var v = movingAverage(samples.map(function (s) { return s.v; }), Math.max(1, Math.round(fs * 0.6)));
  var base = movingAverage(v, Math.max(3, Math.round(fs * 8)));
  var d = v.map(function (x, i) { return x - base[i]; });
  var sd = Math.sqrt(d.reduce(function (a, x) { return a + x * x; }, 0) / d.length);
  if (!(sd > 1e-6)) return NaN;
  var hi = 0.3 * sd, lo = -0.3 * sd, state = d[0] > 0 ? 1 : -1, ups = [];
  for (var i = 1; i < d.length; i++) {
    if (state < 0 && d[i] > hi) { state = 1; ups.push(samples[i].t); }
    else if (state > 0 && d[i] < lo) state = -1;
  }
  if (ups.length < 2) return NaN;
  var span = ups[ups.length - 1] - ups[0];
  var rate = (ups.length - 1) / span * 60;
  return rate >= 2 && rate <= 40 ? rate : NaN;
}

function clamp01(x) { return Math.max(0, Math.min(1, x)); }

/* 落ち着き指数 0..100: 心拍変動 (RMSSD) が大きく、呼吸が毎分 6 回 (共鳴呼吸) に近いほど高い */
function calmIndex(rmssd, breath) {
  var parts = [];
  if (isFinite(rmssd)) parts.push(clamp01(rmssd / 80));
  if (isFinite(breath)) parts.push(clamp01(1 - Math.abs(breath - 6) / 12));
  if (!parts.length) return NaN;
  return 100 * parts.reduce(function (a, x) { return a + x; }, 0) / parts.length;
}

/* 体のサイン → 気分のヒント (tone アトムのみ) + 読み取り内容。
 * モジュール・対象・項目は決して返さない (体の信号はアプリの中身を決めない)。 */
function bioToAtoms(bio) {
  bio = bio || {};
  var atoms = [], readout = [];
  var bpm = bio.bpm, rmssd = bio.rmssd, breath = bio.breath;
  var calm = calmIndex(rmssd, breath);
  if (isFinite(bpm)) readout.push({ label: "心拍数", value: Math.round(bpm) + " bpm", meant: bpm > 100 ? "速い (勢い)" : bpm < 60 ? "ゆっくり (静か)" : "ふつう" });
  if (isFinite(rmssd)) readout.push({ label: "心拍変動 RMSSD", value: Math.round(rmssd) + " ms", meant: rmssd >= 50 ? "余裕がある" : "緊張ぎみ" });
  if (isFinite(breath)) readout.push({ label: "呼吸", value: breath.toFixed(1) + " 回/分", meant: breath <= 8 ? "深くゆっくり" : breath >= 18 ? "浅く速い" : "ふつう" });
  if (isFinite(calm)) readout.push({ label: "落ち着き指数", value: Math.round(calm) + " / 100", meant: calm >= 65 ? "静かな調子 → 落ち着いた構成" : calm < 35 ? "勢いのある調子 → 音で知らせる" : "軽やかな調子" });
  if (!readout.length) return { atoms: [], readout: [], calm: NaN };
  if (isFinite(calm) ? calm >= 65 : (isFinite(bpm) && bpm < 60)) atoms.push("calm");
  else if ((isFinite(calm) && calm < 35) || (isFinite(bpm) && bpm > 100)) atoms.push("urgent");
  else atoms.push("joy");
  readout.push({ label: "添える気分", value: atoms.join(","), meant: "調子のヒントとしてだけ latent に加えます (アプリの中身は決めません)" });
  return { atoms: atoms, readout: readout, calm: calm };
}
