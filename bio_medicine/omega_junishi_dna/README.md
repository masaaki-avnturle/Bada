# Ω-Junishi DNA — 十二支 DNA 検査

対象者の **DNA 配列データ (FASTA / FASTQ)** に、十二支の動物に由来する配列が含まれているかを
種ごとに判定するアプリです (旧 Ω-Canis DNA「戌 DNA 検査」を十二支全体に拡張)。
あわせて、fMRI・MRI・脳トポグラフィー・血液検査・脳磁場 (MEG)・体表熱の値を `analyze/GammaFunction.pdf` の
**Γ大域的部分積分多様体** `∫Γ(γ)′dx_m = 2e^{−x log x}` で熱重みに変換し、**Jones 多項式** `V(t)` を
`t = e^{−β}` で評価する概念ビュー、生まれ年の干支 (参考表示) を備えます。依存ライブラリなし・オフライン動作。

| 十二支 | 動物 | 参照 mtDNA (学名) |
|:--:|:--|:--|
| 子 | ネズミ | *Mus musculus* |
| 丑 | ウシ | *Bos taurus* |
| 寅 | トラ | *Panthera tigris* |
| 卯 | ウサギ | *Oryctolagus cuniculus* |
| 辰 | 竜 | — (伝説上の生物で DNA が存在しないため検査対象外) |
| 巳 | ヘビ | *Elaphe climacophora* (アオダイショウ。NCBI で取得できない場合は近縁種) |
| 午 | ウマ | *Equus caballus* |
| 未 | ヒツジ | *Ovis aries* |
| 申 | サル | *Macaca fuscata* (ニホンザル。取得できない場合は *M. mulatta*) |
| 酉 | ニワトリ | *Gallus gallus* |
| 戌 | イヌ | *Canis lupus familiaris* |
| 亥 | イノシシ | *Sus scrofa* |
| (宿主) | ヒト | *Homo sapiens* (rCRS) |

---

## ⚠ 重要 — どのデータで何が分かるか

- **十二支の「性質」(性格) は民間伝承で、DNA・遺伝では決まりません。** 本アプリが DNA で調べるのは
  「その動物の DNA が試料に含まれるか」だけです。生まれ年の干支と伝承上の性質は参考表示で、検査結果とは無関係です。
- 判定の根拠は **DNA 配列照合のみ**。SNP 生データ (23andMe 等) は配列を含まないため使えません。
  fMRI / MRI / 脳トポグラフィー / MEG / 体表熱 / 血液検査の値にも DNA の種情報は含まれないため、② は概念指標です。
- ヒトのゲノムに他の動物の DNA が遺伝的に含まれることはありません。ヒト試料から検出された場合、
  通常は食品・ペットや家畜との接触・器具や試薬からの**混入 (コンタミネーション)** です。
- 非医療・研究/教育用です。

## ① 十二支 DNA 配列検査 (本物の計算)

1. 11 種 + ヒトの mtDNA 全長の k-mer (相補鎖含む) を列挙し、1 種にしか現れない**種固有 k-mer**の索引を作る。
2. 各リードの k-mer を引き、固有ヒット数が最小ヒット数以上かつ次点の種の 4 倍以上ならその種に割り当てる。
3. 種ごとに: 割当 0 → 非検出、少数 (<3 本 または <1%) → 痕跡/混入疑い、<50% → 混合、それ以上 → 主成分。

参照配列は CI ビルド時に `tools/fetch_refs.py` が NCBI から取得し (FASTA ヘッダの学名で検証)、`www/refs.js` に同梱します。
ブラウザで直接開く場合は、アプリ内で参照 FASTA (マルチ FASTA 可、ヘッダの学名で種を自動判別) を読み込むか、
先に `python3 tools/fetch_refs.py` を実行してください。
「合成試料で検査」で、選んだ動物のリードを混ぜた試料に対して判定が正しく働くかを確認できます。

## ② 生体データ × Γ×Jones 熱エネルギー (概念指標)

- 各モダリティ値 `x∈(0,1]` → Γ熱重み `w = 2e^{−x log x}`、`β = mean(w)`、`t = e^{−β}`。
- 結び目 (3_1, 4_1, 5_1) の Jones 多項式を PD 符号から **Kauffman ブラケットの状態和**で計算し、`|V(t)|` を表示。

## ダウンロード (GitHub Actions)

- **Actions** タブ → 「Ω-Junishi DNA build (APK + Windows EXE + Linux)」→ 最新の実行 (または **Run workflow**) → Artifacts:
  - `omega_junishi_dna-android` — APK
  - `omega_junishi_dna-windows` — Windows 10/11 EXE (インストーラ + ポータブル)
  - `omega_junishi_dna-linux` — AppImage + deb
- タグ `junishi-v1.0.0` を push すると **Releases** にも添付されます。

## テスト

```bash
node tests/test_core.js   # Jones 多項式・十二支 11 種 + ヒトの k-mer 種判別・干支計算の検証
```

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 非医療・研究/教育用*
