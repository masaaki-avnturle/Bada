/*
 * codegen-test.js — 生成した「厳密化されたソースコード」を、実際に各言語の処理系で
 * コンパイル・実行して確かめる。処理系が無い言語は skip と表示する (失敗にはしない)。
 *   node bada_claude/tools/codegen-test.js
 */
"use strict";
const fs = require("fs"), os = require("os"), path = require("path"), { spawnSync } = require("child_process");
const Lab = require("../src/lab.js"), Engine = require("../src/engine.js");

const MODES = { python: "bigint", javascript: "bigint", ruby: "bigint", java: "bigint", go: "bigint", rust: "checked128", c: "checked64", bada: "bound53" };
const CLAIMS = ["Σ k = n(n+1)/2", "Σ k^2 = n(n+1)(2n+1)/6", "Σ k^3 = (n(n+1)/2)^2", "Σ (2k-1) = n^2",
                "Σ k^2 = n(n+1)(2n+1)/5" /* 誤り → 修正して生成 */, "Σ k^7 = n^8/8", "Σ (k^2 - 3k + 5) = n^3"];
const has = c => spawnSync("sh", ["-c", "command -v " + c]).status === 0;
const sh = (cmd, args, cwd) => { const r = spawnSync(cmd, args, { cwd, encoding: "utf8", timeout: 120000 }); return { ok: r.status === 0, out: (r.stdout || "").trim(), err: (r.stderr || "").trim() }; };
const RUN = {
  python: d => has("python3") && sh("python3", ["rigor_sum.py"], d),
  javascript: d => sh("node", ["rigor_sum.js"], d),
  ruby: d => has("ruby") && sh("ruby", ["rigor_sum.rb"], d),
  java: d => has("javac") && (c => c.ok ? sh("java", ["-cp", ".", "RigorSum"], d) : c)(sh("javac", ["-encoding", "UTF-8", "RigorSum.java"], d)),
  go: d => has("go") && sh("go", ["run", "rigor_sum.go"], d),
  rust: d => has("rustc") && (c => c.ok ? sh("./rigor_sum", [], d) : c)(sh("rustc", ["-O", "-D", "warnings", "-o", "rigor_sum", "rigor_sum.rs"], d)),
  c: d => has("gcc") && (c => c.ok ? sh("./rigor_sum", [], d) : c)(sh("gcc", ["-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-o", "rigor_sum", "rigor_sum.c"], d)),
  bada: (d, code) => { const I = new Engine.Interp({ maxSteps: 4e8 }); try { I.run(code); return { ok: true, out: I.out.join("\n").trim(), err: "" }; } catch (e) { return { ok: false, out: "", err: e.message }; } }
};

let pass = 0, fail = 0, skip = 0;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "rigor-"));
CLAIMS.forEach((claim, ci) => {
  const spec = Lab.makeSpec(claim);
  if (!spec.ok || spec.status !== "proved") { fail++; console.log("  ✗ spec: " + claim); return; }
  for (const lang of Object.keys(MODES)) {
    const e = Lab.emit(spec, lang, { overflow: MODES[lang], selftest: 200 });
    const tag = `${lang.padEnd(10)} ${claim}`;
    if (!e.ok) { fail++; console.log("  ✗ emit " + tag + " → " + e.error); continue; }
    const dir = path.join(tmp, ci + "-" + lang); fs.mkdirSync(dir);
    fs.writeFileSync(path.join(dir, e.file), e.code);
    const r = RUN[lang](dir, e.code);
    if (r === false) { skip++; console.log("  - skip " + tag + " (処理系なし)"); continue; }
    if (r.ok && r.out === e.expected) { pass++; console.log("  ✓ " + tag + " → " + r.out + (e.nmax !== null ? `  (n ≤ ${e.nmax} で厳密)` : "")); }
    else { fail++; console.log("  ✗ " + tag + " → got " + JSON.stringify(r.out) + " want " + JSON.stringify(e.expected) + " " + r.err.slice(0, 300)); }
  }
});
/* 仕様が証明済みでなければ生成しない */
const refuse = [Lab.emit({ ok: true, status: "open" }, "python", {}), Lab.emit(Lab.makeSpec("Σ k/2 = n(n+1)/4"), "c", { overflow: "checked64" }), Lab.emit(Lab.makeSpec("Σ k = n(n+1)/2"), "cobol", {})];
refuse.forEach((e, i) => { if (!e.ok) { pass++; console.log("  ✓ 生成を拒否 #" + i + ": " + e.error); } else { fail++; console.log("  ✗ 拒否すべき生成 #" + i); } });
fs.rmSync(tmp, { recursive: true, force: true });
console.log(`\n${pass} passed, ${fail} failed, ${skip} skipped`);
process.exit(fail ? 1 : 0);
