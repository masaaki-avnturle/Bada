#!/usr/bin/env python3
"""Animate the Bada-generated Contact transporter blueprint to MP4.

Reads contact_machine.obj (geometry) and contact_data.txt (numbers) written by
the Bada program, renders a point-cloud animation with numpy + matplotlib and
encodes it with ffmpeg (PATH or imageio-ffmpeg).

    python3 tools/make_video.py [out.mp4] [--fps 30] [--seconds 46]
"""
import argparse
import math
import shutil
import subprocess

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

W, H = 1280, 720
BG = "#04060a"
GOLD, BLUE, VIOLET, CYAN, RED, ORANGE, SILVER, STEEL = (
    "#c8a44a", "#4a80d0", "#9060d0", "#40b8c0", "#ff5050", "#ff9040", "#e8e8f0", "#5a6270")


def set_font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    fam = [n for n in ("IPAGothic", "IPAexGothic", "Noto Sans CJK JP", "WenQuanYi Zen Hei") if n in names]
    plt.rcParams["font.family"] = fam + ["DejaVu Sans"]


def load_obj(path):
    groups, verts, cur = {}, [], None
    for line in open(path):
        if line.startswith("g "):
            cur = line.split(None, 1)[1].strip()
            groups[cur] = [len(verts), len(verts)]
        elif line.startswith("v "):
            verts.append([float(t) for t in line.split()[1:4]])
            groups[cur][1] = len(verts)
    V = np.array(verts)
    return {g: V[a:b] for g, (a, b) in groups.items()}


def load_data(path):
    p, series, comps, jones = {}, {}, [], []
    for line in open(path, encoding="utf-8"):
        t = line.split()
        if not t:
            continue
        if t[0] == "param":
            p[t[1]] = float(t[2])
        elif t[0] == "series":
            series.setdefault(t[1], []).append((float(t[2]), float(t[3])))
        elif t[0] == "comp":
            comps.append((t[1], int(float(t[2])), float(t[3])))
        elif t[0] == "jones":
            jones.append(line.split(None, 2)[2].strip())
    return p, {k: np.array(v) for k, v in series.items()}, comps, jones


def densify(pts, ring, steps):
    """Cylinders/tubes are stored as vertex rings; interpolate between rings."""
    R = pts.reshape(-1, ring, 3)
    out = []
    for a, b in zip(R[:-1], R[1:]):
        for u in np.linspace(0, 1, steps, endpoint=False):
            out.append(a + (b - a) * u)
    out.append(R[-1])
    return np.vstack(out)


def rot(axis, a):
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def fmt_hms(sec):
    sec = int(sec)
    return "%02d:%02d:%02d" % (sec // 3600, sec // 60 % 60, sec % 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="contact_transporter.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float, default=46)
    ap.add_argument("--obj", default="contact_machine.obj")
    ap.add_argument("--data", default="contact_data.txt")
    a = ap.parse_args()
    set_font()
    G = load_obj(a.obj)
    P, S, comps, jones = load_data(a.data)
    gamma = P["gamma"]
    wo, wm, wi = P["omega_outer"], P["omega_middle"], P["omega_inner"]
    top_z = P["tower_h"] + 6

    static, colors, sizes = [], [], []

    def add(pts, col, size):
        static.append(pts); colors.append(col); sizes.append(size)

    for g, pts in G.items():
        if g.startswith("tower") or g.startswith("gantry") or g == "drop_shaft":
            add(densify(pts, len(pts) // 2, 60), "#7a8494", 1.4)
        elif g.startswith("jones_coil_3_1"):
            add(pts, BLUE, 1.0)
        elif g.startswith("jones_coil_5_1"):
            add(pts, VIOLET, 1.0)
        elif g.startswith("jones_coil_4_1"):
            add(pts, CYAN, 1.0)
    rings = {k: G["gimbal_" + k] for k in ("outer", "middle", "inner")}
    pod0 = G["pod"]
    beam = densify(G["door_axis_beam"], 8, 30)
    windows = [v for k, v in G.items() if k.startswith("resonance_window")]

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    def project(X, az, el, dist):
        R = rot("x", -el) @ rot("z", -az)
        Y = X @ R.T
        # camera looks along +y after rotation: screen x = Y[:,0], screen y = Y[:,2]
        z = dist + Y[:, 1]
        f = 620 / z
        return np.c_[W * 0.5 + Y[:, 0] * f * 1.85, H * 0.34 + Y[:, 2] * f * 1.85], z

    exe = ffmpeg_exe()
    proc = subprocess.Popen([exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                             "-s", "%dx%d" % (W, H), "-r", str(a.fps), "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                             "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    n = int(a.seconds * a.fps)
    captions = [
        (5, "① ジュネーブ CERN の衝突 (Linac4 → LHC, √s = 13.6 TeV)",
         "粒子が消えた方向 = 異次元への扉の軸  n̂ = (%.3f, %.3f, %.3f)   E_T^miss = %.0f GeV"
         % (P["door_x"], P["door_y"], P["door_z"], P["met"])),
        (9, "② 特殊相対論: 地球の 1 秒 = 搭乗者の 18 時間",
         "Γ = %.0f   1−β = %.3g   ラピディティ φ = %.4f   ベガ片道 %.2f h"
         % (gamma, P["one_minus_beta"], P["rapidity"], P["one_way_h"])),
        (13, "③ 複素回転体(コマ): Θ = θ + iφ で回転する異次元",
         "3 環の角速度 ω = %.3f, %.3f, %.3f rad/s   輸送計量のワープ exp(−2πT|ψ|) = 1/Γ → T|ψ| = %.5f"
         % (wo, wm, wi, P["tpsi"])),
        (17, "④ ガンマ関数におけるゼータ関数の大域的部分積分多様体",
         "Riemann–Siegel θ(φ) = %.4f    Z(φ) = exp(iθ)·ζ(½ + iφ) = %.4f  (実数)" % (P["rs_theta"], P["rs_Z"])),
        (21, "⑤ Jones 多項式 = 設計図生成機能  (t* = exp(iθ(φ)))",
         "3_1: %s    4_1: %s" % (jones[0].split("|")[0].strip(), jones[1].split("|")[0].strip())),
        (25, "⑥ 論文 15 本の全方程式 %d 本 → 部品へ割り当て" % P["reg_n"],
         "数値評価 %d 本 / 等式の数値検証: 成立 %d・不成立 %d (論文の式はそのまま)"
         % (P["reg_calc"], P["reg_hold"], P["reg_fail"])),
    ]
    T_DROP0, T_DROP1, T_DOOR0, T_DOOR1, T_BACK = 29.0, 34.0, 34.0, 37.0, 40.0
    for i in range(n):
        t = i / a.fps
        ax.clear(); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
        az = math.radians(-60 + 8 * t)
        el = math.radians(18 + 6 * math.sin(t * 0.2))
        spin = smooth((t - 4) / 14)                      # ring spin-up
        ang = lambda w: w * (t - 4) * spin if t > 4 else 0.0
        Ro = rot("x", ang(wo))
        Rm = Ro @ rot("y", ang(wm))
        Ri = Rm @ rot("x", ang(wi))
        pts = list(static); cols = list(colors); sz = list(sizes)
        pts += [rings["outer"] @ Ro.T, rings["middle"] @ Rm.T, rings["inner"] @ Ri.T]
        cols += [GOLD, GOLD, "#e0c060"]; sz += [2.2, 2.0, 1.8]
        # pod
        if t < T_DROP0:
            pz = top_z
        elif t < T_DROP1:
            pz = top_z * (1 - smooth((t - T_DROP0) / (T_DROP1 - T_DROP0)))
        else:
            pz = 0.0
        pod_vis = not (T_DOOR0 + 0.6 < t < T_BACK)
        if pod_vis:
            pts.append(pod0 + np.array([0, 0, pz])); cols.append(SILVER); sz.append(3.0)
        door = smooth((t - T_DOOR0 + 1.0) / 1.0) * (1 - smooth((t - T_BACK) / 2.0))
        if door > 0:
            pts.append(beam); cols.append(RED); sz.append(2 + 10 * door)
            for w in windows:
                pts.append(w); cols.append(ORANGE); sz.append(2 + 8 * door)
        X = np.vstack(pts)
        C = np.concatenate([np.repeat(np.array([matplotlib.colors.to_rgba(c)]), len(p), 0)
                            for c, p in zip(cols, pts)])
        Sz = np.concatenate([np.full(len(p), s) for s, p in zip(sz, pts)])
        xy, z = project(X, az, el, 420)
        order = np.argsort(-z)
        shade = np.clip(1.25 - (z - z.min()) / (np.ptp(z) + 1e-9) * 0.7, 0.35, 1.0)
        C[:, :3] *= shade[:, None]
        intro = smooth(t / 2.0)
        C[:, 3] = intro
        ax.scatter(xy[order, 0], xy[order, 1], s=Sz[order], c=C[order], linewidths=0)
        # flash when the door opens
        if T_DOOR0 <= t <= T_DOOR0 + 1.2:
            f = 1 - abs((t - T_DOOR0 - 0.6) / 0.6)
            ax.add_patch(plt.Rectangle((0, 0), W, H, color="white", alpha=0.85 * max(f, 0)))
        # title card
        if t < 5:
            al = smooth(t / 1.0) * (1 - smooth((t - 4.0) / 1.0))
            ax.text(W / 2, H * 0.80, "CONTACT TRANSPORTER", color=GOLD, fontsize=40, ha="center",
                    alpha=al, weight="bold")
            ax.text(W / 2, H * 0.73, "異次元への輸送機 — 量子プログラミング言語 Bada による 3 次元設計図",
                    color=SILVER, fontsize=18, ha="center", alpha=al)
            ax.text(W / 2, H * 0.68, "複素回転体(コマ) × 特殊相対論 × Γ・ζ 大域的部分積分多様体 × Jones 多項式",
                    color=CYAN, fontsize=14, ha="center", alpha=al)
        # stage captions
        for (t0, head, body) in captions:
            if t0 <= t < t0 + 4:
                al = smooth((t - t0) / 0.5) * (1 - smooth((t - t0 - 3.5) / 0.5))
                ax.add_patch(plt.Rectangle((40, 28), W - 80, 92, color="#0b1220", alpha=0.8 * al))
                ax.text(60, 88, head, color=GOLD, fontsize=19, alpha=al, weight="bold")
                ax.text(60, 48, body, color=SILVER, fontsize=13, alpha=al)
        # pod drop & clocks
        if T_DROP0 - 0.5 <= t < T_BACK + 2:
            al = smooth((t - T_DROP0 + 0.5) / 0.5) * (1 - smooth((t - T_BACK - 1.5) / 0.5))
            ax.text(60, 88, "ポッド投下 → 扉 (消失方向) を通過", color=GOLD, fontsize=19, alpha=al,
                    weight="bold")
            earth = min(max(t - T_DOOR0, 0.0), 1.0)          # 1 real second at the door
            trav = earth * gamma
            ax.text(60, 48, "地球の時計  %.3f s" % earth, color=CYAN, fontsize=18, alpha=al)
            ax.text(460, 48, "搭乗者の時計  %s" % fmt_hms(trav), color=ORANGE, fontsize=18, alpha=al)
            ax.text(900, 48, "Γ = %.0f" % gamma, color=SILVER, fontsize=18, alpha=al)
        # end card
        if t >= T_BACK + 2:
            al = smooth((t - T_BACK - 2) / 1.0)
            ax.add_patch(plt.Rectangle((0, 0), W, H, color=BG, alpha=0.75 * al))
            ax.text(W / 2, H * 0.72, "設計図 生成完了", color=GOLD, fontsize=34, ha="center", alpha=al,
                    weight="bold")
            lines = ["外環 R = %.1f m / 中環 R = %.1f m / 内環 R = %.1f m / ポッド r = %.1f m"
                     % (P["R_out"], P["R_mid"], P["R_in"], P["pod_r"]),
                     "塔高 %.1f m / 井戸深さ %.1f m / Jones コイル R = %.1f m"
                     % (P["tower_h"], P["well_depth"], P["coil_r"]),
                     "論文の全方程式 %d 本 (数値評価 %d 本)" % (P["reg_n"], P["reg_calc"]),
                     "source: contact_transporter/contact_blueprint.bada",
                     "※ 論文の式に基づく思索的な設計図の可視化であり、実在の装置ではありません"]
            for k, s in enumerate(lines):
                ax.text(W / 2, H * 0.60 - k * 38, s, color=SILVER if k < 4 else "#9098a8",
                        fontsize=16 if k < 4 else 13, ha="center", alpha=al)
        fig.canvas.draw()
        proc.stdin.write(bytes(fig.canvas.buffer_rgba()))
        if i % (a.fps * 5) == 0:
            print("frame %d/%d" % (i, n), flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
