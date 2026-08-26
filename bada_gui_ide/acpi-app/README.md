# ACPI — 原子の臨界期の強度シミュレータ (ネイティブ アプリ)

**原子の臨界期の強度シミュレータ (ACPI — Atomic Critical-Period Intensity)** を、
**Windows 10/11・Ubuntu・Android** のネイティブ アプリとしてパッケージします。

ACPI 本体 (`www/index.html`) は完全自己完結の HTML で、モデルコア
[`../www/atom_critical.js`](../www/atom_critical.js) を inline 済みです。
[`node ../tools/build-atom-critical.js`](../tools/build-atom-critical.js) で生成されます
(この `www/index.html` はビルド生成物のため git 管理外)。

## ディレクトリ構成

```
acpi-app/
  www/index.html   ACPI 本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb ラッパー
  cordova/         Android APK 設定
```

## 入手 (Releases)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル | 備考 |
|:---|:---|:---|
| **Windows 10 / 11** | `ACPI-1.0.0-x64.exe` | NSIS インストーラ / ポータブル (どちらも同名パターン) |
| **Ubuntu** | `ACPI-1.0.0-x86_64.AppImage` | `chmod +x` して実行 |
| **Ubuntu** | `ACPI-1.0.0-amd64.deb` | `sudo dpkg -i ACPI-1.0.0-amd64.deb` |
| **Android** | `acpi-debug.apk` | 「提供元不明のアプリ」を許可してインストール |

ビルドは GitHub Actions [`acpi-app-build.yml`](../../.github/workflows/acpi-app-build.yml)
が行います。`acpi-app-v*` タグの push で Release に自動添付、`workflow_dispatch`
でも Actions アーティファクトとして取得できます。

インストールしたくない場合は、単一 HTML の
[`../dist/atom-critical.html`](../dist/atom-critical.html) をダウンロードして
ブラウザで開くだけでも同じものが動きます。

## ローカルでのビルド / 起動

```sh
# ACPI 本体 (www/index.html) を生成
node bada_gui_ide/tools/build-atom-critical.js

# デスクトップ (Electron) — 起動
cd bada_gui_ide/acpi-app/electron && npm install && npm start

# Windows EXE / Ubuntu AppImage・deb
npm run dist         # Windows (要 Windows もしくは wine)
npm run dist:linux   # Ubuntu (AppImage + deb)

# Android APK (Cordova)
cordova create cordova-build io.github.masaaki_avnturle.acpi ACPI
rm -rf cordova-build/www
cp -r bada_gui_ide/acpi-app/www cordova-build/www
cp bada_gui_ide/acpi-app/cordova/config.xml cordova-build/config.xml
cd cordova-build && cordova platform add android@12.0.1 && cordova build android
```

## 使い方

アプリを起動すると、既定で **Ar (アルゴン)・800 nm・6×10¹⁴ W/cm²・FWHM 8 fs** の
条件が計算されます。左のパネルで元素・電離段数・波長・ピーク強度・パルス幅・
CEP・パルス形状・Ω 層のパラメータを動かすと、臨界期が即時に再計算されます。

- **① 場の強度と臨界期** — I(t)・E(t)・臨界強度 I_cr のしきい値線・臨界窓の網掛け
- **② 束縛占有率と ADK 電離率** — P_bound(t) と log W_ADK(t)
- **③ Ω 作用素層** — 超臨界度 x = |E|/F_cr・均衡余裕 2e^{−x log x}・ζ_n・Euler 残差
- **④ 強度スイープ** — I₀ を対数掃引したときの臨界期の長さ・電離確率・E(σ)
- **⑤ 臨界サブ窓** — 半サイクルごとの窓の幅 (アト秒)・ピーク強度・平均強度

右のパネルに臨界期の全長・サブ窓の数・デューティ比・臨界期のピーク/平均強度・
フルーエンス・γ_Keldysh・U_p・Kauffman ⟨D⟩・H(σ)・**臨界強度指数 E(σ)** が出ます。

### 出力の保存

- **Windows / Ubuntu アプリ**: `CSV` / `JSON` / `PNG` ボタンで「名前を付けて保存」
  ダイアログが開きます。
- **Android アプリ**: WebView はファイルのダウンロードを扱えないため、
  同じボタンで内容を表示するパネルが開きます。テキストは「クリップボードに
  コピー」、図は長押しで保存できます。
- **ブラウザ (`dist/atom-critical.html`)**: 通常のダウンロードになります。

Android 版は起動を軽くするため、④ の強度スイープ (46 回のシミュレーション) を
自動実行せず「強度スイープ」ボタン待ちにしています。

## モデル

臨界期 = 強レーザー場のなかで原子のクーロン障壁が完全に抑制され
(over-the-barrier)、束縛状態がもはや保護されない時間窓。原子単位系で

```
F_cr = I_p² / (4 Z_c)   [a.u.]        I_cr = F_cr² · I_a
I_a  = ½ ε₀ c F_au²  = 3.5094×10¹⁶ W/cm²
```

物理層 (障壁抑制場・ADK トンネル電離・Keldysh γ・U_p) に、山口フレームワークの
Ω 作用素層 (ζ(s)=β(p,q)/log x・ζ_n=(x log x)ⁿ・Γ-deprivation e^{−x log x}・
Dalanversian Λ・Euler 極均衡 x^n+y^n−nxyz=0・Kauffman ⟨D⟩(A)・
E(σ)=K(σ)×H(σ)/4(π_n,e_n)) を重ねています。
詳細は [`../README.md`](../README.md) の「ACPI」節を参照。
