/*
 * silent.js — BadaGPT電信「サイレント・トーク (非言語思考入力)」拡張
 *
 * 言葉を介さずに、頭の中のアイデアを **非言語のアトム** (無言のグリフ・
 * 手描きのスケッチ・リズムのタップ) として並べ、それを本物の (小さく・
 * 決定的な) **トランスフォーマー (自己注意)** で「言語化されていない潜在
 * 表現 (latent)」へ変換する。この latent を復号して
 *   ① 本と同じ分量まで展開できる文章 (言語変換)
 *   ② それに合わせたイメージ (生成画像 = 決定的な SVG)
 *   ③ Bada 言語のプログラム
 *   ④ BadaGPT への思考入力 (依頼文)
 * を作る。①〜④ は latent から決定的に導かれる。
 *
 * 正直な範囲: これは利用者が **自分で並べた非言語のアトム** を処理する
 * もので、脳の信号を読み取る機能はない。トランスフォーマーは固定の重みを
 * 持つ小さな自己注意ネットワーク (学習済み LLM ではない) で、同じ入力は
 * 必ず同じ出力になる。文章は latent に駆動された決定的なテンプレート展開
 * であり、意味のある新規の内容を創作するものではない。「サイレント・トーク」
 * は利用者が選んだグリフ等を指し、他者の無言の発話を傍受するものではない。
 */
"use strict";

/* ───────────── 決定的 PRNG (mulberry32) ───────────── */
function mulberry32(seed) {
  var a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashStr(s) {
  var h = 2166136261 >>> 0;
  s = String(s);
  for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

/* ───────────── 非言語アトム (無言のグリフ) ─────────────
 * 各アトムは「無言のグリフ」と、復号に使う弱いタグを持つ。
 * タグはグリフの固定の意味としてパレットに表示される (利用者に見える)。 */
var SILENT_ATOMS = [
  /* 感情・質感 (tone) */
  { id: "calm",    g: "◎", cat: "tone", tags: { mood: "calm" } },
  { id: "joy",     g: "✦", cat: "tone", tags: { mood: "joy" } },
  { id: "urgent",  g: "▲", cat: "tone", tags: { mood: "urgent", feat: "sound" } },
  { id: "cool",    g: "❄", cat: "tone", tags: { theme: "dark", accent: "青" } },
  { id: "warm",    g: "♨", cat: "tone", tags: { theme: "light", accent: "オレンジ" } },
  { id: "vivid",   g: "⚡", cat: "tone", tags: { accent: "紫" } },
  /* 領域 (domain) → モジュール */
  { id: "records", g: "▤", cat: "domain", tags: { mod: "records" } },
  { id: "time",    g: "◷", cat: "domain", tags: { mod: "timer" } },
  { id: "money",   g: "₪", cat: "domain", tags: { mod: "budget" } },
  { id: "note",    g: "✎", cat: "domain", tags: { mod: "notes" } },
  { id: "task",    g: "☑", cat: "domain", tags: { mod: "todo" } },
  { id: "sound",   g: "♪", cat: "domain", tags: { mod: "telegraph" } },
  { id: "quantum", g: "⬡", cat: "domain", tags: { mod: "quantum" } },
  { id: "measure", g: "📐", cat: "domain", tags: { mod: "convert" } },
  { id: "learn",   g: "✚", cat: "domain", tags: { mod: "quiz" } },
  /* 対象 (object) */
  { id: "book",    g: "📖", cat: "object", tags: { entity: "本", mod: "records" } },
  { id: "person",  g: "👤", cat: "object", tags: { entity: "人", mod: "records" } },
  { id: "habit",   g: "🌱", cat: "object", tags: { mod: "habit" } },
  { id: "draw",    g: "🎨", cat: "object", tags: { mod: "draw" } },
  { id: "random",  g: "🎲", cat: "object", tags: { mod: "random" } },
  { id: "count",   g: "⊞", cat: "object", tags: { mod: "counter" } },
  /* 動作 (action) → 機能 */
  { id: "find",    g: "🔍", cat: "action", tags: { feat: "search" } },
  { id: "sort",    g: "⇅", cat: "action", tags: { feat: "sort" } },
  { id: "graph",   g: "▦", cat: "action", tags: { feat: "chart" } },
  { id: "export",  g: "⤓", cat: "action", tags: { feat: "export" } },
  { id: "print",   g: "⎙", cat: "action", tags: { feat: "print" } },
  /* 規模 (scale) → 文章の分量 */
  { id: "small",   g: "·",  cat: "scale", tags: { volume: 0.25 } },
  { id: "medium",  g: "◆", cat: "scale", tags: { volume: 1 } },
  { id: "large",   g: "⬢", cat: "scale", tags: { volume: 3 } },
  { id: "book_vol",g: "∞", cat: "scale", tags: { volume: 12 } },
  /* 環境 (platform) */
  { id: "android", g: "📱", cat: "platform", tags: { platform: "android" } },
  { id: "windows", g: "🖥", cat: "platform", tags: { platform: "windows" } },
  { id: "linux",   g: "🐧", cat: "platform", tags: { platform: "linux" } }
];
var ATOM_BY_ID = {};
SILENT_ATOMS.forEach(function (a) { ATOM_BY_ID[a.id] = a; });

/* ───────────── 行列ユーティリティ ───────────── */
function zeros(r, c) { var m = []; for (var i = 0; i < r; i++) { m.push(new Array(c).fill(0)); } return m; }
function randMat(r, c, rng, s) { var m = zeros(r, c); for (var i = 0; i < r; i++) for (var j = 0; j < c; j++) m[i][j] = (rng() * 2 - 1) * s; return m; }
function matmul(A, B) {
  var r = A.length, k = B.length, c = B[0].length, out = zeros(r, c);
  for (var i = 0; i < r; i++) for (var j = 0; j < c; j++) { var s = 0; for (var t = 0; t < k; t++) s += A[i][t] * B[t][j]; out[i][j] = s; }
  return out;
}
function addRes(A, B) { var out = zeros(A.length, A[0].length); for (var i = 0; i < A.length; i++) for (var j = 0; j < A[0].length; j++) out[i][j] = A[i][j] + B[i][j]; return out; }
function layerNorm(A) {
  var out = zeros(A.length, A[0].length);
  for (var i = 0; i < A.length; i++) {
    var row = A[i], n = row.length, mean = 0, j;
    for (j = 0; j < n; j++) mean += row[j]; mean /= n;
    var v = 0; for (j = 0; j < n; j++) v += (row[j] - mean) * (row[j] - mean); v /= n;
    var sd = Math.sqrt(v + 1e-5);
    for (j = 0; j < n; j++) out[i][j] = (row[j] - mean) / sd;
  }
  return out;
}
function softmaxRow(row) {
  var mx = -Infinity, i; for (i = 0; i < row.length; i++) if (row[i] > mx) mx = row[i];
  var s = 0, e = new Array(row.length);
  for (i = 0; i < row.length; i++) { e[i] = Math.exp(row[i] - mx); s += e[i]; }
  for (i = 0; i < row.length; i++) e[i] /= s;
  return e;
}
function geluRow(A) { var out = zeros(A.length, A[0].length); for (var i = 0; i < A.length; i++) for (var j = 0; j < A[0].length; j++) { var x = A[i][j]; out[i][j] = 0.5 * x * (1 + Math.tanh(0.7978845608 * (x + 0.044715 * x * x * x))); } return out; }

/* ───────────── トランスフォーマー (固定の重み・決定的) ───────────── */
var SILENT_CFG = { D: 16, H: 4, L: 2, FF: 32, seed: 0x5A1E27 };

function buildWeights(cfg) {
  var rng = mulberry32(cfg.seed), layers = [];
  for (var l = 0; l < cfg.L; l++) {
    layers.push({
      Wq: randMat(cfg.D, cfg.D, rng, 0.5), Wk: randMat(cfg.D, cfg.D, rng, 0.5),
      Wv: randMat(cfg.D, cfg.D, rng, 0.5), Wo: randMat(cfg.D, cfg.D, rng, 0.5),
      W1: randMat(cfg.D, cfg.FF, rng, 0.4), W2: randMat(cfg.FF, cfg.D, rng, 0.4)
    });
  }
  return layers;
}
var SILENT_WEIGHTS = buildWeights(SILENT_CFG);

/* アトム列 → 埋め込み行列 (各アトムの固定ベクトル + 位置エンコード) */
function embedSequence(ids, cfg) {
  var n = ids.length, X = zeros(n, cfg.D);
  for (var i = 0; i < n; i++) {
    var rng = mulberry32(hashStr("atom:" + ids[i]));
    for (var j = 0; j < cfg.D; j++) {
      var base = (rng() * 2 - 1);
      var pos = (j % 2 === 0) ? Math.sin(i / Math.pow(1000, j / cfg.D)) : Math.cos(i / Math.pow(1000, (j - 1) / cfg.D));
      X[i][j] = base + 0.3 * pos;
    }
  }
  return X;
}

/* 1 層の自己注意 (多頭)。attRows に各ヘッドの注意行列 (行和=1) を記録する */
function attentionLayer(X, W, cfg, attRows) {
  var n = X.length, dh = cfg.D / cfg.H;
  var Q = matmul(X, W.Wq), K = matmul(X, W.Wk), V = matmul(X, W.Wv);
  var concat = zeros(n, cfg.D);
  for (var h = 0; h < cfg.H; h++) {
    var off = h * dh;
    for (var i = 0; i < n; i++) {
      var scores = new Array(n);
      for (var jk = 0; jk < n; jk++) {
        var dot = 0; for (var d = 0; d < dh; d++) dot += Q[i][off + d] * K[jk][off + d];
        scores[jk] = dot / Math.sqrt(dh);
      }
      var att = softmaxRow(scores);
      if (attRows) attRows.push(att);
      for (var d2 = 0; d2 < dh; d2++) { var acc = 0; for (var jv = 0; jv < n; jv++) acc += att[jv] * V[jv][off + d2]; concat[i][off + d2] = acc; }
    }
  }
  var O = matmul(concat, W.Wo);
  return layerNorm(addRes(X, O));
}
function ffnLayer(X, W) {
  var H1 = geluRow(matmul(X, W.W1));
  var O = matmul(H1, W.W2);
  return layerNorm(addRes(X, O));
}

/* 非言語アトム列 → latent。{ seq, pooled, attention } を返す */
function silentEncode(ids, cfg) {
  cfg = cfg || SILENT_CFG;
  if (!ids || !ids.length) return { seq: [], pooled: new Array(cfg.D).fill(0), attention: [] };
  var X = embedSequence(ids, cfg), attention = [];
  for (var l = 0; l < cfg.L; l++) {
    X = attentionLayer(X, SILENT_WEIGHTS[l], cfg, l === cfg.L - 1 ? attention : null);
    X = ffnLayer(X, SILENT_WEIGHTS[l]);
  }
  var pooled = new Array(cfg.D).fill(0);
  for (var i = 0; i < X.length; i++) for (var j = 0; j < cfg.D; j++) pooled[j] += X[i][j] / X.length;
  return { seq: X, pooled: pooled, attention: attention };
}

/* ───────────── latent → 依頼文 (言語変換) ───────────── */
function collectTags(ids) {
  var mods = [], feats = {}, entity = "", theme = "", accent = "", mood = "", platforms = [], volume = 1, seen = {};
  ids.forEach(function (id) {
    var a = ATOM_BY_ID[id]; if (!a) return; var t = a.tags;
    if (t.mod && !seen[t.mod]) { seen[t.mod] = 1; mods.push(t.mod); }
    if (t.entity) entity = t.entity;
    if (t.feat) feats[t.feat] = 1;
    if (t.theme) theme = t.theme;
    if (t.accent) accent = t.accent;
    if (t.mood) mood = t.mood;
    if (t.platform && platforms.indexOf(t.platform) < 0) platforms.push(t.platform);
    if (typeof t.volume === "number") volume = Math.max(volume, t.volume);
  });
  return { mods: mods, feats: Object.keys(feats), entity: entity, theme: theme, accent: accent, mood: mood, platforms: platforms, volume: volume };
}
var MOD_PHRASE = {
  records: "を記録・管理", timer: "タイマー", budget: "家計簿", notes: "メモ", todo: "ToDo リスト",
  telegraph: "モールス電信", quantum: "量子回路", convert: "単位変換", quiz: "クイズ・単語帳",
  habit: "習慣トラッカー", draw: "お絵かき", random: "抽選・サイコロ", counter: "カウンター"
};
var FEAT_PHRASE = { search: "検索", sort: "並べ替え", chart: "グラフ", export: "CSV で書き出し", print: "印刷" };
var PLAT_PHRASE = { android: "スマホ", windows: "Windows", linux: "Linux" };

/* 非言語アトム列 → BadaGPT への依頼文。latent の符号で表現を少し変える。 */
function silentToRequest(ids, enc) {
  var tg = collectTags(ids);
  if (!tg.mods.length) tg.mods = ["notes"];
  var p = enc && enc.pooled.length ? enc.pooled : [0];
  var parts = [];
  var want = [];
  tg.mods.forEach(function (m) {
    if (m === "records") want.push((tg.entity || "データ") + MOD_PHRASE.records);
    else want.push(MOD_PHRASE[m] || m);
  });
  parts.push(want.join("と") + "のアプリ" + (p[0] >= 0 ? "を作りたい" : "がほしい") + "。");
  if (tg.feats.length) parts.push(tg.feats.map(function (f) { return FEAT_PHRASE[f]; }).filter(Boolean).join("と") + "をしたい。");
  var look = [];
  if (tg.theme === "dark") look.push("暗い"); if (tg.theme === "light") look.push("明るい");
  if (tg.accent) look.push(tg.accent + "色");
  if (look.length) parts.push(look.join("") + "デザインで。");
  if (tg.platforms.length) parts.push(tg.platforms.map(function (x) { return PLAT_PHRASE[x]; }).join("と") + "で使いたい。");
  return { text: parts.join(""), tags: tg };
}

/* ───────────── latent → 本と同じ分量まで展開できる文章 ───────────── */
var CH_TITLES = ["着想", "輪郭", "領域", "要素", "振る舞い", "見え方", "質感", "利用の情景", "周縁", "限界", "展開", "結び"];
function latentToDocument(ids, enc, opts) {
  opts = opts || {};
  var tg = collectTags(ids);
  var pooled = enc && enc.pooled.length ? enc.pooled : new Array(SILENT_CFG.D).fill(0);
  /* 目標文字数: 規模アトムの volume × 基準。∞(book_vol)=12 で約 9.6 万字 (本一冊相当) */
  var target = Math.round((opts.targetChars != null ? opts.targetChars : tg.volume * 8000));
  target = Math.max(400, Math.min(target, 200000));
  var rng = mulberry32((hashStr(ids.join(",")) ^ Math.round(Math.abs(pooled[0]) * 1e6)) >>> 0);
  var subject = (tg.entity ? tg.entity + "を扱う" : "") + (tg.mods.map(function (m) { return (MOD_PHRASE[m] || m).replace(/^を/, ""); }).join("・")) + "アプリケーション";
  var moodWord = { calm: "静かに", joy: "軽やかに", urgent: "すばやく", "": "着実に" }[tg.mood] || "着実に";
  var out = ["# 思考ノート：" + subject, "", "> このノートは、言葉を介さずに並べた非言語のアトム (" +
    ids.map(function (id) { return (ATOM_BY_ID[id] || {}).g || "?"; }).join(" ") + ") を、トランスフォーマーで latent に変換し、" +
    "その latent から決定的に展開した文章です。意味のある新規の内容ではなく、着想を本と同じ分量まで膨らませた素描です。", ""];
  var chN = Math.max(4, Math.min(CH_TITLES.length, Math.round(2 + tg.volume)));
  var LEX_SUBJ = ["この着想", "その輪郭", "利用者", "画面", "ひとつの操作", "記録された要素", "全体", "細部", "入力", "結果"];
  var LEX_VERB = ["立ち上がる", "静かに整えられる", "手のうちに収まる", "次第に像を結ぶ", "滑らかに流れる", "確かめられる", "積み重なる", "呼び戻される", "並べ替えられる", "照らし出される"];
  var LEX_ADJ = ["透明な", "落ち着いた", "軽い", "確かな", "親しい", moodWord.replace(/に$/, "な"), "余白のある", "手触りのある"];
  function sentence() {
    var s = LEX_ADJ[Math.floor(rng() * LEX_ADJ.length)] + LEX_SUBJ[Math.floor(rng() * LEX_SUBJ.length)];
    s += "は、" + moodWord + LEX_VERB[Math.floor(rng() * LEX_VERB.length)];
    if (rng() < 0.5) s += "。そこでは" + LEX_SUBJ[Math.floor(rng() * LEX_SUBJ.length)] + "が" + LEX_VERB[Math.floor(rng() * LEX_VERB.length)];
    return s + "。";
  }
  var len = out.join("\n").length;
  for (var c = 0; c < chN && len < target; c++) {
    var title = CH_TITLES[c] || ("章 " + (c + 1));
    out.push("## " + (c + 1) + ". " + title); out.push("");
    var paras = Math.max(2, Math.round(target / chN / 220));
    for (var pgi = 0; pgi < paras && len < target; pgi++) {
      var sents = 3 + Math.floor(rng() * 4), buf = "";
      for (var s2 = 0; s2 < sents; s2++) buf += sentence();
      out.push(buf); out.push("");
      len += buf.length + 2;
    }
  }
  out.push("---"); out.push("非言語アトム: " + ids.map(function (id) { var a = ATOM_BY_ID[id]; return a ? a.g + a.id : id; }).join(" / "));
  var text = out.join("\n");
  return { markdown: text, chars: text.length, target: target, chapters: chN };
}

/* ───────────── latent → イメージ (決定的な SVG) ───────────── */
function latentToImagery(enc, n) {
  n = n || 3;
  var pooled = enc && enc.pooled.length ? enc.pooled : new Array(SILENT_CFG.D).fill(0);
  var imgs = [];
  for (var k = 0; k < n; k++) {
    var rng = mulberry32((hashStr("img:" + k) ^ Math.round((pooled[k % pooled.length] || 0) * 1e6 + k * 97)) >>> 0);
    var W = 220, H = 160, parts = [];
    var hue = Math.floor((Math.abs(pooled[k % pooled.length] || 0) * 360 + k * 47) % 360);
    parts.push('<rect width="' + W + '" height="' + H + '" fill="hsl(' + hue + ',40%,8%)"/>');
    var shapes = 14 + Math.floor(rng() * 10);
    for (var i = 0; i < shapes; i++) {
      var x = rng() * W, y = rng() * H, r = 4 + rng() * 30;
      var h2 = Math.floor((hue + rng() * 120) % 360), op = (0.2 + rng() * 0.5).toFixed(2);
      if (rng() < 0.5) parts.push('<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + r.toFixed(1) + '" fill="hsl(' + h2 + ',70%,60%)" opacity="' + op + '"/>');
      else parts.push('<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + r.toFixed(1) + '" height="' + r.toFixed(1) + '" fill="hsl(' + h2 + ',70%,55%)" opacity="' + op + '" transform="rotate(' + (rng() * 90).toFixed(1) + ' ' + x.toFixed(1) + ' ' + y.toFixed(1) + ')"/>');
    }
    imgs.push('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '">' + parts.join("") + "</svg>");
  }
  return imgs;
}

/* ───────────── latent → Bada 言語のプログラム ─────────────
 * BadaInterp で構文エラーなく実行できる Bada プログラムを組み立てる。 */
function latentToBada(ids, enc, req) {
  var tg = (req && req.tags) || collectTags(ids);
  var pooled = enc && enc.pooled.length ? enc.pooled : new Array(SILENT_CFG.D).fill(0);
  var H = (Math.abs(pooled[0] || 0) * 3 + 1).toFixed(2);
  var n = 2 + (ids.length % 10);
  var L = [];
  L.push("# silent.bada — 非言語思考入力 (サイレント・トーク) から生成された Bada プログラム");
  L.push("# アトム: " + ids.map(function (id) { return (ATOM_BY_ID[id] || {}).g || id; }).join(" "));
  L.push("set entropy   = " + H);
  L.push("set crossings = " + n);
  L.push("set idea      = 0");
  L.push('idea <- "silent telepathy-free non-verbal thought"');
  L.push("idea -< 1.0");
  L.push("idea >- idea");
  L.push("Omega::push idea as thought_node");
  L.push("print idea");
  /* アトムの領域ごとに 1 行ずつ Bada 命令を積む */
  tg.mods.forEach(function (m, i) {
    L.push("set mod_" + i + " = " + (i + 1));
    L.push('mod_' + i + ' <- "' + m + '"');
    L.push("Omega::push mod_" + i + " as module_node");
  });
  L.push("Tele::encode");
  L.push("Tele::knot crossings");
  L.push("Tele::teleport");
  L.push("Tele::graviton");
  L.push("Tele::send");
  L.push("GPT::comprehend");
  L.push("GPT::plan");
  L.push("GPT::generate");
  L.push("GPT::verify");
  L.push("GPT::paper");
  return L.join("\n");
}

/* ───────────── イメージした思い (ジェスチャー) → 特徴 ─────────────
 * 利用者が「頭に思い描いたものを、言葉を介さずに連続した動きで描く」。
 * その動き (ストロークの集まり) の速さ・広がり・向き・曲がり・リズム・重心を
 * 固定の規則で特徴量にする。思考を読むのではなく、描かれた動きを読む。
 * strokes: [[{x,y,t}, ...], ...]  x,y は 0..1 に正規化、t はミリ秒。 */
function gestureFeatures(strokes) {
  strokes = (strokes || []).filter(function (s) { return s && s.length; });
  var f = {
    strokes: strokes.length, points: 0, pathLen: 0, durationMs: 0,
    minX: 1, minY: 1, maxX: 0, maxY: 0, cx: 0, cy: 0,
    speedMean: 0, speedVar: 0, curvature: 0, dir: new Array(8).fill(0), rhythmVar: 0
  };
  if (!strokes.length) return f;
  var speeds = [], sumX = 0, sumY = 0, tStart = Infinity, tEnd = -Infinity, prevAng = null, strokeStarts = [];
  strokes.forEach(function (st) {
    strokeStarts.push(st[0].t);
    for (var i = 0; i < st.length; i++) {
      var p = st[i];
      f.points++; sumX += p.x; sumY += p.y;
      f.minX = Math.min(f.minX, p.x); f.minY = Math.min(f.minY, p.y);
      f.maxX = Math.max(f.maxX, p.x); f.maxY = Math.max(f.maxY, p.y);
      if (p.t < tStart) tStart = p.t; if (p.t > tEnd) tEnd = p.t;
      if (i > 0) {
        var q = st[i - 1], dx = p.x - q.x, dy = p.y - q.y, len = Math.hypot(dx, dy), dt = Math.max(1, p.t - q.t);
        f.pathLen += len;
        if (len > 1e-4) {
          speeds.push(len / dt * 1000);
          var ang = Math.atan2(dy, dx);
          var bin = Math.floor(((ang + Math.PI) / (2 * Math.PI)) * 8) % 8;
          f.dir[bin] += len;
          if (prevAng != null) { var da = Math.abs(ang - prevAng); if (da > Math.PI) da = 2 * Math.PI - da; f.curvature += da; }
          prevAng = ang;
        }
      }
    }
  });
  f.cx = sumX / f.points; f.cy = sumY / f.points;
  f.durationMs = (tEnd > tStart) ? tEnd - tStart : 0;
  if (speeds.length) {
    var m = speeds.reduce(function (a, b) { return a + b; }, 0) / speeds.length;
    f.speedMean = m;
    f.speedVar = speeds.reduce(function (a, b) { return a + (b - m) * (b - m); }, 0) / speeds.length;
  }
  if (strokeStarts.length > 1) {
    var gaps = [];
    for (var k = 1; k < strokeStarts.length; k++) gaps.push(strokeStarts[k] - strokeStarts[k - 1]);
    var gm = gaps.reduce(function (a, b) { return a + b; }, 0) / gaps.length;
    f.rhythmVar = gaps.reduce(function (a, b) { return a + (b - gm) * (b - gm); }, 0) / gaps.length;
  }
  return f;
}

/* 重心の 3×3 領域 → 主モジュール (どこに思いを描いたかで何のアプリかが決まる) */
var GESTURE_GRID = [
  ["note", "records", "task"],
  ["draw", "quantum", "money"],
  ["random", "habit", "time"]
];
var DIR_NAME = ["右", "右下", "下", "左下", "左", "左上", "上", "右上"];

/* ジェスチャー特徴 → 非言語アトム列 + 読み取り内容 (利用者に見せる) */
function gestureToAtoms(f) {
  var atoms = [], feat = [], readout = [];
  if (!f.points) return { atoms: [], feat: [], readout: [] };
  function add(id) { if (id && atoms.indexOf(id) < 0) atoms.push(id); }
  /* 重心 → 主モジュール */
  var col = Math.min(2, Math.floor(f.cx * 3)), row = Math.min(2, Math.floor(f.cy * 3));
  var primary = GESTURE_GRID[row][col];
  add(primary);
  var pa = ATOM_BY_ID[primary] || {}, pmod = (pa.tags && pa.tags.mod) || "";
  var pname = (MOD_PHRASE[pmod] || MOD_PHRASE[primary] || primary).replace(/^を/, "");
  readout.push({ label: "思いの重心", value: (["上", "中", "下"][row]) + "・" + (["左", "中", "右"][col]), meant: pname + " のアプリ" });
  /* 広がり (pathLen) → 文章の分量・大きさ */
  var vol = f.pathLen < 1.5 ? "small" : f.pathLen < 4 ? "medium" : f.pathLen < 8 ? "large" : "book_vol";
  add(vol);
  readout.push({ label: "広がり (動きの長さ)", value: f.pathLen.toFixed(2), meant: "分量 " + ({ small: "素描", medium: "短編", large: "中編", book_vol: "本一冊" }[vol]) });
  /* 曲がり (curvature) → 気分・配色 */
  var curv = f.curvature;
  if (curv > 12) { add("urgent"); add("vivid"); readout.push({ label: "曲がりの多さ", value: curv.toFixed(1), meant: "勢いのある思い → 音で知らせる・紫" }); }
  else if (curv < 3 && f.speedVar < 1e5) { add("calm"); readout.push({ label: "曲がりの少なさ", value: curv.toFixed(1), meant: "静かな思い → 落ち着いた構成" }); }
  else { add("joy"); readout.push({ label: "動きの質", value: curv.toFixed(1), meant: "軽やかな思い" }); }
  /* 重心の高さ → 明暗・色 */
  if (f.cy < 0.4) { add("cool"); readout.push({ label: "上側に描いた", value: f.cy.toFixed(2), meant: "暗い青のデザイン" }); }
  else if (f.cy > 0.6) { add("warm"); readout.push({ label: "下側に描いた", value: f.cy.toFixed(2), meant: "明るいオレンジのデザイン" }); }
  /* 主な向き → 機能 */
  var domBin = 0, domVal = -1;
  f.dir.forEach(function (v, i) { if (v > domVal) { domVal = v; domBin = i; } });
  if (domBin === 2 || domBin === 6) { add("sort"); readout.push({ label: "主な向き", value: DIR_NAME[domBin], meant: "並べ替え" }); }
  else if (domBin === 0 || domBin === 4) { add("find"); readout.push({ label: "主な向き", value: DIR_NAME[domBin], meant: "検索" }); }
  else { readout.push({ label: "主な向き", value: DIR_NAME[domBin], meant: "—" }); }
  /* ストローク数 → 追加モジュール / グラフ */
  if (f.strokes >= 3) { add("graph"); readout.push({ label: "ストローク数", value: String(f.strokes), meant: "グラフ・集計" }); }
  /* 広がりの形 → 対象プラットフォーム */
  var w = f.maxX - f.minX, h = f.maxY - f.minY;
  if (w > h * 1.3) { add("windows"); add("linux"); readout.push({ label: "横長の思い", value: w.toFixed(2) + "×" + h.toFixed(2), meant: "Windows・Linux" }); }
  else if (h > w * 1.3) { add("android"); readout.push({ label: "縦長の思い", value: w.toFixed(2) + "×" + h.toFixed(2), meant: "スマホ" }); }
  /* トランスフォーマーへ渡す非言語の特徴トークン (latent を細かく変える) */
  feat.push("g:spd" + Math.min(9, Math.round(f.speedMean / 200)));
  feat.push("g:cur" + Math.min(9, Math.round(curv)));
  feat.push("g:dir" + domBin);
  feat.push("g:ext" + Math.min(9, Math.round(f.pathLen)));
  feat.push("g:rhy" + Math.min(9, Math.round(Math.sqrt(f.rhythmVar) / 100)));
  feat.push("g:pts" + Math.min(9, Math.round(f.points / 20)));
  return { atoms: atoms, feat: feat, readout: readout };
}

/* イメージした思い (ジェスチャー) を 1 回で処理して全成果物を返す */
function gestureProcess(strokes, opts) {
  opts = opts || {};
  var f = gestureFeatures(strokes);
  var g = gestureToAtoms(f);
  var seq = g.atoms.concat(g.feat);
  var enc = silentEncode(seq);
  var req = silentToRequest(g.atoms, enc);
  return {
    source: "gesture",
    features: f, readout: g.readout, atoms: g.atoms, seq: seq, enc: enc,
    request: req.text, tags: req.tags,
    document: latentToDocument(seq, enc, opts),
    imagery: latentToImagery(enc, opts.images || 3),
    bada: latentToBada(g.atoms, enc, req)
  };
}

/* 非言語アトム列を 1 回で処理して全成果物を返す (UI/テスト兼用) */
function silentProcess(ids, opts) {
  opts = opts || {};
  var enc = silentEncode(ids);
  var req = silentToRequest(ids, enc);
  return {
    seq: ids.slice(),
    enc: enc,
    request: req.text,
    tags: req.tags,
    document: latentToDocument(ids, enc, opts),
    imagery: latentToImagery(enc, opts.images || 3),
    bada: latentToBada(ids, enc, req)
  };
}
