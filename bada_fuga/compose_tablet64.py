#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXIV · Fuga per augmentationem XVI (LXIII の主題を 16 倍に拡大 — 4 分音符を伸ばす技法で、洗脳的なレクイエム)
  拡大 (augmentatio): 主題の音の長さを 16 倍にする — 4 分音符 1 つが 4 分音符 16 個分 (4 小節) になる。
  バッハの拡大カノン (Canon per augmentationem) と、ペルトの「ブリテンへの追悼歌」の、同じ旋律を違う速さで同時に鳴らすカノン (メンスーラ・カノン) にならい、
  LXIII の 2 つの主題 (Fuga I の 15:16、Fuga II の 15:12) を、1 倍・4 倍・16 倍の速さで同時に鳴らす:
    - 16 倍 (テノール): 伸ばした 4 分音符を、ピアノで 4 分音符ごとに打ち直す (16 倍に伸ばした 1 音 = 16 回の打鍵) — 時計のように止まらない ♩=60 の打鍵
    - 16 倍 (バス): 同じ旋律を 2 オクターヴ下で、小節の頭だけ打つ (深い鐘)
    - 4 倍 (アルト): 4 分音符が全音符に。1 回りのうちに 4 回
    - 1 倍 (ソプラノ): もとの速さの主題が 2 小節ごとに 16 回くり返される (マントラ)
    - 左手の 3 連の分散和音 (LXIII と同じ) は、主和音だけを鳴らし続ける (ペルトのティンティナブリのように和音が動かない)
  4 つの層は同じ音階だけを使うので、ぶつかる 2 度も同じ調の中の響きになる。層は 1 つずつ入り、16 倍の主題の最後の音 (主音) で全員がそろって終わる。
  洗脳的: ♩=60 (1 秒に 1 打) の止まらない打鍵、何分も動かない和音、同じ主題の 16 回のくり返し、ゆっくり大きくなってそろう終わり。
  形式 (♩=60): Introitus (15:20 の実音) → Canon I ×16 (15:16 の主題, イ短調, 32 小節) → Lacrimosa (15:19 の実音)
    → Canon II ×16 (15:12 の主題, ニ短調, 32 小節) → Amen (イ長調)
  すべて録音から切り出したピアノの実音。シンセ・ドラム・心臓の鼓動・弦・オルガンなし。
  使い方: python compose_tablet64.py <bank61.json> [score_tablet64.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet61 as LXI
import compose_tablet63 as LXIII

add, hm = CT.add, T3.hm
BPM = 60
R12, R16, R19, R20 = LXI.R12, LXI.R16, LXIII.R19, LXI.R20
KEYS, ORDER, VOICE_SRC, DYNK = LXIII.KEYS, LXIII.ORDER, LXI.VOICE_SRC, LXI.DYNK
AM, DM = LXIII.AM, LXIII.DM
CYCLE = 32                                         # 16 倍の主題 1 回り (8 拍 × 16 = 128 拍 = 32 小節)
SWELL = []                                         # (b0, b1) — 16 倍の層の打鍵に、1 音ごとのふくらみを付ける区間

def canon(P, f, rid, semis, num):
    """メンスーラ・カノン: 主題 (8 拍) を 16 倍 (T: 4 分音符で打ち直す / B: 小節の頭)・4 倍 (A)・1 倍 (S) で同時に"""
    s_ = T5.SUBJ[rid][0]; tag = '%s (%s)' % (num, hm(rid))
    P.set_harms(f, [['Dm'] * 4] * CYCLE)                             # 和音は主和音のまま動かない (ティンティナブリ)
    t16 = [(1, m) for d, m in s_ for _ in range(int(round(d * 16)))]            # 16 倍: 伸ばした 4 分音符を 1 拍ごとに打ち直す
    P.place('T', f, [(d, m - 12) for d, m in t16], 0, '主題 %s ×16 — 4 分音符を 16 倍に伸ばす' % tag)
    b16 = [(4, m) for d, m in s_ for _ in range(int(round(d * 4)))]             # 16 倍の深い鐘: 小節の頭だけ (2 オクターヴ下)
    P.place('B', f, [(d, m - 24) for d, m in b16], 0, '×16 (深い鐘)')
    P.rest_bars('A', f, f + 8)                                                    # 4 倍: 2 回り目から入る (8 小節で 1 回)
    for k in range(1, 4): P.place('A', f + 8 * k, [(d * 4, m) for d, m in s_], 0, '主題 %s ×4' % tag if k == 1 else None)
    P.rest_bars('S', f, f + 4)                                                    # 1 倍: 3 回目 (4 小節目) から 2 小節ごとに
    for k in range(2, 16): P.place('S', f + 2 * k, s_, 12, '主題 %s ×1 (マントラ)' % tag if k == 2 else None)
    for k in range(CYCLE): P.dyn[f + k] = DYNK * (0.7 + 0.25 * k / (CYCLE - 1))    # 32 小節かけてゆっくり大きく
    LXIII.ARP.append((f, f + CYCLE, 0.13, semis)); SWELL.append((f, f + CYCLE))

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = LXIII.smooth(CT.make_subject(inside, KEYS[r], 66)); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    for r in (R16, R12): print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
    total = 4 + CYCLE + 4 + CYCLE + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def excerpt(rid, bars, title, sub, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, bpm=BPM, gmul=0.6)
        for v in VOICES: P.rest_bars(v, b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, KEYS[rid], {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, VOICE_SRC, {})); b += bars; return f
    excerpt(R20, 4, 'Introitus — %s の実音 (ホ短調)' % hm(R20), '9/29 15:20 のピアノの実音 (録音) — ここから時間が 16 倍に伸びていく')
    f = section('Canon I · per augmentationem ×16 (イ短調)', '%s の主題を 16 倍・4 倍・1 倍で同時に — 16 倍の 4 分音符は 1 拍ごとに打ち直す' % hm(R16), CYCLE, AM)
    canon(P, f, R16, AM, '①')
    excerpt(R19, 4, 'Lacrimosa — %s の実音 (ト長調)' % hm(R19), '9/29 15:19 のピアノの実音 (録音) — 打鍵が止まる、ひとときの息')
    f = section('Canon II · per augmentationem ×16 (ニ短調)', '%s の主題を 16 倍・4 倍・1 倍で同時に — 全員が 16 倍の最後の音でそろう' % hm(R12), CYCLE, DM)
    canon(P, f, R12, DM, '②')
    f = section('Amen — 変格終止 (イ長調の和音で)', 'iv → I: 打鍵が止まり、イ長調の和音だけが残る', 3, AM + 12)
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.62
    LXIII.ARP.append((f, f + 2, 0.12, AM + 12))
    assert b == total, (b, total)
    return P

def swell(d):
    """16 倍の層 (T) の打ち直し: 1 音 (16〜32 打) の中で、頭を強く、あとは息をするようにふくらんで静まる"""
    spb = 60.0 / BPM; n_ = 0
    for b0, b1 in SWELL:
        t0, t1 = d['bar_times'][b0], d['bar_times'][b1]
        ts = sorted([x for x in d['notes'] if x['v'] == 'T' and t0 - 1e-3 <= x['t'] < t1 - 1e-3], key=lambda x: x['t'])
        runs, cur = [], []
        for x in ts:
            if cur and x['m'] != cur[-1]['m']: runs.append(cur); cur = []
            cur.append(x)
        if cur: runs.append(cur)
        for run in runs:
            L = len(run)
            for i, x in enumerate(run):
                ph = i / max(1, L - 1)
                x['dyn'] = round(x['dyn'] * (1.15 if i == 0 else 0.72 + 0.22 * np.sin(np.pi * ph)), 4); n_ += 1
    print('swell:', n_, 'strikes')

META = {k: v for k, v in LXI.META.items()}
META.update(
    rec_order=ORDER,
    title='Requiem BADA — LXIV · Fuga per augmentationem XVI',
    subtitle='LXIII の主題を 16 倍に — 伸ばした 4 分音符を 1 拍ごとに打ち直す、洗脳的なレクイエム (♩=60)',
    legend=['TB', 'PF'], vname={'PF': '分散和音'},
    footer=['Introitus 15:20 → Canon I ×16 (15:16, イ短調) → Lacrimosa 15:19 → Canon II ×16 (15:12, ニ短調) → Amen (イ長調)',
            '同じ主題を 16 倍 (テノール・バス)・4 倍 (アルト)・1 倍 (ソプラノ) で同時に。すべて録音から切り出したピアノの実音。'])

if __name__ == '__main__':
    import numpy as np
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet64.json'
    compose.main(out, seed=164, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LXIII と同じ)
    swell(d)
    import compose_tablet62 as LXII
    LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
