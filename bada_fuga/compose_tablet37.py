"""
Requiem BADA — Tablet Sessions XXXVII · Das wohltemperierte Requiem (10 本の録音を、平均律クラヴィーア曲集のように「前奏曲とフーガ」で、
  Contrapunctus XIV の三重フーガへ — 洗脳的なシンセサイザーの演奏を取り入れた、荘厳でありながら惹かれるレクイエム)
  録音: 9/23 08:06・08:09、9/24 08:49・08:53・11:18・11:21・11:23、9/25 12:46・12:50:36・12:50:53 (10 本)。
  平均律クラヴィーア曲集のように、調の違う「前奏曲とフーガ」を 5 組:
    前奏曲 — 録音の実音の抜粋 (元の調のまま) の上で、シンセサイザー (11:21・12:46 から切り出した持続音の実音) が
             平均律 第 1 巻 ハ長調の前奏曲の型 (低音 → 内声 → 上の 3 音を 2 回) の分散和音を録音の和音で刻み続ける (洗脳的)。
             重低音のサブベースが根音を支え、鼓動が止まらない
    フーガ  — もう 1 本の録音の主題を、同じ調で 4 声 (録音から切り出したピアノの実音) のフーガに: 提示 → ストレッタ
  第 1 組 ホ短調  (前奏曲 11:23 / フーガ 08:53)   第 2 組 変ロ短調 (08:06 / 11:18)   第 3 組 ヘ短調 (12:46 / 08:49)
  第 4 組 ロ短調  (12:50:53 / 12:50:36)          第 5 組 ホ短調  (08:09 / 11:21)
  Contrapunctus XIV (ニ短調) — 3 つの主題 (08:53・11:18・08:49) を順に出して同時に重ねる三重フーガ → 楽譜が途切れる → 沈黙
  Choral — 4 声のコラール (08:06 の主題、掛留、アーメン終止) → 08:06 の本当の終わり
  使い方: python compose_tablet37.py <bank37.json (10 本 + シンセ)> [score_tablet37.json]
"""
import sys, json
KEY_125036 = int(sys.argv[3]) if len(sys.argv) > 3 else -3
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
BPM = 60; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2,
        '20260925_124643': 3, '20260925_125053': -3, '20260925_125036': KEY_125036}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
R1, R2, R3 = '20260925_124643', '20260925_125053', '20260925_125036'
SYN = 'VOXSY'
ORDER = [E1, E2, B1, B2, R1, RF, R2, R3, E3, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦⑧⑨⑩')))
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}
BELL = []; ARP = []; SUBG = {}
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
    for b0, b1, gain in ARP:                                              # 前奏曲: 平均律 I-1 の型の分散和音 (シンセの実音)
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); root = c['root']
                bass = 38 + (root - 2) % 12; ten = bass + 7 if (bass + 7) % 12 in c['pcs'] else bass + [x for x in range(3, 9) if (bass + x) % 12 in c['pcs']][0]
                ups = [m for m in range(55, 76) if m % 12 in c['pcs']][:3]
                seq = [bass, ten] + ups + ups
                for i_, m in enumerate(seq):
                    add('SP', bar * BPB + half + i_ * 0.25, 0.6, m, gain * (1.0 if i_ < 2 else 0.8), None, rid=SYN, pan=(-0.3, -0.15, 0.1, 0.25, 0.4, 0.1, 0.25, 0.4)[i_])
    last = None
    for bar in range(P.nbars):                                            # 重低音のサブベース (根音)
        g = SUBG.get(bar, 0)
        if g <= 0: continue
        for h in range(2):
            a = bar * BPB + 2 * h; m = 26 + (chord(P.harm[a])['root'] - 2) % 12
            if last is not None and last[0] == m and h == 1: continue
            add('SUB', a, 2.2, m, g, None); last = (m, a)
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

def prelude(P, b, rid, bars):
    """前奏曲: 録音の実音 (元の調) の上で、シンセの分散和音とサブベースが録音の和音を刻む"""
    T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=3.0, bpm=BPM, gmul=0.55)
    for v in VOICES: P.rest_bars(v, b, b + bars)
    for k in range(bars): P.dyn[b + k] = 0.5; SUBG[b + k] = 0.05
    ARP.append((b, b + bars, 0.09)); T2.MANTRA.append((b, b + bars, rid, ('PK',))); CT.LAYOUT.append((b, b + bars, KEYS[rid], {v: rid for v in VOICES}, {}))
    return bars

def fuga(P, f, rid, semis, bars=8):
    """フーガ: 主題の 4 声の提示 (2 小節ごと) → ストレッタ (拍をずらして)"""
    E = []; subj = T5.SUBJ[rid][0]; lab = '主題 %s (%s)' % (T7.MARK[rid], hm(rid))
    for k, v in enumerate('ASTB'): entry(P, f + 2 * k, v, subj, 0, lab, E)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    if bars > 8: entry(P, f + 7, 'S', subj, 0, lab + ' ストレッタ', E, beat=2); entry(P, f + 8, 'T', subj, 0, None, E, beat=1)
    T5.harm_from_entries(P, f, f + bars, E)
    for k in range(bars): P.dyn[f + k] = 1.25; SUBG[f + k] = 0.035
    ARP.append((f + bars - 2, f + bars, 0.06))
    T2.MANTRA.append((f, f + bars, rid, ('PK',))); CT.LAYOUT.append((f, f + bars, semis, VOICE_SRC, {})); return bars

def build():
    global CUT, CUT_END, TAIL
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 60); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_b1 = REC[B1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(B1, []).append((end_b1, REC[B1]['dur']))
    PAIRS = [(E1, E2, 'ホ短調'), (B1, B2, '変ロ短調'), (R1, RF, 'ヘ短調'), (R2, R3, 'ロ短調'), (E3, SY, 'ホ短調')]
    total = 5 * (4 + 10) + 20 + 1 + 8 + 5
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    for k, (ra, rb, key) in enumerate(PAIRS):
        P.section(b, '前奏曲 %d — %s の実音 (%s)' % (k + 1, hm(ra), key), '録音の実音の上で、シンセの実音が平均律 I-1 の型の分散和音を録音の和音で刻み続ける — サブベースと鼓動')
        b += prelude(P, b, ra, 4)
        P.section(b, 'フーガ %d — 〈%s〉 の主題 (%s)' % (k + 1, hm(rb), key), '4 声 (ピアノの実音) の提示 → ストレッタ — 終わりに分散和音が戻る')
        b += fuga(P, b, rb, KEYS[ra], 10)
    # ---------------- Contrapunctus XIV (ニ短調)
    f = b; s1, s2, s3 = T5.SUBJ[E2][0], T5.SUBJ[B2][0], T5.SUBJ[RF][0]
    L1, L2, L3 = '主題 ② (08:53)', '主題 ④ (11:18)', '主題 ⑥ (08:49)'
    P.section(b, 'Contrapunctus XIV — Fuga a tre soggetti (ニ短調)', '3 つの主題 (08:53・11:18・08:49) を順に出し、同時に重ねる三重フーガ — 2 度目の重なりの途中で楽譜が途切れる')
    E = []
    for k, (v, s_, lab) in enumerate((('A', s1, L1), ('S', s2, L2), ('T', s3, L3), ('B', s1, L1))): entry(P, f + 2 * k, v, s_, 0, lab, E)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    E = []; entry(P, f + 8, 'S', s1, 0, L1, E); entry(P, f + 8, 'T', s2, 0, L2, E); entry(P, f + 8, 'A', s3, 0, L3, E)
    T5.harm_from_entries(P, f + 8, f + 12, E); P.set_harms(f + 11, [['A7', 'A7', 'Dm', 'Dm']])
    E = []; entry(P, f + 12, 'B', augment(s1), 0, L1 + ' (拡大)', E); entry(P, f + 12, 'S', s2, 0, L2, E); entry(P, f + 12, 'T', s3, 0, L3, E)
    entry(P, f + 14, 'A', s2, 0, L2, E); entry(P, f + 16, 'S', s1, 0, L1, E); entry(P, f + 16, 'A', s3, 0, L3, E, beat=2); entry(P, f + 17, 'T', s2, 0, L2, E)
    T5.harm_from_entries(P, f + 12, f + 20, E)
    CUT = (f + 19) * BPB + 1
    for k in range(20): P.dyn[f + k] = 1.3; SUBG[f + k] = 0.045
    ARP.append((f + 8, f + 20, 0.05))
    BELL.append((f + 8, f + 20, 0.1, B1)); T2.MANTRA.append((f, f + 20, B1, ('PK',))); CT.LAYOUT.append((f, f + 20, 0, VOICE_SRC, {})); b = f + 20
    for v in VOICES: P.rest_bars(v, b, b + 1)
    P.harm[b * BPB:(b + 1) * BPB] = ['Dm'] * BPB
    CUT_END = (b + 1) * BPB; TAIL = (b, 1); BELL.append((b, b + 1, 0.14, B1)); T2.MANTRA.append((b, b + 1, B1, ('PK',))); CT.LAYOUT.append((b, b + 1, 0, VOICE_SRC, {})); b += 1
    # ---------------- Choral (変ロ短調)
    f = b; E = []
    P.section(b, 'Choral — 4 声のコラール 〈%s〉 (変ロ短調)' % hm(B1), '途切れたあとに 4 声のコラール: 08:06 の主題を 2 倍の長さでソプラノに、掛留、iv → i のアーメン終止 — シンセの分散和音が静かに戻る')
    t = chorale(P, f, T5.SUBJ[B1][0], E, '主題 ③ のコラール')
    T5.harm_from_entries(P, f, f + t, E)
    for q in range(2): P.harm[(f + t - 1) * BPB + 2 + q] = 'Gm'
    P.set_harms(f + t, [['Dm', 'Dm', 'Gm', 'Gm'], ['A7', 'A7', 'Dm', 'Dm'], ['Gm', 'Gm', 'Dm', 'Dm'], ['Dm']][:8 - t]); P.hold.update(range(f + t, f + 8))
    for k in range(8): P.dyn[f + k] = 1.1; SUBG[f + k] = 0.04
    ARP.append((f + 4, f + 8, 0.05)); T2.MANTRA.append((f, f + 8, B1, ('PK',))); BELL.append((f, f + 8, 0.08, B1)); CT.LAYOUT.append((f, f + 8, -4, VOICE_SRC, {})); b = f + 8
    # ---------------- Coda — 08:06 の本当の終わり
    P.section(b, 'Coda — %s の本当の終わり' % hm(B1), '08:06 の最後 (実音) → 弔鐘とサブベースが消える')
    T5.passage(P, B1, b, 5, -4, 5, fin=1.0, fout=2.5, t0=end_b1, bpm=BPM, gmul=0.65)
    for v in VOICES: P.rest_bars(v, b, b + 5)
    for k in range(5): P.dyn[b + k] = 0.5; SUBG[b + k] = 0.035
    BELL.append((b, b + 2, 0.1, B1)); T2.MANTRA.append((b, b + 5, B1, ('PK',))); CT.LAYOUT.append((b, b + 5, -4, {v: B1 for v in VOICES}, {})); b += 5
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER + [SYN], 'piano_decay': 1.5, 'src_name': {SYN: 'シンセの実音'},
    'title': 'Requiem BADA — Tablet Sessions XXXVII · Wohltemperiert',
    'subtitle': '10 本の録音を平均律のように 5 組の前奏曲とフーガで — シンセの分散和音が洗脳的に刻み、Contrapunctus XIV へ (♩=60)',
    'legend': ['TB', 'SP', 'SUB', 'PK'], 'vname': {'SP': 'シンセの分散和音', 'SUB': '重低音', 'PK': '鼓動'},
    'footer': ['前奏曲とフーガ ×5 (ホ短調 → 変ロ短調 → ヘ短調 → ロ短調 → ホ短調) → Contrapunctus XIV (ニ短調, 三重フーガ → 途切れる) → Choral (変ロ短調) → Coda 08:06',
               '前奏曲 = 録音の実音 + シンセの実音 (11:21・12:46) の分散和音 (平均律 I-1 の型) + サブベース。フーガ = 録音から切り出したピアノの実音。弔鐘、鼓動、掛留のコラール。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet37.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
