#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — 荘厳で催眠的な (洗脳的に反復する) レクイエム版
  I.   Introitus   : D のドローンと弔鐘の上に「ディエス・イレ」聖歌と B-A-D-A の唱え
  II.  Kyrie (Fuga): 三重フーガ本体を ♩=66 の荘厳なテンポで (鐘は 4 小節ごと)
  III. Lux aeterna : D ペダル上で B-A-D-A のマントラを 8 回反復し、鐘とともに消えていく
"""
import sys
from compose import *
import compose

# ディエス・イレ (グレゴリオ聖歌, D ドリア) の冒頭句
DIES_IRAE = mat(('F4',2),('E4',1),('F4',1),('D4',2),('E4',1),('C4',1),('D4',2),('D4',2),
                ('F4',2),('F4',1),('E4',1),('F4',2),('D4',2),('E4',1),('C4',1),('D4',4))
BADA_CHANT = mat(('Bb4',2),('A4',2),('D5',2),('A4',2))
DRONE_BAR = [(4, n('D2'))]

INTRO = 12
FUGA = 130
CODA = 18
TOTAL = INTRO + FUGA + CODA

extras = []  # 鐘・ドローン (voice 'X' = 鐘, 'D' = ドローン)

def bell(bar, beat, midi=n('D3'), gain=1.0, dbeats=8):
    extras.append({'v': 'X', 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': gain})

def drone(bar0, bar1, midi=n('D1'), gain=1.0):
    extras.append({'v': 'D', 'beat': bar0 * BPB, 'dbeats': (bar1 - bar0) * BPB, 'm': midi, 'gain': gain})

def build_requiem():
    P = Piece(TOTAL)
    # ---------------- I. Introitus
    P.section(0, 'I. Introitus', 'D のドローンと弔鐘 — ディエス・イレの聖歌 と B-A-D-A の唱え')
    P.set_harms(0, [['Dm'], ['Dm'], ['Dm'], ['Dm'], ['Dm'], ['Dm'], ['Gm'], ['Dm'], ['Bb'], ['Gm'], ['A'], ['A']])
    for v in VOICES: P.rest_bars(v, 0, 2)
    P.place('T', 2, DIES_IRAE, 0, 'Dies irae')
    P.place('A', 8, BADA_CHANT, 0, 'B-A-D-A')
    P.rest_bars('A', 2, 8); P.rest_bars('S', 2, 6)
    for bar in range(0, INTRO): P.place('B', bar, DRONE_BAR, 0, None)
    P.hold.update(range(0, INTRO))
    for bar in range(0, INTRO): P.dyn[bar] = 0.55 + 0.03 * bar
    for bar in range(0, INTRO): bell(bar, 0, gain=0.9 if bar % 2 == 0 else 0.6)
    drone(0, INTRO, gain=1.0)
    # ---------------- II. Fuga (Kyrie)
    compose.build_fugue(P, INTRO)
    P.sections = [(b, ('II. Kyrie · ' + t) if INTRO <= b < INTRO + FUGA else t, s) for b, t, s in P.sections]
    # フーガ内: 4 小節ごとに遠くの鐘 (催眠的なパルス), 三重結合ではドローン
    for bar in range(INTRO, INTRO + FUGA, 4): bell(bar, 0, gain=0.35, dbeats=6)
    for b0 in (101, 121):  # 三重結合 (ニ短調) の 5 小節
        drone(INTRO + b0, INTRO + b0 + 5, gain=0.7)
        for k in range(5): bell(INTRO + b0 + k, 0, gain=0.6)
    for bar in range(INTRO, INTRO + FUGA): P.dyn[bar] = 0.9
    # ---------------- III. Lux aeterna — マントラ
    c0 = INTRO + FUGA
    P.section(c0, 'III. Lux aeterna — Mantra', 'D ペダルの上で B-A-D-A を 8 回反復 — 鐘とともに消えていく')
    prog = [['Gm/D', 'Gm/D', 'Dm', 'Dm'], ['Bb/D', 'Bb/D', 'Dm', 'Dm']]
    for k in range(8):
        bar = c0 + 2 * k
        P.set_harms(bar, prog)
        P.place('A', bar, BADA_CHANT, 0, 'B-A-D-A' if k in (0, 4) else None)
        for j in range(2): P.place('B', bar + j, DRONE_BAR, 0, None)
        bell(bar, 0, gain=0.8); bell(bar + 1, 2, midi=n('A2'), gain=0.5)
        P.dyn[bar] = P.dyn[bar + 1] = max(0.25, 0.95 - 0.1 * k)
    # 最後の 2 小節: D 長三和音 (ピカルディ) で静止
    P.set_harms(c0 + 16, [['D'], ['D']])
    P.place('A', c0 + 16, mat(('A4', 8)), 0, None)
    for j in range(2): P.place('B', c0 + 16 + j, DRONE_BAR, 0, None)
    P.dyn[c0 + 16] = P.dyn[c0 + 17] = 0.3
    P.hold.update(range(c0, TOTAL))
    P.rest_bars('T', c0, c0 + 4)
    bell(c0 + 16, 0, gain=0.9, dbeats=16)
    drone(c0, TOTAL, gain=1.0)
    return P

META = {
    'style': 'requiem',
    'title': 'Requiem BADA',
    'subtitle': 'Contrapunctus in memoriam — ニ短調 ／ 三重フーガを荘厳で催眠的なレクイエムに',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA) + 録音 090933 ／ 聖歌 ← Dies irae (グレゴリオ聖歌)',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 ／ 録音 090146    ｜  合成: 合唱+オルガン 4 声 · 弔鐘 · ドローン · 大聖堂リバーブ',
               'III. Lux aeterna では B-A-D-A のマントラを 8 回反復し、鐘の残響とともに消えていく。'],
    'legend': {'X': '弔鐘', 'D': 'ドローン'},
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_requiem.json'
    compose.main(out, seed=7, bpm=66, builder=build_requiem, meta=META, extras=extras)
