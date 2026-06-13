# Ω-Function Foundry — 自己進化FPGAから「任意の機能」を生成し任意アプリへ付加

ユーザ定義の**複数の任意関数**を、それぞれ未知事前エンジンの **FPGA(LUTファブリック)** として
**テロメア自己進化**で生成し、**名前付き関数ライブラリ**として任意アプリへ付加します。
「任意の機能を、自己進化したFPGAから生成して、任意のアプリに付加」を1画面で実現する鍛造所です。

```
任意関数を定義(例示/プリセット) → 各FPGAをテロメア自己進化 →
  ├─ omega-functions.js  … <script> で貼るだけ付加 → omegaFunctions.call("名",x)
  ├─ 各関数ソース(JS/C/Python/Verilog)
  └─ spec.json(fn_library) … omega_apriori_injector で署名付き付加 → eng.call("fpga_functions","名",x)
```

---

## ⚠ 重要 — 非医療・概念実証

生成されるのは入力6bit(0–63)・出力最大6bitの**ブール関数を学習したLUTネットワーク**です。
小規模ファブリックのため複雑な関数は近似(適合度%を表示)になります。実在の医療・人体とは無関係です。

## 使い方
```bash
xdg-open index.html        # or: python3 -m http.server 8000
```
1. **関数を定義**: 名前＋（プリセット: popcount/parity/×2/+1/XOR/mod3、または 例示 `x=y`）。複数追加可。
2. **鍛造**: 「全FPGAを自己進化で鍛造」→ 各関数のFPGAをテロメアGAで進化、適合度を表示。
3. **生成物**:
   - `omega-functions.js`（自己完結ライブラリ。`omegaFunctions.list/call/meta`）
   - 各関数のソース（JS/C/Python/Verilog）
   - `spec.json`（`fn_library` 付き。署名付き付加用）

## 付加先での利用
```html
<!-- 貼るだけ -->
<script src="omega-functions.js"></script>
<script>
  omegaFunctions.list();          // ["popcount","double",...]
  omegaFunctions.call("double",10); // FPGAで評価
</script>
```
```js
// 署名付き(omega_apriori_injector でビルド/署名後)
eng.call("fpga_functions","double",10)        // 名前付きFPGA関数を実行
eng.call("fpga_functions","source","double","c") // その関数のC/Verilog等を表出
eng.call("fpga_functions","list")
```

検証済み: 関数定義→自己進化→`omega-functions.js`生成→`call()`動作、
および `spec.json`→injector署名→付加先 `fpga_functions`（`fn_library`をmanifest経由で伝播）で list/call/source 動作。

## 関連
`omega_apriori_injector`(fpga_functions プラグイン) · `omega_self_evolve` · `omega_patternforge` · `omega_codegen` · `omega_widget` · `omega_attach_station`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
