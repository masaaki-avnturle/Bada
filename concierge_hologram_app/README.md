# まちしおり — ホログラム・コンシェルジュ
### Machi-Shiori — a see-through holographic AR concierge for smartphones (Bada / Omega dialect)

スマートフォンの**半透明（シースルー）ホログラフィーディスプレイ**に、コンシェルジュ「**しおり**」が常駐します。
**風景にかざす**と、画面越しに見えている**山・川・お店・駅・名所・植物・看板**などを認識し、
その対象の実位置に貼り付く**文字ラベル**で情報を教えてくれる Bada 言語製のアプリです。

前作 `pokemon_hologram_game/` のホログラム／パススルー／傾きセンサの設計を引き継ぎ、
「遊ぶ」ためではなく「**街を歩きながら案内を受ける**」ために作り直したものです。

---

## 🧭 使い方

1. アプリを起動すると、ディスプレイは**素通し**（風景がそのまま見える）状態になります。
2. スマホを**風景にかざす**と（`isHeldUp` が検出）、コンシェルジュが働き始めます。
3. 見えている対象に、**発光する文字ラベル**が重なって表示されます。
   ラベルには「対象名・一言解説・方位と距離（例: 北東 300m）」が入ります。
4. 端末を左右に振っても、ラベルは**対象の実位置に貼り付いたまま**追従します（world-locked）。
5. 対象を**タップ**すると、詳細カードが開きます。

---

## 📁 モジュール構成

| ファイル | 役割 | 対応する要求 |
|:--|:--|:--|
| `main.om` | アプリ本体・イベントループ（`App`） | 全体統合 |
| `display/translucent_display.om` | **半透明シースルー表示**・発光文字の加算合成（`TranslucentDisplay`） | 半透明ディスプレイ上に文字 |
| `sensor/pose_anchor.om` | 傾き＋方位＋GPS・**ワールドロック投影**・かざす検出（`PoseSensor`, `worldToScreen`） | 風景にかざす／文字を対象に固定 |
| `vision/scene_reader.om` | 透過像の**対象認識**＋POI突き合わせ（`SceneReader`） | 風景にある情報を読む |
| `concierge/knowledge_base.om` | **POIインデックス＋事実データ**（`POIIndex`, `FactBook`, アカシック） | 情報の出どころ |
| `concierge/concierge.om` | **案内文の生成**＋π-softmaxで優先度選別（`Concierge`） | コンシェルジュが文字で教える |
| `overlay/annotation_overlay.om` | ラベルの**ワールドロック配置・描画**（`AnnotationOverlay`） | 文字ラベルを対象に重ねる |

---

## 🖥 半透明ディスプレイの仕組み

透過型パネル（黒画素＝透明／発光画素＝表示）を前提に、現実の風景はパネルを**素通し**で見え、
その上へ発光文字だけを**加算合成**します。

```
out(x) = scene(x) + α · textLight(x)      // 発光型・加算
τ      = 1 − α_panel                      // 全体の透け具合（既定 τ = 1 = 素通し）
```

文字の背後だけを 42% ほど局所的に遮光し（`LabelStyle.panel`）、逆光の風景でも読めるようにしています。

---

## 📍 文字を「対象に貼り付ける」ワールドロック

ラベルが対象からずれないよう、毎フレーム対象の地理位置を端末姿勢で再投影します（`worldToScreen`）。

- 端末の**方位** `yaw`（コンパス）と対象の**絶対方位** `geoBearing` の差 `rel` を画面横位置へ、
- 対象の見かけ**仰角**と端末 `pitch` の差を画面縦位置へマッピング。
- 画角 `hfov/vfov` の外に出た対象は描画しません。

これにより、端末を振ってもラベルは対象の実位置に留まります。方位・距離は
`bearingText`（北/北東/…）と `distanceText`（m / km）で日本語表示します。

---

## 🗣 コンシェルジュの案内生成

対象ごとに知識ベース（`FactBook`）を引き、`要約 + 事実2件 + 方位/距離` の案内カードを組み立てます。
画面を埋めすぎないよう、**π-softmax**（`omega_math.c` 由来）で表示優先度を正規化し、上位 `MAX_CARDS` 件のみ表示します。

$$
p_i = \frac{e^{\,r_i\,\hbar_\text{eff}\,\pi}}{\sum_j e^{\,r_j\,\hbar_\text{eff}\,\pi}},\qquad
r_i = \text{conf}_i \times w(\text{kind}_i)
$$

名所・駅・飲食店などは案内価値の重み `w` を高くしてあります。

---

## ▶ 実行イメージ

Bada（Omega）ランタイム上で：

```
bada run main.om        # もしくは omega main.om
```

> `Device::Panel` / `Device::Camera` / `Device::IMU` / `Device::Compass` / `Device::GPS` /
> `Device::Detector` / `Device::Font` は BadaOS 側のデバイス抽象（ドライバ）として参照します。
> POI・事実データはサンプルの街データを同梱しています（実運用では地図API等に差し替え）。

---

## 📦 配布パッケージ — Android APK / Windows 10・11 / Ubuntu

Bada版モジュール（`*.om`）のロジックをそのまま移植した**実際に動くアプリ**を同梱し、
3プラットフォーム向けにパッケージ化できます。中身は共通の `www/index.html`（1ファイル完結）を、
Electron（Windows・Ubuntu）と Cordova（Android）でラップする、本リポジトリ標準の構成です。

```
concierge_hologram_app/
├── www/index.html          … 実動作アプリ（カメラ透過＋方位/傾き/GPS＋案内ラベル）
├── electron/               … Windows 10/11 EXE ＆ Ubuntu AppImage/deb
│   ├── main.js             … Electron ラッパー（カメラ/位置の許可を付与）
│   └── package.json        … electron-builder 設定（win: nsis+portable / linux: AppImage+deb）
└── cordova/config.xml      … Android APK（カメラ/位置/センサ権限つき）
```

### ビルド方法（GitHub Actions）

ワークフロー **`.github/workflows/concierge-app-build.yml`** が 3 つを同時にビルドします。

| ジョブ | 生成物 | ツール |
|:--|:--|:--|
| `windows-exe` | `Machi-Shiori-1.0.0-x64.exe`（インストーラ ＋ portable） | Electron / electron-builder |
| `ubuntu-app`  | `Machi-Shiori-1.0.0-x64.AppImage`, `*.deb` | Electron / electron-builder |
| `android-apk` | `machi-shiori-debug.apk` | Cordova 12 |

- **手動実行**: Actions → *まちしおり build* → **Run workflow**。生成物は Actions のアーティファクトに出ます。
- **リリース添付**: `shiori-v*` タグ（例 `shiori-v1.0.0`）を push すると、EXE / AppImage / deb / APK が
  GitHub Release に自動添付されます。

  ```bash
  git tag shiori-v1.0.0 && git push origin shiori-v1.0.0
  ```

### ローカルでの確認

```bash
# デスクトップ（Windows/Ubuntu）で試す
cd concierge_hologram_app/electron
npm install
npm start                 # Electron で起動（Webカメラがあれば風景として使用）
npm run dist              # Windows EXE
npm run dist:linux        # Ubuntu AppImage + deb
```

> **センサの扱い** — スマホでは背面カメラ・コンパス・傾き・GPS を使い、ラベルは実位置へ
> ワールドロックされます。デスクトップなどセンサが無い環境では、自動で**方位ダイヤル**を表示し、
> デモ位置で同等に動作します（カメラが使えなければ空景グラデーションにフォールバック）。
> iOS/Android では初回に カメラ・位置・モーション の許可を求めます。

---

*© 2026 — Bada 言語（Omega方言）による半透明ホログラム・コンシェルジュ*
