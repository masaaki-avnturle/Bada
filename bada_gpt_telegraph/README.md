# 📡🤖 BadaGPT電信 — 思考入力から、依頼の全体を捉えてアプリを錬成する

**BADA グラビトン電信** (`bada_telegraph`) の電信エンジンの上に **BadaGPT** を載せたアプリケーションです。
作りたいアプリを思い描くままに書く (または話す・スマホから音で電信する) と、BadaGPT が

**電信 → 全体把握 → 設計 → 生成 → 検証 → 論文**

の順に Bada プログラム `badagpt.bada` を実行し、

- 依頼の**すべての節**を仕様へ対応付けた「全体把握」(網羅率・節ごとの対応表・仮定・未解釈の節)
- そのまま動く**アプリケーション** (依存ゼロ・オフラインの単一 HTML、画面内でプレビュー)
- 生成過程をまとめた**論文** (Markdown / PDF)
- 生成したアプリを **Android (APK)・Windows 10/11 (EXE)・Linux (AppImage / deb)** にビルドする**一式** (ZIP)

を作ります。依存ゼロ・単一 HTML・API キー不要で完全オフライン動作します。

## 📥 ダウンロード

**[Releases → BadaGPT電信](https://github.com/masaaki-avnturle/Bada/releases/tag/badagpt-telegraph-latest)** から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `bada-gpt-telegraph-debug.apk` (「提供元不明のアプリ」を許可してインストール) |
| **Windows 10 / 11** | `BadaGPTTelegraph-*-x64.exe` (インストーラ) / `BadaGPTTelegraph-*-portable.exe` (インストール不要) |
| **Linux** | `BadaGPTTelegraph-*-x86_64.AppImage` (`chmod +x` して起動) / `BadaGPTTelegraph-*-amd64.deb` (`sudo apt install ./…deb`) |
| **ブラウザ** | `BadaGPTTelegraph-web.html` (ダブルクリックで起動) |
| **論文** | `BadaGPT_Telegraph_paper.pdf` / `.md` |

ビルドは [`badagpt-telegraph-app-build.yml`](../.github/workflows/badagpt-telegraph-app-build.yml) が行います
(`bada_gpt_telegraph/` への push で `badagpt-telegraph-latest` を更新、`badagpt-telegraph-v*` タグでそのタグの Release)。

### ⚙️ Actions からダウンロードする

Release を待たずに、どの実行からでも**全プラットフォームを 1 つの ZIP** で取れます:

1. [Actions → BadaGPT Telegraph app build](https://github.com/masaaki-avnturle/Bada/actions/workflows/badagpt-telegraph-app-build.yml) を開く
2. 一番上の緑の実行 (または **Run workflow** で自分で実行) をクリック
3. ページ下の **Artifacts** から **`badagpt-telegraph-all-platforms`** をダウンロード
   (APK・Windows EXE 2 種・Linux AppImage/deb・ブラウザ版 HTML・論文 PDF/MD・README.txt が入っています)

プラットフォーム別に取りたいときは `badagpt-telegraph-android` / `-windows` / `-linux` を選んでください。
Artifacts のダウンロードには GitHub へのログインが必要です (保存期間 90 日)。

## 🚀 使い方

1. **① 思考入力** に作りたいアプリを書く。例:
   > 読んだ本を管理したい。項目はタイトル、著者、読了日、評価、感想。評価順に並べ替えたい。青いダークなデザインで、スマホとWindowsで使いたい。
   - 🎙 音声入力 (対応環境のみ)、📶 **スマホから電信で受信** (FSK 音、電話のスピーカー越しでも可) でも入力できます。
2. **⚡ 電信して錬成** を押す。② 電信 → ③ 全体把握 → ④ 生成と検証 → ⑤ 論文 が順に進みます。
3. ④ でアプリをプレビュー・操作し、**⬇ アプリ (HTML)**・**📦 ビルド一式 (ZIP)**・**📄 論文 PDF**・**📝 論文 Markdown** を保存。
4. ZIP を GitHub リポジトリに置いて Actions を実行すると、**生成したアプリそのもの**の APK / EXE / AppImage・deb ができます。

## ⓪ サイレント・トーク — イメージした思いを、言葉を介さず動きで入力 (大拡張)

文字や絵文字を選ぶのではなく、頭に**思い描いたもの**を、言葉を介さずに**連続した動き**で
「思いを描く面」になぞります (目を閉じたままでも可)。その動きの**速さ・広がり・向き・曲がり・
リズム・どこに留まったか**を**本物の (小さく決定的な) トランスフォーマー (自己注意 2 層・多頭)** が
読み取って latent に変換します。動きの何がどの意味になったかは「**読み取った思い**」の表に
そのまま表示されます (例: 重心が下・右 → タイマー、広がり → 文章の分量、曲がりの多さ → 勢い・紫、
下側に描いた → 明るいオレンジ)。細かく補いたいときは無言のグリフ (◎ ✦ 📖 ▤ ⇅ …) も足せます。

latent からは決定的に次を復号します:

- 📖 **本と同じ分量まで展開できる文章** (素描〜本一冊 約 96,000 字まで。Markdown / PDF で保存)
- 🖼 **イメージ** (latent から生成した SVG。感覚出力)
- 🅱 **Bada 言語のプログラム** (`silent.bada`。構文エラーなく実行可能)
- ⚡ BadaGPT への**依頼文** → そのまま ①〜⑤ の錬成パイプラインへ

> ※ これは利用者が**自分で描いた動き** (速さ・広がり・向き・曲がり・リズム・重心) を固定の規則で言葉にするもので、**脳の信号は読み取りません**。
> 「読み取った思い」に、動きの何がどの意味になったかをそのまま表示します。
> トランスフォーマーは固定の重みを持つ小さな自己注意ネットワーク (学習済み LLM ではない) で、同じ動きは必ず同じ出力になります。
> 文章は latent に駆動された決定的なテンプレート展開です。

### 🫀 体のサイン — 自分の心拍・呼吸を気分のヒントとして添える (任意)

**自分の指先**をカメラのレンズに当てると脈波 (PPG) から心拍数と心拍変動 (RMSSD) を、マイクから呼吸数を測り、
落ち着き指数にまとめます (BadaGPT改の信号処理を移植)。結果は**気分のヒント (静か / 軽やか / 勢い) としてだけ**
latent に添えられ、**アプリの中身 (モジュール・対象・項目) は決めません** — 単体テストでこの不変条件を検証しています。

> ※ **他人の思考や体内情報を読む機能ではありません。** 通常のカメラで、本人が自分を測る自己計測です。
> 皮膚温・赤外線から思考や言語を推定することは科学的にできず、本アプリはそれを行いません・主張しません。

## 🧭 全体把握とは

依頼文を節に分け、**すべての節**をモジュール・記録対象・項目と型・機能・見た目・対象環境・題名・目的のどれかに対応付けます。
対応付けられなかった節は捨てずに、生成アプリの「この依頼について」画面・論文の考察・(使う場合) Claude へのプロンプトに残します。
依頼にない点を補った**仮定**も同じように明記します。

## 🧩 生成できる部品 (14 種・組み合わせ自由)

記録・管理 (任意の項目) / ToDo / メモ / 家計簿 / タイマー・ポモドーロ / 電卓 / カウンター / クイズ・単語帳 / お絵かき /
単位変換 / 抽選・サイコロ / 習慣 / モールス電信 / 量子回路 (2 qubit)。
検索・並べ替え・CSV / JSON・グラフ・音・印刷・ダーク / ライト・アクセント色を依頼に合わせて付けます。

## 🤖 Claude で生成する (任意)

⑧ 設定に Anthropic の API キーを入れると、全体把握の結果 (未解釈の節を含む) を Claude (既定 Opus 5.5) に渡して、
部品の組み合わせを超えた自由な形のアプリを生成させます。結果は同じ検証にかけ、不合格なら内蔵エンジンの結果を使います。キーは端末内にのみ保存されます。

## 💻 ソースコード化 (⑥)

錬成のあと、全体把握した仕様を**人が読めて実行できるソースコード**に変換します。
記録・管理 (records) は、項目ごとの入力・一覧・検索・並べ替え・CSV 書き出しを持つ
**実際に動く CLI アプリ**として生成されます:

| 言語 | 実行 |
|:--|:--|
| **Python** | `python3 app.py` |
| **Node.js** | `node app.js` |
| **Bada 言語** | `BadaInterp` / 量子ラボ |

その他のモジュールは、仕様をデータとして埋め込んだ**構文的に正しい雛形**として生成します
(完成した動作は HTML アプリ版が担います)。言語を選んで画面で確認し、1 ファイルずつ、または
**全言語まとめて ZIP** で保存できます。生成される Python / Node は構文検査と実行 (追加→一覧→CSV)
まで単体テストで確かめています。

## 📄 論文

[`paper/BadaGPT_Telegraph_paper.pdf`](paper/BadaGPT_Telegraph_paper.pdf) ([Markdown](paper/BadaGPT_Telegraph_paper.md)) —
「BadaGPT電信：思考入力の全体把握に基づくクロスプラットフォーム・アプリケーション生成」。
設計・実装に加え、開発用 24 件 / 未見 10 件の依頼による評価 (未見で F1 81.5%) と、実ブラウザ・実パッケージでの動作確認を報告しています。

## 🧪 開発

```sh
node bada_gpt_telegraph/tools/build.js              # src/ → index.html (CI は --check で一致を検査)
node bada_gpt_telegraph/tools/engine-test.js        # 単体テスト 104 件
node bada_gpt_telegraph/tools/evaluate.js           # 論文 7.2 の評価 (--heldout で 7.3)
cd bada_gpt_telegraph/app/electron && npm install && npm start   # デスクトップ版 (要 ../www/index.html)
```

```
bada_gpt_telegraph/
├── index.html              ← アプリ本体 (src/ から生成・これだけで動く)
├── src/
│   ├── engine.js           ← ZIP / PDF / Markdown・Bada インタプリタ・Ξ・Jones・モールス・FSK
│   ├── comprehend.js       ← 全体把握
│   ├── silent.js           ← サイレント・トーク (非言語 → トランスフォーマー → latent → 文章・画像・Bada)
│   ├── bio.js              ← 体のサイン (本人の PPG 心拍・呼吸 → 気分の tone アトムのみ)
│   ├── codegen.js          ← ソースコード化 (仕様 → Python / Node / Bada の動くソース)
│   ├── generate.js         ← 14 部品・HTML 組み立て・検証
│   ├── paper.js            ← 論文・ビルド一式・Claude (任意)
│   ├── ui.js / shell.html  ← 画面
├── tools/                  ← build.js / engine-test.js / evaluate.js
├── app/electron/           ← Windows EXE / Linux AppImage・deb
├── app/cordova/config.xml  ← Android APK
└── paper/                  ← 論文 (Markdown / PDF)
```

## ⚠️ 正直な範囲

- 「思考入力」は文章・音声・電信 (FSK 音) で入力した依頼文のことで、**脳の信号を読み取る機能はありません**。
- グラビトン↔電磁波変換・量子テレポーテーションの数値は山口フレームワークに基づく**思考実験の可視化**です。
- 依頼の全体把握・アプリ生成・検証・論文・PDF / ZIP 書き出し・FSK 音響通信は**実際に動作**します。
- 内蔵エンジンは規則ベースのため、辞書にない機能は 14 部品の組み合わせでしか表せません (論文 第 8 章)。
