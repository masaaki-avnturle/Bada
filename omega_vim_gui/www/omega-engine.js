/* omega-engine.js — the Bada / Ω-Vim engine, ported to JavaScript.
 *
 * A faithful port of the Ruby modules so the GUI editor runs fully self-
 * contained in any webview (Android APK / Windows EXE / Linux) with no Ruby:
 *
 *   Special          gamma / beta / zeta_gauge / x_log_x        (special.rb)
 *   Entropy          tokenize / shannon / distribution          (entropy.rb)
 *   Manifold         element / integral / invariant Ξ           (manifold.rb)
 *   ErrorCorrection  lorentz / rotate / orbit_average / certify (error_correction.rb)
 *   CodeFix          scan / close_orbit / analyze / fix         (code_fix.rb)
 *   Grammar          mask / open_stack / check / complete /     (grammar.rb)
 *                    reindent / indent_for_new_line
 *
 * The spinning-top (koma) integrable-system idea is intact: delimiter nesting
 * is a walk on the complex rotational body □ = e^{-i(x log x)}; correct code is
 * a CLOSED orbit; the same open-token stack drives the fix, the grammar check,
 * the parser completion and the indentation.
 */
(function (root) {
  "use strict";

  // ---- Special ------------------------------------------------------------
  var LANCZOS_G = 7;
  var LANCZOS_C = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
  ];

  function gamma(x) {
    if (x === 0) return Infinity;
    if (x < 0.5) {
      return Math.PI / (Math.sin(Math.PI * x) * gamma(1.0 - x));
    }
    x -= 1.0;
    var a = LANCZOS_C[0];
    var t = x + LANCZOS_G + 0.5;
    for (var i = 1; i < LANCZOS_G + 2; i++) a += LANCZOS_C[i] / (x + i);
    return Math.sqrt(2 * Math.PI) * Math.pow(t, x + 0.5) * Math.exp(-t) * a;
  }
  function logGamma(x) { return Math.log(Math.abs(gamma(x))); }
  function beta(p, q) { return Math.exp(logGamma(p) + logGamma(q) - logGamma(p + q)); }
  function xLogX(x) { return x <= 0 ? 0.0 : x * Math.log(x); }
  function zetaGauge(p, q, x) {
    var lx = Math.log(x);
    if (Math.abs(lx) < 1e-15) return Infinity;
    return beta(p, q) / lx;
  }

  // ---- Entropy ------------------------------------------------------------
  var TOKEN_RE = /[A-Za-z0-9_]+|[一-鿿぀-ゟ゠-ヿ]/g;
  function tokenize(text) {
    if (text == null) return [];
    var m = String(text).match(TOKEN_RE);
    return m || [];
  }
  function shannon(tokens) {
    if (!tokens || !tokens.length) return 0.0;
    var freq = Object.create(null);
    for (var i = 0; i < tokens.length; i++) freq[tokens[i]] = (freq[tokens[i]] || 0) + 1;
    var total = tokens.length, h = 0.0;
    for (var k in freq) { var p = freq[k] / total; h -= p * Math.log2(p); }
    return h;
  }
  function distribution(tokens) {
    if (!tokens || !tokens.length) return [];
    var freq = Object.create(null);
    for (var i = 0; i < tokens.length; i++) freq[tokens[i]] = (freq[tokens[i]] || 0) + 1;
    var total = tokens.length, out = [];
    for (var k in freq) out.push([k, freq[k] / total]);
    out.sort(function (a, b) { return b[1] - a[1]; });
    return out;
  }

  // ---- Manifold -----------------------------------------------------------
  function element(x) {
    if (x <= 1.0) return 1.0;
    var xl = xLogX(x);
    if (Math.abs(xl) < 1e-9) return 1.0;
    return 1.0 / (xl * xl);
  }
  function integral(dist) {
    if (!dist || !dist.length) return 0.0;
    var s = 0.0;
    for (var i = 0; i < dist.length; i++) { var x = i + 2.0; s += dist[i][1] * element(x); }
    return s;
  }
  function invariant(textOrTokens) {
    var tokens = (typeof textOrTokens === "string") ? tokenize(textOrTokens) : textOrTokens;
    var h = shannon(tokens);
    var m = integral(distribution(tokens));
    var n = tokens.length;
    var xi = zetaGauge(h + 1.0, m + 1.0, n + 1.0);
    return { entropy: h, manifold_integral: m, extent: n,
             beta: beta(h + 1.0, m + 1.0), invariant: xi };
  }
  function xi(text) { return invariant(text).invariant; }

  // ---- ErrorCorrection (complex-rotation spinning-top) --------------------
  function lorentz(v) {
    v = Math.min(Math.abs(v), 0.999999);
    return 1.0 / Math.sqrt(1.0 - v * v);
  }
  function median(arr) {
    if (!arr.length) return 0.0;
    var s = arr.slice().sort(function (a, b) { return a - b; });
    var mid = s.length >> 1;
    return (s.length % 2) ? s[mid] : (s[mid - 1] + s[mid]) / 2.0;
  }
  function rotate(value, theta) {
    // |e^{iθ}·value| = |value|
    var re = Math.cos(theta) * value, im = Math.sin(theta) * value;
    return Math.sqrt(re * re + im * im);
  }
  function orbitAverage(samples) {
    if (!samples || !samples.length) return 0.0;
    var med = median(samples);
    var spread = Math.max(median(samples.map(function (x) { return Math.abs(x - med); })), 1e-9);
    var acc = 0.0, weight = 0.0;
    for (var i = 0; i < samples.length; i++) {
      var v = Math.abs(samples[i] - med) / (spread * 6.0);
      var w = 1.0 / lorentz(v);
      acc += samples[i] * w; weight += w;
    }
    return weight === 0 ? med : acc / weight;
  }
  function correct(samples) {
    if (!samples || !samples.length) return { value: 0.0, residual: 0.0, samples: 0 };
    var est = orbitAverage(samples);
    var res = Math.sqrt(samples.reduce(function (s, x) { return s + (x - est) * (x - est); }, 0) / samples.length);
    return { value: est, residual: res, samples: samples.length };
  }
  function certifyInvariant(text, tol) {
    tol = tol == null ? 1e-6 : tol;
    var base = invariant(text.length ? text : " ").invariant;
    var views = [];
    for (var k = 0; k < 8; k++) views.push(rotate(base, 2 * Math.PI * k / 8.0));
    var c = correct(views);
    return { invariant: base, certified: c.value,
             conserved: Math.abs(c.value - base) <= (Math.abs(base) * tol + tol),
             residual: c.residual };
  }

  // ---- shared: bracket tables ---------------------------------------------
  var OPEN = { "(": ")", "[": "]", "{": "}" };
  var CLOSE = { ")": "(", "]": "[", "}": "{" };
  var LINE_COMMENTS = ["#", "//", "--", ";"];
  var BLOCK_COMMENTS = [["/*", "*/"]];

  // ---- CodeFix (delimiter/quote/comment orbit) ----------------------------
  function lineCommentAt(chars, i) {
    return LINE_COMMENTS.some(function (p) {
      for (var k = 0; k < p.length; k++) if (chars[i + k] !== p[k]) return false;
      return true;
    });
  }
  function scan(source) {
    var stack = [], defects = [], maxDepth = 0;
    var line = 1, col = 0, inString = null, stringStart = null, escaped = false;
    var chars = Array.from(source), i = 0;
    while (i < chars.length) {
      var c = chars[i], nxt = chars[i + 1];
      col += 1;
      if (c === "\n") {
        if (inString && inString !== "block" && (inString === '"' || inString === "'" || inString === "`")) {
          defects.push({ line: line, col: col, kind: "quote",
            message: "unterminated string opened with " + inString,
            suggestion: "insert closing " + inString });
          inString = null;
        }
        line += 1; col = 0; i += 1; continue;
      }
      if (inString) {
        if (inString === "block") {
          if (c === "*" && nxt === "/") { inString = null; i += 2; col += 1; continue; }
        } else {
          if (escaped) escaped = false;
          else if (c === "\\") escaped = true;
          else if (c === inString) inString = null;
        }
        i += 1; continue;
      }
      var two = c + (nxt || "");
      if (two === "/*") { inString = "block"; i += 2; col += 1; continue; }
      if (lineCommentAt(chars, i)) { while (i < chars.length && chars[i] !== "\n") i += 1; continue; }
      if (c === '"' || c === "'" || c === "`") { inString = c; stringStart = [line, col]; i += 1; continue; }
      if (OPEN[c]) {
        stack.push([c, line, col]);
        if (stack.length > maxDepth) maxDepth = stack.length;
      } else if (CLOSE[c]) {
        if (!stack.length) {
          defects.push({ line: line, col: col, kind: "unmatched_close",
            message: "stray '" + c + "' with no opener",
            suggestion: "remove '" + c + "' or add matching '" + CLOSE[c] + "' earlier" });
        } else {
          var top = stack.pop(), want = OPEN[top[0]];
          if (want !== c) {
            defects.push({ line: line, col: col, kind: "mismatch",
              message: "'" + top[0] + "' at " + top[1] + ":" + top[2] + " closed by '" + c + "'",
              suggestion: "replace '" + c + "' with '" + want + "'" });
          }
        }
      }
      i += 1;
    }
    var quoteDefect = 0;
    if (inString) {
      quoteDefect = 1;
      if (inString === "block") {
        defects.push({ line: line, col: col, kind: "comment",
          message: "unterminated block comment /* ... */", suggestion: "insert closing */" });
      } else {
        var ss = stringStart || [line, col];
        defects.push({ line: ss[0], col: ss[1], kind: "quote",
          message: "unterminated string opened with " + inString,
          suggestion: "insert closing " + inString });
      }
    }
    stack.forEach(function (e) {
      defects.push({ line: e[1], col: e[2], kind: "unclosed",
        message: "'" + e[0] + "' opened at " + e[1] + ":" + e[2] + " never closed",
        suggestion: "insert '" + OPEN[e[0]] + "'" });
    });
    return { winding: stack.length, maxDepth: maxDepth, quoteDefect: quoteDefect,
             defects: defects, openStack: stack };
  }

  function splitLines(s) { return s.split("\n"); }
  function replaceAt(source, line, col, ch) {
    var lines = splitLines(source);
    if (line < 1 || line > lines.length) return source;
    var s = lines[line - 1], idx = col - 1;
    if (idx < 0 || idx >= s.length) return source;
    lines[line - 1] = s.slice(0, idx) + ch + s.slice(idx + 1);
    return lines.join("\n");
  }
  function deleteAt(source, line, col) {
    var lines = splitLines(source);
    if (line < 1 || line > lines.length) return source;
    var s = lines[line - 1], idx = col - 1;
    if (idx < 0 || idx >= s.length) return source;
    lines[line - 1] = s.slice(0, idx) + s.slice(idx + 1);
    return lines.join("\n");
  }
  function appendToLine(source, line, str) {
    var lines = splitLines(source);
    if (line < 1 || line > lines.length) return source + str;
    lines[line - 1] = lines[line - 1] + str;
    return lines.join("\n");
  }
  function lineRotationLoad(lines) {
    var out = [];
    for (var i = 0; i < lines.length; i++) {
      var d = 0, ln = lines[i];
      for (var j = 0; j < ln.length; j++) { if (OPEN[ln[j]]) d += 1; if (CLOSE[ln[j]]) d -= 1; }
      out.push(d);
    }
    return out;
  }
  function closeOrbit(source) {
    var applied = [], out = source, st = scan(out);
    st.defects.filter(function (d) { return d.kind === "mismatch"; }).forEach(function (d) {
      var m = d.suggestion.match(/replace '.' with '(.)'/);
      if (m) { out = replaceAt(out, d.line, d.col, m[1]); applied.push("line " + d.line + ": " + d.message + " -> " + d.suggestion); }
    });
    st = scan(out);
    st.defects.filter(function (d) { return d.kind === "unmatched_close"; })
      .sort(function (a, b) { return (b.line - a.line) || (b.col - a.col); })
      .forEach(function (d) { out = deleteAt(out, d.line, d.col); applied.push("line " + d.line + ": removed stray closer"); });
    st = scan(out);
    st.defects.filter(function (d) { return d.kind === "quote"; })
      .sort(function (a, b) { return b.line - a.line; })
      .forEach(function (d) {
        var q = (d.message.match(/opened with (.)/) || [])[1];
        if (q) { out = appendToLine(out, d.line, q); applied.push("line " + d.line + ": closed unterminated string"); }
      });
    if (st.defects.some(function (d) { return d.kind === "comment"; })) {
      out = out.replace(/\s+$/, "") + "\n*/\n"; applied.push("closed unterminated block comment");
    }
    st = scan(out);
    if (st.openStack.length) {
      var closers = st.openStack.slice().reverse().map(function (e) { return OPEN[e[0]]; }).join("");
      out = out.replace(/\s+$/, "") + "\n" + closers + "\n";
      applied.push("appended missing closers: " + closers);
    }
    return { out: out, applied: applied };
  }
  function dampWhitespace(source) {
    var applied = [], lines = splitLines(source), trimmed = false;
    lines = lines.map(function (ln) { var t = ln.replace(/\s+$/, ""); if (t !== ln) trimmed = true; return t; });
    if (trimmed) applied.push("trimmed trailing whitespace");
    var out = lines.join("\n");
    var collapsed = out.replace(/\n{3,}$/, "\n\n");
    if (collapsed !== out) applied.push("collapsed trailing blank lines");
    return { out: collapsed, applied: applied };
  }
  function analyze(source, filename) {
    var lines = splitLines(source);
    var state = scan(source);
    var load = lineRotationLoad(lines).map(Number);
    var corrected = correct(load);
    var cert = certifyInvariant(source.length ? source : " ");
    return {
      filename: filename || null, lines: lines.length,
      winding: state.winding, max_depth: state.maxDepth, quote_defect: state.quoteDefect,
      defects: state.defects, orbit_closed: state.defects.length === 0,
      rotation_residual: corrected.residual,
      certified_invariant: cert.certified, invariant_conserved: cert.conserved
    };
  }
  function fix(source, filename) {
    var before = analyze(source, filename);
    var c1 = closeOrbit(source);
    var c2 = dampWhitespace(c1.out);
    var applied = c1.applied.concat(c2.applied);
    var after = analyze(c2.out, filename);
    return {
      source: c2.out, changed: c2.out !== source, applied: applied,
      before: before, report: after,
      certified_invariant: after.certified_invariant,
      invariant_conserved: after.invariant_conserved
    };
  }

  // ---- Grammar (checker / completion / indentation) -----------------------
  var SPEC = {
    c:      { style: "brace", indent: 4, line_comments: ["//"], block: [["/*", "*/"]] },
    js:     { style: "brace", indent: 2, line_comments: ["//"], block: [["/*", "*/"]] },
    json:   { style: "brace", indent: 2, line_comments: [], block: [] },
    python: { style: "colon", indent: 4, line_comments: ["#"], block: [] },
    ruby:   { style: "keyword", indent: 2, line_comments: ["#"], block: [],
              open_kw: /^(def|class|module|do|if|unless|while|until|case|begin|for)\b/,
              close_kw: /^(end)\b/, mid_kw: /^(else|elsif|when|rescue|ensure|in)\b/,
              trailing_do: /\bdo(\s*\|[^|]*\|)?\s*$/ },
    shell:  { style: "keyword", indent: 2, line_comments: ["#"], block: [],
              pairs: { "if": "fi", "case": "esac" }, do_done: true },
    lisp:   { style: "paren", indent: 1, line_comments: [";"], block: [] },
    text:   { style: "brace", indent: 2, line_comments: ["#", "//"], block: [["/*", "*/"]] }
  };
  var EXT = {
    ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".hpp": "c", ".java": "c", ".go": "c", ".rs": "c",
    ".js": "js", ".mjs": "js", ".ts": "js", ".jsx": "js", ".json": "json",
    ".py": "python", ".rb": "ruby", ".gemspec": "ruby",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".lisp": "lisp", ".lsp": "lisp", ".el": "lisp", ".clj": "lisp", ".scm": "lisp"
  };
  function forFilename(name) {
    if (!name) return "text";
    var m = String(name).toLowerCase().match(/(\.[a-z0-9]+)$/);
    return (m && EXT[m[1]]) || "text";
  }
  function spec(lang) { return SPEC[lang] || SPEC.text; }
  function indentWidth(lang) { return spec(lang).indent; }

  function startsWith(chars, i, s) {
    for (var k = 0; k < s.length; k++) if (chars[i + k] !== s[k]) return false;
    return true;
  }
  function mask(source, lang) {
    var sp = spec(lang), lineComments = sp.line_comments || [], blocks = sp.block || [];
    var out = source.split(""), chars = source.split(""), i = 0, state = null, blockClose = null;
    while (i < chars.length) {
      var c = chars[i];
      if (state === "block") {
        if (blockClose && startsWith(chars, i, blockClose)) {
          for (var k = 0; k < blockClose.length; k++) if (chars[i + k] !== "\n") out[i + k] = " ";
          i += blockClose.length; state = null; blockClose = null; continue;
        }
        if (c !== "\n") out[i] = " "; i += 1; continue;
      } else if (state) {
        if (c === "\\") { out[i] = " "; if (chars[i + 1] && chars[i + 1] !== "\n") out[i + 1] = " "; i += 2; continue; }
        if (c === state) { state = null; i += 1; continue; }
        if (c !== "\n") out[i] = " "; i += 1; continue;
      } else {
        var bc = null;
        for (var b = 0; b < blocks.length; b++) if (startsWith(chars, i, blocks[b][0])) { bc = blocks[b]; break; }
        if (bc) { state = "block"; blockClose = bc[1]; i += bc[0].length; continue; }
        var lc = null;
        for (var l = 0; l < lineComments.length; l++) if (startsWith(chars, i, lineComments[l])) { lc = lineComments[l]; break; }
        if (lc) { var j = i; while (j < chars.length && chars[j] !== "\n") j += 1; for (; i < j; i++) out[i] = " "; continue; }
        if (c === '"' || c === "'" || c === "`") { state = c; i += 1; continue; }
        i += 1;
      }
    }
    return out.join("");
  }

  function netParen(masked) {
    var o = (masked.match(/[([{]/g) || []).length;
    var c = (masked.match(/[)\]}]/g) || []).length;
    return o - c;
  }
  function leadingWs(line) { var m = line.match(/^[ \t]*/); return m ? m[0] : ""; }
  function trimTrailing(source) { return splitLines(source).map(function (l) { return l.replace(/\s+$/, ""); }).join("\n"); }

  function popKw(stack) {
    for (var i = stack.length - 1; i >= 0; i--) if (stack[i].kind === "keyword") { stack.splice(i, 1); return; }
  }
  function openStack(source, lang) {
    var sp = spec(lang), masked = mask(source, lang), stack = [], lineno = 1;
    var mlines = masked.split("\n");
    for (var li = 0; li < mlines.length; li++) {
      var mline = mlines[li], stripped = mline.trim();
      for (var idx = 0; idx < mline.length; idx++) {
        var ch = mline[idx];
        if (OPEN[ch]) stack.push({ close: OPEN[ch], kind: "bracket", line: lineno, col: idx + 1, open: ch });
        else if (CLOSE[ch]) {
          var top = stack[stack.length - 1];
          if (top && top.kind === "bracket") stack.pop();
        }
      }
      if (sp.style === "keyword") {
        if (sp.open_kw) {
          if (sp.close_kw.test(stripped)) popKw(stack);
          else if (sp.mid_kw.test(stripped)) { /* no change */ }
          else if (sp.open_kw.test(stripped)) {
            var mm = stripped.match(sp.open_kw);
            stack.push({ close: "end", kind: "keyword", line: lineno, col: 1, open: mm[1] });
          } else if (sp.trailing_do.test(stripped)) {
            stack.push({ close: "end", kind: "keyword", line: lineno, col: 1, open: "do" });
          }
        } else if (sp.pairs) {
          var first = (stripped.match(/^\w+/) || [""])[0];
          if (first === "fi" || first === "esac") popKw(stack);
          else if (sp.pairs[first]) stack.push({ close: sp.pairs[first], kind: "keyword", line: lineno, col: 1, open: first });
          else if (sp.do_done) {
            if (/\bdo\b\s*$/.test(stripped)) stack.push({ close: "done", kind: "keyword", line: lineno, col: 1, open: "do" });
            else if (first === "done") popKw(stack);
          }
        }
      }
      lineno += 1;
    }
    return stack;
  }

  function check(source, lang, filename) {
    if (filename && (!lang || lang === "text")) lang = forFilename(filename);
    lang = lang || "text";
    var base = analyze(source, filename);
    var diags = base.defects.map(function (d) {
      return { line: d.line, col: d.col, kind: d.kind, message: d.message, suggestion: d.suggestion };
    });
    openStack(source, lang).filter(function (e) { return e.kind === "keyword"; }).forEach(function (e) {
      diags.push({ line: e.line, col: e.col, kind: "unclosed_block",
        message: "block '" + e.open + "' opened at line " + e.line + " needs '" + e.close + "'",
        suggestion: "insert '" + e.close + "'" });
    });
    diags.sort(function (a, b) { return (a.line - b.line) || (a.col - b.col); });
    return { filename: filename || null, lang: lang, ok: diags.length === 0,
             winding: base.winding, diagnostics: diags,
             certified_invariant: base.certified_invariant, invariant_conserved: base.invariant_conserved };
  }

  function complete(before, lang, filename, width) {
    if (filename && (!lang || lang === "text")) lang = forFilename(filename);
    lang = lang || "text";
    width = width || indentWidth(lang);
    var stack = openStack(before, lang);
    var candidates = stack.slice().reverse().map(function (e) { return e.close; });
    var top = stack[stack.length - 1], suggestion = null;
    if (!top) {
      var lines = before.split("\n"), last = null;
      for (var i = lines.length - 1; i >= 0; i--) if (lines[i].trim() !== "") { last = lines[i]; break; }
      if (last && spec(lang).style === "colon" && mask(last, lang).replace(/\s+$/, "").slice(-1) === ":") {
        suggestion = { type: "indent", text: leadingWs(last) + " ".repeat(width), newline: true };
      }
    } else if (top.kind === "bracket") {
      suggestion = { type: "bracket", text: top.close, newline: false };
    } else {
      var opener = (before.split("\n")[top.line - 1]) || "";
      suggestion = { type: "keyword", text: top.close, newline: true, indent: leadingWs(opener) };
    }
    return { candidates: candidates, suggestion: suggestion, stack_depth: stack.length };
  }

  function opensKeyword(stripped, lang) {
    var sp = spec(lang);
    if (sp.open_kw) {
      if (sp.close_kw.test(stripped)) return false;
      if (sp.open_kw.test(stripped) && !/\bend\b\s*$/.test(stripped)) return true;
      if (sp.trailing_do.test(stripped)) return true;
      return false;
    } else if (sp.pairs) {
      var first = (stripped.match(/^\w+/) || [""])[0];
      if (sp.pairs[first]) return true;
      if (sp.do_done && /\bdo\b\s*$/.test(stripped)) return true;
      return false;
    }
    return false;
  }
  function indentForNewLine(lines, row, lang, filename, width) {
    if (filename && (!lang || lang === "text")) lang = forFilename(filename);
    lang = lang || "text";
    width = width || indentWidth(lang);
    var cur = lines[row] || "", base = leadingWs(cur);
    var masked = mask(cur, lang).trim(), st = spec(lang).style, opens = false;
    if (st === "brace" || st === "text") opens = /[{([]$/.test(masked);
    else if (st === "colon") opens = masked.slice(-1) === ":";
    else if (st === "paren") opens = netParen(mask(cur, lang)) > 0;
    else if (st === "keyword") opens = opensKeyword(masked, lang);
    return opens ? base + " ".repeat(width) : base;
  }

  function leadingDedent(stripped, lang) {
    var sp = spec(lang), d = 0;
    for (var i = 0; i < stripped.length; i++) {
      var ch = stripped[i];
      if (")]}".indexOf(ch) >= 0) d += 1;
      else if (ch === " " || ch === "\t") continue;
      else break;
    }
    if (sp.style === "keyword") {
      if (sp.open_kw && (sp.close_kw.test(stripped) || sp.mid_kw.test(stripped))) d += 1;
      else if (sp.pairs) {
        var first = (stripped.match(/^\w+/) || [""])[0];
        if (["fi", "esac", "done", "else", "elif"].indexOf(first) >= 0) d += 1;
      }
    }
    return d;
  }
  function netUnits(masked, lang) {
    var sp = spec(lang), n = netParen(masked);
    if (sp.style === "keyword") {
      var st = masked.trim();
      if (sp.open_kw) {
        if (sp.close_kw.test(st)) n -= 1;
        else if (sp.mid_kw.test(st)) n += 0;
        else if (sp.open_kw.test(st)) n += 1;
        else if (sp.trailing_do.test(st)) n += 1;
      } else if (sp.pairs) {
        var first = (st.match(/^\w+/) || [""])[0];
        if (first === "fi" || first === "esac" || first === "done") n -= 1;
        else if (sp.pairs[first]) n += 1;
        else if (sp.do_done && /\bdo\b\s*$/.test(st)) n += 1;
      }
    }
    return n;
  }
  function reindent(source, lang, filename, width) {
    if (filename && (!lang || lang === "text")) lang = forFilename(filename);
    lang = lang || "text";
    width = width || indentWidth(lang);
    if (spec(lang).style === "colon") return trimTrailing(source);
    var raw = source.split("\n"), masked = mask(source, lang).split("\n"), out = [], depth = 0;
    for (var i = 0; i < raw.length; i++) {
      var ml = masked[i] || "", s = ml.trim(), content = raw[i].trim();
      var dedent = leadingDedent(s, lang), level = Math.max(depth - dedent, 0);
      out.push(content === "" ? "" : " ".repeat(width * level) + content);
      depth += netUnits(ml, lang);
      if (depth < 0) depth = 0;
    }
    return out.join("\n");
  }

  // ---- exports ------------------------------------------------------------
  root.OmegaEngine = {
    Special: { gamma: gamma, beta: beta, xLogX: xLogX, zetaGauge: zetaGauge },
    Entropy: { tokenize: tokenize, shannon: shannon, distribution: distribution },
    Manifold: { element: element, integral: integral, invariant: invariant, xi: xi },
    ErrorCorrection: { lorentz: lorentz, rotate: rotate, orbitAverage: orbitAverage, correct: correct, certifyInvariant: certifyInvariant },
    CodeFix: { scan: scan, analyze: analyze, fix: fix, closeOrbit: closeOrbit },
    Grammar: {
      forFilename: forFilename, indentWidth: indentWidth, spec: spec, mask: mask,
      openStack: openStack, check: check, complete: complete, reindent: reindent,
      indentForNewLine: indentForNewLine
    }
  };
  if (typeof module !== "undefined" && module.exports) module.exports = root.OmegaEngine;
})(typeof window !== "undefined" ? window : this);
