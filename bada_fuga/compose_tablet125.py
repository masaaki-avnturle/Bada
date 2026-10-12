#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXV · Inno e Requiem in Si minore (10/13 06:41・06:42 の録音を、CXXIV をベースに — 剣道の試合会場の体育館に国歌が響く。寒さではなく、身に着ける寒さが一緒になって、そこから荘厳さへ)
  Inno (国歌のように): 10/13 06:41 の最上声の音をロ短調の五音音階に寄せた 4 句の旋律を、4 声のユニゾン (オクターヴ) で、句のあいだに息をつく間 (2 拍) を置いて — はじめは何も重ねず (身に着ける寒さ)、2 句目から高い開いた 5 度 (シ・ファ#、2 オクターヴ上) の共鳴だけ。06:41 の実音 (半音上げてロ短調に) が裏に小さく
  その響きから CXXIV (Introitus → Kyrie → Sanctus → Agnus Dei → Lux aeterna) へ。Lux aeterna では 06:42 の実音 (半音上げて) の上で、讃美歌の拡大と Inno の拡大が重なる
  ロ短調で全体を: 讃美歌はロ短調の五音音階 (シ・レ・ミ・ファ#・ラ) に乗せ直し、冒頭は国歌のように 4 声のユニゾン (オクターヴ) で、和音は 7th を使わず開いた 5 度を多く (Bm・D・G・F#m・A・Em・sus4)。
  ♩=56、残響は体育館・礼拝堂のように長く (8 秒)。実音はロ短調の 9/24 08:53・11:23 と、10/12 13:03・13:07 をテープで半音上げてロ短調にしたもの。始めと終わりに深い鐘がひとつ。勝ち負けとは関係のない、気持ちの新しくなる曲
  讃美歌 (Inno): 10/12 13:06 の録音 (ト長調、1 分 15 秒 — 明るい) の最上声の音を、讃美歌のリズム (♩ ♩ ♩ ♩ 𝅗𝅥 𝅗𝅥 × 4 句) に乗せた 4 句の旋律。4 声のコラールで歌う (ピアノの 1 音)
  フーガの主題: 讃美歌の第 1 句を変ロ短調に移したもの (Kyrie) ＋ 10/03 13:27 の主題 (対主題、二重フーガ)
  形式 (♩=60):
    I.   Introitus — 讃美歌     13:06 の実音 (ト長調) の上で、讃美歌がソプラノに、コラールが包む
    II.  Kyrie — 二重フーガ     13:03 → 10/03 13:24 の実音 (変ロ短調) の上で、主題の 4 声フーガ (提示 → 13:27 の主題 → 二重 → ストレッタ)
    III. Sanctus — 讃美歌のカノン  13:06 の実音 (再び) の上で、讃美歌がソプラノとテノールのカノンに。クリスマスの鐘 (小さく)
    IV.  Agnus Dei — B-A-D-A    13:07 の実音 (変ロ短調) の上で、B-A-D-A を唱える合唱に、フーガの主題が重なる
    V.   Lux aeterna — 讃美歌と主題のストレッタ (ト長調)  13:19 の音の共鳴の上で、讃美歌の拡大 (×2) と主題のストレッタ、鐘 — 長調の和音で閉じる
  音源: 10/12・10/03 のピアノの 1 音 (立ち上がりが速く減衰するもの) + bank109。共鳴は 13:19 の音。声なし
  使い方: python compose_tablet125.py <bank1012b.json (13:03・13:06・13:07)> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet123.json]
"""
import sys, os, json, math
B1012B, B1012, B112, B109, WDIR = sys.argv[1:6]; WDIR = os.path.abspath(WDIR); OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet125.json'
sys.argv = [sys.argv[0], B1012B]
import compose_tablet as CT
import compose_heart as H
from compose import *
import compose
from clean_bank import measure

BB, B12, B3, B9 = [json.load(open(p)) for p in (B1012B, B1012, B112, B109)]; B13 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(B1012B)), '..', 't125', 'bank1013', 'bank.json'))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(B1012B)), '..', 't125', 'bank1013', 'bank.json')) else json.load(open(os.environ.get('BANK1013', 'bank1013/bank.json')))
RECS = dict(B9['recordings']); RECS.update(B3['recordings']); RECS.update(B12['recordings']); RECS.update(BB['recordings']); RECS.update(B13['recordings'])
R03, R06, R07, R24, RS = '20261012_130315', '20261012_130635', '20261012_130752', '20261003_132431', '20261003_131932'
R53, R23 = '20260924_085314', '20260924_112313'                                                    # ロ短調の実音 (9/24)
R41, R42 = '20261013_064129', '20261013_064238'                                                    # 10/13 (半音上げてロ短調に)
PSRC = R53; LOW = '20260925_130431'
BPM = 56
GMAJ = [11, 2, 4, 6, 9]; BBMIN = [11, 1, 2, 4, 6, 7, 9]                                               # 讃美歌はロ短調の五音音階、フーガはロ短調の音階
MIN_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4']
MAJ_B = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'B/D#', 'E/G#', 'Emaj7', 'F#sus4', 'B/F#']
def tr_list(lst, s): return [transpose_h([[c]], s)[0][0] for c in lst]
CANDS_G = CANDS_BB = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'Bsus4', 'F#sus4', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'F#', 'Asus4']   # ロ短調、開いた響き
SUBJ27 = [(d, m + 1) for d, m in [(0.5, 58), (0.5, 61), (0.5, 65), (0.5, 70), (1, 63), (0.5, 65), (0.5, 69), (1.5, 65), (0.5, 63), (2, 58)]]       # 10/03 13:27 の主題 (ロ短調に)

def hymn_tune():
    """13:06 の最上声の音 (ト長調の音階に寄せて、ソ 4〜ミ 5 に) を讃美歌のリズムに — 4 句、各句の終わりは長い音、最後はソ"""
    segs = RECS[R06]['segs']; tops = []
    for sg in segs:
        m = sg['m'][-1]
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < 67: m += 12
        while m > 76: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < 67: m += 12
        while m > 76: m -= 12
        tops.append(m)
    rhythm = [1, 1, 1, 1, 2, 2] * 4; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rhythm)]
    for ph in range(4):                                                                             # 句の終わり: 1・3 句はレかシ、2 句はラ、4 句はソ
        i = ph * 6 + 5; target = {0: (74, 78), 1: (76, 71), 2: (74, 78), 3: (71, 71)}[ph]                 # 句の終わり: レかファ#、ミかシ、…、シ
        out[i] = (2, min(target, key=lambda x: abs(x - out[i][1])))
    return out
HYMN = hymn_tune()
def anthem_tune():
    """10/13 06:41 の最上声の音 (+1 でロ短調に、五音音階に寄せ、シ 3〜ファ# 5 に) を、国歌のようなリズム (𝅗𝅥 ♩ ♩ 𝅗𝅥 𝅗𝅥 ♩ ♩ 𝅝 × 4 句) に — 句の終わりは長い音、最後はシ"""
    tops = []
    for sg in RECS[R41]['segs']:
        m = sg['m'][-1] + 1
        if sg['d'] < 0.4: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < 59: m += 12
        while m > 78: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < 59: m += 12
        while m > 78: m -= 12
        tops.append(m)
    rhythm = [2, 1, 1, 2, 2, 1, 1, 4] * 4; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rhythm)]
    for ph in range(4):
        i = ph * 8 + 7; target = {0: (74, 71), 1: (76, 78), 2: (74, 71), 3: (71, 71)}[ph]
        out[i] = (4, min(target, key=lambda x: abs(x - out[i][1])))
    return out
ANTHEM = anthem_tune()
def aphrase(k): return ANTHEM[8 * k: 8 * k + 8]
def phrase(k): return HYMN[6 * k: 6 * k + 6]
def to_bbmin(mat, base=67):
    out = []
    for d, m in mat:
        x = m + 3; x = min((y for y in range(x - 2, x + 3) if y % 12 in BBMIN), key=lambda y: abs(y - x)); out.append((d, x))
    return out
SUBJ = [(d, m - 12) for d, m in phrase(0)]                                                         # フーガの主題 (讃美歌の第 1 句、ロ短調、1 オクターヴ下)
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def harm_fit(P, b0, b1, entries, cands):
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            rc = set(chord(RH[a])['pcs'])
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + 1.5 * len(cc & rc) / max(1, len(cc)) + (1.2 if c == RH[a] else 0)
            cs = max(cands, key=score)
            for q in range(2): P.harm[a + q] = cs
def fit(v, mat, tr):
    if v == 'B' and min(m for _, m in mat) + tr < 36: tr += 12
    if max(m for _, m in mat) + tr > TOP[v]: tr -= 12
    if min(m for _, m in mat) + tr < RANGE[v][0]: tr += 12
    return tr
def entry(P, bar, v, mat, tr0, label, E, beat=0):
    tr = fit(v, mat, octs[v] + tr0); P.place(v, bar, mat, tr, label or '', beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def augment(mat, k=2): return [(k * d, m) for d, m in mat]
def rest_others(P, b0, b1, keep):
    for v in VOICES:
        if v not in keep: P.rest_bars(v, b0, b1)
# 段落
INNO = 0; INTRO, KYRIE, SANCTUS, AGNUS, LUX = 20, 42, 100, 122, 156; TOTAL = 176
PLAYS = [(R41, 2, 0.4, 'Inno', 1), (R53, INTRO + 2, 0.75, 'I', 0), (R03, KYRIE + 2, 0.5, 'II', 1), (R23, SANCTUS + 1, 0.6, 'III', 0), (R07, AGNUS + 2, 0.5, 'IV', 1), (R42, LUX + 1, 0.5, 'V', 1)]    # (録音, 小節, 大きさ, 段落, テープの移調)
RATE = lambda semis: 2 ** (semis / 12.0)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 1.0
    N = 'C C# D D# E F F# G G# A A# B'.split()
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sec, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = 'Bm'
        RH.append(cur); P.harm[q] = cur
    # ---- I. Introitus: 讃美歌
    P.section(INNO, 'Inno — 国歌のように (ロ短調、ユニゾン)', '10/13 06:41 の最上声の音をロ短調の五音音階に寄せた 4 句を、4 声のユニゾン (オクターヴ) で — 句のあいだに息をつく間。はじめは何も重ねず、2 句目から高い開いた 5 度の共鳴だけ。06:41 の実音 (半音上げて) が裏に小さく')
    rest_others(P, 0, 2, ''); E0 = []
    for k in range(4):
        b = 2 + 4 * k + (1 if k >= 2 else 0)
        for v in VOICES: entry(P, b, v, aphrase(k), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Inno 第 %d 句 (ユニゾン)' % (k + 1)) if v == 'S' else None, E0)
        for v in VOICES: P.rest_bars(v, b + 3, b + 4 + (1 if k == 1 else 0))
    for q in range(INNO * BPB, INTRO * BPB): P.harm[q] = 'Bm'
    for v in VOICES: P.rest_bars(v, 2 + 4 * 4 + 1, INTRO)
    P.section(INTRO, 'I. Introitus — 讃美歌 (ロ短調、はじめはユニゾンで)', '9/24 08:53 の実音 (ロ短調) の上で、讃美歌 %s (13:06 の最上声の音をロ短調の五音音階と讃美歌のリズムに) を 4 声がユニゾン (オクターヴ) で — 国歌のように。2 回目は開いた 5 度のコラールで' % ' '.join(name_of(m) for _, m in HYMN[:6]))
    rest_others(P, INTRO, INTRO + 2, ''); E = []
    for k in range(4):
        for v in VOICES: entry(P, INTRO + 2 + 2 * k, v, phrase(k), -12 + (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('讃美歌 第 %d 句 (ユニゾン)' % (k + 1)) if v == 'S' else None, E)
    for k in range(4): entry(P, INTRO + 12 + 2 * k, 'S', phrase(k), -12, '讃美歌 (コラール)' if k == 0 else None, E)
    P.hold.update(range(INTRO + 10, KYRIE)); harm_fit(P, INTRO + 2, KYRIE, E, CANDS_G); rest_others(P, INTRO + 20, KYRIE, '')
    # ---- II. Kyrie: 二重フーガ
    P.section(KYRIE, 'II. Kyrie — 二重フーガ (ロ短調)', '13:03 の実音 (半音上げてロ短調に) の上で、主題 %s (讃美歌の第 1 句) の 4 声の提示 → 10/03 13:27 の主題 (対主題、ロ短調に) → 二重 → ストレッタ' % ' '.join(name_of(m) for _, m in SUBJ))
    f = KYRIE + 2; E = []; rest_others(P, KYRIE, f, '')
    for k, v in enumerate('ASBT'):
        entry(P, f + 3 * k, v, SUBJ, 7 if k % 2 else 0, '主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 3 * k, f + 3 * k + 3)
    harm_fit(P, KYRIE, f + 12, E, CANDS_BB); f += 12; E = []
    for k, v in enumerate('SATB'):
        entry(P, f + 3 * k, v, SUBJ27, 7 if k % 2 else 0, '13:27 の主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'SATB'[k + 1:]: P.rest_bars(w, f + 3 * k, f + 3 * k + 3)
    harm_fit(P, f, f + 12, E, CANDS_BB); f += 12; E = []
    for k in range(3):
        entry(P, f + 4 * k, 'SAT'[k], SUBJ27, 0, '二重 (主題 + 13:27 の主題)' if k == 0 else None, E); entry(P, f + 4 * k, 'TBA'[k], SUBJ, 0, None, E)
        for w in VOICES:
            if w not in ('SAT'[k], 'TBA'[k]): P.rest_bars(w, f + 4 * k, f + 4 * k + 4)
    harm_fit(P, f, f + 12, E, CANDS_BB); f += 12; E = []
    for k, v in enumerate('ASTB'): entry(P, f + k, v, SUBJ, 0, '主題 ストレッタ' if k == 0 else None, E)
    entry(P, f + 4, 'B', augment(SUBJ), 0, '主題 (拡大 ×2)', E); entry(P, f + 5, 'S', invert(SUBJ), 0, '主題 (反行)', E)
    harm_fit(P, f, SANCTUS, E, CANDS_BB); rest_others(P, f + 8, SANCTUS, '')
    # ---- III. Sanctus: 讃美歌のカノン
    P.section(SANCTUS, 'III. Sanctus — 讃美歌のカノン (ロ短調)', '9/24 11:23 の実音 (ロ短調) の上で、讃美歌がソプラノとテノール (1 小節遅れ、オクターヴ下) のカノンに')
    E = []; rest_others(P, SANCTUS, SANCTUS + 1, '')
    for k in range(4): entry(P, SANCTUS + 1 + 2 * k, 'S', phrase(k), -12, '讃美歌 (カノン)' if k == 0 else None, E); entry(P, SANCTUS + 2 + 2 * k, 'T', phrase(k), -12, None, E)
    for k in range(4): entry(P, SANCTUS + 11 + 2 * k, 'S', phrase(k), -12, None, E); entry(P, SANCTUS + 12 + 2 * k, 'T', phrase(k), -12, None, E)
    P.hold.update(range(SANCTUS + 1, AGNUS)); harm_fit(P, SANCTUS + 1, AGNUS, E, CANDS_G); rest_others(P, AGNUS - 2, AGNUS, '')
    # ---- IV. Agnus Dei: B-A-D-A
    P.section(AGNUS, 'IV. Agnus Dei — B-A-D-A (ロ短調)', '13:07 の実音 (半音上げてロ短調に) の上で、B-A-D-A を唱える合唱に、フーガの主題が重なる')
    rest_others(P, AGNUS, AGNUS + 2, ''); E = []
    for k in range(8):
        bb = AGNUS + 2 + 4 * k
        if bb + 4 > LUX: break
        P.place('A', bb, H.BADA, 1, 'B-A-D-A' if k == 0 else None); E.append((bb * BPB, [(d, m + 1) for d, m in H.BADA]))
        if k % 2 == 1: entry(P, bb, 'S', SUBJ, 0, '主題' if k == 1 else None, E)
        else: P.rest_bars('S', bb, bb + 4)
        P.rest_bars('T', bb, bb + 4); P.place('B', bb, [(4, 47)] * 4, 0, None) if k % 2 == 0 else P.rest_bars('B', bb, bb + 4)
    P.hold.update(range(AGNUS + 2, LUX)); harm_fit(P, AGNUS + 2, LUX, E, CANDS_BB)
    for v in VOICES: P.rest_bars(v, AGNUS + 2 + 4 * 8, LUX) if AGNUS + 2 + 32 < LUX else None
    # ---- V. Lux aeterna
    P.section(LUX, 'V. Lux aeterna — 讃美歌と Inno の拡大、主題のストレッタ (ロ短調)', '10/13 06:42 の実音 (半音上げて) と 13:19 の音の共鳴の上で、讃美歌の拡大 (×2)、つづいて Inno の第 4 句の拡大がソプラノに、主題が下の 3 声でストレッタ — 最後は開いた 5 度 (シ・ファ#) のユニゾンで、深い鐘がひとつ')
    E = []; subj_g = phrase(0)
    entry(P, LUX, 'S', augment(phrase(0)), -12, '讃美歌 (拡大 ×2)', E); entry(P, LUX + 8, 'S', augment(aphrase(3)), 0, 'Inno 第 4 句 (拡大 ×2)', E)
    for k, v in enumerate('ATB'): entry(P, LUX + 1 + 2 * k, v, subj_g, 0, '主題 (長調で、ストレッタ)' if k == 0 else None, E)
    for k, v in enumerate('ATB'): entry(P, LUX + 9 + 2 * k, v, subj_g, 0, None, E)
    rest_others(P, LUX, LUX + 1, 'S'); P.rest_bars('T', LUX + 1, LUX + 3); P.rest_bars('B', LUX + 1, LUX + 5); P.rest_bars('T', LUX + 9, LUX + 11); P.rest_bars('B', LUX + 9, LUX + 13)
    harm_fit(P, LUX, TOTAL - 4, E, CANDS_G)
    for b in range(TOTAL - 4, TOTAL): P.set_harm(b, 'Bm'); P.hold.add(b)
    P.place('S', TOTAL - 4, [(4, 78)] * 4, 0, 'ファ# (開いた 5 度)'); P.place('A', TOTAL - 4, [(4, 71)] * 4, 0, ''); P.place('T', TOTAL - 4, [(4, 66)] * 4, 0, ''); P.place('B', TOTAL - 4, [(4, 47)] * 4, 0, ''); P.rest_bars('S', TOTAL - 1, TOTAL)
    for k in range(TOTAL): P.dyn[k] = 0.95 if k < LUX else 1.1 - 0.15 * max(0, k - (TOTAL - 4))
    return P

def post(P, events, ex):
    for rid, bar, g, sec, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 2 else 0.02, fout=3.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s%s)' % ({R53: '9/24 08:53', R03: '10/12 13:03', R23: '9/24 11:23', R07: '10/12 13:07', R41: '10/13 06:41', R42: '10/13 06:42'}[rid], sec, '、半音上げてロ短調に' if sm else ''))
    add('X', 0, 10, 35, 0.4, '深い鐘 (ひとつ)')
    q = 0; first = True                                                                             # 共鳴 (13:19 の音) — Lux aeterna と Introitus で
    while q < TOTAL * BPB:
        h = P.harm[q]; q1 = q
        while q1 < TOTAL * BPB and P.harm[q1] == h: q1 += 1
        for cut in (6 * BPB, INTRO * BPB):                                                      # Inno の区切り (1 句目は重ねない / 2 句目から高い 5 度)
            if q < cut < q1: q1 = cut
        bar = q // BPB
        if bar < 6: pass                                                                            # Inno の 1 句目: 何も重ねない (身に着ける寒さ)
        elif bar < INTRO:                                                                           # Inno の 2 句目から: 高い開いた 5 度 (シ・ファ#) だけ
            d = max(1.0, (q1 - q) + 0.6); g = 0.07
            for i, m in enumerate((83, 90)): add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
        else:
            d = max(1.0, (q1 - q) + 0.6); c = chord(h)
            tones = [min((x for x in range(52, 76) if x % 12 == p), key=lambda x: abs(x - 62)) for p in (c['root'], c['fifth'], c['third'])]
            g = 0.2 if bar >= LUX else 0.11
            for i, m in enumerate(tones): add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.7), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
            add('PF', q, d, tones[0] - 12, g * 0.6, None, rid='VOXRS', rel=1.5, layer='res')
        q = q1
    add('X', (TOTAL - 2) * BPB, 12, 35, 0.45, '深い鐘 (ひとつ)')

META = {'style': 'recsampler', 'bank': None, 'rec_order': [R41, R53, R03, R23, R07, R42], 'piano_decay': 2.6, 'reverb': [8.0, 3.0, 0.5], 'src_name': {'VOXRS': '共鳴 (13:19 の音)'},
        'title': 'Requiem BADA — CXXV · Inno e Requiem in Si minore',
        'subtitle': '10/13 06:41・06:42 を CXXIV に — 剣道の試合会場の体育館に国歌が響く: Inno (06:41 の音をロ短調の五音音階に、4 声のユニゾン、句のあいだの間、はじめは何も重ねず) → その響きから荘厳な Requiem へ (Introitus → Kyrie 二重フーガ → Sanctus → Agnus Dei → Lux aeterna: 06:42 の上で讃美歌と Inno の拡大)。♩=56、長い残響',
        'legend': ['PF', 'X'], 'vname': {'PF': '共鳴 (13:19 の音)', 'X': '鐘'},
        'footer': ['Inno (国歌のように、ユニゾン) → I. Introitus (讃美歌、ユニゾン → コラール) → II. Kyrie (二重フーガ) → III. Sanctus (カノン) → IV. Agnus Dei (B-A-D-A) → V. Lux aeterna (讃美歌と Inno の拡大、ストレッタ、開いた 5 度のユニゾンで閉じる)',
                   '讃美歌 = 13:06 の最上声の音をロ短調の五音音階 (シ・レ・ミ・ファ#・ラ) と ♩ ♩ ♩ ♩ 𝅗𝅥 𝅗𝅥 の 4 句に。7th なし、sus4 と開いた 5 度。始めと終わりに深い鐘がひとつ。声なし。']}

def make_bank(path):
    out = []
    for s in BB['samples'] + B12['samples']:
        atk, dec = measure(s['file'])
        if atk <= 0.12 and dec <= -0.1: out.append(s)
    out += [dict(s, rid='VOXRS') for s in B3['samples'] if s['rid'] == RS] + B9['samples']
    json.dump(dict(recordings={}, samples=out), open(path, 'w'), ensure_ascii=False)

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; make_bank(bank_out); META['bank'] = bank_out
    print('anthem', ' '.join('%s:%g' % (name_of(m), d) for d, m in ANTHEM), '| hymn', ' '.join('%s:%g' % (name_of(m), d) for d, m in HYMN[:6]), '| subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ))
    compose.main(OUT, seed=125, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
