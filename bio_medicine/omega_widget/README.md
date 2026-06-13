# Ω-Apriori Widget — 任意アプリに「貼るだけ」で付加する完成ウィジェット

これまでの機能（未知事前エンジン＋プラグイン）を、**単一の自己完結ファイル `omega-attach.js`** にまとめた
**完成済み付加ウィジェット**です。生成器（`omega_attach_station`）と違い、これは**そのまま貼るだけ**で動きます。

読み込むだけで任意のWebアプリに次が付加されます:
- `window.omegaApriori`（エンジン＋6プラグイン）
- 右下のフローティング **Ω ボタン＋パネル**（俯瞰 / 系列補完 / 一意ID / 自己進化 / FPGAソース表出 / 機能一覧）
- ページ内の `input[type=text]` / `textarea` への **単語補完**（候補ドロップダウン、<kbd>Tab</kbd>で採用）

依存なし・単一ファイル・約7KB。

---

## ⚠ 重要 — 非医療・概念実証・付加先の限定

付加は **自分が管理する／明示的に許諾されたアプリ**に対してのみ行ってください。

## 付加方法（いずれか）

```html
<!-- ① 自前アプリ: HTML に1行 -->
<script src="omega-attach.js"></script>
```
```text
② userscript:  omega-attach.user.js を Tampermonkey に登録 (OMEGA_SRC を配置先に設定)
③ DevToolsコンソール:  omega-attach.js の中身を貼り付けて Enter (その場で付加)
④ bookmarklet:  javascript:(()=>{var s=document.createElement('script');s.src='URL/omega-attach.js';document.body.appendChild(s);})()
```

## 試す
```bash
xdg-open demo.html        # or: python3 -m http.server 8000
# demo.html は Ω を知らない普通のフォームアプリ。<script src="omega-attach.js"> だけで
# 単語補完と Ω パネルが付加される様子を確認できます。
```

## 付加後の API
```js
omegaApriori.capabilities()                    // ["word_complete","completion","overview","patternmatch","self_evolve","codegen"]
omegaApriori.call("word_complete","con",{k:8}) // 単語補完
omegaApriori.call("self_evolve","uid")         // 一意ID (OAE-xxxxxxx-xxxxxxx)
omegaApriori.call("self_evolve","step")        // 実行時テロメア自己進化
omegaApriori.call("codegen","verilog")         // FPGAソース表出
omegaApriori.infer(45)                          // 生エンジン推論
```

## 関連
- `omega_attach_station` — 署名付き＋多形式の付加アーティファクト生成器（より高機能）
- `omega_apriori_injector` — 署名付きプラグインSDK（8プラグイン）
- `omega_host_app` / `omega_self_evolve` / `omega_patternforge` / `omega_codegen`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
