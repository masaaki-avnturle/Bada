# Bada Telegraph — ダウンロード用アプリ (APK + Windows EXE)

`bada_ruby` の **量子もつれ・汎用電信通信機（Space Telegraph）** を、そのまま
**Android の APK** と **Windows の EXE** として配布できるようにしたものです。
物理エンジンは Ruby ではなく **共有の純 Java コア**（`apps/core`）に移植してあり、
Android と Windows で**同一のコード**が動きます（Ruby ランタイム不要）。

```
apps/
├── core/       共有 Java コア（Bell/CHSH・5次カリア・Jones・不確定性・半導体・通信）
├── desktop/    Windows/デスクトップ front end（Swing GUI ＋ CLI）
└── android/    Android アプリ（Gradle プロジェクト）
```

## ⬇️ ダウンロード（配布物の入手）

ビルド済みの APK / EXE は **GitHub Releases** から入手できます。
バイナリはリポジトリの GitHub Actions（`.github/workflows/build-apps.yml`）が生成します。

1. リポジトリで **タグを付けて push** すると、CI が自動でビルドし Release に添付します：

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. しばらくすると **Releases ページ**に次が並びます：
   - `BadaTelegraph.apk` — Android 用（提供元不明のアプリを許可してインストール）
   - `BadaTelegraph-windows-x64.zip` — 展開して中の `BadaTelegraph.exe` を実行（ポータブル）
   - `BadaTelegraph-1.0.exe` — Windows インストーラ（WiX、スタートメニュー登録）

> 手動で回す場合は Actions タブ → **Build Bada Telegraph apps** → *Run workflow*。
> この場合は Release ではなく **Artifacts** に zip で出力されます。

## 🖥️ Windows EXE をローカルで作る

JDK 21（`jpackage` 同梱）が必要です。

```powershell
# コンパイル
javac -encoding UTF-8 -d build/classes (Get-ChildItem -Recurse apps/core/src, apps/desktop/src -Filter *.java).FullName
jar --create --file build/jar/BadaTelegraph.jar --main-class bada.desktop.DesktopApp -C build/classes .

# ポータブル exe（build/dist/BadaTelegraph/BadaTelegraph.exe）
jpackage --type app-image --name BadaTelegraph --input build/jar `
  --main-jar BadaTelegraph.jar --main-class bada.desktop.DesktopApp --dest build/dist

# インストーラ exe（要 WiX Toolset）
jpackage --type exe --name BadaTelegraph --input build/jar `
  --main-jar BadaTelegraph.jar --main-class bada.desktop.DesktopApp --dest build/installer --app-version 1.0
```

CLI としても使えます：`BadaTelegraph.exe "HELLO SPACE"` で証明＋送信レポートを標準出力へ。

## 📱 Android APK をローカルで作る

Android SDK（`ANDROID_HOME`）と JDK 17 が必要です。

```bash
cd apps/android
./gradlew assembleDebug
# => app/build/outputs/apk/debug/app-debug.apk
```

デバッグ APK はデバッグ鍵で署名済みなので、そのまま端末にインストールできます
（「提供元不明のアプリ」を許可）。ストア配布用の署名付き Release APK が必要な場合は
`assembleRelease` と署名鍵（keystore）を設定してください。

## アプリの中身（7要素）

| 要素 | 実装（`apps/core`） |
|:--|:--|
| もつれペアー / ベルの実験・不気味な遠隔作用 | `Qubit2`, `Bell`（CHSH → Tsirelson `2√2`） |
| 5次方程式の解の公式・周期に合わせた非線形カリア | `Quintic`（Durand–Kerner、周期 `2π/5`） |
| Jones多項式の相関 | `Jones`（Kauffman ブラケット状態和） |
| 確率統計・不確定性理論 | `Uncertainty`（Robertson＋Born） |
| 半導体で使える原理 | `Semiconductor`（Fermi–Dirac／トンネル） |
| 証明する機能 | `SpaceTelegraph.prove()`（全証明書→ `QED`） |
| 宇宙・汎用電信通信 | `Channel`（超密度符号化＋反復符号） |

正典の実装は Ruby 版 `bada_ruby`。本アプリはその忠実な Java 移植（配布用）です。
両者は同じ数値を出します（`S=−2.828`、`QED=true`、メッセージはロスレス送受信）。
