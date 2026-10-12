/*
 * engine.js — BadaGPT電信 (BadaGPT Telegraph) の純ロジック
 *             (DOM 非依存・Node でテスト可能)
 *
 *   BADA グラビトン電信 (bada_telegraph) の電信エンジン —
 *     Bada インタプリタ / ガンマ・ベータ不変量 Ξ / Jones 多項式 / モールス /
 *     FSK 音響モデム —
 *   の上に、BadaGPT の「思考入力 → 全体把握 → 計画 → 生成 → 検証 → 論文」
 *   パイプラインを載せたもの。
 *
 *   1. バイト列 / ZIP / PDF / Markdown
 *   2. 電信エンジン (Bada 数理・インタプリタ・Jones・モールス・FSK)
 *   3. 全体把握 (comprehend) — 依頼文を節に分け、全ての節を仕様の要素へ対応付ける
 *   4. 生成 (generateApp) — モジュールを組み合わせて自己完結 HTML アプリを作る
 *   5. 検証 (verifyApp)
 *   6. 論文 (writePaper)
 *   7. 生成アプリの APK / Windows / Linux ビルド一式 (projectFiles)
 *   8. Claude API (任意) — リクエスト本体 / SSE / HTML 抽出
 *
 * 正直な範囲: 「思考入力」は文章・音声・電信 (FSK 音) で入力された依頼文です。
 * 脳の信号を読む機能はありません。グラビトン↔電磁波・量子テレポーテーションの
 * 数値は山口フレームワークに基づく創作・思考実験の可視化で、
 * 依頼文の解析・アプリ生成・検証・論文・FSK 音響通信は実際に動作します。
 */
"use strict";

var BGT_VERSION = "1.0.0";

/* ═════════════════════ 1. バイト列 / ZIP / PDF / Markdown ═════════════════════ */

function utf8(str) { return new TextEncoder().encode(String(str)); }

function concatBytes(chunks) {
  var n = 0, i;
  for (i = 0; i < chunks.length; i++) n += chunks[i].length;
  var out = new Uint8Array(n), off = 0;
  for (i = 0; i < chunks.length; i++) { out.set(chunks[i], off); off += chunks[i].length; }
  return out;
}

var CRC_TABLE = (function () {
  var t = new Uint32Array(256);
  for (var n = 0; n < 256; n++) {
    var c = n;
    for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(bytes) {
  var c = 0xFFFFFFFF;
  for (var i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function base64ToBytes(b64) {
  var s = atob(b64), out = new Uint8Array(s.length);
  for (var i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

/* ZIP (無圧縮 store・UTF-8 ファイル名・固定日時で再現性あり) */
function zipBuild(files) {
  var locals = [], centrals = [], offset = 0;
  function u16(v) { return [v & 0xFF, (v >>> 8) & 0xFF]; }
  function u32(v) { return [v & 0xFF, (v >>> 8) & 0xFF, (v >>> 16) & 0xFF, (v >>> 24) & 0xFF]; }
  files.forEach(function (f) {
    var name = utf8(f.path);
    var data = typeof f.data === "string" ? utf8(f.data) : f.data;
    var crc = crc32(data);
    var head = [].concat(u16(20), u16(0x0800), u16(0), u16(0), u16(0x21),
                         u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0));
    var local = concatBytes([new Uint8Array([0x50, 0x4B, 0x03, 0x04].concat(head)), name, data]);
    locals.push(local);
    centrals.push(concatBytes([new Uint8Array([0x50, 0x4B, 0x01, 0x02].concat(u16(20), head,
                              u16(0), u16(0), u16(0), u32(0), u32(offset))), name]));
    offset += local.length;
  });
  var cd = concatBytes(centrals);
  var end = new Uint8Array([0x50, 0x4B, 0x05, 0x06].concat(u16(0), u16(0), u16(files.length),
                           u16(files.length), u32(cd.length), u32(offset), u16(0)));
  return concatBytes(locals.concat([cd, end]));
}

/* PDF: pages = [{ jpeg: Uint8Array, w, h }] → A4 (595×842pt)。
 * 日本語は端末のフォントで canvas に描いた画像として埋め込む。 */
function pdfFromJpegs(pages, title) {
  var PW = 595, PH = 842, parts = [], offsets = [], pos = 0;
  function push(b) { parts.push(b); pos += b.length; }
  function obj(num, bytes) { offsets[num] = pos; push(bytes); }
  push(utf8("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"));
  var n = pages.length, kids = [];
  for (var i = 0; i < n; i++) kids.push((4 + i * 3) + " 0 R");
  obj(1, utf8("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"));
  obj(2, utf8("2 0 obj\n<< /Type /Pages /Kids [" + kids.join(" ") + "] /Count " + n + " >>\nendobj\n"));
  var t = String(title || "BadaGPT Telegraph").replace(/[^\x20-\x7E]/g, "?").replace(/[()\\]/g, "");
  obj(3, utf8("3 0 obj\n<< /Title (" + t + ") /Producer (BadaGPT Telegraph " + BGT_VERSION + ") >>\nendobj\n"));
  pages.forEach(function (p, i) {
    var pn = 4 + i * 3, cn = pn + 1, im = pn + 2;
    obj(pn, utf8(pn + " 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + PW + " " + PH + "] " +
                 "/Resources << /XObject << /Im" + i + " " + im + " 0 R >> >> /Contents " + cn + " 0 R >>\nendobj\n"));
    var content = "q " + PW + " 0 0 " + PH + " 0 0 cm /Im" + i + " Do Q";
    obj(cn, utf8(cn + " 0 obj\n<< /Length " + content.length + " >>\nstream\n" + content + "\nendstream\nendobj\n"));
    offsets[im] = pos;
    push(utf8(im + " 0 obj\n<< /Type /XObject /Subtype /Image /Width " + p.w + " /Height " + p.h +
              " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + p.jpeg.length + " >>\nstream\n"));
    push(p.jpeg);
    push(utf8("\nendstream\nendobj\n"));
  });
  var total = 4 + n * 3, xref = pos;
  var x = "xref\n0 " + total + "\n0000000000 65535 f \n";
  for (var k = 1; k < total; k++) x += ("0000000000" + offsets[k]).slice(-10) + " 00000 n \n";
  x += "trailer\n<< /Size " + total + " /Root 1 0 R /Info 3 0 R >>\nstartxref\n" + xref + "\n%%EOF\n";
  push(utf8(x));
  return concatBytes(parts);
}

/* Markdown → ブロック列 (h1-h3 / p / li / code / hr / table / quote) */
function mdBlocks(md) {
  var lines = String(md || "").replace(/\r\n?/g, "\n").split("\n");
  var out = [], para = [], i = 0;
  function flush() { if (para.length) { out.push({ type: "p", text: para.join(" ") }); para = []; } }
  function cells(l) { return l.trim().replace(/^\||\|$/g, "").split("|").map(function (c) { return c.trim(); }); }
  while (i < lines.length) {
    var l = lines[i];
    if (/^```/.test(l)) {
      flush();
      var code = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) { code.push(lines[i]); i++; }
      out.push({ type: "code", text: code.join("\n") }); i++; continue;
    }
    if (/^\s*\|/.test(l)) {
      flush();
      var rows = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) {
        if (!/^\s*\|[\s:|-]+\|\s*$/.test(lines[i])) rows.push(cells(lines[i]));
        i++;
      }
      out.push({ type: "table", rows: rows, text: rows.map(function (r) { return r.join(" │ "); }).join("\n") });
      continue;
    }
    var h = l.match(/^(#{1,3})\s+(.*)$/);
    if (h) { flush(); out.push({ type: "h" + h[1].length, text: h[2].trim() }); i++; continue; }
    var q = l.match(/^>\s?(.*)$/);
    if (q) { flush(); out.push({ type: "quote", text: q[1] }); i++; continue; }
    var li = l.match(/^\s*(?:[-*+]|\d+[.)])\s+(.*)$/);
    if (li) { flush(); out.push({ type: "li", text: li[1].trim() }); i++; continue; }
    if (/^\s*(?:---+|\*\*\*+)\s*$/.test(l)) { flush(); out.push({ type: "hr", text: "" }); i++; continue; }
    if (/^\s*$/.test(l)) { flush(); i++; continue; }
    para.push(l.trim()); i++;
  }
  flush();
  return out;
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function stripInline(s) { return String(s).replace(/\*\*(.+?)\*\*/g, "$1").replace(/`([^`]+)`/g, "$1"); }

function inlineHtml(s) {
  return escapeHtml(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
}

function mdToHtml(md) {
  var html = [], inList = false;
  mdBlocks(md).forEach(function (b) {
    if (b.type !== "li" && inList) { html.push("</ul>"); inList = false; }
    if (b.type === "li") { if (!inList) { html.push("<ul>"); inList = true; } html.push("<li>" + inlineHtml(b.text) + "</li>"); }
    else if (b.type === "code") html.push("<pre>" + escapeHtml(b.text) + "</pre>");
    else if (b.type === "hr") html.push("<hr>");
    else if (b.type === "quote") html.push("<blockquote>" + inlineHtml(b.text) + "</blockquote>");
    else if (b.type === "table") {
      html.push("<table>" + b.rows.map(function (r, ri) {
        var tag = ri === 0 ? "th" : "td";
        return "<tr>" + r.map(function (c) { return "<" + tag + ">" + inlineHtml(c) + "</" + tag + ">"; }).join("") + "</tr>";
      }).join("") + "</table>");
    }
    else if (b.type === "p") html.push("<p>" + inlineHtml(b.text) + "</p>");
    else html.push("<" + b.type + ">" + inlineHtml(b.text) + "</" + b.type + ">");
  });
  if (inList) html.push("</ul>");
  return html.join("\n");
}

function slugify(name) {
  var s = String(name || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
  if (s.length >= 3) return s;
  /* 日本語名など ASCII が残らない場合は名前のハッシュで安定した識別子にする */
  return "app-" + crc32(utf8(String(name || "app"))).toString(16);
}

/* ダウンロード用のファイル名 (日本語の題名をそのまま使い、OS で使えない文字だけ置き換える) */
function fileBase(title) {
  var s = String(title || "").replace(/[\\/:*?"<>|\x00-\x1F]+/g, "").replace(/\s+/g, "_").replace(/^[._]+|[._]+$/g, "").slice(0, 60);
  return s || "badagpt-app";
}

/* ═════════════════════ 2. 電信エンジン (bada_telegraph から移植) ═════════════════════ */

function bXLogX(x) { return x <= 0 ? 0 : x * Math.log(x); }
function bManifoldElement(x) { var d = bXLogX(x), dd = d * d; return dd > 1e-12 ? 1 / dd : 0; }
function gammaln(x) {
  var c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - gammaln(1 - x);
  x -= 1;
  var a = c[0], t = x + 7.5;
  for (var i = 1; i < 9; i++) a += c[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}
function betaFn(p, q) { return Math.exp(gammaln(p) + gammaln(q) - gammaln(p + q)); }
function shannon(str) {
  var toks = Array.from(String(str));
  if (!toks.length) return 0;
  var f = {}, n = toks.length, H = 0;
  toks.forEach(function (t) { f[t] = (f[t] || 0) + 1; });
  Object.keys(f).forEach(function (k) { var p = f[k] / n; H -= p * Math.log2(p); });
  return H;
}
/* 大域的部分積分多様体不変量 Ξ = β(H+1, M+1) / log(N+2) */
function bXi(str) {
  var H = shannon(str), n = Array.from(String(str)).length || 1, M = bManifoldElement(n + 2);
  return betaFn(H + 1, M + 1) / Math.log(n + 2);
}

/* BadaNode：<- / -< / >- 演算子 (bada_ruby language.rb 準拠) */
function BadaNode(v) { this.value = v || 0; }
BadaNode.prototype.coerce = function (v) { return typeof v === "number" ? v : (v instanceof BadaNode ? v.value : bXi(v)); };
BadaNode.prototype.leftAct = function (inp) {
  var chi = this.coerce(inp), x = (Math.abs(this.value) < 1e-9 ? 1 : Math.abs(this.value)) + 1;
  this.value = Math.abs(Math.PI * chi * Math.log(x)); return this;
};
BadaNode.prototype.manifoldIntegral = function (s) {
  var v = s == null ? this.value : this.coerce(s), x = Math.abs(v) + 2;
  this.value = bXLogX(x) * bManifoldElement(x) + bManifoldElement(x); return this;
};
BadaNode.prototype.rightAct = function (o) {
  var v = o == null ? this.value : this.coerce(o), x = Math.abs(v) + 1e-6;
  this.value = Math.exp(-bXLogX(x)); return this;
};

/* Bada インタプリタ。set / <- / -< / >- / Omega::push / print に加え、
 * 名前空間命令 Tele::CMD (電信) と GPT::CMD (BadaGPT) を onCmd(ns, cmd, val) へ渡す。 */
function BadaInterp(onCmd) { this.env = {}; this.out = []; this.onCmd = onCmd; }
BadaInterp.prototype.evalExpr = function (s) {
  s = s.trim();
  var m = s.match(/^"(.*)"$/);
  if (m) return m[1];
  if (/^[-+]?\d+(?:\.\d+)?$/.test(s)) return parseFloat(s);
  if (Object.prototype.hasOwnProperty.call(this.env, s)) return this.env[s];
  return s;
};
BadaInterp.prototype.valOf = function (x) { return x instanceof BadaNode ? x.value : x; };
BadaInterp.prototype.nodef = function (n) {
  if (!(this.env[n] instanceof BadaNode)) this.env[n] = new BadaNode(typeof this.env[n] === "number" ? this.env[n] : 0);
  return this.env[n];
};
BadaInterp.prototype.exec = function (line) {
  var m;
  if ((m = line.match(/^set\s+(\w+)\s*=\s*(.+)$/))) { var v = this.evalExpr(m[2]); this.env[m[1]] = typeof v === "number" ? v : new BadaNode(bXi(v)); return; }
  if ((m = line.match(/^(\w+)\s*<-\s*(.+)$/))) { this.nodef(m[1]).leftAct(this.evalExpr(m[2])); return; }
  if ((m = line.match(/^(\w+)\s*-<\s*(.+)$/))) { this.nodef(m[1]).manifoldIntegral(this.evalExpr(m[2])); return; }
  if ((m = line.match(/^(\w+)\s*>-\s*(.+)$/))) { this.nodef(m[1]).rightAct(this.evalExpr(m[2])); return; }
  if ((m = line.match(/^(?:Omega|Ω)::push\s+(\w+)(?:\s+as\s+(\w+))?$/))) {
    var node = this.nodef(m[1]);
    this.out.push("Ω::push " + (m[2] || "node") + " (Ξ=" + node.value.toFixed(4) + ")"); return;
  }
  if ((m = line.match(/^print\s+(.+)$/))) { this.out.push(String(this.valOf(this.evalExpr(m[1])))); return; }
  if ((m = line.match(/^(Tele|GPT)::(\w+)(?:\s+(.+))?$/))) {
    var arg = m[3] ? m[3].trim() : null;
    var val = arg != null ? this.valOf(this.evalExpr(arg)) : null;
    this.out.push(m[1] + "::" + m[2] + (arg != null ? " " + arg : ""));
    if (this.onCmd) this.onCmd(m[1], m[2], val);
    return;
  }
  throw new Error("Bada syntax error: " + line);
};
BadaInterp.prototype.run = function (src) {
  var self = this;
  String(src).split("\n").forEach(function (raw) { var l = raw.replace(/#.*$/, "").trim(); if (l) self.exec(l); });
  return this.out;
};

/* BadaGPT電信の送信プログラム (Bada 言語)。思考入力を電信し、BadaGPT が受信して錬成する。 */
var BADAGPT_PROGRAM = [
  "# badagpt.bada — BadaGPT電信: 思考入力を電信で BadaGPT へ送り、アプリと論文を錬成する",
  "set entropy   = 3.20     # 依頼文のシャノンエントロピー H (送信時に注入)",
  "set crossings = 5        # Jones ブレイドの交差数 n (送信時に注入)",
  "set line      = 0",
  "line <- \"thought request telegraph\"   # 左作用 π(χ,x)",
  "line -< 1.0                            # 多様体積分 ∬1/(x·log x)²",
  "line >- line                           # 右量子作用 e^{-x·log x}",
  "Omega::push line as thought_node",
  "print line",
  "Tele::encode             # モールス + エントロピー符号化",
  "Tele::knot crossings     # Jones 多項式で量子チャンネルの結び目",
  "Tele::teleport           # 量子テレポーテーション (思考実験)",
  "Tele::graviton           # グラビトン → 電磁波 搬送波",
  "Tele::send               # BadaGPT へ配信",
  "GPT::comprehend          # 全体把握: 全ての節を仕様へ対応付け",
  "GPT::plan                # 設計: モジュール・データモデル・機能",
  "GPT::generate            # 生成: 自己完結 HTML アプリ",
  "GPT::verify              # 検証: 構文・要素・オフライン・網羅率",
  "GPT::paper               # 論文: 要求→設計→実装→検証を論文化"
].join("\n");

/* Jones 多項式 ((2,n) トーラス結び目) — Kauffman 括弧 TL2 */
var Jones = (function () {
  function addTo(m, e, c) { var v = (m.get(e) || 0) + c; if (v === 0) m.delete(e); else m.set(e, v); }
  function build(n) {
    var b = new Map();
    for (var k = 0; k < n; k++) {
      var nb = new Map();
      addTo(nb, k - 1, 1);
      b.forEach(function (c, e) { addTo(nb, e - 3, -c); });
      b = nb;
    }
    var norm = new Map();
    addTo(norm, n + 2, -1); addTo(norm, n - 2, -1);
    b.forEach(function (c, e) { addTo(norm, e, c); });
    var VA = new Map(), s = (n % 2 === 0) ? 1 : -1;
    norm.forEach(function (c, e) { addTo(VA, e - 3 * n, s * c); });
    return { norm: norm, VA: VA };
  }
  var cache = {};
  function get(n) { return cache[n] || (cache[n] = build(n)); }
  function evalReal(map, A) { var s = 0; map.forEach(function (c, e) { s += c * Math.pow(A, e); }); return s; }
  function sup(n) { return String(n).split("").map(function (d) { return d === "-" ? "⁻" : "⁰¹²³⁴⁵⁶⁷⁸⁹"[+d]; }).join(""); }
  function polyStr(map, limit) {
    var es = Array.from(map.keys()).sort(function (a, b) { return b - a; }).slice(0, limit || 3);
    return es.map(function (e) {
      var c = map.get(e), ac = Math.abs(c);
      return (c < 0 ? "−" : "+") + (ac === 1 ? "" : ac) + "A" + (e < 0 ? "⁻" + sup(-e) : sup(e));
    }).join("").replace(/^\+/, "") || "0";
  }
  return {
    bracketStr: function (n) { return polyStr(get(n).norm, 3); },
    Vreal: function (n, t) { return evalReal(get(n).VA, Math.pow(t, -0.25)); }
  };
})();

var MORSE = { A: ".-", B: "-...", C: "-.-.", D: "-..", E: ".", F: "..-.", G: "--.", H: "....", I: "..", J: ".---", K: "-.-",
  L: ".-..", M: "--", N: "-.", O: "---", P: ".--.", Q: "--.-", R: ".-.", S: "...", T: "-", U: "..-", V: "...-", W: ".--",
  X: "-..-", Y: "-.--", Z: "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....",
  "6": "-....", "7": "--...", "8": "---..", "9": "----.", ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--",
  "/": "-..-.", "@": ".--.-.", " ": "/" };
function bitsMorse(ch) { var b = ch.codePointAt(0) % 32, o = ""; for (var i = 4; i >= 0; i--) o += ((b >> i) & 1) ? "-" : "."; return o; }
function toMorse(s) { return Array.from(String(s).toUpperCase()).map(function (ch) { return MORSE[ch] || bitsMorse(ch); }).join(" "); }

/* 依頼文の電信指標 (Tele:: 各段の値) */
function telegraphMetrics(text) {
  var H = shannon(text), xi = bXi(text), len = Array.from(String(text)).length;
  var n = Math.max(2, Math.min(12, 3 + Math.floor(H * 1.6) + (len % 4)));
  var v2 = Jones.Vreal(n, 2);
  var fid = Math.max(0.5, Math.min(0.9999, 1 - Math.exp(-(Math.abs(v2) + xi))));
  var dx = 1 / (1 + H), dp = 0.5 * (1 + H);
  var frac = (xi % 1 + 1) % 1;
  return {
    H: H, xi: xi, n: n, bracket: Jones.bracketStr(n), v2: v2, fidelity: fid,
    uncertainty: dx * dp, strain: 1e-21 * (1 + H), carrierHz: 0.7e9 + frac * 2.4e9,
    morse: toMorse(String(text).slice(0, 48))
  };
}

/* ── FSK 音響モデム (音声帯域 2 周波・100 baud・UART 型フレーム) ──
 * フレーム: SOF 0x7E + 長さ(2byte) + UTF-8 本文 + チェックサム。
 * スマホ ⇄ アプリ間で「思考入力 (依頼文)」を音で送受信する。 */
var F_SPACE = 1000, F_MARK = 1600, BAUD = 100;
function frameBytes(text) {
  var payload = new TextEncoder().encode(text).slice(0, 65535);
  var body = [0x7E, payload.length & 0xFF, (payload.length >> 8) & 0xFF];
  for (var i = 0; i < payload.length; i++) body.push(payload[i]);
  var sum = 0;
  body.forEach(function (b) { sum = (sum + b) & 0xFF; });
  body.push(sum);
  return body;
}
function textToBits(text) {
  var bits = [], k;
  for (k = 0; k < 12; k++) bits.push(1);
  frameBytes(text).forEach(function (b) { bits.push(0); for (var i = 0; i < 8; i++) bits.push((b >> i) & 1); bits.push(1); });
  for (k = 0; k < 8; k++) bits.push(1);
  return bits;
}
function fskModulate(text, sr) {
  var bits = textToBits(text), spb = Math.round(sr / BAUD);
  var out = new Float32Array(bits.length * spb), ph = 0, idx = 0;
  bits.forEach(function (bit) {
    var dp = 2 * Math.PI * (bit ? F_MARK : F_SPACE) / sr;
    for (var i = 0; i < spb; i++) { out[idx++] = Math.sin(ph) * 0.9; ph += dp; if (ph > 2 * Math.PI) ph -= 2 * Math.PI; }
  });
  return out;
}
function goertzelPow(s, start, n, f, sr) {
  var w = 2 * Math.PI * f / sr, coeff = 2 * Math.cos(w), s1 = 0, s2 = 0;
  for (var i = 0; i < n; i++) { var s0 = (s[start + i] || 0) + coeff * s1 - s2; s2 = s1; s1 = s0; }
  return s1 * s1 + s2 * s2 - coeff * s1 * s2;
}
function fskDemodulate(s, sr) {
  var spb = Math.round(sr / BAUD), N = s.length;
  if (N < 14 * spb) return "";
  function power(c) {
    var st = Math.round(c - spb / 2);
    if (st < 0 || st + spb > N) return null;
    var m = goertzelPow(s, st, spb, F_MARK, sr), sp = goertzelPow(s, st, spb, F_SPACE, sr);
    return { m: m, sp: sp };
  }
  function diffC(c) { var p = power(c); return p ? (p.m - p.sp) / (p.m + p.sp + 1e-12) : 0; }
  function bitAt(c) { var p = power(c); return p ? (p.m > p.sp ? 1 : 0) : -1; }
  var i = spb, bytes = [];
  while (i + 11 * spb < N) {
    while (i + spb < N && diffC(i) < 0.4) i++;
    var b = i;
    while (b + spb < N && diffC(b) > 0) b++;
    if (b + 11 * spb >= N) break;
    var byte = 0, ok = true;
    for (var k = 0; k < 8; k++) { var v = bitAt(b + (k + 1.5) * spb); if (v < 0) { ok = false; break; } byte |= v << k; }
    if (!ok) break;
    bytes.push(byte);
    i = Math.round(b + 9.5 * spb);
  }
  for (var fi = bytes.indexOf(0x7E); fi >= 0; fi = bytes.indexOf(0x7E, fi + 1)) {
    if (fi + 2 >= bytes.length) break;
    var len = bytes[fi + 1] | (bytes[fi + 2] << 8), pay = bytes.slice(fi + 3, fi + 3 + len);
    if (pay.length !== len || fi + 3 + len >= bytes.length) continue;
    var sum = (0x7E + bytes[fi + 1] + bytes[fi + 2]) & 0xFF;
    pay.forEach(function (x) { sum = (sum + x) & 0xFF; });
    if (sum !== bytes[fi + 3 + len]) continue;
    try { return new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(pay)); } catch (e) { continue; }
  }
  return "";
}
