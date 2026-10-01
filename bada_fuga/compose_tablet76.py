#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXVI · Requiem della vita (人生の縮図 — 断片ではなく、調和と共鳴でつながる 1 つのレクイエム)
  これまでの主題曲 (ピアノの実音の録音) から作った主題で、人の一生を途切れずにたどる。録音の抜粋は使わず、すべて楽譜から (録音から切り出したピアノの 1 音で)。
  調和と共鳴: 長調の区間は和声をすべて書き (旋律の音を和音に含め、声部はなめらかに)、3 連の分散和音が長く響き合う。短調の区間はフーガとコラール。
  一生の区間 (速さも一生に合わせて変わる):
    1. Nascita 誕生 (ニ長調, ♩=56)       — 光のような分散和音から、9/25 12:46 の「上る」主題 (長調の形) が生まれ、少しずつ高く育つ
    2. Gioventù 青春 (ト長調, ♩=72)      — 9/24 08:53 の主題が流れる 3 連の分散和音の上で歌い、後半は 3 度・6 度で寄り添う 2 声に
    3. Lotta 闘い (ロ短調, ♩=72)         — 9/24 08:49 の主題の 4 声フーガ (提示・下属調・ストレッタ・保続低音)
    4. Amore e perdita 愛と喪失 (ト短調, ♩=60) — 9/23 08:06 の下りる嘆きの主題のコラール、最後はその主題を 2 倍にしてバスで下りる (ラメント・バス)
    5. Vecchiaia 老い (ホ短調, ♩=52)     — 9/23 08:09 の主題を 8 倍に伸ばして打ち直す (時間がゆっくりになる)。その上に、誕生と青春の主題が思い出のように戻る
    6. Morte 死 (ニ短調, ♩=48)           — 9/25 12:46 の「下りる」主題を 2 倍で。主音レの鐘が小節ごとに鳴り、消えていく
    7. Lux aeterna 永遠の光 (ニ長調, ♩=52) — 誕生の主題が 2 倍の長さで戻り、1 倍と 2 倍が重なって、ニ長調の Amen で閉じる (一生がめぐる)
  使い方: python compose_tablet76.py <bank74.json> [score_tablet76.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet63 as LXIII
import compose_tablet65 as LXV
import compose_tablet69 as LXIX

R0806, R0809, R0849, R0853, R1246 = '20260923_080607', '20260923_080918', '20260924_084937', '20260924_085314', '20260925_124643'
VOICE_SRC = {'S': R0809, 'A': R0853, 'T': R0849, 'B': R1246}
DYNK = 1.3
MAJ = {5: 6, 10: 11, 0: 1}                         # ニ短調の音 → ニ長調の音 (ファ → ファ#、シ♭ → シ、ド → ド#)
CMAJ = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m']

def subj_at(rid, semis, at=None, w=8.0):
    segs = CT.REC[rid]['segs']
    if at is None: t0, inside = CT.excerpt(rid, semis, 13.0)
    else:
        t0 = min(segs, key=lambda x: abs(x['t'] - 0.03 - at))['t'] - 0.03; inside = [x for x in segs if t0 <= x['t'] < t0 + w]
    return LXIII.smooth(CT.make_subject(inside, semis, 60))

def major(s_): return [(d, m - m % 12 + MAJ.get(m % 12, m % 12)) for d, m in s_]

DMAJ_PCS = {2, 4, 6, 7, 9, 11, 1}
def dia_third(m):
    up = [x for x in range(m + 1, m + 6) if x % 12 in DMAJ_PCS]
    return up[1] if len(up) > 1 else m + 4

def harm_major(s_):
    """長調の主題に 1 拍ごとの和音: 主題の音をいちばん多く含む和音 (頭と終わりは主和音、終わりの前は属和音を好む)"""
    spans, t = [], 0.0
    for d, m in s_: spans.append((t, t + d, m)); t += d
    out = []
    for b in range(int(round(t))):
        def score(cs):
            c = chord(cs); sc = 0.0
            for s0, s1, m in spans:
                ov = min(b + 1, s1) - max(b, s0)
                if ov > 0: sc += ov * (2.0 if s0 <= b < s1 else 1.0) * (1.0 if m % 12 in c['pcs'] else -0.8)
            if b == 0 or b == int(round(t)) - 1: sc += 0.7 if cs == 'D' else 0
            if b == int(round(t)) - 2: sc += 0.4 if cs in ('A', 'A7') else 0
            return sc
        out.append(max(CMAJ, key=score))
    return out

def chorale(P, f, beats, chords, skip=('S',), lab='和声', dyn=None):
    skip = tuple(skip)
    """和音 (1 拍ごと) を A・T・B に置く: 前の音にいちばん近い和音の音を選び (なめらかに)、同じ音が続けば 1 つに伸ばす"""
    prev = {'S': 74, 'A': 64, 'T': 57, 'B': 45}; rng = {'S': (67, 79), 'A': (57, 71), 'T': (48, 64), 'B': (36, 52)}
    cur = {v: None for v in 'SATB'}
    def flush(v):
        if cur[v]: s_, d, m = cur[v]; P.place(v, f, [(d, m)], 0, lab, beat=s_)
    for b, cs in enumerate(chords[:beats]):
        c = chord(cs); pcs = sorted(c['pcs']); used = set()
        for v in ('B', 'T', 'A', 'S'):
            if v in skip: continue
            lo, hi = rng[v]
            want = [c['root']] if v == 'B' else [p for p in pcs if p not in used] or pcs
            m = min((x for x in range(lo, hi + 1) if x % 12 in want), key=lambda x: abs(x - prev[v]))
            used.add(m % 12); prev[v] = m
            if cur[v] and cur[v][2] == m and cur[v][0] + cur[v][1] == b: cur[v] = (cur[v][0], cur[v][1] + 1, m)
            else: flush(v); cur[v] = (b, 1, m)
    for v in 'SATB':
        if v not in skip: flush(v)

def build():
    rise = subj_at(R1246, 3, at=62.5)              # 上る線 (12:46)
    fall = subj_at(R1246, 3, at=181.5)             # 下りる線 (12:46)
    youth = subj_at(R0853, 2); struggle = subj_at(R0849, 3); lament = subj_at(R0806, -4); old = subj_at(R0809, 2)
    riseM, youthM = major(rise), major(youth)
    for name, s_ in (('rise', rise), ('fall', fall), ('youth', youth), ('struggle', struggle), ('lament', lament), ('old', old)):
        print(name, ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    T5.SUBJ[R0849] = (struggle, CT.harmonize(struggle))
    plan = [16, 16, 16, 12, 16, 8, 12]; total = sum(plan)
    P = Piece(total)
    for k in range(total): P.dyn[k] = DYNK
    b = 0
    def sec(n_, bpm, semis, title, sub):
        nonlocal b
        f = b; P.section(f, title, sub); CT.LAYOUT.append((f, f + n_, semis, VOICE_SRC, {}))
        for k in range(n_): P.tempo[f + k] = bpm
        b += n_; return f
    def mel(v, bar, s_, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in s_], 0, lab)
    def setH(f, chords):
        for i, c in enumerate(chords): P.harm[f * BPB + i] = c
    HR = harm_major(riseM); HY = harm_major(youthM)
    # ================= 1. Nascita (ニ長調)
    f = sec(16, 56, 0, '1. Nascita 誕生 (ニ長調)', '光のような分散和音から、12:46 の上る主題 (長調) が生まれ、少しずつ高く育つ')
    setH(f, ['D'] * 4 + ['G'] * 4 + ['A'] * 4 + ['D'] * 4)
    for v, m in (('B', 38), ('T', 54), ('A', 62)):
        P.place(v, f, [(4, m), (4, m + 5 if v != 'B' else 43), (4, m + 7 if v != 'B' else 45), (4, m if v != 'B' else 38)], 0, '和声')
    P.rest_bars('S', f, f + 4)
    for k, (bar, tr, oc) in enumerate(((4, 0, 0), (6, 5, 0), (8, 7, -12), (10, 0, 12))):    # 主・下属・属・オクターヴ上 — 育つ
        mel('S', f + bar, riseM, tr + oc, '誕生の主題 (12:46 上る線)' if k == 0 else None)
        ch = [transpose_h([[c]], tr)[0][0] for c in HR]; setH(f + bar, ch); chorale(P, f + bar, 8, ch)
    mel('T', f + 12, riseM, -12, '誕生の主題 ×2 (育つ)', k=2); ch2 = [c for c in HR for _ in range(2)]; setH(f + 12, ch2)
    chorale(P, f + 12, 16, ch2, skip=('T',))                                         # ソプラノも和音の音をなめらかにたどる
    for k in range(16): P.dyn[f + k] = DYNK * (0.5 + 0.25 * k / 15)
    LXIII.ARP.append((f, f + 16, 0.09, 0))
    # ================= 2. Gioventù (ト長調)
    f = sec(16, 72, 5, '2. Gioventù 青春 (ト長調)', '08:53 の主題が流れる分散和音の上で歌い、後半は 3 度・6 度で寄り添う 2 声に')
    for k, tr in enumerate((0, 5, 7, 0)):
        mel('S', f + 2 * k, youthM, tr if tr < 7 else tr - 12, '青春の主題 (08:53)' if k == 0 else None)
        ch = [transpose_h([[c]], tr)[0][0] for c in HY]; setH(f + 2 * k, ch); chorale(P, f + 2 * k, 8, ch)
    for k, tr in enumerate((0, 7, 5, 0)):                                              # 後半: アルトが主題、ソプラノが 3 度上で寄り添う
        bar = f + 8 + 2 * k; ch = [transpose_h([[c]], tr)[0][0] for c in HY]; setH(bar, ch)
        base = [(d, m + (tr if tr < 7 else tr - 12)) for d, m in youthM]                 # アルトはレ 4〜レ 5 のあたり
        P.place('A', bar, base, 0, '青春の主題 — 2 声で' if k == 0 else None)
        third, t = [], 0.0                                                               # 寄り添う声: その拍の和音の音のうち、主題のすぐ上 (3 度〜6 度) — 調和
        for d, m in base:
            pcs = chord(ch[min(len(ch) - 1, int(t))])['pcs']
            third.append((d, next((x for x in range(m + 3, m + 10) if x % 12 in pcs), dia_third(m)))); t += d
        P.place('S', bar, third, 0, '寄り添う声 (3 度・6 度)' if k == 0 else None)
        chorale(P, bar, 8, ch, skip=('S', 'A'))
    for k in range(16): P.dyn[f + k] = DYNK * 0.8
    LXIII.ARP.append((f, f + 16, 0.11, 5))
    # ================= 3. Lotta (ロ短調)
    f = sec(16, 72, -3, '3. Lotta 闘い (ロ短調)', '08:49 の主題の 4 声フーガ — 提示、下属調、ストレッタ、保続低音')
    T11.bach_fugue(P, f, R0849, '闘い')
    for k in range(16): P.dyn[f + k] = DYNK * (0.68 + 0.14 * k / 15)
    # ================= 4. Amore e perdita (ト短調)
    f = sec(12, 60, 5, '4. Amore e perdita 愛と喪失 (ト短調)', '08:06 の下りる嘆きの主題のコラール — 最後はその主題を 2 倍にしてバスで下りる (ラメント・バス)')
    HL = CT.harmonize(lament)
    for k, tr in enumerate((0, 0, 5, 0)):
        mel('S', f + 2 * k, lament, tr + 12 if max(m for _, m in lament) + tr < 72 else tr, '嘆きの主題 (08:06)' if k == 0 else None)
        P.set_harms(f + 2 * k, transpose_h(HL, tr))
    fl = HL[0] + HL[1]; P.set_harms(f + 8, [[fl[2 * i], fl[2 * i], fl[2 * i + 1], fl[2 * i + 1]] for i in range(4)])   # 2 倍の嘆きの和声
    mel('B', f + 8, lament, -24, 'ラメント・バス (嘆きの主題 ×2)', k=2)
    for k in range(12): P.dyn[f + k] = DYNK * (0.72 - 0.12 * max(0, k - 8) / 4)
    LXIII.ARP.append((f + 8, f + 12, 0.08, 5))
    # ================= 5. Vecchiaia (ホ短調)
    f = sec(16, 52, 2, '5. Vecchiaia 老い (ホ短調)', '08:09 の主題を 8 倍に伸ばして打ち直す — その上に誕生と青春の主題が思い出のように戻る')
    HO = ['A7', 'A7', 'Dm', 'Dm', 'Bb', 'Bb', 'Gm', 'Dm']
    LXIX.aug(P, f, 8, old, HO, '老いの主題 (08:09) ×8 — 時間がゆっくりに')
    P.set_harms(f + 2, CT.harmonize(rise)); mel('S', f + 2, rise, 0, '思い出: 誕生の主題')
    P.set_harms(f + 5, CT.harmonize(youth)); mel('A', f + 5, youth, -12 if min(m for _, m in youth) - 12 >= 55 else 0, '思い出: 青春の主題')
    P.set_harms(f + 14, CT.harmonize(rise)); mel('S', f + 14, rise, 0, '思い出: 誕生の主題 (もう一度)')
    for k in range(16): P.dyn[f + k] = DYNK * (0.66 - 0.1 * k / 15)
    LXIII.ARP.append((f + 8, f + 14, 0.07, 2))
    # ================= 6. Morte (ニ短調)
    f = sec(8, 48, 0, '6. Morte 死 (ニ短調)', '12:46 の下りる主題を 2 倍で — 主音レの鐘が小節ごとに鳴り、消えていく')
    HF = [c for c in ['A7', 'Gm', 'A7', 'Gm', 'Gm', 'Em7b5', 'Dm', 'Dm'] for _ in range(2)]
    for k in range(2):
        setH(f + 4 * k, HF); mel('S', f + 4 * k, fall, 0, '死の主題 (12:46 下りる線) ×2' if k == 0 else None, k=2)
    P.place('B', f, [(4, n('D2'))] * 8, 0, '主音の鐘')
    for k in range(8): P.dyn[f + k] = DYNK * (0.7 - 0.28 * k / 7)
    # ================= 7. Lux aeterna (ニ長調)
    f = sec(12, 52, 0, '7. Lux aeterna 永遠の光 (ニ長調)', '誕生の主題が 2 倍の長さで戻り、1 倍と 2 倍が重なって、ニ長調の Amen で閉じる — 一生がめぐる')
    ch2 = [c for c in HR for _ in range(2)]
    setH(f, ch2); mel('S', f, riseM, 0, '誕生の主題 ×2 (光)', k=2); chorale(P, f, 16, ch2)
    setH(f + 4, ch2); mel('T', f + 4, riseM, -12, '誕生の主題 ×2', k=2); mel('S', f + 4, riseM, 0, '誕生の主題 ×1'); mel('S', f + 6, riseM, 0, None)
    chorale(P, f + 4, 16, ch2, skip=('S', 'T'))
    setH(f + 8, ['G'] * 4 + ['A7'] * 4 + ['D'] * 8)                                      # Amen: IV → V → I
    chorale(P, f + 8, 16, ['G'] * 4 + ['A7'] * 4 + ['D'] * 8, skip=())
    P.place('S', f + 8, [(4, n('B4')), (4, n('A4')), (8, n('F#4'))], 0, 'Amen')
    for k in range(12): P.dyn[f + k] = DYNK * (0.55 + 0.1 * min(k, 6) / 6 - 0.15 * max(0, k - 8) / 4)
    LXIII.ARP.append((f, f + 10, 0.09, 0))
    P.entries[:] = [e for e in P.entries if e[1] != '和声']                       # 伴奏の和音にはラベルを出さない
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [R0809, R0853, R0849, R1246, R0806], 'piano_decay': 2.4, 'reverb': [6.0, 2.2, 0.5],
    'title': 'Requiem BADA — LXXVI · Requiem della vita',
    'subtitle': '人生の縮図 — 誕生・青春・闘い・愛と喪失・老い・死・永遠の光を、途切れずに調和と共鳴でたどるレクイエム',
    'legend': ['PF'], 'vname': {'PF': '分散和音'},
    'footer': ['誕生 ニ長調 → 青春 ト長調 → 闘い ロ短調 → 愛と喪失 ト短調 → 老い ホ短調 → 死 ニ短調 → 永遠の光 ニ長調',
               '主題はすべて主題曲 (9/23 08:06・08:09、9/24 08:49・08:53、9/25 12:46 の録音) から。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet76.json'
    compose.main(out, seed=176, bpm=56, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    K.BPM = 60; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if n_['v'] == 'S' and lab and lab not in ('和声',) else 1.2), 4)
    LXV.SWELL[:] = LXIX.SWELL; LXV.swell(d); LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:22]) for s in d['sections']])
