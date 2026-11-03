/*
 * test-cinevim.js — BadaCineVim エンジンの自己検査
 *   node sourcetree_search/tools/test-cinevim.js
 *
 * UI を使わず、純粋ロジック (createEditor / feed) だけを検証します。
 */
"use strict";
var path = require("path");
var CV = require(path.join(__dirname, "..", "app", "www", "cinevim.js"));

var failed = 0;
function ok(cond, label){ console.log((cond ? "PASS" : "FAIL") + "  " + label); if (!cond) failed++; }
function feedAll(ed, keys){ keys.forEach(function(k){ CV.feed(ed, k); }); }

/* ── 初期状態 ── */
var ed = CV.createEditor(["abc", "defgh", "ij"]);
ok(ed.mode === "normal" && ed.cx === 0 && ed.cy === 0, "createEditor starts NORMAL at 0,0");

/* ── 基本移動 + クランプ ── */
CV.feed(ed, "j"); ok(ed.cy === 1, "j moves down");
CV.feed(ed, "l"); ok(ed.cx === 1, "l moves right");
CV.feed(ed, "k"); ok(ed.cy === 0, "k moves up");
ok(ed.cx === 1, "column kept when moving up (within short line it clamps)");
CV.feed(ed, "h"); ok(ed.cx === 0, "h moves left");
feedAll(ed, ["j", "j", "j", "j"]); ok(ed.cy === 2, "j clamps at last line");
CV.feed(ed, "$"); ok(ed.cx === 1, "$ goes to end of 'ij' (col 1)");
CV.feed(ed, "0"); ok(ed.cx === 0, "0 goes to col 0");

/* ── 単語移動 ── */
var ew = CV.createEditor(["foo bar  baz"]);
CV.feed(ew, "w"); ok(ew.cx === 4, "w jumps to next word 'bar' (col 4) — got " + ew.cx);
CV.feed(ew, "w"); ok(ew.cx === 9, "w skips extra spaces to 'baz' (col 9) — got " + ew.cx);
CV.feed(ew, "b"); ok(ew.cx === 4, "b jumps back to 'bar' (col 4) — got " + ew.cx);

/* ── gg / G ── */
var eg = CV.createEditor(["l1", "l2", "l3", "l4"]);
CV.feed(eg, "G"); ok(eg.cy === 3, "G goes to last line");
feedAll(eg, ["g", "g"]); ok(eg.cy === 0, "gg goes to first line");

/* ── x / dd ── */
var ex = CV.createEditor(["hello", "world"]);
CV.feed(ex, "x"); ok(ex.lines[0] === "ello" && ex.dirty, "x deletes char under cursor");
feedAll(ex, ["d", "d"]); ok(ex.lines.length === 1 && ex.lines[0] === "world", "dd deletes the current line");

/* ── 挿入 ── */
var ei = CV.createEditor(["cat"]);
CV.feed(ei, "i"); ok(ei.mode === "insert", "i enters INSERT");
feedAll(ei, ["X", "Y"]); ok(ei.lines[0] === "XYcat", "typing inserts before cursor");
CV.feed(ei, "Esc"); ok(ei.mode === "normal", "Esc returns to NORMAL");
CV.feed(ei, "A"); feedAll(ei, ["!", "Esc"]); ok(ei.lines[0] === "XYcat!", "A appends at end of line");
CV.feed(ei, "o"); ok(ei.mode === "insert" && ei.lines.length === 2 && ei.cy === 1, "o opens a new line below in INSERT");

/* ── Enter で改行 / Backspace で結合 ── */
var en = CV.createEditor(["abcd"]);
CV.feed(en, "l"); CV.feed(en, "l"); CV.feed(en, "i");   /* cursor at col 2 */
CV.feed(en, "Enter"); ok(en.lines.length === 2 && en.lines[0] === "ab" && en.lines[1] === "cd", "Enter splits the line");
CV.feed(en, "Backspace"); ok(en.lines.length === 1 && en.lines[0] === "abcd", "Backspace at col 0 joins lines");

/* ── 検索 (/ + n/N) ── */
var es = CV.createEditor(["alpha", "beta kappa", "gamma", "kappa end"]);
feedAll(es, ["/", "k", "a", "p", "p", "a", "Enter"]);
ok(es.cy === 1 && es.lastSearch === "kappa", "/kappa finds first match on line 2 — got line " + (es.cy + 1));
CV.feed(es, "n"); ok(es.cy === 3, "n jumps to next match (line 4)");
CV.feed(es, "N"); ok(es.cy === 1, "N jumps back to previous match (line 2)");
var sig = CV.feed(es, "n");   /* wraps; still fine */
ok(CV.createEditor(["x"]).lastSearch === "", "fresh editor has empty lastSearch");

/* ── ex コマンド ── */
var ec = CV.createEditor(["a", "b", "c", "d", "e"]);
feedAll(ec, [":", "3", "Enter"]); ok(ec.cy === 2, ":3 jumps to line 3");
var sv = (function(){ CV.feed(ec, ":"); CV.feed(ec, "w"); return CV.feed(ec, "Enter"); })();
ok(sv && sv.type === "save", ":w returns a save signal");
var cl = (function(){ CV.feed(ec, ":"); CV.feed(ec, "q"); return CV.feed(ec, "Enter"); })();
ok(cl && cl.type === "close", ":q returns a close signal");
var wq = (function(){ CV.feed(ec, ":"); CV.feed(ec, "w"); CV.feed(ec, "q"); return CV.feed(ec, "Enter"); })();
ok(wq && wq.type === "savequit", ":wq returns a savequit signal");

/* ── 読み取り専用 (PDF 等) ── */
var er = CV.createEditor(["read only text"], { readonly: true });
CV.feed(er, "i"); ok(er.mode === "normal", "readonly blocks INSERT (i ignored)");
CV.feed(er, "x"); ok(er.lines[0] === "read only text", "readonly blocks x (no delete)");
var ro = (function(){ CV.feed(er, ":"); CV.feed(er, "w"); return CV.feed(er, "Enter"); })();
ok(ro && ro.type === "readonly", ":w on readonly returns readonly signal (no save)");

/* ── 検索語の事前設定 + gotoLine 相当 (open が使う初期化) ── */
var ep = CV.createEditor(["one", "two kappa", "three"], { search: "kappa" });
ok(ep.lastSearch === "kappa", "createEditor accepts an initial search term");

console.log(failed === 0 ? "\nALL CINEVIM TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
