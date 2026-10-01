#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXVIII · Fuga per augmentationem (Klavier) (LXVII の全音符を 2 倍に伸ばし、フーガを醸す曲に)
  LXVII (すべて実音のピアノの交響曲) をもとに:
    - 全音符を 2 倍に (拡大 — バッハ「フーガの技法」コントラプンクトゥス VII のように):
        I・II 楽章の ×4 (4 分音符が全音符) を ×8 (全音符が 2 全音符 = 2 小節) に。深い鐘 (バス) も全音符から 2 全音符 (2 小節ごと) に。
        伸ばした音は、これまでどおりテノールが 4 分音符ごとに打ち直す (♩=60、止まらない)。
    - フーガを醸す: 伸ばした主音・属音の長い音 (保続音) の上で、フーガの主題が入る —
        最初のレ (6 小節): 主題 I がアルトで入り、ソプラノが対位法で応える
        ラ (属音、4 小節): 主題 III (B-A-D-A) がソプラノで
        最後のレ (8 小節): 主題 I と主題 II を同時に (二重フーガ)
      ほかの長い音の中では、LXVII と同じく提出した曲をピアノで弾き直したものが鳴る。IV 楽章の終わりは主題 I・II・III の三重フーガ。
  楽章: I. ニ短調 ×8 → イ短調 ×8 / II. Adagio ホ短調 ×8 ×2 / III. Scherzo ハ長調 ×8 / IV. Finale ニ短調 ×16 con Fuga / Coda ニ長調
  使い方: python compose_tablet68.py <bank61.json> <素材の wav フォルダ> <sources.json> [score_tablet68.json]
          python compose_tablet67.py level <score_tablet68.json> <ピアノに直した所だけの wav>   (抜粋の大きさをそろえる)
"""
import sys, os, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet63 as LXIII
import compose_tablet65 as LXV
import compose_tablet66 as LXVI
import compose_tablet67 as LXVII

BPM = 60
OUT = LXVII.OUT
VOICE_SRC, DYNK = LXVI.VOICE_SRC, LXVI.DYNK
H1, S1M, H1M = LXVI.H1, LXVI.S1M, LXVI.H1M
SWELL, AUD = [], []

def aug(P, f, k, subj, hl, label, skip=(), bell=8):
    """主題を k 倍に: テノールは 4 分音符ごとに打ち直し、バス (深い鐘) は bell 拍ごと (2 全音符)。和声も k 倍に"""
    for i, c in enumerate(hl):
        for q in range(k): P.harm[f * BPB + i * k + q] = c
    t, tq, bq = 0, [], []
    for d, m in subj:
        L = int(round(d * k))
        for j in range(L):
            if not any(a <= f * BPB + t + j < b for a, b in skip): tq.append((t + j, m - 12))
        for j in range(0, L, bell): bq.append((t + j, m - 24, min(bell, L - j)))
        t += L
    for v, notes, lab in (('T', [(s_, m, 1) for s_, m in tq], label), ('B', bq, '×%d (深い鐘・2 全音符)' % k)):
        n0 = len(P.entries)
        for s_, m, dur in notes: P.place(v, f, [(dur, m)], 0, lab, beat=s_)
        del P.entries[n0 + 1:]
        cov = {int(s_ + x) for s_, m, dur in notes for x in range(int(dur))}
        for bt in range(t):
            if bt not in cov: P.rest[v].add(f * BPB + bt)
    SWELL.append((f, f + t // BPB))
    return t // BPB

def build():
    total = (8 + 40 + 40) + (8 + 40 + 40 + 8) + 40 + 80 + (10 + 3)
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def lay(b0, n_, semis): CT.LAYOUT.append((b0, b0 + n_, semis, VOICE_SRC, {}))
    def audio(bars, title, sub, src, off, semis, tag, key_semis, fout=4.0):
        nonlocal b
        P.section(b, title, sub); AUD.append((b, bars, src, off, semis, 0.5, tag, fout))
        for v in VOICES: P.rest_bars(v, b, b + bars)
        P.set_harms(b, [['Dm'] * 4] * bars); lay(b, bars, key_semis); b += bars
    def inner(f, windows):
        for b0, n_, src, off, semis, tag in windows:
            AUD.append((f + b0, n_, src, off, semis, 0.5, tag, 3.0))
            for v in 'SA': P.rest_bars(v, f + b0, f + b0 + n_)
    def section(title, sub, k, subj, hl, semis, label, windows, dyn0, dyn1, arp=(), skip=()):
        nonlocal b
        f = b; P.section(f, title, sub); n_ = aug(P, f, k, subj, hl, label, skip); lay(f, n_, semis)
        for j in range(n_): P.dyn[f + j] = DYNK * (dyn0 + (dyn1 - dyn0) * j / max(1, n_ - 1))
        inner(f, windows)
        for a0, a1 in arp: LXIII.ARP.append((f + a0, f + a1, 0.1, semis))
        b += n_; return f
    def fugato(f, tag):
        """×8 の保続音の上のフーガ: 最初のレ (主題 I)、ラ (主題 III)、最後のレ (主題 I + II の二重フーガ)"""
        P.set_harms(f, H_S1); P.place('A', f, S1, 0, '主題 I ×1 — フーガ (%s)' % tag)
        P.set_harms(f + 16, H_S3); P.place('S', f + 16, S3, 0, '主題 III B-A-D-A (属音の上)')
        P.set_harms(f + 32, H_TRIPLE[:5]); P.place('S', f + 32, S1, 12, '主題 I (二重フーガ)'); P.place('A', f + 32, S2, 0, '主題 II')
        P.set_harms(f + 37, [['Dm'] * 4] * 3)
    W = lambda a, b_: [(6, 8) + a, (20, 8) + b_]
    # ================= I (ニ短調 → イ短調)
    audio(8, 'I. Introduzione — symphony (ニ短調)', '交響曲の始まりを実音のピアノで — ここから全音符が 2 倍に伸びていく', 'symphony.wav', 0.0, 0, 'symphony.mp4 — 始まり', 0)
    f = section('I. Fuga per augmentationem ×8 (ニ短調)', '主題 I の 4 分音符が 2 全音符に (全音符を 2 倍) — 長いレとラの上でフーガ、ほかの長い音の中に requiem_fuga_drill・tablet62', 8, S1, H1, 0,
                '主題 I ×8 — 全音符を 2 倍に', W(('requiem_fuga_drill.wav', 1660.0, 0, 'requiem_fuga_drill.mp4'), ('tablet62.wav', 140.0, 0, 'tablet62.mp4 — LXII')),
                0.62, 0.76, arp=[(14, 16), (28, 32)])
    fugato(f, 'ニ短調')
    f = section('I. ×8 — 答え (イ短調)', 'イ短調で主題 I ×8 — フーガと requiem_fuga_small・symphony', 8, S1, H1, -5, '主題 I ×8 (答え)',
                W(('requiem_fuga_small.wav', 680.0, 0, 'requiem_fuga_small.mp4'), ('symphony.wav', 400.0, 0, 'symphony.mp4 — イ短調の所')), 0.7, 0.82, arp=[(14, 16), (28, 32)])
    fugato(f, 'イ短調')
    # ================= II (ホ短調)
    audio(8, 'II. Adagio — acceptance (ホ短調)', 'BADA 528 Acceptance を実音のピアノで — 涙のアダージョへ', 'acceptance.wav', 80.0, 0, 'acceptance.mp4 — BADA 528 Acceptance', 2)
    f = section('II. Adagio per augmentationem ×8 (ホ短調)', 'ホ短調で主題 I ×8 — フーガと tablet46inst・tablet48inst', 8, S1, H1, 2, '主題 I ×8 (ホ短調)',
                W(('tablet46inst.wav', 60.0, 0, 'tablet46inst.mp4 — XLVI'), ('tablet48inst.wav', 80.0, 0, 'tablet48inst.mp4 — XLVIII')), 0.6, 0.68, arp=[(14, 16), (28, 32)])
    fugato(f, 'ホ短調')
    f = section('II. Adagio ×8 — 二度目 (ホ短調)', '主題 I ×8 をもう一度 — フーガと tablet6・tablet49inst', 8, S1, H1, 2, '主題 I ×8 (ホ短調, 二度目)',
                W(('tablet6.wav', 440.0, 0, 'tablet6.mp4 — Tablet Sessions VI'), ('tablet49inst.wav', 80.0, 0, 'tablet49inst.mp4 — XLIX')), 0.62, 0.72, arp=[(14, 16), (28, 32)])
    fugato(f, 'ホ短調')
    audio(8, 'II. Lacrimosa — tablet61 (ホ短調)', 'LXI のホ短調の所を実音のピアノで — 打鍵がひととき止まる', 'tablet61.wav', 140.0, 0, 'tablet61.mp4 — LXI', 2)
    # ================= III (ハ長調)
    f = section('III. Scherzo luminoso per augmentationem ×8 (ハ長調)', '主題 I の長調の形を 8 倍に — 中に cp14_C_G_uplift・piano_solo_8x、合い間はピアノの 1 倍の主題', 8, S1M, H1M, -2,
                '主題 I (長調) ×8',
                [(0, 8, 'cp14_C_G_uplift.wav', 600.0, 0, 'cp14_C_G_uplift.mp4'), (16, 8, 'piano_solo_8x.wav', 1320.0, 0, 'piano_solo_8x.mp4'),
                 (32, 8, 'cp14_C_G_uplift.wav', 1740.0, 0, 'cp14_C_G_uplift.mp4 — 終わり近く')], 0.66, 0.78, arp=[(8, 16), (24, 32)])
    for w0 in (8, 24):
        P.place('S', f + w0, S1M, 12, '主題 I (長調) ×1' if w0 == 8 else None); P.rest_bars('A', f + w0, f + w0 + 8); P.rest_bars('S', f + w0 + 5, f + w0 + 8)
    # ================= IV (ニ短調 ×16 con Fuga)
    f = b
    tri = [((f + 66) * BPB, (f + 69) * BPB), ((f + 73) * BPB, (f + 76) * BPB)]
    section('IV. Finale per augmentationem ×16 con Fuga (ニ短調)', '主題 I の 4 分音符を 16 倍に — 中に requiem_fuga_embrace・tablet・cp14_x8_part3・tablet60・LXV、最後は三重フーガ', 16, S1, H1, 0,
            '主題 I ×16 — 4 分音符を 16 倍に伸ばす',
            [(0, 12, 'requiem_fuga_embrace.wav', 1040.0, 0, 'requiem_fuga_embrace.mp4 (レの中で)'), (12, 12, 'tablet.wav', 320.0, -2, 'tablet.mp4 — Tablet Sessions I'),
             (32, 8, 'cp14_x8_part3.wav', 1120.0, 0, 'cp14_x8_part3.mp4 (ラの保続の中で)'), (40, 8, 'tablet60.wav', 140.0, -3, 'tablet60.mp4 — LX'),
             (56, 8, 'tablet65.wav', 360.0, 0, 'tablet65 — LXV の同じ ×16 の所')], 0.66, 0.86, arp=[(24, 32), (48, 56)], skip=tri)
    for r0, (vs1, vs2, vs3, t1, t2, t3) in ((f + 64, ('A', 'S', 'T', 0, 12, -12)), (f + 71, ('S', 'A', 'T', 12, 0, -12))):
        P.set_harms(r0, H_TRIPLE)
        P.place(vs1, r0, S1, t1, '主題 I (三重フーガ)'); P.place(vs2, r0, S2, t2, '主題 II'); P.place(vs3, r0 + 2, S3, t3, '主題 III B-A-D-A')
    P.set_harms(f + 78, [['Dm'] * 4] * 2)
    # ================= Coda (ニ長調)
    audio(10, 'Coda — symphony の終わり (ニ長調)', '交響曲の終わりのニ長調を実音のピアノで', 'symphony.wav', 456.0, 0, 'symphony.mp4 — 終わり (ニ長調)', 0, fout=3.0)
    f = b; P.section(f, 'Amen — 変格終止 (ニ長調の和音で)', 'iv → I: 打鍵が止まり、ニ長調の和音だけが残る'); lay(f, 3, 0); b += 3
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.62
    LXIII.ARP.append((f, f + 2, 0.1, 0))
    assert b == total, (b, total)
    return P

META = dict(LXVII.META,
    title='Requiem BADA — LXVIII · Fuga (Klavier)',
    subtitle='全音符を 2 倍に伸ばし、長い音の上でフーガが入る — すべて実音のピアノの洗脳的な交響曲 (♩=60)',
    footer=['I. ニ短調 ×8 → II. Adagio ホ短調 ×8 → III. Scherzo ハ長調 ×8 → IV. Finale ニ短調 ×16 con Fuga → Coda ニ長調',
            '全音符を 2 倍 (2 全音符) に伸ばして打ち直し、主音・属音の長い音の上でフーガの主題が入る。提出した曲はピアノで弾き直した。'])

if __name__ == '__main__':
    compose.main(OUT, seed=168, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=LXVII.post)
    CT.finish(OUT)
    K.BPM = BPM; K.fix_voices(OUT)
    d = json.load(open(OUT)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if (n_.get('label') or '').startswith('主題') and n_['v'] in 'SA' else 1.25), 4)  # フーガの主題を少し前に
    LXV.SWELL[:] = SWELL; LXV.swell(d); LXII.fix_pulse(d)
    bt = d['bar_times']
    for w, (b0, n_, src, off, semis, g, tag, fout) in enumerate(AUD):
        t0 = bt[b0]; dur = n_ * BPB * 60.0 / BPM + 1.0
        notes, recs = LXVII.convert(src, off, off + dur, semis)
        notes = LXVII.playable(notes)
        d['extras'].append(dict(v='REC', t=t0, d=dur, beat=b0 * BPB, dbeats=dur, m=0, gain=0.0, src=os.path.join(LXVII.SRC, src), off=off, fin=0.1, fout=0.5,
                                rid=src, tag='%s → 実音のピアノで' % tag, label=None))
        for t, dd, m, v in notes:
            d['extras'].append(dict(v='PF', t=round(t0 + t, 4), d=round(max(0.12, dd), 4), beat=round(t0 + t, 4), dbeats=round(dd, 4),
                                    m=int(m), gain=round(0.22 * v, 4), rid=LXVII.rid_for(m), rel=0.45, label=None, win=w))
        for r in recs:
            r.update(v='REC', t=round(t0 + r['t'], 4), beat=round(t0 + r['t'], 4), dbeats=r['d'], m=0, label=None, win=w, tag='%s — わたしの録音の実音' % tag)
            d['extras'].append(r)
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:22]) for s in d['sections']])
