#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLII · Ray (LUNA SEA の Ray を参考にした、疾走する 90 年代のロック)
  録音 4 本 (9/25): 12:46 (ヘ短調)、12:50:36 (ロ短調)、12:50:53 (ロ短調)、13:04 (変ホ短調)。
  LUNA SEA の曲は旋律を引用せず、音色と編曲だけを参照する: ♩=148 で駆ける 8 ビート、8 分で走り続けるベース、
  コーラスのかかったクリーン・ギターの分散和音と、歪んだギターのパワーコード (ブリッジ・ミュートの刻み → サビで開く) の 2 本、
  リードギター、バイオリンのソロ。旋律は 4 本の録音の主題 (ピアノの実音) を 2 倍の長さで — 速いバンドの上で歌が大きく流れる。
  形式:
    Intro    — 12:50:53 の実音 (ロ短調) にクリーン・ギターが入る → バンドのイントロ (歪んだギターが開く)
    Verse 1  — 12:50:36 の主題 (2 倍)、ミュートの刻みと 8 分のベース
    Pre      — 登っていく和音 (G△7 - A - Bm - F#7) 、スネアの 8 分で盛り上げる
    Chorus 1 — 12:46 の主題 (2 倍)、パワーコードが開き、リードギターが重なる、弦
    Interlude— 12:46 の実音 (ヘ短調)
    Verse 2 / Pre / Chorus 2
    Solo     — 変ホ短調へ: バイオリンが 13:04 と 12:46 の主題を元の速さで弾く
    Break    — 13:04 の実音 (変ホ短調)、クリーン・ギターだけ
    Last chorus — 半音上のハ短調で 2 回、2 回目はバイオリンが 1 オクターヴ上で重なる → 全員の最後の一撃
    Outro    — 13:04 の本当の終わり (実音) にギターの分散和音が寄り添って消える
  使い方: python compose_tablet42.py <bank37.json> [score_tablet42.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC = CT.add, CT.REC
def hm(r): return T3.hm(r) + (':' + r[13:15] if r[9:13] == '1250' else '')     # 12:50:36 と 12:50:53 を区別する
BPM = 148; BAR_S = 240.0 / BPM
R1, R2, R3, R4 = '20260925_124643', '20260925_125053', '20260925_125036', '20260925_130431'
KEYS = {R1: 3, R2: -3, R3: -3, R4: 1}
T7.KEYS.update(KEYS)
ORDER = [R3, R2, R1, R4]
DYNK = 1.6                                             # 旋律 (ピアノの実音) の倍率 (音量は dyn の 2 乗) — 伴奏は割り戻す
GTR, DGT, BASS, DRUM, STRG, LEAD, VLN, CRASH, FILL = [], [], [], [], [], [], [], [], []
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK

def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
def low_root(c, lo=40): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
    for b0, b1, gain, pan in GTR:                  # クリーン・ギター: 8 分の分散和音 + 付点 8 分のディレイ
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c, 45); th = (c['third'] - c['root']) % 12
                nine = r + 12 if c['major3'] else r + 14
                pat = [r, r + 7, nine, r + 12 + th] if half == 0 else [r + 19, r + 12 + th, nine, r + 7]
                for i_, m in enumerate(pat):
                    t = bar * BPB + half + 0.5 * i_; g = gain * dk(P, bar) * (1.0 if i_ == 0 else 0.8)
                    add('CG', t, 0.8, m, g, None, pan=pan); add('CG', t + 0.75, 0.6, m, g * 0.28, None, pan=-pan)
    for b0, b1, gain, mode in DGT:                 # 歪んだギター: 'mute' = 8 分のブリッジ・ミュート / 'open' = 開いたパワーコードの押し
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c, 40)
                if mode == 'mute':
                    for k in range(4): add('DG', bar * BPB + half + 0.5 * k, 0.4, r, gain * dk(P, bar) * (1.0 if k == 0 else 0.8), None, mute=True)
                else:
                    add('DG', bar * BPB + half, 1.45, r, gain * dk(P, bar), None)
                    add('DG', bar * BPB + half + 1.5, 0.45, r, gain * dk(P, bar) * 0.85, None)
    for b0, b1, gain in BASS:                      # 走るベース: 8 分の根音、4 拍目の裏で次の和音へ半音 / 5 度で寄る
        for bar in range(b0, b1):
            c0, c1 = chord(P.harm[bar * BPB]), chord(P.harm[bar * BPB + 2]); nxt = chord(P.harm[min(P.N - 1, (bar + 1) * BPB)])
            r0, r1, rn = low_root(c0, 28), low_root(c1, 28), low_root(nxt, 28)
            seq = [(0, r0), (0.5, r0), (1.0, r0 + 12), (1.5, r0), (2, r1), (2.5, r1), (3.0, r1 + 7 if r1 + 7 <= 47 else r1 - 5), (3.5, rn - 1 if rn != r1 else r1 + 12)]
            for t, m in seq: add('EB', bar * BPB + t, 0.4, m, gain * dk(P, bar) * (1.0 if t in (0, 2) else 0.78), None)
    for b0, b1, lvl, mode in DRUM:                 # ドラム: 'drive' = 駆ける 8 ビート / 'half' = ハーフタイム / 'build' = 4 分のスネアで盛り上げる
        for bar in range(b0, b1):
            if mode == 'half':
                for t in (0, 2.5): add('DR', bar * BPB + t, 0.3, 36, lvl * 0.9, None, kind='kick')
                add('DR', bar * BPB + 2, 0.3, 38, lvl * 0.6, None, kind='snare', pan=0.05)
                for k in range(4): add('DR', bar * BPB + k, 0.1, 42, lvl * 0.09, None, kind='hatc', pan=0.25)
            else:
                for t in (0, 1.5, 2, 2.5) if mode == 'drive' else (0, 1, 2, 3): add('DR', bar * BPB + t, 0.3, 36, lvl * (1.0 if t in (0, 2) else 0.8), None, kind='kick')
                for t in ((1, 3) if mode == 'drive' else (0, 1, 2, 3)): add('DR', bar * BPB + t, 0.3, 38, lvl * 0.75, None, kind='snare', pan=0.05)
                for k in range(8): add('DR', bar * BPB + 0.5 * k, 0.1, 42, lvl * (0.1 if k % 2 == 0 else 0.065), None, kind='hatc', pan=0.25)
    for bar, lvl in FILL:                          # フィル: スネアの 16 分とタム
        for k in range(8):
            t = 2 + 0.25 * k
            if k < 4: add('DR', bar * BPB + t, 0.2, 38, lvl * (0.45 + 0.08 * k), None, kind='snare')
            else: add('DR', bar * BPB + t, 0.3, 45 - 3 * (k - 4), lvl * 0.65, None, kind='tom', pan=(-0.3 + 0.2 * (k - 4)))
    for bar, lvl in CRASH: add('DR', bar * BPB, 2.0, 49, lvl, None, kind='crash', pan=-0.3)
    for b0, b1, gain in STRG:                      # 弦 (和音を全音符で)
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB]); tones = pcs_in(c, 50, 74)
            for iv, m in zip(('VC', 'VA', 'V2', 'V1'), [tones[0], tones[min(1, len(tones) - 1)], tones[min(2, len(tones) - 1)], tones[min(3, len(tones) - 1)]]):
                add(iv, bar * BPB, 4.05, m, gain * dk(P, bar), None)
    for b0, b1, gain, sh in LEAD:                  # リードギターが旋律に重なる
        for s_, d, m, lab in events['S']:
            if b0 * BPB <= s_ < b1 * BPB: add('LG', s_, d * 0.98, m + sh, gain, None)
    for b0, b1, gain, sh in VLN:                   # バイオリンが旋律を弾く (ソロ) / 重なる
        for s_, d, m, lab in events['S']:
            if b0 * BPB <= s_ < b1 * BPB: add('VN', s_, d * 1.0, m + sh, gain, None)

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def place(P, bar, mat_, label, lo=60, hi=79):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > hi: tr -= 12
    while min(ms) + tr < lo: tr += 12
    P.place('S', bar, mat_, tr, label)
def harm_aug(P, b, r):
    rows = []
    for row in CT.harmonize(subj(r)):
        row = row * 4 if len(row) == 1 else row
        rows += [[row[0], row[0], row[1], row[1]], [row[2], row[2], row[3], row[3]]]
    P.set_harms(b, rows)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], 76); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    end4 = REC[R4]['dur'] - 4 * BAR_S * 2 - 0.5
    T5.USED.setdefault(R4, []).append((end4, REC[R4]['dur']))
    total = 8 + 8 + 16 + 8 + 16 + 8 + 16 + 8 + 16 + 16 + 8 + 32 + 2 + 8 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    for v in 'ATB': P.rest_bars(v, 0, total)
    b = 0
    def excerpt(rid, bars, title, sub, semis, t0=None, fout=3.0, gmul=0.6):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, t0=t0, bpm=BPM, gmul=gmul)
        P.rest_bars('S', b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, semis, {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis, src):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, {v: src for v in VOICES}, {})); b += bars; return f
    def melody(f, subs):
        for k, r in enumerate(subs):
            place(P, f + 4 * k, aug(subj(r)), '旋律 (%s) · 2 倍' % hm(r) if k == 0 or r != subs[k - 1] else None); harm_aug(P, f + 4 * k, r)
    PRE = [['Bbmaj7'], ['Bbmaj7'], ['C'], ['C'], ['Dm'], ['Dm'], ['A7'], ['A7']]
    RIFF = [['Dm'], ['Dm'], ['Bb'], ['C'], ['Dm'], ['Dm'], ['Gm'], ['A7']]
    # ================= Intro
    excerpt(R2, 8, 'Intro — %s の実音 (ロ短調)' % hm(R2), '録音の上に、コーラスのクリーン・ギターの分散和音が入ってくる', -3)
    GTR.append((b - 6, b, 0.17, -0.3)); FILL.append((b - 1, 0.1))
    f = section('Intro — バンド (ロ短調)', '♩=148 の 8 ビート、走るベース、歪んだギターのパワーコード', 8, -3, R2)
    P.set_harms(f, RIFF); P.rest_bars('S', f, f + 8); CRASH.append((f, 0.096)); CRASH.append((f + 4, 0.066))
    GTR.append((f, f + 8, 0.15, -0.35)); DGT.append((f, f + 8, 0.1, 'open')); BASS.append((f, f + 8, 0.13)); DRUM.append((f, f + 8, 0.1, 'drive')); FILL.append((f + 7, 0.12))
    # ================= Verse 1 / Pre / Chorus 1
    f = section('Verse 1 — %s の主題 (2 倍の長さで)' % hm(R3), 'ミュートの刻みと 8 分のベース、クリーン・ギター — 旋律はピアノの実音', 16, -3, R3)
    melody(f, [R3, R2, R3, R4]); CRASH.append((f, 0.06))
    GTR.append((f, f + 16, 0.15, -0.3)); DGT.append((f, f + 16, 0.07, 'mute')); BASS.append((f, f + 16, 0.12)); DRUM.append((f, f + 16, 0.09, 'drive'))
    f = section('Pre-chorus — 登っていく和音', 'G△7 - A - Bm - F#7、弦が入り、4 分のスネアで盛り上げる', 8, -3, R3)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 8)
    GTR.append((f, f + 8, 0.16, -0.3)); DGT.append((f, f + 8, 0.08, 'open')); BASS.append((f, f + 8, 0.125)); DRUM.append((f, f + 4, 0.09, 'half')); DRUM.append((f + 4, f + 8, 0.085, 'build')); STRG.append((f, f + 8, 0.035)); FILL.append((f + 7, 0.13))
    for k in range(8): P.dyn[f + k] = DYNK * (1.0 + 0.025 * k)
    f = section('Chorus 1 — %s の主題 (2 倍)' % hm(R1), 'パワーコードが開き、リードギターが重なる、弦', 16, -3, R1)
    melody(f, [R1, R1, R4, R1]); CRASH.append((f, 0.102)); CRASH.append((f + 8, 0.072))
    for k in range(16): P.dyn[f + k] = DYNK * 1.15
    GTR.append((f, f + 16, 0.13, -0.35)); DGT.append((f, f + 16, 0.1, 'open')); BASS.append((f, f + 16, 0.13)); DRUM.append((f, f + 16, 0.105, 'drive')); STRG.append((f, f + 16, 0.04)); LEAD.append((f, f + 16, 0.07, -12)); FILL.append((f + 15, 0.12))
    # ================= Interlude (ヘ短調の実音)
    excerpt(R1, 8, 'Interlude — %s の実音 (ヘ短調)' % hm(R1), '12:46 の録音 (シンセの部分) — ギターの分散和音とベースが寄り添う', 3)
    GTR.append((b - 8, b, 0.11, -0.3)); BASS.append((b - 4, b, 0.09)); DRUM.append((b - 2, b, 0.075, 'half')); FILL.append((b - 1, 0.11))
    # ================= Verse 2 / Pre / Chorus 2
    f = section('Verse 2 — %s と %s の主題' % (hm(R4), hm(R3)), 'ミュートの刻み、弦が薄く残る', 16, -3, R3)
    melody(f, [R4, R3, R2, R3]); CRASH.append((f, 0.072))
    GTR.append((f, f + 16, 0.15, -0.3)); DGT.append((f, f + 16, 0.07, 'mute')); BASS.append((f, f + 16, 0.12)); DRUM.append((f, f + 16, 0.09, 'drive')); STRG.append((f + 8, f + 16, 0.025))
    f = section('Pre-chorus 2', '登っていく和音、4 分のスネア', 8, -3, R3)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 8)
    GTR.append((f, f + 8, 0.16, -0.3)); DGT.append((f, f + 8, 0.08, 'open')); BASS.append((f, f + 8, 0.125)); DRUM.append((f, f + 4, 0.09, 'half')); DRUM.append((f + 4, f + 8, 0.085, 'build')); STRG.append((f, f + 8, 0.035)); FILL.append((f + 7, 0.13))
    for k in range(8): P.dyn[f + k] = DYNK * (1.0 + 0.025 * k)
    f = section('Chorus 2 — %s の主題 (2 倍)' % hm(R1), 'パワーコード、リードギター、弦', 16, -3, R1)
    melody(f, [R1, R1, R4, R1]); CRASH.append((f, 0.102)); CRASH.append((f + 8, 0.072))
    for k in range(16): P.dyn[f + k] = DYNK * 1.15
    GTR.append((f, f + 16, 0.13, -0.35)); DGT.append((f, f + 16, 0.1, 'open')); BASS.append((f, f + 16, 0.13)); DRUM.append((f, f + 16, 0.105, 'drive')); STRG.append((f, f + 16, 0.04)); LEAD.append((f, f + 16, 0.07, -12)); FILL.append((f + 15, 0.13))
    # ================= Violin solo (変ホ短調)
    f = section('Solo — バイオリン (変ホ短調)', '%s と %s の主題を元の速さで、バイオリンが駆ける' % (hm(R4), hm(R1)), 16, 1, R4)
    for k, r in enumerate([R4, R1, R4, R1, R4, R3, R1, R4]):
        place(P, f + 2 * k, subj(r), '旋律 (%s)' % hm(r) if k < 2 else None, lo=67, hi=86); P.set_harms(f + 2 * k, CT.harmonize(subj(r)))
    for k in range(16): P.dyn[f + k] = DYNK * 0.5                       # ピアノは薄く、バイオリンが前に
    CRASH.append((f, 0.09)); GTR.append((f, f + 16, 0.13, -0.35)); DGT.append((f, f + 8, 0.08, 'mute')); DGT.append((f + 8, f + 16, 0.09, 'open'))
    BASS.append((f, f + 16, 0.13)); DRUM.append((f, f + 16, 0.1, 'drive')); VLN.append((f, f + 16, 0.085, 0)); STRG.append((f + 8, f + 16, 0.03)); FILL.append((f + 15, 0.13))
    # ================= Break (変ホ短調の実音)
    excerpt(R4, 8, 'Break — %s の実音 (変ホ短調)' % hm(R4), '13:04 の録音にクリーン・ギターだけが寄り添う — 最後はスネアの 16 分', 1, gmul=1.3)
    GTR.append((b - 8, b, 0.11, -0.3)); DRUM.append((b - 2, b, 0.085, 'build')); FILL.append((b - 1, 0.14))
    # ================= Last chorus ×2 (ハ短調)
    f = section('Last chorus — 半音上のハ短調で 2 回', '全員で — 2 回目はバイオリンが 1 オクターヴ上で重なる', 32, -2, R1)
    melody(f, [R1, R1, R4, R1, R1, R2, R4, R1]); CRASH.append((f, 0.108)); CRASH.append((f + 8, 0.072)); CRASH.append((f + 16, 0.108)); CRASH.append((f + 24, 0.072))
    for k in range(32): P.dyn[f + k] = DYNK * 1.1
    GTR.append((f, f + 32, 0.13, -0.35)); DGT.append((f, f + 32, 0.1, 'open')); BASS.append((f, f + 32, 0.13)); DRUM.append((f, f + 32, 0.11, 'drive')); STRG.append((f, f + 32, 0.045))
    LEAD.append((f, f + 16, 0.06, -12)); VLN.append((f + 16, f + 32, 0.065, 12)); FILL.append((f + 15, 0.13)); FILL.append((f + 31, 0.14))
    # ================= 最後の一撃
    f = section('最後の一撃', '全員で Dm の和音を鳴らし切る', 2, -2, R1)
    P.set_harms(f, [['Dm']] * 2); P.rest_bars('S', f, f + 2); CRASH.append((f, 0.12))
    add('DR', f * BPB, 0.3, 36, 0.11, None, kind='kick'); add('DR', f * BPB, 0.3, 38, 0.075, None, kind='snare')
    add('DG', f * BPB, 6.0, 38, 0.1, None); add('EB', f * BPB, 6.0, 26, 0.13, None)
    for m in (50, 57, 62, 65): add('CG', f * BPB, 6.0, m, 0.12, None)
    for iv, m in (('VC', 50), ('VA', 57), ('V2', 62), ('V1', 69)): add(iv, f * BPB, 6.0, m, 0.04, None)
    # ================= Outro
    excerpt(R4, 8, 'Outro — %s の本当の終わり' % hm(R4), '13:04 の最後の実音に、ギターの分散和音が寄り添って消える', 1, t0=end4, fout=3.0)
    GTR.append((b - 8, b - 2, 0.09, -0.3))
    f = section('Fine', 'add9 の和音で消える', 2, 1, R4)
    P.set_harms(f, [['Dm']] * 2); P.rest_bars('S', f, f + 2)
    for k, m in enumerate((38, 45, 52, 53, 57, 64)): add('CG', f * BPB + 0.5 * k, 5.0, m, 0.15, None, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, 0.2)[k])
    add('EB', f * BPB, 5.0, 26, 0.1, None)
    for iv, m in (('VC', 50), ('VA', 57), ('V2', 64), ('V1', 69)): add(iv, f * BPB, 6.0, m, 0.035, None)
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.4,
    'title': 'Requiem BADA — Tablet Sessions XLII · Ray',
    'subtitle': 'LUNA SEA の Ray を参考にした、疾走する 90 年代のロック — 9/25 の 4 本の録音から (♩=148)',
    'legend': ['TB', 'CG', 'DG', 'EB', 'DR', 'LG', 'VN', 'V1'], 'vname': {'V1': '弦', 'VN': 'バイオリン'},
    'footer': ['Intro 12:50:53 → Verse (12:50:36) → Chorus (12:46) → Interlude → Verse 2 → Chorus 2 → Violin solo (変ホ短調) → Break 13:04 → Last chorus ×2 (ハ短調) → Outro',
               'LUNA SEA の曲は旋律を引用せず、音色と編曲 (駆ける 8 ビート、走るベース、クリーンと歪みの 2 本のギター、バイオリン) だけを参照。旋律は 4 本の録音の主題。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet42.json'
    compose.main(out, seed=142, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
