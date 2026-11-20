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
 *   { type:"textedit",  page, x, y(ベースライン), text, size, color, font:"sans|serif|mono",
 *                       cover:[x1,y1,x2,y2]|null, bg:"#ffffff" }   ← 文字修正 (cover = 元の文字を隠す範囲)
 *   { type:"erase",     page, rects:[[x1,y1,x2,y2],…], color:"#ffffff" }   ← 消去 (塗りつぶし)
 *
 * PDF 専用の編集ツール:
 *   flatten(PDFLib, bytes, annots)   → 書き込みをページ本体に焼き込んだ PDF (注釈ではなくなる)
 *   pageOp(PDFLib, bytes, op)        → ページ操作後の { bytes, annots(結合元の注釈) }
 *        op: {op:"rotate",page,delta} {op:"delete",page} {op:"move",page,to}
 *            {op:"blank",at} {op:"merge",bytes}
 *   remapAnnots(annots, op, info)    → ページ操作に合わせて注釈のページ番号を付け替える
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
  /* 文字修正の文字が占める範囲 [x1,y1,x2,y2] (a.x, a.y は 1 行目のベースライン左端) */
  function textBox(a) {
    var size = a.size || 12, lines = noteLines(a), w = 0;
    for (var i = 0; i < lines.length; i++) w = Math.max(w, lineEm(lines[i]));
    return [a.x, a.y - size * 0.28 - (lines.length - 1) * size * 1.2, a.x + Math.max(0.5, w) * size, a.y + size * 0.92];
  }
  function annotRect(a) {
    var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity, i, j;
    function add(x, y) { if (x < x1) x1 = x; if (x > x2) x2 = x; if (y < y1) y1 = y; if (y > y2) y2 = y; }
    if (a.type === "note") return noteRect(a);
    if (a.type === "textedit") {
      var tb = textBox(a);
      add(tb[0], tb[1]); add(tb[2], tb[3]);
      if (a.cover) { add(a.cover[0], a.cover[1]); add(a.cover[2], a.cover[3]); }
      return [x1, y1, x2, y2];
    }
    if (a.type === "highlight" || a.type === "erase") {
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
    if (a.type === "erase") {
      var er = [];
      for (i = 0; i < (a.rects || []).length; i++) {
        var q0 = a.rects[i];
        if (!q0 || q0.length !== 4 || !q0.every(fin)) continue;
        er.push([Math.min(q0[0], q0[2]), Math.min(q0[1], q0[3]), Math.max(q0[0], q0[2]), Math.max(q0[1], q0[3])]);
      }
      return er.length ? { type: "erase", page: page, rects: er, color: a.color || "#ffffff" } : null;
    }
    if (a.type === "textedit") {
      var tx = String(a.text == null ? "" : a.text).replace(/\r\n?/g, "\n").replace(/\s+$/, "");
      if (!fin(a.x) || !fin(a.y)) return null;
      var cover = null;
      if (a.cover && a.cover.length === 4 && a.cover.every(fin)) {
        cover = [Math.min(a.cover[0], a.cover[2]), Math.min(a.cover[1], a.cover[3]), Math.max(a.cover[0], a.cover[2]), Math.max(a.cover[1], a.cover[3])];
      }
      if (!tx.trim() && !cover) return null;          /* 隠す範囲も文字も無ければ何もしない */
      return { type: "textedit", page: page, x: a.x, y: a.y, text: tx, size: fin(a.size) && a.size > 0 ? a.size : 12,
               color: a.color || "#000000", font: /^(serif|mono)$/.test(a.font) ? a.font : "sans",
               cover: cover, bg: a.bg || "#ffffff" };
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

  function eraseStream(a) {
    var s = rgbOp(a.color, "rg") + "\n";
    for (var i = 0; i < a.rects.length; i++) {
      var r = a.rects[i];
      s += n2(r[0]) + " " + n2(r[1]) + " " + n2(r[2] - r[0]) + " " + n2(r[3] - r[1]) + " re\n";
    }
    return s + "f\n";
  }
  function textEditStream(a, ascii) {
    var size = a.size || 12, lines = noteLines(a), s = "";
    if (a.cover) {
      s += rgbOp(a.bg, "rg") + "\n" + n2(a.cover[0]) + " " + n2(a.cover[1]) + " " +
           n2(a.cover[2] - a.cover[0]) + " " + n2(a.cover[3] - a.cover[1]) + " re f\n";
    }
    if (!a.text.trim()) return s;
    s += "BT /F1 " + n2(size) + " Tf " + n2(size * 1.2) + " TL " + rgbOp(a.color, "rg") + "\n" +
         n2(a.x) + " " + n2(a.y) + " Td\n";
    for (var i = 0; i < lines.length; i++) {
      s += (ascii ? "(" + litEscape(lines[i]) + ")" : "<" + utf16Hex(lines[i]) + ">") + " Tj T*\n";
    }
    return s + "ET\n";
  }
  var LATIN_FONTS = { sans: "Helvetica", serif: "Times-Roman", mono: "Courier" };
  function latinFont(kind) {
    return { Type: "Font", Subtype: "Type1", BaseFont: LATIN_FONTS[kind] || "Helvetica", Encoding: "WinAnsiEncoding" };
  }

  /* 日本語用: 非埋め込みの CID フォント (Adobe-Japan1 / UniJIS-UTF16-H)。
     フォント本体は PDF に入れず、ビューア側の日本語フォントで描画されます。 */
  function cjkFont(ctx, L, kind) {
    var name = kind === "serif" ? "KozMinPr6N-Regular" : (kind ? "KozGoPr6N-Medium" : "KozMinPr6N-Regular");
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

  /* 注釈 1 件ぶんの「見た目」(外観ストリーム = Form XObject) と注釈辞書の中身を作る */
  function buildParts(L, doc, a) {
    var ctx = doc.context, rect = annotRect(a), res, body, extra, ascii;
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
    } else if (a.type === "erase") {
      res = {};
      body = eraseStream(a);
      extra = { Subtype: "Square", C: rgb(a.color), IC: rgb(a.color), BS: { W: 0 } };
    } else if (a.type === "textedit") {
      ascii = isAscii(a.text);
      res = { Font: { F1: ascii ? latinFont(a.font) : cjkFont(ctx, L, a.font) } };
      body = textEditStream(a, ascii);
      extra = { Subtype: "FreeText", DA: L.PDFString.of(rgbOp(a.color, "rg") + " /Helv " + n2(a.size || 12) + " Tf") };
      if (a.text.trim()) extra.Contents = L.PDFHexString.fromText(a.text);
    } else {
      ascii = isAscii(a.text);
      res = { Font: { F1: ascii ? latinFont("sans") : cjkFont(ctx, L) } };
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
    return { ap: ap, rect: rect, extra: extra };
  }
  function buildAnnot(L, doc, a) {
    var ctx = doc.context, parts = buildParts(L, doc, a);
    var model = {};
    for (var k in a) if (k !== "page" && Object.prototype.hasOwnProperty.call(a, k)) model[k] = a[k];
    var dict = { Type: "Annot", Rect: parts.rect, F: 4, T: L.PDFString.of(MARK),
                 BadaData: L.PDFHexString.fromText(JSON.stringify(model)), AP: { N: parts.ap } };
    for (var e in parts.extra) dict[e] = parts.extra[e];
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

  /* ───────── 焼き込み: 書き込みをページ本体 (コンテンツ) に確定する ─────────
     注釈ではなくページの一部になるので、どのビューアでも必ず同じに表示・印刷され、
     以後は動かしたり消したりできなくなる。 */
  function flatten(L, bytes, annots) {
    return L.PDFDocument.load(bytes, { updateMetadata: false }).then(function (doc) {
      stripDoc(L, doc);
      var pages = doc.getPages(), n = 0;
      (annots || []).forEach(function (raw) {
        var a = normalize(raw);
        if (!a || a.page < 0 || a.page >= pages.length) return;
        var page = pages[a.page], parts = buildParts(L, doc, a);
        var name = page.node.newXObject("BadaFx", parts.ap);
        page.pushOperators(L.pushGraphicsState(), L.drawObject(name), L.popGraphicsState());
        n++;
      });
      return doc.save(SAVE);
    });
  }

  /* ───────── ページ操作 (回転 / 削除 / 並べ替え / 空白ページ / 結合) ─────────
     bytes は注釈を外した PDF。戻り値の annots は、結合した PDF に入っていた
     BadaCineVim の注釈 (ページ番号は結合後のもの)。 */
  function pageOp(L, bytes, op) {
    return L.PDFDocument.load(bytes, { updateMetadata: false }).then(function (doc) {
      var count = doc.getPageCount(), i = op.page | 0;
      function inRange(k) { return k >= 0 && k < count; }
      if (op.op === "rotate") {
        if (!inRange(i)) throw new Error("ページがありません");
        var pg = doc.getPage(i), cur = pg.getRotation().angle || 0;
        pg.setRotation(L.degrees(((cur + (op.delta || 90)) % 360 + 360) % 360));
      } else if (op.op === "delete") {
        if (!inRange(i)) throw new Error("ページがありません");
        if (count <= 1) throw new Error("最後の 1 ページは削除できません");
        doc.removePage(i);
      } else if (op.op === "move") {
        var to = op.to | 0;
        if (!inRange(i) || !inRange(to)) throw new Error("移動先がありません");
        if (to !== i) { var moving = doc.getPage(i); doc.removePage(i); doc.insertPage(to, moving); }
      } else if (op.op === "blank") {
        var at = Math.max(0, Math.min(count, op.at | 0));
        var ref = doc.getPage(Math.max(0, Math.min(count - 1, at - 1))).getSize();
        doc.insertPage(at, [ref.width, ref.height]);
      } else if (op.op === "merge") {
        return L.PDFDocument.load(op.bytes, { updateMetadata: false }).then(function (other) {
          return doc.copyPages(other, other.getPageIndices());
        }).then(function (copied) {
          copied.forEach(function (p) { doc.addPage(p); });
          var extra = stripDoc(L, doc).filter(function (a) { return a.page >= count; });
          return doc.save(SAVE).then(function (out) { return { bytes: out, annots: extra, added: copied.length }; });
        });
      } else {
        throw new Error("未対応のページ操作: " + op.op);
      }
      return doc.save(SAVE).then(function (out) { return { bytes: out, annots: [] }; });
    });
  }
  /* ページ操作に合わせて、手元の注釈のページ番号を付け替える (削除したページの注釈は消える) */
  function remapAnnots(annots, op) {
    var out = [], p = op.page | 0, to = op.to | 0, at = op.at | 0;
    (annots || []).forEach(function (a) {
      var k = a.page;
      if (op.op === "delete") { if (k === p) return; if (k > p) k--; }
      else if (op.op === "move") {
        if (k === p) k = to;
        else if (p < to && k > p && k <= to) k--;
        else if (p > to && k >= to && k < p) k++;
      }
      else if (op.op === "blank") { if (k >= at) k++; }
      a.page = k; out.push(a);
    });
    return out;
  }

  var API = {
    MARK: MARK,
    textBox: textBox,
    flatten: flatten,
    pageOp: pageOp,
    remapAnnots: remapAnnots,
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
