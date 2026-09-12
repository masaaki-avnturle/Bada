# 反重力発生器 航空機 YMG-AG01 — ネイティブ アプリ

反重力発生器としての航空機（3Dインタラクティブ機体＋設計図）を、
**Windows 10/11・Ubuntu・Android** のネイティブ アプリとしてパッケージします。

本体（`www/index.html`）は完全自己完結・**オフライン動作**の WebGL ページで、
BadaUFO-OS の反重力方程式コアと Three.js（同梱 `three.min.js`, r128）を含みます。
`node ../tools/build-aircraft-www.js` が Artifact 版
[`../app/antigravity_aircraft_3d.html`](../app/antigravity_aircraft_3d.html)
から生成します（この `www/index.html` はビルド生成物のため git 管理外。
`www/three.min.js` は vendored で git 管理）。

## 駆動する反重力方程式（BadaUFO-OS）

| 部材 | 方程式 |
|---|---|
| 反重力リング・ビーム | `E_ag = U_grav·cosh(x log x)`（重力方程式の補空間＝反重力場） |
| D-brane 支持脚 | `E⊥ = mc² − ½mv²`（特殊相対論の補空間・抽出源） |
| 真空炉心 | `E_vac = ρ·x^x`（無尽蔵の真空エネルギー体） |
| 揚力比 | `L = cosh(x log x)`（x = 1 + r₀/r） |

## ディレクトリ構成

```
aircraft-app/
  www/three.min.js   Three.js r128 (vendored, オフライン用)
  www/index.html     機体アプリ本体 (自己完結・ビルド時に生成)
  electron/          Windows EXE / Ubuntu AppImage・deb ラッパー
  cordova/           Android APK 設定
```

## 入手（Releases）

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `AntigravityAircraft-1.0.0-x64.exe`（NSIS インストーラ / ポータブル） |
| Ubuntu | `AntigravityAircraft-1.0.0-x64.AppImage` / `AntigravityAircraft-1.0.0-x64.deb` |
| Android | `antigravity-aircraft-debug.apk` |

ビルドは GitHub Actions
[`antigravity-aircraft-build.yml`](../../.github/workflows/antigravity-aircraft-build.yml)
が行います。`antigravity-v*` タグの push、または Actions 画面からの手動実行
（`release_tag` を指定すると Release に添付）で起動します。

## ローカルで動かす / ビルドする

```bash
cd bada_ufo_os
node tools/build-aircraft-www.js            # www/index.html を生成

# デスクトップ (Electron)
cd aircraft-app/electron
npm install
npm start                                   # 開発起動
npm run dist                                # Windows EXE
npm run dist:linux                          # Ubuntu AppImage + deb
```

Android APK はワークフロー（Cordova 12 + Gradle 7.6.4 + Android SDK 33）で
ビルドします。

## 注意

本アプリは BadaUFO-OS 反重力理論に基づく<b>概念設計・3Dシミュレーション</b>であり、
物理的に機能する装置ではありません。
