# Ω-Apriori Injector — 署名付きAIプラグインSDK

`omega_apriori_cpu` の **未知事前エンジンAI（進化させたゲノム）** を、
**電子デジタル署名（ECDSA P-256 / SHA-256）** を付した自己完結 JavaScript バンドルに
パッケージし、**任意のアプリへ付加**できるようにする SDK です。付加先には
**囲碁の先読み・俯瞰・補完** などのプラグイン（補完機能）を同梱できます。

```
進化ゲノム ──build──▶ runtime+plugins+bootstrap ──sign(ECDSA)──▶ 署名付きバンドル
                                                              │
   付加先アプリ ◀──verify(署名検証OKのみ実行)── plugin.js + manifest.json
```

---

## ⚠ 重要 — 非医療・概念実証・付加先の限定

本ツールは「**自分が管理する／明示的に許諾されたアプリ**」へAI機能を付加するための
署名付きプラグインを生成します。**他者のソフトウェアへ無断で注入する目的には使用しないでください。**
電子署名は、配布したバンドルが**改竄されていない正規のもの**であることを付加先が検証するための
仕組み（真正性・完全性）として用います。実在の医療・人体とは無関係です。

---

## ファイル

| ファイル | 役割 |
|:--|:--|
| `apriori_runtime.js` | 携帯ランタイム: FPGA様LUTファブリックの推論 + プラグインホスト (ブラウザ/Node) |
| `plugins/go_lookahead.js` | 囲碁 先読み (alpha-beta negamax) プラグイン |
| `plugins/overview.js` | 俯瞰 (ヒートマップ・要点・ホットスポット) プラグイン |
| `plugins/completion.js` | 補完 (系列の次要素予測) プラグイン |
| `plugins/integrable_top.js` | 複素回転体(四元数)における相対論的コマの**可積分系エラー修正**プラグイン (保存量 E・|L|²・四元数ノルムへの射影＋Thomas歳差補正＋AI信頼度) |
| `plugins/codegen.js` | 付加したAIを **Verilog(FPGA)/C/Python/JS のソースコードに表出**するプラグイン (`eng.call("codegen","verilog")`) |
| `plugins/patternmatch.js` | 中枢知能FPGAを**パターンマッチ器**化し、分類/レポート/**マッチャ・ソース生成**を行うプラグイン (`eng.call("patternmatch","source","c")`) |
| `plugins/word_complete.js` | **単語補完**プラグイン: 接頭辞＋語彙＋FPGA推論で候補をランク (`eng.call("word_complete","co",{k:8})`) |
| `index.html` | **Injector Studio**: 進化→プラグイン選択→Web Crypto署名→4形式ダウンロード |
| `verify_and_load.js` | **ホスト側ローダ**: 署名検証に通った場合のみバンドルを実行して付加 |
| `run_plugin.js` | **Node CLI**: build / keygen / sign / verify / run（実行形式） |
| `spec.json` | build 用の入力例 (cfg + genome_hex + plugins) |

## 付加形式（ダウンロードできるもの）

- **`omega-apriori.user.js`** — userscript。Tampermonkey 等に入れると任意Webアプリへ付加。
- **`omega-apriori.bundle.html`** — ダブルクリックで動く**実行形式**HTML。
- **`omega-apriori.plugin.js` + `omega-apriori.manifest.json`** — 自前アプリに置き、
  `verify_and_load.js` で**署名検証してから**読み込む。
- **`omega-apriori.keys.jwk.json`** — 鍵ペア（Node で再署名する場合に使用）。

## 使い方

### ブラウザ (Studio)
```bash
python3 -m http.server 8000      # 相対JSを読むため推奨
# http://localhost:8000/ を開く
#  1) 進化 or run.json or ゲノム貼付   2) プラグイン選択
#  3) 鍵生成→バンドル生成＆署名         4) 各形式をダウンロード
#  右パネル「署名を検証して実行」でライブ動作確認（囲碁/補完/俯瞰）
```

### Node CLI（実行形式・自動化）
```bash
node run_plugin.js keygen priv.jwk.json pub.jwk.json
node run_plugin.js build  spec.json omega-apriori.plugin.js
node run_plugin.js sign   omega-apriori.plugin.js priv.jwk.json pub.jwk.json omega-apriori.manifest.json
node run_plugin.js verify omega-apriori.plugin.js omega-apriori.manifest.json   # ✓ VALID
node run_plugin.js run    omega-apriori.plugin.js omega-apriori.manifest.json   # 検証→実行→デモ
```

### 付加先アプリでの読み込み（署名検証付き）
```html
<script src="verify_and_load.js"></script>
<script>
  omegaVerifyAndLoad("omega-apriori.plugin.js","omega-apriori.manifest.json")
    .then(eng => {
      console.log("付加完了:", eng.capabilities());          // ["go_lookahead","overview","completion"]
      console.log(eng.call("completion","AI",4).predicted);  // 補完
      console.log(eng.call("go_lookahead", board, 1, 2).move);// 囲碁先読み
    })
    .catch(e => console.error("署名検証失敗 — 実行しません:", e.message));
</script>
```

検証済み挙動: 署名検証 ✓ VALID → 実行、バンドルを1バイトでも改竄すると sha256 不一致で**実行拒否**。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
