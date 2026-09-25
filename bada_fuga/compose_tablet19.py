#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XIX · Pastorale della Natività (実録音のピアノ一色、キリスト生誕を哀れみで — レクイエムのフーガ)
  XVIII から、シンセサイザーの全音 (4 声・持続音) を実録音のピアノ (9/23・9/24 の録音から切り出した 1 音、自然に減衰) に置き換え、
  「悲しみの正義の味方」のような勇ましい旋律を消して、曲調をキリスト生誕の牧歌 (パストラーレ) に書き換えた。
    - 主題は 7 本の録音から作るが、5 半音より大きな跳躍はオクターヴに畳んでなだらかにし、シチリアーナの長短 (♩. ♪) の揺れをつける
    - 低音で開いた 5 度 (羊飼いの笛のドローン) が長短のリズムで静かに繰り返す
    - ト短調 (哀れみ) とト長調 (生誕の光) を行き来し、最後は子守歌のようにト長調で pp に消える
  Pastorale — Fuga I (08:53, ト短調, バッハ風) / Kyrie — Fuga II (11:23 · 11:18) / Gloria — ト長調の牧歌 (08:09 の主題を上声に)
  Misericordia — Fuga III (9/23 08:06 · 08:49) / Finale — 7 つの主題のストレッタ → Wiegenlied (子守歌, ト長調)
  使い方: python compose_tablet19.py <bank.json (9/23・9/24 の採譜と 1 音)> [score_tablet19.json]
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
BPM = 66
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
GMIN = 5                             # ト短調 / ト長調 (ニ短調から +5)
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}
DRONE = []                           # (開始小節, 終了小節, 大きさ, 録音 id) — 開いた 5 度のドローン (ピアノ、長短のリズム)

def gentle(subj):
    """勇ましい跳躍をなだらかに: 5 半音より大きな跳びはオクターヴに畳む。同じ長さの 2 音はシチリアーナの長短 (1.5 + 0.5) に"""
    out, prev = [], None
    for d, m in subj:
        if prev is not None:
            while m - prev > 5: m -= 12
            while prev - m > 5: m += 12
        out.append([d, m]); prev = m
    lo, hi = min(m for _, m in out), max(m for _, m in out)
    if lo < 57: out = [[d, m + 12] for d, m in out]
    elif hi > 81: out = [[d, m - 12] for d, m in out]
    i = 0
    while i < len(out) - 1:
        if out[i][0] == 1 and out[i + 1][0] == 1: out[i][0], out[i + 1][0] = 1.5, 0.5; i += 2
        else: i += 1
    return [(d, m) for d, m in out]

def post(P, events, extras):
    for b0, b1, g, rid in DRONE:
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB] or 'Dm'); root = min((x for x in range(36, 48) if x % 12 == c['root']), key=lambda x: abs(x - 38))
            fifth = root + 7
            for q, m, dd, gg in ((0, root, 1.5, 1.0), (1.5, fifth, 0.5, 0.6), (2, root, 1.5, 0.8), (3.5, fifth, 0.5, 0.5)):
                add('PF', bar * BPB + q, dd, m, g * gg, None, rid=rid, rel=0.6, pan=-0.1)

MAJ = ['D', 'G', 'A7', 'Bm', 'Em', 'F#m', 'A']

def harm_major(P, b0, b1, entries):
    """長調の区間: 主題の音に合う長調の和音を半小節ごとに (主題のない所は D)"""
    old = CT.CANDS; CT.CANDS = MAJ
    T5.harm_from_entries(P, b0, b1, entries); CT.CANDS = old
    for q in range(b0 * BPB, b1 * BPB):
        if P.harm[q] in (None, 'Dm', 'Gm'): P.harm[q] = 'D'

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
        subj = gentle(CT.make_subject(inside, KEYS[r], 66)); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    total = 4 + 16 + 1 + 10 + 8 + 1 + 10 + 1 + 14 + 8 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.85
    b = 0
    P.section(b, 'Pastorale — 羊飼いの笛のドローン', 'ト短調 ／ 実録音のピアノの低音が、開いた 5 度を長短のリズムで静かに繰り返す (♩=66)')
    for v in VOICES: P.rest_bars(v, b, b + 4)
    P.set_harms(b, [['Dm']] * 4); DRONE.append((b, b + 4, 0.2, E2)); CT.LAYOUT.append((b, b + 4, GMIN, VOICE_SRC, {})); b += 4
    # ---------------- Fuga I (ト短調)
    f = b
    P.section(b, 'Pastorale — Fuga I 〈%s〉 (ト短調)' % hm(E2), '08:53 の主題 (跳躍を畳み、長短の揺れをつけた) のバッハ風フーガ — 4 声とも実録音のピアノ、下でドローン')
    n_ = T11.bach_fugue(P, b, E2, '②')
    DRONE.append((f, f + n_, 0.13, E2)); CT.LAYOUT.append((f, f + n_, GMIN, VOICE_SRC, {})); b = f + n_
    P.set_harms(b, [['A7']]); P.hold.add(b); DRONE.append((b, b + 1, 0.13, E2)); CT.LAYOUT.append((b, b + 1, GMIN, VOICE_SRC, {})); b += 1
    # ---------------- Kyrie — Fuga II (ト短調)
    f = b
    P.section(b, 'Kyrie — Fuga II 〈%s · %s〉 (ト短調)' % (hm(E1), hm(B2)), '11:23 と 11:18 の主題 (なだらかに) の二重フーガ — 哀れみ')
    labmap = double_fugue(P, f, E1, B2)
    DRONE.append((f, f + 10, 0.13, E1)); CT.LAYOUT.append((f, f + 10, GMIN, VOICE_SRC, labmap)); b = f + 10
    # ---------------- Gloria — ト長調の牧歌
    g0 = b
    P.section(b, 'Gloria — ト長調の牧歌 〈%s〉' % hm(E3), '生誕の光: ト長調のドローンの上で、9/23 08:09 の主題を長調にして上声が歌い、下の 3 声がやさしく支える')
    subj = [(d, m + (1 if m % 12 in (5, 10) else 0)) for d, m in T5.SUBJ[E3][0]]      # ニ長調へ (F → F#, B♭ → B)
    P.place('S', b, subj, 12, '主題 ③ (%s) 長調' % hm(E3)); P.place('S', b + 4, subj, 12, None)
    harm_major(P, b, b + 8, [(b * BPB, [(d, m + 12) for d, m in subj]), ((b + 4) * BPB, [(d, m + 12) for d, m in subj])])
    for q in range((b + 7) * BPB, (b + 8) * BPB): P.harm[q] = 'D'
    P.hold.update({b + 2, b + 3, b + 6, b + 7})
    for k in range(8): P.dyn[b + k] = 0.75
    DRONE.append((g0, g0 + 8, 0.15, E3)); CT.LAYOUT.append((g0, g0 + 8, GMIN, VOICE_SRC, {'主題 ③ (%s) 長調' % hm(E3): E3})); b = g0 + 8
    P.set_harms(b, [['A7']]); P.hold.add(b); DRONE.append((b, b + 1, 0.13, E3)); CT.LAYOUT.append((b, b + 1, GMIN, VOICE_SRC, {})); b += 1
    # ---------------- Misericordia — Fuga III (ト短調)
    f = b
    P.section(b, 'Misericordia — Fuga III 〈%s · %s〉 (ト短調)' % (hm(B1), hm(RF)), '9/23 08:06 と 08:49 の主題 (なだらかに) の二重フーガ — 哀れみの調')
    labmap = double_fugue(P, f, B1, RF, ans=0)
    DRONE.append((f, f + 10, 0.13, B1)); CT.LAYOUT.append((f, f + 10, GMIN, VOICE_SRC, labmap)); b = f + 10
    P.set_harms(b, [['A7']]); P.hold.add(b); DRONE.append((b, b + 1, 0.13, B1)); CT.LAYOUT.append((b, b + 1, GMIN, VOICE_SRC, {})); b += 1
    # ---------------- Finale (ト短調): 7 つの主題
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ト短調)', '7 本の録音の主題 (なだらかに) が次々と入り、最後の 3 つはストレッタで重なる')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    DRONE.append((f, f + 14, 0.13, RF)); CT.LAYOUT.append((f, f + 14, GMIN, VOICE_SRC, labmap)); b = f + 14
    # ---------------- Wiegenlied (ト長調): 子守歌
    w0 = b
    P.section(b, 'Wiegenlied — 子守歌 (ト長調)', '飼い葉桶の子守歌: ト長調のドローンの上で 11:23 の主題を長調にして pp で歌い、静かに消えていく')
    subj = [(d, m + (1 if m % 12 in (5, 10) else 0)) for d, m in T5.SUBJ[E1][0]]
    P.place('S', b, subj, 12, '主題 ① (%s) 長調' % hm(E1)); P.place('A', b + 4, subj, 0, None)
    harm_major(P, b, b + 8, [(b * BPB, [(d, m + 12) for d, m in subj]), ((b + 4) * BPB, [(d, m) for d, m in subj])])
    for q in range((b + 6) * BPB, (b + 8) * BPB): P.harm[q] = 'D'
    P.hold.update({b + 2, b + 3, b + 6, b + 7})
    for v in VOICES: P.rest_bars(v, b + 7, b + 8)
    for k in range(8): P.dyn[b + k] = max(0.3, 0.7 - 0.06 * k)
    DRONE.append((w0, w0 + 8, 0.12, E1)); CT.LAYOUT.append((w0, w0 + 8, GMIN, VOICE_SRC, {'主題 ① (%s) 長調' % hm(E1): E1})); b = w0 + 8
    P.set_harms(b, [['D']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    for k, (m, g) in enumerate(((38, 0.16), (45, 0.11), (54, 0.09), (57, 0.08), (62, 0.07))): add('PF', b * BPB + 0.35 * k, 6.0, m, g, None, rid=E1, rel=3.0)
    CT.LAYOUT.append((b, b + 2, GMIN, VOICE_SRC, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XIX · Pastorale',
    'subtitle': '実録音のピアノ一色 — キリスト生誕を哀れみで、レクイエムのフーガを牧歌に書き換えて (ト短調 / ト長調, ♩=66)',
    'legend': ['PF'], 'vname': {'PF': 'ドローン (ピアノの開いた 5 度)'},
    'footer': ['Pastorale: ドローン → Fuga I (08:53) → Kyrie: Fuga II (11:23 · 11:18) → Gloria (ト長調, 08:09) → Misericordia: Fuga III (9/23 08:06 · 08:49) → Finale (7 つの主題) → Wiegenlied (ト長調)',
               '音はすべて 9/23・9/24 の録音から切り出したピアノの 1 音。主題は跳躍を 5 半音以内に畳み、シチリアーナの長短の揺れ。シンセはなし。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet19.json'
    compose.main(out, seed=103, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
