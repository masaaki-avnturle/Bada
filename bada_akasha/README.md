# 🔮 Bada Akasha — BadaGPT × 方程式 × 直感ポート (Bada 量子エンジン)

**提出された論文 16 本を端末内で検索して出典つきで答える BadaGPT、数値で確かめられる関係だけを出す方程式探索、
直感がどの経路 (ポート) を通って届いているかを実際に測るラボ。中核は Bada 言語で書いた量子エンジンです。**
単一 HTML・通信なし。Android APK / Windows 10・11 EXE / Linux AppImage・deb を GitHub Actions がビルドします。

## 正直な注記 (最初に)

- このアプリは**アカシックレコードに接続しません**。そのような接続を実現する方法は、このアプリにも、ChatGPT を含むどの生成 AI にもありません。
- **未来の知識や、論文にない事実は出しません。** 論文に答えがない質問には「論文集には見つかりません」と答えます
  (論文 *PrecogBada* の規約 P2「幻の未来を作らない」・P3「正直な無知」と同じ)。
- その代わりに、**確かめられる形**にしました: 方程式は数値で成り立つものだけを出して Bada で再検証し、
  「未来の情報が届くか」は予感テストで偶然と比べて測ります。
- 医療機器ではありません。

## できること

| タブ | 内容 |
|:---|:---|
| 🤖 **BadaGPT** | 論文 16 本・1,382 段落 (`src/corpus.json`) を BM25 で検索。Bada エンジンが検索スコアを softmax → `Measure` で振幅にし、そこから段落を選んで回答を組み立てます。回答の各文に **論文名とページ** を付けます。ソースコードより文章の段落を優先します。モードは 3 つ: **答える** / **辞書** (用語の全出現箇所) / **組み換えで生成** (文字 4-gram の統計から新しい文。新しい知識ではないと明示) |
| 🧮 **方程式** | ζ(2)…ζ(8), Γ(1/2), Γ(3/2), Γ(5/2), Γ(1/3), Γ(1/4) を 16 桁で計算し、`(p/q)·基底^k` (基底 π, e, ln 2, √2) との一致を総当たり。ζ(2)=π²/6, ζ(4)=π⁴/90, ζ(6)=π⁶/945, ζ(8)=π⁸/9450, Γ(1/2)=√π などを再発見し、**Bada エンジンが独立に計算し直して** 差 (10⁻¹⁴ 程度) を表示。ζ(3), ζ(5), Γ(1/3), Γ(1/4) は「未知」と表示します (人類の知識の現在の境界) |
| 🫀 **直感ポート** | **A 心臓** (内受容感覚): 脈を触ってタップした基準と、触れずに数えた拍数を比べて精度 0〜1。**B 予感**: 記号を選んだ *後に* 暗号乱数が正解を決める 24 回。偶然 25% と比べた p 値。**C パターン**: 隠れた規則 (左左右左右右, 80%) のある左右予想 48 回。偶然 50% と比べた p 値と学習曲線。「判定」で Bada エンジンが一番強い証拠のポートを選び、**そのポートに映っていたもの** (心拍のリズム / 未来の記号列 / 隠れた規則) を表示。どれも偶然の範囲ならそう表示します |
| ⚛ **Bada エンジン** | `akasha.bada` のソース、デモ実行、直前の入力と出力 |
| 📖 **仕組み** | できること・できないこと、判定基準 |

## Bada 量子エンジン (`src/akasha.bada`)

アプリは入力を Bada の代入文として先頭に差し込み、同梱の Bada インタープリタ
([`bada_gui_ide/www/bada.js`](../bada_gui_ide/www/bada.js)) で実行し、`print` された行を読み取ります。

| MODE | 仕事 | 使う Bada の機能 |
|:---|:---|:---|
| 1 | BadaGPT の段落選択 (正直な無知の判定つき) | `softmax`, `Measure` (測定台帳へコミット), Park–Miller 乱数による非復元抽出 |
| 2 | 方程式の再検証 | Lanczos の Γ (exo-gamma.bada と同じ係数), Euler–Maclaurin の ζ |
| 3 | 直感ポートの判定 | `softmax` → `Measure` の振幅、基準を満たすポートの中で最大 |

単体でも動きます:

```
printf 'DEMO := 1\nMODE := 0\n' | cat - bada_akasha/src/akasha.bada > /tmp/a.bada
node bada_gui_ide/cli/bada-cli.js run /tmp/a.bada
```

## ダウンロード (APK / Windows / Linux)

| プラットフォーム | Artifacts 名 | ファイル |
|:---|:---|:---|
| **Android** | `akasha-android` | `bada-akasha-debug.apk` |
| **Windows 10 / 11** | `akasha-windows` | `BadaAkasha-*-x64.exe` (インストーラ) / `BadaAkasha-*-portable.exe` |
| **Linux** | `akasha-linux` | `BadaAkasha-*-x86_64.AppImage` / `BadaAkasha-*-amd64.deb` |

ビルドは [`akasha-app-build.yml`](../.github/workflows/akasha-app-build.yml): Actions の **Bada Akasha app build** の実行結果 → **Artifacts**。
`akasha-v*` タグを push すると Release にも添付します。

## 開発

```
node bada_akasha/tools/build.js          # src/ から index.html を組み立てる
node bada_akasha/tools/engine-test.js    # テスト (157 件)
python3 bada_akasha/tools/build-corpus.py <論文 PDF...>   # corpus.json を作り直す (要 pypdf)
```

テストは、検索が正しい論文に届くこと、論文にない質問 (株価・宝くじ・前世) が IGNORANCE になること、
Bada の振幅の和が 1 で選択が再現可能なこと、既知の関係の再発見と未知の判定、偽の関係 (ζ(3)=π³/26) を Bada が否定すること、
ランダムな数から偽の関係が出ないこと、予感ポートの偽陽性率が 5% 以下であること、などを確かめます。
