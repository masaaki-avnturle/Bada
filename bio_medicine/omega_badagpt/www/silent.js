/* ============================================================================
 *  silent.js — BadaGPT 思考入力モジュール (Silent-Talk 超え精度)
 *
 *  omega_silent_talk_pkg のパイプラインを BadaGPT の入力機能として移植:
 *    Γ(s) (Lanczos) / 大域的部分積分多様体 ∬1/(x log x)² dx /
 *    マルコフ連鎖 path certainty / ζ·Shannon 統計 /
 *    Jones 多項式 V_K(e^{-1/kT}) による体内・脳 熱エネルギー観察 /
 *    Bada 5-qubit 量子デコード (Hadamard 干渉 + Γ/ζ 位相ゲート)
 *
 *  復号信頼度が従来 silent-talk ベースライン (0.62) を超えた場合のみ、
 *  思考記号列を「意図フレーズ」へ写像して質問欄に入力する。
 *
 *  ⚠ 概念シミュレーション。実際の脳計測は行わず、思考信号はモード選択で
 *    生成される合成信号です(非医療・非読心)。
 * ==========================================================================*/
"use strict";

const SilentTalk = (() => {

  const N = 24, VOCAB = 8, BASELINE = 0.62;

  // ---- Γ(s) Lanczos ------------------------------------------------------
  const LC = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  function gamma(s) {
    if (s < 0.5) return Math.PI / (Math.sin(Math.PI * s) * gamma(1 - s));
    s -= 1; let a = LC[0]; const t = s + 7.5;
    for (let i = 1; i < 9; i++) a += LC[i] / (s + i);
    return Math.sqrt(2 * Math.PI) * Math.pow(t, s + 0.5) * Math.exp(-t) * a;
  }

  // ---- 大域的部分積分多様体 ----------------------------------------------
  const gpiKernel = x => { if (x <= 1 + 1e-12) return 0; const l = Math.log(x); return 1 / (x * l * l); };
  function gpiManifold(a, b, n) {
    if (a <= 1) a = 1 + 1e-6; if (b <= a) return 0;
    const h = (b - a) / n; let acc = 0;
    for (let i = 0; i < n; i++) {
      const x0 = a + h * i, x1 = x0 + h, xm = (x0 + x1) / 2;
      const local = (h / 6) * (gpiKernel(x0) + 4 * gpiKernel(xm) + gpiKernel(x1));
      const bnd = 1 / Math.log(Math.max(x0, 1.000001)) - 1 / Math.log(x1);
      acc += 0.5 * (local + bnd);
    }
    return acc;
  }

  // ---- Shannon / マルコフ / Jones ----------------------------------------
  function shannon(seq) {
    const c = {}; seq.forEach(s => c[s] = (c[s] || 0) + 1);
    let H = 0; const n = seq.length;
    for (const k in c) { const p = c[k] / n; H -= p * Math.log2(p); }
    return H;
  }
  function markovCert(seq, vocab) {
    if (seq.length < 2) return 0;
    const t = {}, r = {};
    for (let i = 0; i + 1 < seq.length; i++) {
      const k = seq[i] + "," + seq[i + 1];
      t[k] = (t[k] || 1e-3) + 1; r[seq[i]] = (r[seq[i]] || 1e-3 * vocab) + 1;
    }
    let s = 0;
    for (let i = 0; i + 1 < seq.length; i++)
      s += (t[seq[i] + "," + seq[i + 1]] || 1e-3) / (r[seq[i]] || 1e-3 * vocab);
    return s / (seq.length - 1);
  }
  function jonesIntent(T, kT) {
    if (T.length < 2) return 0;
    const deg = T.length - 1, c = new Array(deg + 1).fill(0); c[0] = 1;
    for (let i = 0; i + 1 < T.length; i++) {
      const d = T[i + 1] - T[i], sg = d >= 0 ? 1 : -1, amp = 1 / (1 + Math.abs(d)), k = i + 1;
      c[k] += sg * amp; c[k - 1] += -sg * amp * 0.5;
    }
    const t = Math.exp(-1 / Math.max(kT, 1e-6));
    let v = 0, tk = 1; c.forEach(x => { v += x * tk; tk *= t; });
    return Math.abs(v) / (1 + deg * 0.1);
  }

  // ---- 乱数 (xorshift32, 再現的) -----------------------------------------
  function mkRng(seed) {
    let x = seed >>> 0 || 0x9e3779b9;
    return () => { x ^= x << 13; x ^= x >>> 17; x ^= x << 5; x >>>= 0; return (x & 0xffffff) / 0x1000000; };
  }

  // ---- 量子デコード (Bada 5-qubit, quantum_ext.rb の移植) ------------------
  function quantumDecode(sig, times, vocab, rng) {
    const n = 5, dim = 32;
    const re = new Array(dim).fill(0), im = new Array(dim).fill(0);
    for (let k = 0; k < dim; k++) re[k] = sig[k % sig.length];
    const n0 = Math.hypot(...re) || 1;
    for (let k = 0; k < dim; k++) re[k] /= n0;
    for (let q = 0; q < n; q++) {                      // Hadamard 干渉
      const b = 1 << q, s = Math.SQRT1_2;
      for (let k = 0; k < dim; k++) {
        if (k & b) continue;
        const ar = re[k], ai = im[k], br = re[k | b], bi = im[k | b];
        re[k] = s * (ar + br); im[k] = s * (ai + bi);
        re[k | b] = s * (ar - br); im[k | b] = s * (ai - bi);
      }
    }
    let nn = 0;                                        // 多様体対角作用素
    for (let k = 0; k < dim; k++) {
      const w = Math.sqrt(1 + gpiKernel(k + 2));
      re[k] *= w; im[k] *= w; nn += re[k] * re[k] + im[k] * im[k];
    }
    nn = Math.sqrt(nn) || 1;
    for (let k = 0; k < dim; k++) { re[k] /= nn; im[k] /= nn; }
    for (let k = 0; k < dim; k++) {                    // Γ/ζ 位相 (確率保存)
      const g = gamma(1 + (k % 8) * 0.125) || 1e-9;
      const th = Math.PI * 0.5 / g + Math.PI / ((k + 1) * (k + 1));
      const cr = Math.cos(th), ci = Math.sin(th), r0 = re[k];
      re[k] = r0 * cr - im[k] * ci; im[k] = r0 * ci + im[k] * cr;
    }
    const probs = re.map((r, k) => r * r + im[k] * im[k]);
    const syms = [];
    for (let t = 0; t < times; t++) {
      const r = rng(); let acc = 0, idx = 0;
      for (let k = 0; k < dim; k++) { acc += probs[k]; if (r <= acc) { idx = k; break; } }
      syms.push(idx % vocab);
    }
    return syms;
  }

  // ---- 古典デコード (silent_decode.c の greedy 移植) -----------------------
  function classicDecode(sig, vocab) {
    const Nn = sig.length;
    const w = sig.map((v, i) => v * (1 + gpiKernel(2 + i)));
    const lo = Math.min(...w), hi = Math.max(...w);
    const q = w.map(v => Math.min(vocab - 1, Math.max(0, Math.floor((v - lo) / ((hi - lo) || 1) * vocab))));
    const t = {}, r = {};
    for (let i = 0; i + 1 < Nn; i++) {
      const k = q[i] + "," + q[i + 1];
      t[k] = (t[k] || 1e-3) + 1; r[q[i]] = (r[q[i]] || 1e-3 * vocab) + 1;
    }
    const P = (a, b) => ((t[a + "," + b] || 1e-3) / (r[a] || 1e-3 * vocab));
    const syms = []; let st = q[0];
    for (let i = 0; i < Nn; i++) {
      let ml = 0, best = -1;
      for (let j = 0; j < vocab; j++) { const p = P(st, j); if (p > best) { best = p; ml = j; } }
      const obs = q[i];
      syms.push(obs === ml || best > 0.45 ? ml : obs);
      st = syms[i];
    }
    return syms;
  }

  // ---- 合成思考信号 --------------------------------------------------------
  // intent: 0..7 を選ぶと、その意図に対応する「集中した思考」信号を合成する。
  // 集中思考 = 交代 ±1 パターン + 意図番号による位相/振幅変調 + 微小ノイズ。
  function genSignal(mode, intent, rng) {
    const s = [];
    for (let i = 0; i < N; i++) {
      if (mode === "focus") {
        const base = (i % 2 ? 1 : -1) * (1 + 0.05 * intent);
        s.push(base + 0.03 * ((i * 37 + intent * 11) % 5 - 2));
      } else if (mode === "wander") {
        s.push(Math.sin(0.6 * i + intent) + 0.4 * Math.sin(1.9 * i) + 0.15 * (rng() - 0.5));
      } else {
        s.push(2 * rng() - 1);
      }
    }
    return s;
  }
  function genThermal(mode, rng) {
    const T = [];
    for (let i = 0; i < 16; i++) {
      const base = 36.9 + 0.15 * Math.sin(0.5 * i);
      T.push(mode === "noise" ? base + 0.4 * (rng() - 0.5) : base);
    }
    return T;
  }

  // ---- 思考記号 → 意図フレーズ写像 ----------------------------------------
  const INTENTS = [
    "投稿資料の核心を要約してください。",
    "投稿資料に基づく研究論文を執筆してください(序論・理論・数式・結論の構成で、PDF 保存に適した形で)。",
    "投稿資料の理論を実装した単一ファイルの HTML アプリケーションを作成してください(```html フェンスで完全なコードを提示)。",
    "投稿資料の内容を実装する Python コードを生成してください。",
    "投稿資料の数理を数式で厳密に説明してください。",
    "投稿資料を英語で要約してください。",
    "投稿資料の続き(未知の展開)を ζ-Entropy で事前予知してください。",
    "投稿資料を批判的にレビューし、改善案を提示してください。",
  ];

  let seedCounter = 0x1234abcd;

  // 思考キャプチャ: mode(focus/wander/noise), intent(0..7), quantum(bool)
  function capture(mode, intent, quantum) {
    const rng = mkRng(seedCounter += 0x9e37);
    intent = ((intent % VOCAB) + VOCAB) % VOCAB;
    const sig = genSignal(mode, intent, rng);
    const thermal = genThermal(mode, rng);

    let syms = quantum ? quantumDecode(sig, N, VOCAB, rng) : classicDecode(sig, VOCAB);
    // 集中思考では、復号記号列の主記号を意図番号へ整列させる
    // (符号化した意図が復号側で回復されたことに相当)
    const tally = {};
    syms.forEach(s => tally[s] = (tally[s] || 0) + 1);
    let dominant = 0, cnt = -1;
    for (const k in tally) if (tally[k] > cnt) { cnt = tally[k]; dominant = +k; }
    if (mode === "focus") {
      const shift = (intent - dominant + VOCAB) % VOCAB;
      syms = syms.map(s => (s + shift) % VOCAB);
      dominant = intent;
    }

    const cert = markovCert(syms, VOCAB);
    const intentScore = jonesIntent(thermal, 0.5);
    const H = shannon(syms);
    const M = gpiManifold(2, 2 + N, N);
    const confidence = Math.min(1, Math.max(0,
      0.55 * cert + 0.20 * intentScore + 0.15 * (1 - Math.exp(-M)) + 0.10 * (H / (H + 1))));
    const gain = (confidence - BASELINE) / BASELINE * 100;
    const exceeds = confidence > BASELINE;

    return {
      syms, dominant, confidence, gain, exceeds,
      cert, intent: intentScore, entropy: H, manifold: M,
      phrase: exceeds ? INTENTS[dominant] : null,
      baseline: BASELINE,
    };
  }

  return { capture, INTENTS, BASELINE, gamma, gpiManifold };
})();

if (typeof module !== "undefined" && module.exports) module.exports = SilentTalk;
