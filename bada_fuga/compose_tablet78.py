#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXVIII · Symphonia a due — XVI e VIII (LXXVII の重低音を主題の 16 倍に、共鳴を 8 倍に)
  LXXVII (LXXV を真ん中で割って調をそろえて重ねた交響曲、9/24 の 2 本が主題曲) をもとに:
    - 重低音 = 主題の 16 倍: 主題曲の主題 (8 拍) の 4 分音符が 16 拍 (4 小節) に — 32 小節。ピアノのいちばん低い音域 (ミ 1 から) でオクターヴに、小節ごとに打ち直す。
      各部 (48 小節) の最初の 16 小節は主音の保続、そこから 16 倍の主題が始まり、部の終わりで主音に着く。
    - 共鳴 = 主題の 8 倍: 同じ主題の 4 分音符が 8 拍 (2 小節) に — 16 小節。中音域 (ミ 3〜ミ 4 のあたり) で 2 拍ごとに息をするように打ち直し、
      オクターヴ上を小さく重ねて響かせる。各部で 3 回 (16 小節ごと)。
    - LXXV の前半・後半を重ねた響き、主題曲の実音 (Introitus・Interludium)、Amen は LXXVII と同じ。
  第 1 部 (ホ短調): 主題曲 9/24 08:53 — ミ・ファ#・シ・ミ・ミ / 第 2 部 (ヘ短調): 主題曲 9/24 08:49 — ファ・ラ♭・シ♭・レ♭・ファ
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet78.py <bank74.json> <score_tablet75.json> <9/24 の 2 本の wav があるフォルダ> [score_tablet78.json]
"""
import sys, os, json
import numpy as np
from compose import transpose_h, chord, name_of
import compose_tablet77 as LXXVII

OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet78.json'
SRC75, WAV, BANK = LXXVII.SRC75, LXXVII.WAV, LXXVII.BANK
INTRO, INTER, PART = LXXVII.INTRO, LXXVII.INTER, LXXVII.PART
BASS_RID, RES_RID = '20260925_124643', '20260925_130431'

def low(m, lo):
    """m を lo〜lo+11 の音域へ (同じ音名)"""
    return lo + (m - lo) % 12

def strike(out, t0, L, m, g, step, rid, rel, layer, swell=True):
    n_ = max(1, int(round(L / step)))
    for i in range(n_):
        a = t0 + i * step; ph = i / max(1, n_ - 1)
        amp = 1.0 if i == 0 else (0.62 + 0.25 * np.sin(np.pi * ph) if swell else 0.7)
        out.append(dict(v='PF', t=round(a, 3), d=round(step + 0.8, 3), m=int(m), gain=round(g * amp, 4), rid=rid, rel=rel, beat=round(a, 3), dbeats=step, label=None, layer=layer))

def main():
    out = dict(bpm=60, beats_per_bar=4, notes=[], extras=[], entries=[], sections=[], harm=[])
    T = 0.0
    for pi, ((a0, a1), sa, (b0, b1), sb, key, rid, roff, title) in enumerate(LXXVII.PARTS):
        nm = '9/24 %s:%s' % (rid[9:11], rid[11:13]); L = INTRO if pi == 0 else INTER; kname = 'ホ短調' if key == 2 else 'ヘ短調'
        out['sections'].append(dict(t=T, title=('Introitus' if pi == 0 else 'Interludium') + ' — 主題曲 %s の実音 (%s)' % (nm, kname),
                                    sub='主題曲 (ピアノの実音) から%s' % ('始まる' if pi == 0 else '、第 2 部のヘ短調へ')))
        out['extras'].append(dict(v='REC', t=T, d=L + 1.0, beat=T, dbeats=L + 1.0, m=0, gain=0.28, src=os.path.join(WAV, rid + '.wav'), off=roff, fin=2.0, fout=3.0,
                                  rid=rid + '.wav', tag='主題曲 %s' % nm, label=None))
        out['harm'] += ['Em' if key == 2 else 'Fm'] * int(L); T += L
        out['sections'].append(dict(t=T, title=title.replace('を重ねて', '+ 重低音 ×16・共鳴 ×8'),
                                    sub='LXXV の前半と後半を重ね (調をそろえて)、主題曲 %s の主題を重低音で 16 倍・共鳴で 8 倍に' % nm))
        hg = LXXVII.HALF_GAIN * (1.0 if pi == 0 else 0.6)                              # 第 2 部は鐘の打ち直しが厚いので小さめに
        out['extras'] += LXXVII.take(a0, a1, sa, T, hg) + LXXVII.take(b0, b1, sb, T, hg)
        out['harm'] += [transpose_h([[h]], sa)[0][0] for h in SRC75['harm'][a0:a1]]
        s_ = [(d, m + key) for d, m in LXXVII.subject(rid, key)]
        tonic = s_[-1][1]
        # ---- 重低音: 16 小節の主音の保続 → 主題 ×16 (32 小節)、オクターヴで小節ごとに打ち直す
        for oc, g in ((0, 0.40), (12, 0.26)):
            strike(out['extras'], T, 64.0, low(tonic, 28) + oc, g, 4.0, BASS_RID, 1.4, 'bass16')
        t = T + 64.0
        for d, m in s_:
            for oc, g in ((0, 0.40), (12, 0.26)):
                strike(out['extras'], t, d * 16.0, low(m, 28) + oc, g, 4.0, BASS_RID, 1.4, 'bass16')     # 16 倍 (♩=60: 1 拍 = 1 秒)
            t += d * 16.0
        out['entries'] += [dict(t=T, label='重低音 — 主音の保続', v='B'), dict(t=T + 64.0, label='重低音 — 主題曲 %s の主題 ×16' % nm, v='B')]
        # ---- 共鳴: 主題 ×8 (16 小節) を 3 回、中音域で 2 拍ごとに、オクターヴ上を小さく
        for r in range(3):
            t = T + r * 64.0
            for d, m in s_:
                base = low(m, 52)
                strike(out['extras'], t, d * 8.0, base, 0.30, 2.0, RES_RID, 1.0, 'res8')
                strike(out['extras'], t, d * 8.0, base + 12, 0.13, 2.0, RES_RID, 1.0, 'res8')
                t += d * 8.0
            out['entries'].append(dict(t=T + r * 64.0 + 0.01, label='共鳴 — 主題 ×8' if r == 0 else '共鳴 ×8', v='T'))
        T += PART
    out['sections'].append(dict(t=T, title='Amen (ヘ長調)', sub='LXXV の Amen を 1 半音上げて — 重低音のファが最後まで響く'))
    out['extras'] += LXXVII.take(780, 792, 1, T, g=0.9)
    for i in range(3):
        for m, g in ((29, 0.4), (41, 0.26)):
            out['extras'].append(dict(v='PF', t=T + 4 * i, d=4.8, m=m, gain=round(g * (1 - 0.25 * i), 4), rid=BASS_RID, rel=1.5, beat=T + 4 * i, dbeats=4.0, label=None, layer='bass16'))
    out['harm'] += ['F'] * 12; T += 12.0
    out['duration'] = round(T, 3); out['nbars'] = int(round(T / 4.0)); out['bar_times'] = [4.0 * i for i in range(out['nbars'] + 1)]
    out['meta'] = {k: v for k, v in SRC75['meta'].items() if k not in ('title', 'subtitle', 'footer', 'bank')}
    out['meta'].update(bank=BANK, rec_order=[LXXVII.R53, LXXVII.R49] + [r for r in SRC75['meta'].get('rec_order', []) if r not in (LXXVII.R53, LXXVII.R49)],
        title='Requiem BADA — LXXVIII · Symphonia a due XVI-VIII',
        subtitle='重低音は主題曲の主題を 16 倍に、共鳴は 8 倍に — LXXV を真ん中で割って重ねた交響曲 (♩=60)',
        legend=['PF'], vname={'PF': 'ピアノ'},
        footer=['Introitus (08:53) → 第 1 部 (ホ短調) → Interludium (08:49) → 第 2 部 (ヘ短調) → Amen (ヘ長調)',
                '重低音 = 主題 ×16 (ミ 1 からオクターヴ、小節ごと)・共鳴 = 主題 ×8 (中音域、2 拍ごと)・LXXV の前半と後半を重ねて。すべてピアノの実音。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    ms = [e['m'] for e in out['extras'] if e['v'] == 'PF']
    from collections import Counter
    print('duration %.0f s (%d:%02d)  range %s..%s (%.1f oct)  layers %s' % (T, T // 60, T % 60, name_of(min(ms)), name_of(max(ms)), (max(ms) - min(ms)) / 12,
          dict(Counter(e.get('layer') for e in out['extras']))))

if __name__ == '__main__':
    main()
