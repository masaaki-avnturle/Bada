# Ω-SelfEvolve — 自己進化できるソースコード＋一意の機能(UID)

`analyze/GammaFunction.pdf` の **Γ大域的部分積分多様体** に基づき、**テロメア分裂で自己進化**する
未知事前エンジンを鍛造し、次の2つを生成します:

1. **自己進化できるソースコード** — 進化ループ(`selfEvolve()`)とゲノムを内蔵した JS/Python モジュール。
   付加先で目標関数へ向けて自分を進化させ続けられる(テロメア限界まで)。
2. **一意の機能 (UID)** — ゲノムから決定論的に導く一意フィンガープリント (`OAE-xxxxxxx-xxxxxxx`)。
   自己進化でゲノムが変わると更新され、各AIインスタンスを一意に識別する。

生成 `spec.json` は `omega_apriori_injector` で署名し、`omega_host_app` 等の**任意アプリへ付加**できます。

```
テロメア分裂・自己進化  →  一意ID(UID)  →  自己進化ソース(進化ループ内蔵)  →  任意アプリへAI付加
```

---

## ⚠ 重要 — 非医療・概念実証

「テロメア分裂」「自己進化」は遺伝的アルゴリズムのメタファです。生成コードは小さなブール関数を
学習・自己改良する LUT ネットワークで、実在の医療・人体とは無関係です。

## 使い方
```bash
xdg-open index.html        # or: python3 -m http.server 8000 (Python版ソース生成・厳密一致)
```
1. **鍛造**: テロメア自己進化で初期エンジンを生成。UID と適合度を表示。
2. **もう一段 自己進化**: 1+1 戦略でテロメアを消費しつつ自己改良。ゲノムが変われば **UID更新**。
3. **自己進化ソース**: 進化ループ内蔵の JS/Python を表示・ダウンロード。
4. **付加**: `spec.json` をダウンロードし、`omega_apriori_injector` で署名→任意アプリへ付加。

### 付加先での自己進化 (self_evolve プラグイン)
```js
eng.call("self_evolve","uid")                       // 一意ID
eng.call("self_evolve","step",{target:"popcount"})  // ホスト内で実行時自己進化(テロメア消費)
eng.call("self_evolve","source","js")               // 自己進化できるソース生成
```

## 関連
`omega_telomere_forge` · `omega_patternforge` · `omega_codegen` · `omega_apriori_injector` · `omega_host_app`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
