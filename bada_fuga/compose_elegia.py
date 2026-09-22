#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA VI — Elegia (B♭ minor, ♩=36, piano solo)
  シンセサイザーを使わないピアノ独奏。高音の B-A-D-A は 1 オクターヴ下げて長く保ち (木琴に聞こえないように)、
  音符の間はペダルの共鳴・声部ごとの打鍵の時間差・拍節に沿った強弱の起伏 (ルバート) でつなぐ。
  全体を B♭ 短調 (ニ短調 −4 半音)。
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
TRANSPOSE = -4          # D minor -> Bb minor
extras = []

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def low_octaves(P, bar0, bar1, every=1, vel=0.5):
    for bar in range(bar0, bar1, every):
        c = chord(P.harm[bar * BPB])
        root = 24 + c['bass'] + (12 if c['bass'] < 2 else 0)
        add('L', bar, 0, 4, root, vel); add('L', bar, 0, 4, root + 12, vel * 0.8)

def clusters(P, bar0, bar1, vel=0.2, dense=False):
    """電子シンセの不協和音: 各小節の和音の根音に 短 2 度・三全音・長 7 度 を重ねたクラスターを持続。"""
    for bar in range(bar0, bar1):
        c = chord(P.harm[bar * BPB])
        root = 60 + c['root']
        pcs = [root, root + 1, root + 6, root + 11] + ([root + 13, root - 5] if dense else [])
        for i, m in enumerate(pcs):
            add('C', bar, 0, 4.6, m, vel * (1.0 if i == 0 else 0.75), None)

def lament(P, bar0, ncycles, mantra_voices=('A', 'T'), label=None, dyn=0.7):
    for cyc in range(ncycles):
        b = bar0 + 3 * cyc
        P.set_harms(b, LAMENT_H)
        for i, m in enumerate(LAMENT_B):
            P.place('B', b + i // 2, [(2, m)], 0, 'Lamento (嘆きのバス)' if (i == 0 and cyc == 0 and label) else None, beat=(i % 2) * 2)
            add('L', b + i // 2, (i % 2) * 2, 2, m - 12, 0.5)
        v = mantra_voices[cyc % len(mantra_voices)] if mantra_voices else None
        if v:
            P.place(v, b, BADA, {'S': 12, 'A': 0, 'T': -12}[v], 'B-A-D-A' if cyc <= 1 else None)
        for k in range(3): P.dyn[b + k] = dyn(cyc) if callable(dyn) else dyn
    P.hold.update(range(bar0, bar0 + 3 * ncycles))

def high_bada(P, bar0, nreps, label='B-A-D-A (ピアノ高音)'):
    mat_ = [n('Bb5'), n('A5'), n('D6'), n('A5')]
    for r in range(nreps):
        for i, m in enumerate(mat_):
            add('H', bar0 + r * 4 + i, 0, 4, m, 0.42, label if (i == 0 and r == 0) else None)
            add('H', bar0 + r * 4 + i + 2, 0, 4, m - 5, 0.28)

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    P.section(0, 'I. Introitus — Elegia', '嘆きのバスのパッサカリア。ペダルの共鳴とルバートが音符の間をつなぐ')
    lament(P, 0, 2, mantra_voices=(None, 'A'), label=True, dyn=lambda c: 0.55 + 0.15 * c)
    P.rest_bars('S', 0, 3); P.rest_bars('T', 0, 3); P.rest_bars('A', 0, 3)
    high_bada(P, 2, 1)
    d1 = INTRO
    copy_bars(T, P, SEG1[0], SEG1[1], d1)
    P.sections = [(b, t.replace('I. Soggetto I', 'II. Fuga — Soggetto I'), s) for b, t, s in P.sections]
    for bar in range(d1, d1 + 32): P.dyn[bar] = 0.8
    low_octaves(P, d1, d1 + 32, every=2, vel=0.4)
    for k in range(0, 32, 4): add('H', d1 + k, 0, 4, n('D6'), 0.28)
    r0 = d1 + 32
    P.section(r0, 'Ritornello — Elegia', '嘆きのバスの回帰。B-A-D-A をテノール → アルト')
    lament(P, r0, 2, mantra_voices=('T', 'A'), dyn=lambda c: 0.7)
    high_bada(P, r0, 1, label=None)
    d2 = r0 + RIT
    copy_bars(T, P, SEG2[0], SEG2[1], d2)
    P.sections = [(b, t, s) for b, t, s in P.sections if not (b == d2 and 'Soggetto III' in t)]
    P.section(d2, 'III. Fuga a tre soggetti — Elegia', '三主題の三重結合 ×3。最後の休止で途切れる')
    for bar in range(d2, d2 + 26): P.dyn[bar] = 0.85
    low_octaves(P, d2, d2 + 24, every=2, vel=0.45)
    for k in range(0, 24, 4): add('H', d2 + k, 0, 4, n('D6'), 0.28)
    c0 = d2 + 26
    P.section(c0, 'IV. Lacrimosa — Passacaglia', '嘆きのバス ×4。B-A-D-A が声部を渡り、ペダルの残響だけが残って消える')
    lament(P, c0, 4, mantra_voices=('A', 'S', 'T', 'A'), dyn=lambda c: max(0.2, 0.75 - 0.15 * c))
    high_bada(P, c0, 2, label=None)
    P.set_harms(TOTAL - 2, [['Dm'], ['Dm']])
    P.hold.update({TOTAL - 2, TOTAL - 1})
    for v in VOICES: P.rest_bars(v, TOTAL - 2, TOTAL)
    add('L', TOTAL - 2, 0, 8, n('D1'), 0.5); add('L', TOTAL - 2, 0, 8, n('A2'), 0.35)
    add('H', TOTAL - 2, 0, 8, n('D6'), 0.38); add('H', TOTAL - 1, 0, 4, n('A5'), 0.22)
    P.dyn[TOTAL - 2] = P.dyn[TOTAL - 1] = 0.25
    return P

META = {
    'style': 'elegia', 'detach': 0.92, 'humanize': True,
    'title': 'Requiem BADA VI — Elegia',
    'subtitle': 'B♭ minor · ♩=36 ／ ピアノ独奏 — 嘆きのバスのパッサカリアに包まれたフーガ=レクイエム、ペダルの共鳴とルバートで間をつなぐ',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA, B♭短調では G♭-F-B♭-F) ／ 嘆きのバス ← 半音下行',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 のため息 ／ 録音 090146    ｜  合成: グランドピアノのみ (シンセ不使用) · ペダル共鳴 · 声部ごとの打鍵の時間差',
               '高音の B-A-D-A は B♭5–D6 に下げて長く保ち、打鍵雑音を抑えて減衰を長くした (木琴に聞こえないように)。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_elegia.json'
    compose.main(out, seed=3, bpm=36, builder=build, meta=META, extras=extras, transpose_semis=TRANSPOSE)
