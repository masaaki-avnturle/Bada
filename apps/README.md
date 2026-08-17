# Bada アプリ — ダウンロード用 (APK + Windows + Linux)

`bada_ruby` の 2 つのエンジンを、そのまま **Android APK**・**Windows 10/11 アプリ**・
**Ubuntu(Linux) アプリ** として配布できるようにしたものです。物理エンジンは Ruby では
なく **共有の純 Java コア**（`apps/core`）に移植してあり、3 プラットフォームで**同一の
コード**が動きます（Ruby ランタイム不要）。アプリは 2 画面（タブ／モード）構成：

- **① 宇宙電信 (Space Telegraph)** — 量子もつれ・汎用電信通信機
- **② 擬似量子計算機 (Pseudo QC)** — ノイマン型・ディスク内蔵・半導体制御の擬似量子計算機
  （制御回路をモニタに投射、BadaQASM を実行、**半導体 Verilog ソース**を生成）

```
apps/
├── core/       共有 Java コア
│   ├── bada/quantum/  Bell/CHSH・5次カリア・Jones・不確定性・半導体・通信（電信）
│   └── bada/qc/       DiskMemory(HDD)・Logic(MOSFET)・CPU・Monitor・Verilog（擬似QC）
├── desktop/    Windows/Linux/デスクトップ front end（Swing タブ GUI ＋ CLI）
└── android/    Android アプリ（Gradle プロジェクト）
```

## ⬇️ ダウンロード（配布物の入手）

ビルド済みの APK / EXE / DEB は **GitHub Releases** から入手できます。
バイナリはリポジトリの GitHub Actions（`.github/workflows/build-apps.yml`）が生成します。

1. リポジトリで **タグを付けて push** すると、CI が自動でビルドし Release に添付します：

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. しばらくすると **Releases ページ**に次が並びます：
   - `BadaTelegraph.apk` — **Android**（提供元不明のアプリを許可してインストール）
   - `BadaTelegraph-windows-x64.zip` — **Windows 10/11** ポータブル（展開して `BadaTelegraph.exe`）
   - `BadaTelegraph-1.0.exe` — **Windows 10/11** インストーラ（WiX、スタートメニュー登録）
   - `BadaTelegraph-linux-x64.tar.gz` — **Ubuntu/Linux** ポータブル（展開して `bin/BadaTelegraph`）
   - `BadaTelegraph_1.0_amd64.deb` — **Ubuntu/Linux** インストーラ（`sudo dpkg -i`）

> 手動で回す場合は Actions タブ → **Build Bada apps** → *Run workflow*。
> この場合は Release ではなく **Artifacts** に出力されます。

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

## 🐧 Linux (Ubuntu) アプリをローカルで作る

JDK 21（`jpackage` 同梱）と、`.deb` 生成には `fakeroot` が必要です。

```bash
mkdir -p build/classes build/jar
find apps/core/src apps/desktop/src -name '*.java' > sources.txt
javac -encoding UTF-8 -d build/classes @sources.txt
jar --create --file build/jar/BadaTelegraph.jar --main-class bada.desktop.DesktopApp -C build/classes .

# ポータブル（build/dist/BadaTelegraph/bin/BadaTelegraph）
jpackage --type app-image --name BadaTelegraph --input build/jar \
  --main-jar BadaTelegraph.jar --main-class bada.desktop.DesktopApp --dest build/dist

# .deb インストーラ（要 fakeroot）
sudo apt-get install -y fakeroot binutils
jpackage --type deb --name BadaTelegraph --input build/jar \
  --main-jar BadaTelegraph.jar --main-class bada.desktop.DesktopApp --dest build/deb --app-version 1.0
```

CLI としても使えます：`BadaTelegraph "HELLO SPACE"`（電信）／`BadaTelegraph --qc`（擬似QC）。

## アプリの中身

### ① 宇宙電信 (Space Telegraph) — `bada/quantum`

| 要素 | 実装 |
|:--|:--|
| もつれペアー / ベルの実験・不気味な遠隔作用 | `Qubit2`, `Bell`（CHSH → Tsirelson `2√2`） |
| 5次方程式の解の公式・周期に合わせた非線形カリア | `Quintic`（Durand–Kerner、周期 `2π/5`） |
| Jones多項式の相関 | `Jones`（Kauffman ブラケット状態和） |
| 確率統計・不確定性理論 | `Uncertainty`（Robertson＋Born） |
| 半導体で使える原理 | `Semiconductor`（Fermi–Dirac／トンネル） |
| 証明する機能 | `SpaceTelegraph.prove()`（全証明書→ `QED`） |
| 宇宙・汎用電信通信 | `Channel`（超密度符号化＋反復符号） |

### ② 擬似量子計算機 (Pseudo QC) — `bada/qc`

| 要素 | 実装 |
|:--|:--|
| 制御回路をモニタに投射 | `Monitor`（ノイマン型データパス＋量子回路タイムライン） |
| PCのHDD内部の電子回路シミュレーション | `Logic`（CMOS/MOSFET NAND から作るデコーダ） |
| ディスクメモリ内蔵シミュレーション | `DiskMemory`（状態ベクトルとプログラムを実ファイル＝HDD に格納） |
| ノイマン型の擬似量子コンピュータ | `Cpu`（fetch→半導体デコード→実行、ストアドプログラム） |
| 量子コンピュータの半導体ソースコード | `Verilog`（NAND プリミティブ＋デコーダ＋ROM 制御 RTL を自動生成） |

正典の実装は Ruby 版 `bada_ruby`（`Bada::Quantum` / `Bada::QC`）。本アプリはその忠実な
Java 移植（配布用）で、同じ数値を出します（電信：`S=−2.828`, `QED=true`／擬似QC：
Bell = `|00>,|11>` 各 0.5、GHZ = `|000>,|111>` 各 0.5、ディスク像 192/288 bytes）。
