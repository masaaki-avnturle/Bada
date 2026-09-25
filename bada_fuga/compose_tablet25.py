#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXV · A quattro mani impossibili (4 手の指がなければ不可能な不協和音と分散和音)
  2026-09-23 / 09-24 の 7 本の録音 (主題と和声) をもとに、2 本の手では物理的に弾けない書法でレクイエムとフーガを作り換えた。
  音はすべて録音から切り出したピアノの 1 音 (実音、自然に減衰)。
    - 不協和音の塊 (cluster): 根音の上に短 2 度・増 4 度・短 9 度・長 7 度を積んだ 10〜12 音を 4〜5 オクターヴにわたって同時に打つ
      (両手を広げても届かない)。フーガの入りと Dies irae の各小節の頭で。
    - 分散和音の波 (wave): 6 分割 (1 拍 6 音) の分散和音が A0 付近から C8 付近までの 6 オクターヴを休みなく往復する。
      和音の構成音に ♭9・長 7・♭13 を足した不協和な分散和音。2 本の波が反行 (片方が上り、片方が下り) で同時に走り、
      その上に 4 声のフーガ (＋鼓動、保続低音) — 手が 4 本 (40 本の指) あってはじめて可能。
    - 録音の和声: 抜粋の区間では、録音の採譜の和音進行 (11:23、08:06、08:49) をそのまま使い、分散和音の波と塊で鳴らす。
  形式 (XXII〜XXIV と同じレクイエム、主題はフーガ): Introitus → Kyrie: Fuga I → Graduale → Dies irae: Fuga II → Offertorium
    → Sanctus: Fuga III → Agnus Dei (B-A-D-A のカノン) → Finale: 7 主題のストレッタ → In paradisum。
  使い方: python compose_tablet25.py <bank.json (9/23・9/24 の採譜と 1 音)> [score_tablet25.json]
"""
import sys, json, random
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11
import compose_tablet24 as T24

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 56; BAR_S = 240.0 / BPM
KEYS = T24.KEYS
E1, E2, E3, B1, B2, RF, SY = T24.E1, T24.E2, T24.E3, T24.B1, T24.B2, T24.RF, T24.SY
ORDER = T24.ORDER
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}
RNG = random.Random(25)
GW = 3.2            # 波と塊の音量 (ステムを測って: 抜粋の区間で波 ≈ 0.06、フーガの下で ≈ −6 dB、鼓動は −12 dB)
WAVES = []          # (b0, b1, direction, gain)  — post で和声を見て置く
CLUSTERS = []       # (beat, gain, rid)

def cluster(beat, gain=0.05, rid=None, wide=True):
    CLUSTERS.append((beat, gain, rid, wide))

def wave(b0, b1, direction=1, gain=0.075, lo=24, hi=104):
    WAVES.append((b0, b1, direction, gain, lo, hi))

def render_waves(P, events):
    for b0, b1, direction, gain, lo, hi in WAVES:
        cur = lo - 1 if direction > 0 else hi + 1; beat = b0 * BPB; step = 1.0 / 6
        while beat < b1 * BPB - 1e-6:
            ch = chord(P.harm[int(beat)]); root = ch['root']
            pcs = set(ch['pcs']) | {(root + 1) % 12, (root + 11) % 12, (root + 8) % 12}      # ♭9, 長 7, ♭13 の不協和
            m = cur + direction
            while m % 12 not in pcs: m += direction
            if m > hi or m < lo:
                cur = lo - 1 if direction > 0 else hi + 1; continue
            dyn = P.dyn_at(beat)
            add('PF', beat, step * 1.8, m, GW * gain * dyn * (0.85 + 0.3 * RNG.random()) * (1.15 if int(beat * 6) % 6 == 0 else 1.0), None, rid=VOICE_SRC['T' if direction > 0 else 'S'], rel=0.6)
            cur = m; beat += step

def render_clusters(P):
    for beat, gain, rid, wide in CLUSTERS:
        ch = chord(P.harm[int(beat)]); root = ch['root']
        iv = (0, 1, 6, 7, 11, 13, 16, 18, 22, 25, 30, 31) if wide else (0, 1, 6, 7, 11, 13, 16, 18)
        base = 26 + (root - 2) % 12
        for j, x in enumerate(iv):
            add('PF', beat + 0.006 * j, 3.0, base + x + (12 if j >= 8 else 0), GW * gain * P.dyn_at(beat) * (1.0 if j < 3 else 0.8), None, rid=rid or VOICE_SRC['B'], rel=2.5)

def post(P, events, extras):
    render_waves(P, events); render_clusters(P)
    for b0, b1, rid, kinds in T2.MANTRA:
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=rid)

def rec_harmony(P, rid, bar, bars, semis, t0=None):
    """録音の採譜から和音進行だけを取り出して P.harm に置く (音は鳴らさない)"""
    if t0 is None: t0, inside = T5.best_window(rid, semis, bars * BAR_S)
    else: inside = [x for x in REC[rid]['segs'] if t0 <= x['t'] < t0 + bars * BAR_S]
    T5.USED.setdefault(rid, []).append((t0, t0 + bars * BAR_S))
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
    total = 10 + 16 + 8 + 10 + 8 + 10 + 4 + 14 + 3 + 6
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.15
    b = 0
    # Introitus: 11:23 の和声を、反行する 2 本の分散和音の波と塊で
    P.section(b, 'Introitus — %s の和声 (ホ短調)' % hm(E1), '録音の和音進行を、6 オクターヴを往復する 2 本の反行する分散和音の波 (♭9・長 7・♭13 入り) で — 2 小節ごとに 12 音の塊')
    rec_harmony(P, E1, b, 10, 2)
    wave(b, b + 10, +1, 0.095); wave(b + 2, b + 10, -1, 0.08)
    for k in range(0, 10, 2): cluster((b + k) * BPB, 0.06, E1)
    for k in range(10): P.dyn[b + k] = 0.9
    T2.MANTRA.append((b, b + 10, E1, ('PK',))); CT.LAYOUT.append((b, b + 10, 2, VOICE_SRC, {})); b += 10
    # Kyrie — Fuga I
    f = b
    P.section(b, 'Kyrie — Fuga I 〈%s〉 (ホ短調)' % hm(E2), '08:53 の主題のバッハ風フーガ (提示 → エピソード → 下属調 → ストレッタ → 保続低音) — ストレッタから 6 オクターヴの波が下から加わり、入りごとに塊')
    n_ = T11.bach_fugue(P, b, E2, '②')
    for k in range(n_): P.dyn[f + k] = 1.3
    for k in (0, 2, 4, 6): cluster((f + k) * BPB, 0.035, E2, wide=False)
    wave(f + 10, f + n_, +1, 0.06)
    T2.MANTRA.append((f, f + n_, E2, ('PK',))); CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    # Graduale: 08:06 の和声 (変ロ短調)
    P.section(b, 'Graduale — %s の和声 (変ロ短調)' % hm(B1), '9/23 の録音の和音進行を、2 本の反行する波と塊で')
    rec_harmony(P, B1, b, 8, -4)
    wave(b, b + 8, -1, 0.095); wave(b + 1, b + 8, +1, 0.08)
    for k in range(0, 8, 2): cluster((b + k) * BPB, 0.06, B1)
    for k in range(8): P.dyn[b + k] = 0.9
    T2.MANTRA.append((b, b + 8, B1, ('PK',))); CT.LAYOUT.append((b, b + 8, -4, VOICE_SRC, {})); b += 8
    # Dies irae — Fuga II
    f = b
    P.section(b, 'Dies irae — Fuga II 〈%s · %s〉 (変ロ短調)' % (hm(E1), hm(B2)), '11:23 と 11:18 の二重フーガ — 各小節の頭に 12 音の塊が落ち、後半は 2 本の波が反行して走る')
    labmap = double_fugue(P, f, E1, B2)
    for k in range(10): P.dyn[f + k] = 1.25
    for k in range(10): cluster((f + k) * BPB, 0.05 if k % 2 == 0 else 0.035, B2)
    wave(f + 5, f + 10, +1, 0.06); wave(f + 6, f + 10, -1, 0.05)
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    # Offertorium: 08:49 の和声 (ヘ短調)
    P.section(b, 'Offertorium — %s の和声 (ヘ短調)' % hm(RF), '08:49 の和音進行を、上りの波 1 本と 4 小節ごとの塊で — 息をつく')
    rec_harmony(P, RF, b, 8, 3)
    wave(b, b + 8, +1, 0.1, lo=28, hi=100)
    for k in (0, 4): cluster((b + k) * BPB, 0.055, RF)
    for k in range(8): P.dyn[b + k] = 0.85
    T2.MANTRA.append((b, b + 8, RF, ('PK',))); CT.LAYOUT.append((b, b + 8, 3, VOICE_SRC, {})); b += 8
    # Sanctus — Fuga III
    f = b
    P.section(b, 'Sanctus — Fuga III 〈%s · %s〉 (ヘ短調)' % (hm(B1), hm(E3)), '9/23 の 2 本、08:06 と 08:09 の主題の二重フーガ — 下りの波の上で')
    labmap = double_fugue(P, f, B1, E3, ans=0)
    for k in range(10): P.dyn[f + k] = 1.3
    wave(f, f + 10, -1, 0.055)
    for k in (0, 4, 8): cluster((f + k) * BPB, 0.035, B1, wide=False)
    T2.MANTRA.append((f, f + 10, B1, ('PK',))); CT.LAYOUT.append((f, f + 10, 3, VOICE_SRC, labmap)); b = f + 10
    # Agnus Dei
    a0 = b
    P.section(b, 'Agnus Dei — B-A-D-A のカノン', 'B-A-D-A を 2 回、テノールが 1 拍遅れて追う — 保続低音の上に、2 本の波が反行')
    for k in range(2):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        P.place('T', bb, H.BADA, -12, 'B-A-D-A (1 拍遅れ)' if k == 0 else None, beat=1)
        for j in range(2): P.place('B', bb + j, T11.PED, 0, None)
    P.rest_bars('S', b, b + 4); P.hold.update(range(b, b + 4))
    for k in range(4): P.dyn[b + k] = 1.0
    wave(b, b + 4, +1, 0.055); wave(b, b + 4, -1, 0.05)
    T2.MANTRA.append((a0, a0 + 4, RF, ('PK',))); CT.LAYOUT.append((a0, a0 + 4, 3, VOICE_SRC, {})); b = a0 + 4
    # Finale
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ヘ短調)', '7 本の録音の主題が次々と入り、最後の 3 つはストレッタで重なる — 入りごとに塊、2 本の波が反行 → 保続低音')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
        cluster((f + bar) * BPB, 0.045, ORDER[k])
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    for k in range(14): P.dyn[f + k] = 1.3
    wave(f + 4, f + 14, +1, 0.06); wave(f + 8, f + 14, -1, 0.055)
    T2.MANTRA.append((f, f + 14, RF, ('PK',))); CT.LAYOUT.append((f, f + 14, 3, VOICE_SRC, labmap)); b = f + 14
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, T11.PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    for k in range(3): P.dyn[b + k] = 1.1
    for k in range(3): cluster((b + k) * BPB, 0.05, RF)
    T2.MANTRA.append((b, b + 3, RF, ('PK',))); CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    # In paradisum: ヘ長調、上りの波が遅くなって消える
    P.section(b, 'In paradisum (ヘ長調)', '長調の分散和音の波が 6 オクターヴを上り、遅くなり、最後の塊はやわらかい長和音にほどける')
    P.set_harms(b, [['D']] * 6)
    for v in VOICES: P.rest_bars(v, b, b + 6)
    for k in range(6): P.dyn[b + k] = 0.8 - 0.08 * k; P.tempo[b + k] = BPM - 5 * k
    wave(b, b + 4, +1, 0.1, lo=21, hi=105)
    for k, m in enumerate((26, 38, 45, 50, 54, 57, 62, 66, 69, 74, 78, 81)): add('PF', (b + 4) * BPB + k * 0.3, 6.0, m, 0.3, None, rid=RF, rel=3.0)
    T2.MANTRA.append((b, b + 6, RF, ('PK',))); CT.LAYOUT.append((b, b + 6, 3, VOICE_SRC, {})); b += 6
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XXV · A quattro mani impossibili',
    'subtitle': '4 手の指がなければ不可能な不協和音の塊と 6 オクターヴの分散和音の波 — 9/23・9/24 の実録音のピアノ一色 (♩=56)',
    'legend': ['TB', 'PK'], 'vname': {'PK': '鼓動 (ピアノの低い打鍵)'},
    'footer': ['Introitus 11:23 の和声 → Kyrie: Fuga I → Graduale 08:06 の和声 → Dies irae: Fuga II → Offertorium 08:49 の和声 → Sanctus: Fuga III → Agnus Dei → Finale → In paradisum',
               '12 音の塊 (短 2 度・増 4 度・短 9 度・長 7 度) と、♭9・長 7・♭13 入りの分散和音が反行して 6 オクターヴを往復。その上に 4 声のフーガ、鼓動。音はすべて録音から切り出したピアノ。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet25.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']))
