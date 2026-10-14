#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXIX · Sinfonia sull'inno americano (10/13 の雰囲気で、アメリカ国歌を主題にした交響曲 — acceptance を参考に)
  管弦楽だけ (synth の合成: 弦・フルート・オーボエ・ホルン・トランペット・トロンボーン・ティンパニ)。10/13 06:41・06:42 の実音 (半音上げてロ短調に) が序奏・Inno・結尾に小さく
    I.   Introduzione (ロ短調, ♩=60)   冷たい空気: 高い開いた 5 度 (シ・ファ#) の弦が pp で、コントラバスの保続。ホルンが国歌の頭 (ソ・ミ・ド・ミ・ソ・ド) をロ短調で静かに。06:41 の実音
    II.  Inno (ロ短調)                  10/13 06:41 の音から作った国歌のような旋律 (CXXV の Inno) を弦のユニゾン (オクターヴ) で、句のあいだに間。06:42 の実音
    III. Tema (ニ長調, ♩=72)            The Star-Spangled Banner を弦と木管で (Vn I が旋律、フルートが 1 オクターヴ上、Vn II・Va が和音、Vc・Cb が根音)
    IV.  Sviluppo (ロ短調, ♩=60)        主題の頭 (ファ#・レ・シ・レ・ファ#・シ) のフガート (Vn I → Vn II → Va → Vc)、「rockets' red glare」の句の拡大を金管で (ロ短調に)、acceptance の主題 (シ・ラ・ソ・ラ・ソ・ファ#) がホルンに、ティンパニが高まる
    V.   Finale (ニ長調, ♩=72)          国歌の総奏 (トランペット・ホルン・トロンボーン・弦・フルート・ティンパニ)
    VI.  Coda (ロ短調, ♩=60)            冷たい空気に戻る: 06:41 の実音、高い開いた 5 度、ホルンの頭、深い鐘
  使い方: BANK1013=<bank1013.json> SCORE89=<score_tablet89.json> python compose_tablet129.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet129.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet129.json'
sys.argv = sys.argv[:6] + ['/dev/null']
import compose_tablet128 as T
from compose import *
import compose
SSB, RECS, R41, R42, WDIR, aphrase, RATE = T.SSB, T.RECS, T.R41, T.R42, T.WDIR, T.aphrase, T.RATE
add, oadd, harm_fit = T.add, T.oadd, T.harm_fit
CANDS_D = T.CANDS_D; CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'F#', 'F#7', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4', 'C#m7b5']
INTRO, INNO, TEMA, SVIL, FINALE, CODA, TOTAL = 0, 16, 36, 58, 98, 120, 134
SSB_BARS = T.SSB_BARS
HEAD = [(0.75, 69), (0.25, 66), (1, 62), (1, 66), (1, 69), (2, 74)]                                   # 国歌の頭 (ニ長調)
HEAD_BM = [(0.75, 66), (0.25, 62), (1, 59), (1, 62), (1, 66), (2, 71)]                                # ロ短調に
GLARE = [(0.5, 74), (0.5, 74), (1, 74), (1, 75), (1, 77), (2, 77), (0.75, 75), (0.25, 74), (1, 73), (1, 74), (1, 75), (2, 75)]   # "And the rockets' red glare, the bombs bursting in air" (ニ長調)
def to_bm(mat):                                                                                    # ニ長調の音をロ短調 (同じ調号) で: 長 3 度の音 (ファ#) を短 3 度 (レ) 側へ寄せず、そのまま — 平行調なので音階は同じ。主音だけ違う
    return mat
ACC = [(3, 71), (1, 69), (1.5, 67), (0.5, 69), (1, 67), (1, 66)]                                   # acceptance の主題 (ロ短調)
PLAYS = [(R41, 1, 0.45, 1, 60), (R42, INNO + 1, 0.4, 1, 60), (R41, CODA + 1, 0.4, 1, 60)]
def tempo_of(bar): return 72.0 if (TEMA <= bar < SVIL or FINALE <= bar < CODA) else 60.0
def augment(mat, k=2): return [(k * d, m) for d, m in mat]
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def line(v, bar, mat, tr, g, label=None, beat=0):
    t = bar * BPB + beat; first = True; E = []
    for d, m in mat:
        oadd(v, t, d, m + tr, g, label if first else None); first = False; E.append((t, [(d, m + tr)])); t += d
    return (bar * BPB + beat, [(d, m + tr) for d, m in mat])

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = tempo_of(k); P.dyn[k] = 0.9
    for q in range(TOTAL * BPB): T.T.RH.append('Bm'); P.harm[q] = 'D' if (TEMA * BPB <= q < SVIL * BPB or FINALE * BPB <= q < CODA * BPB) else 'Bm'
    for v in VOICES: P.rest_bars(v, 0, TOTAL)                                                       # 4 声 (ピアノ) は使わない — 管弦楽だけ
    P.section(INTRO, 'I. Introduzione — 冷たい空気 (ロ短調, ♩=60)', '10/13 06:41 の実音 (半音上げて、小さく) — 高い開いた 5 度 (シ・ファ#) の弦が pp、コントラバスの保続 (シ)、ホルンが国歌の頭をロ短調で静かに')
    P.section(INNO, 'II. Inno — 10/13 の旋律を弦のユニゾンで (ロ短調)', '06:42 の実音の上で、06:41 の音から作った国歌のような旋律 (CXXV の Inno) を弦のユニゾン (オクターヴ) で — 句のあいだに間')
    P.section(TEMA, 'III. Tema — The Star-Spangled Banner (ニ長調, ♩=72)', '国歌を弦と木管で: Vn I が旋律、フルートが 1 オクターヴ上、Vn II・Va が和音、Vc・Cb が根音')
    harm_fit(P, TEMA + 1, TEMA + 1 + SSB_BARS + 1, [((TEMA + 1) * BPB, SSB)], CANDS_D)
    P.section(SVIL, 'IV. Sviluppo — 主題の頭のフガート、金管の拡大 (ロ短調, ♩=60)', '主題の頭 (ファ#・レ・シ・レ・ファ#・シ) が Vn I → Vn II → Va → Vc と追いかけ、「rockets red glare」の句の拡大 (×2) がトロンボーンとホルンに、acceptance の主題 (シ・ラ・ソ・ラ・ソ・ファ#) がホルンに — ティンパニが高まる')
    E = []
    for k, v in enumerate(('V1', 'V2', 'VA', 'VC')): E.append((( SVIL + 2 + 2 * k) * BPB, [(d, m + (12 if v == 'V1' else 0 if v == 'V2' else -12 if v == 'VA' else -24)) for d, m in HEAD_BM]))
    E.append(((SVIL + 12) * BPB, augment(GLARE))); E.append(((SVIL + 24) * BPB, ACC)); E.append(((SVIL + 30) * BPB, invert(HEAD_BM)))
    harm_fit(P, SVIL, FINALE, E, CANDS_BM)
    P.section(FINALE, 'V. Finale — 国歌の総奏 (ニ長調, ♩=72)', 'トランペットと Vn I が旋律、フルートが 1 オクターヴ上、ホルンが和音、トロンボーン・Vc・Cb が根音、ティンパニ')
    harm_fit(P, FINALE + 1, FINALE + 1 + SSB_BARS + 1, [((FINALE + 1) * BPB, SSB)], CANDS_D)
    P.section(CODA, 'VI. Coda — 冷たい空気に戻る (ロ短調)', '06:41 の実音、高い開いた 5 度の弦、ホルンの頭 — 深い鐘がひとつ')
    return P

def chord_pad(P, b0, b1, parts, g, label=None):
    """和音 (P.harm) を楽器で保つ: parts = [(楽器, 低, 高)]"""
    q = b0 * BPB; first = True
    while q < b1 * BPB:
        h = P.harm[q]; q1 = q
        while q1 < b1 * BPB and P.harm[q1] == h: q1 += 1
        c = chord(h)
        for v, lo, hi in parts:
            tones = sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
            for i, m in enumerate(tones[:3] if v != 'CB' else [min(tones)]): oadd(v, q + 0.03 * i, (q1 - q) + 0.3, m if v != 'CB' else m - 12, g * (1.0 if i == 0 else 0.8), label if (first and i == 0) else None); first = False
        q = q1

def post(P, events, ex):
    for rid, bar, g, sm, _ in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * tempo_of(bar) / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 1 else 0.02, fout=5.0, semis=sm, rid=rid + '.wav', tag='10/13 %s — 実音 (半音上げてロ短調に)' % ('06:41' if rid == R41 else '06:42'))
    # I. 序奏
    for b in range(INTRO + 1, INNO, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, 0.14, '高い開いた 5 度 (Vn, pp)' if b == 1 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.12); oadd('VA', b * BPB + 0.1, 4 * BPB + 0.5, 71, 0.1)
        oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.22, 'コントラバスの保続 (シ)' if b == 1 else None)
    line('HN', INTRO + 7, HEAD_BM, 0, 0.22, 'ホルン — 国歌の頭 (ロ短調で、静かに)'); line('HN', INTRO + 11, HEAD_BM, -12, 0.18)
    # II. Inno (弦のユニゾン)
    for k in range(4):
        b = INNO + 1 + 4 * k + (1 if k >= 2 else 0)
        for v, tr in (('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24), ('CB', -36)): line(v, b, aphrase(k), tr, 0.3 if v in ('V1', 'V2') else 0.26, ('Inno 第 %d 句 (弦のユニゾン)' % (k + 1)) if v == 'V1' else None)
    # III. Tema (弦と木管)
    t = (TEMA + 1) * BPB; first = True
    for i, (d, m) in enumerate(SSB):
        oadd('V1', t, d, m, 0.34, 'Vn I — The Star-Spangled Banner' if first else None); oadd('FL', t, d, m + 12, 0.16, 'フルート (1 オクターヴ上)' if first else None); first = False; t += d
    chord_pad(P, TEMA + 1, TEMA + 2 + SSB_BARS, [('V2', 57, 72), ('VA', 50, 64), ('VC', 43, 55), ('CB', 43, 55)], 0.2, 'Vn II・Va の和音、Vc・Cb の根音')
    oadd('WW', (TEMA + 1 + SSB_BARS) * BPB, 6, 74, 0.2, 'オーボエ'); oadd('WW', (TEMA + 1 + SSB_BARS) * BPB + 6, 4, 69, 0.18)
    # IV. 展開
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, SVIL + 2 + 2 * k, HEAD_BM, tr, 0.3, 'フガート — 主題の頭 (ロ短調)' if k == 0 else None)
    for k, (v, tr) in enumerate((('V2', 0), ('V1', 12), ('VC', -24), ('VA', -12))): line(v, SVIL + 10 + 2 * k, invert(HEAD_BM), tr, 0.26, '主題の頭 (反行)' if k == 0 else None)
    line('TB', SVIL + 12, augment(GLARE), -24, 0.28, 'トロンボーン — rockets\' red glare の拡大 (×2)'); line('HN', SVIL + 12, augment(GLARE), -12, 0.24)
    line('HN', SVIL + 24, ACC, -12, 0.26, 'ホルン — acceptance の主題'); line('HN', SVIL + 28, ACC, 0, 0.24); line('TR', SVIL + 30, invert(HEAD_BM), 0, 0.24, 'トランペット — 頭 (反行)'); line('TR', SVIL + 32, HEAD_BM, 12, 0.26, None)
    chord_pad(P, SVIL + 8, FINALE, [('VA', 50, 64), ('VC', 43, 55), ('CB', 43, 55)], 0.16)
    for k, b in enumerate(range(SVIL + 16, FINALE, 4)): oadd('TP', b * BPB, 2.0, 35 if k % 2 == 0 else 42, 0.3 + 0.03 * k, 'ティンパニ' if k == 0 else None)
    for i in range(8): oadd('TP', (FINALE - 2) * BPB + i * 0.5, 0.5, 35, 0.25 + 0.04 * i, None)
    # V. 終曲 (総奏)
    T.orchestrate(P, FINALE + 1, True)
    # VI. 結尾
    for b in range(CODA + 1, TOTAL - 2, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 90, 0.12, '高い開いた 5 度 (Vn, pp)' if b == CODA + 1 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.1); oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.18)
    line('HN', CODA + 5, HEAD_BM, -12, 0.18, 'ホルン — 頭 (最後に)')
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 35, 0.4, None)

META = dict(T.META, rec_order=[R41, R42], reverb=[8.0, 3.0, 0.5],
            title='Requiem BADA — CXXIX · Sinfonia sull\'inno americano',
            subtitle='10/13 の雰囲気 (冷たい空気の体育館に静かな国歌) で、アメリカ国歌を主題にした交響曲: Introduzione (高い 5 度、ホルンの頭) → Inno (10/13 の旋律を弦で) → Tema (国歌、弦と木管) → Sviluppo (頭のフガート、金管の拡大、acceptance の主題、ロ短調) → Finale (総奏) → Coda (冷たい空気に戻る)。管弦楽だけ、♩=60 / 72',
            legend=['X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'HN', 'TR', 'TB', 'TP'], vname={'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
            footer=['主題 = The Star-Spangled Banner (music21 の収録譜、ニ長調) — 頭 (ソ・ミ・ド・ミ・ソ・ド) をロ短調に移して展開。Inno = CXXV (10/13 06:41 の音)。acceptance の主題 シ・ラ・ソ・ラ・ソ・ファ#',
                    '管弦楽は synth の合成。10/13 の実音は序奏・Inno・結尾に小さく。鐘は始めと終わりに深いものがひとつ。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.T.make_bank(bank_out); META['bank'] = bank_out
    compose.main(OUT, seed=129, bpm=60, builder=build, meta=META, extras=T.extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
