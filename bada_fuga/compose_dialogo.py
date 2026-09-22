#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA VII — Dialogo (B♭ minor, ♩=36, piano solo)
  左手を伴奏から解放する版。
    - 低音オクターヴの打音層 (L) を廃止
    - 嘆きのバス (D C# C B B♭ A) は、各根音から音階を 2 音のぼる歌う音型 (D E F | C# D E | ...) に
    - 左手のテノールは右手のアルトの B-A-D-A と 1 小節遅れのカノンで対話する
    - 持続和音 (全音符の保持) をやめ、自由声部はすべて動く対位法にする
  高音の B-A-D-A (B♭5–D6) はピアノの右手の最上声として残す。
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars

BADA = mat(('Bb4',2),('A4',2),('D5',2),('A4',2))
LAMENT_H = [['Dm', 'Dm', 'A/C#', 'A/C#'], ['F/C', 'F/C', 'G/B', 'G/B'], ['Gm/Bb', 'Gm/Bb', 'A7', 'A7']]
LAMENT_B = [n('D2'), n('C#2'), n('C2'), n('B1'), n('Bb1'), n('A1')]
INTRO, RIT, CODA = 6, 6, 12
SEG1 = (0, 32)
SEG2 = (101, 127)
NF = (SEG1[1] - SEG1[0]) + (SEG2[1] - SEG2[0])
TOTAL = INTRO + NF + RIT + CODA + 2
TRANSPOSE = -4
extras = []

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def singing_bass(root, cs):
    """根音 (1 拍) → 音階を 2 音のぼる (0.5 拍ずつ): 歌う嘆きのバス (2 拍)。"""
    sc = chord(cs)['scale']
    up = []
    m = root
    while len(up) < 2:
        m += 1
        if m % 12 in sc: up.append(m)
    if up[1] - up[0] > 2: up[0] = up[1] - 2          # 増 2 度を避ける (A B C#)
    return [(1, root), (.5, up[0]), (.5, up[1])]

def lament(P, bar0, ncycles, canon=True, label=None, dyn=0.7, first_cycle_solo=False):
    """歌う嘆きのバス + B-A-D-A のカノン (アルト → 1 小節遅れでテノール)。"""
    for cyc in range(ncycles):
        b = bar0 + 3 * cyc
        P.set_harms(b, LAMENT_H)
        for i, m in enumerate(LAMENT_B):
            cs = LAMENT_H[i // 2][(i % 2) * 2]
            P.place('B', b + i // 2, singing_bass(m, cs), 0, 'Lamento (歌う嘆きのバス)' if (i == 0 and cyc == 0 and label) else None, beat=(i % 2) * 2)
        if first_cycle_solo and cyc == 0:
            P.place('T', b, BADA, -12, 'B-A-D-A (左手)')
        else:
            P.place('A', b, BADA, 0, 'B-A-D-A' if cyc == 0 else None)
            if canon: P.place('T', b + 1, BADA, -12, 'B-A-D-A カノン (左手)' if cyc == 0 else None)
        for k in range(3): P.dyn[b + k] = dyn(cyc) if callable(dyn) else dyn

def high_bada(P, bar0, nreps, label='B-A-D-A (最上声)'):
    mat_ = [n('Bb5'), n('A5'), n('D6'), n('A5')]
    for r in range(nreps):
        for i, m in enumerate(mat_):
            add('H', bar0 + r * 4 + i, 0, 4, m, 0.4, label if (i == 0 and r == 0) else None)

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    P.section(0, 'I. Introitus — Dialogo', '歌う嘆きのバスの上で、左手のテノールが B-A-D-A を唱え、右手が 1 小節遅れで応える')
    lament(P, 0, 2, label=True, dyn=lambda c: 0.6 + 0.12 * c, first_cycle_solo=True)
    P.rest_bars('S', 0, 3); P.rest_bars('A', 0, 3)
    high_bada(P, 3, 1)
    d1 = INTRO
    copy_bars(T, P, SEG1[0], SEG1[1], d1)
    P.sections = [(b, t.replace('I. Soggetto I', 'II. Fuga — Soggetto I'), s) for b, t, s in P.sections]
    for bar in range(d1, d1 + 32): P.dyn[bar] = 0.8
    for k in range(4, 32, 8): add('H', d1 + k, 0, 4, n('D6'), 0.26)
    r0 = d1 + 32
    P.section(r0, 'Ritornello — Dialogo', '嘆きのバスの回帰。B-A-D-A のカノン (右手 → 左手)')
    lament(P, r0, 2, dyn=lambda c: 0.72)
    high_bada(P, r0 + 2, 1, label=None)
    d2 = r0 + RIT
    copy_bars(T, P, SEG2[0], SEG2[1], d2)
    P.sections = [(b, t, s) for b, t, s in P.sections if not (b == d2 and 'Soggetto III' in t)]
    P.section(d2, 'III. Fuga a tre soggetti — Dialogo', '三主題の三重結合 ×3。左手にも主題 I・II が渡る。最後の休止で途切れる')
    for bar in range(d2, d2 + 26): P.dyn[bar] = 0.85
    for k in range(4, 24, 8): add('H', d2 + k, 0, 4, n('D6'), 0.26)
    c0 = d2 + 26
    P.section(c0, 'IV. Lacrimosa — Dialogo', '嘆きのバス ×4。B-A-D-A のカノンが両手を渡り、歌う低音だけが残って消える')
    lament(P, c0, 4, dyn=lambda c: max(0.22, 0.75 - 0.14 * c))
    high_bada(P, c0 + 1, 2, label=None)
    P.rest_bars('S', c0 + 9, c0 + 12); P.rest_bars('A', c0 + 11, c0 + 12)
    P.set_harms(TOTAL - 2, [['Dm'], ['Dm']])
    P.hold.update({TOTAL - 2, TOTAL - 1})
    for v in 'SA': P.rest_bars(v, TOTAL - 2, TOTAL)
    P.place('B', TOTAL - 2, mat(('D2', 8)), 0, None); P.place('T', TOTAL - 2, mat(('A3', 8)), 0, None)
    add('H', TOTAL - 2, 0, 8, n('D6'), 0.34)
    P.dyn[TOTAL - 2] = P.dyn[TOTAL - 1] = 0.25
    return P

META = {
    'style': 'elegia', 'detach': 0.92, 'humanize': True,
    'title': 'Requiem BADA VII — Dialogo',
    'subtitle': 'B♭ minor · ♩=36 ／ ピアノ独奏 — 左手も主題を歌う: 歌う嘆きのバス、B-A-D-A の両手カノン、全声部が動く対位法',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA, B♭短調では G♭-F-B♭-F) ／ 嘆きのバス ← 半音下行',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 のため息 ／ 録音 090146    ｜  合成: グランドピアノのみ · ペダル共鳴 · 声部ごとの打鍵の時間差',
               '左手は伴奏ではない: 嘆きのバスは根音から音階をのぼる歌う音型、テノールは右手と 1 小節遅れのカノン、持続和音は廃止。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_dialogo.json'
    compose.main(out, seed=8, bpm=36, builder=build, meta=META, extras=extras, transpose_semis=TRANSPOSE)
