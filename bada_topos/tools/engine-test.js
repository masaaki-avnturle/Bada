/*
 * engine-test.js — Bada 位相 (topos) のエンジン単体テスト (Node で実行)
 *
 *   node bada_topos/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. 複素状態ベクトルと基本ゲート (ベル状態・GHZ・オイラーの位相ゲート)
 *   2. 単体的複体 — 閉包・除去・名前
 *   3. 【定理】∂∂ = 0 (向き付き実係数 / Z_2) — 全模型
 *   4. 【定理】ベッチ数とオイラー・ポアンカレ公式 — 全模型
 *   5. 境界回路 ∂̂ — |c⟩|0⟩ ↦ |c⟩|∂c⟩ を古典の ∂ と照合
 *   6. 閉路フィルタ — 観測確率 2^{dim Z − n_k} と古典階数の一致、観測結果はすべて閉路
 *   7. 【定理】ホッジ — dim ker Δ_k = β_k、分解の直交性と再構成
 *   8. 【不変量】量子歩行 — ユニタリ性と観念成分の保存
 *   9. 理解 (面を張る) と分裂 (連想を切る)
 *  10. 思考の分類 (開いた鎖 / 境界 / 観念)
 *  11. 位相 Bada インタプリタ (英語 + 日本語表記)
 *  12. 生成AIカーネル (5 段パイプラインと生成物の実行検証)
 *  13. 限界 — 量子ビット上限は明示的な誤りとして返る
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

function stubEl(){
  return new Proxy({ style:{}, classList:{ add(){}, remove(){} }, value:"", textContent:"", innerHTML:"", className:"", height:300 }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "getAttribute") return function(){ return ""; };
      if (p === "getContext") return function(){ return stubCtx(); };
      if (p === "clientWidth" || p === "clientHeight") return 600;
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
function stubCtx(){ return new Proxy({}, { get(){ return function(){}; }, set(){ return true; } }); }
const sandbox = {
  console, Math, Date, Object, Array, String, Number, JSON, Float64Array, Proxy, parseInt, parseFloat,
  setTimeout: fn => fn(), setInterval: () => 0, clearInterval(){},
  window: { addEventListener(){} },
  document: {
    readyState: "complete",
    getElementById(){ return stubEl(); },
    createElement(){ return stubEl(); },
    querySelectorAll(){ return []; },
    addEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });
const G = name => vm.runInContext(name, sandbox);

let failures = 0;
function assert(cond, msg){
  if (!cond){ console.error("FAIL: " + msg); failures++; }
  else console.log("ok - " + msg);
}
function close(a, b, eps, msg){ assert(Math.abs(a - b) < eps, msg + "  (" + a + " vs " + b + ")"); }

const qsNew = G("qsNew"), qsProbs = G("qsProbs"), qsNormSq = G("qsNormSq"), qsClone = G("qsClone");
const gateH = G("gateH"), gateX = G("gateX"), gateCNOT = G("gateCNOT"), gatePhase = G("gatePhase");
const qsMeasure = G("qsMeasure"), qsSubProb = G("qsSubProb"), qsProject = G("qsProject"), bitOf = G("bitOf");
const cxNew = G("cxNew"), cxVertex = G("cxVertex"), cxAdd = G("cxAdd"), cxRemove = G("cxRemove"), cxHas = G("cxHas");
const cxSimplices = G("cxSimplices"), cxCounts = G("cxCounts"), cxDim = G("cxDim"), cxName = G("cxName"), cxParse = G("cxParse");
const cxBoundary = G("cxBoundary"), z2Rank = G("z2Rank"), cxBetti = G("cxBetti"), cxEuler = G("cxEuler"), cxDDZero = G("cxDDZero");
const cxClassify = G("cxClassify"), cxChainBoundary = G("cxChainBoundary");
const boundaryCircuit = G("boundaryCircuit"), circuitApply = G("circuitApply"), cycleFilter = G("cycleFilter"), chainOfIndex = G("chainOfIndex");
const cxHodge = G("cxHodge"), symEig = G("symEig"), hodgeDecompose = G("hodgeDecompose"), walkEvolve = G("walkEvolve"), harmonicNorm = G("harmonicNorm"), vecNormSq = G("vecNormSq");
const presetComplex = G("presetComplex"), PRESETS = G("PRESETS"), toposInterpret = G("toposInterpret"), aiCompose = G("aiCompose"), toposRng = G("toposRng"), QMAX = G("QMAX");

const PRESET_KEYS = Object.keys(PRESETS);

/* ════ 1. 状態ベクトルとゲート ════ */
console.log("\n── 1. 複素状態ベクトルと基本ゲート ──");
{
  let st = qsNew(2, 0);
  st = gateH(st, 0); st = gateCNOT(st, 0, 1);
  const p = qsProbs(st);
  close(p[0], 0.5, 1e-12, "ベル状態 |00⟩ の確率 1/2");
  close(p[3], 0.5, 1e-12, "ベル状態 |11⟩ の確率 1/2");
  let g = qsNew(3, 0);
  g = gateH(g, 0); g = gateCNOT(g, 0, 1); g = gateCNOT(g, 1, 2);
  const pg = qsProbs(g);
  close(pg[0] + pg[7], 1, 1e-12, "GHZ 状態は |000⟩ と |111⟩ だけ");
  let x = gateX(qsNew(2, 0), 1);
  close(qsProbs(x)[1], 1, 1e-12, "X q1 |00⟩ = |01⟩");
  let ph = gatePhase(gateX(qsNew(1, 0), 0), 0, Math.PI / 3);
  close(ph.re[1], Math.cos(Math.PI / 3), 1e-12, "オイラーの式: 位相ゲートの実部 = cos θ");
  close(ph.im[1], Math.sin(Math.PI / 3), 1e-12, "オイラーの式: 位相ゲートの虚部 = sin θ");
  close(qsNormSq(ph), 1, 1e-12, "位相ゲートはノルムを保つ");
  let s2 = gateH(qsNew(2, 0), 0);
  close(qsSubProb(s2, [0], 0), 0.5, 1e-12, "部分レジスタの確率 (H|0⟩ で q0 = 0 は 1/2)");
  const pr = qsProject(s2, [0], 0);
  close(pr, 0.5, 1e-12, "射影は確率を返す");
  close(qsNormSq(s2), 1, 1e-12, "射影後は規格化されている");
  close(qsSubProb(s2, [0], 0), 1, 1e-12, "射影後は q0 = 0 が確定");
}

/* ════ 2. 単体的複体 ════ */
console.log("\n── 2. 単体的複体 — 閉包・除去 ──");
{
  const cx = cxNew("T");
  ["a", "b", "c", "d"].forEach(v => cxVertex(cx, v));
  const r = cxAdd(cx, ["a", "b", "c"]);
  assert(r.added.length === 4, "面 abc の追加は閉包で辺 3 + 面 1 = 4 単体を加える");
  assert(cxHas(cx, [0, 1]) && cxHas(cx, [1, 2]) && cxHas(cx, [0, 2]), "閉包 — すべての辺が存在する");
  assert(cxCounts(cx).join(",") === "4,3,1", "単体数 (4, 3, 1)");
  assert(cxDim(cx) === 2, "次元 2");
  assert(cxName(cx, [0, 2]) === "a-c", "単体名は頂点名を - で結ぶ");
  assert(cxParse(cx, "c-a").join(",") === "0,2", "単体の解析は順序に依らない");
  let threw = false; try { cxParse(cx, "a-d"); } catch (e){ threw = true; }
  assert(threw, "複体にない単体の解析は誤りになる");
  const rem = cxRemove(cx, ["a", "b"]);
  assert(rem.length === 2, "辺 ab の除去は辺と、それを含む面の 2 単体を除く");
  assert(cxCounts(cx).join(",") === "4,2", "除去後の単体数 (4, 2)");
  assert(cxVertex(cx, "a") === 0, "既存頂点の再宣言は同じ id を返す");
}

/* ════ 3. ∂∂ = 0 ════ */
console.log("\n── 3. 【定理】∂∂ = 0 ──");
for (const key of PRESET_KEYS){
  const cx = presetComplex(key);
  let ok = true;
  for (let k = 2; k <= cxDim(cx) + 1; k++) ok = ok && cxDDZero(cx, k);
  assert(ok, "模型 " + key + " で ∂_{k-1}∂_k = 0 (向き付き)");
  /* Z_2 でも: 各 (k)-単体の境界の境界が空 */
  let z2ok = true;
  for (let k = 2; k <= cxDim(cx); k++){
    const B = cxBoundary(cx, k), Bl = cxBoundary(cx, k - 1);
    for (let j = 0; j < B.cols.length; j++){
      const bd = cxChainBoundary(B, [j]);
      if (cxChainBoundary(Bl, bd).length) z2ok = false;
    }
  }
  assert(z2ok, "模型 " + key + " で ∂∂ = 0 (Z_2)");
}

/* ════ 4. ベッチ数とオイラー ════ */
console.log("\n── 4. 【定理】ベッチ数とオイラー・ポアンカレ ──");
{
  const expect = { center:"1,1,0", triangle:"1,1", filled:"1,0,0", sphere:"1,0,1", eight:"1,2", split:"2,1,0" };
  for (const key of PRESET_KEYS){
    const cx = presetComplex(key), b = cxBetti(cx), e = cxEuler(cx);
    assert(b.join(",") === expect[key], "模型 " + key + " のベッチ数 (" + b.join(",") + ")");
    assert(e.byCount === e.byBetti, "模型 " + key + " で χ(単体数) = χ(ベッチ数) = " + e.byCount);
  }
  assert(cxEuler(presetComplex("sphere")).byCount === 2, "球面の χ = 2");
  assert(cxEuler(presetComplex("triangle")).byCount === 0, "環 (三角形の縁) の χ = 0");
  assert(z2Rank([[1, 1, 0], [0, 1, 1], [1, 0, 1]]) === 2, "Z_2 階数 (3 列ベクトルが従属)");
  assert(z2Rank([]) === 0 && z2Rank([[]]) === 0, "空行列の階数 0");
}

/* ════ 5. 境界回路 ════ */
console.log("\n── 5. 境界回路 ∂̂ : |c⟩|0⟩ ↦ |c⟩|∂c⟩ ──");
{
  const rnd = toposRng(11);
  for (const key of ["center", "sphere", "eight"]){
    const cx = presetComplex(key);
    for (let k = 1; k <= cxDim(cx); k++){
      const circ = boundaryCircuit(cx, k), B = circ.B;
      let nz = 0; B.M.forEach(r => r.forEach(v => { if (v) nz++; }));
      assert(circ.gates.length === nz, "模型 " + key + " k=" + k + ": CNOT 数 = ∂ の非零成分数 " + nz);
      let allOk = true;
      for (let trial = 0; trial < 6; trial++){
        const cols = [];
        for (let j = 0; j < circ.nk; j++) if (rnd() < 0.5) cols.push(j);
        let idx = 0;
        cols.forEach(j => { idx |= 1 << (circ.qubits - 1 - j); });
        let st = qsNew(circ.qubits, idx);
        st = circuitApply(st, circ.gates);
        const p = qsProbs(st);
        let hit = -1; for (let i = 0; i < p.length; i++) if (p[i] > 0.5) hit = i;
        const bd = cxChainBoundary(B, cols);
        let want = idx;
        bd.forEach(i => { want |= 1 << (circ.qubits - 1 - (circ.nk + i)); });
        if (hit !== want) allOk = false;
      }
      assert(allOk, "模型 " + key + " k=" + k + ": 回路の ∂c が古典の ∂c と一致 (6 鎖)");
    }
  }
  let threw = false; try { boundaryCircuit(presetComplex("triangle"), 2); } catch (e){ threw = true; }
  assert(threw, "存在しない次数の回路は誤りになる");
}

/* ════ 6. 閉路フィルタ ════ */
console.log("\n── 6. 閉路フィルタ — 観測確率から閉路空間の次元を読む ──");
{
  for (const key of PRESET_KEYS){
    const cx = presetComplex(key);
    for (let k = 0; k <= cxDim(cx); k++){
      const f = cycleFilter(cx, k, { seed: 5, samples: 8 });
      close(f.dimZq, f.dimZc, 1e-9, "模型 " + key + " k=" + k + ": dim Z (量子 = n_k + log₂ Pr) = dim Z (古典) = " + f.dimZc);
      close(f.prob0, Math.pow(2, f.dimZc - f.circuit.nk), 1e-12, "模型 " + key + " k=" + k + ": Pr[面 = 0] = 2^{dim Z − n_k}");
      assert(f.samples.every(s => s.cls.kind !== "open"), "模型 " + key + " k=" + k + ": 観測した思考はすべて閉じている");
      close(qsNormSq(f.state), 1, 1e-12, "模型 " + key + " k=" + k + ": 射影後の状態は規格化");
    }
  }
  const tri = cycleFilter(presetComplex("triangle"), 1, { seed: 3, samples: 12 });
  assert(tri.samples.some(s => s.cls.kind === "idea"), "三角形 (問い): 観測に観念 (境界でない閉路) が現れる");
  assert(tri.nCycles === 2, "三角形の閉路は零鎖と環の 2 通り");
  const fil = cycleFilter(presetComplex("filled"), 1, { seed: 3, samples: 12 });
  assert(fil.samples.every(s => s.cls.kind === "boundary" || s.cls.kind === "zero"), "充填三角形 (理解): 観測した閉路はすべて境界 — 観念はない");
  const sph = cycleFilter(presetComplex("sphere"), 2, { seed: 2, samples: 12 });
  assert(sph.samples.some(s => s.names.length === 4 && s.cls.kind === "idea"), "球面: 4 面すべての和が H_2 の観念として観測される");
}

/* ════ 7. ホッジ ════ */
console.log("\n── 7. 【定理】ホッジ — dim ker Δ_k = β_k ──");
{
  const A = [[2, 1], [1, 2]], e = symEig(A);
  const vals = e.vals.slice().sort((a, b) => a - b);
  close(vals[0], 1, 1e-9, "ヤコビ法: 固有値 1"); close(vals[1], 3, 1e-9, "ヤコビ法: 固有値 3");
  for (const key of PRESET_KEYS){
    const cx = presetComplex(key), b = cxBetti(cx);
    for (let k = 0; k <= cxDim(cx); k++){
      const n = cxSimplices(cx, k).length;
      const v = []; for (let i = 0; i < n; i++) v.push(Math.sin(i + 1) + 0.3 * k);
      const hd = hodgeDecompose(cx, k, v);
      assert(hd.dims.harmonic === b[k], "模型 " + key + " k=" + k + ": dim ker Δ = β_k = " + b[k]);
      assert(hd.dims.exact + hd.dims.harmonic + hd.dims.coexact === n, "模型 " + key + " k=" + k + ": 分解の次元和 = n_k");
      let recon = 0, o1 = 0, o2 = 0, o3 = 0;
      for (let i = 0; i < n; i++){
        recon += Math.abs(v[i] - hd.harmonic[i] - hd.exact[i] - hd.coexact[i]);
        o1 += hd.harmonic[i] * hd.exact[i]; o2 += hd.harmonic[i] * hd.coexact[i]; o3 += hd.exact[i] * hd.coexact[i];
      }
      assert(recon < 1e-8, "模型 " + key + " k=" + k + ": v = 完全 + 調和 + 余完全 に再構成される");
      assert(Math.abs(o1) + Math.abs(o2) + Math.abs(o3) < 1e-8, "模型 " + key + " k=" + k + ": 三成分は互いに直交");
      /* 調和成分は Δ で消える */
      let lh = 0;
      for (let i = 0; i < n; i++){ let s = 0; for (let j = 0; j < n; j++) s += hd.L[i][j] * hd.harmonic[j]; lh += Math.abs(s); }
      assert(lh < 1e-8, "模型 " + key + " k=" + k + ": Δ(調和成分) = 0");
    }
  }
}

/* ════ 8. 量子歩行 ════ */
console.log("\n── 8. 【不変量】量子歩行 — 観念は動かない ──");
{
  for (const key of ["center", "eight", "sphere", "split"]){
    const cx = presetComplex(key);
    for (let k = 0; k <= Math.min(1, cxDim(cx)); k++){
      const n = cxSimplices(cx, k).length, re0 = [], im0 = [];
      for (let i = 0; i < n; i++){ re0.push(0); im0.push(0); }
      re0[0] = 1;
      const hd = hodgeDecompose(cx, k, re0), h0 = harmonicNorm(hd.eig, re0, im0);
      let unit = true, inv = true, moved = false;
      for (const t of [0.3, 1.7, 4.2, 9.9, 25]){
        const p = walkEvolve(hd.eig, re0, im0, t);
        if (Math.abs(vecNormSq(p.re, p.im) - 1) > 1e-9) unit = false;
        if (Math.abs(harmonicNorm(hd.eig, p.re, p.im) - h0) > 1e-9) inv = false;
        if (Math.abs(p.re[0] * p.re[0] + p.im[0] * p.im[0] - 1) > 1e-6) moved = true;
      }
      assert(unit, "模型 " + key + " k=" + k + ": 歩行はユニタリ (‖ψ‖² = 1)");
      assert(inv, "模型 " + key + " k=" + k + ": 観念成分 ‖P_H ψ‖² は時間で不変");
      /* 始点が Δ の固有ベクトルなら位相だけが回る (|ψ|² は動かない)。そうでなければ流れる */
      let lam = 0, resid = 0;
      for (let i = 0; i < n; i++) lam += re0[i] * hd.L[i][0];
      for (let i = 0; i < n; i++) resid += Math.abs(hd.L[i][0] - lam * re0[i]);
      if (resid > 1e-9) assert(moved, "模型 " + key + " k=" + k + ": 始点が固有ベクトルでないので思考は流れる");
      else assert(!moved, "模型 " + key + " k=" + k + ": 始点が Δ の固有ベクトル (λ = " + lam + ") なので位相だけが回り |ψ|² は動かない");
    }
  }
  const cx = presetComplex("filled"), re0 = [1, 0, 0], im0 = [0, 0, 0];
  const hd = hodgeDecompose(cx, 1, re0);
  close(harmonicNorm(hd.eig, re0, im0), 0, 1e-12, "充填三角形の連想には観念成分がない (β₁ = 0)");
  const tri = presetComplex("triangle"), hdt = hodgeDecompose(tri, 1, re0);
  close(harmonicNorm(hdt.eig, re0, im0), 1 / 3, 1e-9, "三角形 (問い) の一辺は観念成分 1/3 を持つ");
}

/* ════ 9. 理解と分裂 ════ */
console.log("\n── 9. 理解 (面を張る) と分裂 (連想を切る) ──");
{
  const cx = presetComplex("triangle");
  assert(cxBetti(cx)[1] === 1, "三角形: 問い 1");
  cxAdd(cx, ["a", "b", "c"]);
  assert(cxBetti(cx)[1] === 0, "理解 (面を張る) で β₁ が 1 → 0");
  assert(cxEuler(cx).byCount === 1, "充填後の χ = 1");
  const c2 = presetComplex("center");
  assert(cxBetti(c2)[0] === 1 && cxBetti(c2)[1] === 1, "思考中枢: 中枢 1・問い 1");
  cxRemove(c2, ["判断", "発話"]);
  assert(cxBetti(c2)[1] === 0, "環の連想を切ると問いは問えなくなる (β₁ 1 → 0)");
  cxRemove(c2, ["意味", "判断"]);
  cxRemove(c2, ["記憶", "判断"]);
  assert(cxBetti(c2)[0] === 2, "連想を切り続けると中枢が分裂する (β₀ 1 → 2)");
}

/* ════ 10. 思考の分類 ════ */
console.log("\n── 10. 思考の分類 ──");
{
  const cx = presetComplex("center"), B = cxBoundary(cx, 1);
  const col = name => B.cols.findIndex(s => cxName(cx, s) === name);
  const loop = ["感覚-意味", "意味-判断", "判断-発話", "発話-行動", "感覚-行動"].map(col);
  assert(cxClassify(cx, 1, loop).kind === "idea", "感覚→意味→判断→発話→行動→感覚 の環は観念 (どの理解にも埋められていない)");
  const tri = ["意味-記憶", "記憶-判断", "意味-判断"].map(col);
  assert(cxClassify(cx, 1, tri).kind === "boundary", "意味-記憶-判断 の環は境界 (理解 意味-記憶-判断 から導かれる)");
  const open = ["感覚-意味", "意味-判断"].map(col);
  const oc = cxClassify(cx, 1, open);
  assert(oc.kind === "open" && oc.boundary.length === 2, "感覚-意味 + 意味-判断 は開いた鎖 (∂c = 感覚 + 判断)");
  assert(cxClassify(cx, 1, []).kind === "zero", "空の鎖は零鎖");
}

/* ════ 11. インタプリタ ════ */
console.log("\n── 11. 位相 Bada インタプリタ ──");
{
  const out = toposInterpret([
    "preset center", "betti", "euler", "circuit 1", "filter 1 seed 4", "harmonic 1",
    "walk 1 from 感覚-意味 time 2.5", "think 感覚-意味 意味-判断 判断-発話 発話-行動 行動-感覚",
    "fill 判断 発話 行動", "betti", "cut 意味 記憶", "let x = 2*(3+4)", "print x"
  ].join("\n"), { seed: 1 });
  assert(out.indexOf("!!") < 0, "英語表記のプログラムが誤りなく実行される");
  assert(/β = \(1, 1, 0\)/.test(out), "betti が (1, 1, 0) を出す");
  assert(/オイラー・ポアンカレ ✓/.test(out), "euler が両方の式の一致を報告する");
  assert(/CNOT 14 個/.test(out), "circuit 1 が CNOT 14 個を報告する");
  assert(/古典 2 ✓/.test(out), "filter 1 が dim Z₁ = 2 の一致を報告する");
  assert(/ホッジの定理 ✓/.test(out), "harmonic 1 がホッジの定理を報告する");
  assert(/観念は動かない ✓/.test(out), "walk が観念の保存を報告する");
  assert(/観念 — 閉じているのに/.test(out), "think が環を観念として分類する");
  assert(/理解に変わる|問いが 1 つ解けて|観念は変わらない/.test(out), "fill が結果を報告する");
  assert(/x = 14/.test(out) && /\n14$/.test(out), "let / print が動く");

  const ja = toposInterpret([
    "複体 中枢", "頂点 a b c", "辺 a b", "辺 b c", "辺 a c", "ベッチ", "オイラー",
    "思考 a-b b-c a-c", "閉路 1 種 2", "理解 a b c", "ベッチ", "状態"
  ].join("\n"), { seed: 1 });
  assert(ja.indexOf("!!") < 0, "日本語表記のプログラムが誤りなく実行される");
  assert(/β = \(1, 1\)/.test(ja) && /β = \(1, 0, 0\)/.test(ja), "日本語: 理解で β₁ が 1 → 0");
  assert(/問いが 1 つ解けて理解になった/.test(ja), "日本語: 理解の報告文");

  const err = toposInterpret("preset nothing\nthink a-b\nfoo bar", {});
  assert((err.match(/!!/g) || []).length === 3, "誤りは行番号つきの注記になり実行は続く");
}

/* ════ 12. 生成AI ════ */
console.log("\n── 12. 生成AIカーネル ──");
{
  const cases = [
    ["思考中枢を組んで形を読んで", "center"], ["閉じているのに解けていない問いを回路で取り出して", "filter"],
    ["三角形の問いを理解して解いて", "fill"], ["思考中枢を歩かせて観念が動かないことを見せて", "walk"],
    ["連想を切って中枢を分裂させて", "split"], ["hello", "basic"]
  ];
  for (const [q, want] of cases){
    const r = aiCompose(q);
    assert(r.intent === want, "意図解析: 「" + q + "」 → " + want);
    assert(r.stages.length === 5, "5 段パイプラインを開示する");
    assert(r.ok, "生成物が誤りなく実行される (" + want + ")");
  }
}

/* ════ 13. 限界 ════ */
console.log("\n── 13. 限界 ──");
{
  let threw = false; try { qsNew(QMAX + 1, 0); } catch (e){ threw = true; }
  assert(threw, "量子ビット上限 " + QMAX + " を超える状態は明示的な誤り");
  const cx = cxNew("big");
  for (let i = 0; i < 12; i++) cxVertex(cx, "v" + i);
  for (let i = 0; i < 12; i++) cxAdd(cx, ["v" + i, "v" + ((i + 1) % 12)]);
  for (let i = 0; i < 12; i++) cxAdd(cx, ["v" + i, "v" + ((i + 5) % 12)]);
  let threw2 = false; try { cycleFilter(cx, 1, {}); } catch (e){ threw2 = e.message.indexOf("上限") >= 0; }
  assert(threw2, "大きすぎる複体の閉路フィルタは上限の誤りを返す (古典の不変量は動く: β = " + cxBetti(cx).join(",") + ")");
}

console.log("\n" + (failures ? failures + " failure(s)" : "all tests passed"));
process.exit(failures ? 1 : 0);
