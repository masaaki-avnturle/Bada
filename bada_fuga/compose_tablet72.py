#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXII · Requiem 12:46 II (9/25 12:46 の録音をもう一度主題曲に — 上る主題を 16 倍に伸ばし、LXXI をバックに)
  主題曲: 9/25 12:46 の録音 (ヘ短調)。LXXI は 3 分 1 秒からの「下りる」線を主題にしたので、今度は 1 分 2 秒からの「上る」線を主題に —
    ヘ短調で ファ・ソ・ファ・ラ♭・シ♭・レ♭・ファ (8 拍)。LXXI の下りる主題と向かい合う (反行のように)。
  16 倍の伸び: ファ 4・ソ 8・ファ 4・ラ♭ 2・シ♭ 2・レ♭ 6・ファ 6 小節。テノールが 4 分音符ごとに打ち直し、深い鐘は 2 全音符ごと。
  バック: LXXI (先程の曲) — 同じヘ短調なので、音をそのまま (すべてピアノの実音) 長い音の中で流す。LXXI の保続音が合う所へ:
    長いソ (属和音) ← LXXI の属音ドの保続 / ラ♭・シ♭ (下属和音) ← LXXI の長いシ♭ / 長いレ♭ ← LXXI のラ♭ の所。LXXI は主題曲より約 4 dB 小さく。
  フーガを醸す: 最初の主音ファの上で主題 → 5 度上の答え、長いレ♭ の上でストレッタ、最後のファの上で 1 倍と 2 倍 (拡大) の主題を同時に。
    II 楽章は上る主題の 4 声フーガ。IV 楽章ももう一度 ×16 で、LXXI の Finale をバックに。
  形式 (♩=60, ヘ短調): Introitus (12:46) → I. Requiem ×16 → II. Fuga → III. Lacrimosa (12:46) → IV. Finale ×16 con Fuga → Amen (ヘ長調)
  使い方: python compose_tablet72.py <bank61.json> <素材の wav フォルダ (20260925_124643.wav・tablet71.wav)> [score_tablet72.json]
"""
import sys, os, json
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

add = CT.add
BPM = 60
SRC = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else '.'
TH = '20260925_124643'
FM = 3
SUBJ_AT = (62.5, 8.0)                              # 上る線
VOICE_SRC = {'S': TH, 'A': '20260925_130431', 'T': TH, 'B': '20260929_151249'}
DYNK = 1.3
H8 = ['Dm', 'A7', 'A7', 'Dm', 'Gm', 'Gm', 'Bb', 'Dm']   # 1 拍ごとの和音 (エンジンのニ短調): i・V・V・i・iv・iv・VI・i
AUD = []

def build():
    segs = CT.REC[TH]['segs']; w = SUBJ_AT[1]
    t0 = min(segs, key=lambda x: abs(x['t'] - 0.03 - SUBJ_AT[0]))['t'] - 0.03
    s_ = LXIII.smooth(CT.make_subject([x for x in segs if t0 <= x['t'] < t0 + w], FM, BPM))
    H = [H8[:4], H8[4:]]; T5.SUBJ[TH] = (s_, H)
    print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = 8 + 32 + 16 + 8 + 32 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, FM, VOICE_SRC, {}))
    b = 0
    rec = os.path.join(SRC, TH + '.wav'); l71 = os.path.join(SRC, 'tablet71.wav')
    def window(b0, n_, path, off, tag):
        g = 0.6 if path == rec else 0.32                            # LXXI はバック (主題曲より約 4 dB 小さく)
        AUD.append((b0, n_, path, off, g * LXIX.ex_gain(path, off, n_ * 4.0), tag, 3.0))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def audio(n_, title, sub, off, tag):
        nonlocal b
        P.section(b, title, sub); window(b, n_, rec, off, tag)
        for v in VOICES: P.rest_bars(v, b, b + n_)
        P.set_harms(b, [['Dm'] * 4] * n_); b += n_
    def entry(v, bar, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in s_], 0, lab)
    def requiem16(title, sub, label, wins, dyn0, dyn1, final_lab):
        """主題 ×16 (32 小節: ファ 4 · ソ 8 · ファ 4 · ラ♭ 2 · シ♭ 2 · レ♭ 6 · ファ 6)"""
        nonlocal b
        f = b; P.section(f, title, sub)
        b += LXIX.aug(P, f, 16, s_, H8, label)
        for j in range(32): P.dyn[f + j] = DYNK * (dyn0 + (dyn1 - dyn0) * j / 31)
        P.set_harms(f, H); entry('A', f, 0, '主題 (12:46 上る線) ×1 — フーガ'); P.set_harms(f + 2, transpose_h(H, 7)); entry('S', f + 2, 7 - 12, '答え (5 度上)')
        for b0, n_, path, off, tag in wins: window(f + b0, n_, path, off, tag)
        P.set_harms(f + 20, H + H); entry('S', f + 20, 0, '主題 ストレッタ (レ♭の上)'); entry('A', f + 21, -12, None)
        P.set_harms(f + 28, [[H8[2 * i]] * 2 + [H8[2 * i + 1]] * 2 for i in range(4)])
        entry('A', f + 28, -12, final_lab, k=2); entry('S', f + 28, 0, None); entry('S', f + 30, 0, None)
        LXIII.ARP.append((f + 20, f + 24, 0.09, FM))
    audio(8, 'Introitus — 主題曲 9/25 12:46 の実音 (ヘ短調)', '主題曲をもう一度 — ピアノの実音のまま', 20.0, '主題曲 9/25 12:46')
    requiem16('I. Requiem per augmentationem ×16 (ヘ短調)', '上る主題を 16 倍に — 長い音の中に LXXI (そのまま)・主題曲の実音・主題のフーガ', '主題 (上る線) ×16 — 4 分音符を 16 倍に',
              [(4, 4, l71, 32.0, 'LXXI — 属音ドの上のフーガ (ソの中で)'), (8, 4, l71, 64.0, 'LXXI — 属音ドの保続 (ソの中で)'),
               (12, 4, rec, 62.0, '主題曲 9/25 12:46 — 上る線のあたり (ファの中で)'), (16, 4, l71, 80.0, 'LXXI — 長いシ♭ (ラ♭・シ♭ の中で)'),
               (24, 4, l71, 128.0, 'LXXI — ラ♭ の所 (レ♭ の中で)')], 0.62, 0.8, '主題 ×2 (拡大) + ×1')
    f = b; P.section(f, 'II. Fuga — 上る主題 (ヘ短調)', '12:46 の上る主題の 4 声フーガ — 提示、下属調、ストレッタ、保続低音')
    T11.bach_fugue(P, f, TH, '①'); b += 16
    for j in range(16): P.dyn[f + j] = DYNK * (0.7 if j < 8 else 0.8)
    LXIII.ARP.append((f + 8, f + 12, 0.08, FM))
    audio(8, 'III. Lacrimosa — 主題曲の実音 (ヘ短調)', '9/25 12:46 の実音 — 打ち直しが止まる', 150.0, '主題曲 9/25 12:46 — Lacrimosa')
    requiem16('IV. Finale per augmentationem ×16 con Fuga (ヘ短調)', 'もう一度 16 倍に — LXXI の Finale をバックに、最後は主題の 1 倍と 2 倍', '主題 (上る線) ×16 (二度目)',
              [(4, 4, l71, 256.0, 'LXXI — Finale の属音の上のフーガ (ソの中で)'), (8, 4, l71, 288.0, 'LXXI — Finale の属音の保続 (ソの中で)'),
               (12, 4, rec, 185.0, '主題曲 9/25 12:46 (ファの中で)'), (16, 4, l71, 304.0, 'LXXI — Finale の長いシ♭ (ラ♭・シ♭ の中で)'),
               (24, 4, l71, 352.0, 'LXXI — Finale のラ♭ の所 (レ♭ の中で)')], 0.72, 0.9, '主題 ×2 (拡大) + ×1 — 最後')
    f = b; P.section(f, 'Amen — 変格終止 (ヘ長調の和音で)', 'iv → I: 打ち直しが止まり、ヘ長調の和音だけが残る'); b += 3
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.62
    LXIII.ARP.append((f, f + 2, 0.09, FM))
    assert b == total, (b, total)
    return P

def post(P, events, extras):
    LXIII.post(P, events, extras)
    for b0, n_, path, off, g, tag, fout in AUD:
        add('REC', b0 * BPB, n_ * BPB + 1.0, 0, g, None, src=path, off=off, fin=2.0, fout=fout, rid=os.path.basename(path), tag=tag)

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [TH], 'piano_decay': 1.8, 'reverb': [4.8, 1.7, 0.42],
    'title': 'Requiem BADA — LXXII · Requiem 12:46 II',
    'subtitle': '9/25 12:46 の「上る」線を主題に、16 倍に伸ばし、LXXI をバックに — フーガを醸すレクイエム (ヘ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': '分散和音'},
    'footer': ['Introitus (12:46) → I. Requiem ×16 → II. Fuga (上る主題) → III. Lacrimosa (12:46) → IV. Finale ×16 con Fuga → Amen (ヘ長調)',
               '主題曲は 9/25 12:46 の録音 (上る線)。バックは LXXI (同じヘ短調、音をそのまま)。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet72.json'
    compose.main(out, seed=172, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if n_['v'] in 'SA' and (lab.startswith('主題') or lab.startswith('答え')) else 1.25), 4)
    LXV.SWELL[:] = LXIX.SWELL; LXV.swell(d); LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:24]) for s in d['sections']])
