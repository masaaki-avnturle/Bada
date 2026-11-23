/*
 * entropy.js — 会議の発言を測るエントロピー方程式群
 *
 * レポート "Entropy on manifold and differential of equation" (system_transport.pdf) に
 * 繰り返し現れる式を、発言 (テキスト) の統計量に対応させる。bada_claude/src/semantic.bada と同じ対応:
 *   (E1) x log x                            S(p) = −Σ p log p        発言の情報量 H / 議題とのずれ D
 *   (E2) log(x log x) ≥ 2 (y log y)^{1/2}   x = e^H, y = e^D         議事録に採る発言の門
 *   (E3) ∫∫ 1/(x log x)² dx                 p0(r) ∝ 1/((r+1)log(r+1))²  入力候補の順位の事前分布
 *   (E4) F = ∫ (∇f)² e^{−f} dm              f = 発言ごとのずれ       会議の流れの滑らかさ
 * この対応づけは本アプリの設計上の選択であり、レポートから導かれた定理ではない。
 */
(function (global) {
  "use strict";
  var STOP = new Set(["の", "は", "が", "を", "に", "で", "と", "て", "た", "し", "も", "な", "か", "です", "ます", "する", "ある", "いる", "こと", "これ", "それ", "ため", "よう", "から", "まで", "へ", "や", "ので", "the", "a", "of", "to", "and", "in", "is"]);

  // 字種の連なりで区切り、漢字の連なりは 2-gram も加える
  function tokens(text) {
    var out = [], re = /[A-Za-z][A-Za-z0-9_+#.-]*|[0-9]+(?:\.[0-9]+)?|[一-鿿々]+|[゠-ヿー]+|[぀-ゟ]+/g, m;
    while ((m = re.exec(String(text))) !== null) {
      var t = m[0].toLowerCase();
      if (/^[一-鿿々]+$/.test(t) && t.length > 2) { for (var i = 0; i + 1 < t.length; i++) out.push(t.slice(i, i + 2)); }
      else if (/^[぀-ゟ]+$/.test(t)) { if (t.length >= 3 && !STOP.has(t)) out.push(t); }
      else if (!STOP.has(t)) out.push(t);
    }
    return out;
  }
  function bag(text) {
    var tf = Object.create(null), n = 0;
    tokens(text).forEach(function (t) { tf[t] = (tf[t] || 0) + 1; n++; });
    return { tf: tf, n: n };
  }
  function density(x) { return x > 0 ? x * Math.log(x) : 0; }                 // (E1)
  function entropy(b) {
    if (!b.n) return 0;
    var h = 0; for (var t in b.tf) h -= density(b.tf[t] / b.n);
    return h;
  }
  function divergence(a, b) {                                                  // Jensen–Shannon, 0 … log 2
    if (!a.n || !b.n) return Math.LN2;
    var hm = 0, t;
    for (t in a.tf) hm -= density(0.5 * a.tf[t] / a.n + 0.5 * (b.tf[t] || 0) / b.n);
    for (t in b.tf) if (!(t in a.tf)) hm -= density(0.5 * b.tf[t] / b.n);
    return Math.max(0, hm - 0.5 * entropy(a) - 0.5 * entropy(b));
  }
  function gate(H, D) {                                                        // (E2)
    var x = Math.exp(H), y = Math.exp(D), xl = density(x);
    var lhs = xl > 0 ? Math.log(xl) : -Infinity, rhs = 2 * Math.sqrt(density(y));
    return { x: x, y: y, lhs: lhs, rhs: rhs, margin: lhs - rhs, pass: lhs >= rhs };
  }
  function kernel(r) { var d = density(r + 1); return 1 / (d * d); }           // (E3)  r = 1, 2, …
  // (E4) 発言ごとの値 f_i の勾配二乗を e^{−f_i} で重み付けした平均。小さいほど話題の飛びが少ない
  function flow(fs) {
    if (fs.length < 2) return 0;
    var num = 0, den = 0;
    for (var i = 0; i + 1 < fs.length; i++) { var w = Math.exp(-fs[i]), g = fs[i + 1] - fs[i]; num += w * g * g; den += w; }
    return num / den;
  }
  function merge(bags) {
    var tf = Object.create(null), n = 0;
    bags.forEach(function (b) { for (var t in b.tf) { tf[t] = (tf[t] || 0) + b.tf[t]; } n += b.n; });
    return { tf: tf, n: n };
  }
  // 発言を議題の文脈に照らして測る
  function measure(text, context) {
    var b = bag(text), H = entropy(b), D = divergence(b, context), g = gate(H, D);
    return { tokens: b.n, H: H, D: D, x: g.x, lhs: g.lhs, rhs: g.rhs, pass: g.pass };
  }

  global.BadaEntropy = { tokens: tokens, bag: bag, density: density, entropy: entropy, divergence: divergence, gate: gate,
                         kernel: kernel, flow: flow, merge: merge, measure: measure };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaEntropy;
})(typeof window !== "undefined" ? window : globalThis);
