/* ============================================================================
 * generators.js — Bada on Rails ジェネレータ
 *
 *   bada-rails new <dir>                        — アプリスケルトン生成
 *   bada-rails generate scaffold <name> <f:t..> — モデル + コントローラ +
 *                                                 ビュー + RESTful ルート生成
 *
 * 生成されるコードはすべて Bada 言語 (+ .bada.erb テンプレート)。
 * ==========================================================================*/
"use strict";

const fs = require("fs");
const path = require("path");

function write(file, content, log) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
  if (log) log("  create  " + file);
}

function pluralize(name) {
  if (/(s|x|z|ch|sh)$/.test(name)) return name + "es";
  if (/[^aeiou]y$/.test(name)) return name.slice(0, -1) + "ies";
  return name + "s";
}

/* ---------------------------------------------------------------- layout */

function layoutErb(appName) {
  return `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${appName} · Bada on Rails</title>
<link rel="stylesheet" href="/application.css">
</head>
<body>
<header>
  <div class="brand"><a href="/">⟨ψ| ${appName} |ψ⟩</a></div>
  <div class="sub">Bada on Rails — 作用素 &amp; 分岐オブジェクト</div>
</header>
<main>
<%= raw __content %>
</main>
<footer>
  Bada on Rails · 量子プログラミング言語 Bada の Web フレームワーク ·
  Akashic ledger: <%= akashic_len() %> facts (追記専用)
</footer>
</body>
</html>
`;
}

const APPLICATION_CSS = `/* Bada on Rails — 既定スタイル */
:root {
  --bg: #07090f; --panel: #0d111c; --line: #1d2536;
  --gold: #c8a44a; --blue: #4a80d0; --teal: #40b8c0; --text: #e8e2d0; --dim: #8b93a8;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: "Hiragino Kaku Gothic ProN", "Noto Sans JP", system-ui, sans-serif;
  line-height: 1.7;
}
header { padding: 1.2em 2em .8em; border-bottom: 1px solid var(--line); }
.brand { font-size: 1.35em; font-weight: 700; letter-spacing: .04em; }
.brand a { color: var(--gold); text-decoration: none; }
.sub { color: var(--dim); font-size: .85em; }
main { max-width: 860px; margin: 0 auto; padding: 1.5em 2em 3em; }
footer { border-top: 1px solid var(--line); color: var(--dim); font-size: .8em; padding: 1em 2em 2em; }
h1 { color: var(--gold); font-size: 1.4em; border-bottom: 1px solid var(--line); padding-bottom: .35em; }
a { color: var(--blue); }
table { width: 100%; border-collapse: collapse; margin: 1em 0; }
th, td { text-align: left; padding: .45em .6em; border-bottom: 1px solid var(--line); }
th { color: var(--teal); font-weight: 600; font-size: .85em; }
.btn, button {
  display: inline-block; background: var(--panel); color: var(--gold);
  border: 1px solid var(--gold); border-radius: 4px; padding: .3em .9em;
  text-decoration: none; font-size: .9em; cursor: pointer;
}
.btn:hover, button:hover { background: var(--gold); color: var(--bg); }
form.inline { display: inline; }
label { display: block; color: var(--teal); margin-top: .9em; font-size: .9em; }
input[type=text], textarea, select {
  width: 100%; background: var(--panel); border: 1px solid var(--line);
  color: var(--text); border-radius: 4px; padding: .5em; font: inherit;
}
.count, .muted { color: var(--dim); font-weight: 400; }
.ledger { background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
  padding: .8em 1em; font-family: ui-monospace, monospace; font-size: .75em;
  color: var(--dim); overflow-x: auto; white-space: pre; }
.branch { border: 1px dashed var(--teal); border-radius: 6px; padding: .8em 1em; margin: .8em 0; }
.branch .amp { color: var(--teal); font-family: ui-monospace, monospace; }
.badge { border: 1px solid var(--line); border-radius: 999px; padding: .05em .6em; font-size: .8em; color: var(--dim); }
`;

/* ---------------------------------------------------------------- new app */

function newApp(dir, log) {
  const root = path.resolve(dir);
  const appName = path.basename(root);
  if (fs.existsSync(path.join(root, "config", "routes.bada"))) {
    throw new Error(root + " は既に Bada on Rails アプリです (config/routes.bada が存在)");
  }

  write(path.join(root, "config", "routes.bada"),
`# ${appName} のルーティング — Bada on Rails DSL
# (railtie.bada の @reviser : grammar 拡張が定義する構文)

root to: "welcome#index"
`, log);

  write(path.join(root, "app", "controllers", "welcome_controller.bada"),
`# WelcomeController

def welcome_index() {
  greeting := superpose ["こんにちは、Bada on Rails!", "Hello, Bada on Rails!", "⟨ψ| Bada on Rails |ψ⟩"] with [0.4, 0.3, 0.3]
  render_view("welcome/index", ["message", collapse(greeting), "state", branch_state(greeting)])
}
`, log);

  write(path.join(root, "app", "views", "welcome", "index.bada.erb"),
`<h1><%= message %></h1>
<p>このページの見出しは<strong>分岐オブジェクト</strong>です。リクエストごとに
3 つの状態の重ね合わせが準備され、Born 則 (|振幅|&sup2;) で 1 つに収縮します。
測定結果は Akashic 台帳に追記されました。</p>

<div class="branch">
<% each state as s %>
  <div><span class="amp"><%= s[1] %></span> — <%= s[0] %></div>
<% end %>
</div>

<p class="muted">次の一歩: <code>bada-rails generate scaffold post title:string body:text</code></p>
`, log);

  write(path.join(root, "app", "views", "layouts", "application.bada.erb"), layoutErb(appName), log);
  write(path.join(root, "public", "application.css"), APPLICATION_CSS, log);

  write(path.join(root, "db", "seeds.bada"),
`# seeds.bada — 初期データ (boot 時に毎回評価されるので必ずガードする)
`, log);

  write(path.join(root, ".gitignore"), "db/akashic.jsonl\n", log);

  write(path.join(root, "README.md"),
`# ${appName}

Bada on Rails アプリケーション。

\`\`\`sh
bada-rails server            # http://localhost:2300
bada-rails routes            # ルーティング一覧
bada-rails console           # Bada 対話コンソール (rails 作用素つき)
bada-rails generate scaffold post title:string body:text
\`\`\`
`, log);

  return root;
}

/* ---------------------------------------------------------------- scaffold */

function fieldInput(f, recordVar) {
  if (f.type === "text") {
    return `  <label>${f.name}</label>
  <textarea name="${f.name}" rows="5"><%= form_value(${recordVar}, "${f.name}") %></textarea>`;
  }
  return `  <label>${f.name}</label>
  <input type="text" name="${f.name}" value="<%= form_value(${recordVar}, "${f.name}") %>">`;
}

function scaffold(root, rawName, rawFields, log) {
  const name = String(rawName).toLowerCase().replace(/[^a-z0-9_]/g, "");
  if (!name) throw new Error("model 名が不正です");
  const res = pluralize(name);
  const fields = (rawFields.length ? rawFields : ["title:string", "body:text"]).map((s) => {
    const [n, t] = String(s).split(":");
    return { name: n.replace(/[^A-Za-z0-9_]/g, ""), type: (t || "string").toLowerCase() };
  });
  const fieldNames = fields.map((f) => f.name);

  /* --- model --- */
  write(path.join(root, "app", "models", name + ".bada"),
`# ${name} モデル — fields: は strong parameters (許可リスト) を兼ねる
model :${name}, fields: [${fieldNames.map((f) => `"${f}"`).join(", ")}]
`, log);

  /* --- controller --- */
  const formPairs = fieldNames.map((f) => `["${f}", param("${f}")]`).join(", ");
  write(path.join(root, "app", "controllers", res + "_controller.bada"),
`# ${res} コントローラ — Bada on Rails scaffold
# ルート先 "${res}#index" は関数 ${res}_index にディスパッチされる。

def ${res}_form_params() {
  return [${formPairs}]
}

def ${res}_index() {
  render_view("${res}/index", ["${res}", ${name}_all(), "count", ${name}_count()])
}

def ${res}_show() {
  r := ${name}_find(param("id"))
  if (r == nil) { head(404) return }
  render_view("${res}/show", ["record", r])
}

def ${res}_new() {
  render_view("${res}/new", ["record", nil, "action_url", "/${res}", "form_method", "POST"])
}

def ${res}_create() {
  id := ${name}_create(${res}_form_params())
  redirect_to("/${res}/" + id)
}

def ${res}_edit() {
  r := ${name}_find(param("id"))
  if (r == nil) { head(404) return }
  render_view("${res}/edit", ["record", r, "action_url", "/${res}/" + field(r, "id"), "form_method", "PATCH"])
}

def ${res}_update() {
  if (${name}_find(param("id")) == nil) { head(404) return }
  ${name}_update(param("id"), ${res}_form_params())
  redirect_to("/${res}/" + param("id"))
}

def ${res}_destroy() {
  ${name}_destroy(param("id"))
  redirect_to("/${res}")
}
`, log);

  /* --- views --- */
  const cols = fieldNames.slice(0, 2);
  write(path.join(root, "app", "views", res, "index.bada.erb"),
`<h1>${res} <span class="count">(<%= count %>)</span></h1>
<p><a class="btn" href="/${res}/new">＋ 新規 ${name}</a></p>
<table>
  <tr><th>id</th>${cols.map((c) => `<th>${c}</th>`).join("")}<th></th></tr>
<% each ${res} as r %>
  <tr>
    <td><%= field(r, "id") %></td>
${cols.map((c, i) => i === 0
    ? `    <td><a href="/${res}/<%= field(r, "id") %>"><%= field(r, "${c}") %></a></td>`
    : `    <td><%= field(r, "${c}") %></td>`).join("\n")}
    <td>
      <a href="/${res}/<%= field(r, "id") %>/edit">編集</a>
      <form class="inline" method="POST" action="/${res}/<%= field(r, "id") %>">
        <input type="hidden" name="_method" value="DELETE">
        <button>削除</button>
      </form>
    </td>
  </tr>
<% end %>
</table>
`, log);

  write(path.join(root, "app", "views", res, "show.bada.erb"),
`<h1><%= field(record, "${fieldNames[0]}") %></h1>
<table>
${fieldNames.map((f) => `  <tr><th>${f}</th><td><%= field(record, "${f}") %></td></tr>`).join("\n")}
  <tr><th>created_at</th><td><%= field(record, "created_at") %></td></tr>
</table>
<p>
  <a class="btn" href="/${res}/<%= field(record, "id") %>/edit">編集</a>
  <a class="btn" href="/${res}">一覧へ</a>
</p>
`, log);

  write(path.join(root, "app", "views", res, "_form.bada.erb"),
`<form method="POST" action="<%= action_url %>">
  <input type="hidden" name="_method" value="<%= form_method %>">
${fields.map((f) => fieldInput(f, "record")).join("\n")}
  <p><button>保存</button> <a href="/${res}">キャンセル</a></p>
</form>
`, log);

  write(path.join(root, "app", "views", res, "new.bada.erb"),
`<h1>新規 ${name}</h1>
<% partial "${res}/_form" %>
`, log);

  write(path.join(root, "app", "views", res, "edit.bada.erb"),
`<h1>${name} #<%= field(record, "id") %> を編集</h1>
<% partial "${res}/_form" %>
`, log);

  /* --- route --- */
  const routesFile = path.join(root, "config", "routes.bada");
  const line = "resources :" + res;
  let routes = fs.existsSync(routesFile) ? fs.readFileSync(routesFile, "utf8") : "";
  if (routes.indexOf(line) < 0) {
    routes = routes.replace(/\s*$/, "\n") + line + "\n";
    fs.writeFileSync(routesFile, routes);
    if (log) log("  route   " + line);
  }

  return { name, res, fields };
}

module.exports = { newApp, scaffold, pluralize, layoutErb, APPLICATION_CSS };
