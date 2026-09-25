#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XVII · Organo (4 声をパイプオルガンのシンセに、11:21 のシンセの実音はそのまま、9/23 の録音もミックス)
  XVI から、合成していた側の楽器 = フーガの 4 声 (録音のピアノの 1 音のサンプラー) を、パイプオルガンのシンセ (synth.organ_tone:
  8' プリンシパル + 4' + 2⅔' + 2' / 低音は 16' のストップを重ね、減衰せず鳴り続ける、入りにチフ) に置き換えた。
  11:21 の録音のシンセサイザーの実音 (build_synthbank.py) は、これまでどおり主題の入りに同じ音で重なる。
  2026-09-23 の録音 2 本 (08:06 / 08:09) を実音のミックスと主題に加え、9/24 の 5 本と合わせて 7 本。
    Introitus — 11:23 → 08:53 → 9/23 08:09 (ホ短調) の実音をクロスフェードで / Fuga I — 08:53 のバッハ風フーガ (オルガン)
    Lacrimosa — 9/23 08:06 → 11:18 (変ロ短調) / Fuga II — 11:23 と 11:18 の二重フーガ
    Sanctus — 08:49 → 11:21 (ヘ短調) / Finale — 7 つの主題のストレッタ (ヘ短調) → 保続低音 / In paradisum — 11:21 の本当の終わり → ヘ長調
  使い方: python compose_tablet17.py <bank.json (9/23・9/24 のピアノ + 11:21 のシンセ)> [score_tablet17.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11       # バッハ風フーガ (bach_fugue)

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 60; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}
LEADS = []                           # (開始小節, 終了小節, 大きさ) — 主題の入りに重なる 11:21 のシンセの実音

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:                                 # 鼓動 (pp)
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.13 if k == 0 else 0.07, None, rid=rid)
    for b0, b1, g in LEADS:
        for v in ('S', 'A', 'T'):
            for s, d, m, lab in events[v]:
                if lab and b0 * BPB <= s < b1 * BPB: add('SP', s, d * 0.95, m, g, None, rid='VOXSY', pan=(-0.2 if v == 'S' else 0.2))

def chain(P, b, rids, semis, bars=10):
    """実音を順にクロスフェードでつなぐ (4 声は休む)。占める小節数を返す"""
    st = b
    for i, r in enumerate(rids):
        T5.passage(P, r, st, bars, semis, bars, fin=(1.5 if i == 0 else XF * BAR_S), fout=(XF * BAR_S if i < len(rids) - 1 else 3.0), bpm=BPM, gmul=0.65)
        CT.LAYOUT.append((st + (XF if i else 0), st + bars, semis, {v: r for v in VOICES}, {}))
        st += bars - XF
    end = st + XF
    for v in VOICES: P.rest_bars(v, b, end)
    return end - b

def pivot(P, b, rid, semis_next):
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55)): add('PF', b * BPB + k * 0.5, 2.5, m, 0.16, None, rid=rid, rel=1.5)
    T2.MANTRA.append((b, b + 1, rid, ('PK',))); CT.LAYOUT.append((b, b + 1, semis_next, VOICE_SRC, {}))

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_sy = REC[SY]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(SY, []).append((end_sy, REC[SY]['dur']))
    total = 26 + 16 + 1 + 18 + 10 + 1 + 18 + 14 + 3 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.0
    b = 0
    P.section(b, 'Introitus — 〈%s → %s → %s〉' % (hm(E1), hm(E2), hm(E3)), 'ホ短調 ／ 9/24 の 2 本から 9/23 08:09 へ、実音のピアノを 8 秒のクロスフェードでつなぐ')
    b += chain(P, b, [E1, E2, E3], 2)
    T2.MANTRA.append((0, b, E1, ('PK',)))
    # ---------------- Fuga I (ホ短調): バッハ風、パイプオルガン
    f = b
    P.section(b, 'Fuga I — %s のバッハ風フーガ (ホ短調, オルガン)' % hm(E2), '提示 → エピソード → 下属調の入り → ストレッタ → 保続低音 — 4 声はパイプオルガン、主題の入りに 11:21 のシンセの実音が重なる')
    n_ = T11.bach_fugue(P, b, E2, '②')
    T2.MANTRA.append((f, f + n_, E2, ('PK',))); LEADS.append((f, f + n_, 0.38))
    CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    pivot(P, b, E2, -4); b += 1
    # ---------------- Lacrimosa (変ロ短調): 9/23 08:06 → 11:18
    s0 = b
    P.section(b, 'Lacrimosa — 〈%s → %s〉 (変ロ短調)' % (hm(B1), hm(B2)), '9/23 08:06 から 9/24 11:18 へ、実音のまま')
    b += chain(P, b, [B1, B2], -4)
    T2.MANTRA.append((s0, b, B1, ('PK',)))
    # ---------------- Fuga II (変ロ短調): 二重フーガ
    f = b; entries, labmap = [], {}
    P.section(b, 'Fuga II — 主題 ①⑤ 〈%s · %s〉 (変ロ短調, オルガン)' % (hm(E1), hm(B2)), '11:23 と 11:18 の主題の二重フーガ — パイプオルガンの 4 声、11:21 のシンセの実音が主題をなぞる')
    for bar, v, r, tr0 in ((0, 'A', E1, 0), (2, 'S', B2, 0), (4, 'T', E1, 7), (6, 'B', B2, 0), (8, 'S', E1, 0), (8, 'T', B2, 0)):
        T7.entry(P, f + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); LEADS.append((f, f + 10, 0.38))
    CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    pivot(P, b, RF, 3); b += 1
    # ---------------- Sanctus (ヘ短調): 08:49 → 11:21
    s0 = b
    P.section(b, 'Sanctus — 〈%s → %s (ピアノとシンセ)〉 (ヘ短調)' % (hm(RF), hm(SY)), '08:49 から、ピアノとシンセサイザーの録音 11:21 へ実音のまま')
    b += chain(P, b, [RF, SY], 3)
    T2.MANTRA.append((s0, b, RF, ('PK',)))
    # ---------------- Finale (ヘ短調): 7 つの主題
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ヘ短調, オルガン)', '9/23・9/24 の 7 本の主題が次々と入り、最後の 3 つはストレッタで重なる → 保続低音 — 11:21 のシンセの実音が全部の主題をなぞる')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    for k in range(14): P.dyn[f + k] = 1.1
    T2.MANTRA.append((f, f + 14, RF, ('PK',))); LEADS.append((f, f + 14, 0.4))
    CT.LAYOUT.append((f, f + 14, 3, VOICE_SRC, labmap)); b = f + 14
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, T11.PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    T2.MANTRA.append((b, b + 3, RF, ('PK',))); CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    # ---------------- In paradisum
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(SY), 'ピアノとシンセサイザーの録音 11:21 の最後の 20 秒を実音のまま → ヘ長調の和音を、オルガンと 11:21 のシンセの実音が静かに鳴らして閉じる')
    T5.passage(P, SY, b, 5, 3, 5, fin=1.0, fout=2.5, t0=end_sy, bpm=BPM, gmul=0.7)
    for v in VOICES: P.rest_bars(v, b, b + 5)
    T2.MANTRA.append((b, b + 5, SY, ('PK',))); CT.LAYOUT.append((b, b + 5, 3, {v: SY for v in VOICES}, {})); b += 5
    P.set_harms(b, [['D']] * 3); P.hold.update({b, b + 1})
    P.place('S', b, mat(('F#5', 8)), 0, None); P.place('A', b, mat(('A4', 8)), 0, None); P.place('T', b, mat(('D4', 8)), 0, None); P.place('B', b, mat(('D2', 8)), 0, None)
    for v in VOICES: P.rest_bars(v, b + 2, b + 3)
    for k in range(3): P.dyn[b + k] = 0.7 - 0.15 * k
    for k, (m, pan) in enumerate(((57, -0.2), (66, 0.2))): add('SP', b * BPB + 0.5, 9.0, m, 0.11, None, rid='VOXSY', pan=pan)
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5, 'choir': 'organ',
    'title': 'Requiem BADA — Tablet Sessions XVII · Organo',
    'subtitle': '4 声をパイプオルガンのシンセに、11:21 のシンセの実音は主題に重ねたまま — 9/23 の 2 本もミックス (♩=60)',
    'legend': ['TB', 'SP', 'PK'], 'vname': {'SP': '11:21 のシンセ (実音)'},
    'footer': ['Introitus: 11:23 → 08:53 → 9/23 08:09 (ホ短調) → Fuga I (オルガン) → Lacrimosa: 9/23 08:06 → 11:18 (変ロ短調) → Fuga II → Sanctus: 08:49 → 11:21 → Finale (7 つの主題) → ヘ長調',
               'パイプオルガン (合成): 8 フィートのプリンシパルに 4・2⅔・2 フィート、低音は 16 フィート。減衰せず鳴り続け、入りにチフ。4 声の色は主題の録音を示す。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet17.json'
    compose.main(out, seed=97, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
