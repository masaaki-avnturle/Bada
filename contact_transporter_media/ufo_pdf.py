"""UFO (反重力機) の設計図 PDF — output/ufo_blueprint.pdf."""
import os
import warnings

import numpy as np

from common import BG, C, FG, GRID, OUT
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from blueprint_pdf import page, iso_axes, balloon, styled, disclaimer
import ufo_model as U
import ufo_video as UV

warnings.filterwarnings("ignore")
plt.rcParams["pdf.fonttype"] = 42
BRAND = "UFO BLUEPRINT — 反重力機 3D 設計図"
NOTE = "※ 論文の方程式 (UFO.1–26) に基づく思索的・フィクションの設計図です。実在の反重力装置ではありません。外形寸法は図解用。"
N = 8


def save(pdf, fig):
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def cover(pdf):
    fig = page(None, None, 1, N, BRAND)
    fig.text(0.05, 0.84, "UFO BLUEPRINT", color=FG, fontsize=34, weight="bold")
    fig.text(0.05, 0.785, "反重力機  3 次元設計図 (部品表・方程式対応表・組立図・飛行制御)", color=C["hud"], fontsize=15)
    lines = [
        "原典: contact_blueprint.pdf の方程式レジストリ UFO.1–UFO.26 (26 本)",
        "      src/UFO_OS.om — 反重力発生器の制御 OS (controlGravityDrive)",
        "原理: 重力ポテンシャル U = GMm/r を、多様体座標 x の反重力係数 α_ag = cosh(x log x) ≥ 1 で増幅",
        "      揚力比 L = E_ag/U = cosh(x log x) = 2.125 (地表)、上昇加速度 a = (L − 1)·g_eff = 11.047 m/s²",
        "機体: m = 1.2×10⁴ kg (UFO.16)、10 秒で高度 607.5 m・速度 110.45 m/s (UFO.24)",
    ]
    for i, l in enumerate(lines):
        fig.text(0.05, 0.71 - i * 0.04, l, color=FG, fontsize=10.5)
    ax = iso_axes(fig, (0.5, 0.08, 0.48, 0.5), 10, (-7, 7), 20, -58, 1.3)
    UV.draw_all(ax, 0.7)
    toc = ["01 表紙", "02 方程式と再計算", "03 部品 ↔ 方程式 対応表", "04 三面図", "05 3D 等角図・分解組立図",
           "06 飛行制御 (UFO_OS と方程式)", "07 飛行シミュレーション", "08 注記"]
    fig.text(0.05, 0.47, "目次", color=C["hud"], fontsize=11, weight="bold")
    for i, t in enumerate(toc):
        fig.text(0.05, 0.43 - i * 0.035, t, color=FG, fontsize=9.5)
    disclaimer(fig, NOTE, 0.1)
    save(pdf, fig)


def params(pdf):
    fig = page("1. 方程式と再計算", "本書の Python (ufo_model.py) で再計算し、レポートの値と照合", 2, N, BRAND)
    V = U.V
    rows = [
        ("UFO.1", "U = GMm/r (r = r0)", f"{V['U']:.5e} J", "7.50723e+11"),
        ("UFO.3/16", "E⊥ = mc² − ½mv² (m = 1.2e4 kg, v = 1e4 m/s)", f"{V['Eperp']:.5e} J", "1.07851e+21"),
        ("UFO.4", "□dal(x) = e^{x log x} = x^x (x = 2)", f"{V['xx2']:.0f}", "4"),
        ("UFO.5", "dμ(x) = 1/(x log x)² (x = 2)", f"{V['dmu']:.6f}", "0.520342"),
        ("UFO.9", "β(p,q) = Γ(p)Γ(q)/Γ(p+q) (2,3)", f"{V['beta']:.7f}", "0.0833333"),
        ("UFO.11/19", "L = α_ag = cosh(x log x), x = 2", f"{V['L0']:.5f}", "2.125"),
        ("UFO.13", "E_ag = (GMm/r)·cosh(x log x)", f"{V['Eag']:.5e} J", "1.59529e+12"),
        ("UFO.19", "a = (L − 1)·g_eff", f"{V['a0']:.4f} m/s²", "11.047"),
        ("UFO.22", "›- : e^{−x log x} (x = 2)", f"{V['eneg']:.2f}", "0.25"),
        ("UFO.23", "L(1 km)", f"{V['L1']:.5f}", "2.12450"),
        ("", "L(5 km) / L(20 km)", f"{V['L5']:.5f} / {V['L20']:.5f}", "2.12251 / 2.11510"),
        ("", "L(100 km)", f"{V['L100']:.5f}", "2.07677"),
        ("UFO.24", "10 ステップ後 (dt = 1 s)", f"{V['h10']:.1f} m, {V['v10']:.2f} m/s", "607.6 m, 110.46 m/s"),
        ("UFO.25", "貯槽 5 倍 × 10 回引き出し後", f"{U.RES[-1]*100:.4f} %", "≥ 99.9 %"),
        ("UFO.18/26", "Δ = e^π − π^e", f"{V['delta']:.4f}  (< 1)", "0.6815"),
    ]
    xs = [0.04, 0.14, 0.53, 0.75]
    for j, h in enumerate(["式 ID", "方程式・条件", "再計算", "レポート値"]):
        fig.text(xs[j], 0.86, h, color=C["hud"], fontsize=10.5, weight="bold")
    for i, r in enumerate(rows):
        y = 0.825 - i * 0.045
        for j, v in enumerate(r):
            fig.text(xs[j], y, v, color=C["warn"] if j == 0 else (U.COL["safe"] if j == 3 else FG), fontsize=9.5)
        fig.add_artist(plt.Line2D([0.035, 0.96], [y - 0.012, y - 0.012], color=GRID, lw=0.5))
    fig.text(0.04, 0.115, "x = manifold_coord(r0/r) = 2√(r0/r) (r0 = 6.371×10⁶ m) とおくと L(h) と上昇軌道がレポートと一致する"
             " (L(100 km) は 5 桁目で差 0.0002)。", color=FG, fontsize=8.5)
    save(pdf, fig)


def mapping(pdf):
    fig = page("2. 部品 ↔ 方程式 対応表", "26 本すべてを 10 部品に割り当て", 3, N, BRAND)
    for j, h in enumerate(["No.", "部品", "式 ID", "支配方程式", "寸法・備考"]):
        fig.text([0.035, 0.065, 0.2, 0.33, 0.8][j], 0.87, h, color=C["hud"], fontsize=10, weight="bold")
    for i, (k, name, ids, eqs, note) in enumerate(U.PARTS):
        y = 0.83 - i * 0.075
        col = U.COL[k]
        fig.text(0.04, y, str(i + 1), color=col, fontsize=11, weight="bold")
        fig.text(0.065, y, name, color=col, fontsize=10, weight="bold")
        fig.text(0.2, y, "\n".join(", ".join(ids[j:j + 3]) for j in range(0, len(ids), 3)), color=FG, fontsize=8.5,
                 va="top")
        for j, eq in enumerate(eqs):
            fig.text(0.33, y - j * 0.028, eq, color=FG, fontsize=9)
        fig.text(0.8, y, note, color=FG, fontsize=8.5)
        fig.add_artist(plt.Line2D([0.03, 0.965], [y - 0.048, y - 0.048], color=GRID, lw=0.5))
    save(pdf, fig)


def plan(pdf):
    fig = page("3. 三面図 (単位 m)", "寸法は図解用 (レポートに外形寸法の記載なし)", 4, N, BRAND)
    UV.draw_plan(fig, 1.0, 1.0, rects={"top": (0.03, 0.12, 0.38, 0.74), "front": (0.43, 0.45, 0.27, 0.38),
                                       "side": (0.71, 0.45, 0.27, 0.38)})
    for i, (k, name, *_r) in enumerate(U.PARTS):
        fig.text(0.44 + (i % 2) * 0.26, 0.36 - (i // 2) * 0.04, "■ " + name, color=U.COL[k], fontsize=9)
    save(pdf, fig)


def iso(pdf):
    fig = page("4. 3D 等角図・分解組立図", "右図の番号 = 組立順", 5, N, BRAND)
    ax = iso_axes(fig, (0.0, 0.15, 0.42, 0.7), 10, (-7, 7), 22, -58, 1.35)
    UV.draw_all(ax, 0.7)
    ax2 = iso_axes(fig, (0.36, 0.06, 0.42, 0.86), 13, (-14, 16), 16, -58, 1.35)
    off = {k: np.asarray(v) * 0.8 for k, v in UV.EXPLODE.items()}
    UV.draw_all(ax2, 0.6, offset=off)
    fig.canvas.draw()
    for i, k in enumerate(U.ASSEMBLY_ORDER):
        balloon(ax2, fig, np.concatenate(U.GEOM[k]).mean(0) + off[k], i + 1, U.COL[k])
    for i, k in enumerate(U.ASSEMBLY_ORDER):
        fig.text(0.79, 0.85 - i * 0.07, f"{i + 1}. {U.PART_NAME[k]}", color=U.COL[k], fontsize=10, weight="bold")
    save(pdf, fig)


def control(pdf):
    fig = page("5. 飛行制御 — UFO_OS と方程式", "src/UFO_OS.om の controlGravityDrive() に各方程式を実装", 6, N, BRAND)
    for i, (line, eid) in enumerate(U.UFO_OS):
        y = 0.83 - i * 0.045
        fig.text(0.05, y, line, color=FG, fontsize=12)
        if eid:
            e = next(x for x in U.UFO_EQS if x["id"] == eid)
            fig.text(0.45, y, eid, color=C["warn"], fontsize=10)
            fig.text(0.53, y, e["eq"][:70], color=C["hud"], fontsize=8.5)
    fig.text(0.05, 0.33, "制御の流れ", color=C["hud"], fontsize=11, weight="bold")
    flow = ["① センサ: 高度 h → 多様体座標 x = 2√(r0/(r0+h))",
            "② 反重力リング: α_ag = L = cosh(x log x)",
            "③ 重力結合コア: E_ag = U·L ≥ U を確認",
            "④ 推力: a = (L − 1)·GM/r²,  v ← v + a dt,  h ← h + v dt",
            "⑤ 貯槽 ≥ 99.9 %、Δ = e^π − π^e < 1 を満たす限り継続"]
    for i, l in enumerate(flow):
        fig.text(0.06, 0.29 - i * 0.035, l, color=FG, fontsize=10)
    save(pdf, fig)


def flight(pdf):
    fig = page("6. 飛行シミュレーション", "UFO.24 の 10 ステップ上昇を方程式どおりに計算 (dt = 1 s)", 7, N, BRAND)
    cols = ["k", "t [s]", "h [m]", "v [m/s]", "x", "L = cosh(x log x)", "a [m/s²]", "E_ag [J]"]
    xs = [0.04, 0.08, 0.13, 0.21, 0.29, 0.38, 0.5, 0.59]
    for j, h in enumerate(cols):
        fig.text(xs[j], 0.86, h, color=C["hud"], fontsize=9, weight="bold")
    for i, r in enumerate(U.SIM):
        y = 0.83 - i * 0.034
        vals = [str(r["k"]), f"{r['k']:.0f}", f"{r['h']:.2f}", f"{r['v']:.3f}", f"{r['x']:.6f}", f"{r['L']:.6f}",
                f"{r['a']:.4f}", f"{r['Eag']:.5e}"]
        for j, v in enumerate(vals):
            fig.text(xs[j], y, v, color=FG, fontsize=9)
    ax = fig.add_axes([0.72, 0.52, 0.25, 0.33])
    styled(ax, "高度 h と速度 v")
    ax.plot([r["k"] for r in U.SIM], [r["h"] for r in U.SIM], color=C["warn"], marker="o", ms=3, label="h [m]")
    ax.plot([r["k"] for r in U.SIM], [r["v"] for r in U.SIM], color=U.COL["sensor"], marker="o", ms=3, label="v [m/s]")
    ax.legend(fontsize=7, facecolor=BG, labelcolor=FG, edgecolor=GRID)
    ax = fig.add_axes([0.06, 0.15, 0.4, 0.25])
    styled(ax, "揚力比 L(h) = cosh(x log x) (UFO.23)")
    hh = np.linspace(0, 1e5, 300)
    ax.plot(hh / 1e3, U.lift(hh), color=U.COL["ring"])
    for h, v in ((0, 2.125), (1, 2.1245), (5, 2.12251), (20, 2.1151), (100, 2.07677)):
        ax.scatter(h, v, color=C["warn"], s=14, zorder=5)
    ax.set_xlabel("高度 [km]  (● = レポート値)", color=FG, fontsize=8)
    ax = fig.add_axes([0.55, 0.15, 0.4, 0.25])
    styled(ax, "真空エネルギー貯槽の残量 (UFO.25)")
    ax.plot(range(len(U.RES)), U.RES * 100, color=U.COL["res"], marker="o", ms=3)
    ax.axhline(99.9, color=C["axis"], ls="--", lw=0.8)
    ax.set_ylim(99.85, 100.01)
    ax.set_xlabel("引き出し回数", color=FG, fontsize=8)
    save(pdf, fig)


def notes(pdf):
    fig = page("7. 注記", None, 8, N, BRAND)
    ls = [
        "・方程式・数値の根拠は contact_blueprint.pdf の UFO.1–UFO.26 (本書 2 章で全 26 本を部品に割り当て)。",
        "・x = manifold_coord(r0/r) は 2√(r0/r) と解釈した。この解釈で UFO.23 の L(h) と UFO.24 の上昇軌道を再現できる。",
        "・貯槽の容量 (UFO.25) はレポートに数値がないため図解用の値 (10⁶ 単位) を用いた。",
        "・外形寸法 (直径 16 m など) は図解用。質量 1.2×10⁴ kg のみレポート (UFO.16) による。",
        "・生成スクリプト: contact_transporter_media/ (ufo_model.py, ufo_video.py, ufo_pdf.py)",
        "",
        NOTE,
    ]
    for i, l in enumerate(ls):
        fig.text(0.05, 0.84 - i * 0.05, l, color=C["warn"] if l == NOTE else FG, fontsize=10)
    save(pdf, fig)


def build():
    path = os.path.join(OUT, "ufo_blueprint.pdf")
    with PdfPages(path) as pdf:
        for f in (cover, params, mapping, plan, iso, control, flight, notes):
            f(pdf)
        d = pdf.infodict()
        d["Title"] = "UFO 3D Blueprint"
        d["Author"] = "masaaki-avnturle / Bada"
    return path


if __name__ == "__main__":
    print(build())
