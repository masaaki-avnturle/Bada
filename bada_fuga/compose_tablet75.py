#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXV · Symphonia lamentosa per augmentationem XVI (LXXIV を 16 倍に伸ばし、レクイエムとフーガを矛盾したまま重ねる交響曲)
  LXXIV (21 分 36 秒) をまるごと 16 倍にすると 5 時間 45 分になるので、各楽章の「核」になる 3 小節 (12 秒) — フーガの主題が入る所 — を選び、
  それを 3 つの速さで同時に鳴らす (ペルトの「ブリテンへの追悼歌」のメンスーラ・カノンのように):
    ×16 (Requiem): 3 小節が 48 小節 (3 分 12 秒) に。和音がほとんど動かない、もの哀しいコラール — 伸ばした音は 2 拍ごと (低い音は 4 拍ごと) に打ち直す
    ×4  (中の層): 3 小節が 12 小節に。48 小節のあいだに 4 回
    ×1  (Fuga):   もとの速さのフーガ。6 小節ごと (3 小節鳴って 3 小節休む) に 8 回、遠くで
  同じ音楽が、止まったようなレクイエム (×16) と、動き続けるフーガ (×1) として同時に鳴る — 矛盾したまま 1 つに合わさる。3 つの層は最後の小節でそろって終わる。
  すべて LXXIV の楽譜の音 (録音から切り出したピアノの実音) から。シンセ・ドラムなし。
  楽章 (楽章の間は 1 小節の休み):
    I.   Lamento (ホ短調)      — LXXIV 5:20〜5:32: 主題曲 9/23 08:09 のフーガの提示 (主題 → 答唱)
    II.  Requiem (変ロ短調)    — LXXIV 7:00〜7:12: 主題曲 9/23 08:06 の主題と 5 度上の答え (16 倍の打ち直しの上)
    III. Fuga (ヘ短調)         — LXXIV 11:52〜12:04: 主題曲 9/25 12:46 のフーガの提示
    IV.  Finale (ホ短調)       — LXXIV 19:00〜19:12: 三重フーガの三重結合 (主題 A・B・C を同時に) → Amen (ホ長調)
  使い方: python compose_tablet75.py <bank74.json> <score_tablet74.json> [score_tablet75.json]
"""
import sys, json
import numpy as np

BANK, SRC = sys.argv[1], json.load(open(sys.argv[2]))
OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet75.json'
FRAG = 12.0                                        # 3 小節 (♩=60)
MOVS = [('I. Lamento (ホ短調)', 320.0, '主題曲 9/23 08:09 のフーガの提示'),
        ('II. Requiem (変ロ短調)', 420.0, '主題曲 9/23 08:06 の主題と答え'),
        ('III. Fuga (ヘ短調)', 712.0, '主題曲 9/25 12:46 のフーガの提示'),
        ('IV. Finale (ホ短調)', 1140.0, '三重フーガの三重結合 (主題 A・B・C)')]
GAP = 4.0
LAYER = {16: 1.0, 4: 0.72, 1: 0.5}                 # 層の大きさ: ×16 が前、×1 のフーガは遠く

def fragment(f0):
    """LXXIV の [f0, f0+12) 秒の音: (相対秒, 長さ, 音高, 強さ, 録音 id)"""
    out = []
    for n in SRC['notes']:
        if f0 - 1e-3 <= n['t'] < f0 + FRAG - 1e-3:
            out.append((n['t'] - f0, min(n['d'], f0 + FRAG - n['t']), n['m'], 0.16 * n.get('dyn', 1.0), n.get('src', '')))
    for e in SRC['extras']:
        if e['v'] == 'PF' and f0 - 1e-3 <= e['t'] < f0 + FRAG - 1e-3:
            out.append((e['t'] - f0, min(e['d'], f0 + FRAG - e['t']), e['m'], e.get('gain', 0.2), e.get('rid', '')))
    return out

def strikes(t, d, m, g, rid, k, T0, swell=True):
    """伸ばした音 (k 倍) を打ち直しで鳴らす: 頭で強く、あとは 2 拍ごと (低い音は 4 拍ごと) に、息をするようにふくらんで静まる"""
    s0, L = T0 + t * k, d * k; out = []
    step = 1e9 if k == 1 else (2.0 if m >= 55 else 4.0)
    n_ = max(1, int(np.ceil(L / step - 1e-6)))
    for i in range(n_):
        a = s0 + i * step; dd = min(step, s0 + L - a)
        if dd <= 0.05: break
        ph = i / max(1, n_ - 1)
        amp = 1.0 if i == 0 else (0.55 + 0.25 * np.sin(np.pi * ph) if swell else 0.6)
        out.append(dict(v='PF', t=round(a, 4), d=round(max(0.15, dd + (0.6 if k > 1 else 0)), 4), m=int(m), gain=round(g * amp * LAYER[k], 5),
                        rid=rid, rel=0.6 if k > 1 else 0.4, beat=round(a, 4), dbeats=round(dd, 4), label=None, layer=k))
    return out

def main():
    out = dict(bpm=60, beats_per_bar=4, notes=[], extras=[], entries=[], sections=[], harm=[])
    T = 0.0
    for mi, (title, f0, what) in enumerate(MOVS):
        frag = fragment(f0); H = SRC['harm'][int(f0):int(f0 + FRAG)]
        body = FRAG * 16                           # 192 秒 = 48 小節
        out['sections'].append(dict(t=T, title='%s — ×16・×4・×1' % title.split(' (')[0] + ' (' + title.split(' (')[1],
                                    sub='LXXIV の %s (3 小節) を 16 倍のレクイエム・4 倍・もとの速さのフーガで同時に' % what))
        for x in frag: out['extras'] += strikes(*x, 16, T)                                         # ×16: 1 回
        for r in range(4):                                                                         # ×4: 12 小節ごとに 4 回
            for x in frag: out['extras'] += strikes(*x, 4, T + r * FRAG * 4, swell=False)
        for r in range(8):                                                                         # ×1: 6 小節ごとに 8 回 (最後は終わりにそろえる)
            t1 = T + r * 24.0 + 12.0
            for x in frag: out['extras'] += strikes(*x, 1, t1)
        out['entries'] += [dict(t=T, label='×16 — Requiem (3 小節が 48 小節に)', v='T'), dict(t=T + 0.01, label='×4', v='A'),
                           dict(t=T + 12.0, label='×1 — Fuga (もとの速さ)', v='S')]
        out['harm'] += [H[min(len(H) - 1, int(b // 16))] for b in range(int(body))]
        T += body
        if mi == len(MOVS) - 1:                    # Amen: ホ長調の和音をゆっくり打ち直して閉じる
            out['sections'].append(dict(t=T, title='Amen (ホ長調)', sub='ホ長調の和音だけが、2 拍ごとの打ち直しで静かに消えていく'))
            for m, g in ((40, 0.2), (52, 0.18), (59, 0.16), (64, 0.17), (68, 0.15), (71, 0.15)):
                for i in range(6): out['extras'].append(dict(v='PF', t=T + 2 * i, d=2.6, m=m, gain=round(g * (1 - i * 0.13), 4), rid='20260923_080918', rel=0.8,
                                                            beat=T + 2 * i, dbeats=2.0, label=None, layer=16))
            out['harm'] += ['E'] * 12; T += 12.0
        else:
            out['harm'] += [out['harm'][-1]] * int(GAP); T += GAP
    out['duration'] = round(T, 3); out['nbars'] = int(round(T / 4.0)); out['bar_times'] = [4.0 * i for i in range(out['nbars'] + 1)]
    out['meta'] = {k: v for k, v in SRC['meta'].items() if k not in ('title', 'subtitle', 'footer', 'bank')}
    out['meta'].update(bank=BANK, title='Requiem BADA — LXXV · Symphonia lamentosa',
        subtitle='LXXIV を 16 倍に — 止まったようなレクイエム (×16) と動き続けるフーガ (×1) を、矛盾したまま重ねる (♩=60)',
        legend=['PF'], vname={'PF': 'ピアノ'},
        footer=['I. Lamento ホ短調 → II. Requiem 変ロ短調 → III. Fuga ヘ短調 → IV. Finale ホ短調 → Amen ホ長調',
                '各楽章の核の 3 小節を ×16・×4・×1 で同時に (メンスーラ・カノン)。すべて LXXIV の楽譜の音、ピアノの実音。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('duration %.0f s (%d:%02d)  extras %d  layers %s' % (T, T // 60, T % 60, len(out['extras']), dict(Counter(e['layer'] for e in out['extras']))))

if __name__ == '__main__':
    main()
