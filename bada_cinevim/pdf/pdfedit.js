/*
 * pdfedit.js — BadaCineVim PDF 編集エンジン (注釈の書き込み / 読み戻し)
 *
 * BadaCineVim の PDF ビューで付けた注釈 (ハイライト / 手書き / メモ) を、標準の
 * PDF 注釈 (/Highlight /Ink /FreeText + 外観ストリーム) として PDF に書き込みます。
 * 他の PDF ビューア (Acrobat / ブラウザ / プレビュー等) でもそのまま表示されます。
 *
 *   applyAnnotations(PDFLib, bytes, annots)  → 注釈入りの PDF (Uint8Array)
 *   extractAnnotations(PDFLib, bytes)        → { bytes: 注釈を外した PDF, annots }
 *   hasMarker(bytes)                         → BadaCineVim の注釈を含むか (高速判定)
 *
 * 注釈モデル (座標は PDF ユーザー空間・左下原点、page は 0 始まり):
 *   { type:"highlight", page, rects:[[x1,y1,x2,y2],…], color:"#ffe14a" }
 *   { type:"ink",       page, paths:[[x,y,x,y,…],…],   color:"#ff4a6a", width:2 }
 *   { type:"note",      page, x, y(上端), text, size:12, color:"#102030" }
 *
 * 各注釈には /T (BadaCineVim) と /BadaData (モデルの JSON) を持たせるので、
 * 開き直しても同じ注釈をそのまま再編集できます (読み戻しは無損失)。
 *
 * UMD: ブラウザ (window.BadaPdfEdit) / Node (require) 両対応。PDF の解析と
 * 直列化は同梱の pdf-lib (vendor/pdf-lib) を引数で受け取って使います。
 */
(function (global) {
  "use strict";
  var MARK = "BadaCineVim";

  /* ───────── 小物 ───────── */
  function n2(v) { var r = Math.round(v * 100) / 100; return String(r === 0 ? 0 : r); }
  function rgb(hex) {
    var m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(String(hex || ""));
    if (!m) return [1, 0.88, 0.29];
    return [parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255];
  }
  function rgbOp(hex, op) { var c = rgb(hex); return n2(c[0]) + " " + n2(c[1]) + " " + n2(c[2]) + " " + op; }
  function isAscii(s) { return /^[\x20-\x7e\n]*$/.test(s); }
  function utf16Hex(s) {
    var out = "";
    for (var i = 0; i < s.length; i++) out += ("0000" + s.charCodeAt(i).toString(16)).slice(-4).toUpperCase();
    return out;
  }
  function litEscape(s) { return s.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)"); }

  function hasMarker(bytes) {
    /* "(BadaCineVim)" のバイト列を探す (保存時はオブジェクトストリーム無効なので平文) */
    var pat = [], s = "(" + MARK + ")";
    for (var i = 0; i < s.length; i++) pat.push(s.charCodeAt(i));
    outer:
    for (var p = 0, n = bytes.length - pat.length; p <= n; p++) {
      if (bytes[p] !== 40) continue;
      for (var k = 1; k < pat.length; k++) if (bytes[p + k] !== pat[k]) continue outer;
      return true;
    }
    return false;
  }

  /* ───────── 寸法 ───────── */
  function noteLines(a) { return String(a.text == null ? "" : a.text).split("\n"); }
  function charEm(code) { return code < 0x80 ? 0.56 : (code >= 0xff61 && code <= 0xff9f ? 0.5 : 1); }
  function lineEm(line) { var w = 0; for (var i = 0; i < line.length; i++) w += charEm(line.charCodeAt(i)); return w; }
  /* メモの外接矩形 [x1,y1,x2,y2] (a.x, a.y は左上)。UI の表示とも共有する。 */
  function noteRect(a) {
    var size = a.size || 12, lines = noteLines(a), w = 0;
    for (var i = 0; i < lines.length; i++) w = Math.max(w, lineEm(lines[i]));
    var width = Math.max(1, w) * size + 8, height = lines.length * size * 1.3 + 6;
    return [a.x, a.y - height, a.x + width, a.y];
  }
  function annotRect(a) {
    var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity, i, j;
    function add(x, y) { if (x < x1) x1 = x; if (x > x2) x2 = x; if (y < y1) y1 = y; if (y > y2) y2 = y; }
    if (a.type === "note") return noteRect(a);
    if (a.type === "highlight") {
      for (i = 0; i < a.rects.length; i++) { add(a.rects[i][0], a.rects[i][1]); add(a.rects[i][2], a.rects[i][3]); }
      return [x1, y1, x2, y2];
    }
    if (a.type === "ink") {
      var pad = (a.width || 2) / 2 + 1;
      for (i = 0; i < a.paths.length; i++) for (j = 0; j + 1 < a.paths[i].length; j += 2) add(a.paths[i][j], a.paths[i][j + 1]);
      return [x1 - pad, y1 - pad, x2 + pad, y2 + pad];
    }
    return [0, 0, 0, 0];
  }

  /* 注釈の検証と正規化 (壊れた入力を PDF に書かない) */
  function fin(v) { return typeof v === "number" && isFinite(v); }
  function normalize(a) {
    if (!a || typeof a !== "object") return null;
    var page = a.page | 0, i, j;
    if (a.type === "highlight") {
      var rects = [];
      for (i = 0; i < (a.rects || []).length; i++) {
        var r = a.rects[i];
        if (!r || r.length !== 4 || !r.every(fin)) continue;
        rects.push([Math.min(r[0], r[2]), Math.min(r[1], r[3]), Math.max(r[0], r[2]), Math.max(r[1], r[3])]);
      }
      return rects.length ? { type: "highlight", page: page, rects: rects, color: a.color || "#ffe14a" } : null;
    }
    if (a.type === "ink") {
      var paths = [];
      for (i = 0; i < (a.paths || []).length; i++) {
        var p = a.paths[i], q = [];
        for (j = 0; p && j + 1 < p.length; j += 2) if (fin(p[j]) && fin(p[j + 1])) q.push(p[j], p[j + 1]);
        if (q.length >= 2) paths.push(q);
      }
      return paths.length ? { type: "ink", page: page, paths: paths, color: a.color || "#ff4a6a", width: fin(a.width) ? a.width : 2 } : null;
    }
    if (a.type === "note") {
      var text = String(a.text == null ? "" : a.text).replace(/\r\n?/g, "\n");
      if (!text.trim() || !fin(a.x) || !fin(a.y)) return null;
      return { type: "note", page: page, x: a.x, y: a.y, text: text, size: fin(a.size) ? a.size : 12, color: a.color || "#102030" };
    }
    return null;
  }

  /* ───────── 外観ストリーム ───────── */
  function highlightStream(a) {
    var s = "/GS gs " + rgbOp(a.color, "rg") + "\n";
    for (var i = 0; i < a.rects.length; i++) {
      var r = a.rects[i];
      s += n2(r[0]) + " " + n2(r[1]) + " " + n2(r[2] - r[0]) + " " + n2(r[3] - r[1]) + " re\n";
    }
    return s + "f\n";
  }
  function inkStream(a) {
    var s = rgbOp(a.color, "RG") + " " + n2(a.width || 2) + " w 1 J 1 j\n";
    for (var i = 0; i < a.paths.length; i++) {
      var p = a.paths[i];
      s += n2(p[0]) + " " + n2(p[1]) + " m\n";
      if (p.length === 2) s += n2(p[0]) + " " + n2(p[1]) + " l\n";
      for (var j = 2; j + 1 < p.length; j += 2) s += n2(p[j]) + " " + n2(p[j + 1]) + " l\n";
      s += "S\n";
    }
    return s;
  }
  function noteStream(a, ascii) {
    var r = noteRect(a), size = a.size || 12, lines = noteLines(a);
    var s = "1 0.97 0.62 rg 0.85 0.72 0.2 RG 0.6 w\n" +
            n2(r[0]) + " " + n2(r[1]) + " " + n2(r[2] - r[0]) + " " + n2(r[3] - r[1]) + " re B\n" +
            "BT /F1 " + n2(size) + " Tf " + n2(size * 1.3) + " TL " + rgbOp(a.color, "rg") + "\n" +
            n2(a.x + 4) + " " + n2(a.y - size * 1.05 - 2) + " Td\n";
    for (var i = 0; i < lines.length; i++) {
      s += (ascii ? "(" + litEscape(lines[i]) + ")" : "<" + utf16Hex(lines[i]) + ">") + " Tj T*\n";
    }
    return s + "ET\n";
  }

  /* 日本語メモ用: 非埋め込みの CID フォント (Adobe-Japan1 / UniJIS-UTF16-H)。
     フォント本体は PDF に入れず、ビューア側の日本語フォントで描画されます。 */
  function cjkFont(ctx, L) {
    var name = "KozMinPr6N-Regular";
    return ctx.obj({
      Type: "Font", Subtype: "Type0", BaseFont: name, Encoding: "UniJIS-UTF16-H",
      DescendantFonts: [{
        Type: "Font", Subtype: "CIDFontType0", BaseFont: name,
        CIDSystemInfo: { Registry: L.PDFString.of("Adobe"), Ordering: L.PDFString.of("Japan1"), Supplement: 6 },
        FontDescriptor: {
          Type: "FontDescriptor", FontName: name, Flags: 6, FontBBox: [-437, -340, 1147, 1317],
          ItalicAngle: 0, Ascent: 1317, Descent: -349, CapHeight: 742, StemV: 80
        },
        DW: 1000, W: [1, 94, 560]
      }]
    });
  }

  function buildAnnot(L, doc, a) {
    var ctx = doc.context, rect = annotRect(a), res, body, extra;
    if (a.type === "note") rect = [rect[0] - 1, rect[1] - 1, rect[2] + 1, rect[3] + 1];   /* 枠線が切れないよう 1pt 広げる */
    if (a.type === "highlight") {
      var qp = [];
      for (var i = 0; i < a.rects.length; i++) {
        var r = a.rects[i];
        qp.push(r[0], r[3], r[2], r[3], r[0], r[1], r[2], r[1]);
      }
      res = { ExtGState: { GS: { Type: "ExtGState", BM: "Multiply" } } };
      body = highlightStream(a);
      extra = { Subtype: "Highlight", QuadPoints: qp, C: rgb(a.color) };
    } else if (a.type === "ink") {
      res = {};
      body = inkStream(a);
      extra = { Subtype: "Ink", InkList: a.paths, C: rgb(a.color), BS: { W: a.width || 2 } };
    } else {
      var ascii = isAscii(a.text);
      res = { Font: { F1: ascii
        ? { Type: "Font", Subtype: "Type1", BaseFont: "Helvetica", Encoding: "WinAnsiEncoding" }
        : cjkFont(ctx, L) } };
      body = noteStream(a, ascii);
      extra = {
        Subtype: "FreeText", Contents: L.PDFHexString.fromText(a.text),
        DA: L.PDFString.of(rgbOp(a.color, "rg") + " /Helv " + n2(a.size || 12) + " Tf")
      };
    }
    /* Resources を先に置き、/BadaAP を後ろに置く: 検索エンジン (searchcore) が
       この外観ストリームを本文と誤って索引しないための目印 (メモ本文は /Contents から索引)。 */
    var ap = ctx.register(ctx.stream(body, {
      Type: "XObject", Subtype: "Form", FormType: 1, BBox: rect, Resources: res, BadaAP: true
    }));
    var model = {};
    for (var k in a) if (k !== "page" && Object.prototype.hasOwnProperty.call(a, k)) model[k] = a[k];
    var dict = { Type: "Annot", Rect: rect, F: 4, T: L.PDFString.of(MARK),
                 BadaData: L.PDFHexString.fromText(JSON.stringify(model)), AP: { N: ap } };
    for (var e in extra) dict[e] = extra[e];
    return ctx.register(ctx.obj(dict));
  }

  /* doc から BadaCineVim の注釈を取り外し、モデルの配列で返す */
  function stripDoc(L, doc) {
    var ctx = doc.context, out = [], pages = doc.getPages();
    var kT = L.PDFName.of("T"), kData = L.PDFName.of("BadaData"), kAP = L.PDFName.of("AP"), kN = L.PDFName.of("N");
    for (var pi = 0; pi < pages.length; pi++) {
      var arr = null;
      try { arr = pages[pi].node.Annots(); } catch (e) { arr = null; }
      if (!arr) continue;
      var found = [];
      for (var i = arr.size() - 1; i >= 0; i--) {
        var ref = arr.get(i), d = null;
        try { d = ctx.lookup(ref); } catch (e1) { d = null; }
        if (!(d instanceof L.PDFDict)) continue;
        var t = d.get(kT), name = "";
        try { name = t && t.decodeText ? t.decodeText() : ""; } catch (e2) { name = ""; }
        if (name !== MARK) continue;
        var data = d.get(kData), model = null;
        try { model = JSON.parse(data.decodeText()); } catch (e3) { model = null; }
        if (model) { model.page = pi; model = normalize(model); }
        if (model) found.push(model);
        try {
          var ap = ctx.lookup(d.get(kAP));
          var nref = ap instanceof L.PDFDict ? ap.get(kN) : null;
          if (nref instanceof L.PDFRef) ctx.delete(nref);
        } catch (e4) {}
        arr.remove(i);
        if (ref instanceof L.PDFRef) ctx.delete(ref);
      }
      found.reverse();
      out = out.concat(found);
    }
    return out;
  }

  var SAVE = { useObjectStreams: false, updateFieldAppearances: false };

  function applyAnnotations(L, bytes, annots) {
    return L.PDFDocument.load(bytes, { updateMetadata: false }).then(function (doc) {
      stripDoc(L, doc);                       /* 二重書き込みを防ぐ (常に全置換) */
      var pages = doc.getPages(), written = 0;
      (annots || []).forEach(function (raw) {
        var a = normalize(raw);
        if (!a || a.page < 0 || a.page >= pages.length) return;
        pages[a.page].node.addAnnot(buildAnnot(L, doc, a));
        written++;
      });
      return doc.save(SAVE).then(function (out) { out.badaWritten = written; return out; });
    });
  }

  function extractAnnotations(L, bytes) {
    return L.PDFDocument.load(bytes, { updateMetadata: false }).then(function (doc) {
      var annots = stripDoc(L, doc);
      if (!annots.length) return { bytes: bytes, annots: [] };
      return doc.save(SAVE).then(function (out) { return { bytes: out, annots: annots }; });
    });
  }

  var API = {
    MARK: MARK,
    hasMarker: hasMarker,
    normalize: normalize,
    noteRect: noteRect,
    annotRect: annotRect,
    applyAnnotations: applyAnnotations,
    extractAnnotations: extractAnnotations
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof global !== "undefined") global.BadaPdfEdit = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
