/* omega-editor.js — the GUI front-end for Ω-Vim.
 *
 * Drives a <textarea> as a code editor with:
 *   - the four Bada features as buttons AND keys:
 *       ∮ Fix      (fix + indent)           — closes the rotation orbit
 *       Check      grammar checker          — delimiters + block keywords
 *       ▸ Complete parser completion (Tab)  — expected next token
 *       ⇥ Indent   indent completion        — reindent from parse depth
 *   - auto-indent on Enter, Tab parser-completion, line-number gutter
 *   - an optional vim modal-keys layer (Normal / Insert / Command)
 * Everything runs in-page via window.OmegaEngine — no server, no Ruby.
 */
(function () {
  "use strict";
  var E = window.OmegaEngine;
  var G = E.Grammar, CF = E.CodeFix;

  var code = document.getElementById("code");
  var gutter = document.getElementById("gutter");
  var statusEl = document.getElementById("status");
  var langSel = document.getElementById("lang");
  var modeBadge = document.getElementById("modeBadge");
  var cmdline = document.getElementById("cmdline");
  var diag = document.getElementById("diag");
  var diagList = document.getElementById("diagList");

  var filename = "buffer.txt";
  var vimOn = false;
  var mode = "insert";     // when vimOn: normal | insert | command
  var command = "";
  var pending = "";

  // ---- helpers -----------------------------------------------------------
  function lang() {
    var v = langSel.value;
    return v === "auto" ? G.forFilename(filename) : v;
  }
  function width() { return G.indentWidth(lang()); }

  function setStatus(html) { statusEl.innerHTML = html; }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }

  function renderGutter() {
    var n = code.value.split("\n").length;
    var buf = [];
    for (var i = 1; i <= n; i++) buf.push(i);
    gutter.textContent = buf.join("\n");
    gutter.scrollTop = code.scrollTop;
  }

  // cursor helpers on the textarea
  function pos() { return code.selectionStart; }
  function setPos(p) { code.selectionStart = code.selectionEnd = p; }
  function textBeforeCursor() { return code.value.slice(0, pos()); }
  function curLineInfo() {
    var v = code.value, p = pos();
    var start = v.lastIndexOf("\n", p - 1) + 1;
    var end = v.indexOf("\n", p); if (end < 0) end = v.length;
    return { start: start, end: end, col: p - start, line: v.slice(start, end) };
  }

  // ---- the four features -------------------------------------------------
  function doFix() {
    var r = CF.fix(code.value, filename);
    var reflowed = r.source;
    var indented = false;
    if (G.spec(lang()).style !== "colon") {
      var ri = G.reindent(reflowed, lang(), filename, width());
      if (ri !== reflowed) { reflowed = ri; indented = true; }
    }
    if (r.changed || indented) {
      var p = pos();
      code.value = reflowed;
      setPos(Math.min(p, code.value.length));
      afterChange();
      var cons = r.invariant_conserved ? '<span class="ok">conserved</span>' : '<span class="bad">DRIFT</span>';
      setStatus("∮ orbit closed · " + r.applied.length + " fix(es)" + (indented ? " + indent" : "") +
        " · Ξ " + cons + " (" + r.certified_invariant.toFixed(4) + ") · residual " +
        r.report.rotation_residual.toExponential(2));
    } else {
      setStatus(r.report.orbit_closed ? "∮ orbit already closed — no structural errors" :
        "no automatic fix found (winding=" + r.report.winding + ")");
    }
  }

  function doCheck() {
    var chk = G.check(code.value, lang(), filename);
    if (chk.ok) {
      diag.classList.remove("show");
      setStatus('<span class="ok">✓ grammar OK</span> [' + chk.lang + "] — orbit closed, Ξ " +
        chk.certified_invariant.toFixed(4));
    } else {
      var items = chk.diagnostics.map(function (d) {
        return '<li data-line="' + d.line + '" data-col="' + d.col + '">' +
          '<span class="loc">' + d.line + ":" + d.col + '</span> ' +
          '<span class="kind">[' + d.kind + "]</span> " + esc(d.message) +
          ' — <span style="color:var(--dim)">' + esc(d.suggestion || "") + "</span></li>";
      }).join("");
      diagList.innerHTML = items;
      diag.classList.add("show");
      setStatus('<span class="bad">✗ ' + chk.diagnostics.length + " issue(s)</span> [" + chk.lang +
        "]  " + esc(chk.diagnostics[0].message));
    }
  }

  function doComplete() {
    var res = G.complete(textBeforeCursor(), lang(), filename, width());
    if (!res.suggestion) {
      setStatus(res.candidates.length ? "parser expects: " + res.candidates.join(" ") :
        "parser: nothing open (orbit closed)");
      return;
    }
    var s = res.suggestion;
    if (s.type === "bracket") {
      insertAtCursor(s.text);
    } else if (s.type === "indent") {
      insertAtCursor(s.text);
    } else if (s.type === "keyword") {
      var li = curLineInfo();
      insertAtCursor("\n" + (s.indent || "") + s.text);
    }
    afterChange();
    setStatus('<span class="k">▸ parser completion</span> → ' + (res.candidates.join(" ") || s.text));
  }

  function doIndent() {
    var before = code.value;
    var after = G.reindent(before, lang(), filename, width());
    if (after !== before) {
      var p = pos(); code.value = after; setPos(Math.min(p, after.length)); afterChange();
      setStatus("⇥ indent completed (" + lang() + ", width " + width() + ")");
    } else {
      setStatus("indentation already normal (" + lang() + ")");
    }
  }

  function insertAtCursor(str) {
    var p = pos(), v = code.value;
    code.value = v.slice(0, p) + str + v.slice(p);
    setPos(p + str.length);
  }

  function afterChange() { renderGutter(); }

  // ---- auto-indent on Enter, Tab completion ------------------------------
  function autoIndentNewline() {
    var li = curLineInfo();
    var lines = code.value.slice(0, li.end).split("\n");
    var rowIdx = lines.length - 1;
    var ind = G.indentForNewLine(code.value.split("\n"), rowIdx, lang(), filename, width());
    insertAtCursor("\n" + ind);
    afterChange();
  }

  // ---- key handling ------------------------------------------------------
  code.addEventListener("keydown", function (ev) {
    if (vimOn) { vimKeydown(ev); if (ev.defaultPrevented) return; }
    if (vimOn && mode !== "insert") return;

    if (ev.key === "Tab") {
      ev.preventDefault();
      doComplete();
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      autoIndentNewline();
    }
  });

  code.addEventListener("input", afterChange);
  code.addEventListener("scroll", function () { gutter.scrollTop = code.scrollTop; });
  code.addEventListener("click", updateModeBadge);
  code.addEventListener("keyup", updateModeBadge);

  // ---- optional vim modal layer ------------------------------------------
  function setMode(m) { mode = m; updateModeBadge(); }
  function updateModeBadge() {
    if (!vimOn) { modeBadge.className = "mode off"; return; }
    modeBadge.className = "mode " + mode;
    modeBadge.textContent = mode.toUpperCase();
  }

  function lineBounds(p) {
    var v = code.value;
    var start = v.lastIndexOf("\n", p - 1) + 1;
    var end = v.indexOf("\n", p); if (end < 0) end = v.length;
    return [start, end];
  }
  function deleteCurrentLine() {
    var v = code.value, p = pos(), b = lineBounds(p);
    var delEnd = b[1] < v.length ? b[1] + 1 : b[1];
    code.value = v.slice(0, b[0]) + v.slice(delEnd);
    setPos(Math.min(b[0], code.value.length));
    afterChange();
  }

  function vimKeydown(ev) {
    if (ev.key === "Escape") {
      ev.preventDefault();
      if (mode === "command") { cmdline.classList.remove("show"); command = ""; }
      setMode("normal"); return;
    }
    if (mode === "insert") return;               // let normal typing through
    if (mode === "command") {
      ev.preventDefault();
      if (ev.key === "Enter") { runExCommand(command); command = ""; cmdline.classList.remove("show"); if (mode === "command") setMode("normal"); }
      else if (ev.key === "Backspace") { command = command.slice(0, -1); cmdline.textContent = ":" + command; if (!command) { cmdline.classList.remove("show"); setMode("normal"); } }
      else if (ev.key.length === 1) { command += ev.key; cmdline.textContent = ":" + command; }
      return;
    }
    // normal mode
    ev.preventDefault();
    var key = ev.key, combo = pending + key; pending = "";
    var v = code.value, p = pos(), b = lineBounds(p);
    switch (combo) {
      case "h": setPos(Math.max(p - 1, b[0])); break;
      case "l": setPos(Math.min(p + 1, b[1])); break;
      case "j": moveLine(1); break;
      case "k": moveLine(-1); break;
      case "0": setPos(b[0]); break;
      case "$": setPos(b[1]); break;
      case "G": setPos(v.length); break;
      case "g": pending = "g"; return;
      case "gg": setPos(0); break;
      case "x": if (p < b[1]) { code.value = v.slice(0, p) + v.slice(p + 1); setPos(p); afterChange(); } break;
      case "d": pending = "d"; return;
      case "dd": deleteCurrentLine(); break;
      case "i": setMode("insert"); break;
      case "a": setPos(Math.min(p + 1, b[1])); setMode("insert"); break;
      case "A": setPos(b[1]); setMode("insert"); break;
      case "o": setPos(b[1]); autoIndentNewline(); setMode("insert"); break;
      case "O": setPos(b[0]); insertAtCursor("\n"); setPos(b[0]); afterChange(); setMode("insert"); break;
      case ":": mode = "command"; command = ""; cmdline.textContent = ":"; cmdline.classList.add("show"); updateModeBadge(); break;
      case "=": doFix(); break;
      case "\t": doIndent(); break;
      default: break;
    }
    updateModeBadge();
  }

  function moveLine(dir) {
    var v = code.value, p = pos(), b = lineBounds(p), col = p - b[0];
    if (dir > 0) {
      if (b[1] >= v.length) return;
      var ns = b[1] + 1, ne = v.indexOf("\n", ns); if (ne < 0) ne = v.length;
      setPos(Math.min(ns + col, ne));
    } else {
      if (b[0] === 0) return;
      var pe = b[0] - 1, ps = v.lastIndexOf("\n", pe - 1) + 1;
      setPos(Math.min(ps + col, pe));
    }
  }

  function runExCommand(cmd) {
    cmd = cmd.trim();
    if (cmd === "w") { doSave(); }
    else if (cmd === "q" || cmd === "q!") { setStatus("(in the app, use Open/Save; :q is a no-op)"); }
    else if (cmd === "wq" || cmd === "x") { doSave(); }
    else if (cmd === "fix" || cmd === "correct") { doFix(); }
    else if (cmd === "check" || cmd === "grammar") { doCheck(); }
    else if (cmd === "indent" || cmd === "reindent") { doIndent(); }
    else if (cmd === "complete") { doComplete(); }
    else if (/^set\s+ft\s*=\s*(\w+)$/.test(cmd)) { langSel.value = RegExp.$1; setStatus("filetype = " + RegExp.$1); }
    else if (cmd === "help") { setStatus("hjkl move · i/a/o insert · x/dd delete · = fix · Tab indent · :w :fix :check :indent"); }
    else { setStatus("not an editor command: " + cmd); }
  }

  // ---- file open / save --------------------------------------------------
  function doSave() {
    // Desktop / modern browsers: trigger a real download.
    var downloaded = false;
    try {
      var blob = new Blob([code.value], { type: "text/plain" });
      var a = document.createElement("a");
      if (typeof a.download !== "undefined") {
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        document.body.appendChild(a); a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 0);
        downloaded = true;
      }
    } catch (e) { downloaded = false; }

    // Android WebView (Cordova) often blocks blob downloads — fall back to the
    // clipboard so the user can paste into their target app.
    var inWebView = !!(window.cordova || window._cordovaNative ||
      /; wv\)/.test(navigator.userAgent) || /Android/.test(navigator.userAgent));
    if (!downloaded || inWebView) {
      var copied = false;
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(code.value); copied = true;
        } else {
          code.focus(); code.select();
          copied = document.execCommand && document.execCommand("copy");
          setPos(pos());
        }
      } catch (e2) { copied = false; }
      setStatus(copied ? "copied to clipboard (" + filename + ") — paste into your target app" :
        (downloaded ? "saved (downloaded): " + filename :
         "select-all is active — long-press to copy the text"));
      return;
    }
    setStatus("saved (downloaded): " + filename);
  }

  document.getElementById("file").addEventListener("change", function (ev) {
    var f = ev.target.files[0]; if (!f) return;
    filename = f.name;
    var rd = new FileReader();
    rd.onload = function () { code.value = rd.result; afterChange(); setStatus("opened: " + filename + " [" + G.forFilename(filename) + "]"); };
    rd.readAsText(f);
  });
  document.getElementById("btnOpen").addEventListener("click", function () { document.getElementById("file").click(); });
  document.getElementById("btnSave").addEventListener("click", doSave);

  document.getElementById("btnFix").addEventListener("click", doFix);
  document.getElementById("btnCheck").addEventListener("click", doCheck);
  document.getElementById("btnComplete").addEventListener("click", doComplete);
  document.getElementById("btnIndent").addEventListener("click", doIndent);
  document.getElementById("btnVim").addEventListener("click", function () {
    vimOn = !vimOn;
    this.className = vimOn ? "on" : "gho";
    this.textContent = "vim: " + (vimOn ? "on" : "off");
    setMode(vimOn ? "normal" : "insert");
    setStatus(vimOn ? "vim modal keys ON — Esc=normal, i/a/o insert, hjkl, x/dd, := fix, :cmd" :
      "vim modal keys off — plain editing (Tab completes, Enter auto-indents)");
  });

  diagList.addEventListener("click", function (ev) {
    var li = ev.target.closest("li"); if (!li) return;
    var line = parseInt(li.getAttribute("data-line"), 10) || 1;
    var lines = code.value.split("\n");
    var p = 0; for (var i = 0; i < line - 1 && i < lines.length; i++) p += lines[i].length + 1;
    code.focus(); setPos(p);
  });

  langSel.addEventListener("change", function () {
    setStatus("language: " + lang() + " (indent width " + width() + ")");
  });

  // ---- sample ------------------------------------------------------------
  var SAMPLE = [
    "// Ω-Vim sample — press ∮ Fix (close the orbit + indent), then Check.",
    "// This C snippet is missing the final brace and is mis-indented.",
    "int add(int a, int b) {",
    "return a + b;",
    "}",
    "",
    "int main(void) {",
    "int s = add(2, 3);",
    "printf(\"%d\\n\", s);",
    "return 0;"
  ].join("\n");
  document.getElementById("btnSample").addEventListener("click", function () {
    filename = "sample.c"; langSel.value = "auto";
    code.value = SAMPLE; afterChange();
    setStatus("loaded sample.c — press ∮ Fix to close the orbit and indent.");
  });

  // ---- init --------------------------------------------------------------
  code.value = SAMPLE; filename = "sample.c";
  renderGutter(); updateModeBadge();
})();
