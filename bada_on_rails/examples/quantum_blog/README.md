# quantum_blog — Bada on Rails サンプルアプリ

量子ブログ。全コードが Bada 言語 (+ .bada.erb) です。

```sh
node ../../bin/bada-rails server -p 2300      # このディレクトリで
# または リポジトリルートから:
node bada_on_rails/bin/bada-rails server --root bada_on_rails/examples/quantum_blog -p 2300
```

| URL | 内容 |
|:--|:--|
| `/` `/posts` | 記事 CRUD + Akashic 台帳の末尾表示 |
| `/posts/new` | ステータスに **superposed** を選ぶと draft/published の重ね合わせのまま保存され、最初の読み出しで測定・確定 |
| `/quantum` | 分岐オブジェクト: 3 状態の重ね合わせ + 位相回転 + Born 則測定 |
| `/lucky` | ルート先が分岐オブジェクト — リクエストごとにどのアクションが応答するか測定される |

初回起動時に `db/seeds.bada` が 3 記事 (うち 1 つは重ね合わせステータス) を投入します。
DB は追記専用の `db/akashic.jsonl` (git 管理外)。
