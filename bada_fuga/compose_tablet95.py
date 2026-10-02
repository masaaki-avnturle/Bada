#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCV · Fuga per augmentationem XVI (Klavier) (XCIV を 16 倍に伸ばして、同じようにフーガを醸す曲に)
  XCIV (11 分 44 秒) をまるごと 16 倍にすると 3 時間 8 分になるので、LXXV と同じく、フーガの主題が入る **核の 3 小節** (12 秒) を 4 つ選び、
  それぞれを **3 つの速さで同時に** 鳴らす (ペルト「ベンジャミン・ブリテンへの追悼歌」のメンスーラ・カノンのように):
    ×16  骨組み: 3 小節が 48 小節 (3 分 12 秒) に。和音がほとんど動かないコラール。伸ばした音は 2 拍ごと (低い音は 4 拍ごと) に、息をするようにふくらんで打ち直す
    ×4   中の層: 3 小節が 12 小節に。48 小節のあいだに 4 回
    ×1   フーガ: XCIV の速さのまま (XCII の 2 倍)。3 小節鳴って 3 小節休む、を 8 回 — 遠くで (×16 より小さく)
  核の 3 小節 (XCIV の小節):
    I.   Sectio I 提示 (20〜23)     主題 I の答唱 (ソプラノ) とアルトの対位
    II.  Sectio II 二重 (88〜91)    主題 I (ソプラノ) + 主題 II (テノール) の二重フーガ
    III. Sectio III 三重 (128〜131) 主題 I + 主題 II + B-A-C-H の三重フーガ、その上の主題 I ×1 (拡大カノン)
    IV.  途切れる所 (144〜147)      3 度目の三重の重なり → 10 拍目で楽譜が途切れる = ×16 では 40 小節目で全部が止まる → 沈黙
  Prologo / Epilogo は XCIV と同じ piano_solo_8x の実音 (速さは変えず)。すべて 9/24 08:53 の録音から切り出したピアノの 1 音。声なし (歌声は元からない)。
  使い方: python compose_tablet95.py <score_tablet94.json> [score_tablet95.json]
"""
import sys, json, math
from collections import Counter

SRC = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet95.json'
R = '20260924_085314'
CORE = 12                                                # 核の長さ (拍)
PRO, EPI = 16, 24
CORES = [  # (XCIV の拍, 題, 説明, 途切れる拍 (核の中) or None)
    (80, 'I. Sectio I ×16 — 主題 I の答唱', '核: XCIV 20〜23 小節 — 主題 I の答唱 (ソプラノ) とアルトの対位。×16 の骨組み (2 拍ごとの打ち直し) の中で ×4 が 4 回、×1 のフーガが遠くで 8 回', None),
    (352, 'II. Sectio II ×16 — 二重フーガ', '核: XCIV 88〜91 小節 — 主題 I (ソプラノ) + 主題 II (テノール)。×16・×4・×1 が同時に', None),
    (512, 'III. Sectio III ×16 — 三重フーガ', '核: XCIV 128〜131 小節 — 主題 I + 主題 II + B-A-C-H、その上の主題 I ×1 (拡大カノン) も 16 倍に', None),
    (576, 'IV. ×16 — 途切れる', '核: XCIV 144〜147 小節 — 3 度目の三重の重なり。核の 10 拍目で楽譜が途切れる = 40 小節目で ×16・×4・×1 がそろって止まる → 沈黙', 10),
]

def events(d, t0):
    """核の窓 [t0, t0+12) の音: (拍, 長さ, 音高, 大きさ, ラベル, 声部)"""
    ev = []
    for n in d['notes']:
        if t0 <= n['t'] < t0 + CORE:
            ev.append((n['t'] - t0, min(n['d'], t0 + CORE - n['t']), n['m'], float(n.get('dyn', 1.0)), n['label'], n['v']))
    for e in d['extras']:
        if e['v'] == 'PF' and t0 <= e['t'] < t0 + CORE:
            ev.append((e['t'] - t0, min(e['d'], t0 + CORE - e['t']), e['m'], float(e['gain']) / 0.5, e.get('label'), 'PF'))
    return sorted(ev)

def build(d):
    notes, extras, entries, sections, harm = [], [], [], [], []
    bar = 0
    rec = [dict(e, gain=round(e['gain'] * 0.6, 3)) for e in d['extras'] if e['v'] == 'REC']      # 実音は ×16 の骨組みに合わせて小さく
    # Prologo
    sections.append(dict(t=0.0, bar=1, title='Prologo — piano_solo_8x (実音)', sub='主題 I を採った 2186〜2250 秒 (+5、速さは変えず) — 実音だけ'))
    extras.append(dict(rec[0], beat=0, dbeats=PRO * 4, t=0.0, d=float(PRO * 4)))
    harm += ['Dm'] * (PRO * 4); bar = PRO
    cut_bar = None
    for t0, title, sub, cut in CORES:
        f = bar; ev = events(d, t0); L = 16 * CORE                          # 192 拍 = 48 小節
        stop = 16 * cut if cut is not None else L
        sections.append(dict(t=float(f * 4), bar=f + 1, title=title, sub=sub))
        for q in range(CORE):                                                 # 和音 ×16
            harm += [d['harm'][t0 + q]] * 16
        # ×16 の骨組み: 伸ばした音を 2 拍ごと (低い音は 4 拍ごと) に打ち直す
        for s, dd, m, g, lab, v in ev:
            S0, D = 16 * s, 16 * dd; step = 4.0 if m < 48 else 2.0; n_ = max(1, int(round(D / step))); first = True
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
        # ×4 の中の層: 4 回
        for rep in range(4):
            for s, dd, m, g, lab, v in ev:
                b = f * 4 + rep * 4 * CORE + 4 * s
                if b >= f * 4 + stop: continue
                extras.append(dict(v='PF', t=float(b), d=round(4 * dd + 0.2, 3), beat=float(b), dbeats=round(4 * dd, 3), m=m, gain=round(0.2 * g, 4), rid=R, rel=0.5,
                                   label=(lab + ' ×4') if (lab and rep == 0 and s == 0) else None, layer='x4'))
        # ×1 のフーガ: 3 小節鳴って 3 小節休む、8 回 (遠くで)
        for rep in range(8):
            for s, dd, m, g, lab, v in ev:
                b = f * 4 + rep * 2 * CORE + s
                if b >= f * 4 + stop: continue
                extras.append(dict(v='PF', t=float(b), d=round(dd + 0.15, 3), beat=float(b), dbeats=round(dd, 3), m=m, gain=round(0.11 * g, 4), rid=R, rel=0.4,
                                   label=(lab + ' ×1') if (lab and rep == 0 and s == 0) else None, layer='x1'))
        if cut is not None:
            cut_bar = f + stop // 4
            bar = f + stop // 4 + 4                                           # 途切れたあと 4 小節の沈黙
            harm = harm[:bar * 4]
        else:
            bar = f + L // 4
    # Epilogo
    e0 = bar
    sections.append(dict(t=float(e0 * 4), bar=e0 + 1, title='Epilogo — piano_solo_8x (実音)', sub='沈黙のあと、piano_solo_8x の実音 (2250〜2346 秒、+5) だけが戻って消える'))
    extras.append(dict(rec[1], beat=e0 * 4, dbeats=EPI * 4, t=float(e0 * 4), d=float(EPI * 4)))
    harm += ['Dm'] * (EPI * 4); nb = e0 + EPI
    entries.sort(key=lambda e: e['t'])
    return dict(bpm=60, beats_per_bar=4, nbars=nb, duration=float(nb * 4), bar_times=[4.0 * i for i in range(nb + 1)], notes=notes, extras=extras,
                entries=entries, sections=sections, harm=harm), cut_bar

if __name__ == '__main__':
    d = json.load(open(SRC))
    out, cut_bar = build(d)
    out['meta'] = dict(d['meta'], pause_bar=cut_bar,
                       title='Requiem BADA — XCV · Fuga per augmentationem XVI (Klavier)',
                       subtitle='XCIV を 16 倍に — 核の 3 小節 ×4 を ×16・×4・×1 の 3 つの速さで同時に、フーガを醸す (ニ短調, ♩=60)',
                       legend=['PF'], vname={'PF': '×4 · ×1 の層'},
                       footer=['Prologo (実音) → I. 主題 I の答唱 ×16 → II. 二重フーガ ×16 → III. 三重フーガ ×16 → IV. 途切れる所 ×16 (40 小節目で止まる) → 沈黙 → Epilogo (実音)',
                               '×16 の骨組み (4 声、2 拍ごとの打ち直し) の中で、×4 が 4 回、×1 のフーガが遠くで 8 回。すべて 9/24 08:53 の録音のピアノの 1 音。声なし。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    print('bars', out['nbars'], 'duration', out['duration'], 'notes', len(out['notes']), 'extras', Counter(e.get('layer', e['v']) for e in out['extras']), 'cut bar', cut_bar)
