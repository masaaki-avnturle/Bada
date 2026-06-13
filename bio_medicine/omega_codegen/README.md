# Ω-Apriori CodeGen — AIソースコード生成器

`omega_apriori_cpu` の **未知事前エンジン(進化LUTファブリック)** を、合成可能な
**Verilog(FPGA) / C / Python / JavaScript のソースコードに表出**し、さらに
**量子囲碁 / 量子将棋** の測定結果から **FPGA構成(ゲノム)を生成**するスタジオです。
生成物は `omega_apriori_injector` で署名付きプラグインとして任意アプリへ付加できます。

```
進化 or 量子囲碁/量子将棋  →  ゲノム(FPGA構成)  →  Verilog/C/Python/JS に表出  →  ダウンロード/付加
```

---

## ⚠ 重要 — 非医療・概念実証

「量子将棋/量子囲碁」は**重ね合わせ・エンタングルの簡易状態ベクトルモデル**です。
生成コードは小さなブール関数を実装するLUTネットワークで、実在の医療・人体とは無関係です。

---

## ファイル

| ファイル | 役割 |
|:--|:--|
| `codegen.js` | ファブリック→ Verilog / C / Python / JS の変換器 (ブラウザ/Node) |
| `quantum_games.js` | 状態ベクトル量子シミュレータ + 量子囲碁/量子将棋からの**ゲノム(FPGA)生成** |
| `index.html` | **CodeGen Studio**: 生成元選択→各言語表出→ダウンロード、量子盤可視化 |
| `codegen_cli.js` | Node CLI: `emit`(コード表出) / `quantum`(量子ゲーム→FPGA生成) |

## 使い方

### ブラウザ Studio
```bash
python3 -m http.server 8000     # 相対JS読込のため
# ① 構成 → ② 進化 or ⚛量子囲碁 or ⚛量子将棋 → ③ Verilog/C/Python/JS を表示・DL
```

### Node CLI
```bash
# 既存の進化ゲノム(spec.json)を各言語へ表出
node codegen_cli.js emit ../omega_apriori_injector/spec.json verilog omega.v
node codegen_cli.js emit ../omega_apriori_injector/spec.json c

# 量子囲碁/量子将棋から FPGA を生成 (.v / .c / .spec.json)
node codegen_cli.js quantum go    game-A  qgo
node codegen_cli.js quantum shogi game-B  qshogi
```

### 生成された FPGA を任意アプリへ付加
```bash
# 生成 spec を署名付きプラグインに
cd ../omega_apriori_injector
node run_plugin.js build  ../omega_codegen/qgo.spec.json plugin.js
node run_plugin.js keygen priv.jwk.json pub.jwk.json
node run_plugin.js sign   plugin.js priv.jwk.json pub.jwk.json manifest.json
node run_plugin.js run    plugin.js manifest.json   # 付加先で codegen プラグインがAI自身のVerilogを出力
```

生成コードの正しさは検証済み: 生成した **C / Python / JS は全入力でランタイム評価と完全一致**
（Verilog も同一論理）。`codegen` プラグインにより、付加先アプリ内でAIが
`eng.call("codegen","verilog")` で自分自身のFPGAソースを実行時出力できます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
