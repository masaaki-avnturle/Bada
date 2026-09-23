#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA · Cor — 心臓のレクイエム (ニ短調)
  これまでのレクイエムとフーガを、心臓の鼓動「ドックン (I 音) – ドックン (II 音)」を音楽の流れの芯にして作り換える。
    - 1 拍 = 1 心拍。心拍数がそのままテンポになり、曲の起伏とともに速くなり、遅くなる
      (安静 56 → フーガ I で 72 → 嘆きで 58 → 三重フーガの頂点で 84 → Lux aeterna で 44 へ静まる)
    - 鼓動は和声に溶ける: 「ドッ」(I 音) はその拍の和音の低音、「クン」(II 音) はその 5 度上の音高で鳴る
    - フーガの総休止 (バッハの自筆譜が途切れる箇所へのオマージュ) では心臓も 2 拍止まり、強く打ち直す
  形式: I. Introitus — Cor (心臓だけ → ドローン → Requiem aeternam → B-A-D-A)
        II. Fuga I (主題 I の 4 声フーガ) → Lamento (嘆きのバス、鼓動が落ち着く)
        III. Fuga a tre soggetti (B-A-D-A と三重結合、鼓動が高まり、総休止で止まる)
        IV. Lux aeterna — B-A-D-A のマントラ、鼓動がゆっくり静まり D 長調で安らぐ
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D

REQUIEM_CHANT = mat(('F4',2),('F4',1),('G4',1),('F4',2),('E4',1),('D4',1),('F4',2),('G4',2),
                    ('A4',3),('G4',1),('F4',2),('E4',2),('D4',4))
BADA = mat(('Bb4',2),('A4',2),('D5',2),('A4',2))
DRONE_BAR = [(4, n('D2'))]
MANTRA_PROG = [['Gm/D', 'Gm/D', 'Dm', 'Dm'], ['Bb/D', 'Bb/D', 'Dm', 'Dm']]

INTRO, F1, RIT, F2, CODA = 8, 44, 6, 45, 16
B_F1 = INTRO; B_RIT = B_F1 + F1; B_F2 = B_RIT + RIT; B_CODA = B_F2 + F2; TOTAL = B_CODA + CODA
PAUSE_BAR = B_F2 + (126 - 85)            # フーガの総休止 (1・2 拍目)
extras = []
HEART = {}                               # bar -> 鼓動の強さ

def add(v, beat, dbeats, midi, gain, label=None, **kw):
    e = {'v': v, 'beat': beat, 'dbeats': dbeats, 'm': midi, 'gain': gain, 'label': label}
    e.update(kw); extras.append(e)
def bell(bar, beat, midi=n('D3'), gain=1.0, dbeats=8): add('X', bar * BPB + beat, dbeats, midi, gain)
def drone(bar0, bar1, midi=n('D1'), gain=1.0): add('D', bar0 * BPB, (bar1 - bar0) * BPB, midi, gain)

def ramp(P, b0, b1, t0, t1):
    for k in range(b1 - b0): P.tempo[b0 + k] = round(t0 + (t1 - t0) * k / max(1, b1 - b0 - 1), 1)

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------------- I. Introitus — Cor
    P.section(0, 'I. Introitus — Cor', '心臓の鼓動だけが聞こえる → D のドローン → Requiem aeternam の聖歌 → B-A-D-A の唱え')
    P.set_harms(0, [['Dm']] * 4 + [['Gm'], ['Dm'], ['Bb'], ['A']])
    for v in VOICES: P.rest_bars(v, 0, 2)
    P.place('S', 2, REQUIEM_CHANT, 0, 'Requiem aeternam')
    P.place('A', 6, BADA, 0, 'B-A-D-A')
    P.rest_bars('A', 2, 6); P.rest_bars('T', 2, 4)
    for bar in range(2, INTRO): P.place('B', bar, DRONE_BAR, 0, None)
    P.hold.update(range(INTRO))
    for bar in range(INTRO): P.dyn[bar] = 0.45 + 0.05 * bar; HEART[bar] = 1.0 if bar < 2 else 0.85
    drone(2, INTRO, gain=0.9); bell(2, 0, gain=0.8); bell(6, 0, gain=0.7)
    ramp(P, 0, INTRO, 56, 60)
    # ---------------- II. Fuga I — 主題 I 〈MOTHER〉
    copy_bars(T, P, 0, F1, B_F1)
    P.sections = [(b, t.replace('I. Soggetto I 〈MOTHER〉', 'II. Fuga — 主題 I 〈MOTHER〉'), s.replace('主題 I の提示 — 4 声フーガ (ニ短調)', '主題 I の 4 声フーガ — 鼓動は 62 から 72 へ少しずつ速まる'))
                  for b, t, s in P.sections]
    ramp(P, B_F1, B_RIT, 62, 72)
    for bar in range(B_F1, B_RIT): P.dyn[bar] = 0.85; HEART[bar] = 0.5 + 0.15 * (bar - B_F1) / F1
    for bar in range(B_F1, B_RIT, 4): bell(bar, 0, gain=0.3, dbeats=6)
    # ---------------- Lamento — 鼓動が落ち着く
    P.section(B_RIT, 'Lamento — 嘆きのバス', '歌う嘆きのバス (D C# C B B♭ A) と B-A-D-A のカノン。鼓動は 66 から 58 へ落ち着き、深くなる')
    D.lament(P, B_RIT, 2, label=True, dyn=lambda c: 0.7 - 0.05 * c)
    P.rest_bars('S', B_RIT, B_RIT + 3)
    ramp(P, B_RIT, B_F2, 66, 58)
    for bar in range(B_RIT, B_F2): HEART[bar] = 0.8
    drone(B_RIT, B_F2, gain=0.6)
    # ---------------- III. Fuga a tre soggetti — 鼓動が高まる
    copy_bars(T, P, 85, 130, B_F2)
    P.sections = [(b, t.replace('III. Soggetto III 〈B-A-D-A〉', 'III. Fuga a tre soggetti — 主題 III 〈B-A-D-A〉')
                   .replace('III. Fuga a tre soggetti — 終結', 'III. 三重結合の終結 — 鼓動の頂点と総休止'), s) for b, t, s in P.sections]
    ramp(P, B_F2, B_F2 + 16, 64, 72)                    # B-A-D-A の提示
    ramp(P, B_F2 + 16, B_F2 + 36, 74, 84)               # 三重結合 I・II
    ramp(P, B_F2 + 36, PAUSE_BAR + 1, 84, 80)           # 最終結合
    ramp(P, PAUSE_BAR + 1, B_CODA, 70, 60)              # コーダ (ピカルディ)
    for bar in range(B_F2, B_CODA):
        k = bar - B_F2
        P.dyn[bar] = 0.9 if k < 16 else 1.0
        HEART[bar] = 0.55 + 0.3 * min(1.0, k / 36)
    for b0 in (101, 121):
        s = B_F2 + b0 - 85; drone(s, s + 5, gain=0.7)
        for k in range(5): bell(s + k, 0, gain=0.55)
    # ---------------- IV. Lux aeterna — 鼓動が静まる
    P.section(B_CODA, 'IV. Lux aeterna — Requiem', 'B-A-D-A のマントラ。鼓動は 60 から 44 へゆっくり静まり、D 長調の和音の中で安らぐ')
    for k in range(6):
        b = B_CODA + 2 * k
        P.set_harms(b, MANTRA_PROG)
        v = ('A', 'S', 'A', 'T', 'A', 'S')[k]
        P.place(v, b, BADA, {'S': 12, 'A': 0, 'T': -12}[v], 'B-A-D-A' if k in (0, 3) else None)
        for j in range(2): P.place('B', b + j, DRONE_BAR, 0, None)
        bell(b, 0, gain=0.7); bell(b + 1, 2, midi=n('A2'), gain=0.4)
    P.set_harms(TOTAL - 4, [['D']] * 4)
    P.place('A', TOTAL - 4, mat(('A4', 16)), 0, None); P.place('S', TOTAL - 4, mat(('F#5', 16)), 0, None)
    for j in range(4): P.place('B', TOTAL - 4 + j, DRONE_BAR, 0, None)
    P.rest_bars('T', B_CODA, B_CODA + 6)
    P.hold.update(range(B_CODA, TOTAL))
    ramp(P, B_CODA, TOTAL, 60, 44)
    for k in range(CODA):
        P.dyn[B_CODA + k] = max(0.28, 0.85 - 0.035 * k); HEART[B_CODA + k] = max(0.3, 0.85 - 0.035 * k)
    drone(B_CODA, TOTAL, gain=0.9)
    bell(TOTAL - 4, 0, gain=0.9, dbeats=16)
    return P

def post(P, events, ex):
    """心臓の鼓動: 1 拍 = 1 心拍。I 音 (ドッ) はその拍の和音の低音、II 音 (クン) は 5 度上。
    収縮期 (I 音 → II 音) は心拍が速いほど短い。"""
    for b in range(P.N):
        bar = b // BPB; beat = b % BPB
        if bar == PAUSE_BAR and beat in (0, 1): continue          # 総休止: 心臓も止まる
        hr = P.tempo.get(bar, 60)
        c = chord(P.harm[b]); pc = c['bass']
        low = 31 + (pc - 31) % 12                                  # G1〜F#2 (49〜92 Hz)
        g = HEART.get(bar, 0.6) * (1.0 if beat == 0 else 0.86)
        if bar == PAUSE_BAR and beat == 2: g = min(1.0, g * 1.5)   # 止まった後、強く打ち直す
        systole = max(0.24, 0.32 - 0.0012 * (hr - 60))             # 秒
        add('HB', b, 0.25, low, g, 'Cor' if b == 0 else None, kind='lub')
        add('HB', b + systole * hr / 60.0, 0.2, low + 7, g * 0.72, None, kind='dub')

META = {
    'style': 'heart', 'vowel': 'o', 'heart_gain': 2.5,
    'title': 'Requiem BADA · Cor',
    'subtitle': '心臓のレクイエム — ニ短調 ／ レクイエムとフーガを、鼓動「ドックン・ドックン」を芯にして: 1 拍 = 1 心拍',
    'footer': ['鼓動 ← 心音の I 音 (ドッ) と II 音 (クン)。I 音はその拍の和音の低音、II 音は 5 度上に調律し、心拍数 = テンポ (56 → 72 → 58 → 84 → 44)',
               '主題 I ← MOTHER ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A ／ 嘆きのバス ／ 聖歌 Requiem aeternam    ｜  合唱 (オ)+オルガン · 鼓動 · 弔鐘 · ドローン',
               '総休止では心臓も 2 拍止まり、強く打ち直す。Lux aeterna で鼓動は静まり、D 長調の和音の中で安らぐ。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_heart.json'
    compose.main(out, seed=11, bpm=60, builder=build, meta=META, extras=extras, post=post)
