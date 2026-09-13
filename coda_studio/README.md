# 𝄌 Coda Studio — 坂本龍一トリビュート スペクトル・コード作曲スタジオ(非公式)

**音楽家・坂本龍一(1952–2023)の音楽性 — ピアノの一音、静寂、アンビエンス、ミニマリズム — へのオマージュとして制作された、オリジナルの音楽制作アプリです。** v2 からは**音符を一切表示しない**作曲方式を採用: 行はコード記号、マス目は 4 段階のスペクトル(倍音の厚み)、**縦線(プレイヘッド)の移動**が演奏です。

依存ライブラリゼロ・単一 HTML(`index.html`)・完全オフライン動作。音はすべて Web Audio API によるリアルタイム・シンセシスで、サンプル素材・既存楽曲・商標はいっさい含みません。

> **免責事項:** 本アプリは非公式のファン・トリビュートです。坂本龍一氏、ご遺族、所属事務所・レーベル等とはいっさい関係がなく、承認・提携を受けたものではありません。また、氏が実際に使用した市販の音楽制作ソフトウェアの複製・模倣品ではなく、その音楽的精神に敬意を表して独自に設計されたオリジナル作品です。

## ✨ 機能

| 機能 | 内容 |
|:---|:---|
| ◫ **スペクトル・コード・シーケンサー** | **音符表示なし。** 行は 8 つのコード記号(Ⅰmaj9 / Ⅳmaj7 / Ⅵm9 / Ⅴsus2 / Ⅲm7 / Ⅱm11 / Ⅰ6-9 / ♭Ⅶmaj7、キー変更可)、列は 16 ステップ。マス目をタップするたびにスペクトル段階が **1 深部 (ルート+5度) → 2 中域 (基本ヴォイシング) → 3 上音 (テンション全開) → 4 輝き (オクターブ重ね)** と深まり、色と倍音の厚みが増す。BPM 40–200、スウィング、「おまかせ生成」 |
| ┃ **縦線プレイヘッド** | ▶ 演奏で光る縦線がグリッド上を滑らかに移動し、通過したコードが鳴る — 目で見ながら作曲を聴ける |
| ▁▃▅▇ **リアルタイム・スペクトラム** | いま鳴っている音の周波数スペクトルを多段階の色(深部→中域→上音→輝き)で常時表示 |
| 🎹 **鍵盤** | 2 オクターブ(シフト可)。グランドピアノ / エレクトリックピアノ / アナログパッド / オルゴールの 4 音色。PC キーボード演奏対応(A W S E D F …)、サステイン切替。音名キャップなし |
| 🎼 **コードパッド** | maj9 / maj7 / m9 / sus2 / m11 / 6-9 など、映画音楽的な柔らかいヴォイシング 8 パッド。キー変更可 |
| 🌫 **エフェクト** | 合成インパルスによるコンボリューション・リバーブ + フィードバック・ディレイ(いずれも量を調整可) |
| 💾 **WAV 書き出し** | シーケンスを `OfflineAudioContext` でエフェクト込みレンダリングし、44.1kHz / 16bit ステレオ WAV でダウンロード(ループ回数指定 + 余韻) |

## 🚀 使い方

1. [`index.html`](index.html) をダウンロード(GitHub 上で開いて「Download raw file」⬇)し、ダブルクリックで開くだけ。インストール不要。
2. またはネイティブアプリ(Android APK / Windows EXE / Ubuntu AppImage・deb)を GitHub Actions / Releases から取得 — 下記参照。

## 📱💻 ネイティブアプリのビルド (GitHub Actions)

ビルドは [`.github/workflows/codastudio-app-build.yml`](../.github/workflows/codastudio-app-build.yml) が実行します。

- **起動方法:** リポジトリの **Actions** タブ → 「Coda Studio app build」→ **Run workflow**。`main` や `claude/**` ブランチへの `coda_studio/**` 変更プッシュでも自動起動。
- **成果物 (Actions アーティファクト):**
  - `codastudio-android` — `coda-studio-debug.apk`(Android 7.0+)
  - `codastudio-windows` — `CodaStudio-*-x64.exe`(NSIS インストーラ / ポータブル、Windows 10・11)
  - `codastudio-linux` — `CodaStudio-*-x86_64.AppImage` / `CodaStudio-*-amd64.deb`(Ubuntu)
- **Release 添付:** `codastudio-v*` タグを打つか、Run workflow 時に `release_tag` を指定すると [Releases](https://github.com/masaaki-avnturle/Bada/releases) に添付されます。

## 🧪 テスト

音楽エンジンの純ロジック(音律・コード・多段階スペクトル・ヴォイシング・シーケンサーのタイミング・WAV エンコード・インパルス生成・パターン生成)は Node で単体テストできます:

```bash
node coda_studio/tools/engine-test.js
```

## 🏗 構成

```
coda_studio/
├── index.html            # アプリ本体 (自己完結・全プラットフォーム共通)
├── tools/engine-test.js  # 音楽エンジン単体テスト (Node)
└── app/
    ├── cordova/config.xml    # Android APK ラッパー設定
    └── electron/             # Windows / Ubuntu ラッパー
        ├── main.js
        ├── preload.js
        └── package.json
```

MIT License
