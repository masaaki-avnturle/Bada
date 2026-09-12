/*
 * engine-test.js — BadaGPT道場のエンジン単体テスト (Node で実行)
 *
 *   node bada_gpt_dojo/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM/localStorage を
 * スタブした上で純ロジック部分を検証します:
 *   1. 量子 Bada インタープリタ — ベル状態 / GHZ / エラー報告
 *   2. トークン化 — 第一の技
 *   3. トランスフォーマー — self-attention の行和 / 次トークン予測
 *   4. 意図解析 — 第四の技
 *   5. BadaGPT パイプライン — 全 6 段階の開示と応答
 *   6. アプリ錬成 (appForge) と Bada on Rails scaffold
 *   7. 道場カリキュラム — 印可判定 (lessonCheck) と段位 (dojoProgress)
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

/* 1. 量子 Bada インタープリタ */
const bell = get("badaInterpret")("qubit q0 q1\nH q0\nCNOT q0 q1\nstate\nmeasure");
assert(/\|00⟩ 0\.707/.test(bell) && /\|11⟩ 0\.707/.test(bell), "bell state amplitudes 1/√2 (|00⟩+|11⟩)");
assert(/measure → \|(00|11)⟩/.test(bell), "measurement collapses to correlated |00⟩ or |11⟩");
const ghz = get("badaInterpret")("qubit q0 q1 q2\nH q0\nCNOT q0 q1\nCNOT q1 q2\nstate");
assert(/\|000⟩ 0\.707/.test(ghz) && /\|111⟩ 0\.707/.test(ghz), "GHZ state has |000⟩ and |111⟩ at 1/√2");
const err = get("badaInterpret")("H q9");
assert(/!!/.test(err), "interpreter reports errors for undeclared qubits");
const calc = get("badaInterpret")("let x = 1 + 2\nlet y = x * 2\nprint y");
assert(/print → 6/.test(calc), "let/print classical arithmetic works");

/* 2. トークン化 */
const toks = get("gptTokenize")("CNOT q0 q1 measure");
assert(toks.length === 4 && toks[0] === "CNOT", "tokenizer splits 'CNOT q0 q1 measure' into 4 tokens");

/* 3. トランスフォーマー */
get("tfTrain")("qubit q0 q1\nH q0\nCNOT q0 q1\nmeasure");
const p = get("transformerPredict")("qubit q0 q1 H", 5);
assert(p.preds[0].w === "q0", "after training, H → q0 is the top next-token prediction");
let sum = 0; for (const x of p.preds) sum += x.p;
assert(sum > 0 && sum <= 1.0001, "prediction probabilities form a sub-distribution");
for (const row of p.attn){
  const t = row.reduce(function(a, b){ return a + b; }, 0);
  assert(Math.abs(t - 1) < 1e-9, "attention row sums to 1 (softmax)");
}

/* 4. 意図解析 */
assert(get("intentDetect")("ベル状態を作って").intent === "bell", "intent: ベル状態 → bell");
assert(get("intentDetect")("Book title:string を管理するアプリ").intent === "scaffold", "intent: 管理アプリ → scaffold");
assert(get("intentDetect")("補完: qubit q0 H").intent === "complete", "intent: 補完 → complete");
assert(get("intentDetect")("qubit q0\nH q0\nmeasure").intent === "quantum_code", "intent: raw code → quantum_code");

/* 5. BadaGPT パイプライン (技の開示) */
const pipe = get("gptPipeline")("ベル状態を作って");
assert(pipe.stages.length === 6, "pipeline exposes all 6 stages (tokenize→intent→plan→generate→verify→reply)");
assert(pipe.stages[0].name.indexOf("トークン化") >= 0 && pipe.stages[4].name.indexOf("検証") >= 0, "stages are labeled with the technique names");
assert(/0\.707/.test(pipe.reply), "bell reply contains executed amplitudes");
const pipe2 = get("gptPipeline")("qubit q0\nH q0\nmeasure");
assert(/measure → \|[01]⟩/.test(pipe2.reply), "pasted quantum code is executed in the reply");

/* 6. アプリ錬成 + Bada on Rails */
const f = get("appForge")("Book title:string author:string を管理するアプリを作って");
assert(f.kind === "scaffold" && f.name === "Book", "appForge parses a Japanese request into a Book scaffold");
assert(f.fields.indexOf("title:string") >= 0 && f.fields.indexOf("author:string") >= 0, "appForge extracts the field list");
assert(f.steps.length >= 5, "appForge discloses the 5-step technique");
const r = get("railsScaffold")("Post", ["title:string", "body:text"]);
assert(/model Post/.test(r.code) && /resources :post/.test(r.code), "scaffold generates model/controller/routes code");
const g = get("appForge")("「測定する」ボタンのある画面を作って");
assert(g.kind === "gui" && /on click/.test(g.code), "GUI request forges a form/button app");

/* 7. 道場カリキュラム */
assert(get("lessonCheck")("L1", "4").pass, "L1 (tokenize) accepts the correct token count");
assert(!get("lessonCheck")("L1", "9").pass, "L1 rejects a wrong count");
assert(get("lessonCheck")("L2", "1").pass, "L2 (attention row sum) accepts 1");
assert(get("lessonCheck")("L3", "q0").pass, "L3 (next-token) accepts q0");
assert(get("lessonCheck")("L4", "ベル状態を作って").pass, "L4 accepts a prompt that routes to bell");
assert(get("lessonCheck")("L5", "Book title:string を管理するアプリを作って").pass, "L5 accepts a prompt that forges Book scaffold");
assert(!get("lessonCheck")("L6", "H q0").pass, "L6 rejects broken code");
assert(get("lessonCheck")("L6", "qubit q0\nH q0\nmeasure").pass, "L6 accepts self-repaired code");
assert(get("lessonCheck")("L7", "qubit q0 q1\nH q0\nCNOT q0 q1\nstate\nmeasure").pass, "L7 accepts a bell-state program");
const pg = get("dojoProgress")();
assert(pg.done === pg.total && pg.rank === "免許皆伝", "passing all lessons grants 免許皆伝");

console.log("\nALL ENGINE TESTS PASSED");
