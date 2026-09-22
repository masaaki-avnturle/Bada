"""
compose_flower_real.py — 「Bada Flower Symphony / Concerto」 本物の楽器版(静かで悲しい版)

compose_flower.py の素材(花の主題・フーガ・レクイエムのバス・拡大主題)を、
サウンドフォントの録音楽器(グランドピアノ / ヴァイオリン・ヴィオラ・チェロ・コントラバス /
フルート・オーボエ・クラリネット・ファゴット・ホルン / ハープ / 合唱 / ティンパニ / グロッケン)で演奏し、
坂本龍一《A Flower Is Not a Flower》と《Little Buddha》(Acceptance)の
「静かで悲しい」様式に作り換える。旋律・和声はオリジナル(原曲は引用しない)。

  静かで悲しい版への変更
  ・テンポを落とす(前奏 ♩=48 / フーガ ♩=58 / レクイエム ♩=54 / 後奏 ♩=46)
  ・ピカルディ(長調)終止をやめ、A minor(add9)のまま消える
  ・全奏・ティンパニの打撃を減らし、弦は Slow Strings、旋律はオーボエ / フルート / チェロ
  ・強弱は pp〜mp(velocity 0.25〜0.55)

  MODE=symphony  管弦楽のみ(ピアノなし)
  MODE=concerto  グランドピアノ独奏 + 管弦楽(カデンツァ付き)
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from synth import make_ir, soft_limit, compress, write_wav, SR  # noqa: E402
from sampler import SFMixer  # noqa: E402
import compose as C  # noqa: E402
import compose_flower as F  # noqa: E402

OUT = C.OUT
MODE = os.environ.get("MODE", "symphony")
SYM = MODE == "symphony"
rng = np.random.default_rng(1108)
Section = C.Section

SUBJECT, ANSWER, COUNTER = C.SUBJECT, C.ANSWER, C.COUNTER
SUBJECT_C, COUNTER_C = C.SUBJECT_C, C.COUNTER_C
GROUND = C.GROUND
CHORDS_RF, LAMENT1_RF = F.CHORDS_RF, F.LAMENT1_RF
SUBJECT_AUG, FLOWER, FLOWER_CHORDS, FLOWER_CM = F.SUBJECT_AUG, F.FLOWER, F.FLOWER_CHORDS, F.FLOWER_CM

# 最終周: E7 の後、A minor(add9)へ(ピカルディはしない)
CHORDS_LAST = CHORDS_RF[:7] + [((56, 59, 62), 1), ((57, 60, 64), 4)]
AM_ADD9 = [45, 57, 60, 64, 71]


# ================================================================ I. FLOWER PRELUDE  ♩=48
def flower_prelude(mx, start):
    s = Section(mx, start, 48)
    s.note("contrabass", 0, 33, 64, 0.3, -0.2)
    for rep in range(2):
        b0 = rep * 32
        b = b0
        for bass, tones, d in FLOWER_CHORDS:
            if SYM:
                s.note("cello", b, bass + 12, d, 0.32, -0.3, legato=1.02)
                s.chord("strings_slow", b, tones, d, vel=0.28 if rep else 0.22, pan_spread=0.4, legato=1.03)
                if rep:
                    s.line("harp", b, [(t, 1) for t in tones[:4]], vel=0.35, pan=0.25, legato=2.0)
            else:
                s.note("piano", b, bass, d, 0.42, -0.3, legato=0.98)
                s.note("piano", b, bass + 7, d, 0.28, -0.25, legato=0.98)
                s.chord("piano", b + 0.03, tones[:3], d, vel=0.26, pan_spread=0.2, legato=0.98)
                if rep:
                    s.chord("strings_slow", b, tones[-3:], d, vel=0.22, pan_spread=0.4, legato=1.03)
                    s.note("cello", b, bass + 12, d, 0.22, -0.3, legato=1.02)
            b += d
        if SYM:
            s.line("oboe" if rep == 0 else "flute", b0, FLOWER, vel=0.42, pan=0.2, legato=0.95, transpose=12 if rep else 0)
            if rep:
                s.line("violin", b0, FLOWER, vel=0.3, pan=0.3, legato=0.98)
        else:
            s.line("piano", b0, FLOWER, vel=0.62, pan=0.2, legato=0.95, humanize=0.05)
            if rep:
                s.line("flute", b0, FLOWER, vel=0.28, pan=0.3, legato=0.98, transpose=12)
        if rep:
            s.line("viola" if SYM else "cello", b0, FLOWER_CM, vel=0.28, pan=-0.1, legato=1.0, transpose=0 if SYM else -12)
        s.note("glock", b0, 88, 2, 0.22, 0.3)
    s.note("glock", 64, 81, 2, 0.24, -0.2)
    return s.t(66)


# ================================================================ II. FUGUE  ♩=58(静かなフーガ)
def fugue(mx, start):
    s = Section(mx, start, 58)
    P, A, B = 0.35, 0.0, -0.35
    if SYM:
        sop, alt, bas, v = "violin", "viola", "cello", 0.45
    else:
        sop = alt = bas = "piano"
        v = 0.55

    def voice(inst, beat, seq, vel, pan, transpose=0, double=None, dvel=0.3):
        s.line(inst, beat, seq, vel=vel, pan=pan, transpose=transpose, legato=0.95 if inst == "piano" else 0.98)
        if double:
            s.line(double, beat, seq, vel=dvel, pan=pan, transpose=transpose, legato=0.98)

    # 静かな弦のパッド(和声の枠)
    for b, midis, d in [(0, [45, 57, 64], 8), (8, [40, 52, 59], 8), (16, [45, 57, 64], 8), (24, [45, 55, 60], 8),
                        (32, [48, 55, 64], 8), (40, [50, 57, 65], 8), (48, [45, 57, 64], 8), (56, [40, 52, 59], 4),
                        (60, [45, 57, 64], 8)]:
        s.chord("strings_slow", b, midis, d, vel=0.18, pan_spread=0.3, legato=1.02)
    voice(alt, 0, SUBJECT, v, A)
    voice(sop, 8, ANSWER, v + 0.05, P, double="flute" if SYM else None, dvel=0.28)
    voice(alt, 8, COUNTER, v - 0.1, A, transpose=-5)
    voice(bas, 16, SUBJECT, v + 0.05, B, transpose=-24 if not SYM else -12, double=None if SYM else "cello", dvel=0.35)
    voice(sop, 16, COUNTER, v - 0.05, P, transpose=12)
    voice(alt, 16, [(64, 1), (59, 1), (64, 1), (60, .5), (59, .5), (64, 1.5), (65, .5), (67, .5), (69, .5), (71, 1)], v - 0.15, A)
    voice(sop, 24, [(69, .5), (76, .5), (72, .5), (71, .5), (67, .5), (74, .5), (71, .5), (69, .5),
                    (65, .5), (72, .5), (69, .5), (67, .5), (64, .5), (71, .5), (68, .5), (69, .5)], v, P)
    voice(alt, 24, [(60, 1), (64, 1), (59, 1), (62, 1), (57, 1), (60, 1), (56, 1), (59, 1)], v - 0.15, A)
    voice(bas, 24, [(45, 2), (43, 2), (41, 2), (40, 2)], v - 0.05, B, double="bassoon" if SYM else None, dvel=0.3)
    voice(sop, 32, SUBJECT_C, v + 0.05, P, double="oboe" if SYM else "violin", dvel=0.3)
    voice(bas, 32, COUNTER_C, v - 0.05, B, transpose=-12)
    voice(alt, 32, [(67, 1), (62, 1), (67, .5), (67, .5), (64, .5), (67, .5),
                    (67, 1.5), (69, .5), (71, .5), (72, .5), (74, .5), (71, .5)], v - 0.15, A)
    voice(sop, 40, [(74, .5), (81, .5), (77, .5), (76, .5), (76, .5), (83, .5), (79, .5), (77, .5),
                    (77, .5), (84, .5), (81, .5), (79, .5), (76, .5), (83, .5), (80, .5), (81, .5)], v, P)
    voice(alt, 40, [(65, 1), (69, 1), (67, 1), (71, 1), (69, 1), (72, 1), (71, 1), (74, 1)], v - 0.15, A)
    voice(bas, 40, [(50, 2), (52, 2), (53, 2), (52, 2)], v - 0.05, B, double="contrabass" if SYM else None, dvel=0.3)
    voice(bas, 48, SUBJECT, v + 0.05, B, transpose=-24 if not SYM else -12, double="contrabass" if SYM else "cello", dvel=0.35)
    voice(sop, 50, SUBJECT, v + 0.05, P, double="flute" if SYM else "violin", dvel=0.3)
    voice(alt, 48, [(60, 1), (64, 1), (64, 1), (60, .5), (59, .5), (64, 2), (64, .5), (65, .5), (60, .5), (59, .5),
                    (69, .5), (71, .5), (68, 1), (71, .5), (69, .5), (68, .5), (59, .5)], v - 0.15, A)
    voice(bas, 56, [(40, 4)], v, B, double="contrabass", dvel=0.3)
    s.note("timpani", 56, 40, 4, 0.22, -0.2)
    voice(sop, 58, [(74, .5), (72, .5), (71, .5), (68, .5)], v, P)
    voice(sop, 60, SUBJECT, v + 0.08, P, double="flute" if SYM else "violin", dvel=0.32)
    voice(alt, 60, [(64, 1), (67, 1), (69, 1), (59, 1), (60, 1.5), (64, .5), (69, .5), (71, .5), (68, 1)], v - 0.15, A)
    voice(bas, 60, [(45, 1), (48, 1), (41, 1), (40, 1), (45, 2), (41, .5), (43, .5), (40, 1)], v, B, double="contrabass", dvel=0.3)
    # 終止: A minor add9 のまま(ピカルディはしない)
    if not SYM:
        s.chord("piano", 68, [33, 45, 57, 60, 64, 71], 6, vel=0.5)
    s.chord("strings_slow", 68, [45, 57, 60, 64, 71], 8, vel=0.3)
    s.chord("horn", 68, [45, 52, 60], 6, vel=0.22)
    s.note("glock", 68, 83, 3, 0.2, 0.2)
    return s.t(76)


# ================================================================ II'. CADENZA  ♩=58(協奏曲のみ)
def cadenza(mx, start):
    s = Section(mx, start, 58)
    s.line("piano", 0, SUBJECT, vel=0.5, pan=-0.2, transpose=-12, legato=0.95)
    s.line("piano", 2, SUBJECT, vel=0.58, pan=0.25, legato=0.95, humanize=0.05)
    s.line("piano", 8, [(52, 2)], vel=0.45, pan=-0.2)
    b = 10
    for k, (m, d) in enumerate([(76, 1), (72, 1), (71, 2), (76, 1.5), (72, 1.5), (71, 3)]):
        s.note("piano", b, m, d, 0.5 - 0.05 * k, 0.2, legato=1.2)
        s.note("piano", b + 0.15, m - 12, d, 0.28, -0.1, legato=1.2)
        b += d
    s.chord("piano", 20, [40, 52, 56, 59, 62], 4, vel=0.42)
    s.line("piano", 22, [(64, .5), (65, .5), (68, .5), (71, .5), (72, .5), (74, .5), (76, .5), (80, .5)], vel=0.42, pan=0.3, legato=0.8)
    s.chord("strings_slow", 20, [40, 52, 56, 59], 6, vel=0.16, pan_spread=0.3)
    return s.t(26)


# ================================================================ III. FUGA SOPRA IL BASSO DI REQUIEM  ♩=54
def requiem_fugue(mx, start):
    s = Section(mx, start, 54)
    n_cycles = 5
    for c in range(n_cycles):
        b0 = c * 16
        last = c == n_cycles - 1
        g = GROUND if not last else GROUND[:7] + [(40, 1), (45, 4)]
        s.line("cello", b0, g, vel=0.4, pan=-0.3, legato=0.99)
        s.line("contrabass", b0, g, vel=0.3 + 0.03 * c, pan=-0.2, transpose=-12, legato=0.99)
        if not SYM and c >= 1:
            s.line("piano", b0, g, vel=0.4, pan=-0.35, legato=0.9)
        if c == 3:
            s.note("timpani", b0, 45, 2, 0.28, -0.2)
        if c == 1:
            s.line("viola" if SYM else "piano", b0, SUBJECT_AUG, vel=0.45 if SYM else 0.55, pan=0.1, legato=0.98)
            if SYM:
                s.line("clarinet", b0, SUBJECT_AUG, vel=0.3, pan=-0.1, legato=0.98, transpose=-12)
        if c == 2:
            s.line("oboe" if SYM else "piano", b0, SUBJECT_AUG, vel=0.42 if SYM else 0.55, pan=0.25, legato=0.97, transpose=0 if SYM else 12)
            s.line("violin", b0, SUBJECT_AUG, vel=0.32, pan=0.2, legato=0.98)
        if c == 3:
            s.line("violin", b0, SUBJECT_AUG, vel=0.45, pan=0.2, legato=0.98, transpose=12)
            s.line("horn", b0, SUBJECT_AUG, vel=0.3, pan=-0.1, legato=0.98, transpose=-12)
            s.line("bassoon", b0, SUBJECT_AUG, vel=0.3, pan=-0.2, legato=0.98, transpose=-24)
            if not SYM:
                s.line("piano", b0, SUBJECT_AUG, vel=0.6, pan=0.2, legato=0.95)
                s.line("piano", b0, SUBJECT_AUG, vel=0.4, pan=0.3, legato=0.95, transpose=12)
        if c == 4:
            tail = SUBJECT_AUG[:9] + [(71, 1), (72, 1), (76, 4)]
            s.line("cello", b0, tail, vel=0.36, pan=-0.1, legato=0.98, transpose=-12)
            s.line("flute" if SYM else "piano", b0, tail, vel=0.32 if SYM else 0.5, pan=0.2, legato=0.98)
        if c >= 2:
            b = b0
            for midis, d in (CHORDS_RF if not last else CHORDS_LAST):
                s.chord("choir", b, midis, d, vel=0.26 + 0.04 * (c - 2), pan_spread=0.5, legato=1.0)
                s.chord("strings_slow", b, midis, d, vel=0.2, pan_spread=0.3, legato=1.02)
                b += d
        if c == 3:
            s.line("oboe" if SYM else "violin", b0, LAMENT1_RF, vel=0.4, pan=0.35, legato=0.97)
        if c == 4:
            s.line("flute" if SYM else "piano", b0 + 8, [(76, 2), (72, 1), (71, 1), (None, 1), (76, 1), (72, .5), (71, .5), (69, 2)],
                   vel=0.4, pan=0.3, legato=0.95, transpose=12 if SYM else 0)
        if c in (2, 3):
            b = b0
            for midis, d in CHORDS_RF:
                arp = [midis[0] + 12, midis[1] + 12, midis[2] + 12, midis[1] + 24] * 2
                seq = [(arp[i % len(arp)], .5) for i in range(int(d * 2))]
                if not SYM:
                    s.line("piano", b, seq, vel=0.26, pan=0.2, legato=1.0, humanize=0.04)
                elif c == 3:
                    s.line("harp", b, seq, vel=0.3, pan=0.25, legato=1.0)
                b += d
        s.note("glock", b0, 81 if c % 2 == 0 else 88, 2, 0.16, rng.uniform(-0.4, 0.4))
    end = n_cycles * 16
    # 着地: A minor(add9)— 悲しみのまま静かに
    s.chord("strings_slow", end - 2, AM_ADD9, 10, vel=0.3, pan_spread=0.4, legato=1.02)
    s.chord("horn", end - 2, [45, 52, 60], 8, vel=0.2)
    if not SYM:
        s.chord("piano", end - 2, [33, 45, 57, 60, 64, 71], 6, vel=0.5)
    s.note("timpani", end - 2, 45, 4, 0.3, -0.2)
    s.note("bell", end - 2, 69, 6, 0.22, 0.2)
    return s.t(end + 4)


# ================================================================ IV. FLOWER EPILOGUE  ♩=46
def flower_epilogue(mx, start):
    s = Section(mx, start, 46)
    s.note("contrabass", 0, 33, 46, 0.26, -0.2)
    b = 0
    for bass, tones, d in FLOWER_CHORDS:
        if SYM:
            s.note("cello", b, bass + 12, d, 0.26, -0.3, legato=1.02)
            s.chord("strings_slow", b, tones, d, vel=0.24, pan_spread=0.4, legato=1.03)
            s.line("harp", b, [(t, 1) for t in tones[:4]], vel=0.26, pan=0.25, legato=2.0)
        else:
            s.note("piano", b, bass, d, 0.4, -0.3, legato=0.98)
            s.note("piano", b, bass + 7, d, 0.24, -0.25, legato=0.98)
            s.chord("piano", b + 0.03, tones[:3], d, vel=0.22, pan_spread=0.2, legato=0.98)
            s.chord("strings_slow", b, tones[-3:], d, vel=0.18, pan_spread=0.4, legato=1.03)
        b += d
    if SYM:
        s.line("flute", 0, FLOWER, vel=0.38, pan=0.25, legato=0.95, transpose=12)
        s.line("violin", 0, FLOWER, vel=0.26, pan=0.15, legato=0.98)
    else:
        s.line("piano", 0, FLOWER, vel=0.58, pan=0.2, legato=0.95, humanize=0.05)
    s.line("cello", 0, [(45, 4), (52, 4), (48, 4), (47, 4)], vel=0.28, pan=-0.2, legato=1.0)   # 主題頭 A–E–C–B
    # 終止: A minor(add9)が消えていく
    s.chord("strings_slow", 32, AM_ADD9, 16, vel=0.26, pan_spread=0.4, legato=1.02)
    if not SYM:
        s.chord("piano", 32, [33, 45, 57, 60, 64, 71], 10, vel=0.4)
    s.note("glock", 32, 81, 3, 0.2, 0.2)
    s.note("glock", 36, 88, 3, 0.14, -0.3)
    s.note("glock", 41, 83, 4, 0.1, 0.1)
    return s.t(50)


# ================================================================ assemble
def main():
    mx = SFMixer(440.0)
    print(f"composing ({MODE}, real instruments)...")
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

    # アップロード録音は遠い霧としてごく薄く
    pre, req, epi = marks["prelude"], marks["requiem"], marks["epilogue"]
    C.layer(mx, "ee64108e", 0, 10, pre + 0.3, -24, lowpass=5000, highpass=100, fade=2)
    C.layer(mx, "756b07ab", 20, 30, pre + 8, -30, lowpass=1000, pitch=-12, tempo=0.5, fade=10, pan=-0.2)
    C.layer(mx, "14ae512f", 20, min(70, epi - req - 6), req + 4, -30, lowpass=1800, highpass=200, fade=10, pan=-0.3)
    C.layer(mx, "e8c8a393", 300, 20, epi + 4, -32, lowpass=1200, highpass=150, tempo=0.5, fade=12)

    print("rendering instruments...")
    ir = make_ir(3.8, 1.5)
    mix = mx.render(ir, wet=0.9)[: int(t * SR)]
    mix = compress(mix, threshold_db=-24.0, ratio=1.6)   # 弱く。pp〜mp の呼吸を残す
    mix *= 0.85 / (np.abs(mix).max() + 1e-6)
    nf = int(8 * SR)
    mix[-nf:] *= np.linspace(1, 0, nf)[:, None]
    mix = soft_limit(mix, 0.93)
    name = f"bada_flower_{MODE}_real"
    write_wav(os.path.join(OUT, name + ".wav"), mix)
    common = "Fuga · Requiem · A Flower Is Not a Flower / Little Buddha(様式)"
    if SYM:
        marks.update({
            "title": "Bada Flower Symphony", "subtitle": common,
            "note": "交響曲版 — 本物の楽器(サンプル音源): 弦・木管・ホルン・ハープ・合唱",
            "movements": [
                ["prelude", "I. 花の前奏", "オーボエとフルート、Slow Strings、ハープ · ♩=48", "疎らな旋律と長い休符。頭の E–C–B はフーガ主題の動機。", [120, 130, 220]],
                ["fugue", "II. 静かなフーガ", "ヴァイオリン / ヴィオラ / チェロ · ♩=58", "主題 → 応答 → 対主題 → 嬉遊部 → 中間部 → ストレッタ → A minor add9", [140, 120, 230]],
                ["requiem", "III. レクイエムのバスによるフーガ", "Fuga sopra il basso di Requiem · ♩=54", "2 倍に拡大した主題が、嘆きのバスの上に重なる。合唱は遠く。", [110, 90, 200]],
                ["epilogue", "IV. 花の後奏 — Acceptance", "Slow Strings とフルート · ♩=46", "A minor(add9)のまま、静かに消える。", [150, 140, 200]],
            ],
        })
    else:
        marks.update({
            "title": "Bada Flower Concerto", "subtitle": common,
            "note": "ピアノ協奏曲版 — 本物の楽器(サンプル音源): グランドピアノ + 弦・木管・ホルン・合唱",
            "movements": [
                ["prelude", "I. 花の前奏(グランドピアノ独奏 → 弦)", "Yamaha Grand Piano · ♩=48", "疎らな旋律と長い休符。頭の E–C–B はフーガ主題の動機。", [120, 130, 220]],
                ["fugue", "II. 静かなフーガ(ピアノ + 弦)", "ピアノが 3 声、チェロとヴァイオリンが入りを重ねる · ♩=58", "主題 → 応答 → 対主題 → 嬉遊部 → 中間部 → ストレッタ → A minor add9", [140, 120, 230]],
                ["cadenza", "II'. カデンツァ(ピアノ独奏)", "Cadenza · ストレッタと花の溜息", "主題を 2 拍遅れで追いかけ、E–C–B の溜息へ", [170, 140, 230]],
                ["requiem", "III. レクイエムのバスによるフーガ", "Fuga sopra il basso di Requiem · ♩=54", "2 倍に拡大した主題が、嘆きのバスの上に重なる。合唱は遠く。", [110, 90, 200]],
                ["epilogue", "IV. 花の後奏 — Acceptance(ピアノ)", "Yamaha Grand Piano と Slow Strings · ♩=46", "A minor(add9)のまま、静かに消える。", [150, 140, 200]],
            ],
        })
    with open(os.path.join(OUT, "marks.json"), "w") as f:
        json.dump(marks, f, indent=1, ensure_ascii=False)
    print("wrote", name, f"{len(mix) / SR:.1f}s peak={np.abs(mix).max():.2f}")


if __name__ == "__main__":
    main()
