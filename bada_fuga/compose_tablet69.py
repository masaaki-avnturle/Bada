#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXIX · Requiem 08:09 (2026-09-23 08:09 の録音を主題曲に、LXVIII をバックに — フーガを醸すレクイエム)
  主題曲: 9/23 08:09 の録音 (ト長調 / ホ短調、ピアノの実音)。その最上声から主題 (ホ短調で シ・ラ・シ・ソ・ド・ミ、8 拍) を作る。
  バック: LXVIII (全音符を 2 倍に伸ばしたピアノの交響曲) の技法と音 —
    - 主題を 16 倍・8 倍に伸ばし、伸ばした音をテノールがピアノで 4 分音符ごとに打ち直す (♩=60、止まらない)。深い鐘 (バス) は 2 全音符ごと
    - 伸ばした長い音の中で: 08:09 の録音の実音 / LXVIII の抜粋 (ホ短調の Adagio の、主音ミの保続の上のフーガ — すべてピアノの実音) /
      08:09 の主題のフーガ (属音シの保続の上でストレッタ、最後の主音ミの上で 1 倍と 2 倍 (拡大) の主題を同時に)
  形式 (♩=60, ホ短調):
    Introitus (08:09 の始まり) → I. Requiem per augmentationem ×16 → II. Fuga (08:09 の主題の 4 声フーガ)
    → III. Lacrimosa (08:09 の実音) → IV. Finale ×8 con Fuga → Amen (ホ長調)
  すべてピアノの実音 (録音から切り出した 1 音・録音そのもの・LXVIII のピアノ)。シンセ・ドラムなし。
  使い方: python compose_tablet69.py <bank69.json> <素材の wav フォルダ (tablet68.wav)> [score_tablet69.json]
"""
import sys, os, json
import numpy as np, soundfile as sf
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet63 as LXIII
import compose_tablet65 as LXV

add = CT.add
BPM = 60
SRC = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else '.'
TH = '20260923_080918'                             # 主題曲
EM = 2                                             # ホ短調 (ニ短調から)
VOICE_SRC = {'S': TH, 'A': TH, 'T': '20260925_130431', 'B': '20260925_124643'}
DYNK = 1.3
SWELL, AUD = [], []
_RMS = {}

def ex_gain(path, off, dur):
    if path not in _RMS:
        y, sr = sf.read(path, dtype='float32'); y = y.mean(1) if y.ndim > 1 else y; _RMS[path] = (y, sr, float(np.sqrt((y ** 2).mean())) + 1e-9)
    y, sr, full = _RMS[path]; ex = y[int(off * sr):int((off + dur) * sr)]
    return float(np.clip(full / (np.sqrt((ex ** 2).mean()) + 1e-9), 0.5, 2.0))

def aug(P, f, k, subj, hl, label, bell=8):
    """主題を k 倍に: テノールは 4 分音符ごとに打ち直し、バス (深い鐘) は 2 全音符ごと。和声も k 倍に"""
    for i, c in enumerate(hl):
        for q in range(k): P.harm[f * BPB + i * k + q] = c
    t, tq, bq = 0, [], []
    for d, m in subj:
        L = int(round(d * k))
        tq += [(t + j, m - 12, 1) for j in range(L)]
        bq += [(t + j, m - 24, min(bell, L - j)) for j in range(0, L, bell)]
        t += L
    for v, notes, lab in (('T', tq, label), ('B', bq, '×%d (深い鐘)' % k)):
        n0 = len(P.entries)
        for s_, m, dur in notes: P.place(v, f, [(dur, m)], 0, lab, beat=s_)
        del P.entries[n0 + 1:]
    SWELL.append((f, f + t // BPB))
    return t // BPB

def build():
    t0, inside = CT.excerpt(TH, EM, 13.0); s_ = LXIII.smooth(CT.make_subject(inside, EM, BPM)); H = CT.harmonize(s_)
    T5.SUBJ[TH] = (s_, H); print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_), H)
    Hb = [c for bar in H for c in bar]                               # 1 拍ごとの和音 (8 拍)
    total = 8 + 32 + 16 + 8 + 16 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, EM, VOICE_SRC, {}))
    b = 0
    rec = os.path.join(SRC, TH + '.wav'); l68 = os.path.join(SRC, 'tablet68.wav')
    def window(b0, n_, path, off, tag, fout=3.0):
        g = 0.5 if path == rec else 0.32                             # LXVIII はバック (主題曲より約 4 dB 小さく)
        AUD.append((b0, n_, path, off, g * ex_gain(path, off, n_ * 4.0), tag, fout))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def audio(n_, title, sub, path, off, tag):
        nonlocal b
        P.section(b, title, sub); window(b, n_, path, off, tag, fout=4.0)
        for v in VOICES: P.rest_bars(v, b, b + n_)
        P.set_harms(b, [['Dm'] * 4] * n_); b += n_
    def entry(v, bar, tr, lab, k=1):
        P.place(v, bar, [(d * k, m + tr) for d, m in s_], 0, lab)
    # ================= Introitus
    audio(8, 'Introitus — 主題曲 9/23 08:09 の実音 (ホ短調)', '主題曲の始まり — ピアノの実音のまま', rec, 0.0, '主題曲 9/23 08:09 — 始まり')
    # ================= I. Requiem per augmentationem ×16 (32 小節: シ 2 · ラ 2 · シ 12 · ソ 6 · ド 6 · ミ 4)
    f = b; P.section(f, 'I. Requiem per augmentationem ×16 (ホ短調)', '08:09 の主題を 16 倍に — 伸ばした音の中に、主題曲の実音・LXVIII・主題のフーガ')
    b += aug(P, f, 16, s_, Hb, '主題 (08:09) ×16 — 4 分音符を 16 倍に')
    for j in range(32): P.dyn[f + j] = DYNK * (0.62 + 0.22 * j / 31)
    P.set_harms(f, H); entry('A', f, 0, '主題 (08:09) ×1 — フーガ'); P.set_harms(f + 2, transpose_h(H, 7)); entry('S', f + 2, 7, '答え (5 度上)')
    window(f + 4, 8, l68, 512.0, 'LXVIII — Adagio の二重フーガ (ミの保続の上)')
    P.set_harms(f + 12, H + H); entry('S', f + 12, 0, '主題 ストレッタ'); entry('A', f + 13, -12, None)
    window(f + 16, 6, rec, 40.0, '主題曲 9/23 08:09 (ソの中で)')
    window(f + 22, 6, l68, 384.0, 'LXVIII — Adagio のフーガの入り (ドの中で)')
    P.set_harms(f + 28, [[Hb[2 * i], Hb[2 * i], Hb[2 * i + 1], Hb[2 * i + 1]] for i in range(4)])     # 2 倍の主題の和声 (1 つの和音が 2 拍)
    entry('A', f + 28, -12, '主題 ×2 (拡大) + ×1', k=2); entry('S', f + 28, 0, None); entry('S', f + 30, 0, None)
    LXIII.ARP.append((f + 12, f + 16, 0.09, EM))
    # ================= II. Fuga (08:09 の主題の 4 声フーガ)
    f = b; P.section(f, 'II. Fuga — 08:09 の主題 (ホ短調)', '主題曲の主題の 4 声フーガ — 提示 (アルト → ソプラノの答え → バス → テノール)、下属調、ストレッタ、保続低音')
    T11.bach_fugue(P, f, TH, '①'); b += 16
    for j in range(16): P.dyn[f + j] = DYNK * (0.7 if j < 8 else 0.8)
    LXIII.ARP.append((f + 8, f + 12, 0.08, EM))
    # ================= III. Lacrimosa
    audio(8, 'III. Lacrimosa — 主題曲の実音 (ホ短調)', '9/23 08:09 の実音 — 打ち直しが止まる', rec, 150.0, '主題曲 9/23 08:09 — Lacrimosa')
    # ================= IV. Finale ×8 con Fuga (16 小節: シ 1 · ラ 1 · シ 6 · ソ 3 · ド 3 · ミ 2)
    f = b; P.section(f, 'IV. Finale per augmentationem ×8 con Fuga (ホ短調)', '主題を 8 倍に (全音符が 2 全音符) — LXVIII のフーガと、主題のストレッタ')
    b += aug(P, f, 8, s_, Hb, '主題 (08:09) ×8')
    for j in range(16): P.dyn[f + j] = DYNK * (0.72 + 0.16 * j / 15)
    window(f + 2, 6, l68, 544.0, 'LXVIII — Adagio 二度目のフーガ (シの保続の上)')
    P.set_harms(f + 8, H); entry('S', f + 8, 0, '主題 ストレッタ (最後)'); entry('A', f + 9, -12, None)
    window(f + 11, 3, rec, 190.0, '主題曲 9/23 08:09 — 終わり近く')
    P.set_harms(f + 14, [['Dm'] * 4] * 2); LXIII.ARP.append((f + 14, f + 16, 0.09, EM))
    # ================= Amen (ホ長調)
    f = b; P.section(f, 'Amen — 変格終止 (ホ長調の和音で)', 'iv → I: 打ち直しが止まり、ホ長調の和音だけが残る'); b += 3
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.62
    LXIII.ARP.append((f, f + 2, 0.09, EM))
    assert b == total, (b, total)
    return P

def post(P, events, extras):
    LXIII.post(P, events, extras)
    for b0, n_, path, off, g, tag, fout in AUD:
        add('REC', b0 * BPB, n_ * BPB + 1.0, 0, g, None, src=path, off=off, fin=2.0, fout=fout, rid=os.path.basename(path), tag=tag)

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [TH], 'piano_decay': 1.8, 'reverb': [4.8, 1.7, 0.42],
    'title': 'Requiem BADA — LXIX · Requiem 08:09',
    'subtitle': '9/23 08:09 の録音を主題曲に、LXVIII をバックに — フーガを醸すレクイエム (ホ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': '分散和音'},
    'footer': ['Introitus (08:09) → I. Requiem ×16 → II. Fuga (08:09 の主題) → III. Lacrimosa (08:09) → IV. Finale ×8 con Fuga → Amen (ホ長調)',
               '主題曲は 9/23 08:09 の録音。バックは LXVIII の技法と抜粋 (伸ばした音の打ち直し・深い鐘・保続音の上のフーガ)。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet69.json'
    compose.main(out, seed=169, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if n_['v'] in 'SA' and (lab.startswith('主題') or lab.startswith('答え')) else 1.25), 4)
    LXV.SWELL[:] = SWELL; LXV.swell(d); LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:24]) for s in d['sections']])
