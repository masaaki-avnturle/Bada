#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXIII · Stille Nacht — Requiem nel palazzetto (きよしこの夜の聖歌を、10/13 の 2 曲の雰囲気 — 冷たい空気の体育館、礼拝 — の上で、requiem の雰囲気に被せて)
  旋律: Stille Nacht (Franz Xaver Gruber、1818 年、パブリックドメイン) — 6/8 を 3/4 (♩ = 8 分音符 2 つ) で書く、24 小節。ニ長調 (10/13 の録音を半音上げたロ短調の平行長調) で、実音のピアノ (9/24 08:53 の音) が歌う
    I.   Introitus (ロ短調, ♩=60)       10/13 06:41 の実音 (半音上げて)。高い開いた 5 度の弦が pp、コントラバスの保続、ホルンが Stille Nacht の頭をロ短調で。B-A-D-A の唱えが静かに
    II.  Stille Nacht I (ニ長調)        実音のピアノの 4 声で、聖歌として (ソプラノが旋律、ほかの声部は和音から) — 弦の和音が薄く
    III. Kyrie (ロ短調)                 06:42 の実音の上で、頭 (ファ#・ソ・ファ#・レ) をロ短調の主題にしたフガート — 4 声と弦が追いかける (反行も)
    IV.  Stille Nacht II (ニ長調)       Vn I とフルートが旋律に重なり、Vc・Cb が根音
    V.   Agnus Dei (ロ短調)             B-A-D-A の唱え (アルト) に、Stille Nacht の句がロ短調でソプラノに重なる。バスの保続
    VI.  Lux aeterna — Stille Nacht III (ニ長調)  総奏: ホルンが旋律、トロンボーンが根音、弦と木管、4 声 — 最後の「Sleep in heavenly peace」はユニゾンで。Amen (ソ → レ)
    VII. Coda (ロ短調)                  06:41 の実音、高い開いた 5 度、ホルンの頭、深い鐘
  使い方: BANK1013=<bank1013.json> SCORE89=<score_tablet89.json> python compose_tablet133.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet133.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet133.json'
sys.argv = sys.argv[:6] + ['/dev/null']
import compose
compose.BPB = 3                                                                                    # 3/4 (= 6/8、♩ が 8 分音符 2 つ)
import compose_heart as H
import compose_tablet128 as T
from compose import *
BPB = 3
RECS, R41, R42, WDIR, RATE = T.RECS, T.R41, T.R42, T.WDIR, T.RATE
PSRC, octs, TOP, fit = T.T.PSRC, T.T.octs, T.T.TOP, T.T.fit
GMAJ = T.T.GMAJ
CANDS_D = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m', 'D/F#', 'G/B', 'A/C#', 'Em7', 'Asus4', 'Bm/D', 'D/A', 'G/D']
CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'F#', 'F#7', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4', 'C#m7b5']
BPM = 60
INTRO, SN1, KYRIE, SN2, AGNUS, SN3, CODA, TOTAL = 0, 24, 50, 80, 106, 130, 157, 181
AG1, INNO, AG2, FUGA, AG3 = SN1, KYRIE, SN2, AGNUS, SN3
SN_BARS = 24
# Stille Nacht (ハ長調で書いて、+2 でニ長調に): 3/4 (= 6/8)、(拍, MIDI)、24 小節、1 拍目から
SN_C = [(1.5, 67), (0.5, 69), (1, 67), (3, 64), (1.5, 67), (0.5, 69), (1, 67), (3, 64),
        (2, 74), (1, 74), (3, 71), (2, 72), (1, 72), (3, 67),
        (2, 69), (1, 69), (1.5, 72), (0.5, 71), (1, 69), (1.5, 67), (0.5, 69), (1, 67), (3, 64),
        (2, 69), (1, 69), (1.5, 72), (0.5, 71), (1, 69), (1.5, 67), (0.5, 69), (1, 67), (3, 64),
        (2, 74), (1, 74), (1.5, 77), (0.5, 74), (1, 71), (3, 72), (3, 76),
        (1, 72), (1, 67), (1, 64), (1.5, 67), (0.5, 65), (1, 62), (3, 60), (3, 60)]
AG = [(d, m + 2) for d, m in SN_C]                                                                 # ニ長調 (レ 4 〜 ソ 5)
assert abs(sum(d for d, _ in AG) - 72) < 1e-9
SN_RH = ['D', 'D', 'D', 'D', 'A', 'A', 'D', 'D', 'G', 'G', 'D', 'D', 'G', 'G', 'D', 'D', 'A', 'A', 'D', 'D', 'D', 'A', 'D', 'D']   # 聖歌の和声の下書き (小節ごと)
HEAD_BM = [(1.5, 66), (0.5, 67), (1, 66), (3, 62), (1.5, 66), (0.5, 67), (1, 66), (3, 62)]           # 頭をロ短調に (ファ#・ソ・ファ#・レ、2 度)、12 拍
INV_BM = [(1.5, 66), (0.5, 64), (1, 66), (3, 69), (1.5, 66), (0.5, 64), (1, 66), (3, 69)]            # 反行 (音階の中で: ファ#・ミ・ファ#・ラ)
BADA3 = [(3, m + 1) for _, m in H.BADA]                                                           # B-A-D-A (+1、ロ短調)、1 音 1 小節
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def inno_tune():
    """10/13 06:41 の最上声の音 (+1 でロ短調に、五音音階に寄せ、シ 3〜ファ# 5 に) を 3/4 の讃美歌のリズム (𝅗𝅥 ♩ 𝅗𝅥 ♩ ♩ ♩ ♩ 𝅗𝅥. × 4 句、各句 4 小節) に"""
    tops = []
    for sg in RECS[R41]['segs']:
        m = sg['m'][-1] + 1
        if sg['d'] < 0.4: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < 59: m += 12
        while m > 78: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < 59: m += 12
        while m > 78: m -= 12
        tops.append(m)
    rhythm = [2, 1, 2, 1, 1, 1, 1, 3] * 4; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rhythm)]
    for ph in range(4):
        i = ph * 8 + 7; target = {0: (74, 71), 1: (76, 78), 2: (74, 71), 3: (71, 71)}[ph]
        out[i] = (3, min(target, key=lambda x: abs(x - out[i][1])))
    return out
INNO_T = inno_tune()
def iphrase(k): return INNO_T[8 * k: 8 * k + 8]
PLAYS = [(R41, 1, 0.45, 1), (R42, KYRIE + 1, 0.4, 1), (R41, CODA + 1, 0.4, 1)]
AG_RH = SN_RH                      # (録音, 小節, 大きさ, テープの移調)

extras = []; RH = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
OG = 0.34
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)
def harm_fit(P, b0, b1, entries, cands):
    """小節ごと (3 拍) に、旋律の音を含み、録音の和音 (RH) に近い和音を選ぶ。3 拍目の音が合わなければ 3 拍目だけ別の和音"""
    def notes_in(a, w):
        notes = []
        for e0, sb in entries:
            t = e0
            for d, m in sb:
                ov = min(a + w, t + d) - max(a, t)
                if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                t += d
        return notes
    def pick(a, w, prefer=None):
        notes = notes_in(a, w); rc = set(chord(RH[a])['pcs'])
        def score(c):
            cc = set(chord(c)['pcs'])
            return sum(wt * (1 if m % 12 in cc else -0.8) for wt, m in notes) + 1.5 * len(cc & rc) / max(1, len(cc)) + (1.2 if c == RH[a] else 0) + (1.0 if c == prefer else 0)
        return max(cands, key=score), notes
    for bar in range(b0, b1):
        a = bar * BPB; cs, _ = pick(a, 2)
        P.harm[a] = P.harm[a + 1] = cs
        c3, n3 = pick(a + 2, 1, prefer=cs)
        P.harm[a + 2] = cs if all(m % 12 in chord(cs)['pcs'] for _, m in n3) else c3
def entry(P, bar, v, mat, tr0, label, E, beat=0):
    tr = fit(v, mat, octs[v] + tr0); P.place(v, bar, mat, tr, label or '', beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))
def rest_others(P, b0, b1, keep):
    for v in VOICES:
        if v not in keep: P.rest_bars(v, b0, b1)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):                                                                    # 録音の和音 (半音上げて) を RH に、なければ段落の調
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = 'D' if (SN1 <= q // BPB < KYRIE or SN2 <= q // BPB < AGNUS or SN3 <= q // BPB < CODA) else 'Bm'
        for b0 in (AG1, AG2, AG3):
            if b0 + 1 <= q // BPB < b0 + 1 + SN_BARS: cur = AG_RH[q // BPB - b0 - 1]
        RH.append(cur); P.harm[q] = cur
    # I. Introitus (4 声は B-A-D-A の唱えだけ)
    P.section(INTRO, 'I. Introitus — 冷たい空気 (ロ短調, ♩=60)', '10/13 06:41 の実音 (半音上げて、小さく) — 高い開いた 5 度 (シ・ファ#) の弦が pp、コントラバスの保続 (シ)、ホルンが Stille Nacht の頭をロ短調で静かに。B-A-D-A の唱え (アルト) が静かに')
    rest_others(P, INTRO, SN1, 'A'); P.rest_bars('A', INTRO, INTRO + 10); P.rest_bars('A', INTRO + 18, SN1)
    for k in range(2): P.place('A', INTRO + 10 + 4 * k, BADA3, -12, 'B-A-D-A (唱え)' if k == 0 else None)
    for q in range(INTRO * BPB, SN1 * BPB): P.harm[q] = 'Bm'
    # II. Stille Nacht I (実音のピアノの 4 声、聖歌として)
    P.section(SN1, 'II. Stille Nacht I — 聖歌 (ニ長調)', 'きよしこの夜 (Gruber、1818 年、パブリックドメイン) を実音のピアノの 4 声で: ソプラノが旋律、ほかの声部は旋律の音を含むニ長調の和音から — 弦の和音が薄く')
    E = []; rest_others(P, SN1, SN1 + 1, ''); entry(P, SN1 + 1, 'S', AG, 0, 'Stille Nacht (ソプラノ)', E)
    harm_fit(P, SN1 + 1, SN1 + 1 + SN_BARS, E, CANDS_D)
    for b in (SN1 + 25,): P.set_harm(b, 'D'); P.hold.add(b)
    P.hold.update(range(SN1 + 1, SN1 + 25)); P.rest_bars('S', SN1 + 25, KYRIE)
    # III. Kyrie (頭のフガート)
    P.section(KYRIE, 'III. Kyrie — 頭のフガート (ロ短調)', '06:42 の実音 (半音上げて) の上で、頭 (ファ#・ソ・ファ#・レ) をロ短調の主題にして、アルト → ソプラノ (答唱) → バス → テノール、弦も Vn I → Vn II → Va → Vc と追いかける (後半は反行)')
    E = []; rest_others(P, KYRIE, KYRIE + 2, '')
    for k, v in enumerate('ASBT'):
        entry(P, KYRIE + 2 + 4 * k, v, HEAD_BM, 7 if k % 2 else 0, 'Kyrie — 主題 (Stille Nacht の頭、ロ短調)' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, KYRIE + 2 + 4 * k, KYRIE + 2 + 4 * (k + 1))
    for k, v in enumerate('STAB'):
        entry(P, KYRIE + 18 + 2 * k, v, INV_BM, 0 if k % 2 == 0 else 7, '反行' if k == 0 else None, E)
    harm_fit(P, KYRIE + 2, SN2, E, CANDS_BM); rest_others(P, SN2 - 2, SN2, '')
    # IV. Stille Nacht II
    P.section(SN2, 'IV. Stille Nacht II — 弦と木管が重なる (ニ長調)', 'Vn I とフルート (1 オクターヴ上) が旋律に重なり、Vn II・Va が和音、Vc・Cb が根音 — 実音のピアノの 4 声の聖歌はそのまま')
    E = []; rest_others(P, SN2, SN2 + 1, ''); entry(P, SN2 + 1, 'S', AG, 0, 'Stille Nacht (ソプラノ、弦と)', E)
    harm_fit(P, SN2 + 1, SN2 + 1 + SN_BARS, E, CANDS_D)
    for b in (SN2 + 25,): P.set_harm(b, 'D'); P.hold.add(b)
    P.hold.update(range(SN2 + 1, SN2 + 25)); P.rest_bars('S', SN2 + 25, AGNUS)
    # V. Agnus Dei (B-A-D-A の唱えに、頭がロ短調で重なる)
    P.section(AGNUS, 'V. Agnus Dei — B-A-D-A (ロ短調)', 'B-A-D-A の唱え (アルト) に、Stille Nacht の頭がロ短調でソプラノに重なる。バスの保続 (シ)、深い鐘')
    E = []; rest_others(P, AGNUS, AGNUS + 2, '')
    for k in range(5):
        bb = AGNUS + 2 + 4 * k
        P.place('A', bb, BADA3, 0, 'B-A-D-A' if k == 0 else None); E.append((bb * BPB, [(d, m) for d, m in BADA3]))
        if k % 2 == 1: entry(P, bb, 'S', HEAD_BM, 0, 'Stille Nacht の頭 (ロ短調)' if k == 1 else None, E)
        else: P.rest_bars('S', bb, bb + 4)
        P.rest_bars('T', bb, bb + 4); P.place('B', bb, [(3, 47)] * 4, 0, 'バスの保続' if k == 0 else None)
    P.hold.update(range(AGNUS + 2, SN3)); harm_fit(P, AGNUS + 2, AGNUS + 22, E, CANDS_BM); rest_others(P, AGNUS + 22, SN3, '')
    for q in range((AGNUS + 22) * BPB, SN3 * BPB): P.harm[q] = 'Bm'
    # VI. Lux aeterna — Stille Nacht III (総奏)
    P.section(SN3, 'VI. Lux aeterna — Stille Nacht III (ニ長調)', '総奏: ホルンが旋律、トロンボーン・Vc・Cb が根音、弦と木管、実音のピアノの 4 声 — 最後の「Sleep in heavenly peace」は 4 声のユニゾンで。Amen (ソ → レ)')
    E = []; rest_others(P, SN3, SN3 + 1, ''); entry(P, SN3 + 1, 'S', AG, 0, 'Stille Nacht (ソプラノ、総奏)', E)
    for v in 'ATB':
        P.rest_bars(v, SN3 + 21, SN3 + 25); P.place(v, SN3 + 21, AG[-8:], {'A': -12, 'T': -24, 'B': -36}[v], 'ユニゾン' if v == 'A' else '')
    harm_fit(P, SN3 + 1, SN3 + 1 + SN_BARS, E, CANDS_D)
    for q in range((SN3 + 21) * BPB, (SN3 + 25) * BPB): P.harm[q] = 'D' if P.harm[q] not in ('D', 'G', 'A', 'A7', 'D/F#', 'D/A') else P.harm[q]
    P.hold.update(range(SN3 + 1, SN3 + 21))
    P.set_harm(SN3 + 25, 'G'); P.set_harm(SN3 + 26, 'D'); P.hold.update({SN3 + 25, SN3 + 26})
    P.place('S', SN3 + 25, [(3, 79), (3, 78)], 0, 'Amen (ソ → レ)'); P.place('A', SN3 + 25, [(3, 71), (3, 69)], 0, ''); P.place('T', SN3 + 25, [(3, 67), (3, 66)], 0, ''); P.place('B', SN3 + 25, [(3, 43), (3, 38)], 0, '')
    # VII. 結尾
    P.section(CODA, 'VII. Coda — 冷たい空気に戻る (ロ短調)', '06:41 の実音、高い開いた 5 度の弦、ホルンの頭 — 深い鐘がひとつ')
    rest_others(P, CODA, TOTAL, '')
    for q in range(CODA * BPB, TOTAL * BPB): P.harm[q] = 'Bm'
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
def roots(P, b0, b1, parts, g, label=None):
    """小節ごとの根音を Vc・Cb (・トロンボーン) で"""
    first = True
    for b in range(b0, b1):
        c = chord(P.harm[b * BPB]); r = 38 + c['root']
        for v, tr in parts: oadd(v, b * BPB, BPB + 0.2, r + tr, g, label if first else None); first = False

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 1 else 0.02, fout=5.0, semis=sm, rid=rid + '.wav', tag='10/13 %s — 実音 (半音上げてロ短調に)' % ('06:41' if rid == R41 else '06:42'))
    # I. Introitus: 高い 5 度、保続、ホルンの頭
    for b in range(INTRO + 1, SN1 - 1, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, 0.14, '高い開いた 5 度 (Vn, pp)' if b == 1 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.12); oadd('VA', b * BPB + 0.1, 4 * BPB + 0.5, 71, 0.1)
        oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.22, 'コントラバスの保続 (シ)' if b == 1 else None)
    line('HN', INTRO + 5, HEAD_BM, 0, 0.22, 'ホルン — Stille Nacht の頭 (ロ短調で、静かに)'); line('HN', INTRO + 19, HEAD_BM, -12, 0.18)
    # II. SN I: 弦の和音が薄く
    chord_pad(P, SN1 + 1, SN1 + 27, [('V2', 62, 76), ('VA', 55, 67)], 0.12, 'Vn II・Va の和音 (薄く)')
    # III. Kyrie: 弦も追いかける
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, KYRIE + 4 + 4 * k, HEAD_BM, tr + (7 if k % 2 else 0), 0.24, '弦のフガート (Vn I → Vn II → Va → Vc)' if k == 0 else None)
    for k, (v, tr) in enumerate((('V2', 0), ('V1', 12), ('VC', -24), ('VA', -12))): line(v, KYRIE + 19 + 2 * k, INV_BM, tr, 0.2, '弦の反行' if k == 0 else None)
    chord_pad(P, KYRIE + 10, SN2, [('VA', 50, 64), ('CB', 43, 55)], 0.12)
    # IV. SN II: Vn I + Fl が旋律、和音、根音
    t = (SN2 + 1) * BPB; first = True
    for d, m in AG:
        oadd('V1', t, d, m, 0.3, 'Vn I — Stille Nacht' if first else None); oadd('FL', t, d, m + 12, 0.14, 'フルート (1 オクターヴ上)' if first else None); first = False; t += d
    chord_pad(P, SN2 + 1, SN2 + 27, [('V2', 62, 76), ('VA', 55, 67)], 0.16, 'Vn II・Va の和音')
    roots(P, SN2 + 1, SN2 + 27, [('VC', 12), ('CB', 0)], 0.2, 'Vc・Cb の根音')
    # V. Agnus Dei: 低い弦の和音、保続、鐘
    chord_pad(P, AGNUS + 2, SN3, [('VA', 50, 64), ('VC', 43, 55)], 0.14, 'Va・Vc の和音')
    for b in range(AGNUS + 2, SN3 - 2, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.2, None)
    line('HN', AGNUS + 14, HEAD_BM, -12, 0.2, 'ホルン — 頭'); add('X', AGNUS * BPB, 12, 35, 0.3, '深い鐘')
    # VI. SN III: 総奏
    t = (SN3 + 1) * BPB; first = True
    for i, (d, m) in enumerate(AG):
        oadd('HN', t, d, m - 12, 0.3, 'ホルン — Stille Nacht' if first else None); oadd('V1', t, d, m, 0.32, 'Vn I' if first else None); oadd('FL', t, d, m + 12, 0.16, None); oadd('WW', t, d, m, 0.14, 'オーボエ' if first else None); first = False; t += d
    chord_pad(P, SN3 + 1, SN3 + 27, [('V2', 62, 76), ('VA', 55, 67)], 0.18, 'Vn II・Va の和音')
    roots(P, SN3 + 1, SN3 + 27, [('VC', 12), ('CB', 0), ('TB', 12)], 0.22, 'Vc・Cb・トロンボーンの根音')
    oadd('TP', (SN3 + 25) * BPB, 3.0, 43, 0.3, 'ティンパニ (Amen)'); oadd('TP', (SN3 + 26) * BPB, 4.0, 38, 0.35, None)
    # VII. 結尾
    for b in range(CODA + 1, TOTAL - 2, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, 0.12, '高い開いた 5 度 (Vn, pp)' if b == CODA + 1 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.1); oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.18)
    line('HN', CODA + 6, HEAD_BM, -12, 0.18, 'ホルン — 頭 (最後に)'); line('HN', CODA + 15, HEAD_BM[:3] + [(6, 59)], -12, 0.14, None)
    # 共鳴 (13:19 の音): 高い開いた 5 度を序奏と結尾に、小さく
    first = True
    for b in list(range(INTRO + 2, SN1 - 2, 4)) + list(range(CODA + 2, TOTAL - 3, 4)):
        for i, m in enumerate((83, 90)): add('PF', b * BPB + 0.05 * i, 4 * BPB, m, 0.5 * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 35, 0.4, None)

META = dict(T.T.META, orchestra=True, rec_order=[R41, R42], reverb=[8.0, 3.0, 0.5],
            title='Requiem BADA — CXXXIII · Stille Nacht — Requiem nel palazzetto',
            subtitle='きよしこの夜 (Gruber、1818 年、ニ長調、3/4 = 6/8) を、10/13 の 2 曲の雰囲気 (冷たい空気の体育館、礼拝) の上で requiem の雰囲気に被せて: Introitus (06:41、高い 5 度、ホルンの頭、B-A-D-A) → Stille Nacht I (実音のピアノの聖歌) → Kyrie (06:42、頭のフガート) → Stille Nacht II (弦と木管) → Agnus Dei (B-A-D-A、深い鐘) → Lux aeterna (総奏、Amen) → Coda (06:41、深い鐘)。♩=60',
            legend=['PF', 'X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'HN', 'TB', 'TP'], vname={'PF': '共鳴 (13:19 の音)', 'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'HN': 'Hn', 'TB': 'Tb', 'TP': 'Timp'},
            footer=['旋律 = Stille Nacht (Franz Xaver Gruber、1818 年、パブリックドメイン): 24 小節、6/8 を 3/4 で。ニ長調は 10/13 の録音 (半音上げてロ短調) の平行長調。和音は聖歌の和声の下書きを優先しつつ旋律の音を含む和音を小節ごとに選ぶ',
                    'requiem の形 (Introitus → Kyrie → Agnus Dei → Lux aeterna) に聖歌を 3 度。B-A-D-A の唱え。4 声は実音のピアノ (9/24 08:53 の音)、管弦楽は synth の合成。鐘は始め・Agnus Dei・終わりに深いもの。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.T.make_bank(bank_out); META['bank'] = bank_out
    print('Stille Nacht', ' '.join('%s:%g' % (name_of(m), d) for d, m in AG[:8]))
    compose.main(OUT, seed=133, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'bpb', d['beats_per_bar'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
