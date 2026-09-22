#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Piano Concerto BADA — ピアノ協奏曲 ニ短調 (3 楽章)
  交響曲版の素材を、独奏ピアノと管弦楽のための協奏曲に。
    I.   Allegro moderato : 管弦楽の序奏 (嘆きのパッサカリア, ♩=40) → 主題 I のフーガ (ピアノ独奏が提示、エピソードは管弦楽, ♩=76)
                            → カデンツァ (ピアノのみ, ♩=52: 左手に主題 I、右手に B-A-D-A、半音階の走句) → 管弦楽の結び
    II.  Adagio — Lamento : 嘆きのバス ×4 を 管弦楽 / ピアノ / 合奏 / ピアノ と交替 (♩=40)
    III. Finale           : B-A-D-A 主題の提示 (ピアノ) → 三重結合 ×3 (ピアノ → ピアノ → 合奏)、エピソードは管弦楽、
                            休止、D 長調のコーダ (全合奏, ♩=84 → 60)
  役割 (小節ごと): solo = ピアノ、tutti = 管弦楽、both = 合奏、cadenza = ピアノのみ (管弦楽なし)
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D

I_INTRO = 6
I_A = 40            # fugue bars 0..40
CAD = 8
I_B = 4             # fugue bars 40..44
M2 = I_INTRO + I_A + CAD + I_B          # 58
II_LEN = 14
M3 = M2 + II_LEN                         # 72
III_FUGA, CODA = 45, 6
TOTAL = M3 + III_FUGA + CODA             # 123
extras = D.extras
MOV = {}

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def set_range(P, b0, b1, mov, tempo, dyn, det, role):
    for b in range(b0, b1):
        MOV[b] = mov; P.tempo[b] = tempo; P.dyn[b] = dyn; P.det[b] = det; P.role[b] = role

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------------- I.
    P.section(0, 'I. 序奏 — Tutti', '管弦楽の嘆きのパッサカリア: 低弦が歌う嘆きのバス、ヴィオラとホルンが B-A-D-A')
    D.lament(P, 0, 2, label=True, dyn=lambda c: 0.7, first_cycle_solo=True)
    P.rest_bars('S', 0, 3); P.rest_bars('A', 0, 3)
    set_range(P, 0, I_INTRO, 1, 40, 0.7, 0.98, 'tutti')
    copy_bars(T, P, 0, I_A, I_INTRO)
    P.sections = [(b, t.replace('I. Soggetto I 〈MOTHER〉', 'I. Allegro moderato — 主題 I 〈MOTHER〉 (ピアノ独奏の提示)'), s) for b, t, s in P.sections]
    set_range(P, I_INTRO, I_INTRO + I_A, 1, 76, 0.85, 0.95, 'solo')
    for b0, b1 in ((22, 26), (31, 35)):               # エピソードは管弦楽
        for b in range(I_INTRO + b0, I_INTRO + b1): P.role[b] = 'tutti'
    # ---------------- Cadenza
    c0 = I_INTRO + I_A
    P.section(c0, 'I. Cadenza — ピアノ独奏', '左手に主題 I、右手に B-A-D-A、半音階の走句からトリルへ (管弦楽は沈黙)')
    P.set_harms(c0, [row[:] for row in compose.H_S1] + [['Gm', 'Gm', 'A7', 'A7'], ['A7'], ['A7']])
    P.place('T', c0, compose.S1, -12, 'S1 (カデンツァ, 左手)')
    P.place('S', c0 + 1, D.BADA, 12, 'B-A-D-A (右手)')
    P.rest_bars('A', c0, c0 + 3)
    run = mat(('A4',.5),('Bb4',.5),('C#5',.5),('D5',.5),('E5',.5),('F5',.5),('G5',.5),('A5',.5),
              ('Bb5',.5),('A5',.5),('G5',.5),('F5',.5),('E5',.5),('D5',.5),('C#5',.5),('E5',.5))
    P.place('S', c0 + 5, run, 0, None)
    P.place('S', c0 + 7, mat(('A5', .5), ('Bb5', .5), ('A5', .5), ('Bb5', .5), ('A5', .5), ('Bb5', .5), ('A5', 1)), 0, None)   # トリル
    P.place('B', c0 + 6, mat(('A2', 4), ('A2', 4)), 0, None)
    for v in 'AT': P.rest_bars(v, c0 + 6, c0 + 8)
    set_range(P, c0, c0 + CAD, 1, 52, 0.8, 0.95, 'cadenza')
    P.tempo[c0 + 7] = 44
    copy_bars(T, P, I_A, 44, c0 + CAD)
    set_range(P, c0 + CAD, M2, 1, 76, 0.9, 0.95, 'tutti')
    # ---------------- II.
    P.section(M2, 'II. Adagio — Lamento', '嘆きのバス ×4: 管弦楽 → ピアノ → 合奏 → ピアノ。B-A-D-A のカノン')
    D.lament(P, M2, 4, dyn=lambda c: [0.6, 0.65, 0.85, 0.55][c])
    P.set_harms(M2 + 12, [['Dm'], ['Dm']]); P.hold.update({M2 + 12, M2 + 13})
    set_range(P, M2, M3, 2, 40, 0.6, 1.0, 'tutti')
    for c, role in enumerate(('tutti', 'solo', 'both', 'solo')):
        for k in range(3): P.role[M2 + 3 * c + k] = role; P.dyn[M2 + 3 * c + k] = [0.6, 0.65, 0.85, 0.55][c]
    P.role[M2 + 12] = P.role[M2 + 13] = 'both'; P.dyn[M2 + 12] = P.dyn[M2 + 13] = 0.4
    D.high_bada(P, M2 + 3, 1); D.high_bada(P, M2 + 9, 1, label=None)
    # ---------------- III.
    copy_bars(T, P, 85, 130, M3)
    P.sections = [(b, t.replace('III. Soggetto III 〈B-A-D-A〉', 'III. Finale — 主題 III 〈B-A-D-A〉 と三重結合').replace('III. Fuga a tre soggetti — 終結', 'III. Finale — 三重結合の終結 (合奏)'), s) for b, t, s in P.sections]
    set_range(P, M3, M3 + III_FUGA, 3, 84, 0.9, 0.95, 'solo')
    for b0, b1 in ((97, 101), (107, 111), (117, 121)):
        for b in range(M3 + b0 - 85, M3 + b1 - 85): P.role[b] = 'tutti'
    for b in range(M3 + 121 - 85, M3 + III_FUGA): P.role[b] = 'both'; P.dyn[b] = 1.0
    k0 = M3 + III_FUGA
    P.section(k0, 'III. Coda — Maestoso', 'D 長調のコーダ: 全合奏の和音とティンパニ、ピアノの B♮-A-D-A')
    P.set_harms(k0, [['D'], ['G/D'], ['D'], ['Bm', 'Bm', 'A7', 'A7'], ['D'], ['D']])
    P.hold.update(range(k0, TOTAL))
    P.place('S', k0, mat(('B5', 2), ('A5', 2), ('D6', 2), ('A5', 2)), 0, 'B♮-A-D-A (長調)')
    set_range(P, k0, TOTAL, 3, 60, 1.0, 1.0, 'both')
    P.dyn[TOTAL - 1] = 0.9
    return P

def post(P, events, ex):
    for v in VOICES:
        for s, d, m, lab in events[v]:
            bar = int(s // BPB); role = P.role.get(bar, ''); dyn = P.dyn.get(bar, 1.0); mov = MOV.get(bar, 1)
            if role == 'cadenza' or not lab: continue
            if role in ('tutti', 'both'):
                if v == 'S': add('FL', 0, s, d, m + 12 if m < 72 else m, 0.4 * dyn)
                if v == 'A': add('WW', 0, s, d, m, 0.45 * dyn)
                if v == 'T': add('CL', 0, s, d, m, 0.4 * dyn)
            if role == 'solo':   # ソロ中は弦が主題だけをそっと重ねる
                lay, oct_ = {'S': ('V1', 0), 'A': ('VA', 0), 'T': ('VC', 0), 'B': ('CB', -12)}[v]
                add(lay, 0, s, d, m + oct_, 0.25 * dyn)
            if mov == 3 and role == 'both' and v in 'SA': add('TR', 0, s, d, m if 58 <= m <= 82 else m + 12, 0.4 * dyn)
            if mov == 3 and role == 'both' and v in 'TB': add('TB', 0, s, d, m, 0.42 * dyn)
    for bar in range(P.nbars):
        role = P.role.get(bar, ''); dyn = P.dyn.get(bar, 1.0); mov = MOV.get(bar, 1)
        if role == 'cadenza': continue
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half]); root = 48 + c['root']
            if role in ('tutti', 'both'):
                add('HN', bar, half, 2.2, root, 0.3 * dyn); add('HN', bar, half, 2.2, root + 7, 0.24 * dyn)
            else:
                fifth = [m for m in range(55, 67) if m % 12 == c['fifth']][0]
                add('V2', bar, half, 2.2, fifth, 0.1 * dyn)
            if bar >= M3 + III_FUGA:
                third = [m for m in range(60, 72) if m % 12 == c['third']][0]
                add('TR', bar, half, 2.0, root + 12, 0.4 * dyn); add('TR', bar, half, 2.0, third, 0.35 * dyn)
                add('TB', bar, half, 2.0, root - 12, 0.45 * dyn); add('TB', bar, half, 2.0, root - 5, 0.35 * dyn)
        if mov == 3 and role == 'both': add('TP', bar, 0, 0.6, n('D2'), 0.45 * dyn)
    for b in (0, 3, M2, M2 + 6):
        add('TP', b, 0, 2, n('D2'), 0.5 * P.dyn.get(b, 1.0))
    k0 = M3 + III_FUGA
    add('TP', k0, 0, 4, n('D2'), 0.7); add('TP', k0 + 2, 0, 4, n('D2'), 0.6); add('TP', TOTAL - 2, 0, 8, n('D2'), 0.8)

META = {
    'style': 'pconcerto', 'detach': 0.92, 'humanize': True,
    'title': 'Piano Concerto BADA — in D minor',
    'subtitle': 'ピアノ協奏曲 ニ短調 (3 楽章) — I. Allegro moderato (カデンツァ付き) ／ II. Adagio Lamento ／ III. Finale Maestoso',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA) ／ 嘆きのバス ← 半音下行 D C# C B B♭ A',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 のため息 ／ 録音 090146    ｜  独奏ピアノ + 弦 5 部 · Fl · Ob · Cl · Hn · Tp · Tb · Timp (すべて合成)',
               'ソロ (ピアノ色) と トゥッティ (弦色) が小節ごとに交替。カデンツァでは管弦楽が沈黙する。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_pconcerto.json'
    compose.main(out, seed=13, bpm=76, builder=build, meta=META, extras=extras, post=post)
