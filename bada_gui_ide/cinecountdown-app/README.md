# 🎬 Bada 映画カウントダウンエディタ (BadaCineCountdown)

映画の冒頭に流れる**フィルムリーダー(カウントダウン)**— クラシックな
**SMPTE ユニバーサル・リーダー**(1 秒ごとに 1 回転する掃引ハンド、大きな数字、
全画面の十字、外周リング、フィルムグレイン、ビネット、整数切替フラッシュ、
指定番号でのビープ)— を編集してプレビューし、**動画や画像として書き出す**
デスクトップ/モバイル アプリです(依存ゼロ・オフライン・端末内完結)。

BadaCineVim と同じ「シネマ」路線の付属アプリ。`countdown.js` のエンジンは
`neovim/` の mini-Vim と同様に純 JS・Node でも検証できます。

## できること

- **編集** — 開始/終了番号(既定 8→2)、1 番あたりの秒数、FPS、末尾の黒、
  タイトル/サブタイトル、テーマ(Academy 白黒 / Amber / Blue / Green / Mono)、
  配色、掃引ハンド・十字・グレイン・ビネット・レターボックス・フラッシュの ON/OFF、
  ビープ(1 回 or 各整数、鳴らす番号)。
- **プレビュー** — 再生 / 先頭 / シークバーでリアルタイム確認。
- **書き出し**
  - 🎬 **WebM 動画** — Canvas を `MediaRecorder` で録画(ビープ音も収録)。本物の動画ファイル。
  - 🖼 **PNG** — 現在フレームを静止画で保存。
  - 💾 **設定 JSON** — 設定を保存/共有。
  - 📄 **単体 HTML プレーヤー** — エンジン同梱の自己完結 HTML(ブラウザで開くと再生)。

## ⬇️ ダウンロード / ビルド

### GitHub Actions アーティファクト(タグ不要)
`main` または作業ブランチへ push すると
[**CineCountdown app build**](../../../../actions/workflows/cinecountdown-app-build.yml)
が走り、下記がアーティファクトとして出ます(`workflow_dispatch` でも可):

| アーティファクト | 中身 |
|---|---|
| `cinecountdown-windows` | Windows 10/11 NSIS インストーラ + ポータブル EXE |
| `cinecountdown-linux`   | Ubuntu 向け AppImage + deb |
| `cinecountdown-android` | Android APK |

### GitHub Release に添付
`cinecountdown-v*` タグ(例 `cinecountdown-v1.0.0`)を push するか、
`workflow_dispatch` の `release_tag` に指定すると、その Release に
EXE / AppImage / deb / APK が添付されます。

### ローカルで動かす
```bash
# デスクトップ (Electron)
cd bada_gui_ide/cinecountdown-app/electron
npm install && npm start

# ブラウザで直接: www/index.html を開くだけ (完全自己完結)
```

## テスト

```bash
node bada_gui_ide/cinecountdown-app/test/countdown-test.js
# => ALL COUNTDOWN TESTS PASSED
```

数列(8→2)、尺とフレーム数、時刻ごとの数字推移、掃引角度(1 秒で 1 回転)、
整数フラッシュ、ビープ時刻、done フェーズ、Canvas レンダラが落ちないこと、など
27 項目を検証します(CI の `test-core` で実行)。GUI は Playwright/Chromium の
スモークで、描画・再生・シーク・テーマ切替・PNG/JSON/HTML 書き出しまで確認済みです。

## 構成

```
cinecountdown-app/
├─ www/
│  ├─ index.html     # エディタ UI (編集 / プレビュー / 書き出し)
│  └─ countdown.js   # エンジン + Canvas レンダラ (純 JS, Node 検証可)
├─ electron/         # Windows EXE / Ubuntu AppImage・deb ラッパー
├─ cordova/          # Android APK 設定
└─ test/countdown-test.js
```

MIT License — https://github.com/masaaki-avnturle/Bada
