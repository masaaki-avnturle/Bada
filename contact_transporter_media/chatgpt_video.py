"""ChatGPT 設計図の動画 (mp4) を生成する.

部品 ↔ 方程式 → 平面図 (ブロック図・立面図) → 3D 変換 → 組み立て → 使用 (推論) の順に描く。
  python3 chatgpt_video.py            # output/chatgpt_blueprint.mp4
  python3 chatgpt_video.py --preview
"""
import os
import sys
import warnings

import numpy as np

from common import (BG, C, FG, FPS, GRID, OUT, Timeline, fig_to_rgb, new_fig, render_video,
                    smooth, write_wav)
import matplotlib.pyplot as plt
import chatgpt_model as G

warnings.filterwarnings("ignore")

TL = Timeline([
    ("title", 5), ("params", 9), ("mapping", 12), ("plan", 10), ("to3d", 8),
    ("assembly", 30), ("use", 24), ("end", 8),
])
N_FRAMES = int(TL.total * FPS)
SCENE_TITLE = {
    "params": "1. 設計パラメータ (GPT 系 Transformer)",
    "mapping": "2. 方程式 → 部品への対応",
    "plan": "3. 平面図 — ブロック図と立面図",
    "to3d": "4. 平面図 → 3D 変換",
    "assembly": "5. 組み立て",
    "use": "6. 使用 — プロンプトから次トークンを生成",
}
GEOM = G.geometry()
EQS = [(k, eq) for k, _, _, eqs, _ in G.PARTS for eq in eqs]
MONO = "IPAGothic"


def add_3d(fig, rect=(0, 0, 1, 1), elev=20, azim=-60, zoom=1.35):
    ax = fig.add_axes(rect, projection="3d")
    ax.set_facecolor(BG)
    ax.set_axis_off()
    L = G.LIM
    ax.set_xlim(-L, L)
    ax.set_ylim(-L, L)
    z0, z1 = -30, 170
    ax.set_zlim(z0, z1)
    ax.set_box_aspect((1, 1, (z1 - z0) / (2 * L)), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    return ax


def draw(ax, polys, color, lw=1.0, alpha=1.0, zscale=1.0, offset=(0, 0, 0)):
    off = np.asarray(offset, float)
    for p in polys:
        q = p.copy()
        q[:, 2] *= zscale
        q += off
        ax.plot(q[:, 0], q[:, 1], q[:, 2], color=color, lw=lw, alpha=alpha)


def header(fig, name):
    if name in SCENE_TITLE:
        fig.text(0.03, 0.94, SCENE_TITLE[name], color=FG, fontsize=20, weight="bold")
    fig.text(0.97, 0.955, "ChatGPT BLUEPRINT", color=C["hud"], fontsize=11, ha="right", alpha=0.8)


def progress_bar(fig, sec):
    fig.add_artist(plt.Line2D([0.03, 0.97], [0.018, 0.018], color=GRID, lw=3))
    fig.add_artist(plt.Line2D([0.03, 0.03 + 0.94 * sec / TL.total], [0.018, 0.018], color=C["hud"], lw=3))


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
    return ax


# ---- シーン ---------------------------------------------------------------
def s_title(fig, u, sec):
    grid_bg(fig)
    ax = add_3d(fig, (0.3, 0.0, 0.4, 0.9), elev=15, azim=-60 + 25 * sec, zoom=1.0)
    for k, polys in GEOM.items():
        draw(ax, polys, G.COLOR_OF[k], lw=0.6, alpha=0.3 * smooth(u * 3))
    a = smooth(u * 2.5)
    fig.text(0.5, 0.62, "ChatGPT BLUEPRINT", color=FG, fontsize=46, ha="center", weight="bold", alpha=a)
    fig.text(0.5, 0.52, "大規模言語モデルの設計図 — 方程式から組み立てる 3D", color=C["hud"],
             fontsize=22, ha="center", alpha=a)
    fig.text(0.5, 0.17, "コンタクトの輸送機と同じ手順で: 方程式 → 部品 → 平面図 → 3D → 組み立て → 使用\n"
             "※ ChatGPT 実機の内部構成は非公開。寸法は GPT-3 論文の公開値を参照した図解モデル",
             color=FG, fontsize=13, ha="center", alpha=smooth(u * 2.5 - 0.6), linespacing=1.6)


def s_params(fig, u, sec):
    grid_bg(fig)
    rows = [
        ("層数", "L = 96  (図では代表 8 層)", G.COL["ln"]),
        ("隠れ次元", "d = 12288", G.COL["emb"]),
        ("注意ヘッド", "h = 96,  d_k = d / h = 128", G.COL["attn"]),
        ("FFN 次元", "d_ff = 4d = 49152", G.COL["ffn"]),
        ("文脈長", "n_ctx = 2048 トークン", G.COL["res"]),
        ("語彙", "|V| = 50257 (BPE)", G.COL["tok"]),
        ("パラメータ", r"$\approx 12\,L\,d^2 = 12 \cdot 96 \cdot 12288^2 \approx 1.74\times10^{11}$", G.COL["unemb"]),
        ("整列", "事前学習 → 教師あり微調整 → RLHF (報酬モデル + PPO)", G.COL["rlhf"]),
    ]
    for i, (h, body, col) in enumerate(rows):
        a = smooth((u * 1.25 - i * 0.1) * 5)
        y = 0.82 - i * 0.092
        fig.text(0.07 + 0.02 * (1 - a), y, h, color=col, fontsize=17, weight="bold", alpha=a)
        fig.text(0.25 + 0.02 * (1 - a), y, body, color=FG, fontsize=16, alpha=a)
    fig.text(0.07, 0.06, "参照: Vaswani+ 2017 (Transformer), Brown+ 2020 (GPT-3), Ouyang+ 2022 (InstructGPT/RLHF)",
             color=C["hud"], fontsize=11, alpha=smooth(u * 3 - 2))


def s_mapping(fig, u, sec):
    grid_bg(fig)
    n = int(np.clip(smooth(u * 1.1), 0, 1) * len(EQS) + 0.999)
    ys = {}
    for i, (k, name, ck, *_r) in enumerate(G.PARTS):
        y = 0.84 - i * 0.078
        ys[k] = y
        col = G.COLOR_OF[k]
        cnt = sum(1 for kk, _ in EQS[:n] if kk == k)
        fig.add_artist(plt.Rectangle((0.72, y - 0.026), 0.25, 0.056, fill=cnt > 0, fc=col, alpha=0.15))
        fig.add_artist(plt.Rectangle((0.72, y - 0.026), 0.25, 0.056, fill=False, ec=col, lw=1.3))
        fig.text(0.73, y, name, color=FG, fontsize=12.5, va="center")
    for j, (k, eq) in enumerate(EQS[:n]):
        y = 0.86 - j * 0.047
        a = smooth((u * 1.1 * len(EQS) - j) * 1.5)
        fig.text(0.04, y, eq, color=FG, fontsize=11.5, va="center", alpha=a)
        fig.add_artist(plt.Line2D([0.52, 0.715], [y, ys[k]], color=G.COLOR_OF[k], lw=1.0, alpha=0.7 * a))


BLOCKS = [  # 2D ブロック図 (下から上へ): key, ラベル, y
    ("tok", "トークナイザ (BPE)", 0.05), ("emb", "埋め込み  W_E[t] + W_P[i]", 0.14),
    ("ln", "LayerNorm", 0.25), ("attn", "Masked Multi-Head Attention", 0.33),
    ("ln", "LayerNorm", 0.45), ("ffn", "FFN (GELU)", 0.53),
    ("ln", "LayerNorm (最終)", 0.68), ("unemb", "線形 W_U + softmax", 0.77), ("loss", "次トークン確率", 0.87),
]


def block_diagram(ax, prog=1.0, fs=1.0):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    n = int(np.ceil(prog * len(BLOCKS)))
    for i, (k, lab, y) in enumerate(BLOCKS[:n]):
        col = G.COLOR_OF[k]
        ax.add_patch(plt.Rectangle((0.2, y), 0.6, 0.06, fill=True, fc=BG, ec=col, lw=1.5))
        ax.text(0.5, y + 0.03, lab, color=FG, ha="center", va="center", fontsize=10 * fs)
        if i:
            ax.annotate("", (0.5, y), (0.5, BLOCKS[i - 1][2] + 0.06),
                        arrowprops=dict(arrowstyle="->", color=FG, lw=1))
    if n >= 6:
        ax.add_patch(plt.Rectangle((0.12, 0.23), 0.76, 0.38, fill=False, ec=G.COL["res"], ls="--", lw=1))
        ax.text(0.9, 0.42, "× 96", color=G.COL["res"], fontsize=13 * fs, va="center")
        for y0, y1 in ((0.23, 0.43), (0.43, 0.61)):
            ax.annotate("", (0.14, y1 - 0.02), (0.14, y0 + 0.01),
                        arrowprops=dict(arrowstyle="->", color=G.COL["res"], lw=1))
            ax.text(0.155, (y0 + y1) / 2, "+", color=G.COL["res"], fontsize=13 * fs, va="center")
        ax.text(0.02, 0.33, "残差", color=G.COL["res"], fontsize=10 * fs, rotation=90, va="center")


def elevation(ax, view, prog=1.0, fs=1.0):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=FG, labelsize=7 * fs)
    ax.grid(color=GRID, lw=0.4)
    ax.set_aspect("equal")
    ax.set_xlim(-100, 100)
    ax.set_ylim(-100, 100) if view == "top" else ax.set_ylim(-30, 170)
    ax.set_title({"top": "上面図 (x–y)", "front": "正面図 (x–z)"}[view], color=FG, fontsize=11 * fs)
    for k, polys in GEOM.items():
        for p in polys:
            m = max(1, int(np.ceil(len(p) * prog)))
            q = p[:m]
            x, y = (q[:, 0], q[:, 1]) if view == "top" else (q[:, 0], q[:, 2])
            ax.plot(x, y, color=G.COLOR_OF[k], lw=0.7)


def s_plan(fig, u, sec):
    grid_bg(fig)
    p = smooth(u / 0.75)
    block_diagram(fig.add_axes([0.02, 0.06, 0.36, 0.84]), p)
    elevation(fig.add_axes([0.40, 0.07, 0.28, 0.82]), "front", p)
    elevation(fig.add_axes([0.70, 0.22, 0.28, 0.55]), "top", p)
    if u > 0.8:
        a = smooth((u - 0.8) * 6)
        fig.text(0.70, 0.15, "層ピッチ 14 / 注意ヘッド 12 基 (R = 26) 表示\n実機は 96 層 × 96 ヘッド",
                 color=C["warn"], fontsize=11, alpha=a, linespacing=1.5)


def s_to3d(fig, u, sec):
    s = smooth(u / 0.8)
    ax = add_3d(fig, elev=89.9 - (89.9 - 20) * s, azim=-90 + 30 * s)
    for k, polys in GEOM.items():
        draw(ax, polys, G.COLOR_OF[k], lw=0.9, zscale=max(s, 1e-3))
    fig.text(0.03, 0.86, f"z ← s · z(層番号 × ピッチ),  s = {s:0.2f}", color=C["hud"], fontsize=14)
    fig.text(0.03, 0.82, "上面図を起こして各層を積み上げる (残差ストリームが縦軸)", color=FG, fontsize=12)


EXPLODE = {"tok": (0, 0, -60), "emb": (0, 0, -70), "res": (0, 0, 120), "ln": (-140, 0, 0), "attn": (140, 0, 20),
           "mh": (0, 140, 0), "ffn": (0, -140, 0), "unemb": (0, 0, 90), "loss": (0, 0, 100), "rlhf": (120, 0, 60)}


def s_assembly(fig, u, sec):
    n = len(G.ASSEMBLY_ORDER)
    step = u * n
    cur = min(int(step), n - 1)
    f = smooth((step - cur) / 0.6)
    ax = add_3d(fig, (0.0, 0.0, 0.66, 1.0), elev=18, azim=-60 + 40 * u, zoom=1.15)
    for i, k in enumerate(G.ASSEMBLY_ORDER[:cur + 1]):
        if i < cur:
            draw(ax, GEOM[k], G.COLOR_OF[k], lw=0.9, alpha=0.9)
        else:
            draw(ax, GEOM[k], G.COLOR_OF[k], lw=1.6, alpha=0.25 + 0.75 * f,
                 offset=np.asarray(EXPLODE[k]) * (1 - f))
    k = G.ASSEMBLY_ORDER[cur]
    _, name, _, eqs, note = next(p for p in G.PARTS if p[0] == k)
    col = G.COLOR_OF[k]
    a = 0.35 + 0.65 * smooth((step - cur) / 0.25)
    fig.add_artist(plt.Rectangle((0.62, 0.30), 0.36, 0.50, fc=BG, ec=col, lw=1.5, alpha=0.9))
    fig.text(0.635, 0.75, f"部品 {cur + 1}/{n}", color=col, fontsize=12, alpha=a)
    fig.text(0.635, 0.70, name, color=FG, fontsize=16, weight="bold", alpha=a)
    for j, ln in enumerate(eqs + ([note] if note else [])):
        fig.text(0.635, 0.62 - j * 0.08, ln, color=FG, fontsize=12, alpha=a)
    for i, kk in enumerate(G.ASSEMBLY_ORDER):
        done = i < cur or (i == cur and f > 0.99)
        fig.text(0.635 + (i % 2) * 0.17, 0.24 - (i // 2) * 0.037,
                 ("■ " if done else "□ ") + G.PART_NAME[kk].split(" (")[0],
                 color=C["hud"] if done else GRID, fontsize=10)


def token_x(i, n):
    return -40 + 80 * i / max(n - 1, 1)


def s_use(fig, u, sec):
    n_p = len(G.PROMPT)
    ax = add_3d(fig, (0.12, 0.0, 0.62, 0.92), elev=12, azim=-90 + 25 * u, zoom=1.1)
    for k, polys in GEOM.items():
        draw(ax, polys, G.COLOR_OF[k], lw=0.7, alpha=0.35)
    # A: 入力 (0–0.2), B: 層を上る (0.2–0.6), C: 生成 (0.6–1)
    ntype = int(np.clip(u / 0.15, 0, 1) * n_p + 0.999)
    fig.text(0.03, 0.86, "プロンプト:", color=C["hud"], fontsize=13)
    fig.text(0.13, 0.86, "".join(G.PROMPT[:ntype]), color=FG, fontsize=15)
    cx = 0.03
    for t in G.PROMPT[:ntype]:  # トークン・チップ
        fig.text(cx, 0.80, t, color=G.COL["tok"], fontsize=9,
                 bbox=dict(fc=BG, ec=G.COL["tok"], lw=0.8, pad=2))
        cx += 0.0095 * len(t) + 0.02
    climb = smooth((u - 0.18) / 0.42)
    ztop = G.block_z(G.N_SHOWN) + 4
    zt = -18 + (ztop + 18) * climb
    layer = int(np.clip((zt - G.Z0) / G.DZ, 0, G.N_SHOWN - 1))
    xs = [token_x(i, n_p) for i in range(ntype)]
    ax.scatter(xs, [0] * ntype, [zt] * ntype, color=G.COL["tok"], s=30, depthshade=False)
    if 0.2 < u < 0.62:
        A = G.ATTN[layer]
        q = n_p - 1  # 最後のトークンからの注意を弧で描く
        for j in range(n_p):
            w = A[q, j]
            if w < 0.02:
                continue
            t = np.linspace(0, np.pi, 30)
            x = xs[q] + (xs[j] - xs[q]) * (1 - np.cos(t)) / 2
            z = zt + 4 + 10 * w * np.sin(t) * 2
            ax.plot(x, np.zeros_like(x), z, color=G.COL["attn"], lw=0.6 + 4 * w, alpha=0.9)
        # 注意行列のヒートマップ (実計算)
        hm = fig.add_axes([0.03, 0.10, 0.22, 0.36])
        hm.imshow(A, cmap="magma", vmin=0, vmax=1)
        hm.set_xticks([])
        hm.set_yticks([])
        hm.set_title(f"層 {layer + 1}: softmax(QKᵀ/√d + M)", color=FG, fontsize=9)
        fig.text(0.03, 0.06, "小型ランダム初期化モデルでの実計算 (因果マスク)", color=GRID, fontsize=8.5)
        fig.text(0.03, 0.52, f"層 {layer + 1}/{G.N_SHOWN} (実機 96 層) を通過中", color=C["warn"], fontsize=13)
    gen_u = np.clip((u - 0.6) / 0.38, 0, 1)
    ng = int(gen_u * len(G.GEN) + (0.999 if gen_u > 0 else 0))
    if ng:
        text = "".join(t for t, *_ in G.GEN[:ng])
        fig.text(0.03, 0.70, "生成:", color=C["hud"], fontsize=13)
        fig.text(0.09, 0.70, text, color=C["warn"], fontsize=15)
        tok, cands, logits = G.GEN[min(ng, len(G.GEN)) - 1]
        p = G.softmax(logits, G.TEMP)
        bx = fig.add_axes([0.76, 0.40, 0.21, 0.36])
        bx.set_facecolor(BG)
        bx.barh(range(5)[::-1], p, color=[G.COL["unemb"]] + [G.COL["soft"]] * 4)
        bx.set_yticks(range(5)[::-1])
        bx.set_yticklabels(cands, color=FG, fontsize=10)
        bx.set_xlim(0, 1)
        bx.tick_params(colors=FG, labelsize=8)
        for s in bx.spines.values():
            s.set_color(GRID)
        bx.set_title("p = softmax(z / T),  T = 0.8", color=FG, fontsize=10)
        fig.text(0.76, 0.33, "候補と logit は図解用の例示値", color=GRID, fontsize=8.5)
        # 出力の光点が塔頂へ
        ax.scatter([0], [0], [ztop + 20], color=G.COL["unemb"], s=60 + 40 * np.sin(sec * 8), depthshade=False)
    if u > 0.9:
        fig.text(0.76, 0.24, "→ 生成された寸法は\n   輸送機の設計図 (外環 60.088 m,\n   ポッド r 5.021 m) と一致",
                 color=C["hud"], fontsize=11, linespacing=1.5, alpha=smooth((u - 0.9) * 10))


def s_end(fig, u, sec):
    grid_bg(fig)
    ax = add_3d(fig, (0.25, 0.25, 0.5, 0.72), elev=18, azim=-60 + 20 * sec, zoom=1.2)
    for k, polys in GEOM.items():
        draw(ax, polys, G.COLOR_OF[k], lw=0.7, alpha=0.6 * smooth(u * 3))
    a = smooth(u * 3 - 0.3)
    fig.text(0.5, 0.2, f"方程式 {len(EQS)} 本 → 部品 10 点 → 平面図 → 3D → 組み立て → 使用", color=FG,
             fontsize=16, ha="center", alpha=a)
    fig.text(0.5, 0.09, "※ 公開論文の式に基づく図解モデルです。ChatGPT 実機の非公開の構成・寸法を示すものではありません。",
             color=C["warn"], fontsize=12, ha="center", alpha=a)


SCENES = {"title": s_title, "params": s_params, "mapping": s_mapping, "plan": s_plan, "to3d": s_to3d,
          "assembly": s_assembly, "use": s_use, "end": s_end}


def frame(i):
    sec = i / FPS
    name, u, local = TL.at(sec)
    fig = new_fig()
    SCENES[name](fig, u, local)
    if name != "title":
        header(fig, name)
        progress_bar(fig, sec)
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
    base = 0.08 * np.sin(2 * np.pi * 110 * t) + 0.04 * np.sin(2 * np.pi * 164.8 * t)
    u0 = TL.start("use")
    ticks = np.zeros_like(t)
    for k in range(60):  # 生成トークンごとの短いクリック
        tk = u0 + 24 * (0.2 + 0.78 * k / 60)
        m = (t > tk) & (t < tk + 0.05)
        ticks[m] += 0.12 * np.sin(2 * np.pi * 880 * (t[m] - tk)) * np.exp(-(t[m] - tk) * 60)
    env = np.clip(t / 2, 0, 1) * np.clip((TL.total - t) / 2, 0, 1)
    write_wav(path, (base + ticks) * env)


def main():
    if "--preview" in sys.argv:
        from PIL import Image
        os.makedirs(os.path.join(OUT, "preview"), exist_ok=True)
        for name, t0, dur in TL.scenes:
            for frac in (0.5, 0.9):
                i = int((t0 + dur * frac) * FPS)
                Image.fromarray(frame(i)).save(os.path.join(OUT, "preview", f"gpt_{name}_{int(frac*10)}.png"))
        return
    wav = os.path.join(OUT, "_chatgpt.wav")
    soundtrack(wav)
    render_video(os.path.join(OUT, "chatgpt_blueprint.mp4"), N_FRAMES, frame, audio_wav=wav)
    os.remove(wav)
    print("done", N_FRAMES, "frames")


if __name__ == "__main__":
    main()
