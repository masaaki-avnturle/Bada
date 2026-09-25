#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XI · Adagio in tre bemolli (B♭・E♭・G♭ の 3 つの♭による、荘厳で洗脳的なバッハ風フーガのレクイエム)
  Tablet Sessions X から高音のガラスのシンセを消し、2026-09-23 / 09-24 のピアノ録音 6 本の実音とその旋律をもとに、
  Adagio (♩=48) のバッハ風フーガ (提示 → エピソード → 下属調の入り → ストレッタ → 保続低音) で再構築する。
    調は 3 つの♭ B♭・E♭・G♭ を主音にめぐる: ハ短調 (白鍵の B♮ を導音に) → 変ロ短調 → 変ホ短調 → 変ト長調 → ハ短調
    ホ短調の録音 (08:09 / 08:53 / 11:23) は速さを変えずに半音下げて変ホ短調に、08:49 (ヘ短調) は 2 半音下げて変ホ短調に
    降圧剤: 高音で pianissimo の実音のピアノが、その調の♭の音階を B♭ → A♭ → G♭ → F → E♭ … とゆっくり降り続ける (2 小節で 1 巡)
    ♩=48 の柔らかい鼓動 (録音の低い打鍵) と、やさしい正弦波の低音は残す。音はすべてピアノ録音 (低音の正弦波以外)
  Introitus — Fuga I (ハ短調): 08:09 の主題のバッハ風フーガ
  Kyrie — 08:06 → 11:18 の実音 (変ロ短調) → 08:06 の主題のフガート → 08:06 の本当の終わり (B♭7)
  Graduale — 11:23 → 08:53 の実音 (変ホ短調, 半音下げ) → 二重フーガ (変ホ短調)
  Lux aeterna — 変ト長調のコラール (pp) → 08:49 の実音 (変ホ短調, 2 半音下げ)
  Finale — 6 つの主題のストレッタ (ハ短調) → 保続低音 → ハ長調 (ピカルディ) で pp に消える
  使い方: python compose_tablet11.py <bank.json> [score_tablet11.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2         # 鼓動 (post)
import compose_tablet3 as T3
import compose_tablet5 as T5         # 実音の区間 (pshift つき)、主題からの和声
import compose_tablet7 as T7         # 主題の入り

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 48; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112313': 2}
T7.KEYS.update(KEYS)
RA, RB, RC, RD, RE, RF = '20260923_080918', '20260923_080607', '20260924_111846', '20260924_112313', '20260924_085314', '20260924_084937'
ORDER = [RA, RB, RC, RD, RE, RF]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥')))
CMIN, BbMIN, EbMIN, GbMAJ = -2, -4, 1, 4                 # ニ短調からの移調 (変ト長調はエンジンのニ長調 +4)
VOICE_SRC = {'S': RA, 'A': RE, 'T': RF, 'B': RB}
DESC = []                            # (開始小節, 終了小節, 音階 (エンジンの音名), 大きさ) — 高音の pp の降りる♭の音階
SUBS = []                            # (開始小節, 終了小節) — やさしい低音
PED = mat(('D2', 1)) * 4             # 保続低音 (拍ごとに打ち直す)

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:                                 # 鼓動: 荘厳な pp に合わせて T2 より小さく
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=rid)
    for b0, b1 in SUBS:
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB] or 'Dm')
            add('SUB', bar * BPB, 3.6, min((x for x in range(30, 48) if x % 12 == c['root']), key=lambda x: abs(x - 36)), 0.014, None)
    for b0, b1, scale, g in DESC:                                    # 2 小節で 8 音、ゆっくり降りる (拍ごと)
        line = sorted(scale, reverse=True)
        for k, bar in enumerate(range(b0, b1)):
            for q in range(BPB):
                m = line[(k % 2 * 4 + q) % len(line)]
                add('PF', bar * BPB + q + 0.02, 1.4, m, g, None, rid=VOICE_SRC['S'], rel=1.2)

def scale_engine(semis, pcs_target, lo=77, hi=89):
    """目的の調の音階 (音名の pitch class) を、エンジン (ニ短調基準) の音高 lo〜hi に並べる"""
    return [x for x in range(lo, hi + 1) if (x + semis) % 12 in pcs_target]

PC = {'C': 0, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'Gb': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11, 'Cb': 11}
SC = {'Cm': [PC[x] for x in 'C D Eb F G Ab Bb'.split()], 'Bbm': [PC[x] for x in 'Bb C Db Eb F Gb Ab'.split()],
      'Ebm': [PC[x] for x in 'Eb F Gb Ab Bb Cb Db'.split()], 'Gb': [PC[x] for x in 'Gb Ab Bb Cb Db Eb F'.split()]}

def bach_fugue(P, b, rid, lab_i, minor=True):
    """バッハ風フーガ 16 小節: 提示 (A → S 答唱 → B → T 答唱) 8 → エピソード 2 → 下属調の入り 2 → ストレッタ 2 → 保続低音と終止 2"""
    subj, H_sub = T5.SUBJ[rid]; lab = '主題 %s (%s)' % (lab_i, hm(rid))
    T5.expo(P, b, rid, lab_i)
    P.set_harms(b + 8, [['F', 'F', 'Bb', 'Bb'], ['Gm', 'Gm', 'A7', 'A7']])                     # エピソード (ゼクエンツ)
    P.set_harms(b + 10, transpose_h(H_sub, 5)); P.place('A', b + 10, subj, 5, lab + ' (下属調)')   # 下属調 (Gm) の入り
    P.set_harms(b + 12, H_sub); P.place('S', b + 12, subj, 12, lab + ' ストレッタ')             # ストレッタ: 1 小節遅れて T が 5 度下で
    P.place('T', b + 13, subj, -12, lab + ' ストレッタ')
    P.set_harms(b + 14, [['Dm', 'Dm', 'Gm', 'Gm'], ['A7', 'A7', 'Dm', 'Dm']])
    for k in range(2): P.place('B', b + 14 + k, PED, 0, '保続低音' if k == 0 else None)         # 保続低音 (拍ごとに打ち直す)
    P.hold.add(b + 15)
    return 16

def mix(P, b, r1, r2, semis1, semis2, ps1=0, ps2=0, bars=6):
    T5.passage(P, r1, b, bars, semis1, bars, fin=1.5, fout=XF * BAR_S, bpm=BPM, pshift=ps1, gmul=0.6 if not ps1 else 0.85)
    CT.LAYOUT.append((b, b + bars, semis1, {v: r1 for v in VOICES}, {}))
    st = b + bars - XF
    T5.passage(P, r2, st, bars, semis2, bars, fin=XF * BAR_S, fout=3.0, bpm=BPM, pshift=ps2, gmul=0.6 if not ps2 else 0.85)
    CT.LAYOUT.append((st + XF, st + bars, semis2, {v: r2 for v in VOICES}, {}))
    for v in VOICES: P.rest_bars(v, b, st + bars)
    return 2 * bars - XF

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 48); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_b = REC[RB]['dur'] - 4 * BAR_S - 0.3
    T5.USED.setdefault(RB, []).append((end_b, REC[RB]['dur']))
    total = 16 + 1 + 10 + 6 + 4 + 10 + 10 + 4 + 6 + 1 + 12 + 3 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.3
    b = 0
    # ---------------- Introitus — Fuga I (ハ短調)
    P.section(b, 'Introitus — Fuga I (ハ短調) 〈%s〉' % hm(RA), 'Adagio ／ 08:09 の主題のバッハ風フーガ: 提示 → エピソード → 下属調の入り → ストレッタ → 保続低音。導音は白鍵の B♮、高音では pp の実音が♭の音階を降り続ける')
    n_ = bach_fugue(P, b, RA, '①')
    for k in range(n_): P.dyn[b + k] = 1.3
    T2.MANTRA.append((b, b + n_, RA, ('PK',))); SUBS.append((b, b + n_)); DESC.append((b + 2, b + n_, scale_engine(CMIN, SC['Cm']), 0.19))
    CT.LAYOUT.append((b, b + n_, CMIN, VOICE_SRC, {})); b += n_
    P.set_harms(b, [['A7']]); T2.MANTRA.append((b, b + 1, RA, ('PK',)))                     # 変ロ短調の F7
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55)): add('PF', b * BPB + k * 0.5, 2.5, m, 0.16, None, rid=RB, rel=1.5)
    CT.LAYOUT.append((b, b + 1, BbMIN, VOICE_SRC, {})); b += 1
    # ---------------- Kyrie (変ロ短調): 実音 → フガート → 08:06 の本当の終わり (B♭7)
    s0 = b
    P.section(b, 'Kyrie — %s → %s の実音 (変ロ短調)' % (hm(RB), hm(RC)), '9/23 08:06 から 9/24 11:18 へ実音のまま — 鼓動と低音だけが支える')
    b += mix(P, b, RB, RC, BbMIN, BbMIN)
    T2.MANTRA.append((s0, b, RB, ('PK',))); SUBS.append((s0, b)); DESC.append((s0 + 2, b, scale_engine(BbMIN, SC['Bbm']), 0.15))
    f = b
    P.section(b, 'Kyrie — Fugato (変ロ短調) 〈%s〉' % hm(RB), '08:06 の主題のフガート (提示) — 高音では pp の♭の音階が降り続ける')
    T5.expo(P, b, RB, '②'); P.hold.add(b + 7)
    T2.MANTRA.append((f, f + 6, RB, ('PK',))); SUBS.append((f, f + 6)); DESC.append((f, f + 6, scale_engine(BbMIN, SC['Bbm']), 0.19))
    CT.LAYOUT.append((f, f + 6, BbMIN, {v: RB for v in VOICES}, {})); b = f + 6
    for v in VOICES: P.rest_bars(v, b, b + 4)
    P.section(b, 'Kyrie — %s の本当の終わり (B♭7)' % hm(RB), '08:06 の録音自身の終わり: B♭7 で止まる — 変ホ短調の属和音として次へ')
    T5.passage(P, RB, b, 4, BbMIN, 4, fin=1.0, fout=2.0, t0=end_b, bpm=BPM, gmul=0.6)
    T2.MANTRA.append((b, b + 4, RB, ('PK',))); CT.LAYOUT.append((b, b + 4, BbMIN, {v: RB for v in VOICES}, {})); b += 4
    # ---------------- Graduale (変ホ短調, 半音下げ): 実音 → 二重フーガ
    s0 = b
    P.section(b, 'Graduale — %s → %s の実音 (変ホ短調, 半音下げ)' % (hm(RD), hm(RE)), 'ホ短調の録音を速さを変えずに半音下げて変ホ短調に — 実音のまま')
    b += mix(P, b, RD, RE, EbMIN, EbMIN, -1, -1)
    T2.MANTRA.append((s0, b, RD, ('PK',))); SUBS.append((s0, b)); DESC.append((s0 + 2, b, scale_engine(EbMIN, SC['Ebm']), 0.15))
    f = b; entries, labmap = [], {}
    P.section(b, 'Graduale — Fuga II (変ホ短調) 〈%s · %s〉' % (hm(RD), hm(RE)), '11:23 と 08:53 の主題の二重フーガ')
    for bar, v, r, tr0 in ((0, 'A', RD, 0), (2, 'S', RE, 0), (4, 'T', RD, 7), (6, 'B', RE, 0), (8, 'S', RD, 0), (8, 'T', RE, 0)):
        T7.entry(P, f + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    T2.MANTRA.append((f, f + 10, RD, ('PK',))); SUBS.append((f, f + 10)); DESC.append((f, f + 10, scale_engine(EbMIN, SC['Ebm']), 0.19))
    CT.LAYOUT.append((f, f + 10, EbMIN, VOICE_SRC, labmap)); b = f + 10
    # ---------------- Lux aeterna (変ト長調): pp のコラール → 08:49 (変ホ短調, 2 半音下げ)
    P.section(b, 'Lux aeterna — 変ト長調のコラール (pp)', '3 つ目の♭ G♭ の長調で、4 声が pp のコラール — 高音の♭の音階も G♭ から降りる')
    P.set_harms(b, [['D', 'D', 'G', 'G'], ['Bm', 'Bm', 'Em', 'Em'], ['A7', 'A7', 'D', 'D'], ['G', 'G', 'D', 'D']]); P.hold.update(range(b, b + 4))
    for k in range(4): P.dyn[b + k] = 0.8
    T2.MANTRA.append((b, b + 4, RF, ('PK',))); SUBS.append((b, b + 4)); DESC.append((b, b + 4, scale_engine(GbMAJ, SC['Gb']), 0.16))
    CT.LAYOUT.append((b, b + 4, GbMAJ, VOICE_SRC, {})); b += 4
    P.section(b, 'Lux aeterna — %s の実音 (変ホ短調, 2 半音下げ)' % hm(RF), 'ヘ短調の録音を 2 半音下げて、変ト長調の平行調 変ホ短調に')
    T5.passage(P, RF, b, 6, EbMIN, 6, fin=1.5, fout=3.0, bpm=BPM, pshift=-2, gmul=0.9)
    for v in VOICES: P.rest_bars(v, b, b + 6)
    T2.MANTRA.append((b, b + 6, RF, ('PK',))); SUBS.append((b, b + 6)); DESC.append((b + 1, b + 6, scale_engine(EbMIN, SC['Ebm']), 0.15))
    CT.LAYOUT.append((b, b + 6, EbMIN, {v: RF for v in VOICES}, {})); b += 6
    P.set_harms(b, [['A7']]); T2.MANTRA.append((b, b + 1, RF, ('PK',)))                     # ハ短調の G7 (白鍵の B♮)
    for v in VOICES: P.rest_bars(v, b, b + 1)
    for k, m in enumerate((33, 45, 49, 52, 55)): add('PF', b * BPB + k * 0.5, 2.5, m, 0.16, None, rid=RA, rel=1.5)
    CT.LAYOUT.append((b, b + 1, CMIN, VOICE_SRC, {})); b += 1
    # ---------------- Finale (ハ短調): 6 つの主題のストレッタ → 保続低音 → ハ長調
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sei soggetti (ハ短調)', '6 本の録音の主題が次々と入り、最後の 2 つはストレッタで重なる → 保続低音 → ハ長調 (ピカルディ) で pp に消える')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9)):                                     # 4 つは 2 小節ごと、最後の 2 つはストレッタ (1 小節おき)
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 12, entries)
    for k in range(12): P.dyn[f + k] = 1.35
    T2.MANTRA.append((f, f + 12, RA, ('PK',))); SUBS.append((f, f + 12)); DESC.append((f, f + 12, scale_engine(CMIN, SC['Cm']), 0.19))
    CT.LAYOUT.append((f, f + 12, CMIN, VOICE_SRC, labmap)); b = f + 12
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    for k in range(3): P.dyn[b + k] = 1.0
    T2.MANTRA.append((b, b + 3, RA, ('PK',))); SUBS.append((b, b + 3)); DESC.append((b, b + 3, scale_engine(CMIN, SC['Cm']), 0.16))
    CT.LAYOUT.append((b, b + 3, CMIN, VOICE_SRC, {})); b += 3
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((38, 45, 50, 54, 57, 62, 66)): add('PF', b * BPB + k * 0.4, 3.5, m, 0.2, None, rid=RA, rel=3.0)
    for k, m in enumerate((86, 84, 81, 79, 77, 74, 72)): add('PF', b * BPB + 3 + k * 0.8, 2.0, m, 0.09, None, rid=RA, rel=2.0)   # 最後の降りる音階 (pp)
    add('SUB', b * BPB, 9.0, 26, 0.016, None)
    T2.MANTRA.append((b, b + 2, RA, ('PK',))); CT.LAYOUT.append((b, b + 3, CMIN, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.6,
    'title': 'Requiem BADA — Tablet Sessions XI · Adagio in tre bemolli',
    'subtitle': 'B♭・E♭・G♭ の 3 つの♭をめぐる、荘厳で洗脳的なバッハ風フーガのレクイエム (Adagio ♩=48)',
    'legend': ['TB', 'SUB', 'PK'],
    'footer': ['Fuga I (ハ短調) → Kyrie: 08:06 → 11:18・フガート (変ロ短調) → Graduale: 11:23 → 08:53・二重フーガ (変ホ短調) → Lux aeterna (変ト長調) → 08:49 → Finale: ストレッタ (ハ短調) → ハ長調',
               '高音では pp の実音のピアノが♭の音階を降り続ける (降圧剤)。ホ短調の録音は半音下げ、ヘ短調は 2 半音下げ (速さは元のまま)。高音のガラスのシンセはなし。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet11.json'
    compose.main(out, seed=83, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
