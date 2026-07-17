/*
 * plugins/word_complete.js — 単語補完(word autocomplete)プラグイン
 *
 * 接頭辞(prefix)と語彙(vocab)から候補を前方一致で抽出し、
 *   接頭辞被覆率 + 頻度 + 付加した未知事前エンジン(FPGA)の推論バイアス
 * でランク付けして返す。任意アプリのテキスト入力へ単語補完を付加できる。
 *
 *   run(engine, prefix, {vocab:[...], context:"直前の語", k:8, freq:{w:count}})
 *     → [{word, score}, ...]
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";
  var DEFAULT_VOCAB = [
    "function","return","const","let","var","class","import","export","async","await",
    "value","vector","matrix","manifold","gamma","integral","telomere","evolution","engine",
    "apriori","pattern","complete","completion","overview","quantum","fabric","genome","verilog",
    "the","this","that","with","application","attach","plugin","signature","source","module",
    "compute","calculate","generate","analyze","analysis","network","neural","learning","model"
  ];
  function hashStr(s) { var h = 2166136261 >>> 0; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }

  var plugin = {
    name: "word_complete",
    description: "接頭辞＋語彙＋FPGA推論で単語補完候補をランク付け",
    run: function (engine, prefix, opts) {
      opts = opts || {};
      prefix = String(prefix || "");
      var p = prefix.toLowerCase();
      var vocab = opts.vocab && opts.vocab.length ? opts.vocab : DEFAULT_VOCAB;
      var k = opts.k || 8, freq = opts.freq || {}, ctx = (opts.context || "").toLowerCase();
      var im = (1 << engine.cfg.inbits) - 1, om = (1 << engine.cfg.outbits) - 1;
      // 重複排除しつつ前方一致
      var seen = {}, cands = [];
      for (var i = 0; i < vocab.length; i++) {
        var w = vocab[i]; if (typeof w !== "string") continue;
        var wl = w.toLowerCase();
        if (p && wl.indexOf(p) !== 0) continue;       // 前方一致
        if (wl === p) continue;                        // 既に一致
        if (seen[wl]) continue; seen[wl] = 1;
        // スコア: 被覆率 + 頻度 + エンジンバイアス
        var cover = p.length ? p.length / wl.length : 0.1;
        var fr = (freq[w] || freq[wl] || 0);
        var code = (hashStr(ctx + ">" + wl)) & im;
        var bias = (engine.infer(code) & om) / (om || 1);   // 0..1
        var score = cover * 2 + Math.log(1 + fr) + bias * 0.8;
        cands.push({ word: w, score: Math.round(score * 1e3) / 1e3 });
      }
      cands.sort(function (a, b) { return b.score - a.score; });
      return cands.slice(0, k);
    }
  };
  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).word_complete = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
