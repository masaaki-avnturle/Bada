#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXVIII · La diciassettenne e la mia voce (tablet266 と、取り出した歌声を重ねて)
  届いたもの: tablet266.mp4 (CCLXVI: 倍音の 3 声の 17 歳の声・トラック 18・トラック 8、ヘ長調 / ニ短調) と、
    recording_20250108_144205_voce_sola.mp3 (2025/01/08 14:42 の録音から取り出した作曲者の歌声そのもの、ハ短調)
  調が違う (全音ひとつ) ので、そのまま重ねると濁る。歌声は変えない (CCLX からの決め)。mp4 の音をまるごと 2 半音下げると、
    中の 17 歳の声まで低く遅くなって 17 歳ではなくなる (フォルマント 1.19 → 1.06 倍、1.12 倍の遅さ)。
    そこで mp4 の混ざった音は使わず、tablet266 の素材から組み直す:
      17 歳の声    make_voice266.py の声そのまま (話し声なので移さない。基音の中心 B♭3 と、その 2 倍・3 倍の B♭4・F5 はハ短調の音)
      トラック 18  2 半音下げてハ短調に (0.891 倍速)
      トラック 8   3 半音上げて変ホ長調 / ハ短調に (1.189 倍速) — テープどうしの高さの関係は tablet266 のまま
      歌声        voice_only255.py の声そのまま (高さも速さも響きも変えない、残響も足さない)
  形: tablet266 の並び (2 小節から声、4 小節からトラック 18 の出だしの一節を 3 回 → トラック 18 → トラック 8 → トラック 18 の 2 回目 →
      声の 2 回目とトラック 8 の続き → トラック 18 の後半) の、テープだけになる間の所に歌を置く。歌は 4 分 19 秒あるので、そのぶん間が長い。
      テープの並べ方は CCLX (同じ移調、164 小節) のもの:
    I: 17 歳の声 + トラック 18 の出だしが 3 回 → II: 17 歳の声 + トラック 18 → III: 歌声 + トラック 8 → IV: 歌の後半 + トラック 18 (2 回目) →
    V: 17 歳の声 (2 回目) + トラック 8 の続き → VI: トラック 18 の後半、消える。話し声と歌声は重ねない (どちらの言葉も聞こえるように)
  重ねる位置 (濁りの指数): トラック 18 の 117 秒からトラック 8 (0.19)、トラック 8 の 150 秒後 (元の速さで) からトラック 18 の 2 回目 (0.21)、
    トラック 18 の 128 秒からトラック 8 の続き (0.17)、その 52 秒後 (元の速さで) からトラック 18 の後半 (0.25)。
    歌の入り (3 分 4 秒) は、歌った音で測ったテープとの指数が 0.33 (4 秒ずつ動かしても 0.32〜0.35 で変わらない)。3 分ちょうどに置くと、
    トラック 8 の短い休み (曲の 5 分 5〜9 秒) と歌の息継ぎが同じ瞬間に重なって 0.5 秒だけ −39 dB まで静まるので、4 秒遅らせて歌の句で覆う
  声と歌声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (移調して、ハ短調の綴りで)。♩=60
  使い方: python compose_tablet268.py <wav のフォルダ (20250108_144205.wav = 取り出した歌声, 20261112_144938.wav = make_voice266.py の声,
          20261107_180000.wav, 20261107_080000.wav)> <chords268.json (analyze_chords.py の出力)> [score_tablet268.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet268.json'
GS = float(os.environ.get('GS', '1.1'))                                               # 歌声の音量 (ステムを測って決める)
GP = float(os.environ.get('GP', '1.0'))                                               # 17 歳の声の音量
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RS, RP, R18, R08 = '20250108_144205', '20261112_144938', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S18, S8 = -2, 3                                 # テープの移調 (歌のハ短調に)
COLP, COLS, COL18, COL8 = (255, 200, 205), (250, 215, 150), (120, 190, 250), (110, 210, 190)
S_LEN, S_CUT, GS2 = 258.6, 168.0, 1.35          # 歌の後半 (録音の 168 秒から; 163〜175 秒は歌っていない) は静かに歌われていて、トラック 18 の 2 回目の山と重なるので、歌声を 1.35 倍に
P_OFF, P_LEN = 6.0, 178.3                       # 17 歳の声: 録音の 6.0 秒から (話し始めは 6.5 秒)
P1 = 7.5                                        # 17 歳の声 (1 回目): 2 小節 (8 秒) から話し始める
G_OFF, G_DUR, G_PER = 0.70, 14.8, 14.7 / RATE(S18)    # トラック 18 の出だしの一節: 元の 0.70 秒から 14.8 秒ぶん、くり返しの周期は遅くして 16.5 秒
G_T0, G_GAINS, G18 = 16.0, (0.10, 0.145, 0.205), 0.28 # 1 回目の入りの拍 (4 小節 = 声の 2 小節後)、3 回の音量、本来の音量
TP = G_T0 + len(G_GAINS) * G_PER                # 65.5: 4 回目の出だし = そのまま曲へ
B8 = 196.0                                      # トラック 8: トラック 18 の 117 秒から
VS = 184.0                                      # 歌声: 17 歳の声が終わった所 (2 分 57 秒) の後、3 分 4 秒から (トラック 8 の短い休みを歌の句で覆う位置)
B18_2 = 364.0                                   # トラック 18 の 2 回目: トラック 8 の 168 秒後 (元の速さで 150 秒後)
P2 = 443.5                                      # 17 歳の声 (2 回目): 歌が終わった所 (7 分 21 秒) の後、7 分 24 秒から話し始める
B8C = 508.0                                     # トラック 8 の続き (元の 60 秒から): トラック 18 (2 回目) の 128 秒から
B18H = 566.0                                    # トラック 18 の後半 (元の 60 秒から): トラック 8 がひと息つく所を埋める
S2, S3, S4, S5, S6, TOTAL = 16, 46, 91, 111, 142, 164
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
PLAYS = [play(RP, P1, GP, 0, P_OFF, P_LEN - P_OFF, 0, COLP, '11/12 14:49 の声 — 倍音の 3 声の、17 歳のホッとする声 (2 小節から)', fin=1.0)]
for k, g in enumerate(G_GAINS):
    PLAYS.append(play(R18, G_T0 + k * G_PER, g, S18, G_OFF, G_DUR, 2, COL18, 'トラック 18 の出だしの一節 — %d 回目%s' % (k + 1, ' (声の 2 小節後から)' if k == 0 else ' (少し大きく)'),
                      fin=5.0 if k == 0 else 0.05, fout=0.25, envk=g / G18))
PLAYS += [play(R18, TP, G18, S18, G_OFF, 149.1 - G_OFF, 2, COL18, 'トラック 18 — 2 半音下げて、4 回目の出だしからそのまま曲へ', fin=0.05),
          play(RS, VS, GS, 0, 0.0, S_CUT, 1, COLS, '2025/01/08 14:42 の歌 — 取り出した歌声そのもの', fin=1.5, fout=0.5),
          play(RS, VS + S_CUT, GS * GS2, 0, S_CUT, S_LEN - S_CUT, 1, COLS, '歌声 — 歌の後半'),
          play(R08, B8, 0.30, S8, 0.0, 232.0, 3, COL8, 'トラック 8 — 3 半音上げて、全部'),
          play(R18, B18_2, 0.26, S18, 0.0, 149.1, 2, COL18, 'トラック 18 — 2 半音下げて (2 回目)'),   # 歌の後半と 2 回目の声の下なので、少し控えめに
          play(RP, P2, GP, 0, P_OFF, P_LEN - P_OFF, 0, COLP, '17 歳の声 — もう一度', fin=1.0),
          play(R08, B8C, 0.30, S8, 60.0, 172.0, 3, COL8, 'トラック 8 — 3 半音上げて、続き (60 秒から)'),
          play(R18, B18H, 0.24, S18, 60.0, 80.0, 2, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, G_T0), (2, G_T0 + G_PER), (3, G_T0 + 2 * G_PER), (4, TP), (7, B8 + 34.0), (8, B18_2 + 26.0), (10, B8C + 12.0), (11, B18H + 78.0)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return {'G#': 'Ab', 'C#': 'Db'}.get(compose.NAMES[(PC[name[:i]] + semis) % 12], compose.NAMES[(PC[name[:i]] + semis) % 12]) + name[i:]   # ハ短調の綴りで (A♭・D♭)
def harm_at(q):
    cur = 'Cm'
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
    P.section(0, 'I. 音声と曲のズレ — 17 歳の声、2 小節後にトラック 18 (♩=60)', '2 小節から声、4 小節からトラック 18 の出だしの一節 (低音が C から G へ下りる) が 3 回、少しずつ大きく')
    P.section(S2, 'II. 17 歳の声とトラック 18', '4 回目の出だしから、トラック 18 はそのまま先へ。声は 2 分 57 秒で終わる')
    P.section(S3, 'III. 歌声とトラック 8', '3 分 4 秒から歌声。トラック 18 が消え、トラック 8 (3 半音上げて) が前に出る')
    P.section(S4, 'IV. 歌の後半とトラック 18 (2 回目)', '6 分 4 秒からトラック 18 をもう一度 (2 半音下げて)。歌は 7 分 21 秒で終わる')
    P.section(S5, 'V. 17 歳の声 (2 回目)', '声がもう一度。トラック 18 の終わりに、トラック 8 の続き (60 秒から) が入る')
    P.section(S6, 'VI. トラック 18 の後半、消える', 'トラック 18 の後半が声の終わり (10 分 13 秒) を受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        env = c.get('env')
        if env and p['envk'] != 1.0: env = [round(v * p['envk'], 4) for v in env]       # くり返しの段は、音量に合わせて波形も小さく描く
        kw = dict(lane=p['lane'], color=list(p['color']), env=env, env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid in (RS, RP):  # 声と歌声: 何も変えずにそのまま前に (帯域も削らず、全体の残響も掛けない)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'] if p['fin'] is not None else 0.05, fout=p['fout'] if p['fout'] is not None else 2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。移調はテープのように速さごと。入りは 6 秒で立ち上げる
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXVIII · La diciassettenne e la mia voce',
        'subtitle': 'tablet266 (17 歳の声・トラック 18・8) に、取り出した歌声を重ねて。歌の調のハ短調で。♩=60',
        'footer': ['tablet266 の素材 (倍音の 3 声の 17 歳の声、トラック 18、トラック 8) と、2025/01/08 の録音から取り出した歌声そのもの (ハ短調)。声はどちらも変えない。',
                   '歌の調に合わせて、テープをハ短調に: トラック 18 は 2 半音下げ、トラック 8 は 3 半音上げ。17 歳の声は話し声なので移さない (基音の中心 B♭3 はハ短調の音)。',
                   '17 歳の声 → 歌声 → 17 歳の声。入りは tablet266 と同じ (2 小節から声、4 小節からトラック 18 の出だしの一節を 3 回)。楽器は何も加えない。164 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=268, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
