/*
 * models.js — アセンブリ定義
 *
 *   transporter(bp, t)  異次元輸送機 (設計図書 ⑦ 部品寸法 + ③ ジンバル角速度 + ⑤ Jones コイル)
 *   ufo(params, t)      UFO 設計ソフトのパラメトリック円盤機
 *
 * 各部品は { id, name, color, mesh, matrix }。matrix は時刻 t の姿勢 (アニメーション用)。
 * 座標系: z 上向き, 単位 m, 地表 z = 0。
 */
(function (root) {
  "use strict";
  const CAD = root.CTCad || (typeof require !== "undefined" ? require("./cad.js") : null);
  const { m4, v3, shapes } = CAD;
  const D2R = Math.PI / 180;

  // z 軸を dir に向ける回転
  function alignZ(dir) {
    const n = v3.norm(dir), z = [0, 0, 1], ax = v3.cross(z, n), s = v3.len(ax);
    if (s < 1e-9) return n[2] > 0 ? m4.ident() : m4.rot([1, 0, 0], Math.PI);
    return m4.rot(ax, Math.atan2(s, v3.dot(z, n)));
  }
  const chain = (...ms) => ms.reduce((a, b) => m4.mul(a, b));
  function bake(parts) {
    return parts.map((p) => Object.assign({}, p, { mesh: p.matrix ? p.mesh.transform(p.matrix) : p.mesh, matrix: null }));
  }

  // ============================================================ 輸送機
  const TRANSPORTER_COLORS = {
    ring: "#4fc3f7", pod: "#ffd54f", tower: "#90a4ae", j31: "#ef5350", j51: "#ab47bc", j41: "#66bb6a",
    door: "#ffffff", window: "#ff9800", floor: "#37474f", axle: "#b0bec5",
  };
  const cache = new Map();
  function memo(key, fn) { if (!cache.has(key)) cache.set(key, fn()); return cache.get(key); }

  function transporter(bp, t, opt) {
    opt = Object.assign({ timeScale: 1 }, opt || {});
    const d = bp.dims, C = TRANSPORTER_COLORS, tt = (t || 0) * opt.timeScale;
    const H0 = d.tower - d.ringOuter - d.tube;          // ジンバル中心の高さ
    const center = m4.translate(0, 0, H0);
    const [w1, w2, w3] = bp.omega, th0 = bp.Theta.re;
    const key = JSON.stringify(d);
    const M = memo(key, () => ({
      outer: shapes.torus(d.ringOuter, d.tube, 128, 16),
      mid: shapes.torus(d.ringMid, d.tube, 112, 16),
      inner: shapes.torus(d.ringInner, d.tube, 96, 16),
      pod: shapes.sphere(d.podR, 48, 24),
      spin: shapes.cylinder(0.6, d.podR * 2.6, 16),
      axleV: shapes.cylinder(0.9, d.tower - (H0 + d.ringOuter), 16),
      axle: shapes.cylinder(0.7, 1, 12),
      pylon: shapes.box(6, 6, d.tower),
      beam: shapes.box((d.coil31 + 12) * 2 + 6, 5, 5),
      j31: shapes.torusKnot(d.coil31 - 4, 4, 2, 3, 1.2),
      j51: shapes.torusKnot(d.coil51 - 3.5, 3.5, 2, 5, 1.0),
      j41: shapes.figureEight(d.coil41 / 3, 1.0),
      floor: shapes.lathe([[d.ringInner, 0], [d.coil31 + 16, 0]], 96),
      well: shapes.lathe([[d.ringInner, 0], [d.ringInner, -d.well], [0, -d.well]], 96),
      door: shapes.cylinder(0.5, 110, 12),
      doorTip: shapes.cone(2.2, 0, 7, 16),
      window: shapes.torus(12, 0.6, 64, 8),
      winPanel: shapes.box(3.2, 3.2, 0.6),
    }));

    const Rout = chain(m4.rot([0, 0, 1], w1 * tt));
    const Rmid = chain(Rout, m4.rot([1, 0, 0], th0 + w2 * tt));
    const Rin = chain(Rmid, m4.rot([0, 1, 0], w3 * tt));
    const parts = [];
    const P = (id, name, color, mesh, matrix) => parts.push({ id, name, color, mesh, matrix });

    // ジンバル環 (外: 鉛直軸, 中: 外環内の x 軸, 内: 中環内の y 軸)
    P("ring_outer", `外環 R=${d.ringOuter}`, C.ring, M.outer, chain(center, Rout, m4.rot([1, 0, 0], Math.PI / 2)));
    P("ring_mid", `中環 R=${d.ringMid}`, C.ring, M.mid, chain(center, Rmid));
    P("ring_inner", `内環 R=${d.ringInner}`, C.ring, M.inner, chain(center, Rin, m4.rot([0, 1, 0], Math.PI / 2)));
    // 軸受 (外環-中環: ±x, 中環-内環: ±y)
    for (const s of [-1, 1]) {
      P(`axle_om${s}`, "軸受 外-中", C.axle, M.axle,
        chain(center, Rout, m4.translate(s * d.ringMid, 0, 0), m4.rot([0, 1, 0], s * Math.PI / 2), m4.scale(1, 1, d.ringOuter - d.ringMid)));
      P(`axle_mi${s}`, "軸受 中-内", C.axle, M.axle,
        chain(center, Rmid, m4.translate(0, s * d.ringInner, 0), m4.rot([1, 0, 0], -s * Math.PI / 2), m4.scale(1, 1, d.ringMid - d.ringInner)));
    }
    // ポッド + スピン軸 (歳差 Ω)
    P("pod", `ポッド r=${d.podR}`, C.pod, M.pod, chain(center, Rin));
    P("pod_spin", "ポッド スピン軸 (歳差 Ω)", C.pod, M.spin,
      chain(center, m4.rot([0, 0, 1], bp.Omega * tt * 0.05), m4.rot([1, 0, 0], th0), m4.translate(0, 0, -d.podR * 1.3)));
    // 塔・ガントリー
    const px = d.coil31 + 12;
    P("pylon_l", `塔 H=${d.tower}`, C.tower, M.pylon, m4.translate(-px, 0, d.tower / 2));
    P("pylon_r", `塔 H=${d.tower}`, C.tower, M.pylon, m4.translate(px, 0, d.tower / 2));
    P("beam", "ガントリー梁", C.tower, M.beam, m4.translate(0, 0, d.tower + 2.5));
    P("hanger", "吊り軸 (外環の鉛直軸)", C.axle, M.axleV, chain(m4.translate(0, 0, H0 + d.ringOuter)));
    // Jones コイル
    P("jones31", `Jones 3_1 コイル R=${d.coil31}`, C.j31, M.j31, m4.translate(0, 0, 4));
    P("jones51", `Jones 5_1 コイル R=${d.coil51}`, C.j51, M.j51, m4.translate(0, 0, 10));
    P("jones41", "Jones 4_1 コイル (床下)", C.j41, M.j41, m4.translate(0, 0, -d.well * 0.55));
    // 床・井戸
    P("floor", "床版", C.floor, M.floor, null);
    P("well", `井戸 深さ ${d.well}`, C.floor, M.well, null);
    // 扉の軸 n̂ と共鳴窓
    const n = bp.doorAxis, A = alignZ(n);
    P("door_axis", "扉の軸 n̂", C.door, M.door, chain(center, A));
    P("door_tip", "扉の軸 n̂ (先端)", C.door, M.doorTip, chain(center, A, m4.translate(0, 0, 110)));
    const wd = d.ringOuter + 18;
    P("res_window", "共鳴窓", C.window, M.window, chain(center, A, m4.translate(0, 0, wd)));
    const res = (bp.jones["3_1"].resonance || []).map((r) => r.alpha);
    res.forEach((a, i) => P(`res_panel${i}`, `共鳴窓 α=${a}°`, C.window, M.winPanel,
      chain(center, A, m4.translate(0, 0, wd), m4.rot([0, 0, 1], a * D2R), m4.translate(12, 0, 0))));
    return parts;
  }

  // 輸送機の図面注記 (寸法線)
  function transporterDims(bp) {
    const d = bp.dims, H0 = d.tower - d.ringOuter - d.tube;
    return [
      { view: "top", type: "radius", c: [0, 0], r: d.ringOuter, ang: 135, text: `R${d.ringOuter}` },
      { view: "top", type: "radius", c: [0, 0], r: d.coil31, ang: 45, text: `R${d.coil31} (3_1)` },
      { view: "front", type: "linear", a: [d.coil31 + 12, 0], b: [d.coil31 + 12, d.tower], off: 14, text: `${d.tower}` },
      { view: "front", type: "linear", a: [-d.ringInner, 0], b: [-d.ringInner, -d.well], off: -10, text: `${d.well}` },
      { view: "front", type: "linear", a: [0, 0], b: [0, H0], off: -d.ringOuter - 14, text: `${H0.toFixed(3)}` },
      { view: "side", type: "linear", a: [-d.ringOuter, H0], b: [d.ringOuter, H0], off: d.ringOuter + 12, text: `⌀${(d.ringOuter * 2).toFixed(3)}` },
    ];
  }

  // ============================================================ UFO
  const UFO_DEFAULTS = {
    name: "BADA-UFO 01", diameter: 24, rim: 0.8, upperH: 3.2, lowerH: 2.2,
    domeD: 9, domeH: 3.2, windows: 8, legs: 3, legLen: 3.2, engines: 3,
    contactRing: true, coilKnot: "3_1", mass: 12000, gain: 1.0,
    hullColor: "#cfd8dc", domeColor: "#80deea", accent: "#ff7043",
  };
  function ufoProfile(p) {
    const R = p.diameter / 2, rt = p.domeD / 2, rb = p.diameter * 0.2, n = 18, pr = [];
    pr.push([0, -p.lowerH]);
    pr.push([rb, -p.lowerH]);
    for (let k = 1; k <= n; k++) { // 下面: 底板 → 縁
      const s = k / n, r = rb + (R - rb) * s;
      pr.push([r, -p.lowerH + (p.lowerH - p.rim / 2) * Math.pow(s, 2.2)]);
    }
    pr.push([R, p.rim / 2]);
    for (let k = 1; k <= n; k++) { // 上面: 縁 → ドーム基部
      const s = k / n, r = R - (R - rt) * s;
      pr.push([r, p.rim / 2 + (p.upperH - p.rim / 2) * (1 - Math.pow(1 - s, 2.2))]);
    }
    pr.push([0, p.upperH]);
    return pr;
  }
  function ufo(params, t) {
    const p = Object.assign({}, UFO_DEFAULTS, params || {});
    const R = p.diameter / 2, rt = p.domeD / 2, parts = [];
    const P = (id, name, color, mesh, matrix) => parts.push({ id, name, color, mesh, matrix: matrix || null });
    const lift = p.lowerH + p.legLen; // 着陸状態: 脚の先が地表
    const base = m4.translate(0, 0, lift);
    P("hull", `船体 ⌀${p.diameter}`, p.hullColor, CAD.shapes.lathe(ufoProfile(p), 96), base);
    // ドーム (楕円体の上半分)
    const dome = [];
    for (let k = 0; k <= 16; k++) { const a = k / 16 * Math.PI / 2; dome.push([rt * Math.cos(a), p.upperH + p.domeH * Math.sin(a)]); }
    dome[16][0] = 0;
    P("dome", `ドーム ⌀${p.domeD}`, p.domeColor, CAD.shapes.lathe(dome, 64), base);
    // 舷窓
    const win = CAD.shapes.sphere(Math.min(0.45, p.domeD * 0.05), 16, 8);
    for (let i = 0; i < p.windows; i++) {
      const a = i / p.windows * 2 * Math.PI, rr = (R + rt) / 2;
      const z = p.rim / 2 + (p.upperH - p.rim / 2) * 0.62;
      P(`window${i}`, "舷窓", p.accent, win, chain(base, m4.translate(rr * Math.cos(a), rr * Math.sin(a), z)));
    }
    // 反重力コイル (Jones 結び目) — 船体下面
    const kR = p.diameter * 0.2;
    const knot = p.coilKnot === "4_1" ? CAD.shapes.figureEight(kR / 3, 0.18)
      : CAD.shapes.torusKnot(kR * 0.85, kR * 0.15, 2, p.coilKnot === "5_1" ? 5 : 3, 0.18);
    const spin = (t || 0) * 0.8;
    P("ag_coil", `反重力コイル Jones ${p.coilKnot}`, p.accent, knot, chain(base, m4.translate(0, 0, -p.lowerH - 0.25), m4.rot([0, 0, 1], spin)));
    // 推進ポッド
    const eng = CAD.shapes.lathe([[0, 0], [0.9, 0.2], [1.0, 0.9], [0.6, 1.4], [0, 1.5]], 32);
    for (let i = 0; i < p.engines; i++) {
      const a = (i + 0.5) / p.engines * 2 * Math.PI, rr = p.diameter * 0.34;
      const s = Math.pow((rr - p.diameter * 0.2) / (R - p.diameter * 0.2), 2.2);
      const z = -p.lowerH + (p.lowerH - p.rim / 2) * s - 1.3;
      P(`engine${i}`, "推進ポッド", "#78909c", eng, chain(base, m4.translate(rr * Math.cos(a), rr * Math.sin(a), z)));
    }
    // 着陸脚
    const leg = CAD.shapes.cylinder(0.18, 1, 12), pad = CAD.shapes.cylinder(0.7, 0.15, 24);
    for (let i = 0; i < p.legs; i++) {
      const a = i / p.legs * 2 * Math.PI, r0 = p.diameter * 0.16, r1 = p.diameter * 0.26;
      const top = [r0 * Math.cos(a), r0 * Math.sin(a), lift - p.lowerH], bot = [r1 * Math.cos(a), r1 * Math.sin(a), 0.15];
      const dvec = v3.sub(top, bot), L = v3.len(dvec);
      P(`leg${i}`, "着陸脚", "#90a4ae", leg, chain(m4.translate(bot[0], bot[1], bot[2]), alignZ(dvec), m4.scale(1, 1, L)));
      P(`pad${i}`, "脚パッド", "#90a4ae", pad, m4.translate(bot[0], bot[1], 0));
    }
    // コンタクト・リング (輸送機のジンバル環を縮小搭載)
    if (p.contactRing) {
      P("contact_ring", "コンタクト・リング", "#4fc3f7", CAD.shapes.torus(R + 1.2, 0.35, 96, 16),
        chain(base, m4.rot([1, 0, 0], 0.08 * Math.sin((t || 0) * 0.7)), m4.rot([0, 0, 1], (t || 0) * 0.3)));
    }
    return parts;
  }
  function ufoDims(params) {
    const p = Object.assign({}, UFO_DEFAULTS, params || {});
    const R = p.diameter / 2, lift = p.lowerH + p.legLen, top = lift + p.upperH + p.domeH;
    return [
      { view: "top", type: "linear", a: [-R, 0], b: [R, 0], off: -R - 2.5, text: `⌀${p.diameter}` },
      { view: "top", type: "radius", c: [0, 0], r: p.domeD / 2, ang: 45, text: `⌀${p.domeD}` },
      { view: "front", type: "linear", a: [R, 0], b: [R, top], off: 3, text: `${top.toFixed(2)}` },
      { view: "front", type: "linear", a: [-R, lift], b: [R, lift], off: -(lift + 1.5), text: `⌀${p.diameter}` },
      { view: "side", type: "linear", a: [-R - 1, lift - p.lowerH], b: [-R - 1, lift + p.upperH], off: -2, text: `${(p.lowerH + p.upperH).toFixed(2)}` },
      { view: "side", type: "linear", a: [R + 1, 0], b: [R + 1, lift - p.lowerH], off: 2, text: `${p.legLen}` },
    ];
  }
  // 部材表 (EXP.156 の材料リストに基づく)
  function ufoBOM(params) {
    const p = Object.assign({}, UFO_DEFAULTS, params || {});
    return [
      ["1", "船体 (上下殻)", "Fe·Co60·Pt·Al 合金", "1"],
      ["2", "ドーム", "SiO₂ プリズム", "1"],
      ["3", "舷窓", "Al₂O₃", String(p.windows)],
      ["4", `反重力コイル Jones ${p.coilKnot}`, "Cs / Mg 巻線", "1"],
      ["5", "推進ポッド", "Al (heat) / H₂", String(p.engines)],
      ["6", "着陸脚 + パッド", "Al 合金", String(p.legs)],
      ["7", "コンタクト・リング", "He 冷却 / CnH2n", p.contactRing ? "1" : "0"],
    ];
  }

  const api = { transporter, transporterDims, TRANSPORTER_COLORS, ufo, ufoDims, ufoBOM, ufoProfile, UFO_DEFAULTS, bake, alignZ };
  root.CTModels = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
