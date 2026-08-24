# Bada アプリ — ダウンロード用 (APK + Windows + Linux)

`bada_ruby` の 6 つのエンジンを、そのまま **Android APK**・**Windows 10/11 アプリ**・
**Ubuntu(Linux) アプリ** として配布できるようにしたものです。物理エンジンは Ruby では
なく **共有の純 Java コア**（`apps/core`）に移植してあり、3 プラットフォームで**同一の
コード**が動きます（Ruby ランタイム不要）。アプリは 6 画面（タブ／モード）構成：

- **① 宇宙電信 (Space Telegraph)** — 量子もつれ・汎用電信通信機
- **② 擬似量子計算機 (Pseudo QC)** — ノイマン型・ディスク内蔵・半導体制御の擬似量子計算機
  （制御回路をモニタに投射、BadaQASM を実行、**半導体 Verilog ソース**を生成）
- **③ 思考言語化 (Mind, simulation)** — 擬似QC で量子サンプリングし、ガンマ関数の大域的
  部分積分多様体をゲージにした Bada 製トランスフォーマーで、入力信号から思考の言語化・
  心像（ViT）・脳内アプリの Bada ソースを**合成**（実在の脳を読むものではありません）
- **④ コード生成 (Coder)** — 英語＋日本語の意図から、**プログラミング言語を自動判定**し、
  **予約語認識**・**単語補完**・コード生成（Ruby/Python/JS/C/Java/Bada）
- **⑤ サイレント入力 (Silent IME, simulation)** — **発声せず**入力した手がかりを各エンジンへ
  言語化。`:text` 文章／`:code` ソース／`:qc` QCソース＋実行／`:verilog` 半導体ソース／
  `:telegraph` 宇宙電信／`:bada` Bada構文／`:whisper` を、**全部発声せず文章で入力**（silent-talk 基準超え）
- **⑥ ウィスパード (Whisper, simulation)** — **発声せず**、英語ウィスパード（母音の落ちた・部分的な
  英語）を子音スケルトン照合で**完全文へ復元**。ASCII でも日本語でもない**未知の言語**を検出して
  英語へ言語化（デスクトップ ⑥ タブ／Android ⑦ モード／CLI `bada whisper`）
- **⑧ ChatΩ (AGI 自己進化, simulation)** — **これまでの集大成**。**chatGPT の進化版**として、
  **ガンマ関数の大域的部分積分多様体の機知**（Mind のプライア）から応答候補を標本化し、各候補を
  閉じた (2, m) 組みひもに符号化して **Jones 多項式**でトポロジカル整合度を採点、**世代をまたぐ
  AGI 自己進化**（エリート選択＋交叉＋量子シード突然変異）で最も整合する応答へ収束します。整合度は
  silent-talk 基準を上回ります（デスクトップ ⑧ タブ／Android ⑨ モード／CLI `bada agi`／`--agi`）。
  共有 Java コア `bada.agi.Agi.chat/render`。**実在の AGI ではなく生成シミュレーションです。**

**🧠 思考入力ボタン（全機能共通・本当に発声もタイプもせず）**：どのタブ／モードにも
**「🧠 思考入力」ボタン**があり、**押すだけ**で（手がかりのタイプも発声も不要）、ガンマ関数の
大域的部分積分多様体から量子シード駆動で**思考を捕捉**し、**silent-talk 超えの精度**でその欄に
言語化します（宇宙電信＝送信文、擬似QC＝QASM プログラム、思考言語化＝信号、コード生成＝意図）。
押すたびに別の思考が得られます。共有 Java コア `SilentTalk.thoughtCapture(kind, nonce)`。

**🔉 ウィスパード英語ボタン（全機能共通・全画面複数行 vim・一瞬で）**：どのタブ／モードにも
**「🔉 ウィスパード英語」ボタン**があり、押すと**短文入力の別画面ではなく、全画面の Bada Vim 複数行
エディタ**が開きます。**発声せず**、**複数行のウィスパード英語**（母音を落とした・部分的な英語）を
**そのまま直接入力**し、**⚡ 一括復元**（デスクトップは Ctrl+Enter）で**複数行を一辺に・一瞬で完全な
英語へ一括復元**して、その機能の欄へ入れます（silent-talk 超えの精度・短文入力ではない）。全機能で
この全画面複数行ウィスパードが使えます。共有 Java コア `Whisper.verbalizeBlock(cue)`。

**🧠 思考入力（打鍵せず・発声せず・複数行を一辺に／vim 思考制御）**：ウィスパード英語エディタの
**「🧠 思考入力（複数行を一辺に）」ボタン**は、**直接打鍵すらせず**、思考から**複数行を一辺に**捕捉して
エディタ全体を一瞬で埋めます（silent-talk 超えの精度・発声なし）。**⑧ Bada Vim** タブにも同じ
**🧠 思考入力**ボタンがあり、**vim を思考で制御**して複数行をバッファへ一辺に挿入します。共有 Java コア
`SilentTalk.thoughtBlock(kind, nonce, lines)`（ガンマ多様体プライアから量子シード駆動で決定的に捕捉）。

**🧠 思考コマンド操作（思っただけのコマンドで Bada Vim を操作・Bada 言語をプログラミング）**：
**⑧ Bada Vim** タブでは、**思っただけのコマンド**（発声もタイプもせず・silent-talk 超えの精度）で
vim を操作できます。**「🧠 思考コマンド」**は思考からコマンドを1手捕捉して適用（`:think`）、
**「🧠 思考プログラミング (Bada)」**は**思考コマンドの操作だけで、文法検証済み（Bada✓）の Bada 言語
プログラム**を vim に書き上げます（`:thinkprog [n]`・set/束縛/Omega::push/print の完全なプログラム）。
さらに**キーワードのコマンド入力機能**（`:kw <キーワード>`／キーワードボタン）を備え、
`set/print/push/assign/delete/top/bottom/save`（日本語: 代入/表示/送出/束縛/削除/先頭/末尾/保存）を
発声せずコマンドへ写像します。共有 Java コア `Vim.think/keywordCommand/thinkProgram`（Ruby/Java
バイト一致・量子シード決定的）。Android ⑧ Bada Vim モードと CLI `bada vim` でも `:think`
`:thinkprog` `:kw` が使えます。

**🧠 英語思考入力（英語モードの単語を発声もタイプもせず・全機能共通）**：全エンジンの入力欄に
**「🧠 英語思考入力」ボタン**があり、**英語モードの単語**を、**発声もタイプもせず**思考から捕捉して
英語で入力します（silent-talk 超えの精度）。ウィスパード英語エディタには**「🧠 英語思考入力（単語・
複数行）」**があり、英語の単語を**複数行一辺に**捕捉します。Android のウィスパードは**🧠 英語思考入力**
ボタンで同じ機能を提供します。共有 Java コア `SilentTalk.thoughtCapture("en", nonce)` /
`thoughtBlock("en", nonce, lines)`（英語版の多様体プライア `captureCueEn` を量子シードで標本化・Ruby/Java
バイト一致）。

**🔉 Bada Vim のウィスパード英語挿入モード（画面全体・直接・複数行を一辺に）**：**⑧ Bada Vim** タブでは、
ノーマルモードの `W` または **「🔉 ウィスパード英語挿入」ボタン**で **`-- WHISPER INSERT --`** に入り、
**画面全体に**発声せず**ウィスパード英語**を**複数行そのまま**直接打鍵します。`Esc` を押すと **打鍵した
複数行を一辺に**（`W` を押した行からカーソル行まで跨いで）**一瞬で完全な英語へ一括復元**し、
`precision X% > silent-talk 92.0%` を表示します（別に短文入力ではありません）。

**⚡ 複数行一括ウィスパード（複数行を跨ぐように・一瞬で）**：**「⚡ 一括ウィスパード（複数行一瞬）」ボタン**
または ex コマンド `:burst` で、**バッファの複数行を跨いで、発声せず、一瞬で**まとめて完全な英語へ
**一括復元**します（`:burst a;b;c` で `;` 区切りの複数行を一度に流し込み）。共有 Java コア
`Whisper.verbalizeBlock(cue)` / `Vim.ex("burst")`。
さらに Vim 内で**全機能のソースコード生成**が可能です：**🔩 半導体ソース**（`:verilog` = Verilog RTL）・
**⚛ QCソース**（`:qc` = OpenQASM ＋実行レポート）・**🧩 Badaソース**（`:bada`）・**📄 数学論文**（`:math`）・
**📝 レポート**（`:report`）の各ボタン、または ex コマンドで、発声せずカーソル位置に生成します。
共有 Java コア `Vim.ex("whisperen"/"qc"/"verilog"/…)`。

```
apps/
├── core/       共有 Java コア
│   ├── bada/quantum/  Bell/CHSH・5次カリア・Jones・不確定性・半導体・通信（電信）
│   ├── bada/qc/       DiskMemory(HDD)・Logic(MOSFET)・CPU・Monitor・Verilog（擬似QC）
│   ├── bada/mind/     Tensor・Encoder(多様体ゲージ注意)・Vision(ViT)・MindReader（思考言語化）
│   └── bada/coder/    Coder（言語自動判定・単語補完・予約語認識・コード生成 EN/JA）
├── desktop/    Windows/Linux/デスクトップ front end（Swing タブ GUI ＋ CLI）
└── android/    Android アプリ（Gradle プロジェクト）
```

## ⬇️ ダウンロード（配布物の入手）

ビルド済みの APK / EXE / DEB は、あなたのリポジトリの **GitHub Releases** から
**ログイン不要の恒久 URL**で入手できます。CI（`.github/workflows/build-apps.yml`）が
ビルドのたびに **`latest` Release** を自動更新します。

**▶ Releases ページ:** <https://github.com/masaaki-avnturle/Bada/releases/latest>

| プラットフォーム | ファイル | 直リンク |
|:--|:--|:--|
| **Android** | `BadaTelegraph.apk` | [download](https://github.com/masaaki-avnturle/Bada/releases/download/latest/BadaTelegraph.apk) |
| **Windows 10/11** ポータブル | `BadaTelegraph-windows-x64.zip` | [download](https://github.com/masaaki-avnturle/Bada/releases/download/latest/BadaTelegraph-windows-x64.zip) |
| **Windows 10/11** インストーラ | `BadaTelegraph-1.0.exe`（WiX） | Releases ページ参照 |
| **Ubuntu/Linux** ポータブル | `BadaTelegraph-linux-x64.tar.gz` | [download](https://github.com/masaaki-avnturle/Bada/releases/download/latest/BadaTelegraph-linux-x64.tar.gz) |
| **Ubuntu/Linux** インストーラ | `badatelegraph_1.0_amd64.deb`（`sudo dpkg -i`） | Releases ページ参照 |

- Android: 「提供元不明のアプリ」を許可してインストール（デバッグ署名済み）。
- Windows: zip を展開して `BadaTelegraph.exe`、または `.exe` インストーラで導入。
- Linux: tar.gz を展開して `bin/BadaTelegraph`、または `.deb` を導入。

> 手動ビルド：Actions タブ → **Build Bada apps** → *Run workflow*。実行すると成果物が
> Actions Artifacts に加えて **`latest` Release** にも公開されます。
> バージョン付き Release にするには `v*` タグを push してください（例 `v1.0.0`）。

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
