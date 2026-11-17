#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXLIX · Requiem fedele — la signora di Tsukuyomi (11/12 14:49 の声を月読様の三賢者の一人の淑女の声に、11/17 の音源 2 本をトラック 18 と 8 に、tablet89 を音を忠実に — レクイエムのように)
  音を忠実に: どのテープも原音のまま — 移調なし (速さも変えない)、帯域を削らない、ステレオはステレオのまま、残響も左右の遅れも足さない (synth.py の faithful)。
    足すのは音量と、録音が途中で切れている所の終わりのフェードだけ。楽器は何も加えない (サンプラーも、ペダルも、鐘もなし)
  声: 11/12 14:49 の男声 (基音 112 Hz) を feminize_voice.py で 1 人の淑女の声に — ニ短調の朗唱音 A3 = 220 Hz を中心に (11.69 半音上げ、フォルマント 1.12 倍、抑揚 0.8)、
    ヘ長調の音階 (= ニ短調) に調律、月読様の澄んだ声 (5〜9 kHz +1.5 dB、残響 2.2 秒・0.35)、重ねる声はなし (三賢者の「一人」)
  調の流れ (移調しないので、調の近い録音どうしを重ね、調の遠い録音は順に並べる): ニ短調 (トラック 18) → イ短調 (トラック 8) → ハ長調 (11/17 17:06) → ニ短調 (tablet89) → ニ長調 (Amen)
    重ね方は 1 秒ごとのクロマから「濁りの指数」(半音 1.0・三全音 0.6・全音 0.25 のぶつかり ÷ ぶつかり + 協和) がいちばん小さいずらし方を選んだ:
    トラック 18 に 11/17 17:05 を 8 秒から (0.29)、トラック 18 の 108 秒からトラック 8 (0.23)、トラック 8 の 92 秒から 11/17 17:06 (0.25)、11/17 17:06 の 144 秒から tablet89 (0.18; 最後の和音が消える所で受け渡す)
    (これまでの曲 — トラック 8 を 5 半音上げてトラック 18 と — は 0.27)
  tablet89 (LXXXIX — Requiem e Fuga、♩=60) は 86 小節から初めから終わりまで 1 回、小節線も揃う: Requiem (24) → Fuga (16) → Requiem (24) → Fuga (16) → Stretto (12) → Amen (ニ長調, 4)
  和音の表示は録音から読んだもの (analyze_chords.py: 半小節ごとの三和音)。♩=60、183 小節
  使い方: python compose_tablet249.py <wav のフォルダ (20261112_144938.wav = 淑女の声, 20261107_180000.wav, 20261107_080000.wav, 20261107_089000.wav = tablet89,
          20261117_170501.wav, 20261117_170604.wav — テープはステレオのまま)> <chords249.json (analyze_chords.py の出力)> [score_tablet249.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet249.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')          # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08, R89, RN1, RN2 = '20261112_144938', '20261107_180000', '20261107_080000', '20261107_089000', '20261117_170501', '20261117_170604'
BPM = 60                                                                               # 1 拍 = 1 秒、1 小節 = 4 秒 (tablet89 の小節と同じ)
DUR = {RV: 178.3, R18: 149.1, R08: 249.2, R89: 391.0, RN1: 60.2, RN2: 156.0}
B8, BN2, B89 = 27, 50, 86                                                              # トラック 8・11/17 17:06・tablet89 の入りの小節
BV1, BV2 = 12, B89 + 40                                                                # 淑女の声の話し始めの小節 (録音の頭の 6.5 秒は無音)
TOTAL = B89 + 97                                                                       # tablet89 の音は 387.5 秒で消える
COLV, COLN, COL18, COL8, COL89 = (236, 200, 120), (176, 140, 236), (120, 190, 250), (110, 210, 190), (230, 150, 110)
# (録音, 入りの拍, 音量, 終わりのフェード秒, 段, 色, 画面の名前)
PLAYS = [(R18, 0.0, 0.5, 1.5, 2, COL18, 'トラック 18 — 原音のまま (ニ短調)'),
         (RN1, 8.0, 0.42, 4.0, 1, COLN, '11/17 17:05 の音源 — 原音のまま'),
         (RV, BV1 * 4.0 - 6.5, 0.52, 2.0, 0, COLV, '11/12 14:49 の声 — 月読様の三賢者の一人、淑女の声'),
         (R08, B8 * 4.0, 0.48, 1.5, 3, COL8, 'トラック 8 — 原音のまま (イ短調、移調なし)'),
         (RN2, BN2 * 4.0, 0.55, 6.0, 1, COLN, '11/17 17:06 の音源 — 原音のまま (ハ長調)'),
         (R89, B89 * 4.0, 0.6, 1.5, 2, COL89, 'tablet89 (Requiem e Fuga) — 初めから終わりまで、原音のまま'),
         (RV, BV2 * 4.0 - 6.5, 0.52, 2.0, 0, COLV, '11/12 14:49 の声 — 淑女の声 (もう一度)')]
# 和音の表示を担うテープ (録音, そのテープの入りの拍, 表示の始まりの拍)
LEAD = [(R18, 0.0, 0.0), (R08, B8 * 4.0, 140.0), (RN2, BN2 * 4.0, BN2 * 4.0), (R89, B89 * 4.0, B89 * 4.0)]
def harm_at(q):
    cur = 'Dm'
    for rid, t0, a in LEAD:
        if q >= a:
            c = CH[rid]; cur = c['chords'][min(max(int((q - t0) / c['win']), 0), len(c['chords']) - 1)]
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(0, 'I. Introitus (ニ短調, ♩=60)', 'トラック 18 に、11/17 17:05 の音源が 2 小節から重なる — どの音も原音のまま')
    P.section(BV1, 'II. Requiem aeternam', '月読様の三賢者の一人、淑女の声が入る (11/12 14:49 の声、A3 を中心にニ短調に調律)')
    P.section(B8, 'III. Kyrie (イ短調)', 'トラック 8 (移調なし) が静かに入り、トラック 18 が消える。声は続く')
    P.section(BN2, 'IV. Offertorium (ハ長調 / イ短調)', '11/17 17:06 の音源をトラック 8 に重ねる。声は 54 小節で終わり、トラック 8 は 84 小節で消える')
    P.section(B89, 'V. Requiem (ニ短調) — tablet89', 'tablet89 を初めから終わりまで忠実に: Requiem (表)。11/17 17:06 の最後の和音が消える所から')
    P.section(B89 + 24, 'VI. Fuga — tablet89', 'tablet89 の 4 声のフーガ')
    P.section(B89 + 40, 'VII. Lux aeterna — tablet89', 'tablet89 の 2 回目の Requiem に、淑女の声をもう一度')
    P.section(B89 + 64, 'VIII. Cum sanctis tuis — tablet89', 'tablet89 の 2 つ目のフーガ、声は続く')
    P.section(B89 + 80, 'IX. Stretto — tablet89', 'tablet89 のストレッタ、声が終わる')
    P.section(B89 + 92, 'X. Amen (ニ長調)', 'tablet89 の Amen、消える')
    return P

def post(P, events, ex):
    for rid, beat, g, fo, lane, col, tag in PLAYS:
        c = CH.get(rid, {})
        add('REC', beat, DUR[rid] * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=0.0, fin=0.05, fout=fo, semis=0, faithful=True,
            rid=rid + '.wav', tag=tag, lane=lane, color=list(col), env=c.get('env'), env_dt=c.get('env_dt', 0.05))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {},
        'title': 'Requiem BADA — CCXLIX · Requiem fedele',
        'subtitle': '月読様の三賢者の一人、淑女の声と、原音のままの 5 つの録音。ニ短調 → ニ長調、♩=60',
        'footer': ['音を忠実に: 移調なし、帯域を削らず、ステレオのまま、残響も足さない。足すのは音量と、切れている録音の終わりのフェードだけ。楽器は何も加えない。',
                   '淑女の声 = 11/12 14:49 の声 (112 Hz) を A3 = 220 Hz の 1 人の女声に (フォルマント 1.12 倍、抑揚 0.8、ニ短調に調律、残響 2.2 秒・0.35)。',
                   '重ね方 = 1 秒ごとのクロマから、半音・三全音のぶつかりがいちばん少ないずらし方 (調の近い録音どうしを重ね、遠い録音は順に並べる)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=249, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
