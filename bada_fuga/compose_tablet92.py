#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCII · Contrapunctus XIV sinfonico (piano_solo_8x をコントラプンクトゥス XIV の主題にして、管弦楽で)
  XCI のバックに敷いた piano_solo_8x.mp4 (42 分、×8 のピアノ) のロ短調の窓 (2186〜2386 秒) を採譜 (basic-pitch) し、
  その最上声の線からバッハ『フーガの技法』Contrapunctus XIV (未完の三重フーガ、ニ短調) の主題を作って、管弦楽 (交響曲の編成) で:
    第 1 主題 (荘重)      = 2186〜2250 秒の最上声  F4·B3·F4·E4·A3·E4·G3·D4 を +5 (ロ → ホ、音の集合が ニ短調の音階にそろう) して 8 拍に
                            → シ♭・ミ・シ♭・ラ・レ・ラ・ソ・ファ・レ (源の シ–ファ の三全音が シ♭–ミ に)
    第 2 主題 (駆け足)    = 2250〜2386 秒の最上声 (イ・ソ・ハの領域) を +5 して 8 分音符の 2 小節に
    第 3 主題             = B-A-C-H (シ♭・ラ・ド・シ — バッハ自身の署名、Contrapunctus XIV の第 3 主題そのもの)
  形式 (♩=60、88 小節 = 5 分 52 秒):
    Prologo   (0〜8)     piano_solo_8x の実音 (主題を採った所、+5 に移して、速さは変えず) — 低弦の レ とティンパニが近づく
    Sectio I  (8〜34)    第 1 主題: 4 声の提示 (弦) → エピソード → 反行形 (オーボエ) → 下属調の入りとストレッタ → 低弦の拡大形 (ホルン) → 属音の保続 → 終止
    Sectio II (34〜56)   第 2 主題: 4 声の提示 (木管が加わる) → エピソード → 第 1 主題との二重フーガ (4 回) → エピソード → 終止
    Sectio III (56〜76)  B-A-C-H: 4 声の提示 (金管) → 三重フーガ (3 つの主題を同時に、ティンパニ) → 第 1 主題の拡大の上で → 3 度目の重なりの
                         2 小節目の 2 拍目で楽譜が途切れる (Contrapunctus XIV の 239 小節目のように) → 沈黙
    Epilogo   (76〜88)   piano_solo_8x の実音だけが戻って、消えていく (2250 秒から、+5 でニ短調に)
  管弦楽: 弦 5 部 (S/A/T/B → Vn I / Vn II / Va / Vc+Cb) + Fl・Ob・Cl + Hn・Tp・Tb + Timp (すべて合成)。声なし。
  使い方: python compose_tablet92.py <piano_solo_8x.wav> [score_tablet92.json]
"""
import sys, os
from compose import *
import compose

CANDS = ['Dm', 'Gm', 'A', 'A7', 'F', 'Bb', 'C', 'Em7b5', 'Gm/Bb', 'Dm/F', 'G7', 'E7', 'Eb', 'Cm']  # 和音の候補 (compose_tablet と同じ + B-A-C-H の シ♮ のために G7・E7)

def harm_from_entries(P, b0, b1, entries):
    """その半小節で鳴る主題の音を最も多く含む和音 (compose_tablet5 と同じ)"""
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            cs = max(CANDS, key=lambda c: sum(w * (1 if m % 12 in chord(c)['pcs'] else -0.8) for w, m in notes)) if notes else 'Dm'
            for q in range(2): P.harm[a + q] = cs

BG = os.path.abspath(sys.argv[1]); OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet92.json'
BPM = 60
# 主題 (採譜の最上声から — 上の docstring)
S1 = [(1.5, 70), (0.5, 64), (1, 70), (1, 69), (1, 62), (1, 69), (0.5, 67), (0.5, 65), (1, 62)]                 # シ♭ ミ シ♭ ラ レ ラ ソ ファ レ
S2 = [(0.5, m) for m in (72, 67, 62, 65, 64, 62, 64, 60, 62, 64, 70, 69, 67, 65, 64, 61)]                      # ド ソ レ ファ ミ レ ミ ド レ ミ シ♭ ラ ソ ファ ミ ド#
S3 = [(2, 70), (2, 69), (2, 72), (2, 71)]                                                                      # B-A-C-H
L1, L2, L3 = '主題 I (piano_solo_8x)', '主題 II (piano_solo_8x, 駆け足)', 'B-A-C-H'
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 84, 'A': 74, 'T': 69, 'B': 62}
PRO, SEC1, SEC2, SEC3, EPI = 8, 26, 22, 20, 12
F1 = PRO; F2 = F1 + SEC1; F3 = F2 + SEC2; E0 = F3 + SEC3; TOTAL = E0 + EPI
CUT = None; extras = []; MOV = {}; HN_BARS = set(); TP = []

def add(v, beat, dbeats, midi, gain, label=None):
    extras.append({'v': v, 'beat': beat, 'dbeats': dbeats, 'm': midi, 'gain': gain, 'label': label})

def fit(v, mat, tr):
    if v == 'B' and min(m for _, m in mat) + tr < 36: tr += 12
    if max(m for _, m in mat) + tr > TOP[v]: tr -= 12
    if min(m for _, m in mat) + tr < RANGE[v][0]: tr += 12
    return tr

def entry(P, bar, v, mat, tr0, label, E, beat=0):
    tr = fit(v, mat, octs[v] + tr0)
    P.place(v, bar, mat, tr, label, beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))

def invert(mat):
    m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]

def augment(mat):
    return [(2 * d, m) for d, m in mat]

def expo(P, f, subj, lab, order, E):
    """4 声の提示: 2 小節ずつ、2 番目と 4 番目は属調の答唱"""
    for k, v in enumerate(order):
        entry(P, f + 2 * k, v, subj, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in order[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_from_entries(P, f, f + 8, E)

def build():
    global CUT
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.8
    # ---------------- Prologo: piano_solo_8x の実音
    P.section(0, 'Prologo — piano_solo_8x (実音)', '主題を採った所 (2186 秒から) を +5 に移して、速さは変えず — 低弦の レ とティンパニが近づく')
    for v in VOICES: P.rest_bars(v, 0, PRO)
    for k in range(PRO): MOV[k] = 0
    # ---------------- Sectio I — 第 1 主題
    f = F1; E = []
    P.section(f, 'Sectio I — Soggetto I 〈piano_solo_8x〉', '第 1 主題 (シ♭・ミ・シ♭・ラ・レ・ラ・ソ・ファ・レ) の 4 声の提示 → エピソード → 反行形 → 下属調の入りとストレッタ → 低弦の拡大形 → 属音の保続')
    expo(P, f, S1, L1, 'ASBT', E)
    P.set_harms(f + 8, [['Gm', 'Gm', 'C7', 'C7'], ['F', 'F', 'A7', 'A7']])                    # エピソード
    E = []; entry(P, f + 10, 'S', invert(S1), 0, L1 + ' (反行)', E); entry(P, f + 12, 'T', invert(S1), 0, L1 + ' (反行)', E)
    harm_from_entries(P, f + 10, f + 14, E)
    E = []; entry(P, f + 14, 'A', S1, 5, L1 + ' (下属調)', E)
    entry(P, f + 16, 'S', S1, 0, L1 + ' ストレッタ', E); entry(P, f + 17, 'T', S1, 0, L1 + ' ストレッタ', E)
    harm_from_entries(P, f + 14, f + 19, E)
    E = []; entry(P, f + 19, 'B', augment(S1), 0, L1 + ' (拡大)', E)
    harm_from_entries(P, f + 19, f + 23, E)
    E = []; entry(P, f + 23, 'S', S1, 0, L1, E)
    P.place('B', f + 23, [(4, 45), (4, 45)], 0, '属音の保続')                                   # 属音 ラ の保続
    P.set_harms(f + 23, [['A7'] * 4, ['A7'] * 4, ['Dm'] * 4]); P.hold.add(f + 25)
    for k in range(SEC1): P.dyn[f + k] = 0.8 + 0.3 * k / SEC1; MOV[f + k] = 1
    HN_BARS.update(range(f + 19, f + 26)); TP.extend([(f, 38, 4, 0.5), (f + 19, 38, 2, 0.4), (f + 23, 33, 8, 0.45)])
    # ---------------- Sectio II — 第 2 主題 (駆け足)
    g = F2; E = []
    P.section(g, 'Sectio II — Soggetto II 〈piano_solo_8x, 駆け足〉', '第 2 主題 (8 分音符) の 4 声の提示 — 木管が加わる → エピソード → 第 1 主題との二重フーガ (4 回) → 終止')
    expo(P, g, S2, L2, 'TABS', E)
    P.set_harms(g + 8, [['Bb', 'Bb', 'F', 'F'], ['Gm', 'Gm', 'A7', 'A7']])
    E = []
    entry(P, g + 10, 'S', S1, 0, L1, E); entry(P, g + 10, 'T', S2, 0, L2, E)                   # 二重 1: I (S) + II (T)
    entry(P, g + 12, 'B', S1, 0, L1, E); entry(P, g + 12, 'A', S2, 0, L2, E)                   # 二重 2: I (B) + II (A)
    entry(P, g + 14, 'T', invert(S1), 0, L1 + ' (反行)', E); entry(P, g + 14, 'S', S2, 7, L2 + ' 答唱', E)   # 二重 3
    entry(P, g + 16, 'A', S1, 0, L1, E); entry(P, g + 16, 'B', S2, 0, L2, E)                   # 二重 4: I (A) + II (B)
    harm_from_entries(P, g + 10, g + 18, E)
    P.set_harms(g + 18, [['Gm', 'Gm', 'Em7b5', 'Em7b5'], ['A7', 'A7', 'A7', 'A7']])
    E = []; entry(P, g + 20, 'S', S2, 0, L2, E); entry(P, g + 20, 'B', S1, 0, L1, E)
    harm_from_entries(P, g + 20, g + 22, E)
    for q in range(2): P.harm[(g + 21) * BPB + 2 + q] = 'A7'
    for k in range(SEC2): P.dyn[g + k] = 0.85 + 0.35 * k / SEC2; P.det[g + k] = 0.9; MOV[g + k] = 2
    TP.extend([(g, 38, 4, 0.5), (g + 10, 38, 1, 0.4), (g + 16, 38, 1, 0.45), (g + 20, 33, 2, 0.5), (g + 21, 38, 2, 0.55)])
    # ---------------- Sectio III — B-A-C-H → 三重フーガ → 途切れる
    h = F3; E = []
    P.section(h, 'Sectio III — B-A-C-H · Fuga a tre soggetti', 'バッハの署名 B-A-C-H を 4 声で提示 (金管) → 3 つの主題を同時に重ねる三重フーガ → 低弦の拡大の上で → 3 度目の重なりの途中で楽譜が途切れる')
    expo(P, h, S3, L3, 'BTAS', E)
    E = []                                                                                    # 三重 1: I (S) + II (T) + B-A-C-H (A)
    entry(P, h + 8, 'S', S1, 0, L1, E); entry(P, h + 8, 'T', S2, 0, L2, E); entry(P, h + 8, 'A', S3, 0, L3, E)
    entry(P, h + 10, 'A', S1, 0, L1, E); entry(P, h + 10, 'S', S2, 0, L2, E); entry(P, h + 10, 'B', S3, 0, L3, E)   # 三重 2
    harm_from_entries(P, h + 8, h + 12, E)
    E = []                                                                                    # 拡大の上で: I 拡大 (B) + II (S) + B-A-C-H (T) → B-A-C-H (S) + II 答唱 (A)
    entry(P, h + 12, 'B', augment(S1), 0, L1 + ' (拡大)', E); entry(P, h + 12, 'S', S2, 0, L2, E); entry(P, h + 12, 'T', S3, 0, L3, E)
    entry(P, h + 14, 'S', S3, 0, L3, E); entry(P, h + 14, 'A', S2, 7, L2 + ' 答唱', E)
    harm_from_entries(P, h + 12, h + 16, E)
    E = []                                                                                    # 三重 3 (途切れる): I (S) + II (A) + B-A-C-H (T)
    entry(P, h + 16, 'S', S1, 0, L1, E); entry(P, h + 16, 'A', S2, 0, L2, E); entry(P, h + 16, 'T', S3, 0, L3, E)
    harm_from_entries(P, h + 16, h + 18, E)
    CUT = (h + 17) * BPB + 1                                                                  # 楽譜が途切れる: 2 小節目の 2 拍目
    for v in VOICES: P.rest_bars(v, h + 18, TOTAL)
    for k in range((h + 18) * BPB, TOTAL * BPB): P.harm[k] = 'Dm'
    for k in range(SEC3): P.dyn[h + k] = 1.2 + 0.2 * min(1.0, k / 8.0); MOV[h + k] = 3
    HN_BARS.update(range(h, h + 18))
    TP.extend([(h, 38, 4, 0.6)] + [(h + 8 + k, 38 if k % 2 == 0 else 33, 1, 0.5) for k in range(9)])
    # ---------------- Epilogo
    P.section(E0, 'Epilogo — piano_solo_8x (実音)', '沈黙のあと、piano_solo_8x の実音だけが戻って消えていく (2250 秒から、+5 でニ短調に)')
    for k in range(E0, TOTAL): MOV[k] = 4
    return P

def post(P, events, ex):
    """管弦楽法: 弦 (S/A/T/B) は synth 側。木管は主題の入りを重ね、ホルンは和音を支え、金管は Sectio III、ティンパニは節目に。途切れた後は何も鳴らない"""
    for v in VOICES:
        if CUT is not None: events[v] = [(s, min(d, CUT - s), m, lab) for s, d, m, lab in events[v] if s < CUT]
        for s, d, m, lab in events[v]:
            bar = int(s // BPB); mov = MOV.get(bar, 1); dyn = P.dyn.get(bar, 1.0)
            if not lab or lab == '属音の保続': continue
            if v == 'S' and mov >= 2: add('FL', s, d, m + 12 if m < 72 else m, 0.38 * dyn)
            if v == 'A' and (mov >= 2 or '反行' in lab or '下属調' in lab): add('WW', s, d, m, 0.42 * dyn)
            if v == 'T' and mov >= 2: add('CL', s, d, m, 0.4 * dyn)
            if v == 'B' and ('拡大' in lab or mov == 3): add('HN', s, d, m + 12 if m < 48 else m, 0.42 * dyn)
            if mov == 3 and v in 'SA' and (lab.startswith('B-A-C-H') or lab.startswith('主題 I ')): add('TR', s, d, m if 58 <= m <= 82 else m - 12, 0.4 * dyn)
            if mov == 3 and v in 'TB' and lab.startswith('B-A-C-H'): add('TB', s, d, m, 0.45 * dyn)
    for bar in HN_BARS:                                                                        # ホルン: 根音と 5 度
        dyn = P.dyn.get(bar, 1.0)
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half]); root = 48 + c['root']
            add('HN', bar * BPB + half, 2.2, root, 0.28 * dyn); add('HN', bar * BPB + half, 2.2, root + 7, 0.22 * dyn)
    for bar, m, dbeats, g in TP: add('TP', bar * BPB, dbeats, m, g)
    if CUT is not None:
        ex[:] = [e for e in ex if e['beat'] < CUT]
        for e in ex: e['dbeats'] = min(e['dbeats'], CUT - e['beat'])
    # Prologo / Epilogo: piano_solo_8x の実音 (速さは変えず +5 に)、低弦の レ
    ex.append(dict(v='REC', beat=0, dbeats=PRO * BPB, m=0, gain=4.0, label=None, src=BG, off=2186.0, fin=2.0, fout=8.0, pshift=5, rid='piano_solo_8x.wav',
                   tag='piano_solo_8x — 2186 秒から (+5、主題 I を採った所)'))
    add('CB', 4 * BPB, 4 * BPB, 38, 0.3); add('VC', 5 * BPB, 3 * BPB, 50, 0.2); add('TP', 7 * BPB, 4, 38, 0.4)
    ex.append(dict(v='REC', beat=E0 * BPB, dbeats=EPI * BPB, m=0, gain=3.6, label=None, src=BG, off=2250.0, fin=1.5, fout=14.0, pshift=5, rid='piano_solo_8x.wav',
                   tag='piano_solo_8x — 2250 秒から (+5) — 実音だけが残って消える'))
    add('CB', (E0 + 2) * BPB, 6 * BPB, 38, 0.2)

META = {
    'style': 'symphony', 'humanize': True, 'pause_bar': F3 + 17,
    'title': 'Requiem BADA — XCII · Contrapunctus XIV sinfonico',
    'subtitle': 'piano_solo_8x を Contrapunctus XIV の主題にして、管弦楽で — 第 1・第 2 主題 ← piano_solo_8x の採譜、第 3 主題 = B-A-C-H (ニ短調, ♩=60)',
    'footer': ['Prologo (piano_solo_8x の実音) → Sectio I: 主題 I の提示・反行・ストレッタ・拡大 → Sectio II: 主題 II の提示、I+II の二重フーガ → Sectio III: B-A-C-H、三重フーガ → 途切れる → Epilogo (実音)',
               '管弦楽: 弦 5 部 (Vn I / Vn II / Va / Vc+Cb) · Fl · Ob · Cl · Hn · Tp · Tb · Timp (すべて合成)。声なし。'],
}

if __name__ == '__main__':
    compose.main(OUT, seed=92, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']), 'duration', d['duration'])
