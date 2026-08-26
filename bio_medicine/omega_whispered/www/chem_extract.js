/*
 * chem_extract.js — PDF 本文から化学式・化学/物理の専門用語を検出する
 * Ω-Whispered — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * pdf_symbols.extract() が返す text を走査して、
 *   (1) 化学式らしいトークン (元素記号の並び。実在の元素記号のみ許可して検証する)
 *   (2) chem_phys_bank.js の専門用語 (日本語名・英語名の両方) の出現
 * を数える。検出結果は「その論文から出題する」化学・物理の設問に使われる。
 *
 * 依存ゼロ。Node からも require できる。
 */
(function (root) {
  "use strict";

  /* 元素記号(1-118)。化学式の妥当性検証に使う */
  var ELEMENTS = ("H,He,Li,Be,B,C,N,O,F,Ne,Na,Mg,Al,Si,P,S,Cl,Ar,K,Ca,Sc,Ti,V,Cr,Mn,Fe,Co,Ni,Cu,Zn," +
    "Ga,Ge,As,Se,Br,Kr,Rb,Sr,Y,Zr,Nb,Mo,Tc,Ru,Rh,Pd,Ag,Cd,In,Sn,Sb,Te,I,Xe,Cs,Ba,La,Ce,Pr,Nd,Pm,Sm," +
    "Eu,Gd,Tb,Dy,Ho,Er,Tm,Yb,Lu,Hf,Ta,W,Re,Os,Ir,Pt,Au,Hg,Tl,Pb,Bi,Po,At,Rn,Fr,Ra,Ac,Th,Pa,U,Np,Pu," +
    "Am,Cm,Bk,Cf,Es,Fm,Md,No,Lr,Rf,Db,Sg,Bh,Hs,Mt,Ds,Rg,Cn,Nh,Fl,Mc,Lv,Ts,Og").split(",");
  var ELEM_SET = {};
  ELEMENTS.forEach(function (e) { ELEM_SET[e] = 1; });

  /* よく知られた化合物の読み(検出できたときに説明として添える) */
  var KNOWN = {
    "H2O": "水", "CO2": "二酸化炭素", "CO": "一酸化炭素", "O2": "酸素", "N2": "窒素",
    "H2": "水素", "CH4": "メタン", "C2H6": "エタン", "C2H4": "エチレン", "C2H2": "アセチレン",
    "C6H6": "ベンゼン", "C6H12O6": "グルコース", "C2H5OH": "エタノール", "CH3OH": "メタノール",
    "CH3COOH": "酢酸", "NH3": "アンモニア", "H2SO4": "硫酸", "HCl": "塩酸", "NaCl": "塩化ナトリウム",
    "NaOH": "水酸化ナトリウム", "CaCO3": "炭酸カルシウム", "SiO2": "二酸化ケイ素(シリカ)",
    "Si": "シリコン(半導体の基本材料)", "Ge": "ゲルマニウム", "GaAs": "ガリウムヒ素(化合物半導体)",
    "GaN": "窒化ガリウム(青色LED)", "SiC": "炭化ケイ素(パワー半導体)", "InP": "リン化インジウム",
    "ZnO": "酸化亜鉛", "TiO2": "酸化チタン", "Al2O3": "アルミナ", "Fe2O3": "酸化鉄(III)",
    "Nb3Sn": "ニオブスズ(超伝導線材)", "NbTi": "ニオブチタン(超伝導線材)", "MgB2": "二ホウ化マグネシウム(超伝導体)",
    "YBa2Cu3O7": "YBCO(高温超伝導体)", "LaFeAsO": "鉄系超伝導体の母物質", "Hg": "水銀(初めて超伝導が観測された金属)"
  };

  /* 単一元素からなる実在の分子(単元素 + 数字は変数名と紛れるため、この範囲だけ許可する) */
  var SIMPLE_MOLECULES = {};
  "H2,O2,N2,F2,Cl2,Br2,I2,O3,P4,S8".split(",").forEach(function (m) { SIMPLE_MOLECULES[m] = 1; });

  /* 化学式らしいトークンを取り出す: 元素記号 + 任意の数字 の連なり */
  function parseFormula(tok) {
    var i = 0, n = tok.length, parts = 0, hasDigit = false, hasTwoLetter = false, seen = {};
    while (i < n) {
      var c = tok.charAt(i);
      if (c < "A" || c > "Z") return null;                 /* 元素は大文字始まり */
      var sym = c;
      if (i + 1 < n) {
        var c2 = tok.charAt(i + 1);
        if (c2 >= "a" && c2 <= "z" && ELEM_SET[c + c2]) { sym = c + c2; hasTwoLetter = true; }
      }
      if (!ELEM_SET[sym]) return null;
      seen[sym] = 1;
      i += sym.length;
      var num = "";
      while (i < n && tok.charAt(i) >= "0" && tok.charAt(i) <= "9") { num += tok.charAt(i); i++; }
      if (num) hasDigit = true;
      parts++;
    }
    /* 単元素で数字なしのもの(C, In, No…)は英単語と紛れるので採用しない。
       単元素 + 数字(C2, B2 など)は変数名と紛れるため、実在の分子だけを許可する。 */
    if (parts < 2 && !hasDigit) return null;
    if (parts === 1) return SIMPLE_MOLECULES[tok] ? { formula: tok, parts: parts } : null;
    /* 大文字1字の元素だけが並ぶ数字なしのトークンは、頭字語(UFO, PIN, CW…)とまず区別できない。
       数字を含むか、2文字元素(Na, Ga, Si…)を含むか、既知化合物のときだけ化学式として採用する。 */
    if (!hasDigit && !hasTwoLetter && !KNOWN[tok]) return null;
    /* 同じ 1 文字元素の繰り返し(P2P など)は略語のことが多いので、
       2 文字元素も既知化合物でもない場合は、異なる元素が 2 種以上あることを求める。 */
    if (!hasTwoLetter && !KNOWN[tok] && Object.keys(seen).length < 2) return null;
    return { formula: tok, parts: parts };
  }

  /* 添字(₀-₉)を通常数字へ、上付きマイナスなどを正規化 */
  function normalize(text) {
    var SUB = { "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9" };
    return String(text).replace(/[₀-₉]/g, function (c) { return SUB[c] || c; });
  }

  /**
   * PDF 本文から化学式と専門用語を検出する。
   * @param {string} text            pdf_symbols.extract().text
   * @param {Array}  terms           chem_phys_bank.TERMS (省略可)
   * @param {Array}  symbols         chem_phys_bank.SYMBOLS (省略可)
   * @returns {{formulas:Array, terms:Array, symbols:Array, chars:number}}
   */
  function scan(text, terms, symbols) {
    var t = normalize(text || "");
    var out = { formulas: [], terms: [], symbols: [], chars: t.length };
    if (!t) return out;

    /* --- 化学式 --- */
    var counts = {};
    var re = /[A-Z][A-Za-z0-9]{0,15}/g, m;
    while ((m = re.exec(t))) {
      var p = parseFormula(m[0]);
      if (p) counts[p.formula] = (counts[p.formula] || 0) + 1;
    }
    out.formulas = Object.keys(counts).map(function (f) {
      return { formula: f, count: counts[f], name: KNOWN[f] || null };
    }).sort(function (a, b) {
      /* 既知の化合物を優先し、その中で出現回数順 */
      if (!!b.name !== !!a.name) return b.name ? 1 : -1;
      return b.count - a.count;
    });

    /* --- 専門用語(日本語名・英語名) --- */
    (terms || []).forEach(function (term) {
      var c = 0, idx = 0;
      while ((idx = t.indexOf(term.t, idx)) >= 0) { c++; idx += term.t.length; }
      var en = term.en, lower = t.toLowerCase(), le = en.toLowerCase(), j = 0;
      while (en && (j = lower.indexOf(le, j)) >= 0) { c++; j += le.length; }
      if (c > 0) out.terms.push({ term: term, count: c });
    });
    out.terms.sort(function (a, b) { return b.count - a.count; });

    /* --- 記号表記(E_g, T_c など。空白除去した本文で照合) --- */
    var compact = t.replace(/\s+/g, "");
    (symbols || []).forEach(function (sym) {
      var key = sym.ch.replace(/\s+/g, "");
      if (key.length < 2) return;                       /* 1 文字記号は誤検出が多いので除外 */
      var c = 0, i = 0;
      while ((i = compact.indexOf(key, i)) >= 0) { c++; i += key.length; }
      if (c > 0) out.symbols.push({ sym: sym, count: c });
    });
    out.symbols.sort(function (a, b) { return b.count - a.count; });

    return out;
  }

  var API = { scan: scan, parseFormula: parseFormula, ELEMENTS: ELEMENTS, KNOWN: KNOWN };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.ChemExtract = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
