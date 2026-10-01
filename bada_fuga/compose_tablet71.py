#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXI · Requiem 12:46 (2026-09-25 12:46 の録音を主題曲に、主題を 16 倍に伸ばし、LXX をバックに — フーガを醸すレクイエム)
  主題曲: 9/25 12:46 の録音 (ヘ短調、ピアノの実音)。3 分 1 秒からの最上声から主題 — ヘ短調で ド・レ♭・ド・シ♭・ラ♭・ファ と下りる嘆きの線 (8 拍)。
  16 倍の伸び: 主題の 4 分音符を 16 倍 (4 小節) に — ド 4・レ♭ 4・ド 4・シ♭ 12・ラ♭ 4・ファ 4 小節。テノールが 4 分音符ごとに打ち直し、深い鐘は 2 全音符ごと。
  バック: LXX (先程の曲、変ロ短調) を採譜して 5 半音下げ (変ロ短調 → ヘ短調)、速さは変えずにピアノの実音で弾き直す。
    LXX の長いファ → ミ♭ (属音 → 下属音) が、5 半音下げるとこの曲の長いド → シ♭ にそのまま重なる。
  フーガを醸す: 最初のド (属音) の上で主題 → 5 度上の答え、長いシ♭ の上でストレッタ、最後の主音ファの上で 1 倍と 2 倍 (拡大) の主題を同時に。
    II 楽章は 12:46 の主題の 4 声フーガ。IV 楽章ももう一度 ×16 で、LXX の Finale をバックに。
  形式 (♩=60, ヘ短調): Introitus (12:46 の始まり) → I. Requiem ×16 → II. Fuga → III. Lacrimosa (12:46 の実音) → IV. Finale ×16 con Fuga → Amen (ヘ長調)
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet71.py <bank61.json> <素材の wav フォルダ (20260925_124643.wav・tablet70.wav)> [score_tablet71.json]
          python compose_tablet67.py level <score_tablet71.json> <LXX を弾き直した所だけの wav>
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
import compose_tablet70 as LXX

add = CT.add
BPM = 60
SRC, OUT = LXX.SRC, LXX.OUT
TH = '20260925_124643'                             # 主題曲
FM = 3                                             # ヘ短調 (ニ短調から)
BACK_SEMIS = -5                                    # LXX (変ロ短調) → ヘ短調
SUBJ_AT = (181.5, 8.0)                             # 主題を取る所 (秒, 長さ) — 段のように下りる線
VOICE_SRC = {'S': TH, 'A': '20260925_130431', 'T': TH, 'B': '20260929_151249'}
DYNK = 1.3
H8 = ['A7', 'Gm', 'A7', 'Gm', 'Gm', 'Em7b5', 'Dm', 'Dm']   # 主題の 1 拍ごとの和音 (エンジンのニ短調): V・iv・V・iv (3 拍)・i
AUD, BACK = [], []

def build():
    segs = CT.REC[TH]['segs']; w = SUBJ_AT[1]
    t0 = min(segs, key=lambda x: abs(x['t'] - 0.03 - SUBJ_AT[0]))['t'] - 0.03                  # 打鍵の頭から
    s_ = LXIII.smooth(CT.make_subject([x for x in segs if t0 <= x['t'] < t0 + w], FM, BPM))
    H = [H8[:4], H8[4:]]; T5.SUBJ[TH] = (s_, H)
    print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = 8 + 32 + 16 + 8 + 32 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, FM, VOICE_SRC, {}))
    b = 0
    rec = os.path.join(SRC, TH + '.wav')
    def window(b0, n_, off, tag):
        AUD.append((b0, n_, rec, off, 0.5 * LXIX.ex_gain(rec, off, n_ * 4.0), tag, 3.0))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def back(b0, n_, off, tag):
        BACK.append((b0, n_, off, tag))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def audio(n_, title, sub, off, tag):
        nonlocal b
        P.section(b, title, sub); window(b, n_, off, tag)
        for v in VOICES: P.rest_bars(v, b, b + n_)
        P.set_harms(b, [['Dm'] * 4] * n_); b += n_
    def entry(v, bar, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in s_], 0, lab)
    def requiem16(title, sub, label, wins, backs, dyn0, dyn1, final_lab):
        """主題 ×16 (32 小節: ド 4 · レ♭ 4 · ド 4 · シ♭ 12 · ラ♭ 4 · ファ 4)"""
        nonlocal b
        f = b; P.section(f, title, sub)
        b += LXIX.aug(P, f, 16, s_, H8, label)
        for j in range(32): P.dyn[f + j] = DYNK * (dyn0 + (dyn1 - dyn0) * j / 31)
        P.set_harms(f, H); entry('A', f, 0, '主題 (12:46) ×1 — フーガ'); P.set_harms(f + 2, transpose_h(H, 7)); entry('S', f + 2, 7 - 12, '答え (5 度上)')
        for b0, n_, off, tag in wins: window(f + b0, n_, off, tag)
        for b0, n_, off, tag in backs: back(f + b0, n_, off, tag)
        P.set_harms(f + 20, H + H); entry('S', f + 20, 0, '主題 ストレッタ (シ♭の上)'); entry('A', f + 21, -12, None)
        P.set_harms(f + 28, [[H8[2 * i]] * 2 + [H8[2 * i + 1]] * 2 for i in range(4)])
        entry('A', f + 28, -12, final_lab, k=2); entry('S', f + 28, 0, None); entry('S', f + 30, 0, None)
        LXIII.ARP.append((f + 20, f + 24, 0.09, FM))
    # ================= Introitus
    audio(8, 'Introitus — 主題曲 9/25 12:46 の実音 (ヘ短調)', '主題曲の始まり — ピアノの実音のまま', 0.0, '主題曲 9/25 12:46 — 始まり')
    # ================= I. Requiem ×16
    requiem16('I. Requiem per augmentationem ×16 (ヘ短調)', '12:46 の主題を 16 倍に — 伸ばした音の中に、主題曲の実音・LXX (5 半音下げてピアノで)・主題のフーガ',
              '主題 (12:46) ×16 — 4 分音符を 16 倍に',
              [(4, 4, 40.0, '主題曲 9/25 12:46 (レ♭の中で)'), (16, 4, 60.0, '主題曲 9/25 12:46 (シ♭の中で)'), (24, 4, 95.0, '主題曲 9/25 12:46 (ラ♭の中で)')],
              [(8, 8, 64.0, 'LXX — ×16 のファ → ミ♭ (ド → シ♭ の中で)')], 0.62, 0.8, '主題 ×2 (拡大) + ×1')
    # ================= II. Fuga
    f = b; P.section(f, 'II. Fuga — 12:46 の主題 (ヘ短調)', '主題曲の下りる主題の 4 声フーガ — 提示、下属調、ストレッタ、保続低音')
    T11.bach_fugue(P, f, TH, '①'); b += 16
    for j in range(16): P.dyn[f + j] = DYNK * (0.7 if j < 8 else 0.8)
    LXIII.ARP.append((f + 8, f + 12, 0.08, FM))
    # ================= III. Lacrimosa
    audio(8, 'III. Lacrimosa — 主題曲の実音 (ヘ短調)', '9/25 12:46 の実音 — 打ち直しが止まる', 120.0, '主題曲 9/25 12:46 — Lacrimosa')
    # ================= IV. Finale ×16 con Fuga
    requiem16('IV. Finale per augmentationem ×16 con Fuga (ヘ短調)', 'もう一度 16 倍に — LXX の Finale をバックに、最後は主題の 1 倍と 2 倍',
              '主題 (12:46) ×16 (二度目)',
              [(4, 4, 150.0, '主題曲 9/25 12:46 (レ♭の中で)'), (16, 4, 170.0, '主題曲 9/25 12:46 (シ♭の中で)'), (24, 4, 200.0, '主題曲 9/25 12:46 (ラ♭の中で)')],
              [(8, 8, 288.0, 'LXX — Finale のファ → ミ♭ (ド → シ♭ の中で)')], 0.72, 0.9, '主題 ×2 (拡大) + ×1 — 最後')
    # ================= Amen (ヘ長調)
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

def rid_for(m): return VOICE_SRC['S'] if m >= 72 else VOICE_SRC['A'] if m >= 60 else VOICE_SRC['T'] if m >= 48 else VOICE_SRC['B']

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [TH], 'piano_decay': 1.8, 'reverb': [4.8, 1.7, 0.42],
    'title': 'Requiem BADA — LXXI · Requiem 12:46',
    'subtitle': '9/25 12:46 の録音を主題曲に、16 倍に伸ばし、LXX をバックに — フーガを醸すレクイエム (ヘ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['Introitus (12:46) → I. Requiem ×16 → II. Fuga (12:46 の主題) → III. Lacrimosa (12:46) → IV. Finale ×16 con Fuga → Amen (ヘ長調)',
               '主題曲は 9/25 12:46 の録音。バックは LXX を 5 半音下げてピアノで弾き直したもの。すべてピアノの実音。'],
}

if __name__ == '__main__':
    compose.main(OUT, seed=171, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(OUT)
    K.BPM = BPM; K.fix_voices(OUT)
    d = json.load(open(OUT)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if n_['v'] in 'SA' and (lab.startswith('主題') or lab.startswith('答え')) else 1.25), 4)
    LXV.SWELL[:] = LXIX.SWELL; LXV.swell(d); LXII.fix_pulse(d)
    bt = d['bar_times']; l70 = os.path.join(SRC, 'tablet70.wav')
    for w, (b0, n_, off, tag) in enumerate(BACK):
        t0 = bt[b0]; dur = n_ * BPB * 60.0 / BPM + 1.0
        notes = LXX.playable([(t, dd, m + BACK_SEMIS, v) for t, dd, m, v in LXX.transcribe(l70, off, off + dur)])
        d['extras'].append(dict(v='REC', t=t0, d=dur, beat=b0 * BPB, dbeats=dur, m=0, gain=0.0, src=l70, off=off, fin=0.1, fout=0.5,
                                rid='tablet70.wav', tag='%s → 5 半音下げてピアノで' % tag, label=None))
        for t, dd, m, v in notes:
            d['extras'].append(dict(v='PF', t=round(t0 + t, 4), d=round(max(0.12, dd), 4), beat=round(t0 + t, 4), dbeats=round(dd, 4),
                                    m=int(m), gain=round(0.18 * v, 4), rid=rid_for(m), rel=0.45, label=None, win=w))
        print('back %d  %-40s notes %d' % (w, tag[:40], len(notes)))
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:24]) for s in d['sections']])
