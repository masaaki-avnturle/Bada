# Bada on Rails — 量子プログラミング言語 Bada の Web フレームワーク

**Bada on Rails** は、量子プログラミング言語 **Bada** ([`bada_gui_ide/`](../bada_gui_ide/)
の言語コア) の上に実装した Rails 風フルスタック Web フレームワークです。
アプリケーションコード — ルーティング・モデル・コントローラ・ビュー — は
**すべて Bada 言語** (+ `.bada.erb` テンプレート) で書きます。

3 つの柱:

1. **作用素プログラミング** — フレームワーク API は Bada の
   `@reviser : extension rails { ... }` 拡張トランザクションとして宣言された
   ホスト作用素 (`render_view` / `redirect_to` / `db_create` / `collapse` ...)。
   コントローラのアクションはこれらの作用素をリクエスト状態へ適用する関数です。
2. **分岐オブジェクト** — 値の重ね合わせ `superpose [...] with [...]`。
   複素振幅を持ち、`branch_phase` の位相回転は確率 |amp|² を変えません
   (Bada の性質 (ii))。`collapse` は Born 則の射影測定で、結果は毎回
   **Akashic 台帳へ measurement 事実としてコミット**されます。
   レコードの属性を重ね合わせのまま保存でき、**最初の読み出しで測定・確定**します
   (遅延収縮)。ルート先にも分岐オブジェクトを指定でき、リクエストごとに
   どのアクションが応答するかが測定されます。
3. **Akashic 台帳 (追記専用 DB)** — 永続化は `db/akashic.jsonl` への追記のみ。
   作成・更新・削除 (墓標)・測定がすべて事実 (fact) としてコミットされ、
   現在状態は台帳のリプレイで得られます。tuplespace / Akashic Record の永続版です。

## クイックスタート

Node.js があれば依存ゼロで動きます (`npm install` 不要)。

```sh
# 同梱の量子ブログを起動
node bada_on_rails/bin/bada-rails server --root bada_on_rails/examples/quantum_blog -p 2300
# → http://localhost:2300/         記事一覧 (CRUD + Akashic 台帳)
# → http://localhost:2300/quantum  分岐オブジェクトのデモ
# → http://localhost:2300/lucky    分岐ルート (リクエストごとに測定)

# 新しいアプリを作る
node bada_on_rails/bin/bada-rails new myapp
cd myapp
node ../bada_on_rails/bin/bada-rails generate scaffold post title:string body:text
node ../bada_on_rails/bin/bada-rails server        # http://localhost:2300
node ../bada_on_rails/bin/bada-rails routes        # ルーティング一覧
node ../bada_on_rails/bin/bada-rails console       # Bada 対話コンソール

# テスト
node bada_on_rails/test/run_tests.js
```

## ルーティング — `config/routes.bada`

ルーティング DSL は Bada の **`@reviser : grammar` 文法拡張トランザクション**
([`lib/railtie.bada`](lib/railtie.bada)) が定義します。ルールは解析時ルール台帳へ
追記コミットされ (最新最優先・単調増加)、以後のファイルでこの構文がそのまま
Bada 文になります:

```bada
root to: "posts#index"
get "/quantum", to: "posts#quantum"
resources :posts            # RESTful 7 アクションに展開

# 分岐オブジェクトをルート先に — リクエストごとに Born 則で測定
get "/lucky", to: superpose ["posts#index", "posts#quantum"] with [0.5, 0.5]
```

`get` / `post` / `put` / `patch` / `delete` / `root` / `resources` が使えます。
HTML フォームからの PATCH / DELETE は Rails と同じ `_method` 隠しフィールドで
オーバーライドします。

## モデル — `app/models/*.bada`

```bada
model :post, fields: ["title", "body", "status"]
```

`fields:` は **strong parameters** (許可リスト) を兼ね、宣言にないパラメータは
黙って捨てられます。宣言すると以下のヘルパ作用素が自動定義されます:

| 作用素 | 意味 |
|:--|:--|
| `post_all()` | 全件 (レコード = `[["id","1"], ["title",...], ...]` のペア配列) |
| `post_find(id)` | 1 件 (無ければ `nil`)。**重ね合わせ属性はここで測定・確定** |
| `post_create(pairs)` | create 事実をコミットし id を返す |
| `post_update(id, pairs)` / `post_destroy(id)` / `post_count()` | 〃 |

属性値に分岐オブジェクトを渡すと重ね合わせのまま保存されます:

```bada
post_create([["title", "シュレディンガーの記事"],
             ["status", superpose ["draft", "published"] with [0.5, 0.5]]])
```

## コントローラ — `app/controllers/*_controller.bada`

ルート先 `"posts#show"` は関数 `posts_show` へディスパッチされます:

```bada
def posts_show() {
  r := post_find(param("id"))
  if (r == nil) { head(404) return }
  render_view("posts/show", ["record", r])
}
```

リクエスト作用素: `param(k)` / `params_all()` / `request_method()` / `request_path()`。
レスポンス作用素: `render_view(name, locals)` / `render_html(html)` /
`render_json(value)` / `redirect_to(path)` / `head(status)`。

## ビュー — `app/views/**/*.bada.erb`

ERB 風テンプレートは Bada コードへコンパイルされ、同じセッションで評価されます:

```erb
<h1>記事一覧 (<%= count %>)</h1>
<% each posts as p %>
  <li><a href="/posts/<%= field(p, "id") %>"><%= field(p, "title") %></a></li>
<% end %>
<% if count == 0 %><p>まだ記事がありません</p><% end %>
<% partial "posts/_form" %>
```

- `<%= expr %>` は **既定で HTML エスケープ** (`<%= raw expr %>` で無効化)
- `<% each xs as x %> ... <% end %>`、`<% if %> / <% else %> / <% end %>`
- `<% partial "dir/_name" %>` はコンパイル時インライン展開
- `app/views/layouts/application.bada.erb` があれば `<%= raw __content %>` に本文が入る

## 分岐オブジェクト作用素

| 作用素 | 意味 |
|:--|:--|
| `superpose [v...] with [w...]` | 重ね合わせを準備 (文法拡張構文; 重みは正規化され振幅 √p になる) |
| `branch(values)` | 一様重ね合わせ |
| `collapse(b)` | Born 則の射影測定。恒久確定し、measurement 事実を台帳へコミット |
| `branch_phase(b, i, θ)` | 分岐 i の振幅を位相回転 — 確率は不変 (性質 (ii)) |
| `branch_state(b)` | `[[値, 確率], ...]` |
| `branch_probs(b)` / `branch_values(b)` | 確率 / 値のリスト |

台帳作用素: `akashic_len()` / `akashic_tail(n)`。

## アーキテクチャ

```
bada_on_rails/
  bin/bada-rails        CLI (new / generate scaffold / server / routes / console)
  lib/kernel.js         カーネル: HTTP・ディスパッチ・ERB コンパイラ・
                        Akashic DB (JSONL リプレイ)・BranchSpace (分岐オブジェクト)
  lib/railtie.bada      Bada 側標準ライブラリ: rails FFI 作用素宣言 +
                        @reviser : grammar ルーティング/モデル DSL + シュガー
  lib/generators.js     new / scaffold ジェネレータ
  examples/quantum_blog 量子ブログ (シード済みサンプル)
  test/run_tests.js     結合テスト (node bada_on_rails/test/run_tests.js)
```

カーネルは言語コア `bada_gui_ide/www/bada.js` をそのまま使い、Bada→カーネル呼び出しは
論文 *Reviser-Extensible Grammars* の拡張トランザクション FFI 規約
(JSON over argv/stdout) に従います。つまり **フレームワーク API 自体が
`@reviser : extension` で追記コミットされた拡張事実**であり、`bada-rails console` で
`ledger(tuplespace)` を見るとフレームワークの成り立ちが台帳として読めます。

### 予約語について

ルーティング/モデル DSL は文法拡張なので、`get` / `post` / `put` / `patch` /
`delete` / `root` / `resources` / `model` / `superpose` を**文頭の変数名**に使うのは
避けてください (パーサはバックトラックしますが可読性のため)。scaffold が生成する
コードはローカル名 `record` / `r` を使います。
