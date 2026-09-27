#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXXVIII · Intermezzi (ブラームスの間奏曲 + 坂本龍一の Intermezzo の雰囲気 + Sweet Revenge の雰囲気)
  録音 9 本: 9/24 08:49・08:53・11:18・11:21・11:23、9/25 12:46・12:50:36・12:50:53・13:04。
  ブラームス (公有) は書法をそのまま借り、坂本龍一の 2 曲は旋律を引用せず、響きと編成だけを参照する (Acceptance と同じ方針)。
    I.   Intermezzo (Brahms) — 変ホ短調 (Op. 118-6 と同じ調)。13:04 の実音 → 旋律は内声 (テノール) に置き、
         両手にまたがる幅の広い分散和音 (低音 + 3 音の上声が 8 分音符で 3 つずつ回る = 2 拍子の中の 3 のうねり、ブラームスのヘミオラ)。
         中間部は旋律がソプラノへ上がり、終わりは主題の拡大 (2 倍) とリタルダンド
    II.  Intermezzo (Sakamoto の雰囲気) — ヘ短調。12:46 の実音 (シンセの部分) → まばらなピアノ: 左手の低いオクターヴ、
         右手は 5 度・9 度・3 度の 4 音の繰り返し (add9 の響き)、長いペダル、シンセの実音の薄い持続音。旋律は 2 倍の長さで静かに
    III. Sweet Revenge (の雰囲気) — ロ短調、♩=76 のボサノヴァ: コントラバスのピッツィカート (根音 - 5 度)、ピアノのシンコペーションの
         和音 (3 度・7 度・9 度)、ブラシ (キックとスウィッシュだけ)、厚い弦、7 の和音 (m7・maj7・7)。旋律は 12:50 の 2 本と 11:18 の主題、2 回目は Vn I が重なる
    IV.  Sintesi — 3 つの融合 (変ホ短調): ブラームスの内声の旋律 (08:53) + 坂本の 4 音の繰り返し + ボサノヴァの低音とブラシ + 弦 + 11:21 のシンセの実音
    Coda — 13:04 の本当の終わり → add9 の和音が分散して消える
  使い方: python compose_tablet38.py <bank37.json> [score_tablet38.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 60; BAR_S = 240.0 / BPM
E1, E2, B2, RF, SY = '20260924_112313', '20260924_085314', '20260924_111846', '20260924_084937', '20260924_112131'
R1, R2, R3, R4 = '20260925_124643', '20260925_125053', '20260925_125036', '20260925_130431'
KEYS = {E1: 2, E2: 2, B2: -4, RF: 3, SY: 3, R1: 3, R2: -3, R3: -3, R4: 1}
T7.KEYS.update(KEYS)
ORDER = [R4, E1, R1, RF, R2, R3, B2, E2, SY]
SYN = 'VOXSY'
JAZZ = {'Dm': 'Dm7', 'Gm': 'Gm7', 'A': 'A7', 'A7': 'A7', 'F': 'Fmaj7', 'Bb': 'Bbmaj7', 'C': 'C7', 'Em7b5': 'Em7b5', 'Gm/Bb': 'Gm7', 'Dm/F': 'Dm7'}
ARPB, SAKA, BOSSA, STRG, BRUSH, VDBL, SPDBL = [], [], [], [], [], [], []

def pcs_in(c, lo, hi): return [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]

def post(P, events, extras):
    for b0, b1, gain, rid in ARPB:                  # ブラームス: 低音 + 3 音の上声が 8 分音符で回る (2 拍子の中の 3 のうねり)
        k = 0
        for bar in range(b0, b1):
            g = gain * P.dyn.get(bar, 1.0)
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); bass = 38 + (c['bass'] - 2) % 12
                add('PF', bar * BPB + half, 2.0, bass - (12 if bass > 45 else 0), g * 1.25, None, rid=rid, rel=1.6)
                up = pcs_in(c, 53, 70)[:3] or [bass + 12]
                for e in (0.5, 1.0, 1.5):
                    add('PF', bar * BPB + half + e, 0.9, up[k % len(up)], g * (0.95 if k % 3 == 0 else 0.75), None, rid=rid, rel=1.2); k += 1
    for b0, b1, gain, rid in SAKA:                  # 坂本の雰囲気: 左手の低いオクターヴ + 右手の 5・9・3・9 の繰り返し + シンセの薄い持続音
        for bar in range(b0, b1):
            c = chord(P.harm[bar * BPB]); r = c['root']; root = 26 + (r - 2) % 12
            add('PF', bar * BPB, 4.0, root, gain * 1.1, None, rid=rid, rel=2.5); add('PF', bar * BPB + 0.02, 4.0, root + 12, gain * 0.9, None, rid=rid, rel=2.5)
            base = 62 + (r - 2) % 12
            if base > 69: base -= 12
            fig = [base + 7, base + 14, base + 12 + (c['third'] - r) % 12, base + 14]
            for i_, m in enumerate(fig): add('PF', bar * BPB + i_, 1.6, m, gain * (0.85 if i_ else 0.95), None, rid=rid, rel=2.0)
            for j, m in enumerate(pcs_in(c, 50, 62)[:3]): add('SP', bar * BPB + 0.03 * j, 4.4, m, 0.08, None, rid=SYN, pan=(-0.2, 0.2, 0.0)[j])
    for b0, b1, gain, rid in BOSSA:                 # ボサノヴァ: Cb pizz (根音 - 5 度) + ピアノのシンコペーションの和音
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = 26 + (c['root'] - 2) % 12; f = r + 7
                add('CBP', bar * BPB + half, 1.4, r, gain * 0.32, None); add('CBP', bar * BPB + half + 1.5, 0.45, f if f <= 45 else f - 12, gain * 0.26, None)
            pat = ((0, 0.8), (1.5, 0.45), (3.0, 0.8)) if (bar - b0) % 2 == 0 else ((1.0, 0.45), (2.5, 0.8))
            for t, d in pat:
                c = chord(P.harm[bar * BPB + int(t)]); r = c['root']
                tones = [(r + (c['third'] - r) % 12), (c['seventh'] if c['seventh'] is not None else c['fifth']), (r + 2) % 12]
                vo = sorted(min((x for x in range(57, 72) if x % 12 == pc % 12), key=lambda x: abs(x - 64)) for pc in tones)
                for j, m in enumerate(vo): add('PF', bar * BPB + t + 0.008 * j, d, m, gain * 1.45, None, rid=rid, rel=0.5)
    for b0, b1, gain in STRG:                       # 厚い弦 (和音を全音符で)
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); tones = pcs_in(c, 50, 74)
                for iv, m in zip(('VC', 'VA', 'V2', 'V2'), [tones[0], tones[min(1, len(tones) - 1)], tones[min(2, len(tones) - 1)], tones[min(3, len(tones) - 1)]]):
                    add(iv, bar * BPB + half, 2.05, m, gain * P.dyn.get(bar, 1.0), None)
    for b0, b1, kick, swish in BRUSH:               # ブラシ: キック (1・3 拍)、スウィッシュ (2・4 拍と 4 拍の裏)
        for bar in range(b0, b1):
            for t in (0, 2): add('BR', bar * BPB + t, 0.3, 36, kick, None)
            for t, g in ((1, 1.0), (3, 1.0), (3.5, 0.55)):
                if swish > 0: add('BR', bar * BPB + t, 0.25, 38, swish * g, None, pan=-0.1)
    for b0, b1, gain in VDBL:                       # Vn I がソプラノの 1 オクターヴ上
        for s_, d, m, lab in events['S']:
            if b0 * BPB <= s_ < b1 * BPB: add('V1', s_, d * 1.05, m + 12, gain, None)
    for b0, b1, gain, v in SPDBL:                   # シンセの実音が旋律に重なる
        for s_, d, m, lab in events[v]:
            if b0 * BPB <= s_ < b1 * BPB: add('SP', s_, d * 0.95, m + 12, gain, None, rid=SYN, pan=0.15)

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def place(P, v, bar, mat_, tr, label):
    lo, hi = {'S': (60, 81), 'A': (55, 74), 'T': (48, 67), 'B': (36, 58)}[v]
    ms = [m for _, m in mat_ if m is not None]
    while max(ms) + tr > hi: tr -= 12
    while min(ms) + tr < lo: tr += 12
    P.place(v, bar, mat_, tr, label); return [(bar * BPB, [(d, None if m is None else m + tr) for d, m in mat_])]
def harm_of(P, b, mat_, jazz=False):
    H = CT.harmonize(mat_) if sum(d for d, _ in mat_) == 8 else None
    if H is None: return
    if jazz: H = [[JAZZ.get(c, c) for c in bar] for bar in H]
    P.set_harms(b, H)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], 60); T5.SUBJ[r] = (s_, CT.harmonize(s_))
    end4 = REC[R4]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(R4, []).append((end4, REC[R4]['dur']))
    total = 6 + 16 + 5 + 12 + 4 + 16 + 10 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.0
    b = 0
    def excerpt(rid, bars, title, sub, t0=None, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, t0=t0, bpm=BPM, gmul=0.6)
        for v in VOICES: P.rest_bars(v, b, b + bars)
        for k in range(bars): P.dyn[b + k] = 0.5
        CT.LAYOUT.append((b, b + bars, KEYS[rid], {v: rid for v in VOICES}, {})); b += bars
    # ================= I. Intermezzo (Brahms) — 変ホ短調
    excerpt(R4, 6, 'I. Intermezzo — %s の実音 (変ホ短調)' % hm(R4), 'ブラームスの間奏曲 Op. 118-6 と同じ変ホ短調の録音から始める')
    f = b; E = []
    P.section(b, 'I. Intermezzo (Brahms) — 内声の旋律と幅の広い分散和音', '旋律はテノール (内声)、両手にまたがる分散和音が 8 分音符で 3 つずつ回る (2 拍子の中の 3 のうねり) — 中間部はソプラノへ、終わりは主題の拡大とリタルダンド')
    for k, (bar, r) in enumerate(((0, R4), (2, R4), (4, E1), (6, E1))):
        E += place(P, 'T', f + bar, subj(r), 0, '旋律 (%s) · 内声' % hm(r) if k in (0, 2) else None); harm_of(P, f + bar, subj(r))
    E += place(P, 'S', f + 8, subj(R4), 12, '旋律 (%s) · ソプラノへ' % hm(R4)); harm_of(P, f + 8, subj(R4))
    E += place(P, 'S', f + 10, subj(E1), 12, None); harm_of(P, f + 10, subj(E1))
    E += place(P, 'T', f + 12, aug(subj(R4)), 0, '旋律の拡大 (2 倍)')
    T5.harm_from_entries(P, f + 12, f + 16, E[-1:])
    for q in range(BPB): P.harm[(f + 15) * BPB + q] = 'Dm'
    for v in ('S', 'A'): P.rest_bars(v, f, f + 8); P.rest_bars(v, f + 12, f + 16)
    P.rest_bars('A', f + 8, f + 12); P.rest_bars('T', f + 8, f + 12)
    for k in range(16): P.dyn[f + k] = 0.9 + (0.1 if 8 <= k < 12 else 0)
    for k, tp in enumerate((58, 56, 54, 50)): P.tempo[f + 12 + k] = tp
    ARPB.append((f, f + 16, 0.26, R4))
    CT.LAYOUT.append((f, f + 16, 1, {'S': R4, 'A': R4, 'T': R4, 'B': E1}, {})); b = f + 16
    # ================= II. Intermezzo (Sakamoto の雰囲気) — ヘ短調
    excerpt(R1, 5, 'II. Intermezzo — %s の実音 (ヘ短調)' % hm(R1), '12:46 の途中、シンセサイザーが鳴っている実音')
    f = b; E = []
    P.section(b, 'II. Intermezzo (坂本龍一の雰囲気) — まばらなピアノ', '左手の低いオクターヴ、右手は 5 度・9 度・3 度の 4 音の繰り返し (add9 の響き)、長いペダルとシンセの薄い持続音 — 旋律は 2 倍の長さで静かに (旋律の引用はしない)')
    P.set_harms(f, [['Dm'], ['Bbmaj7'], ['Gm7'], ['A7'], ['Dm'], ['Bbmaj7'], ['F'], ['C'], ['Gm7'], ['Bbmaj7'], ['A7'], ['Dm']])
    E += place(P, 'S', f + 1, aug(subj(R1)), 12, '旋律 (%s) · 2 倍' % hm(R1))
    E += place(P, 'S', f + 6, aug(subj(RF)), 12, '旋律 (%s) · 2 倍' % hm(RF))
    for v in ('A', 'T', 'B'): P.rest_bars(v, f, f + 12)
    P.rest_bars('S', f, f + 1); P.rest_bars('S', f + 5, f + 6); P.rest_bars('S', f + 10, f + 12)
    P.hold.update(range(f, f + 12))
    for k in range(12): P.tempo[f + k] = 56; P.dyn[f + k] = 1.7
    SAKA.append((f, f + 12, 0.36, R1))
    CT.LAYOUT.append((f, f + 12, 3, {'S': R1, 'A': R1, 'T': R1, 'B': R1}, {})); b = f + 12
    # ================= III. Sweet Revenge (の雰囲気) — ロ短調のボサノヴァ
    excerpt(R2, 4, 'III. Sweet Revenge — %s の実音 (ロ短調)' % hm(R2), '12:50 の実音からボサノヴァへ')
    f = b; E = []
    P.section(b, 'III. Sweet Revenge (の雰囲気) — ♩=76 のボサノヴァ', 'Cb pizz (根音 - 5 度)、ピアノのシンコペーションの和音 (3・7・9 度)、ブラシ、厚い弦、7 の和音 — 旋律は 12:50 の 2 本と 11:18 の主題')
    for k, r in enumerate((R3, R2, B2, R3, R2, B2, R3, R2)):
        E += place(P, 'S', f + 2 * k, subj(r), 0, '旋律 (%s)' % hm(r) if k < 3 else None); harm_of(P, f + 2 * k, subj(r), jazz=True)
    for v in ('A', 'T', 'B'): P.rest_bars(v, f, f + 16)
    for k in range(16): P.tempo[f + k] = 76; P.dyn[f + k] = 1.6
    BOSSA.append((f, f + 16, 0.16, R2)); STRG.append((f + 4, f + 16, 0.02)); BRUSH.append((f, f + 16, 0.1, 0.045)); VDBL.append((f + 8, f + 16, 0.08))
    CT.LAYOUT.append((f, f + 16, -3, {'S': R2, 'A': R2, 'T': R2, 'B': R2}, {})); b = f + 16
    # ================= IV. Sintesi — 3 つの融合 (変ホ短調)
    f = b; E = []
    P.section(b, 'IV. Sintesi — ブラームス + 坂本 + Sweet Revenge (変ホ短調)', 'ブラームスの内声の旋律 (08:53) に、坂本の 4 音の繰り返し、ボサノヴァの低音とブラシ、弦、11:21 のシンセの実音が重なる')
    for k, (v, r) in enumerate((('T', E2), ('T', E2), ('S', SY), ('T', E2))):
        E += place(P, v, f + 2 * k, subj(r), 12 if v == 'S' else 0, '旋律 (%s)' % hm(r) if k in (0, 2) else None); harm_of(P, f + 2 * k, subj(r), jazz=True)
    E += place(P, 'T', f + 8, aug(subj(E2), 1), 0, None)
    P.set_harms(f + 8, [['Gm7', 'Gm7', 'A7', 'A7'], ['Dm']])
    P.rest_bars('S', f, f + 4); P.rest_bars('S', f + 6, f + 10); P.rest_bars('A', f, f + 10)
    for k in range(10): P.tempo[f + k] = 66; P.dyn[f + k] = 1.0
    for k, tp in enumerate((60, 54)): P.tempo[f + 8 + k] = tp
    SAKA.append((f, f + 8, 0.2, E2)); BOSSA.append((f, f + 8, 0.1, E2)); STRG.append((f, f + 10, 0.03)); BRUSH.append((f, f + 8, 0.08, 0.0)); SPDBL.append((f + 4, f + 6, 0.08, 'S'))
    CT.LAYOUT.append((f, f + 10, 1, {'S': SY, 'A': E2, 'T': E2, 'B': E2}, {})); b = f + 10
    # ================= Coda
    excerpt(R4, 5, 'Coda — %s の本当の終わり' % hm(R4), '13:04 の最後 (実音) → add9 の和音が分散して消える', t0=end4, fout=2.5)
    P.set_harms(b, [['Dm']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k, m in enumerate((26, 38, 45, 52, 53, 57, 64, 69)): add('PF', b * BPB + 0.35 * k, 8.0, m, 0.2 if k < 2 else 0.15, None, rid=R4, rel=3.5)
    for k in range(3): P.tempo[b + k] = 50
    CT.LAYOUT.append((b, b + 3, 1, {v: R4 for v in VOICES}, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER + [SYN], 'piano_decay': 1.8, 'src_name': {SYN: 'シンセの実音'},
    'title': 'Requiem BADA — Tablet Sessions XXXVIII · Intermezzi',
    'subtitle': 'ブラームスの間奏曲 + 坂本龍一の Intermezzo の雰囲気 + Sweet Revenge の雰囲気 — 9/24・9/25 の 9 本の録音から',
    'legend': ['TB', 'PF', 'SP', 'CBP', 'V1', 'BR'], 'vname': {'PF': 'ピアノ伴奏', 'SP': 'シンセ', 'CBP': 'Cb pizz', 'V1': '弦', 'BR': 'ブラシ'},
    'footer': ['I. Intermezzo (Brahms, 変ホ短調) → II. Intermezzo (坂本の雰囲気, ヘ短調) → III. Sweet Revenge (の雰囲気, ボサノヴァ, ロ短調) → IV. Sintesi → Coda 13:04',
               'ブラームスは書法を借り、坂本龍一の 2 曲は旋律を引用せず響きと編成だけを参照。音は 9 本の録音の実音と、そこから切り出したピアノとシンセの音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet38.json'
    compose.main(out, seed=138, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
