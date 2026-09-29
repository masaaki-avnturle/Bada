/*
 * chat.js — 方程式レジストリ 2111 本の全文検索エンジン (文字 bigram BM25 + タグ + 日本語キーワード展開)
 *
 * ContactGPT の対話ロジックは Bada プログラム bada/apps/contactgpt.bada にあり、
 * そこから組込み関数 eq_search / eq_tags としてこの検索エンジンを呼び出します。
 */
(function (root) {
  "use strict";
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

  const api = { Index, TAG_WORDS };
  root.CTChat = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
