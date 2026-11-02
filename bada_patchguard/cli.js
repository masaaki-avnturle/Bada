#!/usr/bin/env node
/*
 * cli.js — Bada Reviser PatchGuard のコマンドライン版 (Node 18+、依存なし)
 *
 *   node cli.js check <基のディレクトリ> <後のディレクトリ> [<後2> ...] [--out DIR] [--waivers FILE] [--fail-on LEVEL]
 *       書き換えの基と後 (複数なら時系列で折り畳む) を検査し、判定を表示する。
 *       --out を付けると report.json / net.patch / safe.patch / rollback.patch / tuples.jsonl を書き出す。
 *       終了コード: 0 = ACCEPT, 1 = REVIEW (--fail-on medium のとき), 2 = REJECT, 3 = 使い方の誤り
 *
 *   node cli.js apply <サイトのディレクトリ> <パッチ> [--dry-run] [--force] [--waivers FILE] [--strip N]
 *       パッチをサイトに当てる前に、当てた後の木を Bada の門で検査する (REJECT なら当てない)。
 *       各ファイルの基 SHA-256 が一致しなければ 1 つも書き換えない (全か無か)。
 *       書き換え前の内容は <サイト>/.patchguard/backup/<sha256> に、記録は
 *       <サイト>/.patchguard/tuples.jsonl (追記のみ) に残す。
 *       --strip N: パス先頭の N 階層を取り除く (a/ b/ は常に除去。git diff --no-index なら 1)
 *
 *   node cli.js rollback <サイトのディレクトリ> <パッチ> [--dry-run] [--strip N]
 *       同じパッチを逆向きに当てて、書き換えの基へ戻す (SHA-256 で照合)。
 *
 *   node cli.js rules
 *       @reviser で定義された規則 (sink / sanitizer / invariant) の一覧。
 */
"use strict";
const fs = require("fs");
const path = require("path");

function deps() {
  if (typeof __PG_BUNDLE__ !== "undefined") return __PG_BUNDLE__;   // dist の単一ファイル版
  const here = __dirname;
  const enginePath = fs.existsSync(path.join(here, "src", "engine.js")) ? path.join(here, "src", "engine.js") : path.join(here, "..", "bada_claude", "src", "engine.js");
  return {
    Engine: require(enginePath), PHP: require("./src/php.js"), Diff: require("./src/diff.js"), Core: require("./src/core.js"),
    guardSrc: fs.readFileSync(path.join(here, "src", "guard.bada"), "utf8")
  };
}

const USAGE = `Bada Reviser PatchGuard — PHP サイト書き換えの副作用ガード

  check <基> <後> [<後2> ...] [--out DIR] [--waivers FILE] [--fail-on LEVEL] [--json] [--quiet]
      書き換えの基と後 (複数なら時系列で折り畳む) を検査する。
      --out: report.json / net.patch / safe.patch / rollback.patch / tuples.jsonl を書き出す
      終了コード: 0 ACCEPT, 1 --fail-on 以上の指摘 (既定 high), 2 REJECT, 3 使い方の誤り
  apply <サイト> <パッチ> [--dry-run] [--force] [--waivers FILE] [--strip N]
      当てた後の木を Bada の門で検査し、REJECT なら当てない。基の SHA-256 が
      一致しなければ 1 ファイルも書き換えない (全か無か)。
  rollback <サイト> <パッチ> [--dry-run] [--strip N]
      同じパッチを逆向きに当てて書き換えの基へ戻す。
  rules
      @reviser で定義された規則の一覧。

  waivers の形式: [{"id": "PG12", "path": "config.php", "match": "任意", "reason": "理由"}]`;

const SKIP_DIRS = new Set([".git", ".svn", ".hg", "node_modules", ".patchguard", ".idea", ".vscode"]);
function readTree(dir) {
  const out = {}, skipped = [];
  (function walk(d, rel) {
    for (const ent of fs.readdirSync(d, { withFileTypes: true })) {
      if (ent.isDirectory()) { if (!SKIP_DIRS.has(ent.name)) walk(path.join(d, ent.name), rel + ent.name + "/"); continue; }
      if (!ent.isFile()) continue;
      const p = path.join(d, ent.name); const st = fs.statSync(p);
      if (st.size > 4 * 1024 * 1024) { skipped.push(rel + ent.name + " (4MB 超)"); continue; }
      const buf = fs.readFileSync(p);
      if (buf.includes(0)) { skipped.push(rel + ent.name + " (バイナリ)"); continue; }
      out[rel + ent.name] = buf.toString("utf8");
    }
  })(dir, "");
  return { files: out, skipped };
}

function parseArgs(argv) {
  const pos = [], opt = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const k = a.slice(2);
      if (["dry-run", "force", "json", "quiet"].includes(k)) opt[k] = true; else opt[k] = argv[++i];
    } else pos.push(a);
  }
  return { pos, opt };
}

const COLOR = process.stdout.isTTY && !process.env.NO_COLOR;
const c = (code, s) => COLOR ? `\x1b[${code}m${s}\x1b[0m` : s;
const SEVC = { critical: "1;31", high: "31", medium: "33", low: "36", info: "37" };
const SEVJ = { critical: "致命的", high: "高", medium: "中", low: "低", info: "情報" };
const DEC = { ACCEPT: c("1;32", "ACCEPT 受理"), REVIEW: c("1;33", "REVIEW 要確認"), REJECT: c("1;31", "REJECT 拒否") };

function printReport(rep) {
  const net = rep.net;
  console.log(c("1", `\nBada Reviser PatchGuard ${rep.version} — run #${rep.run}`));
  console.log(`変更ファイル ${net.files.length} 件  (+${net.files.reduce((s, f) => s + f.adds, 0)} / -${net.files.reduce((s, f) => s + f.dels, 0)} 行)`);
  if (rep.steps.length) console.log(`折り畳み: ${rep.steps.length} 段 → 正味 1 本  ${rep.fold.ok ? c("32", "✓ 各段のパッチを順に当てると最終版に一致") : c("31", "✗ " + rep.fold.problems.join("; "))}`);
  for (const f of net.files) {
    const fs_ = f.findings;
    const held = rep.held[f.path];
    console.log(`\n${c("1", f.path)}  [${f.status}] +${f.adds} -${f.dels}${held ? c("33", "  ⏸ 保留: " + held) : c("32", "  ✓ 安全パッチに含める")}`);
    for (const x of fs_) {
      const tag = c(SEVC[x.sev], `[${SEVJ[x.sev]}]`);
      console.log(`  ${tag} ${x.id} ${x.title}${x.line ? " (line " + x.line + ")" : ""}${x.waived ? c("2", "  — 免除: " + x.waived) : ""}`);
      console.log(`       ${x.msg}`);
      console.log(c("2", `       ${x.evidence}`));
    }
  }
  if (rep.cancelled.length) {
    console.log(c("1", "\n折り畳みで相殺された指摘 (途中の段にだけ存在):"));
    for (const x of rep.cancelled) console.log(`  段 ${x.step}: ${x.id} ${x.path}:${x.line} ${x.msg}`);
  }
  if (rep.emergent.length) {
    console.log(c("1", "\n合成で初めて現れた指摘 (どの段単独でも出ない):"));
    for (const x of rep.emergent) console.log(`  ${x.id} ${x.path}:${x.line} ${x.msg}`);
  }
  const cnt = Object.entries(rep.counts).map(([k, v]) => `${SEVJ[k]} ${v}`).join(" / ") || "なし";
  console.log(`\n指摘: ${cnt}   タプル: ${rep.tuples} 件`);
  console.log(`判定: ${DEC[rep.decision]}\n`);
}

function loadWaivers(file) {
  if (!file) return [];
  const w = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!Array.isArray(w)) throw new Error("waivers は配列の JSON です: [{\"id\": \"PG12\", \"path\": \"config.php\", \"reason\": \"…\"}]");
  for (const x of w) if (!x.id || !x.path || !x.reason) throw new Error("waiver には id / path / reason が必要です");
  return w;
}

function jsonl(tuples) { return tuples.map(t => JSON.stringify(t)).join("\n") + "\n"; }

function cmdCheck(pg, pos, opt) {
  if (pos.length < 2) throw new Error("check <基> <後> [<後2> ...]");
  const base = readTree(pos[0]);
  const revs = pos.slice(1).map(readTree);
  for (const s of [base, ...revs]) for (const k of s.skipped) console.error("skip: " + k);
  const rep = pg.revise(base.files, revs.map(r => r.files), loadWaivers(opt.waivers));
  if (opt.json) console.log(JSON.stringify(slim(rep), null, 2)); else if (!opt.quiet) printReport(rep);
  if (opt.out) {
    fs.mkdirSync(opt.out, { recursive: true });
    fs.writeFileSync(path.join(opt.out, "report.json"), JSON.stringify(slim(rep), null, 2));
    fs.writeFileSync(path.join(opt.out, "net.patch"), pg.patchText(rep, false));
    fs.writeFileSync(path.join(opt.out, "safe.patch"), pg.patchText(rep, true));
    fs.writeFileSync(path.join(opt.out, "rollback.patch"), pg.rollbackText(rep));
    fs.writeFileSync(path.join(opt.out, "tuples.jsonl"), jsonl(pg.tuples().filter(t => t[0] !== "blob" || true)));
    if (!opt.json) console.log(`書き出し: ${opt.out}/{report.json, net.patch, safe.patch, rollback.patch, tuples.jsonl}`);
  }
  const failOn = opt["fail-on"] || "high";
  const rank = pg.sevRank;
  const worst = rep.active.reduce((m, f) => Math.max(m, rank(f.sev)), -1);
  if (rep.decision === "REJECT" || worst >= rank(failOn)) return rep.decision === "REJECT" ? 2 : 1;
  return 0;
}
function slim(rep) {
  const strip = f => Object.assign({}, f);
  return {
    run: rep.run, version: rep.version, decision: rep.decision, counts: rep.counts, held: rep.held, tuples: rep.tuples,
    fold: rep.fold, steps: rep.steps.map(s => ({ step: s.step, files: s.files.map(f => ({ path: f.path, status: f.status, adds: f.adds, dels: f.dels })), findings: s.findings.map(strip) })),
    files: rep.net.files.map(f => ({ path: f.path, status: f.status, sha_base: f.sha_a, sha_after: f.sha_b, adds: f.adds, dels: f.dels, findings: f.findings.map(strip) })),
    cancelled: rep.cancelled.map(strip), emergent: rep.emergent.map(strip)
  };
}

/* パッチをサイトへ (全か無か)。reverse=true でロールバック */
function cmdApply(pg, D, pos, opt, reverse) {
  if (pos.length < 2) throw new Error((reverse ? "rollback" : "apply") + " <サイト> <パッチ>");
  const site = pos[0];
  const strip = opt.strip === undefined ? 0 : parseInt(opt.strip, 10);
  if (!(strip >= 0)) throw new Error("--strip は 0 以上の整数です");
  const patches = D.Diff.parseUnified(fs.readFileSync(pos[1], "utf8"));
  for (const p of patches) {
    const parts = p.path.split("/");
    if (parts.length <= strip) throw new Error(`${p.path}: --strip ${strip} では取り除けません`);
    p.path = parts.slice(strip).join("/");
    if (p.path.split("/").includes("..") || path.isAbsolute(p.path)) throw new Error(`${p.path}: サイトの外を指すパスは当てません`);
  }
  if (!patches.length) throw new Error("パッチにファイルがありません");
  const tree = readTree(site).files;
  const next = Object.assign({}, tree);
  const plan = [];
  for (const p of patches) {
    let hunks = p.hunks, wantBase = p.a_sha, wantAfter = p.b_sha, absentBase = p.a_absent, absentAfter = p.b_absent;
    if (reverse) { hunks = D.Diff.reverseHunks(hunks); [wantBase, wantAfter] = [wantAfter, wantBase]; [absentBase, absentAfter] = [absentAfter, absentBase]; }
    const cur = Object.prototype.hasOwnProperty.call(tree, p.path) ? tree[p.path] : null;
    if (absentBase && cur !== null) throw new Error(`${p.path}: 新規作成のはずが既に存在します`);
    if (!absentBase && cur === null) throw new Error(`${p.path}: 当てる先のファイルがありません`);
    if (wantBase && cur !== null && D.Diff.sha256(cur) !== wantBase) throw new Error(`${p.path}: 基の SHA-256 が一致しません (サイトが記録と違う版です。副作用を防ぐため中止)`);
    const r = D.Diff.applyHunks(cur || "", hunks);
    if (!r.ok) throw new Error(`${p.path}: ${r.error}`);
    if (!absentAfter && wantAfter && D.Diff.sha256(r.text) !== wantAfter) throw new Error(`${p.path}: 当てた結果の SHA-256 が記録と一致しません`);
    if (absentAfter) delete next[p.path]; else next[p.path] = r.text;
    plan.push({ path: p.path, before: cur, after: absentAfter ? null : r.text });
  }
  // 門: 当てた後の木を Bada で検査
  const rep = pg.revise(tree, [next], loadWaivers(opt.waivers));
  if (!opt.quiet) printReport(rep);
  if (!reverse && rep.decision === "REJECT" && !opt.force) { console.error(c("31", "REJECT のため当てませんでした (--force で上書き。理由は台帳に残ります)")); return 2; }
  if (opt["dry-run"]) { console.log("--dry-run: 書き込みは行いませんでした"); return 0; }
  const meta = path.join(site, ".patchguard"); fs.mkdirSync(path.join(meta, "backup"), { recursive: true });
  const ledger = path.join(meta, "tuples.jsonl");
  const stamp = new Date().toISOString();
  const lines = [];
  for (const s of plan) {
    if (s.before !== null) { const h = D.Diff.sha256(s.before); fs.writeFileSync(path.join(meta, "backup", h), s.before); }
  }
  // 一時ファイルに書いてから rename (途中で落ちても半端な書き込みを残さない)
  const tmp = [];
  try {
    for (const s of plan) {
      const dest = path.join(site, s.path);
      if (s.after === null) continue;
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      const t = dest + ".pg-tmp-" + process.pid; fs.writeFileSync(t, s.after); tmp.push([t, dest]);
    }
  } catch (e) { for (const [t] of tmp) try { fs.unlinkSync(t); } catch (_) { } throw e; }
  for (const [t, dest] of tmp) fs.renameSync(t, dest);
  for (const s of plan) if (s.after === null) fs.unlinkSync(path.join(site, s.path));
  for (const s of plan) lines.push(JSON.stringify([reverse ? "rolled_back" : "applied", stamp, s.path, s.before === null ? "-" : D.Diff.sha256(s.before), s.after === null ? "-" : D.Diff.sha256(s.after), rep.decision, opt.force && rep.decision === "REJECT" ? "forced" : ""]));
  fs.appendFileSync(ledger, lines.join("\n") + "\n");
  console.log(c("32", `${reverse ? "ロールバック" : "適用"}しました: ${plan.length} ファイル (記録: ${ledger})`));
  return 0;
}

function cmdRules(pg) {
  const r = pg.rules();
  console.log(c("1", "@reviser で拡張した文法: ") + r.grammar.join(", "));
  console.log(c("1", "\ninvariant (不変量):"));
  for (const k of r.checks) console.log(`  ${k.id}  ${k.title}`);
  console.log(c("1", "\nsink (危険な受け口):"));
  for (const k of Object.keys(r.sinks)) { const s = r.sinks[k]; console.log(`  ${s.name.padEnd(22)} ${s.kind.padEnd(11)} 汚染時 ${s.tainted.padEnd(8)} 非汚染時 ${s.plain.padEnd(8)} ${s.why}`); }
  console.log(c("1", "\nsanitizer (無害化): ") + r.sanitizers.join(", "));
  return 0;
}

function main() {
  const D = deps();
  const pg = D.Core.create({ Engine: D.Engine, PHP: D.PHP, Diff: D.Diff, guardSrc: D.guardSrc });
  const [cmd, ...rest] = process.argv.slice(2);
  const { pos, opt } = parseArgs(rest);
  try {
    if (cmd === "check") return cmdCheck(pg, pos, opt);
    if (cmd === "apply") return cmdApply(pg, D, pos, opt, false);
    if (cmd === "rollback") return cmdApply(pg, D, pos, opt, true);
    if (cmd === "rules") return cmdRules(pg);
  } catch (e) {
    console.error(c("31", "エラー: " + (e && e.message || e)));
    return 3;
  }
  console.log(USAGE);
  return cmd ? 3 : 0;
}
process.exitCode = main();
