#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Long Distance (不整脈の旅)
  Cor — Mantra から倍音 (倍音シンセ・倍音ドローン) と心臓の鼓動を外し、ロックバンドのドラムを「不整脈流」の
  洗脳的なビートにして、レクイエムとフーガを、作曲者が提出した 7 曲を長い旅としてたどる曲に作り換える。
    - 7 曲をアルバム順に 1 曲 = 1 区間でたどる。区間の長さは原曲の長さに比例 (合計 31 分半 → 約 8 分)、
      調は原曲の主音に、テンポは原曲のテンポ (120 を超える曲はその半分) に合わせる
    - 各区間はその曲から採った素材を中心に: LOVELESS = Introitus と B-A-D-A のマントラ、トラック 8 = ため息の嘆きのバス、
      MOTHER = 主題 I、トラック 17 = 音階のエピソード、トラック 18 = 主題 II、録音 090146 = 二重結合と B-A-D-A、
      録音 090933 = 三重フーガの終結 (主題 III の後半はこの録音から)
    - ドラム: 区間ごとに 1 つの「不整脈」の型 (期外収縮・房室ブロック・二段脈・心房細動・頻脈発作・位相のずれ・心停止)。
      不規則な型そのものが毎回まったく同じに繰り返されるので、崩れたループが洗脳的に回り続ける。
      脈が抜ける所ではベースも一緒に止まる
  全体をニ短調で作曲し、出力の段階で区間ごとに原曲の主音へ移調する。
"""
import sys, json
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D
import compose_heart as H

DIES_IRAE = mat(('F4',2),('E4',1),('F4',1),('D4',2),('E4',1),('C4',1),('D4',2),('D4',2),
                ('F4',2),('F4',1),('E4',1),('F4',2),('D4',2),('E4',1),('C4',1),('D4',4))
BADA, REQUIEM_CHANT, DRONE_BAR, MANTRA_PROG = H.BADA, H.REQUIEM_CHANT, H.DRONE_BAR, H.MANTRA_PROG

# (id, 曲名, 原曲の長さ 秒, 主音への移調, ♩, 小節数, 素材, 不整脈の型, 素材の説明)
SONGS = [
    ('loveless', '01 LOVELESS', 336.0, 5, 161.5 / 2, 30, 'intro', 'pvc', 'Introitus (Requiem aeternam · Dies irae) → B-A-D-A のマントラ'),
    ('t08', 'トラック 8', 249.2, -5, 99.4, 27, 'lament', 'block', '嘆きのバス ×9 (トラック 8 のため息 F–E)'),
    ('mother', '10 MOTHER', 319.0, 2, 68.0, 22, (0, 22), 'bigeminy', 'フーガ — 主題 I 〈MOTHER〉の提示'),
    ('t17', 'トラック 17', 274.9, -5, 172.3 / 2, 22, (22, 44), 'afib', 'フーガ — 上行音階のエピソードと下属調の主題 I'),
    ('t18', 'トラック 18', 149.1, 0, 123.0 / 2, 10, (44, 54), 'tachy', 'フーガ — 主題 II 〈トラック18〉の提示'),
    ('r146', '録音 20260922_090146', 455.5, 5, 95.7, 49, (54, 103), 'phase', 'フーガ — 主題 I+II の二重結合 ×3 → 主題 III 〈B-A-D-A〉'),
    ('r933', '録音 20260922_090933', 105.8, -3, 63.0, 9, (121, 130), 'arrest', '三重フーガの終結 → 総休止 → ピカルディ終止'),
]
ARR = {
    'pvc': '期外収縮 — 早すぎる一打のあと 1 拍抜ける',
    'block': '房室ブロック — 3 小節ごとに脈が抜ける',
    'bigeminy': '二段脈 — 短い・長いの対が続く',
    'afib': '心房細動 — 不規則に不規則 (同じ不規則が繰り返す)',
    'tachy': '頻脈発作 — 各小節の終わりに 16 分の連打',
    'phase': '位相のずれ — キックは 5 つおき、スネアは 4 拍子',
    'arrest': '心停止 → 再開 — 総休止で全部止まり、打ち直して消える',
}
KEYJP = {0: 'ニ', 5: 'ト', -5: 'イ', 2: 'ホ', -3: 'ロ'}
MAJOR = {'loveless', 'r146'}                         # 原曲が長調の曲 (主音を合わせて短調で)
HALF = {'loveless', 't17', 't18'}                     # 原曲が速い曲はテンポを半分に (ドラムは細かく刻む)
START = []
s0 = 0
for sg in SONGS: START.append(s0); s0 += sg[5]
TOTAL = s0
PAUSE_BAR = START[6] + (126 - 121)
extras = []

def add(v, beat, dbeats, midi, gain, label=None, **kw):
    e = {'v': v, 'beat': beat, 'dbeats': dbeats, 'm': midi, 'gain': gain, 'label': label}
    e.update(kw); extras.append(e)
def bell(bar, beat, midi=n('D3'), gain=1.0, dbeats=8): add('X', bar * BPB + beat, dbeats, midi, gain)
def drone(bar0, bar1, midi=n('D1'), gain=1.0): add('D', bar0 * BPB, (bar1 - bar0) * BPB, midi, gain)
def song_of(bar):
    for i in range(len(SONGS) - 1, -1, -1):
        if bar >= START[i]: return i
def mmss(s): return '%d:%02d' % (s // 60, s % 60)

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    for i, (sid, name, dur, semis, bpm, nb, mat_, arr, desc) in enumerate(SONGS):
        b0 = START[i]
        for k in range(nb): P.tempo[b0 + k] = round(bpm, 2); P.dyn[b0 + k] = 0.85
        if mat_ == 'intro':
            P.set_harms(b0, [['Dm']] * 4 + [['Gm'], ['Dm'], ['Bb'], ['A']])
            for v in VOICES: P.rest_bars(v, b0, b0 + 2)
            P.place('S', b0 + 2, REQUIEM_CHANT, 0, 'Requiem aeternam'); P.place('A', b0 + 6, BADA, 0, 'B-A-D-A')
            P.rest_bars('A', b0 + 2, b0 + 6); P.rest_bars('T', b0 + 2, b0 + 4)
            for bar in range(b0 + 2, b0 + 8): P.place('B', bar, DRONE_BAR, 0, None)
            for k in range(8): P.dyn[b0 + k] = 0.55 + 0.04 * k
            drone(b0 + 2, b0 + 8, gain=0.8); bell(b0 + 2, 0, gain=0.8)
            m0 = b0 + 8
            for k in range((nb - 8) // 2):                      # B-A-D-A のマントラ + テノールの Dies irae
                b = m0 + 2 * k
                P.set_harms(b, MANTRA_PROG)
                v = ('A', 'S')[k % 2]
                P.place(v, b, BADA, {'S': 12, 'A': 0}[v], 'B-A-D-A' if k % 4 == 0 else None)
                for j in range(2): P.place('B', b + j, DRONE_BAR, 0, None)
                bell(b, 0, gain=0.5)
            for b in (m0 + 2, m0 + 10, m0 + 18):
                if b + 4 <= b0 + nb: P.place('T', b, DIES_IRAE, -12, 'Dies irae' if b == m0 + 2 else None)
            P.hold.update(range(b0, b0 + nb))
            drone(m0, b0 + nb, gain=0.6)
        elif mat_ == 'lament':
            D.lament(P, b0, nb // 3, label=True, dyn=lambda c: 0.72 + 0.02 * c)
            P.rest_bars('S', b0, b0 + 3)
            drone(b0, b0 + nb, gain=0.5)
        else:
            f0, f1 = mat_
            copy_bars(T, P, f0, f1, b0)
        P.sections = [s for s in P.sections if s[0] != b0]
        half = ' (原曲 ♩≈%d の半分)' % round(bpm * 2) if sid in HALF else ''
        P.section(b0, '%s %s — %s' % ('①②③④⑤⑥⑦'[i], name, desc),
                  '%s短調%s · ♩=%d%s · 原曲 %s → %s ／ 不整脈: %s' % (KEYJP[semis], ' (原曲は%s長調)' % KEYJP[semis] if sid in MAJOR else '', round(bpm), half,
                                                          mmss(dur), mmss(nb * 240 / bpm), ARR[arr]))
    P.sections = [s for s in P.sections if s[0] in START]
    return P

# ---------------------------------------------------------------- 不整脈のドラム
def loop_events(arr, bar_in, bar):
    """区間の型: その小節の (16 分の位置, 楽器, 強さ) の並び と、脈が抜ける 16 分の範囲 (ベースも止める)"""
    ev, drop = [], []
    H8 = [(s, 'hatc', 0.26 if s % 4 == 0 else 0.16) for s in range(0, 16, 2)]
    H16 = [(s, 'hatc', (0.26, 0.1, 0.18, 0.1)[s % 4]) for s in range(16)]
    if arr == 'pvc':                                           # 2 小節ループ: 2 小節目に早すぎる一打 → 代償性の休止
        if bar_in % 2 == 0:
            ev = [(0, 'kick', 0.95), (8, 'kick', 0.85), (10, 'kick', 0.6), (4, 'snare', 0.8), (12, 'snare', 0.85)] + H8
        else:
            ev = [(0, 'kick', 0.95), (4, 'snare', 0.8), (7, 'kick', 0.9), (9, 'snare', 0.9)] + [h for h in H8 if h[0] < 10]
            drop = [(10, 16)]
    elif arr == 'block':                                       # 嘆きのバス 3 小節ごと: 1 小節目は正常、2 小節目は脈が 1 つ抜け、3 小節目は 2 つ抜ける
        c = bar_in % 3
        ev = [(0, 'kick', 0.95), (8, 'snare', 0.85)] + [(s, 'ride', 0.24) for s in (0, 4, 8, 12)]
        if c == 1: ev = [e for e in ev if e[0] < 8]; drop = [(8, 16)]
        if c == 2: ev = [(0, 'kick', 0.95), (3, 'kick', 0.7), (6, 'snare', 0.9)]; drop = [(8, 16)]
    elif arr == 'bigeminy':                                    # 短い・長い の対 (キックの対 + 遅れて入るスネア)、3 つ刻みのハイハット
        ev = [(0, 'kick', 0.95), (3, 'kick', 0.7), (8, 'kick', 0.9), (11, 'kick', 0.65), (6, 'snare', 0.85), (14, 'snare', 0.85)]
        ev += [(s, 'hatc', 0.28 if s % 3 == 0 else 0.1) for s in range(16)]
    elif arr == 'afib':                                        # 不規則に不規則 — ただし 2 小節で同じ並びが戻る
        K = [[0, 5, 7, 13], [2, 5, 11, 14]][bar_in % 2]; S = [[4, 11], [4, 9, 15]][bar_in % 2]
        G = [0.3, 0.08, 0.2, 0.14, 0.1, 0.26, 0.12, 0.18, 0.08, 0.22, 0.1, 0.16, 0.28, 0.1, 0.14, 0.2]
        ev = [(s, 'kick', 0.9) for s in K] + [(s, 'snare', 0.8) for s in S] + [(s, 'hatc', G[(s + 5 * (bar_in % 2)) % 16]) for s in range(16)]
    elif arr == 'tachy':                                       # 8 分のキックに、小節の終わりで 16 分の連打 (発作) が差し込む
        ev = [(s, 'kick', 0.8) for s in range(0, 12, 2)] + [(s, 'kick', 0.7 + 0.05 * (s - 12)) for s in range(12, 16)]
        ev += [(4, 'snare', 0.85), (12, 'snare', 0.9)] + H16
        if bar_in % 2 == 1: ev += [(s, 'tom', 0.5) for s in (13, 14, 15)]
    elif arr == 'phase':                                       # キックは 5 つおき (5 小節で一巡)、スネアとハイハットは 4 拍子のまま
        base = bar_in * 16
        ev = [(s, 'kick', 0.9 if (base + s) % 20 == 0 else 0.75) for s in range(16) if (base + s) % 5 == 0]
        ev += [(4, 'snare', 0.8), (12, 'snare', 0.85)] + H8 + [(14, 'hato', 0.2)]
        if (base // 16) % 5 == 4: ev += [(s, 'tom', 0.45) for s in (10, 13)]
    elif arr == 'arrest':
        if bar < PAUSE_BAR:
            ev = [(0, 'kick', 1.0), (8, 'kick', 0.85), (10, 'kick', 0.6), (4, 'snare', 0.9), (12, 'snare', 0.9)] + H16
            if bar_in % 2 == 1: ev = [e for e in ev if e[0] < 10] + [(7, 'kick', 0.9), (9, 'snare', 0.9)]; drop = [(10, 16)]
        elif bar == PAUSE_BAR:                                   # 心停止: 前半 2 拍は完全な無音
            ev = [(8, 'crash', 0.95), (8, 'kick', 1.0), (12, 'snare', 0.9), (14, 'kick', 0.8)]; drop = [(0, 8)]
        else:                                                    # 打ち直した後、脈が 1 つずつ抜けて消える
            k = bar - PAUSE_BAR
            ev = [(0, 'kick', 0.9 - 0.15 * k), (0, 'crash', 0.6 if k == 1 else 0.0)]
            if k == 1: ev += [(8, 'snare', 0.7), (11, 'kick', 0.6)]
            if k == 2: ev += [(8, 'kick', 0.5)]
            drop = [(4, 16)] if k >= 2 else [(12, 16)]
    return [e for e in ev if e[2] > 0], drop

def post(P, events, ex):
    for bar in range(TOTAL):
        i = song_of(bar); arr = SONGS[i][7]; b0 = bar * BPB; bar_in = bar - START[i]
        ev, drop = loop_events(arr, bar_in, bar)
        if i == 0 and bar_in < 6: ev = [e for e in ev if e[1] in ('kick', 'hatc')]   # 冒頭は崩れたキックとハイハットだけで始まる
        for s16, kind, g in ev:
            m = {'tom': 45}.get(kind, 36 if kind == 'kick' else 60)
            pan = {'hatc': 0.25, 'hato': 0.25, 'ride': 0.35, 'crash': -0.3, 'tom': 0.15}.get(kind, 0.0)
            add('DR', b0 + s16 / 4.0, 0.25, m, g, None, kind=kind, pan=pan)
        if bar_in == 0 and i > 0: add('DR', b0, 0.25, 60, 0.7, SONGS[i][1], kind='crash', pan=-0.3)
        # ---------- シンセ・ベース: 8 分で根音、脈が抜ける所では一緒に止まる。嘆きのバスと終止は 2 分音符
        if i == 0 and bar_in < 4: continue
        dropped = lambda s: any(a <= s < b for a, b in drop)
        c0 = chord(P.harm[b0]); c2 = chord(P.harm[b0 + 2])
        if arr == 'block' or (arr == 'arrest' and bar > PAUSE_BAR):
            for half, c in ((0, c0), (2, c2)):
                if not dropped(half * 4): add('SB', b0 + half, 1.9, 36 + (c['bass'] - 36) % 12, 0.5)
        else:
            for s in range(0, 16, 2):
                if dropped(s): continue
                c = c0 if s < 8 else c2
                add('SB', b0 + s / 4.0, 0.45, 36 + (c['bass'] - 36) % 12, 0.55 if s % 4 == 0 else 0.4)

META = {
    'style': 'arrhythmia', 'vowel': 'o', 'band_gain': 2.4,
    'title': 'Requiem BADA — Long Distance',
    'subtitle': '不整脈の旅 — 提出された 7 曲をたどるレクイエムとフーガ (区間の長さ・主音・テンポ = 原曲)',
    'footer': ['① LOVELESS → ② トラック 8 → ③ MOTHER → ④ トラック 17 → ⑤ トラック 18 → ⑥ 録音 090146 → ⑦ 録音 090933 (原曲 合計 31:29 → 約 8 分)',
               'ドラム ← 区間ごとの不整脈: 期外収縮 · 房室ブロック · 二段脈 · 心房細動 · 頻脈発作 · 位相のずれ · 心停止 — 不規則な型が毎回同じに繰り返す',
               '合唱 (オ)+オルガンのレクイエムとフーガ · ロックのドラム · シンセ・ベース (脈が抜ける所で一緒に止まる) · 弔鐘 · ドローン'],
}

def transpose_sections(path):
    """区間ごとに原曲の主音へ移調 (音符・重ね・和声表示)。ドラムは音高を変えない。"""
    d = json.load(open(path))
    semis = lambda beat: SONGS[song_of(int(beat // BPB))][3]
    for nt in d['notes']: nt['m'] += semis(nt['beat'])
    for e in d['extras']:
        if e['v'] != 'DR': e['m'] += semis(e['beat'])
    d['harm'] = [transpose_h([[h]], semis(b))[0][0] for b, h in enumerate(d['harm'])]
    json.dump(d, open(path, 'w'), ensure_ascii=False, indent=0)
    print('transposed per song:', [(sg[1], sg[3]) for sg in SONGS], 'duration %.1f s' % d['duration'])

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_journey.json'
    compose.main(out, seed=21, bpm=80, builder=build, meta=META, extras=extras, post=post)
    transpose_sections(out)
