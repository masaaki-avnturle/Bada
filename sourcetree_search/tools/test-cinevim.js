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

/* ── undo / redo (u / Ctrl-r) ── */
var eu = CV.createEditor(["one", "two", "three"]);
CV.feed(eu, "x"); ok(eu.lines[0] === "ne", "x deletes (before undo)");
CV.feed(eu, "u"); ok(eu.lines[0] === "one", "u undoes x");
CV.feed(eu, "Ctrl-r"); ok(eu.lines[0] === "ne", "Ctrl-r redoes x");
CV.feed(eu, "u");
feedAll(eu, ["i", "A", "B", "Enter", "C", "Esc"]);
ok(eu.lines.length === 4 && eu.lines[0] === "AB" && eu.lines[1] === "Cone", "insert session typed 'AB<CR>C'");
CV.feed(eu, "u"); ok(eu.lines.length === 3 && eu.lines[0] === "one", "one u undoes the whole insert session");
feedAll(eu, ["d", "d"]); ok(eu.lines.join("|") === "two|three", "dd removed the first line");
CV.feed(eu, "u"); ok(eu.lines.join("|") === "one|two|three", "u restores the deleted line");
var eu2 = CV.createEditor(["keep"]);
feedAll(eu2, ["i", "Esc"]); ok(eu2.undo.length === 0, "an insert that typed nothing leaves no undo step");
CV.feed(eu2, "u"); ok(/戻せません/.test(eu2.status), "u with empty history reports it");
feedAll(eu2, ["o", "x", "Esc", "u", "A", "!", "Esc"]); ok(eu2.redo.length === 0, "a new edit clears the redo stack");

/* ── yank / paste (yy / p / P、dd も取り込む) ── */
var ey = CV.createEditor(["alpha", "beta", "gamma"]);
feedAll(ey, ["y", "y", "j", "p"]);
ok(ey.lines.join("|") === "alpha|beta|alpha|gamma" && ey.cy === 2, "yy then p pastes the line below the cursor");
feedAll(ey, ["g", "g", "d", "d", "G", "p"]);
ok(ey.lines.join("|") === "beta|alpha|gamma|alpha", "dd yanks too: dd … G p moves a line to the end");
feedAll(ey, ["g", "g", "P"]);
ok(ey.lines[0] === "alpha" && ey.lines[1] === "beta" && ey.cy === 0, "P pastes above the cursor");
CV.feed(ey, "u"); ok(ey.lines[0] === "beta", "paste is undoable");
var ep = CV.createEditor(["z"]);
CV.feed(ep, "p"); ok(ep.lines.length === 1 && /ヤンク/.test(ep.status), "p with an empty register does nothing");

/* ── 未保存のまま :q は閉じない (:q! で破棄) ── */
var eq = CV.createEditor(["data"]);
CV.feed(eq, "x");
feedAll(eq, [":", "q"]); var sq = CV.feed(eq, "Enter");
ok(sq && sq.type === "dirty", ":q on a modified buffer is refused — got " + (sq && sq.type));
feedAll(eq, [":", "q", "!"]); var sq2 = CV.feed(eq, "Enter");
ok(sq2 && sq2.type === "close", ":q! discards and closes");

/* ── 読み取り専用では undo / paste / yank 後の貼り付けも不可 ── */
var er = CV.createEditor(["ro line"], { readonly: true });
feedAll(er, ["y", "y", "p", "u"]);
ok(er.lines.length === 1 && !er.dirty, "readonly buffer: p / u do not modify");

/* ── まとまった文字列の入力 (IME 確定・貼り付け・ソフトキーボード) ── */
var et = CV.createEditor(["ab"]);
ok(CV.typeText(et, "量子") === false && et.lines[0] === "ab", "typeText is ignored in NORMAL mode (pasted text never runs as commands)");
CV.feed(et, "a");
CV.typeText(et, "量子メモ"); ok(et.lines[0] === "a量子メモb" && et.cx === 5 && et.dirty, "typeText inserts an IME string at the cursor");
CV.typeText(et, "一行目\r\n二行目"); ok(et.lines.length === 2 && et.lines[0] === "a量子メモ一行目" && et.lines[1] === "二行目b", "typeText splits pasted text on newlines");
CV.feed(et, "Esc"); CV.feed(et, "u"); ok(et.lines.join("|") === "ab", "the whole typed/pasted insert is one undo step");
CV.feed(et, "/"); CV.typeText(et, "多項式"); ok(et.cmd === "/多項式", "typeText feeds the command line (Japanese / search)");
var es2 = CV.createEditor(["alpha", "量子多項式の例", "omega"]);
CV.feed(es2, "/"); CV.typeText(es2, "多項式"); CV.feed(es2, "Enter");
ok(es2.cy === 1 && es2.cx === 2, "Japanese search typed through typeText jumps to the match");
var ero = CV.createEditor(["x"], { readonly: true }); ero.mode = "insert";
ok(CV.typeText(ero, "y") === false && ero.lines[0] === "x", "typeText never edits a readonly buffer");

console.log(failed === 0 ? "\nALL CINEVIM TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
