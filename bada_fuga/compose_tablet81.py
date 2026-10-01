#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXI · Requiem 9/28 (LXXX を圧縮して重低音の土台に、9/28 の歌を想像して作曲し、その代表の旋律を 8 倍に伸ばして強調する)
  9/28 17:46 の録音 (低い声で歌った 2 分 40 秒、変ロ短調) から、いちばん多く歌われた節を代表の旋律 (主題) に —
    変ロ短調で ラ♭・シ♭・シ♭・ファ・ソ♭・ラ・シ♭ (8 拍): シ♭ まで上がってファへ落ち、ソ♭・ラ・シ♭ と半音で上り直す嘆きの節。
  土台 (ベース): LXXX (7 分 4 秒のフーガ) を
    - 時間で圧縮: 2 倍の速さに (424 秒 → 212 秒)
    - 高低音を圧縮: すべての音を シ♭ 1〜シ♭ 3 の 2 オクターヴに折りたたむ (同じ時刻・同じ音は 1 つに)、6 半音動かして変ロ短調に — 暗く低く小さく
  作曲 (圧縮した土台と同じ 212 秒 = 53 小節、♩=60、変ロ短調): 9/28 の主題の和音 (1 拍ごと) を 8 倍に伸ばした和声の上で、
    主題 (1 倍) がアルト・テノールに次々と入り (入るごとに終わりの音がその時の和音の根音に着くように)、ほかの声部が対位法で動く。
  代表の強調: 9/28 の主題を 8 倍に伸ばして (16 小節)、3 回 — ソプラノの音域 (いちばん上でもシ♭ 4 のあたり) とオクターヴ下で、
    2 拍ごとに打ち直して大きく。最後は変格終止で変ロ長調の和音。
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet81.py <bank74.json> <score_tablet80.json> [score_tablet81.json]
"""
import sys, json
import numpy as np
from compose import *
import compose
import compose_tablet as CT
import compose_tablet48 as K
import compose_tablet63 as LXIII

SRC80 = json.load(open(sys.argv[2]))
OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet81.json'
BBM = -4                                           # 変ロ短調 (ニ短調から)
# 9/28 の代表の節 (エンジンのニ短調で): ド・レ・レ・ラ・シ♭・ド#・レ = 変ロ短調で ラ♭・シ♭・シ♭・ファ・ソ♭・ラ・シ♭
THEME = [(1, n('C5')), (1, n('D5')), (1, n('D5')), (1, n('A4')), (2, n('Bb4')), (1, n('C#5')), (1, n('D5'))]
VOICE_SRC = {'S': '20260924_085314', 'A': '20260923_080918', 'T': '20260925_124643', 'B': '20260925_130431'}
DYNK = 1.3
BARS = 53                                          # 圧縮した土台 (212 秒) と同じ
AUG = []                                           # 8 倍の主題 (打ち直しで鳴らす): (開始拍, 長さ拍, 音高)

def build():
    Hb = ['F', 'Dm', 'Dm', 'Dm', 'Gm', 'Gm', 'A7', 'Dm']                                 # 主題の 1 拍ごとの和音 (それぞれの音を含み、終わりは主和音)
    print('theme harmony', Hb)
    P = Piece(BARS)
    for k in range(BARS): P.tempo[k] = 60; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, BARS, BBM, VOICE_SRC, {}))
    P.section(0, '9/28 の主題 ×8 — 一回目 (変ロ短調)', 'LXXX を圧縮した重低音の土台の上で、9/28 の代表の節を 8 倍に伸ばし、1 倍の主題がアルト・テノールに入る')
    P.set_harms(0, [['Dm'] * 4])
    for r, f in enumerate((1, 17, 33)):
        if r: P.section(f, '9/28 の主題 ×8 — %s回目' % ('二' if r == 1 else '三'), '代表の節がもう一度 8 倍で — 1 倍の主題が次々と入り、%s' % ('土台のフーガと重なる' if r == 1 else '最後の終止へ'))
        for i, c in enumerate(Hb):
            for q in range(8): P.harm[f * BPB + i * 8 + q] = c
        t = f * BPB
        for d, m in THEME: AUG.append((t, d * 8, m)); t += d * 8
        P.rest_bars('S', f, f + 16)
        # 1 倍の主題: 2 小節ごとにアルト・テノール交互、終わりの音 (レ) がそのときの和音の根音に着く高さで
        for k in range(8):
            bar = f + 2 * k; v = 'A' if k % 2 == 0 else 'T'
            root = chord(P.harm[bar * BPB + 7] or 'Dm')['root']
            cen = 62 if v == 'A' else 55
            tr = min((x for x in range(-24, 13) if (74 + x) % 12 == root), key=lambda x: abs(74 + x - 4 - cen))
            P.place(v, bar, [(d, m + tr) for d, m in THEME], 0, '9/28 の主題 ×1' if k == 0 and r == 0 else None)
        for k in range(16): P.dyn[f + k] = DYNK * (0.62 + 0.18 * np.sin(np.pi * k / 15))
    f = 49; P.section(f, 'Amen — 変格終止 (変ロ長調)', 'iv → V → I: 変ロ長調の和音で閉じる')
    P.set_harms(f, [['Gm'] * 4, ['A7'] * 4, ['D'] * 4, ['D'] * 4])
    P.place('S', f, [(4, n('Bb4')), (4, n('A4')), (8, n('A4'))], 0, 'Amen')
    for k in range(4): P.dyn[f + k] = DYNK * (0.6 - 0.08 * k)
    LXIII.ARP.append((f, f + 3, 0.08, BBM))
    return P

def base_layer(d):
    """LXXX を 2 倍の速さに、6 半音動かし、シ♭ 1〜シ♭ 3 に折りたたむ"""
    out, seen = [], set()
    for x in SRC80['notes']:
        m = x['m'] + 6
        while m > 58: m -= 12
        while m < 34: m += 12
        t = round(x['t'] / 2.0, 2)
        if t >= BARS * 4 - 0.5 or (t, m) in seen: continue
        seen.add((t, m))
        out.append(dict(v='PF', t=t, d=round(max(0.2, x['d'] / 2.0) + 0.4, 3), m=m, gain=round(0.075 * x.get('dyn', 1.0), 4), rid=x.get('src', ''), rel=1.0,
                        beat=t, dbeats=round(x['d'] / 2.0, 3), label=None, layer='base'))
    return out

def aug_layer():
    """8 倍の主題: 2 拍ごとに打ち直し (頭を強く、息をするように)、オクターヴ下を重ねる — 変ロ短調へ移して"""
    out = []
    for t0, L, m in AUG:
        n_ = int(round(L / 2))
        for i in range(n_):
            amp = 1.0 if i == 0 else 0.62 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1))
            for oc, g in ((0, 0.6), (-12, 0.4)):
                out.append(dict(v='PF', t=t0 + 2 * i, d=2.9, m=m + BBM + oc, gain=round(g * amp, 4), rid=VOICE_SRC['S'], rel=1.0,
                                beat=t0 + 2 * i, dbeats=2.0, label=None, layer='aug'))
    return out

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': list(VOICE_SRC.values()), 'piano_decay': 2.6, 'reverb': [6.5, 2.4, 0.5],
    'title': 'Requiem BADA — LXXXI · Requiem 9/28',
    'subtitle': 'LXXX を圧縮した重低音の土台に、9/28 の歌を想像して — その代表の節を 8 倍に伸ばして強調する (変ロ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['9/28 の主題 ×8 を 3 回 → Amen (変ロ長調)。土台は LXXX を 2 倍の速さ・シ♭ 1〜シ♭ 3 に圧縮したもの',
               '代表の節: ラ♭・シ♭・シ♭・ファ・ソ♭・ラ・シ♭ (9/28 の録音でいちばん多く歌われた節)。すべてピアノの実音。'],
}

if __name__ == '__main__':
    compose.main(OUT, seed=181, bpm=60, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(OUT)
    K.BPM = 60; K.fix_voices(OUT)
    d = json.load(open(OUT)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * (1.1 if n_.get('label') else 0.7), 4)        # 対位法は少し後ろへ、代表の節を前に
    d['extras'] += base_layer(d) + aug_layer()
    d['entries'] += [dict(t=4.0, label='9/28 の代表の節 ×8 (強調)', v='S'), dict(t=0.02, label='土台: LXXX を圧縮 (2 倍の速さ・低音域)', v='B')]
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras'] if e['v'] == 'PF']
    print('duration', round(d['duration'], 1), 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
