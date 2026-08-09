/* ============================================================================
 * bada.js — the Bada language: lexer → parser → AST, a tree-walking INTERPRETER
 * and a bytecode COMPILER + stack VM, plus a quantum backend (state-vector
 * simulator + OpenQASM emitter). Pure, dependency-free; runs in the browser and
 * in node (UMD global `Bada`).
 *
 * 集大成 (culmination) of the Yamaguchi / TupleSpace framework:
 *   <-   left non-commutative act    π(χ,x) = [iπ, f(x)]   → π·|χ|·ln(x+1)
 *   -<   manifold integral           ∬ 1/(x log x)^2 dx_m
 *   >-   quantum right act            ⊕(iℏ∇)^⊕L = e^{-x log x}
 *   Ω::push … as …                    write to the Akashic TupleSpace
 * plus real control flow (if/while/fn/return), math + entropy builtins, and a
 * quantum standard library (qreg/H/X/Z/RY/CNOT/measure/probs) that the compiler
 * can lower to an OpenQASM 2.0 circuit — the "quantum-computer Bada language".
 * ========================================================================== */
(function (global) {
  "use strict";
  var Bada = { VERSION: "4.0.0" };

  /* ------------------------------------------------------------------ math */
  var LZ = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  function gamma(x) {
    if (x < 0.5) return Math.PI / (Math.sin(Math.PI * x) * gamma(1 - x));
    x -= 1; var a = LZ[0], t = x + 7.5;
    for (var i = 1; i < 9; i++) a += LZ[i] / (x + i);
    return Math.sqrt(2 * Math.PI) * Math.pow(t, x + 0.5) * Math.exp(-t) * a;
  }
  function logGamma(x) { return Math.log(Math.abs(gamma(x))); }
  function beta(p, q) { return Math.exp(logGamma(p) + logGamma(q) - logGamma(p + q)); }
  function xLogX(x) { return x <= 0 ? 0 : x * Math.log(x); }
  var TOKEN_RE = /[A-Za-z0-9_]+|[一-鿿぀-ゟ゠-ヿ]/g;
  function tokenizeText(s) { return String(s).match(TOKEN_RE) || []; }
  function shannon(toks) {
    var f = {}, n = toks.length; if (!n) return 0;
    toks.forEach(function (t) { f[t] = (f[t] || 0) + 1; });
    var H = 0; for (var k in f) { var p = f[k] / n; H -= p * Math.log2(p); } return H;
  }
  function mElement(x) { if (x <= 1) return 1; var xl = xLogX(x); return Math.abs(xl) < 1e-9 ? 1 : 1 / (xl * xl); }
  function mIntegral(dist) { return dist.reduce(function (s, p, i) { return s + p * mElement(i + 2); }, 0); }
  function distribution(toks) {
    var f = {}; toks.forEach(function (t) { f[t] = (f[t] || 0) + 1; });
    var n = toks.length; return Object.keys(f).map(function (k) { return f[k] / n; }).sort(function (a, b) { return b - a; });
  }
  function xiOf(str) {
    var toks = tokenizeText(str), H = shannon(toks), M = mIntegral(distribution(toks)), N = toks.length;
    var lx = Math.log(N + 1); return lx < 1e-15 ? 0 : beta(H + 1, M + 1) / lx;
  }

  /* --------------------------------------------------------------- values */
  function isQReg(v) { return v && v.__qreg === true; }
  function isArr(v) { return Array.isArray(v); }
  function isObj(v) { return v && v.__obj === true; }
  function makeObj() { return { __obj: true, m: Object.create(null), keys: [] }; }
  function objSet(o, k, v) { k = String(k); if (!(k in o.m)) o.keys.push(k); o.m[k] = v; return v; }
  function objGet(o, k) { k = String(k); return k in o.m ? o.m[k] : null; }
  // index / member get+set, shared by the interpreter and the VM.
  function rtIndexGet(o, i) {
    if (isArr(o)) { var idx = Math.trunc(num(i)); if (idx < 0) idx += o.length; return (idx >= 0 && idx < o.length) ? o[idx] : null; }
    if (isObj(o)) return objGet(o, i);
    if (typeof o === "string") { var s = Math.trunc(num(i)); if (s < 0) s += o.length; return o[s] !== undefined ? o[s] : null; }
    return null;
  }
  function rtIndexSet(o, i, v) {
    if (isArr(o)) { var idx = Math.trunc(num(i)); if (idx < 0) idx += o.length; if (idx < 0) idx = 0; o[idx] = v; return v; }
    if (isObj(o)) return objSet(o, i, v);
    throw new BadaError("cannot index-assign into " + (o === null ? "null" : typeof o));
  }
  function rtMemberGet(o, k) {
    if (isObj(o)) return objGet(o, k);
    if ((isArr(o) || typeof o === "string") && k === "length") return o.length;
    return null;
  }
  function rtMemberSet(o, k, v) { if (isObj(o)) return objSet(o, k, v); throw new BadaError("cannot set ." + k + " on " + (o === null ? "null" : typeof o)); }
  function num(v) { // coerce any Bada value to a number (the Ω-lattice projection)
    if (typeof v === "number") return v;
    if (typeof v === "boolean") return v ? 1 : 0;
    if (typeof v === "string") return xiOf(v);
    if (v == null) return 0;
    if (isArr(v)) return v.length;
    if (isObj(v)) return v.keys.length;
    if (isQReg(v)) return v.n;
    return 0;
  }
  function truthy(v) {
    if (typeof v === "boolean") return v;
    if (typeof v === "number") return v !== 0;
    if (typeof v === "string") return v.length > 0;
    if (isArr(v)) return v.length > 0;
    if (isObj(v)) return v.keys.length > 0;
    return v != null;
  }
  function show(v) {
    if (v == null) return "null";
    if (typeof v === "number") return (Number.isInteger(v) ? String(v) : String(v));
    if (typeof v === "boolean") return v ? "true" : "false";
    if (isArr(v)) return "[" + v.map(show).join(", ") + "]";
    if (isObj(v)) return "{" + v.keys.map(function (k) { return k + ": " + show(v.m[k]); }).join(", ") + "}";
    if (isQReg(v)) return "<qreg " + v.n + " qubits>";
    if (typeof v === "object" && v.__fn) return "<fn " + (v.name || "anon") + ">";
    return String(v);
  }

  /* ---- the three Bada manifold operators (shared by interpreter and VM) -- */
  function badaLeft(L, R) {           // <-  : π·|χ|·ln(x+1)
    var x = (Math.abs(L) < 1e-9 ? 1 : Math.abs(L)) + 1;
    return Math.PI * Math.abs(num(R)) * Math.log(x);
  }
  function badaIntegral(L, R) {       // -<  : x_log_x(x)·μ(x) + μ(x)
    var s = R == null ? L : num(R), x = Math.abs(s) + 2;
    return xLogX(x) * mElement(x) + mElement(x);
  }
  function badaRight(L, R) {           // >-  : e^{-x log x}
    var o = R == null ? L : num(R), x = Math.abs(o) + 1e-6;
    return Math.exp(-xLogX(x));
  }

  /* -------------------------------------------------------- quantum runtime */
  function qreg(n) {
    n = Math.max(1, Math.min(12, Math.floor(n)));
    var size = 1 << n, re = new Float64Array(size), im = new Float64Array(size);
    re[0] = 1;
    return { __qreg: true, n: n, size: size, re: re, im: im };
  }
  function apply1(q, target, m) { // m = [[ar,ai],[br,bi],[cr,ci],[dr,di]]
    var bit = 1 << target;
    for (var i = 0; i < q.size; i++) {
      if (i & bit) continue;
      var j = i | bit;
      var ar = q.re[i], ai = q.im[i], br = q.re[j], bi = q.im[j];
      q.re[i] = m[0][0] * ar - m[0][1] * ai + m[1][0] * br - m[1][1] * bi;
      q.im[i] = m[0][0] * ai + m[0][1] * ar + m[1][0] * bi + m[1][1] * br;
      q.re[j] = m[2][0] * ar - m[2][1] * ai + m[3][0] * br - m[3][1] * bi;
      q.im[j] = m[2][0] * ai + m[2][1] * ar + m[3][0] * bi + m[3][1] * br;
    }
  }
  var S = 1 / Math.sqrt(2);
  function gateH(q, t) { apply1(q, t, [[S, 0], [S, 0], [S, 0], [-S, 0]]); }
  function gateX(q, t) { apply1(q, t, [[0, 0], [1, 0], [1, 0], [0, 0]]); }
  function gateZ(q, t) { apply1(q, t, [[1, 0], [0, 0], [0, 0], [-1, 0]]); }
  function gateRY(q, t, th) { var c = Math.cos(th / 2), s = Math.sin(th / 2); apply1(q, t, [[c, 0], [-s, 0], [s, 0], [c, 0]]); }
  function gateCNOT(q, c, t) {
    var cb = 1 << c, tb = 1 << t;
    for (var i = 0; i < q.size; i++) {
      if ((i & cb) && !(i & tb)) {
        var j = i | tb, r = q.re[i], m = q.im[i];
        q.re[i] = q.re[j]; q.im[i] = q.im[j]; q.re[j] = r; q.im[j] = m;
      }
    }
  }
  function qprobs(q) { var p = []; for (var i = 0; i < q.size; i++) p.push(q.re[i] * q.re[i] + q.im[i] * q.im[i]); return p; }
  function bits(i, n) { var s = ""; for (var b = n - 1; b >= 0; b--) s += (i >> b) & 1; return s; }
  function qmeasure(q, rng) {
    var p = qprobs(q), r = rng(), acc = 0, idx = 0;
    for (var i = 0; i < p.length; i++) { acc += p[i]; if (r <= acc) { idx = i; break; } idx = i; }
    q.re = new Float64Array(q.size); q.im = new Float64Array(q.size); q.re[idx] = 1;
    return bits(idx, q.n);
  }
  function toQASM(nQubits, circuit) {
    var out = ["OPENQASM 2.0;", 'include "qelib1.inc";'];
    var n = Math.max(1, nQubits);
    out.push("qreg q[" + n + "];", "creg c[" + n + "];");
    circuit.forEach(function (g) {
      switch (g.gate) {
        case "h": out.push("h q[" + g.a + "];"); break;
        case "x": out.push("x q[" + g.a + "];"); break;
        case "z": out.push("z q[" + g.a + "];"); break;
        case "ry": out.push("ry(" + g.theta.toFixed(6) + ") q[" + g.a + "];"); break;
        case "cx": out.push("cx q[" + g.a + "],q[" + g.b + "];"); break;
        case "measure": out.push("measure q[" + g.a + "] -> c[" + g.a + "];"); break;
      }
    });
    return out.join("\n");
  }

  /* -------------------------------------------------------------- builtins */
  // Each builtin is fn(args, ctx). ctx has {rng, circuit, trackQ(n)}.
  var BUILTINS = {
    // math
    sqrt: function (a) { return Math.sqrt(num(a[0])); },
    abs: function (a) { return Math.abs(num(a[0])); },
    log: function (a) { return Math.log(num(a[0])); },
    exp: function (a) { return Math.exp(num(a[0])); },
    sin: function (a) { return Math.sin(num(a[0])); },
    cos: function (a) { return Math.cos(num(a[0])); },
    floor: function (a) { return Math.floor(num(a[0])); },
    ceil: function (a) { return Math.ceil(num(a[0])); },
    round: function (a) { return Math.round(num(a[0])); },
    pow: function (a) { return Math.pow(num(a[0]), num(a[1])); },
    min: function (a) { return Math.min.apply(Math, a.map(num)); },
    max: function (a) { return Math.max.apply(Math, a.map(num)); },
    pi: function () { return Math.PI; },
    e: function () { return Math.E; },
    len: function (a) { var v = a[0]; if (typeof v === "string") return v.length; if (isArr(v)) return v.length; if (isObj(v)) return v.keys.length; if (isQReg(v)) return v.n; return 0; },
    str: function (a) { return show(a[0]); },
    // arrays & objects
    push: function (a) { if (isArr(a[0])) a[0].push(a[1]); return a[0]; },
    pop: function (a) { return (isArr(a[0]) && a[0].length) ? a[0].pop() : null; },
    keys: function (a) { return isObj(a[0]) ? a[0].keys.slice() : []; },
    has: function (a) { return isObj(a[0]) ? (String(a[1]) in a[0].m) : false; },
    get: function (a) { return rtIndexGet(a[0], a[1]); },
    put: function (a) { return rtIndexSet(a[0], a[1], a[2]); },
    range: function (a) { var n = Math.trunc(num(a[0])), r = []; for (var i = 0; i < n; i++) r.push(i); return r; },
    // Bada special functions
    gamma: function (a) { return gamma(num(a[0])); },
    beta: function (a) { return beta(num(a[0]), num(a[1])); },
    xi: function (a) { return typeof a[0] === "string" ? xiOf(a[0]) : xiOf(show(a[0])); },
    entropy: function (a) { return shannon(tokenizeText(typeof a[0] === "string" ? a[0] : show(a[0]))); },
    zeta: function (a) { var lx = Math.log(num(a[2])); return lx === 0 ? Infinity : beta(num(a[0]), num(a[1])) / lx; },
    xlogx: function (a) { return xLogX(num(a[0])); },
    // quantum standard library
    qreg: function (a, ctx) { var q = qreg(num(a[0])); ctx.trackQ(q.n); return q; },
    h: function (a, ctx) { gateH(a[0], num(a[1])); ctx.circuit.push({ gate: "h", a: num(a[1]) }); return a[0]; },
    x: function (a, ctx) { gateX(a[0], num(a[1])); ctx.circuit.push({ gate: "x", a: num(a[1]) }); return a[0]; },
    z: function (a, ctx) { gateZ(a[0], num(a[1])); ctx.circuit.push({ gate: "z", a: num(a[1]) }); return a[0]; },
    ry: function (a, ctx) { gateRY(a[0], num(a[1]), num(a[2])); ctx.circuit.push({ gate: "ry", a: num(a[1]), theta: num(a[2]) }); return a[0]; },
    cnot: function (a, ctx) { gateCNOT(a[0], num(a[1]), num(a[2])); ctx.circuit.push({ gate: "cx", a: num(a[1]), b: num(a[2]) }); return a[0]; },
    probs: function (a) { return qprobs(a[0]).map(function (p) { return Math.round(p * 1e6) / 1e6; }).join(" "); },
    prob: function (a) { return qprobs(a[0])[num(a[1])]; },
    measure: function (a, ctx) { for (var i = 0; i < a[0].n; i++) ctx.circuit.push({ gate: "measure", a: i }); return qmeasure(a[0], ctx.rng); }
  };
  var BUILTIN_NAMES = Object.keys(BUILTINS);

  /* ================================================================ LEXER */
  function tokenize(src) {
    var toks = [], i = 0, line = 1, col = 1, n = src.length;
    function push(type, value) { toks.push({ type: type, value: value, line: line, col: col }); }
    function isIdStart(c) { return /[A-Za-z_Ͱ-Ͽ]/.test(c); }
    function isId(c) { return /[A-Za-z0-9_]/.test(c); }
    var KW = { set: 1, print: 1, "if": 1, "else": 1, "while": 1, fn: 1, "return": 1, "true": 1, "false": 1, and: 1, or: 1, not: 1, as: 1 };
    while (i < n) {
      var c = src[i];
      if (c === "\n") { push("NL"); i++; line++; col = 1; continue; }
      if (c === " " || c === "\t" || c === "\r") { i++; col++; continue; }
      if (c === "#") { while (i < n && src[i] !== "\n") i++; continue; }
      if (c === "Ω") { push("IDENT", "Omega"); i++; col++; continue; }
      if (c === '"') {
        var s = ""; i++; col++;
        while (i < n && src[i] !== '"') {
          if (src[i] === "\\") { i++; var e = src[i]; s += e === "n" ? "\n" : e === "t" ? "\t" : e; }
          else s += src[i];
          i++; col++;
        }
        i++; col++; push("STRING", s); continue;
      }
      if (/[0-9]/.test(c) || (c === "." && /[0-9]/.test(src[i + 1]))) {
        var num0 = ""; while (i < n && /[0-9.]/.test(src[i])) { num0 += src[i]; i++; col++; }
        if (src[i] === "e" || src[i] === "E") { num0 += src[i++]; if (src[i] === "+" || src[i] === "-") num0 += src[i++]; while (i < n && /[0-9]/.test(src[i])) num0 += src[i++]; }
        push("NUMBER", parseFloat(num0)); continue;
      }
      if (isIdStart(c)) {
        var id = ""; while (i < n && isId(src[i])) { id += src[i]; i++; col++; }
        push(KW[id] ? "KW" : "IDENT", id); continue;
      }
      var two = src.substr(i, 2);
      if (two === "<-" || two === "-<" || two === ">-" || two === "==" || two === "!=" ||
        two === "<=" || two === ">=" || two === "::") { push("OP", two); i += 2; col += 2; continue; }
      if ("+-*/%()<>{}[],=.:".indexOf(c) >= 0) { push("OP", c); i++; col++; continue; }
      throw new BadaError("Lex error: unexpected '" + c + "'", line, col);
    }
    push("EOF");
    return toks;
  }

  function BadaError(msg, line, col) { this.name = "BadaError"; this.message = msg + (line ? " (line " + line + ")" : ""); this.line = line; }
  BadaError.prototype = Object.create(Error.prototype);

  /* =============================================================== PARSER */
  // Pratt precedence for infix operators (higher binds tighter).
  var PREC = { "or": 1, "and": 2, "==": 3, "!=": 3, "<": 4, ">": 4, "<=": 4, ">=": 4, "<-": 5, "-<": 5, ">-": 5, "+": 6, "-": 6, "*": 7, "/": 7, "%": 7 };
  function parse(toks) {
    var pos = 0;
    function peek() { return toks[pos]; }
    function next() { return toks[pos++]; }
    function at(type, value) { var t = toks[pos]; return t.type === type && (value === undefined || t.value === value); }
    function eat(type, value) {
      var t = toks[pos];
      if (t.type !== type || (value !== undefined && t.value !== value))
        throw new BadaError("Parse error: expected " + (value || type) + " but got '" + (t.value != null ? t.value : t.type) + "'", t.line);
      pos++; return t;
    }
    function skipSep() { while (at("NL") || at("OP", ";")) pos++; }
    function skipNL() { while (at("NL")) pos++; }

    function parseProgram() {
      var body = []; skipSep();
      while (!at("EOF")) { body.push(parseStatement()); skipSep(); }
      return { type: "Program", body: body };
    }
    function parseBlock() {
      eat("OP", "{"); skipSep(); var body = [];
      while (!at("OP", "}")) { body.push(parseStatement()); skipSep(); }
      eat("OP", "}"); return { type: "Block", body: body };
    }
    function parseStatement() {
      if (at("KW", "set")) { next(); var name = eat("IDENT").value; eat("OP", "="); return { type: "Assign", name: name, value: parseExpr() }; }
      if (at("KW", "print")) { next(); return { type: "Print", value: parseExpr() }; }
      if (at("KW", "if")) return parseIf();
      if (at("KW", "while")) { next(); var cond = parseExpr(); skipNL(); var b = parseBlock(); return { type: "While", cond: cond, body: b }; }
      if (at("KW", "fn")) {
        next(); var fname = eat("IDENT").value; eat("OP", "(");
        var params = []; if (!at("OP", ")")) { params.push(eat("IDENT").value); while (at("OP", ",")) { next(); params.push(eat("IDENT").value); } }
        eat("OP", ")"); skipNL(); var body = parseBlock();
        return { type: "Fn", name: fname, params: params, body: body };
      }
      if (at("KW", "return")) { next(); if (at("NL") || at("OP", ";") || at("OP", "}") || at("EOF")) return { type: "Return", value: null }; return { type: "Return", value: parseExpr() }; }
      // Omega::push EXPR as NAME
      if (at("IDENT", "Omega") && toks[pos + 1] && toks[pos + 1].type === "OP" && toks[pos + 1].value === "::") {
        next(); eat("OP", "::"); eat("IDENT", "push"); var ex = parseExpr(); var as = null;
        if (at("KW", "as")) { next(); as = eat("IDENT").value; } return { type: "Push", value: ex, as: as };
      }
      // general: an expression, optionally an assignment to an lvalue
      // (Var, Index a[i], or Member a.k).
      var lhs = parseExpr();
      if (at("OP", "=")) {
        next(); var value = parseExpr();
        if (lhs.type === "Var") return { type: "Assign", name: lhs.name, value: value };
        if (lhs.type === "Index") return { type: "SetIndex", obj: lhs.obj, index: lhs.index, value: value };
        if (lhs.type === "Member") return { type: "SetMember", obj: lhs.obj, key: lhs.key, value: value };
        throw new BadaError("invalid assignment target");
      }
      return { type: "ExprStmt", value: lhs };
    }
    function parseIf() {
      eat("KW", "if"); var cond = parseExpr(); skipNL(); var cons = parseBlock(); var alt = null;
      skipNL();
      if (at("KW", "else")) { next(); skipNL(); alt = at("KW", "if") ? parseIf() : parseBlock(); }
      return { type: "If", cond: cond, cons: cons, alt: alt };
    }
    function parseExpr(minPrec) {
      minPrec = minPrec || 0;
      var left = parseUnary();
      while (true) {
        var t = peek(); var op = null;
        if (t.type === "OP" && PREC[t.value]) op = t.value;
        else if (t.type === "KW" && (t.value === "and" || t.value === "or")) op = t.value;
        if (op == null || PREC[op] <= minPrec) break;
        next();
        var right = parseExpr(PREC[op]);
        left = { type: "Binary", op: op, left: left, right: right };
      }
      return left;
    }
    function parseUnary() {
      if (at("OP", "-")) { next(); return { type: "Unary", op: "-", operand: parseUnary() }; }
      if (at("KW", "not")) { next(); return { type: "Unary", op: "not", operand: parseUnary() }; }
      return parsePostfix();
    }
    // postfix chain: call f(...), index a[i], member a.k
    function parsePostfix() {
      var e = parsePrimary();
      while (true) {
        if (at("OP", "(")) {
          next(); var args = [];
          if (!at("OP", ")")) { args.push(parseExpr()); while (at("OP", ",")) { next(); args.push(parseExpr()); } }
          eat("OP", ")"); e = { type: "Call", callee: e, args: args };
        } else if (at("OP", "[")) {
          next(); var idx = parseExpr(); eat("OP", "]"); e = { type: "Index", obj: e, index: idx };
        } else if (at("OP", ".")) {
          next(); var key = eat("IDENT").value; e = { type: "Member", obj: e, key: key };
        } else break;
      }
      return e;
    }
    function parsePrimary() {
      var t = peek();
      if (t.type === "NUMBER") { next(); return { type: "Num", value: t.value }; }
      if (t.type === "STRING") { next(); return { type: "Str", value: t.value }; }
      if (t.type === "KW" && (t.value === "true" || t.value === "false")) { next(); return { type: "Bool", value: t.value === "true" }; }
      if (t.type === "IDENT") { next(); return { type: "Var", name: t.value }; }
      if (t.type === "OP" && t.value === "(") { next(); var e = parseExpr(); eat("OP", ")"); return e; }
      // array literal  [e1, e2, ...]
      if (t.type === "OP" && t.value === "[") {
        next(); var elts = []; skipNL();
        while (!at("OP", "]")) { elts.push(parseExpr()); skipNL(); if (at("OP", ",")) { next(); skipNL(); } else break; }
        eat("OP", "]"); return { type: "Array", elements: elts };
      }
      // object literal  { key: v, "str": v, ... }
      if (t.type === "OP" && t.value === "{") {
        next(); var pairs = []; skipNL();
        while (!at("OP", "}")) {
          var k = at("STRING") ? eat("STRING").value : eat("IDENT").value;
          eat("OP", ":"); var val = parseExpr(); pairs.push({ key: k, value: val }); skipNL();
          if (at("OP", ",")) { next(); skipNL(); } else break;
        }
        eat("OP", "}"); return { type: "Object", pairs: pairs };
      }
      throw new BadaError("Parse error: unexpected '" + (t.value != null ? t.value : t.type) + "'", t.line);
    }
    return parseProgram();
  }

  /* ========================================================== INTERPRETER */
  function Scope(parent) { this.vars = Object.create(null); this.parent = parent || null; }
  Scope.prototype.get = function (n) { var s = this; while (s) { if (n in s.vars) return s.vars[n]; s = s.parent; } return undefined; };
  Scope.prototype.has = function (n) { var s = this; while (s) { if (n in s.vars) return true; s = s.parent; } return false; };
  Scope.prototype.set = function (n, v) { this.vars[n] = v; };

  function makeCtx() {
    var seed = 0x2545f491; // deterministic default RNG (measure); UI can reseed
    function rng() { seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; seed |= 0; return ((seed >>> 0) / 4294967296); }
    return { rng: rng, circuit: [], qubits: 0, trackQ: function (n) { if (n > this.qubits) this.qubits = n; } };
  }

  function ReturnSignal(v) { this.value = v; }

  function Interpreter() { }
  Interpreter.prototype.run = function (ast) {
    var out = [], globals = new Scope(), ctx = makeCtx();
    var self = this;
    function callFn(fn, args) {
      if (typeof fn === "function") return fn(args, ctx);          // builtin
      if (fn && fn.__fn) {
        var local = new Scope(globals);
        for (var i = 0; i < fn.params.length; i++) local.set(fn.params[i], args[i]);
        try { execBlock(fn.body, local); } catch (e) { if (e instanceof ReturnSignal) return e.value; throw e; }
        return null;
      }
      throw new BadaError("call of non-function");
    }
    function evalNode(node, scope) {
      switch (node.type) {
        case "Num": return node.value;
        case "Str": return node.value;
        case "Bool": return node.value;
        case "Var":
          if (scope.has(node.name)) return scope.get(node.name);
          if (BUILTINS[node.name]) return BUILTINS[node.name];
          return 0; // undefined var → Ω-lattice zero (matches nodef default)
        case "Unary": {
          var v = evalNode(node.operand, scope);
          return node.op === "-" ? -num(v) : !truthy(v);
        }
        case "Binary": return evalBinary(node, scope);
        case "Array": return node.elements.map(function (e) { return evalNode(e, scope); });
        case "Object": { var o = makeObj(); node.pairs.forEach(function (p) { objSet(o, p.key, evalNode(p.value, scope)); }); return o; }
        case "Index": return rtIndexGet(evalNode(node.obj, scope), evalNode(node.index, scope));
        case "Member": return rtMemberGet(evalNode(node.obj, scope), node.key);
        case "Call": {
          var callee = node.callee.type === "Var" ? (BUILTINS[node.callee.name] || scope.get(node.callee.name)) : evalNode(node.callee, scope);
          var args = node.args.map(function (a) { return evalNode(a, scope); });
          return callFn(callee, args);
        }
      }
      throw new BadaError("cannot eval " + node.type);
    }
    function evalBinary(node, scope) {
      var op = node.op;
      if (op === "and") return truthy(evalNode(node.left, scope)) ? evalNode(node.right, scope) : false;
      if (op === "or") { var l = evalNode(node.left, scope); return truthy(l) ? l : evalNode(node.right, scope); }
      if (op === "<-" || op === "-<" || op === ">-") {
        var Lv = evalNode(node.left, scope), Rv = evalNode(node.right, scope);
        var res = op === "<-" ? badaLeft(num(Lv), Rv) : op === "-<" ? badaIntegral(num(Lv), Rv) : badaRight(num(Lv), Rv);
        if (node.left.type === "Var") scope.set(node.left.name, res); // fluent update
        return res;
      }
      var a = evalNode(node.left, scope), b = evalNode(node.right, scope);
      switch (op) {
        case "+": return (typeof a === "string" || typeof b === "string") ? show(a) + show(b) : num(a) + num(b);
        case "-": return num(a) - num(b);
        case "*": return num(a) * num(b);
        case "/": return num(a) / num(b);
        case "%": return num(a) % num(b);
        case "==": return a === b || num(a) === num(b);
        case "!=": return !(a === b || num(a) === num(b));
        case "<": return num(a) < num(b);
        case ">": return num(a) > num(b);
        case "<=": return num(a) <= num(b);
        case ">=": return num(a) >= num(b);
      }
      throw new BadaError("bad operator " + op);
    }
    function execBlock(block, scope) { for (var i = 0; i < block.body.length; i++) execStmt(block.body[i], scope); }
    function execStmt(node, scope) {
      switch (node.type) {
        case "Assign": scope.set(node.name, evalNode(node.value, scope)); return;
        case "SetIndex": rtIndexSet(evalNode(node.obj, scope), evalNode(node.index, scope), evalNode(node.value, scope)); return;
        case "SetMember": rtMemberSet(evalNode(node.obj, scope), node.key, evalNode(node.value, scope)); return;
        case "Print": out.push(show(evalNode(node.value, scope))); return;
        case "ExprStmt": evalNode(node.value, scope); return;
        case "If": if (truthy(evalNode(node.cond, scope))) execBlock(node.cons, scope); else if (node.alt) { node.alt.type === "If" ? execStmt(node.alt, scope) : execBlock(node.alt, scope); } return;
        case "While": { var guard = 0; while (truthy(evalNode(node.cond, scope))) { execBlock(node.body, scope); if (++guard > 1e7) throw new BadaError("while loop exceeded 1e7 iterations"); } return; }
        case "Fn": scope.set(node.name, { __fn: true, name: node.name, params: node.params, body: node.body }); return;
        case "Return": throw new ReturnSignal(node.value ? evalNode(node.value, scope) : null);
        case "Push": {
          var v = evalNode(node.value, scope), xi = xiOf(show(v));
          out.push("Ω::push " + (node.as || ("Ω" + out.length)) + " (Ξ=" + xi.toFixed(4) + ")");
          return;
        }
      }
      throw new BadaError("cannot exec " + node.type);
    }
    for (var i = 0; i < ast.body.length; i++) execStmt(ast.body[i], globals);
    return { output: out, qasm: toQASM(ctx.qubits, ctx.circuit), circuit: ctx.circuit, qubits: ctx.qubits };
  };

  /* ========================================== COMPILER (AST → bytecode) + VM */
  // Instruction = {op, arg}. Functions compile to separate chunks (by index).
  function compile(ast) {
    var functions = []; // {name, params, code}
    function compileChunk(bodyNodes, params) {
      var code = [];
      function emit(op, arg) { code.push({ op: op, arg: arg }); return code.length - 1; }
      function cExpr(node) {
        switch (node.type) {
          case "Num": emit("PUSH", node.value); return;
          case "Str": emit("PUSH", node.value); return;
          case "Bool": emit("PUSH", node.value); return;
          case "Var": emit("LOAD", node.name); return;
          case "Array": node.elements.forEach(cExpr); emit("MKARR", node.elements.length); return;
          case "Object": node.pairs.forEach(function (p) { emit("PUSH", p.key); cExpr(p.value); }); emit("MKOBJ", node.pairs.length); return;
          case "Index": cExpr(node.obj); cExpr(node.index); emit("INDEX"); return;
          case "Member": cExpr(node.obj); emit("MEMBER", node.key); return;
          case "Unary": cExpr(node.operand); emit(node.op === "-" ? "NEG" : "NOT"); return;
          case "Call": {
            var name = node.callee.type === "Var" ? node.callee.name : null;
            if (name == null) cExpr(node.callee);   // push the callee value first
            node.args.forEach(cExpr);
            emit("CALL", { name: name, argc: node.args.length }); return;
          }
          case "Binary": {
            var op = node.op;
            if (op === "and") { cExpr(node.left); var j = emit("JMP_IF_FALSE_KEEP", 0); emit("POP"); cExpr(node.right); code[j].arg = code.length; return; }
            if (op === "or") { cExpr(node.left); var j2 = emit("JMP_IF_TRUE_KEEP", 0); emit("POP"); cExpr(node.right); code[j2].arg = code.length; return; }
            if (op === "<-" || op === "-<" || op === ">-") {
              cExpr(node.left); cExpr(node.right);
              emit("BADA", { op: op, lvalue: node.left.type === "Var" ? node.left.name : null }); return;
            }
            cExpr(node.left); cExpr(node.right); emit("BIN", op); return;
          }
        }
        throw new BadaError("compile: cannot compile expr " + node.type);
      }
      function cStmt(node) {
        switch (node.type) {
          case "Assign": cExpr(node.value); emit("STORE", node.name); return;
          case "SetIndex": cExpr(node.obj); cExpr(node.index); cExpr(node.value); emit("SETIDX"); return;
          case "SetMember": cExpr(node.obj); cExpr(node.value); emit("SETMEM", node.key); return;
          case "Print": cExpr(node.value); emit("PRINT"); return;
          case "ExprStmt": cExpr(node.value); emit("POP"); return;
          case "Return": if (node.value) cExpr(node.value); else emit("PUSH", null); emit("RET"); return;
          case "Fn": {
            var idx = functions.length; functions.push(null);
            functions[idx] = { name: node.name, params: node.params, code: compileChunk(node.body.body, node.params) };
            emit("MKFUN", idx); emit("STORE", node.name); return;
          }
          case "Push": cExpr(node.value); emit("PUSHΩ", node.as); return;
          case "If": {
            cExpr(node.cond); var jf = emit("JMP_IF_FALSE", 0);
            node.cons.body.forEach(cStmt);
            if (node.alt) {
              var jend = emit("JMP", 0); code[jf].arg = code.length;
              if (node.alt.type === "If") cStmt(node.alt); else node.alt.body.forEach(cStmt);
              code[jend].arg = code.length;
            } else { code[jf].arg = code.length; }
            return;
          }
          case "While": {
            var top = code.length; cExpr(node.cond); var jf2 = emit("JMP_IF_FALSE", 0);
            node.body.body.forEach(cStmt); emit("JMP", top); code[jf2].arg = code.length; return;
          }
        }
        throw new BadaError("compile: cannot compile stmt " + node.type);
      }
      bodyNodes.forEach(cStmt);
      emit("PUSH", null); emit("RET");
      return code;
    }
    var main = compileChunk(ast.body, []);
    return { main: main, functions: functions };
  }

  function disassemble(program) {
    function dis(code, title) {
      var lines = ["; " + title];
      code.forEach(function (ins, i) {
        var a = ins.arg;
        if (a && typeof a === "object") a = JSON.stringify(a);
        lines.push(String(i).padStart(3, " ") + "  " + ins.op + (a !== undefined ? " " + a : ""));
      });
      return lines.join("\n");
    }
    var parts = [dis(program.main, "main")];
    program.functions.forEach(function (f, i) { parts.push(dis(f.code, "fn#" + i + " " + f.name + "(" + f.params.join(",") + ")")); });
    return parts.join("\n\n");
  }

  function runVM(program) {
    var out = [], ctx = makeCtx(), globals = Object.create(null);
    function execChunk(code, locals) {
      var stack = [], ip = 0, guard = 0;
      function look(name) { if (locals && name in locals) return locals[name]; if (name in globals) return globals[name]; if (BUILTINS[name]) return BUILTINS[name]; return 0; }
      while (ip < code.length) {
        if (++guard > 5e7) throw new BadaError("VM step budget exceeded");
        var ins = code[ip++], op = ins.op, a = ins.arg;
        switch (op) {
          case "PUSH": stack.push(a); break;
          case "POP": stack.pop(); break;
          case "LOAD": stack.push(look(a)); break;
          case "STORE": { var v = stack.pop(); if (locals && !(a in globals)) locals[a] = v; else globals[a] = v; } break;
          case "NEG": stack.push(-num(stack.pop())); break;
          case "NOT": stack.push(!truthy(stack.pop())); break;
          case "JMP": ip = a; break;
          case "JMP_IF_FALSE": if (!truthy(stack.pop())) ip = a; break;
          case "JMP_IF_FALSE_KEEP": if (!truthy(stack[stack.length - 1])) ip = a; break;
          case "JMP_IF_TRUE_KEEP": if (truthy(stack[stack.length - 1])) ip = a; break;
          case "PRINT": out.push(show(stack.pop())); break;
          case "MKFUN": stack.push({ __fn: true, __idx: a, name: program.functions[a].name, params: program.functions[a].params }); break;
          case "PUSHΩ": { var pv = stack.pop(), xi = xiOf(show(pv)); out.push("Ω::push " + (a || ("Ω" + out.length)) + " (Ξ=" + xi.toFixed(4) + ")"); } break;
          case "BIN": { var rgt = stack.pop(), lft = stack.pop(); stack.push(binOp(a, lft, rgt)); } break;
          case "MKARR": { var arr = new Array(a); for (var q = a - 1; q >= 0; q--) arr[q] = stack.pop(); stack.push(arr); } break;
          case "MKOBJ": { var o = makeObj(), tmp = []; for (var q = 0; q < a; q++) { var vv = stack.pop(), kk = stack.pop(); tmp.push([kk, vv]); } for (var q = tmp.length - 1; q >= 0; q--) objSet(o, tmp[q][0], tmp[q][1]); stack.push(o); } break;
          case "INDEX": { var ii = stack.pop(), oo = stack.pop(); stack.push(rtIndexGet(oo, ii)); } break;
          case "MEMBER": { var om = stack.pop(); stack.push(rtMemberGet(om, a)); } break;
          case "SETIDX": { var sv = stack.pop(), si = stack.pop(), so = stack.pop(); rtIndexSet(so, si, sv); } break;
          case "SETMEM": { var mv = stack.pop(), mo = stack.pop(); rtMemberSet(mo, a, mv); } break;
          case "BADA": {
            var R = stack.pop(), L = stack.pop();
            var res = a.op === "<-" ? badaLeft(num(L), R) : a.op === "-<" ? badaIntegral(num(L), R) : badaRight(num(L), R);
            if (a.lvalue) { if (locals && !(a.lvalue in globals)) locals[a.lvalue] = res; else globals[a.lvalue] = res; }
            stack.push(res);
          } break;
          case "CALL": {
            var argc = a.argc, args = new Array(argc);
            for (var k = argc - 1; k >= 0; k--) args[k] = stack.pop();
            var fn = a.name != null ? look(a.name) : stack.pop();
            stack.push(callValue(fn, args));
          } break;
          case "RET": return stack.pop();
        }
      }
      return null;
    }
    function binOp(op, a, b) { // a = left operand, b = right operand
      switch (op) {
        case "+": return (typeof a === "string" || typeof b === "string") ? show(a) + show(b) : num(a) + num(b);
        case "-": return num(a) - num(b);
        case "*": return num(a) * num(b);
        case "/": return num(a) / num(b);
        case "%": return num(a) % num(b);
        case "==": return a === b || num(a) === num(b);
        case "!=": return !(a === b || num(a) === num(b));
        case "<": return num(a) < num(b);
        case ">": return num(a) > num(b);
        case "<=": return num(a) <= num(b);
        case ">=": return num(a) >= num(b);
      }
      throw new BadaError("VM bad op " + op);
    }
    function callValue(fn, args) {
      if (typeof fn === "function") return fn(args, ctx);
      if (fn && fn.__fn) {
        var locals = Object.create(null);
        for (var i = 0; i < fn.params.length; i++) locals[fn.params[i]] = args[i];
        return execChunk(program.functions[fn.__idx].code, locals);
      }
      throw new BadaError("VM call of non-function");
    }
    execChunk(program.main, null);
    return { output: out, qasm: toQASM(ctx.qubits, ctx.circuit), circuit: ctx.circuit, qubits: ctx.qubits };
  }

  /* ------------------------------------------------------------ public API */
  Bada.tokenize = tokenize;
  Bada.parse = function (src) { return parse(tokenize(src)); };
  Bada.compile = function (src) { return compile(parse(tokenize(src))); };
  Bada.disassemble = function (src) { return disassemble(compile(parse(tokenize(src)))); };
  Bada.interpret = function (src) { return new Interpreter().run(parse(tokenize(src))); };  // tree-walk
  Bada.execVM = function (src) { return runVM(compile(parse(tokenize(src)))); };            // compile + VM
  Bada.run = Bada.interpret;
  Bada.toQASM = toQASM;
  Bada.BadaError = BadaError;
  Bada.builtins = BUILTIN_NAMES;
  Bada._rt = { num: num, xiOf: xiOf, badaLeft: badaLeft, badaIntegral: badaIntegral, badaRight: badaRight, beta: beta, gamma: gamma };

  if (typeof module !== "undefined" && module.exports) module.exports = Bada;
  global.Bada = Bada;
})(typeof globalThis !== "undefined" ? globalThis : this);
