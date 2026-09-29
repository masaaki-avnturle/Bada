/*
 * ufo.js — UFO 設計図作成ソフト (反重力機)
 *   contact_blueprint.pdf の方程式 UFO.1〜UFO.26 と src/UFO_OS.om から、
 *   方程式 → 部品 → 平面図 → 3D → 組み立て → 飛行 (制御ループが毎秒方程式を評価) の動画と設計図 PDF を生成。
 *   Python 版 (ufo_model.py / ufo_video.py / ufo_pdf.py) の移植。外形寸法は図解用。
 */
(function (root) {
  "use strict";
  var BP = root.BP, C = BP.C, T = BP.text, sm = BP.smooth, PI = Math.PI;

  /* ---- 方程式 (UFO.1, 3, 11, 13, 14, 19, 24) ---- */
  var G = 6.674e-11, ME = 5.972e24, R0 = 6.371e6, m = 1.2e4, c = 299792458, vref = 1e4;
  function xcoord(h) { return 2 * Math.sqrt(R0 / (R0 + h)); }          /* UFO.14: x = manifold_coord(r0/r) */
  function lift(h) { var x = xcoord(h); return Math.cosh(x * Math.log(x)); } /* UFO.11/19/23 */
  function geff(h) { return G * ME / Math.pow(R0 + h, 2); }
  function U(h) { return G * ME * m / (R0 + (h || 0)); }                  /* UFO.1 */
  function accel(h) { return (lift(h) - 1) * geff(h); }                   /* UFO.19 */
  function simulate() {                                                   /* UFO.24 */
    var h = 0, v = 0, rows = [{ k: 0, h: 0, v: 0, x: xcoord(0), L: lift(0), a: accel(0), Eag: U(0) * lift(0) }];
    for (var k = 1; k <= 10; k++) {
      v += accel(h); h += v;
      rows.push({ k: k, h: h, v: v, x: xcoord(h), L: lift(h), a: accel(h), Eag: U(h) * lift(h) });
    }
    return rows;
  }
  var SIM = simulate();
  var V = {
    U: U(0), L0: lift(0), Eag: U(0) * lift(0), a0: accel(0), Eperp: m * c * c - 0.5 * m * vref * vref,
    L1: lift(1e3), L5: lift(5e3), L20: lift(2e4), L100: lift(1e5), h10: SIM[10].h, v10: SIM[10].v,
    dmu: 1 / Math.pow(2 * Math.log(2), 2), beta: 1 * 2 / 24, delta: Math.exp(PI) - Math.pow(PI, Math.E), eneg: Math.exp(-2 * Math.log(2))
  };
  var RES = []; (function () { var r = 1e6; RES.push(1); for (var i = 0; i < 10; i++) { r -= 5; RES.push(r / 1e6); } })();

  var COL = { hull: "#b8c7e0", ring: "#f5b942", core: "#ff6b5b", res: "#4fd6e0", sensor: "#7fb2ff", fc: "#ffd166",
              tuner: "#c28bff", stab: "#9fe8ff", port: "#ffa040", safe: "#7ee787" };
  var PARTS = [
    ["hull", "船体 (円盤)", ["UFO.3", "UFO.16"], ["E⊥ = mc² − ½mv²", "m = 1.2×10⁴ kg, E⊥ ≈ 1.079×10²¹ J"], "直径 16 m / 厚さ 2.4 m (図解)"],
    ["ring", "反重力リング", ["UFO.2", "UFO.11"], ["□ag(x) = 2(sin(i·x log x) + cos(i·x log x))", "α_ag(x) = Re[□ag]/2 = cosh(x log x) ≥ 1"], "トーラス R = 6.5 m"],
    ["core", "重力結合コア", ["UFO.1", "UFO.13", "UFO.15"], ["U = GMm/r = 7.507×10¹¹ J", "E_ag = U·α_ag = 1.595×10¹² J,  E_ag ≥ U"], "中心柱 r = 0.9 m"],
    ["res", "真空エネルギー貯槽", ["UFO.4", "UFO.12", "UFO.17", "UFO.25"], ["□dal(x) = cos(i·x log x) − i·sin(i·x log x) = x^x", "E_vac = ρ·x^x ;  5 倍×10 回で残量 ≥ 99.9%"], "球 r = 1.6 m"],
    ["sensor", "多様体座標センサ", ["UFO.5", "UFO.6", "UFO.7", "UFO.14", "UFO.21"], ["x = manifold_coord(r0/r) = 2√(r0/r) (地表 x = 2)", "dμ(x) = 1/(x log x)²,  x log x → 0 (x→1)"], "マスト高 2.2 m"],
    ["fc", "飛行制御 (UFO_OS)", ["UFO.19", "UFO.23", "UFO.24"], ["L = E_ag/U = cosh(x log x) = 2.125 (地表)", "a = (L − 1)·g_eff = 11.047 m/s²"], "controlGravityDrive()"],
    ["tuner", "ζ・β 調律器", ["UFO.8", "UFO.9"], ["ζ(s) = β(p,q)/log x", "β(p,q) = Γ(p)Γ(q)/Γ(p+q) = 1/12"], "3 連リング"],
    ["stab", "エントロピー姿勢安定器", ["UFO.10"], ["Ξ = β(H+1, M+1)/log(N+1) = 0.0056407"], "外周ジャイロ 8 基"],
    ["port", "量子入出力ポート", ["UFO.20", "UFO.22"], ["← : π(χ,x),   ›- : e^(−x log x) = 0.25"], "底面 3 基 (120°)"],
    ["safe", "安定条件モニタ", ["UFO.18", "UFO.26"], ["e^π ≈ π^e:  Δ = e^π − π^e = 0.6815", "Δ < 1 で運転許可"], "ドーム頂部灯"]
  ];
  var NAME = {}, EQ_PART = {};
  PARTS.forEach(function (p) { NAME[p[0]] = p[1]; p[2].forEach(function (id) { EQ_PART[id] = p[0]; }); });
  var ORDER = ["hull", "core", "res", "ring", "tuner", "stab", "port", "sensor", "fc", "safe"];
  var EQS = (root.BP_REGISTRY || []).map(function (r) { return { id: r[0], st: r[1], eq: r[3], part: EQ_PART[r[0]] || "fc" }; });
  var UFO_OS = [["def controlGravityDrive() {", ""], ["  let x = manifold_coord(r0 / r)", "UFO.14"], ["  let L = cosh(x * log(x))", "UFO.11"],
                ["  let g = G * M / r^2", "UFO.19"], ["  let a = (L - 1) * g", "UFO.19"], ["  v = v + a * dt ; h = h + v * dt", "UFO.24"],
                ["  assert E_ag >= U_grav", "UFO.15"], ["  assert reservoir >= 0.999", "UFO.25"], ["  assert exp(pi) - pi^e < 1", "UFO.26"], ["}", ""]];

  /* ---- 幾何 (図解寸法 m) ---- */
  function revolve(rs, zs, nl) {
    var out = [];
    for (var i = 0; i < nl; i++) {
      var a = PI * i / nl;
      [1, -1].forEach(function (s) { out.push(rs.map(function (r, j) { return [s * r * Math.cos(a), s * r * Math.sin(a), zs[j]]; })); });
    }
    return out;
  }
  function prof(r) { return 1.2 * Math.pow(Math.max(0, 1 - (r / 8) * (r / 8)), 0.8); }
  function torus(R, rr, zc) {
    var out = [];
    for (var j = 0; j < 4; j++) { var a = 2 * PI * j / 4; out.push(BP.circle(R + rr * Math.cos(a), zc + rr * Math.sin(a), 120)); }
    for (var k = 0; k < 12; k++) {
      var t = 2 * PI * k / 12;
      out.push(BP.linspace(0, 2 * PI, 20).map(function (s) { return [(R + rr * Math.cos(s)) * Math.cos(t), (R + rr * Math.cos(s)) * Math.sin(t), zc + rr * Math.sin(s)]; }));
    }
    return out;
  }
  function sphere(r, cc, nl, nm) {
    var out = [];
    BP.linspace(-PI / 2, PI / 2, nl + 2).slice(1, nl + 1).forEach(function (la) { out.push(BP.circle(r * Math.cos(la), cc[2] + r * Math.sin(la), 40, cc[0], cc[1])); });
    for (var k = 0; k < nm; k++) { var lo = PI * k / nm; out.push(BP.shift(BP.apply(BP.rz(lo), BP.circle(r, 0, 40, 0, 0, "xz")), cc)); }
    return out;
  }
  function geometry() {
    var g = {}; ORDER.forEach(function (k) { g[k] = []; });
    var rs = BP.linspace(0, 8, 40);
    g.hull = g.hull.concat(revolve(rs, rs.map(prof), 8), revolve(rs, rs.map(function (r) { return -prof(r); }), 8));
    [2.5, 5, 7, 8].forEach(function (r) { g.hull.push(BP.circle(r, prof(r))); g.hull.push(BP.circle(r, -prof(r))); });
    var tt = BP.linspace(0, PI / 2, 20);
    for (var i = 0; i < 6; i++) {
      var a = PI * i / 6;
      [1, -1].forEach(function (s) { g.hull.push(tt.map(function (t) { return [s * 2.6 * Math.cos(t) * Math.cos(a), s * 2.6 * Math.cos(t) * Math.sin(a), 1.1 + 1.8 * Math.sin(t)]; })); });
    }
    g.ring = torus(6.5, 0.45, -1.1);
    g.core.push(BP.circle(0.9, -1)); g.core.push(BP.circle(0.9, 2.2));
    for (var k = 0; k < 6; k++) { var b = 2 * PI * k / 6; g.core.push([[0.9 * Math.cos(b), 0.9 * Math.sin(b), -1], [0.9 * Math.cos(b), 0.9 * Math.sin(b), 2.2]]); }
    g.res = sphere(1.6, [0, 0, -2.2], 5, 6);
    [[0.2, 4], [0.45, 3.6], [0.7, 3.2]].forEach(function (q) { g.tuner.push(BP.circle(q[1], q[0])); });
    for (var s = 0; s < 8; s++) {
      var a2 = 2 * PI * s / 8, cx = 7.3 * Math.cos(a2), cy = 7.3 * Math.sin(a2);
      g.stab.push(BP.circle(0.35, 0, 20, cx, cy)); g.stab.push([[cx, cy, -0.35], [cx, cy, 0.35]]);
    }
    [PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3].forEach(function (a3) {
      var px = 3.5 * Math.cos(a3), py = 3.5 * Math.sin(a3);
      g.port.push(BP.circle(0.5, -1.05, 24, px, py)); g.port.push([[px, py, -1.05], [px, py, -1.7]]);
    });
    g.sensor.push([[0, 0, 2.9], [0, 0, 5.1]]); g.sensor.push(BP.circle(0.6, 4.3, 30)); g.sensor.push(BP.circle(0.35, 4.8, 30));
    [1.3, 1.9].forEach(function (z) { g.fc.push([[-0.8, -0.5, z], [0.8, -0.5, z], [0.8, 0.5, z], [-0.8, 0.5, z], [-0.8, -0.5, z]]); });
    g.safe = sphere(0.25, [0, 0, 5.3], 3, 3);
    return g;
  }
  var GEOM = geometry();
  function cam(rect, elev, azim, zoom, center) {
    return new BP.Camera({ rect: rect, elev: elev, azim: azim, center: center || [0, 0, 0.5], scale: rect[3] / 15 * (zoom || 1) });
  }
  function drawAll(ctx, c, o) {
    o = o || {};
    ORDER.forEach(function (k) {
      BP.drawPolys(ctx, c, GEOM[k], COL[k], { lw: (o.lw || 0.9) + (k === "ring" ? 1.8 * (o.glow || 0) : 0), alpha: o.alpha === undefined ? 1 : o.alpha,
                                             zscale: o.zscale, offset: o.offset ? o.offset[k] : undefined });
    });
  }

  var TL = new BP.Timeline([["title", 5], ["params", 10], ["mapping", 12], ["plan", 10], ["to3d", 8], ["assembly", 30], ["flight", 28], ["end", 7]]);
  var TITLES = { params: "1. 反重力の方程式 (UFO.1–26) と再計算", mapping: "2. 方程式 26 本 → 部品への対応", plan: "3. 平面図 (三面図)  単位 m",
                 to3d: "4. 平面図 → 3D 変換", assembly: "5. 組み立て", flight: "6. 飛行 — 制御ループが毎秒方程式を評価して上昇" };
  var LABELS = { title: "タイトル", params: "方程式", mapping: "方程式→部品", plan: "平面図", to3d: "3D 変換", assembly: "組み立て", flight: "飛行", end: "終了" };

  function sTitle(ctx, u, sec) {
    BP.gridBg(ctx);
    drawAll(ctx, cam([320, 260, 640, 400], 18, -60 + 25 * sec, 1.1), { lw: 0.7, alpha: 0.4 * sm(u * 3) });
    var a = sm(u * 2.5);
    T(ctx, "UFO BLUEPRINT", 0.5, 0.78, { size: 46, bold: true, align: "center", alpha: a });
    T(ctx, "反重力機 — 方程式が使われる 3D 設計図", 0.5, 0.69, { size: 22, align: "center", color: C.hud, alpha: a });
    T(ctx, "原典: contact_blueprint.pdf の方程式 UFO.1–UFO.26 / src/UFO_OS.om", 0.5, 0.08, { size: 13, align: "center", alpha: sm(u * 2.5 - 0.6) });
  }
  function e5(v) { return v.toExponential(5).replace("e+", "e+"); }
  var PROWS = [
    ["UFO.1", "U = GMm/r", e5(V.U) + " J", "7.50723e+11", COL.core],
    ["UFO.3", "E⊥ = mc² − ½mv²", e5(V.Eperp) + " J", "1.07851e+21", COL.hull],
    ["UFO.11", "α_ag = cosh(x log x),  x = 2", V.L0.toFixed(4), "L = 2.125", COL.ring],
    ["UFO.13", "E_ag = (GMm/r)·cosh(x log x)", e5(V.Eag) + " J", "1.59529e+12", COL.core],
    ["UFO.19", "a = (L − 1)·g_eff", V.a0.toFixed(3) + " m/s²", "11.047", COL.fc],
    ["UFO.23", "L(1 km), L(5 km)", V.L1.toFixed(5) + ", " + V.L5.toFixed(5), "2.12450, 2.12251", COL.sensor],
    ["UFO.23", "L(20 km), L(100 km)", V.L20.toFixed(5) + ", " + V.L100.toFixed(5), "2.11510, 2.07677", COL.sensor],
    ["UFO.24", "10 ステップ後の高度・速度", V.h10.toFixed(1) + " m, " + V.v10.toFixed(2) + " m/s", "607.6 m, 110.46 m/s", COL.fc],
    ["UFO.26", "Δ = e^π − π^e < 1", V.delta.toFixed(4), "0.6815", COL.safe]
  ];
  function sParams(ctx, u) {
    BP.gridBg(ctx);
    [["式 ID", 0.04], ["方程式", 0.13], ["アプリ内で再計算", 0.5], ["レポート値", 0.76]].forEach(function (h) { T(ctx, h[0], h[1], 0.86, { size: 12, color: C.hud }); });
    PROWS.forEach(function (r, i) {
      var a = sm((u * 1.3 - i * 0.09) * 5), y = 0.8 - i * 0.078;
      T(ctx, r[0], 0.04, y, { size: 14, bold: true, color: r[4], alpha: a });
      T(ctx, r[1], 0.13, y, { size: 14, alpha: a });
      T(ctx, r[2], 0.5, y, { size: 13, alpha: a });
      T(ctx, r[3] + "  ✓", 0.76, y, { size: 12, color: C.ok, alpha: a });
    });
    T(ctx, "x = manifold_coord(r0/r) = 2√(r0/r) (地表 x = 2) とすると、レポートの L(h) と上昇軌道を再現", 0.04, 0.06, { size: 11, color: C.hud, alpha: sm(u * 3 - 2) });
  }
  function sMapping(ctx, u) {
    BP.gridBg(ctx);
    var n = Math.min(EQS.length, Math.floor(BP.clamp(sm(u * 1.1), 0, 1) * EQS.length + 0.999)), ys = {};
    PARTS.forEach(function (p, i) {
      var y = 0.86 - i * 0.08, cnt = EQS.slice(0, n).filter(function (e) { return e.part === p[0]; }).length;
      ys[p[0]] = y;
      if (cnt) BP.rectF(ctx, 0.71, y - 0.028, 0.26, 0.058, { fill: COL[p[0]], fillAlpha: 0.15 });
      BP.rectF(ctx, 0.71, y - 0.028, 0.26, 0.058, { stroke: COL[p[0]], lw: 1.3 });
      T(ctx, p[1], 0.72, y - 0.01, { size: 12 });
      T(ctx, String(cnt), 0.96, y - 0.01, { size: 13, color: COL[p[0]], align: "right", bold: true });
    });
    EQS.slice(0, n).forEach(function (e, j) {
      var y = 0.885 - j * 0.0325, txt = e.eq.length < 58 ? e.eq : e.eq.slice(0, 57) + "…";
      T(ctx, e.id, 0.03, y - 0.008, { size: 9.5, color: COL[e.part] });
      T(ctx, txt, 0.09, y - 0.008, { size: 9.5 });
      if (j >= n - 4) BP.lineF(ctx, 0.56, y, 0.705, ys[e.part], COL[e.part], 1.1, 0.8);
    });
  }
  function drawPlan(ctx, prog, dims, rects, fsz) {
    var parts = ORDER.map(function (k) { return { polys: GEOM[k], color: COL[k] }; });
    var t = BP.orthoView(ctx, rects.top, parts, "top", [-9.5, 9.5], [-9.5, 9.5], prog, "上面図 (x–y)", fsz);
    var f = BP.orthoView(ctx, rects.front, parts, "front", [-9.5, 9.5], [-4.5, 6.5], prog, "正面図 (x–z)", fsz);
    BP.orthoView(ctx, rects.side, parts, "side", [-9.5, 9.5], [-4.5, 6.5], prog, "側面図 (y–z)", fsz);
    if (dims > 0) {
      var a = sm(dims), o = { size: 9 * (fsz || 1), color: C.warn, alpha: a };
      BP.arrow2(ctx, t.X(-8), t.Y(0), t.X(8), t.Y(0), C.warn, a); BP.textPx(ctx, "直径 16", t.X(-3), t.Y(0.5), o);
      BP.textPx(ctx, "反重力リング R 6.5", t.X(2.5), t.Y(-6.2), { size: o.size, color: COL.ring, alpha: a });
      BP.arrow2(ctx, f.X(-8.8), f.Y(5.1), f.X(-8.8), f.Y(-3.8), C.warn, a); BP.textPx(ctx, "全高 8.9", f.X(-8.5), f.Y(4.2), o);
      BP.textPx(ctx, "貯槽 r 1.6", f.X(2.2), f.Y(-3.6), { size: o.size, color: COL.res, alpha: a });
      BP.textPx(ctx, "安定灯", f.X(0.5), f.Y(5.4), { size: o.size, color: COL.safe, alpha: a });
    }
  }
  function sPlan(ctx, u) {
    BP.gridBg(ctx);
    drawPlan(ctx, sm(u / 0.7), (u - 0.7) / 0.2, { top: [20, 100, 440, 560], front: [480, 200, 390, 330], side: [880, 200, 390, 330] });
    if (u > 0.75) T(ctx, "寸法はレポートに記載がないため図解用。質量 m = 1.2×10⁴ kg は UFO.16 より。", 0.38, 0.14, { size: 11, color: C.warn, alpha: sm((u - 0.75) * 6) });
  }
  function sTo3d(ctx, u) {
    var s = sm(u / 0.8);
    drawAll(ctx, cam([0, 60, 1280, 660], 89.9 - (89.9 - 22) * s, -90 + 30 * s, 0.62), { zscale: Math.max(s, 1e-3) });
    T(ctx, "z ← s · z(断面),  s = " + s.toFixed(2), 0.03, 0.86, { size: 14, color: C.hud });
    T(ctx, "上面図を起こしてレンズ断面を回転体として復元", 0.03, 0.82, { size: 12 });
  }
  var EXPLODE = { hull: [0, 0, 0], core: [0, 0, 8], res: [0, 0, -8], ring: [0, 0, -6], tuner: [0, 0, 6], stab: [10, 0, 0], port: [0, 0, -9],
                  sensor: [0, 0, 9], fc: [-10, 0, 4], safe: [0, 0, 10] };
  function sAssembly(ctx, u) {
    var n = ORDER.length, step = u * n, cur = Math.min(Math.floor(step), n - 1), f = sm((step - cur) / 0.6);
    var cc = cam([0, 60, 780, 620], 22, -60 + 40 * u, 0.85);
    for (var i = 0; i <= cur; i++) {
      var k = ORDER[i];
      if (i < cur) BP.drawPolys(ctx, cc, GEOM[k], COL[k], { lw: 0.9, alpha: 0.9 });
      else BP.drawPolys(ctx, cc, GEOM[k], COL[k], { lw: 1.6, alpha: 0.25 + 0.75 * f, offset: EXPLODE[k].map(function (v) { return v * (1 - f); }) });
    }
    var key = ORDER[cur], p = PARTS.filter(function (q) { return q[0] === key; })[0], col = COL[key], a = 0.35 + 0.65 * sm((step - cur) / 0.25);
    BP.card(ctx, 0.6, 0.30, 0.38, 0.52, col);
    T(ctx, "部品 " + (cur + 1) + "/" + n + "   " + p[2].join(", "), 0.615, 0.77, { size: 11, color: col, alpha: a });
    T(ctx, p[1], 0.615, 0.72, { size: 16, bold: true, alpha: a });
    p[3].concat([p[4]]).forEach(function (l, j) { T(ctx, l, 0.615, 0.64 - j * 0.08, { size: 12, alpha: a }); });
    ORDER.forEach(function (k, i) {
      var done = i < cur || (i === cur && f > 0.99);
      T(ctx, (done ? "■ " : "□ ") + NAME[k].split(" (")[0], 0.615 + (i % 2) * 0.18, 0.24 - Math.floor(i / 2) * 0.037, { size: 10, color: done ? C.hud : C.grid });
    });
  }
  function simState(t) {
    var k = Math.max(0, Math.min(9, Math.floor(t))), f = BP.clamp(t - k, 0, 1), a = SIM[k], b = SIM[k + 1], o = {};
    ["h", "v", "x", "L", "a", "Eag"].forEach(function (key) { o[key] = a[key] + (b[key] - a[key]) * f; });
    o.k = k + (f >= 1 ? 1 : 0);
    return o;
  }
  function sFlight(ctx, u, sec) {
    var tsim = BP.clamp((u - 0.12) / 0.7, 0, 1) * 10, st = simState(tsim);
    var glow = sm(u / 0.12) * (0.6 + 0.4 * Math.sin(sec * 9));
    var cc = cam([0, 70, 740, 650], 14, -60 + 15 * u, 0.72, [0, 0, -3.5]);
    var ground = -3.5 - st.h / 60;
    if (ground > -14) {
      var gl = [];
      BP.linspace(-10, 10, 11).forEach(function (v) { gl.push([[v, -10, ground], [v, 10, ground]]); gl.push([[-10, v, ground], [10, v, ground]]); });
      BP.drawPolys(ctx, cc, gl, C.grid, { lw: 0.9 });
    }
    drawAll(ctx, cc, { glow: glow });
    var beams = [];
    for (var i = 0; i < 16; i++) {
      var aa = 2 * PI * i / 16, x0 = 6.5 * Math.cos(aa), y0 = 6.5 * Math.sin(aa), ln = 2 + 2 * (st.L - 1);
      beams.push([[x0, y0, -1.5], [0.9 * x0, 0.9 * y0, -1.5 - ln]]);
    }
    BP.drawPolys(ctx, cc, beams, COL.ring, { lw: 0.8, alpha: 0.5 * glow });
    T(ctx, "UFO_OS.om  controlGravityDrive()", 0.58, 0.895, { size: 12, color: C.hud });
    var active = (u > 0.12 && u < 0.82) ? 1 + Math.floor((sec * 3) % 5) : (u >= 0.82 ? 6 + Math.floor((sec * 2) % 3) : -1);
    UFO_OS.forEach(function (l, i) {
      var y = 0.86 - i * 0.031, on = i === active;
      T(ctx, l[0], 0.58, y, { size: 10, color: on ? C.warn : C.fg, alpha: on ? 1 : 0.75 });
      if (l[1]) T(ctx, l[1], 0.9, y, { size: 9, color: on ? C.warn : C.grid });
    });
    var y0 = 0.44;
    T(ctx, "ステップ k = " + Math.min(st.k, 10) + " / 10   (dt = 1 s)", 0.58, y0 + 0.045, { size: 13, color: C.hud });
    [["x = 2√(r0/(r0+h)) = " + st.x.toFixed(6), COL.sensor], ["L = cosh(x log x) = " + st.L.toFixed(5), COL.ring],
     ["a = (L − 1)·g_eff = " + st.a.toFixed(4) + " m/s²", COL.fc], ["E_ag = U·L = " + st.Eag.toExponential(5) + " J  ≥ U ✓", COL.core],
     ["v = " + st.v.toFixed(2) + " m/s     h = " + st.h.toFixed(1) + " m", C.fg]].forEach(function (r, i) {
      T(ctx, r[0], 0.58, y0 - i * 0.045, { size: 13, color: r[1] });
    });
    var pl = new BP.Plot(ctx, [800, 630, 430, 70], [0, 10], [0, 650], "高度 h [m] — 10 s 後 607.5 m (UFO.24)");
    pl.ticks(5, 2);
    pl.line(SIM.map(function (r) { return r.k; }), SIM.map(function (r) { return r.h; }), C.grid, 1);
    var ks = BP.linspace(0, tsim, 40); pl.line(ks, ks.map(function (t) { return simState(t).h; }), C.warn, 2);
    if (u >= 0.82) {
      var a = sm((u - 0.82) * 8);
      T(ctx, "貯槽 残量 " + (RES[10] * 100).toFixed(4) + " % ≥ 99.9 %  ✓ (UFO.25)", 0.03, 0.2, { size: 13, color: COL.res, alpha: a });
      T(ctx, "Δ = e^π − π^e = " + V.delta.toFixed(4) + " < 1  ✓ (UFO.26)  → 巡航許可", 0.03, 0.15, { size: 13, color: COL.safe, alpha: a });
    } else if (u < 0.12) {
      T(ctx, "反重力リング励磁中:  □ag(x) = 2(sin(i x log x) + cos(i x log x))", 0.03, 0.2, { size: 13, color: COL.ring });
    }
  }
  function sEnd(ctx, u, sec) {
    BP.gridBg(ctx);
    drawAll(ctx, cam([320, 90, 640, 400], 18, -60 + 20 * sec, 1.1), { lw: 0.8, alpha: 0.7 * sm(u * 3) });
    var a = sm(u * 3 - 0.3);
    T(ctx, "方程式 26 本 → 部品 10 点 → 平面図 → 3D → 組み立て → 飛行 (方程式を毎秒評価)", 0.5, 0.2, { size: 15, align: "center", alpha: a });
    T(ctx, "※ 論文の方程式に基づく思索的・フィクションの設計図です。実在の反重力装置ではありません。", 0.5, 0.09, { size: 12, align: "center", color: C.warn, alpha: a });
  }
  var SCENES = { title: sTitle, params: sParams, mapping: sMapping, plan: sPlan, to3d: sTo3d, assembly: sAssembly, flight: sFlight, end: sEnd };
  function frame(ctx, sec) {
    var s = TL.at(sec);
    BP.clear(ctx);
    SCENES[s.name](ctx, s.u, s.local);
    if (s.name !== "title") BP.header(ctx, TITLES[s.name], "UFO BLUEPRINT", sec, TL.total);
    var edge = Math.min(s.local, s.dur - s.local);
    if (edge < 0.35) BP.fade(ctx, 1 - edge / 0.35);
  }
  function audio(sr) {
    var n = Math.floor(TL.total * sr), out = new Float32Array(n), f0 = TL.start("flight"), e0 = TL.start("end"), ph = 0;
    for (var i = 0; i < n; i++) {
      var t = i / sr, ramp = BP.clamp((t - f0) / 4, 0, 1) * (t < e0 ? 1 : 0), f = 180 + 60 * Math.sin(2 * PI * 0.5 * t);
      ph += 2 * PI * f / sr;
      out[i] = (0.08 * Math.sin(2 * PI * 73.4 * t) + 0.04 * Math.sin(2 * PI * 110 * t) + 0.09 * ramp * Math.sin(ph)) *
               BP.clamp(t / 2, 0, 1) * BP.clamp((TL.total - t) / 2, 0, 1);
    }
    return out;
  }

  /* ---- PDF ---- */
  var PW = BP.PDF_W, PH = BP.PDF_H;
  function Tp(ctx, s, x, y, o) { T(ctx, s, x, y, o, PW, PH); }
  var NOTE = "※ 論文の方程式 (UFO.1–26) に基づく思索的・フィクションの設計図です。実在の反重力装置ではありません。外形寸法は図解用。";
  var pdfPages = [
    function (ctx) {
      Tp(ctx, "UFO BLUEPRINT", 0.05, 0.84, { size: 34, bold: true });
      Tp(ctx, "反重力機  3 次元設計図 (部品表・方程式対応表・組立図・飛行制御)", 0.05, 0.785, { size: 15, color: C.hud });
      ["原典: contact_blueprint.pdf の方程式レジストリ UFO.1–UFO.26 (26 本)", "      src/UFO_OS.om — 反重力発生器の制御 OS (controlGravityDrive)",
       "原理: 重力ポテンシャル U = GMm/r を、多様体座標 x の反重力係数 α_ag = cosh(x log x) ≥ 1 で増幅",
       "      揚力比 L = E_ag/U = cosh(x log x) = 2.125 (地表)、上昇加速度 a = (L − 1)·g_eff = 11.047 m/s²",
       "機体: m = 1.2×10⁴ kg (UFO.16)、10 秒で高度 607.5 m・速度 110.45 m/s (UFO.24)"].forEach(function (l, i) { Tp(ctx, l, 0.05, 0.71 - i * 0.04, { size: 10.5 }); });
      drawAll(ctx, cam([600, 400, 540, 330], 20, -58, 1.1), { lw: 0.7 });
      Tp(ctx, "目次", 0.05, 0.47, { size: 11, bold: true, color: C.hud });
      ["01 表紙", "02 方程式と再計算", "03 部品 ↔ 方程式 対応表", "04 三面図", "05 3D 等角図・分解組立図", "06 飛行制御 (UFO_OS と方程式)", "07 飛行シミュレーション", "08 注記"]
        .forEach(function (t, i) { Tp(ctx, t, 0.05, 0.43 - i * 0.035, { size: 9.5 }); });
      Tp(ctx, NOTE, 0.03, 0.1, { size: 7.5, color: C.warn });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "1. 方程式と再計算", "アプリ内で再計算し、レポートの値と照合");
      var rows = [["UFO.1", "U = GMm/r (r = r0)", e5(V.U) + " J", "7.50723e+11"], ["UFO.3/16", "E⊥ = mc² − ½mv² (m = 1.2e4 kg, v = 1e4 m/s)", e5(V.Eperp) + " J", "1.07851e+21"],
                  ["UFO.4", "□dal(x) = e^(x log x) = x^x (x = 2)", "4", "4"], ["UFO.5", "dμ(x) = 1/(x log x)² (x = 2)", V.dmu.toFixed(6), "0.520342"],
                  ["UFO.9", "β(p,q) = Γ(p)Γ(q)/Γ(p+q) (2,3)", V.beta.toFixed(7), "0.0833333"], ["UFO.11/19", "L = α_ag = cosh(x log x), x = 2", V.L0.toFixed(5), "2.125"],
                  ["UFO.13", "E_ag = (GMm/r)·cosh(x log x)", e5(V.Eag) + " J", "1.59529e+12"], ["UFO.19", "a = (L − 1)·g_eff", V.a0.toFixed(4) + " m/s²", "11.047"],
                  ["UFO.22", "›- : e^(−x log x) (x = 2)", V.eneg.toFixed(2), "0.25"], ["UFO.23", "L(1 km)", V.L1.toFixed(5), "2.12450"],
                  ["", "L(5 km) / L(20 km)", V.L5.toFixed(5) + " / " + V.L20.toFixed(5), "2.12251 / 2.11510"], ["", "L(100 km)", V.L100.toFixed(5), "2.07677"],
                  ["UFO.24", "10 ステップ後 (dt = 1 s)", V.h10.toFixed(1) + " m, " + V.v10.toFixed(2) + " m/s", "607.6 m, 110.46 m/s"],
                  ["UFO.25", "貯槽 5 倍 × 10 回引き出し後", (RES[10] * 100).toFixed(4) + " %", "≥ 99.9 %"], ["UFO.18/26", "Δ = e^π − π^e", V.delta.toFixed(4) + "  (< 1)", "0.6815"]];
      var xs = [0.04, 0.14, 0.53, 0.75];
      ["式 ID", "方程式・条件", "再計算", "レポート値"].forEach(function (h, j) { Tp(ctx, h, xs[j], 0.86, { size: 10.5, bold: true, color: C.hud }); });
      rows.forEach(function (r, i) {
        var y = 0.825 - i * 0.045;
        r.forEach(function (v, j) { Tp(ctx, v, xs[j], y, { size: 9.5, color: j === 0 ? C.warn : (j === 3 ? C.ok : C.fg) }); });
        BP.lineF(ctx, 0.035, y - 0.012, 0.96, y - 0.012, C.grid, 0.5, 1, PW, PH);
      });
      Tp(ctx, "x = manifold_coord(r0/r) = 2√(r0/r) (r0 = 6.371×10⁶ m) とおくと L(h) と上昇軌道がレポートと一致する (L(100 km) は 5 桁目で差 0.0002)。", 0.04, 0.115, { size: 8.5 });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "2. 部品 ↔ 方程式 対応表", "26 本すべてを 10 部品に割り当て");
      ["No.", "部品", "式 ID", "支配方程式", "寸法・備考"].forEach(function (h, j) { Tp(ctx, h, [0.035, 0.065, 0.2, 0.33, 0.8][j], 0.87, { size: 10, bold: true, color: C.hud }); });
      PARTS.forEach(function (p, i) {
        var y = 0.83 - i * 0.075;
        Tp(ctx, String(i + 1), 0.04, y, { size: 11, bold: true, color: COL[p[0]] });
        Tp(ctx, p[1], 0.065, y, { size: 10, bold: true, color: COL[p[0]] });
        var ids = []; for (var j = 0; j < p[2].length; j += 3) ids.push(p[2].slice(j, j + 3).join(", "));
        Tp(ctx, ids.join("\n"), 0.2, y, { size: 8.5 });
        p[3].forEach(function (e, j2) { Tp(ctx, e, 0.33, y - j2 * 0.028, { size: 9 }); });
        Tp(ctx, p[4], 0.8, y, { size: 8.5 });
        BP.lineF(ctx, 0.03, y - 0.048, 0.965, y - 0.048, C.grid, 0.5, 1, PW, PH);
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "3. 三面図 (単位 m)", "寸法は図解用 (レポートに外形寸法の記載なし)");
      drawPlan(ctx, 1, 1, { top: [30, 110, 430, 600], front: [490, 130, 320, 300], side: [820, 130, 320, 300] }, 1);
      PARTS.forEach(function (p, i) { Tp(ctx, "■ " + p[1], 0.44 + (i % 2) * 0.26, 0.4 - Math.floor(i / 2) * 0.04, { size: 9, color: COL[p[0]] }); });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "4. 3D 等角図・分解組立図", "右図の番号 = 組立順");
      drawAll(ctx, cam([10, 200, 480, 420], 22, -58, 1.1), { lw: 0.7 });
      var cc = new BP.Camera({ rect: [440, 90, 480, 700], elev: 16, azim: -58, center: [0, 0, 1], scale: 700 / 34 });
      ORDER.forEach(function (k, i) {
        var off = EXPLODE[k].map(function (v) { return v * 0.8; });
        BP.drawPolys(ctx, cc, GEOM[k], COL[k], { lw: 0.6, offset: off });
        var cen = BP.centroid(GEOM[k]), q = cc.p([cen[0] + off[0], cen[1] + off[1], cen[2] + off[2]]);
        BP.balloon(ctx, q[0], q[1], i + 1, COL[k]);
      });
      ORDER.forEach(function (k, i) { Tp(ctx, (i + 1) + ". " + NAME[k], 0.79, 0.85 - i * 0.07, { size: 10, bold: true, color: COL[k] }); });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "5. 飛行制御 — UFO_OS と方程式", "src/UFO_OS.om の controlGravityDrive() に各方程式を実装");
      UFO_OS.forEach(function (l, i) {
        var y = 0.83 - i * 0.045;
        Tp(ctx, l[0], 0.05, y, { size: 12 });
        if (l[1]) {
          var e = EQS.filter(function (q) { return q.id === l[1]; })[0];
          Tp(ctx, l[1], 0.45, y, { size: 10, color: C.warn });
          if (e) Tp(ctx, e.eq.slice(0, 70), 0.53, y, { size: 8.5, color: C.hud });
        }
      });
      Tp(ctx, "制御の流れ", 0.05, 0.33, { size: 11, bold: true, color: C.hud });
      ["① センサ: 高度 h → 多様体座標 x = 2√(r0/(r0+h))", "② 反重力リング: α_ag = L = cosh(x log x)", "③ 重力結合コア: E_ag = U·L ≥ U を確認",
       "④ 推力: a = (L − 1)·GM/r²,  v ← v + a dt,  h ← h + v dt", "⑤ 貯槽 ≥ 99.9 %、Δ = e^π − π^e < 1 を満たす限り継続"].forEach(function (l, i) { Tp(ctx, l, 0.06, 0.29 - i * 0.035, { size: 10 }); });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "6. 飛行シミュレーション", "UFO.24 の 10 ステップ上昇を方程式どおりに計算 (dt = 1 s)");
      var xs = [0.04, 0.08, 0.13, 0.21, 0.29, 0.38, 0.5, 0.59];
      ["k", "t [s]", "h [m]", "v [m/s]", "x", "L = cosh(x log x)", "a [m/s²]", "E_ag [J]"].forEach(function (h, j) { Tp(ctx, h, xs[j], 0.86, { size: 9, bold: true, color: C.hud }); });
      SIM.forEach(function (r, i) {
        var y = 0.83 - i * 0.034;
        [String(r.k), String(r.k), r.h.toFixed(2), r.v.toFixed(3), r.x.toFixed(6), r.L.toFixed(6), r.a.toFixed(4), r.Eag.toExponential(5)]
          .forEach(function (v, j) { Tp(ctx, v, xs[j], y, { size: 9 }); });
      });
      var p1 = new BP.Plot(ctx, [840, 130, 280, 240], [0, 10], [0, 650], "高度 h [m] と速度 v [m/s]");
      p1.ticks(5, 5);
      p1.line(SIM.map(function (r) { return r.k; }), SIM.map(function (r) { return r.h; }), C.warn, 1.5);
      p1.line(SIM.map(function (r) { return r.k; }), SIM.map(function (r) { return r.v; }), COL.sensor, 1.5);
      SIM.forEach(function (r) { p1.dot(r.k, r.h, C.warn, 2.5); p1.dot(r.k, r.v, COL.sensor, 2.5); });
      var hh = BP.linspace(0, 100, 200), p2 = new BP.Plot(ctx, [70, 520, 460, 180], [0, 100], [2.07, 2.13], "揚力比 L(h) = cosh(x log x) (UFO.23)  ● = レポート値");
      p2.ticks(5, 3, null, function (v) { return v.toFixed(3); });
      p2.line(hh, hh.map(function (h) { return lift(h * 1e3); }), COL.ring, 1.4);
      [[0, 2.125], [1, 2.1245], [5, 2.12251], [20, 2.1151], [100, 2.07677]].forEach(function (q) { p2.dot(q[0], q[1], C.warn, 3); });
      var p3 = new BP.Plot(ctx, [640, 520, 460, 180], [0, 10], [99.99, 100.001], "真空エネルギー貯槽の残量 [%] (UFO.25)");
      p3.ticks(5, 2, null, function (v) { return v.toFixed(3); });
      p3.line(RES.map(function (_, i) { return i; }), RES.map(function (r) { return r * 100; }), COL.res, 1.4);
    },
    function (ctx) {
      BP.pdfTitle(ctx, "7. 注記");
      ["・方程式・数値の根拠は contact_blueprint.pdf の UFO.1–UFO.26 (2 章で全 26 本を部品に割り当て)。",
       "・x = manifold_coord(r0/r) は 2√(r0/r) と解釈した。この解釈で UFO.23 の L(h) と UFO.24 の上昇軌道を再現できる。",
       "・貯槽の容量 (UFO.25) はレポートに数値がないため図解用の値 (10⁶ 単位) を用いた。",
       "・外形寸法 (直径 16 m など) は図解用。質量 1.2×10⁴ kg のみレポート (UFO.16) による。",
       "・生成: UFO 設計図作成ソフト (Bada Blueprint Studio)", "", NOTE].forEach(function (l, i) { Tp(ctx, l, 0.05, 0.84 - i * 0.05, { size: 10, color: l === NOTE ? C.warn : C.fg }); });
    }
  ];

  root.BP_APP = {
    id: "ufo", title: "UFO 設計図作成ソフト", subtitle: "UFO BLUEPRINT — 反重力の方程式 UFO.1–26 から 3D 設計図と飛行動画を生成",
    brand: "UFO BLUEPRINT — 反重力機 3D 設計図", pdfTitle: "UFO 3D Blueprint", fileBase: "ufo_blueprint",
    timeline: TL, sceneLabels: LABELS, frame: frame, audio: audio, pdfPages: pdfPages,
    aboutHtml: "レポートの方程式 UFO.1–UFO.26 と UFO_OS.om の制御ループから、部品 → 平面図 → 3D → 組み立て → 飛行を描きます。" +
      "飛行シーンでは方程式を毎秒評価して上昇します (10 s 後 607.5 m / 110.45 m/s)。<br>※ 思索的・フィクションの設計図です。",
    _test: { SIM: SIM, V: V, RES: RES, lift: lift, EQS: EQS }
  };
})(typeof window !== "undefined" ? window : globalThis);
