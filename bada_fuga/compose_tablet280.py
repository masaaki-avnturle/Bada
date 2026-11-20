#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXX · Fuga che si fa Requiem (tablet117・tablet89・11/20 02:40 の鍵盤の録音の 3 曲を、フーガにレクイエムを醸すように)
  3 曲を、フーガの 3 つの声部のように順に入れる。楽器は何も加えない:
    1 つ目の声部  tablet89 (LXXXIX — Requiem e Fuga) のフーガ I・フーガ II・ストレッタ。4 半音下げて (テープのように速さごと、0.794 倍速) 変ロ短調に —
                  ゆっくり深いフーガ。フーガ I は主題が 1 声だけで始まる、本物のフーガの提示部
    2 つ目の声部  鍵盤の録音の前半 (黒い鍵盤、変ロ短調)。tablet276 と同じ音 (level273.py で強弱の幅を 4 割に)。高さも速さもそのまま
    3 つ目の声部  tablet117 (CXVII — Ninna nanna 10/03、眠りへの曲) の後半 — 眠りの段 (変ロ短調) から、変ロ長調の共鳴で閉じる所まで。そのまま
  調: 3 曲とも変ロ短調にそろう — tablet117 は変ロ短調で始まり変ロ長調で閉じる、鍵盤の前半は黒い鍵盤 (変ロ短調 / 変ニ長調)、tablet89 (ニ短調) は 4 半音下げて。
    鍵盤の後半 (白い鍵盤、イ短調) は tablet117 と濁る (どう移しても 0.34 以上) ので使わない
  レクイエムを醸す: tablet89 の段落を「フーガ → レクイエム」の順に並べ直す (どの段落も切れ目で切る): フーガ I → フーガ II → ストレッタ (ここまで元の順) →
    Requiem I → Amen (変ロ長調)。フーガが進むにつれて声部が増え、ストレッタで 3 つがそろい、そのままレクイエムに変わって、Amen で閉じる
  重ねる位置 (濁りの指数): 並べ方 6 通りと、鍵盤・tablet117 の入りを 4 秒ずつ (段落の継ぎ目を決めてからは 1 秒ずつ) 動かして、3 組 (tablet89 と鍵盤、tablet89 と tablet117、鍵盤と tablet117) の
    重みつきの平均がいちばん小さい所 (0.20; これまでのテープどうしは 0.15〜0.27)。tablet117 は元の 575 秒 (眠りの段の手前の静けさの終わり) から入り、
    元の 778 秒 (変ロ長調の終わり) が Amen の終わりに重なる
  形 (初めの 2 小節は無音):
    I:   フーガ I (2 小節から) — 主題が 1 声で始まり、26 秒から鍵盤が 2 つ目の声部として小さく入る →
    II:  フーガ II — 別の主題 (09/24 08:53) の 4 声フーガ →
    III: ストレッタ — 6 つの主題が次々に。tablet117 が 3 つ目の声部として入る →
    IV:  Requiem I — 伸ばした主題がゆっくり。鍵盤が流れて前半の山を築き、止まる。tablet117 は変ロ長調の共鳴へ →
    V:   Amen (変ロ長調)。tablet117 の変ロ長調の終わりと一緒に閉じる
  和音の表示は tablet89 の採譜 (4 半音下げて)。♩=60 は目盛り (4 半音下げた tablet89 は ♩=48 前後)
  使い方: python compose_tablet280.py <wav のフォルダ (20261107_089000.wav = tablet89 の音, 20261107_117000.wav = tablet117 の音,
          20261120_024046.wav = level273.py を通した鍵盤の録音)> <chords280.json (analyze_chords.py の出力)> [score_tablet280.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet280.json'
G89 = float(os.environ.get('G89', '0.30'))                                            # tablet89 (1 つ目の声部) の音量
GK = float(os.environ.get('GK', '0.35'))                                              # 鍵盤 (2 つ目の声部) の音量 (tablet276 の 0.31 より 1 dB 大きく — 1 声のフーガに並ぶように)
G117 = float(os.environ.get('G117', '0.42'))                                          # tablet117 (3 つ目の声部) の音量 — ほかの 2 つとそろうように
K0 = float(os.environ.get('K0', '21.0'))                                              # 鍵盤: 録音の f 秒は曲の f + K0 秒 (最初の音は録音の 5.0 秒)
O7 = float(os.environ.get('O7', '-406.0'))                                            # tablet117: 録音の t 秒は曲の t + O7 秒
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
R89, R117, RK = '20261107_089000', '20261107_117000', '20261120_024046'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S89 = -4; R4 = RATE(S89)
COL89, COLK, COL117 = (190, 160, 240), (140, 200, 235), (235, 205, 150)
XF = 1.0                                        # 段落の継ぎ目: 曲の 1 秒ずつ重ねて渡す
# tablet89 の段落 (元の秒): フーガ I、フーガ II とストレッタ (元で続いている)、Requiem I、Amen。継ぎ目は元の音量の谷か段落の境
CLIPS = [('フーガ I — 主題が 1 声で始まる', 96.0, 161.0), ('フーガ II、ストレッタ', 256.0, 367.5), ('Requiem I', 0.0, 98.0), ('Amen (変ロ長調)', 368.0, 391.0)]
T0 = 8.0                                        # フーガ I の入り: 2 小節
HEADS = []; t = T0
for name, a, b in CLIPS:
    HEADS.append(t); t += (b - a) / R4 - XF
END89 = t + XF                                  # tablet89 の終わり
K_END = 305.0                                   # 鍵盤は前半だけ: 録音の 0〜305 秒 (305 秒で止まる — 白い鍵盤の前の間)
S7 = 575.0                                      # tablet117: 元の 575 秒 (眠りの段の手前の静けさの終わり) から終わりまで
TOTAL = int(math.ceil((END89 + 4.0) / 4.0))
S2 = int(round(HEADS[1] / 4.0)); S3 = int(round((HEADS[1] + (320.0 - 256.0) / R4) / 4.0)); S4 = int(round(HEADS[2] / 4.0)); S5 = int(round(HEADS[3] / 4.0))
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = []
for k, (name, a, b) in enumerate(CLIPS):
    PLAYS.append(play(R89, HEADS[k], G89, S89, a, b - a, 0, COL89, 'tablet89 — %s (4 半音下げて)' % name,
                      fin=(1.0 if k == 0 else XF * R4), fout=(3.0 if k == len(CLIPS) - 1 else XF * R4)))
PLAYS.append(play(RK, K0, GK, 0, 0.0, K_END, 1, COLK, '11/20 02:40 の鍵盤の録音 — 前半 (黒い鍵盤)、tablet276 と同じ音', fin=0.5, fout=1.0))
PLAYS.append(play(R117, S7 + O7, G117, 0, S7, 778.5 - S7, 2, COL117, 'tablet117 — 眠りの段から終わりまで', fin=3.0, fout=3.0))
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): tablet89 の段落
LEAD = [(k, HEADS[k]) for k in range(len(CLIPS))]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Bbm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0) * RATE(p['semis'])   # 録音の中の秒
            cur = shift_chord(c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)], p['semis'])
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def mmss(s): return '%d 分 %d 秒' % divmod(int(round(s)), 60)
def build():
    P_ = Piece(TOTAL)
    for q in range(TOTAL * BPB): P_.harm[q] = harm_at(q)
    for k in range(TOTAL): P_.tempo[k] = BPM; P_.dyn[k] = 0.5
    for v in VOICES: P_.rest_bars(v, 0, TOTAL)
    P_.section(0, 'I. フーガ I — 主題が 1 声で (♩=60)', '2 小節から tablet89 のフーガ I (4 半音下げて、変ロ短調、ゆっくり)。%d 秒から鍵盤が 2 つ目の声部として' % round(K0 + 5.0))
    P_.section(S2, 'II. フーガ II', '別の主題 (09/24 08:53) の 4 声フーガ。鍵盤は黒い鍵盤のまま')
    P_.section(S3, 'III. ストレッタ — 3 つ目の声部', '6 つの主題が次々に。%s から tablet117 (眠りへの曲) が 3 つ目の声部として' % mmss(S7 + O7 + 5.0))
    P_.section(S4, 'IV. Requiem I — レクイエムが醸される', '伸ばした主題がゆっくり。鍵盤が山を築いて止まり (%s)、tablet117 は変ロ長調の共鳴へ' % mmss(K0 + 304.4))
    P_.section(S5, 'V. Amen (変ロ長調)', 'tablet117 の変ロ長調の終わりと一緒に閉じる')
    return P_

def post(P_, events, ex):
    for p in PLAYS:         # 3 曲とも、これまでの重ね方 (全体の残響)。移調はテープのように速さごと
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXX · Fuga che si fa Requiem',
        'subtitle': 'tablet89・11/20 の鍵盤・tablet117 の 3 曲を、フーガにレクイエムを醸すように。変ロ短調 → 変ロ長調、♩=60',
        'footer': ['3 曲をフーガの 3 つの声部のように順に入れる: tablet89 のフーガ (4 半音下げて、変ロ短調) → 鍵盤の黒い鍵盤 → tablet117 の眠りの段。',
                   'tablet89 はフーガ I → フーガ II → ストレッタ → Requiem I → Amen と並べ直す。フーガがストレッタで 3 声部になり、そのままレクイエムに変わる。',
                   '楽器は何も加えない。初めの 2 小節は無音。変ロ長調の Amen と、tablet117 の変ロ長調の終わりで閉じる。']}

if __name__ == '__main__':
    compose.main(OUT, seed=280, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), '| sections', S2, S3, S4, S5, TOTAL)
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.3f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
