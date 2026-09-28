#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLVIII · Klang und Fuge (XLVII の大聖堂に、5 人の歌い手とビオラ — 共鳴する不協和音のレクイエムとドイツ語のフーガ)
  録音 5 本 (9/24): 08:49 (ヘ短調)、08:53 (ホ短調)、11:18 (変ロ短調)、11:21 (ヘ短調)、11:23 (ホ短調)。
  歌い手 5 人 (すべて 9/28 17:46 のわたしの声の響きから、響きの長さと声域を変えて作る — sing_user.py):
    ソプラノの淑女・アルトの淑女・高音の紳士 (テノール)・バリトンの紳士・重低音の紳士 (バッソ・プロフォンド)。
  ビオラ: フーガではアルトの声部を、コラールでは内声を弾く。4 声はパイプオルガン、大聖堂の長い響き。
  共鳴する不協和音 (Klang): 全員が 9 度・4 度・導音のぶつかる和音を長く響かせ、長調 / 短調の和音へ解決する (レクイエムの嘆き)。
  ドイツ語のフーガ: 主題が入るたびに、その声部の歌い手が同じ祈りを歌う (バリトンはテノールの 1 オクターヴ下で重なる)。
  歌詞はレクイエムの典礼文のドイツ語 (Herr, gib ihnen ewige Ruhe / und das ewige Licht leuchte ihnen / Herr, erbarme dich …、lyrics_tablet.py の tablet48)。
  形式 (♩=56):
    Introitus (08:49 の実音) → Klang I „Ruhe“ (ホ短調 → ホ長調) → Fuga I „Herr, gib ihnen ewige Ruhe“ (ホ短調、08:53 の主題)
    → Kyrie „Herr, erbarme dich“ (全員のコラール) → Klang II „Tränen“ (ヘ短調) → Fuga II „Ewiges Licht“ (ヘ短調、11:21 の主題) → Amen (ヘ長調)
  使い方: python compose_tablet48.py <bank37.json> [score_tablet48.json]  (歌は add_vocals.py tablet48 ... voice.npz、曲だけの演奏はこの楽譜のまま)
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 56; BAR_S = 240.0 / BPM
B1, B2, B3, B4, B5 = '20260924_084937', '20260924_085314', '20260924_111846', '20260924_112131', '20260924_112313'
KEYS = {B1: 3, B2: 2, B3: -4, B4: 3, B5: 2}
T7.KEYS.update(KEYS)
ORDER = [B2, B5, B4, B1, B3]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤')))
VOICE_SRC = {'S': B4, 'A': B2, 'T': B1, 'B': B5}
DYNK = 1.3
STRG, LOWS, VIOLA = [], [], []
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK
def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
def low_root(c, lo=36): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
    for b0, b1, gain in STRG:                      # 弦 (和音を全音符で、やわらかく)
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB]); tones = pcs_in(c, 52, 74)
            for iv, m in zip(('V2', 'V1'), [tones[min(1, len(tones) - 1)], tones[min(2, len(tones) - 1)]]):
                add(iv, bar * BPB, 4.05, m, gain * dk(P, bar), None)
    for b0, b1, gain in LOWS:                      # チェロとコントラバス: 根音を全音符で
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c, 36)
                add('VC', bar * BPB + half, 2.05, r + 12, gain * dk(P, bar), None); add('CB', bar * BPB + half, 2.05, r, gain * 0.8 * dk(P, bar), None)
    for b0, b1, gain, v in VIOLA:                  # ビオラ: 声部 v の旋律を弾く (音域はビオラ = ハ 3〜ホ 5 に)
        for s_, d, m, lab in events[v]:
            if b0 * BPB <= s_ < b1 * BPB:
                while m > 76: m -= 12
                while m < 48: m += 12
                add('VA', s_, d * 1.0, m, gain, None)

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def place(P, bar, mat_, label):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > 77: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], 60); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    total = 4 + 2 + 16 + 8 + 2 + 16 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def excerpt(rid, bars, title, sub, semis, t0=None, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, t0=t0, bpm=BPM, gmul=0.6)
        for v in VOICES: P.rest_bars(v, b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, semis, {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis, src=None):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, VOICE_SRC if src is None else {v: src for v in VOICES}, {})); b += bars; return f
    def klang(f, parts, harms, word):              # 共鳴する不協和音: 4 声が置いた音を長く響かせ、2 小節目で解決する
        P.set_harms(f, harms)
        for v, pitches in parts.items(): P.place(v, f, [(4, n(pitches[0])), (4, n(pitches[1]))], 0, 'Klang „%s“' % word)
    # ================= Introitus
    excerpt(B1, 4, 'Introitus — %s の実音 (ヘ短調)' % hm(B1), '大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', 3)
    STRG.append((b - 2, b, 0.02))
    # ================= Klang I (ホ短調 → ホ長調)
    f = section('Klang I „Ruhe“ — 共鳴する不協和音 (ホ短調)', '全員が 9 度・4 度・導音のぶつかる和音を響かせ、ホ長調の和音へ解決する', 2, 2)
    klang(f, {'S': ('E5', 'D5'), 'A': ('C#5', 'A4'), 'T': ('G4', 'F#4'), 'B': ('D3', 'D3')}, [['A7'], ['D']], 'Ruhe')
    STRG.append((f, f + 2, 0.025)); LOWS.append((f, f + 2, 0.025)); VIOLA.append((f, f + 2, 0.05, 'T'))
    for k in range(2): P.dyn[f + k] = DYNK * 0.8
    # ================= Fuga I
    f = section('Fuga I „Herr, gib ihnen ewige Ruhe“ (ホ短調)', '%s の主題の 4 声フーガ — 主題が入るたびに、その声部の歌い手が歌う (ビオラはアルトの声部)' % hm(B2), 16, 2)
    n_ = T11.bach_fugue(P, f, B2, '①')
    for k in range(n_): P.dyn[f + k] = DYNK * 0.72
    VIOLA.append((f, f + 16, 0.045, 'A')); LOWS.append((f + 12, f + 16, 0.018))
    # ================= Kyrie (全員のコラール)
    f = section('Kyrie „Herr, erbarme dich“ — 全員のコラール (ホ短調)', '%s・%s の主題を 2 倍の長さで、5 人が和声で歌う (ビオラは内声)' % (hm(B5), hm(B2)), 8, 2)
    for k, r in enumerate([B5, B2]):
        place(P, f + 4 * k, aug(subj(r)), 'コラール (%s) · 2 倍' % hm(r))
        T5.harm_from_entries(P, f + 4 * k, f + 4 * k + 4, [((f + 4 * k) * BPB, aug(subj(r)))])
    for k in range(8): P.dyn[f + k] = DYNK * 0.7
    STRG.append((f, f + 8, 0.022)); VIOLA.append((f, f + 8, 0.04, 'T'))
    # ================= Klang II (ヘ短調)
    f = section('Klang II „Tränen“ — 共鳴する不協和音 (ヘ短調)', '短 2 度と増 4 度がぶつかる和音を響かせ、ヘ短調の和音へ解決する', 2, 3)
    klang(f, {'S': ('Bb4', 'A4'), 'A': ('A4', 'F4'), 'T': ('E4', 'D4'), 'B': ('D3', 'D3')}, [['A7'], ['Dm']], 'Tränen')
    STRG.append((f, f + 2, 0.025)); LOWS.append((f, f + 2, 0.025)); VIOLA.append((f, f + 2, 0.05, 'T'))
    for k in range(2): P.dyn[f + k] = DYNK * 0.8
    # ================= Fuga II
    f = section('Fuga II „Ewiges Licht“ (ヘ短調)', '%s の主題のフーガ — 最後はストレッタで歌い手が重なる' % hm(B4), 16, 3)
    n_ = T11.bach_fugue(P, f, B4, '②')
    for k in range(n_): P.dyn[f + k] = DYNK * 0.72
    VIOLA.append((f, f + 16, 0.045, 'A')); LOWS.append((f + 12, f + 16, 0.02)); STRG.append((f + 14, f + 16, 0.02))
    # ================= Amen (変格終止 → ヘ長調)
    f = section('Amen — 変格終止 (ヘ長調の和音で)', 'iv → I: 5 人が「Amen」を長く歌い、オルガン・ビオラ・弦が長調の和音で包む', 3, 3)
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    STRG.append((f, f + 3, 0.03)); LOWS.append((f, f + 3, 0.025)); VIOLA.append((f, f + 3, 0.04, 'T'))
    for k in range(3): P.dyn[f + k] = DYNK * 0.8
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.8, 'choir': 'organ', 'organ_gain': 0.45,
    'reverb': [7.0, 2.4, 0.5], 'vo_send': 0.5,
    'title': 'Requiem BADA — XLVIII · Klang und Fuge',
    'subtitle': '共鳴する不協和音のレクイエムとドイツ語のフーガ — 5 人の歌い手 (淑女・紳士)、ビオラ、パイプオルガン (♩=56)',
    'legend': ['TB', 'VA', 'V1', 'VC'], 'vname': {'VA': 'ビオラ', 'V1': '弦', 'VC': 'チェロ'},
    'footer': ['Introitus 08:49 → Klang I „Ruhe“ → Fuga I (08:53) → Kyrie (5 人のコラール) → Klang II „Tränen“ → Fuga II (11:21) → Amen (ヘ長調)',
               '歌い手: ソプラノ・アルトの淑女、テノール・バリトン・重低音の紳士 (9/28 のわたしの声の響きから)。歌詞はレクイエムの典礼文のドイツ語。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet48.json'
    compose.main(out, seed=148, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    # 拍の頭で置いた主題と半音でぶつかる自動の声部の音を動かす (Klang の置いた不協和音はそのまま残す)
    spb = 60.0 / BPM; fixed = 0
    def sounding(t, skip): return [n for n in d['notes'] if n is not skip and n['t'] - 1e-3 <= t < n['t'] + n['d'] - 1e-3]
    for n in d['notes']:
        if n.get('label') or n['v'] not in 'SATB': continue
        if abs((n['t'] / spb) % 1) > 1e-3: continue
        others = sounding(n['t'], n)
        if not any((n['m'] - o['m']) % 12 in (1, 11) for o in others): continue
        bass = min([o['m'] for o in others] + [n['m']])
        for strict in (True, False):
            cand = [n['m'] + dm for dm in (-1, 1, -2, 2, -3, 3, -4, 4, -5, 5)
                    if not any((n['m'] + dm - o['m']) % 12 in (1, 2, 6, 10, 11) for o in others)
                    and (not strict or n['m'] + dm == bass or (n['m'] + dm - bass) % 12 in (0, 3, 4, 7, 8, 9))]
            if cand: n['m'] = cand[0]; fixed += 1; break
    # 連続 8 度・5 度: 自動の声部の 2 つ目の音を、そのとき鳴っている和音の別の音へ
    byv = {v: sorted([n for n in d['notes'] if n['v'] == v], key=lambda n: n['t']) for v in 'SATB'}
    def at(v, t): return next((n for n in byv[v] if abs(n['t'] - t) < 1e-3), None)
    pfix = 0
    for u, l in (('S', 'A'), ('S', 'T'), ('S', 'B'), ('A', 'T'), ('A', 'B'), ('T', 'B')):
        for a1, a2 in zip(byv[u], byv[u][1:]):
            b1, b2 = at(l, a1['t']), at(l, a2['t'])
            if not b1 or not b2 or a1['m'] == a2['m']: continue
            if (a1['m'] - b1['m']) % 12 != (a2['m'] - b2['m']) % 12 or (a1['m'] - b1['m']) % 12 not in (0, 7): continue
            mv = a2 if not a2.get('label') else (b2 if not b2.get('label') else None)
            if mv is None: continue
            others = sounding(mv['t'], mv); pcs = {o['m'] % 12 for o in others}
            prev = a1 if mv is a2 else b1; ref1 = b1 if mv is a2 else a1; ref2 = b2 if mv is a2 else a2
            for dm in (-1, 1, -2, 2, -3, 3, -4, 4, -5, 5):
                m2 = mv['m'] + dm
                if m2 % 12 not in pcs or any((m2 - o['m']) % 12 in (1, 11) for o in others): continue
                if (m2 - ref2['m']) % 12 in (0, 7) and (prev['m'] - ref1['m']) % 12 == (m2 - ref2['m']) % 12: continue
                mv['m'] = m2; pfix += 1; break
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('clash fixed:', fixed, 'parallels fixed:', pfix)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
