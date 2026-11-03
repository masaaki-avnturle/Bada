/* demo-data.js — complete.html のブラウザ プレビュー / スモークテスト用サンプル。
 * Electron (BadaSearch.exe) 実行時は実リポジトリの索引が使われ、これは未使用。
 * 論文(PDF 由来テキスト)とソースコードを模した語彙・本文です。 */
window.BADA_DEMO = {
  langs: { "Python": 1, "JavaScript": 1, "C": 1, "PDF": 1, "Markdown": 1 },
  terms: [
    { t: "kauffman",          count: 42, files: 4 },
    { t: "jonesKey",          count: 31, files: 3 },
    { t: "jones_polynomial",  count: 27, files: 2 },
    { t: "bracket",           count: 25, files: 4 },
    { t: "quantum",           count: 22, files: 3 },
    { t: "kauffmanBracket",   count: 18, files: 2 },
    { t: "diagram",           count: 15, files: 3 },
    { t: "polynomial",        count: 14, files: 2 },
    { t: "knot",              count: 12, files: 2 },
    { t: "sampling",          count:  9, files: 2 },
    { t: "量子多項式",         count:  8, files: 2 },
    { t: "量子暗号",           count:  7, files: 2 },
    { t: "結び目",             count:  6, files: 1 },
    { t: "多項式",             count:  6, files: 2 },
    { t: "encrypt",           count:  5, files: 1 },
    { t: "decrypt",           count:  5, files: 1 }
  ],
  docs: [
    { rel: "paper/jones.pdf", lang: "PDF", lines: [
      "Jones polynomial via the Kauffman bracket of a knot diagram.",
      "We compute the Kauffman bracket by state-sum sampling over crossings.",
      "The quantum polynomial invariant distinguishes the trefoil from the unknot." ] },
    { rel: "src/qcrypto.py", lang: "Python", lines: [
      "def kauffman_bracket(diagram):",
      "    # sampling states of the knot diagram",
      "    return jones_polynomial(diagram)",
      "def jonesKey(seed):",
      "    return hash(('quantum', seed))" ] },
    { rel: "web/qcrypto.js", lang: "JavaScript", lines: [
      "function jonesKey(diagram){ return kauffmanBracket(diagram); }",
      "function kauffmanBracket(d){ /* quantum bracket sampling */ return d.length; }" ] },
    { rel: "doc/notes.md", lang: "Markdown", lines: [
      "# 量子暗号メモ",
      "Kauffman ブラケットと Jones 多項式(量子多項式)で結び目から鍵を導出する。",
      "量子暗号の鍵 jonesKey は結び目図から決定論的に計算する。" ] },
    { rel: "src/aead.c", lang: "C", lines: [
      "/* encrypt / decrypt with ChaCha20 keyed by jonesKey */",
      "int encrypt(const uint8_t *key){ return 0; }",
      "int decrypt(const uint8_t *key){ return 0; }" ] }
  ]
};
