#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCIII · Contrapunctus XIV sinfonico (Klavier) (XCII を、すべて実音のピアノで弾いているように)
  楽譜・形式・主題は XCII とまったく同じ。管弦楽の音をすべて、録音から切り出したピアノの 1 音 (bank85、9/24 08:53 の音) で弾き直す:
    - 弦 5 部 (4 声 S/A/T/B) → そのままピアノの 4 声 (低音は 1 オクターヴ下を薄く重ねる、synth の recsampler と同じ)
    - 木管・金管 (Fl・Ob・Cl・Hn・Tp・Tb の extras) → ピアノ。弦と同じ高さを同時に重ねていた所 (入りの重ね) は 1 つの鍵盤に
    - ティンパニは外す。低弦の保続 (Cb・Vc の extras) は低いピアノの 1 音に
    - 同時に鳴らす音は 7 つまで (両手で弾ける厚さに: 4 声は必ず、残りは強い順)。ホルンの和音の持続は 2 拍ごとに打ち直すピアノの和音に
    - Prologo / Epilogo の piano_solo_8x の実音はもともとピアノなのでそのまま
  使い方: python compose_tablet93.py <score_tablet92.json> <bank85.json> [score_tablet93.json]
"""
import sys, json
from collections import Counter

SRC, BANK = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet93.json'
R = '20260924_085314'                                   # ピアノの音: 9/24 08:53 の録音から切り出した 1 音
POLY = 7
WIND = {'FL': 0.95, 'WW': 0.9, 'CL': 0.85, 'HN': 0.7, 'TR': 1.0, 'TB': 0.9, 'CB': 0.8, 'VC': 0.7}   # 楽器ごとのピアノでの大きさ

def convert(d):
    notes = []
    for n in d['notes']:
        notes.append(dict(n, src=R, dyn=round(float(n.get('dyn', 1.0)) * 1.1, 4)))
    notes.sort(key=lambda n: n['t'])
    # 木管・金管・低弦 → ピアノ (PF extras)
    cand = []
    for e in d['extras']:
        if e['v'] not in WIND: continue
        g = float(e.get('gain', 0.3)) / 0.4 * WIND[e['v']]
        cand.append(dict(t=e['t'], d=e['d'], m=int(e['m']), g=g, src=e['v'], beat=e['beat'], dbeats=e['dbeats']))
    cand.sort(key=lambda c: (c['t'], -c['g']))
    # 同じ高さを同時に弾いている弦があれば、その鍵盤は 1 つ (弦の音を残す)
    by_m = {}
    for n in notes: by_m.setdefault(n['m'], []).append(n['t'])
    out, last = [], {}
    for c in cand:
        if any(abs(t - c['t']) < 0.06 for t in by_m.get(c['m'], ())): continue
        j = last.get(c['m'])
        if j is not None and out[j]['t'] + 0.06 > c['t']: out[j]['g'] = max(out[j]['g'], c['g']); continue      # ほぼ同時の同じ音
        if j is not None and out[j]['t'] + out[j]['d'] > c['t']: out[j]['d'] = max(0.1, c['t'] - out[j]['t'])    # 前の同じ音は次の打鍵の前で止める
        last[c['m']] = len(out); out.append(c)
    # 同時の打鍵は 7 つまで (4 声は必ず、残りは強い順)
    res, i = [], 0
    while i < len(out):
        grp = [out[i]]; i += 1
        while i < len(out) and out[i]['t'] - grp[0]['t'] < 0.04: grp.append(out[i]); i += 1
        nv = sum(1 for n in notes if abs(n['t'] - grp[0]['t']) < 0.05 or (n['t'] < grp[0]['t'] < n['t'] + n['d']))
        room = max(0, POLY - nv)
        if len(grp) > room:
            grp = sorted(grp, key=lambda c: -c['g'])[:room]
        res += grp
    pf = [dict(v='PF', t=round(c['t'], 4), d=round(max(0.12, c['d']), 4), beat=round(c['beat'], 4), dbeats=round(c['dbeats'], 4), m=c['m'],
               gain=round(0.24 * min(1.6, c['g']), 4), rid=R, rel=0.4, label=None, src_inst=c['src']) for c in res]
    keep = [dict(e, gain=round(e['gain'] * 0.33, 3)) for e in d['extras'] if e['v'] == 'REC']      # 実音はピアノに合わせて小さく (管弦楽より全体が小さいので)
    return notes, pf + keep

if __name__ == '__main__':
    d = json.load(open(SRC))
    notes, extras = convert(d)
    d['notes'] = notes; d['extras'] = extras
    d['meta'] = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42], 'pause_bar': d['meta'].get('pause_bar'),
                 'title': 'Requiem BADA — XCIII · Contrapunctus XIV (Klavier)',
                 'subtitle': 'XCII を、すべて実音のピアノで — piano_solo_8x の主題による Contrapunctus XIV、管弦楽をピアノで弾き直して (ニ短調, ♩=60)',
                 'legend': ['PF'], 'vname': {'PF': '管 → ピアノ'},
                 'footer': ['Prologo (piano_solo_8x の実音) → Sectio I: 主題 I → Sectio II: 主題 II、I+II の二重フーガ → Sectio III: B-A-C-H、三重フーガ → 途切れる → Epilogo (実音)',
                            '弦の 4 声も木管・金管もすべて、9/24 08:53 の録音から切り出したピアノの 1 音で。ティンパニなし。同時の打鍵は 7 つまで。声なし。']}
    for sec in d['sections']:
        sec['sub'] = sec['sub'].replace('(弦)', '(ピアノ)').replace('(オーボエ)', '').replace('(ホルン)', '').replace('(木管が加わる)', '').replace('(金管)', '').replace('、ティンパニ', '').replace('低弦の レ とティンパニが近づく', '低い レ が近づく')
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('notes', len(notes), 'extras', Counter(e['v'] for e in extras), 'from winds', Counter(e.get('src_inst') for e in extras if e['v'] == 'PF'))
