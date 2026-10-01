#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXIV · Symphonia (LXVIII〜LXXIII を 1 つの交響曲に組み立てる)
  LXVIII〜LXXIII はどれも ♩=60 (1 小節 = 4 秒) で、主題曲 (ピアノの実音の録音) の主題を 16 倍 (LXVIII は 8 倍) に伸ばして打ち直し、
  先程の曲をバックに流し、保続音の上でフーガの主題が入る — 同じ作りなので、区間の切れ目 (小節の頭) で切って並べると打鍵の脈が途切れずにつながる。
  その楽譜をそのまま切り出して 1 つの楽譜にまとめ (音・録音の抜粋・区間・和声・主題の入りを時間をずらして写す)、もう一度合成する。
  楽章 (楽章の間は 1 小節の休み):
    I.   Introduzione e Allegro (ホ短調)   — LXVIII の Adagio ×8 (フーガ入り) → LXIX (主題曲 9/23 08:09) の Introitus・×16・Fuga
    II.  Adagio lamentoso (変ロ短調)       — LXX (主題曲 9/23 08:06) の Introitus・×16・Lacrimosa
    III. Scherzo fugato (ヘ短調)           — LXXI (主題曲 9/25 12:46、下りる主題) の ×16・Fuga → LXXII (上る主題) の Fuga・Lacrimosa
    IV.  Finale a tre soggetti (ヘ短調 → ホ短調 → ホ長調) — LXXIII (08:49・08:53・08:09) の Introitus・×16・Interludium・三重フーガ・×16・Amen
  使い方: python compose_tablet74.py <bank74.json> <scores.json ({"68": "…/score_tablet68.json", …})> [score_tablet74.json]
"""
import sys, re, json, copy

BANK, SCORES = sys.argv[1], json.load(open(sys.argv[2]))
OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet74.json'
GAP = 4.0                                          # 楽章の間の休み (1 小節)
MOVEMENTS = [
    ('I. Introduzione e Allegro (ホ短調)', [('68', 384, 544), ('69', 0, 224)]),
    ('II. Adagio lamentoso (変ロ短調)', [('70', 0, 160), ('70', 224, 256)]),
    ('III. Scherzo fugato (ヘ短調)', [('71', 32, 224), ('72', 160, 256)]),
    ('IV. Finale a tre soggetti (ヘ短調 → ホ短調 → ホ長調)', [('73', 0, 184), ('73', 312, 548)]),
]
ROMAN = {'68': 'LXVIII', '69': 'LXIX', '70': 'LXX', '71': 'LXXI', '72': 'LXXII', '73': 'LXXIII'}

def shift(x, dt):
    x = copy.deepcopy(x); x['t'] = round(x['t'] + dt, 4)
    if 'beat' in x and isinstance(x['beat'], (int, float)): x['beat'] = round(x['beat'] + dt, 4)    # ♩=60: 1 拍 = 1 秒
    x.pop('bar', None)
    return x

def main():
    src = {k: json.load(open(v)) for k, v in SCORES.items()}
    out = dict(bpm=60, beats_per_bar=4, notes=[], extras=[], entries=[], sections=[], harm=[])
    T = 0.0; rec_order = []
    for mi, (mtitle, segs) in enumerate(MOVEMENTS):
        for si, (k, t0, t1) in enumerate(segs):
            d = src[k]; dt = T - t0
            for n in d['notes']:
                if t0 - 1e-3 <= n['t'] < t1 - 1e-3: out['notes'].append(shift(n, dt))
            for e in d['extras']:
                if e['v'] == 'REC':
                    a, b = max(e['t'], t0), min(e['t'] + e['d'], t1)
                    if b - a < 1.0: continue
                    r = 2 ** (e.get('semis', 0) / 12.0); x = shift(e, dt)
                    x['t'] = round(a + dt, 4); x['d'] = round(b - a, 4); x['off'] = round(e['off'] + (a - e['t']) * r, 4); x['beat'] = x['t']; x['dbeats'] = x['d']
                    if b < e['t'] + e['d'] - 1e-3: x['fout'] = min(2.0, x['d'] / 3)                       # 切れ目で切った録音は静かに消す
                    if a > e['t'] + 1e-3: x['fin'] = min(1.0, x['d'] / 4)
                    out['extras'].append(x)
                elif t0 - 1e-3 <= e['t'] < t1 - 1e-3: out['extras'].append(shift(e, dt))
            for e in d['entries']:
                if t0 - 1e-3 <= e['t'] < t1 - 1e-3: out['entries'].append(shift(e, dt))
            secs = [s for s in d['sections'] if t0 - 1e-3 <= s['t'] < t1 - 1e-3]
            for j, s in enumerate(secs):
                core = re.sub(r'^[IVX]+\. ', '', s['title'])                 # もとの曲の楽章番号は外す
                x = shift(s, dt); x['title'] = '%s %s' % (mtitle.split(' ')[0], core)
                x['sub'] = '%s — %s' % (ROMAN[k], s.get('sub', ''))
                if si == 0 and j == 0: x['title'] = '%s — %s' % (mtitle.split(' (')[0], core)
                out['sections'].append(x)
            out['harm'] += d['harm'][int(t0):int(t1)]
            T += t1 - t0
            for r in d['meta'].get('rec_order', []):
                if r not in rec_order: rec_order.append(r)
        if mi < len(MOVEMENTS) - 1:
            out['harm'] += [out['harm'][-1]] * int(GAP); T += GAP
    out['duration'] = round(T, 4); out['nbars'] = int(round(T / 4.0))
    out['bar_times'] = [4.0 * i for i in range(out['nbars'] + 1)]
    m0 = src['73']['meta']
    out['meta'] = {k: v for k, v in m0.items() if k not in ('title', 'subtitle', 'footer', 'legend', 'vname', 'bank', 'rec_order')}
    out['meta'].update(bank=BANK, rec_order=rec_order,
        title='Requiem BADA — LXXIV · Symphonia (LXVIII〜LXXIII)',
        subtitle='主題曲 (ピアノの実音) を 16 倍に伸ばし、先程の曲をバックに — フーガを醸すレクイエムの交響曲 (4 楽章、♩=60)',
        legend=['PF'], vname={'PF': 'ピアノ'},
        footer=['I. ホ短調 (LXVIII・LXIX) → II. 変ロ短調 (LXX) → III. ヘ短調 (LXXI・LXXII) → IV. ヘ短調 → ホ短調 → ホ長調 (LXXIII)',
                '主題曲: 9/23 08:09・08:06、9/25 12:46、9/24 08:49・08:53 の録音。すべてピアノの実音。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('duration %.1f s (%d:%02d), notes %d, extras %s, sections %d' % (T, T // 60, T % 60, len(out['notes']), dict(Counter(e['v'] for e in out['extras'])), len(out['sections'])))
    for s in out['sections']: print('  %5.0f  %s' % (s['t'], s['title'][:60]))

if __name__ == '__main__':
    main()
