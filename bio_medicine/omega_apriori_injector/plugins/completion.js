/*
 * plugins/completion.js — 補完(completion / autocomplete) プラグイン
 *
 * 系列(数値配列 or 文字列)を未知事前エンジンに通し、次要素を予測補完する。
 * スライディング窓のコンテキストを inbits ビットへ符号化して推論する。
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";

  function toCodes(seq) {
    if (typeof seq === "string") {
      var a = []; for (var i = 0; i < seq.length; i++) a.push(seq.charCodeAt(i)); return { codes: a, isStr: true };
    }
    return { codes: seq.slice(), isStr: false };
  }

  var plugin = {
    name: "completion",
    description: "系列の次要素を未知事前エンジンで予測補完",
    // run(engine, seq, k) : seq=配列or文字列, k=補完する個数
    run: function (engine, seq, k) {
      k = k || 4;
      var t = toCodes(seq), codes = t.codes;
      var im = (1 << engine.cfg.inbits) - 1, om = (1 << engine.cfg.outbits) - 1;
      var out = [];
      for (var step = 0; step < k; step++) {
        // 直近2要素を窓としてビット連結（inbits に収める）
        var n = codes.length;
        var ctx = ((codes[n - 1] || 0) ^ ((codes[n - 2] || 0) << 1)) & im;
        var pred = engine.infer(ctx) & om;
        // 予測クラスを文脈にマップして次要素を生成（決定論）
        var next = ((codes[n - 1] || 0) + pred + 1) & (t.isStr ? 0x7f : im);
        if (t.isStr && next < 32) next = 32 + (next % 95); // 表示可能文字へ
        codes.push(next);
        out.push(t.isStr ? String.fromCharCode(next) : next);
      }
      return {
        input: seq,
        predicted: t.isStr ? out.join("") : out,
        full: t.isStr ? codes.map(function (c) { return String.fromCharCode(c); }).join("") : codes
      };
    }
  };

  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).completion = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
