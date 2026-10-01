#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXIII · Requiem e Fuga 12:50 ×4 (LXXXII の 16 倍を 4 倍にして — レクイエムとフーガ)
  録音は 8.6 秒の、ロ短調の劇的な一節 (F#7 = 属七、Gmaj7 = VI、C7、Em …)。LXXXII では 16 倍 (2 分 18 秒) に伸ばしたのを、4 倍 (34 秒) に。
  和音が 2 秒ほどで移っていくので、録音の劇の流れが聞こえる速さ。終わりはさらに 2 倍 (17 秒) に縮めて主題のストレッタ。
  主題: 録音の最上声から — ロ短調で レ・ファ#・シ・レ・シ・ファ#・ラ#・ファ#・ラ#・シ (8 拍、上って導音から主音へ)。
  形式 (♩=60, ロ短調):
    Introitus — 録音そのもの (8.6 秒)
    I. Requiem ×4 — 録音の 17 の和音 (採譜) をすべて 4 倍の長さに (長い音は 2 拍ごと、低い音は 4 拍ごとに打ち直す)。
       その中で主題 (1 倍) がフーガのように 4 回入る (伸ばした和音といちばんぶつからない高さで)
    II. Fuga — 主題の 4 声フーガ (提示・下属調・ストレッタ・保続低音)
    III. Finale ×2 — 録音を 2 倍で、その上で主題が 1 小節ずつずれてストレッタで重なる → Amen (ロ長調の和音)
  高音を抑える: フーガは 1 オクターヴ低く書き、伸ばした録音の音はミ 5 より上をオクターヴ下へ。いちばん上でもミ 5 のあたり。
  すべてピアノの実音 (録音そのもの・録音から切り出した 1 音)。シンセ・ドラムなし。
  使い方: python compose_tablet83.py <bank82.json> [score_tablet83.json]
"""
import sys, os, json
import numpy as np
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet63 as LXIII

R = '20260925_125036'
BM = -3                                            # ロ短調 (ニ短調から)
LOW = BM - 12                                      # フーガは 1 オクターヴ低く
VOICE_SRC = {'S': '20260924_085314', 'A': '20260923_080918', 'T': '20260925_124643', 'B': '20260925_130431'}
DYNK = 1.3
INTRO, REQ, FUGA, FIN, AMEN = 3, 9, 16, 6, 3       # 小節
CAP = 76                                           # いちばん上 (ミ 5)
compose.RANGE['B'] = (40, 58)
X = []                                             # 直接置く音 (伸ばした録音・フーガの入り)

def fold(m):
    while m > CAP: m -= 12
    return m

def stretched(segs, k, T0, layer, step_hi=2.0, step_lo=4.0, g0=0.36):
    """採譜の和音を k 倍に: 1 音ごとに、頭を強く、あとは step 拍ごとに息をするように打ち直す"""
    for s in segs:
        t0, L = T0 + s['t'] * k, s['d'] * k
        for m in s['m']:
            mm = fold(m); step = step_hi if mm >= 52 else step_lo
            n_ = max(1, int(np.ceil(L / step - 1e-6)))
            for i in range(n_):
                a = t0 + i * step; dd = min(step, t0 + L - a)
                if dd <= 0.1: break
                amp = 1.0 if i == 0 else 0.6 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1))
                X.append(dict(v='PF', t=round(a, 3), d=round(dd + 0.8, 3), m=mm, gain=round(g0 * amp, 4), rid=VOICE_SRC['T'] if mm < 55 else VOICE_SRC['A'],
                              rel=1.0, beat=round(a, 3), dbeats=round(dd, 3), label=None, layer=layer))

def clash(T0, s_, tr):
    """主題を tr 動かしたとき、伸ばした和音 (いま鳴っている音) と半音・全音でぶつかる長さ"""
    bad, t = 0.0, T0
    for d, m in s_:
        mid = t + d / 2; pcs = {e['m'] % 12 for e in X if e.get('layer') in ('x4', 'x2') and e['t'] <= mid < e['t'] + e['dbeats']}
        if pcs and (m + tr) % 12 not in pcs and any(min((m + tr - q) % 12, (q - m - tr) % 12) <= 2 for q in pcs): bad += d * (2 if t == T0 or d >= 1 else 1)
        t += d
    return bad

def entry(T0, s_, chord_pcs, cen, g=0.6, rid=None):
    """主題 (1 倍) を、伸ばした和音といちばんぶつからず、終わりの音がその和音の音に着き、中心が cen に近い高さで"""
    cand = [tr for tr in range(-36, 25) if (s_[-1][1] + tr) % 12 in chord_pcs and max(m for _, m in s_) + tr <= CAP and min(m for _, m in s_) + tr >= 47]
    tr = min(cand, key=lambda x: clash(T0, s_, x) * 6 + abs(np.mean([m for _, m in s_]) + x - cen))
    print('  entry t=%.1f tr=%d clash=%.1f' % (T0, tr, clash(T0, s_, tr)))
    t = T0
    for d, m in s_:
        X.append(dict(v='PF', t=round(t, 3), d=round(d + 0.3, 3), m=m + tr, gain=g, rid=rid or VOICE_SRC['S'], rel=0.6, beat=round(t, 3), dbeats=d, label=None, layer='fugato'))
        t += d

def build():
    segs = CT.REC[R]['segs']
    s_ = LXIII.smooth(CT.make_subject(segs, BM, 60)); T5.SUBJ[R] = (s_, CT.harmonize(s_))
    print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = INTRO + REQ + FUGA + FIN + AMEN
    P = Piece(total)
    for k in range(total): P.tempo[k] = 60; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, LOW, VOICE_SRC, {}))
    for v in VOICES: P.rest_bars(v, 0, INTRO + REQ)
    def H_at(sec_t):                                # 録音の時刻 → その和音 (エンジンのニ短調の名前で)
        cur = segs[0]['ch']
        for s in segs:
            if s['t'] <= sec_t: cur = s['ch']
        return transpose_h([[cur]], -BM)[0][0]
    # Introitus
    P.section(0, 'Introitus — 9/25 12:50 の実音 (ロ短調)', '8.6 秒の録音そのもの — これを 4 倍に伸ばしていく')
    CT.add('REC', 0, INTRO * BPB, 0, 0.5, None, src=CT.REC[R]['file'], off=0.0, fin=0.02, fout=1.5, rid=R + '.wav', tag='9/25 12:50 — 8.6 秒の録音')
    for b in range(INTRO * BPB): P.harm[b] = H_at(min(8.5, b * 8.6 / (INTRO * BPB)))
    # I. Requiem ×4
    f = INTRO; P.section(f, 'I. Requiem ×4 — 録音を 4 倍に (ロ短調)', '8.6 秒の 17 の和音が 34 秒に — その中で主題がフーガのように 4 回入る')
    T0 = f * 4.0; stretched(segs, 4, T0, 'x4')
    for b in range(REQ * BPB): P.harm[f * BPB + b] = H_at(min(8.5, b / 4.0))
    def pcs_at(sec_t): return set(chord(transpose_h([[H_at(sec_t)]], BM)[0][0])['pcs'])
    for rt, cen, rid in ((0.3, 66, VOICE_SRC['A']), (2.1, 58, VOICE_SRC['T']), (4.2, 70, VOICE_SRC['S']), (6.1, 62, VOICE_SRC['A'])):
        sb = [(d, m + BM) for d, m in s_]                   # 前後 0.6 秒 (録音の時刻) で、いちばんぶつからない入りの時刻を探す
        def best(r):
            c = [tr for tr in range(-36, 25) if (sb[-1][1] + tr) % 12 in pcs_at(r + 1.6) and max(m for _, m in sb) + tr <= CAP and min(m for _, m in sb) + tr >= 47]
            return min(clash(T0 + r * 4, sb, tr) for tr in c) if c else 99
        rt = min((round(rt + 0.1 * j, 2) for j in range(-6, 7)), key=lambda r: best(r) + 0.2 * abs(r - rt))
        entry(T0 + rt * 4, sb, pcs_at(rt + 1.6), cen, rid=rid)
    for k in range(REQ): P.dyn[f + k] = DYNK
    # II. Fuga
    f = INTRO + REQ; P.section(f, 'II. Fuga — 主題の 4 声フーガ (ロ短調)', '提示 (アルト → ソプラノの答え → バス → テノール)、下属調、ストレッタ、保続低音 — 1 オクターヴ低く')
    T11.bach_fugue(P, f, R, '12:50')
    for k in range(FUGA): P.dyn[f + k] = DYNK * (0.7 + 0.15 * k / 15)
    # III. Finale ×4
    f = INTRO + REQ + FUGA; P.section(f, 'III. Finale ×2 — 録音を 2 倍で、主題のストレッタ', '8.6 秒の録音を 2 倍 (17 秒) で、その上で主題が 1 小節ずつずれて重なる')
    for v in VOICES: P.rest_bars(v, f, f + FIN)
    T0 = f * 4.0; stretched(segs, 2, T0, 'x2', step_hi=99, step_lo=99, g0=0.4)
    for b in range(FIN * BPB): P.harm[f * BPB + b] = H_at(min(8.5, b / 2.0))
    for k, (cen, rid) in enumerate(((66, VOICE_SRC['A']), (58, VOICE_SRC['T']), (70, VOICE_SRC['S']), (52, VOICE_SRC['B']))):
        rt = min(8.5, (k * 4.0 + 7.0) / 2.0)
        entry(T0 + k * 4.0, [(d, m + BM) for d, m in s_], pcs_at(rt), cen, g=0.6, rid=rid)
    # Amen
    f = INTRO + REQ + FUGA + FIN; P.section(f, 'Amen — ロ長調の和音', 'iv → V → I')
    P.set_harms(f, [['Gm', 'Gm', 'A7', 'A7'], ['D'], ['D']])
    P.place('S', f, [(2, n('Bb4')), (2, n('A4')), (8, n('A4'))], 0, 'Amen')
    for k in range(AMEN): P.dyn[f + k] = DYNK * 0.6
    LXIII.ARP.append((f, f + 2, 0.08, LOW))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [R] + list(VOICE_SRC.values()), 'piano_decay': 2.4, 'reverb': [6.0, 2.3, 0.48],
    'title': 'Requiem BADA — LXXXIII · Requiem e Fuga 12:50 x4',
    'subtitle': 'LXXXII の 16 倍を 4 倍にして — 9/25 12:50 のレクイエムとフーガ (ロ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['Introitus (8.6 秒の録音) → I. Requiem ×4 (34 秒) → II. Fuga → III. Finale ×2 + ストレッタ → Amen (ロ長調)',
               '主題: レ・ファ#・シ・レ・シ・ファ#・ラ#・ファ#・ラ#・シ (録音の最上声)。高音はミ 5 のあたりまで。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet83.json'
    compose.main(out, seed=183, bpm=60, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    K.BPM = 60; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * (1.3 if n_.get('label') else 1.1), 4)
    d['extras'] += X
    d['entries'] += [dict(t=INTRO * 4.0, label='録音 ×4 (17 の和音)', v='B'), dict(t=(INTRO + REQ + FUGA) * 4.0, label='録音 ×2', v='B')]
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras'] if e['v'] == 'PF']
    print('duration', round(d['duration'], 1), 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
