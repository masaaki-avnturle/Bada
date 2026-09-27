#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XL · Human Nature (SWV「Right Here (Human Nature Remix)」のような 90 年代 R&B のスロー・ジャム)
  録音 9 本 (9/22): 09:09・17:45・17:48 (2 本)・17:51・17:53・17:54・17:57・17:59。
  SWV の曲とその元の Michael Jackson「Human Nature」は旋律も印象的なフレーズも引用せず、音と編曲だけを参照する:
  16 分のスウィングのヒップホップのビート (キック・スネア・やわらかいハイハット)、あたたかいローズ、なめらかなベース、7 と 9 の和音、弦。
  旋律は 9 本の録音の主題 (録音から切り出したピアノの実音)。
  調: ニ長調 / ロ短調 (17:45・17:48・17:59) を中心に、ホ短調の 17:57 を ii の間奏に、変ロ短調の 3 本 (17:51・17:53・17:54) を
  ブリッジに通って、最後のサビは半音上の変ホ長調へ (R&B の転調)。♩=90。
    Intro → Verse 1 → Pre → Chorus 1 → Interlude (17:57, ホ短調) → Verse 2 → Pre → Chorus 2 → Bridge (17:51, 変ロ短調)
    → Last chorus ×2 (変ホ長調) → Outro (グルーヴがフェードして、ローズの E♭maj9)
  使い方: python compose_tablet40.py <bank40.json> [score_tablet40.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 90; BAR_S = 240.0 / BPM; SW = 0.07                       # 16 分のスウィング (裏の 16 分を遅らせる拍数)
Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7 = '20260922_174527', '20260922_174820', '20260922_175951', '20260922_175717', '20260922_090933', '20260922_175145', '20260922_175316', '20260922_175429'
KEYS = {Q0: -3, Q1: -3, Q2: -3, Q3: 2, Q4: 2, Q5: -4, Q6: -4, Q7: -4}
T7.KEYS.update(KEYS)
ORDER = [Q1, Q0, Q2, Q3, Q4, Q5, Q6, Q7]
JAZZ = {'Dm': 'Dm7', 'Gm': 'Gm7', 'A': 'A7', 'A7': 'A7', 'F': 'Fmaj7', 'Bb': 'Bbmaj7', 'C': 'C7', 'Em7b5': 'Em7b5', 'Gm/Bb': 'Gm7', 'Dm/F': 'Fmaj7'}
DYNK = 1.55                                                      # 旋律 (ピアノの実音) の倍率 (音量は dyn の 2 乗) — 伴奏は割り戻す
RHC, RHA, BASS, BEAT, STRG, VDBL = [], [], [], [], [], []
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK
def sw(t): return t + (SW if abs((t * 4) % 2 - 1) < 1e-6 else 0.0)      # 裏の 16 分だけ遅らせる

def voicing(c):
    r = c['root']; th = (c['third'] - r) % 12; sev = (c['seventh'] - r) % 12 if c['seventh'] is not None else (11 if c['major3'] else 10)
    pcs = [(r + th) % 12, (r + sev) % 12, (r + 2) % 12, (r + 7) % 12]
    return sorted(min((x for x in range(55, 73) if x % 12 == pc), key=lambda x: abs(x - 63)) for pc in pcs)
def low_root(c, lo=28): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
    for b0, b1, gain in RHC:                    # ローズのコンピング: 1 拍目 (長く)、2 拍目の裏の 16 分、3 拍目の裏
        for bar in range(b0, b1):
            for t, d in ((0, 1.6), (1.75, 0.6), (2.5, 1.3)):
                c = chord(P.harm[bar * BPB + int(t)])
                for j, m in enumerate(voicing(c)): add('RH', bar * BPB + sw(t) + 0.012 * j, d, m, gain * dk(P, bar) * (1.0 if t == 0 else 0.8), None, pan=(-0.25, -0.08, 0.08, 0.25)[j])
    for b0, b1, gain in RHA:                    # ローズの 16 分の分散和音 (夢見るように上がる、自作の音型)
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); v = voicing(c)
                for i_, m in enumerate(v + [v[0] + 12, v[2] + 12, v[1] + 12, v[3]]):
                    add('RH', bar * BPB + half + sw(0.25 * i_), 0.5, m, gain * dk(P, bar) * (0.9 if i_ % 4 == 0 else 0.7), None, pan=(-0.4 + 0.1 * i_))
    for b0, b1, gain in BASS:                   # なめらかなベース: 根音、オクターヴ、5 度、次の和音へのつなぎ
        for bar in range(b0, b1):
            c0, c1 = chord(P.harm[bar * BPB]), chord(P.harm[bar * BPB + 2]); nx = chord(P.harm[min(P.N - 1, (bar + 1) * BPB)])
            r0, r1, rn = low_root(c0), low_root(c1), low_root(nx)
            f1 = r1 + 7 if r1 + 7 <= 45 else r1 - 5
            for t, d, m, g in ((0, 1.2, r0, 1.0), (1.5, 0.4, r0 + 12, 0.7), (2, 0.6, r1, 0.95), (2.75, 0.2, f1, 0.7), (3.5, 0.4, rn + (1 if rn > r1 else -1) if rn != r1 else r1 + 12, 0.75)):
                add('EB', bar * BPB + sw(t), d, m, gain * dk(P, bar) * g, None)
    for b0, b1, lvl, full in BEAT:              # ビート: キック (1・2 拍目の裏の 16 分・3 拍目の裏)、スネア 2・4、やわらかいハイハット
        for bar in range(b0, b1):
            for t in ((0, 0.75, 2.5) if full else (0, 2.5)): add('DR', bar * BPB + sw(t), 0.3, 36, lvl, None, kind='kick')
            for t in (1, 3): add('DR', bar * BPB + t, 0.3, 38, lvl * 0.7, None, kind='snare', pan=0.05)
            for k in range(8): add('DR', bar * BPB + 0.5 * k, 0.1, 42, lvl * (0.1 if k % 2 == 0 else 0.065), None, kind='hatc', pan=0.25)
            if full:
                for t in (1.75, 3.75): add('DR', bar * BPB + sw(t), 0.1, 42, lvl * 0.05, None, kind='hatc', pan=0.25)
    for b0, b1, gain in STRG:
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); tones = sorted(set(voicing(c)))
                for iv, m in zip(('VC', 'VA', 'V2', 'V1'), tones): add(iv, bar * BPB + half, 2.05, m - (12 if iv == 'VC' else 0), gain * dk(P, bar), None)
    for b0, b1, gain in VDBL:
        for s_, d, m, lab in events['S']:
            if b0 * BPB <= s_ < b1 * BPB: add('V1', s_, d * 1.02, m + 12, gain, None)

def subj(r): return T5.SUBJ[r][0]
def place(P, bar, mat_, label):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > 79: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)
def harm_of(P, b, mat_): P.set_harms(b, [[JAZZ.get(c, c) for c in bar] for bar in CT.harmonize(mat_)])

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], BPM); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    total = 4 + 8 + 4 + 8 + 4 + 8 + 4 + 8 + 4 + 4 + 16 + 4 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    for v in 'ATB': P.rest_bars(v, 0, total)
    b = 0
    def excerpt(rid, bars, title, sub, semis):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=2.5, bpm=BPM, gmul=0.6)
        P.rest_bars('S', b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, semis, {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis, src):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, {v: src for v in VOICES}, {})); b += bars; return f
    def melody(f, subs):
        for k, r in enumerate(subs):
            place(P, f + 2 * k, subj(r), '旋律 (%s)' % hm(r) if k == 0 or r != subs[k - 1] else None); harm_of(P, f + 2 * k, subj(r))
    PRE = [['Bbmaj7'], ['Am7'], ['Gm7'], ['C7']]                 # (ロ短調の枠で) G△7 - F#m7 - Em7 - A7
    # Intro
    excerpt(Q1, 4, 'Intro — %s の実音 (ニ長調 / ロ短調)' % hm(Q1), '録音の上に、あたたかいローズの 16 分の分散和音が入ってくる', -3)
    RHA.append((b - 3, b, 0.040))
    # Verse 1 / Pre / Chorus 1
    f = section('Verse 1 — %s と %s の主題' % (hm(Q0), hm(Q1)), '16 分のスウィングのビート、ローズのコンピング、なめらかなベース — 旋律はピアノの実音', 8, -3, Q0)
    melody(f, [Q0, Q1, Q0, Q1]); RHC.append((f, f + 8, 0.048)); BASS.append((f, f + 8, 0.14)); BEAT.append((f, f + 8, 0.145, False))
    f = section('Pre-chorus', 'G△7 - F#m7 - Em7 - A7、弦が入る', 4, -3, Q1)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    RHC.append((f, f + 4, 0.052)); RHA.append((f + 2, f + 4, 0.030)); BASS.append((f, f + 4, 0.14)); BEAT.append((f, f + 4, 0.153, True)); STRG.append((f, f + 4, 0.03))
    f = section('Chorus 1 — %s の主題' % hm(Q2), '弦と Vn I が旋律に重なる、ビートが厚く', 8, -3, Q2)
    melody(f, [Q2, Q2, Q1, Q2])
    for k in range(8): P.dyn[f + k] = DYNK * 1.08
    RHC.append((f, f + 8, 0.052)); BASS.append((f, f + 8, 0.15)); BEAT.append((f, f + 8, 0.162, True)); STRG.append((f, f + 8, 0.035)); VDBL.append((f, f + 8, 0.06))
    # Interlude (ii = ホ短調)
    excerpt(Q3, 4, 'Interlude — %s の実音 (ホ短調)' % hm(Q3), 'ニ長調の ii (Em) の録音 — ローズの分散和音とベースが寄り添う', 2)
    RHA.append((b - 4, b, 0.035)); BASS.append((b - 2, b, 0.1))
    # Verse 2 / Pre / Chorus 2
    f = section('Verse 2 — %s と %s の主題' % (hm(Q4), hm(Q3)), 'ビートが戻る', 8, -3, Q4)
    melody(f, [Q4, Q3, Q4, Q0]); RHC.append((f, f + 8, 0.048)); BASS.append((f, f + 8, 0.14)); BEAT.append((f, f + 8, 0.145, True)); STRG.append((f + 4, f + 8, 0.02))
    f = section('Pre-chorus 2', 'G△7 - F#m7 - Em7 - A7', 4, -3, Q1)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    RHC.append((f, f + 4, 0.052)); RHA.append((f + 2, f + 4, 0.030)); BASS.append((f, f + 4, 0.14)); BEAT.append((f, f + 4, 0.153, True)); STRG.append((f, f + 4, 0.03))
    f = section('Chorus 2 — %s の主題' % hm(Q2), '弦と Vn I、ビート', 8, -3, Q2)
    melody(f, [Q2, Q2, Q1, Q2])
    for k in range(8): P.dyn[f + k] = DYNK * 1.08
    RHC.append((f, f + 8, 0.052)); BASS.append((f, f + 8, 0.15)); BEAT.append((f, f + 8, 0.162, True)); STRG.append((f, f + 8, 0.035)); VDBL.append((f, f + 8, 0.06))
    # Bridge (変ロ短調) → 変ホ長調へ
    excerpt(Q5, 4, 'Bridge — %s の実音 (変ロ短調)' % hm(Q5), '変ロ短調の 3 本 (17:51・17:53・17:54) を通って、半音上の変ホ長調へ', -4)
    RHA.append((b - 4, b, 0.030))
    f = section('Bridge — %s と %s の主題 (変ロ短調)' % (hm(Q6), hm(Q7)), 'ビートを抜いて、ローズとベースと弦だけ — 最後の和音 B♭7 (変ホ長調の V) で次へ', 4, -4, Q6)
    melody(f, [Q6, Q7]); P.set_harms(f + 3, [['Gm7', 'Gm7', 'D7', 'D7']])
    RHC.append((f, f + 4, 0.048)); BASS.append((f, f + 4, 0.12)); STRG.append((f, f + 4, 0.035))
    # Last chorus ×2 (変ホ長調 = ハ短調の枠)
    f = section('Last chorus — 半音上の変ホ長調で 2 回', '全員で — 2 回目は Vn I が 1 オクターヴ上で歌い、弦が厚く', 16, -2, Q2)
    melody(f, [Q2, Q2, Q1, Q2, Q2, Q0, Q1, Q2])
    for k in range(16): P.dyn[f + k] = DYNK * 1.12
    RHC.append((f, f + 16, 0.052)); BASS.append((f, f + 16, 0.15)); BEAT.append((f, f + 16, 0.170, True)); STRG.append((f, f + 16, 0.04)); VDBL.append((f + 8, f + 16, 0.07))
    # Outro: グルーヴがフェード
    f = section('Outro — グルーヴがフェードして', 'ローズとベースとビートが少しずつ遠のき、E♭maj9 で消える', 4, -2, Q2)
    P.set_harms(f, [['Fmaj7'], ['Gm7'], ['Fmaj7'], ['Gm7', 'Gm7', 'C7', 'C7']]); P.rest_bars('S', f, f + 4)
    for k in range(4): P.dyn[f + k] = DYNK * (1 - 0.18 * k)
    RHC.append((f, f + 4, 0.048)); BASS.append((f, f + 4, 0.13)); BEAT.append((f, f + 3, 0.128, True)); RHA.append((f + 2, f + 4, 0.025))
    f = section('Fine', 'E♭maj9', 2, -2, Q2)
    P.set_harms(f, [['Fmaj7']] * 2); P.rest_bars('S', f, f + 2)
    for j, m in enumerate((29, 41, 48, 52, 55, 57, 64)): add('RH' if m > 40 else 'EB', f * BPB + 0.15 * j, 7.0, m, 0.07 if m > 40 else 0.12, None)
    for iv, m in (('VC', 41), ('VA', 52), ('V2', 57), ('V1', 64)): add(iv, f * BPB, 7.0, m, 0.035, None)
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.6,
    'title': 'Requiem BADA — Tablet Sessions XL · Human Nature',
    'subtitle': 'SWV「Right Here (Human Nature Remix)」のような 90 年代 R&B のスロー・ジャム — 9/22 の 9 本の録音から (♩=90)',
    'legend': ['TB', 'RH', 'EB', 'DR', 'V1'], 'vname': {'V1': '弦'},
    'footer': ['Intro 17:48 → Verse → Pre → Chorus (17:59) → Interlude 17:57 (ホ短調) → Verse 2 → Pre → Chorus 2 → Bridge 17:51 (変ロ短調) → Last chorus ×2 (変ホ長調) → Outro',
               'SWV と Michael Jackson の曲は旋律もフレーズも引用せず、音と編曲 (スウィングのビート、ローズ、ベース、7・9 の和音) だけを参照。旋律は 9 本の録音の主題。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet40.json'
    compose.main(out, seed=140, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
