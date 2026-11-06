#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLIX · Melodia sola al pianoforte (MOTHER・LOVELESS・トラック 8 から、グランドピアノで、メロディーだけ取り上げて合成)
  MOTHER と LOVELESS (LUNA SEA、1994) の旋律は **採譜して使わない** (著作権のある楽曲の旋律の再現になるので) — 2 曲からは採譜で読んだ調 (ト長調〜ホ短調)、テンポ (♩≈68)、和音の輪 (MOTHER: G → D/F# → Em7 → Cmaj7 / LOVELESS: Em7 → Cmaj7 → G → D7、サビ G → D7 → Em7 → C) と、バラードの形式 (序 → 1 番 → 間奏 → 2 番 → 終わり) だけを借りる
  旋律 = トラック 8 (録音、249 秒) の最上声を採譜したもの全部 (8 分音符に量子化、ハ長調 / イ短調 → 4 度下げてト長調 / ホ短調に)。和音もトラック 8 の採譜を 4 度下げて
  **グランドピアノだけ** (合成のグランドピアノ、録音は鳴らさない): 右手 = 旋律、左手 = 根音 (2 分音符) と分散和音 (8 分音符)。2 番は旋律が 1 オクターヴ上で、アルトに 2 小節遅れのカノン (1 オクターヴ下) — 1 つの旋律でフーガを醸す。高い共鳴 (H) と低いペダル (L) も同じピアノ
  使い方: python compose_tablet159.py <bank150.json (トラック 8 の採譜)> [score_tablet159.json]
"""
import sys, os, json, math
BANKP = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet159.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RECS = json.load(open(BANKP))['recordings']; R08 = '20261107_080000'
BPM = 68; SM = -5                                                                                   # ハ長調 / イ短調 → ト長調 / ホ短調 (4 度下げる)
LOOP_M = ['G', 'D/F#', 'Em7', 'Cmaj7']; LOOP_A = ['Em7', 'Cmaj7', 'G', 'D7']; LOOP_S = ['G', 'D7', 'Em7', 'C']

def melody(segs, lo=55):
    """トラック 8 の採譜の最上声 → 旋律 (拍単位、8 分音符に量子化、4 度下げて)。オクターヴの跳びは下の音に寄せる"""
    spb = 60.0 / BPM; out = []; prev = None
    for s in segs:
        cand = [m for m in s['m'] if m >= lo]
        if not cand: continue
        top = max(cand)
        if prev is not None and top - prev > 9:
            near = [m for m in cand if m <= prev + 7]
            if near: top = max(near)
        t = round(s['t'] / spb * 2) / 2.0
        if out and t < out[-1][0] + 0.5: t = out[-1][0] + 0.5
        if out and out[-1][2] == top and t - (out[-1][0] + out[-1][1]) < 0.01: out[-1][1] += max(0.5, round(s['d'] / spb * 2) / 2.0); continue
        if out: out[-1][1] = min(out[-1][1], t - out[-1][0])
        out.append([t, max(0.5, round(s['d'] / spb * 2) / 2.0), top]); prev = top
    res = []
    for t, d, m in out:
        m += SM
        while m > 84: m -= 12
        while m < 55: m += 12
        res.append((t, d, m))
    return res
MEL = melody(RECS[R08]['segs'])
MEL_BEATS = int(math.ceil((MEL[-1][0] + MEL[-1][1]) / BPB)) * BPB; MEL_BARS = MEL_BEATS // BPB          # 70〜72 小節
def mel_mat(oct_=0):
    """旋律を place 用の (長さ, 音) の列に (休みは None)"""
    mat = []; t = 0.0
    for t0, d, m in MEL:
        if t0 > t: mat.append((t0 - t, None)); t = t0
        m += oct_
        if m > 91: m -= 12
        if m < 43: m += 12
        mat.append((d, m)); t += d
    return mat
def harm08(q):
    """トラック 8 の q 拍目の和音 (4 度下げて)"""
    spb = 60.0 / BPM; sec = q * spb; cur = RECS[R08]['segs'][0]['ch']
    for s in RECS[R08]['segs']:
        if s['t'] <= sec: cur = s['ch']
    return transpose_h([[cur]], SM)[0][0]
INTRO, I, INTER, II, CODA, TOTAL = 0, 12, 12 + MEL_BARS, 12 + MEL_BARS + 16, 12 + 2 * MEL_BARS + 16, 12 + 2 * MEL_BARS + 16 + 18
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def free(P, v, b0, b1):
    for b in range(b0, b1): P.rest[v].difference_update(range(b * BPB, b * BPB + BPB))
def sec_of(b): return 'intro' if b < I else 'I' if b < INTER else 'inter' if b < II else 'II' if b < CODA else 'coda'

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB):
        b = q // BPB; s = sec_of(b)
        if s == 'I': h = harm08(q - I * BPB)
        elif s == 'II': h = harm08(q - II * BPB)
        elif s == 'intro': h = LOOP_M[(b - INTRO) % 4]
        elif s == 'inter': h = (LOOP_A if b < INTER + 8 else LOOP_S)[(b - INTER) % 4]
        else: h = LOOP_M[(b - CODA) % 4] if b < TOTAL - 2 else 'G'
        P.harm[q] = h
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.35 if k < I else min(0.7, 0.45 + 0.004 * (k - I)) if k < INTER else 0.5 if k < II else (min(0.95, 0.6 + 0.012 * (k - II)) if k < II + 40 else 0.85) if k < CODA else max(0.1, 0.5 - 0.025 * (k - CODA))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    def put(v, b, mat, label=None):
        t = b * BPB
        for d, m in mat:
            if m is not None: P.rest[v].difference_update(range(int(math.floor(t)), min(TOTAL * BPB, int(math.ceil(t + d - 1e-9)))))
            t += d
        P.place(v, b, mat, 0, label)
    P.section(INTRO, '序 — 左手の分散和音 (ト長調 / ホ短調, ♩=68)', 'グランドピアノだけ。MOTHER の採譜から読んだ和音の輪 G → D/F# → Em7 → Cmaj7 (バスが下る) を左手の分散和音で pp、高い開いた 5 度が反響')
    P.section(I, '1 番 — トラック 8 の旋律 (右手)', 'トラック 8 の最上声を採譜した旋律の全部 (4 度下げてト長調 / ホ短調に)、左手は根音 (2 分音符) と分散和音 (8 分音符)。和音もトラック 8 の採譜')
    put('S', I, mel_mat(0), 'トラック 8 の旋律 (採譜、4 度下げて)')
    P.section(INTER, '間奏 — LOVELESS の輪', 'LOVELESS の採譜から読んだ和音の輪 Em7 → Cmaj7 → G → D7、続いてサビの輪 G → D7 → Em7 → C。旋律の最初の句をテノールで')
    first = [(d, m) for d, m in mel_mat(-12)][:40]
    put('T', INTER + 1, first, '旋律の最初の句 (テノール、1 オクターヴ下)')
    P.section(II, '2 番 — 旋律が 1 オクターヴ上、アルトにカノン', '旋律が 1 オクターヴ上で (頂点へ)、アルトが 2 小節遅れて 1 オクターヴ下でカノン — 1 つの旋律でフーガを醸す。左手は分散和音を 2 倍に')
    put('S', II, mel_mat(12), '旋律 (1 オクターヴ上)')
    put('A', II + 2, [(d, m) for d, m in mel_mat(-12)][:int(len(MEL) * 0.85)], 'カノン (2 小節遅れ、1 オクターヴ下)')
    P.section(CODA, '終わり — MOTHER の輪', '旋律の終わりの句を 2 倍に伸ばして、左手の分散和音と高い共鳴だけが残って消える')
    tail = [(d * 2, m) for d, m in mel_mat(0) if m is not None][-10:]
    put('S', CODA + 2, tail, '旋律の終わりの句 (2 倍に伸ばして)')
    # 左手: 根音 (2 分音符、B) と分散和音 (8 分音符、T) — 間奏はテノールが旋律なので分散和音はアルトで
    first_lab = True
    for b in range(1, TOTAL - 2):
        s = sec_of(b)
        if s == 'coda' and b >= TOTAL - 4: break
        h = P.harm[b * BPB]; c = chord(h); r = 36 + c['root']
        if r > 43: r -= 12
        bass_lo = 31 if s == 'II' else 36
        free(P, 'B', b, b + 1); P.place('B', b, [(2, r if r >= bass_lo else r + 12), (2, r + 7 if s in ('II',) else r)], 0, '左手の根音 (2 分音符)' if b == 1 else None)
        if s == 'inter' and b < INTER + 11: v = 'A'
        else: v = 'T'
        if s == 'II' and b < CODA: lo, hi = 43, 57
        else: lo, hi = 48, 62
        t3 = tones_of(h, lo, hi); pat = [t3[0], t3[-1], t3[0] + 12 if t3[0] + 12 < hi + 4 else t3[1], t3[-1], t3[1], t3[-1], t3[0] + 12 if t3[0] + 12 < hi + 4 else t3[1], t3[1]] if len(t3) >= 2 else [t3[0]] * 8
        if s == 'intro' or s == 'coda': pat = [t3[0], t3[1 % len(t3)], t3[-1], t3[1 % len(t3)]] * 2
        free(P, v, b, b + 1)
        for k, m in enumerate(pat): P.place(v, b, [(0.5, m)], 0, ('左手の分散和音 (8 分音符)' if first_lab else None), beat=k * 0.5); first_lab = False
    return P

def post(P, events, ex):
    first = True
    for b in list(range(INTRO + 2, I, 4)) + list(range(CODA, TOTAL - 4, 4)):
        add('H', b * BPB, 4 * BPB + 0.5, 86, 0.1, '高い開いた 5 度 (共鳴)' if first else None); add('H', b * BPB + 0.05, 4 * BPB + 0.5, 81, 0.08); first = False
    first = True
    for b in range(II, CODA - 2, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.16 * P.dyn.get(b, 0.8) / 0.8, '低いペダルの音 (2 小節ごと)' if first else None); first = False
    # 2 番の頂点: 旋律の反響 (H、1 オクターヴ上、pp)
    first = True; t = (II + 1) * BPB
    for t0, d, m in MEL[: int(len(MEL) * 0.6)]:
        add('H', (II + 1) * BPB + t0 + 0.25, d, m + 24, 0.07 * P.dyn.get(int((II + 1) + t0 // BPB), 0.8) / 0.8, '旋律の反響 (2 オクターヴ上、pp)' if first else None); first = False

META = {'style': 'elegia', 'detach': 0.88, 'humanize': True, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLIX · Melodia sola al pianoforte',
        'subtitle': 'MOTHER・LOVELESS・トラック 8 から、グランドピアノで、メロディーだけ取り上げて合成: 旋律はトラック 8 の採譜 (全部、4 度下げてト長調 / ホ短調に)、MOTHER・LOVELESS からは旋律を使わず、調・テンポ (♩=68)・和音の輪・バラードの形式だけ。序 → 1 番 → 間奏 → 2 番 (1 オクターヴ上 + カノン) → 終わり',
        'legend': ['S', 'A', 'T', 'B', 'H', 'L'], 'vname': {'S': 'Pf 旋律 (右手)', 'A': 'Pf カノン / 分散和音', 'T': 'Pf 分散和音 (左手)', 'B': 'Pf 根音 (左手)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'},
        'footer': ['旋律 = トラック 8 (録音) の最上声の採譜 (8 分音符に量子化、オクターヴの跳びは下の音に寄せて)、和音もトラック 8 の採譜、どちらも 4 度下げてト長調 / ホ短調に。MOTHER・LOVELESS (LUNA SEA) の旋律は採譜せず、調・テンポ・和音の輪 (G → D/F# → Em7 → Cmaj7 / Em7 → Cmaj7 → G → D7 / G → D7 → Em7 → C)・形式だけ',
                   '合成はグランドピアノだけ (録音は鳴らさない、シンセ不使用)。2 番はアルトが 2 小節遅れのカノン。鐘なし、声なし。']}

if __name__ == '__main__':
    print('melody notes', len(MEL), 'bars', MEL_BARS, 'range', min(m for _, _, m in MEL), max(m for _, _, m in MEL))
    print('head', ' '.join('%s:%g' % (name_of(m), d) for _, d, m in MEL[:16]))
    compose.main(OUT, seed=159, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e['v'] for e in d['extras']))
