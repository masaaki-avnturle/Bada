/*
 * test-search.js — Bada Search コアの自己検査
 *   node sourcetree_search/tools/test-search.js
 *
 * 一時ディレクトリにソースコード数種 + FlateDecode 圧縮の PDF を生成して
 * インデックス→検索を検証します (依存なし・Node 標準のみ)。
 */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const zlib = require("zlib");
const core = require(path.join(__dirname, "..", "core", "searchcore.js"));

let failed = 0;
function ok(cond, label){
  console.log((cond ? "PASS" : "FAIL") + "  " + label);
  if (!cond) failed++;
}

/* ── テスト用リポジトリを作成 ── */
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "badasearch-"));
function W(rel, content){
  const p = path.join(tmp, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content);
}
W("src/main.c", '#include <stdio.h>\nint main(void){\n  printf("kauffman bracket\\n");\n  return 0;\n}\n');
W("src/app.py", "def jones_polynomial(diagram):\n    # kauffman bracket sampling\n    return hash(diagram)\n");
W("web/index.js", "function jonesKey(){ return 'quantum'; }\nconsole.log(jonesKey());\n");
W("doc/notes.md", "# メモ\nKauffman ブラケットと Jones 多項式について。\n");
W("bin/blob.dat", Buffer.from([0, 1, 2, 3, 255]));           /* バイナリ → 除外される */
fs.mkdirSync(path.join(tmp, ".git", "objects"), { recursive: true });
W(".git/config", "[core]\n  bare = false\n");                 /* .git → 除外される */

/* FlateDecode PDF を生成 (Hello Quantum Kauffman) */
function makePdf(text){
  const content = "BT /F1 12 Tf 72 720 Td (" + text + ") Tj ET";
  const flate = zlib.deflateSync(Buffer.from(content, "latin1"));
  const objs = [];
  objs.push("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");
  objs.push("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n");
  objs.push("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n");
  const head = "4 0 obj\n<< /Length " + flate.length + " /Filter /FlateDecode >>\nstream\n";
  const tail = "\nendstream\nendobj\n";
  const parts = [Buffer.from("%PDF-1.4\n", "latin1")];
  objs.forEach(function(o){ parts.push(Buffer.from(o, "latin1")); });
  parts.push(Buffer.from(head, "latin1"), flate, Buffer.from(tail, "latin1"));
  parts.push(Buffer.from("trailer\n<< /Root 1 0 R >>\n%%EOF\n", "latin1"));
  return Buffer.concat(parts);
}
fs.writeFileSync(path.join(tmp, "doc", "paper.pdf"), makePdf("Hello Quantum Kauffman bracket from PDF"));

/* ── PDF 抽出単体 ── */
const pdfText = core.extractPdfText(fs.readFileSync(path.join(tmp, "doc", "paper.pdf")));
ok(pdfText.includes("Hello Quantum Kauffman"), "extractPdfText decodes FlateDecode Tj text");

/* ── インデックス ── */
const idx = core.buildIndex(tmp);
ok(idx.files.length === 5, "index holds 5 files (4 source + 1 PDF), binaries and .git excluded — got " + idx.files.length);
ok(idx.langs["C"] === 1 && idx.langs["Python"] === 1 && idx.langs["JavaScript"] === 1 && idx.langs["PDF"] === 1,
   "language detection (C / Python / JavaScript / PDF)");

/* ── 検索: AND / 大文字小文字 / 言語フィルタ / 正規表現 ── */
const r1 = core.search(idx, "kauffman");
ok(r1.files === 4, "case-insensitive search finds kauffman in 4 files (C/Python/Markdown/PDF) — got " + r1.files);
ok(r1.hits.some(function(h){ return h.lang === "PDF"; }), "PDF content is searchable");
ok(r1.hits.every(function(h){ return h.matches[0].line >= 1; }), "hits carry line numbers");

const r2 = core.search(idx, "kauffman bracket sampling");
ok(r2.files === 1 && r2.hits[0].lang === "Python", "AND search narrows to the Python file");

const r3 = core.search(idx, "kauffman", { lang: "PDF" });
ok(r3.files === 1 && r3.hits[0].rel === "doc/paper.pdf", "language filter lang=PDF");

const r4 = core.search(idx, "jones(Key|_polynomial)", { regex: true });
ok(r4.files === 2, "regex search matches jonesKey and jones_polynomial — got " + r4.files);

const r5 = core.search(idx, "Kauffman", { caseSensitive: true });
ok(r5.files === 2, "case-sensitive search only matches capitalized Kauffman (md + PDF) — got " + r5.files);

const r6 = core.search(idx, "kauffman", { pathFilter: "src/" });
ok(r6.files === 2, "path filter src/ narrows to source dir");

ok(core.search(idx, "no-such-token-xyz").files === 0, "no false positives");
let threw = false;
try { core.search(idx, "([", { regex: true }); } catch (e){ threw = true; }
ok(threw, "invalid regex reports an error");

/* ── CJK 検索 (Markdown) ── */
const r7 = core.search(idx, "多項式");
ok(r7.files === 1 && r7.hits[0].rel === "doc/notes.md", "Japanese text search works");

/* ── リポジトリ実物の PDF でも落ちない (テキスト有無は問わない) ── */
const repoPdf = path.join(__dirname, "..", "..", "Bada#.pdf");
if (fs.existsSync(repoPdf)){
  let t = null, crashed = false;
  try { t = core.extractPdfText(fs.readFileSync(repoPdf)); } catch (e){ crashed = true; }
  ok(!crashed, "real-world PDF (Bada#.pdf) is handled without crashing" + (t && t.trim() ? " (text extracted)" : " (no text layer)"));
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(failed === 0 ? "\nALL SEARCH TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
