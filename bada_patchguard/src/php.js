/*
 * php.js — PHP の字句解析と「副作用の事実」の抽出 (Bada へ渡すネイティブ組込み)
 *
 * ここでは判定はしません。PHP ソースから、書き換え前後を比べるための事実
 * (関数呼び出し・出力・include・関数定義・認可チェック・大域状態・構文の均衡)
 * を集めるだけです。何が危険で、どの変化を副作用とみなすかは guard.bada の
 * @reviser 規則が決めます。
 *
 * 汚染 (taint) の追跡は 1 ファイル内の近似です:
 *   - $_GET/$_POST/$_REQUEST/$_COOKIE/$_FILES と一部の $_SERVER、php://input が源泉
 *   - $x = <汚染された式> で $x が汚染され、無害化関数 (guard.bada の sanitizer) や
 *     (int) などのキャストで包まれた部分は汚染に数えない
 */
"use strict";

const PHP_OPS = ["<=>", "===", "!==", "**=", "...", "<<=", ">>=", "??=", "?->", "->", "=>", "::", "==", "!=", "<>", "<=", ">=",
  "&&", "||", "??", "++", "--", "+=", "-=", "*=", "/=", ".=", "%=", "&=", "|=", "^=", "<<", ">>", "**"];
const SUPERGLOBALS = new Set(["$_GET", "$_POST", "$_REQUEST", "$_COOKIE", "$_FILES"]);
const SERVER_TAINTED = /^(HTTP_|REQUEST_URI$|PHP_SELF$|QUERY_STRING$|PATH_INFO$|PATH_TRANSLATED$|ORIG_PATH_INFO$|CONTENT_TYPE$|REMOTE_USER$|AUTH_)/;
const CASTS = new Set(["int", "integer", "float", "double", "bool", "boolean"]);
const AUTH_RE = /(auth|login|logged|permission|capab|csrf|xsrf|nonce|verify|is_admin|require_role|has_role|can_|current_user_can|check_|session_start|session_regenerate_id|password_verify|hash_equals)/i;

function phpLex(src) {
  const toks = []; let i = 0, line = 1, inPhp = false;
  const n = src.length;
  const push = (t, v, extra) => { const o = { t, v, line }; if (extra) Object.assign(o, extra); toks.push(o); return o; };
  const count = s => { for (let k = 0; k < s.length; k++) if (s.charCodeAt(k) === 10) line++; };
  const interpVars = s => {
    const vs = []; const re = /\{?\$([A-Za-z_\x80-￿][\w\x80-￿]*)/g; let m;
    while ((m = re.exec(s))) { if (m.index > 0 && s[m.index - 1] === "\\" && s[m.index] === "$") continue; vs.push("$" + m[1]); }
    return vs;
  };
  while (i < n) {
    if (!inPhp) {
      const j = src.indexOf("<?", i);
      const end = j < 0 ? n : j;
      if (end > i) { const h = src.slice(i, end); push("html", h); count(h); }
      if (j < 0) break;
      if (src.startsWith("<?php", j)) { push("open", "<?php"); i = j + 5; }
      else if (src.startsWith("<?=", j)) { push("openecho", "<?="); i = j + 3; }
      else { push("open", "<?"); i = j + 2; }
      inPhp = true; continue;
    }
    const c = src[i];
    if (c === "\n") { line++; i++; continue; }
    if (c === " " || c === "\t" || c === "\r") { i++; continue; }
    if (src.startsWith("?>", i)) { push("close", "?>"); i += 2; if (src[i] === "\n") { line++; i++; } inPhp = false; continue; }
    if (c === "#" && src[i + 1] === "[") {           // PHP 8 属性 #[...]
      let d = 0, j = i + 1;
      for (; j < n; j++) { if (src[j] === "[") d++; else if (src[j] === "]") { d--; if (!d) break; } }
      const s = src.slice(i, j + 1); push("comment", s); count(s); i = j + 1; continue;
    }
    if (c === "#" || (c === "/" && src[i + 1] === "/")) {
      let j = i; while (j < n && src[j] !== "\n" && !src.startsWith("?>", j)) j++;
      push("comment", src.slice(i, j)); i = j; continue;
    }
    if (c === "/" && src[i + 1] === "*") {
      let j = src.indexOf("*/", i + 2); const bad = j < 0; if (bad) j = n; else j += 2;
      const s = src.slice(i, j); push(bad ? "error" : "comment", bad ? "unterminated comment" : s); count(s); i = j; continue;
    }
    if (c === "$" && /[A-Za-z_\x80-￿$]/.test(src[i + 1] || "")) {
      if (src[i + 1] === "$") { push("var", "$$"); i += 1; continue; }
      let j = i + 1; while (j < n && /[\w\x80-￿]/.test(src[j])) j++;
      push("var", src.slice(i, j)); i = j; continue;
    }
    if (/[A-Za-z_\\\x80-￿]/.test(c)) {
      let j = i; while (j < n && /[\w\\\x80-￿]/.test(src[j])) j++;
      push("id", src.slice(i, j)); i = j; continue;
    }
    if (/[0-9]/.test(c) || (c === "." && /[0-9]/.test(src[i + 1] || ""))) {
      const m = /^(0[xX][0-9a-fA-F_]+|0[bB][01_]+|(\d[\d_]*)?\.?\d[\d_]*([eE][+-]?\d+)?)/.exec(src.slice(i, i + 64));
      push("num", m[0]); i += m[0].length || 1; continue;
    }
    if (c === "'" || c === '"' || c === "`") {
      let j = i + 1;
      while (j < n && src[j] !== c) { if (src[j] === "\\") j++; j++; }
      const bad = j >= n; const s = src.slice(i, Math.min(j + 1, n));
      if (bad) { push("error", "unterminated string"); count(s); i = n; continue; }
      const body = s.slice(1, -1);
      const o = push(c === "`" ? "backtick" : "str", body, { q: c, vars: c === "'" ? [] : interpVars(body) });
      count(s); i = j + 1; void o; continue;
    }
    if (src.startsWith("<<<", i)) {
      const m = /^<<<[ \t]*(['"]?)([A-Za-z_]\w*)\1\r?\n/.exec(src.slice(i, i + 200));
      if (m) {
        const id = m[2], nowdoc = m[1] === "'";
        const start = i + m[0].length;
        const re = new RegExp("(^|\\n)[ \\t]*" + id + "\\b", "g"); re.lastIndex = start - 1;
        const mm = re.exec(src);
        const stop = mm ? mm.index + mm[0].length : n;
        const body = src.slice(start, mm ? mm.index : n);
        const startLine = line;
        count(src.slice(i, stop));
        toks.push({ t: "str", v: body, line: startLine, q: nowdoc ? "'" : '"', vars: nowdoc ? [] : interpVars(body) });
        i = stop; continue;
      }
    }
    const op = PHP_OPS.find(o => src.startsWith(o, i));
    if (op) { push("op", op); i += op.length; continue; }
    push("op", c); i++;
  }
  return toks;
}

/* 呼び出し・式の範囲を求める補助 */
function matchClose(T, i) {   // T[i] は '(' か '[' か '{'
  const open = T[i].v, close = open === "(" ? ")" : open === "[" ? "]" : "}";
  let d = 0;
  for (let k = i; k < T.length; k++) {
    if (T[k].t !== "op") continue;
    if (T[k].v === open) d++;
    else if (T[k].v === close) { d--; if (d === 0) return k; }
  }
  return T.length - 1;
}
function stmtEnd(T, i) {   // ';' / '?>' (深さ 0) まで
  let d = 0;
  for (let k = i; k < T.length; k++) {
    const t = T[k];
    if (t.t === "close") return k;
    if (t.t !== "op") continue;
    if (t.v === "(" || t.v === "[" || t.v === "{") d++;
    else if (t.v === ")" || t.v === "]" || t.v === "}") { if (d === 0) return k; d--; }
    else if (t.v === ";" && d === 0) return k;
  }
  return T.length;
}
/* トークン列を読みやすい 1 行に (比較の鍵にも使うので空白の規則は決定的) */
function norm(toks) {
  let out = "", prev = null;
  for (const t of toks) {
    const v = t.t === "str" ? t.q + t.v + t.q : t.t === "backtick" ? "`" + t.v + "`" : t.v;
    const tight = prev && (["(", "[", "->", "?->", "::", "!", "$$", "&", "@"].includes(prev.v) && prev.t === "op" ||
      (t.t === "op" && ["(", ")", "[", "]", ",", ";", "->", "?->", "::", "++", "--"].includes(t.v) && !(t.v === "(" && prev.t === "op" && !["(", ")", "]"].includes(prev.v))));
    out += (out && !tight ? " " : "") + v;
    prev = t;
  }
  return out.replace(/\s+/g, " ").trim();
}
const lc = s => String(s).toLowerCase().replace(/^\\/, "");

function analyzePhp(src, sanitizerList) {
  const all = phpLex(String(src));
  const errors = all.filter(t => t.t === "error").map(t => ({ line: t.line, msg: t.v }));
  const T = all.filter(t => t.t !== "comment" && t.t !== "html");
  const sanit = new Set((sanitizerList || []).map(lc));
  const tainted = new Set();

  function isSuper(k) {
    const t = T[k];
    if (t.t !== "var") return false;
    if (SUPERGLOBALS.has(t.v)) return true;
    if (t.v === "$_SERVER" && T[k + 1] && T[k + 1].v === "[" && T[k + 2] && T[k + 2].t === "str") return SERVER_TAINTED.test(T[k + 2].v);
    return false;
  }
  /* 範囲 [a, b) の汚染: raw = 無害化を無視、eff = 無害化された部分を除く */
  function taint(a, b, skipSanitized) {
    const src = [];
    for (let k = a; k < b; k++) {
      const t = T[k];
      if (skipSanitized) {
        const meth = T[k - 1] && (T[k - 1].v === "->" || T[k - 1].v === "?->");
        if (t.t === "id" && (meth ? sanit.has("->" + lc(t.v)) : sanit.has(lc(t.v))) && T[k + 1] && T[k + 1].v === "(") { k = matchClose(T, k + 1); continue; }
        if (t.v === "(" && T[k + 1] && T[k + 1].t === "id" && CASTS.has(lc(T[k + 1].v)) && T[k + 2] && T[k + 2].v === ")") {
          k += 3; while (k + 1 < b && T[k + 1].v === "[") k = matchClose(T, k + 1); continue;
        }
      }
      if (isSuper(k)) src.push(t.v);
      else if (t.t === "var" && tainted.has(t.v)) src.push(t.v);
      else if (t.t === "str" && t.vars) { for (const v of t.vars) if (tainted.has(v) || SUPERGLOBALS.has(v)) src.push(v); }
      else if (t.t === "backtick" && t.vars) { for (const v of t.vars) if (tainted.has(v) || SUPERGLOBALS.has(v)) src.push(v); }
      else if (t.t === "str" && /^php:\/\/input$/i.test(t.v)) src.push("php://input");
    }
    return Array.from(new Set(src));
  }

  /* ── 汚染の伝播 (代入・foreach) を 2 周 ── */
  for (let pass = 0; pass < 2; pass++) {
    for (let k = 0; k < T.length; k++) {
      const t = T[k];
      if (t.t === "var" && T[k + 1] && T[k + 1].t === "op" && ["=", ".=", "??="].includes(T[k + 1].v)
          && !(T[k - 1] && (T[k - 1].v === "->" || T[k - 1].v === "::"))) {
        const e = stmtEnd(T, k + 2);
        const eff = taint(k + 2, e, true);
        if (eff.length) tainted.add(t.v);
        else if (T[k + 1].v === "=" && pass === 0) tainted.delete(t.v);
      }
      if (t.t === "id" && lc(t.v) === "foreach" && T[k + 1] && T[k + 1].v === "(") {
        const c = matchClose(T, k + 1); let asI = -1;
        for (let q = k + 2; q < c; q++) if (T[q].t === "id" && lc(T[q].v) === "as") { asI = q; break; }
        if (asI > 0 && taint(k + 2, asI, true).length) for (let q = asI + 1; q < c; q++) if (T[q].t === "var") tainted.add(T[q].v);
      }
    }
  }

  const calls = [], echoes = [], includes = [], defs = [], auth = [], state = [];
  const classStack = []; let depth = 0, pendingClass = null;
  const KEYWORDS = new Set(["if", "elseif", "while", "for", "foreach", "switch", "match", "return", "array", "list", "isset", "empty", "unset", "function", "fn", "new", "catch", "declare", "use", "exit", "die", "echo", "print", "include", "include_once", "require", "require_once", "and", "or", "xor", "instanceof", "clone", "yield", "static", "self", "parent"]);

  for (let k = 0; k < T.length; k++) {
    const t = T[k], prev = T[k - 1], next = T[k + 1];
    if (t.t === "op" && t.v === "{") { depth++; if (pendingClass) { classStack.push({ name: pendingClass, depth }); pendingClass = null; } continue; }
    if (t.t === "op" && t.v === "}") { if (classStack.length && classStack[classStack.length - 1].depth === depth) classStack.pop(); depth--; continue; }
    const cls = classStack.length ? classStack[classStack.length - 1].name : null;

    if (t.t === "id") {
      const lv = lc(t.v);
      if ((lv === "class" || lv === "interface" || lv === "trait" || lv === "enum") && next && next.t === "id" && !(prev && prev.v === "::")) { pendingClass = next.v; continue; }
      if (lv === "function" && next) {
        let q = k + 1; if (T[q] && T[q].v === "&") q++;
        if (T[q] && T[q].t === "id" && T[q + 1] && T[q + 1].v === "(") {
          const c = matchClose(T, q + 1);
          const params = []; let cur = [];
          const flush = () => {
            if (!cur.length) return;
            const vi = cur.findIndex(x => x.t === "var");
            if (vi >= 0) {
              const eq = cur.findIndex(x => x.v === "=");
              params.push({
                name: cur[vi].v, type: norm(cur.slice(0, vi).filter(x => !["&", "..."].includes(x.v) && !/^(public|private|protected|readonly)$/i.test(x.v))),
                def: eq >= 0 ? norm(cur.slice(eq + 1)) : null, ref: cur.some(x => x.v === "&"), variadic: cur.some(x => x.v === "...")
              });
            }
            cur = [];
          };
          let d = 0;
          for (let p = q + 2; p < c; p++) {
            const x = T[p];
            if (x.v === "(" || x.v === "[") d++; else if (x.v === ")" || x.v === "]") d--;
            if (x.v === "," && d === 0) flush(); else cur.push(x);
          }
          flush();
          let vis = "public", stat = false;
          for (let b = k - 1; b >= Math.max(0, k - 4); b--) {
            const w = lc(T[b].v);
            if (w === "private" || w === "protected" || w === "public") vis = w;
            else if (w === "static") stat = true;
            else if (w !== "final" && w !== "abstract") break;
          }
          const name = T[q].v;
          defs.push({
            key: cls ? lc(cls) + "::" + lc(name) : lc(name), name, cls, line: t.line, visibility: cls ? vis : "public", static: stat,
            params, required: params.filter(p => p.def === null && !p.variadic).length,
            sig: name + "(" + params.map(p => (p.type ? p.type + " " : "") + (p.ref ? "&" : "") + (p.variadic ? "..." : "") + p.name + (p.def !== null ? " = " + p.def : "")).join(", ") + ")"
          });
          continue;
        }
      }
      if (lv === "echo" || lv === "print") {
        const e = stmtEnd(T, k + 1);
        const eff = taint(k + 1, e, true), raw = taint(k + 1, e, false);
        echoes.push({ line: t.line, kind: lv, expr: norm(T.slice(k + 1, e)).slice(0, 160), key: lv + " " + norm(T.slice(k + 1, e)) + (eff.length ? " ⟨tainted⟩" : ""), tainted: eff.length > 0, sources: eff, sanitized: raw.length > 0 && eff.length === 0 });
        continue;
      }
      if (/^(include|require)(_once)?$/.test(lv)) {
        const e = stmtEnd(T, k + 1); const seg = T.slice(k + 1, e);
        const eff = taint(k + 1, e, true);
        const lit = seg.filter(x => x.t === "str").map(x => x.v).join("");
        includes.push({ line: t.line, kind: lv, expr: norm(seg).slice(0, 160), key: lv + " " + norm(seg) + (eff.length ? " ⟨tainted⟩" : ""), dynamic: seg.some(x => x.t === "var") || seg.some(x => x.t === "str" && x.vars && x.vars.length), tainted: eff.length > 0, sources: eff, target: lit });
        continue;
      }
      if (lv === "global") {
        const e = stmtEnd(T, k + 1);
        for (let q = k + 1; q < e; q++) if (T[q].t === "var") state.push({ kind: "global", key: "global " + T[q].v, line: t.line, text: "global " + T[q].v });
        continue;
      }
      if (lv === "if" && next && next.v === "(") {
        const c = matchClose(T, k + 1);
        const seg = T.slice(k + 2, c);
        if (seg.some(x => x.v === "$_SESSION")) auth.push({ name: "if($_SESSION)", key: "if " + norm(seg), line: t.line, text: "if (" + norm(seg).slice(0, 120) + ")" });
      }
      /* 関数・メソッド呼び出し */
      if (next && next.v === "(" && !KEYWORDS.has(lv)) {
        if (prev && (lc(prev.v) === "function" || lc(prev.v) === "new" || prev.v === "fn")) continue;
        let name = t.v, lname = lv;
        if (prev && (prev.v === "->" || prev.v === "?->")) { name = "->" + t.v; lname = "->" + lv; }
        else if (prev && prev.v === "::" && T[k - 2]) { name = T[k - 2].v + "::" + t.v; lname = lc(T[k - 2].v) + "::" + lv; }
        const c = matchClose(T, k + 1);
        const argT = T.slice(k + 2, c);
        let argc = argT.length ? 1 : 0, d = 0;
        for (const x of argT) { if (x.v === "(" || x.v === "[" || x.v === "{") d++; else if (x.v === ")" || x.v === "]" || x.v === "}") d--; else if (x.v === "," && d === 0) argc++; }
        const named = argT.some((x, q) => x.t === "id" && argT[q + 1] && argT[q + 1].v === ":" && (q === 0 || argT[q - 1].v === ","));
        const eff = taint(k + 2, c, true), raw = taint(k + 2, c, false);
        const args = norm(argT);
        const call = { name, lname, line: t.line, argc, named, args: args.slice(0, 200), key: lname + "(" + args + ")" + (eff.length ? " ⟨tainted⟩" : ""), tainted: eff.length > 0, sources: eff, sanitized: raw.length > 0 && eff.length === 0, first: argT[0] ? (argT[0].t === "str" ? argT[0].v : null) : null };
        calls.push(call);
        if (AUTH_RE.test(lname.replace(/^->/, ""))) auth.push({ name, key: call.key, line: t.line, text: name + "(" + call.args.slice(0, 80) + ")" });
        if (["ini_set", "error_reporting", "set_error_handler", "set_exception_handler", "define", "putenv", "date_default_timezone_set", "setlocale", "ini_restore", "set_include_path"].includes(lv))
          state.push({ kind: lv, key: call.key, line: t.line, text: name + "(" + call.args.slice(0, 100) + ")", name: lv === "define" ? (argT[0] && argT[0].t === "str" ? argT[0].v : args) : null });
        continue;
      }
    }
    if (t.t === "openecho") {
      const e = stmtEnd(T, k + 1);
      const eff = taint(k + 1, e, true), raw = taint(k + 1, e, false);
      echoes.push({ line: t.line, kind: "<?=", expr: norm(T.slice(k + 1, e)).slice(0, 160), key: "<?= " + norm(T.slice(k + 1, e)) + (eff.length ? " ⟨tainted⟩" : ""), tainted: eff.length > 0, sources: eff, sanitized: raw.length > 0 && eff.length === 0 });
      continue;
    }
    if (t.t === "backtick") {
      const eff = taint(k, k + 1, true);
      calls.push({ name: "`backtick`", lname: "`backtick`", line: t.line, argc: 1, named: false, args: t.v.slice(0, 200), key: "`" + t.v + "`" + (eff.length ? " ⟨tainted⟩" : ""), tainted: eff.length > 0, sources: eff, sanitized: false, first: null });
      continue;
    }
    if (t.t === "var" && (t.v === "$GLOBALS" || (SUPERGLOBALS.has(t.v) || t.v === "$_SESSION" || t.v === "$_SERVER" || t.v === "$_ENV")) && next && next.v === "[") {
      const c = matchClose(T, k + 1);
      if (T[c + 1] && T[c + 1].t === "op" && ["=", ".=", "+=", "-=", "??="].includes(T[c + 1].v) && !["$_SESSION"].includes(t.v))
        state.push({ kind: "superglobal_write", key: "write " + t.v + norm(T.slice(k + 1, c + 1)), line: t.line, text: t.v + norm(T.slice(k + 1, c + 1)) + " " + T[c + 1].v + " …" });
    }
  }

  /* 構文の均衡 (php -l の代わりの最低限の検査) */
  const bal = { "(": 0, "[": 0, "{": 0 }; const pair = { ")": "(", "]": "[", "}": "{" };
  let firstBad = null;
  for (const t of T) {
    if (t.t !== "op") continue;
    if (t.v in bal) bal[t.v]++;
    else if (t.v in pair) { bal[pair[t.v]]--; if (bal[pair[t.v]] < 0 && !firstBad) firstBad = t.line; }
  }
  const balanced = !firstBad && bal["("] === 0 && bal["["] === 0 && bal["{"] === 0 && errors.length === 0;
  return {
    tokens: T.length, calls, echoes, includes, defs, auth, state,
    syntax: { balanced, errors, detail: balanced ? "" : (errors.length ? errors.map(e => `line ${e.line}: ${e.msg}`).join("; ") : `括弧の対応: () ${bal["("]}, [] ${bal["["]}, {} ${bal["{"]}` + (firstBad ? ` (line ${firstBad} で閉じ過ぎ)` : "")) },
    tainted_vars: Array.from(tainted)
  };
}

const PHPAnalyzer = { phpLex, analyzePhp };
if (typeof module !== "undefined" && module.exports) module.exports = PHPAnalyzer;
