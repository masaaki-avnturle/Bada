/*
 * countdown.js — Bada 映画カウントダウンエディタのエンジン + レンダラ
 *
 * 映画冒頭のフィルムリーダー (SMPTE ユニバーサル・リーダー) を生成する。
 *   ・大きな数字 (start → end、既定 8→2)
 *   ・1 秒ごとに 1 回転する掃引ハンド (sweep)
 *   ・全画面の十字 (crosshair) と外周リング
 *   ・フィルムグレイン / ビネット / レターボックス / 整数切替フラッシュ
 *   ・指定の数字でビープ (1 回 or 各整数)
 *
 * 純粋ロジック (normalize / sequence / duration / stateAtTime / beepTimes) は
 * canvas に依存せず Node からも require でき、単体テストできる。
 * render(ctx, w, h, state, cfg) はブラウザ/Electron の Canvas2D 専用。
 */
(function (global) {
  "use strict";

  var THEMES = {
    academy: { bg: "#0a0a0a", ink: "#ededed", accent: "#cfcfcf" },
    amber:   { bg: "#0a0600", ink: "#ffcf6a", accent: "#ff8c1a" },
    blue:    { bg: "#00060f", ink: "#a9d4ff", accent: "#3aa0ff" },
    green:   { bg: "#000700", ink: "#9fffbf", accent: "#3cff8e" },
    mono:    { bg: "#000000", ink: "#ffffff", accent: "#bdbdbd" }
  };

  var DEFAULTS = {
    start: 8, end: 2, stepSeconds: 1, fps: 24,
    title: "BADA PICTURES", subtitle: "",
    theme: "academy", colors: null,
    beep: true, beepAt: 2, beepEach: false,
    crosshair: true, sweep: true, grain: true, vignette: true,
    letterbox: false, flash: true, holdAfter: 0.5
  };

  function normalize(cfg) {
    cfg = cfg || {};
    var c = {};
    for (var k in DEFAULTS) c[k] = (cfg[k] != null) ? cfg[k] : DEFAULTS[k];
    c.start = clampInt(c.start, 1, 99);
    c.end = clampInt(c.end, 1, 99);
    if (c.end > c.start) c.end = c.start;
    c.stepSeconds = clampNum(c.stepSeconds, 0.2, 10);
    c.fps = clampInt(c.fps, 1, 60);
    c.beepAt = clampInt(c.beepAt, c.end, c.start);
    c.holdAfter = clampNum(c.holdAfter, 0, 10);
    var th = THEMES[c.theme] || THEMES.academy;
    c.colors = {
      bg: (c.colors && c.colors.bg) || th.bg,
      ink: (c.colors && c.colors.ink) || th.ink,
      accent: (c.colors && c.colors.accent) || th.accent
    };
    return c;
  }
  function clampInt(v, lo, hi) { v = Math.round(+v || 0); return v < lo ? lo : v > hi ? hi : v; }
  function clampNum(v, lo, hi) { v = +v; if (!isFinite(v)) v = lo; return v < lo ? lo : v > hi ? hi : v; }

  function sequence(cfg) {
    cfg = normalize(cfg);
    var a = [];
    for (var n = cfg.start; n >= cfg.end; n--) a.push(n);
    return a;
  }
  function runDuration(cfg) { cfg = normalize(cfg); return sequence(cfg).length * cfg.stepSeconds; }
  function duration(cfg) { cfg = normalize(cfg); return runDuration(cfg) + cfg.holdAfter; }
  function totalFrames(cfg) { cfg = normalize(cfg); return Math.round(duration(cfg) * cfg.fps); }

  /* 時刻 t 秒の状態。 phase: "run" | "done" (t<0 は run の 0 と同じ扱い) */
  function stateAtTime(cfg, t) {
    cfg = normalize(cfg);
    var step = cfg.stepSeconds, seq = sequence(cfg), count = seq.length;
    var run = count * step;
    if (t < 0) t = 0;
    if (t >= run) {
      return { phase: "done", index: count, number: cfg.end, p: 1, angle: 0, flash: 0, finished: true };
    }
    var index = Math.floor(t / step);
    if (index > count - 1) index = count - 1;
    var within = t - index * step;
    var p = within / step;                         /* 0..1 */
    var frameDur = 1 / cfg.fps;
    var flash = (cfg.flash && within < frameDur * 2) ? (1 - within / (frameDur * 2)) : 0;
    return {
      phase: "run", index: index, number: seq[index], p: p,
      angle: p * 2 * Math.PI, flash: flash, finished: false
    };
  }

  function beepTimes(cfg) {
    cfg = normalize(cfg);
    if (!cfg.beep) return [];
    var seq = sequence(cfg), step = cfg.stepSeconds, out = [];
    if (cfg.beepEach) { for (var i = 0; i < seq.length; i++) out.push(i * step); }
    else { var k = seq.indexOf(cfg.beepAt); if (k >= 0) out.push(k * step); }
    return out;
  }

  /* ── Canvas2D レンダラ (ブラウザ/Electron 専用) ── */
  function render(ctx, w, h, state, cfg) {
    cfg = normalize(cfg);
    var col = cfg.colors;
    ctx.save();
    ctx.fillStyle = col.bg; ctx.fillRect(0, 0, w, h);

    var barH = cfg.letterbox ? Math.round(h * 0.12) : 0;
    var top = barH, bot = h - barH, ah = bot - top;
    var cx = w / 2, cy = top + ah / 2;
    var R = Math.min(w, ah) * 0.42;

    if (state.phase !== "done") {
      /* 外周リング */
      ctx.strokeStyle = col.ink; ctx.lineWidth = Math.max(2, R * 0.012);
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, cy, R * 0.72, 0, Math.PI * 2);
      ctx.globalAlpha = 0.5; ctx.stroke(); ctx.globalAlpha = 1;

      /* 十字 (全画面) */
      if (cfg.crosshair) {
        ctx.strokeStyle = col.ink; ctx.globalAlpha = 0.33; ctx.lineWidth = Math.max(1, R * 0.006);
        ctx.beginPath(); ctx.moveTo(cx, top); ctx.lineTo(cx, bot);
        ctx.moveTo(0, cy); ctx.lineTo(w, cy); ctx.stroke();
        ctx.globalAlpha = 1;
      }

      /* 掃引ハンド (上=-90° から時計回り) */
      if (cfg.sweep) {
        var a0 = -Math.PI / 2, a1 = a0 + state.angle;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, R, a0, a1); ctx.closePath();
        ctx.fillStyle = col.accent; ctx.globalAlpha = 0.18; ctx.fill(); ctx.globalAlpha = 1;
        ctx.strokeStyle = col.accent; ctx.lineWidth = Math.max(2, R * 0.016);
        ctx.beginPath(); ctx.moveTo(cx, cy);
        ctx.lineTo(cx + R * Math.cos(a1), cy + R * Math.sin(a1)); ctx.stroke();
      }

      /* 大きな数字 */
      ctx.fillStyle = col.ink;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.font = "bold " + Math.round(R * 1.15) + "px 'Arial Black',Impact,'Noto Sans JP',sans-serif";
      ctx.fillText(String(state.number), cx, cy + R * 0.04);

      /* タイトル / サブタイトル */
      if (cfg.title) {
        ctx.font = Math.round(R * 0.14) + "px 'Arial',sans-serif";
        ctx.globalAlpha = 0.85; ctx.fillText(cfg.title, cx, top + ah * 0.08); ctx.globalAlpha = 1;
      }
      if (cfg.subtitle) {
        ctx.font = Math.round(R * 0.1) + "px 'Arial',sans-serif";
        ctx.globalAlpha = 0.7; ctx.fillText(cfg.subtitle, cx, bot - ah * 0.07); ctx.globalAlpha = 1;
      }
    }

    /* グレイン */
    if (cfg.grain) {
      ctx.globalAlpha = 0.07; ctx.fillStyle = "#ffffff";
      for (var i = 0; i < 700; i++) {
        ctx.fillRect((Math.random() * w) | 0, (top + Math.random() * ah) | 0, 1, 1);
      }
      ctx.globalAlpha = 1;
    }
    /* ビネット */
    if (cfg.vignette && ctx.createRadialGradient) {
      var g = ctx.createRadialGradient(cx, cy, R * 0.5, cx, cy, Math.max(w, h) * 0.75);
      g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(0,0,0,0.65)");
      ctx.fillStyle = g; ctx.fillRect(0, top, w, ah);
    }
    /* レターボックス帯 */
    if (barH) { ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, barH); ctx.fillRect(0, h - barH, w, barH); }
    /* 整数フラッシュ */
    if (state.flash > 0) { ctx.globalAlpha = state.flash * 0.5; ctx.fillStyle = "#fff"; ctx.fillRect(0, top, w, ah); ctx.globalAlpha = 1; }

    ctx.restore();
  }

  var BadaCountdown = {
    THEMES: THEMES, DEFAULTS: DEFAULTS,
    normalize: normalize, sequence: sequence,
    runDuration: runDuration, duration: duration, totalFrames: totalFrames,
    stateAtTime: stateAtTime, beepTimes: beepTimes, render: render
  };
  if (typeof module !== "undefined" && module.exports) module.exports = BadaCountdown;
  global.BadaCountdown = BadaCountdown;
})(typeof globalThis !== "undefined" ? globalThis : this);
