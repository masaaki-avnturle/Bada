"""
compose.py — 「Bada Fusion Suite — Fuga · Requiem · Ave Verum · Acceptance」

構成(すべてオリジナルの旋律・和声。公有のバッハ/モーツァルトの様式に倣い、
坂本龍一作品は旋律を引用せず「様式」だけを参照している):

  I   前奏 (瞑想)         A minor  — ドローン + 主題の拡大形 + 録音の霧
  II  フーガ (バッハ様式)  A minor  — 3声・提示部/嬉遊部/中間部/ストレッタ/終結
  III レクイエム (パッサカリア) A minor — 半音階下行の嘆きのバス + 合唱 + 弦の哀歌
  IV  コラール (アヴェ・ベルム・コルプス様式) F major — E7 → F の偽終止で「ほっと一安心」
  V   バラード (坂本龍一様式 / 鉄道員の郷愁) F major — ピアノ + 弦
  VI  コーダ (Acceptance 様式の瞑想) F major — パッド + 疎らなピアノ + 鐘

ユーザーがアップロードした 16 本の音源は、調ごとに対応する楽章へ
(ピッチシフト/タイムストレッチ/ローパス/リバーブで)溶け込ませている。
"""
import os
import sys
import json
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from synth import Mixer, make_ir, soft_limit, write_wav, SR  # noqa: E402

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
UPLOADS = os.environ.get("UPLOADS", "")
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(__file__), "out"))
os.makedirs(OUT, exist_ok=True)

rng = np.random.default_rng(20260922)


# ================================================================ helpers
class Section:
    """拍 → 秒 変換つきのセクション。start は絶対秒。"""

    def __init__(self, mx, start, bpm):
        self.mx, self.start, self.bpm = mx, start, bpm
        self.spb = 60.0 / bpm

    def t(self, beat):
        return self.start + beat * self.spb

    def note(self, inst, beat, midi, beats, vel=0.7, pan=0.0, gain=1.0, legato=1.0, **kw):
        self.mx.note(inst, self.t(beat), midi, beats * self.spb * legato, vel, pan, gain, **kw)

    def line(self, inst, beat, seq, vel=0.7, pan=0.0, gain=1.0, transpose=0, legato=0.98, humanize=0.0):
        """seq = [(midi|None, beats), ...]  None は休符。"""
        b = beat
        for m, d in seq:
            if m is not None:
                v = vel + (rng.uniform(-humanize, humanize) if humanize else 0)
                self.note(inst, b, m + transpose, d, max(0.05, min(1, v)), pan, gain, legato)
            b += d
        return b

    def chord(self, inst, beat, midis, beats, vel=0.6, pan_spread=0.4, gain=1.0, **kw):
        k = len(midis)
        for i, m in enumerate(midis):
            pan = -pan_spread + 2 * pan_spread * i / max(1, k - 1) if k > 1 else 0
            self.note(inst, beat, m, beats, vel, pan, gain, **kw)


def diatonic_transpose(seq, mapping):
    return [(mapping.get(m, m) if m is not None else None, d) for m, d in seq]


# ================================================================ uploaded audio layers
def layer(mx, name, start, dur, at, gain_db, lowpass=None, highpass=None, pitch=0, tempo=1.0,
          fade=4.0, pan=0.0, send=0.5):
    """アップロード音源の一部を ffmpeg で加工して mx に重ねる。"""
    src = None
    if UPLOADS:
        for f in os.listdir(UPLOADS):
            if name in f:
                src = os.path.join(UPLOADS, f)
                break
    if src is None:
        print(f"  [layer] {name}: not found, skipped")
        return
    out_len = dur / tempo
    filters = []
    if pitch or tempo != 1.0:
        filters.append(f"rubberband=pitch={2 ** (pitch / 12):.6f}:tempo={tempo}")
    if highpass:
        filters.append(f"highpass=f={highpass}")
    if lowpass:
        filters.append(f"lowpass=f={lowpass}")
    filters.append(f"afade=t=in:st=0:d={fade}")
    filters.append(f"afade=t=out:st={max(0, out_len - fade)}:d={fade}")
    filters.append("aresample=44100")
    tmp = os.path.join(OUT, f"_layer_{name[:8]}_{int(at)}.wav")
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(start), "-t", str(dur),
           "-i", src, "-af", ",".join(filters), "-ac", "2", "-ar", str(SR), "-f", "wav", tmp]
    subprocess.run(cmd, check=True)
    from scipy.io import wavfile
    sr, x = wavfile.read(tmp)
    x = x.astype(np.float32) / 32768
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    # 正規化してから gain
    peak = np.abs(x).max() + 1e-6
    x = x / peak * (10 ** (gain_db / 20))
    if pan:
        l = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
        r = np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        x[:, 0] *= l
        x[:, 1] *= r
    mx.stereo(x, at, 1.0, send)
    os.remove(tmp)
    print(f"  [layer] {name}: {start:.0f}s+{dur:.0f}s -> t={at:.0f}s ({out_len:.0f}s) {gain_db}dB")


# ================================================================ I. PRELUDE (A minor, meditative)
SUBJECT = [(69, 1), (76, 1), (72, .5), (71, .5), (69, .5), (68, .5),
           (69, 1.5), (71, .5), (72, .5), (74, .5), (76, 1)]                     # 8 拍
ANSWER = [(76, 1), (83, 1), (79, .5), (78, .5), (76, .5), (75, .5),
          (76, 1.5), (78, .5), (79, .5), (81, .5), (83, 1)]                      # 実応答(属調)
COUNTER = [(60, .5), (64, .5), (67, 1), (69, .5), (68, .5), (65, .5), (62, .5),
           (60, 1.5), (62, .5), (64, .5), (65, .5), (68, .5), (64, .5)]          # 対主題 8 拍(八度で転回可能)
# A minor → C major(平行調)の全音階的移高
TO_C = {69: 72, 76: 79, 72: 76, 71: 74, 68: 71, 74: 77, 60: 64, 64: 67, 67: 71, 65: 69, 62: 65}
SUBJECT_C = diatonic_transpose(SUBJECT, TO_C)
COUNTER_C = diatonic_transpose(COUNTER, TO_C)


def prelude(mx, start):
    s = Section(mx, start, 60)
    s.note("drone", 0, 33, 46, vel=0.9)             # A1
    s.note("drone", 0.5, 45, 45, vel=0.35, pan=0.2)  # A2
    s.note("pad", 4, 57, 40, vel=0.35, pan=-0.3)
    s.note("pad", 6, 64, 38, vel=0.3, pan=0.3)
    # 主題の拡大形(4 倍)を疎らなピアノで
    s.line("piano", 8, [(m, d * 4) for m, d in SUBJECT], vel=0.45, pan=0.1, legato=0.7, humanize=0.05)
    s.line("piano", 8, [(m - 24, d * 4) for m, d in SUBJECT[:2]] + [(None, 24)] + [(45, 8)], vel=0.3, pan=-0.2, legato=0.6)
    for b, m in [(2, 81), (14, 76), (26, 84), (36, 81)]:
        s.note("bell", b, m, 3, vel=0.22, pan=rng.uniform(-0.5, 0.5))
    s.chord("strings", 40, [57, 64, 69, 72], 8, vel=0.4)  # Am へ収束
    return s.t(48)


# ================================================================ II. FUGUE (A minor, 72 bpm)
def fugue(mx, start):
    s = Section(mx, start, 72)
    P, A, B = 0.35, 0.0, -0.35  # pan: soprano / alto / bass
    v = 0.62
    inst = "piano"
    # --- 提示部
    s.line(inst, 0, SUBJECT, vel=v, pan=A)                                  # アルト: 主題
    s.line(inst, 8, ANSWER, vel=v + 0.05, pan=P)                            # ソプラノ: 応答
    s.line(inst, 8, COUNTER, vel=v - 0.1, pan=A, transpose=7 - 12)          # アルト: 対主題
    s.line(inst, 16, SUBJECT, vel=v + 0.05, pan=B, transpose=-24)           # バス: 主題
    s.line(inst, 16, COUNTER, vel=v - 0.05, pan=P, transpose=12)            # ソプラノ: 対主題
    s.line(inst, 16, [(64, 1), (59, 1), (64, 1), (60, .5), (59, .5),
                      (64, 1.5), (65, .5), (67, .5), (69, .5), (71, 1)], vel=v - 0.15, pan=A)  # アルト自由
    # --- 嬉遊部 1 (Am G F E)
    s.line(inst, 24, [(69, .5), (76, .5), (72, .5), (71, .5), (67, .5), (74, .5), (71, .5), (69, .5),
                      (65, .5), (72, .5), (69, .5), (67, .5), (64, .5), (71, .5), (68, .5), (69, .5)], vel=v, pan=P)
    s.line(inst, 24, [(60, 1), (64, 1), (59, 1), (62, 1), (57, 1), (60, 1), (56, 1), (59, 1)], vel=v - 0.15, pan=A)
    s.line(inst, 24, [(45, 2), (43, 2), (41, 2), (40, 2)], vel=v - 0.05, pan=B)
    # --- 中間部 (C major)
    s.line(inst, 32, SUBJECT_C, vel=v + 0.05, pan=P)
    s.line(inst, 32, COUNTER_C, vel=v - 0.05, pan=B, transpose=-12)
    s.line(inst, 32, [(67, 1), (62, 1), (67, .5), (67, .5), (64, .5), (67, .5),
                      (67, 1.5), (69, .5), (71, .5), (72, .5), (74, .5), (71, .5)], vel=v - 0.15, pan=A)
    # --- 嬉遊部 2 (Dm Em F E7) 上行して A minor へ
    s.line(inst, 40, [(74, .5), (81, .5), (77, .5), (76, .5), (76, .5), (83, .5), (79, .5), (77, .5),
                      (77, .5), (84, .5), (81, .5), (79, .5), (76, .5), (83, .5), (80, .5), (81, .5)], vel=v + 0.05, pan=P)
    s.line(inst, 40, [(65, 1), (69, 1), (67, 1), (71, 1), (69, 1), (72, 1), (71, 1), (74, 1)], vel=v - 0.15, pan=A)
    s.line(inst, 40, [(50, 2), (52, 2), (53, 2), (52, 2)], vel=v, pan=B)
    # --- ストレッタ (バス主題、2 拍遅れでソプラノ主題) + 属音保続
    s.line(inst, 48, SUBJECT, vel=v + 0.1, pan=B, transpose=-24)
    s.line(inst, 50, SUBJECT, vel=v + 0.1, pan=P)
    s.line("strings", 50, SUBJECT, vel=0.35, pan=P, transpose=12, legato=0.9)
    s.line(inst, 48, [(60, 1), (64, 1), (64, 1), (60, .5), (59, .5), (64, 2), (64, .5), (65, .5), (60, .5), (59, .5),
                      (69, .5), (71, .5), (68, 1), (71, .5), (69, .5), (68, .5), (59, .5)], vel=v - 0.15, pan=A)
    s.line(inst, 56, [(40, 4)], vel=v + 0.1, pan=B)                          # E ペダル
    s.line("organ", 56, [(28, 4)], vel=0.5, pan=B)
    s.line(inst, 58, [(74, .5), (72, .5), (71, .5), (68, .5)], vel=v, pan=P)
    # --- 終結: 主題 + 和声 + ピカルディ
    s.line(inst, 60, SUBJECT, vel=v + 0.12, pan=P)
    s.line("strings", 60, SUBJECT, vel=0.4, pan=P, transpose=12, legato=0.9)
    s.line(inst, 60, [(64, 1), (67, 1), (69, 1), (59, 1), (60, 1.5), (64, .5), (69, .5), (71, .5), (68, 1)], vel=v - 0.15, pan=A)
    s.line(inst, 60, [(45, 1), (48, 1), (41, 1), (40, 1), (45, 2), (41, .5), (43, .5), (40, 1)], vel=v, pan=B)
    s.line("organ", 60, [(33, 1), (36, 1), (29, 1), (28, 1), (33, 2), (29, .5), (31, .5), (28, 1)], vel=0.45, pan=B)
    s.chord("piano", 68, [45, 57, 61, 64, 69, 73], 5, vel=0.7)
    s.chord("strings", 68, [57, 61, 64, 69], 6, vel=0.45)
    s.chord("organ", 68, [33, 45, 52, 61], 6, vel=0.5)
    s.note("bell", 68, 81, 4, vel=0.25)
    return s.t(74)


# ================================================================ III. REQUIEM (passacaglia, A minor, 60 bpm)
GROUND = [(45, 2), (44, 2), (43, 2), (42, 2), (41, 2), (40, 2), (38, 1), (40, 1), (45, 2)]   # 16 拍
CHORDS = [((60, 64, 69), 2), ((59, 64, 68), 2), ((60, 64, 67), 2), ((57, 62, 66), 2),
          ((57, 60, 65), 2), ((56, 59, 64), 2), ((57, 62, 65), 1), ((56, 59, 62), 1), ((57, 60, 64), 2)]
LAMENT1 = [(76, 2), (76, 1), (74, 1), (72, 2), (74, 1), (69, 1), (69, 1), (72, 1), (71, 2), (69, 1), (68, 1), (69, 2)]
LAMENT2 = [(76, 1), (77, 1), (76, 1), (74, 1), (72, 1), (76, 1), (74, 1), (78, 1), (77, 1), (72, 1), (71, 2), (69, 1), (74, 1), (72, 2)]


def requiem(mx, start):
    s = Section(mx, start, 60)
    n_cycles = 6
    for c in range(n_cycles):
        b0 = c * 16
        last = c == n_cycles - 1
        # 地のバス
        g = GROUND if not last else GROUND[:7] + [(40, 5)]   # 最終周は E7 のまま止める(→ F へ偽終止)
        s.line("strings", b0, g, vel=0.55, pan=-0.3, transpose=-12, legato=0.98)
        s.line("organ", b0, g, vel=0.35 + 0.05 * c, pan=-0.2, transpose=-12)
        if c >= 1:
            s.line("piano", b0, g, vel=0.5, pan=-0.35, legato=0.9)
        if c == 0:
            s.line("piano", b0, g, vel=0.45, pan=-0.2, transpose=12, legato=0.9)
        # 合唱
        if c >= 1:
            b = b0
            ch = CHORDS if not last else CHORDS[:7] + [((56, 59, 62), 5)]
            for midis, d in ch:
                vel = 0.4 + 0.045 * min(c, 4)
                s.chord("choir", b, midis, d, vel=vel, pan_spread=0.5, legato=1.0, vowel="ah" if c < 4 else "oh")
                if c >= 4:
                    s.chord("choir", b, [m + 12 for m in midis[:2]], d, vel=vel * 0.55, pan_spread=0.3, vowel="oh")
                    s.chord("strings", b, midis, d, vel=0.35, pan_spread=0.3)
                b += d
        # 弦の哀歌
        if c in (2, 4):
            s.line("strings", b0, LAMENT1, vel=0.55, pan=0.3, legato=0.97)
        if c in (3, 5):
            lam = LAMENT2 if not last else LAMENT2[:12] + [(68, 1), (76, 3)]
            s.line("strings", b0, lam, vel=0.6, pan=0.3, legato=0.97)
            if not last:
                s.line("strings", b0, lam, vel=0.3, pan=0.45, transpose=12, legato=0.97)
        # ピアノのアルペジオ(第 4-5 周)
        if c in (3, 4):
            b = b0
            ch = CHORDS
            for midis, d in ch:
                arp = [midis[0] + 12, midis[1] + 12, midis[2] + 12, midis[1] + 24] * 2
                seq = [(arp[i % len(arp)], .5) for i in range(int(d * 2))]
                s.line("piano", b, seq, vel=0.32, pan=0.2, legato=1.4, humanize=0.04)
                b += d
        # 鐘(周の頭)
        s.note("bell", b0, 69 if c % 2 == 0 else 76, 3, vel=0.2, pan=rng.uniform(-0.4, 0.4))
    # 最終 E7 の上で「ほっ」と息をつく前の間
    end_beat = n_cycles * 16
    s.chord("pad", end_beat - 5, [52, 56, 59, 62], 6, vel=0.4)
    return s.t(end_beat + 1)


# ================================================================ IV. CHORALE (Ave Verum style, F major, 58 bpm)
# (S, A, T, B, 拍, ソプラノの掛留音 or None)
CHORALE = [
    (65, 60, 57, 41, 4, None),
    (65, 62, 58, 46, 2, None), (67, 64, 60, 48, 2, None),
    (69, 65, 60, 53, 2, None), (70, 65, 62, 55, 2, None),
    (69, 65, 60, 57, 2, None), (67, 62, 59, 43, 2, 69),
    (67, 64, 60, 48, 4, None),
    (65, 60, 57, 45, 2, None), (64, 60, 57, 45, 2, None),
    (62, 58, 55, 43, 2, None), (64, 60, 55, 48, 2, None),
    (65, 60, 57, 53, 2, None), (67, 62, 58, 46, 2, None),
    (64, 60, 58, 48, 2, 65), (65, 60, 57, 41, 2, None),
    (69, 65, 62, 50, 2, None), (69, 66, 62, 50, 2, None),
    (70, 67, 62, 55, 2, None), (70, 65, 62, 58, 2, None),
    (69, 65, 60, 53, 2, None), (67, 64, 60, 48, 2, None),
    (65, 62, 58, 46, 2, None), (64, 60, 55, 48, 2, 65),
    (65, 60, 57, 53, 2, None), (69, 65, 60, 53, 2, None),
    (70, 65, 62, 58, 2, None), (72, 67, 64, 60, 2, None),
    (70, 65, 62, 55, 2, None), (69, 65, 62, 50, 2, None),
    (64, 60, 58, 48, 2, 65), (65, 60, 57, 41, 6, None),
    (69, 65, 60, 53, 6, None),
]


def chorale(mx, start):
    s = Section(mx, start, 58)
    b = 0
    pans = [0.35, 0.12, -0.12, -0.35]
    for i, (S_, A_, T_, B_, d, susp) in enumerate(CHORALE):
        vel = 0.5 + 0.12 * (1 if 24 <= b < 32 else 0)   # 第 4 楽句のクライマックス
        voices = [S_, A_, T_, B_]
        for vi, m in enumerate(voices):
            if vi == 0 and susp is not None:
                s.note("choir", b, susp, 1, vel, pans[vi], legato=1.02)
                s.note("choir", b + 1, m, d - 1, vel, pans[vi], legato=1.02)
                s.note("strings", b, susp, 1, vel * 0.55, pans[vi], legato=1.0)
                s.note("strings", b + 1, m, d - 1, vel * 0.55, pans[vi], legato=1.0)
            else:
                s.note("choir", b, m, d, vel * (0.9 if vi == 3 else 1), pans[vi], legato=1.02)
                s.note("strings", b, m, d, vel * 0.55, pans[vi], legato=1.0)
        s.note("organ", b, B_ - 12, d, 0.3, -0.2)
        s.note("organ", b, B_, d, 0.2, -0.2)
        if i % 2 == 0:
            s.note("piano", b, S_ + 12, d, 0.28, 0.3, legato=0.9)   # 高音でそっと旋律をなぞる
        b += d
    # 最後の F の上で鐘
    s.note("bell", b - 12, 77, 4, vel=0.22, pan=0.3)
    s.note("bell", b - 6, 84, 4, vel=0.18, pan=-0.3)
    s.chord("pad", b - 12, [53, 60, 65, 69], 14, vel=0.35)
    return s.t(b + 2)


# ================================================================ V. BALLAD (Sakamoto-style, F major, 66 bpm)
# (バス midi, コードトーン(上向き), 拍)
BALLAD = [
    (41, [53, 57, 60, 64, 67], 4),          # Fmaj9
    (40, [52, 55, 60, 64], 4),              # C/E
    (38, [50, 57, 60, 64, 65], 4),          # Dm9
    (46, [58, 62, 65, 69], 4),              # Bbmaj7
    (43, [55, 58, 62, 65], 4),              # Gm7
    (48, [55, 60, 65, 70], 2), (48, [52, 55, 58, 60], 2),   # C7sus4 → C7
    (41, [53, 57, 60, 64], 4),              # Fmaj7
    (45, [52, 57, 60, 67], 2), (45, [52, 57, 61, 67], 2),   # Am7 → A7
    (38, [50, 57, 60, 64, 65], 4),          # Dm9
    (46, [58, 62, 65, 69], 4),              # Bbmaj7
    (43, [55, 58, 62, 65], 4),              # Gm7
    (39, [51, 55, 58, 62], 4),              # Ebmaj7 (借用)
    (41, [53, 57, 62], 2), (46, [53, 58, 61], 2),           # Dm/F → Bbm
    (48, [53, 57, 60], 2), (48, [55, 58, 60, 65], 2),       # F/C → C7sus
    (41, [53, 57, 60, 64, 67], 4),          # Fmaj9
    (41, [53, 57, 60, 64, 67], 4),          # Fmaj9 (hold)
]
BALLAD_MELODY = [
    (69, 1), (72, 1), (67, 2),
    (67, 2), (64, 1), (62, 1),
    (65, 1), (69, 1), (76, 2),
    (74, 1), (72, 1), (69, 2),
    (70, 1), (69, 1), (67, 1), (65, 1),
    (67, 2), (65, 1), (64, 1),
    (65, 2), (69, 1), (72, 1),
    (76, 2), (73, 1), (76, 1),
    (77, 2), (76, 1), (74, 1),
    (74, 2), (77, 1), (81, 1),
    (79, 2), (77, 1), (74, 1),
    (74, 2), (70, 2),
    (69, 2), (77, 1), (73, 1),
    (72, 2), (70, 1), (67, 1),
    (69, 1), (67, 1), (65, 2),
    (65, 4),
]


def ballad(mx, start):
    s = Section(mx, start, 66)
    b = 0
    for bass, tones, d in BALLAD:
        # 左手: バス + 分散和音(8 分)
        s.note("piano", b, bass, d, 0.5, -0.3, legato=0.95)
        s.note("piano", b, bass + 7, d, 0.3, -0.25, legato=0.95)
        pattern = [tones[0], tones[1], tones[2], tones[-1], tones[2], tones[1]]
        seq = [(pattern[i % len(pattern)], .5) for i in range(int(d * 2))]
        s.line("piano", b, seq, vel=0.3, pan=-0.1, legato=1.6, humanize=0.05)
        # 弦のパッド(コードトーン)
        s.chord("strings", b, [t for t in tones if t >= 55][:4], d, vel=0.22, pan_spread=0.35)
        s.note("pad", b, bass + 12, d, 0.25, 0.1)
        b += d
    total = b
    # 右手: 旋律(2 回目はオクターブ上 + 鐘で重ねる)
    end = s.line("piano", 0, BALLAD_MELODY, vel=0.68, pan=0.25, legato=0.95, humanize=0.06)
    # 後半(9 小節目〜)に鐘の重ね
    b = 0
    for i, (m, d) in enumerate(BALLAD_MELODY):
        if 32 <= b < 56 and d >= 2:
            s.note("bell", b, m + 12, d, 0.14, 0.35)
        if 32 <= b < 60:
            s.note("strings", b, m + 12, d, 0.2, 0.4, legato=0.95)
        b += d
    s.note("bell", 64, 77, 4, 0.2, 0.2)
    s.chord("pad", 64, [41, 53, 60, 64, 67], 10, vel=0.35)
    return s.t(total + 2)


# ================================================================ VI. CODA (Acceptance-style meditation, F major, 50 bpm)
CODA_CHORDS = [
    ([41, 53, 60, 65, 67], 8),   # F(add9)
    ([38, 50, 57, 60, 64], 8),   # Dm9
    ([46, 58, 62, 65, 69], 8),   # Bbmaj7
    ([48, 53, 57, 60], 8),       # F/C
    ([41, 53, 60, 64, 67], 20),  # Fmaj9 hold
]
CODA_PIANO = [(0, 69), (3, 72), (6, 67), (10, 65), (13, 74), (17, 69), (22, 76), (26, 72),
              (30, 70), (33, 69), (38, 67), (42, 65), (48, 60), (52, 65)]


def coda(mx, start):
    s = Section(mx, start, 50)
    s.note("drone", 0, 29, 60, vel=0.8)          # F1
    s.note("drone", 2, 36, 56, vel=0.3, pan=0.2)  # C2
    b = 0
    for midis, d in CODA_CHORDS:
        s.chord("pad", b, midis[1:], d, vel=0.42, pan_spread=0.5)
        s.chord("choir", b + 1, midis[2:], d - 1, vel=0.22, pan_spread=0.4, vowel="oh")
        s.note("strings", b, midis[0] + 12, d, 0.25, -0.2)
        s.note("bell", b, midis[-1] + 12, 4, 0.14, rng.uniform(-0.5, 0.5))
        b += d
    for beat, m in CODA_PIANO:
        s.note("piano", beat, m, 3, 0.42, rng.uniform(-0.3, 0.3), legato=0.8)
        if beat % 2 == 0:
            s.note("piano", beat, m - 12, 3, 0.2, 0.0, legato=0.8)
    s.note("bell", 52, 89, 6, 0.12, 0.3)
    return s.t(b + 6)


# ================================================================ assemble
def main():
    total = 470.0
    mx = Mixer(total)
    print("composing...")
    t0 = 0.0
    t1 = prelude(mx, t0)
    t2 = fugue(mx, t1 - 1.0)
    t3 = requiem(mx, t2 - 0.5)
    t4 = chorale(mx, t3 - 0.5)
    t5 = ballad(mx, t4 - 1.0)
    t6 = coda(mx, t5 - 1.5)
    marks = {"prelude": t0, "fugue": t1 - 1.0, "requiem": t2 - 0.5, "chorale": t3 - 0.5,
             "ballad": t4 - 1.0, "coda": t5 - 1.5, "end": t6}
    print(json.dumps(marks, indent=1))

    # ---- uploaded recordings (調ごとに配置)
    print("layering uploaded recordings...")
    pre, fug, req, cho, bal, cod = (marks[k] for k in ("prelude", "fugue", "requiem", "chorale", "ballad", "coda"))
    req_len, cho_len, bal_len, cod_len = cho - req, bal - cho, cod - bal, t6 - cod
    # I 前奏: A minor の録音を半速・1 オクターブ下で霧に
    layer(mx, "756b07ab", 20, 22, pre + 4, -22, lowpass=1200, pitch=-12, tempo=0.5, fade=6, pan=-0.2)
    layer(mx, "76ed9375", 60, 20, pre + 14, -28, lowpass=500, pitch=-12, tempo=0.5, fade=8, pan=0.3)
    # II フーガ: A minor の録音を遠くに
    layer(mx, "768f36de", 5, 60, fug + 4, -25, lowpass=2500, highpass=200, fade=6, pan=0.3)
    # III レクイエム: A minor の録音を重ねる
    layer(mx, "14ae512f", 20, min(96, req_len - 4), req + 2, -21, lowpass=2500, highpass=150, fade=8, pan=-0.35)
    layer(mx, "d954e87d", 60, min(90, req_len - 8), req + 6, -24, lowpass=2000, highpass=300, fade=8, pan=0.35)
    layer(mx, "6cbfd212", 30, 34, req + 48, -22, lowpass=2200, highpass=200, fade=6, pan=0.1)
    layer(mx, "99b7ddad", 10, 24, req + 30, -28, lowpass=500, pitch=-12, tempo=0.5, fade=8, pan=-0.1)
    # IV コラール: F major の録音
    layer(mx, "22a1e536", 0, min(72, cho_len - 2), cho + 1, -22, lowpass=2000, highpass=150, fade=8, pan=0.3)
    layer(mx, "c5c98299", 0, min(70, cho_len - 4), cho + 3, -26, lowpass=1800, highpass=200, fade=8, pan=-0.3)
    # V バラード: Bada Suite (F major) と Bb minor 録音の霧
    layer(mx, "b6834dcd", 100, min(64, bal_len - 2), bal + 1, -24, lowpass=4000, highpass=120, fade=8, pan=0.0)
    layer(mx, "f280c90f", 10, 30, bal + 8, -30, lowpass=450, pitch=-12, tempo=0.5, fade=10, pan=-0.3)
    layer(mx, "4c17f443", 10, 26, bal + 30, -30, lowpass=450, pitch=-12, tempo=0.5, fade=10, pan=0.3)
    # VI コーダ: 息 + Bada Suite-1 (C major) + G/C major 録音を半速で
    layer(mx, "ee64108e", 0, 10, cod + 0.5, -18, lowpass=6000, highpass=100, fade=2, pan=0.0)
    layer(mx, "e8c8a393", 300, min(36, cod_len / 2 - 2), cod + 3, -25, lowpass=1500, highpass=120, pitch=0, tempo=0.5, fade=10)
    layer(mx, "f416529b", 20, min(60, cod_len - 6), cod + 5, -27, lowpass=1500, highpass=150, fade=10, pan=0.3)
    layer(mx, "526416ff", 10, 24, cod + 20, -30, lowpass=600, pitch=-12, tempo=0.5, fade=10, pan=-0.3)

    print("reverb + master...")
    ir = make_ir(3.4, 1.25)
    mix = mx.render(ir, wet=0.9)
    n_end = int(t6 * SR)
    mix = mix[:n_end]
    # 全体のフェードアウト(最後 8 秒)
    nf = int(8 * SR)
    mix[-nf:] *= np.linspace(1, 0, nf)[:, None]
    mix = soft_limit(mix, 0.93)
    wav = os.path.join(OUT, "bada_fusion_suite.wav")
    write_wav(wav, mix)
    with open(os.path.join(OUT, "marks.json"), "w") as f:
        json.dump(marks, f, indent=1)
    print("wrote", wav, f"{len(mix) / SR:.1f}s peak={np.abs(mix).max():.2f}")


if __name__ == "__main__":
    main()
