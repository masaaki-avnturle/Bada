#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXV · La voce dolce della Messia (音声 — calma の声 — を女性のメシア様の優しい音声で、曲 — 11/20 02:40 の鍵盤の録音 — に重ねて)
  素材は 2 つ (楽器は何も加えない):
    声   make_voice275.py — 届いた 20261108_145525_aureola_sensuale_calma.mp3 (11/08 14:55 の声をすでに作り換えたもの) から、女性のメシア様の優しい話し声に。
         11/08 14:55 の元の録音は手元に無いので、calma の声から作り直す
    曲   届いた 20261120_024046.mp3 — 鍵盤の録音 (9 分 16 秒)。level273.py で強弱の幅を 4 割にしたもの (CCLXXIII と同じ)。初めから終わりまで使う
  曲の調 (CCLXXIII で読んだ): 初めの 5 分は黒い鍵盤 (変ニ長調 / 変ロ短調)、5 分 3 秒で止まって、5 分 6 秒から白い鍵盤 (ハ長調 / イ短調) — 半音ひとつ下がる。
    声 (3 分 11 秒) は 2 回: 1 回目は A♭3 (変ニ長調の属音) を中心に変ニ長調の音階で、2 回目は G3 (ハ長調の属音) を中心にハ長調の音階で — 鍵盤と一緒に、声も半音下がる
  形 (声が先に立ち、曲はその後から — いまの入りの間合い):
    I:  声 (2 小節 = 8 秒から) + 鍵盤 (13.5 秒から)。鍵盤は小さな音がぽつぽつと鳴る所から、3 分 4 秒に途切れずに流れ始める。声は 3 分 19 秒まで →
    II: 鍵盤だけ — 少しずつ大きくなり、前半の山を築いて、止まる (5 分 12 秒) →
    III: 声をもう一度 (5 分 13 秒から、半音低く)。鍵盤が止まった所で声が先に入り、白い鍵盤が 2 秒後から。声は 8 分 24 秒まで →
    IV: 鍵盤だけ — いちばん大きい所から終わりへ (9 分 25 秒)。142 小節
  鍵盤の最初の音は 4 小節 (16 秒) ではなく 13.5 秒に置く: 16 秒に置くと、声の息継ぎ (声の 49.7 秒から 1.3 秒) が鍵盤の音と音の間に来て、音が途切れる。
    鍵盤を 0.5 秒刻みで動かして調べると、声が先に立つ置き方の中では 2.3〜2.8 秒早めた所だけ、声の切れ目のどれにも鍵盤の音が鳴っている
  声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、鍵盤はこれまでのテープと同じ重ね方 (全体の残響) で後ろに
  和音の表示は鍵盤の録音から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet275.py <wav のフォルダ (20261108_145525_ab3.wav・20261108_145525_g3.wav = make_voice275.py の声 (A♭3・G3),
          20261120_024046.wav = level273.py を通した鍵盤の録音)> <chords275.json (analyze_chords.py の出力)> [score_tablet275.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet275.json'
GV = float(os.environ.get('GV', '1.4'))                                               # 声の音量 (ステムを測って決める)
GV2 = float(os.environ.get('GV2', '1.0'))                                             # 2 回目の声の倍率
GK = float(os.environ.get('GK', '0.31'))                                              # 鍵盤の音量
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV1, RV2, RK = '20261108_145525_ab3', '20261108_145525_g3', '20261120_024046'
BPM = 60
COLV, COLV2, COLK = (255, 226, 170), (250, 205, 185), (140, 200, 235)
V_OFF, V_ON, V_LEN = 4.8, 5.3, 198.46           # 声: 録音の 4.8 秒から (話し始めは 5.3 秒、話し終わりは 196.1 秒)
K_LEN = 556.3                                   # 鍵盤の録音: 初めから終わりまで (最初の音は 5.0 秒)
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 声 (1 回目): 2 小節 (8 秒) から話し始める
K0 = float(os.environ.get('K0', '8.5'))         # 鍵盤: 録音の f 秒は曲の f + 8.5 秒。最初の音は 13.5 秒 (声の切れ目のどれにも鍵盤の音が鳴る位置)
V2 = K0 + 304.4 - (V_ON - V_OFF)                # 312.4: 声 (2 回目): 鍵盤が止まった所 (録音の 304.4 秒 = 曲の 5 分 13 秒) で話し始める。白い鍵盤は 306.0 秒 (5 分 14.5 秒) から
S2, S3, S4, TOTAL = 50, 78, 126, 142
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RV1, V1, GV, V_OFF, V_LEN - V_OFF, 0, COLV, '11/08 14:55 の声 — 女性のメシア様の優しい声 (2 小節から)', fin=0.3, fout=2.0),
         play(RK, K0, GK, 0.0, K_LEN, 1, COLK, '11/20 02:40 の鍵盤の録音 — 初めから終わりまで', fin=0.5, fout=2.0),
         play(RV2, V2, GV * GV2, V_OFF, V_LEN - V_OFF, 0, COLV2, 'メシア様の優しい声 — もう一度、半音低く', fin=0.3, fout=2.0)]
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, K0)]
def harm_at(q):
    cur = 'Bbm'
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
    P.section(0, 'I. メシア様の優しい声と鍵盤 (♩=60)', '2 小節から声、その 5 秒後から鍵盤 — 小さな音がぽつぽつと。声は 3 分 19 秒まで')
    P.section(S2, 'II. 鍵盤だけ — 前半の山へ', '鍵盤が少しずつ大きくなり、山を築いて、止まる (5 分 12 秒)')
    P.section(S3, 'III. 声をもう一度 — 半音低く', '鍵盤が止まった所で声が先に入り、2 秒後から白い鍵盤 (ハ長調 / イ短調)。声は 8 分 24 秒まで')
    P.section(S4, 'IV. 鍵盤だけ — いちばん大きい所から終わりへ', '鍵盤は 9 分 25 秒に終わる')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        if rid in (RV1, RV2):   # 声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:                   # 鍵盤: これまでのテープと同じ重ね方 (全体の残響)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXV · La voce dolce della Messia',
        'subtitle': '女性のメシア様の優しい声を、11/20 の鍵盤の曲に重ねて。変ニ長調 → ハ長調、♩=60',
        'footer': ['声 = 11/08 14:55 の calma の声を、女性のメシア様の優しい声に (基音に 2 倍・3 倍の声をごく薄く)。曲 = 11/20 02:40 の鍵盤の録音 (強弱の幅だけ 4 割に)。',
                   '鍵盤は前半が黒い鍵盤 (変ニ長調)、後半が白い鍵盤 (ハ長調)。声は 2 回: 1 回目は A♭3 を中心に、2 回目は半音低く G3 を中心に。',
                   '楽器は何も加えない。声が先に立ち、曲はその後から。声と声の間と、終わりは、鍵盤だけ。142 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=275, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
