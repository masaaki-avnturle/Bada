# ⊕ Bada Reviser PatchGuard — PHP サイトの書き換えの副作用を防ぐパッチ・セキュリティ

**PHP の Web サイトを書き換えるとき、「書き換えの基」と「書き換えた後」をタプルとして台帳に置き、その差をパッチとして扱います。量子プログラミング言語 Bada の `@reviser` で書いたセキュリティ規則がパッチの副作用 (新しい危険関数・エスケープの削除・認可の削除・他のファイルを壊す署名変更など) を検査し、ACCEPT / REVIEW / REJECT を決めます。** 複数回の書き換えは 1 本の正味パッチに**折り畳んで**検査します。合格したファイルだけの部分パッチと、元へ戻す逆パッチも作ります。

- **GUI**: Android / Windows 10・11 / Linux / ブラウザ。依存なし、オフラインで動き、検査するソースは端末の外に出ません。
- **CLI**: サーバーや CI 用。Node 18+ の単一ファイルで、依存はありません。`apply` は SHA-256 で照合し、全ファイルを当てるか 1 つも当てないかのどちらかです。

## 📥 ダウンロード (GitHub Actions)

1. リポジトリの **Actions** タブで **Bada PatchGuard app build** を開きます
2. 最新の成功した実行 (緑のチェック) を開きます
3. ページ下部の **Artifacts** からダウンロードします

| アーティファクト | 中身 | 対象 |
|:---|:---|:---|
| `badapatchguard-android` | `bada-patchguard-debug.apk` | Android 7.0 以上 |
| `badapatchguard-windows` | `BadaPatchGuard-*-x64.exe` (インストーラ) / `BadaPatchGuard-*-portable.exe` | Windows 10 / 11 (x64) |
| `badapatchguard-linux` | `BadaPatchGuard-*-x86_64.AppImage` / `BadaPatchGuard-*-amd64.deb` | Linux (x64) |
| `badapatchguard-cli` | `badapatchguard.js` (単一ファイル CLI) + 例 | Node 18 以上のサーバー / CI |

ブラウザ版は [`index.html`](index.html) を「Download raw file」で保存し、ダブルクリックで開きます。

## 🧭 仕組み

```
 書き換えの基 (base)       書き換えた後 (段 1, 段 2, …)
        │                          │
        ▼  内容を SHA-256 で内容アドレス化して、タプル空間に out
   ["file", run, 0, path, sha]   ["file", run, k, path, sha]
        │                          │
        └──── diff_lines ──────────┘ → ["patch", run, k, path, sha_base, sha_after, +, −]
                     │
   折り畳み  fold(patches, base, |acc, p| patch_apply(acc, p)) == final を検証
                     │
   検査     各段 (監査用) と、正味の base → final (判定用) の両方に @reviser 規則を適用
                     │      相殺 = 途中の段にだけ現れた指摘 / 創発 = 合成で初めて現れた指摘
                     ▼
   門       高以上 → REJECT, 中 → REVIEW, それ以外 → ACCEPT (免除は理由ごとタプルへ)
                     │
   書き出し net.patch / safe.patch (保留ファイルを除き、依存も連鎖除外) / rollback.patch
```

| ファイル | 役割 |
|:---|:---|
| [`src/guard.bada`](src/guard.bada) | **規則・門・タプル空間・折り畳み** (Bada)。`@reviser PATCHGUARD { rule sink … rule sanitizer … rule invariant … }` |
| [`src/php.js`](src/php.js) | PHP の字句解析と事実の抽出: 呼び出し・出力・include・関数定義・認可・大域状態・汚染の伝播 |
| [`src/diff.js`](src/diff.js) | Myers 差分・厳密なパッチ適用・逆パッチ・git 互換 unified diff・SHA-256 |
| [`src/core.js`](src/core.js) | Bada 処理系 (BadaClaude と共有) に組込みを渡して `guard.bada` を動かす |
| [`cli.js`](cli.js) | `check` / `apply` / `rollback` / `rules` |
| [`src/app.js`](src/app.js) + [`src/ui.html`](src/ui.html) | GUI |
| [`examples/`](examples/) | 基・危険な書き換え・安全な書き換え・2 段の折り畳みの例 |
| [`tools/test.js`](tools/test.js) | テスト 63 件 |

### リバイザ (`@reviser`) で文法を拡張する

`guard.bada` の冒頭で、`@reviser` ブロックが 3 つの規則 (`rule`) を台帳に commit します。これ以降、Bada の構文解析器はそれらを**新しい文**として読みます。

```bada
@reviser PATCHGUARD {
  rule sink(name, kind, tainted_sev, plain_sev, why) { … }
  rule sanitizer(name) { … }
  rule invariant(id, title, check) { … }
}

sink "eval", "code", "critical", "high", "文字列を PHP コードとして実行する"
sanitizer "htmlspecialchars"
invariant "PG03", "SQL インジェクション", |d| sink_findings(d, ["sql"])
```

GUI の「規則 (guard.bada)」タブで規則を編集できます。たとえば `sink "mb_send_mail", "cmd", "high", "low", "…"` を足すと、次の検査から効きます。

### 不変量 (書き換えが守るべき性質)

| ID | 検査 | 典型的な重大度 |
|:--|:--|:--|
| PG01 | `eval` / `assert` / `create_function` / `extract` などコード実行の追加 | 致命的 |
| PG02 | `system` / `exec` / `shell_exec` / バッククォートなど OS コマンドの追加 | 致命的 |
| PG03 | `->query` / `mysqli_query` / `->prepare` などへの外部入力の混入 (SQL インジェクション) | 致命的 |
| PG04 | エスケープなしの `echo` / `<?=` / `printf` (XSS)。**既存の出力が書き換えで汚染された場合も検出** | 高 |
| PG05 | パスを外部入力が決める `include` / `require` (LFI / RFI) | 致命的 |
| PG06 | `unserialize` への外部入力 | 高 |
| PG07 | ファイルの読み書き・削除へのパス・トラバーサル | 高 |
| PG08 | 外部通信 (SSRF) | 高 |
| PG09 | 基にあった無害化 (`htmlspecialchars` / `in_array` / `intval` …) の削除 | 中 |
| PG10 | 基にあった認可・CSRF・セッション検査の削除 | 高 |
| PG11 | 関数の削除・必須引数の追加・可視性の縮小が**他のファイルの呼び出し元を壊す** (呼び出し元を特定) | 致命的 / 高 |
| PG12 | `ini_set('display_errors', '1')` など大域状態・設定の変更 | 中 / 高 |
| PG13 | ヘッダ注入・Cookie 属性 | 高 / 低 |
| PG14 | 構文を壊す書き換え (括弧・文字列が閉じていない) | 致命的 |
| PG15 | `md5` / `sha1` / `rand` / `mt_rand` など弱い暗号・予測可能な乱数 | 低 |
| PG16 | まだ `include` されているファイルの削除 | 致命的 |
| PG17 | `phpinfo` / `var_dump` などデバッグ出力の残り | 高 / 低 |

汚染は `$_GET` / `$_POST` / `$_REQUEST` / `$_COOKIE` / `$_FILES`、一部の `$_SERVER`、`php://input` を源泉とし、代入・`foreach`・文字列への埋め込み・heredoc を通じて追跡します。無害化関数や `(int)` などのキャストで包んだ部分は汚染に数えません。

## 💻 CLI

```sh
# 検査 (基・後・…)。--out でパッチと記録を書き出す
node badapatchguard.js check site_before/ site_after/ --out pg-out/
#  → pg-out/{report.json, net.patch, safe.patch, rollback.patch, tuples.jsonl}
#  終了コード: 0 ACCEPT / 1 --fail-on 以上の指摘 (既定 high) / 2 REJECT / 3 使い方の誤り

# 複数回の書き換えを折り畳んで検査
node badapatchguard.js check v1/ v2/ v3/ v4/

# 本番サイトへ適用: 当てた後の木を門で検査し、REJECT なら当てない
node badapatchguard.js apply /var/www/site pg-out/net.patch --dry-run
node badapatchguard.js apply /var/www/site pg-out/safe.patch

# 元に戻す
node badapatchguard.js rollback /var/www/site pg-out/net.patch

# git diff の出力も使える
git diff v1.2 v1.3 -- . > change.patch
node badapatchguard.js apply /var/www/site change.patch
```

`apply` と `rollback` の動作:

- **全か無か**: 各ファイルの基の SHA-256 がパッチの記録と一致しなければ、1 ファイルも書き換えません。本番で誰かが直接編集していた (ドリフトしている) 場合も止まります。
- **門**: 当てた後の木全体を検査し、REJECT なら当てません。`--force` で上書きでき、その事実も記録します。
- **原子的な書き込み**: 一時ファイルに書いてから `rename` します。
- **記録**: 書き換え前の内容は `.patchguard/backup/<sha256>` に保存し、操作は `.patchguard/tuples.jsonl` に追記します (追記のみ)。
- **パスの検査**: サイトの外を指すパス (`../`、絶対パス) は拒否します。

免除 (waiver) は JSON で渡します。理由は必須で、タプルに残ります:

```json
[{ "id": "PG12", "path": "config.php", "match": "display_errors", "reason": "検証環境のみ。本番の php.ini で上書き" }]
```

## 🧪 開発

```sh
node bada_patchguard/tools/build.js     # src/ → index.html と dist/badapatchguard.js
node bada_patchguard/tools/test.js      # 63 件のテスト
node bada_patchguard/cli.js check bada_patchguard/examples/base bada_patchguard/examples/after_risky
```

## ⚖ 正直な範囲

- これは**静的な差分検査**です。PHP を実行するわけではなく、汚染の追跡も 1 ファイル内の近似です。関数の引数を経由する汚染や、フレームワーク固有の無害化 (テンプレートの自動エスケープなど) は見逃したり、誤って指摘したりすることがあります。重要な変更では人によるレビューやテストと組み合わせてください。
- 「受理」は「規則に反する副作用が見つからなかった」という意味で、安全の証明ではありません。
- 構文の検査は括弧と文字列の対応だけで、`php -l` の代わりにはなりません。
