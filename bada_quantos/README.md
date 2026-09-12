# ⚛ Bada QuantOS — 擬似量子オペレーティングシステム

**今までの集大成である擬似量子コンピュータ(量子 Bada 実行系)を、そのままオペレーティングシステムにしたアプリケーション。カーネルは生成 AI。**

タブレット・スマートフォンの機能 — **電話回線 / SMS / メール / カメラ / ギャラリー / 時計・アラーム / 電卓 / メモ / ファイル / 連絡先** — を、**トポロジーの写像機構**によって擬似量子コンピュータの上へ移植しています。依存ゼロ・単一 HTML・オフライン動作。

## 🪢 トポロジーの写像機構

各 OS 機能には**結び目(Reidemeister I カール列 = ±1 の交点符号列)**が割り当てられています。

1. **不変量による分類** — カール列の Kauffman ブラケットは ⟨K⟩ = (−A³)^w(w = ライズ = 符号和)。組 (交点数 c, ライズ w) は全機能で相異なるため、機能はトポロジー不変量で一意に分類されます。
2. **基底への単射写像 φ** — 各機能を 4 量子ビットレジスタの基底状態 |b₀b₁b₂b₃⟩ へ単射に写像します(2⁴ = 16 基底 ≥ 14 機能)。写像先は各アプリのアイコン下と画面上部の Ψ 表示で常に確認できます。
3. **連続変形による遷移** — 機能間の移動はハイパーキューブの辺(X ゲート 1 発 = 1 ビット反転)に沿った連続変形として表され、「写像室」アプリでゲート列と擬似量子カーネルによる検算を観測できます。不変量 (c, w) は変形の間も保存されます。

## 🧠 生成AIカーネル

画面下のコマンドバーが OS シェルです。すべての応答で 6 段パイプラインを開示します:

**① トークン化 → ② 意図解析 → ③ トポロジー写像 → ④ 計画 → ⑤ 生成 → ⑥ 検証**

例:
- 「**090-1234-5678 に電話**」 → 電話 ↦ |0001⟩ へ写像し、`tel:` インテントを端末回線へ発行
- 「**写真を撮って**」 → カメラ ↦ |0101⟩ へ写像して起動
- 「**1+2*3**」 → 電卓パーサで検算つき評価
- 「**qubit q0 q1 ↵ H q0 ↵ CNOT q0 q1 ↵ state**」 → 擬似量子カーネルで直接実行

## 📞 電話回線について

電話・SMS・メールの**発信は端末 OS へ `tel:` / `sms:` / `mailto:` インテントとして委譲**します。Android APK では標準の電話アプリ・SMS アプリが起動して実際に発信できます(APK は Cordova の `allow-intent` で許可済み)。デスクトップ(Windows / Ubuntu)には電話回線がないため、発行予定のインテント内容を表示します(mailto: は既定メールアプリへ)。

## ⚛ 擬似量子カーネル(量子 Bada)

`qubit / H / X / Z / CNOT / measure / state / let / print` を実装した実振幅の状態ベクトル・シミュレータ(8 qubit まで)。「量子ラボ」アプリからベル状態・GHZ などを実行できます。

## 🚀 使い方

1. [`index.html`](index.html) を「Download raw file」で保存 → ダブルクリック(インストール不要)
2. または [Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-quantos-debug.apk` |
| **Windows 10 / 11** | `BadaQuantOS-*-x64.exe`(NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaQuantOS-*-x86_64.AppImage` / `BadaQuantOS-*-amd64.deb` |

ビルドは [`quantos-app-build.yml`](../.github/workflows/quantos-app-build.yml) が実行します(`quantos-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。

## 🧪 テスト

```
node bada_quantos/tools/engine-test.js
```

擬似量子カーネル / トポロジー不変量・写像・連続変形 / 端末プロファイル / 電卓 / 意図解析 / 生成AIカーネル / 実行系 の 40 項目を検証します。

## 📁 構成

```
bada_quantos/
├── index.html            # アプリ本体 (自己完結・オフライン)
├── tools/engine-test.js  # Node 単体テスト
└── app/
    ├── cordova/config.xml    # Android APK (tel:/sms:/mailto: allow-intent)
    └── electron/             # Windows EXE / Ubuntu AppImage・deb
```
