#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXVII · Fiore dolce XVI (9/25 12:50:53・9/24 08:53・LXXXVI を主体に、バックで LXXX・LXXXI・LXXIV のモチーフを 16 倍に伸ばして)
  主体 (前):
    Intro (18 小節, ♩=60) — 9/25 12:50:53 (ロ短調のピアノ、4 分 24 秒) と 9/24 08:53 の録音から、いちばん歌う 16 拍の旋律を採り (LXXXV と同じ方法)、
      ホ短調で、交互に・重ねて・カノンで歌う。伴奏は LXXXVI と同じ循環和音 (Em7 → Cmaj7 → Am7 → B7)
    本体 (62 小節) — LXXXVI (Fiore dolce, ピアノだけ) をそのまま: 11 曲の録音の旋律 × 坂本龍一の 2 曲の曲調
  バック (後ろ、16 倍):
    LXXX のモチーフ — 08:53 の主題 (ミ・ファ#・シ・ミ・ミ、8 拍)        → 128 拍 (32 小節) に伸ばして、低音 (ミ 2〜ミ 3) で   小節 0〜32
    LXXXI のモチーフ — 9/28 の代表の節 (レ・ミ・ミ・シ・ド・レ#・ミ、ホ短調に移して) → 128 拍に伸ばして、テノール (シ 2〜ミ 4) で      小節 ~24〜56
    LXXIV のモチーフ — 主題 I (08:09: ミ・ファ#・ソ・ソ#・ラ、8 拍)       → 128 拍に伸ばして、低音で                              小節 ~48〜80
    伸ばした音は 2 拍ごとに息をするように打ち直す (頭を強く)。入りの小節は、前の和音と半音でぶつかる長さがいちばん短い位置に (数小節の範囲で)。
  音源はピアノだけの録音 (08:09・08:53・08:49・13:04・12:50:53) の 1 音。声なし。高音はミ 5 まで。
  使い方: python compose_tablet87.py <bank85.json> <bank87.json (12:50:53)> <score_tablet86.json> [score_tablet87.json]
"""
import sys, os, json
import numpy as np
from compose import name_of
import compose_tablet86 as T86                     # phrase / to_key / fit_chord / CH / SWEET (sys.argv[1] = bank85)

B87 = json.load(open(sys.argv[2])); R53 = '20260925_125053'
T86.REC[R53] = B87['recordings'][R53]; T86.KEY[R53] = (11, 'm')
SRC86 = json.load(open(sys.argv[3]))
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet87.json'
R24 = '20260924_085314'; ACC = T86.ACC; CH = T86.CH
INTRO = 18; SHIFT = INTRO * 4                      # 本体 (LXXXVI) は 72 拍あとから
EMIN = T86.EMIN
# バックのモチーフ (ホ短調、8 拍): (長さ, 音高)
M80 = [(1, 52), (3, 54), (1.5, 59), (1.5, 64), (1, 64)]                       # LXXX: 08:53 の主題 ミ・ファ#・シ・ミ・ミ
M81 = [(1, 50), (1, 52), (1, 52), (1, 47), (2, 48), (1, 51), (1, 52)]         # LXXXI: 9/28 の代表の節をホ短調に (レ・ミ・ミ・シ・ド・レ#・ミ)
M74 = [(3, 52), (1, 54), (2, 55), (1, 56), (1, 57)]                           # LXXIV: 主題 I (08:09) ミ・ファ#・ソ・ソ#・ラ
MOTIFS = [('08:53 の主題 ×16 (LXXX)', M80, -12, (0, 1), 'B'), ('9/28 の節 ×16 (LXXXI)', M81, 0, (20, 29), 'T'), ('主題 I ×16 (LXXIV)', M74, -12, (44, 50), 'B')]

def build():
    nb86 = SRC86['nbars']; total = INTRO + nb86
    bt = [4.0 * k for k in range(INTRO)] + [t + SHIFT for t in SRC86['bar_times']]
    def sec(beat):
        i = min(int(beat // 4), len(bt) - 2); return bt[i] + (beat - 4 * i) / 4.0 * (bt[i + 1] - bt[i])
    notes, extras, entries, sections, harm = [], [], [], [], []
    def N(v, beat, dur, m, dyn, src, label=None):
        notes.append(dict(v=v, beat=round(beat, 3), dbeats=round(dur, 3), m=int(m), dyn=round(dyn, 3), src=src, label=label, det=1.0, role=''))
    # ---- Intro: 12:50:53 と 08:53 の旋律
    ph53, s53 = T86.phrase(R53); ph53 = T86.to_key(ph53, R53, EMIN)
    ph24, s24 = T86.phrase(R24); ph24 = T86.to_key(ph24, R24, EMIN)
    print('12:50:53 from %.1fs:' % s53, ' '.join(name_of(m) for _, _, m in ph53)); print('08:53 from %.1fs:' % s24, ' '.join(name_of(m) for _, _, m in ph24))
    sections.append(dict(bar=0, title='Intro — 9/25 12:50:53 と 9/24 08:53 の旋律 (ホ短調)', sub='バックで LXXX の 08:53 の主題が 16 倍に伸びる — 2 つの旋律が交互に、重ねて、カノンで'))
    mel = []
    def put(ph, b0, v, oc, src, lab, until=None):
        for i, (b, d, m) in enumerate(ph):
            if until is not None and b0 + b >= until: break
            mm = m + oc
            while mm > 76: mm -= 12
            N(v, b0 + b, d, mm, 1.0 if v == 'S' else 0.8, src, lab if i == 0 else None); mel.append((b0 + b, d, mm))
    put(ph53, 8, 'S', 0, R53, '9/25 12:50:53 の旋律'); put(ph24, 24, 'S', 0, R24, '9/24 08:53 の旋律')
    put(ph53, 40, 'S', 0, R53, None); put(ph24, 40, 'T', -12, R24, '08:53 (重ねて)')
    put(ph24, 56, 'S', 0, R24, None); put(ph53, 60, 'T', -12, R53, '12:50:53 (カノン)', until=SHIFT)
    t = 0.0; bg = []
    for d, m in M80: bg.append((t, d * 16, m - 12 + 12)); t += d * 16                 # 伸ばした主題 (オクターヴは和音の選びに関係ない)
    for k in range(INTRO):
        bb = 4 * k; c = T86.fit_chord(mel + bg, bb, T86.SWEET[k % 4]); harm += [c] * 4
        if k < 1: continue
        pcs = CH[c]; r = 40 + (pcs[0] - 40) % 12; dyn = 0.42 * min(1.0, 0.5 + 0.1 * k)
        N('B', bb, 2.5, r, dyn * 1.25, ACC['B']); N('B', bb + 2.5, 1.5, r + 7 if r + 7 <= 52 else r - 5, dyn * 0.9, ACC['B'])
        voi = sorted(52 + (p - 52) % 12 for p in pcs[1:] + pcs[:1])[:4]
        for i, m in enumerate([voi[0], voi[1], voi[2], voi[1], voi[-1], voi[1], voi[2]]):
            t = bb + 0.5 * (i + 1)
            if any(b <= t < b + d and min((m - mm) % 12, (mm - m) % 12) == 1 for b, d, mm in mel): continue
            N('T' if m < 58 else 'A', t, 1.5, m, dyn * (0.9 if i % 2 else 1.0), ACC['T'] if m < 58 else ACC['A'])
    # ---- 本体: LXXXVI をそのまま 72 拍あとへ
    for x in SRC86['notes']:
        y = dict(x); y['beat'] = round(x['beat'] + SHIFT, 3); notes.append(y)            # dyn は LXXXVI で決めたまま
    harm += SRC86['harm']
    for s in SRC86['sections']: sections.append(dict(bar=s['bar'] + INTRO, title=s['title'], sub=s['sub']))
    # ---- バック: 3 つのモチーフを 16 倍に
    def clash(mot, oc, b0):
        bad, t = 0.0, b0
        for d, m in mot:
            for q in range(int(t), int(t + d * 16)):
                if q >= len(harm): break
                pcs = CH[harm[q]]; pc = (m + oc) % 12
                if pc not in pcs and any(min((pc - p) % 12, (p - pc) % 12) == 1 for p in pcs): bad += 1
            t += d * 16
        return bad
    for lab, mot, oc, (lo, hi), v in MOTIFS:
        b0 = min(range(lo, hi + 1), key=lambda b: clash(mot, oc, 4 * b) + 0.3 * (b - lo)) * 4
        print('  %-22s start bar %d clash %d' % (lab, b0 // 4, clash(mot, oc, b0)))
        t = float(b0); first = True
        for d, m in mot:
            L = d * 16; n_ = int(round(L / 2))
            for i in range(n_):
                if t + 2 * i >= total * 4 - 1: break
                amp = 1.0 if i == 0 else 0.6 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1))
                q = int(t + 2 * i); pcs = CH[harm[min(q, len(harm) - 1)]]; pc = (m + oc) % 12
                if i and pc not in pcs and any(min((pc - p) % 12, (p - pc) % 12) == 1 for p in pcs): continue      # 半音でぶつかる和音の間は打ち直さず、余韻だけ
                for o, g in ((0, 0.6), (12, 0.25)) if v == 'B' else ((0, 0.6),):
                    extras.append(dict(v='PF', beat=round(t + 2 * i, 3), dbeats=2.0, m=m + oc + o, gain=round(0.42 * g * amp, 4), rid=ACC['B'] if v == 'B' else ACC['T'],
                                       rel=1.0, label=lab if first else None, layer='x16'))
                    first = False
            t += L
    for x in notes + extras:
        x['t'] = round(sec(x['beat']), 3); x['d'] = round(sec(x['beat'] + x['dbeats']) - x['t'], 3)
        if x['v'] == 'PF': x['d'] = round(x['d'] + 0.9, 3)
    for x in notes + extras:
        if x.get('label'): entries.append(dict(t=x['t'], label=x['label'], v=x['v'], bar=int(x['beat'] // 4) + 1))
    for s in sections: s['t'] = round(bt[s['bar']], 3)
    for x in extras: x['label'] = None
    return dict(bpm=60, beats_per_bar=4, nbars=total, duration=round(bt[-1], 3), bar_times=[round(x, 3) for x in bt], notes=notes, entries=entries,
                sections=sections, harm=harm, extras=extras)

META = {
    'style': 'recsampler', 'bank': None, 'rec_order': [R53] + list(ACC.values()), 'piano_decay': 2.6, 'reverb': [5.5, 2.2, 0.45],
    'title': 'Requiem BADA — LXXXVII · Fiore dolce XVI',
    'subtitle': '12:50:53・08:53・LXXXVI を主体に — バックで LXXX・LXXXI・LXXIV のモチーフを 16 倍に (ホ短調)',
    'legend': ['PF'], 'vname': {'PF': 'モチーフ ×16'},
    'footer': ['Intro (12:50:53 と 08:53 の旋律) → LXXXVI: Sweet → Flower → Fuga dolce → Sweet ritorno → Coda ｜ バック: 08:53 の主題 ×16 → 9/28 の節 ×16 → 主題 I ×16',
               'すべてピアノの実音 (声なし)。高音はミ 5 まで。'],
}

if __name__ == '__main__':
    d = build()
    bank = dict(recordings={}, samples=[x for x in T86.BANK['samples'] if x['rid'] in ACC.values()] + B87['samples'])
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; json.dump(bank, open(bank_out, 'w'), ensure_ascii=False)
    d['meta'] = dict(META, bank=bank_out)
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras']]
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', len(d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
