#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLII · Ballata ipnotica (tablet140 の曲に、LUNA SEA の「ray」のバラードの響きを共鳴させて、洗脳的な曲に)
  土台: CXL · Sinfonia della tristezza (tablet140.mp4 の音をそのまま、表として): 変ニ長調 → ヘ長調 → ヘ短調 / 変イ長調 → 変ロ長調、♩=60、13 分 24 秒
  共鳴: 1990 年代の日本のロック・バラード (LUNA SEA の「ray」のバラードのような) の響き — 旋律の引用はなく、様式だけ:
    クリーンなアルペジオ (8 分音符、ディレイのように) が全曲、4 つの和音の輪 (vi → IV → I → V を各段階の調で) が洗脳的に回り、柔らかいロックのドラム (キック・スネア・ハイハット)、シンセ・ベースの根音、
    サビでは歪んだギターのパワーコードと弦の総奏、高い開いた 5 度の共鳴。短い動機 (ソ・ラ・ソ・ミ、各段階の調で) を 2 小節ごとに繰り返す (洗脳)
    I.  序 (変ニ長調)       アルペジオと弦のパッドだけ、動機が遠くで
    II. A メロ (ヘ長調)      ドラムとベースが入る、動機にフルート
    III. サビの嵐 (ヘ短調)   歪んだギター、クラッシュとライド、タムのフィル、動機にトランペット → 鎮まる
    IV. 大サビと溶解 (変ロ長調)  総奏のサビ → アルペジオと高い 5 度だけになって、深い鐘と消える
  使い方: python compose_tablet142.py <bank140.json (tablet140 の採譜)> <wav のフォルダ> [score_tablet142.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet142.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']
R140 = '20261105_140000'
DUR = RECS[R140]['dur']; TOTAL = int(math.ceil(DUR / 4.0)) + 1
BPM = 60
S1, S2, S3, S4 = 0, 38, 80, 141
LOOP = {1: ['Bbm', 'Gb', 'Db', 'Ab'], 2: ['Dm', 'Bb', 'F', 'C'], 3: ['Fm', 'Db', 'Ab', 'Eb'], 4: ['Gm', 'Eb', 'Bb', 'F']}      # 4 つの和音の輪 (vi → IV → I → V)
TONIC = {1: 61, 2: 65, 3: 68, 4: 70}                                                              # 変ニ・ヘ・変イ・変ロ (動機の基準)
def stage(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
def hook(st, minor=False): T = TONIC[st]; return [(1, T + 7), (1, T + (8 if minor else 9)), (1, T + 7), (1, T + (3 if minor else 4))]   # ソ・ラ・ソ・ミ (短調ではソ・ラ♭・ソ・ミ♭)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
OG = 0.34
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)
DRUM_G = 0.33
def dr(beat, kind, g, pan=0.0, label=None): add('DR', beat, 0.25, 60, g * DRUM_G, label, kind=kind, pan=pan)
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def line(v, bar, mat, tr, g, label=None, beat=0, orch=True):
    t = bar * BPB + beat; first = True
    for d, m in mat:
        (oadd if orch else add)(v, t, d, m + tr, g, label if first else None); first = False; t += d

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.9
    for b in range(TOTAL):
        st = stage(b); h = LOOP[st][(b - (S1, S2, S3, S4)[st - 1]) % 4]
        for k in range(BPB): P.harm[b * BPB + k] = h
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 序 — アルペジオと弦 (変ニ長調, ♩=60)', '土台 (CXL の I) の上で、クリーンなアルペジオ (8 分音符) と弦のパッドだけ — 4 つの和音の輪 (B♭m → G♭ → D♭ → A♭) が回り、動機 (ソ・ラ・ソ・ミ) が遠くで 2 小節ごとに')
    P.section(S2, 'II. A メロ — ドラムとベース (ヘ長調)', '柔らかいロックのドラム (キック・スネア・ハイハット) とシンセ・ベースの根音が入る。和音の輪 Dm → B♭ → F → C、動機にフルートとホルン、弦の和音')
    P.section(S3, 'III. サビの嵐 (ヘ短調)', '歪んだギターのパワーコード、クラッシュとライド、タムのフィル、動機 (ソ・ラ♭・ソ・ミ♭) にトランペットと Vn I、弦のトレモロ — 和音の輪 Fm → D♭ → A♭ → E♭ → 鎮まってアルペジオだけに')
    P.section(S4, 'IV. 大サビと溶解 (変ロ長調)', '総奏のサビ (ギター・ドラム・ベース・弦・動機の重ね) → 少しずつ消えて、アルペジオと高い開いた 5 度の共鳴だけが残り、深い鐘と消える')
    return P

def post(P, events, ex):
    add('REC', 0, DUR, 0, 0.5, None, src=os.path.join(WDIR, R140 + '.wav'), off=0.0, fin=0.02, fout=6.0, semis=0, rid=R140 + '.wav', tag='CXL (tablet140) — 土台、そのまま')
    add('X', 0, 10, 34, 0.24, '深い鐘 (ひとつ)')
    # アルペジオ (全曲): 8 分音符で 根・5 度・オクターヴ・3 度・5 度・3 度・オクターヴ・5 度 (ディレイのように少し弱く)
    first = True
    for b in range(1, TOTAL - 4):
        st = stage(b); c = chord(P.harm[b * BPB]); r = 50 + c['root']; pat = [r, r + 7, r + 12, r + c['pcs'][1] - c['root'] + 12, r + 7, r + c['pcs'][1] - c['root'] + 12, r + 12, r + 7]
        env = 0.5 if b < S2 else 0.55 if b < S3 else (0.6 if b < S3 + 50 else 0.5) if b < S4 else (0.6 if b < S4 + 34 else max(0.25, 0.5 - 0.012 * (b - S4 - 34)))
        for k, m in enumerate(pat): add('AR', b * BPB + k * 0.5, 0.45, m, env * (1.0 if k % 2 == 0 else 0.8), 'クリーンなアルペジオ (8 分音符、全曲)' if first else None, pan=(-0.3 if k % 2 == 0 else 0.3)); first = False
    # 動機 (ソ・ラ・ソ・ミ) — 2 小節ごと、洗脳的に
    first = True
    for b in range(S1 + 8, TOTAL - 8, 2):
        st = stage(b); minor = (S3 <= b < S3 + 50); H = hook(st, minor)
        if b < S2: line('V1', b, H, 0, 0.14, '動機 (ソ・ラ・ソ・ミ) — 2 小節ごとに繰り返す' if first else None); first = False
        elif b < S3: line('FL', b, H, 12, 0.14, '動機にフルートとホルン' if b == S2 else None); line('HN', b, H, -12, 0.14); line('V1', b, H, 0, 0.12)
        elif b < S3 + 50: line('TR', b, H, 0, 0.22, '動機にトランペットと Vn I (短調)' if b == S3 else None); line('V1', b, H, 12, 0.24); line('HN', b, H, -12, 0.16)
        elif b < S4: line('V1', b, H, 0, 0.14, '鎮まって' if b == S3 + 50 else None)
        elif b < S4 + 34: line('TR', b, H, 0, 0.22, '大サビ — 動機の重ね' if b == S4 else None); line('V1', b, H, 12, 0.26); line('FL', b, H, 24, 0.14); line('HN', b, H, -12, 0.18); line('V2', b, H, 0, 0.18)
        else: line('V1', b, H, 0, max(0.05, 0.14 - 0.004 * (b - S4 - 34)), '溶解' if b == S4 + 34 else None)
    # 弦のパッド (I・II・鎮まり・溶解) とトレモロ (サビ)
    def pad(b0, b1, g, label=None):
        q = b0 * BPB; first = True
        while q < b1 * BPB:
            h = P.harm[q]; q1 = q
            while q1 < b1 * BPB and P.harm[q1] == h: q1 += 1
            for v, lo, hi in (('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)):
                for i, m in enumerate(tones_of(h, lo, hi)[:3]): oadd(v, q + 0.03 * i, (q1 - q) + 0.3, m, g * (1.0 if i == 0 else 0.8), label if (first and i == 0) else None); first = False
            q = q1
    def trem(b0, b1, g, label=None):
        first = True
        for b in range(b0, b1):
            for k in range(BPB * 2):
                t = tones_of(P.harm[b * BPB], 62, 76); oadd('V2', b * BPB + k * 0.5, 0.45, t[-1], g * (1.0 if k % 2 == 0 else 0.8), label if first else None); oadd('VA', b * BPB + k * 0.5, 0.45, t[0], g * 0.9); first = False
    pad(S1 + 2, S2, 0.1, '弦のパッド'); pad(S2, S3, 0.12); pad(S3 + 50, S4, 0.1); pad(S4, S4 + 34, 0.14); pad(S4 + 34, TOTAL - 6, 0.08)
    trem(S3 + 8, S3 + 50, 0.14, '弦のトレモロ (サビ)'); trem(S4 + 8, S4 + 34, 0.14)
    # 高い開いた 5 度の共鳴 (I と溶解)
    for b in list(range(S1 + 4, S2 - 2, 4)) + list(range(S4 + 34, TOTAL - 4, 4)):
        st = stage(b); T = TONIC[st]; oadd('V1', b * BPB, 4 * BPB + 0.5, T + 24, 0.08, '高い開いた 5 度 (共鳴)' if b == S1 + 4 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, T + 31, 0.07)
    # ドラム・ベース (II から)
    first = True
    for b in range(S2, TOTAL - 8):
        calm = (S3 + 50 <= b < S4) or b >= S4 + 34
        loud = (S3 + 8 <= b < S3 + 50) or (S4 <= b < S4 + 34)
        if calm and b >= S4 + 40: continue
        g = 0.5 if calm else 0.75 if loud else 0.6
        c = chord(P.harm[b * BPB]); r = 38 + c['root']
        if r > 45: r -= 12
        add('SB', b * BPB, 1.9, r, 0.45 if not loud else 0.55, 'シンセ・ベース (根音)' if first else None); add('SB', b * BPB + 2, 1.4, r, 0.4); add('SB', b * BPB + 3.5, 0.45, r + 7, 0.3)
        dr(b * BPB, 'kick', g, 0, 'ロックのドラム (柔らかく)' if first else None); dr(b * BPB + 2, 'kick', g * 0.9); dr(b * BPB + 2.5, 'kick', g * 0.6) if loud else None
        dr(b * BPB + 1, 'snare', g * 0.8, 0.05); dr(b * BPB + 3, 'snare', g * 0.8, 0.05)
        for k in range(8): dr(b * BPB + k * 0.5, 'ride' if loud else 'hatc', (0.5 if loud else 0.4) * (1.0 if k % 2 == 0 else 0.7), 0.3)
        if loud and (b - S3) % 4 == 0: dr(b * BPB, 'crash', 0.6, -0.2, 'クラッシュ' if b == S3 + 8 else None)
        if loud and (b - S3) % 8 == 7:
            for k, (tm, mm) in enumerate(((3.0, 55), (3.25, 52), (3.5, 50), (3.75, 47))): add('DR', b * BPB + tm, 0.25, mm, 0.6 * DRUM_G, 'タムのフィル' if b == S3 + 15 else None, kind='tom', pan=-0.3 + 0.2 * k)
        first = False
    # 歪んだギターのパワーコード (サビ)
    first = True
    for b in list(range(S3 + 8, S3 + 50)) + list(range(S4, S4 + 34)):
        c = chord(P.harm[b * BPB]); r = 38 + c['root']
        if r > 45: r -= 12
        add('GT', b * BPB, 3.8, r, 0.3, '歪んだギターのパワーコード (サビ)' if first else None, mute=False, pan=-0.5); add('GT', b * BPB + 0.02, 3.8, r + 12, 0.18, None, mute=False, pan=0.5); first = False
    # 終わり
    add('X', (TOTAL - 5) * BPB, 16, 34, 0.3, '深い鐘 (最後に)')

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R140], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4], 'band_gain': 1.0, 'orchestra': True,
        'title': 'Requiem BADA — CXLII · Ballata ipnotica',
        'subtitle': 'tablet140 (CXL · Sinfonia della tristezza) の曲に、LUNA SEA の「ray」のバラードのような響き (クリーンなアルペジオ、柔らかいロックのドラム、シンセ・ベース、サビの歪んだギターと弦) を共鳴させ、4 つの和音の輪と短い動機 (ソ・ラ・ソ・ミ) の繰り返しで洗脳的に: 序 → A メロ → サビの嵐 → 大サビと溶解。♩=60',
        'legend': ['X', 'AR', 'SB', 'DR', 'GT', 'V1', 'V2', 'VA', 'VC', 'FL', 'HN', 'TR'], 'vname': {'X': '鐘', 'AR': 'アルペジオ', 'SB': 'ベース', 'DR': 'ドラム', 'GT': 'ギター', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'FL': 'Fl', 'HN': 'Hn', 'TR': 'Tp'},
        'footer': ['共鳴 = 1990 年代の日本のロック・バラードの様式 (アルペジオ・ドラム・ベース・パワーコード・弦) だけで、旋律の引用はなし。和音の輪 vi → IV → I → V を各段階の調で (B♭m G♭ D♭ A♭ / Dm B♭ F C / Fm D♭ A♭ E♭ / Gm E♭ B♭ F)',
                   '土台は tablet140 の音をそのまま (表)。動機 ソ・ラ・ソ・ミ (短調ではソ・ラ♭・ソ・ミ♭) を 2 小節ごとに。鐘は始めと終わりに深いもの。声なし。']}

if __name__ == '__main__':
    print('base', DUR, 's bars', TOTAL)
    compose.main(OUT, seed=142, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
