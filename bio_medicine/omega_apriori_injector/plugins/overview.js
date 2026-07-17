/*
 * plugins/overview.js — 俯瞰(birds-eye / overview) プラグイン
 *
 * 2次元グリッド(数値行列)を粗視化したヒートマップ・集約統計・ホットスポット・
 * 要約テキストに変換する。各粗セルは未知事前エンジンで分類する。
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";

  var plugin = {
    name: "overview",
    description: "データ/盤面を俯瞰し、ヒートマップ・要点・ホットスポットを抽出",
    // run(engine, grid, opt) : grid = 2次元配列(数値), opt.cols/rows = 粗視化解像度
    run: function (engine, grid, opt) {
      opt = opt || {};
      var R = grid.length, C = grid[0].length;
      var br = Math.max(1, opt.rows || 4), bc = Math.max(1, opt.cols || 4);
      var heat = [], hotspots = [], gmin = Infinity, gmax = -Infinity, gsum = 0, gcnt = 0;
      var im = (1 << engine.cfg.inbits) - 1, om = (1 << engine.cfg.outbits) - 1;

      for (var i = 0; i < br; i++) {
        var row = [];
        for (var j = 0; j < bc; j++) {
          var r0 = Math.floor(i * R / br), r1 = Math.floor((i + 1) * R / br);
          var c0 = Math.floor(j * C / bc), c1 = Math.floor((j + 1) * C / bc);
          var sum = 0, n = 0, mx = -Infinity;
          for (var r = r0; r < r1; r++) for (var c = c0; c < c1; c++) {
            var v = grid[r][c] || 0; sum += v; n++; if (v > mx) mx = v;
          }
          var mean = n ? sum / n : 0;
          // 粗セルの平均を inbits ビットに量子化してエンジン分類
          var q = Math.max(0, Math.min(im, Math.round(mean) & im));
          var cls = engine.infer(q) & om;
          row.push({ mean: Math.round(mean * 1000) / 1000, max: mx, cls: cls });
          gsum += sum; gcnt += n;
          if (mean < gmin) gmin = mean;
          if (mean > gmax) gmax = mean;
          hotspots.push({ i: i, j: j, mean: mean, cls: cls });
        }
        heat.push(row);
      }
      hotspots.sort(function (a, b) { return b.mean - a.mean; });
      var top = hotspots.slice(0, Math.min(3, hotspots.length));
      var gmean = gcnt ? gsum / gcnt : 0;
      var summary = "俯瞰 " + br + "x" + bc + " | 全体平均=" + (Math.round(gmean * 1000) / 1000) +
        " 範囲=[" + (Math.round(gmin * 100) / 100) + "," + (Math.round(gmax * 100) / 100) + "]" +
        " | ホットスポット: " + top.map(function (h) { return "(" + h.i + "," + h.j + ")"; }).join(" ");
      return { resolution: [br, bc], heatmap: heat, hotspots: top, mean: gmean, min: gmin, max: gmax, summary: summary };
    }
  };

  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).overview = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
