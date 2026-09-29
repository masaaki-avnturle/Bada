/*
 * chat.js — ContactGPT 対話エンジン
 *
 * 1 つの質問に対して
 *   ① 方程式 ID の直接参照 (例: "UFO.19")
 *   ② 設計パラメータの即答 (Γ, φ, Z(φ), Jones, 寸法, 反重力 …) — physics.js で再計算
 *   ③ 数式電卓 ("計算 Z(11.7722)", "= gamma(0.5)^2")
 *   ④ 方程式レジストリ 2111 本の全文検索 (文字 bigram BM25 + タグ)
 *   ⑤ 小型 GPT (gpt.js) による生成
 * を組み合わせて回答します。
 */
(function (root) {
  "use strict";
  const Phys = root.CTPhys || (typeof require !== "undefined" ? require("./physics.js") : null);
  const GPTmod = root.ContactGPT || (typeof require !== "undefined" ? require("./gpt.js") : null);

  // ------------------------------------------------------------ 検索
  const TAG_WORDS = {
    ROT: ["回転", "コマ", "rot", "複素回転", "オイラー", "sin", "cos"],
    SR: ["相対論", "ローレンツ", "光速", "sr", "時間の遅れ"],
    GAMMA: ["ガンマ", "gamma", "Γ"],
    ZETA: ["ゼータ", "zeta", "ζ", "リーマン", "riemann"],
    BETA: ["ベータ", "beta", "β"],
    JONES: ["jones", "ジョーンズ", "結び目", "knot"],
    MANIFOLD: ["多様体", "manifold", "計量", "リッチ", "ricci"],
    QUANTUM: ["量子", "quantum", "波動", "ψ"],
    TRANSPORT: ["輸送", "transport", "ufo", "反重力", "推進"],
    ENTROPY: ["エントロピー", "entropy", "情報", "x log x"],
  };
  // 日本語キーワード → 方程式中の記号による検索語の拡張
  const EXPAND = {
    "反重力": "UFO ag cosh(x log x) E_ag", "ufo": "UFO", "上昇": "UFO altitude a = (L − 1)", "浮上": "UFO L =",
    "ゼータ": "ζ(s) Z(", "ガンマ": "Γ(γ) Γ'", "ベータ": "β(p,q)", "ジョーンズ": "Jones V(t)", "結び目": "Jones 3_1",
    "多様体": "g_ij R_ij ds²", "相対論": "mc² √(1−(v/c)²)", "エントロピー": "x log x H(", "量子": "ψ iℏ HΨ",
    "回転": "e^{iθ} cos θ sin θ", "微分": "d/d", "積分": "∫",
  };
  function expand(q) {
    let x = q; const ql = q.toLowerCase();
    for (const [k, v] of Object.entries(EXPAND)) if (ql.includes(k)) x += " " + v;
    return x;
  }
  function grams(s) {
    s = s.toLowerCase().replace(/\s+/g, " ");
    const g = [], a = Array.from(s), kana = (c) => /[\u3040-\u309f、。？！?!]/.test(c);
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== " " && !kana(a[i])) g.push(a[i]);
      if (i + 1 < a.length && a[i] !== " " && a[i + 1] !== " " && !(kana(a[i]) && kana(a[i + 1]))) g.push(a[i] + a[i + 1]);
    }
    return g;
  }
  class Index {
    constructor(eqs) {
      this.eqs = eqs; this.df = new Map(); this.docs = [];
      let tot = 0;
      for (const e of eqs) {
        const tj = e.tags.map((t) => (GPTmod.TAG_JA[t] || t)).join(" ");
        const g = grams(`${e.id} ${e.expr} ${e.tags.join(" ")} ${tj}`), tf = new Map();
        for (const x of g) tf.set(x, (tf.get(x) || 0) + 1);
        for (const x of tf.keys()) this.df.set(x, (this.df.get(x) || 0) + 1);
        this.docs.push({ tf, len: g.length }); tot += g.length;
      }
      this.avg = tot / eqs.length;
    }
    tagsIn(q) {
      const ql = q.toLowerCase();
      return Object.keys(TAG_WORDS).filter((t) => TAG_WORDS[t].some((w) => ql.includes(w.toLowerCase())));
    }
    search(q, n, filter) {
      const qg = Array.from(new Set(grams(expand(q)))), N = this.eqs.length, k1 = 1.4, b = 0.7;
      const ql = q.toLowerCase(), boostTags = new Set();
      for (const [t, ws] of Object.entries(TAG_WORDS)) if (ws.some((w) => ql.includes(w.toLowerCase()))) boostTags.add(t);
      const res = [];
      this.docs.forEach((d, i) => {
        const e = this.eqs[i];
        if (filter && !filter(e)) return;
        let s = 0;
        for (const g of qg) {
          const f = d.tf.get(g); if (!f) continue;
          const idf = Math.log(1 + (N - this.df.get(g) + 0.5) / (this.df.get(g) + 0.5));
          s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * d.len / this.avg));
        }
        for (const t of e.tags) if (boostTags.has(t)) s += 4;
        if (s > 0) res.push([s, e]);
      });
      res.sort((a, b2) => b2[0] - a[0]);
      return res.slice(0, n || 5).map((r) => r[1]);
    }
  }

  // ------------------------------------------------------------ 電卓 (安全な再帰下降パーサ)
  const FUNCS = {
    sin: Math.sin, cos: Math.cos, tan: Math.tan, exp: Math.exp, log: Math.log, ln: Math.log, log10: Math.log10,
    sqrt: Math.sqrt, abs: Math.abs, sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh, asin: Math.asin, acos: Math.acos,
    atan: Math.atan, acosh: Math.acosh, asinh: Math.asinh, floor: Math.floor, ceil: Math.ceil,
    gamma: (x) => Phys.gammaR(x), lgamma: (x) => Phys.lgammaR(x), beta: (p, q) => Phys.betaR(p, q),
    zeta: (s, t) => { const z = Phys.zeta(Phys.C(s, t || 0)); return t ? Phys.cabs(z) : z.re; },
    Z: (t) => Phys.rsZ(t), theta: (t) => Phys.rsTheta(t), xlogx: (x) => x * Math.log(x),
    L: (h) => Phys.ufo.L(h || 0), max: Math.max, min: Math.min, pow: Math.pow,
    jones31: (a) => Phys.cabs(Phys.jonesEval("3_1", Phys.cexp(Phys.C(0, a)))),
    jones41: (a) => Phys.cabs(Phys.jonesEval("4_1", Phys.cexp(Phys.C(0, a)))),
    jones51: (a) => Phys.cabs(Phys.jonesEval("5_1", Phys.cexp(Phys.C(0, a)))),
  };
  const CONSTS = { pi: Math.PI, "π": Math.PI, e: Math.E, "γ": 0.5772156649015329, c: 299792458, G: 6.674e-11, g: 9.80665,
    "Γ": 64800, "φ": Math.acosh(64800), phi: Math.acosh(64800) };
  function calc(src) {
    const s = src.replace(/×/g, "*").replace(/÷/g, "/").replace(/−/g, "-").replace(/²/g, "^2").replace(/³/g, "^3").replace(/√/g, "sqrt");
    let i = 0;
    const peek = () => { while (s[i] === " ") i++; return s[i]; };
    const expect = (c) => { if (peek() !== c) throw new Error(`'${c}' が必要です (位置 ${i})`); i++; };
    function expr() { let v = term(); for (;;) { const c = peek(); if (c === "+") { i++; v += term(); } else if (c === "-") { i++; v -= term(); } else return v; } }
    function term() { let v = unary(); for (;;) { const c = peek(); if (c === "*") { i++; v *= unary(); } else if (c === "/") { i++; v /= unary(); } else return v; } }
    function unary() { const c = peek(); if (c === "-") { i++; return -unary(); } if (c === "+") { i++; return unary(); } return power(); }
    function power() { const b = atom(); if (peek() === "^") { i++; return Math.pow(b, unary()); } return b; }
    function atom() {
      const c = peek();
      if (c === "(") { i++; const v = expr(); expect(")"); return v; }
      const num = /^(\d+\.?\d*|\.\d+)(e[+-]?\d+)?/i.exec(s.slice(i));
      if (num) { i += num[0].length; return parseFloat(num[0]); }
      const id = /^[A-Za-zπγΓφ_][A-Za-z0-9_]*/.exec(s.slice(i));
      if (id) {
        i += id[0].length; const name = id[0];
        if (peek() === "(") {
          i++; const args = [];
          if (peek() !== ")") { args.push(expr()); while (peek() === ",") { i++; args.push(expr()); } }
          expect(")");
          const f = FUNCS[name]; if (!f) throw new Error(`未知の関数 ${name}`);
          return f.apply(null, args);
        }
        if (name in CONSTS) return CONSTS[name];
        throw new Error(`未知の記号 ${name}`);
      }
      throw new Error(`解釈できません: "${s.slice(i, i + 8)}"`);
    }
    const v = expr();
    if (peek() !== undefined) throw new Error(`余分な入力: "${s.slice(i)}"`);
    return v;
  }

  // ------------------------------------------------------------ 即答
  function paramAnswer(q, bp) {
    const f = (v, p) => (+v.toPrecision(p || 6)).toString();
    const ql = q.toLowerCase(), has = (...ws) => ws.some((w) => ql.includes(w.toLowerCase()));
    const out = [];
    if (has("ローレンツ", "Γ", "gamma factor", "18 時間", "18時間", "1 秒", "1秒"))
      out.push(`**特殊相対論**: Γ = 18 h / 1 s = ${bp.Gamma}、1 − β = ${bp.oneMinusBeta.toExponential(5)}、ラピディティ φ = arcosh Γ = ${f(bp.phi)}`);
    if (has("ラピディティ", "φ", "phi", "複素回転", "Θ", "コマ"))
      out.push(`**複素回転体**: Θ = θ + iφ = ${f(bp.Theta.re)} + ${f(bp.phi)}i (θ₀ = π/6)`);
    if (has("計量", "ds²", "ds2", "T|ψ|", "輸送計量"))
      out.push(`**輸送計量**: ds² = e^{−2πT|ψ|}[η + h̄h̄]dx^μdx^ν + T²dψ²、e^{−2πT|ψ|} = 1/Γ → T|ψ| = ${f(bp.TPsi)} (x log x = 1 の根 ${f(bp.xlogxRoot)})`);
    if (has("ベガ", "vega", "片道", "距離"))
      out.push(`**航程**: ${bp.opts.targetName} ${bp.opts.targetLy} ly → 収縮距離 ${bp.distKm.toExponential(3)} km、搭乗者の片道 ${f(bp.oneWayH, 5)} h`);
    if (has("ジンバル", "角速度", "ω", "omega"))
      out.push(`**ジンバル**: ω(外, 中, 内) = ${bp.omega.map((w) => f(w)).join(", ")} rad/s (段間比 φ/π = ${f(bp.phi / Math.PI)})`);
    if (has("歳差", "Ω", "precession"))
      out.push(`**ポッド歳差**: Ω = Mgl/(I₃ω₃) = ${f(bp.Omega)} rad/s (M = ${bp.opts.podMass} kg, l = ${bp.armL} m, I₃ = 2/5·Mr²)`);
    if (has("リーマン", "riemann", "シーゲル", "siegel", "θ(φ)", "z(φ)", "ゼータ", "zeta", "ζ"))
      out.push(`**Γ・ζ 多様体**: Riemann–Siegel θ(φ) = ${f(bp.rsTheta)}、Z(φ) = e^{iθ(φ)} ζ(½ + iφ) = ${f(bp.Z)}`);
    if (has("jones", "ジョーンズ", "結び目", "コイル", "共鳴"))
      for (const k of Object.keys(bp.jones)) {
        const J = bp.jones[k];
        out.push(`**Jones ${k}**: V = ${J.poly}、V(t*) = ${J.str} (|V| = ${f(J.mag, 5)})、共鳴角 α = ${J.resonance.map((r) => r.alpha + "°").join(", ")}`);
      }
    if (has("寸法", "半径", "外環", "中環", "内環", "塔", "井戸", "ポッド", "サイズ", "大きさ"))
      out.push(`**部品寸法 [m]**: 外環 R ${bp.dims.ringOuter} / 中環 R ${bp.dims.ringMid} / 内環 R ${bp.dims.ringInner} / 管径 ${bp.dims.tube} / ポッド r ${bp.dims.podR} / 塔高 ${bp.dims.tower} / 井戸 ${bp.dims.well} / Jones 3_1 R ${bp.dims.coil31}, 5_1 R ${bp.dims.coil51}`);
    if (has("扉", "cern", "衝突", "door", "消えた"))
      out.push(`**衝突段**: √s = ${bp.opts.sqrtS_TeV} TeV、E_T^miss = ${bp.opts.METGeV} GeV、扉の軸 n̂ = (${bp.doorAxis.map((v) => f(v, 5)).join(", ")})`);
    if (has("ufo", "反重力", "上昇", "浮上", "anti"))  {
      const tr = Phys.ufo.ascend(10, 1).pop();
      out.push(`**UFO 反重力モデル**: x = 1 + r₀/r、L = cosh(x log x) = ${f(Phys.ufo.L(0), 5)} (地表)、a = (L − 1)·g_eff = ${f(Phys.ufo.accel(0), 5)} m/s²、10 s 後 高度 ${f(tr.h, 5)} m・速度 ${f(tr.v, 5)} m/s`);
    }
    if (has("何本", "統計", "件数", "レジストリ"))
      out.push("**方程式レジストリ**: 全 2111 本 (論文 15 本)。数値評価 632 本 = calc 220 + 成立 231 + 不成立 181、記号式 1479 本");
    return out;
  }

  // ------------------------------------------------------------ 対話
  class Chat {
    constructor(equations, model, bp) {
      this.eqs = equations; this.byId = new Map(equations.map((e) => [e.id.toUpperCase(), e]));
      this.index = new Index(equations); this.model = model; this.bp = bp || Phys.blueprint();
    }
    ask(q, opts) {
      opts = Object.assign({ generate: true, temperature: 0.6, maxNew: 140 }, opts || {});
      const res = { answer: [], refs: [], calc: null, gen: null, error: null };
      const text = q.trim();
      if (!text) return res;
      // ③ 電卓
      const cm = /^(?:計算|calc|=)\s*[:：]?\s*(.+)$/i.exec(text);
      if (cm) {
        try { const v = calc(cm[1]); res.calc = { expr: cm[1], value: v }; res.answer.push(`${cm[1]} = **${+v.toPrecision(12)}**`); }
        catch (e) { res.error = e.message; }
        return res;
      }
      // ① ID
      const ids = text.toUpperCase().match(/[A-Z][A-Z0-9_]*\.\d+/g) || [];
      for (const id of ids) { const e = this.byId.get(id); if (e) res.refs.push(e); }
      // ② 即答
      res.answer.push(...paramAnswer(text, this.bp));
      // ④ 検索
      if (!ids.length) {
        const tagOnly = /(の式|一覧|を見せ|list)/.test(text), tags = this.index.tagsIn(text);
        const filter = tagOnly && tags.length ? (e) => e.tags.some((t) => tags.includes(t)) : null;
        res.refs.push(...this.index.search(text, tagOnly ? 8 : 4, filter));
      }
      // ⑤ 生成
      if (opts.generate && this.model) {
        const prompt = `Q: ${ids[0] ? ids[0] + " は？" : text}\nA:`;
        res.gen = this.model.generate(prompt, { temperature: opts.temperature, maxNew: opts.maxNew, topK: 10, stop: "\nQ:", seed: opts.seed }).trim();
      }
      if (!res.answer.length && !res.refs.length) res.answer.push("レジストリに一致する式は見つかりませんでした。ID (例: UFO.19)、キーワード (ゼータ, 反重力, Jones …)、または「計算 Z(11.77)」のように入力してください。");
      return res;
    }
  }

  const api = { Chat, Index, calc, paramAnswer, FUNCS };
  root.CTChat = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
