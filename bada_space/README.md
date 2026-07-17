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
| **📺 実写プレーヤー（Bada 言語駆動 · 早送り/巻き戻し対応）** | 抽象CGではなく**実写の動画**を再生。**早送り ⏩ / 巻き戻し ⏪**（±10秒）・シークバー・再生速度（0.5〜2×）・前/次。トランスポート制御は **Bada 言語のプログラム（`player.bada`）を内蔵インタプリタが実行**して `<video>` を駆動（`Media::seek fwd` など）。実写VOD（パブリックドメイン／サンプル・シーク可）＋各局ライブ（NHK WORLD / DW / France 24 / Al Jazeera English / NASA TV）＋「URL追加」。🔊音声・⛶全画面 |
| **浮遊グラス・ウィンドウ** | 時計 / 天気 / ミュージック（ライブ波形）/ 写真 / 3D（回転ワイヤーフレーム）/ ブラウザ |
| **視線レティクル** | 画面中央の注視点。ウィンドウを見つめるとハイライト |
| **空間ドラッグ** | ウィンドウのバーを掴んで空間内を自由に移動 |
| **イマーシブ・ダイヤル** | Digital Crown 風スライダーで没入度（背景の暗さ・被写界深度ぼけ）を無段階調整 |
| **環境切替** | オーロラ / 山岳 / ディープスペース の3環境 |
| **ホーム・グリッド** | アプリ一覧から各ウィンドウを開閉 |
| **視差 / ジャイロ** | マウス移動・端末の傾き（スマホ）で空間に奥行きの視差 |

### 🅱 Bada 言語で書いたプレーヤー制御（`www/player.bada`）

早送り/巻き戻しなどのトランスポートは **Bada 言語のプログラム**で記述され、アプリ内蔵の
Bada インタプリタ（`bada_ruby` の `Interpreter` と同じ `set / <- / -< / >- / Omega::push / print`
文法）が実行時に解釈して `<video>` を駆動します。ボタンのタップは1行の Bada を実行します:

```bada
set fwd  = 10          # 早送り（秒）
set back = -10         # 巻き戻し（秒）
cursor <- "global manifold transport"   # 左作用 π(χ,x)
cursor -< 1.0                            # 多様体積分 ∬1/(x·log x)²
Omega::push cursor as transport_node     # Akashic TupleSpace へ
Media::seek fwd        # ⏩ 早送り  /  Media::seek back = ⏪ 巻き戻し
Media::rate rate       # 速度       /  Media::channel next = ⏭
```

アプリ下部の **BADA コンソール**に、実行された Bada 命令（`Ω::push …`, `Media::seek fwd` 等）が表示されます。

---

空間UI（環境・ウィンドウ・3D 等）は**完全オフライン**（Canvas 2D + DOM のみ）で動作します。
**実写プレーヤーの映像視聴のみ**、動画/配信への接続（ネット）が必要です。
実写VOD（パブリックドメイン／サンプル）はシーク可能なので**早送り/巻き戻し**が効きます。ライブ配信はシーク不可です。

> ⚠️ **フジテレビ・NHK（国内）の速報配信そのものは、著作権・配信規約上、本アプリには組み込めません。**
> 代わりに各局が公式に無料公開しているライブ配信を収録し、「URL追加」であなたが正規に利用できる
> 配信（HLS .m3u8 / MP4）を追加できます（フジ/NHK 国内も、正規のソースをお持ちならここから）。

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
