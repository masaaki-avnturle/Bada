#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions IX · Ipnotico (電車の警笛のような持続音を消した版)
  Tablet Sessions VIII から、電車の警笛のように聞こえる「伸ばしたまま鳴り続ける和音・持続音」を消した:
    - 低い持続音 (DN) をなくし、サンプラーの音はループで伸ばさずピアノのように自然に減衰させる (meta 'piano_decay')
    - 調の変わり目と最後の、全音符で伸ばした和音 → 自然に消えていくピアノの分散和音
    - 実音の区間の下で和音を伸ばす 4 声をなくし、実音だけを流す
  以下は VIII の説明:
  Tablet Sessions VII から、シンセサイザーの「正義の味方」のような明るく勇ましい部分 — シンセのリード・パッドと、
  ピアノとシンセの録音 11:21 (実音も主題も) — を消し、ピアノ録音 4 本 (09-24 08:49 / 08:53 / 11:18 / 11:23) の実音と、
  その旋律のレクイエムとフーガだけにした。♩=60 の柔らかい鼓動 (録音の低い打鍵) が最後まで止まらず、フーガの下では
  録音の音のオスティナートと持続音が同じ形を回し続ける。鳴る音はすべてピアノ録音。
    Introitus — Mix: 11:23 → 08:53 (ホ短調) の実音
    Fuga I — 11:23 と 08:53 の主題の二重フーガ (オスティナート + 持続音)
    Lacrimosa — 11:18 (変ロ短調) の実音
    Sanctus — 08:49 (ヘ短調) の実音
    Finale — 4 つの主題が 2 小節ごとに (オスティナート + 持続音)
    In paradisum — 08:49 の本当の終わり (属和音で止まる) → ヘ長調の和音で安らかに
  使い方: python compose_tablet9.py <bank.json> [score_tablet8.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2         # 鼓動・持続音・オスティナート (post)
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7         # クロスフェードのミックス、主題の入り

add, REC, hm = CT.add, CT.REC, T3.hm
BPM, BAR_S, KEYS = T7.BPM, T7.BAR_S, T7.KEYS
R_A, R_B, R_L, R_C = T7.R_A, T7.R_B, T7.R_L, T7.R_C
ORDER = [R_A, R_B, R_L, R_C]
T7.MARK.update(dict(zip(ORDER, '①②③④')))
VOICE_SRC = {'S': R_A, 'A': R_B, 'T': R_C, 'B': R_L}

def pivot(P, b):
    """調の変わり目: 伸ばした和音ではなく、次の調の属和音をピアノで分散して自然に消えていく"""
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55, 61)): add('PF', b * BPB + k * 0.4, 2.0, m, 0.2, None, rid=R_B, rel=1.5)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_t0 = REC[R_C]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(R_C, []).append((end_t0, REC[R_C]['dur']))       # 終わりの 20 秒は最後のためにとっておく
    total = 18 + 10 + 1 + 10 + 1 + 10 + 9 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.72
    b = 0
    P.section(b, 'Introitus — Mix 〈%s → %s〉' % (hm(R_A), hm(R_B)), 'ホ短調 ／ 2 本の録音を実音のままつなぐ — その下で ♩=60 の柔らかい鼓動 (録音の低い打鍵) が最後まで止まらない')
    b += T7.mix(P, b, R_A, R_B)
    for v in VOICES: P.rest_bars(v, 0, b)
    T2.MANTRA.append((0, b, R_A, ('PK',)))
    # ---------------- Fuga I (ホ短調)
    f0 = b; entries, labmap = [], {}
    P.section(b, 'Fuga I — 主題 ①② 〈%s · %s〉' % (hm(R_A), hm(R_B)), '2 本の録音の主題の二重フーガ — 下で録音の音のオスティナートと持続音が同じ形を回し続ける')
    for bar, v, r, tr0 in ((0, 'A', R_A, 0), (2, 'S', R_B, 0), (4, 'T', R_A, 7), (6, 'B', R_B, 0), (8, 'S', R_A, 0), (8, 'T', R_B, 0)):
        T7.entry(P, f0 + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f0, f0 + z)
    T5.harm_from_entries(P, f0, f0 + 10, entries)
    for k in range(10): P.dyn[f0 + k] = 1.05
    T2.MANTRA.append((f0, f0 + 10, R_A, ('PK', 'OS'))); CT.LAYOUT.append((f0, f0 + 10, 2, VOICE_SRC, labmap))
    b = f0 + 10
    pivot(P, b); T2.MANTRA.append((b, b + 1, R_A, ('PK',)))
    CT.LAYOUT.append((b, b + 1, KEYS[R_L], VOICE_SRC, {})); b += 1
    # ---------------- Lacrimosa (変ロ短調)
    P.section(b, 'Lacrimosa — 録音 %s の実音' % hm(R_L), '変ロ短調 ／ ループせずそのまま 40 秒 — 後半は 4 声が録音の和音を静かに支える')
    T5.passage(P, R_L, b, 10, KEYS[R_L], 10, fin=1.5, fout=3.0, bpm=BPM)
    T2.MANTRA.append((b, b + 10, R_L, ('PK',))); CT.LAYOUT.append((b, b + 10, KEYS[R_L], {v: R_L for v in VOICES}, {})); b += 10
    pivot(P, b); T2.MANTRA.append((b, b + 1, R_L, ('PK',)))
    CT.LAYOUT.append((b, b + 1, KEYS[R_C], VOICE_SRC, {})); b += 1
    # ---------------- Sanctus (ヘ短調)
    P.section(b, 'Sanctus — 録音 %s の実音' % hm(R_C), 'ヘ短調 ／ ループせずそのまま 40 秒 — 鼓動は止まらない')
    T5.passage(P, R_C, b, 10, KEYS[R_C], 10, fin=1.5, fout=3.0, bpm=BPM)
    T2.MANTRA.append((b, b + 10, R_C, ('PK',))); CT.LAYOUT.append((b, b + 10, KEYS[R_C], {v: R_C for v in VOICES}, {})); b += 10
    # ---------------- Finale (ヘ短調): 4 つの主題が 2 小節ごとに
    f1 = b; entries, labmap = [], {}
    P.section(b, 'Finale — Fuga a quattro soggetti', '4 本の録音の主題が 2 小節ごとに次々と — 下でオスティナートと持続音が回り続ける (ヘ短調)')
    for k in range(4): T7.entry(P, f1 + 2 * k, ['A', 'S', 'T', 'B'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f1, f1 + z)
    T5.harm_from_entries(P, f1, f1 + 8, entries); P.set_harms(f1 + 8, [['Gm', 'Gm', 'A7', 'A7']])
    for k in range(9): P.dyn[f1 + k] = 1.1
    T2.MANTRA.append((f1, f1 + 9, R_C, ('PK', 'OS'))); CT.LAYOUT.append((f1, f1 + 9, 3, VOICE_SRC, labmap))
    b = f1 + 9
    # ---------------- In paradisum: 08:49 の本当の終わり → ヘ長調
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(R_C), '08:49 の最後の 20 秒を実音のまま (属和音で止まる) → ヘ長調の和音で安らかに、鼓動とともに消えていく')
    T5.passage(P, R_C, b, 5, KEYS[R_C], 5, fin=1.0, fout=2.5, t0=end_t0, bpm=BPM)
    T2.MANTRA.append((b, b + 8, R_C, ('PK',))); CT.LAYOUT.append((b, b + 5, KEYS[R_C], {v: R_C for v in VOICES}, {}))
    b += 5
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((38, 45, 50, 54, 57, 62, 66)):              # ヘ長調の和音をゆっくり分散して、自然に消えていく
        add('PF', b * BPB + k * 0.35, 3.0, m, 0.22, None, rid=R_C, rel=2.5)
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER,
    'title': 'Requiem BADA — Tablet Sessions IX · Ipnotico', 'piano_decay': 1.4,
    'subtitle': '警笛のように伸びる和音を消した、人に聞かせられる洗脳的なレクイエムとフーガ — ピアノ録音 4 本の音だけで',
    'legend': ['TB', 'OS', 'PK'],
    'footer': ['Introitus: 11:23 → 08:53 (ホ短調) → Fuga I (二重) → Lacrimosa 11:18 (変ロ短調) → Sanctus 08:49 (ヘ短調) → Finale (4 つの主題) → In paradisum → ヘ長調',
               '録音は速さも音高も元のまま。4 声・オスティナートは録音の 1 音をピアノのように自然に減衰させて。伸ばし続ける和音はなし。鼓動は録音の低い打鍵。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet9.json'
    compose.main(out, seed=73, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=T2.post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
