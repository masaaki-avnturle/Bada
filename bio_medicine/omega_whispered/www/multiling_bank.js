/*
 * multiling_bank.js — ロシア語・フランス語の専門用語のウィスパード問題銀行
 * Ω-Whispered — Masaaki Yamaguchi / Bada (bio_medicine/omega_whispered)
 *
 * 数学・物理学・化学・薬学・経済学の論文で使われる
 *   (1) ロシア語・フランス語の専門用語 (TERMS: t = 原語, en = 日本語)
 *   (2) 論文中の略号・定型表記 (SYMBOLS)
 *   (3) 言語をまたぐと意味がずれる語・空似言葉 (CTX)
 *   (4) 定型表現の対訳 (EQUATIONS)
 * を収録する。TERMS の t に原語を置いてあるので、瞬読ではキリル文字・
 * フランス語がそのまま提示される。
 *
 * 読みはカタカナで def に併記する。依存ゼロ。Node からも require できる。
 */
(function (root) {
  "use strict";

  var FIELDS = ["ロシア語・数学", "ロシア語・物理学", "ロシア語・化学", "ロシア語・薬学", "ロシア語・経済学", "ロシア語・情報科学",
                "フランス語・数学", "フランス語・物理学", "フランス語・化学", "フランス語・薬学", "フランス語・経済学", "フランス語・情報科学",
                "ドイツ語・数学", "ドイツ語・物理学", "ドイツ語・化学", "ドイツ語・薬学", "ドイツ語・経済学", "ドイツ語・情報科学",
                "中国語・数学", "中国語・物理学", "中国語・化学", "中国語・薬学", "中国語・経済学", "中国語・情報科学"];

  /* 系統(math / chem / pharma / econ)との対応。他系統へ配るときに使う */
  var SUBJECT_OF = {
    "ロシア語・数学": "math", "フランス語・数学": "math",
    "ロシア語・物理学": "chem", "フランス語・物理学": "chem",
    "ロシア語・化学": "chem", "フランス語・化学": "chem",
    "ロシア語・薬学": "pharma", "フランス語・薬学": "pharma",
    "ロシア語・経済学": "econ", "フランス語・経済学": "econ",
    "ロシア語・情報科学": "cs", "フランス語・情報科学": "cs",
    "ドイツ語・数学": "math", "中国語・数学": "math",
    "ドイツ語・物理学": "chem", "中国語・物理学": "chem",
    "ドイツ語・化学": "chem", "中国語・化学": "chem",
    "ドイツ語・薬学": "pharma", "中国語・薬学": "pharma",
    "ドイツ語・経済学": "econ", "中国語・経済学": "econ",
    "ドイツ語・情報科学": "cs", "中国語・情報科学": "cs"
  };

  /* 分野名は「言語・分野」の形。前半が言語名になる */
  var LANG_OF = function (f) { return String(f).split("・")[0]; };
  var LANGS = ["ロシア語", "フランス語", "ドイツ語", "中国語"];

  /* ======================= 論文中の略号・定型表記 ======================= */
  var SYMBOLS = [
    /* --- ロシア語 --- */
    { ch: "ч.т.д.", ja: "証明終わり", mean: "что и требовалось доказать(チトトレボヴァロシ ドカザーチ)= Q.E.D.", field: "ロシア語・数学", lv: 3 },
    { ch: "и т.д.", ja: "など", mean: "и так далее(イ タク ダーレエ)= etc.", field: "ロシア語・数学", lv: 1 },
    { ch: "т.е.", ja: "すなわち", mean: "то есть(ト イェスチ)= i.e.", field: "ロシア語・数学", lv: 2 },
    { ch: "т.к.", ja: "なぜなら", mean: "так как(タク カク)= since / because", field: "ロシア語・数学", lv: 2 },
    { ch: "см.", ja: "参照せよ", mean: "смотри(スモトリー)= see / cf.", field: "ロシア語・数学", lv: 2 },
    { ch: "рис.", ja: "図", mean: "рисунок(リスーノク)= figure", field: "ロシア語・物理学", lv: 1 },
    { ch: "табл.", ja: "表", mean: "таблица(タブリーツァ)= table", field: "ロシア語・物理学", lv: 1 },
    { ch: "ур-ние", ja: "方程式", mean: "уравнение(ウラヴネーニエ)の略記 = equation", field: "ロシア語・数学", lv: 3 },
    { ch: "ф-ла", ja: "式", mean: "формула(フォールムラ)の略記 = formula", field: "ロシア語・数学", lv: 3 },
    { ch: "н.у.", ja: "標準状態", mean: "нормальные условия(ノルマーリヌィエ ウスローヴィヤ)= 標準状態(0 °C, 1 atm)", field: "ロシア語・化学", lv: 3 },
    { ch: "р-р", ja: "溶液", mean: "раствор(ラストヴォール)の略記 = solution", field: "ロシア語・化学", lv: 3 },
    { ch: "в-во", ja: "物質", mean: "вещество(ヴェシチェストヴォー)の略記 = substance", field: "ロシア語・化学", lv: 4 },
    { ch: "т. пл.", ja: "融点", mean: "температура плавления(テンペラトゥーラ プラヴレーニヤ)= melting point", field: "ロシア語・化学", lv: 4 },
    { ch: "ЛС", ja: "医薬品", mean: "лекарственное средство(レカールストヴェンノエ スレードストヴォ)= drug product", field: "ロシア語・薬学", lv: 4 },
    { ch: "ЖНВЛП", ja: "必須医薬品リスト", mean: "生命に必要不可欠な医薬品の公定リスト(価格規制の対象)", field: "ロシア語・薬学", lv: 5 },
    { ch: "ВВП", ja: "国内総生産", mean: "валовой внутренний продукт(ヴァロヴォーイ ヴヌートレンニー プロドゥークト)= GDP", field: "ロシア語・経済学", lv: 2 },
    { ch: "ЦБ РФ", ja: "ロシア中央銀行", mean: "Центральный банк(ツェントラーリヌィ バンク)。金融政策を担う", field: "ロシア語・経済学", lv: 3 },
    { ch: "МРОТ", ja: "最低賃金", mean: "минимальный размер оплаты труда(最低労働報酬額)", field: "ロシア語・経済学", lv: 4 },
    { ch: "ЭВМ", ja: "電子計算機", mean: "электронная вычислительная машина(エレクトロンナヤ ヴィチスリーチェリナヤ マシーナ)= computer", field: "ロシア語・情報科学", lv: 3 },
    { ch: "ОС", ja: "オペレーティングシステム", mean: "операционная система(オペラツィオーンナヤ システェーマ)= OS", field: "ロシア語・情報科学", lv: 2 },
    { ch: "БД", ja: "データベース", mean: "база данных(バーザ ダーンヌィフ)= database", field: "ロシア語・情報科学", lv: 3 },
    { ch: "ПО", ja: "ソフトウェア", mean: "программное обеспечение(プログラームノエ オベスペチェーニエ)= software", field: "ロシア語・情報科学", lv: 3 },
    { ch: "ИИ", ja: "人工知能", mean: "искусственный интеллект(イスクーストヴェンヌィ インテレークト)= AI", field: "ロシア語・情報科学", lv: 2 },
    { ch: "СУБД", ja: "データベース管理システム", mean: "система управления базами данных = DBMS", field: "ロシア語・情報科学", lv: 4 },

    /* --- フランス語 --- */
    { ch: "C.Q.F.D.", ja: "証明終わり", mean: "ce qu'il fallait démontrer(ス キル ファレ デモントレ)= Q.E.D.", field: "フランス語・数学", lv: 3 },
    { ch: "ssi", ja: "必要十分条件", mean: "si et seulement si(シ エ スルマン シ)= if and only if", field: "フランス語・数学", lv: 3 },
    { ch: "c.-à-d.", ja: "すなわち", mean: "c'est-à-dire(セタディール)= i.e.", field: "フランス語・数学", lv: 2 },
    { ch: "p. ex.", ja: "たとえば", mean: "par exemple(パー エグザンプル)= e.g.", field: "フランス語・数学", lv: 1 },
    { ch: "d'où", ja: "ゆえに", mean: "ドゥ。「そこから」= hence / therefore。導出の接続に使う", field: "フランス語・数学", lv: 2 },
    { ch: "env.", ja: "およそ", mean: "environ(アンヴィロン)= approximately。数値の概数に添える", field: "フランス語・数学", lv: 2 },
    { ch: "fig.", ja: "図", mean: "figure(フィギュール)", field: "フランス語・物理学", lv: 1 },
    { ch: "tab.", ja: "表", mean: "tableau(タブロー)", field: "フランス語・物理学", lv: 1 },
    { ch: "S.I.", ja: "国際単位系", mean: "Système International d'unités。フランス語が原語の単位系", field: "フランス語・物理学", lv: 2 },
    { ch: "T.P.", ja: "実習", mean: "travaux pratiques(トラヴォー プラティック)= 実験実習", field: "フランス語・化学", lv: 3 },
    { ch: "C.N.T.P.", ja: "標準温度圧力", mean: "conditions normales de température et de pression = 標準状態", field: "フランス語・化学", lv: 4 },
    { ch: "p.f.", ja: "融点", mean: "point de fusion(ポワン ド フュジオン)= melting point", field: "フランス語・化学", lv: 3 },
    { ch: "AMM", ja: "製造販売承認", mean: "autorisation de mise sur le marché = marketing authorisation", field: "フランス語・薬学", lv: 4 },
    { ch: "DCI", ja: "国際一般名", mean: "dénomination commune internationale = INN(一般名)", field: "フランス語・薬学", lv: 4 },
    { ch: "PIB", ja: "国内総生産", mean: "produit intérieur brut(プロデュイ アンテリユール ブリュ)= GDP", field: "フランス語・経済学", lv: 2 },
    { ch: "SMIC", ja: "最低賃金", mean: "salaire minimum interprofessionnel de croissance", field: "フランス語・経済学", lv: 4 },
    { ch: "INSEE", ja: "国立統計経済研究所", mean: "統計を作成する機関。経済指標の一次資料になる", field: "フランス語・経済学", lv: 4 },
    { ch: "TVA", ja: "付加価値税", mean: "taxe sur la valeur ajoutée。付加価値税(VAT)はフランス発祥", field: "フランス語・経済学", lv: 3 },
    { ch: "TIC", ja: "情報通信技術", mean: "technologies de l'information et de la communication = ICT", field: "フランス語・情報科学", lv: 3 },
    { ch: "SGBD", ja: "データベース管理システム", mean: "système de gestion de base de données = DBMS", field: "フランス語・情報科学", lv: 4 },
    { ch: "IA", ja: "人工知能", mean: "intelligence artificielle(アンテリジャンス アルティフィシエル)= AI", field: "フランス語・情報科学", lv: 2 },
    { ch: "RGPD", ja: "一般データ保護規則", mean: "règlement général sur la protection des données = GDPR", field: "フランス語・情報科学", lv: 4 },
    { ch: "Ko / Mo / Go", ja: "キロ/メガ/ギガオクテット", mean: "kilo-octet などの略。英語の KB/MB/GB にあたる", field: "フランス語・情報科学", lv: 3 },
    { ch: "MAJ", ja: "更新", mean: "mise à jour(ミザジュール)= update", field: "フランス語・情報科学", lv: 3 },

    /* --- ドイツ語 --- */
    { ch: "q.e.d. / w.z.b.w.", ja: "証明終わり", mean: "was zu beweisen war(ヴァス ツー ベヴァイゼン ヴァー)= 示すべきであったこと", field: "ドイツ語・数学", lv: 3 },
    { ch: "o.B.d.A.", ja: "一般性を失わずに", mean: "ohne Beschränkung der Allgemeinheit = without loss of generality", field: "ドイツ語・数学", lv: 5 },
    { ch: "d.h.", ja: "すなわち", mean: "das heißt(ダス ハイスト)= i.e.", field: "ドイツ語・数学", lv: 1 },
    { ch: "z.B.", ja: "たとえば", mean: "zum Beispiel(ツム バイシュピール)= e.g.", field: "ドイツ語・数学", lv: 1 },
    { ch: "vgl.", ja: "参照せよ", mean: "vergleiche(フェアグライヒェ)= cf.", field: "ドイツ語・数学", lv: 2 },
    { ch: "bzw.", ja: "あるいは / それぞれ", mean: "beziehungsweise(ベツィーウングスヴァイゼ)= respectively / or rather", field: "ドイツ語・数学", lv: 3 },
    { ch: "Abb.", ja: "図", mean: "Abbildung(アップビルドゥング)= figure。数学では「写像」の意味にもなる", field: "ドイツ語・物理学", lv: 2 },
    { ch: "Tab.", ja: "表", mean: "Tabelle(タベレ)= table", field: "ドイツ語・物理学", lv: 1 },
    { ch: "Vgl. Bd.", ja: "巻を参照", mean: "Band(バント)= 巻。文献参照の表記", field: "ドイツ語・物理学", lv: 4 },
    { ch: "Smp.", ja: "融点", mean: "Schmelzpunkt(シュメルツプンクト)= melting point。Sdp. は沸点", field: "ドイツ語・化学", lv: 3 },
    { ch: "Lsg.", ja: "溶液", mean: "Lösung(レーズング)の略。「解」の意味も持つ", field: "ドイツ語・化学", lv: 3 },
    { ch: "AM", ja: "医薬品", mean: "Arzneimittel(アルツナイミッテル)= drug product", field: "ドイツ語・薬学", lv: 3 },
    { ch: "NW", ja: "副作用", mean: "Nebenwirkung(ネーベンヴィルクング)= side effect", field: "ドイツ語・薬学", lv: 3 },
    { ch: "BIP", ja: "国内総生産", mean: "Bruttoinlandsprodukt(ブルットインラントスプロドゥクト)= GDP", field: "ドイツ語・経済学", lv: 2 },
    { ch: "MwSt.", ja: "付加価値税", mean: "Mehrwertsteuer(メーアヴェルトシュトイアー)= VAT", field: "ドイツ語・経済学", lv: 3 },
    { ch: "EZB", ja: "欧州中央銀行", mean: "Europäische Zentralbank。ユーロ圏の金融政策を担う", field: "ドイツ語・経済学", lv: 3 },
    { ch: "KI", ja: "人工知能", mean: "künstliche Intelligenz(キュンストリッヒェ インテリゲンツ)= AI", field: "ドイツ語・情報科学", lv: 2 },
    { ch: "DSGVO", ja: "一般データ保護規則", mean: "Datenschutz-Grundverordnung = GDPR。原語はドイツ語", field: "ドイツ語・情報科学", lv: 4 },
    { ch: "EDV", ja: "電子データ処理", mean: "elektronische Datenverarbeitung。IT の古くからの呼び方", field: "ドイツ語・情報科学", lv: 4 },

    /* --- 中国語 --- */
    { ch: "证毕", ja: "証明終わり", mean: "zhèngbì(ジョンビー)= Q.E.D.。「证明完毕」の略", field: "中国語・数学", lv: 3 },
    { ch: "即", ja: "すなわち", mean: "jí(ジー)= i.e.。「亦即」も使う", field: "中国語・数学", lv: 2 },
    { ch: "例如", ja: "たとえば", mean: "lìrú(リールー)= e.g.", field: "中国語・数学", lv: 1 },
    { ch: "参见", ja: "参照せよ", mean: "cānjiàn(ツァンジエン)= cf. / see", field: "中国語・数学", lv: 2 },
    { ch: "当且仅当", ja: "必要十分条件", mean: "dāng qiě jǐn dāng = if and only if。「そのときかつそのときに限り」の直訳", field: "中国語・数学", lv: 4 },
    { ch: "图 / 表", ja: "図 / 表", mean: "tú / biǎo。日本語の「図」「表」と同じ用法", field: "中国語・物理学", lv: 1 },
    { ch: "标准状况", ja: "標準状態", mean: "biāozhǔn zhuàngkuàng = 標準状態(0 °C, 101.3 kPa)", field: "中国語・化学", lv: 3 },
    { ch: "熔点 / 沸点", ja: "融点 / 沸点", mean: "róngdiǎn / fèidiǎn。日本語の「融点」は中国語では「熔点」と書く", field: "中国語・化学", lv: 3 },
    { ch: "国药准字", ja: "医薬品承認番号", mean: "guóyào zhǔnzì。中国の医薬品承認番号の冒頭表記", field: "中国語・薬学", lv: 5 },
    { ch: "不良反应", ja: "副作用・有害反応", mean: "bùliáng fǎnyìng = adverse reaction", field: "中国語・薬学", lv: 3 },
    { ch: "国内生产总值", ja: "国内総生産", mean: "guónèi shēngchǎn zǒngzhí = GDP。略して「国内生产总值(GDP)」と併記される", field: "中国語・経済学", lv: 2 },
    { ch: "增值税", ja: "付加価値税", mean: "zēngzhíshuì = VAT", field: "中国語・経済学", lv: 3 },
    { ch: "人工智能", ja: "人工知能", mean: "réngōng zhìnéng = AI。「智能」が intelligence", field: "中国語・情報科学", lv: 2 },
    { ch: "操作系统", ja: "オペレーティングシステム", mean: "cāozuò xìtǒng = OS。「系统」が system", field: "中国語・情報科学", lv: 2 }
  ];

  /* ============ 空似言葉・言語で意味がずれる語 ============ */
  var CTX = [
    { ch: "expérience", items: [
      { field: "フランス語・物理学", mean: "実験(experiment)。英語の experience と同形だが第一義は実験" },
      { field: "フランス語・化学", mean: "実験操作・試行" },
      { field: "フランス語・経済学", mean: "経験・体験(expérience acquise)" },
      { field: "フランス語・薬学", mean: "臨床での経験(expérience clinique)" }
    ]},
    { ch: "опыт", items: [
      { field: "ロシア語・物理学", mean: "実験(オープィト)。experiment の意味で使う" },
      { field: "ロシア語・化学", mean: "実験・試行" },
      { field: "ロシア語・経済学", mean: "経験・実績" },
      { field: "ロシア語・薬学", mean: "臨床経験" }
    ]},
    { ch: "actuel / актуальный", items: [
      { field: "フランス語・経済学", mean: "現在の(actuel = current)。英語 actual(実際の)とは別" },
      { field: "ロシア語・経済学", mean: "актуальный = 今日的な・喫緊の。英語 actual とは意味がずれる" },
      { field: "フランス語・数学", mean: "現時点の値・現行の定義" },
      { field: "ロシア語・数学", mean: "актуальная бесконечность = 実無限(数学の術語)" }
    ]},
    { ch: "sensible", items: [
      { field: "フランス語・物理学", mean: "感度が高い(検出器が sensible)" },
      { field: "フランス語・薬学", mean: "感受性がある(菌が抗菌薬に sensible)" },
      { field: "フランス語・経済学", mean: "顕著な(une hausse sensible = 目立った上昇)" },
      { field: "フランス語・化学", mean: "反応しやすい・不安定な" }
    ]},
    { ch: "решение / solution", items: [
      { field: "ロシア語・数学", mean: "решение = 方程式の解" },
      { field: "ロシア語・化学", mean: "раствор が溶液。решение は「解決」で溶液ではない" },
      { field: "フランス語・化学", mean: "solution = 溶液" },
      { field: "フランス語・数学", mean: "solution = 解" }
    ]},
    { ch: "порядок / ordre", items: [
      { field: "ロシア語・数学", mean: "порядок = 位数・階数・順序" },
      { field: "ロシア語・物理学", mean: "порядок величины = 桁" },
      { field: "フランス語・数学", mean: "ordre = 位数・順序" },
      { field: "フランス語・化学", mean: "ordre de réaction = 反応次数" }
    ]},
    { ch: "рецепт / recette", items: [
      { field: "ロシア語・薬学", mean: "рецепт = 処方箋(prescription)" },
      { field: "フランス語・薬学", mean: "ordonnance が処方箋。recette は「レシピ・収入」で処方箋ではない" },
      { field: "フランス語・経済学", mean: "recette = 収入・売上(recettes fiscales = 税収)" },
      { field: "ロシア語・経済学", mean: "выручка = 売上。рецепт は使わない" }
    ]},
    { ch: "octet / byte", items: [
      { field: "フランス語・情報科学", mean: "octet = 8 ビット。フランス語では byte を使わず、8 ビットであることを語で明示する" },
      { field: "ロシア語・情報科学", mean: "байт(バイト)。英語からの借用をそのまま使う" },
      { field: "フランス語・数学", mean: "octet は「8 個組」。数学では 8 元数(octonion)は別語" },
      { field: "フランス語・化学", mean: "octet rule = オクテット則(最外殻電子 8 個)" }
    ]},
    { ch: "ordinateur / компьютер", items: [
      { field: "フランス語・情報科学", mean: "ordinateur = 計算機。ordonner(秩序づける)から作られた仏語独自の語で、computer の直訳ではない" },
      { field: "ロシア語・情報科学", mean: "компьютер(英語からの借用)。旧来は ЭВМ(電子計算機)と呼んだ" },
      { field: "フランス語・経済学", mean: "ordinateur は経済統計でも設備投資の項目名として現れる" },
      { field: "ロシア語・数学", mean: "вычислительная машина = 計算機械(計算そのものを指す言い方)" }
    ]},
    { ch: "logiciel / courriel", items: [
      { field: "フランス語・情報科学", mean: "logiciel = ソフトウェア、courriel = 電子メール。いずれも英語を避けて作られた造語" },
      { field: "フランス語・経済学", mean: "l'industrie du logiciel = ソフトウェア産業" },
      { field: "ロシア語・情報科学", mean: "программное обеспечение(ПО)= ソフトウェア。электронная почта が電子メール" },
      { field: "フランス語・薬学", mean: "logiciel de prescription = 処方支援ソフト" }
    ]},
    { ch: "Satz", items: [
      { field: "ドイツ語・数学", mean: "定理(Lehrsatz)。証明の対象になる主張" },
      { field: "ドイツ語・物理学", mean: "法則(Erhaltungssatz = 保存則)" },
      { field: "ドイツ語・経済学", mean: "率(Zinssatz = 金利、Steuersatz = 税率)" },
      { field: "ドイツ語・情報科学", mean: "文(自然言語処理の sentence)・組版の一組" }
    ]},
    { ch: "Körper", items: [
      { field: "ドイツ語・数学", mean: "体(たい)。四則が自由にできる代数構造(英語 field)" },
      { field: "ドイツ語・物理学", mean: "物体(starrer Körper = 剛体)" },
      { field: "ドイツ語・薬学", mean: "身体(Körpergewicht = 体重、用量計算に使う)" },
      { field: "ドイツ語・化学", mean: "固体・物体としての試料" }
    ]},
    { ch: "Lösung", items: [
      { field: "ドイツ語・化学", mean: "溶液(wässrige Lösung = 水溶液)" },
      { field: "ドイツ語・数学", mean: "解(方程式を満たす値)" },
      { field: "ドイツ語・情報科学", mean: "解決策・ソリューション" },
      { field: "ドイツ語・経済学", mean: "問題の解決(Problemlösung)" }
    ]},
    { ch: "Gift", items: [
      { field: "ドイツ語・薬学", mean: "毒。英語の gift(贈り物)とは全く別の意味" },
      { field: "ドイツ語・化学", mean: "毒物(Giftstoff)。触媒毒は Katalysatorgift" },
      { field: "ドイツ語・物理学", mean: "半導体の文脈では使わない。ドープは dotieren" },
      { field: "ドイツ語・数学", mean: "数学の術語としては用いない" }
    ]},
    { ch: "程序 / 算法", items: [
      { field: "中国語・情報科学", mean: "程序 = プログラム、算法 = アルゴリズム。日本語の「程序(順序)」とは意味が違う" },
      { field: "中国語・数学", mean: "算法 は計算手続き全般。「运算」が演算" },
      { field: "中国語・経済学", mean: "程序 は「手続き・プロセス」の意味でも使う" },
      { field: "中国語・薬学", mean: "操作程序 = 操作手順(SOP)" }
    ]},
    { ch: "需求 / 函数", items: [
      { field: "中国語・経済学", mean: "需求 = 需要。日本語の「需要」とは字が違う" },
      { field: "中国語・数学", mean: "函数 = 関数。日本語が「関数」に書き換える前の表記" },
      { field: "中国語・情報科学", mean: "函数 は関数(サブルーチン)。需求 は要件(requirements)" },
      { field: "中国語・物理学", mean: "波函数 = 波動関数" }
    ]},
    { ch: "氧 / 熵", items: [
      { field: "中国語・化学", mean: "氧 = 酸素。だから酸化は「氧化」で「酸」の字を使わない" },
      { field: "中国語・物理学", mean: "熵 = エントロピー。熱(火)と商から作られた一字の新造字" },
      { field: "中国語・薬学", mean: "氧疗 = 酸素療法" },
      { field: "中国語・情報科学", mean: "信息熵 = 情報エントロピー" }
    ]},
    { ch: "производная / dérivée", items: [
      { field: "ロシア語・数学", mean: "производная = 導関数" },
      { field: "フランス語・数学", mean: "dérivée = 導関数" },
      { field: "フランス語・経済学", mean: "produit dérivé = デリバティブ(金融派生商品)" },
      { field: "ロシア語・化学", mean: "производное = 誘導体(化合物)" }
    ]}
  ];

  /* ==================== 定型表現の対訳 ==================== */
  var EQUATIONS = [
    /* --- ロシア語 --- */
    { eq: "ч.т.д. = что и требовалось доказать", name: "証明終わり(露)", field: "ロシア語・数学", lv: 3,
      mean: "「示すべきことであった」。証明の終わりに置く",
      why: "ラテン語 quod erat demonstrandum の直訳。フランス語の C.Q.F.D. と同じ構造をしている。" },
    { eq: "тогда и только тогда, когда", name: "必要十分条件(露)", field: "ロシア語・数学", lv: 4,
      mean: "「そのときかつそのときに限り」= if and only if",
      why: "英語 iff、フランス語 ssi にあたる定型。数学の同値を宣言する言い方。" },
    { eq: "предел последовательности", name: "数列の極限(露)", field: "ロシア語・数学", lv: 3,
      mean: "предел(プレヂェール)= 極限、последовательность = 数列",
      why: "解析の基本語彙。предельный переход で「極限移行」を表す。" },
    { eq: "необходимо и достаточно", name: "必要かつ十分(露)", field: "ロシア語・数学", lv: 4,
      mean: "必要条件かつ十分条件であること",
      why: "定理の主張を述べるときの定型。フランス語では nécessaire et suffisant。" },
    { eq: "закон сохранения энергии", name: "エネルギー保存則(露)", field: "ロシア語・物理学", lv: 2,
      mean: "закон = 法則、сохранение = 保存、энергия = エネルギー",
      why: "закон сохранения(保存則)は импульса(運動量)、заряда(電荷)にも同じ形で使う。" },
    { eq: "скорость реакции", name: "反応速度(露)", field: "ロシア語・化学", lv: 2,
      mean: "скорость(スコーロスチ)= 速度、реакция = 反応",
      why: "скорость は物理の「速さ」と同じ語。константа скорости で速度定数。" },
    { eq: "период полувыведения", name: "生物学的半減期(露)", field: "ロシア語・薬学", lv: 4,
      mean: "период = 期間、полу- = 半分、выведение = 排出",
      why: "物理の半減期は период полураспада(半崩壊)。薬学では「半分抜ける期間」と言い分ける。" },
    { eq: "побочное действие", name: "副作用(露)", field: "ロシア語・薬学", lv: 3,
      mean: "побочное = 副次的な、действие = 作用",
      why: "нежелательная реакция(望まれない反応)も使う。安全性情報の基本語。" },
    { eq: "спрос и предложение", name: "需要と供給(露)", field: "ロシア語・経済学", lv: 2,
      mean: "спрос(スプロース)= 需要、предложение = 供給",
      why: "предложение は「文・提案」の意味もある多義語。文脈で見分ける。" },
    { eq: "уровень инфляции", name: "インフレ率(露)", field: "ロシア語・経済学", lv: 3,
      mean: "уровень = 水準、инфляция = インフレーション",
      why: "уровень безработицы なら失業率。уровень + 名詞で「〜率・水準」を作る。" },

    /* --- フランス語 --- */
    { eq: "C.Q.F.D. = ce qu'il fallait démontrer", name: "証明終わり(仏)", field: "フランス語・数学", lv: 3,
      mean: "「示すべきであったこと」。証明の終わりに置く",
      why: "ロシア語の ч.т.д. と同じくラテン語 Q.E.D. の直訳。三言語で構造が一致する。" },
    { eq: "si et seulement si (ssi)", name: "必要十分条件(仏)", field: "フランス語・数学", lv: 3,
      mean: "「かつそのときに限り」= if and only if",
      why: "略記 ssi は英語 iff と同じ作り方(語をつなげて短縮)。" },
    { eq: "il suffit de montrer que", name: "〜を示せば十分である(仏)", field: "フランス語・数学", lv: 4,
      mean: "証明の方針を宣言する定型",
      why: "il suffit(十分である)/ il faut(必要である)の対で、必要性と十分性を書き分ける。" },
    { eq: "théorème des accroissements finis", name: "平均値の定理(仏)", field: "フランス語・数学", lv: 5,
      mean: "accroissement = 増分、fini = 有限。「有限増分の定理」",
      why: "英語 mean value theorem と発想が違う名前。仏語圏の教科書ではこの名で載る。" },
    { eq: "quantité de mouvement", name: "運動量(仏)", field: "フランス語・物理学", lv: 3,
      mean: "quantité = 量、mouvement = 運動",
      why: "英語 momentum のようなラテン借用ではなく、意味をそのまま並べた語。" },
    { eq: "loi de conservation de l'énergie", name: "エネルギー保存則(仏)", field: "フランス語・物理学", lv: 2,
      mean: "loi = 法則、conservation = 保存",
      why: "loi de … の形で法則名を作る。ロシア語の закон сохранения と同じ構造。" },
    { eq: "vitesse de réaction", name: "反応速度(仏)", field: "フランス語・化学", lv: 2,
      mean: "vitesse = 速度、réaction = 反応",
      why: "constante de vitesse で速度定数。物理の「速さ」と同じ語を使う点はロシア語と同じ。" },
    { eq: "liaison covalente", name: "共有結合(仏)", field: "フランス語・化学", lv: 3,
      mean: "liaison = 結合、covalente = 共有の",
      why: "liaison hydrogène(水素結合)、liaison ionique(イオン結合)と同じ型で並ぶ。" },
    { eq: "demi-vie plasmatique", name: "血漿中半減期(仏)", field: "フランス語・薬学", lv: 4,
      mean: "demi = 半分、vie = 寿命、plasmatique = 血漿の",
      why: "英語 half-life の直訳的な語。物理の放射性半減期も demi-vie と言う。" },
    { eq: "effet indésirable", name: "副作用(仏)", field: "フランス語・薬学", lv: 3,
      mean: "effet = 作用、indésirable = 望ましくない",
      why: "EU の規制文書で使われる公式表現。英語 adverse reaction に対応する。" },
    { eq: "offre et demande", name: "需要と供給(仏)", field: "フランス語・経済学", lv: 2,
      mean: "offre = 供給、demande = 需要",
      why: "日本語や英語と語順が逆(供給が先)。loi de l'offre et de la demande で需給の法則。" },
    { eq: "taux de chômage", name: "失業率(仏)", field: "フランス語・経済学", lv: 3,
      mean: "taux = 率、chômage = 失業",
      why: "taux d'intérêt(金利)、taux d'inflation(インフレ率)と同じ型。taux + de + 名詞。" },

    /* --- 情報科学 --- */
    { eq: "вычислительная сложность", name: "計算量(露)", field: "ロシア語・情報科学", lv: 4,
      mean: "вычислительный = 計算の、сложность = 複雑さ",
      why: "「計算の複雑さ」という直訳。英語 computational complexity と語の構成が一致する。" },
    { eq: "машинное обучение", name: "機械学習(露)", field: "ロシア語・情報科学", lv: 3,
      mean: "машинное = 機械の、обучение = 学習・訓練",
      why: "обучение は「教えること」でもある。нейронная сеть(ニューラルネット)と組で使われる。" },
    { eq: "открытый ключ / закрытый ключ", name: "公開鍵 / 秘密鍵(露)", field: "ロシア語・情報科学", lv: 4,
      mean: "открытый = 開かれた、закрытый = 閉じられた、ключ = 鍵",
      why: "「開/閉」の対で公開鍵暗号を表す。フランス語では clé publique / clé privée。" },
    { eq: "complexité algorithmique", name: "計算量(仏)", field: "フランス語・情報科学", lv: 4,
      mean: "complexité = 複雑さ、algorithmique = アルゴリズムの",
      why: "英語 computational complexity にあたる。フランス語は形容詞を後置する点が語形の目印。" },
    { eq: "apprentissage automatique", name: "機械学習(仏)", field: "フランス語・情報科学", lv: 3,
      mean: "apprentissage = 学習、automatique = 自動の",
      why: "英語 machine learning を機械ではなく「自動」と訳しているのが特徴。apprentissage profond で深層学習。" },
    { eq: "traitement du signal", name: "信号処理(仏)", field: "フランス語・情報科学", lv: 4,
      mean: "traitement = 処理、signal = 信号",
      why: "traitement de données なら情報処理。traitement + de + 名詞で「〜処理」を作る。" },

    /* --- ドイツ語 --- */
    { eq: "was zu beweisen war (w.z.b.w.)", name: "証明終わり(独)", field: "ドイツ語・数学", lv: 3,
      mean: "「示すべきであったこと」。証明の終わりに置く",
      why: "ラテン語 Q.E.D. の直訳。露 ч.т.д.、仏 C.Q.F.D. と四言語で構造が一致する。" },
    { eq: "genau dann, wenn", name: "必要十分条件(独)", field: "ドイツ語・数学", lv: 4,
      mean: "「ちょうどそのとき、〜のとき」= if and only if",
      why: "英語 iff、仏 ssi、露 тогда и только тогда にあたる定型。" },
    { eq: "ohne Beschränkung der Allgemeinheit", name: "一般性を失わずに(独)", field: "ドイツ語・数学", lv: 5,
      mean: "対称性から場合を絞ってよい、という宣言",
      why: "英語 without loss of generality の直訳。略記 o.B.d.A. で書かれる。" },
    { eq: "Energieerhaltungssatz", name: "エネルギー保存則(独)", field: "ドイツ語・物理学", lv: 3,
      mean: "Energie + Erhaltung(保存)+ Satz(法則)を 1 語に連結したもの",
      why: "ドイツ語は概念を複合語で 1 語にする。長さがそのまま定義の構造を表す。" },
    { eq: "wässrige Lösung", name: "水溶液(独)", field: "ドイツ語・化学", lv: 3,
      mean: "Wasser(水)の形容詞形 + Lösung(溶液)",
      why: "Lösung は「解」でもあるので、数学の文脈と読み分ける必要がある。" },
    { eq: "Halbwertszeit", name: "半減期(独)", field: "ドイツ語・薬学", lv: 4,
      mean: "halb(半分)+ Wert(値)+ Zeit(時間)",
      why: "物理の放射性半減期も薬学の生物学的半減期も同じ語を使う。" },
    { eq: "Angebot und Nachfrage", name: "需要と供給(独)", field: "ドイツ語・経済学", lv: 2,
      mean: "Angebot = 供給、Nachfrage = 需要",
      why: "フランス語 offre et demande と同じく供給が先に来る。日本語と語順が逆。" },
    { eq: "maschinelles Lernen", name: "機械学習(独)", field: "ドイツ語・情報科学", lv: 3,
      mean: "maschinell(機械の)+ Lernen(学習)",
      why: "英語 machine learning の直訳。仏 apprentissage automatique は「自動」と訳す点が違う。" },

    /* --- 中国語 --- */
    { eq: "当且仅当", name: "必要十分条件(中)", field: "中国語・数学", lv: 4,
      mean: "「当たり、かつ、ただ〜のときのみ当たる」= if and only if",
      why: "英語 if and only if を語順ごと写した訳語。数学の同値を宣言する定型。" },
    { eq: "证明完毕(证毕)", name: "証明終わり(中)", field: "中国語・数学", lv: 3,
      mean: "「証明が完了した」",
      why: "四言語(露・仏・独・中)とも、ラテン語 Q.E.D. に対応する決まり文句を持つ。" },
    { eq: "能量守恒定律", name: "エネルギー保存則(中)", field: "中国語・物理学", lv: 3,
      mean: "能量(エネルギー)+ 守恒(保存)+ 定律(法則)",
      why: "「守恒」が保存。动量守恒(運動量保存)、电荷守恒(電荷保存)と同じ型で並ぶ。" },
    { eq: "氧化还原反应", name: "酸化還元反応(中)", field: "中国語・化学", lv: 3,
      mean: "氧化(酸化)+ 还原(還元)+ 反应(反応)",
      why: "「氧」が酸素なので、酸化は「酸」ではなく「氧」の字で書く。日本語との大きな違い。" },
    { eq: "时间复杂度", name: "時間計算量(中)", field: "中国語・情報科学", lv: 3,
      mean: "时间(時間)+ 复杂度(複雑さの度合い)",
      why: "英語 time complexity の直訳。空间复杂度なら空間計算量。" },
    { eq: "通货膨胀率", name: "インフレ率(中)", field: "中国語・経済学", lv: 3,
      mean: "通货(通貨)+ 膨胀(膨張)+ 率",
      why: "「通貨が膨らむ」という比喩がそのまま術語になっている。失业率(失業率)と同じ「〜率」の型。" }
  ];

  /* ============ 日本語/英語 → ロシア語・フランス語 の連想 ============ */
  var ASSOC = [
    { simple: "証明の終わりに書く記号(英: Q.E.D.)", simpleMean: "示すべきことは示された",
      adv: "ч.т.д.", advName: "что и требовалось доказать(露)", field: "ロシア語・数学", lv: 3,
      why: "ラテン語 quod erat demonstrandum をロシア語に直訳したもの。フランス語 C.Q.F.D. も同じ直訳。",
      wrong: ["и т.д.", "т.е.", "см."] },
    { simple: "「かつそのときに限り」(英: iff)", simpleMean: "同値であることの宣言",
      adv: "si et seulement si (ssi)", advName: "必要十分条件(仏)", field: "フランス語・数学", lv: 3,
      why: "英語 iff、ロシア語 тогда и только тогда と対応する。三言語とも「そのときかつそのときだけ」という同じ言い方。",
      wrong: ["c'est-à-dire", "par exemple", "d'où"] },
    { simple: "微分して得られる関数", simpleMean: "変化の速さを表す関数",
      adv: "производная", advName: "導関数(露)", field: "ロシア語・数学", lv: 3,
      why: "производить(生み出す)から。フランス語 dérivée も「派生したもの」で、発想は同じ。",
      wrong: ["интеграл", "предел", "уравнение"] },
    { simple: "エネルギーは増えも減りもしない", simpleMean: "保存される量がある",
      adv: "loi de conservation de l'énergie", advName: "エネルギー保存則(仏)", field: "フランス語・物理学", lv: 2,
      why: "loi de conservation(保存則)の型。ロシア語 закон сохранения も語の並びが同じ。",
      wrong: ["quantité de mouvement", "vitesse de réaction", "liaison covalente"] },
    { simple: "温度を上げると反応が速くなる", simpleMean: "反応の速さが変わる",
      adv: "скорость реакции", advName: "反応速度(露)", field: "ロシア語・化学", lv: 2,
      why: "скорость は物理の「速さ」と同じ語。константа скорости(速度定数)へつながる。",
      wrong: ["раствор", "вещество", "давление"] },
    { simple: "原子どうしが電子を出し合ってつながる", simpleMean: "電子を共有して結合する",
      adv: "liaison covalente", advName: "共有結合(仏)", field: "フランス語・化学", lv: 3,
      why: "liaison(結合)+ covalente(共有の)。liaison hydrogène / ionique と同じ型で語彙が広がる。",
      wrong: ["solution aqueuse", "point de fusion", "vitesse de réaction"] },
    { simple: "薬が半分になるまでの時間", simpleMean: "濃度が半減する時間",
      adv: "период полувыведения", advName: "生物学的半減期(露)", field: "ロシア語・薬学", lv: 4,
      why: "полу-(半分)+ выведение(排出)。放射性物質の半減期は полураспада(半崩壊)と言い分ける。",
      wrong: ["побочное действие", "лекарственное средство", "дозировка"] },
    { simple: "薬の望ましくない働き", simpleMean: "副作用",
      adv: "effet indésirable", advName: "副作用(仏)", field: "フランス語・薬学", lv: 3,
      why: "effet(作用)+ indésirable(望ましくない)。EU の規制文書の公式表現。",
      wrong: ["demi-vie plasmatique", "ordonnance", "posologie"] },
    { simple: "買いたい量と売りたい量", simpleMean: "需要と供給",
      adv: "offre et demande", advName: "需要と供給(仏)", field: "フランス語・経済学", lv: 2,
      why: "フランス語では供給(offre)が先に来る。日本語・英語と語順が逆になる点に注意。",
      wrong: ["taux de chômage", "produit intérieur brut", "valeur ajoutée"] },
    { simple: "国内で生み出された付加価値の合計", simpleMean: "GDP",
      adv: "ВВП (валовой внутренний продукт)", advName: "国内総生産(露)", field: "ロシア語・経済学", lv: 3,
      why: "валовой(粗い・総額の)+ внутренний(内部の)+ продукт(生産物)。フランス語 PIB も同じ構成。",
      wrong: ["уровень инфляции", "спрос и предложение", "ЦБ РФ"] },
    { simple: "物価が上がっていく割合", simpleMean: "インフレ率",
      adv: "уровень инфляции", advName: "インフレ率(露)", field: "ロシア語・経済学", lv: 3,
      why: "уровень(水準)+ 名詞で率を表す。уровень безработицы なら失業率。",
      wrong: ["спрос и предложение", "ВВП", "выручка"] },
    { simple: "働きたいのに職がない人の割合", simpleMean: "失業率",
      adv: "taux de chômage", advName: "失業率(仏)", field: "フランス語・経済学", lv: 3,
      why: "taux(率)+ de + 名詞。taux d'intérêt(金利)、taux d'inflation(インフレ率)と同じ作り方。",
      wrong: ["offre et demande", "valeur ajoutée", "produit intérieur brut"] },
    { simple: "実験のことを何と言うか(仏)", simpleMean: "experiment にあたる語",
      adv: "expérience", advName: "実験(仏)", field: "フランス語・物理学", lv: 3,
      why: "英語の experience と同形だが、フランス語では第一義が「実験」。空似言葉の代表例。",
      wrong: ["expertise", "épreuve", "essai clinique"] },
    { simple: "「計算機」をフランス語で言うと", simpleMean: "コンピュータのこと",
      adv: "ordinateur", advName: "計算機(仏)", field: "フランス語・情報科学", lv: 3,
      why: "英語 computer(計算するもの)を借りず、ordonner(秩序づける)から作った仏語独自の語。logiciel(ソフト)・courriel(メール)も同じく英語を避けて作られた。",
      wrong: ["calculatrice", "compteur", "processeur"] },
    { simple: "「8 ビットのまとまり」をフランス語では", simpleMean: "1 バイトのこと",
      adv: "octet", advName: "オクテット(仏)", field: "フランス語・情報科学", lv: 3,
      why: "byte は必ずしも 8 ビットではなかったため、フランス語は「8 個組」を意味する octet を採った。Ko/Mo/Go は KB/MB/GB にあたる。",
      wrong: ["bit", "mot", "chiffre"] },
    { simple: "コンピュータに例から学ばせること(露)", simpleMean: "データから規則を覚える",
      adv: "машинное обучение", advName: "機械学習(露)", field: "ロシア語・情報科学", lv: 3,
      why: "машинное(機械の)+ обучение(学習)。フランス語は apprentissage automatique で、「機械」ではなく「自動」と表現する。",
      wrong: ["искусственный интеллект", "нейронная сеть", "программирование"] },
    { simple: "開ける鍵と閉める鍵を分ける(露)", simpleMean: "公開鍵暗号のこと",
      adv: "открытый ключ / закрытый ключ", advName: "公開鍵 / 秘密鍵(露)", field: "ロシア語・情報科学", lv: 4,
      why: "открытый(開かれた)/ закрытый(閉じられた)の対で表す。フランス語では clé publique / clé privée。",
      wrong: ["шифрование", "хеш-функция", "цифровая подпись"] },
    { simple: "「毒」をドイツ語で言うと", simpleMean: "体に害を与える物質",
      adv: "Gift", advName: "毒(独)", field: "ドイツ語・薬学", lv: 3,
      why: "英語の gift(贈り物)と同じ綴りだが意味は「毒」。空似言葉の代表例で、Giftstoff(毒物)のように複合語を作る。",
      wrong: ["Geschenk", "Arznei", "Wirkstoff"] },
    { simple: "代数で「四則が自由にできる構造」(独)", simpleMean: "足し算も割り算もできる集まり",
      adv: "Körper", advName: "体(独)", field: "ドイツ語・数学", lv: 4,
      why: "英語 field、仏語 corps にあたる。ドイツ語では「身体・物体」と同じ語で、物理では剛体 starrer Körper に使う。",
      wrong: ["Ring", "Menge", "Gruppe"] },
    { simple: "解の形をあらかじめ仮に置く(独)", simpleMean: "こういう形だろうと当たりをつける",
      adv: "Ansatz", advName: "アンザッツ(独)", field: "ドイツ語・数学", lv: 5,
      why: "英語圏でもそのまま ansatz として使われる。訳しにくいまま輸入された数学・物理の語。",
      wrong: ["Beweis", "Vermutung", "Abbildung"] },
    { simple: "エネルギーは増えも減りもしない(独)", simpleMean: "保存される量がある",
      adv: "Energieerhaltungssatz", advName: "エネルギー保存則(独)", field: "ドイツ語・物理学", lv: 3,
      why: "Energie + Erhaltung + Satz を 1 語に連結する。ドイツ語では概念の構造がそのまま語の長さになる。",
      wrong: ["Wellenfunktion", "Beschleunigung", "Wirkungsquerschnitt"] },
    { simple: "薬が半分になるまでの時間(独)", simpleMean: "濃度が半減する時間",
      adv: "Halbwertszeit", advName: "半減期(独)", field: "ドイツ語・薬学", lv: 3,
      why: "halb(半分)+ Wert(値)+ Zeit(時間)。ロシア語は период полувыведения、フランス語は demi-vie。",
      wrong: ["Nebenwirkung", "Dosierung", "Wirkstoff"] },
    { simple: "「酸化」を中国語で書くと", simpleMean: "酸素と結びつくこと",
      adv: "氧化", advName: "酸化(中)", field: "中国語・化学", lv: 3,
      why: "中国語では酸素を「氧」と書くため、酸化は「酸」ではなく「氧化」。還元は「还原」。",
      wrong: ["酸化", "还原", "催化"] },
    { simple: "「関数」を中国語で書くと", simpleMean: "入力に対して出力が決まる対応",
      adv: "函数", advName: "関数(中)", field: "中国語・数学", lv: 2,
      why: "日本語も戦前は「函数」と書いた。中国語は今もこの表記を使う。方程(方程式)、矩阵(行列)も日本語と字が違う。",
      wrong: ["方程", "矩阵", "集合"] },
    { simple: "「コンピュータ」を中国語で言うと", simpleMean: "計算する機械",
      adv: "计算机", advName: "計算機(中)", field: "中国語・情報科学", lv: 2,
      why: "大陸では「计算机」、台湾では「電腦(電子の脳)」。フランス語 ordinateur と同じく、音訳を避けて意味で作った語。",
      wrong: ["电脑", "程序", "网络"] },
    { simple: "でたらめさの度合いを表す一字(中)", simpleMean: "乱雑さを測る量",
      adv: "熵", advName: "エントロピー(中)", field: "中国語・物理学", lv: 4,
      why: "火(熱)と商を組み合わせて作られた一字の新造字。熱量を温度で割る(商)という定義がそのまま字形になっている。",
      wrong: ["焓", "能量", "功"] },
    { simple: "買いたい量のことを中国語では", simpleMean: "需要のこと",
      adv: "需求", advName: "需要(中)", field: "中国語・経済学", lv: 2,
      why: "日本語の「需要」は中国語では「需求」、「供給」は「供给」。字が少しずつ違う点に注意。",
      wrong: ["供给", "价格", "市场"] },
    { simple: "方程式の「解」(露)", simpleMean: "方程式を満たす値",
      adv: "решение", advName: "解(露)", field: "ロシア語・数学", lv: 3,
      why: "решение は「解決」でもある。化学の「溶液」は раствор で、英語 solution の二つの意味が別語になる。",
      wrong: ["раствор", "уравнение", "предел"] }
  ];

  /* ======================= 専門用語(t = 原語) ======================= */
  var TERMS = [
    /* --- ロシア語・数学 --- */
    { t: "производная", en: "導関数", field: "ロシア語・数学", lv: 3, def: "プロイズヴォードナヤ。微分して得られる関数" },
    { t: "интеграл", en: "積分", field: "ロシア語・数学", lv: 2, def: "インテグラール。和の極限として面積などを与える" },
    { t: "предел", en: "極限", field: "ロシア語・数学", lv: 2, def: "プレヂェール。限りなく近づく値" },
    { t: "уравнение", en: "方程式", field: "ロシア語・数学", lv: 2, def: "ウラヴネーニエ。равный(等しい)から作られた語" },
    { t: "множество", en: "集合", field: "ロシア語・数学", lv: 3, def: "ムノージェストヴォ。много(多い)から。теория множеств で集合論" },
    { t: "функция", en: "関数", field: "ロシア語・数学", lv: 1, def: "フーンクツィヤ" },
    { t: "матрица", en: "行列", field: "ロシア語・数学", lv: 3, def: "マートリツァ。собственное значение で固有値" },
    { t: "вероятность", en: "確率", field: "ロシア語・数学", lv: 3, def: "ヴェロヤートノスチ。вероятный(ありそうな)から" },
    { t: "доказательство", en: "証明", field: "ロシア語・数学", lv: 3, def: "ドカザーチェリストヴォ。доказать(証明する)の名詞形" },
    { t: "теорема", en: "定理", field: "ロシア語・数学", lv: 2, def: "テオレーマ。лемма(補題)、следствие(系)と組で使う" },
    { t: "непрерывность", en: "連続性", field: "ロシア語・数学", lv: 4, def: "ネプレルィーヴノスチ。не(否定)+ прерывать(中断する)" },

    /* --- ロシア語・物理学 --- */
    { t: "скорость", en: "速度", field: "ロシア語・物理学", lv: 1, def: "スコーロスチ。化学の反応速度にも同じ語を使う" },
    { t: "ускорение", en: "加速度", field: "ロシア語・物理学", lv: 2, def: "ウスコレーニエ。скорость に接頭辞が付いた形" },
    { t: "сила", en: "力", field: "ロシア語・物理学", lv: 1, def: "シーラ。сила тяжести で重力" },
    { t: "энергия", en: "エネルギー", field: "ロシア語・物理学", lv: 1, def: "エネールギヤ" },
    { t: "импульс", en: "運動量", field: "ロシア語・物理学", lv: 3, def: "イーンプリス。закон сохранения импульса で運動量保存則" },
    { t: "волновая функция", en: "波動関数", field: "ロシア語・物理学", lv: 4, def: "ヴォルノヴァーヤ フーンクツィヤ。волна = 波" },
    { t: "проводимость", en: "伝導率", field: "ロシア語・物理学", lv: 4, def: "プロヴォヂーモスチ。сверхпроводимость で超伝導" },
    { t: "сверхпроводимость", en: "超伝導", field: "ロシア語・物理学", lv: 5, def: "スヴェルフプロヴォヂーモスチ。сверх-(超)+ проводимость(伝導)" },
    { t: "плотность", en: "密度", field: "ロシア語・物理学", lv: 2, def: "プロートノスチ。плотность состояний で状態密度" },
    { t: "колебание", en: "振動", field: "ロシア語・物理学", lv: 3, def: "コレバーニエ。колебания решётки で格子振動" },

    /* --- ロシア語・化学 --- */
    { t: "вещество", en: "物質", field: "ロシア語・化学", lv: 2, def: "ヴェシチェストヴォー" },
    { t: "раствор", en: "溶液", field: "ロシア語・化学", lv: 2, def: "ラストヴォール。растворить(溶かす)から。решение(解決)とは別語" },
    { t: "реакция", en: "反応", field: "ロシア語・化学", lv: 1, def: "レアークツィヤ" },
    { t: "окисление", en: "酸化", field: "ロシア語・化学", lv: 3, def: "オキスレーニエ。восстановление が還元" },
    { t: "восстановление", en: "還元", field: "ロシア語・化学", lv: 4, def: "ヴォススタノヴレーニエ。「回復」の意味もある" },
    { t: "кислота", en: "酸", field: "ロシア語・化学", lv: 2, def: "キスロター。основание が塩基" },
    { t: "соединение", en: "化合物", field: "ロシア語・化学", lv: 3, def: "ソエヂネーニエ。соединить(結合する)から" },
    { t: "катализатор", en: "触媒", field: "ロシア語・化学", lv: 3, def: "カタリザートル" },
    { t: "равновесие", en: "平衡", field: "ロシア語・化学", lv: 3, def: "ラヴノヴェーシエ。равный(等しい)+ вес(重さ)" },
    { t: "молекулярная масса", en: "分子量", field: "ロシア語・化学", lv: 3, def: "モレクリャールナヤ マッサ" },

    /* --- ロシア語・薬学 --- */
    { t: "лекарство", en: "薬", field: "ロシア語・薬学", lv: 2, def: "レカールストヴォ。лечить(治療する)から" },
    { t: "доза", en: "用量", field: "ロシア語・薬学", lv: 2, def: "ドーザ。дозировка で用法用量" },
    { t: "рецепт", en: "処方箋", field: "ロシア語・薬学", lv: 3, def: "レツェープト。フランス語の recette(レシピ・収入)とは意味が違う" },
    { t: "побочное действие", en: "副作用", field: "ロシア語・薬学", lv: 3, def: "パボーチノエ ヂェーイストヴィエ" },
    { t: "всасывание", en: "吸収", field: "ロシア語・薬学", lv: 4, def: "フサースィヴァニエ。消化管からの吸収" },
    { t: "выведение", en: "排泄", field: "ロシア語・薬学", lv: 4, def: "ヴィヴェヂェーニエ。период полувыведения で半減期" },
    { t: "противопоказание", en: "禁忌", field: "ロシア語・薬学", lv: 5, def: "プロチヴォポカザーニエ。против(反対)+ показание(適応)" },
    { t: "показание", en: "適応", field: "ロシア語・薬学", lv: 4, def: "ポカザーニエ。その薬を使ってよい病態" },
    { t: "антибиотик", en: "抗生物質", field: "ロシア語・薬学", lv: 2, def: "アンチビオーチク" },
    { t: "клиническое испытание", en: "臨床試験", field: "ロシア語・薬学", lv: 4, def: "クリニーチェスコエ イスピターニエ" },

    /* --- ロシア語・経済学 --- */
    { t: "спрос", en: "需要", field: "ロシア語・経済学", lv: 2, def: "スプロース。спросить(尋ねる・求める)から" },
    { t: "предложение", en: "供給", field: "ロシア語・経済学", lv: 3, def: "プレドロジェーニエ。「文・提案」の意味もある多義語" },
    { t: "издержки", en: "費用", field: "ロシア語・経済学", lv: 3, def: "イズヂェールジキ。предельные издержки で限界費用" },
    { t: "прибыль", en: "利潤", field: "ロシア語・経済学", lv: 2, def: "プリーブィリ。убыток が損失" },
    { t: "инфляция", en: "インフレーション", field: "ロシア語・経済学", lv: 2, def: "インフリャーツィヤ" },
    { t: "безработица", en: "失業", field: "ロシア語・経済学", lv: 3, def: "ベズラボーチツァ。без(無い)+ работа(仕事)" },
    { t: "процентная ставка", en: "金利", field: "ロシア語・経済学", lv: 3, def: "プロツェーントナヤ スターフカ" },
    { t: "налог", en: "税", field: "ロシア語・経済学", lv: 2, def: "ナローグ。НДС で付加価値税" },
    { t: "рынок", en: "市場", field: "ロシア語・経済学", lv: 2, def: "ルィーノク。рыночная экономика で市場経済" },
    { t: "равновесная цена", en: "均衡価格", field: "ロシア語・経済学", lv: 4, def: "ラヴノヴェースナヤ ツェナー" },

    /* --- ロシア語・情報科学 --- */
    { t: "программа", en: "プログラム", field: "ロシア語・情報科学", lv: 1, def: "プログラーンマ。программирование で プログラミング" },
    { t: "вычисление", en: "計算", field: "ロシア語・情報科学", lv: 3, def: "ヴィチスレーニエ。вычислительная машина で計算機" },
    { t: "алгоритм", en: "アルゴリズム", field: "ロシア語・情報科学", lv: 2, def: "アルゴリートム。al-Khwārizmī 由来なのは英語と同じ" },
    { t: "данные", en: "データ", field: "ロシア語・情報科学", lv: 2, def: "ダーンヌィエ。常に複数形。база данных でデータベース" },
    { t: "память", en: "メモリ", field: "ロシア語・情報科学", lv: 2, def: "パーミャチ。「記憶」の一般語でもある" },
    { t: "сеть", en: "ネットワーク", field: "ロシア語・情報科学", lv: 2, def: "セーチ。「網」。нейронная сеть でニューラルネットワーク" },
    { t: "нейронная сеть", en: "ニューラルネットワーク", field: "ロシア語・情報科学", lv: 4, def: "ネイローンナヤ セーチ" },
    { t: "машинное обучение", en: "機械学習", field: "ロシア語・情報科学", lv: 3, def: "マシーンノエ オブチェーニエ" },
    { t: "шифрование", en: "暗号化", field: "ロシア語・情報科学", lv: 4, def: "シフロヴァーニエ。шифр(暗号)から" },
    { t: "ключ", en: "鍵", field: "ロシア語・情報科学", lv: 2, def: "クリューチ。открытый ключ で公開鍵" },
    { t: "поиск", en: "探索", field: "ロシア語・情報科学", lv: 2, def: "ポーイスク。двоичный поиск で二分探索" },
    { t: "сортировка", en: "整列(ソート)", field: "ロシア語・情報科学", lv: 3, def: "ソルチローフカ" },
    { t: "файл", en: "ファイル", field: "ロシア語・情報科学", lv: 1, def: "ファイル。英語からの借用" },
    { t: "ошибка", en: "誤り・バグ", field: "ロシア語・情報科学", lv: 2, def: "オシープカ。「間違い」の一般語。баг も使う" },
    { t: "пользователь", en: "利用者", field: "ロシア語・情報科学", lv: 3, def: "ポーリゾヴァチェリ。польза(役に立つこと)から" },
    { t: "сервер", en: "サーバ", field: "ロシア語・情報科学", lv: 2, def: "セールヴェル" },
    { t: "облачные вычисления", en: "クラウドコンピューティング", field: "ロシア語・情報科学", lv: 4, def: "オーブラチヌィエ ヴィチスレーニヤ。облако = 雲" },
    { t: "искусственный интеллект", en: "人工知能", field: "ロシア語・情報科学", lv: 3, def: "イスクーストヴェンヌィ インテレークト" },

    /* --- フランス語・数学 --- */
    { t: "dérivée", en: "導関数", field: "フランス語・数学", lv: 3, def: "デリヴェ。dériver(派生する)から" },
    { t: "intégrale", en: "積分", field: "フランス語・数学", lv: 2, def: "アンテグラル" },
    { t: "limite", en: "極限", field: "フランス語・数学", lv: 2, def: "リミット" },
    { t: "ensemble", en: "集合", field: "フランス語・数学", lv: 3, def: "アンサンブル。théorie des ensembles で集合論" },
    { t: "application", en: "写像", field: "フランス語・数学", lv: 4, def: "アプリカシオン。英語 map にあたる。「応用」の意味もある" },
    { t: "corps", en: "体(たい)", field: "フランス語・数学", lv: 4, def: "コール。英語 field。anneau(環)、groupe(群)と組で覚える" },
    { t: "anneau", en: "環", field: "フランス語・数学", lv: 4, def: "アノー。「指輪」が原義。英語 ring と同じ発想" },
    { t: "démonstration", en: "証明", field: "フランス語・数学", lv: 3, def: "デモンストラシオン。preuve も使う" },
    { t: "borné", en: "有界な", field: "フランス語・数学", lv: 4, def: "ボルネ。borne(境界)から" },
    { t: "dénombrable", en: "可算な", field: "フランス語・数学", lv: 5, def: "デノンブラーブル。dénombrer(数え上げる)から" },
    { t: "espace vectoriel", en: "ベクトル空間", field: "フランス語・数学", lv: 3, def: "エスパス ヴェクトリエル" },

    /* --- フランス語・物理学 --- */
    { t: "vitesse", en: "速度", field: "フランス語・物理学", lv: 1, def: "ヴィテス。化学の反応速度にも使う" },
    { t: "accélération", en: "加速度", field: "フランス語・物理学", lv: 2, def: "アクセレラシオン" },
    { t: "quantité de mouvement", en: "運動量", field: "フランス語・物理学", lv: 3, def: "カンティテ ド ムーヴマン。英語 momentum の言い換え" },
    { t: "énergie", en: "エネルギー", field: "フランス語・物理学", lv: 1, def: "エネルジー" },
    { t: "champ", en: "場", field: "フランス語・物理学", lv: 3, def: "シャン。champ magnétique で磁場。数学の「体」は corps で別語" },
    { t: "onde", en: "波", field: "フランス語・物理学", lv: 2, def: "オンド。fonction d'onde で波動関数" },
    { t: "rayonnement", en: "放射", field: "フランス語・物理学", lv: 4, def: "レヨンヌマン。rayon(光線)から" },
    { t: "supraconductivité", en: "超伝導", field: "フランス語・物理学", lv: 5, def: "スュプラコンデュクティヴィテ。supra-(超)+ conductivité" },
    { t: "pesanteur", en: "重力", field: "フランス語・物理学", lv: 3, def: "プザントゥール。gravitation も使う" },
    { t: "rendement", en: "効率・収率", field: "フランス語・物理学", lv: 3, def: "ランドマン。化学では収率、経済では利回りも指す" },

    /* --- フランス語・化学 --- */
    { t: "solution aqueuse", en: "水溶液", field: "フランス語・化学", lv: 2, def: "ソリュシオン アクーズ" },
    { t: "mélange", en: "混合物", field: "フランス語・化学", lv: 2, def: "メランジュ。corps pur(純物質)と対になる" },
    { t: "liaison covalente", en: "共有結合", field: "フランス語・化学", lv: 3, def: "リエゾン コヴァラント" },
    { t: "oxydoréduction", en: "酸化還元", field: "フランス語・化学", lv: 4, def: "オキシドレデュクシオン。oxydation と réduction の合成" },
    { t: "acide / base", en: "酸 / 塩基", field: "フランス語・化学", lv: 2, def: "アシッド / バーズ" },
    { t: "point de fusion", en: "融点", field: "フランス語・化学", lv: 3, def: "ポワン ド フュジオン。point d'ébullition が沸点" },
    { t: "rendement de réaction", en: "反応収率", field: "フランス語・化学", lv: 3, def: "ランドマン ド レアクシオン" },
    { t: "catalyseur", en: "触媒", field: "フランス語・化学", lv: 3, def: "カタリズール" },
    { t: "équilibre chimique", en: "化学平衡", field: "フランス語・化学", lv: 3, def: "エキリーブル シミック" },
    { t: "masse molaire", en: "モル質量", field: "フランス語・化学", lv: 3, def: "マス モレール" },

    /* --- フランス語・薬学 --- */
    { t: "médicament", en: "医薬品", field: "フランス語・薬学", lv: 2, def: "メディカマン" },
    { t: "ordonnance", en: "処方箋", field: "フランス語・薬学", lv: 3, def: "オルドナンス。recette(レシピ・収入)ではない" },
    { t: "posologie", en: "用法用量", field: "フランス語・薬学", lv: 4, def: "ポゾロジー。dose(用量)と投与間隔をまとめた語" },
    { t: "effet indésirable", en: "副作用", field: "フランス語・薬学", lv: 3, def: "エフェ アンデジラーブル" },
    { t: "biodisponibilité", en: "バイオアベイラビリティ", field: "フランス語・薬学", lv: 4, def: "ビオディスポニビリテ。全身循環に到達する割合" },
    { t: "demi-vie", en: "半減期", field: "フランス語・薬学", lv: 3, def: "ドゥミ ヴィ。demi(半分)+ vie(寿命)" },
    { t: "contre-indication", en: "禁忌", field: "フランス語・薬学", lv: 4, def: "コントル アンディカシオン。contre(反対)+ indication(適応)" },
    { t: "essai clinique", en: "臨床試験", field: "フランス語・薬学", lv: 3, def: "エセ クリニック" },
    { t: "principe actif", en: "有効成分", field: "フランス語・薬学", lv: 3, def: "プランシプ アクティフ。excipient が添加剤" },
    { t: "voie orale", en: "経口投与", field: "フランス語・薬学", lv: 3, def: "ヴォワ オラル。voie intraveineuse で静脈内投与" },

    /* --- フランス語・経済学 --- */
    { t: "offre", en: "供給", field: "フランス語・経済学", lv: 2, def: "オフル。offre et demande で需給(供給が先)" },
    { t: "demande", en: "需要", field: "フランス語・経済学", lv: 2, def: "ドゥマンド" },
    { t: "coût marginal", en: "限界費用", field: "フランス語・経済学", lv: 3, def: "クー マルジナル" },
    { t: "valeur ajoutée", en: "付加価値", field: "フランス語・経済学", lv: 3, def: "ヴァルール アジュテ。TVA(付加価値税)の由来" },
    { t: "chômage", en: "失業", field: "フランス語・経済学", lv: 3, def: "ショマージュ。taux de chômage で失業率" },
    { t: "croissance", en: "成長", field: "フランス語・経済学", lv: 2, def: "クロワサンス。croissance économique で経済成長" },
    { t: "impôt", en: "税", field: "フランス語・経済学", lv: 2, def: "アンポ。impôt sur le revenu で所得税" },
    { t: "taux d'intérêt", en: "金利", field: "フランス語・経済学", lv: 3, def: "トー ダンテレ" },
    { t: "épargne", en: "貯蓄", field: "フランス語・経済学", lv: 3, def: "エパルニュ。investissement(投資)と対になる" },
    { t: "concurrence", en: "競争", field: "フランス語・経済学", lv: 3, def: "コンキュランス。concurrence parfaite で完全競争" },

    /* --- フランス語・情報科学 --- */
    { t: "ordinateur", en: "計算機(コンピュータ)", field: "フランス語・情報科学", lv: 2, def: "オルディナトゥール。ordonner(秩序づける)から作られた仏語独自の語" },
    { t: "logiciel", en: "ソフトウェア", field: "フランス語・情報科学", lv: 2, def: "ロジシエル。logique + matériel の型で作られた造語。matériel がハードウェア" },
    { t: "octet", en: "バイト(8 ビット)", field: "フランス語・情報科学", lv: 3, def: "オクテ。「8 個組」。Ko/Mo/Go が KB/MB/GB にあたる" },
    { t: "données", en: "データ", field: "フランス語・情報科学", lv: 2, def: "ドネ。base de données でデータベース" },
    { t: "mémoire", en: "メモリ・記憶", field: "フランス語・情報科学", lv: 2, def: "メモワール。「論文・記憶」の意味もある多義語" },
    { t: "réseau", en: "ネットワーク", field: "フランス語・情報科学", lv: 2, def: "レゾー。「網」。réseau de neurones でニューラルネット" },
    { t: "apprentissage automatique", en: "機械学習", field: "フランス語・情報科学", lv: 3, def: "アプランティサージュ オトマティック。「自動学習」と表現する" },
    { t: "apprentissage profond", en: "深層学習", field: "フランス語・情報科学", lv: 4, def: "アプランティサージュ プロフォン" },
    { t: "chiffrement", en: "暗号化", field: "フランス語・情報科学", lv: 4, def: "シフルマン。chiffre(数字・暗号)から" },
    { t: "clé publique", en: "公開鍵", field: "フランス語・情報科学", lv: 4, def: "クレ ピュブリック。clé privée が秘密鍵" },
    { t: "tri", en: "整列(ソート)", field: "フランス語・情報科学", lv: 3, def: "トリ。trier(選り分ける)から。tri rapide でクイックソート" },
    { t: "recherche", en: "探索・研究", field: "フランス語・情報科学", lv: 2, def: "ルシェルシュ。「研究」と「探索」の両方を指す" },
    { t: "fichier", en: "ファイル", field: "フランス語・情報科学", lv: 2, def: "フィシエ" },
    { t: "bogue", en: "バグ", field: "フランス語・情報科学", lv: 3, def: "ボーグ。英語 bug のフランス語化した綴り。déboguer でデバッグ" },
    { t: "utilisateur", en: "利用者", field: "フランス語・情報科学", lv: 2, def: "ユティリザトゥール" },
    { t: "serveur", en: "サーバ", field: "フランス語・情報科学", lv: 2, def: "セルヴール" },
    { t: "infonuagique", en: "クラウドコンピューティング", field: "フランス語・情報科学", lv: 5, def: "アンフォニュアジック。information + nuage(雲)の造語。ケベックで作られた" },
    { t: "courriel", en: "電子メール", field: "フランス語・情報科学", lv: 3, def: "クーリエル。courrier + électronique の造語。ケベック発祥で仏本国にも広まった" },
    { t: "intelligence artificielle", en: "人工知能", field: "フランス語・情報科学", lv: 3, def: "アンテリジャンス アルティフィシエル" },

    /* --- ドイツ語・数学 --- */
    { t: "Ableitung", en: "導関数", field: "ドイツ語・数学", lv: 3, def: "アップライトゥング。ableiten(導き出す)から" },
    { t: "Integral", en: "積分", field: "ドイツ語・数学", lv: 2, def: "インテグラール" },
    { t: "Grenzwert", en: "極限", field: "ドイツ語・数学", lv: 3, def: "グレンツヴェルト。Grenze(境界)+ Wert(値)" },
    { t: "Menge", en: "集合", field: "ドイツ語・数学", lv: 2, def: "メンゲ。「量・多数」の一般語でもある。Mengenlehre で集合論" },
    { t: "Abbildung", en: "写像", field: "ドイツ語・数学", lv: 4, def: "アップビルドゥング。「図」の意味もある(Abb.)" },
    { t: "Körper", en: "体(たい)", field: "ドイツ語・数学", lv: 4, def: "ケルパー。「身体・物体」でもある。英語 field にあたる" },
    { t: "Ring", en: "環", field: "ドイツ語・数学", lv: 4, def: "リング。英語 ring と同じ語で、加法と乗法をもつ構造" },
    { t: "Beweis", en: "証明", field: "ドイツ語・数学", lv: 3, def: "ベヴァイス。beweisen(証明する)から" },
    { t: "Satz", en: "定理", field: "ドイツ語・数学", lv: 3, def: "ザッツ。「文・楽章」の意味もある多義語" },
    { t: "Eigenwert", en: "固有値", field: "ドイツ語・数学", lv: 3, def: "アイゲンヴェルト。英語 eigenvalue はこの語の前半をそのまま借りた" },
    { t: "Ansatz", en: "解の形の仮置き", field: "ドイツ語・数学", lv: 5, def: "アンザッツ。英語圏でもそのまま ansatz として使う" },
    { t: "Vermutung", en: "予想", field: "ドイツ語・数学", lv: 4, def: "フェアムートゥング。未証明の主張" },

    /* --- ドイツ語・物理学 --- */
    { t: "Geschwindigkeit", en: "速度", field: "ドイツ語・物理学", lv: 2, def: "ゲシュヴィンディヒカイト" },
    { t: "Beschleunigung", en: "加速度", field: "ドイツ語・物理学", lv: 3, def: "ベシュロイニグング" },
    { t: "Kraft", en: "力", field: "ドイツ語・物理学", lv: 1, def: "クラフト。Schwerkraft で重力" },
    { t: "Impuls", en: "運動量", field: "ドイツ語・物理学", lv: 3, def: "インプルス。Impulserhaltung で運動量保存" },
    { t: "Wellenfunktion", en: "波動関数", field: "ドイツ語・物理学", lv: 4, def: "ヴェレンフンクツィオーン。Welle = 波" },
    { t: "Zustandsdichte", en: "状態密度", field: "ドイツ語・物理学", lv: 5, def: "ツーシュタンツディヒテ。Zustand(状態)+ Dichte(密度)" },
    { t: "Supraleitung", en: "超伝導", field: "ドイツ語・物理学", lv: 5, def: "ズープラライトゥング。supra-(超)+ Leitung(伝導)" },
    { t: "Erhaltungssatz", en: "保存則", field: "ドイツ語・物理学", lv: 4, def: "エアハルトゥングスザッツ。Erhaltung(保存)+ Satz(定理)" },
    { t: "Nullpunktsenergie", en: "零点エネルギー", field: "ドイツ語・物理学", lv: 5, def: "ヌルプンクツエネルギー" },
    { t: "Wirkungsquerschnitt", en: "断面積(反応断面積)", field: "ドイツ語・物理学", lv: 5, def: "ヴィルクングスクヴェアシュニット。Wirkung(作用)+ Querschnitt(断面)" },

    /* --- ドイツ語・化学 --- */
    { t: "Lösung", en: "溶液", field: "ドイツ語・化学", lv: 2, def: "レーズング。「解決・解」の意味もあり、数学では「解」を指す" },
    { t: "Stoff", en: "物質", field: "ドイツ語・化学", lv: 2, def: "シュトフ。Reinstoff で純物質、Gemisch が混合物" },
    { t: "Reaktionsgeschwindigkeit", en: "反応速度", field: "ドイツ語・化学", lv: 4, def: "レアクツィオーンスゲシュヴィンディヒカイト。長い複合語はドイツ語の特徴" },
    { t: "Oxidation / Reduktion", en: "酸化 / 還元", field: "ドイツ語・化学", lv: 3, def: "オクシダツィオーン / レドゥクツィオーン" },
    { t: "Säure / Base", en: "酸 / 塩基", field: "ドイツ語・化学", lv: 2, def: "ゾイレ / バーゼ" },
    { t: "Gleichgewicht", en: "平衡", field: "ドイツ語・化学", lv: 3, def: "グライヒゲヴィヒト。gleich(等しい)+ Gewicht(重さ)" },
    { t: "Katalysator", en: "触媒", field: "ドイツ語・化学", lv: 3, def: "カタリザートル" },
    { t: "Bindung", en: "結合", field: "ドイツ語・化学", lv: 3, def: "ビンドゥング。kovalente Bindung で共有結合" },
    { t: "Ausbeute", en: "収率", field: "ドイツ語・化学", lv: 4, def: "アウスボイテ。実験項でよく使う" },
    { t: "Siedepunkt", en: "沸点", field: "ドイツ語・化学", lv: 3, def: "ジーデプンクト。Schmelzpunkt が融点" },

    /* --- ドイツ語・薬学 --- */
    { t: "Arzneimittel", en: "医薬品", field: "ドイツ語・薬学", lv: 3, def: "アルツナイミッテル。Arznei(薬)+ Mittel(手段・剤)" },
    { t: "Wirkstoff", en: "有効成分", field: "ドイツ語・薬学", lv: 3, def: "ヴィルクシュトフ。Wirkung(作用)+ Stoff(物質)" },
    { t: "Nebenwirkung", en: "副作用", field: "ドイツ語・薬学", lv: 3, def: "ネーベンヴィルクング。neben(そばの)+ Wirkung(作用)" },
    { t: "Gegenanzeige", en: "禁忌", field: "ドイツ語・薬学", lv: 4, def: "ゲーゲンアンツァイゲ。gegen(反対)+ Anzeige(適応)" },
    { t: "Dosierung", en: "用法用量", field: "ドイツ語・薬学", lv: 3, def: "ドジールング" },
    { t: "Halbwertszeit", en: "半減期", field: "ドイツ語・薬学", lv: 3, def: "ハルプヴェルツツァイト。halb(半分)+ Wert(値)+ Zeit(時間)" },
    { t: "Verordnung", en: "処方", field: "ドイツ語・薬学", lv: 4, def: "フェアオルドヌング。「規則・法令」の意味もある" },
    { t: "Bioverfügbarkeit", en: "バイオアベイラビリティ", field: "ドイツ語・薬学", lv: 5, def: "ビオフェアフューグバーカイト。verfügbar(利用可能な)から" },
    { t: "Wechselwirkung", en: "相互作用", field: "ドイツ語・薬学", lv: 4, def: "ヴェクセルヴィルクング。物理でも「相互作用」に使う" },
    { t: "klinische Studie", en: "臨床試験", field: "ドイツ語・薬学", lv: 3, def: "クリーニシェ シュトゥーディエ" },

    /* --- ドイツ語・経済学 --- */
    { t: "Angebot und Nachfrage", en: "需要と供給", field: "ドイツ語・経済学", lv: 2, def: "アンゲボート ウント ナーハフラーゲ。供給が先に来る語順" },
    { t: "Grenzkosten", en: "限界費用", field: "ドイツ語・経済学", lv: 3, def: "グレンツコステン。Grenze(境界)+ Kosten(費用)" },
    { t: "Wertschöpfung", en: "付加価値", field: "ドイツ語・経済学", lv: 4, def: "ヴェルトシェプフング。Wert(価値)+ Schöpfung(創造)" },
    { t: "Arbeitslosigkeit", en: "失業", field: "ドイツ語・経済学", lv: 3, def: "アルバイツロージヒカイト。Arbeit(仕事)+ los(無い)" },
    { t: "Konjunktur", en: "景気", field: "ドイツ語・経済学", lv: 4, def: "コンユンクトゥーア。英語 conjuncture とは意味がずれる" },
    { t: "Zinssatz", en: "金利", field: "ドイツ語・経済学", lv: 3, def: "ツィンスザッツ。Zins(利子)+ Satz(率)" },
    { t: "Steuer", en: "税", field: "ドイツ語・経済学", lv: 2, def: "シュトイアー。「舵」の意味もある同綴りの語がある" },
    { t: "Ersparnis", en: "貯蓄", field: "ドイツ語・経済学", lv: 3, def: "エアシュパルニス。sparen(節約する)から" },
    { t: "Wettbewerb", en: "競争", field: "ドイツ語・経済学", lv: 3, def: "ヴェットベヴェルプ" },
    { t: "Geldpolitik", en: "金融政策", field: "ドイツ語・経済学", lv: 3, def: "ゲルトポリティーク。Geld(貨幣)+ Politik(政策)" },

    /* --- ドイツ語・情報科学 --- */
    { t: "Rechner", en: "計算機", field: "ドイツ語・情報科学", lv: 2, def: "レヒナー。rechnen(計算する)から。Computer も使う" },
    { t: "Speicher", en: "メモリ・記憶装置", field: "ドイツ語・情報科学", lv: 2, def: "シュパイヒャー。speichern(蓄える)から" },
    { t: "Datenbank", en: "データベース", field: "ドイツ語・情報科学", lv: 2, def: "ダーテンバンク" },
    { t: "Verschlüsselung", en: "暗号化", field: "ドイツ語・情報科学", lv: 4, def: "フェアシュリュッセルング。Schlüssel(鍵)から" },
    { t: "Schlüssel", en: "鍵", field: "ドイツ語・情報科学", lv: 3, def: "シュリュッセル。öffentlicher Schlüssel で公開鍵" },
    { t: "maschinelles Lernen", en: "機械学習", field: "ドイツ語・情報科学", lv: 3, def: "マシネレス レルネン" },
    { t: "neuronales Netz", en: "ニューラルネットワーク", field: "ドイツ語・情報科学", lv: 4, def: "ノイロナーレス ネッツ" },
    { t: "Rechenaufwand", en: "計算量", field: "ドイツ語・情報科学", lv: 4, def: "レッヒェンアウフヴァント。Aufwand は「手間・コスト」" },
    { t: "Betriebssystem", en: "オペレーティングシステム", field: "ドイツ語・情報科学", lv: 3, def: "ベトリープスジステーム。Betrieb(運転)+ System" },
    { t: "Datenschutz", en: "データ保護", field: "ドイツ語・情報科学", lv: 3, def: "ダーテンシュッツ。DSGVO(GDPR)の中心概念" },

    /* --- 中国語・数学 --- */
    { t: "导数", en: "導関数", field: "中国語・数学", lv: 3, def: "dǎoshù(ダオシュー)。「导」は導く" },
    { t: "积分", en: "積分", field: "中国語・数学", lv: 2, def: "jīfēn(ジーフェン)。日本語と同じ漢字の簡体字" },
    { t: "极限", en: "極限", field: "中国語・数学", lv: 2, def: "jíxiàn(ジーシエン)" },
    { t: "集合", en: "集合", field: "中国語・数学", lv: 2, def: "jíhé(ジーホー)。日本語と同じ語" },
    { t: "函数", en: "関数", field: "中国語・数学", lv: 2, def: "hánshù(ハンシュー)。日本語の「函数」の元の表記" },
    { t: "方程", en: "方程式", field: "中国語・数学", lv: 2, def: "fāngchéng(ファンチョン)。「方程式」ではなく「方程」で完結する" },
    { t: "矩阵", en: "行列", field: "中国語・数学", lv: 3, def: "jǔzhèn(ジュージェン)。日本語の「行列」とは字が違う" },
    { t: "概率", en: "確率", field: "中国語・数学", lv: 3, def: "gàilǜ(ガイリュー)。台湾では「機率」" },
    { t: "证明", en: "証明", field: "中国語・数学", lv: 2, def: "zhèngmíng(ジョンミン)" },
    { t: "定理", en: "定理", field: "中国語・数学", lv: 2, def: "dìnglǐ(ディンリー)。「引理」が補題" },
    { t: "特征值", en: "固有値", field: "中国語・数学", lv: 4, def: "tèzhēngzhí(トージョンジー)。「特徴の値」と表現する" },
    { t: "流形", en: "多様体", field: "中国語・数学", lv: 5, def: "liúxíng(リウシン)。manifold の訳語" },

    /* --- 中国語・物理学 --- */
    { t: "速度", en: "速度", field: "中国語・物理学", lv: 1, def: "sùdù(スードゥー)" },
    { t: "加速度", en: "加速度", field: "中国語・物理学", lv: 2, def: "jiāsùdù(ジアスードゥー)" },
    { t: "动量", en: "運動量", field: "中国語・物理学", lv: 3, def: "dòngliàng(ドンリアン)。「動く量」" },
    { t: "能量", en: "エネルギー", field: "中国語・物理学", lv: 1, def: "néngliàng(ノンリアン)。「能の量」" },
    { t: "波函数", en: "波動関数", field: "中国語・物理学", lv: 4, def: "bōhánshù(ボーハンシュー)" },
    { t: "超导", en: "超伝導", field: "中国語・物理学", lv: 4, def: "chāodǎo(チャオダオ)。「超导电性」の略" },
    { t: "守恒定律", en: "保存則", field: "中国語・物理学", lv: 3, def: "shǒuhéng dìnglǜ(ショウホン ディンリュー)。「守恒」が保存" },
    { t: "熵", en: "エントロピー", field: "中国語・物理学", lv: 4, def: "shāng(シャン)。熱(火)と商の会意で作られた一字の新造字" },
    { t: "电导率", en: "電気伝導率", field: "中国語・物理学", lv: 4, def: "diàndǎolǜ(ディエンダオリュー)" },
    { t: "跃迁", en: "遷移", field: "中国語・物理学", lv: 5, def: "yuèqiān(ユエチエン)。エネルギー準位間の transition" },

    /* --- 中国語・化学 --- */
    { t: "溶液", en: "溶液", field: "中国語・化学", lv: 2, def: "róngyè(ロンイエ)。日本語と同じ語" },
    { t: "物质", en: "物質", field: "中国語・化学", lv: 2, def: "wùzhì(ウージー)" },
    { t: "反应", en: "反応", field: "中国語・化学", lv: 1, def: "fǎnyìng(ファンイン)。日本語「反応」の簡体字" },
    { t: "氧化 / 还原", en: "酸化 / 還元", field: "中国語・化学", lv: 3, def: "yǎnghuà / huányuán。「酸化」ではなく「氧化」(氧=酸素)" },
    { t: "酸 / 碱", en: "酸 / 塩基", field: "中国語・化学", lv: 2, def: "suān / jiǎn。塩基は「碱」の一字" },
    { t: "催化剂", en: "触媒", field: "中国語・化学", lv: 3, def: "cuīhuàjì(ツイホアジー)。「催化」が触媒作用" },
    { t: "化合物", en: "化合物", field: "中国語・化学", lv: 2, def: "huàhéwù(ホアホーウー)" },
    { t: "平衡", en: "平衡", field: "中国語・化学", lv: 3, def: "pínghéng(ピンホン)" },
    { t: "共价键", en: "共有結合", field: "中国語・化学", lv: 4, def: "gòngjiàjiàn(ゴンジアジエン)。「键」が結合(bond)" },
    { t: "摩尔质量", en: "モル質量", field: "中国語・化学", lv: 3, def: "mó'ěr zhìliàng。「摩尔」は mole の音訳" },

    /* --- 中国語・薬学 --- */
    { t: "药物", en: "薬物", field: "中国語・薬学", lv: 2, def: "yàowù(ヤオウー)。「药」は「薬」の簡体字" },
    { t: "处方", en: "処方箋", field: "中国語・薬学", lv: 3, def: "chǔfāng(チューファン)。「处方药」で処方箋医薬品" },
    { t: "剂量", en: "用量", field: "中国語・薬学", lv: 3, def: "jìliàng(ジーリアン)。「剂」は剤" },
    { t: "半衰期", en: "半減期", field: "中国語・薬学", lv: 3, def: "bànshuāiqī(バンシュアイチー)。「衰える」で減衰を表す" },
    { t: "不良反应", en: "副作用", field: "中国語・薬学", lv: 3, def: "bùliáng fǎnyìng。「副作用」も使うが公式文書では「不良反应」" },
    { t: "禁忌症", en: "禁忌", field: "中国語・薬学", lv: 4, def: "jìnjìzhèng(ジンジージョン)" },
    { t: "生物利用度", en: "バイオアベイラビリティ", field: "中国語・薬学", lv: 4, def: "shēngwù lìyòngdù。「利用できる度合い」" },
    { t: "临床试验", en: "臨床試験", field: "中国語・薬学", lv: 3, def: "línchuáng shìyàn(リンチュアン シーイエン)" },
    { t: "抗生素", en: "抗生物質", field: "中国語・薬学", lv: 2, def: "kàngshēngsù(カンションスー)" },
    { t: "药代动力学", en: "薬物動態学", field: "中国語・薬学", lv: 5, def: "yàodài dònglìxué。「薬の代謝の動力学」" },

    /* --- 中国語・経済学 --- */
    { t: "需求 / 供给", en: "需要 / 供給", field: "中国語・経済学", lv: 2, def: "xūqiú / gōngjǐ。日本語の「需要」は中国語では「需求」" },
    { t: "边际成本", en: "限界費用", field: "中国語・経済学", lv: 3, def: "biānjì chéngběn。「边际」が marginal" },
    { t: "通货膨胀", en: "インフレーション", field: "中国語・経済学", lv: 3, def: "tōnghuò péngzhàng。「通貨が膨張する」" },
    { t: "失业率", en: "失業率", field: "中国語・経済学", lv: 2, def: "shīyèlǜ(シーイエリュー)" },
    { t: "利率", en: "金利", field: "中国語・経済学", lv: 2, def: "lìlǜ(リーリュー)" },
    { t: "增加值", en: "付加価値", field: "中国語・経済学", lv: 4, def: "zēngjiāzhí。「增值税」(付加価値税)の元" },
    { t: "均衡价格", en: "均衡価格", field: "中国語・経済学", lv: 3, def: "jūnhéng jiàgé" },
    { t: "货币政策", en: "金融政策", field: "中国語・経済学", lv: 3, def: "huòbì zhèngcè。「货币」が貨幣" },
    { t: "博弈论", en: "ゲーム理論", field: "中国語・経済学", lv: 4, def: "bóyìlùn(ボーイールン)。「博弈」は囲碁・賭け事" },
    { t: "计量经济学", en: "計量経済学", field: "中国語・経済学", lv: 4, def: "jìliàng jīngjìxué" },

    /* --- 中国語・情報科学 --- */
    { t: "计算机", en: "計算機(コンピュータ)", field: "中国語・情報科学", lv: 1, def: "jìsuànjī(ジースアンジー)。台湾では「電腦」" },
    { t: "算法", en: "アルゴリズム", field: "中国語・情報科学", lv: 2, def: "suànfǎ(スアンファー)。「計算の法」。日本語の「算法」とは指す範囲が違う" },
    { t: "数据", en: "データ", field: "中国語・情報科学", lv: 2, def: "shùjù(シュージュー)。「数据库」でデータベース" },
    { t: "内存", en: "メモリ", field: "中国語・情報科学", lv: 3, def: "nèicún(ネイツン)。「内部の記憶」" },
    { t: "网络", en: "ネットワーク", field: "中国語・情報科学", lv: 2, def: "wǎngluò(ワンルオ)。「网」は網" },
    { t: "程序", en: "プログラム", field: "中国語・情報科学", lv: 2, def: "chéngxù(チョンシュー)。日本語の「程序(順序)」とは意味が違う" },
    { t: "机器学习", en: "機械学習", field: "中国語・情報科学", lv: 3, def: "jīqì xuéxí(ジーチー シュエシー)" },
    { t: "神经网络", en: "ニューラルネットワーク", field: "中国語・情報科学", lv: 4, def: "shénjīng wǎngluò" },
    { t: "加密", en: "暗号化", field: "中国語・情報科学", lv: 3, def: "jiāmì(ジアミー)。「密を加える」。解密が復号" },
    { t: "密钥", en: "鍵(暗号鍵)", field: "中国語・情報科学", lv: 4, def: "mìyuè / mìyào。「公钥」が公開鍵、「私钥」が秘密鍵" },
    { t: "复杂度", en: "計算量(複雑度)", field: "中国語・情報科学", lv: 3, def: "fùzádù(フーザードゥー)。「时间复杂度」で時間計算量" },
    { t: "云计算", en: "クラウドコンピューティング", field: "中国語・情報科学", lv: 3, def: "yún jìsuàn。「云」は雲" }
  ];

  /* ============================== 適性設問 ============================== */
  var APTITUDE = [
    { q: "原語で論文を読むとしたら、どちらに惹かれますか。", opts: [
      { t: "ロシア語。数学・物理の古典的な文献が読みたい", w: { "ロシア語・数学": 2, "ロシア語・物理学": 2 } },
      { t: "フランス語。数学の術語の作り方に興味がある", w: { "フランス語・数学": 2.5 } },
      { t: "ロシア語。化学・薬学の実務文書を読みたい", w: { "ロシア語・化学": 2, "ロシア語・薬学": 1.5 } },
      { t: "フランス語。EU の規制文書や経済統計を読みたい", w: { "フランス語・薬学": 1.5, "フランス語・経済学": 2 } }
    ]},
    { q: "知らない外国語の専門語に出会ったとき、どうしますか。", opts: [
      { t: "接頭辞・語根に分けて意味を推測する", w: { "ロシア語・物理学": 2, "フランス語・化学": 1.5 } },
      { t: "英語の対応語を探して一対一で覚える", w: { "フランス語・数学": 2, "ロシア語・数学": 1.5 } },
      { t: "用例の文ごと覚える", w: { "フランス語・薬学": 2, "ロシア語・薬学": 1.5 } },
      { t: "定義を数式や図に置き換える", w: { "ロシア語・数学": 2.5 } }
    ]},
    { q: "空似言葉(形は似ているが意味が違う語)についてどう感じますか。", opts: [
      { t: "面白い。意味のずれ方に法則を探したい", w: { "フランス語・物理学": 2, "ロシア語・経済学": 1.5 } },
      { t: "危険だ。必ず辞書で確認する", w: { "フランス語・薬学": 2.5 } },
      { t: "文脈で判断できるので気にしない", w: { "ロシア語・化学": 2 } },
      { t: "定義が数式で書いてあれば問題ない", w: { "ロシア語・数学": 2, "フランス語・数学": 1 } }
    ]},
    { q: "キリル文字を見たときの感覚は？", opts: [
      { t: "読める。音を当てれば意味も見えてくる", w: { "ロシア語・物理学": 2.5, "ロシア語・数学": 1.5 } },
      { t: "図形として覚えれば怖くない", w: { "ロシア語・化学": 2.5 } },
      { t: "略号(ЛС, ВВП)から入るのが早い", w: { "ロシア語・薬学": 2, "ロシア語・経済学": 2 } },
      { t: "ラテン文字の言語のほうが取り組みやすい", w: { "フランス語・数学": 2, "フランス語・経済学": 1.5 } }
    ]},
    { q: "術語の名前の付け方で、興味があるのは？", opts: [
      { t: "意味をそのまま並べる作り方(quantité de mouvement)", w: { "フランス語・物理学": 3 } },
      { t: "接頭辞を重ねる作り方(сверхпроводимость)", w: { "ロシア語・物理学": 3 } },
      { t: "ラテン語から直訳する作り方(ч.т.д. / C.Q.F.D.)", w: { "ロシア語・数学": 1.5, "フランス語・数学": 1.5 } },
      { t: "制度の名前がそのまま術語になる作り方(AMM, ЖНВЛП)", w: { "フランス語・薬学": 2, "ロシア語・薬学": 2 } }
    ]},
    { q: "薬の文書を原語で読むとしたら、まず知りたい語は？", opts: [
      { t: "禁忌と副作用", w: { "フランス語・薬学": 2.5, "ロシア語・薬学": 1.5 } },
      { t: "用法用量と投与経路", w: { "ロシア語・薬学": 2.5, "フランス語・薬学": 1 } },
      { t: "有効成分と添加剤", w: { "フランス語・薬学": 2, "ロシア語・化学": 1 } },
      { t: "承認と規制の枠組み", w: { "フランス語・薬学": 2, "ロシア語・経済学": 1 } }
    ]},
    { q: "経済統計を原語で見るとき、気になるのは？", opts: [
      { t: "指標の定義(何を数えているか)", w: { "フランス語・経済学": 2.5 } },
      { t: "発表機関と一次資料", w: { "フランス語・経済学": 2, "ロシア語・経済学": 1 } },
      { t: "政策の名前と制度の略号", w: { "ロシア語・経済学": 2.5 } },
      { t: "他国と比較できる形になっているか", w: { "ロシア語・経済学": 1.5, "フランス語・経済学": 1.5 } }
    ]},
    { q: "化学の実験手順書を原語で読むなら？", opts: [
      { t: "条件(温度・圧力・標準状態)の表記から入る", w: { "ロシア語・化学": 2.5 } },
      { t: "操作の動詞(溶かす・還流する)から入る", w: { "フランス語・化学": 2.5 } },
      { t: "物質名と命名法から入る", w: { "フランス語・化学": 2, "ロシア語・化学": 1 } },
      { t: "図表の見出しから入る", w: { "ロシア語・物理学": 1.5, "フランス語・物理学": 1.5 } }
    ]},
    { q: "同じ概念に言語ごとに別の名前が付いていることを知ったら？", opts: [
      { t: "どちらの発想が自然かを比べたい", w: { "フランス語・数学": 2.5 } },
      { t: "歴史的にどちらが先かを調べたい", w: { "ロシア語・数学": 2, "フランス語・物理学": 1 } },
      { t: "実務で通じるほうを覚えれば十分", w: { "ロシア語・薬学": 2 } },
      { t: "両方覚えて対応表を作りたい", w: { "ロシア語・経済学": 1.5, "フランス語・経済学": 1.5 } }
    ]},
    { q: "英語をそのまま借りるか、自国語で作り直すか。", opts: [
      { t: "自国語で作り直したい(ordinateur, logiciel, courriel)", w: { "フランス語・情報科学": 3 } },
      { t: "借用でよい(компьютер, файл, сервер)", w: { "ロシア語・情報科学": 2.5 } },
      { t: "分野の慣例に従う", w: { "ロシア語・薬学": 1.5, "フランス語・薬学": 1.5 } },
      { t: "訳語の作られ方そのものに興味がある", w: { "フランス語・情報科学": 1.5, "ロシア語・情報科学": 1.5 } }
    ]},
    { q: "技術文書を原語で読むなら、どこから入りますか。", opts: [
      { t: "略号(ЭВМ, ОС, БД / TIC, SGBD, IA)から", w: { "ロシア語・情報科学": 2.5 } },
      { t: "頻出する動詞と操作の語から", w: { "フランス語・情報科学": 2.5 } },
      { t: "図表とコード例から", w: { "ロシア語・物理学": 1.5, "フランス語・物理学": 1.5 } },
      { t: "用語集を先に作ってから", w: { "フランス語・情報科学": 1.5, "ロシア語・情報科学": 1.5 } }
    ]},
    { q: "長い複合語(Energieerhaltungssatz)を見たときの感覚は？", opts: [
      { t: "分解すれば意味が読める。むしろ分かりやすい", w: { "ドイツ語・物理学": 2.5, "ドイツ語・化学": 1 } },
      { t: "定義がそのまま語になっていて気持ちがよい", w: { "ドイツ語・数学": 2.5 } },
      { t: "長すぎる。略号のほうがよい", w: { "ロシア語・情報科学": 1.5, "フランス語・情報科学": 1.5 } },
      { t: "薬や制度の名前もこの形で覚えたい", w: { "ドイツ語・薬学": 2, "ドイツ語・経済学": 1.5 } }
    ]},
    { q: "漢字で書かれた術語(函数・矩阵・熵・算法)はどうですか。", opts: [
      { t: "字から意味が推測できて読みやすい", w: { "中国語・数学": 2.5 } },
      { t: "日本語と字が違う点が面白い", w: { "中国語・化学": 2, "中国語・情報科学": 1.5 } },
      { t: "一字の新造字(熵)に驚く", w: { "中国語・物理学": 2.5 } },
      { t: "読み(ピンイン)も一緒に覚えたい", w: { "中国語・薬学": 1.5, "中国語・経済学": 1.5 } }
    ]},
    { q: "外国語の専門語を覚えるとき、効くと感じるのは？", opts: [
      { t: "音読して音で覚える", w: { "ロシア語・物理学": 2 } },
      { t: "語形の規則(taux de …, уровень …)で束にする", w: { "フランス語・経済学": 2, "ロシア語・経済学": 1.5 } },
      { t: "対訳カードで一対一に覚える", w: { "フランス語・化学": 2 } },
      { t: "実際の文書を読み流して慣れる", w: { "フランス語・薬学": 1.5, "ロシア語・薬学": 1.5 } }
    ]}
  ];

  /* ============================== 分野プロファイル ============================== */
  function prof(tag, think, eqs, syms, near, next) {
    return { tag: tag, think: think, eqs: eqs, syms: syms, near: near, next: next };
  }
  var FIELD_PROFILE = {
    "ロシア語・数学": prof(
      "ロシア語で書かれた数学の語彙と論証の型",
      "ラテン語由来の定型をロシア語に直訳した言い回しが多く、語根から意味を組み立てられる。",
      "ч.т.д. · тогда и только тогда · необходимо и достаточно",
      "ч.т.д. и т.д. т.е. т.к. см. ур-ние ф-ла",
      ["ロシア語・物理学", "フランス語・数学"],
      "略号と定型句 → 解析の基本語彙(предел・производная) → 定理の述べ方"),
    "ロシア語・物理学": prof(
      "ロシア語で書かれた物理の語彙",
      "接頭辞(сверх-, у-, про-)を重ねて概念を作るため、語形から意味が読める。",
      "закон сохранения энергии · импульс · волновая функция",
      "рис. табл. н.у.",
      ["ロシア語・数学", "ロシア語・化学"],
      "力学の基本語 → 保存則の言い回し → 固体物理(сверхпроводимость)"),
    "ロシア語・化学": prof(
      "ロシア語で書かれた化学の語彙",
      "実験条件と操作の語彙が中心。溶液(раствор)と解(решение)のように英語の一語が別語に分かれる。",
      "скорость реакции · окисление / восстановление · равновесие",
      "р-р в-во т. пл. н.у.",
      ["ロシア語・物理学", "ロシア語・薬学"],
      "物質と操作の語 → 反応の語彙 → 実験項の読み方"),
    "ロシア語・薬学": prof(
      "ロシア語で書かれた薬学・規制の語彙",
      "против-(反対)や полу-(半分)など接頭辞で概念が対になる。制度の略号が多い。",
      "период полувыведения · побочное действие · противопоказание",
      "ЛС ЖНВЛП",
      ["ロシア語・化学", "フランス語・薬学"],
      "薬の基本語 → 薬物動態の語 → 添付文書と規制文書"),
    "ロシア語・経済学": prof(
      "ロシア語で書かれた経済の語彙",
      "уровень + 名詞で「〜率」を作るなど、語形の型で語彙が広がる。",
      "спрос и предложение · уровень инфляции · равновесная цена",
      "ВВП ЦБ РФ МРОТ",
      ["フランス語・経済学", "ロシア語・数学"],
      "需給の語 → 指標名と略号 → 統計資料の読み方"),
    "ロシア語・情報科学": prof(
      "ロシア語で書かれた情報科学の語彙",
      "英語からの借用(файл, сервер, компьютер)と、自国語の複合語(вычислительная машина)が併存する。",
      "вычислительная сложность · машинное обучение · открытый ключ / закрытый ключ",
      "ЭВМ ОС БД ПО ИИ СУБД",
      ["ロシア語・数学", "フランス語・情報科学"],
      "略号と基本語 → アルゴリズムと データ構造の語 → 機械学習・暗号の語彙"),
    "フランス語・情報科学": prof(
      "フランス語で書かれた情報科学の語彙",
      "英語を避けて自国語で作った造語(ordinateur, logiciel, courriel, infonuagique)が公用語として使われる。",
      "complexité algorithmique · apprentissage automatique · traitement du signal",
      "TIC SGBD IA RGPD Ko/Mo/Go MAJ",
      ["フランス語・数学", "ロシア語・情報科学"],
      "造語された基本語 → アルゴリズムと データの語 → 機械学習・規制(RGPD)の語彙"),
    "フランス語・数学": prof(
      "フランス語で書かれた数学の語彙と論証の型",
      "corps(体)・anneau(環)のように日常語をそのまま構造名にする。定型句が論証の骨格を作る。",
      "C.Q.F.D. · si et seulement si · il suffit de montrer que",
      "ssi c.-à-d. p. ex. d'où cf.",
      ["フランス語・物理学", "ロシア語・数学"],
      "定型句 → 代数の構造名(groupe/anneau/corps) → 解析の語彙"),
    "フランス語・物理学": prof(
      "フランス語で書かれた物理の語彙",
      "意味をそのまま並べた複合語(quantité de mouvement)が多く、直訳で理解できる。",
      "loi de conservation de l'énergie · quantité de mouvement",
      "fig. tab. S.I.",
      ["フランス語・化学", "フランス語・数学"],
      "力学の語 → 場と波の語彙 → 単位系(S.I.)の記述"),
    "フランス語・化学": prof(
      "フランス語で書かれた化学の語彙",
      "liaison … / point de … のような型で語彙が体系的に並ぶ。",
      "vitesse de réaction · liaison covalente · oxydoréduction",
      "T.P. C.N.T.P. p.f.",
      ["フランス語・物理学", "フランス語・薬学"],
      "物質と結合の語 → 反応と平衡 → 実験実習(T.P.)の記述"),
    "フランス語・薬学": prof(
      "フランス語で書かれた薬学・規制の語彙",
      "contre-(反対)や demi-(半分)など接頭辞で対になる語が多い。EU 規制の公式表現が使われる。",
      "demi-vie plasmatique · effet indésirable · posologie",
      "AMM DCI",
      ["フランス語・化学", "ロシア語・薬学"],
      "薬の基本語 → 薬物動態の語 → 承認文書(AMM/DCI)の語彙"),
    "ドイツ語・数学": prof(
      "ドイツ語で書かれた数学の語彙と論証の型",
      "Körper(体)・Ring(環)・Menge(集合)のように日常語をそのまま構造名にし、複合語で概念を組み立てる。",
      "was zu beweisen war · genau dann, wenn · ohne Beschränkung der Allgemeinheit",
      "q.e.d./w.z.b.w. o.B.d.A. d.h. z.B. vgl. bzw.",
      ["ドイツ語・物理学", "フランス語・数学"],
      "定型句 → 代数の構造名(Gruppe/Ring/Körper) → Ansatz・Eigenwert など輸出された語"),
    "ドイツ語・物理学": prof(
      "ドイツ語で書かれた物理の語彙",
      "Erhaltungssatz(保存則)のように、概念の構造がそのまま複合語の長さになる。",
      "Energieerhaltungssatz · Wellenfunktion · Wirkungsquerschnitt",
      "Abb. Tab. Bd.",
      ["ドイツ語・化学", "ドイツ語・数学"],
      "力学の基本語 → 保存則の言い回し → 量子・固体物理(Supraleitung)"),
    "ドイツ語・化学": prof(
      "ドイツ語で書かれた化学の語彙",
      "Stoff(物質)を核に複合語を作る。Lösung が「溶液」と「解」を兼ねる点に注意する。",
      "wässrige Lösung · Reaktionsgeschwindigkeit · Gleichgewicht",
      "Smp. Sdp. Lsg.",
      ["ドイツ語・物理学", "ドイツ語・薬学"],
      "物質と操作の語 → 反応と平衡 → 実験項(Ausbeute)の記述"),
    "ドイツ語・薬学": prof(
      "ドイツ語で書かれた薬学の語彙",
      "Wirkung(作用)を核に、Neben-(副)・Gegen-(反対)などの接頭辞で概念が対になる。",
      "Halbwertszeit · Nebenwirkung · Gegenanzeige · Bioverfügbarkeit",
      "AM NW",
      ["ドイツ語・化学", "フランス語・薬学"],
      "薬の基本語 → 薬物動態の語 → 添付文書(Fachinformation)の語彙"),
    "ドイツ語・経済学": prof(
      "ドイツ語で書かれた経済の語彙",
      "Grenz-(限界)や -satz(率)など、部品の組み合わせで術語が体系的に並ぶ。",
      "Angebot und Nachfrage · Grenzkosten · Wertschöpfung",
      "BIP MwSt. EZB",
      ["フランス語・経済学", "ドイツ語・数学"],
      "需給の語 → 指標名(BIP, Zinssatz) → 政策文書(EZB)の語彙"),
    "ドイツ語・情報科学": prof(
      "ドイツ語で書かれた情報科学の語彙",
      "Rechner・Speicher・Datenbank のように、英語を自国語に置き換えた語が定着している。",
      "maschinelles Lernen · Verschlüsselung · Rechenaufwand",
      "KI DSGVO EDV",
      ["ドイツ語・数学", "中国語・情報科学"],
      "基本語 → アルゴリズムとデータの語 → 機械学習・データ保護(DSGVO)"),
    "中国語・数学": prof(
      "中国語で書かれた数学の語彙",
      "漢字から意味が読めるが、函数・矩阵・概率のように日本語と字が違うものが多い。",
      "当且仅当 · 证明完毕(证毕)",
      "证毕 即 例如 参见",
      ["中国語・情報科学", "中国語・物理学"],
      "日本語と字が違う語 → 定型句 → 解析・代数の語彙(流形など)"),
    "中国語・物理学": prof(
      "中国語で書かれた物理の語彙",
      "守恒(保存)・跃迁(遷移)のように、動きを表す漢字で概念を作る。熵のような新造字もある。",
      "能量守恒定律 · 波函数 · 超导",
      "图 表",
      ["中国語・化学", "中国語・数学"],
      "力学の語 → 保存則 → 量子・固体物理(超导)"),
    "中国語・化学": prof(
      "中国語で書かれた化学の語彙",
      "氧(酸素)・碱(塩基)・键(結合)など、日本語と字が違う基本語をまず押さえる。",
      "氧化还原反应 · 共价键 · 摩尔质量",
      "标准状况 熔点 沸点",
      ["中国語・物理学", "中国語・薬学"],
      "元素と基本語 → 反応と平衡 → 有機化学の命名"),
    "中国語・薬学": prof(
      "中国語で書かれた薬学の語彙",
      "药(薬)を核に、不良反应・禁忌症のように公式文書の言い回しが決まっている。",
      "半衰期 · 不良反应 · 生物利用度 · 药代动力学",
      "国药准字 不良反应",
      ["中国語・化学", "ドイツ語・薬学"],
      "薬の基本語 → 薬物動態の語 → 説明書(说明书)の読み方"),
    "中国語・経済学": prof(
      "中国語で書かれた経済の語彙",
      "「〜率」「〜政策」の型で語彙が束になる。需求・供给のように日本語と字が違う語に注意する。",
      "通货膨胀率 · 均衡价格 · 货币政策",
      "国内生产总值 增值税",
      ["中国語・情報科学", "フランス語・経済学"],
      "需給の語 → 指標名 → 統計・政策文書の語彙"),
    "中国語・情報科学": prof(
      "中国語で書かれた情報科学の語彙",
      "音訳を避け、算法・程序・网络・密钥のように意味で訳した語が使われる。",
      "时间复杂度 · 机器学习 · 加密 / 解密",
      "人工智能 操作系统",
      ["中国語・数学", "ドイツ語・情報科学"],
      "基本語(计算机・程序) → アルゴリズムとデータ → 機械学習・暗号"),
    "フランス語・経済学": prof(
      "フランス語で書かれた経済の語彙",
      "taux de … の型で率を表すなど、語形の規則で語彙が束になる。付加価値税など制度語の原語でもある。",
      "offre et demande · taux de chômage · valeur ajoutée",
      "PIB SMIC INSEE TVA",
      ["ロシア語・経済学", "フランス語・薬学"],
      "需給の語 → 指標名(taux de …) → 統計機関の資料")
  };

  var API = { FIELDS: FIELDS, SYMBOLS: SYMBOLS, CTX: CTX, EQUATIONS: EQUATIONS,
              ASSOC: ASSOC, TERMS: TERMS, APTITUDE: APTITUDE, FIELD_PROFILE: FIELD_PROFILE,
              SUBJECT_OF: SUBJECT_OF, LANG_OF: LANG_OF,
              LABELS: {
                p1: "第一次検査 — 原語の表記",
                p2: "第二次検査 — 定型表現の対訳",
                symMean: "この論文中の略号・表記は何を意味しますか。",
                symField: "この表記(%ja%)が使われるのは、どの言語のどの分野ですか。",
                ctx: "<b>%field%</b> の文献でこの語が現れたとき、最も自然な訳はどれですか。",
                eqMean: "この原語の表現は何を意味しますか。",
                eqName: "この表現の日本語名はどれですか。",
                assoc: "この言い方にあたる原語の表現はどれですか。",
                assocRev: "この原語の表現に対応する、日本語での言い方はどれですか。",
                flashSym: "いま一瞬だけ表示された略号・表記は、次のどれですか。",
                flashTerm: "いま一瞬だけ表示された原語の専門用語は、次のどれですか。",
                flashTermMean: "いま表示された原語の用語のうち 1 つの意味が下にあります。正しい説明はどれですか。",
                flashEq: "いま<b>バラバラに散らして</b>表示されたのは、どの表現の断片ですか。",
                kindSym: "略号・表記の意味", kindSymField: "表記の言語と分野", kindCtx: "空似言葉・多義語",
                kindEqMean: "原語表現の意味", kindEqName: "原語表現の同定",
                kindAssoc: "連想(日本語→原語)", kindAssocRev: "連想(原語→日本語)",
                kindFlashSym: "瞬読(原語の表記)", kindFlashEq: "瞬読(原語表現バラバラ)"
              } };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.MultiLingBank = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
