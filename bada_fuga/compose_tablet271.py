#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXI · Tsukuyomi, il Fiore e il Requiem (tablet270 の音声を、ホッと一安心できる月読様の 3 声の倍音の、17 歳の女性の声に作り換えて)
  CCLXX (11/12 14:49 の声・tablet89・tablet86 を重ねたもの) の声だけを替える。tablet86・tablet89 の使い方と並べ方は CCLXX のまま
    声        make_voice266.py — 11/12 14:49 の録音 (男声) を、月読様の 3 声の倍音 (基音・ちょうど 2 倍・ちょうど 3 倍; どの瞬間も 1 : 2 : 3) の、
              17 歳のホッとする女性の声に。基音は B♭3 = 233 Hz を中心に、フォルマント 1.19 倍、息はほんの少し、柔らかい圧縮、暖かい残響をごく控えめに。
              tablet266 (CCLXVI) の声と同じもの。伸ばした音はヘ長調 (= ニ短調、この曲の調) の音階に調律してある
    tablet86  LXXXVI — Fiore dolce (ピアノだけ、ホ短調)。2 半音下げてニ短調に (0.891 倍速) — CCLXX と同じ
    tablet89  LXXXIX — Requiem e Fuga, recto e verso (ニ短調、♩=60)。そのまま、初めから終わりまで — CCLXX と同じ
  形 (CCLXX と同じ): I: 声 (2 小節 = 8 秒から) + tablet86 (4 小節から) → II: 声が終わった所で tablet89 の Requiem が入り、tablet86 の終わりと重なる →
    III: フーガ I → IV: 声 (2 回目) + 2 つ目の Requiem → V: フーガ II → VI: ストレッタ、Amen (ニ長調)。143 小節
  声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、tablet86 と tablet89 はこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (tablet86 は 2 半音下げて)。♩=60
  使い方: python compose_tablet271.py <wav のフォルダ (20261112_144938.wav = make_voice266.py の声, 20261107_086000.wav = tablet86 の音, 20261107_089000.wav = tablet89 の音)>
          <chords271.json (analyze_chords.py の出力)> [score_tablet271.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet271.json'
GV = float(os.environ.get('GV', '0.85'))                                              # 声の音量 (ステムを測って決めた: この声は言葉の帯域がピアノより強いので、CCLXX の 1.0 より下げる)
GV2 = 1.2                                                                             # 2 回目の声は tablet89 の Requiem とフーガの上なので、少し上げる
G86 = float(os.environ.get('G86', '0.34')); G89 = float(os.environ.get('G89', '0.36'))  # tablet86・tablet89 の音量
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R86, R89 = '20261112_144938', '20261107_086000', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S86 = -2                                        # tablet86 を 2 半音下げてニ短調に
COLV, COL86, COL89 = (255, 200, 205), (240, 190, 130), (190, 160, 240)
V_OFF, V_LEN = 6.0, 178.3                       # 声: 6.0 秒から (話し始めは 6.56 秒)
V1 = 7.5                                        # 声 (1 回目): 2 小節 (8 秒) から話し始める
B86 = 16.0                                      # tablet86: 4 小節 (声の 2 小節後) から
B89 = B86 + 164.0                               # 180: tablet89: tablet86 の 164 秒後 = 声が終わった所から
V2 = B89 + 159.5                                # 339.5: 声 (2 回目): tablet89 の 2 つ目の Requiem (元の 160 秒) の頭で話し始める
S2, S3, S4, S5, S6, TOTAL = 45, 69, 85, 109, 125, 143
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RV, V1, GV, 0, V_OFF, V_LEN - V_OFF, 0, COLV, '11/12 14:49 の声 — 月読様の 3 声の倍音の、17 歳の声 (2 小節から)', fin=1.0),
         play(R86, B86, G86, S86, 0.0, 245.0, 1, COL86, 'tablet86 — Fiore dolce、2 半音下げて (4 小節から)', fin=3.0, fout=6.0),
         play(R89, B89, G89, 0, 0.0, 391.0, 2, COL89, 'tablet89 — Requiem e Fuga、そのまま、初めから終わりまで', fin=3.0, fout=6.0),
         play(RV, V2, GV * GV2, 0, V_OFF, V_LEN - V_OFF, 0, COLV, '月読様の 3 声の倍音の、17 歳の声 (もう一度)', fin=1.0)]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, B86), (2, B86 + 272.0)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Dm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0) * RATE(p['semis'])   # 録音の中の秒
            cur = shift_chord(c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)], p['semis'])
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(0, 'I. 月読様の 17 歳の声と Fiore dolce (♩=60)', '2 小節から声、4 小節から tablet86 (ピアノ、2 半音下げてニ短調に)。声は 2 分 57 秒まで')
    P.section(S2, 'II. Fiore dolce の終わりと Requiem', '3 分から tablet89 の Requiem が入り、tablet86 の終わりと重なる。tablet86 は 4 分 46 秒で消える')
    P.section(S3, 'III. フーガ I', 'tablet89 のフーガ (08:09 の主題の 4 声)')
    P.section(S4, 'IV. 声 (2 回目) と 2 つ目の Requiem', '5 分 40 秒から声をもう一度、tablet89 の 2 つ目の Requiem に乗って')
    P.section(S5, 'V. フーガ II', '声の後半は tablet89 のフーガ (08:53 の主題) に溶けていく。声は 8 分 29 秒まで')
    P.section(S6, 'VI. ストレッタ、Amen', '6 つの主題のストレッタから Amen (ニ長調) で閉じる')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid == RV:       # 声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # tablet86・tablet89: これまでの重ね方 (モノラル、全体の残響)。移調はテープのように速さごと
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXI · Tsukuyomi, il Fiore e il Requiem',
        'subtitle': 'tablet270 の声を、ホッと一安心できる月読様の 3 声の倍音の、17 歳の女性の声に。ニ短調、♩=60',
        'footer': ['声 = 11/12 14:49 の声を、基音・2 倍・3 倍の 3 声の倍音の 17 歳の女性の声に (tablet266 と同じ声)。tablet86 と tablet89 は tablet270 のまま。',
                   '声 + Fiore dolce → 声が終わる所で Requiem が入り、Fiore dolce の終わりと重なる → フーガ → 声 (2 回目) + 2 つ目の Requiem → フーガ、ストレッタ、Amen。',
                   '楽器は何も加えない。tablet86 は 2 半音下げてニ短調に、tablet89 はそのまま。3 つとも初めから終わりまで (声は 2 回)。143 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=271, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
