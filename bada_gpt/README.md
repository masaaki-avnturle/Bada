# BadaGPT — 数学の予想を、計算で確かめられる範囲で調べる対話アプリ

話しかけると、ζ 関数の零点の数値検証、深リーマン予想の証拠、擬似量子コンピュータによる反例探索、数学的帰納法による証明と誤った式の修正を実行し、結果と判定を返します。Android / Windows 10・11 / Ubuntu / ブラウザで動き、依存なし・オフライン・単一 HTML です。

> **できないこと**: リーマン予想・深リーマン予想・ゴールドバッハ予想・コラッツ予想などの**未解決問題そのものは証明できません**。これらへの判定は必ず「未解決（経験的証拠のみ）」になります。「証明完了」と出るのは、帰納法で厳密に決まる等式と、コラッツの降下補題のような有限の手続きで確定する主張だけです。
>
> **GPT という名前について**: 言語モデルは入っていません。入力文のキーワードから意図を判定し、決まった計算を実行して文章にします（応答のたびに「意図解析 → 実行 → 検証」を表示）。

## 話しかけ方

| 入力例 | 実行する内容 |
|:--|:--|
| `リーマン予想を高さ 1000 まで調べて` | 偏角の原理による零点総数と臨界線上の符号変化の個数を照合。Schoenfeld 不等式（RH と同値）を x ≤ 10⁶ で検査 |
| `深リーマン予想の証拠を見せて` | 臨界線上のオイラー積の部分積と `L(s,χ)`（実指標の s = 1/2 では `√2·L`）の相対誤差の表 |
| `Σ k^2 = n(n+1)(2n+1)/5` | 帰納法で判定。誤りなら最小の反例を示し、保存量の等位集合へ射影して正しい式に修正して証明 |
| `コラッツ予想を 14 ビットで` | 「最小反例は 2^k 以上で特定の剰余類に属する」という降下補題の証明と、量子探索 |
| `未解決問題の反例を 12 量子ビットで探して` | Grover 探索（リーマン予想の Lagarias 形・ゴールドバッハ・コラッツ・ルジャンドル・対照実験） |
| `ζ(0.5+14.1347i)` | ζ(s) の数値 |
| `証明書を作って` → `証明書を検査して` | 全結果を証明書にまとめて Jones 多項式暗号で封印し、PatchGuard の門（RG01〜RG11）で検査 |

画面上部の「基を読込」「証明書を読込」で JSON を 2 つ読み込むと、書き換え（基 → 後）として検査します。予想を「証明済み」に書き換えた証明書は REJECT になります。

## リポジトリ内の既存アプリケーションとの関係

Python 版 [`riemann_prover/`](../riemann_prover/) を JavaScript に移植したものです（数値結果と Jones 鍵の指紋は Python 版と一致することをテストで確認）。各部品の元になったコード:

| 部品 | 元のコード |
|:--|:--|
| 判定体系（証明完了 / 反証 / 未解決） | 未知事前エンジン `bada_ruby/lib/bada/prover/` |
| ζ 関数 | `bada_webos/apps/discover/lib/zeta.bada`, `bada_ruby/lib/bada/special.rb` |
| 封印 | 量子暗号 `jones_quantum_crypto/` |
| 書き換えの門 | BadaPatchGuard `bada_patchguard/`（ブランチ `ccr-fd691112-eo2fdo`） |
| 量子探索 | 擬似量子コンピュータ `bada_webos/quantum/shor9.py` / `bada_quantos/` |
| 証明の修正 | コマの可積分系エラー修正 `bio_medicine/omega_apriori_injector/plugins/integrable_top.js` |

## 📥 ダウンロード（GitHub Actions）

1. リポジトリの **Actions** タブで **BadaGPT app build** を開きます
2. 最新の成功した実行を開き、ページ下部の **Artifacts** からダウンロードします

| アーティファクト | 中身 | 対象 |
|:--|:--|:--|
| `badagpt-android` | `bada-gpt-debug.apk` | Android 7.0 以上 |
| `badagpt-windows` | `BadaGPT-*-x64.exe`（インストーラ）/ `BadaGPT-*-portable.exe` | Windows 10 / 11 (x64) |
| `badagpt-linux` | `BadaGPT-*-x86_64.AppImage` / `BadaGPT-*-amd64.deb` | Ubuntu (x64) |

ブラウザ版は [`index.html`](index.html) を保存してダブルクリックで開きます。APK はデバッグ署名です（Play ストア配布用の署名ではありません）。EXE はコード署名していないため、初回起動時に Windows の警告が出ます。

ビルドは [`badagpt-app-build.yml`](../.github/workflows/badagpt-app-build.yml) が、`bada_gpt/` への push・`badagpt-v*` タグ・手動実行で行います。

## 🧪 テストとビルド

```sh
node bada_gpt/tools/engine-test.js   # エンジン・対話層・配布 HTML の 74 項目
node bada_gpt/tools/build.js         # src/ から index.html を作り直す
```

## 📁 構成

```
bada_gpt/
├── index.html            # アプリ本体 (自己完結・オフライン。build.js の出力)
├── src/engine.js         # 計算エンジン
├── src/chat.js           # 対話層 (意図判定と文章化)
├── src/ui.html           # 画面
├── tools/build.js        # src/ → index.html
├── tools/engine-test.js  # Node 単体テスト
└── app/
    ├── cordova/config.xml    # Android APK
    └── electron/             # Windows EXE / Ubuntu AppImage・deb
```

## 限界

- 計算は倍精度浮動小数点で、区間演算による厳密な証明ではありません（帰納法と降下補題は整数・有理数の厳密演算）。
- 擬似量子コンピュータはシミュレーションで、オラクルの構成に 2^k 回の古典計算を使うため量子的な高速化はありません。
- 重い計算中は画面が一時的に固まります（高さ 5000・13 量子ビット・18 ビットが上限）。
