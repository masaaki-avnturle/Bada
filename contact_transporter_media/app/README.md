# Blueprint Studio — 輸送機 / ChatGPT / UFO 設計図作成ソフト

動画 (`../output/*.mp4`) と設計図 PDF を作ったシステムを、そのままアプリにしたものです。
3 つのアプリは共通エンジン (`src/engine.js`) を使い、アプリ内で

- 動画のプレビュー再生 (シーン選択・シーク)
- **設計図 PDF の作成と保存** (A4 横, 7〜9 ページ)
- **動画 mp4 の作成と保存** (1280×720 / 1920×1080 / 854×480、音声付き)

を行います。ネット接続は不要です。

| アプリ | ソース | 内容 |
|---|---|---|
| 輸送機設計図作成ソフト | `src/transporter.js` | contact_blueprint.pdf の方程式 2111 本 → 部品 → 平面図 → 3D → 組み立て → 起動・輸送 |
| ChatGPT 設計図作成ソフト | `src/chatgpt.js` | GPT 系 Transformer の部品と方程式 → 平面図 → 3D → 組み立て → 推論 (注意行列はアプリ内で実計算) |
| UFO 設計図作成ソフト | `src/ufo.js` | 反重力の方程式 UFO.1〜26 → 部品 → 平面図 → 3D → 組み立て → 飛行 (制御ループが毎秒方程式を評価) |

## ダウンロード (GitHub Actions)

`.github/workflows/blueprint-apps-build.yml` が、`contact_transporter_media/app/` を変更して push するたびに
(または Actions 画面の「Run workflow」で) 3 アプリ × 3 プラットフォームをビルドします。
Actions → 「Blueprint apps build」→ 実行結果ページ下部の **Artifacts** からダウンロードできます。

| アーティファクト | 中身 |
|---|---|
| `transporter-blueprint-android` / `chatgpt-blueprint-android` / `ufo-blueprint-android` | APK (デバッグ署名。インストール時に「提供元不明のアプリ」を許可) |
| `transporter-blueprint-windows` / `chatgpt-blueprint-windows` / `ufo-blueprint-windows` | Windows 10/11 用 EXE (インストーラ + ポータブル版) |
| `transporter-blueprint-linux` / `chatgpt-blueprint-linux` / `ufo-blueprint-linux` | Linux 用 AppImage と deb |

`blueprint-v*` タグを push するか、Run workflow で `release_tag` を指定すると GitHub Release にも添付されます。

## 動画の書き出しについて

mp4 は WebCodecs でエンコードし、`vendor/mp4-muxer.js` (MIT) で mp4 に格納します。
映像コーデックは H.264 → VP9 → AV1 の順に端末が対応するものを使います (いずれも .mp4)。
音声は AAC、非対応環境では Opus です。書き出し中はアプリを閉じないでください。

## 開発

```sh
node tools/engine-test.js                      # 数値テスト (レポート値との一致・全フレーム描画)
node tools/build_www.js ufo /tmp/www-ufo       # 自己完結 HTML を生成 (ブラウザで index.html を開けば動く)
node tools/prepare.js ufo electron /tmp/e-ufo  # Electron プロジェクト (cd /tmp/e-ufo && npm i && npm run dist:linux)
node tools/prepare.js ufo cordova /tmp/c-ufo   # Cordova 用 config.xml + www
```

フォント: IPA ゴシック (`fonts/ipag.ttf`, IPA Font License v1.0 — `fonts/IPA_Font_License.txt`)。

> ※ 輸送機・UFO は論文の方程式に基づく思索的・フィクションの設計図です。ChatGPT は公開論文に基づく図解モデルで、
> 実機の非公開の構成を示すものではありません。
