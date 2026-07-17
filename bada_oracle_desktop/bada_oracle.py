#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bada Oracle (Desktop) — Windows 10/11 edition.

A PROCEDURAL message generator in the style of the Bada / Omega "Akashic"
motif. It combines poetic fragments using a deterministic hash shaped by the
gamma function and a Shannon-entropy value, and plays a soft biofeedback chime.

⚠️ HONEST NOTE: This does NOT access any "Akashic Record" and does NOT predict
the future. The output is generated art for reflection / entertainment only.
Do not use it to make real-life decisions (health, money, relationships, etc.).

© Masaaki Yamaguchi · 山口雅旭 · Bada Language
"""

import math

try:
    import winsound  # Windows only; used for the chime
    HAVE_SOUND = True
except Exception:
    HAVE_SOUND = False

MASK64 = (1 << 64) - 1

FRAGMENTS = {
    "openings": [
        "静けさの中で、", "遠い水面の向こうに、", "夜明け前のうすあかりに、",
        "巡る季節のはざまで、", "こころの奥の小部屋で、",
        "風がひとつ向きを変えるとき、", "積もった時間の底で、",
    ],
    "images": [
        "ひとすじの光がゆっくりほどけていきます。",
        "小さな種が、まだ見えない芽をあたためています。",
        "古い扉の鍵が、静かに手になじみます。",
        "遠くの鐘が、やわらかく余韻を残します。",
        "川はいそがず、けれど確かに海へ向かいます。",
        "霧が晴れ、輪郭がすこしずつ戻ってきます。",
        "星が一つ、名前を思い出したように瞬きます。",
    ],
    "guidance": [
        "急がなくてよい。あなたの歩幅で十分に間に合います。",
        "手放すことは、負けることではありません。",
        "小さな「はい」が、大きな流れを呼びます。",
        "答えはすでに、あなたの呼吸の中にあります。",
        "今日の休息は、明日の力になります。",
        "比べる相手は、昨日のあなただけで足ります。",
        "うまく言えない気持ちも、ちゃんと意味を持っています。",
    ],
    "closings": [
        "——それで、だいじょうぶ。", "——ゆっくりでいい。",
        "——あなたはもう気づいている。", "——今はそれで満ちている。",
        "——また、朝は来ます。", "——その静けさを信じて。",
    ],
}

_LANCZOS = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
]


def gamma(x):
    if x < 0.5:
        return math.pi / (math.sin(math.pi * x) * gamma(1 - x))
    x -= 1.0
    a = _LANCZOS[0]
    t = x + 7.0 + 0.5
    for i in range(1, len(_LANCZOS)):
        a += _LANCZOS[i] / (x + i)
    return math.sqrt(2 * math.pi) * (t ** (x + 0.5)) * math.exp(-t) * a


def shannon(p):
    p = min(max(p, 0.01), 0.99)
    return (-p * math.log(p) - (1 - p) * math.log(1 - p)) / math.log(2.0)


def _mix(v):
    x = v & MASK64
    x ^= x >> 33
    x = (x * 0xFF51AFD7ED558CCD) & MASK64
    x ^= x >> 29
    x = (x * 0xC4CEB9FE1A85EC53) & MASK64
    x ^= x >> 32
    return x & 0x7FFFFFFFFFFFFFFF


def generate(question, nonce):
    q = question.strip() or "∞"
    base = (abs(hash(q)) & 0xFFFFFFFF)
    seed = _mix(base ^ ((nonce * 0x9E3779B97F4A7C15) & MASK64))

    p = ((seed >> 8) & 0xFFFF) / 0xFFFF
    entropy = shannon(p)
    g_shape = 1.0 + 3.0 * (((seed >> 20) & 0xFF) / 255.0)
    g = gamma(g_shape)

    seed = _mix(seed ^ (int(g * 1000) ^ int(entropy * 1e6)))

    def pick(key):
        nonlocal seed
        seed = _mix(seed)
        lst = FRAGMENTS[key]
        return lst[((seed >> 16) & 0x7FFFFFFF) % len(lst)]

    message = (
        pick("openings") + pick("images") + "\n\n"
        + pick("guidance") + "\n" + pick("closings")
    )
    return message, g, entropy, "0x%08X" % base


class OracleApp:
    BG = "#060410"
    PANEL = "#120C22"
    VIOLET = "#9060D0"
    GOLD = "#C8A44A"
    DIM = "#8A93A0"
    WARN = "#E0A24A"
    TEXT = "#E6EAF0"

    def __init__(self, root):
        self.root = root
        self.taps = 0
        root.title("Bada Oracle")
        root.configure(bg=self.BG)
        root.geometry("560x640")

        tk.Label(root, text="Bada Oracle", fg=self.GOLD, bg=self.BG,
                 font=("Yu Gothic UI", 22, "bold")).pack(pady=(16, 0))
        tk.Label(root, text="Γ(s) · 大域的部分積分多様体 · 手続き的託宣ジェネレーター",
                 fg=self.DIM, bg=self.BG, font=("Yu Gothic UI", 9)).pack()

        disc = ("⚠ これは娯楽・内省のための生成アートです。アカシックレコードへのアクセスや\n"
                "未来の予知ではありません。健康・お金・進路など重要な判断の根拠には\n"
                "使わないでください。")
        tk.Label(root, text=disc, fg=self.WARN, bg="#1A130A", justify="left",
                 font=("Yu Gothic UI", 9), wraplength=520).pack(fill="x", padx=16, pady=10)

        tk.Label(root, text="いま心にあること（任意）", fg=self.DIM, bg=self.BG,
                 font=("Yu Gothic UI", 10)).pack(anchor="w", padx=16)
        self.entry = tk.Entry(root, bg=self.PANEL, fg=self.TEXT, insertbackground=self.TEXT,
                              relief="flat", font=("Yu Gothic UI", 12))
        self.entry.pack(fill="x", padx=16, pady=(2, 10), ipady=6)

        tk.Button(root, text="受信する", command=self.receive, bg=self.VIOLET, fg=self.BG,
                  activebackground=self.GOLD, relief="flat", font=("Yu Gothic UI", 13, "bold")
                  ).pack(fill="x", padx=16, ipady=8)

        self.out = scrolledtext.ScrolledText(
            root, bg=self.PANEL, fg=self.TEXT, relief="flat", wrap="word",
            font=("Yu Gothic UI", 13), height=8, padx=14, pady=14)
        self.out.pack(fill="both", expand=True, padx=16, pady=14)
        self.out.insert("1.0", "「受信する」を押してください。\n\n※ 生成アートです（予知ではありません）。")
        self.out.configure(state="disabled")

        self.tele = tk.Label(root, text="", fg=self.DIM, bg=self.BG, font=("Consolas", 9))
        self.tele.pack()
        tk.Label(root, text="© Masaaki Yamaguchi · 山口雅旭 · Bada Language",
                 fg=self.DIM, bg=self.BG, font=("Yu Gothic UI", 8)).pack(pady=(0, 8))

    def receive(self):
        self.taps += 1
        msg, g, ent, seed = generate(self.entry.get(), self.taps)
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", msg)
        self.out.configure(state="disabled")
        self.tele.configure(text="seed %s  Γ=%.4f  S=%.4f bits" % (seed, g, ent))
        if HAVE_SOUND:
            try:
                winsound.Beep(int(440 + g * 30), 500)
            except Exception:
                pass


def main():
    global tk, scrolledtext
    import tkinter as tk
    from tkinter import scrolledtext
    root = tk.Tk()
    OracleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
