/*
 * badaxp.js — Bada XP のローカル分派の中核 (bada_ruby/mobile/www/index.html の移植)
 *
 *   Ξ = β(H+1, M+1) / log(N+1)      H = シャノンのエントロピー (bit)、M = 多様体線素 1/(x log x)² で重み付けした積分、N = トークン数
 *   localReply     質問のエントロピーに近い理論文を 3 つ選ぶ
 *   localEquation  質問のエントロピーに最も近い式を 1 つ選ぶ
 *   summarize / keywords   頻度にもとづく抜粋と頻出語
 * 理論文と式の選び方は「エントロピーの値が近いもの」であり、質問の意味を理解して答えるものではない。
 * Bada XP 本体にある言語モデルへの接続は、ここには含めていない。
 */
(function (global) {
  "use strict";
  var LANCZOS_G = 7, LANCZOS_C = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  function gamma(x) {
    if (x === 0) return Infinity;
    if (x < 0.5) return Math.PI / (Math.sin(Math.PI * x) * gamma(1 - x));
    x -= 1; var a = LANCZOS_C[0], t = x + LANCZOS_G + 0.5;
    for (var i = 1; i < LANCZOS_G + 2; i++) a += LANCZOS_C[i] / (x + i);
    return Math.sqrt(2 * Math.PI) * Math.pow(t, x + 0.5) * Math.exp(-t) * a;
  }
  var logGamma = function (x) { return Math.log(Math.abs(gamma(x))); };
  var beta = function (p, q) { return Math.exp(logGamma(p) + logGamma(q) - logGamma(p + q)); };
  function zetaGauge(p, q, x) { var lx = Math.log(x); return Math.abs(lx) < 1e-15 ? Infinity : beta(p, q) / lx; }
  function xLogX(x) { return x <= 0 ? 0 : x * Math.log(x); }
  var TOKEN_RE = /[A-Za-z0-9_]+|[一-鿿぀-ゟ゠-ヿ]/g;
  var tokenize = function (s) { return String(s).match(TOKEN_RE) || []; };
  function shannon(tokens) {
    if (!tokens.length) return 0;
    var f = {}, n = tokens.length, h = 0, k; tokens.forEach(function (t) { f[t] = (f[t] || 0) + 1; });
    for (k in f) { var p = f[k] / n; h -= p * Math.log2(p); }
    return h;
  }
  function distribution(tokens) {
    var f = {}, n = tokens.length; tokens.forEach(function (t) { f[t] = (f[t] || 0) + 1; });
    return Object.keys(f).map(function (t) { return [t, f[t] / n]; }).sort(function (a, b) { return b[1] - a[1]; });
  }
  function manifoldElement(x) { if (x <= 1) return 1; var xl = xLogX(x); return Math.abs(xl) < 1e-9 ? 1 : 1 / (xl * xl); }
  function integral(dist) { return dist.reduce(function (s, e, i) { return s + e[1] * manifoldElement(i + 2); }, 0); }
  function xi(text) { var tk = tokenize(text); return zetaGauge(shannon(tk) + 1, integral(distribution(tk)) + 1, tk.length + 1); }
  var ofEntropy = function (s) { return shannon(tokenize(s)); };

  var THEORY = [
    "大域的部分積分多様体 M 上で、エントロピー不変量 Ξ は複素回転体 e^{iθ} の下で保存される。",
    "ガンマ関数 Γ(γ) の部分積分により β(p,q) が現れ、これが ζ(s)=x·log x のゲージを与える。",
    "シャノンのエントロピー H を多様体線素 1/(x·log x)² で重み付け積分すると不変量 Ξ を得る。",
    "特殊相対性理論のコマ幾何の可積分系がエラーを修正し、Ξ を閉軌道 ∮ 上で安定化させる。",
    "未知エンジンは質問のエントロピー値 H_q を多様体不変量 Ξ_q に写し、近傍の知識を生成する。"
  ];
  var EQUATIONS = [
    "ζ(s) = β(p,q)/log x = x·log x", "β(p,q) = Γ(p)Γ(q)/Γ(p+q)",
    "∬ 1/(x·log x)² dx_m = π(χ,x)∇ d∇", "□ = 2(sin(ix·log x) + cos(ix·log x))",
    "∮ e^{-□} d□ = π e,  e^π ≅ π^e", "H = -Σ p·log₂ p,  Ξ = β(H+1, M+1)/log(N+1)",
    "⊕(iℏ∇)^⊕L = e^{-x·log x}", "Γ′(γ) dx_m = T,  ζ(s) e^{-f} dV = β(p,q)/log x"
  ];
  var nearest = function (list, target) { return list.slice().sort(function (a, b) { return Math.abs(ofEntropy(a) - target) - Math.abs(ofEntropy(b) - target); }); };
  function localReply(question) { return nearest(THEORY, ofEntropy(question)).slice(0, 3).join(" ") + " (Ξ=" + xi(question).toFixed(4) + ")"; }
  function localEquation(question) { return nearest(EQUATIONS, ofEntropy(question))[0]; }
  function splitSentences(t) { return t.split(/[。．.!?！？\n]+/).map(function (x) { return x.trim(); }).filter(function (x) { return x.length > 1; }); }
  function summarize(text, k) {
    k = k || 3;
    var sents = splitSentences(text); if (sents.length <= k) return text.trim();
    var freq = {}; tokenize(text).forEach(function (w) { freq[w] = (freq[w] || 0) + 1; });
    var scored = sents.map(function (sen, idx) { var tk = tokenize(sen); return { sen: sen, idx: idx, sc: tk.reduce(function (a, w) { return a + (freq[w] || 0); }, 0) / (tk.length || 1) }; });
    return scored.slice().sort(function (a, b) { return b.sc - a.sc; }).slice(0, k).sort(function (a, b) { return a.idx - b.idx; }).map(function (x) { return x.sen; }).join("。 ") + "。";
  }
  var STOP = new Set("の に は を が と で て た し も へ や か な this that the a an of to and is in for on at it です ます する いる ある こと これ それ".split(" "));
  function keywords(text, k) {
    k = k || 8; var freq = {};
    tokenize(text).forEach(function (w) { if (!STOP.has(w)) freq[w] = (freq[w] || 0) + 1; });
    return Object.keys(freq).map(function (w) { return [w, freq[w]]; }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, k);
  }

  // 思念会議のプラグインとしての Bada XP
  var plugin = {
    id: "xp", name: "Bada XP", kind: "native", description: "各発言の不変量 Ξ とエントロピーに近い式を注記。/xp 質問 で理論文を返し、議事録に所見を加える",
    onMessage: function (m) {
      if (m.kind === "agenda" || m.kind === "agree") return null;
      return "Ξ = " + xi(m.text).toFixed(4) + " · H = " + ofEntropy(m.text).toFixed(2) + " bit · 近い式: " + localEquation(m.text);
    },
    onCommand: function (args) {
      if (!args.trim()) return "使い方: /xp 質問 — 質問のエントロピーに近い理論文と式を返します (意味を理解して答えるものではありません)。";
      return localReply(args) + "\n式: " + localEquation(args);
    },
    onMinutes: function (ctx) {
      var text = ctx.msgs.map(function (m) { return m.text; }).join("\n"); if (!text.trim()) return null;
      var agenda = ctx.msgs.length ? ctx.msgs[0].text : "";
      return ["- 議事録全体の不変量 Ξ = " + xi(text).toFixed(4) + " (H = " + ofEntropy(text).toFixed(3) + " bit、トークン " + tokenize(text).length + " 個)",
              "- 議題の不変量 Ξ = " + xi(agenda).toFixed(4) + "、エントロピーの近い式: " + localEquation(agenda),
              "", "_Ξ = β(H+1, M+1)/log(N+1)。文字の頻度の統計であり、内容の評価ではありません。式は、エントロピーの値が近いものを選んでいるだけです。_"].join("\n");
    }
  };

  global.BadaXP = { gamma: gamma, beta: beta, tokenize: tokenize, shannon: shannon, xi: xi, ofEntropy: ofEntropy, localReply: localReply, localEquation: localEquation,
                    summarize: summarize, keywords: keywords, THEORY: THEORY, EQUATIONS: EQUATIONS, plugin: plugin };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaXP;
})(typeof window !== "undefined" ? window : globalThis);
