#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLIII · Erbarm dich mein — BWV 721 ipnotico (tablet142 の曲に、バッハの BWV 721 を共鳴的洗脳の仕上がりに)
  土台: CXLII · Ballata ipnotica (tablet142 の音をそのまま、表として): 4 つの和音の輪 (B♭m G♭ D♭ A♭ / Dm B♭ F C / Fm D♭ A♭ E♭ / Gm E♭ B♭ F)、♩=60、13 分 35 秒
  被せる: バッハ コラール前奏曲「Erbarm dich mein, o Herre Gott」BWV 721 の書法 — 打ち続ける和音 (8 分音符の繰り返し、脈のように) の上に、コラールの定旋律を長い音で。
          定旋律 = コラール「Erbarm dich mein, o Herre Gott」(Walter 1524; music21 の収録譜 bach/bwv305 のソプラノ、イ短調、52 拍) を 2 倍に伸ばして (104 拍 = 26 小節)、各段階の関係短調に移す (変ロ短調 +1、ニ短調 +5、ヘ短調 +8、ト短調 −2)
    I.  (変ロ短調)  打ち続ける和音が pp で始まり、ホルンが定旋律を遠くで
    II. (ニ短調)    定旋律がクラリネットと Vn I に、トロンボーンの和音が脈に加わる
    III. (ヘ短調)   定旋律がトランペットと Vn I に、脈が強く、ティンパニ → 定旋律が低く (Vc・Cb) 2 度目
    IV. (ト短調)    総奏の定旋律 (Vn I・フルート・トランペット・ホルン) → ホルンだけの定旋律と、脈が消えていく、深い鐘
  音源: 土台は tablet142 の音 (REC)、被せるのは管弦楽だけ (synth の合成)
  使い方: python compose_tablet143.py <bank142.json (tablet142 の採譜; 和音は輪なので長さだけ使う)> <wav のフォルダ> [score_tablet143.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet143.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']
R142 = '20261105_142000'
DUR = RECS[R142]['dur']; TOTAL = int(math.ceil(DUR / 4.0)) + 1
BPM = 60
S1, S2, S3, S4 = 0, 38, 80, 141
LOOP = {1: ['Bbm', 'Gb', 'Db', 'Ab'], 2: ['Dm', 'Bb', 'F', 'C'], 3: ['Fm', 'Db', 'Ab', 'Eb'], 4: ['Gm', 'Eb', 'Bb', 'F']}
TRK = {1: 1, 2: 5, 3: 8, 4: -2}                                                                  # イ短調 → 変ロ短調・ニ短調・ヘ短調・ト短調
CANDS = {1: ['Bbm', 'Gb', 'Db', 'Ab', 'Ebm', 'Fm', 'F', 'Bbm/Db', 'Gb/Bb', 'Cb'],
         2: ['Dm', 'Bb', 'F', 'C', 'Gm', 'Am', 'A', 'Dm/F', 'Bb/D', 'Eb'],
         3: ['Fm', 'Db', 'Ab', 'Eb', 'Bbm', 'Cm', 'C', 'Fm/Ab', 'Db/F', 'Gb'],
         4: ['Gm', 'Eb', 'Bb', 'F', 'Cm', 'Dm', 'D', 'Gm/Bb', 'Eb/G', 'Ab']}
def stage(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
ERB = [(d, m) for d, m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erbarm_melody.json')))['notes']]   # (拍, MIDI)、イ短調
def cantus(st, oct_=0, k=2): return [(d * k, m + TRK[st] + oct_) for d, m in ERB]                 # 2 倍に伸ばした定旋律
CF_BEATS = 2 * sum(d for d, _ in ERB)
PLAYS = [(R142, 0, 0.5, 0)]
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
    for b in range(TOTAL):
        st = stage(b); h = LOOP[st][(b - (S1, S2, S3, S4)[st - 1]) % 4]
        for k in range(BPB): RH.append(h); P.harm[b * BPB + k] = h; RECQ.add(b * BPB + k)
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 脈と定旋律 (変ロ短調, ♩=60)', 'BWV 721 の書法: 打ち続ける和音 (8 分音符、弦) が pp で始まり、ホルンが「Erbarm dich mein」の定旋律 (2 倍に伸ばして) を遠くで — 土台の和音の輪 (B♭m G♭ D♭ A♭) の上で')
    harm_fit(P, S1 + 6, S1 + 6 + 27, [((S1 + 6) * BPB, cantus(1, -12))], CANDS[1])
    P.section(S2, 'II. 定旋律が近づく (ニ短調)', '定旋律がクラリネットと Vn I に、トロンボーンの和音が脈に加わる')
    harm_fit(P, S2 + 2, S2 + 2 + 27, [((S2 + 2) * BPB, cantus(2))], CANDS[2])
    P.section(S3, 'III. 脈が強く (ヘ短調)', '定旋律がトランペットと Vn I に、脈が強く、ティンパニ → 2 度目は定旋律が低く (Vc・Cb)、オーボエが上で')
    harm_fit(P, S3 + 2, S3 + 2 + 27, [((S3 + 2) * BPB, cantus(3))], CANDS[3]); harm_fit(P, S3 + 31, S3 + 31 + 27, [((S3 + 31) * BPB, cantus(3, -24))], CANDS[3])
    P.section(S4, 'IV. 総奏と消える脈 (ト短調)', '総奏の定旋律 (Vn I・フルート・トランペット・ホルン) → ホルンだけの定旋律、脈が少しずつ消えて、深い鐘')
    harm_fit(P, S4 + 2, S4 + 2 + 27, [((S4 + 2) * BPB, cantus(4))], CANDS[4]); harm_fit(P, S4 + 31, min(TOTAL - 4, S4 + 31 + 27), [((S4 + 31) * BPB, cantus(4, -12))], CANDS[4])
    return P

def cf(P, b0, st, parts, label, oct_=0):
    t = b0 * BPB; first = True
    for d, m in cantus(st, oct_):
        for v, tr, g in parts: oadd(v, t, d + 0.1, m + tr, g, label if (first and v == parts[0][0]) else None)
        first = False; t += d
def pulse(P, b0, b1, g, parts, label=None):
    """BWV 721 の打ち続ける和音: 8 分音符ごとに和音 (3 音) を打つ (弱拍は少し弱く)"""
    first = True
    for b in range(b0, b1):
        for k in range(BPB * 2):
            h = P.harm[b * BPB + k // 2]; gg = g * (1.0 if k % 2 == 0 else 0.75) * (1.08 if k == 0 else 1.0)
            for v, lo, hi in parts:
                for i, m in enumerate(tones_of(h, lo, hi)[:3]): oadd(v, b * BPB + k * 0.5 + 0.01 * i, 0.42, m, gg * (1.0 if i == 0 else 0.85), label if (first and i == 0) else None); first = False

def post(P, events, ex):
    add('REC', 0, DUR, 0, 0.5, None, src=os.path.join(WDIR, R142 + '.wav'), off=0.0, fin=0.02, fout=6.0, semis=0, rid=R142 + '.wav', tag='CXLII (tablet142) — 土台、そのまま')
    add('X', 0, 10, 34, 0.24, '深い鐘 (ひとつ)')
    # I
    pulse(P, S1 + 2, S2, 0.08, [('V2', 62, 76), ('VA', 55, 67)], '打ち続ける和音 (BWV 721 の脈、pp)')
    cf(P, S1 + 6, 1, [('HN', 0, 0.2)], 'I. 定旋律「Erbarm dich mein」— ホルン (遠くで)', -12)
    for b in range(S1 + 2, S2, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 34, 0.12, None)
    # II
    pulse(P, S2, S3, 0.12, [('V2', 62, 76), ('VA', 55, 67), ('VC', 48, 60)], '脈が近づく')
    pulse(P, S2 + 8, S3, 0.07, [('TB', 43, 57)], 'トロンボーンの和音の脈')
    cf(P, S2 + 2, 2, [('CL', 0, 0.22), ('V1', 0, 0.22)], 'II. 定旋律 — クラリネットと Vn I')
    # III
    pulse(P, S3, S3 + 30, 0.17, [('V2', 62, 76), ('VA', 55, 67), ('VC', 48, 60), ('TB', 43, 57)], '脈が強く')
    cf(P, S3 + 2, 3, [('TR', 0, 0.24), ('V1', 12, 0.26), ('HN', -12, 0.16)], 'III. 定旋律 — トランペットと Vn I')
    for k, b in enumerate(range(S3 + 4, S3 + 30, 2)): oadd('TP', b * BPB, 1.0, 41, 0.22 + 0.01 * k, 'ティンパニ (脈に)' if k == 0 else None); oadd('TP', b * BPB + 2, 1.0, 41, 0.18)
    pulse(P, S3 + 30, S4, 0.13, [('V2', 62, 76), ('VA', 55, 67)], None)
    cf(P, S3 + 31, 3, [('VC', 0, 0.26), ('CB', -12, 0.22)], '定旋律が低く (Vc・Cb)', -24); cf(P, S3 + 31, 3, [('WW', 0, 0.14)], 'オーボエが上で', 12)
    # IV
    pulse(P, S4, S4 + 30, 0.18, [('V2', 62, 76), ('VA', 55, 67), ('VC', 48, 60), ('TB', 43, 57)], '総奏の脈')
    cf(P, S4 + 2, 4, [('V1', 12, 0.3), ('FL', 24, 0.16), ('TR', 0, 0.24), ('HN', -12, 0.2)], 'IV. 定旋律 — 総奏 (Vn I・フルート・トランペット・ホルン)')
    for k, b in enumerate(range(S4 + 2, S4 + 30, 2)): oadd('TP', b * BPB, 1.0, 43, 0.26, 'ティンパニ' if k == 0 else None); oadd('TP', b * BPB + 2, 1.0, 43, 0.2)
    first = True
    for b in range(S4 + 30, TOTAL - 4):
        g = max(0.02, 0.13 - 0.004 * (b - S4 - 30)); pulse(P, b, b + 1, g, [('V2', 62, 76), ('VA', 55, 67)], '脈が消えていく' if first else None); first = False
    cf(P, S4 + 31, 4, [('HN', 0, 0.18)], 'ホルンだけの定旋律', -12)
    for b in range(S4 + 30, TOTAL - 4, 4): oadd('V1', b * BPB, 4 * BPB + 0.5, 91, 0.07, '高い開いた 5 度 (共鳴)' if b == S4 + 30 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 86, 0.06)
    add('X', (TOTAL - 5) * BPB, 16, 34, 0.3, '深い鐘 (最後に)')

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R142], 'piano_decay': 2.6, 'reverb': [7.0, 3.0, 0.5], 'orchestra': True,
        'title': 'Requiem BADA — CXLIII · Erbarm dich mein — BWV 721 ipnotico',
        'subtitle': 'tablet142 (CXLII · Ballata ipnotica) の曲に、バッハのコラール前奏曲 BWV 721「Erbarm dich mein, o Herre Gott」の書法 (打ち続ける和音の上の定旋律) を被せて、共鳴的洗脳の仕上がりに: 脈 pp とホルンの定旋律 (変ロ短調) → クラリネットと Vn I (ニ短調) → トランペット、ティンパニ、低い定旋律 (ヘ短調) → 総奏 → 消える脈と深い鐘 (ト短調)。♩=60',
        'legend': ['X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'CL', 'HN', 'TR', 'TB', 'TP'], 'vname': {'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
        'footer': ['定旋律 = コラール「Erbarm dich mein, o Herre Gott」(music21 の収録譜 bach/bwv305 のソプラノ、イ短調、52 拍) を 2 倍に伸ばして (26 小節)、各段階の関係短調に。BWV 721 からは書法 (8 分音符で打ち続ける和音) を借りる',
                   '土台は tablet142 の音をそのまま (表)。和音は土台の 4 つの和音の輪を優先しつつ定旋律の音を含む和音を選ぶ。被せるのは管弦楽だけ (synth の合成)。鐘は始めと終わりに深いもの。声なし。']}

if __name__ == '__main__':
    print('base', DUR, 's bars', TOTAL, '| cantus beats', CF_BEATS)
    compose.main(OUT, seed=143, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
