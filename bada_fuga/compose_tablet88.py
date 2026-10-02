#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXVIII · Summa dolce (LXXXVII をベースに、提出された全曲の主題を表に — 4 倍・8 倍・16 倍を使い分けて)
  ベース (後ろ): LXXXVII (Fiore dolce XVI: 12:50:53・08:53・LXXXVI + 16 倍のモチーフ) をそのまま、少し小さく (×0.7)
  表 (前): 提出された曲の主題を、ホ短調に移して、伸ばして重ねる (伸ばした音は 2 拍ごと — 16 倍は 4 拍ごと — に息をするように打ち直す)
    cp14_x8    — Contrapunctus BADA の主題 I (レ・ミ・ファ・ファ#・ソ・ラ・ソ・ファ・ミ・レ・ド#・レ、20 拍) → ×16 = 320 拍 = 曲全体 (80 小節) の背骨、アルト
    08:53      — 9/24 08:53 の主題 (ミ・ファ#・シ・ミ・ミ、8 拍、tablet60 の主題 ①)              → ×4、ソプラノ、小節 2〜 と 69〜 (再現)
    acceptance — タブレットの主題 (シ・ラ・ソ・ラ・ソ・ファ#、8 拍)                               → ×4、ソプラノ、小節 11〜
    requiem    — ディエス・イレ (ソ・ファ#・ソ・ミ・ファ#・レ・ミ、10 拍)                        → ×8、ソプラノ、小節 20〜
    symphony   — 歌う嘆きのバス (ミ・ファ#・ソ・レ#・ミ・ファ#・レ、10 拍)                       → ×8、バス、小節 40〜
    tablet60   — 主題 ② 11:21 (ミ・ド・レ#・ド・ミ・ド・ラ・ド・ラ・ミ、10 拍、ヘ短調から)         → ×4、ソプラノ、小節 40〜
    tablet     — 主題 ① 17:48 (レ・ミ・シ・シ・ド# → ホ短調で ミ・ファ#・ド#・ド#・レ#、10 拍)     → ×4、ソプラノ、小節 48〜
    tablet     — 主題 ⑤ 08:09 (シ・ラ・シ・ソ・ミ・ド#・シ → ド#・シ・ド#・ラ・ファ#・レ#・ド#、8 拍) → ×4、ソプラノ、小節 59〜
  入りの小節は前後 2 小節の範囲で、ベースの和音と半音でぶつかる長さがいちばん短い位置に。ぶつかる和音の間は打ち直さず余韻だけ。
  表の主題はベースより約 3〜4 dB 大きく (ステムで測って 0.5 → 0.28)。すべてピアノの実音 (声なし)。高音はミ 5 まで。
  使い方: python compose_tablet88.py <score_tablet87.json> [score_tablet88.json]
"""
import sys, os, json
import numpy as np
from compose import name_of

SRC = json.load(open(sys.argv[1]))
OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet88.json'
CH = {'Em7': [4, 7, 11, 2], 'Em9': [4, 7, 11, 2, 6], 'Gmaj7': [7, 11, 2, 6], 'Cmaj7': [0, 4, 7, 11], 'Cmaj9': [0, 4, 7, 11, 2], 'C6': [0, 4, 7, 9],
      'Am7': [9, 0, 4, 7], 'Am9': [9, 0, 4, 7, 11], 'D': [2, 6, 9], 'Dadd9': [2, 6, 9, 4], 'D6': [2, 6, 9, 11], 'B7': [11, 3, 6, 9], 'Bsus4': [11, 4, 6, 9],
      'B7b9': [11, 3, 6, 9, 0], 'Bm7': [11, 2, 6, 9], 'F#m7b5': [6, 9, 0, 4], 'Em': [4, 7, 11]}
RID = {'S': '20260923_080918', 'A': '20260924_085314', 'B': '20260925_130431'}
CAP = 76
E, F, Fs, G, Gs, A, B, C, Cs, D, Ds = 64, 65, 66, 67, 68, 69, 71, 72, 73, 74, 75
THEMES = [  # (ラベル, [(拍, 音高)], 倍率, 声部, 入りの小節 (基準), 中心の音高)
    ('主題 I ×16 (cp14_x8 / Contrapunctus BADA)', [(3, E), (1, Fs), (2, G), (1, Gs), (1, A), (2, B), (1, A), (1, G), (2, Fs), (1, E), (1, Ds), (4, E)], 16, 'A', 0, 66),
    ('08:53 の主題 ×4 (tablet60 ①)', [(1, E), (3, Fs), (1.5, B), (1.5, E + 12), (1, E + 12)], 4, 'S', 2, 70),
    ('タブレットの主題 ×4 (acceptance)', [(3, B), (0.5, A), (0.5, G), (2, A), (1, G), (1, Fs)], 4, 'S', 11, 69),
    ('ディエス・イレ ×8 (requiem)', [(2, G), (1, Fs), (1, G), (2, E), (1, Fs), (1, D), (2, E)], 8, 'S', 20, 68),
    ('嘆きのバス ×8 (symphony)', [(2, E), (1, Fs), (1, G), (2, Ds), (1, E), (1, Fs), (2, D)], 8, 'B', 40, 45),
    ('主題 ② 11:21 ×4 (tablet60)', [(0.5, E), (0.5, C), (0.5, Ds), (1.5, C), (0.5, E), (0.5, C), (0.5, A), (0.5, C), (1, A), (2, E), (2, E)], 4, 'S', 40, 70),
    ('主題 ① 17:48 ×4 (tablet)', [(2, E), (3, Fs), (1, Cs), (2, Cs), (2, Ds)], 4, 'S', 48, 68),
    ('主題 ⑤ 08:09 ×4 (tablet)', [(1, Cs), (1, B), (3, Cs), (2, A), (1, Fs), (0.5, Ds), (0.5, Cs)], 4, 'S', 59, 70),
    ('08:53 の主題 ×4 — 再現', [(1, E), (3, Fs), (1.5, B), (1.5, E + 12), (1, E + 12)], 4, 'S', 69, 70),
]

def build():
    harm = SRC['harm']; nb = SRC['nbars']; bt = SRC['bar_times']
    def sec(beat):
        i = min(int(beat // 4), len(bt) - 2); return bt[i] + (beat - 4 * i) / 4.0 * (bt[i + 1] - bt[i])
    notes = []
    for x in SRC['notes']: y = dict(x); y['dyn'] = round(x['dyn'] * 0.7, 3); notes.append(y)           # ベースは少し後ろへ
    extras = []
    for x in SRC['extras']: y = dict(x); y['gain'] = round(x['gain'] * 0.7, 4); y['label'] = None; extras.append(y)
    entries = [dict(e) for e in SRC['entries']]; sections = [dict(s) for s in SRC['sections']]
    def clash_pc(q, pc):
        pcs = CH[harm[min(q, len(harm) - 1)]]
        return pc not in pcs and any(min((pc - p) % 12, (p - pc) % 12) == 1 for p in pcs)
    def clash(th, k, b0):
        bad, t = 0.0, float(b0)
        for d, m in th:
            for q in range(int(t), int(min(t + d * k, nb * 4))):
                if clash_pc(q, m % 12): bad += 1
            t += d * k
        return bad
    for lab, th, k, v, bar, cen in THEMES:
        oc = 12 * min(range(-3, 3), key=lambda o: abs(np.mean([m for _, m in th]) + 12 * o - cen))
        cands = [bar] if bar == 0 else range(max(0, bar - 2), bar + 3)
        b0 = min(cands, key=lambda b: clash(th, k, 4 * b) + 0.5 * abs(b - bar)) * 4
        print('  %-40s bar %2d  clash %3d / %d beats' % (lab, b0 // 4, clash(th, k, b0), sum(d for d, _ in th) * k))
        step = 4 if k == 16 else 2
        t = float(b0); first = True
        for d, m in th:
            L = d * k; n_ = max(1, int(round(L / step)))
            for i in range(n_):
                beat = t + step * i
                if beat >= nb * 4 - 1: break
                if i and clash_pc(int(beat), m % 12): continue                  # ぶつかる和音の間は余韻だけ
                amp = 1.0 if i == 0 else 0.62 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1))
                mm = m + oc
                while mm > CAP: mm -= 12
                for o, g in ((0, 1.0), (-12, 0.45)) if v != 'B' else ((0, 1.0), (12, 0.4)):
                    extras.append(dict(v='PF', beat=round(beat, 3), dbeats=float(step), m=mm + o, gain=round(0.28 * g * amp, 4), rid=RID[v], rel=1.0,
                                       label=lab if first else None, layer='theme'))
                    first = False
            t += L
    for x in extras:
        if x.get('layer') == 'theme':
            x['t'] = round(sec(x['beat']), 3); x['d'] = round(sec(x['beat'] + x['dbeats']) - x['t'] + 0.9, 3)
            if x.get('label'): entries.append(dict(t=x['t'], label=x['label'], v=x['v'], bar=int(x['beat'] // 4) + 1)); x['label'] = None
    entries.sort(key=lambda e: e['t'])
    return dict(SRC, notes=notes, extras=extras, entries=entries, sections=sections)

META = dict(SRC['meta'], title='Requiem BADA — LXXXVIII · Summa dolce', vname={'PF': '主題'},
            subtitle='LXXXVII をベースに、提出された全曲の主題を表に — 4 倍・8 倍・16 倍を使い分けて (ホ短調)',
            footer=['背骨: Contrapunctus BADA の主題 I ×16 (曲全体)。表: 08:53 ×4 → acceptance ×4 → ディエス・イレ ×8 → 嘆きのバス ×8 + 11:21 ×4 → 17:48 ×4 → 08:09 ×4 → 08:53 ×4',
                    'ベースは LXXXVII (Fiore dolce XVI)。すべてピアノの実音 (声なし)。高音はミ 5 まで。'])

if __name__ == '__main__':
    d = build(); d['meta'] = META
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras']]
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', len(d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
