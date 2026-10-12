/*
 * evaluate.js — 論文「表 3・表 4」の評価を再現するスクリプト
 *
 *   node bada_gpt_telegraph/tools/evaluate.js            # 結果を表示
 *   node bada_gpt_telegraph/tools/evaluate.js --markdown # 論文用の Markdown 表を出力
 *   node bada_gpt_telegraph/tools/evaluate.js --heldout  # 未見の評価セット (HELDOUT) で測る
 *
 * 正解ラベル付きの依頼文 (下の BENCH) を全体把握 → 生成 → 検証に通し、
 *   - モジュール選択の適合率・再現率・完全一致率
 *   - 項目 (データモデル) 抽出の完全一致率
 *   - 節の網羅率 (平均・最小) と未解釈の節の数
 *   - 生成アプリの静的検証の合格率
 * を測る。ラベルは依頼文を人手で読んで付けたもの (作者による)。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const ctx = { console, TextEncoder, TextDecoder, atob, btoa };
vm.createContext(ctx);
for (const f of ["src/engine.js", "src/comprehend.js", "src/generate.js", "src/paper.js"]) {
  vm.runInContext(fs.readFileSync(path.join(root, f), "utf8"), ctx, { filename: f });
}
const comprehend = vm.runInContext("comprehend", ctx);
const generateApp = vm.runInContext("generateApp", ctx);
const verifyApp = vm.runInContext("verifyApp", ctx);

/* [依頼文, 期待するモジュール, 期待する項目 (records のときのみ・null は検査しない)] */
const BENCH = [
  ["読んだ本を管理したい。項目はタイトル、著者、読了日、評価、感想。評価順に並べ替えたい。", ["records"], ["タイトル", "著者", "読了日", "評価", "感想"]],
  ["毎月の家計簿をつけたい。支出と収入を記録してグラフで見たい。", ["budget"], null],
  ["勉強用にポモドーロタイマーと単語帳クイズ、それとToDoリストが欲しい。音で知らせて。", ["timer", "quiz", "todo"], null],
  ["量子もつれのベル状態を試せる回路と、モールスで電信を打てる画面を一つのアプリに。", ["quantum", "telegraph"], null],
  ["子供と遊べるお絵かきとサイコロのアプリを作って。", ["draw", "random"], null],
  ["電卓とカウンターと単位変換と習慣トラッカーとメモ帳をまとめたツール箱。", ["calc", "counter", "convert", "habit", "notes"], null],
  ["「ワインノート」というアプリ。ワインの銘柄・産地・購入日・評価を記録", ["records"], ["銘柄", "産地", "購入日", "評価"]],
  ["Book title:string author:string price:integer read:boolean を管理", ["records"], ["title", "author", "price", "read"]],
  ["顧客を管理したい。名前、会社、電話、メールを登録して検索できるように。", ["records"], ["名前", "会社", "電話", "メール"]],
  ["在庫管理アプリ。品名・数量・単価・保管場所を記録し、CSVで書き出したい。", ["records"], ["品名", "数量", "単価", "保管場所"]],
  ["毎日の日記を書くアプリ。検索もしたい。", ["notes"], null],
  ["今日やることのチェックリストと締め切りの管理。", ["todo"], null],
  ["カップラーメン用のカウントダウンタイマー。アラームで知らせて。", ["timer"], null],
  ["英単語の暗記カードでクイズを出して。", ["quiz"], null],
  ["体重を記録したい。日付、体重、運動時間、メモ。グラフで推移を見たい。", ["records"], ["日付", "体重", "運動時間", "メモ"]],
  ["じゃんけんとくじ引きで当番を決めるアプリ。", ["random"], null],
  ["早起きと読書の習慣を続けるための記録アプリ。", ["habit"], null],
  ["摂氏と華氏、メートルとフィートを換算したい。", ["convert"], null],
  ["お小遣い帳。収入と出費を記録する。", ["budget"], null],
  ["映画の鑑賞記録をつけたい。", ["records"], ["タイトル", "監督", "鑑賞日", "評価", "感想"]],
  ["人数を数えるカウンターがほしい。", ["counter"], null],
  ["SOS をモールス信号で打電できるアプリ。", ["telegraph"], null],
  ["手書きでスケッチして保存できるお絵描きアプリ。", ["draw"], null],
  ["量子回路でキュービットを操作して測定したい。", ["quantum"], null]
];

/* 未見の評価セット: 上の規則の修正を終えた後に書き、修正せずに一度だけ評価したもの */
const HELDOUT = [
  ["レシピを管理するアプリ。料理名、材料、手順、調理時間を記録したい。", ["records"], ["料理名", "材料", "手順", "調理時間"]],
  ["会議の時間を計るストップウォッチ。", ["timer"], null],
  ["旅行の支出を記録して合計を見たい。", ["budget"], null],
  ["植物の水やりを管理したい。", ["records"], ["名前", "前回のお世話", "次回予定", "メモ"]],
  ["歴史の年号を覚えるための問題集。", ["quiz"], null],
  ["毎日の筋トレの継続を記録する習慣アプリ。", ["habit"], null],
  ["ボードゲーム用のサイコロとタイマーをひとつに。", ["random", "timer"], null],
  ["アイデアを書き留めるノートと、やることリスト。", ["notes", "todo"], null],
  ["社員名簿を作りたい。氏名、部署、内線番号、入社日。", ["records"], ["氏名", "部署", "内線番号", "入社日"]],
  ["ベル状態を作って測定する量子の練習。", ["quantum"], null]
];
const SET = process.argv.includes("--heldout") ? HELDOUT : BENCH;

let tp = 0, fp = 0, fn = 0, exact = 0, fieldN = 0, fieldOk = 0, covSum = 0, covMin = 1, unresolved = 0, verified = 0;
const rows = [];
SET.forEach(([text, want, fields], i) => {
  const s = comprehend(text);
  const got = s.modules.map((m) => m.id);
  const t = got.filter((g) => want.includes(g)).length;
  tp += t; fp += got.length - t; fn += want.length - t;
  const ex = t === want.length && got.length === want.length;
  if (ex) exact++;
  let fOk = null;
  if (fields) { fieldN++; fOk = JSON.stringify(s.fields.map((f) => f.name)) === JSON.stringify(fields); if (fOk) fieldOk++; }
  covSum += s.coverage; covMin = Math.min(covMin, s.coverage); unresolved += s.unresolved.length;
  const g = generateApp(s), v = verifyApp(g.html, s);
  if (v.ok) verified++;
  rows.push({ i: i + 1, text, want: want.join("+"), got: got.join("+"), ex, fOk, cov: s.coverage, ver: v.ok });
});
const P = tp / (tp + fp), R = tp / (tp + fn);
const summary = {
  n: SET.length, precision: P, recall: R, f1: 2 * P * R / (P + R), exact: exact / SET.length,
  fieldExact: fieldOk / fieldN, fieldN, coverageMean: covSum / SET.length, coverageMin: covMin, unresolved, verified: verified / SET.length
};

const pct = (x) => (x * 100).toFixed(1) + "%";
if (process.argv.includes("--markdown")) {
  console.log("| # | 依頼文 | 正解 | 選択 | 一致 | 項目 | 網羅率 | 検証 |");
  console.log("|---|---|---|---|---|---|---|---|");
  rows.forEach((r) => console.log("| " + r.i + " | " + r.text.replace(/\|/g, "／") + " | " + r.want + " | " + r.got + " | " + (r.ex ? "○" : "×") + " | " +
    (r.fOk === null ? "—" : r.fOk ? "○" : "×") + " | " + pct(r.cov) + " | " + (r.ver ? "合格" : "不合格") + " |"));
  console.log("");
  console.log("| 指標 | 値 |");
  console.log("|---|---|");
  console.log("| 依頼文の数 | " + summary.n + " |");
  console.log("| モジュール選択の適合率 / 再現率 / F1 | " + pct(summary.precision) + " / " + pct(summary.recall) + " / " + pct(summary.f1) + " |");
  console.log("| モジュール集合の完全一致率 | " + pct(summary.exact) + " |");
  console.log("| 項目抽出の完全一致率 (" + summary.fieldN + " 件) | " + pct(summary.fieldExact) + " |");
  console.log("| 節の網羅率 (平均 / 最小) | " + pct(summary.coverageMean) + " / " + pct(summary.coverageMin) + " |");
  console.log("| 未解釈の節 (合計) | " + summary.unresolved + " |");
  console.log("| 生成アプリの静的検証合格率 | " + pct(summary.verified) + " |");
} else {
  rows.filter((r) => !r.ex || r.fOk === false || !r.ver).forEach((r) => console.log("  ✗ #" + r.i + " " + r.text + "  want=" + r.want + " got=" + r.got + " fields=" + r.fOk));
  console.log(JSON.stringify(summary, null, 2));
}
