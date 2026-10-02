#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Vox · Fuga senza voce (声のないフーガ — Vox から歌声 (喘ぎ声) を消して、フーガの雰囲気を醸し出す曲に)
  Vox (compose_vox.py) の調・主題 (歌声 1/8 19:33 の伸ばした音から作った 8 拍の主題)・鼓動・持続音・オスティナート・B-A-D-A はそのまま、
  歌声のフレーズ (REC) と歌声のサンプラー (VOX) をすべて外し、4 声はすべて 9/24 のピアノ録音の 1 音で。曲全体が主題のフーガになる:
    Introitus — 主題が 1 声ずつ (バス → テノール)、持続音と ♩=60 の鼓動の上で
    Kyrie     — 4 声の提示 (A → S 答唱 → B → T 答唱) → 全音符の和音
    Mix       — ピアノ録音 9/24 11:23 の実音の上で、主題の拡大 (×2) がバスに
    Fuga      — 提示 → 反行 (S・T) → ストレッタ (4 声が 1 小節ずつ) → 拡大とストレッタの重なり (頂点)
    Sanctus   — オスティナートの上で主題と反行が交互に
    Agnus Dei — B-A-D-A を唱える合唱に、主題がソプラノで重なる
    Lux aeterna — 主題の拡大 (×2) がバスで最後に歌い、長調 (ピカルディ) の和音で安らかに
  使い方: python compose_voxfuga.py <piano_bank.json> <voice_bank.json> [score_voxfuga.json]
"""
import sys, json, math
from compose import *
import compose
import compose_vox as V
import compose_heart as H
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet5 as T5

add = CT.add; BPM = V.BPM; SEMIS = V.SEMIS; PIANO = V.PIANO; PIANO_RIDS = V.PIANO_RIDS
choir = {v: PIANO for v in VOICES}
TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 60}
SUBJ_R = []

def fit(v, mat_, tr):
    if max(m for _, m in mat_) + tr > TOP[v]: tr -= 12
    if min(m for _, m in mat_) + tr < RANGE[v][0]: tr += 12
    return tr
def entry(P, bar, v, mat_, tr0, label, E, beat=0):
    tr = fit(v, mat_, tr0); P.place(v, bar, mat_, tr, label or '', beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat_]))
def invert(mat_): m0 = mat_[0][1]; return [(d, 2 * m0 - m) for d, m in mat_]
def augment(mat_, k=2): return [(k * d, m) for d, m in mat_]
def rest_others(P, b0, b1, keep):
    for v in VOICES:
        if v not in keep: P.rest_bars(v, b0, b1)

def build():
    PH = V.pick_phrases(); queue = [(r, p) for r in V.VOICE for p in PH[r]]
    r, p = max(queue, key=lambda x: (len({int(round(m)) for _, _, m in V.voice_notes(*x)}), len(V.voice_notes(*x))))
    subj = V.voice_subject(r, p); T5.SUBJ[r] = (subj, CT.harmonize(subj)); SUBJ_R.append(r)
    lab = '主題 (声 %s)' % V.hmv(r); pr = PIANO_RIDS[0]
    total = 6 + 10 + 10 + 20 + 8 + 8 + 8
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.7
    # ---------------- Introitus
    b = 0
    P.section(b, 'Introitus — 主題がひとりで', '歌声から作った主題が、ピアノ録音の持続音と ♩=60 の柔らかい鼓動の上で、バス → テノールと 1 声ずつ — 鼓動は最後まで止まらない')
    P.set_harms(b, [['Dm']] * 6); E = []
    entry(P, b + 1, 'B', subj, -24, lab, E); entry(P, b + 3, 'T', subj, -12, lab, E)
    rest_others(P, b, b + 6, 'BT'); P.rest_bars('B', b, b + 1); P.rest_bars('B', b + 3, b + 6); P.rest_bars('T', b, b + 3); P.rest_bars('T', b + 5, b + 6)
    T5.harm_from_entries(P, b + 1, b + 5, E)
    for k in range(6): P.dyn[b + k] = 0.55
    T2.MANTRA.append((b, b + 6, pr, ('DN', 'PK'))); CT.LAYOUT.append((b, b + 6, SEMIS, choir, {})); b += 6
    # ---------------- Kyrie: 提示
    P.section(b, 'Kyrie — 4 声の提示', '主題の提示 (A → S 答唱 → B → T 答唱) → 全音符の和音が包む')
    T5.expo(P, b, r, '')
    P.set_harms(b + 8, [['Gm', 'Gm', 'A7', 'A7'], ['Dm']]); P.hold.update((b + 8, b + 9))
    for k in range(10): P.dyn[b + k] = 0.5
    T2.MANTRA.append((b, b + 10, pr, ('PK',))); CT.LAYOUT.append((b, b + 10, SEMIS, choir, {})); b += 10
    # ---------------- Mix: ピアノ録音の実音 + 主題の拡大
    mr = PIANO_RIDS[-1]
    P.section(b, 'Mix — ピアノ録音 %s と主題の拡大' % V.hmv(mr), 'タブレットのピアノ録音をループせず実音のまま — その上で主題の拡大 (×2) がバスに 2 度')
    T5.passage(P, mr, b, 10, SEMIS, 10, fin=1.5, fout=3.0, bpm=BPM)
    E = []; entry(P, b + 1, 'B', augment(subj), -24, lab + ' 拡大 ×2', E); entry(P, b + 5, 'B', augment(subj), -24, None, E)
    rest_others(P, b, b + 10, 'B'); P.rest_bars('B', b, b + 1); P.rest_bars('B', b + 9, b + 10)
    T2.MANTRA.append((b, b + 10, pr, ('PK',))); CT.LAYOUT.append((b, b + 10, SEMIS, choir, {})); b += 10
    # ---------------- Fuga
    f = b
    P.section(f, 'Fuga — 提示 → 反行 → ストレッタ', '主題の 4 声フーガ: 提示 → 反行 (S・T) → ストレッタ (4 声が 1 小節ずつ) → 拡大の上でストレッタ (頂点)。下でオスティナートと持続音')
    T5.expo(P, f, r, '')
    E = []; entry(P, f + 8, 'S', invert(subj), 12, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(subj), -12, lab + ' (反行)', E)
    P.rest_bars('A', f + 8, f + 12); P.rest_bars('B', f + 8, f + 10); entry(P, f + 10, 'B', subj, -24, lab, E)
    T5.harm_from_entries(P, f + 8, f + 12, E)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, subj, {'S': 12, 'A': 0, 'T': -12, 'B': -24}[v], lab + ' ストレッタ' if k == 0 else None, E)
    T5.harm_from_entries(P, f + 12, f + 17, E)
    E = []; entry(P, f + 16, 'B', augment(subj), -24, lab + ' 拡大 ×2', E)
    entry(P, f + 16, 'S', subj, 12, lab + ' ストレッタ', E); entry(P, f + 17, 'A', subj, 0, None, E); entry(P, f + 18, 'T', subj, -12, None, E)
    T5.harm_from_entries(P, f + 16, f + 20, E)
    for k in range(20): P.dyn[f + k] = 0.8 + 0.3 * max(0, k - 8) / 12.0
    T2.MANTRA.append((f, f + 20, pr, ('DN', 'PK', 'OS'))); CT.LAYOUT.append((f, f + 20, SEMIS, choir, {})); b += 20
    # ---------------- Sanctus
    P.section(b, 'Sanctus — オスティナートの上で', 'ピアノ録音の音のオスティナートが同じ形を刻み続け、その上で主題と反行が交互に — 合唱が全音符で支える')
    E = []
    for k in range(4):
        v = 'AS'[k % 2]; entry(P, b + 2 * k, v, subj if k % 2 == 0 else invert(subj), {'A': 0, 'S': 12}[v], (lab if k == 0 else lab + ' (反行)') if k < 2 else None, E)
    T5.harm_from_entries(P, b, b + 8, E); P.hold.update(range(b, b + 8))
    for k in range(8): P.dyn[b + k] = 0.45
    T2.MANTRA.append((b, b + 8, pr, ('PK', 'OS'))); CT.LAYOUT.append((b, b + 8, SEMIS, choir, {})); b += 8
    # ---------------- Agnus Dei
    P.section(b, 'Agnus Dei — B-A-D-A', 'B-A-D-A を 4 回唱える合唱に、主題がソプラノで 2 度重なる')
    for k in range(4):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, H.DRONE_BAR, 0, None)
        if k % 2 == 0: add('X', bb * BPB, 8, n('D3'), 0.3)
    P.place('S', b + 1, subj, 12, lab); P.place('S', b + 5, subj, 12, None)
    P.rest_bars('S', b, b + 1); P.rest_bars('S', b + 3, b + 5); P.rest_bars('S', b + 7, b + 8)
    P.hold.update(range(b, b + 8))
    for k in range(8): P.dyn[b + k] = 0.6
    T2.MANTRA.append((b, b + 8, pr, ('DN', 'PK'))); CT.LAYOUT.append((b, b + 8, SEMIS, choir, {})); b += 8
    # ---------------- Lux aeterna
    P.section(b, 'Lux aeterna — 安らかに', '主題の拡大 (×2) がバスで最後に歌い、長調 (ピカルディ) の和音で安らかに消えていく')
    P.set_harms(b, [['Dm']] * 4); E = []; entry(P, b, 'B', augment(subj), -24, lab + ' 拡大 ×2', E); T5.harm_from_entries(P, b, b + 4, E)
    rest_others(P, b, b + 4, 'B')
    T2.MANTRA.append((b, b + 4, pr, ('DN', 'PK'))); b += 4
    P.set_harms(b, [['D']] * 4); P.hold.update(range(b, b + 4))
    P.place('S', b, mat(('F#5', 12)), 0, None); P.place('A', b, mat(('A4', 12)), 0, None); P.place('T', b, mat(('D4', 12)), 0, None); P.place('B', b, mat(('D3', 12)), 0, None)
    for v in VOICES: P.rest_bars(v, b + 3, b + 4)
    for k in range(4): P.dyn[b + k] = 0.55 - 0.08 * k
    T2.MANTRA.append((b, b + 3, pr, ('PK',))); CT.LAYOUT.append((b - 4, b + 4, SEMIS, choir, {})); b += 4
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': PIANO_RIDS,
    'title': 'Requiem BADA — Vox · Fuga senza voce',
    'subtitle': '声のないフーガ — Vox の歌声をすべて消し、歌声から作った主題だけを 4 声のフーガに (ピアノ録音の音だけ、止まらない柔らかな鼓動, イ短調, ♩=60)',
    'footer': ['Introitus (主題がひとりで) → Kyrie (提示) → Mix (ピアノ録音と拡大) → Fuga (提示 → 反行 → ストレッタ → 拡大) → Sanctus → Agnus Dei (B-A-D-A) → Lux aeterna (長調で安らかに)',
               '主題は歌声 1/8 19:33 の伸ばした音から (Vox と同じ)。歌声のフレーズ・歌声のサンプラーは使わない。4 声・持続音・オスティナート・鼓動はすべて 9/24 のピアノ録音の 1 音。'],
}

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_voxfuga.json'
    compose.main(out, seed=62, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=T2.post)
    CT.finish(out); V.fix_sources(out)
    d = json.load(open(out)); assert not any(e['v'] == 'REC' and 'voice' in str(e.get('src', '')) for e in d['extras']) and not any(nt['src'] == 'VOX' for nt in d['notes'])
    d['meta']['subtitle'] = d['meta']['subtitle'].replace('イ短調', V.NAMES[V.TONIC] + '短調')
    d['meta']['footer'][1] = d['meta']['footer'][1].replace('1/8 19:33', V.hmv(SUBJ_R[0]))
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    print('subject', SUBJ_R[0], ' '.join('%s:%g' % (name_of(m), d_) for d_, m in T5.SUBJ[SUBJ_R[0]][0]))
