/*
 * gpt.js — ContactGPT: ゼロから書いた小型 GPT (decoder-only Transformer)
 *
 * 外部ライブラリなし。Float32Array 上のテープ式自動微分で
 *   トークン埋め込み + 位置埋め込み
 *   → [LayerNorm → 因果的マルチヘッド自己注意 → 残差
 *      LayerNorm → MLP (GELU) → 残差] × nLayer
 *   → LayerNorm → 語彙ロジット (埋め込み行列を共有)
 * を学習 (Adam) / 推論 (温度 + top-k サンプリング) します。
 *
 * コーパスは設計図書 (contact_blueprint.pdf) の全方程式 2111 本と
 * 設計パラメータの Q&A から作ります (tools/train.js)。
 * 文字単位トークナイザなので日本語・数式記号をそのまま扱えます。
 *
 * ブラウザ (window.ContactGPT) と Node (module.exports) の両対応。
 */
(function (root) {
  "use strict";

  // ------------------------------------------------------------ RNG
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(rng) {
    let u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  // 数値型 (勾配チェック時は Float64Array に切り替え)
  let FA = Float32Array;
  const setFloat = (T) => { FA = T; };

  // ------------------------------------------------------------ tensors & tape
  class Tensor {
    constructor(rows, cols, data) {
      this.rows = rows; this.cols = cols;
      this.data = data || new FA(rows * cols);
      this.grad = null;
    }
    zeroGrad() { if (this.grad) this.grad.fill(0); else this.grad = new FA(this.data.length); }
    ensureGrad() { if (!this.grad) this.grad = new FA(this.data.length); return this.grad; }
  }

  class Tape {
    constructor(train) { this.ops = []; this.train = train; }
    push(fn) { if (this.train) this.ops.push(fn); }
    backward() { for (let i = this.ops.length - 1; i >= 0; i--) this.ops[i](); this.ops = []; }
  }

  // Y[N,out] = X[N,in] · W[in,out] + b
  function linear(tape, X, W, b) {
    const N = X.rows, I = X.cols, O = W.cols, x = X.data, w = W.data;
    const Y = new Tensor(N, O), y = Y.data;
    for (let n = 0; n < N; n++) {
      const yo = n * O, xo = n * I;
      if (b) for (let o = 0; o < O; o++) y[yo + o] = b.data[o];
      for (let i = 0; i < I; i++) {
        const xv = x[xo + i];
        if (xv === 0) continue;
        const wo = i * O;
        for (let o = 0; o < O; o++) y[yo + o] += xv * w[wo + o];
      }
    }
    tape.push(() => {
      const gy = Y.grad; if (!gy) return;
      const gx = X.ensureGrad(), gw = W.ensureGrad();
      for (let n = 0; n < N; n++) {
        const yo = n * O, xo = n * I;
        for (let i = 0; i < I; i++) {
          const wo = i * O, xv = x[xo + i];
          let s = 0;
          for (let o = 0; o < O; o++) { const g = gy[yo + o]; s += g * w[wo + o]; gw[wo + o] += xv * g; }
          gx[xo + i] += s;
        }
      }
      if (b) { const gb = b.ensureGrad(); for (let n = 0; n < N; n++) for (let o = 0; o < O; o++) gb[o] += gy[n * O + o]; }
    });
    return Y;
  }

  function add(tape, A, B) {
    const Y = new Tensor(A.rows, A.cols);
    for (let i = 0; i < Y.data.length; i++) Y.data[i] = A.data[i] + B.data[i];
    tape.push(() => {
      const g = Y.grad; if (!g) return;
      const ga = A.ensureGrad(), gb = B.ensureGrad();
      for (let i = 0; i < g.length; i++) { ga[i] += g[i]; gb[i] += g[i]; }
    });
    return Y;
  }

  function layernorm(tape, X, G, Bb) {
    const N = X.rows, D = X.cols, x = X.data;
    const Y = new Tensor(N, D), y = Y.data;
    const xhat = new FA(N * D), rstd = new FA(N);
    for (let n = 0; n < N; n++) {
      const o = n * D;
      let m = 0; for (let d = 0; d < D; d++) m += x[o + d]; m /= D;
      let v = 0; for (let d = 0; d < D; d++) { const t = x[o + d] - m; v += t * t; } v /= D;
      const r = 1 / Math.sqrt(v + 1e-5); rstd[n] = r;
      for (let d = 0; d < D; d++) { const h = (x[o + d] - m) * r; xhat[o + d] = h; y[o + d] = h * G.data[d] + Bb.data[d]; }
    }
    tape.push(() => {
      const gy = Y.grad; if (!gy) return;
      const gx = X.ensureGrad(), gg = G.ensureGrad(), gb = Bb.ensureGrad();
      for (let n = 0; n < N; n++) {
        const o = n * D;
        let s1 = 0, s2 = 0;
        for (let d = 0; d < D; d++) {
          const dh = gy[o + d] * G.data[d];
          s1 += dh; s2 += dh * xhat[o + d];
          gg[d] += gy[o + d] * xhat[o + d]; gb[d] += gy[o + d];
        }
        s1 /= D; s2 /= D;
        for (let d = 0; d < D; d++) {
          const dh = gy[o + d] * G.data[d];
          gx[o + d] += rstd[n] * (dh - s1 - xhat[o + d] * s2);
        }
      }
    });
    return Y;
  }

  const GC = Math.sqrt(2 / Math.PI);
  function gelu(tape, X) {
    const Y = new Tensor(X.rows, X.cols), x = X.data, y = Y.data;
    for (let i = 0; i < x.length; i++) {
      const v = x[i]; y[i] = 0.5 * v * (1 + Math.tanh(GC * (v + 0.044715 * v * v * v)));
    }
    tape.push(() => {
      const gy = Y.grad; if (!gy) return;
      const gx = X.ensureGrad();
      for (let i = 0; i < x.length; i++) {
        const v = x[i], u = GC * (v + 0.044715 * v * v * v), th = Math.tanh(u);
        const du = GC * (1 + 3 * 0.044715 * v * v);
        gx[i] += gy[i] * (0.5 * (1 + th) + 0.5 * v * (1 - th * th) * du);
      }
    });
    return Y;
  }

  // 因果的マルチヘッド自己注意。QKV[N=B*T, 3C] → Y[N, C]
  function attention(tape, QKV, B, T, H) {
    const C3 = QKV.cols, Cc = C3 / 3, hd = Cc / H, scale = 1 / Math.sqrt(hd), q = QKV.data;
    const Y = new Tensor(B * T, Cc), y = Y.data;
    const P = new FA(B * H * T * T);
    for (let b = 0; b < B; b++) for (let h = 0; h < H; h++) {
      const po = (b * H + h) * T * T;
      for (let t = 0; t < T; t++) {
        const qo = (b * T + t) * C3 + h * hd;
        let mx = -Infinity;
        for (let s = 0; s <= t; s++) {
          const ko = (b * T + s) * C3 + Cc + h * hd;
          let d = 0; for (let k = 0; k < hd; k++) d += q[qo + k] * q[ko + k];
          d *= scale; P[po + t * T + s] = d; if (d > mx) mx = d;
        }
        let sum = 0;
        for (let s = 0; s <= t; s++) { const e = Math.exp(P[po + t * T + s] - mx); P[po + t * T + s] = e; sum += e; }
        const yo = (b * T + t) * Cc + h * hd;
        for (let s = 0; s <= t; s++) {
          const p = P[po + t * T + s] / sum; P[po + t * T + s] = p;
          const vo = (b * T + s) * C3 + 2 * Cc + h * hd;
          for (let k = 0; k < hd; k++) y[yo + k] += p * q[vo + k];
        }
      }
    }
    tape.push(() => {
      const gy = Y.grad; if (!gy) return;
      const gq = QKV.ensureGrad();
      const dP = new FA(T);
      for (let b = 0; b < B; b++) for (let h = 0; h < H; h++) {
        const po = (b * H + h) * T * T;
        for (let t = 0; t < T; t++) {
          const yo = (b * T + t) * Cc + h * hd, qo = (b * T + t) * C3 + h * hd;
          let dot = 0;
          for (let s = 0; s <= t; s++) {
            const vo = (b * T + s) * C3 + 2 * Cc + h * hd, p = P[po + t * T + s];
            let d = 0;
            for (let k = 0; k < hd; k++) { d += gy[yo + k] * q[vo + k]; gq[vo + k] += p * gy[yo + k]; }
            dP[s] = d; dot += d * p;
          }
          for (let s = 0; s <= t; s++) {
            const dS = P[po + t * T + s] * (dP[s] - dot) * scale;
            if (dS === 0) continue;
            const ko = (b * T + s) * C3 + Cc + h * hd;
            for (let k = 0; k < hd; k++) { gq[qo + k] += dS * q[ko + k]; gq[ko + k] += dS * q[qo + k]; }
          }
        }
      }
    });
    return Y;
  }

  function embed(tape, wte, wpe, idx, B, T) {
    const D = wte.cols, X = new Tensor(B * T, D), x = X.data;
    for (let n = 0; n < B * T; n++) {
      const to = idx[n] * D, po = (n % T) * D, o = n * D;
      for (let d = 0; d < D; d++) x[o + d] = wte.data[to + d] + wpe.data[po + d];
    }
    tape.push(() => {
      const g = X.grad; if (!g) return;
      const gt = wte.ensureGrad(), gp = wpe.ensureGrad();
      for (let n = 0; n < B * T; n++) {
        const to = idx[n] * D, po = (n % T) * D, o = n * D;
        for (let d = 0; d < D; d++) { gt[to + d] += g[o + d]; gp[po + d] += g[o + d]; }
      }
    });
    return X;
  }

  // 共有埋め込みで語彙ロジットを出し、(targets があれば) 交差エントロピーまで一括計算
  function lmHead(tape, X, wte, targets, onlyLast) {
    const N = X.rows, D = X.cols, V = wte.rows, x = X.data, w = wte.data;
    const rows = onlyLast ? [N - 1] : Array.from({ length: N }, (_, i) => i);
    const logits = new FA(rows.length * V);
    rows.forEach((n, r) => {
      for (let v = 0; v < V; v++) {
        let s = 0; const wo = v * D, xo = n * D;
        for (let d = 0; d < D; d++) s += x[xo + d] * w[wo + d];
        logits[r * V + v] = s;
      }
    });
    if (!targets) return { logits };
    let loss = 0; const probs = new FA(N * V);
    for (let n = 0; n < N; n++) {
      let mx = -Infinity; for (let v = 0; v < V; v++) mx = Math.max(mx, logits[n * V + v]);
      let sum = 0; for (let v = 0; v < V; v++) { const e = Math.exp(logits[n * V + v] - mx); probs[n * V + v] = e; sum += e; }
      for (let v = 0; v < V; v++) probs[n * V + v] /= sum;
      loss -= Math.log(Math.max(probs[n * V + targets[n]], 1e-12));
    }
    loss /= N;
    tape.push(() => {
      const gx = X.ensureGrad(), gw = wte.ensureGrad();
      for (let n = 0; n < N; n++) {
        for (let v = 0; v < V; v++) {
          const g = (probs[n * V + v] - (v === targets[n] ? 1 : 0)) / N;
          if (g === 0) continue;
          const wo = v * D, xo = n * D;
          for (let d = 0; d < D; d++) { gx[xo + d] += g * w[wo + d]; gw[wo + d] += g * x[xo + d]; }
        }
      }
    });
    return { logits, loss };
  }

  // ------------------------------------------------------------ model
  class GPT {
    constructor(cfg, vocab) {
      this.cfg = Object.assign({ nLayer: 2, nHead: 4, nEmbd: 64, block: 96, seed: 1337 }, cfg || {});
      this.vocab = vocab; // 文字配列
      this.stoi = new Map(vocab.map((ch, i) => [ch, i]));
      const { nLayer, nEmbd: D, block } = this.cfg, V = vocab.length;
      const rng = mulberry32(this.cfg.seed);
      const P = (r, c, std, fill) => {
        const t = new Tensor(r, c);
        if (fill != null) t.data.fill(fill); else for (let i = 0; i < t.data.length; i++) t.data[i] = gauss(rng) * std;
        return t;
      };
      const projStd = 0.02 / Math.sqrt(2 * nLayer);
      this.params = {};
      this.params.wte = P(V, D, 0.02);
      this.params.wpe = P(block, D, 0.01);
      for (let l = 0; l < nLayer; l++) {
        Object.assign(this.params, {
          [`h${l}.ln1.g`]: P(1, D, 0, 1), [`h${l}.ln1.b`]: P(1, D, 0, 0),
          [`h${l}.attn.w`]: P(D, 3 * D, 0.02), [`h${l}.attn.b`]: P(1, 3 * D, 0, 0),
          [`h${l}.proj.w`]: P(D, D, projStd), [`h${l}.proj.b`]: P(1, D, 0, 0),
          [`h${l}.ln2.g`]: P(1, D, 0, 1), [`h${l}.ln2.b`]: P(1, D, 0, 0),
          [`h${l}.fc.w`]: P(D, 4 * D, 0.02), [`h${l}.fc.b`]: P(1, 4 * D, 0, 0),
          [`h${l}.fc2.w`]: P(4 * D, D, projStd), [`h${l}.fc2.b`]: P(1, D, 0, 0),
        });
      }
      this.params["lnf.g"] = P(1, D, 0, 1);
      this.params["lnf.b"] = P(1, D, 0, 0);
      this.step = 0;
    }
    get nParams() { return Object.values(this.params).reduce((s, t) => s + t.data.length, 0); }

    encode(str) { const u = this.stoi.get("\u0000") ?? 0; return Array.from(str).map((c) => this.stoi.has(c) ? this.stoi.get(c) : u); }
    decode(ids) { return ids.map((i) => this.vocab[i] === "\u0000" ? "" : this.vocab[i]).join(""); }

    forward(tape, idx, B, T, targets, onlyLast) {
      const p = this.params, { nLayer, nHead } = this.cfg;
      let x = embed(tape, p.wte, p.wpe, idx, B, T);
      for (let l = 0; l < nLayer; l++) {
        const h = layernorm(tape, x, p[`h${l}.ln1.g`], p[`h${l}.ln1.b`]);
        const qkv = linear(tape, h, p[`h${l}.attn.w`], p[`h${l}.attn.b`]);
        const a = attention(tape, qkv, B, T, nHead);
        x = add(tape, x, linear(tape, a, p[`h${l}.proj.w`], p[`h${l}.proj.b`]));
        const h2 = layernorm(tape, x, p[`h${l}.ln2.g`], p[`h${l}.ln2.b`]);
        const f = gelu(tape, linear(tape, h2, p[`h${l}.fc.w`], p[`h${l}.fc.b`]));
        x = add(tape, x, linear(tape, f, p[`h${l}.fc2.w`], p[`h${l}.fc2.b`]));
      }
      x = layernorm(tape, x, p["lnf.g"], p["lnf.b"]);
      return lmHead(tape, x, p.wte, targets, onlyLast);
    }

    // 1 ステップ学習。data: Int32Array のトークン列
    trainStep(data, opts) {
      opts = Object.assign({ batch: 8, lr: 3e-3, wd: 0.0, beta1: 0.9, beta2: 0.99, clip: 1.0 }, opts || {});
      const T = this.cfg.block, B = opts.batch, rng = this._rng || (this._rng = mulberry32(this.cfg.seed + 7));
      const idx = new Int32Array(B * T), tgt = new Int32Array(B * T);
      for (let b = 0; b < B; b++) {
        const s = Math.floor(rng() * (data.length - T - 1));
        for (let t = 0; t < T; t++) { idx[b * T + t] = data[s + t]; tgt[b * T + t] = data[s + t + 1]; }
      }
      for (const t of Object.values(this.params)) t.zeroGrad();
      const tape = new Tape(true);
      const { loss } = this.forward(tape, idx, B, T, tgt);
      tape.backward();
      // grad clip
      let gn = 0; for (const t of Object.values(this.params)) for (const g of t.grad) gn += g * g;
      gn = Math.sqrt(gn);
      const sc = gn > opts.clip ? opts.clip / gn : 1;
      // Adam
      this.step++;
      const b1 = opts.beta1, b2 = opts.beta2, bc1 = 1 - b1 ** this.step, bc2 = 1 - b2 ** this.step;
      for (const [name, t] of Object.entries(this.params)) {
        if (!t.m) { t.m = new FA(t.data.length); t.v = new FA(t.data.length); }
        const decay = opts.wd && name.endsWith(".w") ? opts.wd : 0;
        for (let i = 0; i < t.data.length; i++) {
          const g = t.grad[i] * sc;
          t.m[i] = b1 * t.m[i] + (1 - b1) * g;
          t.v[i] = b2 * t.v[i] + (1 - b2) * g * g;
          t.data[i] -= opts.lr * ((t.m[i] / bc1) / (Math.sqrt(t.v[i] / bc2) + 1e-8) + decay * t.data[i]);
        }
      }
      return loss;
    }

    evalLoss(data, n, seed) {
      const T = this.cfg.block, rng = mulberry32(seed || 99); let tot = 0;
      for (let k = 0; k < n; k++) {
        const s = Math.floor(rng() * (data.length - T - 1));
        const idx = Int32Array.from(data.subarray(s, s + T)), tgt = Int32Array.from(data.subarray(s + 1, s + T + 1));
        tot += this.forward(new Tape(false), idx, 1, T, tgt).loss;
      }
      return tot / n;
    }

    // 文字列 prompt に続けて生成
    generate(prompt, opts) {
      opts = Object.assign({ maxNew: 160, temperature: 0.7, topK: 12, stop: "\n\n", seed: Date.now() }, opts || {});
      const rng = mulberry32(opts.seed), T = this.cfg.block;
      let ids = this.encode(prompt);
      const out = [];
      for (let n = 0; n < opts.maxNew; n++) {
        const ctx = ids.slice(-T);
        const { logits } = this.forward(new Tape(false), Int32Array.from(ctx), 1, ctx.length, null, true);
        const V = this.vocab.length;
        const arr = Array.from(logits.subarray(0, V), (l, i) => [l / Math.max(opts.temperature, 1e-3), i]);
        arr.sort((a, b) => b[0] - a[0]);
        const top = arr.slice(0, opts.topK), mx = top[0][0];
        let sum = 0; for (const t of top) { t[0] = Math.exp(t[0] - mx); sum += t[0]; }
        let r = rng() * sum, pick = top[0][1];
        for (const t of top) { r -= t[0]; if (r <= 0) { pick = t[1]; break; } }
        ids.push(pick); out.push(pick);
        const s = this.decode(out);
        if (opts.stop && s.endsWith(opts.stop)) return s.slice(0, -opts.stop.length);
      }
      return this.decode(out);
    }

    // ------------------------------------------------ 保存 (float16 → base64)
    toJSON() {
      const names = Object.keys(this.params);
      const total = names.reduce((s, n) => s + this.params[n].data.length, 0);
      const u16 = new Uint16Array(total); let o = 0;
      for (const n of names) for (const v of this.params[n].data) u16[o++] = f32ToF16(v);
      return { format: "contactgpt-f16-v1", cfg: this.cfg, vocab: this.vocab, step: this.step,
        names, shapes: names.map((n) => [this.params[n].rows, this.params[n].cols]), weights: b64enc(new Uint8Array(u16.buffer)) };
    }
    static fromJSON(j) {
      const g = new GPT(j.cfg, j.vocab);
      const bytes = b64dec(j.weights), u16 = new Uint16Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 2);
      let o = 0;
      j.names.forEach((n) => { const t = g.params[n]; for (let i = 0; i < t.data.length; i++) t.data[i] = f16ToF32(u16[o++]); });
      g.step = j.step || 0;
      return g;
    }
  }

  // ------------------------------------------------------------ f16 / base64
  const f32b = new Float32Array(1), u32b = new Uint32Array(f32b.buffer);
  function f32ToF16(v) {
    f32b[0] = v; const x = u32b[0];
    const sign = (x >>> 16) & 0x8000; let e = ((x >>> 23) & 0xff) - 127 + 15; let m = x & 0x7fffff;
    if (e <= 0) { if (e < -10) return sign; m = (m | 0x800000) >> (1 - e); return sign | ((m + 0x1000) >> 13); }
    if (e >= 31) return sign | 0x7c00;
    const r = sign | (e << 10) | ((m + 0x1000) >> 13);
    return r;
  }
  function f16ToF32(h) {
    const s = h & 0x8000 ? -1 : 1, e = (h >> 10) & 0x1f, m = h & 0x3ff;
    if (e === 0) return s * Math.pow(2, -14) * (m / 1024);
    if (e === 31) return m ? NaN : s * Infinity;
    return s * Math.pow(2, e - 15) * (1 + m / 1024);
  }
  function b64enc(bytes) {
    if (typeof Buffer !== "undefined") return Buffer.from(bytes).toString("base64");
    let s = ""; for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }
  function b64dec(str) {
    if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(str, "base64"));
    const s = atob(str), b = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) b[i] = s.charCodeAt(i); return b;
  }

  // ------------------------------------------------------------ corpus
  // 設計図書の方程式レジストリと設計パラメータから学習テキストを作る
  const TAG_JA = {
    ROT: "複素回転体", SR: "特殊相対論", GAMMA: "ガンマ関数", ZETA: "ゼータ関数", BETA: "ベータ関数",
    JONES: "Jones 多項式", MANIFOLD: "多様体", QUANTUM: "量子", TRANSPORT: "輸送", ENTROPY: "エントロピー", OTHER: "その他",
  };
  const STATUS_JA = { symb: "記号式", calc: "数値評価", holds: "等式成立", differs: "等式不成立" };
  function buildCorpus(equations, bp) {
    const lines = [];
    for (const e of equations) {
      const tags = e.tags.map((t) => TAG_JA[t] || t).join("・");
      const val = e.value ? ` = ${e.value}` : "";
      lines.push(`Q: ${e.id} は？\nA: [${tags}] ${STATUS_JA[e.status]}: ${e.expr}${val}\n`);
    }
    if (bp) {
      const f = (v, p) => (+v.toPrecision(p || 6)).toString();
      const qa = [
        ["ローレンツ因子 Γ は？", `Γ = 18 h / 1 s = ${bp.Gamma}。地球の 1 秒が搭乗者の 18 時間。`],
        ["ラピディティ φ は？", `φ = arcosh Γ = ${f(bp.phi)}。Θ = θ + iφ の虚部になる。`],
        ["1 − β は？", `1 − β = ${bp.oneMinusBeta.toExponential(5)}`],
        ["輸送計量は？", `ds² = e^{−2πT|ψ|}[η + h̄h̄]dx^μ dx^ν + T²dψ²。e^{−2πT|ψ|} = 1/Γ より T|ψ| = ${f(bp.TPsi)}。`],
        ["ベガまでの時間は？", `ベガ 25.04 ly は収縮距離 ${bp.distKm.toExponential(3)} km、片道 ${f(bp.oneWayH, 5)} h。`],
        ["ジンバルの角速度は？", `ω(外, 中, 内) = ${bp.omega.map((w) => f(w)).join(", ")} rad/s。段間の比は φ/π。`],
        ["ポッドの歳差は？", `Ω = Mgl/(I₃ω₃) = ${f(bp.Omega)} rad/s`],
        ["Riemann–Siegel θ(φ) は？", `θ(φ) = ${f(bp.rsTheta)}`],
        ["Z(φ) は？", `Z(φ) = e^{iθ(φ)} ζ(½ + iφ) = ${f(bp.Z)}`],
        ["扉の軸は？", `n̂ = (${bp.doorAxis.map((v) => f(v, 5)).join(", ")})。CERN の衝突で粒子が消えた方向。`],
        ["外環の半径は？", `外環 R = ${bp.dims.ringOuter} m、中環 R = ${bp.dims.ringMid} m、内環 R = ${bp.dims.ringInner} m、管径 ${bp.dims.tube} m。`],
        ["塔の高さは？", `塔高 = ${bp.dims.tower} m、井戸深さ = ${bp.dims.well} m、ポッド r = ${bp.dims.podR} m。`],
        ["Jones コイルは？", `3_1 R = ${bp.dims.coil31} m、5_1 R = ${bp.dims.coil51} m、4_1 は床下。`],
        ["反重力係数 L は？", "L = cosh(x log x)、地表 x = 2 で L = 2.125。a = (L − 1)·g_eff = 11.047 m/s²。"],
        ["UFO の上昇は？", "10 ステップ後の高度 607.6 m、速度 110.46 m/s (UFO.24)。"],
      ];
      for (const k of Object.keys(bp.jones)) qa.push([`Jones ${k} は？`, `V = ${bp.jones[k].poly}、V(t*) = ${bp.jones[k].str}`]);
      for (let r = 0; r < 12; r++) for (const [q, a] of qa) lines.push(`Q: ${q}\nA: ${a}\n`);
    }
    return lines.join("\n");
  }
  function buildVocab(text) {
    const set = new Set(Array.from(text)); set.add("\u0000");
    return Array.from(set).sort();
  }

  const api = { setFloat, GPT, Tensor, Tape, buildCorpus, buildVocab, mulberry32, TAG_JA, STATUS_JA };
  root.ContactGPT = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
