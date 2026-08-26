/* ============================================================================
 * app.js — Bada GUI IDE
 *
 * ドラッグ&ドロップした .bada ソースを自動で
 *   1) インタープリタ実行 (全プラットフォーム)
 *   2) Bada → C コンパイル (全プラットフォーム)
 *   3) C → ネイティブ コンパイル&リンク + 実行 (デスクトップ版: gcc 検出時)
 * のパイプラインに流します。
 * ==========================================================================*/
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var editor = $("editor");
  var consoleEl = $("console");
  var cView = $("cView");
  var nativeView = $("nativeView");
  var inspectView = $("inspectView");
  var statusEl = $("status");
  var fileNameEl = $("fileName");
  var autoMode = true;
  var lastC = "";
  var lastBinPath = null;

  /* native bridge (Electron preload) — absent in browser / APK */
  var native = (typeof window !== "undefined" && window.badaNative) ? window.badaNative : null;
  $("envInfo").textContent = native
    ? "デスクトップ版 (ネイティブ リンク対応)"
    : "ポータブル版 (インタープリタ + C生成)";
  if (!native) $("btnSaveBin").style.display = "none";

  /* ---------------- console helpers ---------------- */
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function clearConsole() { consoleEl.innerHTML = ""; }
  function logLine(text, cls) {
    var span = document.createElement("span");
    if (cls) span.className = cls;
    span.innerHTML = esc(text) + "\n";
    consoleEl.appendChild(span);
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }
  function setStatus(s) { statusEl.textContent = s; }

  function showTab(name) {
    var tabs = document.querySelectorAll(".tab");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.toggle("on", tabs[i].dataset.tab === name);
    }
    var bodies = document.querySelectorAll(".tab-body");
    for (var j = 0; j < bodies.length; j++) {
      bodies[j].classList.toggle("on", bodies[j].id === "tab-" + name);
    }
  }
  var tabBtns = document.querySelectorAll(".tab");
  for (var ti = 0; ti < tabBtns.length; ti++) {
    tabBtns[ti].addEventListener("click", function () { showTab(this.dataset.tab); });
  }

  /* ---------------- pipeline steps ---------------- */
  function runInterpreter() {
    var src = editor.value;
    clearConsole();
    showTab("out");
    logLine("── インタープリタ実行 ──────────────────────────", "head");
    var t0 = Date.now();
    var r = BadaLang.run(src, {
      maxSteps: 20000000,
      /* デスクトップ版: @reviser : extension (python/java/c) を FFI で実行 */
      ffi: native && native.ffiSync
        ? function (lang, name, code, params, argv) { return native.ffiSync(lang, name, code, params, argv); }
        : null
    });
    if (r.parseErrors.length) {
      for (var i = 0; i < r.parseErrors.length; i++) logLine(r.parseErrors[i], "err");
    }
    if (r.output) logLine(r.output);
    if (r.rules && r.rules.length)
      logLine("[grammar] reviser拡張ルール: " + r.rules.join(", "), "cyan");
    var ms = Date.now() - t0;
    if (r.ok) {
      logLine("── 完了 (" + ms + " ms, ledger " + r.ledgerLen + " facts) ──", "ok");
      setStatus("インタープリタ実行 完了 (" + ms + " ms)");
    } else {
      logLine("── エラーで終了 ──", "err");
      setStatus("実行エラー — 出力を確認してください");
    }
    return r;
  }

  function compileToC() {
    var src = editor.value;
    var r = BadaLang.emitC(src);
    lastC = r.c;
    cView.textContent = r.c;
    if (r.errors.length) {
      cView.textContent = r.errors.join("\n") + "\n\n" + r.c;
    }
    setStatus("Bada → C コンパイル " + (r.ok ? "完了" : "(構文エラーあり)") +
      " — " + r.c.split("\n").length + " 行の C を生成");
    return r;
  }

  function buildNative(auto) {
    if (!lastC) compileToC();
    nativeView.textContent = "";
    if (!native) {
      nativeView.textContent =
        "このビルドではネイティブ コンパイル&リンクは利用できません。\n\n" +
        "・Windows / Ubuntu 版 (デスクトップアプリ) では、gcc が見つかれば\n" +
        "  生成した C を自動でコンパイル&リンクし、バイナリを実行します。\n" +
        "・ここでは「📄 生成C」タブから .c を保存し、\n" +
        "    gcc -O2 -o program program.c -lm\n" +
        "  でビルドできます。インタープリタ実行は全プラットフォームで動作します。";
      if (!auto) showTab("native");
      return Promise.resolve(null);
    }
    if (!auto) showTab("native");
    nativeView.textContent = "gcc でコンパイル&リンク中…\n";
    setStatus("ネイティブ ビルド中…");
    return native.buildAndRun(lastC).then(function (res) {
      var txt = "";
      txt += "$ " + res.command + "\n\n";
      if (res.compileLog) txt += res.compileLog + "\n";
      if (res.ok) {
        lastBinPath = res.exePath;
        $("btnSaveBin").disabled = false;
        txt += "[link ok] → " + res.exePath + "\n";
        txt += "\n── コンパイル済みバイナリの実行結果 ──────────────\n";
        txt += res.runOutput || "(出力なし)";
        setStatus("ネイティブ ビルド&リンク&実行 完了");
        logLine("", null);
        logLine("── ネイティブ (コンパイル&リンク済みバイナリ) ──────", "head");
        logLine(res.runOutput || "(出力なし)");
        logLine("── ネイティブ実行 完了 ──", "ok");
      } else {
        txt += "[build failed]\n" + (res.error || "");
        setStatus("ネイティブ ビルド失敗 — gcc の有無を確認してください");
      }
      nativeView.textContent = txt;
      return res;
    }).catch(function (e) {
      nativeView.textContent = "ネイティブ ビルド エラー: " + e;
      setStatus("ネイティブ ビルド エラー");
      return null;
    });
  }

  /* the full drop pipeline: interpret + compile + (native link) */
  function autoPipeline() {
    runInterpreter();
    compileToC();
    return buildNative(true);
  }

  /* ---------------- file loading ---------------- */
  function loadSource(name, text) {
    fileNameEl.textContent = name;
    editor.value = text;
    lastBinPath = null;
    $("btnSaveBin").disabled = true;
    if (autoMode) autoPipeline();
    else setStatus(name + " を読み込みました — ▶ 実行 または ⚙ コンパイル を押してください");
  }

  function readDroppedFile(file) {
    var reader = new FileReader();
    reader.onload = function () { loadSource(file.name, String(reader.result)); };
    reader.readAsText(file);
  }

  /* drag & drop — the whole window is a drop target */
  var dragDepth = 0;
  var overlay = $("dropOverlay");
  window.addEventListener("dragenter", function (e) {
    e.preventDefault();
    dragDepth++;
    overlay.classList.add("on");
  });
  window.addEventListener("dragleave", function (e) {
    e.preventDefault();
    if (--dragDepth <= 0) { dragDepth = 0; overlay.classList.remove("on"); }
  });
  window.addEventListener("dragover", function (e) { e.preventDefault(); });
  window.addEventListener("drop", function (e) {
    e.preventDefault();
    dragDepth = 0;
    overlay.classList.remove("on");
    var files = e.dataTransfer && e.dataTransfer.files;
    if (files && files.length) readDroppedFile(files[0]);
  });

  $("filePick").addEventListener("change", function () {
    if (this.files && this.files.length) readDroppedFile(this.files[0]);
    this.value = "";
  });

  $("exampleSel").addEventListener("change", function () {
    var k = this.value;
    this.value = "";
    if (k && BADA_EXAMPLES[k]) loadSource(k + ".bada", BADA_EXAMPLES[k]);
  });

  /* ---------------- buttons ---------------- */
  $("btnRun").addEventListener("click", function () { runInterpreter(); });
  $("btnCompile").addEventListener("click", function () { compileToC(); showTab("c"); });
  $("btnBuild").addEventListener("click", function () { compileToC(); buildNative(false); });
  $("btnAuto").addEventListener("click", function () {
    autoMode = !autoMode;
    this.classList.toggle("on", autoMode);
    this.textContent = autoMode ? "⚡ 自動: ON" : "⚡ 自動: OFF";
  });
  $("btnClearEd").addEventListener("click", function () {
    editor.value = "";
    fileNameEl.textContent = "untitled.bada";
  });
  $("btnTokens").addEventListener("click", function () {
    inspectView.textContent = BadaLang.tokens(editor.value);
  });
  $("btnAst").addEventListener("click", function () {
    var a = BadaLang.ast(editor.value);
    inspectView.textContent = (a.errors.length ? a.errors.join("\n") + "\n\n" : "") + a.text;
  });

  function downloadText(name, text) {
    if (native && native.saveFile) { native.saveFile(name, text); return; }
    var blob = new Blob([text], { type: "text/plain" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }
  $("btnSaveC").addEventListener("click", function () {
    if (!lastC) compileToC();
    var base = (fileNameEl.textContent || "program.bada").replace(/\.bada$/, "");
    downloadText(base + ".gen.c", lastC);
  });
  $("btnSaveBin").addEventListener("click", function () {
    if (native && native.exportBinary && lastBinPath) native.exportBinary(lastBinPath);
  });

  /* Ctrl+Enter = run */
  editor.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); runInterpreter(); }
  });

  /* boot: load the quantum example so the IDE opens alive */
  fileNameEl.textContent = "quantum.bada";
  editor.value = BADA_EXAMPLES.quantum;
  setStatus("準備完了 — Bada v" + BadaLang.VERSION +
    " / .bada をドロップすると コンパイル&リンク&実行 を自動で行います");
})();
