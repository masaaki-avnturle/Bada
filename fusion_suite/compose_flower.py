"""
compose_flower.py — 「Bada Flower Suite」 交響曲版 / ピアノ協奏曲版

前作(compose.py)のフーガ主題とレクイエムの嘆きのバスを、
坂本龍一《A Flower Is Not a Flower》様式(♩=54、疎らな旋律、長い休符、
add9 / maj7♯11 の和声、ペダルの残響)で統合し直す。旋律・和声はオリジナル。

  統合の仕掛け
  ・「花」の主題の頭 E–C–B は、フーガ主題 A–E–C–B の頭の 3 音(共通の動機)
  ・第 III 楽章はフーガ主題の 2 倍拡大形(16 拍)を、レクイエムの地のバス(16 拍)の
    上に乗せる「レクイエムのバスによるフーガ」。合唱和声・弦の哀歌もその上に重なる

  楽章
  I   花の前奏      ♩=54  A minor   花の主題(2 回)+ 主題頭の対旋律
  II  フーガ        ♩=69  A minor   前作の 3 声フーガを管弦楽化(協奏曲版はピアノが主導)
  II' カデンツァ    ♩=69            協奏曲版のみ: ピアノ独奏のストレッタと花の溜息
  III レクイエムのバスによるフーガ ♩=60  拡大主題 × 地のバス × 合唱 × 哀歌
  IV  花の後奏      ♩=54  A minor → A major の鐘で閉じる

  mode = "symphony"  管弦楽(弦・フルート・ホルン・オルガン・合唱・ティンパニ・ハープ)、ピアノなし
  mode = "concerto"  ピアノ独奏 + 管弦楽
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from synth import Mixer, make_ir, soft_limit, compress, write_wav, SR  # noqa: E402
import compose as C  # noqa: E402  (Section / layer / SUBJECT / GROUND などを再利用)

OUT = C.OUT
MODE = os.environ.get("MODE", "symphony")
rng = np.random.default_rng(54)

Section = C.Section
SUBJECT, ANSWER, COUNTER = C.SUBJECT, C.ANSWER, C.COUNTER
SUBJECT_C, COUNTER_C = C.SUBJECT_C, C.COUNTER_C
GROUND, CHORDS, LAMENT1, LAMENT2 = C.GROUND, C.CHORDS, C.LAMENT1, C.LAMENT2
# 拡大主題の導音 G♯(第 7 拍)と衝突しないよう、第 4 和音を D/F♯ → Bm/F♯ に、哀歌の第 7 拍を A → B に
CHORDS_RF = CHORDS[:3] + [((59, 62, 66), 2)] + CHORDS[4:]
LAMENT1_RF = LAMENT1[:5] + [(71, 1)] + LAMENT1[6:]

# フーガ主題の 2 倍拡大形(16 拍)— 地のバスと同じ長さ、各拍で協和するよう配置
SUBJECT_AUG = [(69, 2), (76, 2), (72, 1), (71, 1), (69, 1), (68, 1),
               (69, 2), (71, 2), (72, 1), (74, 1), (76, 2)]

# 「花」の主題(8 小節 = 32 拍)。頭の E–C–B はフーガ主題の頭 A–(E–C–B)
FLOWER = [(76, 2), (72, 1), (None, 1), (71, 3), (None, 1), (69, 1), (72, 1), (76, 2), (74, 2), (None, 2),
          (77, 2), (76, 1), (74, 1), (72, 3), (None, 1), (71, 1), (69, 1), (71, 2), (69, 4)]
# 花の和声(バス, コードトーン, 拍)
FLOWER_CHORDS = [
    (45, [57, 60, 64, 67, 71], 4),          # Am9
    (41, [57, 60, 64, 71], 4),              # Fmaj7#11
    (48, [55, 59, 64, 67], 4),              # Cmaj7
    (50, [53, 57, 60, 64], 4),              # Dm9
    (41, [57, 60, 64], 4),                  # Fmaj7
    (40, [55, 59, 62], 4),                  # Em7
    (40, [57, 59, 62], 2), (40, [56, 59, 62], 2),   # E7sus4 → E7
    (45, [57, 59, 60, 64], 4),              # Am(add9)
]
# 花の対旋律 = フーガ主題頭の拡大(全音符)
FLOWER_CM = [(64, 4), (64, 4), (67, 4), (65, 4), (69, 4), (67, 4), (62, 4), (60, 4)]

SYM = MODE == "symphony"
if not SYM:
    # 協奏曲版: 独奏ピアノを管弦楽に対して前へ出す(+3 dB)
    import synth as _synth
    _piano = _synth.INSTRUMENTS["piano"]
    _synth.INSTRUMENTS["piano"] = lambda f, hold, vel: _piano(f, hold, vel) * 1.41


# ================================================================ I. FLOWER PRELUDE
def flower_prelude(mx, start):
    s = Section(mx, start, 54)
    s.note("drone", 0, 33, 70, vel=0.7)
    for rep in range(2):
        b0 = rep * 32
        # 和声
        b = b0
        for bass, tones, d in FLOWER_CHORDS:
            if SYM:
                s.note("strings", b, bass, d, 0.3, -0.3, legato=1.02)
                s.note("strings", b, bass + 12, d, 0.22, -0.2, legato=1.02)
                s.chord("strings" if rep else "pad", b, tones, d, vel=0.22 if rep else 0.3, pan_spread=0.4, legato=1.02)
                # ハープの分散和音(2 回目)
                if rep:
                    seq = [(t, 1) for t in tones[:4]]
                    s.line("harp", b, seq, vel=0.3, pan=0.2, legato=2.0)
            else:
                s.note("piano", b, bass, d, 0.42, -0.3, legato=0.95)
                s.note("piano", b, bass + 7, d, 0.25, -0.25, legato=0.95)
                s.chord("piano", b + 0.02, tones[:3], d, vel=0.24, pan_spread=0.2, legato=0.95)
                if rep:
                    s.chord("pad", b, tones[-3:], d, vel=0.2, pan_spread=0.4)
            b += d
        # 旋律
        if SYM:
            s.line("flute" if rep else "strings", b0, FLOWER, vel=0.5, pan=0.25, legato=0.92, transpose=12 if rep else 0)
            if rep:
                s.line("strings", b0, FLOWER, vel=0.3, pan=0.1, legato=0.98)
        else:
            s.line("piano", b0, FLOWER, vel=0.66, pan=0.25, legato=0.9, humanize=0.05)
            if rep:
                s.line("piano", b0, FLOWER, vel=0.3, pan=0.35, legato=0.9, transpose=12)
                s.line("strings", b0, FLOWER, vel=0.25, pan=0.1, legato=0.98)
        # 対旋律(2 回目): フーガ主題頭の拡大
        if rep:
            s.line("horn" if SYM else "strings", b0, FLOWER_CM, vel=0.3, pan=-0.1, legato=0.98)
        s.note("bell", b0, 88, 3, 0.16, 0.3)
    s.note("bell", 64, 81, 4, 0.2, -0.2)
    return s.t(66)


# ================================================================ II. FUGUE (orchestrated)
def fugue(mx, start):
    s = Section(mx, start, 69)
    P, A, B = 0.35, 0.0, -0.35
    # 声部ごとの楽器
    if SYM:
        sop, alt, bas = "strings", "strings", "strings"
        v = 0.55
    else:
        sop = alt = bas = "piano"
        v = 0.62

    def voice(inst, beat, seq, vel, pan, transpose=0, double=None, dvel=0.35):
        s.line(inst, beat, seq, vel=vel, pan=pan, transpose=transpose, legato=0.95 if inst == "piano" else 0.98)
        if double:
            s.line(double, beat, seq, vel=dvel, pan=pan, transpose=transpose, legato=0.98)

    # 提示部
    voice(alt, 0, SUBJECT, v, A)
    voice(sop, 8, ANSWER, v + 0.05, P, double="flute" if SYM else None)
    voice(alt, 8, COUNTER, v - 0.1, A, transpose=-5)
    voice(bas, 16, SUBJECT, v + 0.05, B, transpose=-24, double="horn" if SYM else "strings", dvel=0.4)
    voice(sop, 16, COUNTER, v - 0.05, P, transpose=12, double="flute" if SYM else None)
    voice(alt, 16, [(64, 1), (59, 1), (64, 1), (60, .5), (59, .5), (64, 1.5), (65, .5), (67, .5), (69, .5), (71, 1)], v - 0.15, A)
    # 嬉遊部 1
    voice(sop, 24, [(69, .5), (76, .5), (72, .5), (71, .5), (67, .5), (74, .5), (71, .5), (69, .5),
                    (65, .5), (72, .5), (69, .5), (67, .5), (64, .5), (71, .5), (68, .5), (69, .5)], v, P)
    voice(alt, 24, [(60, 1), (64, 1), (59, 1), (62, 1), (57, 1), (60, 1), (56, 1), (59, 1)], v - 0.15, A)
    voice(bas, 24, [(45, 2), (43, 2), (41, 2), (40, 2)], v - 0.05, B, double="horn" if SYM else None)
    # 中間部 (C major)
    voice(sop, 32, SUBJECT_C, v + 0.05, P, double="flute" if SYM else "strings", dvel=0.3)
    voice(bas, 32, COUNTER_C, v - 0.05, B, transpose=-12)
    voice(alt, 32, [(67, 1), (62, 1), (67, .5), (67, .5), (64, .5), (67, .5),
                    (67, 1.5), (69, .5), (71, .5), (72, .5), (74, .5), (71, .5)], v - 0.15, A)
    # 嬉遊部 2
    voice(sop, 40, [(74, .5), (81, .5), (77, .5), (76, .5), (76, .5), (83, .5), (79, .5), (77, .5),
                    (77, .5), (84, .5), (81, .5), (79, .5), (76, .5), (83, .5), (80, .5), (81, .5)], v + 0.05, P)
    voice(alt, 40, [(65, 1), (69, 1), (67, 1), (71, 1), (69, 1), (72, 1), (71, 1), (74, 1)], v - 0.15, A)
    voice(bas, 40, [(50, 2), (52, 2), (53, 2), (52, 2)], v, B, double="horn" if SYM else None)
    # ストレッタ + 属音保続
    voice(bas, 48, SUBJECT, v + 0.1, B, transpose=-24, double="horn" if SYM else "strings", dvel=0.45)
    voice(sop, 50, SUBJECT, v + 0.1, P, double="flute" if SYM else "strings", dvel=0.4)
    s.line("strings", 50, SUBJECT, vel=0.35, pan=P, transpose=12, legato=0.9)
    voice(alt, 48, [(60, 1), (64, 1), (64, 1), (60, .5), (59, .5), (64, 2), (64, .5), (65, .5), (60, .5), (59, .5),
                    (69, .5), (71, .5), (68, 1), (71, .5), (69, .5), (68, .5), (59, .5)], v - 0.15, A)
    voice(bas, 56, [(40, 4)], v + 0.1, B)
    s.line("organ", 56, [(28, 4)], vel=0.5, pan=B)
    s.note("timpani", 56, 40, 4, 0.5, -0.2)
    voice(sop, 58, [(74, .5), (72, .5), (71, .5), (68, .5)], v, P)
    # 終結
    voice(sop, 60, SUBJECT, v + 0.12, P, double="flute" if SYM else "strings", dvel=0.45)
    s.line("strings", 60, SUBJECT, vel=0.4, pan=P, transpose=12, legato=0.9)
    voice(alt, 60, [(64, 1), (67, 1), (69, 1), (59, 1), (60, 1.5), (64, .5), (69, .5), (71, .5), (68, 1)], v - 0.15, A)
    voice(bas, 60, [(45, 1), (48, 1), (41, 1), (40, 1), (45, 2), (41, .5), (43, .5), (40, 1)], v, B, double="horn", dvel=0.45)
    s.line("organ", 60, [(33, 1), (36, 1), (29, 1), (28, 1), (33, 2), (29, .5), (31, .5), (28, 1)], vel=0.45, pan=B)
    s.note("timpani", 66, 45, 2, 0.45, -0.2)
    s.note("timpani", 68, 45, 4, 0.7, -0.2)
    if not SYM:
        s.chord("piano", 68, [45, 57, 61, 64, 69, 73], 5, vel=0.7)
    s.chord("strings", 68, [57, 61, 64, 69, 76], 6, vel=0.5)
    s.chord("horn", 68, [45, 52, 61], 6, vel=0.5)
    s.chord("organ", 68, [33, 45, 52, 61], 6, vel=0.5)
    s.note("bell", 68, 81, 4, vel=0.25)
    return s.t(74)


# ================================================================ II'. CADENZA (concerto only)
def cadenza(mx, start):
    s = Section(mx, start, 69)
    # ストレッタ(バス主題 → 2 拍遅れでソプラノ主題)
    s.line("piano", 0, SUBJECT, vel=0.6, pan=-0.2, transpose=-12, legato=0.9)
    s.line("piano", 2, SUBJECT, vel=0.68, pan=0.25, legato=0.9, humanize=0.05)
    s.line("piano", 8, [(52, 2)], vel=0.5, pan=-0.2)
    # 花の溜息 E–C–B をアルペジオで(徐々にゆっくり)
    b = 10
    for k, (m, d) in enumerate([(76, 1), (72, 1), (71, 2), (76, 1.5), (72, 1.5), (71, 3)]):
        s.note("piano", b, m, d, 0.55 - 0.05 * k, 0.2, legato=1.2)
        s.note("piano", b + 0.15, m - 12, d, 0.3, -0.1, legato=1.2)
        b += d
    s.chord("piano", 20, [40, 52, 56, 59, 62], 4, vel=0.5)           # E7
    s.line("piano", 22, [(64, .5), (65, .5), (68, .5), (71, .5), (72, .5), (74, .5), (76, .5), (80, .5)], vel=0.5, pan=0.3, legato=0.8)
    return s.t(26)


# ================================================================ III. FUGA SOPRA IL BASSO DI REQUIEM
def requiem_fugue(mx, start):
    s = Section(mx, start, 60)
    n_cycles = 5
    for c in range(n_cycles):
        b0 = c * 16
        last = c == n_cycles - 1
        g = GROUND if not last else GROUND[:7] + [(40, 1), (45, 4)]   # 最終周は A で着地
        # 地のバス
        s.line("strings", b0, g, vel=0.55, pan=-0.3, transpose=-12, legato=0.98)
        s.line("organ", b0, g, vel=0.3 + 0.05 * c, pan=-0.2, transpose=-12)
        if not SYM and c >= 1:
            s.line("piano", b0, g, vel=0.5, pan=-0.35, legato=0.9)
        if c >= 2:
            s.note("timpani", b0, 45, 2, 0.45 + 0.1 * (c - 2), -0.2)
            s.note("timpani", b0 + 14, 45, 2, 0.4, -0.2)
        # 拡大主題(c=1 弦アルト / c=2 フルート+弦 / c=3 全奏 / c=4 ホルン)
        if c == 1:
            s.line("strings", b0, SUBJECT_AUG, vel=0.5, pan=0.1, legato=0.98)
            if not SYM:
                s.line("piano", b0, SUBJECT_AUG, vel=0.6, pan=0.2, legato=0.95)
        if c == 2:
            s.line("flute" if SYM else "piano", b0, SUBJECT_AUG, vel=0.55, pan=0.25, legato=0.95, transpose=12)
            s.line("strings", b0, SUBJECT_AUG, vel=0.45, pan=0.1, legato=0.98)
        if c == 3:
            s.line("strings", b0, SUBJECT_AUG, vel=0.6, pan=0.15, legato=0.98, transpose=12)
            s.line("horn", b0, SUBJECT_AUG, vel=0.5, pan=-0.1, legato=0.98, transpose=-12)
            if not SYM:
                s.line("piano", b0, SUBJECT_AUG, vel=0.7, pan=0.2, legato=0.95)
                s.line("piano", b0, SUBJECT_AUG, vel=0.45, pan=0.3, legato=0.95, transpose=12)
        if c == 4:
            s.line("horn", b0, SUBJECT_AUG[:9] + [(71, 1), (73, 1), (76, 4)], vel=0.45, pan=-0.1, legato=0.98, transpose=-12)
            s.line("strings", b0, SUBJECT_AUG[:9] + [(71, 1), (73, 1), (76, 4)], vel=0.4, pan=0.1, legato=0.98)
        # 合唱の和声(c ≥ 2)
        if c >= 2:
            b = b0
            ch = CHORDS_RF if not last else CHORDS_RF[:7] + [((56, 59, 62), 1), ((57, 61, 64), 4)]
            for midis, d in ch:
                s.chord("choir", b, midis, d, vel=0.38 + 0.05 * (c - 2), pan_spread=0.5, legato=1.0, vowel="ah" if c < 4 else "oh")
                if c >= 3:
                    s.chord("strings", b, midis, d, vel=0.3, pan_spread=0.3)
                b += d
        # 弦の哀歌(c=3)/ 花の溜息(c=4)
        if c == 3:
            s.line("flute" if SYM else "strings", b0, LAMENT1_RF, vel=0.5, pan=0.35, legato=0.97, transpose=12 if SYM else 0)
        if c == 4:
            s.line("flute" if SYM else "piano", b0 + 8, [(76, 2), (72, 1), (71, 1), (None, 1), (76, 1), (72, .5), (71, .5), (69, 2)],
                   vel=0.5, pan=0.3, legato=0.95, transpose=12 if SYM else 0)
        # ピアノの分散和音(協奏曲 c=2,3)/ ハープ(交響曲 c=3)
        if c in (2, 3):
            b = b0
            for midis, d in CHORDS_RF:
                arp = [midis[0] + 12, midis[1] + 12, midis[2] + 12, midis[1] + 24] * 2
                seq = [(arp[i % len(arp)], .5) for i in range(int(d * 2))]
                if not SYM:
                    s.line("piano", b, seq, vel=0.3, pan=0.2, legato=1.0, humanize=0.04)
                elif c == 3:
                    s.line("harp", b, seq, vel=0.28, pan=0.2, legato=1.0)
                b += d
        s.note("bell", b0, 69 if c % 2 == 0 else 76, 3, vel=0.18, pan=rng.uniform(-0.4, 0.4))
    end = n_cycles * 16
    # 着地: A major(ピカルディ)
    s.chord("strings", end - 2, [45, 57, 61, 64, 69], 8, vel=0.45)
    s.chord("horn", end - 2, [45, 52, 61], 8, vel=0.4)
    if not SYM:
        s.chord("piano", end - 2, [33, 45, 57, 61, 64, 69], 6, vel=0.6)
    s.note("timpani", end - 2, 45, 4, 0.7, -0.2)
    s.note("bell", end - 2, 81, 5, 0.25, 0.2)
    return s.t(end + 3)


# ================================================================ IV. FLOWER EPILOGUE
def flower_epilogue(mx, start):
    s = Section(mx, start, 54)
    s.note("drone", 0, 33, 50, vel=0.6)
    b = 0
    for bass, tones, d in FLOWER_CHORDS:
        if SYM:
            s.note("strings", b, bass, d, 0.28, -0.3, legato=1.02)
            s.chord("pad", b, tones, d, vel=0.28, pan_spread=0.4)
            s.line("harp", b, [(t, 1) for t in tones[:4]], vel=0.22, pan=0.2, legato=2.0)
        else:
            s.note("piano", b, bass, d, 0.4, -0.3, legato=0.95)
            s.note("piano", b, bass + 7, d, 0.22, -0.25, legato=0.95)
            s.chord("piano", b + 0.02, tones[:3], d, vel=0.2, pan_spread=0.2, legato=0.95)
            s.chord("pad", b, tones[-3:], d, vel=0.18, pan_spread=0.4)
        b += d
    if SYM:
        s.line("flute", 0, FLOWER, vel=0.45, pan=0.25, legato=0.92, transpose=12)
        s.line("strings", 0, FLOWER, vel=0.28, pan=0.1, legato=0.98)
    else:
        s.line("piano", 0, FLOWER, vel=0.6, pan=0.25, legato=0.9, humanize=0.05)
    # バスにフーガ主題頭の拡大(統合の署名)
    s.line("horn" if SYM else "strings", 0, [(45, 4), (52, 4), (48, 4), (47, 4)], vel=0.28, pan=-0.2, legato=1.0)
    # 終止: A major の鐘と長い残響
    s.chord("pad", 32, [45, 57, 61, 64, 69], 14, vel=0.32)
    if not SYM:
        s.chord("piano", 32, [33, 45, 61, 64, 69, 76], 8, vel=0.45)
    s.note("bell", 32, 81, 6, 0.24, 0.2)
    s.note("bell", 36, 88, 6, 0.16, -0.3)
    s.note("bell", 40, 85, 8, 0.12, 0.1)
    return s.t(48)


# ================================================================ assemble
def main():
    total = 400.0
    mx = Mixer(total)
    print(f"composing ({MODE})...")
    marks = {}
    t = 0.0
    marks["prelude"] = t
    t = flower_prelude(mx, t)
    marks["fugue"] = t - 1.0
    t = fugue(mx, t - 1.0)
    if not SYM:
        marks["cadenza"] = t - 0.5
        t = cadenza(mx, t - 0.5)
    marks["requiem"] = t - 0.5
    t = requiem_fugue(mx, t - 0.5)
    marks["epilogue"] = t - 1.0
    t = flower_epilogue(mx, t - 1.0)
    marks["end"] = t
    print(json.dumps(marks, indent=1))

    # ---- アップロード録音(A minor 系を中心に、前作より控えめに)
    print("layering uploaded recordings...")
    pre, fug, req, epi = marks["prelude"], marks["fugue"], marks["requiem"], marks["epilogue"]
    C.layer(mx, "ee64108e", 0, 10, pre + 0.3, -20, lowpass=6000, highpass=100, fade=2)
    C.layer(mx, "756b07ab", 20, 30, pre + 6, -24, lowpass=1200, pitch=-12, tempo=0.5, fade=8, pan=-0.2)
    C.layer(mx, "b6834dcd", 100, 30, pre + 36, -30, lowpass=1000, fade=8, pan=0.3)
    C.layer(mx, "768f36de", 5, 60, fug + 4, -26, lowpass=2500, highpass=200, fade=6, pan=0.3)
    C.layer(mx, "14ae512f", 20, min(78, epi - req - 4), req + 2, -23, lowpass=2500, highpass=150, fade=8, pan=-0.35)
    C.layer(mx, "d954e87d", 60, min(70, epi - req - 8), req + 6, -26, lowpass=2000, highpass=300, fade=8, pan=0.35)
    C.layer(mx, "6cbfd212", 30, 30, req + 32, -24, lowpass=2200, highpass=200, fade=6, pan=0.1)
    C.layer(mx, "e8c8a393", 300, 20, epi + 2, -27, lowpass=1500, highpass=120, tempo=0.5, fade=10)
    C.layer(mx, "f416529b", 20, 40, epi + 4, -29, lowpass=1200, highpass=150, fade=10, pan=0.3)

    print("reverb + master...")
    ir = make_ir(3.6, 1.35)
    mix = mx.render(ir, wet=0.95)[: int(t * SR)]
    nf = int(8 * SR)
    mix[-nf:] *= np.linspace(1, 0, nf)[:, None]
    if not SYM:
        mix = compress(mix, threshold_db=-20.0, ratio=2.5)   # 独奏の静かな楽句を管弦楽に対して持ち上げる
        mix *= 0.9 / (np.abs(mix).max() + 1e-6)
    mix = soft_limit(mix, 0.93)
    name = f"bada_flower_{MODE}"
    write_wav(os.path.join(OUT, name + ".wav"), mix)
    if SYM:
        marks.update({
            "title": "Bada Flower Symphony",
            "subtitle": "Fuga · Requiem · A Flower Is Not a Flower(様式)",
            "note": "交響曲版 — 弦・フルート・ホルン・オルガン・合唱・ティンパニ・ハープ",
            "movements": [
                ["prelude", "I. 花の前奏", "Prelude · A Flower Is Not a Flower 様式 · A minor", "疎らな旋律と長い休符。頭の E–C–B はフーガ主題の動機。", [120, 130, 220]],
                ["fugue", "II. フーガ(管弦楽)", "Fuga a 3 voci · 弦 / フルート / ホルン", "主題 → 応答 → 対主題 → 嬉遊部 → 中間部 → ストレッタ → ピカルディ終止", [140, 120, 230]],
                ["requiem", "III. レクイエムのバスによるフーガ", "Fuga sopra il basso di Requiem", "2 倍に拡大した主題が、半音階で下る嘆きのバスの上に重なる", [110, 90, 200]],
                ["epilogue", "IV. 花の後奏", "Epilogue · A major の鐘で閉じる", "バスにフーガ主題の頭。花は花ではない。", [210, 180, 140]],
            ],
        })
    else:
        marks.update({
            "title": "Bada Flower Concerto",
            "subtitle": "Fuga · Requiem · A Flower Is Not a Flower(様式)",
            "note": "ピアノ協奏曲版 — ピアノ独奏 + 弦・フルート・ホルン・オルガン・合唱・ティンパニ",
            "movements": [
                ["prelude", "I. 花の前奏(ピアノ独奏 → 管弦楽)", "Prelude · A Flower Is Not a Flower 様式 · A minor", "疎らな旋律と長い休符。頭の E–C–B はフーガ主題の動機。", [120, 130, 220]],
                ["fugue", "II. フーガ(ピアノ + 管弦楽)", "Fuga a 3 voci · ピアノが 3 声を担い、弦とホルンが入りを重ねる", "主題 → 応答 → 対主題 → 嬉遊部 → 中間部 → ストレッタ → ピカルディ終止", [140, 120, 230]],
                ["cadenza", "II'. カデンツァ(ピアノ独奏)", "Cadenza · ストレッタと花の溜息", "主題を 2 拍遅れで追いかけ、E–C–B の溜息へ", [170, 140, 230]],
                ["requiem", "III. レクイエムのバスによるフーガ", "Fuga sopra il basso di Requiem", "2 倍に拡大した主題が、半音階で下る嘆きのバスの上に重なる", [110, 90, 200]],
                ["epilogue", "IV. 花の後奏(ピアノ)", "Epilogue · A major の鐘で閉じる", "バスにフーガ主題の頭。花は花ではない。", [210, 180, 140]],
            ],
        })
    with open(os.path.join(OUT, "marks.json"), "w") as f:
        json.dump(marks, f, indent=1, ensure_ascii=False)
    print("wrote", name, f"{len(mix) / SR:.1f}s peak={np.abs(mix).max():.2f}")


if __name__ == "__main__":
    main()
