#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXIII · Summa sintetica (集大成 XXII のピアノの音を、11:21 のシンセサイザーの実音一色に)
  XXII の全音を、2026-09-24 の 2 曲目 (11:21) から切り出したシンセサイザーの持続音の実音 (rid 'VOXSY') に置き換えた。
  実音のピアノの抜粋は、各録音の採譜 (打鍵ごとの和音と長さ) をこのシンセの実音で鳴らし直す (synth_passage)。
  4 声のフーガ、B-A-D-A、保続低音、鼓動 (シンセの低い音を 160 Hz 以下に)、最後の和音もすべてこのシンセ。洗脳的: 減衰しない持続音、鼓動、ストレッタ。
  以下は XXII の説明:
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
  使い方: python compose_tablet23.py <bank.json (9/23・9/24 の採譜と 1 音)> [score_tablet22.json]
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
SYN = 'VOXSY'
VOICE_SRC = {v: SYN for v in VOICES}

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:                                 # 鼓動 (pp、ピアノの低い打鍵)
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=SYN)

def synth_passage(P, rid, bar, bars, semis, gain=0.62, t0=None):
    """実音の抜粋の代わりに: 録音の採譜 (打鍵ごとの和音・長さ) を 11:21 のシンセの実音で鳴らし直す。和声は録音の和音"""
    if t0 is None: t0, inside = T5.best_window(rid, semis, bars * BAR_S)
    else: inside = [x for x in REC[rid]['segs'] if t0 <= x['t'] < t0 + bars * BAR_S]
    T5.USED.setdefault(rid, []).append((t0, t0 + bars * BAR_S))
    for s_ in inside:
        beat = bar * BPB + (s_['t'] - t0) * BPM / 60.0; dur = max(0.4, s_['d'] * BPM / 60.0)
        for j, m in enumerate(sorted(s_['m'])):
            add('SP', beat + 0.01 * j, dur, m - semis, gain / (1 + 0.35 * (len(s_['m']) - 1)), None, rid=SYN, pan=(-0.25, 0.25, -0.1, 0.1)[j % 4])
    for k in range(bars):
        a, z = t0 + k * BAR_S, t0 + (k + 1) * BAR_S; w = {}
        for s_ in inside:
            ov = min(z, s_['t'] + s_['d']) - max(a, s_['t'])
            if ov > 0: w[s_['ch']] = w.get(s_['ch'], 0) + ov
        prev = None
        for s_ in REC[rid]['segs']:
            if s_['t'] <= a: prev = s_['ch']
        ch = max(w, key=w.get) if w else (prev or transpose_h([['Dm']], semis)[0][0])
        for q in range(BPB): P.harm[(bar + k) * BPB + q] = transpose_h([[ch]], -semis)[0][0]
    for v in VOICES: P.rest_bars(v, bar, bar + bars)
    for k in range(bars): P.dyn[bar + k] = 0.42

def chain(P, b, rids, semis, bars=10):
    st = b
    for i, r in enumerate(rids):
        synth_passage(P, r, st, bars - (XF if i < len(rids) - 1 else 0), semis)
        CT.LAYOUT.append((st, st + bars, semis, VOICE_SRC, {}))
        st += bars - XF
    end = st + XF
    for v in VOICES: P.rest_bars(v, b, end)
    T2.MANTRA.append((b, end, rids[0], ('PK',)))
    return end - b

def pivot(P, b, rid, semis_next):
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55)): add('SP', b * BPB + k * 0.5, 2.5, m, 0.2, None, rid=SYN, pan=(-0.2, 0.2)[k % 2])
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
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.7
    b = 0
    P.section(b, 'Introitus — 〈%s → %s〉 (ホ短調)' % (hm(E1), hm(E2)), '録音の採譜を 11:21 のシンセの実音で鳴らし直す — ♩=56 の柔らかい鼓動 (シンセの低い音) が最後まで止まらない')
    b += chain(P, b, [E1, E2], 2)
    # ---------------- Kyrie — Fuga I (ホ短調)
    f = b
    P.section(b, 'Kyrie — Fuga I 〈%s〉 (ホ短調)' % hm(E2), '08:53 の主題のバッハ風フーガ: 提示 → エピソード → 下属調の入り → ストレッタ → 拍ごとに打ち直す保続低音 — 4 声とも 11:21 のシンセの実音')
    n_ = T11.bach_fugue(P, b, E2, '②')
    for k in range(n_): P.dyn[f + k] = 0.78
    T2.MANTRA.append((f, f + n_, E2, ('PK',))); CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    pivot(P, b, E2, -4); b += 1
    # ---------------- Graduale — 実音 (変ロ短調)
    P.section(b, 'Graduale — 〈%s → %s〉 (変ロ短調)' % (hm(B1), hm(B2)), '9/23 08:06 から 9/24 11:18 へ — 採譜をシンセの実音で')
    b += chain(P, b, [B1, B2], -4)
    # ---------------- Dies irae — Fuga II (変ロ短調)
    f = b
    P.section(b, 'Dies irae — Fuga II 〈%s · %s〉 (変ロ短調)' % (hm(E1), hm(B2)), '11:23 と 11:18 の主題の二重フーガ — 荘厳に')
    labmap = double_fugue(P, f, E1, B2)
    for k in range(10): P.dyn[f + k] = 0.76
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    pivot(P, b, RF, 3); b += 1
    # ---------------- Offertorium — 実音 (ヘ短調)
    P.section(b, 'Offertorium — %s の実音 (ヘ短調)' % hm(RF), '08:49 の採譜をシンセの実音で 43 秒')
    synth_passage(P, RF, b, 10, 3)
    T2.MANTRA.append((b, b + 10, RF, ('PK',))); CT.LAYOUT.append((b, b + 10, 3, VOICE_SRC, {})); b += 10
    # ---------------- Sanctus — Fuga III (ヘ短調)
    f = b
    P.section(b, 'Sanctus — Fuga III 〈%s · %s〉 (ヘ短調)' % (hm(B1), hm(E3)), '9/23 の 2 本、08:06 と 08:09 の主題の二重フーガ')
    labmap = double_fugue(P, f, B1, E3, ans=0)
    for k in range(10): P.dyn[f + k] = 0.762
    T2.MANTRA.append((f, f + 10, B1, ('PK',))); CT.LAYOUT.append((f, f + 10, 3, VOICE_SRC, labmap)); b = f + 10
    # ---------------- Agnus Dei — B-A-D-A
    a0 = b
    P.section(b, 'Agnus Dei — B-A-D-A', 'シリーズの印 B-A-D-A を 2 回、保続低音の上で — 洗脳的な繰り返し')
    for k in range(2):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, T11.PED, 0, None)
    P.hold.update(range(b, b + 4))
    for k in range(4): P.dyn[b + k] = 0.62
    T2.MANTRA.append((a0, a0 + 4, RF, ('PK',))); CT.LAYOUT.append((a0, a0 + 4, 3, VOICE_SRC, {})); b = a0 + 4
    # ---------------- Finale (ヘ短調): 7 つの主題のストレッタ → 保続低音
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ヘ短調)', '7 本の録音の主題が次々と入り、最後の 3 つはストレッタで重なる → 拍ごとに打ち直す保続低音')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    for k in range(14): P.dyn[f + k] = 0.78
    T2.MANTRA.append((f, f + 14, RF, ('PK',))); CT.LAYOUT.append((f, f + 14, 3, VOICE_SRC, labmap)); b = f + 14
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, T11.PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    for k in range(3): P.dyn[b + k] = 0.66
    T2.MANTRA.append((b, b + 3, RF, ('PK',))); CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    # ---------------- In paradisum: 08:49 の本当の終わり → ヘ長調 (pp)
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(RF), '08:49 の最後の 21 秒の採譜をシンセの実音で (属和音で止まる) → ヘ長調の和音をシンセが静かに分散して、鼓動とともに消えていく')
    synth_passage(P, RF, b, 5, 3, t0=end_f)
    T2.MANTRA.append((b, b + 7, RF, ('PK',))); CT.LAYOUT.append((b, b + 5, 3, VOICE_SRC, {})); b += 5
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((38, 45, 50, 54, 57, 62, 66)): add('SP', b * BPB + k * 0.4, 8.0, m, 0.2, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, -0.2, 0.2)[k])
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [SYN], 'src_name': {SYN: '11:21 のシンセ (実音)'},
    'title': 'Requiem BADA — Tablet Sessions XXIII · Summa sintetica',
    'subtitle': '集大成 XXII を、11:21 のシンセサイザーの実音一色で — 荘厳で洗脳的なレクイエムとフーガ (♩=56)',
    'legend': ['SP', 'PK'], 'vname': {'SP': '11:21 のシンセ (採譜の鳴らし直し)', 'PK': '鼓動 (シンセの低い音)'},
    'footer': ['Introitus 11:23 → 08:53 (ホ短調) → Kyrie: Fuga I → Graduale 9/23 08:06 → 11:18 (変ロ短調) → Dies irae: Fuga II → Offertorium 08:49 (ヘ短調) → Sanctus: Fuga III → Agnus Dei: B-A-D-A → Finale → In paradisum',
               '音はすべて 11:21 の録音から切り出したシンセの持続音 (実音)。抜粋は録音の採譜を鳴らし直したもの。バッハ風のフーガ、ストレッタ、打ち直す保続低音、鼓動。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet23.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    import json
    d = json.load(open(out))
    for nt in d['notes']: nt['src'] = SYN
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
