#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BADA 528 — Sweet Trio (Ambient Trio Sonata after BWV 528, in E minor)
  骨格: BWV 528 (バッハ オルガン・トリオ・ソナタ第 4 番 ホ短調) の「2 つの上声部 + バス」のトリオ書法。
  素材: これまでの作曲集の集大成 — 主題 I (MOTHER) / 主題 II (トラック18) / 主題 III (B-A-D-A) / 嘆きのバス / 三重フーガ。
  雰囲気: 坂本龍一「Sweet Revenge」を思わせるダウンテンポの循環コード (Em7 – Cmaj7 – Am7 – B7)、
          エレクトリック・ピアノのコンピング、シンセ・パッド、ブラシのグルーヴ、抒情的なシンセ・リードのフック。
          (旋律の引用はしない。コード進行の型・音色・グルーヴだけを参照する。)
  形式 (催眠的な反復):
    Intro (グルーヴ + フック) → Trio (主題 I と主題 II の二重奏, 上下交換) → Lament (嘆きのバス + B-A-D-A のカノン)
    → Fugato (主題 I の 4 声提示, ピアノ + 弦) → 三重結合 → Lament 再現 → Outro (フックの反復 → B-A-D-A のマントラ → 消える)
  全体をニ短調で書き、出力時に +2 半音してホ短調にする。
"""
import sys, math
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D

LOOP = [['Dm7'], ['Bbmaj7'], ['Gm7'], ['A7']]
LOOP2 = [['Dm7'], ['Bbmaj7'], ['Em7b5'], ['A7']]
HOOK = mat(('D5',1.5),('C5',.5),('A4',2), ('F4',1.5),('G4',.5),('A4',2), ('Bb4',1.5),('A4',.5),('G4',2), ('E4',1.5),('F4',.5),('E4',1),('C#4',1))
INTRO, TRIO, LAM, FUG, TRI, LAM2, OUT = 8, 16, 12, 22, 6, 6, 24
B0 = 0; B1 = B0 + INTRO; B2 = B1 + TRIO; B3 = B2 + LAM; B4 = B3 + FUG; B5 = B4 + TRI; B6 = B5 + LAM2; TOTAL = B6 + OUT
extras = D.extras
TRANSPOSE = 2

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def set_range(P, b0, b1, role, dyn, det=0.95):
    for b in range(b0, b1): P.role[b] = role; P.dyn[b] = dyn; P.det[b] = det

def groove_bass(P, bar0, bar1):
    """ゆったりした電気ベース: 根音 (1.5) – 5 度 (0.5) – 根音 (1.5) – 4 度 (0.5)"""
    for bar in range(bar0, bar1):
        c = chord(P.harm[bar * BPB]); r = 36 + c['bass'] + (12 if c['bass'] < 2 else 0)
        P.place('B', bar, [(1.5, r), (.5, r + 7), (1.5, r), (.5, r + 5)], 0, None)

def loop_harm(P, bar0, nbars):
    for k in range(nbars):
        P.set_harm(bar0 + k, (LOOP if (k // 4) % 2 == 0 else LOOP2)[k % 4])

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------- Intro
    P.section(B0, 'Intro — Groove', '循環コード Em7–Cmaj7–Am7–B7 の上に、エレピ・パッド・ブラシ、そしてシンセ・リードのフック')
    loop_harm(P, B0, INTRO); groove_bass(P, B0, INTRO)
    for v in 'SAT': P.rest_bars(v, B0, B1)
    set_range(P, B0, B1, 'groove', 0.65)
    P.place('S', B1 - 4, HOOK, 0, 'Hook (シンセ・リード)')
    # ---------- Trio (BWV 528 風: 2 上声 + バス)
    P.section(B1, 'Trio — 主題 I × 主題 II', 'BWV 528 風のトリオ: オーボエが主題 I、フルートが主題 II、電気ベースが歩く。5 小節後に上下を交換')
    P.set_harms(B1, compose.H_S1); P.place('S', B1, compose.S1, 12, 'S1 (オーボエ)'); P.place('A', B1, compose.S2, 0, 'S2 (フルート)')
    P.set_harms(B1 + 5, compose.H_S1); P.place('A', B1 + 5, compose.S1, 0, 'S1 (オーボエ)'); P.place('S', B1 + 5, compose.S2, 12, 'S2 (フルート)')
    P.rest_bars('T', B1, B1 + 10)
    loop_harm(P, B1 + 10, 6); P.set_harm(B1 + 14, 'Gm7'); P.set_harm(B1 + 15, 'A7')
    P.place('S', B1 + 10, HOOK, 0, 'Hook')
    for v in 'AT': P.rest_bars(v, B1 + 10, B2)
    set_range(P, B1, B2, 'trio', 0.8)
    # ---------- Lament
    P.section(B2, 'Lament — 嘆きのバス', '嘆きのバス (E D# D C# C B) のパッサカリア。B-A-D-A (C–B–E–B) のカノンをシンセ・リードとチェロが歌う')
    D.lament(P, B2, 4, label=True, dyn=lambda c: 0.7 + 0.05 * c)
    P.rest_bars('S', B2, B2 + 3)
    set_range(P, B2, B3, 'lament', 0.75)
    for c in range(4):
        for k in range(3): P.dyn[B2 + 3 * c + k] = 0.7 + 0.05 * c
    # ---------- Fugato
    copy_bars(T, P, 0, FUG, B3)
    P.sections = [(b, t.replace('I. Soggetto I 〈MOTHER〉', 'Fugato — 主題 I 〈MOTHER〉の 4 声提示'), s) for b, t, s in P.sections]
    set_range(P, B3, B4, 'fugato', 0.85)
    # ---------- Triple
    copy_bars(T, P, 101, 107, B4)
    P.section(B4, 'Fuga a tre soggetti — 三重結合', '主題 I + II + III が全楽器で重なる頂点')
    set_range(P, B4, B5, 'triple', 1.0)
    # ---------- Lament reprise
    P.section(B5, 'Lament — 再現', '嘆きのバスの再現 (全楽器)')
    D.lament(P, B5, 2, dyn=lambda c: 0.9)
    set_range(P, B5, B6, 'lament2', 0.9)
    # ---------- Outro
    P.section(B6, 'Outro — Mantra', 'フックの反復 → B-A-D-A のマントラ → パッドの残響に消える')
    loop_harm(P, B6, OUT - 4); groove_bass(P, B6, B6 + 16)
    for v in 'SAT': P.rest_bars(v, B6, TOTAL)
    P.place('S', B6, HOOK, 0, 'Hook'); P.place('S', B6 + 4, HOOK, 0, None); P.place('S', B6 + 8, HOOK, 0, None)
    for k in range(4): P.place('A', B6 + 12 + 2 * k, D.BADA, 0, 'B-A-D-A (マントラ)' if k == 0 else None)
    P.set_harms(B6 + 12, [['Gm7', 'Gm7', 'Dm7', 'Dm7'], ['Bbmaj7', 'Bbmaj7', 'Dm7', 'Dm7']] * 4)
    P.set_harms(TOTAL - 4, [['Dm7']] * 4)
    P.place('B', TOTAL - 4, mat(('D2', 8), ('D2', 8)), 0, None)
    P.rest_bars('B', B6 + 16, TOTAL - 4)
    P.hold.update(range(TOTAL - 4, TOTAL))
    for k in range(OUT): P.dyn[B6 + k] = 0.75 if k < 12 else max(0.2, 0.75 - 0.05 * (k - 12))
    for k in range(OUT): P.role[B6 + k] = 'groove'
    return P

def post(P, events, ex):
    """グルーヴと重ね: エレピのコンピング、パッド、ドラム、弦の重ね、木管/リードによる主題の重ね。"""
    for bar in range(P.nbars):
        role = P.role.get(bar, ''); dyn = P.dyn.get(bar, 1.0)
        # ドラム (ブラシ): lament は薄く、triple は強め
        if role in ('groove', 'trio', 'fugato', 'triple', 'lament2') and bar >= 2 and bar < TOTAL - 4:
            g = {'groove': 0.5, 'trio': 0.5, 'fugato': 0.35, 'triple': 0.6, 'lament2': 0.45}[role] * dyn
            add('DR', bar, 0, .5, 36, g); add('DR', bar, 2.5, .5, 36, g * 0.8)
            add('DR', bar, 1, .5, 38, g * 0.7); add('DR', bar, 3, .5, 38, g * 0.75)
            for k in range(8): add('DR', bar, k * .5, .25, 42, g * (0.45 if k % 2 == 0 else 0.3))
            add('DR', bar, 3.5, .25, 46, g * 0.35)
        if role == 'lament':
            for k in range(4): add('DR', bar, k, .25, 46, 0.25 * dyn)
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half]); root = c['root']
            tones = [m for m in range(60, 76) if m % 12 in c['pcs']][:4]
            # パッド (常に、役割で濃さを変える)
            pv = {'groove': 0.2, 'trio': 0.14, 'lament': 0.22, 'fugato': 0.12, 'triple': 0.22, 'lament2': 0.24}.get(role, 0.18) * dyn
            for i, m in enumerate(tones[:3]): add('PD', bar, half, 2.6, m, pv * (1.0 if i == 0 else 0.8))
            add('PD', bar, half, 2.6, 62 + ((root + 2) % 12), pv * 0.55)           # 9 度
            # エレピのコンピング: 1 拍目と 2.5 拍目 (シンコペーション)
            if role in ('groove', 'trio', 'lament', 'lament2'):
                ev = {'groove': 0.42, 'trio': 0.3, 'lament': 0.32, 'lament2': 0.4}[role] * dyn
                for i, m in enumerate(tones):
                    add('EP', bar, half, 1.2, m, ev * (0.9 if i else 1.0)); add('EP', bar, half + 1.5, 0.5, m, ev * 0.7)
            # 弦のパッド (fugato / triple / lament2)
            if role in ('fugato', 'triple', 'lament2'):
                sv = {'fugato': 0.16, 'triple': 0.3, 'lament2': 0.26}[role] * dyn
                add('V2', bar, half, 2.2, tones[1] if len(tones) > 1 else tones[0], sv); add('VA', bar, half, 2.2, tones[0] - 12, sv)
    # 主題の重ね
    for v in VOICES:
        for s, d, m, lab in events[v]:
            bar = int(s // BPB); role = P.role.get(bar, ''); dyn = P.dyn.get(bar, 1.0)
            if lab:
                if lab.startswith('Hook'): add('LD', 0, s, d, m, 0.55 * dyn)
                elif 'B-A-D-A' in lab or lab.startswith('S3'): add('LD', 0, s, d, m + (12 if m < 60 else 0), 0.42 * dyn)
                elif lab.startswith('S1'): add('WW', 0, s, d, m, 0.45 * dyn)
                elif lab.startswith('S2'): add('FL', 0, s, d, m + (12 if m < 65 else 0), 0.4 * dyn)
                elif lab.startswith('Lamento'): add('VC', 0, s, d, m + 12, 0.45 * dyn)
            if v == 'B' and role in ('lament', 'lament2'): add('VC', 0, s, d, m + 12, 0.3 * dyn)
            if role in ('triple',) and v in 'SAT': add('V1' if v == 'S' else 'VA', 0, s, d, m, 0.3 * dyn)
    # マントラのカノン (B-A-D-A をパッドの上でリードが反復するあいだ、フルートが 1 小節遅れで追う)
    for k in range(4):
        b = B6 + 12 + 2 * k + 1
        for i, (dd, mm) in enumerate(D.BADA): add('FL', b, i * 2 - (0 if i == 0 else 0), 2, mm + 12, 0.22 * P.dyn.get(b, 1.0)) if False else None
    add('PD', TOTAL - 4, 0, 16, n('D3'), 0.25); add('PD', TOTAL - 4, 0, 16, n('A3'), 0.2); add('PD', TOTAL - 4, 0, 16, n('E4'), 0.15)

META = {
    'style': 'sweet', 'detach': 0.9, 'humanize': True,
    'title': 'BADA 528 — Sweet Trio',
    'subtitle': 'Ambient Trio Sonata after BWV 528 · E minor · ♩=72 ／ これまでの主題 (I・II・B-A-D-A・嘆きのバス・三重フーガ) をダウンテンポの循環コードの上に集大成',
    'footer': ['骨格 ← J.S.バッハ BWV 528 (トリオ・ソナタ第 4 番 ホ短調) の 2 上声+バスのトリオ書法 ／ 雰囲気 ← 坂本龍一「Sweet Revenge」風の循環コード・エレピ・パッド (旋律は引用せず)',
               '主題 I ← MOTHER ／ 主題 II ← トラック18 ／ 主題 III ← B-A-D-A ／ 嘆きのバス ／ 三重フーガ    ｜  楽器: ピアノ · オーボエ · フルート · チェロ · 弦 + エレピ · パッド · リード · 電気ベース · ブラシ',
               'Intro → Trio → Lament → Fugato → 三重結合 → Lament 再現 → Outro (フック ×3 → B-A-D-A のマントラ → 消える)'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_sweet.json'
    compose.main(out, seed=28, bpm=72, builder=build, meta=META, extras=extras, transpose_semis=TRANSPOSE, post=post)
