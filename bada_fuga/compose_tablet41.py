#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLI · Recall (LUNA SEA の Recall のようなロックに、Anubis の冥界の響きを合わせたレクイエム)
  録音 8 本 (9/22): 09:01・09:09・17:45・17:48・17:51・17:53・17:57・17:59。
  LUNA SEA の曲は旋律を引用せず、音色と編曲だけを参照する: コーラスのかかったクリーン・ギターの分散和音 (付点 8 分のディレイ)、
  歌うベース、ハーフタイムから 8 ビートへ開くドラム、リードギター、弦。
  Anubis (死者の魂を冥界へ導くエジプトの神) の響き: ヒジャーズの旋法 (レ・ミ♭・ファ#・ソ・ラ・シ♭・ド)、タンプーラの持続音、
  ダラブッカ (dum / tek) と枠太鼓、ウード、ネイ (笛)、低い合唱。旋律は 8 本の録音の主題 (ピアノの実音) — 冥界の部分ではヒジャーズに読み替える。
  レクイエムの流れ: Introitus → Kyrie → Sequentia → Requiem aeternam → Duat (冥界) → Lacrimosa → Lux aeterna → In paradisum。
  調: ロ短調 (17:45・17:48・17:59) を中心に、ホ短調の 09:01・09:09・17:57 を冥界 (ホのヒジャーズ) に、変ロ短調の 17:51・17:53 を
  Lacrimosa に通って、最後のサビは半音上のロ短調に戻る。♩=72。
  使い方: python compose_tablet41.py <bank41.json> [score_tablet41.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 72; BAR_S = 240.0 / BPM
A1, A2 = '20260922_090146', '20260922_090933'
Q0, Q1, Q2, Q3, Q5, Q6 = '20260922_174527', '20260922_174820', '20260922_175951', '20260922_175717', '20260922_175145', '20260922_175316'
KEYS = {A1: 2, A2: 2, Q0: -3, Q1: -3, Q2: -3, Q3: 2, Q5: -4, Q6: -4}
T7.KEYS.update(KEYS)
ORDER = [Q1, Q0, Q2, Q3, A1, A2, Q5, Q6]
DYNK = 1.35                                             # 旋律 (ピアノの実音) の倍率 (音量は dyn の 2 乗) — 伴奏は割り戻す
GTR, GTR2, BASS, DRUM, STRG, LEAD, CRASH, FILL = [], [], [], [], [], [], [], []
CHOIR, DRONE, DARB, OUD, NEY = [], [], [], [], []
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK

HIJAZ = {4: 3, 5: 6, 1: 0}                              # ニ短調の枠 → レのヒジャーズ (ミ→ミ♭、ファ→ファ#、ド#→ド)
HSCALE = [2, 3, 6, 7, 9, 10, 0]
def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
def low_root(c, lo=40): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
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
    for b0, b1, lvl, mode in DARB:                 # ダラブッカ: マクスーム (dum tek - tek dum - tek -) / 枠太鼓の遅い鼓動
        for bar in range(b0, b1):
            if mode == 'daf':
                for t, g in ((0, 1.0), (2.5, 0.6)): add('DR', bar * BPB + t, 1.0, 36, lvl * g, None, kind='daf', pan=-0.1)
            else:
                for t, k_, g in ((0, 'dum', 1.0), (0.5, 'tek', 0.55), (1.5, 'tek', 0.6), (2, 'dum', 0.9), (3, 'tek', 0.6), (3.75, 'tek', 0.35)):
                    add('DR', bar * BPB + t, 0.3, 38, lvl * g, None, kind=k_, pan=(-0.15 if k_ == 'dum' else 0.2))
                if bar % 2 == 1:
                    for t in (3.25, 3.5): add('DR', bar * BPB + t, 0.2, 38, lvl * 0.3, None, kind='tek', pan=0.25)
    for b0, b1, gain in STRG:                      # 弦 (和音を全音符で)
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); tones = pcs_in(c, 50, 74)
                for iv, m in zip(('VC', 'VA', 'V2', 'V1'), [tones[0], tones[min(1, len(tones) - 1)], tones[min(2, len(tones) - 1)], tones[min(3, len(tones) - 1)]]):
                    add(iv, bar * BPB + half, 2.05, m, gain * dk(P, bar), None)
    for b0, b1, gain in CHOIR:                     # 低い合唱 (Ah): 1 小節ずつ和音を保つ
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB]); tones = pcs_in(c, 45, 64)
            for j, m in enumerate([tones[0], tones[len(tones) // 2], tones[-1]]):
                add('CO', bar * BPB, 4.1, m, gain * dk(P, bar), None, pan=(-0.3, 0.0, 0.3)[j])
    for b0, b1, gain in DRONE:                     # タンプーラ: 主音と 5 度の持続音 (枠のレ、区間ごとに移調される)
        for bar in range(b0, b1, 2):
            for m, g in ((38, 1.0), (45, 0.7), (50, 0.5)): add('TA', bar * BPB, 8.2, m, gain * g, None)
    for b0, b1, gain in OUD:                       # ウード: ヒジャーズの上下する 8 分の音型 + 小節頭のトレモロ
        for bar in range(b0, b1):
            pat = (50, 51, 54, 55, 57, 55, 54, 51) if bar % 2 == 0 else (57, 58, 57, 55, 54, 51, 50, 51)
            for k, m in enumerate(pat): add('OU', bar * BPB + 0.5 * k, 0.45, m, gain * dk(P, bar) * (1.0 if k % 4 == 0 else 0.75), None)
            for k in range(4): add('OU', bar * BPB + 0.125 * k, 0.12, 38, gain * dk(P, bar) * 0.5, None)
    for s_, d, m, g in NEY: add('BN', s_ * BPB, d, m, g, None)
    for b0, b1, gain, sh in LEAD:                  # リードギターが旋律に重なる
        for s_, d, m, lab in events['S']:
            if b0 * BPB <= s_ < b1 * BPB: add('LG', s_, d * 0.98, m + sh, gain, None)

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def hijaz(mat_): return [(d, (m - m % 12 + HIJAZ.get(m % 12, m % 12)) if m is not None else None) for d, m in mat_]
def place(P, bar, mat_, label):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > 79: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)
def harm_of(P, b, mat_): P.set_harms(b, CT.harmonize(mat_))
def harm_hijaz(P, b, mat_):
    """ヒジャーズの和声: 2 拍ごとに D / E♭ / Cm / Gm から旋律をいちばん覆う和音 (小節頭は主和音の D を優先)"""
    cands = {'D': {2, 6, 9}, 'Eb': {3, 7, 10}, 'Cm': {0, 3, 7}, 'Gm': {7, 10, 2}}
    bars = []; t = 0.0; ev = []
    for d, m in mat_:
        if m is not None: ev.append((t, d, m % 12))
        t += d
    nb = int(round(t / BPB))
    for bb in range(nb):
        row = []
        for half in (0, 2):
            lo, hi = bb * BPB + half, bb * BPB + half + 2
            w = {}
            for s_, d, pc in ev:
                ov = min(hi, s_ + d) - max(lo, s_)
                if ov > 0: w[pc] = w.get(pc, 0) + ov * (1.5 if lo <= s_ < lo + 0.5 else 1.0)
            best = max(cands, key=lambda c: sum(v for pc, v in w.items() if pc in cands[c]) + (0.6 if c == 'D' and half == 0 else 0) + (0.2 if c == 'D' else 0))
            row += [best, best]
        bars.append(row)
    P.set_harms(b, bars)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], BPM); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    endA = REC[A1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(A1, []).append((endA, REC[A1]['dur']))
    total = 4 + 6 + 4 + 8 + 4 + 8 + 6 + 8 + 8 + 5 + 4 + 16 + 5 + 2
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
    def melody(f, subs, hij=False):
        for k, r in enumerate(subs):
            m_ = hijaz(subj(r)) if hij else subj(r)
            place(P, f + 2 * k, m_, '旋律 (%s)' % hm(r) if k == 0 or r != subs[k - 1] else None)
            (harm_hijaz if hij else harm_of)(P, f + 2 * k, m_)
    PRE = [['Bbmaj7'], ['C'], ['Dm'], ['A7']]
    # ================= Introitus: 冥界の入口 (レのヒジャーズ → ホ短調の実音)
    f = section('Introitus — 冥界の入口', 'タンプーラの持続音、枠太鼓の遅い鼓動、ネイがヒジャーズの旋法を歌う', 4, 2, A1)
    P.set_harms(f, [['D'], ['D', 'D', 'Eb', 'Eb'], ['Cm', 'Cm', 'D', 'D'], ['D']]); P.rest_bars('S', f, f + 4)
    DRONE.append((f, f + 4, 0.125)); DARB.append((f + 1, f + 4, 0.16, 'daf')); CHOIR.append((f + 2, f + 4, 0.0308))
    for s_, d, m in ((0.5, 2.5, 69), (3.2, 0.3, 70), (3.5, 2.0, 69), (5.5, 1.0, 67), (6.5, 1.5, 66), (8.0, 1.0, 63), (9.0, 3.0, 62),
                     (12.0, 1.0, 66), (13.0, 1.0, 67), (14.0, 2.0, 70)):
        NEY.append((f + s_ / BPB, d, m, 0.033))                                 # 自作のヒジャーズの節 (ラ・シ♭・ソ・ファ#・ミ♭・レ)
    excerpt(A1, 6, 'Introitus — %s の実音 (ホ短調)' % hm(A1), '09:01 の録音に、低い合唱とタンプーラが寄り添う', 2)
    CHOIR.append((b - 6, b, 0.0252)); DRONE.append((b - 6, b - 2, 0.075)); GTR.append((b - 2, b, 0.15, -0.3))
    # ================= Intro (ロ短調)
    f = section('Intro — ギター・ベース・ドラム (ロ短調)', 'コーラスのクリーン・ギターの分散和音 (付点 8 分のディレイ) と歌うベース', 4, -3, Q1)
    P.set_harms(f, [['Dm'], ['Bb'], ['Gm'], ['A7']]); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.2, -0.3)); BASS.append((f + 1, f + 4, 0.12, False)); DRUM.append((f + 2, f + 4, 0.17, 'half')); FILL.append((f + 3, 0.2))
    # ================= Kyrie = Verse 1 / Pre / Sequentia = Chorus 1
    f = section('Kyrie — %s と %s の主題' % (hm(Q1), hm(Q0)), 'ハーフタイムのドラム、ギターの分散和音とディレイ — 旋律はピアノの実音', 8, -3, Q1)
    melody(f, [Q1, Q0, Q1, Q0]); CRASH.append((f, 0.09))
    GTR.append((f, f + 8, 0.18, -0.3)); BASS.append((f, f + 8, 0.12, False)); DRUM.append((f, f + 8, 0.17, 'half')); CHOIR.append((f + 4, f + 8, 0.0168))
    f = section('Pre-chorus — 登っていく和音', 'G△7 - A - Bm - F#7、弦と合唱が入り、スネアのフィル', 4, -3, Q1)
    P.set_harms(f, PRE); P.rest_bars('S', f, f + 4)
    GTR.append((f, f + 4, 0.2, -0.3)); GTR2.append((f + 2, f + 4, 0.1, 0.35)); BASS.append((f, f + 4, 0.125, False)); DRUM.append((f, f + 4, 0.19, 'half')); STRG.append((f, f + 4, 0.035)); CHOIR.append((f, f + 4, 0.0224)); FILL.append((f + 3, 0.24))
    for k in range(4): P.dyn[f + k] = DYNK * (1.0 + 0.05 * k)
    f = section('Sequentia — %s の主題 (サビ)' % hm(Q2), 'リードギターが重なり、2 本のギター、8 ビート、弦と合唱', 8, -3, Q2)
    melody(f, [Q2, Q2, Q0, Q2]); CRASH.append((f, 0.15)); CRASH.append((f + 4, 0.1))
    for k in range(8): P.dyn[f + k] = DYNK * 1.2
    GTR.append((f, f + 8, 0.2, -0.35)); GTR2.append((f, f + 8, 0.12, 0.35)); BASS.append((f, f + 8, 0.13, False)); DRUM.append((f, f + 8, 0.2, 'full')); STRG.append((f, f + 8, 0.04)); CHOIR.append((f, f + 8, 0.0224)); LEAD.append((f, f + 8, 0.08, -12))
    # ================= Requiem aeternam (ホ短調の実音)
    excerpt(Q3, 6, 'Requiem aeternam — %s の実音 (ホ短調)' % hm(Q3), '17:57 の録音、ドラムを抜いて合唱と弦だけ — 冥界へ下りていく', 2)
    CHOIR.append((b - 6, b, 0.028)); STRG.append((b - 4, b, 0.025)); DRONE.append((b - 2, b, 0.0875)); DARB.append((b - 2, b, 0.14, 'daf'))
    # ================= Duat: 冥界 (ホのヒジャーズ)
    f = section('Duat — 冥界 (ホのヒジャーズ)', '%s と %s の主題をヒジャーズに読み替え、ウード・ダラブッカ・タンプーラ・合唱' % (hm(A2), hm(Q3)), 8, 2, A2)
    melody(f, [A2, Q3, A2, A1], hij=True)
    DRONE.append((f, f + 8, 0.1)); DARB.append((f, f + 8, 0.2, 'maqsum')); OUD.append((f, f + 8, 0.245)); CHOIR.append((f, f + 8, 0.0224)); BASS.append((f + 4, f + 8, 0.1, True))
    f = section('Duat — ギター・ソロ', 'リードギターがヒジャーズの主題を歌い、ダラブッカとドラム、ギターの分散和音', 8, 2, A1)
    melody(f, [A1, A2, Q3, A2], hij=True); CRASH.append((f, 0.14))
    for k in range(8): P.dyn[f + k] = DYNK * 1.1
    GTR.append((f, f + 8, 0.16, -0.35)); BASS.append((f, f + 8, 0.12, True)); DRUM.append((f, f + 8, 0.17, 'half')); DARB.append((f, f + 8, 0.16, 'maqsum')); OUD.append((f + 4, f + 8, 0.175)); LEAD.append((f, f + 8, 0.05, 0)); DRONE.append((f, f + 8, 0.075)); FILL.append((f + 7, 0.24))
    # ================= Lacrimosa (変ロ短調)
    excerpt(Q5, 5, 'Lacrimosa — %s の実音 (変ロ短調)' % hm(Q5), '17:51 の録音に、ギターの分散和音と合唱が寄り添う', -4)
    GTR.append((b - 5, b, 0.1, -0.3)); CHOIR.append((b - 3, b, 0.0252))
    f = section('Lacrimosa — %s の主題を 2 倍の長さで' % hm(Q6), 'ピアノと弦と合唱だけ — 最後の和音 F#7 で半音上のロ短調へ', 4, -4, Q6)
    place(P, f, aug(subj(Q6)), '旋律 (%s) · 2 倍' % hm(Q6)); T5.harm_from_entries(P, f, f + 4, [(f * BPB, [(d, m + 12) for d, m in aug(subj(Q6))])])
    P.set_harms(f + 3, [['Gm', 'Gm', 'G#dim7', 'G#dim7']])
    for k in range(4): P.dyn[f + k] = DYNK * 1.15
    STRG.append((f, f + 4, 0.04)); CHOIR.append((f, f + 4, 0.028)); GTR.append((f + 2, f + 4, 0.1, -0.3)); FILL.append((f + 3, 0.22))
    # ================= Lux aeterna: 最後のサビ ×2 (ロ短調)
    f = section('Lux aeterna — 最後のサビ ×2 (ロ短調)', '全員で — 2 回目はリードギターが 1 オクターヴ上、ダラブッカも加わる', 16, -3, Q2)
    melody(f, [Q2, Q2, Q0, Q2, Q2, Q1, Q0, Q2]); CRASH.append((f, 0.17)); CRASH.append((f + 8, 0.17))
    for k in range(16): P.dyn[f + k] = DYNK * 1.25
    GTR.append((f, f + 16, 0.2, -0.35)); GTR2.append((f, f + 16, 0.12, 0.35)); BASS.append((f, f + 16, 0.13, False)); DRUM.append((f, f + 16, 0.21, 'full')); STRG.append((f, f + 16, 0.045)); CHOIR.append((f, f + 16, 0.0224))
    DARB.append((f + 8, f + 16, 0.12, 'maqsum')); LEAD.append((f, f + 8, 0.05, -12)); LEAD.append((f + 8, f + 16, 0.05, 0)); FILL.append((f + 7, 0.26)); FILL.append((f + 15, 0.26))
    # ================= In paradisum: 09:01 の本当の終わり → ホ長調 (ピカルディ) で消える
    excerpt(A1, 5, 'In paradisum — %s の本当の終わり' % hm(A1), '09:01 の最後の実音にタンプーラと合唱が寄り添い、魂が送られていく', 2, t0=endA, fout=2.5)
    DRONE.append((b - 5, b, 0.0875)); CHOIR.append((b - 5, b - 1, 0.0224)); GTR.append((b - 5, b - 2, 0.09, -0.3)); DARB.append((b - 5, b - 2, 0.1, 'daf'))
    f = section('Fine', 'ホ長調の和音 (ヒジャーズの主和音) で消える', 2, 2, A1)
    P.set_harms(f, [['D']] * 2); P.rest_bars('S', f, f + 2)
    for k, m in enumerate((38, 45, 50, 54, 57, 62)): add('CG', f * BPB + 0.5 * k, 6.0, m, 0.16, None, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, 0.2)[k])
    for m in (50, 57, 62): add('CO', f * BPB, 7.0, m, 0.028, None)
    for m, g in ((38, 1.0), (45, 0.7)): add('TA', f * BPB, 8.0, m, 0.1 * g, None)
    add('EB', f * BPB, 6.0, 26, 0.1, None); add('OU', f * BPB + 2.5, 3.0, 50, 0.2, None)
    for iv, m in (('VC', 50), ('VA', 57), ('V2', 62), ('V1', 66)): add(iv, f * BPB, 7.0, m, 0.035, None)
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.6,
    'title': 'Requiem BADA — Tablet Sessions XLI · Recall',
    'subtitle': 'LUNA SEA の Recall のようなロックに Anubis の冥界の響きを合わせたレクイエム — 9/22 の 8 本 (♩=72)',
    'legend': ['TB', 'CG', 'EB', 'DR', 'OU', 'CO', 'V1'], 'vname': {'V1': '弦'},
    'footer': ['Introitus (09:01) → Intro → Kyrie → Pre → Sequentia (17:59) → Requiem aeternam 17:57 → Duat (ヒジャーズ) → Solo → Lacrimosa 17:51 (変ロ短調) → Lux aeterna ×2 → In paradisum 09:01',
               'LUNA SEA の曲は旋律を引用せず、音色と編曲だけを参照。冥界の部分はヒジャーズの旋法・ウード・ダラブッカ・タンプーラ・ネイ。旋律は 8 本の録音の主題。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet41.json'
    compose.main(out, seed=141, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
