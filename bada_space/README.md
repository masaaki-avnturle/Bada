# BADA SPACE — 空間コンピューティング

**Apple Vision Pro / visionOS の空間UIを参考にした、浮遊グラス・ウィンドウのホーム体験**

深い宇宙空間のような環境（Environment）のなかに、すりガラス（frosted glass）の
ウィンドウが浮かびます。視線レティクル（gaze reticle）でウィンドウを見つめて
ハイライトし、ドラッグで空間内に配置。下部ドックの「イマーシブ」スライダーで
没入度（背景の暗さ・ぼけ）を調整でき、環境（オーロラ / 山 / 宇宙）を切り替えられます。

> 🍎 **Apple Vision Pro / visionOS を参考にしたオリジナルデザインです。**
> Apple のロゴ・商標・実際の visionOS ソフトウェアは含まれていません。Apple とは無関係です。
> ジェスチャや空間ウィンドウの“考え方”のみを参考にした独自実装です。

---

## ✨ 機能

| 機能 | 内容 |
|:---|:---|
| **浮遊グラス・ウィンドウ** | 時計 / 天気 / ミュージック（ライブ波形）/ 写真 / 3D（回転ワイヤーフレーム）/ ブラウザ |
| **視線レティクル** | 画面中央の注視点。ウィンドウを見つめるとハイライト |
| **空間ドラッグ** | ウィンドウのバーを掴んで空間内を自由に移動 |
| **イマーシブ・ダイヤル** | Digital Crown 風スライダーで没入度（背景の暗さ・被写界深度ぼけ）を無段階調整 |
| **環境切替** | オーロラ / 山岳 / ディープスペース の3環境 |
| **ホーム・グリッド** | アプリ一覧から各ウィンドウを開閉 |
| **視差 / ジャイロ** | マウス移動・端末の傾き（スマホ）で空間に奥行きの視差 |

すべて**完全オフライン**（Canvas 2D + DOM のみ、外部通信なし）で動作します。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `BadaSpace-x.y.z-debug.apk` |
| **Windows 10/11** | `BadaSpace Setup x.y.z.exe`（インストーラ） / `BadaSpace-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します。

---

## 🛠 自分でビルド

```bash
cd bada_space
npm install
npm start                 # Electron でデスクトップ起動
npm run dist:win          # Windows 10/11 用 EXE
npx cap add android && npx cap sync android && cd android && ./gradlew assembleDebug
```

## 🤖 GitHub Actions

`Actions` → **Build Bada Space** → Run workflow で APK / EXE を自動生成。
タグ `space-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
