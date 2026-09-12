# 🕶 Mimir(ミーミル)— ARグラス・コンシェルジュ

**今までの集大成のシステム**として、タブレット / スマートフォン上の**画像や文章を
AR グラスへ投影**し、**コンシェルジュとして応対**する自己完結アプリです。
投影光学系は**特殊相対性理論の光路差・反射システム**が駆動します。

- **依存ゼロ・単一 HTML・オフライン動作** — [`index.html`](index.html) を開くだけ
- **Android APK / Windows 10・11 EXE / Ubuntu AppImage・deb** —
  [Releases](https://github.com/masaaki-avnturle/Bada/releases) から(下記)

---

## 使い方(3 ステップ)

1. **グラスを接続** — USB-C / HDMI のミラーリング型 AR グラス
   (XREAL / Rokid / VITURE など「外部ディスプレイ」として映るタイプ)を
   タブレット・スマートフォン・PC に接続します。接続すると画面がそのまま
   グラスに表示されます。
2. **投影** — 「⛶ 全画面投影」で HUD だけを表示(スマホ / タブレット)。
   PC では「🗔 別ウィンドウ投影」で HUD ウィンドウをグラス側ディスプレイに
   移動して F11。**黒背景は透過型グラスでは透明**になり、カードだけが
   視界に浮かびます。
3. **コンテンツを流す** — 画像ファイル・入力した文章・クリップボードが
   HUD カードとしてグラスに投影されます。コンシェルジュ「ミーミル」への
   質問(時刻・日付・計算・メモ・投影操作)の答えも HUD に出ます。

### コンシェルジュ「ミーミル」への話しかけ方

| 例 | 動作 |
|:---|:---|
| `いま何時?` / `今日は何日?` | 時刻・日付 |
| `3+4*2` / `計算 (2+3)*4` | 安全な四則演算(eval 不使用) |
| `メモ 牛乳を買う` / `メモ一覧` / `メモ削除` | メモ(localStorage 永続化) |
| `明るくして` / `暗くして` / `文字大きく` / `文字小さく` | HUD 調整 |
| `SBSにして` / `単眼にして` / `全画面` / `クリア` | 投影操作 |
| `光路差は?` / `相対論の補正は?` | 光学エンジンの現在値を報告 |

意図判定はレーベンシュタイン距離のあいまい照合。Web Speech API がある
環境では 🎤 音声入力と読み上げも使えます(無くても全機能動作)。

---

## 特殊相対性理論の光路差・反射システム

HUD の輝度と左右像は、次の物理エンジンが毎フレーム計算します
(実装は `index.html` の純関数、検証は [`tools/engine-test.js`](tools/engine-test.js)):

| 量 | 式 |
|:---|:---|
| ローレンツ因子 | γ = 1/√(1−β²)、β = v/c |
| 相対論的ドップラー | D = 1/(γ(1−β cosθ))、観測波長 λ' = λ/D |
| 相対論的光行差 | cosθ' = (cosθ+β)/(1+β cosθ) |
| スネル屈折 | sinθt = sinθi / n |
| コンバイナ反射の光路差 | **Δ = 2 n d cosθt**(反射合成板の薄膜) |
| 干渉位相 | φ = 2πΔ/λ' + π(外面反射の λ/2 跳び) |
| フリンジ強度 | I = (1+cosφ)/2 → **干渉輝度補正**(I が低いほど HUD を増光) |
| 両眼収束シフト | atan(IPD/2 ÷ 虚像距離) × (画素/rad) → SBS の左右像へ適用 |

頭部速度 v(歩行 ≈1.4 m/s)ではドップラー・光行差の補正は極小(β ≈ 4.7×10⁻⁹)
ですが、エンジンは任意の β で厳密に解きます(テストは 0.5c まで検証)。
「🔬 光学エンジン」パネルで n・膜厚 d・入射角 θ・波長 λ・v を動かすと、
γ / D / θ' / λ' / Δ / 伝播時間差(アト秒)/ φ / I がライブ表示されます。

---

## 📱💻 ダウンロード(APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `mimir-concierge-debug.apk` |
| **Windows 10 / 11** | `Mimir-*-x64.exe`(NSIS インストーラ)/ `Mimir-*-portable.exe` |
| **Ubuntu** | `Mimir-*-x86_64.AppImage` / `Mimir-*-amd64.deb` |

ビルドは [`mimir-app-build.yml`](../.github/workflows/mimir-app-build.yml) が実行します:

- `mimir-v*` タグを push(例: `mimir-v1.0.0`)→ 3 プラットフォームをビルドして
  その Release に自動添付
- Actions の **Run workflow**(`workflow_dispatch`)→ Actions アーティファクトとして取得
  (`release_tag` を入れれば Release へ添付)

ブラウザ版はダウンロード不要 — [`index.html`](index.html) を
「Download raw file」(⬇)で保存してダブルクリックするだけです。

### インストールメモ

- **APK**: 「提供元不明のアプリ」を許可してインストール。グラス接続中は
  画面ミラーリングで HUD がグラスに表示されます。
- **Windows**: NSIS インストーラ(インストール先変更可)またはポータブル EXE。
- **Ubuntu**: `chmod +x Mimir-*.AppImage && ./Mimir-*.AppImage`、
  または `sudo apt install ./Mimir-*_amd64.deb`。

---

## 構成

```
mimir/
├── index.html              ★ アプリ本体(自己完結・依存ゼロ)
├── tools/engine-test.js    エンジン単体テスト (node mimir/tools/engine-test.js)
└── app/
    ├── cordova/config.xml  Android APK 用 Cordova 設定
    └── electron/           Windows / Ubuntu 用 Electron ラッパー
        ├── main.js  preload.js  package.json
```
