"""設計図 PDF を 2 冊生成する.

  output/contact_transporter_blueprint.pdf  … コンタクトの異次元輸送機
  output/chatgpt_blueprint.pdf              … ChatGPT (GPT 系 Transformer)
"""
import collections
import datetime
import os
import warnings

import numpy as np

from common import BG, C, FG, GRID, OUT, smooth  # noqa: F401  (フォント設定を先に読み込む)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import transporter_model as M
import transporter_video as TV
import chatgpt_model as G
import chatgpt_video as GV

warnings.filterwarnings("ignore")
plt.rcParams["pdf.fonttype"] = 42
A4L = (11.69, 8.27)
TODAY = datetime.date.today().isoformat()


# ---- 共通 -----------------------------------------------------------------
def page(title, sub, no, total, brand):
    fig = plt.figure(figsize=A4L, facecolor=BG)
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_facecolor(BG)
    for x in np.linspace(0, 1, 48):
        bg.axvline(x, color=GRID, lw=0.25, alpha=0.5)
    for y in np.linspace(0, 1, 34):
        bg.axhline(y, color=GRID, lw=0.25, alpha=0.5)
    bg.set_xlim(0, 1)
    bg.set_ylim(0, 1)
    bg.set_axis_off()
    # 図枠と表題欄
    bg.add_patch(plt.Rectangle((0.015, 0.02), 0.97, 0.96, fill=False, ec=FG, lw=1.2))
    bg.add_patch(plt.Rectangle((0.66, 0.02), 0.325, 0.06, fill=True, fc=BG, ec=FG, lw=0.8))
    fig.text(0.67, 0.058, brand, color=C["hud"], fontsize=9, weight="bold")
    fig.text(0.67, 0.033, f"図番 {no:02d}/{total:02d}   {TODAY}   masaaki-avnturle / Bada", color=FG, fontsize=7.5)
    if title:
        fig.text(0.03, 0.935, title, color=FG, fontsize=17, weight="bold")
    if sub:
        fig.text(0.03, 0.905, sub, color=C["hud"], fontsize=10)
    return fig


def disclaimer(fig, text, y=0.035):
    fig.text(0.03, y, text, color=C["warn"], fontsize=7.5)


def iso_axes(fig, rect, lim, zr, elev=22, azim=-58, zoom=1.3):
    ax = fig.add_axes(rect, projection="3d")
    ax.set_facecolor(BG)
    ax.set_axis_off()
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(*zr)
    ax.set_box_aspect((1, 1, (zr[1] - zr[0]) / (2 * lim)), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    return ax


def balloon(ax3d, fig, p, num, color):
    from mpl_toolkits.mplot3d import proj3d
    x, y, _ = proj3d.proj_transform(*p, ax3d.get_proj())
    X, Y = fig.transFigure.inverted().transform(ax3d.transData.transform((x, y)))
    fig.text(X, Y, str(num), color=BG, fontsize=9, ha="center", va="center", weight="bold",
             bbox=dict(boxstyle="circle,pad=0.25", fc=color, ec=FG, lw=0.6))


# ==== コンタクト輸送機 ======================================================
TR_BRAND = "CONTACT TRANSPORTER — 異次元への輸送機 3D 設計図"
TR_NOTE = ("※ 論文の方程式に基づく思索的・フィクションの設計図 (幾何的な可視化) です。"
           "工学的に検証された装置ではなく、異次元への輸送を可能にするものではありません。")


def tr_cover(pdf, n):
    fig = page(None, None, 1, n, TR_BRAND)
    fig.text(0.05, 0.84, "CONTACT TRANSPORTER", color=FG, fontsize=34, weight="bold")
    fig.text(0.05, 0.785, "異次元への輸送機  3 次元設計図 (組立図・部品表・方程式対応表)", color=C["hud"], fontsize=15)
    lines = [
        "原典: contact_blueprint.pdf  (量子プログラミング言語 Bada: contact_transporter/contact_blueprint.bada)",
        "原理: ジュネーブ CERN の衝突で粒子が消えた方向 = 異次元への扉",
        "   × 特殊相対論 (地球の 1 秒 = 搭乗者の 18 時間, Γ = 64800)",
        "   × 複素回転体 (コマ) の幾何学 (Θ = θ + iφ, φ = 11.7722)",
        "   × ガンマ関数におけるゼータ関数の大域的部分積分多様体 (Riemann–Siegel Z)",
        "   × Jones 多項式 = 設計図生成機能",
        "論文 15 本の全方程式 2111 本 (数値評価 632 / 等式検証 成立 231・不成立 181) を 10 部品に割り当て",
    ]
    for i, l in enumerate(lines):
        fig.text(0.05, 0.71 - i * 0.04, l, color=FG, fontsize=10.5)
    ax = iso_axes(fig, (0.6, 0.1, 0.39, 0.62), 95, (M.GROUND - 35, 150), zoom=1.3)
    for key, (ck, polys) in M.scene(pod_z=0, t_rot=4).items():
        TV.draw_part(ax, polys, C[ck], lw=0.8)
    toc = ["01 表紙", "02 設計パラメータ", "03 部品 ↔ 方程式 対応表", "04 三面図", "05 3D 等角図",
           "06 分解組立図・組立手順", "07 動作シーケンス (起動・輸送)", "08 方程式レジストリ抜粋", "09 注記"]
    fig.text(0.05, 0.37, "目次", color=C["hud"], fontsize=11, weight="bold")
    for i, t in enumerate(toc):
        fig.text(0.05 + (i // 5) * 0.2, 0.33 - (i % 5) * 0.035, t, color=FG, fontsize=9.5)
    disclaimer(fig, TR_NOTE, 0.1)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_params(pdf, n):
    fig = page("1. 設計パラメータ", "Bada 実行結果 (レポート 1 章) と mpmath による再計算", 2, n, TR_BRAND)
    P = M.P
    rows = [
        ("① 衝突段", "√s", "13.6 TeV", "Linac4 → PSB → PS → SPS → LHC"),
        ("", "E_T^miss", "1348.29 GeV", ""),
        ("", "扉の軸 n̂", "(0.86964, −0.25101, 0.42511)", f"|n̂| = {np.linalg.norm(P['n_hat']):.5f}"),
        ("② 特殊相対論", "Γ", "18 h / 1 s = 64800", "再計算 64800 ✓"),
        ("", "1 − β", "1.19075e−10", f"再計算 {1/(2*P['Gamma']**2):.5e} ✓"),
        ("", "ラピディティ φ", "arcosh Γ = 11.772200", f"再計算 {np.arccosh(P['Gamma']):.6f} ✓"),
        ("", "ベガ 25.04 ly", "収縮 3.656e9 km, 片道 3.3874 h",
         f"再計算 {25.04*9.4607e12/P['Gamma']:.4g} km ✓"),
        ("②' 輸送計量", "T|ψ|", "1.763290", "x log x = 1 の根 1.763220"),
        ("③ 複素回転体", "θ₀", "0.523599 rad (30°)", ""),
        ("", "ω 外・中・内", "0.10472, 0.39241, 1.47043 rad/s", "外 = π/30"),
        ("", "歳差 Ω", "Mgl/(I₃ω₃) = 3.70640 rad/s", ""),
        ("④ Γ・ζ 多様体", "θ(φ)", "−2.581360", f"再計算 {P['rs_theta']:.6f} ✓"),
        ("", "Z(φ)", "−1.334150", f"再計算 {P['rs_Z']:.6f} ✓"),
        ("⑤ Jones", "V_3_1(t*)", "−0.116342 + 2.30908i", f"再計算 {P['V_tstar']['3_1']:.6f}"),
        ("", "V_4_1(t*)", "3.56478", f"再計算 {P['V_tstar']['4_1'].real:.6f}"),
        ("", "V_5_1(t*)", "−2.81527 + 1.09654i", f"再計算 {P['V_tstar']['5_1']:.6f}"),
        ("⑦ 部品寸法", "環 R 外/中/内", "60.088 / 47.431 / 37.440 m", "管径 2.066 m"),
        ("", "ポッド r / 塔高 / 井戸", "5.021 / 132.194 / 38.800 m", ""),
        ("", "Jones コイル R", "3_1: 70.269, 5_1: 56.215 m", "4_1 は床下"),
    ]
    x = [0.04, 0.17, 0.33, 0.62]
    for j, h in enumerate(["段", "量", "値 (レポート)", "検算・備考"]):
        fig.text(x[j], 0.86, h, color=C["hud"], fontsize=10.5, weight="bold")
    for i, r in enumerate(rows):
        y = 0.825 - i * 0.037
        for j, v in enumerate(r):
            fig.text(x[j], y, v, color=FG if j else C["warn"], fontsize=9.5)
        fig.add_artist(plt.Line2D([0.035, 0.96], [y - 0.01, y - 0.01], color=GRID, lw=0.5))
    fig.text(0.04, 0.1, "V(t*) は t* = e^{iθ(φ)} での値。|V| がコイル寸法、|V(e^{iα})| の極小が扉の共鳴窓の角度を決める。"
             "寸法は各方程式群の数値エネルギー Σ log(1+|v|) で変調 (レポート記載)。", color=FG, fontsize=8.5)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_mapping(pdf, n, reg):
    fig = page("2. 部品 ↔ 方程式 対応表", "全方程式 2111 本を先頭タグで部品に割り当て (右列は件数と代表式 ID)", 3, n, TR_BRAND)
    cnt = collections.Counter(e["part"] for e in reg)
    tags = collections.defaultdict(list)
    for tg, pk in M.TAG_PART.items():
        tags[pk].append(tg)
    ids = collections.defaultdict(list)
    for e in reg:
        if e["status"] in ("holds", "calc") and len(ids[e["part"]]) < 4:
            ids[e["part"]].append(e["id"])
    for j, h in enumerate(["No.", "部品", "支配方程式 (レポート 1 章)", "寸法", "タグ / 件数 / 代表式"]):
        fig.text([0.035, 0.07, 0.2, 0.6, 0.76][j], 0.86, h, color=C["hud"], fontsize=10, weight="bold")
    for i, (k, name, ck, eqs, dim) in enumerate(M.PARTS):
        y = 0.82 - i * 0.092
        col = TV.PART_COLOR[k]
        fig.text(0.04, y, f"{i+1}", color=col, fontsize=11, weight="bold")
        fig.text(0.07, y, name, color=col, fontsize=10.5, weight="bold")
        for j, eq in enumerate(eqs):
            fig.text(0.2, y - j * 0.032, eq, color=FG, fontsize=9)
        fig.text(0.6, y, dim.replace(", ", "\n"), color=FG, fontsize=8.5, va="top", linespacing=1.4)
        fig.text(0.76, y, " ".join(tags.get(k, [])) + f"  —  {cnt.get(k, 0)} 本", color=FG, fontsize=8.5)
        fig.text(0.76, y - 0.03, ", ".join(ids[k]), color=GRID if not ids[k] else C["hud"], fontsize=8)
        fig.add_artist(plt.Line2D([0.03, 0.965], [y - 0.058, y - 0.058], color=GRID, lw=0.5))
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_plan(pdf, n):
    fig = page("3. 三面図 (単位 m)", "上面図・正面図・側面図 — 各寸法はレポートの Bada 実行結果", 4, n, TR_BRAND)
    TV.draw_plan(fig, 1.0, dims=1.0, fs=1.0, rects={
        "top": (0.03, 0.12, 0.36, 0.74), "front": (0.40, 0.12, 0.28, 0.74), "side": (0.69, 0.12, 0.28, 0.74)})
    items = [("ジンバル環", "ring"), ("ポッド", "pod"), ("塔・床", "tower"), ("Jones 3_1", "j31"),
             ("Jones 5_1", "j51"), ("Jones 4_1", "j41"), ("扉の軸", "axis"), ("共鳴窓", "window"), ("井戸", "well")]
    for i, (lab, ck) in enumerate(items):
        fig.text(0.04 + i * 0.068, 0.09, "■ " + lab, color=C[ck], fontsize=8)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_iso(pdf, n):
    fig = page("4. 3D 等角図", "平面図の各部品を z 方向に復元した 3 次元形状 (3 方向から)", 5, n, TR_BRAND)
    sc = M.scene(pod_z=0, t_rot=4)
    views = [((0.02, 0.1, 0.5, 0.8), 22, -58, 1.35, "等角 (仰角 22°, 方位 −58°)"),
             ((0.52, 0.47, 0.46, 0.43), 5, -90, 1.3, "正面透視 (仰角 5°)"),
             ((0.52, 0.06, 0.46, 0.43), 60, -30, 1.3, "俯瞰 (仰角 60°)")]
    for rect, el, az, zm, lab in views:
        ax = iso_axes(fig, rect, 95, (M.GROUND - 35, 150), el, az, zm)
        for key, (ck, polys) in sc.items():
            TV.draw_part(ax, polys, C[ck], lw=0.7)
        fig.text(rect[0] + 0.01, rect[1] + rect[3] - 0.02, lab, color=C["hud"], fontsize=9)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_exploded(pdf, n):
    fig = page("5. 分解組立図・組立手順", "部品番号順に組み立てる (番号 = 組立順)", 6, n, TR_BRAND)
    ax = iso_axes(fig, (0.0, 0.05, 0.6, 0.86), 150, (-140, 260), 18, -58, 1.3)
    sc = M.scene(pod_z=TV.POD_TOP, t_rot=4)
    for i, key in enumerate(M.ASSEMBLY_ORDER):
        ck, polys = sc[key]
        off = np.asarray(TV.EXPLODE[key]) * 0.55
        TV.draw_part(ax, polys, C[ck], lw=0.7, offset=off)
        cen = np.concatenate(polys).mean(0) + off
        fig.canvas.draw()
        balloon(ax, fig, cen, i + 1, C[ck])
    steps = [
        ("基礎・床", "床面 z = −38.8 m に円形プラットフォームを敷設 (R 66–90 m)"),
        ("井戸", "輸送計量 ds² の漏斗。深さ 38.8 m、底径 30 m"),
        ("塔・ガントリー", "4 脚 (±48 m) を高さ 132.194 m まで建て、頂部アームを中心に集める"),
        ("ジンバル環", "外環 R 60.088 → 中環 47.431 → 内環 37.440 を入れ子に。θ₀ = 30° 傾斜"),
        ("Jones 3_1", "三葉結び目コイル R 70.269 m を赤道面に巻く"),
        ("Jones 5_1", "5_1 コイル R 56.215 m を z = +70 m に巻く"),
        ("Jones 4_1", "8 の字結び目コイルを床下 (z ≈ −25 m) に設置"),
        ("共鳴窓", f"|V_K(e^{{iα}})| 極小の角度 {len(M.WINDOWS)} 箇所にセンサを配置"),
        ("ポッド", "r = 5.021 m の球殻。塔頂から吊り下げ (z ≈ 118 m)"),
        ("扉の軸", "n̂ = (0.870, −0.251, 0.425) に照準を合わせる"),
    ]
    for i, (h, d) in enumerate(steps):
        y = 0.85 - i * 0.07
        fig.text(0.61, y, f"{i+1}. {h}", color=FG, fontsize=10, weight="bold")
        fig.text(0.625, y - 0.027, d, color=FG, fontsize=8.3)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def styled(ax, title):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=FG, labelsize=7)
    ax.grid(color=GRID, lw=0.4)
    ax.set_title(title, color=FG, fontsize=9.5)


def tr_operation(pdf, n):
    fig = page("6. 動作シーケンス (起動・輸送)", "動画 contact_transporter.mp4 の 6・7 章に対応", 7, n, TR_BRAND)
    ax = fig.add_axes([0.06, 0.55, 0.4, 0.3])
    styled(ax, "臨界線上の Riemann–Siegel Z(t) — φ = 11.7722 で Z = −1.334")
    ax.plot(M.ZT, M.ZV, color=C["window"], lw=1)
    ax.axvline(M.P["phi"], color=C["axis"], ls="--", lw=0.8)
    ax.axhline(0, color=GRID)
    ax = fig.add_axes([0.54, 0.55, 0.4, 0.3])
    styled(ax, "|V_K(e^{iα})| — 極小が扉の共鳴角")
    for k, ck in (("3_1", "j31"), ("4_1", "j41"), ("5_1", "j51")):
        ax.plot(np.degrees(M.ALPHA), M.VABS[k], color=C[ck], lw=1, label=k)
    for k, a, v in M.WINDOWS:
        ax.scatter(np.degrees(a), v, color=C["window"], s=12, zorder=5)
    ax.set_xlabel("α [deg]", color=FG, fontsize=8)
    ax.legend(fontsize=7, facecolor=BG, labelcolor=FG, edgecolor=GRID)
    ax = fig.add_axes([0.06, 0.13, 0.4, 0.3])
    styled(ax, "起動: 角速度 ω(t) とポッド高度")
    t = np.linspace(0, 16, 200)
    spin = 1 + 7 * smooth(t / 16)
    for w, lab, col in zip(M.P["omega"], ("外", "中", "内"), (C["ring"], C["warn"], C["window"])):
        ax.plot(t, w * spin, color=col, lw=1, label=f"ω{lab} ×倍率")
    ax2 = ax.twinx()
    ax2.plot(t, TV.POD_TOP * (1 - smooth((t / 16 - 0.1) / 0.55)), color=C["pod"], ls="--", lw=1)
    ax2.tick_params(colors=FG, labelsize=7)
    ax.set_xlabel("起動からの時間 [s] (動画の時間軸)", color=FG, fontsize=8)
    ax.legend(fontsize=7, facecolor=BG, labelcolor=FG, edgecolor=GRID, loc="upper left")
    ax = fig.add_axes([0.54, 0.13, 0.4, 0.3])
    styled(ax, "輸送: 地球時間 t と搭乗者時間 τ (Γ = 64800)")
    te = np.linspace(0, 1, 100)
    ax.plot(te, 18 * te, color=C["warn"], lw=1.5)
    ax.set_xlabel("地球時間 t [s]", color=FG, fontsize=8)
    ax.set_ylabel("搭乗者時間 τ [h]", color=FG, fontsize=8)
    ax.text(0.05, 15, "ベガ 25.04 ly → 収縮距離 3.656e9 km\n片道 3.3874 h (搭乗者)", color=FG, fontsize=8)
    seq = "① ポッド降下 → ② 環の回転上昇 (ω×1→×8) → ③ Jones コイル励磁 → ④ 共鳴窓同期 (Z(φ)) → ⑤ 扉開放 → ⑥ n̂ 方向へ輸送"
    fig.text(0.06, 0.475, seq, color=C["hud"], fontsize=9)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_registry(pdf, n, reg):
    fig = page("7. 方程式レジストリ抜粋 (数値が成立・評価された式)", "各部品 4 本ずつ。全 2111 本は data/equations.json", 8, n, TR_BRAND)
    y = 0.86
    for k, name, *_ in M.PARTS:
        sel = [e for e in reg if e["part"] == k and e["status"] in ("holds", "calc")][:4]
        fig.text(0.035, y, name, color=TV.PART_COLOR[k], fontsize=9.5, weight="bold")
        y -= 0.024
        for e in sel:
            txt = e["eq"] if len(e["eq"]) < 120 else e["eq"][:118] + "…"
            fig.text(0.05, y, f"{e['id']:<10s} [{e['status']}]  {txt}", color=FG, fontsize=7.3)
            y -= 0.02
        y -= 0.006
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def tr_notes(pdf, n):
    fig = page("8. 注記", None, 9, n, TR_BRAND)
    notes = [
        "・本図面は contact_blueprint.pdf の数値 (Bada 実行結果) を唯一の寸法根拠とし、形状の配置は可視化のための解釈である。",
        "・部品への方程式割り当ては各式の先頭タグによる: ROT→環, SR/QUANTUM→ポッド, GAMMA/BETA→塔, ZETA→共鳴窓,",
        "   JONES→コイル, MANIFOLD/ENTROPY→井戸, TRANSPORT→扉の軸, OTHER→基礎。",
        "・θ(φ), Z(φ), V_K(t*) は mpmath で再計算し、レポート値と有効数字 6 桁で一致した。",
        "・共鳴窓の角度は |V_K(e^{iα})| の極小 (α ∈ [0, 2π), 0.1° 刻み) から求めた。",
        "・生成スクリプト: contact_transporter_media/ (transporter_model.py, transporter_video.py, blueprint_pdf.py)",
        "",
        TR_NOTE,
    ]
    for i, l in enumerate(notes):
        fig.text(0.05, 0.84 - i * 0.05, l, color=C["warn"] if l == TR_NOTE else FG, fontsize=10)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def build_transporter():
    reg = TV.REG
    n = 9
    path = os.path.join(OUT, "contact_transporter_blueprint.pdf")
    with PdfPages(path) as pdf:
        tr_cover(pdf, n)
        tr_params(pdf, n)
        tr_mapping(pdf, n, reg)
        tr_plan(pdf, n)
        tr_iso(pdf, n)
        tr_exploded(pdf, n)
        tr_operation(pdf, n)
        tr_registry(pdf, n, reg)
        tr_notes(pdf, n)
        d = pdf.infodict()
        d["Title"] = "CONTACT TRANSPORTER 3D Blueprint"
        d["Author"] = "masaaki-avnturle / Bada"
    return path


# ==== ChatGPT ==============================================================
GP_BRAND = "ChatGPT BLUEPRINT — 大規模言語モデル 3D 設計図"
GP_NOTE = ("※ 公開論文 (Transformer, GPT-3, InstructGPT) の式に基づく図解モデルです。"
           "ChatGPT 実機の非公開の構成・寸法を示すものではありません。")


def gp_draw_all(ax, lw=0.7, off=None):
    for k, polys in G.geometry().items():
        GV.draw(ax, polys, G.COLOR_OF[k], lw=lw, offset=(off or {}).get(k, (0, 0, 0)))


def gp_cover(pdf, n):
    fig = page(None, None, 1, n, GP_BRAND)
    fig.text(0.05, 0.84, "ChatGPT BLUEPRINT", color=FG, fontsize=34, weight="bold")
    fig.text(0.05, 0.785, "大規模言語モデル  3 次元設計図 (組立図・部品表・方程式対応表)", color=C["hud"], fontsize=15)
    lines = [
        "コンタクトの輸送機と同じ手順で作図: 方程式 → 部品 → 平面図 → 3D → 組み立て → 使用",
        "構成: トークナイザ → 埋め込み → [LayerNorm → 自己注意 → LayerNorm → FFN] × 96 → 出力 softmax",
        "整列: 事前学習 (次トークン予測) → 教師あり微調整 → RLHF (報酬モデル + PPO)",
        "寸法: GPT-3 論文の公開値 (L = 96, d = 12288, h = 96, |V| = 50257, n_ctx = 2048)",
    ]
    for i, l in enumerate(lines):
        fig.text(0.05, 0.71 - i * 0.04, l, color=FG, fontsize=10.5)
    ax = iso_axes(fig, (0.55, 0.08, 0.43, 0.75), 100, (-30, 170), 18, -58, 1.3)
    gp_draw_all(ax)
    toc = ["01 表紙", "02 設計パラメータ", "03 部品 ↔ 方程式 対応表", "04 平面図 (ブロック図・立面図)",
           "05 3D 等角図・分解組立図", "06 使用 (推論フロー)", "07 注記"]
    fig.text(0.05, 0.47, "目次", color=C["hud"], fontsize=11, weight="bold")
    for i, t in enumerate(toc):
        fig.text(0.05, 0.43 - i * 0.035, t, color=FG, fontsize=9.5)
    disclaimer(fig, GP_NOTE, 0.1)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def gp_params(pdf, n):
    fig = page("1. 設計パラメータ", "GPT-3 175B (Brown et al., 2020) の公開値を参照", 2, n, GP_BRAND)
    h = G.HP
    rows = [
        ("層数 L", f"{h['n_layer']}", "図では代表 8 層を表示 (層ピッチ 14)"),
        ("隠れ次元 d", f"{h['d_model']}", ""),
        ("注意ヘッド h", f"{h['n_head']}", f"d_k = d/h = {h['d_head']} (図では 12 基を表示)"),
        ("FFN 次元 d_ff", f"{h['d_ff']}", "= 4d"),
        ("文脈長 n_ctx", f"{h['n_ctx']}", ""),
        ("語彙 |V|", f"{h['n_vocab']}", "BPE"),
        ("パラメータ数", "≈ 1.75 × 10¹¹", f"概算 12·L·d² = {12*h['n_layer']*h['d_model']**2:.3e}"),
        ("温度 T", "0.8 (図解例)", "p = softmax(z/T)"),
        ("RLHF 係数 β", "KL 正則化", "max E[r] − β KL(π‖π_ref)"),
    ]
    for j, hh in enumerate(["量", "値", "備考"]):
        fig.text([0.05, 0.3, 0.5][j], 0.85, hh, color=C["hud"], fontsize=11, weight="bold")
    for i, r in enumerate(rows):
        y = 0.8 - i * 0.06
        for j, v in enumerate(r):
            fig.text([0.05, 0.3, 0.5][j], y, v, color=C["warn"] if j == 0 else FG, fontsize=11)
        fig.add_artist(plt.Line2D([0.045, 0.95], [y - 0.018, y - 0.018], color=GRID, lw=0.5))
    fig.text(0.05, 0.16, "参照: Vaswani+ 2017 “Attention Is All You Need”, Brown+ 2020 “Language Models are Few-Shot Learners”,\n"
             "Ouyang+ 2022 “Training language models to follow instructions with human feedback”", color=FG, fontsize=9,
             linespacing=1.6)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def gp_mapping(pdf, n):
    fig = page("2. 部品 ↔ 方程式 対応表", None, 3, n, GP_BRAND)
    for j, hh in enumerate(["No.", "部品", "支配方程式", "寸法・備考"]):
        fig.text([0.035, 0.07, 0.24, 0.72][j], 0.88, hh, color=C["hud"], fontsize=10, weight="bold")
    for i, (k, name, ck, eqs, note) in enumerate(G.PARTS):
        y = 0.84 - i * 0.078
        col = G.COLOR_OF[k]
        fig.text(0.04, y, f"{i+1}", color=col, fontsize=11, weight="bold")
        fig.text(0.07, y, name, color=col, fontsize=10.5, weight="bold")
        for j, eq in enumerate(eqs):
            fig.text(0.24, y - j * 0.03, eq, color=FG, fontsize=9.5)
        fig.text(0.72, y, note, color=FG, fontsize=9)
        fig.add_artist(plt.Line2D([0.03, 0.965], [y - 0.05, y - 0.05], color=GRID, lw=0.5))
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def gp_plan(pdf, n):
    fig = page("3. 平面図 — ブロック図と立面図", "左: 1 ブロックの構成 (Pre-LN)  中: 正面図  右: 上面図", 4, n, GP_BRAND)
    GV.block_diagram(fig.add_axes([0.03, 0.1, 0.33, 0.78]), 1.0, fs=0.95)
    GV.elevation(fig.add_axes([0.38, 0.12, 0.3, 0.74]), "front")
    GV.elevation(fig.add_axes([0.69, 0.3, 0.29, 0.5]), "top")
    fig.text(0.69, 0.22, "層ピッチ 14 / 注意ヘッド 12 基 (R = 26) / FFN 62×62\n"
             "RLHF ループ R = 88 (報酬の帰還路)", color=C["warn"], fontsize=9, linespacing=1.6)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def gp_iso(pdf, n):
    fig = page("4. 3D 等角図・分解組立図", "右の番号 = 組立順", 5, n, GP_BRAND)
    ax = iso_axes(fig, (0.0, 0.08, 0.45, 0.82), 100, (-30, 170), 18, -58, 1.3)
    gp_draw_all(ax)
    ax = iso_axes(fig, (0.40, 0.06, 0.38, 0.86), 125, (-90, 220), 18, -58, 1.45)
    off = {k: np.asarray(v) * 0.6 for k, v in GV.EXPLODE.items()}
    gp_draw_all(ax, 0.6, off)
    fig.canvas.draw()
    geom = G.geometry()
    for i, k in enumerate(G.ASSEMBLY_ORDER):
        balloon(ax, fig, np.concatenate(geom[k]).mean(0) + off[k], i + 1, G.COLOR_OF[k])
    for i, k in enumerate(G.ASSEMBLY_ORDER):
        fig.text(0.78, 0.85 - i * 0.07, f"{i+1}. {G.PART_NAME[k]}", color=G.COLOR_OF[k], fontsize=10, weight="bold")
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def gp_use(pdf, n):
    fig = page("5. 使用 (推論フロー)", "プロンプト → トークン → 96 層 → softmax → 次トークン (自己回帰)", 6, n, GP_BRAND)
    fig.text(0.04, 0.86, "プロンプト: " + "".join(G.PROMPT), color=FG, fontsize=11)
    fig.text(0.04, 0.83, "トークン (概略): " + " | ".join(G.PROMPT), color=G.COL["tok"], fontsize=9.5)
    for i, l in enumerate((0, 2, 5, 7)):
        ax = fig.add_axes([0.04 + i * 0.16, 0.5, 0.14, 0.28])
        ax.imshow(G.ATTN[l], cmap="magma", vmin=0, vmax=1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"層 {l+1} の注意行列", color=FG, fontsize=9)
    fig.text(0.04, 0.46, "softmax(QKᵀ/√d + M): 小型ランダム初期化モデル (d = 16) での実計算。上三角は因果マスク M = −∞ で 0。",
             color=FG, fontsize=8.5)
    ax = fig.add_axes([0.72, 0.5, 0.24, 0.28])
    styled(ax, "次トークン確率 (1 手目, T = 0.8)")
    tok, cands, logits = G.GEN[0]
    p = G.softmax(logits, G.TEMP)
    ax.barh(range(5)[::-1], p, color=[G.COL["unemb"]] + [G.COL["soft"]] * 4)
    ax.set_yticks(range(5)[::-1])
    ax.set_yticklabels(cands, color=FG, fontsize=8)
    fig.text(0.04, 0.38, "生成ステップ (候補と logit は図解用の例示値):", color=C["hud"], fontsize=10)
    text = ""
    for i, (t, cands, logits) in enumerate(G.GEN):
        text += t
        p = G.softmax(logits, G.TEMP)
        fig.text(0.05, 0.345 - i * 0.03, f"{i+1}. 選択 “{t.strip()}” (p = {p[0]:.2f})   →   {text}", color=FG, fontsize=9)
    fig.text(0.6, 0.3, "生成された寸法 (外環 R = 60.088 m, ポッド r = 5.021 m)\nは輸送機の設計図の値と一致する。",
             color=C["hud"], fontsize=10, linespacing=1.6)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def gp_notes(pdf, n):
    fig = page("6. 注記", None, 7, n, GP_BRAND)
    notes = [
        "・部品と方程式は公開論文の標準的な Transformer デコーダ (GPT 系) に従う。",
        "・3D 形状は図解のための配置: 層 = 水平スラブ, 注意ヘッド = 環状に並ぶ円柱, 残差ストリーム = 中心軸, RLHF = 外周の帰還環。",
        "・注意行列は小型のランダム初期化モデルで実際に softmax(QKᵀ/√d + M) を計算した例であり、学習済みモデルの値ではない。",
        "・生成例の候補・logit は説明用の例示値である。",
        "・生成スクリプト: contact_transporter_media/ (chatgpt_model.py, chatgpt_video.py, blueprint_pdf.py)",
        "",
        GP_NOTE,
    ]
    for i, l in enumerate(notes):
        fig.text(0.05, 0.84 - i * 0.05, l, color=C["warn"] if l == GP_NOTE else FG, fontsize=10)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def build_chatgpt():
    n = 7
    path = os.path.join(OUT, "chatgpt_blueprint.pdf")
    with PdfPages(path) as pdf:
        gp_cover(pdf, n)
        gp_params(pdf, n)
        gp_mapping(pdf, n)
        gp_plan(pdf, n)
        gp_iso(pdf, n)
        gp_use(pdf, n)
        gp_notes(pdf, n)
        d = pdf.infodict()
        d["Title"] = "ChatGPT 3D Blueprint"
        d["Author"] = "masaaki-avnturle / Bada"
    return path


if __name__ == "__main__":
    print(build_transporter())
    print(build_chatgpt())
