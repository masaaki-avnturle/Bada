#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions X · Alto e basso (高音と低音の差が大きく、やさしい、実音のピアノと洗脳的なシンセ)
  Tablet Sessions IX から、近い音を上下する警笛のようなオスティナート (根音・5 度・3 度・5 度の 8 分音符) を外し、
  2026-09-23 / 09-24 のピアノ録音 6 本 (ピアノとシンセの録音 11:21 は除く) の実音とそのレクイエムとフーガに、
  高音と低音が大きく離れたやさしいシンセサイザーを重ねる:
    - 高音 (C6〜C7 あたり): ガラスのような柔らかい音 (GL) が、大きく跳ぶ分散和音 (隣り合う音へは動かない) を毎小節同じ形で
    - 低音 (F1〜E2 あたり): やさしい正弦波 (SUB) が和音の根音をゆっくり
    - その間 (中音域) に実音のピアノと、4 声 (録音の 1 音、ピアノのように自然に減衰)
    - ♩=60 の柔らかい鼓動 (録音の低い打鍵) は最後まで止まらない
  実音の区間ではシンセは控えめ (高音は 1・3 拍目だけ)、フーガでは 8 分音符の分散和音。
    Introitus — Mix 11:23 → 08:53 (ホ短調) / Fuga I — 9/23 08:09 と 08:53 の二重フーガ
    Lacrimosa — Mix 9/23 08:06 → 11:18 (変ロ短調) / Sanctus — 08:49 (ヘ短調)
    Finale — 6 つの主題が 2 小節ごとに (ヘ短調) / In paradisum — 08:49 の本当の終わり → ヘ長調
  使い方: python compose_tablet10.py <bank.json> [score_tablet10.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2         # 鼓動 (post)
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7         # クロスフェードのミックス、主題の入り

add, REC, hm = CT.add, CT.REC, T3.hm
BPM, BAR_S = T7.BPM, T7.BAR_S
T7.KEYS.update({'20260923_080607': -4, '20260923_080918': 2})
KEYS = T7.KEYS
E1, E2, E3 = '20260924_112313', '20260924_085314', '20260923_080918'
B1, B2, F1 = '20260923_080607', '20260924_111846', '20260924_084937'
ORDER = [E1, E2, E3, B1, B2, F1]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥')))
VOICE_SRC = {'S': E3, 'A': E2, 'T': F1, 'B': B1}
SYN = []                             # (開始小節, 終了小節, 'sparse' / 'full')

def near(pc, target): return min((x for x in range(20, 110) if x % 12 == pc), key=lambda x: abs(x - target))

def post(P, events, extras):
    T2.post(P, events, extras)
    for b0, b1, mode in SYN:
        for bar in range(b0, b1):
            B0 = bar * BPB; c = chord(P.harm[B0] or 'Dm')
            add('SUB', B0, 3.6, near(c['root'], 36), 0.07 if mode == 'full' else 0.05, None)
            if mode == 'sparse':                                  # 実音の区間: 高音は 1・3 拍目だけ
                for q, pc in ((0, c['root']), (2, c['fifth'])):
                    add('GL', B0 + q, 1.5, near(pc, 88), 0.055, None, pan=(-0.3 if q == 0 else 0.3))
                continue
            for q in range(8):                                    # 大きく跳ぶ高音の分散和音 (毎小節同じ形)
                cq = chord(P.harm[B0 + q // 2] or 'Dm')
                pc, tg = [(cq['root'], 83), (cq['fifth'], 90), (cq['third'], 85), (cq['root'], 95),
                          (cq['fifth'], 83), (cq['third'], 92), (cq['root'], 88), (cq['fifth'], 95)][q]
                add('GL', B0 + q * 0.5, 0.9, near(pc, tg), 0.06 if q % 2 == 0 else 0.045, None, pan=(-0.35 if q % 2 == 0 else 0.35))

def pivot(P, b, rid):
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55, 61)): add('PF', b * BPB + k * 0.4, 2.0, m, 0.2, None, rid=rid, rel=1.5)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_t0 = REC[F1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(F1, []).append((end_t0, REC[F1]['dur']))
    total = 18 + 10 + 1 + 18 + 1 + 10 + 13 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.72
    b = 0
    P.section(b, 'Introitus — Mix 〈%s → %s〉' % (hm(E1), hm(E2)), 'ホ短調 ／ 実音のピアノ 2 本をつなぐ — 高音にガラスのような音、低音にやさしい正弦波、その間に実音')
    b += T7.mix(P, b, E1, E2)
    for v in VOICES: P.rest_bars(v, 0, b)
    T2.MANTRA.append((0, b, E1, ('PK',))); SYN.append((0, b, 'sparse'))
    # ---------------- Fuga I (ホ短調)
    f0 = b; entries, labmap = [], {}
    P.section(b, 'Fuga I — 主題 ③② 〈%s · %s〉' % (hm(E3), hm(E2)), '9/23 と 9/24 の主題の二重フーガ — 高音で大きく跳ぶ分散和音が毎小節同じ形で回り、低音がやさしく支える')
    for bar, v, r, tr0 in ((0, 'A', E3, 0), (2, 'S', E2, 0), (4, 'T', E3, 7), (6, 'B', E2, 0), (8, 'S', E3, 0), (8, 'T', E2, 0)):
        T7.entry(P, f0 + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f0, f0 + z)
    T5.harm_from_entries(P, f0, f0 + 10, entries)
    for k in range(10): P.dyn[f0 + k] = 1.0
    T2.MANTRA.append((f0, f0 + 10, E1, ('PK',))); SYN.append((f0, f0 + 10, 'full')); CT.LAYOUT.append((f0, f0 + 10, 2, VOICE_SRC, labmap))
    b = f0 + 10
    pivot(P, b, E2); T2.MANTRA.append((b, b + 1, E1, ('PK',))); CT.LAYOUT.append((b, b + 1, KEYS[B1], VOICE_SRC, {})); b += 1
    # ---------------- Lacrimosa — Mix (変ロ短調)
    s0 = b
    P.section(b, 'Lacrimosa — Mix 〈%s → %s〉' % (hm(B1), hm(B2)), '変ロ短調 ／ 9/23 08:06 から 9/24 11:18 へ実音のまま')
    b += T7.mix(P, b, B1, B2)
    for v in VOICES: P.rest_bars(v, s0, b)
    T2.MANTRA.append((s0, b, B1, ('PK',))); SYN.append((s0, b, 'sparse'))
    pivot(P, b, B2); T2.MANTRA.append((b, b + 1, B2, ('PK',))); CT.LAYOUT.append((b, b + 1, KEYS[F1], VOICE_SRC, {})); b += 1
    # ---------------- Sanctus (ヘ短調)
    P.section(b, 'Sanctus — 録音 %s の実音' % hm(F1), 'ヘ短調 ／ ループせずそのまま 40 秒')
    T5.passage(P, F1, b, 10, KEYS[F1], 10, fin=1.5, fout=3.0, bpm=BPM)
    T2.MANTRA.append((b, b + 10, F1, ('PK',))); SYN.append((b, b + 10, 'sparse'))
    CT.LAYOUT.append((b, b + 10, KEYS[F1], {v: F1 for v in VOICES}, {})); b += 10
    # ---------------- Finale (ヘ短調): 6 つの主題が 2 小節ごとに
    f1 = b; entries, labmap = [], {}
    P.section(b, 'Finale — Fuga a sei soggetti', '9/23・9/24 の 6 本の主題が 2 小節ごとに次々と — 高音の分散和音と低音が回り続ける (ヘ短調)')
    for k in range(6): T7.entry(P, f1 + 2 * k, ['A', 'S', 'T', 'B', 'S', 'A'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f1, f1 + z)
    T5.harm_from_entries(P, f1, f1 + 12, entries); P.set_harms(f1 + 12, [['Gm', 'Gm', 'A7', 'A7']])
    for k in range(13): P.dyn[f1 + k] = 1.05
    T2.MANTRA.append((f1, f1 + 13, F1, ('PK',))); SYN.append((f1, f1 + 13, 'full')); CT.LAYOUT.append((f1, f1 + 13, 3, VOICE_SRC, labmap))
    b = f1 + 13
    # ---------------- In paradisum
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(F1), '08:49 の最後の 20 秒を実音のまま → ヘ長調の和音が高音と低音に広がって、やさしく消えていく')
    T5.passage(P, F1, b, 5, KEYS[F1], 5, fin=1.0, fout=2.5, t0=end_t0, bpm=BPM)
    T2.MANTRA.append((b, b + 8, F1, ('PK',))); SYN.append((b, b + 5, 'sparse')); CT.LAYOUT.append((b, b + 5, KEYS[F1], {v: F1 for v in VOICES}, {}))
    b += 5
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((38, 45, 50, 54, 57, 62, 66)): add('PF', b * BPB + k * 0.35, 3.0, m, 0.22, None, rid=F1, rel=2.5)
    for k, m in enumerate((86, 93, 90, 98)): add('GL', b * BPB + 2.5 + k * 0.75, 1.5, m, 0.05, None, pan=(-0.3, 0.3)[k % 2])
    add('SUB', b * BPB, 8.0, 26, 0.06, None)
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.4,
    'title': 'Requiem BADA — Tablet Sessions X · Alto e basso',
    'subtitle': '高音と低音が大きく離れた、やさしい実音のピアノと洗脳的なシンセ — 9/23・9/24 のピアノ録音 6 本で',
    'legend': ['TB', 'GL', 'SUB', 'PK'],
    'footer': ['Introitus 11:23 → 08:53 → Fuga I (9/23 08:09 · 08:53) → Lacrimosa 9/23 08:06 → 11:18 → Sanctus 08:49 → Finale (6 つの主題) → In paradisum → ヘ長調',
               '警笛のような近い音の上下はなし。高音はガラスのような音が大きく跳ぶ分散和音、低音はやさしい正弦波、中音域に実音のピアノ。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet10.json'
    compose.main(out, seed=79, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
