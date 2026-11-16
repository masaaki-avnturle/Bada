#!/usr/bin/env node
/* 論文 第8節の評価: 台帳内 20 問 (期待する事実の一部を照合) + 台帳外 10 問 (棄権を期待)。
   各質問は新しいセッションで評価する (会話の信念を持ち越さない)。 */
"use strict";
const fs = require("fs"), path = require("path");
const Bada = require(path.join(__dirname, "..", "..", "bada_gui_ide", "www", "bada.js"));
const lib = fs.readFileSync(path.join(__dirname, "..", "zeta_shannon.bada"), "utf8").split("# ==== MAIN ====")[0];
const IN = [
  ["ナッシュ・シャノンゼータの定義を教えて", "ζ_NS(s) = ζ(s)·exp"],
  ["臨界線でのシャノンエントロピーの値は", "3.4568"],
  ["ζ に H を足すとどうなりますか", "加法版"],
  ["ナッシュ均衡はどんな分布ですか", "ボルツマン形"],
  ["零の保存とは何ですか", "零の保存とは"],
  ["未知事前分布はどこから始まりますか", "一様分布から始まり"],
  ["TupleSpace とは何ですか", "追記専用の不変な台帳"],
  ["リバイザは何をしますか", "文法拡張トランザクション"],
  ["PrecogBada は幻覚を起こしますか", "PrecogBada"],
  ["リーマン予想は解決しましたか", "リーマン予想は未解決"],
  ["最初の零点の虚部はいくつですか", "14.134725"],
  ["x log x は何を数えますか", "零点の個数"],
  ["深リーマン予想とは何ですか", "深リーマン予想は、極を持たない"],
  ["χ₄ の L(1/2) の値は", "0.667691457"],
  ["Perelman の λ 汎関数とは", "最小固有値"],
  ["8 幾何のうち Einstein なのはどれ", "E³、S³、H³"],
  ["ホッジ予想は解けていますか", "ホッジ予想は未解決"],
  ["フェルミ=ディラック積分とゼータの関係は", "F_j(0)"],
  ["ミレニアム問題で解決済みなのは", "ポアンカレ予想だけ"],
  ["ジップの法則とは", "ジップの法則では"],
];
const OUT = ["明日の東京の天気は", "今日の夕食は何がいいですか", "サッカーの試合結果を教えて", "おすすめの映画はありますか",
  "富士山の高さは何メートルですか", "円周率の百桁目は", "来年の選挙は誰が勝ちますか", "カレーの作り方を教えて",
  "新幹線の料金はいくらですか", "犬と猫はどちらが賢いですか"];
function ask(q) {
  const s = Bada.createSession({ maxSteps: 1e15 });
  s.eval(lib);
  const r = s.eval('VERBOSE[0] = 0\nrr := zs_reply("' + q + '")\nprint(rr[1])\nprint(rr[0])');
  const [status, ...rest] = r.output.split("\n");
  return { status, text: rest.join(" ") };
}
let ok = 0, abst = 0, wrong = [];
for (const [q, want] of IN) {
  const a = ask(q);
  if (a.status === "無知") { abst++; wrong.push([q, "(棄権)"]); }
  else if (a.text.includes(want)) ok++;
  else wrong.push([q, a.text.slice(0, 40)]);
}
let okOut = 0, leak = [];
for (const q of OUT) { const a = ask(q); if (a.status === "無知") okOut++; else leak.push([q, a.text.slice(0, 40)]); }
console.log(JSON.stringify({ inN: IN.length, inCorrect: ok, inAbstain: abst, outN: OUT.length, outAbstain: okOut, wrong, leak }, null, 1));
