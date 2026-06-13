# Ω-Host App — 生成FPGAを付加して機能拡張する「任意アプリ」デモ

普通の**メモ帳/エディタ**（＝任意アプリの代表）に、生成FPGA（未知事前エンジン）を**付加**し、
**単語補完(word completion)** をはじめ俯瞰・系列補完・パターンマッチ・FPGAソース表出などの機能を
ライブで付加・拡張するデモです。組み込みエンジンで即動作し、`omega_apriori_injector` が出力した
**署名付きバンドル**(`plugin.js` + `manifest.json`)を**ECDSA署名検証**してから付加することもできます。

```
任意アプリ(メモ帳) ──付加── 生成FPGA(未知事前エンジン) + プラグイン
        │                         │
   テキスト入力 ──単語補完──▶ 候補ランク(接頭辞被覆率+頻度+FPGA推論)
        └── 機能パレット: 俯瞰 / 系列補完 / パターンマッチ / FPGAソース表出
```

---

## ⚠ 重要 — 非医療・概念実証・付加先の限定

「付加」は **自分が管理する／明示的に許諾されたアプリ**に対してのみ行ってください。
署名検証は配布バンドルが改竄されていない正規物であることを確認するためのものです。

## 使い方

```bash
xdg-open index.html        # or: python3 -m http.server 8000
```

- **単語補完**: エディタに単語を打つと候補チップが出ます。<kbd>Tab</kbd> で先頭候補を採用、クリックで個別採用。
  語彙＝既定辞書＋文書中の既出語（適応学習）。順位は接頭辞被覆率＋頻度＋付加FPGAの推論バイアス。
- **機能パレット**: 俯瞰(文書要約) / 系列補完(選択) / パターンマッチ(選択数値) / FPGAソース表出 / 付加機能一覧。
- **生成FPGAバンドルを付加**: `omega_apriori_injector` / `omega_patternforge` 等が出力した
  `plugin.js` + `manifest.json` を読み込み「署名検証して付加」。検証OKのみ実行し、付加機能が増えます。

### 付加バンドルの作り方
```bash
cd ../omega_apriori_injector
node run_plugin.js build  spec.json plugin.js     # word_complete を含む6+プラグイン
node run_plugin.js keygen priv.jwk.json pub.jwk.json
node run_plugin.js sign   plugin.js priv.jwk.json pub.jwk.json manifest.json
# 生成した plugin.js / manifest.json を本アプリで読み込んで付加
```

## 関連
`omega_apriori_injector`(付加SDK・word_completeプラグイン) · `omega_patternforge` · `omega_codegen` · `omega_telomere_forge`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
