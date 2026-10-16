#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXVII · Missa in si minore sull'inno americano (10/13 の 2 曲を雰囲気に、バッハのミサ曲の形に、モーツァルトのレクイエムを舞台にして、アメリカ国歌を主題に)
  形はバッハのロ短調ミサ (Kyrie I のフーガ → Christe の二重唱 → Kyrie II の古様式 → Gloria → Crucifixus の固執低音 → Et resurrexit → Sanctus → Benedictus → Agnus Dei → Dona nobis pacem)、
  舞台 (音の情景) はモーツァルトのレクイエム (Introitus の歩く低音と低いクラリネット (バセットホルンの代わり)、トロンボーン、ため息の弦、Dies irae のトレモロ、Agnus Dei の独唱)、
  主題はアメリカ国歌 The Star-Spangled Banner (1773 年の旋律、パブリックドメイン、ニ長調 — 頭をロ短調に移してフーガの主題に)。バッハ・モーツァルトの旋律の引用はなく、様式だけ
  音源: 管弦楽だけ (synth の合成: 弦・フルート・オーボエ・クラリネット・ホルン・トランペット・トロンボーン・ティンパニ)。10/13 06:41・06:42 の実音 (半音上げてロ短調に) が Kyrie I・Christe・Agnus Dei・Dona nobis pacem に小さく
  使い方: python compose_tablet137.py <bank1013.json> <wav のフォルダ> [score_tablet137.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet137.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']
R41, R42 = '20261013_064129', '20261013_064238'
SSB = [(d, m) for d, m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssb_melody.json')))['notes']]
SSB_BEATS = sum(d for d, _ in SSB); SSB_BARS = int(math.ceil(SSB_BEATS / 4.0))
P1, P2, P5, P7 = SSB[:12], SSB[12:21], SSB[39:54], SSB[63:75]                                         # 句: O say can you see / what so proudly / rockets' red glare / O say does that star-spangled banner
HEAD = [(0.75, 69), (0.25, 66), (1, 62), (1, 66), (1, 69), (2, 74)]                                   # 頭 (ニ長調)
HEAD_BM = [(0.75, 66), (0.25, 62), (1, 59), (1, 62), (1, 66), (2, 71)]                                # 頭をロ短調に (ファ#・レ・シ・レ・ファ#・シ)
CS = [(1, 74), (1, 73), (1, 71), (0.5, 69), (0.5, 71), (1, 67), (1, 66)]                              # 対主題 (ロ短調、下行)
CANDS_D = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m', 'D/F#', 'G/B', 'A/C#', 'Em7', 'Asus4', 'Bm/D', 'D/A', 'G/D']
CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'F#', 'F#7', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4', 'C#m7b5']
GROUND = ['Bm', 'F#/A#', 'D/A', 'Em/G', 'G', 'F#7', 'F#7', 'Bm']                                     # Crucifixus の固執低音 (半音で下る: シ・ラ#・ラ・ソ#・ソ・ファ#・ファ#・シ) の和音、1 拍ずつ (2 小節)
GROUND_M = [47, 46, 45, 44, 43, 42, 42, 47]
KYRIE1, CHRISTE, KYRIE2, GLORIA, TERRA, CRUC, RESURR, SANCTUS, HOSANNA, BENED, AGNUS, DONA, TOTAL = 0, 40, 64, 88, 108, 124, 152, 172, 184, 196, 216, 244, 280
def tempo_of(bar): return 72.0 if (CHRISTE <= bar < KYRIE2 or GLORIA <= bar < CRUC or RESURR <= bar < SANCTUS or HOSANNA <= bar < BENED or DONA <= bar < TOTAL - 4) else 56.0
def key_of(bar): return 'D' if (CHRISTE <= bar < KYRIE2 or GLORIA <= bar < TERRA or RESURR <= bar < AGNUS or bar >= DONA) else 'Bm'
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(R41, 1, 0.42, 1), (R42, CHRISTE + 1, 0.36, 1), (R41, AGNUS + 1, 0.4, 1), (R42, DONA + 1, 0.3, 1)]
extras = []; RH = []
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
            rc = set(chord(RH[a])['pcs'])
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + 1.5 * len(cc & rc) / max(1, len(cc)) + (1.2 if c == RH[a] else 0)
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
def orchestrate(P, b0, tutti, label='The Star-Spangled Banner'):
    """国歌の旋律を管弦楽で (CXXVIII と同じ作り)"""
    t = b0 * BPB; first = True; ph_end = {11, 20, 29, 38, 53, 62, 74}
    for i, (d, m) in enumerate(SSB):
        g = 0.42 if tutti else 0.32
        oadd('V1', t, d, m, g, ('Vn I — ' + label) if first else None); oadd('V1', t, d, m, g * 0.6, None)
        if tutti:
            oadd('TR', t, d, m, 0.34, 'トランペット' if first else None); oadd('FL', t, d, m + 12, 0.2, 'フルート (1 オクターヴ上)' if first else None); oadd('V2', t, d, m - 12 if m >= 74 else m, 0.22, None)
        c = chord(P.harm[min(int(t), TOTAL * BPB - 1)])
        below = max((x for x in range(m - 12, m - 2) if x % 12 in c['pcs']), default=m - 5)
        oadd('V2' if not tutti else 'HN', t, d, below, 0.22 if not tutti else 0.26, ('Vn II' if not tutti else 'ホルン') if first else None)
        va = max((x for x in range(52, 66) if x % 12 in c['pcs']), default=57); oadd('VA', t, d, va, 0.2, 'Va' if first else None)
        if tutti: oadd('HN', t, d, va + 7 if (va + 7) % 12 in c['pcs'] else va + 5, 0.2, None)
        if i % 2 == 0 or d >= 2:
            root = 38 + c['root']; oadd('VC', t, max(d, 1.0), root + 12, 0.22, 'Vc' if first else None); oadd('CB', t, max(d, 1.0), root, 0.26, 'Cb' if first else None)
            if tutti: oadd('TB', t, max(d, 1.0), root + 12, 0.24, 'トロンボーン' if first else None)
        if tutti and i in ph_end: oadd('TP', t, 2.0, 38 if c['root'] == 2 else 45, 0.5, 'ティンパニ' if i == 11 else None)
        first = False; t += d
    if tutti: oadd('TP', t, 3.0, 38, 0.6, None); oadd('TP', t + 0.5, 2.5, 45, 0.45, None)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = tempo_of(k); P.dyn[k] = 0.9
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * tempo_of(bar) / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / tempo_of(bar) * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = key_of(q // BPB)
        RH.append(cur); P.harm[q] = cur
    for v in VOICES: P.rest_bars(v, 0, TOTAL)                                                       # 4 声 (ピアノ) は使わない — 管弦楽だけ
    # Kyrie I (フーガ、Introitus の舞台)
    P.section(KYRIE1, 'Kyrie I — フーガ (ロ短調, ♩=56)', 'モーツァルトの Introitus の舞台: 10/13 06:41 の実音、歩く低音 (Cb・Vc)、低いクラリネット、トロンボーン。国歌の頭をロ短調にした主題のフーガ (Vn II → Vn I → Va → Vc、対主題は下行)、ストレッタ、高い開いた 5 度')
    E = []
    for k, (v, tr) in enumerate((('V2', 0), ('V1', 12), ('VA', -12), ('VC', -24))): E.append(((KYRIE1 + 6 + 3 * k) * BPB, [(d, m + tr + (7 if k % 2 else 0)) for d, m in HEAD_BM]))
    for k, (v, tr) in enumerate((('V1', 12), ('VA', -12), ('V2', 0), ('VC', -24))): E.append(((KYRIE1 + 22 + 2 * k) * BPB, [(d, m + tr) for d, m in HEAD_BM]))
    for k in range(4): E.append(((KYRIE1 + 30 + k) * BPB, [(d, m + (12 if k % 2 else 0)) for d, m in HEAD_BM]))
    harm_fit(P, KYRIE1 + 6, KYRIE1 + 38, E, CANDS_BM)
    for q in range((KYRIE1 + 38) * BPB, CHRISTE * BPB): P.harm[q] = 'Bm'
    # Christe (二重唱)
    P.section(CHRISTE, 'Christe — 二重唱 (ニ長調, ♩=72)', 'バッハの Christe のように 2 つの声 (フルートとオーボエ、のちに Vn I・Vn II) がカノンで: 国歌の第 2 句 (what so proudly we hailed) を 1 小節遅れで追う。06:42 の実音、Vc・Cb の根音')
    E = [((CHRISTE + 2) * BPB, P2), ((CHRISTE + 3) * BPB, [(d, m - 5) for d, m in P2]), ((CHRISTE + 12) * BPB, [(d, m + 12) for d, m in P2]), ((CHRISTE + 13) * BPB, [(d, m + 7) for d, m in P2])]
    harm_fit(P, CHRISTE + 1, KYRIE2 - 2, E, CANDS_D)
    for q in range((KYRIE2 - 2) * BPB, KYRIE2 * BPB): P.harm[q] = 'A7' if q < (KYRIE2 - 1) * BPB else 'D'
    # Kyrie II (古様式)
    P.section(KYRIE2, 'Kyrie II — 古様式 (ロ短調, ♩=56)', 'バッハの Kyrie II のような stile antico: 主題の拡大 (×2) が Vc・トロンボーン → Va・ホルン → Vn II → Vn I と長い音で重なる、クラリネットが重ね、開いた 5 度で閉じる')
    E = []
    for k, tr in enumerate((-24, -12, 0, 12)): E.append(((KYRIE2 + 1 + 4 * k) * BPB, [(d, m + tr + (7 if k % 2 else 0)) for d, m in augment(HEAD_BM)]))
    harm_fit(P, KYRIE2 + 1, GLORIA - 3, E, CANDS_BM)
    for q in range((GLORIA - 3) * BPB, GLORIA * BPB): P.harm[q] = 'Bsus4' if q < (GLORIA - 1) * BPB else 'Bm'
    # Gloria
    P.section(GLORIA, 'Gloria — トランペットとティンパニ (ニ長調, ♩=72)', 'トランペットとティンパニの頭 (ニ長調)、「rockets\' red glare」の句のフガート (Vn I → Vn II → Va → Vc)、弦のトレモロ → Et in terra pax (静かに: クラリネット、低い弦、ロ短調)')
    E = [((GLORIA + 1) * BPB, HEAD), ((GLORIA + 3) * BPB, [(d, m + 12) for d, m in HEAD])]
    for k, tr in enumerate((12, 0, -12, -24)): E.append(((GLORIA + 6 + 3 * k) * BPB, [(d, m + tr) for d, m in P5[:8]]))
    harm_fit(P, GLORIA, TERRA, E, CANDS_D)
    P.section(TERRA, 'Et in terra pax — 静かに (ロ短調)', 'クラリネットが国歌の頭をロ短調で、低い弦、ティンパニの小さな拍、トロンボーンの和音')
    E = [((TERRA + 2) * BPB, HEAD_BM), ((TERRA + 7) * BPB, [(d, m - 12) for d, m in HEAD_BM]), ((TERRA + 12) * BPB, invert(HEAD_BM))]
    harm_fit(P, TERRA, CRUC, E, CANDS_BM)
    # Crucifixus (固執低音)
    P.section(CRUC, 'Crucifixus — 固執低音 (ロ短調, ♩=56)', 'バッハの Crucifixus のように半音で下る固執低音 (シ・ラ#・ラ・ソ#・ソ・ファ#、2 小節) を 14 回、その上に国歌の最後の句 (O say does that star-spangled banner) の拡大 (×2) がオーボエ・ホルン・Vn I に、弦のため息 (2 音のスラー)、トロンボーン')
    for b in range(CRUC, RESURR):
        for k in range(BPB): P.harm[b * BPB + k] = GROUND[((b - CRUC) % 2) * 4 + k]
    # Et resurrexit
    P.section(RESURR, 'Et resurrexit — 総奏 (ニ長調, ♩=72)', '国歌の第 1・2 句を総奏で (トランペット・Vn I・フルート・ホルン・トロンボーン・ティンパニ)、Vn II・Va の 8 分音符')
    E = [((RESURR + 1) * BPB, P1 + P2), ((RESURR + 10) * BPB, P1 + P2)]
    harm_fit(P, RESURR, SANCTUS, E, CANDS_D)
    # Sanctus / Hosanna
    P.section(SANCTUS, 'Sanctus — 荘厳に (ニ長調, ♩=56)', 'モーツァルトの Sanctus のようなニ長調の荘厳: 弦のトレモロ、トランペットとティンパニの頭、トロンボーンの和音')
    E = [((SANCTUS + 1) * BPB, augment(HEAD)), ((SANCTUS + 6) * BPB, augment(HEAD))]
    harm_fit(P, SANCTUS, HOSANNA, E, CANDS_D)
    P.section(HOSANNA, 'Hosanna — フガート (ニ長調, ♩=72)', '頭 (ニ長調) のフガート: Vn I → Vn II → Va → Vc、フルート、トランペット')
    E = []
    for k, tr in enumerate((12, 0, -12, -24)): E.append(((HOSANNA + 1 + 2 * k) * BPB, [(d, m + tr + (7 if k % 2 else 0)) for d, m in HEAD]))
    E.append(((HOSANNA + 9) * BPB, [(d, m + 12) for d, m in HEAD]))
    harm_fit(P, HOSANNA, BENED, E, CANDS_D)
    # Benedictus
    P.section(BENED, 'Benedictus — 四重奏 (ニ長調, ♩=56)', 'フルート・オーボエ・クラリネット・ホルンの四重奏が国歌の第 2 句を模倣で、弦は短い音の根音 (ピツィカートのように)')
    E = []
    for k, (tr) in enumerate((12, 0, -12, -5)): E.append(((BENED + 1 + 3 * k) * BPB, [(d, m + tr) for d, m in P2]))
    E.append(((BENED + 14) * BPB, [(d, m) for d, m in P2])); harm_fit(P, BENED, AGNUS, E, CANDS_D)
    # Agnus Dei
    P.section(AGNUS, 'Agnus Dei — 独唱 (ロ短調, ♩=56)', 'モーツァルトの Agnus Dei の舞台: クラリネット (バセットホルンの代わり) の独唱が国歌の最後の句をロ短調の上で、弦のため息、歩く低音、トロンボーン、06:41 の実音、深い鐘')
    E = [((AGNUS + 2) * BPB, [(d, m - 12) for d, m in P7]), ((AGNUS + 10) * BPB, [(d, m) for d, m in P7]), ((AGNUS + 19) * BPB, [(d, m - 12) for d, m in augment(HEAD_BM)])]
    harm_fit(P, AGNUS + 1, DONA - 2, E, CANDS_BM)
    for q in range((DONA - 2) * BPB, DONA * BPB): P.harm[q] = 'F#7' if q < (DONA - 1) * BPB else 'A7'
    # Dona nobis pacem
    P.section(DONA, 'Dona nobis pacem — 総奏 (ニ長調, ♩=72)', 'バッハの Dona nobis pacem のように総奏で閉じる: 国歌の全曲を総奏で (トランペット・Vn I・フルート・ホルン・トロンボーン・ティンパニ)、06:42 の実音、ニ長調の和音、深い鐘')
    harm_fit(P, DONA + 1, DONA + 1 + SSB_BARS + 1, [((DONA + 1) * BPB, SSB)], CANDS_D)
    for q in range((DONA + 2 + SSB_BARS) * BPB, TOTAL * BPB): P.harm[q] = 'D'
    return P

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * tempo_of(bar) / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 1 else 0.02, fout=5.0, semis=sm, rid=rid + '.wav', tag='10/13 %s — 実音 (半音上げてロ短調に)' % ('06:41' if rid == R41 else '06:42'))
    # Kyrie I
    for b in range(KYRIE1 + 1, KYRIE1 + 6, 4): oadd('V1', b * BPB, 5 * BPB, 90, 0.12, '高い開いた 5 度 (Vn, pp)'); oadd('V2', b * BPB + 0.05, 5 * BPB, 83, 0.1)
    walking(P, KYRIE1 + 2, KYRIE1 + 38, 0.2, '歩く低音 (Cb・Vc)')
    for b in range(KYRIE1 + 2, KYRIE1 + 6): oadd('CL', b * BPB, BPB + 0.3, tones_of(P.harm[b * BPB], 50, 62)[0], 0.18, '低いクラリネット' if b == KYRIE1 + 2 else None)
    for k, (v, tr) in enumerate((('V2', 0), ('V1', 12), ('VA', -12), ('VC', -24))):
        line(v, KYRIE1 + 6 + 3 * k, HEAD_BM, tr + (7 if k % 2 else 0), 0.28, 'Kyrie — 主題 (国歌の頭、ロ短調)' + (' 答唱' if k % 2 else '') if k < 2 else None)
        if k > 0: line((('V2', 0), ('V1', 12), ('VA', -12), ('VC', -24))[k - 1][0], KYRIE1 + 6 + 3 * k, CS, (('V2', 0), ('V1', 12), ('VA', -12), ('VC', -24))[k - 1][1] + (7 if (k - 1) % 2 else 0), 0.2, '対主題 (下行)' if k == 1 else None)
    for b in range(KYRIE1 + 10, KYRIE1 + 22, 2): oadd('CL', b * BPB, 2 * BPB + 0.3, tones_of(P.harm[b * BPB], 50, 62)[1 % len(tones_of(P.harm[b * BPB], 50, 62))], 0.16, None)
    chord_pad(P, KYRIE1 + 14, KYRIE1 + 38, [('TB', 43, 57)], 0.14, 'トロンボーンの和音')
    for k, (v, tr) in enumerate((('V1', 12), ('VA', -12), ('V2', 0), ('VC', -24))): line(v, KYRIE1 + 22 + 2 * k, HEAD_BM, tr, 0.28, '主題 (2 回目の提示)' if k == 0 else None)
    for k, (v, tr) in enumerate((('V2', 0), ('V1', 12), ('VA', -12), ('VC', -24))): line(v, KYRIE1 + 30 + k, HEAD_BM, tr, 0.3, 'ストレッタ' if k == 0 else None)
    line('FL', KYRIE1 + 34, HEAD_BM, 24, 0.16, 'フルート'); line('CL', KYRIE1 + 34, HEAD_BM, 0, 0.2, None)
    for k, b in enumerate(range(KYRIE1 + 30, KYRIE1 + 38, 2)): oadd('TP', b * BPB, 2.0, 35, 0.26 + 0.03 * k, 'ティンパニ' if k == 0 else None)
    for i, m in enumerate((35, 47, 54, 59, 66, 71)): oadd(('CB', 'VC', 'TB', 'VA', 'V2', 'V1')[i], (KYRIE1 + 38) * BPB + 0.03 * i, 2 * BPB - 0.5, m, 0.2, 'ロ短調の開いた 5 度' if i == 0 else None)
    # Christe
    for k, (v, tr, g) in enumerate((('FL', 12, 0.18), ('WW', 0, 0.18))): line(v, CHRISTE + 2 + k, P2, tr, g, ('二重唱 — フルートとオーボエ (カノン、1 小節遅れ)' if k == 0 else None))
    for k, (v, tr, g) in enumerate((('V1', 12, 0.26), ('V2', 7, 0.24))): line(v, CHRISTE + 12 + k, P2, tr, g, ('二重唱 — Vn I・Vn II' if k == 0 else None))
    roots(P, CHRISTE + 1, KYRIE2 - 1, [('VC', 12), ('CB', 0)], 0.16, 'Vc・Cb の根音', every=2)
    chord_pad(P, CHRISTE + 6, KYRIE2 - 1, [('VA', 55, 67)], 0.12, 'Va')
    # Kyrie II
    for k, (vs, tr) in enumerate(((('VC', 'TB'), -24), (('VA', 'HN'), -12), (('V2',), 0), (('V1',), 12))):
        for v in vs: line(v, KYRIE2 + 1 + 4 * k, augment(HEAD_BM), tr + (7 if k % 2 else 0), 0.24 if v in ('V1', 'V2', 'VA', 'VC') else 0.2, ('Kyrie II — 主題の拡大 (古様式)' if (k == 0 and v == 'VC') else None))
    line('CL', KYRIE2 + 13, augment(HEAD_BM), 0, 0.18, 'クラリネット'); line('CL', KYRIE2 + 17, augment(HEAD_BM), -12, 0.16, None)
    chord_pad(P, KYRIE2 + 9, GLORIA - 3, [('CB', 43, 55)], 0.18)
    for i, m in enumerate((35, 47, 54, 59, 66, 71)): oadd(('CB', 'VC', 'TB', 'VA', 'V2', 'V1')[i], (GLORIA - 3) * BPB + 0.03 * i, 3 * BPB - 0.5, m, 0.22, '開いた 5 度 (Kyrie の終わり)' if i == 0 else None)
    # Gloria
    line('TR', GLORIA + 1, HEAD, 0, 0.3, 'Gloria — トランペットの頭 (ニ長調)'); line('TR', GLORIA + 3, HEAD, 12, 0.3, None); line('HN', GLORIA + 1, HEAD, -12, 0.24, 'ホルン')
    for b in (GLORIA + 1, GLORIA + 3): oadd('TP', b * BPB, 1.5, 38, 0.5, 'ティンパニ' if b == GLORIA + 1 else None); oadd('TP', b * BPB + 2, 1.0, 45, 0.4, None)
    tremolo(P, GLORIA, GLORIA + 6, 0.14, '弦のトレモロ (Vn II・Va)')
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, GLORIA + 6 + 3 * k, P5[:8], tr, 0.28, 'rockets\' red glare の句のフガート (Vn I → Vn II → Va → Vc)' if k == 0 else None)
    line('FL', GLORIA + 15, P5[:8], 24, 0.16, 'フルート'); line('TR', GLORIA + 17, P5[:8], 0, 0.28, 'トランペット')
    roots(P, GLORIA + 6, TERRA, [('CB', 0), ('TB', 12)], 0.2, 'Cb・トロンボーンの根音', every=2)
    tremolo(P, GLORIA + 15, TERRA, 0.12, None)
    for k, b in enumerate(range(GLORIA + 14, TERRA, 2)): oadd('TP', b * BPB, 2.0, 38 if k % 2 == 0 else 45, 0.3, None)
    # Et in terra pax
    line('CL', TERRA + 2, HEAD_BM, 0, 0.2, 'Et in terra pax — クラリネットの頭 (ロ短調、静かに)'); line('CL', TERRA + 7, HEAD_BM, -12, 0.18, None); line('WW', TERRA + 12, invert(HEAD_BM), 0, 0.16, 'オーボエ (反行)')
    chord_pad(P, TERRA, CRUC, [('VA', 50, 64), ('VC', 43, 55), ('CB', 43, 55)], 0.12, '低い弦 (静かに)'); chord_pad(P, TERRA + 4, CRUC, [('TB', 43, 57)], 0.1)
    for b in range(TERRA, CRUC, 2): oadd('TP', b * BPB, 1.0, 35, 0.14, 'ティンパニ (小さく)' if b == TERRA else None)
    # Crucifixus
    first = True
    for b in range(CRUC, RESURR):
        for k in range(BPB):
            m = GROUND_M[((b - CRUC) % 2) * 4 + k]
            oadd('VC', b * BPB + k, 1.0, m, 0.24, 'Crucifixus — 半音で下る固執低音 (Vc・Cb)' if first else None); oadd('CB', b * BPB + k, 1.0, m - 12, 0.26); first = False
    sighs(P, CRUC + 2, RESURR - 1, 0.16, 'ため息 (2 音のスラー、Vn I・Vn II)')
    aug7 = augment(P7)
    line('WW', CRUC + 2, aug7, 0, 0.2, 'オーボエ — 最後の句の拡大 (×2)'); line('HN', CRUC + 10, aug7, -12, 0.22, 'ホルン'); line('V1', CRUC + 18, aug7, 12, 0.22, 'Vn I'); line('CL', CRUC + 18, aug7, 0, 0.16, None)
    chord_pad(P, CRUC + 4, RESURR - 1, [('TB', 43, 57)], 0.12, 'トロンボーン'); chord_pad(P, CRUC, RESURR - 1, [('VA', 55, 67)], 0.1)
    # Et resurrexit
    for rep in range(2):
        t = (RESURR + 1 + 9 * rep) * BPB; first = True
        for d, m in P1 + P2:
            oadd('TR', t, d, m, 0.34, 'Et resurrexit — トランペット・Vn I (国歌の第 1・2 句)' if (first and rep == 0) else None); oadd('V1', t, d, m, 0.34); oadd('FL', t, d, m + 12, 0.2); oadd('HN', t, d, m - 12, 0.22); first = False; t += d
    tremolo(P, RESURR + 1, SANCTUS - 1, 0.14, 'Vn II・Va の 8 分音符')
    roots(P, RESURR + 1, SANCTUS - 1, [('VC', 12), ('CB', 0), ('TB', 12)], 0.22, 'Vc・Cb・トロンボーンの根音', every=2)
    for k, b in enumerate(range(RESURR + 1, SANCTUS - 1, 3)): oadd('TP', b * BPB, 2.0, 38, 0.4, 'ティンパニ' if k == 0 else None)
    # Sanctus
    tremolo(P, SANCTUS, HOSANNA, 0.16, 'Sanctus — 弦のトレモロ')
    line('TR', SANCTUS + 1, augment(HEAD), 0, 0.32, 'トランペット — 頭の拡大'); line('TR', SANCTUS + 6, augment(HEAD), 12, 0.3, None); line('HN', SANCTUS + 1, augment(HEAD), -12, 0.24, 'ホルン'); line('V1', SANCTUS + 6, augment(HEAD), 12, 0.3, 'Vn I')
    chord_pad(P, SANCTUS, HOSANNA, [('TB', 43, 57), ('CB', 43, 55)], 0.2, 'トロンボーン・Cb の和音')
    for b in range(SANCTUS, HOSANNA, 2): oadd('TP', b * BPB, 2.0, 38, 0.45, 'ティンパニ' if b == SANCTUS else None); oadd('TP', b * BPB + 3, 1.0, 45, 0.3, None)
    # Hosanna
    for k, (v, tr) in enumerate((('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))): line(v, HOSANNA + 1 + 2 * k, HEAD, tr + (7 if k % 2 else 0), 0.3, 'Hosanna — 頭のフガート (Vn I → Vn II → Va → Vc)' if k == 0 else None)
    line('FL', HOSANNA + 9, HEAD, 24, 0.18, 'フルート'); line('TR', HOSANNA + 9, HEAD, 12, 0.3, 'トランペット'); line('TB', HOSANNA + 9, HEAD, -12, 0.26, None)
    roots(P, HOSANNA + 1, BENED, [('CB', 0)], 0.22, None, every=2); oadd('TP', (BENED - 1) * BPB, 3.0, 38, 0.5, None)
    # Benedictus
    for k, (v, tr, g) in enumerate((('FL', 12, 0.18), ('WW', 0, 0.18), ('CL', -12, 0.18), ('HN', -5, 0.2))): line(v, BENED + 1 + 3 * k, P2, tr, g, 'Benedictus — 四重奏 (フルート → オーボエ → クラリネット → ホルン)' if k == 0 else None)
    line('FL', BENED + 14, P2, 12, 0.16, None); line('WW', BENED + 14, [(d, m - 5) for d, m in P2], 0, 0.16, None)
    first = True
    for b in range(BENED + 1, AGNUS - 1):
        for k in (0, 2):
            r = 38 + chord(P.harm[b * BPB + k])['root']; oadd('VC', b * BPB + k, 0.3, r + 12, 0.2, '弦の短い根音 (ピツィカートのように)' if first else None); oadd('CB', b * BPB + k, 0.3, r, 0.22); first = False
    chord_pad(P, BENED + 1, AGNUS - 1, [('VA', 55, 67)], 0.08)
    # Agnus Dei
    add('X', AGNUS * BPB, 12, 35, 0.3, '深い鐘')
    line('CL', AGNUS + 2, P7, -12, 0.26, 'Agnus Dei — クラリネットの独唱 (最後の句、ロ短調の上で)'); line('CL', AGNUS + 10, P7, 0, 0.24, None); line('WW', AGNUS + 10, [(d, m - 5) for d, m in P7], 0, 0.14, 'オーボエ')
    line('HN', AGNUS + 19, augment(HEAD_BM), -12, 0.22, 'ホルン — 頭の拡大'); line('CL', AGNUS + 23, HEAD_BM, 0, 0.2, None)
    sighs(P, AGNUS + 1, DONA - 2, 0.14, 'ため息 (Vn I・Vn II)')
    walking(P, AGNUS + 2, DONA - 2, 0.16, '歩く低音')
    chord_pad(P, AGNUS + 6, DONA - 2, [('TB', 43, 57)], 0.1, 'トロンボーン')
    for i, m in enumerate((42, 54, 58, 61, 64)): oadd(('CB', 'TB', 'VA', 'V2', 'V1')[i], (DONA - 2) * BPB + 0.03 * i, 2 * BPB - 0.3, m, 0.2, 'ファ# の属和音 → ニ長調へ' if i == 0 else None)
    # Dona nobis pacem
    orchestrate(P, DONA + 1, True, 'Dona nobis pacem (国歌の全曲、総奏)')
    for i, m in enumerate((38, 50, 57, 62, 66, 74, 78)): oadd(('CB', 'VC', 'TB', 'HN', 'VA', 'V2', 'V1')[i], (DONA + 2 + SSB_BARS) * BPB + 0.03 * i, (TOTAL - DONA - 2 - SSB_BARS) * BPB - 1.0, m, 0.22, 'ニ長調の和音 (レ・ラ・ファ#)' if i == 0 else None)
    oadd('TR', (DONA + 2 + SSB_BARS) * BPB, 4 * BPB, 74, 0.26, None); oadd('FL', (DONA + 2 + SSB_BARS) * BPB, 6 * BPB, 86, 0.16, None); oadd('TP', (DONA + 2 + SSB_BARS) * BPB, 4.0, 38, 0.5, None)
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 3) * BPB, 14, 38, 0.4, None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R41, R42], 'piano_decay': 2.6, 'reverb': [8.0, 3.0, 0.5], 'orchestra': True,
        'title': 'Requiem BADA — CXXXVII · Missa in si minore sull\'inno americano',
        'subtitle': '10/13 の 2 曲を雰囲気に、バッハのロ短調ミサの形 (Kyrie I のフーガ → Christe → Kyrie II → Gloria → Crucifixus の固執低音 → Et resurrexit → Sanctus → Hosanna → Benedictus → Agnus Dei → Dona nobis pacem) に、モーツァルトのレクイエムの舞台 (歩く低音、低いクラリネット、トロンボーン、ため息の弦、トレモロ、独唱) で、アメリカ国歌を主題に。管弦楽だけ、♩=56 / 72',
        'legend': ['X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'CL', 'HN', 'TR', 'TB', 'TP'], 'vname': {'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
        'footer': ['主題 = The Star-Spangled Banner (music21 の収録譜、ニ長調): 頭 (ソ・ミ・ド・ミ・ソ・ド) をロ短調に移してフーガの主題に、第 2 句を二重唱に、「rockets\' red glare」を Gloria に、最後の句を Crucifixus と Agnus Dei に、全曲を Dona nobis pacem に',
                   'バッハ・モーツァルトの旋律の引用はなく、形と様式 (フーガ・古様式・固執低音・歩く低音・ため息・トレモロ) だけ。10/13 の実音は Kyrie I・Christe・Agnus Dei・Dona nobis pacem に小さく。鐘は始め・Agnus Dei・終わりに深いもの。声なし。']}

if __name__ == '__main__':
    print('SSB beats', SSB_BEATS, 'bars', SSB_BARS, '| P2', ' '.join('%s:%g' % (name_of(m), d) for d, m in P2), '| P7', ' '.join('%s:%g' % (name_of(m), d) for d, m in P7))
    compose.main(OUT, seed=137, bpm=56, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); d['notes'] = []
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', Counter(e['v'] for e in d['extras']))
