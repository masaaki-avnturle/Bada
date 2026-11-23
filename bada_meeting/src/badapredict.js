/*
 * badapredict.js — Bada Predict: 単語の補完と、次の単語の先読み
 *
 * Bada Precog (bada_apk、ブランチ claude/bada-prediction-engine-in0dfk) の Predictor.kt の移植。
 *   ・読み込んだ文章から 1-gram / 2-gram / 3-gram の回数を数える (train)
 *   ・入力中の語の続きを補完する (complete)。区切りのあとでは次の語を先読みする (predictNext)。
 *     3-gram の証拠を優先し (重み 3)、無ければ 2-gram、それも無ければ頻出語
 *   ・候補の確率は softmax(log(回数 + 1))。元の実装が掛けるエントロピー位相は確率を変えないので、ここでは省いている
 *   ・打った語をその場で学ぶ (observe)
 * 元の実装に足したもの: 日本語の文は語の間に空白が無いので、字種 (漢字・ひらがな・カタカナ・英数字) の
 * 変わり目で区切ってから数える (segment)。形態素解析ではないので、区切りは粗い。
 */
(function (global) {
  "use strict";
  var WORD_RE = /[A-Za-z][A-Za-z0-9'\-]*|[぀-ゟ゠-ヿ一-鿿々ー]+/g;
  var TAIL_RE = /([A-Za-z0-9'\-]+|[぀-ゟ゠-ヿ一-鿿々ー]+)$/;
  function softmax(z) {
    if (!z.length) return [];
    var m = Math.max.apply(null, z), e = z.map(function (v) { return Math.exp(v - m); }), s = e.reduce(function (a, b) { return a + b; }, 0) || 1;
    return e.map(function (v) { return v / s; });
  }
  // 字種の変わり目に空白を入れる (漢字 / ひらがな / カタカナ・長音 / 英数字)
  function segment(text) {
    var cls = function (ch) {
      var c = ch.charCodeAt(0);
      if ((c >= 0x4E00 && c <= 0x9FFF) || c === 0x3005) return "K";
      if (c >= 0x3040 && c <= 0x309F) return "H";
      if ((c >= 0x30A0 && c <= 0x30FF)) return "T";
      if (/[A-Za-z0-9'\-]/.test(ch)) return "L";
      return " ";
    };
    var out = "", prev = " ";
    Array.from(String(text)).forEach(function (ch) {
      var k = cls(ch);
      if (k !== prev && k !== " " && prev !== " ") out += " ";
      out += k === " " ? " " : ch; prev = k;
    });
    return out.replace(/\s+/g, " ").trim();
  }

  function Predictor(maxCandidates) { this.max = maxCandidates || 8; this.unigram = new Map(); this.bigram = new Map(); this.trigram = new Map(); this.totalTokens = 0; }
  var P = Predictor.prototype;
  P.tokenize = function (text) { return String(text).match(WORD_RE) || []; };
  var bump = function (map, key, t) { var m = map.get(key); if (!m) { m = new Map(); map.set(key, m); } m.set(t, (m.get(t) || 0) + 1); };
  P.train = function (text) {
    var self = this, prev = null, prev2 = null;
    this.tokenize(text).forEach(function (t) {
      self.unigram.set(t, (self.unigram.get(t) || 0) + 1); self.totalTokens++;
      if (prev !== null) { bump(self.bigram, prev, t); if (prev2 !== null) bump(self.trigram, prev2 + " " + prev, t); }
      prev2 = prev; prev = t;
    });
    return this;
  };
  P.observe = function (word) { if (String(word).trim()) this.train(word); };
  P._rank = function (cands, k, kind) {
    if (!cands.length) return [];
    var top = cands.slice().sort(function (a, b) { return b[1] - a[1]; }).slice(0, Math.max(k * 4, k));
    var p = softmax(top.map(function (c) { return Math.log(c[1] + 1); }));
    return top.map(function (c, i) { return { word: c[0], probability: p[i], kind: kind }; }).sort(function (a, b) { return b.probability - a.probability; }).slice(0, k);
  };
  P.complete = function (prefix, k) {
    k = k || this.max; if (!prefix) return [];
    var ascii = prefix.charCodeAt(0) < 128, p = ascii ? prefix.toLowerCase() : prefix, hits = [];
    this.unigram.forEach(function (c, w) {
      if (w === prefix) return;
      var cand = ascii ? w.toLowerCase() : w;
      if (cand.indexOf(p) === 0 && cand.length > p.length) hits.push([w, c]);
    });
    return this._rank(hits, k, "complete");
  };
  P.predictNext = function (context, k) {
    k = k || this.max;
    var last = context.length ? context[context.length - 1] : null, prev = context.length >= 2 ? context[context.length - 2] : null, counts = new Map(), kind = "unigram";
    var tri = last !== null && prev !== null ? this.trigram.get(prev + " " + last) : null, bi = last !== null ? this.bigram.get(last) : null;
    if (tri) { tri.forEach(function (c, w) { counts.set(w, (counts.get(w) || 0) + c * 3); }); kind = "trigram"; }
    if (bi) { bi.forEach(function (c, w) { counts.set(w, (counts.get(w) || 0) + c); }); if (kind === "unigram") kind = "bigram"; }
    if (!counts.size) Array.from(this.unigram.entries()).sort(function (a, b) { return b[1] - a[1]; }).slice(0, k * 2).forEach(function (e) { counts.set(e[0], e[1]); });
    return this._rank(Array.from(counts.entries()), k, kind);
  };
  // 入力位置より左の文字列 left から: 語の途中なら補完、区切りのあとなら次の語
  P.suggest = function (left, k) {
    k = k || this.max;
    var m = TAIL_RE.exec(left);
    if (m) {
      var partial = m[0], ctx = this.tokenize(left.slice(0, left.length - partial.length)), comp = this.complete(partial, k);
      return comp.length ? comp : this.predictNext(ctx.concat([partial]), k);
    }
    return this.predictNext(this.tokenize(left), k);
  };

  /* ── 思念会議のプラグイン ── */
  function makePlugin(seeds) {
    var pr = new Predictor(8), seen = {};
    (seeds || []).forEach(function (s) { pr.train(s); });
    var seedTokens = pr.totalTokens;
    // 候補: {text 表示, insert 発言欄に足す文字列, p 確率, kind}
    function suggest(left) {
      var line = String(left).split("\n").pop(), endsOpen = /[A-Za-z0-9぀-ヿ一-鿿々]$/.test(line), seg = segment(line), parts = seg ? seg.split(" ") : [];
      var partial = endsOpen && parts.length ? parts[parts.length - 1] : "", list = pr.suggest(seg + (endsOpen ? "" : " "), 8);
      if (!line.trim() || (list.length && list[0].kind === "unigram")) return [];      // 手掛かりが無いとき (頻出語しか出せないとき) は候補を出さない
      return list.map(function (s) {
        var done = s.kind === "complete", latin = /^[A-Za-z]/.test(s.word);
        var insert = done ? s.word.slice(partial.length) : (latin && line && !/\s$/.test(line) ? " " : "") + s.word;
        return { text: done ? s.word : "→ " + s.word, insert: insert, p: s.probability, kind: s.kind };
      }).filter(function (c) { return c.insert; });
    }
    return {
      id: "predict", name: "Bada Predict", kind: "native", predictor: pr, suggest: suggest,
      description: "単語の補完と次の単語の先読みを入力候補に出す (n-gram。発言を読んでその場で学ぶ)。/predict 文 で候補と確率を表示",
      onMessage: function (m) {                                   // 発言を 1 度だけ学ぶ (注記は付けない)
        var key = m.seq + "|" + m.text; if (!seen[key]) { seen[key] = true; pr.train(segment(m.text)); }
        return null;
      },
      onSuggest: function (left) { return suggest(left); },
      onCommand: function (args) {
        if (!args.trim()) return "語彙 " + pr.unigram.size + " 語 / 学んだ語 " + pr.totalTokens + " 個 (うち同梱の種 " + seedTokens + " 個)。使い方: /predict 文の途中まで";
        var list = suggest(args);
        if (!list.length) return "候補がありません。";
        var names = { complete: "補完", trigram: "3-gram", bigram: "2-gram", unigram: "頻出語" };
        return "「" + args + "」の続き (" + names[list[0].kind] + "):\n" + list.map(function (c) { return "- " + c.text.replace(/^→ /, "") + "  " + (c.p * 100).toFixed(1) + "%"; }).join("\n");
      }
    };
  }

  global.BadaPredict = { Predictor: Predictor, segment: segment, softmax: softmax, makePlugin: makePlugin };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaPredict;
})(typeof window !== "undefined" ? window : globalThis);
