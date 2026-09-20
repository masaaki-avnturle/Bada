/* ============================================================================
 * lambda_driver.js — LÆVATEIN: Λ ドライバ無力化シミュレータのモデルコア
 *
 * 「暴走する指数関数的エネルギー解放を、抑制場で封じ込められるか」を
 * 熱収支として見積もる。核となる問いは一つ:
 *
 *      抑制した分のエネルギーを、どこへ、どれだけの速さで捨てられるか。
 *
 * 三層構成:
 *
 *  (A) 暴走系 [抽象] — 初期出力 P0・倍加時間 τ_d・総エネルギー E_max の
 *      3 つだけで記述する、装置非依存の指数関数的暴走。特定の装置の
 *      設計量 (質量・幾何・材料) は一切含まない。電池の熱暴走でも
 *      雪崩増倍でも同じ式になる、純粋な runaway モデル。
 *
 *  (B) 抑制層 [山口フレームワーク + 架空] —
 *      ・Γ 大域的部分積分多様体: 不完全ガンマ関数 Γ(s,x) を繰り返し
 *        部分積分すると境界項の漸近級数が現れる。各境界項を「吸収層」と
 *        見なし、最適打ち切り (superasymptotics) の位置で級数を止める。
 *        そこに残る最小項が、抑制を抜けて漏れるエネルギー比 ρ になる。
 *        ρ は x に対して指数関数的に小さい (~e^{-x})。これは実在の
 *        漸近解析であり、数値的に厳密に計算できる。
 *      ・Λ ドライバ: フレームワークの Dalanversian 作用素
 *        Λ = cos(i·u) − i·sin(i·u) = e^u,  u = x log x を抑制場とする。
 *        名称は『フルメタル・パニック!』(賀東招二) の架空装置に由来し、
 *        作中でレーバテインの AI「アル」が行う封じ込めの筋立てを
 *        手順の骨格として借りている。装置そのものは完全な創作である。
 *      ・Jones 多項式の熱エネルギー消費: 抑制場の再整形手順を閉ブレイド
 *        の交差とみなし、Kauffman ブラケット ⟨D⟩(A) を状態和で評価する。
 *        その計算に要する非可逆ビット操作数に Landauer 限界
 *        k_B T ln2 を掛けたものが、制御計算そのものの発熱になる。
 *        状態和は 2^c で増えるので、倍加時間内に評価し切れる交差数に
 *        上限が生じる — これが制御側の実在の制約になる。
 *
 *  (C) 冷却層 [実在の物理] — 青色 LED の電界発光冷却。
 *      順方向バイアス V が光子エネルギー ħω/q を下回る領域で駆動すると、
 *      LED は 1 光子あたり (η·ħω − qV) だけ格子から熱を奪う熱ポンプになる。
 *      冷却条件は外部量子効率 η > qV/ħω。これは実証済みの現象だが、
 *      実測された冷却能力は pW オーダーにとどまる
 *      (Santhanam, Gray & Ram, Phys. Rev. Lett. 108, 097403 (2012))。
 *
 * このシミュレータの主眼は「うまくいく」ことではなく、(A) が要求する
 * 排熱速度と (C) が実際に出せる冷却能力の間に何桁の隔たりがあるかを
 * 数値で示すことにある。判定は必ずその桁数を添えて返す。
 *
 * ブラウザ (dist/lambda-driver.html に inline) と Node (cli/) の両方で動く
 * UMD モジュール。依存なし。
 * ==========================================================================*/
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.LambdaDriver = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var VERSION = "1.0.0";

  /* ===================== 物理定数 (CODATA 2018) ===================== */
  var H_PLANCK = 6.62607015e-34;   /* J·s   */
  var C_LIGHT  = 2.99792458e8;     /* m/s   */
  var Q_E      = 1.602176634e-19;  /* C     */
  var K_B      = 1.380649e-23;     /* J/K   */
  var HC_EVNM  = 1239.841984;      /* eV·nm */
  var LN2      = Math.LN2;

  /* 実証済み電界発光冷却の桁 (Santhanam et al. 2012, PRL 108, 097403)。
     赤外 InGaAs 素子・高温動作での実測で、オーダーの基準としてのみ使う。 */
  var EL_COOLING_DEMONSTRATED_W = 1e-10;   /* ~100 pW */

  /* ===================== 数学ユーティリティ ===================== */
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
  function betaFn(p, q) { return gammaFn(p) * gammaFn(q) / gammaFn(p + q); }
  function shannon(ps) {
    var H = 0;
    for (var i = 0; i < ps.length; i++) { var p = ps[i]; if (p > 1e-15) H += -p * Math.log(p); }
    return H;
  }
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

  /* ===================== (B1) Γ 大域的部分積分多様体 =====================
     Γ(s,x) = ∫_x^∞ t^{s-1} e^{-t} dt を繰り返し部分積分すると

        Γ(s,x) = x^{s-1} e^{-x} · Σ_{k≥0} a_k ,
        a_0 = 1,  a_k = a_{k-1} · (s-k)/x

     という漸近級数になる。これは収束せず、|a_k| は k ≈ s+x で最小に
     なってから発散する。最小項の位置で打ち切るのが最適打ち切り
     (superasymptotics) で、そこに残る誤差は最小項と同じ桁 ~ e^{-x}。

     各 a_k を「第 k 吸収層」と読み替え、層の総和を抑制容量、最小項を
     抜けてくる漏れとみなす。漏れ比 ρ = min|a_k| / Σ|a_k| は x に対して
     指数関数的に小さくなる。                                             */
  function gammaManifold(s, x, maxLayers) {
    maxLayers = maxLayers || 400;
    var a = 1, layers = [{ k: 0, term: 1, abs: 1 }];
    /* sumAbs = 抑制容量 (層の大きさの総和)。
       sumSigned = Γ(s,x) の漸近評価に使う符号付き和。別物なので分けて持つ。 */
    var sumAbs = 1, sumSigned = 1, minAbs = 1, minK = 0;
    var kOpt = Math.max(1, Math.round(s + x));   /* 最小項の理論位置 */
    var kMax = Math.min(maxLayers, Math.max(4, Math.ceil(kOpt * 1.6)));
    for (var k = 1; k <= kMax; k++) {
      a = a * (s - k) / x;
      if (!isFinite(a)) break;
      var abs = Math.abs(a);
      layers.push({ k: k, term: a, abs: abs });
      if (abs < minAbs) { minAbs = abs; minK = k; }
      /* 最小項までの層だけが「使える」抑制容量 */
      if (k <= minK) { sumAbs += abs; sumSigned += a; }
      /* 発散に転じてから十分離れたら打ち切る */
      if (k > minK + 8 && abs > minAbs * 1e6) break;
    }
    var rho = sumAbs > 0 ? minAbs / sumAbs : 1;
    if (!isFinite(rho) || rho < 0) rho = 0;
    if (rho > 1) rho = 1;
    return {
      s: s, x: x,
      layers: layers,
      optimalTruncation: minK,            /* 最適打ち切り層 */
      predictedTruncation: kOpt,          /* 理論位置 s+x   */
      minTerm: minAbs,                    /* 最小項 (超漸近残差の桁) */
      capacity: sumAbs,                   /* 抑制容量 Σ|a_k| (大きさの総和) */
      signedSum: sumSigned,               /* Σ a_k (符号付き) */
      leakFraction: rho,                  /* 漏れ比 ρ */
      /* Γ(s,x) の漸近評価。前因子 x^{s-1}e^{-x} に符号付き和を掛ける。
         最適打ち切りなので誤差は最小項と同じ桁 (超漸近精度)。 */
      gammaAsym: Math.pow(x, s - 1) * Math.exp(-x) * sumSigned
    };
  }

  /* ===================== (B2) Λ ドライバ (Dalanversian) =====================
     u = x log x,  Λ = cos(i u) − i sin(i u) = cosh u + sinh u = e^u
     Λ⁻ = 2 cosh u (反重力側),  均衡余裕 = 2 e^{-u}
     臨界期シミュレータ (atom_critical.js) と同じ作用素を使う。            */
  function xlogx(x) { return x <= 0 ? 0 : x * Math.log(x); }
  function dalanversian(x) { return Math.exp(xlogx(x)); }
  function antigravity(x) { return 2 * Math.cosh(xlogx(x)); }
  function balanceMargin(x) { return 2 * Math.exp(-xlogx(x)); }

  /* ===================== (B3) Kauffman ブラケット + Landauer =====================
     状態和 ⟨D⟩(A) = Σ_states A^{a-b} d^{loops-1},  d = -A² - A⁻²
     非可逆ビット操作を数え、Landauer 限界 k_B T ln2 を掛けて発熱を出す。   */
  function ufFind(parent, x, ctr) { while (parent[x] >= 0) { x = parent[x]; ctr.ops++; } ctr.ops++; return x; }
  function kauffmanBracket(cross, A, ctr) {
    ctr = ctr || { ops: 0 };
    var n = cross.length;
    if (n === 0) return { value: 1, ops: 0 };
    var maxlbl = 0, i, k;
    for (i = 0; i < n; i++) for (k = 0; k < 4; k++) if (cross[i][k] > maxlbl) maxlbl = cross[i][k];
    var U = maxlbl + 1;
    var states = Math.pow(2, n);
    var d = -(A * A) - 1 / (A * A);
    var sum = 0;
    for (var st = 0; st < states; st++) {
      var parent = new Array(U);
      for (var q = 0; q < U; q++) { parent[q] = -1; ctr.ops++; }
      var a_cnt = 0, b_cnt = 0;
      for (i = 0; i < n; i++) {
        var e = cross[i], bit = (st >> i) & 1, p1, p2, r1, r2;
        ctr.ops++;
        if (bit === 0) { p1 = [e[0], e[1]]; p2 = [e[2], e[3]]; a_cnt++; }
        else { p1 = [e[1], e[2]]; p2 = [e[3], e[0]]; b_cnt++; }
        r1 = ufFind(parent, p1[0], ctr); r2 = ufFind(parent, p1[1], ctr);
        if (r1 !== r2) { parent[r1] = r2; ctr.ops++; }
        r1 = ufFind(parent, p2[0], ctr); r2 = ufFind(parent, p2[1], ctr);
        if (r1 !== r2) { parent[r1] = r2; ctr.ops++; }
      }
      var seen = {}, loops = 0;
      for (var lbl = 0; lbl < U; lbl++) {
        var r = ufFind(parent, lbl, ctr);
        if (!seen[r]) { seen[r] = 1; loops++; ctr.ops++; }
      }
      sum += Math.pow(A, a_cnt - b_cnt) * Math.pow(d, loops - 1);
      ctr.ops++;
    }
    return { value: sum, ops: ctr.ops };
  }
  /* c 交差の閉 2-ブレイド ((2,c) トーラス絡み目) */
  function braidDiagram(c) {
    var cross = [];
    for (var i = 0; i < c; i++) cross.push([i, c + i, c + ((i + 1) % c), (i + 1) % c]);
    return cross;
  }
  /* 交差数 c の状態和に必要な操作数の見積り (実測に比例、2^c·c スケール) */
  function bracketOpsEstimate(c) { return Math.pow(2, c) * (10 * c + 6); }

  /* ===================== (C) 青色 LED 電界発光冷却 [実在] =====================
     1 電子注入あたり: 電気的仕事 qV を入れ、平均 η 個の光子が ħω を持ち去る。
     格子から奪う正味の熱 = η·ħω − qV  (これが正なら冷却)
        冷却条件      η > qV / ħω
        冷却能力      P_cool = I·(η·ħω/q − V)
        成績係数 COP  = P_cool / (V·I) = η·ħω/(qV) − 1                     */
  function photonEnergyEV(lambdaNm) { return HC_EVNM / lambdaNm; }
  function elCooling(opt) {
    var lam = opt.lambdaNm, V = opt.biasV, eta = opt.eqe, I = opt.currentA;
    var hwEV = photonEnergyEV(lam);
    var perElectronEV = eta * hwEV - V;            /* 1 電子あたりの吸熱 [eV] */
    var coolsAt = eta > (V / hwEV);
    var pCool = I * perElectronEV;                 /* [W] = A × (J/C) */
    var pElec = V * I;
    return {
      lambdaNm: lam, photonEV: hwEV, biasV: V, eqe: eta, currentA: I,
      cools: coolsAt,
      etaThreshold: V / hwEV,                      /* 冷却に必要な最小 EQE */
      perElectronEV: perElectronEV,
      coolingW: pCool,
      electricalW: pElec,
      cop: pElec > 0 ? pCool / pElec : Infinity,
      /* 目標冷却能力を出すのに必要な電流 */
      currentForW: function (W) { return perElectronEV > 0 ? W / perElectronEV : Infinity; }
    };
  }

  /* ===================== パラメータ ===================== */
  var DEFAULTS = {
    /* (A) 暴走系 — 装置非依存の抽象モデル */
    p0W: 1e6,            /* 初期出力 [W]            */
    doublingNs: 10,      /* 倍加時間 [ns]           */
    emaxJ: 4.184e12,     /* 解放可能な総エネルギー [J] (1 kt TNT 相当の桁) */
    horizonNs: 600,      /* 観測時間 [ns]           */
    steps: 2000,

    /* (B) 抑制層 */
    gammaS: 2.5,         /* 不完全ガンマの s        */
    depthX: 30,          /* 部分積分の深さ x        */
    crossings: 14,       /* Λ 場再整形の交差数 c    */
    kauffmanA: 1.0699,   /* Kauffman ループ変数 A   */
    opsRate: 1e18,       /* 制御計算の演算速度 [ops/s] */
    tempK: 300,          /* 制御系の温度 [K]        */

    /* (C) 冷却層 (青色 LED) */
    ledLambdaNm: 450,    /* 青色 InGaN             */
    ledBiasV: 0.10,      /* 順方向バイアス [V]      */
    ledEQE: 0.70,        /* 外部量子効率            */
    ledCount: 1e12,      /* 素子数                  */
    ledCurrentA: 1e-3    /* 1 素子あたりの駆動電流 [A] */
  };

  function normalize(opt) {
    var p = {};
    for (var k in DEFAULTS) p[k] = DEFAULTS[k];
    for (var j in (opt || {})) if (opt[j] !== undefined && opt[j] !== null) p[j] = opt[j];
    p.steps = Math.max(100, Math.min(50000, Math.round(p.steps)));
    p.crossings = Math.max(1, Math.min(22, Math.round(p.crossings)));
    return p;
  }

  /* ===================== メイン ===================== */
  function simulate(opt) {
    var p = normalize(opt);

    /* ---------- (A) 暴走系 ---------- */
    var tau = p.doublingNs * 1e-9;                  /* s */
    var lambdaRate = LN2 / tau;                     /* 成長率 [1/s] */
    var horizon = p.horizonNs * 1e-9;
    /* P(t) = P0 e^{λt},  E(t) = P0/λ (e^{λt} − 1) が E_max に達したら停止 */
    var tQuench = Math.log(1 + p.emaxJ * lambdaRate / p.p0W) / lambdaRate;
    var tEnd = Math.min(horizon, tQuench);
    var pPeak = p.p0W * Math.exp(lambdaRate * tEnd);
    var eReleased = Math.min(p.emaxJ, (p.p0W / lambdaRate) * (Math.exp(lambdaRate * tEnd) - 1));

    /* ---------- (B1) Γ 大域的部分積分多様体 ---------- */
    var gm = gammaManifold(p.gammaS, p.depthX);
    var rho = gm.leakFraction;
    var eLeak = eReleased * rho;                    /* 抑制を抜けた分 [J] */
    var eAbsorb = eReleased - eLeak;                /* 吸収して捨てる分 [J] */
    var pAbsorbPeak = pPeak * (1 - rho);            /* 排熱のピーク要求 [W] */

    /* ---------- (B2) Λ ドライバ ---------- */
    var u = xlogx(p.depthX);
    var lam = { u: u, Lambda: dalanversian(p.depthX), antigravity: antigravity(p.depthX),
                margin: balanceMargin(p.depthX) };

    /* ---------- (B3) Jones 多項式の熱エネルギー消費 ---------- */
    var ctr = { ops: 0 };
    var br = kauffmanBracket(braidDiagram(p.crossings), p.kauffmanA, ctr);
    var landauerQuantum = K_B * p.tempK * LN2;      /* 1 ビット消去の下限 [J] */
    var eLandauer = br.ops * landauerQuantum;       /* 制御計算の発熱 [J] */
    var tCompute = br.ops / p.opsRate;              /* 評価にかかる時間 [s] */
    var pControl = p.opsRate * landauerQuantum;     /* 定常発熱 [W] (ops 数に依らない) */
    /* 倍加時間内に評価し切れる最大交差数 */
    var cFeasible = 0;
    for (var c = 1; c <= 64; c++) { if (bracketOpsEstimate(c) / p.opsRate <= tau) cFeasible = c; else break; }
    var computeCloses = tCompute <= tau;

    /* Ω 層: E(σ) = K(σ)×H(σ) / (4 (π_n, e_n)) */
    var hSigma = shannon([1 - rho, rho]) + shannon([eAbsorb / (eReleased || 1), eLeak / (eReleased || 1)]);
    var piN = piApprox(p.crossings), eN = eApprox(p.crossings);
    var eSigma = br.value * hSigma / (4 * piN * eN);

    /* ---------- (C) 青色 LED 電界発光冷却 ---------- */
    var led = elCooling({ lambdaNm: p.ledLambdaNm, biasV: p.ledBiasV,
                          eqe: p.ledEQE, currentA: p.ledCurrentA });
    var coolPerDevice = led.coolingW;
    var coolTotal = coolPerDevice * p.ledCount;
    var loadW = pAbsorbPeak + pControl;             /* 排熱すべき総電力 [W] */
    var coolingCloses = led.cools && coolTotal >= loadW;
    var devicesNeeded = led.cools && coolPerDevice > 0 ? loadW / coolPerDevice : Infinity;
    var currentNeededTotal = led.currentForW(loadW);
    /* 実証済み素子 (pW オーダー) で賄うなら何台必要か */
    var demonstratedDevices = loadW / EL_COOLING_DEMONSTRATED_W;
    var realityGapOrders = Math.log10(loadW / EL_COOLING_DEMONSTRATED_W);

    /* ---------- 時系列 ---------- */
    var N = p.steps, dt = tEnd / (N - 1 || 1);
    var t = new Float64Array(N), pw = new Float64Array(N), en = new Float64Array(N);
    var absorbed = new Float64Array(N), leaked = new Float64Array(N), coolCap = new Float64Array(N);
    var tBreak = null;
    for (var i = 0; i < N; i++) {
      var tt = i * dt;
      var P = p.p0W * Math.exp(lambdaRate * tt);
      var E = (p.p0W / lambdaRate) * (Math.exp(lambdaRate * tt) - 1);
      if (E > p.emaxJ) { E = p.emaxJ; P = 0; }
      t[i] = tt * 1e9;                    /* ns */
      pw[i] = P;
      en[i] = E;
      absorbed[i] = E * (1 - rho);
      leaked[i] = E * rho;
      coolCap[i] = coolTotal;
      if (tBreak === null && P * (1 - rho) + pControl > coolTotal) tBreak = tt * 1e9;
    }

    /* ---------- 判定 ---------- */
    var limiting =
      !computeCloses ? "control-compute" :
      !led.cools ? "el-cooling-condition" :
      !coolingCloses ? "cooling-power" : null;
    var verdict = limiting === null ? "closes" : "fails";

    return {
      version: VERSION,
      params: p,
      runaway: {
        lambdaRate: lambdaRate, doublingS: tau,
        tQuenchNs: tQuench * 1e9, tEndNs: tEnd * 1e9,
        pPeakW: pPeak, eReleasedJ: eReleased,
        ktEquivalent: eReleased / 4.184e12      /* kt TNT 換算 (桁の目安) */
      },
      gamma: gm,
      lambda: lam,
      jones: {
        crossings: p.crossings, A: p.kauffmanA, bracket: br.value,
        ops: br.ops, opsEstimate: bracketOpsEstimate(p.crossings),
        landauerQuantumJ: landauerQuantum,
        heatJ: eLandauer, computeS: tCompute, controlW: pControl,
        computeCloses: computeCloses, maxFeasibleCrossings: cFeasible,
        entropy: hSigma, piN: piN, eN: eN, Esigma: eSigma
      },
      budget: {
        leakFraction: rho, eLeakJ: eLeak, eAbsorbJ: eAbsorb,
        pAbsorbPeakW: pAbsorbPeak, loadW: loadW,
        breakNs: tBreak
      },
      led: {
        lambdaNm: led.lambdaNm, photonEV: led.photonEV, biasV: led.biasV,
        eqe: led.eqe, etaThreshold: led.etaThreshold, cools: led.cools,
        perElectronEV: led.perElectronEV,
        perDeviceW: coolPerDevice, count: p.ledCount, totalW: coolTotal,
        cop: led.cop, electricalW: led.electricalW * p.ledCount,
        devicesNeeded: devicesNeeded,
        currentNeededA: currentNeededTotal,
        demonstratedW: EL_COOLING_DEMONSTRATED_W,
        demonstratedDevices: demonstratedDevices,
        realityGapOrders: realityGapOrders
      },
      series: { t: t, power: pw, energy: en, absorbed: absorbed, leaked: leaked, coolCap: coolCap },
      verdict: { result: verdict, limiting: limiting, coolingCloses: coolingCloses,
                 computeCloses: computeCloses, elCondition: led.cools }
    };
  }

  /* ===================== 出力 ===================== */
  function sci(v, d) {
    if (!isFinite(v)) return v > 0 ? "∞" : "-∞";
    return Number(v).toExponential(d === undefined ? 3 : d);
  }

  function summary(r) {
    var L = [], b = r.budget, j = r.jones, d = r.led, g = r.gamma, ra = r.runaway;
    L.push("── (A) 暴走系 [装置非依存の抽象モデル] ──────────────────");
    L.push("  初期出力        : " + sci(r.params.p0W) + " W   倍加時間 " + r.params.doublingNs + " ns");
    L.push("  成長率 λ        : " + sci(ra.lambdaRate) + " s⁻¹");
    L.push("  解放エネルギー  : " + sci(ra.eReleasedJ) + " J  (TNT 換算 " + sci(ra.ktEquivalent, 2) + " kt 相当の桁)");
    L.push("  ピーク出力      : " + sci(ra.pPeakW) + " W   自己消滅まで " + ra.tQuenchNs.toFixed(1) + " ns");
    L.push("");
    L.push("── (B1) Γ 大域的部分積分多様体 ─────────────────────────");
    L.push("  Γ(s,x) の s, x  : s = " + g.s + ",  x = " + g.x);
    L.push("  最適打ち切り層  : k* = " + g.optimalTruncation + "  (理論位置 s+x = " + g.predictedTruncation + ")");
    L.push("  吸収容量 Σ|a_k| : " + sci(g.capacity, 5));
    L.push("  最小項 (超漸近) : " + sci(g.minTerm, 5));
    L.push("  漏れ比 ρ        : " + sci(b.leakFraction, 5) + "   → 抜けたエネルギー " + sci(b.eLeakJ) + " J");
    L.push("");
    L.push("── (B2) Λ ドライバ [架空: フルメタル・パニック!] ────────");
    L.push("  u = x log x     : " + r.lambda.u.toFixed(5));
    L.push("  Λ = e^u         : " + sci(r.lambda.Lambda, 5) + "   Λ⁻ = 2cosh u = " + sci(r.lambda.antigravity, 5));
    L.push("  均衡余裕 2e^{-u}: " + sci(r.lambda.margin, 5));
    L.push("");
    L.push("── (B3) Jones 多項式の熱エネルギー消費 ─────────────────");
    L.push("  交差数 c        : " + j.crossings + "   ⟨D⟩(A=" + j.A + ") = " + sci(j.bracket, 5));
    L.push("  非可逆操作数    : " + sci(j.ops, 4) + " ops   (状態和 2^" + j.crossings + ")");
    L.push("  Landauer 量子   : " + sci(j.landauerQuantumJ, 4) + " J/bit  (k_B T ln2, T = " + r.params.tempK + " K)");
    L.push("  制御計算の発熱  : " + sci(j.heatJ, 4) + " J   定常発熱 " + sci(j.controlW, 4) + " W");
    L.push("  評価所要時間    : " + sci(j.computeS, 4) + " s  " +
           (j.computeCloses ? "≤ 倍加時間 → 間に合う" : "> 倍加時間 → 間に合わない"));
    L.push("  間に合う最大 c  : " + j.maxFeasibleCrossings + " 交差 (演算速度 " + sci(r.params.opsRate, 2) + " ops/s)");
    L.push("  H(σ)            : " + (j.entropy >= 1e-4 ? j.entropy.toFixed(5) : sci(j.entropy, 3)) + " nats");
    L.push("  E(σ)            : " + sci(j.Esigma, 5));
    L.push("");
    L.push("── (C) 青色 LED 電界発光冷却 [実在の物理] ──────────────");
    L.push("  波長 / 光子     : " + d.lambdaNm + " nm  →  ħω = " + d.photonEV.toFixed(4) + " eV");
    L.push("  バイアス / EQE  : V = " + d.biasV + " V,  η = " + d.eqe +
           "   (冷却条件 η > qV/ħω = " + d.etaThreshold.toFixed(5) + ")");
    L.push("  冷却成立        : " + (d.cools ? "はい" : "いいえ") +
           "   1 電子あたり吸熱 " + d.perElectronEV.toFixed(4) + " eV");
    L.push("  1 素子の冷却能力: " + sci(d.perDeviceW, 4) + " W   (駆動電流 " + sci(r.params.ledCurrentA, 2) + " A)");
    L.push("  素子数 / 総能力 : " + sci(d.count, 3) + " 個  →  " + sci(d.totalW, 4) + " W   COP = " + d.cop.toFixed(3));
    L.push("");
    L.push("── 熱収支 ────────────────────────────────────────────");
    L.push("  排熱要求ピーク  : " + sci(b.loadW) + " W  (吸収 " + sci(b.pAbsorbPeakW) + " + 制御 " + sci(j.controlW, 2) + ")");
    L.push("  冷却能力        : " + sci(d.totalW) + " W");
    L.push("  不足            : " + (d.totalW >= b.loadW ? "なし" : sci(b.loadW / d.totalW, 3) + " 倍の能力が必要"));
    if (b.breakNs !== null) L.push("  冷却破綻時刻    : t = " + b.breakNs.toFixed(2) + " ns");
    L.push("");
    L.push("── 判定 ──────────────────────────────────────────────");
    if (r.verdict.result === "closes") {
      L.push("  モデル上は収支が閉じます。ただし下の「現実との差」を必ず参照してください。");
    } else {
      var why = { "control-compute": "制御計算が倍加時間内に終わらない",
                  "el-cooling-condition": "EQE が冷却条件 η > qV/ħω を満たさない",
                  "cooling-power": "冷却能力が排熱要求に届かない" }[r.verdict.limiting];
      L.push("  収支は閉じません — 律速: " + why);
    }
    L.push("");
    L.push("── 現実との差 ────────────────────────────────────────");
    L.push("  実証済みの電界発光冷却は pW オーダー (" + sci(d.demonstratedW, 1) + " W/素子,");
    L.push("  Santhanam et al. 2012, PRL 108, 097403 — 赤外 InGaAs・高温動作)。");
    L.push("  この排熱要求を実証済み素子だけで賄うと " + sci(d.demonstratedDevices, 3) + " 台、");
    L.push("  すなわち 10^" + d.realityGapOrders.toFixed(1) + " のスケール差になります。");
    L.push("  室温の青色 InGaN での正味電界発光冷却は未実証であり、低バイアス域では");
    L.push("  非発光再結合が EQE を潰すため、この構成は現実の装置にはなりません。");
    return L.join("\n");
  }

  function toCSV(r) {
    var s = r.series, n = s.t.length, L = [];
    L.push("# LAEVATEIN " + VERSION + " — Lambda-driver neutralization heat budget");
    L.push("# p0_W=" + r.params.p0W + " doubling_ns=" + r.params.doublingNs +
           " emax_J=" + r.params.emaxJ + " gamma_s=" + r.params.gammaS + " depth_x=" + r.params.depthX);
    L.push("# leak_fraction=" + r.budget.leakFraction + " load_W=" + r.budget.loadW +
           " cooling_W=" + r.led.totalW + " verdict=" + r.verdict.result +
           " limiting=" + (r.verdict.limiting || "none"));
    L.push("t_ns,power_W,energy_J,absorbed_J,leaked_J,cooling_capacity_W");
    for (var i = 0; i < n; i++)
      L.push([s.t[i], s.power[i], s.energy[i], s.absorbed[i], s.leaked[i], s.coolCap[i]]
             .map(function (v) { return Number(v).toExponential(6); }).join(","));
    return L.join("\n") + "\n";
  }

  return {
    VERSION: VERSION,
    CONST: { H_PLANCK: H_PLANCK, C_LIGHT: C_LIGHT, Q_E: Q_E, K_B: K_B,
             HC_EVNM: HC_EVNM, EL_COOLING_DEMONSTRATED_W: EL_COOLING_DEMONSTRATED_W },
    DEFAULTS: DEFAULTS,
    gammaFn: gammaFn, betaFn: betaFn, shannon: shannon,
    piApprox: piApprox, eApprox: eApprox,
    gammaManifold: gammaManifold,
    xlogx: xlogx, dalanversian: dalanversian, antigravity: antigravity, balanceMargin: balanceMargin,
    kauffmanBracket: kauffmanBracket, braidDiagram: braidDiagram, bracketOpsEstimate: bracketOpsEstimate,
    photonEnergyEV: photonEnergyEV, elCooling: elCooling,
    normalize: normalize, simulate: simulate, summary: summary, toCSV: toCSV
  };
});
