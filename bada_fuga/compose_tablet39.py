#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXXIX · Eden (LUNA SEA の EDEN のような、もの悲しい 90 年代のロック)
  録音 3 本: 9/25 12:46 (ヘ短調)、12:50:53 (ロ短調)、13:04 (変ホ短調)。
  LUNA SEA の曲は旋律を引用せず、音色と編曲だけを参照する: コーラスのかかったクリーン・ギターの分散和音 (付点 8 分のディレイ)、
  歌うように動くピック弾きのベース、ハーフタイムのバラードから開くドラム、もの悲しい弦、リードギター。旋律は 3 本の録音の主題。
  形式 (♩=76):
    Intro    — 12:50:53 の実音 (ロ短調) に、ギターの分散和音が入ってくる → ギター + ベース + ドラムのイントロ
    Verse 1  — 12:50:53 の主題 (ピアノの実音)、ハーフタイムのドラム、ギターの分散和音 + ディレイ、歌うベース
    Pre      — 登っていく和音 (G△7 - A - Bm - F#7)、弦が入り、スネアのフィル
    Chorus 1 — 12:46 の主題、リードギターが重なる、2 本のギター、8 分のハイハット、弦
    Verse 2 / Pre / Chorus 2 — 13:04 の主題を交えて
    Interlude— 12:46 の実音 (ヘ短調) → ギター・ソロ (12:46 と 13:04 の主題)
    Bridge   — 変ホ短調へ: ピアノと弦だけ、13:04 の主題を 2 倍の長さで
    Chorus 3 — 変ホ短調で 2 回、2 回目はリードギターが 1 オクターヴ上
    Outro    — 13:04 の本当の終わり (実音) にギターの分散和音が寄り添い、add9 の和音で消える
  使い方: python compose_tablet39.py <bank37.json> [score_tablet39.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 76; BAR_S = 240.0 / BPM
R1, R2, R4 = '20260925_124643', '20260925_125053', '20260925_130431'
KEYS = {R1: 3, R2: -3, R4: 1}
T7.KEYS.update(KEYS)
ORDER = [R2, R1, R4]
GTR, GTR2, BASS, DRUM, STRG, LEAD, CRASH, FILL = [], [], [], [], [], [], [], []
DYNK = 1.55                                             # 旋律 (ピアノの実音) を上げる倍率 (音量は dyn の 2 乗で効く) — 伴奏はこの分を割り戻す
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK

def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
def low_root(c, lo=40): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
    for b0, b1, gain, pan in GTR:                  # クリーン・ギター: 8 分の分散和音 + 付点 8 分のディレイ
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c); th = (c['third'] - c['root']) % 12
                dom = c['major3'] and c['seventh'] is not None
                nine = r + 12 if dom else r + 14
                pat = [r, r + 7, nine, r + 12 + th] if half == 0 else [r + 19, r + 12 + th, nine, r + 7]
                for i_, m in enumerate(pat):
                    t = bar * BPB + half + 0.5 * i_; g = gain * dk(P, bar) * (1.0 if i_ == 0 else 0.8)
                    add('CG', t, 1.0, m, g, None, pan=pan); add('CG', t + 0.75, 0.8, m, g * 0.3, None, pan=-pan)
    for b0, b1, gain, pan in GTR2:                 # 2 本目のギター: 高い音域で 16 分ずらした分散和音
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); up = pcs_in(c, 59, 76)[:4]
                for i_, m in enumerate(up + up[1:3][::-1]):
                    if i_ < 4: add('CG', bar * BPB + half + 0.25 + 0.5 * i_, 0.9, m, gain * dk(P, bar) * 0.8, None, pan=pan)
    for b0, b1, gain in BASS:                      # 歌うベース: 8 分の根音、オクターヴの跳躍、次の和音へのつなぎ
        for bar in range(b0, b1):
            c0, c1 = chord(P.harm[bar * BPB]), chord(P.harm[bar * BPB + 2]); nxt = chord(P.harm[min(P.N - 1, (bar + 1) * BPB)])
            r0, r1, rn = low_root(c0, 28), low_root(c1, 28), low_root(nxt, 28)
            seq = [(0, r0), (0.5, r0), (1.0, r0 + 12), (1.5, r0 + 7), (2, r1), (2.5, r1), (3.0, r1 + 7 if r1 + 7 <= 47 else r1 - 5), (3.5, rn - 1 if (rn - r1) % 12 not in (0,) else r1 + 12)]
            for t, m in seq: add('EB', bar * BPB + t, 0.45, m, gain * dk(P, bar) * (1.0 if t in (0, 2) else 0.8), None)
    for b0, b1, lvl, mode in DRUM:                 # ドラム: ハーフタイム (verse) / 8 ビート (chorus)
        for bar in range(b0, b1):
            if mode == 'half':
                for t in (0, 2.5): add('DR', bar * BPB + t, 0.3, 36, lvl * 0.9, None, kind='kick')
                add('DR', bar * BPB + 2, 0.3, 38, lvl * 0.55, None, kind='snare', pan=0.05)
                for k in range(8): add('DR', bar * BPB + 0.5 * k, 0.1, 42, lvl * (0.1 if k % 2 == 0 else 0.06), None, kind='hatc', pan=0.25)
            else:
                for t in (0, 1.5, 2.5): add('DR', bar * BPB + t, 0.3, 36, lvl, None, kind='kick')
                for t in (1, 3): add('DR', bar * BPB + t, 0.3, 38, lvl * 0.75, None, kind='snare', pan=0.05)
                for k in range(8): add('DR', bar * BPB + 0.5 * k, 0.1, 42, lvl * (0.13 if k % 2 == 0 else 0.08), None, kind='hatc', pan=0.25)
    for bar, lvl in FILL:                          # フィル: スネアの 8 分とタム
        for k, t in enumerate((2, 2.5, 3, 3.5)):
            if k < 2: add('DR', bar * BPB + t, 0.3, 38, lvl * (0.5 + 0.15 * k), None, kind='snare')
            else: add('DR', bar * BPB + t, 0.4, 45 - 5 * (k - 2), lvl * 0.7, None, kind='tom', pan=(-0.2, 0.2)[k - 2])
    for bar, lvl in CRASH: add('DR', bar * BPB, 2.0, 49, lvl, None, kind='crash', pan=-0.3)
    for b0, b1, gain in STRG:                      # もの悲しい弦 (和音を全音符で)
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); tones = pcs_in(c, 50, 74)
                for iv, m in zip(('VC', 'VA', 'V2', 'V1'), [tones[0], tones[min(1, len(tones) - 1)], tones[min(2, len(tones) - 1)], tones[min(3, len(tones) - 1)]]):
                    add(iv, bar * BPB + half, 2.05, m, gain * dk(P, bar), None)
    for b0, b1, gain, sh in LEAD:                  # リードギターが旋律に重なる
        for s_, d, m, lab in events['S']:
            if b0 * BPB <= s_ < b1 * BPB: add('LG', s_, d * 0.98, m + sh, gain, None)

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def place(P, bar, mat_, tr, label):
    ms = [m for _, m in mat_ if m is not None]
    while max(ms) + tr > 79: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)
def harm_of(P, b, mat_): P.set_harms(b, CT.harmonize(mat_))

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], BPM); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    end4 = REC[R4]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(R4, []).append((end4, REC[R4]['dur']))
    total = 6 + 4 + 8 + 4 + 8 + 8 + 4 + 8 + 6 + 8 + 4 + 16 + 5 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    for v in VOICES: P.rest_bars(v, 0, total) if v != 'S' else None
    b = 0
    def excerpt(rid, bars, title, sub, semis, t0=None, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, t0=t0, bpm=BPM, gmul=0.6)
        P.rest_bars('S', b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK                     # passage() が 0.42 にするのを戻す (伴奏の音量のため)
        CT.LAYOUT.append((b, b + bars, semis, {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis, src):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, {v: src for v in VOICES}, {})); b += bars; return f
    def verse(f, subs):
        for k, r in enumerate(subs):
            place(P, f + 2 * k, subj(r), 0, '旋律 (%s)' % hm(r) if k == 0 or r != subs[k - 1] else None); harm_of(P, f + 2 * k, subj(r))
    PRE = [['Bbmaj7'], ['C'], ['Dm'], ['A7']]
    # ================= Intro (ロ短調)
    excerpt(R2, 6, 'Intro — %s の実音 (ロ短調)' % hm(R2), '録音の上に、コーラスのかかったクリーン・ギターの分散和音が入ってくる', -3)
    GTR.append((b - 4, b, 0.2, -0.3))
    f = section('Intro — ギター・ベース・ドラム', 'もの悲しい分散和音 (付点 8 分のディレイ) と歌うベース — 3 小節目からドラム', 4, -3, R2)
    P.set_harms(f, [['Dm'], ['Bb'], ['Gm'], ['A7']]); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.2, -0.3)); BASS.append((f + 1, f + 4, 0.12)); DRUM.append((f + 2, f + 4, 0.17, 'half')); FILL.append((f + 3, 0.2))
    # ================= Verse 1 / Pre / Chorus 1
    f = section('Verse 1 — %s の主題 (ロ短調)' % hm(R2), 'ハーフタイムのドラム、ギターの分散和音とディレイ、歌うベース — 旋律はピアノの実音', 8, -3, R2)
    verse(f, [R2, R2, R4, R2]); CRASH.append((f, 0.090))
    GTR.append((f, f + 8, 0.18, -0.3)); BASS.append((f, f + 8, 0.12)); DRUM.append((f, f + 8, 0.17, 'half'))
    f = section('Pre-chorus — 登っていく和音', 'G△7 - A - Bm - F#7、弦が入り、スネアのフィル', 4, -3, R2)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.2, -0.3)); GTR2.append((f + 2, f + 4, 0.1, 0.35)); BASS.append((f, f + 4, 0.125)); DRUM.append((f, f + 4, 0.19, 'half')); STRG.append((f, f + 4, 0.035)); FILL.append((f + 3, 0.24))
    for k in range(4): P.dyn[f + k] = DYNK * (1.0 + 0.05 * k)
    f = section('Chorus 1 — %s の主題' % hm(R1), 'リードギターが旋律に重なり、2 本のギター、8 ビート、もの悲しい弦', 8, -3, R1)
    verse(f, [R1, R1, R4, R1]); CRASH.append((f, 0.150)); CRASH.append((f + 4, 0.100))
    for k in range(8): P.dyn[f + k] = DYNK * (1.2)
    GTR.append((f, f + 8, 0.2, -0.35)); GTR2.append((f, f + 8, 0.12, 0.35)); BASS.append((f, f + 8, 0.13)); DRUM.append((f, f + 8, 0.2, 'full')); STRG.append((f, f + 8, 0.04)); LEAD.append((f, f + 8, 0.085, -12))
    # ================= Verse 2 / Pre / Chorus 2
    f = section('Verse 2 — %s と %s の主題' % (hm(R2), hm(R4)), 'ハーフタイムに戻る — 弦が薄く残る', 8, -3, R2)
    verse(f, [R4, R2, R4, R2])
    GTR.append((f, f + 8, 0.18, -0.3)); BASS.append((f, f + 8, 0.12)); DRUM.append((f, f + 8, 0.17, 'half')); STRG.append((f + 4, f + 8, 0.025))
    f = section('Pre-chorus 2', '登っていく和音、スネアのフィル', 4, -3, R2)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.2, -0.3)); GTR2.append((f, f + 4, 0.1, 0.35)); BASS.append((f, f + 4, 0.125)); DRUM.append((f, f + 4, 0.19, 'half')); STRG.append((f, f + 4, 0.035)); FILL.append((f + 3, 0.24))
    for k in range(4): P.dyn[f + k] = DYNK * (1.0 + 0.05 * k)
    f = section('Chorus 2 — %s の主題' % hm(R1), 'リードギターと 2 本のギター、8 ビート、弦', 8, -3, R1)
    verse(f, [R1, R1, R4, R1]); CRASH.append((f, 0.150)); CRASH.append((f + 4, 0.100))
    for k in range(8): P.dyn[f + k] = DYNK * (1.2)
    GTR.append((f, f + 8, 0.2, -0.35)); GTR2.append((f, f + 8, 0.12, 0.35)); BASS.append((f, f + 8, 0.13)); DRUM.append((f, f + 8, 0.2, 'full')); STRG.append((f, f + 8, 0.04)); LEAD.append((f, f + 8, 0.085, -12))
    # ================= Interlude → Solo (ヘ短調)
    excerpt(R1, 6, 'Interlude — %s の実音 (ヘ短調)' % hm(R1), '12:46 の録音 (シンセの部分) — ギターの分散和音が寄り添う', 3)
    GTR.append((b - 6, b, 0.12, -0.3))
    f = section('Guitar solo — %s と %s の主題 (ヘ短調)' % (hm(R1), hm(R4)), 'リードギターが主題を歌い、2 本のギターとベース、8 ビート', 8, 3, R1)
    verse(f, [R1, R4, R1, R4]); CRASH.append((f, 0.140))
    for k in range(8): P.dyn[f + k] = DYNK * (1.1)
    GTR.append((f, f + 8, 0.18, -0.35)); GTR2.append((f, f + 8, 0.11, 0.35)); BASS.append((f, f + 8, 0.13)); DRUM.append((f, f + 8, 0.2, 'full')); STRG.append((f + 4, f + 8, 0.035)); LEAD.append((f, f + 8, 0.06, 0)); FILL.append((f + 7, 0.24))
    # ================= Bridge (変ホ短調)
    f = section('Bridge — %s の主題を 2 倍の長さで (変ホ短調)' % hm(R4), 'ピアノと弦だけ — もの悲しく静かに', 4, 1, R4)
    place(P, f, aug(subj(R4)), 0, '旋律 (%s) · 2 倍' % hm(R4)); T5.harm_from_entries(P, f, f + 4, [(f * BPB, [(d, m + 12) for d, m in aug(subj(R4))])])
    for k in range(4): P.dyn[f + k] = DYNK * (0.95)
    STRG.append((f, f + 4, 0.04)); GTR.append((f + 2, f + 4, 0.1, -0.3)); FILL.append((f + 3, 0.22))
    # ================= Chorus 3 ×2 (変ホ短調)
    f = section('Last chorus — 変ホ短調で 2 回', '全員で — 2 回目はリードギターが 1 オクターヴ上で歌う', 16, 1, R1)
    verse(f, [R1, R1, R4, R1, R1, R1, R4, R4]); CRASH.append((f, 0.170)); CRASH.append((f + 8, 0.170))
    for k in range(16): P.dyn[f + k] = DYNK * (1.25)
    GTR.append((f, f + 16, 0.2, -0.35)); GTR2.append((f, f + 16, 0.12, 0.35)); BASS.append((f, f + 16, 0.13)); DRUM.append((f, f + 16, 0.21, 'full')); STRG.append((f, f + 16, 0.045))
    LEAD.append((f, f + 8, 0.05, -12)); LEAD.append((f + 8, f + 16, 0.05, 0)); FILL.append((f + 7, 0.26)); FILL.append((f + 15, 0.26))
    # ================= Outro
    excerpt(R4, 5, 'Outro — %s の本当の終わり' % hm(R4), '13:04 の最後の実音に、ギターの分散和音が寄り添って消える', 1, t0=end4, fout=2.5)
    GTR.append((b - 5, b - 1, 0.1, -0.3)); CRASH.append((b - 5, 0.110))
    P.set_harms(b, [['Dm']] * 2); P.rest_bars('S', b, b + 2)
    for k, m in enumerate((38, 45, 52, 53, 57, 64)): add('CG', b * BPB + 0.5 * k, 6.0, m, 0.18, None, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, 0.2)[k])
    add('EB', b * BPB, 6.0, 26, 0.12, None)
    for iv, m in (('VC', 50), ('VA', 57), ('V2', 64), ('V1', 69)): add(iv, b * BPB, 7.0, m, 0.04, None)
    CT.LAYOUT.append((b, b + 2, 1, {v: R4 for v in VOICES}, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.6,
    'title': 'Requiem BADA — Tablet Sessions XXXIX · Eden',
    'subtitle': 'LUNA SEA の EDEN のような、もの悲しい 90 年代のロック — 9/25 の 3 本の録音から (♩=76)',
    'legend': ['TB', 'CG', 'EB', 'DR', 'LG', 'V1'], 'vname': {'V1': '弦'},
    'footer': ['Intro 12:50 → Verse → Pre → Chorus (12:46) → Verse 2 → Pre → Chorus 2 → Interlude 12:46 → Guitar solo → Bridge (変ホ短調) → Last chorus ×2 → Outro 13:04',
               'LUNA SEA の曲は旋律を引用せず、音色と編曲 (コーラスのクリーン・ギター、ディレイ、歌うベース、弦) だけを参照。旋律は 3 本の録音の主題、ピアノの実音で。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet39.json'
    compose.main(out, seed=139, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
