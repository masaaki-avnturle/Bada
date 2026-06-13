# Ω-Attach Station — 上のアプリを「任意のアプリ」へ付加する統合生成器

`bio_medicine` の未知事前エンジン＋プラグイン(8種)を **ECDSA 署名付きバンドル**にし、
**対象アプリの種別ごとに「貼るだけ／置くだけ」で付加できる成果物**を生成する統合ステーションです。
`omega_apriori_injector`・`omega_host_app`・`omega_self_evolve` 等の機能を任意アプリへ運べます。

## 生成できる付加アーティファクト（対象アプリ別）

| 対象 | 成果物 | 付加方法 |
|:--|:--|:--|
| 任意Webサイト | `userscript` (.user.js) | Tampermonkey 等に貼付 |
| 任意ページ | ブックマークレット | ブックマークURLに貼付（plugin.js を配置） |
| 任意Webアプリ | DevToolsコンソール片 | F12→Console に貼付（その場付加） |
| 自前Webアプリ | HTML埋め込み(署名検証) | `verify_and_load.js`＋plugin.js＋manifest.json を配置 |
| Node アプリ | `require` 片 | plugin.js を同梱（`run_plugin.js run`で署名検証実行も可） |
| Electron アプリ | preload.js | contextBridge で `omegaApriori` を公開 |

共通DL: `omega-apriori.plugin.js`（署名付きバンドル）/ `omega-apriori.manifest.json`（署名・公開鍵）/ `verify_and_load.js`。

---

## ⚠ 重要 — 非医療・概念実証・付加先の限定

付加は **自分が管理する／明示的に許諾されたアプリ**に対してのみ行ってください。
ECDSA 署名は、配布バンドルが改竄されていない正規物であることを付加先が検証するためのものです。

## 使い方
```bash
python3 -m http.server 8000     # runtime/plugins を相対読込するため推奨
# 1) 付加する機能を選択 → 進化 or spec.json で genome 設定
# 2) ホスティングURLを入れて「署名付きバンドル生成」
# 3) 対象アプリ種別タブで成果物をコピー/ダウンロードして付加
```

付加後、対象アプリ内で:
```js
omegaApriori.capabilities()
omegaApriori.call("word_complete","co",{k:8})
omegaApriori.call("self_evolve","uid")
omegaApriori.call("codegen","verilog")
```

## 関連
`omega_apriori_injector`(署名付きSDK・8プラグイン) · `omega_host_app` · `omega_self_evolve` · `omega_patternforge` · `omega_codegen`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
