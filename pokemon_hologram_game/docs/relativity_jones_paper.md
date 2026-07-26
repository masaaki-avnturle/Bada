# 透過ホログラフィー式獣ARにおける特殊相対性理論とJones多項式
### 光円錐上の光線場結像と、世界線ブレイドの位相的分類

**山口フレームワーク / Bada言語（Omega方言）技術報告**
*Special Relativity and the Jones Polynomial in a See-through Holographic Creature-AR System*

---

## 要旨 (Abstract)

本稿は、Bada言語（Omega方言）で実装した透過ホログラフィー式獣ARゲーム
（`pokemon_hologram_game/`）の技術基盤を、二つの理論の合流として定式化する。
第一に**特殊相対性理論**は、ホログラフィーディスプレイが再構成する「光線場（light field）」を
**光円錐上のヌル測地線の合同族**として、また平行感覚（傾き）センサを**局所ローレンツ標構
（tetrad）の姿勢**として与える。デバイスを傾ける操作はローレンツ群 $SO(3,1)$ の回転部分群
$SO(3)$ の作用であり、視差はヌル方向の**光行差変換**として現れる。第二に**Jones多項式**は、
$(2{+}1)$ 次元時空において式獣（キャラクター）の**世界線が編み込まれた結び目・絡み目**の
位相不変量として、召喚・戦闘の相互作用を分類する。両者は Witten の Chern–Simons
位相的場の理論（TQFT）を通じて同一の時空の上で結ばれ、実装上は有効作用量子 $\hbar_\text{eff}$ と
$\pi$-softmax 正規化（Markov トレースの類似）によって接続される。各節は実際のソース
モジュール（`caustics_field.om`, `tilt_balance.om`, `battle_system.om` ほか）へ対応づける。

**キーワード:** 特殊相対性理論, 光円錐, 光線場, コースティクス, 光行差, Jones多項式,
Kauffman ブラケット, ブレイド群, Chern–Simons TQFT, エニオン, TupleSpace

---

## 1. 序論

ホログラフィーとは畢竟「**光の場（電磁波）を、その位相まで含めて再構成する**」技術である。
電磁波は光速 $c$ で伝播する質量ゼロの場であり、その運動学は本質的に特殊相対論的である。
したがって、空中結像で式獣を描く本システムの物理層は、はじめから相対論の言語で書くのが自然
である（第2–3章）。

一方、複数の式獣が空間中を運動し、互いに絡み合いながら戦うという**動的な相互作用**は、
時間を一軸に加えた $(2{+}1)$ 次元時空では**世界線の編み込み（braiding）**として表れる。
編み込まれた曲線族の同値類を数え上げる普遍的な不変量が **Jones多項式** $V_L(t)$ であり、
本リポジトリの Omega 実装（`src/omegascript_Jonesequation.txt`, `Jones_manifold_from_omegascript.txt`）
は、まさに結び目の同値類判定にこれを用いている（第4章）。

第5章で両理論が Chern–Simons TQFT の下で一つの時空幾何に統合されることを示し、
第6章で実装モジュールへの対応表を与える。

---

## 2. 特殊相対性理論 I —— 光線場と光円錐

### 2.1 ヌル測地線としての光線

計量を $\eta_{\mu\nu}=\mathrm{diag}(-1,+1,+1,+1)$、座標を $x^\mu=(ct,\mathbf{x})$ とする。
ホログラムが再構成する各光線は、時空の**ヌル（光的）世界線**

$$
ds^2 = \eta_{\mu\nu}\,dx^\mu dx^\nu = -c^2 dt^2 + d\mathbf{x}^2 = 0
$$

に沿う。すなわち再構成すべき対象は、点の集合ではなく**光円錐上の測地線の合同族（congruence）**
である。ディスプレイの各ボクセル `Voxel{x,y,z,...}` は、この合同族が観測者面と交わる断面に他ならない。

### 2.2 位相はローレンツ・スカラー

平面波 $\exp(i\phi)$ の位相は四元波数 $k^\mu=(\omega/c,\mathbf{k})$ を用いて

$$
\phi = k_\mu x^\mu = \mathbf{k}\!\cdot\!\mathbf{x} - \omega t,
\qquad k_\mu k^\mu = -\frac{\omega^2}{c^2}+|\mathbf{k}|^2 = 0 \ \ (\text{光は質量ゼロ})
$$

と書ける。**$\phi$ はローレンツ不変**（スカラー）であり、$k_\mu k^\mu=0$ という光円錐条件は
どの慣性系でも保たれる。これが、干渉縞（位相）で像を刻むホログラフィーが観測者の運動状態に
依らず整合する根拠である。

> **実装対応 —** `caustics_field.om` の `wavefrontPhase(layer, depth)`
> $\displaystyle \phi=\frac{2\pi\,\ell}{N}$ は、この不変位相 $\phi=k_\mu x^\mu$ を奥行きレイヤ $\ell$
> について離散化したものである。位相がスカラーであるがゆえに、レイヤ位相の設定は標構に依らない。

### 2.3 コースティクス = ヌル測地線の共役点

隣接する光線が交差し光線密度が発散する場所が**コースティクス**である。相対論的には、
ヌル測地線合同の**膨張率** $\theta$ が発散する**共役点（focal point）**に対応し、
Raychaudhuri 方程式

$$
\frac{d\theta}{d\lambda} = -\frac{1}{2}\theta^2 - \sigma_{\mu\nu}\sigma^{\mu\nu} + \omega_{\mu\nu}\omega^{\mu\nu} - R_{\mu\nu}k^\mu k^\nu
$$

が焦線の生成を支配する。幾何光学の強度則

$$
I(\mathbf{x}) \;=\; \left|\det \frac{\partial^2 \Phi}{\partial x^i \partial x^j}\right|^{-1}
$$

（波面 $\Phi$ のヘッシアン＝ヤコビアンの逆）は、共役点で $\det(\cdot)\to 0$、すなわち $I\to\infty$
となって明線（式獣の輪郭光）を描く。

> **実装対応 —** `caustics_field.om` の
> `causticIntensity(curvature)` は $I=|\partial^2\Phi/\partial x^2|^{-1}$ を実装し、焦線での発散を
> $\varepsilon=10^{-6}$ でクランプ、さらに $\hbar_\text{eff}$ の $\pi$-softmax
> $\;\sigma(u)=\dfrac{e^{u\hbar_\text{eff}\pi}}{1+e^{u\hbar_\text{eff}\pi}}$ で有界化する。
> `waveCurvature` は $\partial^2\Phi$ の差分近似 $\Phi_{\ell+1}-2\Phi_\ell+\Phi_{\ell-1}$ である。

---

## 3. 特殊相対性理論 II —— 平行感覚センサと局所ローレンツ標構

### 3.1 デバイス標構は tetrad（vierbein）

平行感覚（傾き）センサが定めるのは、デバイスに固定された正規直交標構
$\{e_{\hat a}{}^\mu\}_{\hat a=0,1,2,3}$（tetrad）である。加速度計が読む重力／慣性ベクトルは、
等価原理により標構の**時間的（timelike）軸** $e_{\hat 0}$ を与える。

$$
g_{\mu\nu}\,e_{\hat a}{}^\mu e_{\hat b}{}^\nu = \eta_{\hat a\hat b}.
$$

> **実装対応 —** `tilt_balance.om` の `readIMU()` は加速度ベクトル $\mathbf a$ から
> $\text{pitch}=\operatorname{atan2}(a_y,\sqrt{a_x^2+a_z^2})$,
> $\text{roll}=\operatorname{atan2}(-a_x,a_z)$ を得る。これは重力（$e_{\hat 0}$ 方向）に対する
> 標構の姿勢角の抽出そのものである。`calibrate()` のゼロ点校正は基準標構の選択に当たる。

### 3.2 傾け操作 = ローレンツ群の回転部分群

デバイスを傾ける操作は、時間軸を保つ**空間回転** $R\in SO(3)\subset SO(3,1)$ である。
ローレンツ変換 $\Lambda$ の一般形は回転とブースト $B(\boldsymbol\beta)$ の合成 $\Lambda=B\,R$ で、
低速の手持ち運動では回転が主、並進速度 $\boldsymbol\beta=\mathbf v/c$ の寄与が視差として現れる。

$$
k'^{\hat a} = \Lambda^{\hat a}{}_{\hat b}\,k^{\hat b},\qquad
\Lambda = B(\boldsymbol\beta)\,R(\text{pitch},\text{roll},\text{yaw}).
$$

### 3.3 視差 = ヌル方向の光行差

光線のヌル方向 $\hat{\mathbf n}$ は、標構が速度 $\boldsymbol\beta$ で運動すると**光行差
（aberration）**により方向を変える：

$$
\cos\theta' = \frac{\cos\theta - \beta}{1-\beta\cos\theta},
\qquad
\tan\frac{\theta'}{2} = \sqrt{\frac{1+\beta}{1-\beta}}\;\tan\frac{\theta}{2}.
$$

観測者面上での像のずれ（視差 parallax）は、この方向変換の $O(\beta)$ 近似
$\delta\theta \approx -\beta\sin\theta$ に一致する。すなわち「傾け・動かすとマスコットが
ずれて見える」という体験は、ヌル方向の相対論的変換の非相対論極限である。

> **実装対応 —** `tilt_balance.om` の `applyToPose(base, tilt)` は、標構の傾き
> $(\text{pitch},\text{roll},\text{yaw})$ を式獣の姿勢へ回転として与え（$SO(3)$ 部分）、
> 視差項 $t_x = \sin(\text{roll})\cdot p$, $t_y=-\sin(\text{pitch})\cdot p$ で $O(\beta)$ の
> 光行差ずれを近似する。奥行き $t_z=-\text{pitch}\cdot 0.5$ は前傾で像面が手前へ寄る効果。
> `caustics_field.om` の `Renderer.transform` はこの姿勢を各光点へ適用する回転行列である。

---

## 4. Jones多項式 —— 世界線ブレイドの位相的分類

### 4.1 なぜ結び目か：$(2{+}1)$ 次元時空の世界線

空間 2 次元＋時間 1 次元の時空 $\mathbb{R}^{2,1}$ を考える。$n$ 体の式獣の位置は時間発展に伴い
$n$ 本の**世界線** $\{\gamma_i(t)\}$ を描く。粒子が互いに位置を交換しながら運動すると、世界線は
**ブレイド群** $B_n$ の元 $\beta$ として編み込まれ、時間方向に閉じる（Markov 閉包）ことで
**絡み目** $\hat\beta$ を成す。二つの絡み目が同位（ambient isotopy）であることと、
それらが同じ物理的相互作用の同値類に属することは等価である。

### 4.2 Kauffman ブラケットと Jones多項式

各交差（crossing）に対し**スケイン関係式**を課す。Kauffman ブラケット $\langle L\rangle$ は

$$
\big\langle\, \text{（交差）} \,\big\rangle
= A\,\big\langle\, )(\ \big\rangle + A^{-1}\big\langle\, \asymp\ \big\rangle,
\qquad
\langle \bigcirc \rangle = 1,\quad
\langle L \sqcup \bigcirc\rangle = (-A^2 - A^{-2})\langle L\rangle,
$$

で定まり、書き数 $w(L)$ による正規化を経て **Jones多項式**

$$
V_L(t) = \big(-A^{3}\big)^{-w(L)}\,\langle L\rangle \Big|_{A = t^{-1/4}}
$$

を得る。等価な形は**スケイン関係式**

$$
t^{-1}\,V_{L_+}(t) \;-\; t\,V_{L_-}(t) \;=\; \big(t^{1/2}-t^{-1/2}\big)\,V_{L_0}(t),
\qquad V_{\bigcirc}=1.
$$

$V_L(t)$ は絡み目の**位相不変量**であり、異なる絡み目（異なる相互作用の履歴）を判別する。

> **実装対応 —** `src/omegascript_Jonesequation.txt` の `jones_polynomial(knot)` は各交差の符号
> $\text{sign}\in\{+1,-1\}$ を走査してブラケットを更新する Omega 実装であり、
> `is_knot_valid?` は $V_L\neq 0$ による同値類判定を行う。`Jones_manifold_from_omegascript.txt`
> は $V_L$ を「ガンマ関数による大域的部分積分多様体」へ変換する枠組みを与える。

### 4.3 ブレイド群・Temperley–Lieb 代数・Markov トレース

Jones の原構成では、ブレイド群 $B_n$ の生成子 $\sigma_i$ が Temperley–Lieb 代数 $TL_n(\delta)$
（$\delta = -A^2-A^{-2}$、$e_i^2=\delta e_i$）へ表現され、**Markov トレース** $\mathrm{tr}$ によって

$$
V_{\hat\beta}(t) \;\propto\; \big(-A^3\big)^{-w}\,\mathrm{tr}\!\big(\rho(\beta)\big)
$$

と与えられる。トレースは全経路にわたる正規化された和であり、**$\pi$-softmax 正規化**
（分配関数 $Z=\sum_i e^{s_i \hbar_\text{eff}\pi}$ による確率化）はこの Markov トレースの
指数重み和と同型の役割を果たす。

> **実装対応 —** `passthrough_scene.om` / `caustics_field.om` の `piSoftmax`
> $\;p_i = e^{s_i\hbar_\text{eff}\pi}/\sum_j e^{s_j\hbar_\text{eff}\pi}\;$ は、状態和の正規化＝
> Markov トレースの規格化に相当する。式獣の属性同値類（`Element` と `Omega::DATABASE` 図鑑）
> は、この不変量が定める超選択則（superselection sector）に対応する。

### 4.4 戦闘＝スケイン操作

`battle_system.om` の 1 ターンは、味方と敵の 2 本の世界線に 1 個の交差を挿入する操作である。
相性倍率 `typeMultiplier(atk, def)` は交差の符号と重みを与える局所スケイン係数と見なせ、
決着（一方の $\gamma_i$ が消える＝結び目が解ける）までの履歴が絡み目 $\hat\beta$ を定める。
その $V_{\hat\beta}(t)$ が、その戦闘が属する同値類（＝物語上の「意味のある勝敗」）を刻印する。

---

## 5. 統合 —— Chern–Simons TQFT が二理論を結ぶ

Witten (1989) は、Jones多項式が $(2{+}1)$ 次元 **Chern–Simons 位相的場の理論**の
Wilson ループ期待値として得られることを示した：

$$
Z = \int \mathcal{D}A\;\exp\!\left(\frac{ik}{4\pi}\int_M \mathrm{Tr}\Big(A\wedge dA + \tfrac{2}{3}A\wedge A\wedge A\Big)\right),
\qquad
V_L = \Big\langle \textstyle\prod_i W_{R}(\gamma_i)\Big\rangle,
$$

$$
W_R(\gamma) = \mathrm{Tr}_R\,\mathcal{P}\exp\!\oint_\gamma A,
\qquad
t = \exp\!\left(\frac{2\pi i}{k+2}\right).
$$

ここに二つの理論が合流する。

1. **同じ時空。** Chern–Simons 作用は計量 $g_{\mu\nu}$ を含まず**一般共変（位相的）**である。
   これは特殊相対論的なローレンツ共変性よりさらに強く、第2–3章の光線場・標構が乗る
   $(2{+}1)$ 次元スライスと**同一の時空**の上に定義される。光錐（因果構造）は保たれつつ、
   観測量は距離に依らない**トポロジー**だけで決まる。

2. **同じ $\hbar$。** 準古典パラメータは $\hbar \sim 1/k$。ブレイド位相 $t=e^{2\pi i/(k+2)}$ は
   準古典極限 $k\to\infty$（$\hbar\to 0$）で自明化し、有限 $k$ で式獣は**エニオン**的な
   分数統計を帯びる。実装の $\hbar_\text{eff}$ は、この有効レベル $k$ を集光の鋭さ
   （コースティクス）とブレイド位相の双方に流し込む単一パラメータである。

3. **エニオンによる計算。** 世界線のブレイドは、エニオンのモノドロミー行列 $\rho(\sigma_i)$ を
   通じてユニタリ変換を実装する。式獣図鑑（`Omega::DATABASE` = アカシックレコード/TupleSpace）は
   このエニオン超選択則の格納庫であり、召喚とはある同値類の代表元を取り出す操作である。

したがって本システムは、**特殊相対論（光円錐・光線場・局所標構）が「見せる」層**を担い、
**Jones多項式（Chern–Simons）が「関係を分類する」層**を担う、二層構造として一貫して定式化される。
$\hbar_\text{eff}$ と $\pi$-softmax が両層を貫く連結子である。

---

## 6. 実装対応表

| 理論的対象 | 数式 | ソースモジュール / 関数 |
|:--|:--|:--|
| ヌル位相（不変） | $\phi=k_\mu x^\mu,\ k_\mu k^\mu=0$ | `caustics_field.om` `wavefrontPhase` |
| コースティクス強度 | $I=\lvert\partial^2\Phi/\partial x^2\rvert^{-1}$ | `caustics_field.om` `causticIntensity`, `waveCurvature` |
| 局所ローレンツ標構 | $g_{\mu\nu}e_{\hat a}{}^\mu e_{\hat b}{}^\nu=\eta_{\hat a\hat b}$ | `tilt_balance.om` `readIMU`, `calibrate` |
| ローレンツ回転 $SO(3)$ | $\Lambda=B\,R(\text{pitch,roll,yaw})$ | `tilt_balance.om` `applyToPose` / `caustics_field.om` `transform` |
| 光行差（視差） | $\cos\theta'=\frac{\cos\theta-\beta}{1-\beta\cos\theta}$ | `tilt_balance.om` 視差項 $t_x,t_y,t_z$ |
| 光線場結像 | ヌル測地線合同 | `hologram_display.om` `project`, `emitWaveguide`, `streamExternal` |
| Jones多項式 / スケイン | $t^{-1}V_{L_+}-tV_{L_-}=(t^{1/2}-t^{-1/2})V_{L_0}$ | `src/omegascript_Jonesequation.txt` `jones_polynomial` |
| Markov トレース ≅ $\pi$-softmax | $p_i=e^{s_i\hbar_\text{eff}\pi}/Z$ | `passthrough_scene.om` `piSoftmax` |
| ブレイド（戦闘） | $\beta\in B_n,\ \hat\beta$ 閉包 | `battle_system.om` `run`, `typeMultiplier` |
| エニオン超選択則 | $t=e^{2\pi i/(k+2)}$ | `shikijuu.om` `Element`, `Dex` + `Omega::DATABASE` |

---

## 7. 結論

透過ホログラフィー式獣ARの技術は、二つの理論の**役割分担**として最も明晰に理解される。
特殊相対性理論は、光速で伝わる電磁場を光円錐上のヌル測地線合同として扱い、コースティクスによる
空中結像（`caustics_field.om`）と、平行感覚センサが定める局所ローレンツ標構およびその傾け操作・
視差（`tilt_balance.om`）を、観測者の運動に依らず整合的に与える。Jones多項式は、$(2{+}1)$ 次元
時空における式獣世界線のブレイドを位相不変量として分類し、召喚・戦闘の相互作用に「意味のある
同値類」を与える（`battle_system.om`, `Omega::DATABASE` 図鑑）。両者は Witten の Chern–Simons
TQFT の下で同一時空上に統合され、有効作用量子 $\hbar_\text{eff}$ と $\pi$-softmax 正規化が、
集光の鋭さとブレイド位相を貫く単一の連結子として機能する。

---

## 参考文献

1. A. Einstein, *Zur Elektrodynamik bewegter Körper*, Ann. Phys. **17**, 891 (1905).
2. V. F. R. Jones, *A polynomial invariant for knots via von Neumann algebras*, Bull. AMS **12**, 103 (1985).
3. L. H. Kauffman, *State models and the Jones polynomial*, Topology **26**, 395 (1987).
4. E. Witten, *Quantum field theory and the Jones polynomial*, Commun. Math. Phys. **121**, 351 (1989).
5. A. Kitaev, *Fault-tolerant quantum computation by anyons*, Ann. Phys. **303**, 2 (2003).
6. M. Born & E. Wolf, *Principles of Optics*, 7th ed., Cambridge Univ. Press (1999) — coherence, caustics.
7. C. W. Misner, K. S. Thorne, J. A. Wheeler, *Gravitation*, Freeman (1973) — null congruences, Raychaudhuri.
8. 山口雅旭, *Bada言語 / Omega方言・TupleSpace アカシックレコード技術資料*, 本リポジトリ
   （`src/omegascript_Jonesequation.txt`, `Jones_manifold_from_omegascript.txt`, `README.md`）.

---

*© 2026 — Bada言語（Omega方言）ホログラフィーAR技術報告 / 山口フレームワーク*
