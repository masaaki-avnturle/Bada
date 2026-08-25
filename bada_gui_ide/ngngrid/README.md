# NGN Quantum Grid — zone:// を NTT NGN 回線に投射

ウルトラネットワーク **`zone://url.or.jp`** を **NTT NGN 回線**に投射した
シミュレーション システムです。これまでに作った各層を融合します:

- **NTT NGN バックボーン** → zone:// の P2P リング(地域局が環のピア。
  記録は UltraDatabase として複数局に複製)。
- **各家庭・職場の PC(ノイマン型)** → NTT 加入者線の葉ノード。各 PC は
  **HDD 擬似量子レジスタ**(セクタが `|ψ|²` 状態を保持)を持ちます。
- **エンタングルメント** → PC 間で NTT 回線上に張る Bell 対
  (`H` + `CNOT` + `Measure`)。禁制状態 `|01>,|10>` がゼロのまま=
  相関の整合(=盗聴なしの証拠)。
- **zone://url.or.jp** → NGN 上で UltraDatabase クォーラムに複製・**Jones
  多項式量子暗号**で封緘され、各 PC が NTT 経由で取得(200 + quorum + AEAD)。

## ファイル

```
ngngrid/
  ngn-extra.bada     zone-lib に載せる NGN/HDD/エンタングル拡張 (Bada)
  cli/ngn-project.js このマシンを NGN グリッドに投射(自分のIP検出→登録→
                     エンタングル→zone取得)(Node)
```
- 可視化アプリ(単一HTML): `../dist/ngn-quantum.html`
  (`node ../tools/build-ngngrid.js` で生成)
- 統合デモ(CLI/IDE): `../examples/ngn-quantum.bada`
  (`node ../tools/build-ngn-example.js` で生成)
- 基盤は `../browser/zone-lib.bada`(zone:// + UltraDB + Jones暗号)を再利用。

## 使い方

```sh
# 可視化: dist/ngn-quantum.html を開き、
#   「NTT回線でエンタングル」→ 各PC間にBell対の相関線が描かれます
#   「zone://url.or.jp を NTT経由で取得」→ 200 / quorum / Jones鍵 を表示
# デモ(CLI):
node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/ngn-quantum.bada
# このマシンを投射:
node bada_gui_ide/ngngrid/cli/ngn-project.js
```

## 位置づけ

これは既存コンポーネント(zone:// ランタイム・UltraDB・Jones量子暗号・
Bada の量子レジスタ)を **NTT NGN のトポロジに写像したシミュレーション**です。
実際の NTT 設備・回線を操作するものではなく、各家庭/職場PCを擬似量子ノードと
見立てて zone:// ウルトラネットワークを描く、Bada 上のモデルです。
