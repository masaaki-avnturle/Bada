"""UFO (反重力機) の設計図モデル — contact_blueprint.pdf の方程式 UFO.1〜UFO.26 と src/UFO_OS.om から.

方程式の数値 (U, L(h), E_ag, 10 ステップ上昇 607.5 m / 110.45 m/s など) は本モジュールで
再計算し、レポートの値と一致することを確認している。機体の外形寸法はレポートに記載がないため図解用。
"""
import json
import os

import numpy as np
from math import gamma

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 物理定数と機体パラメータ (UFO.1, UFO.16) -------------------------------
Gc = 6.674e-11
M_E = 5.972e24
R0 = 6.371e6
m = 1.2e4          # 機体質量 [kg]
c = 299792458.0
v_ref = 1e4        # UFO.16 の v = 10^4 m/s


def xcoord(h):
    """UFO.14: x = manifold_coord(r0/r) — 地表で x = 2. x = 2√(r0/r) でレポートの L(h) を再現."""
    return 2.0 * np.sqrt(R0 / (R0 + h))


def lift(h):
    """UFO.11/19/23: L = E_ag/U_grav = cosh(x log x)."""
    x = xcoord(h)
    return np.cosh(x * np.log(x))


def g_eff(h):
    return Gc * M_E / (R0 + h) ** 2


def U(h=0.0):
    """UFO.1: U = GMm/r."""
    return Gc * M_E * m / (R0 + h)


def accel(h):
    """UFO.19: a = (L − 1)·g_eff."""
    return (lift(h) - 1) * g_eff(h)


def simulate(steps=10, dt=1.0):
    """UFO.24: 1 s 刻みで 10 ステップ上昇 (v ← v + a dt, h ← h + v dt)."""
    h, v = 0.0, 0.0
    rows = [dict(k=0, h=0.0, v=0.0, x=xcoord(0), L=lift(0), a=accel(0), Eag=U(0) * lift(0))]
    for k in range(1, steps + 1):
        a = accel(h)
        v += a * dt
        h += v * dt
        rows.append(dict(k=k, h=h, v=v, x=xcoord(h), L=lift(h), a=accel(h), Eag=U(h) * lift(h)))
    return rows


SIM = simulate()

V = dict(
    U=U(0), L0=lift(0), Eag=U(0) * lift(0), a0=accel(0),
    Eperp=m * c ** 2 - 0.5 * m * v_ref ** 2, KE=0.5 * m * v_ref ** 2,
    L1=lift(1e3), L5=lift(5e3), L20=lift(2e4), L100=lift(1e5),
    h10=SIM[-1]["h"], v10=SIM[-1]["v"],
    dmu=1 / (2 * np.log(2)) ** 2,  # UFO.5 (x = 2 で 0.520342)
    beta=gamma(2) * gamma(3) / gamma(5),  # β(2,3) = 1/12 (UFO.9)
    epi=np.exp(np.pi), pie=np.pi ** np.e, delta=np.exp(np.pi) - np.pi ** np.e,
    xx2=2.0 ** 2, eneg=np.exp(-2 * np.log(2)),
)


def reservoir(draws=10, level=5.0, cap=1e6):
    """UFO.25: 現在値の 5 倍を 10 回引き出しても貯槽は 99.9% 以上残る (図解用の容量 cap)."""
    r = cap
    out = [r]
    for _ in range(draws):
        r -= level * 1.0
        out.append(r)
    return np.array(out) / cap


RES = reservoir()

# ---- 部品 ↔ 方程式 -------------------------------------------------------
COL = {
    "hull": "#b8c7e0", "ring": "#f5b942", "core": "#ff6b5b", "res": "#4fd6e0", "sensor": "#7fb2ff",
    "fc": "#ffd166", "tuner": "#c28bff", "stab": "#9fe8ff", "port": "#ffa040", "safe": "#7ee787",
}

PARTS = [
    ("hull", "船体 (円盤)", ["UFO.3", "UFO.16"],
     [r"$E_\perp = mc^2 - \frac{1}{2}mv^2$", "m = 1.2×10⁴ kg, E⊥ ≈ 1.079×10²¹ J"], "直径 16 m / 厚さ 2.4 m (図解)"),
    ("ring", "反重力リング", ["UFO.2", "UFO.11"],
     ["□ag(x) = 2(sin(i·x log x) + cos(i·x log x))",
      "α_ag(x) = Re[□ag]/2 = cosh(x log x) ≥ 1"], "トーラス R = 6.5 m"),
    ("core", "重力結合コア", ["UFO.1", "UFO.13", "UFO.15"],
     [r"$U = GMm/r = 7.507\times10^{11}$ J",
      r"$E_{ag} = U\,\alpha_{ag} = 1.595\times10^{12}$ J,  $E_{ag} \geq U$"], "中心柱 r = 0.9 m"),
    ("res", "真空エネルギー貯槽", ["UFO.4", "UFO.12", "UFO.17", "UFO.25"],
     ["□dal(x) = cos(i·x log x) − i·sin(i·x log x) = x^x",
      r"$E_{vac} = \rho\,x^x$ ;  5 倍×10 回で残量 $\geq$ 99.9%"], "球 r = 1.6 m"),
    ("sensor", "多様体座標センサ", ["UFO.5", "UFO.6", "UFO.7", "UFO.14", "UFO.21"],
     [r"$x = \mathrm{manifold\_coord}(r_0/r) = 2\sqrt{r_0/r}$ (地表 x = 2)",
      r"$d\mu(x) = 1/(x\log x)^2,\ \ x\log x \to 0\ (x\to1)$"], "マスト高 2.2 m"),
    ("fc", "飛行制御 (UFO_OS)", ["UFO.19", "UFO.23", "UFO.24"],
     [r"$L = E_{ag}/U = \cosh(x\log x) = 2.125$ (地表)",
      r"$a = (L-1)\,g_{eff} = 11.047\ \mathrm{m/s^2}$"], "controlGravityDrive()"),
    ("tuner", "ζ・β 調律器", ["UFO.8", "UFO.9"],
     [r"$\zeta(s) = \beta(p,q)/\log x$",
      r"$\beta(p,q) = \Gamma(p)\Gamma(q)/\Gamma(p+q) = 1/12$"], "3 連リング"),
    ("stab", "エントロピー姿勢安定器", ["UFO.10"],
     [r"$\Xi = \beta(H+1, M+1)/\log(N+1) = 0.0056407$"], "外周ジャイロ 8 基"),
    ("port", "量子入出力ポート", ["UFO.20", "UFO.22"],
     [r"$\leftarrow\,:\ \pi(\chi,x)$,   $\succ\,:\ e^{-x\log x} = 0.25$"], "底面 3 基 (120°)"),
    ("safe", "安定条件モニタ", ["UFO.18", "UFO.26"],
     [r"$e^\pi \approx \pi^e$:  $\Delta = e^\pi - \pi^e = 0.6815$",
      r"$\Delta < 1$ で運転許可"], "ドーム頂部灯"),
]
PART_NAME = {k: n for k, n, *_ in PARTS}
EQ_PART = {i: k for k, _, ids, *_ in PARTS for i in ids}
ASSEMBLY_ORDER = ["hull", "core", "res", "ring", "tuner", "stab", "port", "sensor", "fc", "safe"]


def load_ufo_equations():
    with open(os.path.join(HERE, "data", "equations.json"), encoding="utf-8") as f:
        eqs = [e for e in json.load(f) if e["id"].startswith("UFO.")]
    for e in eqs:
        e["part"] = EQ_PART.get(e["id"], "fc")
    return eqs


UFO_EQS = load_ufo_equations()

UFO_OS = [  # src/UFO_OS.om の制御ループに方程式を割り当てたもの
    ("def controlGravityDrive() {", None),
    ("  let x = manifold_coord(r0 / r)", "UFO.14"),
    ("  let L = cosh(x * log(x))", "UFO.11"),
    ("  let g = G * M / r^2", "UFO.19"),
    ("  let a = (L - 1) * g", "UFO.19"),
    ("  v = v + a * dt ; h = h + v * dt", "UFO.24"),
    ("  assert E_ag >= U_grav", "UFO.15"),
    ("  assert reservoir >= 0.999", "UFO.25"),
    ("  assert exp(pi) - pi^e < 1", "UFO.26"),
    ("}", None),
]


# ---- 幾何 (図解寸法, m) -----------------------------------------------------
def circle(R, z, n=90, cx=0.0, cy=0.0):
    t = np.linspace(0, 2 * np.pi, n)
    return np.c_[cx + R * np.cos(t), cy + R * np.sin(t), np.full_like(t, z)]


def hull_profile():
    """レンズ型の半断面 (r, z)."""
    r = np.linspace(0, 8, 40)
    top = 1.2 * (1 - (r / 8) ** 2) ** 0.8
    bot = -1.2 * (1 - (r / 8) ** 2) ** 0.8
    return r, top, bot


def revolve(r, z, n_lon=16):
    out = []
    for a in np.linspace(0, np.pi, n_lon, endpoint=False):
        for s in (1, -1):
            out.append(np.c_[s * r * np.cos(a), s * r * np.sin(a), z])
    return out


def torus(R, rr, zc, k=4, n=120):
    out = []
    for j in range(k):
        a = 2 * np.pi * j / k
        out.append(circle(R + rr * np.cos(a), zc + rr * np.sin(a), n))
    for t in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        s = np.linspace(0, 2 * np.pi, 20)
        out.append(np.c_[(R + rr * np.cos(s)) * np.cos(t), (R + rr * np.cos(s)) * np.sin(t), zc + rr * np.sin(s)])
    return out


def sphere(r, center, nl=5, nm=6):
    cx = np.asarray(center, float)
    out = []
    for la in np.linspace(-np.pi / 2, np.pi / 2, nl + 2)[1:-1]:
        cc = circle(r * np.cos(la), r * np.sin(la), 40)
        out.append(cc + cx)
    for lo in np.linspace(0, np.pi, nm, endpoint=False):
        t = np.linspace(0, 2 * np.pi, 40)
        out.append(np.c_[r * np.cos(t) * np.cos(lo), r * np.cos(t) * np.sin(lo), r * np.sin(t)] + cx)
    return out


def geometry():
    g = {k: [] for k, *_ in PARTS}
    r, top, bot = hull_profile()
    for zz in (top, bot):
        g["hull"] += revolve(r, zz, 8)
    for rr in (2.5, 5.0, 7.0, 8.0):
        zt = 1.2 * (1 - (rr / 8) ** 2) ** 0.8
        g["hull"].append(circle(rr, zt))
        g["hull"].append(circle(rr, -zt))
    # ドーム
    t = np.linspace(0, np.pi / 2, 20)
    for a in np.linspace(0, np.pi, 6, endpoint=False):
        for s in (1, -1):
            g["hull"].append(np.c_[s * 2.6 * np.cos(t) * np.cos(a), s * 2.6 * np.cos(t) * np.sin(a),
                                   1.1 + 1.8 * np.sin(t)])
    g["ring"] += torus(6.5, 0.45, -1.1)
    g["core"].append(circle(0.9, -1.0))
    g["core"].append(circle(0.9, 2.2))
    for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        g["core"].append(np.array([[0.9 * np.cos(a), 0.9 * np.sin(a), -1.0], [0.9 * np.cos(a), 0.9 * np.sin(a), 2.2]]))
    g["res"] += sphere(1.6, (0, 0, -2.2))
    for zz, R in ((0.2, 4.0), (0.45, 3.6), (0.7, 3.2)):
        g["tuner"].append(circle(R, zz))
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        cx, cy = 7.3 * np.cos(a), 7.3 * np.sin(a)
        g["stab"].append(circle(0.35, 0.0, 20, cx, cy))
        g["stab"].append(np.array([[cx, cy, -0.35], [cx, cy, 0.35]]))
    for a in (np.pi / 2, np.pi / 2 + 2 * np.pi / 3, np.pi / 2 + 4 * np.pi / 3):
        cx, cy = 3.5 * np.cos(a), 3.5 * np.sin(a)
        g["port"].append(circle(0.5, -1.05, 24, cx, cy))
        g["port"].append(np.array([[cx, cy, -1.05], [cx, cy, -1.7]]))
    g["sensor"].append(np.array([[0, 0, 2.9], [0, 0, 5.1]]))
    g["sensor"].append(circle(0.6, 4.3, 30))
    g["sensor"].append(circle(0.35, 4.8, 30))
    g["fc"] += [np.array([[-0.8, -0.5, 1.3], [0.8, -0.5, 1.3], [0.8, 0.5, 1.3], [-0.8, 0.5, 1.3], [-0.8, -0.5, 1.3]]),
                np.array([[-0.8, -0.5, 1.9], [0.8, -0.5, 1.9], [0.8, 0.5, 1.9], [-0.8, 0.5, 1.9], [-0.8, -0.5, 1.9]])]
    g["safe"] += sphere(0.25, (0, 0, 5.3), 3, 3)
    return g


GEOM = geometry()
COLOR_OF = COL
