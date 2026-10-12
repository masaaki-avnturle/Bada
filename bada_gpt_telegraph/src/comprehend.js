/*
 * comprehend.js — BadaGPT電信の「全体把握」
 *
 * 依頼文 (思考入力) を文 → 節に分け、すべての節を仕様の要素
 * (モジュール / 対象データ / 項目 / 機能 / 見た目 / 対象プラットフォーム /
 *  題名 / 目的) のどれかへ対応付ける。対応付けられなかった節は「未解釈」として
 * 残し、網羅率 (coverage) と一緒に仕様・論文に明記する。
 * 何も読み取れない部分を黙って捨てないことが「全体を捉える」ことの定義。
 */
"use strict";

/* ── モジュール辞書: 依頼文中の語 → 生成するアプリ部品 ── */
var MODULE_DEFS = [
  { id: "budget",    label: "家計簿",         icon: "💴", kw: ["家計簿", "支出", "収入", "出費", "お小遣い", "おこづかい", "残高", "レシート", "家計", "budget", "expense", "income"] },
  { id: "todo",      label: "ToDo",           icon: "✅", kw: ["todo", "to-do", "タスク", "やること", "やる事", "チェックリスト", "課題", "締め切り", "締切", "予定"] },
  { id: "notes",     label: "メモ",           icon: "📝", kw: ["メモ帳", "メモ", "ノート", "日記", "日誌", "アイデア", "note", "diary", "journal"] },
  { id: "timer",     label: "タイマー",       icon: "⏱", kw: ["タイマー", "ストップウォッチ", "ポモドーロ", "時間を計", "時間をはか", "時間を測", "カウントダウン", "timer", "stopwatch", "pomodoro"] },
  { id: "calc",      label: "電卓",           icon: "🧮", kw: ["電卓", "計算機", "計算", "四則", "calculator"] },
  { id: "counter",   label: "カウンター",     icon: "🔢", kw: ["カウンター", "数を数", "数える", "人数", "回数を数", "counter", "tally"] },
  { id: "quiz",      label: "クイズ",         icon: "🎓", kw: ["クイズ", "問題集", "暗記", "単語帳", "フラッシュカード", "学習カード", "quiz", "flashcard"] },
  { id: "draw",      label: "お絵かき",       icon: "🎨", kw: ["お絵かき", "お絵描き", "絵を描", "描画", "ペイント", "スケッチ", "手書き", "draw", "paint"] },
  { id: "convert",   label: "単位変換",       icon: "📐", kw: ["単位変換", "換算", "単位", "摂氏", "華氏", "converter"] },
  { id: "random",    label: "抽選",           icon: "🎲", kw: ["サイコロ", "ダイス", "くじ", "抽選", "ルーレット", "ランダム", "じゃんけん", "dice", "random", "lottery"] },
  { id: "habit",     label: "習慣",           icon: "📅", kw: ["習慣", "日課", "継続", "毎日続", "habit", "streak"] },
  { id: "telegraph", label: "電信",           icon: "📡", kw: ["電信", "モールス", "telegraph", "morse"] },
  { id: "quantum",   label: "量子回路",       icon: "⚛", kw: ["量子", "キュービット", "qubit", "ベル状態", "もつれ", "quantum"] }
];

/* 「◯◯を管理」等から取り出した対象が、既存モジュールを指す場合の対応 */
var ENTITY_TO_MODULE = [
  [/タスク|やること|課題|締め切り|締切|予定|チェックリスト|todo/i, "todo"], [/メモ|ノート|日記|アイデア/, "notes"], [/家計|支出|収入|出費|お金|小遣い/, "budget"],
  [/習慣|日課/, "habit"], [/単語|問題/, "quiz"]
];

/* 記録・管理 (CRUD) を呼び出す語 */
var RECORD_VERBS = "管理|記録|登録|整理|一覧|保存|蓄積|追跡";
var RECORD_NOUNS = ["台帳", "名簿", "在庫", "蔵書", "コレクション", "データベース", "リスト", "一覧", "database", "inventory", "tracker"];

/* 対象ごとの既定の項目 (依頼文に項目がないとき) */
var ENTITY_FIELDS = [
  [/本|書籍|蔵書|読書|book/i,          ["タイトル", "著者", "読了日", "評価", "感想"]],
  [/映画|ドラマ|アニメ|movie/i,         ["タイトル", "監督", "鑑賞日", "評価", "感想"]],
  [/顧客|お客|取引先|連絡先|名簿|customer|contact/i, ["名前", "会社", "電話", "メール", "メモ"]],
  [/在庫|商品|備品|部品|inventory|stock/i, ["品名", "数量", "単価", "保管場所"]],
  [/薬|服薬|medicine/i,                 ["薬名", "服用量", "服用日", "メモ"]],
  [/体重|健康|運動|ランニング|筋トレ|workout/i, ["日付", "体重", "運動時間", "メモ"]],
  [/レシピ|料理|recipe/i,               ["料理名", "材料", "手順", "調理時間"]],
  [/ワイン|お酒|コーヒー|wine|coffee/i,  ["銘柄", "産地", "購入日", "評価", "メモ"]],
  [/植物|ペット|水やり/,                 ["名前", "前回のお世話", "次回予定", "メモ"]]
];

var FEATURE_DEFS = [
  { id: "search", label: "検索・絞り込み",   kw: ["検索", "探せ", "探す", "絞り込", "フィルタ", "search", "filter"] },
  { id: "sort",   label: "並べ替え",         kw: ["並べ替", "並び替", "ソート", "順番", "sort"] },
  { id: "export", label: "CSV 書き出し / JSON バックアップ", kw: ["csv", "エクスポート", "書き出", "バックアップ", "export", "backup", "エクセル", "excel"] },
  { id: "chart",  label: "グラフ・集計",     kw: ["グラフ", "チャート", "集計", "統計", "可視化", "合計", "chart", "graph"] },
  { id: "sound",  label: "音・アラーム",     kw: ["アラーム", "サウンド", "通知音", "ベル", "鳴ら", "beep", "sound", "音で"] },
  { id: "print",  label: "印刷",             kw: ["印刷", "プリント", "print", "pdf"] }
];

var COLOR_DEFS = [
  [/水色|シアン|cyan/i, "#3cc8e0", "水色"], [/青|ブルー|blue/i, "#4f8cff", "青"], [/赤|レッド|red/i, "#ff5a5a", "赤"],
  [/緑|グリーン|green/i, "#3ccf7a", "緑"], [/紫|パープル|purple/i, "#a77bff", "紫"], [/ピンク|桃色|pink/i, "#ff6fb1", "ピンク"],
  [/オレンジ|橙|orange/i, "#ff9a3c", "オレンジ"], [/黄|イエロー|yellow/i, "#f5c542", "黄"], [/金色|ゴールド|gold/i, "#e8b84a", "金"]
];

var PLATFORM_DEFS = [
  { id: "android", label: "Android (APK)",       kw: ["android", "アンドロイド", "apk", "スマホ", "スマートフォン", "携帯", "タブレット"] },
  { id: "windows", label: "Windows 10 / 11 (EXE)", kw: ["windows", "ウィンドウズ", "ウインドウズ", "exe", "パソコン", "pc"] },
  { id: "linux",   label: "Linux (AppImage / deb)", kw: ["linux", "リナックス", "ubuntu", "ウブントゥ", "appimage", "deb"] }
];

/* 作成依頼の定型句 (意図は「アプリを作ってほしい」) */
var REQUEST_PHRASES = /アプリ|ツール|ソフト|作って|作りたい|作成|欲しい|ほしい|お願い|ください|下さい|したい|たい$|make|build|create|want|please|app/i;

var KANJI_KATA_RUN = /[一-龠々〆ヵヶァ-ヴーA-Za-z0-9_]+$/;

function lower(s) { return String(s || "").toLowerCase(); }
function hasAny(text, kws) {
  var t = lower(text);
  for (var i = 0; i < kws.length; i++) if (t.indexOf(lower(kws[i])) >= 0) return kws[i];
  return null;
}

/* 文 → 節 (、で区切る。ただし項目の列挙は 1 節として扱う) */
function splitClauses(text) {
  var sentences = String(text || "").replace(/\r\n?/g, "\n")
    .split(/[。．！!？?\n]+/).map(function (s) { return s.trim(); }).filter(Boolean);
  var clauses = [];
  sentences.forEach(function (s) {
    if (isFieldList(s)) { clauses.push(s); return; }
    s.split(/[、，,]\s*/).map(function (c) { return c.trim(); }).filter(function (c) { return c.length >= 2; })
      .forEach(function (c) { clauses.push(c); });
  });
  return clauses;
}

function isFieldList(s) {
  if (/項目|フィールド|カラム|入力欄|列は|記録するのは|fields?\s*[:：]/i.test(s)) return true;
  if (/\w+:(string|text|integer|int|number|float|date|boolean|bool)\b/i.test(s)) return true;
  var seps = (s.match(/[、・，,]/g) || []).length;
  if (seps >= 2 && new RegExp("(を|の)(" + RECORD_VERBS + "|入力|メモ)").test(s)) return true;
  /* 名詞だけを並べた文: 「日付、体重、運動時間、メモ」 */
  var parts = s.split(/[、・，,]/).map(function (x) { return x.trim(); });
  return seps >= 2 && parts.every(function (x) { return /^[一-龠々〆ヵヶァ-ヴーA-Za-z0-9_ ]{1,10}$/.test(x); });
}

/* 名詞の末尾 (漢字・カタカナ・英数字の連続) を取り出す: 「読んだ本」→「本」 */
function nounTail(s) {
  var m = String(s).replace(/(など|とか|等|も|は|が|を|に|の|で|と)$/, "").match(KANJI_KATA_RUN);
  return m ? m[0] : "";
}

var FIELD_STOP = /^(アプリ|機能|画面|ボタン|データ|もの|こと|ため|よう|管理|記録|登録|入力|保存|一覧|項目|フィールド|カラム|情報)$/;

function fieldType(name) {
  if (/日付|日時|期限|締切|締め切り|誕生日|日$|date|day/i.test(name)) return "date";
  if (/評価|スコア|点数|星|rating|score/i.test(name)) return "rating";
  if (/金額|価格|値段|単価|料金|円|費|数量|個数|数$|量$|年齢|回数|時間|距離|体重|身長|kg|cm|price|amount|count|qty|age|weight/i.test(name)) return "number";
  if (/済|完了|有無|フラグ|done|flag/i.test(name)) return "bool";
  if (/メモ|説明|内容|本文|感想|備考|コメント|手順|材料|note|memo|description|comment/i.test(name)) return "text";
  return "string";
}

function extractFields(text) {
  var fields = [], seen = {};
  function add(name, type) {
    name = String(name).trim();
    if (!name || name.length > 14 || FIELD_STOP.test(name) || seen[name]) return;
    seen[name] = true;
    fields.push({ name: name, type: type || fieldType(name) });
  }
  /* Rails 形式: title:string price:integer */
  var re = /([A-Za-z_][A-Za-z0-9_]*):(string|text|integer|int|number|float|date|boolean|bool)\b/gi, m;
  var railsMap = { string: "string", text: "text", integer: "number", int: "number", number: "number", float: "number", date: "date", boolean: "bool", bool: "bool" };
  while ((m = re.exec(text))) add(m[1], railsMap[m[2].toLowerCase()]);
  /* 日本語の列挙: 「項目は A、B、C」「A・B・C を記録」 */
  String(text).split(/[。．！!？?\n]+/).forEach(function (s) {
    if (!isFieldList(s)) return;
    var body = s;
    var after = s.match(/(?:項目|フィールド|カラム|入力欄|列|記録するの)(?:は|：|:)\s*(.+)$/);
    if (after) body = after[1];
    else {
      var before = s.match(new RegExp("^(.*?)(?:を|の)(?:" + RECORD_VERBS + "|入力|メモ)"));
      if (before) body = before[1];
    }
    body = body.replace(/(など|とか|等)(を|の)?.*$/, "").replace(/(を|の)(記録|登録|入力|管理|保存).*$/, "");
    body.split(/[、・，,／\/]|(?<=[一-龠々ァ-ヴーA-Za-z0-9])と(?=[一-龠々ァ-ヴーA-Za-z0-9])/).forEach(function (part) {
      var n = nounTail(part.trim());
      if (n && part.indexOf(":") < 0) add(n);
    });
  });
  return fields;
}

function extractEntity(text, fields) {
  var isField = {};
  (fields || []).forEach(function (f) { isField[f.name] = true; });
  var m, best = "";
  /* Rails 形式: 「Book title:string ...」の先頭のモデル名 */
  m = String(text).match(/(?:^|\s)([A-Z][A-Za-z0-9]*)\s+[A-Za-z_]\w*:(?:string|text|integer|int|number|float|date|boolean|bool)\b/);
  if (m) return m[1];
  /* 項目の列挙文: 「ワインの銘柄・産地・評価を記録」→「ワイン」 */
  String(text).split(/[。．！!？?\n]+/).forEach(function (s) {
    if (best || !isFieldList(s)) return;
    var h = s.match(/^\s*([^、・，,「」\s]+?)の/);
    if (h) { var hn = nounTail(h[1]); if (hn && !isField[hn] && !FIELD_STOP.test(hn)) best = hn; }
  });
  if (best) return best;
  /* 複合名詞: 「映画の鑑賞記録」「家族の予定管理」→「映画」「家族」 */
  m = String(text).match(/([^、。\s「」]+?)の[一-龠々ァ-ヴー]{1,6}(?:記録|管理|リスト|一覧|台帳|日誌)/);
  if (m) { var cn = nounTail(m[1]); if (cn && cn.length <= 10 && !FIELD_STOP.test(cn) && !isField[cn]) return cn; }
  var re = new RegExp("([^、。\\s「」]+?)(?:を|の)(?:" + RECORD_VERBS + ")", "g");
  while ((m = re.exec(text))) {
    var n = nounTail(m[1]);
    if (n && n.length <= 10 && !FIELD_STOP.test(n) && !isField[n]) { best = n; break; }
  }
  if (!best) {
    for (var i = 0; i < RECORD_NOUNS.length; i++) {
      var k = String(text).indexOf(RECORD_NOUNS[i]);
      if (k > 0) { var t = nounTail(String(text).slice(0, k + RECORD_NOUNS[i].length)); if (t) { best = t; break; } }
    }
  }
  return best;
}

function extractTitle(text) {
  var m = String(text).match(/[「『]([^」』]{1,30})[」』]\s*(?:という|って|と言う|の名前|という名前|のアプリ|アプリ)/) ||
          String(text).match(/(?:名前|タイトル|題名|アプリ名)(?:は|を|：|:)\s*[「『]?([^」』、。]{1,30})/) ||
          String(text).match(/[「『]([^」』]{1,30})[」』]/);
  return m ? m[1].trim() : "";
}

function extractPurpose(clauses) {
  for (var i = 0; i < clauses.length; i++) {
    if (/ため|ように|向け|用に|したい|たい$|ほしい|欲しい|便利/.test(clauses[i])) return clauses[i];
  }
  return clauses[0] || "";
}

/* 依頼文 → 仕様 (spec) */
function comprehend(input, opts) {
  opts = opts || {};
  var text = String(input || "").trim();
  var clauses = splitClauses(text);
  var spec = {
    version: BGT_VERSION, input: text, title: "", purpose: "", modules: [], entity: "", fields: [],
    features: {}, theme: { mode: "dark", accent: "#8fd0ff", accentName: "" }, platforms: [],
    clauses: [], coverage: 0, assumptions: [], unresolved: []
  };
  var t = lower(text);
  /* 項目の列挙文 (「名前、メモ、日付を記録」) の語でモジュールを呼ばないよう除いた本文 */
  var tMods = lower(String(text).replace(/[「『][^」』]*[」』]/g, "").split(/[。．！!？?\n]+/)
    .filter(function (s) { return !isFieldList(s); }).join("。"));

  /* モジュール */
  var picked = {};
  function pick(id, why) {
    if (picked[id]) return;
    var def = MODULE_DEFS.filter(function (d) { return d.id === id; })[0];
    picked[id] = true;
    spec.modules.push({ id: id, label: def ? def.label : "記録・管理", icon: def ? def.icon : "📋", reason: why });
  }
  MODULE_DEFS.forEach(function (d) {
    var hit = hasAny(tMods, d.kw);
    if (!hit) return;
    /* 「カウントダウン」は timer。counter の誤検出を避ける */
    if (d.id === "calc" && picked.budget && !hasAny(t, ["電卓", "計算機", "calculator", "四則"])) return;
    pick(d.id, "「" + hit + "」");
  });

  /* 記録・管理 (CRUD) */
  var fields = extractFields(text);
  var entity = extractEntity(text, fields);
  var recordHit = new RegExp(RECORD_VERBS).test(text) || hasAny(t, RECORD_NOUNS) || fields.length >= 2;
  var mapped = null;
  if (entity) {
    ENTITY_TO_MODULE.forEach(function (p) { if (!mapped && p[0].test(entity)) mapped = p[1]; });
    if (mapped) { pick(mapped, "「" + entity + "」を扱う"); entity = ""; }
  }
  var ownFieldsUsed = false;
  if (entity || (recordHit && fields.length >= 2 && !mapped)) {
    spec.entity = entity || "データ";
    spec.modules.unshift({ id: "records", label: spec.entity + "の管理", icon: "📋", reason: entity ? "「" + entity + "を管理/記録」" : "項目の列挙" });
    picked.records = true;
    if (fields.length) { spec.fields = fields; ownFieldsUsed = true; }
    else {
      ENTITY_FIELDS.forEach(function (p) { if (!spec.fields.length && p[0].test(spec.entity)) spec.fields = p[1].map(function (n) { return { name: n, type: fieldType(n) }; }); });
      if (!spec.fields.length) spec.fields = [{ name: "名前", type: "string" }, { name: "日付", type: "date" }, { name: "メモ", type: "text" }];
      spec.assumptions.push("項目の指定がないため、「" + spec.entity + "」の一般的な項目 (" + spec.fields.map(function (f) { return f.name; }).join("・") + ") を用意しました。");
    }
  }
  if (!spec.modules.length) {
    spec.modules.push({ id: "notes", label: "メモ", icon: "📝", reason: "具体的な機能が読み取れないため" });
    spec.modules.push({ id: "todo", label: "ToDo", icon: "✅", reason: "具体的な機能が読み取れないため" });
    spec.assumptions.push("依頼文から具体的な機能が読み取れなかったため、汎用の「メモ + ToDo」アプリとして構成しました。");
  }
  spec.fields.forEach(function (f, i) { f.key = "f" + i; });

  /* 機能 */
  FEATURE_DEFS.forEach(function (d) { var hit = hasAny(t, d.kw); if (hit) spec.features[d.id] = { label: d.label, reason: "「" + hit + "」" }; });
  /* データを扱うモジュールには検索・並べ替え・書き出しを標準で付ける */
  if (picked.records || picked.notes || picked.todo || picked.budget) {
    ["search", "sort", "export"].forEach(function (id) {
      if (!spec.features[id]) {
        var d = FEATURE_DEFS.filter(function (x) { return x.id === id; })[0];
        spec.features[id] = { label: d.label, reason: "データを扱うアプリの標準機能 (仮定)", assumed: true };
      }
    });
  }
  if (picked.budget && !spec.features.chart) spec.features.chart = { label: "グラフ・集計", reason: "家計簿の標準機能 (仮定)", assumed: true };

  /* 見た目 */
  if (/ライト|明るい|白い背景|白背景|light/i.test(text)) spec.theme.mode = "light";
  if (/ダーク|暗い|黒い背景|黒背景|夜|dark/i.test(text)) spec.theme.mode = "dark";
  for (var ci = 0; ci < COLOR_DEFS.length; ci++) {
    if (COLOR_DEFS[ci][0].test(text)) { spec.theme.accent = COLOR_DEFS[ci][1]; spec.theme.accentName = COLOR_DEFS[ci][2]; break; }
  }

  /* プラットフォーム */
  PLATFORM_DEFS.forEach(function (p) { if (hasAny(t, p.kw)) spec.platforms.push(p.id); });
  if (!spec.platforms.length) {
    spec.platforms = ["android", "windows", "linux"];
    spec.assumptions.push("対象プラットフォームの指定がないため、Android (APK)・Windows 10/11・Linux の 3 種すべてを対象にしました。");
  }

  /* 題名・目的 */
  spec.title = extractTitle(text) || opts.title || "";
  if (!spec.title) {
    if (spec.modules.length === 1) spec.title = (spec.modules[0].id === "records" ? spec.entity + "の管理" : spec.modules[0].label) + "アプリ";
    else spec.title = spec.modules.slice(0, 3).map(function (m) { return m.id === "records" ? spec.entity + "管理" : m.label; }).join("・") + " アプリ";
  }
  spec.purpose = extractPurpose(clauses);

  /* 網羅: すべての節を仕様の要素に対応付ける */
  spec.clauses = clauses.map(function (c) {
    var lc = lower(c), hits = [];
    MODULE_DEFS.forEach(function (d) { if (picked[d.id] && hasAny(lc, d.kw)) hits.push("モジュール: " + d.label); });
    if (picked.records && (new RegExp(RECORD_VERBS).test(c) || hasAny(lc, RECORD_NOUNS) || (spec.entity && c.indexOf(spec.entity) >= 0))) hits.push("記録・管理: " + spec.entity);
    if (ownFieldsUsed) {
      var fs = spec.fields.filter(function (f) { return c.indexOf(f.name) >= 0; }).map(function (f) { return f.name; });
      if (fs.length) hits.push("項目: " + fs.join("・"));
    }
    FEATURE_DEFS.forEach(function (d) { if (hasAny(lc, d.kw)) hits.push("機能: " + d.label); });
    if (/ライト|明るい|白い背景|ダーク|暗い|黒い背景|dark|light/i.test(c)) hits.push("見た目: " + (spec.theme.mode === "light" ? "ライト" : "ダーク"));
    COLOR_DEFS.forEach(function (p) { if (p[0].test(c)) hits.push("色: " + p[2]); });
    PLATFORM_DEFS.forEach(function (p) { if (hasAny(lc, p.kw)) hits.push("対象: " + p.label); });
    if (spec.title && c.indexOf(spec.title) >= 0 && /[「『]/.test(c)) hits.push("題名: " + spec.title);
    if (!hits.length && c === spec.purpose && /ため|ように|向け|用に/.test(c)) hits.push("目的: " + c);
    if (!hits.length && REQUEST_PHRASES.test(c) && c.length <= 24) hits.push("意図: 作成依頼");
    return { text: c, hits: hits };
  });
  var covered = spec.clauses.filter(function (c) { return c.hits.length; }).length;
  spec.coverage = spec.clauses.length ? covered / spec.clauses.length : 1;
  spec.unresolved = spec.clauses.filter(function (c) { return !c.hits.length; }).map(function (c) { return c.text; });
  if (spec.unresolved.length) {
    spec.assumptions.push("解釈できなかった節 " + spec.unresolved.length + " 件は、アプリ内「この依頼について」と論文の「限界」に原文のまま記載しました。");
  }
  return spec;
}
