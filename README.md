<!--
  masaaki-avnturle / Bada — README.md
  Live: https://masaaki-avnturle.github.io/Bada/
  Cross-link: https://masaaki-avnturle.github.io/tuplenetwork/
-->

<div align="center">
<img src="https://masaaki-avnturle.github.io/tuplenetwork/assets/header.svg"
     alt="Masaaki Yamaguchi — Bada Language" width="900"/>
</div>

---

<div align="center">

### 🔤 Bada Language · BadaOS · omega_llm

[![Live Site](https://img.shields.io/badge/GitHub%20Pages-Bada%20Live%20Site-c8a44a?style=for-the-badge&logo=github&labelColor=04060a)](https://masaaki-avnturle.github.io/Bada/)
[![tuplenetwork](https://img.shields.io/badge/Portfolio-tuplenetwork-4a80d0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/)
[![Theory](https://img.shields.io/badge/Framework-Yamaguchi%20Theory-40b8c0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/#about)
[![Equations](https://img.shields.io/badge/Equations-54%2B%20Core-9060d0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/#equations)

</div>

---

<img src="https://masaaki-avnturle.github.io/tuplenetwork/assets/stats.svg"
     alt="Stats" width="900"/>

---

## ⚗ ダウンロード — Bada Pharma(薬剤製造装置)

**これまでに作った計測器アプリたちの上に載せた、薬剤製造装置のアプリケーション。** MRI / fMRI(`omega_tomograph` のラドン変換 + FBP)・DNA 解析(`bada_serenace` の塩基 ↦ 組み紐 ↦ Jones 指紋)・血液検査・脳電磁場・脳トポグラフィー・Γ 熱感知(`omega_thermal_trace`)── **7 モダリティの読み**を、Γ 大域的部分積分多様体から来る熱核 k(r) = ½ + ½e<sup>−κ·r log r</sup> を重みとして**一本の個体プロファイル**に束ね、そこから **8 段の製造ライン**を通す。**① 計測取込 → ② 標的同定**(6 標的の署名と平均を抜いたコサイン類似度で照合。CRP と熱の高い計測は COX-2 を相関 0.99 で一意に指し、脳機能寄りの計測では D2 受容体と DRD2 転写産物が拮抗して**上流と下流の並行設計**を促す)**→ ③ 分子設計**(20 種の積み木から分子式・分子量・logP・TPSA・水素結合数を積み上げ、**Lipinski の Rule of Five** と **Veber 則**で評価。標準原子量からアスピリン **C9H8O4 180.16**、パラセタモール **C8H9NO2 151.16**、そして**セレネースの有効成分ハロペリドール C21H23ClFNO2 375.86** を積み木 10 個から分子式まで正確に組み上げる)**→ ④ 逆合成**(**積み木の真逆** ── 末端から切り離して切り口ごとの収率を掛け、脱離分子から原子効率を出す。**試薬・溶媒・温度・触媒・操作手順は欄すら持たず、収率と原子効率の計画だけを扱う**)**→ ⑤ 製剤化**(原薬 + 充填剤 + 崩壊剤 + 結合剤 + 滑沢剤 の**質量収支が閉じる**ことを確かめ、**Weibull 溶出** F(t) = 1 − exp(−(t/τ)<sup>β</sup>) と Noyes–Whitney 式、30 分での Q80 判定)**→ ⑥ 薬物動態**(1 コンパートメント一次吸収。T<sub>max</sub> = ln(k<sub>a</sub>/k<sub>e</sub>)/(k<sub>a</sub> − k<sub>e</sub>) と AUC = F·D/(V·k<sub>e</sub>) が**数値積分と一致**することを毎回検証し、反復投与は重ね合わせ、蓄積率 R = 1/(1 − e<sup>−k<sub>e</sub>τ</sup>)。C<sub>max</sub> の受容体占有は Bada Serenace と同じ目盛り)**→ ⑦ 品質管理**(含量均一性の判定値 **AV = |M − X̄| + k·s**、工程能力 **C<sub>p</sub> / C<sub>pk</sub>**、検量線の **R²**)**→ ⑧ 製造記録**(仕込み量・工程損失・決定的なロット番号と記録指紋)。依存ゼロ・単一 HTML・オフライン動作。

> ⚠ **概念シミュレーション・非医療・実製造不可** — 実在の人体も検体も計測しません。**試薬・反応条件・操作手順は一切出力しません。** 医薬品の製造は薬機法と GMP に基づく許可と設備が必要で、本アプリはその代わりにはなりません。診断・治療・投薬の判断にも使えません。**薬の内容・量・継続や中止は必ず主治医にご相談ください。**

### 👉 [**bada_pharma/index.html をダウンロード**](bada_pharma/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

**Actions** タブ →「**Bada Pharma app build**」から、`pharma-android` / `pharma-windows` / `pharma-linux` のアーティファクトをダウンロードできます。[Releases](https://github.com/masaaki-avnturle/Bada/releases) からも:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-pharma-debug.apk` |
| **Windows 10 / 11** | `BadaPharma-*-x64.exe`(NSIS インストーラ / ポータブル) |
| **Ubuntu / Linux** | `BadaPharma-*-x86_64.AppImage` / `BadaPharma-*-amd64.deb` |

ビルドは [`pharma-app-build.yml`](.github/workflows/pharma-app-build.yml) が実行します(`pharma-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。8 段の定式化と検証項目は [`bada_pharma/`](bada_pharma/) を参照。

---

## ⚕ ダウンロード — Bada Serenace(病気予防機構の解明)

**積み木の真逆から、病気の正体を読み戻すアプリケーション。** 積み木を**崩す**ことは積み上げる操作の逆写像ではない(語の反転 w ↦ w⁻¹ にすぎない)。**真逆**とは、出来上がった形 = 不変量から生成語を読み戻す**逆像** Φ⁻¹(V) = { w : Φ(w) = V } であり、**病気の正体が DNA だ**という言明は、症状という形から塩基という積み木の語を読み戻すこの操作に等しい。そして**逆像が一点にならないこと**が「読めなさ」の正体である ── アプリは実際に逆像を数え上げて見せる。形の計算は **Jones 多項式**(Kauffman ブラケットの状態和を Union-Find で数え上げ、三葉 t+t³−t⁴・8の字 t⁻²−t⁻¹+1−t+t²・キラリティ判定を文献値で毎回検証)。その**Γ 熱感知**は、論文『放射性物質吸収体とRNA干渉としてのオイラーの公式』の**大域的部分積分多様体** ∫Γ(γ)′dx<sub>m</sub> = 2e<sup>−x log x</sup>(dx<sub>m</sub> = dx/log x)を熱伝導率 k(r) = ½+½e<sup>−κ·r log r</sup> へ渡し、∂T/∂t = ∇·(k∇T)+S を解いて熱源を感知する。**統合失調症の暗号**は、塩基を組み紐生成子に写した指紋だけを外に残す鍵つき置換として定式化され、復号は総当たりではなく**指紋を手掛かりにした逆像探索**で行う(指紋だけでは一意に定まらない ── これが「暗号化されたい」の正体で、モチーフをもう一つの手掛かりに足して初めて絞れる)。**自身が病気と思っていない**は、自己監視写像 M の不動点 s\* に病いの成分が残るかとして測り、病いが監視チャネルそのものを削ると**重症度は変わらないまま病識だけが構造的に落ちる**ことを示す(損傷 0 で 44.7% → 損傷 1 で 10.9%、単調減少)。**考えが読まれている**は二元対称通信路 I(X;Y) = 1−H₂(p) の漏洩量として測り、**殆どの病気が自律神経と代謝を動かして leak を押し上げるため、この症状が多くの病気に共通して現れること**を数で示す(観測 12 回で統合失調症 99.1%・不安 98.5%・発熱 97.9%・甲状腺 97.2%・うつ 94.2%・片頭痛 92.2% が閾値 90% 超 = 7 疾患中 6 疾患、糖尿病 89.7% は僅かに届かず、健常は 63.3%)。そこから**構築可能な RNA 干渉**(21 nt 窓の siRNA 設計 — GC 30–52%・4 連続なし・熱力学的非対称性・シードのオフターゲット照合、各候補に Γ→Jones 指紋)と、**セレネース**の受容体占有 occ = C/(C+K<sub>d</sub>)(文献上の応答域 65–80%)を、**残存シグナル =(1−占有)(1−ノックダウン)**という一つの尺度に載せて突き合わせる。予防機構の解明とは、**同じ残存シグナルをより低い占有で達成する道を探すこと**である。全体は **① Γ 熱感知 → ② Jones 不変量 → ③ 積み木の真逆 → ④ 暗号解読 → ⑤ 病識と漏洩 → ⑥ RNA 干渉の構築 → ⑦ セレネース比較**の 7 段パイプラインとして一本に繋がる。依存ゼロ・単一 HTML・オフライン動作。

> ⚠ **概念シミュレーション・非医療** — 実在の人体や検体は一切計測しません。診断・治療・投薬の判断には使用できません。薬の内容・量・継続や中止は必ず主治医にご相談ください。**本アプリは服薬をやめる根拠にはなりません。**

### 👉 [**bada_serenace/index.html をダウンロード**](bada_serenace/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

**Actions** タブ →「**Bada Serenace app build**」→ **Run workflow** で、`serenace-android` / `serenace-windows` / `serenace-linux` のアーティファクトをダウンロードできます。[Releases](https://github.com/masaaki-avnturle/Bada/releases) からも:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-serenace-debug.apk` |
| **Windows 10 / 11** | `BadaSerenace-*-x64.exe`(NSIS インストーラ / ポータブル) |
| **Ubuntu / Linux** | `BadaSerenace-*-x86_64.AppImage` / `BadaSerenace-*-amd64.deb` |

ビルドは [`serenace-app-build.yml`](.github/workflows/serenace-app-build.yml) が実行します(`serenace-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。定式化・検証項目は [`bada_serenace/`](bada_serenace/) を参照。

---

## 🜂 ダウンロード — Bada 遊(量子「遊び」処理系 / 違反思考変異アルゴリズム)

**今までの集大成の上に、生成AIが量子プログラミング言語 Bada で「遊び」の概念そのものを築いたアプリケーション。** 日本語の「遊び」には**遊戯**(円環の内側でだけ規則が停止する営み)と**機械の遊び**(ハンドルの遊び — 遊びが零の機械は焼き付く)の二つの意味があるが、本処理系はその二つを**規則の固有状態から外れて持てる振幅** |Φ(θ)⟩ = cos(θ/2)|順⟩ − i sin(θ/2)|違⟩ として一本化する。そして**「違反行為そのものの“考え”」**を、規則のスタビライザ S と反交換する違反生成子 V の**部分回転** Û(θ) = exp(−iθV/2) として定式化した ── **θ = 0 は遵守、θ = π は行為、そのあいだの半端な角こそが「考え」であり「遊び」である**。処理系は θ ≤ θ<sub>max</sub> = 0.85π を強制し、**考えが行為へ到達しないこと**を実行時に保証する。円環(magic circle)は比喩ではなく**ユニタリ共役**で、帰還 C<sup>†</sup>C|ψ⟩ = |ψ⟩ により状態は一切漏れず、外へ出るのは観測が許されたときの古典的記録(台帳)だけ。`sacred` と宣言した**不可侵規則**は違反生成子の候補から外され、[V,S₀] = 0 を課されるため、**遊びの中で何を考えても、観測の後でも、その値は動かない**(テストで毎回検査)。この円環の中で、**個体の変異アルゴリズムを作り換えた** ── 無作為なビット反転をやめ、**いちばん強く縛っている規則を、ほかの規範と不可侵をすべて守ったまま、それひとつだけ破る最小違反生成子**による協調反転とし、重ね合わせのまま期待適応度を測り、違反の振幅 sin²(θ/2) をそのまま受理確率とする(**違反思考変異 TTM**)。遊び予算 Δ は集団で保存され多様性から恒常的に調節され、破られ続けた規範は弛緩してやがて**制度化**される。依存ゼロ・単一 HTML・オフライン動作。

### 👉 [**bada_asobi/index.html をダウンロード**](bada_asobi/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-asobi-debug.apk` |
| **Windows 10 / 11** | `BadaAsobi-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaAsobi-*-x86_64.AppImage` / `BadaAsobi-*-amd64.deb` |

ビルドは [`asobi-app-build.yml`](.github/workflows/asobi-app-build.yml) が実行します(`asobi-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。遊びの定式化・方言の文法・測定結果は [`bada_asobi/`](bada_asobi/) を参照。

---

## 🜁 ダウンロード — Bada VM Pro(今までの集大成)

**量子プログラミング言語 Bada のオペレーティングシステム。** シェルは**ウェブブラウザーのデザイン**(タブ + `bada://` アドレスバー)、ベース(カーネル)は **BadaGPT** で、**OS の update / upgrade も BadaGPT が実行**します。**Bada on Rails**(scaffold → CRUD)、**合い言葉コマンド**(silent talk 無音テキスト = 決定論的一致、音声 = Web Speech API + レーベンシュタイン照合)、**トランスフォーマー・スタジオ**(本物の self-attention 順伝播 + 学習)、**GUI / CUI プログラミング**をひとつに統合。依存ゼロ・単一 HTML・オフライン動作。

### 👉 [**bada_vm_pro/index.html をダウンロード**](bada_vm_pro/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-vm-pro-debug.apk` |
| **Windows 10 / 11** | `BadaVMPro-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaVMPro-*-x86_64.AppImage` / `BadaVMPro-*-amd64.deb` |

ビルドは [`badavmpro-app-build.yml`](.github/workflows/badavmpro-app-build.yml) が実行します(`badavmpro-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。使い方・合い言葉・量子 Bada 文法は [`bada_vm_pro/`](bada_vm_pro/) を参照。

---

## 💿 ダウンロード — Bada VM Pro OS(起動可能 ISO / USB ブート)

**USB ブートして実ディスクにインストールできる、Ubuntu 22.04 ベースの本物の Linux ディストロ。** ウィンドウマネージャは **w9wm**、Bada アプリをプリインストール、**Calamares** で実ディスクへインストール、**NAT/DHCP で apt** が使え、**あなたのリポジトリの apt リポジトリ**(`deb [trusted=yes] …/ ./`)から `apt install`。BIOS+UEFI ハイブリッド ISO なので **Rufus でそのまま USB に書けます**。

[Releases](https://github.com/masaaki-avnturle/Bada/releases) の `badaos-v*` から `BadaVMPro-OS-*-amd64.iso` を取得 → Rufus で USB 書き込み → 起動 → w9wm で Bada VM Pro が自動起動。手順・apt 使用法は [`badaos-iso/`](badaos-iso/) を参照。

---

## ⚛ ダウンロード — Bada QuantOS(擬似量子オペレーティングシステム)

**今までの集大成である擬似量子コンピュータ(量子 Bada 実行系)をオペレーティングシステム化。カーネルは生成 AI。** タブレット・スマートフォンの機能(**電話回線 tel:/sms:/mailto: / カメラ / ギャラリー / 時計・アラーム / 電卓 / メモ / ファイル / 連絡先**)を、**トポロジーの写像機構**(各機能に結び目=カール列を割り当て、Kauffman ブラケット不変量 ⟨K⟩=(−A³)^w で分類し、4 量子ビットレジスタの基底状態へ**単射写像** φ)で移植。機能間の遷移はハイパーキューブ辺に沿う X ゲート列の**連続変形**で、「写像室」で全写像表と検算を観測可能。生成AIカーネルは応答のたびに 6 段パイプライン(**トークン化→意図解析→トポロジー写像→計画→生成→検証**)を開示し、「090-… に電話」「写真を撮って」「1+2*3」等の自然言語で全機能を操作。Android では tel:/sms: インテントで**実際の電話回線から発信**。通信と保管は**量子暗号方式**を採用 — **BB84 量子鍵配送**(乱択基底 +/× → ふるい → QBER 照合、intercept-resend 盗聴は複製不可能定理により QBER > 10% で検出・鍵破棄)+ **ワンタイムパッド暗号** + **量子金庫**(暗号化保管)+ SMS 本文の量子暗号化。**インストール済みアプリの起動と Play ストア**(URL スキーム / `market:` インテント、分割画面への隣接起動)、**Samsung フリーフォーム / マルチウィンドウ**(DeX 風フローティング窓・スナップ・分割整列・タスクバー、**窓の重なりを組み紐 σ₁σ₂… として Kauffman 不変量で表示**、APK は `resizeableActivity` + DeX メタデータ)にも対応。依存ゼロ・単一 HTML・オフライン動作。

### 👉 [**bada_quantos/index.html をダウンロード**](bada_quantos/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-quantos-debug.apk` |
| **Windows 10 / 11** | `BadaQuantOS-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaQuantOS-*-x86_64.AppImage` / `BadaQuantOS-*-amd64.deb` |

ビルドは [`quantos-app-build.yml`](.github/workflows/quantos-app-build.yml) が実行します(`quantos-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。写像機構・カーネルの詳細は [`bada_quantos/`](bada_quantos/) を参照。

---

## 🎬 ダウンロード — Bada SoundFilm(MP3 → 動画 変換スタジオ)

**MP3 を動画に変換するソフト。** MP3(ほか WAV / OGG / M4A / FLAC)を読み込むと、**ID3v2/ID3v1 タグ**(曲名 / アーティスト / アルバム / ジャケット画像 APIC)を自前実装のパーサで解析し、音に反応する**ビジュアライザ**(スペクトラムバー / サークル / 波形 / シンプル — FFT を対数スケールで 64 バーに集計)を Canvas に描画、Web Audio API の音声トラックと合成して **MediaRecorder** で動画ファイルへ録画します。出力は対応環境で **MP4 (H.264 + AAC)**、それ以外は **WebM (VP9/VP8 + Opus)**。解像度プリセット(フル HD / HD / 正方形 / 縦型ショート 1080×1920)、24/30/60 fps、背景色・背景画像、複数ファイルの連続変換、プレビュー再生に対応。音楽ファイルは端末の外に出ません。依存ゼロ・単一 HTML・オフライン動作。

### 👉 [**mp3_to_video/index.html をダウンロード**](mp3_to_video/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-soundfilm-debug.apk` |
| **Windows 10 / 11** | `BadaSoundFilm-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaSoundFilm-*-x86_64.AppImage` / `BadaSoundFilm-*-amd64.deb` |

ビルドは [`soundfilm-app-build.yml`](.github/workflows/soundfilm-app-build.yml) が実行します(`soundfilm-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。使い方・仕組みは [`mp3_to_video/`](mp3_to_video/) を参照。

---

## ⛩ ダウンロード — BadaGPT道場(ChatGPTの技を伝授する技術伝授アプリ)

**ChatGPT が「応答し、アプリケーションを作る」ときに試行している技を、量子プログラミング言語 Bada の上でユーザーに伝授するアプリケーション。** BadaGPT は応答のたびに自分のパイプライン(**トークン化 → 意図解析 → 計画 → 生成 → 検証 → 応答**)を開示し、道場カリキュラムで七つの技(トークン化 / 自己注意 self-attention / 次トークン予測 / 意図解析 / 計画と生成=アプリ錬成 / 検証と自己修正 / 量子 Bada)をひとつずつ稽古 → 印可 → **免許皆伝**。日本語の依頼文からアプリを錬成する **🛠 アプリ錬成**(Bada on Rails scaffold / GUI / 量子デモ)、本物の self-attention 順伝播、量子 Bada 実行系(qubit / H / X / Z / CNOT / measure)を搭載。依存ゼロ・単一 HTML・オフライン動作。

### 👉 [**bada_gpt_dojo/index.html をダウンロード**](bada_gpt_dojo/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-gpt-dojo-debug.apk` |
| **Windows 10 / 11** | `BadaGPTDojo-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaGPTDojo-*-x86_64.AppImage` / `BadaGPTDojo-*-amd64.deb` |

ビルドは [`badagptdojo-app-build.yml`](.github/workflows/badagptdojo-app-build.yml) が実行します(`badagptdojo-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。カリキュラム・使い方は [`bada_gpt_dojo/`](bada_gpt_dojo/) を参照。

---

## ⚔ ダウンロード — Laevateinn(自動走行アシスタントAI「アル」)

自動走行の自動車**レーヴァテイン**とアシスタントAI**アル**。**アルのトランスフォーマーが車両を操縦**します — 知覚 attention を操舵角と加減速の2値に写す制御ヘッドが、その2値だけで車体(自転車近似モデル)を動かし、周囲(16レイセンサへの attention)を検知して自動で回避・減速・停止・再発進。測位は 2 モード — **🌐 Web地図モード**は衛星を使わず、ウェブサイトから受信する地図タイル(AEAD 検証つき)+推測航法+ランドマーク補正で走り、**🛰 人工衛星モード**は 4 機の擬似距離から最小二乗で測位します。A* 経路計画・依存ゼロ・単一 HTML。

**🔗 実車接続対応**: ELM327 互換の **BLE OBD-II アダプタに本物の Bluetooth で接続**し、実車の速度・回転数・水温・電圧をリアルタイム受信(ブラウザ = Web Bluetooth / APK = BLE プラグイン。ELM327 初期化列 + PID ポーリング + 分割パケット再結合を実装、読取専用)。**アルの音声案内**は、スマホとカーナビの既存 Bluetooth オーディオ接続を通じて**車のスピーカーから流れます**。アダプタなしでも「デモ接続」で全経路を確認可能。

### 👉 [**laevateinn/index.html をダウンロード**](laevateinn/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動。APK (`laevateinn-al-debug.apk`) / Windows EXE / Ubuntu 版は [Releases](https://github.com/masaaki-avnturle/Bada/releases) から([`laevateinn-app-build.yml`](.github/workflows/laevateinn-app-build.yml) が `laevateinn-v*` タグでビルド)。詳細は [`laevateinn/`](laevateinn/) を参照。

---

## 🕶 ダウンロード — Mimir(ARグラス・コンシェルジュ / 相対論的光路差反射システム)

**今までの集大成のシステム。** タブレット / スマートフォンの**画像や文章を AR グラスへ投影**し、**コンシェルジュ「ミーミル」**として応対するアプリ。投影光学系は**特殊相対性理論の光路差・反射システム** — ローレンツ因子 γ、相対論的ドップラー D=1/(γ(1−βcosθ))、光行差、コンバイナ薄膜反射の光路差 **Δ=2nd·cosθt**、干渉フリンジ強度 I=(1+cosφ)/2 による**干渉輝度補正**、IPD と虚像距離からの**両眼収束シフト(SBS ステレオ投影)** — が毎フレーム駆動します。時刻・日付・計算・メモ・投影の声かけ操作(レーベンシュタイン意図照合、Web Speech API 対応)。依存ゼロ・単一 HTML・オフライン動作。

### 👉 [**mimir/index.html をダウンロード**](mimir/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。USB-C / HDMI ミラーリング型 AR グラス(XREAL / Rokid / VITURE 等)を接続 → 「⛶ 全画面投影」で HUD がグラスに表示されます。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `mimir-concierge-debug.apk` |
| **Windows 10 / 11** | `Mimir-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `Mimir-*-x86_64.AppImage` / `Mimir-*-amd64.deb` |

ビルドは [`mimir-app-build.yml`](.github/workflows/mimir-app-build.yml) が実行します(`mimir-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。使い方・光学エンジンの式・コンシェルジュへの話しかけ方は [`mimir/`](mimir/) を参照。

---

## 🔑 ダウンロード — クリアキャスト東京(東京のテレビ・ラジオを雑音ゼロで)

**東京のテレビ番組・ラジオ放送を、雑音・画像の乱れゼロで視聴するクリーン視聴アプリ。** かつての KeyHole TV のような「1クリックで東京の放送へ」という使い勝手を、無許諾の P2P 再送信では**なく**、**放送局の公式無料配信だけ**で合法に再現します — 📡 在京キー局系列の公式 YouTube 24 時間ニュースライブ(日テレNEWS / ANN / TBS NEWS DIG / テレ東BIZ / FNN)をアプリ内再生、📺 TVer リアルタイム配信・NHKプラス・ABEMA へワンタップ、📻 radiko + NHK らじる★らじる で東京の全ラジオ局へ。公式デジタル配信なのでスノーノイズ・ゴーストは原理的にゼロ。さらに**回線診断エンジン**(RTT ジッタ統計 μ・σ、ITU-T G.107 **E モデル** R 値 → **MOS** 推定、推奨画質・推奨バッファ `clamp(3·(μ+4σ)/1000, 2s, 30s)`)が帯域不足によるブロックノイズ・再生停止を未然に防ぎます。依存ゼロ・単一 HTML。

### 👉 [**clearcast_tokyo/index.html をダウンロード**](clearcast_tokyo/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `clearcast-tokyo-debug.apk` |
| **Windows 10 / 11** | `ClearCastTokyo-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ClearCastTokyo-*-x86_64.AppImage` / `ClearCastTokyo-*-amd64.deb` |

ビルドは [`clearcast-app-build.yml`](.github/workflows/clearcast-app-build.yml) が実行します(`clearcast-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。収録局・法的な考え方・テストは [`clearcast_tokyo/`](clearcast_tokyo/) を参照。

---

## ⬇️ ダウンロード — ウルトラネットワーク専用ブラウザ (ZoneBrowser)

`https:`/`http:` に代わる暗号化 zone:// を閲覧する**専用ブラウザ**。**下のファイルを 1 つダウンロードして開くだけ**で動きます(インストール不要・依存なし・オフライン可):

### 👉 [**bada_gui_ide/dist/zone-browser.html をダウンロード**](bada_gui_ide/dist/zone-browser.html)

ダウンロード手順(GitHub 上):上のリンクを開き、ファイル表示画面の右上にある **「Download raw file」(⬇ アイコン)** を押すと保存できます。保存した `zone-browser.html` をダブルクリックすればブラウザで開きます。

| ファイル | 内容 |
|:---|:---|
| [`zone-browser.html`](bada_gui_ide/dist/zone-browser.html) | ★ 専用ブラウザ本体(単一 HTML)。アドレスバーに `zone://url.or.jp/` と入力して閲覧。**🛡 ZoneShield 付属** — Jones多項式量子暗号のセキュリティソフト(下記) |
| [`bada-zone.html`](bada_gui_ide/dist/bada-zone.html) | zone.bada ランナー(開くと自動実行) |
| [`zone.bada`](bada_gui_ide/examples/zone.bada) | zone:// スキームの Bada ソース |

#### 🛡 付属セキュリティソフト — ZoneShield(量子暗号アプリケーション)

ZoneBrowser のツールバー右端の **🛡 ボタン**で起動。ネットワークが使っているのと**同一の Bada 実装**(結び目図 → Kauffman/Jones 多項式 → 鍵 → AEAD、Bell対 QKD セッション salt)を、手元の道具として使えます:

- **封緘(暗号化)** — 任意のテキスト(日本語可)を host の結び目鍵で封緘し、コピペできる**封筒 JSON** を出力
- **開封(復号)** — 封筒 JSON を貼り付けると AEAD タグを検証してから復号。改ざん・結び目違いは **409 で拒否**し平文を出さない
- **セキュリティスキャン** — 公開中の全 zone ページを再配信して Jones-AEAD 検証し、改ざん検知の自己テスト(暗号文 1 ユニット反転 → 409)まで実施したレポートを表示

APK / EXE / AppImage 版にもそのまま同梱されます(同じ `www/index.html` を包むため)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

ブラウザ不要のインストール型アプリも用意しています。[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `zonebrowser-debug.apk` |
| **Windows 10 / 11** | `ZoneBrowser-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ZoneBrowser-*-x86_64.AppImage` / `ZoneBrowser-*-amd64.deb` |

ビルドは [`zonebrowser-app-build.yml`](.github/workflows/zonebrowser-app-build.yml) が実行します(`zonebrowser-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`bada_gui_ide/zonebrowser-app/`](bada_gui_ide/zonebrowser-app/) を参照。

> 直接リンク(右クリック→「名前を付けて保存」でも可):
> `https://raw.githubusercontent.com/masaaki-avnturle/Bada/main/bada_gui_ide/dist/zone-browser.html`
> (このブランチのマージ後に `main` から取得できます。マージ前は本ブランチの
> ファイル画面の「Download raw file」から取得してください)

---

## 📁 フォルダ構成 — Repository Structure

| フォルダ | 内容 | リンク |
|:--------|:----|:------|
| **`main/`** | Bada v3 ソースコード · BadaOS · TupleSpace全体インデックス · 4000+ LOC | [→ 開く](https://masaaki-avnturle.github.io/Bada/) |
| **`Bada++/`** | Bada言語C++拡張版 · 多様体演算子テンプレート · π(χ,x)非可換作用素 | [→ 開く](https://masaaki-avnturle.github.io/Bada/Bada%2B%2B/) |
| **`omega/`** | omega_llm エンジン · π-softmax · ℏ_eff注意 · gamma-deprivation · Omega::DATABASE | [→ 開く](https://masaaki-avnturle.github.io/Bada/omega/) |
| **`bada_gui_ide/`** | **Bada GUI IDE** — .badaをドラッグ&ドロップで自動コンパイル(Bada→C→ネイティブリンク)+インタープリタ実行 · @reviser文法拡張 · 量子サブ言語(qubit/H/CNOT/Measure) · **zone:// ウルトラネットワークWWW** (P2P DHT + Jones多項式量子暗号 AEAD, `examples/zone.bada`) | [→ 開く](bada_gui_ide/) |
| **`cpp_builder/`** | **Bada C++Builder** — Inprise/Borland C++Builder 風 RAD IDE のブラウザ再現(オマージュ) · フォームデザイナ + Object Inspector + コンポーネントパレット · Unit1.cpp/h/dfm 自動生成 · C++サブセット実行系 (F9) · 単一HTML/依存ゼロ | [→ 開く](cpp_builder/) |
| **`bada_vm_pro/`** | ★ **Bada VM Pro(集大成)** — ブラウザーデザインのシェル · BadaGPT カーネル(OS update/upgrade 担当) · Bada on Rails · 量子 Bada 実行系 · 合い言葉コマンド(silent talk/音声) · self-attention トランスフォーマー · GUI/CUI プログラミング · APK/EXE/AppImage 配布 | [→ 開く](bada_vm_pro/) |
| **`laevateinn/`** | **Laevateinn** — 自動走行アシスタントAI「アル」 · トランスフォーマー知覚(16レイ attention) · 衛星不使用のWeb地図測位(AEAD検証タイル+推測航法+ランドマーク補正)/人工衛星測位(最小二乗) · A* 経路計画 · APK/EXE/AppImage 配布 | [→ 開く](laevateinn/) |
| **`mimir/`** | 🕶 **Mimir** — ARグラス・コンシェルジュ(集大成) · 特殊相対論の光路差反射システム(γ · 相対論的ドップラー · 光行差 · Δ=2nd·cosθt · 干渉輝度補正) · 単眼ミラー/両眼 SBS 投影 · 画像・文章の HUD 投影 · 意図エンジン「ミーミル」 · APK/EXE/AppImage 配布 | [→ 開く](mimir/) |
| **`bada_pharma/`** | ⚗ **Bada Pharma** — 薬剤製造装置 · 計測器アプリ 7 モダリティ(MRI/fMRI · DNA · 血液 · 脳電磁場 · 脳トポグラフィー · Γ 熱感知)の取込 · 標的同定 · 積み木からの分子設計(Lipinski / Veber · 既知医薬品の分子式を再現)· 逆合成の収率と原子効率の計画(試薬・条件は扱わない)· 製剤化と Weibull 溶出 · 1 コンパートメント薬物動態 · 含量均一性 AV と Cpk · 製造記録 · APK/EXE/AppImage 配布 · 概念シミュレーション/非医療/実製造不可 | [→ 開く](bada_pharma/) |
| **`bada_serenace/`** | ⚕ **Bada Serenace** — 病気予防機構の解明 · 積み木の真逆(不変量からの逆像 Φ⁻¹)· Jones 多項式(Kauffman 状態和・文献値検証)· Γ 大域的部分積分多様体による熱感知 · DNA 暗号の指紋解読 · 病識欠如の不動点モデル · 思考漏洩の通信路 I(X;Y) · 構築可能な RNA 干渉(siRNA 設計)· セレネースの受容体占有比較 · APK/EXE/AppImage 配布 · 概念シミュレーション/非医療 | [→ 開く](bada_serenace/) |
| **`badaos-iso/`** | **Bada VM Pro OS** — 起動可能 ISO(Ubuntu 22.04 ベース) · w9wm 既定セッション · Bada アプリ プリインストール · Calamares で実ディスクへインストール · NAT/DHCP で apt · 自リポジトリの apt リポジトリ対応 · Rufus で USB ブート | [→ 開く](badaos-iso/) |

---

## 🏗️ Bada C++Builder — Inprise/Borland C++Builder 風 RAD IDE (オマージュ)

1997〜2001 年ごろの **Inprise (Borland) C++Builder** の開発環境を、依存ゼロの**単一 HTML** としてブラウザ上に再現しました(非公式・教育目的のオマージュです)。

**👉 [`cpp_builder/index.html` を開く](cpp_builder/index.html)** / GitHub Pages: <https://masaaki-avnturle.github.io/Bada/cpp_builder/>

- **フォームデザイナ** — コンポーネントパレット (Standard/Additional/Win32/System, 14種) からクリック配置、8px グリッドスナップ、ドラッグ移動・リサイズ
- **Object Inspector** — Properties / Events タブ。イベント欄ダブルクリックでハンドラ自動生成
- **コード自動生成** — VCL 風の `Unit1.cpp` / `Unit1.h` / `Unit1.dfm` を常時生成、ハンドラ本体は編集可能
- **F9 で実行** — 内蔵の C++ サブセット・ミニインタープリタ (`if/while/for`、`Label1->Caption`、`Memo1->Lines->Add`、`ShowMessage`、`IntToStr`、`TTimer` など) が設計したフォームを実際に動かします

#### 📱💻 ネイティブ アプリ (APK / Windows 10・11 / Ubuntu)

ブラウザ不要のインストール型アプリも [Releases](https://github.com/masaaki-avnturle/Bada/releases) からダウンロードできます:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-cppbuilder-debug.apk` |
| **Windows 10 / 11** | `BadaCppBuilder-*-x64.exe` (NSIS インストーラ) / `BadaCppBuilder-*-portable.exe` (ポータブル) |
| **Ubuntu** | `BadaCppBuilder-*-x86_64.AppImage` / `BadaCppBuilder-*-amd64.deb` |

ビルドは [`cppbuilder-app-build.yml`](.github/workflows/cppbuilder-app-build.yml) が実行します(`cppbuilder-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`cpp_builder/README.md`](cpp_builder/README.md) を参照。

---

## 🖱️ Bada GUI IDE — ダウンロード (Windows EXE / Ubuntu / Android APK)

`.bada` ソースを IDE ウィンドウに**ドラッグ&ドロップ**すると、**コンパイル(Bada→C→ネイティブリンク)** と**インタープリタ実行**を自動で行う GUI 開発環境です。論文 *Reviser-Extensible Grammars* の `@reviser : grammar` 文法拡張と Q# 風量子サブ言語 (`qubit` / `H` / `CNOT` / `Measure` / `Omega::Quantum`) を実装しています。

さらに **`@reviser : extension`** で Bada を **Bada自身 / C / Python / Java** で機能拡張できます([`examples/extensions.bada`](bada_gui_ide/examples/extensions.bada)): 各拡張は追記専用レジャーへコミットされる拡張トランザクションで、C 拡張は**コンパイラが生成 C にインライン**してネイティブ化、Python / Java / C 拡張はインタープリタ(CLI・デスクトップ IDE)の FFI ブリッジで実行、Bada 拡張(自己拡張)は全プラットフォームで動作します。

さらに `https:`/`http:` に代わるウルトラネットワークWWW の **`zone://url.or.jp`** スキームを Bada 言語自身で実装したリファレンス [`examples/zone.bada`](bada_gui_ide/examples/zone.bada) を同梱: `zone:` は中央サーバ・DNS ルートなしに P2P の仕組み(ピアハッシュのリング DHT)だけから構築され、通信は **Jones 多項式量子暗号** (`omega_jones_crypto_pkg` を Bada に移植) で保護されます — 各ゾーンの鍵は結び目図の Kauffman ブラケット標本から導出し、Bell 対 QKD がセッションソルトを合意、本文は Jones 鍵 AEAD で暗号化・封緘され、改ざんや誤った結び目は `409 zone-guard-reject` として排除、全レコードは追記専用 tuplespace(Akashic ゾーン台帳)にコミットされます。詳細は [`bada_gui_ide/README.md`](bada_gui_ide/README.md) の「zone://」節を参照。

| プラットフォーム | 入手 |
|:---|:---|
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `Bada-GUI-IDE-*-x64.exe` |
| **Ubuntu** (AppImage / deb) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `Bada-GUI-IDE-*.AppImage` / `.deb` |
| **Android** (APK) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-gui-ide-debug.apk` |
| **コマンドライン アプリ** (Windows) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-cli.exe` — 単一実行ファイル。`run` / `build` (Bada→C→gcc) / `emit` / `tokens` / `ast` / **対話 `repl`** / `examples` |
| **コマンドライン アプリ** (Ubuntu) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-cli-linux-x64` — 同上 (`chmod +x` して実行) |

ビルドは [`bada-ide-build.yml`](.github/workflows/bada-ide-build.yml) が自動実行します (`bada-ide-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`bada_gui_ide/README.md`](bada_gui_ide/README.md) を参照。

### 🌐 ウルトラネットワーク専用ブラウザ (ZoneBrowser) — インストール不要でダウンロード

`https:`/`http:` に代わる暗号化 zone:// を閲覧する**専用ブラウザ**を、**1 ファイルだけ**でどこでも動く自己完結版にしました:

| 入手方法 | 内容 |
|:---|:---|
| **専用ブラウザ (単一 HTML)** ★ | [`bada_gui_ide/dist/zone-browser.html`](bada_gui_ide/dist/zone-browser.html) をダウンロードして開くだけ。アドレスバーに `zone://url.or.jp/` と入力すると、P2P リング DHT でページを解決し、Bell 対 QKD + Jones 量子暗号で復号して表示。戻る/進む・リンク遷移・セキュリティパネル (DHT 鍵/経路/Jones 鍵/AEAD タグ/暗号文) 付き (依存なし・オフライン可) |
| **ランナー (単一 HTML)** | [`bada_gui_ide/dist/bada-zone.html`](bada_gui_ide/dist/bada-zone.html) — `zone.bada` を開くだけで自動実行 |
| **配布 zip** | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-zone-dist.zip` (専用ブラウザ + ランナー + `zone.bada` + `bada.js` + CLI + README)。[`zone-dist.yml`](.github/workflows/zone-dist.yml) が `zone-v*` タグ / `workflow_dispatch` で生成・添付します |
| **CLI** | `node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/zone.bada` |

---

## 🔤 Bada Language — 設計原理

山口フレームワークの作用素環プログラミングを実現するために設計された独自OOP言語。

### 核心設計思想

```
// Bada v3 — 多様体演算子構文例

class ManifoldNode <- TupleSpace {
  operator <- (input) {
    return beta(p,q) / log(input);   // ζ(s) = β(p,q)/log x
  }
  operator -< (state) {
    return gamma(state) * exp(-state * log(state));  // Γ(s)
  }
  operator >- (output) {
    return pi_operator(chi, output);  // π(χ,x) non-commutative
  }
}

Omega::DATABASE[tuplespace] {
  push(ManifoldNode);  // Akashic Record への書き込み
}
```

### 演算子一覧

| 演算子 | 数学的対応 | 説明 |
|:------|:---------|:----|
| `<-`  | `π(χ,x) = [iπ, f(x)]` | 非可換左作用 |
| `-<`  | `∬1/(x·log x)² dx_m` | 多様体積分 |
| `>-`  | `⊕(iℏ∇)^⊕L` | 量子作用素右作用 |
| `Ω::` | `Ω::DATABASE` | TupleSpace名前空間 |

---

## 🖥️ omega_llm エンジン — `omega/` フォルダ

```c
/* omega_math.c — π-softmax 実装 */
double pi_softmax(double* logits, int n, double hbar_eff) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        // ⊕(iℏ∇)^⊕L スケーリング
        sum += exp(logits[i] * hbar_eff * M_PI);
    }
    return sum;
}

/* omega_tuplespace.c — Akashic Record */
void omega_push(OmegaDB* db, const char* key, Manifold* m) {
    // Ω::DATABASE ⊃ Z ⊃ C ⊕ ∇R⁺
    tuplespace_insert(db->akashic, key, manifold_encode(m));
}
```

### ファイル構成

| ファイル | 内容 |
|:--------|:----|
| `omega_core.h` | コアヘッダ · 型定義 · 多様体構造体 |
| `omega_math.c` | π-softmax · gamma-deprivation · β(p,q)積分 |
| `omega_tuplespace.c` | Omega::DATABASE · Akashic Record実装 |
| `omega_attention.c` | ℏ_eff注意スケーリング · Jones多項式カーネル |
| `omega_model.c` | モデル本体 · 推論ループ · 生成サンプリング |

---

## ⚡ Bada++ — `Bada++/` フォルダ

```cpp
// Bada++/manifold_operator.hpp
template<typename T, typename Gamma = GammaFunction<T>>
class ManifoldOperator {
    T pi_operator(T chi, T x) const {
        // π(χ,x) = [iπ(χ,x), f(x)] non-commutative
        return std::complex<T>(0, M_PI) * chi * std::log(x);
    }
    T beta_zeta(T p, T q) const {
        // ζ(s) = β(p,q)/log x
        return gamma_(p) * gamma_(q) / gamma_(p + q);
    }
};
```

---

## 🔗 関連リポジトリ

| リポジトリ | 内容 | リンク |
|:---------|:----|:------|
| **tuplenetwork** | 論文PDF全16本 · TupleSpace理論 · ポートフォリオ | [→](https://masaaki-avnturle.github.io/tuplenetwork/) |
| **tuplenetwork/pdf/** | caostics.pdf · jum.pdf · Bada__1.pdf 等 | [→](https://masaaki-avnturle.github.io/tuplenetwork/pdf/) |
| **tuplenetwork/altmistypdf/** | アミノ医薬・有機化学論文 | [→](https://masaaki-avnturle.github.io/tuplenetwork/altmistypdf/) |
| **tuplenetwork/exceedpdf/** | Secureproduct · Magic演算子 · カタストロフィ | [→](https://masaaki-avnturle.github.io/tuplenetwork/exceedpdf/) |
| **tuplenetwork/origin/** | 1998年原典・研究記録・履歴書 | [→](https://masaaki-avnturle.github.io/tuplenetwork/origin/) |

---

<img src="https://masaaki-avnturle.github.io/tuplenetwork/assets/timeline.svg"
     alt="Research Timeline" width="900"/>

---

<div align="center">

```
β(p,q) = Γ(p)Γ(q)/Γ(p+q)  ·  ζ(s) = x·log x
⊕(iℏ∇)^⊕L = e^{-x·log x}  ·  π(χ,x) = [iπ, f(x)]
        Ω::DATABASE ↔ ∞  ← TupleSpace Akashic
```

[![Portfolio](https://img.shields.io/badge/Full%20Portfolio-masaaki--avnturle.github.io%2Ftuplenetwork-4a80d0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/)

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*

</div>
