#!/usr/bin/env node
/*
 * engine-test.js — BadaGPT 道場 (bada_teach/index.html) のエンジンテスト。
 * index.html のインライン <script> を抽出して Node の vm で実行し、
 * ミニ Bada インタープリタ・量子コア・BadaGPT 先生 (tutorReply)・
 * 演習判定 (checkExercise) を検証します。UI (initUI) は
 * document が無いのでスキップされます。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("NG: inline <script> が見つかりません"); process.exit(1); }

const ctx = {};
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(m[1], ctx, { filename: "bada_teach-inline.js" });

const T = ctx.BadaTeach;
if (!T) { console.error("NG: globalThis.BadaTeach がエクスポートされていません"); process.exit(1); }

let failures = 0;
function ok(cond, label) {
  if (cond) { console.log("ok  - " + label); }
  else { console.error("NG  - " + label); failures++; }
}
function approx(a, b, eps) { return Math.abs(a - b) <= (eps || 1e-9); }

/* ---- 確率・情報コア ---- */
{
  const p = T.softmax([2, 1, 0, -1]);
  ok(approx(p.reduce((a, b) => a + b, 0), 1, 1e-12), "softmax は総和 1");
  ok(p[0] > p[1] && p[1] > p[2] && p[2] > p[3], "softmax は単調");
  ok(approx(T.entropy(T.unknownPrior(4)), Math.log(4), 1e-12), "一様分布のエントロピー = ln 4");
  ok(approx(T.entropy(T.unknownPrior(3)), 1.0986122886681098, 1e-9), "entropy(unknown_prior(3)) ≈ 1.09861");
}

/* ---- 量子コア ---- */
{
  let reg = T.qubitReg(1);
  reg = T.applyH(reg, 0);
  const p1 = T.measureProbs(reg);
  ok(approx(p1[0], 0.5) && approx(p1[1], 0.5), "H|0> = [0.5, 0.5]");

  let bell = T.qubitReg(2);
  bell = T.applyH(bell, 0);
  bell = T.applyCNOT(bell, 0, 1);
  const pb = T.measureProbs(bell);
  ok(approx(pb[0], 0.5) && pb[1] === 0 && pb[2] === 0 && approx(pb[3], 0.5),
     "Bell 状態 = [0.5, 0, 0, 0.5] (confident zero 保存)");
}

/* ---- ミニ Bada インタープリタ ---- */
{
  const out = T.badaRun([
    '# comment',
    'x := 40 + 2',
    'name := "Bada"',
    'print(name, "の答え:", x)',
    'xs := [10, 20, 30]',
    'print("len:", len(xs), " head:", xs[0])',
    'total := 0',
    'for v in xs {',
    '    total := total + v',
    '}',
    'print("total:", total)',
    'repeat 2 {',
    '    print("稽古")',
    '}',
    'fun hanbetsu |s| {',
    '    if s >= 60 {',
    '        return "合格"',
    '    }',
    '    return "追試"',
    '}',
    'print(hanbetsu(75), hanbetsu(30))',
    '"fact" >> tuplespace',
    '"fact2" >> tuplespace',
    'print("ledger:", len(tuplespace))'
  ].join("\n"));
  const lines = out.split("\n");
  ok(lines[0] === "Bada の答え: 42", "print + 変数 + 算術");
  ok(lines[1] === "len: 3  head: 10", "リストと len");
  ok(lines[2] === "total: 60", "for in の合計");
  ok(lines[3] === "稽古" && lines[4] === "稽古", "repeat");
  ok(lines[5] === "合格 追試", "fun / if / return");
  ok(lines[6] === "ledger: 2", ">> tuplespace と len(tuplespace)");
}
{
  const out = T.badaRun([
    'bell := qubit(2)',
    'bell := H(bell, 0)',
    'bell := CNOT(bell, 0, 1)',
    'p := Measure(bell)',
    'print("Bell :", p)',
    'print("zeros:", zeros_of(p))'
  ].join("\n"));
  ok(out.indexOf("Bell : [0.5, 0, 0, 0.5]") >= 0, "Bada からのベル状態");
  ok(out.indexOf("zeros: [1, 2]") >= 0, "zeros_of で禁止状態列挙");
}
{
  const out = T.badaRun([
    'prior := unknown_prior(4)',
    'print("H0 =", entropy(prior))',
    'post := update(prior, softmax([2.0, 1.0, 0.0, -1.0]))',
    'print("H1 =", entropy(post))'
  ].join("\n"));
  const h0 = parseFloat(out.split("\n")[0].split("=")[1]);
  const h1 = parseFloat(out.split("\n")[1].split("=")[1]);
  ok(h1 < h0, "update でエントロピーが下がる");
}
{
  let threw = false;
  try { T.badaRun('xs := [1, 2]\nprint(xs[5])'); }
  catch (e) { threw = /行目/.test(String(e.message)); }
  ok(threw, "範囲外アクセスは行番号つきエラー");
  threw = false;
  try { T.badaRun('repeat 10 {\n repeat 100000 {\n  x := 1\n }\n}'); }
  catch (e) { threw = /上限/.test(String(e.message)); }
  ok(threw, "無限ループ相当はステップ上限で停止");
}
{
  const out = T.badaRun('p := [0.1, 0.2, 0.7]\nprint(sample(p))', { seed: 7 });
  const v = parseInt(out, 10);
  ok(v >= 0 && v <= 2, "sample は分布の範囲内");
  ok(T.badaRun('print(sample([0, 1, 0]))', { seed: 1 }) === "1", "sample は確率 1 の状態を返す");
}

/* ---- BadaGPT 先生 (tutorReply) — 全テンプレートが動くコードを生成 ---- */
{
  const asks = {
    dice: "サイコロアプリを作って",
    fortune: "おみくじアプリを作って",
    todo: "ToDo アプリを作って",
    quiz: "クイズアプリを作って",
    calc: "電卓を作って",
    bell: "ベル状態のデモを見せて",
    counter: "カウンターアプリを作って"
  };
  for (const [id, ask] of Object.entries(asks)) {
    const r = T.tutorReply(ask, {});
    ok(r.steps.length >= 4, "tutorReply(" + id + "): 技①〜④ の 4 ステップ以上");
    ok(typeof r.code === "string" && r.code.length > 0, "tutorReply(" + id + "): コード生成");
    let ran = null;
    try { ran = T.badaRun(r.code, { seed: 42 }); } catch (e) { ran = null; console.error("      実行エラー: " + e.message); }
    ok(ran !== null && ran.length > 0, "tutorReply(" + id + "): 生成コードが実行できる");
  }
  const g = T.tutorReply("家計簿のようなものを作りたい", {});
  ok(g.code && g.code.indexOf("骨組み") >= 0, "未知の依頼は骨組みコードで応答");
  let ranG = null;
  try { ranG = T.badaRun(g.code, { seed: 1 }); } catch (e) { ranG = null; }
  ok(ranG !== null, "骨組みコードも実行できる");

  /* 技④ 反復: 面数変更 */
  const dice = T.tutorReply("サイコロアプリを作って", {});
  const refined = T.tutorReply("12面にして", { lastCode: dice.code, lastAppName: "量子サイコロ" });
  ok(refined.code && refined.code.indexOf("% 12 + 1") >= 0, "反復の技: 12面への差分修正");
  let ranR = null;
  try { ranR = T.badaRun(refined.code, { seed: 3 }); } catch (e) { ranR = null; }
  ok(ranR !== null && /出た目: (1[0-2]|[1-9])\b/.test(ranR), "12面サイコロが 1〜12 を出す");
}

/* ---- 演習の自動判定 ---- */
{
  let r = T.checkExercise("l4", 'p := unknown_prior(3)\nprint("H =", entropy(p))');
  ok(r.pass === true, "第4章演習: 正解コードは合格");
  r = T.checkExercise("l4", 'print("H =", 1.09861)');
  ok(r.pass === false, "第4章演習: unknown_prior 未使用は不合格");
  r = T.checkExercise("l5", 'reg := qubit(2)\nreg := H(reg, 0)\nreg := H(reg, 1)\nprint(Measure(reg))');
  ok(r.pass === true, "第5章演習: 2 量子ビット重ね合わせで合格");
  r = T.checkExercise("l7", 'menu := ["うどん", "そば", "カレー"]\nprint("今日の昼:", menu[2])');
  ok(r.pass === true, "第7章演習: バグ修正で合格");
  r = T.checkExercise("l7", 'menu := ["うどん", "そば", "カレー"]\nprint("今日の昼:", menu[3])');
  ok(r.pass === false && /エラー/.test(r.message), "第7章演習: バグのままは実行エラーで不合格");
  r = T.checkExercise("l8",
    'reg := qubit(2)\nreg := H(reg, 0)\np := Measure(reg)\nprint("p:", p)\ni := sample(p)\nprint("引いた:", i)\ni >> tuplespace\nprint("台帳:", len(tuplespace))',
    { seed: 5 });
  ok(r.pass === true, "卒業試験: 量子コア + 台帳で合格");
}

/* ---- カリキュラムの整合性 ---- */
{
  ok(T.LESSONS.length === 8, "カリキュラムは 8 章");
  let allHave = true;
  for (const l of T.LESSONS) {
    if (!l.id || !l.title || typeof l.body !== "function") allHave = false;
    if (l.starter != null) {
      try { T.badaRun(l.starter === "" ? 'print("ok")' : l.starter, { seed: 9 }); }
      catch (e) {
        /* 第7章のスターターは意図的なバグ (範囲外) のみ許容 */
        if (l.id !== "l7") { allHave = false; console.error("      " + l.id + " starter エラー: " + e.message); }
      }
    }
  }
  ok(allHave, "全章: body/starter が健全 (第7章の意図的バグを除く)");
  ok(T.APP_TEMPLATES.length >= 7, "テンプレートは 7 種以上");
}

console.log("");
if (failures) { console.error(failures + " 件のテストが失敗しました"); process.exit(1); }
console.log("BadaGPT 道場 engine tests: すべて合格 🎖");
