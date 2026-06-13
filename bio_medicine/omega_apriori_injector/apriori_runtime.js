/*
 * apriori_runtime.js — Ω-Apriori 携帯ランタイム + プラグインホスト
 *
 * omega_apriori_cpu で進化させた未知事前エンジン(ゲノム)を、任意のアプリへ
 * 付加して実行するための最小ランタイム。ブラウザ / Node 両対応。
 * FPGA様LUTファブリックの eval 仕様は apriori_cpu.c / apriori_engine.py と一致。
 *
 * ⚠ 概念実証・教育用。付加は「自分が管理する／許諾されたアプリ」に対してのみ行うこと。
 */
(function (global) {
  "use strict";
  var LUT_INPUTS = 4, CELL_BYTES = 6;

  function hexToBytes(h) {
    h = (h || "").replace(/[^0-9a-fA-F]/g, "");
    var n = h.length >> 1, b = new Uint8Array(n);
    for (var i = 0; i < n; i++) b[i] = parseInt(h.substr(i * 2, 2), 16);
    return b;
  }

  // FPGA様 LUT ファブリック（前方伝播評価のみ）
  function Fabric(cfg) {
    this.cfg = cfg;
    var n = cfg.layers * cfg.width;
    this.lut = new Int32Array(n);
    this.insel = [];
    for (var i = 0; i < n; i++) this.insel.push([0, 0, 0, 0]);
  }
  Fabric.prototype.load = function (bytes) {
    var idx = 0, c = this.cfg;
    for (var L = 0; L < c.layers; L++) {
      var src = (L === 0) ? c.inbits : c.width;
      for (var w = 0; w < c.width; w++) {
        var p = idx * CELL_BYTES;
        for (var k = 0; k < LUT_INPUTS; k++) this.insel[idx][k] = bytes[p + k] % Math.max(1, src);
        this.lut[idx] = bytes[p + 4] | (bytes[p + 5] << 8);
        idx++;
      }
    }
  };
  Fabric.prototype.eval = function (x) {
    var c = this.cfg, prev = x & ((1 << c.inbits) - 1), src = c.inbits, cur = 0;
    for (var L = 0; L < c.layers; L++) {
      cur = 0;
      for (var w = 0; w < c.width; w++) {
        var cell = L * c.width + w, addr = 0;
        for (var k = 0; k < LUT_INPUTS; k++) {
          var sel = this.insel[cell][k];
          if (sel >= src) sel = src ? sel % src : 0;
          addr |= ((prev >> sel) & 1) << k;
        }
        cur |= ((this.lut[cell] >> addr) & 1) << w;
      }
      prev = cur; src = c.width;
    }
    return cur & ((1 << c.outbits) - 1);
  };

  // 未知事前エンジン + プラグインホスト
  function OmegaApriori(manifest) {
    if (!manifest || !manifest.cfg || !manifest.genome_hex)
      throw new Error("OmegaApriori: invalid manifest");
    this.meta = manifest;
    this.cfg = manifest.cfg;
    this.fab = new Fabric(this.cfg);
    this.fab.load(hexToBytes(manifest.genome_hex));
    this.plugins = {};
  }
  // 生のエンジン推論: 入力ワード -> 出力ワード
  OmegaApriori.prototype.infer = function (x) { return this.fab.eval(x); };
  // ベクトル入力を inbits 単位に畳んで推論列を返す（補完・俯瞰の素材）
  OmegaApriori.prototype.inferSeq = function (arr) {
    var out = [], m = (1 << this.cfg.inbits) - 1;
    for (var i = 0; i < arr.length; i++) out.push(this.infer(arr[i] & m));
    return out;
  };
  OmegaApriori.prototype.register = function (plugin) {
    if (!plugin || !plugin.name) throw new Error("plugin needs a name");
    this.plugins[plugin.name] = plugin;
    if (typeof plugin.attach === "function") plugin.attach(this);
    return this;
  };
  OmegaApriori.prototype.call = function (name) {
    var p = this.plugins[name];
    if (!p) throw new Error("no such plugin: " + name);
    var args = Array.prototype.slice.call(arguments, 1);
    return p.run.apply(p, [this].concat(args));
  };
  OmegaApriori.prototype.capabilities = function () { return Object.keys(this.plugins); };

  global.OmegaApriori = OmegaApriori;
  global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {};
  if (typeof module !== "undefined" && module.exports)
    module.exports = { OmegaApriori: OmegaApriori, Fabric: Fabric, hexToBytes: hexToBytes };
})(typeof window !== "undefined" ? window : globalThis);
