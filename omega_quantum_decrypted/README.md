# omega_quantum_decrypted

**Jones 多項式・量子暗号の解読アプリケーション — Linux / Ubuntu 版**
*Omega-Quantum-Decrypted — a Jones-polynomial quantum-cryptography decryption tool*

Bada / 山口 (Yamaguchi) フレームワーク · 完全自己完結（外部ライブラリ不要）
Part of the [Bada](https://masaaki-avnturle.github.io/Bada/) repository.

> ⚠️ **研究・概念実証 (research / proof-of-concept).**
> このツールは論文で提示された「Jones 多項式 × 量子位相コア」の暗号モデルを
> 実際に動く形にした概念実装です。認証付き対称暗号としては健全に動作しますが、
> 独自方式であり、機密保護の本番用途には確立された標準（OpenSSL 等）を推奨します。

---

## これは何か / What it is

論文群（`badaquantumreviserpaper1`, `caostics`, `quantum_computer4`, `badasource1`）
で述べられた 2 つの数学的対象を 1 つの鍵導出に結び付けます：

1. **Kauffman ブラケット / Jones 多項式** — 結び目図式（knot diagram）の位相不変量。
   状態和 `⟨D⟩ = Σ A^(a−b) · d^(loops−1)`, `d = −A² − A⁻²` を Laurent 多項式として計算し、
   ライズ数（writhe）で正規化して Jones 不変量 `f(A) = (−A)^(−3w)⟨D⟩` を得ます。

2. **Unknown-Prior Engine の位相コア** — reviser 論文 Appendix C：
   ```
   a_i     = softmax(z)_i                  (最大エントロピー事前分布)
   theta_i = Σ_m beta_m · H_m · phi_m^(i)  (蓄積位相)
   psi_i   = sqrt(a_i) · exp(i·theta_i)    (ネイティブ位相値)
   q_i     = |psi_i|² = a_i                (ユニタリ性 |e^{iθ}|=1)
   ```
   定理 1（zero-preservation）: `a_i = 0 ⇒ q_i = 0`（確信ゼロは復活しない）。
   定理 2（`|psi|² = a`）: 純位相ゲートはユニタリ。
   本実装はユニタリ性誤差 `~1e-16`（論文の Hadamard 値 1.11×10⁻¹⁶ と一致）を確認します。

Jones 不変量と位相スペクトルを種（seed）として、SHA-256 ベースの KDF で
32 バイトのマスター鍵を導出し、**SHA256-CTR + HMAC-SHA256** の認証付き暗号
（OQD コンテナ）で暗号化／**解読（復号）** します。

---

## ダウンロード / Download

このリポジトリから取得できます（3 通り）：

### 1. `.deb` パッケージ（Ubuntu / Debian 推奨）
GitHub Actions の **Release** もしくは **Actions アーティファクト** から
`omega_quantum_decrypted_<version>_amd64.deb` をダウンロードして：
```sh
sudo apt install ./omega_quantum_decrypted_1.0.0_amd64.deb
omega_quantum_decrypted selftest
```

### 2. 移植可能な tar.gz
```sh
tar xzf omega_quantum_decrypted-1.0.0-linux-amd64.tar.gz
cd omega_quantum_decrypted-1.0.0-linux-amd64
sudo ./install.sh          # もしくは  PREFIX=$HOME/.local ./install.sh
```

### 3. ソースからビルド（gcc だけでOK）
```sh
git clone https://github.com/masaaki-avnturle/Bada.git
cd Bada/omega_quantum_decrypted
make            # -> build/omega_quantum_decrypted
make test       # セルフテスト + ラウンドトリップ
sudo make install
```
依存は **libc と libm のみ**。OpenSSL 等は不要です。

---

## 使い方 / Usage

```
omega_quantum_decrypted decrypt  <knot.key> <in.oqd>  <out.file> [-p PASS]   # 解読
omega_quantum_decrypted encrypt  <knot.key> <in.file> <out.oqd>  [-p PASS]
omega_quantum_decrypted keyinfo  <knot.key> [-p PASS]
omega_quantum_decrypted inspect  <in.oqd>
omega_quantum_decrypted selftest
omega_quantum_decrypted version | help
```

### 例 / Example
```sh
# 鍵となる結び目図式（trefoil）で暗号化
omega_quantum_decrypted encrypt examples/trefoil.knot secret.txt secret.oqd

# 同じ結び目鍵で解読（復号）
omega_quantum_decrypted decrypt examples/trefoil.knot secret.oqd recovered.txt

# 鍵レポート（Jones span / writhe / 位相エントロピー / ユニタリ性誤差）
omega_quantum_decrypted keyinfo examples/trefoil.knot
```

パスフレーズを併用すると、結び目鍵に加えてパスフレーズも必要になります：
```sh
omega_quantum_decrypted encrypt examples/trefoil.knot m.txt m.oqd -p "私の合言葉"
omega_quantum_decrypted decrypt examples/trefoil.knot m.oqd  out.txt -p "私の合言葉"
```

---

## 結び目鍵ファイル形式 / Knot key file format

1 行 1 交差（crossing）。`#` で始まる行はコメント：
```
# id  a b c d  sign
0  1 2 3 4  1
1  3 4 5 6  1
2  5 6 1 2  1
```
- `a b c d` — 交差の周囲 4 本の辺ラベル（反時計回り）。
- `sign` — 交差の符号 `+1` / `-1`（ライズ数に寄与）。
- 交差数の上限は 24（状態和が 2²⁴）。

同梱例: `examples/trefoil.knot`（三葉結び目 3₁）、`examples/figure8.knot`（8の字 4₁）、
`examples/unknot.knot`。異なる結び目は異なる鍵指紋（fingerprint）を生成します。

**鍵は結び目そのものが握っています。** `.oqd` ファイルとは別に結び目鍵ファイルを
安全に保管してください（鍵指紋はどの結び目鍵で開くかを示すだけで、鍵材料は含みません）。

---

## OQD コンテナ形式 / Container layout

すべてリトルエンディアン：
```
0    4   magic "OQD1"
4    1   version (=1)
5    1   flags (bit0: passphrase 使用)
6    2   reserved
8   16   salt   (ファイルごとにランダム)
24  16   nonce  (CTR nonce, ランダム)
40   8   fingerprint = SHA256(jones||phase seed) の先頭 8 バイト
48   N   ciphertext = plaintext XOR SHA256-CTR keystream
48+N 32  tag = HMAC-SHA256(mac_key, header||ciphertext)
```
鍵スケジュール: `master = KDF(jones_seed ‖ phase_spectrum [‖ passphrase], salt, 120000 回)`、
`enc_key = HMAC(master,"oqd-enc-key")`、`mac_key = HMAC(master,"oqd-mac-key")`。
復号時は HMAC を検証（改ざん・誤鍵を検出）してから復号します。

---

## セキュリティ上の注意 / Security notes

- 認証付き暗号（encrypt-then-MAC, 定数時間比較）で、誤った結び目鍵・誤ったパスフレーズ・
  改ざんは復号前に拒否されます。
- 乱数は `/dev/urandom` から取得。
- SHA-256 / HMAC は FIPS 180-4 / RFC 2104 のテストベクタで検証済み（ビルド時 self-test）。
- ただし本方式は**独自設計の概念実装**です。規制・本番の機密保護には
  監査済みの標準実装をご利用ください。

---

## ライセンス / License

リポジトリの [LICENSE](./LICENSE)（MIT）に従います。
© Masaaki Yamaguchi — Bada / Yamaguchi framework.
