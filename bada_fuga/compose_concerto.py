#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA VIII — Concerto (B♭ minor, ♩=30) — 独奏ピアノと管弦楽のための
  Dialogo 版をピアノ協奏曲に。バロック協奏曲のリトルネッロ形式と重ねる:
    トゥッティ (前奏・回帰句・終結 = 嘆きのバスのパッサカリア): 弦 5 部 + オーボエ + フルート + ホルン + ティンパニ が
      ピアノの全声部を重ね、ホルンが和音を支える
    ソロ (フーガ部): ピアノ独奏が主体。弦は主題の入りだけをそっと重ね、第 2 ヴァイオリンが和音を薄く保つ
  層: V1 第1Vn / V2 第2Vn / VA Va / VC Vc / CB Cb / WW オーボエ / FL フルート / HN ホルン / TP ティンパニ
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D

INTRO, RIT, CODA = 6, 6, 12
SEG1 = (0, 22)
SEG2 = (101, 127)
NF = (SEG1[1] - SEG1[0]) + (SEG2[1] - SEG2[0])
TOTAL = INTRO + NF + RIT + CODA + 2
TRANSPOSE = -4
extras = D.extras          # H (ピアノ高音) は D.add で入る
TUTTI = set()

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    P.section(0, 'I. Introitus — Tutti', '管弦楽のトゥッティ: 歌う嘆きのバスの上で左手が B-A-D-A を唱え、弦と木管が重なる')
    D.lament(P, 0, 2, label=True, dyn=lambda c: 0.65 + 0.12 * c, first_cycle_solo=True)
    P.rest_bars('S', 0, 3); P.rest_bars('A', 0, 3)
    D.high_bada(P, 3, 1)
    TUTTI.update(range(0, INTRO))
    d1 = INTRO
    copy_bars(T, P, SEG1[0], SEG1[1], d1)
    P.sections = [(b, t.replace('I. Soggetto I', 'II. Solo — Fuga, Soggetto I'), s) for b, t, s in P.sections]
    for bar in range(d1, d1 + 22): P.dyn[bar] = 0.82
    r0 = d1 + 22
    P.section(r0, 'Ritornello — Tutti', '管弦楽の回帰。嘆きのバスと B-A-D-A のカノン (ピアノ → 弦・オーボエ)')
    D.lament(P, r0, 2, dyn=lambda c: 0.78)
    D.high_bada(P, r0 + 2, 1, label=None)
    TUTTI.update(range(r0, r0 + RIT))
    d2 = r0 + RIT
    copy_bars(T, P, SEG2[0], SEG2[1], d2)
    P.sections = [(b, t, s) for b, t, s in P.sections if not (b == d2 and 'Soggetto III' in t)]
    P.section(d2, 'III. Solo — Fuga a tre soggetti', '独奏ピアノの三重結合 ×3。弦は主題の入りだけを重ねる。最後の休止で途切れる')
    for bar in range(d2, d2 + 26): P.dyn[bar] = 0.86
    c0 = d2 + 26
    P.section(c0, 'IV. Lacrimosa — Tutti', '全管弦楽の嘆きのパッサカリア ×4。ティンパニと低弦の上で消えていく')
    D.lament(P, c0, 4, dyn=lambda c: max(0.25, 0.85 - 0.16 * c))
    D.high_bada(P, c0 + 1, 2, label=None)
    P.rest_bars('S', c0 + 9, c0 + 12); P.rest_bars('A', c0 + 11, c0 + 12)
    TUTTI.update(range(c0, TOTAL))
    P.set_harms(TOTAL - 2, [['Dm'], ['Dm']])
    P.hold.update({TOTAL - 2, TOTAL - 1})
    for v in 'SA': P.rest_bars(v, TOTAL - 2, TOTAL)
    P.place('B', TOTAL - 2, mat(('D2', 8)), 0, None); P.place('T', TOTAL - 2, mat(('A3', 8)), 0, None)
    add('H', TOTAL - 2, 0, 8, n('D6'), 0.3)
    P.dyn[TOTAL - 2] = P.dyn[TOTAL - 1] = 0.3
    return P

def post(P, events, ex):
    """生成後: トゥッティでは弦がピアノの全声部を重ね、ソロではラベル付きの主題だけを薄く重ねる。"""
    STR = {'S': ('V1', 0), 'A': ('VA', 0), 'T': ('VC', 0), 'B': ('CB', -12)}
    for v in VOICES:
        lay, oct_ = STR[v]
        for s, d, m, lab in events[v]:
            bar = int(s // BPB)
            dyn = P.dyn.get(bar, 1.0)
            if bar in TUTTI:
                add(lay, 0, s, d, m + oct_, 0.55 * dyn, None)
                if v == 'B': add('VC', 0, s, d, m, 0.4 * dyn, None)          # チェロは実音、コントラバスは 1 オクターヴ下
                if v == 'A' and lab: add('WW', 0, s, d, m, 0.5 * dyn, None)  # オーボエが B-A-D-A を歌う
                if v == 'T' and lab: add('WW', 0, s, d, m + 12, 0.35 * dyn, None)
            elif lab:
                add(lay, 0, s, d, m + oct_, 0.28 * dyn, None)
    # H (ピアノ高音) をトゥッティではフルートが重ねる
    for e in list(ex):
        if e['v'] == 'H' and int(e['beat'] // BPB) in TUTTI:
            add('FL', 0, e['beat'], e['dbeats'], e['m'], 0.35, None)
    # ホルンの和音 / 第 2 ヴァイオリンの薄い和音 / ティンパニ
    for bar in range(P.nbars):
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half])
            root = 48 + c['root']
            dyn = P.dyn.get(bar, 1.0)
            if bar in TUTTI:
                add('HN', bar, half, 2.3, root, 0.32 * dyn); add('HN', bar, half, 2.3, root + 7, 0.26 * dyn)
                third = [m for m in range(60, 72) if m % 12 == c['third']][0]
                add('V2', bar, half, 2.2, third, 0.3 * dyn)
            else:
                fifth = [m for m in range(55, 67) if m % 12 == c['fifth']][0]
                add('V2', bar, half, 2.2, fifth, 0.12 * dyn)
    lam_starts = [0, 3, INTRO + 22, INTRO + 22 + 3] + [INTRO + 22 + RIT + 26 + 3 * k for k in range(4)]
    for b in lam_starts:
        add('TP', b, 0, 2, n('D2'), 0.55 * P.dyn.get(b, 1.0), None)              # ロール
        add('TP', b + 2, 2, 1, n('A1'), 0.4 * P.dyn.get(b, 1.0), None)
    add('TP', TOTAL - 2, 0, 6, n('D2'), 0.5, None)

META = {
    'style': 'concerto', 'detach': 0.92, 'humanize': True,
    'title': 'Requiem BADA VIII — Concerto',
    'subtitle': 'for Piano and Orchestra · B♭ minor · ♩=30 ／ トゥッティ (嘆きのパッサカリア) と ソロ (三重フーガ) が交替するリトルネッロ形式',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA, B♭短調では G♭-F-B♭-F) ／ 嘆きのバス ← 半音下行',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 のため息 ／ 録音 090146    ｜  合成: ピアノ · 弦 5 部 · オーボエ · フルート · ホルン · ティンパニ',
               'トゥッティでは弦がピアノの全声部を重ね、ホルンが和音を支える。ソロでは弦が主題の入りだけをそっと重ね、第 2 Vn が和音を薄く保つ。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_concerto.json'
    compose.main(out, seed=8, bpm=30, builder=build, meta=META, extras=extras, transpose_semis=TRANSPOSE, post=post)
