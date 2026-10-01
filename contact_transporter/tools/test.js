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
const D = require("../src/drafting.js"), H = require("./badahost.js");

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
const asc = P.ufo.ascend(10, 1).pop();
near("UFO.24 高度 10 step", asc.h, 607.6, 1e-3);
near("UFO.24 速度 10 step", asc.v, 110.46, 1e-3);
near("UFO.1 U = GMm/r (m=1.2e4)", P.ufo.Ugrav(12000, 0), 7.50723e11, 1e-3);
near("UFO.9 β(3,2)", P.betaR(3, 2), 0.0833333, 1e-5);
// ---- 方程式レジストリ
const eqs = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "equations.json"), "utf8"));
const cnt = (s) => eqs.filter((e) => e.status === s).length;
near("方程式 総数", eqs.length, 2111, 0);
near("数値評価 632 本", cnt("calc") + cnt("holds") + cnt("differs"), 632, 0);
near("成立 231", cnt("holds"), 231, 0);
near("不成立 181", cnt("differs"), 181, 0);

// ---- Bada アプリ: 3 つとも Bada プログラムとして実行し、Bada が計算した値を設計図書と照合
const tr = H.makeApp("apps/transporter.bada");
const out = (k) => tr.ui.outputs[k][1];
near("[Bada] transporter.bada Γ", out("G"), 64800, 0);
near("[Bada] transporter.bada φ", out("phi"), 11.7722, 1e-5);
near("[Bada] transporter.bada T|ψ|", out("tpsi"), 1.76329, 1e-5);
near("[Bada] transporter.bada θ(φ)", out("rsth"), -2.58136, 1e-5);
near("[Bada] transporter.bada Z(φ) (Borwein ζ を Bada で)", out("Z"), -1.33415, 1e-5);
truthy("[Bada] transporter.bada V_3_1(t*) = -0.116342 + 2.30908i", out("V31") === "-0.116342 + 2.30908i");
truthy("[Bada] transporter.bada V_5_1(t*) = -2.81527 + 1.09654i", out("V51") === "-2.81527 + 1.09654i");
truthy("[Bada] transporter.bada 歳差 Ω = 3.7064", String(out("Omega")).startsWith("3.7064"));
truthy(`[Bada] transporter.bada 部品 ${tr.env.scene.parts.size} 個`, tr.env.scene.parts.size >= 24);
tr.app.call("frame", [3.5]);
truthy("[Bada] transporter.bada frame(t) で外環が回転", tr.env.scene.parts.get("ring_outer").matrix != null);
tr.app.call("make_sheet", []);
truthy(`[Bada] transporter.bada 図面 (尺度 1:${tr.env.lastSheet && tr.env.lastSheet.scale})`, tr.env.lastSheet && tr.env.lastSheet.svg.includes("CONTACT TRANSPORTER"));
const uf = H.makeApp("apps/ufo.bada");
near("[Bada] ufo.bada L = cosh(x log x)", uf.ui.outputs.L[1], 2.125, 1e-9);
truthy("[Bada] ufo.bada 10 s 後 h = 607.58 m, v = 110.46 m/s", uf.ui.outputs.h10[1] === "h = 607.58 m, v = 110.46 m/s");
truthy("[Bada] ufo.bada が図面を描く", uf.env.lastSheet && uf.env.lastSheet.svg.includes("部材表") && uf.env.lastSheet.svg.includes("SiO₂"));
const ub = CAD.Mesh && require("../src/badalib.js").boundsOf(uf.env.scene.baked());
near("[Bada] ufo.bada 着陸時の最下点 z = 0", ub.min[2], 0, 1e-6);
near("[Bada] ufo.bada 全高 = 脚+下殻+上殻+ドーム", ub.max[2], 3.2 + 2.2 + 3.2 + 3.2, 1e-6);
uf.app.call("preset_mothership", []);
near("[Bada] ufo.bada プリセット (大型母船) ⌀60", uf.ui.vals.diameter, 60, 0);
const cg = H.makeApp("apps/contactgpt.bada", { model: false });
cg.app.call("on_message", ["UFO.19"]);
truthy("[Bada] contactgpt.bada ID 参照 UFO.19", cg.chat.refs[0] === "UFO.19");
cg.chat.refs.length = 0; cg.app.call("on_message", ["反重力で上昇するには？"]);
truthy("[Bada] contactgpt.bada 反重力 → UFO 系を検索", cg.chat.refs.some((id) => id.startsWith("UFO.")));
cg.chat.replies.length = 0; cg.app.call("on_message", ["ローレンツ因子は？"]);
truthy("[Bada] contactgpt.bada Γ の即答", cg.chat.replies.join().includes("64800"));
cg.chat.replies.length = 0; cg.app.call("on_message", ["計算 rs_z(14.1347)"]);
truthy("[Bada] contactgpt.bada 計算 = Bada の式 (Z の第 1 零点 ≈ 0)", /\*\*-?0\.0000/.test(cg.chat.replies[0]));
{
  const files = H.badaFiles(), B = require("../src/bada.js"), Lb = require("../src/badalib.js"), o = [];
  const vm = new B.BadaVM({ host: Lb.makeHost({ files, ui: {}, chat: {} }), files, onPrint: (l) => o.push(l) });
  vm.load(files["examples/quantum_demo.bada"]);
  truthy("[Bada] 量子: ベル状態 [0.5, 0, 0, 0.5]", o[1] === "[0.5, 0, 0, 0.5]");
  truthy("[Bada] 量子: Grover (2 qubit) が |11⟩ を確率 1 で見つける", o[5] === "[0, 0, 0, 1]");
  const z = []; const vm2 = new B.BadaVM({ host: Lb.makeHost({ files, ui: {}, chat: {} }), files, onPrint: (l) => z.push(l) });
  vm2.load(files["examples/zeta_zeros.bada"]);
  truthy("[Bada] ζ の非自明零点 14.134725 / 21.022040 / 25.010858", z[1].includes("14.134725") && z[2].includes("21.022040") && z[3].includes("25.010858"));
  for (const f of Object.keys(files)) {
    const diags = B.lint(new B.BadaVM({ files }).expand(files[f], f), new Set(Object.keys(Lb.makeHost({ files, ui: {}, chat: {}, equations: [], index: { search: () => [], tagsIn: () => [] }, scene: new Lb.Scene() }))));
    truthy(`[Bada] 構文チェック ${f}`, diags.length === 0);
  }
}

// ---- 要求に応える (on_request) / ContactGPT が Bada でアプリを書く (codegen)
{
  const Lb = require("../src/badalib.js"), B = require("../src/bada.js");
  const t2 = H.makeApp("apps/transporter.bada");
  t2.app.call("on_request", ["外環を80mに"]);
  near("[Bada] 輸送機 on_request「外環を80mに」", t2.ui.vals.ring_outer, 80, 0);
  t2.app.call("on_request", ["塔を1.5倍"]);
  near("[Bada] 輸送機 on_request「塔を1.5倍」", t2.ui.vals.tower, 132.194 * 1.5, 1e-9);
  truthy("[Bada] 輸送機 on_request「Γは？」", String(t2.app.call("on_request", ["Γは？"])).includes("64800"));
  t2.app.call("on_request", ["STLで保存"]);
  truthy("[Bada] 輸送機 on_request「STLで保存」→ export_file", t2.ui.log.some((x) => x[0] === "export" && x[1] === "stl"));
  const u2 = H.makeApp("apps/ufo.bada");
  u2.app.call("on_request", ["12個の窓と4本の脚、直径40m"]);
  truthy("[Bada] UFO on_request「12個の窓と4本の脚、直径40m」", u2.ui.vals.windows === 12 && u2.ui.vals.legs === 4 && u2.ui.vals.diameter === 40);
  u2.app.call("on_request", ["コイルを5_1に、リングを外して、名前は「SKY-1」"]);
  truthy("[Bada] UFO on_request コイル / リング / 名前", u2.ui.vals.knot === "5_1" && u2.ui.vals.ring === false && u2.ui.vals.name === "SKY-1");
  truthy("[Bada] UFO on_request で図面が更新", u2.env.lastSheet.svg.includes("SKY-1"));
  const g = H.makeApp("apps/contactgpt.bada", { model: false });
  const cases = [
    ["「SKY-7」という名前で直径30m、12個の窓と4本の脚、5_1コイルのUFOの設計図アプリを作って", "ufo"],
    ["外環80mで24時間、4_1コイルのリング4つの輸送機を設計して", "cad"],
    ["4量子ビットのGHZのプログラムを書いて", "console"],
    ["ゼータの零点を40まで求めるアプリを作って", "console"],
    ["24時間のローレンツ計算アプリを作って", "console"],
    ["5_1の共鳴を計算するアプリを作って", "console"],
    ["20秒の上昇を計算するプログラムを作って", "console"],
  ];
  for (const [q, target] of cases) {
    g.chat.codes.length = 0; g.app.call("on_message", [q]);
    const c = g.chat.codes[0];
    truthy(`[Bada] ContactGPT がアプリを書く: ${q}`, c && c.target === target && g.files[c.file] === c.src);
    if (!c) continue;
    let ok = false, info = "";
    try {
      if (target === "console") {
        const out = [], vm = new B.BadaVM({ host: Lb.makeHost({ files: g.files, ui: {}, chat: {} }), files: g.files, onPrint: (l) => out.push(l) });
        vm.load(c.src, c.file); ok = out.length >= 3; info = out[1];
      } else {
        const env = { files: g.files, ui: H.stubUI(), chat: {}, scene: new Lb.Scene(), onError: (e) => { throw e; } };
        const a = new Lb.BadaApp(env); a.start(c.src, c.file); a.call("frame", [1.5]); a.call("make_sheet", []);
        ok = env.scene.parts.size >= 8 && env.lastSheet != null; info = `部品 ${env.scene.parts.size}`;
      }
    } catch (e) { info = e.message; }
    truthy(`[Bada]   → 生成された ${c.file} が動く (${info})`, ok);
  }
  g.chat.codes.length = 0; g.app.call("on_message", ["ゼータの零点を40まで求めるアプリを作って"]);
  const zsrc = g.chat.codes[0].src, zo = [];
  new B.BadaVM({ host: Lb.makeHost({ files: g.files, ui: {}, chat: {} }), files: g.files, onPrint: (l) => zo.push(l) }).load(zsrc);
  truthy("[Bada]   → 生成された零点アプリが 14.134725 … 37.586178 の 6 個を出す", zo.join().includes("14.134725") && zo.join().includes("37.586178") && zo[zo.length - 1].includes("6 個"));
}

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
const parts = tr.env.scene.baked();
truthy(`輸送機アセンブリ (Bada) ${parts.length} 部品`, parts.length >= 20);
const stl = CAD.toSTLBinary(parts);
const tris = parts.reduce((s, p) => s + p.mesh.triCount, 0);
near("STL バイト数 = 84 + 50·三角形数", stl.byteLength, 84 + 50 * tris, 0);
truthy("OBJ に全部品", CAD.toOBJ(parts).split("\no ").length - 1 === parts.length);

// ---- 図面
const sh = D.sheet({ parts, dims: tr.env.scene.dims, title: "test" });
truthy(`図面 SVG (尺度 1:${sh.scale})`, sh.svg.startsWith("<svg") && sh.svg.includes("平面図") && sh.svg.endsWith("</svg>"));
truthy("図面 DXF", sh.dxf.includes("ENTITIES") && sh.dxf.trim().endsWith("EOF"));

// ---- ビルド成果物
const dist = path.join(__dirname, "..", "dist", "studio", "www", "index.html");
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
