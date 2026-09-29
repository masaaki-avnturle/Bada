#!/usr/bin/env node
/*
 * test.js — エンジン検証 (CI で実行)
 *   設計図書 (contact_blueprint.pdf) 第 1 章の数値を方程式から再現できるか、
 *   GPT の勾配、CAD メッシュ、図面、対話エンジン、ビルド成果物を検査します。
 */
const path = require("path"), fs = require("fs");
global.CTPhys = require("../src/physics.js");
global.ContactGPT = require("../src/gpt.js");
global.CTCad = require("../src/cad.js");
const P = global.CTPhys, CAD = global.CTCad;
const M = require("../src/models.js"), D = require("../src/drafting.js"), { Chat, calc } = require("../src/chat.js");

let fail = 0, pass = 0;
function near(name, got, want, tol) {
  const ok = Math.abs(got - want) <= (tol == null ? 1e-4 : tol) * Math.max(1, Math.abs(want));
  ok ? pass++ : fail++;
  console.log(`${ok ? "ok  " : "FAIL"} ${name}: ${got} (期待 ${want})`);
}
function truthy(name, v) { v ? pass++ : fail++; console.log(`${v ? "ok  " : "FAIL"} ${name}`); }

// ---- ① 設計パラメータ (設計図書 p.2)
const bp = P.blueprint();
near("Γ = 18h/1s", bp.Gamma, 64800, 0);
near("1 − β", bp.oneMinusBeta, 1.19075e-10, 1e-5);
near("φ = arcosh Γ", bp.phi, 11.772200, 1e-5);
near("収縮距離 [km]", bp.distKm, 3.656e9, 1e-3);
near("片道 [h]", bp.oneWayH, 3.3874, 1e-4);
near("T|ψ|", bp.TPsi, 1.763290, 1e-5);
near("x log x = 1 の根", bp.xlogxRoot, 1.763220, 1e-5);
near("ω 外", bp.omega[0], 0.10472, 1e-4);
near("ω 中", bp.omega[1], 0.39241, 1e-4);
near("ω 内", bp.omega[2], 1.47043, 1e-4);
near("歳差 Ω", bp.Omega, 3.70640, 1e-4);
near("Riemann–Siegel θ(φ)", bp.rsTheta, -2.581360, 1e-5);
near("Z(φ)", bp.Z, -1.334150, 1e-5);
near("V_3_1(t*) re", bp.jones["3_1"].value.re, -0.116342, 1e-4);
near("V_3_1(t*) im", bp.jones["3_1"].value.im, 2.30908, 1e-5);
near("V_4_1(t*)", bp.jones["4_1"].value.re, 3.56478, 1e-5);
near("V_5_1(t*) re", bp.jones["5_1"].value.re, -2.81527, 1e-5);
near("V_5_1(t*) im", bp.jones["5_1"].value.im, 1.09654, 1e-5);
near("ζ(2) = π²/6", P.zeta(P.C(2, 0)).re, Math.PI ** 2 / 6, 1e-9);
near("Z(14.1347) ≈ 0 (第 1 零点)", P.rsZ(14.134725), 0, 1e-5);
// ---- UFO 系 (UFO.1–26)
near("UFO.11 L(0) = cosh(2 ln 2·…)", P.ufo.L(0), 2.125, 1e-9);
near("UFO.23 L(1 km)", P.ufo.L(1000), 2.12450, 1e-5);
near("UFO.23 L(100 km)", P.ufo.L(1e5), 2.07677, 1e-5);
near("UFO.19 a", P.ufo.accel(0), 11.047, 1e-3);
const tr = P.ufo.ascend(10, 1).pop();
near("UFO.24 高度 10 step", tr.h, 607.6, 1e-3);
near("UFO.24 速度 10 step", tr.v, 110.46, 1e-3);
near("UFO.1 U = GMm/r (m=1.2e4)", P.ufo.Ugrav(12000, 0), 7.50723e11, 1e-3);
near("UFO.9 β(3,2)", P.betaR(3, 2), 0.0833333, 1e-5);
// ---- 方程式レジストリ
const eqs = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "equations.json"), "utf8"));
const cnt = (s) => eqs.filter((e) => e.status === s).length;
near("方程式 総数", eqs.length, 2111, 0);
near("数値評価 632 本", cnt("calc") + cnt("holds") + cnt("differs"), 632, 0);
near("成立 231", cnt("holds"), 231, 0);
near("不成立 181", cnt("differs"), 181, 0);

// ---- 電卓 / 対話
near("calc gamma(0.5)^2", calc("gamma(0.5)^2"), Math.PI, 1e-9);
near("calc Z(11.7722)", calc("Z(11.7722)"), -1.33415, 1e-4);
near("calc 2^3^2 (右結合)", calc("2^3^2"), 512, 0);
const chat = new Chat(eqs, null, bp);
truthy("対話: ID 参照 UFO.19", chat.ask("UFO.19").refs[0].id === "UFO.19");
truthy("対話: 反重力 → UFO 系を検索", chat.ask("反重力で上昇するには？").refs.some((e) => e.id.startsWith("UFO.")));
truthy("対話: Γ の即答", chat.ask("ローレンツ因子は？").answer.join().includes("64800"));

// ---- GPT 勾配チェック + 学習で損失が下がる + 重みの往復
{
  const G = global.ContactGPT;
  G.setFloat(Float64Array);
  const g = new G.GPT({ nLayer: 1, nHead: 2, nEmbd: 8, block: 5, seed: 3 }, ["\u0000", "a", "b", "c"]);
  for (const t of Object.values(g.params)) for (let i = 0; i < t.data.length; i++) t.data[i] += Math.sin(i * 7.1 + t.data.length) * 0.3;
  const idx = Int32Array.from([1, 2, 3, 1, 2]), tgt = Int32Array.from([2, 3, 1, 2, 3]);
  const tape = new G.Tape(true); g.forward(tape, idx, 1, 5, tgt); tape.backward();
  let worst = 0;
  for (const t of Object.values(g.params)) for (let k = 0; k < Math.min(4, t.data.length); k++) {
    const i = (k * 13) % t.data.length, o = t.data[i], h = 1e-5;
    t.data[i] = o + h; const lp = g.forward(new G.Tape(false), idx, 1, 5, tgt).loss;
    t.data[i] = o - h; const lm = g.forward(new G.Tape(false), idx, 1, 5, tgt).loss; t.data[i] = o;
    const num = (lp - lm) / (2 * h), ana = t.grad[i];
    worst = Math.max(worst, Math.abs(num - ana) / Math.max(1e-6, Math.abs(num) + Math.abs(ana)));
  }
  truthy(`GPT 勾配チェック (最大相対誤差 ${worst.toExponential(2)})`, worst < 1e-4);
  G.setFloat(Float32Array);
  const text = "Q: Γ は？\nA: 64800\n".repeat(40), m2 = new G.GPT({ nLayer: 1, nHead: 2, nEmbd: 16, block: 16, seed: 1 }, G.buildVocab(text));
  const data = Int32Array.from(m2.encode(text)), l0 = m2.evalLoss(data, 4);
  for (let s = 0; s < 60; s++) m2.trainStep(data, { batch: 4, lr: 1e-2 });
  const l1 = m2.evalLoss(data, 4);
  truthy(`GPT 学習で損失低下 ${l0.toFixed(3)} → ${l1.toFixed(3)}`, l1 < l0 * 0.5);
  const m3 = G.GPT.fromJSON(JSON.parse(JSON.stringify(m2.toJSON())));
  near("GPT 重み (f16) 往復後の損失", m3.evalLoss(data, 4), l1, 0.05);
  const wPath = path.join(__dirname, "..", "data", "contactgpt_weights.json");
  if (fs.existsSync(wPath)) {
    const mw = G.GPT.fromJSON(JSON.parse(fs.readFileSync(wPath, "utf8")));
    const out = mw.generate("Q: UFO.19 は？\nA:", { seed: 1, temperature: 0.3, maxNew: 60, stop: "\nQ:" });
    truthy(`同梱の学習済み ContactGPT が生成できる (step ${mw.step}): ${JSON.stringify(out.slice(0, 50))}`, out.length > 5);
  }
}

// ---- CAD
function signedVolume(m) {
  let V = 0;
  for (let i = 0; i < m.idx.length; i += 3) { const a = m.pos[m.idx[i]], b = m.pos[m.idx[i + 1]], c = m.pos[m.idx[i + 2]]; V += CAD.v3.dot(a, CAD.v3.cross(b, c)) / 6; }
  return V;
}
near("トーラス体積 2π²Rr²", signedVolume(CAD.shapes.torus(10, 2, 256, 64)), 2 * Math.PI ** 2 * 10 * 4, 2e-3);
near("球体積 4/3πr³", signedVolume(CAD.shapes.sphere(3, 128, 64)), 4 / 3 * Math.PI * 27, 2e-3);
truthy("結び目チューブが外向き", signedVolume(CAD.shapes.torusKnot(10, 2, 2, 3, 0.5)) > 0);
const parts = M.bake(M.transporter(bp, 0));
truthy(`輸送機アセンブリ ${parts.length} 部品`, parts.length >= 20);
const stl = CAD.toSTLBinary(parts);
const tris = parts.reduce((s, p) => s + p.mesh.triCount, 0);
near("STL バイト数 = 84 + 50·三角形数", stl.byteLength, 84 + 50 * tris, 0);
truthy("OBJ に全部品", CAD.toOBJ(parts).split("\no ").length - 1 === parts.length);
const ub = M.bake(M.ufo({}, 0)).reduce((m, p) => m.merge(p.mesh), new CAD.Mesh()).bounds();
near("UFO 着陸時の最下点 z = 0", ub.min[2], 0, 1e-6);
near("UFO 全高 = 脚+下殻+上殻+ドーム", ub.max[2], 3.2 + 2.2 + 3.2 + 3.2, 1e-6);

// ---- 図面
const sh = D.sheet({ parts, dims: M.transporterDims(bp), title: "test" });
truthy(`図面 SVG (尺度 1:${sh.scale})`, sh.svg.startsWith("<svg") && sh.svg.includes("平面図") && sh.svg.endsWith("</svg>"));
truthy("図面 DXF", sh.dxf.includes("ENTITIES") && sh.dxf.trim().endsWith("EOF"));
const us = D.sheet({ parts: M.bake(M.ufo({}, 0)), dims: M.ufoDims({}), bom: M.ufoBOM({}), title: "UFO" });
truthy("UFO 図面に部材表", us.svg.includes("部材表") && us.svg.includes("SiO₂"));

// ---- ビルド成果物
const dist = path.join(__dirname, "..", "dist", "www", "index.html");
if (fs.existsSync(dist)) {
  const h = fs.readFileSync(dist, "utf8");
  truthy("dist/www/index.html にプレースホルダが残っていない", !/\/\*@@[A-Z_]+@@\*\//.test(h));
  const scripts = h.match(/<script>([\s\S]*?)<\/script>/g) || [];
  let ok = true;
  for (const s of scripts) { try { new Function(s.slice(8, -9)); } catch (e) { ok = false; console.log(e.message); } }
  truthy(`埋め込みスクリプト ${scripts.length} 個が構文的に正しい`, ok);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
