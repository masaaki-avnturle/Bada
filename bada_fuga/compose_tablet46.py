#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLVI · Requiem in fuga (歌の旋律がフーガでありながらレクイエム — 20 代の女性のきれいな声で歌う)
  録音 5 本 (9/24): 08:49 (ヘ短調)、08:53 (ホ短調)、11:18 (変ロ短調)、11:21 (ヘ短調)、11:23 (ホ短調)。
  歌: 2026/9/28 17:46 のわたしの声の響き (voice_templates.py) を、若い女性の声に書き換えて歌う (sing_user.py):
  響きを周波数の方向に 1.18 倍 (声道を短く)、ソプラノとアルトの声域、2.5 kHz より上に軽い息 (透きとおった声)、少し速く浅いビブラート。
  歌の旋律がフーガ: 主題が入るたびに、その声部 (ソプラノ・アルト) が同じ歌詞を歌う (モーツァルトのレクイエムの Kyrie のフーガと同じ作り方)。
  テノール・バスの入りはピアノの実音と弦。歌詞はレクイエムの祈りの言葉をもとに書いたオリジナルの日本語 (lyrics_tablet.py の tablet46)。
  形式 (♩=60):
    Introitus               — 08:49 の実音 (ヘ短調) に弦
    Requiem aeternam — Fuga I (ホ短調) — 08:53 の主題の 4 声フーガ 16 小節、ソプラノとアルトの入りを歌う
    Kyrie — コラール        — 11:23・08:53 の主題を 2 倍の長さで歌い、ピアノの 4 声と弦が支える
    Lacrimosa               — 11:18 の実音 (変ロ短調)
    Lux aeterna — Fuga II (ヘ短調) — 11:21 の主題のフーガ、最後はストレッタで 2 声が重なる
    In paradisum — コラール — 08:49 の主題を 2 倍で歌い、ヘ長調の和音で → 08:49 の本当の終わり
  使い方: python compose_tablet46.py <bank37.json> [score_tablet46.json]  (歌は add_vocals.py tablet46 ... voice.npz で入れる)
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
BPM = 60; BAR_S = 240.0 / BPM
B1, B2, B3, B4, B5 = '20260924_084937', '20260924_085314', '20260924_111846', '20260924_112131', '20260924_112313'
KEYS = {B1: 3, B2: 2, B3: -4, B4: 3, B5: 2}
T7.KEYS.update(KEYS)
ORDER = [B2, B5, B4, B1, B3]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤')))
VOICE_SRC = {'S': B4, 'A': B2, 'T': B1, 'B': B5}
DYNK = 1.3
PFA, STRG, LOWS, DRUM = [], [], [], []
def dk(P, bar): return P.dyn.get(bar, DYNK) / DYNK
def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
def low_root(c, lo=36): return lo + (c['root'] - lo) % 12

def post(P, events, extras):
    for b0, b1, gain, rid in PFA:                  # バラードのピアノ (ピアノの実音): 8 分の分散和音 — 根音・5 度・オクターヴ・3 度・5 度…
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c, 38); th = (c['third'] - c['root']) % 12
                for k, m in enumerate((r, r + 7, r + 12, r + 12 + th)):
                    add('PF', bar * BPB + half + 0.5 * k, 1.6 - 0.3 * k, m, gain * dk(P, bar) * (1.0 if k == 0 else 0.72), None, rid=rid, rel=0.8, pan=-0.1)
    for b0, b1, gain in STRG:                      # 弦 (和音を全音符で、やわらかく)
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB]); tones = pcs_in(c, 52, 74)
            for iv, m in zip(('VA', 'V2', 'V1'), [tones[0], tones[min(1, len(tones) - 1)], tones[min(2, len(tones) - 1)]]):
                add(iv, bar * BPB, 4.05, m, gain * dk(P, bar), None)
    for b0, b1, gain in LOWS:                      # チェロとコントラバス: 根音を全音符で
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = low_root(c, 36)
                add('VC', bar * BPB + half, 2.05, r + 12, gain * dk(P, bar), None); add('CB', bar * BPB + half, 2.05, r, gain * 0.8 * dk(P, bar), None)
    for b0, b1, lvl in DRUM:                       # やわらかいドラム (バラードのハーフタイム)
        for bar in range(b0, b1):
            add('DR', bar * BPB, 0.3, 36, lvl, None, kind='kick'); add('DR', bar * BPB + 2.5, 0.3, 36, lvl * 0.6, None, kind='kick')
            add('DR', bar * BPB + 2, 0.3, 38, lvl * 0.5, None, kind='snare', pan=0.05)
            for k in range(4): add('DR', bar * BPB + k, 0.1, 42, lvl * 0.07, None, kind='hatc', pan=0.25)

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def place(P, bar, mat_, label):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > 77: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)
def harm_of(P, b, mat_): P.set_harms(b, CT.harmonize(mat_))
def harm_aug(P, b, r):
    rows = []
    for row in CT.harmonize(subj(r)):
        row = row * 4 if len(row) == 1 else row
        rows += [[row[0], row[0], row[1], row[1]], [row[2], row[2], row[3], row[3]]]
    P.set_harms(b, rows)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], 60); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    end1 = REC[B1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(B1, []).append((end1, REC[B1]['dur']))
    total = 6 + 16 + 8 + 5 + 16 + 4 + 5 + 2
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
    def chorale(f, subs):                            # コラール: 主題を 2 倍の長さで S が歌い、A・T・B (ピアノの実音) が和声を支える
        for k, r in enumerate(subs):
            place(P, f + 4 * k, aug(subj(r)), 'コラール (%s) · 2 倍' % hm(r))
            T5.harm_from_entries(P, f + 4 * k, f + 4 * k + 4, [((f + 4 * k) * BPB, aug(subj(r)))])
    # ================= Introitus
    excerpt(B1, 6, 'Introitus — %s の実音 (ヘ短調)' % hm(B1), '08:49 の録音に、弦とチェロがそっと寄り添う', 3)
    STRG.append((b - 4, b, 0.022)); LOWS.append((b - 4, b, 0.025))
    # ================= Requiem aeternam — Fuga I
    f = section('Requiem aeternam — Fuga I (ホ短調)', '%s の主題の 4 声フーガ — 主題が入るたびに、ソプラノとアルトの女声が同じ祈りを歌う' % hm(B2), 16, 2)
    n_ = T11.bach_fugue(P, f, B2, '①')
    for k in range(n_): P.dyn[f + k] = DYNK * 0.72
    LOWS.append((f + 4, f + 16, 0.018)); STRG.append((f + 12, f + 16, 0.018))
    # ================= Kyrie — コラール
    f = section('Kyrie — コラール (ホ短調)', '%s・%s の主題を 2 倍の長さで女声が歌い、ピアノの 4 声と弦が支える' % (hm(B5), hm(B2)), 8, 2)
    chorale(f, [B5, B2]); STRG.append((f, f + 8, 0.025)); LOWS.append((f, f + 8, 0.025))
    for k in range(8): P.dyn[f + k] = DYNK * 0.7
    # ================= Lacrimosa
    excerpt(B3, 5, 'Lacrimosa — %s の実音 (変ロ短調)' % hm(B3), '11:18 の録音に、弦がそっと寄り添う', -4)
    STRG.append((b - 3, b, 0.022)); LOWS.append((b - 3, b, 0.022))
    # ================= Lux aeterna — Fuga II
    f = section('Lux aeterna — Fuga II (ヘ短調)', '%s の主題のフーガ — 最後はストレッタで女声の 2 声が重なる' % hm(B4), 16, 3)
    n_ = T11.bach_fugue(P, f, B4, '②')
    for k in range(n_): P.dyn[f + k] = DYNK * 0.72
    LOWS.append((f + 4, f + 16, 0.018)); STRG.append((f + 12, f + 16, 0.02))
    # ================= In paradisum — コラール
    f = section('In paradisum — コラール (ヘ短調 → ヘ長調)', '%s の主題を 2 倍の長さで女声が歌い、ピアノの 4 声と弦 — 最後はヘ長調の和音' % hm(B1), 4, 3)
    chorale(f, [B1]); STRG.append((f, f + 4, 0.03)); LOWS.append((f, f + 4, 0.028))
    for k in range(4): P.dyn[f + k] = DYNK * 0.72
    excerpt(B1, 5, 'In paradisum — %s の本当の終わり' % hm(B1), '08:49 の最後の実音に、弦とチェロが寄り添って消える', 3, t0=end1, fout=2.5)
    STRG.append((b - 5, b - 2, 0.02)); LOWS.append((b - 5, b - 2, 0.02))
    f = section('Fine', 'ヘ長調の和音 (ピカルディ終止)', 2, 3, B1)
    P.set_harms(f, [['D']] * 2)
    for v in VOICES: P.rest_bars(v, f, f + 2)
    for k, m in enumerate((38, 45, 50, 54, 57, 62)): add('PF', f * BPB + 0.3 * k, 7.0, m, 0.13 if k else 0.16, None, rid=B4, rel=3.0)
    for iv, m in (('VC', 50), ('VA', 57), ('V2', 62), ('V1', 66)): add(iv, f * BPB, 7.0, m, 0.03, None)
    add('CB', f * BPB, 7.0, 38, 0.03, None)
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.8,
    'title': 'Requiem BADA — Tablet Sessions XLVI · Requiem in fuga',
    'subtitle': '歌の旋律がフーガのレクイエム — 9/24 の 5 本と、わたしの声から書き換えた 20 代の女性の声 (♩=60)',
    'legend': ['TB', 'V1', 'VC', 'PF'], 'vname': {'V1': '弦', 'VC': 'チェロ', 'PF': 'ピアノ'},
    'footer': ['Introitus 08:49 → Requiem aeternam (Fuga I, 08:53) → Kyrie (コラール) → Lacrimosa 11:18 → Lux aeterna (Fuga II, 11:21) → In paradisum → 08:49',
               '歌: 主題が入るたびにソプラノ・アルトの女声が歌う (声は 9/28 のわたしの声の響きを若い女性の声に書き換えたもの)。歌詞はオリジナル。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet46.json'
    compose.main(out, seed=146, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    # 拍の頭で置いた主題と半音 (短 2 度・長 7 度) でぶつかる自動の声部の音を、ぶつからない近くの協和音へ動かす
    spb = 60.0 / BPM; fixed = 0
    def sounding(t, skip): return [n for n in d['notes'] if n is not skip and n['t'] - 1e-3 <= t < n['t'] + n['d'] - 1e-3]
    for n in d['notes']:
        if n.get('label') or n['v'] not in 'SATB': continue
        if abs((n['t'] / spb) % 1) > 1e-3: continue
        others = sounding(n['t'], n)
        if not any((n['m'] - o['m']) % 12 in (1, 11) for o in others): continue
        bass = min([o['m'] for o in others] + [n['m']])
        for strict in (True, False):                               # 見つからなければ低音との協和の条件を外して
            cand = [n['m'] + dm for dm in (-1, 1, -2, 2, -3, 3, -4, 4, -5, 5)
                    if not any((n['m'] + dm - o['m']) % 12 in (1, 2, 6, 10, 11) for o in others)
                    and (not strict or n['m'] + dm == bass or (n['m'] + dm - bass) % 12 in (0, 3, 4, 7, 8, 9))]
            if cand: n['m'] = cand[0]; fixed += 1; break
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('clash fixed:', fixed)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
