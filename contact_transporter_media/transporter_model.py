"""CONTACT TRANSPORTER — 設計図書 (contact_blueprint.pdf) の数値から 3D 形状を組み立てるモデル.

すべての寸法・角速度・共鳴角はレポートの Bada 実行結果に由来する。
形状は思索的・フィクションの可視化であり、工学的に検証された装置ではない。
"""
import json
import os

import numpy as np
import mpmath

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- レポート「1. 設計パラメータ」より ---------------------------------------
P = dict(
    sqrt_s_TeV=13.6, Et_miss_GeV=1348.29,
    n_hat=np.array([0.86964, -0.25101, 0.42511]),
    Gamma=64800.0, one_minus_beta=1.19075e-10, phi=11.772200,
    vega_ly=25.04, vega_contracted_km=3.656e9, one_way_h=3.3874,
    T_psi=1.763290, xlogx_root=1.763220,
    theta0=0.523599, omega=(0.10472, 0.39241, 1.47043), Omega_prec=3.70640,
    R_out=60.088, R_mid=47.431, R_in=37.440, tube=2.066,
    pod_r=5.021, tower_h=132.194, well_d=38.800,
    J31_R=70.269, J51_R=56.215,
)
# 再計算 (mpmath) — レポートの値と一致することを確認する
P["rs_theta"] = float(mpmath.siegeltheta(P["phi"]))  # -2.581360
P["rs_Z"] = float(mpmath.siegelz(P["phi"]))  # -1.334150

JONES = {
    "3_1": ({-4: -1, -3: 1, -1: 1}, "-t^{-4} + t^{-3} + t^{-1}"),
    "4_1": ({-2: 1, -1: -1, 0: 1, 1: -1, 2: 1}, "t^{-2} - t^{-1} + 1 - t + t^{2}"),
    "5_1": ({2: 1, 4: 1, 5: -1, 6: 1, 7: -1}, "t^{2} + t^{4} - t^{5} + t^{6} - t^{7}"),
}


def jones_eval(knot, t):
    return sum(c * t ** k for k, c in JONES[knot][0].items())


T_STAR = np.exp(1j * P["rs_theta"])
P["V_tstar"] = {k: complex(jones_eval(k, T_STAR)) for k in JONES}

# |V(e^{iα})| の極小 → 扉の共鳴窓の角度
ALPHA = np.linspace(0, 2 * np.pi, 3601)
VABS = {k: np.abs(jones_eval(k, np.exp(1j * ALPHA))) for k in JONES}


def local_minima(y):
    i = np.where((y[1:-1] < y[:-2]) & (y[1:-1] < y[2:]))[0] + 1
    return i


WINDOWS = []  # (knot, alpha_rad, |V|)
for k in JONES:
    for i in local_minima(VABS[k]):
        WINDOWS.append((k, ALPHA[i], VABS[k][i]))

# Riemann–Siegel Z(t) 曲線 (HUD / 図用)
ZT = np.linspace(0.5, 40, 500)
ZV = np.array([float(mpmath.siegelz(t)) for t in ZT])


# ---- 方程式レジストリ (レポート 4 章, 2111 本) -------------------------------
def load_registry():
    with open(os.path.join(HERE, "data", "equations.json"), encoding="utf-8") as f:
        return json.load(f)


# タグ → 部品 の割り当て (レポート 3 章「部品 (タグ) ごとの方程式数」に対応)
TAG_PART = {
    "ROT": "ring", "SR": "pod", "QUANTUM": "pod", "GAMMA": "tower", "BETA": "tower",
    "ZETA": "window", "JONES": "coil", "MANIFOLD": "well", "ENTROPY": "well",
    "TRANSPORT": "axis", "OTHER": "base",
}

PARTS = [
    # key, 名称, 色キー, 支配方程式 (レポート記載), 寸法の説明
    ("base", "基礎・床", "tower",
     ["□ = −(16πG/c⁴)·T_μν", "= κ·T_μν  (OTHER 群)"],
     "床面 z = −38.8 m"),
    ("well", "井戸 (輸送計量)", "well",
     [r"$ds^2 = e^{-2\pi T|\psi|}[\eta+\bar h]dx^\mu dx^\nu + T^2 d\psi^2$",
      r"$e^{-2\pi T|\psi|} = 1/\Gamma \;\Rightarrow\; T|\psi| = 1.76329$"],
     "深さ 38.800 m"),
    ("tower", "塔・ガントリー", "tower",
     [r"$\Gamma(s)=\int_0^\infty e^{-x}x^{s-1}dx$",
      r"$\theta(\varphi) = \arg\Gamma(\frac{1}{4}+\frac{i\varphi}{2}) - \frac{\varphi}{2}\log\pi = -2.58136$"],
     "塔高 132.194 m"),
    ("ring", "ジンバル環 ×3", "ring",
     [r"$\Theta = \theta + i\varphi,\;\; \theta_0 = 0.523599$",
      "ω (外, 中, 内) = 0.10472, 0.39241, 1.47043 rad/s"],
     "R = 60.088 / 47.431 / 37.440 m, 管径 2.066 m"),
    ("coil", "Jones コイル", "j31",
     [r"$V_{3_1} = -t^{-4}+t^{-3}+t^{-1}$,  $|V(t^*)|$ → R = 70.269",
      r"$V_{5_1} = t^2+t^4-t^5+t^6-t^7$,  R = 56.215 ; $4_1$ 床下"],
     "t* = e^(iθ(φ))"),
    ("window", "共鳴窓", "window",
     [r"$Z(\varphi) = e^{i\theta(\varphi)}\zeta(\frac{1}{2}+i\varphi) = -1.33415$",
      r"$\min_\alpha |V_K(e^{i\alpha})|$ → 窓の角度"],
     "極小 α から配置"),
    ("pod", "ポッド", "pod",
     [r"$\Gamma = 18\,\mathrm{h}/1\,\mathrm{s} = 64800,\;\varphi = \mathrm{arcosh}\,\Gamma = 11.7722$",
      r"$\Omega = Mgl/(I_3\omega_3) = 3.70640$ rad/s"],
     "r = 5.021 m"),
    ("axis", "扉の軸", "axis",
     [r"$\sqrt{s} = 13.6$ TeV,  $E_T^{miss} = 1348.29$ GeV",
      r"$\hat n = \vec p_T^{\,miss}/|\cdot| = (0.870, -0.251, 0.425)$"],
     "CERN 衝突で粒子が消えた方向"),
]
PART_NAME = {k: n for k, n, *_ in PARTS}

GROUND = -P["well_d"]


# ---- 幾何 -----------------------------------------------------------------
def circle(R, n=160, plane="xy"):
    t = np.linspace(0, 2 * np.pi, n)
    a, b = R * np.cos(t), R * np.sin(t)
    z = np.zeros_like(t)
    return {"xy": np.c_[a, b, z], "xz": np.c_[a, z, b], "yz": np.c_[z, a, b]}[plane]


def rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def ring_tube(R, r, plane, n=160, k=3):
    """管径 r の環を k 本の平行線で表す."""
    out = []
    for j in range(k):
        a = 2 * np.pi * j / k
        c = circle(R + r * np.cos(a), n, plane)
        off = {"xy": [0, 0, 1], "xz": [0, 1, 0], "yz": [1, 0, 0]}[plane]
        out.append(c + np.array(off) * r * np.sin(a))
    return out


def gimbal(t_rot, spin=1.0):
    """3 重ジンバル環. t_rot [s] 経過時の姿勢 (spin で角速度を倍率)."""
    w1, w2, w3 = (w * spin for w in P["omega"])
    R1 = rz(w1 * t_rot) @ rx(P["theta0"])
    R2 = R1 @ rx(w2 * t_rot)
    R3 = R2 @ ry(w3 * t_rot)
    rings = []
    for R, rad, plane in ((R1, P["R_out"], "xz"), (R2, P["R_mid"], "xy"), (R3, P["R_in"], "yz")):
        for c in ring_tube(rad, P["tube"], plane):
            rings.append(c @ R.T)
    return rings


def torus_knot(p, q, R, b, zc, n=700, zscale=1.0):
    t = np.linspace(0, 2 * np.pi, n)
    a = R - b
    r = a + b * np.cos(q * t)
    return np.c_[r * np.cos(p * t), r * np.sin(p * t), zc + zscale * b * np.sin(q * t)]


def fig8_knot(s, zc, n=500):
    t = np.linspace(0, 2 * np.pi, n)
    return np.c_[s * (2 + np.cos(2 * t)) * np.cos(3 * t), s * (2 + np.cos(2 * t)) * np.sin(3 * t),
                 zc + s * np.sin(4 * t)]


def coils():
    return {
        "j31": [torus_knot(2, 3, P["J31_R"], 12.0, 0.0)],
        "j51": [torus_knot(2, 5, P["J51_R"], 9.0, 70.0)],
        "j41": [fig8_knot(4.5, GROUND + 14.0)],
    }


def sphere(r, center, n_lat=7, n_lon=8):
    cx = np.asarray(center, float)
    out = []
    for la in np.linspace(-np.pi / 2, np.pi / 2, n_lat + 2)[1:-1]:
        c = circle(r * np.cos(la), 48)
        c[:, 2] = r * np.sin(la)
        out.append(c + cx)
    for lo in np.linspace(0, np.pi, n_lon, endpoint=False):
        c = circle(r, 48, "xz") @ rz(lo).T
        out.append(c + cx)
    return out


TOWER_A = 48.0


def tower():
    a, h, g = TOWER_A, P["tower_h"], GROUND
    L = []
    corners = [(a, a), (-a, a), (-a, -a), (a, -a)]
    for x, y in corners:
        L.append(np.array([[x, y, g], [x, y, h]]))
        L.append(np.array([[x, y, h], [0, 0, h + 8]]))  # 頂部アーム → 中心
    for z in np.linspace(g + 20, h - 10, 6):  # 水平トラス
        sq = np.array([[x, y, z] for x, y in corners + corners[:1]])
        L.append(sq)
    for i in range(4):  # 斜材
        (x1, y1), (x2, y2) = corners[i], corners[(i + 1) % 4]
        zs = np.linspace(g + 20, h - 10, 6)
        for z0, z1 in zip(zs[:-1], zs[1:]):
            L.append(np.array([[x1, y1, z0], [x2, y2, z1]]))
    L.append(np.array([[0, 0, h + 8], [0, 0, h - 6]]))  # 吊り下げ
    return L


def well_base():
    g = GROUND
    L = []
    for R in (66, 78, 90):  # 床面 (円形プラットフォーム)
        c = circle(R, 120)
        c[:, 2] = g
        L.append(c)
    for ang in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        L.append(np.array([[66 * np.cos(ang), 66 * np.sin(ang), g], [90 * np.cos(ang), 90 * np.sin(ang), g]]))
    return L


def well():
    g = GROUND
    L = []
    for z in np.linspace(g, g - 30, 4):  # 井戸 (輸送計量の漏斗)
        R = 66 - (g - z) * 1.2
        c = circle(R, 120)
        c[:, 2] = z
        L.append(c)
    for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
        L.append(np.array([[66 * np.cos(ang), 66 * np.sin(ang), g],
                           [30 * np.cos(ang), 30 * np.sin(ang), g - 30]]))
    return L


def windows():
    pts = []
    for k, a, v in WINDOWS:
        R = 26 + 4 * v
        pts.append(np.array([[R * np.cos(a), R * np.sin(a), 0.0]]))
    return pts


def door_axis(length=95):
    n = P["n_hat"] / np.linalg.norm(P["n_hat"])
    return [np.array([np.zeros(3), n * length])]


def scene(t_rot=0.0, spin=1.0, pod_z=0.0):
    """部品キー → (色キー, [polyline]) の辞書."""
    k = coils()
    return {
        "base": ("tower", well_base()),
        "well": ("well", well()),
        "tower": ("tower", tower()),
        "ring": ("ring", gimbal(t_rot, spin)),
        "j31": ("j31", k["j31"]),
        "j51": ("j51", k["j51"]),
        "j41": ("j41", k["j41"]),
        "window": ("window", windows()),
        "pod": ("pod", sphere(P["pod_r"], (0, 0, pod_z))),
        "axis": ("axis", door_axis()),
    }


ASSEMBLY_ORDER = ["base", "well", "tower", "ring", "j31", "j51", "j41", "window", "pod", "axis"]
PART_OF_KEY = {"j31": "coil", "j51": "coil", "j41": "coil"}
