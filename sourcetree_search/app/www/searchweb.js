/*
 * searchweb.js — Bada Search ブラウザ/APK 用インデクサ (Electron 非依存)
 *
 * Electron のメインプロセス (Node) が使えない Android APK / ブラウザでは、
 * ユーザーが選んだファイル (File オブジェクト) をこのモジュールが読み込み、
 * searchcore.js (UMD) の純粋関数で索引・語彙・補完・検索を行います。
 *   ・ソース/テキスト: File.text() で読み込み (NUL を含むものはバイナリ扱いで除外)
 *   ・PDF: FlateDecode ストリームを DecompressionStream('deflate') で展開し
 *          searchcore の抽出ロジックでテキスト化 (未対応環境では PDF をスキップ)
 *
 * 画面 (complete.html / index.html) からは Electron の badaSearch と同じ形の
 * 「ブリッジ」として使われ、検索結果はそのまま BadaCineVim で開けます。
 *
 * 編集と保存 (閲覧専用ではありません):
 *   ・ソース/テキストは CineVim で編集し :w で保存、PDF はページ表示で注釈編集して保存。
 *   ・保存先は環境に応じて自動で選びます —
 *       1. フォルダを File System Access API で開いた場合 … 元のファイルに上書き
 *          (PDF は初回のみ <名前>.pdf.bak を残す)
 *       2. Android APK (cordova-plugin-file) … アプリの保存フォルダに書き出し
 *       3. それ以外 … ダウンロードとして保存 (元ファイルは変更しない)
 *     いずれの場合もメモリ上の索引は更新するので、編集内容はすぐ検索に反映されます。
 */
(function (global) {
  "use strict";
  var Core = global.BadaSearchCore;
  var MAX_FILE = 8 * 1024 * 1024;

  var HAS_INFLATE = (typeof DecompressionStream !== "undefined");

  async function inflate(bytes, raw) {
    var ds = new DecompressionStream(raw ? "deflate-raw" : "deflate");
    var stream = new Blob([bytes]).stream().pipeThrough(ds);
    var buf = await new Response(stream).arrayBuffer();
    return new Uint8Array(buf);
  }

  function latin1(bytes) {
    var s = "", CH = 0x8000;
    for (var i = 0; i < bytes.length; i += CH) {
      s += String.fromCharCode.apply(null, bytes.subarray(i, Math.min(i + CH, bytes.length)));
    }
    return s;
  }

  /* ブラウザでの PDF テキスト抽出。
     stream を DecompressionStream で展開し、searchcore (UMD) の
     parseToUnicodeCMap / decodeTextOps を再利用して ToUnicode で正しく
     Unicode 化する (日本語 CID フォントの文字化けを防止)。 */
  async function extractPdfTextBrowser(bytes) {
    if (!HAS_INFLATE) return "";
    var raw = latin1(bytes), streams = [], idx = 0;
    while (true) {
      var s = raw.indexOf("stream", idx); if (s < 0) break;
      var e = raw.indexOf("endstream", s); if (e < 0) break;
      var start = s + 6;
      if (raw[start] === "\r") start++;
      if (raw[start] === "\n") start++;
      var dictStart = raw.lastIndexOf("<<", s);
      var dict = dictStart >= 0 ? raw.slice(dictStart, s) : "";
      var content = null;
      if (Core.isBadaAppearance(dict)) {
        content = null;                 /* BadaCineVim の注釈の外観ストリームは本文ではない */
      } else if (/\/FlateDecode/.test(dict)) {
        /* DecompressionStream は厳格で末尾の余分なバイト (endstream 前の EOL) で
           失敗するため、inline /Length があれば正確に切り出し、無ければ末尾を
           1〜2 バイト削って再試行する。 */
        var ends = [];
        var lenM = /\/Length\s+(\d+)(?!\s+\d+\s+R)/.exec(dict);
        if (lenM) { var n = parseInt(lenM[1], 10); if (n > 0 && start + n <= e) ends.push(start + n); }
        ends.push(e, e - 1, e - 2);
        for (var ei = 0; ei < ends.length && content === null; ei++) {
          var be = ends[ei]; if (be <= start) continue;
          var body = bytes.subarray(start, be);
          try { content = latin1(await inflate(body, false)); }
          catch (e1) { try { content = latin1(await inflate(body, true)); } catch (e2) { content = null; } }
        }
      } else if (!/\/Filter/.test(dict)) {
        content = latin1(bytes.subarray(start, e));
      }
      if (content) { if (content.length > 4 * 1024 * 1024) content = content.slice(0, 4 * 1024 * 1024); streams.push(content); }
      idx = e + 9;
    }
    /* パス 1: ToUnicode CMap を集約 */
    var cmap = { map: {}, width: 0 };
    for (var i = 0; i < streams.length; i++) if (/beginbf(char|range)/.test(streams[i])) Core.parseToUnicodeCMap(streams[i], cmap);
    if (!cmap.width) cmap.width = 2;
    var hasMap = Object.keys(cmap.map).length > 0;
    /* パス 2: テキストを抽出 (必要なら ToUnicode 変換) */
    var texts = [];
    for (var j = 0; j < streams.length; j++) {
      if (/\b(Tj|TJ|BT)\b/.test(streams[j])) {
        var t = Core.decodeTextOps(streams[j], hasMap ? cmap : null);
        if (t.trim()) texts.push(t);
      }
    }
    return texts.concat(Core.extractAnnotTexts(raw)).join("\n");
  }

  /* entries: File の配列、または { file, rel, handle, dir } の配列
     (handle / dir は File System Access API のハンドル — あれば上書き保存に使う) */
  async function buildIndexFromFiles(fileList, onProgress) {
    var files = [], langs = {}, scanned = 0, skippedPdf = 0, n = fileList.length, store = {};
    for (var i = 0; i < n; i++) {
      var ent = fileList[i];
      var f = (ent && ent.file) ? ent.file : ent;
      var rel = ((ent && ent.rel) || f.webkitRelativePath || f.name || "file").split("\\").join("/");
      var lang = Core.langOf(rel);
      if (!lang) continue;
      scanned++;
      if (onProgress && (i % 25 === 0)) onProgress(i, n, rel);
      if (f.size > MAX_FILE) continue;
      var lines = null;
      try {
        if (lang === "PDF") {
          if (!HAS_INFLATE) { skippedPdf++; continue; }
          var bytes = new Uint8Array(await f.arrayBuffer());
          var t = await extractPdfTextBrowser(bytes);
          if (!t.trim()) { skippedPdf++; continue; }
          lines = t.split(/\r?\n/);
        } else {
          var txt = await f.text();
          if (txt.indexOf("\u0000") >= 0) continue;   /* バイナリ */
          lines = txt.split(/\r?\n/);
        }
      } catch (e) { continue; }
      files.push({ path: rel, rel: rel, lang: lang, size: f.size, lines: lines });
      store[rel] = { blob: f, handle: (ent && ent.handle) || null, dir: (ent && ent.dir) || null };
      langs[lang] = (langs[lang] || 0) + 1;
    }
    return { root: "(選択したファイル)", files: files, scanned: scanned, errors: [], langs: langs,
             skippedPdf: skippedPdf, store: store, builtAt: new Date().toISOString() };
  }

  /* File System Access API のフォルダを再帰的に走査して entries を作る (読み書き可のハンドル付き) */
  async function entriesFromDirectory(dirHandle, onProgress) {
    var out = [], skip = {}, MAX = 20000;
    (Core.SKIP_DIRS || []).forEach(function (d) { skip[d] = true; });
    async function walk(dir, prefix) {
      for await (var pair of dir.entries()) {
        if (out.length >= MAX) return;
        var name = pair[0], h = pair[1];
        if (h.kind === "directory") { if (!skip[name]) await walk(h, prefix + name + "/"); continue; }
        if (!Core.langOf(name)) continue;
        try {
          out.push({ file: await h.getFile(), rel: prefix + name, handle: h, dir: dir });
          if (onProgress && out.length % 50 === 0) onProgress(out.length, 0, prefix + name);
        } catch (e) {}
      }
    }
    await walk(dirHandle, "");
    return out;
  }

  /* ── 保存 ── */
  function baseNameOf(rel) { return String(rel).split("/").pop(); }
  async function writeHandle(handle, blob) {
    var w = await handle.createWritable();
    await w.write(blob);
    await w.close();
  }
  /* Android APK (Cordova) のときだけ cordova.js を読み込み、プラグインの準備 (deviceready) を待つ。
     ブラウザや EXE では何もしない (cordova.js は APK のビルド時にだけ www に入る)。 */
  var cordovaReady = null;
  function looksLikeCordova() {
    if (global.cordova) return true;
    var loc = global.location || {};
    return /Android/i.test((global.navigator && global.navigator.userAgent) || "") &&
           loc.protocol === "https:" && loc.hostname === "localhost";
  }
  function ensureCordova() {
    if (!looksLikeCordova() || typeof document === "undefined") return Promise.resolve(false);
    if (cordovaReady) return cordovaReady;
    cordovaReady = new Promise(function (resolve) {
      var done = false;
      function finish(v) { if (!done) { done = true; resolve(v); } }
      document.addEventListener("deviceready", function () { finish(true); }, false);
      if (!global.cordova) {
        var el = document.createElement("script");
        el.src = "cordova.js";
        el.onerror = function () { finish(false); };
        document.head.appendChild(el);
      }
      setTimeout(function () { finish(!!(global.cordova && global.cordova.file)); }, 4000);
    });
    return cordovaReady;
  }
  function cordovaWrite(name, blob) {
    return new Promise(function (resolve, reject) {
      var dirUrl = global.cordova.file.externalDataDirectory || global.cordova.file.dataDirectory;
      global.resolveLocalFileSystemURL(dirUrl, function (dir) {
        dir.getFile(name, { create: true }, function (fe) {
          fe.createWriter(function (w) {
            w.onerror = function (e) { reject(e); };
            w.onwriteend = function () {               /* truncate 完了 → 本体を書く */
              w.onwriteend = function () { resolve(fe.nativeURL || fe.toURL()); };
              w.write(blob);
            };
            w.truncate(0);
          }, reject);
        }, reject);
      }, reject);
    });
  }
  function download(name, blob) {
    var url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = name; a.style.display = "none";
    document.body.appendChild(a); a.click();
    setTimeout(function () { if (a.parentNode) a.parentNode.removeChild(a); URL.revokeObjectURL(url); }, 4000);
  }
  /* rel のファイルを blob の内容で保存する。slot は index.store[rel] */
  async function persist(rel, slot, blob, backupOld) {
    if (slot && slot.handle && slot.handle.createWritable) {
      var note = "フォルダ内のファイルに上書きしました";
      if (backupOld && slot.dir) {
        var bak = baseNameOf(rel) + ".bak", has = true;
        try { await slot.dir.getFileHandle(bak); } catch (e) { has = false; }
        if (!has) {
          try { await writeHandle(await slot.dir.getFileHandle(bak, { create: true }), slot.blob); note += " (元の PDF は " + bak + " に退避)"; }
          catch (e2) {}
        }
      }
      await writeHandle(slot.handle, blob);
      return { ok: true, note: note };
    }
    await ensureCordova();
    if (global.cordova && global.cordova.file && global.resolveLocalFileSystemURL) {
      var where = await cordovaWrite(String(rel).replace(/[\\/]/g, "__"), blob);
      return { ok: true, note: "保存先: " + where };
    }
    download(baseNameOf(rel), blob);
    return { ok: true, note: "ダウンロードとして保存しました (元のファイルは変更されません)" };
  }

  /* Electron の badaSearch と同じ形のブリッジ (complete.html / index.html から使用) */
  function makeWebBridge() {
    var index = null, vocab = null;
    return {
      isWeb: true,
      hasInflate: HAS_INFLATE,
      canPickDirectory: typeof global.showDirectoryPicker === "function",
      buildFromFiles: async function (fileList, onProgress) {
        index = await buildIndexFromFiles(fileList, onProgress); vocab = null;
        return { root: index.root, files: index.files.length, scanned: index.scanned,
                 langs: index.langs, skippedPdf: index.skippedPdf };
      },
      /* フォルダを読み書き可で開いて索引 (対応ブラウザのみ)。キャンセル時は null */
      pickDirectory: async function (onProgress) {
        var dir;
        try { dir = await global.showDirectoryPicker({ mode: "readwrite" }); }
        catch (e) { return null; }
        var entries = await entriesFromDirectory(dir, onProgress);
        index = await buildIndexFromFiles(entries, onProgress); vocab = null;
        index.root = dir.name;
        return { root: dir.name, files: index.files.length, scanned: index.scanned,
                 langs: index.langs, skippedPdf: index.skippedPdf, writable: true };
      },
      buildVocab: function () { vocab = Core.buildVocab(index || { files: [] }, {}); return Promise.resolve({ size: vocab.size }); },
      complete: function (p, o) { return Promise.resolve(vocab ? Core.complete(vocab, p, o || {}) : { items: [], total: 0 }); },
      search: function (q, o) { return Promise.resolve(index ? Core.search(index, q, o || {}) : { hits: [], total: 0, files: 0 }); },
      fileText: function (p) {
        var f = find(p);
        /* PDF の抽出テキストは読み取り専用 (PDF 自体はページ表示で注釈編集)。ソースは編集可 */
        return Promise.resolve(f ? { name: f.rel, lines: f.lines, lang: f.lang, readonly: f.lang === "PDF" }
                                 : { error: "ファイルが見つかりません" });
      },
      fileBytes: async function (p) {
        var f = find(p), slot = f && index.store[f.rel];
        if (!slot) return { error: "ファイルが見つかりません" };
        try { return { bytes: new Uint8Array(await slot.blob.arrayBuffer()) }; }
        catch (e) { return { error: e.message || String(e) }; }
      },
      saveFile: async function (p, text) {
        var f = find(p);
        if (!f) return { error: "ファイルが見つかりません" };
        if (f.lang === "PDF") return { error: "PDF はページ表示で編集してください" };
        var blob = new Blob([text], { type: "text/plain;charset=utf-8" });
        try {
          var r = await persist(f.rel, index.store[f.rel], blob, false);
          f.lines = String(text).split(/\r?\n/); f.size = blob.size;
          index.store[f.rel].blob = blob;
          return r;
        } catch (e) { return { error: e.message || String(e) }; }
      },
      saveBytes: async function (p, bytes) {
        var f = find(p);
        if (!f) return { error: "ファイルが見つかりません" };
        var blob = new Blob([bytes], { type: "application/pdf" });
        try {
          var r = await persist(f.rel, index.store[f.rel], blob, true);
          var t = await extractPdfTextBrowser(bytes);        /* メモを検索に反映 */
          if (t.trim()) f.lines = t.split(/\r?\n/);
          f.size = blob.size;
          index.store[f.rel].blob = blob;
          return r;
        } catch (e) { return { error: e.message || String(e) }; }
      }
    };
    function find(p) {
      return (index && index.files.filter(function (x) { return x.path === p || x.rel === p; })[0]) || null;
    }
  }

  global.BadaSearchWeb = {
    hasInflate: HAS_INFLATE,
    buildIndexFromFiles: buildIndexFromFiles,
    extractPdfTextBrowser: extractPdfTextBrowser,
    entriesFromDirectory: entriesFromDirectory,
    makeWebBridge: makeWebBridge
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
