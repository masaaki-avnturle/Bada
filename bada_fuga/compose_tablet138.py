#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXVIII · Kimigayo nel palazzetto (10/13 の 2 曲を雰囲気に、ニ長調の君が代を — 剣道の県大会の試合会場で全員が聞く、冷たい空気の会場に静かに流れる曲に)
  旋律: 君が代 (林廣守、公有; この曲集の XXIX の採譜、主音レ・44 拍 = 11 小節)。ニ長調の和音 (レ・ソ・ラ・シ短・ミ短、ド♮の所は ♭VII の C と Am) で、静かに
  舞台: 冷たい空気の総合体育館 — 10/13 06:41・06:42 の実音 (半音上げてロ短調に) が序奏・間奏・結尾に、高い開いた 5 度の弦が pp、コントラバスの保続、低いクラリネット、遠い深い鐘。
        国歌は館内放送のように遠く静かに (弦とクラリネット → 2 度目はフルートとホルンが加わる)、最後は国歌の終わりのようにユニゾンのレ
  音源: 管弦楽だけ (synth の合成)。声なし
  使い方: python compose_tablet138.py <bank1013.json> <wav のフォルダ> [score_tablet138.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet138.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']
R41, R42 = '20261013_064129', '20261013_064238'
# 君が代 (XXIX の採譜): 一音一拍、句の終わりを伸ばす。主音レ
KIMI = [[(1, 62), (1, 62), (1, 60), (1, 62), (1, 64), (1, 67), (1, 64), (1, 62)],                 # 君が代は
        [(1, 64), (1, 67), (1, 69), (1, 67), (1, 64), (1, 67), (2, 69)],                          # 千代に八千代に
        [(1, 69), (1, 67), (1, 69), (1, 67), (1, 64), (3, 62)],                                   # さざれ石の
        [(1, 60), (1, 62), (1, 64), (1, 67), (1, 64), (3, 62)],                                   # 巌となりて
        [(1, 64), (1, 67), (1, 69), (1, 67), (1, 64), (3, 62)],                                   # 苔のむすまで
        [(4, 62)]]                                                                               # (ユニゾン)
KIMI_ALL = [x for ph in KIMI for x in ph]; KIMI_BEATS = sum(d for d, _ in KIMI_ALL)
KNAMES = ['君が代は', '千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで']
CANDS_DK = ['D', 'G', 'A', 'Bm', 'Em', 'G/D', 'D/A', 'C', 'Am', 'G/B', 'Bm/D', 'D/F#']   # ニ長調 (ド♮には C・Am)
CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4']
INTRO, KIMI1, INTER, KIMI2, UNIS, CODA, TOTAL = 0, 20, 32, 50, 64, 72, 88
BPM = 52
def tempo_of(bar): return float(BPM)
def key_of(bar): return 'D' if (KIMI1 <= bar < INTER or KIMI2 <= bar < CODA) else 'Bm'
PLAYS = [(R41, 1, 0.42, 1), (R42, INTER + 1, 0.38, 1), (R41, CODA + 1, 0.38, 1)]
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

def kimi_entries(b0, tr=0): return [(b0 * BPB, [(d, m + tr) for d, m in KIMI_ALL])]

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.9
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: cur = key_of(q // BPB)
        RH.append(cur); P.harm[q] = cur
    for v in VOICES: P.rest_bars(v, 0, TOTAL)                                                       # 管弦楽だけ
    P.section(INTRO, 'Introduzione — 冷たい空気の会場 (ロ短調, ♩=52)', '10/13 06:41 の実音 (半音上げて)。高い開いた 5 度 (シ・ファ#) の弦が pp、コントラバスの保続、低いクラリネット — ホルンが「君が代は」を遠くで、深い鐘がひとつ')
    harm_fit(P, INTRO + 8, INTRO + 12, [((INTRO + 8) * BPB, [(d, m - 12) for d, m in KIMI[0]])], CANDS_BM)
    P.section(KIMI1, 'Kimigayo I — 館内放送のように静かに (ニ長調)', '君が代をニ長調の和音で: Vn I が旋律 (pp)、クラリネットが 1 オクターヴ下、Vn II・Va の和音、Vc・Cb の根音 — 全員が立って聞く')
    harm_fit(P, KIMI1 + 1, KIMI1 + 12, kimi_entries(KIMI1 + 1), CANDS_DK)
    for q in range((KIMI1 + 12) * BPB, INTER * BPB): P.harm[q] = 'D'
    P.section(INTER, 'Interludio — 間 (ロ短調)', '06:42 の実音。「千代に八千代に」「さざれ石の」の句がホルン → オーボエ → クラリネット → Vc と静かに追いかける (フーガの気配)、高い開いた 5 度')
    E = [((INTER + 3) * BPB, [(d, m - 12) for d, m in KIMI[1]]), ((INTER + 6) * BPB, [(d, m) for d, m in KIMI[2]]), ((INTER + 9) * BPB, [(d, m - 12) for d, m in KIMI[1]]), ((INTER + 12) * BPB, [(d, m - 24) for d, m in KIMI[2]])]
    harm_fit(P, INTER + 2, KIMI2 - 2, E, CANDS_BM)
    for q in range((KIMI2 - 2) * BPB, KIMI2 * BPB): P.harm[q] = 'A' if q >= (KIMI2 - 1) * BPB else 'Bm'
    P.section(KIMI2, 'Kimigayo II — 2 度目 (ニ長調)', 'フルート (1 オクターヴ上) とホルンが加わる、トロンボーンの根音、「巌となりて」にティンパニの小さなロール — それでも静かに')
    harm_fit(P, KIMI2 + 1, KIMI2 + 12, kimi_entries(KIMI2 + 1), CANDS_DK)
    for q in range((KIMI2 + 12) * BPB, UNIS * BPB): P.harm[q] = 'D'
    P.section(UNIS, 'ユニゾンのレ — 国歌の終わりのように (ニ長調)', '「君が代は」を弦のオクターヴのユニゾンで pp、最後はレだけ (国歌の終わりの斉唱のように)')
    for q in range(UNIS * BPB, CODA * BPB): P.harm[q] = 'D'
    P.section(CODA, 'Coda — 冷たい空気に戻る (ロ短調)', '06:41 の実音、高い開いた 5 度、ホルンの「君が代は」、コントラバスの保続 — 深い鐘')
    return P

def kimigayo(P, b0, parts, pad_g, root_g, label, fl=False, hn=False, tb=False, tp=False):
    t = b0 * BPB; first = True
    for ph_i, ph in enumerate(KIMI):
        for d, m in ph:
            for v, tr, g in parts: oadd(v, t, d + 0.1, m + tr, g, (label + ' — ' + KNAMES[0]) if (first and v == parts[0][0]) else (KNAMES[ph_i] if (v == parts[0][0] and d == ph[0][0] and (t - b0 * BPB) == sum(dd for p in KIMI[:ph_i] for dd, _ in p) and ph_i < 5 and ph_i > 0) else None))
            if fl: oadd('FL', t, d + 0.1, m + 12, 0.12, 'フルート (1 オクターヴ上)' if first else None)
            if hn: oadd('HN', t, d + 0.1, m - 12, 0.16, 'ホルン' if first else None)
            first = False; t += d
    chord_pad(P, b0, b0 + 11, [('V2', 62, 76), ('VA', 55, 67)], pad_g, 'Vn II・Va の和音')
    roots(P, b0, b0 + 11, [('VC', 12), ('CB', 0)] + ([('TB', 12)] if tb else []), root_g, 'Vc・Cb の根音' + ('・トロンボーン' if tb else ''), every=2)
    if tp:
        t3 = b0 * BPB + sum(dd for p in KIMI[:3] for dd, _ in p)
        for i in range(8): oadd('TP', t3 + i * 0.5, 0.5, 38, 0.12 + 0.02 * i, 'ティンパニ (小さなロール)' if i == 0 else None)

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 1 else 0.02, fout=5.0, semis=sm, rid=rid + '.wav', tag='10/13 %s — 実音 (半音上げてロ短調に)' % ('06:41' if rid == R41 else '06:42'))
    def cold(b0, b1, g, label):
        for b in range(b0, b1, 4):
            oadd('V1', b * BPB, 4 * BPB + 0.5, 90, g, label if b == b0 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, g * 0.85); oadd('VA', b * BPB + 0.1, 4 * BPB + 0.5, 71, g * 0.7)
            oadd('CB', b * BPB, 4 * BPB + 0.5, 35, g * 1.6, 'コントラバスの保続 (シ)' if b == b0 else None)
    # 序奏
    cold(INTRO + 1, KIMI1 - 3, 0.13, '高い開いた 5 度 (Vn・Va, pp)')
    for b in range(INTRO + 3, KIMI1 - 3, 4): oadd('CL', b * BPB, 4 * BPB + 0.3, 47, 0.14, '低いクラリネット' if b == INTRO + 3 else None)
    line('HN', INTRO + 8, KIMI[0], -12, 0.18, 'ホルン — 君が代は (遠くで)'); line('HN', INTRO + 13, KIMI[0], -24, 0.14, None)
    # 君が代 I
    kimigayo(P, KIMI1 + 1, [('V1', 0, 0.24), ('CL', -12, 0.16)], 0.1, 0.16, 'Kimigayo I — Vn I (pp)')
    # 間奏
    cold(INTER + 1, KIMI2 - 3, 0.11, '高い開いた 5 度 (pp)')
    for k, (v, tr, ph) in enumerate((('HN', -12, 1), ('WW', 0, 2), ('CL', -12, 1), ('VC', -24, 2))): line(v, INTER + 3 + 3 * k, KIMI[ph], tr, 0.18 if v != 'VC' else 0.2, ('%s (ホルン → オーボエ → クラリネット → Vc)' % KNAMES[ph]) if k == 0 else None)
    chord_pad(P, INTER + 2, KIMI2 - 2, [('VA', 50, 64)], 0.08)
    oadd('V1', (KIMI2 - 2) * BPB, 2 * BPB, 81, 0.12, 'ラ → ニ長調へ'); oadd('CB', (KIMI2 - 2) * BPB, 2 * BPB, 33, 0.18)
    # 君が代 II
    kimigayo(P, KIMI2 + 1, [('V1', 0, 0.28), ('CL', -12, 0.16)], 0.14, 0.2, 'Kimigayo II — Vn I・フルート・ホルン', fl=True, hn=True, tb=True, tp=True)
    # ユニゾン
    for v, tr in (('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24), ('CB', -36)): line(v, UNIS + 1, KIMI[0], tr, 0.2 if v in ('V1', 'V2') else 0.18, '「君が代は」— 弦のユニゾン (pp)' if v == 'V1' else None)
    for i, (v, m) in enumerate((('CB', 26), ('VC', 38), ('VA', 50), ('V2', 62), ('V1', 74), ('FL', 86), ('HN', 50), ('CL', 38))): oadd(v, (UNIS + 3) * BPB + 0.03 * i, 4 * BPB, m, 0.18 if v not in ('FL', 'HN', 'CL') else 0.1, 'ユニゾンのレ (国歌の終わり)' if i == 0 else None)
    # 結尾
    cold(CODA + 1, TOTAL - 3, 0.11, '高い開いた 5 度 (pp)')
    line('HN', CODA + 5, KIMI[0], -12, 0.16, 'ホルン — 君が代は (最後に)'); line('HN', CODA + 10, KIMI[0][:4] + [(6, 50)], -24, 0.12, None)
    for b in range(CODA + 3, TOTAL - 3, 4): oadd('CL', b * BPB, 4 * BPB + 0.3, 47, 0.12, None)
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 3) * BPB, 14, 35, 0.4, None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R41, R42], 'piano_decay': 2.6, 'reverb': [10.0, 4.0, 0.55], 'orchestra': True,
        'title': 'Requiem BADA — CXXXVIII · Kimigayo nel palazzetto',
        'subtitle': '10/13 の 2 曲を雰囲気に、ニ長調の君が代を — 剣道の県大会の試合会場で全員が聞く、冷たい空気の会場に静かに流れる曲に: Introduzione (06:41、高い 5 度、ホルンの「君が代は」) → Kimigayo I (館内放送のように静かに) → Interludio (06:42、句の追いかけ) → Kimigayo II (フルートとホルンが加わる) → ユニゾンのレ → Coda (06:41、深い鐘)。管弦楽だけ、♩=52',
        'legend': ['X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'CL', 'HN', 'TB', 'TP'], 'vname': {'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TB': 'Tb', 'TP': 'Timp'},
        'footer': ['旋律 = 君が代 (林廣守、公有; XXIX の採譜、主音レ、11 小節)。和音は旋律の音を含むニ長調の和音を半小節ごとに (ド♮の所は C・Am)、録音が鳴っている拍はその和音を優先',
                   '管弦楽は synth の合成 (クラリネットが低く寄り添う)。10/13 の実音は序奏・間奏・結尾に。鐘は始めと終わりに深いものがひとつ。声なし。']}

if __name__ == '__main__':
    print('kimigayo beats', KIMI_BEATS)
    compose.main(OUT, seed=138, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
