/*
 * engine-test.js — Bada 瞬読 のエンジン単体テスト (Node で実行)
 *
 *   node bada_sokudoku/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 画像側・文字側・時間側の純ロジックを合成頁で検証します:
 *    1. 基盤 (決定論的乱数 / 直交射影 / softmax / LayerNorm)
 *    2. 積分画像と Sauvola 適応二値化 (照明勾配に耐えるか)
 *    3. 書字方向の判定 (横書き / 縦書き)
 *    4. パッチ特徴
 *    5. 窓分割と窓自己注意 (行和 1 / 相対位置バイアスの異方性)
 *    6. 注意ロールアウト (区分対角の積 / 行和 1)
 *    7. 連結成分 = 文字の固まり (二段組を二つに分ける)
 *    8. 行分割と固まり分割 (投影プロファイル)
 *    9. XY-cut の読み順 (縦書きは右から左)
 *   10. analyzePage 総体 (横書き頁 / 縦書き頁)
 *   11. 日本語チャンカ (切っても字は消えない)
 *   12. LaTeX 剥がし / 語中シャッフル
 *   13. 速読スケジューラ (目標 cpm の再現 / 二分探索)
 *   14. 対象者プロファイルと視野負荷
   15. 読み手の取り込み (肌色・顔・目・視線)
   16. 視線の追跡 (停留 / サッカード / 逆行 / 瞬き)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m){ console.error("no inline <script> in index.html"); process.exit(1); }

/* ── DOM スタブ (エンジン部は DOM に触れない。boot() は呼ばない) ── */
function stubEl(){
  return new Proxy({ style:{}, classList:{ add(){}, remove(){}, toggle(){} }, value:"", textContent:"",
                     innerHTML:"", className:"", width:0, height:0, checked:false }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "getAttribute") return function(){ return ""; };
      if (p === "getContext") return function(){ return new Proxy({}, { get(){ return function(){}; } }); };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console, Math, Date, Object, Array, String, Number, JSON, Boolean, RegExp, Error,
  Float64Array, Float32Array, Uint8Array, Uint8ClampedArray, Int32Array, Map, Set, Proxy,
  isNaN, parseInt, parseFloat, performance: { now: () => Date.now() },
  setTimeout: fn => fn(), setInterval: () => 0, clearInterval(){},
  requestAnimationFrame: null,
  window: { addEventListener(){}, __SOKUDOKU_NO_BOOT: true },
  document: {
    readyState: "complete",
    getElementById(){ return stubEl(); },
    createElement(){ return stubEl(); },
    querySelector(){ return stubEl(); },
    querySelectorAll(){ return []; },
    addEventListener(){},
    body: { clientWidth: 900 }
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "bada_sokudoku/index.html" });

const {
  srand, matOrtho, matVec, softmaxInto, layerNorm, gelu, median, mad,
  integralImage, boxStats, sauvola, resizeGray, projection, detectDirection, rlsa, inkRatio,
  patchFeatures, posEnc2D, embedPatches, windowPartition, windowAttention, swinEncode,
  rolloutHat, attentionRollout, blocksFromAttention,
  splitLines, splitChunks, xyCut, groupChunks, analyzePage,
  textChunks, groupTextChunks, normalizeText, orpIndex, scrambleInner, stripLatex,
  buildSchedule, stepAt, profileFrom, sessionStats, loadIndex, charClass,
  skinMask, motionMap, readerPatchFeatures, locateEyes, gazeFrom, analyzeReaderFrame,
  trackerNew, trackerPush, trackerStats
} = sandbox;

let failures = 0, checks = 0;
function assert(cond, msg){
  checks++;
  if (cond) console.log("  ✓ " + msg);
  else { failures++; console.log("  ✗ " + msg); }
}
function near(a, b, tol, msg){ assert(Math.abs(a - b) <= tol, msg + "  (" + a + " ≈ " + b + " ±" + tol + ")"); }

/* ═════════ 合成頁 — 本物の画素を作ってから解析させる ═════════ */
/* 紙は照明が傾いた白、字は黒い矩形。字の形は問わない (本アプリは字を読まない)。 */
function blankPage(w, h){
  const g = new Float64Array(w * h);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++)
      g[y * w + x] = 0.98 - 0.30 * (x / w) - 0.12 * (y / h);   /* 右下ほど暗い照明 */
  return g;
}
function putChar(g, w, h, x0, y0, cw, ch){
  for (let y = y0; y < y0 + ch; y++)
    for (let x = x0; x < x0 + cw; x++){
      if (x < 0 || y < 0 || x >= w || y >= h) continue;
      /* 字らしく内側に隙間を作る (一様な黒塗りにしない) */
      const inner = (x - x0) > 3 && (x - x0) < cw - 3 && (y - y0) > 3 && (y - y0) < ch - 3;
      g[y * w + x] = Math.max(0.02, g[y * w + x] - (inner ? 0.30 : 0.82));
    }
}
/* 横書き頁: 1 段 or 2 段 */
function makeHPage(opts){
  opts = opts || {};
  const w = opts.w || 480, h = opts.h || 640;
  const g = blankPage(w, h);
  const cw = 14, chh = 14, pitch = 18, lineH = 26;
  const cols = opts.cols || 1;
  const colW = cols === 1 ? (w - 80) : 170;
  const gutter = 60;
  const lines = opts.lines || 6;
  const boxes = [];
  for (let c = 0; c < cols; c++){
    const x0 = 40 + c * (colW + gutter);
    const nchars = Math.floor(colW / pitch);
    for (let l = 0; l < lines; l++){
      const y = 60 + l * lineH;
      for (let i = 0; i < nchars; i++) putChar(g, w, h, x0 + i * pitch, y, cw, chh);
    }
    boxes.push({ x: x0, y: 60, w: nchars * pitch, h: lines * lineH });
  }
  return { gray: g, w: w, h: h, lines: lines, cols: cols, boxes: boxes, pitch: pitch, lineH: lineH };
}
/* 縦書き頁: 列が右から左へ */
function makeVPage(opts){
  opts = opts || {};
  const w = opts.w || 480, h = opts.h || 640;
  const g = blankPage(w, h);
  const cw = 14, chh = 14, pitch = 18, colW = 26;
  const ncols = opts.ncols || 6;
  const nchars = Math.floor((h - 120) / pitch);
  for (let c = 0; c < ncols; c++){
    const x = w - 60 - c * colW;
    for (let i = 0; i < nchars; i++) putChar(g, w, h, x, 60 + i * pitch, cw, chh);
  }
  return { gray: g, w: w, h: h, ncols: ncols, nchars: nchars };
}

/* ═══════════════ 1. 基盤 ═══════════════ */
console.log("\n── 1. 基盤 (乱数・直交射影・softmax・LayerNorm) ──");
{
  const a = srand(42), b = srand(42);
  let same = true;
  for (let i = 0; i < 100; i++) if (a() !== b()) same = false;
  assert(same, "同じ種からは同じ乱数列 (同じ頁は必ず同じ版面に分かれる)");
  const r = srand(1);
  let mn = 1, mx = 0;
  for (let i = 0; i < 5000; i++){ const v = r(); if (v < mn) mn = v; if (v > mx) mx = v; }
  assert(mn >= 0 && mx < 1, "乱数は [0,1)");

  const M = matOrtho(8, 12, 99);
  let ortho = true;
  for (let i = 0; i < 8; i++){
    let n = 0;
    for (let k = 0; k < 12; k++) n += M[i][k] * M[i][k];
    if (Math.abs(n - 1) > 1e-9) ortho = false;
    for (let j = i + 1; j < 8; j++){
      let d = 0;
      for (let k = 0; k < 12; k++) d += M[i][k] * M[j][k];
      if (Math.abs(d) > 1e-9) ortho = false;
    }
  }
  assert(ortho, "固定射影の行ベクトルは正規直交 (無学習でも特徴を潰さない)");

  const v = softmaxInto(Float64Array.from([1, 2, 3, 4]));
  let s = 0;
  for (let i = 0; i < v.length; i++) s += v[i];
  near(s, 1, 1e-12, "softmax の和は 1");
  assert(v[3] > v[0], "softmax は大きい要素に重みを寄せる");
  const big = softmaxInto(Float64Array.from([1000, 1001]));
  assert(isFinite(big[0]) && isFinite(big[1]), "softmax は大きな値でも溢れない (最大値を引いている)");

  const ln = layerNorm(Float64Array.from([1, 2, 3, 4, 10]));
  let mu = 0;
  for (let i = 0; i < ln.length; i++) mu += ln[i];
  near(mu / ln.length, 0, 1e-9, "LayerNorm の平均は 0");
  let sd = 0;
  for (let i = 0; i < ln.length; i++) sd += ln[i] * ln[i];
  near(Math.sqrt(sd / ln.length), 1, 1e-4, "LayerNorm の分散は 1");
  near(gelu(0), 0, 1e-12, "GELU(0)=0");
  assert(gelu(3) > 2.9 && gelu(-3) < 0, "GELU は正で線形に近づき負で潰れる");
  assert(median([3, 1, 2]) === 2 && mad([1, 1, 1, 10]) === 0, "中央値と MAD (外れ値に動じない)");
}

/* ═══════════════ 2. 積分画像と Sauvola ═══════════════ */
console.log("\n── 2. 積分画像と Sauvola 適応二値化 ──");
{
  const w = 40, h = 30;
  const g = new Float64Array(w * h);
  const rng = srand(5);
  for (let i = 0; i < g.length; i++) g[i] = rng();
  const ii = integralImage(g, w, h);
  let ok = true;
  for (let t = 0; t < 20; t++){
    const x0 = Math.floor(rng() * 20), y0 = Math.floor(rng() * 15);
    const x1 = x0 + 1 + Math.floor(rng() * 15), y1 = y0 + 1 + Math.floor(rng() * 10);
    let s = 0, n = 0;
    for (let y = y0; y < Math.min(y1, h); y++)
      for (let x = x0; x < Math.min(x1, w); x++){ s += g[y * w + x]; n++; }
    const st = boxStats(ii, x0, y0, x1, y1);
    if (Math.abs(st.mean - s / n) > 1e-9) ok = false;
  }
  assert(ok, "積分画像の窓平均が総当たりと一致する (O(1) で引ける)");

  const pg = makeHPage({});
  const ink = sauvola(pg.gray, pg.w, pg.h, {});
  const ratio = inkRatio(ink);
  assert(ratio > 0.02 && ratio < 0.45, "墨率が妥当な範囲 (" + (ratio * 100).toFixed(1) + "%) — 全黒でも白飛びでもない");
  /* 照明がいちばん暗い右下の余白が墨と誤判定されていないこと */
  let bgInk = 0, bgN = 0;
  for (let y = pg.h - 40; y < pg.h - 5; y++)
    for (let x = pg.w - 40; x < pg.w - 5; x++){ bgInk += ink[y * pg.w + x]; bgN++; }
  assert(bgInk / bgN < 0.05, "照明が落ちた余白を墨と間違えない (適応二値化が効いている)");
  /* 字のある所は墨と判定されること */
  let fg = 0, fgN = 0;
  for (let y = 62; y < 70; y++)
    for (let x = 42; x < 200; x++){ fg += ink[y * pg.w + x]; fgN++; }
  assert(fg / fgN > 0.3, "字のある行は墨として拾われる");

  const sm = rlsa(Uint8Array.from([0,1,0,0,1,0, 0,0,0,0,0,0]), 6, 2, 3, 0);
  assert(sm[2] === 1 && sm[3] === 1, "RLSA は閾値以下の空白を埋める");
  const sm2 = rlsa(Uint8Array.from([0,1,0,0,1,0, 0,0,0,0,0,0]), 6, 2, 1, 0);
  assert(sm2[2] === 0, "RLSA は閾値を超える空白は埋めない (段の間は繋がない)");
}

/* ═══════════════ 3. 書字方向 ═══════════════ */
console.log("\n── 3. 書字方向の判定 ──");
{
  const hp = makeHPage({});
  const hInk = sauvola(hp.gray, hp.w, hp.h, {});
  const dh = detectDirection(hInk, hp.w, hp.h);
  assert(dh.dir === "h", "横書きの頁を横書きと判定する");
  const vp = makeVPage({});
  const vInk = sauvola(vp.gray, vp.w, vp.h, {});
  const dv = detectDirection(vInk, vp.w, vp.h);
  assert(dv.dir === "v", "縦書きの頁を縦書きと判定する");
  const rowp = projection(hInk, hp.w, hp.h, "row");
  assert(rowp.length === hp.h, "行プロファイルの長さは頁の高さ");
}

/* ═══════════════ 4. パッチ特徴 ═══════════════ */
console.log("\n── 4. パッチ埋め込み ──");
{
  const w = 64, h = 32;
  const g = new Float64Array(w * h).fill(1);
  const ink = new Uint8Array(w * h);
  for (let y = 8; y < 16; y++) for (let x = 8; x < 16; x++) ink[y * w + x] = 1;
  const grid = patchFeatures(g, ink, w, h, 8);
  assert(grid.cols === 8 && grid.rows === 4 && grid.n === 32, "パッチ格子の大きさ");
  near(grid.dens[1 * 8 + 1], 1, 1e-12, "墨で埋まったパッチの密度は 1");
  near(grid.dens[0], 0, 1e-12, "白いパッチの密度は 0");
  assert(grid.feat.length === grid.n * 12, "パッチあたり 12 次元の特徴");
  const pe = posEnc2D(3, 5, 24);
  let bounded = true;
  for (let i = 0; i < pe.length; i++) if (Math.abs(pe[i]) > 1.0000001) bounded = false;
  assert(bounded && pe.length === 24, "位置符号は有界で次元が合う");
  const pe2 = posEnc2D(3, 6, 24);
  let diff = 0;
  for (let i = 0; i < 24; i++) diff += Math.abs(pe[i] - pe2[i]);
  assert(diff > 1e-6, "違う位置には違う符号が付く");
  const toks = embedPatches(grid, 24, 7);
  assert(toks.length === grid.n && toks[0].length === 24, "トークン列の形");
}

/* ═══════════════ 5. 窓分割と窓自己注意 ═══════════════ */
console.log("\n── 5. 窓自己注意 (Swin 型) ──");
{
  const cols = 16, rows = 12;
  const wins = windowPartition(cols, rows, 8, 0);
  const seen = new Set();
  let dup = false;
  wins.forEach(function(idx){ idx.forEach(function(i){ if (seen.has(i)) dup = true; seen.add(i); }); });
  assert(!dup && seen.size === cols * rows, "窓分割はパッチを重複なく覆う");
  const shifted = windowPartition(cols, rows, 8, 4);
  const seen2 = new Set();
  shifted.forEach(function(idx){ idx.forEach(function(i){ seen2.add(i); }); });
  assert(seen2.size === cols * rows, "ずらした窓分割も全パッチを覆う");
  assert(shifted.length !== wins.length || JSON.stringify(shifted[0]) !== JSON.stringify(wins[0]),
         "ずらした窓は元の窓と境界が違う (窓を跨いで情報が流れる)");

  const dim = 16, n = cols * rows;
  const rng = srand(3);
  const toks = [];
  for (let i = 0; i < n; i++){
    const t = new Float64Array(dim);
    for (let k = 0; k < dim; k++) t[k] = rng() - 0.5;
    toks.push(t);
  }
  const Wq = matOrtho(dim, dim, 1), Wk = matOrtho(dim, dim, 2),
        Wv = matOrtho(dim, dim, 3), Wo = matOrtho(dim, dim, 4);
  const idx = wins[0];
  const r = windowAttention(toks, idx, cols, Wq, Wk, Wv, Wo, 4, 0.55, 0.12);
  let rowsOk = true;
  for (let i = 0; i < r.m; i++){
    let s = 0;
    for (let j = 0; j < r.m; j++) s += r.A[i * r.m + j];
    if (Math.abs(s - 1) > 1e-9) rowsOk = false;
  }
  assert(rowsOk, "注意行列の行和は 1 (ヘッド平均をとっても確率のまま)");
  /* 異方バイアス: 同じ行の 3 つ隣 vs 同じ列の 3 つ下 */
  const i0 = idx.indexOf(0);
  const sameRow = idx.indexOf(3), sameCol = idx.indexOf(3 * cols);
  assert(sameRow >= 0 && sameCol >= 0, "比較用のパッチが同じ窓にある");
  assert(r.A[i0 * r.m + sameRow] > r.A[i0 * r.m + sameCol],
         "横書きでは同じ行の隣を、同じ距離の縦の隣より強く見る (相対位置バイアスの異方性)");
  const rv = windowAttention(toks, idx, cols, Wq, Wk, Wv, Wo, 4, 0.12, 0.55);
  assert(rv.A[i0 * rv.m + sameCol] > rv.A[i0 * rv.m + sameRow],
         "縦書き設定では上下の隣を強く見る (α,β を入れ替えた効き)");
}

/* ═══════════════ 6. 注意ロールアウト ═══════════════ */
console.log("\n── 6. 注意ロールアウト ──");
{
  const m = 4;
  const A = new Float64Array(m * m);
  for (let i = 0; i < m; i++){
    let s = 0;
    for (let j = 0; j < m; j++){ A[i * m + j] = (i + j + 1); s += (i + j + 1); }
    for (let j = 0; j < m; j++) A[i * m + j] /= s;
  }
  const H = rolloutHat(A, m);
  let ok = true;
  for (let i = 0; i < m; i++){
    let s = 0;
    for (let j = 0; j < m; j++) s += H[i * m + j];
    if (Math.abs(s - 1) > 1e-12) ok = false;
    if (H[i * m + i] <= A[i * m + i]) ok = false;
  }
  assert(ok, "Â = 行正規化(½(A+I)) は確率行列で、対角 (残差経路) が強まる");

  const pg = makeHPage({});
  const ink = sauvola(pg.gray, pg.w, pg.h, {});
  const grid = patchFeatures(pg.gray, ink, pg.w, pg.h, 8);
  const enc = swinEncode(embedPatches(grid, 24, 11), grid.cols, grid.rows,
                         { heads: 4, winW: 8, layers: 3, dir: "h", seed: 11 });
  const rolls = attentionRollout(enc.attn);
  assert(rolls.length > 0 && rolls.length < enc.attn.length,
         "同じ窓分割を共有する層どうしが畳まれる (" + enc.attn.length + " 窓 → " + rolls.length + " 窓)");
  let rok = true;
  for (let r = 0; r < rolls.length; r++){
    const R = rolls[r].R, mm = rolls[r].m;
    for (let i = 0; i < mm; i++){
      let s = 0;
      for (let j = 0; j < mm; j++) s += R[i * mm + j];
      if (Math.abs(s - 1) > 1e-8) rok = false;
    }
  }
  assert(rok, "ロールアウト後も各行は確率分布のまま (区分対角行列の積)");
  assert(enc.tokens.length === grid.n && enc.tokens[0].length === 24, "エンコーダはトークンの形を保つ");
}

/* ═══════════════ 7. 連結成分 = 文字の固まり ═══════════════ */
console.log("\n── 7. 連結成分 (二段組を二つに分ける) ──");
{
  const pg = makeHPage({ cols: 2 });
  const ink = sauvola(pg.gray, pg.w, pg.h, {});
  const grid = patchFeatures(pg.gray, ink, pg.w, pg.h, 8);
  const enc = swinEncode(embedPatches(grid, 24, 11), grid.cols, grid.rows,
                         { heads: 4, winW: 8, layers: 3, dir: "h", seed: 11 });
  const bl = blocksFromAttention(grid, attentionRollout(enc.attn), { tau: 1.3, dir: "h" });
  assert(bl.attnEdges > 0, "注意が辺を張っている (" + bl.attnEdges + " 本)");
  assert(bl.rlsaEdges > 0, "RLSA も辺を張っている (" + bl.rlsaEdges + " 本)");
  const big = bl.comps.slice().sort(function(a, b){ return b.patches.length - a.patches.length; });
  assert(big.length >= 2, "二段組から 2 つ以上の成分が出る (" + big.length + " 個)");
  const c1 = big[0], c2 = big[1];
  const sep = (c1.x0 > c2.x1) || (c2.x0 > c1.x1);
  assert(sep, "上位 2 成分は横に離れている = ノドを跨いで繋いでいない");
}

/* ═══════════════ 8. 行分割と固まり分割 ═══════════════ */
console.log("\n── 8. 行と文字の固まり ──");
{
  const pg = makeHPage({ lines: 5 });
  const ink = sauvola(pg.gray, pg.w, pg.h, {});
  const box = { x: 30, y: 50, w: pg.w - 60, h: 200 };
  const sl = splitLines(ink, pg.w, pg.h, box, "h", {});
  assert(sl.lines.length === 5, "5 行の版面から 5 行を切り出す (得られた行数 " + sl.lines.length + ")");
  assert(sl.pitch > 8 && sl.pitch < 30, "行の太さ (字の大きさ) の推定が妥当: " + sl.pitch.toFixed(1));
  const ch = splitChunks(ink, pg.w, pg.h, sl.lines[0], "h", sl.pitch, { spanChars: 4 });
  assert(ch.length >= 3, "空白のない行も字送りで固まりに割る (" + ch.length + " 個)");
  let monotone = true;
  for (let i = 1; i < ch.length; i++) if (ch[i].x < ch[i - 1].x) monotone = false;
  assert(monotone, "固まりは行に沿って左から右へ並ぶ");
  const covered = ch[ch.length - 1].x + ch[ch.length - 1].w - ch[0].x;
  assert(covered > 300, "行の端から端までが固まりで覆われる (" + Math.round(covered) + " px)");

  /* 語間の空白がある版面 (欧文) では空白で切れること */
  const w = 300, h = 40;
  const g = new Float64Array(w * h).fill(1);
  for (let word = 0; word < 4; word++)
    for (let c = 0; c < 3; c++)
      putChar(g, w, h, 10 + word * 70 + c * 16, 12, 12, 14);
  const ink2 = sauvola(g, w, h, { win: 25 });
  const l2 = { x: 0, y: 8, w: w, h: 24 };
  const ch2 = splitChunks(ink2, w, h, l2, "h", 14, { spanChars: 8 });
  assert(ch2.length === 4, "空白で分かれた 4 語を 4 つの固まりにする (" + ch2.length + " 個)");

  /* 縦書きの行 (= 列) は右から左 */
  const vp = makeVPage({ ncols: 4 });
  const vink = sauvola(vp.gray, vp.w, vp.h, {});
  const vbox = { x: 20, y: 40, w: vp.w - 40, h: vp.h - 80 };
  const vl = splitLines(vink, vp.w, vp.h, vbox, "v", {});
  assert(vl.lines.length === 4, "縦書き 4 列を 4 本の行として切る (" + vl.lines.length + ")");
  assert(vl.lines[0].x > vl.lines[vl.lines.length - 1].x, "縦書きの行は右から左へ並ぶ");
}

/* ═══════════════ 9. XY-cut の読み順 ═══════════════ */
console.log("\n── 9. 読み順 (XY-cut) ──");
{
  const items = [
    { box: { x: 200, y: 0, w: 100, h: 100 }, id: "右上" },
    { box: { x: 0, y: 0, w: 100, h: 100 }, id: "左上" },
    { box: { x: 0, y: 200, w: 300, h: 80 }, id: "下段" }
  ];
  const h = xyCut(items, "h").map(function(o){ return o.id; });
  assert(h[0] === "左上" && h[1] === "右上" && h[2] === "下段", "横書き: 左上 → 右上 → 下段 (" + h.join(" → ") + ")");
  const v = xyCut(items, "v").map(function(o){ return o.id; });
  assert(v[0] === "右上" && v[1] === "左上", "縦書き: 右の段が先 (" + v.join(" → ") + ")");
  const one = xyCut([items[0]], "h");
  assert(one.length === 1, "1 個でも落ちない");

  const chunks = [];
  for (let i = 0; i < 7; i++) chunks.push({ x: i * 10, y: 0, w: 8, h: 10, chars: 2, line: 0, block: 0 });
  chunks.push({ x: 0, y: 20, w: 8, h: 10, chars: 2, line: 1, block: 0 });
  const gs = groupChunks(chunks, 3);
  assert(gs.length === 4, "7 個の固まりを 3 個ずつ束ねると 3+3+1、行が変われば別ブロック (" + gs.length + " 個)");
  assert(gs[0].chars === 6 && gs[3].line === 1, "束ねたブロックの字数と行が引き継がれる");
  assert(gs[0].w >= 28, "束ねたブロックは固まりを包む矩形になる");
}

/* ═══════════════ 10. analyzePage 総体 ═══════════════ */
console.log("\n── 10. 版面解析の総体 ──");
{
  const pg = makeHPage({ lines: 6 });
  const a = analyzePage(pg.gray, pg.w, pg.h, { patch: 8, winW: 8, layers: 3, heads: 4, tau: 1.3, perBlock: 3 });
  assert(a.dir === "h", "横書きと判定");
  assert(a.meta.blocks >= 1, "ブロックが取れる (" + a.meta.blocks + ")");
  assert(a.meta.lines >= 5 && a.meta.lines <= 8, "行数が版面と合う (" + a.meta.lines + " 行 / 実際 6 行)");
  assert(a.meta.chunks > a.meta.lines * 2, "行より多くの固まりに割れている (" + a.meta.chunks + ")");
  assert(a.meta.readBlocks > 0 && a.meta.readBlocks <= a.meta.chunks, "速読ブロックは固まりを束ねたもの");
  let inRange = true;
  ["chunk", "line", "block"].forEach(function(k){
    a.units[k].forEach(function(u){
      if (!(u.x >= -1e-9 && u.y >= -1e-9 && u.x + u.w <= 1 + 1e-6 && u.y + u.h <= 1 + 1e-6)) inRange = false;
      if (!(u.w > 0 && u.h > 0)) inRange = false;
    });
  });
  assert(inRange, "全単位の座標が 0..1 の正規化座標に収まる (どの表示寸法にも載る)");
  let downward = true;
  const L = a.units.line;
  for (let i = 1; i < L.length; i++) if (L[i].block === L[i - 1].block && L[i].y < L[i - 1].y - 1e-6) downward = false;
  assert(downward, "横書きの行は上から下へ並ぶ");
  assert(a.meta.chars > 50, "推定字数が取れる (" + a.meta.chars + " 字)");
  assert(a.meta.ms >= 0 && a.meta.patches > 100, "解析の計量が返る (" + a.meta.patches + " パッチ / " + a.meta.ms + " ms)");

  /* 同じ入力は同じ結果 (決定論) */
  const a2 = analyzePage(pg.gray, pg.w, pg.h, { patch: 8, winW: 8, layers: 3, heads: 4, tau: 1.3, perBlock: 3 });
  assert(a2.meta.chunks === a.meta.chunks && a2.meta.blocks === a.meta.blocks,
         "同じ頁を二度解析しても同じ版面になる");

  /* 縦書き頁 */
  const vp = makeVPage({ ncols: 6 });
  const av = analyzePage(vp.gray, vp.w, vp.h, { patch: 8, winW: 8, layers: 3, heads: 4, tau: 1.3, perBlock: 3 });
  assert(av.dir === "v", "縦書きと判定");
  const VL = av.units.line;
  let rightFirst = true;
  for (let i = 1; i < VL.length; i++) if (VL[i].block === VL[i - 1].block && VL[i].x > VL[i - 1].x + 1e-6) rightFirst = false;
  assert(rightFirst, "縦書きの読み順は右の列から左へ");
  let vTall = 0;
  av.units.chunk.forEach(function(u){ if (u.h > u.w) vTall++; });
  assert(vTall > av.units.chunk.length * 0.5, "縦書きの固まりは縦長 (" + vTall + "/" + av.units.chunk.length + ")");

  /* 白紙 */
  const blank = new Float64Array(200 * 200).fill(0.97);
  const ab = analyzePage(blank, 200, 200, { patch: 8 });
  assert(ab.units.chunk.length === 0 || ab.meta.inkRatio < 0.02, "白紙からは固まりが出ない (誤検出しない)");
}

/* ═══════════════ 11. 日本語チャンカ ═══════════════ */
console.log("\n── 11. 日本語チャンカ ──");
{
  const t = "速読とは、字を速く見る技術ではない。視点を送る順番を先に知っている状態のことである。";
  const cs = textChunks(t, {});
  assert(cs.length > 5, "文が複数の固まりに割れる (" + cs.length + " 個)");
  assert(cs.map(function(c){ return c.text; }).join("") === normalizeText(t), "切っても字は一字も消えない (連結すれば元に戻る)");
  let noEmpty = true;
  cs.forEach(function(c){ if (!c.text.length) noEmpty = false; });
  assert(noEmpty, "空の固まりを作らない");
  assert(cs[0].show === "速読とは、", "自立語+付属語+句読点で切れる: " + cs[0].show);
  const en = textChunks("I propose with God pressure in Hotel levin.", {});
  assert(en.length >= 6, "欧文は語境界で切れる (" + en.length + " 個)");
  assert(en.map(function(c){ return c.text; }).join("") === "I propose with God pressure in Hotel levin.", "欧文も連結で元に戻る");
  const longOne = textChunks("あああああああああああああああああああ", { maxLen: 6 });
  assert(longOne.length === 4, "切れ目のない列も最大長で強制的に割る (" + longOne.length + " 個)");
  assert(charClass("漢") === "kanji" && charClass("あ") === "hira" && charClass("ア") === "kata" &&
         charClass("a") === "latin" && charClass("、") === "punct", "文字種の判定");

  const gs = groupTextChunks(cs, 3);
  assert(gs.length === Math.ceil(cs.length / 3) || gs.length <= cs.length, "固まりを 3 個ずつ束ねる (" + gs.length + " ブロック)");
  let cover = 0;
  gs.forEach(function(b){ cover += (b.to - b.from + 1); });
  assert(cover === cs.length, "束ね直しても固まりは過不足なく全部使われる");
  assert(orpIndex("あ") === 0 && orpIndex("速読とは") === 1 && orpIndex("速読とはこういうものだ") === 3,
         "最適認識点は語長とともに右へずれる");
}

/* ═══════════════ 12. LaTeX 剥がしと語中シャッフル ═══════════════ */
console.log("\n── 12. 論文 (.tex) の取り込みと耐性訓練 ──");
{
  const tex = [
    "\\documentclass{jsarticle}", "\\usepackage{amsmath}", "% これはコメント",
    "\\begin{document}", "\\title{瞬読の理論}",
    "本文の一行目である。\\textbf{強調}も本文として残る。",
    "\\begin{equation} E = mc^2 \\end{equation}",
    "数式 $\\alpha + \\beta$ は記号に置き換わる。",
    "\\end{document}", "この後ろは捨てられる。"
  ].join("\n");
  const out = stripLatex(tex);
  assert(!/documentclass|usepackage/.test(out), "前文 (preamble) が落ちる");
  assert(!/これはコメント/.test(out), "コメントが落ちる");
  assert(!/この後ろは捨てられる/.test(out), "\\end{document} の後ろが落ちる");
  assert(/本文の一行目である/.test(out), "本文は残る");
  assert(/強調/.test(out), "\\textbf の中身は本文として残る");
  assert(/〈式〉/.test(out) && !/mc\^2/.test(out), "数式環境は 〈式〉 に畳まれる");
  assert(!/\\/.test(out), "命令の残骸がない");

  const rng = srand(3);
  const s = "abcdefgh";
  const sc = scrambleInner(s, rng);
  assert(sc[0] === "a" && sc[sc.length - 1] === "h" && sc.length === s.length, "語中シャッフルは先頭と末尾を動かさない");
  assert(sc.split("").sort().join("") === s.split("").sort().join(""), "字は増えも減りもしない");
  assert(scrambleInner("ab", rng) === "ab", "3 字以下はそのまま");
}

/* ═══════════════ 13. 速読スケジューラ ═══════════════ */
console.log("\n── 13. 滞留時間のスケジュール ──");
{
  const units = [];
  for (let i = 0; i < 40; i++) units.push({ chars: 6, show: "あいうえおか" });
  const sc = buildSchedule(units, { cpm: 1200, minMs: 10, ramp: 0, punctExtra: 0 });
  near(sc.effCpm, 1200, 1, "目標 1200 字/分 がそのまま実効速度になる");
  near(sc.totalMs, 40 * 6 / 1200 * 60000, 1, "総所要時間 = 字数 / 速度");
  let mono = true;
  for (let i = 1; i < sc.steps.length; i++) if (sc.steps[i].t <= sc.steps[i - 1].t) mono = false;
  assert(mono, "開始時刻は単調増加");

  const fast = buildSchedule(units, { cpm: 100000, minMs: 90, ramp: 0, punctExtra: 0 });
  let floored = true;
  fast.steps.forEach(function(s){ if (Math.abs(s.ms - 90) > 1e-9) floored = false; });
  assert(floored, "どれだけ速度を上げても最短滞留 (視覚の下限) を割らない");

  const ramped = buildSchedule(units, { cpm: 1200, minMs: 10, ramp: 50, punctExtra: 0 });
  assert(ramped.totalMs < sc.totalMs, "漸増を効かせると同じ量が短時間で終わる");
  assert(ramped.steps[39].ms < ramped.steps[0].ms, "後半ほど滞留が短くなる (速度が上がっている)");

  const punct = buildSchedule([{ chars: 4, show: "ですが、" }, { chars: 4, show: "つぎに" }],
                              { cpm: 600, minMs: 1, ramp: 0, punctExtra: 0.2 });
  assert(punct.steps[0].ms > punct.steps[1].ms, "句読点では少し長く留まる");

  let ok = true;
  for (let t = 0; t < sc.totalMs; t += 37){
    let lin = 0;
    for (let i = 0; i < sc.steps.length; i++) if (sc.steps[i].t <= t) lin = i;
    if (stepAt(sc, t) !== lin) ok = false;
  }
  assert(ok, "経過時刻から現在の単位を引く二分探索が総当たりと一致する");
  assert(stepAt(sc, -100) === 0 && stepAt(sc, 1e9) === sc.steps.length - 1, "範囲外でも端に張り付く");
  assert(stepAt({ steps: [] }, 0) === -1, "空のスケジュールでも落ちない");
}

/* ═══════════════ 14. 対象者プロファイル ═══════════════ */
console.log("\n── 14. 対象者プロファイル ──");
{
  const p = profileFrom({ cpm: 600, span: 6, reg: 15, goal: 3 });
  assert(p.net === 510, "逆行 15% を差し引いた実効読速 (" + p.net + " 字/分)");
  assert(p.target === 1530, "目標 3 倍 = " + p.target + " 字/分");
  assert(p.perBlock >= 1 && p.perBlock <= 8, "1 ブロックの固まり数が範囲内 (" + p.perBlock + ")");
  assert(p.minMs >= 40 && p.minMs <= 400, "最短滞留が生理的な範囲 (" + p.minMs + " ms)");
  const slow = profileFrom({ cpm: 600, span: 6, reg: 40, goal: 3 });
  assert(slow.target < p.target && /逆行/.test(slow.note), "逆行が多い対象者には目標を下げ、警告を出す");
  const hard = profileFrom({ cpm: 600, span: 6, reg: 0, goal: 8 });
  assert(hard.ramp === 20 && /漸増/.test(hard.note), "高い目標には漸増を勧める");
  near(loadIndex(12, 6), 2, 1e-12, "視野負荷 = ブロックの字数 / 視野幅");

  const st = sessionStats(buildSchedule([{ chars: 6 }, { chars: 6 }], { cpm: 600, minMs: 1, ramp: 0 }), 6);
  assert(st.units === 2 && st.chars === 12 && st.cpm === 600, "セッション成績の集計");
  assert(st.load === 1, "1 ブロック 6 字 / 視野幅 6 字 = 負荷 1.0 (ちょうど見切れる)");
}

/* ═════════ 合成した読み手のフレーム ═════════ */
/* 明るい壁を背景に、肌色の楕円 (顔) と、その上半分に二つの暗い楕円 (目)。
   瞳の左右のずれ・目の開き具合・顔の位置を引数で動かせる。 */
function makeFaceFrame(w, h, o){
  o = o || {};
  const cx = o.cx === undefined ? w / 2 : o.cx;
  const cy = o.cy === undefined ? h / 2 : o.cy;
  const rx = o.rx || Math.round(w * 0.25), ry = o.ry || Math.round(h * 0.38);
  const pupil = o.pupil || 0;              /* 瞳の水平ずれ (画素) */
  const lid = o.lid === undefined ? 4 : o.lid;   /* 目の縦半径。小さいほど閉じている */
  const rgba = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++){
    for (let x = 0; x < w; x++){
      const p = (y * w + x) * 4;
      let r = 200, g = 205, b = 215;                     /* 明るい壁 (肌色ではない) */
      const dx = (x - cx) / rx, dy = (y - cy) / ry;
      if (dx * dx + dy * dy <= 1){ r = 222; g = 178; b = 148; }   /* 肌 */
      rgba[p] = r; rgba[p + 1] = g; rgba[p + 2] = b; rgba[p + 3] = 255;
    }
  }
  if (!o.noEyes){
    const ey = cy - ry * 0.25;
    [-1, 1].forEach(function(sgn){
      const ex = cx + sgn * rx * 0.45 + pupil;
      for (let y = Math.round(ey - lid); y <= Math.round(ey + lid); y++){
        for (let x = Math.round(ex - 7); x <= Math.round(ex + 7); x++){
          if (x < 0 || y < 0 || x >= w || y >= h) continue;
          const u = (x - ex) / 7, v = (y - ey) / Math.max(1, lid);
          if (u * u + v * v > 1) continue;
          const p = (y * w + x) * 4;
          rgba[p] = 25; rgba[p + 1] = 22; rgba[p + 2] = 20;
        }
      }
    });
  }
  return rgba;
}

/* ═══════════════ 15. 読み手の取り込み ═══════════════ */
console.log("\n── 15. 読み手 (対象者) の取り込み ──");
{
  const w = 160, h = 120;
  const frame = makeFaceFrame(w, h, {});
  const skin = skinMask(frame, w, h);
  let sk = 0;
  for (let i = 0; i < skin.length; i++) sk += skin[i];
  assert(sk > w * h * 0.10 && sk < w * h * 0.45, "肌色規則が顔だけを拾う (" + (sk / (w * h) * 100).toFixed(1) + "%)");
  assert(skin[2 * w + 2] === 0, "背景の壁は肌色ではない");
  assert(skin[(h / 2 | 0) * w + (w / 2 | 0)] === 1, "顔の中心は肌色");

  const r = analyzeReaderFrame(frame, w, h, {});
  assert(r.face !== null, "顔が一つの連結成分として掴まれる");
  const fcx = r.face.x + r.face.w / 2, fcy = r.face.y + r.face.h / 2;
  assert(Math.abs(fcx - w / 2) < 14 && Math.abs(fcy - h / 2) < 14,
         "顔の中心が合っている (" + Math.round(fcx) + "," + Math.round(fcy) + " / 期待 80,60)");
  assert(r.face.w > 50 && r.face.w < 110, "顔の幅が妥当 (" + r.face.w + " px)");
  assert(r.eyes !== null, "目が二つ見つかる");
  assert(r.eyes.left.cx < fcx && r.eyes.right.cx > fcx, "目は顔の中心の左右に分かれている");
  assert(r.eyes.left.cy < fcy && r.eyes.right.cy < fcy, "目は顔の上半分にある");
  assert(r.meta.patches > 100 && r.meta.windows > 0, "パッチと窓が立っている (" + r.meta.patches + " パッチ / " + r.meta.windows + " 窓)");

  /* 瞳を右へずらすと視線指標が右へ動く */
  const right = analyzeReaderFrame(makeFaceFrame(w, h, { pupil: 9 }), w, h, {});
  const left = analyzeReaderFrame(makeFaceFrame(w, h, { pupil: -9 }), w, h, {});
  assert(right.gaze.pupilX > left.gaze.pupilX, "瞳のずれが視線指標に出る (" +
         right.gaze.pupilX.toFixed(3) + " > " + left.gaze.pupilX.toFixed(3) + ")");
  assert(right.gaze.x > left.gaze.x, "総合の視線指標も同じ向きに動く");

  /* 顔ごと右へ寄せると頭の偏りが出る */
  const moved = analyzeReaderFrame(makeFaceFrame(w, h, { cx: w / 2 + 22 }), w, h, {});
  assert(moved.gaze.headX > r.gaze.headX + 0.1, "顔の位置が頭の偏りとして出る");

  /* 前面カメラは左右が逆 — 読み進む向きに合わせて符号が反転する */
  assert(Math.abs(right.gaze.readX + right.gaze.x) < 1e-12, "前面カメラでは readX = −x");
  const back = gazeFrom(r.face, r.eyes, w, h, { front: false });
  assert(Math.abs(back.readX - back.x) < 1e-12, "背面カメラでは readX = x");

  /* 瞬き — 目が縦につぶれると開き具合が落ちる */
  const blink = analyzeReaderFrame(makeFaceFrame(w, h, { lid: 1 }), w, h, {});
  assert(blink.eyes !== null && blink.eyes.openness < r.eyes.openness,
         "閉じた目は開き具合が下がる (" + blink.eyes.openness.toFixed(2) + " < " + r.eyes.openness.toFixed(2) + ")");
  assert(r.eyes.openness > 0.45 && blink.eyes.openness < 0.45,
         "開閉が瞬きの閾値 0.45 をまたぐ");

  /* 顔がないフレーム */
  const empty = new Uint8ClampedArray(w * h * 4);
  for (let i = 0; i < w * h; i++){ empty[i * 4] = 200; empty[i * 4 + 1] = 205; empty[i * 4 + 2] = 215; empty[i * 4 + 3] = 255; }
  const none = analyzeReaderFrame(empty, w, h, {});
  assert(none.face === null && none.gaze === null, "顔のないフレームでは何も掴まず、落ちない");

  /* 動き — 前フレームを渡すと差分が効く */
  const g0 = analyzeReaderFrame(frame, w, h, {});
  const g1 = analyzeReaderFrame(makeFaceFrame(w, h, { cx: w / 2 + 10 }), w, h, { prevGray: g0.gray });
  assert(g1.motion > 0 && g0.motion === 0, "前フレームとの差が動きとして出る (" + g1.motion.toFixed(4) + ")");
  const feats = readerPatchFeatures(g0.gray, skinMask(frame, w, h), motionMap(g0.gray, null), w, h, 8);
  assert(feats.F === 10 && feats.feat.length === feats.n * 10, "読み手のパッチは 10 次元");
  assert(feats.dens[Math.floor(feats.rows / 2) * feats.cols + Math.floor(feats.cols / 2)] > 0.9,
         "顔の中心のパッチは肌色密度がほぼ 1");
}

/* ═══════════════ 16. 視線の追跡 ═══════════════ */
console.log("\n── 16. 視線の追跡 (停留 / サッカード / 逆行 / 瞬き) ──");
{
  /* 横書き: 右へ 4 回進み、1 回だけ左へ戻る */
  const tr = trackerNew({ dir: "h", sacThr: 0.10 });
  const xs = [-0.6, -0.3, 0.0, 0.3, -0.2, 0.1];
  for (let i = 0; i < xs.length; i++)
    trackerPush(tr, { t: i * 250, x: xs[i], y: 0, open: 1, chars: 6, target: xs[i] });
  const st = trackerStats(tr);
  assert(st.saccades === 5, "跳んだ回数 = 5 (" + st.saccades + ")");
  assert(st.regressions === 1, "左へ戻ったのは 1 回 = 逆行 1 (" + st.regressions + ")");
  assert(st.regRate === 20, "逆行率 20% (" + st.regRate + "%)");
  assert(st.fixations === 5 && st.meanFixMs === 250, "停留 5 回・中央値 250 ms");
  assert(st.span === 7.2, "測れた視野幅 = 字数/停留 = 36/5 = 7.2 (" + st.span + ")");
  assert(st.fixPerMin > 0, "1 分あたりの停留数が出る (" + st.fixPerMin + ")");

  /* 微動だけなら跳んだことにしない */
  const tr2 = trackerNew({ dir: "h" });
  for (let i = 0; i < 10; i++) trackerPush(tr2, { t: i * 100, x: 0.01 * (i % 2), y: 0, open: 1 });
  assert(trackerStats(tr2).saccades === 0, "閾値以下の揺れはサッカードに数えない");

  /* 縦書き: 下へ進むのが順、上へ戻るか右の列へ跳ぶのが逆行 */
  const tv = trackerNew({ dir: "v", sacThr: 0.10 });
  const pts = [[0, -0.5], [0, -0.2], [0, 0.2], [0, -0.1], [0.4, 0.0]];
  for (let i = 0; i < pts.length; i++)
    trackerPush(tv, { t: i * 200, x: pts[i][0], y: pts[i][1], open: 1 });
  const sv = trackerStats(tv);
  assert(sv.regressions === 2, "縦書きでは上へ戻る跳びと右の列へ戻る跳びが逆行 (" + sv.regressions + ")");

  /* 瞬き */
  const tb = trackerNew({});
  const opens = [1, 1, 0.2, 0.2, 1, 1, 0.1, 1];
  for (let i = 0; i < opens.length; i++)
    trackerPush(tb, { t: i * 120, x: 0, y: 0, open: opens[i] });
  assert(trackerStats(tb).blinks === 2, "閉じている連続は 1 回と数える (" + trackerStats(tb).blinks + " 回)");

  /* 追従率 — 照らしている所と視線が合っているか */
  const tsame = trackerNew({});
  const tfar = trackerNew({});
  for (let i = 0; i < 5; i++){
    trackerPush(tsame, { t: i * 200, x: -0.5 + i * 0.25, y: 0, open: 1, target: -0.5 + i * 0.25 });
    trackerPush(tfar, { t: i * 200, x: -1, y: 0, open: 1, target: 1 });
  }
  assert(trackerStats(tsame).sync === 100, "視線が照らした所に乗っていれば追従率 100%");
  assert(trackerStats(tfar).sync === 0, "正反対を見ていれば追従率 0%");

  /* 顔を見失ったフレーム */
  const tl = trackerNew({});
  trackerPush(tl, { t: 0, x: 0, y: 0, open: 1 });
  trackerPush(tl, { t: 100, x: null, y: null });
  assert(trackerStats(tl).lost === 1, "顔を見失ったフレームは lost として数え、跳びには数えない");
  assert(trackerStats(tl).saccades === 0, "見失いでサッカードを誤検出しない");
}

console.log("");
console.log(checks + " 項目を検査。");
if (failures){ console.error("FAILURES: " + failures); process.exit(1); }
console.log("すべて通過 — Bada 瞬読 のエンジンは、頁の画像から固まりと読み順を復元し、時間に載せられる。");
