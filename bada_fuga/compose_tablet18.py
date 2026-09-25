#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XVIII · Lacrimosa (ピアノを消し、11:21 のシンセサイザーの実音だけで歌う、悲しみのフーガのレクイエム)
  XVII から、ピアノをすべて消した: 実音のピアノの録音、ピアノの 1 音のサンプラー、ピアノの低音から作った鼓動、パイプオルガン。
  残る楽器は、2026-09-24 の 2 曲目 (11:21、ピアノとシンセを重ねた録音) から切り出したシンセサイザーの持続音の実音 (build_synthbank.py) だけ。
  4 声のフーガをこの実音が歌い (rid 'VOXSY'、減衰させずループで伸ばす)、その下で同じ実音の低い持続音が支える。
  旋律は 9/23・9/24 の録音 7 本から作った主題。Adagio (♩=52)、短調のまま終わる (ピカルディ終止なし)、最後は半音で下がる嘆きの低音。
    Introitus — 持続音だけ / Kyrie — Fuga I: 08:53 のバッハ風フーガ (ホ短調)
    Lacrimosa — Fuga II: 11:23 と 11:18 の二重フーガ (変ロ短調) / Fuga III: 9/23 08:06 と 08:09 の二重フーガ (変ロ短調)
    Finale — 7 つの主題のストレッタ (ヘ短調) → 嘆きの低音 (半音で下がる) → ヘ短調の和音が消えていく
  使い方: python compose_tablet18.py <bank.json (9/23・9/24 の採譜 + 11:21 のシンセ)> [score_tablet18.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11       # バッハ風フーガ (bach_fugue)

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 52
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
SYN = 'VOXSY'
VOICE_SRC = {v: SYN for v in VOICES}
DRONES = []                          # (開始小節, 終了小節, 大きさ) — 同じ実音の低い持続音

def near(pc, target): return min((x for x in range(30, 60) if x % 12 == pc), key=lambda x: abs(x - target))

def post(P, events, extras):
    for b0, b1, g in DRONES:
        for bar in range(b0, b1, 2):
            c = chord(P.harm[bar * BPB] or 'Dm'); nb = min(2, b1 - bar)
            add('SP', bar * BPB, nb * BPB + 0.6, near(c['root'], 38), g, None, rid=SYN, pan=0.0)
            add('SP', bar * BPB, nb * BPB + 0.6, near(c['fifth'], 45), g * 0.6, None, rid=SYN, pan=0.3)

def double_fugue(P, f, ra, rb, lab_a, lab_b, ans=7):
    entries, labmap = [], {}
    for bar, v, r, tr0 in ((0, 'A', ra, 0), (2, 'S', rb, 0), (4, 'T', ra, ans), (6, 'B', rb, 0), (8, 'S', ra, 0), (8, 'T', rb, 0)):
        T7.entry(P, f + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    return labmap

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 52); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    total = 4 + 16 + 1 + 10 + 10 + 1 + 14 + 4 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.9
    b = 0
    P.section(b, 'Introitus — 11:21 のシンセの実音の持続音', 'ピアノはない。録音 11:21 から切り出したシンセサイザーの実音だけが、低く鳴り始める (ホ短調)')
    for v in VOICES: P.rest_bars(v, b, b + 4)
    P.set_harms(b, [['Dm']] * 4); DRONES.append((b, b + 4, 0.3)); CT.LAYOUT.append((b, b + 4, 2, VOICE_SRC, {})); b += 4
    # ---------------- Kyrie — Fuga I (ホ短調)
    f = b
    P.section(b, 'Kyrie — Fuga I 〈%s〉 (ホ短調)' % hm(E2), '08:53 の主題のバッハ風フーガ — 4 声とも 11:21 のシンセの実音。提示 → エピソード → 下属調 → ストレッタ → 保続低音')
    n_ = T11.bach_fugue(P, b, E2, '②')
    DRONES.append((f, f + n_, 0.16)); CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    P.set_harms(b, [['A7']]); P.hold.add(b); DRONES.append((b, b + 1, 0.2)); CT.LAYOUT.append((b, b + 1, -4, VOICE_SRC, {})); b += 1
    # ---------------- Lacrimosa — Fuga II, III (変ロ短調)
    f = b
    P.section(b, 'Lacrimosa — Fuga II 〈%s · %s〉 (変ロ短調)' % (hm(E1), hm(B2)), '11:23 と 11:18 の主題の二重フーガ — 悲しみの調')
    labmap = double_fugue(P, f, E1, B2, '①', '⑤')
    DRONES.append((f, f + 10, 0.16)); CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    f = b
    P.section(b, 'Lacrimosa — Fuga III 〈%s · %s〉 (変ロ短調)' % (hm(B1), hm(E3)), '9/23 の 2 本、08:06 と 08:09 の主題の二重フーガ')
    labmap = double_fugue(P, f, B1, E3, '④', '③', ans=0)
    DRONES.append((f, f + 10, 0.16)); CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    P.set_harms(b, [['A7']]); P.hold.add(b); DRONES.append((b, b + 1, 0.2)); CT.LAYOUT.append((b, b + 1, 3, VOICE_SRC, {})); b += 1
    # ---------------- Finale (ヘ短調): 7 つの主題 → 嘆きの低音
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ヘ短調)', '7 本の録音の主題が次々と入り、最後の 3 つはストレッタで重なる')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    DRONES.append((f, f + 14, 0.16)); CT.LAYOUT.append((f, f + 14, 3, VOICE_SRC, labmap)); b = f + 14
    P.section(b, 'Lamento — 嘆きの低音', '低音が半音ずつ下がる嘆き (D → C♯ → C → B → B♭ → A) の上で上声が長く嘆き、短調のまま消えていく')
    P.set_harms(b, [['Dm', 'Dm', 'A', 'A'], ['F', 'F', 'Gm', 'Gm'], ['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'Dm', 'Dm']])
    P.place('B', b, mat(('D3', 2), ('C#3', 2)), 0, '嘆きの低音'); P.place('B', b + 1, mat(('C3', 2), ('B2', 2)), 0, None)
    P.place('B', b + 2, mat(('Bb2', 2), ('A2', 2)), 0, None); P.place('B', b + 3, mat(('D2', 4)), 0, None)
    P.hold.update(range(b, b + 4))
    for k in range(4): P.dyn[b + k] = 0.8 - 0.1 * k
    DRONES.append((b, b + 4, 0.14)); CT.LAYOUT.append((b, b + 4, 3, VOICE_SRC, {})); b += 4
    P.set_harms(b, [['Dm']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, (m, g) in enumerate(((38, 0.22), (45, 0.14), (53, 0.12), (57, 0.1))): add('SP', b * BPB + 0.3 * k, 10.0, m, g, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15)[k])
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [SYN], 'src_name': {SYN: '11:21 のシンセ (実音)'},
    'title': 'Requiem BADA — Tablet Sessions XVIII · Lacrimosa',
    'subtitle': 'ピアノを消し、11:21 のシンセサイザーの実音だけで歌う、悲しみのフーガのレクイエム (Adagio ♩=52)',
    'legend': ['SP'], 'vname': {'SP': '11:21 のシンセ (持続音)'},
    'footer': ['Introitus (持続音) → Kyrie: Fuga I (08:53, ホ短調) → Lacrimosa: Fuga II (11:23 · 11:18) · Fuga III (9/23 08:06 · 08:09) (変ロ短調) → Finale (7 つの主題, ヘ短調) → 嘆きの低音',
               '音はすべて 11:21 の録音から切り出したシンセの持続音 (C♯2〜G♯3 の 8 音) を移調したもの。ピアノ・鼓動・オルガンはなし。短調のまま終わる。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet18.json'
    compose.main(out, seed=101, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    import json
    d = json.load(open(out))
    for nt in d['notes']: nt['src'] = SYN                              # 4 声はすべて 11:21 のシンセの実音で
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
