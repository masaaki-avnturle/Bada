# ⛩ BadaGPT道場 — ChatGPTの技を量子Badaで伝授する技術伝授アプリ

**ChatGPT が「応答し、アプリケーションを作る」ときに使っている技を、量子プログラミング言語 Bada の上でユーザーに伝授するアプリケーション。**

BadaGPT は応答するたびに自分のパイプライン (技の内部) を開示します。道場カリキュラムで七つの技をひとつずつ稽古し、印可を集めると **免許皆伝** です。

依存ゼロ・単一 HTML・オフライン動作。

## 🚀 使い方

[`index.html`](index.html) を開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動 (インストール不要)。

## 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-gpt-dojo-debug.apk` |
| **Windows 10 / 11** | `BadaGPTDojo-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaGPTDojo-*-x86_64.AppImage` / `BadaGPTDojo-*-amd64.deb` |

ビルドは [`badagptdojo-app-build.yml`](../.github/workflows/badagptdojo-app-build.yml) が実行します (`badagptdojo-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。

## 🥋 伝授する七つの技

ChatGPT が試行している「応答してアプリケーションを作る」手順を、実行できる形で分解して伝授します:

| # | 技 | 内容 |
|:--|:--|:--|
| 一 | **トークン化** | 文章をトークンに刻む。`gptTokenize` の実演と稽古 |
| 二 | **自己注意 (self-attention)** | Q·Kᵀ/√d → softmax の本物の順伝播。attention 行列を表示 (各行の合計 = 1) |
| 三 | **次トークン予測** | 文脈ベクトル×語彙埋め込み + 学習頻度 → softmax。応答は一手ずつの予測の連なり |
| 四 | **意図解析** | 「何を求められたか」の判定 (bell / scaffold / gui / complete / …) |
| 五 | **計画と生成 (アプリ錬成)** | ①要件抽出 → ②資源名決定 → ③フィールド設計 → ④コード生成 → ⑤検証 の 5 手 |
| 六 | **検証と自己修正** | 生成したら実行して検証し、エラーなら直す |
| 七 | **量子 Bada** | H + CNOT でベル状態 (もつれ)。`qubit / H / X / Z / CNOT / measure / state` |

## 🖥 4 つのタブ

- **⛩ 道場** — 七つの技のカリキュラム。伝授 (解説) → 師範の実演 → 稽古 → 判定。合格で 🈴 印可、段位が 入門 → 初伝 → 中伝 → 奥伝 → **免許皆伝** と進む (localStorage に永続化)
- **🤖 BadaGPT** — 対話。応答のたびに「🔍 技を見る」で **トークン化 → 意図解析 → 計画 → 生成 → 検証 → 応答** の全 6 段階を開示
- **🛠 アプリ錬成** — 日本語の依頼文からアプリを錬成。「Book title:string を管理するアプリ」→ Bada on Rails scaffold、「ボタンのある画面」→ GUI Bada、その他 → 量子デモ。全手順を開示
- **⚛ 量子ラボ** — 量子 Bada 実行系 (Bada VM Pro と同一文法)。ベル状態 / GHZ 状態 / let・print

## 🧪 テスト

```sh
node bada_gpt_dojo/tools/engine-test.js
```

量子インタープリタ (ベル/GHZ/エラー報告)、トークナイザ、self-attention の行和、次トークン予測、意図解析、パイプラインの 6 段階開示、アプリ錬成、印可判定と段位を検証します。

## 📁 構成

```
bada_gpt_dojo/
├── index.html            ← アプリ本体 (自己完結・これだけで動く)
├── tools/engine-test.js  ← エンジン単体テスト (Node)
└── app/
    ├── cordova/config.xml    ← Android APK 用 Cordova 設定
    └── electron/             ← Windows EXE / Ubuntu AppImage・deb 用
        ├── package.json
        ├── main.js
        └── preload.js
```
