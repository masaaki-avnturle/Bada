#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXV · Summa per augmentationem (これまでの曲を 1 曲に — コントラプンクトゥスの主題を 4 倍・16 倍に伸ばし、その中に fuga を)
  合わせる曲 (音は mp4 から取り出して、録音の抜粋と同じように流す — テープのように調をニ短調へ合わせる):
    requiem.mp4 (Requiem BADA, ニ短調) · fuga.mp4 (Contrapunctus BADA, ニ短調) · tablet.mp4 (Tablet Sessions I) · tablet4.mp4 (IV, ホ短調 → 全音下げ)
    tablet5.mp4 (V, ヘ短調 → 短 3 度下げ) · tablet6.mp4 (VI, ヘ短調 → 短 3 度下げ) · tablet64 (LXIV, ニ短調の Canon II の終わり)
  骨組み: fuga.mp4 (Contrapunctus BADA) の主題 I (レ・ミ・ファ・ファ#・ソ・ラ・ソ・ファ・ミ・レ・ド#・レ、20 拍) を拡大する —
    Augmentatio ×4: 4 分音符が全音符に (20 小節)。Augmentatio ×16: 4 分音符が 16 個分 = 4 小節に (80 小節)
    伸ばした音はピアノで 4 分音符ごとに打ち直す (テノール、♩=60 = 1 秒に 1 打、止まらない)。バスは同じ旋律を 2 オクターヴ下で小節の頭だけ (深い鐘)。
    和声も主題 I のもとの和声を 4 倍・16 倍に伸ばす (1 つの和音が 4 拍・16 拍続く)。
  16 倍に伸ばしている音の中に fuga: 長い音のあいだに、
    レ (12 小節) — fuga.mp4 の提示部 / ミ・ファ — tablet.mp4 / ファ#・ソ — ピアノの 4 声が自由に対位法 / ラ (8 小節、属音の保続) — fuga.mp4 の三重結合のあたり
    / ソ・ファ — tablet5.mp4 / ミ — ピアノの 4 声 / レ・ド# — tablet4.mp4 / 最後のレ (16 小節、主音の保続) — 主題 I・II・III (B-A-D-A) の三重フーガをピアノで 2 回
  洗脳的: ♩=60 の止まらない打鍵、何十秒も変わらない和音、同じ主題を 4 倍・16 倍で聴かせ続ける。
  形式 (♩=60, ニ短調): Introitus (requiem.mp4) → Augmentatio ×4 → Lacrimosa (tablet6.mp4) → Augmentatio ×16 con Fuga → LXIV の Canon II の終わり → Amen (ニ長調)
  4 声はすべて録音から切り出したピアノの実音 (bank61)。新しく足した音にシンセ・ドラム・心臓の鼓動なし (requiem.mp4・fuga.mp4 はもとの音のまま)。
  使い方: python compose_tablet65.py <bank61.json> <素材の wav があるフォルダ> [score_tablet65.json]
"""
import sys, os, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet48 as K
import compose_tablet61 as LXI
import compose_tablet62 as LXII
import compose_tablet63 as LXIII

add = CT.add
BPM = 60
SRC = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else '.'
VOICE_SRC, DYNK = LXI.VOICE_SRC, LXI.DYNK
H1 = [c for bar in H_S1 for c in bar]              # 主題 I の和声 (1 拍に 1 つ、20 拍)
SWELL = []
AUD = []                                           # (小節, 小節数, 素材, 開始秒, テープの移調, 大きさ, 表示)

def aug(P, f, k, label, skip=()):
    """主題 I を k 倍に: テノールは 4 分音符ごとに打ち直し、バスは小節の頭だけ。和声も k 倍に伸ばす"""
    for i, c in enumerate(H1):
        for q in range(k): P.harm[f * BPB + i * k + q] = c
    t, tq, bq = 0, [], []
    for d, m in S1:
        for j in range(int(round(d * k))):
            if not any(a <= f * BPB + t + j < b for a, b in skip): tq.append((t + j, m - 12))
        for j in range(0, int(round(d * k)), BPB): bq.append((t + j, m - 24))
        t += int(round(d * k))
    def put(v, notes, dur, lab):
        n0 = len(P.entries)
        for s_, m in notes: P.place(v, f, [(dur, m)], 0, lab, beat=s_)      # ラベル付き = 自動の声部直しで動かさない
        del P.entries[n0 + 1:]                                               # 画面の主題ラベルは最初の 1 打だけ
        cov = {int(s_ + x) for s_, m in notes for x in range(int(dur))}
        for bt in range(t):
            if bt not in cov: P.rest[v].add(f * BPB + bt)
    put('T', tq, 1, label); put('B', bq, 4, '×%d (深い鐘)' % k)
    SWELL.append((f, f + t // BPB))
    return t // BPB

def build():
    total = 8 + 20 + 6 + 80 + 8 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, 0, VOICE_SRC, {}))
    b = 0
    def audio(bars, title, sub, src, off, semis, gain, tag, fout=4.0):
        nonlocal b
        P.section(b, title, sub); AUD.append((b, bars, src, off, semis, gain, tag, fout))
        for v in VOICES: P.rest_bars(v, b, b + bars)
        P.set_harms(b, [['Dm'] * 4] * bars); b += bars
    # ================= Introitus (requiem.mp4)
    audio(8, 'Introitus — requiem.mp4 (ニ短調)', 'Requiem BADA の始まりの音のまま — ここから時間が伸びていく', 'requiem.wav', 0.0, 0, 0.5, 'requiem.mp4 — Requiem BADA')
    # ================= Augmentatio ×4
    f = b; P.section(f, 'Augmentatio ×4 — 主題 I を 4 倍に (ニ短調)', 'fuga.mp4 の主題 I の 4 分音符が全音符に — 伸ばした音を 1 拍ごとに打ち直し、ピアノの 2 声が自由に歌う')
    b += aug(P, f, 4, '主題 I ×4 — 4 分音符を 4 倍に')
    for k in range(20): P.dyn[f + k] = DYNK * (0.6 + 0.12 * k / 19)
    LXIII.ARP.append((f, f + 20, 0.11, 0))
    # ================= Lacrimosa (tablet6.mp4)
    audio(6, 'Lacrimosa — tablet6.mp4 (ヘ短調 → ニ短調)', 'Tablet Sessions VI の実音を、テープのように短 3 度下げて', 'tablet6.wav', 96.0, -3, 0.55, 'tablet6.mp4 — Tablet Sessions VI (短 3 度下げ)')
    # ================= Augmentatio ×16 con Fuga
    f = b; P.section(f, 'Augmentatio ×16 con Fuga (ニ短調)', '主題 I の 4 分音符を 16 倍 (4 小節) に — 伸ばしている音の中に、fuga.mp4・Tablet Sessions・三重フーガ')
    tri = [((f + 66) * BPB, (f + 69) * BPB), ((f + 73) * BPB, (f + 76) * BPB)]   # 三重フーガの B-A-D-A をテノールが弾くあいだは打ち直しを休む (バスの鐘は続く)
    aug(P, f, 16, '主題 I ×16 — 4 分音符を 16 倍に伸ばす', skip=tri)
    for k in range(80): P.dyn[f + k] = DYNK * (0.62 + 0.2 * k / 79)
    inner = [(0, 12, 'fuga.wav', 30.0, 0, 0.5, 'fuga.mp4 — Contrapunctus BADA の提示部 (レの中で)'),
             (12, 12, 'tablet.wav', 304.0, -2, 0.55, 'tablet.mp4 — Tablet Sessions I (全音下げ, ミ・ファの中で)'),
             (32, 8, 'fuga.wav', 190.0, 0, 0.5, 'fuga.mp4 — 三重結合のあたり (ラの保続の中で)'),
             (40, 8, 'tablet5.wav', 16.0, -3, 0.55, 'tablet5.mp4 — Tablet Sessions V (短 3 度下げ, ソ・ファの中で)'),
             (56, 8, 'tablet4.wav', 128.0, -2, 0.55, 'tablet4.mp4 — Tablet Sessions IV (全音下げ, レ・ド#の中で)')]
    for b0, n_, src, off, semis, g, tag in inner:
        AUD.append((f + b0, n_, src, off, semis, g, tag, 3.0))
        for v in 'SA': P.rest_bars(v, f + b0, f + b0 + n_)
    for b0, b1 in ((24, 32), (48, 56)): LXIII.ARP.append((f + b0, f + b1, 0.1, 0))   # ピアノの 4 声だけの所 (ファ#・ソ、ミ)
    # 最後のレ (16 小節の主音の保続) の中で、主題 I・II・III の三重フーガを 2 回
    for r0, (vs1, vs2, vs3, t1, t2, t3) in ((f + 64, ('A', 'S', 'T', 0, 12, -12)), (f + 71, ('S', 'A', 'T', 12, 0, -12))):
        P.set_harms(r0, H_TRIPLE)
        P.place(vs1, r0, S1, t1, '主題 I (三重フーガ)'); P.place(vs2, r0, S2, t2, '主題 II'); P.place(vs3, r0 + 2, S3, t3, '主題 III B-A-D-A')
    P.set_harms(f + 78, [['Dm'] * 4] * 2)
    b += 80
    # ================= LXIV の Canon II の終わり
    audio(8, 'LXIV — Canon II の終わり (ニ短調)', '前の曲の、16 倍・4 倍・1 倍の主題が主音でそろう所', 'tablet64.wav', 256.0, 0, 0.5, 'tablet64 — LXIV Canon II の終わり')
    # ================= Amen (ニ長調)
    f = b; P.section(f, 'Amen — 変格終止 (ニ長調の和音で)', 'iv → I: 打鍵が止まり、ニ長調の和音だけが残る'); b += 3
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.62
    LXIII.ARP.append((f, f + 2, 0.1, 0))
    assert b == total, (b, total)
    return P

def post(P, events, extras):
    LXIII.post(P, events, extras)
    for b0, n_, src, off, semis, g, tag, fout in AUD:
        add('REC', b0 * BPB, n_ * BPB + 1.0, 0, g, None, src=os.path.join(SRC, src), off=off, fin=2.0, fout=fout, rid=src, tag=tag,
            **({'semis': semis} if semis else {}))

def swell(d):
    """伸ばした音の打ち直し (テノール): 1 音の中で、頭を強く、あとは息をするようにふくらんで静まる"""
    import numpy as np
    for b0, b1 in SWELL:
        t0, t1 = d['bar_times'][b0], d['bar_times'][min(b1, len(d['bar_times']) - 1)] if b1 < len(d['bar_times']) else d['duration']
        ts = sorted([x for x in d['notes'] if x['v'] == 'T' and not (x.get('label') or '').startswith('主題 III') and t0 - 1e-3 <= x['t'] < t1 - 1e-3], key=lambda x: x['t'])
        runs, cur = [], []
        for x in ts:
            if cur and (x['m'] != cur[-1]['m'] or x['t'] - cur[-1]['t'] > 1.5): runs.append(cur); cur = []
            cur.append(x)
        if cur: runs.append(cur)
        for run in runs:
            for i, x in enumerate(run):
                x['dyn'] = round(x['dyn'] * (1.15 if i == 0 else 0.72 + 0.22 * np.sin(np.pi * i / max(1, len(run) - 1))), 4)

META = {k: v for k, v in LXI.META.items()}
META.update(
    rec_order=LXIII.ORDER,
    title='Requiem BADA — LXV · Summa per augmentationem',
    subtitle='requiem・fuga・tablet I・IV・V・VI・LXIV を、主題 I の 4 倍・16 倍の中に — 洗脳的なレクイエムとフーガ (♩=60)',
    legend=['TB', 'PF'], vname={'TB': '取り込んだ曲 (mp4)', 'PF': '分散和音'}, tb_label='取り込んだ曲 (mp4)',
    footer=['Introitus (requiem) → ×4 → Lacrimosa (tablet6) → ×16 con Fuga (fuga・tablet・tablet5・tablet4・三重フーガ) → LXIV → Amen (ニ長調)',
            '主題 I (fuga.mp4 の Contrapunctus BADA) の 4 分音符を 4 倍・16 倍に伸ばし、1 拍ごとに打ち直す。新しい音はすべて録音から切り出したピアノの実音。'])

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet65.json'
    compose.main(out, seed=165, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * 1.25, 4)
    swell(d); LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:24]) for s in d['sections']])
