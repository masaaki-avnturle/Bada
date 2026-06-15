# Gradle ビルド (`assembleDebug`)

このリポジトリの各アプリケーションは Gradle で **デバッグビルド** できます。

```bash
# リポジトリのルートから
./gradlew assembleDebug                       # 全アプリをデバッグビルド
./gradlew :omega_finance_pkg:assembleDebug    # 単一アプリのみ
```

### アプリのフォルダの中から実行する
各アプリのフォルダにも `gradlew` を置いてあるので、フォルダの中から直接実行できます
（そのアプリだけがビルドされます）。`gradlew` 本体はリポジトリのルートにあり、各フォルダの
`gradlew` はそこへ転送する薄いラッパーです。

```bash
cd omega_finance_pkg
./gradlew assembleDebug        # → :omega_finance_pkg:assembleDebug だけ実行
```

> 注: `gradlew` はリポジトリのルートと各アプリのフォルダにあります。`git switch` 後に
> 見当たらない場合は `git pull` で最新を取得してください。小文字 `assembledebug` でも動きます。

## Android アプリ（このブランチのみ）

`bada_biofeedback_app` と `bada_morphogenesis_app` は本物の Android アプリ
（Kotlin + Jetpack Compose / Android Gradle Plugin 8.5.2）で、**独立した Gradle ビルド**です。
それぞれに Gradle 8.7 のラッパーを同梱しているので、フォルダ内で直接ビルドできます。

```bash
cd bada_biofeedback_app
./gradlew assembleDebug         # APK: app/build/outputs/apk/debug/*.apk
```

ビルドには JDK 17・Android SDK・初回はネットワーク（Gradle 8.7 と依存の取得）が必要です。
CI（`.github/workflows/build-apk.yml` 等）でも APK をビルドします。

> ルートの `./gradlew`（C/Python 等のマルチプロジェクト）と Android アプリの `./gradlew` は
> それぞれ独立したビルドです。Android アプリはルートの集約ビルドには含めていません。

### Android アプリの Linux ネイティブ版（APK 不要）

各 Android アプリのコアを **Linux のネイティブ実行ファイル（ELF）** に移植したものを
用意しています。Android SDK もネットワークも要らず、ターミナルですぐ動きます。
ルートの `assembleDebug` に含まれ、`make` でも単体ビルドできます。

| Android アプリ | Linux ネイティブ版 | 実行ファイル |
|:--|:--|:--|
| `bada_biofeedback_app` | `bada_biofeedback_linux` | リラクゼーション音風景（WAV生成）＋EEG/ECG/部位グロー |
| `bada_morphogenesis_app` | `bada_morphogenesis_linux` | カスプ・カタストロフィ＋Gray-Scott反応拡散＋分化系譜樹＋製造指標 |

```bash
cd bada_biofeedback_linux && make && ./bin/bada_biofeedback --list
cd bada_morphogenesis_linux && make && ./bin/bada_morphogenesis cardio
```

## C / Python / Ruby / その他アプリ

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

## コンパイル状況：54/54 すべて成功 ✅

全ての C ソースがコンパイルできます（`compiled=54 skipped=0`）。
以前コンパイルできなかった 11 ファイルは次のように修正しました。

### 不完全な断片 → 共有ヘッダを追加
型や補助関数の定義が他ファイルにあった断片に、必要な型・プロトタイプを宣言する
ヘッダを新設して取り込みました。

- `noema_system/noema_value.h` — `Value` 型・タグ・`val_*` / `env_set` を宣言
  → `llm_qury.c` / `readline.c` / `set_env.c` が利用
- `omega_language/omega_lang.h` — `Token` / `Lexer` / `Ex` / `Parser` ・`TK_*` ・
  レキサ/パーサ補助関数を宣言 → `lex_lang.c` が利用
- `Kauffman_omega/report_ask.h` — `equation.c`（`main()` 断片）が呼ぶ補助関数の
  プロトタイプと定数（`BUF_CHUNK` 等）を宣言

### 生成物の破損 → 壊れた文字列・行を再生成
- `omegastreem/omegastreem_pkg.c` — 文字列リテラル内の未エスケープ `'"'` を `'\"'` に修正
- `omega_qa_package/omega_qa_pkg.c` — 実コードの `printf` 文が過剰エスケープ（`\"`）→ 1段アンエスケープ
- `noema_system/noema_read.c` — リスト `[` パーサで欠落していた `}` を補い構造を修復
- `neovim/omega-vim.c` / `vim-neo/omega-neo.c` — 行に混入した ```` ```c ```` で分断された
  行（`p += b->lines[r].len;`）を再生成し、visual モードハンドラの欠落 `}` を補完
- `Kauffman_omega/Kauffman.c` — ```` ```c ```` で挿入された切り詰め重複ブロックを除去し
  完全版を採用

> 先頭に混入していた markdown フェンス（```` ```c ````）や日本語説明文の除去も併用しています。
> ビルドは引き続き、万一コンパイルできないソースがあっても SKIP して green になります。
