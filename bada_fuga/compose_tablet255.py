#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLV · Il canto dell'aureola giovane (2025/01/08 14:42 の歌を、ドエロの若い女性の光輪様の歌声にして、トラック 18 とトラック 8 を重ねて)
  歌声: make_voice255.py — 録音から取り出した歌声 (男声、ハ短調) を 14 半音上げてニ短調 (トラック 18 の調) の若い女性の歌声に。
    光輪 = 倍音の 2 声 (ちょうど 2 倍と 3 倍) と残響、ドエロ = 息の多い発声と囁きの層、近さ。ステレオ
  歌は 4 分 19 秒あるので 1 回だけ (これまでの話し声の曲は 3 分の声を 2 回)。歌の前半 (2 分 43 秒) をトラック 18 に、後半 (1 分 23 秒) を
    トラック 8 (4 度上げて = 5 半音、1.335 倍速、ニ短調 / ヘ長調) に乗せ、歌の終わりをトラック 18 の後半が受けて消える:
    I: 歌声 + トラック 18 → II: 歌声 + トラック 8 → III: トラック 18 の後半、消える。83 小節
  入りの間合いは tablet219 と同じ: 初めの 2 小節は何も鳴らず、2 小節 (8 秒) から歌声、4 小節 (16 秒) からトラック 18。どちらもゆっくり現れる
  重ねる位置は濁りの指数 (analyze_chords.py の節を参照) で: トラック 18 の 112 秒からトラック 8 (0.20; トラック 8 が大きくなってからの重なりは 0.15)、
    トラック 8 の 124 秒後からトラック 18 の後半 (0.26)。歌声とテープの指数は README の節に
  歌声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet255.py <wav のフォルダ (20250108_144205.wav = 光輪様の歌声, 20261107_180000.wav, 20261107_080000.wav)> <chords255.json (analyze_chords.py の出力)> [score_tablet255.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet255.json'
GV = float(os.environ.get('GV', '1.15'))                                              # 歌声の音量 (ステムを測って決めた)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08 = '20250108_144205', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COL18, COL8 = (250, 160, 190), (120, 190, 250), (110, 210, 190)
V_T0, B18 = 8.0, 16.0                                                                 # 2 小節から歌声、4 小節からトラック 18 (tablet219 と同じ入りの間合い)
B8 = B18 + 112.0                                                                      # トラック 8: トラック 18 の 112 秒から (歌声との指数もここが小さい)
B18B = B8 + 124.0                                                                     # トラック 18 の後半: トラック 8 の 124 秒後から
S2, S3, TOTAL = 39, 63, 83
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
V_CUT, GV2 = 168.0, 1.2                                                               # 歌の後半 (録音の 168 秒から; 163〜175 秒は歌っていない) は静かに歌われているので、歌声を 1.2 倍に
PLAYS = [play(RV, V_T0, GV, 0, 0.0, V_CUT, 0, COLV, '2025/01/08 14:42 の歌 — ドエロの若い女性の光輪様の歌声 (2 小節から)', fin=3.0, fout=0.5),
         play(RV, V_T0 + V_CUT, GV * GV2, 0, V_CUT, 258.6 - V_CUT, 0, COLV, '光輪様の歌声 — 歌の後半'),
         play(R18, B18, 0.33, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま (4 小節から)'),
         play(R08, B8, 0.28, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部'),            # 歌の後半は静かに歌われているので、伴奏も控えめに
         play(R18, B18B, 0.24, 0, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(2, B18), (3, B8 + 27.0), (4, B18B + 40.0)]
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
    P.section(0, 'I. 光輪様の歌声とトラック 18 (♩=60)', '2 小節から歌声、4 小節からトラック 18 (ニ短調、そのまま)。どちらもゆっくり現れる')
    P.section(S2, 'II. 歌声とトラック 8', 'トラック 18 が消え、トラック 8 (4 度上げて) が前に出る。歌は 2 分 51 秒でひと息つき、3 分 3 秒から後半')
    P.section(S3, 'III. トラック 18 の後半、消える', '歌の終わり (4 分 25 秒) をトラック 18 の後半が受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid == RV:       # 歌声: 帯域を削らず、ステレオのまま、全体の残響を掛けずに前に (光輪の響きは声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'] if p['fin'] is not None else 0.05, fout=p['fout'] if p['fout'] is not None else 2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。入りは 6 秒で立ち上げる
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLV · Il canto dell\'aureola giovane',
        'subtitle': '2025/01/08 の歌を、ドエロの若い女性の光輪様の歌声にして、トラック 18 と 8 を重ねて。ニ短調、♩=60',
        'footer': ['歌声 = 2025/01/08 14:42 の歌 (ハ短調) から歌声を取り出し、14 半音上げてニ短調に。若い女性の響き、息と囁き、光輪 = 倍音の 2 声 (2 倍と 3 倍) と残響。',
                   '入りは tablet219 と同じ間合い: 2 小節から歌声、4 小節からトラック 18。歌の後半はトラック 8 (4 度上げて) に乗り、終わりをトラック 18 の後半が受ける。',
                   '楽器は何も加えない。歌は 1 回 (4 分 19 秒)。83 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=255, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
