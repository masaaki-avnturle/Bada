/*
 * engine-test.js — BadaGPT のエンジン・対話層・配布 HTML の単体テスト
 *   node bada_gpt/tools/engine-test.js
 */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const E = require("../src/engine.js"), C = require("../src/chat.js");
let pass = 0, fail = 0;
function ok(name, cond) { if (cond) pass++; else { fail++; console.error("NG: " + name); } }
const near = (a, b, eps) => Math.abs(a - b) < (eps || 1e-9);
const clone = o => JSON.parse(JSON.stringify(o));

/* 1. ζ・L 関数 */
ok("zeta(2)", near(E.zeta(2, 0)[0], Math.PI ** 2 / 6, 1e-12));
ok("zeta(1/2)", near(E.zeta(0.5, 0)[0], -1.4603545088095868, 1e-11));
ok("zeta(-1)", near(E.zeta(-1, 0)[0], -1 / 12, 1e-12));
ok("first zero", Math.hypot(...E.zeta(0.5, 14.134725141734693)) < 1e-12);
ok("L(3,chi_-4)", near(E.dirichletL(3, 0, E.CHARACTERS["chi_-4"])[0], Math.PI ** 3 / 32, 1e-12));
ok("L(2,chi_-4) = Catalan", near(E.dirichletL(2, 0, E.CHARACTERS["chi_-4"])[0], 0.915965594177219, 1e-12));
ok("|Z| = |zeta|", near(Math.abs(E.hardyZ(20)), Math.hypot(...E.zeta(0.5, 20)), 1e-12));

/* 2. 高さ T までの RH・Schoenfeld */
const rh = E.verifyRH(100, 3);
ok("N(100) = 29", rh.zeros_in_strip_argument_principle === 29 && rh.zeros_on_critical_line_sign_changes === 29);
ok("RH(100) verified", rh.status === "verified");
ok("zeros", near(rh.first_zeros[0], 14.134725142, 1e-8) && near(rh.first_zeros[2], 25.01085758, 1e-8));
ok("N(500) = 269", E.zeroCount(500)[0] === 269);
const sch = E.schoenfeld(1e5);
ok("schoenfeld", sch.status === "verified" && sch.max_ratio < 1 && sch.max_ratio_at === 96);

/* 3. 深リーマン予想の証拠 */
const d = E.drhEvidence("chi_-4", 0, 1e5), last = d.table[d.table.length - 1];
ok("drh stays open", d.status === "open" && d.sqrt2_factor);
ok("drh sqrt2", last.rel_error_vs_DRH_limit < 0.1 && last.rel_error_vs_plain_L > 0.3);
ok("drh complex char has no sqrt2", !E.drhEvidence("chi_5_complex", 0, 1e3).sqrt2_factor);

/* 4. 擬似量子コンピュータ */
const marked = new Array(256).fill(false); marked[173] = true;
const g = E.groverSearch(marked, 0);
ok("grover", g.success_probability > 0.99 && g.measured === 173 && g.iterations === 12);
ok("false statement disproved (sparse)", E.quantumSearch("euler_polynomial", 6, 0).status === "disproved");
ok("false statement disproved (dense)", E.quantumSearch("euler_polynomial", 10, 0).status === "disproved");
ok("counterexample is real", E.isCounterexample("euler_polynomial", E.quantumSearch("euler_polynomial", 6, 0).counterexample));
for (const p of ["riemann_lagarias", "goldbach", "collatz", "legendre"]) {
  const q = E.quantumSearch(p, 8, 0);
  ok(p + " stays open", q.status === "open" && q.bounded_status === "verified" && q.marked === 0);
}

/* 5. 帰納法・修正・補集合 */
ok("sum k", E.proveSum([0, 1], [0, "1/2", "1/2"]).status === "proved");
const bad = E.proveSum([0, 1], [0, "1/2", "1/3"]);
ok("wrong sum disproved", bad.status === "disproved" && bad.counterexample === 1);
ok("late counterexample", E.proveSum([0, 1], [0, 1]).counterexample === 2);
const rep = E.repairSum([0, 0, 1], [0, "1/5", "3/5", "2/5"]);
ok("repair", rep.status === "proved" && rep.repaired.g.join() === "0,1/6,1/2,1/3" && rep.drift_after === "0");
ok("parse", E.proveSum(E.pParse("k^3"), E.pParse("(n(n+1)/2)^2")).status === "proved");
ok("parse odd sum", E.proveSum(E.pParse("2k-1"), E.pParse("n²")).status === "proved");
ok("collatz survivors (A076227)", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(k => E.collatzDescent(k).survivor_count).join() === "1,1,2,3,4,8,13,19,38,64");
const cd = E.collatzDescent(10);
ok("collatz lemma proved, conjecture open", cd.status === "proved" && cd.conjecture_status === "open");

/* 6. SHA-256 / Jones 暗号 (Python 版 jones_quantum_crypto と同じ鍵) */
ok("sha256", E.hex(E.sha256("abc")) === "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
ok("sha256 long", E.hex(E.sha256("a".repeat(1000))) === require("crypto").createHash("sha256").update("a".repeat(1000)).digest("hex"));
ok("hmac", E.hex(E.hmac(new TextEncoder().encode("key"), new TextEncoder().encode("msg"))) ===
   require("crypto").createHmac("sha256", "key").update("msg").digest("hex"));
ok("trefoil", E.jonesStr([1, 1, 1]) === "+1*t^1 +1*t^3 -1*t^4");
ok("figure-eight", E.jonesStr([1, -2, 1, -2]) === "+1*t^-2 -1*t^-1 +1*t^0 -1*t^1 +1*t^2");
ok("key matches python", E.fingerprint(E.braidKey([1, 1, 1])) === "0661037b539b7507");

/* 7. 証明書・封印・PatchGuard */
const cert = E.fullCertificate({ height: 50, limit: 1e4, qubits: 6, sieveBits: 8 });
ok("verdicts open", cert.verdicts.riemann_hypothesis === "open" && cert.verdicts.deep_riemann_hypothesis === "open");
ok("seal ok", E.checkSeal(cert));
ok("wrong braid", !E.checkSeal(cert, [1, 1]));
ok("honest accepted", E.guard([cert], true).verdict === "ACCEPT");
const tampered = clone(cert); tampered.verdicts.riemann_hypothesis = "proved";
ok("tamper breaks seal", !E.checkSeal(tampered));
function rejects(name, id, mutate, recompute) {
  const c = clone(cert); mutate(c);
  const r = E.guard([cert, E.seal(c)], recompute);
  ok(name, r.verdict === "REJECT" && r.findings.some(f => f.id === id));
}
rejects("RG01 proof claim", "RG01", c => { c.verdicts.deep_riemann_hypothesis = "proved"; });
rejects("RG03 forged zero count", "RG03", c => { c.rh_bounded.zeros_in_strip_argument_principle++; c.rh_bounded.zeros_on_critical_line_sign_changes++; }, true);
rejects("RG05 drh proved", "RG05", c => { c.drh_evidence[0].status = "proved"; });
rejects("RG06 soundness removed", "RG06", c => { c.soundness = ""; });
rejects("RG10 quantum proof", "RG10", c => { c.quantum_search[0].status = "proved"; });
rejects("RG10 fake counterexample", "RG10", c => { c.quantum_search[1].status = "disproved"; c.quantum_search[1].counterexample = 10; });
rejects("RG11 collatz proved", "RG11", c => { c.induction[3].conjecture_status = "proved"; });
rejects("RG11 wrong formula", "RG11", c => { c.induction[0].g = ["0", "1", "1"]; });
const small = E.fullCertificate({ height: 30, limit: 1e4, qubits: 6, sieveBits: 8 });
ok("shrink needs review", E.guard([cert, small]).verdict === "REVIEW");
const mid = clone(cert); mid.drh_evidence[0].status = "proved";
const folded = E.guard([cert, mid, cert]);
ok("fold cancels", folded.verdict === "ACCEPT" && folded.cancelled.length > 0 && Object.keys(folded.net_patch).length === 0);

/* 8. 対話層 */
const intents = { "リーマン予想を証明して": "rh", "深リーマン予想は？": "drh", "Σ k^2 = n(n+1)(2n+1)/6": "induct",
  "コラッツ予想": "collatz", "ゴールドバッハ予想": "goldbach", "証明書を作って": "certificate",
  "証明書を検査して": "guard", "ζ(2)": "zeta", "反例を探して": "quantum", "こんにちは": "help" };
for (const t in intents) ok("intent " + t, C.detect(t) === intents[t]);
const st = {};
const r1 = C.reply("リーマン予想を高さ 60 まで証明して", st).lines.join("\n");
ok("chat never claims RH", /【リーマン予想】 判定: \? 未解決/.test(r1) && !/リーマン予想】 判定: ∎/.test(r1));
ok("chat drh open", /【深リーマン予想】 判定: \? 未解決/.test(C.reply("深リーマン予想を証明して", st).lines.join("\n")));
const r2 = C.reply("Σ k^2 = n(n+1)(2n+1)/5", st).lines.join("\n");
ok("chat repairs", /反証/.test(r2) && /\(1\/3\)·n\^3 \+ \(1\/2\)·n\^2 \+ \(1\/6\)·n/.test(r2) && /証明完了/.test(r2));
ok("chat subscript", /証明完了/.test(C.reply("帰納法で Σ_(k=1..n) (2k-1) = n^2 を証明して", st).lines.join("\n")));
ok("chat bad input", /処理できませんでした/.test(C.reply("Σ k = n^2/0", st).lines[0]));
ok("guard needs cert", /先に/.test(C.reply("証明書を検査して", {}).lines[0]));
C.reply("証明書を作って", st);
ok("chat cert", st.cert && E.checkSeal(st.cert));
ok("chat guard accept", /判定: ACCEPT/.test(C.reply("証明書を検査して", st).lines.join("\n")));
st.base = clone(st.cert); st.cert = clone(st.cert); st.cert.verdicts.riemann_hypothesis = "proved";
ok("chat guard reject", /判定: REJECT/.test(C.reply("証明書を検査して", st).lines.join("\n")));

/* 9. 配布 HTML: 最新で、インライン JS が単体で動く */
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const built = fs.readFileSync(path.join(__dirname, "..", "src", "ui.html"), "utf8")
  .replace("/*__ENGINE__*/", () => fs.readFileSync(path.join(__dirname, "..", "src", "engine.js"), "utf8"))
  .replace("/*__CHAT__*/", () => fs.readFileSync(path.join(__dirname, "..", "src", "chat.js"), "utf8"));
ok("index.html up to date", html === built);
ok("no external resources", !/(src|href)\s*=\s*["']https?:/.test(html));
const script = html.match(/<script>([\s\S]*)<\/script>/)[1];
const els = {};
const el = () => ({ addEventListener() {}, appendChild() {}, remove() {}, set textContent(v) {}, className: "", style: {}, files: [] });
const sandbox = { TextEncoder, console, setTimeout, URL, Blob: function () {},
  document: { getElementById: id => (els[id] = els[id] || el()), createElement: el, body: el() } };
sandbox.window = sandbox;
try { vm.runInNewContext(script, sandbox); ok("inline script runs", !!sandbox.BadaGPTEngine && !!sandbox.BadaGPTChat); }
catch (e) { ok("inline script runs: " + e.message, false); }

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
