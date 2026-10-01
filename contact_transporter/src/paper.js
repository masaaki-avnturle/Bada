/*
 * paper.js — 投稿された論文 PDF を読み、アプリの材料 (題名・本文・方程式・数値パラメータ・分類) にする
 *
 *   const doc = await CTPaper.readPdf(pdfjsLib, bytes)   // pdf.js でテキスト行を取り出す
 *   const paper = CTPaper.analyze(doc, "file.pdf")         // 方程式・数値・タグ・等式の数値検証
 *
 * ブラウザ (window.CTPaper) と Node (module.exports, Actions の論文→アプリ パイプライン) の両対応。
 */
(function (root) {
  "use strict";

  // ------------------------------------------------------------ PDF → 行
  async function readPdf(pdfjs, bytes, opts) {
    opts = opts || {};
    const task = pdfjs.getDocument(Object.assign({ data: bytes, disableFontFace: true, isEvalSupported: false, useSystemFonts: false }, opts.docOptions || {}));
    const doc = await task.promise;
    let info = {};
    try { info = (await doc.getMetadata()).info || {}; } catch (e) { /* メタデータなし */ }
    const pages = [];
    const maxPages = Math.min(doc.numPages, opts.maxPages || 400);
    for (let pn = 1; pn <= maxPages; pn++) {
      const page = await doc.getPage(pn);
      const tc = await page.getTextContent();
      const rows = [];
      for (const it of tc.items) {
        if (!("str" in it)) continue;
        const y = it.transform[5], x = it.transform[4], h = Math.abs(it.height || it.transform[3] || 0);
        let row = rows.find((r) => Math.abs(r.y - y) <= Math.max(2, h * 0.35));
        if (!row) { row = { y, items: [], size: 0 }; rows.push(row); }
        row.items.push({ x, s: it.str, w: it.width || 0 });
        if (it.str.trim()) row.size = Math.max(row.size, h);
      }
      rows.sort((a, b) => b.y - a.y);
      const lines = [];
      for (const r of rows) {
        r.items.sort((a, b) => a.x - b.x);
        let text = "", lastEnd = null;
        for (const it of r.items) {
          if (lastEnd != null && it.x - lastEnd > r.size * 0.25 && !text.endsWith(" ") && !it.s.startsWith(" ")) text += " ";
          text += it.s; lastEnd = it.x + it.w;
        }
        text = text.replace(/\s+/g, " ").trim();
        if (text) lines.push({ text, y: r.y, size: r.size });
      }
      pages.push({ n: pn, lines });
      if (opts.onProgress) opts.onProgress(pn, doc.numPages);
    }
    return { numPages: doc.numPages, info, pages };
  }

  // ------------------------------------------------------------ 分類
  const TAGS = [
    ["ZETA", /ζ|zeta|ゼータ|Riemann|リーマン|Z\(t\)|Z\(φ\)/i],
    ["GAMMA", /Γ\(|Γ'|ガンマ|gamma/i],
    ["BETA", /β\(|B\(|ベータ|beta/i],
    ["JONES", /Jones|V\(t|結び目|knot|3_1|4_1|5_1/i],
    ["SR", /c²|c\^2|mc|v\/c|ローレンツ|Lorentz|相対|√\(1\s*[−-]/i],
    ["ROT", /sin|cos|e\^\{?i|e\^\(i|θ|回転|rot/i],
    ["QUANTUM", /ψ|Ψ|ℏ|量子|quantum|⟨|⟩|qubit|\|0⟩|\|1⟩/i],
    ["MANIFOLD", /∫|∮|∂|∇|g_\{?ij|R_\{?ij|ds²|多様体|manifold|dx\^/i],
    ["ENTROPY", /log|ln|エントロピー|entropy|H\(/i],
    ["TRANSPORT", /輸送|transport|UFO|反重力|推進|GM/i],
  ];
  const TAG_JA = { ZETA: "ゼータ関数", GAMMA: "ガンマ関数", BETA: "ベータ関数", JONES: "Jones 多項式", SR: "特殊相対論", ROT: "複素回転体",
    QUANTUM: "量子", MANIFOLD: "多様体", ENTROPY: "エントロピー", TRANSPORT: "輸送", OTHER: "その他" };
  function tagsOf(s) { const t = TAGS.filter(([, re]) => re.test(s)).map(([k]) => k); return t.length ? t : ["OTHER"]; }

  // ------------------------------------------------------------ 数式の数値評価 (安全な再帰下降)
  const FN = { sin: Math.sin, cos: Math.cos, tan: Math.tan, exp: Math.exp, log: Math.log, ln: Math.log, sqrt: Math.sqrt, abs: Math.abs,
    sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh, arcosh: Math.acosh, acosh: Math.acosh, atan: Math.atan, asin: Math.asin, acos: Math.acos };
  const CONST = { "π": Math.PI, pi: Math.PI, e: Math.E, "γ": 0.5772156649015329 };
  function normalizeMath(s) {
    return s.replace(/[−–—]/g, "-").replace(/[×·⋅∙]/g, "*").replace(/÷/g, "/").replace(/＝/g, "=").replace(/（/g, "(").replace(/）/g, ")")
      .replace(/²/g, "^2").replace(/³/g, "^3").replace(/√\s*(\d+(?:\.\d+)?|[πγ])/g, "sqrt($1)").replace(/√/g, "sqrt").replace(/\s+/g, " ").trim();
  }
  function evalNum(src) {
    const s = normalizeMath(src); let i = 0;
    const peek = () => { while (s[i] === " ") i++; return s[i]; };
    const fail = () => { throw new Error("not numeric"); };
    function expr() { let v = term(); for (;;) { const c = peek(); if (c === "+") { i++; v += term(); } else if (c === "-") { i++; v -= term(); } else return v; } }
    function term() {
      let v = unary();
      for (;;) {
        const c = peek();
        if (c === "*") { i++; v *= unary(); } else if (c === "/") { i++; v /= unary(); }
        else if (c === "(" || (c && /[0-9.πγ]/.test(c) && /[)\dπ]$/.test(s.slice(0, i).trim()))) { v *= unary(); } // 暗黙の積 2π, 2(3)
        else return v;
      }
    }
    function unary() { const c = peek(); if (c === "-") { i++; return -unary(); } if (c === "+") { i++; return unary(); } return power(); }
    function power() { const b = atom(); if (peek() === "^") { i++; let e; if (peek() === "{") { i++; e = expr(); if (peek() !== "}") fail(); i++; } else e = unary(); return Math.pow(b, e); } return b; }
    function atom() {
      const c = peek();
      if (c === "(") { i++; const v = expr(); if (peek() !== ")") fail(); i++; return v; }
      const m = /^(\d+\.?\d*|\.\d+)(e[+-]?\d+)?/i.exec(s.slice(i));
      if (m) { i += m[0].length; return parseFloat(m[0]); }
      const id = /^[A-Za-zπγ]+/.exec(s.slice(i));
      if (id) {
        const w = id[0];
        if (FN[w] && s[i + w.length] === "(") { i += w.length; i++; const v = expr(); if (peek() !== ")") fail(); i++; return FN[w](v); }
        if (w in CONST) { i += w.length; return CONST[w]; }
      }
      fail();
    }
    const v = expr();
    if (peek() !== undefined) fail();
    if (!isFinite(v)) fail();
    return v;
  }
  const tryNum = (s) => { try { return evalNum(s); } catch (e) { return null; } };

  // ------------------------------------------------------------ 論文の解析
  const CJK = /[぀-ヿ㐀-鿿]/g;
  const MATHCH = /[=≈≅≥≤∝∫∮∂∇√ΣΠ∏∑^_ζΓβψΨℏθφπ⊕⊗]/;
  function isEquation(t) {
    if (t.length < 3 || t.length > 400) return false;
    if (!/[=≈≅≥≤∝]/.test(t)) return false;
    const cjk = (t.match(CJK) || []).length;
    if (cjk / t.length > 0.45) return false;            // 日本語の地の文
    if (!/[A-Za-z0-9α-ωΑ-Ω∫∂∇√πζΓβψ]/.test(t)) return false;
    return MATHCH.test(t);
  }
  function analyze(doc, fileName) {
    const pages = doc.pages;
    const all = [];
    pages.forEach((p) => p.lines.forEach((l) => all.push(Object.assign({ page: p.n }, l))));
    // 題名: 1 ページ目で最も大きい文字の行 (連続する同じ大きさの行をつなぐ)
    let title = (doc.info && doc.info.Title) || "";
    const p1 = all.filter((l) => l.page === 1);
    if (p1.length) {
      const maxSize = Math.max(...p1.map((l) => l.size || 0));
      const big = p1.filter((l) => (l.size || 0) >= maxSize * 0.8).slice(0, 3).map((l) => l.text);
      if (!title || title.length < 3) title = big.join(" ");
    }
    if (!title) title = (fileName || "paper").replace(/\.pdf$/i, "");
    // 方程式: 登録簿形式 (ID 行 + 状態行) を優先、なければ数式らしい行
    const eqs = [];
    const ID = /^[A-Z][A-Z0-9_]*\.[0-9]+$/, ST = new Set(["symb", "calc", "holds", "differs"]);
    for (let k = 0; k + 1 < all.length; k++) {
      if (ID.test(all[k].text) && ST.has(all[k + 1].text)) {
        const body = []; let j = k + 2, tags = null;
        while (j < all.length && !(ID.test(all[j].text) && j + 1 < all.length && ST.has(all[j + 1].text))) {
          const t = all[j].text;
          if (/^\d+\. 全方程式|^=== PAGE/.test(t)) { j++; continue; }
          if (!tags && !body.length && /^\[[A-Z, ]+\]$/.test(t)) tags = t.replace(/[[\]]/g, "").split(",").map((x) => x.trim()).filter(Boolean);
          else body.push(t);
          j++;
        }
        const text = body.join(" "), m = /^(.*)\s{2,}=\s(.*)$/.exec(text) || /^(.*?)\s+=\s([-\d.e+ i]+(?: vs [-\d.e+ i]+)?)$/.exec(text);
        eqs.push({ id: all[k].text, page: all[k].page, status: all[k + 1].text, tags: tags || tagsOf(text), text: m && all[k + 1].text !== "symb" ? m[1].trim() : text, value: m && all[k + 1].text !== "symb" ? m[2].trim() : "" });
        k = j - 1;
      }
    }
    // 1 行形式の登録簿: 「ID 状態 式 = 値 [TAGS]」 (折り返し行は直前の式に続ける)
    if (eqs.length < 10) {
      eqs.length = 0;
      const ONE = /^([A-Z][A-Z0-9_]*\.[0-9]+)\s+(symb|calc|holds|differs)\s+(.*)$/;
      let cur = null;
      const finish = () => {
        if (!cur) return;
        let t = cur.raw.trim(), tags = null;
        const tm = /\s*\[([A-Z][A-Z, ]*)\]\s*$/.exec(t);
        if (tm) { tags = tm[1].split(",").map((x) => x.trim()).filter(Boolean); t = t.slice(0, tm.index).trim(); }
        let text = t, value = "";
        if (cur.status !== "symb") {
          const vm = /^(.*)\s=\s(-?[\d.]+(?:e[+-]?\d+)?(?:\s*[+−-]\s*[\d.]+(?:e[+-]?\d+)?i)?(?:\s+vs\s+-?[\d.]+(?:e[+-]?\d+)?(?:\s*[+−-]\s*[\d.]+(?:e[+-]?\d+)?i)?)?)$/.exec(t);
          if (vm) { text = vm[1].trim(); value = vm[2].trim(); }
        }
        eqs.push({ id: cur.id, page: cur.page, status: cur.status, tags: tags || tagsOf(text), text, value });
        cur = null;
      };
      for (const l of all) {
        const m = ONE.exec(l.text);
        if (m) { finish(); cur = { id: m[1], status: m[2], raw: m[3], page: l.page }; continue; }
        if (cur && l.page === cur.page && !/^\d+\.\s/.test(l.text) && (l.size || 0) <= 8) cur.raw += " " + l.text;
        else finish();
      }
      finish();
      if (eqs.length < 10) eqs.length = 0;
    }
    const registry = eqs.length >= 10;
    if (!registry) {
      let n = 0;
      for (const l of all) {
        if (!isEquation(l.text)) continue;
        n++;
        const sides = normalizeMath(l.text).split(/=|≈|≅/).map((x) => x.trim()).filter(Boolean);
        const nums = sides.map(tryNum);
        const known = nums.filter((v) => v != null);
        let status = "symb", value = "";
        if (known.length >= 2) {
          const ok = known.every((v) => Math.abs(v - known[0]) <= 1e-6 * Math.max(1, Math.abs(known[0])));
          status = ok ? "holds" : "differs"; value = known.map((v) => +v.toPrecision(6)).join(" vs ");
        } else if (known.length === 1) { status = "calc"; value = String(+known[0].toPrecision(6)); }
        eqs.push({ id: `EQ.${n}`, page: l.page, status, tags: tagsOf(l.text), text: l.text, value });
      }
    }
    // 数値パラメータ: 「記号 = 数値 [単位]」
    const params = [], seen = new Set();
    const PRE = /([A-Za-zα-ωΑ-Ωφθψζγβ][A-Za-z0-9_α-ωΑ-Ω'|]{0,8})\s*[=＝≈]\s*(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(m|km|kg|s|h|rad\/s|GeV|TeV|ly|Hz|K|J|%)?(?![\d.])/g;
    for (const l of all) {
      let m;
      PRE.lastIndex = 0;
      while ((m = PRE.exec(l.text)) && params.length < 80) {
        const key = m[1] + "=" + m[2];
        if (seen.has(key)) continue; seen.add(key);
        params.push({ name: m[1], value: parseFloat(m[2]), unit: m[3] || "", page: l.page });
      }
    }
    const tagCount = {};
    for (const e of eqs) for (const t of e.tags) tagCount[t] = (tagCount[t] || 0) + 1;
    const stat = { symb: 0, calc: 0, holds: 0, differs: 0 };
    for (const e of eqs) stat[e.status] = (stat[e.status] || 0) + 1;
    const text = all.map((l) => l.text).join("\n");
    // 決定的な種 (同じ論文 → 同じアプリ)
    let h = 2166136261;
    for (let k = 0; k < text.length; k++) { h ^= text.charCodeAt(k); h = Math.imul(h, 16777619) >>> 0; }
    return {
      file: fileName || "paper.pdf", title: title.slice(0, 120), pages: doc.numPages, lines: all.length, chars: text.length,
      registry, equations: eqs, params, tagCount, stat, hash: h, excerpt: all.slice(0, 40).map((l) => l.text),
    };
  }

  // 英数字の短い識別子 (ファイル名用)
  function slug(s) {
    const a = String(s).normalize("NFKD").replace(/[^\w]+/g, "_").replace(/^_+|_+$/g, "").toLowerCase().slice(0, 40);
    return a || "paper";
  }

  const api = { readPdf, analyze, evalNum, tagsOf, TAG_JA, slug, isEquation };
  root.CTPaper = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
