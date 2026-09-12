# ⬒ Bada Illustrator — 量子建築設計スタジオ

**Illustrator 流のベクター作図で建築図面を描き、量子プログラミング言語 Bada で図面を操作・拡張できる建築設計アプリ。**
依存ゼロ・単一 HTML・オフライン動作。Android APK / Windows 10・11 EXE / Ubuntu AppImage・deb として配布します。

## 何ができるか

### 1. ベクター建築 CAD (Illustrator 流の直接操作)

| ツール | キー | 動作 |
|:--|:--:|:--|
| ⬚ 選択 | V | クリックで選択、ドラッグで移動、Delete で削除 |
| ✋ パン | H | 画面移動 (中ボタンドラッグ / Space でも可) |
| ▬ 壁 | W | ドラッグで厚みのある壁 (既定 200mm、変更可) |
| ╱ 線 | L | 下書き線 |
| ▭ 部屋 | R | ドラッグで部屋。名前をつけると面積 (m²) を自動表示、延床面積に算入 |
| ◯ 柱 | C | ドラッグで半径指定 |
| 🚪 ドア | D | 吊元からドラッグ = 幅と向き。90° の開き弧を描画 |
| ▤ 窓 | N | 壁の上にドラッグ |
| ↔ 寸法 | M | 2 点間の寸法線 (mm 自動記入) |
| A 文字 | T | クリックして入力 |
| ⌫ 消去 | X | クリックで削除 |

- 座標・寸法はすべて **mm**。グリッド 100/250/500/**910 (尺モジュール)**/1000 mm + スナップ
- **レイヤー**: 壁・構造 / 開口部 / 部屋 / 寸法・注釈 / 下書き (表示切替 + アクティブ切替)
- **undo/redo** (Ctrl+Z / Ctrl+Y)、ホイールズーム、ピンチズーム (タッチ)、⛶ 全体表示
- プロパティパネルで数値編集 (位置・寸法・壁厚・部屋名・色)
- 💾 保存 / 📂 開く (`.badaarch.json`)、🖼 **SVG 出力** (白図面)、📷 **PNG 出力**、自動保存 (localStorage)

### 2. 量子プログラミング言語 Bada (右パネル ⚛ コンソール)

リポジトリの Bada 文法 (`bada_gui_ide/examples/`) と同系のインタプリタを搭載:

```bada
# ベル状態
reg := qubit(2)
reg := H(reg, 0)
reg := CNOT(reg, 0, 1)
print("ベル状態:", Measure(reg))     # → [0.5, 0, 0, 0.5]
Measure(reg) >> tuplespace           # 追記専用台帳へコミット
```

- `:=` 代入 / `if・else` / `while` / `for x in` / `fun name |a, b| { return ... }` / リスト / `#` コメント
- **量子コア**: `qubit(n)` 状態ベクトル、`H` `X` `Z` `RY` `CNOT` ゲート、`Measure` (Born 則 |ψ|²)、`Sample` (基底へ収束)
- **情報エンジン**: `softmax` / `entropy` (bit) / `unknown_prior` (Jaynes 最大エントロピー) / `update` (ゼロ保存) / `zeros_of`
- **`>> tuplespace`** 追記専用台帳、`@reviser : extension bada { fun 名 |引数| """本体""" }` 拡張トランザクション
  (c / python / java 拡張は台帳に記録され、ネイティブ環境専用である旨を案内)
- `help()` で全 API を表示。無限ループはステップ上限で安全に停止

### 3. Bada から図面を操作する建築 API

```bada
clear()
wall(0, 0, 9100, 0, 200)             # 壁 (mm, 厚 200)
room(0, 0, 9100, 7280, "LDK")        # 部屋 → 面積自動計算
door(4550, 0, 800, 0)                # ドア (吊元, 幅, 向き°)
window(1000, 7280, 3000, 7280)       # 窓
dim(0, -600, 9100, -600)             # 寸法線
column(0, 0, 150)  ·  stairs(x,y,w,l,n)  ·  label(x,y,"文字")
print("延床:", total_area(), "m2")   # count() / areas() / set_layer() も
```

### 4. 拡張機能 (🧩 タブ)

Bada スクリプトそのものが拡張機能です。**組み込み 6 本**:

1. **量子間取りジェネレータ** — 3 qubit の重ね合わせ + CNOT を測定し、その結果で間取り (幅・奥行・間仕切り方向) を決定
2. **外周壁ウィザード** — W×D 指定で外周壁 + 柱 + 寸法 + 部屋を一括生成
3. **通り芯グリッド** — 910mm 尺モジュールの通り芯 X0…/Y0… を符号つきで生成
4. **面積表** — 図面上の部屋を集計して面積表を図面に書き込み
5. **階段ジェネレータ** — 幅・長さ・段数から階段を生成 (蹴上げの目安つき)
6. **ベル状態デモ** — 量子コアと台帳のチュートリアル

「＋新規拡張」で自分の Bada スクリプトを名前つきで保存 (localStorage)、📤/📥 で JSON として共有できます。

## ダウンロード

**ブラウザ版**: [`index.html`](index.html) を開いて「Download raw file」(⬇) → ダブルクリックで起動。インストール不要。

**ネイティブ アプリ** — [Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-illustrator-debug.apk` |
| **Windows 10 / 11** | `BadaIllustrator-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaIllustrator-*-x86_64.AppImage` / `BadaIllustrator-*-amd64.deb` |

Ubuntu: `chmod +x BadaIllustrator-*.AppImage && ./BadaIllustrator-*.AppImage`、または `sudo apt install ./BadaIllustrator-*-amd64.deb`。
Android: APK を開いて「提供元不明のアプリ」を許可してインストール (デバッグ署名)。

ビルドは [`badaillustrator-app-build.yml`](../.github/workflows/badaillustrator-app-build.yml) が実行します:
`badaillustrator-v*` タグを push すると Release へ自動添付、`workflow_dispatch` (release_tag 空欄) なら Actions アーティファクトのみ。

## テスト

```
node bada_illustrator/tools/engine-test.js
```

幾何 (スナップ/壁ポリゴン/靴ひも面積/延床/ヒットテスト)、情報エンジン、量子コア (ベル状態・Born 則・ユニタリ性・決定論サンプル)、Bada 言語 (字句/構文/評価/再帰/台帳/エラー処理/ステップ上限)、@reviser 拡張、建築 API、SVG/JSON 入出力、組み込み拡張 6 本の実行、の 62 項目。

## ファイル構成

```
bada_illustrator/
├── index.html              アプリ本体 (自己完結・依存ゼロ)
├── README.md               このファイル
├── tools/engine-test.js    エンジン単体テスト (Node)
└── app/
    ├── cordova/config.xml  Android APK 用 Cordova 設定
    └── electron/           Windows / Ubuntu 用 Electron ラッパー
        ├── main.js  ·  preload.js  ·  package.json
```
