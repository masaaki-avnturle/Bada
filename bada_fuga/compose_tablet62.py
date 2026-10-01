#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXII · Requiem e Fuga in re (LXI に、プロの楽曲のトラック 18 の雰囲気を合わせて — 実音のピアノだけで)
  トラック 18 も、音そのもの・旋律は使っていない。解析で得た雰囲気だけを借りる:
    - ニ短調、♩≈123、軽い響き (低音が薄い)、細かく動く音 (1 秒に 4〜8 打) → この曲はニ短調、♩=62 (8 分音符が 1 分に 124 = トラック 18 の速さ)
    - 調の道のり: ニ短調 → イ短調 → 変ロ → (ト短調) → ヘ長調 → ニ短調 → ニ長調 → ニ短調で消える
      → Requiem (ニ短調) → Fuga I (イ短調) → Lacrimosa (変ロ短調) → Fuga II (ニ短調、途中で下属調のト短調) → Amen (ニ長調)
    - 50 秒・100 秒あたりの静かな谷 → Lacrimosa (録音の実音だけの静けさ)
  LXI からの変更:
    - ドラムを外し、すべて実音のピアノ (録音から切り出した 1 音) で。トラック 18 の細かい動きは、ピアノの左手の 8 分音符の刻み (PF) で —
      根音・根音・5 度・オクターヴ (和音の根音、低い音域)。バラードの後半は 4 分音符でそっと、フーガは 8 分音符で
    - Introitus の 15:20 の録音 (ホ短調) は、テープのように全音下げてニ短調に (速さも 1 割ほどゆっくり、ピアノの音色はそのまま)
  形式 (♩=62): Introitus (15:20 の実音、ニ短調へ) → Requiem aeternam (12:50・13:04 の主題のコラール) → Fuga I (15:12 の主題, イ短調)
    → Lacrimosa (15:16 の実音, 変ロ短調) → Fuga II (15:20 の主題, ニ短調, ストレッタが山) → Amen (ニ長調)
  使い方: python compose_tablet62.py <bank61.json> [score_tablet62.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet61 as LXI

add, hm = CT.add, T3.hm
BPM = 62
R12, R16, R20, Q46, Q50, Q04 = LXI.R12, LXI.R16, LXI.R20, LXI.Q46, LXI.Q50, LXI.Q04
KEYS, ORDER, VOICE_SRC, DYNK = LXI.KEYS, LXI.ORDER, LXI.VOICE_SRC, LXI.DYNK
INTRO_TAPE = -2                                    # Introitus の録音をテープのように全音下げる (ホ短調 → ニ短調)
PULSE = []                                         # (b0, b1, 大きさ, 'eighth' / 'quarter', 区間の移調)

def post(P, events, extras):
    for b0, b1, g, mode, semis in PULSE:                  # 左手の刻み: 根音・根音・5 度・オクターヴ (エンジンのニ短調で書き、finish で区間の調へ)
        for bar in range(b0, b1):
            for h in range(2):
                c = chord(P.harm[bar * BPB + 2 * h] or 'Dm'); lo = 40 - semis; r = lo + (c['root'] - lo) % 12     # 鳴る音域はミ 2〜レ# 3
                fifth = r + 7 if (r + 7) % 12 in c['pcs'] else r + 12
                if mode == 'eighth':
                    for k, (m, a) in enumerate(((r, 1.0), (r + 12, 0.7), (fifth, 0.8), (r + 12, 0.7))):
                        add('PF', bar * BPB + 2 * h + 0.5 * k, 0.45, m, g * a, None, rid=VOICE_SRC['B'], rel=0.3)
                else:
                    for k, (m, a) in enumerate(((r, 1.0), (fifth, 0.75))):
                        add('PF', bar * BPB + 2 * h + k, 0.9, m, g * a, None, rid=VOICE_SRC['B'], rel=0.4)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], BPM); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    total = 4 + 8 + 16 + 4 + 16 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def excerpt(rid, bars, title, sub, semis_out, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, bpm=BPM, gmul=0.6)
        for v in VOICES: P.rest_bars(v, b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, semis_out, {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, VOICE_SRC, {})); b += bars; return f
    # ================= Introitus (15:20 の実音、テープのように全音下げてニ短調へ)
    excerpt(R20, 4, 'Introitus — %s の実音 (ニ短調へ)' % hm(R20), '9/29 15:20 のピアノの実音 (録音) を、テープのように全音下げて', 0)
    # ================= Requiem aeternam (ニ短調)
    f = section('Requiem aeternam — コラール (ニ短調)', '%s・%s の主題を 2 倍の長さで、ピアノの 4 声に — 後半から左手が 4 分音符でそっと刻む' % (hm(Q50), hm(Q04)), 8, 0)
    for k, r in enumerate([Q50, Q04]):
        LXI.place(P, f + 4 * k, LXI.aug(LXI.subj(r)), 'コラール (%s) · 2 倍' % hm(r))
        T5.harm_from_entries(P, f + 4 * k, f + 4 * k + 4, [((f + 4 * k) * BPB, LXI.aug(LXI.subj(r)))])
    for k in range(8): P.dyn[f + k] = DYNK * (0.62 if k < 4 else 0.72)
    PULSE.append((f + 4, f + 8, 0.26, 'quarter', 0))
    # ================= Fuga I (15:12 の主題, イ短調)
    f = section('Fuga I (イ短調)', '%s の主題の 4 声フーガ — 2 声目の入りの後から、左手の 8 分音符の刻み (トラック 18 の速さ)' % hm(R12), 16, -5)
    n_ = T11.bach_fugue(P, f, R12, '①')
    for k in range(n_): P.dyn[f + k] = DYNK * 0.74
    PULSE.append((f + 2, f + 14, 0.33, 'eighth', -5))
    # ================= Lacrimosa (15:16 の実音, 変ロ短調)
    excerpt(R16, 4, 'Lacrimosa — %s の実音 (変ロ短調)' % hm(R16), '9/29 15:16 のピアノの実音 (録音) — 刻みが止まる静かな谷', KEYS[R16])
    # ================= Fuga II (15:20 の主題, ニ短調)
    f = section('Fuga II (ニ短調)', '%s の主題のフーガ — すぐに左手の 8 分音符、下属調 (ト短調) の入りを経て、ストレッタが曲の山' % hm(R20), 16, 0)
    n_ = T11.bach_fugue(P, f, R20, '②')
    for k in range(n_): P.dyn[f + k] = DYNK * (0.78 if k < 12 else 0.86)
    PULSE.append((f + 1, f + 14, 0.36, 'eighth', 0))
    # ================= Amen (変格終止 → ニ長調)
    f = section('Amen — 変格終止 (ニ長調の和音で)', 'iv → I: 刻みが止まり、ピアノが長調の和音で静かに閉じる', 3, 0)
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.7
    assert b == total, (b, total)
    return P

def tape_intro(d, bars=4):
    """Introitus の録音をテープのように INTRO_TAPE 半音動かす: 録音は速さごと変わるので、採譜の表示も時間を伸ばして合わせる"""
    ratio = 2 ** (INTRO_TAPE / 12.0); t_end = d['bar_times'][bars]; spb = 60.0 / BPM
    for e in d['extras']:
        if e['v'] == 'REC' and e['t'] < 1e-3: e['semis'] = INTRO_TAPE
    keep = []
    for e in d['extras']:
        if e['v'] == 'TB' and e['t'] < t_end - 1e-3:
            e['t'] = round(e['t'] / ratio, 6); e['d'] = round(e['d'] / ratio, 6)
            e['beat'] = round(e['beat'] / ratio, 6); e['dbeats'] = round(e.get('dbeats', e['d'] / spb) / ratio, 6)
            if e['t'] >= t_end - 0.05: continue    # 伸ばした分、区間の外へ出た採譜は消す
        keep.append(e)
    d['extras'] = keep

def fix_pulse(d):
    """左手の刻みが、そのとき鳴っている 4 声と半音でぶつかったら、鳴っている音の音名へ寄せる (寄せられなければ休む)"""
    keep, moved, dropped = [], 0, 0
    for e in d['extras']:
        if e['v'] == 'PF':
            t0, t1 = e['t'], e['t'] + min(e['d'], 0.3)
            snd = [n for n in d['notes'] if n['t'] - 1e-3 < t1 and e['t'] < n['t'] + n['d'] - 1e-3]
            if any((e['m'] - n['m']) % 12 in (1, 11) for n in snd):
                pcs = {n['m'] % 12 for n in snd}
                cand = [e['m'] + dm for dm in (-1, 1, -2, 2, -3, 3, -4, 4, -5, 5)
                        if (e['m'] + dm) % 12 in pcs and not any((e['m'] + dm - n['m']) % 12 in (1, 11) for n in snd)]
                if not cand: dropped += 1; continue
                e['m'] = cand[0]; moved += 1
        keep.append(e)
    d['extras'] = keep
    print('pulse: moved', moved, 'dropped', dropped)

META = {k: v for k, v in LXI.META.items()}
META.update(
    title='Requiem BADA — LXII · Requiem e Fuga in re',
    subtitle='トラック 18 の雰囲気 (ニ短調 ♩≈123、軽く細かい動き) を合わせて — 実音のピアノだけで (♩=62)',
    legend=['TB', 'PF'], vname={'PF': '左手の刻み'},
    footer=['Introitus 15:20 (ニ短調へ) → Requiem → Fuga I (15:12, イ短調) → Lacrimosa 15:16 → Fuga II (15:20, ニ短調) → Amen (ニ長調)',
            'すべて録音から切り出したピアノの実音。プロの楽曲からは調・速さ・調の道のり・動きの細かさだけを借りた (音と旋律は使っていない)。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet62.json'
    compose.main(out, seed=162, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LXI と同じ)
    tape_intro(d); fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']), 'duration', d['duration'])
