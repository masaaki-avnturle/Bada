/*
 * engine-test.js — Mimir (ARグラス・コンシェルジュ) のエンジン単体テスト
 *
 *   node mimir/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブして
 * 純ロジック部分を検証します:
 *   1. 特殊相対論 — ローレンツ因子 γ / 相対論的ドップラー / 光行差
 *   2. 光路差反射システム — スネル屈折 / Δ=2nd·cosθt / 干渉位相・フリンジ強度
 *   3. 相対論込み光路差 (relativisticOPD) — v=0 で静止解に一致、v>0 で青方偏移
 *   4. 両眼収束シフト (SBS 投影)
 *   5. コンシェルジュ「ミーミル」 — レーベンシュタイン / 安全計算機 / 意図応答
 *   6. HUD 投影パイプライン (projectText → hudState)
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
  return new Proxy({ style: { setProperty(){} }, classList: { add(){}, remove(){}, toggle(){} },
                     value: "", textContent: "", innerHTML: "", checked: false,
                     children: [], width: 1280, height: 720 }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement" ||
          p === "getContext" || p === "removeChild" || p === "replaceChildren") {
        return function(){ return stubEl(); };
      }
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus" ||
          p === "getBoundingClientRect") {
        return function(){ return { left: 0, top: 0, width: 1280, height: 720 }; };
      }
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console, Math, Proxy, String, Number, Object, Array, JSON, Date,
  parseFloat, parseInt, isNaN, isFinite,
  setTimeout: function(fn){ fn(); }, setInterval: function(){ return 0; }, clearInterval: function(){},
  requestAnimationFrame: function(){},
  document: {
    getElementById(){ return stubEl(); }, createElement(){ return stubEl(); },
    querySelectorAll(){ return []; }, addEventListener(){}, removeEventListener(){},
    documentElement: stubEl()
  },
  navigator: {},
  window: {}
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });
const G = function(name){ return vm.runInContext(name, sandbox); };
function assert(cond, msg){ if (!cond){ console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }
function near(a, b, eps){ return Math.abs(a - b) <= (eps || 1e-9); }

/* 1. 特殊相対論 */
const gammaFactor = G("gammaFactor");
assert(gammaFactor(0) === 1, "γ(0) = 1 (静止でローレンツ因子は 1)");
assert(near(gammaFactor(0.6), 1.25, 1e-12), "γ(0.6c) = 1.25");
assert(gammaFactor(1) === Infinity, "γ(c) = ∞ (光速で発散)");

const relDoppler = G("relDoppler");
assert(near(relDoppler(0, 1), 1, 1e-12), "ドップラー: v=0 で D=1");
assert(near(relDoppler(0.6, 1), 2, 1e-12), "正面接近 0.6c で D=2 (青方偏移)");
assert(near(relDoppler(0.6, -1), 0.5, 1e-12), "正面後退 0.6c で D=0.5 (赤方偏移)");
assert(near(relDoppler(0.6, 0), 1 / 1.25, 1e-12), "横方向 (cosθ=0) は横ドップラー D=1/γ");

const aberrate = G("aberrate");
assert(near(aberrate(0.3, 0), 0.3, 1e-12), "光行差: β=0 で方向不変");
assert(near(aberrate(0, 0.6), 0.6, 1e-12), "光行差: 横からの光が前方 (cosθ'=β) へ傾く");
assert(aberrate(0.5, 0.3) > 0.5, "光行差: 運動方向へ光が集まる (cosθ' > cosθ)");

/* 2. 光路差反射システム */
const snellRefract = G("snellRefract");
assert(near(snellRefract(1.5, 30), Math.asin(0.5 / 1.5), 1e-12),
       "スネル屈折: n=1.5, θi=30° → θt=asin(1/3)≈19.47°");
assert(near(snellRefract(1.52, 0), 0, 1e-12), "垂直入射は屈折角 0");

const opticalPathDiff = G("opticalPathDiff");
assert(near(opticalPathDiff(1.38, 100, 0), 276, 1e-9),
       "光路差: n=1.38, d=100nm, θ=0 → Δ=2nd=276nm");
assert(opticalPathDiff(1.52, 180, 45) < opticalPathDiff(1.52, 180, 0),
       "斜入射で cosθt < 1 → Δ が減少");

const opdPhase = G("opdPhase");
const fringeIntensity = G("fringeIntensity");
assert(near(opdPhase(266, 532), 2 * Math.PI, 1e-12),
       "Δ=λ/2 で φ=2π (外面反射の λ/2 跳び込みで強め合い)");
assert(near(fringeIntensity(2 * Math.PI), 1, 1e-12), "φ=2π でフリンジ強度 I=1");
assert(near(fringeIntensity(Math.PI), 0, 1e-12), "φ=π で I=0 (打ち消し)");

/* 3. 相対論込み光路差 */
const relativisticOPD = G("relativisticOPD");
const r0 = relativisticOPD(1.52, 180, 30, 532, 0);
assert(near(r0.opdNm, opticalPathDiff(1.52, 180, 30), 1e-9) &&
       near(r0.phase, opdPhase(r0.opdNm, 532), 1e-9),
       "v=0 で静止解 (Δ, φ) に厳密一致");
assert(near(r0.gamma, 1, 1e-15) && near(r0.doppler, 1, 1e-15),
       "v=0 で γ=1, D=1");
const C = G("C_LIGHT");
const rHalf = relativisticOPD(1.52, 180, 30, 532, 0.5 * C);
assert(near(rHalf.gamma, 1 / Math.sqrt(0.75), 1e-12), "v=0.5c で γ=1.1547…");
assert(rHalf.doppler > 1 && rHalf.lambdaObsNm < 532,
       "接近 0.5c で青方偏移 (D>1, λ'<λ)");
assert(rHalf.thetaObsDeg < 30, "光行差で入射角が前方へ寄る (θ'<θ)");
const rWalk = relativisticOPD(1.52, 180, 30, 532, 1.4);
assert(rWalk.beta > 0 && rWalk.beta < 1e-8 && near(rWalk.opdNm, r0.opdNm, 1e-3),
       "歩行速度 1.4m/s では補正は極小 (β≈4.7e-9)");

/* 4. 両眼収束シフト */
const stereoShiftPx = G("stereoShiftPx");
const sNear = stereoShiftPx(64, 2, 1920, 46);
const sFar = stereoShiftPx(64, 4, 1920, 46);
assert(sNear > 0 && sFar > 0 && sNear > sFar,
       "収束シフト: 虚像が近いほど大きい (2m > 4m)");
assert(near(sNear, Math.atan(0.032 / 2) * (1920 / (46 * Math.PI / 180)), 1e-9),
       "収束シフトの厳密値 (atan(IPD/2/D)·px/rad)");

/* 5. コンシェルジュ「ミーミル」 */
const levenshtein = G("levenshtein");
assert(levenshtein("kitten", "sitting") === 3, "レーベンシュタイン距離 kitten→sitting = 3");
assert(levenshtein("", "abc") === 3 && levenshtein("abc", "abc") === 0,
       "レーベンシュタイン距離の境界条件");

const safeCalc = G("safeCalc");
assert(safeCalc("(2+3)*4") === 20, "計算機: (2+3)*4 = 20");
assert(safeCalc("3+4*2") === 11, "計算機: 演算子優先順位 3+4*2 = 11");
assert(near(safeCalc("10/4"), 2.5, 1e-12), "計算機: 10/4 = 2.5");
assert(isNaN(safeCalc("2+alert(1)")), "計算機: 不正トークンは NaN (コード実行なし)");

const mimirReply = G("mimirReply");
assert(mimirReply("3+4*2").reply.indexOf("11") >= 0, "ミーミル: 式を計算して応答");
assert(mimirReply("いま何時?").reply.indexOf(":") >= 0, "ミーミル: 時刻に応答");
assert(mimirReply("今日は何日?").reply.indexOf("年") >= 0, "ミーミル: 日付に応答");
const memoR = mimirReply("メモ 牛乳を買う");
assert(memoR.reply.indexOf("牛乳") >= 0, "ミーミル: メモを登録");
assert(mimirReply("メモ一覧").reply.indexOf("牛乳") >= 0, "ミーミル: メモ一覧に反映");
assert(mimirReply("メモ削除").reply.indexOf("削除") >= 0, "ミーミル: メモ削除");
assert(mimirReply("明るくして").action === "brighter", "ミーミル: 「明るくして」→ 輝度アップ操作");
assert(mimirReply("SBSにして").action === "sbs", "ミーミル: 「SBSにして」→ 両眼投影へ");
assert(mimirReply("光路差は?").reply.indexOf("nm") >= 0, "ミーミル: 現在の光路差を報告");
assert(mimirReply("相対論の補正は?").reply.indexOf("γ") >= 0, "ミーミル: 相対論補正を報告");
assert(mimirReply("こんにちは").reply.indexOf("ミーミル") >= 0, "ミーミル: 挨拶に応答");

/* 6. HUD 投影パイプライン */
const before = G("hudState").items.length;
assert(G("projectText")("テスト投影") === true, "projectText がカードを受理");
assert(G("hudState").items.length === before + 1 &&
       G("hudState").items[G("hudState").items.length - 1].content === "テスト投影",
       "hudState.items にカードが積まれる");
assert(G("projectText")("") === false, "空文字は投影しない");
assert(G("renderHUD")() === true, "renderHUD がスタブ DOM 上で完走");

console.log("\nMimir engine tests: all passed");
