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

## 🚀 使い方

1. **① 思考入力** に作りたいアプリを書く。例:
   > 読んだ本を管理したい。項目はタイトル、著者、読了日、評価、感想。評価順に並べ替えたい。青いダークなデザインで、スマホとWindowsで使いたい。
   - 🎙 音声入力 (対応環境のみ)、📶 **スマホから電信で受信** (FSK 音、電話のスピーカー越しでも可) でも入力できます。
2. **⚡ 電信して錬成** を押す。② 電信 → ③ 全体把握 → ④ 生成と検証 → ⑤ 論文 が順に進みます。
3. ④ でアプリをプレビュー・操作し、**⬇ アプリ (HTML)**・**📦 ビルド一式 (ZIP)**・**📄 論文 PDF**・**📝 論文 Markdown** を保存。
4. ZIP を GitHub リポジトリに置いて Actions を実行すると、**生成したアプリそのもの**の APK / EXE / AppImage・deb ができます。

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
