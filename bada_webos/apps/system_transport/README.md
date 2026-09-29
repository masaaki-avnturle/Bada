# system_transport — 方程式群の列挙・解析と次元輸送機（Bada）

レポート **system_transport.pdf**（100 ページ・14 論文の合本）、**quantum_computer4.pdf**、
**caostics.pdf**、および **inter_dimensional_port_directory.pdf** に記述された方程式群を列挙し、
コンタクト Machine（`apps/contact/`）と同じ原理 —「方程式を Bada で数値評価 → 残差で判定 →
成立した式を輸送機の部品に割り当てる」— で解析して、3 分の動画を生成します。
（explorerfiles_-____.pdf は以前の explorerfiles.pdf とバイト単位で同一でした。）

```
cd bada_webos
python3 cli.py contact --system-transport          # + system_transport_video.{html,mp4}
python3 -m contact.st_video generated/st            # 同じ（出力先指定）
python3 -m unittest tests.test_system_transport     # 15 テスト（Bada の判定を Python で照合）
```

生成例: `examples/system_transport_video.mp4`（3 分 05 秒、1280×720、30 fps）と、
シーク可能な HTML プレーヤー `examples/system_transport_video.html`。

## 判定の原理

| 判定 | 意味 |
|:--|:--|
| VERIFIED | Bada の数値計算で残差が許容誤差未満 |
| CONDITIONAL | 特定の領域・特殊点でのみ成立（Bada がその領域を見つける） |
| NOT VERIFIED | Bada が反例を計算した |

判定文字列は手で書かず、`lib/eqgroup.bada` の残差から計算されます。
結果: **VERIFIED 19 / CONDITIONAL 3 / NOT VERIFIED 3**。

## 列挙と解析（Bada の実出力）

ST = system_transport, QC = quantum_computer4, CA = caostics, IDPD = port directory。

| # | 出典 | 方程式 | Bada の計算 | 判定 | 部品 |
|:--|:--|:--|:--|:--|:--|
| E01 | ST p.9,13,15 | β(p,q) = Γ(p)Γ(q)/Γ(p+q) | p=2.5,q=1.5: ∫ = 0.1963495408493539 , ΓΓ/Γ = 0.19634954084936548 , Δ = 1.16e-14 | **VERIFIED** | gimbal ring radii r_k |
| E02 | QC p.4 | Γ'(s) = ∫₀^∞ e^{−x} x^{s−1} log x dx | Γ'(1) = -0.5772156649015446 (= −γ_Euler) , finite-diff Δ = 5.84e-11 | **VERIFIED** | — |
| E03 | QC p.3,6 | e^{iθ} = cos θ + i sin θ | θ=2.2 via Taylor series: Δ = 7.85e-16 | **VERIFIED** | ring phases |
| E04 | QC p.6 | sin(ix) = (e^{−x} + e^{x}) / 2i | stated form Δ = 3.669 ; corrected (e^{−x} − e^{x})/2i = i sinh x : Δ = 1.11e-15 | **NOT VERIFIED** | — (corrected form only) |
| E05 | ST p.3, QC p.7 | x + y ≥ 2√(xy) | 1600-point grid: min(x + y − 2√xy) = 0 (equality at x = y) | **VERIFIED** | — |
| E06 | ST p.7,10 | ∂g/∂t = −2 Ric   (round S³:  r² = r₀² − 4t) | RK4 r(11) = 2.2360679757287247 vs √(49−44) , Δ = 1.77e-9 ; extinction T = 12.25 | **VERIFIED** | Ricci sphere (S²×R port) |
| E07 | ST p.11 | L_p = √(ħG/c³) | L_p = 1.61625502392855 × 10⁻³⁵ m (CODATA 1.616255) , rel Δ = 1.48e-8 | **VERIFIED** | — (scale reference) |
| E08 | ST p.9 | ds² = g_μν dx^μ dx^ν + φ²(dy + κA_μ dx^μ)² | compact circle φ=2.5: ∮ = 15.707963267948776 = 2πφ , Δ = 1.9e-13 | **VERIFIED** | Kaluza-Klein torus |
| E09 | ST p.1,2,13 | \|\|ds²\|\| = e^{−2πT\|ψ\|}[η_μν + h_μν]dx^μdx^ν + T²dψ² | e^{−π} = 0.043213918263772196 , e^{−2π} = 0.001867442731707984 (port table) , Δ = 3.62e-11 | **VERIFIED** | AdS5 throat |
| E10 | ST p.9,15 | n(u = 2π) · n(u = 0) = −1  (non-orientable) | normal after one loop · start = -0.9999999999999998 | **VERIFIED** | Moebius band (H3 port) |
| E11 | ST p.1,2,12,98 | h(e^{αu} q) = h(q) ,  h(q) = q̄ u q | 180 fibre points: max \|Δh\| = 1.09e-14 | **VERIFIED** | Hopf fibres (S3 port) |
| E12 | ST p.13 | β⁵ = (βθ)² = θ³ | quaternion rep: all = −1 (Δ = 8.33e-17) ; ⟨β,θ⟩ has 120 elements, 720 edges = 600-cell | **VERIFIED** | 600-cell (Poincaré sphere π₁) |
| E13 | ST p.2,10 | X = Σ(−1)^k #(k-simplices of a₀a₁a₂a₃) ,  χ(3) = 2 | solid tetrahedron χ = 1 ; its boundary S² χ = 2 → χ = 2 holds for the boundary only | **CONDITIONAL** | tetrahedron (Nil port) |
| E14 | QC p.5 | Â(t) = e^{iĤt} Â e^{−iĤt} ,  dÂ/dt = (1/i)[Â, Ĥ] | Ĥ = σ_z, Â = σ_x : max \|dÂ/dt − (1/i)[Â,Ĥ]\| = 1.67e-10 | **VERIFIED** | Bloch precession (SL2 port) |
| E15 | ST p.5 | f(r) = ¼ \|r\|² | 5-point Laplacian Δf = 1 , Δ = 2.33e-12 (derivation in the report not reproduced) | **VERIFIED** | gravity-well paraboloid (H2×R) |
| E16 | ST p.3,5,6 | x^{1/2 + iy} = e^{x log x} | \|·\| equal only at x ∈ [0.5, 1] ; x = 2, y = 0 : \|√2 − 4\| = 2.586 | **CONDITIONAL** | — |
| E17 | ST p.2,11,98,100 | log(x log x) ≥ 2 (y log y)^{1/2} | holds on 160 / 3600 grid points (y near 1) ; on y = x : 0 / 60 | **CONDITIONAL** | — |
| E18 | ST p.2,26 QC p.3 CA p.3 | ∫∫ 1/(x log x)² dx^m = 1/2i | real ∫_e^∞ dx/(x log x)² = E₂(1) = 0.14849532283654865 ; \|value − 1/2i\| = 0.522 | **NOT VERIFIED** | — |
| E19 | IDPD, QC | ζ(s) = Π_p 1/(1 − p^{−s}) | s = 2, 430 primes: 1.6448731005410586 vs π²/6 , Δ = 6.1e-5 (tail < 2/3000) | **VERIFIED** | cross-check of the ζ used by the curve |
| E20 | IDPD | ζ(½ + iγ_n) = 0 ,  n = 1..10 | Euler-Maclaurin (N=40, 8 Bernoulli): max \|ζ\| = 1.05e-10 | **VERIFIED** | zero markers on the curve |
| E21 | ST p.26 (UFO) | γ = 18 h / 1 s ,  γ²(1 − β)(1 + β) = 1 | γ = 64800 , φ = arccosh γ = 11.772 , invariant = 1 | **VERIFIED** | clocks + spin budget φ |
| E22 | explorer (Jones 4 patterns) | V(t) = t + t³ − t⁴ ,  ω_k = \|V(e^{ikπ/2})\| | repo jones.bada: V = [[1, 1], [3, 1], [4, -1]] ; ω = 1 : 3 : 1 , Δ = 0 | **VERIFIED** | ring spin ratios |
| E23 | CA p.1 | ∫∫ e^{−x²−y²} dx dy = π | quadrature = 3.141592653589794 , Δ = 8.88e-16 | **VERIFIED** | Gaussian bell (E3 port) |
| E24 | CA p.2,4 | π^e = e^π | π^e = 22.459 , e^π = 23.141 , differ by 0.682 | **NOT VERIFIED** | — |
| E25 | CA p.1,2 | cos(ix log x) − i sin(ix log x) = e^{x log x} = x^x | x = 1.7: series = 2.4646948994848694 = 1.7^1.7 , Δ = 4.44e-16 | **VERIFIED** | — |

## 輸送機の構成

中央にコンタクト Machine の中核（3 本のジンバルリング・ポッド・ガントリー）と、
AdS5 スロート（E09）、カルツァ・クライン円環（E08）。その周囲、半径 62 m の円上に
8 つの Thurston ポート（IDPD）を置き、各ポートに 1 つの部品を配置しました
（ポートと部品の対応は主題的な割り当てです）:

| ポート | 部品 | 元の式 |
|:--|:--|:--|
| E3 | ガウス積分の鐘 | E23 |
| S3 | ホップ・ファイバー 12 本 + 600 胞体（120 頂点・720 辺） | E11, E12 |
| H3 | メビウスの帯 + 一周で反転する法線 | E10 |
| S²×R | リッチ流で縮む球 | E06 |
| H²×R | 重力井戸 f = r²/4 | E15 |
| SL2 | ブロッホ球 + ハイゼンベルク歳差 | E14 |
| Nil | 四面体 a₀a₁a₂a₃ | E13 |
| Sol | ゼータ曲線 ζ(½+it) と零点 10 個 | E19, E20 |

起動シーンでは 600 胞体が左等傾回転 e^{αu} で**自分自身のホップ・ファイバーに沿って**動きます
（u は位数 10 の元 β の軸なので、12 本のファイバーはちょうど 600 胞体の十角形です）。

## 動画の構成（3 分 05 秒）

| 時刻 | 場面 |
|:--|:--|
| 0–5 s | タイトル |
| 5–17 s | I. 列挙：25 式が出典つきで並び、判定が押されていく |
| 17–107 s | II. 解析：1 式 3.6 秒。式のタイプ → Bada の計算値 → 判定スタンプ → 部品 |
| 107–155 s | III. 構築：20 部品を一筆ずつ描画。カメラが各ポートへ外側から寄る |
| 155–178 s | IV. 起動：リング回転・ポッド落下・600 胞体の回転・リッチ流・歳差・ζ 走査、地球 1 秒 ↔ ポッド 18 時間 |
| 178–185 s | 完成：判定の集計 |

181 フレームの全頂点を Bada が計算し（約 66 秒）、プレーヤーはフレーム間を線形補間して
30 fps で描画します。MP4 は `contact/record_video.js`（Playwright + ffmpeg）で記録します。

## 正直な注記

- 数値はすべて検証済みですが、「これで次元輸送ができる」という物理的解釈はレポートの仮説であり、
  確立した物理ではありません。これはデザイン・フィクションです。
- 多くの式はレポート中で表記が崩れていたり意味が曖昧だったりするため、**検証可能な形に読み替えて**
  評価しています（例: E06 は丸い S³ 上のリッチ流、E11 はホップ・ファイバー、E13 は四面体の単体数）。
  読み替えの内容は表の「Bada の計算」欄に明記しています。
- NOT VERIFIED の 3 式（E04 sin(ix) の符号、E18 実数の積分 = 虚数、E24 π^e = e^π）は部品に使っていません
  （E04 は訂正形のみ確認）。CONDITIONAL のうち部品にしたのは E13 だけで、成立する側
  （四面体の境界 S² で χ = 2）に限って使っています。E16・E17 は部品にしていません。
