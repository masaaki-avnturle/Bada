#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA III — Grave, for Grand Piano (à six mains et plus)
  ♩=44 の極めて遅いテンポ。4 声のフーガ (第 I 部 と 三重結合部を抜粋) の上下に
    H: 高音の鐘のカノン (B-A-D-A を全音符で、2 小節遅れの追走つき)
    W: 分散和音のうねり (安心感のための和音の洗い流し)
    L: 低音オクターヴの心拍
  を重ね、6〜7 層 (4 本の手を超える) の多層書法にする。終結は D 長調の B♮-A-D-A で安らぐ。
"""
import sys, math
from compose import *
import compose

BADA = mat(('Bb4',2),('A4',2),('D5',2),('A4',2))
HADA = mat(('B4',2),('A4',2),('D5',2),('A4',2))              # 長調版 (H-A-D-A)
REQUIEM_CHANT = mat(('F4',2),('F4',1),('G4',1),('F4',2),('E4',1),('D4',1),('F4',2),('G4',2),
                    ('A4',3),('G4',1),('F4',2),('E4',2),('D4',4))
INTRO, RIT, CODA = 8, 8, 16
SEG1 = (0, 44)      # フーガ第 I 部
SEG2 = (97, 130)    # エピソード 7 → 三重結合 I/II/III → 休止 → ピカルディ
NF = (SEG1[1] - SEG1[0]) + (SEG2[1] - SEG2[0])
TOTAL = INTRO + NF + RIT + CODA + 2
extras = []

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None):
    extras.append({'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label})

def copy_bars(T, P, s0, s1, dst):
    """T の小節 [s0, s1) を P の dst 以降へ複写 (和声・固定音・休止・保持・主題入り・セクション)。"""
    off = dst - s0
    for b in range(s0 * BPB, s1 * BPB): P.harm[b + off * BPB] = T.harm[b]
    for v in VOICES:
        for s, d, m, lab in T.fixed[v]:
            if s0 * BPB <= s < s1 * BPB: P.fixed[v].append((s + off * BPB, d, m, lab))
        for b in T.rest[v]:
            if s0 * BPB <= b < s1 * BPB: P.rest[v].add(b + off * BPB)
    for bar in T.hold:
        if s0 <= bar < s1: P.hold.add(bar + off)
    for b, lab, v in T.entries:
        if s0 * BPB <= b < s1 * BPB: P.entries.append((b + off * BPB, lab, v))
    for bar, t, s in T.sections:
        if s0 <= bar < s1: P.sections.append((bar + off, t, s))

def wash(P, bar0, bar1, lo=45, hi=79, vel=0.30):
    """各拍の和音を分散和音 (8 分音符) で上下に洗い流す層 W。"""
    for bar in range(bar0, bar1):
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half])
            tones = [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
            # 低い方から 4 音上行 → その上の 4 音を下行 (小節内でうねる)
            base = [m for m in tones if m % 12 == c['bass']][0]
            asc = [m for m in tones if m >= base][:4]
            desc = list(reversed([m for m in tones if m > asc[-1]][:4])) if len([m for m in tones if m > asc[-1]]) >= 4 else list(reversed(asc))
            seq = asc + desc
            for i, m in enumerate(seq[:4]):
                add('W', bar, half + i * 0.5, 0.5, m, vel * (1.0 if i == 0 else 0.8))

def low_octaves(P, bar0, bar1, every=1, vel=0.55):
    for bar in range(bar0, bar1, every):
        c = chord(P.harm[bar * BPB])
        root = 24 + c['bass'] + (12 if c['bass'] < 2 else 0)      # C1..B1 付近
        add('L', bar, 0, 4, root, vel); add('L', bar, 0, 4, root + 12, vel * 0.8)
        if every == 1: add('L', bar, 2, 2, root + 12, vel * 0.45)

def bell_canon(P, bar0, nreps, follow=True, label='B-A-D-A (鐘)', material=None):
    """高音の鐘: B-A-D-A を全音符で (1 音 = 1 小節)。2 小節遅れの追走 (5 度上) つき。"""
    mat_ = material or [n('Bb6'), n('A6'), n('D7'), n('A6')]
    for r in range(nreps):
        for i, m in enumerate(mat_):
            add('H', bar0 + r * 4 + i, 0, 4, m, 0.42, label if (i == 0 and r == 0) else None)
            if follow: add('H', bar0 + r * 4 + i + 2, 0, 4, m + 7 - 12, 0.28)

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------------- I. Introitus (D 長調と短調のあいだで安らぐ)
    P.section(0, 'I. Introitus — Grave', '分散和音のうねりと低音の心拍、高音の鐘のカノン、Requiem aeternam の聖歌')
    P.set_harms(0, [['D'], ['D'], ['G/D', 'G/D', 'D', 'D'], ['Bb'], ['Gm', 'Gm', 'A', 'A'], ['Dm'], ['Gm', 'Gm', 'A7', 'A7'], ['A7']])
    for v in VOICES: P.rest_bars(v, 0, 2)
    P.place('S', 2, REQUIEM_CHANT, 0, 'Requiem aeternam')
    P.place('A', 3, BADA, 0, 'B-A-D-A')
    P.rest_bars('T', 0, 4)
    P.hold.update(range(INTRO))
    for bar in range(INTRO): P.dyn[bar] = 0.6 + 0.04 * bar
    wash(P, 0, INTRO); low_octaves(P, 0, INTRO); bell_canon(P, 0, 2)
    # ---------------- II. Fuga (第 I 部)
    d1 = INTRO
    copy_bars(T, P, SEG1[0], SEG1[1], d1)
    for bar in range(d1, d1 + 44): P.dyn[bar] = 0.85
    wash(P, d1 + 12, d1 + 44, vel=0.22)                  # 3 声目以降が入ったら洗い流しも入る
    low_octaves(P, d1, d1 + 44, every=2, vel=0.45)
    for k in range(0, 44, 4): add('H', d1 + k, 0, 4, n('D7'), 0.25)     # 4 小節ごとの高い鐘
    # ---------------- Ritornello — Mantra
    r0 = d1 + 44
    P.section(r0, 'Ritornello — Mantra', 'B-A-D-A の回帰句: 中声の唱え + 高音の鐘のカノン + 分散和音')
    prog = [['Gm/D', 'Gm/D', 'Dm', 'Dm'], ['Bb/D', 'Bb/D', 'Dm', 'Dm']]
    for k in range(RIT // 2):
        P.set_harms(r0 + 2 * k, prog)
        P.place(('A', 'T')[k % 2], r0 + 2 * k, BADA, (0, -12)[k % 2], 'B-A-D-A' if k == 0 else None)
    P.hold.update(range(r0, r0 + RIT))
    for bar in range(r0, r0 + RIT): P.dyn[bar] = 0.75
    wash(P, r0, r0 + RIT); low_octaves(P, r0, r0 + RIT); bell_canon(P, r0, 2)
    # ---------------- III. Fuga a tre soggetti (三重結合)
    d2 = r0 + RIT
    copy_bars(T, P, SEG2[0], SEG2[1], d2)
    P.sections = [(b, t.replace('I. Soggetto I', 'II. Fuga — Soggetto I'), s) for b, t, s in P.sections]
    P.section(d2, 'III. Fuga a tre soggetti — Grave', '三主題の三重結合 ×3 (ニ短調 → イ短調 → ニ短調) を極めて遅く、7 層で')
    for bar in range(d2, d2 + 33): P.dyn[bar] = 0.9
    wash(P, d2, d2 + 29, vel=0.20)
    low_octaves(P, d2, d2 + 33, every=2, vel=0.5)
    for k in range(0, 33, 4): add('H', d2 + k, 0, 4, n('D7'), 0.25)
    # ---------------- IV. Lux aeterna — 長調へ (安らぎ)
    c0 = d2 + 33
    P.section(c0, 'IV. Lux aeterna — Mantra (in D major)', 'B-A-D-A → B♮-A-D-A: ニ長調へ移り、鐘のカノンと分散和音の中で安らかに消える')
    for k in range(4):
        P.set_harms(c0 + 2 * k, prog)
        P.place('A', c0 + 2 * k, BADA, 0, 'B-A-D-A' if k == 0 else None)
    prog_major = [['G/D', 'G/D', 'D', 'D'], ['D', 'D', 'D', 'D']]
    for k in range(4, 8):
        P.set_harms(c0 + 2 * k, prog_major)
        P.place(('A', 'S')[k % 2], c0 + 2 * k, HADA, (0, 12)[k % 2], 'B♮-A-D-A (長調)' if k == 4 else None)
    P.hold.update(range(c0, TOTAL))
    for k in range(CODA): P.dyn[c0 + k] = max(0.2, 0.8 - 0.04 * k)
    wash(P, c0, c0 + CODA); low_octaves(P, c0, c0 + CODA)
    bell_canon(P, c0, 2); bell_canon(P, c0 + 8, 2, label=None, material=[n('B6'), n('A6'), n('D7'), n('A6')])
    P.set_harms(TOTAL - 2, [['D'], ['D']])
    P.place('A', TOTAL - 2, mat(('A4', 8)), 0, None); P.place('S', TOTAL - 2, mat(('F#5', 8)), 0, None)
    P.dyn[TOTAL - 2] = P.dyn[TOTAL - 1] = 0.3
    add('L', TOTAL - 2, 0, 8, n('D1'), 0.6); add('L', TOTAL - 2, 0, 8, n('D2'), 0.5); add('H', TOTAL - 2, 0, 8, n('D7'), 0.4)
    return P

META = {
    'style': 'piano',
    'title': 'Requiem BADA III — Grave',
    'subtitle': 'for Grand Piano (à six mains et plus) — ♩=44 ／ 4 声フーガ + 鐘のカノン + 分散和音 + 低音の心拍 = 7 層',
    'footer': ['主題 I ← MOTHER (LUNA SEA) ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A (BADA) + 録音 090933 ／ 聖歌 ← Requiem aeternam',
               'エピソード ← LOVELESS ／ トラック17 ／ トラック8 ／ 録音 090146    ｜  合成: グランドピアノ (非整数倍音・ハンマー雑音・ペダル残響)',
               '4 本の手を超える 7 層: S/A/T/B のフーガ + 高音の鐘のカノン (H) + 分散和音のうねり (W) + 低音オクターヴの心拍 (L)。終結はニ長調。'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_piano.json'
    compose.main(out, seed=5, bpm=44, builder=build, meta=META, extras=extras)
