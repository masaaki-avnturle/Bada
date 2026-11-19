#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXIII · Il canto dolce della Messia (音声を女性のメシア様の優しい音声で、曲 — 11/20 02:40 の鍵盤の録音 — に重ねて)
  素材は 2 つ (楽器は何も加えない):
    歌声  make_voice273.py — 2025/01/08 14:42 の歌 (男声、ハ短調) を、女性のメシア様の優しい歌声に。届いた aureola_donna_sensuale.mp3 は
          すでに作り換えた声なので、同じ元 (取り出した歌声) から作り直す
    曲    届いた 20261120_024046.mp3 — 鍵盤の録音 (9 分 16 秒、モノラル)。level273.py で強弱の幅を 4 割にしたもの (音量のつまみだけ)
  曲の調 (1 秒ごとのクロマで読んだ): 初めの 5 分は黒い鍵盤 — 変ニ長調 / 変ロ短調 (D♭ E♭ F G♭ A♭ B♭ C)。5 分 3 秒で止まって、5 分 6 秒から白い鍵盤 —
    ハ長調 / イ短調。半音ひとつ下がる。歌 (4 分 16 秒) はちょうど半分ずつに収まるので、2 回歌う:
    1 回目は 10 半音上げて変ロ短調 (基音の中央値 C♯4)、2 回目は 9 半音上げてイ短調 (C4) — 鍵盤と一緒に、歌も半音下がる。
    濁りの指数 (歌った音と鍵盤): 変ロ短調で前半に 0.34、イ短調で後半に 0.35 (逆にすると 0.42 / 0.44)。これまでの歌とテープは 0.33〜0.35
  形 (声が先に立ち、曲は 2 小節後から — いまの入りの間合い):
    I:  歌声 (2 小節 = 8 秒から、変ロ短調) + 鍵盤 (4 小節から)。鍵盤は小さな音がぽつぽつと鳴る所から →
    II: 鍵盤が途切れずに流れ始める (2 分 51 秒)。歌はひと息ついて (2 分 54 秒〜3 分 2 秒) 後半へ、4 分 24 秒まで →
    III: 鍵盤だけ — 前半の山を築いて、止まる (4 分 59 秒) →
    IV: 歌をもう一度 (4 分 59 秒から、イ短調)。鍵盤が止まった所で歌声が先に入り、白い鍵盤が 2 秒後から →
    V: 歌の後半 (7 分 53 秒から)、鍵盤のいちばん大きい所。鍵盤は 9 分 11 秒に終わり、歌声の最後の音が残る (9 分 15 秒)。140 小節
  鍵盤の録音は 20 秒から使う: 初めの 20 秒 (ごく小さい音が 3 回) を入れると、歌の長い息継ぎ (歌の 2 分 47 秒〜2 分 54 秒) が、鍵盤がまだぽつぽつとしか
    鳴っていない所に来て、4.5 秒のあいだ音が途切れる。20 秒から使うと、歌の息継ぎは鍵盤が流れ始めた後に来る (声が先に立つ入りはそのまま)
  歌声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、鍵盤はこれまでのテープと同じ重ね方 (全体の残響) で後ろに
  和音の表示は鍵盤の録音から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet273.py <wav のフォルダ (20250108_144205_p10.wav・20250108_144205_p9.wav = make_voice273.py の歌声 (10 半音・9 半音),
          20261120_024046.wav = level273.py を通した鍵盤の録音)> <chords273.json (analyze_chords.py の出力)> [score_tablet273.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet273.json'
GS = float(os.environ.get('GS', '1.4'))                                               # 歌声の音量 (ステムを測って決める)
GS2 = float(os.environ.get('GS2', '1.15'))                                            # 歌の後半は静かに歌われているので、少し上げる (CCLXIX と同じ)
GK = float(os.environ.get('GK', '0.26'))                                              # 鍵盤の音量
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RS1, RS2, RK = '20250108_144205_p10', '20250108_144205_p9', '20261120_024046'
BPM = 60
COLS, COLS2, COLK = (255, 226, 170), (250, 205, 185), (140, 200, 235)
S_LEN, S_ON, S_CUT = 258.6, 0.4, 168.0          # 歌: 258.6 秒、歌い出しは 0.4 秒、歌い終わりは 256.4 秒。後半は 168 秒から (166.5〜174.4 秒は歌っていない)
K_LEN, K_OFF = 556.3, 20.0                      # 鍵盤の録音: 20 秒から終わりまで (21.0 秒の音が最初に聞こえる)
VS1 = 8.0 - S_ON                                # 7.6: 歌 (1 回目): 2 小節 (8 秒) から歌い出す
K0 = 16.0 - (21.0 - K_OFF)                      # 15.0: 鍵盤: 最初の音が 4 小節 (16 秒) に鳴る。録音の f 秒は曲の f − 5 秒
VS2 = K0 + (304.4 - K_OFF) - S_ON               # 299.0: 歌 (2 回目): 鍵盤が止まった所 (録音の 304.4 秒 = 曲の 4 分 59 秒) で歌い出す。白い鍵盤は 306.0 秒 (5 分 1 秒) から
S2, S3, S4, S5, TOTAL = 43, 66, 75, 118, 140
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
def song(rid, beat, color, tag, tag2):          # 歌を 2 つに分けて置く (歌っていない所で分けて、後半を少し上げる。歌の音は変えない)
    return [play(rid, beat, GS, 0.0, S_CUT, 0, color, tag, fin=0.3, fout=0.5),
            play(rid, beat + S_CUT, GS * GS2, S_CUT, S_LEN - S_CUT, 0, color, tag2, fin=0.05, fout=2.0)]
PLAYS = (song(RS1, VS1, COLS, '2025/01/08 14:42 の歌 — 女性のメシア様の優しい歌声、変ロ短調で (2 小節から)', 'メシア様の歌声 — 歌の後半') +
         [play(RK, K0, GK, K_OFF, K_LEN - K_OFF, 1, COLK, '11/20 02:40 の鍵盤の録音 — 20 秒から終わりまで (4 小節から)', fin=0.5, fout=2.0)] +
         song(RS2, VS2, COLS2, 'メシア様の歌声 — もう一度、半音低くイ短調で', 'メシア様の歌声 — 歌の後半'))
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍)
LEAD = [(2, K0)]
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
    P.section(0, 'I. メシア様の歌声と鍵盤 (♩=60)', '2 小節から歌声 (変ロ短調)、4 小節から鍵盤 — 小さな音がぽつぽつと')
    P.section(S2, 'II. 鍵盤が流れ始める', '歌は 2 分 54 秒でひと息つき、3 分 2 秒から後半。歌は 4 分 24 秒まで')
    P.section(S3, 'III. 鍵盤だけ — 前半の山', '歌が終わり、鍵盤が前半の山を築いて、止まる')
    P.section(S4, 'IV. 歌をもう一度 — 半音低く、イ短調で', '鍵盤が止まった所で歌声が先に入り、2 秒後から白い鍵盤 (ハ長調 / イ短調)')
    P.section(S5, 'V. 歌の後半、鍵盤のいちばん大きい所', '鍵盤は 9 分 11 秒に終わり、歌声の最後の音が残る (9 分 15 秒)')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        if rid in (RS1, RS2):   # 歌声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:                   # 鍵盤: これまでのテープと同じ重ね方 (全体の残響)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXIII · Il canto dolce della Messia',
        'subtitle': '女性のメシア様の優しい歌声を、11/20 の鍵盤の曲に重ねて。変ロ短調 → イ短調、♩=60',
        'footer': ['歌声 = 2025/01/08 の歌を、女性のメシア様の優しい歌声に (基音に 2 倍・3 倍の声をごく薄く)。曲 = 11/20 02:40 の鍵盤の録音 (強弱の幅だけ 4 割に)。',
                   '鍵盤は前半が黒い鍵盤 (変ニ長調 / 変ロ短調)、後半が白い鍵盤 (ハ長調 / イ短調)。歌は 2 回: 1 回目は変ロ短調、2 回目は半音低くイ短調で。',
                   '楽器は何も加えない。声が先に立ち、曲は 2 小節後から。鍵盤が終わった後、歌声の最後の音が残る。140 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=273, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
