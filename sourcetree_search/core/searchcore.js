/*
 * searchcore.js — Bada Search (SourceTree 付属の PDF・ソースコード検索エンジン)
 *
 * リポジトリ ツリーを走査して
 *   ・プログラミング言語のソースコード (拡張子で言語判定, UTF-8 テキスト)
 *   ・PDF (FlateDecode ストリームを zlib で伸長し Tj/TJ オペレータから
 *     テキストを抽出 — 依存ライブラリなし)
 * をインデックスし、AND 検索 / 正規表現検索を行番号つきで返します。
 * Node 標準モジュール (fs / path / zlib) のみに依存。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

/* ── 言語判定 (拡張子 → 言語名) ── */
const LANGS = {
  ".c": "C", ".h": "C/C++ header", ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++ header",
  ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript (JSX)",
  ".ts": "TypeScript", ".tsx": "TypeScript (TSX)",
  ".py": "Python", ".rb": "Ruby", ".java": "Java", ".go": "Go", ".rs": "Rust",
  ".php": "PHP", ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
  ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".bat": "Batch",
  ".pl": "Perl", ".pm": "Perl", ".lua": "Lua", ".sql": "SQL", ".r": "R",
  ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".xml": "XML", ".json": "JSON",
  ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".ini": "INI",
  ".md": "Markdown", ".txt": "Text", ".tex": "TeX/LaTeX", ".csv": "CSV",
  ".om": "OmegaScript", ".bada": "Bada", ".erb": "ERB", ".vue": "Vue",
  ".gradle": "Gradle", ".mk": "Makefile", ".cmake": "CMake",
  ".pdf": "PDF"
};
const SKIP_DIRS = new Set([".git", "node_modules", "dist", "out", "build", ".gradle",
  "__pycache__", ".idea", ".vscode", "platforms", "plugins", ".cache", "vendor"]);
const MAX_FILE = 8 * 1024 * 1024;      /* 8MB 超は読まない */
const MAX_FILES = 20000;

function langOf(file){
  const base = path.basename(file).toLowerCase();
  if (base === "makefile") return "Makefile";
  if (base === "dockerfile") return "Dockerfile";
  if (base === "rakefile" || base === "gemfile") return "Ruby";
  return LANGS[path.extname(base)] || null;
}

/* ── PDF テキスト抽出 ─────────────────────────────────────────── */
function pdfLiteralUnescape(s){
  let out = "", i = 0;
  while (i < s.length){
    const ch = s[i];
    if (ch !== "\\"){ out += ch; i++; continue; }
    const n = s[i + 1];
    if (n === "n") out += "\n";
    else if (n === "r") out += "\r";
    else if (n === "t") out += "\t";
    else if (n === "b" || n === "f") out += "";
    else if (n === "(" || n === ")" || n === "\\") out += n;
    else if (/[0-7]/.test(n || "")){
      const oct = s.substr(i + 1, 3).match(/^[0-7]{1,3}/)[0];
      out += String.fromCharCode(parseInt(oct, 8) & 0xff);
      i += oct.length - 1;
    }
    i += 2;
  }
  return out;
}
function pdfHexToText(hex){
  const clean = hex.replace(/[^0-9a-fA-F]/g, "");
  const bytes = [];
  for (let i = 0; i + 1 < clean.length; i += 2) bytes.push(parseInt(clean.substr(i, 2), 16));
  /* UTF-16BE (BOM FE FF) なら 2 バイトずつ */
  if (bytes.length >= 2 && bytes[0] === 0xfe && bytes[1] === 0xff){
    let s = "";
    for (let i = 2; i + 1 < bytes.length; i += 2) s += String.fromCharCode((bytes[i] << 8) | bytes[i + 1]);
    return s;
  }
  return bytes.map(function(b){ return String.fromCharCode(b); }).join("");
}
function extractTextOps(content){
  /* content stream 内の (…)Tj / (…)' / [ … ]TJ / <hex>Tj を拾う。
     各選択肢は重複のない線形パターン (バックトラッキング爆発防止)。 */
  const parts = [];
  const re = /\(((?:\\.|[^\\()])*)\)\s*(Tj|')|\[((?:\\.|[^\]\\])*)\]\s*TJ|<([0-9a-fA-F\s]+)>\s*Tj/g;
  let m;
  while ((m = re.exec(content))){
    if (m[1] !== undefined) parts.push(pdfLiteralUnescape(m[1]));
    else if (m[3] !== undefined){
      const inner = m[3];
      const re2 = /\(((?:\\.|[^\\()])*)\)|<([0-9a-fA-F\s]+)>/g;
      let mm;
      while ((mm = re2.exec(inner))){
        if (mm[1] !== undefined) parts.push(pdfLiteralUnescape(mm[1]));
        else parts.push(pdfHexToText(mm[2]));
      }
    }
    else if (m[4] !== undefined) parts.push(pdfHexToText(m[4]));
  }
  /* BT…ET ブロック間・TJ 間は空白で継ぐ */
  return parts.join(" ");
}
function extractPdfText(buf){
  const texts = [];
  const raw = buf.toString("latin1");
  let idx = 0;
  while (true){
    const s = raw.indexOf("stream", idx);
    if (s < 0) break;
    const e = raw.indexOf("endstream", s);
    if (e < 0) break;
    /* stream キーワード直後の EOL をスキップ */
    let start = s + 6;
    if (raw[start] === "\r") start++;
    if (raw[start] === "\n") start++;
    const dictStart = raw.lastIndexOf("<<", s);
    const dict = dictStart >= 0 ? raw.slice(dictStart, s) : "";
    const body = buf.slice(start, e);
    let content = null;
    if (/\/FlateDecode/.test(dict)){
      try { content = zlib.inflateSync(body).toString("latin1"); }
      catch (err){
        try { content = zlib.inflateRawSync(body).toString("latin1"); } catch (e2) { content = null; }
      }
    } else if (!/\/Filter/.test(dict)){
      content = body.toString("latin1");
    }
    if (content && content.length > 4 * 1024 * 1024) content = content.slice(0, 4 * 1024 * 1024);
    if (content && /\b(Tj|TJ|BT)\b/.test(content)){
      const t = extractTextOps(content);
      if (t.trim()) texts.push(t);
    }
    idx = e + 9;
  }
  return texts.join("\n");
}

/* ── インデックス構築 ─────────────────────────────────────────── */
function buildIndex(rootDir, opts){
  opts = opts || {};
  const files = [];
  const errors = [];
  let scanned = 0;
  function walk(dir){
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
    catch (e){ errors.push(dir + ": " + e.message); return; }
    for (const ent of entries){
      if (files.length >= MAX_FILES) return;
      const full = path.join(dir, ent.name);
      if (ent.isDirectory()){
        if (!SKIP_DIRS.has(ent.name)) walk(full);
        continue;
      }
      if (!ent.isFile()) continue;
      const lang = langOf(ent.name);
      if (!lang) continue;
      scanned++;
      let stat;
      try { stat = fs.statSync(full); } catch (e){ continue; }
      if (stat.size > MAX_FILE) continue;
      try {
        let text;
        if (lang === "PDF"){
          text = extractPdfText(fs.readFileSync(full));
          if (!text.trim()) continue;   /* テキストを取れない PDF (画像のみ等) は飛ばす */
        } else {
          const buf = fs.readFileSync(full);
          if (buf.includes(0)) continue;  /* バイナリ */
          text = buf.toString("utf8");
        }
        files.push({
          path: full,
          rel: path.relative(rootDir, full).split(path.sep).join("/"),
          lang: lang,
          size: stat.size,
          lines: text.split(/\r?\n/)
        });
      } catch (e){ errors.push(full + ": " + e.message); }
    }
  }
  walk(rootDir);
  const langs = {};
  files.forEach(function(f){ langs[f.lang] = (langs[f.lang] || 0) + 1; });
  return { root: rootDir, files: files, scanned: scanned, errors: errors, langs: langs, builtAt: new Date().toISOString() };
}

/* ── 検索 ─────────────────────────────────────────────────────── */
function makeMatchers(query, opts){
  opts = opts || {};
  if (opts.regex){
    try { return [new RegExp(query, opts.caseSensitive ? "" : "i")]; }
    catch (e){ throw new Error("正規表現エラー: " + e.message); }
  }
  const terms = String(query).split(/\s+/).filter(Boolean);
  return terms.map(function(t){
    const escd = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(escd, opts.caseSensitive ? "" : "i");
  });
}
function search(index, query, opts){
  opts = opts || {};
  if (!query || !String(query).trim()) return { query: query, hits: [], total: 0 };
  const matchers = makeMatchers(query, opts);
  const langFilter = opts.lang || null;      /* 言語名 or "PDF" or null */
  const maxHits = opts.maxHits || 500;
  const hits = [];
  let total = 0;
  for (const f of index.files){
    if (langFilter && f.lang !== langFilter) continue;
    if (opts.pathFilter && f.rel.toLowerCase().indexOf(String(opts.pathFilter).toLowerCase()) < 0) continue;
    /* ファイル全体で全 term が出現する (AND) ことを先に確認 */
    const whole = f.lines.join("\n");
    if (!matchers.every(function(m){ return m.test(whole); })) continue;
    const fileHits = [];
    for (let ln = 0; ln < f.lines.length; ln++){
      const line = f.lines[ln];
      const hitTerm = matchers.find(function(m){ return m.test(line); });
      if (!hitTerm) continue;
      fileHits.push({ line: ln + 1, text: line.length > 400 ? line.slice(0, 400) + "…" : line });
      if (fileHits.length >= 50) break;
    }
    if (!fileHits.length) continue;
    total += fileHits.length;
    hits.push({ path: f.path, rel: f.rel, lang: f.lang, count: fileHits.length, matches: fileHits });
    if (hits.length >= maxHits) break;
  }
  hits.sort(function(a, b){ return b.count - a.count; });
  return { query: query, hits: hits, total: total, files: hits.length };
}

/* ── 単語補完エンジン (広島大学病院の薬剤検索のようなインクリメンタル補完) ──
 *
 * インデックス済みの論文 (PDF テキスト) とソースコードから「単語」を抽出して
 * 語彙 (vocabulary) を作り、入力途中の文字列に対して補完候補をランク付きで
 * 返します。候補を選ぶと、その語で本文・コードを横断検索できます。
 *   ・ASCII 識別子/単語: [A-Za-z_][A-Za-z0-9_]+  (例 jonesKey, jones_polynomial)
 *   ・和文の語: ひらがな/カタカナ/漢字の連続 (例 量子多項式)
 * 補完は「前方一致」を最優先し、足りなければ「部分一致」で補います
 * (頻度の高い順)。薬剤名検索と同じく、数文字打つだけで候補が絞り込まれます。
 */
function tokenizeLine(line){
  var toks = [];
  var m;
  var reA = /[A-Za-z_][A-Za-z0-9_]+/g;                       /* 英数字識別子 (len>=2) */
  while ((m = reA.exec(line))) toks.push(m[0]);
  var reJ = /[぀-ゟ゠-ヿ㐀-鿿豈-﫿ｦ-ﾟ]+/g; /* 和文の連続 */
  while ((m = reJ.exec(line))) toks.push(m[0]);
  return toks;
}
function buildVocab(index, opts){
  opts = opts || {};
  var minLen = opts.minLen || 2;
  var maxTermLen = opts.maxTermLen || 48;
  var maxTerms = opts.maxTerms || 120000;
  var map = new Map();                                       /* lower -> entry */
  (index.files || []).forEach(function(f){
    var localSeen = new Set();                               /* ファイル内の重複除去 (files 計上用) */
    for (var i = 0; i < f.lines.length; i++){
      var toks = tokenizeLine(f.lines[i]);
      for (var j = 0; j < toks.length; j++){
        var t = toks[j];
        if (t.length < minLen || t.length > maxTermLen) continue;
        var key = t.toLowerCase();
        var e = map.get(key);
        if (!e){ e = { lower: key, count: 0, files: 0, casings: Object.create(null) }; map.set(key, e); }
        e.count++;
        e.casings[t] = (e.casings[t] || 0) + 1;
        if (!localSeen.has(key)){ e.files++; localSeen.add(key); }
      }
    }
  });
  /* 頻度降順に整列し、代表表記 (最頻ケーシング) を決めて配列化 */
  var terms = [];
  map.forEach(function(e){
    var disp = e.lower, best = -1;
    for (var c in e.casings){ if (e.casings[c] > best){ best = e.casings[c]; disp = c; } }
    terms.push({ t: disp, lower: e.lower, count: e.count, files: e.files });
  });
  terms.sort(function(a, b){ return b.count - a.count || (a.lower < b.lower ? -1 : 1); });
  if (terms.length > maxTerms) terms = terms.slice(0, maxTerms);
  return { terms: terms, size: terms.length, builtAt: new Date().toISOString() };
}
function complete(vocab, prefix, opts){
  opts = opts || {};
  var limit = opts.limit || 30;
  var terms = (vocab && vocab.terms) || [];
  var p = String(prefix == null ? "" : prefix).trim().toLowerCase();
  if (!p) return { prefix: prefix, items: terms.slice(0, limit).map(clone), total: terms.length };
  var pre = [], sub = [];
  for (var i = 0; i < terms.length; i++){
    var idx = terms[i].lower.indexOf(p);
    if (idx === 0) pre.push(terms[i]);
    else if (idx > 0 && sub.length < limit * 8) sub.push(terms[i]);
  }
  /* terms は既に頻度降順なので pre/sub もその順。前方一致を優先。 */
  var items = pre.slice(0, limit).map(clone);
  for (var k = 0; k < items.length; k++) items[k].kind = "prefix";
  if (items.length < limit){
    var extra = sub.slice(0, limit - items.length).map(clone);
    for (var n = 0; n < extra.length; n++) extra[n].kind = "substr";
    items = items.concat(extra);
  }
  return { prefix: prefix, items: items, total: pre.length + sub.length };
  function clone(e){ return { t: e.t, lower: e.lower, count: e.count, files: e.files }; }
}

module.exports = {
  LANGS: LANGS,
  langOf: langOf,
  extractPdfText: extractPdfText,
  buildIndex: buildIndex,
  search: search,
  tokenizeLine: tokenizeLine,
  buildVocab: buildVocab,
  complete: complete
};
