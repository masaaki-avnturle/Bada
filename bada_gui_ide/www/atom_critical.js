/* ============================================================================
 * atom_critical.js — 原子の臨界期の強度シミュレータ (ACPI) のモデルコア
 *   Atomic Critical-Period Intensity core model
 *
 * 「臨界期」= 強レーザー場のなかで原子のクーロン障壁が完全に抑制され
 * (over-the-barrier)、束縛状態がもはや保護されない時間窓。
 * 「強度」= その時間窓での場の強度 I(t) [W/cm^2]。
 *
 * 二層構成:
 *  (A) 物理層 — 標準的な強場原子物理。原子単位系での障壁抑制場
 *      F_cr = I_p^2/(4 Z_c)、ADK トンネル電離率、Keldysh パラメータ、
 *      ポンデロモーティブエネルギー、瞬時場の時間積分。
 *  (B) Ω 層 — 山口フレームワーク (Bada / omega_llm) の作用素層:
 *      zeta 半径  ζ(s) = β(p,q)/log x,  ζ_n = (x log x)^n
 *      gamma-deprivation      e^{-x log x}
 *      Dalanversian / 反重力  Λ = cos(i x log x) - i sin(i x log x) = e^{x log x}
 *      均衡余裕                e^f + e^{-f} - (e^f - e^{-f}) = 2 e^{-f}
 *      Euler 極均衡            x^n + y^n - n x y z = 0
 *      Kauffman ブラケット     <D>(A) = Σ_states A^{a-b} d^{loops-1}
 *      臨界強度指数            E(σ) = K(σ) × H(σ) / (4 (π_n, e_n))
 *
 * ブラウザ (dist/atom-critical.html に inline) と Node (cli/) の両方で動く
 * UMD モジュール。依存なし。
 * ==========================================================================*/
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.AtomCritical = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var VERSION = "1.0.0";

  /* ===================== 物理定数 (CODATA 2018) ===================== */
  var C_LIGHT = 2.99792458e8;            /* m/s                        */
  var EPS0 = 8.8541878128e-12;           /* F/m                        */
  var E_HARTREE = 27.211386245988;       /* eV / hartree               */
  var A0 = 5.29177210903e-11;            /* m (Bohr)                   */
  var T_AU = 2.4188843265857e-17;        /* s / a.u. of time           */
  var F_AU = 5.14220674763e11;           /* V/m  (atomic field unit)   */
  var HC_EVNM = 1239.841984;             /* eV*nm                      */
  /* 原子単位の強度 I_a = (1/2) eps0 c F_au^2 -> W/cm^2 (1e-4 m^2/cm^2) */
  var I_AU = 0.5 * EPS0 * C_LIGHT * F_AU * F_AU * 1e-4;   /* 3.5094e16 */
  var FS_AU = 1e-15 / T_AU;              /* 1 fs = 41.3414 a.u.        */

  /* ===================== 元素データ =====================
     Ip: 逐次イオン化エネルギー [eV] (NIST)。 l: 最外殻電子の軌道角運動量。 */
  var ELEMENTS = [
    { sym: "H",  name: "水素",       Z: 1,  l: 0, Ip: [13.5984] },
    { sym: "He", name: "ヘリウム",   Z: 2,  l: 0, Ip: [24.5874, 54.4178] },
    { sym: "Li", name: "リチウム",   Z: 3,  l: 0, Ip: [5.3917, 75.6400, 122.4543] },
    { sym: "Be", name: "ベリリウム", Z: 4,  l: 0, Ip: [9.3227, 18.2112, 153.8961, 217.7186] },
    { sym: "C",  name: "炭素",       Z: 6,  l: 1, Ip: [11.2603, 24.3833, 47.8878, 64.4939, 392.087] },
    { sym: "N",  name: "窒素",       Z: 7,  l: 1, Ip: [14.5341, 29.6013, 47.4453, 77.4735, 97.8902] },
    { sym: "O",  name: "酸素",       Z: 8,  l: 1, Ip: [13.6181, 35.1211, 54.9355, 77.4135, 113.899] },
    { sym: "Ne", name: "ネオン",     Z: 10, l: 1, Ip: [21.5645, 40.9630, 63.4233, 97.1900, 126.247] },
    { sym: "Na", name: "ナトリウム", Z: 11, l: 0, Ip: [5.1391, 47.2864, 71.6200] },
    { sym: "Ar", name: "アルゴン",   Z: 18, l: 1, Ip: [15.7596, 27.6297, 40.7350, 59.5800, 74.8400] },
    { sym: "Kr", name: "クリプトン", Z: 36, l: 1, Ip: [13.9996, 24.3599, 36.9500, 52.5000, 64.7000] },
    { sym: "Xe", name: "キセノン",   Z: 54, l: 1, Ip: [12.1298, 20.9750, 31.0500, 42.2000, 54.1400] }
  ];

  function element(sym) {
    for (var i = 0; i < ELEMENTS.length; i++)
      if (ELEMENTS[i].sym.toLowerCase() === String(sym).toLowerCase()) return ELEMENTS[i];
    return null;
  }

  /* ===================== 数学ユーティリティ ===================== */
  /* Lanczos 近似による Γ(z) (z > 0) */
  var LANCZOS = [
    676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7
  ];
  function gammaFn(z) {
    if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gammaFn(1 - z));
    z -= 1;
    var x = 0.99999999999980993;
    for (var i = 0; i < LANCZOS.length; i++) x += LANCZOS[i] / (z + i + 1);
    var t = z + LANCZOS.length - 0.5;
    return Math.sqrt(2 * Math.PI) * Math.pow(t, z + 0.5) * Math.exp(-t) * x;
  }
  /* β(p,q) = Γ(p)Γ(q)/Γ(p+q) — フレームワークのベータ関数 */
  function betaFn(p, q) { return gammaFn(p) * gammaFn(q) / gammaFn(p + q); }

  /* ===================== (A) 物理層 ===================== */

  /* 障壁抑制場 F_cr [a.u.] = I_p^2 / (4 Z_c)   (I_p は a.u.) */
  function criticalFieldAU(IpAU, Zc) { return IpAU * IpAU / (4 * Zc); }

  /* 障壁抑制強度 (BSI) [W/cm^2]。H では 1.37e14 W/cm^2 を再現する。 */
  function criticalIntensity(IpEV, Zc) {
    var F = criticalFieldAU(IpEV / E_HARTREE, Zc || 1);
    return F * F * I_AU;
  }

  /* ポンデロモーティブエネルギー U_p [eV] (直線偏光) */
  function ponderomotive(IWcm2, lambdaNm) {
    var lamUm = lambdaNm / 1000;
    return 9.33744e-14 * IWcm2 * lamUm * lamUm;
  }

  /* Keldysh パラメータ γ = sqrt(I_p / 2U_p) */
  function keldysh(IpEV, IWcm2, lambdaNm) {
    var Up = ponderomotive(IWcm2, lambdaNm);
    return Up > 0 ? Math.sqrt(IpEV / (2 * Up)) : Infinity;
  }

  /* ADK パラメータ: n* = Z_c/κ, κ = sqrt(2 I_p), |C_{n*l*}|^2 = 2^{2n*}/(n* Γ(2n*)) */
  function adkParams(IpEV, Zc, l) {
    var Ip = IpEV / E_HARTREE;
    var kappa = Math.sqrt(2 * Ip);
    var nstar = Zc / kappa;
    var Cn2 = Math.pow(2, 2 * nstar) / (nstar * gammaFn(2 * nstar));
    return { Ip: Ip, kappa: kappa, nstar: nstar, Cn2: Cn2, flm: 2 * l + 1 };
  }

  /* 瞬時 (準静的) ADK 電離率 [a.u.^-1]
     w = |C|^2 f_{l0} I_p (2κ^3/F)^{2n*-1} exp(-2κ^3/(3F))
     H (n*=1) では厳密な w = (4/F) e^{-2/(3F)} に一致する。 */
  function adkRate(F, ap) {
    F = Math.abs(F);
    if (F < 1e-12) return 0;
    var k3 = ap.kappa * ap.kappa * ap.kappa;
    var arg = 2 * k3 / F;
    var expo = Math.exp(-arg / 3);
    if (!isFinite(expo) || expo === 0) return 0;
    var w = ap.Cn2 * ap.flm * ap.Ip * Math.pow(arg, 2 * ap.nstar - 1) * expo;
    return isFinite(w) ? w : 0;
  }
  /* サイクル平均 ADK 率 (参考値): × sqrt(3F/(π κ^3)) */
  function adkRateCycleAvg(F, ap) {
    var k3 = ap.kappa * ap.kappa * ap.kappa;
    return adkRate(F, ap) * Math.sqrt(3 * Math.abs(F) / (Math.PI * k3));
  }

  /* ===================== (B) Ω 層 ===================== */

  /* ζ_n(x) = (x log x)^n  — 20250330 / caostics の ζ(s) = (x log x)^n */
  function zetaN(x, n) {
    if (x <= 0) return 0;
    var u = x * Math.log(x);
    return Math.pow(u, n);
  }
  /* gamma-deprivation  D(x) = e^{-x log x}  (README: ⊕(iℏ∇)^⊕L = e^{-x log x}) */
  function gammaDeprivation(x) {
    if (x <= 0) return 1;
    return Math.exp(-x * Math.log(x));
  }
  /* Dalanversian Λ = cos(i u) - i sin(i u) = cosh u + sinh u = e^u,  u = x log x */
  function dalanversian(x) {
    if (x <= 0) return 1;
    return Math.exp(x * Math.log(x));
  }
  /* 反重力 Λ^- = 2(cos(i u) + sin(i u)) の実部 2 cosh u */
  function antigravity(x) {
    if (x <= 0) return 2;
    return 2 * Math.cosh(x * Math.log(x));
  }
  /* 均衡余裕: e^f + e^{-f} >= e^f - e^{-f} の余裕 = 2 e^{-f},  f = x log x
     臨界期では f が急増し余裕が 0 に潰れる = 重力/反重力均衡の喪失。 */
  function balanceMargin(x) {
    if (x <= 0) return 2;
    return 2 * Math.exp(-x * Math.log(x));
  }
  /* Euler 極均衡残差  R = x^n + y^n - n x y z   (20250330 / caostics) */
  function eulerResidual(x, y, z, n) {
    return Math.pow(x, n) + Math.pow(y, n) - n * x * y * z;
  }

  /* --- Kauffman ブラケット状態和 (zone.bada / omega_jones_crypto と同一構成)
     交差は [e0,e1,e2,e3] (反時計回り)。A-平滑化は e0-e1 と e2-e3 を、
     B-平滑化は e1-e2 と e3-e0 を結ぶ。
     <D>(A) = Σ_states A^{a-b} d^{loops-1},  d = -A^2 - A^{-2}          */
  function ufFind(parent, x) { while (parent[x] >= 0) x = parent[x]; return x; }
  function kauffmanBracket(cross, A) {
    var n = cross.length;
    if (n === 0) return 1;
    var maxlbl = 0, i, k;
    for (i = 0; i < n; i++) for (k = 0; k < 4; k++) if (cross[i][k] > maxlbl) maxlbl = cross[i][k];
    var U = maxlbl + 1;
    var states = Math.pow(2, n);
    var d = -(A * A) - 1 / (A * A);
    var sum = 0;
    for (var st = 0; st < states; st++) {
      var parent = new Array(U);
      for (var q = 0; q < U; q++) parent[q] = -1;
      var a_cnt = 0, b_cnt = 0;
      for (i = 0; i < n; i++) {
        var e = cross[i];
        var bit = (st >> i) & 1;
        var p1, p2, r1, r2;
        if (bit === 0) { p1 = [e[0], e[1]]; p2 = [e[2], e[3]]; a_cnt++; }
        else { p1 = [e[1], e[2]]; p2 = [e[3], e[0]]; b_cnt++; }
        r1 = ufFind(parent, p1[0]); r2 = ufFind(parent, p1[1]); if (r1 !== r2) parent[r1] = r2;
        r1 = ufFind(parent, p2[0]); r2 = ufFind(parent, p2[1]); if (r1 !== r2) parent[r1] = r2;
      }
      var seen = {}, loops = 0;
      for (var lbl = 0; lbl < U; lbl++) {
        var r = ufFind(parent, lbl);
        if (!seen[r]) { seen[r] = 1; loops++; }
      }
      sum += Math.pow(A, a_cnt - b_cnt) * Math.pow(d, loops - 1);
    }
    return sum;
  }
  /* 臨界サブ窓 c 個から閉 2-ブレイド ((2,c) トーラス絡み目) 図式を組む */
  function braidDiagram(c) {
    var cross = [];
    for (var i = 0; i < c; i++) {
      var j = (i + 1) % c;
      cross.push([i, c + i, c + j, j]);   /* SW, SE, NE, NW */
    }
    return cross;
  }
  /* π と e の n 次近似 (Leibniz / 指数級数) — E(σ) の分母 4(π_n, e_n) */
  function piApprox(n) {
    var s = 0;
    for (var k = 0; k <= n; k++) s += (k % 2 === 0 ? 1 : -1) / (2 * k + 1);
    return 4 * s;
  }
  function eApprox(n) {
    var s = 0, f = 1;
    for (var k = 0; k <= n; k++) { if (k > 0) f *= k; s += 1 / f; }
    return s;
  }
  function shannon(ps) {
    var H = 0;
    for (var i = 0; i < ps.length; i++) { var p = ps[i]; if (p > 1e-15) H += -p * Math.log(p); }
    return H;
  }

  /* ===================== パルス形状 ===================== */
  /* 強度包絡の FWHM を tau とする。振幅包絡 = sqrt(強度包絡)。 */
  function envelope(tAU, tauAU, shape) {
    var x;
    switch (shape) {
      case "sech2":
        /* I(t) = sech^2(1.7627 t/tau) */
        x = 1.7627471740390861 * tAU / tauAU;
        return 1 / Math.cosh(x);                       /* amplitude */
      case "flattop":
        /* 平坦部 tau, 両端 tau/4 の cos^2 立ち上がり/下がり */
        var half = tauAU / 2, ramp = tauAU / 4, a = Math.abs(tAU);
        if (a <= half) return 1;
        if (a >= half + ramp) return 0;
        return Math.cos(Math.PI / 2 * (a - half) / ramp);
      case "gaussian":
      default:
        /* I(t) = exp(-4 ln2 t^2/tau^2) -> amplitude exp(-2 ln2 t^2/tau^2) */
        x = tAU / tauAU;
        return Math.exp(-2 * Math.LN2 * x * x);
    }
  }

  /* ===================== パラメータ ===================== */
  var DEFAULTS = {
    element: "Ar",
    charge: 1,          /* 残留イオン電荷 Z_c (1 = 中性原子の初回電離) */
    stage: 1,           /* 何段目の電離か (1 = 第一電離)               */
    lambdaNm: 800,
    intensity: 2e14,    /* ピーク強度 I0 [W/cm^2]                      */
    fwhmFs: 10,
    shape: "gaussian",
    cep: 0,             /* キャリアエンベロープ位相 [rad]              */
    steps: 6000,
    windowFactor: 2.2,  /* 時間窓 = ±windowFactor × FWHM               */
    zetaOrder: 3,       /* Euler 極均衡 / ζ_n の n                     */
    kauffmanA: 1.0699,  /* Kauffman ブラケットのループ変数 A           */
    maxCrossings: 12,   /* 状態和は 2^12 = 4096 状態まで               */
    rateCap: 0          /* 0 なら 2*I_p [a.u.] で自動キャップ          */
  };

  function normalize(opt) {
    var p = {};
    for (var k in DEFAULTS) p[k] = DEFAULTS[k];
    for (var j in (opt || {})) if (opt[j] !== undefined && opt[j] !== null) p[j] = opt[j];
    p.stage = Math.max(1, Math.round(p.stage));
    p.charge = Math.max(1, Math.round(p.charge));
    p.steps = Math.max(200, Math.min(200000, Math.round(p.steps)));
    return p;
  }

  /* ===================== メイン: シミュレーション ===================== */
  function simulate(opt) {
    var p = normalize(opt);
    var el = element(p.element);
    if (!el) throw new Error("unknown element: " + p.element);
    var stage = Math.min(p.stage, el.Ip.length);
    var IpEV = el.Ip[stage - 1];
    var Zc = p.charge;
    var ap = adkParams(IpEV, Zc, el.l);

    /* --- スケール量 --- */
    var Fcr = criticalFieldAU(ap.Ip, Zc);          /* 障壁抑制場 [a.u.] */
    var Icr = Fcr * Fcr * I_AU;                    /* 臨界強度 [W/cm^2] */
    var E0 = Math.sqrt(p.intensity / I_AU);        /* ピーク場 [a.u.]   */
    var omega = HC_EVNM / (p.lambdaNm * E_HARTREE);/* 角振動数 [a.u.]   */
    var photonEV = HC_EVNM / p.lambdaNm;
    var cycleFs = (2 * Math.PI / omega) / FS_AU;
    var Up = ponderomotive(p.intensity, p.lambdaNm);
    var gammaK = keldysh(IpEV, p.intensity, p.lambdaNm);
    var tauAU = p.fwhmFs * FS_AU;
    var Tau = p.windowFactor * tauAU;
    var N = p.steps;
    var dt = 2 * Tau / (N - 1);
    var cap = p.rateCap > 0 ? p.rateCap : 2 * ap.Ip;

    /* --- 時系列 --- */
    var t = new Float64Array(N), E = new Float64Array(N), Iinst = new Float64Array(N);
    var Pb = new Float64Array(N), rate = new Float64Array(N), xs = new Float64Array(N);
    var zeta = new Float64Array(N), dep = new Float64Array(N), marg = new Float64Array(N);
    var eul = new Float64Array(N), lam = new Float64Array(N);

    var P = 1.0, cappedSteps = 0;
    var zetaRadius = ap.nstar * ap.nstar / Zc;      /* 水素様平均半径 [a0] */
    var betaPQ = betaFn(ap.nstar, el.l + 1);        /* β(p,q) */

    for (var i = 0; i < N; i++) {
      var tt = -Tau + i * dt;
      var env = envelope(tt, tauAU, p.shape);
      var f = E0 * env * Math.cos(omega * tt + p.cep);
      var af = Math.abs(f);
      var w = adkRate(af, ap);
      if (w > cap) { w = cap; cappedSteps++; }
      t[i] = tt / FS_AU;
      E[i] = f;
      Iinst[i] = af * af * I_AU;
      rate[i] = w;
      Pb[i] = P;
      var x = af / Fcr;
      xs[i] = x;
      zeta[i] = zetaN(x, p.zetaOrder);
      dep[i] = gammaDeprivation(x);
      marg[i] = balanceMargin(x);
      lam[i] = dalanversian(x);
      eul[i] = eulerResidual(x, P, zetaRadius, p.zetaOrder);
      /* 指数積分 (率が大きい領域でも安定) */
      P *= Math.exp(-w * dt);
      if (P < 1e-300) P = 0;
    }

    /* --- 臨界期の抽出: |E(t)| >= F_cr の連結窓 --- */
    var windows = [], open = null;
    for (i = 0; i < N; i++) {
      var over = xs[i] >= 1;
      if (over && !open) open = { i0: i, t0: t[i], Ipeak: 0, sum: 0, n: 0, sign: E[i] >= 0 ? 1 : -1 };
      if (open) {
        if (Iinst[i] > open.Ipeak) open.Ipeak = Iinst[i];
        open.sum += Iinst[i]; open.n++;
      }
      if (!over && open) {
        open.i1 = i - 1; open.t1 = t[i - 1];
        windows.push(open); open = null;
      }
    }
    if (open) { open.i1 = N - 1; open.t1 = t[N - 1]; windows.push(open); }

    var dtFs = dt / FS_AU;
    var totalOn = 0, Ipeak = 0, Isum = 0, Icount = 0;
    for (i = 0; i < windows.length; i++) {
      var wdw = windows[i];
      wdw.durFs = (wdw.i1 - wdw.i0 + 1) * dtFs;
      wdw.durAs = wdw.durFs * 1000;
      wdw.Imean = wdw.n ? wdw.sum / wdw.n : 0;
      totalOn += wdw.durFs;
      if (wdw.Ipeak > Ipeak) Ipeak = wdw.Ipeak;
      Isum += wdw.sum; Icount += wdw.n;
      delete wdw.sum; delete wdw.n;
    }
    var exists = windows.length > 0;
    var tStart = exists ? windows[0].t0 : null;
    var tEnd = exists ? windows[windows.length - 1].t1 : null;
    var durationFs = exists ? (tEnd - tStart) : 0;
    var ImeanCrit = Icount ? Isum / Icount : 0;
    /* 臨界期の内部フルーエンス [J/cm^2] = ∫ I dt  (I は W/cm^2, dt は s) */
    var fluence = Isum * dt * T_AU;

    /* --- Ω 層の集計 --- */
    var cUsed = Math.min(windows.length, p.maxCrossings);
    var truncated = windows.length > cUsed;
    var writhe = 0;
    for (i = 0; i < cUsed; i++) writhe += windows[i].sign;
    var K = cUsed > 0 ? kauffmanBracket(braidDiagram(cUsed), p.kauffmanA) : 1;
    /* Jones 正規化 f(A) = (-A^3)^{-w} <D> */
    var jones = K * Math.pow(-Math.pow(p.kauffmanA, 3), -writhe);

    /* H(σ): 臨界窓のフルーエンス分布のエントロピー + 束縛/電離の二値エントロピー */
    var shares = [];
    for (i = 0; i < windows.length; i++) shares.push(windows[i].Imean * windows[i].durFs);
    var sTot = shares.reduce(function (a, b) { return a + b; }, 0);
    if (sTot > 0) shares = shares.map(function (v) { return v / sTot; });
    var Hw = shannon(shares);
    var Pion = 1 - P;
    var Hion = shannon([Math.max(P, 0), Math.max(Pion, 0)]);
    var Hsigma = Hw + Hion;

    var nApprox = Math.max(1, cUsed);
    var piN = piApprox(nApprox), eN = eApprox(nApprox);
    var Esigma = K * Hsigma / (4 * piN * eN);       /* Ω 臨界強度指数 (無次元) */
    var EsigmaW = Esigma * Icr;                     /* W/cm^2 スケール          */

    /* Euler 極均衡 R = x^n + y^n - n x y z の零交差 */
    var zeroCross = 0;
    for (i = 1; i < N; i++) if ((eul[i - 1] < 0) !== (eul[i] < 0)) zeroCross++;

    var depMin = 1, margMin = 2, xMax = 0, zetaMax = 0;
    for (i = 0; i < N; i++) {
      if (dep[i] < depMin) depMin = dep[i];
      if (marg[i] < margMin) margMin = marg[i];
      if (xs[i] > xMax) xMax = xs[i];
      if (zeta[i] > zetaMax) zetaMax = zeta[i];
    }

    return {
      version: VERSION,
      params: p,
      atom: {
        sym: el.sym, name: el.name, Z: el.Z, l: el.l, stage: stage,
        IpEV: IpEV, IpAU: ap.Ip, Zc: Zc,
        kappa: ap.kappa, nstar: ap.nstar, Cn2: ap.Cn2, flm: ap.flm,
        zetaRadiusA0: zetaRadius, betaPQ: betaPQ
      },
      scales: {
        FcrAU: Fcr, Icr: Icr, E0AU: E0, I0: p.intensity,
        omegaAU: omega, photonEV: photonEV, cycleFs: cycleFs,
        UpEV: Up, gammaK: gammaK, IauWcm2: I_AU,
        overcritical: p.intensity / Icr,
        regime: gammaK < 0.5 ? "tunneling" : (gammaK > 2 ? "multiphoton" : "intermediate"),
        dtFs: dtFs, spanFs: 2 * Tau / FS_AU
      },
      series: { t: t, E: E, I: Iinst, Pbound: Pb, rate: rate, x: xs, zeta: zeta, dep: dep, margin: marg, lambda: lam, euler: eul },
      critical: {
        exists: exists, count: windows.length, windows: windows,
        tStartFs: tStart, tEndFs: tEnd, durationFs: durationFs,
        totalOnFs: totalOn, dutyRatio: durationFs > 0 ? totalOn / durationFs : 0,
        IpeakWcm2: Ipeak, ImeanWcm2: ImeanCrit, fluenceJcm2: fluence,
        overcriticalPeak: xMax * xMax,
        meanWindowAs: windows.length ? (totalOn / windows.length) * 1000 : 0
      },
      omega: {
        crossings: windows.length, crossingsUsed: cUsed, truncated: truncated,
        A: p.kauffmanA, writhe: writhe, kauffman: K, jones: jones,
        entropyWindows: Hw, entropyIon: Hion, entropy: Hsigma,
        piN: piN, eN: eN, n: nApprox,
        Esigma: Esigma, EsigmaWcm2: EsigmaW,
        zetaMax: zetaMax, depMin: depMin, marginMin: margMin, xMax: xMax,
        eulerZeroCrossings: zeroCross
      },
      result: {
        Pbound: P, ionization: Pion,
        cappedFraction: cappedSteps / N,
        note: cappedSteps ? "ADK は障壁抑制強度を超えると外挿になるため、率を 2·I_p [a.u.] でキャップしています。" : ""
      }
    };
  }

  /* ===================== 強度スイープ ===================== */
  /* ピーク強度 I0 を対数掃引し、臨界期の長さ・電離率・E(σ) の応答を返す。 */
  function sweep(opt, range) {
    var r = range || {};
    var from = r.from || 1e12, to = r.to || 1e17, pts = r.points || 40;
    var out = [];
    var lf = Math.log10(from), lt = Math.log10(to);
    for (var i = 0; i < pts; i++) {
      var I0 = Math.pow(10, lf + (lt - lf) * i / (pts - 1));
      var o = {};
      for (var k in (opt || {})) o[k] = opt[k];
      o.intensity = I0;
      o.steps = Math.min(opt && opt.steps ? opt.steps : 2500, 4000);
      var s = simulate(o);
      out.push({
        intensity: I0,
        overcritical: I0 / s.scales.Icr,
        durationFs: s.critical.durationFs,
        totalOnFs: s.critical.totalOnFs,
        windows: s.critical.count,
        ionization: s.result.ionization,
        gammaK: s.scales.gammaK,
        Esigma: s.omega.Esigma,
        marginMin: s.omega.marginMin
      });
    }
    return { Icr: simulate(Object.assign({}, opt, { intensity: from, steps: 400 })).scales.Icr, points: out };
  }

  /* ===================== 出力 ===================== */
  function toCSV(res) {
    var s = res.series, n = s.t.length, L = [];
    L.push("# ACPI " + VERSION + " — atomic critical-period intensity");
    L.push("# element=" + res.atom.sym + " stage=" + res.atom.stage + " Ip_eV=" + res.atom.IpEV +
           " Zc=" + res.atom.Zc + " lambda_nm=" + res.params.lambdaNm +
           " I0_Wcm2=" + res.params.intensity + " fwhm_fs=" + res.params.fwhmFs + " shape=" + res.params.shape);
    L.push("# I_cr_Wcm2=" + res.scales.Icr + " F_cr_au=" + res.scales.FcrAU +
           " gamma_K=" + res.scales.gammaK + " Up_eV=" + res.scales.UpEV);
    L.push("# critical_period_fs=" + res.critical.durationFs + " windows=" + res.critical.count +
           " I_peak_Wcm2=" + res.critical.IpeakWcm2 + " E_sigma=" + res.omega.Esigma);
    L.push("t_fs,E_au,I_Wcm2,x_over_critical,P_bound,rate_au,zeta_n,gamma_dep,balance_margin,euler_residual");
    for (var i = 0; i < n; i++) {
      L.push([s.t[i], s.E[i], s.I[i], s.x[i], s.Pbound[i], s.rate[i],
              s.zeta[i], s.dep[i], s.margin[i], s.euler[i]]
             .map(function (v) { return Number(v).toExponential(6); }).join(","));
    }
    return L.join("\n") + "\n";
  }

  function summary(res) {
    var c = res.critical, s = res.scales, o = res.omega, a = res.atom;
    function sci(v, d) { return Number(v).toExponential(d === undefined ? 3 : d); }
    var L = [];
    L.push("原子              : " + a.sym + " (" + a.name + ")  第 " + a.stage + " 電離  I_p = " + a.IpEV.toFixed(4) + " eV");
    L.push("ADK               : κ = " + a.kappa.toFixed(4) + "  n* = " + a.nstar.toFixed(4) +
           "  |C_n*|² = " + a.Cn2.toFixed(4) + "  β(p,q) = " + a.betaPQ.toFixed(5));
    L.push("臨界(障壁抑制)場  : F_cr = " + sci(s.FcrAU) + " a.u.  →  I_cr = " + sci(s.Icr) + " W/cm²");
    L.push("駆動場            : λ = " + res.params.lambdaNm + " nm (" + s.photonEV.toFixed(3) + " eV)  " +
           "I₀ = " + sci(s.I0) + " W/cm²  FWHM = " + res.params.fwhmFs + " fs  " + res.params.shape);
    L.push("レジーム          : γ_Keldysh = " + s.gammaK.toFixed(4) + " (" + s.regime + ")  U_p = " + s.UpEV.toFixed(3) + " eV" +
           "  I₀/I_cr = " + s.overcritical.toFixed(3));
    L.push("");
    if (c.exists) {
      L.push("■ 臨界期 (critical period)");
      L.push("  時間窓          : t = " + c.tStartFs.toFixed(4) + " fs … " + c.tEndFs.toFixed(4) + " fs");
      L.push("  全長            : " + c.durationFs.toFixed(4) + " fs  (" + (c.durationFs * 1000).toFixed(1) + " as)");
      L.push("  サブ窓 (半周期) : " + c.count + " 個  合計 " + c.totalOnFs.toFixed(4) + " fs  " +
             "平均 " + c.meanWindowAs.toFixed(1) + " as  デューティ比 " + (c.dutyRatio * 100).toFixed(1) + " %");
      L.push("  臨界期の強度    : ピーク " + sci(c.IpeakWcm2) + " W/cm²  平均 " + sci(c.ImeanWcm2) + " W/cm²");
      L.push("  超臨界度        : I_peak/I_cr = " + c.overcriticalPeak.toFixed(3));
      L.push("  フルーエンス    : " + sci(c.fluenceJcm2) + " J/cm² (臨界期の内側のみ)");
    } else {
      L.push("■ 臨界期 : なし — 場は障壁抑制場 F_cr に達していません (I₀ < I_cr)。");
      L.push("  必要ピーク強度  : " + sci(s.Icr) + " W/cm² 以上");
    }
    L.push("");
    L.push("■ Ω 層 (山口フレームワーク)");
    L.push("  ζ 半径          : r_ζ = " + a.zetaRadiusA0.toFixed(4) + " a₀   ζ_n(max) = " + sci(o.zetaMax));
    L.push("  gamma-deprivation : min e^{-x log x} = " + sci(o.depMin));
    L.push("  均衡余裕        : min 2e^{-x log x} = " + sci(o.marginMin) + "  (0 → 重力/反重力均衡の喪失)");
    L.push("  Euler 極均衡    : x^n + y^n - n x y z の零交差 " + o.eulerZeroCrossings + " 回 (n = " + res.params.zetaOrder + ")");
    L.push("  Kauffman        : A = " + o.A + "  交差数 " + o.crossingsUsed + (o.truncated ? " (切詰)" : "") +
           "  writhe = " + o.writhe + "  <D> = " + sci(o.kauffman, 5));
    L.push("  Jones f(A)      : " + sci(o.jones, 5) + "   H(σ) = " + o.entropy.toFixed(5) + " nats");
    L.push("  臨界強度指数    : E(σ) = K(σ)·H(σ)/(4 π_" + o.n + " e_" + o.n + ") = " + sci(o.Esigma, 5));
    L.push("                    E(σ)·I_cr = " + sci(o.EsigmaWcm2) + " W/cm²");
    L.push("");
    L.push("■ 結果");
    L.push("  束縛残存        : " + (res.result.Pbound * 100).toFixed(6) + " %");
    L.push("  電離確率        : " + (res.result.ionization * 100).toFixed(6) + " %");
    if (res.result.note) L.push("  注意            : " + res.result.note);
    return L.join("\n");
  }

  return {
    VERSION: VERSION,
    CONST: { C_LIGHT: C_LIGHT, EPS0: EPS0, E_HARTREE: E_HARTREE, A0: A0, T_AU: T_AU, F_AU: F_AU, I_AU: I_AU, FS_AU: FS_AU, HC_EVNM: HC_EVNM },
    ELEMENTS: ELEMENTS, DEFAULTS: DEFAULTS,
    element: element, gammaFn: gammaFn, betaFn: betaFn,
    criticalFieldAU: criticalFieldAU, criticalIntensity: criticalIntensity,
    ponderomotive: ponderomotive, keldysh: keldysh,
    adkParams: adkParams, adkRate: adkRate, adkRateCycleAvg: adkRateCycleAvg,
    zetaN: zetaN, gammaDeprivation: gammaDeprivation, dalanversian: dalanversian,
    antigravity: antigravity, balanceMargin: balanceMargin, eulerResidual: eulerResidual,
    kauffmanBracket: kauffmanBracket, braidDiagram: braidDiagram,
    piApprox: piApprox, eApprox: eApprox, shannon: shannon,
    envelope: envelope, normalize: normalize,
    simulate: simulate, sweep: sweep, toCSV: toCSV, summary: summary
  };
});
