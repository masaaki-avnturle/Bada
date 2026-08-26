/*
 * sound.js — 電子音エンジン (Web Audio API / 音声ファイル不要)
 * Ω-Whispered — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * 検査中の各イベントで短い電子音を鳴らす。すべて発振器 (OscillatorNode) から
 * その場で合成するため、音声ファイルも外部通信も不要。
 *
 *   起動シーケンス / 出題 / 選択 / 正答 / 誤答 / 瞬読の注視点・提示・マスク /
 *   フェーズ切替 / 判定表示
 *
 * ブラウザの自動再生制限があるため、AudioContext は「最初のユーザー操作」で
 * 初期化する (Sound.unlock() を検査開始ボタンなどから呼ぶ)。
 */
(function (root) {
  "use strict";

  var ctx = null, master = null, enabled = true, volume = 0.5, count = 0;

  function unlock() {
    if (ctx) { if (ctx.state === "suspended") ctx.resume(); return true; }
    var AC = root.AudioContext || root.webkitAudioContext;
    if (!AC) return false;
    try {
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = volume;
      master.connect(ctx.destination);
      if (ctx.state === "suspended") ctx.resume();
      return true;
    } catch (e) { ctx = null; return false; }
  }

  /* 単発のトーン: 周波数 f(Hz)、開始 t0(秒後)、長さ dur(秒)、波形、音量 */
  function tone(f, t0, dur, type, gain, sweepTo) {
    if (!ctx) return;
    var t = ctx.currentTime + t0;
    var osc = ctx.createOscillator(), g = ctx.createGain();
    osc.type = type || "square";
    osc.frequency.setValueAtTime(f, t);
    if (sweepTo) osc.frequency.exponentialRampToValueAtTime(Math.max(20, sweepTo), t + dur);
    /* クリックノイズを避けるための短いアタック/リリース */
    var peak = (gain === undefined ? 0.22 : gain);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + Math.min(0.012, dur * 0.3));
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(g); g.connect(master);
    osc.start(t); osc.stop(t + dur + 0.02);
    count++;
  }

  /* ノイズ的な短打(マスク音などに使う) */
  function noise(t0, dur, gain) {
    if (!ctx) return;
    var t = ctx.currentTime + t0;
    var n = Math.max(1, Math.floor(ctx.sampleRate * dur));
    var buf = ctx.createBuffer(1, n, ctx.sampleRate), d = buf.getChannelData(0);
    for (var i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
    var src = ctx.createBufferSource(), g = ctx.createGain();
    src.buffer = buf;
    g.gain.value = (gain === undefined ? 0.12 : gain);
    src.connect(g); g.connect(master);
    src.start(t);
    count++;
  }

  /* イベント名 → 音のパターン */
  var PATTERNS = {
    /* 起動: 上昇アルペジオ(システム始動らしい電子音) */
    boot: function () { [523, 659, 784, 1047].forEach(function (f, i) { tone(f, i * 0.07, 0.09, "square", 0.16); }); },
    /* 出題: 短い一打 */
    question: function () { tone(880, 0, 0.05, "square", 0.14); },
    /* 選択(クリック) */
    select: function () { tone(1200, 0, 0.03, "square", 0.10); },
    /* 正答: 三度上がる二音 */
    correct: function () { tone(988, 0, 0.07, "square", 0.18); tone(1319, 0.07, 0.12, "square", 0.18); },
    /* 誤答: 低く下がるブザー */
    wrong: function () { tone(220, 0, 0.16, "sawtooth", 0.16, 130); },
    /* フェーズ切替: 二音の合図 */
    phase: function () { tone(660, 0, 0.08, "triangle", 0.16); tone(990, 0.09, 0.12, "triangle", 0.16); },
    /* 瞬読 注視点: 低いカウント音 */
    fix: function () { tone(440, 0, 0.05, "sine", 0.12); },
    /* 瞬読 提示開始: 鋭い高音 */
    flash: function () { tone(1568, 0, 0.04, "square", 0.20); },
    /* 瞬読 マスク: ノイズ短打 */
    mask: function () { noise(0, 0.06, 0.10); },
    /* 判定表示: 下降から上昇へ(結果の確定) */
    result: function () {
      [784, 659, 523].forEach(function (f, i) { tone(f, i * 0.08, 0.09, "triangle", 0.15); });
      tone(1047, 0.26, 0.22, "square", 0.18);
    },
    /* 警告(閾値到達など) */
    alert: function () { tone(1760, 0, 0.05, "square", 0.16); tone(1760, 0.09, 0.05, "square", 0.16); }
  };

  function play(name) {
    if (!enabled) return false;
    if (!ctx && !unlock()) return false;
    var p = PATTERNS[name];
    if (!p) return false;
    try { p(); return true; } catch (e) { return false; }
  }

  var API = {
    unlock: unlock,
    play: play,
    names: function () { return Object.keys(PATTERNS); },
    setEnabled: function (v) {
      enabled = !!v;
      if (enabled) unlock();
    },
    isEnabled: function () { return enabled; },
    setVolume: function (v) {
      volume = Math.max(0, Math.min(1, v));
      if (master) master.gain.value = volume;
    },
    getVolume: function () { return volume; },
    /* 自動検証用: これまでに生成した音源ノードの数 */
    played: function () { return count; },
    available: function () { return !!(root.AudioContext || root.webkitAudioContext); }
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.OmegaSound = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
