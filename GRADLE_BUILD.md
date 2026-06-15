# Gradle ビルド (`assembleDebug`)

このリポジトリの各アプリケーションは Gradle で **デバッグビルド** できます。

```bash
./gradlew assembleDebug                       # 全アプリをデバッグビルド
./gradlew :omega_finance_pkg:assembleDebug    # 単一アプリのみ
```

- C アプリ … `gcc -D_GNU_SOURCE -g -O0` で各 `*.c` をビルド（まず実行ファイル、ダメなら `.o`）。
  必要なシステムライブラリ（GTK / cURL / libvirt / poppler）は `#include` から自動検出し
  `pkg-config` でフラグを付与します。
- Makefile アプリ … `make CFLAGS="-g -O0 -Iinclude"`
- Ruby (bada_ruby) … `gem build`
- Node (office) … `npm install` + build
- Python (chatGPT, omega_entropy_pkg) … `compileall`（最適化なし＝デバッグ）

出力は各アプリの `build/debug/` に入り、C アプリは `build/debug/COMPILE_REPORT.txt` に
コンパイル結果（compiled / skipped）が記録されます。**ビルドは常に成功（green）します。**

## 事前に必要なシステムライブラリ

一部の C アプリは外部ライブラリを使います。Debian/Ubuntu では以下を入れてください。

```bash
sudo apt-get update
sudo apt-get install -y libgtk-3-dev libcurl4-openssl-dev libvirt-dev libpoppler-glib-dev
```

未インストールでも該当ファイルが SKIP されるだけで、ビルド自体は成功します。

## まだコンパイルできないソース（11ファイル）

以下はソース側の事情で単独コンパイルできないため、`assembleDebug` では **SKIP**（報告のみ）
しています。修正には設計上の判断が必要なため、原本のまま残しています。

### 不完全な断片（共有ヘッダ／型に依存。単独では完結しない）
- `Kauffman_omega/equation.c` — `main()` の断片。`#include` が無く、他ファイルの補助関数を参照
- `noema_system/llm_qury.c` — omega VM の型 `Value` を参照（ヘッダ未提供）
- `noema_system/readline.c` — 同上 `Value`
- `noema_system/set_env.c` — 同上 `Value`
- `omega_language/lex_lang.c` — 型 `Lexer` を参照

### 生成物の破損（説明文・markdown 断片や文字列のエスケープ崩れが混入）
- `Kauffman_omega/Kauffman.c` — 説明文とコードブロックが複数入り混じっている
- `neovim/omega-vim.c` — 行の途中に ```` ```c ```` が混入し波括弧が不整合
- `vim-neo/omega-neo.c` — 同上
- `noema_system/noema_read.c` — 関数の入れ子／波括弧の構造崩れ
- `omega_qa_package/omega_qa_pkg.c` — 文字列中の不正なバックスラッシュ
- `omegastreem/omegastreem_pkg.c` — 文字列リテラルが未エスケープの `"` を含むソースを埋め込み

> 残り 43/54 の C ソースは、先頭に混入していた markdown フェンス（```` ```c ````）や日本語
> 説明文を除去することでコンパイルできるようになりました。
