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
  使い方: python compose_tablet105.py <score_tablet104.json> [score_tablet105.json] [bank85p.json (録音を採譜に置き換えるとき)] → python render_long.py score_tablet105.json out105 192 3
"""
import sys, json, math
from collections import Counter

SRC = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet105.json'
BANKP = sys.argv[3] if len(sys.argv) > 3 else None                                # 録音 (REC) を採譜に置き換えるための bank (CVI → CVII)
REC_G = 1.6                                                                       # 採譜の音の大きさ (録音の代わり、表として)
K = 16; WIN = 12

def source_events(d):
    ev = []; vox = 'Fuga senza voce' in d['meta'].get('title', '')
    rec_g, aux = (0.45, 0.3) if vox else (REC_G, 1.0)                              # Vox: 採譜・鼓動・持続音・オスティナートは 4 声に合わせて控えめに
    for n in d['notes']:
        if n.get('role') == 'base':                                               # 裏 (LXXXIX など) の音は小さいピアノの層として (4 声の大きさにしない)
            ev.append((n['t'], n['d'], n['m'], 0.62 * float(n.get('dyn', 1.0)) + 0.08, n['label'], 'PF', n.get('src'))); continue
        ev.append((n['t'], n['d'], n['m'], float(n.get('dyn', 1.0)), n['label'], n['v'], n.get('src')))
    for e in d['extras']:
        if e['v'] in ('PF', 'PK', 'OS', 'DN'): ev.append((e['t'], e['d'], e['m'], float(e['gain']) / 0.5 * (1.0 if e['v'] == 'PF' else aux), e.get('label'), 'PF', e.get('rid')))   # 鼓動・オスティナート・持続音もピアノの 1 音
    if BANKP:                                                                     # 録音の実音 → その採譜をピアノで (16 倍には伸ばせないので)
        bank = json.load(open(BANKP))['recordings']
        for e in d['extras']:
            if e['v'] != 'REC': continue
            rid = str(e.get('rid', '')).replace('.wav', '')
            if rid not in bank: continue
            first = True
            for sg in bank[rid]['segs']:
                t = e['t'] + (sg['t'] - e.get('off', 0.0))
                if t < e['t'] or t >= e['t'] + e['d']: continue
                for m in sg['m']:
                    ev.append((t, min(max(0.5, sg['d']), e['t'] + e['d'] - t), m, rec_g * float(e.get('gain', 0.8)) / 0.8 * (1.2 if m < 48 else 1.0), ('録音 %s:%s の採譜 (実音の代わり)' % (rid[9:11], rid[11:13])) if first else None, 'PF', rid)); first = False
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

def equalize(out, block=32):
    """声部の少ない曲 (Vox) のために、8 小節ごとの音の量 (音量² × 長さ、低い音は重く) をそろえる — 0.5〜1.8 倍、隣の区画となめらかに"""
    nblk = int(math.ceil(out['duration'] / block)); E = [0.0] * nblk
    def addE(t, d, amp, m):
        for k in range(int(t // block), min(nblk, int((t + d) // block) + 1)):
            ov = min(t + d, (k + 1) * block) - max(t, k * block)
            if ov > 0: E[k] += amp * amp * ov
    for n in out['notes']:                                                        # 低い音は 1 音で +16 dB ほど大きい (bank の低音のサンプル) → まず dyn を下げる
        if n['m'] < 48: n['dyn'] = round(n['dyn'] * 0.35, 4)
        addE(n['t'], n['d'], (0.62 * n['dyn'] + 0.08) / 0.67 * (5.0 if n['m'] < 48 else 1.0), n['m'])
    for e in out['extras']:
        if e['v'] == 'PF': addE(e['t'], e['d'], 2.5 * e['gain'], e['m'])
    med = sorted(x for x in E if x > 0)[len([x for x in E if x > 0]) // 2]
    f = [min(1.8, max(0.5, (med / x) ** 0.5)) if x > 0 else 1.0 for x in E]
    f = [(f[max(0, k - 1)] + 2 * f[k] + f[min(nblk - 1, k + 1)]) / 4.0 for k in range(nblk)]
    for n in out['notes']: n['dyn'] = round(min(1.45 if n['m'] >= 48 else 0.5, n['dyn'] * f[min(nblk - 1, int(n['t'] // block))]), 4)
    for e in out['extras']:
        if e['v'] == 'PF': e['gain'] = round(e['gain'] * f[min(nblk - 1, int(e['t'] // block))], 4)
    print('equalize: factors %.2f..%.2f' % (min(f), max(f)))

if __name__ == '__main__':
    d = json.load(open(SRC)); out = build(d)
    h, rem = divmod(out['duration'], 3600); dur_s = '%d 時間 %d 分' % (h, rem // 60)
    if 'sopra due temi' in d['meta'].get('title', ''):
        meta = dict(title='Requiem BADA — CXV · Requiem 10/03 sopra due temi XVI',
                    subtitle='CXIV をまるごと 16 倍に (%s) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す。録音は採譜のピアノに、共鳴は 13:19 の音のまま (変ロ短調 → 変ロ長調, ♩=60)' % dur_s,
                    footer=['CXIV の 100 小節 × 16 = 1600 小節: Praeludium ×16 → Interludium ×16 → Fuga (二重フーガ) ×16 → 締めくくり ×16 — 大黒柱の主題と 3 分目の主題',
                            '×16 の骨組み (2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。裏 (LXXXIX)・共鳴・鼓動・録音の採譜も 16 倍に。声なし。'])
    elif 'Fuga senza voce' in d['meta'].get('title', ''):
        meta = dict(title='Requiem BADA — Vox · Fuga senza voce XVI',
                    subtitle='Fuga senza voce をまるごと 16 倍に (%s) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す。ピアノ録音の音だけ、声なし (イ短調, ♩=60)' % dur_s,
                    footer=['Fuga senza voce の 70 小節 × 16 = 1120 小節: Introitus ×16 → Kyrie ×16 → Mix (録音は採譜のピアノに) ×16 → Fuga ×16 → Sanctus ×16 → Agnus Dei ×16 → Lux aeterna ×16',
                            '×16 の骨組み (2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。鼓動・持続音・オスティナートも 16 倍に。音源は 9/24 のピアノ録音。'])
    elif 'CVI' in d['meta'].get('title', ''):
        meta = dict(title='Requiem BADA — CVII · Canzone 9/23 tre in uno XVI',
                    subtitle='CVI をまるごと 16 倍に (%s) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す。録音は採譜のピアノに (変ロ短調 → ホ短調 → ホ長調, ♩=60)' % dur_s,
                    footer=['CVI の 110 小節 × 16 = 1760 小節: 表 1 08:06 (採譜) ×16 → 表 2 08:09 (採譜) ×16 → Fusione ×16 → Amen ×16',
                            '×16 の骨組み (2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。録音の実音は採譜のピアノに置き換えた (声なし)。音源は bank85p。'])
    else:
        meta = dict(title='Requiem BADA — CV · Fiore e Fuga 9/23 XVI',
                    subtitle='CIV をまるごと 16 倍に (%s) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す (変ロ短調 → ホ短調 → ホ長調, ♩=60)' % dur_s,
                    footer=['CIV の 76 小節 × 16 = 1216 小節: I. Fiore dolce 08:06 ×16 → II. Requiem 08:06 ×16 → III. Fuga 08:09 ×16 → IV. Fusione ×16 → V. Amen ×16',
                            '×16 の骨組み (2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。音源は bank85p (ピアノだけ) と鐘。声なし。'])
    if 'sopra due temi' in d['meta'].get('title', ''):
        meta = dict(title='Requiem BADA — CXV · Requiem 10/03 sopra due temi XVI',
                    subtitle='CXIV をまるごと 16 倍に (%s) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す。録音は採譜のピアノに、共鳴は 13:19 の音のまま (変ロ短調 → 変ロ長調, ♩=60)' % dur_s,
                    footer=['CXIV の 100 小節 × 16 = 1600 小節: Praeludium ×16 → Interludium ×16 → Fuga (二重フーガ) ×16 → 締めくくり ×16 — 大黒柱の主題と 3 分目の主題',
                            '×16 の骨組み (2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。裏 (LXXXIX)・共鳴・鼓動・録音の採譜も 16 倍に。声なし。'])
    elif 'Fuga senza voce' in d['meta'].get('title', ''): equalize(out)
    out['meta'] = dict(d['meta'], fps=15, fixed_peak=(0.8 if BANKP else 0.35), legend=['PF', 'X'], vname={'PF': '×16 / ×4 / ×1 の層', 'X': '鐘'}, **meta)
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    h, rem = divmod(out['duration'], 3600)
    print('bars', out['nbars'], 'duration %d:%02d:%02d' % (h, rem // 60, rem % 60), 'notes', len(out['notes']), 'extras', Counter(e.get('layer', e['v']) for e in out['extras']))
