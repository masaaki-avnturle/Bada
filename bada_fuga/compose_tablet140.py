#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXL · Sinfonia della tristezza (tablet139 の曲をショパンの「別れの曲」に合わせて、シンフォニーで作り換える)
  土台: CXXXIX · Lebewohl — Requiem sulla ninna nanna (tablet139.mp4 の音をそのまま): 変ロ短調 → ヘ長調 → ヘ短調 → 変ロ長調、♩=60、13 分 12 秒
  主題: ショパン 練習曲 Op. 10-3 ホ長調「別れの曲」(Tristesse、1832 年、公有) の旋律の頭 — 記憶からの採譜 (細部は原曲と違いうる): ソ# | シ ラ ソ# ファ# ソ# ・ ファ# ミ レ# ミ ／ 上る句 ソ# ラ シ ド# レ# ミ レ# ド# シ ラ ソ# ファ# ミ レ# ミ
        各段階の調で: I 変ニ長調 (変ロ短調の平行長調) → II ヘ長調 → III 変イ長調 (ヘ短調の平行長調) → IV 変ロ長調
  シンフォニー (管弦楽だけ、synth の合成): I 弦 (Vn I が歌う) → II 木管 → 総奏の第 1 主題 → III 中間部 (原曲の嵐のように: 弦のトレモロ、トロンボーン、ティンパニの高まり) → 主題の静かな再現 → IV 総奏の再現 → 消えていく結尾
  使い方: python compose_tablet140.py <bank139.json (tablet139 の採譜)> <wav のフォルダ> [score_tablet140.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet140.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']
R139 = '20261105_139000'
DUR = RECS[R139]['dur']; TOTAL = int(math.ceil(DUR / 4.0)) + 1
BPM = 60
S1, S2, S3, S4 = 0, 38, 80, 141                                                                    # 土台の 4 段階 (秒 = 拍)
def key_of(bar): return 'Db' if bar < S2 else 'F' if bar < S3 else 'Ab' if bar < S4 else 'Bb'
C_DB = ['Db', 'Gb', 'Ab', 'Ab7', 'Bbm', 'Ebm', 'Fm', 'Db/F', 'Gb/Bb', 'Ab/C', 'Ebm7', 'Db/Ab']
C_F = ['F', 'Bb', 'C', 'C7', 'Dm', 'Gm', 'Am', 'F/A', 'Bb/D', 'C/E', 'Gm7', 'F/C']
C_AB = ['Ab', 'Db', 'Eb', 'Eb7', 'Fm', 'Bbm', 'Cm', 'Ab/C', 'Db/F', 'Eb/G', 'Bbm7', 'Ab/Eb']
C_FM = ['Fm', 'Ab', 'Db', 'Cm', 'Bbm', 'Eb', 'C', 'C7', 'Fm/Ab', 'Db/F', 'Bbm/Db', 'Fm/C']
C_BB = ['Bb', 'Eb', 'F', 'F7', 'Gm', 'Cm', 'Dm', 'Bb/D', 'Eb/G', 'F/A', 'Cm7', 'Bb/F']
# ショパン Op. 10-3 の旋律の頭 (ホ長調、記憶からの採譜; 拍 = 4 分音符、原曲の 2/4 の 2 小節が 4/4 の 1 小節)
CH_A = [(0.5, 68), (0.75, 71), (0.25, 69), (0.5, 68), (0.5, 66), (1.0, 68), (0.5, 66), (0.5, 64), (0.5, 63), (1.5, 64)]                      # ソ# | シ ラ ソ# ファ# ソ# ファ# ミ レ# ミ
CH_B = [(0.5, 68), (0.5, 69), (0.5, 71), (0.5, 73), (0.5, 75), (1.0, 76), (0.5, 75), (0.5, 73), (0.5, 71), (0.5, 69), (0.5, 68), (0.5, 66), (1.0, 64), (0.5, 63), (1.5, 64)]   # 上る句
CH = CH_A + CH_B                                                                                   # 16.5 拍
TR_KEY = {'Db': -3, 'F': 1, 'Ab': 4, 'Bb': 6}                                                       # ホ長調 → 各段階の調
def ch(key, oct_=0, part=None): return [(d, m + TR_KEY[key] + oct_) for d, m in (CH if part is None else part)]
PLAYS = [(R139, 0, 0.5, 0)]
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
    segs = RECS[R139]['segs']
    for q in range(TOTAL * BPB):
        cur = None
        if q < DUR:
            cur = segs[0]['ch']
            for s in segs:
                if s['t'] <= q: cur = s['ch']
            RECQ.add(q)
        if cur is None: cur = key_of(q // BPB)
        RH.append(cur); P.harm[q] = cur
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. Tristesse — 弦が歌う (変ニ長調, ♩=60)', '土台の I (変ロ短調、くつろぎ) の上で、ショパンの「別れの曲」の旋律 (記憶からの採譜) を平行長調の変ニ長調で Vn I が歌う — Vn II・Va の和音、Vc・Cb の根音、ホルンの支え、高い開いた 5 度')
    E = [((S1 + 4) * BPB, ch('Db')), ((S1 + 14) * BPB, ch('Db')), ((S1 + 26) * BPB, ch('Db', 12, CH_A))]
    harm_fit(P, S1 + 3, S2, E, C_DB)
    P.section(S2, 'II. 木管から総奏へ (ヘ長調)', '土台の II (暖まり) の上で、旋律をフルートとオーボエが、クラリネットとホルンが答える → 総奏の第 1 主題 (Vn I・フルート・ホルン・トランペット、ティンパニ)')
    E = [((S2 + 2) * BPB, ch('F', 12)), ((S2 + 12) * BPB, ch('F', -12)), ((S2 + 22) * BPB, ch('F')), ((S2 + 32) * BPB, ch('F', 0, CH_B))]
    harm_fit(P, S2 + 1, S3, E, C_F)
    P.section(S3, 'III. 中間部 — 嵐 (ヘ短調 → 変イ長調)', '土台の III (冷え) の上で、原曲の中間部のように: 弦のトレモロ、半音の動き、トロンボーン、ティンパニの高まり — 鎮まって、旋律が変イ長調で静かに戻る (Vn I、クラリネット)')
    E = [((S3 + 2) * BPB, [(d, m) for d, m in ch('Ab', -12, CH_A)]), ((S3 + 10) * BPB, [(d, m) for d, m in ch('Ab', -12, CH_A)])]
    harm_fit(P, S3 + 1, S3 + 20, E, C_FM)
    for b in range(S3 + 20, S3 + 40):
        for k in range(BPB): P.harm[b * BPB + k] = ['Fm', 'Fm', 'Db', 'Db', 'Bbm', 'Bbm', 'C7', 'C7', 'Fm', 'Fm', 'Ab', 'Ab', 'Db', 'Db', 'C7', 'C7'][((b - S3 - 20) % 4) * 4 + k]
    E = [((S3 + 42) * BPB, ch('Ab')), ((S3 + 52) * BPB, ch('Ab', -12))]
    harm_fit(P, S3 + 40, S4, E, C_AB)
    P.section(S4, 'IV. 再現と結尾 (変ロ長調)', '土台の IV (眠り) の上で、旋律を総奏で (Vn I・フルート・ホルン・トランペット、トロンボーンと Vc・Cb の根音、ティンパニ) → 旋律の頭だけが残って、高い開いた 5 度と深い鐘で消える')
    E = [((S4 + 2) * BPB, ch('Bb')), ((S4 + 14) * BPB, ch('Bb')), ((S4 + 28) * BPB, ch('Bb', 0, CH_A)), ((S4 + 38) * BPB, ch('Bb', -12, CH_A))]
    harm_fit(P, S4 + 1, TOTAL - 8, E, C_BB)
    for q in range((TOTAL - 8) * BPB, TOTAL * BPB): P.harm[q] = 'Bb'
    return P

def melody(P, b0, key, parts, label, oct_=0, part=None):
    t = b0 * BPB; first = True
    for d, m in ch(key, oct_, part):
        for v, tr, g in parts: oadd(v, t, d + 0.05, m + tr, g, label if (first and v == parts[0][0]) else None)
        first = False; t += d

def post(P, events, ex):
    add('REC', 0, DUR, 0, 0.5, None, src=os.path.join(WDIR, R139 + '.wav'), off=0.0, fin=0.02, fout=6.0, semis=0, rid=R139 + '.wav', tag='CXXXIX (tablet139) — 土台、そのまま')
    def cold(b0, b1, g, hi, lo, label, step=4):
        for b in range(b0, b1, step):
            oadd('V1', b * BPB, step * BPB + 0.5, hi, g, label if b == b0 else None); oadd('V2', b * BPB + 0.05, step * BPB + 0.5, lo, g * 0.85)
    # I
    add('X', 0, 10, 34, 0.26, '深い鐘 (ひとつ)')
    cold(S1 + 1, S1 + 4, 0.1, 89, 82, '高い開いた 5 度 (pp)', step=3)
    melody(P, S1 + 4, 'Db', [('V1', 0, 0.3)], 'I. Tristesse — Vn I (ショパン Op. 10-3 の旋律、変ニ長調)')
    melody(P, S1 + 14, 'Db', [('V1', 0, 0.32), ('HN', -12, 0.16)], 'Vn I とホルン')
    melody(P, S1 + 26, 'Db', [('V1', 12, 0.3), ('FL', 12, 0.14)], 'Vn I (1 オクターヴ上) とフルート', 0, CH_A)
    chord_pad(P, S1 + 4, S2 - 1, [('V2', 62, 76), ('VA', 55, 67)], 0.12, 'Vn II・Va の和音')
    roots(P, S1 + 4, S2 - 1, [('VC', 12), ('CB', 0)], 0.16, 'Vc・Cb の根音', every=2)
    # II
    melody(P, S2 + 2, 'F', [('FL', 0, 0.2), ('WW', -12, 0.16)], 'II. フルートとオーボエ (ヘ長調)', 12)
    melody(P, S2 + 12, 'F', [('CL', 0, 0.2), ('HN', 0, 0.18)], 'クラリネットとホルン', -12)
    melody(P, S2 + 22, 'F', [('V1', 0, 0.36), ('FL', 12, 0.18), ('HN', -12, 0.24), ('TR', 0, 0.2)], '総奏の第 1 主題 (Vn I・フルート・ホルン・トランペット)')
    melody(P, S2 + 32, 'F', [('V1', 0, 0.34), ('V2', -12, 0.2), ('FL', 12, 0.16), ('TR', 0, 0.18)], None, 0, CH_B)
    chord_pad(P, S2 + 2, S2 + 22, [('V2', 62, 76), ('VA', 55, 67)], 0.1, 'Vn II・Va の和音'); roots(P, S2 + 2, S2 + 22, [('VC', 12), ('CB', 0)], 0.14, None, every=2)
    chord_pad(P, S2 + 22, S3 - 1, [('VA', 55, 67), ('TB', 43, 57)], 0.16, 'Va・トロンボーンの和音'); roots(P, S2 + 22, S3 - 1, [('VC', 12), ('CB', 0)], 0.22, None, every=2)
    for k, b in enumerate(range(S2 + 22, S3 - 2, 4)): oadd('TP', b * BPB, 2.0, 41, 0.3, 'ティンパニ' if k == 0 else None)
    # III
    melody(P, S3 + 2, 'Ab', [('VA', 0, 0.22), ('CL', 0, 0.16)], 'III. 旋律の頭が短調の上で (Va・クラリネット)', -12, CH_A)
    melody(P, S3 + 10, 'Ab', [('VC', 0, 0.22), ('HN', 0, 0.16)], None, -12, CH_A)
    tremolo(P, S3 + 20, S3 + 40, 0.16, '嵐 — 弦のトレモロ (Vn II・Va)')
    first = True
    for b in range(S3 + 20, S3 + 40):
        for k in range(BPB):
            r = 38 + chord(P.harm[b * BPB + k])['root']; oadd('VC', b * BPB + k, 0.9, r + 12, 0.2, '半音の動き (Vc・Cb)' if first else None); oadd('CB', b * BPB + k, 0.9, r, 0.22); first = False
    chord_pad(P, S3 + 22, S3 + 40, [('TB', 43, 57), ('HN', 50, 64)], 0.2, 'トロンボーン・ホルンの和音')
    for k, b in enumerate(range(S3 + 24, S3 + 40, 2)): oadd('TP', b * BPB, 2.0, 41 if k % 2 == 0 else 46, 0.26 + 0.03 * k, 'ティンパニ (高まる)' if k == 0 else None)
    for i in range(8): oadd('TP', (S3 + 39) * BPB + i * 0.5, 0.5, 41, 0.3 + 0.03 * i, None)
    line('V1', S3 + 36, [(0.5, m) for m in (80, 79, 78, 77, 76, 75, 74, 73)] + [(4, 72)], 0, 0.3, 'Vn I — 半音で下る'); line('FL', S3 + 36, [(0.5, m) for m in (92, 91, 90, 89, 88, 87, 86, 85)] + [(4, 84)], 0, 0.16, None)
    melody(P, S3 + 42, 'Ab', [('V1', 0, 0.3), ('CL', -12, 0.14)], '鎮まって — 旋律が変イ長調で (Vn I)')
    melody(P, S3 + 52, 'Ab', [('VA', 0, 0.24), ('HN', 0, 0.16)], None, -12)
    chord_pad(P, S3 + 42, S4 - 1, [('V2', 62, 76), ('VA', 55, 67)], 0.1); roots(P, S3 + 42, S4 - 1, [('VC', 12), ('CB', 0)], 0.14, None, every=2)
    # IV
    melody(P, S4 + 2, 'Bb', [('V1', 0, 0.36), ('FL', 12, 0.18), ('HN', -12, 0.24), ('TR', 0, 0.22)], 'IV. 再現 — 総奏 (変ロ長調)')
    melody(P, S4 + 14, 'Bb', [('V1', 12, 0.34), ('V2', 0, 0.22), ('FL', 12, 0.16), ('HN', -12, 0.22), ('TR', 0, 0.2)], None)
    chord_pad(P, S4 + 2, S4 + 28, [('VA', 55, 67), ('TB', 43, 57)], 0.16, 'Va・トロンボーンの和音'); roots(P, S4 + 2, S4 + 28, [('VC', 12), ('CB', 0)], 0.22, 'Vc・Cb の根音', every=2)
    for k, b in enumerate(range(S4 + 2, S4 + 28, 4)): oadd('TP', b * BPB, 2.0, 46, 0.3, 'ティンパニ' if k == 0 else None)
    melody(P, S4 + 28, 'Bb', [('V1', 0, 0.26), ('CL', -12, 0.12)], '旋律の頭だけが残る', 0, CH_A)
    melody(P, S4 + 38, 'Bb', [('HN', 0, 0.18)], None, -12, CH_A)
    cold(S4 + 30, TOTAL - 4, 0.09, 94, 89, '高い開いた 5 度 (ファ・シ♭, pp)')
    chord_pad(P, S4 + 30, TOTAL - 10, [('VA', 55, 67), ('VC', 43, 55)], 0.07)
    add('X', (TOTAL - 5) * BPB, 16, 34, 0.3, '深い鐘 (最後に)')
    for e in extras:                                                                                # 土台が小さい所 (III の始め、IV の総奏) は被せる管弦楽を少し上げる
        if e['v'] in ('REC', 'X'): continue
        if S3 * BPB <= e['beat'] < (S3 + 20) * BPB: e['gain'] = round(e['gain'] * 1.3, 4)
        elif S4 * BPB <= e['beat'] < (S4 + 28) * BPB: e['gain'] = round(e['gain'] * 1.4, 4)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R139], 'piano_decay': 2.6, 'reverb': [8.0, 3.0, 0.5], 'orchestra': True,
        'title': 'Requiem BADA — CXL · Sinfonia della tristezza',
        'subtitle': 'tablet139 (CXXXIX · Lebewohl) の曲を、ショパンの練習曲 Op. 10-3「別れの曲」(Tristesse) の旋律 (記憶からの採譜) に合わせて、シンフォニーで作り換える: I 弦が歌う (変ニ長調) → II 木管から総奏へ (ヘ長調) → III 中間部の嵐 (ヘ短調) と静かな再現 (変イ長調) → IV 総奏の再現と消えていく結尾 (変ロ長調)。♩=60',
        'legend': ['X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'CL', 'HN', 'TR', 'TB', 'TP'], 'vname': {'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
        'footer': ['主題 = ショパン Op. 10-3 ホ長調「別れの曲」(1832 年、公有) の旋律の頭 (記憶からの採譜、細部は原曲と違いうる): ソ# | シ ラ ソ# ファ# ソ# ファ# ミ レ# ミ ／ ソ# ラ シ ド# レ# ミ レ# ド# シ ラ ソ# ファ# ミ レ# ミ — 各段階の調 (変ニ・ヘ・変イ・変ロ長調) に移して',
                   '土台は tablet139 の音をそのまま。和音は土台の採譜 (拍ごと) を優先しつつ主題の音を含む和音を選ぶ。被せるのは管弦楽だけ (synth の合成)。鐘は始めと終わりに深いもの。声なし。']}

if __name__ == '__main__':
    print('base', DUR, 's bars', TOTAL, '| theme beats', sum(d for d, _ in CH))
    compose.main(OUT, seed=140, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
