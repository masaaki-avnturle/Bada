# ✨ BadaGPT改 — イメージから APK / Windows EXE / PDF / ソースコードを生成

**頭に描いたイメージを、文章・音声・スケッチ・写真で BadaGPT改 に渡すと、Claude がそれをコードに変換し、Android APK と Windows 10/11 EXE 用のプロジェクト、PDF 文書、任意言語のソースコードとして出力します。**
指先の脈波 (カメラ) と呼吸音 (マイク) から心拍・心拍変動・呼吸数を測るバイオフィードバックを内蔵しており、その「身体のリズム」を生成物の雰囲気 (色・テンポ) のヒントとして添えられます。

依存ゼロ・単一 HTML。API キーがなくても端末内の簡易生成 (オフライン) で動きます。

## 📱💻 ダウンロード

[Releases → `badagptkai-latest`](https://github.com/masaaki-avnturle/Bada/releases/tag/badagptkai-latest) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-gpt-kai-debug.apk` — 「提供元不明のアプリ」を許可してインストール |
| **Windows 10 / 11** | `BadaGPTKai-*-x64.exe` (インストーラ) / `BadaGPTKai-*-portable.exe` (インストール不要) |
| **Ubuntu** | `BadaGPTKai-*-x86_64.AppImage` / `BadaGPTKai-*-amd64.deb` |

ブラウザで試すだけなら [`index.html`](index.html) を保存してダブルクリック。

ビルドは [`badagptkai-app-build.yml`](../.github/workflows/badagptkai-app-build.yml) が行います。`bada_gpt_kai/` を変更して push すると `badagptkai-latest` が更新され、`badagptkai-v*` タグを push するとそのタグの Release ができます。

## 🧭 使い方

1. **④ 設定** に Claude の API キー ([console.anthropic.com](https://console.anthropic.com/)) を入れる。空欄なら端末内の簡易生成になります。
2. **① イメージ入力** で名前・出力形式 (APK+EXE / APK / EXE / PDF / 任意のソースコード) を選び、イメージを文章 (🎙 音声入力も可) とスケッチ・写真で伝える。
3. (任意) **② バイオフィードバック** で心拍・呼吸を測る。音とガンマ関数の模様で返ってきます。
4. **✨ 生成する** → **③ 生成結果** にファイルが並びます。
   - **📦 ZIP で保存** — プロジェクト一式 (Android: アプリ専用フォルダ `Android/data/io.github.masaaki_avnturle.badagptkai/files/`)
   - **📄 PDF を保存** — 出力形式が PDF のとき
   - **⬆ GitHub にプッシュしてビルド** — 自分のリポジトリに 1 コミットで送り、同梱のワークフローが **APK と Windows EXE を自動でビルド**して Release `<名前>-latest` に添付します

### GitHub トークン

Fine-grained token を作り、対象リポジトリに **Contents: Read and write** と **Workflows: Read and write** を付けてください (ワークフローファイルを書き込むため Workflows 権限が必要です)。既定では `badagpt-kai-apps` ブランチにプッシュします (なければ既定ブランチから作ります)。

### 生成されるプロジェクトの形

```
apps/<名前>/www/index.html          ← アプリ本体 (Claude が生成・自己完結)
apps/<名前>/cordova/config.xml      ← Android APK 用 (BadaGPT改 の雛形)
apps/<名前>/electron/package.json   ← Windows EXE 用 (同上)
apps/<名前>/electron/main.js
.github/workflows/<名前>-build.yml  ← push で APK / EXE をビルド
```

PDF は `apps/<名前>/document.md` と `document.pdf`、任意のソースコードは `apps/<名前>/` 以下に Claude が書いた構成のまま入ります。

## 🔬 しくみ

| 部分 | 内容 |
|:--|:--|
| 生成 | Claude Messages API をストリーミングで呼び出し (既定 `claude-opus-5-5`、effort `high`)。安全分類器に拒否されたときは代替モデルへ自動で回す `fallbacks: "default"` を有効にしています。出力は `=== FILE: path ===` 形式で受け取り、パスを検査してから取り込みます |
| パッケージング | Cordova (cordova-android 12) と Electron (electron-builder, NSIS + portable) の雛形と GitHub Actions ワークフローは BadaGPT改 が決定的に生成し、Claude の出力では上書きしません |
| PDF | Markdown を Canvas にページ描画 (端末のフォントで日本語も可) → JPEG → 自前の PDF ライタで埋め込み |
| ZIP | 自前の無圧縮 ZIP ライタ (UTF-8 ファイル名) |
| 心拍 | カメラの赤チャネル輝度 (PPG) を反転・基線除去・平滑化し、ピーク間隔から心拍数と RMSSD を算出 |
| 呼吸 | マイク音量の包絡を平滑化・基線除去し、ヒステリシス付き交差から呼吸数を算出 |
| 落ち着き指数 | RMSSD (80ms で満点) と、呼吸数の 6 回/分 (共鳴呼吸) への近さの平均 |
| 音 | 両耳にわずかに違う周波数を流すドローン (落ち着くほど唸りがゆっくり) + 拍動ごとの音 |
| Γ(z) | Lanczos 近似 (g=7) + 相反公式による複素ガンマ関数。色 = arg Γ(z)、明るさ = log\|Γ(z)\| |

## ⚠ できないこと (正直な範囲)

- **思考を直接読み取ることはできません。** Neuralink の「Telepathy」は脳に埋め込んだ電極で運動野の神経活動を読み取る医療機器で、スマートフォンやPCのソフトウェアだけでは実現できません。BadaGPT改 への入力は、あなたが言葉・音声・スケッチ・写真で表したイメージです。
- 心拍・呼吸は身体の状態であって思考の内容ではありません。生成には雰囲気のヒントとしてのみ使います。
- アカシックレコードへのアクセス、未来予知、体内・脳内の熱の流れの観測はできません (ガンマ関数の模様は数学アートです)。
- 医療機器ではありません。測定値は目安です。
- API キーと GitHub トークンは端末内 (「記憶する」をオフにすると閉じた時点で消える) にだけ保存され、それぞれ api.anthropic.com / api.github.com にだけ送られます。Claude の利用料金は API キーの持ち主に発生します。

## 🧪 開発

```sh
node bada_gpt_kai/tools/build.js        # src/ → index.html を組み立てる
node bada_gpt_kai/tools/engine-test.js  # エンジン単体テスト (index.html 内のコードを検証)
```

```
bada_gpt_kai/
├── index.html            ← アプリ本体 (build.js が生成。APK / EXE に同梱)
├── src/
│   ├── shell.html        ← 画面とスタイル
│   ├── engine.js         ← 純ロジック (ZIP / PDF / Claude / 雛形 / 生体信号 / Γ(z))
│   └── ui.js             ← 画面・センサー・通信
├── tools/
│   ├── build.js
│   └── engine-test.js
└── app/
    ├── cordova/config.xml    ← Android APK 用 (カメラ・マイク権限)
    └── electron/             ← Windows EXE / Ubuntu 用
```
