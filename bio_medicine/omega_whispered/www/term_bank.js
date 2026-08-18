/*
 * term_bank.js — 数学の専門用語銀行(瞬読検査用)
 * Ω-Whispered — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * 10 分野 × 10 語 = 100 語。瞬読(フラッシュ)でランダムに散らして提示し、
 * 「何が見えたか」「その語の意味は何か」を問うために使う。
 *
 * t: 用語(日本語) / en: 英語 / field: 専門分野 / lv: 難度(2〜5) / def: 一行の意味
 */
(function (root) {
  "use strict";

  var TERMS = [
    /* ---------------- 解析学 ---------------- */
    { t: "一様連続", en: "uniformly continuous", field: "解析学", lv: 2, def: "δ の取り方が点によらず一様に選べる連続性" },
    { t: "コーシー列", en: "Cauchy sequence", field: "解析学", lv: 2, def: "項どうしが限りなく近づく数列。完備空間では必ず収束する" },
    { t: "完備性", en: "completeness", field: "解析学", lv: 2, def: "すべてのコーシー列が空間内で収束すること" },
    { t: "優収束定理", en: "dominated convergence", field: "解析学", lv: 3, def: "可積分な優関数があれば極限と積分を交換してよい" },
    { t: "稠密", en: "dense", field: "解析学", lv: 3, def: "閉包が全体に一致する。いくらでも近くに元がある" },
    { t: "一様収束", en: "uniform convergence", field: "解析学", lv: 3, def: "収束の速さが点によらない収束。連続性・積分と両立する" },
    { t: "ソボレフ空間", en: "Sobolev space", field: "解析学", lv: 4, def: "弱微分まで可積分な関数の空間。偏微分方程式の解の舞台" },
    { t: "弱解", en: "weak solution", field: "解析学", lv: 4, def: "部分積分で微分を試験関数へ移して定義される、微分可能性を要さない解" },
    { t: "楕円型作用素", en: "elliptic operator", field: "解析学", lv: 4, def: "主表象が退化しない作用素。解の滑らかさ(正則性)が保証される" },
    { t: "漸近展開", en: "asymptotic expansion", field: "解析学", lv: 4, def: "収束しなくても有限項で良い近似を与える展開" },

    /* ---------------- 微分幾何 ---------------- */
    { t: "多様体", en: "manifold", field: "微分幾何", lv: 3, def: "局所的にユークリッド空間と同じに見える空間" },
    { t: "接束", en: "tangent bundle", field: "微分幾何", lv: 3, def: "各点の接空間を束ねたベクトル束" },
    { t: "微分形式", en: "differential form", field: "微分幾何", lv: 3, def: "積分される対象。反対称なテンソル場" },
    { t: "外微分", en: "exterior derivative", field: "微分幾何", lv: 3, def: "微分形式の次数を1つ上げる作用素。d∘d=0 を満たす" },
    { t: "接続", en: "connection", field: "微分幾何", lv: 4, def: "離れた点のベクトルを比べる規則。平行移動を定める" },
    { t: "曲率テンソル", en: "curvature tensor", field: "微分幾何", lv: 4, def: "平行移動が経路に依存する度合い。接続の非可換性" },
    { t: "測地線", en: "geodesic", field: "微分幾何", lv: 3, def: "曲がった空間での「まっすぐな線」。局所的な最短経路" },
    { t: "ホロノミー", en: "holonomy", field: "微分幾何", lv: 5, def: "閉曲線に沿って一周したときに生じる平行移動のズレ" },
    { t: "リッチ曲率", en: "Ricci curvature", field: "微分幾何", lv: 4, def: "曲率テンソルの縮約。体積の増減を測り、重力方程式に現れる" },
    { t: "ケーラー多様体", en: "Kähler manifold", field: "微分幾何", lv: 5, def: "複素構造・計量・シンプレクティック形式が両立する多様体" },

    /* ---------------- 位相幾何 ---------------- */
    { t: "ホモトピー", en: "homotopy", field: "位相幾何", lv: 3, def: "写像を連続的に変形する道筋。連続変形の同値関係" },
    { t: "ホモロジー", en: "homology", field: "位相幾何", lv: 3, def: "「穴」を代数的に数える不変量。閉じているが境界でない鎖" },
    { t: "コホモロジー", en: "cohomology", field: "位相幾何", lv: 4, def: "双対側から穴を測る不変量。積構造(カップ積)を持つ" },
    { t: "基本群", en: "fundamental group", field: "位相幾何", lv: 3, def: "基点を通るループのホモトピー類がなす群" },
    { t: "被覆空間", en: "covering space", field: "位相幾何", lv: 4, def: "局所的に何枚も重なって射影される空間。基本群と対応する" },
    { t: "ファイバー束", en: "fiber bundle", field: "位相幾何", lv: 4, def: "局所的には直積だが、大域的にはねじれている空間" },
    { t: "CW複体", en: "CW complex", field: "位相幾何", lv: 4, def: "胞体を次元順に貼り合わせて作る空間。計算に適した構成" },
    { t: "完全系列", en: "exact sequence", field: "位相幾何", lv: 4, def: "各点で像と核が一致する射の列。部分と商の関係を表す" },
    { t: "スペクトル系列", en: "spectral sequence", field: "位相幾何", lv: 5, def: "近似を繰り返してホモロジーを計算する装置" },
    { t: "種数", en: "genus", field: "位相幾何", lv: 3, def: "閉曲面の穴の数。オイラー標数と χ=2−2g で結ばれる" },

    /* ---------------- 代数・数論 ---------------- */
    { t: "イデアル", en: "ideal", field: "代数・数論", lv: 3, def: "環の中で吸収律を満たす部分集合。商環を作る核" },
    { t: "素イデアル", en: "prime ideal", field: "代数・数論", lv: 3, def: "積が入れば因子のどれかが入るイデアル。素数の一般化" },
    { t: "ガロア群", en: "Galois group", field: "代数・数論", lv: 4, def: "体の拡大の自己同型群。方程式の対称性そのもの" },
    { t: "拡大次数", en: "degree of extension", field: "代数・数論", lv: 3, def: "拡大体を下の体上のベクトル空間と見たときの次元" },
    { t: "円分体", en: "cyclotomic field", field: "代数・数論", lv: 4, def: "1 の冪根を添加した体。アーベル拡大の基本例" },
    { t: "判別式", en: "discriminant", field: "代数・数論", lv: 3, def: "根の重複や分岐を検出する不変量" },
    { t: "類数", en: "class number", field: "代数・数論", lv: 5, def: "イデアル類群の位数。一意分解が崩れる度合いを測る" },
    { t: "L関数", en: "L-function", field: "代数・数論", lv: 5, def: "算術的対象に付随するディリクレ級数。零点が分布を支配する" },
    { t: "合同式", en: "congruence", field: "代数・数論", lv: 2, def: "法 n で割った余りが等しいという関係" },
    { t: "局所大域原理", en: "local-global principle", field: "代数・数論", lv: 5, def: "すべての局所体で解を持てば大域的にも解を持つ、という原理" },

    /* ---------------- 代数幾何 ---------------- */
    { t: "代数多様体", en: "algebraic variety", field: "代数幾何", lv: 3, def: "多項式の共通零点として定まる図形" },
    { t: "スキーム", en: "scheme", field: "代数幾何", lv: 5, def: "可換環のスペクトルを貼り合わせた、代数幾何の一般的な空間" },
    { t: "層", en: "sheaf", field: "代数幾何", lv: 4, def: "局所的なデータを貼り合わせ条件つきで管理する仕組み" },
    { t: "連接層", en: "coherent sheaf", field: "代数幾何", lv: 5, def: "局所的に有限生成な関係で表される層。有限性の良い性質を持つ" },
    { t: "因子", en: "divisor", field: "代数幾何", lv: 4, def: "余次元 1 の部分多様体の形式的な整数結合。零点と極を記述する" },
    { t: "直線束", en: "line bundle", field: "代数幾何", lv: 4, def: "各点にの 1 次元ベクトル空間を割り当てた束。因子と対応する" },
    { t: "特異点解消", en: "resolution of singularities", field: "代数幾何", lv: 5, def: "特異点を持つ多様体を、双有理な非特異多様体に置き換える操作" },
    { t: "双有理同値", en: "birational equivalence", field: "代数幾何", lv: 5, def: "稠密開集合の上で同型になるという、緩い同値" },
    { t: "モジュライ空間", en: "moduli space", field: "代数幾何", lv: 5, def: "対象の同型類そのものを点とする空間" },
    { t: "リーマン・ロッホ", en: "Riemann-Roch", field: "代数幾何", lv: 5, def: "切断の次元差を種数と次数で与える定理。指数定理の原型" },

    /* ---------------- 圏論・論理 ---------------- */
    { t: "関手", en: "functor", field: "圏論・論理", lv: 3, def: "圏から圏への対応で、合成と恒等射を保つもの" },
    { t: "自然変換", en: "natural transformation", field: "圏論・論理", lv: 4, def: "関手から関手への「一斉に整合する」射の族" },
    { t: "随伴", en: "adjunction", field: "圏論・論理", lv: 4, def: "Hom(FA,B) ≅ Hom(A,GB) を自然に満たす関手の対" },
    { t: "極限", en: "limit", field: "圏論・論理", lv: 4, def: "図式に対する最も普遍的な錐。積・引き戻しなどを統一する" },
    { t: "普遍性", en: "universal property", field: "圏論・論理", lv: 3, def: "「一意に分解する」という条件で対象を特徴づける方法" },
    { t: "米田の補題", en: "Yoneda lemma", field: "圏論・論理", lv: 5, def: "対象は、それが他の対象へどう見えるかで完全に決まる" },
    { t: "モナド", en: "monad", field: "圏論・論理", lv: 5, def: "自己関手と単位・積からなる代数構造。計算の抽象化にも使う" },
    { t: "トポス", en: "topos", field: "圏論・論理", lv: 5, def: "集合論的な操作が行える圏。幾何と論理の橋渡し" },
    { t: "不完全性定理", en: "incompleteness theorem", field: "圏論・論理", lv: 4, def: "十分強い無矛盾な体系には証明も反証もできない命題がある" },
    { t: "選択公理", en: "axiom of choice", field: "圏論・論理", lv: 3, def: "空でない集合族から一斉に元を選べるという公理" },

    /* ---------------- 確率・統計 ---------------- */
    { t: "確率空間", en: "probability space", field: "確率・統計", lv: 3, def: "標本空間・σ加法族・確率測度の三つ組" },
    { t: "可測関数", en: "measurable function", field: "確率・統計", lv: 3, def: "逆像が可測集合になる関数。確率変数の定義そのもの" },
    { t: "条件付き期待値", en: "conditional expectation", field: "確率・統計", lv: 4, def: "部分情報(σ加法族)のもとでの最良予測。射影として特徴づけられる" },
    { t: "マルチンゲール", en: "martingale", field: "確率・統計", lv: 4, def: "将来の期待値が現在値に等しい確率過程。公正な賭けのモデル" },
    { t: "ブラウン運動", en: "Brownian motion", field: "確率・統計", lv: 4, def: "連続だが至る所微分不可能な、独立増分をもつ確率過程" },
    { t: "大数の法則", en: "law of large numbers", field: "確率・統計", lv: 2, def: "標本平均が母平均に収束するという法則" },
    { t: "中心極限定理", en: "central limit theorem", field: "確率・統計", lv: 3, def: "和の分布が正規分布に近づくという普遍現象" },
    { t: "伊藤積分", en: "Itô integral", field: "確率・統計", lv: 5, def: "ブラウン運動に関する確率積分。非有界変動でも定義できる" },
    { t: "停止時刻", en: "stopping time", field: "確率・統計", lv: 4, def: "現在までの情報だけで判定できる、ランダムな時刻" },
    { t: "エルゴード性", en: "ergodicity", field: "確率・統計", lv: 4, def: "時間平均と空間平均が一致する性質" },

    /* ---------------- 作用素環・関数解析 ---------------- */
    { t: "ヒルベルト空間", en: "Hilbert space", field: "作用素環・関数解析", lv: 3, def: "内積を持ち完備な空間。直交分解が使える" },
    { t: "バナッハ空間", en: "Banach space", field: "作用素環・関数解析", lv: 3, def: "ノルムを持ち完備なベクトル空間" },
    { t: "自己共役", en: "self-adjoint", field: "作用素環・関数解析", lv: 4, def: "A = A† を満たす作用素。実スペクトルを持ち観測量に対応する" },
    { t: "コンパクト作用素", en: "compact operator", field: "作用素環・関数解析", lv: 4, def: "有界集合をコンパクト集合に近い像へ写す作用素。行列に近い振る舞い" },
    { t: "スペクトル", en: "spectrum", field: "作用素環・関数解析", lv: 4, def: "A − λI が可逆にならない λ の集合。固有値の一般化" },
    { t: "レゾルベント", en: "resolvent", field: "作用素環・関数解析", lv: 4, def: "(A − λI)^{−1}。スペクトルの外側で解析的に振る舞う" },
    { t: "C*代数", en: "C*-algebra", field: "作用素環・関数解析", lv: 5, def: "‖a*a‖=‖a‖² を満たすノルム付き対合代数。非可換位相空間の代数" },
    { t: "フォン・ノイマン環", en: "von Neumann algebra", field: "作用素環・関数解析", lv: 5, def: "弱位相で閉じた作用素環。M″ = M で特徴づけられる" },
    { t: "GNS構成", en: "GNS construction", field: "作用素環・関数解析", lv: 5, def: "状態からヒルベルト空間と表現を作り出す構成法" },
    { t: "閉グラフ定理", en: "closed graph theorem", field: "作用素環・関数解析", lv: 4, def: "グラフが閉ならば作用素は有界、というバナッハ空間の定理" },

    /* ---------------- 表現論・群論 ---------------- */
    { t: "既約表現", en: "irreducible representation", field: "表現論・群論", lv: 3, def: "自明でない不変部分空間を持たない表現。表現の原子" },
    { t: "指標", en: "character", field: "表現論・群論", lv: 4, def: "表現行列のトレース。共役類上の関数で表現を決定する" },
    { t: "シューアの補題", en: "Schur's lemma", field: "表現論・群論", lv: 4, def: "既約表現の間の絡作用素はゼロかスカラー倍しかない" },
    { t: "誘導表現", en: "induced representation", field: "表現論・群論", lv: 5, def: "部分群の表現から全体の群の表現を作る操作。制限の左随伴" },
    { t: "ルート系", en: "root system", field: "表現論・群論", lv: 5, def: "リー環の重みが作る対称的なベクトル配置。分類の骨格" },
    { t: "リー環", en: "Lie algebra", field: "表現論・群論", lv: 4, def: "リー群の単位元での接空間に括弧積を入れた代数" },
    { t: "カルタン部分代数", en: "Cartan subalgebra", field: "表現論・群論", lv: 5, def: "極大な可換部分代数。同時対角化の基準となる" },
    { t: "完全可約性", en: "complete reducibility", field: "表現論・群論", lv: 4, def: "表現が既約表現の直和に分解できる性質" },
    { t: "ヤング図形", en: "Young diagram", field: "表現論・群論", lv: 4, def: "分割を箱で表した図。対称群の既約表現を分類する" },
    { t: "共役類", en: "conjugacy class", field: "表現論・群論", lv: 3, def: "g⁻¹xg で移り合う元の集まり。指標はこの上の関数" },

    /* ---------------- 数理物理 ---------------- */
    { t: "ハミルトニアン", en: "Hamiltonian", field: "数理物理", lv: 3, def: "系の全エネルギーを表す関数・作用素。時間発展の生成子" },
    { t: "ラグランジアン", en: "Lagrangian", field: "数理物理", lv: 3, def: "運動エネルギーとポテンシャルの差。作用の被積分関数" },
    { t: "作用汎関数", en: "action functional", field: "数理物理", lv: 4, def: "経路に数値を返す汎関数。停留点が運動方程式を与える" },
    { t: "正準量子化", en: "canonical quantization", field: "数理物理", lv: 4, def: "ポアソン括弧を交換子 [·,·]/iℏ に置き換える手続き" },
    { t: "ゲージ対称性", en: "gauge symmetry", field: "数理物理", lv: 4, def: "各点ごとに独立な内部対称性。接続として場を導く" },
    { t: "くりこみ", en: "renormalization", field: "数理物理", lv: 5, def: "発散を有限個のパラメータに吸収し、スケール依存性を扱う枠組み" },
    { t: "経路積分", en: "path integral", field: "数理物理", lv: 5, def: "すべての経路の位相因子を足し上げて振幅を得る定式化" },
    { t: "対称性の自発的破れ", en: "spontaneous symmetry breaking", field: "数理物理", lv: 5, def: "法則は対称でも、基底状態が対称性を保たない現象" },
    { t: "フォック空間", en: "Fock space", field: "数理物理", lv: 5, def: "粒子数が変化する系を記述する、対称積の直和空間" },
    { t: "可積分系", en: "integrable system", field: "数理物理", lv: 5, def: "十分多くの保存量を持ち、厳密に解ける力学系" }
  ];

  var API = { TERMS: TERMS };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.TermBank = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
