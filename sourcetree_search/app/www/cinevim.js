/*
 * cinevim.js — BadaCineVim: Bada Search 付属の「シネマ風」Vim スタイル
 *              コード/論文ビューア兼エディタ (依存ゼロの純 JS)
 *
 * 黒い大画面に合うモーダル Vim エディタ。検索ヒットからファイルを開いて
 * 該当行へジャンプし、Vim のキーバインドで閲覧・編集できます。
 *   NORMAL : h j k l / 0 $ ^ / w b / gg G / x dd / yy p P / u Ctrl-r /
 *            i a A I o O / Ctrl-d Ctrl-u / n N
 *   INSERT : 文字入力 / Enter 改行 / Backspace / Esc で NORMAL へ
 *   COMMAND: ":" と "/" — :w 保存  :q 閉じる (未保存なら :q!)  :wq 保存して閉じる
 *            :<行> 移動  /<語> 検索 (n/N で次/前)
 *
 * エンジン (createEditor / feed) は Node からも require でき、UI 層とは独立に
 * 単体テストできます。UI 層 (BadaCineVim.open) はブラウザ/Electron 専用。
 *
 * ※ :w の保存はオプションの onSave コールバック経由 (EXE はその場に上書き、
 *   ブラウザ/APK はフォルダへ書き戻し or 端末に保存)。PDF は pdfview.js の
 *   ページ表示で注釈編集し、抽出テキスト側は readonly で開きます。
 */
(function (global) {
  "use strict";

  /* ───────────────────────── エンジン (純粋ロジック) ───────────────────────── */
  function createEditor(lines, opts) {
    opts = opts || {};
    var ls = (lines && lines.length) ? lines.slice() : [""];
    return {
      lines: ls,
      cx: 0, cy: 0,
      mode: "normal",            /* normal | insert | command */
      pending: "",               /* g / d 等の 2 ストローク待ち */
      cmd: "",                   /* コマンドライン (":" or "/" 始まり) */
      lastSearch: opts.search || "",
      status: "",
      dirty: false,
      readonly: !!opts.readonly,
      undo: [], redo: [],        /* u / Ctrl-r 用のスナップショット */
      reg: null                  /* yy / dd で取り込んだ行 (p / P で貼り付け) */
    };
  }

  /* ── undo / redo (行配列のスナップショット方式。挿入モード 1 回 = 1 単位) ── */
  var MAX_UNDO = 300;
  function shot(ed) { return { lines: ed.lines.slice(), cx: ed.cx, cy: ed.cy }; }
  function sameLines(a, b) {
    if (a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }
  function snap(ed) {
    ed.undo.push(shot(ed));
    if (ed.undo.length > MAX_UNDO) ed.undo.shift();
    ed.redo = [];
  }
  function restore(ed, s) { ed.lines = s.lines.slice(); ed.cx = s.cx; ed.cy = s.cy; ed.dirty = true; clamp(ed); }
  function undo(ed) {
    if (!ed.undo.length) { ed.status = "これ以上戻せません"; return; }
    ed.redo.push(shot(ed)); restore(ed, ed.undo.pop()); ed.status = "元に戻しました";
  }
  function redo(ed) {
    if (!ed.redo.length) { ed.status = "やり直す変更がありません"; return; }
    ed.undo.push(shot(ed)); restore(ed, ed.redo.pop()); ed.status = "やり直しました";
  }
  function pasteLine(ed, below) {
    if (ed.reg == null) { ed.status = "貼り付ける行がありません (yy でヤンク)"; return; }
    snap(ed);
    var at = below ? ed.cy + 1 : ed.cy;
    ed.lines.splice(at, 0, ed.reg);
    ed.cy = at; ed.cx = firstNonBlank(ed.reg); ed.dirty = true; clamp(ed);
  }

  function isWord(c) { return /[A-Za-z0-9_]/.test(c); }
  function curLine(ed) { return ed.lines[ed.cy] != null ? ed.lines[ed.cy] : ""; }
  function clampY(ed) { if (ed.cy < 0) ed.cy = 0; if (ed.cy > ed.lines.length - 1) ed.cy = ed.lines.length - 1; }
  function clampX(ed) {
    var max = curLine(ed).length - (ed.mode === "insert" ? 0 : 1);
    if (max < 0) max = 0;
    if (ed.cx < 0) ed.cx = 0;
    if (ed.cx > max) ed.cx = max;
  }
  function clamp(ed) { clampY(ed); clampX(ed); }

  function firstNonBlank(line) { var m = line.match(/\S/); return m ? line.indexOf(m[0]) : 0; }

  function wordForward(ed) {
    var line = curLine(ed), i = ed.cx, n = line.length;
    if (i >= n - 1) { if (ed.cy < ed.lines.length - 1) { ed.cy++; ed.cx = 0; clamp(ed); } return; }
    var inW = isWord(line[i]);
    while (i < n && isWord(line[i]) === inW && line[i] !== " ") i++;
    while (i < n && line[i] === " ") i++;
    if (i >= n && ed.cy < ed.lines.length - 1) { ed.cy++; ed.cx = 0; } else ed.cx = i;
    clamp(ed);
  }
  function wordBack(ed) {
    var line = curLine(ed), i = ed.cx;
    if (i <= 0) { if (ed.cy > 0) { ed.cy--; ed.cx = curLine(ed).length; clampX(ed); } return; }
    i--;
    while (i > 0 && line[i] === " ") i--;
    while (i > 0 && isWord(line[i - 1])) i--;
    ed.cx = i; clamp(ed);
  }

  function insertChar(ed, ch) {
    var l = curLine(ed);
    ed.lines[ed.cy] = l.slice(0, ed.cx) + ch + l.slice(ed.cx);
    ed.cx += ch.length; ed.dirty = true;
  }
  function splitLine(ed) {
    var l = curLine(ed), left = l.slice(0, ed.cx), right = l.slice(ed.cx);
    ed.lines.splice(ed.cy, 1, left, right);
    ed.cy++; ed.cx = 0; ed.dirty = true;
  }
  function backspace(ed) {
    if (ed.cx > 0) { var l = curLine(ed); ed.lines[ed.cy] = l.slice(0, ed.cx - 1) + l.slice(ed.cx); ed.cx--; ed.dirty = true; }
    else if (ed.cy > 0) {
      var prev = ed.lines[ed.cy - 1], cur = curLine(ed);
      ed.cx = prev.length; ed.lines[ed.cy - 1] = prev + cur;
      ed.lines.splice(ed.cy, 1); ed.cy--; ed.dirty = true;
    }
  }
  function deleteChar(ed) {
    var l = curLine(ed);
    if (l.length) { ed.lines[ed.cy] = l.slice(0, ed.cx) + l.slice(ed.cx + 1); ed.dirty = true; clampX(ed); }
  }
  function deleteLine(ed) {
    ed.lines.splice(ed.cy, 1);
    if (!ed.lines.length) ed.lines = [""];
    ed.dirty = true; clamp(ed);
  }
  function openLine(ed, below) {
    var indent = curLine(ed).match(/^\s*/)[0];
    if (below) { ed.lines.splice(ed.cy + 1, 0, indent); ed.cy++; }
    else { ed.lines.splice(ed.cy, 0, indent); }
    ed.cx = indent.length; ed.mode = "insert"; ed.dirty = true;
  }

  function search(ed, pat, dir) {
    if (!pat) return false;
    var n = ed.lines.length, low = pat.toLowerCase();
    for (var step = 1; step <= n; step++) {
      var y = ((ed.cy + dir * step) % n + n) % n;
      var idx = ed.lines[y].toLowerCase().indexOf(low);
      if (idx >= 0) { ed.cy = y; ed.cx = idx; clamp(ed); return true; }
    }
    /* 同じ行の現在位置より先も一応みる */
    return false;
  }

  function execEx(ed, raw) {
    var cmd = raw.slice(1);                 /* ":" を除く */
    if (cmd === "w") return ed.readonly ? sig("readonly", "読み取り専用 (保存不可)") : sig("save");
    if (cmd === "q") return ed.dirty ? sig("dirty", "未保存の変更があります (:w で保存 / :q! で破棄)") : sig("close");
    if (cmd === "q!") return sig("close");
    if (cmd === "wq" || cmd === "x") return ed.readonly ? sig("close") : sig("savequit");
    if (/^\d+$/.test(cmd)) { ed.cy = Math.max(0, Math.min(ed.lines.length - 1, parseInt(cmd, 10) - 1)); ed.cx = 0; clamp(ed); return sig("goto"); }
    return sig("unknown", "未対応のコマンド: :" + cmd);
    function sig(type, msg) { return { type: type, message: msg || "" }; }
  }

  /* 1 キー入力を処理。key は正規化済みトークン:
     1 文字 / "Esc" "Enter" "Backspace" "Left" "Right" "Up" "Down" "Ctrl-d" "Ctrl-u"
     戻り値: null か {type: "save"|"close"|"savequit"|...} のシグナル */
  function feed(ed, key) {
    ed.status = "";
    if (ed.mode === "insert") return feedInsert(ed, key);
    if (ed.mode === "command") return feedCommand(ed, key);
    return feedNormal(ed, key);
  }

  function feedInsert(ed, key) {
    if (key === "Esc") {
      ed.mode = "normal"; ed.cx--; clampX(ed);
      /* 何も打たずに抜けた挿入は undo 履歴に残さない */
      var top = ed.undo[ed.undo.length - 1];
      if (top && sameLines(top.lines, ed.lines)) ed.undo.pop();
      return null;
    }
    if (key === "Enter") { splitLine(ed); return null; }
    if (key === "Backspace") { backspace(ed); return null; }
    if (key === "Left") { ed.cx--; clampX(ed); return null; }
    if (key === "Right") { ed.cx++; clampX(ed); return null; }
    if (key === "Up") { ed.cy--; clamp(ed); return null; }
    if (key === "Down") { ed.cy++; clamp(ed); return null; }
    if (key.length === 1) { insertChar(ed, key); return null; }
    return null;
  }

  function feedCommand(ed, key) {
    if (key === "Esc") { ed.mode = "normal"; ed.cmd = ""; return null; }
    if (key === "Backspace") {
      ed.cmd = ed.cmd.slice(0, -1);
      if (!ed.cmd) ed.mode = "normal";
      return null;
    }
    if (key === "Enter") {
      var line = ed.cmd; ed.cmd = ""; ed.mode = "normal";
      if (line[0] === "/") {
        ed.lastSearch = line.slice(1);
        var ok = search(ed, ed.lastSearch, 1);
        ed.status = ok ? ("/" + ed.lastSearch) : ("見つかりません: " + ed.lastSearch);
        return { type: "search", message: ed.status };
      }
      if (line[0] === ":") {
        var s = execEx(ed, line);
        ed.status = s.message || "";
        return s;
      }
      return null;
    }
    if (key.length === 1) { ed.cmd += key; return null; }
    return null;
  }

  function feedNormal(ed, key) {
    /* 2 ストローク待ち (g, d) */
    if (ed.pending === "g") { ed.pending = ""; if (key === "g") { ed.cy = 0; ed.cx = 0; clamp(ed); return null; } }
    if (ed.pending === "d") { ed.pending = ""; if (key === "d") { snap(ed); ed.reg = curLine(ed); deleteLine(ed); return null; } }
    if (ed.pending === "y") { ed.pending = ""; if (key === "y") { ed.reg = curLine(ed); ed.status = "1 行ヤンクしました"; return null; } }

    switch (key) {
      case "h": case "Left": ed.cx--; clampX(ed); return null;
      case "l": case "Right": ed.cx++; clampX(ed); return null;
      case "j": case "Down": ed.cy++; clamp(ed); return null;
      case "k": case "Up": ed.cy--; clamp(ed); return null;
      case "0": ed.cx = 0; return null;
      case "$": ed.cx = Math.max(0, curLine(ed).length - 1); return null;
      case "^": ed.cx = firstNonBlank(curLine(ed)); clampX(ed); return null;
      case "w": wordForward(ed); return null;
      case "b": wordBack(ed); return null;
      case "G": ed.cy = ed.lines.length - 1; ed.cx = 0; clamp(ed); return null;
      case "g": ed.pending = "g"; return null;
      case "d": if (ed.readonly) { ed.status = "読み取り専用"; return null; } ed.pending = "d"; return null;
      case "x": if (ed.readonly) { ed.status = "読み取り専用"; return null; } if (curLine(ed).length) snap(ed); deleteChar(ed); return null;
      case "y": ed.pending = "y"; return null;
      case "p": if (chk(ed)) return null; pasteLine(ed, true); return null;
      case "P": if (chk(ed)) return null; pasteLine(ed, false); return null;
      case "u": if (chk(ed)) return null; undo(ed); return null;
      case "Ctrl-r": if (chk(ed)) return null; redo(ed); return null;
      case "i": if (chk(ed)) return null; snap(ed); ed.mode = "insert"; return null;
      case "a": if (chk(ed)) return null; snap(ed); ed.cx++; clampForInsert(ed); ed.mode = "insert"; return null;
      case "A": if (chk(ed)) return null; snap(ed); ed.cx = curLine(ed).length; ed.mode = "insert"; return null;
      case "I": if (chk(ed)) return null; snap(ed); ed.cx = firstNonBlank(curLine(ed)); ed.mode = "insert"; return null;
      case "o": if (chk(ed)) return null; snap(ed); openLine(ed, true); return null;
      case "O": if (chk(ed)) return null; snap(ed); openLine(ed, false); return null;
      case "/": ed.mode = "command"; ed.cmd = "/"; return null;
      case ":": ed.mode = "command"; ed.cmd = ":"; return null;
      case "n": { var a = search(ed, ed.lastSearch, 1); ed.status = a ? ("/" + ed.lastSearch) : "見つかりません"; return null; }
      case "N": { var c = search(ed, ed.lastSearch, -1); ed.status = c ? ("?" + ed.lastSearch) : "見つかりません"; return null; }
      case "Ctrl-d": ed.cy = Math.min(ed.lines.length - 1, ed.cy + 10); clamp(ed); return null;
      case "Ctrl-u": ed.cy = Math.max(0, ed.cy - 10); clamp(ed); return null;
      default: return null;
    }
    function chk(e) { if (e.readonly) { e.status = e.readonlyHint || "読み取り専用 (編集不可)"; return true; } return false; }
    function clampForInsert(e) { if (e.cx > curLine(e).length) e.cx = curLine(e).length; }
  }

  /* まとまった文字列の入力 (IME の確定文字列・貼り付け・ソフトキーボード)。
     挿入モードでは本文へ (改行は行分割)、コマンドモードではコマンドラインへ入れる。
     NORMAL モードでは何もしない (貼り付けた文章がコマンドとして実行されるのを防ぐ)。 */
  function typeText(ed, text) {
    text = String(text == null ? "" : text).replace(/\r\n?/g, "\n");
    if (!text) return false;
    ed.status = "";
    if (ed.mode === "insert") {
      if (ed.readonly) return false;
      var parts = text.split("\n");
      for (var i = 0; i < parts.length; i++) {
        if (i > 0) splitLine(ed);
        if (parts[i]) insertChar(ed, parts[i]);
      }
      return true;
    }
    if (ed.mode === "command") { ed.cmd += text.split("\n")[0]; return true; }
    return false;
  }

  var engine = {
    createEditor: createEditor,
    feed: feed,
    search: search,
    _internal: { wordForward: wordForward, wordBack: wordBack, deleteLine: deleteLine, execEx: execEx, undo: undo, redo: redo }
  };

  /* ───────────────────────── UI 層 (ブラウザ/Electron) ───────────────────────── */
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  function open(optsU) {
    optsU = optsU || {};
    if (typeof document === "undefined") return null;
    var ed = createEditor(optsU.lines || [""], { readonly: optsU.readonly, search: optsU.search || "" });
    if (optsU.readonlyHint) ed.readonlyHint = optsU.readonlyHint;
    if (optsU.gotoLine) { ed.cy = Math.max(0, Math.min(ed.lines.length - 1, (optsU.gotoLine | 0) - 1)); }
    if (optsU.search) { ed.cx = Math.max(0, curLine(ed).toLowerCase().indexOf(String(optsU.search).toLowerCase())); clampX(ed); }

    var ov = document.createElement("div");
    ov.className = "cinevim-overlay";
    ov.setAttribute("role", "dialog");
    ov.innerHTML =
      '<div class="cv-frame">' +
        '<div class="cv-bar cv-top"><span class="cv-name"></span>' +
          '<span class="cv-flag"></span><span class="cv-acts"></span><span class="cv-grow"></span>' +
          '<span class="cv-hint">h j k l 移動 · i 挿入 · u 取消 · yy/p 複写 · /語 検索 · :w 保存 · :q 閉じる</span>' +
          '<button class="cv-x" title="閉じる (:q)">✕</button></div>' +
        '<div class="cv-body"><div class="cv-gutter"></div><pre class="cv-text"></pre></div>' +
        '<textarea class="cv-ime" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="BadaCineVim 入力"></textarea>' +
        '<div class="cv-bar cv-status"><span class="cv-mode"></span><span class="cv-msg"></span>' +
          '<span class="cv-grow"></span><span class="cv-pos"></span><span class="cv-cmd"></span></div>' +
      '</div>';
    document.body.appendChild(ov);
    ensureStyle();

    var elName = ov.querySelector(".cv-name"), elFlag = ov.querySelector(".cv-flag"),
        elGutter = ov.querySelector(".cv-gutter"), elText = ov.querySelector(".cv-text"),
        elMode = ov.querySelector(".cv-mode"), elMsg = ov.querySelector(".cv-msg"),
        elPos = ov.querySelector(".cv-pos"), elCmd = ov.querySelector(".cv-cmd");
    elName.textContent = "🎬 " + (optsU.name || "untitled") + (optsU.lang ? "  [" + optsU.lang + "]" : "");
    /* 追加ボタン (例: 「📄 PDF 表示」「📝 .tex を編集」)。onClick には閉じる関数を渡す */
    var elActs = ov.querySelector(".cv-acts");
    (optsU.actions || []).forEach(function (act) {
      var b = document.createElement("button");
      b.className = "cv-act"; b.textContent = act.label; if (act.title) b.title = act.title;
      b.addEventListener("click", function () {
        if (ed.dirty && !confirmDiscard()) return;
        act.onClick({ close: teardown, editor: ed });
      });
      elActs.appendChild(b);
    });
    var closeArmed = false;
    function confirmDiscard() {
      if (closeArmed) return true;
      closeArmed = true; ed.status = "未保存の変更があります — もう一度押すと破棄します (:w で保存)"; render();
      return false;
    }

    function render() {
      elFlag.textContent = (ed.readonly ? " [RO]" : (ed.dirty ? " [+]" : ""));
      var low = (ed.lastSearch || "").toLowerCase();
      var gut = [], body = [];
      for (var y = 0; y < ed.lines.length; y++) {
        gut.push('<div class="cv-ln' + (y === ed.cy ? " cur" : "") + '">' + (y + 1) + "</div>");
        body.push(renderLine(ed.lines[y], y, low));
      }
      elGutter.innerHTML = gut.join("");
      elText.innerHTML = body.join("");
      var modeTxt = ed.mode === "insert" ? "-- 挿入 --" : ed.mode === "command" ? "" : "NORMAL";
      elMode.textContent = modeTxt;
      elMode.className = "cv-mode " + ed.mode;
      elMsg.textContent = ed.status || "";
      elPos.textContent = (ed.cy + 1) + "," + (ed.cx + 1) + "  /" + ed.lines.length;
      elCmd.textContent = ed.mode === "command" ? ed.cmd : "";
      var cur = elText.querySelector(".cv-row.cur");
      if (cur) cur.scrollIntoView({ block: "nearest" });
    }
    function renderLine(line, y, low) {
      var cls = "cv-row" + (y === ed.cy ? " cur" : "");
      var html;
      if (y === ed.cy && ed.mode !== "command") {
        var cx = Math.min(ed.cx, line.length);
        html = esc(line.slice(0, cx)) + '<span class="cv-cursor">' + esc(line.slice(cx, cx + 1) || " ") + "</span>" + esc(line.slice(cx + 1));
      } else {
        html = esc(line) || "&nbsp;";
      }
      if (low) {
        /* 検索語ハイライト (カーソル span を壊さないよう、カーソル行以外のみ素朴置換) */
        if (!(y === ed.cy && ed.mode !== "command")) {
          try {
            var re = new RegExp(low.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
            html = esc(line).replace(re, function (m) { return "\u0001" + m + "\u0002"; });
            html = html.replace(/\u0001/g, '<span class="cv-hit">').replace(/\u0002/g, "</span>") || "&nbsp;";
          } catch (e) {}
        }
      }
      return '<div class="' + cls + '">' + html + "</div>";
    }

    function normalizeKey(e) {
      if (e.ctrlKey && (e.key === "d" || e.key === "u" || e.key === "r")) return "Ctrl-" + e.key;
      if (e.ctrlKey || e.metaKey || e.altKey) return null;
      switch (e.key) {
        case "Escape": return "Esc";
        case "Enter": return "Enter";
        case "Backspace": return "Backspace";
        case "ArrowLeft": return "Left";
        case "ArrowRight": return "Right";
        case "ArrowUp": return "Up";
        case "ArrowDown": return "Down";
        case "Tab": return "\t";
        default: return e.key.length === 1 ? e.key : null;
      }
    }
    /* エンジンが返したシグナル (保存・閉じる等) を処理して再描画 */
    function afterFeed(sig) {
      if (sig) {
        if (sig.type === "save" || sig.type === "savequit") {
          var text = ed.lines.join("\n");
          if (typeof optsU.onSave === "function") {
            Promise.resolve(optsU.onSave(text)).then(function (r) {
              ed.dirty = (r && r.error) ? ed.dirty : false;
              ed.status = (r && r.error) ? ("保存エラー: " + r.error) : ("保存しました" + (r && r.note ? " — " + r.note : ""));
              render();
              if (sig.type === "savequit" && !(r && r.error)) teardown();
            });
          } else { ed.status = "保存ハンドラがありません"; }
        } else if (sig.type === "close") { teardown(); return; }
        else if (sig.type === "readonly" || sig.type === "dirty") { ed.status = sig.message; }
      }
      render();
    }
    function onKey(e) {
      /* 日本語変換 (IME) 中のキーは IME に任せ、確定した文字列を compositionend で受け取る */
      if (e.isComposing || e.keyCode === 229 || composing) return;
      if (e.target && e.target !== ime && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName || "")) return;
      var k = normalizeKey(e);
      if (k == null) return;
      e.preventDefault();                 /* ブラウザの既定動作 (スクロール・検索等) を抑止 */
      e.stopPropagation();
      closeArmed = false;
      afterFeed(feed(ed, k));
    }

    /* ── 文字入力の受け口 (画面外の textarea) ──
       キー押下イベントだけでは日本語変換 (IME)・Android のソフトキーボード・貼り付けの
       文字を受け取れないため、常にこの textarea にフォーカスを置き、input / composition /
       paste イベントで届いた文字列をエンジンへ流し込む。 */
    var ime = ov.querySelector(".cv-ime"), composing = false;
    function focusIme() { try { ime.focus({ preventScroll: true }); } catch (e) { ime.focus(); } }
    function takeText(text) {
      if (!text) return;
      closeArmed = false;
      if (ed.mode === "normal") {
        /* ソフトキーボードの 1 文字入力は NORMAL モードのコマンドとして扱う。
           まとまった文字列 (貼り付け・変換確定) は誤実行を避けて無視する。 */
        if (text.length === 1) afterFeed(feed(ed, text));
        else { ed.status = "文字を入力するには i (挿入モード) を押してください"; render(); }
        return;
      }
      if (ed.readonly && ed.mode === "insert") return;
      typeText(ed, text); render();
    }
    ime.addEventListener("compositionstart", function () {
      composing = true;
      var cur = ov.querySelector(".cv-cursor"), r = cur ? cur.getBoundingClientRect() : null;
      if (r) { ime.style.left = r.left + "px"; ime.style.top = r.top + "px"; }
      ime.classList.add("on");               /* 変換中の文字をカーソル位置に見せる */
    });
    ime.addEventListener("compositionend", function (e) {
      composing = false; ime.classList.remove("on");
      var text = e.data || ime.value; ime.value = "";
      takeText(text);
    });
    ime.addEventListener("beforeinput", function (e) {
      if (composing) return;
      /* ソフトキーボードは Backspace / Enter をキーイベントではなく入力種別で送ってくる */
      if (e.inputType === "deleteContentBackward") { e.preventDefault(); afterFeed(feed(ed, "Backspace")); }
      else if (e.inputType === "insertLineBreak" || e.inputType === "insertParagraph") { e.preventDefault(); afterFeed(feed(ed, "Enter")); }
    });
    ime.addEventListener("input", function (e) {
      /* 変換中・変換確定の文字は compositionend で受け取るので、ここでは二重に入れない
         (ブラウザにより input が compositionend の前にも後にも来るため、種別で判定する) */
      if (composing || e.inputType === "insertCompositionText" || e.inputType === "insertFromComposition") { if (!composing) ime.value = ""; return; }
      var text = e.data != null ? e.data : ime.value;
      ime.value = "";
      if (e.inputType === "insertFromPaste" || e.inputType === "insertFromDrop") return;   /* paste イベント側で処理済み */
      takeText(text);
    });
    ime.addEventListener("paste", function (e) {
      e.preventDefault();
      var text = (e.clipboardData && e.clipboardData.getData("text")) || "";
      if (!text) return;
      if (ed.mode === "insert" && !ed.readonly) { typeText(ed, text); render(); }
      else if (ed.mode === "command") { typeText(ed, text); render(); }
      else { ed.status = "貼り付けるには i (挿入モード) を押してください"; render(); }
    });
    /* 本文をクリック/タップしたら入力の受け口へフォーカスを戻す (Android ではキーボードが出る) */
    ov.querySelector(".cv-body").addEventListener("click", focusIme);
    function teardown() {
      document.removeEventListener("keydown", onKey, true);
      if (ov.parentNode) ov.parentNode.removeChild(ov);
      if (typeof optsU.onClose === "function") optsU.onClose();
    }
    ov.querySelector(".cv-x").addEventListener("click", function () {
      if (ed.dirty && !confirmDiscard()) return;
      teardown();
    });
    document.addEventListener("keydown", onKey, true);
    render();
    focusIme();
    return { editor: ed, close: teardown, render: render };
  }

  function ensureStyle() {
    if (document.getElementById("cinevim-style")) return;
    var css = document.createElement("style");
    css.id = "cinevim-style";
    css.textContent = [
      ".cinevim-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.86);display:flex;align-items:center;justify-content:center;backdrop-filter:blur(2px)}",
      ".cinevim-overlay .cv-frame{width:min(1100px,96vw);height:min(88vh,900px);background:#000;border:2px solid #1f6f3f;border-radius:14px;box-shadow:0 30px 120px #000,0 0 40px #0f54;display:flex;flex-direction:column;overflow:hidden;font-family:'SFMono-Regular',Consolas,'Noto Sans Mono CJK JP',monospace}",
      ".cinevim-overlay .cv-bar{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:13px;color:#8fe8ab;background:#041a0e;border-bottom:1px solid #15351f}",
      ".cinevim-overlay .cv-status{border-bottom:none;border-top:1px solid #15351f;color:#5f8f6a}",
      ".cinevim-overlay .cv-grow{flex:1}",
      ".cinevim-overlay .cv-name{color:#3cff8e;font-weight:bold;text-shadow:0 0 10px #0f5}",
      ".cinevim-overlay .cv-flag{color:#ffcf4a}",
      ".cinevim-overlay .cv-hint{color:#4a6e55;font-size:11.5px}",
      ".cinevim-overlay .cv-x{margin-left:6px;background:#06160d;color:#9fe8b6;border:1px solid #15351f;border-radius:7px;padding:3px 10px;cursor:pointer;font:inherit}",
      ".cinevim-overlay .cv-x:hover{border-color:#3cff8e}",
      ".cinevim-overlay .cv-acts{display:flex;gap:6px}",
      ".cinevim-overlay .cv-act{background:#06160d;color:#4fe8ff;border:1px solid #15351f;border-radius:7px;padding:3px 10px;cursor:pointer;font:inherit;font-size:12px;white-space:nowrap}",
      ".cinevim-overlay .cv-act:hover{border-color:#4fe8ff}",
      ".cinevim-overlay .cv-hint{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}",
      ".cinevim-overlay .cv-body{flex:1;display:flex;overflow:auto;background:radial-gradient(120% 80% at 50% 0,#02130a,#000 70%)}",
      ".cinevim-overlay .cv-gutter{flex:none;text-align:right;padding:12px 10px 12px 14px;color:#2f6a45;user-select:none;font-size:16px;line-height:1.5}",
      ".cinevim-overlay .cv-ln.cur{color:#ffcf4a}",
      ".cinevim-overlay .cv-text{flex:1;margin:0;padding:12px 16px;color:#d7ffe2;font-size:16px;line-height:1.5;white-space:pre;tab-size:4;outline:none}",
      ".cinevim-overlay .cv-row{min-height:1.5em}",
      ".cinevim-overlay .cv-row.cur{background:#07260f;box-shadow:inset 3px 0 0 #3cff8e}",
      ".cinevim-overlay .cv-cursor{background:#3cff8e;color:#021;border-radius:1px}",
      ".cinevim-overlay .cv-hit{background:#ffcf4a;color:#1a1200;border-radius:2px}",
      ".cinevim-overlay .cv-mode{font-weight:bold;color:#5f8f6a}",
      ".cinevim-overlay .cv-mode.insert{color:#3cff8e;text-shadow:0 0 8px #0f5}",
      ".cinevim-overlay .cv-mode.command{color:#4fe8ff}",
      ".cinevim-overlay .cv-msg{color:#ffb0b0}",
      ".cinevim-overlay .cv-cmd{color:#4fe8ff;font-weight:bold}",
      ".cinevim-overlay .cv-ime{position:fixed;left:0;top:0;width:1px;height:1.5em;padding:0;margin:0;border:0;outline:0;resize:none;overflow:hidden;opacity:0;background:transparent;color:transparent;caret-color:transparent;font:16px/1.5 'SFMono-Regular',Consolas,'Noto Sans Mono CJK JP',monospace;z-index:10001;white-space:pre}",
      ".cinevim-overlay .cv-ime.on{opacity:1;width:60vw;background:#07260f;color:#3cff8e;text-decoration:underline}"
    ].join("\n");
    document.head.appendChild(css);
  }

  var BadaCineVim = {
    createEditor: createEditor,
    feed: feed,
    typeText: typeText,
    search: search,
    open: open,
    ensureStyle: function () { if (typeof document !== "undefined") ensureStyle(); },
    _internal: engine._internal
  };
  if (typeof module !== "undefined" && module.exports) module.exports = BadaCineVim;
  if (typeof global !== "undefined") global.BadaCineVim = BadaCineVim;
})(typeof globalThis !== "undefined" ? globalThis : this);
