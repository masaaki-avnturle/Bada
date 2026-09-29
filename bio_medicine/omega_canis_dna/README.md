# Ω-Canis DNA — 戌 (イヌ) DNA 検査

対象者の **DNA 配列データ (FASTA / FASTQ)** に、イヌ (*Canis lupus familiaris*) 由来の配列が
含まれているかを判定するアプリです。あわせて、fMRI・MRI・脳トポグラフィー・血液検査・脳磁場 (MEG)・
体表熱の値を `analyze/GammaFunction.pdf` の **Γ大域的部分積分多様体** `∫Γ(γ)′dx_m = 2e^{−x log x}` で
熱重みに変換し、**Jones 多項式** `V(t)` を `t = e^{−β}` で評価する概念ビューを備えます。
依存ライブラリなし・オフライン動作。

---

## ⚠ 重要 — どのデータで何が分かるか

| 入力 | 戌 DNA の判定に使うか | 理由 |
|:--|:--|:--|
| DNA 配列 (FASTA/FASTQ) | **使う (唯一の判定根拠)** | 塩基配列そのものを種の参照ゲノムと照合できる |
| 23andMe 等の SNP 生データ | 使えない | ヒト SNP の遺伝型のみで、配列を含まない |
| fMRI / MRI / 脳トポグラフィー / MEG / 体表熱 | 使えない | 神経活動・組織コントラスト・磁場・温度の計測で、DNA 情報を含まない |
| 血液検査 (生化学・血算) | 使えない | 成分濃度で、DNA 配列を含まない (血液から DNA を抽出・シーケンスすれば配列として使える) |

- ヒトのゲノムにイヌの DNA が遺伝的に含まれることは生物学的にありません。ヒト試料から検出された場合、
  通常はペットの毛・唾液、器具・試薬からの**混入 (コンタミネーション)** です。
- ② の Γ×Jones 熱エネルギー値は、Jones 多項式の計算そのものは厳密ですが、生体値への意味づけは概念モデルです。
- 非医療・研究/教育用です。

## ① 戌 DNA 配列検査 (本物の計算)

1. イヌ mtDNA (NCBI **NC_002008.4**) とヒト mtDNA (NCBI **NC_012920.1**, rCRS) の k-mer (相補鎖含む) を列挙し、
   一方の種にしか現れない**種固有 k-mer**の索引を作る。
2. 各リードの k-mer を引き、固有ヒット数が最小ヒット数以上かつ他種の 4 倍以上ならその種に割り当てる。
3. イヌ割当リード 0 → 陰性、少数 (<3 本 または <1%) → 痕跡/混入疑い、それ以上 → 混合 / イヌ由来試料。

参照配列は CI ビルド時に `tools/fetch_refs.py` が NCBI から取得して `www/refs.js` に同梱します。
ブラウザで直接開く場合は、アプリ内で参照 FASTA を読み込むか、先に `python3 tools/fetch_refs.py` を実行してください。
「合成試料で検査」で、参照から作った変異入りリードに対して判定が正しく働くかを確認できます。

## ② 生体データ × Γ×Jones 熱エネルギー (概念指標)

- 各モダリティ値 `x∈(0,1]` → Γ熱重み `w = 2e^{−x log x}`、`β = mean(w)`、`t = e^{−β}`。
- 結び目 (3_1, 4_1, 5_1) の Jones 多項式を PD 符号から **Kauffman ブラケットの状態和**で計算し、`|V(t)|` を表示。
- 既存アプリ (`omega_tomograph`, `omega_thermal_trace`, `omega_biofeedback` など) の出力を正規化して入力できます。

## ダウンロード (GitHub Actions)

- **Actions** タブ → 「Ω-Canis DNA build (APK + Windows EXE + Linux)」→ 最新の実行 (または **Run workflow**) → Artifacts:
  - `omega_canis_dna-android` — APK
  - `omega_canis_dna-windows` — Windows 10/11 EXE (インストーラ + ポータブル)
  - `omega_canis_dna-linux` — AppImage + deb
- タグ `canis-v1.0.0` を push すると **Releases** にも添付されます。

## テスト

```bash
node tests/test_core.js   # Jones 多項式 (3_1, 4_1, 5_1) と k-mer 種判別の検証
```

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 非医療・研究/教育用*
