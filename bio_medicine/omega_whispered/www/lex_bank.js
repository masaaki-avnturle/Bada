/*
 * lex_bank.js — 専門英語と造語のウィスパード問題銀行
 * Ω-Whispered — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * 数学・化学・物理学・薬学・経済学の論文で実際に使われる
 *   (1) 学術英語の表記・略号 (SYMBOLS)
 *   (2) 分野で意味が変わる多義語 (CTX)
 *   (3) 専門英語の語彙 (TERMS: t = 英語, en = 日本語)
 *   (4) 造語 (COIN: 語基への分解・出典・意味)
 *   (5) 語根・接辞 (MORPH)
 * を収録する。COIN からは EQUATIONS を機械的に組み立てるので、
 * 既存の「式の意味 / 式の同定」検査がそのまま「造語の意味 / 造語の同定」になる。
 *
 * 依存ゼロ。Node からも require できる。
 */
(function (root) {
  "use strict";

  var FIELDS = ["数学英語", "化学英語", "物理英語", "薬学英語", "経済英語", "情報科学英語", "学術英語共通"];

  /* 系統(math / chem / pharma / econ)との対応。他系統へ造語を配るときに使う */
  var SUBJECT_OF = {
    "数学英語": "math", "物理英語": "chem", "化学英語": "chem",
    "薬学英語": "pharma", "経済英語": "econ", "情報科学英語": "cs", "学術英語共通": "all"
  };

  /* ======================= 学術英語の表記・略号 ======================= */
  var SYMBOLS = [
    /* --- 学術英語共通 --- */
    { ch: "et al.", ja: "エト・アル", mean: "「ほか」。ラテン語 et alii の略で、3 名以上の著者を省略するときに使う", field: "学術英語共通", lv: 1 },
    { ch: "i.e.", ja: "すなわち", mean: "ラテン語 id est。直前の内容を言い換える(= that is)", field: "学術英語共通", lv: 1 },
    { ch: "e.g.", ja: "たとえば", mean: "ラテン語 exempli gratia。例を挙げる(= for example)", field: "学術英語共通", lv: 1 },
    { ch: "cf.", ja: "比較せよ", mean: "ラテン語 confer。別の箇所や文献と対照させる指示", field: "学術英語共通", lv: 2 },
    { ch: "ibid.", ja: "同上", mean: "ラテン語 ibidem。直前と同じ文献を指す", field: "学術英語共通", lv: 3 },
    { ch: "viz.", ja: "すなわち(列挙)", mean: "ラテン語 videlicet。具体的に列挙して言い直す", field: "学術英語共通", lv: 4 },
    { ch: "N.B.", ja: "注意せよ", mean: "ラテン語 nota bene。とくに注意すべき点を示す", field: "学術英語共通", lv: 3 },
    { ch: "ca.", ja: "およそ", mean: "ラテン語 circa。年代や数値の概数を示す", field: "学術英語共通", lv: 3 },
    { ch: "vs.", ja: "対", mean: "ラテン語 versus。二つを対比させる", field: "学術英語共通", lv: 1 },
    { ch: "n.d.", ja: "発行年不明", mean: "no date。引用文献に年が記載されていないとき", field: "学術英語共通", lv: 3 },
    { ch: "sic", ja: "原文のまま", mean: "引用中の誤りが原文どおりであることを示す", field: "学術英語共通", lv: 4 },
    { ch: "passim", ja: "各所に", mean: "その文献の随所に記述があることを示す", field: "学術英語共通", lv: 5 },

    /* --- 数学英語 --- */
    { ch: "iff", ja: "必要十分条件", mean: "if and only if。同値であることを表す", field: "数学英語", lv: 2 },
    { ch: "s.t.", ja: "〜を満たすように", mean: "such that(または subject to、最適化の制約条件)", field: "数学英語", lv: 2 },
    { ch: "w.l.o.g.", ja: "一般性を失わずに", mean: "without loss of generality。対称性から場合を絞ってよいという宣言", field: "数学英語", lv: 4 },
    { ch: "w.r.t.", ja: "〜に関して", mean: "with respect to。どの変数で微分するかなどを明示する", field: "数学英語", lv: 3 },
    { ch: "Q.E.D.", ja: "証明終わり", mean: "ラテン語 quod erat demonstrandum(以上が示すべきことであった)", field: "数学英語", lv: 2 },
    { ch: "a.e.", ja: "ほとんど至るところ", mean: "almost everywhere。測度ゼロの例外を除いて成り立つ", field: "数学英語", lv: 5 },
    { ch: "a.s.", ja: "ほとんど確実に", mean: "almost surely。確率 1 で成り立つ", field: "数学英語", lv: 5 },
    { ch: "resp.", ja: "それぞれ", mean: "respectively。並列した対応を簡潔に書く", field: "数学英語", lv: 3 },
    { ch: "LHS / RHS", ja: "左辺 / 右辺", mean: "left-hand side / right-hand side", field: "数学英語", lv: 2 },
    { ch: "s.t. (max)", ja: "制約条件", mean: "subject to。最大化・最小化問題の制約を導く", field: "数学英語", lv: 3 },

    /* --- 物理英語 --- */
    { ch: "SI", ja: "国際単位系", mean: "Système International d'unités。m, kg, s などの単位系", field: "物理英語", lv: 2 },
    { ch: "RMS", ja: "二乗平均平方根", mean: "root mean square。交流やゆらぎの実効値", field: "物理英語", lv: 3 },
    { ch: "FWHM", ja: "半値全幅", mean: "full width at half maximum。ピークの幅を高さ半分で測る", field: "物理英語", lv: 4 },
    { ch: "DOS", ja: "状態密度", mean: "density of states。単位エネルギーあたりの量子状態の数", field: "物理英語", lv: 4 },
    { ch: "S/N", ja: "信号対雑音比", mean: "signal-to-noise ratio。測定の質を表す基本指標", field: "物理英語", lv: 2 },
    { ch: "in situ", ja: "その場で", mean: "試料を取り出さずに、その位置・条件のまま測定すること", field: "物理英語", lv: 4 },
    { ch: "ab initio", ja: "第一原理から", mean: "経験的パラメータを使わず基本法則だけから計算すること", field: "物理英語", lv: 5 },

    /* --- 化学英語 --- */
    { ch: "aq.", ja: "水溶液", mean: "aqueous。反応式で水に溶けている状態を示す", field: "化学英語", lv: 1 },
    { ch: "conc. / dil.", ja: "濃 / 希", mean: "concentrated / dilute。試薬の濃度の別を示す", field: "化学英語", lv: 2 },
    { ch: "m.p. / b.p.", ja: "融点 / 沸点", mean: "melting point / boiling point。同定と純度の指標", field: "化学英語", lv: 2 },
    { ch: "r.t.", ja: "室温", mean: "room temperature。反応条件の記述に使う", field: "化学英語", lv: 2 },
    { ch: "NMR", ja: "核磁気共鳴", mean: "nuclear magnetic resonance。構造決定の中心的手法", field: "化学英語", lv: 3 },
    { ch: "ee", ja: "鏡像体過剰率", mean: "enantiomeric excess。不斉合成の選択性を表す", field: "化学英語", lv: 5 },
    { ch: "eq. (equiv)", ja: "当量", mean: "equivalent。反応剤の物質量比を表す", field: "化学英語", lv: 3 },
    { ch: "TLC", ja: "薄層クロマトグラフィー", mean: "thin-layer chromatography。反応の進行を簡便に追う", field: "化学英語", lv: 3 },

    /* --- 薬学英語 --- */
    { ch: "RCT", ja: "ランダム化比較試験", mean: "randomized controlled trial。因果を示す標準的な試験デザイン", field: "薬学英語", lv: 3 },
    { ch: "ITT", ja: "治療企図解析", mean: "intention-to-treat。割り付けどおりに解析して選択バイアスを避ける", field: "薬学英語", lv: 5 },
    { ch: "PP", ja: "実施計画書適合解析", mean: "per protocol。計画どおりに完遂した例だけで解析する", field: "薬学英語", lv: 5 },
    { ch: "AE / SAE", ja: "有害事象 / 重篤な有害事象", mean: "adverse event / serious adverse event。因果を問わず記録する", field: "薬学英語", lv: 3 },
    { ch: "NSAID", ja: "非ステロイド性抗炎症薬", mean: "non-steroidal anti-inflammatory drug", field: "薬学英語", lv: 3 },
    { ch: "in vitro / in vivo", ja: "試験管内 / 生体内", mean: "ラテン語で「ガラスの中で / 生きたものの中で」", field: "薬学英語", lv: 2 },
    { ch: "in silico", ja: "計算機上で", mean: "in vitro / in vivo をもじった造語。シリコン(計算機)上での実験", field: "薬学英語", lv: 4 },

    /* --- 経済英語 --- */
    { ch: "ceteris paribus", ja: "他の条件を一定として", mean: "ラテン語。着目する要因以外を固定して考える約束", field: "経済英語", lv: 3 },
    { ch: "YoY", ja: "前年同期比", mean: "year over year。季節性を避けて前年の同じ時期と比べる", field: "経済英語", lv: 2 },
    { ch: "QoQ", ja: "前期比", mean: "quarter over quarter。四半期どうしを比べる", field: "経済英語", lv: 3 },
    { ch: "CAGR", ja: "年平均成長率", mean: "compound annual growth rate。複利換算した平均成長率", field: "経済英語", lv: 3 },
    { ch: "s.a.", ja: "季節調整済み", mean: "seasonally adjusted。季節変動を取り除いた系列", field: "経済英語", lv: 4 },
    { ch: "FY", ja: "会計年度", mean: "fiscal year。暦年とずれることがある", field: "経済英語", lv: 2 },
    { ch: "ppt", ja: "パーセントポイント", mean: "percentage point。率どうしの差を表す(% との混同に注意)", field: "経済英語", lv: 3 },

    /* --- 情報科学英語 --- */
    { ch: "w.h.p.", ja: "高い確率で", mean: "with high probability。乱択アルゴリズムの解析で使う", field: "情報科学英語", lv: 5 },
    { ch: "s.t. (subject to)", ja: "制約のもとで", mean: "最適化問題の制約条件を導く", field: "情報科学英語", lv: 3 },
    { ch: "RFC", ja: "インターネット標準文書", mean: "Request for Comments。仕様が番号付きで公開される", field: "情報科学英語", lv: 3 },
    { ch: "API", ja: "アプリケーション・プログラミング・インタフェース", mean: "呼び出しの約束事。実装を隠して機能だけを見せる", field: "情報科学英語", lv: 2 },
    { ch: "POSIX", ja: "ポシックス", mean: "Portable Operating System Interface。UNIX 系 OS の共通仕様", field: "情報科学英語", lv: 4 },
    { ch: "REPL", ja: "対話実行環境", mean: "Read-Eval-Print Loop。読んで評価して表示する繰り返し", field: "情報科学英語", lv: 4 },
    { ch: "ASCII", ja: "アスキー", mean: "American Standard Code for Information Interchange。7 ビットの文字符号", field: "情報科学英語", lv: 2 },
    { ch: "UTF-8", ja: "可変長 Unicode 符号", mean: "1〜4 バイトで符号化する方式。ASCII と互換", field: "情報科学英語", lv: 3 },
    { ch: "CI/CD", ja: "継続的統合 / 継続的デリバリ", mean: "変更ごとに自動で検査し、届けるまでを自動化する運用", field: "情報科学英語", lv: 3 },
    { ch: "SLA / SLO", ja: "サービス水準合意 / 目標", mean: "可用性や応答時間について約束する水準と、内部で狙う目標", field: "情報科学英語", lv: 4 },
    { ch: "FLOPS", ja: "浮動小数点演算性能", mean: "floating point operations per second。計算機の速さの指標", field: "情報科学英語", lv: 3 },
    { ch: "P vs NP", ja: "P 対 NP 問題", mean: "解くのと検証するのは同じ難しさか、という未解決問題", field: "情報科学英語", lv: 4 }
  ];

  /* ============ 文脈依存: 同じ英単語が分野で意味を変える ============ */
  var CTX = [
    { ch: "field", items: [
      { field: "数学英語", mean: "体(たい) — 四則演算が自由にできる代数構造" },
      { field: "物理英語", mean: "場 — 空間の各点に量が割り当てられたもの" },
      { field: "経済英語", mean: "分野・業界(field study なら実地調査)" },
      { field: "薬学英語", mean: "視野・領域(顕微鏡の field of view)" }
    ]},
    { ch: "normal", items: [
      { field: "数学英語", mean: "法線の / 正規部分群の(normal subgroup)" },
      { field: "化学英語", mean: "規定濃度の(1 N 溶液)・直鎖の(n-butane)" },
      { field: "薬学英語", mean: "正常値の(検査値が基準範囲内)" },
      { field: "学術英語共通", mean: "通常の・標準的な" }
    ]},
    { ch: "regular", items: [
      { field: "数学英語", mean: "正則な(特異点がない・可逆である)" },
      { field: "薬学英語", mean: "定時の(regular dosing = 定時投与)" },
      { field: "経済英語", mean: "常用の(regular employment = 正規雇用)" },
      { field: "学術英語共通", mean: "規則的な・定期的な" }
    ]},
    { ch: "positive", items: [
      { field: "数学英語", mean: "正の(0 より大きい)・正定値の" },
      { field: "薬学英語", mean: "陽性の(検査で反応あり)" },
      { field: "物理英語", mean: "正電荷の" },
      { field: "経済英語", mean: "実証的な(positive economics = 事実の記述、規範と対比)" }
    ]},
    { ch: "elastic", items: [
      { field: "物理英語", mean: "弾性の(elastic collision = 弾性衝突)" },
      { field: "経済英語", mean: "弾力的な(価格の変化に需要が敏感)" },
      { field: "化学英語", mean: "弾性のある高分子の性質(elastomer)" },
      { field: "学術英語共通", mean: "融通のきく" }
    ]},
    { ch: "derivative", items: [
      { field: "数学英語", mean: "導関数・微分係数" },
      { field: "経済英語", mean: "デリバティブ(原資産から価値が派生する金融商品)" },
      { field: "化学英語", mean: "誘導体(母体化合物から作られた化合物)" },
      { field: "学術英語共通", mean: "派生した・独創性に乏しい" }
    ]},
    { ch: "solution", items: [
      { field: "化学英語", mean: "溶液" },
      { field: "数学英語", mean: "解(方程式を満たす値・関数)" },
      { field: "薬学英語", mean: "液剤(製剤の剤形のひとつ)" },
      { field: "学術英語共通", mean: "解決策" }
    ]},
    { ch: "volume", items: [
      { field: "物理英語", mean: "体積" },
      { field: "経済英語", mean: "出来高・取引量" },
      { field: "薬学英語", mean: "分布容積の容積(volume of distribution)" },
      { field: "学術英語共通", mean: "巻(雑誌の Vol.)" }
    ]},
    { ch: "order", items: [
      { field: "数学英語", mean: "位数・階数・順序" },
      { field: "化学英語", mean: "反応次数(first-order reaction)" },
      { field: "経済英語", mean: "注文・発注" },
      { field: "学術英語共通", mean: "桁(order of magnitude = 桁違い)" }
    ]},
    { ch: "degenerate", items: [
      { field: "物理英語", mean: "縮退した(同じエネルギーの状態が複数ある)" },
      { field: "数学英語", mean: "退化した(次元が落ちる・特別な場合になる)" },
      { field: "化学英語", mean: "縮重した軌道(degenerate orbitals)" },
      { field: "学術英語共通", mean: "劣化する" }
    ]},
    { ch: "resolution", items: [
      { field: "物理英語", mean: "分解能(どこまで細かく識別できるか)" },
      { field: "化学英語", mean: "光学分割(ラセミ体を鏡像体に分ける)" },
      { field: "数学英語", mean: "分解(加群の resolution)" },
      { field: "学術英語共通", mean: "解決・決議" }
    ]},
    { ch: "spectrum", items: [
      { field: "物理英語", mean: "スペクトル(波長・エネルギーごとの強度分布)" },
      { field: "数学英語", mean: "作用素のスペクトル(固有値の一般化)" },
      { field: "薬学英語", mean: "抗菌スペクトル(効く菌の範囲)" },
      { field: "学術英語共通", mean: "連続的な幅・範囲" }
    ]},
    { ch: "potency", items: [
      { field: "薬学英語", mean: "力価 — 同じ効果を出すのに必要な用量の小ささ(EC50 が小さいほど強力)" },
      { field: "化学英語", mean: "有効成分の含量・効力" },
      { field: "学術英語共通", mean: "潜在的な力" },
      { field: "経済英語", mean: "政策の効き目(policy potency)" }
    ]},
    { ch: "kernel", items: [
      { field: "情報科学英語", mean: "OS の中核(特権モードで動く部分)。機械学習ではカーネル法の核関数" },
      { field: "数学英語", mean: "核(準同型で 0 に写る元の集合)・積分核" },
      { field: "物理英語", mean: "積分核(グリーン関数の核)" },
      { field: "学術英語共通", mean: "穀粒・核心" }
    ]},
    { ch: "thread", items: [
      { field: "情報科学英語", mean: "スレッド(同じプロセス内で並行に走る実行の流れ)" },
      { field: "学術英語共通", mean: "議論の流れ・一連の投稿" },
      { field: "化学英語", mean: "ねじ山(器具の接合部)" },
      { field: "数学英語", mean: "糸のように連なる列(比喩的な用法)" }
    ]},
    { ch: "bug", items: [
      { field: "情報科学英語", mean: "不具合。1947 年に実際の蛾が挟まった逸話が有名だが、語自体はそれ以前からある" },
      { field: "薬学英語", mean: "病原体(俗な言い方。superbug = 多剤耐性菌)" },
      { field: "学術英語共通", mean: "虫" },
      { field: "経済英語", mean: "熱狂・過熱(the bug for …)" }
    ]},
    { ch: "protocol", items: [
      { field: "情報科学英語", mean: "通信規約(TCP/IP のような取り決め)" },
      { field: "薬学英語", mean: "試験実施計画書(臨床試験の手順書)" },
      { field: "化学英語", mean: "実験手順(合成の標準手順)" },
      { field: "学術英語共通", mean: "儀礼・議定書" }
    ]},
    { ch: "stable", items: [
      { field: "数学英語", mean: "安定な(摂動で解が離れていかない)" },
      { field: "化学英語", mean: "安定な(分解しにくい)" },
      { field: "経済英語", mean: "安定した(物価や雇用が変動しない)" },
      { field: "物理英語", mean: "安定な平衡(ポテンシャルの極小)" }
    ]}
  ];

  /* ============================== 造語 ============================== */
  /* kind: 混成語(portmanteau) / 新古典複合語 / 頭字語 / 人名由来 / 借用 / 縮約 */
  var COIN = [
    /* ---------- 物理 ---------- */
    { w: "photon", ja: "光子", field: "物理英語", lv: 2, kind: "新古典複合語",
      parts: [{ p: "phōs / phōt- (ギリシャ語: 光)" }, { p: "-on (粒子・量子を表す接尾辞)" }],
      mean: "電磁場の量子。光をエネルギーの粒として数える単位",
      note: "Lewis が 1926 年に命名。-on は ion から広がった「粒子」の接尾辞で、以後の素粒子名の型になった。" },
    { w: "phonon", ja: "フォノン(音子)", field: "物理英語", lv: 4, kind: "新古典複合語",
      parts: [{ p: "phōnē (ギリシャ語: 音)" }, { p: "-on (粒子・量子)" }],
      mean: "結晶格子の振動を粒子として扱った量子",
      note: "photon の型をそのまま音に当てはめた語。素励起に -on を付ける命名法の代表例。" },
    { w: "exciton", ja: "励起子", field: "物理英語", lv: 4, kind: "混成語",
      parts: [{ p: "excitation (励起)" }, { p: "-on (粒子・量子)" }],
      mean: "電子と正孔がクーロン力で束縛された、電気的に中性な励起状態",
      note: "半導体・有機 EL の発光を説明する。plasmon(プラズマ)・magnon(磁気)も同じ作り方。" },
    { w: "positron", ja: "陽電子", field: "物理英語", lv: 3, kind: "混成語",
      parts: [{ p: "positive (正の)" }, { p: "electron (電子)" }],
      mean: "電子と同じ質量で正電荷をもつ反粒子",
      note: "Anderson が 1932 年に発見。反粒子であることを「正の電子」という縮約で表した。" },
    { w: "neutrino", ja: "ニュートリノ", field: "物理英語", lv: 4, kind: "借用",
      parts: [{ p: "neutro (イタリア語: 中性の)" }, { p: "-ino (イタリア語の指小辞: 小さい)" }],
      mean: "電荷をもたず質量が極めて小さい素粒子",
      note: "Fermi による命名。「小さくて中性のもの」。同じ指小辞は neutralino などにも使われる。" },
    { w: "quark", ja: "クォーク", field: "物理英語", lv: 4, kind: "借用",
      parts: [{ p: "Joyce の小説の一節 \"Three quarks for Muster Mark\"" }],
      mean: "陽子・中性子を構成する素粒子",
      note: "Gell-Mann が 1964 年に、3 個で 1 組という性質に合う語として小説から借りた。意味を持たない語をあえて選んだ例。" },
    { w: "qubit", ja: "量子ビット", field: "物理英語", lv: 4, kind: "混成語",
      parts: [{ p: "quantum (量子)" }, { p: "bit (情報の単位)" }],
      mean: "0 と 1 の重ね合わせを取りうる量子情報の最小単位",
      note: "Schumacher が 1995 年に命名。古典情報の bit(binary + digit)自体も混成語。" },
    { w: "spintronics", ja: "スピントロニクス", field: "物理英語", lv: 5, kind: "混成語",
      parts: [{ p: "spin (電子のスピン)" }, { p: "electronics (電子工学)" }],
      mean: "電荷だけでなく電子のスピンも情報として使う技術分野",
      note: "巨大磁気抵抗(GMR)によるハードディスク読み取りヘッドが最初の実用例。" },
    { w: "laser", ja: "レーザー", field: "物理英語", lv: 3, kind: "頭字語",
      parts: [{ p: "Light Amplification by" }, { p: "Stimulated Emission of Radiation" }],
      mean: "誘導放出によって光を増幅し、位相のそろった光を出す装置",
      note: "先行する maser(Microwave…)の M を Light に替えた。頭字語が普通名詞化した代表例。" },
    { w: "soliton", ja: "ソリトン", field: "物理英語", lv: 5, kind: "混成語",
      parts: [{ p: "solitary wave (孤立波)" }, { p: "-on (粒子)" }],
      mean: "形を崩さずに伝わり、衝突しても形が戻る孤立波",
      note: "Zabusky と Kruskal が 1965 年に命名。波なのに粒子のようにふるまうため -on を付けた。" },

    /* ---------- 化学 ---------- */
    { w: "entropy", ja: "エントロピー", field: "化学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "en- (ギリシャ語: 中に)" }, { p: "tropē (ギリシャ語: 転換)" }],
      mean: "エネルギーの散らばり方を表す状態量。孤立系では減らない",
      note: "Clausius が 1865 年に、energy と語形をそろえる意図で作った。「変化の内容量」の含み。" },
    { w: "enthalpy", ja: "エンタルピー", field: "化学英語", lv: 4, kind: "新古典複合語",
      parts: [{ p: "en- (ギリシャ語: 中に)" }, { p: "thalpein (ギリシャ語: 温める)" }],
      mean: "内部エネルギーに圧力×体積を加えた、定圧下の熱量を扱う状態量",
      note: "Onnes による命名とされる。entropy と対になる語形にそろえてある。" },
    { w: "isotope", ja: "同位体", field: "化学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "isos (ギリシャ語: 等しい)" }, { p: "topos (ギリシャ語: 場所)" }],
      mean: "陽子数が同じで中性子数が違う核種。周期表で同じ位置を占める",
      note: "Soddy が 1913 年に命名。周期表の「同じ場所」に入るという着眼がそのまま語になった。" },
    { w: "polymer", ja: "重合体", field: "化学英語", lv: 2, kind: "新古典複合語",
      parts: [{ p: "poly- (ギリシャ語: 多くの)" }, { p: "meros (ギリシャ語: 部分)" }],
      mean: "同じ単位が多数つながった巨大分子",
      note: "対になる monomer(単一の部分)・oligomer(少数の部分)も同じ語基でできている。" },
    { w: "enzyme", ja: "酵素", field: "化学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "en- (ギリシャ語: 中に)" }, { p: "zymē (ギリシャ語: 酵母)" }],
      mean: "生体内の反応を触媒するタンパク質",
      note: "「酵母の中にあるもの」。個々の酵素名に付く -ase はこの語から生まれた接尾辞。" },
    { w: "chirality", ja: "キラリティー(掌性)", field: "化学英語", lv: 4, kind: "新古典複合語",
      parts: [{ p: "cheir (ギリシャ語: 手)" }, { p: "-ality (性質を表す接尾辞)" }],
      mean: "鏡像と重ね合わせられない性質",
      note: "Kelvin による命名。左手と右手の関係が語源そのもので、医薬品の光学異性体の議論に直結する。" },
    { w: "catalysis", ja: "触媒作用", field: "化学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "kata- (ギリシャ語: 下へ・完全に)" }, { p: "lysis (ギリシャ語: 分解)" }],
      mean: "自身は変化せずに反応速度を上げる働き",
      note: "Berzelius が 1835 年に命名。-lysis は hydrolysis(加水分解)・electrolysis(電気分解)にも現れる。" },
    { w: "graphene", ja: "グラフェン", field: "化学英語", lv: 4, kind: "混成語",
      parts: [{ p: "graphite (黒鉛)" }, { p: "-ene (二重結合を含む炭化水素の接尾辞)" }],
      mean: "炭素原子が六角形に並んだ厚さ 1 原子のシート",
      note: "-ene は benzene・ethylene と同じ接尾辞。fullerene は建築家 Fuller の名から。" },

    /* ---------- 薬学 ---------- */
    { w: "vitamin", ja: "ビタミン", field: "薬学英語", lv: 2, kind: "混成語",
      parts: [{ p: "vital (生命に必要な)" }, { p: "amine (アミン)" }],
      mean: "微量で生理機能を保つ必須の有機化合物",
      note: "Funk が 1912 年に vitamine と命名。のちにアミンでないものが見つかり、語尾の e を落として vitamin になった。" },
    { w: "aspirin", ja: "アスピリン", field: "薬学英語", lv: 3, kind: "混成語",
      parts: [{ p: "a- (acetyl: アセチル基)" }, { p: "spir- (Spiraea: シモツケ属)" }, { p: "-in (薬物の接尾辞)" }],
      mean: "アセチルサリチル酸。解熱鎮痛・抗血小板薬",
      note: "サリチル酸がもとはシモツケ属から得られたことに由来する商品名が、そのまま一般名になった。" },
    { w: "paracetamol", ja: "パラセタモール", field: "薬学英語", lv: 4, kind: "縮約",
      parts: [{ p: "para-" }, { p: "acetyl" }, { p: "amino" }, { p: "phenol" }],
      mean: "アセトアミノフェン。化学名 para-acetylaminophenol を縮めた名前",
      note: "米国では別の縮め方をした acetaminophen が使われる。同じ物質が地域で違う一般名を持つ例。" },
    { w: "ibuprofen", ja: "イブプロフェン", field: "薬学英語", lv: 4, kind: "縮約",
      parts: [{ p: "iso-butyl" }, { p: "propanoic" }, { p: "phenolic" }],
      mean: "プロピオン酸系の非ステロイド性抗炎症薬",
      note: "化学構造の三つの部分をつないだ名前。語尾 -profen はこの系統の薬に共通のステム。" },
    { w: "antibiotic", ja: "抗生物質", field: "薬学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "anti- (ギリシャ語: 対抗する)" }, { p: "bios (ギリシャ語: 生命)" }],
      mean: "微生物が作る、他の微生物の生育を抑える物質",
      note: "Waksman による命名。「生命に対抗する」だが、対象は病原微生物に限られる。" },
    { w: "agonist", ja: "作動薬", field: "薬学英語", lv: 3, kind: "借用",
      parts: [{ p: "agōnistēs (ギリシャ語: 競技者・行動する者)" }],
      mean: "受容体に結合して、内因性物質と同じ反応を起こす薬",
      note: "対語の antagonist は anti-(対抗)+ agōnistēs。競技場の比喩がそのまま薬理学の基本語彙になった。" },
    { w: "biosimilar", ja: "バイオ後続品", field: "薬学英語", lv: 4, kind: "混成語",
      parts: [{ p: "bio- (生物由来の)" }, { p: "similar (類似の)" }],
      mean: "先行するバイオ医薬品と同等・同質と評価された後続品",
      note: "低分子の generic と違い完全に同一にはできないため、「同一」ではなく「類似」という語が選ばれた。" },
    { w: "theranostics", ja: "セラノスティクス", field: "薬学英語", lv: 5, kind: "混成語",
      parts: [{ p: "therapy (治療)" }, { p: "diagnostics (診断)" }],
      mean: "診断と治療を同じ分子・同じ薬剤で一体化させる手法",
      note: "放射性標識薬で、診断用核種と治療用核種を入れ替える設計が代表例。" },
    { w: "in silico", ja: "イン・シリコ", field: "薬学英語", lv: 4, kind: "混成語",
      parts: [{ p: "in vitro / in vivo のラテン語の型" }, { p: "silicon (ケイ素 = 計算機)" }],
      mean: "計算機上で行う実験・予測",
      note: "既存のラテン語表現の型に新しい語を差し込んだ造語。creative analogy による命名の好例。" },

    /* ---------- 数学 ---------- */
    { w: "algorithm", ja: "アルゴリズム", field: "数学英語", lv: 2, kind: "人名由来",
      parts: [{ p: "al-Khwārizmī (9 世紀の数学者の名)" }],
      mean: "有限の手順で答えに至る計算の手続き",
      note: "人名のラテン語形 Algoritmi が「計算法」を意味する普通名詞になった。" },
    { w: "algebra", ja: "代数学", field: "数学英語", lv: 2, kind: "借用",
      parts: [{ p: "al-jabr (アラビア語: 移項・接骨)" }],
      mean: "数の代わりに文字を置いて構造を扱う数学の分野",
      note: "al-Khwārizmī の著書名から。方程式の項を移す操作を「折れた骨をつなぐ」に喩えた語。" },
    { w: "logarithm", ja: "対数", field: "数学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "logos (ギリシャ語: 比・言葉)" }, { p: "arithmos (ギリシャ語: 数)" }],
      mean: "指数の逆演算。積を和に変える",
      note: "Napier が 1614 年に命名。「比の数」。掛け算を足し算に落とす道具として作られた。" },
    { w: "topology", ja: "位相幾何学", field: "数学英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "topos (ギリシャ語: 場所)" }, { p: "logos (ギリシャ語: 学)" }],
      mean: "連続変形で変わらない性質を扱う幾何学",
      note: "Listing が 1847 年に命名。それ以前は analysis situs(位置の解析)と呼ばれていた。" },
    { w: "homeomorphism", ja: "同相写像", field: "数学英語", lv: 4, kind: "新古典複合語",
      parts: [{ p: "homoios (ギリシャ語: 同じような)" }, { p: "morphē (ギリシャ語: 形)" }, { p: "-ism" }],
      mean: "連続で逆も連続な全単射。位相的に同じとみなす対応",
      note: "homo-(同じ)+ morph(形)の型は homomorphism・isomorphism・endomorphism と体系をなす。" },
    { w: "fractal", ja: "フラクタル", field: "数学英語", lv: 4, kind: "借用",
      parts: [{ p: "fractus (ラテン語: 砕けた・不規則な)" }],
      mean: "どの尺度で見ても似た構造が現れる図形",
      note: "Mandelbrot が 1975 年に造語。整数でない次元を持ちうることを語形で示した。" },
    { w: "eigenvalue", ja: "固有値", field: "数学英語", lv: 3, kind: "混成語",
      parts: [{ p: "eigen (ドイツ語: 固有の)" }, { p: "value (英語: 値)" }],
      mean: "線形変換が方向を変えずに引き伸ばす倍率",
      note: "ドイツ語 Eigenwert の半分だけを訳した独英混成語。eigenvector・eigenstate も同じ型。" },
    { w: "tensor", ja: "テンソル", field: "数学英語", lv: 4, kind: "借用",
      parts: [{ p: "tendere (ラテン語: 張る)" }],
      mean: "座標変換に対して決まった規則で成分が変わる多重線形量",
      note: "もとは弾性体の「張力」を表す語。Voigt が現在の意味で用い、一般相対論で不可欠になった。" },
    { w: "googol", ja: "グーゴル", field: "数学英語", lv: 3, kind: "借用",
      parts: [{ p: "Kasner の甥が思いついた無意味語" }],
      mean: "10 の 100 乗",
      note: "1920 年の命名。検索エンジンの社名はこの語の綴り違いに由来する。" },

    /* ---------- 経済 ---------- */
    { w: "stagflation", ja: "スタグフレーション", field: "経済英語", lv: 3, kind: "混成語",
      parts: [{ p: "stagnation (停滞)" }, { p: "inflation (物価上昇)" }],
      mean: "景気の停滞と物価上昇が同時に起こる状態",
      note: "1965 年の英国議会で使われた語。従来のフィリップス曲線では説明できない現象に名前が必要になった。" },
    { w: "econometrics", ja: "計量経済学", field: "経済英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "economy (経済)" }, { p: "-metrics (ギリシャ語 metron: 測る)" }],
      mean: "経済理論・統計・データを結び、経済現象を数量的に検証する分野",
      note: "Frisch が 1926 年に命名。biometrics・psychometrics と同じ「測定の学」の型。" },
    { w: "oligopoly", ja: "寡占", field: "経済英語", lv: 3, kind: "新古典複合語",
      parts: [{ p: "oligos (ギリシャ語: 少数の)" }, { p: "pōlein (ギリシャ語: 売る)" }],
      mean: "少数の売り手が市場を占める状態",
      note: "monopoly(単独の売り手)、monopsony(単独の買い手)と対をなす。買い手側は -psōnia(買う)。" },
    { w: "fintech", ja: "フィンテック", field: "経済英語", lv: 2, kind: "混成語",
      parts: [{ p: "financial (金融の)" }, { p: "technology (技術)" }],
      mean: "情報技術を用いた金融サービスの総称",
      note: "近年の混成語は語頭を切って足す形が多い(fin + tech, ed + tech, bio + tech)。" },
    { w: "stakeholder", ja: "利害関係者", field: "経済英語", lv: 3, kind: "混成語",
      parts: [{ p: "stake (賭け金・利害)" }, { p: "holder (持つ人)" }],
      mean: "その活動に利害を持つすべての関係者",
      note: "stockholder(株主)をもじって作られ、株主以外にも視野を広げる主張とともに広まった。" },
    { w: "nudge", ja: "ナッジ", field: "経済英語", lv: 3, kind: "借用",
      parts: [{ p: "nudge (英語の日常語: 肘で軽くつつく)" }],
      mean: "選択の自由を残したまま、望ましい行動へ後押しする設計",
      note: "Thaler と Sunstein が 2008 年に学術用語として定着させた。日常語を専門語に転用した例。" },
    { w: "Abenomics", ja: "アベノミクス", field: "経済英語", lv: 3, kind: "混成語",
      parts: [{ p: "人名" }, { p: "economics (経済政策)" }],
      mean: "特定の政権が掲げた一連の経済政策を指す通称",
      note: "Reaganomics(1980 年代)以来の型。-nomics は人名に付いて政策パッケージを指す接尾辞になった。" },
    /* ---------- 情報科学 ---------- */
    { w: "bit", ja: "ビット", field: "情報科学英語", lv: 2, kind: "混成語",
      parts: [{ p: "binary (2 進の)" }, { p: "digit (桁)" }],
      mean: "情報量の最小単位。2 値のどちらかを表す",
      note: "Tukey が 1946 年ごろに提案し、Shannon が 1948 年の論文で採用した。qubit はこの語を土台にしている。" },
    { w: "byte", ja: "バイト", field: "情報科学英語", lv: 2, kind: "借用",
      parts: [{ p: "bite (ひと口) の綴りを変えた語" }],
      mean: "1 文字ぶんをまとめて扱う単位。今日では 8 ビット",
      note: "bit と綴りが紛れないよう i を y に替えた。フランス語では 8 ビットであることを明示して octet と呼ぶ。" },
    { w: "pixel", ja: "画素", field: "情報科学英語", lv: 2, kind: "混成語",
      parts: [{ p: "picture (画像)" }, { p: "element (要素)" }],
      mean: "画像を構成する最小の点",
      note: "voxel は volume + element で立体の画素。texel(texture + element)も同じ作り方。" },
    { w: "codec", ja: "コーデック", field: "情報科学英語", lv: 3, kind: "混成語",
      parts: [{ p: "coder (符号化器)" }, { p: "decoder (復号器)" }],
      mean: "符号化と復号を行う一組の仕組み",
      note: "modem(modulator + demodulator)と同じ、対になる装置名を縮めて足す型。" },
    { w: "modem", ja: "モデム", field: "情報科学英語", lv: 3, kind: "混成語",
      parts: [{ p: "modulator (変調器)" }, { p: "demodulator (復調器)" }],
      mean: "デジタル信号を回線に載る波形へ変換し、また戻す装置",
      note: "codec と同型の造語。往復する二つの機能を 1 語にまとめている。" },
    { w: "malware", ja: "悪意のあるソフトウェア", field: "情報科学英語", lv: 3, kind: "混成語",
      parts: [{ p: "malicious (悪意のある)" }, { p: "software (ソフトウェア)" }],
      mean: "利用者に害を与えることを目的とした software の総称",
      note: "software 自体が hardware をもじった造語(hard/soft の対比)。firmware・freeware も同じ系列。" },
    { w: "phishing", ja: "フィッシング詐欺", field: "情報科学英語", lv: 3, kind: "混成語",
      parts: [{ p: "fishing (釣り)" }, { p: "ph-（phreaking の綴りに合わせた置き換え)" }],
      mean: "偽の画面や連絡で認証情報を釣り出す攻撃",
      note: "f を ph に替えるのは電話をハックする phreaking(phone + freak)以来の綴りの遊び。" },
    { w: "blog", ja: "ブログ", field: "情報科学英語", lv: 1, kind: "縮約",
      parts: [{ p: "web (ウェブ)" }, { p: "log (記録)" }],
      mean: "日付順に記事を並べて公開する形式のサイト",
      note: "weblog を we + blog と切り直した冗談から広まった。切る位置が語を作り替えた例。" },
    { w: "cybernetics", ja: "サイバネティクス", field: "情報科学英語", lv: 4, kind: "新古典複合語",
      parts: [{ p: "kybernētēs (ギリシャ語: 舵取り)" }, { p: "-ics (学問を表す接尾辞)" }],
      mean: "生物と機械に共通する制御と通信の理論",
      note: "Wiener が 1948 年に命名。ここから cyberspace・cyborg・cybersecurity と cyber- が広がった。" },
    { w: "cyborg", ja: "サイボーグ", field: "情報科学英語", lv: 3, kind: "混成語",
      parts: [{ p: "cybernetic (制御の)" }, { p: "organism (生体)" }],
      mean: "機械と一体化した生体",
      note: "1960 年に宇宙飛行の文脈で提案された語。cybernetics から派生した接頭辞 cyber- の初期の例。" },
    { w: "boolean", ja: "ブール値", field: "情報科学英語", lv: 2, kind: "人名由来",
      parts: [{ p: "George Boole (19 世紀の論理学者の名)" }],
      mean: "真か偽の 2 値をとる型",
      note: "人名がそのまま型名になった。Turing machine・Hamming distance・Markov chain も同じ人名由来。" },
    { w: "daemon", ja: "デーモン(常駐プロセス)", field: "情報科学英語", lv: 4, kind: "借用",
      parts: [{ p: "daimōn (ギリシャ語: 見えない働き手・精霊)" }],
      mean: "背後で常時動き続けるプロセス",
      note: "マクスウェルの悪魔(Maxwell's demon)にちなむとされる。悪霊の demon とは綴りを分けている。" },
    { w: "wiki", ja: "ウィキ", field: "情報科学英語", lv: 2, kind: "借用",
      parts: [{ p: "wiki wiki (ハワイ語: 速い)" }],
      mean: "誰でも編集できる形式のウェブサイト",
      note: "Cunningham が 1995 年に命名。英語以外の日常語がそのまま情報科学の術語になった例。" },
    { w: "avatar", ja: "アバター", field: "情報科学英語", lv: 3, kind: "借用",
      parts: [{ p: "avatāra (サンスクリット語: 神の化身)" }],
      mean: "利用者を画面上で表す分身",
      note: "宗教用語が仮想空間の語に転用された。emoji(絵文字)のように、他言語からの借用も情報科学には多い。" },
    { w: "spam", ja: "迷惑メール", field: "情報科学英語", lv: 2, kind: "借用",
      parts: [{ p: "Monty Python のコントで連呼される缶詰肉の商品名" }],
      mean: "無差別に大量に送りつけられるメッセージ",
      note: "「同じ語が延々と繰り返される」というコントの情景がそのまま比喩になった。" },
    { w: "firmware", ja: "ファームウェア", field: "情報科学英語", lv: 3, kind: "混成語",
      parts: [{ p: "firm (固い、hard と soft の中間)" }, { p: "-ware (software の型)" }],
      mean: "機器に組み込まれ、書き換えは可能だが普段は固定されている制御プログラム",
      note: "hardware と software の中間という位置づけを、語の硬さの度合いで表している。" },
    { w: "Brexit", ja: "ブレグジット", field: "経済英語", lv: 2, kind: "混成語",
      parts: [{ p: "Britain (英国)" }, { p: "exit (離脱)" }],
      mean: "英国の欧州連合からの離脱",
      note: "Grexit(ギリシャの離脱懸念)が先にあり、その型を借りた。造語が政治日程の呼称そのものになった例。" }
  ];

  /* 語基の表示用の断片(説明の括弧を落とす)を各造語に持たせる。
     瞬読で散らしてよいのは、断片が 2 つ以上あり、かつ断片に答えの語そのものが
     含まれないものだけ(borrowing は語そのものが語源なので散らせない)。 */
  COIN.forEach(function (c) {
    c.frags = c.parts.map(function (p) {
      return p.p.replace(/\([^)]*\)/g, "").replace(/\s+/g, " ").trim();
    }).filter(function (x) { return x; });
    var w = c.w.toLowerCase();
    c.flashable = c.frags.length >= 2 && !c.frags.some(function (f) {
      return f.toLowerCase().indexOf(w) >= 0;
    });
  });

  /* COIN から設問素材を組み立てる。
     語基を合成した造語は「語 = 語基 + 語基」、借用・人名由来は「語 ← 由来」で表す。 */
  COIN.forEach(function (c) {
    c.formula = c.frags.length >= 2
      ? c.w + " = " + c.frags.join(" + ")
      : c.w + " ← " + c.parts.map(function (p) { return p.p; }).join(" / ");
  });
  var EQUATIONS = COIN.map(function (c) {
    return {
      eq: c.formula, name: c.ja, field: c.field, lv: c.lv,
      mean: c.mean, why: c.note, coin: c
    };
  });

  /* ============================== 語根・接辞 ============================== */
  var MORPH = [
    { m: "-on", from: "ion から広がった接尾辞", mean: "粒子・量子・素励起", ex: ["photon", "phonon", "exciton", "soliton"], field: "物理英語", lv: 3 },
    { m: "-ase", from: "enzyme(diastase)から", mean: "酵素", ex: ["protease", "lipase", "polymerase"], field: "薬学英語", lv: 3 },
    { m: "-ose", from: "glucose から", mean: "糖", ex: ["glucose", "sucrose", "lactose"], field: "化学英語", lv: 3 },
    { m: "-ol", from: "alcohol から", mean: "アルコール(ヒドロキシ基をもつ)", ex: ["ethanol", "phenol", "menthol"], field: "化学英語", lv: 2 },
    { m: "-ene", from: "ギリシャ語系の接尾辞", mean: "二重結合を含む炭化水素", ex: ["ethylene", "benzene", "graphene"], field: "化学英語", lv: 3 },
    { m: "-lysis", from: "ギリシャ語 lysis", mean: "分解", ex: ["hydrolysis", "electrolysis", "catalysis"], field: "化学英語", lv: 3 },
    { m: "iso-", from: "ギリシャ語 isos", mean: "等しい・同じ", ex: ["isotope", "isomer", "isotherm"], field: "化学英語", lv: 2 },
    { m: "homo- / hetero-", from: "ギリシャ語 homos / heteros", mean: "同じ / 異なる", ex: ["homogeneous", "heterogeneous", "homomorphism"], field: "数学英語", lv: 3 },
    { m: "poly- / mono- / oligo-", from: "ギリシャ語 polys / monos / oligos", mean: "多い / 単一 / 少数", ex: ["polymer", "monomer", "oligopoly"], field: "化学英語", lv: 2 },
    { m: "-morph", from: "ギリシャ語 morphē", mean: "形", ex: ["homeomorphism", "isomorphism", "polymorphism"], field: "数学英語", lv: 3 },
    { m: "-logy", from: "ギリシャ語 logos", mean: "〜学・〜論", ex: ["topology", "pharmacology", "morphology"], field: "学術英語共通", lv: 1 },
    { m: "-metry / -metrics", from: "ギリシャ語 metron", mean: "測定・計量", ex: ["geometry", "econometrics", "spectrometry"], field: "経済英語", lv: 3 },
    { m: "-nomics", from: "economics の切り出し", mean: "(人名に付いて)経済政策の体系", ex: ["Reaganomics", "Abenomics"], field: "経済英語", lv: 4 },
    { m: "endo- / exo-", from: "ギリシャ語 endon / exō", mean: "内側の / 外側の", ex: ["endothermic", "exothermic", "endogenous"], field: "化学英語", lv: 3 },
    { m: "hypo- / hyper-", from: "ギリシャ語 hypo / hyper", mean: "下の・不足 / 上の・過剰", ex: ["hypotension", "hyperglycemia", "hypothesis"], field: "薬学英語", lv: 2 },
    { m: "anti-", from: "ギリシャ語 anti", mean: "対抗する・逆の", ex: ["antibiotic", "antagonist", "antiparticle"], field: "薬学英語", lv: 2 },
    { m: "-gen / -genic", from: "ギリシャ語 gennan", mean: "生じさせる", ex: ["hydrogen", "carcinogen", "endogenous"], field: "化学英語", lv: 3 },
    { m: "-oid", from: "ギリシャ語 -oeidēs", mean: "〜のような形の", ex: ["ellipsoid", "steroid", "colloid"], field: "数学英語", lv: 3 },
    { m: "quasi-", from: "ラテン語 quasi", mean: "準〜・ほぼ〜", ex: ["quasiparticle", "quasi-linear", "quasi-experiment"], field: "学術英語共通", lv: 4 },
    { m: "pseudo-", from: "ギリシャ語 pseudēs", mean: "疑似の・偽の", ex: ["pseudocode", "pseudoinverse", "pseudo-random"], field: "数学英語", lv: 3 },
    { m: "macro- / micro-", from: "ギリシャ語 makros / mikros", mean: "大きい / 小さい", ex: ["macroeconomics", "microscope", "macromolecule"], field: "経済英語", lv: 1 },
    { m: "eigen-", from: "ドイツ語 eigen", mean: "固有の", ex: ["eigenvalue", "eigenvector", "eigenstate"], field: "数学英語", lv: 3 },
    { m: "-tropy / -tropic", from: "ギリシャ語 tropē", mean: "転換・向き", ex: ["entropy", "isotropic", "phototropic"], field: "物理英語", lv: 4 },
    { m: "-stat", from: "ギリシャ語 statos", mean: "一定に保つもの", ex: ["thermostat", "bacteriostatic", "electrostatics"], field: "物理英語", lv: 3 },
    { m: "-emia", from: "ギリシャ語 haima", mean: "血中の状態", ex: ["hyperglycemia", "anemia", "bacteremia"], field: "薬学英語", lv: 4 },
    { m: "-ic / -ous (酸)", from: "命名法の語尾", mean: "酸化数の高い / 低い", ex: ["sulfuric acid", "sulfurous acid", "ferric / ferrous"], field: "化学英語", lv: 4 },
    { m: "-ware", from: "hardware / software の対比から", mean: "〜として作られたもの(の総称)", ex: ["software", "firmware", "malware", "freeware"], field: "情報科学英語", lv: 2 },
    { m: "cyber-", from: "cybernetics(ギ: kybernētēs 舵取り)", mean: "計算機・ネットワークに関わる", ex: ["cyberspace", "cyborg", "cybersecurity"], field: "情報科学英語", lv: 3 },
    { m: "-el (要素)", from: "element の切り出し", mean: "画像・空間を構成する最小単位", ex: ["pixel", "voxel", "texel"], field: "情報科学英語", lv: 4 },
    { m: "meta-", from: "ギリシャ語 meta", mean: "〜についての〜(一段上の階層)", ex: ["metadata", "metaprogramming", "metalanguage"], field: "情報科学英語", lv: 3 },
    { m: "-oid / -bot", from: "-oeidēs(〜のような)/ robot の切り出し", mean: "〜に似たもの / 自動で動くもの", ex: ["humanoid", "chatbot", "botnet"], field: "情報科学英語", lv: 3 },
    { m: "en- / de- (符号化)", from: "encode / decode の対", mean: "符号化する / 復号する", ex: ["encode", "decode", "encrypt", "decrypt"], field: "情報科学英語", lv: 2 }
  ];

  /* ======================= 専門英語の語彙(t = 英語) ======================= */
  var TERMS = [
    /* --- 数学英語 --- */
    { t: "eigenvalue", en: "固有値", field: "数学英語", lv: 3, def: "線形変換が方向を変えずに引き伸ばす倍率" },
    { t: "manifold", en: "多様体", field: "数学英語", lv: 4, def: "局所的にはユークリッド空間と同じに見える空間" },
    { t: "convergence", en: "収束", field: "数学英語", lv: 2, def: "列や関数が限りなくある値に近づくこと" },
    { t: "conjecture", en: "予想", field: "数学英語", lv: 3, def: "正しいと思われるが証明されていない命題" },
    { t: "lemma", en: "補題", field: "数学英語", lv: 3, def: "定理を示すために用意される補助的な命題" },
    { t: "corollary", en: "系", field: "数学英語", lv: 3, def: "定理から直ちに導かれる命題" },
    { t: "sufficient condition", en: "十分条件", field: "数学英語", lv: 2, def: "それが成り立てば結論が成り立つ条件" },
    { t: "counterexample", en: "反例", field: "数学英語", lv: 2, def: "主張が偽であることを示す具体例" },
    { t: "smooth", en: "滑らかな", field: "数学英語", lv: 3, def: "何回でも微分できること(C^∞)" },
    { t: "vanish", en: "消える(ゼロになる)", field: "数学英語", lv: 3, def: "関数や項の値が 0 になること。英語では「消滅する」と表現する" },
    { t: "up to isomorphism", en: "同型を除いて", field: "数学英語", lv: 4, def: "同型なものを同じとみなせば、という限定" },

    /* --- 物理英語 --- */
    { t: "degeneracy", en: "縮退", field: "物理英語", lv: 4, def: "同じエネルギーをもつ量子状態が複数あること" },
    { t: "band gap", en: "バンドギャップ", field: "物理英語", lv: 3, def: "価電子帯と伝導帯の間の禁制エネルギー幅" },
    { t: "mean free path", en: "平均自由行程", field: "物理英語", lv: 4, def: "粒子が衝突するまでに進む平均距離" },
    { t: "steady state", en: "定常状態", field: "物理英語", lv: 3, def: "時間が経っても状態量が変化しない状態" },
    { t: "boundary condition", en: "境界条件", field: "物理英語", lv: 3, def: "境界での値や勾配を指定する条件" },
    { t: "order of magnitude", en: "桁", field: "物理英語", lv: 2, def: "10 の何乗か。概算の議論に使う" },
    { t: "quenching", en: "消光・急冷", field: "物理英語", lv: 4, def: "発光が抑えられること。材料では急冷処理も指す" },
    { t: "coherence", en: "コヒーレンス(可干渉性)", field: "物理英語", lv: 4, def: "位相の揃い具合。干渉が起こるかを決める" },

    /* --- 化学英語 --- */
    { t: "yield", en: "収率", field: "化学英語", lv: 2, def: "理論量に対して実際に得られた生成物の割合" },
    { t: "reflux", en: "還流", field: "化学英語", lv: 3, def: "蒸気を冷却して戻しながら加熱を続ける操作" },
    { t: "quench", en: "反応停止", field: "化学英語", lv: 3, def: "試薬を加えて反応を止めること" },
    { t: "aqueous layer", en: "水層", field: "化学英語", lv: 2, def: "抽出操作で分かれる水側の層" },
    { t: "stoichiometry", en: "化学量論", field: "化学英語", lv: 3, def: "反応する物質の量的な関係" },
    { t: "racemic mixture", en: "ラセミ体", field: "化学英語", lv: 4, def: "鏡像異性体が等量混ざったもの" },
    { t: "activation energy", en: "活性化エネルギー", field: "化学英語", lv: 3, def: "反応が進むために越えるべきエネルギー障壁" },
    { t: "solubility", en: "溶解度", field: "化学英語", lv: 2, def: "一定量の溶媒に溶けうる最大量" },

    /* --- 薬学英語 --- */
    { t: "bioavailability", en: "バイオアベイラビリティ", field: "薬学英語", lv: 3, def: "投与量のうち未変化体として全身循環に到達する割合" },
    { t: "half-life", en: "半減期", field: "薬学英語", lv: 2, def: "血中濃度が半分になるまでの時間" },
    { t: "clearance", en: "クリアランス", field: "薬学英語", lv: 3, def: "単位時間あたりに薬物が完全に除去される見かけの血漿体積" },
    { t: "first-pass effect", en: "初回通過効果", field: "薬学英語", lv: 3, def: "吸収後に肝臓で代謝され、全身に届く量が減る現象" },
    { t: "adverse event", en: "有害事象", field: "薬学英語", lv: 3, def: "薬との因果を問わず、投与中に起きた好ましくない出来事" },
    { t: "placebo", en: "プラセボ", field: "薬学英語", lv: 2, def: "薬効成分を含まない対照。ラテン語「私は喜ばせる」に由来" },
    { t: "double-blind", en: "二重盲検", field: "薬学英語", lv: 3, def: "被験者も評価者もどちらの群かを知らされない設計" },
    { t: "compliance / adherence", en: "服薬遵守", field: "薬学英語", lv: 3, def: "指示どおりに服薬すること。近年は患者主体の adherence が好まれる" },
    { t: "sustained release", en: "徐放性", field: "薬学英語", lv: 3, def: "有効成分がゆっくり放出される製剤設計" },
    { t: "therapeutic window", en: "治療域", field: "薬学英語", lv: 4, def: "有効かつ安全な血中濃度の範囲" },

    /* --- 経済英語 --- */
    { t: "opportunity cost", en: "機会費用", field: "経済英語", lv: 2, def: "その選択のために諦めた次善の選択肢の価値" },
    { t: "diminishing returns", en: "収穫逓減", field: "経済英語", lv: 2, def: "投入を増やすほど追加の産出が小さくなること" },
    { t: "elasticity", en: "弾力性", field: "経済英語", lv: 2, def: "ある変数の変化率に対する別の変数の変化率" },
    { t: "moral hazard", en: "モラルハザード", field: "経済英語", lv: 4, def: "契約後に行動が観察されないことで注意が緩む現象" },
    { t: "adverse selection", en: "逆選択", field: "経済英語", lv: 4, def: "契約前の情報格差により、悪い相手ばかりが集まる現象" },
    { t: "deadweight loss", en: "死荷重", field: "経済英語", lv: 3, def: "取引が減ることで誰の手にも渡らずに失われる余剰" },
    { t: "crowding out", en: "クラウディング・アウト", field: "経済英語", lv: 4, def: "政府支出の拡大が金利を上げ、民間投資を押しのけること" },
    { t: "sunk cost", en: "埋没費用", field: "経済英語", lv: 2, def: "すでに支出して回収できない費用。意思決定では無視すべきもの" },
    { t: "arbitrage", en: "裁定取引", field: "経済英語", lv: 4, def: "同じ価値のものの価格差からリスクなしに利益を得る取引" },
    { t: "identification", en: "識別", field: "経済英語", lv: 5, def: "データから因果パラメータを一意に取り出せること" },

    /* --- 学術英語共通(論文の言い回し) --- */
    { t: "novel", en: "新規の", field: "学術英語共通", lv: 2, def: "「小説」ではなく「これまでにない」の意。論文の主張でよく使う" },
    { t: "robust", en: "頑健な", field: "学術英語共通", lv: 3, def: "仮定や条件が多少変わっても結論が変わらないこと" },
    { t: "significant", en: "有意な", field: "学術英語共通", lv: 3, def: "統計的に偶然とは考えにくいこと。「重要」とは別" },
    { t: "trade-off", en: "二律背反", field: "学術英語共通", lv: 2, def: "一方を良くすると他方が悪くなる関係" },
    { t: "state of the art", en: "最先端", field: "学術英語共通", lv: 3, def: "現時点で到達している最高の水準" },
    { t: "ad hoc", en: "その場限りの", field: "学術英語共通", lv: 4, def: "一般原理ではなく、その場合のために設けた説明や仮定" },
    { t: "a priori / a posteriori", en: "先験的 / 事後的", field: "学術英語共通", lv: 5, def: "経験に先立つ / 経験のあとに得られる" },
    { t: "mutatis mutandis", en: "必要な変更を加えて", field: "学術英語共通", lv: 5, def: "同じ議論が細部を変えればそのまま通用する、という断り" },
    { t: "a fortiori", en: "なおさら", field: "学術英語共通", lv: 5, def: "より強い理由で成り立つ、という論法" },
    { t: "seminal", en: "先駆的な", field: "学術英語共通", lv: 4, def: "後続の研究の出発点になった、という評価" },
    { t: "caveat", en: "留保・注意点", field: "学術英語共通", lv: 4, def: "主張に付ける限定条件" },
    { t: "reproducibility", en: "再現性", field: "学術英語共通", lv: 3, def: "同じ手順で同じ結果が得られること" },

    /* --- 情報科学英語 --- */
    { t: "time complexity", en: "時間計算量", field: "情報科学英語", lv: 2, def: "入力サイズに対して手数がどう増えるか" },
    { t: "overhead", en: "オーバーヘッド", field: "情報科学英語", lv: 2, def: "本来の処理以外に余分にかかる時間・容量" },
    { t: "throughput", en: "スループット", field: "情報科学英語", lv: 2, def: "単位時間あたりに処理できる量" },
    { t: "latency", en: "レイテンシ(遅延)", field: "情報科学英語", lv: 2, def: "要求してから応答が返るまでの時間。throughput とは別物" },
    { t: "bottleneck", en: "ボトルネック", field: "情報科学英語", lv: 2, def: "全体の速度を決めてしまう最も遅い箇所" },
    { t: "deadlock", en: "デッドロック", field: "情報科学英語", lv: 3, def: "互いに相手の資源を待って進まなくなる状態" },
    { t: "race condition", en: "競合状態", field: "情報科学英語", lv: 3, def: "実行順序によって結果が変わる不具合" },
    { t: "idempotent", en: "冪等な", field: "情報科学英語", lv: 4, def: "何度実行しても結果が同じであること" },
    { t: "graceful degradation", en: "緩やかな劣化", field: "情報科学英語", lv: 4, def: "一部が壊れても全体が止まらず、機能を落として動き続けること" },
    { t: "backward compatible", en: "後方互換の", field: "情報科学英語", lv: 3, def: "新しい版が古い入力・利用者を壊さないこと" },
    { t: "garbage collection", en: "ごみ集め", field: "情報科学英語", lv: 3, def: "到達不能になった記憶領域を自動的に回収すること" },
    { t: "sandbox", en: "サンドボックス", field: "情報科学英語", lv: 3, def: "外に影響を出さない隔離された実行環境" },
    { t: "boilerplate", en: "定型コード", field: "情報科学英語", lv: 3, def: "毎回ほぼ同じ形で書かざるを得ない部分" },
    { t: "regression", en: "デグレ(退行)", field: "情報科学英語", lv: 3, def: "以前は動いていた機能が変更で壊れること。統計の回帰とは別語義" },
    { t: "fault tolerance", en: "耐障害性", field: "情報科学英語", lv: 4, def: "部品が壊れても系全体としては動き続ける性質" },
    { t: "state of the art (SOTA)", en: "最高性能", field: "情報科学英語", lv: 3, def: "その時点で最も良いとされる結果" }
  ];

  /* ============ 日常語 → 専門英語 の連想 ============ */
  var ASSOC = [
    { simple: "「新しい」と言いたいとき", simpleMean: "これまでに無かった、という主張",
      adv: "novel", advName: "新規の", field: "学術英語共通", lv: 2,
      why: "論文の novel は「小説」ではなく「新規の」。new より強く、先行研究に無いことを主張する語。",
      wrong: ["robust", "seminal", "ad hoc"] },
    { simple: "「差が偶然とは思えない」と言いたいとき", simpleMean: "たまたまではなさそうだ",
      adv: "statistically significant", advName: "統計的に有意", field: "学術英語共通", lv: 3,
      why: "significant は日常語の「重要」ではなく、統計的な判断を指す。効果の大きさ(effect size)とは別の話。",
      wrong: ["substantial", "robust", "salient"] },
    { simple: "「多少条件が変わっても大丈夫」と言いたいとき", simpleMean: "前提が揺れても結論は変わらない",
      adv: "robust", advName: "頑健な", field: "学術英語共通", lv: 3,
      why: "robustness check(頑健性の確認)は、仮定を変えても結論が保たれるかを示す標準的な手続き。",
      wrong: ["novel", "rigorous", "consistent"] },
    { simple: "「手が左右で重ならない」性質", simpleMean: "鏡に映すと別物になる",
      adv: "chirality", advName: "キラリティー(掌性)", field: "化学英語", lv: 4,
      why: "語源はギリシャ語 cheir(手)。医薬品では一方の鏡像体だけが有効なことが多く、光学分割が必要になる。",
      wrong: ["isotope", "polymer", "catalysis"] },
    { simple: "「音を粒として数える」考え方", simpleMean: "振動をひとつ、ふたつと数える",
      adv: "phonon", advName: "フォノン(音子)", field: "物理英語", lv: 4,
      why: "photon(光子)の型をそのまま音に当てはめた語。-on を付けると素励起を粒子として扱う、という命名の作法。",
      wrong: ["exciton", "positron", "soliton"] },
    { simple: "「同じ場所に入る仲間」", simpleMean: "周期表で同じ位置に来る",
      adv: "isotope", advName: "同位体", field: "化学英語", lv: 3,
      why: "isos(等しい)+ topos(場所)。陽子数が同じで中性子数が違うため、化学的性質はほぼ同じで質量だけが違う。",
      wrong: ["isomer", "polymer", "monomer"] },
    { simple: "「効き目のわりに危ない量が近い薬」", simpleMean: "少し多いと危険になる",
      adv: "therapeutic window", advName: "治療域", field: "薬学英語", lv: 4,
      why: "有効濃度と中毒濃度の間の幅。狭い薬は TDM(血中濃度モニタリング)の対象になる。",
      wrong: ["bioavailability", "first-pass effect", "sustained release"] },
    { simple: "「薬だと思って飲むと少し効く」", simpleMean: "成分がなくても効果が出る",
      adv: "placebo", advName: "プラセボ", field: "薬学英語", lv: 2,
      why: "ラテン語「私は喜ばせるだろう」。この効果を差し引くために二重盲検(double-blind)が必要になる。",
      wrong: ["adverse event", "half-life", "clearance"] },
    { simple: "「不景気なのに物価が上がる」", simpleMean: "景気が悪いのに値段は上がる",
      adv: "stagflation", advName: "スタグフレーション", field: "経済英語", lv: 3,
      why: "stagnation + inflation の混成語。失業とインフレが交換関係にあるという当時の常識が崩れたときに必要になった語。",
      wrong: ["deflation", "disinflation", "crowding out"] },
    { simple: "「もう払ったお金は取り返せない」", simpleMean: "使ってしまった分は戻らない",
      adv: "sunk cost", advName: "埋没費用", field: "経済英語", lv: 2,
      why: "回収不能な費用は、これからの意思決定では無視するのが合理的。無視できないのが sunk cost fallacy。",
      wrong: ["opportunity cost", "marginal cost", "deadweight loss"] },
    { simple: "「同じ形とみなしてよい」", simpleMean: "伸ばしたり曲げたりして重なる",
      adv: "homeomorphism", advName: "同相写像", field: "数学英語", lv: 4,
      why: "homoios(同じような)+ morphē(形)。連続変形で移り合うものを同一視するのが位相幾何の立場。",
      wrong: ["isomorphism", "diffeomorphism", "automorphism"] },
    { simple: "「掛け算を足し算に変えたい」", simpleMean: "計算を楽にしたい",
      adv: "logarithm", advName: "対数", field: "数学英語", lv: 3,
      why: "logos(比)+ arithmos(数)。Napier は天文計算の労力を減らすために作った。指数関数の逆として整理されたのは後の話。",
      wrong: ["algorithm", "algebra", "arithmetic"] },
    { simple: "「計算機の中だけで実験する」", simpleMean: "実際の試料を使わない",
      adv: "in silico", advName: "イン・シリコ", field: "薬学英語", lv: 4,
      why: "in vitro(ガラスの中で)/ in vivo(生体内で)というラテン語の型に silicon を差し込んだ造語。",
      wrong: ["in situ", "ab initio", "ex vivo"] },
    { simple: "「2 進の桁」を 1 語で言うと", simpleMean: "0 か 1 かの最小単位",
      adv: "bit", advName: "ビット", field: "情報科学英語", lv: 2,
      why: "binary + digit の混成語。qubit(quantum + bit)はこの語の上に建てられた造語。",
      wrong: ["byte", "pixel", "codec"] },
    { simple: "「画像を作る最小の点」", simpleMean: "拡大すると見える四角い粒",
      adv: "pixel", advName: "画素", field: "情報科学英語", lv: 2,
      why: "picture + element。立体版は voxel(volume + element)、模様は texel(texture + element)。",
      wrong: ["bit", "byte", "codec"] },
    { simple: "「舵を取る」から生まれた学問の名", simpleMean: "制御と通信を一緒に扱う",
      adv: "cybernetics", advName: "サイバネティクス", field: "情報科学英語", lv: 4,
      why: "ギリシャ語 kybernētēs(舵取り)から Wiener が命名。cyberspace・cyborg の cyber- はここから。",
      wrong: ["informatics", "automata", "robotics"] },
    { simple: "「悪さをするソフト」の総称", simpleMean: "害を与える目的のプログラム",
      adv: "malware", advName: "マルウェア", field: "情報科学英語", lv: 3,
      why: "malicious + software。software 自体が hardware をもじった造語で、-ware が総称の接尾辞になった。",
      wrong: ["firmware", "freeware", "spyware"] },
    { simple: "「0 と 1 を同時に持てる情報の単位」", simpleMean: "どちらとも決まっていない状態",
      adv: "qubit", advName: "量子ビット", field: "物理英語", lv: 4,
      why: "quantum + bit の混成語。bit 自体も binary + digit の混成語で、造語の上に造語が重なっている。",
      wrong: ["byte", "photon", "spintronics"] }
  ];

  /* ============================== 適性設問 ============================== */
  var APTITUDE = [
    { q: "知らない専門用語に出会ったとき、まず何をしますか。", opts: [
      { t: "語を分解して、語根から意味を推測する", w: { "学術英語共通": 2, "化学英語": 1.5 } },
      { t: "その分野での定義を厳密に確認する", w: { "数学英語": 3 } },
      { t: "実験や測定でどう使われるかを見る", w: { "物理英語": 2.5, "化学英語": 1 } },
      { t: "実務や臨床でどう扱われているかを調べる", w: { "薬学英語": 2.5, "経済英語": 1 } }
    ]},
    { q: "英語論文を読むとき、いちばん気になるのは？", opts: [
      { t: "定義と仮定が明示されているか", w: { "数学英語": 3 } },
      { t: "測定条件と誤差の書き方", w: { "物理英語": 3 } },
      { t: "合成手順と収率が再現できるか", w: { "化学英語": 3 } },
      { t: "試験デザインと統計処理が妥当か", w: { "薬学英語": 2, "経済英語": 2 } }
    ]},
    { q: "同じ単語が分野で意味を変えることについて、どう感じますか。", opts: [
      { t: "面白い。語がどう転用されたのかを知りたい", w: { "学術英語共通": 3 } },
      { t: "危険だ。定義を毎回確認したい", w: { "数学英語": 2.5 } },
      { t: "自然だ。文脈で決まるものだと思う", w: { "経済英語": 2, "薬学英語": 1 } },
      { t: "現場では慣用で通じるので気にならない", w: { "化学英語": 2, "物理英語": 1 } }
    ]},
    { q: "新しい概念に名前を付けるとしたら？", opts: [
      { t: "ギリシャ語・ラテン語の語根で組み立てる", w: { "化学英語": 2, "物理英語": 1.5 } },
      { t: "既存の語をつなげた分かりやすい混成語にする", w: { "経済英語": 2.5 } },
      { t: "頭字語にして短く言えるようにする", w: { "薬学英語": 2.5 } },
      { t: "既存の語の型に当てはめて体系に組み込む", w: { "数学英語": 2.5 } }
    ]},
    { q: "「-on」で終わる語(photon, phonon, exciton)を見て思うのは？", opts: [
      { t: "同じ作りの語がまだあるはずだと探したくなる", w: { "物理英語": 3 } },
      { t: "接尾辞の由来(ion)を確認したくなる", w: { "学術英語共通": 2.5 } },
      { t: "それぞれの物理的実体の違いが気になる", w: { "物理英語": 2, "化学英語": 1.5 } },
      { t: "命名の体系が整理されていて心地よい", w: { "数学英語": 2 } }
    ]},
    { q: "略語(RCT, ITT, NNT)が並ぶ文章はどうですか。", opts: [
      { t: "慣れれば読みやすい。定義さえ押さえればよい", w: { "薬学英語": 3 } },
      { t: "初出で展開してほしい", w: { "学術英語共通": 2.5 } },
      { t: "数式に置き換えて理解したい", w: { "数学英語": 2, "経済英語": 1 } },
      { t: "実際のデータを見ないと意味が入ってこない", w: { "経済英語": 2.5 } }
    ]},
    { q: "ラテン語由来の表現(ceteris paribus, in vitro, a fortiori)は？", opts: [
      { t: "議論の型を短く示せて便利だ", w: { "学術英語共通": 3 } },
      { t: "経済の議論では前提の宣言として不可欠", w: { "経済英語": 3 } },
      { t: "実験系の条件表示として自然に使う", w: { "薬学英語": 2, "化学英語": 1.5 } },
      { t: "日本語に直したほうが誤解が少ない", w: { "数学英語": 1.5, "物理英語": 1 } }
    ]},
    { q: "専門用語を人に説明するとき、どうしますか。", opts: [
      { t: "語源から入って、意味の成り立ちを見せる", w: { "学術英語共通": 3 } },
      { t: "厳密な定義を先に置く", w: { "数学英語": 3 } },
      { t: "身近な例に置き換える", w: { "経済英語": 2.5 } },
      { t: "実物や測定結果を見せる", w: { "物理英語": 2, "化学英語": 2 } }
    ]},
    { q: "訳語が定まっていない新語に出会ったら？", opts: [
      { t: "原語のままカタカナで使う", w: { "薬学英語": 2, "経済英語": 2 } },
      { t: "語根から訳語を作ってみる", w: { "化学英語": 2.5 } },
      { t: "定義を書き下してから短い呼び名を決める", w: { "数学英語": 2.5 } },
      { t: "分野の慣例に従うのを待つ", w: { "学術英語共通": 2 } }
    ]},
    { q: "術語が略号だらけの文書(API, RFC, POSIX)はどうですか。", opts: [
      { t: "定義さえ押さえれば読みやすい", w: { "情報科学英語": 3 } },
      { t: "初出で展開してほしい", w: { "学術英語共通": 2.5 } },
      { t: "仕様の原文に当たりたくなる", w: { "情報科学英語": 2, "学術英語共通": 1 } },
      { t: "実際に動かして確かめたい", w: { "情報科学英語": 2, "物理英語": 1 } }
    ]},
    { q: "日常語が術語に転用された例(bug, thread, kernel, daemon)を見て思うのは？", opts: [
      { t: "比喩の元をたどりたくなる", w: { "情報科学英語": 2.5, "学術英語共通": 1 } },
      { t: "分野ごとの意味を区別して覚えたい", w: { "数学英語": 2 } },
      { t: "実務では文脈で決まるので気にしない", w: { "情報科学英語": 2 } },
      { t: "誤解を招くので別語にすべきだと思う", w: { "薬学英語": 2 } }
    ]},
    { q: "語彙を増やすとき、効くと感じるのは？", opts: [
      { t: "語根・接辞の体系を覚えること", w: { "化学英語": 2, "学術英語共通": 2 } },
      { t: "論文をたくさん読んで文脈ごと覚えること", w: { "物理英語": 2, "薬学英語": 1.5 } },
      { t: "定義を自分の言葉で書き直すこと", w: { "数学英語": 3 } },
      { t: "実データや実務で使ってみること", w: { "経済英語": 3 } }
    ]}
  ];

  /* ============================== 分野プロファイル ============================== */
  var FIELD_PROFILE = {
    "数学英語": {
      tag: "定義と論証の言い回しを扱う分野",
      think: "語より先に定義があり、語はその定義への短い参照として使われる。",
      eqs: "iff · w.l.o.g. · up to isomorphism · Q.E.D.",
      syms: "iff s.t. w.l.o.g. w.r.t. a.e. a.s. LHS/RHS",
      near: ["学術英語共通", "物理英語"],
      next: "証明の定型表現 → 論文の構成語彙 → 分野固有の慣用(圏論・解析)"
    },
    "物理英語": {
      tag: "測定と現象の記述に使う語彙を扱う分野",
      think: "量・単位・精度をセットで述べ、桁と誤差で議論する。",
      eqs: "order of magnitude · in situ · ab initio · FWHM",
      syms: "SI RMS FWHM DOS S/N",
      near: ["化学英語", "数学英語"],
      next: "単位と次元解析 → 測定の記述 → 素励起の命名法(-on)"
    },
    "化学英語": {
      tag: "物質と操作を記述する語彙を扱う分野",
      think: "手順・条件・収率を再現可能な形で書き、命名法で構造を伝える。",
      eqs: "aq. · reflux · quench · ee · stoichiometry",
      syms: "aq. conc./dil. m.p./b.p. r.t. NMR ee TLC",
      near: ["薬学英語", "物理英語"],
      next: "実験項の書き方 → IUPAC 命名法 → 接尾辞の体系(-ase/-ose/-ene)"
    },
    "薬学英語": {
      tag: "臨床と試験デザインの語彙を扱う分野",
      think: "有効性と安全性を、集団に対する統計として述べる。",
      eqs: "RCT · ITT · PP · in vitro / in vivo / in silico",
      syms: "RCT ITT PP AE/SAE NSAID",
      near: ["化学英語", "経済英語"],
      next: "試験デザインの用語 → 添付文書の英語 → 規制文書(ICH)の語彙"
    },
    "経済英語": {
      tag: "前提と因果の主張を組み立てる語彙を扱う分野",
      think: "何を一定と置いたかを明示し、相関と因果を書き分ける。",
      eqs: "ceteris paribus · YoY · CAGR · identification",
      syms: "YoY QoQ CAGR s.a. FY ppt bps",
      near: ["学術英語共通", "薬学英語"],
      next: "指標の読み方 → 因果推論の語彙 → 政策文書の言い回し"
    },
    "情報科学英語": {
      tag: "仕様と実装を過不足なく述べる語彙を扱う分野",
      think: "曖昧さを残さず、性能と失敗の仕方まで含めて書く。日常語の転用と略号が多い。",
      eqs: "time complexity · idempotent · graceful degradation · backward compatible",
      syms: "API RFC POSIX REPL ASCII UTF-8 CI/CD SLA FLOPS w.h.p.",
      near: ["数学英語", "学術英語共通"],
      next: "略号と仕様書の語彙 → 日常語の転用(bug/thread/kernel) → 造語の型(-ware, cyber-)"
    },
    "学術英語共通": {
      tag: "分野を問わず論文で共有される語彙と型",
      think: "主張の強さ・留保・先行研究との関係を、決まった語で示す。",
      eqs: "novel · robust · trade-off · mutatis mutandis · a fortiori",
      syms: "et al. i.e. e.g. cf. ibid. N.B. ca. sic",
      near: ["数学英語", "経済英語"],
      next: "引用と参照の表記 → 主張の強度を表す語 → ラテン語由来の定型句"
    }
  };

  var API = { FIELDS: FIELDS, SYMBOLS: SYMBOLS, CTX: CTX, EQUATIONS: EQUATIONS,
              ASSOC: ASSOC, TERMS: TERMS, APTITUDE: APTITUDE, FIELD_PROFILE: FIELD_PROFILE,
              COIN: COIN, MORPH: MORPH, SUBJECT_OF: SUBJECT_OF,
              /* 設問文の言い回しを「記号 → 表記」「方程式 → 造語」に差し替える */
              LABELS: {
                p1: "第一次検査 — 専門英語の表記",
                p2: "第二次検査 — 造語の成り立ち",
                symMean: "この学術英語の表記・略号は何を意味しますか。",
                symField: "この表記(%ja%)が最も特徴的に使われるのはどの分野の英語ですか。",
                ctx: "<b>%field%</b> の論文でこの語が現れたとき、最も自然な読み方はどれですか。",
                eqMean: "この造語は何を意味しますか。",
                eqName: "この造語の日本語名はどれですか。",
                assoc: "この言い方に対応する専門英語はどれですか。",
                assocRev: "この専門英語のもとになった、日常的な言い方はどれですか。",
                flashSym: "いま一瞬だけ表示された学術英語の表記は、次のどれですか。",
                flashTerm: "いま一瞬だけ表示された専門英語は、次のどれですか。",
                flashTermMean: "いま表示された専門英語のうち 1 つの意味が下にあります。正しい説明はどれですか。",
                flashEq: "いま散らばって提示された語基を組み立てると、どの造語になりますか。",
                kindSym: "表記の意味", kindSymField: "表記の分野", kindCtx: "文脈依存の多義語",
                kindEqMean: "造語の意味", kindEqName: "造語の同定",
                kindAssoc: "連想(日常→専門英語)", kindAssocRev: "連想(専門英語→日常)",
                kindFlashSym: "瞬読(学術表記)", kindFlashEq: "瞬読(造語バラバラ)"
              } };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.LexBank = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
