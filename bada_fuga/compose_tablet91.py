#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCI · Canzone 08:53 (9/24 08:53 を主題歌に、バックに piano_solo_8x)
  主題歌: 9/24 08:53 の録音 (ロ短調のピアノ、3 分 22 秒) をそのまま、元の速さ・元の高さで (実音)
  バック: piano_solo_8x.mp4 (42 分、調がゆっくり移る ×8 のピアノ) の音声から、ロ短調とその近い調 (ホ短調 → ロ短調 → イ短調 → ト長調) が続く
    2130〜2386 秒の窓を切り出して、移調せずに小さく敷く (録音と同じロ短調の窓が主題歌の真ん中に来る)
  形式 (♩=60、64 小節 = 4 分 16 秒):
    Intro (0〜4 小節)   バックだけ (4 秒でフェードイン)
    主題歌 (4〜54.5)    08:53 の録音そのもの — 画面には採譜の音を (音は出さず)、和音の表示も録音の採譜から
    Coda (55〜64)       録音の主題 (ミ・ファ#・シ・ミ・ミ) を 4 倍に伸ばして、録音自身の音 (切り出した 1 音) で — バックは消えていく
  すべてピアノの実音。声なし。
  使い方: python compose_tablet91.py <bank (piano samples).json> <bank85.json (08:53 の採譜)> <piano_solo_8x.wav> [score_tablet91.json]
"""
import sys, json
import numpy as np
from compose import name_of

BANK, B85, BG = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet91.json'
R = '20260924_085314'; REC = B85['recordings'][R]
INTRO, NB = 4, 64; T_REC = INTRO * 4.0; BG_OFF = 2130.0
G_REC, G_BG = 0.8, 0.14
SUBJ = [(1, 64), (3, 66), (1.5, 71), (1.5, 76), (1, 76)]                      # ミ・ファ#・シ・ミ・ミ (実音、ロ短調)

def build():
    notes, extras, entries, sections, harm = [], [], [], [], []
    extras.append(dict(v='REC', beat=0, dbeats=NB * 4, m=0, gain=G_BG, label=None, src=BG, off=BG_OFF, fin=4.0, fout=8.0, rid='piano_solo_8x.wav',
                       tag='piano_solo_8x — 2130 秒から (ホ短調 → ロ短調 → イ短調 → ト長調)', t=0.0, d=float(NB * 4)))
    extras.append(dict(v='REC', beat=T_REC, dbeats=round(REC['dur'], 3), m=0, gain=G_REC, label=None, src=REC['file'], off=0.0, fin=0.02, fout=1.0, rid=R + '.wav',
                       tag='9/24 08:53 — 主題歌 (実音)', t=T_REC, d=round(REC['dur'], 3)))
    sections.append(dict(t=0.0, bar=0, title='Intro — piano_solo_8x', sub='バックだけ — ホ短調からロ短調へ移っていくところ'))
    sections.append(dict(t=T_REC, bar=INTRO, title='主題歌 — 9/24 08:53 (実音、ロ短調)', sub='録音そのもの、元の速さ・元の高さで — バックは小さく'))
    entries.append(dict(t=T_REC, label='主題歌 08:53 (実音)', v='S', bar=INTRO + 1))
    # 画面の表示だけ: 録音の採譜の音を gain 0 の PF で (音は出さない — 音は REC の実音)
    for sg in REC['segs']:
        for m in sg['m']:
            extras.append(dict(v='PF', beat=round(T_REC + sg['t'], 3), dbeats=round(max(0.25, sg['d']), 3), m=int(m), gain=0.0, rid=R, rel=0.3, label=None, layer='disp',
                               t=round(T_REC + sg['t'], 3), d=round(max(0.25, sg['d']), 3)))
    # 和音の表示: 採譜から
    cur = 'Bm'
    for q in range(NB * 4):
        sec_t = q - T_REC
        for s in REC['segs']:
            if s['t'] <= sec_t: cur = s['ch']
        harm.append(cur if 0 <= sec_t < REC['dur'] else 'Bm')
    # Coda: 主題 ×4 を録音自身の音で
    c0 = int(np.ceil((T_REC + REC['dur']) / 4.0)) + 0.5
    sections.append(dict(t=c0 * 4, bar=int(c0), title='Coda — 主題 ×4 (録音の音で)', sub='ミ・ファ#・シ・ミ・ミ を 4 倍に伸ばして、2 拍ごとに息をするように — バックは消えていく'))
    t = c0 * 4; first = True
    for d, m in SUBJ:
        L = d * 4; n_ = int(round(L / 2))
        for i in range(n_):
            amp = 1.0 if i == 0 else 0.6 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1)); g = 1.0 - 0.5 * (t + 2 * i - c0 * 4) / 36.0
            for o, gg in ((0, 1.0), (-12, 0.45)):
                extras.append(dict(v='PF', beat=round(t + 2 * i, 3), dbeats=2.0, m=m + o, gain=round(0.5 * gg * amp * g, 4), rid=R, rel=1.0, label=None, layer='coda',
                                   t=round(t + 2 * i, 3), d=2.9))
            if first: entries.append(dict(t=t, label='主題 ×4 (08:53 の音)', v='S', bar=int(c0) + 1)); first = False
        t += L
    for q in range(int(c0 * 4), NB * 4): harm[q] = 'Bm'
    return dict(bpm=60, beats_per_bar=4, nbars=NB, duration=float(NB * 4), bar_times=[4.0 * i for i in range(NB + 1)], notes=notes, extras=extras,
                entries=entries, sections=sections, harm=harm)

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R], 'piano_decay': 2.4, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — XCI · Canzone 08:53', 'subtitle': '9/24 08:53 を主題歌に (実音、ロ短調) — バックに piano_solo_8x (移調なし)',
        'legend': ['PF'], 'vname': {'PF': '主題 ×4'},
        'footer': ['Intro (piano_solo_8x) → 主題歌: 08:53 の録音そのもの (3 分 22 秒) → Coda: 主題 ×4 (録音の音で)', 'すべてピアノの実音。声なし。']}

if __name__ == '__main__':
    d = build(); d['meta'] = META
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration', d['duration'], 'extras', len(d['extras']), 'coda from', d['sections'][-1]['t'])
