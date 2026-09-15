/*
 * engine-test.js — Bada 遊 (asobi) のエンジン単体テスト (Node で実行)
 *
 *   node bada_asobi/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. 複素状態ベクトルと基本ゲート (ベル状態・GHZ)
 *   2. パウリ代数 (適用・期待値・反交換判定)
 *   3. 違反思考 = 部分回転 exp(−iθV/2) — ユニタリ性と cos/sin の振幅
 *   4. 最小違反生成子 — 狙った規則だけを破り、他の規範と不可侵を保つ
 *   5. 【不変量】不可侵規則は遊びの中でも観測の後でも保存される
 *   6. 【不変量】円環の帰還 C†C = I — 状態は外へ漏れない
 *   7. 【不変量】考えは行為にならない (θ ≤ θmax < π)
 *   8. 【不変量】遊び予算の保存 (Σθ ≤ Δ)
 *   9. 変異の単調性 — 円環内の評価が許した観測は適応度を下げない
 *  10. 違反思考変異 (TTM) vs 古典的無作為変異 — 複数種での比較
 *  11. 遊びゼロは焼き付く (予算 0 で探索が止まる)
 *  12. 規範の弛緩・制度化と遊び台帳
 *  13. Bada 遊 インタプリタ (量子 Bada + 遊びの語彙 + 日本語表記)
 *  14. 生成AIカーネル (5 段パイプラインと生成物の実行検証)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* ── DOM スタブ (エンジン部は DOM に触れない。boot() だけが触る) ── */
function stubEl(){
  return new Proxy({ style:{}, classList:{ add(){}, remove(){} }, value:"", textContent:"", innerHTML:"", className:"" }, {
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
function stubCtx(){
  return new Proxy({}, { get(){ return function(){}; }, set(){ return true; } });
}
const sandbox = {
  console, Math, Date, Object, Array, String, Number, JSON, Float64Array, Proxy,
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

const qsNew = G("qsNew"), qsProbs = G("qsProbs"), qsNormSq = G("qsNormSq"), qsDiff = G("qsDiff");
const qsClone = G("qsClone"), qsMeasure = G("qsMeasure"), gateH = G("gateH"), gateCNOT = G("gateCNOT");
const pauliApply = G("pauliApply"), pauliExpect = G("pauliExpect"), pauliAnticommute = G("pauliAnticommute");
const rotApply = G("rotApply"), violationGen = G("violationGen"), violationGens = G("violationGens");
const nkLandscape = G("nkLandscape"), trapLandscape = G("trapLandscape");
const defaultRules = G("defaultRules"), constrainedRules = G("constrainedRules"), ruleConform = G("ruleConform");
const ttmInit = G("ttmInit"), ttmStep = G("ttmStep"), ttmRun = G("ttmRun"), gaClassicRun = G("gaClassicRun");
const asobiInterpret = G("asobiInterpret"), aiCompose = G("aiCompose"), asobiRng = G("asobiRng");
const THETA_MAX = G("THETA_MAX"), popEntropy = G("popEntropy"), initPop = G("initPop");

/* ════ 1. 状態ベクトルと基本ゲート ════ */
console.log("\n── 1. 複素状態ベクトルと基本ゲート ──");
{
  let st = qsNew(2, 0);
  st = gateH(st, 0); st = gateCNOT(st, 0, 1);
  const p = qsProbs(st);
  close(p[0], 0.5, 1e-12, "ベル状態 |00⟩ の確率 1/2");
  close(p[3], 0.5, 1e-12, "ベル状態 |11⟩ の確率 1/2");
  close(p[1] + p[2], 0, 1e-12, "ベル状態に |01⟩ |10⟩ は現れない");
  let g = qsNew(3, 0);
  g = gateH(g, 0); g = gateCNOT(g, 0, 1); g = gateCNOT(g, 1, 2);
  const pg = qsProbs(g);
  close(pg[0], 0.5, 1e-12, "GHZ 状態 |000⟩ の確率 1/2");
  close(pg[7], 0.5, 1e-12, "GHZ 状態 |111⟩ の確率 1/2");
}

/* ════ 2. パウリ代数 ════ */
console.log("\n── 2. パウリ代数 ──");
{
  const z00 = qsNew(2, 0), z10 = qsNew(2, 2);
  close(pauliExpect(z00, [{q:0,p:"Z"},{q:1,p:"Z"}]), 1, 1e-12, "⟨ZZ⟩ = +1 (偶パリティ = 遵守)");
  close(pauliExpect(z10, [{q:0,p:"Z"},{q:1,p:"Z"}]), -1, 1e-12, "⟨ZZ⟩ = −1 (奇パリティ = 違反)");
  close(pauliExpect(z00, [{q:0,p:"X"}]), 0, 1e-12, "基底状態での ⟨X⟩ = 0");
  assert(pauliAnticommute([{q:0,p:"X"}], [{q:0,p:"Z"},{q:1,p:"Z"}]), "X g0 は Z g0 Z g1 と反交換する (= 違反しうる)");
  assert(!pauliAnticommute([{q:0,p:"X"},{q:1,p:"X"}], [{q:0,p:"Z"},{q:1,p:"Z"}]), "X g0 X g1 は Z g0 Z g1 と可換 (= 違反にならない)");
  assert(!pauliAnticommute([{q:2,p:"X"}], [{q:0,p:"Z"},{q:1,p:"Z"}]), "台が交わらないパウリは可換");
  const y = pauliApply(qsNew(1, 0), [{q:0,p:"Y"}]);
  close(y.im[1], 1, 1e-12, "Y|0⟩ = i|1⟩ (虚振幅として実装されている)");
}

/* ════ 3. 違反思考 = 部分回転 ════ */
console.log("\n── 3. 違反思考 exp(−iθV/2) ──");
{
  const V = [{q:0,p:"X"}], S = [{q:0,p:"Z"},{q:1,p:"Z"}];
  for (const th of [0, 0.3, 0.7, 1.4, 2.2, THETA_MAX]){
    const st = rotApply(qsNew(2, 0), V, th);
    close(qsNormSq(st), 1, 1e-12, "θ=" + th.toFixed(2) + " でもユニタリ (ノルム保存)");
  }
  const st = rotApply(qsNew(2, 0), V, 0.9);
  const p = qsProbs(st);
  close(p[0], Math.cos(0.45) ** 2, 1e-12, "遵守枝の確率 = cos²(θ/2)");
  close(p[2], Math.sin(0.45) ** 2, 1e-12, "違反枝の確率 = sin²(θ/2) = 遊び");
  close(pauliExpect(st, S), Math.cos(0.9), 1e-12, "⟨S⟩ = cos θ — 考えの深さがそのまま遵守度の低下");
  close(pauliExpect(rotApply(qsNew(2,0), V, 0), S), 1, 1e-12, "θ=0 は完全遵守 (遊びゼロ)");
  close(pauliExpect(rotApply(qsNew(2,0), V, Math.PI), S), -1, 1e-12, "θ=π は完全な違反 = 行為");
  assert(THETA_MAX < Math.PI - 0.1, "θmax は π より手前 — 考えは行為に届かない");
}

/* ════ 4. 最小違反生成子 ════ */
console.log("\n── 4. 最小違反生成子 ──");
{
  const n = 6;
  const R1 = [{q:0,p:"Z"},{q:1,p:"Z"}], R2 = [{q:1,p:"Z"},{q:2,p:"Z"}], R3 = [{q:2,p:"Z"},{q:3,p:"Z"}];
  const S0 = [{q:4,p:"Z"},{q:5,p:"Z"}];
  const V = violationGen(R2, [R1, R3, S0], n);
  assert(V !== null, "他の規範と不可侵を保ったまま R2 を破る生成子が存在する");
  assert(pauliAnticommute(V, R2), "生成子は狙った規則 R2 とだけ反交換する");
  assert(!pauliAnticommute(V, R1) && !pauliAnticommute(V, R3), "生成子は他の規範 R1 R3 と可換 (壊さない)");
  assert(!pauliAnticommute(V, S0), "生成子は不可侵規則 S0 と可換");
  assert(V.length >= 2, "鎖の内側の規則を破る最小生成子は協調反転になる (重み " + V.length + " — 単一ビット反転では足りない)");
  const Vend = violationGen(R1, [R2, R3, S0], n);
  assert(Vend.length === 1, "鎖の末端の規則は単一反転で破れる (遊びの深さは規範の絡み方で決まる)");
  const all = violationGens(R2, [R1, R3, S0], n);
  assert(all.every(v => v.length === V.length), "返る候補はすべて最小重み");
  assert(all.length > 1, "最小重みの候補が複数ある (遊びには選択の幅がある: " + all.length + " 通り)");
  const impossible = violationGen(S0, [S0], n);
  assert(impossible === null, "自分自身を保ったまま破ることはできない (遊べない規則)");
}

/* ════ 5. 不可侵規則の保存 ════ */
console.log("\n── 5. 【不変量】不可侵規則は遊びの中でも観測の後でも保存される ──");
{
  const n = 6, rnd = asobiRng(99);
  const S0 = [{q:4,p:"Z"},{q:5,p:"Z"}];
  const rules = [[{q:0,p:"Z"},{q:1,p:"Z"}], [{q:1,p:"Z"},{q:2,p:"Z"}], [{q:2,p:"Z"},{q:3,p:"Z"}]];
  let bad = 0, measured = 0;
  for (let trial = 0; trial < 40; trial++){
    let st = qsNew(n, Math.floor(rnd() * 16) * 4);          /* g4 g5 = 00 → ⟨S0⟩ = +1 */
    const before = pauliExpect(st, S0);
    for (let step = 0; step < 4; step++){
      const target = rules[Math.floor(rnd() * rules.length) % rules.length];
      const keep = rules.filter(r => r !== target).concat([S0]);
      const V = violationGen(target, keep, n);
      if (!V) continue;
      st = rotApply(st, V, rnd() * THETA_MAX);
      if (Math.abs(pauliExpect(st, S0) - before) > 1e-9) bad++;
    }
    qsMeasure(st, rnd); measured++;
    if (Math.abs(pauliExpect(st, S0) - before) > 1e-9) bad++;
  }
  assert(bad === 0, "40 回の思考列と観測 (" + measured + " 回) を通して ⟨S0⟩ は一度も動かなかった");
}

/* ════ 6. 円環の帰還 ════ */
console.log("\n── 6. 【不変量】円環 C†C = I — 遊びは外へ漏れない ──");
{
  const n = 4, rnd = asobiRng(31);
  const V1 = [{q:0,p:"X"}], V2 = [{q:1,p:"Y"},{q:2,p:"X"}];
  let st = qsNew(n, 5), snap = qsClone(st);
  const ops = [];
  for (let i = 0; i < 6; i++){
    const V = i % 2 ? V1 : V2, th = 0.2 + rnd() * (THETA_MAX - 0.2);
    st = rotApply(st, V, th); ops.push({ V, th });
  }
  assert(qsDiff(st, snap) > 0.1, "円環の内側では状態は確かに動いている");
  for (let i = ops.length - 1; i >= 0; i--) st = rotApply(st, ops[i].V, -ops[i].th);
  assert(qsDiff(st, snap) < 1e-12, "帰還 C† で残差 " + qsDiff(st, snap).toExponential(1) + " — 完全に巻き戻る");
  const out = asobiInterpret([
    "qubit g0 g1 g2 g3", "rule R1 = Z g0 Z g1", "sacred S0 = Z g2 Z g3",
    "circle open budget 3.0", "think R1 angle 0.8", "think R1 angle 1.1", "circle close", "conform"
  ].join("\n"), { seed: 5 });
  assert(/残差/.test(out) && /e[-+]?\d+/.test(out), "インタプリタの circle close が帰還残差を報告する");
  assert(/R1[^\n]*⟨S⟩ = 1\.0000/.test(out), "帰還後の遵守は元通り ⟨R1⟩ = +1 (考えた痕跡は状態に残らない)");
}

/* ════ 7. 考えは行為にならない ════ */
console.log("\n── 7. 【不変量】θ ≤ θmax — 考えは考えに留まる ──");
{
  const out = asobiInterpret([
    "qubit g0 g1 g2 g3", "rule R1 = Z g0 Z g1", "sacred S0 = Z g2 Z g3",
    "circle open budget 9.0", "think R1 angle 3.14159", "conform", "circle close"
  ].join("\n"), { seed: 5 });
  assert(/行為の域/.test(out) && /拒否/.test(out), "θ = π の違反思考は処理系が拒否する");
  assert(/R1[^\n]*⟨S⟩ = 1\.0000/.test(out), "拒否された以上、状態は動いていない");
  const outSac = asobiInterpret([
    "qubit g0 g1 g2 g3", "sacred S0 = Z g2 Z g3",
    "circle open budget 1.0", "think S0 angle 0.5", "circle close"
  ].join("\n"), { seed: 5 });
  assert(/不可侵規則 S0 は遊びの対象外/.test(outSac), "不可侵規則に対する違反思考は最初から立てられない");
  const outNoCircle = asobiInterpret([
    "qubit g0 g1", "rule R1 = Z g0 Z g1", "think R1 angle 0.5"
  ].join("\n"), { seed: 5 });
  assert(/円環の中でしか/.test(outNoCircle), "円環の外では違反思考そのものが実行できない");
}

/* ════ 8-9. 遊び予算の保存 / 変異の単調性 ════ */
console.log("\n── 8-9. 遊び予算の保存と変異の単調性 ──");
{
  const w = ttmInit({ n:6, k:2, pop:16, seed:7, budget:1.2 });
  let overspend = 0, worse = 0, steps = 0;
  for (let g = 0; g < 40; g++){
    const budget = w.budget;
    const before = w.inds.map(i => w.land.vals[i.g]);
    const rec = ttmStep(w);
    steps++;
    if (rec.spent > budget + 1e-9) overspend++;
    const bestBefore = Math.max(...before);
    const bestAfter = Math.max(...w.inds.map(i => w.land.vals[i.g]));
    if (bestAfter < bestBefore - 1e-12) worse++;
  }
  assert(overspend === 0, "全 " + steps + " 世代で Σθ ≤ Δ (遊び予算の保存則)");
  assert(worse === 0, "最良個体の適応度は一度も下がらない (円環内の評価が観測を許した変異のみ確定するため)");
  assert(w.thought > 0 && w.returned > 0, "考えた回数 " + w.thought + " のうち " + w.returned + " は帰還・崩壊で消えた");
  const sac = w.rules.filter(r => r.sacred)[0];
  assert(w.inds.every(i => ruleConform(qsNew(w.n, i.g), sac) >= 0.5), "40 世代を経ても全個体が不可侵規則を満たす");
  assert(w.hist.every(h => h.H >= 0 && h.H <= 1), "多様性 H は [0,1]");
  assert(w.hist.some(h => Math.abs(h.budget - w.budget0) > 1e-6), "遊び予算は多様性に応じて恒常的に調節されている");
}

/* ════ 10. TTM vs 古典的無作為変異 ════
 * 二つの規則系で比べる。条件は完全に共通 (同じ初期集団・地形・選択・
 * エリート保存・評価回数・受理規則=メトロポリス)。違うのは「変異の作り方」だけ。
 *   拘束系 … 不可侵な対パリティが空間を強く絞る。無作為な反転はその大半が
 *            不可侵を壊して棄却されるが、違反生成子は構成上つねに不可侵と
 *            可換なので一手も無駄にならない  → TTM が有利なはずの領域
 *   鎖系   … 不可侵が 1 本しかなく空間がほぼ自由。TTM の手は限られた生成子に
 *            縛られる                        → 古典が有利なはずの領域
 * どちらの結果も正直に測る。 */
console.log("\n── 10. 違反思考変異 (TTM) vs 古典的無作為変異 ──");
function compare(rulesOf, landOf, n, K, pop, gens, seeds){
  let wins = 0, losses = 0, sumT = 0, sumC = 0, hitT = 0, hitC = 0, genT = 0, genC = 0;
  for (let seed = 1; seed <= seeds; seed++){
    const land = landOf(n, K, seed * 131 + 7);
    const sac = rulesOf(n).filter(r => r.sacred);
    let fmax = 0;
    for (let g = 0; g < (1 << n); g++){
      if (sac.every(r => ruleConform(qsNew(n, g), r) >= 0.5)) fmax = Math.max(fmax, land.vals[g]);
    }
    const common = { n, k:K, pop, gens, seed, land };
    const t = ttmRun(Object.assign({}, common, { budget:1.2, rules:rulesOf(n) }));
    const c = gaClassicRun(Object.assign({}, common, { rules:rulesOf(n) }));
    const tb = t.hist[gens-1].best, cb = c.hist[gens-1].best;
    sumT += tb; sumC += cb;
    if (tb > cb + 1e-12) wins++; else if (tb < cb - 1e-12) losses++;
    const ti = t.hist.findIndex(h => h.best >= fmax - 1e-12);
    const ci = c.hist.findIndex(h => h.best >= fmax - 1e-12);
    if (ti >= 0){ hitT++; genT += ti + 1; } else genT += gens;
    if (ci >= 0){ hitC++; genC += ci + 1; } else genC += gens;
  }
  return { wins, losses, seeds, meanT:sumT/seeds, meanC:sumC/seeds,
           hitT, hitC, genT:genT/seeds, genC:genC/seeds };
}
{
  const r = compare(constrainedRules, nkLandscape, 8, 3, 16, 60, 20);
  console.log("   拘束系: TTM " + r.wins + " 勝 " + r.losses + " 敗 / 平均 TTM " + r.meanT.toFixed(4) +
              " 古典 " + r.meanC.toFixed(4) + " / 最適到達 TTM " + r.hitT + " 古典 " + r.hitC +
              " / 平均到達世代 TTM " + r.genT.toFixed(1) + " 古典 " + r.genC.toFixed(1));
  assert(r.meanT > r.meanC, "拘束系では TTM の最終適応度が平均で上回る (+" + (r.meanT - r.meanC).toFixed(4) + ")");
  assert(r.wins > r.losses, "拘束系では TTM が勝ち越す (" + r.wins + " 勝 " + r.losses + " 敗)");
  assert(r.hitT >= r.hitC, "拘束系では TTM のほうが多くの地形で実行可能集合の最大へ到達する");
  assert(r.genT * 2 < r.genC, "拘束系では TTM が半分以下の世代で最適へ到達する (" +
         r.genT.toFixed(1) + " 対 " + r.genC.toFixed(1) + " 世代) — 違反生成子は不可侵を壊さないので一手も棄却されない");
}
{
  const r = compare(constrainedRules, trapLandscape, 8, 4, 16, 60, 20);
  console.log("   拘束系×トラップ地形: TTM " + r.wins + " 勝 " + r.losses + " 敗 / 平均 TTM " + r.meanT.toFixed(4) +
              " 古典 " + r.meanC.toFixed(4) + " / 平均到達世代 TTM " + r.genT.toFixed(1) + " 古典 " + r.genC.toFixed(1));
  assert(r.meanT >= r.meanC, "欺瞞的なトラップ地形でも TTM は下回らない");
  assert(r.genT < r.genC, "トラップ地形でも TTM のほうが早く最適へ届く");
}
{
  /* 正直な負けの記録 — 不可侵が弱く空間が自由な鎖系では、限られた生成子は不利になる */
  const r = compare(defaultRules, nkLandscape, 8, 3, 16, 60, 20);
  console.log("   鎖系 (不可侵 1 本): TTM " + r.wins + " 勝 " + r.losses + " 敗 / 平均 TTM " + r.meanT.toFixed(4) +
              " 古典 " + r.meanC.toFixed(4) + " / 最適到達 TTM " + r.hitT + " 古典 " + r.hitC);
  assert(r.meanT > r.meanC * 0.9, "鎖系では TTM は古典に及ばないが大崩れはしない (比 " +
         (r.meanT / r.meanC).toFixed(3) + ") — 遊びの有利は拘束の強さに依る");
}

/* ════ 11. 遊びゼロは焼き付く ════ */
console.log("\n── 11. 遊びゼロの機械は動かない ──");
{
  const n = 8, land = nkLandscape(n, 3, 7 * 131 + 7);
  const common = { n, k:3, pop:16, gens:60, seed:7, land };
  const live = ttmRun(Object.assign({}, common, { budget:1.2, rules:constrainedRules(n) }));
  const dead = ttmRun(Object.assign({}, common, { budget:0.0001, rules:constrainedRules(n) }));
  const l = live.hist[live.hist.length-1], d = dead.hist[dead.hist.length-1];
  assert(d.best <= l.best, "遊び予算をほぼ零にすると探索が進まない (焼き付き: " + d.best.toFixed(4) + " ≤ " + l.best.toFixed(4) + ")");
  assert(dead.acted === 0 || dead.acted < live.acted, "遊びが無ければ変異が確定しない (" + dead.acted + " < " + live.acted + ")");
}

/* ════ 12. 規範の弛緩・制度化と台帳 ════ */
console.log("\n── 12. 規範の書き換えと遊び台帳 ──");
{
  let found = null;
  for (let seed = 1; seed <= 12 && !found; seed++){
    const w = ttmRun({ n:8, k:3, pop:20, gens:80, seed, budget:2.2, rules:constrainedRules(8) });
    if (w.rewrites > 0 || w.rules.some(r => !r.sacred && r.w < 1.0)) found = w;
  }
  assert(found !== null, "破られ続けた規則は荷重が弛緩し、やがて制度化される");
  assert(found.ledger.length > 0, "遊び台帳に記録が残る (" + found.ledger.length + " 件)");
  const kinds = new Set(found.ledger.map(e => e.kind));
  assert(kinds.has("帰還") || kinds.has("崩壊"), "「考えたが何も起きなかった」も記録されている");
  assert(found.ledger.every(e => e.theta <= THETA_MAX + 1e-12), "台帳のすべての記録で θ ≤ θmax");
  assert(found.rules.filter(r => r.sacred).every(r => r.w === 1.0 && r.sign === 1), "不可侵規則は弛緩も制度化もされない");
}

/* ════ 13. インタプリタ ════ */
console.log("\n── 13. Bada 遊 インタプリタ ──");
{
  const bell = asobiInterpret("qubit q0 q1\nH q0\nCNOT q0 q1\nstate", { seed: 3 });
  assert(/\|00⟩ 0\.707/.test(bell) && /\|11⟩ 0\.707/.test(bell), "量子 Bada 互換: H + CNOT でベル状態");
  assert(/print → 6/.test(asobiInterpret("let x = 1 + 2\nlet y = x * 2\nprint y")), "let / print が動く");
  assert(/!!/.test(asobiInterpret("H q9")), "誤りは !! で報告される");
  const jp = asobiInterpret([
    "遺伝子 g0 g1 g2 g3", "規則 R1 = Z g0 Z g1 荷重 1.0", "不可侵 S0 = Z g2 Z g3",
    "円環 開く 予算 1.5", "違反思考 R1 角 0.7", "遊び", "円環 閉じる", "遵守"
  ].join("\n"), { seed: 11 });
  assert(!/!!/.test(jp), "日本語表記のプログラムが誤りなく走る");
  assert(/違反思考 R1/.test(jp) && /遊び予算/.test(jp), "日本語別名が正規形に写される");
  const ev = asobiInterpret([
    "qubit g0 g1 g2 g3 g4 g5",
    "rule R1 = Z g0 Z g1 weight 1.0", "rule R2 = Z g1 Z g2 weight 1.0", "rule R3 = Z g2 Z g3 weight 1.0",
    "sacred S0 = Z g4 Z g5",
    "population 16 genes 6 k 2 seed 7 budget 1.2", "evolve 40", "norms", "ledger"
  ].join("\n"), { seed: 13 });
  assert(!/!!/.test(ev), "変異アルゴリズムのプログラムが誤りなく走る");
  assert(/違反思考変異を 40 世代/.test(ev), "evolve が世代を回す");
  assert(/不可侵 S0 : 全個体で 保存 ✓/.test(ev), "evolve の出力が不可侵規則の保存を報告する");
  const open = asobiInterpret("qubit g0 g1\nrule R1 = Z g0 Z g1\ncircle open", { seed: 3 });
  assert(/円環が開いたまま/.test(open), "閉じ忘れた円環は警告される (遊びは閉じて初めて遊びになる)");
}

/* ════ 14. 生成AIカーネル ════ */
console.log("\n── 14. 生成AIカーネル ──");
{
  const r = aiCompose("不可侵な規則を守ったまま、いちばん強く縛っている規則を破る考えを個体に持たせて変異させたい");
  assert(r.intent === "evolve", "意図解析: 変異アルゴリズムの依頼と判定");
  assert(r.stages.length === 5, "5 段のパイプラインを開示する");
  assert(/population/.test(r.code) && /evolve/.test(r.code) && /sacred/.test(r.code), "生成コードに個体群・変異・不可侵が含まれる");
  assert(r.ok, "生成したコードを自分で実行して検証している");
  const b = aiCompose("違反の考えが行為にならないことを確かめたい");
  assert(b.intent === "boundary" && /行為の域/.test(b.run), "境界の依頼では θ 超過の拒否まで実演される");
  const s = aiCompose("不可侵な規則が保存されることを見たい");
  assert(s.intent === "sacred" && /sacred/.test(s.code), "不可侵の依頼では sacred を置いたコードを書く");
  const rt = aiCompose("遊びが円環の外に漏れないことを証明して");
  assert(rt.intent === "return" && /circle close/.test(rt.code) && /残差/.test(rt.run), "帰還の依頼では残差まで示す");
}

console.log("");
if (failures){ console.error("FAILURES: " + failures); process.exit(1); }
console.log("すべて通過 — Bada 遊 エンジンの不変量は保たれている");
