#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA IV — Lamento (♩=36)
  高音を木琴系シンセ (H: 鐘のカノン, W: 分散和音の刻み) にし、テンポを極端に落とした悲しみのレクイエム・フーガ。
  前奏・回帰句・終結は「嘆きのバス」(D C# C B B♭ A の半音下行) によるパッサカリア。
  ピカルディ終止を捨て、短調のまま空虚 5 度 (D–A) で消える。
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars

BADA = mat(('Bb4',2),('A4',2),('D5',2),('A4',2))
# 嘆きのバス: 半小節ごとに半音ずつ下る 3 小節周期
LAMENT_H = [['Dm', 'Dm', 'A/C#', 'A/C#'], ['F/C', 'F/C', 'G/B', 'G/B'], ['Gm/Bb', 'Gm/Bb', 'A7', 'A7']]
LAMENT_B = [n('D2'), n('C#2'), n('C2'), n('B1'), n('Bb1'), n('A1')]
INTRO, RIT, CODA = 6, 6, 12
SEG1 = (0, 32)
SEG2 = (101, 127)
NF = (SEG1[1] - SEG1[0]) + (SEG2[1] - SEG2[0])
TOTAL = INTRO + NF + RIT + CODA + 2
extras = []

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def wash(P, bar0, bar1, lo=60, hi=88, vel=0.30):
    """木琴シンセの刻み: 各半小節の和音を 8 分音符で上行→下行 (高音域)。"""
    for bar in range(bar0, bar1):
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half])
            tones = [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
            seq = tones[:3] + list(reversed(tones[1:4]))[:1]
            for i, m in enumerate((seq + seq)[:4]):
                add('W', bar, half + i * 0.5, 0.5, m, vel * (1.0 if i == 0 else 0.75))

def low_octaves(P, bar0, bar1, every=1, vel=0.55):
    for bar in range(bar0, bar1, every):
        c = chord(P.harm[bar * BPB])
        root = 24 + c['bass'] + (12 if c['bass'] < 2 else 0)
        add('L', bar, 0, 4, root, vel); add('L', bar, 0, 4, root + 12, vel * 0.8)

def lament(P, bar0, ncycles, mantra_voices=('A', 'T'), label=None, dyn=0.7, wash_vel=0.3):
    """嘆きのバスのパッサカリア: 3 小節周期。バスは固定、和声は LAMENT_H、マントラを各周期の前 2 小節に。"""
    for cyc in range(ncycles):
        b = bar0 + 3 * cyc
        P.set_harms(b, LAMENT_H)
        for i, m in enumerate(LAMENT_B):
            P.place('B', b + i // 2, [(2, m)], 0, 'Lamento (嘆きのバス)' if (i == 0 and cyc == 0 and label) else None, beat=(i % 2) * 2)
            add('L', b + i // 2, (i % 2) * 2, 2, m - 12, 0.5)
        v = mantra_voices[cyc % len(mantra_voices)] if mantra_voices else None
        if v:
            P.place(v, b, BADA, {'S': 12, 'A': 0, 'T': -12}[v], 'B-A-D-A' if cyc <= 1 else None)
        for k in range(3): P.dyn[b + k] = dyn if callable(dyn) is False else dyn(cyc)
    P.hold.update(range(bar0, bar0 + 3 * ncycles))
    wash(P, bar0, bar0 + 3 * ncycles, vel=wash_vel)

def bell_canon(P, bar0, nreps, follow=True, label='B-A-D-A (木琴シンセ)'):
    mat_ = [n('Bb6'), n('A6'), n('D7'), n('A6')]
    for r in range(nreps):
        for i, m in enumerate(mat_):
            add('H', bar0 + r * 4 + i, 0, 4, m, 0.5, label if (i == 0 and r == 0) else None)
            add('H', bar0 + r * 4 + i, 2, 2, m, 0.25)                       # 余韻の打ち直し (木琴は減衰が速い)
            if follow: add('H', bar0 + r * 4 + i + 2, 0, 4, m - 5, 0.32)

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------------- I. Introitus — Lamento
    P.section(0, 'I. Introitus — Lamento', '嘆きのバス (D C# C B B♭ A) のパッサカリア。木琴シンセの刻みと B-A-D-A の唱え')
    lament(P, 0, 2, mantra_voices=(None, 'A'), label=True, dyn=lambda c: 0.55 + 0.15 * c, wash_vel=0.26)
    P.rest_bars('S', 0, 3); P.rest_bars('T', 0, 3); P.rest_bars('A', 0, 3)
    bell_canon(P, 2, 1)
    # ---------------- II. Fuga (第 I 部の前半)
    d1 = INTRO
    copy_bars(T, P, SEG1[0], SEG1[1], d1)
    P.sections = [(b, t.replace('I. Soggetto I', 'II. Fuga — Soggetto I'), s) for b, t, s in P.sections]
    for bar in range(d1, d1 + 32): P.dyn[bar] = 0.8
    wash(P, d1 + 10, d1 + 32, vel=0.2)
    low_octaves(P, d1, d1 + 32, every=2, vel=0.4)
    for k in range(0, 32, 4): add('H', d1 + k, 0, 4, n('D7'), 0.3); add('H', d1 + k, 2, 2, n('A6'), 0.18)
    # ---------------- Ritornello — Lamento
    r0 = d1 + 32
    P.section(r0, 'Ritornello — Lamento', '嘆きのバスの回帰。B-A-D-A をテノールとアルトが唱え、木琴シンセのカノンが重なる')
    lament(P, r0, 2, mantra_voices=('T', 'A'), dyn=lambda c: 0.7)
    bell_canon(P, r0, 1, label=None)
    # ---------------- III. Fuga a tre soggetti
    d2 = r0 + RIT
    copy_bars(T, P, SEG2[0], SEG2[1], d2)
    P.sections = [(b, t, s) for b, t, s in P.sections if not (b == d2 and 'Soggetto III' in t)]
    P.section(d2, 'III. Fuga a tre soggetti — Lamento', '三主題の三重結合 ×3 を極端に遅く。最後の休止で途切れる')
    for bar in range(d2, d2 + 26): P.dyn[bar] = 0.85
    wash(P, d2, d2 + 24, vel=0.18)
    low_octaves(P, d2, d2 + 24, every=2, vel=0.45)
    for k in range(0, 24, 4): add('H', d2 + k, 0, 4, n('D7'), 0.3); add('H', d2 + k, 2, 2, n('A6'), 0.18)
    # ---------------- IV. Lacrimosa — 嘆きのパッサカリア (終結)
    c0 = d2 + 26
    P.section(c0, 'IV. Lacrimosa — Passacaglia', '嘆きのバスを 4 回。B-A-D-A が声部を渡り、木琴シンセの残響だけが残る')
    lament(P, c0, 4, mantra_voices=('A', 'S', 'T', 'A'), dyn=lambda c: max(0.2, 0.75 - 0.15 * c), wash_vel=0.28)
    bell_canon(P, c0, 2, label=None)
    # 最後: 空虚 5 度 D–A (短調のまま)
    P.set_harms(TOTAL - 2, [['Dm'], ['Dm']])
    P.hold.update({TOTAL - 2, TOTAL - 1})
    for v in VOICES: P.rest_bars(v, TOTAL - 2, TOTAL)
    add('L', TOTAL - 2, 0, 8, n('D1'), 0.5); add('L', TOTAL - 2, 0, 8, n('A2'), 0.35)
    add('H', TOTAL - 2, 0, 8, n('D7'), 0.4); add('H', TOTAL - 2, 2, 6, n('A6'), 0.25); add('H', TOTAL - 1, 0, 4, n('D6'), 0.2)
    P.dyn[TOTAL - 2] = P.dyn[TOTAL - 1] = 0.25
    return P

META = {
    'style': 'mallet',
    'title': 'Requiem BADA IV — Lamento',
    'subtitle': '♩=36 ／ 木琴シンセ (高音) + グランドピアノ ／ 嘆きのバスのパッサカリアに包まれた三重フーガ — 短調のまま消える',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA) + 録音 090933 ／ 嘆きのバス ← 半音下行 D C# C B B♭ A',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 のため息 (B♭–A) ／ 録音 090146    ｜  合成: 木琴シンセ (H/W) · グランドピアノ (S/A/T/B/L)',
               '前奏・回帰句・終結はパッサカリア。ピカルディ終止を捨て、空虚 5 度 D–A と木琴の残響で終わる。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_lamento.json'
    compose.main(out, seed=3, bpm=36, builder=build, meta=META, extras=extras)
