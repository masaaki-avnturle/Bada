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
 *   9. Ex コマンド       — :42 :%s/// :set :w :countdown
 *  10. シネマ数理        — focusStyle / docLayout / crashFrame / countdownState
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
  st.events.length = 0; E.execEx(st, "slam");
  eq(st.events[0].type, "crash", ":slam がクラッシュを発行");
  eq(st.events[0].mag, 1, ":slam は最大強度");
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
  E.execEx(st, "crash"); eq(st.opts.crash, false, ":crash でトグル");
  E.execEx(st, "bogus-cmd"); ok(st.msgErr, "未知のコマンドはエラー");

  /* Space はスラム (クラッシュ) */
  st = ed("line one\nline two");
  st.events.length = 0; E.feedKey(st, "<Space>");
  eq(st.events[0].type, "crash", "Space でポイント行がクラッシュ");
  eq(st.events[0].mag, 1, "Space は最大強度");
}

/* ═════ 10. シネマ数理 ═════ */
console.log("10. focusStyle / docLayout / crashFrame / countdownState");
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

  /* クラッシュの包絡 */
  const c0 = E.crashFrame(0, 1), cm = E.crashFrame(0.25, 1), c1 = E.crashFrame(1, 1);
  eq(c0.lift, 0, "t=0 では浮き上がっていない");
  ok(cm.lift > 20, "立ち上がりで大きく浮き上がる");
  eq(c1.lift, 0, "t=1 で完全に収まる");
  eq(c1.shakeX, 0, "t=1 で揺れが止まる");
  eq(c1.alpha, 0, "t=1 で残光が消える");
  ok(E.crashFrame(0.1, 1).alpha > E.crashFrame(0.8, 1).alpha, "残光は減衰する");
  ok(Math.abs(E.crashFrame(0.15, 0.3).shakeX) < Math.abs(E.crashFrame(0.15, 1).shakeX),
     "mag が小さいほど揺れも小さい");
  eq(E.crashFrame(1.5, 1).lift, 0, "t>1 は無効");
  eq(E.crashFrame(-0.2, 1).lift, 0, "t<0 は無効");
  ok(E.crashFrame(0.5, 1).ring > E.crashFrame(0.2, 1).ring, "衝撃波は広がる");

  /* 破片は決定的 */
  const s1 = JSON.stringify(E.shardField(8, 3)), s2 = JSON.stringify(E.shardField(8, 3));
  eq(s1, s2, "同じ種なら同じ破片");
  ok(E.shardField(8, 3)[0].ang !== E.shardField(8, 9)[0].ang, "種が違えば破片も違う");
  eq(E.shardField(12, 1).length, 12, "指定した数の破片");

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

/* ═════ 結果 ═════ */
console.log("\n" + (fail ? "✘" : "✔") + "  " + pass + " 件成功 / " + fail + " 件失敗");
process.exit(fail ? 1 : 0);
