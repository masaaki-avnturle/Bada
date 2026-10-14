#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXI · Amazing Grace nel palazzetto (Amazing Grace を、10/13 の 2 曲の雰囲気 — 冷たい空気の体育館に静かに流れる国歌、礼拝 — に合わせて)
  旋律: Amazing Grace (New Britain、1835 年の旋律、パブリックドメイン) — 3/4、五音音階、16 小節。ニ長調 (10/13 の録音を半音上げたロ短調の平行長調) で、実音のピアノ (9/24 08:53 の音) が歌う
    I.   Introduzione (ロ短調, ♩=60)   10/13 06:41 の実音 (半音上げて)。高い開いた 5 度 (シ・ファ#) の弦が pp、コントラバスの保続、ホルンが Amazing Grace の頭をロ短調で静かに
    II.  Amazing Grace I (ニ長調)       実音のピアノの 4 声で、讃美歌として (ソプラノが旋律、ほかの声部は和音から) — 弦の和音が薄く
    III. Inno (ロ短調)                  06:42 の実音の上で、06:41 の音から作った国歌のような旋律を 3/4 にして、4 声のユニゾンと弦のユニゾンで
    IV.  Amazing Grace II (ニ長調)      Vn I とフルートが旋律に重なり、Vc・Cb が根音 — 4 声の讃美歌はそのまま
    V.   Fugato (ロ短調)                Amazing Grace の頭 (ファ#・シ・レ・シ・レ・ド#・シ・ソ・ファ#) をロ短調の主題にして、4 声と弦が追いかける (反行も)
    VI.  Amazing Grace III (ニ長調)     総奏: ホルンが旋律、トロンボーンが根音、弦と木管、4 声 — 最後の句はユニゾンで。Amen (ソ → レ)
    VII. Coda (ロ短調)                  06:41 の実音、高い開いた 5 度、ホルンの頭、深い鐘
  使い方: BANK1013=<bank1013.json> SCORE89=<score_tablet89.json> python compose_tablet131.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet131.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet131.json'
sys.argv = sys.argv[:6] + ['/dev/null']
import compose
compose.BPB = 3                                                                                    # 3/4 (Amazing Grace)
import compose_tablet128 as T
from compose import *
BPB = 3
RECS, R41, R42, WDIR, RATE = T.RECS, T.R41, T.R42, T.WDIR, T.RATE
PSRC, octs, TOP, fit = T.T.PSRC, T.T.octs, T.T.TOP, T.T.fit
GMAJ = T.T.GMAJ
CANDS_D = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m', 'D/F#', 'G/B', 'A/C#', 'Em7', 'Asus4', 'Bm/D', 'D/A', 'G/D']
CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'F#', 'F#7', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4', 'C#m7b5']
BPM = 60
INTRO, AG1, INNO, AG2, FUGA, AG3, CODA, TOTAL = 0, 22, 40, 60, 78, 104, 122, 146
# Amazing Grace (ト長調で書いて、+7 でニ長調に): 3/4、(拍, MIDI)。はじめの 1 拍はアナクルーシス (3 拍目から)
AG_G = [(1, 62), (2, 67), (0.5, 71), (0.5, 67), (2, 71), (1, 69), (2, 67), (1, 64), (2, 62), (1, 62),
        (2, 67), (0.5, 71), (0.5, 67), (2, 71), (1, 69), (3, 74), (2, 74), (1, 71),
        (2, 74), (0.5, 71), (0.5, 74), (2, 71), (1, 67), (2, 62), (1, 64), (2, 67), (1, 62),
        (2, 67), (0.5, 71), (0.5, 67), (2, 71), (1, 69), (3, 67)]
AG = [(d, m + 7) for d, m in AG_G]                                                                 # ニ長調 (ラ 4 〜 ラ 5)
assert abs(sum(d for d, _ in AG) - 46) < 1e-9
HEAD_BM = [(1, 66), (2, 71), (0.5, 74), (0.5, 71), (2, 74), (1, 73), (2, 71), (1, 67), (3, 66)]    # 頭をロ短調に (ファ#・シ・レ・シ・レ・ド#・シ・ソ・ファ#)、13 拍
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
PLAYS = [(R41, 1, 0.45, 1), (R42, INNO + 1, 0.4, 1), (R41, CODA + 1, 0.4, 1)]
AG_RH = ['D', 'D', 'G', 'A', 'D', 'D', 'A', 'D', 'D', 'Bm', 'D', 'D', 'D', 'D', 'D', 'D']                # 讃美歌の和声の下書き (小節ごと、ニ長調) — harm_fit がこれを優先しつつ旋律に合わせる (3 拍目のミには A)                      # (録音, 小節, 大きさ, テープの移調)

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
        if cur is None: cur = 'D' if (AG1 <= q // BPB < INNO or AG2 <= q // BPB < FUGA or AG3 <= q // BPB < CODA) else 'Bm'
        for b0 in (AG1, AG2, AG3):
            if b0 + 1 <= q // BPB < b0 + 17: cur = AG_RH[q // BPB - b0 - 1]
        RH.append(cur); P.harm[q] = cur
    # I. 序奏 (4 声は休む)
    P.section(INTRO, 'I. Introduzione — 冷たい空気 (ロ短調, ♩=60)', '10/13 06:41 の実音 (半音上げて、小さく) — 高い開いた 5 度 (シ・ファ#) の弦が pp、コントラバスの保続 (シ)、ホルンが Amazing Grace の頭をロ短調で静かに')
    rest_others(P, INTRO, AG1, '')
    for q in range(INTRO * BPB, AG1 * BPB): P.harm[q] = 'Bm'
    # II. Amazing Grace I (実音のピアノの 4 声、讃美歌として)
    P.section(AG1, 'II. Amazing Grace I — 讃美歌 (ニ長調)', 'Amazing Grace (1835 年の旋律、パブリックドメイン) を実音のピアノの 4 声で: ソプラノが旋律 (3 拍目から)、ほかの声部は旋律の音を含むニ長調の和音から — 弦の和音が薄く')
    E = []; rest_others(P, AG1, AG1 + 1, ''); entry(P, AG1, 'S', AG, 0, 'Amazing Grace (ソプラノ)', E, beat=2)
    harm_fit(P, AG1, AG1 + 16, E, CANDS_D)
    for b in (AG1 + 16, AG1 + 17): P.set_harm(b, 'D'); P.hold.add(b)
    P.hold.update(range(AG1 + 1, AG1 + 16)); rest_others(P, AG1 + 18, INNO, '')
    # III. Inno (10/13 の旋律、ユニゾン)
    P.section(INNO, 'III. Inno — 10/13 の旋律を 3/4 で (ロ短調)', '06:42 の実音 (半音上げて) の上で、06:41 の音から作った国歌のような旋律を 3/4 の讃美歌のリズムにして、4 声のユニゾンと弦のユニゾンで — 句のあいだに間')
    rest_others(P, INNO, INNO + 1, ''); E = []
    for k in range(4):
        b = INNO + 1 + 4 * k + (1 if k >= 2 else 0)
        for v in VOICES: entry(P, b, v, iphrase(k), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Inno 第 %d 句 (ユニゾン)' % (k + 1)) if v == 'S' else None, E)
        if k == 1:
            for v in VOICES: P.rest_bars(v, b + 4, b + 5)
    for q in range(INNO * BPB, AG2 * BPB): P.harm[q] = 'Bm'
    rest_others(P, INNO + 18, AG2, '')
    # IV. Amazing Grace II
    P.section(AG2, 'IV. Amazing Grace II — 弦と木管が重なる (ニ長調)', 'Vn I とフルート (1 オクターヴ上) が旋律に重なり、Vn II・Va が和音、Vc・Cb が根音 — 実音のピアノの 4 声の讃美歌はそのまま')
    E = []; rest_others(P, AG2, AG2 + 1, ''); entry(P, AG2, 'S', AG, 0, 'Amazing Grace (ソプラノ、弦と)', E, beat=2)
    harm_fit(P, AG2, AG2 + 16, E, CANDS_D)
    for b in (AG2 + 16, AG2 + 17): P.set_harm(b, 'D'); P.hold.add(b)
    P.hold.update(range(AG2 + 1, AG2 + 16))
    # V. Fugato (頭をロ短調で)
    P.section(FUGA, 'V. Fugato — Amazing Grace の頭をロ短調で (ロ短調)', '頭 (ファ#・シ・レ・シ・レ・ド#・シ・ソ・ファ#) を主題にして、アルト → ソプラノ → バス → テノール、弦も Vn I → Vn II → Va → Vc と追いかける (後半は反行)')
    E = []; rest_others(P, FUGA, FUGA + 1, '')
    for k, v in enumerate('ASBT'):
        entry(P, FUGA + 1 + 4 * k, v, HEAD_BM, 7 if k % 2 else 0, '主題 (Amazing Grace の頭、ロ短調)' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, FUGA + 1 + 4 * k, FUGA + 1 + 4 * (k + 1))
    for k, v in enumerate('STAB'):
        entry(P, FUGA + 17 + 2 * k, v, invert(HEAD_BM), 0 if k % 2 == 0 else 7, '反行' if k == 0 else None, E)
    harm_fit(P, FUGA + 1, AG3, E, CANDS_BM)
    # VI. Amazing Grace III (総奏)
    P.section(AG3, 'VI. Amazing Grace III — 総奏 (ニ長調)', 'ホルンが旋律、トロンボーン・Vc・Cb が根音、弦と木管、実音のピアノの 4 声 — 最後の句 (was blind, but now I see) は 4 声のユニゾンで。Amen (ソ → レ)')
    E = []; rest_others(P, AG3, AG3 + 1, ''); entry(P, AG3, 'S', AG, 0, 'Amazing Grace (ソプラノ、総奏)', E, beat=2)
    last = 46 - 10                                                                                  # 最後の句 (10 拍) はユニゾン
    for v in 'ATB':
        P.rest_bars(v, AG3 + 12, AG3 + 16); P.place(v, AG3 + 12, AG[-5:], {'A': -12, 'T': -24, 'B': -36}[v], 'ユニゾン' if v == 'A' else '')
    harm_fit(P, AG3, AG3 + 16, E, CANDS_D)
    for q in range((AG3 + 12) * BPB, (AG3 + 16) * BPB): P.harm[q] = 'D' if P.harm[q] not in ('D', 'G', 'A', 'A7', 'D/F#', 'D/A') else P.harm[q]
    P.hold.update(range(AG3 + 1, AG3 + 12))
    P.set_harm(AG3 + 16, 'G'); P.set_harm(AG3 + 17, 'D'); P.hold.update({AG3 + 16, AG3 + 17})
    P.place('S', AG3 + 16, [(3, 79), (3, 78)], 0, 'Amen (ソ → レ)'); P.place('A', AG3 + 16, [(3, 71), (3, 69)], 0, ''); P.place('T', AG3 + 16, [(3, 67), (3, 66)], 0, ''); P.place('B', AG3 + 16, [(3, 43), (3, 38)], 0, '')
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
    # I. 序奏: 高い 5 度、保続、ホルンの頭
    for b in range(INTRO + 1, AG1 - 1, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, 0.14, '高い開いた 5 度 (Vn, pp)' if b == 1 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.12); oadd('VA', b * BPB + 0.1, 4 * BPB + 0.5, 71, 0.1)
        oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.22, 'コントラバスの保続 (シ)' if b == 1 else None)
    line('HN', INTRO + 8, HEAD_BM, 0, 0.22, 'ホルン — Amazing Grace の頭 (ロ短調で、静かに)', beat=2); line('HN', INTRO + 14, HEAD_BM, -12, 0.18, beat=2)
    # II. AG I: 弦の和音が薄く
    chord_pad(P, AG1 + 1, AG1 + 18, [('V2', 62, 76), ('VA', 55, 67)], 0.12, 'Vn II・Va の和音 (薄く)')
    # III. Inno: 弦のユニゾン
    for k in range(4):
        b = INNO + 1 + 4 * k + (1 if k >= 2 else 0)
        for v, tr in (('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24)): line(v, b, iphrase(k), tr, 0.22 if v in ('V1', 'V2') else 0.2, '弦のユニゾン' if (k == 0 and v == 'V1') else None)
    # IV. AG II: Vn I + Fl が旋律、和音、根音
    t = AG2 * BPB + 2; first = True
    for d, m in AG:
        oadd('V1', t, d, m, 0.3, 'Vn I — Amazing Grace' if first else None); oadd('FL', t, d, m + 12, 0.14, 'フルート (1 オクターヴ上)' if first else None); first = False; t += d
    chord_pad(P, AG2 + 1, AG2 + 18, [('V2', 62, 76), ('VA', 55, 67)], 0.16, 'Vn II・Va の和音')
    roots(P, AG2 + 1, AG2 + 18, [('VC', 12), ('CB', 0)], 0.2, 'Vc・Cb の根音')
    # V. Fugato: 弦も追いかける
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, FUGA + 3 + 4 * k, HEAD_BM, tr + (7 if k % 2 else 0), 0.24, '弦のフガート (Vn I → Vn II → Va → Vc)' if k == 0 else None)
    for k, (v, tr) in enumerate((('V2', 0), ('V1', 12), ('VC', -24), ('VA', -12))): line(v, FUGA + 18 + 2 * k, invert(HEAD_BM), tr, 0.2, '弦の反行' if k == 0 else None)
    chord_pad(P, FUGA + 9, AG3, [('VA', 50, 64), ('CB', 43, 55)], 0.12)
    line('HN', AG3 - 4, HEAD_BM, 0, 0.22, 'ホルン — 頭', beat=2)
    # VI. AG III: 総奏
    t = AG3 * BPB + 2; first = True
    for i, (d, m) in enumerate(AG):
        oadd('HN', t, d, m - 12, 0.3, 'ホルン — Amazing Grace' if first else None); oadd('V1', t, d, m, 0.32, 'Vn I' if first else None); oadd('FL', t, d, m + 12, 0.16, None); oadd('WW', t, d, m, 0.14, 'オーボエ' if first else None); first = False; t += d
    chord_pad(P, AG3 + 1, AG3 + 18, [('V2', 62, 76), ('VA', 55, 67)], 0.18, 'Vn II・Va の和音')
    roots(P, AG3 + 1, AG3 + 18, [('VC', 12), ('CB', 0), ('TB', 12)], 0.22, 'Vc・Cb・トロンボーンの根音')
    oadd('TP', (AG3 + 16) * BPB, 3.0, 43, 0.3, 'ティンパニ (Amen)'); oadd('TP', (AG3 + 17) * BPB, 4.0, 38, 0.35, None)
    # VII. 結尾
    for b in range(CODA + 1, TOTAL - 2, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, 0.12, '高い開いた 5 度 (Vn, pp)' if b == CODA + 1 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.1); oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.18)
    line('HN', CODA + 7, HEAD_BM, -12, 0.18, 'ホルン — 頭 (最後に)', beat=2); line('HN', CODA + 14, [(d, m) for d, m in HEAD_BM[:4]] + [(6, 71)], -12, 0.14, None, beat=2)
    # 共鳴 (13:19 の音): 高い開いた 5 度を序奏と結尾に、小さく
    first = True
    for b in list(range(INTRO + 2, AG1 - 2, 4)) + list(range(CODA + 2, TOTAL - 3, 4)):
        for i, m in enumerate((83, 90)): add('PF', b * BPB + 0.05 * i, 4 * BPB, m, 0.5 * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 35, 0.4, None)

META = dict(T.T.META, orchestra=True, rec_order=[R41, R42], reverb=[8.0, 3.0, 0.5],
            title='Requiem BADA — CXXXI · Amazing Grace nel palazzetto',
            subtitle='Amazing Grace (1835 年の旋律、ニ長調、3/4) を、10/13 の 2 曲の雰囲気 (冷たい空気の体育館に静かな国歌、礼拝) に合わせて: Introduzione (06:41、高い 5 度、ホルンの頭) → Amazing Grace I (実音のピアノの讃美歌) → Inno (10/13 の旋律、06:42) → Amazing Grace II (弦と木管が重なる) → Fugato (頭をロ短調で) → Amazing Grace III (総奏、Amen) → Coda (06:41、深い鐘)。♩=60',
            legend=['PF', 'X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'HN', 'TB', 'TP'], vname={'PF': '共鳴 (13:19 の音)', 'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'HN': 'Hn', 'TB': 'Tb', 'TP': 'Timp'},
            footer=['旋律 = Amazing Grace (New Britain、1835 年、パブリックドメイン): 五音音階、16 小節 + アナクルーシス。ニ長調は 10/13 の録音 (半音上げてロ短調) の平行長調。和音は旋律の音を含む和音を小節ごとに選ぶ',
                    '4 声は実音のピアノ (9/24 08:53 の音)。管弦楽は synth の合成。10/13 の実音は序奏・Inno・結尾に。鐘は始めと終わりに深いものがひとつ。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.T.make_bank(bank_out); META['bank'] = bank_out
    print('inno', ' '.join('%s:%g' % (name_of(m), d) for d, m in INNO_T[:8]))
    compose.main(OUT, seed=131, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'bpb', d['beats_per_bar'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
