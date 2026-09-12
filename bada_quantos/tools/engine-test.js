/*
 * engine-test.js — Bada QuantOS のエンジン単体テスト (Node で実行)
 *
 *   node bada_quantos/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM/localStorage を
 * スタブした上で純ロジック部分を検証します:
 *   1. 擬似量子カーネル (qkInterpret) — ベル状態 / GHZ / エラー / let·print
 *   2. トポロジー不変量 (topoInvariant) — 交点数・ライズ・⟨K⟩、全機能で一意
 *   3. トポロジー写像 (topoMap) — 機能 ↦ 基底状態の単射、準備回路の検算
 *   4. 連続変形 (topoRoute) — ハミング距離と X ゲート列
 *   5. 端末プロファイル (deviceProfile) — スマートフォン / タブレット / デスクトップ
 *   6. 電卓 (calcEval) — 再帰下降パーサ
 *   7. 意図解析 (intentDetect) — 電話番号抽出・各機能への振り分け
 *   8. 生成AIカーネル (aiKernel) — 6 段パイプラインと実行
 *   9. 実行系 (osDispatch) — テスト環境では発行せず記述のみ返す
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

/* ── DOM / localStorage スタブ ── */
function stubEl(){
  return new Proxy({ style: {}, classList: { add(){}, remove(){} }, value: "", textContent: "", innerHTML: "" }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus") return function(){};
      if (p === "getAttribute") return function(){ return "0"; };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console: console,
  Math: Math,
  Function: Function,
  setTimeout: function(fn){ fn(); },
  setInterval: function(){ return 0; },
  clearInterval: function(){},
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

/* 1. 擬似量子カーネル */
const bell = get("qkInterpret")("qubit q0 q1\nH q0\nCNOT q0 q1\nstate\nmeasure");
assert(/\|00⟩ 0\.707/.test(bell) && /\|11⟩ 0\.707/.test(bell), "bell state amplitudes 1/√2 (|00⟩+|11⟩)");
assert(/measure → \|(00|11)⟩/.test(bell), "measurement collapses to correlated |00⟩ or |11⟩");
const ghz = get("qkInterpret")("qubit q0 q1 q2\nH q0\nCNOT q0 q1\nCNOT q1 q2\nstate");
assert(/\|000⟩ 0\.707/.test(ghz) && /\|111⟩ 0\.707/.test(ghz), "GHZ state has |000⟩ and |111⟩ at 1/√2");
assert(/!!/.test(get("qkInterpret")("H q9")), "interpreter reports errors for undeclared qubits");
assert(/print → 6/.test(get("qkInterpret")("let x = 1 + 2\nlet y = x * 2\nprint y")), "let/print classical arithmetic works");

/* 2. トポロジー不変量 */
const inv3 = get("topoInvariant")([1, 1, 1]);
assert(inv3.crossings === 3 && inv3.writhe === 3 && inv3.aExp === 9, "trefoil-like curl [+1,+1,+1] → c=3, w=3, A-exponent 9");
assert(/\(−A³\)\^3/.test(inv3.bracket), "Kauffman bracket of w=3 curls is (−A³)^3");
const inv0 = get("topoInvariant")([]);
assert(inv0.crossings === 0 && inv0.writhe === 0 && inv0.bracket === "1", "unknot (AI kernel) has trivial bracket 1");
const apps = get("OS_APPS");
const keys = new Set();
for (const a of apps) keys.add(get("topoInvariant")(a.knot).key);
assert(keys.size === apps.length, "invariant (c,w) is distinct for every OS function (injective classification)");

/* 3. トポロジー写像 */
const phone = get("topoMap")("phone");
assert(phone.ket === "|0001⟩", "phone maps to basis |0001⟩");
const camera = get("topoMap")("camera");
assert(camera.ket === "|0101⟩", "camera maps to basis |0101⟩");
const kets = new Set();
for (const a of apps) kets.add(get("topoMap")(a.id).ket);
assert(kets.size === apps.length, "φ is injective: every function gets a unique basis state");
const prep = get("qkInterpret")(camera.program);
assert(/\|0101⟩ 1\.000/.test(prep), "camera's preparation circuit reaches |0101⟩ with amplitude 1.000");
assert(get("topoMap")("nosuch") === null, "unknown function maps to null");

/* 4. 連続変形 */
const route = get("topoRoute")("phone", "camera");
assert(route.hamming === 1 && route.steps.length === 1 && route.steps[0] === "X q1", "phone→camera is one hypercube edge (X q1)");
const far = get("topoRoute")("ai", "settings");
assert(far.hamming === far.steps.length && far.hamming >= 1, "route step count equals Hamming distance");
const self = get("topoRoute")("phone", "phone");
assert(self.hamming === 0 && self.steps.length === 0, "identity deformation has zero steps");

/* 5. 端末プロファイル */
const sp = get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile Safari", 412);
assert(sp.kind === "smartphone" && sp.tel === true, "Android Mobile UA → smartphone with tel: capability");
const tb = get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; SM-X910) Safari", 1280);
assert(tb.kind === "tablet" && tb.tel === true, "Android non-Mobile UA → tablet");
const ip = get("deviceProfile")("Mozilla/5.0 (iPad; CPU OS 17_0)", 1024);
assert(ip.kind === "tablet", "iPad UA → tablet");
const dt = get("deviceProfile")("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", 1920);
assert(dt.kind === "desktop" && dt.tel === false, "Windows UA → desktop without phone line");

/* 6. 電卓 */
assert(get("calcEval")("1+2*3") === 7, "calcEval respects operator precedence (1+2*3=7)");
assert(get("calcEval")("(1+2)*3") === 9, "calcEval handles parentheses ((1+2)*3=9)");
assert(Math.abs(get("calcEval")("10/4") - 2.5) < 1e-12, "calcEval divides (10/4=2.5)");
let threw = false;
try { get("calcEval")("1+"); } catch (e) { threw = true; }
assert(threw, "calcEval rejects malformed expressions");

/* 7. 意図解析 */
const it1 = get("intentDetect")("090-1234-5678 に電話をかけて");
assert(it1.intent === "phone" && it1.number === "090-1234-5678", "intent: phone call with extracted number");
assert(get("intentDetect")("写真を撮って").intent === "camera", "intent: 写真 → camera");
const it3 = get("intentDetect")("7時にアラームをかけて起こして");
assert(it3.intent === "clock" && it3.hour === "7", "intent: alarm with extracted hour");
assert(get("intentDetect")("1+2*3").intent === "calc", "intent: bare expression → calc");
assert(get("intentDetect")("qubit q0\nH q0\nmeasure").intent === "quantum_code", "intent: raw quantum code");
assert(get("intentDetect")("トポロジーの写像を見せて").intent === "topo", "intent: 写像 → topo");
assert(get("intentDetect")("こんにちは").intent === "chat", "intent: greeting → chat");

/* 8. 生成AIカーネル */
const k1 = get("aiKernel")("090-1234-5678 に電話をかけて");
assert(k1.stages.length === 6, "kernel pipeline discloses all 6 stages");
assert(k1.stages[2].name.indexOf("トポロジー写像") >= 0 && /\|0001⟩/.test(k1.stages[2].detail), "stage③ shows the topological mapping to |0001⟩");
assert(k1.action.type === "tel" && k1.action.number === "090-1234-5678", "phone request produces a tel: action");
const k2 = get("aiKernel")("1+2*3");
assert(/= 7/.test(k2.reply), "calculator request is evaluated in the reply (=7)");
const k3 = get("aiKernel")("qubit q0 q1\nH q0\nCNOT q0 q1\nstate");
assert(/0\.707/.test(k3.reply), "pasted quantum code is executed by the pseudo-quantum kernel");
const k4 = get("aiKernel")("こんにちは");
assert(k4.reply.length > 0 && k4.intent === "chat", "chat produces a generated reply");

/* 9. 実行系 (テスト環境では location が無い → 発行せず記述を返す) */
const d1 = get("osDispatch")({ action: { type: "tel", number: "0312345678" } });
assert(d1.performed === false && /tel:0312345678/.test(d1.how), "tel dispatch in test env describes the intent without navigating");
const d2 = get("osDispatch")({ action: { type: "open", app: "camera" } });
assert(d2.performed === true && /camera/.test(d2.how), "open dispatch reports the mapped transition");

console.log("\nALL ENGINE TESTS PASSED");
