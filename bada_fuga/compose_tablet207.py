#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCVII · Cinque suoni con la voce accordata al sol (tablet204 の女性の声を、オーケストラのバイオリンの G 線 (G3 = 196 Hz) に調律して合わせて作り換え)
  CCIV と同じ 5 つの音の重ね方で、女性の声の調律だけを変える: 元の男声 (f0 中央値 116 Hz) を 9.07 半音上げて音高の中央をちょうど G3 (196 Hz、A4 = 440 Hz 基準のバイオリンの G 線) に、フォルマントを 1.15 倍、ト長調の音階に 0.9 で強く寄せる (調律)、9 kHz より上だけ丸め、rms −22.5 dB (0.52)
  使い方: python compose_tablet207.py <bank150.json> <wav のフォルダ (20261108_145525.wav = 調律した声)> [score_tablet207.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet207.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R89, R86, R18, R08 = '20261108_145525', '20261107_089000', '20261107_086000', '20261107_180000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 150, 176
NAMES = {RV: '11/08 14:55 の声 (女性の声、G3 に調律)', R89: 'tablet89', R86: 'tablet86', R18: 'トラック 18', R08: 'トラック 8'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(R89, 0, 0.45, 0, 0.0, 391.0, True), (RV, 2, 0.52, 0, 0.0, 198.5, True),                      # I: tablet89 + 声 (原音)
         (R86, S2, 0.45, -2, 0.0, 245.0, True), (R18, S2 + 2, 0.5, 0, 0.0, 149.1, True),               # II: tablet86 (全音下げて) + トラック 18
         (R89, S3, 0.45, 0, 90.0, 300.0, True), (RV, S3 + 2, 0.52, 0, 0.0, 198.5, True), (R08, S3 + 2, 0.4, 5, 0.0, 249.2, True),   # III: tablet89 の後半 + 声 (2 回目) + トラック 8 (4 度上げて)
         (R86, S4, 0.45, -2, 100.0, 145.0, True), (R18, S4 + 2, 0.45, 0, 60.0, 89.1, True)]            # IV: tablet86 の後半 + トラック 18 の後半
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. tablet89 と声 (♩=60)', 'tablet89 (レクイエム) の上に 14:55 の声 (女性の声、G3 に調律)')
    P.section(S2, 'II. tablet86 とトラック 18', 'tablet86 (全音下げてヘ長調に) の上にトラック 18 (ニ短調、そのまま)')
    P.section(S3, 'III. tablet89 の後半、声、トラック 8', 'tablet89 の後半 (90 秒から) の上に声をもう一度、トラック 8 (4 度上げて)')
    P.section(S4, 'IV. tablet86 の後半とトラック 18 の後半、消える', 'tablet86 の後半 (100 秒から) とトラック 18 の後半、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], {5: '原音、4 度上げて', -2: '原曲、全音下げて', 0: ('女性の声に変換、G3 = 196 Hz に調律' if rid == RV else '原音、そのまま' if rid == R18 else '原曲、そのまま')}[sm] + ('、後半' if off else '')))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R18, R08, R89, R86], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCVII · Cinque suoni con la voce accordata al sol',
        'subtitle': 'tablet204 の女性の声を、オーケストラのバイオリンの G 線 (G3 = 196 Hz) に調律して合わせて作り換え: 音高の中央をちょうど G3 に (9.07 半音上げ)、ト長調の音階に強く寄せる。tablet89・tablet86 (全音下げて)・トラック 18・トラック 8 (4 度上げて) はそのまま、楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['14:55 の声は feminize_voice.py で女性の声に、G3 = 196 Hz に調律 (9.07 半音上げて中央を G3 に、フォルマント 1.15 倍、ト長調の音階に 0.9 で寄せる、9 kHz より上を丸め)、rms −22.5 dB で 2 回 (0.52)。tablet89 (ニ短調) は全曲と後半 (0.45)、tablet86 (ト長調) は全音下げてヘ長調に全曲と後半 (0.45)、トラック 18 (ニ短調) はそのまま全部と後半 (0.5 / 0.45)、トラック 8 (ハ長調 / イ短調) は 4 度上げて (0.4)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えず、何も取り除かない (サンプラーのピアノも、ペダルも、鐘もなし)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=207, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
