#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXVII · Symphonia a due (LXXV を真ん中で割って重ね、9/24 の 2 本を主題曲に — 共鳴する重低音と 4 オクターヴ半の交響曲)
  LXXV (13 分 19 秒) を真ん中 — 楽章の切れ目 (I・II | III・IV) — で割り、前半と後半を同時に重ねる:
    第 1 部 (ホ短調): LXXV の I (ホ短調) + III (ヘ短調 → 1 半音下げてホ短調)
    第 2 部 (ヘ短調): LXXV の II (変ロ短調 → 5 半音下げてヘ短調) + IV (ホ短調 → 1 半音上げてヘ短調) → Amen (ヘ長調)
    重ねると調がぶつかるので、どちらも同じ調にそろえて共鳴させる。2 つの半分はそれぞれ少し小さく。
  主題曲 (9/24 の 2 本、ピアノの実音): 第 1 部は 08:53 (ホ短調)、第 2 部は 08:49 (ヘ短調) — 録音の実音で各部を始め、
    その主題を 4 倍の長さで (8 小節に 1 回) 重ねた響きの上に歌わせる (旋律と、オクターヴ上を少し小さく)。
  共鳴する重低音: 和音の根音を、ミ 1 のあたりからオクターヴで (ピアノのいちばん低い音域)、小節ごとに息をするように打ち直す。
    いちばん上はド 6 まで (ガラスのような高音は使わない) — 低いミ 1 から上まで 4 オクターヴ半。
  形式 (♩=60): Introitus (08:53 の実音) → 第 1 部 (I + III, ホ短調) → Interludium (08:49 の実音) → 第 2 部 (II + IV, ヘ短調) → Amen (ヘ長調)
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet77.py <bank73.json> <score_tablet75.json> <9/24 の 2 本の wav があるフォルダ> [score_tablet77.json]
"""
import sys, os, json
import numpy as np
import compose
from compose import transpose_h, chord, name_of
import compose_tablet as CT
import compose_tablet63 as LXIII

BANK, SRC75, WAV = sys.argv[1], json.load(open(sys.argv[2])), os.path.abspath(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet77.json'
R49, R53 = '20260924_084937', '20260924_085314'
HALF_GAIN = 0.72                                   # 重ねる 2 つの半分の大きさ
INTRO, INTER, PART = 32.0, 24.0, 192.0
# (前半の区間, 移調, 後半の区間, 移調, 部の調 (ニ短調から), 主題曲, 主題の録音の開始秒, 部の名前)
PARTS = [((0, 192), 0, (392, 584), -1, 2, R53, 30.0, '第 1 部 — I. Lamento + III. Fuga を重ねて (ホ短調)'),
         ((196, 388), -5, (588, 780), 1, 3, R49, 50.0, '第 2 部 — II. Requiem + IV. Finale を重ねて (ヘ短調)')]
AMEN = (780, 792, 1)

def take(t0, t1, semis, dt, g=HALF_GAIN):
    out = []
    for e in SRC75['extras']:
        if e['v'] == 'PF' and t0 - 1e-3 <= e['t'] < t1 - 1e-3:
            x = dict(e); x['t'] = round(e['t'] - t0 + dt, 4); x['beat'] = x['t']; x['m'] = e['m'] + semis; x['gain'] = round(e['gain'] * g, 5)
            out.append(x)
    return out

def subject(rid, semis):
    t0, inside = CT.excerpt(rid, semis, 13.0)
    return LXIII.smooth(CT.make_subject(inside, semis, 60))

def main():
    out = dict(bpm=60, beats_per_bar=4, notes=[], extras=[], entries=[], sections=[], harm=[])
    T = 0.0
    for pi, ((a0, a1), sa, (b0, b1), sb, key, rid, roff, title) in enumerate(PARTS):
        # ---- 主題曲の実音
        nm = '9/24 %s:%s' % (rid[9:11], rid[11:13]); L = INTRO if pi == 0 else INTER
        out['sections'].append(dict(t=T, title=('Introitus' if pi == 0 else 'Interludium') + ' — 主題曲 %s の実音 (%s)' % (nm, 'ホ短調' if key == 2 else 'ヘ短調'),
                                    sub='主題曲 (ピアノの実音) から%s' % ('始まる' if pi == 0 else '、第 2 部のヘ短調へ')))
        out['extras'].append(dict(v='REC', t=T, d=L + 1.0, beat=T, dbeats=L + 1.0, m=0, gain=0.28, src=os.path.join(WAV, rid + '.wav'), off=roff, fin=2.0, fout=3.0,
                                  rid=rid + '.wav', tag='主題曲 %s' % nm, label=None))
        out['harm'] += ['Em' if key == 2 else 'Fm'] * int(L); T += L
        # ---- 2 つの半分を重ねる
        out['sections'].append(dict(t=T, title=title, sub='LXXV の前半と後半を同時に (調をそろえて共鳴させる) — 主題曲 %s の主題を 4 倍で、重低音の根音' % nm))
        hg = HALF_GAIN * (1.0 if pi == 0 else 0.76)                                   # 第 2 部は鐘の打ち直しが厚いので少し小さく
        out['extras'] += take(a0, a1, sa, T, hg) + take(b0, b1, sb, T, hg)
        H = [transpose_h([[h]], sa)[0][0] for h in SRC75['harm'][a0:a1]]
        out['harm'] += H
        # ---- 主題 (4 倍) を 8 小節に 1 回、旋律とオクターヴ上
        s_ = subject(rid, key)                                                         # 録音の主題 (エンジンのニ短調) → 部の調へ
        s_ = [(d, m + key) for d, m in s_]
        for r in range(6):
            t = T + r * 32.0
            for d, m in s_:
                for oc, g in ((0, 0.5), (12, 0.22)):
                    mm = m + oc
                    while mm > 84: mm -= 12
                    out['extras'].append(dict(v='PF', t=round(t, 3), d=round(d * 4 + 0.8, 3), m=int(mm), gain=g, rid=rid, rel=0.8, beat=round(t, 3), dbeats=d * 4,
                                              label=None, layer='theme'))
                t += d * 4
            out['entries'].append(dict(t=T + r * 32.0, label='主題曲 %s の主題 ×4' % nm if r == 0 else '主題 ×4', v='S'))
        # ---- 共鳴する重低音: 和音の根音をオクターヴで、小節ごとに
        for bar in range(int(PART // 4)):
            c = chord(H[min(len(H) - 1, bar * 4)] or ('Em' if key == 2 else 'Fm')); r0 = 28 + (c['root'] - 28) % 12          # ミ 1〜レ# 2
            for k, (m, g) in enumerate(((r0, 0.36), (r0 + 12, 0.26), (r0 + 19, 0.11))):
                amp = 0.8 + 0.2 * np.sin(np.pi * (bar % 4) / 3)
                out['extras'].append(dict(v='PF', t=T + bar * 4, d=4.6, m=int(m), gain=round(g * amp, 4), rid='20260925_124643', rel=1.2,
                                          beat=T + bar * 4, dbeats=4.0, label=None, layer='bass'))
        out['entries'].append(dict(t=T + 0.02, label='共鳴する重低音 (根音のオクターヴ)', v='B'))
        T += PART
    # ---- Amen (ヘ長調)
    out['sections'].append(dict(t=T, title='Amen (ヘ長調)', sub='LXXV の Amen を 1 半音上げて — 重低音のファが最後まで響く'))
    out['extras'] += take(AMEN[0], AMEN[1], AMEN[2], T, g=0.9)
    for i in range(3):
        for m, g in ((29, 0.3), (41, 0.22), (48, 0.1)):
            out['extras'].append(dict(v='PF', t=T + 4 * i, d=4.8, m=m, gain=round(g * (1 - 0.25 * i), 4), rid='20260925_124643', rel=1.5, beat=T + 4 * i, dbeats=4.0, label=None, layer='bass'))
    out['harm'] += ['F'] * 12; T += 12.0
    out['duration'] = round(T, 3); out['nbars'] = int(round(T / 4.0)); out['bar_times'] = [4.0 * i for i in range(out['nbars'] + 1)]
    out['meta'] = {k: v for k, v in SRC75['meta'].items() if k not in ('title', 'subtitle', 'footer', 'bank')}
    out['meta'].update(bank=BANK, rec_order=[R53, R49] + [r for r in SRC75['meta'].get('rec_order', []) if r not in (R53, R49)],
        title='Requiem BADA — LXXVII · Symphonia a due',
        subtitle='LXXV を真ん中で割って重ね、9/24 の 2 本を主題曲に — 共鳴する重低音と 4 オクターヴ半の交響曲 (♩=60)',
        legend=['PF'], vname={'PF': 'ピアノ'},
        footer=['Introitus (08:53) → 第 1 部 I + III (ホ短調) → Interludium (08:49) → 第 2 部 II + IV (ヘ短調) → Amen (ヘ長調)',
                '重ねた 2 つの半分は調をそろえ、主題曲の主題を 4 倍で歌わせ、根音をミ 1 からオクターヴで響かせる。すべてピアノの実音。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    ms = [e['m'] for e in out['extras'] if e['v'] == 'PF']
    from collections import Counter
    print('duration %.0f s (%d:%02d)  PF %d  range %s..%s (%.1f octaves)  layers %s' % (T, T // 60, T % 60, len(ms), name_of(min(ms)), name_of(max(ms)),
          (max(ms) - min(ms)) / 12, dict(Counter(e.get('layer') for e in out['extras']))))

if __name__ == '__main__':
    main()
