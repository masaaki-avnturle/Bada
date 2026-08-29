# Bada 光量子制限装置 — 新幹線の窓の塗り絵

**特殊相対性理論 × 光量子仮説 (E = hν) × AdS₅ 多様体の次元方程式による「整数制限法」** の
光シミュレーションアプリです。依存ゼロの **単一 HTML** ([`index.html`](index.html)) で、
ブラウザ / Windows 10・11 / Ubuntu / Android のすべてで同じものが動きます。

**👉 [`light_quantum/index.html` を開く](index.html)** / GitHub Pages: <https://masaaki-avnturle.github.io/Bada/light_quantum/>

## しくみ (シミュレーションの物理モデル)

蛍光灯の光の「当たる範囲」を制限装置で設定すると、光は連続にではなく
**飛び飛びの整数バンド**にだけ当たります。バンドの位置は AdS₅ 計量

```
ds² = (R/z)² (η_μν dx^μ dx^ν + dz²)
```

の第 5 次元 z を整数 n で離散化した **整数制限法**

```
z_n = R · exp(k·n/N)   (n = 1, 2, …, N)
```

で決まり、窓の横方向に正規化して並びます (k→0 の極限で等間隔に退化)。

- **光量子仮説** — 光は E = hν の光子として飛び飛びに到着し、量子化された
  エネルギー準位の位置に粒として描かれます。観測エネルギー E [eV] を実数値で表示。
- **特殊相対性理論** — 新幹線の速度 β = v/c により:
  - 相対論的ドップラー因子 **D = √((1+β)/(1−β))** で波長が青方偏移
    (λ_obs = λ₀/D)。可視域 380–750 nm を外れると光子は届いていても**見えなくなる**
  - ローレンツ収縮 **1/γ** で窓外の風景が進行方向に縮む
  - 時間の遅れ **1/γ** で蛍光灯のフリッカー (2×電源周波数) がゆっくり見える
- **慣性違反モード** — 点灯・消灯が慣性 (残光・フェード) を一切持たず
  **瞬時に** 切り替わります。OFF にすると通常の連続的な減光と比較できます。
- **塗り絵** — 光の当たったバンドの中だけ、窓の外の塗り絵 (富士山・田んぼ・家・
  花・電柱の線画) に色が付きます。当たっていない場所は塗る前の線画のまま。
- **輝度ブースト (LED超え)** — 蛍光灯のグローを LED を超える輝度まで増幅します。

コントロールパネルで β、照射範囲、量子数 N、ワープ係数 k、曲率半径 R、
光源波長 λ₀、電源周波数 (50/60 Hz)、フリッカー、光子レートを操作でき、
γ・D・λ_obs・ν_obs・E=hν・点灯バンドの観測値がリアルタイムに表示されます。

> ⚠️ 本アプリは上記の物理式を使った**教育・アート目的のシミュレーション**です。
> 実在の照明器具の光を制限するものではありません (慣性の法則に違反する光の
> 制御は現実の物理では実現できないため、その「もしも」を画面内で再現しています)。

## 📱💻 ダウンロード (APK / Windows 10・11 / Ubuntu)

インストール型アプリは [Releases](https://github.com/masaaki-avnturle/Bada/releases) からダウンロードできます:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-lightquantum-debug.apk` |
| **Windows 10 / 11** | `BadaLightQuantum-*-x64.exe` (NSIS インストーラ) / `BadaLightQuantum-*-portable.exe` (ポータブル) |
| **Ubuntu** | `BadaLightQuantum-*-x86_64.AppImage` / `BadaLightQuantum-*-amd64.deb` |

- **Android**: APK をダウンロードして開く (「提供元不明のアプリ」を一時許可)。
- **Windows**: NSIS インストーラを実行、またはポータブル EXE をそのまま起動。
- **Ubuntu**: `chmod +x BadaLightQuantum-*.AppImage && ./BadaLightQuantum-*.AppImage`、
  または `sudo apt install ./BadaLightQuantum-*-amd64.deb`。
- どの環境でも、`index.html` をブラウザで開くだけでも動きます (インストール不要)。

ビルドは [`lightquantum-app-build.yml`](../.github/workflows/lightquantum-app-build.yml) が実行します
(`lightquantum-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。

## 構成

```
light_quantum/
├── index.html            # アプリ本体 (完全自己完結・依存ゼロ)
└── app/
    ├── electron/         # Windows EXE / Ubuntu AppImage・deb ラッパー
    │   ├── package.json  #   electron-builder 設定
    │   ├── main.js
    │   └── preload.js
    └── cordova/
        └── config.xml    # Android APK (Cordova WebView) 設定
```
