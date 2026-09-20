# 🎬 Bada SoundFilm — MP3 → 動画 変換スタジオ

**MP3 を動画に変換するソフト。** 音楽ファイルを読み込むと、曲名・アーティスト名・ジャケット画像を自動で読み取り、音に反応するビジュアライザ付きの動画(MP4 / WebM)に変換します。YouTube・SNS への音楽投稿用動画づくりに。依存ゼロ・単一 HTML・完全オフライン動作。

## ✨ できること

- **MP3 → 動画変換** — MP3(ほか WAV / OGG / M4A / FLAC などブラウザが再生できる音声)を、音声付き動画ファイルへ変換
- **ID3 タグの自動解析** — ID3v2.3 / v2.4(TIT2 曲名 / TPE1 アーティスト / TALB アルバム / APIC ジャケット画像)と ID3v1 フォールバックを自前実装で解析し、動画に自動反映
- **4 種のビジュアライザ** — スペクトラムバー / サークル / 波形 / シンプル(FFT を対数スケールで 64 バーに集計)
- **解像度プリセット** — 1920×1080(フル HD)/ 1280×720 / 1080×1080(正方形)/ 1080×1920(縦型ショート)、24 / 30 / 60 fps
- **カスタマイズ** — 背景色・背景画像・曲名表示の ON/OFF
- **複数ファイルの連続変換** — キューに積んで順番に変換、1 曲ずつ保存
- **プレビュー再生** — 変換前に仕上がりをそのまま確認

## 🎥 出力形式

環境が対応していれば **MP4 (H.264 + AAC)**、それ以外は **WebM (VP9/VP8 + Opus)** で出力します(画面右上のバッジに実際の出力形式が表示されます)。変換は **リアルタイム録画** のため、曲の長さと同じ時間がかかります。変換中はウィンドウを前面に表示したままにしてください。

## 💾 保存

「💾 動画を保存」を押すと、環境ごとにいちばん確実な方法で保存します:

1. **Android (APK)** — 保存ダイアログ(SAF)が開き、保存先フォルダとファイル名を選べます(`cordova-plugin-save-dialog`)
2. **Windows / Ubuntu / Chrome / Edge** — ネイティブの保存ダイアログ(`showSaveFilePicker`)
3. **それ以外のブラウザ** — 通常のダウンロードとして保存

## ⚙ 仕組み

1. `FileReader` → **ID3 パーサ**(自前実装: syncsafe 整数 / latin1 / UTF-16 BOM / UTF-8 / APIC 画像抽出)
2. `AudioContext.decodeAudioData` で音声をデコード
3. `AnalyserNode` の FFT を **対数スケールで集計**して Canvas にビジュアライザを描画
4. `canvas.captureStream(fps)` の映像トラック + `MediaStreamAudioDestinationNode` の音声トラックを合成
5. `MediaRecorder` で MP4 / WebM へ録画 → `Blob` としてダウンロード保存

外部ライブラリ・サーバーは一切使いません。音楽ファイルが端末の外に出ることはありません。

## 🚀 使い方

1. [`index.html`](index.html) を「Download raw file」で保存 → ダブルクリック(インストール不要)
2. MP3 をドロップ → 設定を選ぶ → **⚡ すべて変換** → **💾 動画を保存**
3. または [Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-soundfilm-debug.apk` |
| **Windows 10 / 11** | `BadaSoundFilm-*-x64.exe`(NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaSoundFilm-*-x86_64.AppImage` / `BadaSoundFilm-*-amd64.deb` |

ビルドは [`soundfilm-app-build.yml`](../.github/workflows/soundfilm-app-build.yml) が実行します(`soundfilm-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。

## 🧪 テスト

```
node mp3_to_video/tools/engine-test.js
```

整形(fmtTime / fmtBytes)、ファイル名からの曲情報推定(parseTrackMeta / sanitizeName)、録画形式の選択(pickRecorderMime)、ビットレート・サイズ見積り(videoBitrate / estimateSize)、スペクトラム集計(spectrumBars / energyOf)、ID3 タグ解析(ID3v2.3 / v2.4 / ID3v1 / APIC / 壊れたタグ)を Node 単体テストで検証します。
