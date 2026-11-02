/*
 * test.js — Bada PatchGuard のテスト (Node で実行、依存なし)
 *
 *   node bada_patchguard/tools/test.js
 *
 *   1. 差分・パッチ: Myers 差分 → 適用 → 逆パッチが元に戻る (無作為 3000 組)、unified 往復、SHA-256
 *   2. PHP 解析: 汚染の伝播・無害化・キャスト・heredoc・メソッド・include・関数定義・認可・構文
 *   3. @reviser: sink / sanitizer / invariant が文法として追加され、台帳に commit される
 *   4. 門: 危険な書き換え → REJECT、安全な書き換え → ACCEPT、期待した不変量だけが出る
 *   5. 折り畳み: 段のパッチを順に当てると最終版、相殺の検出、壊れた連鎖の検出
 *   6. 部分パッチ: 保留ファイルに依存するファイルも連鎖的に保留
 *   7. タプル空間: append-only (凍結)・rd の STAR 照会・免除の記録
 *   8. CLI: apply / rollback (全か無か・SHA-256 照合・REJECT 拒否・ドリフト検出・--strip・パス脱出の拒否)
 *   9. 配布物: index.html が src から組み立てられ、単一ファイル CLI が同じ判定を返す
 */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const cp = require("child_process");

const ROOT = path.join(__dirname, "..");
const Engine = require(path.join(ROOT, "..", "bada_claude", "src", "engine.js"));
const PHP = require(path.join(ROOT, "src", "php.js"));
const Diff = require(path.join(ROOT, "src", "diff.js"));
const Core = require(path.join(ROOT, "src", "core.js"));
const guardSrc = fs.readFileSync(path.join(ROOT, "src", "guard.bada"), "utf8");
const mk = () => Core.create({ Engine, PHP, Diff, guardSrc });

let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  → " + (typeof extra === "string" ? extra : JSON.stringify(extra)) : "")); }
}
function readTree(dir) {
  const out = {};
  (function walk(d, rel) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.isDirectory()) { if (e.name !== ".patchguard") walk(path.join(d, e.name), rel + e.name + "/"); } else out[rel + e.name] = fs.readFileSync(path.join(d, e.name), "utf8"); } })(dir, "");
  return out;
}
const EX = n => readTree(path.join(ROOT, "examples", n));
const ids = fs_ => Array.from(new Set(fs_.map(f => f.id))).sort();

console.log("1. 差分・パッチ");
{
  let seed = 7; const r = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  const gen = () => { const n = Math.floor(r() * 16); const L = []; for (let i = 0; i < n; i++) L.push("<?php $x" + Math.floor(r() * 5) + ";"); let s = L.join("\n"); if (n && r() < 0.6) s += "\n"; return s; };
  let bad = 0;
  for (let t = 0; t < 3000; t++) {
    const a = gen(), b = gen(); const d = Diff.diffLines(a, b);
    const f = Diff.applyHunks(a, d.hunks), v = Diff.applyHunks(b, Diff.reverseHunks(d.hunks));
    const u = Diff.parseUnified(Diff.unified("x.php", d, {})); const w = Diff.applyHunks(a, u.length ? u[0].hunks : []);
    if (!f.ok || f.text !== b || !v.ok || v.text !== a || !w.ok || w.text !== b) bad++;
  }
  ok(bad === 0, "適用・逆適用・unified 往復が無作為 3000 組で一致", bad);
  const d = Diff.diffLines("a\nb\nc\n", "a\nB\nc\n");
  ok(!Diff.applyHunks("a\nX\nc\n", d.hunks).ok, "文脈が土台と違えば適用を拒否 (ずれた土台に当てない)");
  ok(Diff.applyHunks("a\nb\nc", Diff.diffLines("a\nb\nc", "a\nb\nc\n").hunks).text === "a\nb\nc\n", "末尾改行の追加も差分になる");
  ok(Diff.sha256("abc") === "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA-256 (abc)");
  ok(Diff.sha256("書き換え") === require("crypto").createHash("sha256").update("書き換え").digest("hex"), "SHA-256 (UTF-8)");
}

console.log("2. PHP 解析");
{
  const A = s => PHP.analyzePhp(s, ["htmlspecialchars", "intval", "->quote"]);
  let a = A("<?php\n$q = $_GET['q'];\n$r = $q . 'x';\necho $r;\necho htmlspecialchars($r);\necho (int)$q;\n");
  ok(a.echoes[0].tainted && !a.echoes[1].tainted && a.echoes[1].sanitized && !a.echoes[2].tainted, "汚染の伝播 / 無害化 / (int) キャスト");
  a = A("<?php\n$id = intval($_GET['id']);\n$db->query(\"SELECT * FROM t WHERE id = $id\");\n$db->query(\"SELECT * FROM t WHERE n = {$_POST['n']}\");\n");
  ok(!a.calls.find(c => c.lname === "->query" && c.line === 3).tainted && a.calls.find(c => c.lname === "->query" && c.line === 4).tainted, "文字列への埋め込み ($id は無害、{$_POST} は汚染)");
  a = A("<?php\n$s = <<<SQL\nSELECT * FROM t WHERE a = '{$_GET['a']}'\nSQL;\n$db->query($s);\n");
  ok(a.calls.find(c => c.lname === "->query").tainted, "heredoc 経由の汚染");
  a = A("<?php\nforeach ($_POST as $k => $v) { system($v); }\n");
  ok(a.calls.find(c => c.lname === "system").tainted, "foreach で汚染が伝わる");
  a = A("<?php\n$x = $pdo->quote($_GET['x']);\n$pdo->query('SELECT ' . $x);\n");
  ok(!a.calls.find(c => c.lname === "->query").tainted, "メソッド形の無害化 (->quote)");
  a = A("<?php\ninclude $_GET['p'] . '.php';\nrequire_once __DIR__ . '/lib.php';\n");
  ok(a.includes[0].tainted && a.includes[0].dynamic && !a.includes[1].dynamic && a.includes[1].target === "/lib.php", "include の動的・汚染・対象");
  a = A("<?php\nclass A { private static function f(int $a, ?string $b = null, ...$r) {} }\nfunction g(&$x) {}\n");
  const f = a.defs.find(d => d.key === "a::f");
  ok(f && f.visibility === "private" && f.static && f.required === 1 && f.params.length === 3 && a.defs.find(d => d.key === "g").params[0].ref, "関数定義・可視性・必須引数・参照渡し", a.defs);
  a = A("<?php\nsession_start();\nif (empty($_SESSION['uid'])) { exit; }\ncsrf_check($_POST['t']);\n");
  ok(a.auth.length === 3, "認可・CSRF・セッション検査の抽出", a.auth.map(x => x.text));
  ok(!A("<?php\nfunction f() {\n  if (1) {\n}\n").syntax.balanced && A("<?php\nfunction f() { return [1, (2)]; }\n").syntax.balanced, "構文の均衡検査");
  ok(!A("<?php\n$s = 'abc;\n").syntax.balanced, "閉じていない文字列を検出");
  a = A("<html><?= $_GET['x'] ?></html>");
  ok(a.echoes[0].kind === "<?=" && a.echoes[0].tainted, "<?= の出力");
  a = A("<?php\n$o = `ls $dir`;\n$p = `cat {$_GET['f']}`;\n");
  ok(!a.calls[0].tainted && a.calls[1].tainted && a.calls[1].lname === "`backtick`", "バッククォートのシェル実行");
}

console.log("3. @reviser による文法拡張");
{
  const pg = mk(); const r = pg.rules();
  ok(r.grammar.join(",") === "sink,sanitizer,invariant", "reviser が sink / sanitizer / invariant を文法に追加", r.grammar);
  ok(r.checks.length === 17 && Object.keys(r.sinks).length > 50 && r.sanitizers.includes("htmlspecialchars"), `invariant ${r.checks.length} 件・sink ${Object.keys(r.sinks).length} 件・sanitizer ${r.sanitizers.length} 件`);
  ok(pg.interp.Omega.items.some(t => t[0] === "rule" && t[1] === "invariant") && pg.interp.Omega.items.some(t => t[0] === "@reviser" && t[2] === "commit"), "規則の追加は Omega 台帳に commit される");
  let threw = false; try { Core.create({ Engine, PHP, Diff, guardSrc: 'sink "eval", "code", "high", "high", "x"' }); } catch (e) { threw = true; }
  ok(threw, "reviser の前には sink 文は使えない (文法は reviser が commit して初めて存在する)");
  const extra = Core.create({ Engine, PHP, Diff, guardSrc: guardSrc + '\nsink "mb_send_mail", "cmd", "critical", "high", "テスト"\n' });
  const rep = extra.revise({ "a.php": "<?php\n" }, [{ "a.php": "<?php\nmb_send_mail('a', 'b', 'c');\n" }], []);
  ok(rep.decision === "REJECT" && rep.active[0].id === "PG02", "利用者が追加した sink 規則がそのまま効く");
}

console.log("4. 門 (gate)");
{
  const pg = mk();
  const risky = pg.revise(EX("base"), [EX("after_risky")], []);
  ok(risky.decision === "REJECT", "危険な書き換え → REJECT");
  const want = ["PG02", "PG03", "PG04", "PG05", "PG06", "PG09", "PG10", "PG11", "PG12", "PG17"];
  ok(JSON.stringify(ids(risky.active)) === JSON.stringify(want), "検出: " + want.join(" "), ids(risky.active));
  const byId = id => risky.active.filter(f => f.id === id);
  ok(byId("PG11").some(f => f.sev === "high" && f.evidence.includes("pages/profile.php:2")), "署名変更で壊れる呼び出し元 (pages/profile.php:2) を特定");
  ok(byId("PG03")[0].sev === "critical" && byId("PG05")[0].sev === "critical" && byId("PG02")[0].sev === "critical", "SQLi / LFI / コマンド注入は致命的");
  ok(Object.keys(risky.held).length === risky.net.files.length, "危険なファイルはすべて保留");
  const safe = pg.revise(EX("base"), [EX("after_safe")], []);
  ok(safe.decision === "ACCEPT" && safe.active.every(f => pg.sevRank(f.sev) <= 1), "安全な書き換え → ACCEPT (低の指摘のみ)", safe.active);
  const same = pg.revise(EX("base"), [EX("base")], []);
  ok(same.decision === "ACCEPT" && same.net.files.length === 0, "変更なし → ACCEPT");
  const del = pg.revise(EX("base"), [Object.fromEntries(Object.entries(EX("base")).filter(([p]) => p !== "lib/auth.php"))], []);
  ok(del.active.some(f => f.id === "PG16" && f.sev === "critical"), "まだ require されているファイルの削除 → 致命的 (PG16)");
  const broken = pg.revise({ "a.php": "<?php\nfunction f() { return 1; }\n" }, [{ "a.php": "<?php\nfunction f() { return 1;\n" }], []);
  ok(broken.active.some(f => f.id === "PG14"), "構文を壊す書き換え → PG14");
  const moved = pg.revise({ "a.php": "<?php\nfunction f() {}\n", "b.php": "<?php\nf();\n" }, [{ "a.php": "<?php\n", "c.php": "<?php\nfunction f() {}\n", "b.php": "<?php\nf();\n" }], []);
  ok(!moved.active.some(f => f.id === "PG11" && f.sev === "critical"), "関数を別ファイルへ移しただけなら削除扱いしない");
  const taintShift = pg.revise({ "a.php": "<?php\n$b = 'x';\necho $b;\n" }, [{ "a.php": "<?php\n$b = $_GET['q'];\necho $b;\n" }], []);
  ok(taintShift.active.some(f => f.id === "PG04"), "既存の echo が書き換えで汚染される副作用も検出");
}

console.log("5. 折り畳み (fold)");
{
  const pg = mk();
  const rep = pg.revise(EX("base"), [EX("fold_step1"), EX("fold_step2")], []);
  ok(rep.steps.length === 2 && rep.fold.ok, "2 段のパッチを基へ順に当てると最終版に一致");
  ok(rep.decision === "ACCEPT", "正味 (base → final) は ACCEPT");
  ok(rep.cancelled.some(f => f.id === "PG04" && f.step === 1), "段 1 の XSS は段 2 で相殺されたと報告");
  ok(rep.steps[0].findings.some(f => f.id === "PG04"), "各段の検査も残る (監査用)");
  const net = pg.revise(EX("base"), [EX("fold_step2")], []);
  ok(JSON.stringify(net.net.files.map(f => f.sha_b)) === JSON.stringify(rep.net.files.map(f => f.sha_b)), "折り畳んだ正味パッチ = 基から最終版への直接のパッチ");
  const tri = pg.revise({ "a.php": "<?php\necho 1;\n" }, [{ "a.php": "<?php\necho 2;\n" }, { "a.php": "<?php\necho 3;\n" }, { "a.php": "<?php\necho 1;\n" }], []);
  ok(tri.fold.ok && tri.net.files.length === 0, "戻ってくる書き換えは正味ゼロに畳まれる");
}

console.log("6. 安全な部分パッチ");
{
  const pg = mk();
  const base = { "lib.php": "<?php\nfunction f() { return 1; }\n", "page.php": "<?php\necho f();\n", "about.php": "<?php\necho 'about';\n" };
  const after = {
    "lib.php": "<?php\nfunction f() { return 1; }\nfunction g() { eval($_GET['code']); }\n",
    "page.php": "<?php\necho f();\ng();\n",
    "about.php": "<?php\necho 'about us';\n"
  };
  const rep = pg.revise(base, [after], []);
  ok(rep.held["lib.php"] && rep.held["page.php"] && rep.held["page.php"].startsWith("依存") && !rep.held["about.php"], "保留した lib.php の新関数 g() を使う page.php も連鎖的に保留", rep.held);
  const sp = pg.patchText(rep, true);
  ok(sp.includes("about.php") && !sp.includes("lib.php") && !sp.includes("page.php"), "safe.patch は about.php だけ");
  const rb = Diff.parseUnified(pg.rollbackText(rep));
  ok(rb.every(f => Diff.applyHunks(after[f.path], f.hunks).text === base[f.path]), "rollback.patch で書き換えの基へ戻る");
}

console.log("7. タプル空間");
{
  const pg = mk();
  pg.revise(EX("base"), [EX("after_risky")], [{ id: "PG12", path: "config.php", reason: "検証環境" }]);
  const T = pg.tuples();
  ok(T.length > 0 && T.every(t => Object.isFrozen(t)), "すべてのタプルは凍結 (append-only)");
  const rd = pg.interp.call(pg.interp.global.get("rd"), [["verdict", pg.interp.global.get("STAR"), pg.interp.global.get("STAR"), pg.interp.global.get("STAR"), pg.interp.global.get("STAR")]]);
  ok(rd.length === 1 && rd[0][2] === "REJECT", "rd([\"verdict\", *, *, *, *]) で照会");
  ok(T.some(t => t[0] === "waiver" && t[2] === "PG12" && t[4] === "検証環境"), "免除は理由ごとタプルに記録");
  ok(T.filter(t => t[0] === "blob").every(t => /^[0-9a-f]{64}$/.test(t[1])), "内容は SHA-256 で内容アドレス化");
  const before = T.length; pg.revise(EX("base"), [EX("after_safe")], []);
  ok(pg.tuples().length > before && pg.tuples()[0] === T[0], "2 回目の検査は追記されるだけ (前の記録は不変)");
}

console.log("8. CLI");
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "pgtest-"));
  const cli = path.join(ROOT, "cli.js");
  const run = (args) => { const r = cp.spawnSync(process.execPath, [cli, ...args], { encoding: "utf8" }); return { code: r.status, out: r.stdout + r.stderr }; };
  const copy = (src, dst) => { fs.cpSync(src, dst, { recursive: true }); return dst; };
  const ex = n => path.join(ROOT, "examples", n);
  let r = run(["check", ex("base"), ex("after_risky"), "--quiet"]);
  ok(r.code === 2, "check 危険 → 終了コード 2", r.code);
  r = run(["check", ex("base"), ex("after_safe"), "--quiet", "--out", path.join(tmp, "safe")]);
  ok(r.code === 0 && fs.existsSync(path.join(tmp, "safe", "net.patch")), "check 安全 → 0 と書き出し");
  run(["check", ex("base"), ex("after_risky"), "--quiet", "--out", path.join(tmp, "risky")]);
  const site = copy(ex("base"), path.join(tmp, "site"));
  r = run(["apply", site, path.join(tmp, "risky", "net.patch"), "--quiet"]);
  ok(r.code === 2 && JSON.stringify(readTree(site)) === JSON.stringify(EX("base")), "apply: REJECT のパッチは当てない (サイトは不変)");
  r = run(["apply", site, path.join(tmp, "safe", "net.patch"), "--quiet"]);
  ok(r.code === 0 && JSON.stringify(readTree(site)) === JSON.stringify(EX("after_safe")), "apply: 安全なパッチを当てると書き換えた後と一致");
  const led = fs.readFileSync(path.join(site, ".patchguard", "tuples.jsonl"), "utf8").trim().split("\n").map(JSON.parse);
  ok(led.length === 4 && led.every(t => t[0] === "applied" && t[5] === "ACCEPT"), "apply の記録 (tuples.jsonl に追記)");
  ok(led.filter(t => t[3] !== "-").every(t => fs.existsSync(path.join(site, ".patchguard", "backup", t[3]))), "書き換え前の内容を SHA-256 名でバックアップ");
  r = run(["apply", site, path.join(tmp, "safe", "net.patch"), "--quiet"]);
  ok(r.code === 3 && /一致しません|存在します/.test(r.out), "同じパッチの二重適用は拒否");
  r = run(["rollback", site, path.join(tmp, "safe", "net.patch"), "--quiet"]);
  ok(r.code === 0 && JSON.stringify(readTree(site)) === JSON.stringify(EX("base")), "rollback で書き換えの基へ戻る");
  fs.appendFileSync(path.join(site, "lib", "db.php"), "// 誰かが本番で直接編集\n");
  const snap = JSON.stringify(readTree(site));
  r = run(["apply", site, path.join(tmp, "safe", "net.patch"), "--quiet"]);
  ok(r.code === 3 && r.out.includes("SHA-256") && JSON.stringify(readTree(site)) === snap, "基がずれていたら 1 ファイルも書き換えない (全か無か)");
  const site2 = copy(ex("base"), path.join(tmp, "site2"));
  const gp = path.join(tmp, "git.patch");
  const g = cp.spawnSync("git", ["diff", "--no-index", "base", "after_safe"], { cwd: path.join(ROOT, "examples"), encoding: "utf8" });
  if (g.status === 1) {
    fs.writeFileSync(gp, g.stdout);
    r = run(["apply", site2, gp, "--quiet", "--strip", "1"]);
    ok(r.code === 0 && JSON.stringify(readTree(site2)) === JSON.stringify(EX("after_safe")), "git diff 形式のパッチ (--strip 1) も当てられる");
  } else ok(true, "git が無いので git diff 形式の検査は省略");
  fs.writeFileSync(path.join(tmp, "evil.patch"), "--- a/../evil.php\n+++ b/../evil.php\n@@ -0,0 +1 @@\n+<?php system($_GET['c']);\n");
  r = run(["apply", site2, path.join(tmp, "evil.patch"), "--quiet"]);
  ok(r.code === 3 && !fs.existsSync(path.join(tmp, "evil.php")), "サイトの外を指すパスは拒否");
  const pt = cp.spawnSync("patch", ["--version"]);
  if (pt.status === 0) {
    const site3 = copy(ex("base"), path.join(tmp, "site3"));
    const p = cp.spawnSync("patch", ["-p1", "-s", "-i", path.join(tmp, "safe", "net.patch")], { cwd: site3 });
    ok(p.status === 0 && JSON.stringify(readTree(site3)) === JSON.stringify(EX("after_safe")), "GNU patch でも同じ結果 (互換)");
  } else ok(true, "patch コマンドが無いので互換検査は省略");
  r = run(["check", ex("base"), ex("after_risky"), "--quiet", "--fail-on", "medium", "--waivers", path.join(tmp, "nope.json")]);
  ok(r.code === 3, "存在しない waivers ファイルは使い方の誤り");
  fs.rmSync(tmp, { recursive: true, force: true });
}

console.log("9. 配布物");
{
  const b = cp.spawnSync(process.execPath, [path.join(__dirname, "build.js"), "--check"], { encoding: "utf8" });
  ok(b.status === 0, "index.html は src から組み立てた最新版", b.stderr);
  const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
  ok(html.includes('id="guard-src"') && html.includes("@reviser PATCHGUARD"), "index.html に guard.bada を同梱");
  const dist = path.join(ROOT, "dist", "badapatchguard.js");
  if (fs.existsSync(dist)) {
    const r = cp.spawnSync(process.execPath, [dist, "check", path.join(ROOT, "examples", "base"), path.join(ROOT, "examples", "after_risky"), "--quiet"]);
    ok(r.status === 2, "単一ファイル CLI (dist/badapatchguard.js) も REJECT を返す");
  } else ok(true, "dist/badapatchguard.js は未生成 (node tools/build.js で生成)");
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
