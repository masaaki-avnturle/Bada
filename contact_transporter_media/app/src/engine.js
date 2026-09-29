/*
 * engine.js — Blueprint Studio 共通エンジン
 *   輸送機設計図作成ソフト / ChatGPT 設計図作成ソフト / UFO 設計図作成ソフト で共有する。
 *
 *   - 3D ワイヤーフレームの正射影 (matplotlib mplot3d と同じ elev/azim 規約)
 *   - 1280×720 の論理座標で描き、出力解像度へ拡大縮小
 *   - 設計図 PDF: 各ページを Canvas に描き JPEG 化して最小構成の PDF に格納
 *   - 動画 mp4: WebCodecs (H.264 → VP9 → AV1 の順に対応を確認) + mp4-muxer
 *   - 数学: 複素数, 対数ガンマ, ζ(s) (Euler–Maclaurin), Riemann–Siegel θ / Z
 *
 * Node からも require できる (tools/engine-test.js の数値テスト用)。
 */
(function (root) {
  "use strict";
  var BP = {};

  /* ---------------- 基本 ---------------- */
  BP.W = 1280; BP.H = 720;
  BP.C = {
    bg: "#0b2447", grid: "#2b4a7a", fg: "#e8f1ff", hud: "#9fe8ff", warn: "#ffd166",
    ring: "#f5b942", pod: "#ffffff", tower: "#b8c7e0", j31: "#7fb2ff", j51: "#c28bff",
    j41: "#4fd6e0", axis: "#ff6b5b", window: "#ffa040", well: "#5a7bb0", ok: "#7ee787"
  };
  BP.FONT = '"BPGothic", "IPAGothic", "Yu Gothic UI", "Meiryo", "Noto Sans CJK JP", "Noto Sans JP", sans-serif';
  function clamp(x, a, b) { return x < a ? a : (x > b ? b : x); }
  function smooth(x) { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function linspace(a, b, n, endpoint) {
    if (endpoint === undefined) endpoint = true;
    var out = [], d = endpoint ? (n - 1) : n;
    for (var i = 0; i < n; i++) out.push(a + (b - a) * (d ? i / d : 0));
    return out;
  }
  BP.clamp = clamp; BP.smooth = smooth; BP.lerp = lerp; BP.linspace = linspace;
  BP.fs = function (pt) { return pt * 100 / 72; };          /* matplotlib pt → px (dpi 100) */

  /* ---------------- タイムライン ---------------- */
  function Timeline(scenes) {
    var t = 0;
    this.scenes = scenes.map(function (s) { var o = { name: s[0], t0: t, dur: s[1] }; t += s[1]; return o; });
    this.total = t;
  }
  Timeline.prototype.at = function (sec) {
    for (var i = 0; i < this.scenes.length; i++) {
      var s = this.scenes[i];
      if (sec < s.t0 + s.dur) return { name: s.name, u: (sec - s.t0) / s.dur, local: sec - s.t0, dur: s.dur, t0: s.t0 };
    }
    var l = this.scenes[this.scenes.length - 1];
    return { name: l.name, u: 1, local: l.dur, dur: l.dur, t0: l.t0 };
  };
  Timeline.prototype.start = function (name) {
    for (var i = 0; i < this.scenes.length; i++) if (this.scenes[i].name === name) return this.scenes[i].t0;
    throw new Error("scene " + name);
  };
  BP.Timeline = Timeline;

  /* ---------------- 3D 幾何 ---------------- */
  function mat(a) { return a; }
  BP.rx = function (a) { var c = Math.cos(a), s = Math.sin(a); return mat([[1, 0, 0], [0, c, -s], [0, s, c]]); };
  BP.ry = function (a) { var c = Math.cos(a), s = Math.sin(a); return mat([[c, 0, s], [0, 1, 0], [-s, 0, c]]); };
  BP.rz = function (a) { var c = Math.cos(a), s = Math.sin(a); return mat([[c, -s, 0], [s, c, 0], [0, 0, 1]]); };
  BP.mm = function (A, B) {
    var R = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) for (var k = 0; k < 3; k++) R[i][j] += A[i][k] * B[k][j];
    return R;
  };
  BP.apply = function (M, poly) {
    return poly.map(function (p) {
      return [M[0][0] * p[0] + M[0][1] * p[1] + M[0][2] * p[2],
              M[1][0] * p[0] + M[1][1] * p[1] + M[1][2] * p[2],
              M[2][0] * p[0] + M[2][1] * p[1] + M[2][2] * p[2]];
    });
  };
  BP.shift = function (poly, o) { return poly.map(function (p) { return [p[0] + o[0], p[1] + o[1], p[2] + o[2]]; }); };
  BP.circle = function (R, z, n, cx, cy, plane) {
    n = n || 90; cx = cx || 0; cy = cy || 0; plane = plane || "xy";
    var out = [];
    for (var i = 0; i < n; i++) {
      var t = 2 * Math.PI * i / (n - 1), a = R * Math.cos(t), b = R * Math.sin(t);
      if (plane === "xy") out.push([cx + a, cy + b, z]);
      else if (plane === "xz") out.push([a, 0, b]);
      else out.push([0, a, b]);
    }
    return out;
  };
  BP.seg = function (a, b) { return [a.slice(), b.slice()]; };
  BP.centroid = function (polys) {
    var s = [0, 0, 0], n = 0;
    polys.forEach(function (p) { p.forEach(function (q) { s[0] += q[0]; s[1] += q[1]; s[2] += q[2]; n++; }); });
    return n ? [s[0] / n, s[1] / n, s[2] / n] : s;
  };

  /* カメラ: rect = [x0,y0,w,h] (論理 px), elev/azim [deg], center = データ中心, scale = px/データ単位 */
  function Camera(o) {
    this.elev = o.elev === undefined ? 20 : o.elev;
    this.azim = o.azim === undefined ? -60 : o.azim;
    this.rect = o.rect || [0, 0, BP.W, BP.H];
    this.center = o.center || [0, 0, 0];
    this.scale = o.scale || 3;
    var e = this.elev * Math.PI / 180, a = this.azim * Math.PI / 180;
    this.r = [-Math.sin(a), Math.cos(a), 0];
    this.u = [-Math.sin(e) * Math.cos(a), -Math.sin(e) * Math.sin(a), Math.cos(e)];
    this.cx = this.rect[0] + this.rect[2] / 2;
    this.cy = this.rect[1] + this.rect[3] / 2;
  }
  Camera.prototype.p = function (q) {
    var x = q[0] - this.center[0], y = q[1] - this.center[1], z = q[2] - this.center[2];
    return [this.cx + this.scale * (this.r[0] * x + this.r[1] * y),
            this.cy - this.scale * (this.u[0] * x + this.u[1] * y + this.u[2] * z)];
  };
  BP.Camera = Camera;

  /* polys を描く. opt: {lw, alpha, zscale, offset, dots} */
  BP.drawPolys = function (ctx, cam, polys, color, opt) {
    opt = opt || {};
    var zs = opt.zscale === undefined ? 1 : opt.zscale, off = opt.offset || [0, 0, 0];
    ctx.save();
    ctx.strokeStyle = color; ctx.fillStyle = color;
    ctx.globalAlpha = clamp(opt.alpha === undefined ? 1 : opt.alpha, 0, 1);
    ctx.lineWidth = opt.lw || 1.1;
    ctx.lineJoin = "round";
    for (var i = 0; i < polys.length; i++) {
      var p = polys[i];
      if (p.length === 1 || opt.dots) {
        for (var j = 0; j < p.length; j++) {
          var d = cam.p([p[j][0] + off[0], p[j][1] + off[1], p[j][2] * zs + off[2]]);
          ctx.beginPath(); ctx.arc(d[0], d[1], opt.r || 4, 0, 2 * Math.PI); ctx.fill();
        }
        continue;
      }
      ctx.beginPath();
      for (var k = 0; k < p.length; k++) {
        var s = cam.p([p[k][0] + off[0], p[k][1] + off[1], p[k][2] * zs + off[2]]);
        if (k) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]);
      }
      ctx.stroke();
    }
    ctx.restore();
  };

  /* ---------------- 2D 描画ヘルパ ---------------- */
  BP.clear = function (ctx) { ctx.fillStyle = BP.C.bg; ctx.fillRect(0, 0, BP.W, BP.H); };
  BP.gridBg = function (ctx, w, h) {
    w = w || BP.W; h = h || BP.H;
    ctx.save(); ctx.strokeStyle = BP.C.grid; ctx.globalAlpha = 0.5; ctx.lineWidth = 0.6;
    for (var i = 0; i <= 32; i++) { var x = w * i / 32; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    for (var j = 0; j <= 18; j++) { var y = h * j / 18; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
    ctx.restore();
  };
  /* 図の比率座標 (x: 左から, y: 下から) で文字を置く. o: {size(pt), color, align, alpha, bold, base} */
  BP.text = function (ctx, s, fx, fy, o, w, h) {
    o = o || {}; w = w || BP.W; h = h || BP.H;
    ctx.save();
    ctx.globalAlpha = clamp(o.alpha === undefined ? 1 : o.alpha, 0, 1);
    ctx.fillStyle = o.color || BP.C.fg;
    ctx.font = (o.bold ? "bold " : "") + BP.fs(o.size || 12).toFixed(1) + "px " + BP.FONT;
    ctx.textAlign = o.align || "left";
    ctx.textBaseline = o.base || "alphabetic";
    var lines = String(s).split("\n"), lh = BP.fs(o.size || 12) * (o.lh || 1.45);
    for (var i = 0; i < lines.length; i++) ctx.fillText(lines[i], fx * w, (1 - fy) * h + i * lh);
    ctx.restore();
  };
  BP.textPx = function (ctx, s, x, y, o) {
    o = o || {};
    ctx.save();
    ctx.globalAlpha = clamp(o.alpha === undefined ? 1 : o.alpha, 0, 1);
    ctx.fillStyle = o.color || BP.C.fg;
    ctx.font = (o.bold ? "bold " : "") + BP.fs(o.size || 12).toFixed(1) + "px " + BP.FONT;
    ctx.textAlign = o.align || "left"; ctx.textBaseline = o.base || "alphabetic";
    ctx.fillText(s, x, y);
    ctx.restore();
  };
  BP.line = function (ctx, x0, y0, x1, y1, color, lw, alpha) {
    ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = lw || 1; ctx.globalAlpha = clamp(alpha === undefined ? 1 : alpha, 0, 1);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); ctx.restore();
  };
  /* 比率座標の矩形 (x0,y0: 左下) */
  BP.rectF = function (ctx, fx, fy, fw, fh, o, w, h) {
    o = o || {}; w = w || BP.W; h = h || BP.H;
    var x = fx * w, y = (1 - fy - fh) * h;
    ctx.save();
    if (o.fill) { ctx.globalAlpha = o.fillAlpha === undefined ? 1 : o.fillAlpha; ctx.fillStyle = o.fill; ctx.fillRect(x, y, fw * w, fh * h); }
    if (o.stroke) { ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha; ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw || 1.4; ctx.strokeRect(x, y, fw * w, fh * h); }
    ctx.restore();
  };
  BP.lineF = function (ctx, x0, y0, x1, y1, color, lw, alpha, w, h) {
    w = w || BP.W; h = h || BP.H;
    BP.line(ctx, x0 * w, (1 - y0) * h, x1 * w, (1 - y1) * h, color, lw, alpha);
  };
  BP.fade = function (ctx, a) {
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = clamp(a, 0, 1); ctx.fillStyle = BP.C.bg; ctx.fillRect(0, 0, BP.W, BP.H); ctx.restore();
  };
  BP.header = function (ctx, title, brand, sec, total) {
    if (title) BP.text(ctx, title, 0.03, 0.94, { size: 20, bold: true });
    BP.text(ctx, brand, 0.97, 0.955, { size: 11, color: BP.C.hud, align: "right", alpha: 0.8 });
    BP.lineF(ctx, 0.03, 0.018, 0.97, 0.018, BP.C.grid, 3);
    BP.lineF(ctx, 0.03, 0.018, 0.03 + 0.94 * sec / total, 0.018, BP.C.hud, 3);
  };

  /* 簡易 2D グラフ. rect = [x,y,w,h] 論理 px (y は上から) */
  function Plot(ctx, rect, xlim, ylim, title) {
    this.ctx = ctx; this.r = rect; this.xl = xlim; this.yl = ylim;
    ctx.save();
    ctx.strokeStyle = BP.C.grid; ctx.lineWidth = 1; ctx.strokeRect(rect[0], rect[1], rect[2], rect[3]);
    ctx.restore();
    if (title) BP.textPx(ctx, title, rect[0] + rect[2] / 2, rect[1] - 8, { size: 9, align: "center" });
  }
  Plot.prototype.X = function (x) { return this.r[0] + (x - this.xl[0]) / (this.xl[1] - this.xl[0]) * this.r[2]; };
  Plot.prototype.Y = function (y) { return this.r[1] + this.r[3] - (y - this.yl[0]) / (this.yl[1] - this.yl[0]) * this.r[3]; };
  Plot.prototype.line = function (xs, ys, color, lw, alpha, dash) {
    var c = this.ctx; c.save(); c.beginPath(); c.rect(this.r[0], this.r[1], this.r[2], this.r[3]); c.clip();
    c.strokeStyle = color; c.lineWidth = lw || 1.2; c.globalAlpha = alpha === undefined ? 1 : alpha;
    if (dash) c.setLineDash(dash);
    c.beginPath();
    for (var i = 0; i < xs.length; i++) { var X = this.X(xs[i]), Y = this.Y(ys[i]); if (i) c.lineTo(X, Y); else c.moveTo(X, Y); }
    c.stroke(); c.restore();
  };
  Plot.prototype.dot = function (x, y, color, r) {
    var c = this.ctx; c.save(); c.fillStyle = color; c.beginPath(); c.arc(this.X(x), this.Y(y), r || 3, 0, 2 * Math.PI); c.fill(); c.restore();
  };
  Plot.prototype.ticks = function (nx, ny, fmtx, fmty) {
    var c = this.ctx, i, v;
    fmtx = fmtx || function (v) { return String(Math.round(v * 100) / 100); };
    fmty = fmty || fmtx;
    for (i = 0; i <= nx; i++) {
      v = this.xl[0] + (this.xl[1] - this.xl[0]) * i / nx;
      BP.textPx(c, fmtx(v), this.X(v), this.r[1] + this.r[3] + 12, { size: 7, align: "center" });
    }
    for (i = 0; i <= ny; i++) {
      v = this.yl[0] + (this.yl[1] - this.yl[0]) * i / ny;
      BP.textPx(c, fmty(v), this.r[0] - 4, this.Y(v) + 3, { size: 7, align: "right" });
      BP.line(c, this.r[0], this.Y(v), this.r[0] + this.r[2], this.Y(v), BP.C.grid, 0.5, 0.5);
    }
  };
  BP.Plot = Plot;

  /* 平面図 (正射影 2D). parts = [{polys, color}], view = "top"|"front"|"side", prog = 描き進み率 */
  BP.orthoView = function (ctx, rect, parts, view, xl, yl, prog, title, fsz) {
    fsz = fsz || 1;
    /* 縦横比を保って rect 内に収める */
    var sx = rect[2] / (xl[1] - xl[0]), sy = rect[3] / (yl[1] - yl[0]), s = Math.min(sx, sy);
    var w = s * (xl[1] - xl[0]), h = s * (yl[1] - yl[0]);
    var x0 = rect[0] + (rect[2] - w) / 2, y0 = rect[1] + (rect[3] - h) / 2;
    var P = new Plot(ctx, [x0, y0, w, h], xl, yl, title);
    var step = Math.pow(10, Math.floor(Math.log10((xl[1] - xl[0]) / 4)));
    if ((xl[1] - xl[0]) / step > 8) step *= 2.5;
    ctx.save();
    for (var v = Math.ceil(xl[0] / step) * step; v <= xl[1]; v += step) {
      BP.line(ctx, P.X(v), y0, P.X(v), y0 + h, BP.C.grid, 0.5, 0.6);
      BP.textPx(ctx, String(Math.round(v * 10) / 10), P.X(v), y0 + h + 11 * fsz, { size: 6.5 * fsz, align: "center" });
    }
    for (var u = Math.ceil(yl[0] / step) * step; u <= yl[1]; u += step) {
      BP.line(ctx, x0, P.Y(u), x0 + w, P.Y(u), BP.C.grid, 0.5, 0.6);
      BP.textPx(ctx, String(Math.round(u * 10) / 10), x0 - 3, P.Y(u) + 3, { size: 6.5 * fsz, align: "right" });
    }
    ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.clip();
    parts.forEach(function (pt) {
      ctx.strokeStyle = pt.color; ctx.fillStyle = pt.color; ctx.lineWidth = 0.9; ctx.globalAlpha = 0.95;
      pt.polys.forEach(function (p) {
        var m = Math.max(1, Math.ceil(p.length * (prog === undefined ? 1 : prog)));
        function pr(q) { return view === "top" ? [q[0], q[1]] : (view === "front" ? [q[0], q[2]] : [q[1], q[2]]); }
        if (p.length === 1) { var d = pr(p[0]); ctx.beginPath(); ctx.arc(P.X(d[0]), P.Y(d[1]), 2.5, 0, 7); ctx.fill(); return; }
        ctx.beginPath();
        for (var k = 0; k < m; k++) { var e = pr(p[k]); if (k) ctx.lineTo(P.X(e[0]), P.Y(e[1])); else ctx.moveTo(P.X(e[0]), P.Y(e[1])); }
        ctx.stroke();
      });
    });
    ctx.restore();
    return P;
  };
  BP.arrow2 = function (ctx, x0, y0, x1, y1, color, alpha) {
    ctx.save(); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.globalAlpha = clamp(alpha === undefined ? 1 : alpha, 0, 1);
    ctx.lineWidth = 1.1; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    [[x0, y0, x1, y1], [x1, y1, x0, y0]].forEach(function (a) {
      var ang = Math.atan2(a[1] - a[3], a[0] - a[2]), L = 7;
      ctx.beginPath(); ctx.moveTo(a[0], a[1]);
      ctx.lineTo(a[0] - L * Math.cos(ang - 0.35), a[1] - L * Math.sin(ang - 0.35));
      ctx.lineTo(a[0] - L * Math.cos(ang + 0.35), a[1] - L * Math.sin(ang + 0.35)); ctx.closePath(); ctx.fill();
    });
    ctx.restore();
  };
  BP.card = function (ctx, fx, fy, fw, fh, color, alpha) {
    BP.rectF(ctx, fx, fy, fw, fh, { fill: BP.C.bg, fillAlpha: 0.9, stroke: color, alpha: alpha === undefined ? 1 : alpha, lw: 1.5 });
  };
  BP.balloon = function (ctx, x, y, n, color) {
    ctx.save(); ctx.fillStyle = color; ctx.strokeStyle = BP.C.fg; ctx.lineWidth = 0.8;
    ctx.beginPath(); ctx.arc(x, y, 9, 0, 7); ctx.fill(); ctx.stroke(); ctx.restore();
    BP.textPx(ctx, String(n), x, y + 4, { size: 8.5, color: BP.C.bg, align: "center", bold: true });
  };

  BP.heatmap = function (ctx, rect, A) {
    var n = A.length, cw = rect[2] / n, ch = rect[3] / n;
    for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
      var v = clamp(A[i][j], 0, 1);
      /* magma 風 */
      var r = Math.round(255 * clamp(1.6 * v, 0, 1)), g = Math.round(255 * clamp(1.9 * v - 0.9, 0, 1) * 0.95),
          b = Math.round(255 * clamp(0.35 + 0.9 * v - 1.1 * Math.max(0, v - 0.5), 0, 1));
      if (v < 1e-9) { r = g = 0; b = 4; }
      ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
      ctx.fillRect(rect[0] + j * cw, rect[1] + i * ch, Math.ceil(cw), Math.ceil(ch));
    }
    ctx.save(); ctx.strokeStyle = BP.C.grid; ctx.strokeRect(rect[0], rect[1], rect[2], rect[3]); ctx.restore();
  };

  /* ---------------- 複素数と特殊関数 ---------------- */
  function cx(re, im) { return { re: re, im: im || 0 }; }
  function cadd(a, b) { return cx(a.re + b.re, a.im + b.im); }
  function csub(a, b) { return cx(a.re - b.re, a.im - b.im); }
  function cmul(a, b) { return cx(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re); }
  function cdiv(a, b) { var d = b.re * b.re + b.im * b.im; return cx((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d); }
  function cexp(a) { var e = Math.exp(a.re); return cx(e * Math.cos(a.im), e * Math.sin(a.im)); }
  function clog(a) { return cx(Math.log(Math.hypot(a.re, a.im)), Math.atan2(a.im, a.re)); }
  function cpowReal(n, s) { /* n^s, n > 0 実数 */ return cexp(cmul(cx(Math.log(n)), s)); }
  BP.cx = { make: cx, add: cadd, sub: csub, mul: cmul, div: cdiv, exp: cexp, log: clog, pow: cpowReal };

  /* 複素 log Γ(z) (Re z > 0): z を +8 シフトして Stirling 級数 */
  function lgammaC(z) {
    var shift = cx(0), w = z;
    for (var k = 0; k < 8; k++) { shift = cadd(shift, clog(w)); w = cadd(w, cx(1)); }
    var lw = clog(w);
    var r = csub(cmul(csub(w, cx(0.5)), lw), w);
    r = cadd(r, cx(0.5 * Math.log(2 * Math.PI)));
    var wi = cdiv(cx(1), w), w2 = cmul(wi, wi), term = wi;
    var coef = [1 / 12, -1 / 360, 1 / 1260, -1 / 1680, 1 / 1188, -691 / 360360];
    for (var i = 0; i < coef.length; i++) { r = cadd(r, cmul(cx(coef[i]), term)); term = cmul(term, w2); }
    return csub(r, shift);
  }
  BP.lgammaC = lgammaC;
  /* Riemann–Siegel θ(t) = Im logΓ(1/4 + it/2) − (t/2) log π  (枝は連続になるよう mpmath と同じ) */
  BP.rsTheta = function (t) { return lgammaC(cx(0.25, t / 2)).im - t / 2 * Math.log(Math.PI); };
  /* ζ(s) by Euler–Maclaurin (|Im s| ≲ 60 で倍精度十分) */
  BP.zeta = function (s) {
    var N = 24, sum = cx(0);
    for (var n = 1; n < N; n++) sum = cadd(sum, cpowReal(n, cx(-s.re, -s.im)));
    var Ns = cpowReal(N, cx(-s.re, -s.im));
    sum = cadd(sum, cdiv(cmul(Ns, cx(N)), csub(s, cx(1))));       /* N^{1-s}/(s-1) */
    sum = cadd(sum, cmul(Ns, cx(0.5)));
    var B = [1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6, -3617 / 510];
    var fact = 1, poch = s, pw = cdiv(Ns, cx(N));                  /* s(s+1)..(s+2k-2) N^{-s-2k+1} */
    for (var k = 1; k <= B.length; k++) {
      fact *= (2 * k - 1) * (2 * k);
      sum = cadd(sum, cmul(cx(B[k - 1] / fact), cmul(poch, pw)));
      poch = cmul(poch, cmul(cadd(s, cx(2 * k - 1)), cadd(s, cx(2 * k))));
      pw = cdiv(pw, cx(N * N));
    }
    return sum;
  };
  BP.rsZ = function (t) {
    var z = BP.zeta(cx(0.5, t)), th = BP.rsTheta(t);
    return cmul(cexp(cx(0, th)), z).re;
  };

  /* ---------------- PDF 書き出し (JPEG ページ) ---------------- */
  function strBytes(s) { var a = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i) & 255; return a; }
  function b64ToBytes(b64) {
    var bin = atob(b64), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }
  /* pages: [{jpeg: Uint8Array, w, h}] (px), 用紙は A4 横 842×595pt */
  BP.buildPdf = function (pages, title) {
    var chunks = [], offsets = [], len = 0;
    function push(b) { if (typeof b === "string") b = strBytes(b); chunks.push(b); len += b.length; }
    function obj(n) { offsets[n] = len; push(n + " 0 obj\n"); }
    push("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n");
    var n = pages.length, pageIds = [];
    for (var i = 0; i < n; i++) pageIds.push(3 + i * 3);
    obj(1); push("<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");
    obj(2); push("<< /Type /Pages /Count " + n + " /Kids [" + pageIds.map(function (x) { return x + " 0 R"; }).join(" ") + "] >>\nendobj\n");
    var PW = 842, PH = 595;
    pages.forEach(function (pg, i) {
      var pid = 3 + i * 3, cid = pid + 1, iid = pid + 2;
      obj(pid);
      push("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + PW + " " + PH + "] /Resources << /XObject << /Im0 " + iid +
           " 0 R >> >> /Contents " + cid + " 0 R >>\nendobj\n");
      var cs = "q " + PW + " 0 0 " + PH + " 0 0 cm /Im0 Do Q\n";
      obj(cid); push("<< /Length " + cs.length + " >>\nstream\n" + cs + "endstream\nendobj\n");
      obj(iid);
      push("<< /Type /XObject /Subtype /Image /Width " + pg.w + " /Height " + pg.h +
           " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + pg.jpeg.length + " >>\nstream\n");
      push(pg.jpeg); push("\nendstream\nendobj\n");
    });
    var infoId = 3 + n * 3;
    var t = String(title || "Blueprint").replace(/[^\x20-\x7e]/g, "?").replace(/[()\\]/g, "");
    obj(infoId); push("<< /Title (" + t + ") /Producer (Bada Blueprint Studio) >>\nendobj\n");
    var xref = len;
    var x = "xref\n0 " + (infoId + 1) + "\n0000000000 65535 f \n";
    for (var k = 1; k <= infoId; k++) x += ("0000000000" + offsets[k]).slice(-10) + " 00000 n \n";
    push(x + "trailer\n<< /Size " + (infoId + 1) + " /Root 1 0 R /Info " + infoId + " 0 R >>\nstartxref\n" + xref + "\n%%EOF\n");
    return new Blob(chunks, { type: "application/pdf" });
  };
  /* APP.pdfPages の各関数でページを描き PDF Blob を返す */
  BP.makePdf = function (app, onProgress) {
    var PW = 2339, PH = 1654;              /* A4 横 200 dpi */
    var cv = document.createElement("canvas"); cv.width = PW; cv.height = PH;
    var ctx = cv.getContext("2d");
    var pages = [], i = 0, list = app.pdfPages;
    return new Promise(function (resolve, reject) {
      function next() {
        try {
          if (i >= list.length) { resolve(BP.buildPdf(pages, app.pdfTitle)); return; }
          ctx.setTransform(1, 0, 0, 1, 0, 0);
          var s = PW / BP.PDF_W;
          ctx.setTransform(s, 0, 0, s, 0, 0);
          BP.pdfFrame(ctx, i + 1, list.length, app);
          list[i](ctx, BP.PDF_W, BP.PDF_H);
          var url = cv.toDataURL("image/jpeg", 0.9);
          pages.push({ jpeg: b64ToBytes(url.split(",")[1]), w: PW, h: PH });
          i++;
          if (onProgress) onProgress(i / list.length);
          setTimeout(next, 0);
        } catch (e) { reject(e); }
      }
      next();
    });
  };
  BP.PDF_W = 1169; BP.PDF_H = 827;          /* PDF ページの論理座標 (A4 横, 1/10 mm 相当) */
  /* 図枠 + 表題欄 */
  BP.pdfFrame = function (ctx, no, total, app) {
    var w = BP.PDF_W, h = BP.PDF_H;
    ctx.fillStyle = BP.C.bg; ctx.fillRect(0, 0, w, h);
    ctx.save(); ctx.strokeStyle = BP.C.grid; ctx.globalAlpha = 0.5; ctx.lineWidth = 0.4;
    for (var i = 0; i <= 48; i++) { ctx.beginPath(); ctx.moveTo(w * i / 48, 0); ctx.lineTo(w * i / 48, h); ctx.stroke(); }
    for (var j = 0; j <= 34; j++) { ctx.beginPath(); ctx.moveTo(0, h * j / 34); ctx.lineTo(w, h * j / 34); ctx.stroke(); }
    ctx.restore();
    ctx.save(); ctx.strokeStyle = BP.C.fg; ctx.lineWidth = 1.2; ctx.strokeRect(0.015 * w, 0.02 * h, 0.97 * w, 0.96 * h);
    ctx.fillStyle = BP.C.bg; ctx.fillRect(0.66 * w, 0.92 * h, 0.325 * w, 0.06 * h);
    ctx.lineWidth = 0.8; ctx.strokeRect(0.66 * w, 0.92 * h, 0.325 * w, 0.06 * h); ctx.restore();
    var d = new Date(), ds = d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
    BP.text(ctx, app.brand, 0.67, 0.058, { size: 9, color: BP.C.hud, bold: true }, w, h);
    BP.text(ctx, "図番 " + ("0" + no).slice(-2) + "/" + ("0" + total).slice(-2) + "   " + ds + "   masaaki-avnturle / Bada",
            0.67, 0.033, { size: 7.5 }, w, h);
  };
  BP.pdfTitle = function (ctx, title, sub) {
    var w = BP.PDF_W, h = BP.PDF_H;
    if (title) BP.text(ctx, title, 0.03, 0.935, { size: 17, bold: true }, w, h);
    if (sub) BP.text(ctx, sub, 0.03, 0.905, { size: 10, color: BP.C.hud }, w, h);
  };

  /* ---------------- 動画 mp4 書き出し ---------------- */
  BP.pickVideoCodec = function (w, h, fps) {
    var cands = [
      { enc: "avc1.640028", mux: "avc" }, { enc: "avc1.4d0028", mux: "avc" }, { enc: "avc1.42001f", mux: "avc" },
      { enc: "vp09.00.40.08", mux: "vp9" }, { enc: "av01.0.08M.08", mux: "av1" }
    ];
    var br = Math.round(w * h * fps * 0.12);
    var i = 0;
    return new Promise(function (resolve) {
      function next() {
        if (i >= cands.length) { resolve(null); return; }
        var c = cands[i++];
        var cfg = { codec: c.enc, width: w, height: h, bitrate: br, framerate: fps };
        if (c.mux === "avc") cfg.avc = { format: "avc" };
        VideoEncoder.isConfigSupported(cfg).then(function (r) {
          if (r.supported) resolve({ cfg: cfg, mux: c.mux }); else next();
        }, next);
      }
      next();
    });
  };
  BP.pickAudioCodec = function (sr) {
    if (typeof AudioEncoder === "undefined") return Promise.resolve(null);
    var cands = [{ codec: "mp4a.40.2", mux: "aac" }, { codec: "opus", mux: "opus" }], i = 0;
    return new Promise(function (resolve) {
      function next() {
        if (i >= cands.length) { resolve(null); return; }
        var c = cands[i++], cfg = { codec: c.codec, sampleRate: sr, numberOfChannels: 1, bitrate: 128000 };
        AudioEncoder.isConfigSupported(cfg).then(function (r) { if (r.supported) resolve({ cfg: cfg, mux: c.mux }); else next(); }, next);
      }
      next();
    });
  };
  /*
   * opts: {width, height, fps, total(sec), frame(ctx, sec), audio(sr) -> Float32Array, onProgress(frac, msg), signal:{abort}}
   */
  BP.exportMp4 = function (opts) {
    if (typeof VideoEncoder === "undefined" || typeof root.Mp4Muxer === "undefined")
      return Promise.reject(new Error("この環境は WebCodecs (VideoEncoder) に対応していません。"));
    var W = opts.width, H = opts.height, fps = opts.fps, n = Math.round(opts.total * fps), SR = 48000;
    var cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    var ctx = cv.getContext("2d", { alpha: false });
    return Promise.all([BP.pickVideoCodec(W, H, fps), BP.pickAudioCodec(SR)]).then(function (res) {
      var vc = res[0], ac = res[1];
      if (!vc) throw new Error("H.264 / VP9 / AV1 のいずれの動画エンコーダも利用できません。");
      var M = root.Mp4Muxer;
      var target = new M.ArrayBufferTarget();
      var mcfg = { target: target, video: { codec: vc.mux, width: W, height: H, frameRate: fps },
                   fastStart: "in-memory", firstTimestampBehavior: "offset" };
      if (ac) mcfg.audio = { codec: ac.mux, numberOfChannels: 1, sampleRate: SR };
      var muxer = new M.Muxer(mcfg);
      var failed = null;
      var venc = new VideoEncoder({
        output: function (chunk, meta) { muxer.addVideoChunk(chunk, meta); },
        error: function (e) { failed = e; }
      });
      venc.configure(vc.cfg);
      var aenc = null;
      if (ac) {
        aenc = new AudioEncoder({ output: function (c, m) { muxer.addAudioChunk(c, m); }, error: function (e) { failed = e; } });
        aenc.configure(ac.cfg);
        var pcm = opts.audio(SR).subarray(0, Math.round(opts.total * SR)), block = 4800;
        for (var p = 0; p < pcm.length; p += block) {
          var part = pcm.subarray(p, Math.min(pcm.length, p + block));
          var ad = new AudioData({ format: "f32", sampleRate: SR, numberOfFrames: part.length, numberOfChannels: 1,
                                   timestamp: Math.round(p / SR * 1e6), data: part });
          aenc.encode(ad); ad.close();
        }
      }
      var i = 0, t0 = Date.now();
      return new Promise(function (resolve, reject) {
        function step() {
          if (failed) { reject(failed); return; }
          if (opts.signal && opts.signal.abort) { reject(new Error("中止しました")); return; }
          if (venc.encodeQueueSize > 8) { setTimeout(step, 5); return; }
          var until = Math.min(n, i + 3);
          for (; i < until; i++) {
            ctx.setTransform(W / BP.W, 0, 0, H / BP.H, 0, 0);
            opts.frame(ctx, i / fps);
            var vf = new VideoFrame(cv, { timestamp: Math.round(i * 1e6 / fps), duration: Math.round(1e6 / fps) });
            venc.encode(vf, { keyFrame: i % (fps * 2) === 0 });
            vf.close();
          }
          if (opts.onProgress) {
            var el = (Date.now() - t0) / 1000, rem = i ? el / i * (n - i) : 0;
            opts.onProgress(i / n, "フレーム " + i + "/" + n + "  残り約 " + Math.ceil(rem) + " 秒  [" + vc.cfg.codec + (ac ? " + " + ac.cfg.codec : "") + "]");
          }
          if (i < n) { setTimeout(step, 0); return; }
          var flushes = [venc.flush()];
          if (aenc) flushes.push(aenc.flush());
          Promise.all(flushes).then(function () {
            muxer.finalize();
            resolve({ blob: new Blob([target.buffer], { type: "video/mp4" }), codec: vc.cfg.codec, audio: ac ? ac.cfg.codec : null });
          }, reject);
        }
        step();
      });
    });
  };

  /* ---------------- 保存 ---------------- */
  BP.saveBlob = function (blob, name, mime, setMsg) {
    var cdv = root.cordova && root.cordova.plugins && root.cordova.plugins.saveDialog;
    if (cdv && typeof cdv.saveFile === "function") {
      setMsg("保存先を選択してください…");
      cdv.saveFile(blob, name).then(function () { setMsg("✅ 保存しました: " + name); },
        function (err) { if (err && !/cancel/i.test(String(err))) setMsg("保存に失敗しました: " + err, true); else setMsg(""); });
      return;
    }
    if (typeof root.showSaveFilePicker === "function") {
      var acc = {}; acc[mime] = ["." + name.split(".").pop()];
      root.showSaveFilePicker({ suggestedName: name, types: [{ description: name, accept: acc }] })
        .then(function (h) { return h.createWritable(); })
        .then(function (w) { return w.write(blob).then(function () { return w.close(); }); })
        .then(function () { setMsg("✅ 保存しました: " + name); })
        .catch(function (e) { if (e && e.name === "AbortError") return; anchor(); });
      return;
    }
    anchor();
    function anchor() {
      var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setMsg("✅ ダウンロードしました: " + name);
    }
  };

  /* ---------------- UI ---------------- */
  BP.boot = function (app) {
    var $ = function (id) { return document.getElementById(id); };
    document.title = app.title;
    $("appTitle").textContent = app.title;
    $("appSub").textContent = app.subtitle;
    var cv = $("preview"), ctx = cv.getContext("2d");
    var playing = true, sec = 0, last = performance.now(), busy = false;
    var seek = $("seek"); seek.max = String(app.timeline.total);
    var chips = $("chips");
    app.timeline.scenes.forEach(function (s) {
      var b = document.createElement("button"); b.className = "chip";
      b.textContent = app.sceneLabels[s.name] || s.name;
      b.onclick = function () { sec = s.t0 + 0.01; };
      chips.appendChild(b);
    });
    function draw() {
      var dpr = Math.min(2, root.devicePixelRatio || 1), w = cv.clientWidth * dpr, h = w * 9 / 16;
      if (cv.width !== Math.round(w)) { cv.width = Math.round(w); cv.height = Math.round(h); }
      ctx.setTransform(cv.width / BP.W, 0, 0, cv.height / BP.H, 0, 0);
      app.frame(ctx, sec);
    }
    function loop(now) {
      var dt = (now - last) / 1000; last = now;
      if (playing && !busy) { sec += dt; if (sec >= app.timeline.total) sec = 0; }
      if (!busy) { draw(); seek.value = String(sec); $("time").textContent = sec.toFixed(1) + " / " + app.timeline.total + " s"; }
      requestAnimationFrame(loop);
    }
    $("play").onclick = function () { playing = !playing; $("play").textContent = playing ? "⏸ 一時停止" : "▶ 再生"; };
    seek.oninput = function () { sec = parseFloat(seek.value); };
    function setMsg(m, err) { var e = $("msg"); e.textContent = m; e.className = err ? "msg err" : "msg"; }
    function setProg(f, m) { $("bar").style.width = (100 * f).toFixed(1) + "%"; if (m) $("prog").textContent = m; }
    var lastPdf = null, lastMp4 = null;
    $("mkpdf").onclick = function () {
      if (busy) return; busy = true; setMsg("設計図 PDF を作成中…"); setProg(0, "");
      BP.makePdf(app, function (f) { setProg(f, "ページ " + Math.round(f * app.pdfPages.length) + "/" + app.pdfPages.length); })
        .then(function (blob) {
          lastPdf = blob; busy = false;
          setMsg("✅ PDF 完成 (" + (blob.size / 1e6).toFixed(1) + " MB, " + app.pdfPages.length + " ページ)。「PDF を保存」で保存できます。");
          $("savepdf").disabled = false;
        }, function (e) { busy = false; setMsg("PDF 作成に失敗: " + e.message, true); });
    };
    $("savepdf").onclick = function () { if (lastPdf) BP.saveBlob(lastPdf, app.fileBase + "_blueprint.pdf", "application/pdf", setMsg); };
    var job = null;
    $("mkmp4").onclick = function () {
      if (busy) { if (job) job.abort = true; return; }
      var q = $("quality").value.split("x").map(Number);   /* "1280x720x30" */
      busy = true; job = { abort: false };
      $("mkmp4").textContent = "■ 中止";
      setMsg("動画 (mp4) を書き出し中… アプリを閉じずにお待ちください。");
      BP.exportMp4({ width: q[0], height: q[1], fps: q[2], total: app.timeline.total, frame: app.frame, audio: app.audio,
                     signal: job, onProgress: setProg })
        .then(function (r) {
          lastMp4 = r.blob; busy = false; $("mkmp4").textContent = "🎬 動画 mp4 を作成";
          setMsg("✅ 動画完成 (" + (r.blob.size / 1e6).toFixed(1) + " MB, " + r.codec + (r.audio ? " / " + r.audio : " / 音声なし") + ")。「動画を保存」で保存できます。");
          $("savemp4").disabled = false;
        }, function (e) { busy = false; $("mkmp4").textContent = "🎬 動画 mp4 を作成"; setMsg("動画作成に失敗: " + e.message, true); });
    };
    $("savemp4").onclick = function () { if (lastMp4) BP.saveBlob(lastMp4, app.fileBase + ".mp4", "video/mp4", setMsg); };
    $("about").innerHTML = app.aboutHtml;
    requestAnimationFrame(loop);
  };

  root.BP = BP;
  if (typeof module !== "undefined" && module.exports) module.exports = BP;
})(typeof window !== "undefined" ? window : globalThis);
