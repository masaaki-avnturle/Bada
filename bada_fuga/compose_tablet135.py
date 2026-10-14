#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXV · Missa pro defunctis nel palazzetto (10/13 の 2 曲をベースに、ミサ曲 — 死者のためのミサ — をベースと主題にして)
  10/13 06:41・06:42 の実音 (半音上げてロ短調に) の雰囲気 (冷たい空気の体育館、礼拝) の上に、ミサの形と主題を重ねる:
    Introitus  (ロ短調, ♩=56)  06:41 の実音。グレゴリオ聖歌「Requiem aeternam」(ロ短調に) を 4 声のユニゾンで、高い開いた 5 度の弦、コントラバスの保続、深い鐘
    Kyrie      (ロ短調)        06:42 の実音の上で、06:41 の音から作った主題 (CXXV の Inno の第 1 句) のフーガ: 提示 (A → S → B → T) → Christe (反行) → ストレッタ
    Dies irae  (ロ短調)        続唱「Dies irae」の頭 (レ・ド#・レ・シ・ド#・ラ・シ・シ、ロ短調に) のフガート — 4 声と弦、トロンボーン・ホルンの拡大、ティンパニが高まる
    Sanctus    (ニ長調)        06:42 の音から作った旋律を讃美歌のリズムで、4 声のコラール (Sanctus) → Hosanna は高い開いた 5 度とフルート
    Agnus Dei  (ロ短調)        B-A-D-A の唱え (アルト) に「Requiem aeternam」がソプラノに重なる、バスの保続、深い鐘
    Lux aeterna (ニ長調 → ロ短調)  06:41 の実音、ホルンが「Requiem aeternam」の頭、高い開いた 5 度、ニ長調の和音、深い鐘
  旋律: Requiem aeternam (Introitus)・Dies irae はグレゴリオ聖歌 (パブリックドメイン)。Kyrie・Sanctus の主題は 10/13 の録音の最上声の音から
  使い方: BANK1013=<bank1013.json> SCORE89=<score_tablet89.json> python compose_tablet135.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet135.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet135.json'
sys.argv = sys.argv[:6] + ['/dev/null']
import compose_tablet127 as T
from compose import *
import compose
import compose_heart as H
RECS, R41, R42, WDIR, RATE, PSRC, GMAJ = T.RECS, T.R41, T.R42, T.WDIR, T.RATE, T.PSRC, T.GMAJ
extras, RH, add, entry, harm_fit, rest_others, invert, augment, aphrase = T.extras, T.RH, T.add, T.entry, T.harm_fit, T.rest_others, T.invert, T.augment, T.aphrase
CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'F#', 'F#7', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4', 'C#m7b5']
CANDS_D = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m', 'D/F#', 'G/B', 'A/C#', 'Em7', 'Asus4', 'Bm/D', 'D/A', 'G/D']
BPM = 56
INTRO, KYRIE, DIES, SANCTUS, AGNUS, LUX, TOTAL = 0, 24, 64, 104, 136, 164, 190
REQ = [(d, m - 3) for d, m in H.REQUIEM_CHANT]                                                     # Requiem aeternam (ニ短調 → ロ短調: レ・レ・ミ・レ・ド#・シ・レ・ミ・ファ#・ミ・レ・ド#・シ)、24 拍
DIES_T = [(1, 62), (1, 61), (1, 62), (1, 59), (1, 61), (1, 57), (2, 59), (1, 59)]                   # Dies irae の頭 (ファ・ミ・ファ・レ・ミ・ド・レ・レ → ロ短調に)、9 拍
KYRIE_T = aphrase(0)                                                                               # 10/13 06:41 の音から (CXXV の Inno の第 1 句)、14 拍
def tune_from(rid, lo=62, hi=79, rhythm=(1, 1, 1, 1, 2, 2), ends=((74, 78), (76, 71), (74, 78), (74, 74))):
    """録音の最上声の音 (+1 でロ短調/ニ長調に、五音音階に寄せる) を讃美歌のリズムに — 4 句、各句の終わりは長い音"""
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + 1
        if sg['d'] < 0.4: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * 4; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(4):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph], key=lambda x: abs(x - out[i][1])))
    return out
SANCTUS_T = tune_from(R42)                                                                         # 06:42 の音から (ニ長調)、8 拍 × 4 句
def sphrase(k): return SANCTUS_T[6 * k: 6 * k + 6]
BADA = [(d, m + 1) for d, m in H.BADA]
SAN_RH = ['D', 'G', 'D', 'A', 'Bm', 'G', 'D', 'A', 'D', 'G', 'A', 'D', 'G', 'A', 'D', 'D']                 # Sanctus の和声の下書き (小節ごと)
PLAYS = [(R41, 1, 0.45, 1), (R42, KYRIE + 1, 0.4, 1), (R41, LUX + 1, 0.4, 1)]
OG = 0.34
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = 'D' if (SANCTUS <= q // BPB < AGNUS or LUX <= q // BPB < TOTAL - 6) else 'Bm'
        if SANCTUS + 2 <= q // BPB < SANCTUS + 18: cur = SAN_RH[q // BPB - SANCTUS - 2]                   # Sanctus の和声の下書き
        RH.append(cur); P.harm[q] = cur
    # Introitus
    P.section(INTRO, 'Introitus — Requiem aeternam (ロ短調, ♩=56)', '10/13 06:41 の実音 (半音上げて) の上で、グレゴリオ聖歌「Requiem aeternam」をロ短調で 4 声のユニゾンに — 高い開いた 5 度の弦が pp、コントラバスの保続、深い鐘')
    rest_others(P, INTRO, INTRO + 6, ''); E = []
    for k, (b, tr) in enumerate(((INTRO + 6, 0), (INTRO + 14, 0))):
        for v in VOICES: entry(P, b, v, REQ, tr + (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Requiem aeternam (ユニゾン)' if k == 0 else 'Requiem aeternam (2 度目)') if v == 'S' else None, E)
    for v in VOICES: P.rest_bars(v, INTRO + 12, INTRO + 14); P.rest_bars(v, INTRO + 20, KYRIE)
    for q in range(INTRO * BPB, KYRIE * BPB): P.harm[q] = 'Bm'
    # Kyrie (フーガ)
    P.section(KYRIE, 'Kyrie — フーガ (ロ短調)', '06:42 の実音 (半音上げて) の上で、06:41 の音から作った主題のフーガ: 提示 (アルト → ソプラノ 答唱 → バス → テノール 答唱) → Christe (反行、2 声) → Kyrie (ストレッタ)')
    f = KYRIE + 2; E = []; rest_others(P, KYRIE, f, '')
    for k, v in enumerate('ASBT'):
        entry(P, f + 4 * k, v, KYRIE_T, 7 if k % 2 else 0, 'Kyrie — 主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 4 * k, f + 4 * (k + 1))
    harm_fit(P, KYRIE, f + 16, E, CANDS_BM); f += 16; E = []
    for k in range(2):
        entry(P, f + 4 * k, 'SA'[k], invert(KYRIE_T), 0, 'Christe (反行)' if k == 0 else None, E)
        for w in VOICES:
            if w != 'SA'[k]: P.rest_bars(w, f + 4 * k, f + 4 * k + 4)
        P.place('TB'[k], f + 4 * k, [(4, 47 - 12 * k)] * 4, 0, None)
    harm_fit(P, f, f + 8, E, CANDS_BM); f += 8; E = []
    for k, v in enumerate('ASTB'): entry(P, f + k, v, KYRIE_T, 0, 'Kyrie — ストレッタ' if k == 0 else None, E)
    harm_fit(P, f, DIES, E, CANDS_BM); P.hold.update(range(f + 6, DIES)); rest_others(P, DIES - 2, DIES, '')
    # Dies irae
    P.section(DIES, 'Dies irae — フガート (ロ短調)', '続唱「Dies irae」の頭 (レ・ド#・レ・シ・ド#・ラ・シ・シ) が 4 声と弦に追いかけ、トロンボーンとホルンの拡大 (×2)、ティンパニが高まる — 最後は 4 声のユニゾンで')
    f = DIES + 1; E = []; rest_others(P, DIES, f, '')
    for k, v in enumerate('BTAS'):
        entry(P, f + 3 * k, v, DIES_T, 7 if k % 2 else 0, 'Dies irae — 主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'BTAS'[k + 1:]: P.rest_bars(w, f + 3 * k, f + 3 * (k + 1))
    harm_fit(P, DIES, f + 12, E, CANDS_BM); f += 12; E = []
    for k, v in enumerate('SATB'): entry(P, f + 2 * k, v, invert(DIES_T), 0, 'Dies irae (反行)' if k == 0 else None, E)
    harm_fit(P, f, f + 10, E, CANDS_BM); f += 10; E = []
    for k, v in enumerate('ASTB'): entry(P, f + k, v, DIES_T, 0, 'ストレッタ' if k == 0 else None, E)
    harm_fit(P, f, f + 8, E, CANDS_BM); f += 8; E = []
    for v in VOICES: entry(P, f, v, augment(DIES_T), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), 'Dies irae — ユニゾン (拡大)' if v == 'S' else None, E)
    harm_fit(P, f, SANCTUS, E, CANDS_BM); P.hold.update(range(f + 5, SANCTUS)); rest_others(P, f + 5, SANCTUS, '')
    # Sanctus
    P.section(SANCTUS, 'Sanctus — コラール (ニ長調)', '06:42 の音から作った旋律を讃美歌のリズムで、4 声のコラールに (Sanctus, Sanctus, Sanctus) — Hosanna は高い開いた 5 度とフルート、弦の和音')
    E = []; rest_others(P, SANCTUS, SANCTUS + 2, '')
    for k in range(4):
        b = SANCTUS + 2 + 4 * k + (2 if k >= 2 else 0)
        entry(P, b, 'S', sphrase(k), 0, 'Sanctus 第 %d 句' % (k + 1), E)
        for v in 'ATB': P.rest_bars(v, b + 2, b + 4) if k < 3 else None
    P.hold.update(range(SANCTUS + 2, AGNUS)); harm_fit(P, SANCTUS + 2, SANCTUS + 22, E, CANDS_D)
    for q in range((SANCTUS + 22) * BPB, AGNUS * BPB): P.harm[q] = 'D'
    for v in 'ATB': P.rest_bars(v, SANCTUS + 22, AGNUS)
    P.place('S', SANCTUS + 22, [(4, 81)] * 4, 0, 'Hosanna (高いラ)'); P.rest_bars('S', SANCTUS + 26, AGNUS)
    # Agnus Dei
    P.section(AGNUS, 'Agnus Dei — B-A-D-A (ロ短調)', 'B-A-D-A の唱え (アルト) に、「Requiem aeternam」がソプラノに重なる — バスの保続 (シ)、低い弦の和音、深い鐘')
    rest_others(P, AGNUS, AGNUS + 2, ''); E = []
    for k in range(6):
        bb = AGNUS + 2 + 4 * k
        P.place('A', bb, BADA, 0, 'B-A-D-A' if k == 0 else None); E.append((bb * BPB, [(d, m) for d, m in BADA]))
        if k in (1, 3): entry(P, bb, 'S', REQ, 0, 'Requiem aeternam' if k == 1 else None, E)
        elif k not in (2, 4): P.rest_bars('S', bb, bb + 4)
        P.rest_bars('T', bb, bb + 4); P.place('B', bb, [(4, 47)] * 4, 0, 'バスの保続' if k == 0 else None)
    P.hold.update(range(AGNUS + 2, LUX)); harm_fit(P, AGNUS + 2, AGNUS + 26, E, CANDS_BM); rest_others(P, AGNUS + 26, LUX, '')
    # Lux aeterna
    P.section(LUX, 'Lux aeterna — 光 (ニ長調 → ロ短調)', '06:41 の実音、ホルンが「Requiem aeternam」の頭、高い開いた 5 度の弦、ニ長調の和音 (レ・ラ・ファ#) — 最後はロ短調の冷たい空気に戻り、深い鐘')
    rest_others(P, LUX, TOTAL, '')
    for b in range(LUX + 14, LUX + 20): P.set_harm(b, 'D'); P.hold.add(b)
    P.place('S', LUX + 14, [(4, 78)] * 6, 0, 'ニ長調 (レ・ラ・ファ#)'); P.place('A', LUX + 14, [(4, 74)] * 6, 0, ''); P.place('T', LUX + 14, [(4, 69)] * 6, 0, ''); P.place('B', LUX + 14, [(4, 50)] * 6, 0, '')
    for q in range((LUX + 20) * BPB, TOTAL * BPB): P.harm[q] = 'Bm'
    return P

def line(v, bar, mat, tr, g, label=None, beat=0):
    t = bar * BPB + beat; first = True
    for d, m in mat:
        oadd(v, t, d, m + tr, g, label if first else None); first = False; t += d
def chord_pad(P, b0, b1, parts, g, label=None):
    q = b0 * BPB; first = True
    while q < b1 * BPB:
        h = P.harm[q]; q1 = q
        while q1 < b1 * BPB and P.harm[q1] == h: q1 += 1
        c = chord(h)
        for v, lo, hi in parts:
            tones = sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
            for i, m in enumerate(tones[:3] if v != 'CB' else [min(tones)]): oadd(v, q + 0.03 * i, (q1 - q) + 0.3, m if v != 'CB' else m - 12, g * (1.0 if i == 0 else 0.8), label if (first and i == 0) else None); first = False
        q = q1
def fifths(b0, b1, g, label):
    for b in range(b0, b1, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, g, label if b == b0 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, g * 0.85); oadd('VA', b * BPB + 0.1, 4 * BPB + 0.5, 71, g * 0.7)
        oadd('CB', b * BPB, 4 * BPB + 0.5, 35, g * 1.5, 'コントラバスの保続 (シ)' if b == b0 else None)

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 1 else 0.02, fout=5.0, semis=sm, rid=rid + '.wav', tag='10/13 %s — 実音 (半音上げてロ短調に)' % ('06:41' if rid == R41 else '06:42'))
    # Introitus
    fifths(INTRO + 1, KYRIE - 3, 0.14, '高い開いた 5 度 (Vn, pp)')
    # Kyrie: 弦が主題を追いかける (提示のあと)
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, KYRIE + 20 + 2 * k, KYRIE_T, tr + (7 if k % 2 else 0), 0.22, '弦 — Kyrie の主題' if k == 0 else None)
    chord_pad(P, KYRIE + 18, DIES, [('VA', 50, 64), ('CB', 43, 55)], 0.1)
    # Dies irae: 弦のフガート、金管の拡大、ティンパニ
    for k, (v, tr) in enumerate((('VC', -24), ('VA', -12), ('V2', 0), ('V1', 12))): line(v, DIES + 2 + 3 * k, DIES_T, tr + (7 if k % 2 else 0), 0.26, '弦のフガート (Vc → Va → Vn II → Vn I)' if k == 0 else None)
    line('TB', DIES + 14, augment(DIES_T), -24, 0.3, 'トロンボーン — Dies irae の拡大 (×2)'); line('HN', DIES + 14, augment(DIES_T), -12, 0.26)
    line('TB', DIES + 24, augment(DIES_T), -12, 0.3, None); line('HN', DIES + 24, augment(DIES_T), 0, 0.26, None); line('TR', DIES + 31, DIES_T, 12, 0.26, 'トランペット — 頭')
    for k, b in enumerate(range(DIES + 8, SANCTUS - 2, 3)): oadd('TP', b * BPB, 2.0, 35 if k % 2 == 0 else 42, 0.28 + 0.03 * k, 'ティンパニ' if k == 0 else None)
    for i in range(8): oadd('TP', (SANCTUS - 2) * BPB + i * 0.5, 0.5, 35, 0.25 + 0.04 * i, None)
    chord_pad(P, DIES + 12, SANCTUS - 2, [('VA', 50, 64), ('VC', 43, 55), ('CB', 43, 55)], 0.16)
    # Sanctus: 弦の和音、Hosanna
    chord_pad(P, SANCTUS + 2, SANCTUS + 22, [('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)], 0.16, 'Vn II・Va・Vc の和音')
    for b in range(SANCTUS + 22, AGNUS - 2, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 93, 0.16, 'Hosanna — 高い開いた 5 度 (Vn, Fl)' if b == SANCTUS + 22 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 86, 0.14); oadd('FL', b * BPB + 0.1, 4 * BPB + 0.5, 98, 0.1); oadd('CB', b * BPB, 4 * BPB + 0.5, 38, 0.2)
    # Agnus Dei: 低い弦の和音、鐘
    chord_pad(P, AGNUS + 2, LUX, [('VA', 50, 64), ('VC', 43, 55)], 0.14, 'Va・Vc の和音')
    for b in range(AGNUS + 2, LUX - 2, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.2, None)
    add('X', AGNUS * BPB, 12, 35, 0.3, '深い鐘')
    # Lux aeterna: ホルンの頭、高い 5 度、ニ長調
    line('HN', LUX + 4, REQ[:8], 0, 0.22, 'ホルン — Requiem aeternam の頭'); line('HN', LUX + 9, REQ[:8], -12, 0.18, None)
    fifths(LUX + 1, LUX + 13, 0.12, '高い開いた 5 度 (Vn, pp)')
    chord_pad(P, LUX + 14, LUX + 20, [('V1', 74, 86), ('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55), ('CB', 43, 55)], 0.18, 'ニ長調の和音 (弦)')
    oadd('FL', (LUX + 14) * BPB, 6 * BPB, 90, 0.12, 'フルート')
    fifths(LUX + 20, TOTAL - 2, 0.1, '冷たい空気に戻る (高い 5 度)')
    # 共鳴 (13:19 の音): 高い開いた 5 度を Introitus と Lux aeterna に小さく
    first = True
    for b in list(range(INTRO + 2, KYRIE - 4, 4)) + list(range(LUX + 2, TOTAL - 4, 4)):
        for i, m in enumerate((83, 90)): add('PF', b * BPB + 0.05 * i, 4 * BPB, m, 0.5 * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 35, 0.4, None)

META = dict(T.META, orchestra=True, rec_order=[R41, R42], reverb=[8.0, 3.0, 0.5],
            title='Requiem BADA — CXXXV · Missa pro defunctis nel palazzetto',
            subtitle='10/13 の 2 曲 (半音上げてロ短調に) をベースに、ミサ曲 (死者のためのミサ) をベースと主題にして: Introitus (Requiem aeternam、06:41) → Kyrie (10/13 の主題のフーガ、06:42) → Dies irae (続唱の頭のフガート、金管、ティンパニ) → Sanctus (コラール、Hosanna) → Agnus Dei (B-A-D-A) → Lux aeterna (06:41、ニ長調の和音、深い鐘)。ロ短調、♩=56',
            legend=['PF', 'X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'HN', 'TR', 'TB', 'TP'], vname={'PF': '共鳴 (13:19 の音)', 'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
            footer=['主題: Requiem aeternam (Introitus) と Dies irae はグレゴリオ聖歌 (パブリックドメイン、ロ短調に)。Kyrie の主題は 10/13 06:41 の音 (CXXV の Inno の第 1 句)、Sanctus の旋律は 06:42 の音から。B-A-D-A',
                    '4 声は実音のピアノ (9/24 08:53 の音)。管弦楽は synth の合成。10/13 の実音は Introitus・Kyrie・Lux aeterna に。鐘は始め・Agnus Dei・終わりに深いもの。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    print('kyrie', ' '.join('%s:%g' % (name_of(m), d) for d, m in KYRIE_T), '| sanctus', ' '.join('%s:%g' % (name_of(m), d) for d, m in SANCTUS_T[:6]))
    compose.main(OUT, seed=135, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
