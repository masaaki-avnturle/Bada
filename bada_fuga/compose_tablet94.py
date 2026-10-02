#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCIV · Fuga per augmentationem (Klavier) (XCIII の全音符を 2 倍に伸ばして、フーガを醸す曲に)
  XCIII (piano_solo_8x の主題による Contrapunctus XIV、すべて実音のピアノ) をもとに:
    - 全音符を 2 倍に (拡大 — 『フーガの技法』Contrapunctus VII "per augmentationem" のように): すべての音の長さと時刻を 2 倍に。
      88 小節 → 176 小節 (♩=60 のまま、11 分 44 秒)。4 拍より長くなった音は 2 拍ごとに打ち直す (ピアノなので)
    - Prologo / Epilogo の piano_solo_8x の実音は速さを変えず、2 倍の長さの窓を流す (Prologo: 2186〜2250 秒 = 主題 I を採った所の全部、Epilogo: 2250〜2346 秒)
    - フーガを醸す: 伸ばした (×2) フーガの上に、主題を元の速さ (×1) で重ねる — 同じ主題の ×2 と ×1 が同時に鳴る「拡大カノン」:
        Sectio I 低音の拡大 (×4)   主題 II ×1 が高く 2 回
        Sectio I 属音の保続        主題 I ×1 のストレッタ (アルト → ソプラノ → テノール)
        Sectio II エピソード        B-A-C-H ×1 が先ぶれで (ソプラノ、テノール)
        Sectio III 三重 1          主題 I ×1 がソプラノで 2 回 (×2 の主題 I と拡大カノン)
        Sectio III 拡大の上        主題 II ×1 (アルト) ×2 回 → B-A-C-H ×1 (ソプラノ)
        Epilogo (実音の上)         主題 I ×1 がアルトで、反行形が続いて、消える
    - 声なし (XCIII にも声はない)
  使い方: python compose_tablet94.py <score_tablet93.json> [score_tablet94.json]
"""
import sys, json
from collections import Counter

SRC = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet94.json'
K = 2                                                          # 拡大の倍率
R = '20260924_085314'
S1 = [(1.5, 70), (0.5, 64), (1, 70), (1, 69), (1, 62), (1, 69), (0.5, 67), (0.5, 65), (1, 62)]
S2 = [(0.5, m) for m in (72, 67, 62, 65, 64, 62, 64, 60, 62, 64, 70, 69, 67, 65, 64, 61)]
S3 = [(2, 70), (2, 69), (2, 72), (2, 71)]
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
VN = {'S': 'Soprano', 'A': 'Alto', 'T': 'Tenore'}
# (元の小節, 拍, 主題, 移調, 声部 (表示), 大きさ, ラベル)
FUGA = [
    (27, 0, S2, 12, 'S', 0.30, '主題 II ×1 — 拡大の上で'), (29, 0, S2, 7 + 12, 'S', 0.30, '主題 II ×1 答唱'),
    (31, 0, S1, 0, 'A', 0.32, '主題 I ×1 ストレッタ (保続の上)'), (31, 2, S1, 12, 'S', 0.30, '主題 I ×1 ストレッタ'), (32, 0, S1, -12, 'T', 0.30, '主題 I ×1 ストレッタ'),
    (42, 0, S3, 12, 'S', 0.26, 'B-A-C-H ×1 — 先ぶれ'), (43, 0, S3, -12, 'T', 0.26, 'B-A-C-H ×1 — 先ぶれ'),
    (64, 0, S1, 12, 'S', 0.34, '主題 I ×1 — 拡大カノン'), (65, 0, S1, 12, 'S', 0.32, '主題 I ×1 — 拡大カノン'),
    (68, 0, S2, 0, 'A', 0.32, '主題 II ×1 — 拡大の上で'), (69, 0, S2, 0, 'A', 0.32, '主題 II ×1'), (70, 0, S3, 12, 'S', 0.34, 'B-A-C-H ×1'),
    (78, 0, S1, 0, 'A', 0.24, '主題 I ×1 — 醸す (実音の上)'), (80, 0, invert(S1), 0, 'A', 0.18, '主題 I ×1 (反行)'), (82, 0, S1, -12, 'T', 0.12, '主題 I ×1 — 消える'),
]

def stretch(d):
    notes, extras = [], []
    for n in d['notes']:
        t, dd = n['t'] * K, n['d'] * K
        if dd <= 4.0 + 1e-6:
            notes.append(dict(n, t=round(t, 4), d=round(dd, 4), beat=round(n['beat'] * K, 4))); continue
        q, first = 0.0, True                                                     # 4 拍より長い音: 2 拍ごとに打ち直す
        while q < dd - 1e-6:
            L = min(2.0, dd - q)
            notes.append(dict(n, t=round(t + q, 4), d=round(L, 4), beat=round(n['beat'] * K + q, 4), label=n['label'] if first else None,
                              dyn=round(n.get('dyn', 1.0) * (1.0 if first else 0.72), 4)))
            q += 2.0; first = False
    for e in d['extras']:
        if e['v'] == 'REC':
            dd = e['dbeats'] * K
            extras.append(dict(e, beat=e['beat'] * K, dbeats=dd, t=e['t'] * K, d=float(dd), fout=e['fout'] * K, gain=round(e['gain'] * 0.9, 3),
                               tag=e['tag'].replace('2186 秒から', '2186〜2250 秒 (主題 I を採った所の全部)').replace('2250 秒から', '2250〜2346 秒')))
            continue
        t, dd = e['t'] * K, e['d'] * K
        if dd <= 4.4 + 1e-6:
            extras.append(dict(e, t=round(t, 4), d=round(dd, 4), beat=round(e['beat'] * K, 4), dbeats=round(e['dbeats'] * K, 4))); continue
        q, first = 0.0, True
        while q < dd - 1e-6:
            L = min(2.0, dd - q)
            extras.append(dict(e, t=round(t + q, 4), d=round(L + 0.3, 4), beat=round(e['beat'] * K + q, 4), dbeats=round(L, 4), gain=round(e['gain'] * (1.0 if first else 0.72), 4)))
            q += 2.0; first = False
    return notes, extras

def brew(d, extras, entries):
    """伸ばしたフーガの上に、主題を元の速さ (×1) で"""
    for bar, beat, subj, tr, v, g, lab in FUGA:
        b0 = (bar * 4 + beat) * K; t = float(b0); first = True
        for dd, m in subj:
            extras.append(dict(v='PF', t=round(t, 4), d=round(dd + 0.25, 4), beat=round(t, 4), dbeats=dd, m=m + tr, gain=g, rid=R, rel=0.5,
                               label=('%s · %s' % (lab, VN[v])) if first else None, layer='fuga'))
            t += dd; first = False
        entries.append(dict(t=float(b0), label=lab, v=v, bar=int(b0 // 4) + 1))

if __name__ == '__main__':
    d = json.load(open(SRC))
    notes, extras = stretch(d)
    entries = [dict(e, t=e['t'] * K, bar=(e['bar'] - 1) * K + 1) for e in d['entries']]
    brew(d, extras, entries); entries.sort(key=lambda e: e['t'])
    nb = d['nbars'] * K
    d.update(notes=notes, extras=extras, entries=entries, nbars=nb, duration=d['duration'] * K, bar_times=[4.0 * i for i in range(nb + 1)],
             harm=[c for c in d['harm'] for _ in range(K)])
    d['sections'] = [dict(s, t=s['t'] * K, bar=(s['bar'] - 1) * K + 1) for s in d['sections']]
    for s in d['sections']: s['sub'] = s['sub'] + ' — 全音符を 2 倍に'
    d['sections'][0]['sub'] = '主題 I を採った 2186〜2250 秒の全部 (+5、速さは変えず) — 実音だけ'
    d['sections'][-1]['sub'] = '沈黙のあと、piano_solo_8x の実音 (2250〜2346 秒、+5) — その上で主題 I ×1 がもう一度、反行して、消える'
    d['meta'] = dict(d['meta'], pause_bar=d['meta']['pause_bar'] * K,
                     title='Requiem BADA — XCIV · Fuga per augmentationem (Klavier)',
                     subtitle='XCIII の全音符を 2 倍に伸ばして — 伸ばした Contrapunctus XIV の上に、主題を元の速さで重ねてフーガを醸す (ニ短調, ♩=60)',
                     legend=['PF'], vname={'PF': '×1 の主題 / 管 → ピアノ'},
                     footer=['Prologo (実音だけ) → Sectio I ×2 (拡大の上に主題 II ×1、保続の上に主題 I ×1 のストレッタ) → Sectio II ×2 (B-A-C-H の先ぶれ) → Sectio III ×2 (拡大カノン) → 途切れる → Epilogo (実音 + 主題 I ×1)',
                             'すべて 9/24 08:53 の録音から切り出したピアノの 1 音と、piano_solo_8x の実音。4 拍より長い音は 2 拍ごとに打ち直す。声なし。'])
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', nb, 'duration', d['duration'], 'notes', len(notes), 'extras', Counter(e['v'] for e in extras), 'fuga notes', sum(1 for e in extras if e.get('layer') == 'fuga'))
