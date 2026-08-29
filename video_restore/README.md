# 動画リストア — Video Restore Studio

**編集(色補正・明るさ・コントラスト・彩度・色相・ネガ反転・回転・反転・ズーム・再生速度)された動画** を、
**逆補正して元の映像に近づける** アプリです。ブラウザでも動き、**Android APK** としてもビルドできます。
依存ライブラリなし・**すべて端末内で完結**(動画はどこにも送信されません)。

> ⚠ 逆補正は **近似** です。**切り取られた画素やカット編集で失われた情報は復元できません**
> (トリミング/カットの完全復元は原理的に不可能)。素材の取り扱いは各自の権利と責任の範囲で。

---

## できること

- 🎬 **読み込み**: 動画ファイル(MP4 / WebM / MOV など端末対応形式)。
- 🎨 **色の逆補正**: 明るさ / コントラスト / 彩度 / 色相回転 / ネガ反転(invert)戻し / 白黒・セピア戻し。
- 🔄 **かたちの逆補正**: 回転(90/180/270)戻し / 左右・上下反転戻し / ズーム・位置(トリミング/ズーム編集の再フレーミング)。
- ⏩ **速度の逆補正**: 倍速編集を戻す再生速度倍率(編集倍率の逆数が目安)。
- 🔍 **色を自動推定**: 現在フレームの平均輝度・彩度を測り、中庸へ戻す初期値を提案。
- ⬇ **書き出し**: 逆補正後の映像を実時間録画して **WebM(映像+音声)** で保存。

## 使い方(ブラウザ)

```bash
cd video_restore/www
python3 -m http.server 8000     # → http://localhost:8000/
```

1. **① 読み込み** — 動画ファイルを選択。プレビューが Canvas に表示されます。
2. **② 編集を戻す** — 「色を自動推定」で初期値 → スライダー/ボタンで微調整(リアルタイム反映)。
3. **③ 書き出す** — 「逆補正した動画を書き出す(WebM)」。頭から実時間で録画し、終了で自動保存。

## ネイティブ アプリ (Android APK / Windows 10・11 / Ubuntu)

**偽のバイナリはリポジトリに置いていません。** 実際のインストーラは GitHub Actions がビルドします。

| プラットフォーム | 成果物 | 技術 |
|:--|:--|:--|
| **Android** | `video-restore-debug.apk` | Cordova |
| **Windows 10 / 11** | `Video-Restore-Studio-*-x64.exe`(NSIS / ポータブル) | Electron |
| **Ubuntu** | `Video-Restore-Studio-*-x86_64.AppImage` / `*-amd64.deb` | Electron |

### ダウンロード手順

1. GitHub の **Actions** タブ → **「Restore apps build (APK + Windows + Ubuntu)」** → **Run workflow**。
   完了後、各 **Artifacts**(`video-restore-android` / `video_restore-windows` / `video_restore-linux`)から取得。
2. **Releases から配布**する場合はタグを push:
   ```bash
   git tag restore-v1.0.0 && git push origin restore-v1.0.0
   ```
   `.github/workflows/restore-apps-build.yml` が3プラットフォーム分をビルドし、[Releases](https://github.com/masaaki-avnturle/Bada/releases) に添付します。

> デスクトップ版(Electron)は `captureStream` に対応しており書き出しが安定します。
> Android は WebView が captureStream 非対応の場合、書き出し不可(プレビュー調整は可能)。

## 仕組み — `www/vfx.js`(UMD / 純粋関数)+ Canvas

- **色補正**: `buildFilter()` が CSS `filter`(brightness/contrast/saturate/hue-rotate/invert/…)を生成し、
  各フレームを `<video>` → `<canvas>` へ描画する際に適用。
- **かたち**: Canvas の `rotate` / `scale`(反転)/ `translate`(ズーム・位置)で変換。
- **自動推定**: `analyzePixels()` で輝度・彩度統計 → `suggestCorrection()` が逆補正の初期値を算出。
- **書き出し**: `canvas.captureStream()` の映像 + `video.captureStream()` の音声を合成し、`MediaRecorder` で WebM 録画。

映像処理は Canvas / MediaRecorder に依存するためブラウザ実行が前提です。`vfx.js` の計算部分のみ Node で単体テストしています。

## テスト

```bash
node video_restore/test/vfx.test.mjs      # 23 件
```

## ファイル構成

```
video_restore/
├── www/index.html      … UI(プレビュー + 逆補正)
├── www/vfx.js          … 映像補正コア(UMD)
├── cordova/config.xml  … Android APK 設定
├── electron/           … Windows / Ubuntu 用ラッパー(main.js + package.json)
├── test/vfx.test.mjs
└── README.md
```

## 制限

- **トリミング/クロップ/カットで失われた画素は復元不可**(表示範囲の再フレーミングのみ)。
- ガンマや高度なカラーグレーディングの完全逆変換はできません(明るさ/コントラスト/彩度/色相での近似)。
- 書き出しは **WebM**。端末/WebView が `captureStream` 非対応の場合は書き出し不可(プレビュー調整は可能)。
- 実時間録画のため、書き出しには動画の長さ分の時間がかかります。
