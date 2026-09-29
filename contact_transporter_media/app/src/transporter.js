/*
 * transporter.js — 輸送機設計図作成ソフト (CONTACT TRANSPORTER)
 *   contact_blueprint.pdf の Bada 実行結果と方程式 2111 本 (BP_REGISTRY) から
 *   部品 → 平面図 → 3D → 組み立て → 起動・輸送 の動画と設計図 PDF を生成する。
 *   Python 版 (transporter_model.py / transporter_video.py / blueprint_pdf.py) の移植。
 */
(function (root) {
  "use strict";
  var BP = root.BP, C = BP.C, T = BP.text, sm = BP.smooth, PI = Math.PI;

  /* ---- レポート 1 章「設計パラメータ」 ---- */
  var P = {
    nhat: [0.86964, -0.25101, 0.42511], Gamma: 64800, phi: 11.7722,
    theta0: 0.523599, omega: [0.10472, 0.39241, 1.47043], Omega: 3.70640,
    Rout: 60.088, Rmid: 47.431, Rin: 37.440, tube: 2.066, podR: 5.021, towerH: 132.194, wellD: 38.8,
    J31R: 70.269, J51R: 56.215
  };
  P.rsTheta = BP.rsTheta(P.phi);
  P.rsZ = BP.rsZ(P.phi);
  var GROUND = -P.wellD, POD_TOP = P.towerH - 14;

  /* Jones 多項式 */
  var JONES = {
    "3_1": [[-4, -1], [-3, 1], [-1, 1]],
    "4_1": [[-2, 1], [-1, -1], [0, 1], [1, -1], [2, 1]],
    "5_1": [[2, 1], [4, 1], [5, -1], [6, 1], [7, -1]]
  };
  function jonesAt(k, a) { /* t = e^{ia} */
    var re = 0, im = 0;
    JONES[k].forEach(function (t) { re += t[1] * Math.cos(t[0] * a); im += t[1] * Math.sin(t[0] * a); });
    return [re, im];
  }
  var VT = {};
  Object.keys(JONES).forEach(function (k) { VT[k] = jonesAt(k, P.rsTheta); });
  var ALPHA = BP.linspace(0, 2 * PI, 3601), VABS = {}, WINDOWS = [];
  Object.keys(JONES).forEach(function (k) {
    VABS[k] = ALPHA.map(function (a) { var v = jonesAt(k, a); return Math.hypot(v[0], v[1]); });
    for (var i = 1; i < ALPHA.length - 1; i++)
      if (VABS[k][i] < VABS[k][i - 1] && VABS[k][i] < VABS[k][i + 1]) WINDOWS.push([k, ALPHA[i], VABS[k][i]]);
  });
  var ZT = BP.linspace(0.5, 40, 400), ZV = ZT.map(BP.rsZ);

  /* ---- 幾何 ---- */
  function ringTube(R, r, plane, n) {
    var out = [];
    for (var j = 0; j < 3; j++) {
      var a = 2 * PI * j / 3, c = BP.circle(R + r * Math.cos(a), 0, n || 140, 0, 0, plane);
      var off = plane === "xy" ? [0, 0, 1] : (plane === "xz" ? [0, 1, 0] : [1, 0, 0]);
      out.push(BP.shift(c, [off[0] * r * Math.sin(a), off[1] * r * Math.sin(a), off[2] * r * Math.sin(a)]));
    }
    return out;
  }
  function gimbal(t) {
    var w = P.omega;
    var R1 = BP.mm(BP.rz(w[0] * t), BP.rx(P.theta0)), R2 = BP.mm(R1, BP.rx(w[1] * t)), R3 = BP.mm(R2, BP.ry(w[2] * t));
    var out = [];
    [[R1, P.Rout, "xz"], [R2, P.Rmid, "xy"], [R3, P.Rin, "yz"]].forEach(function (g) {
      ringTube(g[1], P.tube, g[2]).forEach(function (c) { out.push(BP.apply(g[0], c)); });
    });
    return out;
  }
  function torusKnot(p, q, R, b, zc, n) {
    var out = [], a = R - b;
    for (var i = 0; i < n; i++) {
      var t = 2 * PI * i / (n - 1), r = a + b * Math.cos(q * t);
      out.push([r * Math.cos(p * t), r * Math.sin(p * t), zc + b * Math.sin(q * t)]);
    }
    return out;
  }
  function fig8(s, zc) {
    var out = [];
    for (var i = 0; i < 400; i++) {
      var t = 2 * PI * i / 399, r = s * (2 + Math.cos(2 * t));
      out.push([r * Math.cos(3 * t), r * Math.sin(3 * t), zc + s * Math.sin(4 * t)]);
    }
    return out;
  }
  function sphere(r, c) {
    var out = [];
    BP.linspace(-PI / 2, PI / 2, 9).slice(1, 8).forEach(function (la) {
      out.push(BP.circle(r * Math.cos(la), c[2] + r * Math.sin(la), 40, c[0], c[1]));
    });
    for (var k = 0; k < 8; k++) {
      var lo = PI * k / 8;
      out.push(BP.shift(BP.apply(BP.rz(lo), BP.circle(r, 0, 40, 0, 0, "xz")), c));
    }
    return out;
  }
  var TA = 48;
  function tower() {
    var h = P.towerH, g = GROUND, L = [], cs = [[TA, TA], [-TA, TA], [-TA, -TA], [TA, -TA]];
    cs.forEach(function (c) { L.push([[c[0], c[1], g], [c[0], c[1], h]]); L.push([[c[0], c[1], h], [0, 0, h + 8]]); });
    var zs = BP.linspace(g + 20, h - 10, 6);
    zs.forEach(function (z) { L.push(cs.concat([cs[0]]).map(function (c) { return [c[0], c[1], z]; })); });
    for (var i = 0; i < 4; i++) {
      var a = cs[i], b = cs[(i + 1) % 4];
      for (var k = 0; k < 5; k++) L.push([[a[0], a[1], zs[k]], [b[0], b[1], zs[k + 1]]]);
    }
    L.push([[0, 0, h + 8], [0, 0, h - 6]]);
    return L;
  }
  function base() {
    var L = [];
    [66, 78, 90].forEach(function (R) { L.push(BP.circle(R, GROUND, 120)); });
    for (var k = 0; k < 12; k++) {
      var a = 2 * PI * k / 12;
      L.push([[66 * Math.cos(a), 66 * Math.sin(a), GROUND], [90 * Math.cos(a), 90 * Math.sin(a), GROUND]]);
    }
    return L;
  }
  function well() {
    var L = [];
    BP.linspace(GROUND, GROUND - 30, 4).forEach(function (z) { L.push(BP.circle(66 - (GROUND - z) * 1.2, z, 120)); });
    for (var k = 0; k < 16; k++) {
      var a = 2 * PI * k / 16;
      L.push([[66 * Math.cos(a), 66 * Math.sin(a), GROUND], [30 * Math.cos(a), 30 * Math.sin(a), GROUND - 30]]);
    }
    return L;
  }
  var NH = (function () { var n = P.nhat, l = Math.hypot(n[0], n[1], n[2]); return [n[0] / l, n[1] / l, n[2] / l]; })();
  var STATIC = {
    base: base(), well: well(), tower: tower(),
    j31: [torusKnot(2, 3, P.J31R, 12, 0, 600)], j51: [torusKnot(2, 5, P.J51R, 9, 70, 700)], j41: [fig8(4.5, GROUND + 14)],
    window: WINDOWS.map(function (w) { var R = 26 + 4 * w[2]; return [[R * Math.cos(w[1]), R * Math.sin(w[1]), 0]]; }),
    axis: [[[0, 0, 0], [NH[0] * 95, NH[1] * 95, NH[2] * 95]]]
  };
  var COLKEY = { base: "tower", well: "well", tower: "tower", ring: "ring", j31: "j31", j51: "j51", j41: "j41",
                 window: "window", pod: "pod", axis: "axis" };
  function scene(tRot, podZ) {
    return {
      base: STATIC.base, well: STATIC.well, tower: STATIC.tower, ring: gimbal(tRot || 0),
      j31: STATIC.j31, j51: STATIC.j51, j41: STATIC.j41, window: STATIC.window,
      pod: sphere(P.podR, [0, 0, podZ || 0]), axis: STATIC.axis
    };
  }
  var ORDER = ["base", "well", "tower", "ring", "j31", "j51", "j41", "window", "pod", "axis"];
  var EXPLODE = { base: [0, 0, -80], well: [0, 0, -90], tower: [0, 0, 160], ring: [140, 0, 30], j31: [-150, 0, 0],
                  j51: [0, 150, 60], j41: [0, -140, -40], window: [0, 0, 120], pod: [0, 0, 120], axis: [60, -20, 60] };
  var CARD = {
    base: ["基礎・床", ["床面 z = −井戸深さ = −38.800 m", "OTHER 群: □ = −(16πG/c⁴)·T_μν"]],
    well: ["井戸 (輸送計量)", ["ds² = e^(−2πT|ψ|)[η + h̄]dx^μ dx^ν + T² dψ²", "e^(−2πT|ψ|) = 1/Γ ⇒ T|ψ| = 1.76329", "深さ 38.800 m"]],
    tower: ["塔・ガントリー", ["θ(φ) = arg Γ(1/4 + iφ/2) − (φ/2) log π", "θ(11.7722) = " + P.rsTheta.toFixed(5), "塔高 132.194 m"]],
    ring: ["ジンバル環 ×3 (複素回転体)", ["Θ = θ + iφ,  θ₀ = 0.523599 rad", "ω = 0.10472, 0.39241, 1.47043 rad/s", "R = 60.088 / 47.431 / 37.440 m"]],
    j31: ["Jones コイル 3_1 (三葉結び目)", ["V = −t⁻⁴ + t⁻³ + t⁻¹", "V(t*) = " + cstr(VT["3_1"]), "R = 70.269 m"]],
    j51: ["Jones コイル 5_1", ["V = t² + t⁴ − t⁵ + t⁶ − t⁷", "V(t*) = " + cstr(VT["5_1"]), "R = 56.215 m"]],
    j41: ["Jones コイル 4_1 (8の字結び目, 床下)", ["V = t⁻² − t⁻¹ + 1 − t + t²", "V(t*) = " + VT["4_1"][0].toFixed(5), "t* = e^(iθ(φ))"]],
    window: ["扉の共鳴窓", ["Z(φ) = e^(iθ(φ)) ζ(1/2 + iφ) = " + P.rsZ.toFixed(5), "min_α |V_K(e^(iα))| の角度に配置", "窓 " + WINDOWS.length + " 箇所"]],
    pod: ["ポッド (搭乗室)", ["Γ = 18 h / 1 s = 64800", "φ = arcosh Γ = " + Math.acosh(P.Gamma).toFixed(4), "Ω = Mgl/(I₃ω₃) = 3.70640 rad/s,  r = 5.021 m"]],
    axis: ["扉の軸 n̂", ["√s = 13.6 TeV,  E_T^miss = 1348.29 GeV", "n̂ = (0.86964, −0.25101, 0.42511)", "CERN の衝突で粒子が消えた方向"]]
  };
  function cstr(v) { return v[0].toFixed(5) + (v[1] >= 0 ? " + " : " − ") + Math.abs(v[1]).toFixed(5) + "i"; }

  /* ---- 方程式レジストリ → 部品 ---- */
  var TAG_PART = { ROT: "ring", SR: "pod", QUANTUM: "pod", GAMMA: "tower", BETA: "tower", ZETA: "window", JONES: "coil",
                   MANIFOLD: "well", ENTROPY: "well", TRANSPORT: "axis", OTHER: "base" };
  var PARTS = [["base", "基礎・床", C.tower], ["well", "井戸 (輸送計量)", C.well], ["tower", "塔・ガントリー", C.tower],
               ["ring", "ジンバル環 ×3", C.ring], ["coil", "Jones コイル", C.j51], ["window", "共鳴窓", C.window],
               ["pod", "ポッド", C.pod], ["axis", "扉の軸", C.axis]];
  var PCOL = {}; PARTS.forEach(function (p) { PCOL[p[0]] = p[2]; });
  var REG = (root.BP_REGISTRY || []).map(function (r) { return { id: r[0], st: r[1], tag: r[2], eq: r[3], part: TAG_PART[r[2]] || "base" }; });
  var CUM = {};
  PARTS.forEach(function (p) { var c = 0; CUM[p[0]] = REG.map(function (e) { if (e.part === p[0]) c++; return c; }); });

  /* ---- カメラ ---- */
  function cam(rect, elev, azim, zoom, center) {
    return new BP.Camera({ rect: rect, elev: elev, azim: azim, center: center || [0, 0, 38], scale: rect[3] / 290 * (zoom || 1) });
  }
  function drawScene(ctx, c, sc, o) {
    o = o || {};
    Object.keys(sc).forEach(function (k) {
      if (o.skip && o.skip[k]) return;
      var extra = o.per ? (o.per[k] || {}) : {};
      BP.drawPolys(ctx, c, sc[k], C[COLKEY[k]], { lw: extra.lw || o.lw || 1.0, alpha: extra.alpha === undefined ? (o.alpha === undefined ? 0.9 : o.alpha) : extra.alpha,
                                              zscale: o.zscale, offset: extra.offset, r: 3.5 });
    });
  }

  /* ---- タイムライン ---- */
  var TL = new BP.Timeline([["title", 5], ["params", 9], ["mapping", 12], ["plan", 10], ["to3d", 8],
                            ["assembly", 30], ["activate", 16], ["transport", 14], ["end", 8]]);
  var TITLES = {
    params: "1. 設計原理と Bada 実行結果", mapping: "2. 方程式 2111 本 → 部品への対応", plan: "3. 平面図 (三面図)  単位 m",
    to3d: "4. 平面図 → 3D 変換", assembly: "5. 組み立て", activate: "6. 起動 — ジンバル環の回転と共鳴",
    transport: "7. 輸送 — 扉の軸 n̂ に沿って異次元へ"
  };
  var LABELS = { title: "タイトル", params: "パラメータ", mapping: "方程式→部品", plan: "平面図", to3d: "3D 変換",
                 assembly: "組み立て", activate: "起動", transport: "輸送", end: "終了" };

  function sTitle(ctx, u, sec) {
    BP.gridBg(ctx);
    var c = cam([320, 100, 640, 560], 18, -60 + 20 * sec, 1.3, [0, 0, 0]);
    BP.drawPolys(ctx, c, gimbal(sec * 3), C.ring, { lw: 0.9, alpha: 0.35 * sm(u * 3) });
    var a = sm(u * 2.5);
    T(ctx, "CONTACT TRANSPORTER", 0.5, 0.62, { size: 46, align: "center", bold: true, alpha: a });
    T(ctx, "異次元への輸送機 — 方程式から組み立てる 3D 設計図", 0.5, 0.52, { size: 22, align: "center", color: C.hud, alpha: a });
    T(ctx, "原典: contact_blueprint.pdf (Bada: contact_transporter/contact_blueprint.bada)\n論文 15 本・全方程式 2111 本 → 部品 → 平面図 → 3D → 組み立て → 起動",
      0.5, 0.2, { size: 13, align: "center", alpha: sm(u * 2.5 - 0.6) });
  }
  var PARAMS = [
    ["① 衝突段", "√s = 13.6 TeV,  E_T^miss = 1348.29 GeV  →  扉の軸 n̂ = (0.870, −0.251, 0.425)", C.axis],
    ["② 特殊相対論", "地球の 1 秒 = 搭乗者の 18 時間:  Γ = 64800,  1 − β = 1.19×10⁻¹⁰,  φ = 11.7722", C.pod],
    ["②' 輸送計量", "ds² = e^(−2πT|ψ|)[η + h̄]dx^μ dx^ν + T² dψ²,   T|ψ| = 1.76329", C.well],
    ["③ 複素回転体", "Θ = θ + iφ,  θ₀ = 30°,   ω = (0.105, 0.392, 1.470) rad/s", C.ring],
    ["④ Γ・ζ 多様体", "θ(φ) = " + P.rsTheta.toFixed(5) + ",   Z(φ) = e^(iθ) ζ(1/2 + iφ) = " + P.rsZ.toFixed(5), C.window],
    ["⑤ Jones 多項式", "V_3_1(t*) = −0.116 + 2.309i,  V_4_1 = 3.565,  V_5_1 = −2.815 + 1.097i", C.j51],
    ["⑥ 寸法", "外環 60.088 / 中環 47.431 / 内環 37.440 / ポッド r 5.021 / 塔高 132.194 / 井戸 38.8 m", C.tower]
  ];
  function sParams(ctx, u) {
    BP.gridBg(ctx);
    PARAMS.forEach(function (r, i) {
      var a = sm((u * 1.25 - i * 0.12) * 5), y = 0.8 - i * 0.105;
      T(ctx, r[0], 0.05 + 0.02 * (1 - a), y, { size: 17, bold: true, color: r[2], alpha: a });
      T(ctx, r[1], 0.23 + 0.02 * (1 - a), y, { size: 15, alpha: a });
    });
    T(ctx, "θ(φ), Z(φ), V(t*) はアプリ内で再計算 (複素 logΓ + Euler–Maclaurin ζ) — レポート値と一致 (V は 4 桁以上)", 0.05, 0.06,
      { size: 12, color: C.hud, alpha: sm(u * 3 - 2) });
  }
  function sMapping(ctx, u) {
    BP.gridBg(ctx);
    var n = Math.floor(BP.clamp(sm(u * 1.15), 0, 1) * REG.length);
    T(ctx, "方程式レジストリ  " + n + " / " + REG.length, 0.04, 0.86, { size: 14, color: C.hud });
    var shown = REG.slice(Math.max(0, n - 15), n).reverse();
    shown.forEach(function (e, j) {
      var y = 0.81 - j * 0.049, a = 1 - j / 17, txt = e.eq.length < 46 ? e.eq : e.eq.slice(0, 45) + "…";
      T(ctx, e.id, 0.04, y, { size: 10.5, color: PCOL[e.part], alpha: a });
      T(ctx, txt, 0.12, y, { size: 10.5, alpha: a });
    });
    var ys = {};
    PARTS.forEach(function (p, i) {
      var y = 0.82 - i * 0.095, cnt = n ? CUM[p[0]][n - 1] : 0, tot = CUM[p[0]][REG.length - 1] || 1;
      ys[p[0]] = y;
      BP.rectF(ctx, 0.66, y - 0.03, 0.31 * cnt / tot, 0.07, { fill: p[2], fillAlpha: 0.18 });
      BP.rectF(ctx, 0.66, y - 0.03, 0.31, 0.07, { stroke: p[2] });
      T(ctx, p[1], 0.67, y - 0.012, { size: 13 });
      T(ctx, String(cnt), 0.96, y - 0.012, { size: 14, color: p[2], align: "right", bold: true });
      var tags = Object.keys(TAG_PART).filter(function (t) { return TAG_PART[t] === p[0]; }).join(" ");
      T(ctx, tags, 0.655, y - 0.01, { size: 8.5, color: C.grid, align: "right" });
    });
    REG.slice(Math.max(0, n - 5), n).reverse().forEach(function (e, j) {
      BP.lineF(ctx, 0.5, 0.81 - j * 0.049 + 0.006, 0.655, ys[e.part], PCOL[e.part], 1.2, 0.8 - j * 0.15);
    });
    if (u > 0.9) T(ctx, "先頭タグで割り当て: ROT→環, SR/QUANTUM→ポッド, GAMMA/BETA→塔, ZETA→共鳴窓, JONES→コイル, MANIFOLD/ENTROPY→井戸, TRANSPORT→扉の軸",
                   0.04, 0.05, { size: 11, color: C.hud });
  }
  function planParts(sc) { return Object.keys(sc).map(function (k) { return { polys: sc[k], color: C[COLKEY[k]] }; }); }
  function drawPlan(ctx, prog, dims, rects, fsz) {
    var sc = scene(0, 0), parts = planParts(sc);
    var V = {
      top: BP.orthoView(ctx, rects.top, parts, "top", [-95, 95], [-95, 95], prog, "上面図 (x–y)", fsz),
      front: BP.orthoView(ctx, rects.front, parts, "front", [-95, 95], [GROUND - 35, 150], prog, "正面図 (x–z)", fsz),
      side: BP.orthoView(ctx, rects.side, parts, "side", [-95, 95], [GROUND - 35, 150], prog, "側面図 (y–z)", fsz)
    };
    if (dims > 0) {
      var a = sm(dims), t = V.top, f = V.front, s = V.side, o = { size: 9 * (fsz || 1), color: C.warn, alpha: a };
      BP.arrow2(ctx, t.X(0), t.Y(0), t.X(P.Rout), t.Y(0), C.warn, a); BP.textPx(ctx, "R外 = 60.088", t.X(8), t.Y(4), o);
      BP.arrow2(ctx, t.X(0), t.Y(0), t.X(0), t.Y(-P.J31R), C.j31, a);
      BP.textPx(ctx, "Jones 3_1 R = 70.269", t.X(3), t.Y(-50), { size: o.size, color: C.j31, alpha: a });
      BP.arrow2(ctx, f.X(-85), f.Y(P.towerH), f.X(-85), f.Y(GROUND), C.warn, a);
      BP.textPx(ctx, "塔高 132.194", f.X(-82), f.Y(62), o); BP.textPx(ctx, "(+38.8)", f.X(-82), f.Y(52), o);
      BP.arrow2(ctx, f.X(70), f.Y(0), f.X(70), f.Y(GROUND), C.warn, a); BP.textPx(ctx, "井戸 38.8", f.X(72), f.Y(-20), o);
      BP.textPx(ctx, "ポッド r=5.021", f.X(8), f.Y(8), { size: o.size * 0.9, alpha: a });
      BP.textPx(ctx, "5_1 R=56.215", s.X(-90), s.Y(80), { size: o.size, color: C.j51, alpha: a });
      BP.textPx(ctx, "4_1 床下", s.X(-90), s.Y(GROUND + 20), { size: o.size, color: C.j41, alpha: a });
    }
  }
  function sPlan(ctx, u) {
    BP.gridBg(ctx);
    drawPlan(ctx, sm(u / 0.7), (u - 0.7) / 0.2, { top: [30, 110, 440, 560], front: [500, 110, 370, 560], side: [890, 110, 370, 560] });
  }
  function sTo3d(ctx, u) {
    var s = sm(u / 0.8), c = cam([0, 30, 1280, 690], 89.9 - (89.9 - 22) * s, -90 + 30 * s, 1.15);
    drawScene(ctx, c, scene(0, POD_TOP), { zscale: Math.max(s, 1e-3) });
    T(ctx, "z ← s · z(方程式),  s = " + s.toFixed(2), 0.03, 0.86, { size: 14, color: C.hud });
    T(ctx, "上面図 (x–y) を仰角 90° → 22° に回し、各部品の高さを復元", 0.03, 0.82, { size: 12 });
  }
  function sAssembly(ctx, u) {
    var n = ORDER.length, step = u * n, cur = Math.min(Math.floor(step), n - 1), f = sm((step - cur) / 0.6);
    var c = cam([0, 40, 820, 660], 20, -60 + 40 * u, 1.1), sc = scene(0, POD_TOP);
    for (var i = 0; i <= cur; i++) {
      var k = ORDER[i];
      if (i < cur) BP.drawPolys(ctx, c, sc[k], C[COLKEY[k]], { lw: 1, alpha: 0.9, r: 3.5 });
      else BP.drawPolys(ctx, c, sc[k], C[COLKEY[k]], { lw: 1.8, alpha: 0.25 + 0.75 * f, r: 4,
                                                          offset: EXPLODE[k].map(function (v) { return v * (1 - f); }) });
    }
    var key = ORDER[cur], card = CARD[key], col = key === "pod" ? C.hud : C[COLKEY[key]], a = 0.35 + 0.65 * sm((step - cur) / 0.25);
    BP.card(ctx, 0.64, 0.30, 0.34, 0.50, col);
    T(ctx, "部品 " + (cur + 1) + "/" + n, 0.655, 0.75, { size: 12, color: col, alpha: a });
    T(ctx, card[0], 0.655, 0.70, { size: 16, bold: true, alpha: a });
    card[1].forEach(function (l, j) { T(ctx, l, 0.655, 0.62 - j * 0.075, { size: 12.5, alpha: a }); });
    ORDER.forEach(function (k, i) {
      var done = i < cur || (i === cur && f > 0.99);
      T(ctx, (done ? "■ " : "□ ") + CARD[k][0].split(" (")[0], 0.655 + (i % 2) * 0.17, 0.24 - Math.floor(i / 2) * 0.037,
        { size: 10, color: done ? C.hud : C.grid });
    });
  }
  function hudZeta(ctx, sec) {
    var p = new BP.Plot(ctx, [50, 520, 330, 140], [0, 40], [-2.2, 3.2], "Riemann–Siegel Z(t)   φ = 11.7722 で Z = " + P.rsZ.toFixed(3));
    p.ticks(4, 2);
    p.line([0, 40], [0, 0], C.grid, 0.8);
    p.line(ZT, ZV, C.window, 1.2);
    p.line([P.phi, P.phi], [-2.2, 3.2], C.axis, 1, 1, [4, 3]);
    var tt = 0.5 + (sec * 4) % 39.5; p.dot(tt, BP.rsZ(tt), C.pod, 3.5);
  }
  function sActivate(ctx, u, sec) {
    var spin = 1 + 7 * sm(u), tRot = 2 * sec + 7 * sec * sec / 32, podZ = POD_TOP * (1 - sm((u - 0.1) / 0.55));
    var c = cam([160, 30, 820, 690], 18 + 6 * Math.sin(u * 3), -40 + 60 * u, 1.15), pulse = 0.5 + 0.5 * Math.sin(sec * 6);
    var coilW = 1 + 1.6 * pulse * sm(u * 2);
    drawScene(ctx, c, scene(tRot, podZ), { per: { j31: { lw: coilW }, j51: { lw: coilW }, j41: { lw: coilW },
                                                window: { alpha: 0.3 + 0.7 * pulse }, axis: { alpha: sm((u - 0.6) * 4) } } });
    hudZeta(ctx, sec);
    T(ctx, "ω 倍率  ×" + spin.toFixed(1), 0.74, 0.84, { size: 15, color: C.ring });
    T(ctx, "ポッド高度  " + podZ.toFixed(1) + " m", 0.74, 0.79, { size: 15, color: C.pod });
    T(ctx, "歳差 Ω = 3.70640 rad/s", 0.74, 0.74, { size: 13, color: C.hud });
    T(ctx, u < 0.65 ? "ポッド降下中" : (u < 0.85 ? "共鳴窓 同期" : "扉 開放"), 0.74, 0.68, { size: 17, color: C.warn, bold: true });
  }
  function tunnel(ctx, c, sec, alpha) {
    var a = [NH[1], -NH[0], 0], la = Math.hypot(a[0], a[1]); a = [a[0] / la, a[1] / la, 0];
    var b = [NH[1] * a[2] - NH[2] * a[1], NH[2] * a[0] - NH[0] * a[2], NH[0] * a[1] - NH[1] * a[0]];
    for (var k = 0; k < 14; k++) {
      var d = (k * 12 + sec * 40) % 170, r = 22 * Math.exp(-d / 90) + 3, pts = [];
      for (var i = 0; i < 60; i++) {
        var t = 2 * PI * i / 59;
        pts.push([d * NH[0] + r * (Math.cos(t) * a[0] + Math.sin(t) * b[0]), d * NH[1] + r * (Math.cos(t) * a[1] + Math.sin(t) * b[1]),
                  d * NH[2] + r * (Math.cos(t) * a[2] + Math.sin(t) * b[2])]);
      }
      BP.drawPolys(ctx, c, [pts], C.hud, { lw: 1, alpha: alpha * (1 - d / 170) });
    }
  }
  function sTransport(ctx, u, sec) {
    var trav = sm((u - 0.12) / 0.6), c = cam([200, 30, 880, 690], 15, -30 + 25 * u, 1.15 + 0.5 * trav, [0, 0, 38 * (1 - trav) + 20 * trav]);
    var sc = scene(30 + 12 * sec, 0), fade = 1 - 0.75 * trav;
    drawScene(ctx, c, sc, { skip: { pod: 1 }, alpha: 0.9 * fade });
    tunnel(ctx, c, sec, sm(u * 4));
    var pos = [NH[0] * 150 * trav, NH[1] * 150 * trav, NH[2] * 150 * trav];
    BP.drawPolys(ctx, c, sphere(P.podR, pos), C.pod, { lw: 1.4, alpha: u < 0.8 ? 1 : Math.max(0, 1 - (u - 0.8) * 5) });
    var flash = Math.max(0, 1 - Math.abs(u - 0.1) / 0.06);
    if (flash > 0) { ctx.save(); ctx.globalAlpha = 0.85 * flash; ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, BP.W, BP.H); ctx.restore(); }
    var te = BP.clamp((u - 0.12) / 0.8, 0, 1);
    T(ctx, "地球時間      t = " + te.toFixed(3) + " s", 0.03, 0.84, { size: 16 });
    T(ctx, "搭乗者時間  τ = " + (18 * te).toFixed(2) + " h", 0.03, 0.79, { size: 16, color: C.warn });
    T(ctx, "Γ = 64800   (地球の 1 秒 = 搭乗者の 18 時間)", 0.03, 0.73, { size: 12, color: C.hud });
    T(ctx, "ベガ (25.04 ly) 収縮距離 残り " + (3.656e9 * (1 - te)).toExponential(3) + " km", 0.03, 0.67, { size: 13 });
    T(ctx, "片道 3.3874 h (搭乗者時間)", 0.03, 0.63, { size: 12 });
    T(ctx, "n̂ = (0.86964, −0.25101, 0.42511) — 衝突で消えた運動量の方向", 0.03, 0.1, { size: 13, color: C.axis });
  }
  function sEnd(ctx, u, sec) {
    BP.gridBg(ctx);
    var c = cam([260, 40, 760, 470], 20, -60 + 20 * sec, 1.1);
    drawScene(ctx, c, scene(sec * 1.5, 0), { alpha: 0.6 * sm(u * 3) });
    var a = sm(u * 3 - 0.3);
    T(ctx, "方程式 2111 本 → 部品 10 点 → 平面図 → 3D → 組み立て → 起動", 0.5, 0.2, { size: 16, align: "center", alpha: a });
    T(ctx, "※ 論文の方程式に基づく思索的・フィクションの設計図 (幾何的な可視化) です。\n工学的に検証された装置ではなく、異次元への輸送を可能にするものではありません。",
      0.5, 0.11, { size: 12, align: "center", color: C.warn, alpha: a });
  }
  var SCENES = { title: sTitle, params: sParams, mapping: sMapping, plan: sPlan, to3d: sTo3d, assembly: sAssembly,
                 activate: sActivate, transport: sTransport, end: sEnd };

  function frame(ctx, sec) {
    var s = TL.at(sec);
    BP.clear(ctx);
    SCENES[s.name](ctx, s.u, s.local);
    if (s.name !== "title") BP.header(ctx, TITLES[s.name], "CONTACT TRANSPORTER", sec, TL.total);
    var edge = Math.min(s.local, s.dur - s.local);
    if (edge < 0.35) BP.fade(ctx, 1 - edge / 0.35);
  }

  function audio(sr) {
    var n = Math.floor(TL.total * sr), out = new Float32Array(n), a0 = TL.start("activate"), a1 = TL.start("transport"),
        burst = a1 + 1.4, endT = TL.start("end"), ph = 0, seed = 1;
    for (var i = 0; i < n; i++) {
      var t = i / sr, ramp = BP.clamp((t - a0) / (a1 - a0), 0, 1), f = 110 + 330 * ramp * ramp;
      ph += 2 * PI * f / sr;
      var v = 0.1 * Math.sin(2 * PI * 55 * t) + 0.05 * Math.sin(2 * PI * 82.5 * t) + 0.08 * ramp * Math.sin(ph);
      if (t > burst) { seed = (seed * 1103515245 + 12345) & 0x7fffffff; v += 0.2 * Math.exp(-(t - burst) * 3) * (seed / 0x7fffffff * 2 - 1); }
      if (t > burst && t < endT) v += 0.05 * Math.sin(2 * PI * (660 + 30 * Math.sin(t)) * t);
      out[i] = v * BP.clamp(t / 2, 0, 1) * BP.clamp((TL.total - t) / 2, 0, 1);
    }
    return out;
  }

  /* ---- PDF ---- */
  var PW = BP.PDF_W, PH = BP.PDF_H;
  function Tp(ctx, s, x, y, o) { T(ctx, s, x, y, o, PW, PH); }
  var NOTE = "※ 論文の方程式に基づく思索的・フィクションの設計図 (幾何的な可視化) です。工学的に検証された装置ではなく、異次元への輸送を可能にするものではありません。";
  function pcam(rect, elev, azim, zoom, center) {
    return new BP.Camera({ rect: rect, elev: elev, azim: azim, center: center || [0, 0, 38], scale: rect[3] / 250 * (zoom || 1) });
  }
  var pdfPages = [
    function (ctx) {
      Tp(ctx, "CONTACT TRANSPORTER", 0.05, 0.84, { size: 34, bold: true });
      Tp(ctx, "異次元への輸送機  3 次元設計図 (組立図・部品表・方程式対応表)", 0.05, 0.785, { size: 15, color: C.hud });
      ["原典: contact_blueprint.pdf  (量子プログラミング言語 Bada: contact_transporter/contact_blueprint.bada)",
       "原理: ジュネーブ CERN の衝突で粒子が消えた方向 = 異次元への扉",
       "   × 特殊相対論 (地球の 1 秒 = 搭乗者の 18 時間, Γ = 64800)",
       "   × 複素回転体 (コマ) の幾何学 (Θ = θ + iφ, φ = 11.7722)",
       "   × ガンマ関数におけるゼータ関数の大域的部分積分多様体 (Riemann–Siegel Z)",
       "   × Jones 多項式 = 設計図生成機能",
       "論文 15 本の全方程式 2111 本を 10 部品に割り当て"].forEach(function (l, i) { Tp(ctx, l, 0.05, 0.71 - i * 0.04, { size: 10.5 }); });
      drawScene(ctx, pcam([730, 250, 420, 520], 22, -58, 1.0), scene(4, 0), { lw: 0.8 });
      Tp(ctx, "目次", 0.05, 0.37, { size: 11, bold: true, color: C.hud });
      ["01 表紙", "02 設計パラメータ", "03 部品 ↔ 方程式 対応表", "04 三面図", "05 3D 等角図", "06 分解組立図・組立手順",
       "07 動作シーケンス", "08 方程式レジストリ抜粋", "09 注記"].forEach(function (t, i) {
        Tp(ctx, t, 0.05 + Math.floor(i / 5) * 0.2, 0.33 - (i % 5) * 0.035, { size: 9.5 });
      });
      Tp(ctx, NOTE, 0.03, 0.1, { size: 7.5, color: C.warn });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "1. 設計パラメータ", "Bada 実行結果 (レポート 1 章) とアプリ内の再計算");
      var rows = [
        ["① 衝突段", "√s / E_T^miss", "13.6 TeV / 1348.29 GeV", "Linac4 → PSB → PS → SPS → LHC"],
        ["", "扉の軸 n̂", "(0.86964, −0.25101, 0.42511)", "|n̂| = " + Math.hypot(P.nhat[0], P.nhat[1], P.nhat[2]).toFixed(5)],
        ["② 特殊相対論", "Γ", "18 h / 1 s = 64800", "再計算 " + (18 * 3600) + " ✓"],
        ["", "1 − β", "1.19075e−10", "再計算 " + (1 / (2 * P.Gamma * P.Gamma)).toExponential(5) + " ✓"],
        ["", "ラピディティ φ", "arcosh Γ = 11.772200", "再計算 " + Math.acosh(P.Gamma).toFixed(6) + " ✓"],
        ["", "ベガ 25.04 ly", "収縮 3.656e9 km, 片道 3.3874 h", "再計算 " + (25.04 * 9.4607e12 / P.Gamma).toExponential(4) + " km ✓"],
        ["②' 輸送計量", "T|ψ|", "1.763290", "x log x = 1 の根 1.763220"],
        ["③ 複素回転体", "θ₀ / ω", "0.523599 rad / 0.10472, 0.39241, 1.47043", "外 = π/30"],
        ["", "歳差 Ω", "Mgl/(I₃ω₃) = 3.70640 rad/s", ""],
        ["④ Γ・ζ 多様体", "θ(φ)", "−2.581360", "再計算 " + P.rsTheta.toFixed(6) + " ✓"],
        ["", "Z(φ)", "−1.334150", "再計算 " + P.rsZ.toFixed(6) + " ✓"],
        ["⑤ Jones", "V_3_1(t*)", "−0.116342 + 2.30908i", "再計算 " + cstr(VT["3_1"])],
        ["", "V_4_1(t*)", "3.56478", "再計算 " + VT["4_1"][0].toFixed(6)],
        ["", "V_5_1(t*)", "−2.81527 + 1.09654i", "再計算 " + cstr(VT["5_1"])],
        ["⑦ 部品寸法", "環 R 外/中/内", "60.088 / 47.431 / 37.440 m", "管径 2.066 m"],
        ["", "ポッド r / 塔高 / 井戸", "5.021 / 132.194 / 38.800 m", ""],
        ["", "Jones コイル R", "3_1: 70.269, 5_1: 56.215 m", "4_1 は床下"]
      ];
      var xs = [0.04, 0.17, 0.33, 0.62];
      ["段", "量", "値 (レポート)", "検算・備考"].forEach(function (h, j) { Tp(ctx, h, xs[j], 0.86, { size: 10.5, bold: true, color: C.hud }); });
      rows.forEach(function (r, i) {
        var y = 0.825 - i * 0.041;
        r.forEach(function (v, j) { Tp(ctx, v, xs[j], y, { size: 9.5, color: j ? C.fg : C.warn }); });
        BP.lineF(ctx, 0.035, y - 0.012, 0.96, y - 0.012, C.grid, 0.5, 1, PW, PH);
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "2. 部品 ↔ 方程式 対応表", "全方程式 " + REG.length + " 本を先頭タグで部品に割り当て (右列は件数と代表式 ID)");
      var rows = [["base", "基礎・床", ["□ = −(16πG/c⁴)·T_μν", "= κ·T_μν (OTHER 群)"], "床面 z = −38.8 m"],
                  ["well", "井戸 (輸送計量)", ["ds² = e^(−2πT|ψ|)[η+h̄]dx^μdx^ν + T²dψ²", "e^(−2πT|ψ|) = 1/Γ ⇒ T|ψ| = 1.76329"], "深さ 38.800 m"],
                  ["tower", "塔・ガントリー", ["Γ(s) = ∫₀^∞ e^(−x) x^(s−1) dx", "θ(φ) = arg Γ(1/4+iφ/2) − (φ/2)log π = −2.58136"], "塔高 132.194 m"],
                  ["ring", "ジンバル環 ×3", ["Θ = θ + iφ,  θ₀ = 0.523599", "ω (外,中,内) = 0.10472, 0.39241, 1.47043 rad/s"], "R 60.088/47.431/37.440 m"],
                  ["coil", "Jones コイル", ["V_3_1 = −t⁻⁴+t⁻³+t⁻¹  → R = 70.269", "V_5_1 = t²+t⁴−t⁵+t⁶−t⁷ → R = 56.215; 4_1 床下"], "t* = e^(iθ(φ))"],
                  ["window", "共鳴窓", ["Z(φ) = e^(iθ(φ)) ζ(1/2+iφ) = −1.33415", "min_α |V_K(e^(iα))| → 窓の角度"], "極小 α から配置"],
                  ["pod", "ポッド", ["Γ = 18h/1s = 64800, φ = arcosh Γ = 11.7722", "Ω = Mgl/(I₃ω₃) = 3.70640 rad/s"], "r = 5.021 m"],
                  ["axis", "扉の軸", ["√s = 13.6 TeV, E_T^miss = 1348.29 GeV", "n̂ = p_T^miss/|·| = (0.870, −0.251, 0.425)"], "衝突で粒子が消えた方向"]];
      ["No.", "部品", "支配方程式 (レポート 1 章)", "寸法", "タグ / 件数 / 代表式"].forEach(function (h, j) {
        Tp(ctx, h, [0.035, 0.07, 0.2, 0.6, 0.76][j], 0.86, { size: 10, bold: true, color: C.hud });
      });
      rows.forEach(function (r, i) {
        var y = 0.82 - i * 0.092, col = PCOL[r[0]];
        Tp(ctx, String(i + 1), 0.04, y, { size: 11, bold: true, color: col });
        Tp(ctx, r[1], 0.07, y, { size: 10.5, bold: true, color: col });
        r[2].forEach(function (e, j) { Tp(ctx, e, 0.2, y - j * 0.032, { size: 9 }); });
        Tp(ctx, r[3], 0.6, y, { size: 8.5 });
        var tags = Object.keys(TAG_PART).filter(function (t) { return TAG_PART[t] === r[0]; }).join(" ");
        var ids = REG.filter(function (e) { return e.part === r[0] && (e.st === "holds" || e.st === "calc"); }).slice(0, 4).map(function (e) { return e.id; });
        Tp(ctx, tags + "  —  " + (CUM[r[0]][REG.length - 1] || 0) + " 本", 0.76, y, { size: 8.5 });
        Tp(ctx, ids.join(", "), 0.76, y - 0.03, { size: 8, color: C.hud });
        BP.lineF(ctx, 0.03, y - 0.058, 0.965, y - 0.058, C.grid, 0.5, 1, PW, PH);
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "3. 三面図 (単位 m)", "上面図・正面図・側面図 — 各寸法はレポートの Bada 実行結果");
      drawPlan(ctx, 1, 1, { top: [40, 130, 420, 560], front: [480, 130, 320, 560], side: [820, 130, 320, 560] }, 1);
      [["ジンバル環", C.ring], ["ポッド", C.pod], ["塔・床", C.tower], ["Jones 3_1", C.j31], ["Jones 5_1", C.j51], ["Jones 4_1", C.j41],
       ["扉の軸", C.axis], ["共鳴窓", C.window], ["井戸", C.well]].forEach(function (l, i) {
        Tp(ctx, "■ " + l[0], 0.04 + i * 0.068, 0.1, { size: 8, color: l[1] });
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "4. 3D 等角図", "平面図の各部品を z 方向に復元した 3 次元形状 (3 方向から)");
      var sc = scene(4, 0);
      drawScene(ctx, pcam([20, 120, 580, 640], 22, -58, 1.05), sc, { lw: 0.8 });
      drawScene(ctx, pcam([620, 100, 520, 330], 5, -90, 1.05), sc, { lw: 0.7 });
      drawScene(ctx, pcam([620, 440, 520, 330], 60, -30, 1.05, [0, 0, 10]), sc, { lw: 0.7 });
      Tp(ctx, "等角 (仰角 22°, 方位 −58°)", 0.03, 0.83, { size: 9, color: C.hud });
      Tp(ctx, "正面透視 (仰角 5°)", 0.54, 0.86, { size: 9, color: C.hud });
      Tp(ctx, "俯瞰 (仰角 60°)", 0.54, 0.46, { size: 9, color: C.hud });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "5. 分解組立図・組立手順", "部品番号順に組み立てる (番号 = 組立順)");
      var c = new BP.Camera({ rect: [10, 90, 680, 700], elev: 18, azim: -58, center: [0, 0, 50], scale: 700 / 420 }), sc = scene(4, POD_TOP);
      ORDER.forEach(function (k, i) {
        var off = EXPLODE[k].map(function (v) { return v * 0.55; });
        BP.drawPolys(ctx, c, sc[k], C[COLKEY[k]], { lw: 0.8, offset: off, r: 3 });
        var cen = BP.centroid(sc[k]), p = c.p([cen[0] + off[0], cen[1] + off[1], cen[2] + off[2]]);
        BP.balloon(ctx, p[0], p[1], i + 1, C[COLKEY[k]]);
      });
      var steps = [["基礎・床", "床面 z = −38.8 m に円形プラットフォームを敷設 (R 66–90 m)"],
                   ["井戸", "輸送計量 ds² の漏斗。深さ 38.8 m、底径 30 m"],
                   ["塔・ガントリー", "4 脚 (±48 m) を高さ 132.194 m まで建て、頂部アームを中心に集める"],
                   ["ジンバル環", "外環 60.088 → 中環 47.431 → 内環 37.440 を入れ子に。θ₀ = 30°"],
                   ["Jones 3_1", "三葉結び目コイル R 70.269 m を赤道面に巻く"],
                   ["Jones 5_1", "5_1 コイル R 56.215 m を z = +70 m に巻く"],
                   ["Jones 4_1", "8 の字結び目コイルを床下 (z ≈ −25 m) に設置"],
                   ["共鳴窓", "|V_K(e^(iα))| 極小の角度 " + WINDOWS.length + " 箇所にセンサを配置"],
                   ["ポッド", "r = 5.021 m の球殻。塔頂から吊り下げ (z ≈ 118 m)"],
                   ["扉の軸", "n̂ = (0.870, −0.251, 0.425) に照準を合わせる"]];
      steps.forEach(function (s, i) {
        var y = 0.85 - i * 0.07;
        Tp(ctx, (i + 1) + ". " + s[0], 0.61, y, { size: 10, bold: true });
        Tp(ctx, s[1], 0.625, y - 0.027, { size: 8.3 });
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "6. 動作シーケンス (起動・輸送)", "動画の「起動」「輸送」シーンに対応");
      var p1 = new BP.Plot(ctx, [70, 150, 460, 220], [0, 40], [-2.2, 3.2], "臨界線上の Riemann–Siegel Z(t) — φ = 11.7722 で Z = " + P.rsZ.toFixed(3));
      p1.ticks(8, 4); p1.line(ZT, ZV, C.window, 1.2); p1.line([P.phi, P.phi], [-2.2, 3.2], C.axis, 1, 1, [4, 3]);
      var p2 = new BP.Plot(ctx, [640, 150, 460, 220], [0, 360], [0, 5.2], "|V_K(e^(iα))| — 極小が扉の共鳴角 (● = 窓)");
      p2.ticks(6, 4, function (v) { return Math.round(v) + "°"; });
      [["3_1", C.j31], ["4_1", C.j41], ["5_1", C.j51]].forEach(function (k) {
        p2.line(ALPHA.map(function (a) { return a * 180 / PI; }), VABS[k[0]], k[1], 1.1);
      });
      WINDOWS.forEach(function (w) { p2.dot(w[1] * 180 / PI, w[2], C.window, 3); });
      var t = BP.linspace(0, 16, 100), p3 = new BP.Plot(ctx, [70, 470, 460, 220], [0, 16], [0, 12.5], "起動: 角速度 ω × 倍率 (外・中・内) と ポッド高度 (破線, 右軸 0–118 m)");
      p3.ticks(8, 5);
      [C.ring, C.warn, C.window].forEach(function (col, j) { p3.line(t, t.map(function (x) { return P.omega[j] * (1 + 7 * sm(x / 16)); }), col, 1.2); });
      p3.line(t, t.map(function (x) { return 12.5 * (1 - sm((x / 16 - 0.1) / 0.55)); }), C.pod, 1, 1, [5, 3]);
      var p4 = new BP.Plot(ctx, [640, 470, 460, 220], [0, 1], [0, 18], "輸送: 地球時間 t [s] と搭乗者時間 τ [h] (Γ = 64800)");
      p4.ticks(5, 6); p4.line([0, 1], [0, 18], C.warn, 1.6);
      Tp(ctx, "① ポッド降下 → ② 環の回転上昇 (ω×1→×8) → ③ Jones コイル励磁 → ④ 共鳴窓同期 (Z(φ)) → ⑤ 扉開放 → ⑥ n̂ 方向へ輸送",
         0.06, 0.475, { size: 9, color: C.hud });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "7. 方程式レジストリ抜粋 (数値が成立・評価された式)", "各部品 4 本ずつ");
      var y = 0.86;
      PARTS.forEach(function (p) {
        Tp(ctx, p[1], 0.035, y, { size: 9.5, bold: true, color: p[2] }); y -= 0.024;
        REG.filter(function (e) { return e.part === p[0] && (e.st === "holds" || e.st === "calc"); }).slice(0, 4).forEach(function (e) {
          Tp(ctx, e.id + "  [" + e.st + "]  " + (e.eq.length < 118 ? e.eq : e.eq.slice(0, 117) + "…"), 0.05, y, { size: 7.3 }); y -= 0.02;
        });
        y -= 0.006;
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "8. 注記");
      ["・本図面は contact_blueprint.pdf の数値 (Bada 実行結果) を唯一の寸法根拠とし、形状の配置は可視化のための解釈である。",
       "・部品への方程式割り当ては各式の先頭タグによる: ROT→環, SR/QUANTUM→ポッド, GAMMA/BETA→塔, ZETA→共鳴窓,",
       "   JONES→コイル, MANIFOLD/ENTROPY→井戸, TRANSPORT→扉の軸, OTHER→基礎。",
       "・θ(φ), Z(φ) はアプリ内で再計算しレポート値と有効数字 6 桁で一致。V_K(t*) は 4 桁以上で一致 (V_3_1 実部: 再計算 −0.116358 / レポート −0.116342)。",
       "・共鳴窓の角度は |V_K(e^(iα))| の極小 (α ∈ [0, 2π), 0.1° 刻み) から求めた。",
       "・生成: 輸送機設計図作成ソフト (Bada Blueprint Studio)", "", NOTE].forEach(function (l, i) {
        Tp(ctx, l, 0.05, 0.84 - i * 0.05, { size: 10, color: l === NOTE ? C.warn : C.fg });
      });
    }
  ];

  root.BP_APP = {
    id: "transporter", title: "輸送機設計図作成ソフト", subtitle: "CONTACT TRANSPORTER — 方程式 2111 本から異次元輸送機の 3D 設計図と動画を生成",
    brand: "CONTACT TRANSPORTER — 異次元への輸送機 3D 設計図", pdfTitle: "CONTACT TRANSPORTER 3D Blueprint",
    fileBase: "contact_transporter", timeline: TL, sceneLabels: LABELS, frame: frame, audio: audio, pdfPages: pdfPages,
    aboutHtml: "原典: contact_blueprint.pdf (Bada: contact_transporter)。方程式 " + REG.length +
      " 本を部品に割り当て、平面図 → 3D → 組み立て → 起動・輸送を描きます。<br>※ 論文の方程式に基づく思索的・フィクションの設計図です。",
    _test: { P: P, VT: VT, WINDOWS: WINDOWS, REG: REG, CUM: CUM }
  };
})(typeof window !== "undefined" ? window : globalThis);
