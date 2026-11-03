/*
 * bci.js — BadaGPT電信「思考だけで (脳波 BCI)」
 *
 * 声を出さず、絵も描かず、文字も打たずに、**自分の頭に付けた脳波計 (EEG)** の
 * 信号だけで BadaGPT に選択を伝える、ブレイン・コンピュータ・インタフェース (BCI)。
 *
 *   - 集中度 (attention): β 帯 (13–30 Hz) / (α 8–12 Hz + θ 4–7 Hz) のバンドパワー比。
 *     選択肢を順に提示 (スキャン) し、ある選択肢の間に集中度がしきい値を超えて
 *     一定時間続いたら、それを選ぶ (dwell 選択)。
 *   - SSVEP: 画面の選択肢を異なる周波数 (60 Hz の約数: 7.5 / 8.57 / 10 / 12 / 15 Hz)
 *     で点滅させ、見つめている選択肢の周波数が脳波に現れる (視覚誘発電位) ことを
 *     Goertzel で検出する。BCI スペラーで確立された方式。
 *   - 機器: Muse (Web Bluetooth)・OpenBCI Cyton (Web Serial) のパケットを復号する。
 *     機器が無いときは「デモ (合成信号)」で仕組みを動かす (明示的にシミュレーション)。
 *
 * 正直な範囲 (重要):
 *   - 脳波計が読むのは「集中している / リラックスしている / どの点滅を見ているか」
 *     という **脳の状態** であり、思考の内容や言語は読み取れない。利用者は提示された
 *     選択肢から **注意を向けることで選ぶ**。これが「思考だけで入力する」の、現在の
 *     技術で正直に成立する形である。
 *   - 他人の脳波を読むものではなく、利用者本人が自分の頭に付けた機器で、同意の上で使う。
 *   - デモはシミュレーションであり、本人の脳波ではない。
 */
"use strict";

/* ───────────── DSP ───────────── */

/* 周波数 f のパワー (Goertzel)。samples は µV の配列。 */
function goertzelPower(samples, fs, f) {
  var n = samples.length, w = 2 * Math.PI * f / fs, c = 2 * Math.cos(w), s1 = 0, s2 = 0;
  for (var i = 0; i < n; i++) { var s0 = samples[i] + c * s1 - s2; s2 = s1; s1 = s0; }
  return (s1 * s1 + s2 * s2 - c * s1 * s2) / (n * n);
}

function demean(samples) {
  var m = 0; for (var i = 0; i < samples.length; i++) m += samples[i]; m /= (samples.length || 1);
  var out = new Array(samples.length); for (var j = 0; j < samples.length; j++) out[j] = samples[j] - m;
  return out;
}

/* θ / α / β のバンドパワー (1 Hz 刻みの Goertzel の和)。1 秒以上の窓が必要。 */
function bandPowers(samples, fs) {
  if (!samples || samples.length < fs) return { theta: NaN, alpha: NaN, beta: NaN };
  var x = demean(samples);
  function band(lo, hi) { var p = 0; for (var f = lo; f <= hi; f++) p += goertzelPower(x, fs, f); return p; }
  return { theta: band(4, 7), alpha: band(8, 12), beta: band(13, 30) };
}

/* 集中度 0..1: β / (α + θ) を 0..1 に圧縮 (比 1 で 0.5) */
function attentionIndex(bp) {
  if (!isFinite(bp.beta) || !isFinite(bp.alpha) || !isFinite(bp.theta)) return NaN;
  var r = bp.beta / (bp.alpha + bp.theta + 1e-12);
  return r / (1 + r);
}

/* SSVEP: 候補周波数のうち、基本波のパワーがスペクトル全体 (5–30 Hz) の中央値
 * (雑音床) に比べて最も高いものを返す。中央値は α のピーク 1 本に引きずられない。
 * 第 2 高調波は候補どうしで重なる (6→12, 7.5→15) ため使わない。{ freq, snr, scores } */
function ssvepDetect(samples, fs, freqs) {
  if (!samples || samples.length < fs * 2) return { freq: NaN, snr: 0, scores: [] };
  var x = demean(samples), floorPows = [];
  for (var f0 = 5; f0 <= 30; f0 += 0.25) {
    var near = freqs.some(function (f) { return Math.abs(f0 - f) < 0.6; });
    if (!near) floorPows.push(goertzelPower(x, fs, f0));
  }
  floorPows.sort(function (a, b) { return a - b; });
  var noise = floorPows.length ? floorPows[floorPows.length >> 1] : 1e-12;
  var scores = freqs.map(function (f) { return { freq: f, snr: goertzelPower(x, fs, f) / (noise + 1e-12) }; });
  var best = scores.reduce(function (a, b) { return b.snr > a.snr ? b : a; }, { freq: NaN, snr: 0 });
  var second = scores.filter(function (sc) { return sc.freq !== best.freq; }).reduce(function (a, b) { return b.snr > a.snr ? b : a; }, { snr: 0 });
  /* 雑音床の 12 倍以上 (背景の漏れは最大 10 倍程度、本物の誘発電位は 100 倍以上)、
   * かつ次点の 2 倍以上ではっきり勝っているときだけ採用 */
  var okHit = best.snr >= 12 && best.snr >= 2 * second.snr;
  return { freq: okHit ? best.freq : NaN, snr: best.snr, scores: scores };
}

/* 60 Hz 描画で正確に出せる点滅周波数 (60/n)。α 帯 (8–12 Hz) の 10 Hz は背景律動と
 * 混同するため外し、β 帯の 20 Hz も集中時の β と混同するため外す。
 * 段階ごとの選択肢は最大 5 個 (それぞれ別の周波数)。 */
var SSVEP_FREQS = [6, 7.5, 8.57, 12, 15];

/* ───────────── 機器のパケット復号 ───────────── */

/* Muse (2 / S): EEG 特性 (273e0003〜0006) の 20 バイト通知。
 * [0..1] パケット番号 (BE)、[2..19] 12 ビット × 12 サンプル。0x800 を中心に 0.48828125 µV/bit。 */
var MUSE = {
  SERVICE: "0000fe8d-0000-1000-8000-00805f9b34fb",
  CONTROL: "273e0001-4c4d-454d-96be-f03bac821358",
  EEG: ["273e0003-4c4d-454d-96be-f03bac821358", "273e0004-4c4d-454d-96be-f03bac821358", "273e0005-4c4d-454d-96be-f03bac821358", "273e0006-4c4d-454d-96be-f03bac821358"],
  CHANNELS: ["TP9", "AF7", "AF8", "TP10"],
  FS: 256
};
function museDecodeEEG(bytes) {
  if (!bytes || bytes.length < 20) return { index: -1, samples: [] };
  var index = (bytes[0] << 8) | bytes[1], out = [];
  for (var i = 0; i < 12; i++) {
    var bit = 16 + i * 12, byteI = bit >> 3, raw;
    if (bit % 8 === 0) raw = (bytes[byteI] << 4) | (bytes[byteI + 1] >> 4);
    else raw = ((bytes[byteI] & 0x0F) << 8) | bytes[byteI + 1];
    out.push((raw - 0x800) * 0.48828125);
  }
  return { index: index, samples: out };
}
/* Muse へ送る制御コマンド (長さ + ASCII + '\n') */
function museCommand(str) {
  var s = str + "\n", out = new Uint8Array(s.length + 1); out[0] = s.length;
  for (var i = 0; i < s.length; i++) out[i + 1] = s.charCodeAt(i);
  return out;
}

/* OpenBCI Cyton: 33 バイト。0xA0, サンプル番号, 8ch × 24bit (2 の補数, BE), 6 バイト補助, 0xC0..0xCF。
 * 1 LSB = 4.5 V / ゲイン 24 / (2^23 - 1) → µV */
var OPENBCI = { FS: 250, SCALE_UV: 4.5 / 24 / (Math.pow(2, 23) - 1) * 1e6 };
function openbciDecode(bytes) {
  var out = [], i = 0;
  while (i + 33 <= bytes.length) {
    if (bytes[i] !== 0xA0 || (bytes[i + 32] & 0xF0) !== 0xC0) { i++; continue; }
    var ch = [];
    for (var c = 0; c < 8; c++) {
      var o = i + 2 + c * 3, v = (bytes[o] << 16) | (bytes[o + 1] << 8) | bytes[o + 2];
      if (v & 0x800000) v -= 0x1000000;
      ch.push(v * OPENBCI.SCALE_UV);
    }
    out.push({ sample: bytes[i + 1], channels: ch });
    i += 33;
  }
  return out;
}

/* ───────────── 合成信号 (デモ・テスト用) ───────────── */

/* fs Hz・seconds 秒。実際の脳波に近づけて、α は 9.6–10.4 Hz に広がり、β は 14–26 Hz の
 * 広帯域、θ は 5–6.5 Hz。attention 区間では β を強め α を弱める。ssvepHz を与えると
 * その周波数の成分 (視覚誘発電位) を乗せる。 */
function syntheticEEG(fs, seconds, opts) {
  opts = opts || {};
  var n = Math.round(fs * seconds), out = new Array(n), rng = mulberry32(opts.seed || 7);
  var att = opts.attention || [], t0 = opts.t0 || 0; /* t0: 連続生成のための開始時刻 (位相をつなぐ) */
  var alphaF = [9.6, 10, 10.4], betaF = [14, 17, 20, 23, 26], thetaF = [5, 6.5];
  for (var i = 0; i < n; i++) {
    var t = t0 + i / fs, focus = att.some(function (r) { return t >= r[0] && t < r[1]; }), v = 0, k;
    for (k = 0; k < alphaF.length; k++) v += (focus ? 2.5 : 8) * Math.sin(2 * Math.PI * alphaF[k] * t + k);
    for (k = 0; k < betaF.length; k++) v += (focus ? 6 : 1.5) * Math.sin(2 * Math.PI * betaF[k] * t + k * 1.7);
    for (k = 0; k < thetaF.length; k++) v += 3 * Math.sin(2 * Math.PI * thetaF[k] * t + k * 2.1);
    v += (rng() - 0.5) * 6;
    if (opts.ssvepHz) v += 9 * Math.sin(2 * Math.PI * opts.ssvepHz * t);
    out[i] = v;
  }
  return out;
}

/* ───────────── スキャン選択 (状態機械) ───────────── */

/* 選択肢を順に提示し、集中度が thr 以上で dwellMs 続いたら現在の選択肢を選ぶ。
 * SSVEP モードでは、検出された周波数の選択肢を selectMs 続いたら選ぶ。 */
function Scanner(options, cfg) {
  cfg = cfg || {};
  this.options = options.slice(); this.i = 0;
  this.stepMs = cfg.stepMs || 3000; this.thr = cfg.thr != null ? cfg.thr : 0.6; this.dwellMs = cfg.dwellMs || 1200;
  this.lastStep = null; this.focusSince = null; this.selected = null; this.cooldownUntil = 0;
}
Scanner.prototype.current = function () { return this.options[this.i]; };
/* now: ms, attention: 0..1 (NaN 可) → { current, selected (このティックで確定した選択肢 or null), progress 0..1 } */
Scanner.prototype.tick = function (now, attention) {
  if (this.lastStep == null) this.lastStep = now;
  var selected = null;
  if (now < this.cooldownUntil) { attention = 0; }
  if (isFinite(attention) && attention >= this.thr) {
    if (this.focusSince == null) this.focusSince = now;
    if (now - this.focusSince >= this.dwellMs) {
      selected = this.current(); this.selected = selected; this.focusSince = null;
      this.cooldownUntil = now + this.stepMs; this.lastStep = now;
      this.i = (this.i + 1) % this.options.length;
      return { current: this.current(), selected: selected, progress: 0 };
    }
  } else this.focusSince = null;
  if (now - this.lastStep >= this.stepMs) { this.lastStep = now; this.i = (this.i + 1) % this.options.length; this.focusSince = null; }
  var progress = this.focusSince == null ? 0 : Math.min(1, (now - this.focusSince) / this.dwellMs);
  return { current: this.current(), selected: selected, progress: progress };
};

/* ───────────── BadaGPT の選択肢 (段階ごとに非言語アトムを選ぶ) ─────────────
 * 各段で 1 つ選ぶと次の段へ。「次へ」で選ばずに進める。最後の「完了」で言葉にする。 */
var BCI_STAGES = [
  { key: "domain", label: "何のアプリ？", options: ["records", "task", "note", "money", "time"] },
  { key: "object", label: "何を扱う？ (任意)", options: ["book", "person", "habit", "random", "_skip"] },
  { key: "action", label: "どんな機能？ (任意)", options: ["find", "sort", "graph", "export", "_skip"] },
  { key: "tone", label: "どんな調子・色？ (任意)", options: ["calm", "urgent", "cool", "warm", "_skip"] },
  { key: "scale", label: "文章の分量", options: ["small", "medium", "large", "book_vol"] },
  { key: "platform", label: "どこで使う？", options: ["android", "windows", "linux", "_all"] }
];
var BCI_LABEL = { _skip: "次へ (選ばない)", _all: "すべて" };
function bciOptionLabel(id) {
  if (BCI_LABEL[id]) return BCI_LABEL[id];
  var a = ATOM_BY_ID[id]; if (!a) return id;
  var m = a.tags.mod, name = m ? (MOD_PHRASE[m] || m).replace(/^を/, "") : "";
  if (a.tags.entity) name = a.tags.entity;
  if (a.tags.feat) name = { search: "検索", sort: "並べ替え", chart: "グラフ", export: "CSV 書き出し", print: "印刷" }[a.tags.feat] || a.tags.feat;
  if (a.cat === "tone") name = { calm: "静か", joy: "軽やか", urgent: "勢い", cool: "暗い青", warm: "明るい橙", vivid: "紫" }[id] || id;
  if (a.cat === "scale") name = { small: "素描", medium: "短編", large: "中編", book_vol: "本一冊" }[id];
  if (a.cat === "platform") name = { android: "スマホ", windows: "Windows", linux: "Linux" }[id];
  return a.g + " " + name;
}
/* 段ごとの選択 → 非言語アトム列 */
function bciSelectionsToAtoms(sel) {
  var atoms = [];
  BCI_STAGES.forEach(function (st) {
    var v = sel[st.key]; if (!v || v === "_skip") return;
    if (v === "_all") { atoms.push("android", "windows", "linux"); return; }
    atoms.push(v);
  });
  return atoms;
}
