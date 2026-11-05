#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXIX · Lebewohl — Requiem sulla ninna nanna (tablet117 の曲に合わせて、ベートーヴェンの「告別」の動機を被せて、requiem に仕上げる)
  土台: CXVII · Ninna nanna 10/03 (tablet117.mp4 の音をそのまま、表として): 変ロ短調 (くつろぎ) → ヘ長調 (暖まり) → ヘ短調 (冷え) → 変ロ長調 (眠り)、♩=60 → 44、12 分 59 秒
  被せる主題: ベートーヴェン ピアノ・ソナタ第 26 番「告別」(Les Adieux, Op. 81a, 1810 年、公有) の冒頭の「Le-be-wohl」の動機 — ソ・ファ・ミ (角笛の別れの呼び声) — を各段階の調で:
    I.   Introitus (変ロ短調)      ホルンの Lebewohl (ファ・ミ♭・レ♭、拡大) が遠くで呼び交わす、高い開いた 5 度の弦が pp、コントラバスの保続、深い鐘
    II.  Kyrie (ヘ長調)            Lebewohl (ド・シ♭・ラ) のカノン: フルート → オーボエ → クラリネット → ホルン、弦のフガート (ソ・ファ・ミ・レ・ド)
    III. Lacrimosa (ヘ短調)        Lebewohl (ド・シ♭・ラ♭) の拡大が Vn I に、弦のため息、半音で下る低音 (ファ・ミ・ミ♭・レ・レ♭・ド)、トロンボーン、ティンパニの遠い拍
    IV.  Agnus Dei — Lux aeterna (変ロ長調)  Lebewohl (ファ・ミ♭・レ) の大きな拡大がホルン → Vn I → フルートに、高い開いた 5 度、最後は深い鐘と消える
  音源: 土台は tablet117 の音 (REC)、被せるのは管弦楽だけ (synth の合成)。♩=60 で 1 拍 = 1 秒 (土台のテンポの変化は和音の採譜で追う)
  使い方: python compose_tablet139.py <bank117.json (tablet117 の採譜)> <wav のフォルダ> [score_tablet139.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet139.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']
R117 = '20261003_117000'
DUR = RECS[R117]['dur']; TOTAL = int(math.ceil(DUR / 4.0)) + 1
BPM = 60
S1, S2, S3, S4 = 0, 38, 80, 141                                                                    # CXVII の 4 段階 (秒 ≈ 拍: 0 / 152 / 320 / 564)
def key_of(bar): return 'Bbm' if bar < S2 else 'F' if bar < S3 else 'Fm' if bar < S4 else 'Bb'
C_BBM = ['Bbm', 'Db', 'Gb', 'Fm', 'Ab', 'Ebm', 'Bbm/Db', 'Gb/Bb', 'F', 'F7', 'Fsus4', 'Ebm/Gb']
C_F = ['F', 'Bb', 'C', 'C7', 'Dm', 'Gm', 'Am', 'F/A', 'Bb/D', 'C/E', 'Gm7', 'Csus4', 'F/C']
C_FM = ['Fm', 'Ab', 'Db', 'Cm', 'Bbm', 'Eb', 'C', 'C7', 'Fm/Ab', 'Db/F', 'Bbm/Db', 'Csus4', 'Fm/C']
C_BB = ['Bb', 'Eb', 'F', 'F7', 'Gm', 'Cm', 'Dm', 'Bb/D', 'Eb/G', 'F/A', 'Cm7', 'Fsus4', 'Bb/F']
# Lebewohl (ソ・ファ・ミ) を各段階の調で: (拍, MIDI)
def leb(s, f, m, k=1): return [(1 * k, s), (1 * k, f), (2 * k, m)]
def lebx(s, f, m, r, d, k=1): return [(1 * k, s), (1 * k, f), (1 * k, m), (0.5 * k, r), (0.5 * k, d), (2 * k, m)]       # ソ・ファ・ミ・レ・ド・ミ (展開)
LEB_BBM = (65, 63, 61); LEB_F = (72, 70, 69); LEB_FM = (72, 70, 68); LEB_BB = (77, 75, 74)
GROUND_FM = [53, 52, 51, 50, 49, 48, 48, 53]                                                        # ファ・ミ・ミ♭・レ・レ♭・ド・ド・ファ (半音で下る、2 小節)
PLAYS = [(R117, 0, 0.55, 0)]
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []; RH = []; RECQ = set()                                                                 # RECQ: 録音が鳴っている拍 (その和音を優先する)
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
OG = 0.34
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)
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
            rc = set(chord(RH[a])['pcs']); rec = a in RECQ; prev = P.harm[a - 1] if a > 0 else None
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + (1.5 if rec else 0.4) * len(cc & rc) / max(1, len(cc)) + ((1.2 if rec else 0.2) if c == RH[a] else 0) - (0.3 if (c == prev and notes) else 0)
            cs = max(cands, key=score)
            for q in range(2): P.harm[a + q] = cs
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def augment(mat, k=2): return [(k * d, m) for d, m in mat]
def line(v, bar, mat, tr, g, label=None, beat=0):
    t = bar * BPB + beat; first = True
    for d, m in mat:
        oadd(v, t, d, m + tr, g, label if first else None); first = False; t += d
    return (bar * BPB + beat, [(d, m + tr) for d, m in mat])
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def chord_pad(P, b0, b1, parts, g, label=None):
    q = b0 * BPB; first = True
    while q < b1 * BPB:
        h = P.harm[q]; q1 = q
        while q1 < b1 * BPB and P.harm[q1] == h: q1 += 1
        for v, lo, hi in parts:
            tones = tones_of(h, lo, hi)
            for i, m in enumerate(tones[:3] if v != 'CB' else [min(tones)]): oadd(v, q + 0.03 * i, (q1 - q) + 0.3, m if v != 'CB' else m - 12, g * (1.0 if i == 0 else 0.8), label if (first and i == 0) else None); first = False
        q = q1
def roots(P, b0, b1, parts, g, label=None, every=1):
    first = True
    for b in range(b0, b1):
        for k in range(0, BPB, every):
            r = 38 + chord(P.harm[b * BPB + k])['root']
            for v, tr in parts: oadd(v, b * BPB + k, every + 0.15, r + tr, g, label if first else None); first = False
def walking(P, b0, b1, g, label):
    """モーツァルトの Introitus のような歩く低音: 1 拍ずつ、根音と 5 度を行き来 (Cb・Vc)"""
    first = True
    for b in range(b0, b1):
        for k in range(BPB):
            c = chord(P.harm[b * BPB + k]); m = 38 + (c['root'] if k % 2 == 0 else c['fifth'])
            if m > 47: m -= 12
            oadd('CB', b * BPB + k, 0.95, m, g, label if first else None); oadd('VC', b * BPB + k, 0.95, m + 12, g * 0.7); first = False
def sighs(P, b0, b1, g, label, v1='V1', v2='V2'):
    """ため息 (2 音のスラー: 上の隣の音 → 和音の音) を 1・3 拍に、Vn I と Vn II が交互に"""
    SC = [11, 1, 2, 4, 6, 7, 9, 10]; first = True
    for b in range(b0, b1):
        for k in (0, 2):
            h = P.harm[b * BPB + k]; t = tones_of(h, 69, 83); m = t[1] if len(t) > 1 else t[0]
            up = min((x for x in range(m + 1, m + 3) if x % 12 in SC), default=m + 2)
            v = v1 if (b + k // 2) % 2 == 0 else v2
            oadd(v, b * BPB + k, 0.6, up, g, label if first else None); oadd(v, b * BPB + k + 0.5, 1.4, m, g * 0.8); first = False
def tremolo(P, b0, b1, g, label):
    """Dies irae のような弦のトレモロ (8 分音符の繰り返し): Vn II・Va"""
    first = True
    for b in range(b0, b1):
        for k in range(BPB * 2):
            h = P.harm[b * BPB + k // 2]; t = tones_of(h, 62, 76)
            oadd('V2', b * BPB + k * 0.5, 0.45, t[-1], g * (1.0 if k % 2 == 0 else 0.8), label if first else None); oadd('VA', b * BPB + k * 0.5, 0.45, t[0], g * 0.9); first = False

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.9
    segs = RECS[R117]['segs']
    for q in range(TOTAL * BPB):
        cur = None
        if q < DUR:
            cur = segs[0]['ch']
            for s in segs:
                if s['t'] <= q: cur = s['ch']
            RECQ.add(q)
        if cur is None: cur = key_of(q // BPB)
        RH.append(cur); P.harm[q] = cur
    for v in VOICES: P.rest_bars(v, 0, TOTAL)                                                       # 管弦楽だけ
    s, f, m = LEB_BBM
    P.section(S1, 'I. Introitus — くつろぎの上に (変ロ短調, ♩=60)', 'CXVII の I (10/03 13:24 の実音) の上で、ホルンの Lebewohl (ファ・ミ♭・レ♭、拡大) が遠くで呼び交わす — 高い開いた 5 度の弦が pp、コントラバスの保続、低いクラリネット、深い鐘')
    E = [((b) * BPB, [(d, mm + tr) for d, mm in leb(s, f, m, 2)]) for b, tr in ((4, 0), (10, -12), (18, 0), (26, -12), (32, 0))]
    harm_fit(P, S1 + 2, S2, E, C_BBM)
    s, f, m = LEB_F
    P.section(S2, 'II. Kyrie — カノン (ヘ長調)', 'CXVII の II (9/24 11:18 の実音、暖かい) の上で、Lebewohl (ド・シ♭・ラ) のカノン: フルート → オーボエ → クラリネット → ホルン (2 小節ずつ)、弦のフガート (ソ・ファ・ミ・レ・ド)')
    E = [((S2 + 2 + 2 * k) * BPB, [(d, mm + tr) for d, mm in leb(s, f, m)]) for k, tr in enumerate((12, 0, -12, -12))]
    E += [((S2 + 14 + 2 * k) * BPB, [(d, mm + tr) for d, mm in leb(s, f, m)]) for k, tr in enumerate((12, 0, -12, -24))]
    E += [((S2 + 24 + 3 * k) * BPB, [(d, mm + tr) for d, mm in lebx(s, f, m, m - 2, m - 4)]) for k, tr in enumerate((12, 0, -12, -24))]
    E += [((S2 + 36) * BPB, [(d, mm) for d, mm in lebx(s, f, m, m - 2, m - 4, 2)])]
    harm_fit(P, S2 + 1, S3, E, C_F)
    s, f, m = LEB_FM
    P.section(S3, 'III. Lacrimosa — 冷え (ヘ短調)', 'CXVII の III (9/24 08:49 の実音、テンポが落ちる) の上で、Lebewohl (ド・シ♭・ラ♭) の拡大が Vn I に、弦のため息 (2 音のスラー)、半音で下る低音 (ファ・ミ・ミ♭・レ・レ♭・ド)、トロンボーンの和音、ティンパニの遠い拍、低いクラリネット')
    E = [((S3 + 3 + 8 * k) * BPB, [(d, mm + tr) for d, mm in leb(s, f, m, 2)]) for k, tr in enumerate((0, -12, 0, 12, -12, 0, -24))]
    E += [((S3 + 40) * BPB, [(d, mm) for d, mm in lebx(s, f, m, m - 1, m - 3, 2)])]
    harm_fit(P, S3 + 1, S4, E, C_FM)
    for b in range(S3 + 20, S3 + 36):
        for k in range(BPB): P.harm[b * BPB + k] = ['Fm', 'C/E', 'Fm/Eb', 'Bbm/Db', 'Db', 'C7', 'C7', 'Fm'][((b - S3) % 2) * 4 + k]
    s, f, m = LEB_BB
    P.section(S4, 'IV. Agnus Dei — Lux aeterna (変ロ長調)', 'CXVII の IV (眠り、10/03 13:27 を半分の大きさで、♩=50 → 44) の上で、Lebewohl (ファ・ミ♭・レ) の大きな拡大 (×4) がホルン → Vn I → フルートに、高い開いた 5 度が pp、最後は深い鐘と一緒に消える')
    E = [((S4 + 2) * BPB, [(d, mm - 12) for d, mm in leb(s, f, m, 4)]), ((S4 + 14) * BPB, [(d, mm) for d, mm in leb(s, f, m, 4)]), ((S4 + 26) * BPB, [(d, mm + 12) for d, mm in leb(s, f, m, 4)]), ((S4 + 38) * BPB, [(d, mm - 12) for d, mm in leb(s, f, m, 4)])]
    harm_fit(P, S4 + 1, TOTAL - 8, E, C_BB)
    for q in range((TOTAL - 8) * BPB, TOTAL * BPB): P.harm[q] = 'Bb'
    return P

def post(P, events, ex):
    add('REC', 0, DUR, 0, 0.55, None, src=os.path.join(WDIR, R117 + '.wav'), off=0.0, fin=0.02, fout=6.0, semis=0, rid=R117 + '.wav', tag='CXVII · Ninna nanna 10/03 (tablet117) — 土台、そのまま')
    def cold(b0, b1, g, hi, lo, label, step=4):
        for b in range(b0, b1, step):
            oadd('V1', b * BPB, step * BPB + 0.5, hi, g, label if b == b0 else None); oadd('V2', b * BPB + 0.05, step * BPB + 0.5, lo, g * 0.85)
    # I. Introitus
    add('X', 0, 10, 34, 0.28, '深い鐘 (ひとつ)')
    cold(S1 + 2, S2 - 2, 0.1, 89, 82, '高い開いた 5 度 (シ♭・ファ, pp)')
    for b in range(S1 + 2, S2 - 2, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 34, 0.16, 'コントラバスの保続 (シ♭)' if b == S1 + 2 else None)
    s, f, m = LEB_BBM
    for k, (b, tr) in enumerate(((4, 0), (10, -12), (18, 0), (26, -12), (32, 0))): line('HN', b, leb(s, f, m, 2), tr, 0.2 if tr == 0 else 0.16, 'ホルン — Lebewohl (ファ・ミ♭・レ♭、告別の呼び声)' if k == 0 else None)
    for k, b in enumerate((14, 22, 30)): line('CL', b, leb(s, f, m, 2), -12, 0.14, '低いクラリネットの答え' if k == 0 else None)
    chord_pad(P, S1 + 8, S2 - 2, [('VA', 55, 67)], 0.07)
    # II. Kyrie
    s, f, m = LEB_F
    for k, (v, tr) in enumerate((('FL', 12), ('WW', 0), ('CL', -12), ('HN', -12))): line(v, S2 + 2 + 2 * k, leb(s, f, m), tr, 0.16, 'Kyrie — Lebewohl のカノン (フルート → オーボエ → クラリネット → ホルン)' if k == 0 else None)
    for k, (v, tr) in enumerate((('FL', 12), ('WW', 0), ('CL', -12), ('HN', -24))): line(v, S2 + 14 + 2 * k, leb(s, f, m), tr, 0.16, None)
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, S2 + 24 + 3 * k, lebx(s, f, m, m - 2, m - 4), tr, 0.2, '弦のフガート (ソ・ファ・ミ・レ・ド)' if k == 0 else None)
    line('V1', S2 + 36, lebx(s, f, m, m - 2, m - 4, 2), 0, 0.2, None); line('FL', S2 + 36, lebx(s, f, m, m - 2, m - 4, 2), 12, 0.12, None)
    chord_pad(P, S2 + 6, S3 - 1, [('V2', 62, 76), ('VA', 55, 67)], 0.08, 'Vn II・Va の和音 (薄く)')
    roots(P, S2 + 10, S3 - 1, [('VC', 12), ('CB', 0)], 0.1, 'Vc・Cb の根音', every=4)
    # III. Lacrimosa
    s, f, m = LEB_FM
    for k, tr in enumerate((0, -12, 0, 12, -12, 0, -24)): line('V1' if tr >= 0 else 'VA', S3 + 3 + 8 * k, leb(s, f, m, 2), tr, 0.2, 'Lacrimosa — Lebewohl の拡大 (ド・シ♭・ラ♭)' if k == 0 else None)
    line('WW', S3 + 40, lebx(s, f, m, m - 1, m - 3, 2), 0, 0.16, 'オーボエ'); line('CL', S3 + 48, leb(s, f, m, 2), -12, 0.14, None)
    sighs(P, S3 + 4, S4 - 2, 0.1, 'ため息 (2 音のスラー、Vn I・Vn II)')
    first = True
    for b in range(S3 + 20, S3 + 36):
        for k in range(BPB):
            mm = GROUND_FM[((b - S3) % 2) * 4 + k]
            oadd('VC', b * BPB + k, 1.0, mm, 0.16, '半音で下る低音 (Vc・Cb)' if first else None); oadd('CB', b * BPB + k, 1.0, mm - 12, 0.16); first = False
    chord_pad(P, S3 + 8, S4 - 2, [('TB', 43, 57)], 0.08, 'トロンボーンの和音')
    for k, b in enumerate(range(S3 + 24, S4 - 4, 4)): oadd('TP', b * BPB, 2.0, 41, 0.14, 'ティンパニ (遠い拍)' if k == 0 else None)
    # IV. Agnus Dei — Lux aeterna
    s, f, m = LEB_BB
    line('HN', S4 + 2, leb(s, f, m, 4), -12, 0.18, 'Agnus Dei — Lebewohl の大きな拡大 (ファ・ミ♭・レ、ホルン)'); line('V1', S4 + 14, leb(s, f, m, 4), 0, 0.2, 'Vn I'); line('FL', S4 + 26, leb(s, f, m, 4), 12, 0.12, 'フルート'); line('HN', S4 + 38, leb(s, f, m, 4), -12, 0.14, None)
    cold(S4 + 1, TOTAL - 4, 0.09, 94, 89, 'Lux aeterna — 高い開いた 5 度 (ファ・シ♭, pp)')
    chord_pad(P, S4 + 4, TOTAL - 10, [('VA', 55, 67), ('VC', 43, 55)], 0.07)
    for b in range(S4 + 2, TOTAL - 6, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 34, 0.12, None)
    add('X', (TOTAL - 5) * BPB, 16, 34, 0.32, '深い鐘 (最後に)')
    for e in extras:                                                                                # IV は土台が眠りで小さいので、被せる管弦楽も 0.6 倍に (土台が表のまま)
        if e['v'] not in ('REC', 'X') and e['beat'] >= S4 * BPB: e['gain'] = round(e['gain'] * 0.6, 4)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R117], 'piano_decay': 2.6, 'reverb': [9.0, 3.5, 0.5], 'orchestra': True,
        'title': 'Requiem BADA — CXXXIX · Lebewohl — Requiem sulla ninna nanna',
        'subtitle': 'tablet117 (CXVII · Ninna nanna 10/03) の曲に合わせて、ベートーヴェンの「告別」(Les Adieux, Op. 81a) の Lebewohl の動機 (ソ・ファ・ミ) を各段階の調で被せ、requiem に仕上げる: Introitus (変ロ短調、ホルンの呼び声) → Kyrie (ヘ長調、カノン) → Lacrimosa (ヘ短調、ため息と下る低音) → Agnus Dei — Lux aeterna (変ロ長調、大きな拡大、深い鐘)。♩=60',
        'legend': ['X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'CL', 'HN', 'TB', 'TP'], 'vname': {'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TB': 'Tb', 'TP': 'Timp'},
        'footer': ['主題 = ベートーヴェン「告別」の冒頭「Le-be-wohl」(ソ・ファ・ミ、角笛の別れの呼び声; 1810 年、公有) — 動機だけを借りて、各段階の調 (変ロ短調・ヘ長調・ヘ短調・変ロ長調) で拡大とカノンに。ほかの旋律の引用はなし',
                   '土台は tablet117 の音をそのまま (表)。和音は土台の採譜 (拍ごと) を優先しつつ主題の音を含む和音を選ぶ。被せるのは管弦楽だけ (synth の合成)。鐘は始めと終わりに深いもの。声なし。']}

if __name__ == '__main__':
    print('base', DUR, 's bars', TOTAL)
    compose.main(OUT, seed=139, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
