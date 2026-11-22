/*
 * engine-test.js — BadaClaude の単体テスト (Node で実行)
 *
 *   node bada_claude/tools/engine-test.js
 *
 * index.html (配布物そのもの) から Bada 処理系・知識ベース・brain.bada を
 * 取り出して検証します:
 *   1. Bada 言語: 束縛 / 関数 / クロージャ / ラムダ / struct / 制御構文
 *   2. 原稿の演算子: >> commit, <- append, :: scope, ~ consistency, => query
 *   3. @reviser による文法拡張 (規則が次の文の構文になる)
 *   4. 数値核: Γ, β, ζ (実・複素), Lambert W, Riemann–Siegel θ / Z, Jones
 *   5. Unknown-Prior Engine: ゼロ保存と |ψ|² = a (原稿 S.22 / Q.16)
 *   6. Q# 型量子副言語: ベル状態, GHZ, 測定の台帳 commit
 *   7. 知識ベース: 方程式 2111 本 (成立 231 / 不成立 181) と論文チャンク
 *   8. brain.bada: 意図推定・検索・道具・生成と Claude API 用文脈の組み立て
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const grab = re => { const m = html.match(re); if (!m) { console.error("missing section: " + re); process.exit(1); } return m[1]; };
const kb = JSON.parse(grab(/<script type="application\/json" id="kb-data">([\s\S]*?)<\/script>/));
const brainSrc = grab(/<script type="text\/bada" id="brain-src">([\s\S]*?)<\/script>/);
const engineSrc = grab(/<script>\s*(\/\*\s*\n \* engine\.js[\s\S]*?)<\/script>/);

const ctx = { module: { exports: {} }, console };
vm.createContext(ctx);
vm.runInContext(engineSrc, ctx);
const B = ctx.module.exports;

let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + extra : "")); }
}
const near = (a, b, tol) => Math.abs(a - b) <= (tol || 1e-9) * Math.max(1, Math.abs(b));
function run(src, I) { I = I || new B.Interp(); return { v: I.run(src), I }; }
function throws(src) { try { new B.Interp().run(src); return false; } catch (e) { return e instanceof B.BadaError; } }

console.log("1. Bada 言語");
ok(run("x := 1 + 2 * 3\nx").v === 7, "束縛と演算子の優先順位");
ok(run("2 ^ 3 ^ 2").v === 512, "べき乗は右結合");
ok(run("fn f(n) { if n < 2 { return 1 } return n * f(n-1) }\nf(10)").v === 3628800, "再帰関数");
ok(run("mk := fn() { n := 0; return || { n = n + 1; return n } }\nc := mk()\nc(); c(); c()").v === 3, "クロージャ");
ok(B.show(run("map([1,2,3], |x| x * x)").v, 1) === "[1, 4, 9]", "ラムダと map");
ok(run("s := 0\nfor x, i in [5, 6, 7] { s = s + x * i }\ns").v === 20, "for (値, 添字)");
ok(run("n := 0\nwhile true { n += 1\n if n >= 5 { break } }\nn").v === 5, "while / break / +=");
ok(run("struct V { x, y }\nfn V.norm(self) { return sqrt(self.x^2 + self.y^2) }\nV(3, 4).norm()").v === 5, "struct とメソッド");
ok(run("m := {a: 1, b: [2, 3]}\nm.b[1] + m[\"a\"]").v === 4, "マップと添字");
ok(run("if 0 { 1 } elif nil { 2 } else { 3 }").v === 3, "if / elif / else");
ok(run("1 / 0").v === 0, "原稿 S.25: a / 0 = 0");
ok(throws("undefined_name + 1"), "未定義名はエラー");
ok(throws("while true { }"), "無限ループはステップ上限で停止");
ok(run("「日本語の文字列」").v === "日本語の文字列", "かぎ括弧の文字列リテラル");

console.log("2. 原稿の演算子");
{
  const { v, I } = run("Omega >> [\"fact\", 1]\nOmega >> [\"fact\", 2]\nlen(Omega::DATABASE)");
  ok(v === 2 && Object.isFrozen(I.Omega.items[0]), ">> は append-only 台帳へ commit (凍結)");
}
ok(B.show(run("xs := [1]\nxs <- 2\nxs").v, 1) === "[1, 2]", "<- は配列へ追加");
ok(run("STAR ~ 42").v === true && run("1 ~ \"a\"").v === false, "~ は漸進型の整合");
ok(B.show(run("[1, 2, 3] => |x| x + 1").v, 1) === "[2, 3, 4]", "=> は写像照会");

console.log("3. @reviser 文法拡張");
{
  const { v, I } = run("@reviser GRAMMAR {\n  rule bell(r) { H(r, 0); CNOT(r, 0, 1) }\n}\nqubit q[2]\nbell q\nqstate(q)");
  ok(v === "0.7071|00⟩ + 0.7071|11⟩", "rule bell が新しい文 `bell q` になる", v);
  ok(I.Omega.items.some(f => f[0] === "rule" && f[1] === "bell"), "規則は台帳に commit される");
  ok(throws("qubit q[2]\nbell q"), "reviser の前には `bell q` は構文エラー / 未定義");
}

console.log("4. 数値核");
const E = s => new B.Interp().evalExpr(s);
ok(near(E("gamma(0.5)"), Math.sqrt(Math.PI), 1e-12), "Γ(1/2) = √π");
ok(near(E("beta(0.5, 0.5)"), Math.PI, 1e-12), "β(1/2, 1/2) = π (論文集 1.2)");
ok(near(E("beta(2, 3)"), 1 / 12, 1e-12), "β(2, 3) = 1/12 (ACAFE.17)");
ok(near(E("zeta(2)"), Math.PI ** 2 / 6, 1e-12), "ζ(2) = π²/6");
ok(near(E("zeta(-1)"), -1 / 12, 1e-10), "ζ(−1) = −1/12 (関数等式)");
ok(E("zeta(-2)") === 0, "自明な零点 ζ(−2) = 0");
{
  const s = 2.5, lhs = B.zeta(s);
  const rhs = 2 ** s * Math.PI ** (s - 1) * Math.sin(Math.PI * s / 2) * B.beta(s, 1 - s) / B.gamma(s) * B.zeta(1 - s);
  ok(near(lhs, rhs, 1e-9), "定理 I-1: ベータ型関数等式 (s = 2.5)", lhs + " vs " + rhs);
}
ok(Math.abs(E("rs_Z(14.134725142)")) < 1e-6, "Z(t) の第 1 零点 t = 14.1347…");
ok(near(E("rs_theta(11.7722)"), -2.58136, 1e-5), "設計図 ④ θ(φ) = −2.58136");
ok(near(E("rs_Z(11.7722)"), -1.33415, 1e-5), "設計図 ④ Z(φ) = −1.33415");
ok(near(E("lambertw(1)"), 0.5671432904097838, 1e-12), "Lambert W(1) = Ω 定数");
ok(near(E("xlogx_root()"), 1.763222834, 1e-9), "x log x = 1 の根 1.763222… (設計図 ②')");
ok(near(E("exp(lambertw(zeta(2)))"), 2.149534489, 1e-8), "定義方程式 ζ(s)/(x log x) = 1 の解 x(2)");
{
  const v = E("jones(\"3_1\", exp(cx(0, rs_theta(11.7722))))");
  ok(near(v.re, -0.116342, 1e-4) && near(v.im, 2.30908, 1e-4), "設計図 ⑤ Jones 3_1 = −0.116342 + 2.30908i", B.show(v));
}
ok(near(E("integrate(|x| exp(-x*x), -10, 10)") ** 2, Math.PI, 1e-9), "∫∫ e^{−x²−y²} = π (INV.1)");
ok(near(E("acosh(64800)"), 11.7722, 1e-5), "ラピディティ arcosh Γ = 11.7722 (設計図 ②)");

console.log("5. Unknown-Prior Engine");
{
  const { v } = run("z := [1.6, 0.6, 0.1, -40, -0.4, 1.1, -40, 0.4]\na := softmax(z)\ncs := cognitive_system(a, [[a, map(range(8), |i| 0.3 * i)], [unknown_prior(8), 0.5]], [0.7, 0.9])\n[zeros_of(a), cs.zeros, cs.maxdiff]");
  ok(B.show(v[0], 1) === "[3, 6]" && B.show(v[1], 1) === "[3, 6]", "ゼロ保存: base [3, 6] → posterior [3, 6] (S.22)");
  ok(v[2] < 1e-15, "|ψ|² = a (最大偏差 " + v[2].toExponential(2) + ")");
  ok(near(E("entropy(unknown_prior(4))"), Math.log(4), 1e-12), "H(unknown_prior(4)) = ln 4 (S.26)");
  const sm = E("softmax([2, 1, 0, -1])");
  ok(near(sm[0], 0.64391, 1e-4) && near(sm[3], 0.03206, 1e-3), "softmax([2,1,0,−1]) (S.26)");
  const p = run("p := unknown_prior(4)\nh := [entropy(p)]\nfor k in range(3) { p = update(p, [1, 0, 0, 0]); h <- entropy(p) }\nh").v;
  ok(p.every((x, i) => i === 0 || x < p[i - 1]), "未知事前分布のエントロピーは単調減少 (Q.20)");
}

console.log("6. Q# 型量子副言語");
{
  const { v } = run("qubit q[2]\nH(q, 0)\nCNOT(q, 0, 1)\nprobs(q)");
  ok(B.show(v, 1) === "[0.5, 0, 0, 0.5]", "ベル状態の確率");
  const g = run("qubit g[3]\nH(g, 0)\nCNOT(g, 0, 1)\nCNOT(g, 1, 2)\nqstate(g)").v;
  ok(g === "0.7071|000⟩ + 0.7071|111⟩", "GHZ 状態", g);
  const m = run("qubit q[2]\nH(q, 0)\nCNOT(q, 0, 1)\n[Measure(q, 0), Measure(q, 1)]");
  ok(m.v[0] === m.v[1], "もつれた測定結果は一致");
  ok(m.I.Omega.items.filter(f => f[0] === "measure").length === 2, "測定は台帳への commit (Q.21)");
  const z = run("qubit q[2]\nH(q, 0)\nS(q, 0)\nT(q, 0)\nRZ(q, 0, 1.3)\nprobs(q)").v;
  ok(z[2] === 0 && z[3] === 0, "位相ゲートは振幅ゼロの状態を復活させない (no-resurrection)");
  ok(throws("qubit q[2]\nCNOT(q, 0, 0)"), "制御と標的が同じ CNOT はエラー");
}

console.log("7. 知識ベース");
{
  const st = {}; kb.equations.forEach(e => st[e.status] = (st[e.status] || 0) + 1);
  ok(kb.equations.length === 2111, "方程式レジストリ 2111 本", kb.equations.length);
  ok(st.holds === 231 && st.differs === 181, "成立 231・不成立 181 (設計図の表紙と一致)", JSON.stringify(st));
  ok(kb.sources.length === 10 && kb.chunks.length > 150, "論文 10 本のチャンク " + kb.chunks.length + " 件");
  const a17 = kb.equations.find(e => e.id === "ACAFE.17");
  ok(a17 && a17.status === "holds" && a17.eq.includes("β(p,q)"), "ACAFE.17 の内容");
}

console.log("8. brain.bada");
{
  let mode = "local";
  const I = new B.Interp({ host: { kb, mode: () => mode }, maxSteps: 4e9 });
  I.run(brainSrc);
  const n = I.call(I.global.get("brain_boot"), []);
  ok(n === kb.equations.length + kb.chunks.length, "起動: 全文書を索引化 (" + n + ")");
  const ask = q => I.call(I.global.get("respond"), [q]);
  const cases = [
    ["こんにちは", "greet"], ["あなたは誰?", "identity"], ["ヘルプ", "help"], ["計算 zeta(2)", "calc"],
    ["ACAFE.17", "eqid"], ["方程式は全部で何本?", "stats"], ["ベル状態を作って", "quantum"],
    ["```bada\nprint(1 + 1)\n```", "code"], ["輸送機の設計図", "blueprint"], ["リーマン予想は証明されたの?", "open_problem"],
    ["ゼータ関数で文章を生成して", "generate"], ["ゼータ関数とベータ関数の関係は?", "explain"], ["もっと", "more"]
  ];
  for (const [q, want] of cases) { const r = ask(q); ok(r.intent === want, `意図 "${q.split("\n")[0]}" → ${want}`, r.intent); }
  ok(ask("計算 zeta(2)").text.includes("1.644934067"), "計算の結果が回答に入る");
  ok(ask("```bada\nprint(1 + 1)\n```").text.includes("2"), "送られた Bada コードを実行");
  ok(/未解決/.test(ask("リーマン予想は証明されたの?").text), "未解決問題を解決済みと言わない");
  ok(/含まれていません/.test(ask("あなたは誰?").text), "本物の Claude/ChatGPT の重みが無いことを正直に述べる");
  const r = ask("ゼータ関数とベータ関数の関係は?");
  ok(r.trace.length === 6 && r.sources.length > 0, "6 段のパイプラインと出典を返す");
  ok(/出典/.test(r.text) && /β/.test(r.text), "根拠つき応答 (論文チャンク + 方程式)");
  mode = "llm";
  const L = ask("ゼータ関数とベータ関数の関係は?");
  ok(L.mode === "llm" && L.system.includes("<bada_context>") && L.system.includes("<document") && L.system.includes("<equation"), "Claude API モード: Bada が文脈を組み立てる");
  const C2 = ask("計算 beta(0.5, 0.5)");
  ok(C2.system.includes("<tool_result tool=\"calc\">") && C2.system.includes("3.141592654"), "Claude API モード: 道具の結果を文脈に渡す");
  const before = I.Omega.items.length;
  I.call(I.global.get("after_llm"), ["reply", "end_turn"]);
  ok(I.Omega.items.length === before + 1, "Claude の応答も台帳に記録");
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
