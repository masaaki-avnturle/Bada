#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXII · Requiem e Fuga 12:50 (9/25 12:50:36 の 8.6 秒の録音を 16 倍に伸ばして — レクイエムとフーガ)
  録音は 8.6 秒の、ロ短調の劇的な一節 (F#7 = 属七、Gmaj7 = VI、C7、Em …)。短いので、曲そのものを本当に 16 倍に伸ばせる (8.6 秒 → 2 分 18 秒)。
  主題: 録音の最上声から — ロ短調で レ・ファ#・シ・レ・シ・ファ#・ラ#・ファ#・ラ#・シ (8 拍、上って導音から主音へ)。
  形式 (♩=60, ロ短調):
    Introitus — 録音そのもの (8.6 秒)
    I. Requiem ×16 — 録音の 17 の和音 (採譜) をすべて 16 倍の長さに。伸ばした音は 2 拍ごと (低い音は 4 拍ごと) に息をするように打ち直す (ピアノの実音)。
       長い F#7・Gmaj7・Em の和音の中で、主題 (1 倍) がフーガのように次々と入る (入るごとに終わりの音がその和音の音に着く高さで)
    II. Fuga — 主題の 4 声フーガ (提示・下属調・ストレッタ・保続低音)
    III. Finale ×4 — 録音を 4 倍で、その上で主題がストレッタで重なる → Amen (ロ長調の和音)
  高音を抑える: フーガは 1 オクターヴ低く書き、伸ばした録音の音はミ 5 より上をオクターヴ下へ。いちばん上でもミ 5 のあたり。
  すべてピアノの実音 (録音そのもの・録音から切り出した 1 音)。シンセ・ドラムなし。
  使い方: python compose_tablet82.py <bank82.json> [score_tablet82.json]
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
INTRO, REQ, FUGA, FIN, AMEN = 3, 35, 16, 9, 3       # 小節
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

def entry(T0, s_, chord_pcs, cen, g=0.6, rid=None):
    """主題 (1 倍) を、終わりの音がその和音の音に着き、中心が cen に近い高さで"""
    cand = [tr for tr in range(-36, 25) if (s_[-1][1] + tr) % 12 in chord_pcs and max(m for _, m in s_) + tr <= CAP]
    tr = min(cand, key=lambda x: abs(np.mean([m for _, m in s_]) + x - cen))
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
    P.section(0, 'Introitus — 9/25 12:50 の実音 (ロ短調)', '8.6 秒の録音そのもの — これを 16 倍に伸ばしていく')
    CT.add('REC', 0, INTRO * BPB, 0, 0.5, None, src=CT.REC[R]['file'], off=0.0, fin=0.02, fout=1.5, rid=R + '.wav', tag='9/25 12:50 — 8.6 秒の録音')
    for b in range(INTRO * BPB): P.harm[b] = H_at(min(8.5, b * 8.6 / (INTRO * BPB)))
    # I. Requiem ×16
    f = INTRO; P.section(f, 'I. Requiem ×16 — 録音を 16 倍に (ロ短調)', '8.6 秒の 17 の和音が 2 分 18 秒に — 長い F#7・Gmaj7・Em の中で主題がフーガのように入る')
    T0 = f * 4.0; stretched(segs, 16, T0, 'x16')
    for b in range(REQ * BPB): P.harm[f * BPB + b] = H_at(b / 16.0)
    def pcs_at(sec_t): return set(chord(transpose_h([[H_at(sec_t)]], BM)[0][0])['pcs'])
    for rt, cen, rid in ((3.15, 66, VOICE_SRC['A']), (3.75, 58, VOICE_SRC['T']), (4.3, 70, VOICE_SRC['S']),
                         (5.1, 70, VOICE_SRC['S']), (5.7, 62, VOICE_SRC['A']), (6.25, 56, VOICE_SRC['T']), (7.7, 64, VOICE_SRC['A'])):
        entry(T0 + rt * 16, [(d, m + BM) for d, m in s_], pcs_at(rt + 0.3), cen, rid=rid)
    for k in range(REQ): P.dyn[f + k] = DYNK
    # II. Fuga
    f = INTRO + REQ; P.section(f, 'II. Fuga — 主題の 4 声フーガ (ロ短調)', '提示 (アルト → ソプラノの答え → バス → テノール)、下属調、ストレッタ、保続低音 — 1 オクターヴ低く')
    T11.bach_fugue(P, f, R, '12:50')
    for k in range(FUGA): P.dyn[f + k] = DYNK * (0.7 + 0.15 * k / 15)
    # III. Finale ×4
    f = INTRO + REQ + FUGA; P.section(f, 'III. Finale ×4 — 録音を 4 倍で、主題のストレッタ', '8.6 秒の録音を 4 倍 (34 秒) で、その上で主題が 2 小節ずつずれて重なる')
    for v in VOICES: P.rest_bars(v, f, f + FIN)
    T0 = f * 4.0; stretched(segs, 4, T0, 'x4', step_hi=99, step_lo=99, g0=0.4)
    for b in range(FIN * BPB): P.harm[f * BPB + b] = H_at(min(8.5, b / 4.0))
    for k, (cen, rid) in enumerate(((66, VOICE_SRC['A']), (58, VOICE_SRC['T']), (70, VOICE_SRC['S']), (52, VOICE_SRC['B']))):
        rt = min(8.0, (k * 8.0 + 8.0) / 4.0)
        entry(T0 + k * 8.0, [(d, m + BM) for d, m in s_], pcs_at(rt), cen, g=0.6, rid=rid)
    # Amen
    f = INTRO + REQ + FUGA + FIN; P.section(f, 'Amen — ロ長調の和音', 'iv → V → I')
    P.set_harms(f, [['Gm', 'Gm', 'A7', 'A7'], ['D'], ['D']])
    P.place('S', f, [(2, n('Bb4')), (2, n('A4')), (8, n('A4'))], 0, 'Amen')
    for k in range(AMEN): P.dyn[f + k] = DYNK * 0.6
    LXIII.ARP.append((f, f + 2, 0.08, LOW))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [R] + list(VOICE_SRC.values()), 'piano_decay': 2.4, 'reverb': [6.0, 2.3, 0.48],
    'title': 'Requiem BADA — LXXXII · Requiem e Fuga 12:50',
    'subtitle': '9/25 12:50 の 8.6 秒の録音を 16 倍に伸ばして — レクイエムとフーガ (ロ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['Introitus (8.6 秒の録音) → I. Requiem ×16 (2 分 18 秒) → II. Fuga → III. Finale ×4 + ストレッタ → Amen (ロ長調)',
               '主題: レ・ファ#・シ・レ・シ・ファ#・ラ#・ファ#・ラ#・シ (録音の最上声)。高音はミ 5 のあたりまで。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet82.json'
    compose.main(out, seed=182, bpm=60, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    K.BPM = 60; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * (1.3 if n_.get('label') else 1.1), 4)
    d['extras'] += X
    d['entries'] += [dict(t=INTRO * 4.0, label='録音 ×16 (17 の和音)', v='B'), dict(t=(INTRO + REQ + FUGA) * 4.0, label='録音 ×4', v='B')]
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras'] if e['v'] == 'PF']
    print('duration', round(d['duration'], 1), 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
