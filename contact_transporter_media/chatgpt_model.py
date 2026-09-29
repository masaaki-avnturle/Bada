"""ChatGPT (GPT 系 Transformer) の設計図モデル — 部品 ↔ 方程式 と 3D 形状.

ChatGPT 実機の内部構成は非公開のため、寸法は GPT-3 論文 (Brown et al., 2020) の公開値を参照した
図解用のモデルである。表示する層は 96 層のうち代表 8 層。
"""
import zlib

import numpy as np

HP = dict(n_layer=96, d_model=12288, n_head=96, d_head=128, d_ff=4 * 12288, n_ctx=2048,
          n_vocab=50257, params="175B")

N_SHOWN = 8
Z0 = 12.0
DZ = 14.0
LIM = 100

COL = {
    "tok": "#4fd6e0", "emb": "#7fb2ff", "ln": "#b8c7e0", "attn": "#f5b942", "mh": "#ffd166",
    "ffn": "#c28bff", "res": "#ffffff", "unemb": "#ff6b5b", "soft": "#ffa040", "rlhf": "#9fe8ff",
}

# 部品: key, 名称, 色, 方程式 (mathtext), 寸法/備考
PARTS = [
    ("tok", "トークナイザ (BPE)", "tok",
     [r"$(a,b)^* = \arg\max_{(a,b)}\ \mathrm{count}(a\,b)$ を反復併合",
      r"語彙 $|V| = 50257$"], "文字列 → トークン列 $t_1 \ldots t_n$"),
    ("emb", "埋め込み", "emb",
     [r"$x_i^{(0)} = W_E[t_i] + W_P[i]$",
      r"$W_E \in \mathbb{R}^{|V| \times d},\ d = 12288$"], "文脈長 2048"),
    ("ln", "層正規化", "ln",
     [r"$\mathrm{LN}(x) = \gamma \odot \frac{x-\mu}{\sqrt{\sigma^2+\epsilon}} + \beta$"],
     "各ブロックに 2 枚 (Pre-LN)"),
    ("attn", "自己注意 (ヘッド)", "attn",
     [r"$\mathrm{Attn}(Q,K,V) = \mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)V$",
      r"$Q = XW_Q,\ K = XW_K,\ V = XW_V,\ M_{ij} = -\infty\ (j>i)$"], "d_k = 128"),
    ("mh", "多頭結合", "mh",
     [r"$\mathrm{MH}(X) = [\mathrm{head}_1;\ldots;\mathrm{head}_{96}]\,W_O$"], "96 ヘッド"),
    ("ffn", "フィードフォワード", "ffn",
     [r"$\mathrm{FFN}(x) = \mathrm{GELU}(xW_1+b_1)W_2+b_2$",
      r"$\mathrm{GELU}(x) = x\,\Phi(x),\ \ d_{ff} = 4d = 49152$"], ""),
    ("res", "残差ストリーム", "res",
     [r"$h \leftarrow h + \mathrm{MH}(\mathrm{LN}(h))$",
      r"$h \leftarrow h + \mathrm{FFN}(\mathrm{LN}(h))$  (×96 層)"], ""),
    ("unemb", "出力層 (softmax)", "unemb",
     [r"$p(t_{n+1}\mid t_{\leq n}) = \mathrm{softmax}(W_U\,\mathrm{LN}(h_L)/T)$"],
     "温度 T でサンプリング"),
    ("loss", "事前学習の損失", "soft",
     [r"$\mathcal{L} = -\sum_i \log p_\theta(t_i \mid t_{<i})$"], "次トークン予測"),
    ("rlhf", "RLHF ループ", "rlhf",
     [r"$\mathcal{L}_{RM} = -\log\sigma\left(r(x,y_w) - r(x,y_l)\right)$",
      r"$\max_\pi\ \mathbb{E}[r(x,y)] - \beta\,\mathrm{KL}(\pi\,\|\,\pi_{ref})$"], "人間の選好で整列"),
]
PART_NAME = {k: n for k, n, *_ in PARTS}
ASSEMBLY_ORDER = ["tok", "emb", "res", "ln", "attn", "mh", "ffn", "unemb", "loss", "rlhf"]


# ---- 幾何 -----------------------------------------------------------------
def box(cx, cy, cz, sx, sy, sz):
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz, cz + sz
    b = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z0]])
    t = b.copy()
    t[:, 2] = z1
    L = [b, t]
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        L.append(np.array([[x, y, z0], [x, y, z1]]))
    return L


def plate(cz, s):
    return box(0, 0, cz, s, s, 0.01)[:1]


def circle(R, z, n=90, cx=0, cy=0):
    t = np.linspace(0, 2 * np.pi, n)
    return np.c_[cx + R * np.cos(t), cy + R * np.sin(t), np.full_like(t, z)]


def block_z(l):
    return Z0 + DZ * l


def heads_pos(n=12, R=26):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / 12
    return np.c_[R * np.cos(a), R * np.sin(a)]


def geometry():
    g = {k: [] for k, *_ in PARTS}
    # トークナイザ: 床のタイル
    for v in np.linspace(-50, 50, 11):
        g["tok"].append(np.array([[v, -50, -20], [v, 50, -20]]))
        g["tok"].append(np.array([[-50, v, -20], [50, v, -20]]))
    # 埋め込み行列: 箱 + 列
    g["emb"] += box(0, 0, -8, 80, 80, 10)
    for v in np.linspace(-36, 36, 9):
        g["emb"].append(np.array([[v, -40, 2], [v, 40, 2]]))
    top = block_z(N_SHOWN)
    for l in range(N_SHOWN):
        z = block_z(l)
        g["ln"] += plate(z, 72)
        g["ln"] += plate(z + 7, 72)
        for hx, hy in heads_pos():
            g["attn"].append(circle(3, z + 1, 24, hx, hy))
            g["attn"].append(circle(3, z + 5, 24, hx, hy))
            g["attn"].append(np.array([[hx + 3, hy, z + 1], [hx + 3, hy, z + 5]]))
            g["attn"].append(np.array([[hx - 3, hy, z + 1], [hx - 3, hy, z + 5]]))
        g["mh"].append(circle(26, z + 6, 120))
        g["ffn"] += box(0, 0, z + 8, 62, 62, 4)
        for v in np.linspace(-28, 28, 8):
            g["ffn"].append(np.array([[v, -31, z + 12], [v, 31, z + 12]]))
    # 残差ストリーム: 中心軸と四隅の柱
    g["res"].append(np.array([[0, 0, 2], [0, 0, top + 4]]))
    for x, y in ((-36, -36), (36, -36), (36, 36), (-36, 36)):
        g["res"].append(np.array([[x, y, 2], [x, y, top]]))
    # 出力層: 逆ピラミッド + 語彙の扇
    apex = np.array([0, 0, top + 2])
    sq = np.array([[-45, -45], [45, -45], [45, 45], [-45, 45], [-45, -45]])
    rim = np.c_[sq, np.full(5, top + 22)]
    g["unemb"].append(rim)
    for p in rim[:4]:
        g["unemb"].append(np.array([apex, p]))
    # 損失: 出力上の確率バー (教師トークンとの比較)
    for i, h in enumerate([10, 4, 3, 2, 1.5, 1, 0.8]):
        x = -30 + i * 10
        g["loss"].append(np.array([[x, 0, top + 24], [x, 0, top + 24 + h * 2]]))
    # RLHF: 塔を囲む縦の環 (報酬の帰還路) + 2 本の帰還矢
    t = np.linspace(0.15 * np.pi, 1.85 * np.pi, 200)
    R = 88
    zc = (top + 22 - 20) / 2
    g["rlhf"].append(np.c_[R * np.cos(t + np.pi / 2) * 0 + R * np.sin(t), np.zeros_like(t),
                           zc + 1.05 * R * np.cos(t)])
    g["rlhf"].append(np.c_[np.zeros_like(t), R * np.sin(t), zc + 1.05 * R * np.cos(t)])
    return g


COLOR_OF = {k: COL[c] for k, _, c, *_ in PARTS}


# ---- 利用シーン用: 小型 Transformer の実計算 --------------------------------
PROMPT = ["コンタクト", "の", "輸送", "機", "の", "設計", "図", "を", "描い", "て"]
GEN = [
    ("外環", ["外環", "ポッド", "塔", "中環", "扉"], [4.1, 2.3, 1.9, 1.5, 0.7]),
    (" R", [" R", " 半径", " =", " は", "、"], [3.6, 2.2, 1.4, 1.2, 0.9]),
    (" =", [" =", " ≈", " :", " は", " 約"], [4.4, 1.6, 1.2, 1.0, 0.8]),
    (" 60", [" 60", " 47", " 70", " 37", " 132"], [3.9, 2.0, 1.8, 1.4, 1.0]),
    (".088", [".088", ".1", ".0", ".09", ".08"], [3.7, 2.1, 1.5, 1.3, 1.1]),
    (" m", [" m", " メートル", "、", " [m]", "。"], [4.0, 2.4, 1.6, 1.2, 1.0]),
    ("、ポッド", ["、ポッド", "、中環", "、塔", "。", "、扉"], [3.3, 3.0, 1.9, 1.2, 0.9]),
    (" r = 5.021 m", [" r = 5.021 m", " r = 5 m", " 半径", " 直径", " r"], [3.5, 2.2, 1.6, 1.1, 0.9]),
]
TEMP = 0.8


def softmax(z, T=1.0):
    z = np.asarray(z, float) / T
    e = np.exp(z - z.max())
    return e / e.sum()


def tiny_attention(tokens, n_layer=N_SHOWN, d=16):
    """ランダム初期化の小型モデルで softmax(QK^T/√d + M) を実計算する (図解用)."""
    n = len(tokens)
    X = np.stack([np.random.default_rng(zlib.crc32(t.encode())).standard_normal(d) for t in tokens])
    pos = np.arange(n)[:, None] / (10000 ** (np.arange(d)[None, :] / d))
    X = X + np.where(np.arange(d) % 2 == 0, np.sin(pos), np.cos(pos))
    mats = []
    mask = np.triu(np.full((n, n), -np.inf), 1)
    for l in range(n_layer):
        r = np.random.default_rng(100 + l)
        Wq, Wk, Wv = (r.standard_normal((d, d)) / np.sqrt(d) for _ in range(3))
        Q, K, V = X @ Wq, X @ Wk, X @ Wv
        S = Q @ K.T / np.sqrt(d) + mask
        A = np.exp(S - S.max(1, keepdims=True))
        A /= A.sum(1, keepdims=True)
        mats.append(A)
        X = X + A @ V
        X = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-5)
    return mats


ATTN = tiny_attention(PROMPT)
