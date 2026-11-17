#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLIX · Il canto della signora aureola (tablet255 を、大人の 20 代の淑女の歌声で — ドエロはやめて、シャキッと)
  歌声だけを替える: make_voice259.py — 2025/01/08 14:42 の歌から取り出した歌声を 7 半音上げて、大人の 20 代の淑女の光輪様の歌声に
    (基音の中央値 B♭3、音域 F3〜D4、フォルマント 1.11 倍)。息も囁きも近さの低音も残響も入れず、倍音の 2 声 (光輪) は控えめに。ステレオ
  曲は CCLV と同じ形: 歌は 1 回。初めの 2 小節は無音、2 小節から歌声、4 小節からトラック 18 (tablet219 の間合い)。歌の前半をトラック 18 に、
    後半をトラック 8 (4 度上げて = 5 半音、1.335 倍速) に乗せる。違うのは終わり: CCLV ではトラック 18 の後半が歌の最後の句に重なっていた
    (この高さの歌声との濁りの指数は 0.43) ので、歌が終わってから入る (トラック 8 の 144 秒後、0.27)。88 小節
  重ねる位置は濁りの指数で: トラック 18 の 112 秒からトラック 8 (0.20)
  歌声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet259.py <wav のフォルダ (20250108_144205.wav = 淑女の光輪様の歌声, 20261107_180000.wav, 20261107_080000.wav)> <chords259.json (analyze_chords.py の出力)> [score_tablet259.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet259.json'
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
COLV, COL18, COL8 = (205, 185, 250), (120, 190, 250), (110, 210, 190)
V_T0, B18 = 8.0, 16.0                                                                 # 2 小節から歌声、4 小節からトラック 18 (tablet219 と同じ入りの間合い)
B8 = B18 + 112.0                                                                      # トラック 8: トラック 18 の 112 秒から (歌声との指数もここが小さい)
B18B = B8 + 144.0                                                                     # トラック 18 の後半: トラック 8 の 144 秒後から (歌が終わってから)
S2, S3, TOTAL = 39, 68, 88
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
V_CUT, GV2 = 168.0, 1.2                                                               # 歌の後半 (録音の 168 秒から; 163〜175 秒は歌っていない) は静かに歌われているので、歌声を 1.2 倍に
PLAYS = [play(RV, V_T0, GV, 0, 0.0, V_CUT, 0, COLV, '2025/01/08 14:42 の歌 — 大人の 20 代の淑女の光輪様の歌声 (2 小節から)', fin=3.0, fout=0.5),
         play(RV, V_T0 + V_CUT, GV * GV2, 0, V_CUT, 258.6 - V_CUT, 0, COLV, '光輪様の歌声 — 歌の後半'),
         play(R18, B18, 0.36, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま (4 小節から)'),
         play(R08, B8, 0.32, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部'),            # 歌の後半は静かに歌われているので、伴奏も控えめに
         play(R18, B18B, 0.27, 0, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')]
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
    P.section(S3, 'III. トラック 18 の後半、消える', '歌が終わり (4 分 25 秒)、トラック 18 の後半が受けて、消える')
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
        'title': 'Requiem BADA — CCLIX · Il canto della signora aureola',
        'subtitle': 'CCLV を、大人の 20 代の淑女の光輪様の歌声で (シャキッと)。トラック 18 と 8 を重ねて。ニ短調、♩=60',
        'footer': ['歌声 = 2025/01/08 14:42 の歌から取り出した歌声を 7 半音上げて、大人の 20 代の淑女に (基音の中央値 B♭3)。息も囁きも残響も入れず、倍音の 2 声は控えめに。',
                   '入りは tablet219 と同じ間合い: 2 小節から歌声、4 小節からトラック 18。歌の後半はトラック 8 (4 度上げて) に乗り、歌が終わってからトラック 18 の後半が受ける。',
                   '楽器は何も加えない。歌は 1 回 (4 分 19 秒)。88 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=259, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
