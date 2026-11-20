#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXIII · Sollievo e mente chiara (tablet280・tablet281・tablet282 をミックス — ホッと一安心して、頭に仕切りができる曲に)
  届いた言葉は薬にたとえた気分。薬の働きを音で作ることはできないので、言葉が指している気分を音の言葉に直した:
    ホッと一安心 (不安をほどく薬と、眠りに入る薬を合わせたように)   → 小さな音量、やわらかい打鍵 (tablet282 の仕上げ)、短調の夜が長調の Amen で解ける
    バタンキューにならない (急に上がって、急に落ちない)            → 段落ごとの大きさを揃える (差は数 dB)。山を作らず、消え入らず、はっきりした和音で閉じる
    思考に仕切りができる                                           → 仕切り = 段落。フーガ (声部が順番に入る) を骨組みに、7 つの段落を小節の線に揃える。
                                                                      段落の大きな境目は同じ 1 つの音 (ファ)
    抗うつ (気分が上がる)                                          → 調が明るくなっていく: 変ロ短調 (夜) → 変ロ長調 (Amen) → ハ長調 (白い鍵盤)
  素材は 3 曲の中の段 (ステム) だけ (make_stems283.py; 楽器は何も加えない、速さも音の高さも変えない)。3 曲とも同じ 11/20 02:40 の鍵盤の録音が入っているので、
  できあがった曲をそのまま重ねず、段に分けて、鍵盤が 3 つ重ならないように混ぜ直した。3 曲の役割:
    tablet280 (フーガがレクイエムに変わって閉じる)  → 骨組み。フーガ I → フーガ II → ストレッタ → Requiem I → Amen を、そのままの順で、そのままの位置で。tablet117 の段も
    tablet282 (聖夜のしっとりするレクイエム)        → 夜の鍵盤。tablet280 の鍵盤の段を、同じ録音・同じ位置の tablet282 の鍵盤 (しっとりの仕上げ) に置き換える。
                                                       11/21 の鍵盤の黒い鍵盤の出だしも、tablet282 と同じ位置 (フーガ II の入り) に
    tablet281 (2 つの鍵盤のミックス)                → 光。白い鍵盤の二重奏は、tablet281 と tablet282 を同じ位置で半分ずつ重ねる (同じ録音なので、濁らずに 1 つの音になる)
  形 (♩=60、4 秒 = 1 小節):
    I.   Fuga I (0 小節)        2 小節 (8 秒) からフーガの主題が 1 声で。26 秒から 11/20 の鍵盤の小さな音
    II.  Fuga II (22 小節)      別の主題の 4 声フーガ。1 分 24 秒から 2 分 18 秒まで、11/21 の鍵盤の黒い鍵盤の出だし
    III. Stretto (42 小節)      主題が次々に。2 分 54 秒から tablet117 (眠りの曲)。3 分 17 秒から鍵盤が流れ始める
    IV.  Requiem I (57 小節)    伸ばした主題がゆっくり。鍵盤は 5 分 22 秒、ファの手前で止まる
    V.   Amen (88 小節)         変ロ長調。ホッと一安心
    VI.  Luce (92 小節)         6 分 8 秒、2 つの鍵盤が同じファで入り、白い鍵盤 (ハ長調 / イ短調) へ。11/21 は 7 分 27 秒から 28 秒休む
    VII. Chiarezza (119 小節)   7 分 55 秒から、また 2 つで。9 分 58 秒に山。11/20 の最後の音 (ファ・ラ) の上で、11/21 がシ・ファからド・ミへ閉じる (10 分 20 秒)。158 小節
  仕切りのファ: 鍵盤の録音は 2 つとも、黒い鍵盤から白い鍵盤へ移る最初の音がファ。ファは変ロ長調の 5 番目の音で、ハ長調の 4 番目の音。
    Amen (変ロ長調) の余韻の上にファが 1 つ鳴って、白い鍵盤 (ハ長調) が始まる
  終わり: 11/21 の鍵盤は、白い鍵盤の終わりでシ・ファ (ソの和音) からド・ミへ進む。ハ長調のはっきりした終止。その 0.8 秒後に黒い鍵盤へ戻るので、
    戻る手前で止めた (make_stems283.py)。響きの尾は残る
  和音の表示は、Amen まではフーガの段から、ファからは 11/20 の鍵盤から読んだもの
  使い方: python compose_tablet283.py <ステムのフォルダ (make_stems283.py の出力)> <chords283.json (ステム 6 つを analyze_chords.py に通したもの)> [score_tablet283.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet283.json'
E = lambda k, v: float(os.environ.get(k, v))
# 段ごとの大きさ (dB): その段が元の曲の中で鳴っていた大きさからの差
D_F1, D_F2 = E('D_F1', '-5.0'), E('D_F2', '-1.5')           # フーガの段: 鍵盤と重なる間 / 鍵盤が止まってから (Requiem I の終わりと Amen)
D_T1, D_T2 = E('D_T1', '-6.0'), E('D_T2', '0.0')            # tablet117 の段: 同じく
D_A1, D_B1 = E('D_A1', '-2.5'), E('D_B1', '0.5')            # 夜の鍵盤 (tablet282): 11/20 / 11/21 の出だし — フーガの少し後ろに
D_281, D_282 = E('D_281', '-10.3'), E('D_282', '-5.0')      # 白い鍵盤の二重奏: tablet281 と tablet282 を、同じ大きさになるように半分ずつ
IN_281 = 12.0                                               # tablet281 の方は、ファから 12 秒かけて入る (ファそのものは tablet282 のやわらかい音だけで、そっと鳴る)
FIXPEAK = E('FIXPEAK', '1.31')                               # 仕上げの大きさ (synth.py の基準): 曲の平均が −19.5 dB になる所 (曲の山は 0.729)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
import numpy as np, soundfile as sf
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (ステムだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
FUGA, T117, A281, B281, A282, B282 = 's280_fuga', 's280_117', 's281_a', 's281_b', 's282_a', 's282_b'
def file_rms(rid):                                              # ステム全体の rms (synth.py はこれを 0.1 に揃えるので、倍率で元の大きさに戻す)
    cp = os.path.join(WDIR, 'rms283.json'); c = json.load(open(cp)) if os.path.exists(cp) else {}
    if rid not in c:
        s = 0.0; n = 0
        with sf.SoundFile(os.path.join(WDIR, rid + '.wav')) as f:
            for blk in f.blocks(blocksize=1 << 20, dtype='float32', always_2d=True): s += float((blk.astype(np.float64) ** 2).sum()); n += blk.size
        c[rid] = math.sqrt(s / n); json.dump(c, open(cp, 'w'))
    return c[rid]
def G(rid, d): return 10 ** (d / 20.0) * file_rms(rid) / (0.1 * 0.707)   # その段を、元の曲の中の大きさ + d dB で鳴らす倍率
BPM = 60
COLF, COLT, COLA, COLB = (200, 180, 240), (160, 215, 190), (150, 195, 240), (245, 215, 150)
KB1 = 18.0                                      # 夜の鍵盤: tablet282 の t 秒は曲の t + 18 秒 (tablet280 の鍵盤と同じ位置 — 鍵盤の録音の f 秒は曲の f + 21 秒)
T_F = 368.0                                     # 仕切りのファ (92 小節)
KB2 = T_F - 304.013                             # 63.987: 白い鍵盤: tablet281・282 の t 秒は曲の t + 63.987 秒 (どちらもファは 304.013 秒)
X1, XF = 322.0, 4.0                             # 鍵盤が止まる所 (5 分 22 秒)。ここからフーガの段を 4 秒かけて、tablet117 の段を 16 秒かけて持ち上げる
A_CUT = 303.90                                  # 鍵盤の切れ目: ファ (304.013 秒) の直前
A_END, A_FADE = 556.00, 1.4                     # 11/20 の鍵盤の終わり: 最後の音 (ファ・ラ、553.70 秒) の後、録音の終わりのかすかな物音 (556.05 秒から) の手前で消す
S2, S3, S4, S5, S6, S7, TOTAL = 22, 42, 57, 88, 92, 119, 158
def play(rid, beat, d, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=G(rid, d), off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [# tablet280 の骨組み: フーガ I → フーガ II → ストレッタ → Requiem I → Amen (そのままの位置)
         play(FUGA, 0.0, D_F1, 0.0, X1 + XF, 0, COLF, 'tablet280 — フーガ (tablet89 を 4 半音下げたもの)。2 小節から', fin=0.05, fout=XF),
         play(FUGA, X1, D_F2, X1, 391.0 - X1, 0, COLF, '', fin=XF, fout=2.0),
         play(T117, 160.0, D_T1, 160.0, X1 - 160.0 + 16.0, 1, COLT, 'tablet280 — tablet117 (眠りの曲)', fin=1.0, fout=16.0),
         play(T117, X1, D_T2, X1, 391.0 - X1, 1, COLT, '', fin=16.0, fout=2.0),
         # tablet282 の夜の鍵盤 (しっとりの仕上げ)
         play(A282, KB1 + 4.0, D_A1, 4.0, A_CUT - 4.0, 2, COLA, 'tablet282 — 11/20 の鍵盤 (しっとりの仕上げ)', fin=0.5, fout=0.9),
         play(B282, KB1 + 64.0, D_B1, 64.0, 68.0, 3, COLB, 'tablet282 — 11/21 の鍵盤の出だし', fin=0.5, fout=4.0),
         # 白い鍵盤の二重奏: tablet281 と tablet282 を同じ位置で半分ずつ
         play(A282, KB2 + A_CUT, D_282, A_CUT, A_END - A_CUT, 2, COLA, 'tablet282 + tablet281 — 11/20 の鍵盤 (同じファから)', fin=0.08, fout=A_FADE),
         play(A281, KB2 + A_CUT, D_281, A_CUT, A_END - A_CUT, 2, COLA, '', fin=IN_281, fout=A_FADE),
         play(B282, KB2 + 303.85, D_282, 303.85, 265.15, 3, COLB, 'tablet282 + tablet281 — 11/21 の鍵盤 (同じファから)', fin=0.05, fout=1.0),
         play(B281, KB2 + 303.85, D_281, 303.85, 262.15, 3, COLB, '', fin=IN_281, fout=1.0)]
# 和音の表示を担う段 (PLAYS の番号, 表示の始まりの拍)
LEAD = [(0, 8.0), (1, X1 + XF), (6, T_F)]
def harm_at(q):
    cur = 'Bbm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0)                        # ステムの中の秒
            cur = c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)]
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 5), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(0, 'I. Fuga I — 声が順番に入る (♩=60)', '2 小節からフーガの主題が 1 声で (変ロ短調)。26 秒から 11/20 の鍵盤の小さな音')
    P.section(S2, 'II. Fuga II — 2 つの夜の小さな音', '別の主題の 4 声フーガ。1 分 24 秒から 11/21 の鍵盤の出だしが、同じ黒い鍵盤で重なる')
    P.section(S3, 'III. Stretto — 眠りの曲が入る', '主題が次々に。2 分 54 秒から tablet117。3 分 17 秒から鍵盤が流れ始める')
    P.section(S4, 'IV. Requiem I — ゆっくり', '伸ばした主題がゆっくり。鍵盤は 5 分 22 秒、ファの手前で止まる')
    P.section(S5, 'V. Amen — ホッと一安心 (変ロ長調)', '短調の夜が、長調の Amen で解ける')
    P.section(S6, 'VI. Luce — 同じファから、白い鍵盤へ', '6 分 8 秒、2 つの鍵盤が同じファで入り、白い鍵盤 (ハ長調 / イ短調) へ。11/21 は 7 分 27 秒から休む')
    P.section(S7, 'VII. Chiarezza — 2 つで、はっきり閉じる', '7 分 55 秒から、また 2 つで。9 分 58 秒に山。10 分 20 秒、ド・ミで閉じる')
    return P

def post(P, events, ex):
    for p in PLAYS:         # どの段も、元の曲の中の音のまま (synth.py の faithful の経路: 帯域を削らず、響きも足さない — 響きは段の中にある)
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4], 'fixed_peak': FIXPEAK,
        'title': 'Requiem BADA — CCLXXXIII · Sollievo e mente chiara',
        'subtitle': 'tablet280・281・282 をミックス。ホッとして、頭に仕切りができる曲に。変ロ短調 → ハ長調、♩=60',
        'footer': ['tablet280 (フーガ → レクイエム → Amen) を骨組みに、tablet282 のしっとりした鍵盤を夜に、tablet281 と 282 の白い鍵盤を光に。',
                   '3 曲の中の段だけ。楽器は何も加えない。速さも音の高さも変えない。段落の大きさを揃え、山を作らず、はっきり閉じる。',
                   '仕切りは同じファの音。変ロ短調の夜 → 変ロ長調の Amen → ハ長調の白い鍵盤。ド・ミで終わる。158 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=283, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for e in d['extras']: print('  %7.2f - %7.2f s  gain %.4f  off %7.2f  %s  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['off'], e['rid'], e['tag']))
