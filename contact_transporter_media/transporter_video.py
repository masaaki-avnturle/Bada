"""CONTACT TRANSPORTER の動画 (mp4) を生成する.

方程式 → 部品の対応 → 平面図 (三面図) → 3D 変換 → 組み立て → 起動・輸送 の順に描く。
  python3 transporter_video.py          # output/contact_transporter.mp4
  python3 transporter_video.py --preview  # 各シーンの代表フレームを PNG に書き出す
"""
import collections
import os
import sys
import warnings

import numpy as np

from common import (BG, C, FG, FPS, GRID, OUT, Timeline, fig_to_rgb, new_fig, render_video,
                    smooth, write_wav)
import matplotlib.pyplot as plt
import transporter_model as M

warnings.filterwarnings("ignore")

TL = Timeline([
    ("title", 5), ("params", 9), ("mapping", 12), ("plan", 10), ("to3d", 8),
    ("assembly", 30), ("activate", 16), ("transport", 14), ("end", 8),
])
N_FRAMES = int(TL.total * FPS)

SCENE_TITLE = {
    "params": "1. 設計原理と Bada 実行結果",
    "mapping": "2. 方程式 2111 本 → 部品への対応",
    "plan": "3. 平面図 (三面図)  単位 m",
    "to3d": "4. 平面図 → 3D 変換",
    "assembly": "5. 組み立て",
    "activate": "6. 起動 — ジンバル環の回転と共鳴",
    "transport": "7. 輸送 — 扉の軸 n̂ に沿って異次元へ",
}

# ---- レジストリ → 部品 (先頭タグで割り当て) --------------------------------
REG = M.load_registry()
PART_KEYS = [k for k, *_ in M.PARTS]
for e in REG:
    e["part"] = M.TAG_PART.get(e["tags"][0] if e["tags"] else "OTHER", "base")
    e["eq"] = e["eq"].replace("$", r"\$")
CUM = {k: np.cumsum([e["part"] == k for e in REG]) for k in PART_KEYS}
PART_COLOR = {k: C[c] for k, _, c, *_ in M.PARTS}
PART_COLOR["coil"] = C["j51"]

KEY_CARD = {
    "base": ("基礎・床", [r"床面 z = −井戸深さ = −38.800 m", "OTHER 群: □ = −(16πG/c⁴)·T_μν"]),
    "well": ("井戸 (輸送計量)", [r"$ds^2 = e^{-2\pi T|\psi|}[\eta+\bar h]dx^\mu dx^\nu + T^2d\psi^2$",
                              r"$e^{-2\pi T|\psi|}=1/\Gamma \Rightarrow T|\psi| = 1.76329$", "深さ 38.800 m"]),
    "tower": ("塔・ガントリー", [r"$\theta(\varphi)=\arg\Gamma(\frac{1}{4}+\frac{i\varphi}{2})-\frac{\varphi}{2}\log\pi$",
                             r"$\theta(11.7722) = -2.58136$", "塔高 132.194 m"]),
    "ring": ("ジンバル環 ×3 (複素回転体)", [r"$\Theta = \theta + i\varphi,\ \theta_0 = 0.523599$ rad",
                                     r"$\omega = 0.10472,\ 0.39241,\ 1.47043$ rad/s",
                                     "R = 60.088 / 47.431 / 37.440 m"]),
    "j31": ("Jones コイル 3_1 (三葉結び目)", [r"$V = -t^{-4}+t^{-3}+t^{-1}$",
                                       r"$V(t^*) = -0.11634 + 2.30909i$", "R = 70.269 m"]),
    "j51": ("Jones コイル 5_1", [r"$V = t^2+t^4-t^5+t^6-t^7$",
                              r"$V(t^*) = -2.81527 + 1.09659i$", "R = 56.215 m"]),
    "j41": ("Jones コイル 4_1 (8の字結び目, 床下)", [r"$V = t^{-2}-t^{-1}+1-t+t^2$",
                                          r"$V(t^*) = 3.56479$", r"$t^* = e^{i\theta(\varphi)}$"]),
    "window": ("扉の共鳴窓", [r"$Z(\varphi)=e^{i\theta(\varphi)}\zeta(\frac{1}{2}+i\varphi) = -1.33415$",
                          r"$\min_\alpha |V_K(e^{i\alpha})|$ の角度に配置", f"窓 {len(M.WINDOWS)} 箇所"]),
    "pod": ("ポッド (搭乗室)", [r"$\Gamma = 18\,h/1\,s = 64800$",
                            r"$\varphi = \mathrm{arcosh}\,\Gamma = 11.7722$",
                            r"$\Omega = Mgl/(I_3\omega_3) = 3.70640$ rad/s,  r = 5.021 m"]),
    "axis": ("扉の軸 n̂", [r"$\sqrt{s} = 13.6$ TeV,  $E_T^{miss} = 1348.29$ GeV",
                         r"$\hat n = (0.86964,\,-0.25101,\,0.42511)$", "CERN の衝突で粒子が消えた方向"]),
}

POD_TOP = M.P["tower_h"] - 14


# ---- 描画ヘルパ ------------------------------------------------------------
def add_3d(fig, rect=(0, 0, 1, 1), elev=22, azim=-60, zoom=1.35, lim=95):
    ax = fig.add_axes(rect, projection="3d")
    ax.set_facecolor(BG)
    ax.set_axis_off()
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    z0, z1 = M.GROUND - 35, 150
    ax.set_zlim(z0, z1)
    ax.set_box_aspect((1, 1, (z1 - z0) / (2 * lim)), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    return ax


def draw_part(ax, polys, color, lw=1.1, alpha=1.0, zscale=1.0, offset=(0, 0, 0), marker=False):
    off = np.asarray(offset, float)
    for p in polys:
        q = p.copy()
        q[:, 2] *= zscale
        q = q + off
        if marker or len(q) == 1:
            ax.scatter(q[:, 0], q[:, 1], q[:, 2], color=color, s=36, alpha=alpha, depthshade=False)
        else:
            ax.plot(q[:, 0], q[:, 1], q[:, 2], color=color, lw=lw, alpha=alpha)


def header(fig, name, u):
    if name in SCENE_TITLE:
        fig.text(0.03, 0.94, SCENE_TITLE[name], color=FG, fontsize=20, weight="bold")
    fig.text(0.97, 0.955, "CONTACT TRANSPORTER", color=C["hud"], fontsize=11, ha="right", alpha=0.8)
    t = TL.start(name) + u * dict((n, d) for n, _, d in TL.scenes)[name]
    fig.add_artist(plt.Line2D([0.03, 0.97], [0.018, 0.018], color=GRID, lw=3))
    fig.add_artist(plt.Line2D([0.03, 0.03 + 0.94 * t / TL.total], [0.018, 0.018], color=C["hud"], lw=3))


def blueprint_grid(fig):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    for x in np.linspace(0, 1, 33):
        ax.axvline(x, color=GRID, lw=0.4, alpha=0.5)
    for y in np.linspace(0, 1, 19):
        ax.axhline(y, color=GRID, lw=0.4, alpha=0.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    return ax


# ---- シーン ---------------------------------------------------------------
def s_title(fig, u, sec):
    blueprint_grid(fig)
    ax = add_3d(fig, (0.25, 0.0, 0.5, 0.85), elev=18, azim=-60 + 20 * sec, zoom=0.9, lim=70)
    for c in M.gimbal(sec * 3):
        ax.plot(*c.T, color=C["ring"], lw=0.8, alpha=0.35 * smooth(u * 3))
    a = smooth(u * 2.5)
    fig.text(0.5, 0.62, "CONTACT TRANSPORTER", color=FG, fontsize=46, ha="center", weight="bold", alpha=a)
    fig.text(0.5, 0.52, "異次元への輸送機 — 方程式から組み立てる 3D 設計図", color=C["hud"],
             fontsize=22, ha="center", alpha=a)
    fig.text(0.5, 0.18, "原典: contact_blueprint.pdf (Bada: contact_transporter/contact_blueprint.bada)\n"
             "論文 15 本・全方程式 2111 本 → 部品 → 平面図 → 3D → 組み立て → 起動",
             color=FG, fontsize=13, ha="center", alpha=smooth(u * 2.5 - 0.6), linespacing=1.6)


PARAM_LINES = [
    ("① 衝突段", r"$\sqrt{s}=13.6$ TeV,  $E_T^{miss}=1348.29$ GeV  →  扉の軸 $\hat n=(0.870,-0.251,0.425)$", C["axis"]),
    ("② 特殊相対論", r"地球の 1 秒 = 搭乗者の 18 時間:  $\Gamma = 64800,\ 1-\beta = 1.19\times10^{-10},\ \varphi = 11.7722$", C["pod"]),
    ("②' 輸送計量", r"$ds^2 = e^{-2\pi T|\psi|}[\eta+\bar h]dx^\mu dx^\nu + T^2 d\psi^2,\ \ T|\psi| = 1.76329$", C["well"]),
    ("③ 複素回転体", r"$\Theta=\theta+i\varphi,\ \theta_0 = 30°,\ \ \omega = (0.105,\ 0.392,\ 1.470)$ rad/s", C["ring"]),
    ("④ Γ・ζ 多様体", r"$\theta(\varphi) = -2.58136,\ \ Z(\varphi) = e^{i\theta}\zeta(\frac{1}{2}+i\varphi) = -1.33415$", C["window"]),
    ("⑤ Jones 多項式", r"$V_{3_1}(t^*) = -0.116+2.309i,\ V_{4_1} = 3.565,\ V_{5_1} = -2.815+1.097i$", C["j51"]),
    ("⑥ 寸法", "外環 60.088 / 中環 47.431 / 内環 37.440 / ポッド r 5.021 / 塔高 132.194 / 井戸 38.8 m", C["tower"]),
]


def s_params(fig, u, sec):
    blueprint_grid(fig)
    for i, (h, body, col) in enumerate(PARAM_LINES):
        a = smooth((u * 1.25 - i * 0.12) * 5)
        y = 0.80 - i * 0.105
        fig.text(0.05 + 0.02 * (1 - a), y, h, color=col, fontsize=17, weight="bold", alpha=a)
        fig.text(0.23 + 0.02 * (1 - a), y, body, color=FG, fontsize=15, alpha=a)
    fig.text(0.05, 0.06, "再計算 (mpmath) でも θ(φ), Z(φ), V(t*) はレポート値と一致", color=C["hud"],
             fontsize=12, alpha=smooth(u * 3 - 2))


def s_mapping(fig, u, sec):
    blueprint_grid(fig)
    n = int(np.clip(smooth(u * 1.15), 0, 1) * len(REG))
    # 左: 流れてくる方程式
    fig.text(0.04, 0.86, f"方程式レジストリ  {n:4d} / 2111", color=C["hud"], fontsize=14)
    shown = REG[max(0, n - 15):n]
    for j, e in enumerate(reversed(shown)):
        y = 0.81 - j * 0.049
        col = PART_COLOR[e["part"]]
        txt = e["eq"] if len(e["eq"]) < 46 else e["eq"][:45] + "…"
        a = 1.0 - j / 17
        fig.text(0.04, y, f"{e['id']:<9s}", color=col, fontsize=10.5, alpha=a, family="IPAGothic")
        fig.text(0.12, y, txt, color=FG, fontsize=10.5, alpha=a)
    # 右: 部品ボックスとカウンタ
    ys = {}
    for i, (k, name, ck, *_rest) in enumerate(M.PARTS):
        y = 0.82 - i * 0.095
        ys[k] = y
        col = PART_COLOR[k] if k != "coil" else C["j51"]
        cnt = int(CUM[k][n - 1]) if n else 0
        tot = int(CUM[k][-1])
        fig.add_artist(plt.Rectangle((0.66, y - 0.03), 0.31, 0.07, fill=False, ec=col, lw=1.4))
        fig.add_artist(plt.Rectangle((0.66, y - 0.03), 0.31 * cnt / max(tot, 1), 0.07, color=col, alpha=0.18))
        fig.text(0.67, y, name, color=FG, fontsize=13, va="center")
        fig.text(0.96, y, f"{cnt}", color=col, fontsize=14, va="center", ha="right", weight="bold")
    tags = collections.defaultdict(list)
    for tg, pk in M.TAG_PART.items():
        tags[pk].append(tg)
    for k, y in ys.items():
        fig.text(0.655, y, " ".join(tags.get(k, [])), color=GRID, fontsize=8.5, va="center", ha="right",
                 alpha=0.0 if u < 0.05 else 0.9)
    # 最新 5 本は部品へ線で結ぶ
    for j, e in enumerate(reversed(REG[max(0, n - 5):n])):
        y0 = 0.81 - j * 0.049
        fig.add_artist(plt.Line2D([0.5, 0.655], [y0 + 0.006, ys[e["part"]]], color=PART_COLOR[e["part"]],
                                  lw=1.2, alpha=0.8 - j * 0.15))
    if u > 0.9:
        fig.text(0.04, 0.05, "先頭タグで割り当て: ROT→環, SR/QUANTUM→ポッド, GAMMA/BETA→塔, ZETA→共鳴窓, "
                 "JONES→コイル, MANIFOLD/ENTROPY→井戸, TRANSPORT→扉の軸", color=C["hud"], fontsize=11)


def project(p, view):
    return {"top": (p[:, 0], p[:, 1]), "front": (p[:, 0], p[:, 2]), "side": (p[:, 1], p[:, 2])}[view]


def draw_plan(fig, progress, dims=0.0, rects=None, fs=1.0):
    """三面図. progress∈[0,1] で線を描き進める. PDF からも使う."""
    sc = M.scene()
    rects = rects or {"top": (0.03, 0.07, 0.36, 0.82), "front": (0.41, 0.07, 0.28, 0.82),
                      "side": (0.705, 0.07, 0.28, 0.82)}
    titles = {"top": "上面図 (x–y)", "front": "正面図 (x–z)", "side": "側面図 (y–z)"}
    axes = {}
    for v, r in rects.items():
        ax = fig.add_axes(r)
        ax.set_facecolor(BG)
        for s in ax.spines.values():
            s.set_color(GRID)
        ax.tick_params(colors=FG, labelsize=7 * fs)
        ax.grid(color=GRID, lw=0.4)
        ax.set_title(titles[v], color=FG, fontsize=12 * fs)
        ax.set_aspect("equal")
        if v == "top":
            ax.set_xlim(-95, 95)
            ax.set_ylim(-95, 95)
        else:
            ax.set_xlim(-95, 95)
            ax.set_ylim(M.GROUND - 35, 150)
        axes[v] = ax
        for key, (ck, polys) in sc.items():
            for p in polys:
                m = max(1, int(np.ceil(len(p) * progress)))
                x, y = project(p[:m], v)
                if len(p) == 1:
                    ax.scatter(x, y, color=C[ck], s=14 * fs, zorder=5)
                else:
                    ax.plot(x, y, color=C[ck], lw=0.8, alpha=0.9)
    if dims > 0:
        a = smooth(dims)
        kw = dict(color=C["warn"], fontsize=9 * fs, alpha=a)
        at = axes["top"]
        at.annotate("", (M.P["R_out"], 0), (0, 0), arrowprops=dict(arrowstyle="<->", color=C["warn"], alpha=a))
        at.text(8, 3, "R外 = 60.088", **kw)
        at.annotate("", (0, -M.P["J31_R"]), (0, 0), arrowprops=dict(arrowstyle="<->", color=C["j31"], alpha=a))
        at.text(2, -50, "Jones 3_1 R = 70.269", color=C["j31"], fontsize=9 * fs, alpha=a)
        af = axes["front"]
        af.annotate("", (-85, M.P["tower_h"]), (-85, M.GROUND),
                    arrowprops=dict(arrowstyle="<->", color=C["warn"], alpha=a))
        af.text(-82, 60, "塔高\n132.194\n(+38.8)", **kw)
        af.annotate("", (70, 0), (70, M.GROUND), arrowprops=dict(arrowstyle="<->", color=C["warn"], alpha=a))
        af.text(72, -30, "井戸\n38.8", **kw)
        af.text(8, 8, "ポッド r=5.021", color=FG, fontsize=8 * fs, alpha=a)
        asd = axes["side"]
        asd.text(-90, 75, "5_1 R=56.215", color=C["j51"], fontsize=9 * fs, alpha=a)
        asd.text(-90, M.GROUND + 18, "4_1 床下", color=C["j41"], fontsize=9 * fs, alpha=a)
    return axes


def s_plan(fig, u, sec):
    blueprint_grid(fig)
    draw_plan(fig, smooth(u / 0.7), dims=(u - 0.7) / 0.2, rects={
        "top": (0.02, 0.07, 0.36, 0.8), "front": (0.40, 0.07, 0.29, 0.8), "side": (0.70, 0.07, 0.29, 0.8)})


def all_parts(ax, sc, zscale=1.0, alpha=1.0, skip=(), lw=1.0):
    for key, (ck, polys) in sc.items():
        if key in skip:
            continue
        draw_part(ax, polys, C[ck], lw=lw, alpha=alpha, zscale=zscale)


def s_to3d(fig, u, sec):
    s = smooth(u / 0.8)
    ax = add_3d(fig, elev=89.9 - (89.9 - 22) * s, azim=-90 + 30 * s, zoom=1.35)
    sc = M.scene(pod_z=POD_TOP)
    # z 方向を 0 (平面図) から方程式由来の実寸へ持ち上げる
    all_parts(ax, sc, zscale=max(s, 1e-3))
    fig.text(0.03, 0.86, f"z ← s · z(方程式),  s = {s:0.2f}", color=C["hud"], fontsize=14)
    fig.text(0.03, 0.82, "上面図 (x–y) を仰角 90° → 22° に回し、各部品の高さを復元", color=FG, fontsize=12)


EXPLODE = {
    "base": (0, 0, -80), "well": (0, 0, -90), "tower": (0, 0, 160), "ring": (140, 0, 30),
    "j31": (-150, 0, 0), "j51": (0, 150, 60), "j41": (0, -140, -40), "window": (0, 0, 120),
    "pod": (0, 0, 120), "axis": (60, -20, 60),
}


def s_assembly(fig, u, sec):
    n = len(M.ASSEMBLY_ORDER)
    step = u * n
    cur = min(int(step), n - 1)
    f = smooth((step - cur) / 0.6)
    ax = add_3d(fig, (0.0, 0.0, 0.66, 1.0), elev=20, azim=-60 + 40 * u, zoom=1.3)
    sc = M.scene(pod_z=POD_TOP)
    for i, key in enumerate(M.ASSEMBLY_ORDER[:cur + 1]):
        ck, polys = sc[key]
        if i < cur:
            draw_part(ax, polys, C[ck], lw=1.0, alpha=0.9)
        else:
            off = np.asarray(EXPLODE[key]) * (1 - f)
            draw_part(ax, polys, C[ck], lw=1.8, alpha=0.25 + 0.75 * f, offset=off)
    key = M.ASSEMBLY_ORDER[cur]
    title, lines = KEY_CARD[key]
    col = C[sc[key][0]] if key != "pod" else C["hud"]
    a = 0.35 + 0.65 * smooth((step - cur) / 0.25)
    fig.add_artist(plt.Rectangle((0.64, 0.30), 0.34, 0.50, fill=True, fc=BG, ec=col, lw=1.5, alpha=0.9))
    fig.text(0.655, 0.75, f"部品 {cur + 1}/{n}", color=col, fontsize=12, alpha=a)
    fig.text(0.655, 0.70, title, color=FG, fontsize=16, weight="bold", alpha=a)
    for j, ln in enumerate(lines):
        fig.text(0.655, 0.62 - j * 0.075, ln, color=FG, fontsize=12.5, alpha=a)
    # 組み立て済みリスト
    for i, k in enumerate(M.ASSEMBLY_ORDER):
        done = i < cur or (i == cur and f > 0.99)
        fig.text(0.655 + (i % 2) * 0.17, 0.24 - (i // 2) * 0.037,
                 ("■ " if done else "□ ") + KEY_CARD[k][0].split(" (")[0],
                 color=C["hud"] if done else GRID, fontsize=10)


def hud_zeta(fig, sec, rect=(0.03, 0.08, 0.28, 0.2)):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=FG, labelsize=7)
    ax.plot(M.ZT, M.ZV, color=C["window"], lw=1)
    ax.axhline(0, color=GRID, lw=0.6)
    tt = 0.5 + (sec * 4) % 39.5
    ax.scatter([tt], [np.interp(tt, M.ZT, M.ZV)], color=C["pod"], s=18, zorder=5)
    ax.axvline(M.P["phi"], color=C["axis"], lw=0.8, ls="--")
    ax.set_title("Riemann–Siegel Z(t)   φ = 11.7722 で Z = −1.334", color=FG, fontsize=9)
    return ax


def s_activate(fig, u, sec):
    spin = 1 + 7 * smooth(u)  # 表示上の角速度倍率
    t_rot = 2 * sec + 7 * (sec ** 2) / (2 * 16)  # 角速度を積分した回転時間
    pod_z = POD_TOP * (1 - smooth((u - 0.1) / 0.55))
    ax = add_3d(fig, elev=18 + 6 * np.sin(u * 3), azim=-40 + 60 * u, zoom=1.35)
    sc = M.scene(t_rot=t_rot, pod_z=pod_z)
    pulse = 0.5 + 0.5 * np.sin(sec * 6)
    for key, (ck, polys) in sc.items():
        lw = 1.0
        alpha = 0.9
        if key in ("j31", "j51", "j41"):
            lw = 1.0 + 1.6 * pulse * smooth(u * 2)
        if key == "window":
            alpha = 0.3 + 0.7 * pulse
        if key == "axis":
            alpha = smooth((u - 0.6) * 4)
        draw_part(ax, polys, C[ck], lw=lw, alpha=alpha)
    hud_zeta(fig, sec)
    fig.text(0.72, 0.84, f"ω 倍率  ×{spin:4.1f}", color=C["ring"], fontsize=15, family="IPAGothic")
    fig.text(0.72, 0.79, f"ポッド高度  {pod_z:6.1f} m", color=C["pod"], fontsize=15, family="IPAGothic")
    fig.text(0.72, 0.74, f"歳差 Ω = 3.70640 rad/s", color=C["hud"], fontsize=13)
    state = "ポッド降下中" if u < 0.65 else ("共鳴窓 同期" if u < 0.85 else "扉 開放")
    fig.text(0.72, 0.68, state, color=C["warn"], fontsize=17, weight="bold")


def tunnel(ax, sec, alpha):
    n = M.P["n_hat"] / np.linalg.norm(M.P["n_hat"])
    a = np.cross(n, [0, 0, 1])
    a /= np.linalg.norm(a)
    b = np.cross(n, a)
    t = np.linspace(0, 2 * np.pi, 60)
    for k in range(14):
        d = (k * 12 + sec * 40) % 170
        r = 22 * np.exp(-d / 90) + 3
        pts = d * n[None, :] + r * (np.cos(t)[:, None] * a + np.sin(t)[:, None] * b)
        ax.plot(*pts.T, color=C["hud"], lw=1.0, alpha=alpha * (1 - d / 170))


def s_transport(fig, u, sec):
    n = M.P["n_hat"] / np.linalg.norm(M.P["n_hat"])
    trav = smooth((u - 0.12) / 0.6)
    ax = add_3d(fig, elev=15, azim=-30 + 25 * u, zoom=1.35 + 0.5 * trav)
    sc = M.scene(t_rot=30 + 12 * sec, pod_z=0)
    fade = 1 - 0.75 * trav
    for key, (ck, polys) in sc.items():
        if key == "pod":
            continue
        draw_part(ax, polys, C[ck], lw=1.0, alpha=0.9 * fade)
    tunnel(ax, sec, smooth(u * 4))
    pos = n * 150 * trav
    pod_a = 1.0 if u < 0.8 else max(0.0, 1 - (u - 0.8) * 5)
    draw_part(ax, M.sphere(M.P["pod_r"], pos), C["pod"], lw=1.4, alpha=pod_a)
    flash = max(0.0, 1 - abs(u - 0.1) / 0.06)
    if flash > 0:
        fig.add_artist(plt.Rectangle((0, 0), 1, 1, color="white", alpha=0.85 * flash))
    te = np.clip((u - 0.12) / 0.8, 0, 1)
    tau_h = 18.0 * te
    fig.text(0.03, 0.84, f"地球時間      t = {te:6.3f} s", color=FG, fontsize=16, family="IPAGothic")
    fig.text(0.03, 0.79, f"搭乗者時間  τ = {tau_h:6.2f} h", color=C["warn"], fontsize=16,
             family="IPAGothic")
    fig.text(0.03, 0.73, "Γ = 64800   (地球の 1 秒 = 搭乗者の 18 時間)", color=C["hud"], fontsize=12)
    d = 3.656e9 * (1 - te)
    fig.text(0.03, 0.67, f"ベガ (25.04 ly) 収縮距離 残り {d:9.3e} km", color=FG, fontsize=13)
    fig.text(0.03, 0.63, "片道 3.3874 h (搭乗者時間)", color=FG, fontsize=12)
    fig.text(0.03, 0.10, r"$\hat n = (0.86964,\ -0.25101,\ 0.42511)$ — 衝突で消えた運動量の方向",
             color=C["axis"], fontsize=13)


def s_end(fig, u, sec):
    blueprint_grid(fig)
    ax = add_3d(fig, (0.2, 0.25, 0.6, 0.72), elev=20, azim=-60 + 20 * sec, zoom=1.3)
    sc = M.scene(t_rot=sec * 1.5, pod_z=0)
    all_parts(ax, sc, alpha=0.6 * smooth(u * 3))
    a = smooth(u * 3 - 0.3)
    fig.text(0.5, 0.2, "方程式 2111 本 → 部品 10 点 → 平面図 → 3D → 組み立て → 起動", color=FG,
             fontsize=16, ha="center", alpha=a)
    fig.text(0.5, 0.09, "※ 論文の方程式に基づく思索的・フィクションの設計図 (幾何的な可視化) です。\n"
             "工学的に検証された装置ではなく、異次元への輸送を可能にするものではありません。",
             color=C["warn"], fontsize=12, ha="center", alpha=a, linespacing=1.5)


SCENES = {"title": s_title, "params": s_params, "mapping": s_mapping, "plan": s_plan, "to3d": s_to3d,
          "assembly": s_assembly, "activate": s_activate, "transport": s_transport, "end": s_end}


def frame(i):
    sec = i / FPS
    name, u, local = TL.at(sec)
    fig = new_fig()
    SCENES[name](fig, u, local)
    if name != "title":
        header(fig, name, u)
    # シーン境界でフェード
    _, t0, dur = next(s for s in TL.scenes if s[0] == name)
    edge = min(local, dur - local)
    if edge < 0.35:
        fig.add_artist(plt.Rectangle((0, 0), 1, 1, color=BG, alpha=1 - edge / 0.35))
    img = fig_to_rgb(fig)
    plt.close(fig)
    return img


def soundtrack(path):
    sr = 44100
    t = np.arange(int(TL.total * sr)) / sr
    env = np.ones_like(t)
    base = 0.10 * np.sin(2 * np.pi * 55 * t) + 0.05 * np.sin(2 * np.pi * 82.5 * t)
    a0, a1 = TL.start("activate"), TL.start("transport")
    ramp = np.clip((t - a0) / (a1 - a0), 0, 1)
    f = 110 + 330 * ramp ** 2
    phase = 2 * np.pi * np.cumsum(f) / sr
    whine = 0.08 * ramp * np.sin(phase)
    rng = np.random.default_rng(1)
    burst_t = a1 + 0.1 * 14
    burst = 0.5 * np.exp(-np.clip(t - burst_t, 0, None) * 3) * (t > burst_t) * rng.standard_normal(len(t))
    shimmer = 0.05 * (t > burst_t) * (t < TL.start("end")) * np.sin(2 * np.pi * (660 + 30 * np.sin(t)) * t)
    env *= np.clip(t / 2, 0, 1) * np.clip((TL.total - t) / 2, 0, 1)
    write_wav(path, (base + whine + burst * 0.4 + shimmer) * env)


def main():
    if "--preview" in sys.argv:
        from PIL import Image
        os.makedirs(os.path.join(OUT, "preview"), exist_ok=True)
        for name, t0, dur in TL.scenes:
            for frac in (0.5, 0.9):
                i = int((t0 + dur * frac) * FPS)
                Image.fromarray(frame(i)).save(os.path.join(OUT, "preview", f"tr_{name}_{int(frac*10)}.png"))
        return
    wav = os.path.join(OUT, "_transporter.wav")
    soundtrack(wav)
    render_video(os.path.join(OUT, "contact_transporter.mp4"), N_FRAMES, frame, audio_wav=wav)
    os.remove(wav)
    print("done", N_FRAMES, "frames")


if __name__ == "__main__":
    main()
