/*
 * phasecore.js — 山口フレームワークの文献から取り込んだ「検証できる」数理
 *
 * 利用者が提出した文献 (paper/references/) のうち、計算で確かめられるものだけを
 * 実装し、文献集自身の標識 (証明済 / 検証済 / 古典 / 予想 / 未検証) を付けて使う。
 *
 *   1. エントロピー位相融合 (文献 03 Entropy–Phase, 05 Bada quantum reviser)
 *      ψ_i = √a_i · exp(i Σ_m β_m H_m φ_{m,i}),  q_i = |ψ_i|² / Σ_j |ψ_j|²
 *      「非零因子の乗算は零点を保存する」(証明済・初等) を設計規則にしたもの。
 *      BadaGPT では、主チャネル (認識した語・グリフ) の分布 a を、補助チャネル
 *      (描いた動き・体のサイン・画像) が **位相でしか** 変えられない。
 *        - 零の保存: a_i = 0 (依頼に無い語) は、どの補助チャネルも復活させられない
 *        - 情報のない補助チャネル (H_m 一定・φ 一様) は定位相で洗い流される
 *      以前は「体のサインはアプリの中身を決めない」と規則で縛っていたが、この融合では
 *      それが数学的性質として成り立つ。
 *
 *   2. 大域的部分積分 (文献 02 定理 6・定理 7・系 2)
 *      生成関数 f = log x (L = x log x − x のルジャンドル双対) のもとで
 *      ∫_1^x log t dt + ∫_1^x t d(log t) = x log x   (系 2, 証明済)
 *      を数値積分で確かめ、特徴量 x に対する「微分側 / 積分側」の二つの値を
 *      熱エネルギー経路の可視化に使う (右辺の x log x はエントロピー項)。
 *
 *   3. 零点計数としての x log x (文献 01 定理 I-10, 古典・検証済)
 *      N(T) = x log x − x + 7/8 + S(T),  x = T/2π  (Riemann–von Mangoldt)
 *      文献集は、これだけが「ζ は x log x である」の内容を持つ読みだと述べる。
 *
 *   4. ナッシュ・シャノンの素数ゲームのエントロピー (文献 04, 検証済・自明に近い保存)
 *      q_k(σ) = p_k^{−σ} / Z(σ),  H(σ) = −Σ q_k log q_k,  ζ_NS = ζ · e^{iβH(Re s)}
 *      |e^{iβH}| = 1 なので零点を保存する。位相因子として可視化に使う。
 *
 *   5. 標識表 (文献 01 の分類に従う)
 *      本アプリで表示する各式に、文献集の標識を付ける。π(χ,x) = ∬(x log x)^{−2} dx_m = ½i
 *      (文献 06, 旧 Telegraph の Ξ の由来) は文献集が「未検証・定義がない」と判定しており、
 *      本アプリでも思考実験の可視化としてのみ扱う。
 *
 * 正直な範囲: これらは文献が「成り立つ」と述べた範囲の計算であり、リーマン予想・
 * 深リーマン予想・統一場についての主張は文献集自身が「未解決 / 研究計画」としている。
 */
"use strict";

/* ───────────── 1. エントロピー位相融合 ───────────── */
function shannonH(p) {
  var H = 0;
  for (var i = 0; i < p.length; i++) if (p[i] > 0) H -= p[i] * Math.log(p[i]);
  return H;
}
function normalize(p) {
  var s = 0, i; for (i = 0; i < p.length; i++) s += Math.max(0, p[i]);
  var out = new Array(p.length); for (i = 0; i < p.length; i++) out[i] = s > 0 ? Math.max(0, p[i]) / s : 0;
  return out;
}
/* base: 主チャネルの分布 a (長さ V)。modules: [{ phi: [V] (各トークンの位相 −π..π), p: [V] (そのモジュールの分布、H_m 用), beta }] */
function entropyPhaseFuse(base, modules) {
  var V = base.length, a = normalize(base), mods = modules || [];
  var H = mods.map(function (m) { return shannonH(normalize(m.p || m.phi.map(function () { return 1; }))); });
  var re = new Array(V), im = new Array(V), q = new Array(V), Z = 0, theta = new Array(V);
  for (var i = 0; i < V; i++) {
    var th = 0;
    for (var m = 0; m < mods.length; m++) th += (mods[m].beta != null ? mods[m].beta : 1) * H[m] * (mods[m].phi[i] || 0);
    theta[i] = th;
    var amp = Math.sqrt(a[i]);
    re[i] = amp * Math.cos(th); im[i] = amp * Math.sin(th);
    q[i] = re[i] * re[i] + im[i] * im[i]; Z += q[i];
  }
  for (var k = 0; k < V; k++) q[k] = Z > 0 ? q[k] / Z : 0;
  /* 純位相の融合では |ψ_i|² = a_i なので q = a (ユニタリ性)。情報のあるモジュールが
   * 確率を動かすのは、文献 03 §4.2 の通り、位相を実部へ射影する読み出しを通してである。 */
  var readout = new Array(V), Zr = 0;
  for (var r = 0; r < V; r++) { readout[r] = a[r] * (1 + Math.cos(theta[r])) / 2; Zr += readout[r]; }
  for (var r2 = 0; r2 < V; r2++) readout[r2] = Zr > 0 ? readout[r2] / Zr : 0;
  return { a: a, q: q, psi: { re: re, im: im }, theta: theta, H: H, readout: readout };
}

/* ───────────── 2. 大域的部分積分 (定理 6 / 系 2) ───────────── */
function simpson(fn, lo, hi, n) {
  n = n || 400; if (n % 2) n++;
  var h = (hi - lo) / n, s = fn(lo) + fn(hi);
  for (var i = 1; i < n; i++) s += fn(lo + i * h) * (i % 2 ? 4 : 2);
  return s * h / 3;
}
/* 系 2: ∫_1^x log t dt (積分側) + ∫_1^x t d(log t) = ∫_1^x 1 dt (微分側) = x log x。残差も返す。 */
function partialIntegration(x) {
  x = Math.max(1, x);
  var integralSide = simpson(function (t) { return Math.log(t); }, 1, x);   /* = x log x − x + 1 */
  var differentialSide = x - 1;                                             /* ∫ t · (1/t) dt */
  var xlogx = x * Math.log(x);
  return { integralSide: integralSide, differentialSide: differentialSide, sum: integralSide + differentialSide, xlogx: xlogx, residual: integralSide + differentialSide - xlogx, L: xlogx - x };
}
/* 定理 7 (iii): ポテンシャル L = x log x − x、f = ∇L = log x、計量 g = 1/x */
function entropyPotential(x) { return { L: x * Math.log(x) - x, f: Math.log(x), g: 1 / x }; }

/* ───────────── 3. 零点計数 N(T) (古典) ───────────── */
function zeroCount(T) {
  var x = T / (2 * Math.PI);
  return { x: x, main: x * Math.log(x) - x + 7 / 8, xlogx: x * Math.log(x) };
}

/* ───────────── 4. ナッシュ・シャノンの素数ゲーム ───────────── */
function primesUpTo(n) {
  var sieve = new Uint8Array(n + 1), out = [];
  for (var i = 2; i <= n; i++) { if (!sieve[i]) { out.push(i); for (var j = i * i; j <= n; j += i) sieve[j] = 1; } }
  return out;
}
var NS_PRIMES = primesUpTo(2000);
function nashShannonH(sigma, primes) {
  primes = primes || NS_PRIMES;
  var Z = 0, i; for (i = 0; i < primes.length; i++) Z += Math.pow(primes[i], -sigma);
  var H = 0; for (i = 0; i < primes.length; i++) { var q = Math.pow(primes[i], -sigma) / Z; H -= q * Math.log(q); }
  return H;
}
/* ζ_NS の位相因子 e^{iβH(σ)} (絶対値 1) */
function nsPhase(sigma, beta) { var H = nashShannonH(sigma); return { H: H, re: Math.cos(beta * H), im: Math.sin(beta * H), abs: 1 }; }

/* ───────────── 5. 標識表 (文献 01 の分類) ───────────── */
var FRAMEWORK_CLAIMS = [
  { key: "phase", label: "非零因子の乗算は零点を保存する (ζ·e^{iβH})", status: "証明済", ref: "03, 04", note: "初等。位相融合の設計規則の根拠" },
  { key: "partial", label: "大域的部分積分 ∫F^{f′}G df = [FG] − ∫FG^{g′}dg", status: "証明済", ref: "02 定理6", note: "正方形を 2 枚の三角形に分ける操作" },
  { key: "legendre", label: "L = x log x − x, f = ∇L = log x (ルジャンドル双対)", status: "証明済", ref: "02 定理7", note: "微分側と積分側を同じポテンシャルで結ぶ" },
  { key: "zerocount", label: "N(T) = x log x − x + 7/8 + S(T), x = T/2π", status: "古典・検証済", ref: "01 定理I-10", note: "「ζ は x log x」の内容を持つ唯一の読み" },
  { key: "beta_fe", label: "ζ(s) = 2^s π^{s−1} sin(πs/2) β(s,1−s) Γ(1−s) ζ(1−s)", status: "証明済", ref: "01 定理I-1", note: "ベータ型関数等式" },
  { key: "jones", label: "Jones 多項式 V_{T(2,n)} (Kauffman 括弧)", status: "古典", ref: "Jones 1985 / Kauffman 1987", note: "結び目不変量。熱経路の可視化に使用" },
  { key: "shannon", label: "シャノンエントロピー H = −Σ p log p", status: "古典", ref: "Shannon 1948", note: "生成 AI の損失そのもの (03 §3)" },
  { key: "xi", label: "Ξ = β(H+1, M+1)/log(N+2), π(χ,x) = ∬(x log x)^{−2} dx_m = ½i", status: "未検証", ref: "06, 01 1.8", note: "文献集が「定義がない」と判定。思考実験の可視化のみ" },
  { key: "graviton", label: "グラビトン↔電磁波変換・量子テレポーテーション忠実度", status: "未検証", ref: "Telegraph", note: "思考実験の可視化のみ。物理的通信の主張ではない" },
  { key: "rh", label: "リーマン予想・深リーマン予想・統一場", status: "予想 (未解決)", ref: "01 序論", note: "文献集自身が未解決・研究計画と明記" }
];
function claimStatus(key) { var c = FRAMEWORK_CLAIMS.filter(function (x) { return x.key === key; })[0]; return c ? c.status : "—"; }

/* 文献一覧 (paper/references/) */
var REFERENCE_DOCS = [
  { n: 1, file: "01_yamaguchi_framework_collection_unified_field.pdf", title: "山口フレームワーク論文集：リーマン予想・深リーマン予想・量子力学・一般相対性理論の統一場 (エントロピー交換子版)", year: "2026-09" },
  { n: 2, file: "02_global_partial_integration_calculus_theorems.pdf", title: "微分・積分の計算体系に関する定理の構成 —「大域的偏微分と大域的多重積分、大域的部分積についてのレポート」の定理化", year: "2026-11" },
  { n: 3, file: "03_entropy_phase_generative_ai.pdf", title: "An Entropy–Phase Mechanism for Generative AI", year: "2026-06" },
  { n: 4, file: "04_nash_shannon_zeta.pdf", title: "ナッシュ・シャノン公式に基づくゼータ関数と本物のゼータの相関", year: "2026-06" },
  { n: 5, file: "05_bada_quantum_reviser.pdf", title: "Reviser-Extensible Grammars: A Q#-Targeted Quantum Front End for the Unknown-Prior Engine (Bada)", year: "2026" },
  { n: 6, file: "06_caostics_euler_product_heisenberg.pdf", title: "Euler product estrade from Heisenberg Non-commutative with deprivate equation", year: "—" },
  { n: 7, file: "07_entropy_zeta_ai.pdf", title: "Entropy / Zeta / AI", year: "—" },
  { n: 8, file: "08_beta_zeta.pdf", title: "ベータ関数とゼータ関数の構造的対応", year: "—" },
  { n: 9, file: "09_deep_riemann.pdf", title: "Deep Riemann", year: "—" },
  { n: 10, file: "10_gauss_surface_quantization.pdf", title: "Gauss surface quantization", year: "—" },
  { n: 11, file: "11_hpsi_multiplicity_sphere_family.pdf", title: "HΨ = ⊕(iħ∇)^⊕L の同定と球面族への拡張", year: "—" },
  { n: 12, file: "12_inter_dimensional_port_directory.pdf", title: "Inter-dimensional port directory", year: "—" },
  { n: 13, file: "13_bada_engine_full_source.pdf", title: "Bada engine full source", year: "—" },
  { n: 14, file: "14_bada_unknown_prior_engine.pdf", title: "Bada unknown-prior engine", year: "—" },
  { n: 15, file: "15_bada_extended_sources.pdf", title: "Bada extended sources", year: "—" },
  { n: 16, file: "16_bada_self_hosting_project.pdf", title: "Bada Self-Hosting Project", year: "—" },
  { n: 17, file: "17_bada_source.pdf", title: "Bada source", year: "—" }
];
