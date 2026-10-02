#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CV · Fiore e Fuga 9/23 per augmentationem XVI (CIV を 16 倍に伸ばして、同じようにフーガを醸す曲に)
  CIV (76 小節、5 分 4 秒) の **すべての 3 小節** (26 の窓) を順に、XCVI と同じ 3 つの速さで同時に鳴らす:
    ×16  骨組み: 3 小節が 48 小節に。伸ばした音は 2 拍ごと (低い音は 4 拍ごと) に、息をするようにふくらんで打ち直す (4 声も、旋律・左手・層のピアノも)
    ×4   中の層: 48 小節のあいだに 4 回
    ×1   フーガ: CIV の速さのまま。3 小節鳴って 3 小節休む、を 8 回 — 遠くで
  鐘は ×16 の位置にひとつずつ。和音・区切りも 16 倍に。76 × 16 = 1216 小節 = 1 時間 21 分 4 秒 (♩=60)
  音源は bank85p (ピアノだけ)。声なし
  使い方: python compose_tablet105.py <score_tablet104.json> [score_tablet105.json] → python render_long.py score_tablet105.json out105 192 3
"""
import sys, json, math
from collections import Counter

SRC = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet105.json'
K = 16; WIN = 12

def source_events(d):
    ev = []
    for n in d['notes']: ev.append((n['t'], n['d'], n['m'], float(n.get('dyn', 1.0)), n['label'], n['v'], n.get('src')))
    for e in d['extras']:
        if e['v'] == 'PF': ev.append((e['t'], e['d'], e['m'], float(e['gain']) / 0.5, e.get('label'), 'PF', e.get('rid')))
    return sorted(ev, key=lambda x: x[0])

def build(d):
    ev_all = source_events(d); bells = [e for e in d['extras'] if e['v'] == 'X']
    notes, extras, entries, harm, sections = [], [], [], [], []
    sec_src = sorted(d['sections'], key=lambda s: s['t']); nb = 0
    for w0 in range(0, d['nbars'] * 4, WIN):
        L = min(WIN, d['nbars'] * 4 - w0); f = nb
        for s in sec_src:
            if w0 <= s['t'] < w0 + L:
                sections.append(dict(t=float(f * 4 + K * (s['t'] - w0)), bar=f + int(K * (s['t'] - w0)) // 4 + 1, title=s['title'] + ' ×16', sub=s['sub'] + ' — 全音符を 16 倍に (×16 の骨組みの中で ×4 が 4 回、×1 が 8 回)'))
        for x in bells:
            if w0 <= x['t'] < w0 + L:
                b = f * 4 + K * (x['t'] - w0)
                extras.append(dict(x, t=float(b), d=float(x['d']), beat=float(b), dbeats=float(x['dbeats'])))
        ev = [(t - w0, min(dd, w0 + L - t), m, g, lab, v, rid) for t, dd, m, g, lab, v, rid in ev_all if w0 <= t < w0 + L]
        for q in range(L): harm += [d['harm'][w0 + q]] * K
        for s, dd, m, g, lab, v, rid in ev:                                         # ×16
            S0, D = K * s, K * dd; step = 4.0 if m < 48 else 2.0; n_ = max(1, int(round(D / step))); first = True
            for i in range(n_):
                b = f * 4 + S0 + i * step
                amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, n_ - 1))
                if v == 'PF':
                    extras.append(dict(v='PF', t=float(b), d=step + 0.4, beat=float(b), dbeats=step, m=m, gain=round(0.22 * g * amp, 4), rid=rid, rel=0.6,
                                       label=(lab + ' ×16') if (first and lab) else None, layer='x16'))
                else:
                    notes.append(dict(v=v, t=float(b), d=step - 0.05, m=m, label=(lab + ' ×16') if (first and lab) else None, beat=float(b),
                                      dyn=round(0.95 * amp, 4), det=1.0, role='', src=rid))
                if first and lab: entries.append(dict(t=float(b), label=lab + ' ×16', v=v if v != 'PF' else 'S', bar=int(b // 4) + 1))
                first = False
        for rep in range(4):                                                        # ×4
            for s, dd, m, g, lab, v, rid in ev:
                b = f * 4 + rep * 4 * L + 4 * s
                extras.append(dict(v='PF', t=float(b), d=round(4 * dd + 0.2, 3), beat=float(b), dbeats=round(4 * dd, 3), m=m, gain=round(0.2 * g, 4), rid=rid, rel=0.5,
                                   label=(lab + ' ×4') if (lab and rep == 0) else None, layer='x4'))
        for rep in range(8):                                                        # ×1
            for s, dd, m, g, lab, v, rid in ev:
                b = f * 4 + rep * 2 * L + s
                extras.append(dict(v='PF', t=float(b), d=round(dd + 0.15, 3), beat=float(b), dbeats=round(dd, 3), m=m, gain=round(0.11 * g, 4), rid=rid, rel=0.4,
                                   label=(lab + ' ×1') if (lab and rep == 0) else None, layer='x1'))
        nb += K * L // 4
    entries.sort(key=lambda e: e['t']); notes.sort(key=lambda n: n['t']); extras.sort(key=lambda e: e['t'])
    return dict(bpm=60, beats_per_bar=4, nbars=nb, duration=float(nb * 4), bar_times=[4.0 * i for i in range(nb + 1)], notes=notes, extras=extras,
                entries=entries, sections=sections, harm=harm)

if __name__ == '__main__':
    d = json.load(open(SRC)); out = build(d)
    out['meta'] = dict(d['meta'], fps=15, fixed_peak=0.35,
                       title='Requiem BADA — CV · Fiore e Fuga 9/23 XVI',
                       subtitle='CIV をまるごと 16 倍に (1 時間 21 分) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す (変ロ短調 → ホ短調 → ホ長調, ♩=60)',
                       legend=['PF', 'X'], vname={'PF': '×16 / ×4 / ×1 の層', 'X': '鐘'},
                       footer=['CIV の 76 小節 × 16 = 1216 小節: I. Fiore dolce 08:06 ×16 → II. Requiem 08:06 ×16 → III. Fuga 08:09 ×16 → IV. Fusione ×16 → V. Amen ×16',
                               '×16 の骨組み (2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。音源は bank85p (ピアノだけ) と鐘。声なし。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    h, rem = divmod(out['duration'], 3600)
    print('bars', out['nbars'], 'duration %d:%02d:%02d' % (h, rem // 60, rem % 60), 'notes', len(out['notes']), 'extras', Counter(e.get('layer', e['v']) for e in out['extras']))
