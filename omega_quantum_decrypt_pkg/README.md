# omega_quantum_decrypt — Jones × Burau × Shor 復号アプリケーション

`secretdata.pdf` と `quantum_computer4.pdf`（山口理論）で述べられている復号のパイプラインを、
**実際に動く**アプリケーションとして実装したものです。技術用語をそのまま実数学の演算に対応させ、
末尾の「暗号が掛けられたUSBスティック」を最後まで解きます。

A runnable realization of the decryption pipeline sketched in `secretdata.pdf`.
Every step of the request maps onto a standard, verifiable mathematical
operation — no numerology.

---

## リクエスト文 → 実装の対応 (request → implementation)

`secretdata.pdf` の核心式は `y = π(χ,x) ⋄ f(x) − f(x) ⋄ π(χ,x)`（＝**交換子／差分**）で、
RSA と非可換方程式が復号対象として名指しされています。ご依頼の一文は次のように分解できます。

| ご依頼の語 (your phrase) | 実際の数学 (real math) | モジュール |
|---|---|---|
| 暗号が掛けられたUSBスティック | RSA 暗号文（＝復号対象の "secret data"） | `rsa_toy.py` |
| Jones多項式の乱数を掛ける | Kauffman ブラケット／Jones 多項式のサンプル値 | `jones.py` |
| 逆行列の暗号 ＋ 基本群の性質 | **Burau 表現**（組み紐補空間の基本群に由来）。行列式が単元 `±vᵏ` ⇒ 逆行列が存在すると判定 | `jones.py`, `matrix.py` |
| その式で差分する (`π⋄f − f⋄π`) | 行列の**交換子** `[π,f]`。二つの Jones 乱数化を差分し Δ=0 で鍵一致（PDF の "pair check with success"） | `commutator.py` |
| 量子暗号の解読に相関する機能 | **Shor のアルゴリズム**（位数発見）で RSA を因数分解し秘密鍵を復元 | `shor.py` |
| 対象の暗号を解く | 上記を連結して平文を復元 | `pipeline.py` |

---

## 実行方法 (usage)

依存パッケージなし（Python 3 標準ライブラリのみ）。

```sh
cd omega_quantum_decrypt_pkg

# 全部入りデモ: ターゲットを生成 → 6段パイプラインで解読
python3 -m omega_qdecrypt.cli demo "3: 1 1 1"

# 個別ツール
python3 -m omega_qdecrypt.cli jones  "2: 1 1 1"        # 三葉結び目の Jones 多項式・鍵
python3 -m omega_qdecrypt.cli invmat "3: 1 2 1 2 1 2"  # Burau 行列と逆行列存在判定
python3 -m omega_qdecrypt.cli crack  --e 65537 --N 120194077 --cipher 35533253,98963345

# まとめて実行（テスト含む）
sh run_demo.sh
python3 tests/test_all.py
```

組み紐の記法 `"<本数>: <符号付き生成元>"`。例 `"2: 1 1 1"` は σ₁³ の閉包＝三葉結び目。

### デモ出力（抜粋）

```
=== 1. Jones multipliers (Kauffman bracket samples) ===
=== 2. Inverse-matrix cipher (Burau / fundamental group) ===
  det_B: -1*v^3
  inverse_exists: True                 ← 基本群由来の Burau 行列は逆行列を持つ
=== 3. Difference / commutator pair-check (Delta) ===
  key_matches_true_braid: True         ← 差分 Δ=0 ⇒ 鍵一致
=== 4. Quantum decryption (Shor order-finding) ===
  factored: True   p: 10007  q: 12011  ← Shor が N を因数分解
=== 5. Target cipher solved ===
>>> SOLVED. plaintext = 'MASAAKI-YAMAGUCHI/JONES-MANIFOLD/USB'
```

---

## 数学的な裏付け (what is verifiable)

- **Jones 多項式** — Kauffman ブラケットの状態和で計算。三葉結び目 σ₁³ の閉包で
  `V(t) = −t⁻⁴ + t⁻³ + t⁻¹`、非結び目で正規化ブラケット `= 1` になることを単体テストで固定。
- **Burau 表現** — σᵢ の 2×2 ブロック `[[1−v, v],[1,0]]`。組み紐補空間の無限巡回被覆の
  ホモロジーへの作用で、被覆は基本群から構成される。`det(B)` は常に単元 `±vᵏ` ＝逆行列が存在。
- **交換子／差分** — `[π,f] = πf − fπ`。組み紐生成元は非可換（テストで確認）。
- **Shor** — 位数発見による因数分解。トイ RSA を実際に破って平文を復元。

すべて `python3 tests/test_all.py`（12 件）で検証済み。

---

## 正直な但し書き (honest disclaimer)

このアプリは **実在の暗号（2048bit RSA や AES-256）を破りません**。破れるものは一切含まれていません。

- Shor の「量子」部分（位数発見）は**古典シミュレーション**です。一般には指数時間かかるため、
  本アプリが因数分解できるのは**おもちゃサイズ**の N（数十ビット）に限られます。これは
  「量子計算が暗号を破る」仕組みを忠実に**再現・学習**するデモです。
- 既存の `omega_jones_crypto_pkg`（AES-256-GCM）は、正しい結び目図＝鍵を持っている場合にのみ
  復号できる、まっとうな鍵導出方式です。Jones 多項式で AES を「解読」できるわけではありません。
- 差分 Δ・交換子・逆行列存在判定は、鍵の**整合性チェック**（一致検証）として機能します。
  実際に暗号を解くゲートは Shor（RSA 因数分解）です。

つまり本パッケージは、山口理論の枠組みを実数学で忠実に表現した、**動作する教育的デモ**です。

---

## 構成 (layout)

```
omega_quantum_decrypt_pkg/
  omega_qdecrypt/
    laurent.py       # Z[v, v^-1] 上のローラン多項式
    matrix.py        # 多項式行列・行列式・逆行列存在判定
    jones.py         # 組み紐 → Burau / Kauffman ブラケット / Jones 多項式 / 鍵導出
    commutator.py    # 差分 [π,f] と Δ ペアチェック
    shor.py          # Shor 位数発見による RSA 破り（量子部分の古典シミュレーション）
    rsa_toy.py       # 復号対象を作るためのトイ RSA
    pipeline.py      # 6 段パイプラインの統合
    cli.py           # コマンドライン
  examples/trefoil_braid.txt
  tests/test_all.py
  run_demo.sh
```

関連: 同リポジトリの `omega_jones_crypto_pkg`（C 実装の Jones→AES-256-GCM 鍵導出）と同じ
鍵導出レシピを `jones.derive_key` で Python 再現しています。
