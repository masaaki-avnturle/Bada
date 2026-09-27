#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLIV · Anubis (LUNA SEA の Anubis を参考にした、暗く重いレクイエム — 2026/9/28 のわたしの声で歌う)
  録音 8 本 (9/22): 09:01・09:09・17:45・17:48・17:51・17:53・17:57・17:59 (XLI・XLIII と同じ)。
  歌: 2026/9/28 06:42 の話し声の録音から、その人の声の母音ごとの響きを取り出し (voice_templates.py)、WORLD で旋律を歌わせる (sing_user.py)。
  LUNA SEA の曲は旋律も歌詞も引用せず、雰囲気と編曲だけを参照する: 暗く重い歪んだギターのリフ、儀式のようなタムの連打、
  コーラスのクリーン・ギターの分散和音 (付点 8 分のディレイ)、うねるベース、弦。歌詞はこの曲のために書いたオリジナル (lyrics_tablet.py)。
  形式 (♩=84):
    Introitus — 17:57 の実音 (ホ短調) にタムの連打 → 重いリフ
    Verse 1 (ホ短調) — 09:09・09:01 の主題をわたしの声で → Pre (刻み) → Chorus 1 (ロ短調、17:59 の主題)
    Interlude — 17:48 の実音 (ロ短調)
    Verse 2 → Pre → Chorus 2 → Lacrimosa (変ロ短調: 17:51 の実音 → 17:53 の主題を 2 倍) → Solo (リードギター、ホ短調)
    → Last chorus ×2 (ロ短調) → In paradisum (09:01 の本当の終わり)
  使い方: python compose_tablet44.py <bank41.json> [score_tablet44.json]  (歌は add_vocals.py tablet44 ... で入れる)
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 84; BAR_S = 240.0 / BPM
A1, A2 = '20260922_090146', '20260922_090933'
Q0, Q1, Q2, Q3, Q5, Q6 = '20260922_174527', '20260922_174820', '20260922_175951', '20260922_175717', '20260922_175145', '20260922_175316'
KEYS = {A1: 2, A2: 2, Q0: -3, Q1: -3, Q2: -3, Q3: 2, Q5: -4, Q6: -4}
T7.KEYS.update(KEYS)
ORDER = [Q1, Q0, Q2, Q3, A1, A2, Q5, Q6]
DYNK = 1.35                                             # 旋律 (ピアノの実音) の倍率 (音量は dyn の 2 乗) — 伴奏は割り戻す
GTR, GTR2, BASS, DRUM, STRG, LEAD, CRASH, FILL = [], [], [], [], [], [], [], []
DGT, TOMS = [], []
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK

def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
def low_root(c, lo=40): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
    for b0, b1, gain, mode in DGT:                 # 歪んだギター: 'riff' = 重いリフ (付点のうねり) / 'mute' = 刻み / 'open' = 開いたパワーコード
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c, 40)
                if mode == 'riff':
                    for t, dd, m, g in ((0, 0.7, r, 1.0), (0.75, 0.2, r, 0.7), (1.0, 0.45, r + 1 if half == 0 else r + 3, 0.8), (1.5, 0.45, r, 0.85)):
                        add('DG', bar * BPB + half + t, dd, m, gain * dk(P, bar) * g, None, mute=dd < 0.3)
                elif mode == 'mute':
                    for k in range(4): add('DG', bar * BPB + half + 0.5 * k, 0.4, r, gain * dk(P, bar) * (1.0 if k == 0 else 0.8), None, mute=True)
                else:
                    add('DG', bar * BPB + half, 1.45, r, gain * dk(P, bar), None); add('DG', bar * BPB + half + 1.5, 0.45, r, gain * dk(P, bar) * 0.85, None)
    for b0, b1, lvl in TOMS:                       # 重いタムの連打 (儀式のように): 低いフロアタムが 8 分で鳴り、2・4 拍目の頭に高いタム
        for bar in range(b0, b1):
            for k in range(8):
                t = 0.5 * k; hi = k in (2, 6)
                add('DR', bar * BPB + t, 0.5, 47 if hi else 40, lvl * (0.9 if k % 4 == 0 else 0.75 if hi else 0.5), None, kind='tom', pan=(0.2 if hi else -0.2))
    for b0, b1, gain, pan in GTR:                  # クリーン・ギター: 8 分の分散和音 + 付点 8 分のディレイ
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c); th = (c['third'] - c['root']) % 12
                pat = [r, r + 7, r + 14, r + 12 + th] if half == 0 else [r + 19, r + 12 + th, r + 14, r + 7]
                if c['major3']: pat = [m - 2 if (m - r) % 12 == 2 else m for m in pat]        # 長三和音 (ヒジャーズの D など) では 9 度を避ける
                for i_, m in enumerate(pat):
                    t = bar * BPB + half + 0.5 * i_; g = gain * dk(P, bar) * (1.0 if i_ == 0 else 0.8)
                    add('CG', t, 1.0, m, g, None, pan=pan); add('CG', t + 0.75, 0.8, m, g * 0.3, None, pan=-pan)
    for b0, b1, gain, pan in GTR2:                 # 2 本目のギター: 高い音域で 16 分ずらす
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); up = pcs_in(c, 59, 76)[:4]
                for i_, m in enumerate(up): add('CG', bar * BPB + half + 0.25 + 0.5 * i_, 0.9, m, gain * dk(P, bar) * 0.8, None, pan=pan)
    for b0, b1, gain, drone in BASS:               # 歌うベース (drone=True: 冥界ではレ (主音) の持続を 8 分で刻む)
        for bar in range(b0, b1):
            c0, c1 = chord(P.harm[bar * BPB]), chord(P.harm[bar * BPB + 2]); nxt = chord(P.harm[min(P.N - 1, (bar + 1) * BPB)])
            r0, r1, rn = low_root(c0, 28), low_root(c1, 28), low_root(nxt, 28)
            if drone:
                seq = [(0, 38), (1.0, 38), (1.5, 38), (2, 38), (3.0, 45 - 12), (3.5, 38)]
            else:
                seq = [(0, r0), (0.5, r0), (1.0, r0 + 12), (1.5, r0 + 7), (2, r1), (2.5, r1), (3.0, r1 + 7 if r1 + 7 <= 47 else r1 - 5), (3.5, rn - 1 if rn != r1 else r1 + 12)]
            for t, m in seq: add('EB', bar * BPB + t, 0.45, m, gain * dk(P, bar) * (1.0 if t in (0, 2) else 0.8), None)
    for b0, b1, lvl, mode in DRUM:                 # ドラム: ハーフタイム / 8 ビート
        for bar in range(b0, b1):
            if mode == 'half':
                for t in (0, 2.5): add('DR', bar * BPB + t, 0.3, 36, lvl * 0.9, None, kind='kick')
                add('DR', bar * BPB + 2, 0.3, 38, lvl * 0.55, None, kind='snare', pan=0.05)
                for k in range(8): add('DR', bar * BPB + 0.5 * k, 0.1, 42, lvl * (0.09 if k % 2 == 0 else 0.055), None, kind='hatc', pan=0.25)
            else:
                for t in (0, 1.5, 2.5): add('DR', bar * BPB + t, 0.3, 36, lvl, None, kind='kick')
                for t in (1, 3): add('DR', bar * BPB + t, 0.3, 38, lvl * 0.75, None, kind='snare', pan=0.05)
                for k in range(8): add('DR', bar * BPB + 0.5 * k, 0.1, 42, lvl * (0.11 if k % 2 == 0 else 0.07), None, kind='hatc', pan=0.25)
    for bar, lvl in FILL:
        for k, t in enumerate((2, 2.5, 3, 3.5)):
            if k < 2: add('DR', bar * BPB + t, 0.3, 38, lvl * (0.5 + 0.15 * k), None, kind='snare')
            else: add('DR', bar * BPB + t, 0.4, 45 - 5 * (k - 2), lvl * 0.7, None, kind='tom', pan=(-0.2, 0.2)[k - 2])
    for bar, lvl in CRASH: add('DR', bar * BPB, 2.0, 49, lvl, None, kind='crash', pan=-0.3)
    for b0, b1, gain in STRG:                      # 弦 (和音を全音符で)
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
def place(P, bar, mat_, label):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > 79: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)
def harm_of(P, b, mat_): P.set_harms(b, CT.harmonize(mat_))
def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], 72); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    endA = REC[A1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(A1, []).append((endA, REC[A1]['dur']))
    total = 4 + 4 + 8 + 4 + 8 + 6 + 8 + 4 + 8 + 4 + 4 + 8 + 16 + 5 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    for v in 'ATB': P.rest_bars(v, 0, total)
    b = 0
    def excerpt(rid, bars, title, sub, semis, t0=None, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, t0=t0, bpm=BPM, gmul=0.6)
        P.rest_bars('S', b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, semis, {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis, src):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, {v: src for v in VOICES}, {})); b += bars; return f
    def melody(f, subs):
        for k, r in enumerate(subs):
            place(P, f + 2 * k, subj(r), '旋律 (%s)' % hm(r) if k == 0 or r != subs[k - 1] else None); harm_of(P, f + 2 * k, subj(r))
    RIFF = [['Dm'], ['Dm'], ['Bb'], ['A7']]
    PRE = [['Bbmaj7'], ['C'], ['Dm'], ['A7']]
    # ================= Introitus (ホ短調)
    excerpt(Q3, 4, 'Introitus — %s の実音 (ホ短調)' % hm(Q3), '17:57 の録音に、儀式のようなタムの連打が近づいてくる', 2)
    TOMS.append((b - 2, b, 0.1)); FILL.append((b - 1, 0.2))
    f = section('Introitus — 重いリフ (ホ短調)', '暗く重い歪んだギターのリフ、うねるベース、タムの連打', 4, 2, A2)
    P.set_harms(f, RIFF); P.rest_bars('S', f, f + 4); CRASH.append((f, 0.14))
    DGT.append((f, f + 4, 0.1, 'riff')); BASS.append((f, f + 4, 0.13, False)); TOMS.append((f, f + 4, 0.12)); GTR.append((f + 2, f + 4, 0.12, -0.3)); FILL.append((f + 3, 0.24))
    # ================= Verse 1 / Pre / Chorus 1
    f = section('Verse 1 — %s と %s の主題 (ホ短調)' % (hm(A2), hm(A1)), 'わたしの声が歌う — クリーン・ギターの分散和音、ハーフタイムのドラム、うねるベース', 8, 2, A2)
    melody(f, [A2, A1, A2, Q3]); CRASH.append((f, 0.1))
    GTR.append((f, f + 8, 0.17, -0.3)); BASS.append((f, f + 8, 0.12, False)); DRUM.append((f, f + 8, 0.16, 'half')); DGT.append((f + 4, f + 8, 0.05, 'mute'))
    f = section('Pre-chorus — 刻みとタム', 'B♭△7 - C - Dm - A7 (ホ短調の枠)、歪んだギターの刻み、タムの連打で高まる', 4, 2, A2)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.16, -0.3)); DGT.append((f, f + 4, 0.08, 'mute')); BASS.append((f, f + 4, 0.125, False)); TOMS.append((f, f + 4, 0.12)); STRG.append((f, f + 4, 0.035)); FILL.append((f + 3, 0.26))
    for k in range(4): P.dyn[f + k] = DYNK * (1.0 + 0.05 * k)
    f = section('Chorus 1 — %s の主題 (ロ短調)' % hm(Q2), 'パワーコードが開き、8 ビート、弦 — わたしの声がサビを歌う', 8, -3, Q2)
    melody(f, [Q2, Q2, Q0, Q2]); CRASH.append((f, 0.15)); CRASH.append((f + 4, 0.1))
    for k in range(8): P.dyn[f + k] = DYNK * 1.15
    GTR.append((f, f + 8, 0.15, -0.35)); DGT.append((f, f + 8, 0.09, 'open')); BASS.append((f, f + 8, 0.13, False)); DRUM.append((f, f + 8, 0.19, 'full')); STRG.append((f, f + 8, 0.04))
    # ================= Interlude (ロ短調の実音)
    excerpt(Q1, 6, 'Interlude — %s の実音 (ロ短調)' % hm(Q1), '17:48 の録音に、クリーン・ギターと弦が寄り添う', -3)
    GTR.append((b - 6, b, 0.11, -0.3)); STRG.append((b - 4, b, 0.025)); TOMS.append((b - 2, b, 0.09)); FILL.append((b - 1, 0.22))
    # ================= Verse 2 / Pre / Chorus 2
    f = section('Verse 2 — %s と %s の主題 (ホ短調)' % (hm(Q3), hm(A2)), 'リフが低く続き、わたしの声が歌う', 8, 2, Q3)
    melody(f, [Q3, A2, Q3, A1]); CRASH.append((f, 0.1))
    GTR.append((f, f + 8, 0.15, -0.3)); DGT.append((f, f + 8, 0.06, 'riff')); BASS.append((f, f + 8, 0.12, False)); DRUM.append((f, f + 8, 0.16, 'half')); STRG.append((f + 4, f + 8, 0.025))
    f = section('Pre-chorus 2', '刻みとタムの連打', 4, 2, A2)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.16, -0.3)); DGT.append((f, f + 4, 0.08, 'mute')); BASS.append((f, f + 4, 0.125, False)); TOMS.append((f, f + 4, 0.12)); STRG.append((f, f + 4, 0.035)); FILL.append((f + 3, 0.26))
    for k in range(4): P.dyn[f + k] = DYNK * (1.0 + 0.05 * k)
    f = section('Chorus 2 — %s の主題 (ロ短調)' % hm(Q2), 'パワーコード、8 ビート、弦', 8, -3, Q2)
    melody(f, [Q2, Q2, Q0, Q2]); CRASH.append((f, 0.15)); CRASH.append((f + 4, 0.1))
    for k in range(8): P.dyn[f + k] = DYNK * 1.15
    GTR.append((f, f + 8, 0.15, -0.35)); DGT.append((f, f + 8, 0.09, 'open')); BASS.append((f, f + 8, 0.13, False)); DRUM.append((f, f + 8, 0.19, 'full')); STRG.append((f, f + 8, 0.04)); FILL.append((f + 7, 0.24))
    # ================= Lacrimosa (変ロ短調)
    excerpt(Q5, 4, 'Lacrimosa — %s の実音 (変ロ短調)' % hm(Q5), '17:51 の録音に、ギターの分散和音と弦', -4)
    GTR.append((b - 4, b, 0.1, -0.3)); STRG.append((b - 3, b, 0.025))
    f = section('Lacrimosa — %s の主題を 2 倍の長さで' % hm(Q6), 'わたしの声と弦とピアノだけ — 最後の和音 A7 でホ短調のソロへ', 4, -4, Q6)
    place(P, f, aug(subj(Q6)), '旋律 (%s) · 2 倍' % hm(Q6)); T5.harm_from_entries(P, f, f + 4, [(f * BPB, [(d, m + 12) for d, m in aug(subj(Q6))])])
    for k in range(4): P.dyn[f + k] = DYNK * 1.1
    STRG.append((f, f + 4, 0.04)); GTR.append((f + 2, f + 4, 0.1, -0.3)); TOMS.append((f + 3, f + 4, 0.1)); FILL.append((f + 3, 0.24))
    # ================= Solo (ホ短調)
    f = section('Solo — リードギター (ホ短調)', '%s と %s の主題をリードギターが歌い、重いリフとタム' % (hm(A1), hm(Q3)), 8, 2, A1)
    melody(f, [A1, Q3, A1, A2]); CRASH.append((f, 0.14))
    for k in range(8): P.dyn[f + k] = DYNK * 0.8
    DGT.append((f, f + 8, 0.08, 'riff')); GTR.append((f, f + 8, 0.12, -0.35)); BASS.append((f, f + 8, 0.13, False)); DRUM.append((f, f + 4, 0.18, 'full')); TOMS.append((f + 4, f + 8, 0.1)); LEAD.append((f, f + 8, 0.07, 0)); FILL.append((f + 7, 0.26))
    # ================= Last chorus ×2 (ロ短調)
    f = section('Last chorus — ロ短調で 2 回', '全員で — 2 回目はリードギターが 1 オクターヴ上で重なる', 16, -3, Q2)
    melody(f, [Q2, Q2, Q0, Q2, Q2, Q1, Q0, Q2]); CRASH.append((f, 0.17)); CRASH.append((f + 8, 0.17))
    for k in range(16): P.dyn[f + k] = DYNK * 1.2
    GTR.append((f, f + 16, 0.15, -0.35)); DGT.append((f, f + 16, 0.09, 'open')); BASS.append((f, f + 16, 0.13, False)); DRUM.append((f, f + 16, 0.2, 'full')); STRG.append((f, f + 16, 0.045))
    LEAD.append((f + 8, f + 16, 0.04, 0)); FILL.append((f + 7, 0.26)); FILL.append((f + 15, 0.28))
    # ================= In paradisum
    excerpt(A1, 5, 'In paradisum — %s の本当の終わり' % hm(A1), '09:01 の最後の実音に、ギターの分散和音と弦が寄り添って消える', 2, t0=endA, fout=2.5)
    GTR.append((b - 5, b - 1, 0.1, -0.3)); CRASH.append((b - 5, 0.11)); STRG.append((b - 5, b - 2, 0.02)); TOMS.append((b - 5, b - 3, 0.06))
    f = section('Fine', 'add9 の和音で消える', 2, 2, A1)
    P.set_harms(f, [['Dm']] * 2); P.rest_bars('S', f, f + 2)
    for k, m in enumerate((38, 45, 52, 53, 57, 64)): add('CG', f * BPB + 0.5 * k, 6.0, m, 0.18, None, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, 0.2)[k])
    add('EB', f * BPB, 6.0, 26, 0.12, None); add('DG', f * BPB, 5.0, 38, 0.06, None)
    for iv, m in (('VC', 50), ('VA', 57), ('V2', 64), ('V1', 69)): add(iv, f * BPB, 7.0, m, 0.04, None)
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.6,
    'title': 'Requiem BADA — Tablet Sessions XLIV · Anubis',
    'subtitle': 'LUNA SEA の Anubis を参考にした、暗く重いレクイエム — 9/28 のわたしの声で歌う (♩=84)',
    'legend': ['TB', 'CG', 'DG', 'EB', 'DR', 'LG', 'V1'], 'vname': {'V1': '弦'},
    'footer': ['Introitus 17:57 → Riff → Verse (09:09) → Pre → Chorus (17:59) → Interlude 17:48 → Verse 2 → Chorus 2 → Lacrimosa 17:51 → Solo → Last chorus ×2 → In paradisum 09:01',
               'LUNA SEA の曲は旋律も歌詞も引用せず、雰囲気と編曲だけを参照。歌は 9/28 のわたしの声 (話し声から取り出した響き) で、歌詞はオリジナル。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet44.json'
    compose.main(out, seed=144, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
