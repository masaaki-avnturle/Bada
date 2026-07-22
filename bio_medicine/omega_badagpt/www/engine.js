/* ============================================================================
 *  engine.js — BadaGPT ζ-Entropy 未知事前予知エンジン (ζ-Entropy A-priori Engine)
 *  ---------------------------------------------------------------------------
 *  山口フレームワーク / Bada v3 の作用素環に基づく言語生成コア。
 *  リーマンゼータ関数から導かれる「ゼータ分布」P(n)=n^-s/ζ(s) のエントロピー
 *      H(s) = s * (-ζ'(s)/ζ(s)) + log ζ(s)
 *  を「未知事前予知(a-priori prediction)」の温度・重みとして用い、
 *  投稿テキスト(PDF/ソースコード)から次トークンを π-softmax で生成する。
 *
 *  数式的中核はすべて実在の解析数論:
 *      β(p,q) = Γ(p)Γ(q)/Γ(p+q)                     (ベータ関数)
 *      ζ(s)   = Σ_{n≥1} n^-s        (s>1)            (ゼータ関数)
 *      ζ(s)   = β(p,q)/log x                         (Bada 中核演算子, README)
 *      ζ(s) - 1/(s-1) → γ = 0.5772156649...  (s→1)  (オイラー・マスケローニ)
 *  これらを Bada 言語の作用素 <- / -< / >- として写像する。
 *
 *  ⚠ 概念シミュレーション/研究アート。実在の予言・医療・投資助言ではありません。
 * ==========================================================================*/
"use strict";

const Bada = (() => {
  const GAMMA = 0.5772156649015328606; // Euler–Mascheroni γ

  // --- Γ(x) : Lanczos 近似 -------------------------------------------------
  const G = [
    676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7
  ];
  function gamma(z) {
    if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gamma(1 - z));
    z -= 1;
    let x = 0.99999999999980993;
    for (let i = 0; i < G.length; i++) x += G[i] / (z + i + 1);
    const t = z + G.length - 0.5;
    return Math.sqrt(2 * Math.PI) * Math.pow(t, z + 0.5) * Math.exp(-t) * x;
  }
  // --- ベータ関数 β(p,q) = Γ(p)Γ(q)/Γ(p+q) --------------------------------
  function beta(p, q) { return (gamma(p) * gamma(q)) / gamma(p + q); }

  // --- リーマンゼータ ζ(s) (s>1, オイラー–マクローリン補正) ----------------
  function zeta(s, N = 64) {
    if (s === 1) return Infinity;
    let sum = 0;
    for (let n = 1; n < N; n++) sum += Math.pow(n, -s);
    // 末尾補正 ∫ + オイラー–マクローリン
    const t = Math.pow(N, 1 - s);
    sum += t / (s - 1) + 0.5 * Math.pow(N, -s);
    sum += (s / 12) * Math.pow(N, -s - 1);
    return sum;
  }
  // --- ζ'(s) 数値微分 ------------------------------------------------------
  function zetaPrime(s) {
    const h = 1e-4;
    return (zeta(s + h) - zeta(s - h)) / (2 * h);
  }
  // --- ゼータ分布のシャノンエントロピー -----------------------------------
  //     H(s) = s * (-ζ'(s)/ζ(s)) + log ζ(s)     [nat]
  function zetaEntropy(s) {
    const z = zeta(s);
    return s * (-zetaPrime(s) / z) + Math.log(z);
  }
  // --- Bada 中核演算子 ζ(s) = β(p,q)/log x (README v3) --------------------
  function badaCoreOperator(p, q, x) {
    return beta(p, q) / Math.log(Math.max(x, Math.E));
  }

  // ------------------------------------------------------------------------
  //  決定論的擬似乱数 (シードは投稿テキストのハッシュ) — 再現可能な予知
  // ------------------------------------------------------------------------
  function hashSeed(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ------------------------------------------------------------------------
  //  トークン化 (語 + 記号) — 多言語対応 (日本語は文字 n-gram にフォールバック)
  // ------------------------------------------------------------------------
  function tokenize(text) {
    const toks = text.match(/[A-Za-z0-9_]+|[^\sA-Za-z0-9_]/g) || [];
    // 日本語などマルチバイトが多い場合は 2-gram で補強
    return toks;
  }

  // ------------------------------------------------------------------------
  //  未知事前予知エンジン本体
  //    1) 投稿テキストから n-gram マルコフ連鎖を構築
  //    2) ζ-エントロピーを温度 τ に写像 (π-softmax)
  //    3) β(p,q)/log x で語の事前確率(a-priori)を重み付け
  //    4) 決定論的サンプリングで「未知の続き」を生成
  // ------------------------------------------------------------------------
  function buildModel(corpus) {
    const toks = tokenize(corpus);
    const uni = new Map();
    const bi = new Map();   // prev -> Map(next -> count)
    for (let i = 0; i < toks.length; i++) {
      uni.set(toks[i], (uni.get(toks[i]) || 0) + 1);
      if (i > 0) {
        const p = toks[i - 1];
        if (!bi.has(p)) bi.set(p, new Map());
        const m = bi.get(p);
        m.set(toks[i], (m.get(toks[i]) || 0) + 1);
      }
    }
    return { toks, uni, bi, size: toks.length };
  }

  // π-softmax : Bada の非可換 π(χ,x) 作用素を模した温度付き softmax
  function piSoftmax(weights, tau, rnd) {
    const keys = Object.keys(weights);
    if (!keys.length) return null;
    let max = -Infinity;
    for (const k of keys) if (weights[k] > max) max = weights[k];
    let sum = 0; const exp = {};
    for (const k of keys) { exp[k] = Math.exp((weights[k] - max) / tau); sum += exp[k]; }
    let r = rnd() * sum;
    for (const k of keys) { r -= exp[k]; if (r <= 0) return k; }
    return keys[keys.length - 1];
  }

  // s パラメータ(1<s≤3)を、投稿の情報量に応じて選ぶ
  function chooseS(model) {
    const V = model.uni.size, N = Math.max(model.size, 1);
    // 語彙が豊か → s を 1 に近づけ (高エントロピー・高創発)
    const ratio = Math.min(1, V / N);
    return 1.15 + 1.6 * (1 - ratio); // s ∈ (1.15, 2.75)
  }

  function generate(corpus, prompt, opts = {}) {
    const maxTokens = opts.maxTokens || 220;
    const model = buildModel(corpus + "\n" + prompt);
    if (model.size < 2) {
      return {
        text: "(投稿テキストが不足しています / insufficient corpus)",
        telemetry: null
      };
    }
    const s = opts.s || chooseS(model);
    const H = zetaEntropy(s);          // nat
    const Z = zeta(s);
    const tau = Math.max(0.35, Math.min(1.8, H / 1.6)); // ζ-エントロピー→温度
    const seed = hashSeed(prompt + "::" + s.toFixed(4));
    const rnd = mulberry32(seed);

    // シード語: プロンプト末尾の語、なければコーパス先頭
    const ptoks = tokenize(prompt);
    let cur = ptoks.length ? ptoks[ptoks.length - 1] : model.toks[0];
    const out = [];
    for (let i = 0; i < maxTokens; i++) {
      const nexts = model.bi.get(cur);
      let weights;
      if (nexts && nexts.size) {
        weights = {};
        let x = 2;
        for (const [w, c] of nexts) {
          // a-priori 重み: 頻度 × Bada中核演算子 β(p,q)/log x
          const prior = badaCoreOperator(1 + (c % 5), 1 + (w.length % 7), x + w.length);
          weights[w] = Math.log(1 + c) + prior;
          x += 1;
        }
      } else {
        // バックオフ: ユニグラムから ζ-重み付け
        weights = {};
        let rank = 1;
        for (const [w, c] of model.uni) {
          weights[w] = Math.log(1 + c) * Math.pow(rank, -1 / s); // Zipf/ゼータ
          if (++rank > 40) break;
        }
      }
      const nxt = piSoftmax(weights, tau, rnd);
      if (!nxt) break;
      out.push(nxt);
      cur = nxt;
    }

    // 記号結合の整形
    let text = "";
    for (let i = 0; i < out.length; i++) {
      const w = out[i];
      const isPunct = /^[^\sA-Za-z0-9_]$/.test(w);
      if (i > 0 && !isPunct && !/^[([{]$/.test(out[i - 1])) text += " ";
      text += w;
    }

    return {
      text: text.trim(),
      telemetry: {
        s: +s.toFixed(4),
        zeta: +Z.toFixed(6),
        entropy_nat: +H.toFixed(6),
        entropy_bit: +(H / Math.LN2).toFixed(6),
        temperature: +tau.toFixed(4),
        gamma: GAMMA,
        vocab: model.uni.size,
        corpusTokens: model.size,
        seed
      }
    };
  }

  return {
    gamma, beta, zeta, zetaPrime, zetaEntropy, badaCoreOperator,
    buildModel, generate, tokenize, hashSeed, GAMMA
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = Bada;
