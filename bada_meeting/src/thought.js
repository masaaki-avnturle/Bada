/*
 * thought.js — 入力の 3 つの方法: キーボード / 電鍵 (モールス符号) / ポインタの滞留、と語句の予測
 *
 * 電鍵は Bada Telegraph (bada_telegraph) のモールス符号を使う。キー 1 つの「短く押す / 長く押す」
 * だけで文字を打てる。和文モールスにも対応 (濁点・半濁点は直前のかなに付く)。
 *   短点 = 押した時間が 2 単位未満 / 長点 = 2 単位以上
 *   文字の区切り = 2.5 単位の無操作 / 語の区切り (欧文のみ) = 6 単位の無操作
 * ポインタの滞留: 候補やかなの上にポインタを留めると確定する (Ω-Telepathy と同じ方式)。
 *   滞留時間 T(c) = 基準時間 × clamp(−log p(c) / log(候補数), 0.35, 1.6)   … 確からしい候補ほど短い
 * 予測した候補は Alt + 数字でも入れられる。候補の確率には、レポートの核 1/(x log x)² を
 * 順位の事前分布として使う (E3)。
 */
(function (global) {
  "use strict";
  var En = global.BadaEntropy || (typeof require !== "undefined" ? require("./entropy.js") : null);
  var PHRASES = ["賛成です", "反対です", "もう少し詳しくお願いします", "期限を見直しましょう", "範囲を絞りましょう", "見積りをお願いします", "日程をお願いします",
    "リスクを確認しましょう", "次の議題に進みましょう", "決定とします", "確認します", "了解しました", "ありがとうございます"];

  // 欧文 (Bada Telegraph の MORSE 表と同じ)
  var LATIN = { A: ".-", B: "-...", C: "-.-.", D: "-..", E: ".", F: "..-.", G: "--.", H: "....", I: "..", J: ".---", K: "-.-", L: ".-..", M: "--", N: "-.", O: "---", P: ".--.",
    Q: "--.-", R: ".-.", S: "...", T: "-", U: "..-", V: "...-", W: ".--", X: "-..-", Y: "-.--", Z: "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--", "/": "-..-.", "@": ".--.-." };
  // 和文
  var KANA = { "い": ".-", "ろ": ".-.-", "は": "-...", "に": "-.-.", "ほ": "-..", "へ": ".", "と": "..-..", "ち": "..-.", "り": "--.", "ぬ": "....", "る": "-.--.", "を": ".---",
    "わ": "-.-", "か": ".-..", "よ": "--", "た": "-.", "れ": "---", "そ": "---.", "つ": ".--.", "ね": "--.-", "な": ".-.", "ら": "...", "む": "-", "う": "..-", "ゐ": ".-..-",
    "の": "..--", "お": ".-...", "く": "...-", "や": ".--", "ま": "-..-", "け": "-.--", "ふ": "--..", "こ": "----", "え": "-.---", "て": ".-.--", "あ": "--.--", "さ": "-.-.-",
    "き": "-.-..", "ゆ": "-..--", "め": "-...-", "み": "..-.-", "し": "--.-.", "ゑ": ".--..", "ひ": "--..-", "も": "-..-.", "せ": ".---.", "す": "---.-", "ん": ".-.-.",
    "゛": "..", "゜": "..--.", "ー": ".--.-", "、": ".-.-.-", "。": ".-.-..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----." };
  var invert = function (t) { var o = {}; Object.keys(t).forEach(function (k) { o[t[k]] = k; }); return o; };
  var DECODE = { latin: invert(LATIN), kana: invert(KANA) };

  function decodeSymbol(code, mode) { return DECODE[mode === "latin" ? "latin" : "kana"][code] || null; }
  // 文字を文章の末尾に付ける。濁点・半濁点は直前のかなと合成する (か + ゛ → が)
  function append(text, ch) {
    if (ch === "゛" || ch === "゜") {
      if (!text) return text;
      var c = (text.slice(-1) + (ch === "゛" ? "゙" : "゚")).normalize("NFC");
      return c.length === 1 ? text.slice(0, -1) + c : text;      // 濁点の付かない字はそのまま
    }
    return text + ch;
  }
  function toMorse(text, mode) {
    var table = mode === "latin" ? LATIN : KANA;
    return Array.from(String(text).normalize("NFD").toUpperCase()).map(function (ch) {
      if (ch === "゙") return KANA["゛"]; if (ch === "゚") return KANA["゜"];
      if (ch === " " || ch === "\n") return "/";
      var small = "ぁぃぅぇぉっゃゅょゎ".indexOf(ch); if (small >= 0) ch = "あいうえおつやゆよわ"[small];      // 和文モールスに小書きの字は無い
      return table[ch] || "?";
    }).join(" ");
  }

  // 電鍵: down(t) / up(t) / tick(t) を時刻 (ミリ秒) つきで呼ぶ。確定した文字を配列で返す
  function Keyer(unitMs, mode) { this.unit = unitMs || 120; this.mode = mode || "kana"; this.symbol = ""; this.downAt = null; this.lastUp = null; this.spaced = true; }
  Keyer.prototype.setMode = function (mode) { this.mode = mode; this.symbol = ""; this.downAt = null; this.lastUp = null; this.spaced = true; };
  // もう確定待ちの文字も語の区切りも無い (タイマーを止めてよい)
  Keyer.prototype.idle = function (t) {
    if (this.downAt !== null || this.symbol) return false;
    return this.lastUp === null || this.spaced || this.mode !== "latin" || (t - this.lastUp) > 7 * this.unit;
  };
  Keyer.prototype.down = function (t) { var out = this.tick(t); if (this.downAt === null) this.downAt = t; return out; };
  Keyer.prototype.up = function (t) {
    if (this.downAt === null) return [];
    this.symbol += (t - this.downAt) < 2 * this.unit ? "." : "-";
    this.downAt = null; this.lastUp = t; this.spaced = false; return [];
  };
  Keyer.prototype.tick = function (t) {
    var out = [];
    if (this.downAt !== null || this.lastUp === null) return out;
    var gap = t - this.lastUp;
    if (this.symbol && gap >= 2.5 * this.unit) {
      var ch = decodeSymbol(this.symbol, this.mode);
      out.push(ch === null ? { unknown: this.symbol } : { char: this.mode === "latin" ? ch.toLowerCase() : ch });
      this.symbol = "";
    }
    if (!this.symbol && !this.spaced && this.mode === "latin" && gap >= 6 * this.unit) { out.push({ char: " " }); this.spaced = true; }
    return out;
  };

  // 語彙: 定型句 + 議事録に出てきた語句 (出現回数つき)
  function lexicon(msgs) {
    var count = Object.create(null);
    PHRASES.forEach(function (p) { count[p] = 1; });
    (msgs || []).forEach(function (m) {
      String(m.text).split(/[、。・\s()「」→:：,]+/).forEach(function (w) {
        w = w.trim(); if (w.length >= 2 && w.length <= 18 && !/^[0-9.]+$/.test(w)) count[w] = (count[w] || 0) + 1;
      });
    });
    return count;
  }
  // 入力中の行の末尾 (最後の区切り以降) に続く候補を、確率の高い順に返す
  function predict(prefix, count, k) {
    var tail = String(prefix).split(/[、。\s]/).pop();
    // 入力が空のときは定型句だけを出す (議事録の語句は、頭の文字が入ってから)
    var cands = tail ? Object.keys(count).filter(function (w) { return w.indexOf(tail) === 0 && w !== tail; }) : PHRASES.slice();
    cands.sort(function (a, b) { return count[b] - count[a] || a.length - b.length || (a < b ? -1 : 1); });
    cands = cands.slice(0, k || 8);
    var z = 0, w = cands.map(function (c, i) { var v = (count[c] + 1) * En.kernel(i + 1); z += v; return v; });
    return cands.map(function (c, i) { var p = w[i] / z; return { text: c, insert: tail ? c.slice(tail.length) : c, p: p, surprisal: -Math.log(p) }; });
  }

  // ポインタ用のかな盤 (列ごと)。"↵" は改行
  var GRID = ["あいうえお", "かきくけこ", "さしすせそ", "たちつてと", "なにぬねの", "はひふへほ", "まみむめも", "や ゆ よ", "らりるれろ", "わをんー゛", "、。？゜↵"];
  // 候補の滞留時間 (ミリ秒)。候補が 1 つならもっとも短い
  function dwellMs(cand, n, baseMs) {
    var ratio = n > 1 ? cand.surprisal / Math.log(n) : 0;
    return Math.round(baseMs * Math.max(0.35, Math.min(1.6, ratio)));
  }

  global.BadaThought = { GRID: GRID, dwellMs: dwellMs, PHRASES: PHRASES, LATIN: LATIN, KANA: KANA, decodeSymbol: decodeSymbol, append: append, toMorse: toMorse, Keyer: Keyer, lexicon: lexicon, predict: predict };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaThought;
})(typeof window !== "undefined" ? window : globalThis);
