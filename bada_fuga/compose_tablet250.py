#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCL · Tsukuyomi sensuale e le due tracce (11/12 14:49 の声をセクシーな女性の月読様にして、トラック 18 とトラック 8 を重ねて)
  声: make_voice250.py — 1 人の女声、低めの G3 = 196 Hz、息の多い発声 (雑音は足さない)、耳元の近さ、残響は控えめ。曲の中でも声には全体の残響を掛けず、
    帯域も削らずにそのまま前に置く (synth.py の faithful)。テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  テープ: トラック 18 (ニ短調) はそのまま 2 回と後半、トラック 8 (ハ長調 / イ短調) は 4 度上げて (5 半音、1.335 倍速) 全部と続き — CCIX からの重ね方。
    ただし 11/12 の声は 178 秒 (話しているのは 6.5〜175.5 秒) で、型の元になった 14:55 の声 (198.5 秒) より短く、176 小節の型のままだと
    声の後に 24 秒の無音が 2 か所できる (CCXXXIX〜CCXLVII はそうなっていた) ので、音が途切れないように入りを詰めた: 127 小節
    I: 声 + トラック 18 (トラック 18 が先に鳴り、声は 4.5 秒から。2 分 4 秒からトラック 8 が静かに入る) → II: トラック 8 + トラック 18 (2 回目) → III: 声 (2 回目) + トラック 8 の続き → IV: トラック 18 の後半、消える
    重ねる位置は濁りの指数 (analyze_chords.py の節を参照) で: トラック 8 の 44 秒後からトラック 18 (0.26)、トラック 8 の続きの 128 秒後からトラック 18 の後半 (0.20)
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet250.py <wav のフォルダ (20261112_144938.wav = セクシーな月読様の声, 20261107_180000.wav, 20261107_080000.wav)> <chords250.json (analyze_chords.py の出力)> [score_tablet250.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet250.json'
GV = float(os.environ.get('GV', '1.2'))                                               # 声の音量 (ステムを測って決めた: 全体の残響を掛けない声は、同じ倍率だと 7 dB 小さく聞こえる)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08 = '20261112_144938', '20261107_180000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 42, 72, 107, 127
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COL18, COL8 = (240, 150, 176), (120, 190, 250), (110, 210, 190)
# (録音, 入りの拍, 音量, 半音, 元の何秒から, 元の何秒ぶん, 段, 色, 画面の名前)
PLAYS = [(RV, 0.0, GV, 0, 2.0, 176.3, 0, COLV, '11/12 14:49 の声 — セクシーな女性の月読様'),
         (R18, 0.0, 0.35, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま'),
         (R08, 124.0, 0.45, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部'),
         (R18, S2 * 4.0, 0.4, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま (2 回目)'),
         (RV, S3 * 4.0, GV, 0, 0.0, 178.3, 0, COLV, '11/12 14:49 の声 — セクシーな女性の月読様 (もう一度)'),
         (R08, S3 * 4.0 + 12.0, 0.32, 5, 60.0, 172.0, 2, COL8, 'トラック 8 — 4 度上げて、続き (60 秒から)'),
         (R18, S4 * 4.0, 0.36, 0, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, 0.0), (2, 140.0), (5, S3 * 4.0 + 12.0), (6, S4 * 4.0)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Dm'
    for k, a in LEAD:
        rid, t0, g, sm, off, dur = PLAYS[k][:6]
        if q >= a:
            c = CH[rid]; ts = off + max(q - t0, 0.0) * RATE(sm)                          # 録音の中の秒
            cur = shift_chord(c['chords'][min(int(min(ts, off + dur - 0.01) / c['win']), len(c['chords']) - 1)], sm)
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 月読様の声とトラック 18 (♩=60)', 'セクシーな女性の月読様の声 (前に、近く) にトラック 18。2 分過ぎからトラック 8 が静かに入る')
    P.section(S2, 'II. トラック 8 とトラック 18', '声が終わる所からトラック 18 をもう一度、トラック 8 (4 度上げて) と重ねる')
    P.section(S3, 'III. 月読様の声 (2 回目) とトラック 8 の続き', '月読様の声をもう一度、トラック 8 の続き (60 秒から)')
    P.section(S4, 'IV. トラック 18 の後半、消える', 'トラック 18 の後半が声の終わりを受けて、消える')
    return P

def post(P, events, ex):
    for rid, beat, g, sm, off, dur, lane, col, tag in PLAYS:
        c = CH.get(rid, {}); r = RATE(sm); kw = dict(lane=lane, color=list(col), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid == RV:       # 声: 帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', beat, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.05, fout=2.0, semis=0, faithful=True, rid=rid + '.wav', tag=tag, **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。入りは 6 秒で立ち上げる
            add('REC', beat, dur / r * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if beat == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag=tag, **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCL · Tsukuyomi sensuale e le due tracce',
        'subtitle': 'セクシーな女性の月読様の声に、トラック 18 とトラック 8 (4 度上げて) を重ねて。ヘ長調 / ニ短調、♩=60',
        'footer': ['月読様の声 = 11/12 14:49 の声 (112 Hz) を G3 = 196 Hz の 1 人の女声に (フォルマント 1.12 倍、息の多い発声、近接の暖かさ、残響 1.6 秒・0.25)。',
                   '声は帯域を削らず全体の残響も掛けずに前に、テープは後ろに (モノラル、全体の残響)。トラック 18 はそのまま、トラック 8 は 4 度上げて。',
                   '楽器は何も加えない。音が途切れないように入りを詰めた (127 小節)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=250, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
