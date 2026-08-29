# apps/ — 全 Ω アプリ 統一ネイティブパッケージング

これまでにこのリポジトリで作った **HTML アプリ全部**を、1 つの仕組みで

- **Android** — APK (Cordova, debug ビルド)
- **Windows 10 / 11** — EXE (Electron: NSIS インストーラ + ポータブル)
- **Ubuntu** — AppImage + deb (Electron)

にビルドして、[Releases](https://github.com/masaaki-avnturle/Bada/releases) からダウンロードできるようにします。

> ⚠ いずれのアプリも**概念シミュレーション/アート・非医療**です。

## 仕組み

| ファイル | 役割 |
|:---|:---|
| [`apps.json`](apps.json) | 対象アプリのマニフェスト (id / 製品名 / ソースの場所 / ウィンドウ設定など)。**アプリを増やすときはここに 1 エントリ追加するだけ** |
| [`wrapper/`](wrapper/) | 汎用 Electron ラッパー (Windows / Ubuntu 共通)。ビルド時に各アプリの HTML を `www/` として同梱 |
| [`wrapper/electron-builder.config.js`](wrapper/electron-builder.config.js) | `BADA_*` 環境変数で 1 アプリ分に特殊化される electron-builder 設定 |
| [`tools/gen-config.js`](tools/gen-config.js) | `apps.json` から Cordova `config.xml` / ラッパー `app.json` / 環境変数 / リリースノートを生成 |
| [`../.github/workflows/all-apps-build.yml`](../.github/workflows/all-apps-build.yml) | 全アプリ × 3 プラットフォームを一括ビルドするワークフロー |

## ビルドの実行方法

- **タグを push**: `all-apps-v1.0.0` のようなタグを push すると全ビルドが走り、生成物がその GitHub Release に添付されます。
- **手動実行**: Actions の「Ω all apps build」で `Run workflow`。`release_tag` を入れると Release に添付、空欄なら Actions アーティファクトのみ。

## 収録アプリ (13)

`node apps/tools/gen-config.js notes` で最新の一覧 (ファイル名付き) を出力できます。

| id | アプリ | ソース |
|:---|:---|:---|
| `omega_biofeedback` | Ω-Biofeedback Oracle | `bio_medicine/omega_biofeedback/www` |
| `omega_thermal_trace` | Ω-Thermal Trace | `bio_medicine/omega_thermal_trace/www` |
| `omega_telepathy` | Ω-Telepathy | `bio_medicine/omega_telepathy/www` |
| `omega_attach_station` | Ω-Attach Station | `bio_medicine/omega_attach_station` |
| `omega_codegen` | Ω-Apriori CodeGen Studio | `bio_medicine/omega_codegen` |
| `omega_function_foundry` | Ω-Function Foundry | `bio_medicine/omega_function_foundry` |
| `omega_host_app` | Ω-Host App | `bio_medicine/omega_host_app` |
| `omega_patternforge` | Ω-PatternForge | `bio_medicine/omega_patternforge` |
| `omega_self_evolve` | Ω-SelfEvolve | `bio_medicine/omega_self_evolve` |
| `omega_telomere_forge` | Ω-Telomere Forge | `bio_medicine/omega_telomere_forge` |
| `omega_tomograph` | Ω-Tomograph | `bio_medicine/omega_tomograph` |
| `omega_apriori_injector` | Ω-Apriori Injector Studio | `bio_medicine/omega_apriori_injector` |
| `omega_apriori_cpu` | Ω-Apriori Core | `bio_medicine/omega_apriori_cpu` |

生成されるファイル名 (バージョン `1.0.0` の例):

- Android: `<id>-debug.apk` (例 `omega_tomograph-debug.apk`)
- Windows: `<Product>-1.0.0-x64.exe` (NSIS インストーラ) / `<Product>-1.0.0-portable.exe` (ポータブル)
- Ubuntu: `<Product>-1.0.0-x86_64.AppImage` / `<Product>-1.0.0-amd64.deb`

## 既存の個別ワークフローとの関係

- **ZoneBrowser** ([`zonebrowser-app-build.yml`](../.github/workflows/zonebrowser-app-build.yml))、**Bada C++Builder** ([`cppbuilder-app-build.yml`](../.github/workflows/cppbuilder-app-build.yml))、**Bada GUI IDE** ([`bada-ide-build.yml`](../.github/workflows/bada-ide-build.yml)) は、すでに APK / Windows / Ubuntu の 3 プラットフォームを個別ワークフローでビルドしています (そのまま利用可)。
- 旧 [`omega-apps-build.yml`](../.github/workflows/omega-apps-build.yml) (Ω アプリ 3 本 · APK + Windows のみ) は本仕組みに**置き換え**られます。`all-apps-build.yml` は同じ 3 本を Ubuntu 込みでビルドします。

## Android APK のインストール

debug 署名の APK なので、端末の「提供元不明のアプリ」を許可してインストールしてください。

## Ubuntu での実行

```bash
chmod +x Omega-Tomograph-1.0.0-x86_64.AppImage && ./Omega-Tomograph-1.0.0-x86_64.AppImage
# または
sudo apt install ./Omega-Tomograph-1.0.0-amd64.deb
```
