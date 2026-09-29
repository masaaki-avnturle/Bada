/*
 * physics.js — CONTACT TRANSPORTER の設計パラメータ計算エンジン
 *
 * 「異次元への輸送機 3 次元設計図書」(contact_blueprint.pdf) 第 1 章の値を
 * 論文の方程式から再計算します。ブラウザ (window.CTPhys) と Node (module.exports)
 * の両方で動きます。
 *
 *   ① 衝突段      √s, E_T^miss, 扉の軸 n̂
 *   ② 特殊相対論  Γ = 18 h / 1 s, 1−β, ラピディティ φ = arcosh Γ, ベガまでの片道
 *   ②' 輸送計量   e^{−2πT|ψ|} = 1/Γ → T|ψ|,  x log x = 1 の根
 *   ③ 複素回転体  Θ = θ + iφ, ジンバル角速度, ポッド歳差 Ω = Mgl/(I₃ω₃)
 *   ④ Γ・ζ 多様体 Riemann–Siegel θ(φ), Z(φ) = e^{iθ(φ)} ζ(½ + iφ)
 *   ⑤ Jones 多項式 V_K(t*) (t* = e^{iθ(φ)}), 共鳴窓 = |V_K(e^{iα})| の極小
 *   UFO 系        反重力係数 L = cosh(x log x), a = (L−1)·g_eff, 上昇シミュレーション
 *
 * ※ 論文の方程式に基づく思索的・フィクションの設計 (幾何的な可視化) です。
 */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------- complex
  const C = (re, im) => ({ re, im: im || 0 });
  const cadd = (a, b) => C(a.re + b.re, a.im + b.im);
  const csub = (a, b) => C(a.re - b.re, a.im - b.im);
  const cmul = (a, b) => C(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
  const cdiv = (a, b) => {
    const d = b.re * b.re + b.im * b.im;
    return C((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d);
  };
  const cexp = (a) => { const e = Math.exp(a.re); return C(e * Math.cos(a.im), e * Math.sin(a.im)); };
  const cabs = (a) => Math.hypot(a.re, a.im);
  const cpowReal = (base, s) => cexp(C(s.re * Math.log(base), s.im * Math.log(base))); // base^s, base>0
  const cpowInt = (z, n) => {
    let r = C(1, 0), b = n < 0 ? cdiv(C(1, 0), z) : z;
    for (let k = Math.abs(n); k > 0; k--) r = cmul(r, b);
    return r;
  };
  const fmtC = (z, p) => {
    p = p || 6;
    const tiny = 1e-12 * Math.max(1, Math.abs(z.re), Math.abs(z.im));
    const re = Math.abs(z.re) < tiny ? 0 : +z.re.toPrecision(p);
    const im = Math.abs(z.im) < tiny ? 0 : +z.im.toPrecision(p);
    return im === 0 ? String(re) : `${re} ${im < 0 ? "−" : "+"} ${Math.abs(im)}i`;
  };

  // ---------------------------------------------------------------- constants
  const K = {
    c: 299792458, G: 6.674e-11, hbar: 1.054571817e-34,
    ly_km: 9.4607304725808e12, M_earth: 5.972e24, r_earth: 6.371e6,
    GM: 3.986004418e14, g0: 9.80665,
  };

  // ---------------------------------------------------------------- ζ / θ / Z
  // Dirichlet η を Borwein のアルゴリズムで評価し ζ(s) = η(s)/(1 − 2^{1−s})。
  // 臨界線上 |t| ≲ 60 で十分な精度 (n = 60)。
  function zeta(s, n) {
    n = n || 60;
    const d = new Array(n + 1);
    let sum = 0;
    for (let i = 0; i <= n; i++) {
      let term = 1;
      // d_k = n Σ_{i=0}^{k} (n+i−1)! 4^i / ((n−i)! (2i)!)
      term = factRatio(n, i);
      sum += term;
      d[i] = n * sum;
    }
    let acc = C(0, 0);
    for (let k = 0; k < n; k++) {
      const sign = k % 2 === 0 ? 1 : -1;
      const coef = sign * (d[k] - d[n]);
      acc = cadd(acc, cmul(C(coef, 0), cdiv(C(1, 0), cpowReal(k + 1, s))));
    }
    const eta = cmul(acc, C(-1 / d[n], 0));
    const denom = csub(C(1, 0), cpowReal(2, C(1 - s.re, -s.im)));
    return cdiv(eta, denom);
  }
  function factRatio(n, i) { // (n+i−1)! 4^i / ((n−i)! (2i)!)
    let lg = lgammaR(n + i) + i * Math.log(4) - lgammaR(n - i + 1) - lgammaR(2 * i + 1);
    return Math.exp(lg);
  }
  // 実数の log Γ (Lanczos)
  function lgammaR(x) {
    const g = 7, p = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
      771.32342877765313, -176.61502916214059, 12.507343278686905,
      -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lgammaR(1 - x);
    x -= 1;
    let a = p[0];
    const t = x + g + 0.5;
    for (let i = 1; i < g + 2; i++) a += p[i] / (x + i);
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
  }
  // 実数 Γ(x)
  function gammaR(x) {
    if (x < 0.5) return Math.PI / (Math.sin(Math.PI * x) * gammaR(1 - x));
    return Math.exp(lgammaR(x));
  }
  const betaR = (p, q) => gammaR(p) * gammaR(q) / gammaR(p + q);
  const digamma1 = 1 - 0.5772156649015329; // Γ'(2) = 1 − γ  (= 0.422784, ACAFE.5/7)

  // Riemann–Siegel θ(t) (漸近展開)
  function rsTheta(t) {
    return t / 2 * Math.log(t / (2 * Math.PI)) - t / 2 - Math.PI / 8
      + 1 / (48 * t) + 7 / (5760 * t ** 3) + 31 / (80640 * t ** 5);
  }
  // Z(t) = e^{iθ(t)} ζ(½ + it)  (実数値)
  function rsZ(t) {
    const z = cmul(cexp(C(0, rsTheta(t))), zeta(C(0.5, t)));
    return z.re;
  }

  // ---------------------------------------------------------------- Jones
  // Laurent 多項式を {指数: 係数} で保持
  const JONES = {
    "3_1": { name: "三葉結び目 (trefoil)", terms: { "-4": -1, "-3": 1, "-1": 1 }, p: 2, q: 3 },
    "4_1": { name: "8 の字結び目 (figure-eight)", terms: { "-2": 1, "-1": -1, "0": 1, "1": -1, "2": 1 } },
    "5_1": { name: "五葉結び目 (cinquefoil)", terms: { "2": 1, "4": 1, "5": -1, "6": 1, "7": -1 }, p: 2, q: 5 },
  };
  function jonesEval(key, t) {
    let r = C(0, 0);
    for (const [e, c] of Object.entries(JONES[key].terms)) r = cadd(r, cmul(C(c, 0), cpowInt(t, +e)));
    return r;
  }
  function jonesString(key) {
    const parts = Object.entries(JONES[key].terms).sort((a, b) => +a[0] - +b[0]).map(([e, c], i) => {
      const mon = +e === 0 ? "1" : `t^${e}`;
      const sgn = c < 0 ? "−" : (i ? "+" : "");
      return `${sgn}${i ? " " : ""}${mon}`;
    });
    return parts.join(" ").replace(/^\s+/, "");
  }
  // |V_K(e^{iα})| の極小 (α in degrees) → 扉の共鳴窓
  function resonanceMinima(key, step) {
    step = step || 0.5;
    const vals = [];
    for (let a = 0; a < 360; a += step) vals.push([a, cabs(jonesEval(key, cexp(C(0, a * Math.PI / 180))))]);
    const mins = [];
    for (let i = 0; i < vals.length; i++) {
      const p = vals[(i - 1 + vals.length) % vals.length][1], c = vals[i][1], n = vals[(i + 1) % vals.length][1];
      if (c < p && c <= n) mins.push({ alpha: vals[i][0], mag: c });
    }
    return { curve: vals, minima: mins };
  }

  // ---------------------------------------------------------------- x log x
  function solveXlogX(target) { // x log x = target の根 (x > 1)
    let x = 2;
    for (let i = 0; i < 60; i++) x -= (x * Math.log(x) - target) / (Math.log(x) + 1);
    return x;
  }

  // ---------------------------------------------------------------- blueprint
  function blueprint(opts) {
    opts = Object.assign({
      earthSeconds: 1, riderHours: 18, sqrtS_TeV: 13.6, METGeV: 1348.29,
      doorAxis: [0.86964, -0.25101, 0.42511], targetLy: 25.04, targetName: "ベガ",
      theta0: Math.PI / 6, omegaOuter: Math.PI / 30,
      podMass: 12000, podRadius: 5.021,
    }, opts || {});
    const Gam = opts.riderHours * 3600 / opts.earthSeconds;
    const oneMinusBeta = 1 - Math.sqrt(1 - 1 / (Gam * Gam));
    const phi = Math.acosh(Gam);
    const distKm = opts.targetLy * K.ly_km / Gam;
    const oneWayH = opts.targetLy * 365.25 * 24 / Gam; // β≈1
    const TPsi = Math.log(Gam) / (2 * Math.PI);
    const xlogxRoot = solveXlogX(1);
    const ratio = phi / Math.PI; // ジンバル段間の角速度比
    const omega = [opts.omegaOuter, opts.omegaOuter * ratio, opts.omegaOuter * ratio * ratio];
    const theta = rsTheta(phi);
    const Z = rsZ(phi);
    const tStar = cexp(C(0, theta));
    const jones = {};
    for (const k of Object.keys(JONES)) {
      const v = jonesEval(k, tStar);
      jones[k] = { poly: jonesString(k), value: v, str: fmtC(v), mag: cabs(v), resonance: resonanceMinima(k, 1).minima };
    }
    // ポッド歳差 Ω = Mgl/(I₃ω₃), 球殻ポッド I₃ = (2/5) M r², l = ポッド中心〜支点
    const armL = opts.armLength != null ? opts.armLength : 5.60424;
    const I3 = 0.4 * opts.podMass * opts.podRadius ** 2;
    const Omega = opts.podMass * K.g0 * armL / (I3 * omega[2]);
    const n = opts.doorAxis, nl = Math.hypot(n[0], n[1], n[2]);
    return {
      opts, Gamma: Gam, oneMinusBeta, phi, distKm, oneWayH, TPsi, xlogxRoot,
      Theta: { re: opts.theta0, im: phi }, omega, Omega, armL,
      rsTheta: theta, Z, tStar, jones,
      doorAxis: n.map((v) => v / nl),
      // 部品寸法 [m] (設計図書 ⑦ — 方程式群の数値エネルギー Σ log(1+|v|) で変調済みの値)
      dims: Object.assign({
        ringOuter: 60.088, ringMid: 47.431, ringInner: 37.440, tube: 2.066,
        podR: opts.podRadius, tower: 132.194, well: 38.800,
        coil31: 70.269, coil51: 56.215, coil41: 30.0,
      }, opts.dims || {}),
    };
  }

  // ---------------------------------------------------------------- UFO 系
  // UFO.1–26: 反重力 (anti-gravity) 係数と上昇モデル
  //   x = manifold_coord(r0/r) = 1 + r0/r        (UFO.14: 地表で x = 2)
  //   L = E_ag/U_grav = cosh(x log x)            (UFO.11/19: 地表 2.125)
  //   a = (L − 1) · g_eff,  g_eff = GM/r²        (UFO.19: 11.047 m/s²)
  const ufo = {
    manifoldX: (h) => 1 + K.r_earth / (K.r_earth + h),
    L(h) { const x = this.manifoldX(h); return Math.cosh(x * Math.log(x)); },
    gEff: (h) => K.GM / (K.r_earth + h) ** 2,
    accel(h, gain) { return (this.L(h) - 1) * this.gEff(h) * (gain == null ? 1 : gain); },
    Ugrav: (m, h) => K.GM * m / (K.r_earth + h),
    Eag(m, h) { return this.Ugrav(m, h) * this.L(h); },
    Eperp: (m, v) => m * K.c * K.c - 0.5 * m * v * v,
    // 半陰的オイラー: v += a dt; h += v dt   (UFO.24: 10 ステップで 607.6 m, 110.46 m/s)
    ascend(steps, dt, gain) {
      let h = 0, v = 0; const tr = [{ t: 0, h, v }];
      for (let i = 1; i <= steps; i++) { v += this.accel(h, gain) * dt; h += v * dt; tr.push({ t: i * dt, h, v }); }
      return tr;
    },
  };

  const api = {
    C, cadd, csub, cmul, cdiv, cexp, cabs, cpowInt, fmtC, K,
    zeta, rsTheta, rsZ, gammaR, lgammaR, betaR, digamma1,
    JONES, jonesEval, jonesString, resonanceMinima, solveXlogX, blueprint, ufo,
  };
  root.CTPhys = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
