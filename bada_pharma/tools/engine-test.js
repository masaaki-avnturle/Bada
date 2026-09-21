/*
 * engine-test.js — Bada Pharma (薬剤製造装置) のエンジン単体テスト
 *
 *   node bada_pharma/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1.  Γ 大域的部分積分多様体 (gammaManifold / gammaKernel)
 *   2.  計測取込 (modalityNormalize / modalityIntake / profileSimilarity)
 *   3.  標的同定 (targetIdentify)
 *   4.  分子設計 (molWeight / molBuild / lipinski / veber / desirability)
 *   5.  逆合成 (retroRoute) — 収率と原子効率の計画のみ
 *   6.  製剤化 (formulate / dissolution / noyesWhitney / dissolutionQ)
 *   7.  薬物動態 (pkConc / pkMetrics / pkMultiDose / accumulationRatio)
 *   8.  品質管理 (contentUniformity / processCapability / calibration)
 *   9.  製造記録 (lotNumber / batchRecord)
 *   10. 製造ライン (manufacturePipeline) — 8 段
 *   11. 装置カタログと意図解析 (unitCatalog / intentDetect / aiShell)
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
  console: console, Math: Math, JSON: JSON, Set: Set, Map: Map, Proxy: Proxy, Error: Error,
  String: String, Number: Number, Array: Array, Object: Object, Infinity: Infinity,
  isFinite: isFinite, parseInt: parseInt, parseFloat: parseFloat,
  setTimeout: function(fn){ fn(); }, setInterval: function(){ return 0; }, clearInterval: function(){},
  localStorage: { _d: {}, getItem(k){ return k in this._d ? this._d[k] : null; }, setItem(k, v){ this._d[k] = String(v); } },
  window: {},
  document: {
    getElementById(){ return stubEl(); }, createElement(){ return stubEl(); },
    querySelectorAll(){ return []; }, addEventListener(){}, removeEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

function get(name){ return vm.runInContext(name, sandbox); }
function assert(cond, msg){ if (!cond){ console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }
function near(a, b, eps){ return Math.abs(a - b) <= (eps === undefined ? 1e-9 : eps); }
function throws(fn){ try { fn(); return false; } catch (e){ return true; } }

/* ── 1. Γ 多様体 ── */
const gammaManifold = get("gammaManifold"), gammaKernel = get("gammaKernel");
assert(near(gammaManifold(1), 2), "∫Γ(γ)′dx_m は x = 1 で 2 (計測器アプリ群と同じ核)");
assert(gammaManifold(-1) === null, "x ≤ 0 は定義域外");
assert(near(gammaKernel(1, 1.2), 1) && gammaKernel(2, 1.2) < gammaKernel(1.5, 1.2),
  "Γ 熱核は r > 1 で単調に減る (遠いモダリティほど緩く効く)");

/* ── 2. 計測取込 ── */
const modalityNormalize = get("modalityNormalize"), modalityIntake = get("modalityIntake"),
      profileSimilarity = get("profileSimilarity"), MODALITIES = get("MODALITIES"),
      DEFAULT_READINGS = get("DEFAULT_READINGS");
assert(MODALITIES.length === 7, "モダリティは 7 種 (MRI / fMRI / DNA / 血液 / 脳電磁場 / 脳トポグラフィー / Γ 熱感知)");
assert(near(modalityNormalize("blood", 0).norm, 0) && near(modalityNormalize("blood", 10).norm, 1),
  "参照範囲の下端が 0、上端が 1 に正規化される");
assert(modalityNormalize("blood", 12).saturated, "参照範囲外は飽和として旗が立つ");
assert(modalityNormalize("nosuch", 1) === null, "未知のモダリティは null");
const intake = modalityIntake(DEFAULT_READINGS);
assert(intake.rows.length === 7 && intake.coverage === 1, "全モダリティを取り込むと網羅率 1");
assert(intake.burden >= 0 && intake.burden <= 1, "Γ 重み付き総合負荷は 0–1");
assert(intake.usable, "網羅率が半分以上なら標的同定へ進める");
const partial = modalityIntake({ mri: 0.5, fmri: 1.0 });
assert(!partial.usable && partial.missing.length === 5, "モダリティが足りなければ進めず、欠測が列挙される");
assert(modalityIntake({}).rows.length === 0, "空入力でも落ちない");
assert(near(profileSimilarity([1, 2, 3], [1, 2, 3]), 1, 1e-6), "同じ形の相関は 1");
assert(near(profileSimilarity([1, 2, 3], [3, 2, 1]), -1, 1e-6), "逆の形の相関は −1");
assert(profileSimilarity([0.9, 0.9, 0.1], [0.8, 0.8, 0.2]) > profileSimilarity([0.9, 0.9, 0.1], [0.2, 0.8, 0.8]),
  "平均を抜いた相関は形の違いを見分ける (生のコサインでは潰れる)");

/* ── 3. 標的同定 ── */
const targetIdentify = get("targetIdentify"), TARGETS = get("TARGETS");
assert(TARGETS.length === 6, "標的カタログは 6 種");
const infl = targetIdentify(modalityIntake({ mri: 0.5, fmri: 0.3, dna: 0.2, blood: 8.0, meg: 0.6, topo: 0.5, therm: 1.0 }));
assert(infl.best.id === "cox" && infl.confident, "炎症寄りの計測 (CRP 高値 + 熱) は COX-2 を一意に指す");
const lipid = targetIdentify(modalityIntake({ mri: 0.5, fmri: 0.2, dna: 0.6, blood: 6.0, meg: 0.4, topo: 0.3, therm: 0.5 }));
assert(lipid.best.id === "hmgcr", "血液寄りで熱の低い計測は HMG-CoA 還元酵素を指す");
const psych = targetIdentify(modalityIntake({ mri: 0.6, fmri: 2.2, dna: 0.8, blood: 0.5, meg: 2.4, topo: 3.0, therm: 0.3 }));
assert(["d2", "drd2m"].indexOf(psych.best.id) >= 0, "脳機能寄りの計測は D2 系 (受容体または転写産物) を指す");
assert(!psych.confident && /拮抗/.test(psych.note), "上流と下流が拮抗するときは並行設計を促す");
assert(infl.ranking.length === TARGETS.length, "全標的が相関の順に並ぶ");
for (let i = 1; i < infl.ranking.length; i++) assert(infl.ranking[i - 1].score >= infl.ranking[i].score, "順位 " + i + " は相関降順");

/* ── 4. 分子設計 ── */
const molWeight = get("molWeight"), molBuild = get("molBuild"), formulaString = get("formulaString"),
      lipinski = get("lipinski"), veber = get("veber"), desirability = get("desirability"),
      drugRef = get("drugRef"), FRAGMENTS = get("FRAGMENTS");
assert(near(molWeight({ H: 2, O: 1 }), 18.015, 1e-3), "水の分子量 18.015");
assert(formulaString({ C: 9, H: 8, O: 4 }) === "C9H8O4", "分子式は C, H, その他の順で書く");
assert(throws(() => molWeight({ Xx: 1 })), "未知の元素は拒否される");
const aspirin = molBuild(["phenyl", "carboxyl", "acetyloxy"]);
assert(aspirin.formulaText === "C9H8O4" && near(aspirin.mw, 180.16, 0.01),
  "フェニル + カルボキシル + アセチルオキシ = C9H8O4、分子量 180.16 (アスピリンの実測値)");
const para = molBuild(["phenyl", "hydroxyl", "acetamido"]);
assert(para.formulaText === "C8H9NO2" && near(para.mw, 151.16, 0.01),
  "フェニル + ヒドロキシル + アセトアミド = C8H9NO2、分子量 151.16 (パラセタモールの実測値)");
assert(formulaString({ C: 21, H: 23, Cl: 1, F: 1, N: 1, O: 2 }) === "C21H23ClFNO2",
  "Hill 表記は C, H のあと元素記号のアルファベット順");
assert(near(molWeight(drugRef("haloperidol").f), 375.86, 0.02),
  "ハロペリドール C21H23ClFNO2 の分子量 375.86 (セレネースの有効成分)");
const halo = molBuild(drugRef("haloperidol").blocks);
assert(halo.formulaText === "C21H23ClFNO2" && near(halo.mw, 375.86, 0.02),
  "積み木 10 個からセレネースの有効成分ハロペリドールが分子式まで正確に組み上がる");
assert(lipinski(halo).count === 1 && lipinski(halo).pass,
  "ハロペリドールは logP が高く違反 1 件 — Rule of Five は違反 1 件までを許容する");
assert(throws(() => molBuild(["nosuch"])), "未知のフラグメントは拒否される");
assert(aspirin.hbd === 1 && aspirin.hba === 4, "水素結合の供与/受容数が積み上がる");
assert(lipinski(aspirin).pass && lipinski(aspirin).count === 0, "アスピリンは Rule of Five に違反しない");
const huge = molBuild(new Array(14).fill("phenylEnd"));
assert(huge.mw > 500 && !lipinski(huge).pass, "分子量が 500 を超え logP も高い分子は Rule of Five に落ちる");
assert(veber(aspirin).pass, "アスピリンは Veber 則 (回転結合 ≤ 10 / TPSA ≤ 140) に適合");
assert(!veber(molBuild(new Array(12).fill("methylene"))).pass, "回転可能結合が多すぎる鎖は Veber 則に落ちる");
const des = desirability(aspirin);
assert(des.score > 0.7 && des.grade === "良", "アスピリンの望ましさは良");
assert(desirability(huge).score < desirability(aspirin).score, "巨大分子の望ましさは下がる");

/* ── 5. 逆合成 ── */
const retroRoute = get("retroRoute"), COUPLINGS = get("COUPLINGS");
const route = retroRoute(["phenyl", "carboxyl", "acetyloxy"]);
assert(route.stepCount === 2, "積み木 3 個なら切り口は 2 つ (工程数 = 積み木 − 1)");
assert(near(route.overallYield, route.steps.reduce((y, s) => y * s.yield, 1)), "通算収率は各工程収率の積");
assert(route.overallYield < 1 && route.overallYield > 0, "通算収率は 0 と 1 のあいだ");
assert(route.atomEconomy < 1, "脱離分子が出るので原子効率は 1 未満");
assert(near(route.atomEconomy, route.target.mw / (route.target.mw + route.lossMass)),
  "原子効率 = 目的物質量 / (目的物 + 脱離分子) 質量");
assert(route.steps[0].n === 1 && route.steps[route.steps.length - 1].n === route.stepCount, "工程は前向きに番号が振られる");
assert(near(route.requiredInput, 1 / route.overallYield), "目的 1 mol に必要な仕込みは収率の逆数");
assert(retroRoute(["phenyl", "carboxyl", "acetyloxy"], { scale: 2 }).requiredInput > route.requiredInput,
  "仕込み規模を上げれば必要量も増える");
assert(throws(() => retroRoute([])), "空の分子は拒否される");
assert(COUPLINGS.every(c => c.yield > 0 && c.yield < 1), "どの結合形成も収率は 1 未満");
assert(route.steps.every(s => !("reagent" in s) && !("solvent" in s) && !("temperature" in s) && !("catalyst" in s)),
  "工程は試薬・溶媒・温度・触媒の欄を持たない (収率と原子効率と接続する積み木だけ)");
assert(/試薬・反応条件・操作手順は扱いません/.test(route.note), "経路は試薬・条件・手順を扱わないことを明示する");

/* ── 6. 製剤化 ── */
const formulate = get("formulate"), dissolution = get("dissolution"), noyesWhitney = get("noyesWhitney"),
      dissolutionQ = get("dissolutionQ"), dissolutionProfile = get("dissolutionProfile");
const form = formulate(100, { tabletMg: 250 });
assert(near(form.total, 250) && form.balanced, "質量収支が閉じる (原薬 + 充填剤 + 崩壊剤 + 結合剤 + 滑沢剤 = 錠剤質量)");
assert(near(form.drugLoad, 0.4), "原薬含量 100 / 250 = 40%");
assert(form.composition.reduce((s, c) => s + c.mg, 0) === form.total, "組成表の合計は総質量に一致");
assert(throws(() => formulate(300, { tabletMg: 250 })), "原薬が錠剤質量を超える配合は拒否される");
assert(throws(() => formulate(240, { tabletMg: 250, disintegrant: 0.2 })), "賦形剤が入り切らない配合も拒否される");
assert(formulate(100, { tabletMg: 250, disintegrant: 0.10 }).tau < form.tau, "崩壊剤を増やすと溶出が速くなる (τ が短い)");
assert(near(dissolution(form.tau, form.tau, 1), 1 - 1 / Math.E, 1e-9), "Weibull の τ は 63.2% 溶出時間");
assert(dissolution(0, 10, 1) === 0 && dissolution(1e6, 10, 1) > 0.999, "溶出は 0 から始まり 1 に漸近する");
assert(dissolution(20, 10, 1) > dissolution(10, 10, 1), "溶出率は時間について単調増加");
assert(near(noyesWhitney(0, 0.1, 50, 0), 0) && near(noyesWhitney(1e6, 0.1, 50, 0), 50, 1e-6),
  "Noyes–Whitney は飽和溶解度 Cs に漸近する");
assert(dissolutionQ(form, 30, 0.8).pass === (dissolution(30, form.tau, form.beta) >= 0.8), "溶出規格 Q の判定");
assert(dissolutionProfile(form).length === 7, "既定の溶出プロファイルは 7 点");

/* ── 7. 薬物動態 ── */
const pkConc = get("pkConc"), pkMetrics = get("pkMetrics"), pkMultiDose = get("pkMultiDose"),
      accumulationRatio = get("accumulationRatio"), occupancy = get("occupancy"),
      therapeuticWindow = get("therapeuticWindow"), pkCurve = get("pkCurve");
const P = { dose: 100, F: 0.8, ka: 1.2, ke: 0.15, V: 30 };
const met = pkMetrics(P);
assert(near(met.tmax, Math.log(P.ka / P.ke) / (P.ka - P.ke)), "Tmax = ln(ka/ke)/(ka − ke)");
let tbest = 0, cbest = 0;
for (let t = 0; t < 24; t += 0.001){ const c = pkConc(t, P); if (c > cbest){ cbest = c; tbest = t; } }
assert(near(tbest, met.tmax, 2e-3) && near(cbest, met.cmax, 1e-6), "解析解の Tmax/Cmax が数値探索と一致する");
let auc = 0;
for (let t = 0; t < 400; t += 0.001) auc += pkConc(t, P) * 0.001;
assert(near(auc, met.auc, 1e-3), "AUC = F·D/(V·ke) が数値積分と一致する");
assert(near(met.halfLife, Math.LN2 / P.ke), "消失半減期 t½ = ln2/ke");
assert(near(met.clearance, P.V * P.ke), "クリアランス CL = V·ke");
assert(pkConc(0, P) === 0 && pkConc(-1, P) === 0, "投与前の濃度は 0");
const flip = { dose: 100, F: 1, ka: 0.3, ke: 0.3, V: 20 };
assert(isFinite(pkConc(2, flip)) && pkConc(2, flip) > 0, "ka = ke の極限でも発散しない");
assert(near(pkMultiDose(3, P, 12, 3), pkConc(3, P)), "1 回目の投与間隔内では反復投与も単回と同じ");
assert(pkMultiDose(14, P, 12, 3) > pkConc(14, P), "2 回目以降は前回の残りが重なる");
assert(near(accumulationRatio(0.15, 12), 1 / (1 - Math.exp(-0.15 * 12))), "蓄積率 R = 1/(1 − e^{−ke·τ})");
assert(accumulationRatio(0.05, 6) > accumulationRatio(0.5, 24), "半減期が長く間隔が短いほど蓄積する");
assert(pkCurve(P, 24, 10).length === 11, "曲線は n + 1 点");
assert(occupancy(0, 1) === 0 && near(occupancy(1, 1), 0.5), "占有 = C/(C + Kd)");
assert(therapeuticWindow(0.5).band === "閾下" && therapeuticWindow(0.72).band === "応答域" &&
       therapeuticWindow(0.9).band === "過占有", "占有率の区分 (Bada Serenace と同じ目盛り)");

/* ── 8. 品質管理 ── */
const contentUniformity = get("contentUniformity"), processCapability = get("processCapability"),
      calibration = get("calibration");
const vals = [99.2, 101.3, 98.7, 100.5, 99.8, 100.9, 98.2, 101.0, 99.5, 100.1];
const cu = contentUniformity(vals);
assert(cu.n === 10 && cu.k === 2.4, "n ≤ 10 では k = 2.4");
assert(near(cu.av, Math.abs(cu.M - cu.mean) + cu.k * cu.sd), "判定値 AV = |M − X̄| + k·s");
assert(cu.M === cu.mean, "平均が 98.5–101.5% の内なら基準値 M は平均そのもの");
assert(cu.pass, "ばらつきの小さいロットは含量均一性に適合する");
const low = contentUniformity([85, 86, 84, 87, 85, 86, 83, 88, 85, 86]);
assert(low.M === 98.5, "平均が 98.5% を下回れば基準値 M は 98.5 に固定される");
assert(!low.pass && low.av > low.L1, "表示量から大きく外れたロットは判定値が L1 を超えて不適合");
const spread = contentUniformity([100, 108, 92, 104, 96, 110, 90, 106, 94, 102]);
assert(spread.M === spread.mean && !spread.pass, "平均が中心でも、ばらつきが大きければ不適合");
assert(contentUniformity(vals, { k: 2.0 }).av < cu.av, "n が大きく k が小さいほど判定値は下がる");
assert(throws(() => contentUniformity([100, 100])), "3 点未満は拒否される");
const cap = processCapability([99, 100, 101, 100, 99.5, 100.5], 95, 105);
assert(near(cap.cp, (105 - 95) / (6 * cap.sd)), "Cp = (USL − LSL)/6σ");
assert(near(cap.cpk, Math.min(105 - cap.mean, cap.mean - 95) / (3 * cap.sd)), "Cpk = min(USL − μ, μ − LSL)/3σ");
assert(cap.capable, "Cpk ≥ 1.33 なら工程能力あり");
assert(!processCapability([97, 103, 95.5, 104.5, 100], 95, 105).capable, "ばらつきが規格幅に近いと工程能力不足");
const cal = calibration([1, 2, 3, 4, 5], [2, 4, 6, 8, 10]);
assert(near(cal.slope, 2) && near(cal.intercept, 0, 1e-9) && near(cal.r2, 1, 1e-9),
  "完全な直線 y = 2x では傾き 2、切片 0、R² = 1");
assert(calibration([1, 2, 3, 4, 5], [2.1, 4.0, 6.2, 7.9, 10.1]).linear, "実測風のデータでも R² ≥ 0.99 なら直線性あり");
assert(throws(() => calibration([1, 2], [1, 2])), "検量線も 3 点未満は拒否される");

/* ── 9. 製造記録 ── */
const lotNumber = get("lotNumber"), batchRecord = get("batchRecord");
assert(/^BP-[A-Z]{2}-\d{5}$/.test(lotNumber("x")), "ロット番号の書式 BP-XX-00000");
assert(lotNumber("x") === lotNumber("x") && lotNumber("x") !== lotNumber("y"), "ロット番号は決定的で、種が違えば変わる");
const rec = batchRecord({ tablets: 1000, formulation: form, overallYield: route.overallYield });
assert(near(rec.apiNeededMg, form.api * 1000), "製品中の原薬量 = 1 錠あたり × 錠数");
assert(near(rec.apiChargedMg, rec.apiNeededMg / route.overallYield), "仕込み量 = 必要量 / 通算収率");
assert(rec.processLossMg > 0 && near(rec.processLossMg, rec.apiChargedMg - rec.apiNeededMg), "工程損失 = 仕込み − 製品中");
assert(rec.massBalanceClosed, "記録は質量収支が閉じたことを保持する");
assert(/^[0-9a-f]{8}$/.test(rec.fingerprint), "記録指紋は 8 桁の 16 進");
assert(batchRecord({ tablets: 1001, formulation: form, overallYield: route.overallYield }).fingerprint !== rec.fingerprint,
  "錠数が 1 つ違えば記録指紋も変わる");

/* ── 10. 製造ライン ── */
const manufacturePipeline = get("manufacturePipeline");
const run = manufacturePipeline({});
assert(run.stages.length === 8, "製造ラインは 8 段");
assert(run.stages.every(s => s.ok) && run.ok, "既定の入力では全段が成立する");
assert(run.stages.map(s => s.title).join("→") ===
  "計測取込→標的同定→分子設計→逆合成→製剤化→薬物動態→品質管理→製造記録",
  "段の順序: 計測 → 標的 → 分子 → 経路 → 製剤 → 動態 → 品質 → 記録");
assert(run.summary.formula === "C9H8O4" && run.summary.lot.startsWith("BP-"), "要約に分子式とロット番号が載る");
assert(run.artifacts.record.apiChargedMg > run.artifacts.record.apiNeededMg,
  "逆合成の収率が製造記録の仕込み量へ伝わっている");
assert(near(run.artifacts.pk.auc, run.summary.auc), "薬物動態の結果が要約へ伝わっている");
const heavy = manufacturePipeline({ blocks: new Array(14).fill("phenylEnd") });
assert(!heavy.stages[2].ok && !heavy.ok, "Rule of Five に落ちる分子では分子設計の段が不成立になる");
const scaled = manufacturePipeline({ tablets: 5000 });
assert(near(scaled.artifacts.record.apiNeededMg, run.artifacts.record.apiNeededMg * 5),
  "錠数を 5 倍にすれば必要な原薬も 5 倍");
assert(manufacturePipeline({ readings: { mri: 0.5 } }).stages[0].ok === false,
  "モダリティが足りなければ 1 段目で止まる");

/* ── 11. 装置カタログと意図解析 ── */
const unitCatalog = get("unitCatalog"), unitInfo = get("unitInfo"),
      intentDetect = get("intentDetect"), aiShell = get("aiShell");
assert(unitCatalog().length === 9, "装置は 9 つ (8 段 + 製造ライン)");
assert(new Set(unitCatalog().map(u => u.id)).size === 9, "装置 id は重複しない");
assert(unitInfo("nosuch") === null, "未知の装置は null");
assert(intentDetect("MRI と血液検査を取り込んで").intent === "intake", "意図: 計測 → 計測取込");
assert(intentDetect("標的はどこ").intent === "target", "意図: 標的 → 標的同定");
assert(intentDetect("分子を設計して").intent === "design", "意図: 設計 → 分子設計");
assert(intentDetect("合成経路と収率").intent === "retro", "意図: 経路 → 逆合成");
assert(intentDetect("錠剤にして").intent === "formulate", "意図: 錠剤 → 製剤化");
assert(intentDetect("血中濃度を見せて").intent === "pk", "意図: 血中濃度 → 薬物動態");
assert(intentDetect("含量均一性を判定して").intent === "qc", "意図: 均一性 → 品質管理");
assert(intentDetect("ロットの記録").intent === "record", "意図: ロット → 製造記録");
assert(intentDetect("全部通して").intent === "line", "意図: 全部 → 製造ライン");
assert(intentDetect("アスピリン").intent === "drug", "意図: 参照医薬品の名前 → 分子照合");
assert(intentDetect("").intent === "none" && intentDetect("ところで").intent === "unknown",
  "空入力と該当なしを区別する");
const sh = aiShell("アスピリン");
assert(sh.steps.length === 6 && sh.open === "design", "シェルは 6 段を開示し、参照医薬品は分子設計へ回す");
assert(/一致/.test(sh.steps[5]), "参照分子量との照合が最終段で検証される");
const sh2 = aiShell("全部通して");
assert(sh2.open === "line" && /全段成立/.test(sh2.steps[5]), "製造ラインを通して検証結果を返す");
assert(/案内/.test(aiShell("ところで").steps[4]), "該当なしのときは案内を返す");

console.log("\nBada Pharma engine tests: すべて成功");
