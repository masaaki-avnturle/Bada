/*
 * codegen.js — BadaGPT電信「ソースコード化」
 *
 * 思考入力から全体把握した仕様 (spec) を、実際に動く / 構文的に正しい
 * ソースコードに変換する。文章化された思いを、人が読めて実行できる
 * ソースコードにするのが目的。
 *
 *   generateSource(spec, lang) → { lang, label, ext, files:[{path,data}], run, note }
 *     lang = "python" | "node" | "bada"
 *
 * 記録・管理 (records) を主とする仕様は、項目ごとの入力・一覧・検索・
 * 並べ替え・CSV / JSON 書き出しを持つ完全に動く CLI アプリとして生成する。
 * それ以外の仕様は、仕様 (モジュール・機能) をデータとして埋め込み、
 * 構文的に正しく実行できる雛形 (scaffold) として生成し、拡張点を TODO で示す。
 * Bada はいずれの場合も Bada 言語のプログラムを生成する (BadaInterp で実行可能)。
 *
 * 正直な範囲: records の CLI は実際に動く。その他のモジュール (タイマー・
 * お絵かき等) は言語とデバイスに依存するため、ここでは仕様を反映した雛形を
 * 生成し、完成した動作は HTML アプリ版が担う旨をコメントに明記する。
 */
"use strict";

var CODE_LANGS = [
  { id: "python", label: "Python (CLI)", ext: "py", run: "python3 {file}" },
  { id: "node", label: "Node.js (CLI)", ext: "js", run: "node {file}" },
  { id: "bada", label: "Bada 言語", ext: "bada", run: "(Bada VM / BadaGPT電信の量子ラボ)" }
];
var TYPE_LABEL = { string: "文字列", text: "長文", number: "数値", date: "日付 (YYYY-MM-DD)", bool: "y/n", rating: "1〜5" };

function cgHeader(spec, mark) {
  var first = String(spec.input || "").split("\n")[0].slice(0, 80);
  return [mark + " " + spec.title + " — BadaGPT電信が思考入力から生成したソースコード",
    mark + " 依頼 (思考入力): " + first,
    mark + " 生成: BadaGPT電信 v" + BGT_VERSION + " · データは端末内のファイルに保存・ネットワーク通信なし"];
}
function isRecords(spec) { return spec.modules.some(function (m) { return m.id === "records"; }) && spec.fields && spec.fields.length; }
function pyStr(s) { return JSON.stringify(String(s)); }

/* ───────────── Python ───────────── */
function genPython(spec) {
  var H = cgHeader(spec, "#");
  if (isRecords(spec)) {
    var fields = spec.fields.map(function (f) { return '    {"key": ' + pyStr(f.key) + ', "name": ' + pyStr(f.name) + ', "type": ' + pyStr(f.type) + "}"; }).join(",\n");
    var feat = spec.features || {};
    var L = [
      "#!/usr/bin/env python3", "# -*- coding: utf-8 -*-"
    ].concat(H).concat([
      '"""' + spec.entity + " を記録・管理する CLI アプリ。python3 で実行してください。\"\"\"",
      "import json, os",
      "",
      "FIELDS = [",
      fields,
      "]",
      "STORE = " + pyStr(slugify(spec.title) + ".json"),
      "",
      "def load():",
      "    if os.path.exists(STORE):",
      "        with open(STORE, encoding='utf-8') as f:",
      "            return json.load(f)",
      "    return []",
      "",
      "def save(items):",
      "    with open(STORE, 'w', encoding='utf-8') as f:",
      "        json.dump(items, f, ensure_ascii=False, indent=2)",
      "",
      "def prompt_type(t):",
      "    return {" + Object.keys(TYPE_LABEL).map(function (k) { return pyStr(k) + ": " + pyStr(TYPE_LABEL[k]); }).join(", ") + "}.get(t, t)",
      "",
      "def add(items):",
      "    rec = {}",
      "    for fld in FIELDS:",
      "        rec[fld['key']] = input('  %s (%s): ' % (fld['name'], prompt_type(fld['type'])))",
      "    items.append(rec); save(items); print('  保存しました (%d 件)' % len(items))",
      "",
      "def show(rows):",
      "    if not rows:",
      "        print('  (該当なし)'); return",
      "    for i, it in enumerate(rows):",
      "        line = ' / '.join('%s=%s' % (f['name'], it.get(f['key'], '')) for f in FIELDS)",
      "        print('  [%d] %s' % (i, line))",
      ""
    ]);
    if (feat.search) L = L.concat(["def search(items):", "    q = input('  検索語: ').strip()", "    show([it for it in items if any(q in str(v) for v in it.values())])", ""]);
    if (feat.sort) L = L.concat(["def sort_items(items):", "    key = input('  並べ替えるキー (" + spec.fields.map(function (f) { return f.key; }).join("/") + "): ').strip()", "    show(sorted(items, key=lambda it: it.get(key, '')))", ""]);
    if (feat.export) L = L.concat([
      "def export_csv(items):",
      "    import csv",
      "    path = " + pyStr(slugify(spec.title) + ".csv"),
      "    with open(path, 'w', newline='', encoding='utf-8-sig') as f:",
      "        w = csv.writer(f); w.writerow([fl['name'] for fl in FIELDS])",
      "        for it in items: w.writerow([it.get(fl['key'], '') for fl in FIELDS])",
      "    print('  書き出しました: ' + path)",
      ""]);
    var menu = ["[a]追加", "[l]一覧"].concat(feat.search ? ["[s]検索"] : []).concat(feat.sort ? ["[o]並べ替え"] : []).concat(feat.export ? ["[e]CSV"] : []).concat(["[q]終了"]).join(" ");
    L = L.concat([
      "def main():",
      "    items = load()",
      "    print(" + pyStr(spec.title) + ")",
      "    while True:",
      "        try:",
      "            cmd = input('" + menu + " > ').strip().lower()",
      "        except EOFError:",
      "            break",
      "        if cmd == 'a': add(items)",
      "        elif cmd == 'l': show(items)"
    ]);
    if (feat.search) L.push("        elif cmd == 's': search(items)");
    if (feat.sort) L.push("        elif cmd == 'o': sort_items(items)");
    if (feat.export) L.push("        elif cmd == 'e': export_csv(items)");
    L = L.concat([
      "        elif cmd == 'q': break",
      "        else: print('  不明なコマンド')",
      "",
      "if __name__ == '__main__':",
      "    main()",
      ""
    ]);
    return L.join("\n");
  }
  /* 雛形 */
  var mods = spec.modules.map(function (m) { return m.id; });
  var feats = Object.keys(spec.features || {});
  return ["#!/usr/bin/env python3", "# -*- coding: utf-8 -*-"].concat(H).concat([
    "# records 以外のモジュール (" + mods.join(", ") + ") は言語・デバイスに依存するため、",
    "# ここでは仕様を反映した雛形を生成します。完成した動作は HTML アプリ版が担います。",
    "SPEC = {",
    "    'title': " + pyStr(spec.title) + ",",
    "    'modules': " + JSON.stringify(mods) + ",",
    "    'features': " + JSON.stringify(feats) + ",",
    "    'theme': " + pyStr(spec.theme.mode) + ",",
    "    'platforms': " + JSON.stringify(spec.platforms) + ",",
    "}",
    "",
    "def main():",
    "    print('アプリ:', SPEC['title'])",
    "    print('作るモジュール:', ', '.join(SPEC['modules']))",
    "    for feat in SPEC['features']:",
    "        print('TODO: 機能を実装 ->', feat)",
    "    print('見た目:', SPEC['theme'], '/ 対象:', ', '.join(SPEC['platforms']))",
    "",
    "if __name__ == '__main__':",
    "    main()",
    ""
  ]).join("\n");
}

/* ───────────── Node.js ───────────── */
function genNode(spec) {
  var H = cgHeader(spec, "//");
  if (isRecords(spec)) {
    var feat = spec.features || {};
    var fields = spec.fields.map(function (f) { return "  { key: " + JSON.stringify(f.key) + ", name: " + JSON.stringify(f.name) + ", type: " + JSON.stringify(f.type) + " }"; }).join(",\n");
    var L = ["#!/usr/bin/env node", '"use strict";'].concat(H).concat([
      "const fs = require(\"fs\"), readline = require(\"readline\");",
      "const FIELDS = [",
      fields,
      "];",
      "const STORE = " + JSON.stringify(slugify(spec.title) + ".json") + ";",
      "function load() { try { return JSON.parse(fs.readFileSync(STORE, \"utf8\")); } catch (e) { return []; } }",
      "function save(items) { fs.writeFileSync(STORE, JSON.stringify(items, null, 2)); }",
      "const rl = readline.createInterface({ input: process.stdin });",
      "const _q = []; let _w = null;",
      "rl.on(\"line\", (l) => { if (_w) { const w = _w; _w = null; w(l); } else _q.push(l); });",
      "rl.on(\"close\", () => { if (_w) { const w = _w; _w = null; w(null); } });",
      "function ask(q) { process.stdout.write(q); return new Promise((res) => { if (_q.length) res(_q.shift()); else _w = res; }); }",
      "function show(rows) {",
      "  if (!rows.length) { console.log(\"  (該当なし)\"); return; }",
      "  rows.forEach((it, i) => console.log('  [' + i + '] ' + FIELDS.map((f) => f.name + '=' + (it[f.key] || '')).join(' / ')));",
      "}",
      "async function add(items) {",
      "  const rec = {};",
      "  for (const f of FIELDS) rec[f.key] = (await ask('  ' + f.name + ' (' + f.type + '): ')) || '';",
      "  items.push(rec); save(items); console.log('  保存しました (' + items.length + ' 件)');",
      "}"
    ]);
    if (feat.search) L = L.concat(["async function search(items) {", "  const q = ((await ask('  検索語: ')) || '').trim();", "  show(items.filter((it) => Object.values(it).some((v) => String(v).includes(q))));", "}"]);
    if (feat.sort) L = L.concat(["async function sortItems(items) {", "  const k = ((await ask('  並べ替えるキー (" + spec.fields.map(function (f) { return f.key; }).join("/") + "): ')) || '').trim();", "  show(items.slice().sort((a, b) => String(a[k] || '').localeCompare(String(b[k] || ''), 'ja')));", "}"]);
    if (feat.export) L = L.concat([
      "function exportCsv(items) {",
      "  const path = " + JSON.stringify(slugify(spec.title) + ".csv") + ";",
      "  const q = (v) => /[\",\\n]/.test(String(v)) ? '\"' + String(v).replace(/\"/g, '\"\"') + '\"' : String(v == null ? '' : v);",
      "  const csv = '\\uFEFF' + [FIELDS.map((f) => q(f.name)).join(',')].concat(items.map((it) => FIELDS.map((f) => q(it[f.key])).join(','))).join('\\n');",
      "  fs.writeFileSync(path, csv); console.log('  書き出しました: ' + path);",
      "}"]);
    var menu = ["[a]追加", "[l]一覧"].concat(feat.search ? ["[s]検索"] : []).concat(feat.sort ? ["[o]並べ替え"] : []).concat(feat.export ? ["[e]CSV"] : []).concat(["[q]終了"]).join(" ");
    L = L.concat([
      "async function main() {",
      "  const items = load();",
      "  console.log(" + JSON.stringify(spec.title) + ");",
      "  for (;;) {",
      "    const line = await ask('" + menu + " > ');",
      "    if (line === null) { rl.close(); break; }",
      "    const cmd = line.trim().toLowerCase();",
      "    if (cmd === 'a') await add(items);",
      "    else if (cmd === 'l') show(items);"
    ]);
    if (feat.search) L.push("    else if (cmd === 's') await search(items);");
    if (feat.sort) L.push("    else if (cmd === 'o') await sortItems(items);");
    if (feat.export) L.push("    else if (cmd === 'e') exportCsv(items);");
    L = L.concat([
      "    else if (cmd === 'q') { rl.close(); break; }",
      "    else console.log('  不明なコマンド');",
      "  }",
      "}",
      "main();",
      ""
    ]);
    return L.join("\n");
  }
  var mods = spec.modules.map(function (m) { return m.id; });
  return ["#!/usr/bin/env node", '"use strict";'].concat(H).concat([
    "// records 以外のモジュール (" + mods.join(", ") + ") は言語・デバイスに依存するため、",
    "// ここでは仕様を反映した雛形を生成します。完成した動作は HTML アプリ版が担います。",
    "const SPEC = " + JSON.stringify({ title: spec.title, modules: mods, features: Object.keys(spec.features || {}), theme: spec.theme.mode, platforms: spec.platforms }, null, 2) + ";",
    "function main() {",
    "  console.log('アプリ:', SPEC.title);",
    "  console.log('作るモジュール:', SPEC.modules.join(', '));",
    "  SPEC.features.forEach((f) => console.log('TODO: 機能を実装 ->', f));",
    "  console.log('見た目:', SPEC.theme, '/ 対象:', SPEC.platforms.join(', '));",
    "}",
    "main();",
    ""
  ]).join("\n");
}

/* ───────────── Bada 言語 ───────────── */
function genBada(spec) {
  var H = cgHeader(spec, "#");
  var L = H.slice();
  L.push("set entropy   = 3.00");
  L.push("set crossings = 5");
  L.push("set app       = 0");
  L.push('app <- "' + String(spec.title).replace(/"/g, "'") + '"');
  L.push("app -< 1.0");
  L.push("app >- app");
  L.push("Omega::push app as app_node");
  L.push("print app");
  spec.modules.forEach(function (m, i) {
    L.push("set mod_" + i + " = " + (i + 1));
    L.push('mod_' + i + ' <- "' + m.id + '"');
    L.push("Omega::push mod_" + i + " as module_node");
  });
  (spec.fields || []).forEach(function (f, i) {
    L.push("set field_" + i + " = " + (i + 1));
    L.push('field_' + i + ' <- "' + f.name + ":" + f.type + '"');
    L.push("Omega::push field_" + i + " as field_node");
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

function generateSource(spec, lang) {
  var def = CODE_LANGS.filter(function (l) { return l.id === lang; })[0] || CODE_LANGS[0];
  var code = def.id === "python" ? genPython(spec) : def.id === "node" ? genNode(spec) : genBada(spec);
  var slug = slugify(spec.title), fname = "app." + def.ext;
  var note = isRecords(spec) || def.id === "bada"
    ? (def.id === "bada" ? "Bada 言語のプログラム。BadaInterp / 量子ラボで実行できます。" : "実際に動く CLI アプリです。" + def.run.replace("{file}", fname) + " で実行してください。")
    : "records 以外のモジュールは仕様を反映した雛形です (構文は正しく実行できます)。完成した動作は HTML アプリ版が担います。";
  var files = [{ path: fname, data: code }];
  return { lang: def.id, label: def.label, ext: def.ext, files: files, run: def.run.replace("{file}", fname), note: note };
}

/* 全言語のソース + 依頼文を 1 つの ZIP 用ファイル配列にする */
function sourceProject(spec) {
  var files = [];
  CODE_LANGS.forEach(function (l) {
    var g = generateSource(spec, l.id);
    files.push({ path: l.id + "/" + g.files[0].path, data: g.files[0].data });
  });
  files.push({ path: "README.txt", data: [spec.title, "", "思考入力から BadaGPT電信が生成したソースコード。", "", "python/app.py : " + CODE_LANGS[0].run.replace("{file}", "python/app.py"), "node/app.js  : " + CODE_LANGS[1].run.replace("{file}", "node/app.js"), "bada/app.bada: Bada 言語 (BadaInterp / 量子ラボ)", "", "依頼:", String(spec.input || "")].join("\n") });
  return files;
}
