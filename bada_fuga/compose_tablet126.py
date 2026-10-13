#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXVI · Inno nel palazzetto (10/13 の 2 曲を、剣道の試合の前座、総合体育館に静かに流れる国歌の、冷たい空気の漂う礼拝のような曲に — あとの曲 (acceptance・LXXXVI・LXXXIX・子守歌・piano_solo_8x・CXXV) をベースに)
  ♩=52、ロ短調、長い残響 (10 秒)。鼓動なし、ドラムなし、鐘は始めと終わりに深いものがひとつ
    1. Inno I     10/13 06:41 の実音 (半音上げてロ短調に) — CXXV の Inno (06:41 の音の国歌のような旋律) を 4 声のユニゾンで静かに、句のあいだに間。1 句目は何も重ねず、2 句目から高い開いた 5 度の共鳴
    2. Preghiera  礼拝: 讃美歌 (13:06 の音、ロ短調の五音音階) を開いた 5 度のコラールで — テノールに acceptance のタブレットの主題 (シ・ラ・ソ・ラ・ソ・ファ#) の拡大、LXXXVI の Flower の旋律 (+7) が小さく、LXXXIX の伸ばした主題 (−3) と piano_solo_8x のロ短調の窓 (2160 秒〜) が遠くで
    3. Inno II    10/13 06:42 の実音 (半音上げて) — Inno がソプラノとテノール (1 小節遅れ) のカノンに、コラールが包む
    4. Silenzio   冷たい空気: 共鳴と piano_solo_8x だけ、子守歌 (ninna nanna 10・12) の大黒柱の主題 (+1) が 4 倍に伸びて低く
    5. Inno III   Inno の拡大 (×2) を 4 声のユニゾンで、高い開いた 5 度 — 讃美歌の第 4 句が答え、開いた 5 度のユニゾンで閉じる。深い鐘
  使い方: BANK1013=<bank1013.json> python compose_tablet126.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <score_tablet89.json> <score_tablet86.json> <wav のフォルダ> [score_tablet126.json]
"""
import sys, os, json, math
B1012B, B1012, B112, B109, SCORE89, SCORE86, WDIR = sys.argv[1:8]; OUT = sys.argv[8] if len(sys.argv) > 8 else 'score_tablet126.json'
sys.argv = [sys.argv[0], B1012B, B1012, B112, B109, WDIR, OUT]
import compose_tablet125 as T
from compose import *
import compose
import compose_heart as H
S89, S86 = json.load(open(SCORE89)), json.load(open(SCORE86))
RECS, R41, R42, WDIR = T.RECS, T.R41, T.R42, os.path.abspath(WDIR)
ANTHEM, HYMN, aphrase, phrase = T.ANTHEM, T.HYMN, T.aphrase, T.phrase
CANDS = T.CANDS_G; LOW = T.LOW; PSRC = T.R53
BPM = 52; RATE = T.RATE
ACC = [(3, 71), (1, 69), (1.5, 67), (0.5, 69), (1, 67), (1, 66)]                                    # acceptance のタブレットの主題: シ・ラ・ソ・ラ・ソ・ファ# (ロ短調)
PILLAR = [(1.5, 68 + 1), (1.5, 61 + 1), (1, 63 + 1), (1, 61 + 1), (1, 63 + 1), (0.5, 61 + 1), (0.5, 60 + 1), (1, 58 + 1)]      # 子守歌の大黒柱の主題 (+1 でロ短調に)
INNO1, PREG, INNO2, SIL, INNO3, TOTAL = 0, 22, 50, 68, 82, 100
PLAYS = [(R41, 2, 0.45, 1), (R42, INNO2 + 1, 0.45, 1)]
extras = T.extras; add = T.add; entry = T.entry; harm_fit = T.harm_fit; augment = T.augment; rest_others = T.rest_others

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.85
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = 'Bm'
        T.RH.append(cur); P.harm[q] = cur
    # 1. Inno I
    P.section(INNO1, '1. Inno I — 国歌が静かに流れる (ロ短調、ユニゾン)', '10/13 06:41 の実音 (半音上げて) の上で、Inno を 4 声のユニゾン (オクターヴ) で静かに — 句のあいだに間。1 句目は何も重ねず、2 句目から高い開いた 5 度の共鳴')
    rest_others(P, 0, 2, ''); E = []
    for k in range(4):
        b = 2 + 4 * k + (1 if k >= 2 else 0)
        for v in VOICES: entry(P, b, v, aphrase(k), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Inno 第 %d 句 (ユニゾン)' % (k + 1)) if v == 'S' else None, E)
        for v in VOICES: P.rest_bars(v, b + 3, b + 4 + (1 if k == 1 else 0))
    for v in VOICES: P.rest_bars(v, 19, PREG)
    for q in range(INNO1 * BPB, PREG * BPB): P.harm[q] = 'Bm'
    # 2. Preghiera
    P.section(PREG, '2. Preghiera — 礼拝 (開いた 5 度のコラール)', '讃美歌 (13:06 の音、ロ短調の五音音階) がソプラノに、テノールに acceptance の主題 (シ・ラ・ソ・ラ・ソ・ファ#) の拡大 — LXXXVI の Flower が小さく、LXXXIX と piano_solo_8x が遠くで')
    E = []
    for k in range(4): entry(P, PREG + 2 + 2 * k, 'S', phrase(k), -12, '讃美歌 第 %d 句' % (k + 1) if k < 1 else None, E)
    for k in range(4): entry(P, PREG + 12 + 2 * k, 'S', phrase(k), -12, None, E)
    for k in range(3): entry(P, PREG + 4 + 6 * k, 'T', augment(ACC), 0, 'acceptance の主題 (拡大 ×2)' if k == 0 else None, E)
    rest_others(P, PREG, PREG + 2, ''); P.rest_bars('T', PREG + 2, PREG + 4); P.rest_bars('T', PREG + 22, INNO2); P.rest_bars('S', PREG + 20, INNO2)
    P.hold.update(range(PREG + 2, INNO2)); harm_fit(P, PREG + 2, INNO2, E, CANDS)
    # 3. Inno II
    P.section(INNO2, '3. Inno II — カノン', '10/13 06:42 の実音 (半音上げて) の上で、Inno がソプラノとテノール (1 小節遅れ、オクターヴ下) のカノンに、コラールが包む')
    E = []; rest_others(P, INNO2, INNO2 + 1, '')
    for k in range(4):
        b = INNO2 + 1 + 4 * k; entry(P, b, 'S', aphrase(k), 0, 'Inno (カノン)' if k == 0 else None, E); entry(P, b + 1, 'T', aphrase(k), -12, None, E)
    P.rest_bars('T', INNO2 + 1, INNO2 + 2); P.hold.update(range(INNO2 + 1, SIL)); harm_fit(P, INNO2 + 1, SIL, E, CANDS)
    # 4. Silenzio
    P.section(SIL, '4. Silenzio — 冷たい空気', '共鳴と piano_solo_8x だけ — 子守歌の大黒柱の主題 (+1) が 4 倍に伸びて低く')
    E = []; entry(P, SIL, 'B', augment(PILLAR, 4), -24, '大黒柱の主題 (拡大 ×4)', E); rest_others(P, SIL, INNO3, 'B'); P.rest_bars('B', SIL + 8, INNO3)
    harm_fit(P, SIL, INNO3, E, CANDS)
    # 5. Inno III
    P.section(INNO3, '5. Inno III — 拡大のユニゾン、開いた 5 度', 'Inno の第 1 句と第 4 句の拡大 (×2) を 4 声のユニゾンで、高い開いた 5 度 — 讃美歌の第 4 句が答え、開いた 5 度 (シ・ファ#) のユニゾンで閉じる。深い鐘')
    E = []
    for k, ph in enumerate((0, 3)):
        b = INNO3 + 1 + 5 * k
        for v in VOICES: entry(P, b, v, augment(aphrase(ph)), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), 'Inno 第 %d 句 (拡大 ×2、ユニゾン)' % (ph + 1) if v == 'S' else None, E)
    rest_others(P, INNO3, INNO3 + 1, ''); E2 = []
    entry(P, INNO3 + 12, 'S', phrase(3), -12, '讃美歌 第 4 句 (答え)', E2); rest_others(P, INNO3 + 11, INNO3 + 14, 'S')
    for q in range(INNO3 * BPB, (TOTAL - 4) * BPB): P.harm[q] = 'Bm'
    for b in range(TOTAL - 4, TOTAL): P.set_harm(b, 'Bm'); P.hold.add(b)
    P.place('S', TOTAL - 4, [(4, 78)] * 4, 0, 'ファ# (開いた 5 度)'); P.place('A', TOTAL - 4, [(4, 71)] * 4, 0, ''); P.place('T', TOTAL - 4, [(4, 66)] * 4, 0, ''); P.place('B', TOTAL - 4, [(4, 47)] * 4, 0, ''); P.rest_bars('S', TOTAL - 1, TOTAL)
    for k in range(TOTAL): P.dyn[k] = 0.8 if k < INNO3 else 0.95 - 0.15 * max(0, k - (TOTAL - 4))
    return P

def notes86(b0, b1, semis, bar_at, bar_end, gain, label):
    first = True
    for n in S86['notes']:
        if not (b0 * BPB <= n['beat'] < b1 * BPB) or n['v'] != 'S': continue
        beat = bar_at * BPB + (n['beat'] - b0 * BPB)
        if beat >= bar_end * BPB: continue
        add('PF', beat, n['dbeats'] + 0.1, n['m'] + semis, gain * (0.62 * n.get('dyn', 1.0) + 0.08), label if first else None, rid=n.get('src'), rel=0.6, layer='86'); first = False

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 2 else 0.02, fout=4.0, semis=sm, rid=rid + '.wav', tag='10/13 %s — 実音 (半音上げてロ短調に)' % ('06:41' if rid == R41 else '06:42'))
    add('REC', PREG * BPB, (INNO2 - PREG) * BPB, 0, 0.1, None, src=os.path.join(WDIR, 'piano_solo_8x_bm.wav'), off=60.0, fin=10.0, fout=10.0, rid='piano_solo_8x.wav', tag='piano_solo_8x — ロ短調の窓 (遠くで)')
    add('REC', SIL * BPB, (INNO3 - SIL + 2) * BPB, 0, 0.12, None, src=os.path.join(WDIR, 'piano_solo_8x_bm.wav'), off=200.0, fin=8.0, fout=8.0, rid='piano_solo_8x.wav', tag=None)
    notes86(20, 36, 7, PREG + 4, INNO2 - 2, 0.3, 'LXXXVI Flower の旋律 (+7)')
    first = True
    for e in S89['extras']:
        if e['v'] != 'PF' or e['t'] >= 96: continue
        beat = PREG * BPB + e['beat'] * 0.5
        if beat >= (INNO2 - 1) * BPB: continue
        add('PF', beat, e['dbeats'] * 0.5 + 0.2, e['m'] - 3, e['gain'] * 0.25, 'LXXXIX の伸ばした主題 (−3、遠くで)' if first else None, rid=e.get('rid'), rel=0.6, layer='89'); first = False
    add('X', 0, 12, 35, 0.35, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 35, 0.4, None)
    q = 0; first = True
    while q < TOTAL * BPB:
        h = P.harm[q]; q1 = q
        while q1 < TOTAL * BPB and P.harm[q1] == h: q1 += 1
        for cut in (6 * BPB, PREG * BPB, SIL * BPB, INNO3 * BPB):
            if q < cut < q1: q1 = cut
        bar = q // BPB; d = max(1.0, (q1 - q) + 0.6); c = chord(h)
        if bar < 6: pass
        elif bar < PREG or bar >= INNO3:
            for i, m in enumerate((83, 90)): add('PF', q + 0.05 * i, d, m, 0.8 * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
            if bar >= INNO3:
                for i, m in enumerate((47, 54)): add('PF', q + 0.1 * i, d, m, 0.12, None, rid='VOXRS', rel=1.5, layer='res')
        else:
            tones = [min((x for x in range(52, 76) if x % 12 == p), key=lambda x: abs(x - 62)) for p in (c['root'], c['fifth'], c['third'])]
            g = 0.1 if bar < SIL else 0.13
            for i, m in enumerate(tones): add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.7), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
            add('PF', q, d, tones[0] - 12, g * 0.6, None, rid='VOXRS', rel=1.5, layer='res')
        q = q1

META = dict(T.META, rec_order=[R41, R42, T.R53], reverb=[10.0, 3.5, 0.55], piano_decay=2.8,
            title='Requiem BADA — CXXVI · Inno nel palazzetto',
            subtitle='10/13 06:41・06:42 — 剣道の試合の前座、総合体育館に静かに流れる国歌、冷たい空気の漂う礼拝のように: Inno I (ユニゾン) → Preghiera (開いた 5 度のコラール、acceptance の主題、LXXXVI・LXXXIX・piano_solo_8x が遠くで) → Inno II (カノン) → Silenzio (子守歌の主題が低く) → Inno III (拡大のユニゾン)。ロ短調、♩=52、残響 10 秒',
            footer=['Inno = CXXV (06:41 の音をロ短調の五音音階と国歌のリズムに)。讃美歌 = 13:06 の音。acceptance の主題 シ・ラ・ソ・ラ・ソ・ファ#。大黒柱の主題 (子守歌 10・12) +1',
                    '鼓動なし、ドラムなし。鐘は始めと終わりに深いものがひとつ。7th なし、開いた 5 度。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    compose.main(OUT, seed=126, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.4 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 10); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
