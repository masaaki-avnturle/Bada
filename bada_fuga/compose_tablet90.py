#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XC · Continuazione 12:50:53 (LXXXIX からカノンを消し、フーガを裏のベースに — 9/25 12:50:53 の終わりから続きを作曲して、実音のピアノで)
  裏 (ベース): LXXXIX の I〜IV (80 小節) — V のストレッタ (カノン) と Amen は消す。フーガ (II・IV) は ×0.45、伸ばした主題は裏の大きさ、cp14_x4 は全部 0.25 で小さく。
  表: 9/25 12:50:53 (ロ短調 → 終わりはニ長調で閉じる、4 分 24 秒) の続き —
    Intro (0〜5 小節): 録音の終わりの 20 秒そのもの (ニ長調の終止 A7 → D)
    続き (5〜76 小節): 録音の終わりの節 M = ミ・ラ・ソ・ファ#・ソ・ファ# (8 拍、256.8 秒〜) を種に —
      裏のフーガ・レクイエムの和音 (LXXXIX の harm) に、2 小節ごとに M をいちばん合う移調 (±7 半音) で置いていく (シャコンヌのように、裏の和声に従って動く)
      5〜24: M の連鎖 ／ 24〜40: M を 2 倍に (裏のフーガの上で) ／ 40〜64: M と転回を交互に、密に ／ 64〜76: M をオクターヴで、2 倍で
      左手: 裏の和音の根音 (1 拍目に 2 拍)・5 度 (3 拍目)、内声は 3 度・5 度を 2・4 拍目に — 録音の終わりの (ラ 2 … ファ# 4 の) 簡素な手つき
    Amen (76〜80): A7 → D、録音の終わりの和音 (ラ 2・レ 4・ファ# 4) で閉じる — 裏はここで消える
  表は裏より約 4 dB 大きく (ステムで測って: 表 ×2.2、裏のフーガ ×0.32、cp14_x4 0.18)。旋律の音は 12:50:53 の録音から切り出した 1 音 (ファ# 3〜シ 5)、低音は 13:04 の音。すべてピアノの実音、声なし。高音はミ 5 まで。
  使い方: python compose_tablet90.py <score_tablet89.json> <bank89.json> <bank87.json (12:50:53)> [score_tablet90.json]
"""
import sys, os, json
import numpy as np
from compose import name_of, chord

SRC = json.load(open(sys.argv[1])); B89 = json.load(open(sys.argv[2])); B87 = json.load(open(sys.argv[3]))
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet90.json'
R53 = '20260925_125053'; REC53 = B87['recordings'][R53]
LOWSRC = '20260925_130431'
NB = 80; END = 76; CAP = 76
M = [(1, 64), (1, 69), (1, 67), (2, 66), (1, 67), (2, 66)]          # ミ・ラ・ソ・ファ#・ソ・ファ# (録音の終わりの節)
MI = [(d, 2 * 66 - m) for d, m in M]                                # 転回 (ファ# を軸に)

def fit(mot, b0, harm, prev, k=1):
    """2 小節の和音に、いちばん合う移調 (強拍・長い音は和音の音に) — 前の置き方に近いほうを少し優先"""
    def score(tr):
        s, t = 0.0, float(b0)
        for d, m in mot:
            c = chord(harm[min(int(t), len(harm) - 1)] or 'Dm'); pc = (m + tr) % 12
            w = d * k * (2.0 if (t - b0) % 4 == 0 else 1.0)
            if pc in c['pcs']: s += w
            elif pc in c['scale']: s -= 0.3 * w
            else: s -= 1.2 * w
            t += d * k
        return s
    cand = [tr for tr in range(-9, 8) if max(m for _, m in mot) + tr <= CAP and min(m for _, m in mot) + tr >= 57]
    return max(cand, key=lambda tr: score(tr) - 0.12 * abs(tr - prev) - (0.6 if tr == prev else 0))   # 同じ移調が続かないように

def build():
    harm = list(SRC['harm'][:END * 4]) + ['A7'] * 4 + ['D'] * 12
    notes, extras, entries, sections = [], [], [], []
    # 裏: LXXXIX の I〜IV
    for x in SRC['notes']:
        if x['beat'] >= END * 4: continue
        y = dict(x); y['dyn'] = round(x['dyn'] * 0.32, 3); y['label'] = None; notes.append(y)
    for x in SRC['extras']:
        if x['beat'] >= END * 4: continue
        y = dict(x); y['label'] = None
        if y['v'] == 'REC':
            y['gain'] = 0.18; y['tag'] = (y.get('tag') or '').replace(' (裏 → 表)', '').replace(' (裏)', '') + ' (裏)'
            if y['beat'] + y['dbeats'] > END * 4: y['dbeats'] = END * 4 - y['beat']; y['d'] = float(y['dbeats'])
        elif y.get('layer') == 'front': y['gain'] = round(y['gain'] * 0.21, 4); y['layer'] = 'back'
        elif y['v'] == 'PF': y['gain'] = round(y['gain'] * 0.35, 4)
        extras.append(y)
    # 表: Intro — 録音の終わり
    sections.append(dict(t=0.0, bar=0, title='Intro — 9/25 12:50:53 の終わり (実音)', sub='録音の最後の 20 秒そのもの (A7 → D のニ長調の終止) — ここから続きを作曲する'))
    extras.append(dict(v='REC', beat=0, dbeats=20, m=0, gain=0.55, label=None, src=REC53['file'], off=round(REC53['dur'] - 20.0, 3), fin=0.05, fout=2.5,
                       rid=R53 + '.wav', tag='12:50:53 の終わり (実音)', t=0.0, d=20.0))
    def N(v, beat, dur, m, dyn, src, label=None):
        notes.append(dict(v=v, beat=round(beat, 3), dbeats=round(dur, 3), m=int(m), dyn=round(dyn * 2.2, 3), src=src, label=label, det=1.0, role='', t=round(beat, 3), d=round(dur, 3)))
    def acc(bar, dyn=0.5, inner=True):
        c = chord(harm[bar * 4] or 'Dm'); r = 38 + (c['root'] - 38) % 12
        N('B', bar * 4, 2.0, r, dyn * 1.2, LOWSRC); N('B', bar * 4 + 2, 1.0, r + 7 if r + 7 <= 50 else r - 5, dyn * 0.8, LOWSRC)
        if inner:
            for q, pc in ((1, c['third']), (3, c['fifth'])): N('A', bar * 4 + q, 1.0, 55 + (pc - 55) % 12, dyn * 0.7, R53)
    plan = [(5, 24, 'I. 続き — M の連鎖', '録音の終わりの節 M (ミ・ラ・ソ・ファ#・ソ・ファ#) が、裏の和音に従って移調しながら続く', M, 1, False, 1.0),
            (24, 40, 'II. 続き — M を 2 倍に (裏: フーガ 08:09)', '裏で 08:09 のフーガが小さく — 表では M がゆっくり 2 倍で', M, 2, False, 0.95),
            (40, 64, 'III. 続き — M と転回を交互に', '裏のレクイエム (15:12・15:16 ×4) の上で、M とその転回 (ファ# を軸に) が 2 小節ごとに入れ替わる', None, 1, True, 1.05),
            (64, 76, 'IV. 続き — M をオクターヴで (裏: フーガ 08:53)', '裏で 08:53 のフーガが小さく — 表では M がオクターヴで、最後は 2 倍で', M, 1, False, 1.15)]
    prev = 0
    for b0, b1, title, sub, mot, k, alt, dyn in plan:
        sections.append(dict(t=float(b0 * 4), bar=b0, title=title, sub=sub))
        bar = b0; i = 0
        while bar + 2 * k <= b1:
            mo = (M if i % 2 == 0 else MI) if alt else mot
            kk = 2 if (b0 == 64 and bar >= 72) else k
            if bar + 2 * kk > b1: break
            tr = fit(mo, bar * 4, harm, prev, kk); prev = tr
            t = bar * 4.0
            lab = ('M' if mo is M else 'M の転回') + (' ×2' if kk == 2 else '') + (' (オクターヴ)' if b0 == 64 else '')
            for j, (d, m) in enumerate(mo):
                N('S', t, d * kk, m + tr, dyn, R53, lab if j == 0 and (i == 0 or alt and i < 2) else None)
                if b0 == 64: N('A', t, d * kk, m + tr - 12, dyn * 0.6, R53)
                t += d * kk
            for b in range(bar, bar + 2 * kk): acc(b, dyn=0.45 + 0.1 * (b0 >= 40), inner=(b0 != 24))
            bar += 2 * kk; i += 1
        while bar < b1: acc(bar, dyn=0.4); bar += 1
    # Amen
    sections.append(dict(t=float(END * 4), bar=END, title='Amen — A7 → D (録音の終わりの和音で)', sub='ラ 2・レ 4・ファ# 4 — 12:50:53 が閉じた和音で、もう一度閉じる'))
    N('S', END * 4, 2, 67, 1.0, R53, 'Amen'); N('S', END * 4 + 2, 2, 66, 1.0, R53); N('B', END * 4, 4, 45, 0.7, LOWSRC); N('A', END * 4 + 1, 3, 61, 0.5, R53)
    N('S', END * 4 + 4, 12, 66, 1.0, R53); N('A', END * 4 + 4, 12, 62, 0.6, R53); N('B', END * 4 + 4, 12, 45, 0.75, LOWSRC); N('B', END * 4 + 4.5, 11.5, 38, 0.5, LOWSRC)
    for q, m in enumerate((50, 57, 62, 66)): N('A', END * 4 + 8 + 0.5 * q, 8 - 0.5 * q, m, 0.45, R53 if m >= 54 else LOWSRC)
    for x in notes:
        if x.get('label'): entries.append(dict(t=x['t'], label=x['label'], v=x['v'], bar=int(x['beat'] // 4) + 1))
    return dict(SRC, nbars=NB, duration=float(NB * 4), bar_times=[4.0 * i for i in range(NB + 1)], notes=notes, extras=extras, entries=entries, sections=sections, harm=harm)

META = dict(SRC['meta'], title='Requiem BADA — XC · Continuazione 12:50:53', rec_order=[R53, LOWSRC], legend=['PF'], vname={'PF': '裏の主題'},
            subtitle='9/25 12:50:53 の終わりから続きを作曲 — 裏に LXXXIX のフーガとレクイエム (カノンなし)、ニ短調 / ニ長調',
            footer=['Intro (12:50:53 の終わりの実音) → M の連鎖 → M ×2 → M と転回 → M をオクターヴで → Amen (A7 → D)',
                    '裏: LXXXIX の I〜IV (フーガ 08:09・08:53、伸ばした主題、cp14_x4) を小さく。すべてピアノの実音。'])

if __name__ == '__main__':
    d = build(); d['meta'] = META
    bank = dict(recordings={}, samples=B89['samples'] + B87['samples'])
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; json.dump(bank, open(bank_out, 'w'), ensure_ascii=False)
    d['meta']['bank'] = bank_out
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras'] if e['v'] == 'PF']
    print('bars', d['nbars'], 'notes', len(d['notes']), 'extras', len(d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
    print('front S:', ' '.join(name_of(x['m']) for x in d['notes'] if x['v'] == 'S' and x.get('src') == R53)[:400])
