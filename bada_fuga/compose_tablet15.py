#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XV · Violino (主題に重なるシンセを、切り裂かないバイオリンに)
  XIV から、主題の入り (11:23 の主題を含む) に重なっていたシンセサイザーを、バイオリン (synth.violin_tone: 弓で弾く弦の倍音列 →
  胴の共鳴 → 3 kHz 以上はなだらかに落とし、高い音ほど音量を抑える) に置き換えた。高揚しても耳障りにならず、洗脳的に主題をなぞる。
  最後のヘ長調の和音は、バイオリンの重音 (C5・A5) が静かに添う。
  以下は XIV の説明:
  XIII から、シンセの「ビュー」という音 — 共鳴するフィルターが開くときの音 (主題に重なるシンセの音ごとの開き、最後の和音のゆっくりした開き) — を消した。
  フィルターの共鳴 (Q) をなくし、開き方も最初から固定 (open ≈ 0)。残るのは、主題の入りに同じ音で重なる、共鳴しないシンセ。
  以下は XIII の説明:
  XII から、シンセの「共鳴するうねり」(LFO でカットオフが往復するパッド RS) を消した。残るのは、フーガの主題の入りに同じ音で重なる
  共鳴シンセ (RL) だけで、そのフィルターは一度開いて固定 (lfo=0) — うねらない。最後のヘ長調の和音は、一度だけゆっくり開く。
  以下は XII の説明:
  XI の pianissimo の降りる音階 (降圧剤) を消し、2026-09-24 のピアノ録音 5 本 (08:49 / 08:53 / 11:18 / 11:21 / 11:23) の実音
  (速さも音高も元のまま) とその旋律のレクイエムとフーガに、本格的なアナログ風シンセサイザー (synth.reso_synth:
  デチューンした鋸歯波 3 本 + サブを、共鳴する 2 次ローパスに通し、カットオフが LFO でゆっくり往復する) を重ねる:
    - RS (パッド): 和音の根音・5 度・3 度を 2 小節ごとに、共鳴のうねりが 2 小節で 1 往復 — 実音の下では控えめ
    - RL (主題に共鳴するリード): フーガの主題の入りを、共鳴するシンセが同じ音で重ねて響かせる
    Introitus — Mix 11:23 → 08:53 (ホ短調) / Fuga I — 11:23 のバッハ風フーガ (提示 → エピソード → 下属調 → ストレッタ → 保続低音)
    Lacrimosa — 11:18 (変ロ短調) / Fuga II — 08:53 と 11:18 の二重フーガ (変ロ短調)
    Sanctus — Mix 08:49 → 11:21 (ヘ短調, ピアノとシンセの録音) / Finale — 5 つの主題のストレッタ (ヘ短調) → 保続低音
    In paradisum — 11:21 の本当の終わり → ヘ長調の和音を共鳴シンセが開いて閉じる
  使い方: python compose_tablet15.py <bank.json> [score_tablet12.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11       # バッハ風フーガ (bach_fugue)

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 60; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, RB, RF, SY = '20260924_112313', '20260924_085314', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, RB, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤')))
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': RB}
PADS = []                            # (開始小節, 終了小節, 大きさ)
LEADS = []                           # (開始小節, 終了小節, 大きさ) — 主題の入りに共鳴するリード

def near(pc, target, lo=24, hi=100): return min((x for x in range(lo, hi) if x % 12 == pc), key=lambda x: abs(x - target))

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:                                 # 鼓動 (pp)
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.13 if k == 0 else 0.07, None, rid=rid)
    for b0, b1, g in LEADS:                                              # 主題の入り (ラベル付きの音) に共鳴するリード
        for v in ('S', 'A', 'T'):
            for s, d, m, lab in events[v]:
                if lab and b0 * BPB <= s < b1 * BPB: add('VN', s, d * 0.95, m, g, None, pan=(-0.2 if v == 'S' else 0.2))

def mix(P, b, r1, r2, semis, bars=10):
    T5.passage(P, r1, b, bars, semis, bars, fin=1.5, fout=XF * BAR_S, bpm=BPM, gmul=0.65)
    CT.LAYOUT.append((b, b + bars, semis, {v: r1 for v in VOICES}, {}))
    st = b + bars - XF
    T5.passage(P, r2, st, bars, semis, bars, fin=XF * BAR_S, fout=3.0, bpm=BPM, gmul=0.65)
    CT.LAYOUT.append((st + XF, st + bars, semis, {v: r2 for v in VOICES}, {}))
    for v in VOICES: P.rest_bars(v, b, st + bars)
    return 2 * bars - XF

def pivot(P, b, rid, semis_next):
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55)): add('PF', b * BPB + k * 0.5, 2.5, m, 0.16, None, rid=rid, rel=1.5)
    T2.MANTRA.append((b, b + 1, rid, ('PK',))); CT.LAYOUT.append((b, b + 1, semis_next, VOICE_SRC, {}))

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_sy = REC[SY]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(SY, []).append((end_sy, REC[SY]['dur']))
    total = 18 + 16 + 1 + 10 + 10 + 1 + 18 + 10 + 3 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    P.section(b, 'Introitus — Mix 〈%s → %s〉' % (hm(E1), hm(E2)), 'ホ短調 ／ 実音のピアノ 2 本をつなぐ — 柔らかい鼓動だけが下で続く')
    b += mix(P, b, E1, E2, 2)
    T2.MANTRA.append((0, b, E1, ('PK',))); PADS.append((0, b, 0.04))
    # ---------------- Fuga I (ホ短調): バッハ風
    f = b
    P.section(b, 'Fuga I — %s のバッハ風フーガ (ホ短調)' % hm(E2), '提示 → エピソード → 下属調の入り → ストレッタ → 保続低音 — 主題の入りにバイオリンが同じ音で重なる')
    n_ = T11.bach_fugue(P, b, E2, '②')
    T2.MANTRA.append((f, f + n_, E1, ('PK',))); PADS.append((f, f + n_, 0.055)); LEADS.append((f, f + n_, 0.075))
    CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    pivot(P, b, E2, -4); b += 1
    # ---------------- Lacrimosa (変ロ短調)
    P.section(b, 'Lacrimosa — %s の実音 (変ロ短調)' % hm(RB), 'ループせずそのまま 40 秒')
    T5.passage(P, RB, b, 10, -4, 10, fin=1.5, fout=3.0, bpm=BPM, gmul=0.65)
    for v in VOICES: P.rest_bars(v, b, b + 10)
    T2.MANTRA.append((b, b + 10, RB, ('PK',))); PADS.append((b, b + 10, 0.04)); CT.LAYOUT.append((b, b + 10, -4, {v: RB for v in VOICES}, {})); b += 10
    # ---------------- Fuga II (変ロ短調): 二重フーガ
    f = b; entries, labmap = [], {}
    P.section(b, 'Fuga II — 主題 ①③ 〈%s · %s〉 (変ロ短調)' % (hm(E1), hm(RB)), '11:23 と 11:18 の主題の二重フーガ — バイオリンが主題をなぞる (高くなっても柔らかく)')
    for bar, v, r, tr0 in ((0, 'A', E1, 0), (2, 'S', RB, 0), (4, 'T', E1, 7), (6, 'B', RB, 0), (8, 'S', E1, 0), (8, 'T', RB, 0)):
        T7.entry(P, f + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    T2.MANTRA.append((f, f + 10, RB, ('PK',))); PADS.append((f, f + 10, 0.055)); LEADS.append((f, f + 10, 0.075))
    CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    pivot(P, b, RF, 3); b += 1
    # ---------------- Sanctus (ヘ短調): 08:49 → 11:21 (ピアノとシンセの録音)
    s0 = b
    P.section(b, 'Sanctus — Mix 〈%s → %s (ピアノとシンセ)〉 (ヘ短調)' % (hm(RF), hm(SY)), '08:49 から、ピアノとシンセサイザーの録音 11:21 へ実音のまま')
    b += mix(P, b, RF, SY, 3)
    T2.MANTRA.append((s0, b, RF, ('PK',))); PADS.append((s0, s0 + 8, 0.04)); PADS.append((s0 + 8, b, 0.025))
    # ---------------- Finale (ヘ短調): 5 つの主題のストレッタ → 保続低音
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a cinque soggetti (ヘ短調)', '5 本の録音の主題が次々と入り、最後の 2 つはストレッタで重なる → 保続低音 — バイオリンが全部の主題をなぞる')
    for k, bar in enumerate((0, 2, 4, 6, 7)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    for k in range(10): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + 10, RF, ('PK',))); PADS.append((f, f + 10, 0.06)); LEADS.append((f, f + 10, 0.08))
    CT.LAYOUT.append((f, f + 10, 3, VOICE_SRC, labmap)); b = f + 10
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, T11.PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    T2.MANTRA.append((b, b + 3, RF, ('PK',))); PADS.append((b, b + 3, 0.055)); CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    # ---------------- In paradisum: 11:21 の本当の終わり → ヘ長調
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(SY), 'ピアノとシンセサイザーの録音 11:21 の最後の 20 秒を実音のまま → ヘ長調の和音を、ピアノとバイオリンの重音が静かに鳴らして閉じる')
    T5.passage(P, SY, b, 5, 3, 5, fin=1.0, fout=2.5, t0=end_sy, bpm=BPM, gmul=0.7)
    for v in VOICES: P.rest_bars(v, b, b + 5)
    T2.MANTRA.append((b, b + 5, SY, ('PK',))); PADS.append((b, b + 5, 0.03)); CT.LAYOUT.append((b, b + 5, 3, {v: SY for v in VOICES}, {})); b += 5
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((38, 45, 50, 54, 57, 62, 66)): add('PF', b * BPB + k * 0.4, 3.5, m, 0.2, None, rid=RF, rel=3.0)
    for k, (m, pan) in enumerate(((69, -0.2), (78, 0.2))):                       # バイオリンの重音 (ヘ長調で C5・A5)
        add('VN', b * BPB + 1.0, 9.0, m, 0.07, None, pan=pan)
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XV · Violino',
    'subtitle': '主題に重なるシンセをバイオリンに — 切り裂かず、高揚しても耳障りにならない (♩=60)',
    'legend': ['TB', 'VN', 'PK'],
    'footer': ['Introitus: 11:23 → 08:53 (ホ短調) → Fuga I (08:53, バッハ風) → Lacrimosa 11:18 (変ロ短調) → Fuga II (二重) → Sanctus: 08:49 → 11:21 (ヘ短調) → Finale (ストレッタ) → 11:21 の終わり → ヘ長調',
               'バイオリン (合成): 弓の弦の倍音列 → 胴の共鳴 (275 / 450 / 1000 / 1900 Hz) → 3 kHz 以上はなだらかに落とす。A5 より上は音量を抑える。シンセはなし。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet15.json'
    compose.main(out, seed=89, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
