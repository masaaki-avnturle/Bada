# Ω-PatternForge — テロメア分裂限界で生成するパターンマッチAI

`analyze/GammaFunction.pdf` の **Γ大域的部分積分多様体** `e^{−x log x}` に基づき、
**テロメア分裂で自己進化**し、**テロメア分裂の限界値(Hayflick限界)に到達した時点で**
最良マッチャを「生成」する生成AIです。中枢知能FPGA(LUTファブリック)が学習したパターンを、
**パターンマッチ用ソースコード(C/Python/JS/Verilog)に生成**します。依存なし・ダブルクリック動作。

```
パターン定義(例示/プリセット)
   │
Γカーネルで変調したテロメア分裂・自己進化
   │   ← 分裂ごとにテロメア短縮。テロメラーゼで限界を延長(回数制限)
   ▼
全個体がHayflick限界に到達 = テロメア分裂の限界値 → 【生成トリガ】
   │
中枢知能FPGAが学習したパターン → pattern_match() ソース(C/Py/JS/Verilog)
   │
omega_apriori_injector で署名・任意アプリへ付加(機能拡張)
```

---

## ⚠ 重要 — 非医療・概念実証

「テロメア分裂」「自己進化」は**遺伝的アルゴリズムのメタファ**です。生成されるのは
学習したブール・パターンを判定する `pattern_match()` 関数(LUTネットワーク)で、
実在の医療・人体とは無関係です。

## 生成の鍵: 「分裂限界での生成」

通常のGAと違い、本アプリは**テロメア分裂の限界値で生成イベントが起きます**:
分裂ごとにテロメアが短縮し、全個体が Hayflick 限界 (`初期×limFrac`) に達すると、
テロメラーゼ予算が残っていれば限界を延長、尽きれば**その世代で最良マッチャを生成**します。
チャートの縦線が生成点(分裂限界)です。

## パターン
- 回文(ビット対称) / x mod 3 / マスク一致(0b010101) / popcount / **カスタム例示**(`x=label` 改行区切り)

## 使い方
```bash
xdg-open index.html        # or: python3 -m http.server 8000
# ① パターン選択 ② テロメア分裂限界設定 ③ 実行(限界まで自己進化→生成)
# ④ pattern_match ソース(C/Py/JS/Verilog)を表示・DL ⑤ spec.json をDLして付加
```

### 任意アプリへ付加
```bash
cd ../omega_apriori_injector
node run_plugin.js build  <DL>/pattern_match.spec.json plugin.js
node run_plugin.js sign   plugin.js priv.jwk.json pub.jwk.json manifest.json
node run_plugin.js run    plugin.js manifest.json
# 付加先で: eng.call("patternmatch","classify",[5,42,63])
#           eng.call("patternmatch","source","c")  → pattern_match()/is_match() を生成
```

## 関連
`omega_tomograph` · `omega_apriori_cpu` · `omega_codegen` · `omega_apriori_injector` · `omega_telomere_forge`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
