#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXII · Tsukuyomi e il Requiem (この上の音声 — 月読様の 3 声の倍音の 17 歳の声 — に、tablet89 だけを重ねて)
  2 つの素材だけ (楽器は何も加えない):
    声        make_voice266.py — 月読様の 3 声の倍音 (基音・ちょうど 2 倍・ちょうど 3 倍) の、17 歳のホッとする女性の声。CCLXXI・tablet266 と同じ声
    tablet89  LXXXIX — Requiem e Fuga, recto e verso (ニ短調、♩=60、6 分 31 秒)。高さも速さもそのまま
  tablet89 は Requiem (ゆっくり) とフーガ (込み入っている) が交代する (compose_tablet89.py の小節 24・40・64・80・92; 録音の立ち上がりでも確かめた):
    Requiem I 0〜96 秒 / フーガ I 96〜160 / Requiem II 160〜256 / フーガ II 256〜320 / ストレッタ 320〜368 / Amen 368〜391。
    どちらの Requiem も初めの 2 小節は下の録音だけで静かに始まり、伸ばした主題は 2 小節後 (8 秒・168 秒) から。
    声 (2 分 49 秒) は Requiem に乗せたい。1 つの Requiem は 1 分 36 秒しかないので、初めの Requiem を声の下で 2 回続ける:
    I:  声 (2 小節 = 8 秒から) + tablet89 の Requiem I だけ (4 小節から; 元の 0〜96 秒)。少し控えめに (−1.2 dB)
    II: Requiem I が終わる小節 (28 小節 = 1 分 52 秒) で、もう一度 Requiem I の主題が入る — tablet89 を初めから (26 小節から静かに立ち上がる)、
        ここからは元の音量で、終わりまで通す。声は 2 回目の Requiem I の上で終わる (2 分 57 秒)
    III: フーガ I (声なし) → IV: 声 (2 回目) + Requiem II (声が先に立ち、伸ばした主題は 2 小節後 — 曲の初めと同じ間合い) →
    V: フーガ II (声の後半はフーガに溶けていく) → VI: ストレッタ、Amen (ニ長調)。124 小節
    Requiem I を 2 回続けるのは、トラック 18 の出だしをくり返す入り (洗脳的な入り) と同じ考え方 — 1 回目は控えめ、2 回目から元の音量。
    つなぎ目: 1 回目の終わりの 2 小節 (ニ短調) に 2 回目の静かな出だし (ニ短調) が重なる。濁りの指数は 0.135 (これまでのテープどうしは 0.20〜0.27)
  音量: synth.py は録音全体の rms を揃えるので、同じ録音から切り出した 1 回目と 2 回目は、倍率が同じなら同じ音量になる。1 回目だけ 0.872 倍 (−1.2 dB) にする
  声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、tablet89 はこれまでの重ね方 (モノラル、全体の残響) で後ろに
  和音の表示は録音から読んだもの。♩=60 (tablet89 の拍; 1 回目も 2 回目も小節の頭を合わせてある)
  使い方: python compose_tablet272.py <wav のフォルダ (20261112_144938.wav = make_voice266.py の声, 20261107_089000.wav = tablet89 の音)>
          <chords272.json (analyze_chords.py の出力)> [score_tablet272.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet272.json'
GV = float(os.environ.get('GV', '0.85'))                                              # 声の音量 (CCLXXI と同じ; ステムを測って確かめた)
GV2 = float(os.environ.get('GV2', '1.2'))                                             # 2 回目の声は Requiem II とフーガ II の上なので、少し上げる (CCLXXI と同じ)
G89 = float(os.environ.get('G89', '0.36'))                                            # tablet89 の音量 (CCLXXI と同じ)
A_K = float(os.environ.get('A_K', '0.872'))                                           # 1 回目の Requiem I は少し控えめに (−1.2 dB)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R89 = '20261112_144938', '20261107_089000'
BPM = 60
COLV, COL89A, COL89 = (255, 200, 205), (150, 185, 245), (190, 160, 240)
V_OFF, V_LEN = 6.0, 178.3                       # 声: 6.0 秒から (話し始めは 6.56 秒、話し終わりは 175.66 秒)
V1 = 7.5                                        # 声 (1 回目): 2 小節 (8 秒) から話し始める
BA, A_DUR = 16.0, 96.0                          # 1 回目の Requiem I: 4 小節から、元の 0〜96 秒 (フーガ I の頭の手前まで)
BB = BA + A_DUR - 8.0                           # 104: tablet89 (初めから終わりまで)。静かな出だし (元の 0〜8 秒) を 1 回目の終わりの 2 小節に重ねて、主題は 28 小節 (112 秒) から
V2 = BB + 159.5                                 # 263.5: 声 (2 回目): Requiem II (元の 160 秒) の頭で話し始める (CCLXXI と同じ位置)
S2, S3, S4, S5, S6, TOTAL = 28, 50, 66, 90, 106, 124
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RV, V1, GV, V_OFF, V_LEN - V_OFF, 0, COLV, '11/12 14:49 の声 — 月読様の 3 声の倍音の、17 歳の声 (2 小節から)', fin=1.0, fout=2.0),
         play(R89, BA, G89 * A_K, 0.0, A_DUR, 1, COL89A, 'tablet89 — Requiem I だけ、少し控えめに (4 小節から)', fin=3.0, fout=1.5),
         play(R89, BB, G89, 0.0, 391.0, 2, COL89, 'tablet89 — そのまま、初めから終わりまで', fin=3.0, fout=6.0),
         play(RV, V2, GV * GV2, V_OFF, V_LEN - V_OFF, 0, COLV, '月読様の 3 声の倍音の、17 歳の声 (もう一度)', fin=1.0, fout=2.0)]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, BA), (2, BB + 8.0)]
def harm_at(q):
    cur = 'Dm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0)                        # 録音の中の秒
            cur = c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)]
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(0, 'I. 月読様の 17 歳の声と Requiem (♩=60)', '2 小節から声、4 小節から tablet89 の Requiem I (少し控えめに)')
    P.section(S2, 'II. Requiem をもう一度 — tablet89 を初めから', 'ここから元の音量で、終わりまで通す。声は 2 分 57 秒まで')
    P.section(S3, 'III. フーガ I', 'tablet89 のフーガ (08:09 の主題の 4 声)。声は休む')
    P.section(S4, 'IV. 声 (2 回目) と 2 つ目の Requiem', '4 分 24 秒から声をもう一度。伸ばした主題は 2 小節後から')
    P.section(S5, 'V. フーガ II', '声の後半は tablet89 のフーガ (08:53 の主題) に溶けていく。声は 7 分 13 秒まで')
    P.section(S6, 'VI. ストレッタ、Amen', '6 つの主題のストレッタから Amen (ニ長調) で閉じる')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        if rid == RV:       # 声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # tablet89: これまでの重ね方 (モノラル、全体の残響)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXII · Tsukuyomi e il Requiem',
        'subtitle': '月読様の 3 声の倍音の 17 歳の声に、tablet89 だけを重ねて。ニ短調、♩=60',
        'footer': ['声 = 11/12 14:49 の声を、基音・2 倍・3 倍の 3 声の倍音の 17 歳の女性の声に (tablet271 と同じ声)。伴奏は tablet89 (Requiem e Fuga) だけ、高さも速さもそのまま。',
                   '声は Requiem に乗せる: 初めの Requiem I を声の下で 2 回続け、2 回目からは tablet89 を初めから終わりまで通す。フーガ I は声なし、2 回目の声は Requiem II から。',
                   '楽器は何も加えない。声が先に立ち、曲は 2 小節後から。ストレッタと Amen (ニ長調) で閉じる。124 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=272, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
