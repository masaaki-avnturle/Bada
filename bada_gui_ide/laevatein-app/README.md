# LÆVATEIN — Λ ドライバ無力化シミュレータ (ネイティブ アプリ)

**Λ ドライバ無力化シミュレータ (LÆVATEIN)** を、**Windows 10/11・Ubuntu・Android** の
ネイティブ アプリとしてパッケージします。

本体 (`www/index.html`) は完全自己完結の HTML で、モデルコア
[`../www/lambda_driver.js`](../www/lambda_driver.js) を inline 済みです。
[`node ../tools/build-lambda-driver.js`](../tools/build-lambda-driver.js) で生成されます
(この `www/index.html` はビルド生成物のため git 管理外)。

## ディレクトリ構成

```
laevatein-app/
  www/index.html   LÆVATEIN 本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb ラッパー
  cordova/         Android APK 設定
```

## 入手 (Actions — タグ不要)

関連ブランチ / `main` への push で
[`laevatein-app-build.yml`](../../.github/workflows/laevatein-app-build.yml) が自動実行されます。
[Actions](https://github.com/masaaki-avnturle/Bada/actions/workflows/laevatein-app-build.yml)
→ 最新の実行 → ページ下部の **Artifacts**:

| Artifact | 中身 |
|:---|:---|
| `laevatein-android-apk` | `laevatein-debug.apk` |
| `laevatein-windows-exe` | `LAEVATEIN-1.0.0-x64-setup.exe` / `LAEVATEIN-1.0.0-x64-portable.exe` |
| `laevatein-ubuntu-appimage-deb` | `LAEVATEIN-1.0.0-x86_64.AppImage` / `LAEVATEIN-1.0.0-amd64.deb` |
| **`laevatein-all-platforms`** | 上記すべて + 単一 HTML + CLI + Bada 実装 |

Actions のアーティファクトは要ログイン・保存期間 90 日です。
`laevatein-app-v*` タグの push (または `workflow_dispatch` の `release_tag` 入力) で
同じ成果物が Release にも添付されます (期限なし)。

インストールしたくない場合は、単一 HTML の
[`../dist/lambda-driver.html`](../dist/lambda-driver.html) をダウンロードして
ブラウザで開くだけでも同じものが動きます。

## ローカルでのビルド / 起動

```sh
# 本体 (www/index.html) を生成
node bada_gui_ide/tools/build-lambda-driver.js

# デスクトップ (Electron) — 起動
cd bada_gui_ide/laevatein-app/electron && npm install && npm start

# Windows EXE / Ubuntu AppImage・deb
npm run dist         # Windows (要 Windows もしくは wine)
npm run dist:linux   # Ubuntu (AppImage + deb)

# Android APK (Cordova)
cordova create cordova-build io.github.masaaki_avnturle.laevatein LAEVATEIN
rm -rf cordova-build/www
cp -r bada_gui_ide/laevatein-app/www cordova-build/www
cp bada_gui_ide/laevatein-app/cordova/config.xml cordova-build/config.xml
cd cordova-build && cordova platform add android@12.0.1 && cordova build android
```

## 使い方

左のパネルで 3 つの層のパラメータを動かすと、熱収支が即時に再計算されます。

- **A. 暴走系** — 初期出力 `P₀`・倍加時間 `τ_d`・総エネルギー `E_max`・観測時間
- **B. 抑制層** — 部分積分の深さ `x`・不完全ガンマの `s`・Λ 場の交差数 `c`・
  Kauffman ループ変数 `A`・制御系の演算速度と温度
- **C. 青色 LED 冷却** — 波長 `λ`・順方向バイアス `V`・外部量子効率 `η`・
  素子あたり電流・素子数

図は 4 枚:

1. **出力と冷却能力** — `P(t)`・排熱要求・LED 冷却能力・実証済み素子 1 台を対数目盛で
   並べ、冷却が破綻する時刻を示します
2. **Γ 大域的部分積分多様体** — 境界項 `|a_k|` が `k ≈ s+x` で最小になってから発散する
   様子と、最適打ち切り `k*`・最小項 (= 漏れの桁)
3. **エネルギー収支** — 解放・吸収・漏れ
4. **冷却スケールの比較** — 排熱要求と各冷却源の桁差

右のパネルに判定 (律速が `cooling-power` / `control-compute` /
`el-cooling-condition` のどれか) と各層の数値、下に実行手順の成否が出ます。

### 出力の保存

- **Windows / Ubuntu アプリ**: `CSV` / `JSON` ボタンで「名前を付けて保存」ダイアログ。
- **Android アプリ**: WebView はファイル保存を扱えないため、新しいウィンドウに
  内容を表示します。
- **ブラウザ**: 通常のダウンロード。

## 創作についての注記

Λ ドライバ・レーバテイン・アルは『フルメタル・パニック!』(賀東招二) の架空の装置と
キャラクタです。作中の封じ込めの筋立てを手順の骨格として借りていますが、装置そのものは
完全な創作であり、**この構成は現実の装置にはなりません**。

抑制対象は「指数関数的に暴走する系」という抽象モデル (初期出力・倍加時間・総エネルギー
のみ) で、特定の装置の設計量は一切含みません。実在の物理は冷却層 (電界発光冷却) と
Landauer 限界・Kauffman ブラケット・不完全ガンマの漸近解析だけで、このアプリの主眼は
**要求排熱と実在の熱力学の間に何桁の隔たりがあるかを数えること**にあります。
