#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fantaisie-Révolution — 録音 5 本 (2026-09-24) を、ショパンの「革命のエチュード」(Op.10-12, ハ短調) と
「幻想即興曲」(Op.66, 嬰ハ短調) の書法でリメイクしたピアノ曲。鳴る音はすべて録音の 1 音 (build_sampler.py のサンプラー)。
  旋律は録音の最上声から作った主題 (compose_tablet.make_subject) を、それぞれの調と書法に移したもの。
    Preludio — 録音 11:18 の実音
    Rivoluzione — ハ短調 Allegro con fuoco: 属和音 (G7♭9) の強打と左手の下行する奔流 → 右手のオクターヴで主題 (11:18, 08:49)
    Ponte — G7 → G♯7: 半音ずり上げて嬰ハ短調へ
    Fantaisie — 嬰ハ短調 Allegro agitato: 左手の 3 連符の分散和音 (8 分音符 6 つ) に右手の 16 分音符 (4 対 3)、主題 (11:21, 08:53)
    Moderato cantabile — 変ニ長調: 11:23 の主題を長調にして歌う (左手は広い分散和音)
    Fantaisie — ripresa → Coda (革命の奔流で嬰ハ短調の強奏) → 幻想即興曲の終わりのように、低音に歌の旋律が静かに戻る (嬰ハ長調)
  使い方: python compose_tablet_chopin.py <bank.json> [score_chopin.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT          # 抜粋と主題 (同じ bank.json を読む)
import compose_tablet3 as T3

REC, hm = CT.REC, T3.hm
R_REV, R_REV2, R_FI, R_FI2, R_CAN = '20260924_111846', '20260924_084937', '20260924_112131', '20260924_085314', '20260924_112313'
KEYS = {R_REV: -4, R_REV2: 3, R_FI: 3, R_FI2: 2, R_CAN: 2}           # 録音の調 (ニ短調からの移調)
LH_SRC = {'rev': R_REV2, 'fi': R_FI2, 'can': R_CAN}
X = []

def pf(beat, dbeats, m, gain, rid, label=None, rel=0.35):
    X.append({'v': 'PF', 'beat': round(beat, 4), 'dbeats': dbeats, 'm': int(m), 'gain': gain, 'label': label, 'rid': rid, 'rel': rel})

def subject(rid, semis_to):
    """録音の主題 (ニ短調) を取り出し、目的の調へ移す"""
    t0, inside = CT.excerpt(rid, KEYS[rid], 13.0)
    return [(d, m + semis_to) for d, m in CT.make_subject(inside, KEYS[rid], 56)]

def to_major(subj):
    """ニ短調の主題をニ長調へ (F → F#, B♭ → B, C# はそのまま)"""
    return [(d, m + (1 if m % 12 in (5, 10) else 0)) for d, m in subj]

def spans(mel, start):
    out, t = [], start
    for d, m in mel: out.append((t, d, m)); t += d
    return out

def harmonize(mel_spans, b0, nbeats, cands, first=None, last=None):
    """2 拍ごとに、旋律の音を最も多く和音構成音にする和音を選ぶ"""
    labs = []
    for h in range(nbeats // 2):
        a, z = b0 + 2 * h, b0 + 2 * h + 2
        def sc(c):
            pcs = chord(c)['pcs']; s = 0.0
            for t, d, m in mel_spans:
                ov = min(z, t + d) - max(a, t)
                if ov > 0: s += ov * (2 if a <= t < a + 0.01 else 1) * (1 if m % 12 in pcs else -0.8)
            return s
        labs.append(max(cands, key=sc))
    if first: labs[0] = first
    if last: labs[-1] = last
    return labs

def set_harm(P, b0, labs):
    for h, c in enumerate(labs):
        for q in range(2): P.harm[b0 + 2 * h + q] = c

def near(pc, target, lo=None, hi=None):
    c = [x for x in range(24, 100) if x % 12 == pc and (lo is None or x >= lo) and (hi is None or x <= hi)]
    return min(c, key=lambda x: abs(x - target))

HMIN = {'C': [0, 2, 3, 5, 7, 8, 11], 'C#': [1, 3, 4, 6, 8, 9, 0]}

def rev_run(b0, lab, key, rid, gain=0.2, up_first=False):
    """革命の左手: 2 拍 (16 分音符 8 つ) で音階を駆け下り、次の 2 拍で和音を駆け上がる"""
    c = chord(lab); scale = sorted(set(HMIN[key]) | set(c['pcs']))
    top = near(c['root'], 67 if not up_first else 43)
    down = [x for x in range(top, 30, -1) if x % 12 in scale][:8]
    arp = [x for x in range(down[-1], 80) if x % 12 in c['pcs']][:8]
    seq = (arp + down) if up_first else (down + arp)
    for k, m in enumerate(seq): pf(b0 + k * 0.25, 0.3, m, gain * (1.25 if k % 4 == 0 else 1.0), rid, rel=0.25)

def rev_melody(mel_spans, labs, b0, rid, label, gain=0.42):
    """右手のオクターヴの旋律 + 強拍の和音"""
    for t, d, m in mel_spans:
        pf(t, d * 0.92, m, gain, rid, label, rel=0.45); pf(t, d * 0.92, m - 12, gain * 0.75, rid, label, rel=0.45)
        h = labs[min(len(labs) - 1, int((t - b0) // 2))]
        if abs((t - b0) % 2) < 1e-6:
            for pc in chord(h)['pcs'][:3]:
                x = near(pc, m - 6, hi=m - 1)
                if x > m - 12: pf(t, min(d, 1.0) * 0.8, x, gain * 0.45, rid, rel=0.4)

def fi_lh(b0, lab, rid, gain=0.18):
    """幻想即興曲の左手: 2 拍に 3 連符の 8 分音符 6 つ (根音 - 5 度 - 根音 - 10 度 - 根音 - 5 度)"""
    c = chord(lab); r = near(c['root'], 40, lo=36, hi=47); f = r + ((c['fifth'] - c['root']) % 12); t3 = r + 12 + ((c['third'] - c['root']) % 12)
    for k, m in enumerate([r, f, r + 12, t3, r + 12, f]): pf(b0 + k / 3.0, 0.45, m, gain * (1.3 if k == 0 else 1.0), rid, rel=0.5)

def fi_rh(mel_spans, labs, b0, nbeats, rid, label, gain=0.2):
    """幻想即興曲の右手: 1 拍に 16 分音符 4 つ — 拍の頭が旋律の音、そこから下の刺繍音で回り、和音を駆け上がる"""
    for q in range(nbeats):
        t = b0 + q; cur = [s for s in mel_spans if s[0] <= t + 1e-6 < s[0] + s[1]]
        if not cur: continue
        s0, d, m = cur[0]; c = chord(labs[min(len(labs) - 1, q // 2)])
        up = [x for x in range(m + 1, m + 13) if x % 12 in c['pcs']]
        if abs(t - s0) < 1e-6: fig = [m, m - 1, m, up[0] if up else m + 3]
        elif (t - s0) % 2 < 1e-6: fig = [m] + up[:3]
        else: fig = [up[1] if len(up) > 1 else m + 7, up[0] if up else m + 3, m, m - 1 if (m - 1) % 12 in HMIN['C#'] else m - 2]
        for k, x in enumerate(fig): pf(t + k * 0.25, 0.28, x, gain * (1.6 if k == 0 else 1.0), rid, label if k == 0 else None, rel=0.3)

def can_lh(b0, lab, rid, gain=0.16):
    """カンタービレの左手: 2 拍に 3 連符 6 つの広い分散和音"""
    c = chord(lab); r = near(c['root'], 38, lo=34, hi=45)
    seq = [r, r + ((c['fifth'] - c['root']) % 12), r + 12, r + 12 + ((c['third'] - c['root']) % 12), r + 12 + ((c['fifth'] - c['root']) % 12), r + 12 + ((c['third'] - c['root']) % 12)]
    for k, m in enumerate(seq): pf(b0 + k / 3.0, 0.9, m, gain * (1.3 if k == 0 else 1.0), rid, rel=0.9)

def can_rh(mel_spans, labs, b0, rid, label, gain=0.42):
    for t, d, m in mel_spans:
        pf(t, d * 0.98, m, gain, rid, label, rel=0.8)
        h = labs[min(len(labs) - 1, int((t - b0) // 2))]
        if d >= 1:
            inner = [x for x in range(m - 9, m - 2) if x % 12 in chord(h)['pcs']]
            if inner: pf(t + 0.02, d * 0.9, inner[-1], gain * 0.35, rid, rel=0.8)

REV_C = ['Cm', 'Fm', 'G7', 'Ab', 'Eb', 'Dm7b5', 'Bb7']
FI_C = ['C#m', 'F#m', 'G#7', 'A', 'E', 'D#m7b5', 'B7']
CAN_C = ['Db', 'Gb', 'Ab7', 'Ebm', 'Bbm', 'Fm', 'Ebm7']

def stretch(mel, k): return [(d * k, m) for d, m in mel]

def build():
    rev = stretch(subject(R_REV, -2), 2); rev2 = stretch(subject(R_REV2, -2), 2)
    fi = stretch(subject(R_FI, -1), 2); fi2 = stretch(subject(R_FI2, -1), 2)
    can = stretch(to_major(subject(R_CAN, -1)), 2)
    bars = [('pre', 3, 66), ('intro', 8, 144), ('tema', 8, 144), ('ponte', 2, 144), ('fi_intro', 2, 152), ('fi', 8, 152), ('fi_cad', 2, 152),
            ('can', 8, 66), ('can2', 8, 63), ('fi_rip', 8, 152), ('coda', 6, 144), ('fine', 4, 60)]
    total = sum(n_ for _, n_, _ in bars)
    P = Piece(total); starts = {}; b = 0
    for name, nb, bpm in bars:
        starts[name] = b
        for k in range(nb): P.tempo[b + k] = bpm; P.dyn[b + k] = 0.8
        b += nb
    for v in VOICES: P.rest_bars(v, 0, total)
    B = lambda name: starts[name] * BPB
    # ---- Preludio: 録音 11:18 の実音
    b0 = starts['pre']
    P.section(b0, 'Preludio — 録音 %s の実音' % hm(R_REV), '録音 %s の実音 — この録音の音と旋律から、革命と幻想即興曲が始まる' % R_REV)
    t0, inside = CT.excerpt(R_REV, KEYS[R_REV], 3 * 240.0 / 66)
    X.append({'v': 'REC', 'beat': B('pre'), 'dbeats': 3 * BPB + 1, 'm': 0, 'gain': 0.8, 'label': None, 'src': REC[R_REV]['file'], 'off': t0, 'rid': R_REV, 'fout': 1.2})
    for s in inside:
        for m in s['m']: X.append({'v': 'TB', 'beat': B('pre') + (s['t'] - t0) * 66 / 60.0, 'dbeats': s['d'] * 66 / 60.0, 'm': m, 'gain': 0.0, 'label': None})
        for k in range(3 * BPB):
            if s['t'] <= t0 + k * 60 / 66.0 + 0.05: P.harm[B('pre') + k] = s['ch']
    # ---- Rivoluzione — Introduzione: G7♭9 の強打と左手の奔流
    b0 = B('intro')
    P.section(starts['intro'], 'Rivoluzione — Allegro con fuoco (ハ短調)', '革命のエチュードの書法: 属和音 G7♭9 の強打と、左手の 16 分音符の奔流 — 音はすべて録音の 1 音')
    labs = ['G7'] * 4 + ['Dm7b5', 'G7'] + ['G7'] * 4 + ['Fm', 'G7', 'Dm7b5', 'G7', 'Cm', 'G7']
    set_harm(P, b0, labs)
    for crash in (b0, b0 + 8):
        for m in (79, 77, 74, 71, 68, 67): pf(crash, 1.5, m, 0.34, R_REV, rel=1.2)        # G7♭9 (A♭ を含む) の強打
        pf(crash, 1.5, 43, 0.3, LH_SRC['rev'], rel=1.2)
    for h, lab in enumerate(labs):
        if h in (0, 4): continue                                     # 強打のあいだは鳴り終わりを待つ
        rev_run(b0 + 2 * h, lab, 'C', LH_SRC['rev'], up_first=(h % 2 == 1))
    # ---- Rivoluzione — Tema: 右手のオクターヴの主題 (11:18 → 08:49)
    b0 = B('tema')
    P.section(starts['tema'], 'Rivoluzione — Tema 〈録音 %s · %s〉' % (hm(R_REV), hm(R_REV2)), '録音 11:18 と 08:49 の主題を右手のオクターヴで — 左手は駆け下り、駆け上がる')
    s1 = spans(rev, b0); s2 = spans(rev2, b0 + 16)
    labs = harmonize(s1, b0, 16, REV_C, first='Cm', last='G7') + harmonize(s2, b0 + 16, 16, REV_C, first='Cm', last='Cm')
    set_harm(P, b0, labs)
    rev_melody(s1, labs[:8], b0, R_REV, '主題 (11:18)'); rev_melody(s2, labs[8:], b0 + 16, R_REV2, '主題 (08:49)')
    for h, lab in enumerate(labs): rev_run(b0 + 2 * h, lab, 'C', LH_SRC['rev'], up_first=(h % 2 == 1), gain=0.17)
    # ---- Ponte: G7 → G#7
    b0 = B('ponte')
    P.section(starts['ponte'], 'Ponte — G7 → G♯7', '属和音を半音ずり上げて、嬰ハ短調 (幻想即興曲) へ')
    labs = ['G7', 'G7', 'G#7', 'G#7']; set_harm(P, b0, labs)
    for h, lab in enumerate(labs): rev_run(b0 + 2 * h, lab, 'C' if h < 2 else 'C#', LH_SRC['rev'], up_first=(h % 2 == 1), gain=0.2)
    for m in (80, 75, 72, 68): pf(b0 + 4, 3.5, m, 0.3, R_FI, rel=1.0)
    # ---- Fantaisie — Allegro agitato
    b0 = B('fi_intro')
    P.section(starts['fi_intro'], 'Fantaisie-Impromptu — Allegro agitato (嬰ハ短調)', '幻想即興曲の書法: 左手の 3 連符 (8 分音符 6 つ) に右手の 16 分音符 — 4 対 3 のポリリズム')
    labs = ['C#m', 'C#m', 'C#m', 'G#7']; set_harm(P, b0, labs)
    for h, lab in enumerate(labs): fi_lh(b0 + 2 * h, lab, LH_SRC['fi'])
    pf(b0 + 7, 1.0, 80, 0.35, R_FI, rel=0.6)                          # 右手の入りの G# の強打
    b0 = B('fi')
    P.section(starts['fi'], 'Fantaisie — Tema 〈録音 %s · %s〉' % (hm(R_FI), hm(R_FI2)), '録音 11:21 と 08:53 の主題が、右手の 16 分音符の拍の頭で歌う')
    s1 = spans(fi, b0); s2 = spans(fi2, b0 + 16)
    labs = harmonize(s1, b0, 16, FI_C, first='C#m', last='G#7') + harmonize(s2, b0 + 16, 16, FI_C, first='C#m', last='C#m')
    set_harm(P, b0, labs)
    fi_rh(s1, labs[:8], b0, 16, R_FI, '主題 (11:21)'); fi_rh(s2, labs[8:], b0 + 16, 16, R_FI2, '主題 (08:53)')
    for h, lab in enumerate(labs): fi_lh(b0 + 2 * h, lab, LH_SRC['fi'])
    b0 = B('fi_cad')
    labs = ['F#m', 'G#7', 'C#m', 'Ab7']; set_harm(P, b0, labs)                # A♭7 = G#7 (変ニ長調の属和音として)
    for h, lab in enumerate(labs): fi_lh(b0 + 2 * h, lab, LH_SRC['fi'])
    for k, m in enumerate([85, 80, 76, 73, 68, 64, 61, 56, 60, 63, 68, 72]): pf(b0 + k * 0.5, 0.45, m, 0.2, R_FI, rel=0.4)
    # ---- Moderato cantabile (変ニ長調)
    b0 = B('can')
    P.section(starts['can'], 'Moderato cantabile — 変ニ長調 〈録音 %s〉' % hm(R_CAN), '録音 11:23 の主題を長調にして歌う — 左手は広い分散和音')
    s1 = spans(can, b0); s2 = spans([(d, m + 12 if i % 2 else m) for i, (d, m) in enumerate(can)], starts['can2'] * BPB)
    labs = harmonize(s1, b0, 16, CAN_C, first='Db', last='Ab7') + harmonize(s1, b0, 16, CAN_C, first='Db', last='Db')
    set_harm(P, b0, labs)
    can_rh(s1, labs[:8], b0, R_CAN, '主題 (11:23)'); can_rh(spans(can, b0 + 16), labs[8:], b0 + 16, R_CAN, None)
    for h, lab in enumerate(labs): can_lh(b0 + 2 * h, lab, LH_SRC['can'])
    b0 = B('can2')
    P.section(starts['can2'], 'Moderato cantabile — 2 回目', '旋律がオクターヴを行き来し、内声が寄り添う')
    labs2 = harmonize(s2, b0, 16, CAN_C, first='Gb', last='Ab7') + harmonize(spans(can, b0 + 16), b0 + 16, 16, CAN_C, first='Db', last='Ab7')
    set_harm(P, b0, labs2)
    can_rh(s2, labs2[:8], b0, R_CAN, '主題 (11:23)')
    can_rh(spans(can, b0 + 16), labs2[8:], b0 + 16, R_CAN, None, gain=0.36)
    for h, lab in enumerate(labs2): can_lh(b0 + 2 * h, lab, LH_SRC['can'])
    # ---- Fantaisie — ripresa
    b0 = B('fi_rip')
    P.section(starts['fi_rip'], 'Fantaisie — ripresa (嬰ハ短調)', '幻想即興曲の奔流が戻る — 主題 (11:21) を 1 オクターヴ上で')
    s1 = spans([(d, m + 12) for d, m in fi], b0); s2 = spans(fi, b0 + 16)
    labs = harmonize(s1, b0, 16, FI_C, first='C#m', last='G#7') + harmonize(s2, b0 + 16, 16, FI_C, first='C#m', last='G#7')
    set_harm(P, b0, labs)
    fi_rh(s1, labs[:8], b0, 16, R_FI, '主題 (11:21)', gain=0.22); fi_rh(s2, labs[8:], b0 + 16, 16, R_FI, None)
    for h, lab in enumerate(labs): fi_lh(b0 + 2 * h, lab, LH_SRC['fi'])
    # ---- Coda: 革命の奔流で強奏
    b0 = B('coda')
    P.section(starts['coda'], 'Coda — Rivoluzione (嬰ハ短調)', '革命の左手の奔流が戻り、主題 (08:49) を右手のオクターヴで — 嬰ハ短調の強奏')
    s1 = spans(stretch(subject(R_REV2, -1), 2)[:6], b0)
    labs = harmonize(s1, b0, 16, FI_C, first='C#m', last='G#7') + ['C#m', 'C#m', 'G#7', 'C#m', 'G#7', 'C#m']
    set_harm(P, b0, labs)
    rev_melody(s1, labs[:8], b0, R_REV2, '主題 (08:49)')
    for h, lab in enumerate(labs[:10]): rev_run(b0 + 2 * h, lab, 'C#', LH_SRC['rev'], up_first=(h % 2 == 1), gain=0.19)
    for k, t in enumerate((b0 + 20, b0 + 22)):
        for m in ((73, 68, 64, 61) if k else (80, 75, 72, 68)): pf(t, 1.6, m, 0.34, R_FI, rel=1.0)
        pf(t, 1.6, 37 if k else 44, 0.3, LH_SRC['rev'], rel=1.0)
    # ---- Fine: 低音に歌の旋律が静かに戻る (嬰ハ長調)
    b0 = B('fine')
    P.section(starts['fine'], 'Fine — 嬰ハ長調', '幻想即興曲の終わりのように、カンタービレの旋律 (11:23) が低音で静かに戻り、嬰ハ長調で消える')
    labs = ['C#', 'C#', 'F#', 'C#', 'G#7', 'C#', 'C#', 'C#']; set_harm(P, b0, labs)
    for h, lab in enumerate(labs[:6]):
        c = chord(lab)
        for pc, tg in ((c['root'], 61), (c['third'], 65), (c['fifth'], 68)): pf(b0 + 2 * h, 1.9, near(pc, tg), 0.12, R_CAN, rel=1.2)
    for t, d, m in spans([(d, m - 24) for d, m in can[:4]], b0): pf(t, d * 0.98, m, 0.3, R_CAN, '主題 (11:23)', rel=1.0)
    for m in (49, 56, 61, 65, 68, 73): pf(b0 + 12, 4.0, m, 0.16, R_CAN, rel=2.5)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [R_REV, R_REV2, R_FI, R_FI2, R_CAN],
    'title': 'Fantaisie-Révolution — Tablet Sessions',
    'subtitle': '録音 5 本 (09-24) を、ショパンの革命のエチュードと幻想即興曲の書法でリメイク (音はすべて録音から)',
    'footer': ['Preludio (11:18 の実音) → Rivoluzione (ハ短調) → G7 → G♯7 → Fantaisie (嬰ハ短調) → Moderato cantabile (変ニ長調) → ripresa → Coda → Fine (嬰ハ長調)',
               '旋律は各録音の最上声から作った主題。革命: 左手の 16 分音符の奔流と右手のオクターヴ、幻想即興曲: 左手の 3 連符と右手の 16 分音符 (4 対 3)。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_chopin.json'
    compose.main(out, seed=59, bpm=144, builder=build, meta=META, extras=X)
    print('notes', sum(1 for e in X if e['v'] == 'PF'))
