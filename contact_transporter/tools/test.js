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

// ---- BadaClaude: 対話の頭脳 (apps/badaclaude.bada) — 検索・意図推定・道具・Claude 文脈・台帳
{
  const asked = [];
  const bc = H.makeApp("apps/badaclaude.bada", { model: false, claude: { ready: () => asked.ready, ask: (system, q) => { asked.push({ system, q }); return null; } } });
  const say = (q) => { bc.chat.replies.length = 0; bc.chat.refs.length = 0; bc.chat.codes.length = 0; bc.app.call("on_message", [q]); return bc.chat.replies.join("\n"); };
  truthy("[BadaClaude] 知識ベース: 論文 10 本・抜粋 256 件 + 方程式 2111 本", /10 本の論文 · 抜粋 256 件 \+ 方程式 2111 本/.test(bc.ui.outputs.kb[1]));
  let r = say("ゼータ関数とベータ関数の関係は?");
  truthy("[BadaClaude] BM25 (Bada で採点) が「ベータ関数とゼータ関数の構造的対応」を引く", r.includes("『ベータ関数とゼータ関数の構造的対応』") && bc.chat.refs.length > 0);
  truthy("[BadaClaude] 意図推定 (softmax → ψ → |ψ|²) = explain", /意図 explain/.test(r));
  const first = r;
  r = say("もっと");
  truthy("[BadaClaude] 「もっと」で同じ質問の続きの結果", /意図 more/.test(r) && r !== first && r.includes("p."));
  say("ACAFE.17");
  truthy("[BadaClaude] 方程式 ID 参照", bc.chat.refs.includes("ACAFE.17"));
  r = say("計算 rs_z(14.134725)");
  truthy("[BadaClaude] 計算 (bada_expr) — Z(14.134725) ≈ 0", /= \*\*-?1\.\d+e-0?7\*\*/.test(r));
  r = say("ベル状態を見せて");
  truthy("[BadaClaude] 量子回路 (H + CNOT) の確率 [0.5, 0, 0, 0.5]", /0\.5000000000000001?, 0, 0, 0\.5/.test(r) || /\[0\.5\d*, 0, 0, 0\.5\d*\]/.test(r));
  r = say("リーマン予想は証明されたの?");
  truthy("[BadaClaude] 未解決問題は論文の標識どおり「未解決」と答える", /意図 open_problem/.test(r) && r.includes("未解決"));
  say("```bada\nx <- 6\nprint x * 7\n```");
  truthy("[BadaClaude] 送られた Bada コードを保存して実行に回す", bc.chat.codes.length === 1 && bc.chat.codes[0].target === "console" && bc.files[bc.chat.codes[0].file].includes("print x * 7"));
  say("直径40mで舷窓12個のUFOの設計図アプリを作って");
  truthy("[BadaClaude] 要求に応えて Bada でアプリを書く (codegen)", bc.chat.codes.length === 1 && bc.chat.codes[0].src.includes("ui_param"));
  asked.ready = true;
  say("反重力 UFO-OS とは");
  truthy("[BadaClaude] Claude API モード: Bada が <bada_context> (出典つき) を組み立てて渡す", asked.length === 1 && asked[0].system.includes("<bada_context intent=\"explain\">") && asked[0].system.includes("BadaUFO-OS") && asked[0].q === "反重力 UFO-OS とは");
  bc.app.call("after_claude", ["回答", "end_turn"]);
  r = say("台帳");
  truthy("[BadaClaude] Ω 台帳 (Omega::DATABASE[ledger]) に boot / turn / build / claude を追記", /boot/.test(r) && /turn/.test(r) && /build/.test(r) && /claude · end_turn/.test(r) && (bc.app.vm.tuplespace.ledger || []).length >= 10);
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
const dist = path.join(__dirname, "..", "dist", "nexus", "www", "index.html");
// ファイルの取り込み: Android の WebView で開かない <input type="file" accept="…"> を HTML に置かない
for (const app of Object.keys(require("../apps.json"))) {
  const f = path.join(__dirname, "..", "dist", app, "www", "index.html");
  if (!fs.existsSync(f)) continue;
  const h = fs.readFileSync(f, "utf8");
  const body = h.slice(h.indexOf("<body"), h.indexOf("<script"));
  truthy(`dist/${app}: 取り込みは OS のファイル画面 (pickFile) — 静的な <input type="file"> なし`, !/<input[^>]+type="file"/.test(body) && h.includes("function pickFile(kind)"));
}
// Android 用 www: cordova.js は <head> に 1 つだけ、アプリのスクリプトはすべて構文的に正しい
// (以前は CI の sed が JavaScript 内の "</head>" まで書き換え、Android 版の全スクリプトが壊れていた)
for (const app of Object.keys(require("../apps.json"))) {
  const f = path.join(__dirname, "..", "dist", app, "cordova", "www", "index.html");
  if (!fs.existsSync(f)) continue;
  const h = fs.readFileSync(f, "utf8"), web = fs.readFileSync(path.join(__dirname, "..", "dist", app, "www", "index.html"), "utf8");
  let ok = true;
  for (const m of h.matchAll(/<script>([\s\S]*?)<\/script>/g)) { try { new Function(m[1]); } catch (e) { ok = false; console.log(app, e.message); } }
  const head = h.slice(0, h.indexOf("</head>"));
  truthy(`dist/${app}/cordova/www (Android): cordova.js は <head> に 1 つ、スクリプトはすべて正しい、本体は Web 版と同一`, ok && (head.match(/<script src="cordova.js">/g) || []).length === 1 && h.replace('<script src="cordova.js"></script>\n', "") === web);
}
{
  const plug = path.join(__dirname, "..", "app", "cordova", "bada-files");
  const xml = fs.readFileSync(path.join(plug, "plugin.xml"), "utf8"), java = fs.readFileSync(path.join(plug, "src", "android", "BadaFiles.java"), "utf8");
  truthy("Android プラグイン BadaFiles: ACTION_OPEN_DOCUMENT (開く) / MediaStore.Downloads (保存) / ACTION_CREATE_DOCUMENT / ダウンロード フォルダ",
    xml.includes('<clobbers target="BadaFiles" />') && xml.includes("io.github.masaaki_avnturle.badafiles.BadaFiles") && /ACTION_OPEN_DOCUMENT/.test(java) && /MediaStore\.Downloads\.EXTERNAL_CONTENT_URI/.test(java) && /ACTION_CREATE_DOCUMENT/.test(java) && /ACTION_VIEW_DOWNLOADS/.test(java));
  const main = fs.readFileSync(path.join(__dirname, "..", "app", "electron", "main.js"), "utf8"), pre = fs.readFileSync(path.join(__dirname, "..", "app", "electron", "preload.js"), "utf8");
  truthy("Electron: OS 標準の「開く」ダイアログ (ct-open-file) とダウンロード フォルダ (ct-show-downloads)", main.includes("dialog.showOpenDialog") && main.includes('"ct-open-file"') && pre.includes('exposeInMainWorld("ctNative"'));
  const cfgDir = path.join(__dirname, "..", "dist", "ufo", "cordova", "bada-files", "plugin.xml");
  if (fs.existsSync(path.join(__dirname, "..", "dist", "ufo", "cordova"))) truthy("package-app.js がプラグインを dist/<app>/cordova/bada-files に同梱", fs.existsSync(cfgDir));
}
{
  const A = require("../apps.json").nexus;
  truthy("統合アプリ Bada Nexus (nexus): ContactGPT・BadaClaude・輸送機 CAD・UFO・論文→アプリ・IDE を 1 つに", ["chat", "claude", "cad", "ufo", "paper", "ide", "eqs"].every((t) => A.tabs.includes(t)) && A.kb && A.claude && A.weights && A.file === "BadaNexus" && A.id === "io.github.masaaki_avnturle.badanexus");
  const sd = path.join(__dirname, "..", "dist", "nexus", "www", "index.html");
  if (fs.existsSync(sd)) { const h = fs.readFileSync(sd, "utf8"); truthy("dist/nexus に BadaClaude の頭脳・知識ベース・ContactGPT の重みを同梱", h.includes("apps/badaclaude.bada") && h.includes("window.CT_KB = {\"sources\"") && !h.includes("window.CT_WEIGHTS = null") && h.includes('id="tab-claude"')); }
}
// ---- アップデート (上書きインストール): 名前・ID・署名は毎回同じ、バージョンだけ大きくなる
{
  const cp = require("child_process"), crypto = require("crypto");
  const ver = (b) => JSON.parse(cp.execFileSync(process.execPath, [path.join(__dirname, "version.js")], { env: Object.assign({}, process.env, { CT_BUILD: String(b) }) }).toString());
  const v1 = ver(11), v2 = ver(12);
  truthy(`バージョンはビルド番号で増える: ${v1.version} (${v1.versionCode}) → ${v2.version} (${v2.versionCode})、旧版 1.0.0 (10000) より大きい`, v2.versionCode > v1.versionCode && v1.versionCode > 10000 && v2.version === "1.1.12");
  const sig = path.join(__dirname, "..", "app", "signing");
  const key = crypto.createPrivateKey({ key: fs.readFileSync(path.join(sig, "bada-apps-key.pk8")), format: "der", type: "pkcs8" });
  const cert = new crypto.X509Certificate(fs.readFileSync(path.join(sig, "bada-apps-cert.der")));
  const msg = Buffer.from("bada"), sg = crypto.sign("sha256", msg, key);
  truthy(`固定の署名鍵と証明書が対 (${cert.subject.replace(/\n/g, ", ")}、期限 ${cert.validTo})`, crypto.verify("sha256", msg, cert.publicKey, sg) && cert.keyUsage.includes("1.3.6.1.5.5.7.3.3"));
  for (const app of Object.keys(require("../apps.json"))) {
    const d = path.join(__dirname, "..", "dist", app);
    if (!fs.existsSync(path.join(d, "cordova", "config.xml"))) continue;
    const cfg = fs.readFileSync(path.join(d, "cordova", "config.xml"), "utf8"), pkg = JSON.parse(fs.readFileSync(path.join(d, "electron", "package.json"), "utf8"));
    truthy(`dist/${app}: 専用アイコン (Android / Windows / Linux)`, pkg.build.icon === "icon.png" && fs.existsSync(path.join(d, "electron", "icon.png")) && cfg.includes('<icon src="www/icon.png" />') && fs.existsSync(path.join(d, "cordova", "www", "icon.png")));
    truthy(`dist/${app}: versionCode と固定のファイル名 (${pkg.build.win.artifactName})、署名鍵を同梱`, /android-versionCode="\d+"/.test(cfg) && !/\$\{version\}/.test(pkg.build.win.artifactName + pkg.build.portable.artifactName + pkg.build.linux.artifactName) && fs.existsSync(path.join(d, "signing", "bada-apps-key.pk8")));
  }
}
const bcDist = path.join(__dirname, "..", "dist", "badaclaude", "www", "index.html");
if (fs.existsSync(bcDist)) {
  const h = fs.readFileSync(bcDist, "utf8");
  truthy("dist/badaclaude: 知識ベースと頭脳 (apps/badaclaude.bada) を同梱、接続先は api.anthropic.com だけ許可", h.includes("window.CT_KB = {\"sources\"") && h.includes("apps/badaclaude.bada") && h.includes("connect-src 'self' data: blob: file: https://api.anthropic.com;"));
}
if (fs.existsSync(dist)) {
  const h = fs.readFileSync(dist, "utf8");
  truthy("dist/nexus/www/index.html にプレースホルダが残っていない (書き出し用の PAYLOAD 以外)", !/\/\*@@(?!PAYLOAD@@)[A-Z_]+@@\*\//.test(h));
  const scripts = h.match(/<script>([\s\S]*?)<\/script>/g) || [];
  let ok = true;
  for (const s of scripts) { try { new Function(s.slice(8, -9)); } catch (e) { ok = false; console.log(e.message); } }
  truthy(`埋め込みスクリプト ${scripts.length} 個が構文的に正しい`, ok);
}

// ---- 論文 PDF → アプリ / 書き出し (非同期)
(async () => {
  const X = require("../src/exporters.js"), Lb = require("../src/badalib.js"), B = require("../src/bada.js");
  const { loadPaper } = require("./paperinfo.js");
  const qw = console.warn; console.warn = () => {};
  const qlog = console.log; console.log = (...a) => { if (!/polyfill|Require stack|^- \//.test(String(a[0]))) qlog(...a); };
  const paper = await loadPaper(path.join(__dirname, "..", "contact_blueprint.pdf"));
  console.warn = qw;
  near("[論文] contact_blueprint.pdf から方程式を抽出", paper.equations.length, 2111, 0);
  const st = new Map(eqs.map((e) => [e.id, e.status]));
  truthy("[論文] 全 2111 本の状態 (symb/calc/holds/differs) が設計図書と一致", paper.registry && paper.equations.every((e) => st.get(e.id) === e.status));
  truthy(`[論文] 題名「${paper.title}」`, paper.title.includes("Contact Transporter"));
  truthy("[論文] 数値パラメータ Γ = 64800 を本文から読む", paper.params.some((x) => x.name === "Γ" && x.value === 64800));
  near("[論文] 数式の数値評価 2^10 + √16 = 1028", require("../src/paper.js").evalNum("2^10 + √16"), 1028, 0);
  const files = H.badaFiles();
  const vm = new B.BadaVM({ host: Lb.makeHost({ files, ui: {}, chat: {}, paper: () => paper }), files });
  vm.load("#include lib/paper.bada\n");
  for (const kind of ["manifold", "ufo", "transporter"]) {
    const r = vm.call("paper_app", [kind]);
    let info = "";
    try {
      const env = { files, ui: H.stubUI(), chat: {}, scene: new Lb.Scene(), onError: (e) => { throw e; } };
      const a = new Lb.BadaApp(env); a.start(r[1], r[0]); a.call("frame", [1]); a.call("make_sheet", []);
      info = `部品 ${env.scene.parts.size}, 図面 ${env.lastSheet ? "あり" : "なし"}`;
      truthy(`[論文] Bada が書いた ${kind} アプリ ${r[0]} が動く (${info})`, env.scene.parts.size >= 8 && env.lastSheet);
      if (kind === "manifold") truthy("[論文]   on_request「一番多い分類は？」→ MANIFOLD", String(a.call("on_request", ["一番多い分類は？"])).includes("MANIFOLD"));
    } catch (e) { truthy(`[論文] Bada が書いた ${kind} アプリが動く: ${e.message}`, false); }
  }
  // 書き出し
  const enc = (t) => new TextEncoder().encode(t);
  const zip = await X.writeZip([{ name: "a.txt", data: enc("hello ".repeat(50)) }, { name: "b/c.bin", data: new Uint8Array([1, 2, 3]), store: true }]);
  const back = X.readZip(zip);
  truthy("[書き出し] ZIP の書き込み → 読み込み", back.length === 2 && new TextDecoder().decode(await X.entryData(back[0])) === "hello ".repeat(50));
  const key = { pk8: new Uint8Array(fs.readFileSync(path.join(__dirname, "..", "app", "signing", "debug-key.pk8"))), cert: new Uint8Array(fs.readFileSync(path.join(__dirname, "..", "app", "signing", "debug-cert.der"))) };
  const tpl = await X.writeZip([{ name: "AndroidManifest.xml", data: enc("<m/>".repeat(30)) }, { name: "resources.arsc", data: enc("R".repeat(200)), store: true }, { name: "assets/www/index.html", data: enc("<html><head></head></html>") }]);
  const apk = await X.buildApk(tpl, "<html><head></head><body>論文アプリ</body></html>", key);
  const ents = X.readZip(apk).map((e) => e.name);
  truthy("[書き出し] APK に MANIFEST.MF / CERT.SF / CERT.RSA と差し替えた index.html", ["META-INF/MANIFEST.MF", "META-INF/CERT.SF", "META-INF/CERT.RSA", "assets/www/index.html"].every((n) => ents.includes(n)));
  const cp = require("child_process");
  let hasJar = false; try { cp.execSync("jarsigner -help", { stdio: "ignore" }); hasJar = true; } catch (e) { /* jarsigner なし */ }
  if (hasJar) {
    const tmp = path.join(require("os").tmpdir(), "ct_test.apk"); fs.writeFileSync(tmp, apk);
    const out = cp.execSync(`jarsigner -verify "${tmp}" 2>&1`).toString();
    truthy("[書き出し] APK の JAR 署名を jarsigner が検証 (jar verified)", out.includes("jar verified"));
  }
  const deb = await X.buildDeb({ pkg: "Bada Test", title: "テスト", description: "d", html: "<html></html>" });
  const debStr = new TextDecoder().decode(deb.bytes.subarray(0, 200));
  truthy("[書き出し] .deb (ar: debian-binary / control.tar.gz / data.tar.gz)", debStr.startsWith("!<arch>\n") && debStr.includes("debian-binary") && new TextDecoder("latin1").decode(deb.bytes).includes("data.tar.gz") && deb.pkg === "bada-test");
  truthy(`[書き出し] 論文アプリ .deb のバージョンは作成日時 (${deb.version}) — 作り直すと apt で上書きアップデート`, /^1\.0\.\d{12}$/.test(deb.version) && new TextDecoder("latin1").decode(deb.bytes).length > 0);
  const lpath = path.join(__dirname, "..", "data", "bada-launcher.exe");
  const launcher = fs.existsSync(lpath) ? new Uint8Array(fs.readFileSync(lpath)) : new Uint8Array([0x4d, 0x5a, 0, 0]);
  const exe = X.buildWinExe(launcher, [{ name: "index.html", data: "<html>論文アプリ</html>" }, { name: "a.bada", data: "say 1" }], "bada-test");
  const back2 = X.readWinExe(exe);
  truthy("[書き出し] Windows EXE (ランチャー + アプリ一式) の末尾を読み戻せる", exe[0] === 0x4d && exe[1] === 0x5a && new TextDecoder().decode(back2["index.html"]) === "<html>論文アプリ</html>" && new TextDecoder().decode(back2["app.id"]) === "bada-test");
  const pdf = X.imagePdf([{ jpeg: new Uint8Array([0xff, 0xd8, 0xff, 0xd9]), w: 10, h: 14 }, { jpeg: new Uint8Array([0xff, 0xd8, 0xff, 0xd9]), w: 14, h: 10 }], "設計書");
  const pdfjs = require("pdfjs-dist/legacy/build/pdf.js");
  const d = await pdfjs.getDocument({ data: pdf }).promise;
  truthy(`[書き出し] 設計書 PDF (画像ページ) を pdf.js が読める: ${d.numPages} ページ`, d.numPages === 2);
  const runner = path.join(__dirname, "..", "dist", "runner", "www", "index.html");
  if (fs.existsSync(runner)) {
    const html = X.standaloneHtml(fs.readFileSync(runner, "utf8"), { title: "T", main: "user/x.bada", files: { "user/x.bada": "say 1" } });
    truthy("[書き出し] 単体 HTML アプリに Bada ソースを同梱", html.includes('window.CT_PAYLOAD = {"title":"T","main":"user/x.bada","files":{"user/x.bada":"say 1"}}'));
  }
  console.log = qlog;
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
