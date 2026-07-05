/*
 * iq_engine.js — on-device port of the Bada IQ / Jones-telomere engine.
 * Pure JavaScript, runs in the Android WebView (and in Node for testing).
 *
 *   絵 → 方程式 → Jones多項式 → テロメア分裂 → 赤外線/温度 → IQ (順 + 真逆)
 *
 * Numerically identical to the Ruby package (lib/omega_iq). The drawing and the
 * thermal frame are embedded below so the whole pipeline runs offline.
 */
(function (root) {
  "use strict";

  // ---- Laurent polynomial: {exp:int -> coeff:int} ----
  function Laurent(terms) {
    this.t = {};
    if (terms) for (var k in terms) { if (terms[k]) this.t[k] = (this.t[k] || 0) + terms[k]; }
  }
  Laurent.mono = function (e, c) { var o = {}; o[e] = (c === undefined ? 1 : c); return new Laurent(o); };
  Laurent.zero = function () { return new Laurent(); };
  Laurent.prototype.add = function (o) {
    var r = new Laurent(this.t);
    for (var k in o.t) { r.t[k] = (r.t[k] || 0) + o.t[k]; if (!r.t[k]) delete r.t[k]; }
    return r;
  };
  Laurent.prototype.mul = function (o) {
    var r = {};
    for (var a in this.t) for (var b in o.t) {
      var e = (+a) + (+b); r[e] = (r[e] || 0) + this.t[a] * o.t[b];
    }
    return new Laurent(r);
  };
  Laurent.prototype.pow = function (n) {
    var r = Laurent.mono(0, 1);
    for (var i = 0; i < n; i++) r = r.mul(this);
    return r;
  };
  Laurent.prototype.isZero = function () { return Object.keys(this.t).length === 0; };
  Laurent.prototype.exps = function () { return Object.keys(this.t).map(Number); };
  Laurent.prototype.min = function () { return Math.min.apply(null, this.exps()); };
  Laurent.prototype.max = function () { return Math.max.apply(null, this.exps()); };
  Laurent.prototype.eval = function (x) {
    var s = 0; for (var e in this.t) s += this.t[e] * Math.pow(x, +e); return s;
  };
  function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = b; b = a % b; a = t; } return a || 1; }
  Laurent.prototype.toString = function (v, scale) {
    v = v || "A"; scale = scale || 1;
    if (this.isZero()) return "0";
    var es = this.exps().sort(function (a, b) { return b - a; });
    var out = es.map(function (e) {
      var c = this.t[e], mag = Math.abs(c), sign = c < 0 ? "-" : "+";
      var num = e, den = scale, g = gcd(num, den); num /= g; den /= g;
      var body;
      if (num === 0) body = "" + mag;
      else {
        var base = (mag === 1 ? v : mag + v);
        var exp = (den === 1 ? "" + num : num + "/" + den);
        body = (num === 1 && den === 1) ? base : base + "^" + exp;
      }
      return sign + " " + body;
    }, this).join(" ");
    return out.replace(/^\+ /, "");
  };

  // ---- Union-find ----
  function UF(labels) { this.p = {}; this.r = {}; for (var i = 0; i < labels.length; i++) { this.p[labels[i]] = labels[i]; this.r[labels[i]] = 0; } }
  UF.prototype.find = function (x) { while (this.p[x] !== x) { this.p[x] = this.p[this.p[x]]; x = this.p[x]; } return x; };
  UF.prototype.union = function (a, b) {
    var ra = this.find(a), rb = this.find(b); if (ra === rb) return;
    if (this.r[ra] < this.r[rb]) this.p[ra] = rb;
    else if (this.r[ra] > this.r[rb]) this.p[rb] = ra;
    else { this.p[rb] = ra; this.r[ra]++; }
  };
  UF.prototype.components = function () {
    var seen = {}, n = 0; for (var k in this.p) { var r = this.find(k); if (!seen[r]) { seen[r] = 1; n++; } } return n;
  };

  // ---- Jones (Kauffman bracket). crossing = [id,e0,e1,e2,e3,sign] ----
  function applySmoothing(uf, c, aSmoothing) {
    var e0 = c[1], e1 = c[2], e2 = c[3], e3 = c[4];
    var pairs = aSmoothing ? [[e0, e1], [e2, e3]] : [[e1, e2], [e3, e0]];
    for (var i = 0; i < pairs.length; i++) uf.union(pairs[i][0], pairs[i][1]);
  }
  function bracket(cr) {
    if (cr.length === 0) return Laurent.mono(0, 1);
    var n = cr.length, labels = {};
    for (var i = 0; i < n; i++) for (var j = 1; j <= 4; j++) labels[cr[i][j]] = 1;
    var lab = Object.keys(labels);
    var loopVal = new Laurent({ 2: -1, "-2": -1 });
    var total = Laurent.zero();
    for (var s = 0; s < (1 << n); s++) {
      var uf = new UF(lab), aCount = 0;
      for (var k = 0; k < n; k++) { var a = ((s >> k) & 1) === 0; applySmoothing(uf, cr[k], a); if (a) aCount++; }
      var loops = uf.components();
      total = total.add(Laurent.mono(aCount - (n - aCount), 1).mul(loopVal.pow(loops - 1)));
    }
    return total;
  }
  function writhe(cr) { var w = 0; for (var i = 0; i < cr.length; i++) w += cr[i][5]; return w; }
  function mirror(cr) { return cr.map(function (c) { return [c[0], c[2], c[3], c[4], c[1], -c[5]]; }); }
  function normalised(cr) {
    var w = writhe(cr);
    var factor = (w >= 0) ? new Laurent({ "-3": -1 }).pow(w) : new Laurent({ 3: -1 }).pow(-w);
    return factor.mul(bracket(cr));
  }
  function polynomial(cr) {
    var f = normalised(cr), terms = {};
    for (var e in f.t) { var key = -e; terms[key] = (terms[key] || 0) + f.t[e]; }
    return new Laurent(terms);
  }

  // ---- Drawing: 絵 → 方程式 → PD ----
  function loadDrawing(spec) {
    // spec: {segments:[[id,x1,y1,x2,y2],...], arrow:[...]}
    var byId = {}; spec.segments.forEach(function (s) { byId[s[0]] = s; });
    var order = (spec.arrow && spec.arrow.length) ? spec.arrow : spec.segments.map(function (s) { return s[0]; });
    var segs = order.map(function (i) { return byId[i]; });
    return { segments: segs, order: order };
  }
  function dir(s) { return [s[3] - s[1], s[4] - s[2]]; }
  function equations(segs) {
    var eqs = segs.map(function (s) {
      return "L" + s[0] + "(u) = (" + s[1].toFixed(3) + " + " + (s[3] - s[1]).toFixed(3) + " u, " +
        s[2].toFixed(3) + " + " + (s[4] - s[2]).toFixed(3) + " u),  u in [0,1]";
    });
    eqs.push("closure: L" + segs[segs.length - 1][0] + "(1) = L" + segs[0][0] + "(0)");
    return eqs;
  }
  function intersect(a, b) {
    var x1 = a[1], y1 = a[2], x2 = a[3], y2 = a[4], x3 = b[1], y3 = b[2], x4 = b[3], y4 = b[4];
    var den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    if (Math.abs(den) < 1e-12) return null;
    var t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den;
    var u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / den;
    var eps = 1e-9;
    if (!(t > eps && t < 1 - eps && u > eps && u < 1 - eps)) return null;
    return [x1 + t * (x2 - x1), y1 + t * (y2 - y1), t, u];
  }
  function crossingsOf(segs) {
    var n = segs.length, pts = [];
    for (var i = 0; i < n; i++) for (var j = i + 1; j < n; j++) {
      if (Math.abs(i - j) === 1 || (i === 0 && j === n - 1)) continue;
      var hit = intersect(segs[i], segs[j]);
      if (!hit) continue;
      pts.push([i, j, hit[2], hit[3]]); // i,j,si,sj
    }
    // passes along the closed walk: [ [segIndex, frac], cid, strand ]
    var passes = [];
    pts.forEach(function (p, cid) { passes.push([[p[0], p[2]], cid, "i"]); passes.push([[p[1], p[3]], cid, "j"]); });
    passes.sort(function (a, b) { return a[0][0] - b[0][0] || a[0][1] - b[0][1]; });
    var m = passes.length, info = {};
    passes.forEach(function (p, k) {
      var cid = p[1]; if (!info[cid]) info[cid] = {};
      info[cid][p[2]] = { inArc: (k - 1 + m) % m, outArc: k, k: k };
    });
    return pts.map(function (pt, cid) { return assemble(segs, cid, pt, info[cid]); });
  }
  function assemble(segs, cid, pt, info) {
    var i = pt[0], j = pt[1], di = dir(segs[i]), dj = dir(segs[j]);
    var halves = [
      { arc: info.i.inArc, ang: Math.atan2(-di[1], -di[0]), strand: "i" },
      { arc: info.i.outArc, ang: Math.atan2(di[1], di[0]), strand: "i" },
      { arc: info.j.inArc, ang: Math.atan2(-dj[1], -dj[0]), strand: "j" },
      { arc: info.j.outArc, ang: Math.atan2(dj[1], dj[0]), strand: "j" }
    ];
    halves.sort(function (a, b) { return a.ang - b.ang; });
    var over = (info.i.k % 2 === 0) ? "i" : "j";
    var under = over === "i" ? "j" : "i";
    var start = 0; for (var h = 0; h < 4; h++) { if (halves[h].strand === under && halves[h].arc === info[under].inArc) { start = h; break; } }
    var e = [0, 1, 2, 3].map(function (k) { return halves[(start + k) % 4].arc; });
    var od = over === "i" ? di : dj, ud = over === "i" ? dj : di;
    var cross = od[0] * ud[1] - od[1] * ud[0];
    var sign = cross >= 0 ? 1 : -1;
    return [cid, e[0], e[1], e[2], e[3], sign];
  }

  // ---- Telomere splitting ----
  function loopSpectrum(cr) {
    var n = cr.length, labels = {};
    for (var i = 0; i < n; i++) for (var j = 1; j <= 4; j++) labels[cr[i][j]] = 1;
    var lab = Object.keys(labels), spec = {};
    for (var s = 0; s < (1 << n); s++) {
      var uf = new UF(lab);
      for (var k = 0; k < n; k++) applySmoothing(uf, cr[k], ((s >> k) & 1) === 0);
      var c = uf.components(); spec[c] = (spec[c] || 0) + 1;
    }
    return spec;
  }
  function shannon(spec) {
    var total = 0, k; for (k in spec) total += spec[k]; if (!total) return 0;
    var h = 0; for (k in spec) { var p = spec[k] / total; if (p > 0) h -= p * Math.log2(p); } return h;
  }
  function telomere(cr) {
    var gens = [], remaining = cr.slice(0), gen = 0;
    function smoothOne(list) {
      if (!list.length) return [];
      var f = list[0], merge = {}; merge[f[2]] = f[1]; merge[f[4]] = f[3];
      return list.slice(1).map(function (c) {
        function mp(x) { return merge.hasOwnProperty(x) ? merge[x] : x; }
        return [c[0], mp(c[1]), mp(c[2]), mp(c[3]), mp(c[4]), c[5]];
      });
    }
    while (remaining.length) { gens.push({ generation: gen, length: remaining.length, daughters: Math.pow(2, gen) }); remaining = smoothOne(remaining); gen++; }
    gens.push({ generation: gen, length: 0, daughters: Math.pow(2, gen), senescent: true });
    var spec = loopSpectrum(cr);
    return { generations: gens, hayflick: cr.length, entropy: shannon(spec) };
  }

  // ---- Thermal (IR camera + thermometer) ----
  var THETA = 300.0;
  function thermalFromPixels(pixels) {
    var n = pixels.length;
    var temps = pixels.map(function (p) { return 20.0 + (p / 255.0) * 25.0; });
    var mean = temps.reduce(function (a, b) { return a + b; }, 0) / n;
    var varr = temps.reduce(function (a, t) { return a + (t - mean) * (t - mean); }, 0) / n;
    var coherence = Math.max(1.0 - varr / (12.5 * 12.5), 0.0);
    var tK = mean + 273.15;
    return { meanC: mean, coherence: coherence, tEval: Math.exp(-THETA / tK) };
  }

  // ---- IQ ----
  var WEIGHTS = { complexity: 0.30, magnitude: 0.20, entropy: 0.30, coherence: 0.20 };
  function squash(x) { return 1.0 / (1.0 + Math.exp(-4.0 * (x - 0.5))); }
  function round1(x) { return Math.round(x * 10) / 10; }
  function scoreOne(cr, tEval, coherence, invert) {
    var jones = polynomial(cr);
    var span = jones.isZero() ? 0 : (jones.max() - jones.min()) / 4.0;
    var complexity = squash(span / 4.0);
    var mag = Math.abs(jones.eval(tEval));
    var magnitude = squash(Math.log(1 + mag));
    var tel = telomere(cr), hl = Math.max(tel.hayflick, 1);
    var ent = tel.entropy / (Math.log2(hl + 1) + 1e-9); if (invert) ent = 1.0 - ent;
    var entropy = squash(ent);
    var coh = squash(coherence);
    var comps = { complexity: complexity, magnitude: magnitude, entropy: entropy, coherence: coh };
    var raw = 0; for (var k in WEIGHTS) raw += WEIGHTS[k] * comps[k];
    return { iq: round1(100 + 60 * (raw - 0.5)), components: comps, raw: raw, jones: jones };
  }
  function band(iq) {
    if (iq < 85) return "senescent-strand (低テロメア活性)";
    if (iq < 100) return "baseline";
    if (iq < 115) return "elevated";
    if (iq < 130) return "high-coherence";
    return "superchiral (超分裂活性)";
  }

  // ---- Full pipeline ----
  function run(spec, pixels) {
    var d = loadDrawing(spec);
    var cr = crossingsOf(d.segments);
    var th = thermalFromPixels(pixels);
    var fwd = scoreOne(cr, th.tEval, th.coherence, false);
    var rev = scoreOne(mirror(cr), th.tEval, th.coherence, true);
    return {
      segments: d.segments, order: d.order, equations: equations(d.segments),
      crossings: cr, writhe: writhe(cr),
      jones: fwd.jones, mirrorJones: polynomial(mirror(cr)),
      telomere: telomere(cr), thermal: th,
      iq: fwd.iq, mirrorIq: rev.iq,
      divergence: round1(Math.abs(fwd.iq - rev.iq)),
      components: fwd.components, raw: fwd.raw, band: band(fwd.iq)
    };
  }

  root.BadaIQ = {
    Laurent: Laurent, bracket: bracket, writhe: writhe, mirror: mirror, polynomial: polynomial,
    crossingsOf: crossingsOf, telomere: telomere, thermalFromPixels: thermalFromPixels, run: run
  };
})(typeof window !== "undefined" ? window : globalThis);
