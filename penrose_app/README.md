# Penrose Studio — Windows (.exe) と Android (.apk) アプリ

`bada_ruby` の **ペンローズ絵記号スタジオ**（パレットで絵記号を選び、ダイアログで
組み合わせると、清書した方程式と計算した方程式を生成するアプリ）を、
**Windows 10 / 11 の実行ファイル (.exe)** と **Android アプリ (.apk)** として
配布するためのパッケージです。

- **Windows**: Electron + [electron-builder](https://www.electron.build/)（NSIS インストーラ + ポータブル版）
- **Android**: [Capacitor](https://capacitorjs.com/) + Gradle（デバッグ署名 APK・そのままインストール可能）
- どちらも同じ `www/index.html`（外部依存ゼロ・オフライン動作の自己完結アプリ）を読み込みます。

## ⬇️ ダウンロード（利用者向け）

ビルド済みの `.exe` と `.apk` は **GitHub Releases** から入手できます。

1. リポジトリの **Releases** ページを開く
2. 最新リリースの **Assets** から選ぶ
   - `PenroseStudio-Setup-x.y.z.exe` … Windows 用インストーラ
   - `PenroseStudio-x.y.z-portable.exe` … インストール不要のポータブル版
   - `PenroseStudio-vX.Y.Z.apk` … Android 用（設定で「提供元不明のアプリ」を許可してインストール）

> リリースは、メンテナが `vX.Y.Z` のタグを push すると GitHub Actions が
> 自動でビルドして添付します（下記「リリース手順」）。

## 🚀 リリース手順（メンテナ向け）

タグを打つだけで、Windows と Android のビルドが走り Release に添付されます。

```bash
git tag v1.0.0
git push origin v1.0.0
```

- ワークフロー: [`.github/workflows/release.yml`](../.github/workflows/release.yml)
- `windows` ジョブ（`windows-latest`）が `.exe` を、`android` ジョブ（`ubuntu-latest`）が `.apk` をビルド。
- 手動実行（Actions ▸ *Build & Release Penrose Studio* ▸ Run workflow）でも
  ビルドでき、その場合は成果物が **workflow artifact** として残ります（Release へは
  タグ push のときのみ添付）。

## 🛠 ローカルでビルドする

### 共通
```bash
cd penrose_app
npm install
npm run gen        # www/index.html を bada_ruby から再生成（任意・Ruby が必要）
```

### Windows (.exe) — 要 Windows または wine
```bash
npm start          # Electron でアプリを起動（動作確認）
npm run dist:win   # dist/ に NSIS インストーラ + ポータブル .exe を生成
```

### Android (.apk) — 要 Android SDK + JDK 17
```bash
npx cap add android    # android/ ネイティブプロジェクトを生成（初回のみ）
npx cap sync android   # www/ をネイティブへ同期
cd android && ./gradlew assembleDebug
#   -> android/app/build/outputs/apk/debug/app-debug.apk
```

## 📁 構成

```
penrose_app/
  package.json            npm 設定 + electron-builder(build) 設定
  capacitor.config.json   Capacitor 設定（appId / appName / webDir=www）
  electron/main.js        Electron メインプロセス（www/index.html を表示）
  www/index.html          ペンローズ絵記号スタジオ本体（自己完結・オフライン）
  build/icon.png          アプリアイコン（1024²・純Ruby生成）
  build/make_icon.rb      アイコン生成スクリプト（zlib のみ）
  .gitignore              node_modules / dist / android(生成物)
```

`www/index.html` は `Bada::Penrose::WebApp`（`bada_ruby/lib/bada/penrose/webapp.rb`）が
生成します。エンジン（アインシュタイン縮約・清書方程式）を更新したら `npm run gen`
で再生成してください。

## 署名について

Android の APK は既定で **デバッグ署名**（`assembleDebug`）です。そのまま端末に
インストールして動作しますが、Google Play 配布には**リリース署名**が必要です。
本番配布時は keystore を用意し `assembleRelease` + 署名設定に切り替えてください。
Windows の `.exe` は未署名です（SmartScreen 警告が出る場合があります）。
コード署名証明書があれば electron-builder の `win.certificateFile` 等で署名できます。
