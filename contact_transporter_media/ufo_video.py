"""UFO (反重力機) 設計図の動画 (mp4) を生成する.

方程式 UFO.1〜26 → 部品 → 平面図 → 3D → 組み立て → 飛行 (方程式を毎ステップ評価して上昇) の順に描く。
  python3 ufo_video.py            # output/ufo_blueprint.mp4
  python3 ufo_video.py --preview
"""
import os
import sys
import warnings

import numpy as np

from common import (BG, C, FG, FPS, GRID, OUT, Timeline, fig_to_rgb, new_fig, render_video,
                    smooth, write_wav)
import matplotlib.pyplot as plt
import ufo_model as U

warnings.filterwarnings("ignore")

TL = Timeline([
    ("title", 5), ("params", 10), ("mapping", 12), ("plan", 10), ("to3d", 8),
    ("assembly", 30), ("flight", 28), ("end", 7),
])
N_FRAMES = int(TL.total * FPS)
SCENE_TITLE = {
    "params": "1. 反重力の方程式 (UFO.1–26) と再計算",
    "mapping": "2. 方程式 26 本 → 部品への対応",
    "plan": "3. 平面図 (三面図)  単位 m",
    "to3d": "4. 平面図 → 3D 変換",
    "assembly": "5. 組み立て",
    "flight": "6. 飛行 — 制御ループが毎秒方程式を評価して上昇",
}
LIM = 10.0
ZR = (-7.0, 7.0)


def add_3d(fig, rect=(0, 0, 1, 1), elev=20, azim=-60, zoom=1.3, zr=ZR):
    ax = fig.add_axes(rect, projection="3d")
    ax.set_facecolor(BG)
    ax.set_axis_off()
    ax.set_xlim(-LIM, LIM)
    ax.set_ylim(-LIM, LIM)
    ax.set_zlim(*zr)
    ax.set_box_aspect((1, 1, (zr[1] - zr[0]) / (2 * LIM)), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    return ax


def draw(ax, polys, color, lw=1.0, alpha=1.0, zscale=1.0, offset=(0, 0, 0)):
    off = np.asarray(offset, float)
    for p in polys:
        q = p.copy()
        q[:, 2] *= zscale
        q += off
        ax.plot(q[:, 0], q[:, 1], q[:, 2], color=color, lw=lw, alpha=alpha)


def draw_all(ax, lw=0.9, alpha=1.0, zscale=1.0, offset=None, glow=0.0):
    for k, polys in U.GEOM.items():
        w = lw + (1.8 * glow if k == "ring" else 0)
        draw(ax, polys, U.COL[k], w, alpha, zscale, (offset or {}).get(k, (0, 0, 0)))


def grid_bg(fig):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    for x in np.linspace(0, 1, 33):
        ax.axvline(x, color=GRID, lw=0.4, alpha=0.5)
    for y in np.linspace(0, 1, 19):
        ax.axhline(y, color=GRID, lw=0.4, alpha=0.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()


def header(fig, name, sec):
    if name in SCENE_TITLE:
        fig.text(0.03, 0.94, SCENE_TITLE[name], color=FG, fontsize=20, weight="bold")
    fig.text(0.97, 0.955, "UFO BLUEPRINT", color=C["hud"], fontsize=11, ha="right", alpha=0.8)
    fig.add_artist(plt.Line2D([0.03, 0.97], [0.018, 0.018], color=GRID, lw=3))
    fig.add_artist(plt.Line2D([0.03, 0.03 + 0.94 * sec / TL.total], [0.018, 0.018], color=C["hud"], lw=3))


def s_title(fig, u, sec):
    grid_bg(fig)
    ax = add_3d(fig, (0.25, 0.05, 0.5, 0.6), elev=18, azim=-60 + 25 * sec, zoom=1.2)
    draw_all(ax, 0.7, 0.4 * smooth(u * 3))
    a = smooth(u * 2.5)
    fig.text(0.5, 0.78, "UFO BLUEPRINT", color=FG, fontsize=46, ha="center", weight="bold", alpha=a)
    fig.text(0.5, 0.69, "反重力機 — 方程式が使われる 3D 設計図", color=C["hud"], fontsize=22, ha="center", alpha=a)
    fig.text(0.5, 0.08, "原典: contact_blueprint.pdf の方程式 UFO.1–UFO.26 / src/UFO_OS.om", color=FG,
             fontsize=13, ha="center", alpha=smooth(u * 2.5 - 0.6))


def s_params(fig, u, sec):
    grid_bg(fig)
    V = U.V
    rows = [
        ("UFO.1", r"$U = GMm/r$", f"{V['U']:.5e} J", "7.50723e+11", U.COL["core"]),
        ("UFO.3", r"$E_\perp = mc^2 - \frac{1}{2}mv^2$", f"{V['Eperp']:.5e} J", "1.07851e+21", U.COL["hull"]),
        ("UFO.11", r"$\alpha_{ag} = \cosh(x\log x)$,  x = 2", f"{V['L0']:.4f}", "L = 2.125", U.COL["ring"]),
        ("UFO.13", r"$E_{ag} = (GMm/r)\cosh(x\log x)$", f"{V['Eag']:.5e} J", "1.59529e+12", U.COL["core"]),
        ("UFO.19", r"$a = (L-1)\,g_{eff}$", f"{V['a0']:.3f} m/s²", "11.047", U.COL["fc"]),
        ("UFO.23", "L(1 km), L(5 km), L(20 km), L(100 km)",
         f"{V['L1']:.5f}, {V['L5']:.5f}, {V['L20']:.5f}, {V['L100']:.5f}", "2.12450, 2.12251, 2.11510, 2.07677",
         U.COL["sensor"]),
        ("UFO.24", "10 ステップ後の高度・速度", f"{V['h10']:.1f} m, {V['v10']:.2f} m/s", "607.6 m, 110.46 m/s",
         U.COL["fc"]),
        ("UFO.26", r"$\Delta = e^\pi - \pi^e < 1$", f"{V['delta']:.4f}", "0.6815", U.COL["safe"]),
    ]
    fig.text(0.04, 0.86, "式 ID", color=C["hud"], fontsize=12)
    fig.text(0.13, 0.86, "方程式", color=C["hud"], fontsize=12)
    fig.text(0.52, 0.86, "再計算", color=C["hud"], fontsize=12)
    fig.text(0.78, 0.86, "レポート値", color=C["hud"], fontsize=12)
    for i, (eid, eq, val, rep, col) in enumerate(rows):
        a = smooth((u * 1.3 - i * 0.1) * 5)
        y = 0.8 - i * 0.087
        fig.text(0.04, y, eid, color=col, fontsize=14, weight="bold", alpha=a)
        fig.text(0.13, y, eq, color=FG, fontsize=14, alpha=a)
        small = len(val) > 24
        fig.text(0.52, y, val.replace(", ", "\n", 1) if small else val, color=FG, fontsize=10 if small else 13,
                 alpha=a, va="center" if small else "baseline")
        fig.text(0.78, y, (rep.replace(", ", "\n", 1) if small else rep) + "  ✓", color=U.COL["safe"],
                 fontsize=10 if small else 12, alpha=a, va="center" if small else "baseline")
    fig.text(0.04, 0.06, "x = manifold_coord(r0/r) = 2√(r0/r) (地表 x = 2) とすると、レポートの L(h) と上昇軌道を再現",
             color=C["hud"], fontsize=11, alpha=smooth(u * 3 - 2))


def s_mapping(fig, u, sec):
    grid_bg(fig)
    eqs = U.UFO_EQS
    n = int(np.clip(smooth(u * 1.1), 0, 1) * len(eqs) + 0.999)
    ys = {}
    for i, (k, name, *_r) in enumerate(U.PARTS):
        y = 0.86 - i * 0.08
        ys[k] = y
        col = U.COL[k]
        cnt = sum(1 for e in eqs[:n] if e["part"] == k)
        fig.add_artist(plt.Rectangle((0.71, y - 0.028), 0.26, 0.058, fc=col, alpha=0.15 if cnt else 0))
        fig.add_artist(plt.Rectangle((0.71, y - 0.028), 0.26, 0.058, fill=False, ec=col, lw=1.3))
        fig.text(0.72, y, name, color=FG, fontsize=12, va="center")
        fig.text(0.96, y, str(cnt), color=col, fontsize=13, va="center", ha="right", weight="bold")
    for j, e in enumerate(eqs[:n]):
        y = 0.885 - j * 0.0325
        col = U.COL[e["part"]]
        txt = e["eq"] if len(e["eq"]) < 58 else e["eq"][:57] + "…"
        fig.text(0.03, y, e["id"], color=col, fontsize=9.5, va="center")
        fig.text(0.09, y, txt.replace("$", r"\$"), color=FG, fontsize=9.5, va="center")
        if j >= n - 4:
            fig.add_artist(plt.Line2D([0.56, 0.705], [y, ys[e["part"]]], color=col, lw=1.1, alpha=0.8))


def project(p, view):
    return {"top": (p[:, 0], p[:, 1]), "front": (p[:, 0], p[:, 2]), "side": (p[:, 1], p[:, 2])}[view]


def draw_plan(fig, prog=1.0, dims=0.0, rects=None, fs=1.0):
    rects = rects or {"top": (0.02, 0.08, 0.34, 0.8), "front": (0.38, 0.28, 0.3, 0.45),
                      "side": (0.69, 0.28, 0.3, 0.45)}
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
        ax.set_xlim(-9.5, 9.5)
        ax.set_ylim(-9.5, 9.5) if v == "top" else ax.set_ylim(-4.5, 6.5)
        axes[v] = ax
        for k, polys in U.GEOM.items():
            for p in polys:
                mm = max(1, int(np.ceil(len(p) * prog)))
                ax.plot(*project(p[:mm], v), color=U.COL[k], lw=0.7)
    if dims > 0:
        a = smooth(dims)
        kw = dict(color=C["warn"], fontsize=9 * fs, alpha=a)
        at = axes["top"]
        at.annotate("", (8, 0), (-8, 0), arrowprops=dict(arrowstyle="<->", color=C["warn"], alpha=a))
        at.text(-3, 0.4, "直径 16", **kw)
        at.text(2.5, -6.2, "反重力リング R 6.5", color=U.COL["ring"], fontsize=9 * fs, alpha=a)
        af = axes["front"]
        af.annotate("", (-8.8, 5.1), (-8.8, -2.2 - 1.6), arrowprops=dict(arrowstyle="<->", color=C["warn"], alpha=a))
        af.text(-8.5, 4.2, "全高 8.9", **kw)
        af.text(2.2, -3.6, "貯槽 r 1.6", color=U.COL["res"], fontsize=9 * fs, alpha=a)
        af.text(0.4, 5.3, "安定灯", color=U.COL["safe"], fontsize=9 * fs, alpha=a)
    return axes


def s_plan(fig, u, sec):
    grid_bg(fig)
    draw_plan(fig, smooth(u / 0.7), (u - 0.7) / 0.2)
    if u > 0.75:
        fig.text(0.38, 0.14, "寸法はレポートに記載がないため図解用。質量 m = 1.2×10⁴ kg は UFO.16 より。",
                 color=C["warn"], fontsize=11, alpha=smooth((u - 0.75) * 6))


def s_to3d(fig, u, sec):
    s = smooth(u / 0.8)
    ax = add_3d(fig, elev=89.9 - (89.9 - 22) * s, azim=-90 + 30 * s)
    draw_all(ax, zscale=max(s, 1e-3))
    fig.text(0.03, 0.86, f"z ← s · z(断面),  s = {s:0.2f}", color=C["hud"], fontsize=14)
    fig.text(0.03, 0.82, "上面図を起こしてレンズ断面を回転体として復元", color=FG, fontsize=12)


EXPLODE = {"hull": (0, 0, 0), "core": (0, 0, 8), "res": (0, 0, -8), "ring": (0, 0, -6), "tuner": (0, 0, 6),
           "stab": (10, 0, 0), "port": (0, 0, -9), "sensor": (0, 0, 9), "fc": (-10, 0, 4), "safe": (0, 0, 10)}


def s_assembly(fig, u, sec):
    n = len(U.ASSEMBLY_ORDER)
    step = u * n
    cur = min(int(step), n - 1)
    f = smooth((step - cur) / 0.6)
    ax = add_3d(fig, (0.0, 0.0, 0.62, 1.0), elev=22, azim=-60 + 40 * u, zoom=1.35)
    for i, k in enumerate(U.ASSEMBLY_ORDER[:cur + 1]):
        if i < cur:
            draw(ax, U.GEOM[k], U.COL[k], 0.9, 0.9)
        else:
            draw(ax, U.GEOM[k], U.COL[k], 1.6, 0.25 + 0.75 * f, offset=np.asarray(EXPLODE[k]) * (1 - f))
    k = U.ASSEMBLY_ORDER[cur]
    _, name, ids, eqs, note = next(p for p in U.PARTS if p[0] == k)
    col = U.COL[k]
    a = 0.35 + 0.65 * smooth((step - cur) / 0.25)
    fig.add_artist(plt.Rectangle((0.6, 0.30), 0.38, 0.52, fc=BG, ec=col, lw=1.5, alpha=0.9))
    fig.text(0.615, 0.77, f"部品 {cur + 1}/{n}   " + ", ".join(ids), color=col, fontsize=11, alpha=a)
    fig.text(0.615, 0.72, name, color=FG, fontsize=16, weight="bold", alpha=a)
    for j, ln in enumerate(eqs + [note]):
        fig.text(0.615, 0.64 - j * 0.08, ln, color=FG, fontsize=12, alpha=a)
    for i, kk in enumerate(U.ASSEMBLY_ORDER):
        done = i < cur or (i == cur and f > 0.99)
        fig.text(0.615 + (i % 2) * 0.18, 0.24 - (i // 2) * 0.037,
                 ("■ " if done else "□ ") + U.PART_NAME[kk].split(" (")[0],
                 color=C["hud"] if done else GRID, fontsize=10)


def sim_state(t):
    """t ∈ [0, 10] 秒 の状態 (ステップ間は線形補間)."""
    k = int(np.clip(np.floor(t), 0, 9))
    f = np.clip(t - k, 0, 1)
    a, b = U.SIM[k], U.SIM[k + 1]
    return {key: a[key] + (b[key] - a[key]) * f for key in ("h", "v", "x", "L", "a", "Eag")}, k + (1 if f >= 1 else 0)


def s_flight(fig, u, sec):
    # 0–0.12 起動 / 0.12–0.82 10 ステップ上昇 / 0.82– 安全確認
    tsim = np.clip((u - 0.12) / 0.7, 0, 1) * 10
    st, k = sim_state(tsim)
    glow = smooth(u / 0.12) * (0.6 + 0.4 * np.sin(sec * 9))
    ax = add_3d(fig, (0.0, 0.0, 0.58, 1.0), elev=14, azim=-60 + 15 * u, zoom=1.25, zr=(-14, 7))
    ground = -3.5 - st["h"] / 60.0  # 地面が下がって見える
    if ground > -14:
        for v in np.linspace(-10, 10, 11):
            ax.plot([v, v], [-10, 10], [ground] * 2, color=GRID, lw=0.8)
            ax.plot([-10, 10], [v, v], [ground] * 2, color=GRID, lw=0.8)
    draw_all(ax, 0.9, 1.0, glow=glow)
    for aa in np.linspace(0, 2 * np.pi, 16, endpoint=False):  # 反重力場 (L − 1 に比例)
        x0, y0 = 6.5 * np.cos(aa), 6.5 * np.sin(aa)
        ln = 2 + 2 * (st["L"] - 1)
        ax.plot([x0, x0 * 0.9], [y0, y0 * 0.9], [-1.5, -1.5 - ln], color=U.COL["ring"], lw=0.8, alpha=0.5 * glow)
    # 制御コード (UFO_OS) — 評価中の行を強調
    fig.text(0.58, 0.895, "UFO_OS.om  controlGravityDrive()", color=C["hud"], fontsize=12)
    active = 1 + int((sec * 3) % 5) if 0.12 < u < 0.82 else (6 + int((sec * 2) % 3) if u >= 0.82 else -1)
    for i, (line, eid) in enumerate(U.UFO_OS):
        y = 0.86 - i * 0.031
        on = i == active
        fig.text(0.58, y, line, color=C["warn"] if on else FG, fontsize=10, alpha=1 if on else 0.75,
                 family="IPAGothic")
        if eid:
            fig.text(0.9, y, eid, color=C["warn"] if on else GRID, fontsize=9)
    # 代入された方程式 (毎ステップ評価)
    y0 = 0.44
    eqs = [
        (f"x = 2√(r0/(r0+h)) = {st['x']:.6f}", U.COL["sensor"]),
        (f"L = cosh(x log x) = {st['L']:.5f}", U.COL["ring"]),
        (f"a = (L − 1)·g_eff = {st['a']:.4f} m/s²", U.COL["fc"]),
        (f"E_ag = U·L = {st['Eag']:.5e} J  ≥ U ✓", U.COL["core"]),
        (f"v = {st['v']:7.2f} m/s     h = {st['h']:7.1f} m", FG),
    ]
    fig.text(0.58, y0 + 0.045, f"ステップ k = {min(k, 10):2d} / 10   (dt = 1 s)", color=C["hud"], fontsize=13)
    for i, (t, col) in enumerate(eqs):
        fig.text(0.58, y0 - i * 0.045, t, color=col, fontsize=13)
    # 高度グラフ
    g = fig.add_axes([0.62, 0.06, 0.34, 0.13])
    g.set_facecolor(BG)
    for s in g.spines.values():
        s.set_color(GRID)
    g.tick_params(colors=FG, labelsize=7)
    ks = [r["k"] for r in U.SIM]
    g.plot(ks, [r["h"] for r in U.SIM], color=GRID, lw=1)
    kk = np.linspace(0, tsim, 50)
    g.plot(kk, [sim_state(t)[0]["h"] for t in kk], color=C["warn"], lw=2)
    g.set_xlim(0, 10)
    g.set_ylim(0, 650)
    g.set_title("高度 h [m] — 10 s 後 607.5 m (UFO.24)", color=FG, fontsize=9)
    if u >= 0.82:
        a = smooth((u - 0.82) * 8)
        fig.text(0.03, 0.2, f"貯槽 残量 {U.RES[-1] * 100:.4f} % ≥ 99.9 %  ✓ (UFO.25)", color=U.COL["res"],
                 fontsize=13, alpha=a)
        fig.text(0.03, 0.15, f"Δ = e^π − π^e = {U.V['delta']:.4f} < 1  ✓ (UFO.26)  → 巡航許可",
                 color=U.COL["safe"], fontsize=13, alpha=a)
    elif u < 0.12:
        fig.text(0.03, 0.2, "反重力リング励磁中:  □ag(x) = 2(sin(i x log x) + cos(i x log x))", color=U.COL["ring"],
                 fontsize=13)


def s_end(fig, u, sec):
    grid_bg(fig)
    ax = add_3d(fig, (0.25, 0.28, 0.5, 0.62), elev=18, azim=-60 + 20 * sec, zoom=1.2)
    draw_all(ax, 0.8, 0.7 * smooth(u * 3))
    a = smooth(u * 3 - 0.3)
    fig.text(0.5, 0.2, "方程式 26 本 → 部品 10 点 → 平面図 → 3D → 組み立て → 飛行 (方程式を毎秒評価)",
             color=FG, fontsize=15, ha="center", alpha=a)
    fig.text(0.5, 0.09, "※ 論文の方程式に基づく思索的・フィクションの設計図です。実在の反重力装置ではありません。",
             color=C["warn"], fontsize=12, ha="center", alpha=a)


SCENES = {"title": s_title, "params": s_params, "mapping": s_mapping, "plan": s_plan, "to3d": s_to3d,
          "assembly": s_assembly, "flight": s_flight, "end": s_end}


def frame(i):
    sec = i / FPS
    name, u, local = TL.at(sec)
    fig = new_fig()
    SCENES[name](fig, u, local)
    if name != "title":
        header(fig, name, sec)
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
    base = 0.08 * np.sin(2 * np.pi * 73.4 * t) + 0.04 * np.sin(2 * np.pi * 110 * t)
    f0 = TL.start("flight")
    ramp = np.clip((t - f0) / 4, 0, 1) * (t < TL.start("end"))
    f = 180 + 60 * np.sin(2 * np.pi * 0.5 * t)
    hum = 0.09 * ramp * np.sin(2 * np.pi * np.cumsum(f) / sr)
    env = np.clip(t / 2, 0, 1) * np.clip((TL.total - t) / 2, 0, 1)
    write_wav(path, (base + hum) * env)


def main():
    if "--preview" in sys.argv:
        from PIL import Image
        os.makedirs(os.path.join(OUT, "preview"), exist_ok=True)
        for name, t0, dur in TL.scenes:
            for frac in (0.05, 0.5, 0.9):
                i = int((t0 + dur * frac) * FPS)
                Image.fromarray(frame(i)).save(os.path.join(OUT, "preview", f"ufo_{name}_{int(frac*100)}.png"))
        return
    wav = os.path.join(OUT, "_ufo.wav")
    soundtrack(wav)
    render_video(os.path.join(OUT, "ufo_blueprint.mp4"), N_FRAMES, frame, audio_wav=wav)
    os.remove(wav)
    print("done", N_FRAMES, "frames")


if __name__ == "__main__":
    main()
