/*
 * codegen.js — Ω-Apriori コード生成器: 進化ファブリックを各言語ソースに表出
 *
 * 未知事前エンジン(進化LUTファブリック)を、合成可能な Verilog(FPGA) / C / Python / JS の
 * ソースコードへ変換する。eval 仕様は apriori_cpu.c / apriori_runtime.js と一致。
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";
  var CELL_BYTES = 6, LUT_INPUTS = 4;

  function hexToBytes(h) {
    h = (h || "").replace(/[^0-9a-fA-F]/g, "");
    var n = h.length >> 1, b = new Uint8Array(n);
    for (var i = 0; i < n; i++) b[i] = parseInt(h.substr(i * 2, 2), 16);
    return b;
  }
  // 各セルの実ソース添字と LUT を解決
  function cells(cfg, bytes) {
    var out = [], idx = 0;
    for (var L = 0; L < cfg.layers; L++) {
      var src = (L === 0) ? cfg.inbits : cfg.width;
      for (var w = 0; w < cfg.width; w++) {
        var p = idx * CELL_BYTES, sel = [];
        for (var k = 0; k < LUT_INPUTS; k++) sel.push(bytes[p + k] % Math.max(1, src));
        out.push({ layer: L, w: w, idx: idx, sel: sel, lut: (bytes[p + 4] | (bytes[p + 5] << 8)) & 0xFFFF });
        idx++;
      }
    }
    return out;
  }
  function hex16(v) { return (v & 0xFFFF).toString(16).toUpperCase().padStart(4, "0"); }

  // ---- Verilog (合成可能 FPGA モジュール) ----
  function toVerilog(cfg, bytes, name) {
    name = name || "omega_apriori";
    var C = cells(cfg, bytes), s = [];
    s.push("// " + name + " — Ω-Apriori unknown-a-priori engine as a synthesizable LUT fabric");
    s.push("// conceptual/educational only. inbits=" + cfg.inbits + " layers=" + cfg.layers +
           " width=" + cfg.width + " outbits=" + cfg.outbits);
    s.push("module " + name + " (input  [" + (cfg.inbits - 1) + ":0] din, output [" + (cfg.outbits - 1) + ":0] dout);");
    var prev = "din";
    for (var L = 0; L < cfg.layers; L++) {
      var wname = "s" + L;
      s.push("  wire [" + (cfg.width - 1) + ":0] " + wname + ";");
      for (var w = 0; w < cfg.width; w++) {
        var c = C[L * cfg.width + w];
        var lp = "LUT_" + L + "_" + w;
        s.push("  localparam [15:0] " + lp + " = 16'h" + hex16(c.lut) + ";");
        var sel = c.sel.map(function (si) { return prev + "[" + si + "]"; });
        // addr = {b3,b2,b1,b0}  (b0 = LSB = sel[0])
        s.push("  assign " + wname + "[" + w + "] = " + lp + "[{" + sel[3] + "," + sel[2] + "," + sel[1] + "," + sel[0] + "}];");
      }
      prev = wname;
    }
    s.push("  assign dout = " + prev + "[" + (cfg.outbits - 1) + ":0];");
    s.push("endmodule");
    return s.join("\n");
  }

  // ---- C ----
  function toC(cfg, bytes, fn) {
    fn = fn || "omega_infer";
    var C = cells(cfg, bytes), s = [];
    s.push("/* " + fn + " — Ω-Apriori engine (generated). conceptual/educational only. */");
    s.push("#include <stdint.h>");
    s.push("uint32_t " + fn + "(uint32_t din){");
    s.push("    uint32_t prev = din & 0x" + ((1 << cfg.inbits) - 1).toString(16) + "u, cur = 0; int b0,b1,b2,b3,addr;");
    var prev = "prev";
    for (var L = 0; L < cfg.layers; L++) {
      s.push("    cur = 0;");
      for (var w = 0; w < cfg.width; w++) {
        var c = C[L * cfg.width + w];
        s.push("    b0=(prev>>" + c.sel[0] + ")&1; b1=(prev>>" + c.sel[1] + ")&1; b2=(prev>>" + c.sel[2] +
               ")&1; b3=(prev>>" + c.sel[3] + ")&1; addr=b0|b1<<1|b2<<2|b3<<3;");
        s.push("    cur |= ((0x" + hex16(c.lut) + ">>addr)&1)<<" + w + ";");
      }
      s.push("    prev = cur;");
    }
    s.push("    return cur & 0x" + ((1 << cfg.outbits) - 1).toString(16) + "u;");
    s.push("}");
    return s.join("\n");
  }

  // ---- Python ----
  function toPython(cfg, bytes, fn) {
    fn = fn || "omega_infer";
    var C = cells(cfg, bytes), s = [];
    s.push("# " + fn + " — Ω-Apriori engine (generated). conceptual/educational only.");
    s.push("def " + fn + "(din):");
    s.push("    prev = din & " + ((1 << cfg.inbits) - 1));
    for (var L = 0; L < cfg.layers; L++) {
      s.push("    cur = 0");
      for (var w = 0; w < cfg.width; w++) {
        var c = C[L * cfg.width + w];
        s.push("    addr = ((prev>>" + c.sel[0] + ")&1)|(((prev>>" + c.sel[1] + ")&1)<<1)|(((prev>>" +
               c.sel[2] + ")&1)<<2)|(((prev>>" + c.sel[3] + ")&1)<<3)");
        s.push("    cur |= ((0x" + hex16(c.lut) + ">>addr)&1)<<" + w);
      }
      s.push("    prev = cur");
    }
    s.push("    return cur & " + ((1 << cfg.outbits) - 1));
    return s.join("\n");
  }

  // ---- JavaScript ----
  function toJS(cfg, bytes, fn) {
    fn = fn || "omegaInfer";
    var C = cells(cfg, bytes), s = [];
    s.push("// " + fn + " — Ω-Apriori engine (generated). conceptual/educational only.");
    s.push("function " + fn + "(din){");
    s.push("  var prev = din & " + ((1 << cfg.inbits) - 1) + ", cur = 0, addr;");
    for (var L = 0; L < cfg.layers; L++) {
      s.push("  cur = 0;");
      for (var w = 0; w < cfg.width; w++) {
        var c = C[L * cfg.width + w];
        s.push("  addr=((prev>>" + c.sel[0] + ")&1)|(((prev>>" + c.sel[1] + ")&1)<<1)|(((prev>>" +
               c.sel[2] + ")&1)<<2)|(((prev>>" + c.sel[3] + ")&1)<<3);");
        s.push("  cur|=((0x" + hex16(c.lut) + ">>addr)&1)<<" + w + ";");
      }
      s.push("  prev = cur;");
    }
    s.push("  return cur & " + ((1 << cfg.outbits) - 1) + ";");
    s.push("}");
    return s.join("\n");
  }

  var API = { hexToBytes: hexToBytes, cells: cells, toVerilog: toVerilog, toC: toC, toPython: toPython, toJS: toJS };
  global.OmegaCodegen = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
