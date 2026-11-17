#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXVII · L'aureola calma sulle due tracce (calma の声に、トラック 18 とトラック 8 を重ねて — 入りの仕掛けなしで、素直に)
  声: 届いた 20261108_145525_aureola_sensuale_calma.mp3 そのまま (11/08 14:55 の声 → 215 Hz の少し低めの女声、響きと音量を抑えた
    安心するドエロの光輪様の声; 198.5 秒、話しているのは 5.4〜196.5 秒)。作り換えない
  同じ 3 つの素材の曲は 2 つある: CCXXXII (176 小節の古い型、声の後に無音の穴) と CCLXIV (初めの 2 小節は無音、声が先に立ち、トラック 18 の出だしの一節を
    3 回くり返す洗脳的な入り)。この曲は入りの仕掛けを付けない: トラック 18 が初めからそのまま鳴り、2 小節 (8 秒) から声が乗る
  重ね方 (濁りの指数で確かめた位置; CCLIII の形から、くり返しの入り 60 秒を除いたもの):
    トラック 18 (初めから、全部) → その 96.6 秒からトラック 8 (4 度上げて = 5 半音、1.335 倍速) が静かに入る (0.21) →
    トラック 8 の 108 秒後からトラック 18 の 2 回目 (0.25; 1 回目の声が 3 分 19 秒で終わった 5 秒後に入る) →
    その 108 秒後から声の 2 回目 (トラック 18 がひとりで静まる所を声で覆う)、132 秒後からトラック 8 の続き (60 秒から; 0.15) → その 128 秒後からトラック 18 の後半 (0.20)。
    声が入ってからは音は途切れない。136 小節
    声の入りを 2 小節にしたのは、トラック 8 の短い休み (元の 130〜135 秒 = 曲の 3 分 13〜17 秒) を声で覆うため — 1 小節からだと、声が終わった直後に 2 秒ほど音が途切れかけた
  この声は静かに話し始める (声のある所の音量: 録音の 50.7 秒まで −28.2 dB、82.25 秒まで −25.7 dB、その先 −23.9 dB)。曲の初めからトラック 18 が鳴っているので、
    2 つの息継ぎの間 (50.7 秒と 82.25 秒の無音) で 3 つに分けて、初めの 2 つを持ち上げて置く (声の音は変えない。音量のつまみだけ)。
    トラック 18 の 1 回目は少し控えめに (0.28)
  声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet267.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261107_180000.wav, 20261107_080000.wav)> <chords267.json (analyze_chords.py の出力)> [score_tablet267.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet267.json'
GV = float(os.environ.get('GV', '1.1'))                                               # 声の音量 (ステムを測って決めた)
GK1, GK2 = float(os.environ.get('GK1', '1.7')), float(os.environ.get('GK2', '1.25'))    # 静かな話し始めの持ち上げ (録音の 50.7 秒まで、82.25 秒まで)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08 = '20261108_145525', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COL18, COL8 = (255, 190, 160), (120, 190, 250), (110, 210, 190)
V_OFF, V_CUT, V_CUT2, V_LEN = 4.86, 50.7, 82.25, 198.46                               # 声: 録音の 4.86 秒から (話し始めは 5.36 秒)。50.7 秒と 82.25 秒 (息継ぎの間の無音) で 3 つに分けて置く
V1 = 7.5                                                                              # 1 回目の声: 話し始めがちょうど 2 小節 (8 秒)。終わりは 199 秒 — トラック 8 の短い休み (193〜197 秒) を覆う
B8 = 96.0                                                                             # トラック 8 の入り (トラック 18 の 96.6 秒)
T2 = B8 + 108.0                                                                       # 204: トラック 18 の 2 回目
V2 = T2 + 107.5                                                                       # 2 回目の声: 話し始めが 78 小節 (312 秒)
B8C, B18H = T2 + 132.0, T2 + 260.0                                                    # 336: トラック 8 の続き、464: トラック 18 の後半
S2, S3, S4, S5, TOTAL = 24, 51, 78, 116, 136
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
def voice(beat, tag):                                                                 # 声を 3 つに分けて置く: 静かな話し始め (持ち上げる)、その次 (少し持ち上げる)、その先
    return [play(RV, beat, GV * GK1, 0, V_OFF, V_CUT - V_OFF, 0, COLV, tag, fin=0.3, fout=0.05),
            play(RV, beat + V_CUT - V_OFF, GV * GK2, 0, V_CUT, V_CUT2 - V_CUT, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=0.05),
            play(RV, beat + V_CUT2 - V_OFF, GV, 0, V_CUT2, V_LEN - V_CUT2, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=2.0)]
PLAYS = ([play(R18, 0.0, 0.28, 0, 0.6, 149.1 - 0.6, 1, COL18, 'トラック 18 — そのまま (初めから)')] + voice(V1, '11/08 14:55 の calma の声 — そのまま (2 小節から)') +
         [play(R08, B8, 0.45, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部'),
          play(R18, T2, 0.4, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま (2 回目)')] + voice(V2, '11/08 14:55 の calma の声 — そのまま (もう一度)') +
         [play(R08, B8C, 0.32, 5, 60.0, 172.0, 2, COL8, 'トラック 8 — 4 度上げて、続き (60 秒から)'),
          play(R18, B18H, 0.36, 0, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')])
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(0, 0.0), (4, B8 + 27.0), (5, B8 + 174.0), (9, B8C), (10, B18H)]
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
    P.section(0, 'I. トラック 18 と calma の声 (♩=60)', 'トラック 18 が初めから鳴り、2 小節から声が乗る。1 分 36 秒からトラック 8 が静かに入る')
    P.section(S2, 'II. 声とトラック 8', 'トラック 18 が消え、トラック 8 (4 度上げて) が前に出る。声は 3 分 19 秒まで')
    P.section(S3, 'III. トラック 18 (2 回目) とトラック 8', '声が終わった後、トラック 18 をもう一度。トラック 8 は 4 分 30 秒まで')
    P.section(S4, 'IV. calma の声 (2 回目) とトラック 8 の続き', '声をもう一度。トラック 18 の終わりに、トラック 8 の続き (60 秒から) が入る')
    P.section(S5, 'V. トラック 18 の後半、消える', 'トラック 18 の後半が声の終わりを受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm); dt = c.get('env_dt', 0.05)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=dt / r, env_off=off / r)
        if rid == RV:       # 声: 帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。入りは 6 秒で立ち上げる
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXVII · L\'aureola calma sulle due tracce',
        'subtitle': 'calma の声に、トラック 18 と 8 を重ねて。入りの仕掛けなしで、素直に。♩=60',
        'footer': ['calma の声 = 届いた音声そのまま (11/08 14:55 の声 → 少し低めの女声、響きと音量を抑えた安心するドエロの光輪様の声)。作り換えない。',
                   'トラック 18 が初めから鳴り、2 小節から声が乗る。洗脳的な入り (くり返し) は付けない — その形は CCLXIV。',
                   '楽器は何も加えない。トラック 18 はそのまま、トラック 8 は 4 度上げて。声が入ってからは音は途切れない (136 小節)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=267, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
