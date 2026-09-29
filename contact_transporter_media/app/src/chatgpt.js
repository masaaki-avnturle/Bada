/*
 * chatgpt.js — ChatGPT 設計図作成ソフト (GPT 系 Transformer の図解モデル)
 *   部品 ↔ 方程式 → 平面図 (ブロック図・立面図) → 3D → 組み立て → 使用 (推論) の動画と設計図 PDF を生成。
 *   ChatGPT 実機の内部構成は非公開のため、寸法は GPT-3 論文の公開値を参照した図解モデル。
 *   Python 版 (chatgpt_model.py / chatgpt_video.py / blueprint_pdf.py) の移植。
 */
(function (root) {
  "use strict";
  var BP = root.BP, C = BP.C, T = BP.text, sm = BP.smooth, PI = Math.PI;

  var HP = { L: 96, d: 12288, h: 96, dk: 128, dff: 49152, ctx: 2048, V: 50257 };
  var NS = 8, Z0 = 12, DZ = 14, LIM = 100;
  var COL = { tok: "#4fd6e0", emb: "#7fb2ff", ln: "#b8c7e0", attn: "#f5b942", mh: "#ffd166", ffn: "#c28bff",
              res: "#ffffff", unemb: "#ff6b5b", loss: "#ffa040", rlhf: "#9fe8ff" };
  var PARTS = [
    ["tok", "トークナイザ (BPE)", ["(a,b)* = argmax_(a,b) count(a b) を反復併合", "語彙 |V| = 50257"], "文字列 → トークン列 t₁…tₙ"],
    ["emb", "埋め込み", ["x_i⁽⁰⁾ = W_E[t_i] + W_P[i]", "W_E ∈ ℝ^(|V|×d),  d = 12288"], "文脈長 2048"],
    ["ln", "層正規化", ["LN(x) = γ ⊙ (x − μ)/√(σ² + ε) + β"], "各ブロックに 2 枚 (Pre-LN)"],
    ["attn", "自己注意 (ヘッド)", ["Attn(Q,K,V) = softmax(QKᵀ/√d_k + M) V", "Q = XW_Q, K = XW_K, V = XW_V,  M_ij = −∞ (j > i)"], "d_k = 128"],
    ["mh", "多頭結合", ["MH(X) = [head₁; …; head₉₆] W_O"], "96 ヘッド"],
    ["ffn", "フィードフォワード", ["FFN(x) = GELU(xW₁ + b₁)W₂ + b₂", "GELU(x) = x·Φ(x),  d_ff = 4d = 49152"], ""],
    ["res", "残差ストリーム", ["h ← h + MH(LN(h))", "h ← h + FFN(LN(h))   (×96 層)"], ""],
    ["unemb", "出力層 (softmax)", ["p(t_(n+1) | t_≤n) = softmax(W_U · LN(h_L) / T)"], "温度 T でサンプリング"],
    ["loss", "事前学習の損失", ["𝓛 = −Σ_i log p_θ(t_i | t_<i)"], "次トークン予測"],
    ["rlhf", "RLHF ループ", ["𝓛_RM = −log σ(r(x, y_w) − r(x, y_l))", "max_π E[r(x,y)] − β·KL(π ‖ π_ref)"], "人間の選好で整列"]
  ];
  var NAME = {}; PARTS.forEach(function (p) { NAME[p[0]] = p[1]; });
  var ORDER = ["tok", "emb", "res", "ln", "attn", "mh", "ffn", "unemb", "loss", "rlhf"];
  var EQS = []; PARTS.forEach(function (p) { p[2].forEach(function (e) { EQS.push([p[0], e]); }); });

  /* ---- 幾何 ---- */
  function box(cx, cy, cz, sx, sy, sz) {
    var x0 = cx - sx / 2, x1 = cx + sx / 2, y0 = cy - sy / 2, y1 = cy + sy / 2, z0 = cz, z1 = cz + sz;
    var b = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z0]];
    var t = b.map(function (p) { return [p[0], p[1], z1]; });
    var L = [b, t];
    [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].forEach(function (q) { L.push([[q[0], q[1], z0], [q[0], q[1], z1]]); });
    return L;
  }
  function bz(l) { return Z0 + DZ * l; }
  function geometry() {
    var g = {}; ORDER.forEach(function (k) { g[k] = []; });
    BP.linspace(-50, 50, 11).forEach(function (v) { g.tok.push([[v, -50, -20], [v, 50, -20]]); g.tok.push([[-50, v, -20], [50, v, -20]]); });
    g.emb = g.emb.concat(box(0, 0, -8, 80, 80, 10));
    BP.linspace(-36, 36, 9).forEach(function (v) { g.emb.push([[v, -40, 2], [v, 40, 2]]); });
    var top = bz(NS);
    for (var l = 0; l < NS; l++) {
      var z = bz(l);
      g.ln.push(box(0, 0, z, 72, 72, 0)[0]); g.ln.push(box(0, 0, z + 7, 72, 72, 0)[0]);
      for (var k = 0; k < 12; k++) {
        var a = 2 * PI * k / 12 + PI / 12, hx = 26 * Math.cos(a), hy = 26 * Math.sin(a);
        g.attn.push(BP.circle(3, z + 1, 20, hx, hy)); g.attn.push(BP.circle(3, z + 5, 20, hx, hy));
        g.attn.push([[hx + 3, hy, z + 1], [hx + 3, hy, z + 5]]); g.attn.push([[hx - 3, hy, z + 1], [hx - 3, hy, z + 5]]);
      }
      g.mh.push(BP.circle(26, z + 6, 100));
      g.ffn = g.ffn.concat(box(0, 0, z + 8, 62, 62, 4));
      BP.linspace(-28, 28, 8).forEach(function (v) { g.ffn.push([[v, -31, z + 12], [v, 31, z + 12]]); });
    }
    g.res.push([[0, 0, 2], [0, 0, top + 4]]);
    [[-36, -36], [36, -36], [36, 36], [-36, 36]].forEach(function (q) { g.res.push([[q[0], q[1], 2], [q[0], q[1], top]]); });
    var rim = [[-45, -45], [45, -45], [45, 45], [-45, 45], [-45, -45]].map(function (q) { return [q[0], q[1], top + 22]; });
    g.unemb.push(rim);
    for (var i = 0; i < 4; i++) g.unemb.push([[0, 0, top + 2], rim[i]]);
    [10, 4, 3, 2, 1.5, 1, 0.8].forEach(function (h, i) { var x = -30 + i * 10; g.loss.push([[x, 0, top + 24], [x, 0, top + 24 + 2 * h]]); });
    var zc = (top + 2) / 2, t = BP.linspace(0.15 * PI, 1.85 * PI, 160);
    g.rlhf.push(t.map(function (s) { return [88 * Math.sin(s), 0, zc + 92.4 * Math.cos(s)]; }));
    g.rlhf.push(t.map(function (s) { return [0, 88 * Math.sin(s), zc + 92.4 * Math.cos(s)]; }));
    return g;
  }
  var GEOM = geometry();

  /* ---- 使用シーン: 小型モデルでの注意の実計算 ---- */
  var PROMPT = ["コンタクト", "の", "輸送", "機", "の", "設計", "図", "を", "描い", "て"];
  var GEN = [
    ["外環", ["外環", "ポッド", "塔", "中環", "扉"], [4.1, 2.3, 1.9, 1.5, 0.7]],
    [" R", [" R", " 半径", " =", " は", "、"], [3.6, 2.2, 1.4, 1.2, 0.9]],
    [" =", [" =", " ≈", " :", " は", " 約"], [4.4, 1.6, 1.2, 1.0, 0.8]],
    [" 60", [" 60", " 47", " 70", " 37", " 132"], [3.9, 2.0, 1.8, 1.4, 1.0]],
    [".088", [".088", ".1", ".0", ".09", ".08"], [3.7, 2.1, 1.5, 1.3, 1.1]],
    [" m", [" m", " メートル", "、", " [m]", "。"], [4.0, 2.4, 1.6, 1.2, 1.0]],
    ["、ポッド", ["、ポッド", "、中環", "、塔", "。", "、扉"], [3.3, 3.0, 1.9, 1.2, 0.9]],
    [" r = 5.021 m", [" r = 5.021 m", " r = 5 m", " 半径", " 直径", " r"], [3.5, 2.2, 1.6, 1.1, 0.9]]
  ];
  var TEMP = 0.8;
  function softmax(z, Tt) { var m = Math.max.apply(null, z), e = z.map(function (v) { return Math.exp((v - m) / (Tt || 1)); }), s = e.reduce(function (a, b) { return a + b; }, 0); return e.map(function (v) { return v / s; }); }
  function crc32(str) {
    var c, crc = 0xffffffff;
    for (var i = 0; i < str.length; i++) { c = (crc ^ str.charCodeAt(i)) & 0xff; for (var k = 0; k < 8; k++) c = c & 1 ? (c >>> 1) ^ 0xedb88320 : c >>> 1; crc = (crc >>> 8) ^ c; }
    return (crc ^ 0xffffffff) >>> 0;
  }
  function rng(seed) { var s = seed >>> 0; return function () { s = (s + 0x6d2b79f5) >>> 0; var t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function gauss(r) { var u = Math.max(r(), 1e-12), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * PI * v); }
  function tinyAttention(tokens, nl, d) {
    var n = tokens.length, X = tokens.map(function (t, i) {
      var r = rng(crc32(t)), row = [];
      for (var j = 0; j < d; j++) { var ang = i / Math.pow(10000, j / d); row.push(gauss(r) + (j % 2 ? Math.cos(ang) : Math.sin(ang))); }
      return row;
    });
    function mul(A, B) { return A.map(function (a) { return B[0].map(function (_, j) { var s = 0; for (var k = 0; k < a.length; k++) s += a[k] * B[k][j]; return s; }); }); }
    var mats = [];
    for (var l = 0; l < nl; l++) {
      var r = rng(100 + l), W = [0, 1, 2].map(function () { var M = []; for (var i = 0; i < d; i++) { M.push([]); for (var j = 0; j < d; j++) M[i].push(gauss(r) / Math.sqrt(d)); } return M; });
      var Q = mul(X, W[0]), K = mul(X, W[1]), V = mul(X, W[2]), A = [];
      for (var i = 0; i < n; i++) {
        var s = [];
        for (var j = 0; j < n; j++) { var v = 0; for (var k = 0; k < d; k++) v += Q[i][k] * K[j][k]; s.push(j > i ? -Infinity : v / Math.sqrt(d)); }
        A.push(softmax(s.map(function (v) { return v === -Infinity ? -1e9 : v; })));
      }
      mats.push(A);
      var AV = mul(A, V);
      X = X.map(function (row, i) {
        var y = row.map(function (v, j) { return v + AV[i][j]; }), m = y.reduce(function (a, b) { return a + b; }, 0) / d;
        var sd = Math.sqrt(y.reduce(function (a, b) { return a + (b - m) * (b - m); }, 0) / d) + 1e-5;
        return y.map(function (v) { return (v - m) / sd; });
      });
    }
    return mats;
  }
  var ATTN = tinyAttention(PROMPT, NS, 16);

  function cam(rect, elev, azim, zoom) {
    return new BP.Camera({ rect: rect, elev: elev, azim: azim, center: [0, 0, 70], scale: rect[3] / 260 * (zoom || 1) });
  }
  function drawAll(ctx, c, o) {
    o = o || {};
    ORDER.forEach(function (k) {
      BP.drawPolys(ctx, c, GEOM[k], COL[k], { lw: o.lw || 0.9, alpha: o.alpha === undefined ? 0.95 : o.alpha, zscale: o.zscale,
                                             offset: o.offset ? o.offset[k] : undefined });
    });
  }

  var TL = new BP.Timeline([["title", 5], ["params", 9], ["mapping", 12], ["plan", 10], ["to3d", 8], ["assembly", 30], ["use", 24], ["end", 8]]);
  var TITLES = { params: "1. 設計パラメータ (GPT 系 Transformer)", mapping: "2. 方程式 → 部品への対応", plan: "3. 平面図 — ブロック図と立面図",
                 to3d: "4. 平面図 → 3D 変換", assembly: "5. 組み立て", use: "6. 使用 — プロンプトから次トークンを生成" };
  var LABELS = { title: "タイトル", params: "パラメータ", mapping: "方程式→部品", plan: "平面図", to3d: "3D 変換", assembly: "組み立て", use: "使用 (推論)", end: "終了" };

  function sTitle(ctx, u, sec) {
    BP.gridBg(ctx);
    drawAll(ctx, cam([390, 60, 500, 620], 15, -60 + 25 * sec, 1), { lw: 0.6, alpha: 0.3 * sm(u * 3) });
    var a = sm(u * 2.5);
    T(ctx, "ChatGPT BLUEPRINT", 0.5, 0.62, { size: 46, bold: true, align: "center", alpha: a });
    T(ctx, "大規模言語モデルの設計図 — 方程式から組み立てる 3D", 0.5, 0.52, { size: 22, align: "center", color: C.hud, alpha: a });
    T(ctx, "コンタクトの輸送機と同じ手順で: 方程式 → 部品 → 平面図 → 3D → 組み立て → 使用\n※ ChatGPT 実機の内部構成は非公開。寸法は GPT-3 論文の公開値を参照した図解モデル",
      0.5, 0.17, { size: 13, align: "center", alpha: sm(u * 2.5 - 0.6) });
  }
  var ROWS = [["層数", "L = 96  (図では代表 8 層)", COL.ln], ["隠れ次元", "d = 12288", COL.emb], ["注意ヘッド", "h = 96,  d_k = d / h = 128", COL.attn],
              ["FFN 次元", "d_ff = 4d = 49152", COL.ffn], ["文脈長", "n_ctx = 2048 トークン", COL.res], ["語彙", "|V| = 50257 (BPE)", COL.tok],
              ["パラメータ", "≈ 12·L·d² = 12·96·12288² ≈ " + (12 * 96 * 12288 * 12288).toExponential(2), COL.unemb],
              ["整列", "事前学習 → 教師あり微調整 → RLHF (報酬モデル + PPO)", COL.rlhf]];
  function sParams(ctx, u) {
    BP.gridBg(ctx);
    ROWS.forEach(function (r, i) {
      var a = sm((u * 1.25 - i * 0.1) * 5), y = 0.82 - i * 0.092;
      T(ctx, r[0], 0.07 + 0.02 * (1 - a), y, { size: 17, bold: true, color: r[2], alpha: a });
      T(ctx, r[1], 0.25 + 0.02 * (1 - a), y, { size: 16, alpha: a });
    });
    T(ctx, "参照: Vaswani+ 2017 (Transformer), Brown+ 2020 (GPT-3), Ouyang+ 2022 (InstructGPT/RLHF)", 0.07, 0.06, { size: 11, color: C.hud, alpha: sm(u * 3 - 2) });
  }
  function sMapping(ctx, u) {
    BP.gridBg(ctx);
    var n = Math.min(EQS.length, Math.floor(BP.clamp(sm(u * 1.1), 0, 1) * EQS.length + 0.999)), ys = {};
    PARTS.forEach(function (p, i) {
      var y = 0.84 - i * 0.078, cnt = EQS.slice(0, n).filter(function (e) { return e[0] === p[0]; }).length;
      ys[p[0]] = y;
      if (cnt) BP.rectF(ctx, 0.72, y - 0.026, 0.25, 0.056, { fill: COL[p[0]], fillAlpha: 0.15 });
      BP.rectF(ctx, 0.72, y - 0.026, 0.25, 0.056, { stroke: COL[p[0]], lw: 1.3 });
      T(ctx, p[1], 0.73, y - 0.01, { size: 12.5 });
    });
    EQS.slice(0, n).forEach(function (e, j) {
      var y = 0.86 - j * 0.047, a = sm((u * 1.1 * EQS.length - j) * 1.5);
      T(ctx, e[1], 0.04, y - 0.01, { size: 11.5, alpha: a });
      BP.lineF(ctx, 0.52, y, 0.715, ys[e[0]], COL[e[0]], 1, 0.7 * a);
    });
  }
  var BLOCKS = [["tok", "トークナイザ (BPE)", 0.05], ["emb", "埋め込み  W_E[t] + W_P[i]", 0.14], ["ln", "LayerNorm", 0.25],
                ["attn", "Masked Multi-Head Attention", 0.33], ["ln", "LayerNorm", 0.45], ["ffn", "FFN (GELU)", 0.53],
                ["ln", "LayerNorm (最終)", 0.68], ["unemb", "線形 W_U + softmax", 0.77], ["loss", "次トークン確率", 0.87]];
  function blockDiagram(ctx, r, prog, fsz) {
    fsz = fsz || 1;
    function X(f) { return r[0] + f * r[2]; } function Y(f) { return r[1] + (1 - f) * r[3]; }
    var n = Math.ceil(prog * BLOCKS.length);
    BLOCKS.slice(0, n).forEach(function (b, i) {
      ctx.save(); ctx.fillStyle = C.bg; ctx.strokeStyle = COL[b[0]]; ctx.lineWidth = 1.5;
      ctx.fillRect(X(0.2), Y(b[2] + 0.06), 0.6 * r[2], 0.06 * r[3]); ctx.strokeRect(X(0.2), Y(b[2] + 0.06), 0.6 * r[2], 0.06 * r[3]); ctx.restore();
      BP.textPx(ctx, b[1], X(0.5), Y(b[2] + 0.03) + 4, { size: 10 * fsz, align: "center" });
      if (i) BP.line(ctx, X(0.5), Y(BLOCKS[i - 1][2] + 0.06), X(0.5), Y(b[2]), C.fg, 1);
    });
    if (n >= 6) {
      ctx.save(); ctx.strokeStyle = COL.res; ctx.setLineDash([5, 4]); ctx.strokeRect(X(0.12), Y(0.61), 0.76 * r[2], 0.38 * r[3]); ctx.restore();
      BP.textPx(ctx, "× 96", X(0.9), Y(0.42), { size: 13 * fsz, color: COL.res });
      BP.textPx(ctx, "残差 +", X(0.02), Y(0.42), { size: 10 * fsz, color: COL.res });
    }
  }
  function elevation(ctx, rect, view, prog, fsz) {
    var parts = ORDER.map(function (k) { return { polys: GEOM[k], color: COL[k] }; });
    return BP.orthoView(ctx, rect, parts, view, [-100, 100], view === "top" ? [-100, 100] : [-30, 170], prog,
                        view === "top" ? "上面図 (x–y)" : "正面図 (x–z)", fsz);
  }
  function sPlan(ctx, u) {
    BP.gridBg(ctx);
    var p = sm(u / 0.75);
    blockDiagram(ctx, [30, 90, 440, 600], p);
    elevation(ctx, [500, 100, 380, 580], "front", p);
    elevation(ctx, [900, 180, 360, 380], "top", p);
    if (u > 0.8) T(ctx, "層ピッチ 14 / 注意ヘッド 12 基 (R = 26) 表示\n実機は 96 層 × 96 ヘッド", 0.71, 0.15, { size: 11, color: C.warn, alpha: sm((u - 0.8) * 6) });
  }
  function sTo3d(ctx, u) {
    var s = sm(u / 0.8);
    drawAll(ctx, cam([0, 30, 1280, 690], 89.9 - (89.9 - 20) * s, -90 + 30 * s, 1), { zscale: Math.max(s, 1e-3) });
    T(ctx, "z ← s · z(層番号 × ピッチ),  s = " + s.toFixed(2), 0.03, 0.86, { size: 14, color: C.hud });
    T(ctx, "上面図を起こして各層を積み上げる (残差ストリームが縦軸)", 0.03, 0.82, { size: 12 });
  }
  var EXPLODE = { tok: [0, 0, -60], emb: [0, 0, -70], res: [0, 0, 120], ln: [-140, 0, 0], attn: [140, 0, 20], mh: [0, 140, 0],
                  ffn: [0, -140, 0], unemb: [0, 0, 90], loss: [0, 0, 100], rlhf: [120, 0, 60] };
  function sAssembly(ctx, u) {
    var n = ORDER.length, step = u * n, cur = Math.min(Math.floor(step), n - 1), f = sm((step - cur) / 0.6);
    var c = cam([0, 40, 800, 660], 18, -60 + 40 * u, 0.95);
    for (var i = 0; i <= cur; i++) {
      var k = ORDER[i];
      if (i < cur) BP.drawPolys(ctx, c, GEOM[k], COL[k], { lw: 0.9, alpha: 0.9 });
      else BP.drawPolys(ctx, c, GEOM[k], COL[k], { lw: 1.6, alpha: 0.25 + 0.75 * f, offset: EXPLODE[k].map(function (v) { return v * (1 - f); }) });
    }
    var key = ORDER[cur], p = PARTS.filter(function (q) { return q[0] === key; })[0], col = COL[key], a = 0.35 + 0.65 * sm((step - cur) / 0.25);
    BP.card(ctx, 0.62, 0.30, 0.36, 0.50, col);
    T(ctx, "部品 " + (cur + 1) + "/" + n, 0.635, 0.75, { size: 12, color: col, alpha: a });
    T(ctx, p[1], 0.635, 0.70, { size: 16, bold: true, alpha: a });
    p[2].concat(p[3] ? [p[3]] : []).forEach(function (l, j) { T(ctx, l, 0.635, 0.62 - j * 0.08, { size: 12, alpha: a }); });
    ORDER.forEach(function (k, i) {
      var done = i < cur || (i === cur && f > 0.99);
      T(ctx, (done ? "■ " : "□ ") + NAME[k].split(" (")[0], 0.635 + (i % 2) * 0.17, 0.24 - Math.floor(i / 2) * 0.037, { size: 10, color: done ? C.hud : C.grid });
    });
  }
  function sUse(ctx, u, sec) {
    var np = PROMPT.length, c = cam([150, 70, 800, 650], 12, -90 + 25 * u, 0.95);
    drawAll(ctx, c, { lw: 0.7, alpha: 0.35 });
    var ntype = Math.min(np, Math.floor(BP.clamp(u / 0.15, 0, 1) * np + 0.999));
    T(ctx, "プロンプト:", 0.03, 0.86, { size: 13, color: C.hud });
    T(ctx, PROMPT.slice(0, ntype).join(""), 0.13, 0.86, { size: 15 });
    var cx = 0.03 * BP.W;
    ctx.save(); ctx.font = BP.fs(9).toFixed(1) + "px " + BP.FONT;
    PROMPT.slice(0, ntype).forEach(function (t) {
      var w = ctx.measureText(t).width + 10;
      ctx.strokeStyle = COL.tok; ctx.strokeRect(cx, 0.2 * BP.H - 13, w, 20);
      ctx.fillStyle = COL.tok; ctx.fillText(t, cx + 5, 0.2 * BP.H + 2); cx += w + 6;
    });
    ctx.restore();
    var climb = sm((u - 0.18) / 0.42), ztop = bz(NS) + 4, zt = -18 + (ztop + 18) * climb;
    var layer = Math.max(0, Math.min(NS - 1, Math.floor((zt - Z0) / DZ)));
    var xs = PROMPT.slice(0, ntype).map(function (_, i) { return -40 + 80 * i / (np - 1); });
    BP.drawPolys(ctx, c, xs.map(function (x) { return [[x, 0, zt]]; }), COL.tok, { r: 4.5 });
    if (u > 0.2 && u < 0.62) {
      var A = ATTN[layer], q = np - 1;
      for (var j = 0; j < np; j++) {
        var w = A[q][j]; if (w < 0.02) continue;
        var arc = BP.linspace(0, PI, 30).map(function (t) { return [xs[q] + (xs[j] - xs[q]) * (1 - Math.cos(t)) / 2, 0, zt + 4 + 20 * w * Math.sin(t)]; });
        BP.drawPolys(ctx, c, [arc], COL.attn, { lw: 0.6 + 4 * w, alpha: 0.9 });
      }
      BP.heatmap(ctx, [40, 400, 250, 250], A);
      BP.textPx(ctx, "層 " + (layer + 1) + ": softmax(QKᵀ/√d + M)", 165, 392, { size: 9, align: "center" });
      BP.textPx(ctx, "小型ランダム初期化モデルでの実計算 (因果マスク)", 40, 672, { size: 8.5, color: C.grid });
      T(ctx, "層 " + (layer + 1) + "/" + NS + " (実機 96 層) を通過中", 0.03, 0.52, { size: 13, color: C.warn });
    }
    var gu = BP.clamp((u - 0.6) / 0.38, 0, 1), ng = Math.min(GEN.length, Math.floor(gu * GEN.length + (gu > 0 ? 0.999 : 0)));
    if (ng) {
      T(ctx, "生成:", 0.03, 0.7, { size: 13, color: C.hud });
      T(ctx, GEN.slice(0, ng).map(function (g) { return g[0]; }).join(""), 0.09, 0.7, { size: 15, color: C.warn });
      var g = GEN[ng - 1], p = softmax(g[2], TEMP), pl = new BP.Plot(ctx, [1040, 175, 200, 250], [0, 1], [0, 5], "p = softmax(z / T),  T = 0.8");
      p.forEach(function (v, i) {
        ctx.save(); ctx.fillStyle = i ? COL.loss : COL.unemb; ctx.fillRect(pl.X(0), pl.Y(5 - i) + 8, pl.X(v) - pl.X(0), 30); ctx.restore();
        BP.textPx(ctx, g[1][i], pl.X(0) - 6, pl.Y(5 - i) + 28, { size: 9.5, align: "right" });
      });
      BP.textPx(ctx, "候補と logit は図解用の例示値", 1040, 450, { size: 8.5, color: C.grid });
      BP.drawPolys(ctx, c, [[[0, 0, ztop + 20]]], COL.unemb, { r: 5 + 2 * Math.sin(sec * 8) });
    }
    if (u > 0.9) T(ctx, "→ 生成された寸法は\n   輸送機の設計図 (外環 60.088 m,\n   ポッド r 5.021 m) と一致", 0.8, 0.3, { size: 11, color: C.hud, alpha: sm((u - 0.9) * 10) });
  }
  function sEnd(ctx, u, sec) {
    BP.gridBg(ctx);
    drawAll(ctx, cam([320, 40, 640, 470], 18, -60 + 20 * sec, 1), { lw: 0.7, alpha: 0.6 * sm(u * 3) });
    var a = sm(u * 3 - 0.3);
    T(ctx, "方程式 " + EQS.length + " 本 → 部品 10 点 → 平面図 → 3D → 組み立て → 使用", 0.5, 0.2, { size: 16, align: "center", alpha: a });
    T(ctx, "※ 公開論文の式に基づく図解モデルです。ChatGPT 実機の非公開の構成・寸法を示すものではありません。", 0.5, 0.09, { size: 12, align: "center", color: C.warn, alpha: a });
  }
  var SCENES = { title: sTitle, params: sParams, mapping: sMapping, plan: sPlan, to3d: sTo3d, assembly: sAssembly, use: sUse, end: sEnd };
  function frame(ctx, sec) {
    var s = TL.at(sec);
    BP.clear(ctx);
    SCENES[s.name](ctx, s.u, s.local);
    if (s.name !== "title") BP.header(ctx, TITLES[s.name], "ChatGPT BLUEPRINT", sec, TL.total);
    var edge = Math.min(s.local, s.dur - s.local);
    if (edge < 0.35) BP.fade(ctx, 1 - edge / 0.35);
  }
  function audio(sr) {
    var n = Math.floor(TL.total * sr), out = new Float32Array(n), u0 = TL.start("use"), k;
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      out[i] = (0.08 * Math.sin(2 * PI * 110 * t) + 0.04 * Math.sin(2 * PI * 164.8 * t)) * BP.clamp(t / 2, 0, 1) * BP.clamp((TL.total - t) / 2, 0, 1);
    }
    for (k = 0; k < 60; k++) {
      var tk = u0 + 24 * (0.2 + 0.78 * k / 60), i0 = Math.floor(tk * sr);
      for (var j = 0; j < 0.05 * sr && i0 + j < n; j++) out[i0 + j] += 0.12 * Math.sin(2 * PI * 880 * j / sr) * Math.exp(-j / sr * 60);
    }
    return out;
  }

  /* ---- PDF ---- */
  var PW = BP.PDF_W, PH = BP.PDF_H;
  function Tp(ctx, s, x, y, o) { T(ctx, s, x, y, o, PW, PH); }
  var NOTE = "※ 公開論文 (Transformer, GPT-3, InstructGPT) の式に基づく図解モデルです。ChatGPT 実機の非公開の構成・寸法を示すものではありません。";
  var pdfPages = [
    function (ctx) {
      Tp(ctx, "ChatGPT BLUEPRINT", 0.05, 0.84, { size: 34, bold: true });
      Tp(ctx, "大規模言語モデル  3 次元設計図 (組立図・部品表・方程式対応表)", 0.05, 0.785, { size: 15, color: C.hud });
      ["コンタクトの輸送機と同じ手順で作図: 方程式 → 部品 → 平面図 → 3D → 組み立て → 使用",
       "構成: トークナイザ → 埋め込み → [LayerNorm → 自己注意 → LayerNorm → FFN] × 96 → 出力 softmax",
       "整列: 事前学習 (次トークン予測) → 教師あり微調整 → RLHF (報酬モデル + PPO)",
       "寸法: GPT-3 論文の公開値 (L = 96, d = 12288, h = 96, |V| = 50257, n_ctx = 2048)"].forEach(function (l, i) { Tp(ctx, l, 0.05, 0.71 - i * 0.04, { size: 10.5 }); });
      drawAll(ctx, cam([680, 170, 460, 600], 18, -58, 1), { lw: 0.7 });
      Tp(ctx, "目次", 0.05, 0.47, { size: 11, bold: true, color: C.hud });
      ["01 表紙", "02 設計パラメータ", "03 部品 ↔ 方程式 対応表", "04 平面図 (ブロック図・立面図)", "05 3D 等角図・分解組立図", "06 使用 (推論フロー)", "07 注記"]
        .forEach(function (t, i) { Tp(ctx, t, 0.05, 0.43 - i * 0.035, { size: 9.5 }); });
      Tp(ctx, NOTE, 0.03, 0.1, { size: 7.5, color: C.warn });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "1. 設計パラメータ", "GPT-3 175B (Brown et al., 2020) の公開値を参照");
      var rows = [["層数 L", "96", "図では代表 8 層を表示 (層ピッチ 14)"], ["隠れ次元 d", "12288", ""], ["注意ヘッド h", "96", "d_k = d/h = 128 (図では 12 基)"],
                  ["FFN 次元 d_ff", "49152", "= 4d"], ["文脈長 n_ctx", "2048", ""], ["語彙 |V|", "50257", "BPE"],
                  ["パラメータ数", "≈ 1.75 × 10¹¹", "概算 12·L·d² = " + (12 * 96 * 12288 * 12288).toExponential(3)], ["温度 T", "0.8 (図解例)", "p = softmax(z/T)"],
                  ["RLHF 係数 β", "KL 正則化", "max E[r] − β KL(π‖π_ref)"]];
      ["量", "値", "備考"].forEach(function (h, j) { Tp(ctx, h, [0.05, 0.3, 0.5][j], 0.85, { size: 11, bold: true, color: C.hud }); });
      rows.forEach(function (r, i) {
        var y = 0.8 - i * 0.06;
        r.forEach(function (v, j) { Tp(ctx, v, [0.05, 0.3, 0.5][j], y, { size: 11, color: j ? C.fg : C.warn }); });
        BP.lineF(ctx, 0.045, y - 0.018, 0.95, y - 0.018, C.grid, 0.5, 1, PW, PH);
      });
      Tp(ctx, "参照: Vaswani+ 2017 “Attention Is All You Need”, Brown+ 2020 “Language Models are Few-Shot Learners”,\nOuyang+ 2022 “Training language models to follow instructions with human feedback”", 0.05, 0.16, { size: 9 });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "2. 部品 ↔ 方程式 対応表");
      ["No.", "部品", "支配方程式", "寸法・備考"].forEach(function (h, j) { Tp(ctx, h, [0.035, 0.07, 0.24, 0.72][j], 0.88, { size: 10, bold: true, color: C.hud }); });
      PARTS.forEach(function (p, i) {
        var y = 0.84 - i * 0.078;
        Tp(ctx, String(i + 1), 0.04, y, { size: 11, bold: true, color: COL[p[0]] });
        Tp(ctx, p[1], 0.07, y, { size: 10.5, bold: true, color: COL[p[0]] });
        p[2].forEach(function (e, j) { Tp(ctx, e, 0.24, y - j * 0.03, { size: 9.5 }); });
        Tp(ctx, p[3], 0.72, y, { size: 9 });
        BP.lineF(ctx, 0.03, y - 0.05, 0.965, y - 0.05, C.grid, 0.5, 1, PW, PH);
      });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "3. 平面図 — ブロック図と立面図", "左: 1 ブロックの構成 (Pre-LN)  中: 正面図  右: 上面図");
      blockDiagram(ctx, [30, 110, 380, 640], 1, 0.95);
      elevation(ctx, [440, 120, 350, 620], "front", 1);
      elevation(ctx, [810, 220, 330, 400], "top", 1);
      Tp(ctx, "層ピッチ 14 / 注意ヘッド 12 基 (R = 26) / FFN 62×62\nRLHF ループ R = 88 (報酬の帰還路)", 0.69, 0.2, { size: 9, color: C.warn });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "4. 3D 等角図・分解組立図", "右の番号 = 組立順");
      drawAll(ctx, cam([10, 120, 480, 650], 18, -58, 1), { lw: 0.7 });
      var c = new BP.Camera({ rect: [450, 90, 440, 700], elev: 18, azim: -58, center: [0, 0, 70], scale: 700 / 420 });
      ORDER.forEach(function (k, i) {
        var off = EXPLODE[k].map(function (v) { return v * 0.6; });
        BP.drawPolys(ctx, c, GEOM[k], COL[k], { lw: 0.6, offset: off });
        var cen = BP.centroid(GEOM[k]), q = c.p([cen[0] + off[0], cen[1] + off[1], cen[2] + off[2]]);
        BP.balloon(ctx, q[0], q[1], i + 1, COL[k]);
      });
      ORDER.forEach(function (k, i) { Tp(ctx, (i + 1) + ". " + NAME[k], 0.79, 0.85 - i * 0.07, { size: 10, bold: true, color: COL[k] }); });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "5. 使用 (推論フロー)", "プロンプト → トークン → 96 層 → softmax → 次トークン (自己回帰)");
      Tp(ctx, "プロンプト: " + PROMPT.join(""), 0.04, 0.86, { size: 11 });
      Tp(ctx, "トークン (概略): " + PROMPT.join(" | "), 0.04, 0.83, { size: 9.5, color: COL.tok });
      [0, 2, 5, 7].forEach(function (l, i) {
        BP.heatmap(ctx, [50 + i * 185, 200, 160, 160], ATTN[l]);
        BP.textPx(ctx, "層 " + (l + 1) + " の注意行列", 130 + i * 185, 192, { size: 9, align: "center" });
      });
      Tp(ctx, "softmax(QKᵀ/√d + M): 小型ランダム初期化モデル (d = 16) での実計算。上三角は因果マスク M = −∞ で 0。", 0.04, 0.53, { size: 8.5 });
      var g = GEN[0], p = softmax(g[2], TEMP), pl = new BP.Plot(ctx, [880, 200, 250, 160], [0, 1], [0, 5], "次トークン確率 (1 手目, T = 0.8)");
      p.forEach(function (v, i) {
        ctx.save(); ctx.fillStyle = i ? COL.loss : COL.unemb; ctx.fillRect(pl.X(0), pl.Y(5 - i) + 5, pl.X(v) - pl.X(0), 20); ctx.restore();
        BP.textPx(ctx, g[1][i], pl.X(0) - 5, pl.Y(5 - i) + 19, { size: 8, align: "right" });
      });
      Tp(ctx, "生成ステップ (候補と logit は図解用の例示値):", 0.04, 0.45, { size: 10, color: C.hud });
      var text = "";
      GEN.forEach(function (g, i) {
        text += g[0]; var q = softmax(g[2], TEMP);
        Tp(ctx, (i + 1) + ". 選択 “" + g[0].trim() + "” (p = " + q[0].toFixed(2) + ")   →   " + text, 0.05, 0.41 - i * 0.03, { size: 9 });
      });
      Tp(ctx, "生成された寸法 (外環 R = 60.088 m, ポッド r = 5.021 m)\nは輸送機の設計図の値と一致する。", 0.6, 0.35, { size: 10, color: C.hud });
    },
    function (ctx) {
      BP.pdfTitle(ctx, "6. 注記");
      ["・部品と方程式は公開論文の標準的な Transformer デコーダ (GPT 系) に従う。",
       "・3D 形状は図解のための配置: 層 = 水平スラブ, 注意ヘッド = 環状の円柱, 残差ストリーム = 中心軸, RLHF = 外周の帰還環。",
       "・注意行列は小型のランダム初期化モデルで実際に softmax(QKᵀ/√d + M) を計算した例であり、学習済みモデルの値ではない。",
       "・生成例の候補・logit は説明用の例示値である。", "・生成: ChatGPT 設計図作成ソフト (Bada Blueprint Studio)", "", NOTE]
        .forEach(function (l, i) { Tp(ctx, l, 0.05, 0.84 - i * 0.05, { size: 10, color: l === NOTE ? C.warn : C.fg }); });
    }
  ];

  root.BP_APP = {
    id: "chatgpt", title: "ChatGPT 設計図作成ソフト", subtitle: "ChatGPT BLUEPRINT — GPT 系 Transformer の部品・方程式から 3D 設計図と動画を生成",
    brand: "ChatGPT BLUEPRINT — 大規模言語モデル 3D 設計図", pdfTitle: "ChatGPT 3D Blueprint", fileBase: "chatgpt_blueprint",
    timeline: TL, sceneLabels: LABELS, frame: frame, audio: audio, pdfPages: pdfPages,
    aboutHtml: "公開論文 (Transformer / GPT-3 / InstructGPT) の式を部品に対応させ、平面図 → 3D → 組み立て → 推論を描きます。" +
      "注意行列はアプリ内の小型モデルで実計算します。<br>※ ChatGPT 実機の非公開の構成を示すものではありません。",
    _test: { ATTN: ATTN, softmax: softmax, EQS: EQS }
  };
})(typeof window !== "undefined" ? window : globalThis);
