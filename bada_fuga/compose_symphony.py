#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symphony BADA — 交響曲 ニ短調 (Sinfonia in D minor, 4 楽章)
  I.   Grave — Allegro moderato : 嘆きのパッサカリア (序奏, ♩=40) → 主題 I の 4 声フーガ (♩=76)
  II.  Adagio — Lamento         : 嘆きのバスのパッサカリア ×4 と B-A-D-A のカノン (♩=40)
  III. Scherzo                  : 主題 II の提示と主題 I との二重結合 (♩=126, スタッカート気味)
  IV.  Finale — Maestoso        : B-A-D-A 主題と三重結合 ×3 (♩=84)、休止、D 長調のコーダ (♩=60)
  管弦楽: 弦 5 部 (S/A/T/B → Vn I / Vn II / Va / Vc+Cb) + フルート・オーボエ・クラリネット + ホルン・トランペット・トロンボーン + ティンパニ
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D

I_INTRO, I_FUGA = 6, 44           # bars 0-5, 6-49
II_LEN = 14                       # bars 50-63 (12 + 2)
III_LEN = 41                      # bars 64-104  (fugue 44..85)
IV_FUGA, IV_CODA = 45, 6          # bars 105-149 (fugue 85..130), 150-155
M1, M2, M3, M4 = 0, I_INTRO + I_FUGA, I_INTRO + I_FUGA + II_LEN, I_INTRO + I_FUGA + II_LEN + III_LEN
TOTAL = M4 + IV_FUGA + IV_CODA
extras = D.extras
MOV = {}   # bar -> movement number

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def set_range(P, b0, b1, mov, tempo, dyn, det):
    for b in range(b0, b1):
        MOV[b] = mov; P.tempo[b] = tempo; P.dyn[b] = dyn; P.det[b] = det

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------------- I.
    P.section(0, 'I. Grave — 序奏', '嘆きのパッサカリア: 低弦が歌う嘆きのバス、ヴィオラとホルンが B-A-D-A を唱える')
    D.lament(P, 0, 2, label=True, dyn=lambda c: 0.7, first_cycle_solo=True)
    P.rest_bars('S', 0, 3); P.rest_bars('A', 0, 3)
    set_range(P, 0, I_INTRO, 1, 40, 0.7, 0.98)
    copy_bars(T, P, 0, 44, I_INTRO)
    P.sections = [(b, t.replace('I. Soggetto I 〈MOTHER〉', 'I. Allegro moderato — 主題 I 〈MOTHER〉のフーガ'), s) for b, t, s in P.sections]
    set_range(P, I_INTRO, M2, 1, 76, 0.85, 0.95)
    # ---------------- II.
    P.section(M2, 'II. Adagio — Lamento', '嘆きのバスのパッサカリア ×4。B-A-D-A のカノンが弦を渡り、木管が歌う')
    D.lament(P, M2, 4, dyn=lambda c: [0.55, 0.7, 0.85, 0.6][c])
    P.set_harms(M2 + 12, [['Dm'], ['Dm']]); P.hold.update({M2 + 12, M2 + 13})
    set_range(P, M2, M3, 2, 40, 0.65, 1.0)
    for c in range(4):
        for k in range(3): P.dyn[M2 + 3 * c + k] = [0.55, 0.7, 0.85, 0.6][c]
    P.dyn[M2 + 12] = P.dyn[M2 + 13] = 0.4
    # ---------------- III.
    copy_bars(T, P, 44, 85, M3)
    P.sections = [(b, t.replace('II. Soggetto II 〈トラック18〉', 'III. Scherzo — 主題 II 〈トラック18〉'), s) for b, t, s in P.sections]
    set_range(P, M3, M4, 3, 126, 0.78, 0.6)
    # ---------------- IV.
    copy_bars(T, P, 85, 130, M4)
    P.sections = [(b, t.replace('III. Soggetto III 〈B-A-D-A〉', 'IV. Finale — 主題 III 〈B-A-D-A〉と三重結合').replace('III. Fuga a tre soggetti — 終結', 'IV. Finale — 三重結合の終結'), s) for b, t, s in P.sections]
    set_range(P, M4, M4 + IV_FUGA, 4, 84, 0.95, 0.95)
    c0 = M4 + IV_FUGA
    P.section(c0, 'IV. Coda — Maestoso', 'D 長調のコーダ: 全管弦楽の和音とティンパニ、B-A-D-A の最後の呼びかけ')
    P.set_harms(c0, [['D'], ['G/D'], ['D'], ['Bm', 'Bm', 'A7', 'A7'], ['D'], ['D']])
    P.hold.update(range(c0, TOTAL))
    P.place('S', c0, mat(('B5', 2), ('A5', 2), ('D6', 2), ('A5', 2)), 0, 'B♮-A-D-A (長調)')
    set_range(P, c0, TOTAL, 4, 60, 1.0, 1.0)
    P.dyn[TOTAL - 1] = 0.9
    return P

def post(P, events, ex):
    """楽章ごとの管弦楽法。弦 (S/A/T/B) は synth 側で鳴る。ここでは木管・金管・ティンパニを重ねる。"""
    for v in VOICES:
        for s, d, m, lab in events[v]:
            bar = int(s // BPB); mov = MOV.get(bar, 1); dyn = P.dyn.get(bar, 1.0)
            if not lab: continue
            if v == 'S': add('FL', 0, s, d, m + 12 if m < 72 else m, 0.4 * dyn)
            if v == 'A': add('WW', 0, s, d, m, 0.45 * dyn)
            if v == 'T': add('CL', 0, s, d, m, 0.4 * dyn)
            if mov == 4 and v in 'SA' and (lab.startswith('S1') or lab.startswith('S3')):
                add('TR', 0, s, d, m if 58 <= m <= 82 else m + 12, 0.42 * dyn)
            if mov == 4 and v in 'TB' and (lab.startswith('S1') or lab.startswith('S3')):
                add('TB', 0, s, d, m, 0.45 * dyn)
            if mov == 1 and v in 'TB' and lab.startswith('S1'):
                add('HN', 0, s, d, m, 0.4 * dyn)
    for bar in range(P.nbars):
        mov = MOV.get(bar, 1); dyn = P.dyn.get(bar, 1.0)
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half]); root = 48 + c['root']
            if mov in (2, 4) or (mov == 1 and bar < I_INTRO):
                add('HN', bar, half, 2.2, root, 0.3 * dyn); add('HN', bar, half, 2.2, root + 7, 0.25 * dyn)
            if bar >= M4 + IV_FUGA:   # コーダ: 金管の和音
                third = [m for m in range(60, 72) if m % 12 == c['third']][0]
                add('TR', bar, half, 2.0, root + 12, 0.4 * dyn); add('TR', bar, half, 2.0, third, 0.35 * dyn)
                add('TB', bar, half, 2.0, root - 12, 0.45 * dyn); add('TB', bar, half, 2.0, root - 5, 0.35 * dyn)
        if mov == 3 and bar % 2 == 0: add('TP', bar, 0, 0.5, n('D2') if chord(P.harm[bar * BPB])['root'] == 2 else n('A1'), 0.35 * dyn)
        if mov == 4 and bar >= M4 + 16: add('TP', bar, 0, 0.6, n('D2'), 0.45 * dyn)
    for b in (0, 3, M2, M2 + 3, M2 + 6, M2 + 9):
        add('TP', b, 0, 2, n('D2'), 0.5 * P.dyn.get(b, 1.0))
    c0 = M4 + IV_FUGA
    add('TP', c0, 0, 4, n('D2'), 0.7); add('TP', c0 + 2, 0, 4, n('D2'), 0.6); add('TP', TOTAL - 2, 0, 8, n('D2'), 0.8)

META = {
    'style': 'symphony', 'humanize': True,
    'title': 'Symphony BADA — Sinfonia in D minor',
    'subtitle': '交響曲 ニ短調 (4 楽章) — I. Grave–Allegro moderato ／ II. Adagio Lamento ／ III. Scherzo ／ IV. Finale Maestoso',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA) ／ 嘆きのバス ← 半音下行 D C# C B B♭ A',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 のため息 ／ 録音 090146    ｜  管弦楽: 弦 5 部 · Fl · Ob · Cl · Hn · Tp · Tb · Timp (すべて合成)',
               '弦 (Vn I / Vn II / Va / Vc+Cb) がフーガの 4 声を担い、木管が主題の入りを重ね、金管は終楽章とコーダで加わる。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_symphony.json'
    compose.main(out, seed=21, bpm=76, builder=build, meta=META, extras=extras, post=post)
