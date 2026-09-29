#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LX · Klavier solo (実音のピアノの独奏 — 心臓の鼓動と、始めの Klang I「Ruhe」を消して)
  楽譜は XLVIII〜LIX と同じで、4 声は録音から切り出したピアノの実音 (Introitus の 08:49 の録音もピアノの実音)。
  消したもの: 心臓の鼓動 (ドクン)、始めの Klang I「Ruhe」の 2 小節 (全員で長く伸ばす不協和音の和音 — シンセのように聞こえた所)。
    ドラム・シンセ・弦・オルガンもなし。ピアノの実音だけの独奏。
  Klang I は楽譜を書き出したあとで 2 小節まるごと切り取り (cut_bars)、後ろを前へ詰める: Introitus の録音が消えていくところから、そのまま Fuga I の主題へ。
  使い方: python compose_tablet60.py <bank37.json> [score_tablet60.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet58 as LVIII

K = LVIII.K

def cut_bars(d, b0, b1):
    """書き出した楽譜から小節 b0〜b1 (0 始まり、b1 は含まない) を切り取り、後ろを前へ詰める"""
    bt = d['bar_times']; t0, t1 = bt[b0], bt[b1]; D = t1 - t0; bpb = d['beats_per_bar']
    eps = 1e-3                                                                    # 区間の時刻は丸めて保存されている (切り捨て) ので 1 ms の余裕
    def keep_shift(items, tkey='t'):
        out = []
        for x in items:
            t = x[tkey]
            if t0 - eps <= t < t1 - eps: continue                                    # 切り取る区間に始まるもの
            if t < t0 - eps and 'd' in x and t + x['d'] > t0: x['d'] = t0 - t        # 区間にかかるものは区間の頭で止める
            if t >= t1 - eps:
                x[tkey] = round(t - D, 6)
                if 'beat' in x and isinstance(x['beat'], (int, float)): x['beat'] -= (b1 - b0) * bpb
                if 'bar' in x: x['bar'] -= (b1 - b0)
            out.append(x)
        return out
    d['notes'] = keep_shift(d['notes']); d['extras'] = keep_shift(d['extras'])
    for e in d['extras']:                                                         # 録音の抜粋が短くなったら、消えていく長さもそれに合わせる
        if e['v'] == 'REC' and 'fout' in e: e['fout'] = min(e['fout'], max(0.5, e['d'] * 0.3))
    d['sections'] = keep_shift(d['sections']); d['entries'] = keep_shift(d['entries'])
    d['harm'] = d['harm'][:b0 * bpb] + d['harm'][b1 * bpb:]
    d['bar_times'] = bt[:b0] + [round(t - D, 6) for t in bt[b1:]]
    d['nbars'] -= (b1 - b0); d['duration'] = round(d['duration'] - D, 6)
    return D

META = {k: v for k, v in LVIII.META.items() if k != 'heart_gain'}
META.update(
    title='Requiem BADA — LX · Klavier solo',
    subtitle='実音のピアノの独奏 — 心臓の鼓動と、始めの Klang「Ruhe」を消して (♩=56)',
    legend=['TB'], vname={},
    footer=['Introitus 08:49 → Fuga I (08:53 の主題) → Kyrie (コラール) → Klang II「Tränen」 → Fuga II (11:21 の主題) → Amen (ヘ長調)',
            '録音から切り出したピアノの実音だけの独奏 (ドラム・心臓の鼓動・シンセ・弦なし)。始めの Klang I「Ruhe」は切り取った。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet60.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=K.build, meta=META, extras=CT.extras, post=lambda P, events, extras: None)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LIX と同じ)
    D = cut_bars(d, 4, 6)                          # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 …
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノが長調の和音で包む'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('cut %.2f s;' % D, 'extras:', Counter(e['v'] for e in d['extras']), 'sections:', [s['title'][:12] for s in d['sections']])
