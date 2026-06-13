/*
 * plugins/codegen.js — 付加したAIが自分自身のソースコードを出力するプラグイン
 *
 * バンドルされた未知事前エンジン(engine.meta.genome_hex + engine.cfg)を、
 * 合成可能な Verilog(FPGA) / C / Python / JS のソースコードへ実行時に表出する。
 * 「付加するAIをソースコードに表出させる」を任意ホスト内で実現する自己完結プラグイン。
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";
  var CELL_BYTES = 6, LUT_INPUTS = 4;

  function hexToBytes(h) { h = (h || "").replace(/[^0-9a-fA-F]/g, ""); var n = h.length >> 1, b = new Uint8Array(n);
    for (var i = 0; i < n; i++) b[i] = parseInt(h.substr(i * 2, 2), 16); return b; }
  function cells(cfg, by) { var o = [], idx = 0;
    for (var L = 0; L < cfg.layers; L++) { var src = L === 0 ? cfg.inbits : cfg.width;
      for (var w = 0; w < cfg.width; w++) { var p = idx * CELL_BYTES, sel = [];
        for (var k = 0; k < LUT_INPUTS; k++) sel.push(by[p + k] % Math.max(1, src));
        o.push({ L: L, w: w, sel: sel, lut: (by[p + 4] | (by[p + 5] << 8)) & 0xFFFF }); idx++; } } return o; }
  function h16(v) { return (v & 0xFFFF).toString(16).toUpperCase().padStart(4, "0"); }

  function verilog(cfg, by, name) { var C = cells(cfg, by), s = [], prev = "din";
    s.push("module " + name + " (input [" + (cfg.inbits - 1) + ":0] din, output [" + (cfg.outbits - 1) + ":0] dout);");
    for (var L = 0; L < cfg.layers; L++) { var wn = "s" + L; s.push("  wire [" + (cfg.width - 1) + ":0] " + wn + ";");
      for (var w = 0; w < cfg.width; w++) { var c = C[L * cfg.width + w], lp = "LUT_" + L + "_" + w;
        s.push("  localparam [15:0] " + lp + " = 16'h" + h16(c.lut) + ";");
        var sl = c.sel.map(function (x) { return prev + "[" + x + "]"; });
        s.push("  assign " + wn + "[" + w + "] = " + lp + "[{" + sl[3] + "," + sl[2] + "," + sl[1] + "," + sl[0] + "}];"); }
      prev = wn; }
    s.push("  assign dout = " + prev + "[" + (cfg.outbits - 1) + ":0];"); s.push("endmodule"); return s.join("\n"); }

  function clike(cfg, by, lang) {
    var C = cells(cfg, by), s = [], inM = (1 << cfg.inbits) - 1, outM = (1 << cfg.outbits) - 1;
    var px = lang === "py" ? "    " : "  ";
    if (lang === "c") { s.push("#include <stdint.h>"); s.push("uint32_t omega_infer(uint32_t din){"); s.push("  uint32_t prev=din&0x" + inM.toString(16) + "u,cur=0;int addr;"); }
    else if (lang === "py") { s.push("def omega_infer(din):"); s.push("    prev = din & " + inM); }
    else { s.push("function omegaInfer(din){"); s.push("  var prev=din&" + inM + ",cur=0,addr;"); }
    for (var L = 0; L < cfg.layers; L++) {
      s.push(lang === "py" ? "    cur = 0" : px + "cur = 0;");
      for (var w = 0; w < cfg.width; w++) { var c = C[L * cfg.width + w];
        var a = "((prev>>" + c.sel[0] + ")&1)|(((prev>>" + c.sel[1] + ")&1)<<1)|(((prev>>" + c.sel[2] + ")&1)<<2)|(((prev>>" + c.sel[3] + ")&1)<<3)";
        if (lang === "py") { s.push("    addr = " + a); s.push("    cur |= ((0x" + h16(c.lut) + ">>addr)&1)<<" + w); }
        else { s.push(px + "addr=" + a + ";"); s.push(px + "cur|=((0x" + h16(c.lut) + ">>addr)&1)<<" + w + ";"); } }
      s.push(lang === "py" ? "    prev = cur" : px + "prev = cur;");
    }
    if (lang === "py") s.push("    return cur & " + outM);
    else { s.push(px + "return cur & " + outM + ";"); s.push("}"); }
    return s.join("\n");
  }

  var plugin = {
    name: "codegen",
    description: "付加したAIを Verilog(FPGA)/C/Python/JS のソースに表出",
    // run(engine, target, name) target: verilog|c|python|js
    run: function (engine, target, name) {
      target = (target || "verilog").toLowerCase();
      name = name || "omega_apriori";
      var by = hexToBytes(engine.meta.genome_hex), cfg = engine.cfg;
      if (target === "verilog" || target === "v") return verilog(cfg, by, name);
      if (target === "c") return clike(cfg, by, "c");
      if (target === "python" || target === "py") return clike(cfg, by, "py");
      if (target === "js" || target === "javascript") return clike(cfg, by, "js");
      throw new Error("unknown target: " + target);
    }
  };
  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).codegen = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
