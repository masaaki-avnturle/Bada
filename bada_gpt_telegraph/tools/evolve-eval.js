/*
 * evolve-eval.js — 第 2 版 (会話台帳) の多ターン評価
 *
 *   node bada_gpt_telegraph/tools/evolve-eval.js            # 結果を表示
 *   node bada_gpt_telegraph/tools/evolve-eval.js --markdown # 論文用の Markdown 表
 *
 * 複数の発話からなる対話を、(a) 会話台帳の投影 (projectSpec) と (b) 基準法: 発話を連結して
 * 1 回で全体把握 (comprehend) に通したもの、の 2 通りで仕様にし、期待する最終仕様と比べる。
 * 期待は対話を人手で読んで付けた (作者による)。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const ctx = { console, TextEncoder, TextDecoder, atob, btoa };
vm.createContext(ctx);
for (const f of ["src/engine.js", "src/phasecore.js", "src/comprehend.js", "src/ledger.js", "src/generate.js"]) {
  vm.runInContext(fs.readFileSync(path.join(root, f), "utf8"), ctx, { filename: f });
}
const E = (x) => vm.runInContext(x, ctx);
const comprehend = E("comprehend"), Ledger = E("Ledger"), ledgerSay = E("ledgerSay"), projectSpec = E("projectSpec");
const generateApp = E("generateApp"), verifyApp = E("verifyApp");

/* [発話列, 期待] 期待: mods (集合一致), feats (明示的に有効), noFeats (無効), plats (集合一致・null は検査しない), entity, fields (完全一致・null は検査しない) */
const DIALOGS = [
  [["読んだ本を管理したい。", "検索も足して。", "Windows で使いたい。", "評価順に並べ替え。"], { mods: ["records"], feats: ["search", "sort"], plats: ["windows"], entity: "本" }],
  [["本の管理とタイマーのアプリ。", "タイマーは外して。"], { mods: ["records"], entity: "本" }],
  [["家計簿。", "グラフはいらない。", "印刷したい。"], { mods: ["budget"], feats: ["print"], noFeats: ["chart"] }],
  [["ポモドーロタイマー。", "音で知らせて。", "単語帳クイズも。"], { mods: ["timer", "quiz"], feats: ["sound"] }],
  [["顧客を管理したい。名前、会社、電話。", "メールも項目に足して。", "会社の項目は外して。"], { mods: ["records"], entity: "顧客", fields: ["名前", "電話", "メール"] }],
  [["お絵かきアプリ。", "@reset", "サイコロのアプリ。"], { mods: ["random"] }],
  [["「ワインノート」というアプリ。ワインの銘柄・産地・評価を記録。", "並べ替えもほしい。", "ダークで紫色に。"], { mods: ["records"], feats: ["sort"], entity: "ワイン", fields: ["銘柄", "産地", "評価"], accent: "紫", mode: "dark", title: "ワインノート" }],
  [["メモ帳。", "ToDo も足して。", "スマホで。"], { mods: ["notes", "todo"], plats: ["android"] }],
  [["量子回路で遊びたい。", "モールス電信も。", "電信はやっぱりやめて。"], { mods: ["quantum"] }],
  [["体重を記録したい。日付、体重、運動時間、メモ。", "グラフで推移を見たい。", "CSV で書き出し。"], { mods: ["records"], feats: ["chart", "export"], fields: ["日付", "体重", "運動時間", "メモ"] }],
  [["カウンター。", "電卓も。", "カウンターはいらない。"], { mods: ["calc"] }],
  [["習慣トラッカー。", "Linux と Windows で。", "Linux はなしで。"], { mods: ["habit"], plats: ["windows"] }],
  [["英単語クイズ。", "作って。"], { mods: ["quiz"] }],
  [["本を管理。", "検索も足して。", "検索はやめて。", "検索をもう一度足して。"], { mods: ["records"], feats: ["search"] }],
  [["毎日の日記。", "暗い青にして。", "アイデアも書きたい。"], { mods: ["notes"], accent: "青", mode: "dark" }],
  [["じゃんけんとくじ引き。", "タイマーも付けて。", "くじはいらない。"], { mods: ["random", "timer"] }]
];

function judge(spec, want) {
  const problems = [];
  if (!spec) return ["仕様なし"];
  const mods = spec.modules.map((m) => m.id).sort().join("+");
  if (mods !== want.mods.slice().sort().join("+")) problems.push("モジュール " + mods);
  (want.feats || []).forEach((f) => { if (!spec.features[f] || spec.features[f].assumed) problems.push("機能 " + f + " なし"); });
  (want.noFeats || []).forEach((f) => { if (spec.features[f] && !spec.features[f].assumed) problems.push("機能 " + f + " が残る"); });
  if (want.plats && spec.platforms.slice().sort().join() !== want.plats.slice().sort().join()) problems.push("対象 " + spec.platforms.join("+"));
  if (want.entity && spec.entity !== want.entity) problems.push("対象データ " + spec.entity);
  if (want.fields && spec.fields.map((f) => f.name).join() !== want.fields.join()) problems.push("項目 " + spec.fields.map((f) => f.name).join("・"));
  if (want.accent && spec.theme.accentName !== want.accent) problems.push("色 " + (spec.theme.accentName || "なし"));
  if (want.mode && spec.theme.mode !== want.mode) problems.push("見た目 " + spec.theme.mode);
  if (want.title && spec.title !== want.title) problems.push("題名 " + spec.title);
  return problems;
}

const rows = [];
let okLedger = 0, okConcat = 0, verified = 0, hSum = 0, hN = 0;
DIALOGS.forEach(([turns, want], i) => {
  const lg = new Ledger();
  const kept = [];
  turns.forEach((t) => { if (t === "@reset") { lg.append({ kind: "reset" }); kept.length = 0; } else { ledgerSay(lg, t, "文字"); kept.push(t); } });
  const proj = projectSpec(lg);
  const concat = comprehend(kept.join(""));
  const pL = judge(proj, want), pC = judge(concat, want);
  if (!pL.length) okLedger++;
  if (!pC.length) okConcat++;
  const g = generateApp(proj), v = verifyApp(g.html, proj);
  if (v.ok) verified++;
  const pe = proj.ledger.priorEntropy; hSum += pe[0] - pe[pe.length - 1]; hN++;
  rows.push({ i: i + 1, turns, want, pL, pC, ver: v.ok, facts: lg.size(), pe });
});
const summary = { n: DIALOGS.length, ledgerExact: okLedger / DIALOGS.length, concatExact: okConcat / DIALOGS.length, verified: verified / DIALOGS.length, meanEntropyDrop: hSum / hN };
const pct = (x) => (x * 100).toFixed(1) + "%";

if (process.argv.includes("--markdown")) {
  console.log("| # | 対話 (発話の列) | 期待する最終仕様 | 台帳の投影 | 連結 (基準法) | 事実 | H: 一様 → 最終 |");
  console.log("|---|---|---|---|---|---|---|");
  rows.forEach((r) => {
    const want = [r.want.mods.join("+"), (r.want.feats || []).map((f) => "+" + f).join(" "), (r.want.noFeats || []).map((f) => "−" + f).join(" "), r.want.plats ? r.want.plats.join("+") : "", r.want.fields ? "項目 " + r.want.fields.join("・") : ""].filter(Boolean).join(" / ");
    console.log("| " + r.i + " | " + r.turns.map((t) => t === "@reset" ? "(やり直し)" : t).join(" → ").replace(/\|/g, "／") + " | " + want + " | " + (r.pL.length ? "× " + r.pL.join("、") : "○") + " | " + (r.pC.length ? "× " + r.pC.join("、") : "○") + " | " + r.facts + " | " + r.pe[0].toFixed(2) + " → " + r.pe[r.pe.length - 1].toFixed(2) + " |");
  });
  console.log("");
  console.log("| 指標 | 台帳の投影 | 連結 (基準法) |");
  console.log("|---|---|---|");
  console.log("| 最終仕様の完全一致率 (" + summary.n + " 対話) | " + pct(summary.ledgerExact) + " | " + pct(summary.concatExact) + " |");
  console.log("| 投影した仕様から生成したアプリの静的検証合格率 | " + pct(summary.verified) + " | — |");
  console.log("| 未知事前のエントロピーの平均低下 (bit) | " + summary.meanEntropyDrop.toFixed(2) + " | — |");
} else {
  rows.forEach((r) => { if (r.pL.length || r.pC.length) console.log("  #" + r.i + " 台帳=" + (r.pL.join("、") || "○") + "  連結=" + (r.pC.join("、") || "○")); });
  console.log(JSON.stringify(summary, null, 2));
}
