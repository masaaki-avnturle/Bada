#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA II — 荘厳な洗脳のレクイエム
  全曲を通して心拍のような低い脈拍と弔鐘が続き、B-A-D-A のマントラがフーガの各部の間に
  回帰句 (リトルネッロ) として何度も戻ってくる。合唱は暗い母音「オ」。
    I.   Introitus     : ドローン・脈拍・弔鐘 — 「Requiem aeternam」風の聖歌 と ディエス・イレ、B-A-D-A の唱え
    II.  Kyrie (Fuga)  : 三重フーガ 第 I 部 → マントラ回帰句 → 第 II 部 → マントラ回帰句 → 第 III 部
    III. Lux aeterna   : マントラを声部交替で 12 回反復、うねるように強弱を繰り返して消える
"""
import sys
from compose import *
import compose

DIES_IRAE = mat(('F4',2),('E4',1),('F4',1),('D4',2),('E4',1),('C4',1),('D4',2),('D4',2),
                ('F4',2),('F4',1),('E4',1),('F4',2),('D4',2),('E4',1),('C4',1),('D4',4))
# 「Requiem aeternam dona eis Domine」の抑揚を模した聖歌風の旋律 (D ドリア)
REQUIEM_CHANT = mat(('F4',2),('F4',1),('G4',1),('F4',2),('E4',1),('D4',1),('F4',2),('G4',2),
                    ('A4',3),('G4',1),('F4',2),('E4',2),('D4',4))
BADA = mat(('Bb4',2),('A4',2),('D5',2),('A4',2))
DRONE_BAR = [(4, n('D2'))]

INTRO, RIT, CODA = 12, 8, 24
FUGA = 130
TOTAL = INTRO + FUGA + 2 * RIT + CODA
extras = []

def bell(bar, beat, midi=n('D3'), gain=1.0, dbeats=8):
    extras.append({'v': 'X', 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': gain})
def drone(bar0, bar1, midi=n('D1'), gain=1.0):
    extras.append({'v': 'D', 'beat': bar0 * BPB, 'dbeats': (bar1 - bar0) * BPB, 'm': midi, 'gain': gain})
def pulse(bar, beat, gain=1.0):
    extras.append({'v': 'P', 'beat': bar * BPB + beat, 'dbeats': 1, 'm': n('D2'), 'gain': gain})

MANTRA_PROG = [['Gm/D', 'Gm/D', 'Dm', 'Dm'], ['Bb/D', 'Bb/D', 'Dm', 'Dm']]

def mantra(P, bar, nbars, voices=('A',), label_every=4, dyn=None, octave=0):
    """B-A-D-A を nbars 小節にわたり反復 (2 小節で 1 回)。voices を順に交替。"""
    for k in range(nbars // 2):
        b = bar + 2 * k
        P.set_harms(b, MANTRA_PROG)
        v = voices[k % len(voices)]
        oct_ = {'S': 12, 'A': 0, 'T': -12, 'B': -24}[v] + octave
        P.place(v, b, BADA, oct_, 'B-A-D-A' if k % label_every == 0 else None)
        for j in range(2):
            P.place('B', b + j, DRONE_BAR, 0, None) if v != 'B' else None
            pulse(b + j, 0, 1.0); pulse(b + j, 2, 0.6)
            if dyn is not None: P.dyn[b + j] = dyn(k)
        bell(b, 0, gain=0.8); bell(b + 1, 2, midi=n('A2'), gain=0.45)
    P.hold.update(range(bar, bar + nbars))
    drone(bar, bar + nbars, gain=1.0)

def build():
    P = Piece(TOTAL)
    # ---------------- I. Introitus
    P.section(0, 'I. Introitus', 'ドローン・心拍・弔鐘の上に — Requiem aeternam の聖歌、ディエス・イレ、B-A-D-A の唱え')
    P.set_harms(0, [['Dm']] * 6 + [['Gm'], ['Dm'], ['Bb'], ['Gm'], ['A'], ['A']])
    for v in VOICES: P.rest_bars(v, 0, 2)
    P.place('S', 2, REQUIEM_CHANT, 0, 'Requiem aeternam')
    P.place('T', 6, DIES_IRAE, -12, 'Dies irae')
    P.place('A', 8, BADA, 0, 'B-A-D-A')
    P.rest_bars('A', 2, 8); P.rest_bars('T', 2, 6)
    for bar in range(INTRO):
        P.place('B', bar, DRONE_BAR, 0, None)
        P.dyn[bar] = 0.5 + 0.035 * bar
        bell(bar, 0, gain=0.9 if bar % 2 == 0 else 0.55)
        pulse(bar, 0, 0.9); pulse(bar, 2, 0.5)
    P.hold.update(range(INTRO)); drone(0, INTRO)
    # ---------------- II. Kyrie: フーガ (第 I 部 / 回帰句 / 第 II 部 / 回帰句 / 第 III 部)
    compose.build_fugue(P, INTRO, gaps=(RIT, RIT))
    f1 = INTRO + 44; f2 = INTRO + 44 + RIT + 41
    P.section(f1, 'Ritornello — Mantra I', 'B-A-D-A の回帰句 (アルト → ソプラノ) — 心拍と鐘')
    mantra(P, f1, RIT, voices=('A', 'S'), dyn=lambda k: 0.8)
    for v in 'ST': P.rest_bars(v, f1, f1 + 2)
    P.section(f2, 'Ritornello — Mantra II', 'B-A-D-A の回帰句 (テノール → アルト) — 心拍と鐘')
    mantra(P, f2, RIT, voices=('T', 'A'), dyn=lambda k: 0.8)
    for v in 'SA': P.rest_bars(v, f2, f2 + 2)
    P.sections = [(b, ('II. Kyrie · ' + t) if (INTRO <= b < INTRO + FUGA + 2 * RIT and not t.startswith('Ritornello')) else t, s)
                  for b, t, s in P.sections]
    # フーガ内の催眠的パルス: 2 小節ごとの遠い鐘 + 各小節 1 拍目の弱い心拍
    for bar in range(INTRO, INTRO + FUGA + 2 * RIT):
        if bar in P.dyn: continue
        P.dyn[bar] = 0.9
        pulse(bar, 0, 0.35)
        if (bar - INTRO) % 2 == 0: bell(bar, 0, gain=0.3, dbeats=6)
    for b0 in (101, 121):
        s = INTRO + b0 + 2 * RIT
        drone(s, s + 5, gain=0.7)
        for k in range(5): bell(s + k, 0, gain=0.6)
    # ---------------- III. Lux aeterna — Mantra (12 回, うねる強弱)
    c0 = INTRO + FUGA + 2 * RIT
    P.section(c0, 'III. Lux aeterna — Mantra ×12', 'B-A-D-A を声部交替で 12 回反復 — うねりながら鐘の残響へ消えていく')
    import math
    mantra(P, c0, CODA, voices=('A', 'S', 'T', 'A', 'S', 'A'), label_every=3,
           dyn=lambda k: max(0.18, (0.95 - 0.055 * k) * (0.8 + 0.2 * math.cos(k * 1.3))))
    P.rest_bars('T', c0, c0 + 2)
    P.set_harms(TOTAL - 2, [['D'], ['D']])
    P.place('A', TOTAL - 2, mat(('A4', 8)), 0, None)
    bell(TOTAL - 2, 0, gain=1.0, dbeats=16)
    return P

META = {
    'style': 'requiem', 'vowel': 'o',
    'title': 'Requiem BADA II',
    'subtitle': '荘厳な洗脳のレクイエム — ニ短調 ／ 心拍・弔鐘・ドローンの上で B-A-D-A のマントラが回帰し続ける三重フーガ',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA) + 録音 090933 ／ 聖歌 ← Dies irae・Requiem aeternam',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 ／ 録音 090146    ｜  合成: 合唱 (母音オ)+オルガン 4 声 · 弔鐘 · 心拍 · ドローン · 大聖堂リバーブ',
               'マントラ回帰句 ×2 (フーガ各部の間) と Lux aeterna のマントラ ×12 が、聴き手を同じ 4 音へ引き込み続ける。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_requiem2.json'
    compose.main(out, seed=11, bpm=66, builder=build, meta=META, extras=extras)
