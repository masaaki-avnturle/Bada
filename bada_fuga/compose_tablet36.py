"""
Requiem BADA — Tablet Sessions XXXVI · Contrapunctus XIV — ramo (2026-09-23 の 2 本の録音から: J. S. バッハのレクイエムでありながら、Contrapunctus XIV の分派)
  録音: 9/23 08:06 (変ロ短調) と 9/23 08:09 (ホ短調)。それぞれの主題を『フーガの技法』Contrapunctus XIV の形で:
    Introitus — 08:09 の実音 (ホ短調のまま)
    Sectio I  (ホ短調)  — 第 1 主題 = 08:09 の主題: 4 声の提示 → 反行形 → 低音の拡大形 (2 倍)
    Interludium — 08:06 の実音 (変ロ短調のまま)
    Sectio II (変ロ短調) — 第 2 主題 = 08:06 の主題: 4 声の提示 → 第 1 主題と重なる二重フーガ
    Sectio III (ニ短調、Contrapunctus XIV と同じ調) — 第 3 主題 = B-A-D-A (バッハの B-A-C-H の代わり) の提示
              → 3 つの主題を同時に重ねる三重フーガ → 2 度目の重なりの途中で楽譜が途切れる (Contrapunctus XIV のように)
    Choral (変ロ短調) — バッハのレクイエム (葬送カンタータ) のように、途切れたあとに 4 声のコラール: 08:06 の主題を 2 倍の長さでソプラノに、
              掛留、iv → i のアーメン終止 → 08:06 の本当の終わり (実音) で閉じる
  音はすべて 2 本の録音から切り出したピアノの 1 音と実音の抜粋、弔鐘 (低い打鍵)、鼓動。
  使い方: python compose_tablet36.py <bank17.json> [score_tablet36.json]
"""
import sys, json
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11
import compose_tablet24 as T24

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 56; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E3, B1]
T7.MARK.update({E3: '①', B1: '②'})
VOICE_SRC = {'S': E3, 'A': B1, 'T': E3, 'B': B1}
S1, S2 = E3, B1                       # 第 1 主題 (08:09)、第 2 主題 (08:06)
BELL = []
CLUSTERS = []; CUT = None; CUT_END = None; TAIL = ()
octs, TOP = T7.octs, T7.TOP

def fit(v, mat, tr):
    if v == 'B' and min(m for _, m in mat) + tr < 36: tr += 12
    if max(m for _, m in mat) + tr > TOP[v]: tr -= 12
    return tr

def entry(P, bar, v, mat, tr0, label, entries, beat=0):
    tr = fit(v, mat, octs[v] + tr0)
    P.place(v, bar, mat, tr, label, beat=beat); entries.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))

def invert(mat):
    m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]

def augment(mat):
    return [(2 * d, m) for d, m in mat]

def diminish(mat):
    return [(d / 2.0, m) for d, m in mat]

def rest_until(P, v, b0, bar, beat):
    """b0 小節から、bar 小節 beat 拍の入りまで休む"""
    P.rest_bars(v, b0, bar)
    if beat: P.rest_bars(v, bar, bar + 1, beats=range(int(beat)))

def chain(P, b, rids, semis, bars=8):
    """実音の抜粋をクロスフェードでつなぐ (XXII と同じ)"""
    st = b
    for i, r in enumerate(rids):
        T5.passage(P, r, st, bars, semis, bars, fin=(1.5 if i == 0 else XF * BAR_S), fout=(XF * BAR_S if i < len(rids) - 1 else 3.0), bpm=BPM, gmul=0.65)
        CT.LAYOUT.append((st + (XF if i else 0), st + bars, semis, {v: r for v in VOICES}, {}))
        st += bars - XF
    end = st + XF
    for v in VOICES: P.rest_bars(v, b, end)
    T2.MANTRA.append((b, end, rids[0], ('PK',)))
    return end - b

def cluster(beat, gain=0.14, rid=None):
    CLUSTERS.append((beat, gain, rid))

def post(P, events, extras):
    T24.suspend(P, events)                                                # 掛留 (バッハの対位法)
    for b0, b1, gain, rid in BELL:                                        # 弔鐘: 低い打鍵が小節ごとに
        for bar in range(b0, b1): add('PF', bar * BPB, 3.8, 38, gain, None, rid=rid, rel=3.5)
    for beat, gain, rid in CLUSTERS:                                     # 12 音の塊 (弔鐘)
        root = chord(P.harm[int(beat)])['root']; base = 26 + (root - 2) % 12
        for j, x in enumerate((0, 1, 6, 7, 11, 13, 16, 18, 22, 25, 30, 31)):
            add('PF', beat + 0.006 * j, 3.0, base + x + (12 if j >= 8 else 0), gain * (1.0 if j < 3 else 0.8), None, rid=rid or VOICE_SRC['B'], rel=2.5)
    if CUT is not None:                                                  # 楽譜が途切れる: 2 拍目以降の音を切る
        for v in VOICES:
            events[v] = [(s, min(d, CUT - s) if s < CUT else d, m, lab) for s, d, m, lab in events[v] if s < CUT or s >= CUT_END]
    for b0, b1, rid, kinds in T2.MANTRA:
        for bar in range(b0, b1):
            g = 0.35 if TAIL and TAIL[0] <= bar < TAIL[0] + TAIL[1] else 1.0
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, (0.11 if k == 0 else 0.06) * g, None, rid=rid)

def chorale(P, f, mat_, E, label):
    aug = [(2 * d, m) for d, m in mat_]
    entry(P, f, 'S', aug, 0, label, E); return int(round(sum(d for d, _ in aug) / BPB))

def build():
    global CUT, CUT_END, TAIL
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    s1, s2, s3 = T5.SUBJ[S1][0], T5.SUBJ[S2][0], list(H.BADA)
    L1, L2, L3 = '主題 ① (08:09)', '主題 ② (08:06)', 'B-A-D-A'
    end_b1 = REC[B1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(B1, []).append((end_b1, REC[B1]['dur']))
    total = 6 + 18 + 6 + 16 + 20 + 1 + 8 + 5
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    # ---------------- Introitus — 08:09 (ホ短調)
    P.section(b, 'Introitus — %s の実音 (ホ短調)' % hm(E3), '9/23 の 2 本目をそのまま — 弔鐘と鼓動')
    T5.passage(P, E3, b, 6, 2, 6, fin=1.5, fout=3.0, bpm=BPM, gmul=0.65)
    for v in VOICES: P.rest_bars(v, b, b + 6)
    for k in range(6): P.dyn[b + k] = 0.5
    BELL.append((b, b + 6, 0.12, E3)); T2.MANTRA.append((b, b + 6, E3, ('PK',))); CT.LAYOUT.append((b, b + 6, 2, {v: E3 for v in VOICES}, {})); b += 6
    # ---------------- Sectio I — 第 1 主題 (ホ短調)
    f = b; E = []
    P.section(b, 'Sectio I — Soggetto I 〈%s〉 (ホ短調)' % hm(E3), '第 1 主題の 4 声の提示 (オクターヴごとに) → エピソード → 反行形 (S, T) → 低音の拡大形 (2 倍の長さ)')
    for k, v in enumerate('ASTB'): entry(P, f + 2 * k, v, s1, 0, L1, E)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    P.set_harms(f + 8, [['Gm', 'Gm', 'C7', 'C7'], ['F', 'F', 'A7', 'A7']])
    E = []; entry(P, f + 10, 'S', invert(s1), 0, L1 + ' (反行)', E); entry(P, f + 12, 'T', invert(s1), 0, L1 + ' (反行)', E)
    T5.harm_from_entries(P, f + 10, f + 14, E)
    E = []; entry(P, f + 14, 'B', augment(s1), 0, L1 + ' (拡大)', E); T5.harm_from_entries(P, f + 14, f + 18, E)
    P.hold.update({f + 16, f + 17})
    for k in range(18): P.dyn[f + k] = 1.2
    BELL.append((f, f + 8, 0.08, E3)); T2.MANTRA.append((f, f + 18, E3, ('PK',))); CT.LAYOUT.append((f, f + 18, 2, VOICE_SRC, {})); b = f + 18
    # ---------------- Interludium — 08:06 (変ロ短調)
    P.section(b, 'Interludium — %s の実音 (変ロ短調)' % hm(B1), '9/23 の 1 本目をそのまま — 弔鐘と鼓動')
    T5.passage(P, B1, b, 6, -4, 6, fin=1.5, fout=3.0, bpm=BPM, gmul=0.65)
    for v in VOICES: P.rest_bars(v, b, b + 6)
    for k in range(6): P.dyn[b + k] = 0.5
    BELL.append((b, b + 6, 0.12, B1)); T2.MANTRA.append((b, b + 6, B1, ('PK',))); CT.LAYOUT.append((b, b + 6, -4, {v: B1 for v in VOICES}, {})); b += 6
    # ---------------- Sectio II — 第 2 主題 (変ロ短調)
    f = b; E = []
    P.section(b, 'Sectio II — Soggetto II 〈%s〉 (変ロ短調)' % hm(B1), '第 2 主題の 4 声の提示 → 第 1 主題と重なる二重フーガ')
    for k, v in enumerate('TABS'): entry(P, f + 2 * k, v, s2, 0, L2, E)
    for v, z in {'A': 2, 'B': 4, 'S': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    E = []
    entry(P, f + 8, 'S', s1, 0, L1, E); entry(P, f + 8, 'T', s2, 0, L2, E)
    entry(P, f + 11, 'A', s2, 0, L2, E); entry(P, f + 11, 'B', s1, 0, L1, E)
    T5.harm_from_entries(P, f + 8, f + 14, E)
    P.set_harms(f + 14, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7']]); P.hold.update({f + 14, f + 15})
    for k in range(16): P.dyn[f + k] = 1.25
    BELL.append((f + 8, f + 16, 0.08, B1)); T2.MANTRA.append((f, f + 16, B1, ('PK',))); CT.LAYOUT.append((f, f + 16, -4, VOICE_SRC, {})); b = f + 16
    # ---------------- Sectio III — B-A-D-A → 三重フーガ → 途切れる (ニ短調)
    f = b; E = []
    P.section(b, 'Sectio III — B-A-D-A · Fuga a tre soggetti (ニ短調)', 'Contrapunctus XIV と同じ調へ。B-A-C-H の代わりに B-A-D-A を 4 声で提示 → 3 つの主題を同時に重ねる三重フーガ → 2 度目の重なりの途中で楽譜が途切れる')
    for k, v in enumerate('BTAS'): entry(P, f + 2 * k, v, s3, 0, L3, E)
    for v, z in {'T': 2, 'A': 4, 'S': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    E = []; entry(P, f + 8, 'S', s1, 0, L1, E); entry(P, f + 8, 'T', s2, 0, L2, E); entry(P, f + 8, 'A', s3, 0, L3, E)
    T5.harm_from_entries(P, f + 8, f + 12, E); P.set_harms(f + 11, [['A7', 'A7', 'Dm', 'Dm']])
    E = []; entry(P, f + 12, 'B', augment(s1), 0, L1 + ' (拡大)', E); entry(P, f + 12, 'S', s2, 0, L2, E); entry(P, f + 12, 'T', s3, 0, L3, E); entry(P, f + 14, 'A', s3, 0, L3, E)
    entry(P, f + 16, 'S', s1, 0, L1, E); entry(P, f + 16, 'A', s2, 0, L2, E, beat=2); entry(P, f + 17, 'T', s3, 0, L3, E)
    T5.harm_from_entries(P, f + 12, f + 20, E)
    CUT = (f + 19) * BPB + 1                                                              # 途切れる: 20 小節目の 2 拍目
    for k in range(8, 20): P.dyn[f + k] = 1.3
    BELL.append((f + 8, f + 20, 0.1, B1)); T2.MANTRA.append((f, f + 20, B1, ('PK',))); CT.LAYOUT.append((f, f + 20, 0, VOICE_SRC, {})); b = f + 20
    # ---------------- 沈黙 1 小節
    for v in VOICES: P.rest_bars(v, b, b + 1)
    P.harm[b * BPB:(b + 1) * BPB] = ['Dm'] * BPB
    CUT_END = (b + 1) * BPB; TAIL = (b, 1); BELL.append((b, b + 1, 0.14, B1)); T2.MANTRA.append((b, b + 1, B1, ('PK',))); CT.LAYOUT.append((b, b + 1, 0, VOICE_SRC, {})); b += 1
    # ---------------- Choral — コラール (変ロ短調)
    f = b; E = []
    P.section(b, 'Choral — 4 声のコラール 〈%s〉 (変ロ短調)' % hm(B1), 'バッハのレクイエムのように、途切れたあとに 4 声のコラール: 08:06 の主題を 2 倍の長さでソプラノに、掛留、iv → i のアーメン終止')
    t = chorale(P, f, s2, E, '主題 ② のコラール')
    T5.harm_from_entries(P, f, f + t, E)
    for q in range(2): P.harm[(f + t - 1) * BPB + 2 + q] = 'Gm'
    P.set_harms(f + t, [['Dm', 'Dm', 'Gm', 'Gm'], ['A7', 'A7', 'Dm', 'Dm'], ['Gm', 'Gm', 'Dm', 'Dm'], ['Dm']][:8 - t]); P.hold.update(range(f + t, f + 8))
    for k in range(8): P.dyn[f + k] = 1.1
    T2.MANTRA.append((f, f + 8, B1, ('PK',))); BELL.append((f, f + 8, 0.08, B1)); CT.LAYOUT.append((f, f + 8, -4, VOICE_SRC, {})); b = f + 8
    # ---------------- Coda — 08:06 の本当の終わり
    P.section(b, 'Coda — %s の本当の終わり' % hm(B1), '08:06 の最後 (実音) → 弔鐘が消える')
    T5.passage(P, B1, b, 5, -4, 5, fin=1.0, fout=2.5, t0=end_b1, bpm=BPM, gmul=0.65)
    for v in VOICES: P.rest_bars(v, b, b + 5)
    for k in range(5): P.dyn[b + k] = 0.5
    BELL.append((b, b + 2, 0.1, B1)); T2.MANTRA.append((b, b + 5, B1, ('PK',))); CT.LAYOUT.append((b, b + 5, -4, {v: B1 for v in VOICES}, {})); b += 5
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XXXVI · Ramo',
    'subtitle': '9/23 の 2 本 (08:06・08:09) から — バッハのレクイエムでありながら Contrapunctus XIV の分派: 三重フーガが途切れ、コラールへ',
    'legend': ['TB', 'PK'], 'vname': {'PK': '鼓動'},
    'footer': ['Introitus 08:09 → Sectio I (主題 ①, ホ短調) → Interludium 08:06 → Sectio II (② + ①, 変ロ短調) → Sectio III (B-A-D-A · 三重, ニ短調 → 途切れる) → Choral → Coda 08:06',
               '『フーガの技法』の未完の Contrapunctus XIV にならい、B-A-C-H の代わりに B-A-D-A。音はすべて 9/23 の 2 本の録音のピアノと実音、弔鐘、鼓動。掛留とアーメン終止のコラール。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet36.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
