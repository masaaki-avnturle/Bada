/*
 * plugins.js — 思念会議のプラグイン機構 (拡張機能)
 *
 * プラグインには 2 種類ある。
 *   ・組み込み (JavaScript): Bada XP など、アプリに同梱したもの
 *   ・Bada プラグイン: Bada 言語の拡張トランザクション
 *         @reviser : extension bada { fun 名前 |引数| """コード""" }
 *     で書いたもの。利用者があとから追加でき、同梱の Bada 処理系の中だけで動く
 *     (画面・通信・保存領域には触れられない。実行ステップ数に上限がある)。
 *
 * 拡張点 (フック):
 *   on_message |role, kind, text, seq|   発言が議事録に入るたび。返した文字列が、その発言の「注記」になる
 *   on_command |args|                    発言欄で /<id> 引数 と打ったとき。返した文字列をその端末だけに表示する
 *   on_minutes |count|                   議事録を書き出すとき。返した文字列が、議事録の 1 節になる
 *   on_suggest |left|                    発言欄の内容が変わるたび。入力候補を返す (Bada プラグインは 1 行に 1 候補)
 * Bada プラグインからは、議事録 MINUTES ([役割, 種類, 本文] の配列) と議題 AGENDA、
 * 補助関数 contains(s, sub) / count_of(s, sub) が使える。数値を文字にするには "" + n と書く。
 *
 * Bada プラグインの冒頭には、次の見出しを書く:
 *   # plugin: risk          (/risk の名前になる。英小文字で始まる 2〜20 文字)
 *   # name: リスク見張り
 *   # description: 何をするか
 */
(function (global) {
  "use strict";
  var PRELUDE = [
    "def contains(s, sub) { return str_find(s, sub) >= 0 }",
    "def count_of(s, sub) {",
    "    n := 0",
    "    rest := s",
    "    p := str_find(rest, sub)",
    "    while (p >= 0) { n := n + 1; rest := substr(rest, p + len(sub), len(rest) - p - len(sub)); p := str_find(rest, sub) }",
    "    return n",
    "}", ""].join("\n");
  var HOOKS = ["on_message", "on_command", "on_minutes", "on_suggest"], MAX_SOURCE = 20000, MAX_STEPS = 3000000;
  var lit = function (s) { return JSON.stringify(String(s)); };

  function header(src, key) { var m = String(src).match(new RegExp("^\\s*#\\s*" + key + "\\s*:\\s*(.+)$", "m")); return m ? m[1].trim() : ""; }
  function Host(Bada, opts) { this.Bada = Bada; this.plugins = []; this.onChange = (opts && opts.onChange) || function () {}; }
  var H = Host.prototype;
  H.find = function (id) { return this.plugins.filter(function (p) { return p.id === id; })[0] || null; };
  H.addNative = function (p) { this.plugins.push(Object.assign({ enabled: true, errors: 0 }, p, { kind: "native" })); };
  // Bada プラグインを調べて追加する。{ok, plugin} / {ok:false, error}
  H.addBada = function (src, builtin) {
    src = String(src);
    if (src.length > MAX_SOURCE) return { ok: false, error: "プラグインが大きすぎます (" + MAX_SOURCE + " 文字まで)" };
    var id = header(src, "plugin"), self = this;
    if (!/^[a-z][a-z0-9_]{1,19}$/.test(id)) return { ok: false, error: "冒頭に「# plugin: 名前」が必要です (英小文字で始まる 2〜20 文字の英数字)" };
    if (id === "plugins" || (this.find(id) && this.find(id).kind === "native")) return { ok: false, error: "「" + id + "」という名前は使えません" };
    if (!/@reviser\s*:\s*extension\s+bada\s*\{/.test(src)) return { ok: false, error: "@reviser : extension bada { … } の形で書いてください" };
    if (/@reviser\s*:\s*extension\s+(c|python|java)\b/.test(src)) return { ok: false, error: "このアプリで動くのは bada の拡張だけです" };
    var hooks = HOOKS.filter(function (h) { return new RegExp("fun\\s+" + h + "\\s*\\|").test(src); });
    if (!hooks.length) return { ok: false, error: "フック (on_message / on_command / on_minutes / on_suggest) が 1 つもありません" };
    var r = this.Bada.run(PRELUDE + 'MINUTES := []\nAGENDA := ""\n' + src, { maxSteps: MAX_STEPS });
    if (!r.ok) return { ok: false, error: "Bada の実行エラー: " + (r.error || (r.parseErrors || []).join("; ")) };
    var p = { id: id, name: header(src, "name") || id, description: header(src, "description"), kind: "bada", builtin: !!builtin, source: src, hooks: hooks, enabled: true, errors: 0 };
    var call = function (hook, args, ctx) { return self._call(p, hook, args, ctx); };
    if (hooks.indexOf("on_message") >= 0) p.onMessage = function (m, ctx) { return call("on_message", [lit(m.role || ""), lit(m.kind), lit(m.text), String(m.seq | 0)], ctx); };
    if (hooks.indexOf("on_command") >= 0) p.onCommand = function (args, ctx) { return call("on_command", [lit(args)], ctx); };
    if (hooks.indexOf("on_suggest") >= 0) p.onSuggest = function (left, ctx) {
      var out = call("on_suggest", [lit(left)], ctx); if (!out) return [];
      return out.split("\n").map(function (x) { return x.trim(); }).filter(Boolean).slice(0, 8).map(function (x) { return { text: x, insert: x, p: 0 }; });
    };
    if (hooks.indexOf("on_minutes") >= 0) p.onMinutes = function (ctx) { return call("on_minutes", [String(ctx.msgs.length)], ctx); };
    this.plugins = this.plugins.filter(function (x) { return x.id !== id; }); this.plugins.push(p); this.onChange();
    return { ok: true, plugin: p };
  };
  H._call = function (p, hook, args, ctx) {
    var data = "MINUTES := [" + ctx.msgs.map(function (m) { return "[" + lit(m.role || "") + ", " + lit(m.kind) + ", " + lit(m.text) + "]"; }).join(", ") + "]\nAGENDA := " + lit(ctx.msgs.length ? ctx.msgs[0].text : "") + "\n";
    var r = this.Bada.run(PRELUDE + data + p.source + '\nprint("@@BEGIN")\nprint(' + hook + "(" + args.join(", ") + '))\nprint("@@END")\n', { maxSteps: MAX_STEPS });
    if (!r.ok) throw new Error(r.error || (r.parseErrors || []).join("; "));
    var out = r.output.split("@@BEGIN\n")[1]; if (out === undefined) return null;
    out = out.split("\n@@END")[0].trim();
    return out === "" || out === "nil" || out === "0" || out === "false" ? null : out;
  };
  // 1 つのプラグインのフックを安全に呼ぶ。3 回続けて失敗したプラグインは止める
  H._safe = function (p, fn) {
    try { var v = fn(); p.errors = 0; return v == null || v === "" ? null : String(v); }
    catch (e) { p.errors++; if (p.errors >= 3) { p.enabled = false; this.onChange(); } return "(エラー: " + e.message + (p.enabled ? "" : " — 3 回続いたので止めました") + ")"; }
  };
  H.active = function () { return this.plugins.filter(function (p) { return p.enabled; }); };
  H.notes = function (m, ctx) {
    var self = this, out = [];
    this.active().forEach(function (p) { if (p.onMessage) { var t = self._safe(p, function () { return p.onMessage(m, ctx); }); if (t) out.push({ id: p.id, name: p.name, text: t }); } });
    return out;
  };
  // 入力候補: 入になっているプラグインの on_suggest を集める。[{text, insert, p, from}]
  H.suggest = function (left, ctx) {
    var out = [];
    this.active().forEach(function (p) {
      if (!p.onSuggest) return;
      try { (p.onSuggest(left, ctx) || []).forEach(function (c) { if (c && c.insert) out.push({ text: String(c.text || c.insert), insert: String(c.insert), p: +c.p || 0, from: p.name }); }); p.errors = 0; }
      catch (e) { p.errors++; if (p.errors >= 3) p.enabled = false; }
    });
    return out;
  };
  // "/id 引数" → {name, text}。プラグインの命令でなければ null
  H.command = function (line, ctx) {
    var m = String(line).match(/^\/([a-z][a-z0-9_]*)\s*([\s\S]*)$/); if (!m) return null;
    if (m[1] === "plugins") return { name: "プラグイン", text: this.plugins.map(function (p) { return (p.enabled ? "● " : "○ ") + "/" + p.id + " — " + p.name + (p.description ? ": " + p.description : ""); }).join("\n") || "(なし)" };
    var p = this.find(m[1]);
    if (!p) return { name: "プラグイン", text: "/" + m[1] + " というプラグインはありません。/plugins で一覧を表示します。" };
    if (!p.enabled) return { name: p.name, text: "このプラグインは止めてあります (F9 で入れられます)。" };
    if (!p.onCommand) return { name: p.name, text: "このプラグインに命令はありません。" };
    return { name: p.name, text: this._safe(p, function () { return p.onCommand(m[2], ctx); }) || "(返答なし)" };
  };
  H.minutes = function (ctx) {
    var self = this, out = [];
    this.active().forEach(function (p) { if (p.onMinutes) { var t = self._safe(p, function () { return p.onMinutes(ctx); }); if (t) out.push("## プラグイン: " + p.name + "\n\n" + t); } });
    return out.join("\n\n");
  };
  H.setEnabled = function (id, on) { var p = this.find(id); if (p) { p.enabled = !!on; p.errors = 0; this.onChange(); } };
  H.remove = function (id) { var p = this.find(id); if (!p || p.kind === "native" || p.builtin) return false; this.plugins = this.plugins.filter(function (x) { return x !== p; }); this.onChange(); return true; };
  // 保存用: 利用者が追加したプラグインの本文と、入 / 切
  H.save = function () {
    return JSON.stringify({ user: this.plugins.filter(function (p) { return p.kind === "bada" && !p.builtin; }).map(function (p) { return p.source; }),
                            off: this.plugins.filter(function (p) { return !p.enabled; }).map(function (p) { return p.id; }) });
  };
  H.load = function (json) {
    var self = this, d; try { d = JSON.parse(json); } catch (e) { return; }
    (d.user || []).forEach(function (src) { self.addBada(src, false); });
    (d.off || []).forEach(function (id) { var p = self.find(id); if (p) p.enabled = false; });
  };

  global.BadaPlugins = { Host: Host, PRELUDE: PRELUDE, HOOKS: HOOKS, header: header };
  if (typeof module !== "undefined" && module.exports) module.exports = global.BadaPlugins;
})(typeof window !== "undefined" ? window : globalThis);
