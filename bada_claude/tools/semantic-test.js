/*
 * semantic-test.js — 意味認識システム (semantic.bada) のテスト
 *   node bada_claude/tools/semantic-test.js
 */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const kb = JSON.parse(html.match(/<script type="application\/json" id="kb-data">([\s\S]*?)<\/script>/)[1]);
const brainSrc = html.match(/<script type="text\/bada" id="brain-src">([\s\S]*?)<\/script>/)[1];
const scripts = Array.from(html.matchAll(/<script>([\s\S]*?)<\/script>/g), m => m[1]);
const ctx = { console, TextEncoder, TextDecoder }; ctx.window = ctx; vm.createContext(ctx);
vm.runInContext(scripts[0] + "\n;globalThis.BadaEngine = BadaEngine;", ctx); vm.runInContext(scripts[1], ctx);
const I = new ctx.BadaEngine.Interp({ host: { kb, mode: () => "local" }, maxSteps: 4e9 });
ctx.BadaLab.install(I); I.run(brainSrc);
const call = (n, a) => I.call(I.global.get(n), a || []);
call("brain_boot");

let pass = 0, fail = 0;
const ok = (c, name, extra) => { if (c) { pass++; console.log("  ✓ " + name); } else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + String(extra).slice(0, 300) : "")); } };
const near = (a, b, e) => Math.abs(a - b) < (e || 1e-9);

console.log("エントロピー方程式群");
ok(near(call("sem_density", [Math.E]), Math.E) && call("sem_density", [1]) === 0 && call("sem_density", [0]) === 0, "(E1) x log x");
const uni = call("sem_bag", ["zeta beta gamma jones"]);
ok(near(call("sem_entropy", [uni]), Math.log(4)), "(E1) 一様な 4 語のエントロピーは log 4");
ok(call("sem_entropy", [call("sem_bag", ["zeta zeta zeta"])]) === 0, "(E1) 1 語だけならエントロピー 0");
ok(near(call("sem_divergence", [uni, uni]), 0), "同じ分布のずれは 0");
ok(near(call("sem_divergence", [uni, call("sem_bag", ["manifold entropy quantum"])]), Math.log(2)), "共通の語が無ければずれは log 2");
const a = call("sem_bag", ["zeta beta gamma"]), b = call("sem_bag", ["zeta beta jones"]);
ok(near(call("sem_divergence", [a, b]), call("sem_divergence", [b, a])) && call("sem_divergence", [a, b]) > 0 && call("sem_divergence", [a, b]) < Math.log(2), "ずれは対称で 0 と log 2 の間");
// (E2) の境界: D = 0 のとき x log x = 1、つまり x = e^{W(1)} が門のしきい値
const root = call("xlogx_root");
ok(call("sem_gate", [Math.log(root) + 1e-9, 0]).pass && !call("sem_gate", [Math.log(root) - 1e-6, 0]).pass, "(E2) D = 0 の門のしきい値は x log x = 1 の根 e^{W(1)} = " + root.toFixed(6));
const g = call("sem_gate", [2, 0.3]);
ok(near(g.lhs, Math.log(Math.exp(2) * 2)) && near(g.rhs, 2 * Math.sqrt(0.3 * Math.exp(0.3))), "(E2) 両辺の値");
ok(call("sem_gate", [3, 0.2]).margin > call("sem_gate", [3, 0.6]).margin, "(E2) ずれが大きいほど門は厳しくなる");
ok(!call("sem_gate", [0, 0.1]).pass, "(E2) 情報量 0 の文は通らない");
// (E3) 事前分布
call("sem_boot");
const SEM = I.global.get("SEM");
let z = 0; for (let r = 1; r <= SEM.V; r++) z += call("sem_kernel", [r]);
ok(near(z + SEM.tail, SEM.Z, 1e-9) && SEM.tail > 0 && SEM.tail < 1e-4, "(E3) 核 1/((r+1) log(r+1))² の総和は収束し、未知語の質量が残る");
ok(call("sem_kernel", [1]) > call("sem_kernel", [2]) && call("sem_kernel", [2]) > call("sem_kernel", [100]), "(E3) 順位が下がるほど事前確率が下がる");
const pz = call("sem_prob", ["zeta"]), pu = call("sem_prob", ["存在しない語xyz"]);
ok(pz > pu && pu > 0, "(E3) 未知語にも正の確率 (驚きが有限)");
ok(call("sem_surprisal", ["存在しない語xyz"]) > call("sem_surprisal", ["zeta"]), "頻出語より未知語のほうが驚きが大きい");
// (E4) 流れ
const corpusText = kb.chunks.find(c => /[ぁ-ん]/.test(c.text) && c.text.length > 300).text.replace(/\n/g, "").slice(0, 200);
const f1 = call("sem_flow", [corpusText]), f2 = call("sem_flow", ["ぬるぽよ〜ん★ふがふが＠＠みょーん％％ぽよぽよ"]);
ok(f1.F >= 0 && f1.mean < f2.mean, "(E4) コーパスの文は無意味な文字列より平均の驚きが小さい", f1.mean + " vs " + f2.mean);

console.log("意味認識");
// 文書の前半から、同じ文書の後半を当てる (60 文書、まぐれ当たり 1.7%)
const chunks = kb.chunks.filter(c => c.text.length > 400), step = Math.floor(chunks.length / 60), pick = chunks.filter((c, i) => i % step === 0).slice(0, 60);
const A = pick.map(c => call("sem_bag", [c.text.slice(0, c.text.length >> 1)])), Bq = pick.map(c => call("sem_bag", [c.text.slice(c.text.length >> 1)]));
let top1 = 0, top3 = 0;
A.forEach((x, i) => { const d = Bq.map((y, j) => [call("sem_divergence", [x, y]), j]).sort((p, q) => p[0] - q[0]); if (d[0][1] === i) top1++; if (d.slice(0, 3).some(p => p[1] === i)) top3++; });
console.log(`    文書の照合: 1 位正解 ${top1}/${pick.length}, 3 位以内 ${top3}/${pick.length} (まぐれ当たり ${(100 / pick.length).toFixed(1)}%)`);
ok(top1 >= 18 && top3 >= 30, "ずれ D による文書の照合がまぐれ当たりを大きく上回る");
let r = call("respond", ["意味を認識して: ゼータ関数の零点は臨界線上に並び、素数の分布と結びつく"]);
ok(r.intent === "semantic" && /情報量 H/.test(r.text) && /\*\*成立\*\*/.test(r.text) && /意味の担い手/.test(r.text) && /最も近い文脈/.test(r.text), "意味認識の応答");
ok(/真偽は判定しません/.test(r.text), "真偽を判定しないと明記");
ok(/\*\*不成立\*\*/.test(call("respond", ["意味を認識して: あ"]).text), "情報量の無い文は門を通らない");
ok(call("respond", ["リーマン予想の意味は?"]).intent !== "semantic", "「意味は?」という普通の質問は意味認識にしない");

console.log("意味認識つき言語生成");
call("seed", [3]);
const hits = call("retrieve", ["ゼータ関数", 0]), gen = call("sem_generate", ["ゼータ関数", hits, 8]);
const passing = gen.cands.filter(c => c.pass), pool = passing.length ? passing : gen.cands;
ok(gen.cands.length === 8, "候補 8 個");
ok(pool.every(c => gen.best.score >= c.score), "門を通った候補のうちスコア最大を選ぶ");
ok(gen.best.D <= gen.cands.reduce((s, c) => s + c.D, 0) / gen.cands.length, "選んだ文の文脈とのずれは候補の平均以下", gen.best.D);
r = call("respond", ["ゼータ関数で文章を生成して"]);
ok(r.intent === "generate" && /意味認識による選別/.test(r.text) && /◀/.test(r.text) && /正しさは保証しません/.test(r.text), "生成の応答に選別の表と注記");
ok(I.Omega.items.some(t => t[0] === "generate") && I.Omega.items.some(t => t[0] === "semantic"), "台帳 Ω に記録");

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
