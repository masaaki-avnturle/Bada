/*
 * lab-test.js — 証明ラボ (lab.js / lab.bada) と頭脳への統合のテスト
 *   node bada_claude/tools/lab-test.js
 * 配布物 index.html から各スクリプトを取り出し、アプリと同じ順で起動して検証します。
 */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const kb = JSON.parse(html.match(/<script type="application\/json" id="kb-data">([\s\S]*?)<\/script>/)[1]);
const brainSrc = html.match(/<script type="text\/bada" id="brain-src">([\s\S]*?)<\/script>/)[1];
const scripts = Array.from(html.matchAll(/<script>([\s\S]*?)<\/script>/g), m => m[1]);
const ctx = { console, TextEncoder, TextDecoder };
ctx.window = ctx; vm.createContext(ctx);
vm.runInContext(scripts[0] + "\n;globalThis.BadaEngine = BadaEngine;", ctx);   // engine.js
vm.runInContext(scripts[1], ctx);                                             // BadaGPT エンジン + 対話層 + lab.js
const { BadaEngine: B, BadaLab: Lab } = ctx;

let pass = 0, fail = 0;
const ok = (c, name, extra) => { if (c) { pass++; console.log("  ✓ " + name); } else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + String(extra).slice(0, 300) : "")); } };
function boot(mode) {
  const I = new B.Interp({ host: { kb, mode: () => mode || "local" }, maxSteps: 4e9 });
  Lab.install(I); I.run(brainSrc);
  const call = (n, a) => I.call(I.global.get(n), a || []);
  call("brain_boot");
  return { I, ask: t => call("respond", [t]) };
}
const { I, ask } = boot();

console.log("リバイザ (@reviser RIGOR)");
ok(["target", "strict", "selftest", "obligation"].every(r => I.rules.has(r)), "規則が文法台帳に入る");
ok(I.global.get("TARGETS").length === 8, "対象言語 8 つ");
ok(I.global.get("OBLIGATIONS").length === 3, "義務 3 つ");
ok(I.Omega.items.some(t => t[0] === "rigor.target" && t[1] === "rust" && t[2] === "checked128"), "規則が台帳 Ω に commit される");
I.run('selftest "python", 50\nstrict "python", "追加の規則"');
ok(I.global.get("STRICT").python.selftest === 50 && I.global.get("STRICT").python.notes.length === 2, "規則を後から文として追加できる");

console.log("意図推定");
const intents = {
  "リーマン予想を高さ 100 まで調べて": "prove", "コラッツ予想を 10 ビットで検証して": "prove", "Σ k^2 = n(n+1)(2n+1)/6": "prove",
  "未解決問題の反例を探して": "prove", "論文を作成して": "paper", "リーマン予想の証明の論文を書いて": "paper",
  "厳密なソースコードを生成して": "codegen", "rust でコードを生成して": "codegen", "[1,1,1] で暗号化: こんにちは": "crypto",
  "リーマン予想は証明されたの?": "open_problem", "ベル状態を作って": "quantum", "計算 zeta(2)": "calc", "あなたは誰?": "identity",
  "ゼータ関数とベータ関数の関係は?": "explain", "方程式は全部で何本?": "stats", "ゼータ関数で文章を生成して": "generate"
};
for (const t in intents) { const r = ask(t); ok(r.intent === intents[t], `「${t}」→ ${intents[t]}`, r.intent); }

console.log("証明");
let r = ask("リーマン予想を高さ 100 まで証明して");
ok(/N\(T\) = 29/.test(r.text) && /【リーマン予想】 判定: \? 未解決/.test(r.text), "RH: 有限範囲は検証、予想は未解決");
ok(!/リーマン予想】 判定: ∎/.test(r.text), "RH を証明済みと出力しない");
r = ask("Σ k^2 = n(n+1)(2n+1)/5");
ok(/反証/.test(r.text) && /\(1\/6\)·n/.test(r.text) && /証明完了/.test(r.text), "誤った式を反証して修正");

console.log("論文");
r = ask("論文を作成して");
ok(r.intent === "paper" && /^# 定理/.test(r.text) && /数学的帰納法により/.test(r.text), "直前の主張の論文");
ok(/元の主張とその修正/.test(r.text) && /\\frac\{1\}\{3\}n\^\{3\}/.test(r.text), "修正の経緯と LaTeX の式");
ok(r.files.length === 2 && /\\begin\{theorem\}/.test(r.files[1].text) && /\\end\{document\}/.test(r.files[1].text), "paper.md と paper.tex");
const sealLine = r.files[0].text.match(/鍵指紋 ([0-9a-f]{16})/);
ok(sealLine && sealLine[1] === "0661037b539b7507", "Jones 暗号で封印 (三葉結び目の鍵)");
for (const t of ["リーマン予想", "深リーマン予想", "コラッツ予想", "ゴールドバッハ予想"]) {
  r = ask(t + "の証明の論文を作成して");
  ok(/証明ではない/.test(r.text) && /未解決/.test(r.text) && !/証明完了 \(QED\) · \*\*手法/.test(r.text) && !/\\begin\{proof\}/.test(r.files[1].text), t + ": 証明の論文ではなく証拠の報告になる");
}
const p = Lab.paper(Lab.makeSpec("Σ k = n(n+1)/2"));
ok(Lab.checkSealText(p.md.split("\n\n---\n封印")[0], p.seal) && !Lab.checkSealText(p.md.split("\n\n---\n封印")[0] + "x", p.seal), "封印は改ざんを検出する");

console.log("厳密化されたソースコード");
ask("Σ k^3 = (n(n+1)/2)^2");
r = ask("厳密なソースコードを rust と c で生成して");
ok(r.intent === "codegen" && r.files.length === 8, "8 言語のファイル", r.files.length);
ok(/RS01[^\n]*✓/.test(r.text) && /RS02[^\n]*✓/.test(r.text) && /RS03[^\n]*✓/.test(r.text), "義務 RS01〜RS03 が成立");
ok(/```rust/.test(r.text) && /```c\n/.test(r.text) && !/```python/.test(r.text), "指定した言語だけ本文に表示");
ok(/checked_mul/.test(r.files.find(f => f.name === "rigor_sum.rs").text) && /__builtin_mul_overflow/.test(r.files.find(f => f.name === "rigor_sum.c").text), "桁あふれ検査つき");
ok(/OK 404010000/.test(r.text), "期待される出力");
const bada = r.files.find(f => f.name === "rigor_sum.bada").text, sub = new B.Interp({ maxSteps: 4e8 }); sub.run(bada);
ok(sub.out.join("") === "OK 404010000", "生成した Bada 版が実行できる", sub.out.join(""));
r = ask("Σ k/2 = n(n+1)/4 の厳密なソースコードを生成して");
ok(/RS02[^\n]*✗/.test(r.text) && r.files.length === 0 && /生成しません/.test(r.text), "義務を満たさなければ生成しない");
r = boot().ask("厳密なソースコードを生成して");
ok(r.files.length === 0 && /対象の主張がありません/.test(r.text), "主張が無ければ生成しない");

console.log("量子暗号");
r = ask("[1,-2,1,-2] で暗号化: 明日の朝に会いましょう");
const hx = (r.text.match(/[0-9a-f]{98,}/) || [""])[0];
ok(r.intent === "crypto" && hx && /鍵指紋/.test(r.text), "暗号化");
ok(/明日の朝に会いましょう/.test(ask("復号 [1,-2,1,-2] " + hx).text), "同じ組みひもで復号");
ok(/復号できません/.test(ask("復号 [1,1,1] " + hx).text), "違う組みひもでは復号できない");
ok(/復号できません/.test(ask("復号 [1,-2,1,-2] " + hx.slice(0, -2) + (hx.slice(-2) === "00" ? "01" : "00")).text), "改ざんされた暗号文を拒否");

console.log("Claude API モード (文脈の組み立てのみ。送信はしない)");
const llm = boot("llm");
r = llm.ask("Σ k^2 = n(n+1)(2n+1)/6");
ok(r.mode === "llm" && /<tool_result tool="prove:induct">/.test(r.system) && /証明完了/.test(r.system), "検証結果を tool_result として渡す");
ok(/判定を格上げしたり/.test(r.system), "判定を変えない指示を含む");
r = llm.ask("[1,1,1] で暗号化: ひみつ");
ok(r.mode === "local" && !r.system, "暗号化は API に送らない");

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
