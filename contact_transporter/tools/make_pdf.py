#!/usr/bin/env python3
"""Build the blueprint document (PDF) from the Bada outputs.

Inputs : contact_machine.obj, contact_data.txt, contact_blueprint.txt
Output : contact_blueprint.pdf  (cover, parameters, orthographic blueprint
         views, charts, and the full equation registry)

    python3 tools/make_pdf.py [out.pdf]
"""
import re
import sys
import textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from make_video import densify, load_obj, load_data, set_font  # noqa: E402

A4 = (8.27, 11.69)
NAVY, WHITE, GOLD, CYAN = "#0d2a52", "#e8f0ff", "#c8a44a", "#40b8c0"
GROUP_COL = [("gimbal", "#ffd27a"), ("pod", "#ffffff"), ("tower", "#b8c8e8"), ("gantry", "#b8c8e8"),
             ("drop", "#b8c8e8"), ("jones_coil_3_1", "#7fb0ff"), ("jones_coil_5_1", "#c8a0ff"),
             ("jones_coil_4_1", "#70e0e8"), ("door", "#ff7070"), ("resonance", "#ffb070")]


def gcol(g):
    for k, c in GROUP_COL:
        if g.startswith(k):
            return c
    return WHITE


def parse_registry(path):
    """Entries from contact_blueprint.txt: (id, status, eq, value, tags, gloss)."""
    out, cur = [], None
    head = re.compile(r"^  (\S+) \[(\w+)\] (.*)$")
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = head.match(line)
        if m:
            cur = [m.group(1), m.group(2), m.group(3), "", "", ""]
            out.append(cur)
        elif cur and line.startswith("        = "):
            v, _, tags = line[10:].partition("    -> ")
            cur[3], cur[4] = v, tags
        elif cur and line.startswith("        -> "):
            tags, _, gloss = line[11:].partition("  (")
            cur[4], cur[5] = tags, gloss.rstrip(")")
    return out


def page(pdf, fig):
    pdf.savefig(fig)
    plt.close(fig)


def cover(pdf, P, preview):
    fig = plt.figure(figsize=A4, facecolor="white")
    fig.text(0.5, 0.93, "CONTACT TRANSPORTER", ha="center", fontsize=28, color=NAVY, weight="bold")
    fig.text(0.5, 0.895, "異次元への輸送機 3 次元設計図書", ha="center", fontsize=18, color=NAVY)
    fig.text(0.5, 0.87, "量子プログラミング言語 Bada (contact_transporter/contact_blueprint.bada) による生成",
             ha="center", fontsize=10, color="#445")
    ax = fig.add_axes([0.06, 0.42, 0.88, 0.42])
    ax.imshow(plt.imread(preview)); ax.axis("off")
    lines = [
        "原理: ジュネーブ CERN の衝突で粒子が消えた方向 = 異次元への扉",
        "      × 特殊相対論 (地球の 1 秒 = 搭乗者の 18 時間, Γ = %.0f)" % P["gamma"],
        "      × 複素回転体(コマ)の幾何学 (Θ = θ + iφ, φ = %.4f)" % P["rapidity"],
        "      × ガンマ関数におけるゼータ関数の大域的部分積分多様体 (Riemann–Siegel Z)",
        "      × Jones 多項式 = 設計図生成機能",
        "",
        "論文 15 本の全方程式: %d 本 (数値評価 %d 本 / 等式の数値検証 成立 %d・不成立 %d)"
        % (P["reg_n"], P["reg_calc"], P["reg_hold"], P["reg_fail"]),
        "",
        "※ 本書は論文の方程式に基づく思索的・フィクションの設計図 (幾何的な可視化) です。",
        "   工学的に検証された装置ではなく、異次元への輸送を可能にするものではありません。",
    ]
    for k, s in enumerate(lines):
        fig.text(0.08, 0.37 - k * 0.026, s, fontsize=10.5, color="#223")
    fig.text(0.5, 0.04, "masaaki-avnturle / Bada — contact_transporter", ha="center", fontsize=8, color="#667")
    page(pdf, fig)


def params_page(pdf, P, jones):
    fig = plt.figure(figsize=A4)
    fig.text(0.06, 0.95, "1. 設計パラメータ (Bada 実行結果)", fontsize=16, color=NAVY, weight="bold")
    rows = [
        ("① 衝突段", "√s = 13.6 TeV (Linac4 → PSB → PS → SPS → LHC)"),
        ("", "E_T^miss = %.2f GeV" % P["met"]),
        ("", "扉の軸 n̂ = (%.5f, %.5f, %.5f)" % (P["door_x"], P["door_y"], P["door_z"])),
        ("② 特殊相対論", "Γ = 18 h / 1 s = %.0f" % P["gamma"]),
        ("", "1 − β = %.6g,  ラピディティ φ = arcosh Γ = %.6f" % (P["one_minus_beta"], P["rapidity"])),
        ("", "ベガ 25.04 ly → 収縮距離 %.4g km,  片道 %.4f h" % (P["contracted_km"], P["one_way_h"])),
        ("②' 輸送計量", "ds² = e^{−2πT|ψ|}[η+h̄]dx^μdx^ν + T²dψ²"),
        ("", "e^{−2πT|ψ|} = 1/Γ → T|ψ| = %.6f  (x log x = 1 の根 %.6f)" % (P["tpsi"], P["xlogx_root"])),
        ("③ 複素回転体", "Θ = θ + iφ,  θ₀ = %.6f rad" % P["theta0"]),
        ("", "ω(外, 中, 内) = %.5f, %.5f, %.5f rad/s" % (P["omega_outer"], P["omega_middle"], P["omega_inner"])),
        ("", "ポッド歳差 Ω = Mgl/(I₃ω₃) = %.5f rad/s" % P["precession"]),
        ("④ Γ・ζ 多様体", "Riemann–Siegel θ(φ) = %.6f" % P["rs_theta"]),
        ("", "Z(φ) = e^{iθ(φ)} ζ(½ + iφ) = %.6f" % P["rs_Z"]),
        ("⑤ Jones 多項式", "3_1: " + jones[0]),
        ("", "4_1: " + jones[1]),
        ("", "5_1: " + jones[2]),
        ("⑦ 部品寸法 [m]", "外環 R = %.3f, 中環 R = %.3f, 内環 R = %.3f, 管径 = %.3f"
         % (P["R_out"], P["R_mid"], P["R_in"], P["tube"])),
        ("", "ポッド r = %.3f, 塔高 = %.3f, 井戸深さ = %.3f" % (P["pod_r"], P["tower_h"], P["well_depth"])),
        ("", "Jones コイル: 3_1 R = %.3f, 5_1 R = %.3f, 4_1 床下"
         % (P["coil_r"], P["coil_r"] * 0.8)),
    ]
    y = 0.90
    for a, b in rows:
        if a:
            y -= 0.012
            fig.text(0.06, y, a, fontsize=10.5, color=NAVY, weight="bold")
        fig.text(0.26, y, b, fontsize=9.5, color="#222")
        y -= 0.03
    fig.text(0.06, 0.12, "V(t*) は t* = e^{iθ(φ)} での値。|V| がコイル寸法、|V(e^{iα})| の極小が扉の共鳴窓の角度を決める。",
             fontsize=8.5, color="#445")
    fig.text(0.06, 0.10, "寸法は各方程式群の数値エネルギー Σ log(1+|v|) で変調される (lib_registry.bada / main_blueprint.bada)。",
             fontsize=8.5, color="#445")
    page(pdf, fig)


def blueprint_views(pdf, G, P):
    fig = plt.figure(figsize=A4, facecolor=NAVY)
    fig.text(0.06, 0.955, "2. 三面図 (単位 m)", fontsize=16, color=WHITE, weight="bold")
    views = [("上面図 (x–y)", 0, 1, [0.08, 0.575, 0.84, 0.36]),
             ("正面図 (x–z)", 0, 2, [0.05, 0.06, 0.44, 0.44]),
             ("側面図 (y–z)", 1, 2, [0.52, 0.06, 0.44, 0.44])]
    for title, i, j, rect in views:
        ax = fig.add_axes(rect, facecolor=NAVY)
        for g, pts in G.items():
            if g.startswith(("tower", "gantry", "drop")):
                pts = densify(pts, len(pts) // 2, 80)
            ax.scatter(pts[:, i], pts[:, j], s=0.25, c=gcol(g), linewidths=0)
        ax.set_aspect("equal")
        ax.grid(color="#3a5a8a", lw=0.4)
        ax.tick_params(colors=WHITE, labelsize=6)
        for sp in ax.spines.values():
            sp.set_color(WHITE)
        ax.set_title(title, color=WHITE, fontsize=11)
        if j == 1:
            for r, lab in ((P["R_out"], "外環"), (P["R_mid"], "中環"), (P["R_in"], "内環")):
                ax.annotate("", xy=(r, 0), xytext=(0, 0),
                            arrowprops=dict(arrowstyle="->", color=GOLD, lw=0.8))
            ax.text(P["R_out"] * 0.5, -6, "R外 = %.1f" % P["R_out"], color=GOLD, fontsize=7, ha="center")
            ax.text(0, P["coil_r"] + 12, "Jones コイル R = %.1f" % P["coil_r"], color="#7fb0ff",
                    fontsize=7, ha="center")
        else:
            ax.annotate("", xy=(-P["R_out"] - 20, P["tower_h"]), xytext=(-P["R_out"] - 20, -P["well_depth"]),
                        arrowprops=dict(arrowstyle="<->", color=GOLD, lw=0.8))
            ax.text(-P["R_out"] - 24, P["tower_h"] * 0.4, "%.0f" % (P["tower_h"] + P["well_depth"]),
                    color=GOLD, fontsize=7, rotation=90, ha="right")
    leg = [("ジンバル環", "#ffd27a"), ("ポッド", "#ffffff"), ("塔・ガントリー", "#b8c8e8"),
           ("Jones 3_1", "#7fb0ff"), ("Jones 5_1", "#c8a0ff"), ("Jones 4_1", "#70e0e8"),
           ("扉の軸", "#ff7070"), ("共鳴窓", "#ffb070")]
    for k, (lab, c) in enumerate(leg):
        fig.text(0.08 + (k % 4) * 0.22, 0.548 - (k // 4) * 0.015, "■ " + lab, color=c, fontsize=8)
    page(pdf, fig)


def charts(pdf, S, comps):
    fig, axs = plt.subplots(3, 1, figsize=A4)
    fig.suptitle("3. ゼータ多様体・Jones 共鳴・方程式の割り当て", fontsize=15, color=NAVY, weight="bold", x=0.06,
                 ha="left", y=0.975)
    z = S["Z"]
    axs[0].plot(z[:, 0], z[:, 1], color=NAVY, lw=1)
    axs[0].axhline(0, color="#999", lw=0.5)
    axs[0].set_title("臨界線上の Riemann–Siegel Z(t) = e^{iθ(t)} ζ(½+it)  (零点 = ζ の非自明零点)", fontsize=10)
    axs[0].set_xlabel("t")
    names = ["3_1", "4_1", "5_1"]
    for k, c in enumerate(["#4a80d0", "#40b8c0", "#9060d0"]):
        v = S["V%d" % k]
        axs[1].plot(v[:, 0], v[:, 1], color=c, lw=1.2, label=names[k])
    axs[1].set_title("|V_K(e^{iα})| — 極小が扉の共鳴角", fontsize=10)
    axs[1].set_xlabel("α [deg]"); axs[1].legend(fontsize=8)
    lab = [c[0] for c in comps]
    axs[2].bar(lab, [c[1] for c in comps], color=GOLD)
    axs[2].set_title("部品 (タグ) ごとの方程式数", fontsize=10)
    axs[2].tick_params(axis="x", labelsize=7, rotation=30)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    page(pdf, fig)


def registry_pages(pdf, reg):
    status_col = {"holds": "#1a7f37", "differs": "#b3261e", "calc": "#1f4fa0", "symb": "#666666"}
    per_page, y0, dy = 68, 0.945, 0.0133
    lines = []
    for eid, st, eq, val, tags, gloss in reg:
        body = eq if not val else "%s    = %s" % (eq, val)
        wrapped = textwrap.wrap(body, 118) or [""]
        for k, w in enumerate(wrapped[:4]):
            lines.append((eid if k == 0 else "", st if k == 0 else "", w, tags if k == 0 else ""))
    total = (len(lines) + per_page - 1) // per_page
    for p in range(total):
        fig = plt.figure(figsize=A4)
        fig.text(0.04, 0.965, "4. 全方程式レジストリ (%d 本)   p.%d/%d" % (len(reg), p + 1, total),
                 fontsize=10, color=NAVY, weight="bold")
        for k, (eid, st, w, tags) in enumerate(lines[p * per_page:(p + 1) * per_page]):
            y = y0 - k * dy
            if eid:
                fig.text(0.03, y, eid, fontsize=5.6, color="#223", weight="bold")
                fig.text(0.125, y, st, fontsize=5.6, color=status_col.get(st, "#333"))
                fig.text(0.83, y, tags[:40], fontsize=5, color="#667")
            fig.text(0.175, y, w, fontsize=5.6, color="#111")
        page(pdf, fig)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "contact_blueprint.pdf"
    set_font()
    G = load_obj("contact_machine.obj")
    P, S, comps, jones = load_data("contact_data.txt")
    reg = parse_registry("contact_blueprint.txt")
    with PdfPages(out) as pdf:
        cover(pdf, P, "preview.png")
        params_page(pdf, P, jones)
        blueprint_views(pdf, G, P)
        charts(pdf, S, comps)
        registry_pages(pdf, reg)
        d = pdf.infodict()
        d["Title"] = "Contact Transporter — 3D Blueprint (Bada)"
        d["Subject"] = "Speculative blueprint generated from the Bada program contact_blueprint.bada"
    print("wrote %s (%d equations)" % (out, len(reg)))


if __name__ == "__main__":
    main()
