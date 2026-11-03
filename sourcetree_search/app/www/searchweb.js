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

  /* ブラウザでの PDF テキスト抽出 (searchcore の extractTextOps 相当を再利用) */
  async function extractPdfTextBrowser(bytes) {
    if (!HAS_INFLATE) return "";
    var raw = latin1(bytes), texts = [], idx = 0;
    while (true) {
      var s = raw.indexOf("stream", idx); if (s < 0) break;
      var e = raw.indexOf("endstream", s); if (e < 0) break;
      var start = s + 6;
      if (raw[start] === "\r") start++;
      if (raw[start] === "\n") start++;
      var dictStart = raw.lastIndexOf("<<", s);
      var dict = dictStart >= 0 ? raw.slice(dictStart, s) : "";
      var body = bytes.subarray(start, e);
      var content = null;
      if (/\/FlateDecode/.test(dict)) {
        try { content = latin1(await inflate(body, false)); }
        catch (e1) { try { content = latin1(await inflate(body, true)); } catch (e2) { content = null; } }
      } else if (!/\/Filter/.test(dict)) {
        content = latin1(body);
      }
      if (content && content.length > 4 * 1024 * 1024) content = content.slice(0, 4 * 1024 * 1024);
      if (content && /\b(Tj|TJ|BT)\b/.test(content)) {
        var t = extractTextOps(content);
        if (t.trim()) texts.push(t);
      }
      idx = e + 9;
    }
    return texts.join("\n");
  }
  /* searchcore と同一の抽出ロジック (ブラウザ移植版) */
  function extractTextOps(content) {
    var parts = [];
    var re = /\(((?:\\.|[^\\()])*)\)\s*(Tj|')|\[((?:\\.|[^\]\\])*)\]\s*TJ|<([0-9a-fA-F\s]+)>\s*Tj/g;
    var m;
    while ((m = re.exec(content))) {
      if (m[1] !== undefined) parts.push(unescapePdf(m[1]));
      else if (m[3] !== undefined) {
        var inner = m[3], re2 = /\(((?:\\.|[^\\()])*)\)|<([0-9a-fA-F\s]+)>/g, mm;
        while ((mm = re2.exec(inner))) {
          if (mm[1] !== undefined) parts.push(unescapePdf(mm[1]));
          else parts.push(hexToText(mm[2]));
        }
      } else if (m[4] !== undefined) parts.push(hexToText(m[4]));
    }
    return parts.join(" ");
  }
  function unescapePdf(s) {
    var out = "", i = 0;
    while (i < s.length) {
      var ch = s[i];
      if (ch !== "\\") { out += ch; i++; continue; }
      var n = s[i + 1];
      if (n === "n") out += "\n"; else if (n === "r") out += "\r"; else if (n === "t") out += "\t";
      else if (n === "b" || n === "f") out += ""; else if (n === "(" || n === ")" || n === "\\") out += n;
      else if (/[0-7]/.test(n || "")) { var oct = s.substr(i + 1, 3).match(/^[0-7]{1,3}/)[0]; out += String.fromCharCode(parseInt(oct, 8) & 0xff); i += oct.length - 1; }
      i += 2;
    }
    return out;
  }
  function hexToText(hex) {
    var clean = hex.replace(/[^0-9a-fA-F]/g, ""), bytes = [];
    for (var i = 0; i + 1 < clean.length; i += 2) bytes.push(parseInt(clean.substr(i, 2), 16));
    if (bytes.length >= 2 && bytes[0] === 0xfe && bytes[1] === 0xff) {
      var s = ""; for (var j = 2; j + 1 < bytes.length; j += 2) s += String.fromCharCode((bytes[j] << 8) | bytes[j + 1]); return s;
    }
    return bytes.map(function (b) { return String.fromCharCode(b); }).join("");
  }

  async function buildIndexFromFiles(fileList, onProgress) {
    var files = [], langs = {}, scanned = 0, skippedPdf = 0, n = fileList.length;
    for (var i = 0; i < n; i++) {
      var f = fileList[i];
      var rel = (f.webkitRelativePath || f.name || "file").split("\\").join("/");
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
      langs[lang] = (langs[lang] || 0) + 1;
    }
    return { root: "(選択したファイル)", files: files, scanned: scanned, errors: [], langs: langs,
             skippedPdf: skippedPdf, builtAt: new Date().toISOString() };
  }

  /* Electron の badaSearch と同じ形のブリッジ (complete.html / index.html から使用) */
  function makeWebBridge() {
    var index = null, vocab = null;
    return {
      isWeb: true,
      hasInflate: HAS_INFLATE,
      buildFromFiles: async function (fileList, onProgress) {
        index = await buildIndexFromFiles(fileList, onProgress); vocab = null;
        return { root: index.root, files: index.files.length, scanned: index.scanned,
                 langs: index.langs, skippedPdf: index.skippedPdf };
      },
      buildVocab: function () { vocab = Core.buildVocab(index || { files: [] }, {}); return Promise.resolve({ size: vocab.size }); },
      complete: function (p, o) { return Promise.resolve(vocab ? Core.complete(vocab, p, o || {}) : { items: [], total: 0 }); },
      search: function (q, o) { return Promise.resolve(index ? Core.search(index, q, o || {}) : { hits: [], total: 0, files: 0 }); },
      fileText: function (p) {
        var f = index && index.files.filter(function (x) { return x.path === p || x.rel === p; })[0];
        return Promise.resolve(f ? { name: f.rel, lines: f.lines, lang: f.lang, readonly: true }
                                 : { error: "ファイルが見つかりません" });
      },
      saveFile: function () { return Promise.resolve({ error: "ブラウザ/APK では保存できません (閲覧専用)" }); }
    };
  }

  global.BadaSearchWeb = {
    hasInflate: HAS_INFLATE,
    buildIndexFromFiles: buildIndexFromFiles,
    extractPdfTextBrowser: extractPdfTextBrowser,
    makeWebBridge: makeWebBridge
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
