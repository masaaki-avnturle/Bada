/*
 * engine.js — BadaGPT の計算エンジン (依存なし。ブラウザ / Node 共通)
 *
 * riemann_prover/ (Python) の移植:
 *   ζ・L 関数 / 高さ T までの RH 数値検証 / Schoenfeld 不等式 / 深リーマン予想の証拠 /
 *   擬似量子コンピュータ上の Grover 反例探索 / 数学的帰納法と証明の修正 /
 *   コラッツ降下補題 / Jones 多項式暗号による封印 / 証明書 PatchGuard
 *
 * 健全性: 未解決の予想そのものは決して「証明済み」と判定しない。
 */
(function (global) {
  "use strict";

  /* ───────────── ζ(s), L(s,χ), θ(t), Z(t) ───────────── */
  var B2K = [0.08333333333333333, -0.001388888888888889, 3.306878306878307e-05, -8.267195767195768e-07, 2.08767569878681e-08, -5.284190138687493e-10, 1.3382536530684679e-11, -3.3896802963225827e-13, 8.586062056277845e-15, -2.174868698558062e-16, 5.5090028283602295e-18, -1.3954464685812522e-19];

  // ζ(s, a) = Σ (n+a)^(-s)  (Euler–Maclaurin, s = sr + i·si ≠ 1) → [re, im]
  function hurwitz(sr, si, a) {
    var N = Math.floor(Math.hypot(sr, si)) + 25, re = 0, im = 0, n, L, m;
    for (n = 0; n < N; n++) {
      L = Math.log(n + a); m = Math.exp(-sr * L);
      re += m * Math.cos(si * L); im -= m * Math.sin(si * L);
    }
    var w = N + a, lw = Math.log(w), mw = Math.exp(-sr * lw);
    var wr = mw * Math.cos(si * lw), wi = -mw * Math.sin(si * lw);       // w^(-s)
    var dr = sr - 1, di = si, dd = dr * dr + di * di;                    // w^(1-s)/(s-1)
    re += w * (wr * dr + wi * di) / dd + wr / 2;
    im += w * (wi * dr - wr * di) / dd + wi / 2;
    var pr = sr, pi = si, qr = wr / w, qi = wi / w, k, t, ar, ai, br, bi;
    for (k = 1; k <= B2K.length; k++) {
      re += B2K[k - 1] * (pr * qr - pi * qi);
      im += B2K[k - 1] * (pr * qi + pi * qr);
      ar = sr + 2 * k - 1; ai = si; br = sr + 2 * k; bi = si;            // poch *= (s+2k-1)(s+2k)
      t = ar * br - ai * bi; ai = ar * bi + ai * br; ar = t;
      t = pr * ar - pi * ai; pi = pr * ai + pi * ar; pr = t;
      qr /= w * w; qi /= w * w;
    }
    return [re, im];
  }
  function zeta(sr, si) { return hurwitz(sr, si || 0, 1); }

  // L(s,χ),  χ = [χ(0), …, χ(q-1)] with entries [re, im]
  function dirichletL(sr, si, chi) {
    var q = chi.length, re = 0, im = 0, a, c, h;
    for (a = 1; a <= q; a++) {
      c = chi[a % q];
      if (c[0] === 0 && c[1] === 0) continue;
      h = hurwitz(sr, si, a / q);
      re += c[0] * h[0] - c[1] * h[1]; im += c[0] * h[1] + c[1] * h[0];
    }
    var lq = Math.log(q), m = Math.exp(-sr * lq), cr = m * Math.cos(si * lq), ci = -m * Math.sin(si * lq);
    return [re * cr - im * ci, re * ci + im * cr];
  }

  // Im log Γ(x + iy) on the continuous branch (x > 0)
  function loggammaIm(x, y) {
    var shift = 0;
    while (x < 15) { shift += Math.atan2(y, x); x += 1; }
    var d = x * x + y * y, ir = x / d, ii = -y / d;                      // 1/z
    var z2r = ir * ir - ii * ii, z2i = 2 * ir * ii;
    var c = [1 / 12, -1 / 360, 1 / 1260, -1 / 1680, 1 / 1188], sr = 0, si = 0, pr = ir, pi = ii, k, t;
    for (k = 0; k < c.length; k++) {
      sr += c[k] * pr; si += c[k] * pi;
      t = pr * z2r - pi * z2i; pi = pr * z2i + pi * z2r; pr = t;
    }
    var lr = 0.5 * Math.log(d), li = Math.atan2(y, x);                   // log z
    return (x - 0.5) * li + y * lr - y + si - shift;
  }
  function theta(t) { return loggammaIm(0.25, t / 2) - t / 2 * Math.log(Math.PI); }
  function hardyZ(t) {
    var th = theta(t), z = zeta(0.5, t);
    return Math.cos(th) * z[0] - Math.sin(th) * z[1];
  }

  /* ───────────── 高さ T までの RH ───────────── */
  function spacing(t) { return 2 * Math.PI / Math.log(Math.max(t, 14) / (2 * Math.PI)); }
  function scanSignChanges(T, density) {
    var out = [], a = 1, za = hardyZ(1), b, zb;
    while (a < T) {
      b = Math.min(a + spacing(a) / density, T); zb = hardyZ(b);
      if (za * zb < 0) out.push([a, b]);
      a = b; za = zb;
    }
    return out;
  }
  function refineZero(a, b) {
    var fa = hardyZ(a), i, m, fm;
    for (i = 0; i < 60; i++) {
      m = (a + b) / 2; fm = hardyZ(m);
      if (fa * fm <= 0) b = m; else { a = m; fa = fm; }
    }
    return (a + b) / 2;
  }
  // arg ζ(1/2+iT) by continuous variation from σ = 4 (where |ζ−1| < 0.083)
  function argZeta(T) {
    var sigma = 4, z = zeta(sigma, T), arg = Math.atan2(z[1], z[0]), step = 0.05, nxt, z2, d;
    while (sigma > 0.5) {
      nxt = Math.max(sigma - step, 0.5); z2 = zeta(nxt, T);
      d = Math.atan2(z2[1] * z[0] - z2[0] * z[1], z2[0] * z[0] + z2[1] * z[1]);
      if (Math.abs(d) > 0.3 && step > 1e-6) { step /= 2; continue; }
      arg += d; sigma = nxt; z = z2; step = Math.min(step * 1.5, 0.05);
    }
    return arg;
  }
  function zeroCount(T) {
    var n = theta(T) / Math.PI + 1 + argZeta(T) / Math.PI;
    return [Math.round(n), Math.abs(n - Math.round(n))];
  }
  function verifyRH(T, listZeros) {
    T = T || 500; if (listZeros === undefined) listZeros = 10;
    var zc = zeroCount(T), density = 6, br = [];
    while (density <= 96) {
      br = scanSignChanges(T, density);
      if (br.length >= zc[0]) break;
      density *= 2;
    }
    var ok = br.length === zc[0] && zc[1] < 1e-3;
    return {
      claim: "0 < Im ρ < " + T + " の ζ の非自明零点はすべて Re ρ = 1/2 上にあり単純",
      height: T, zeros_in_strip_argument_principle: zc[0], argument_principle_residual: zc[1],
      zeros_on_critical_line_sign_changes: br.length, scan_density: density,
      first_zeros: br.slice(0, listZeros).map(function (p) { return +refineZero(p[0], p[1]).toFixed(9); }),
      status: ok ? "verified" : "inconclusive"
    };
  }

  /* ───────────── Schoenfeld 不等式 (RH と同値) ───────────── */
  function sieve(n) {
    var s = new Uint8Array(n + 1).fill(1), p, m;
    s[0] = 0; if (n >= 1) s[1] = 0;
    for (p = 2; p * p <= n; p++) if (s[p]) for (m = p * p; m <= n; m += p) s[m] = 0;
    return s;
  }
  function schoenfeld(X) {
    X = X || 1e6;
    var s = sieve(X), lam = new Float64Array(X + 1), p, q, lp;
    for (p = 2; p <= X; p++) if (s[p]) { lp = Math.log(p); for (q = p; q <= X; q *= p) lam[q] = lp; }
    var psi = 0, worst = 0, worstX = 0, ok = true, c = 1 / (8 * Math.PI), n, ln, r;
    for (n = 1; n < X; n++) {
      psi += lam[n];
      if (n < 74) continue;
      ln = Math.log(n);
      r = Math.max(Math.abs(psi - n), Math.abs(psi - (n + 1))) / (c * Math.sqrt(n) * ln * ln);
      if (r > worst) { worst = r; worstX = n; }
      if (r >= 1) ok = false;
    }
    return { claim: "|ψ(x) − x| < √x·log²x/(8π)  (74 ≤ x ≤ " + X + ")", limit: X,
             max_ratio: worst, max_ratio_at: worstX, status: ok ? "verified" : "disproved" };
  }

  /* ───────────── 深リーマン予想の証拠 ───────────── */
  var CHARACTERS = {
    "chi_-4": [[0, 0], [1, 0], [0, 0], [-1, 0]],
    "chi_-3": [[0, 0], [1, 0], [-1, 0]],
    "chi_5": [[0, 0], [1, 0], [-1, 0], [-1, 0], [1, 0]],
    "chi_5_complex": [[0, 0], [1, 0], [0, 1], [0, -1], [-1, 0]]
  };
  function drhEvidence(name, t, X) {
    name = name || "chi_-4"; t = t || 0; X = X || 1e6;
    var chi = CHARACTERS[name], q = chi.length;
    var isReal = chi.every(function (c) { return c[1] === 0; });
    var factor = (t === 0 && isReal) ? Math.SQRT2 : 1;
    var L = dirichletL(0.5, t, chi), target = [L[0] * factor, L[1] * factor];
    var cps = [], k; for (k = 100; k <= X; k *= 10) cps.push(k);
    if (!cps.length || cps[cps.length - 1] !== X) cps.push(X);
    var s = sieve(X), lr = 0, li = 0, p = 2, rows = [];
    cps.forEach(function (x) {
      for (; p <= x; p++) {
        if (!s[p]) continue;
        var c = chi[p % q]; if (c[0] === 0 && c[1] === 0) continue;
        var lp = Math.log(p), m = Math.exp(-0.5 * lp), pr = m * Math.cos(t * lp), pi = -m * Math.sin(t * lp);
        var ur = 1 - (c[0] * pr - c[1] * pi), ui = -(c[0] * pi + c[1] * pr);     // 1 − χ(p)p^(−s)
        lr -= 0.5 * Math.log(ur * ur + ui * ui); li -= Math.atan2(ui, ur);
      }
      var e = Math.exp(lr), prod = [e * Math.cos(li), e * Math.sin(li)];
      var rel = function (z) { return Math.hypot(prod[0] - z[0], prod[1] - z[1]) / Math.hypot(z[0], z[1]); };
      rows.push({ x: x, partial_product: prod, rel_error_vs_DRH_limit: rel(target), rel_error_vs_plain_L: rel(L) });
    });
    return {
      claim: "Π_(p≤x)(1−χ(p)p^(−s))^(−1) → " + (factor !== 1 ? "√2·" : "") + "L(s,χ),  χ=" + name + ", s=1/2+" + t + "i",
      character: name, s: [0.5, t], L: L, sqrt2_factor: factor !== 1, drh_limit: target, table: rows, status: "open"
    };
  }

  /* ───────────── 擬似量子コンピュータ (状態ベクトル) + Grover ───────────── */
  function rng(seed) {                       // mulberry32
    var a = (seed >>> 0) + 0x6D2B79F5;
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function hadamard(amps, q) {
    var N = amps.length, mask = 1 << q, r = Math.SQRT1_2, i, j, x0, x1;
    for (i = 0; i < N; i++) {
      if (i & mask) continue;
      j = i | mask; x0 = amps[i]; x1 = amps[j];
      amps[i] = r * (x0 + x1); amps[j] = r * (x0 - x1);
    }
  }
  function groverSearch(marked, seed, shots) {
    var N = marked.length, k = Math.round(Math.log2(N)), M = 0, i, q, it;
    if ((1 << k) !== N) throw new Error("marked.length must be a power of two");
    for (i = 0; i < N; i++) if (marked[i]) M++;
    var amps = new Float64Array(N); amps[0] = 1;
    for (q = 0; q < k; q++) hadamard(amps, q);
    var iterations = 0;
    if (M > 0 && M < N) iterations = Math.max(0, Math.round(Math.PI / (4 * Math.asin(Math.sqrt(M / N))) - 0.5));
    for (it = 0; it < iterations; it++) {
      for (i = 0; i < N; i++) if (marked[i]) amps[i] = -amps[i];          // oracle
      for (q = 0; q < k; q++) hadamard(amps, q);                          // diffusion
      for (i = 1; i < N; i++) amps[i] = -amps[i];
      for (q = 0; q < k; q++) hadamard(amps, q);
    }
    var pm = 0; for (i = 0; i < N; i++) if (marked[i]) pm += amps[i] * amps[i];
    var rand = rng(seed || 0), samples = [], s, u, acc;
    for (s = 0; s < (shots || 16); s++) {
      u = rand(); acc = 0;
      for (i = 0; i < N; i++) { acc += amps[i] * amps[i]; if (u < acc) break; }
      samples.push(Math.min(i, N - 1));
    }
    return { qubits: k, marked: M, iterations: iterations, success_probability: pm, measured: samples[0], samples: samples };
  }

  function isPrime(n) {
    if (n < 2) return false;
    if (n % 2 === 0) return n === 2;
    for (var d = 3; d * d <= n; d += 2) if (n % d === 0) return false;
    return true;
  }
  function sigma(n) {
    var t = 0, d;
    for (d = 1; d * d <= n; d++) if (n % d === 0) t += d + (d * d !== n ? n / d : 0);
    return t;
  }
  var HARM = [0];
  function harmonic(n) { while (HARM.length <= n) HARM.push(HARM[HARM.length - 1] + 1 / HARM.length); return HARM[n]; }
  function reachesOne(n, limit) {
    for (var i = 0; i < (limit || 100000); i++) {
      if (n === 1) return true;
      n = n % 2 === 0 ? n / 2 : 3 * n + 1;
    }
    return false;
  }
  var PROBLEMS = {
    riemann_lagarias: { title: "リーマン予想 (Lagarias の同値形)", statement: "すべての n ≥ 1 で σ(n) ≤ H_n + exp(H_n)·log(H_n)",
      nOf: function (i) { return i + 1; },
      cx: function (n) { var h = harmonic(n); return sigma(n) > h + Math.exp(h) * Math.log(h) + 1e-9; } },
    goldbach: { title: "ゴールドバッハ予想", statement: "4 以上のすべての偶数は 2 つの素数の和",
      nOf: function (i) { return 2 * i + 4; },
      cx: function (n) { for (var p = 2; p <= n / 2; p++) if (isPrime(p) && isPrime(n - p)) return false; return true; } },
    collatz: { title: "コラッツ予想", statement: "すべての n ≥ 1 は 3n+1 操作で 1 に到達する",
      nOf: function (i) { return i + 1; }, cx: function (n) { return !reachesOne(n, 10000); } },
    legendre: { title: "ルジャンドル予想", statement: "すべての n ≥ 1 で n² と (n+1)² の間に素数がある",
      nOf: function (i) { return i + 1; },
      cx: function (n) { for (var m = n * n + 1; m < (n + 1) * (n + 1); m++) if (isPrime(m)) return false; return true; } },
    euler_polynomial: { title: "（対照実験・偽の命題）n² + n + 41 は常に素数", statement: "すべての n ≥ 0 で n² + n + 41 は素数",
      nOf: function (i) { return i; }, cx: function (n) { return !isPrime(n * n + n + 41); } }
  };
  function isCounterexample(problem, n) { return !!PROBLEMS[problem].cx(n); }
  function quantumSearch(problem, qubits, seed) {
    var spec = PROBLEMS[problem], N = 1 << (qubits || 10), ns = [], marked = [], i;
    for (i = 0; i < N; i++) { ns.push(spec.nOf(i)); marked.push(!!spec.cx(ns[i])); }
    var g = groverSearch(marked, seed), samples = g.samples, found = false, n = ns[samples[0]], shots = 0;
    delete g.samples;
    for (i = 0; i < samples.length; i++) {                 // every measurement is re-checked classically
      shots++;
      if (isCounterexample(problem, ns[samples[i]])) { n = ns[samples[i]]; found = true; g.measured = samples[i]; break; }
    }
    return {
      problem: problem, title: spec.title, statement: spec.statement, range: [ns[0], ns[N - 1]],
      qubits: g.qubits, marked: g.marked, iterations: g.iterations, success_probability: g.success_probability,
      measured: g.measured, shots: shots, counterexample: found ? n : null, counterexamples_in_range: g.marked,
      status: found ? "disproved" : "open",
      bounded_status: found ? "disproved" : (g.marked === 0 ? "verified" : "inconclusive")
    };
  }
  function quantumSearchAll(qubits, seed) {
    return Object.keys(PROBLEMS).map(function (p) { return quantumSearch(p, qubits, seed); });
  }

  /* ───────────── 厳密な有理数・多項式 (BigInt) ───────────── */
  function gcd(a, b) { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) { var t = a % b; a = b; b = t; } return a; }
  function F(n, d) {
    n = BigInt(n); d = d === undefined ? 1n : BigInt(d);
    if (d === 0n) throw new Error("0 で割ることはできません");
    if (d < 0n) { n = -n; d = -d; }
    var g = gcd(n, d) || 1n;
    return { n: n / g, d: d / g };
  }
  function fParse(x) {
    if (typeof x === "object") return x;
    var m = String(x).trim().match(/^(-?\d+)(?:\/(\d+))?$/);
    if (!m) throw new Error("分数として読めません: " + x);
    return F(m[1], m[2] || 1);
  }
  function fAdd(a, b) { return F(a.n * b.d + b.n * a.d, a.d * b.d); }
  function fSub(a, b) { return F(a.n * b.d - b.n * a.d, a.d * b.d); }
  function fMul(a, b) { return F(a.n * b.n, a.d * b.d); }
  function fDiv(a, b) { return F(a.n * b.d, a.d * b.n); }
  function fEq(a, b) { return a.n === b.n && a.d === b.d; }
  function fStr(a) { return a.d === 1n ? String(a.n) : a.n + "/" + a.d; }
  var ZERO = F(0), ONE = F(1);

  function poly(c) { var p = c.map(fParse); while (p.length && p[p.length - 1].n === 0n) p.pop(); return p; }
  function pEval(p, x) { var acc = ZERO; for (var i = p.length - 1; i >= 0; i--) acc = fAdd(fMul(acc, x), p[i]); return acc; }
  function pAdd(a, b, sign) {
    var out = [], n = Math.max(a.length, b.length), i;
    for (i = 0; i < n; i++) out.push((sign === -1 ? fSub : fAdd)(a[i] || ZERO, b[i] || ZERO));
    return poly(out);
  }
  function pMul(a, b) {
    if (!a.length || !b.length) return [];
    var out = [], i, j;
    for (i = 0; i < a.length + b.length - 1; i++) out.push(ZERO);
    for (i = 0; i < a.length; i++) for (j = 0; j < b.length; j++) out[i + j] = fAdd(out[i + j], fMul(a[i], b[j]));
    return poly(out);
  }
  function pScale(p, c) { return poly(p.map(function (x) { return fMul(x, c); })); }
  function pShift(p) {                         // p(n) → p(n+1)
    var out = [], power = [ONE];
    p.forEach(function (c) { out = pAdd(out, pScale(power, c)); power = pMul(power, [ONE, ONE]); });
    return out;
  }
  function pInterpolate(pts) {
    var out = [];
    pts.forEach(function (pi, i) {
      var term = [ONE], denom = ONE;
      pts.forEach(function (pj, j) {
        if (i === j) return;
        term = pMul(term, [fSub(ZERO, pj[0]), ONE]); denom = fMul(denom, fSub(pi[0], pj[0]));
      });
      out = pAdd(out, pScale(term, fDiv(pi[1], denom)));
    });
    return out;
  }
  function pStr(p) {
    if (!p.length) return "0";
    var parts = [];
    for (var i = p.length - 1; i >= 0; i--)
      if (p[i].n !== 0n) parts.push("(" + fStr(p[i]) + ")" + (i === 0 ? "" : i === 1 ? "·n" : "·n^" + i));
    return parts.join(" + ");
  }
  // "n(n+1)(2n+1)/6" → 多項式 (変数は n / k / x のいずれか 1 文字)
  function pParse(src) {
    var s = String(src).replace(/\s+/g, "").replace(/[×·]/g, "*").replace(/²/g, "^2").replace(/³/g, "^3"), pos = 0;
    function peek() { return s[pos]; }
    function expr() {
      var v = term();
      while (peek() === "+" || peek() === "-") { var op = s[pos++]; v = pAdd(v, term(), op === "-" ? -1 : 1); }
      return v;
    }
    function term() {
      var v = factor();
      for (;;) {
        var c = peek();
        if (c === "*") { pos++; v = pMul(v, factor()); }
        else if (c === "/") {
          pos++; var d = factor();
          if (!d.length) throw new Error("0 で割ることはできません");
          if (d.length !== 1) throw new Error("定数以外では割れません");
          v = pScale(v, fDiv(ONE, d[0]));
        } else if (c !== undefined && /[0-9a-zA-Z(]/.test(c)) v = pMul(v, factor());   // 暗黙の積
        else return v;
      }
    }
    function factor() {
      var v = atom();
      if (peek() === "^") {
        pos++; var m = s.slice(pos).match(/^\d+/);
        if (!m) throw new Error("指数は非負整数にしてください");
        pos += m[0].length;
        var r = [ONE]; for (var i = 0; i < +m[0]; i++) r = pMul(r, v);
        v = r;
      }
      return v;
    }
    function atom() {
      var c = peek();
      if (c === "-") { pos++; return pScale(factor(), F(-1)); }
      if (c === "(") { pos++; var v = expr(); if (s[pos++] !== ")") throw new Error("括弧が閉じていません"); return v; }
      var m = s.slice(pos).match(/^\d+/);
      if (m) { pos += m[0].length; return poly([F(m[0])]); }
      if (c !== undefined && /[nkx]/i.test(c)) { pos++; return [ZERO, ONE]; }
      throw new Error("式を読めません: 「" + s.slice(pos) + "」");
    }
    var out = expr();
    if (pos !== s.length) throw new Error("式を読めません: 「" + s.slice(pos) + "」");
    return out;
  }

  /* ───────────── 数学的帰納法・証明の修正 ───────────── */
  function drift(f, g) { return pAdd(pAdd(pShift(g), g, -1), pShift(f), -1); }
  function proveSum(f, g) {
    f = poly(f); g = poly(g);
    var base = pEval(g, ZERO), d = drift(f, g);
    var out = { kind: "sum_identity", f: f.map(fStr), g: g.map(fStr),
                claim: "Σ_(k=1..n) [" + pStr(f) + "] = " + pStr(g), method: "数学的帰納法" };
    if (base.n === 0n && !d.length) {
      out.status = "proved";
      out.steps = ["基底: g(0) = 0 = 空和", "段: g(n+1) − g(n) − f(n+1) は多項式として恒等的に 0",
                   "ゆえに帰納法によりすべての n ≥ 0 で成立"];
      return out;
    }
    var total = ZERO, n = 0;
    while (fEq(total, pEval(g, F(n)))) { n++; total = fAdd(total, pEval(f, F(n))); }
    out.status = "disproved"; out.counterexample = n;
    out.steps = ["n = " + n + ": 左辺 = " + fStr(total) + ", 右辺 = " + fStr(pEval(g, F(n)))];
    out.drift = base.n === 0n ? pStr(d) : "基底 g(0) = " + fStr(base) + " ≠ 0";
    return out;
  }
  // 誤った閉形式を、保存量 I(n) = g(n) − Σ f(k) ≡ 0 の等位集合へ射影する
  function repairSum(f, g) {
    f = poly(f); g = poly(g);
    var pts = [[ZERO, ZERO]], total = ZERO, n;
    for (n = 1; n < f.length + 2; n++) { total = fAdd(total, pEval(f, F(n))); pts.push([F(n), total]); }
    var fixed = pInterpolate(pts), proof = proveSum(f, fixed);
    return { kind: "repair", original: proveSum(f, g), repaired: proof,
             drift_before: pStr(drift(f, g)), drift_after: pStr(drift(f, fixed)), status: proof.status };
  }
  // 補題 (証明つき): コラッツ予想の最小反例は 2^bits 以上で、生き残った剰余類に属する
  function collatzDescent(bits) {
    bits = bits || 12;
    var M = Math.pow(2, bits), survivors = [], r, a, b, j, descended, small = true, n;
    for (r = 0; r < M; r++) {
      a = M; b = r; descended = false;
      for (j = 0; j < bits; j++) {
        if (b % 2) { a = 3 * a / 2; b = (3 * b + 1) / 2; } else { a /= 2; b /= 2; }
        if (a < M && M - a > b - r) { descended = true; break; }
      }
      if (!descended) survivors.push(r);
    }
    for (n = 1; n < M; n++) if (!reachesOne(n)) { small = false; break; }
    return {
      kind: "collatz_descent", bits: bits, modulus: M,
      claim: "コラッツ予想の最小反例 n0 は n0 ≥ " + M + " かつ n0 mod " + M + " が " + survivors.length + " 個の剰余類のいずれか",
      survivor_count: survivors.length, survivors_head: survivors.slice(0, 12),
      excluded_fraction: 1 - survivors.length / M, small_cases_verified: small,
      method: "強い帰納法 (降下) + 補集合の剰余類ふるい",
      status: small ? "proved" : "disproved", conjecture_status: "open"
    };
  }
  var NO_STEP = [
    { kind: "no_inductive_step", problem: "riemann_hypothesis", status: "open",
      note: "零点は離散的な添字 n に沿った P(n) ⇒ P(n+1) の形を持たず、既知の帰納の段がない" },
    { kind: "no_inductive_step", problem: "deep_riemann_hypothesis", status: "open",
      note: "オイラー積の収束は極限の主張であり、有限段の帰納では到達できない" },
    { kind: "no_inductive_step", problem: "goldbach", status: "open",
      note: "2n が素数 2 個の和でも 2n+2 について何も導けない。補集合に既知の降下構造がない" }
  ];
  function inductionReport(bits) {
    return [
      proveSum([0, 1], [0, "1/2", "1/2"]),
      proveSum([0, 0, 0, 1], [0, 0, "1/4", "1/2", "1/4"]),
      repairSum([0, 0, 1], [0, "1/5", "3/5", "2/5"]),
      collatzDescent(bits)
    ].concat(JSON.parse(JSON.stringify(NO_STEP)));
  }
  function recheck(e) {
    if (e.kind === "sum_identity") return proveSum(e.f, e.g).status === e.status;
    if (e.kind === "repair") return recheck(e.repaired) && e.repaired.status === e.status;
    if (e.kind === "collatz_descent") {
      var fresh = collatzDescent(+e.bits);
      return e.conjecture_status === "open" && fresh.status === e.status && fresh.survivor_count === e.survivor_count;
    }
    if (e.kind === "no_inductive_step") return e.status === "open";
    return false;
  }

  /* ───────────── SHA-256 / HMAC (同期) ───────────── */
  var K256 = (function () {
    var k = [], n = 2, i;
    while (k.length < 64) {
      for (i = 2; i * i <= n; i++) if (n % i === 0) break;
      if (i * i > n) k.push(Math.floor((Math.cbrt(n) % 1) * 4294967296) >>> 0);
      n++;
    }
    return k;
  })();
  function utf8(s) { return new TextEncoder().encode(s); }
  function concat() {
    var len = 0, i, o = 0;
    for (i = 0; i < arguments.length; i++) len += arguments[i].length;
    var out = new Uint8Array(len);
    for (i = 0; i < arguments.length; i++) { out.set(arguments[i], o); o += arguments[i].length; }
    return out;
  }
  function sha256(msg) {
    if (typeof msg === "string") msg = utf8(msg);
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var l = msg.length, total = ((l + 9 + 63) >> 6) << 6, buf = new Uint8Array(total), dv = new DataView(buf.buffer);
    buf.set(msg); buf[l] = 0x80;
    dv.setUint32(total - 8, Math.floor(l / 536870912)); dv.setUint32(total - 4, (l * 8) >>> 0);
    var w = new Uint32Array(64), off, i, a, b, c, d, e, f, g, hh, s0, s1, t1, t2;
    function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }
    for (off = 0; off < total; off += 64) {
      for (i = 0; i < 16; i++) w[i] = dv.getUint32(off + 4 * i);
      for (i = 16; i < 64; i++) {
        s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
        s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
      }
      a = h[0]; b = h[1]; c = h[2]; d = h[3]; e = h[4]; f = h[5]; g = h[6]; hh = h[7];
      for (i = 0; i < 64; i++) {
        t1 = (hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K256[i] + w[i]) >>> 0;
        t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
        hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0; h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
      h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0; h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
    }
    var out = new Uint8Array(32), odv = new DataView(out.buffer);
    for (i = 0; i < 8; i++) odv.setUint32(4 * i, h[i]);
    return out;
  }
  function hmac(key, msg) {
    if (key.length > 64) key = sha256(key);
    var ip = new Uint8Array(64).fill(0x36), op = new Uint8Array(64).fill(0x5c), i;
    for (i = 0; i < key.length; i++) { ip[i] ^= key[i]; op[i] ^= key[i]; }
    return sha256(concat(op, sha256(concat(ip, msg))));
  }
  function hex(b) { return Array.prototype.map.call(b, function (x) { return (x < 16 ? "0" : "") + x.toString(16); }).join(""); }
  function unhex(s) { var o = new Uint8Array(s.length / 2); for (var i = 0; i < o.length; i++) o[i] = parseInt(s.substr(2 * i, 2), 16); return o; }

  /* ───────────── Jones 多項式 (Kauffman ブラケット) と暗号 ───────────── */
  function lAdd(a, b) { var o = new Map(a); b.forEach(function (v, e) { o.set(e, (o.get(e) || 0) + v); }); return lClean(o); }
  function lMul(a, b) {
    var o = new Map();
    a.forEach(function (v1, e1) { b.forEach(function (v2, e2) { o.set(e1 + e2, (o.get(e1 + e2) || 0) + v1 * v2); }); });
    return lClean(o);
  }
  function lClean(m) { m.forEach(function (v, e) { if (v === 0) m.delete(e); }); return m; }
  function normalizedBracket(braid) {
    var n = Math.max.apply(null, braid.map(Math.abs)) + 1, c = braid.length, total = new Map();
    var D = new Map([[2, -1], [-2, -1]]);
    for (var state = 0; state < (1 << c); state++) {
      var parent = [], fresh = function () { parent.push(parent.length); return parent.length - 1; };
      var find = function (x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
      var union = function (a, b) { a = find(a); b = find(b); if (a !== b) parent[a] = b; };
      var bottom = [], cur, aExp = 0, k, i;
      for (i = 0; i < n; i++) bottom.push(fresh());
      cur = bottom.slice();
      for (k = 0; k < c; k++) {
        var g = braid[k], a = Math.abs(g) - 1, b = a + 1, choice = (state >> k) & 1;
        aExp += choice === 0 ? 1 : -1;
        if (g > 0 ? choice === 1 : choice === 0) {
          union(cur[a], cur[b]);
          var na = fresh(), nb = fresh(); union(na, nb); cur[a] = na; cur[b] = nb;
        }
      }
      for (i = 0; i < n; i++) union(cur[i], bottom[i]);
      var roots = new Set(); for (i = 0; i < parent.length; i++) roots.add(find(i));
      var term = new Map([[aExp, 1]]);
      for (i = 1; i < roots.size; i++) term = lMul(term, D);
      total = lAdd(total, term);
    }
    var w = braid.reduce(function (s, g) { return s + (g > 0 ? 1 : -1); }, 0);
    return lMul(new Map([[-3 * w, (((-w) % 2) + 2) % 2 ? -1 : 1]]), total);
  }
  function canonical(l) { return Array.from(l.entries()).sort(function (x, y) { return x[0] - y[0]; }); }
  function jonesStr(braid) {
    var V = new Map();
    normalizedBracket(braid).forEach(function (v, e) { V.set(-e / 4, (V.get(-e / 4) || 0) + v); });
    var ks = Array.from(V.keys()).filter(function (k) { return V.get(k) !== 0; }).sort(function (a, b) { return a - b; });
    if (!ks.length) return "0";
    return ks.map(function (e) { return (V.get(e) > 0 ? "+" : "") + V.get(e) + "*t^" + e; }).join(" ");
  }
  function braidKey(braid) {
    return sha256("jones-qkd|" + canonical(normalizedBracket(braid)).map(function (p) { return p[0] + ":" + p[1]; }).join(";"));
  }
  function keystream(key, n, nonce) {
    var out = new Uint8Array(n), off = 0, counter = 0, ctr, block;
    while (off < n) {
      ctr = new Uint8Array(8); new DataView(ctr.buffer).setUint32(4, counter++);
      block = hmac(key, concat(nonce, ctr));
      out.set(block.subarray(0, Math.min(32, n - off)), off); off += 32;
    }
    return out;
  }
  function jonesEncrypt(key, plain, nonce) {
    if (!nonce) {
      nonce = new Uint8Array(16);
      if (global.crypto && global.crypto.getRandomValues) global.crypto.getRandomValues(nonce);
      else for (var i = 0; i < 16; i++) nonce[i] = Math.floor(Math.random() * 256);
    }
    var ks = keystream(key, plain.length, nonce), ct = plain.map(function (p, i) { return p ^ ks[i]; });
    return concat(nonce, hmac(key, concat(utf8("tag|"), nonce, ct)), ct);
  }
  function jonesDecrypt(key, blob) {
    var nonce = blob.subarray(0, 16), tag = blob.subarray(16, 48), ct = blob.subarray(48);
    if (hex(hmac(key, concat(utf8("tag|"), nonce, ct))) !== hex(tag)) throw new Error("authentication failed (wrong Jones key?)");
    var ks = keystream(key, ct.length, nonce);
    return ct.map(function (c, i) { return c ^ ks[i]; });
  }
  function fingerprint(key) { return hex(sha256(key)).slice(0, 16); }

  /* ───────────── 証明書・封印 ───────────── */
  var SOUNDNESS = "本アプリはリーマン予想・深リーマン予想を証明しない。両者は未解決問題である。" +
    "「verified」は有限範囲の主張を倍精度浮動小数点で数値検証したという意味であり、" +
    "区間演算による厳密証明でも、予想全体の証明でもない。";
  function stable(v) {
    if (Array.isArray(v)) return "[" + v.map(stable).join(",") + "]";
    if (v && typeof v === "object")
      return "{" + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ":" + stable(v[k]); }).join(",") + "}";
    return JSON.stringify(v === undefined ? null : v);
  }
  function digest(cert) {
    var body = {}; Object.keys(cert).forEach(function (k) { if (k !== "seal") body[k] = cert[k]; });
    return sha256(stable(body));
  }
  function buildCertificate(rh, sch, drh, quantum, induction) {
    var cert = {
      engine: "BadaGPT (未知事前エンジン規約: proved / disproved / open)",
      verdicts: { riemann_hypothesis: "open", deep_riemann_hypothesis: "open",
                  rh_up_to_height: rh.status, schoenfeld_inequality: sch.status },
      rh_bounded: rh, schoenfeld: sch, drh_evidence: drh, soundness: SOUNDNESS
    };
    if (quantum) cert.quantum_search = quantum;
    if (induction) cert.induction = induction;
    return cert;
  }
  function seal(cert, braid) {
    braid = braid || [1, 1, 1];
    var key = braidKey(braid);
    delete cert.seal;
    cert.seal = { braid: braid, jones_polynomial: jonesStr(braid), key_fingerprint: fingerprint(key),
                  sealed_digest: hex(jonesEncrypt(key, digest(cert))) };
    return cert;
  }
  function checkSeal(cert, braid) {
    try {
      if (!cert.seal) return false;
      return hex(jonesDecrypt(braidKey(braid || cert.seal.braid), unhex(cert.seal.sealed_digest))) === hex(digest(cert));
    } catch (e) { return false; }
  }

  /* ───────────── 証明書 PatchGuard (書き換えの門) ───────────── */
  var SEV = { critical: 3, high: 2, medium: 1, low: 0 };
  function flatten(o, prefix, out) {
    out = out || {}; prefix = prefix || "";
    if (o && typeof o === "object") Object.keys(o).forEach(function (k) { flatten(o[k], prefix + "/" + k, out); });
    else out[prefix] = o;
    return out;
  }
  function diff(base, after) {
    var a = flatten(base), b = flatten(after), out = {};
    Object.keys(Object.assign({}, a, b)).sort().forEach(function (p) { if (a[p] !== b[p]) out[p] = [a[p], b[p]]; });
    return out;
  }
  function invariants(base, cert, recompute) {
    var out = [], f = function (id, sev, why) { out.push({ id: id, severity: sev, why: why }); };
    var v = cert.verdicts || {};
    [["riemann_hypothesis", "リーマン予想"], ["deep_riemann_hypothesis", "深リーマン予想"]].forEach(function (p) {
      if (v[p[0]] !== "open") f("RG01", "critical", p[1] + "の判定が " + JSON.stringify(v[p[0]]) + "。検査可能な証明なしに未解決以外へは書き換えられない");
    });
    var rh = cert.rh_bounded || {};
    if (rh.status === "verified" || v.rh_up_to_height === "verified") {
      var n = rh.zeros_in_strip_argument_principle, m = rh.zeros_on_critical_line_sign_changes;
      if (n === undefined || n !== m || !(rh.argument_principle_residual < 1e-3))
        f("RG02", "critical", "高さ " + rh.height + " まで検証済みとあるが、零点総数 " + n + " と線上の個数 " + m + " が裏付けない");
      else if (recompute) {
        var got = zeroCount(+rh.height)[0];
        if (got !== n) f("RG03", "critical", "再計算した N(" + rh.height + ") = " + got + " が記載の " + n + " と一致しない");
      }
    }
    var sch = cert.schoenfeld || {};
    if (sch.status === "verified" && !(sch.max_ratio < 1)) f("RG04", "high", "Schoenfeld 不等式が検証済みとあるが最大比 " + sch.max_ratio + " が 1 以上");
    (cert.drh_evidence || []).forEach(function (d, i) {
      if (d.status !== "open") f("RG05", "critical", "深リーマン予想の証拠 #" + i + " の判定が " + JSON.stringify(d.status) + "。有限の部分積は証明にならない");
    });
    (cert.quantum_search || []).forEach(function (q) {
      if (q.status === "disproved") {
        if (!PROBLEMS[q.problem] || q.counterexample == null || !isCounterexample(q.problem, q.counterexample))
          f("RG10", "critical", q.problem + ": 反証とあるが、反例 " + JSON.stringify(q.counterexample) + " が古典的な再検査を通らない");
      } else if (q.status !== "open") f("RG10", "critical", q.problem + ": 判定が " + JSON.stringify(q.status) + "。有限範囲の量子探索は予想の証明にならない");
    });
    (cert.induction || []).forEach(function (e, i) {
      var ok; try { ok = recheck(e); } catch (err) { ok = false; }
      if (!ok) f("RG11", "critical", "帰納法の項目 #" + i + " (" + e.kind + ") の判定 " + JSON.stringify(e.status) + " が再導出と一致しない");
    });
    if (cert.soundness !== SOUNDNESS) f("RG06", "high", "健全性の注記が削除または変更されている");
    if (!cert.seal) f("RG07", "medium", "Jones 暗号による封印がない");
    else if (!checkSeal(cert)) f("RG07", "high", "封印が内容と一致しない（封印後に書き換えられている）");
    if (base) {
      [["零点検証の高さ", "rh_bounded", "height"], ["Schoenfeld 検査の上限", "schoenfeld", "limit"]].forEach(function (p) {
        var o = (base[p[1]] || {})[p[2]], nw = (cert[p[1]] || {})[p[2]];
        if (o !== undefined && (nw === undefined || nw < o)) f("RG08", "medium", p[0] + "が " + o + " から " + nw + " へ縮小している");
      });
      if ((cert.drh_evidence || []).length < (base.drh_evidence || []).length) f("RG09", "medium", "深リーマン予想の証拠が削除されている");
    }
    return out;
  }
  function gate(findings) {
    var worst = -1; findings.forEach(function (x) { worst = Math.max(worst, SEV[x.severity]); });
    return worst >= 2 ? "REJECT" : worst === 1 ? "REVIEW" : "ACCEPT";
  }
  function guard(stages, recompute) {
    var run = hex(sha256(stable(stages))).slice(0, 12), tuples = [], per = [], k;
    stages.forEach(function (c, i) { tuples.push(["cert", run, i, hex(sha256(stable(c)))]); });
    for (k = 1; k < stages.length; k++) {
      tuples.push(["patch", run, k, hex(sha256(stable(stages[k - 1]))), hex(sha256(stable(stages[k]))), Object.keys(diff(stages[k - 1], stages[k])).length]);
      per.push(invariants(stages[k - 1], stages[k]));
    }
    var base = stages.length > 1 ? stages[0] : null, net = invariants(base, stages[stages.length - 1], recompute);
    var ids = new Set(net.map(function (x) { return x.id + "|" + x.why; })), cancelled = [];
    per.slice(0, -1).forEach(function (fs) { fs.forEach(function (x) { if (!ids.has(x.id + "|" + x.why)) cancelled.push(x); }); });
    net.forEach(function (x) { tuples.push(["finding", run, "net", x.id, x.severity, x.why]); });
    cancelled.forEach(function (x) { tuples.push(["finding", run, "cancelled", x.id, x.severity, x.why]); });
    var verdict = gate(net); tuples.push(["gate", run, verdict]);
    return { run: run, verdict: verdict, findings: net, cancelled: cancelled,
             net_patch: base ? diff(base, stages[stages.length - 1]) : {}, tuples: tuples };
  }

  function fullCertificate(opt) {
    opt = opt || {};
    var X = opt.limit || 1e6, drh = Object.keys(CHARACTERS).map(function (c) { return drhEvidence(c, 0, X); });
    drh.push(drhEvidence("chi_-4", 1, X));
    return seal(buildCertificate(verifyRH(opt.height || 500), schoenfeld(X), drh,
                                 quantumSearchAll(opt.qubits || 10, opt.seed || 0), inductionReport(opt.sieveBits || 12)),
                opt.braid || [1, 1, 1]);
  }

  global.BadaGPTEngine = {
    hurwitz: hurwitz, zeta: zeta, dirichletL: dirichletL, theta: theta, hardyZ: hardyZ,
    zeroCount: zeroCount, verifyRH: verifyRH, schoenfeld: schoenfeld, CHARACTERS: CHARACTERS, drhEvidence: drhEvidence,
    groverSearch: groverSearch, PROBLEMS: PROBLEMS, isCounterexample: isCounterexample,
    quantumSearch: quantumSearch, quantumSearchAll: quantumSearchAll,
    pParse: pParse, pStr: pStr, proveSum: proveSum, repairSum: repairSum, collatzDescent: collatzDescent,
    inductionReport: inductionReport, recheck: recheck,
    sha256: sha256, hmac: hmac, hex: hex, braidKey: braidKey, jonesStr: jonesStr, fingerprint: fingerprint,
    SOUNDNESS: SOUNDNESS, buildCertificate: buildCertificate, seal: seal, checkSeal: checkSeal,
    invariants: invariants, gate: gate, guard: guard, fullCertificate: fullCertificate
  };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaGPTEngine;
})(typeof window !== "undefined" ? window : globalThis);
