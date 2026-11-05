#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLVII · Basso profondo ipnotico (2026/11/06 の曲をメインにして、tablet117 を合わせて、両方とも高音の響く音を重低音に変換して、静かな洗脳的な曲に)
  変換: deep_bass.py — 録音の高い帯域 (1.2〜8 kHz、ピアノの響きの倍音) を取り出し、4 オクターヴ下げて (位相ボコーダー)、220 Hz 以下だけを残す。元の低い帯域 (< 500 Hz) は小さく残す
  メイン: 11/06 06:42 の重低音 (227 秒) を 2 度、バックに tablet117 (眠りへの曲) の重低音を全曲に小さく。その上に、和音の根音の正弦波の低音 (SUB) が 2 小節ごとにゆっくり脈打つ (洗脳)、低いピアノの音がまれに
  静かに: 高い音は何もない。鐘なし、声なし
  使い方: python compose_tablet147.py <bank1106.json (06:42 の採譜)> <wav のフォルダ (20261106_064228_deep.wav, 20261003_117000_deep.wav)> [score_tablet147.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet147.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
import soundfile as sf
RECS = json.load(open(BANKP))['recordings']
R42, R117 = '20261106_064228', '20261003_117000'
D42 = RECS[R42]['dur']; D117 = sf.SoundFile(os.path.join(WDIR, R117 + '_deep.wav')).frames / 44100.0
BPM = 60
P1, P2, TOTAL = 0, 60, 124
PLAYS = [(R42, 1, 0.9, 0), (R42, P2 + 1, 0.85, 0)]
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []; RH = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
        if cur is None: cur = 'F'
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(P1, 'I. 06:42 の重低音 (♩=60)', '11/06 06:42 の高音の響きを 4 オクターヴ下げた重低音 (メイン)。バックに tablet117 の重低音が小さく。和音の根音の正弦波の低音が 2 小節ごとにゆっくり脈打つ')
    P.section(P2, 'II. 06:42 の重低音、2 度目', '同じ重低音をもう一度、脈は 5 度を重ねて少し深く — 最後は tablet117 の重低音と脈だけが消えていく')
    return P

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_deep.wav'), off=0.0, fin=1.0 if bar > 1 else 0.05, fout=8.0, semis=sm, rid=rid + '.wav', tag='11/06 06:42 — 高音の響きを重低音に (メイン)')
    add('REC', 0, min(D117, (TOTAL - 1) * BPB), 0, 0.5, None, src=os.path.join(WDIR, R117 + '_deep.wav'), off=0.0, fin=3.0, fout=10.0, semis=0, rid=R117 + '.wav', tag='tablet117 — 高音の響きを重低音に (バックに小さく)')
    first = True
    for b in range(2, TOTAL - 3, 2):
        r = 31 + chord(P.harm[b * BPB])['root']
        if r > 40: r -= 12
        g = 0.2 if b < TOTAL - 16 else max(0.04, 0.2 - 0.012 * (b - (TOTAL - 16)))
        add('SUB', b * BPB, 7.0, r, g, '根音の正弦波の低音 (2 小節ごと、脈)' if first else None); first = False
        if b >= P2 and b % 4 == 0: add('SUB', b * BPB + 0.5, 6.0, r + 7, g * 0.5, '5 度を重ねて' if b == P2 else None)
    for b in (P1 + 8, P1 + 32, P2 + 8, P2 + 32):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.5, r, 0.1, '低いピアノの音 (まれに)' if b == P1 + 8 else None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R42, R117], 'piano_decay': 2.6, 'reverb': [6.0, 2.5, 0.35],
        'title': 'Requiem BADA — CXLVII · Basso profondo ipnotico',
        'subtitle': '11/06 06:42 をメインにして tablet117 を合わせ、両方とも高音の響く音を重低音に変換して (4 オクターヴ下げ、220 Hz 以下)、静かな洗脳的な曲に: 06:42 の重低音 → 2 度目 → 消える。根音の正弦波の低音が 2 小節ごとに脈打つ。♩=60',
        'legend': ['SUB', 'L'], 'vname': {'SUB': '正弦波の低音 (脈)', 'L': 'Pf 低音'},
        'footer': ['変換 = deep_bass.py: 1.2〜8 kHz の帯域を位相ボコーダーで −48 半音、低域通過 220 Hz、元の 500 Hz 以下を 0.2〜0.3 で残す。メイン 0.9 / 0.85、tablet117 0.5',
                   '和音は 06:42 の採譜から (脈の根音)。高い音はない。鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=147, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
