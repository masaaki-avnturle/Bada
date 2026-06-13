/*
 * plugins/go_lookahead.js — 囲碁(Go) 先読みプラグイン
 *
 * NxN 盤に対し alpha-beta 先読み(negamax)で最善手を返す。
 * 局所3x3パターンを未知事前エンジンに通したバイアスで評価を補正する。
 * board: 2次元配列 (0=空, 1=黒, 2=白)
 *
 * ⚠ 概念実証・教育用。完全なルール(コウ/取り/終局判定)の一部を簡略化。
 */
(function (global) {
  "use strict";

  function clone(b) { return b.map(function (r) { return r.slice(); }); }
  function inb(b, r, c) { return r >= 0 && c >= 0 && r < b.length && c < b[0].length; }
  var DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

  // 連(group)とその呼吸点(liberties)を取得
  function group(b, r, c) {
    var color = b[r][c], st = [[r, c]], seen = {}, stones = [], libs = {};
    seen[r + "," + c] = 1;
    while (st.length) {
      var p = st.pop(), pr = p[0], pc = p[1];
      stones.push(p);
      for (var d = 0; d < 4; d++) {
        var nr = pr + DIRS[d][0], nc = pc + DIRS[d][1];
        if (!inb(b, nr, nc)) continue;
        if (b[nr][nc] === 0) libs[nr + "," + nc] = 1;
        else if (b[nr][nc] === color && !seen[nr + "," + nc]) { seen[nr + "," + nc] = 1; st.push([nr, nc]); }
      }
    }
    return { stones: stones, liberties: Object.keys(libs).length };
  }

  // 着手を適用(相手の呼吸点0の連を取る)。非合法(自殺手)なら null。
  function play(b, r, c, color) {
    if (b[r][c] !== 0) return null;
    var nb = clone(b); nb[r][c] = color;
    var opp = color === 1 ? 2 : 1, captured = 0;
    for (var d = 0; d < 4; d++) {
      var nr = r + DIRS[d][0], nc = c + DIRS[d][1];
      if (inb(nb, nr, nc) && nb[nr][nc] === opp) {
        var g = group(nb, nr, nc);
        if (g.liberties === 0) { g.stones.forEach(function (s) { nb[s[0]][s[1]] = 0; }); captured += g.stones.length; }
      }
    }
    if (group(nb, r, c).liberties === 0 && captured === 0) return null; // 自殺手
    return { board: nb, captured: captured };
  }

  // 局所3x3 を inbits ビットに符号化 → エンジン推論バイアス
  function engineBias(engine, b, r, c, color) {
    var bits = 0, k = 0, n = engine.cfg.inbits;
    for (var dr = -1; dr <= 1 && k < n; dr++)
      for (var dc = -1; dc <= 1 && k < n; dc++) {
        var v = inb(b, r + dr, c + dc) ? (b[r + dr][c + dc] === color ? 1 : 0) : 0;
        bits |= v << k; k++;
      }
    return engine.infer(bits); // 0..(2^outbits-1)
  }

  // 静的評価(color視点): 石差 + 呼吸差 + 取った石
  function evaluate(engine, b, color, captured) {
    var opp = color === 1 ? 2 : 1, mine = 0, his = 0, myLib = 0, hisLib = 0, seen = {};
    for (var r = 0; r < b.length; r++)
      for (var c = 0; c < b[0].length; c++) {
        if (b[r][c] === 0 || seen[r + "," + c]) continue;
        var g = group(b, r, c);
        g.stones.forEach(function (s) { seen[s[0] + "," + s[1]] = 1; });
        if (b[r][c] === color) { mine += g.stones.length; myLib += g.liberties; }
        else { his += g.stones.length; hisLib += g.liberties; }
      }
    return (mine - his) + 0.5 * (myLib - hisLib) + 2 * captured;
  }

  function legalMoves(b) {
    var mv = [];
    for (var r = 0; r < b.length; r++) for (var c = 0; c < b[0].length; c++) if (b[r][c] === 0) mv.push([r, c]);
    return mv;
  }

  // negamax + alpha-beta
  function negamax(engine, b, color, depth, alpha, beta, captured) {
    if (depth === 0) return { score: evaluate(engine, b, color, captured) };
    var moves = legalMoves(b);
    if (!moves.length) return { score: evaluate(engine, b, color, captured) };
    var best = { score: -Infinity, move: null };
    for (var i = 0; i < moves.length; i++) {
      var r = moves[i][0], c = moves[i][1];
      var res = play(b, r, c, color);
      if (!res) continue;
      var bias = engineBias(engine, b, r, c, color) * 0.25;
      var child = negamax(engine, res.board, color === 1 ? 2 : 1, depth - 1, -beta, -alpha, res.captured);
      var sc = bias - child.score;
      if (sc > best.score) { best = { score: sc, move: [r, c] }; }
      if (sc > alpha) alpha = sc;
      if (alpha >= beta) break;
    }
    if (!best.move) best.score = evaluate(engine, b, color, captured);
    return best;
  }

  var plugin = {
    name: "go_lookahead",
    description: "囲碁の先読み(alpha-beta)で最善手を提案",
    // run(engine, board, color, depth)
    run: function (engine, board, color, depth) {
      color = color || 1; depth = depth || 2;
      var r = negamax(engine, board, color, depth, -Infinity, Infinity, 0);
      return { move: r.move, score: Math.round(r.score * 100) / 100, depth: depth, color: color };
    }
  };

  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).go_lookahead = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
