/*
 * engine.js — Bada 言語処理系 (字句解析 → 構文解析 → 木構造インタプリタ)
 *
 * BadaClaude の頭脳 (brain.bada) はこの処理系の上で動きます。JavaScript が
 * 担うのは「言語そのもの」と、I/O・数値核などのネイティブ組込みだけです。
 * 対話パイプライン (意図推定・検索・計算・生成・台帳記録) はすべて Bada で
 * 書かれています (src/brain.bada)。
 *
 * 文法は bada-source-1.pdf (The Unknown-Prior Engine Language) と
 * bada-quantum-reviser-paper.pdf (Reviser-Extensible Grammars) に従います:
 *   :=  束縛        >>  台帳への commit (append-only)   <-  配列への追加
 *   ::  スコープ    ~   漸進型の整合 (STAR ~ x は常に真)  |x| ラムダ
 *   @reviser { rule 名(引数) { ... } }  — 文法拡張: 規則を台帳に commit し、
 *        以降の文は「名 引数, 引数」という新しい文として構文解析される
 *   qubit q[n] / H / CNOT / Measure — Q# 型量子副言語 (位相核の上に実装)
 */
"use strict";

/* ───────────────────────── 値 ───────────────────────── */
class Complex {
  constructor(re, im) { this.re = re; this.im = im; }
}
const C = (re, im) => new Complex(re, im || 0);
const isC = v => v instanceof Complex;
const toC = v => isC(v) ? v : C(+v, 0);

class Ledger {
  constructor(name) { this.name = name; this.items = []; }
  commit(v) { this.items.push(Object.freeze(v)); return v; }
}

class QReg {
  constructor(n) {
    if (n < 1 || n > 12) throw new BadaError("qubit 数は 1〜12 です");
    this.n = n; this.N = 1 << n;
    this.re = new Float64Array(this.N); this.im = new Float64Array(this.N);
    this.re[0] = 1;
  }
}

class Closure {
  constructor(name, params, body, env, isExpr) {
    this.name = name; this.params = params; this.body = body; this.env = env; this.isExpr = isExpr;
  }
}

class BadaError extends Error {}
class BreakSig {}
class ContinueSig {}
class ReturnSig { constructor(v) { this.v = v; } }

/* ───────────────────────── 字句解析 ───────────────────────── */
const OPS = [":=>", "**", ":=", "::", ">>", "<-", "->", "=>", "==", "!=", "<=", ">=", "&&", "||", "+=", "-=", "*=", "/=",
  "+", "-", "*", "/", "%", "^", "<", ">", "=", "(", ")", "[", "]", "{", "}", ",", ".", ":", ";", "|", "~", "@", "!"];
const KEYWORDS = new Set(["fn", "def", "if", "elif", "else", "while", "for", "in", "return", "break", "continue",
  "true", "false", "nil", "and", "or", "not", "struct", "rule", "qubit"]);
const BINOP_END = new Set(["+", "-", "*", "/", "%", "^", "**", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "and", "or",
  ":=", "=", ">>", "<-", ",", "(", "[", "{", "=>", "->", "::", ".", "~", "+=", "-=", "*=", "/=", "not", "in"]);

function lex(src) {
  const toks = []; let i = 0, line = 1, depth = 0;
  const push = (t, v) => toks.push({ t, v, line });
  const idStart = /[\p{L}_$]/u, idPart = /[\p{L}\p{N}_$']/u;
  while (i < src.length) {
    const c = src[i];
    if (c === "\n") {
      line++; i++;
      if (depth === 0 && toks.length && toks[toks.length - 1].t !== "NL") {
        const last = toks[toks.length - 1];
        if (!(last.t === "op" && BINOP_END.has(last.v) && last.v !== ")" && last.v !== "]" && last.v !== "}")) push("NL", "\n");
      }
      continue;
    }
    if (c === " " || c === "\t" || c === "\r") { i++; continue; }
    if (c === "#" || (c === "/" && src[i + 1] === "/")) { while (i < src.length && src[i] !== "\n") i++; continue; }
    if (/[0-9]/.test(c) || (c === "." && /[0-9]/.test(src[i + 1] || ""))) {
      const m = /^(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/.exec(src.slice(i));
      push("num", parseFloat(m[0])); i += m[0].length; continue;
    }
    if (c === '"' || c === "'" || c === "「") {
      const close = c === "「" ? "」" : c; let s = ""; i++;
      while (i < src.length && src[i] !== close) {
        if (src[i] === "\\" && close !== "」") {
          const n = src[i + 1]; i += 2;
          s += n === "n" ? "\n" : n === "t" ? "\t" : n === "u" ? (() => { const h = src.substr(i, 4); i += 4; return String.fromCharCode(parseInt(h, 16)); })() : n;
          continue;
        }
        if (src[i] === "\n") line++;
        s += src[i++];
      }
      if (src[i] !== close) throw new BadaError(`line ${line}: 文字列が閉じていません`);
      i++; push("str", s); continue;
    }
    if (idStart.test(c)) {
      let j = i + 1; while (j < src.length && idPart.test(src[j])) j++;
      const w = src.slice(i, j); i = j;
      push(KEYWORDS.has(w) ? "kw" : "id", w); continue;
    }
    const op = OPS.find(o => src.startsWith(o, i));
    if (!op) throw new BadaError(`line ${line}: 不明な文字 '${c}'`);
    if (op === "(" || op === "[") depth++;
    if ((op === ")" || op === "]") && depth > 0) depth--;
    push("op", op); i += op.length;
  }
  push("NL", "\n"); push("EOF", null);
  return toks;
}

/* ───────────────────────── 構文解析 ─────────────────────────
 * 文を 1 つずつ解析・実行できるよう、Parser は rules (文法台帳) を参照する。 */
class Parser {
  constructor(toks, rules) { this.toks = toks; this.p = 0; this.rules = rules || new Map(); }
  peek(o) { return this.toks[this.p + (o || 0)]; }
  next() { return this.toks[this.p++]; }
  is(t, v) { const k = this.peek(); return k.t === t && (v === undefined || k.v === v); }
  isOp(v) { return this.is("op", v); }
  isKw(v) { return this.is("kw", v); }
  eat(t, v) {
    const k = this.next();
    if (k.t !== t || (v !== undefined && k.v !== v))
      throw new BadaError(`line ${k.line}: '${v || t}' が必要ですが '${k.v === null ? "EOF" : k.v}' がありました`);
    return k;
  }
  skipNL() { while (this.is("NL") || this.isOp(";")) this.p++; }
  atEnd() { this.skipNL(); return this.is("EOF"); }

  block() {
    this.skipNL(); this.eat("op", "{"); const body = [];
    for (;;) { this.skipNL(); if (this.isOp("}")) break; if (this.is("EOF")) throw new BadaError("'}' がありません"); body.push(this.statement()); }
    this.eat("op", "}"); return { k: "block", body };
  }
  params() {
    this.eat("op", "("); const ps = [];
    while (!this.isOp(")")) { ps.push(this.eat("id").v); if (this.isOp(",")) this.next(); }
    this.eat("op", ")"); return ps;
  }
  statement() {
    this.skipNL(); const t = this.peek(); const line = t.line;
    const st = this.statementInner(); st.line = st.line || line;
    const prev = this.toks[this.p - 1];
    if (!(this.is("NL") || this.isOp(";") || this.isOp("}") || this.is("EOF") || (prev.t === "op" && prev.v === "}" && (st.k === "if" || st.k === "while" || st.k === "for" || st.k === "fndef" || st.k === "annot" || st.k === "rule"))))
      throw new BadaError(`line ${this.peek().line}: 文の終わりに余分な '${this.peek().v}'`);
    return st;
  }
  statementInner() {
    const t = this.peek();
    if (t.t === "kw") {
      switch (t.v) {
        case "fn": case "def":
          if (this.peek(1).t === "id") {
            this.next(); let name = this.eat("id").v;
            if (this.isOp(".")) { this.next(); name += "." + this.eat("id").v; }
            const ps = this.params(); const body = this.block();
            return { k: "fndef", name, params: ps, body };
          }
          break;
        case "if": {
          this.next(); const branches = [[this.expr(), this.block()]]; let els = null;
          for (;;) {
            const save = this.p; this.skipNL();
            if (this.isKw("elif")) { this.next(); branches.push([this.expr(), this.block()]); continue; }
            if (this.isKw("else")) {
              this.next();
              if (this.isKw("if")) { els = { k: "block", body: [this.statementInner()] }; }
              else els = this.block();
            } else this.p = save;
            break;
          }
          return { k: "if", branches, els };
        }
        case "while": { this.next(); const c = this.expr(); return { k: "while", cond: c, body: this.block() }; }
        case "for": {
          this.next(); const a = this.eat("id").v; let b = null;
          if (this.isOp(",")) { this.next(); b = this.eat("id").v; }
          this.eat("kw", "in"); const it = this.expr();
          return { k: "for", a, b, it, body: this.block() };
        }
        case "return": {
          this.next();
          if (this.is("NL") || this.isOp(";") || this.isOp("}") || this.is("EOF")) return { k: "return", e: null };
          return { k: "return", e: this.expr() };
        }
        case "break": this.next(); return { k: "break" };
        case "continue": this.next(); return { k: "continue" };
        case "struct": {
          this.next(); const name = this.eat("id").v; this.eat("op", "{"); const fields = [];
          for (;;) { this.skipNL(); if (this.isOp("}")) break; fields.push(this.eat("id").v); if (this.isOp(",")) this.next(); }
          this.eat("op", "}"); return { k: "struct", name, fields };
        }
        case "rule": {
          this.next(); const name = this.eat("id").v; const ps = this.params(); const body = this.block();
          this.rules.set(name, ps.length);      // 解析時にも文法台帳へ (同じ入力内の後続文から有効)
          return { k: "rule", name, params: ps, body };
        }
        case "qubit": {
          this.next(); const name = this.eat("id").v; this.eat("op", "["); const n = this.expr(); this.eat("op", "]");
          return { k: "qubit", name, n };
        }
      }
    }
    if (t.t === "op" && t.v === "@") {
      this.next(); const kind = this.eat("id").v; let name = null;
      if (this.is("id") || this.is("str")) name = this.next().v;
      // 原稿の見出し (例: @reviser GRAMMAR :=> ) は '{' まで読み飛ばす
      while (!this.isOp("{") && !this.is("EOF")) this.next();
      return { k: "annot", kind, name, body: this.block() };
    }
    // 文法台帳の規則による文:  bell q  /  prepare q, 3
    if (t.t === "id" && this.rules.has(t.v)) {
      const n1 = this.peek(1);
      const callLike = n1.t === "op" && ["(", "=", ":=", ".", "[", "::", "+=", "-=", "*=", "/=", ">>", "<-"].includes(n1.v);
      if (!callLike) {
        this.next(); const args = [];
        if (!(this.is("NL") || this.isOp(";") || this.isOp("}") || this.is("EOF"))) {
          args.push(this.expr()); while (this.isOp(",")) { this.next(); args.push(this.expr()); }
        }
        return { k: "expr", e: { k: "call", f: { k: "name", name: t.v }, args } };
      }
    }
    const e = this.expr();
    if (this.isOp(":=")) {
      if (e.k !== "name") throw new BadaError(`line ${t.line}: ':=' の左辺は名前です`);
      this.next(); return { k: "bind", name: e.name, e: this.expr() };
    }
    if (this.isOp("=") || this.isOp("+=") || this.isOp("-=") || this.isOp("*=") || this.isOp("/=")) {
      const op = this.next().v;
      if (!["name", "index", "member"].includes(e.k)) throw new BadaError(`line ${t.line}: 代入できない左辺です`);
      let rhs = this.expr();
      if (op !== "=") rhs = { k: "bin", op: op[0], l: e, r: rhs };
      return { k: "assign", target: e, e: rhs };
    }
    return { k: "expr", e };
  }

  expr() { return this.commit(); }
  commit() {
    let l = this.or();
    while (this.isOp(">>") || this.isOp("<-") || this.isOp("=>") || this.isOp("->")) {
      const op = this.next().v; const r = this.or();
      l = { k: op === ">>" ? "commit" : op === "<-" ? "append" : "query", l, r };
    }
    return l;
  }
  or() { let l = this.and(); while (this.isOp("||") || this.isKw("or")) { this.next(); l = { k: "or", l, r: this.and() }; } return l; }
  and() { let l = this.not(); while (this.isOp("&&") || this.isKw("and")) { this.next(); l = { k: "and", l, r: this.not() }; } return l; }
  not() { if (this.isKw("not") || this.isOp("!")) { this.next(); return { k: "not", e: this.not() }; } return this.cmp(); }
  cmp() {
    let l = this.add();
    for (;;) {
      const k = this.peek();
      if (k.t === "op" && ["==", "!=", "<", ">", "<=", ">=", "~"].includes(k.v)) { this.next(); l = { k: "bin", op: k.v, l, r: this.add() }; }
      else if (k.t === "kw" && k.v === "in") { this.next(); l = { k: "bin", op: "in", l, r: this.add() }; }
      else return l;
    }
  }
  add() { let l = this.mul(); while (this.isOp("+") || this.isOp("-")) { const op = this.next().v; l = { k: "bin", op, l, r: this.mul() }; } return l; }
  mul() { let l = this.unary(); while (this.isOp("*") || this.isOp("/") || this.isOp("%")) { const op = this.next().v; l = { k: "bin", op, l, r: this.unary() }; } return l; }
  unary() {
    if (this.isOp("-")) { this.next(); return { k: "neg", e: this.unary() }; }
    if (this.isOp("+")) { this.next(); return this.unary(); }
    return this.pow();
  }
  pow() {
    const b = this.postfix();
    if (this.isOp("^") || this.isOp("**")) { this.next(); return { k: "bin", op: "^", l: b, r: this.unary() }; }
    return b;
  }
  postfix() {
    let e = this.primary();
    for (;;) {
      if (this.isOp("(")) {
        this.next(); const args = [];
        while (!this.isOp(")")) { args.push(this.expr()); if (this.isOp(",")) this.next(); else break; }
        this.eat("op", ")"); e = { k: "call", f: e, args };
      } else if (this.isOp("[")) {
        this.next(); const i = this.expr(); this.eat("op", "]"); e = { k: "index", o: e, i };
      } else if (this.isOp(".") || this.isOp("::")) {
        const op = this.next().v; const k = this.next();
        if (k.t !== "id" && k.t !== "kw") throw new BadaError(`line ${k.line}: '${op}' の後に名前が必要です`);
        e = { k: "member", o: e, name: k.v, scope: op === "::" };
      } else return e;
    }
  }
  lambda(params) {
    if (this.isOp("{")) return { k: "lambda", params, body: this.block() };
    return { k: "lambda", params, body: this.expr(), isExpr: true };
  }
  primary() {
    const t = this.next();
    switch (t.t) {
      case "num": return { k: "lit", v: t.v };
      case "str": return { k: "lit", v: t.v };
      case "id": return { k: "name", name: t.v };
      case "kw":
        if (t.v === "true") return { k: "lit", v: true };
        if (t.v === "false") return { k: "lit", v: false };
        if (t.v === "nil") return { k: "lit", v: null };
        if (t.v === "fn" || t.v === "def") { const ps = this.params(); return { k: "lambda", params: ps, body: this.block() }; }
        break;
      case "op":
        if (t.v === "(") { const e = this.expr(); this.eat("op", ")"); return e; }
        if (t.v === "[") {
          const items = []; this.skipNL();
          while (!this.isOp("]")) { items.push(this.expr()); this.skipNL(); if (this.isOp(",")) { this.next(); this.skipNL(); } else break; }
          this.skipNL(); this.eat("op", "]"); return { k: "list", items };
        }
        if (t.v === "{") {
          const pairs = []; this.skipNL();
          while (!this.isOp("}")) {
            const kt = this.next(); let key;
            if (kt.t === "id" || kt.t === "str" || kt.t === "kw") key = { k: "lit", v: String(kt.v) };
            else if (kt.t === "num") key = { k: "lit", v: String(kt.v) };
            else if (kt.t === "op" && kt.v === "[") { key = this.expr(); this.eat("op", "]"); }
            else throw new BadaError(`line ${kt.line}: マップのキーが不正です`);
            this.eat("op", ":"); this.skipNL(); pairs.push([key, this.expr()]); this.skipNL();
            if (this.isOp(",")) { this.next(); this.skipNL(); } else break;
          }
          this.skipNL(); this.eat("op", "}"); return { k: "map", pairs };
        }
        if (t.v === "|") {
          const ps = [];
          while (!this.isOp("|")) { ps.push(this.eat("id").v); if (this.isOp(",")) this.next(); }
          this.eat("op", "|"); return this.lambda(ps);
        }
        if (t.v === "||") return this.lambda([]);
        break;
    }
    throw new BadaError(`line ${t.line}: 予期しない '${t.v === null ? "EOF" : t.v}'`);
  }
}

/* ───────────────────────── 環境 ───────────────────────── */
class Env {
  constructor(parent) { this.vars = new Map(); this.parent = parent || null; }
  lookup(n) { for (let e = this; e; e = e.parent) if (e.vars.has(n)) return e; return null; }
  get(n) { const e = this.lookup(n); if (!e) throw new BadaError(`未定義の名前 '${n}'`); return e.vars.get(n); }
  def(n, v) { this.vars.set(n, v); return v; }
  set(n, v) { const e = this.lookup(n); (e || this).vars.set(n, v); return v; }
}

/* ───────────────────────── 表示 ───────────────────────── */
function fnum(x) {
  if (!isFinite(x)) return isNaN(x) ? "NaN" : (x > 0 ? "∞" : "-∞");
  if (Number.isInteger(x) && Math.abs(x) < 1e15) return String(x);
  const a = Math.abs(x);
  if (a !== 0 && (a < 1e-4 || a >= 1e10)) return x.toExponential(6).replace(/\.?0+e/, "e");
  return String(+x.toPrecision(10));
}
function show(v, depth) {
  depth = depth || 0;
  if (v === null || v === undefined) return "nil";
  if (typeof v === "number") return fnum(v);
  if (typeof v === "string") return depth ? JSON.stringify(v) : v;
  if (typeof v === "boolean") return v ? "true" : "false";
  if (isC(v)) {
    if (Math.abs(v.im) < 1e-15) return fnum(v.re);
    return `${fnum(v.re)} ${v.im < 0 ? "-" : "+"} ${fnum(Math.abs(v.im))}i`;
  }
  if (Array.isArray(v)) {
    if (depth > 3) return "[…]";
    const items = v.slice(0, 40).map(x => show(x, depth + 1));
    return "[" + items.join(", ") + (v.length > 40 ? `, … (${v.length})` : "") + "]";
  }
  if (v instanceof Closure) return `<fn ${v.name || "λ"}(${v.params.join(", ")})>`;
  if (typeof v === "function") return `<native ${v.bname || "fn"}>`;
  if (v instanceof Ledger) return `<Ω ${v.name}: ${v.items.length} facts>`;
  if (v instanceof QReg) return `<qubit[${v.n}] ${qstateString(v)}>`;
  if (typeof v === "object") {
    if (depth > 3) return "{…}";
    const ks = Object.keys(v).filter(k => k !== "__type");
    const body = ks.slice(0, 30).map(k => `${k}: ${show(v[k], depth + 1)}`).join(", ");
    return (v.__type ? v.__type + " " : "") + "{" + body + (ks.length > 30 ? ", …" : "") + "}";
  }
  return String(v);
}
const truthy = v => !(v === null || v === undefined || v === false || v === 0 || v === "");

/* ───────────────────────── 数値核 ───────────────────────── */
const LG = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
  -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
function gamma(x) {
  if (x < 0.5) return Math.PI / (Math.sin(Math.PI * x) * gamma(1 - x));
  x -= 1; let a = LG[0]; const t = x + 7.5;
  for (let i = 1; i < 9; i++) a += LG[i] / (x + i);
  return Math.sqrt(2 * Math.PI) * Math.pow(t, x + 0.5) * Math.exp(-t) * a;
}
function lgamma(x) {
  if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lgamma(1 - x);
  x -= 1; let a = LG[0]; const t = x + 7.5;
  for (let i = 1; i < 9; i++) a += LG[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}
function beta(p, q) {
  if (p > 0 && q > 0) return Math.exp(lgamma(p) + lgamma(q) - lgamma(p + q));
  return gamma(p) * gamma(q) / gamma(p + q);
}
function digamma(x) {
  let r = 0; while (x < 6) { r -= 1 / x; x += 1; }
  const f = 1 / (x * x);
  return r + Math.log(x) - 0.5 / x - f * (1 / 12 - f * (1 / 120 - f * (1 / 252 - f * (1 / 240 - f / 132))));
}
/* 複素演算 */
const cadd = (a, b) => C(a.re + b.re, a.im + b.im);
const csub = (a, b) => C(a.re - b.re, a.im - b.im);
const cmul = (a, b) => C(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
const cdiv = (a, b) => { const d = b.re * b.re + b.im * b.im; return C((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d); };
const cexp = a => { const m = Math.exp(a.re); return C(m * Math.cos(a.im), m * Math.sin(a.im)); };
const clog = a => C(Math.log(Math.hypot(a.re, a.im)), Math.atan2(a.im, a.re));
const cabs = a => Math.hypot(a.re, a.im);
const cpow = (a, b) => (a.re === 0 && a.im === 0) ? C(0, 0) : cexp(cmul(b, clog(a)));
const csin = a => C(Math.sin(a.re) * Math.cosh(a.im), Math.cos(a.re) * Math.sinh(a.im));
const ccos = a => C(Math.cos(a.re) * Math.cosh(a.im), -Math.sin(a.re) * Math.sinh(a.im));
const csqrt = a => { const r = cabs(a), t = Math.atan2(a.im, a.re) / 2, s = Math.sqrt(r); return C(s * Math.cos(t), s * Math.sin(t)); };
/* 複素 log Γ: 平行移動 + Stirling 級数 (Re z > 0 で連続な分枝) */
function clgamma(z) {
  let shift = C(0, 0);
  while (z.re < 10) { shift = cadd(shift, clog(z)); z = cadd(z, C(1, 0)); }
  const zi = cdiv(C(1, 0), z), zi2 = cmul(zi, zi);
  let s = cadd(csub(cmul(csub(z, C(0.5, 0)), clog(z)), z), C(0.5 * Math.log(2 * Math.PI), 0));
  const co = [1 / 12, -1 / 360, 1 / 1260, -1 / 1680];
  let term = zi;
  for (const c of co) { s = cadd(s, C(term.re * c, term.im * c)); term = cmul(term, zi2); }
  return csub(s, shift);
}
/* ζ(s): Borwein のイータ加速 (Re s > 0) + 関数等式 (Re s ≤ 0) */
function czeta(s) {
  s = toC(s);
  if (Math.abs(s.re - 1) < 1e-12 && Math.abs(s.im) < 1e-12) return C(Infinity, 0);
  if (s.re < 0.5) {
    // ζ(s) = 2^s π^(s−1) sin(πs/2) Γ(1−s) ζ(1−s)
    const one = C(1, 0), oms = csub(one, s);
    const g = cexp(clgamma(oms));
    const f = cmul(cmul(cpow(C(2, 0), s), cpow(C(Math.PI, 0), csub(s, one))), csin(C(Math.PI * s.re / 2, Math.PI * s.im / 2)));
    return cmul(cmul(f, g), czeta(oms));
  }
  const n = Math.min(400, 40 + Math.ceil(Math.abs(s.im) * 1.3));
  const d = new Array(n + 1); let sum = 0;
  for (let i = 0; i <= n; i++) {
    // d_i = n Σ_{j=0}^{i} (n+j−1)! 4^j / ((n−j)! (2j)!)  を対数で安定に
    const lt = Math.log(n) + lgamma(n + i) + i * Math.log(4) - lgamma(n - i + 1) - lgamma(2 * i + 1);
    sum += Math.exp(lt - (n * Math.log(5.8284271247461903)));
    d[i] = sum;
  }
  let acc = C(0, 0);
  for (let k = 0; k < n; k++) {
    const w = (k % 2 ? -1 : 1) * (d[k] - d[n]);
    const term = cexp(cmul(C(-Math.log(k + 1), 0), s));
    acc = cadd(acc, C(w * term.re, w * term.im));
  }
  const eta = C(-acc.re / d[n], -acc.im / d[n]);
  const denom = csub(C(1, 0), cpow(C(2, 0), csub(C(1, 0), s)));
  return cdiv(eta, denom);
}
function zeta(s) {
  if (isC(s)) return czeta(s);
  if (s === 1) return Infinity;
  if (s < 0 && Number.isInteger(s) && s % 2 === 0) return 0;
  return czeta(C(s, 0)).re;
}
function rsTheta(t) { return clgamma(C(0.25, t / 2)).im - (t / 2) * Math.log(Math.PI); }
function rsZ(t) { const th = rsTheta(t); return cmul(C(Math.cos(th), Math.sin(th)), czeta(C(0.5, t))).re; }
function lambertw(x) {
  if (x < -1 / Math.E) return NaN;
  let w;
  if (x < -0.32) w = -1 + Math.sqrt(2 * (1 + Math.E * x));
  else if (x < 3) w = Math.log1p(x);
  else w = Math.log(x) - Math.log(Math.log(x));
  for (let i = 0; i < 60; i++) {
    const ew = Math.exp(w), f = w * ew - x, wp1 = w + 1;
    const dw = f / (ew * wp1 - (w + 2) * f / (2 * wp1));
    w -= dw; if (Math.abs(dw) < 1e-15 * (1 + Math.abs(w))) break;
  }
  return w;
}
/* Jones 多項式 (blueprint の表記と同じ向き) */
const JONES = {
  "3_1": [[-4, -1], [-3, 1], [-1, 1]],
  "4_1": [[-2, 1], [-1, -1], [0, 1], [1, -1], [2, 1]],
  "5_1": [[2, 1], [4, 1], [5, -1], [6, 1], [7, -1]],
  "unknot": [[0, 1]],
};
function jones(knot, t) {
  const poly = JONES[knot]; if (!poly) throw new BadaError(`未知の結び目 '${knot}' (3_1, 4_1, 5_1, unknot)`);
  let acc = C(0, 0); const tc = toC(t);
  for (const [e, c] of poly) { const p = cpow(tc, C(e, 0)); acc = cadd(acc, C(c * p.re, c * p.im)); }
  return Math.abs(acc.im) < 1e-14 ? acc.re : acc;
}
function jonesString(knot) {
  const poly = JONES[knot]; if (!poly) return "?";
  return poly.map(([e, c], i) => {
    const sg = c < 0 ? "-" : (i ? "+" : ""); const mono = e === 0 ? "1" : (e === 1 ? "t" : `t^${e}`);
    return (i ? " " : "") + sg + (i && sg ? " " : "") + mono;
  }).join("");
}

/* ─────────── Unknown-Prior Engine (原稿 S.12〜S.26 / Q.1〜Q.21) ─────────── */
function softmax(z) {
  const m = Math.max(...z); const p = z.map(v => (v - m < -30 ? 0 : Math.exp(v - m)));
  const s = p.reduce((a, b) => a + b, 0); return p.map(v => v / s);
}
function entropy(p) { let h = 0; for (const x of p) { const q = Math.max(x, 1e-12); h -= q * Math.log(q); } return h; }
function normalize(p) { const s = p.reduce((a, b) => a + b, 0); return s > 0 ? p.map(v => v / s) : p.slice(); }
function update(p, e, lr) {
  lr = lr === undefined ? 0.5 : lr;
  return normalize(p.map((v, i) => (1 - lr) * v + lr * (e[i] || 0)));
}
function cognitiveSystem(a, modules, betas) {
  const V = a.length; const theta = new Array(V).fill(0);
  modules.forEach((m, k) => {
    const q = m[0], phi = m[1] || []; const b = betas && betas[k] !== undefined ? betas[k] : 1;
    const H = entropy(q);
    for (let i = 0; i < V; i++) theta[i] += b * H * (Array.isArray(phi) ? (phi[i] || 0) : phi);
  });
  const psi = a.map((ai, i) => C(Math.sqrt(ai) * Math.cos(theta[i]), Math.sqrt(ai) * Math.sin(theta[i])));
  const mod = psi.map(z => z.re * z.re + z.im * z.im);
  const q = normalize(mod);
  let md = 0; for (let i = 0; i < V; i++) md = Math.max(md, Math.abs(q[i] - a[i]));
  const zeros = []; q.forEach((v, i) => { if (v === 0) zeros.push(i); });
  return { a, theta, psi, q, maxdiff: md, zeros, entropy: entropy(q) };
}

/* ─────────── 量子レジスタ (Q# 型副言語の数値核) ─────────── */
function q1(reg, i, m) {   // m = [[a,b],[c,d]] 複素 2x2
  const bit = 1 << i;
  for (let s = 0; s < reg.N; s++) {
    if (s & bit) continue;
    const t = s | bit;
    const ar = reg.re[s], ai = reg.im[s], br = reg.re[t], bi = reg.im[t];
    const [[a, b], [c, d]] = m;
    reg.re[s] = a.re * ar - a.im * ai + b.re * br - b.im * bi;
    reg.im[s] = a.re * ai + a.im * ar + b.re * bi + b.im * br;
    reg.re[t] = c.re * ar - c.im * ai + d.re * br - d.im * bi;
    reg.im[t] = c.re * ai + c.im * ar + d.re * bi + d.im * br;
  }
  return reg;
}
const R2 = Math.SQRT1_2;
const GATES = {
  H: [[C(R2), C(R2)], [C(R2), C(-R2)]],
  X: [[C(0), C(1)], [C(1), C(0)]],
  Y: [[C(0), C(0, -1)], [C(0, 1), C(0)]],
  Z: [[C(1), C(0)], [C(0), C(-1)]],
  S: [[C(1), C(0)], [C(0), C(0, 1)]],
  T: [[C(1), C(0)], [C(0), C(R2, R2)]],
};
function rot(axis, th) {
  const c = Math.cos(th / 2), s = Math.sin(th / 2);
  if (axis === "X") return [[C(c), C(0, -s)], [C(0, -s), C(c)]];
  if (axis === "Y") return [[C(c), C(-s)], [C(s), C(c)]];
  return [[C(Math.cos(-th / 2), Math.sin(-th / 2)), C(0)], [C(0), C(Math.cos(th / 2), Math.sin(th / 2))]];
}
function qcheck(reg, ...idx) {
  if (!(reg instanceof QReg)) throw new BadaError("量子レジスタが必要です (qubit q[n])");
  for (const i of idx) if (!(Number.isInteger(i) && i >= 0 && i < reg.n)) throw new BadaError(`qubit 番号 ${i} は範囲外です`);
}
function cnot(reg, c, t) {
  const cb = 1 << c, tb = 1 << t;
  for (let s = 0; s < reg.N; s++) if ((s & cb) && !(s & tb)) {
    const u = s | tb; let x = reg.re[s]; reg.re[s] = reg.re[u]; reg.re[u] = x; x = reg.im[s]; reg.im[s] = reg.im[u]; reg.im[u] = x;
  }
  return reg;
}
function qprobs(reg) { const p = []; for (let s = 0; s < reg.N; s++) p.push(reg.re[s] ** 2 + reg.im[s] ** 2); return p; }
function bits(s, n) { let b = ""; for (let i = n - 1; i >= 0; i--) b += (s >> i) & 1; return b; }
function qstateString(reg) {
  const parts = [];
  for (let s = 0; s < reg.N; s++) {
    const re = reg.re[s], im = reg.im[s]; if (re * re + im * im < 1e-12) continue;
    const amp = Math.abs(im) < 1e-12 ? fnum(+re.toFixed(4)) : `(${fnum(+re.toFixed(4))}${im < 0 ? "-" : "+"}${fnum(+Math.abs(im).toFixed(4))}i)`;
    parts.push(`${amp}|${bits(s, reg.n)}⟩`);
  }
  return parts.join(" + ").replace(/\+ -/g, "- ") || "0";
}

/* ─────────── 決定論的乱数 (mulberry32) ─────────── */
function makeRng(seed) {
  let a = seed >>> 0;
  return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

/* ─────────── 日本語混じりテキストの分かち書き (文字種の連なり) ─────────── */
function tokens(s) {
  const out = [];
  const re = /[\p{Script=Han}々〆]+|[\p{Script=Katakana}ー]+|[\p{Script=Hiragana}]+|[A-Za-z][A-Za-z0-9_'.]*[A-Za-z0-9]|[A-Za-z]|\d+(?:\.\d+)?|[α-ωΑ-Ωβζγπψφθλ∫∮∇□⊕⊗ℏ]/gu;
  let m; const low = String(s).toLowerCase();
  while ((m = re.exec(low))) {
    const w = m[0];
    if (/^[\p{Script=Han}]+$/u.test(w) && w.length > 2) {   // 長い漢字列は 2-gram も索引へ
      out.push(w); for (let i = 0; i + 2 <= w.length; i++) out.push(w.slice(i, i + 2));
    } else out.push(w);
  }
  return out;
}

/* ───────────────────────── インタプリタ ───────────────────────── */
class Interp {
  constructor(opts) {
    opts = opts || {};
    this.out = []; this.steps = 0; this.maxSteps = opts.maxSteps || 2e7;
    this.rules = new Map();                       // 文法台帳 (解析器が読む)
    this.Omega = new Ledger("Omega");
    this.global = new Env(null);
    this.rng = makeRng(opts.seed || 20260918);
    this.host = opts.host || {};
    installNatives(this);
  }
  print(s) { this.out.push(s); if (this.host.onPrint) this.host.onPrint(s); }
  /* 文を 1 つずつ解析・実行する: 前の文で commit された rule が次の文の構文になる */
  run(src, env) {
    env = env || this.global;
    const toks = lex(src); const P = new Parser(toks, this.rules);
    let last = null;
    while (!P.atEnd()) { const st = P.statement(); last = this.exec(st, env); }
    return last;
  }
  evalExpr(src, env) {
    const P = new Parser(lex(src), this.rules); const e = P.expr(); P.skipNL();
    if (!P.is("EOF")) throw new BadaError(`式の後に余分な '${P.peek().v}'`);
    return this.eval(e, env || this.global);
  }
  tick() { if (++this.steps > this.maxSteps) throw new BadaError("実行ステップ上限に達しました (無限ループ?)"); }
  execBlock(b, env) { let last = null; for (const s of b.body) last = this.exec(s, env); return last; }
  exec(s, env) {
    this.tick();
    try {
      return this.execInner(s, env);
    } catch (e) {
      if (e instanceof BadaError && !/^line \d+/.test(e.message) && s.line) e.message = `line ${s.line}: ${e.message}`;
      throw e;
    }
  }
  execInner(s, env) {
    switch (s.k) {
      case "expr": return this.eval(s.e, env);
      case "bind": return env.def(s.name, this.eval(s.e, env));
      case "assign": return this.assign(s.target, this.eval(s.e, env), env);
      case "fndef": {
        if (s.name.includes(".")) {
          const [tn, mn] = s.name.split("."); const T = env.get(tn);
          if (!T || !T.__methods) throw new BadaError(`'${tn}' は struct ではありません`);
          T.__methods[mn] = new Closure(s.name, s.params, s.body, env); return null;
        }
        return env.def(s.name, new Closure(s.name, s.params, s.body, env));
      }
      case "if": {
        for (const [c, b] of s.branches) if (truthy(this.eval(c, env))) return this.execBlock(b, new Env(env));
        return s.els ? this.execBlock(s.els, new Env(env)) : null;
      }
      case "while": {
        while (truthy(this.eval(s.cond, env))) {
          this.tick();
          try { this.execBlock(s.body, new Env(env)); }
          catch (e) { if (e instanceof BreakSig) break; if (e instanceof ContinueSig) continue; throw e; }
        }
        return null;
      }
      case "for": {
        const it = this.eval(s.it, env);
        let seq;
        if (Array.isArray(it)) seq = it.map((v, i) => [v, i]);
        else if (typeof it === "string") seq = Array.from(it).map((v, i) => [v, i]);
        else if (it instanceof Ledger) seq = it.items.map((v, i) => [v, i]);
        else if (it && typeof it === "object") seq = Object.keys(it).filter(k => k !== "__type").map(k => [k, it[k]]);
        else throw new BadaError("for の対象は配列・文字列・マップ・台帳です");
        for (const [v, i] of seq) {
          this.tick(); const e2 = new Env(env);
          if (s.b) { e2.def(s.a, v); e2.def(s.b, i); } else e2.def(s.a, v);
          try { this.execBlock(s.body, e2); }
          catch (e) { if (e instanceof BreakSig) break; if (e instanceof ContinueSig) continue; throw e; }
        }
        return null;
      }
      case "return": throw new ReturnSig(s.e ? this.eval(s.e, env) : null);
      case "break": throw new BreakSig();
      case "continue": throw new ContinueSig();
      case "struct": {
        const fields = s.fields; const methods = {};
        const ctor = (args) => {
          const o = { __type: s.name }; fields.forEach((f, i) => { o[f] = args[i] === undefined ? null : args[i]; });
          Object.defineProperty(o, "__methods", { value: methods, enumerable: false });
          return o;
        };
        ctor.bname = s.name; ctor.__methods = methods;
        return env.def(s.name, ctor);
      }
      case "rule": {
        const fn = new Closure(s.name, s.params, s.body, env);
        this.rules.set(s.name, s.params.length);
        this.Omega.commit(["rule", s.name, "stmt", s.params.slice(), "denotation"]);
        return env.def(s.name, fn);
      }
      case "qubit": {
        const n = this.eval(s.n, env); const reg = new QReg(n);
        this.Omega.commit(["qubit", s.name, n]);
        return env.def(s.name, reg);
      }
      case "annot": {
        this.Omega.commit(["@" + s.kind, s.name || "", "open"]);
        const r = this.execBlock(s.body, env);           // reviser の規則は囲む環境に定義される
        this.Omega.commit(["@" + s.kind, s.name || "", "commit"]);
        return r;
      }
    }
    throw new BadaError("不明な文 " + s.k);
  }
  assign(t, v, env) {
    if (t.k === "name") return env.set(t.name, v);
    const o = this.eval(t.o, env);
    if (t.k === "index") {
      const i = this.eval(t.i, env);
      if (Array.isArray(o)) { if (typeof i !== "number") throw new BadaError("配列の添字は数です"); o[i < 0 ? o.length + i : i] = v; return v; }
      if (o && typeof o === "object") { o[String(i)] = v; return v; }
    }
    if (t.k === "member" && o && typeof o === "object" && !(o instanceof Ledger)) { o[t.name] = v; return v; }
    throw new BadaError("代入できない対象です");
  }
  call(f, args) {
    this.tick();
    if (typeof f === "function") return f(args, this);
    if (f instanceof Closure) {
      const env = new Env(f.env);
      f.params.forEach((p, i) => env.def(p, args[i] === undefined ? null : args[i]));
      if (f.isExpr) return this.eval(f.body, env);
      try { return this.execBlock(f.body, env); }
      catch (e) { if (e instanceof ReturnSig) return e.v; throw e; }
    }
    throw new BadaError(`${show(f)} は関数ではありません`);
  }
  eval(e, env) {
    switch (e.k) {
      case "lit": return e.v;
      case "name": return env.get(e.name);
      case "list": return e.items.map(x => this.eval(x, env));
      case "map": { const o = {}; for (const [k, v] of e.pairs) o[String(this.eval(k, env))] = this.eval(v, env); return o; }
      case "lambda": return new Closure(null, e.params, e.body, env, e.isExpr);
      case "neg": { const v = this.eval(e.e, env); return isC(v) ? C(-v.re, -v.im) : -num(v); }
      case "not": return !truthy(this.eval(e.e, env));
      case "and": { const l = this.eval(e.l, env); return truthy(l) ? this.eval(e.r, env) : l; }
      case "or": { const l = this.eval(e.l, env); return truthy(l) ? l : this.eval(e.r, env); }
      case "bin": return binop(e.op, this.eval(e.l, env), this.eval(e.r, env));
      case "commit": {
        const l = this.eval(e.l, env), r = this.eval(e.r, env);
        if (l instanceof Ledger) return l.commit(r);
        if (Array.isArray(l)) { l.push(r); return r; }
        throw new BadaError(">> の左辺は台帳 (Omega / tuplespace) です");
      }
      case "append": {
        const l = this.eval(e.l, env), r = this.eval(e.r, env);
        if (Array.isArray(l)) { l.push(r); return l; }
        if (l instanceof Ledger) { l.commit(r); return l; }
        throw new BadaError("<- の左辺は配列です");
      }
      case "query": {   // xs => f  : 写像 / パターン照会
        const l = this.eval(e.l, env), r = this.eval(e.r, env);
        const src = l instanceof Ledger ? l.items : l;
        if (Array.isArray(src) && (r instanceof Closure || typeof r === "function")) return src.map(x => this.call(r, [x]));
        if (r instanceof Closure || typeof r === "function") return this.call(r, [l]);
        return r;
      }
      case "call": {
        if (e.f.k === "member" && !e.f.scope) {   // メソッド呼び出し
          const o = this.eval(e.f.o, env);
          if (o && typeof o === "object" && o.__methods && o.__methods[e.f.name])
            return this.call(o.__methods[e.f.name], [o, ...e.args.map(a => this.eval(a, env))]);
        }
        const f = this.eval(e.f, env);
        return this.call(f, e.args.map(a => this.eval(a, env)));
      }
      case "index": {
        const o = this.eval(e.o, env), i = this.eval(e.i, env);
        if (Array.isArray(o) || typeof o === "string") {
          const k = i < 0 ? o.length + i : i; const v = o[k];
          if (Array.isArray(o) && (k < 0 || k >= o.length)) throw new BadaError(`添字 ${i} は範囲外 (長さ ${o.length})`);
          return v === undefined ? null : v;
        }
        if (o instanceof Ledger) return o.items[i] === undefined ? null : o.items[i];
        if (o && typeof o === "object") { const v = o[String(i)]; return v === undefined ? null : v; }
        throw new BadaError(`${show(o)} は添字で参照できません`);
      }
      case "member": {
        const o = this.eval(e.o, env);
        if (o instanceof Ledger) {
          if (e.name === "DATABASE" || e.name === "items") return o.items;
          if (e.name === "size" || e.name === "len") return o.items.length;
          if (e.name === "name") return o.name;
        }
        if (o instanceof QReg && e.name === "n") return o.n;
        if (o && (typeof o === "object" || typeof o === "function")) {
          const v = o[e.name];
          if (v !== undefined && !(typeof o === "function" && e.name in Function.prototype)) return v;
          return null;
        }
        if (typeof o === "string" && e.name === "len") return o.length;
        if (Array.isArray(o) && e.name === "len") return o.length;
        throw new BadaError(`${show(o)} に '${e.name}' はありません`);
      }
    }
    throw new BadaError("不明な式 " + e.k);
  }
}
function num(v) {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  throw new BadaError(`数が必要ですが ${show(v, 1)} でした`);
}
function eq(a, b) {
  if (isC(a) || isC(b)) { const x = toC(a), y = toC(b); return x.re === y.re && x.im === y.im; }
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => eq(v, b[i]));
  return a === b;
}
function binop(op, a, b) {
  if (op === "==") return eq(a, b);
  if (op === "!=") return !eq(a, b);
  if (op === "~") return a === "STAR" || b === "STAR" || a === null || b === null || typeof a === typeof b;
  if (op === "in") {
    if (Array.isArray(b)) return b.some(x => eq(x, a));
    if (typeof b === "string") return b.includes(String(a));
    if (b instanceof Ledger) return b.items.some(x => eq(x, a));
    if (b && typeof b === "object") return Object.prototype.hasOwnProperty.call(b, String(a));
    return false;
  }
  if (op === "+") {
    if (typeof a === "string" || typeof b === "string") return show(a) + show(b);
    if (Array.isArray(a) && Array.isArray(b)) return a.concat(b);
  }
  if (isC(a) || isC(b)) {
    const x = toC(a), y = toC(b);
    switch (op) {
      case "+": return cadd(x, y); case "-": return csub(x, y); case "*": return cmul(x, y);
      case "/": return cdiv(x, y); case "^": return cpow(x, y);
    }
    throw new BadaError(`複素数に '${op}' は使えません`);
  }
  if (op === "*" && typeof a === "string" && typeof b === "number") return a.repeat(Math.max(0, b));
  const x = num(a), y = num(b);
  switch (op) {
    case "+": return x + y; case "-": return x - y; case "*": return x * y;
    case "/": return y === 0 ? 0 : x / y;              // 原稿 S.25: a/b = 0 if b = 0
    case "%": return y === 0 ? 0 : x % y;
    case "^": if (x < 0 && !Number.isInteger(y)) return cpow(C(x, 0), C(y, 0)); return Math.pow(x, y);
    case "<": return x < y; case ">": return x > y; case "<=": return x <= y; case ">=": return x >= y;
  }
  throw new BadaError("不明な演算子 " + op);
}

/* ───────────────────────── 組込み ───────────────────────── */
function installNatives(I) {
  const g = I.global;
  const def = (name, fn) => { fn.bname = name; g.def(name, fn); };
  const arr = v => { if (!Array.isArray(v)) throw new BadaError(`配列が必要ですが ${show(v, 1)} でした`); return v; };
  const fcall = (f, ...a) => I.call(f, a);
  const cplx = (f, fc) => ([x]) => isC(x) ? fc(x) : f(num(x));

  g.def("Omega", I.Omega); g.def("tuplespace", I.Omega);
  g.def("pi", Math.PI); g.def("π", Math.PI); g.def("e", Math.E); g.def("I", C(0, 1)); g.def("i_", C(0, 1));
  g.def("phi", (1 + Math.sqrt(5)) / 2); g.def("euler_gamma", 0.5772156649015329); g.def("STAR", "STAR");
  g.def("inf", Infinity);

  /* 入出力と基本 */
  def("print", a => { I.print(a.map(x => show(x)).join(" ")); return null; });
  def("show", a => show(a[0], 1));
  def("str", a => show(a[0]));
  def("num", a => { const v = parseFloat(a[0]); return isNaN(v) ? null : v; });
  def("int", a => Math.trunc(num(a[0])));
  def("type", a => { const v = a[0]; return v === null ? "nil" : Array.isArray(v) ? "array" : isC(v) ? "complex" : v instanceof Ledger ? "tuplespace" : v instanceof QReg ? "qubits" : (v instanceof Closure || typeof v === "function") ? "func" : (v && v.__type) ? v.__type : typeof v === "object" ? "map" : typeof v; });
  def("len", a => { const v = a[0]; if (v instanceof Ledger) return v.items.length; if (Array.isArray(v) || typeof v === "string") return v.length; if (v && typeof v === "object") return Object.keys(v).length; return 0; });
  def("push", a => { arr(a[0]).push(a[1]); return a[0]; });
  def("pop", a => { const v = arr(a[0]).pop(); return v === undefined ? null : v; });
  def("keys", a => Object.keys(a[0] || {}).filter(k => k !== "__type"));
  def("values", a => Object.keys(a[0] || {}).filter(k => k !== "__type").map(k => a[0][k]));
  def("has", a => a[0] != null && Object.prototype.hasOwnProperty.call(a[0], String(a[1])));
  def("get", a => { const o = a[0]; if (o && typeof o === "object" && Object.prototype.hasOwnProperty.call(o, String(a[1]))) return o[String(a[1])]; return a[2] === undefined ? null : a[2]; });
  def("range", a => { let [s, e, st] = a.length === 1 ? [0, num(a[0]), 1] : [num(a[0]), num(a[1]), a[2] === undefined ? 1 : num(a[2])]; const r = []; if (st === 0) return r; for (let x = s; st > 0 ? x < e : x > e; x += st) { r.push(x); if (r.length > 1e6) break; } return r; });
  def("map", a => arr(a[0]).map((x, i) => fcall(a[1], x, i)));
  def("filter", a => arr(a[0]).filter((x, i) => truthy(fcall(a[1], x, i))));
  def("fold", a => arr(a[0]).reduce((acc, x) => fcall(a[2], acc, x), a[1]));
  def("each", a => { arr(a[0]).forEach((x, i) => fcall(a[1], x, i)); return null; });
  def("any", a => arr(a[0]).some(x => truthy(a[1] ? fcall(a[1], x) : x)));
  def("all", a => arr(a[0]).every(x => truthy(a[1] ? fcall(a[1], x) : x)));
  def("sum", a => arr(a[0]).reduce((s, x) => (isC(s) || isC(x)) ? cadd(toC(s), toC(x)) : s + num(x), 0));
  def("sort", a => arr(a[0]).slice().sort((x, y) => (typeof x === "string" ? (x < y ? -1 : x > y ? 1 : 0) : x - y)));
  def("sortby", a => arr(a[0]).map(x => [num(fcall(a[1], x)), x]).sort((p, q) => p[0] - q[0]).map(p => p[1]));
  def("reverse", a => typeof a[0] === "string" ? Array.from(a[0]).reverse().join("") : arr(a[0]).slice().reverse());
  def("slice", a => { const v = a[0]; const s = a[1] === undefined ? 0 : num(a[1]); const e = a[2] === undefined || a[2] === null ? undefined : num(a[2]); return typeof v === "string" ? Array.from(v).slice(s, e).join("") : arr(v).slice(s, e); });
  def("index_of", a => Array.isArray(a[0]) ? a[0].findIndex(x => eq(x, a[1])) : String(a[0]).indexOf(String(a[1])));
  def("unique", a => { const seen = new Set(), out = []; for (const x of arr(a[0])) { const k = typeof x + ":" + show(x, 1); if (!seen.has(k)) { seen.add(k); out.push(x); } } return out; });
  def("zip", a => arr(a[0]).map((x, i) => [x, arr(a[1])[i]]));
  def("argmax", a => { const v = arr(a[0]); let b = 0; v.forEach((x, i) => { if (num(x) > num(v[b])) b = i; }); return b; });
  def("argsort_desc", a => arr(a[0]).map((x, i) => [num(x), i]).sort((p, q) => q[0] - p[0]).map(p => p[1]));
  def("min", a => Math.min(...(a.length === 1 && Array.isArray(a[0]) ? a[0] : a).map(num)));
  def("max", a => Math.max(...(a.length === 1 && Array.isArray(a[0]) ? a[0] : a).map(num)));
  def("copy", a => JSON.parse(JSON.stringify(a[0])));
  def("json", a => JSON.stringify(a[0], (k, v) => isC(v) ? show(v) : v));

  /* 文字列 */
  def("split", a => String(a[0]).split(a[1] === undefined ? /\s+/ : String(a[1])).filter(x => a[1] !== undefined || x !== ""));
  def("join", a => arr(a[0]).map(x => show(x)).join(a[1] === undefined ? "" : String(a[1])));
  def("lower", a => String(a[0]).toLowerCase());
  def("upper", a => String(a[0]).toUpperCase());
  def("trim", a => String(a[0]).trim());
  def("contains", a => Array.isArray(a[0]) ? a[0].some(x => eq(x, a[1])) : String(a[0]).includes(String(a[1])));
  def("startswith", a => String(a[0]).startsWith(String(a[1])));
  def("endswith", a => String(a[0]).endsWith(String(a[1])));
  def("replace", a => String(a[0]).split(String(a[1])).join(String(a[2])));
  def("chars", a => Array.from(String(a[0])));
  def("repeat", a => String(a[0]).repeat(Math.max(0, num(a[1]))));
  def("match", a => { const m = new RegExp(String(a[1]), "u").exec(String(a[0])); return m ? Array.from(m, x => x === undefined ? null : x) : null; });
  def("match_all", a => Array.from(String(a[0]).matchAll(new RegExp(String(a[1]), "gu")), m => m[0]));
  def("tokens", a => tokens(a[0]));
  def("f5", a => num(a[0]).toFixed(5));
  def("fixed", a => num(a[0]).toFixed(a[1] === undefined ? 4 : num(a[1])));
  def("sci", a => num(a[0]).toExponential(a[1] === undefined ? 3 : num(a[1])));
  def("fmt", a => show(a[0]));
  def("pad", a => String(a[0]).padStart(num(a[1])));

  /* 数学 (実数・複素数) */
  def("abs", a => isC(a[0]) ? cabs(a[0]) : Math.abs(num(a[0])));
  def("sqrt", a => isC(a[0]) || num(a[0]) < 0 ? csqrt(toC(a[0])) : Math.sqrt(a[0]));
  def("exp", cplx(Math.exp, cexp));
  def("log", a => { const x = a[0]; if (isC(x) || num(x) < 0) return clog(toC(x)); if (a[1] !== undefined) return Math.log(x) / Math.log(num(a[1])); return Math.log(x); });
  def("sin", cplx(Math.sin, csin)); def("cos", cplx(Math.cos, ccos));
  def("tan", a => isC(a[0]) ? cdiv(csin(a[0]), ccos(a[0])) : Math.tan(num(a[0])));
  def("atan", a => Math.atan(num(a[0]))); def("atan2", a => Math.atan2(num(a[0]), num(a[1])));
  def("asin", a => Math.asin(num(a[0]))); def("acos", a => Math.acos(num(a[0])));
  def("sinh", a => Math.sinh(num(a[0]))); def("cosh", a => Math.cosh(num(a[0]))); def("tanh", a => Math.tanh(num(a[0])));
  def("acosh", a => Math.acosh(num(a[0])));
  def("pow", a => binop("^", a[0], a[1]));
  def("floor", a => Math.floor(num(a[0]))); def("ceil", a => Math.ceil(num(a[0])));
  def("round", a => { const d = a[1] === undefined ? 0 : num(a[1]); const m = Math.pow(10, d); return Math.round(num(a[0]) * m) / m; });
  def("cx", a => C(num(a[0]), a[1] === undefined ? 0 : num(a[1])));
  def("re", a => toC(a[0]).re); def("im", a => toC(a[0]).im);
  def("conj", a => { const z = toC(a[0]); return C(z.re, -z.im); });
  def("arg", a => { const z = toC(a[0]); return Math.atan2(z.im, z.re); });
  def("gamma", a => isC(a[0]) ? cexp(clgamma(a[0])) : gamma(num(a[0])));
  def("lgamma", a => isC(a[0]) ? clgamma(a[0]) : lgamma(num(a[0])));
  def("digamma", a => digamma(num(a[0])));
  def("beta", a => beta(num(a[0]), num(a[1])));
  def("zeta", a => zeta(a[0]));
  def("rs_theta", a => rsTheta(num(a[0])));
  def("rs_Z", a => rsZ(num(a[0])));
  def("lambertw", a => lambertw(num(a[0])));
  def("xlogx_root", () => Math.exp(lambertw(1)));
  def("jones", a => jones(String(a[0]), a[1]));
  def("jones_poly", a => jonesString(String(a[0])));
  def("integrate", a => {   // 合成シンプソン
    const f = a[0], lo = num(a[1]), hi = num(a[2]); let n = a[3] === undefined ? 2000 : num(a[3]); if (n % 2) n++;
    const h = (hi - lo) / n; let s = C(0, 0);
    for (let k = 0; k <= n; k++) {
      const w = k === 0 || k === n ? 1 : (k % 2 ? 4 : 2); const v = toC(fcall(f, lo + k * h));
      s = cadd(s, C(w * v.re, w * v.im));
    }
    const r = C(s.re * h / 3, s.im * h / 3); return Math.abs(r.im) < 1e-14 ? r.re : r;
  });
  def("deriv", a => { const h = a[2] === undefined ? 1e-5 : num(a[2]); const x = num(a[1]); const d = binop("-", fcall(a[0], x + h), fcall(a[0], x - h)); return binop("/", d, 2 * h); });
  def("solve", a => {   // 二分法 f(x)=0 on [lo,hi]
    const f = x => num(fcall(a[0], x)); let lo = num(a[1]), hi = num(a[2]); let flo = f(lo);
    if (flo * f(hi) > 0) return null;
    for (let k = 0; k < 200; k++) { const m = (lo + hi) / 2, fm = f(m); if (flo * fm <= 0) hi = m; else { lo = m; flo = fm; } }
    return (lo + hi) / 2;
  });
  def("seed", a => { I.rng = makeRng(num(a[0])); return null; });
  def("rand", () => I.rng());

  /* Unknown-Prior Engine */
  def("softmax", a => softmax(arr(a[0]).map(num)));
  def("entropy", a => entropy(arr(a[0]).map(num)));
  def("unknown_prior", a => { const V = num(a[0]); return new Array(V).fill(1 / V); });
  def("update", a => update(arr(a[0]).map(num), arr(a[1]).map(num), a[2] === undefined ? undefined : num(a[2])));
  def("dist", a => normalize(arr(a[0]).map(num)));
  def("phase", a => arr(a[0]).map(t => C(Math.cos(num(t)), Math.sin(num(t)))));
  def("zeros_of", a => { const z = []; arr(a[0]).forEach((v, i) => { if (v === 0) z.push(i); }); return z; });
  def("maxdiff", a => { let m = 0; arr(a[0]).forEach((v, i) => { m = Math.max(m, Math.abs(num(v) - num(arr(a[1])[i]))); }); return m; });
  def("manifold_embed", a => {
    const x = arr(a[0]).map(num); let d = x;
    if (a[1]) d = arr(a[1]).map(row => row.reduce((s, w, j) => s + num(w) * (x[j] || 0), 0));
    const n = Math.sqrt(d.reduce((s, v) => s + v * v, 0)) + 1e-12; return d.map(v => v / n);
  });
  def("cognitive_system", a => cognitiveSystem(arr(a[0]).map(num), arr(a[1]), a[2] ? arr(a[2]).map(num) : []));
  def("ledger", a => new Ledger(a[0] === undefined ? "tuplespace" : String(a[0])));
  def("commit", a => { const L = a[0] instanceof Ledger ? a[0] : I.Omega; return L.commit(a[0] instanceof Ledger ? a[1] : a[0]); });
  def("rules", () => Array.from(I.rules.keys()));

  /* Q# 型量子副言語 */
  def("Qubits", a => { const r = new QReg(num(a[0])); I.Omega.commit(["qubit", "anon", r.n]); return r; });
  for (const gname of Object.keys(GATES)) def(gname, a => { qcheck(a[0], a[1]); return q1(a[0], a[1], GATES[gname]); });
  def("RX", a => { qcheck(a[0], a[1]); return q1(a[0], a[1], rot("X", num(a[2]))); });
  def("RY", a => { qcheck(a[0], a[1]); return q1(a[0], a[1], rot("Y", num(a[2]))); });
  def("RZ", a => { qcheck(a[0], a[1]); return q1(a[0], a[1], rot("Z", num(a[2]))); });
  def("CNOT", a => { qcheck(a[0], a[1], a[2]); if (a[1] === a[2]) throw new BadaError("CNOT の制御と標的が同じです"); return cnot(a[0], a[1], a[2]); });
  def("CZ", a => { qcheck(a[0], a[1], a[2]); const r = a[0], cb = 1 << a[1], tb = 1 << a[2]; for (let s = 0; s < r.N; s++) if ((s & cb) && (s & tb)) { r.re[s] = -r.re[s]; r.im[s] = -r.im[s]; } return r; });
  def("SWAP", a => { qcheck(a[0], a[1], a[2]); cnot(a[0], a[1], a[2]); cnot(a[0], a[2], a[1]); return cnot(a[0], a[1], a[2]); });
  const measure = a => {
    const r = a[0], i = a[1]; qcheck(r, i); const bit = 1 << i; let p1 = 0;
    for (let s = 0; s < r.N; s++) if (s & bit) p1 += r.re[s] ** 2 + r.im[s] ** 2;
    const out = I.rng() < p1 ? 1 : 0; const norm = Math.sqrt(out ? p1 : 1 - p1) || 1;
    for (let s = 0; s < r.N; s++) {
      if (((s & bit) ? 1 : 0) !== out) { r.re[s] = 0; r.im[s] = 0; } else { r.re[s] /= norm; r.im[s] /= norm; }
    }
    I.Omega.commit(["measure", i, out, +p1.toFixed(12)]);   // 測定は台帳への commit
    return out;
  };
  def("Measure", measure); def("M", measure);
  def("probs", a => { qcheck(a[0]); return qprobs(a[0]); });
  def("amps", a => { qcheck(a[0]); const r = a[0], o = []; for (let s = 0; s < r.N; s++) o.push(C(r.re[s], r.im[s])); return o; });
  def("qstate", a => { qcheck(a[0]); return qstateString(a[0]); });
  def("basis", a => bits(num(a[0]), num(a[1])));
  def("reset", a => { qcheck(a[0]); a[0].re.fill(0); a[0].im.fill(0); a[0].re[0] = 1; return a[0]; });

  /* 知識ベースとホスト */
  const kb = () => (I.host.kb || { equations: [], chunks: [], sources: [], blueprint: "" });
  def("kb_equations", () => kb().equations);
  def("kb_chunks", () => kb().chunks);
  def("kb_sources", () => kb().sources);
  def("kb_blueprint", () => kb().blueprint);
  def("host_mode", () => (I.host.mode ? I.host.mode() : "local"));
  def("now", () => Date.now());
  def("eval_bada", a => {   // サンドボックスで Bada を実行 (チャットから送られたコード)
    const sub = new Interp({ host: { kb: I.host.kb }, maxSteps: 3e6, seed: 7 });
    const src = String(a[0]);
    try {
      let v;
      try { v = sub.evalExpr(src); }
      catch (e) { if (!(e instanceof BadaError)) throw e; sub.out = []; v = sub.run(src); }
      return { ok: true, value: v, shown: show(v, 1), out: sub.out.slice(), ledger: sub.Omega.items.length, rules: Array.from(sub.rules.keys()) };
    } catch (e) {
      if (e instanceof ReturnSig) return { ok: true, value: e.v, shown: show(e.v, 1), out: sub.out.slice(), ledger: sub.Omega.items.length, rules: [] };
      return { ok: false, error: e instanceof BadaError ? e.message : String(e && e.message || e), out: sub.out.slice() };
    }
  });
}

const BadaEngine = { lex, Parser, Interp, BadaError, Complex, Ledger, QReg, show, tokens, gamma, lgamma, beta, zeta, czeta, rsZ, rsTheta, lambertw, jones, softmax, entropy, cognitiveSystem };
if (typeof module !== "undefined" && module.exports) module.exports = BadaEngine;
