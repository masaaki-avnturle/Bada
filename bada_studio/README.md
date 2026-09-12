# 🎹 Bada Studio — 音楽制作アプリ (macOS / Android / Windows / Ubuntu)

プロ用 DAW と同じ構成要素 — シンセサイザー、ドラムマシン(ステップシーケンサー)、ミキサー、
センドエフェクト、マスターバス録音 — を 1 画面に統合した音楽制作アプリです。

2 つの実装を同梱しています:

| 実装 | 対象 | 中身 |
|:---|:---|:---|
| **ネイティブ macOS 版** (`Sources/`) | MacBook / Mac (macOS 13+) | SwiftUI + **AVAudioEngine (Core Audio)** のリアルタイムレンダースレッドでサンプル単位に波形合成 |
| **Web Audio 版** (`index.html`) | Android APK / Windows 10・11 EXE / Ubuntu AppImage・deb (+ ブラウザ単体でも動作) | 単一 HTML・依存ゼロ。**Web Audio API** でシンセ・ドラム合成、Web Audio クロックでサンプル精度シーケンス |

---

## ⬇️ ダウンロード(このリポジトリから)

[**Releases ページ**](https://github.com/masaaki-avnturle/Bada/releases) の
`badastudio-v*` リリースから、お使いのプラットフォームのファイルを取得してください:

| プラットフォーム | ファイル |
|:---|:---|
| **macOS 13+** (Apple Silicon / Intel universal) | ★ `BadaStudio-macOS-*.dmg`(開いて「アプリケーション」へドラッグ)/ `BadaStudio-macOS-*.zip` |
| **Android** (APK) | `bada-studio-debug.apk` |
| **Windows 10 / 11** | `BadaStudio-*-x64.exe`(NSIS インストーラ)/ `BadaStudio-*-portable.exe`(ポータブル) |
| **Ubuntu** | `BadaStudio-*-x86_64.AppImage` / `BadaStudio-*-amd64.deb` |

インストール不要で今すぐ試すなら:[`index.html`](index.html) を開いて
**「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックでブラウザ起動でも動きます。

### 📦 Actions からのダウンロード(タグ・リリース不要)

`bada_studio/` に触れる push のたびに 2 本のワークフローが自動でビルドするので、
リリースを待たずに **Actions タブから直接ダウンロード**できます:

1. [**Actions タブ**](https://github.com/masaaki-avnturle/Bada/actions) を開く
2. 左のワークフロー一覧から **「Bada Studio app build (macOS DMG)」** または
   **「Bada Studio apps build (Android APK + Windows EXE + Ubuntu)」** を選ぶ
3. 一番上の ✅ 実行をクリック → ページ下部の **Artifacts** 欄から取得
   - `badastudio-macos` (DMG + ZIP) / `badastudio-android` (APK) /
     `badastudio-windows` (EXE) / `badastudio-linux` (AppImage + deb)

Artifacts は zip で落ちてくるので解凍して中のファイルを使ってください
(GitHub にログインしている必要があります。保存期間は既定 90 日)。
Actions タブの「Run workflow」(workflow_dispatch) から手動でビルドを起動することもできます。

### プラットフォーム別の注意

- **macOS**: Apple Developer 証明書を持たない ad-hoc 署名のため、初回のみ
  **右クリック(Control+クリック)→「開く」→「開く」**。または
  `xattr -dr com.apple.quarantine "/Applications/Bada Studio.app"`。2 回目以降は普通に起動します。
- **Android**: 「提供元不明のアプリ」を一時的に許可して APK をインストールしてください(debug 署名のため)。
- **Windows**: SmartScreen が出たら「詳細情報」→「実行」。
- **Ubuntu**: AppImage は `chmod +x BadaStudio-*.AppImage` して実行、deb は
  `sudo apt install ./BadaStudio-*-amd64.deb`。

---

## 🎛 機能(全プラットフォーム共通)

### シンセサイザー(ポリフォニック)
- 波形 4 種: **サイン / ノコギリ / 矩形 / 三角**
- **アタック / リリース** エンベロープ
- 画面の 2 オクターブ鍵盤を**マウス / タッチで演奏**、または **PC キーボードで演奏**
  (`A W S E D F T G Y H U J K O L` = ド から 1 オクターブ上のレ まで、ピアノ配列)
- オクターブ切り替え (C2〜C6)

### ドラムマシン(16 ステップシーケンサー)
- **キック / スネア / ハイハット** の 3 トラック × 16 ステップ
- ドラム音はサンプル再生ではなく**シンセシス**(キック = 160→45Hz ピッチスイープ正弦波、
  スネア = ハイパスノイズ + 190Hz トーン、ハイハット = 6kHz ハイパスノイズ)
- BPM 60〜200、**サンプル精度**のタイミング(macOS = オーディオスレッド内、
  Web 版 = Web Audio クロック先読みスケジューラ)
- 再生中は現在ステップをハイライト表示

### ミキサー & エフェクト
- シンセ / ドラム / マスターの各音量
- センドエフェクト: **ディレイ**(時間・フィードバック・ミックス)→ **リバーブ**
  (macOS = Medium Hall プリセット、Web 版 = 生成インパルス応答のコンボリューション)

### 録音
- **録音ボタン 1 つでマスターバスをそのままファイルに書き出し**
- macOS 版: `~/Music/Bada Studio/BadaStudio-<日時>.caf`(停止すると Finder に表示)
- Web 版 (APK / EXE / AppImage): 停止するとアプリ内で試聴でき、**WAV をダウンロード**ボタンで保存

---

## 🔨 ビルド(自分でビルドする場合)

**macOS ネイティブ版** — macOS 13+ / Xcode 15+ (Swift 5.9+):

```bash
cd bada_studio
swift run                      # そのまま起動
bash scripts/make_app.sh 1.0.0 # dist/ に .app / .dmg / .zip を作成
```

**Web Audio 版** — ビルド不要。`index.html` をブラウザで開くだけ。エンジンの単体テストは:

```bash
node bada_studio/tools/engine-test.js
```

## 🚀 リリースの作り方(メンテナ向け)

タグ `badastudio-v*` を 1 つ push すると、2 本のワークフローが同じ Release に全プラットフォームを添付します:

- [`badastudio-app-build.yml`](../.github/workflows/badastudio-app-build.yml) — macOS DMG / ZIP(macos ランナー、universal バイナリ、ad-hoc 署名)
- [`badastudio-apps-build.yml`](../.github/workflows/badastudio-apps-build.yml) — Android APK(Cordova)+ Windows EXE + Ubuntu AppImage / deb(Electron)

```bash
git tag badastudio-v1.0.0
git push origin badastudio-v1.0.0
```

どちらも Actions タブから `workflow_dispatch` で手動実行もできます
(`release_tag` を空欄にすると Actions アーティファクトのみ)。

---

## 📁 構成

```
bada_studio/
├── index.html                           # ★ Web Audio 版アプリ本体 (単一 HTML・依存ゼロ)
├── Package.swift                        # SwiftPM 定義 (macOS 13+, 依存ゼロ)
├── Sources/BadaStudio/
│   ├── BadaStudioApp.swift              # @main エントリポイント
│   ├── StudioEngine.swift               # AVAudioEngine: シンセ / ドラム / シーケンサー / 録音
│   └── ContentView.swift                # SwiftUI UI: トランスポート / パネル / 鍵盤 / グリッド
├── scripts/make_app.sh                  # macOS .app バンドル + ad-hoc 署名 + DMG / ZIP
├── app/
│   ├── cordova/config.xml               # Android APK 用 Cordova 設定
│   └── electron/                        # Windows / Ubuntu 用 Electron ラッパー
│       ├── package.json                 #   electron-builder (NSIS / portable / AppImage / deb)
│       ├── main.js
│       └── preload.js
└── tools/engine-test.js                 # Web 版エンジンの単体テスト (node で実行)
```
