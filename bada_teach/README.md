# 🥋 BadaGPT 道場 (BadaTeach)

**ChatGPT が「応答してアプリケーションを作る」ときに使っている技を、量子プログラミング言語 Bada を題材にユーザーへ伝授する教習アプリ。**

依存ゼロ・単一 HTML・オフライン動作。[`index.html`](index.html) をダウンロードしてダブルクリックするだけで動きます (インストール不要)。Android APK / Windows 10・11 EXE / Ubuntu AppImage・deb は [Releases](https://github.com/masaaki-avnturle/Bada/releases) から。

## 伝授する「4 つの技」

ChatGPT のようなアシスタントは、会話のたびに次のループを回してアプリを組み立てています。道場ではこれを **BadaGPT 先生が実演しながら** 教えます:

| 技 | 内容 |
|:--|:--|
| **技① 要件抽出** | あいまいな日本語の依頼を、箇条書きの要件に直す |
| **技② 仕様化** | 要件を「入力・処理・出力・状態」の 4 点セットに落とす |
| **技③ コード生成** | 仕様を言語の決まった型 (テンプレート) に流し込む |
| **技④ 実行と反復** | 動かして出力を読み、差分だけを応答で直す |

## 3 つの画面

- **📚 カリキュラム** — 8 章構成 (応答型開発とは → 技①〜④ → Bada 入門 → 量子コア → 卒業試験)。各章に実験エディタと **自動判定つき演習**。進捗は localStorage に保存。
- **🥋 道場** — **BadaGPT 先生チャット**。「サイコロアプリを作って」と日本語で頼むと、技①→②→③→④ の途中経過をすべて見せながら、**実際に動く Bada コード**を生成。生成コードはその場で ▶ 実行でき、「12面にして」のような応答で差分修正 (技④) も実演。
- **📖 リファレンス** — 道場サブセットの Bada 言語チートシート。

## 内蔵ミニ Bada インタープリタ

- 文: `x := 式` / `print` / `値 >> tuplespace` (append-only 台帳) / `repeat` / `for in` / `if else` / `fun |a,b| { return }`
- 確率・情報: `unknown_prior` (最大エントロピー事前分布) / `softmax` / `update` (ベイズ更新) / `entropy` / `zeros_of`
- 量子コア: `qubit(n)` / `H` / `X` / `CNOT` / `Measure` (|ψ|²) / `sample` (量子乱数)
- 日本語・行番号つきエラー、ステップ上限つき (無限ループ防止)

## ビルド

[`../.github/workflows/badateach-app-build.yml`](../.github/workflows/badateach-app-build.yml) が実行します:

| プラットフォーム | 生成物 | 方法 |
|:--|:--|:--|
| Android | `bada-teach-debug.apk` | Cordova 12 + cordova-android 12 |
| Windows 10/11 | `BadaTeach-*-x64.exe` (NSIS / ポータブル) | Electron + electron-builder |
| Ubuntu | `BadaTeach-*-x86_64.AppImage` / `BadaTeach-*-amd64.deb` | Electron + electron-builder |

`badateach-v*` タグを push (または workflow_dispatch で `release_tag` を指定) すると GitHub Release に添付されます。

## テスト

```sh
node bada_teach/tools/engine-test.js
```

インタープリタ (代入・リスト・for/repeat/fun・台帳)、量子コア (H|0>、ベル状態 [0.5, 0, 0, 0.5]、confident zero 保存)、エントロピー単調減少、BadaGPT 先生の全テンプレート生成コードの実行可否、技④ の差分修正、全章演習の合否判定を検証します。
