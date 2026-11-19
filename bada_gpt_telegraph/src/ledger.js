/*
 * ledger.js — 会話台帳 (TupleSpace: 追記のみ) と、未知事前の仕様の研ぎ澄まし (第 2 版)
 *
 * 文献 13 (Bada engine full source) Module 1 と文献 14 (Unknown-Prior Engine) 定義 1–4 の
 * 設計を、BadaGPT電信の対話に移したもの:
 *
 *   Omega::DATABASE[tuplespace] — 「事実は積み上がるだけで、何も上書きされない」
 *     def append |fact| >> facts <- fact.frozen   # never mutate
 *     def gc => projection.exclude ; facts.preserved
 *
 *   - 台帳 (Ledger) は追記のみ。発話・読み取った仕様・除外・錬成・やり直し を事実として積む。
 *   - 「いまの仕様」は台帳の **投影** (projectSpec)。除外は投影から外すだけで、事実は残る。
 *   - 「やり直し」も事実 (reset)。投影の地平 (horizon) が進むだけで、過去の事実は消えない。
 *   - 未知事前 (定義 4): モジュールへの信念は一様 (最大エントロピー) から始まり、台帳の証拠で
 *     尖る。除外されたモジュールは信念 0 (確信した零) で、後の発話が明示的に再び足すまで戻らない。
 *
 * 第 2 版 (対話) の中核: ChatGPT のように、続けて話すほど仕様が研ぎ澄まされる。
 */
"use strict";

function Ledger(facts) {
  this.facts = [];
  var self = this;
  (facts || []).forEach(function (f) { self.facts.push(Object.freeze(Object.assign({}, f))); });
}
/* 追記のみ。返り値は事実の番号 t。事実は凍結され、二度と変わらない。 */
Ledger.prototype.append = function (fact) {
  var f = Object.freeze(Object.assign({}, fact || {}, { t: this.facts.length, at: (fact && fact.at) || Date.now() }));
  this.facts.push(f);
  return f.t;
};
Ledger.prototype.read = function (pred) { return pred ? this.facts.filter(pred) : this.facts.slice(); };
Ledger.prototype.size = function () { return this.facts.length; };
Ledger.prototype.toJSON = function () { return this.facts.slice(); };
/* 投影の地平: 最後の reset の次。それ以前の事実は保存されるが、投影には使わない。 */
Ledger.prototype.horizon = function () { var h = 0; this.facts.forEach(function (f) { if (f.kind === "reset") h = f.t + 1; }); return h; };
Ledger.prototype.turns = function () { var h = this.horizon(); return this.facts.filter(function (f) { return f.t >= h && f.kind === "say"; }).length; };

/* ───────────── 発話の読み取り: 除外の節と、追加の節 ───────────── */
var REMOVE_VERBS = /(外して|外す|はずして|いらない|要らない|不要|なしで|無しで|なしに|やめて|やめる|やめ|削除|消して|抜いて|除いて|取って|without|remove|drop)/i;
var FIELD_ADD = /([^、。\s「」]+?)(?:も|を)?(?:項目|フィールド|列)(?:に|として)?(?:足|追加|加え|入れ)/;
var FIELD_REMOVE = /([^、。\s「」]+?)(?:の|は|を)?(?:項目|フィールド|列)(?:は|を)?(?:外|いらない|要らない|不要|削除|消)/;

function exclusionsIn(clause) {
  var lc = lower(clause), out = [];
  MODULE_DEFS.forEach(function (d) { var k = hasAny(lc, d.kw); if (k) out.push({ target: "module", id: d.id, label: d.label, by: k }); });
  FEATURE_DEFS.forEach(function (d) { var k = hasAny(lc, d.kw); if (k) out.push({ target: "feature", id: d.id, label: d.label, by: k }); });
  PLATFORM_DEFS.forEach(function (d) { var k = hasAny(lc, d.kw); if (k) out.push({ target: "platform", id: d.id, label: d.label, by: k }); });
  return out;
}

/* 1 発話を、追加の仕様 (delta) と除外 (exclusions) と項目の増減に分ける */
function analyzeTurn(text) {
  var clauses = splitClauses(text), keep = [], excl = [], removedClauses = [], fieldAdds = [], fieldRemoves = [];
  clauses.forEach(function (c) {
    var fr = c.match(FIELD_REMOVE);
    if (fr && REMOVE_VERBS.test(c)) { var rn = nounTail(fr[1]); if (rn) { fieldRemoves.push(rn); removedClauses.push({ text: c, hits: ["項目を除外: " + rn] }); return; } }
    var fa = c.match(FIELD_ADD);
    if (fa) { var an = nounTail(fa[1]); if (an && !FIELD_STOP.test(an)) { fieldAdds.push(an); removedClauses.push({ text: c, hits: ["項目を追加: " + an] }); return; } }
    if (REMOVE_VERBS.test(c)) {
      var e = exclusionsIn(c);
      if (e.length) { excl = excl.concat(e); removedClauses.push({ text: c, hits: e.map(function (x) { return "除外: " + x.label; }) }); return; }
    }
    keep.push(c);
  });
  var delta = keep.length ? comprehend(keep.join("。") + "。") : null;
  var flags = delta ? {
    fallbackModules: delta.assumptions.some(function (a) { return /具体的な機能が読み取れなかった/.test(a); }),
    fieldsAssumed: delta.assumptions.some(function (a) { return /項目の指定がないため/.test(a); }),
    platformsAssumed: delta.assumptions.some(function (a) { return /対象プラットフォームの指定がない/.test(a); }),
    titleExplicit: !!extractTitle(text),
    themeMentioned: /ライト|明るい|白い背景|白背景|light|ダーク|暗い|黒い背景|黒背景|夜|dark/i.test(text),
    accentMentioned: !!delta.theme.accentName
  } : null;
  return { text: text, delta: delta, flags: flags, exclusions: excl, fieldAdds: fieldAdds, fieldRemoves: fieldRemoves, extraClauses: removedClauses };
}

/* 発話を台帳に積む: 発話 → 読み取った仕様 → 除外 の順にすべて事実として追記 (上書きなし) */
function ledgerSay(ledger, text, src) {
  var a = analyzeTurn(text);
  var turn = ledger.append({ kind: "say", src: src || "文字", text: String(text) });
  if (a.delta) {
    var d = a.delta;
    ledger.append({ kind: "spec", turn: turn, flags: a.flags,
      modules: a.flags.fallbackModules ? [] : d.modules.map(function (m) { return { id: m.id, label: m.label, icon: m.icon, reason: m.reason }; }),
      fallback: a.flags.fallbackModules ? d.modules.map(function (m) { return { id: m.id, label: m.label, icon: m.icon, reason: m.reason }; }) : [],
      entity: d.entity, fields: d.fields.map(function (f) { return { name: f.name, type: f.type }; }),
      features: Object.keys(d.features).map(function (id) { return { id: id, label: d.features[id].label, reason: d.features[id].reason, assumed: !!d.features[id].assumed }; }),
      theme: { mode: d.theme.mode, accent: d.theme.accent, accentName: d.theme.accentName },
      platforms: a.flags.platformsAssumed ? [] : d.platforms.slice(),
      title: a.flags.titleExplicit ? d.title : "", purpose: d.purpose,
      clauses: d.clauses.map(function (c) { return { text: c.text, hits: c.hits.slice() }; }).concat(a.extraClauses),
      unresolved: d.unresolved.slice(), assumptions: d.assumptions.slice() });
  } else if (a.extraClauses.length) {
    ledger.append({ kind: "spec", turn: turn, flags: null, modules: [], fallback: [], entity: "", fields: [], features: [], theme: null, platforms: [], title: "", purpose: "", clauses: a.extraClauses, unresolved: [], assumptions: [] });
  }
  a.exclusions.forEach(function (e) { ledger.append({ kind: "exclude", turn: turn, target: e.target, id: e.id, label: e.label, by: e.by }); });
  a.fieldAdds.forEach(function (n) { ledger.append({ kind: "field", turn: turn, op: "add", name: n, type: fieldType(n) }); });
  a.fieldRemoves.forEach(function (n) { ledger.append({ kind: "field", turn: turn, op: "remove", name: n }); });
  return { turn: turn, delta: a.delta, flags: a.flags, exclusions: a.exclusions, fieldAdds: a.fieldAdds, fieldRemoves: a.fieldRemoves };
}

/* ───────────── 投影: 台帳 → いまの仕様 (comprehend と同じ形) ───────────── */
function shannonBits(p) { var H = 0, s = 0, i; for (i = 0; i < p.length; i++) s += p[i]; for (i = 0; i < p.length; i++) if (p[i] > 0) { var q = p[i] / s; H -= q * Math.log2(q); } return H; }

function projectSpec(ledger) {
  var h = ledger.horizon(), facts = ledger.read(function (f) { return f.t >= h; });
  var says = facts.filter(function (f) { return f.kind === "say"; });
  if (!says.length) return null;
  var mod = {}, modOrder = [], feat = {}, featOrder = [], plat = {}, platOrder = [];
  var entity = "", fields = [], fieldsAssumed = true, fieldsTurn = -1, theme = { mode: "dark", accent: "#8fd0ff", accentName: "" };
  var title = "", purpose = "", clauses = [], unresolved = [], fallback = [], turnsSpec = 0, evidence = {};
  var prior = [], order = MODULE_DEFS.map(function (d) { return d.id; }).concat(["records"]);
  function belief() {
    var eps = 0.05, p = order.map(function (id) { var m = mod[id]; if (m && m.state === "off") return 0; return eps + (evidence[id] || 0); });
    return shannonBits(p);
  }
  prior.push(belief()); /* 未知事前: 一様 (最大エントロピー) */
  facts.forEach(function (f) {
    if (f.kind === "spec") {
      turnsSpec++;
      f.modules.forEach(function (m) { if (!mod[m.id]) modOrder.push(m.id); mod[m.id] = { state: "on", turn: f.turn, label: m.label, icon: m.icon, reason: m.reason }; evidence[m.id] = (evidence[m.id] || 0) + 1; });
      if (f.fallback && f.fallback.length && !fallback.length) fallback = f.fallback;
      if (f.entity && f.modules.some(function (m) { return m.id === "records"; })) entity = f.entity;
      if (f.flags && !f.flags.fieldsAssumed && f.fields.length) { fields = f.fields.map(function (x) { return { name: x.name, type: x.type }; }); fieldsAssumed = false; fieldsTurn = f.turn; }
      else if (fieldsAssumed && f.fields.length && !fields.length) { fields = f.fields.map(function (x) { return { name: x.name, type: x.type }; }); fieldsTurn = f.turn; }
      f.features.forEach(function (x) {
        if (x.assumed) { if (!feat[x.id]) { featOrder.push(x.id); feat[x.id] = { state: "on", assumed: true, turn: f.turn, label: x.label, reason: x.reason }; } return; }
        if (!feat[x.id]) featOrder.push(x.id); feat[x.id] = { state: "on", assumed: false, turn: f.turn, label: x.label, reason: x.reason };
      });
      if (f.theme && f.flags && f.flags.themeMentioned) theme.mode = f.theme.mode;
      if (f.theme && f.flags && f.flags.accentMentioned) { theme.accent = f.theme.accent; theme.accentName = f.theme.accentName; }
      f.platforms.forEach(function (p) { if (!plat[p]) platOrder.push(p); plat[p] = { state: "on", turn: f.turn }; });
      if (f.title) title = f.title;
      if (!purpose && f.purpose) purpose = f.purpose;
      f.clauses.forEach(function (c) { clauses.push({ text: c.text, hits: c.hits.slice(), turn: f.turn }); });
      f.unresolved.forEach(function (u) { if (unresolved.indexOf(u) < 0) unresolved.push(u); });
      prior.push(belief());
    } else if (f.kind === "exclude") {
      if (f.target === "module") { if (!mod[f.id]) modOrder.push(f.id); mod[f.id] = Object.assign({}, mod[f.id] || { label: f.label, icon: "" }, { state: "off", turn: f.turn }); evidence[f.id] = 0; }
      if (f.target === "feature") { if (!feat[f.id]) featOrder.push(f.id); feat[f.id] = Object.assign({}, feat[f.id] || { label: f.label, reason: "" }, { state: "off", turn: f.turn }); }
      if (f.target === "platform") { if (!plat[f.id]) platOrder.push(f.id); plat[f.id] = { state: "off", turn: f.turn }; }
      prior.push(belief());
    } else if (f.kind === "field") {
      if (f.op === "add") { if (!fields.some(function (x) { return x.name === f.name; })) fields.push({ name: f.name, type: f.type || fieldType(f.name) }); fieldsAssumed = false; fieldsTurn = f.turn; }
      else fields = fields.filter(function (x) { return x.name !== f.name; });
    }
  });
  var spec = { version: BGT_VERSION, input: says.map(function (s) { return s.text; }).join("\n"), turns: says.map(function (s) { return { t: s.t, src: s.src, text: s.text }; }),
    title: "", purpose: purpose, modules: [], entity: "", fields: [], features: {}, theme: theme, platforms: [], clauses: [], coverage: 0, assumptions: [], unresolved: unresolved.slice(),
    ledger: { facts: ledger.size(), horizon: h, turns: says.length, priorEntropy: prior, excluded: [] } };
  modOrder.forEach(function (id) { var m = mod[id]; if (m.state === "on") spec.modules.push({ id: id, label: m.label, icon: m.icon, reason: m.reason + " (第 " + (says.findIndex(function (s) { return s.t === m.turn; }) + 1) + " 発話)", turn: m.turn }); else spec.ledger.excluded.push({ target: "module", id: id, label: m.label }); });
  if (!spec.modules.length) {
    if (fallback.length) { spec.modules = fallback.map(function (m) { return { id: m.id, label: m.label, icon: m.icon, reason: m.reason }; }); spec.assumptions.push("依頼から具体的な機能が読み取れなかったため、汎用の「メモ + ToDo」アプリとして構成しました。"); }
    else { spec.modules = [{ id: "notes", label: "メモ", icon: "📝", reason: "モジュールがすべて除外されたため (仮定)" }]; spec.assumptions.push("モジュールがすべて除外されたため、メモだけのアプリとして構成しました。"); }
  }
  var hasRecords = spec.modules.some(function (m) { return m.id === "records"; });
  if (hasRecords) {
    spec.entity = entity || "データ";
    spec.fields = fields.length ? fields.map(function (x) { return { name: x.name, type: x.type || fieldType(x.name) }; }) : [{ name: "名前", type: "string" }, { name: "日付", type: "date" }, { name: "メモ", type: "text" }];
    if (fieldsAssumed) spec.assumptions.push("項目の指定がないため、「" + spec.entity + "」の一般的な項目 (" + spec.fields.map(function (f) { return f.name; }).join("・") + ") を用意しました。");
  }
  spec.fields.forEach(function (f, i) { f.key = "f" + i; });
  featOrder.forEach(function (id) { var x = feat[id]; if (x.state === "on") spec.features[id] = { label: x.label, reason: x.reason, assumed: !!x.assumed }; else spec.ledger.excluded.push({ target: "feature", id: id, label: x.label }); });
  var dataMods = spec.modules.some(function (m) { return ["records", "notes", "todo", "budget"].indexOf(m.id) >= 0; });
  if (dataMods) ["search", "sort", "export"].forEach(function (id) { if (!feat[id]) { var d = FEATURE_DEFS.filter(function (x) { return x.id === id; })[0]; spec.features[id] = { label: d.label, reason: "データを扱うアプリの標準機能 (仮定)", assumed: true }; } });
  if (spec.modules.some(function (m) { return m.id === "budget"; }) && !spec.features.chart && !(feat.chart && feat.chart.state === "off")) spec.features.chart = { label: "グラフ・集計", reason: "家計簿の標準機能 (仮定)", assumed: true };
  platOrder.forEach(function (id) { var p = plat[id]; if (p.state === "on") spec.platforms.push(id); else spec.ledger.excluded.push({ target: "platform", id: id, label: id }); });
  if (!spec.platforms.length) {
    var offAll = platOrder.length && platOrder.every(function (id) { return plat[id].state === "off"; });
    spec.platforms = PLATFORM_DEFS.map(function (p) { return p.id; }).filter(function (id) { return !(plat[id] && plat[id].state === "off"); });
    if (!spec.platforms.length) spec.platforms = ["windows"];
    spec.assumptions.push(offAll ? "対象プラットフォームがすべて除外されたため、Windows を対象にしました。" : "対象プラットフォームの指定がないため、Android (APK)・Windows 10/11・Linux の 3 種すべてを対象にしました。");
  }
  spec.title = title || (spec.modules.length === 1 ? (spec.modules[0].id === "records" ? spec.entity + "の管理" : spec.modules[0].label) + "アプリ"
    : spec.modules.slice(0, 3).map(function (m) { return m.id === "records" ? spec.entity + "管理" : m.label; }).join("・") + " アプリ");
  spec.clauses = clauses;
  var covered = clauses.filter(function (c) { return c.hits.length; }).length;
  spec.coverage = clauses.length ? covered / clauses.length : 1;
  if (spec.unresolved.length) spec.assumptions.push("解釈できなかった節 " + spec.unresolved.length + " 件は、アプリ内「この依頼について」と論文の「限界」に原文のまま記載しました。");
  spec.assumptions.push("この仕様は会話台帳 (事実 " + spec.ledger.facts + " 件・発話 " + spec.ledger.turns + " 回) の投影です。除外された要素 " + spec.ledger.excluded.length + " 件は台帳に残っています。");
  return spec;
}

/* 1 ターンの差分を短く言う (チャットの返答用) */
function describeTurn(said, spec) {
  var parts = [];
  if (said.delta && said.flags && !said.flags.fallbackModules && said.delta.modules.length) parts.push("+" + said.delta.modules.map(function (m) { return m.label; }).join("・"));
  if (said.delta) { var fx = Object.keys(said.delta.features).filter(function (id) { return !said.delta.features[id].assumed; }); if (fx.length) parts.push("+" + fx.map(function (id) { return said.delta.features[id].label; }).join("・")); }
  if (said.delta && said.flags && !said.flags.platformsAssumed && said.delta.platforms.length) parts.push("+" + said.delta.platforms.join("・"));
  if (said.fieldAdds.length) parts.push("+項目 " + said.fieldAdds.join("・"));
  if (said.exclusions.length) parts.push("−" + said.exclusions.map(function (e) { return e.label; }).join("・"));
  if (said.fieldRemoves.length) parts.push("−項目 " + said.fieldRemoves.join("・"));
  return parts.join(" ") || "(仕様の変更なし)";
}
