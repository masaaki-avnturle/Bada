#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCVI · Fuga per augmentationem XVI integra (Klavier) (XCIV をまるごと 16 倍に — 3 時間 8 分、声なし)
  XCV は核の 3 小節を 4 つ選んだが、ここでは XCIV (176 小節、11 分 44 秒) の **すべての 3 小節** (59 の窓) を順に、XCV と同じ 3 つの速さで同時に鳴らす:
    ×16  骨組み (4 声): 3 小節が 48 小節に。伸ばした音は 2 拍ごと (低い音は 4 拍ごと) に、息をするようにふくらんで打ち直す
    ×4   中の層: 48 小節のあいだに 4 回
    ×1   フーガ: XCIV の速さのまま。3 小節鳴って 3 小節休む、を 8 回 — 遠くで
  声を消す: XCIV の Prologo / Epilogo で流していた piano_solo_8x.mp4 の実音 (声が入っている) をやめ、その採譜 (basic-pitch、+5) をピアノの 1 音で弾いて、同じ 3 つの速さに
  楽譜が途切れる所 (XCIV 146 小節目の 2 拍目) もそのまま 16 倍の所 (2345 小節目) で全部が止まり、沈黙 (4 小節 → 64 小節 = 4 分 16 秒) も 16 倍に
  176 小節 × 16 = 2816 小節 = 3 時間 7 分 44 秒 (♩=60)。すべて 9/24 08:53 の録音から切り出したピアノの 1 音。声なし
  使い方: python compose_tablet96.py <score_tablet94.json> <piano_solo_8x の採譜 (bp_cache json, 2130 秒から)> [score_tablet96.json]
          python render_long.py score_tablet96.json out_dir      # 分割して合成・描画 (synth.py / video.py を 13 分ずつ)
"""
import sys, json, math
from collections import Counter

SRC, BP = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet96.json'
R = '20260924_085314'; K = 16; WIN = 12                                    # 窓 = 3 小節 = 12 拍
BP_OFF, SEMIS = 2130.0, 5
REC_WIN = [(0, 64, 2186.0), (152 * 4, 96, 2250.0)]                          # XCIV の実音の窓 (拍, 長さ 秒, piano_solo_8x の秒) → 採譜に置き換える

def source_events(d):
    """XCIV の音 (拍, 長さ, 音高, 大きさ, ラベル, 声部) — 実音は採譜のピアノに"""
    ev = []
    for n in d['notes']: ev.append((n['t'], n['d'], n['m'], float(n.get('dyn', 1.0)), n['label'], n['v']))
    for e in d['extras']:
        if e['v'] == 'PF': ev.append((e['t'], e['d'], e['m'], float(e['gain']) / 0.5, e.get('label'), 'PF'))
    bp = json.load(open(BP))
    for b0, L, off in REC_WIN:
        a = off - BP_OFF; first = True
        for t, dd, m, v in sorted(bp):
            if a <= t < a + L and v >= 0.4 and 36 <= m + SEMIS <= 96:
                fade = 1.0 if (t - a) < L * 0.7 else max(0.15, 1.0 - (t - a - L * 0.7) / (L * 0.3))     # 終わりは消えていく
                ev.append((b0 + (t - a), min(max(0.5, dd), a + L - t), m + SEMIS, 3.5 * v * fade, 'piano_solo_8x の採譜 (+5)' if first else None, 'PF'))
                first = False
    return sorted(ev)

def build(d):
    ev_all = source_events(d)
    cut = d['meta']['pause_bar'] * 4 + 1                                    # XCIV の途切れる拍 (146 小節目の 2 拍目)
    notes, extras, entries, harm = [], [], [], []
    nb = 0; cut_bar = None
    sec_src = sorted(d['sections'], key=lambda s: s['t']); sections = []
    for w0 in range(0, d['nbars'] * 4, WIN):
        L = min(WIN, d['nbars'] * 4 - w0); f = nb                           # 窓 [w0, w0+L) 拍 → f 小節から
        for s in sec_src:
            if w0 <= s['t'] < w0 + L:
                title, sub = s['title'] + ' ×16', s['sub']
                if 'Prologo' in title: title, sub = 'Prologo — piano_solo_8x (採譜のピアノ) ×16', '主題 I を採った 2186〜2250 秒の採譜 (+5) をピアノの 1 音で、16 倍に — 実音はやめて声を消した'
                if 'Epilogo' in title: title, sub = 'Epilogo — piano_solo_8x (採譜のピアノ) ×16', '沈黙のあと、2250〜2346 秒の採譜 (+5) をピアノで、16 倍に — 消えていく'
                sections.append(dict(t=float(f * 4 + K * (s['t'] - w0)), bar=f + int(K * (s['t'] - w0)) // 4 + 1, title=title, sub=sub))
        ev = [(t - w0, min(dd, w0 + L - t), m, g, lab, v) for t, dd, m, g, lab, v in ev_all if w0 <= t < w0 + L]
        stop = K * L
        if w0 <= cut < w0 + L: stop = K * (cut - w0); cut_bar = f + stop // 4
        for q in range(L): harm += [d['harm'][w0 + q]] * K
        for s, dd, m, g, lab, v in ev:                                        # ×16 の骨組み
            S0, D = K * s, K * dd; step = 4.0 if m < 48 else 2.0; n_ = max(1, int(round(D / step))); first = True
            for i in range(n_):
                b = f * 4 + S0 + i * step
                if b >= f * 4 + stop: break
                amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, n_ - 1))
                if v == 'PF':
                    extras.append(dict(v='PF', t=float(b), d=step + 0.4, beat=float(b), dbeats=step, m=m, gain=round(0.22 * g * amp, 4), rid=R, rel=0.6,
                                       label=(lab + ' ×16') if (first and lab) else None, layer='x16'))
                else:
                    notes.append(dict(v=v, t=float(b), d=step - 0.05, m=m, label=(lab + ' ×16') if (first and lab) else None, beat=float(b),
                                      dyn=round(0.95 * amp, 4), det=1.0, role='', src=R))
                if first and lab: entries.append(dict(t=float(b), label=lab + ' ×16', v=v if v != 'PF' else 'S', bar=int(b // 4) + 1))
                first = False
        for rep in range(4):                                                   # ×4
            for s, dd, m, g, lab, v in ev:
                b = f * 4 + rep * 4 * L + 4 * s
                if b >= f * 4 + stop: continue
                extras.append(dict(v='PF', t=float(b), d=round(4 * dd + 0.2, 3), beat=float(b), dbeats=round(4 * dd, 3), m=m, gain=round(0.2 * g, 4), rid=R, rel=0.5,
                                   label=(lab + ' ×4') if (lab and rep == 0) else None, layer='x4'))
        for rep in range(8):                                                   # ×1 (3 小節鳴って 3 小節休む)
            for s, dd, m, g, lab, v in ev:
                b = f * 4 + rep * 2 * L + s
                if b >= f * 4 + stop: continue
                extras.append(dict(v='PF', t=float(b), d=round(dd + 0.15, 3), beat=float(b), dbeats=round(dd, 3), m=m, gain=round(0.11 * g, 4), rid=R, rel=0.4,
                                   label=(lab + ' ×1') if (lab and rep == 0) else None, layer='x1'))
        nb += K * L // 4
    entries.sort(key=lambda e: e['t']); notes.sort(key=lambda n: n['t']); extras.sort(key=lambda e: e['t'])
    return dict(bpm=60, beats_per_bar=4, nbars=nb, duration=float(nb * 4), bar_times=[4.0 * i for i in range(nb + 1)], notes=notes, extras=extras,
                entries=entries, sections=sections, harm=harm), cut_bar

if __name__ == '__main__':
    d = json.load(open(SRC))
    out, cut_bar = build(d)
    out['meta'] = dict(d['meta'], pause_bar=cut_bar, fps=15,
                       title='Requiem BADA — XCVI · Fuga XVI integra (Klavier)',
                       subtitle='XCIV をまるごと 16 倍に (3 時間 8 分) — すべての 3 小節を ×16・×4・×1 の 3 つの速さで同時に、声なし (ニ短調, ♩=60)',
                       legend=['PF'], vname={'PF': '×4 · ×1 の層'},
                       footer=['XCIV の 176 小節 × 16 = 2816 小節。Prologo / Epilogo の piano_solo_8x は実音をやめて採譜のピアノで (声を消す)。途切れる所も沈黙も 16 倍',
                               '×16 の骨組み (4 声、2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。すべて 9/24 08:53 の録音のピアノの 1 音。声なし。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    h, rem = divmod(out['duration'], 3600)
    print('bars', out['nbars'], 'duration %d:%02d:%02d' % (h, rem // 60, rem % 60), 'notes', len(out['notes']), 'extras', Counter(e.get('layer', e['v']) for e in out['extras']), 'cut bar', cut_bar)
