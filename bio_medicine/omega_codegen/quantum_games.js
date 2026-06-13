/*
 * quantum_games.js — 量子囲碁 / 量子将棋 による FPGA ゲノム生成器
 *
 * 盤上の各マスを 1 量子ビットに割り当て、ゲーム手をゲート(H/X/CX/位相)に写して
 * 状態ベクトルを構成し、Born 則で測定。測定結果(と上位基底状態)を種に未知事前エンジンの
 * ゲノム(=FPGA 構成)を決定論的に生成する。生成ゲノムは codegen.js で Verilog 等へ表出できる。
 *
 * ⚠ 概念実証・教育用。「量子将棋/量子囲碁」は重ね合わせ・エンタングルの簡易モデル。
 */
(function (global) {
  "use strict";
  var CELL_BYTES = 6;

  function mulberry32(a) {
    return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  function hashStr(s) { var h = 2166136261 >>> 0; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }

  // ---- 状態ベクトル量子シミュレータ ----
  function QState(n) { this.n = n; var N = 1 << n; this.re = new Float64Array(N); this.im = new Float64Array(N); this.re[0] = 1; }
  QState.prototype.H = function (q) {
    var bit = 1 << q, N = this.re.length, s = Math.SQRT1_2;
    for (var i = 0; i < N; i++) if (!(i & bit)) {
      var j = i | bit, ar = this.re[i], ai = this.im[i], br = this.re[j], bi = this.im[j];
      this.re[i] = (ar + br) * s; this.im[i] = (ai + bi) * s;
      this.re[j] = (ar - br) * s; this.im[j] = (ai - bi) * s;
    }
  };
  QState.prototype.X = function (q) {
    var bit = 1 << q, N = this.re.length;
    for (var i = 0; i < N; i++) if (!(i & bit)) { var j = i | bit;
      var tr = this.re[i]; this.re[i] = this.re[j]; this.re[j] = tr;
      var ti = this.im[i]; this.im[i] = this.im[j]; this.im[j] = ti; }
  };
  QState.prototype.P = function (q, th) { // 位相ゲート
    var bit = 1 << q, N = this.re.length, c = Math.cos(th), s = Math.sin(th);
    for (var i = 0; i < N; i++) if (i & bit) { var r = this.re[i], m = this.im[i];
      this.re[i] = r * c - m * s; this.im[i] = r * s + m * c; }
  };
  QState.prototype.CX = function (c, t) {
    var cb = 1 << c, tb = 1 << t, N = this.re.length;
    for (var i = 0; i < N; i++) if ((i & cb) && !(i & tb)) { var j = i | tb;
      var tr = this.re[i]; this.re[i] = this.re[j]; this.re[j] = tr;
      var ti = this.im[i]; this.im[i] = this.im[j]; this.im[j] = ti; }
  };
  QState.prototype.probs = function () { var N = this.re.length, p = new Float64Array(N);
    for (var i = 0; i < N; i++) p[i] = this.re[i] * this.re[i] + this.im[i] * this.im[i]; return p; };
  QState.prototype.sample = function (rng) { var p = this.probs(), r = rng(), acc = 0;
    for (var i = 0; i < p.length; i++) { acc += p[i]; if (r <= acc) return i; } return p.length - 1; };

  // ---- ゲーム→回路 ----
  function buildCircuit(kind, qs, rng) {
    var n = qs.n, moves = [];
    var rec = function (g, a, b) { moves.push([g, a, b]); };
    // 初手: 全マスを重ね合わせ(布石)
    for (var q = 0; q < n; q++) { qs.H(q); rec("H", q); }
    var rounds = kind === "shogi" ? n + 4 : n;
    for (var r = 0; r < rounds; r++) {
      var a = (rng() * n) | 0, b = (a + 1 + ((rng() * (n - 1)) | 0)) % n;
      if (kind === "shogi") {
        // 将棋: 駒打ち(X) と 利き(CX) と 成り(位相) を多用
        var pick = (rng() * 3) | 0;
        if (pick === 0) { qs.X(a); rec("X", a); }
        else if (pick === 1) { qs.CX(a, b); rec("CX", a, b); }
        else { qs.P(a, Math.PI / 2); rec("P", a); }
      } else {
        // 囲碁: 連の接続(CX) と コウ(位相) を多用
        if (rng() < 0.7) { qs.CX(a, b); rec("CX", a, b); }
        else { qs.P(a, Math.PI / 3); rec("P", a); }
      }
    }
    return moves;
  }

  // 量子ゲームから FPGA ゲノムを生成
  function quantumGenerate(kind, opt) {
    opt = opt || {};
    var cfg = opt.cfg || { inbits: 6, layers: 3, width: 8, outbits: 3 };
    var seed = (typeof opt.seed === "number") ? opt.seed : hashStr(String(opt.seed || (kind + "-0")));
    var n = opt.qubits || 9, shots = opt.shots || 256;
    var rng = mulberry32(seed >>> 0);
    var qs = new QState(n);
    var moves = buildCircuit(kind, qs, rng);

    // 測定: shots 回サンプリングし、最頻状態と分布エントロピーを得る
    var tally = {};
    for (var s = 0; s < shots; s++) { var m = qs.sample(rng); tally[m] = (tally[m] || 0) + 1; }
    var entries = Object.keys(tally).map(function (k) { return { state: +k, count: tally[k] }; })
      .sort(function (x, y) { return y.count - x.count; });
    var measured = entries[0].state;
    var ent = 0; entries.forEach(function (e) { var p = e.count / shots; ent -= p * Math.log2(p); });

    // 上位状態を混ぜてゲノム種を作る → PRNG でゲノム展開(決定論)
    var mix = measured >>> 0;
    for (var i = 0; i < Math.min(4, entries.length); i++) mix = (Math.imul(mix, 31) + entries[i].state) >>> 0;
    var grng = mulberry32((mix ^ seed) >>> 0);
    var gs = cfg.layers * cfg.width * CELL_BYTES;
    var g = new Uint8Array(gs);
    for (var j = 0; j < gs; j++) g[j] = (grng() * 256) | 0;
    var hex = Array.prototype.map.call(g, function (b) { return b.toString(16).padStart(2, "0"); }).join("");

    // 測定状態を盤(NxN風)へ
    var side = Math.ceil(Math.sqrt(n)), board = [];
    for (var rr = 0; rr < side; rr++) { var row = [];
      for (var cc = 0; cc < side; cc++) { var bitIdx = rr * side + cc; row.push(bitIdx < n ? ((measured >> bitIdx) & 1) : 0); }
      board.push(row); }

    return {
      kind: kind, qubits: n, shots: shots, seed: seed >>> 0,
      moves: moves.length, measured: measured, entropy: Math.round(ent * 1e3) / 1e3,
      top_states: entries.slice(0, 5).map(function (e) { return { state: e.state, p: Math.round(e.count / shots * 1e3) / 1e3 }; }),
      board: board, genome_hex: hex, genome_bytes: gs,
      summary: (kind === "shogi" ? "量子将棋" : "量子囲碁") + " " + n + "qubit " + moves.length +
        "手 → 測定 |" + measured.toString(2).padStart(n, "0") + "⟩ (エントロピー " +
        (Math.round(ent * 100) / 100) + " bit) → FPGAゲノム " + gs + "B"
    };
  }

  var API = { QState: QState, quantumGenerate: quantumGenerate,
    quantumGo: function (o) { return quantumGenerate("go", o); },
    quantumShogi: function (o) { return quantumGenerate("shogi", o); } };
  global.QuantumGames = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
