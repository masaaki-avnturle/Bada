#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLVII · Aria di cattedrale (XLVI を、キリスト教の大聖堂の賛美歌のアリアに — 19 歳の淑女の英語の歌声)
  録音 5 本 (9/24): 08:49 (ヘ短調)、08:53 (ホ短調)、11:18 (変ロ短調)、11:21 (ヘ短調)、11:23 (ホ短調)。
  歌: 2026/9/28 17:46 のわたしの声の響きを、19 歳の淑女の声に書き換えて英語で歌う (響き 1.24 倍、軽い息、ビブラート 0.42 半音)。
  大聖堂: 4 声はパイプオルガン (8' プリンシパル + 4' + 2⅔' + 2'、低音は 16')、長く深い響き (7 秒、減衰 2.4 秒)、歌声も響きへ多く送る。
  賛美歌のアリア: オルガンがまず賛美歌の旋律を弾き (前奏)、ソプラノの独唱が 3 つの節を歌う。節の間にオルガンのフーガ (提示)、
  最後の節は半音上へ、そして「Amen」(変格終止 iv → I、長調の和音で)。旋律は 9/24 の主題を 2 倍の長さに (賛美歌のゆったりした歩み)。
  歌詞はこの曲のために書いたオリジナルの英語の賛美歌 (lyrics_tablet.py の tablet47)。
  形式 (♩=56): Introitus (08:49 の実音) → Organ prelude (ホ短調) → Verse 1 → Verse 2 → Organ fugue (提示) → Verse 3 (ヘ短調) → Amen (ヘ長調)
  使い方: python compose_tablet47.py <bank37.json> [score_tablet47.json]  (歌は add_vocals.py tablet47 ... voice.npz で入れる)
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
    total = 4 + 4 + 8 + 8 + 8 + 8 + 3
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
    def hymn(f, subs, lab='賛美歌'):                 # 賛美歌: 主題を 2 倍の長さで S が歌い (旋律)、A・T・B (オルガン) が和声を支える
        for k, r in enumerate(subs):
            place(P, f + 4 * k, aug(subj(r)), '%s (%s) · 2 倍' % (lab, hm(r)))
            T5.harm_from_entries(P, f + 4 * k, f + 4 * k + 4, [((f + 4 * k) * BPB, aug(subj(r)))])
    # ================= Introitus
    excerpt(B1, 4, 'Introitus — %s の実音 (ヘ短調)' % hm(B1), '大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', 3)
    STRG.append((b - 2, b, 0.02))
    # ================= Organ prelude
    f = section('Organ prelude — オルガンが賛美歌の旋律を (ホ短調)', '%s の主題を 2 倍の長さで、パイプオルガンの 4 声が先に弾く' % hm(B2), 4, 2)
    hymn(f, [B2], 'オルガン')
    for k in range(4): P.dyn[f + k] = DYNK * 0.95
    # ================= Verse 1 / Verse 2
    f = section('Verse 1 — アリア (ホ短調)', '19 歳の淑女の独唱、パイプオルガンの 4 声が支える', 8, 2)
    hymn(f, [B2, B5])
    for k in range(8): P.dyn[f + k] = DYNK * 0.75
    f = section('Verse 2 — アリア (ホ短調)', '独唱とオルガン — 5 小節目から弦がそっと加わる', 8, 2)
    hymn(f, [B4, B1]); STRG.append((f + 4, f + 8, 0.02))
    for k in range(8): P.dyn[f + k] = DYNK * 0.75
    # ================= Organ fugue (提示)
    f = section('Organ fugue — %s の主題の提示 (ヘ短調)' % hm(B4), 'オルガンの 4 声が次々と主題を弾く (アルト → ソプラノ → バス → テノール)', 8, 3)
    T5.expo(P, f, B4, '②')
    for k in range(8): P.dyn[f + k] = DYNK * 1.08
    # ================= Verse 3 (半音上)
    f = section('Verse 3 — アリア (ヘ短調)', '半音上へ — 独唱、オルガン、弦がいちばん厚く', 8, 3)
    hymn(f, [B2, B5]); STRG.append((f, f + 8, 0.03)); LOWS.append((f, f + 8, 0.02))
    for k in range(8): P.dyn[f + k] = DYNK * 0.7
    # ================= Amen (変格終止 → ヘ長調)
    f = section('Amen — 変格終止 (ヘ長調の和音で)', 'iv → I: 独唱が「Amen」を長く歌い、オルガンと弦が長調の和音で包む', 3, 3)
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    STRG.append((f, f + 3, 0.03)); LOWS.append((f, f + 3, 0.025))
    for k in range(3): P.dyn[f + k] = DYNK * 0.8
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.8, 'choir': 'organ', 'organ_gain': 0.5,
    'reverb': [7.0, 2.4, 0.5], 'vo_send': 0.5,
    'title': 'Requiem BADA — XLVII · Aria di cattedrale',
    'subtitle': '大聖堂の賛美歌のアリア — パイプオルガンと、わたしの声から書き換えた 19 歳の淑女の英語の歌声 (♩=56)',
    'legend': ['TB', 'V1', 'VC'], 'vname': {'V1': '弦', 'VC': 'チェロ'},
    'footer': ['Introitus 08:49 → Organ prelude → Verse 1 (ホ短調) → Verse 2 → Organ fugue (11:21) → Verse 3 (ヘ短調) → Amen (ヘ長調)',
               '4 声はパイプオルガン、大聖堂の長い響き。歌は 9/28 のわたしの声の響きを 19 歳の淑女の声に書き換えたもの。歌詞はオリジナルの英語の賛美歌。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet47.json'
    compose.main(out, seed=147, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
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
    # 連続 8 度・5 度 (オルガンでは目立つ): 自動の声部の 2 つ目の音を、そのとき鳴っている和音の別の音へ動かす
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
            others = [n for n in sounding(mv['t'], mv)]
            pcs = {o['m'] % 12 for o in others}
            prev = a1 if mv is a2 else b1; ref1 = b1 if mv is a2 else a1; ref2 = b2 if mv is a2 else a2
            for dm in (-1, 1, -2, 2, -3, 3, -4, 4, -5, 5):
                m2 = mv['m'] + dm
                if m2 % 12 not in pcs: continue
                if any((m2 - o['m']) % 12 in (1, 11) for o in others): continue
                if (m2 - ref2['m']) % 12 in (0, 7) and (prev['m'] - ref1['m']) % 12 == (m2 - ref2['m']) % 12: continue
                mv['m'] = m2; pfix += 1; break
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('clash fixed:', fixed, 'parallels fixed:', pfix)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
