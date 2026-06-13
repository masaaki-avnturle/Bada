/*
 * plugins/patternmatch.js — 中枢知能FPGAのパターンマッチ & マッチャ・ソース生成プラグイン
 *
 * 付加した未知事前エンジン(進化LUTファブリック)を「パターンマッチ器」として使う:
 *   run(engine)                         → 既定: classify (単一/配列入力を分類)
 *   run(engine,"classify",x|[x..])      → 学習済みパターンの分類ラベル
 *   run(engine,"report",[[x,label],..]) → 例示に対する一致率/被覆レポート
 *   run(engine,"source","c"|"py"|"js"|"verilog") → パターンマッチ用ソースコード生成
 *
 * "source" は同梱の codegen プラグインを土台に pattern_match() ラッパを付与する。
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";

  function wrap(lang, core) {
    if (lang === "c") return core + "\n\n/* pattern matcher */\nint pattern_match(uint32_t x){ return (int)omega_infer(x); }\nint is_match(uint32_t x,int label){ return (int)omega_infer(x)==label; }\n";
    if (lang === "py" || lang === "python") return core + "\n\n# pattern matcher\ndef pattern_match(x):\n    return omega_infer(x)\n\ndef is_match(x, label):\n    return omega_infer(x) == label\n";
    if (lang === "js" || lang === "javascript") return core + "\n\n// pattern matcher\nfunction pattern_match(x){ return omegaInfer(x); }\nfunction is_match(x,label){ return omegaInfer(x)===label; }\n";
    // verilog: module IS the matcher
    return core + "\n// pattern matcher: instantiate omega_apriori; dout = matched class for din.\n";
  }

  var plugin = {
    name: "patternmatch",
    description: "中枢知能FPGAをパターンマッチ器として使い、マッチャ・ソースを生成",
    run: function (engine, mode, arg, lang) {
      mode = mode || "classify";
      if (mode === "report") {
        var ex = arg || [], ok = 0, conf = {};
        for (var i = 0; i < ex.length; i++) {
          var x = ex[i][0], lab = ex[i][1], y = engine.infer(x);
          if (y === lab) ok++;
          var key = lab + "->" + y; conf[key] = (conf[key] || 0) + 1;
        }
        return { n: ex.length, hit: ok, accuracy: ex.length ? ok / ex.length : 0, confusion: conf };
      }
      if (mode === "source") {
        var lg = (arg || "js").toLowerCase();
        if (!engine.plugins || !engine.plugins.codegen)
          throw new Error("patternmatch 'source' requires the codegen plugin in the bundle");
        var core = engine.call("codegen", lg);
        return wrap(lg, core);
      }
      // classify
      if (Array.isArray(arg)) return arg.map(function (x) { return engine.infer(x); });
      return engine.infer(arg);
    }
  };
  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).patternmatch = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
