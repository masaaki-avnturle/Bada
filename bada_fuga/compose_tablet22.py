#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXII · Summa (集大成 — ゲームのような音を消した、荘厳で洗脳的なレクイエムとフーガ)
  VI〜XXI の集大成。合成の楽器 (ガラスの高音、共鳴シンセ、リード、パッド、低音の正弦波、ロックバンド、パイプオルガン) をすべて消し、
  鳴る音は 2026-09-23 / 09-24 の録音 7 本の実録音のピアノだけ:
    - 実音の抜粋 (速さも音高も元のまま、8 秒のクロスフェードでつなぐ)
    - 録音から切り出したピアノの 1 音 (自然に減衰) による 4 声のフーガ — バッハ風 (提示 → エピソード → 下属調 → ストレッタ → 拍ごとに打ち直す保続低音)
    - シリーズの印 B-A-D-A のマントラ、7 つの主題のストレッタ、ピアノの低い打鍵から作った柔らかい鼓動 (♩=56、最後まで止まらない)
  荘厳: Adagio、短調 (ホ短調 → 変ロ短調 → ヘ短調)、低い保続低音。洗脳的: 鼓動、同じ主題の重なり (ストレッタ)、B-A-D-A の繰り返し。
    Introitus — 11:23 → 08:53 (ホ短調) の実音 / Kyrie — Fuga I: 08:53 のバッハ風フーガ
    Graduale — 9/23 08:06 → 11:18 (変ロ短調) の実音 / Dies irae — Fuga II: 11:23 と 11:18 の二重フーガ
    Offertorium — 08:49 (ヘ短調) の実音 / Sanctus — Fuga III: 9/23 08:06 と 08:09 の二重フーガ
    Agnus Dei — B-A-D-A ×2 (保続低音) / Finale — 7 つの主題のストレッタ → 保続低音 / In paradisum — 08:49 の本当の終わり → ヘ長調 (pp)
  使い方: python compose_tablet22.py <bank.json (9/23・9/24 の採譜と 1 音)> [score_tablet22.json]
"""
import sys
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11       # バッハ風フーガ (bach_fugue), 保続低音 (PED)

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 56; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:                                 # 鼓動 (pp、ピアノの低い打鍵)
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=rid)

def chain(P, b, rids, semis, bars=10):
    st = b
    for i, r in enumerate(rids):
        T5.passage(P, r, st, bars, semis, bars, fin=(1.5 if i == 0 else XF * BAR_S), fout=(XF * BAR_S if i < len(rids) - 1 else 3.0), bpm=BPM, gmul=0.65)
        CT.LAYOUT.append((st + (XF if i else 0), st + bars, semis, {v: r for v in VOICES}, {}))
        st += bars - XF
    end = st + XF
    for v in VOICES: P.rest_bars(v, b, end)
    T2.MANTRA.append((b, end, rids[0], ('PK',)))
    return end - b

def pivot(P, b, rid, semis_next):
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55)): add('PF', b * BPB + k * 0.5, 2.5, m, 0.16, None, rid=rid, rel=1.5)
    T2.MANTRA.append((b, b + 1, rid, ('PK',))); CT.LAYOUT.append((b, b + 1, semis_next, VOICE_SRC, {}))

def double_fugue(P, f, ra, rb, ans=7):
    entries, labmap = [], {}
    for bar, v, r, tr0 in ((0, 'A', ra, 0), (2, 'S', rb, 0), (4, 'T', ra, ans), (6, 'B', rb, 0), (8, 'S', ra, 0), (8, 'T', rb, 0)):
        T7.entry(P, f + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    return labmap

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_f = REC[RF]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(RF, []).append((end_f, REC[RF]['dur']))
    total = 18 + 16 + 1 + 18 + 10 + 1 + 10 + 10 + 4 + 14 + 3 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.15
    b = 0
    P.section(b, 'Introitus — 〈%s → %s〉 (ホ短調)' % (hm(E1), hm(E2)), '実録音のピアノをそのまま、8 秒のクロスフェードでつなぐ — ♩=56 の柔らかい鼓動 (ピアノの低い打鍵) が最後まで止まらない')
    b += chain(P, b, [E1, E2], 2)
    # ---------------- Kyrie — Fuga I (ホ短調)
    f = b
    P.section(b, 'Kyrie — Fuga I 〈%s〉 (ホ短調)' % hm(E2), '08:53 の主題のバッハ風フーガ: 提示 → エピソード → 下属調の入り → ストレッタ → 拍ごとに打ち直す保続低音 — 4 声とも実録音のピアノ')
    n_ = T11.bach_fugue(P, b, E2, '②')
    for k in range(n_): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + n_, E2, ('PK',))); CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    pivot(P, b, E2, -4); b += 1
    # ---------------- Graduale — 実音 (変ロ短調)
    P.section(b, 'Graduale — 〈%s → %s〉 (変ロ短調)' % (hm(B1), hm(B2)), '9/23 08:06 から 9/24 11:18 へ、実音のまま')
    b += chain(P, b, [B1, B2], -4)
    # ---------------- Dies irae — Fuga II (変ロ短調)
    f = b
    P.section(b, 'Dies irae — Fuga II 〈%s · %s〉 (変ロ短調)' % (hm(E1), hm(B2)), '11:23 と 11:18 の主題の二重フーガ — 荘厳に')
    labmap = double_fugue(P, f, E1, B2)
    for k in range(10): P.dyn[f + k] = 1.25
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    pivot(P, b, RF, 3); b += 1
    # ---------------- Offertorium — 実音 (ヘ短調)
    P.section(b, 'Offertorium — %s の実音 (ヘ短調)' % hm(RF), 'ループせずそのまま 43 秒')
    T5.passage(P, RF, b, 10, 3, 10, fin=1.5, fout=3.0, bpm=BPM, gmul=0.65)
    for v in VOICES: P.rest_bars(v, b, b + 10)
    T2.MANTRA.append((b, b + 10, RF, ('PK',))); CT.LAYOUT.append((b, b + 10, 3, {v: RF for v in VOICES}, {})); b += 10
    # ---------------- Sanctus — Fuga III (ヘ短調)
    f = b
    P.section(b, 'Sanctus — Fuga III 〈%s · %s〉 (ヘ短調)' % (hm(B1), hm(E3)), '9/23 の 2 本、08:06 と 08:09 の主題の二重フーガ')
    labmap = double_fugue(P, f, B1, E3, ans=0)
    for k in range(10): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + 10, B1, ('PK',))); CT.LAYOUT.append((f, f + 10, 3, VOICE_SRC, labmap)); b = f + 10
    # ---------------- Agnus Dei — B-A-D-A
    a0 = b
    P.section(b, 'Agnus Dei — B-A-D-A', 'シリーズの印 B-A-D-A を 2 回、保続低音の上で — 洗脳的な繰り返し')
    for k in range(2):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, T11.PED, 0, None)
    P.hold.update(range(b, b + 4))
    for k in range(4): P.dyn[b + k] = 1.0
    T2.MANTRA.append((a0, a0 + 4, RF, ('PK',))); CT.LAYOUT.append((a0, a0 + 4, 3, VOICE_SRC, {})); b = a0 + 4
    # ---------------- Finale (ヘ短調): 7 つの主題のストレッタ → 保続低音
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ヘ短調)', '7 本の録音の主題が次々と入り、最後の 3 つはストレッタで重なる → 拍ごとに打ち直す保続低音')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    for k in range(14): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + 14, RF, ('PK',))); CT.LAYOUT.append((f, f + 14, 3, VOICE_SRC, labmap)); b = f + 14
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, T11.PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    for k in range(3): P.dyn[b + k] = 1.1
    T2.MANTRA.append((b, b + 3, RF, ('PK',))); CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    # ---------------- In paradisum: 08:49 の本当の終わり → ヘ長調 (pp)
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(RF), '08:49 の最後の 21 秒を実音のまま (属和音で止まる) → ヘ長調の和音をピアノが静かに分散して、鼓動とともに消えていく')
    T5.passage(P, RF, b, 5, 3, 5, fin=1.0, fout=2.5, t0=end_f, bpm=BPM, gmul=0.7)
    for v in VOICES: P.rest_bars(v, b, b + 5)
    T2.MANTRA.append((b, b + 7, RF, ('PK',))); CT.LAYOUT.append((b, b + 5, 3, {v: RF for v in VOICES}, {})); b += 5
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((38, 45, 50, 54, 57, 62, 66)): add('PF', b * BPB + k * 0.4, 3.5, m, 0.18, None, rid=RF, rel=3.0)
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XXII · Summa',
    'subtitle': '集大成 — 合成の音を消し、実録音のピアノだけで、荘厳で洗脳的なレクイエムとフーガ (♩=56)',
    'legend': ['TB', 'PK'], 'vname': {'PK': '鼓動 (ピアノの低い打鍵)'},
    'footer': ['Introitus 11:23 → 08:53 (ホ短調) → Kyrie: Fuga I → Graduale 9/23 08:06 → 11:18 (変ロ短調) → Dies irae: Fuga II → Offertorium 08:49 (ヘ短調) → Sanctus: Fuga III → Agnus Dei: B-A-D-A → Finale → In paradisum',
               '音はすべて 9/23・9/24 の実録音のピアノ (抜粋と、切り出した 1 音)。シンセ・オルガン・バンドはなし。バッハ風のフーガ、ストレッタ、打ち直す保続低音、鼓動。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet22.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
