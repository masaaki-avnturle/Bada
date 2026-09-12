# 🎹 Bada Studio — macOS (MacBook) 専用 音楽制作アプリ

**Apple の MacBook / Mac 専用**に作られた、SwiftUI + AVAudioEngine のネイティブ音楽制作アプリです。
プロ用 DAW と同じ構成要素 — シンセサイザー、ドラムマシン(ステップシーケンサー)、ミキサー、
センドエフェクト、マスターバス録音 — を 1 画面に統合しています。

Web ラッパーではなく、Core Audio(AVAudioEngine)の**リアルタイムレンダースレッド上で
サンプル単位に波形を合成**する本物のネイティブアプリです。

---

## ⬇️ ダウンロード(このリポジトリから)

[**Releases ページ**](https://github.com/masaaki-avnturle/Bada/releases) の
`badastudio-v*` リリースから、どちらかを取得してください:

| ファイル | 内容 |
|:---|:---|
| `BadaStudio-macOS-<version>.dmg` | ★ おすすめ。開いて `Bada Studio.app` を「アプリケーション」へドラッグ |
| `BadaStudio-macOS-<version>.zip` | 解凍すると `Bada Studio.app` が出てきます |

Apple Silicon (M1/M2/M3/M4) と Intel Mac の両対応(universal バイナリ)。macOS 13 Ventura 以降。

### 初回起動(Gatekeeper について)

このアプリは Apple Developer 証明書を持たない **ad-hoc 署名**のため、初回のみ macOS に
ブロックされます。次のどちらかで起動できます:

1. `Bada Studio.app` を **右クリック(Control+クリック)→「開く」→「開く」**
2. または、ターミナルで検疫属性を外す:

   ```bash
   xattr -dr com.apple.quarantine "/Applications/Bada Studio.app"
   ```

2 回目以降は普通にダブルクリックで起動します。

---

## 🎛 機能

### シンセサイザー(8 ボイス ポリフォニック)
- 波形 4 種: **サイン / ノコギリ / 矩形 / 三角**
- **アタック / リリース** エンベロープ
- 画面の 2 オクターブ鍵盤を**マウスで演奏**、または **PC キーボードで演奏**
  (`A W S E D F T G Y H U J K O L` = ド から 1 オクターブ上のレ まで、ピアノ配列)
- オクターブ切り替え (C2〜C6)

### ドラムマシン(16 ステップシーケンサー)
- **キック / スネア / ハイハット** の 3 トラック × 16 ステップ
- ドラム音はサンプル再生ではなく**シンセシス**(キック = ピッチスイープ正弦波、
  スネア = ノイズ + トーン、ハイハット = 差分フィルタしたノイズ)
- BPM 60〜200、**オーディオスレッド内でサンプル精度**のタイミング
- 再生中は現在ステップをハイライト表示

### ミキサー & エフェクト
- シンセ / ドラム / マスターの各音量
- センドエフェクト: **ディレイ**(時間・フィードバック・ミックス)→ **リバーブ**(Medium Hall)

### 録音
- **録音ボタン 1 つでマスターバスをそのままファイルに書き出し**
- 保存先: `~/Music/Bada Studio/BadaStudio-<日時>.caf`(停止すると Finder に表示)
- `.caf` は QuickTime / Logic / GarageBand / ffmpeg でそのまま読めます

---

## 🔨 ビルド(自分でビルドする場合)

macOS 13+ / Xcode 15+ (Swift 5.9+) で:

```bash
cd bada_studio
swift run                      # そのまま起動
bash scripts/make_app.sh 1.0.0 # dist/ に .app / .dmg / .zip を作成
```

依存パッケージはゼロ(Apple 標準の SwiftUI / AVFoundation のみ)です。

## 🚀 リリースの作り方(メンテナ向け)

ビルドは GitHub Actions の
[`badastudio-app-build.yml`](../.github/workflows/badastudio-app-build.yml)
が macOS ランナーで実行します。

- タグ `badastudio-v1.0.0` を push → DMG / ZIP が自動ビルドされ、その Release に添付
- または Actions タブから `workflow_dispatch` で手動実行
  (`release_tag` を空欄にすると Actions アーティファクトのみ)

```bash
git tag badastudio-v1.0.0
git push origin badastudio-v1.0.0
```

---

## 📁 構成

```
bada_studio/
├── Package.swift                        # SwiftPM 定義 (macOS 13+, 依存ゼロ)
├── Sources/BadaStudio/
│   ├── BadaStudioApp.swift              # @main エントリポイント
│   ├── StudioEngine.swift               # AVAudioEngine: シンセ / ドラム / シーケンサー / 録音
│   └── ContentView.swift                # SwiftUI UI: トランスポート / パネル / 鍵盤 / グリッド
└── scripts/make_app.sh                  # .app バンドル + ad-hoc 署名 + DMG / ZIP
```
