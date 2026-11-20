/*
 * pdfview.js — BadaCineVim PDF ビュー: PDF をページとして表示し、その場で編集する
 *
 * Bada Search の検索結果から PDF を「本物のページ」として開き (同梱の pdf.js で描画)、
 * 検索語のあるページへ自動ジャンプして一致箇所を光らせます。さらに BadaCineVim の
 * 編集機能として、ページの上に
 *     🖍 マーカー (ハイライト) / ✎ ペン (手書き) / 💬 メモ (文字の書き込み)
 * を付け、:w で PDF そのものに保存します (標準の PDF 注釈として書き込むので、
 * 他の PDF ビューアでも表示されます。書き込みは pdfedit.js + 同梱の pdf-lib)。
 *
 * 編集は Vim と同じ 3 つのモードで行います。ページ上の文字 (1 行ぶんのまとまり) の上に
 * カーソルがあり、その行をその場で書き換えます (元の文字を隠して打ち直す「文字修正」)。
 *
 *   NORMAL  h l 文字 / j k 行 / w b 次・前のまとまり / 0 $ 行頭・行末 / gg G 先頭・末尾ページ
 *           Ctrl-d Ctrl-u 半画面 / ] [ (← →) 次・前のページ / n N 次・前のヒット / + - 拡大縮小
 *           x 1 字削除  dd 行を削除  D 行末まで削除  yy ヤンク  p 下に貼り付け  u 取り消し
 *   INSERT  i a I A (カーソル位置 / 次 / 行頭 / 行末から入力)  o O (下 / 上に新しい行)
 *           cc S (行を打ち直す) — 文字を打って Esc で確定 (Enter は改行)。日本語変換も可。
 *   COMMAND :s/旧/新/[g][i]   カーソル行を置換      :%s/旧/新/g   全ページを置換
 *           :d 行を削除   :note 文 … カーソル行にメモ   :hl … カーソル行にマーカー
 *           :marker :pen :note :text :erase :select  … マウスで使うツールの切り替え
 *           :rotate :delpage :blank :merge :move N :flatten  … ページ操作 / 焼き込み
 *           :N ページ移動  /語 検索  :w 保存  :q 閉じる (未保存なら :q!)  :wq  :undo
 *   その他  v 選択ツール  m マーカー  M ヒットをマーカー化  R 回転  < > ページ移動
 *           F 焼き込み  t テキスト表示へ  (選択中の書き込みは x で削除)
 *
 * マウス用のツール (ツールバー): 🖍 マーカー / ✎ ペン / 💬 メモ / ✏ 文字修正 (文字をクリック
 * して書き換え) / ⬜ 消去 / ページの回転・並べ替え・空白・結合・削除 / 📌 焼き込み。
 * どの操作も u で取り消せます (ページ操作・焼き込みも含む)。
 *
 * ライブラリ (vendor/pdfjs, vendor/pdf-lib) は PDF を開いたときに初めて読み込みます。
 *
 * このファイルは Bada Search (sourcetree_search/app/www) と単体アプリ Bada CineVim
 * (bada_cinevim/pdf) で同じものを使います (CI が一致を検証)。アプリごとの違いは
 * open() のオプションで渡します:
 *   loadPdfJs()  … pdf.js を用意して返す関数 (省略時は vendorBase から読み込む)
 *   docParams    … pdf.js の getDocument に足す設定 (CMap の供給方法など)
 *   pdfLibUrl    … pdf-lib の場所 (省略時は vendorBase + "pdf-lib/pdf-lib.min.js")
 *   annots/dirty … 前回閉じたときの注釈を引き継ぐ (bytes は注釈を外した PDF を渡す)。
 *                  keepOnClose:true なら未保存でも確認なしで閉じ、onClose に
 *                  { annots, dirty, baseBytes } を渡すので、呼び出し側で保持できる。
 */
(function (global) {
  "use strict";

  var SVGNS = "http://www.w3.org/2000/svg";
  var COLORS = ["#ffe14a", "#7dff9c", "#ff9ecb", "#7fd8ff"];
  var INK_COLORS = ["#ff3b5c", "#1f6fff", "#12a150", "#111111"];

  /* ───────── ライブラリの遅延読み込み ───────── */
  var scriptCache = {};
  function loadScript(src) {
    if (scriptCache[src]) return scriptCache[src];
    scriptCache[src] = new Promise(function (resolve, reject) {
      var el = document.createElement("script");
      el.src = src;
      el.onload = function () { resolve(); };
      el.onerror = function () { delete scriptCache[src]; reject(new Error("読み込めません: " + src)); };
      document.head.appendChild(el);
    });
    return scriptCache[src];
  }
  function ensurePdfJs(base) {
    if (global.pdfjsLib) return Promise.resolve(global.pdfjsLib);
    return loadScript(base + "pdfjs/pdf.min.js").then(function () {
      /* file:// などで Worker を作れない環境では pdf.js が自動で同一スレッド実行に切り替える */
      global.pdfjsLib.GlobalWorkerOptions.workerSrc = base + "pdfjs/pdf.worker.min.js";
      return global.pdfjsLib;
    });
  }
  function ensurePdfLib(url) {
    if (global.PDFLib) return Promise.resolve(global.PDFLib);
    return loadScript(url).then(function () { return global.PDFLib; });
  }

  /* pdf.js へ CMap (日本語など CID フォントの文字コード表) と標準フォントを供給する。
     既定の読み込み (fetch / XHR) は file:// でブロックされ日本語が描画されないため、
     <script> で読める同梱バンドル (cmaps.bundle.js / standard_fonts.bundle.js) から渡す。 */
  function b64Bytes(b64) {
    var bin = atob(b64), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function assetFactory(base, kind) {
    function Factory() {}
    Factory.prototype.fetch = function (arg) {
      var cmap = kind === "cmap", file = cmap ? arg.name + ".bcmap" : arg.filename;
      return loadScript(base + "pdfjs/" + (cmap ? "cmaps.bundle.js" : "standard_fonts.bundle.js")).then(function () {
        var b64 = (cmap ? global.BADA_PDF_CMAPS : global.BADA_PDF_FONTS)[file];
        if (!b64) throw new Error("同梱データにありません: " + file);
        var data = b64Bytes(b64);
        return cmap ? { cMapData: data, compressionType: global.pdfjsLib.CMapCompressionType.BINARY } : data;
      });
    };
    return Factory;
  }

  function svg(tag, attrs) {
    var el = document.createElementNS(SVGNS, tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }
  /* 文字列の相対幅 (ヒット位置を 1 つのテキスト片の中で按分するのに使う)。
     実フォントは分からないので、プロポーショナル書体で実測した比率で近似する。 */
  var measureCtx = null;
  function emOf(s) {
    if (!s) return 0;
    if (!measureCtx) {
      measureCtx = document.createElement("canvas").getContext("2d");
      measureCtx.font = "100px 'Times New Roman',Times,'Noto Serif',serif";
    }
    return measureCtx.measureText(s).width / 100;
  }

  /* ───────── 本体 ───────── */
  function open(opts) {
    opts = opts || {};
    if (typeof document === "undefined") return null;
    var Edit = global.BadaPdfEdit;
    var base = opts.vendorBase || "vendor/";
    var pdfLibUrl = opts.pdfLibUrl || (base + "pdf-lib/pdf-lib.min.js");
    var canSave = typeof opts.onSave === "function" && !opts.readonly;

    var st = {
      pdf: null, pages: [], scale: 1, annots: [], sel: null, tool: "select",
      color: COLORS[0], inkColor: INK_COLORS[0], undo: [], dirty: false, editable: canSave,
      hits: {}, hitPages: [], hitCount: 0, terms: [], mode: "normal", cmd: "", pending: "",
      baseBytes: null, closed: false, status: "", cur: 0, nextId: 1, scanToken: 0, closeArmed: false, busy: false
    };

    var ov = document.createElement("div");
    ov.className = "cinevim-overlay badapdf-overlay";
    ov.setAttribute("role", "dialog");
    ov.innerHTML =
      '<div class="cv-frame pv-frame">' +
        '<div class="cv-bar cv-top"><span class="cv-name"></span><span class="cv-flag"></span>' +
          '<span class="cv-acts"></span><span class="cv-grow"></span>' +
          '<button class="pv-b" data-act="prev" title="前のページ ([)">◀</button>' +
          '<span class="pv-pageno">– / –</span>' +
          '<button class="pv-b" data-act="next" title="次のページ (])">▶</button>' +
          '<button class="pv-b" data-act="zout" title="縮小 (-)">−</button>' +
          '<span class="pv-zoom">100%</span>' +
          '<button class="pv-b" data-act="zin" title="拡大 (+)">＋</button>' +
          '<button class="cv-x" title="閉じる (:q)">✕</button></div>' +
        '<div class="cv-bar pv-tools">' +
          '<button class="pv-t" data-tool="select" title="選択・移動 (v)">👆 選択</button>' +
          '<button class="pv-t" data-tool="highlight" title="ドラッグでマーカー (m)">🖍 マーカー</button>' +
          '<button class="pv-t" data-tool="ink" title="手書き (:pen)">✎ ペン</button>' +
          '<button class="pv-t" data-tool="note" title="クリックした場所にメモを書き込む (:note)">💬 メモ</button>' +
          '<span class="pv-colors"></span>' +
          '<button class="pv-b" data-act="hitmark" title="このページの検索ヒットをマーカーとして残す (M)">🔎→🖍</button>' +
          '<button class="pv-b" data-act="del" title="選択した注釈を削除 (x)">🗑</button>' +
          '<button class="pv-b" data-act="undo" title="取り消し (u)">↶</button>' +
          '<span class="cv-grow"></span>' +
          '<button class="pv-b pv-save" data-act="save" title="PDF に保存 (:w)">💾 保存</button></div>' +
        '<div class="cv-bar pv-tools pv-edit"><span class="pv-lab">PDF 編集</span>' +
          '<button class="pv-t" data-tool="textedit" title="文字をクリックして書き換える / 何もない所をクリックして文字を追加 (:text)">✏ 文字修正</button>' +
          '<button class="pv-t" data-tool="erase" title="ドラッグした範囲を塗りつぶして消す (:erase)">⬜ 消去</button>' +
          '<span class="pv-sep"></span><span class="pv-lab">ページ</span>' +
          '<button class="pv-b" data-act="rot" title="このページを右に 90° 回転 (R)">⟳ 回転</button>' +
          '<button class="pv-b" data-act="pgup" title="このページを 1 つ前へ (<)">⬆ 前へ</button>' +
          '<button class="pv-b" data-act="pgdn" title="このページを 1 つ後ろへ (>)">⬇ 後ろへ</button>' +
          '<button class="pv-b" data-act="blank" title="このページの後ろに空白ページを入れる (:blank)">➕ 空白</button>' +
          '<button class="pv-b" data-act="merge" title="別の PDF を末尾に結合 (:merge)">📎 結合</button>' +
          '<button class="pv-b" data-act="pgdel" title="このページを削除 (:delpage)">✂ 削除</button>' +
          '<span class="pv-sep"></span>' +
          '<button class="pv-b" data-act="flatten" title="書き込みをページ本体に焼き込んで確定する (F)">📌 焼き込み</button>' +
          '<input type="file" class="pv-mergein" accept=".pdf,application/pdf" style="display:none"/></div>' +
        '<div class="cv-body pv-body" tabindex="0"><div class="pv-pages"></div></div>' +
        '<div class="cv-bar cv-status"><span class="cv-mode">PDF</span><span class="cv-msg"></span>' +
          '<span class="cv-grow"></span>' +
          '<span class="cv-hint">h j k l カーソル · i a o 挿入 (Esc 確定) · x dd 削除 · u 取消 · :s/旧/新/ 置換 · [ ] ページ · :w 保存 · :q 閉じる</span>' +
          '<input class="pv-cmdin" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="コマンド (:w :q /検索語)"/></div>' +
      '</div>';
    document.body.appendChild(ov);
    if (global.BadaCineVim && global.BadaCineVim.ensureStyle) global.BadaCineVim.ensureStyle();   /* 枠の共通スタイル */
    ensureStyle();

    var q = function (s) { return ov.querySelector(s); };
    var elBody = q(".pv-body"), elPages = q(".pv-pages"), elMsg = q(".cv-msg"), elCmd = q(".pv-cmdin"),
        elFlag = q(".cv-flag"), elPageNo = q(".pv-pageno"), elZoom = q(".pv-zoom"), elColors = q(".pv-colors"),
        elMode = q(".cv-mode");
    q(".cv-name").textContent = "🎬 " + (opts.name || "document.pdf") + "  [PDF]";

    /* 追加ボタン (「⌨ テキスト」「📝 .tex を編集」など) */
    var acts = (opts.actions || []).slice();
    if (typeof opts.onTextMode === "function") {
      acts.unshift({ label: "⌨ テキスト", title: "抽出テキストを CineVim で表示 (t)", onClick: function (c) { c.close(); opts.onTextMode(); } });
    }
    acts.forEach(function (act) {
      var b = document.createElement("button");
      b.className = "cv-act"; b.textContent = act.label; if (act.title) b.title = act.title;
      b.addEventListener("click", function () { if (st.dirty && !confirmDiscard()) return; act.onClick({ close: teardown }); });
      q(".cv-acts").appendChild(b);
    });

    function setStatus(s) { st.status = s || ""; refreshChrome(); }
    function refreshChrome() {
      elMsg.textContent = st.status;
      elCmd.style.display = st.mode === "command" ? "" : "none";
      q(".cv-hint").style.display = st.mode === "command" ? "none" : "";
      elFlag.textContent = !st.editable ? " [RO]" : (st.dirty ? " [+]" : "");
      elPageNo.textContent = st.pages.length ? (st.cur + 1) + " / " + st.pages.length : "– / –";
      elZoom.textContent = Math.round(st.scale * 100) + "%";
      elMode.textContent = st.mode === "command" ? "" : st.mode === "insert" ? "-- 挿入 --" : ({ select: "NORMAL", highlight: "-- マーカー --", ink: "-- ペン --", note: "-- メモ --", textedit: "-- 文字修正 --", erase: "-- 消去 --" })[st.tool];
      elMode.className = "cv-mode " + (st.tool === "select" && st.mode !== "insert" ? "" : "insert");
      Array.prototype.forEach.call(ov.querySelectorAll(".pv-t"), function (b) {
        b.classList.toggle("on", b.getAttribute("data-tool") === st.tool);
        b.disabled = !st.editable && b.getAttribute("data-tool") !== "select";
      });
      ["del", "undo", "save", "hitmark", "rot", "pgup", "pgdn", "blank", "merge", "pgdel", "flatten"].forEach(function (a) { q('[data-act="' + a + '"]').disabled = !st.editable; });
      ov.classList.toggle("pv-drawing", st.tool !== "select");
      renderColors();
    }
    function renderColors() {
      var list = st.tool === "ink" ? INK_COLORS : COLORS, cur = st.tool === "ink" ? st.inkColor : st.color;
      elColors.innerHTML = "";
      list.forEach(function (c) {
        var b = document.createElement("button");
        b.className = "pv-c" + (c === cur ? " on" : ""); b.style.background = c; b.title = "色";
        b.addEventListener("click", function () {
          if (st.tool === "ink") st.inkColor = c; else st.color = c;
          var a = selected();
          if (a && st.editable) { pushUndo(); a.color = c; touch(a.page); }
          refreshChrome();
        });
        elColors.appendChild(b);
      });
    }

    /* ───────── 注釈モデル ───────── */
    function selected() { for (var i = 0; i < st.annots.length; i++) if (st.annots[i]._id === st.sel) return st.annots[i]; return null; }
    /* 取り消し用の履歴。注釈に加えて PDF 本体 (ページ操作・焼き込みで変わる) も覚える */
    function pushUndo() {
      st.undo.push({ a: JSON.stringify(st.annots), b: st.baseBytes });
      if (st.undo.length > 100) st.undo.shift();
    }
    function touch(page) { st.dirty = true; st.closeArmed = false; drawOverlay(page); refreshChrome(); }
    function addAnnot(a) {
      var n = Edit.normalize(a);
      if (!n) return null;
      pushUndo();
      n._id = st.nextId++;
      st.annots.push(n); st.sel = n._id;
      touch(n.page);
      return n;
    }
    function removeSelected() {
      var a = selected();
      if (!a) { setStatus("削除する注釈を選んでください (👆 選択でクリック)"); return; }
      pushUndo();
      st.annots = st.annots.filter(function (x) { return x !== a; });
      st.sel = null; touch(a.page); setStatus("注釈を削除しました");
    }
    function undo() {
      if (st.busy) return;
      if (!st.undo.length) { setStatus("これ以上戻せません"); return; }
      var u = st.undo.pop();
      st.annots = JSON.parse(u.a);
      st.sel = null; st.dirty = true;
      if (u.b !== st.baseBytes) { st.baseBytes = u.b; reloadDoc(st.cur).then(function () { setStatus("元に戻しました"); }); return; }
      refreshCursor().then(function () { st.pages.forEach(function (_, i) { drawOverlay(i); }); });
      setStatus("元に戻しました");
    }
    function moveAnnot(a, dx, dy) {
      var i, j;
      if (a.type === "note") { a.x += dx; a.y += dy; }
      else if (a.type === "textedit") {
        a.x += dx; a.y += dy;
        if (a.cover) { a.cover[0] += dx; a.cover[2] += dx; a.cover[1] += dy; a.cover[3] += dy; }
      }
      else if (a.type === "highlight" || a.type === "erase") for (i = 0; i < a.rects.length; i++) { a.rects[i][0] += dx; a.rects[i][2] += dx; a.rects[i][1] += dy; a.rects[i][3] += dy; }
      else if (a.type === "ink") for (i = 0; i < a.paths.length; i++) for (j = 0; j + 1 < a.paths[i].length; j += 2) { a.paths[i][j] += dx; a.paths[i][j + 1] += dy; }
    }

    /* ───────── 座標変換 (PDF ユーザー空間 ⇔ 画面 px。回転・CropBox は viewport が吸収) ───────── */
    function toView(P, x, y) { return P.viewport.convertToViewportPoint(x, y); }
    function toPdf(P, vx, vy) { return P.viewport.convertToPdfPoint(vx, vy); }
    function viewRect(P, r) {
      var a = toView(P, r[0], r[1]), b = toView(P, r[2], r[3]);
      return { x: Math.min(a[0], b[0]), y: Math.min(a[1], b[1]), w: Math.abs(b[0] - a[0]), h: Math.abs(b[1] - a[1]) };
    }

    /* ───────── 注釈レイヤの描画 (SVG) ───────── */
    function drawOverlay(i) {
      var P = st.pages[i];
      if (!P) return;
      var g = P.svg;
      while (g.firstChild) g.removeChild(g.firstChild);
      (st.hits[i] || []).forEach(function (r) {
        var v = viewRect(P, r);
        g.appendChild(svg("rect", { x: v.x, y: v.y, width: v.w, height: v.h, "class": "pv-hit", rx: 2 }));
      });
      st.annots.forEach(function (a) {
        if (a.page !== i) return;
        var grp = svg("g", { "class": "pv-a pv-" + a.type + (a._id === st.sel ? " sel" : ""), "data-id": a._id });
        if (a.type === "highlight") {
          a.rects.forEach(function (r) {
            var v = viewRect(P, r);
            grp.appendChild(svg("rect", { x: v.x, y: v.y, width: v.w, height: v.h, fill: a.color, "class": "pv-mark" }));
          });
        } else if (a.type === "erase") {
          a.rects.forEach(function (r) {
            var v = viewRect(P, r);
            grp.appendChild(svg("rect", { x: v.x, y: v.y, width: v.w, height: v.h, fill: a.color }));
          });
        } else if (a.type === "textedit") {
          if (a.cover) {
            var cv = viewRect(P, a.cover);
            grp.appendChild(svg("rect", { x: cv.x, y: cv.y, width: cv.w, height: cv.h, fill: a.bg }));
          }
          var o = toView(P, a.x, a.y), tfs = (a.size || 12) * st.scale;
          var tt = svg("text", { x: o[0], y: o[1], fill: a.color, "font-size": tfs, "class": "pv-edittext pv-font-" + (a.font || "sans") });
          String(a.text).split("\n").forEach(function (line, k) {
            var ts = svg("tspan", { x: o[0], y: o[1] + k * tfs * 1.2 });
            ts.textContent = line || " ";
            tt.appendChild(ts);
          });
          grp.appendChild(tt);
          var hb = viewRect(P, Edit.annotRect(a));      /* 文字の上のどこでも掴めるように透明の当たり判定 */
          grp.appendChild(svg("rect", { x: hb.x, y: hb.y, width: hb.w, height: hb.h, "class": "pv-grabbox" }));
        } else if (a.type === "ink") {
          a.paths.forEach(function (p) {
            var pts = [];
            for (var j = 0; j + 1 < p.length; j += 2) { var pt = toView(P, p[j], p[j + 1]); pts.push(pt[0].toFixed(1) + "," + pt[1].toFixed(1)); }
            if (pts.length === 1) pts.push(pts[0]);
            grp.appendChild(svg("polyline", { points: pts.join(" "), stroke: a.color, "stroke-width": Math.max(1, (a.width || 2) * st.scale),
              fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" }));
            grp.appendChild(svg("polyline", { points: pts.join(" "), "class": "pv-grab" }));
          });
        } else if (a.type === "note") {
          var v = viewRect(P, Edit.noteRect(a)), fs = (a.size || 12) * st.scale;
          grp.appendChild(svg("rect", { x: v.x, y: v.y, width: v.w, height: v.h, "class": "pv-notebg", rx: 2 }));
          var t = svg("text", { x: v.x + 4 * st.scale, y: v.y, fill: a.color, "font-size": fs, "class": "pv-notetext" });
          String(a.text).split("\n").forEach(function (line, k) {
            var ts = svg("tspan", { x: v.x + 4 * st.scale, y: v.y + 2 * st.scale + fs * 1.05 + k * fs * 1.3 });
            ts.textContent = line || " ";
            t.appendChild(ts);
          });
          grp.appendChild(t);
        }
        if (a._id === st.sel) {
          var b = viewRect(P, Edit.annotRect(a));
          grp.appendChild(svg("rect", { x: b.x - 3, y: b.y - 3, width: b.w + 6, height: b.h + 6, "class": "pv-selbox", rx: 3 }));
        }
        g.appendChild(grp);
      });
      /* Vim カーソル (NORMAL モードで文字の上に載るブロック) */
      var vc = st.vc, ln = st.vcLine;
      if (vc && ln && vc.page === i && st.mode !== "insert") {
        var first = String(ln.text).split("\n")[0], total = emOf(first) || 1, size = ln.size || 12;
        var cx = ln.x + (first ? ln.width * emOf(first.slice(0, vc.c)) / total : 0);
        var cw = first && vc.c < first.length ? ln.width * emOf(first.charAt(vc.c)) / total : size * 0.5;
        var lr = viewRect(P, [ln.x - 1, ln.y - size * 0.27, ln.x + Math.max(ln.width, size * 0.5) + 1, ln.y + size * 0.92]);
        g.appendChild(svg("rect", { x: lr.x, y: lr.y, width: lr.w, height: lr.h, "class": "pv-curline" }));
        var cr = viewRect(P, [cx, ln.y - size * 0.27, cx + Math.max(cw, size * 0.25), ln.y + size * 0.92]);
        g.appendChild(svg("rect", { x: cr.x, y: cr.y, width: cr.w, height: cr.h, "class": "pv-vimcur" }));
      }
    }

    /* ───────── ページの生成と遅延描画 ───────── */
    var io = null;
    function buildPages(fixedScale) {
      var n = st.pdf.numPages, chain = Promise.resolve();
      for (var k = 1; k <= n; k++) (function (num) {
        chain = chain.then(function () { return st.pdf.getPage(num); }).then(function (page) {
          if (st.closed) return;
          if (num === 1 && !fixedScale) {
            var w0 = page.getViewport({ scale: 1 }).width;
            st.scale = Math.max(0.5, Math.min(1.6, (elBody.clientWidth - 48) / w0));
          }
          var P = { page: page, viewport: page.getViewport({ scale: st.scale }), rendered: null, task: null, visible: false };
          P.wrap = document.createElement("div"); P.wrap.className = "pv-page"; P.wrap.setAttribute("data-i", num - 1);
          P.canvas = document.createElement("canvas");
          P.svg = svg("svg", { "class": "pv-ann" });
          var no = document.createElement("div"); no.className = "pv-pno"; no.textContent = num;
          P.wrap.appendChild(P.canvas); P.wrap.appendChild(P.svg); P.wrap.appendChild(no);
          elPages.appendChild(P.wrap);
          st.pages.push(P);
          sizePage(P);
          bindPointer(P, num - 1);
          drawOverlay(num - 1);
          if (io) io.observe(P.wrap);
          if (num === 1) refreshChrome();
        });
      })(k);
      return chain;
    }
    function sizePage(P) {
      P.viewport = P.page.getViewport({ scale: st.scale });
      var w = Math.floor(P.viewport.width), h = Math.floor(P.viewport.height);
      P.wrap.style.width = w + "px"; P.wrap.style.height = h + "px";
      P.svg.setAttribute("width", w); P.svg.setAttribute("height", h);
      P.svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    }
    function renderPage(i) {
      var P = st.pages[i];
      if (!P || !P.visible || st.closed) return;
      if (P.rendered === st.scale || P.task) return;
      var want = st.scale, dpr = Math.min(global.devicePixelRatio || 1, 2);
      var vp = P.page.getViewport({ scale: want * dpr });
      /* 新しいキャンバスに描いてから差し替える (拡大縮小中のちらつき防止) */
      var c = document.createElement("canvas");
      c.width = Math.floor(vp.width); c.height = Math.floor(vp.height);
      P.task = P.page.render({ canvasContext: c.getContext("2d"), viewport: vp });
      P.task.promise.then(function () {
        P.task = null;
        if (st.closed) return;
        P.wrap.replaceChild(c, P.canvas); P.canvas = c; P.rendered = want;
        P.wrap.classList.add("ready");
        if (st.scale !== want) renderPage(i);
      }, function () { P.task = null; });
    }
    function setupObserver() {
      if (typeof IntersectionObserver === "undefined") {
        st.pages.forEach(function (P, i) { P.visible = true; renderPage(i); });
        return;
      }
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          var i = parseInt(en.target.getAttribute("data-i"), 10), P = st.pages[i];
          if (!P) return;
          P.visible = en.isIntersecting;
          if (P.visible) renderPage(i);
          else if (P.rendered != null && !P.task) {   /* 画面外のページはメモリを解放 */
            P.canvas.width = 0; P.canvas.height = 0; P.rendered = null; P.wrap.classList.remove("ready");
          }
        });
      }, { root: elBody, rootMargin: "700px 0px" });
      st.pages.forEach(function (P) { io.observe(P.wrap); });
    }
    function setScale(s) {
      s = Math.max(0.4, Math.min(4, s));
      if (s === st.scale || !st.pages.length) return;
      var keep = st.cur;
      st.scale = s;
      st.pages.forEach(function (P, i) { sizePage(P); drawOverlay(i); renderPage(i); });
      gotoPage(keep);
      refreshChrome();
    }
    function gotoPage(i) {
      if (!st.pages.length) return;
      i = Math.max(0, Math.min(st.pages.length - 1, i));
      elBody.scrollTop = st.pages[i].wrap.offsetTop - 10;
      st.cur = i; refreshChrome();
    }
    /* ヒットのあるページへ移動し、最初のヒットが画面の上 1/3 あたりに来るようにする */
    function gotoHit(i) {
      var P = st.pages[i], rects = st.hits[i];
      if (!P || !rects || !rects.length) { gotoPage(i); return; }
      var y = Infinity;
      rects.forEach(function (r) { y = Math.min(y, viewRect(P, r).y); });
      elBody.scrollTop = Math.max(0, P.wrap.offsetTop + y - elBody.clientHeight / 3);
      st.cur = i; refreshChrome();
    }
    function onScroll() {
      var top = elBody.scrollTop + elBody.clientHeight * 0.35, cur = 0;
      for (var i = 0; i < st.pages.length; i++) { if (st.pages[i].wrap.offsetTop <= top) cur = i; else break; }
      if (cur !== st.cur) { st.cur = cur; refreshChrome(); }
    }
    elBody.addEventListener("scroll", onScroll);

    /* ───────── PDF 内の検索ヒット (検索語のあるページへジャンプ + 光らせる) ───────── */
    function scanHits(query, jump, quiet) {
      var token = ++st.scanToken;
      st.lastQuery = String(query || "");
      st.terms = String(query || "").split(/\s+/).filter(Boolean).map(function (t) { return t.toLowerCase(); });
      st.hits = {}; st.hitPages = []; st.hitCount = 0;
      st.pages.forEach(function (_, i) { drawOverlay(i); });
      if (!st.terms.length || !st.pdf) return Promise.resolve();
      var jumped = false, chain = Promise.resolve();
      for (var k = 0; k < st.pages.length; k++) (function (i) {
        chain = chain.then(function () {
          if (st.closed || token !== st.scanToken) return null;
          return st.pages[i].page.getTextContent();
        }).then(function (tc) {
          if (!tc || st.closed || token !== st.scanToken) return;
          var rects = [];
          tc.items.forEach(function (it) {
            if (!it.str) return;
            var low = it.str.toLowerCase(), tx = it.transform, total = emOf(it.str) || 1;
            var h = it.height || Math.hypot(tx[2], tx[3]) || 10;
            st.terms.forEach(function (term) {
              var from = 0, idx;
              while ((idx = low.indexOf(term, from)) >= 0) {
                var x = tx[4] + it.width * emOf(it.str.slice(0, idx)) / total;
                var w = it.width * emOf(it.str.slice(idx, idx + term.length)) / total;
                var pad = Math.min(2, h * 0.12);      /* 按分の誤差で文字が欠けないよう少し広げる */
                rects.push([x - pad, tx[5] - h * 0.22, x + w + pad, tx[5] + h * 0.85]);
                from = idx + term.length;
              }
            });
          });
          if (rects.length) {
            st.hits[i] = rects; st.hitPages.push(i); st.hitCount += rects.length;
            drawOverlay(i);
            if (jump && !jumped) { jumped = true; gotoHit(i); cursorToHit(i); }
          }
        }, function () {});
      })(k);
      return chain.then(function () {
        if (st.closed || token !== st.scanToken || quiet) return;   /* quiet: 再読み込み後の付け直し (操作結果の表示を消さない) */
        setStatus(st.hitCount ? ("「" + query + "」 " + st.hitCount + " 箇所 / " + st.hitPages.length + " ページ (n N で移動)")
                              : ("「" + query + "」はこの PDF のページ上では見つかりません"));
      });
    }
    function nextHit(dir) {
      if (!st.hitPages.length) { setStatus("ヒットがありません (/語 で PDF 内検索)"); return; }
      var list = st.hitPages, target = null, i;
      if (dir > 0) { for (i = 0; i < list.length; i++) if (list[i] > st.cur) { target = list[i]; break; } if (target == null) target = list[0]; }
      else { for (i = list.length - 1; i >= 0; i--) if (list[i] < st.cur) { target = list[i]; break; } if (target == null) target = list[list.length - 1]; }
      gotoHit(target);
      cursorToHit(target);
    }
    /* ヒットのある行へカーソルを置く (そのまま i や :s で直せる) */
    function cursorToHit(page) {
      return linesOf(page).then(function (lines) {
        for (var k = 0; k < lines.length; k++) {
          var low = lines[k].text.toLowerCase();
          for (var t = 0; t < st.terms.length; t++) {
            var at = low.indexOf(st.terms[t]);
            if (at >= 0) return setCursor(page, k, at, false);
          }
        }
      });
    }
    function hitsToMarker() {
      var rects = st.hits[st.cur];
      if (!rects || !rects.length) { setStatus("このページに検索ヒットがありません"); return; }
      addAnnot({ type: "highlight", page: st.cur, rects: rects.map(function (r) { return r.slice(); }), color: st.color });
      setStatus("検索ヒット " + rects.length + " 箇所をマーカーにしました (:w で PDF に保存)");
    }

    /* ───────── ポインタ操作 (マーカー / ペン / メモ / 選択・移動) ───────── */
    function bindPointer(P, pageIndex) {
      var drag = null;
      function pos(e) { var r = P.svg.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
      P.svg.addEventListener("pointerdown", function (e) {
        if (e.button != null && e.button > 0) return;
        var p = pos(e), tool = st.tool;
        if (tool === "select") {
          var el = e.target.closest ? e.target.closest(".pv-a") : null;
          var id = el ? parseInt(el.getAttribute("data-id"), 10) : null;
          if (st.sel !== id) { st.sel = id; st.pages.forEach(function (_, i) { drawOverlay(i); }); refreshChrome(); }
          if (id == null || !st.editable) return;
          drag = { kind: "move", start: toPdf(P, p[0], p[1]), last: toPdf(P, p[0], p[1]), moved: false, pid: e.pointerId };
        } else if (!st.editable) {
          return;
        } else if (tool === "highlight") {
          drag = { kind: "highlight", a: p, b: p, pid: e.pointerId,
                   el: svg("rect", { "class": "pv-mark pv-preview", fill: st.color }) };
          P.svg.appendChild(drag.el);
        } else if (tool === "erase") {
          drag = { kind: "erase", a: p, b: p, pid: e.pointerId, color: sampleBg(P, p[0] - 2, p[1] - 2),
                   el: svg("rect", { "class": "pv-preview pv-erasing" }) };
          drag.el.setAttribute("fill", drag.color);
          P.svg.appendChild(drag.el);
        } else if (tool === "textedit") {
          e.preventDefault();
          startTextEdit(P, pageIndex, p);
          return;
        } else if (tool === "ink") {
          drag = { kind: "ink", pts: [p], pid: e.pointerId,
                   el: svg("polyline", { stroke: st.inkColor, "stroke-width": Math.max(1, 2 * st.scale), fill: "none",
                                         "stroke-linecap": "round", "stroke-linejoin": "round" }) };
          P.svg.appendChild(drag.el);
        } else if (tool === "note") {
          e.preventDefault();
          editNote(P, pageIndex, null, p);
          return;
        }
        if (drag) { try { P.svg.setPointerCapture(e.pointerId); } catch (err) {} e.preventDefault(); }
      });
      P.svg.addEventListener("pointermove", function (e) {
        if (!drag || drag.pid !== e.pointerId) return;
        var p = pos(e);
        if (drag.kind === "highlight" || drag.kind === "erase") {
          drag.b = p;
          drag.el.setAttribute("x", Math.min(drag.a[0], p[0])); drag.el.setAttribute("y", Math.min(drag.a[1], p[1]));
          drag.el.setAttribute("width", Math.abs(p[0] - drag.a[0])); drag.el.setAttribute("height", Math.abs(p[1] - drag.a[1]));
        } else if (drag.kind === "ink") {
          var last = drag.pts[drag.pts.length - 1];
          if (Math.abs(p[0] - last[0]) + Math.abs(p[1] - last[1]) < 1.5) return;
          drag.pts.push(p);
          drag.el.setAttribute("points", drag.pts.map(function (x) { return x[0].toFixed(1) + "," + x[1].toFixed(1); }).join(" "));
        } else if (drag.kind === "move") {
          var a = selected(); if (!a) return;
          var now = toPdf(P, p[0], p[1]), dx = now[0] - drag.last[0], dy = now[1] - drag.last[1];
          if (!drag.moved) { if (Math.abs(now[0] - drag.start[0]) + Math.abs(now[1] - drag.start[1]) < 2 / st.scale) return; pushUndo(); drag.moved = true; }
          moveAnnot(a, dx, dy); drag.last = now; st.dirty = true; drawOverlay(pageIndex);
        }
      });
      function finish(e) {
        if (!drag || drag.pid !== e.pointerId) return;
        var d = drag; drag = null;
        try { P.svg.releasePointerCapture(e.pointerId); } catch (err) {}
        if (d.el && d.el.parentNode) d.el.parentNode.removeChild(d.el);
        if (d.kind === "highlight") {
          if (Math.abs(d.b[0] - d.a[0]) < 4 || Math.abs(d.b[1] - d.a[1]) < 3) return;
          var c1 = toPdf(P, d.a[0], d.a[1]), c2 = toPdf(P, d.b[0], d.b[1]);
          addAnnot({ type: "highlight", page: pageIndex, rects: [[c1[0], c1[1], c2[0], c2[1]]], color: st.color });
        } else if (d.kind === "erase") {
          if (Math.abs(d.b[0] - d.a[0]) < 3 || Math.abs(d.b[1] - d.a[1]) < 3) return;
          var e1 = toPdf(P, d.a[0], d.a[1]), e2 = toPdf(P, d.b[0], d.b[1]);
          addAnnot({ type: "erase", page: pageIndex, rects: [[e1[0], e1[1], e2[0], e2[1]]], color: d.color });
        } else if (d.kind === "ink") {
          var flat = [];
          d.pts.forEach(function (pt) { var c = toPdf(P, pt[0], pt[1]); flat.push(c[0], c[1]); });
          addAnnot({ type: "ink", page: pageIndex, paths: [flat], color: st.inkColor, width: 2 });
        } else if (d.kind === "move" && d.moved) {
          refreshChrome();
        }
      }
      /* メモ ツールでは既定のフォーカス移動を止め、入力欄がすぐ文字を受け取れるようにする */
      P.svg.addEventListener("mousedown", function (e) { if ((st.tool === "note" || st.tool === "textedit") && st.editable) e.preventDefault(); });
      P.svg.addEventListener("pointerup", finish);
      P.svg.addEventListener("pointercancel", finish);
      P.svg.addEventListener("dblclick", function (e) {
        if (!st.editable) return;
        /* ドラッグ用のポインタ捕捉でイベントの宛先が SVG 全体になるため、座標から要素を引き直す */
        var hit = document.elementFromPoint(e.clientX, e.clientY) || e.target;
        var el = hit.closest ? hit.closest(".pv-note,.pv-textedit") : null;
        if (!el) return;
        var id = parseInt(el.getAttribute("data-id"), 10);
        var a = st.annots.filter(function (x) { return x._id === id; })[0];
        if (!a) return;
        if (a.type === "note") editNote(P, pageIndex, a, null); else editTextAnnot(P, pageIndex, a);
      });
    }

    /* ページ画像の画素から背景色を拾う (消去・文字修正で元の文字を隠す色。取れなければ白) */
    function sampleBg(P, vx, vy) {
      try {
        var c = P.canvas, k = c.width / P.viewport.width;
        var x = Math.max(0, Math.min(c.width - 1, Math.round(vx * k))), y = Math.max(0, Math.min(c.height - 1, Math.round(vy * k)));
        var d = c.getContext("2d").getImageData(x, y, 1, 1).data;
        if (d[3] < 200) return "#ffffff";
        return "#" + [d[0], d[1], d[2]].map(function (v) { return ("0" + v.toString(16)).slice(-2); }).join("");
      } catch (e) { return "#ffffff"; }
    }

    /* ───────── 入力欄 (メモ / 文字修正 共通) ─────────
       Enter で確定 / Shift+Enter で改行 / Esc で取り消し。日本語変換中の Enter は確定しない。 */
    var noteBox = null;
    function openEditor(P, o) {
      if (noteBox) noteBox.commit();
      var ta = document.createElement("textarea");
      ta.className = "pv-noteedit" + (o.plain ? " pv-plainedit" : ""); ta.value = o.value || "";
      ta.style.left = o.vx + "px"; ta.style.top = o.vy + "px"; ta.style.fontSize = o.fontPx + "px";
      if (o.width) ta.style.width = Math.max(120, o.width) + "px";
      ta.placeholder = o.placeholder || "";
      P.wrap.appendChild(ta);
      var done = false;
      function close() { noteBox = null; if (ta.parentNode) ta.parentNode.removeChild(ta); elBody.focus(); }
      function finish() { if (typeof o.onEnd === "function") o.onEnd(); }
      function commit() {
        if (done) return; done = true;
        var text = ta.value.replace(/\s+$/, ""), caret = ta.selectionStart || 0;
        close(); finish(); o.onCommit(text, caret);
      }
      function cancel() { if (done) return; done = true; close(); finish(); }
      ta.addEventListener("keydown", function (e) {
        e.stopPropagation();
        if (e.isComposing || e.keyCode === 229) return;
        if (o.vim) {
          /* Vim の挿入モード: Esc (または Ctrl-[) で確定して NORMAL へ。Enter は改行 */
          if (e.key === "Escape" || (e.ctrlKey && e.key === "[")) { e.preventDefault(); commit(); }
          return;
        }
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); commit(); }
        else if (e.key === "Escape") { e.preventDefault(); cancel(); }
      });
      ta.addEventListener("blur", function () { setTimeout(commit, 0); });
      noteBox = { commit: commit, cancel: cancel, el: ta };
      ta.focus();
      if (o.caret != null) { try { ta.setSelectionRange(o.caret, o.caret); } catch (e) {} }
      else if (o.value) { try { ta.select(); } catch (e) {} }
      setTimeout(function () { if (!done && document.activeElement !== ta) ta.focus(); }, 0);
    }
    function editNote(P, pageIndex, existing, at) {
      var vx, vy, size = existing ? (existing.size || 12) : 12;
      if (existing) { var v = toView(P, existing.x, existing.y); vx = v[0]; vy = v[1]; } else { vx = at[0]; vy = at[1]; }
      openEditor(P, { vx: vx, vy: vy, fontPx: size * st.scale, value: existing ? existing.text : "", placeholder: "メモ (Enter で確定)",
        onCommit: function (text) {
          if (existing) {
            if (text === existing.text) return;
            pushUndo();
            if (!text.trim()) { st.annots = st.annots.filter(function (x) { return x !== existing; }); st.sel = null; }
            else existing.text = text;
            touch(pageIndex);
          } else if (text.trim()) {
            var c = toPdf(P, vx, vy);
            addAnnot({ type: "note", page: pageIndex, x: c[0], y: c[1], text: text, size: size, color: "#102030" });
            st.tool = "select"; setStatus("");
          }
        } });
    }

    /* ───────── ✏ 文字修正 ─────────
       クリックした位置に (1) 自分が直した文字があれば再編集、(2) PDF の文字があれば
       それを隠して打ち直す、(3) 何もなければその場所に文字を追加する。 */
    function fontKind(family) { return /mono|courier/i.test(family || "") ? "mono" : (/sans|gothic|helvet|arial/i.test(family || "") ? "sans" : "serif"); }
    function itemsOf(P) {
      if (!P.items) {
        P.items = P.page.getTextContent().then(function (tc) {
          return tc.items.filter(function (it) { return it.str && it.str.trim(); }).map(function (it) {
            var tx = it.transform, h = it.height || Math.hypot(tx[2], tx[3]) || 10;
            return { str: it.str, x: tx[4], y: tx[5], size: h, width: it.width,
                     rect: [tx[4], tx[5] - h * 0.27, tx[4] + it.width, tx[5] + h * 0.92],
                     font: fontKind(tc.styles && tc.styles[it.fontName] && tc.styles[it.fontName].fontFamily) };
          });
        }, function () { return []; });
      }
      return P.items;
    }
    function inRect(r, x, y) { return x >= r[0] && x <= r[2] && y >= r[1] && y <= r[3]; }
    function startTextEdit(P, pageIndex, p) {
      var c = toPdf(P, p[0], p[1]);
      for (var i = st.annots.length - 1; i >= 0; i--) {
        var a = st.annots[i];
        if (a.page === pageIndex && a.type === "textedit" && inRect(Edit.annotRect(a), c[0], c[1])) { editTextAnnot(P, pageIndex, a); return; }
      }
      itemsOf(P).then(function (items) {
        if (st.closed || st.tool !== "textedit") return;
        var hit = null;
        for (var k = 0; k < items.length; k++) if (inRect(items[k].rect, c[0], c[1])) { hit = items[k]; break; }
        if (hit) {
          var v = viewRect(P, hit.rect), cover = [hit.rect[0] - 1, hit.rect[1], hit.rect[2] + 1, hit.rect[3]];
          var bg = sampleBg(P, v.x - 3, v.y - 2);
          openEditor(P, { vx: v.x, vy: v.y, fontPx: hit.size * st.scale, width: v.w + 30, value: hit.str, plain: true,
            onCommit: function (text) {
              if (text === hit.str.replace(/\s+$/, "")) return;          /* 変えていなければ何もしない */
              addAnnot({ type: "textedit", page: pageIndex, x: hit.x, y: hit.y, text: text, size: hit.size,
                         color: "#000000", font: hit.font, cover: cover, bg: bg });
              setStatus(text.trim() ? "文字を書き換えました (:w で PDF に保存)" : "文字を消しました (:w で PDF に保存)");
            } });
        } else {
          openEditor(P, { vx: p[0], vy: p[1] - 12 * st.scale, fontPx: 12 * st.scale, value: "", plain: true, placeholder: "文字を追加 (Enter で確定)",
            onCommit: function (text) {
              if (!text.trim()) return;
              addAnnot({ type: "textedit", page: pageIndex, x: c[0], y: c[1], text: text, size: 12, color: "#000000", font: "sans", cover: null });
              setStatus("文字を追加しました (:w で PDF に保存)");
            } });
        }
      });
    }
    function editTextAnnot(P, pageIndex, a) {
      var v = toView(P, a.x, a.y + (a.size || 12) * 0.92);
      openEditor(P, { vx: v[0], vy: v[1], fontPx: (a.size || 12) * st.scale, value: a.text, plain: true,
        onCommit: function (text) {
          if (text === a.text) return;
          pushUndo();
          if (!text.trim() && !a.cover) { st.annots = st.annots.filter(function (x) { return x !== a; }); st.sel = null; }
          else a.text = text;
          touch(pageIndex);
        } });
    }

    /* ───────── ページ操作 / 焼き込み (PDF 本体を書き換えるので、表示を読み込み直す) ───────── */
    function docParams() {
      var params = opts.docParams ? Object.assign({}, opts.docParams) : {
        CMapReaderFactory: assetFactory(base, "cmap"), cMapUrl: "bundle/", cMapPacked: true,
        StandardFontDataFactory: assetFactory(base, "font"), standardFontDataUrl: "bundle/"
      };
      params.data = st.baseBytes.slice();      /* pdf.js はバッファを占有するので複製を渡す */
      params.isEvalSupported = false;          /* フォント経由のコード実行 (CVE-2024-4367) を封じる (上書き不可) */
      return params;
    }
    function openDoc() {
      return (typeof opts.loadPdfJs === "function" ? opts.loadPdfJs() : ensurePdfJs(base))
        .then(function (pdfjs) { return pdfjs.getDocument(docParams()).promise; });
    }
    function reloadDoc(keepPage) {
      st.busy = true;
      var old = st.pdf, query = st.lastQuery;
      if (io) { io.disconnect(); io = null; }
      st.pages.forEach(function (P) { if (P.task) { try { P.task.cancel(); } catch (e) {} } });
      st.pages = []; elPages.innerHTML = ""; st.hits = {}; st.hitPages = []; st.hitCount = 0; st.scanToken++;
      return openDoc().then(function (pdf) {
        if (old) { try { old.destroy(); } catch (e) {} }
        st.pdf = pdf;
        return buildPages(true);
      }).then(function () {
        st.busy = false;
        if (st.closed) return;
        setupObserver();
        gotoPage(Math.max(0, Math.min(st.pages.length - 1, keepPage | 0)));
        st.vc = null; st.vcLine = null;         /* ページ構成が変わったのでカーソルは置き直す */
        refreshChrome();
        if (query) scanHits(query, false, true);
      }, function (err) { st.busy = false; setStatus("PDF を表示できません: " + (err && err.message || err)); });
    }
    function pageOperation(op, done) {
      if (!st.editable) { setStatus("読み取り専用のため編集できません"); return Promise.resolve(); }
      if (st.busy || !st.pages.length) return Promise.resolve();
      if (noteBox) noteBox.commit();
      st.busy = true; setStatus("ページを編集中…");
      var count = st.pages.length;
      return ensurePdfLib(pdfLibUrl).then(function (L) { return Edit.pageOp(L, st.baseBytes, op); }).then(function (r) {
        pushUndo();
        st.baseBytes = r.bytes;
        st.annots = Edit.remapAnnots(st.annots, op);
        (r.annots || []).forEach(function (a) { a._id = st.nextId++; st.annots.push(a); });
        st.sel = null; st.dirty = true; st.closeArmed = false;
        var go = op.op === "move" ? op.to : op.op === "blank" ? op.at : op.op === "merge" ? count : Math.min(op.page | 0, count - 1);
        return reloadDoc(go).then(function () { setStatus(done(r) + " (u で取り消し / :w で保存)"); });
      }, function (err) { st.busy = false; setStatus("ページ操作エラー: " + (err && err.message || err)); });
    }
    function rotatePage() { return pageOperation({ op: "rotate", page: st.cur, delta: 90 }, function () { return (st.cur + 1) + " ページ目を回転しました"; }); }
    function deletePage() {
      if (st.pages.length <= 1) { setStatus("最後の 1 ページは削除できません"); return Promise.resolve(); }
      var n = st.cur + 1;
      return pageOperation({ op: "delete", page: st.cur }, function () { return n + " ページ目を削除しました"; });
    }
    function movePage(to) {
      if (to < 0 || to >= st.pages.length || to === st.cur) { setStatus("これ以上は動かせません"); return Promise.resolve(); }
      var from = st.cur + 1;
      return pageOperation({ op: "move", page: st.cur, to: to }, function () { return from + " ページ目を " + (to + 1) + " ページ目へ移動しました"; });
    }
    function blankPage() { return pageOperation({ op: "blank", at: st.cur + 1 }, function () { return "空白ページを挿入しました"; }); }
    function mergePdf(bytes) {
      return pageOperation({ op: "merge", bytes: bytes }, function (r) { return "PDF を結合しました (+" + r.added + " ページ)"; });
    }
    function flattenAll() {
      if (!st.editable) { setStatus("読み取り専用のため編集できません"); return Promise.resolve(); }
      if (st.busy) return Promise.resolve();
      if (noteBox) noteBox.commit();
      var clean = st.annots.map(function (a) { return Edit.normalize(a); }).filter(Boolean);
      if (!clean.length) { setStatus("焼き込む書き込みがありません"); return Promise.resolve(); }
      st.busy = true; setStatus("焼き込み中…");
      return ensurePdfLib(pdfLibUrl).then(function (L) { return Edit.flatten(L, st.baseBytes, clean); }).then(function (out) {
        pushUndo();
        st.baseBytes = out; st.annots = []; st.sel = null; st.dirty = true;
        return reloadDoc(st.cur).then(function () { setStatus(clean.length + " 件をページ本体に焼き込みました (u で取り消し / :w で保存)"); });
      }, function (err) { st.busy = false; setStatus("焼き込みエラー: " + (err && err.message || err)); });
    }
    var elMerge = q(".pv-mergein");
    elMerge.addEventListener("change", function () {
      var f = elMerge.files && elMerge.files[0];
      elMerge.value = "";
      if (!f) return;
      f.arrayBuffer().then(function (buf) { return mergePdf(new Uint8Array(buf)); });
    });

    /* ───────── Vim モード: 文字カーソルと行の編集 ─────────
       「行」= PDF の文字のまとまり (pdf.js のテキスト片) に、自分の文字修正を重ねたもの。
       直した行は textedit (cover つき) として持ち、元の文字と同じ内容に戻せば修正は消える。
       o / O で足した行は cover なしの textedit。 */
    function lineWidth(a) { var b = Edit.textBox(a); return b[2] - b[0]; }
    function linesOf(pi) {
      var P = st.pages[pi];
      if (!P) return Promise.resolve([]);
      return itemsOf(P).then(function (items) {
        var used = {}, lines = items.map(function (it) {
          var an = null;
          for (var i = 0; i < st.annots.length; i++) {
            var a = st.annots[i];
            if (a.type === "textedit" && a.page === pi && a.cover && !used[a._id] &&
                Math.abs(a.x - it.x) < 0.01 && Math.abs(a.y - it.y) < 0.01) { an = a; used[a._id] = 1; break; }
          }
          return { item: it, annot: an, x: it.x, y: it.y, size: it.size, font: it.font,
                   text: an ? an.text : it.str.replace(/\s+$/, ""), width: an ? lineWidth(an) : it.width };
        });
        st.annots.forEach(function (a) {
          if (a.type === "textedit" && a.page === pi && !a.cover)
            lines.push({ item: null, annot: a, x: a.x, y: a.y, size: a.size, font: a.font, text: a.text, width: lineWidth(a) });
        });
        lines.sort(function (p, q) { return Math.abs(q.y - p.y) > Math.min(p.size, q.size) * 0.5 ? q.y - p.y : p.x - q.x; });
        return lines;
      });
    }
    function firstLine(ln) { return String(ln.text).split("\n")[0]; }
    function showCursor(scroll) {
      var vc = st.vc, P = vc && st.pages[vc.page], ln = st.vcLine;
      st.pages.forEach(function (_, i) { drawOverlay(i); });
      if (!scroll || !P || !ln) return;
      var r = viewRect(P, [ln.x, ln.y - ln.size * 0.3, ln.x + ln.width, ln.y + ln.size]);
      var top = P.wrap.offsetTop + r.y, bottom = top + r.h, pad = 60;
      if (top - pad < elBody.scrollTop) elBody.scrollTop = Math.max(0, top - pad);
      else if (bottom + pad > elBody.scrollTop + elBody.clientHeight) elBody.scrollTop = bottom + pad - elBody.clientHeight;
      var left = P.wrap.offsetLeft + r.x;
      if (left < elBody.scrollLeft || left > elBody.scrollLeft + elBody.clientWidth - 40) elBody.scrollLeft = Math.max(0, left - 80);
      if (st.cur !== vc.page) { st.cur = vc.page; refreshChrome(); }
    }
    /* カーソルを (page, k 行目, c 文字目) へ。行が無いページでは false */
    function setCursor(page, k, c, scroll) {
      return linesOf(page).then(function (lines) {
        if (!lines.length) return false;
        k = Math.max(0, Math.min(lines.length - 1, k));
        var len = firstLine(lines[k]).length;
        st.vc = { page: page, k: k, c: Math.max(0, Math.min(Math.max(0, len - 1), c | 0)) };
        st.vcLine = lines[k];
        showCursor(scroll !== false);
        return true;
      });
    }
    /* いまのカーソル行で fn(行, 行の一覧) を実行。カーソルが無ければ表示中のページの先頭に置く */
    function withCursor(fn) {
      var vc = st.vc, page = (vc && st.pages[vc.page]) ? vc.page : st.cur;
      return linesOf(page).then(function (lines) {
        if (!lines.length) { setStatus("このページには文字がありません (:text でクリックした場所に文字を追加できます)"); return null; }
        var k = (vc && vc.page === page) ? Math.max(0, Math.min(lines.length - 1, vc.k)) : 0;
        if (!vc || vc.page !== page) st.vc = { page: page, k: k, c: 0 };
        else st.vc.k = k;
        st.vcLine = lines[k];
        return fn(lines[k], lines, page, k);
      });
    }
    function refreshCursor() { if (st.vc) return setCursor(st.vc.page, st.vc.k, st.vc.c, false); return Promise.resolve(); }
    function moveCursor(what) {
      return withCursor(function (ln, lines, page, k) {
        var c = st.vc.c, len = firstLine(ln).length;
        if (what === "h") { if (c > 0) return setCursor(page, k, c - 1); return stepLine(page, k, -1, "end"); }
        if (what === "l") { if (c < len - 1) return setCursor(page, k, c + 1); return stepLine(page, k, 1, 0); }
        if (what === "0") return setCursor(page, k, 0);
        if (what === "$") return setCursor(page, k, len - 1);
        if (what === "j") return stepLine(page, k, 1, c);
        if (what === "k") return stepLine(page, k, -1, c);
        if (what === "w") return stepLine(page, k, 1, 0);
        if (what === "b") { if (c > 0) return setCursor(page, k, 0); return stepLine(page, k, -1, 0); }
      });
    }
    /* 行を dir (+1/-1) へ。ページの端では文字のある隣のページへ続く */
    function stepLine(page, k, dir, col) {
      function place(pg, kk, lines) { return setCursor(pg, kk, col === "end" ? firstLine(lines[kk]).length - 1 : col); }
      return linesOf(page).then(function (lines) {
        var nk = k + dir;
        if (nk >= 0 && nk < lines.length) return place(page, nk, lines);
        function hop(pg) {
          if (pg < 0 || pg >= st.pages.length) return false;
          return linesOf(pg).then(function (ls) { return ls.length ? place(pg, dir > 0 ? 0 : ls.length - 1, ls) : hop(pg + dir); });
        }
        return hop(page + dir);
      });
    }
    function cursorToPage(page) {
      gotoPage(page);
      return linesOf(st.cur).then(function (lines) {
        if (lines.length) { st.vc = { page: st.cur, k: 0, c: 0 }; st.vcLine = lines[0]; }
        else { st.vc = null; st.vcLine = null; }
        st.pages.forEach(function (_, i) { drawOverlay(i); });
      });
    }
    /* 行の文字を text にする (noUndo: 呼び出し側でまとめて 1 回の取り消しにする)。変わったら true */
    function setLineText(page, ln, text, noUndo) {
      var P = st.pages[page];
      text = String(text).replace(/\s+$/, "");
      if (text === ln.text) return false;
      if (!noUndo) pushUndo();
      if (ln.annot) {
        if (ln.item && text === ln.item.str.replace(/\s+$/, "")) st.annots = st.annots.filter(function (x) { return x !== ln.annot; });   /* 元どおり → 修正を外す */
        else if (!ln.item && !text.trim()) st.annots = st.annots.filter(function (x) { return x !== ln.annot; });
        else ln.annot.text = text;
      } else {
        var it = ln.item, v = viewRect(P, it.rect);
        var n = Edit.normalize({ type: "textedit", page: page, x: it.x, y: it.y, text: text, size: it.size, color: "#000000", font: it.font,
                                 cover: [it.rect[0] - 1, it.rect[1], it.rect[2] + 1, it.rect[3]], bg: sampleBg(P, v.x - 3, v.y - 2) });
        n._id = st.nextId++; st.annots.push(n);
      }
      st.sel = null; touch(page);
      return true;
    }
    function needEdit() { if (!st.editable) { setStatus("読み取り専用のため編集できません"); return false; } return !st.busy; }

    /* INSERT モード: 行の上に入力欄を重ねて直接打つ (Esc で確定)。kind = i a I A cc o O */
    function startInsert(kind) {
      if (!needEdit()) return;
      withCursor(function (ln, lines, page, k) {
        var P = st.pages[page], text = ln.text, c = st.vc.c, size = ln.size || 12;
        var fresh = kind === "o" || kind === "O";
        var y = fresh ? ln.y + (kind === "o" ? -1 : 1) * size * 1.35 : ln.y;
        var v = viewRect(P, [ln.x, y - size * 0.27, ln.x + Math.max(ln.width, size * 6), y + size * 0.92]);
        var caret = kind === "i" ? c : kind === "a" ? Math.min(text.length, c + 1) : kind === "I" ? 0 : text.length;
        st.mode = "insert"; st.status = ""; showCursor(true); refreshChrome();
        openEditor(P, {
          vim: true, plain: true, vx: v.x, vy: v.y, fontPx: size * st.scale, width: v.w + 80,
          value: fresh || kind === "cc" ? "" : text, caret: fresh || kind === "cc" ? 0 : caret,
          onEnd: function () { st.mode = "normal"; },
          onCommit: function (out, at) {
            if (fresh) {
              if (out.trim()) {
                pushUndo();
                var n = Edit.normalize({ type: "textedit", page: page, x: ln.x, y: y, text: out, size: size, color: "#000000", font: ln.font, cover: null });
                n._id = st.nextId++; st.annots.push(n); touch(page);
                setStatus("行を追加しました (:w で PDF に保存)");
              }
              return linesOf(page).then(function (ls) {
                var nk = k;
                for (var i = 0; i < ls.length; i++) if (ls[i].annot && Math.abs(ls[i].y - y) < 0.01 && Math.abs(ls[i].x - ln.x) < 0.01) nk = i;
                return setCursor(page, nk, Math.max(0, at - 1));
              });
            }
            if (setLineText(page, ln, out)) setStatus("文字を書き換えました (:w で PDF に保存)");
            return setCursor(page, k, Math.max(0, at - 1));
          }
        });
      });
    }
    function deleteChar() {
      if (!needEdit()) return;
      withCursor(function (ln, lines, page, k) {
        var t = ln.text, c = st.vc.c;
        if (!t.length) return;
        setLineText(page, ln, t.slice(0, c) + t.slice(c + 1));
        return setCursor(page, k, c);
      });
    }
    function deleteToEnd() {
      if (!needEdit()) return;
      withCursor(function (ln, lines, page, k) { setLineText(page, ln, ln.text.slice(0, st.vc.c)); return setCursor(page, k, st.vc.c - 1); });
    }
    function deleteLine() {
      if (!needEdit()) return;
      withCursor(function (ln, lines, page, k) {
        st.reg = ln.text;
        if (setLineText(page, ln, "")) setStatus("行を削除しました (u で取り消し)");
        return setCursor(page, k, 0);
      });
    }
    function yankLine() { withCursor(function (ln) { st.reg = ln.text; setStatus("1 行ヤンクしました (p で下に貼り付け)"); }); }
    function pasteLine() {
      if (!needEdit()) return;
      if (!st.reg) { setStatus("貼り付ける行がありません (yy でヤンク)"); return; }
      withCursor(function (ln, lines, page, k) {
        pushUndo();
        var y = ln.y - ln.size * 1.35;
        var n = Edit.normalize({ type: "textedit", page: page, x: ln.x, y: y, text: st.reg, size: ln.size, color: "#000000", font: ln.font, cover: null });
        n._id = st.nextId++; st.annots.push(n); touch(page);
        return linesOf(page).then(function (ls) {
          var nk = k;
          for (var i = 0; i < ls.length; i++) if (ls[i].annot === n) nk = i;
          return setCursor(page, nk, 0);
        });
      });
    }
    /* :s/旧/新/[g][i] (カーソル行) と :%s/旧/新/[g][i] (全ページ)。旧は正規表現 (不正なら文字どおり) */
    function substitute(all, pat, repl, flags) {
      if (!needEdit()) return Promise.resolve(0);
      var re, f = (/g/.test(flags) ? "g" : "") + (/i/.test(flags) ? "i" : "");
      try { re = new RegExp(pat, f); } catch (e) { re = new RegExp(pat.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), f); }
      var to = repl.replace(/\$/g, "$$$$").replace(/\\(\d)/g, "$$$1").replace(/\\&/g, "\u0000").replace(/&/g, "$$&").replace(/\u0000/g, "&");
      var count = 0, pagesHit = {};
      pushUndo();
      function onPage(pg, only) {
        return linesOf(pg).then(function (lines) {
          lines.forEach(function (ln, k) {
            if (only != null && k !== only) return;
            var out = ln.text.replace(re, to);
            if (out !== ln.text && setLineText(pg, ln, out, true)) { count++; pagesHit[pg] = 1; }
          });
        });
      }
      var chain;
      if (all) { chain = Promise.resolve(); st.pages.forEach(function (_, pg) { chain = chain.then(function () { return onPage(pg, null); }); }); }
      else chain = withCursor(function (ln, lines, page, k) { return onPage(page, k); });
      return Promise.resolve(chain).then(function () {
        if (!count) { st.undo.pop(); setStatus("パターンが見つかりません: " + pat); return 0; }
        setStatus(count + " 行を置換しました" + (all ? " (" + Object.keys(pagesHit).length + " ページ)" : "") + " — u で取り消し / :w で保存");
        return refreshCursor().then(function () { return count; });
      });
    }
    function noteAtCursor(text) {
      if (!needEdit()) return;
      withCursor(function (ln, lines, page) {
        addAnnot({ type: "note", page: page, x: ln.x, y: ln.y - ln.size * 0.5, text: text, size: 12, color: "#102030" });
        setStatus("カーソル行にメモを付けました (:w で PDF に保存)");
      });
    }
    function markCursorLine() {
      if (!needEdit()) return;
      withCursor(function (ln, lines, page) {
        addAnnot({ type: "highlight", page: page, rects: [[ln.x, ln.y - ln.size * 0.27, ln.x + ln.width, ln.y + ln.size * 0.92]], color: st.color });
        setStatus("カーソル行にマーカーを引きました (:w で PDF に保存)");
      });
    }

    /* ───────── 保存 ───────── */
    function save(thenClose) {
      if (!st.editable) { setStatus("この PDF は保存できません (読み取り専用)"); return Promise.resolve({ error: "readonly" }); }
      if (st.busy) return Promise.resolve({ error: "busy" });
      if (noteBox) noteBox.commit();
      st.busy = true; setStatus("PDF に保存中…");
      var clean = st.annots.map(function (a) { return Edit.normalize(a); }).filter(Boolean);
      return ensurePdfLib(pdfLibUrl).then(function (L) {
        return Edit.applyAnnotations(L, st.baseBytes, clean);
      }).then(function (out) {
        return Promise.resolve(opts.onSave(out, { annotations: clean.length }));
      }).then(function (r) {
        st.busy = false;
        if (r && r.error) { setStatus("保存エラー: " + r.error); return r; }
        st.dirty = false;
        setStatus("PDF に保存しました (注釈 " + clean.length + " 件)" + (r && r.note ? " — " + r.note : ""));
        if (thenClose) teardown();
        return r || { ok: true };
      }, function (err) {
        st.busy = false;
        setStatus("保存エラー: " + (err && err.message || err));
        return { error: String(err && err.message || err) };
      });
    }

    /* ───────── キーボード ───────── */
    function execCmd(line) {
      if (line[0] === "/") { var s = line.slice(1); if (s) { setStatus("検索中: " + s); scanHits(s, true); } return; }
      var c = line.slice(1);
      if (c === "w") { save(false); return; }
      if (c === "wq" || c === "x") { if (st.editable) save(true); else teardown(); return; }
      if (c === "q") { if (st.dirty && !opts.keepOnClose) setStatus("未保存の注釈があります (:w で保存 / :q! で破棄)"); else teardown(); return; }
      if (c === "q!") { teardown(); return; }
      if (/^\d+$/.test(c)) { cursorToPage(parseInt(c, 10) - 1); return; }
      var sub = /^(%?)s(.)/.exec(c);
      if (sub && !/[A-Za-z0-9\s]/.test(sub[2])) {
        /* 区切り文字で 旧 / 新 / フラグ に分ける (\ で区切り文字そのものを書ける) */
        var d = sub[2], rest = c.slice(sub[0].length), parts = [""], esc = false;
        for (var ci = 0; ci < rest.length; ci++) {
          var ch = rest[ci];
          if (esc) { parts[parts.length - 1] += (ch === d ? d : "\\" + ch); esc = false; }
          else if (ch === "\\") esc = true;
          else if (ch === d && parts.length < 3) parts.push("");
          else parts[parts.length - 1] += ch;
        }
        if (!parts[0]) { setStatus("置換するパターンがありません (:s/旧/新/)"); return; }
        substitute(sub[1] === "%", parts[0], parts[1] || "", parts[2] || "");
        return;
      }
      if (c === "d" || c === "delete") { deleteLine(); return; }
      if (c === "u" || c === "undo") { if (st.editable) undo(); return; }
      if (c === "hl") { markCursorLine(); return; }
      var nt = /^note\s+(.+)$/.exec(c);
      if (nt) { noteAtCursor(nt[1]); return; }
      var toolName = { marker: "highlight", pen: "ink", note: "note", text: "textedit", erase: "erase", select: "select" }[c];
      if (toolName) { setTool(toolName); refreshChrome(); return; }
      if (c === "rotate") { rotatePage(); return; }
      if (c === "delpage") { deletePage(); return; }
      if (c === "blank") { blankPage(); return; }
      if (c === "flatten") { flattenAll(); return; }
      if (c === "merge") { if (st.editable) elMerge.click(); return; }
      var mv = /^move\s+(\d+)$/.exec(c);
      if (mv) { movePage(parseInt(mv[1], 10) - 1); return; }
      setStatus("未対応のコマンド: :" + c);
    }
    function setTool(t) {
      if (!st.editable && t !== "select") { setStatus("読み取り専用のため編集できません"); return; }
      st.tool = t;
      setStatus(({ select: "", highlight: "ドラッグした範囲にマーカーを引きます", ink: "ドラッグで手書きします", note: "書き込みたい場所をクリックしてください",
                   textedit: "直したい文字をクリックして書き換えます (何もない所をクリックすると文字を追加)", erase: "消したい範囲をドラッグします" })[t]);
    }
    function onKey(e) {
      if (st.closed) return;
      var tag = e.target && e.target.tagName;
      if (noteBox) { if (document.activeElement !== noteBox.el) noteBox.el.focus(); return; }   /* メモ入力中はキーを奪わない */
      if (tag === "TEXTAREA" || tag === "INPUT") return;
      var k = e.key;
      if (e.ctrlKey && (k === "d" || k === "u" || k === "f" || k === "b")) k = "Ctrl-" + k;
      else if (e.ctrlKey || e.metaKey || e.altKey) return;
      e.stopPropagation();
      st.closeArmed = false;
      var handled = true, half = elBody.clientHeight / 2;
      /* 2 ストローク (gg dd yy cc) */
      if (st.pending) {
        var pend = st.pending; st.pending = "";
        if (pend === k) {
          e.preventDefault();
          if (k === "g") cursorToPage(0);
          else if (k === "d") deleteLine();
          else if (k === "y") yankLine();
          else if (k === "c") startInsert("cc");
          refreshChrome();
          return;
        }
      }
      switch (k) {
        case "h": moveCursor("h"); break;
        case "l": moveCursor("l"); break;
        case "j": moveCursor("j"); break;
        case "k": moveCursor("k"); break;
        case "w": moveCursor("w"); break;
        case "b": moveCursor("b"); break;
        case "0": moveCursor("0"); break;
        case "$": moveCursor("$"); break;
        case "ArrowDown": elBody.scrollTop += 70; break;
        case "ArrowUp": elBody.scrollTop -= 70; break;
        case "Ctrl-d": case " ": elBody.scrollTop += half; break;
        case "Ctrl-u": elBody.scrollTop -= half; break;
        case "]": case "ArrowRight": case "PageDown": case "Ctrl-f": cursorToPage(st.cur + 1); break;
        case "[": case "ArrowLeft": case "PageUp": case "Ctrl-b": cursorToPage(st.cur - 1); break;
        case "g": case "d": case "y": case "c": st.pending = k; break;
        case "G": cursorToPage(st.pages.length - 1); break;
        case "i": case "a": case "I": case "A": case "o": case "O": startInsert(k); break;
        case "S": startInsert("cc"); break;
        case "D": deleteToEnd(); break;
        case "p": pasteLine(); break;
        case "n": nextHit(1); break;
        case "N": nextHit(-1); break;
        case "+": case "=": setScale(st.scale * 1.2); break;
        case "-": setScale(st.scale / 1.2); break;
        case "v": setTool("select"); break;
        case "m": setTool("highlight"); break;
        case "R": rotatePage(); break;
        case "<": movePage(st.cur - 1); break;
        case ">": movePage(st.cur + 1); break;
        case "F": flattenAll(); break;
        case "M": if (st.editable) hitsToMarker(); break;
        case "x": if (st.sel != null) { if (st.editable) removeSelected(); } else deleteChar(); break;
        case "Delete": if (st.editable) removeSelected(); break;
        case "u": if (st.editable) undo(); break;
        case "t": case "Tab": if (typeof opts.onTextMode === "function") { if (st.dirty && !confirmDiscard()) break; teardown(); opts.onTextMode(); } break;
        case ":": startCmd(":"); break;
        case "/": startCmd("/"); break;
        case "Escape": if (st.tool !== "select") setTool("select"); else if (st.sel != null) { st.sel = null; st.pages.forEach(function (_, i) { drawOverlay(i); }); } break;
        default: handled = false;
      }
      if (handled) { e.preventDefault(); refreshChrome(); }
    }
    /* コマンドライン (:w :q :<ページ> /検索語) は本物の入力欄なので、日本語変換 (IME) や
       ソフトキーボードでもそのまま打てる */
    function startCmd(prefix) {
      st.mode = "command"; st.status = "";
      elCmd.value = prefix; refreshChrome();
      elCmd.focus();
      try { elCmd.setSelectionRange(prefix.length, prefix.length); } catch (e) {}
    }
    function endCmd() { st.mode = "normal"; elCmd.value = ""; refreshChrome(); elBody.focus(); }
    elCmd.addEventListener("keydown", function (e) {
      e.stopPropagation();
      if (e.isComposing || e.keyCode === 229) return;
      if (e.key === "Enter") { e.preventDefault(); var line = elCmd.value; endCmd(); if (line.length > 1) execCmd(line); }
      else if (e.key === "Escape") { e.preventDefault(); endCmd(); }
    });
    elCmd.addEventListener("input", function () { if (!/^[:\/]/.test(elCmd.value)) endCmd(); });
    elCmd.addEventListener("blur", function () { if (st.mode === "command") setTimeout(function () { if (st.mode === "command" && document.activeElement !== elCmd) endCmd(); }, 0); });

    function confirmDiscard() {
      if (opts.keepOnClose) return true;          /* 注釈は呼び出し側が保持するので破棄にならない */
      if (st.closeArmed) return true;
      st.closeArmed = true; setStatus("未保存の注釈があります — もう一度押すと破棄します (:w で保存)");
      return false;
    }

    ov.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("button") : null;
      if (!b || b.disabled) return;
      var tool = b.getAttribute("data-tool"), act = b.getAttribute("data-act");
      if (tool) { setTool(tool); refreshChrome(); }
      else if (act === "prev") gotoPage(st.cur - 1);
      else if (act === "next") gotoPage(st.cur + 1);
      else if (act === "zin") setScale(st.scale * 1.2);
      else if (act === "zout") setScale(st.scale / 1.2);
      else if (act === "del") removeSelected();
      else if (act === "undo") undo();
      else if (act === "save") save(false);
      else if (act === "hitmark") hitsToMarker();
      else if (act === "rot") rotatePage();
      else if (act === "pgup") movePage(st.cur - 1);
      else if (act === "pgdn") movePage(st.cur + 1);
      else if (act === "blank") blankPage();
      else if (act === "pgdel") deletePage();
      else if (act === "flatten") flattenAll();
      else if (act === "merge") elMerge.click();
      if (tool || act) elBody.focus();
    });
    q(".cv-x").addEventListener("click", function () { if (st.dirty && !confirmDiscard()) return; teardown(); });

    function teardown() {
      if (st.closed) return;
      st.closed = true;
      document.removeEventListener("keydown", onKey, true);
      if (io) io.disconnect();
      st.pages.forEach(function (P) { if (P.task) { try { P.task.cancel(); } catch (e) {} } });
      if (st.pdf) { try { st.pdf.destroy(); } catch (e) {} }
      if (ov.parentNode) ov.parentNode.removeChild(ov);
      if (BadaPdfView.current === ctl) BadaPdfView.current = null;
      if (typeof opts.onClose === "function") {
        opts.onClose({ annots: st.annots.map(function (a) { return Edit.normalize(a); }).filter(Boolean),
                       dirty: st.dirty, baseBytes: st.baseBytes });
      }
    }
    document.addEventListener("keydown", onKey, true);

    /* ───────── 起動 ───────── */
    var bytes = opts.bytes instanceof Uint8Array ? opts.bytes : new Uint8Array(opts.bytes || 0);
    st.baseBytes = bytes;
    setStatus("PDF を読み込み中…");
    var ready = Promise.resolve().then(function () {
      /* 以前 BadaCineVim で付けた注釈があれば、編集できる形で取り出す
         (ページ画像からは外し、注釈レイヤに載せ直す) */
      if (opts.annots) {                           /* 引き継ぎ: bytes は注釈を外した PDF */
        opts.annots.forEach(function (raw) { var a = Edit.normalize(raw); if (a) { a._id = st.nextId++; st.annots.push(a); } });
        st.dirty = !!opts.dirty;
        return null;
      }
      if (!Edit.hasMarker(bytes)) return null;
      return ensurePdfLib(pdfLibUrl).then(function (L) { return Edit.extractAnnotations(L, bytes); }).then(function (r) {
        st.baseBytes = r.bytes;
        r.annots.forEach(function (a) { a._id = st.nextId++; st.annots.push(a); });
      }, function (err) {
        st.editable = false;
        st.status = "既存の注釈を読み取れないため読み取り専用で開きます: " + (err && err.message || err);
      });
    }).then(function () {
      return openDoc();
    }).then(function (pdf) {
      if (st.closed) { pdf.destroy(); return; }
      st.pdf = pdf;
      return buildPages().then(function () {
        if (st.closed) return;
        setupObserver();
        var msg = pdf.numPages + " ページ" + (st.annots.length ? " / 注釈 " + st.annots.length + " 件" : "") +
                  (st.editable ? "" : " (読み取り専用)");
        if (!st.status || /読み込み中/.test(st.status)) setStatus(msg);
        refreshChrome();
        if (opts.search) return scanHits(opts.search, true);
        return setCursor(0, 0, 0, false);            /* 先頭の行にカーソルを置く */
      });
    }).then(function () { return ctl; }, function (err) {
      setStatus("PDF を表示できません: " + (err && err.message || err));
      if (typeof opts.onError === "function") opts.onError(err);
      return ctl;
    });

    refreshChrome();
    elBody.focus();
    var ctl = { state: st, ready: ready, close: teardown, save: save, addAnnot: addAnnot, gotoPage: gotoPage,
                rotatePage: rotatePage, deletePage: deletePage, movePage: movePage, blankPage: blankPage,
                mergePdf: mergePdf, flatten: flattenAll, undo: undo,
                substitute: substitute, setCursor: setCursor, linesOf: linesOf, exec: function (line) { return execCmd(line); },
                setScale: setScale, setTool: function (t) { setTool(t); refreshChrome(); }, scanHits: scanHits };
    BadaPdfView.current = ctl;
    return ctl;
  }

  function ensureStyle() {
    if (document.getElementById("badapdf-style")) return;
    var css = document.createElement("style");
    css.id = "badapdf-style";
    css.textContent = [
      /* 枠の基本スタイル (Bada Search では cinevim.js と同じ見た目。単体アプリではこれだけで完結) */
      ".badapdf-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.86);display:flex;align-items:center;justify-content:center;backdrop-filter:blur(2px)}",
      ".badapdf-overlay .cv-frame{background:#000;border:2px solid #1f6f3f;border-radius:14px;box-shadow:0 30px 120px #000,0 0 40px #0f54;display:flex;flex-direction:column;overflow:hidden;font-family:'SFMono-Regular',Consolas,'Noto Sans Mono CJK JP',monospace}",
      ".badapdf-overlay .cv-bar{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:13px;color:#8fe8ab;background:#041a0e;border-bottom:1px solid #15351f}",
      ".badapdf-overlay .cv-status{border-bottom:none;border-top:1px solid #15351f;color:#5f8f6a}",
      ".badapdf-overlay .cv-grow{flex:1}",
      ".badapdf-overlay .cv-name{color:#3cff8e;font-weight:bold;text-shadow:0 0 10px #0f5}",
      ".badapdf-overlay .cv-flag{color:#ffcf4a}",
      ".badapdf-overlay .cv-hint{color:#4a6e55;font-size:11.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}",
      ".badapdf-overlay .cv-x{margin-left:6px;background:#06160d;color:#9fe8b6;border:1px solid #15351f;border-radius:7px;padding:3px 10px;cursor:pointer;font:inherit}",
      ".badapdf-overlay .cv-x:hover{border-color:#3cff8e}",
      ".badapdf-overlay .cv-body{flex:1}",
      ".badapdf-overlay .cv-mode{font-weight:bold;color:#5f8f6a}",
      ".badapdf-overlay .cv-mode.insert{color:#3cff8e;text-shadow:0 0 8px #0f5}",
      ".badapdf-overlay .cv-acts{display:flex;gap:6px}",
      ".badapdf-overlay .cv-act{background:#06160d;color:#4fe8ff;border:1px solid #15351f;border-radius:7px;padding:3px 10px;cursor:pointer;font:inherit;font-size:12px;white-space:nowrap}",
      ".badapdf-overlay .cv-act:hover{border-color:#4fe8ff}",
      ".badapdf-overlay .pv-frame{width:min(1240px,98vw);height:min(94vh,1100px)}",
      ".badapdf-overlay .cv-bar{flex-wrap:wrap;row-gap:6px}",
      ".badapdf-overlay .pv-tools{background:#03120a}",
      ".badapdf-overlay .cv-msg{color:#ffcf4a}",
      ".badapdf-overlay .pv-cmdin{flex:1 1 220px;min-width:140px;background:#000;color:#4fe8ff;border:1px solid #1f6f3f;border-radius:6px;padding:3px 8px;font:inherit;font-weight:bold;outline:none}",
      ".badapdf-overlay .pv-b,.badapdf-overlay .pv-t{background:#06160d;color:#9fe8b6;border:1px solid #15351f;border-radius:7px;padding:3px 10px;cursor:pointer;font:inherit;font-size:12.5px;white-space:nowrap}",
      ".badapdf-overlay .pv-b:hover,.badapdf-overlay .pv-t:hover{border-color:#3cff8e}",
      ".badapdf-overlay .pv-t.on{background:#0a3a1e;border-color:#3cff8e;color:#3cff8e;box-shadow:0 0 10px #0f54}",
      ".badapdf-overlay button:disabled{opacity:.35;cursor:not-allowed}",
      ".badapdf-overlay .pv-save{color:#ffcf4a}",
      ".badapdf-overlay .pv-pageno,.badapdf-overlay .pv-zoom{color:#ffcf4a;min-width:52px;text-align:center}",
      ".badapdf-overlay .pv-colors{display:flex;gap:5px;margin:0 4px}",
      ".badapdf-overlay .pv-c{width:18px;height:18px;border-radius:50%;border:2px solid #15351f;padding:0;cursor:pointer}",
      ".badapdf-overlay .pv-c.on{border-color:#fff;box-shadow:0 0 8px #fff8}",
      ".badapdf-overlay .pv-body{display:block;position:relative;overflow:auto;background:#0b0f0c;outline:none}",
      ".badapdf-overlay .pv-pages{display:flex;flex-direction:column;align-items:center;gap:14px;padding:14px 12px 40px;min-width:min-content}",
      ".badapdf-overlay .pv-page{position:relative;flex:none;background:#fff;box-shadow:0 6px 30px #000c;border-radius:2px}",
      ".badapdf-overlay .pv-page canvas{position:absolute;left:0;top:0;width:100%;height:100%;display:block}",
      ".badapdf-overlay .pv-page:not(.ready)::before{content:'…';position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#9aa;font-size:28px}",
      ".badapdf-overlay .pv-ann{position:absolute;left:0;top:0;touch-action:pan-x pan-y}",
      ".badapdf-overlay.pv-drawing .pv-ann{touch-action:none;cursor:crosshair}",
      ".badapdf-overlay .pv-pno{position:absolute;right:-2px;bottom:-12px;font-size:10.5px;color:#4a6e55}",
      ".badapdf-overlay .pv-hit{fill:#ff9d00;fill-opacity:.38;stroke:#ff7a00;stroke-width:1;pointer-events:none}",
      ".badapdf-overlay .pv-mark{mix-blend-mode:multiply}",
      ".badapdf-overlay .pv-preview{opacity:.8;pointer-events:none}",
      ".badapdf-overlay .pv-grab{stroke:transparent;stroke-width:14;fill:none}",
      ".badapdf-overlay .pv-notebg{fill:#fff79e;stroke:#d9b833;stroke-width:1}",
      ".badapdf-overlay .pv-notetext{font-family:'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,Helvetica,Arial,sans-serif;white-space:pre;user-select:none}",
      ".badapdf-overlay .pv-a{cursor:pointer}",
      ".badapdf-overlay.pv-drawing .pv-a{pointer-events:none}",
      ".badapdf-overlay .pv-edit{background:#020d07;border-bottom:1px solid #15351f}",
      ".badapdf-overlay .pv-lab{color:#ffcf4a;font-size:11.5px;letter-spacing:.05em}",
      ".badapdf-overlay .pv-sep{width:1px;align-self:stretch;background:#15351f;margin:0 4px}",
      ".badapdf-overlay .pv-erasing{stroke:#ff3b5c;stroke-width:1;stroke-dasharray:4 3}",
      ".badapdf-overlay .pv-edittext{white-space:pre;user-select:none}",
      ".badapdf-overlay .pv-font-sans{font-family:Helvetica,Arial,'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif}",
      ".badapdf-overlay .pv-font-serif{font-family:'Times New Roman',Times,'Noto Serif JP','Hiragino Mincho ProN','Yu Mincho',serif}",
      ".badapdf-overlay .pv-font-mono{font-family:Courier,'Courier New',monospace}",
      ".badapdf-overlay .pv-grabbox{fill:transparent}",
      ".badapdf-overlay .pv-plainedit{background:#fff;border-color:#ff7a00;padding:0 2px;min-height:1.3em;line-height:1.2}",
      ".badapdf-overlay .pv-vimcur{fill:#19c463;fill-opacity:.55;stroke:#0a7a3a;stroke-width:1;pointer-events:none}",
      ".badapdf-overlay .pv-curline{fill:#19c463;fill-opacity:.10;pointer-events:none}",
      ".badapdf-overlay .pv-selbox{fill:none;stroke:#1f6fff;stroke-width:1.5;stroke-dasharray:5 3;pointer-events:none}",
      ".badapdf-overlay .pv-noteedit{position:absolute;z-index:5;min-width:180px;min-height:2.2em;padding:2px 4px;border:2px solid #1f6fff;border-radius:3px;background:#fffbd0;color:#102030;font-family:'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,Helvetica,Arial,sans-serif;line-height:1.3;resize:both;outline:none;box-shadow:0 4px 18px #0006}"
    ].join("\n");
    document.head.appendChild(css);
  }

  var BadaPdfView = { open: open, current: null, _colors: COLORS };
  global.BadaPdfView = BadaPdfView;
})(typeof globalThis !== "undefined" ? globalThis : this);
