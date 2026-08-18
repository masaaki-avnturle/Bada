/*
 * pdf_symbols.js — 数学論文 PDF から「方程式の記号」を実抽出するミニ PDF パーサ
 * Ω-Whispered / ウィスパード適性検査 — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * 依存ゼロ。ブラウザ(DecompressionStream)と Node 18+ の両方で動作する。
 *
 * 対応:
 *   - 通常オブジェクト + 圧縮オブジェクトストリーム(/Type /ObjStm, PDF 1.5+)
 *   - FlateDecode ストリームの伸長 (DecompressionStream 'deflate' / 'deflate-raw')
 *   - /Type /Page の /Resources /Font と /Contents を辿ったページ単位のテキスト抽出
 *   - フォント別デコード:
 *       (1) /ToUnicode CMap (bfchar / bfrange)           ← 最も確実
 *       (2) /Encoding /Differences のグリフ名 → Unicode  ← LaTeX サブセットフォント
 *       (3) CM/AMS フォント (CMMI/CMSY/CMEX/CMR/MSBM/EUFM) の内蔵エンコーディング
 *   - Type0(Identity-H 等) の 2 バイトコード
 *
 * 非対応(正直な限界): スキャン画像だけの PDF、暗号化 PDF、上記以外の特殊エンコーディング。
 * 抽出できない場合は symbols が空で返る(偽の結果は返さない)。
 */
(function (root) {
  "use strict";

  /* ============================ グリフ名 → Unicode ============================ */
  /* TeX/AGL でよく現れる数学グリフ名のみ。網羅ではなく「方程式の記号」に絞る。 */
  var GLYPH = {
    /* 演算子・関係子 */
    integral: "∫", integraltext: "∫", integraldisplay: "∫", contourintegral: "∮",
    summationtext: "∑", summationdisplay: "∑", summation: "∑",
    producttext: "∏", productdisplay: "∏", product: "∏",
    coproducttext: "∐", coproductdisplay: "∐", coproduct: "∐",
    partialdiff: "∂", gradient: "∇", nabla: "∇", Delta: "Δ", increment: "Δ",
    infinity: "∞", radical: "√", radicalbig: "√", surd: "√",
    plusminus: "±", minusplus: "∓", minus: "−", multiply: "×", divide: "÷",
    asteriskmath: "∗", periodcentered: "·", bullet: "∙", star: "⋆",
    circleplus: "⊕", circlemultiply: "⊗", circleminus: "⊖", circledivide: "⊘",
    circledot: "⊙", circlecopyrt: "○", bigcircle: "○", openbullet: "∘",
    circleplusdisplay: "⨁", circlemultiplydisplay: "⨂", circledotdisplay: "⨀",
    circleplustext: "⨁", circlemultiplytext: "⨂", circledottext: "⨀",
    equivalence: "≡", similar: "∼", similarequal: "≃", approxequal: "≈",
    congruent: "≅", asymptequal: "≍", notequal: "≠", proportional: "∝",
    lessequal: "≤", greaterequal: "≥", muchless: "≪", muchgreater: "≫",
    precedes: "≺", follows: "≻", precedesequal: "≼", followsequal: "≽",
    /* 集合・論理 */
    element: "∈", owner: "∋", notelement: "∉", propersubset: "⊂", propersuperset: "⊃",
    reflexsubset: "⊆", reflexsuperset: "⊇", intersection: "∩", union: "∪",
    unionmulti: "⊎", unionsq: "⊔", intersectionsq: "⊓", followsorcurly: "⊒",
    precedesorcurly: "⊑", emptyset: "∅", universal: "∀", existential: "∃",
    logicalnot: "¬", logicaland: "∧", logicalor: "∨",
    logicalanddisplay: "⋀", logicalordisplay: "⋁", uniondisplay: "⋃", intersectiondisplay: "⋂",
    turnstileleft: "⊢", turnstileright: "⊣", perpendicular: "⊥", tackdown: "⊤", tackup: "⊥",
    /* 矢印 */
    arrowleft: "←", arrowright: "→", arrowup: "↑", arrowdown: "↓", arrowboth: "↔",
    arrowdblleft: "⇐", arrowdblright: "⇒", arrowdblboth: "⇔", arrowdblup: "⇑", arrowdbldown: "⇓",
    arrownortheast: "↗", arrowsoutheast: "↘", arrownorthwest: "↖", arrowsouthwest: "↙",
    mapsto: "↦", arrowhookleft: "↩", arrowhookright: "↪", arrowtailright: "↣",
    /* 特殊文字 */
    aleph: "ℵ", weierstrass: "℘", Ifraktur: "ℑ", Rfraktur: "ℜ", scriptl: "ℓ",
    dagger: "†", daggerdbl: "‡", section: "§", paragraph: "¶", prime: "′", minute: "′",
    angbracketleft: "⟨", angbracketright: "⟩", bardbl: "‖", bar: "|",
    floorleft: "⌊", floorright: "⌋", ceilingleft: "⌈", ceilingright: "⌉",
    braceleft: "{", braceright: "}", wreathproduct: "≀", amalg: "⨿",
    ellipsis: "…", periodcentereddots: "⋯", ldots: "…", cdots: "⋯", vdots: "⋮", ddots: "⋱",
    triangle: "△", triangleinv: "▽", triangleleft: "◁", triangleright: "▷",
    trianglelefteq: "⊴", trianglerighteq: "⊵", ltimes: "⋉", rtimes: "⋊",
    lessorequalslant: "⩽", greaterorequalslant: "⩾", squareimage: "⊏", squareoriginal: "⊐",
    square: "□", filledsquare: "■", lozenge: "◊", hbar: "ℏ", hslash: "ℏ",
    /* ギリシャ小文字 */
    alpha: "α", beta: "β", gamma: "γ", delta: "δ", epsilon: "ε", epsilon1: "ε",
    varepsilon: "ε", zeta: "ζ", eta: "η", theta: "θ", theta1: "ϑ", vartheta: "ϑ",
    iota: "ι", kappa: "κ", lambda: "λ", mu: "μ", nu: "ν", xi: "ξ", omicron: "ο",
    pi: "π", pi1: "ϖ", varpi: "ϖ", rho: "ρ", rho1: "ϱ", varrho: "ϱ",
    sigma: "σ", sigma1: "ς", varsigma: "ς", tau: "τ", upsilon: "υ",
    phi: "φ", phi1: "ϕ", varphi: "ϕ", chi: "χ", psi: "ψ", omega: "ω",
    /* ギリシャ大文字 */
    Gamma: "Γ", Theta: "Θ", Lambda: "Λ", Xi: "Ξ", Pi: "Π", Sigma: "Σ",
    Upsilon: "Υ", Phi: "Φ", Psi: "Ψ", Omega: "Ω"
  };

  /* ==================== CM / AMS フォントの内蔵エンコーディング ==================== */
  function fillStr(map, start, str) {
    var arr = Array.from(str);
    for (var i = 0; i < arr.length; i++) if (arr[i] !== " ") map[start + i] = arr[i];
  }
  function fillArr(map, start, arr) {
    for (var i = 0; i < arr.length; i++) if (arr[i]) map[start + i] = arr[i];
  }
  function range(map, start, from, count) {
    for (var i = 0; i < count; i++) map[start + i] = String.fromCharCode(from + i);
  }

  var SCRIPT = ["𝒜","ℬ","𝒞","𝒟","ℰ","ℱ","𝒢","ℋ","ℐ","𝒥","𝒦","ℒ","ℳ","𝒩","𝒪","𝒫","𝒬","ℛ","𝒮","𝒯","𝒰","𝒱","𝒲","𝒳","𝒴","𝒵"];
  var BBOARD = ["𝔸","𝔹","ℂ","𝔻","𝔼","𝔽","𝔾","ℍ","𝕀","𝕁","𝕂","𝕃","𝕄","ℕ","𝕆","ℙ","ℚ","ℝ","𝕊","𝕋","𝕌","𝕍","𝕎","𝕏","𝕐","ℤ"];
  var FRAK_U = ["𝔄","𝔅","ℭ","𝔇","𝔈","𝔉","𝔊","ℌ","ℑ","𝔍","𝔎","𝔏","𝔐","𝔑","𝔒","𝔓","𝔔","ℜ","𝔖","𝔗","𝔘","𝔙","𝔚","𝔛","𝔜","ℨ"];
  var FRAK_L = ["𝔞","𝔟","𝔠","𝔡","𝔢","𝔣","𝔤","𝔥","𝔦","𝔧","𝔨","𝔩","𝔪","𝔫","𝔬","𝔭","𝔮","𝔯","𝔰","𝔱","𝔲","𝔳","𝔴","𝔵","𝔶","𝔷"];

  /* CMMI (math italic): 大文字ギリシャ・小文字ギリシャ・∂ など */
  var ENC_CMMI = {};
  fillStr(ENC_CMMI, 0x00, "ΓΔΘΛΞΠΣΥΦΨΩ");
  fillStr(ENC_CMMI, 0x0b, "αβγδεζηθικλμνξπρστυφχψω");
  fillStr(ENC_CMMI, 0x22, "εϑϖϱςϕ");
  fillStr(ENC_CMMI, 0x28, "↼↽⇀⇁");
  range(ENC_CMMI, 0x30, 0x30, 10);            /* oldstyle digits */
  fillStr(ENC_CMMI, 0x3a, ".,</>⋆∂");
  range(ENC_CMMI, 0x41, 0x41, 26);            /* italic A-Z → A-Z */
  fillStr(ENC_CMMI, 0x5b, "♭♮♯⌣⌢ℓ");
  range(ENC_CMMI, 0x61, 0x61, 26);            /* italic a-z → a-z */
  fillStr(ENC_CMMI, 0x7b, "ıȷ℘");

  /* CMSY (math symbols) */
  var ENC_CMSY = {};
  fillStr(ENC_CMSY, 0x00, "−·×∗÷⋄±∓⊕⊖⊗⊘⊙○∘∙");
  fillStr(ENC_CMSY, 0x10, "≍≡⊆⊇≤≥≼≽∼≈⊂⊃≪≫≺≻");
  fillStr(ENC_CMSY, 0x20, "←→↑↓↔↗↘≃⇐⇒⇑⇓⇔↖↙∝");
  fillStr(ENC_CMSY, 0x30, "′∞∈∋△▽ ↦∀∃¬∅ℜℑ⊤⊥");
  ENC_CMSY[0x40] = "ℵ";
  fillArr(ENC_CMSY, 0x41, SCRIPT);
  fillStr(ENC_CMSY, 0x5b, "∪∩⊎∧∨⊢⊣⌊⌋⌈⌉{}⟨⟩|‖↕⇕\\≀√⨿∇∫⊔⊓⊑⊒§†‡¶♣♦♥♠");

  /* CMEX (large operators): text サイズと display サイズ */
  var ENC_CMEX = {};
  fillStr(ENC_CMEX, 0x50, "∑∏∫∪∩⊎∧∨∑∏∫∪∩⊎∧∨");
  fillStr(ENC_CMEX, 0x60, "∐∐");

  /* CMR (roman): 0x00-0x0A に立体大文字ギリシャ */
  var ENC_CMR = {};
  fillStr(ENC_CMR, 0x00, "ΓΔΘΛΞΠΣΥΦΨΩ");
  for (var cr = 0x21; cr <= 0x7a; cr++) ENC_CMR[cr] = String.fromCharCode(cr);

  /* MSBM (AMS): 黒板太字 𝔸..ℤ */
  var ENC_MSBM = {};
  fillArr(ENC_MSBM, 0x41, BBOARD);

  /* EUFM (Euler Fraktur): 𝔤, 𝔪, 𝔭 などリー環/イデアル記号 */
  var ENC_EUFM = {};
  fillArr(ENC_EUFM, 0x41, FRAK_U);
  fillArr(ENC_EUFM, 0x61, FRAK_L);

  function builtinEncoding(baseFont) {
    var b = (baseFont || "").toUpperCase();
    if (/CMMI|CMMIB|MATHITALIC/.test(b)) return ENC_CMMI;
    if (/CMSY|CMBSY|MATHSYMBOL/.test(b)) return ENC_CMSY;
    if (/CMEX|MATHEXTENSION/.test(b)) return ENC_CMEX;
    if (/MSBM|BBOLD|BBM/.test(b)) return ENC_MSBM;
    if (/EUFM|EUFB|FRAKTUR/.test(b)) return ENC_EUFM;
    if (/CMR|CMB|CMTI|CMSS|CMTT|CMCSC/.test(b)) return ENC_CMR;
    return null;
  }

  /* ================================ 低レベル補助 ================================ */

  /* バイト列 → Latin1 文字列 (1 文字 = 1 バイト)。正規表現/indexOf で走査するため。 */
  function toLatin1(bytes) {
    var CH = 0x8000, out = [];
    for (var i = 0; i < bytes.length; i += CH) {
      out.push(String.fromCharCode.apply(null, bytes.subarray(i, Math.min(i + CH, bytes.length))));
    }
    return out.join("");
  }
  function toBytes(str) {
    var b = new Uint8Array(str.length);
    for (var i = 0; i < str.length; i++) b[i] = str.charCodeAt(i) & 0xff;
    return b;
  }

  /* FlateDecode 伸長。zlib ヘッダ付き('deflate')→生('deflate-raw')の順で試す。 */
  function inflate(bytes) {
    var DS = root.DecompressionStream;
    if (!DS) return Promise.resolve(null);
    function attempt(fmt) {
      try {
        var ds = new DS(fmt);
        var w = ds.writable.getWriter();
        var noop = function () {};
        w.write(bytes).catch(noop); w.close().catch(noop);   /* 末尾ゴミ等の拒否は握り潰す */
        var reader = ds.readable.getReader(), chunks = [], total = 0;
        function collect() {
          var out = new Uint8Array(total), o = 0;
          for (var i = 0; i < chunks.length; i++) { out.set(chunks[i], o); o += chunks[i].length; }
          return out;
        }
        return (function pump() {
          return reader.read().then(function (r) {
            if (r.done) return collect();
            chunks.push(r.value); total += r.value.length;
            return pump();
          }, function (err) {
            /* "trailing junk"/途中破損でも、そこまでに伸長できた分は使う */
            if (total > 0) return collect();
            throw err;
          });
        })();
      } catch (e) { return Promise.reject(e); }
    }
    return attempt("deflate").catch(function () {
      return attempt("deflate-raw").catch(function () { return null; });
    });
  }

  /* << >> / [ ] / ( ) を数えながら 1 つの値トークンを読む */
  function readValue(s, i) {
    while (i < s.length && /\s/.test(s.charAt(i))) i++;
    var c = s.charAt(i);
    if (c === "<" && s.charAt(i + 1) === "<") {
      var d = 0, j = i;
      while (j < s.length) {
        if (s.charAt(j) === "<" && s.charAt(j + 1) === "<") { d++; j += 2; continue; }
        if (s.charAt(j) === ">" && s.charAt(j + 1) === ">") { d--; j += 2; if (!d) break; continue; }
        j++;
      }
      return { value: s.slice(i, j), end: j };
    }
    if (c === "[") {
      var dd = 0, k = i;
      while (k < s.length) {
        if (s.charAt(k) === "[") dd++;
        else if (s.charAt(k) === "]") { dd--; if (!dd) { k++; break; } }
        k++;
      }
      return { value: s.slice(i, k), end: k };
    }
    var m = /^(\d+\s+\d+\s+R\b|\/[^\s\/\[\]<>()]*|[-+]?[\d.]+|true|false|null|<[0-9A-Fa-f\s]*>)/.exec(s.slice(i, i + 256));
    if (m) return { value: m[1], end: i + m[1].length };
    return { value: "", end: i + 1 };
  }

  /* 辞書文字列から /Key の値を取り出す (トップレベルのみ) */
  function dictGet(dict, key) {
    if (!dict) return null;
    var re = new RegExp("\\/" + key + "(?![A-Za-z0-9])", "g"), m;
    while ((m = re.exec(dict))) {
      /* ネストした辞書内のキーを拾わないよう、深さ 1 のものだけ採用 */
      var depth = 0;
      for (var i = 0; i < m.index; i++) {
        if (dict.charAt(i) === "<" && dict.charAt(i + 1) === "<") { depth++; i++; }
        else if (dict.charAt(i) === ">" && dict.charAt(i + 1) === ">") { depth--; i++; }
      }
      if (depth <= 1) return readValue(dict, m.index + m[0].length).value;
    }
    return null;
  }

  function isRef(v) { return !!v && /^\d+\s+\d+\s+R$/.test(v.trim()); }
  function refNum(v) { return parseInt(v, 10); }

  /* ============================== PDF ドキュメント ============================== */

  function PDFDoc(raw) {
    this.raw = raw;         /* Latin1 文字列 */
    this.objs = {};         /* objnum -> {dict, sStart, sEnd} または {body} */
  }

  /* すべての "N G obj ... endobj" を走査 */
  PDFDoc.prototype.scanObjects = function () {
    var s = this.raw, re = /(\d+)\s+(\d+)\s+obj\b/g, m;
    while ((m = re.exec(s))) {
      var num = parseInt(m[1], 10), start = m.index + m[0].length;
      var sIdx = s.indexOf("stream", start), eIdx = s.indexOf("endobj", start);
      if (eIdx < 0) eIdx = s.length;
      if (sIdx >= 0 && sIdx < eIdx) {
        var dict = s.slice(start, sIdx);
        var p = sIdx + 6;
        if (s.charAt(p) === "\r") p++;
        if (s.charAt(p) === "\n") p++;
        var len = dictGet(dict, "Length"), endS = -1;
        if (len && /^\d+$/.test(len.trim())) {
          var cand = p + parseInt(len, 10);
          if (s.slice(cand, cand + 20).indexOf("endstream") >= 0) endS = cand;
        }
        if (endS < 0) endS = s.indexOf("endstream", p);
        if (endS < 0) endS = eIdx;
        this.objs[num] = { dict: dict, sStart: p, sEnd: endS };
        re.lastIndex = Math.max(re.lastIndex, endS);
      } else {
        this.objs[num] = { body: s.slice(start, eIdx) };
      }
    }
  };

  /* オブジェクトのストリームを (必要なら伸長して) 文字列で返す */
  PDFDoc.prototype.streamText = function (o) {
    if (!o || o.sStart === undefined) return Promise.resolve(null);
    var bytes = toBytes(this.raw.slice(o.sStart, o.sEnd));
    var f = dictGet(o.dict, "Filter") || "";
    if (/FlateDecode/.test(f)) {
      return inflate(bytes).then(function (out) { return out ? toLatin1(out) : null; });
    }
    if (/DCTDecode|JPXDecode|CCITTFaxDecode|JBIG2Decode|RunLengthDecode|LZWDecode/.test(f)) return Promise.resolve(null);
    return Promise.resolve(toLatin1(bytes));
  };

  /* /Type /ObjStm を展開して this.objs に流し込む */
  PDFDoc.prototype.expandObjStreams = function () {
    var self = this, nums = Object.keys(this.objs), chain = Promise.resolve();
    nums.forEach(function (n) {
      var o = self.objs[n];
      if (!o.dict || !/\/Type\s*\/ObjStm/.test(o.dict)) return;
      chain = chain.then(function () {
        return self.streamText(o).then(function (txt) {
          if (!txt) return;
          var N = parseInt(dictGet(o.dict, "N") || "0", 10);
          var first = parseInt(dictGet(o.dict, "First") || "0", 10);
          var head = txt.slice(0, first).trim().split(/\s+/);
          for (var i = 0; i < N; i++) {
            var onum = parseInt(head[2 * i], 10), off = parseInt(head[2 * i + 1], 10);
            if (isNaN(onum) || isNaN(off)) continue;
            var nextOff = (i + 1 < N) ? parseInt(head[2 * i + 3], 10) : (txt.length - first);
            if (isNaN(nextOff)) nextOff = txt.length - first;
            if (self.objs[onum] === undefined)
              self.objs[onum] = { body: txt.slice(first + off, first + nextOff) };
          }
        });
      });
    });
    return chain;
  };

  /* 参照を解決して辞書/本体文字列を返す */
  PDFDoc.prototype.deref = function (v) {
    if (!v) return null;
    if (isRef(v)) {
      var o = this.objs[refNum(v)];
      if (!o) return null;
      return o.body !== undefined ? o.body : o.dict;
    }
    return v;
  };
  PDFDoc.prototype.derefObj = function (v) {
    if (isRef(v)) return this.objs[refNum(v)] || null;
    return null;
  };

  /* =============================== CMap / フォント =============================== */

  function hexToStr(h) {
    h = h.replace(/[^0-9A-Fa-f]/g, "");
    var out = "";
    for (var i = 0; i < h.length; i += 4) {
      var quad = h.substr(i, 4);
      while (quad.length < 4) quad += "0";
      out += String.fromCharCode(parseInt(quad, 16));
    }
    return out;
  }

  function parseToUnicode(txt) {
    var map = {}, m;
    var reChar = /beginbfchar([\s\S]*?)endbfchar/g;
    while ((m = reChar.exec(txt))) {
      var body = m[1], mm, re2 = /<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/g;
      while ((mm = re2.exec(body))) map[parseInt(mm[1], 16)] = hexToStr(mm[2]);
    }
    var reRange = /beginbfrange([\s\S]*?)endbfrange/g;
    while ((m = reRange.exec(txt))) {
      var b = m[1], r1 = /<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])/g, x;
      while ((x = r1.exec(b))) {
        var lo = parseInt(x[1], 16), hi = parseInt(x[2], 16), dst = x[3];
        if (hi < lo || hi - lo > 65535) continue;
        if (dst.charAt(0) === "[") {
          var items = dst.match(/<([0-9A-Fa-f]+)>/g) || [];
          for (var i = 0; i < items.length && lo + i <= hi; i++) map[lo + i] = hexToStr(items[i].slice(1, -1));
        } else {
          var base = dst.slice(1, -1), baseVal = parseInt(base, 16);
          for (var c = lo; c <= hi; c++) map[c] = String.fromCharCode(baseVal + (c - lo));
        }
      }
    }
    return map;
  }

  function parseDifferences(arrStr) {
    var map = {}, cur = 0;
    var re = /(\d+)|\/([^\s\/\[\]]+)/g, m;
    while ((m = re.exec(arrStr))) {
      if (m[1] !== undefined) cur = parseInt(m[1], 10);
      else { map[cur] = m[2]; cur++; }
    }
    return map;
  }

  /* フォント辞書 → { twoByte, map: code→文字列 } のデコーダを作る */
  PDFDoc.prototype.buildFont = function (fontDict) {
    var self = this;
    if (!fontDict) return Promise.resolve(null);
    var baseFont = (dictGet(fontDict, "BaseFont") || "").replace(/^\//, "");
    var subtype = (dictGet(fontDict, "Subtype") || "").replace(/^\//, "");
    var twoByte = subtype === "Type0";
    var font = { base: baseFont, twoByte: twoByte, map: {}, src: "none" };

    var tuObj = this.derefObj(dictGet(fontDict, "ToUnicode") || "");
    var step = tuObj ? this.streamText(tuObj).then(function (txt) {
      if (txt) {
        var m = parseToUnicode(txt);
        if (Object.keys(m).length) { font.map = m; font.src = "ToUnicode"; }
      }
    }) : Promise.resolve();

    return step.then(function () {
      /* Differences (ToUnicode が無い/穴がある場合の補完) */
      var encStr = self.deref(dictGet(fontDict, "Encoding"));
      if (encStr && /\/Differences/.test(encStr)) {
        var diffArr = dictGet(encStr, "Differences");
        if (diffArr) {
          var names = parseDifferences(diffArr), filled = 0;
          for (var code in names) {
            var name = names[code], u = GLYPH[name];
            if (!u && /^uni([0-9A-Fa-f]{4})$/.test(name)) u = String.fromCharCode(parseInt(RegExp.$1, 16));
            if (!u && /^[A-Za-z]$/.test(name)) u = name;
            if (u && font.map[code] === undefined) { font.map[code] = u; filled++; }
          }
          if (filled && font.src === "none") font.src = "Differences";
        }
      }
      /* CM/AMS 内蔵エンコーディング */
      var be = builtinEncoding(baseFont);
      if (be) {
        var added = 0;
        for (var c in be) if (font.map[c] === undefined) { font.map[c] = be[c]; added++; }
        if (added && font.src === "none") font.src = "builtin:" + baseFont.replace(/^[A-Z]{6}\+/, "");
      }
      if (font.src === "none" && !twoByte) font.src = "latin1";
      return font;
    });
  };

  function decodeString(bytes, font) {
    if (!font) return "";
    var out = "";
    if (font.twoByte) {
      for (var i = 0; i + 1 < bytes.length; i += 2) {
        var code = (bytes.charCodeAt(i) << 8) | bytes.charCodeAt(i + 1);
        var v = font.map[code];
        out += (v !== undefined) ? v : "";
      }
    } else {
      for (var j = 0; j < bytes.length; j++) {
        var c = bytes.charCodeAt(j), w = font.map[c];
        if (w !== undefined) out += w;
        else if (font.src === "latin1" && c >= 32 && c < 127) out += String.fromCharCode(c);
      }
    }
    return out;
  }

  /* =========================== コンテンツストリーム走査 =========================== */

  function readPdfString(s, i) {              /* i は '(' の位置 */
    var depth = 0, out = "", j = i;
    while (j < s.length) {
      var c = s.charAt(j);
      if (c === "\\") {
        var n = s.charAt(j + 1);
        if (/[0-7]/.test(n)) {
          var oct = /^[0-7]{1,3}/.exec(s.slice(j + 1))[0];
          out += String.fromCharCode(parseInt(oct, 8)); j += 1 + oct.length; continue;
        }
        var esc = { n: "\n", r: "\r", t: "\t", b: "\b", f: "\f", "(": "(", ")": ")", "\\": "\\" }[n];
        if (esc !== undefined) out += esc;
        else if (n !== "\n" && n !== "\r") out += n;
        j += 2; continue;
      }
      if (c === "(") { depth++; if (depth > 1) out += c; j++; continue; }
      if (c === ")") { depth--; if (!depth) { j++; break; } out += c; j++; continue; }
      out += c; j++;
    }
    return { str: out, end: j };
  }

  /* コンテンツからテキスト断片の配列を得る。fonts: リソース名→font */
  function extractRuns(content, fonts) {
    var runs = [], i = 0, n = content.length, cur = null, pending = [], lastName = null;
    while (i < n) {
      var c = content.charAt(i);
      if (c === "(") { var r = readPdfString(content, i); pending.push(r.str); i = r.end; continue; }
      if (c === "<" && content.charAt(i + 1) === "<") { i += 2; continue; }
      if (c === "<") {
        var e = content.indexOf(">", i);
        if (e < 0) break;
        var hex = content.slice(i + 1, e).replace(/[^0-9A-Fa-f]/g, "");
        if (hex.length % 2) hex += "0";
        var st = "";
        for (var h = 0; h < hex.length; h += 2) st += String.fromCharCode(parseInt(hex.substr(h, 2), 16));
        pending.push(st); i = e + 1; continue;
      }
      if (c === ">") { i++; continue; }
      if (c === "/") {
        var m = /^\/([^\s\/\[\]<>()]*)/.exec(content.slice(i, i + 128));
        lastName = m ? m[1] : null;
        i += m ? m[0].length : 1; continue;
      }
      if (/[A-Za-z'"]/.test(c)) {
        var om = /^[A-Za-z'"*0-9]+/.exec(content.slice(i, i + 32));
        var op = om ? om[0] : c;
        i += op.length;
        if (op === "Tf") { cur = fonts[lastName] || null; pending = []; }
        else if (op === "Tj" || op === "TJ" || op === "'" || op === '"') {
          var txt = "";
          for (var p = 0; p < pending.length; p++) txt += decodeString(pending[p], cur);
          if (txt) runs.push(txt);
          pending = [];
        } else pending = [];
        continue;
      }
      i++;
    }
    return runs;
  }

  /* ============================== 記号フィルタ ============================== */

  /* 「方程式の記号」として数える Unicode 範囲 */
  function isMathSymbol(ch) {
    var c = ch.codePointAt(0);
    if (c >= 0x0391 && c <= 0x03c9) return true;                   /* ギリシャ */
    if (c >= 0x03d0 && c <= 0x03f5) return true;                   /* ϑ ϖ ϱ ϕ など */
    if (c >= 0x2100 && c <= 0x214f) return true;                   /* ℂ ℕ ℝ ℤ ℵ ℑ ℜ ℏ ℓ ℘ */
    if (c >= 0x2190 && c <= 0x21ff) return true;                   /* 矢印 */
    if (c >= 0x2200 && c <= 0x22ff) return true;                   /* 数学演算子 */
    if (c >= 0x2308 && c <= 0x232a) return true;                   /* ⌈⌉⌊⌋⟨⟩ */
    if (c >= 0x27c0 && c <= 0x27ef) return true;
    if (c >= 0x2900 && c <= 0x297f) return true;                   /* 補助矢印 */
    if (c >= 0x2a00 && c <= 0x2aff) return true;                   /* 補助演算子 ⨁ ⨂ */
    if (c >= 0x1d400 && c <= 0x1d7ff) return true;                 /* 数学英数記号 𝒪 𝔤 𝕂 */
    if (c === 0x00b1 || c === 0x00d7 || c === 0x00f7) return true; /* ± × ÷ */
    if (c === 0x2032 || c === 0x2033) return true;                 /* ′ ″ */
    if (c === 0x2020 || c === 0x2021) return true;                 /* † ‡ */
    if (c === 0x00ac || c === 0x2016) return true;                 /* ¬ ‖ */
    if (c === 0x25b3 || c === 0x25bd || c === 0x25a1) return true; /* △ ▽ □ */
    return false;
  }

  /* ================================ 公開 API ================================ */

  /**
   * PDF バイト列から数式記号を抽出する。
   * @param {Uint8Array} bytes
   * @param {function(string)} [onProgress]
   * @returns {Promise<{ok:boolean,symbols:Array,fragments:Array,pages:number,fonts:Array,glyphs:number,note:string}>}
   */
  function extract(bytes, onProgress) {
    var report = function (m) { if (onProgress) { try { onProgress(m); } catch (e) {} } };
    var doc = new PDFDoc(toLatin1(bytes));
    report("オブジェクトを走査中…");
    doc.scanObjects();

    if (/trailer[\s\S]{0,600}\/Encrypt/.test(doc.raw)) {
      return Promise.resolve({ ok: false, symbols: [], fragments: [], pages: 0, fonts: [], glyphs: 0,
        note: "暗号化された PDF です(このアプリは復号しません)。" });
    }

    return doc.expandObjStreams().then(function () {
      report("ページと埋め込みフォントを解析中…");
      var pageNums = [];
      for (var k in doc.objs) {
        var o = doc.objs[k], d = o.dict !== undefined ? o.dict : o.body;
        if (d && /\/Type\s*\/Page(?![sA-Za-z])/.test(d)) pageNums.push(k);
      }
      var counts = {}, fragments = [], fontsSeen = {}, stats = { glyphs: 0 };

      function resourcesOf(pageDict, depth) {
        var res = dictGet(pageDict, "Resources");
        if (res) return doc.deref(res);
        if (depth > 6) return null;
        var pd = doc.deref(dictGet(pageDict, "Parent"));
        return pd ? resourcesOf(pd, depth + 1) : null;
      }

      var chain = Promise.resolve();
      pageNums.forEach(function (pn, idx) {
        chain = chain.then(function () {
          if (idx % 10 === 0) report("ページ解析 " + (idx + 1) + " / " + pageNums.length);
          var po = doc.objs[pn], pd = po.dict !== undefined ? po.dict : po.body;
          var res = resourcesOf(pd, 0);
          if (!res) return;
          var fontDictStr = doc.deref(dictGet(res, "Font"));
          if (!fontDictStr) return;

          /* リソース名 → フォント辞書 */
          var fonts = {}, entries = [], re = /\/([^\s\/\[\]<>()]+)\s*(\d+\s+\d+\s+R|<<)/g, m;
          while ((m = re.exec(fontDictStr))) {
            var val = m[2] === "<<" ? readValue(fontDictStr, m.index + m[0].length - 2).value : m[2];
            entries.push([m[1], val]);
          }
          var fchain = Promise.resolve();
          entries.forEach(function (ent) {
            fchain = fchain.then(function () {
              var fd = isRef(ent[1]) ? doc.deref(ent[1]) : ent[1];
              return doc.buildFont(fd).then(function (f) {
                if (!f) return;
                fonts[ent[0]] = f;
                var key = (f.base.replace(/^[A-Z]{6}\+/, "") || "(no name)") + " [" + f.src + "]";
                fontsSeen[key] = (fontsSeen[key] || 0) + 1;
              });
            });
          });

          return fchain.then(function () {
            var contents = dictGet(pd, "Contents");
            if (!contents) return;
            var refs = [];
            if (isRef(contents)) refs.push(contents);
            else { var mm, r2 = /\d+\s+\d+\s+R/g; while ((mm = r2.exec(contents))) refs.push(mm[0]); }
            var cchain = Promise.resolve(), pageText = [];
            refs.forEach(function (rf) {
              cchain = cchain.then(function () {
                var co = doc.derefObj(rf);
                if (!co) return;
                return doc.streamText(co).then(function (txt) { if (txt) pageText.push(txt); });
              });
            });
            return cchain.then(function () {
              if (!pageText.length) return;
              var runs = extractRuns(pageText.join("\n"), fonts);
              for (var i = 0; i < runs.length; i++) {
                var t = runs[i], hasSym = false, arr = Array.from(t);
                for (var q = 0; q < arr.length; q++) {
                  stats.glyphs++;
                  if (isMathSymbol(arr[q])) { counts[arr[q]] = (counts[arr[q]] || 0) + 1; hasSym = true; }
                }
                if (hasSym && arr.length <= 80 && fragments.length < 400) {
                  var tt = t.replace(/\s+/g, " ").trim();
                  if (tt.length >= 2) fragments.push(tt);
                }
              }
            });
          });
        });
      });

      return chain.then(function () {
        var symbols = Object.keys(counts).map(function (ch) { return { ch: ch, count: counts[ch] }; });
        symbols.sort(function (a, b) { return b.count - a.count; });
        var fonts = Object.keys(fontsSeen).sort();
        var ok = symbols.length > 0;
        var note = ok ? "" :
          (stats.glyphs === 0
            ? "テキストを抽出できませんでした(スキャン画像のみの PDF、または未対応の圧縮方式の可能性があります)。"
            : "テキストは抽出できましたが、数式記号は見つかりませんでした。");
        report("完了");
        return { ok: ok, symbols: symbols, fragments: fragments, pages: pageNums.length,
                 fonts: fonts, glyphs: stats.glyphs, note: note };
      });
    });
  }

  var API = { extract: extract, isMathSymbol: isMathSymbol, GLYPH: GLYPH, _PDFDoc: PDFDoc };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.PDFSymbols = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
