/*
 * thought.js — 思念入力 (Ω-Telepathy と同じ方式: 滞留で選び、予測で加速する)
 *
 * 実際に思考を読み取るものではありません。入力は「候補の上にポインタを留める (滞留)」
 * という通常の操作で、次に入れそうな語句を予測して並べ、確からしい候補ほど
 * 短い滞留で確定できるようにします。
 *   候補の確率  p(c) ∝ (文脈での出現回数 + 1) × 1/((r+1) log(r+1))²      … (E3) 順位の事前分布
 *   滞留時間    T(c) = 基準時間 × clamp(−log p(c) / log(候補数), 0.35, 1.6)   … 驚きが小さいほど短い
 */
(function (global) {
  "use strict";
  var En = global.BadaEntropy || (typeof require !== "undefined" ? require("./entropy.js") : null);
  var PHRASES = ["賛成です", "反対です", "もう少し詳しくお願いします", "期限を見直しましょう", "範囲を絞りましょう", "見積りをお願いします", "日程をお願いします",
    "リスクを確認しましょう", "次の議題に進みましょう", "決定とします", "確認します", "了解しました", "ありがとうございます"];
  var KANA = ["あいうえお", "かきくけこ", "さしすせそ", "たちつてと", "なにぬねの", "はひふへほ", "まみむめも", "や ゆ よ", "らりるれろ", "わをんー、", "。？！ 　"];

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
  // 入力中の文字列 prefix (最後の区切り以降) に続く候補を、確率の高い順に返す
  function predict(prefix, count, k) {
    var tail = String(prefix).split(/[、。\s]/).pop();
    // 入力が空のときは定型句だけを出す (議事録の語句は、頭の文字が入ってから)
    var cands = tail ? Object.keys(count).filter(function (w) { return w.indexOf(tail) === 0 && w !== tail; }) : PHRASES.slice();
    cands.sort(function (a, b) { return count[b] - count[a] || a.length - b.length || (a < b ? -1 : 1); });
    cands = cands.slice(0, k || 8);
    var z = 0, w = cands.map(function (c, i) { var v = (count[c] + 1) * En.kernel(i + 1); z += v; return v; });
    return cands.map(function (c, i) {
      var p = w[i] / z;
      return { text: c, insert: tail ? c.slice(tail.length) : c, p: p, surprisal: -Math.log(p) };
    });
  }
  // 候補の滞留時間 (ミリ秒)。候補が 1 つならもっとも短い
  function dwellMs(cand, n, baseMs) {
    var ratio = n > 1 ? cand.surprisal / Math.log(n) : 0;
    return Math.round(baseMs * Math.max(0.35, Math.min(1.6, ratio)));
  }
  // 滞留の進み具合: ポインタが載ってから elapsed ミリ秒 → 0〜1。1 で確定
  function progress(elapsed, ms) { return Math.max(0, Math.min(1, elapsed / ms)); }

  global.BadaThought = { PHRASES: PHRASES, KANA: KANA, lexicon: lexicon, predict: predict, dwellMs: dwellMs, progress: progress };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaThought;
})(typeof window !== "undefined" ? window : globalThis);
