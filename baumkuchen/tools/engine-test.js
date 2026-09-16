/*
 * engine-test.js — Bada Baumkuchen(優しさのソース検索・蓄積)のエンジン単体テスト
 *
 *   node baumkuchen/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. normJa / tokenize          — 全角・カタカナの正規化と分割
 *   2. detectGenes / popcount     — 本文からの DNA スイッチ自動判定
 *   3. rarityOf / priceTag        — 希少性と値札
 *   4. buildGraph / genusOf       — 種数 g = E - V + C
 *   5. handleClosers              — 輪を閉じた層(後ろから読む)
 *   6. reverseRead                — 外側から剥く逆走査 (P + R = 総額)
 *   7. geneExpression / lastFlips — 発現率と最後の反転
 *   8. searchSources              — 検索・DNA マスク・絞り込み・並び
 *   9. seedRecords / normalizeAll / toCsv — 見本と入出力
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* ── サンドボックス (boot は __ENGINE_TEST__ で抑止) ── */
const sandbox = {
  console,
  window: { __ENGINE_TEST__: true },
  document: undefined,
  localStorage: undefined,
  setTimeout: function () { return 0; },
  clearTimeout: function () {}
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "baumkuchen-inline.js" });

/* ── テストハーネス ── */
let pass = 0, fail = 0;
function ok(cond, name) {
  if (cond) { pass++; console.log("  ✔ " + name); }
  else { fail++; console.error("  ✘ " + name); }
}
function eq(a, b, name) { ok(a === b, name + "  [" + JSON.stringify(a) + " === " + JSON.stringify(b) + "]"); }
function near(a, b, eps, name) { ok(Math.abs(a - b) <= eps, name + "  [" + a + " ~= " + b + "]"); }

const E = sandbox;
const DAY = 24 * 3600 * 1000;
const T0 = Date.UTC(2026, 0, 1);

/* 層をひとつ作るヘルパ (ts は T0 からの日数) */
function rec(id, src, dir, day, text, cost, ben, dna) {
  return E.sanitizeRecord({
    id: id, ts: T0 + day * DAY, src: src, dir: dir, text: text,
    cost: cost, benefit: ben, dna: dna
  }, 0);
}

/* ── 1. normJa / tokenize ── */
console.log("1. normJa / tokenize");
eq(E.normJa("ＡＢＣ１２３"), "abc123", "全角英数 → 半角小文字");
eq(E.normJa("カタカナ"), "かたかな", "カタカナ → ひらがな");
eq(E.normJa("　"), " ", "全角スペース → 半角");
eq(E.normJa("傘"), "傘", "漢字はそのまま");
eq(E.normJa(null), "", "null は空文字");
eq(E.normJa("ア").length, "ア".length, "正規化は長さを変えない(ハイライト位置の前提)");
eq(E.tokenize("  母  傘 ").join("|"), "母|傘", "空白区切り");
eq(E.tokenize("母、傘。").join("|"), "母|傘", "読点・句点も区切り");
eq(E.tokenize("").length, 0, "空文字はトークンなし");

/* ── 2. detectGenes / popcount / dnaString ── */
console.log("2. detectGenes / popcount / dnaString");
const dListen = E.detectGenes("話を最後まで聞いてくれた。");
eq(dListen[0], 1, "「聞いて」で 聴 が ON");
const dQuiet = E.detectGenes("何も言わずにそっと置いていった。");
eq(dQuiet[7], 1, "「何も言わ」「そっと」で 黙 が ON");
eq(E.popcount(E.detectGenes("今日は晴れだった。")), 0, "手がかりが無ければ全 OFF");
const dMulti = E.detectGenes("傘に入れてくれて、急かさないで待ってくれた。");
ok(dMulti[4] === 1 && dMulti[6] === 1, "複数の遺伝子が同時に ON (護 + 待)");
eq(E.dnaString([1,0,0,0,0,0,0,1]), "10000001", "dnaString");
eq(E.popcount([1,1,0,0,0,0,0,1]), 3, "popcount");
eq(E.detectGenes("ユズッてくれた").length, 8, "遺伝子は 8 本");

/* ── 3. rarityOf / priceTag ── */
console.log("3. rarityOf / priceTag");
eq(E.rarityOf([0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0], 10), 1, "全 OFF の希少性は 1");
eq(E.rarityOf([1,0,0,0,0,0,0,0], [10,0,0,0,0,0,0,0], 10), 1, "全層に有る遺伝子 → rho = 1");
eq(E.rarityOf([1,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0], 10), 2, "どこにも無い遺伝子 → rho = 2");
near(E.rarityOf([1,0,0,0,0,0,0,0], [5,0,0,0,0,0,0,0], 10), 1.5, 1e-9, "半分にある遺伝子 → rho = 1.5");
/* price = 100 (1+c)(1+b/10) rho (1+k/8), rho = 1, k = 0 → 100*4*1.5 = 600 */
eq(E.priceTag({ cost:3, benefit:5, dna:E.emptyDna() }, E.emptyDna(), 0), 600, "値札の素の値 (c=3,b=5,k=0)");
/* 蓄積が空 (total=0) のときは希少性を測れないので rho = 1 に倒す */
eq(E.priceTag({ cost:10, benefit:10, dna:[1,1,1,1,1,1,1,1] }, E.emptyDna(), 0),
   100 * 11 * 2 * 1 * 2, "蓄積が空なら rho=1 (c=b=10, k=8)");
/* 蓄積 10 層のうち一度も出ていない遺伝子ばかりなら rho = 2 */
eq(E.priceTag({ cost:10, benefit:10, dna:[1,1,1,1,1,1,1,1] }, E.emptyDna(), 10),
   100 * 11 * 2 * 2 * 2, "どこにも無い遺伝子ばかりなら rho=2 で倍");
ok(E.priceTag({ cost:5, benefit:5, dna:E.emptyDna() }, E.emptyDna(), 0)
   > E.priceTag({ cost:1, benefit:5, dna:E.emptyDna() }, E.emptyDna(), 0), "コストが高いほど値札も高い");
/* c=-4 → 0, b=99 → 10, dna=null → k=0 なので 100*1*2*1*1 = 200 */
eq(E.priceTag({ cost:-4, benefit:99, dna:null }, E.emptyDna(), 0), 200, "範囲外の c/b は 0..10 に丸める");
eq(E.fmtYen(1234567), "¥1,234,567", "fmtYen の三桁区切り");
eq(E.fmtYen(0), "¥0", "fmtYen(0)");

/* ── 4. buildGraph / genusOf ── */
console.log("4. buildGraph / genusOf  (g = E - V + C)");
eq(E.genusOf([]), 0, "空の蓄積は種数 0");
const oneWay = [rec("a", "母", "in", 0, "x", 1, 1, null)];
const g1 = E.buildGraph(oneWay);
ok(g1.V === 2 && g1.E === 1 && g1.C === 1, "一層: V=2 (母・自分), E=1, C=1");
eq(g1.genus, 0, "一層だけでは輪にならない (g=0)");
const tree = [
  rec("a", "母", "in", 0, "x", 1, 1, null),
  rec("b", "弟", "in", 1, "x", 1, 1, null),
  rec("c", "同僚", "out", 2, "x", 1, 1, null)
];
eq(E.genusOf(tree), 0, "相手が全員ちがえば木のまま (g=0)");
const back = tree.concat([rec("d", "母", "out", 3, "返した", 1, 1, null)]);
eq(E.genusOf(back), 1, "同じ相手に返すと輪が閉じる (g=1)");
const twice = back.concat([rec("e", "弟", "out", 4, "返した", 1, 1, null)]);
eq(E.genusOf(twice), 2, "二人目に返すと g=2");
const self = [rec("s", "自分", "out", 0, "自分に優しく", 1, 1, null)];
const gs = E.buildGraph(self);
ok(gs.V === 1 && gs.E === 1, "自分 → 自分 は自己ループ (V=1, E=1)");
eq(gs.genus, 1, "自己ループも穴を一つ作る (g=1)");
eq(E.handleClosers(twice).length, E.genusOf(twice), "輪を閉じた層の数 = 種数");
eq(E.handleClosersReverse(twice).length, E.genusOf(twice), "後ろから読んでも本数は同じ");
const cyc = E.handleClosersReverse(back)[0].cycle;
ok(cyc[0] === cyc[cyc.length - 1], "復元した閉路は始点に戻る");
ok(cyc.indexOf("母") >= 0 && cyc.indexOf("自分") >= 0, "閉路に 母 と 自分 が含まれる");

/* ── 5. reverseRead ── */
console.log("5. reverseRead  (後ろからの意味合い)");
const arc = E.repriceAll([
  rec("r1", "母", "in", 0, "話を聞いてくれた", 5, 6, null),
  rec("r2", "弟", "in", 10, "そっと荷物を運んだ", 4, 5, null),
  rec("r3", "母", "out", 20, "席を譲った", 3, 4, null)
]);
const steps = E.reverseRead(arc);
eq(steps.length, 3, "層の数だけ段がある");
eq(steps[0].layer.id, "r3", "最初に剥がれるのは一番外側 (新しい層)");
eq(steps[2].layer.id, "r1", "最後に残るのは芯 (古い層)");
const tot = E.totalPrice(arc);
for (let k = 0; k < steps.length; k++) {
  near(steps[k].peeledPrice + steps[k].residual, tot, 1e-9, "P(" + (k + 1) + ") + R(" + (k + 1) + ") = 総額");
}
eq(steps[2].residual, 0, "全部剥けば残りは ¥0");
eq(E.genusOf(arc), 1, "母 への返礼で輪が閉じている (g=1)");
eq(steps[0].genusRemain, 0, "その層を剥くと輪はほどける (g=0)");
ok(steps[0].peeledPrice === arc[2].price, "剥いた分は外側 1 層の値札そのもの");

/* ── 6. geneExpression / lastFlips ── */
console.log("6. geneExpression / lastFlips");
const now = T0 + 100 * DAY;
const flipArc = [
  rec("f1", "母", "in", 0,  "話を聞いてくれた", 3, 3, [1,0,0,0,0,0,0,0]),
  rec("f2", "弟", "in", 40, "何も言わなかった", 3, 3, [0,0,0,0,0,0,0,1]),
  rec("f3", "母", "in", 90, "また聞いてくれた", 3, 3, [1,0,0,0,0,0,0,0])
];
const expr = E.geneExpression(flipArc, now);
ok(expr[0] > expr[7], "直近で点いている 聴 の発現率が 黙 より高い");
ok(expr[1] === 0, "一度も点いていない遺伝子は 0");
for (let j = 0; j < 8; j++) ok(expr[j] >= 0 && expr[j] <= 1, "発現率 e[" + j + "] は 0..1");
near(E.recencyWeight(T0, T0 + 90 * DAY), 0.5, 1e-9, "半減期 90 日で重みは 1/2");
const flips = E.lastFlips(flipArc);
eq(flips[0].index, 2, "聴 の最後の反転は 3 層目");
eq(flips[0].dir, "on", "その反転は ON");
eq(flips[7].index, 2, "黙 は 3 層目で消えている");
eq(flips[7].dir, "off", "その反転は OFF");
eq(flips[1], null, "一度も点かない遺伝子に反転はない");

/* ── 7. searchSources ── */
console.log("7. searchSources");
const lib = E.repriceAll([
  rec("s1", "母",   "in",  0,  "話を最後まで聞いてくれた", 5, 6, null),
  rec("s2", "弟",   "out", 10, "何も言わずにそっと待った", 2, 3, null),
  rec("s3", "同僚", "in",  20, "傘に入れてくれた",        8, 9, null),
  rec("s4", "母",   "out", 30, "和菓子を渡した",          3, 4, null),
  rec("s5", "先輩", "in",  35, "コーヒーをおごってくれた", 2, 5, null)
]);
const opt = { now: T0 + 40 * DAY };
eq(E.searchSources(lib, "", opt).length, 5, "空クエリは全件");
eq(E.searchSources(lib, "母", opt).length, 2, "ソース名で引ける");
eq(E.searchSources(lib, "傘", opt)[0].rec.id, "s3", "本文の語で引ける");
eq(E.searchSources(lib, "こーひー", opt)[0].rec.id, "s5", "ひらがな入力でカタカナ本文を引ける(正規化)");
eq(E.searchSources(lib, "コーヒー", opt)[0].rec.id, "s5", "カタカナ入力でも同じ層に当たる");
eq(E.searchSources(lib, "存在しない語", opt).length, 0, "無い語は 0 件");
eq(E.searchSources(lib, "母 和菓子", opt).length, 1, "複数トークンは AND");
eq(E.searchSources(lib, "傾聴", opt)[0].rec.id, "s1", "遺伝子名でも引ける");

const maskOn = [-1,-1,-1,-1,-1,-1,-1,-1]; maskOn[7] = 1;
const onlyQuiet = E.searchSources(lib, "", { mask: maskOn, now: opt.now });
eq(onlyQuiet.length, 1, "DNA マスク ON 必須で絞れる");
eq(onlyQuiet[0].rec.id, "s2", "黙 が点いているのは s2");
const maskOff = [-1,-1,-1,-1,-1,-1,-1,-1]; maskOff[7] = 0;
eq(E.searchSources(lib, "", { mask: maskOff, now: opt.now }).length, 4, "OFF 必須は残り 4 件");
eq(E.searchSources(lib, "", { dir: "out", now: opt.now }).length, 2, "向きで絞れる (贈った層は 2 件)");
eq(E.searchSources(lib, "", { min: 99999, now: opt.now }).length, 0, "値札の下限で絞れる");
eq(E.searchSources(lib, "", { max: 0, now: opt.now }).length, 0, "値札の上限で絞れる");

const byNew = E.searchSources(lib, "", { sort: "new", now: opt.now });
eq(byNew[0].rec.id, "s5", "新しい順(外側から)");
const byOld = E.searchSources(lib, "", { sort: "old", now: opt.now });
eq(byOld[0].rec.id, "s1", "古い順(芯から)");
const byPrice = E.searchSources(lib, "", { sort: "price", now: opt.now });
ok(byPrice[0].rec.price >= byPrice[byPrice.length - 1].rec.price, "値札の高い順");
const lm = {}; lm["s4"] = 1;
const loops = E.searchSources(lib, "", { onlyLoop: true, loopIds: lm, now: opt.now });
eq(loops.length, 1, "輪を閉じた層だけに絞れる");
eq(loops[0].rec.id, "s4", "母 への返礼が輪を閉じた層");

/* ── 8. seedRecords / normalizeAll / toCsv ── */
console.log("8. seedRecords / normalizeAll / toCsv");
const seed = E.seedRecords(T0);
eq(seed.length, 14, "見本は 14 層");
ok(seed[0].ts < seed[seed.length - 1].ts, "見本は古い順(内側が古い)");
ok(seed.every(function (r) { return r.price > 0; }), "見本すべてに値札が付く");
ok(seed.every(function (r) { return r.dna.length === 8; }), "見本すべてに DNA が付く");
ok(E.genusOf(seed) >= 2, "見本には輪が二つ以上ある (g>=2)");
eq(E.handleClosersReverse(seed).length, E.genusOf(seed), "見本でも 輪の数 = 種数");
const dirty = E.normalizeAll([{ text: "席を譲ってくれた" }, { ts: "こわれた", src: "  ", cost: 99 }]);
eq(dirty.length, 2, "壊れた入力も 2 件として通る");
eq(dirty[1].src, "(無名)", "空のソースは (無名)");
eq(dirty[1].cost, 10, "範囲外の cost は丸められる");
ok(dirty.some(function (r) { return r.dna[1] === 1; }), "dna 欠落時は本文から自動判定");
const csv = E.toCsv(lib).split("\n");
eq(csv.length, 6, "CSV は見出し + 5 行");
eq(csv[0], "date,source,direction,cost,benefit,dna,price,text", "CSV 見出し");
ok(csv[1].indexOf('"母"') >= 0, "CSV はソース名を引用符で囲む");
ok(E.toCsv([rec("q", 'あ"い', "in", 0, "x", 1, 1, null)]).indexOf('あ""い') >= 0, "CSV の引用符はエスケープされる");

/* ── 結果 ── */
console.log("\n" + (fail ? "✘ " : "✔ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
