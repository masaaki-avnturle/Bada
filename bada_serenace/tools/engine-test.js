/*
 * engine-test.js — Bada Serenace のエンジン単体テスト (Node で実行)
 *
 *   node bada_serenace/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1.  Γ 大域的部分積分多様体 (gammaManifold / gammaMeasure / gammaKernel)
 *   2.  熱感知 (thermalSolve / thermalSense)
 *   3.  Jones 多項式 (kauffmanBracket / jonesPolynomial) — 三葉・8の字・Hopf の文献値
 *   4.  積み木の真逆 (blockAssemble / blockDemolish / blockInverse)
 *   5.  DNA と暗号 (dnaToBraid / dnaInvariant / cipherEncode / cipherDecode / cipherCrack)
 *   6.  病識 (insightModel) — 病識欠如の定理
 *   7.  思考漏洩 (leakChannel / leakFromThermal / leakSurvey)
 *   8.  RNA 干渉 (revComp / rnaiDesign / rnaiKnockdown)
 *   9.  セレネース (d2Occupancy / serenaceWindow / serenaceCompare)
 *   10. 予防機構パイプライン (preventionPipeline)
 *   11. 機能カタログ (funcCatalog) — 不変量が全機能で相異なること
 *   12. 意図解析とシェル (intentDetect / aiShell)
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
  return new Proxy({ style: {}, classList: { add(){}, remove(){} }, value: "", textContent: "", innerHTML: "" }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus" || p === "scrollIntoView") return function(){};
      if (p === "getContext") return function(){ return stubEl(); };
      if (p === "getAttribute") return function(){ return "0"; };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console: console, Math: Math, JSON: JSON, Set: Set, Map: Map, Proxy: Proxy,
  Int32Array: Int32Array, Float64Array: Float64Array, Error: Error,
  String: String, Number: Number, Array: Array, Object: Object,
  isFinite: isFinite, parseInt: parseInt, parseFloat: parseFloat,
  setTimeout: function(fn){ fn(); }, setInterval: function(){ return 0; }, clearInterval: function(){},
  alert: function(){},
  localStorage: { _d: {}, getItem(k){ return k in this._d ? this._d[k] : null; }, setItem(k, v){ this._d[k] = String(v); } },
  window: {},
  document: {
    getElementById(){ return stubEl(); },
    createElement(){ return stubEl(); },
    querySelectorAll(){ return []; },
    addEventListener(){}, removeEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

function get(name){ return vm.runInContext(name, sandbox); }
function assert(cond, msg){ if (!cond){ console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }
function near(a, b, eps){ return Math.abs(a - b) <= (eps === undefined ? 1e-9 : eps); }

/* ── 1. Γ 大域的部分積分多様体 ── */
const gammaManifold = get("gammaManifold"), gammaMeasure = get("gammaMeasure"), gammaKernel = get("gammaKernel");
assert(near(gammaManifold(1), 2), "∫Γ(γ)′dx_m = 2e^{−x log x} は x = 1 で 2");
assert(near(gammaManifold(Math.E), 2 * Math.exp(-Math.E)), "x = e では 2e^{−e}");
assert(gammaManifold(1 / Math.E) > gammaManifold(1) && gammaManifold(1 / Math.E) > gammaManifold(2),
  "多様体の最大は x = 1/e (x log x の最小点)");
assert(gammaManifold(0) === null && gammaManifold(-1) === null, "x ≤ 0 は定義域外");
assert(near(gammaMeasure(Math.E), 1), "大域的微分変数の密度 dx_m = dx/log x は x = e で 1");
assert(gammaMeasure(1) === null, "x = 1 は log x = 0 の特異点として除かれる");
assert(near(gammaKernel(1, 1.2), 1) && gammaKernel(2, 1.2) < 1 && gammaKernel(3, 1.2) < gammaKernel(2, 1.2),
  "Γ 熱核 k(r) は r > 1 で単調に減る");
assert(gammaKernel(5, 1.2) >= 0.02 && gammaKernel(0.3, 1.2) <= 1, "熱核は [0.02, 1] に収まる");

/* ── 2. 熱感知 ── */
const thermalSolve = get("thermalSolve"), thermalSense = get("thermalSense");
const field = thermalSolve({ sources: [{ x: 14, y: 14, q: 1 }] });
const sense = thermalSense(field);
assert(field.T.every(v => isFinite(v)), "温度場は全点有限 (陽解法が発散しない)");
assert(sense.maxT > 0 && sense.hotspots.length >= 1, "熱源を感知できる");
assert(sense.hotspots[0].x === 14 && sense.hotspots[0].y === 14, "最高温点は熱源の位置");
assert(field.T[14 * field.w + 14] > field.T[3 * field.w + 3], "熱源は周辺より高温");
const cold = thermalSense(thermalSolve({ sources: [] }));
assert(cold.maxT === 0 && cold.hotspots.length === 0, "熱源が無ければ感知も無い");
const two = thermalSense(thermalSolve({ sources: [{ x: 9, y: 9, q: 1 }, { x: 19, y: 19, q: 1 }] }));
assert(two.hotspots.length >= 2, "熱源 2 点は 2 点として分離される");
assert(sense.edgeFlux > 0, "境界へ漏れる熱流束が正 (漏洩チャネルの物理量)");

/* ── 3. Jones 多項式 ── */
const jonesPolynomial = get("jonesPolynomial"), kauffmanBracket = get("kauffmanBracket"),
      jonesKey = get("jonesKey"), braidWrithe = get("braidWrithe");
assert(jonesPolynomial([], 1).V === "1", "自明結び目の Jones 多項式は 1");
assert(jonesPolynomial([1], 2).V === "1", "σ₁ の閉包 (自明結び目) も 1 — Reidemeister I 不変");
assert(jonesPolynomial([1, 1, 1], 2).V === "t + t^3 − t^4", "三葉結び目 V(t) = t + t³ − t⁴");
assert(jonesPolynomial([-1, -1, -1], 2).V === "−t^-4 + t^-3 + t^-1", "鏡像三葉は V(1/t) = −t⁻⁴ + t⁻³ + t⁻¹");
assert(jonesPolynomial([1, -2, 1, -2], 3).V === "t^-2 − t^-1 + 1 − t + t^2",
  "8の字結び目 V(t) = t⁻² − t⁻¹ + 1 − t + t² (自己鏡像)");
assert(jonesPolynomial([1, 1], 2).V === "−t^1/2 − t^5/2", "Hopf 絡み目は t の半整数冪を持つ");
assert(kauffmanBracket([1, 1, 1], 2).size === 3 && jonesPolynomial([1, 1, 1], 2).bracket === "−A^5 − A^-3 + A^-7",
  "三葉の Kauffman ブラケット ⟨K⟩ = −A⁵ − A⁻³ + A⁻⁷");
assert(braidWrithe([1, 1, -2]) === 1, "ライズは符号和");
assert(jonesKey([1, 1, 1], 2) !== jonesKey([-1, -1, -1], 2), "三葉と鏡像三葉は不変量で区別される (キラリティ)");
let threw = false;
try { jonesPolynomial(new Array(17).fill(1), 2); } catch (e){ threw = true; }
assert(threw, "交点数の上限 (16) を超える語は拒否される");

/* ── 4. 積み木の真逆 ── */
const blockAssemble = get("blockAssemble"), blockDemolish = get("blockDemolish"), blockInverse = get("blockInverse");
const built = blockAssemble([1, 1, 1], 2);
assert(built.key === "t + t^3 − t^4", "組立 Φ は語を不変量へ写す");
assert(blockDemolish([1, 1, 2]).join(",") === "-2,-1,-1", "崩す操作は語の反転 w⁻¹ (真逆ではない)");
const fiber = blockInverse(built.key, { strands: 3, maxLen: 4 });
assert(fiber.size > 1 && !fiber.injective, "真逆 Φ⁻¹ は一点にならない — 同じ形を作る語が複数ある");
assert(fiber.fiber.every(w => jonesKey(w, 3) === built.key), "逆像の全ての語が同じ不変量へ戻る");
assert(fiber.canonical.length <= fiber.fiber[fiber.fiber.length - 1].length, "代表語は最短のもの");
const trivial = blockInverse("1", { strands: 2, maxLen: 2 });
assert(trivial.size >= 2 && trivial.fiber.every(w => jonesKey(w, 2) === "1"),
  "自明結び目の形の逆像は σ₁ や σ₁⁻¹ など (2 本鎖では空語は 2 成分の自明絡み目なので入らない)");
assert(trivial.canonical.length === 1, "自明結び目を作る最短の語はブロック 1 個");
assert(blockInverse("t^99", { strands: 3, maxLen: 2 }).size === 0, "存在しない形の逆像は空");

/* ── 5. DNA と暗号 ── */
const dnaToBraid = get("dnaToBraid"), dnaInvariant = get("dnaInvariant"), dnaClean = get("dnaClean"),
      cipherEncode = get("cipherEncode"), cipherDecode = get("cipherDecode"), cipherCrack = get("cipherCrack");
assert(dnaClean("atg-gc n") === "ATGGC", "配列は ACGTU だけに正規化される");
assert(dnaToBraid("ATGC").join(",") === "1,-1,2,-2", "塩基は組み紐生成子へ (A→σ₁, T→σ₁⁻¹, G→σ₂, C→σ₂⁻¹)");
assert(dnaToBraid("AUGC").join(",") === dnaToBraid("ATGC").join(","), "RNA の U は T と同じ生成子");
const seq = "ATGGCATTAC", key = "777";
const inv = dnaInvariant(seq, 8);
assert(inv.key === dnaInvariant(seq, 8).key && inv.key.length > 0, "配列の指紋は決定的");
const enc = cipherEncode(seq, key);
assert(enc !== seq && cipherDecode(enc, key) === seq, "鍵つき置換は往復して戻る (XOR は対合)");
assert(cipherDecode(enc, "778") !== seq, "鍵が違えば戻らない");
assert(dnaInvariant(enc, 8).key !== inv.key, "暗号文は指紋も変わる — 外に残る形だけが手掛かり");
const crack = cipherCrack(enc, inv.key, { motif: "ATG", maxKey: 1024 });
assert(crack.found && crack.candidates.some(c => c.key === key && c.plain === seq),
  "指紋を手掛かりにした逆像探索で正解の鍵と配列に到達する");
assert(!crack.unique, "指紋だけでは一意に定まらない — 暗号化されたい、の正体");
assert(crack.candidates.every(c => c.plain.indexOf("ATG") >= 0), "モチーフの手掛かりが候補を絞る");

/* ── 6. 病識 ── */
const insightModel = get("insightModel");
const intact = insightModel({ damage: 0, severity: 0.8 });
const lost = insightModel({ damage: 1, severity: 0.8 });
assert(intact.insight > lost.insight, "監視チャネルの損傷が増えると病識は落ちる");
assert(lost.insight < 0.25 && lost.anosognosia, "損傷が極まると病識欠如と判定される");
assert(!intact.anosognosia, "損傷が無ければ病識は保たれる");
assert(intact.severity === lost.severity, "重症度は病識と独立 — 落ちたのは気づきだけ");
let prev = Infinity, mono = true;
for (let d = 0; d <= 1.0001; d += 0.1){ const v = insightModel({ damage: d }).insight; if (v > prev + 1e-12) mono = false; prev = v; }
assert(mono, "病識は損傷 d について単調減少");
assert(insightModel({ illness: 2 }).illnessDim === "感情", "病いの載る次元を選べる");
assert(near(insightModel({ damage: 0 }).fixedPoint.reduce((s, v) => s + v * v, 0), 1, 1e-6), "不動点は単位ベクトル");

/* ── 7. 思考漏洩 ── */
const leakChannel = get("leakChannel"), leakFromThermal = get("leakFromThermal"), leakSurvey = get("leakSurvey");
assert(near(leakChannel(0, 8).mutualInformation, 0), "漏洩 0 では相互情報量 0 bit — 何も読めない");
assert(near(leakChannel(1, 8).mutualInformation, 1), "漏洩 1 では 1 bit — 内心がそのまま出る");
assert(near(leakChannel(0, 9).readProb, 0.5), "漏洩 0 の読み取り確率は当て推量の 50%");
assert(near(leakChannel(1, 8).readProb, 1), "漏洩 1 なら必ず当てられる");
assert(leakChannel(0.6, 20).readProb > leakChannel(0.6, 4).readProb, "観測回数が増えるほど読み取り確率は上がる");
assert(leakChannel(0.6, 12).read && !leakChannel(0.1, 12).read, "閾値 90% で「読まれ得る」を判定");
assert(near(leakFromThermal(0.6, 1.2), 0.5) && leakFromThermal(99, 1.2) === 1, "境界熱流束から漏洩量への換算 (上限 1)");
const survey = leakSurvey(12);
assert(survey.majority && survey.share > 0.5, "疾患の過半で読み取り確率が閾値を超える — 殆どの病気がこの症状を起こす");
assert(!survey.rows.find(r => r.id === "healthy").read, "健常では読み取り確率が閾値に届かない");
assert(survey.rows.find(r => r.id === "schizophrenia").readProb > survey.rows.find(r => r.id === "diabetes").readProb,
  "漏洩量の順序が読み取り確率の順序として保たれる");

/* ── 8. RNA 干渉 ── */
const revComp = get("revComp"), rnaiDesign = get("rnaiDesign"), rnaiKnockdown = get("rnaiKnockdown"),
      gcContent = get("gcContent"), hasRun = get("hasRun"), seedOffTargets = get("seedOffTargets");
assert(revComp("ATGC") === "GCAT", "逆相補 (DNA)");
assert(revComp("ATGC", true) === "GCAU", "逆相補 (RNA) では T が U になる");
assert(near(gcContent("GGCC"), 1) && near(gcContent("ATAT"), 0), "GC 含量");
assert(hasRun("AAAAT", 4) && !hasRun("AAATA", 4), "同一塩基 4 連続の検出");
assert(seedOffTargets("AUGCAUUGCUAGGAUCCGUAA", ["TGCATTGC"]) >= 1, "シード (2–8 位) のオフターゲット一致を数える");
const design = rnaiDesign("ATGGCATTACGGATCCTAGCAATGCATTGCAAGGCTTAACGTTAGCCATGACTGCATTAGC", { decoys: ["GGCATTACGGATCCTAGCAA"] });
assert(design.accepted > 0 && design.best, "設計候補が得られる");
assert(design.candidates.every(c => c.guide === revComp(c.target, true) + "dTdT"), "ガイド鎖は標的窓の逆相補 + dTdT");
assert(design.candidates.every(c => c.gc >= 0.30 && c.gc <= 0.52), "GC 含量 30–52% の窓だけが採択される");
assert(design.candidates.every(c => !c.run), "同一塩基 4 連続を含む窓は落とされる");
assert(design.candidates.every(c => c.asym > 0), "ガイド 5′ 側が AU に富む (熱力学的非対称性) ものだけ採択");
for (let i = 1; i < design.candidates.length; i++) {
  assert(design.candidates[i - 1].score >= design.candidates[i].score, "候補 " + i + " は得点降順に並ぶ");
}
assert(rnaiDesign("GGGGGGGGGGGGGGGGGGGGGGGG", {}).accepted === 0, "GC に偏った配列からは候補が出ない");
assert(design.candidates.every(c => typeof c.fingerprint === "string" && c.fingerprint.length > 0),
  "各候補に Γ→Jones の指紋が付く (積み木の真逆へ渡せる = 構築可能)");
const planted = rnaiDesign("ATGGCATTACGGATCCTAGCAATGCATTGCAAGGCTTAACGTTAGCCATGACTGCATTAGC",
  { decoys: ["GGCATTACGGATCCTAGCAA", "GCATTGCGCATTGCGCATTGC"] });
assert(planted.all.some(c => c.offTargets > 0), "オフターゲット配列を足すとシード一致が検出される");
assert(rnaiKnockdown(0, 1, 1) === 0, "用量 0 ではノックダウン 0");
assert(near(rnaiKnockdown(1, 1, 1), 0.5), "用量 = IC50 でノックダウン 50%");
assert(rnaiKnockdown(8, 1, 1.4) > rnaiKnockdown(2, 1, 1.4), "ノックダウンは用量について単調増加");
assert(rnaiKnockdown(1e6, 1, 1) < 1, "ノックダウンは 1 に漸近するが到達しない");

/* ── 9. セレネース ── */
const d2Occupancy = get("d2Occupancy"), serenaceWindow = get("serenaceWindow"), serenaceCompare = get("serenaceCompare");
assert(d2Occupancy(0, 1) === 0, "濃度 0 では占有 0");
assert(near(d2Occupancy(1, 1), 0.5), "C = Kd で占有 50%");
assert(d2Occupancy(1e6, 1) < 1 && d2Occupancy(1e6, 1) > 0.999, "占有は 1 に漸近する");
assert(serenaceWindow(0.5).band === "閾下" && serenaceWindow(0.72).band === "応答域" && serenaceWindow(0.9).band === "過占有",
  "占有率の区分 (文献上の目安 65–80%)");
const cmp = serenaceCompare(0.7, 0.5);
assert(near(cmp.signal, 0.15), "残存シグナル = (1 − 占有)(1 − ノックダウン)");
assert(near(serenaceCompare(0.5, 0).signal, serenaceCompare(0, 0.5).signal),
  "下流の遮断 50% と上流の抑制 50% は同じ残存シグナルを与える");
assert(cmp.equivalentOccupancy > 0.7, "併用は単独占有より低い残存シグナルに到達する");
assert(serenaceCompare(2, -1).occupancy === 1 && serenaceCompare(2, -1).knockdown === 0, "入力は [0,1] に丸められる");

/* ── 10. 予防機構パイプライン ── */
const preventionPipeline = get("preventionPipeline");
const run = preventionPipeline({});
assert(run.stages.length === 7, "パイプラインは 7 段");
assert(run.stages.every(s => s.ok) && run.ok, "全段が成立する");
assert(run.stages.map(s => s.title).join("→") ===
  "Γ 熱感知→Jones 不変量→積み木の真逆→暗号解読→病識と漏洩→RNA 干渉の構築→セレネース比較",
  "段の順序: 熱感知 → 不変量 → 真逆 → 復号 → 病識/漏洩 → RNA 干渉 → セレネース");
assert(run.summary.hotspots > 0 && run.summary.fiber > 0 && run.summary.knockdown > 0,
  "各段が後段へ数値を引き渡している");
assert(run.summary.signal < 1 - run.summary.occupancy + 1e-12,
  "上流の RNA 干渉を足すと残存シグナルは受容体遮断だけの場合より下がる");
const run2 = preventionPipeline({ seq: "ATGAAGGGCCTTAACCGGTTAAGGCCTTAAC" });
assert(run2.stages.length === 7 && run2.summary.invariant !== run.summary.invariant,
  "配列を変えると不変量が変わる (指紋として働く)");
assert(preventionPipeline({ seq: "ATGCATGCATGCATGCATGCATGCATGCATG" }).summary.invariant === run.summary.invariant,
  "不変量は配列の並びの細部ではなく形を見る — 違う配列が同じ指紋を持ちうる (逆像が一点にならない理由)");

/* ── 11. 機能カタログ ── */
const funcCatalog = get("funcCatalog"), funcInvariant = get("funcInvariant");
const catalog = funcCatalog();
assert(catalog.length === 9, "機能は 9 つ");
assert(new Set(catalog.map(f => f.V)).size === catalog.length,
  "Jones 不変量は全機能で相異なる — 機能はトポロジー不変量で一意に分類される");
assert(funcInvariant("serenace").V === "−t^-4 + t^-3 + t^-1", "セレネースは鏡像三葉に割り当てられている");
assert(funcInvariant("nosuch") === null, "未知の機能は null");

/* ── 12. 意図解析とシェル ── */
const intentDetect = get("intentDetect"), aiShell = get("aiShell");
assert(intentDetect("熱を感知して").intent === "thermal", "意図: 熱 → 熱感知");
assert(intentDetect("積み木の真逆を見せて").intent === "blocks", "意図: 真逆 → 積み木の真逆");
assert(intentDetect("暗号を解いて").intent === "cipher", "意図: 暗号 → DNA 暗号");
assert(intentDetect("自分が病気だと思えない").intent === "insight", "意図: 自覚 → 病識");
assert(intentDetect("考えが読まれている").intent === "leak", "意図: 読まれる → 思考漏洩");
assert(intentDetect("RNA干渉を設計して").intent === "rnai", "意図: RNA 干渉 → 設計");
assert(intentDetect("セレネースの仕組みは").intent === "serenace", "意図: セレネース → 受容体占有");
assert(intentDetect("予防機構を解明して").intent === "prevent", "意図: 予防 → パイプライン");
assert(intentDetect("ATGGCATTACGGATCC").intent === "sequence", "意図: 生の配列 → 配列として受理");
assert(intentDetect("1,-2,1,-2").intent === "braid", "意図: 生の組み紐語 → 語として受理");
assert(intentDetect("").intent === "none" && intentDetect("それはそれとして").intent === "unknown",
  "空入力と該当なしを区別する");
const shell = aiShell("1,1,1");
assert(shell.steps.length === 6, "シェルは 6 段を開示する");
assert(/V\(t\) = t \+ t\^3 − t\^4/.test(shell.text), "組み紐語を渡すと Jones 多項式を返す");
const shell2 = aiShell("ATGGCATTACGGATCCTAGCAATGCATTGCAAGGCTTAACGT");
assert(shell2.open === "rnai" && /ガイド/.test(shell2.text), "配列を渡すと RNA 干渉設計へ回る");
assert(/⑥ 検証/.test(shell2.steps[5]) && /一致/.test(shell2.steps[5]), "最終段でガイド鎖の逆相補性を検証する");
const shell3 = aiShell("予防機構を解明して");
assert(/成立/.test(shell3.steps[5]), "パイプラインを回して検証結果を返す");

console.log("\nBada Serenace engine tests: すべて成功");
