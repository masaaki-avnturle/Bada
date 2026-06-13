/*
 * plugins/fpga_functions.js — 自己進化FPGAから生成した「任意の名前付き関数」ライブラリ実行
 *
 * 付加先で、自己進化させた複数のFPGA(関数)を名前で呼び出す。ライブラリは
 * engine.meta.fn_library = { name: {cfg, genome_hex, fitness} } として運ばれる
 * (spec.json / manifest 経由)。任意の機能をFPGAから生成して任意アプリへ付加する核。
 *
 *   run(engine,"list")                 → 関数名一覧
 *   run(engine, name, x)               → その関数(FPGA)を入力 x で評価
 *   run(engine,"call", name, x)        → 同上(明示形)
 *   run(engine,"source", name, lang)   → その関数のソース(js/c/py/verilog)生成
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";
  var CB = 6;
  function h2b(h) { h = (h || "").replace(/[^0-9a-fA-F]/g, ""); var n = h.length >> 1, b = new Uint8Array(n); for (var i = 0; i < n; i++) b[i] = parseInt(h.substr(i * 2, 2), 16); return b; }
  function evalFab(cfg, g, x) {
    var prev = x & ((1 << cfg.inbits) - 1), src = cfg.inbits, cur = 0;
    for (var L = 0; L < cfg.layers; L++) { cur = 0;
      for (var w = 0; w < cfg.width; w++) { var cell = L * cfg.width + w, p = cell * CB, addr = 0;
        for (var k = 0; k < 4; k++) { var sel = g[p + k] % Math.max(1, (L === 0 ? cfg.inbits : cfg.width)); if (sel >= src) sel = src ? sel % src : 0; addr |= ((prev >> sel) & 1) << k; }
        cur |= (((g[p + 4] | (g[p + 5] << 8)) >> addr) & 1) << w; }
      prev = cur; src = cfg.width; }
    return cur & ((1 << cfg.outbits) - 1);
  }
  function h16(v) { return (v & 0xFFFF).toString(16).toUpperCase().padStart(4, "0"); }
  function emit(cfg, by, lang, fname) {
    fname = fname || "fpga_fn"; var inM = (1 << cfg.inbits) - 1, outM = (1 << cfg.outbits) - 1, idx = 0, s = [];
    if (lang === "verilog") { var prev = "din"; s.push("module " + fname + " (input [" + (cfg.inbits - 1) + ":0] din, output [" + (cfg.outbits - 1) + ":0] dout);");
      for (var L = 0; L < cfg.layers; L++) { var wn = "s" + L; s.push("  wire [" + (cfg.width - 1) + ":0] " + wn + ";"); var src = L === 0 ? cfg.inbits : cfg.width;
        for (var w = 0; w < cfg.width; w++) { var p = idx * CB, sel = []; for (var k = 0; k < 4; k++) sel.push(by[p + k] % Math.max(1, src));
          s.push("  localparam [15:0] L_" + L + "_" + w + " = 16'h" + h16(by[p + 4] | (by[p + 5] << 8)) + ";");
          s.push("  assign " + wn + "[" + w + "] = L_" + L + "_" + w + "[{" + prev + "[" + sel[3] + "]," + prev + "[" + sel[2] + "]," + prev + "[" + sel[1] + "]," + prev + "[" + sel[0] + "}];"); idx++; }
        prev = wn; }
      s.push("  assign dout = " + prev + "[" + (cfg.outbits - 1) + ":0];"); s.push("endmodule"); return s.join("\n"); }
    var px = lang === "py" ? "    " : "  ";
    if (lang === "c") { s.push("#include <stdint.h>"); s.push("int " + fname + "(uint32_t din){"); s.push("  uint32_t prev=din&0x" + inM.toString(16) + "u,cur=0;int addr;"); }
    else if (lang === "py") { s.push("def " + fname + "(din):"); s.push("    prev = din & " + inM); }
    else { s.push("function " + fname + "(din){"); s.push("  var prev=din&" + inM + ",cur=0,addr;"); }
    for (var L2 = 0; L2 < cfg.layers; L2++) { s.push(lang === "py" ? "    cur = 0" : px + "cur = 0;");
      for (var w2 = 0; w2 < cfg.width; w2++) { var p2 = idx * CB, sl = []; for (var k2 = 0; k2 < 4; k2++) sl.push(by[p2 + k2] % Math.max(1, (L2 === 0 ? cfg.inbits : cfg.width)));
        var a = "((prev>>" + sl[0] + ")&1)|(((prev>>" + sl[1] + ")&1)<<1)|(((prev>>" + sl[2] + ")&1)<<2)|(((prev>>" + sl[3] + ")&1)<<3)";
        if (lang === "py") { s.push("    addr = " + a); s.push("    cur |= ((0x" + h16(by[p2 + 4] | (by[p2 + 5] << 8)) + ">>addr)&1)<<" + w2); }
        else { s.push(px + "addr=" + a + ";"); s.push(px + "cur|=((0x" + h16(by[p2 + 4] | (by[p2 + 5] << 8)) + ">>addr)&1)<<" + w2 + ";"); } idx++; }
      s.push(lang === "py" ? "    prev = cur" : px + "prev = cur;"); }
    if (lang === "py") s.push("    return cur & " + outM);
    else if (lang === "c") { s.push("  return (int)(cur & 0x" + outM.toString(16) + "u);"); s.push("}"); }
    else { s.push("  return cur & " + outM + ";"); s.push("}"); }
    return s.join("\n");
  }

  var plugin = {
    name: "fpga_functions",
    description: "自己進化FPGAから生成した任意の名前付き関数ライブラリを実行/表出",
    run: function (engine, mode, a, b) {
      var lib = (engine.meta && engine.meta.fn_library) || {};
      if (mode === "list") return Object.keys(lib);
      if (mode === "source") { var f = lib[a]; if (!f) throw new Error("no fpga function: " + a);
        return emit(f.cfg, h2b(f.genome_hex), (b || "js").toLowerCase(), a); }
      if (mode === "call") { var fc = lib[a]; if (!fc) throw new Error("no fpga function: " + a); return evalFab(fc.cfg, h2b(fc.genome_hex), b | 0); }
      // mode == function name
      var fn = lib[mode]; if (fn) return evalFab(fn.cfg, h2b(fn.genome_hex), a | 0);
      throw new Error("fpga_functions: unknown mode/function '" + mode + "'");
    }
  };
  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).fpga_functions = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
