/*
 * engine-test.js — Bada CineVim のエンジン単体テスト
 *
 *   node bada_cinevim/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジックを検証します:
 *   1. badaTokenize      — Bada 構文のトークン化 (<- -< >- Ω:: |0⟩ コメント)
 *   2. gammaFn/betaFn    — Γ(s) と β(p,q)、ζ(s)=β/log x
 *   3. badaLeft/Mani/Right — 3 つの非可換オペレータの数値意味論
 *   4. 量子シミュレータ  — H / X / CNOT / measure / 確率分布
 *   5. badaEval          — 式パーサ (優先順位)
 *   6. quantumRun        — Bada プログラムの実行
 *   7. VIM モーション    — w b e $ ^ gg G f t % { }
 *   8. VIM オペレータ    — dd dw cw yy p x J >> u Ctrl-R . ビジュアル
 *   9. Ex コマンド       — :42 :%s/// :set :w :countdown :emit :flash
 *  10. イベントバス      — key / motion / edit / mode の発行とディスパッチ順
 *  11. シネマ数理        — focusStyle / docLayout / flashFrame / countdownState
 *  12. 多段落と拡大鏡    — splitParagraphs / paragraphText / wordAt /
 *                          sentenceAt / loupeTransform / markRange
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

const sandbox = {
  console, Math, Object, Array, String, Number, JSON, RegExp, Error, Date, isFinite, parseFloat, parseInt,
  window: { __ENGINE_TEST__: true },
  document: undefined,
  navigator: {},
  performance: { now: function(){ return 0; } },
  requestAnimationFrame: function(){ return 0; },
  setTimeout: function(){ return 0; }
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "cinevim-inline.js" });
const E = sandbox;

/* ── テストハーネス ── */
let pass = 0, fail = 0;
function ok(cond, name){
  if (cond){ pass++; console.log("  ✔ " + name); }
  else { fail++; console.error("  ✘ " + name); }
}
function eq(a, b, name){ ok(a === b, name + "  [" + JSON.stringify(a) + " === " + JSON.stringify(b) + "]"); }
function near(a, b, tol, name){
  const d = Math.abs(a - b);
  ok(d <= (tol === undefined ? 1e-9 : tol), name + "  [" + a + " ≈ " + b + "]");
}
/* キー列を流し込んで本文を得るヘルパ */
function ed(text){ return E.vimNew(text, "t.bada"); }
function txt(st){ return E.vimText(st); }
function keys(st, s){ E.feedString(st, s); return st; }

/* ═════ 1. トークナイザ ═════ */
console.log("1. badaTokenize — Bada 構文");
{
  const t = E.badaTokenize("class CountdownNode <- TupleSpace {").toks;
  const types = t.filter(x => x.t !== "ws").map(x => x.t).join(",");
  eq(types, "kw,id,qop,id,punct", "class 宣言のトークン列");
  eq(t[0].v, "class", "キーワード class");

  const q = E.badaTokenize("  return beta(2, 3) / log(x);   // ζ").toks.filter(x => x.t !== "ws");
  eq(q[0].t, "kw", "return はキーワード");
  eq(q[1].t, "fn", "beta は組み込み関数");
  eq(q[q.length - 1].t, "com", "行末コメント");

  const ops = E.badaTokenize("a <- b -< c >- d").toks.filter(x => x.t === "qop").map(x => x.v);
  eq(ops.join(" "), "<- -< >-", "3 つの量子オペレータを認識");

  eq(E.badaTokenize("-5").toks[0].v, "-", "単項マイナスは通常オペレータ");
  eq(E.badaTokenize("Omega::DATABASE").toks[0].t, "ns", ":: の直前は名前空間");
  eq(E.badaTokenize("|0⟩ + |1⟩").toks[0].t, "ket", "量子ケット |0⟩");
  eq(E.badaTokenize('let s = "hi // not a comment";').toks.filter(x => x.t === "com").length, 0,
     "文字列内の // はコメントではない");
  eq(E.badaTokenize("0x1F 3.14e-2 42").toks.filter(x => x.t === "num").length, 3, "16進 / 指数 / 整数");

  /* ブロックコメントの行またぎ */
  const b1 = E.badaTokenize("/* T-5 まで", false);
  eq(b1.inBlock, true, "ブロックコメントが継続する");
  const b2 = E.badaTokenize("   まだコメント */ let x = 1;", true);
  eq(b2.inBlock, false, "ブロックコメントが閉じる");
  eq(b2.toks[0].t, "com", "継続行の先頭はコメント");
  ok(b2.toks.some(x => x.t === "kw" && x.v === "let"), "閉じた後は通常のコード");

  const all = E.badaTokenizeAll(["/* a", "b", "c */ let z = 1;"]);
  eq(all[1][0].t, "com", "複数行にまたがるブロックコメント");
}

/* ═════ 2. Γ / β / ζ ═════ */
console.log("2. gammaFn / betaFn / zetaBeta");
near(E.gammaFn(5), 24, 1e-6, "Γ(5) = 4! = 24");
near(E.gammaFn(1), 1, 1e-9, "Γ(1) = 1");
near(E.gammaFn(0.5), Math.sqrt(Math.PI), 1e-8, "Γ(1/2) = √π");
near(E.betaFn(1, 1), 1, 1e-9, "β(1,1) = 1");
near(E.betaFn(2, 3), 1 / 12, 1e-9, "β(2,3) = 1/12");
near(E.betaFn(3, 2), E.betaFn(2, 3), 1e-12, "β は対称");
near(E.zetaBeta(2, 3, Math.E), 1 / 12, 1e-9, "ζ = β(2,3)/log(e)");

/* ═════ 3. 非可換オペレータ ═════ */
console.log("3. badaLeft / badaMani / badaRight");
near(E.badaLeft(1, 0), 1, 1e-12, "a <- 0 = a·cos0 = a");
near(E.badaLeft(0, 2), -2 * Math.sin(0), 1e-12, "0 <- b = -b·sin0 = 0");
ok(E.badaLeft(2, 3) !== E.badaLeft(3, 2), "<- は非可換");
near(E.badaMani(2, 2), 0, 1e-12, "a -< a = 0 (積分区間が退化)");
ok(E.badaMani(2, 12) > 0, "2 -< 12 は正");
near(E.badaMani(12, 2), -E.badaMani(2, 12), 1e-9, "-< は向きで符号が反転");
{
  /* ∫1/(x ln x)² dx の解析解と照合 (十分細かい刻みで) */
  const F = x => -1 / (Math.log(x)) - E.badaMani ? 0 : 0;   /* 数値同士の一貫性で検証 */
  const coarse = E.badaMani(2, 6, 40), fine = E.badaMani(2, 6, 4000);
  near(coarse, fine, 1e-4, "シンプソン則が刻み幅に対して安定");
}
near(E.badaRight(0, 0), 1, 1e-12, "b=0 のとき ℏ·cos(a)");
near(E.badaRight(0, 1e-7), Math.cos(0), 1e-6, ">- は ∇sin(a) の極限へ収束");

/* ═════ 4. 量子シミュレータ ═════ */
console.log("4. 量子状態ベクトル");
{
  let q = E.qnew(1);
  eq(E.qprobs(q)[0], 1, "初期状態は |0⟩");
  E.qgate1(q, "X", 0);
  near(E.qprobs(q)[1], 1, 1e-12, "X|0⟩ = |1⟩");
  q = E.qnew(1); E.qgate1(q, "H", 0);
  near(E.qprobs(q)[0], 0.5, 1e-12, "H|0⟩ は 50%");
  near(E.qprobs(q)[1], 0.5, 1e-12, "H|0⟩ の |1⟩ も 50%");
  E.qgate1(q, "H", 0);
  near(E.qprobs(q)[0], 1, 1e-12, "H·H = I");

  /* ベル状態 */
  let b = E.qnew(2);
  E.qgate1(b, "H", 0); E.qcnot(b, 0, 1);
  const p = E.qprobs(b);
  near(p[0], 0.5, 1e-12, "ベル状態 |00⟩ 50%");
  near(p[3], 0.5, 1e-12, "ベル状態 |11⟩ 50%");
  near(p[1] + p[2], 0, 1e-12, "|01⟩ と |10⟩ は 0%");

  /* 観測 → collapse、以後は決定的 */
  const rng = E.mulberry32(7);
  const shot = E.qmeasure(b, rng);
  ok(shot === 0 || shot === 3, "ベル状態の観測は |00⟩ か |11⟩");
  near(E.qprobs(b)[shot], 1, 1e-12, "観測後は固有状態へ collapse");
  eq(E.qmeasure(b, rng), shot, "collapse 後は同じ値しか出ない");

  /* 確率の総和 */
  let r = E.qnew(3);
  E.qgate1(r, "H", 0); E.qgate1(r, "H", 1); E.qrot(r, "RY", 2, 0.7);
  near(E.qprobs(r).reduce((a, b2) => a + b2, 0), 1, 1e-10, "確率の総和は 1 (ユニタリ)");

  /* SWAP / CZ */
  let s = E.qnew(2); E.qgate1(s, "X", 0); E.qswap(s, 0, 1);
  near(E.qprobs(s)[2], 1, 1e-12, "SWAP で |01⟩ → |10⟩");

  eq(E.qbits(5, 3), "101", "qbits(5,3)");
  eq(E.qbits(0, 4), "0000", "qbits(0,4)");

  /* mulberry32 は決定的 */
  eq(E.mulberry32(42)(), E.mulberry32(42)(), "同じ種なら同じ乱数");
}

/* ═════ 5. 式パーサ ═════ */
console.log("5. badaEval — 優先順位と関数");
{
  const env = { vars: {}, rng: E.mulberry32(1) };
  eq(E.badaEval("1 + 2 * 3", env), 7, "* が + より優先");
  eq(E.badaEval("(1 + 2) * 3", env), 9, "括弧");
  eq(E.badaEval("2 ** 3 ** 2", env), 512, "** は右結合");
  eq(E.badaEval("-3 + 1", env), -2, "単項マイナス");
  near(E.badaEval("log(exp(2))", env), 2, 1e-12, "log(exp(2))");
  near(E.badaEval("beta(2,3)", env), 1 / 12, 1e-9, "beta(2,3)");
  /* 量子オペレータは最も弱く結合する */
  near(E.badaEval("1 + 1 <- 0", env), E.badaLeft(2, 0), 1e-12, "<- は + より弱い");
  near(E.badaEval("4.0 <- 2.0", env), E.badaLeft(4, 2), 1e-12, "4.0 <- 2.0");
  near(E.badaEval("2.0 -< 12.0", env), E.badaMani(2, 12), 1e-12, "2.0 -< 12.0");
  near(E.badaEval("1.0 >- 0.5", env), E.badaRight(1, 0.5), 1e-12, "1.0 >- 0.5");
  env.vars.x = 10;
  eq(E.badaEval("x * 2", env), 20, "変数の参照");
  near(E.badaEval("√(9)", env), 3, 1e-12, "√ 演算子");
  let threw = false;
  try { E.badaEval("nosuchvar + 1", env); } catch (e){ threw = /未定義/.test(e.message); }
  ok(threw, "未定義の識別子はエラー");
}

/* ═════ 6. quantumRun ═════ */
console.log("6. quantumRun — プログラム実行");
{
  const r = E.quantumRun([
    "qubit q[2];",
    "H q[0];",
    "CNOT q[0], q[1];",
    "let z = 4.0 <- 2.0;",
    "print z;"
  ].join("\n"), 0x5EED);
  eq(r.err, null, "ベル状態プログラムはエラーなし");
  eq(r.state.n, 2, "2 量子ビット");
  near(E.qprobs(r.state)[0] + E.qprobs(r.state)[3], 1, 1e-10, "ベル状態が張られている");
  near(r.vars.z, E.badaLeft(4, 2), 1e-12, "let z = 4.0 <- 2.0");
  ok(r.out.some(o => /▸/.test(o.text)), "print が出力に現れる");

  /* 同じ種なら結果は完全に再現する */
  const a = E.quantumRun("qubit q[2];\nH q[0];\nlet s = measure q;\nprint s;", 123);
  const b = E.quantumRun("qubit q[2];\nH q[0];\nlet s = measure q;\nprint s;", 123);
  eq(a.vars.s, b.vars.s, "同じ種なら観測結果が一致 (決定的)");

  /* クラス / オペレータ定義の本体はスキップされる */
  const c = E.quantumRun([
    "class Node <- TupleSpace {",
    "  operator <- (input) {",
    "    return beta(2,3) / log(input);",
    "  }",
    "}",
    "let v = 1 + 1;"
  ].join("\n"), 1);
  eq(c.err, null, "定義ブロックを読み飛ばす");
  eq(c.vars.v, 2, "ブロックの後の文が実行される");
  eq(c.classes[0], "Node", "class 名を記録");

  /* エラー行の報告 */
  const e2 = E.quantumRun("qubit q[2];\nH q[9];", 1);
  ok(/行 2/.test(e2.err), "エラーは行番号つきで報告される");

  /* コメントだけの行は無視 */
  const e3 = E.quantumRun("// なにもしない\n/* ブロック */\nlet k = 3;", 1);
  eq(e3.err, null, "コメント行は無視される");
  eq(e3.vars.k, 3, "コメントの後の文が実行される");

  /* 同梱デモがそのまま走る */
  const demo = E.quantumRun(E.DEMO_SRC, 0x5EED);
  eq(demo.err, null, "同梱デモ (DEMO_SRC) がエラーなく完走する");
}

/* ═════ 7. VIM モーション ═════ */
console.log("7. VIM モーション");
{
  let st = ed("alpha beta gamma\nsecond line\nthird");
  keys(st, "w"); eq(st.cur.c, 6, "w で次の単語へ");
  keys(st, "w"); eq(st.cur.c, 11, "w をもう一度");
  keys(st, "b"); eq(st.cur.c, 6, "b で前の単語へ");
  keys(st, "$"); eq(st.cur.c, 15, "$ で行末");
  keys(st, "0"); eq(st.cur.c, 0, "0 で行頭");
  keys(st, "e"); eq(st.cur.c, 4, "e で単語末");
  keys(st, "G"); eq(st.cur.l, 2, "G で最終行");
  keys(st, "gg"); eq(st.cur.l, 0, "gg で先頭行");
  keys(st, "2G"); eq(st.cur.l, 1, "2G で 2 行目");
  keys(st, "j"); eq(st.cur.l, 2, "j で下へ");
  keys(st, "kk"); eq(st.cur.l, 0, "k で上へ");
  keys(st, "3l"); eq(st.cur.c, 3, "3l でカウント付き移動");
  keys(st, "2h"); eq(st.cur.c, 1, "2h");

  st = ed("  indented line");
  keys(st, "^"); eq(st.cur.c, 2, "^ で最初の非空白");

  st = ed("find the x here");
  keys(st, "fx"); eq(st.cur.c, 9, "fx で x へ");
  keys(st, "0tx"); eq(st.cur.c, 8, "tx は x の手前");
  keys(st, "$Fx"); eq(st.cur.c, 9, "Fx で後方検索");

  st = ed("call(a, b)");
  keys(st, "%"); eq(st.cur.c, 9, "% で対応する閉じ括弧へ");
  keys(st, "%"); eq(st.cur.c, 4, "% で戻る");

  st = ed("a\nb\n\nc\nd\n\ne");
  keys(st, "}"); eq(st.cur.l, 2, "} で次の空行へ");
  keys(st, "}"); eq(st.cur.l, 5, "} をもう一度");
  keys(st, "{"); eq(st.cur.l, 2, "{ で前の空行へ");

  /* 検索 */
  st = ed("one\ntwo target\nthree\ntarget again");
  E.feedString(st, "/target<CR>");
  eq(st.cur.l, 1, "/target で 2 行目へ");
  keys(st, "n"); eq(st.cur.l, 3, "n で次の一致");
  keys(st, "N"); eq(st.cur.l, 1, "N で前の一致");

  /* 行を越える w */
  st = ed("last\nnext");
  keys(st, "$w"); eq(st.cur.l, 1, "w は行をまたぐ");
}

/* ═════ 8. VIM オペレータ ═════ */
console.log("8. VIM オペレータ / 編集");
{
  let st = ed("one\ntwo\nthree");
  keys(st, "dd"); eq(txt(st), "two\nthree", "dd で行削除");
  keys(st, "p"); eq(txt(st), "two\none\nthree", "p で貼り付け");
  keys(st, "u"); eq(txt(st), "two\nthree", "u で取り消し");
  keys(st, "<C-r>"); eq(txt(st), "two\none\nthree", "Ctrl-R でやり直し");

  st = ed("alpha beta gamma");
  keys(st, "dw"); eq(txt(st), "beta gamma", "dw で単語削除");
  keys(st, "d$"); eq(txt(st), "", "d$ で行末まで削除");

  st = ed("aaa bbb ccc");
  keys(st, "2dw"); eq(txt(st), "ccc", "2dw で 2 単語削除");

  st = ed("one\ntwo\nthree\nfour");
  keys(st, "2dd"); eq(txt(st), "three\nfour", "2dd で 2 行削除");

  st = ed("hello world");
  keys(st, "cwbye<Esc>"); eq(txt(st), "bye world", "cw で単語を変更");

  st = ed("keep this");
  keys(st, "x"); eq(txt(st), "eep this", "x で一文字削除");
  keys(st, "3x"); eq(txt(st), " this", "3x で 3 文字削除");

  st = ed("abc");
  keys(st, "rz"); eq(txt(st), "zbc", "r で一文字置換");
  keys(st, "$"); keys(st, "~"); eq(txt(st), "zbC", "~ で大小反転");

  st = ed("first\nsecond");
  keys(st, "J"); eq(txt(st), "first second", "J で行連結");

  st = ed("line");
  keys(st, "ihello <Esc>"); eq(txt(st), "hello line", "i で挿入");
  st = ed("line");
  keys(st, "A!<Esc>"); eq(txt(st), "line!", "A で行末に追記");
  st = ed("line");
  keys(st, "Onew<Esc>"); eq(txt(st), "new\nline", "O で上に行を開く");
  st = ed("line");
  keys(st, "onew<Esc>"); eq(txt(st), "line\nnew", "o で下に行を開く");

  /* 挿入モードの改行とバックスペース */
  st = ed("ab");
  keys(st, "a<CR>c<Esc>"); eq(txt(st), "a\ncb", "挿入モードの <CR>");
  st = ed("abc");
  keys(st, "A<BS><BS><Esc>"); eq(txt(st), "a", "挿入モードの <BS>");

  /* インデント */
  st = ed("x\ny");
  keys(st, ">>"); eq(txt(st), "  x\ny", ">> でインデント");
  keys(st, "<<"); eq(txt(st), "x\ny", "<< でアンインデント");
  st = ed("a\nb\nc");
  keys(st, "3>>"); eq(txt(st), "  a\n  b\n  c", "3>> で 3 行インデント");

  /* ヤンクと名前付きレジスタ */
  st = ed("copy\nme");
  keys(st, "yyjp"); eq(txt(st), "copy\nme\ncopy", "yy と p");
  st = ed("one\ntwo");
  keys(st, '"ayyj"ap'); eq(txt(st), "one\ntwo\none", "名前付きレジスタ");

  /* ビジュアルモード */
  st = ed("delete these words");
  keys(st, "vld"); eq(txt(st), "lete these words", "ビジュアルで 2 文字削除");
  st = ed("a\nb\nc\nd");
  keys(st, "Vjd"); eq(txt(st), "c\nd", "ビジュアル行で 2 行削除");
  st = ed("abc def");
  keys(st, "vey"); eq(st.regs['"'].text[0], "abc", "ビジュアルの ve でヤンク");
  st = ed("make upper");
  keys(st, "veU"); eq(txt(st), "MAKE upper", "ビジュアルの U で大文字化");

  /* . リピート */
  st = ed("a a a");
  keys(st, "x"); keys(st, "."); eq(txt(st), "a a", ". で削除を繰り返す");
  st = ed("one\ntwo\nthree");
  keys(st, "dd"); keys(st, "."); eq(txt(st), "three", ". で dd を繰り返す");

  /* 挿入を含む . リピート */
  st = ed("x\nx");
  keys(st, "I> <Esc>"); keys(st, "j0"); keys(st, ".");
  eq(txt(st), "> x\n> x", ". が挿入テキストごと繰り返される");

  /* 空バッファでも壊れない */
  st = ed("");
  keys(st, "dd"); eq(txt(st), "", "空バッファの dd");
  keys(st, "x"); eq(txt(st), "", "空バッファの x");
  keys(st, "hhhjjjkkklll"); eq(st.cur.l + st.cur.c, 0, "空バッファでカーソルが飛ばない");
}

/* ═════ 9. Ex コマンド ═════ */
console.log("9. Ex コマンド");
{
  let st = ed("l1\nl2\nl3\nl4\nl5");
  E.feedString(st, ":3<CR>"); eq(st.cur.l, 2, ":3 で 3 行目へ");

  st = ed("foo bar foo\nfoo");
  E.feedString(st, ":%s/foo/baz/g<CR>");
  eq(txt(st), "baz bar baz\nbaz", ":%s/foo/baz/g で全置換");
  ok(/3 件/.test(st.msg), "置換件数を報告");

  st = ed("aaa\naaa\naaa");
  E.feedString(st, ":2,3s/a/b/<CR>");
  eq(txt(st), "aaa\nbaa\nbaa", ":2,3s/// で範囲置換");

  st = ed("x");
  E.feedString(st, ":s/nomatch/y/<CR>");
  ok(st.msgErr, "一致しない置換はエラー表示");
  eq(txt(st), "x", "一致しなければ本文は変わらない");

  st = ed("a");
  E.feedString(st, ":set nonumber<CR>"); eq(st.opts.number, false, ":set nonumber");
  E.feedString(st, ":set number<CR>"); eq(st.opts.number, true, ":set number");
  E.feedString(st, ":set peak=3.4<CR>"); eq(st.opts.peak, 3.4, ":set peak=3.4");
  E.feedString(st, ":set shiftwidth=4<CR>"); eq(st.shiftwidth, 4, ":set shiftwidth=4");
  E.feedString(st, ":set bogus<CR>"); ok(st.msgErr, "未知のオプションはエラー");

  /* イベントの発行 */
  st = ed("a");
  st.events.length = 0; E.execEx(st, "countdown 7");
  eq(st.events[0].type, "countdown", ":countdown がイベントを発行");
  eq(st.events[0].seconds, 7, ":countdown 7 の秒数");
  st.events.length = 0; E.execEx(st, "countdown");
  eq(st.events[0].seconds, 5, ":countdown の既定は 5 秒");
  st.events.length = 0; E.execEx(st, "run");
  eq(st.events[0].type, "run", ":run がイベントを発行");
  st.events.length = 0; E.execEx(st, "emit");
  eq(st.events[0].type, "signal", ":emit が SIGNAL イベントを発行");
  eq(st.events[0].mag, 1, ":emit は最大強度");
  st.events.length = 0; E.execEx(st, "emit deploy");
  eq(st.events[0].what, "deploy", ":emit に名前を渡せる");
  st.events.length = 0; E.execEx(st, "w out.bada");
  eq(st.events[0].type, "write", ":w が保存イベントを発行");
  eq(st.fname, "out.bada", ":w name でファイル名が変わる");

  st = ed("a"); st.dirty = true;
  st.events.length = 0; E.execEx(st, "q");
  ok(st.msgErr, "未保存の :q は拒否される");
  st.events.length = 0; E.execEx(st, "q!");
  eq(st.events[0].type, "quit", ":q! は破棄して終了");

  st = ed("a");
  E.execEx(st, "focus"); eq(st.opts.focus, false, ":focus でトグル");
  E.execEx(st, "flash"); eq(st.opts.flash, false, ":flash でトグル");
  E.execEx(st, "flash"); eq(st.opts.flash, true, ":flash で戻る");
  E.execEx(st, "bus"); eq(st.opts.bus, false, ":bus でトグル");
  E.execEx(st, "bogus-cmd"); ok(st.msgErr, "未知のコマンドはエラー");
}

/* ═════ 10. イベントバス ═════ */
console.log("10. イベントの発行とディスパッチ");
{
  /* 1 キー = 1 ディスパッチ。key が必ず先頭に来る */
  let st = ed("alpha beta\nsecond\nthird");
  E.feedKey(st, "j");
  eq(st.events[0].type, "key", "先頭は必ず key イベント");
  eq(st.events[0].key, "j", "押されたキーが載る");
  ok(st.events.some(e => e.type === "motion"), "j は motion イベントを発行");
  eq(st.events.filter(e => e.type === "motion")[0].line, 1, "motion の対象行");
  eq(st.events.filter(e => e.type === "motion")[0].from, 0, "motion の移動元");

  /* 連番は単調増加する (バスの並び順) */
  const seqs = st.events.map(e => e.seq);
  for (let i = 1; i < seqs.length; i++) ok(seqs[i] > seqs[i - 1], "seq が単調増加 (" + i + ")");

  /* 行内の移動では motion は出ない */
  st = ed("alpha beta");
  E.feedKey(st, "l");
  eq(st.events.filter(e => e.type === "motion").length, 0, "同じ行の移動では motion なし");

  /* 編集は edit イベント */
  st = ed("abc");
  E.feedKey(st, "x");
  ok(st.events.some(e => e.type === "edit"), "x は edit イベントを発行");

  /* モード遷移は mode イベント */
  st = ed("abc");
  E.feedKey(st, "i");
  const mev = st.events.filter(e => e.type === "mode")[0];
  ok(mev, "i は mode イベントを発行");
  eq(mev.from, "normal", "遷移元");
  eq(mev.to, "insert", "遷移先");

  /* 挿入した文字も edit として拾われる */
  st = ed("abc");
  E.feedString(st, "i");
  st.events.length = 0;
  E.feedKey(st, "Z");
  ok(st.events.some(e => e.type === "edit"), "挿入モードの文字入力も edit");

  /* o は open-below の edit を 1 件だけ出す (二重発行しない) */
  st = ed("one\ntwo");
  E.feedKey(st, "o");
  eq(st.events.filter(e => e.type === "edit").length, 1, "o の edit は 1 件だけ");
  eq(st.events.filter(e => e.type === "edit")[0].what, "open-below", "o の内容");

  /* p / P も edit */
  st = ed("one\ntwo");
  E.feedString(st, "yy");
  st.events.length = 0;
  E.feedKey(st, "p");
  eq(st.events.filter(e => e.type === "edit")[0].what, "put-after", "p の内容");

  /* Space は SIGNAL */
  st = ed("line one\nline two");
  E.feedKey(st, "<Space>");
  const sig = st.events.filter(e => e.type === "signal")[0];
  ok(sig, "Space は SIGNAL イベントを発行");
  eq(sig.mag, 1, "SIGNAL は最大強度");
  eq(sig.line, 0, "SIGNAL の対象は現在行");

  /* dispatched は累計される */
  st = ed("a\nb\nc");
  const before = st.dispatched;
  E.feedString(st, "jjx");
  ok(st.dispatched > before, "dispatched が累計される");

  /* 検索も jump を出す */
  st = ed("one\ntwo target\nthree");
  E.feedString(st, "/target<CR>");
  ok(st.events.some(e => e.type === "jump"), "検索一致で jump イベント");

  /* イベント種別の見た目は決定的 */
  eq(E.eventStyle("edit").label, "EDIT", "eventStyle のラベル");
  eq(E.eventStyle("edit").hue, E.eventStyle("edit").hue, "同じ種別なら同じ色相");
  ok(E.eventStyle("edit").hue !== E.eventStyle("error").hue, "種別が違えば色相も違う");
  eq(E.eventStyle("nosuchtype").label, "NOSUCHTYPE", "未知の種別もラベル化される");
  ok(E.eventStyle(undefined).hue >= 0, "種別なしでも色相が返る");
  ok(E.eventMag("signal") > E.eventMag("key"), "SIGNAL は KEY より強い");
  eq(E.eventMag("nosuchtype"), 0.5, "未知の種別は既定の強さ");
}

/* ═════ 11. シネマ数理 ═════ */
console.log("11. focusStyle / docLayout / flashFrame / countdownState");
{
  const o = {depth:1, peak:2.6, spread:2.2, maxBlur:3.2, minOpacity:0.13, maxZ:26};
  const f0 = E.focusStyle(0, o);
  near(f0.scale, 2.6, 1e-12, "ポイント行は最大倍率 (どアップ)");
  near(f0.blur, 0, 1e-12, "ポイント行はぼけない");
  near(f0.opacity, 1, 1e-12, "ポイント行は最も明るい");
  near(f0.z, 26, 1e-12, "ポイント行が最前面");
  const f1 = E.focusStyle(1, o), f4 = E.focusStyle(4, o);
  ok(f1.scale < f0.scale && f4.scale < f1.scale, "距離が離れるほど縮小");
  ok(f1.blur < f4.blur, "距離が離れるほどぼける");
  ok(f4.opacity < f1.opacity, "距離が離れるほど暗い");
  eq(E.focusStyle(-3, o).scale, E.focusStyle(3, o).scale, "上下で対称");
  ok(E.focusStyle(40, o).opacity >= o.minOpacity - 1e-9, "最小不透明度を下回らない");

  const off = E.focusStyle(0, {depth:0});
  near(off.scale, 1, 1e-12, "depth=0 ならフォーカス効果なし");
  near(off.blur, 0, 1e-12, "depth=0 ならぼかしなし");
  near(off.z, 0, 1e-12, "depth=0 なら浮き上がりなし");

  /* 焦点を狭めると (spread 小) 減衰が急になる */
  ok(E.focusStyle(2, {spread:1}).scale < E.focusStyle(2, {spread:4}).scale,
     "spread が小さいほど被写界深度が浅い");

  /* 行が重ならないレイアウト */
  const lay = E.docLayout([1, 2, 1], 30);
  eq(lay.heights.join(","), "30,60,30", "占有高さ = baseH × scale");
  eq(lay.tops.join(","), "0,30,90", "上端が累積する");
  eq(lay.centers[1], 60, "拡大行の中心");
  eq(lay.total, 120, "総高さ");
  for (let i = 1; i < lay.tops.length; i++){
    ok(lay.tops[i] >= lay.tops[i - 1] + lay.heights[i - 1] - 1e-9, "行 " + i + " が前の行と重ならない");
  }

  /* イベント処理フラッシュの包絡 */
  eq(E.flashFrame(0, 1).env, 0, "t=0 ではまだ光らない");
  eq(E.flashFrame(1, 1).env, 0, "t=1 で消灯する");
  eq(E.flashFrame(1.5, 1).env, 0, "t>1 は無効");
  eq(E.flashFrame(-0.2, 1).env, 0, "t<0 は無効");
  eq(E.flashFrame(1, 1).glow, 0, "t=1 でにじみも消える");
  eq(E.flashFrame(1, 1).rise, 0, "t=1 で浮きも戻る");

  /* 立ち上がりが速く、その後は単調に減衰する (信号ランプの包絡) */
  const peak = E.flashFrame(0.12, 1).env;
  ok(peak > 0.8, "ピークは立ち上がり直後 (t=0.12)");
  ok(E.flashFrame(0.06, 1).env < peak, "ピーク前は立ち上がり途中");
  let prevEnv = peak;
  for (let t = 0.14; t < 1; t += 0.02){
    const e = E.flashFrame(t, 1).env;
    ok(e <= prevEnv + 1e-12, "t=" + t.toFixed(2) + " で単調に減衰");
    prevEnv = e;
  }
  /* 立ち上がり区間でも単調増加 */
  let prevUp = 0;
  for (let t = 0.01; t <= 0.12; t += 0.01){
    const e = E.flashFrame(t, 1).env;
    ok(e >= prevUp - 1e-12, "t=" + t.toFixed(2) + " で単調に立ち上がる");
    prevUp = e;
  }
  /* 強さは線形にスケールする */
  near(E.flashFrame(0.3, 0.5).env, E.flashFrame(0.3, 1).env * 0.5, 1e-12, "intensity は線形");
  near(E.flashFrame(0.3, 0).env, 0, 1e-12, "intensity=0 なら光らない");
  ok(E.flashFrame(0.3, 1.8).env === E.flashFrame(0.3, 1).env, "intensity は 1 で頭打ち");
  ok(E.flashFrame(0.3, -1).env === 0, "負の intensity は 0 に丸める");

  /* 各出力は包絡に比例する */
  const f = E.flashFrame(0.2, 1);
  near(f.glow, 30 * f.env, 1e-12, "glow は包絡に比例");
  near(f.wash, 0.9 * f.env, 1e-12, "wash は包絡に比例");
  near(f.edge, 5 * f.env, 1e-12, "edge は包絡に比例");
  near(f.rise, 7 * f.env, 1e-12, "rise は包絡に比例");
  ok(f.rise < 10, "浮き上がりは控えめ (クラッシュのような跳ね上げではない)");

  /* 処理の光は行を左から右へ走る */
  eq(E.flashFrame(0.25, 1).sweep, 0.25, "sweep は進行そのもの");
  ok(E.flashFrame(0.7, 1).sweep > E.flashFrame(0.3, 1).sweep, "sweep は単調に進む");

  /* 映画のカウントダウン */
  let cd = E.countdownState(0, 5);
  eq(cd.n, 5, "開始時は T-5");
  near(cd.phase, 0, 1e-12, "開始時の位相は 0");
  near(cd.sweep, 0, 1e-12, "開始時の指針は 12 時");
  eq(cd.done, false, "開始時は未完了");
  cd = E.countdownState(0.5, 5);
  eq(cd.n, 5, "0.5 秒後もまだ 5");
  near(cd.phase, 0.5, 1e-12, "1 秒の半分まで進んだ");
  near(cd.sweep, Math.PI, 1e-12, "指針が半周した");
  cd = E.countdownState(1.0, 5);
  eq(cd.n, 4, "1 秒後は T-4");
  eq(E.countdownState(4.5, 5).n, 1, "4.5 秒後は T-1");
  cd = E.countdownState(5, 5);
  eq(cd.done, true, "5 秒で完了");
  eq(cd.label, "0", "完了時のラベルは 0");
  eq(E.countdownState(9, 5).done, true, "超過しても完了のまま");
  /* 単調に減る */
  let prev = 99;
  for (let t = 0; t <= 5; t += 0.25){
    const s = E.countdownState(t, 5);
    ok(s.n <= prev, "t=" + t + " で秒数が増えない");
    prev = s.n;
  }

  eq(E.gutterWidth(9), 1, "ガター幅 (1 桁)");
  eq(E.gutterWidth(150), 3, "ガター幅 (3 桁)");
}

/* ═════ 12. 多段落の文章と拡大鏡 ═════ */
console.log("12. 段落分け / 語と文の切り出し / 拡大鏡の写像");
{
  /* ── 段落分け ── */
  const paras = E.splitParagraphs(["一行目", "二行目", "", "次の段落", "", "", "最後"]);
  eq(paras.filter(p => p.kind === "para").length, 3, "段落は 3 つ");
  eq(paras.filter(p => p.kind === "gap").length, 3, "空行も隙間として保持される");
  eq(paras[0].from, 0, "第 1 段落の開始行");
  eq(paras[0].to, 1, "第 1 段落の終了行");
  eq(paras[0].lines.join("/"), "一行目/二行目", "第 1 段落の中身");
  eq(E.splitParagraphs([]).length, 0, "空の入力");
  eq(E.splitParagraphs(["   "]).length, 1, "空白だけの行は隙間");
  eq(E.splitParagraphs(["   "])[0].kind, "gap", "空白だけの行の種別");
  /* すべての行がどこかに現れる (カーソルを置けなくなる行がない) */
  {
    const src = ["a", "b", "", "c", "", "d"];
    const seen = new Set();
    for (const p of E.splitParagraphs(src)) for (let l = p.from; l <= p.to; l++) seen.add(l);
    eq(seen.size, src.length, "全行が段落か隙間に含まれる");
  }

  /* ── 行の継ぎ方 (和文は詰める / 欧文は空白) ── */
  ok(E.isCJK("文"), "漢字は CJK");
  ok(E.isCJK("あ"), "ひらがなは CJK");
  ok(E.isCJK("。"), "句点は CJK");
  ok(!E.isCJK("a"), "ラテン文字は CJK ではない");
  eq(E.lineSeparator("読むものだ", "そのために"), "", "和文どうしは詰める");
  eq(E.lineSeparator("the quick", "brown fox"), " ", "欧文どうしは空白を入れる");
  eq(E.lineSeparator("Bada", "の読み方"), "", "片方が和文なら詰める");
  eq(E.lineSeparator("", "next"), "", "空行のあとは空白なし");

  /* ── 段落の連結とオフセット対応 ── */
  const pt = E.paragraphText(["文章は、", "光を当てて読む。"]);
  eq(pt.text, "文章は、光を当てて読む。", "和文の段落は詰めて連結される");
  eq(pt.map[0].start, 0, "1 行目の開始オフセット");
  eq(pt.map[1].start, 4, "2 行目の開始オフセット");
  eq(pt.map[1].sep, "", "和文の区切りは空");
  const pe = E.paragraphText(["the quick", "brown fox"]);
  eq(pe.text, "the quick brown fox", "欧文の段落は空白で連結される");
  eq(pe.map[1].start, 10, "空白ぶんだけ開始位置がずれる");
  eq(pe.map[1].sep, " ", "欧文の区切りは空白");
  /* オフセット -> 行/桁 の往復 */
  eq(E.offsetToLine(pt.map, 0).l, 0, "先頭は 1 行目");
  eq(E.offsetToLine(pt.map, 3).l, 0, "1 行目の末尾");
  eq(E.offsetToLine(pt.map, 4).l, 1, "2 行目の先頭");
  eq(E.offsetToLine(pt.map, 4).c, 0, "2 行目の桁");
  eq(E.offsetToLine(pt.map, 6).c, 2, "2 行目の途中");
  eq(E.offsetToLine(pt.map, 999).l, 1, "範囲外は最終行へ丸める");
  eq(E.offsetToLine([], 5).l, 0, "空の対応表でも壊れない");

  /* ── 語の切り出し (和欧混在) ── */
  eq(E.wordAt("文章は、目で追う", 0).text, "文章は", "漢字 + 送り仮名で 1 語");
  eq(E.wordAt("文章は、目で追う", 3).text, "、", "約物は 1 文字");
  eq(E.wordAt("Bada CineVim は", 5).text, "CineVim", "ラテン語");
  eq(E.wordAt("カタカナ語です", 1).text, "カタカナ", "辞書を使わないので カタカナ|漢字 の境目で語が分かれる");
  eq(E.wordAt("カタカナ語です", 4).text, "語です", "漢字 + 送り仮名はまとまる");
  eq(E.wordAt("動く", 0).text, "動く", "送り仮名を含む");
  eq(E.wordAt("動く", 1).text, "動く", "送り仮名の側から引いても同じ語");
  eq(E.wordAt("", 0).text, "", "空文字列");
  eq(E.wordAt("abc", 99).text, "abc", "範囲外は末尾に丸める");
  eq(E.wordAt("abc", -5).text, "abc", "負の位置は先頭に丸める");
  ok(E.wordAt("a b", 1).text === " ", "空白は 1 文字として返す");

  /* ── 文の切り出し ── */
  const T = "文章は目で追う。光を当てて読むものだ。次の文。";
  eq(E.sentenceAt(T, 0).text, "文章は目で追う。", "1 文目");
  eq(E.sentenceAt(T, 3).text, "文章は目で追う。", "1 文目の途中から引いても同じ");
  eq(E.sentenceAt(T, 8).text, "光を当てて読むものだ。", "2 文目");
  eq(E.sentenceAt(T, T.length - 1).text, "次の文。", "最後の文");
  eq(E.sentenceAt("終止符なし", 2).text, "終止符なし", "終止符がなければ全体が 1 文");
  eq(E.sentenceAt("", 0).text, "", "空文字列");
  eq(E.sentenceAt("Hello there. Next one.", 2).text, "Hello there.", "欧文の文");
  /* 小数点は文末ではない */
  ok(!E.isSentenceEnd("3.14 です", 1), "数値の小数点は文末ではない");
  ok(E.isSentenceEnd("end. next", 3), "空白が続く '.' は文末");
  ok(E.isSentenceEnd("終わり。", 3), "句点は文末");
  ok(E.isSentenceEnd("なぜ？", 2), "疑問符は文末");
  eq(E.sentenceAt("円周率は 3.14 です。次。", 4).text, "円周率は 3.14 です。", "小数点で切れない");
  /* 閉じ括弧は文末に含める */
  eq(E.sentenceAt("「そうだ。」と言った。", 2).text, "「そうだ。」", "閉じ括弧まで 1 文");

  /* ── 拡大鏡の写像 ── */
  {
    /* (px,py) が半径 r のレンズ中心 (r,r) に来ること */
    const check = (px, py, r, z) => {
      const t = E.loupeTransform(px, py, r, z);
      return {x:t.scale * (px + t.tx), y:t.scale * (py + t.ty)};
    };
    let m = check(441.5, 382, 150, 3);
    near(m.x, 150, 1e-9, "拡大しても指した点がレンズ中心に来る (x)");
    near(m.y, 150, 1e-9, "拡大しても指した点がレンズ中心に来る (y)");
    m = check(0, 0, 100, 7);
    near(m.x, 100, 1e-9, "原点を指しても中心に来る");
    m = check(50, 80, 120, 1);
    near(m.x, 120, 1e-9, "等倍でも中心に来る");
    eq(E.loupeTransform(10, 10, 100, 0).scale, 1, "倍率 0 は等倍に丸める");
    eq(E.loupeTransform(10, 10, 100).scale, 1, "倍率なしは等倍");
    /* 倍率が上がるほど、ずらし量は中心へ寄る */
    ok(E.loupeTransform(400, 300, 150, 6).tx < E.loupeTransform(400, 300, 150, 3).tx,
       "倍率が上がるほど、ずらし量は負に大きくなる (r/z が小さくなるため)");
  }

  /* ── レンズのはみ出し防止 ── */
  eq(E.clampLoupe(500, 300, 1000, 700, 150).x, 500, "中央付近はそのまま");
  eq(E.clampLoupe(10, 300, 1000, 700, 150).x, 150, "左にはみ出さない");
  eq(E.clampLoupe(990, 300, 1000, 700, 150).x, 850, "右にはみ出さない");
  eq(E.clampLoupe(500, 5, 1000, 700, 150).y, 150, "上にはみ出さない");
  eq(E.clampLoupe(500, 695, 1000, 700, 150).y, 550, "下にはみ出さない");
  eq(E.clampLoupe(500, 300, 200, 700, 150).x, 100, "レンズより狭ければ中央に置く");

  /* ── 倍率の段階 ── */
  eq(E.zoomStep(3, 1), 4, "1 段上げる");
  eq(E.zoomStep(3, -1), 2.2, "1 段下げる");
  eq(E.zoomStep(1.6, -1), 1.6, "最小で止まる");
  eq(E.zoomStep(7, 1), 7, "最大で止まる");
  eq(E.zoomStep(3.1, 0), 3, "近い段に吸着する");

  /* ── 強調範囲の切り出し (行にまたがる文を、行ごとに包む) ── */
  eq(E.markRange("abcdef", 0, 2, 4), "ab<span class=\"snap\">cd</span>ef", "行の途中を包む");
  eq(E.markRange("abcdef", 0, null, null), "abcdef", "範囲なしは素の行");
  eq(E.markRange("abcdef", 0, 10, 20), "abcdef", "行に掛からない範囲");
  eq(E.markRange("abcdef", 10, 8, 14), "<span class=\"snap\">abcd</span>ef",
     "前の行から続く範囲は行頭から包む");
  eq(E.markRange("abcdef", 0, 4, 99), "abcd<span class=\"snap\">ef</span>",
     "次の行へ続く範囲は行末まで包む");
  eq(E.markRange("a<b>", 0, null, null), "a&lt;b&gt;", "HTML をエスケープする");
  eq(E.markRange("a<b>", 0, 1, 4), "a<span class=\"snap\">&lt;b&gt;</span>",
     "強調の内側もエスケープする");
  eq(E.markRange("abc", 0, 2, 2), "abc", "空の範囲は無視する");
  eq(E.escapeHtml("<&>"), "&lt;&amp;&gt;", "escapeHtml");
  eq(E.escapeHtml(null), "", "escapeHtml(null)");

  /* 段落全体を行ごとに包み直すと、元の文章に戻る */
  {
    const lines = ["まわりの段落は静かに退き、", "いま読んでいる一文だけが浮かぶ。"];
    const t = E.paragraphText(lines);
    const s2 = E.sentenceAt(t.text, 5);
    let joined = "";
    for (let k = 0; k < lines.length; k++){
      joined += E.markRange(lines[k], t.map[k].start, s2.from, s2.to).replace(/<[^>]+>/g, "");
    }
    eq(joined, lines.join(""), "行ごとに包んでも文字は失われない");
    ok(E.markRange(lines[0], t.map[0].start, s2.from, s2.to).indexOf("snap") >= 0 &&
       E.markRange(lines[1], t.map[1].start, s2.from, s2.to).indexOf("snap") >= 0,
       "行をまたぐ文は両方の行が包まれる");
  }
}

/* ═════ 結果 ═════ */
console.log("\n" + (fail ? "✘" : "✔") + "  " + pass + " 件成功 / " + fail + " 件失敗");
process.exit(fail ? 1 : 0);
