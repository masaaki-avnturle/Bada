#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CVIII · Fiore dolce senza sospiri (LXXXV から喘ぎ声を消して)
  LXXXV (→ LXXXVI) で「喘ぎ声」のように聞こえていたのは、音源の 1 音のうち、立ち上がりが遅く減衰せずにふくらむ音
  (ペダルの響き・うなり・声の混じった音を切り出したもの) を、synth が持続部のループで伸ばしたとき — 息を吸うように聞こえる。ここでは:
    - clean_bank.py で、立ち上がりが 0.12 秒以内で、ふくらまない (減衰する) 1 音だけを残した音源 (bank85q) で鳴らす
    - piano_decay で、長い音もピアノのように自然に減衰させる (ループで伸ばした持続音を残さない)
    - 録音そのもの (LXXXV の Intro の 11:21 の実音) は使わない (LXXXVI と同じ)
  曲 (旋律・和音・形式) は LXXXV・LXXXVI と同じ (compose_tablet86.build を使う)
  使い方: python compose_tablet108.py <bank85q.json (clean_bank.py の出力)> [score_tablet108.json]
"""
import sys, json
OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet108.json'
sys.argv = [sys.argv[0], sys.argv[1], OUT]
import compose_tablet86 as T86
from compose import name_of

if __name__ == '__main__':
    d = T86.build()
    d['meta'] = dict(T86.META, bank=sys.argv[1], piano_decay=2.2,
                     title='Requiem BADA — CVIII · Fiore dolce senza sospiri',
                     subtitle='LXXXV から喘ぎ声を消して — ふくらむ音を外したピアノの 1 音だけで、長い音は自然に減衰 (坂本龍一の 2 曲の曲調 × 11 曲の録音の旋律、ホ短調)',
                     footer=['Intro (分散和音) → I. Sweet (循環和音) → II. Flower (五音音階) → III. Fuga dolce (カノン) → IV. Sweet ritorno → Coda (Em9)',
                             '旋律はすべてユーザーの 11 曲の録音から。音源は、立ち上がりが速く減衰する 1 音だけを残した表 (bank85q)。声なし。'])
    for x in d['notes']:
        if x['v'] != 'S': x['dyn'] = round(x['dyn'] * 1.25, 3)
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']]
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
