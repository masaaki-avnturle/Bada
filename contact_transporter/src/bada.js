/*
 * bada.js — 量子プログラミング言語 Bada の処理系 (JavaScript 移植)
 *
 * bada_silent_vim/bada (Python: lexer.py / parser.py / compiler.py / vm.py /
 * loader.py) と同じ文法・同じバイトコード・同じ意味論を持つ移植です。
 *   source → tokenize → parse → compile (bytecode) → BadaVM
 *
 *   <-   代入 (non-commutative left action)       <->  比較オブジェクト (==)
 *   -<   多様体積分 / spawn → 対 [a, b]            行頭では分岐オブジェクト (if)
 *   >-   量子右作用 / emit → 結合                   行頭では合流オブジェクト (else)
 *   ->   遷移オブジェクト (while)                  >>   ストリーム前送 / =>  写像
 *   Omega::DATABASE[space] { push(x) pop() }      アカシック TupleSpace
 *
 * アプリ用の拡張:
 *   - ホスト組込み関数 (vm.host) — 3D CAD・図面・Transformer・量子状態などの
 *     ランタイムライブラリを Bada から呼び出す (名前は cad_torus, ufo_param … の形)
 *   - vm.call(name, args) — ホスト (UI) から Bada の関数を呼ぶ (イベント駆動)
 *   - vm.eval(src)        — 同じ状態 (大域変数・関数・TupleSpace) で追加コードを実行 (REPL)
 *   - #include path       — 仮想ファイル表からのライブラリ読み込み
 * ブラウザ (window.Bada) / Node (module.exports) 両対応。
 */
(function (root) {
  "use strict";

  // ============================================================ lexer
  const KEYWORDS = new Set(["print", "say", "if", "else", "while", "repeat", "push", "pop", "true", "false", "nil", "def", "return", "Omega"]);
  const OPERATORS = ["<->", "::", "<-", "-<", "->", ">-", ">>", "=>", "==", "!=", "<=", ">=",
    "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", "[", "]", "{", "}", ",", ";"];

  class BadaError extends Error {
    constructor(kind, msg, line) { super(msg); this.kind = kind; this.line = line || null; }
  }
  const isDigit = (c) => c >= "0" && c <= "9";
  const isAlpha = (c) => /\p{L}/u.test(c) || c === "_";
  const isAlnum = (c) => isAlpha(c) || /\p{N}/u.test(c);

  function tokenize(src) {
    const toks = []; let i = 0, line = 1, col = 1; const n = src.length;
    const adv = (k) => { i += k; col += k; };
    while (i < n) {
      const c = src[i];
      if (c === "\n") { line++; col = 1; i++; continue; }
      if (c === " " || c === "\t" || c === "\r") { adv(1); continue; }
      if (c === "/" && src[i + 1] === "/") { while (i < n && src[i] !== "\n") i++; continue; }
      if (c === '"' || c === "'") {
        const q = c, sc = col; adv(1); let buf = "";
        while (i < n && src[i] !== q) {
          if (src[i] === "\\" && i + 1 < n) {
            const nx = src[i + 1]; buf += ({ n: "\n", t: "\t", "\\": "\\" })[nx] || (nx === q ? q : nx); adv(2);
          } else { if (src[i] === "\n") { line++; col = 1; } buf += src[i]; i++; col++; }
        }
        if (i >= n) throw new BadaError("LexError", `unterminated string at line ${line}`, line);
        adv(1); toks.push({ kind: "STRING", value: buf, line, col: sc }); continue;
      }
      if (isDigit(c) || (c === "." && isDigit(src[i + 1] || ""))) {
        const sc = col; let j = i, dot = false;
        while (j < n && (isDigit(src[j]) || (src[j] === "." && !dot))) { if (src[j] === ".") dot = true; j++; }
        const num = src.slice(i, j); adv(j - i); toks.push({ kind: "NUMBER", value: num, line, col: sc }); continue;
      }
      if (isAlpha(c)) {
        const sc = col; let j = i;
        while (j < n && isAlnum(src[j])) j++;
        const w = src.slice(i, j); adv(j - i);
        toks.push({ kind: KEYWORDS.has(w) ? "KW" : "IDENT", value: w, line, col: sc }); continue;
      }
      let m = null;
      for (const op of OPERATORS) if (src.startsWith(op, i)) { m = op; break; }
      if (m) { toks.push({ kind: "OP", value: m, line, col }); adv(m.length); continue; }
      throw new BadaError("LexError", `unexpected character ${JSON.stringify(c)} at line ${line} col ${col}`, line);
    }
    toks.push({ kind: "EOF", value: "", line, col });
    return toks;
  }

  // ============================================================ parser
  const PIPE_OPS = new Set([">>", "=>", ">-", "-<"]);
  const CMP_OPS = new Set(["==", "!=", "<", ">", "<=", ">=", "<->"]);

  class Parser {
    constructor(toks) { this.toks = toks; this.pos = 0; }
    get cur() { return this.toks[this.pos]; }
    at(k, v) { const t = this.cur; return t.kind === k && (v == null || t.value === v); }
    eat(k, v) {
      const t = this.cur;
      if (t.kind !== k || (v != null && t.value !== v))
        throw new BadaError("ParseError", `expected ${JSON.stringify(v != null ? v : k)} but found ${JSON.stringify(t.value)} at line ${t.line}`, t.line);
      this.pos++; return t;
    }
    accept(k, v) { return this.at(k, v) ? this.eat(k, v) : null; }
    parse() { const s = []; while (!this.at("EOF")) s.push(this.statement()); return s; }

    statement() {
      const t = this.cur;
      if (t.kind === "KW" && (t.value === "print" || t.value === "say")) {
        this.eat("KW"); const e = this.expr(); this.accept("OP", ";"); return ["print", t.value, e, t.line];
      }
      if (t.kind === "KW" && t.value === "def") return this.defStmt();
      if (t.kind === "KW" && t.value === "return") {
        this.eat("KW");
        const e = (this.at("OP", "}") || this.at("OP", ";") || this.at("EOF")) ? null : this.expr();
        this.accept("OP", ";"); return ["return", e, t.line];
      }
      if (t.kind === "KW" && t.value === "Omega") return this.tuplespace();
      if (t.kind === "KW" && t.value === "if") return this.ifStmt();
      if (t.kind === "KW" && t.value === "while") { this.eat("KW"); const c = this.expr(); return ["while", c, this.block(), t.line]; }
      if (t.kind === "KW" && t.value === "repeat") { this.eat("KW"); const c = this.expr(); return ["repeat", c, this.block(), t.line]; }
      if (t.kind === "OP" && t.value === "-<") return this.branchStmt();
      if (t.kind === "OP" && t.value === "->") { this.eat("OP", "->"); const c = this.expr(); return ["while", c, this.block(), t.line]; }
      if (t.kind === "IDENT") {
        const save = this.pos;
        const target = this.lvalue();
        if (this.cur.kind === "OP" && (this.cur.value === "<-" || this.cur.value === "=")) {
          this.eat("OP"); const rhs = this.expr(); this.accept("OP", ";");
          if (target[0] === "var") return ["assign", target[1], rhs, t.line];
          return ["setindex", target[1], target[2], rhs, t.line];
        }
        this.pos = save;
      }
      const e = this.expr(); this.accept("OP", ";"); return ["exprstmt", e, t.line];
    }
    defStmt() {
      const t = this.eat("KW", "def"); const name = this.eat("IDENT").value; this.eat("OP", "(");
      const params = [];
      if (!this.at("OP", ")")) { params.push(this.eat("IDENT").value); while (this.accept("OP", ",")) params.push(this.eat("IDENT").value); }
      this.eat("OP", ")");
      return ["def", name, params, this.block(), t.line];
    }
    lvalue() {
      let node = ["var", this.eat("IDENT").value];
      while (this.at("OP", "[")) { this.eat("OP", "["); const idx = this.expr(); this.eat("OP", "]"); node = ["index", node, idx]; }
      return node;
    }
    tuplespace() {
      const t = this.eat("KW", "Omega"); this.eat("OP", "::"); this.eat("IDENT", "DATABASE"); this.eat("OP", "[");
      const name = this.eat("IDENT").value; this.eat("OP", "]"); this.eat("OP", "{");
      const ops = [];
      while (!this.at("OP", "}")) {
        if (this.at("KW", "push")) { this.eat("KW"); this.eat("OP", "("); const e = this.expr(); this.eat("OP", ")"); this.accept("OP", ";"); ops.push(["push", e]); }
        else if (this.at("KW", "pop")) { this.eat("KW"); this.eat("OP", "("); this.eat("OP", ")"); this.accept("OP", ";"); ops.push(["pop"]); }
        else throw new BadaError("ParseError", `only push/pop allowed in tuplespace, found ${JSON.stringify(this.cur.value)} at line ${this.cur.line}`, this.cur.line);
      }
      this.eat("OP", "}");
      return ["tuplespace", name, ops, t.line];
    }
    ifStmt() {
      const t = this.eat("KW", "if"); const c = this.expr(); const th = this.block();
      const el = this.accept("KW", "else") ? this.block() : null;
      return ["if", c, th, el, t.line];
    }
    branchStmt() {
      const t = this.eat("OP", "-<"); const c = this.expr(); const th = this.block(); let el = null;
      if (this.at("OP", ">-")) { this.eat("OP", ">-"); el = this.block(); }
      return ["if", c, th, el, t.line];
    }
    block() { this.eat("OP", "{"); const s = []; while (!this.at("OP", "}")) s.push(this.statement()); this.eat("OP", "}"); return s; }
    expr() { return this.pipe(); }
    pipe() {
      let node = this.compare();
      while (this.cur.kind === "OP" && PIPE_OPS.has(this.cur.value)) {
        if (this.cur.line !== this.toks[this.pos - 1].line) break;
        const op = this.eat("OP").value; node = ["bin", op, node, this.compare()];
      }
      return node;
    }
    compare() {
      let node = this.add();
      while (this.cur.kind === "OP" && CMP_OPS.has(this.cur.value)) {
        let op = this.eat("OP").value; if (op === "<->") op = "=="; node = ["bin", op, node, this.add()];
      }
      return node;
    }
    add() { let n = this.mul(); while (this.cur.kind === "OP" && (this.cur.value === "+" || this.cur.value === "-")) { const op = this.eat("OP").value; n = ["bin", op, n, this.mul()]; } return n; }
    mul() { let n = this.unary(); while (this.cur.kind === "OP" && "*/%".includes(this.cur.value) && this.cur.value.length === 1) { const op = this.eat("OP").value; n = ["bin", op, n, this.unary()]; } return n; }
    unary() { if (this.at("OP", "-")) { this.eat("OP"); return ["neg", this.unary()]; } return this.postfix(); }
    postfix() { let n = this.atom(); while (this.at("OP", "[")) { this.eat("OP", "["); const i = this.expr(); this.eat("OP", "]"); n = ["index", n, i]; } return n; }
    atom() {
      const t = this.cur;
      if (t.kind === "NUMBER") { this.eat("NUMBER"); return ["num", t.value.includes(".") ? new PyFloat(parseFloat(t.value)) : parseInt(t.value, 10)]; }
      if (t.kind === "STRING") { this.eat("STRING"); return ["str", t.value]; }
      if (t.kind === "KW" && (t.value === "true" || t.value === "false")) { this.eat("KW"); return ["bool", t.value === "true"]; }
      if (t.kind === "KW" && t.value === "nil") { this.eat("KW"); return ["nil"]; }
      if (t.kind === "IDENT") {
        const name = this.eat("IDENT").value;
        if (this.at("OP", "(")) {
          this.eat("OP", "("); const args = [];
          if (!this.at("OP", ")")) { args.push(this.expr()); while (this.accept("OP", ",")) args.push(this.expr()); }
          this.eat("OP", ")"); return ["call", name, args, t.line];
        }
        return ["var", name];
      }
      if (this.at("OP", "[")) {
        this.eat("OP", "["); const el = [];
        if (!this.at("OP", "]")) { el.push(this.expr()); while (this.accept("OP", ",")) el.push(this.expr()); }
        this.eat("OP", "]"); return ["array", el];
      }
      if (this.at("OP", "(")) { this.eat("OP", "("); const e = this.expr(); this.eat("OP", ")"); return e; }
      throw new BadaError("ParseError", `unexpected token ${JSON.stringify(t.value)} (${t.kind}) at line ${t.line}`, t.line);
    }
  }
  const parse = (src) => new Parser(tokenize(src)).parse();

  // 小数リテラル (Python の float) — 表示を Python に合わせるための印
  class PyFloat { constructor(v) { this.v = v; } }

  // ============================================================ compiler
  const BUILTINS = new Set(["len", "append", "idiv", "imod", "abs", "str", "pow2"]);

  class Compiler {
    constructor(opts) {
      this.code = []; this.rep = 0; this.funcNames = new Set(); this.opts = opts || {};
      this.hostNames = this.opts.host || new Set(); this.known = this.opts.knownFuncs || new Set();
      this.repBase = this.opts.repBase || 0; this.line = 0;
    }
    emit(...ins) { ins.line = this.line; this.code.push(ins); return this.code.length - 1; }
    patch(i, target) { this.code[i][1] = target; }
    compileProgram(stmts) {
      const defs = stmts.filter((s) => s[0] === "def"), body = stmts.filter((s) => s[0] !== "def");
      this.funcNames = new Set(defs.map((d) => d[1]));
      for (const s of body) this.stmt(s);
      this.emit("HALT");
      for (const [, name, params, fbody, line] of defs) {
        this.line = line; this.emit("FUNC", name, params);
        for (const s of fbody) this.stmt(s);
        this.emit("CONST", null); this.emit("RET");
      }
      return this.code;
    }
    stmt(node) {
      const tag = node[0]; if (typeof node[node.length - 1] === "number" && tag !== "exprstmt") this.line = node[node.length - 1];
      if (tag === "exprstmt") this.line = node[2];
      switch (tag) {
        case "assign": this.expr(node[2]); this.emit("STORE", node[1]); break;
        case "print": this.expr(node[2]); this.emit(node[1] === "say" ? "SAY" : "PRINT"); break;
        case "exprstmt": this.expr(node[1]); this.emit("POP"); break;
        case "tuplespace":
          for (const op of node[2]) {
            if (op[0] === "push") { this.expr(op[1]); this.emit("TPUSH", node[1]); }
            else { this.emit("TPOP", node[1]); this.emit("POP"); }
          }
          break;
        case "if": {
          this.expr(node[1]); const jf = this.emit("JFALSE", -1);
          for (const s of node[2]) this.stmt(s);
          if (node[3] !== null) {
            const je = this.emit("JMP", -1); this.patch(jf, this.code.length);
            for (const s of node[3]) this.stmt(s);
            this.patch(je, this.code.length);
          } else this.patch(jf, this.code.length);
          break;
        }
        case "while": {
          const start = this.code.length; this.expr(node[1]); const jf = this.emit("JFALSE", -1);
          for (const s of node[2]) this.stmt(s);
          this.emit("JMP", start); this.patch(jf, this.code.length); break;
        }
        case "repeat": {
          const v = `__rep${this.repBase + this.rep++}`;
          this.expr(node[1]); this.emit("STORE", v);
          const start = this.code.length;
          this.emit("LOAD", v); this.emit("CONST", 0); this.emit("BIN", ">"); const jf = this.emit("JFALSE", -1);
          for (const s of node[2]) this.stmt(s);
          this.emit("LOAD", v); this.emit("CONST", 1); this.emit("BIN", "-"); this.emit("STORE", v); this.emit("JMP", start);
          this.patch(jf, this.code.length); break;
        }
        case "return": if (node[1] === null) this.emit("CONST", null); else this.expr(node[1]); this.emit("RET"); break;
        case "setindex": this.expr(node[1]); this.expr(node[2]); this.expr(node[3]); this.emit("SETINDEX"); break;
        default: throw new BadaError("CompileError", `unknown statement ${JSON.stringify(tag)}`, this.line);
      }
    }
    expr(node) {
      switch (node[0]) {
        case "num": case "str": case "bool": this.emit("CONST", node[1]); break;
        case "nil": this.emit("CONST", null); break;
        case "var": this.emit("LOAD", node[1]); break;
        case "neg": this.expr(node[1]); this.emit("NEG"); break;
        case "bin": this.expr(node[2]); this.expr(node[3]); this.emit("BIN", node[1]); break;
        case "array": for (const e of node[1]) this.expr(e); this.emit("ARRAY", node[1].length); break;
        case "index": this.expr(node[1]); this.expr(node[2]); this.emit("INDEX"); break;
        case "call": {
          const [, name, args, line] = node; if (line) this.line = line;
          for (const a of args) this.expr(a);
          if (BUILTINS.has(name) || this.hostNames.has(name)) this.emit("CALLB", name, args.length);
          else if (this.funcNames.has(name) || this.known.has(name)) this.emit("CALL", name, args.length);
          else throw new BadaError("CompileError", `call to unknown function ${JSON.stringify(name)} at line ${this.line}`, this.line);
          break;
        }
        default: throw new BadaError("CompileError", `unknown expression ${JSON.stringify(node[0])}`, this.line);
      }
    }
  }
  // 小数リテラルは VM に渡す前に JS の数へ (表示用の印は FLOAT 集合で保持)
  function lowerFloats(code) {
    for (const ins of code) if (ins[0] === "CONST" && ins[1] instanceof PyFloat) { const v = ins[1].v; ins[1] = v; ins.isFloat = true; }
    return code;
  }
  function compileSource(src, opts) { return lowerFloats(new Compiler(opts).compileProgram(parse(src))); }
  function disassemble(code) {
    return code.map((ins, i) => `${String(i).padStart(4)}  ${String(ins[0]).padEnd(8)} ${ins.slice(1).map((a) => JSON.stringify(a)).join(" ")}`).join("\n");
  }

  // ============================================================ values
  // Python の値の振る舞いを JS 上で再現する (int/float は number、list は Array、None は null)
  function truthy(v) {
    if (v === null || v === undefined || v === false) return false;
    if (v === 0 || v === "" || (Array.isArray(v) && v.length === 0)) return false;
    return true;
  }
  function numText(v) {
    if (Number.isInteger(v)) return String(v);
    if (!isFinite(v)) return isNaN(v) ? "nan" : (v > 0 ? "inf" : "-inf");
    let s = String(v);
    // Python repr: 1e-07 / 1e+16 形式
    const m = /^(-?[\d.]+)e([+-])(\d+)$/.exec(s);
    if (m) s = `${m[1]}e${m[2]}${m[3].padStart(2, "0")}`;
    return s;
  }
  function toText(v) {
    if (v === true) return "true";
    if (v === false) return "false";
    if (v === null || v === undefined) return "nil";
    if (typeof v === "number") return numText(v);
    if (typeof v === "bigint") return v.toString();
    if (Array.isArray(v)) return "[" + v.map(toText).join(", ") + "]";
    return String(v);
  }
  // Python の repr (リスト内の文字列表示用ではなく、Bada の to_text と同じ)
  function pyEq(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) { if (a.length !== b.length) return false; for (let i = 0; i < a.length; i++) if (!pyEq(a[i], b[i])) return false; return true; }
    const na = typeof a === "boolean" ? +a : a, nb = typeof b === "boolean" ? +b : b;
    const nn = (x) => typeof x === "number" || typeof x === "bigint";
    if (nn(na) && nn(nb)) return na == nb; // eslint-disable-line eqeqeq
    return a === b || ((a === null || a === undefined) && (b === null || b === undefined));
  }
  function pyCmp(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) {
      for (let i = 0; i < Math.min(a.length, b.length); i++) { if (pyEq(a[i], b[i])) continue; return pyCmp(a[i], b[i]); }
      return a.length - b.length;
    }
    const ta = typeof a, tb = typeof b;
    const isn = (x) => typeof x === "number" || typeof x === "boolean" || typeof x === "bigint";
    if (isn(a) && isn(b)) { const A = typeof a === "boolean" ? +a : a, B = typeof b === "boolean" ? +b : b; return A < B ? -1 : A > B ? 1 : 0; }
    if (ta === "string" && tb === "string") return a < b ? -1 : a > b ? 1 : 0;
    throw new BadaError("RuntimeError", `'<' not supported between ${typeName(a)} and ${typeName(b)}`);
  }
  function typeName(v) { return v === null || v === undefined ? "nil" : Array.isArray(v) ? "list" : typeof v === "boolean" ? "bool" : typeof v === "number" || typeof v === "bigint" ? "number" : typeof v; }
  const pyMod = (a, b) => { if (b === 0) throw new BadaError("RuntimeError", "modulo by zero"); const r = a % b; return r !== 0 && (r < 0) !== (b < 0) ? r + b : r; };
  const isStr = (v) => typeof v === "string";
  const isNum = (v) => typeof v === "number" || typeof v === "boolean" || typeof v === "bigint";
  // Python の任意精度整数: 2^53 を超える整数演算は BigInt に自動昇格し、戻れる範囲なら number に戻す
  const MAXS = BigInt(Number.MAX_SAFE_INTEGER);
  const norm = (x) => (typeof x === "bigint" && x <= MAXS && x >= -MAXS ? Number(x) : x);
  const isIntLike = (v) => typeof v === "bigint" || (typeof v === "number" && Number.isInteger(v)) || typeof v === "boolean";
  const big = (v) => (typeof v === "bigint" ? v : BigInt(+v));
  const num = (v) => (typeof v === "bigint" ? Number(v) : +v);
  function intArith(op, a, b) {
    if (isIntLike(a) && isIntLike(b)) {
      if (typeof a !== "bigint" && typeof b !== "bigint") {
        const r = op === "+" ? (+a) + (+b) : op === "-" ? a - b : a * b;
        if (Number.isSafeInteger(r)) return r;
      }
      const A = big(a), B = big(b);
      return norm(op === "+" ? A + B : op === "-" ? A - B : A * B);
    }
    const A = num(a), B = num(b);
    return op === "+" ? A + B : op === "-" ? A - B : A * B;
  }
  function floorDiv(a, b) {
    if (typeof a === "bigint" || typeof b === "bigint") {
      const A = big(a), B = big(b); if (B === 0n) throw new BadaError("RuntimeError", "division by zero");
      let q = A / B; if ((A % B !== 0n) && ((A < 0n) !== (B < 0n))) q -= 1n; return norm(q);
    }
    if (+b === 0) throw new BadaError("RuntimeError", "division by zero");
    return Math.floor(a / b);
  }
  function modAny(a, b) {
    if (typeof a === "bigint" || typeof b === "bigint") {
      const A = big(a), B = big(b); if (B === 0n) throw new BadaError("RuntimeError", "modulo by zero");
      let r = A % B; if (r !== 0n && ((r < 0n) !== (B < 0n))) r += B; return norm(r);
    }
    return pyMod(+a, +b);
  }

  // ============================================================ VM
  class BadaVM {
    constructor(opts) {
      opts = opts || {};
      this.stack = []; this.vars = {}; this.frames = [this.vars]; this.retStack = [];
      this.tuplespace = {}; this.stream = []; this.output = [];
      this.funcTable = {}; this.host = Object.assign({}, opts.host || {});
      this.onPrint = opts.onPrint || null; this.onTuple = opts.onTuple || null;
      this.maxSteps = opts.maxSteps || 2e8; this.steps = 0; this.files = opts.files || {};
      this.units = 0; this.depth = 0;
    }
    hostNames() { return new Set(Object.keys(this.host)); }
    register(code) {
      for (let i = 0; i < code.length; i++) if (code[i][0] === "FUNC") this.funcTable[code[i][1]] = { code, entry: i + 1, params: code[i][2] };
    }
    // ソースを読み込んで実行 (#include 展開 → コンパイル → 関数登録 → 本体実行)
    load(src, name) {
      const full = this.expand(src, name || "main.bada");
      const code = compileSource(full, { host: this.hostNames(), knownFuncs: new Set(Object.keys(this.funcTable)), repBase: this.units * 1000 });
      this.units++;
      this.register(code); this.lastCode = code;
      this._run(() => this._exec(code, 0));
      return this;
    }
    eval(src) { return this.load(src, "<repl>"); }
    expand(src, name, seen) {
      seen = seen || new Set(); seen.add(name);
      return src.split("\n").map((ln) => {
        const s = ln.trim();
        if (!s.startsWith("#include")) return ln;
        const inc = s.slice(8).trim().replace(/^["<]|[">]$/g, "");
        if (seen.has(inc)) return "";
        if (!(inc in this.files)) throw new BadaError("IncludeError", `#include: ${inc} が見つかりません`);
        return this.expand(this.files[inc], inc, seen);
      }).join("\n");
    }
    // ホストから Bada 関数を呼ぶ
    call(name, args) {
      const f = this.funcTable[name];
      if (!f) throw new BadaError("RuntimeError", `undefined function ${JSON.stringify(name)}`);
      const frame = {}; f.params.forEach((p, i) => { frame[p] = args && i < args.length ? args[i] : undefined; });
      for (const p of f.params) if (frame[p] === undefined) delete frame[p];
      const f0 = this.frames.length, r0 = this.retStack.length;
      this.frames.push(frame); this.retStack.push(null);
      try { return this._run(() => this._exec(f.code, f.entry)); }
      catch (e) { this.frames.length = f0; this.retStack.length = r0; throw e; }
    }
    // 最外周の実行ではステップ数を数え直す (ネストした実行はそのまま)
    _run(fn) {
      if (this.depth === 0) this.steps = 0;
      this.depth++;
      try { return fn(); } finally { this.depth--; }
    }
    has(name) { return !!this.funcTable[name]; }
    get(name) { return this.vars[name]; }
    set(name, v) { this.vars[name] = v; }
    _load(name) {
      const fr = this.frames[this.frames.length - 1];
      if (name in fr) return fr[name];
      if (this.frames.length > 1 && name in this.vars) return this.vars[name];
      throw new BadaError("RuntimeError", `undefined variable ${JSON.stringify(name)}`);
    }
    _exec(code, ip) {
      const st = this.stack, baseRet = this.retStack.length;
      const f0 = this.frames.length, r0 = this.retStack.length, s0 = st.length;
      for (;;) {
        if (ip >= code.length) return null;
        const ins = code[ip], op = ins[0];
        if (++this.steps > this.maxSteps) { this.steps = 0; throw this._err(new BadaError("RuntimeError", "実行ステップ上限に達しました (無限ループ?)"), ins, f0, r0, s0); }
        try {
          switch (op) {
            case "CONST": st.push(ins[1]); break;
            case "LOAD": st.push(this._load(ins[1])); break;
            case "STORE": this.frames[this.frames.length - 1][ins[1]] = st.pop(); break;
            case "POP": st.pop(); break;
            case "NEG": { const v = st.pop(); if (!isNum(v)) throw new BadaError("RuntimeError", `bad operand type for unary -: ${typeName(v)}`); st.push(typeof v === "boolean" ? -(+v) : -v); break; }
            case "ARRAY": { const c = ins[1]; st.push(st.splice(st.length - c, c)); break; }
            case "INDEX": { const idx = st.pop(), base = st.pop(); st.push(this._index(base, idx)); break; }
            case "SETINDEX": {
              const val = st.pop(), idx = st.pop(), base = st.pop();
              if (!Array.isArray(base)) throw new BadaError("RuntimeError", `index error: '${typeName(base)}' object does not support item assignment`);
              let i = Math.trunc(+idx); if (i < 0) i += base.length;
              if (i < 0 || i >= base.length) throw new BadaError("RuntimeError", "index error: list assignment index out of range");
              base[i] = val; break;
            }
            case "PRINT": case "SAY": {
              const line = toText(st.pop()); this.output.push(line);
              if (this.onPrint) this.onPrint(line, op === "SAY" ? "say" : "print"); break;
            }
            case "BIN": { const b = st.pop(), a = st.pop(); st.push(this._binary(ins[1], a, b)); break; }
            case "TPUSH": { const v = st.pop(); (this.tuplespace[ins[1]] || (this.tuplespace[ins[1]] = [])).push(v); if (this.onTuple) this.onTuple(ins[1], "push", v); break; }
            case "TPOP": { const l = this.tuplespace[ins[1]]; const v = l && l.length ? l.pop() : null; st.push(v); if (this.onTuple) this.onTuple(ins[1], "pop", v); break; }
            case "CALL": {
              const f = this.funcTable[ins[1]];
              if (!f) throw new BadaError("RuntimeError", `undefined function ${JSON.stringify(ins[1])}`);
              const args = st.splice(st.length - ins[2], ins[2]), frame = {};
              f.params.forEach((p, i) => { if (i < args.length) frame[p] = args[i]; });
              if (this.frames.length > 4000) throw new BadaError("RuntimeError", "再帰が深すぎます");
              this.frames.push(frame); this.retStack.push({ code, ip: ip + 1 });
              code = f.code; ip = f.entry; continue;
            }
            case "CALLB": this._builtin(ins[1], ins[2]); break;
            case "RET": {
              const rv = st.pop(); this.frames.pop(); st.push(rv);
              const r = this.retStack.pop();
              if (r === null || this.retStack.length < baseRet) { st.pop(); return rv; }
              code = r.code; ip = r.ip; continue;
            }
            case "FUNC": break;
            case "JMP": ip = ins[1]; continue;
            case "JFALSE": if (!truthy(st.pop())) { ip = ins[1]; continue; } break;
            case "HALT": return null;
            default: throw new BadaError("RuntimeError", `bad opcode ${op}`);
          }
        } catch (e) { throw this._err(e, ins, f0, r0, s0); }
        ip++;
      }
    }
    _err(e, ins, f0, r0, s0) {
      if (!(e instanceof BadaError)) e = new BadaError("RuntimeError", e && e.message ? e.message : String(e));
      if (e.line == null && ins && ins.line) { e.line = ins.line; e.message += ` (line ${ins.line})`; }
      // この実行の開始時点まで状態を巻き戻す (REPL やネスト実行で続行できるように)
      this.frames.length = f0; this.retStack.length = r0; this.stack.length = s0;
      return e;
    }
    _index(base, idx) {
      if (Array.isArray(base) || isStr(base)) {
        const s = isStr(base) ? Array.from(base) : base;
        let i = Math.trunc(+idx); if (i < 0) i += s.length;
        if (i < 0 || i >= s.length || !isNum(idx)) throw new BadaError("RuntimeError", `index error: ${isStr(base) ? "string" : "list"} index out of range`);
        return s[i];
      }
      throw new BadaError("RuntimeError", `index error: '${typeName(base)}' object is not subscriptable`);
    }
    _builtin(name, argc) {
      const st = this.stack, args = st.splice(st.length - argc, argc);
      switch (name) {
        case "len": if (!Array.isArray(args[0]) && !isStr(args[0])) throw new BadaError("RuntimeError", `object of type '${typeName(args[0])}' has no len()`); st.push(isStr(args[0]) ? Array.from(args[0]).length : args[0].length); return;
        case "append": args[0].push(args[1]); st.push(args[0]); return;
        case "idiv": st.push(floorDiv(tint(args[0]), tint(args[1]))); return;
        case "imod": st.push(modAny(tint(args[0]), tint(args[1]))); return;
        case "abs": st.push(typeof args[0] === "bigint" ? (args[0] < 0n ? -args[0] : args[0]) : Math.abs(args[0])); return;
        case "pow2": st.push(2 ** Math.trunc(args[0])); return;
        case "str": st.push(toText(args[0])); return;
      }
      const h = this.host[name];
      if (!h) throw new BadaError("RuntimeError", `unknown builtin ${JSON.stringify(name)}`);
      const r = h.apply(this, args);
      st.push(r === undefined ? null : r);
    }
    _binary(op, a, b) {
      switch (op) {
        case "+":
          if (isStr(a) || isStr(b)) return toText(a) + toText(b);
          if (Array.isArray(a) && Array.isArray(b)) return a.concat(b);
          if (isNum(a) && isNum(b)) return intArith("+", a, b);
          throw new BadaError("RuntimeError", `unsupported operand type(s) for +: ${typeName(a)} and ${typeName(b)}`);
        case "-": this._nums(op, a, b); return intArith("-", a, b);
        case "*":
          if (isStr(a) && isNum(b)) return b > 0 ? a.repeat(Math.trunc(b)) : "";
          if (Array.isArray(a) && isNum(b)) { let r = []; for (let k = 0; k < b; k++) r = r.concat(a); return r; }
          this._nums(op, a, b); return intArith("*", a, b);
        case "/": this._nums(op, a, b); if (num(b) === 0) throw new BadaError("RuntimeError", "division by zero"); return num(a) / num(b);
        case "%": this._nums(op, a, b); return modAny(a, b);
        case "==": return pyEq(a, b);
        case "!=": return !pyEq(a, b);
        case "<": return pyCmp(a, b) < 0;
        case ">": return pyCmp(a, b) > 0;
        case "<=": return pyCmp(a, b) <= 0;
        case ">=": return pyCmp(a, b) >= 0;
        case "-<": return [a, b];
        case ">-":
          if (Array.isArray(a) || Array.isArray(b)) return (Array.isArray(a) ? a : [a]).concat(Array.isArray(b) ? b : [b]);
          if (isStr(a) || isStr(b)) return toText(a) + toText(b);
          this._nums(op, a, b); return intArith("+", a, b);
        case ">>": this.stream.push(a); return Array.isArray(b) ? b.concat([a]) : b;
        case "=>": return Array.isArray(a) ? a.map((x) => combine(x, b)) : combine(a, b);
      }
      throw new BadaError("RuntimeError", `unknown operator ${op}`);
    }
    _nums(op, a, b) { if (!isNum(a) || !isNum(b)) throw new BadaError("RuntimeError", `unsupported operand type(s) for ${op}: ${typeName(a)} and ${typeName(b)}`); }
  }
  // int() 相当 (0 方向への切り捨て)
  function tint(v) { return typeof v === "bigint" ? v : Math.trunc(+v); }
  function combine(x, y) {
    if (isStr(x) || isStr(y)) return toText(x) + toText(y);
    return Array.isArray(x) ? x.concat([y]) : intArith("*", x, y);
  }

  function run(src, opts) { const vm = new BadaVM(opts); vm.load(src); return vm; }

  // 文法チェック (lint) — [{line, message}]
  function lint(src, hostNames) {
    try { compileSource(src, { host: hostNames || new Set(), knownFuncs: new Set() }); return []; }
    catch (e) { return [{ line: e.line || 1, kind: e.kind || "Error", message: e.message }]; }
  }

  const DIRECTIVES = { "<-": "代入オブジェクト", "<->": "比較オブジェクト (==)", "-<": "分岐オブジェクト / 多様体 spawn", "->": "遷移オブジェクト (while)",
    ">-": "合流オブジェクト (else) / 量子 emit", "=>": "写像", ">>": "ストリーム前送", "::": "名前空間 (Omega::DATABASE)" };

  const api = { tokenize, parse, compileSource, disassemble, BadaVM, BadaError, run, lint, toText, truthy, KEYWORDS, BUILTINS, DIRECTIVES };
  root.Bada = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
