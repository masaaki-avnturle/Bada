#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXVI · Symphonia per augmentationem (提出した 16 曲を LXV に合わせて、洗脳的な交響曲に)
  LXV の技法 (主題を 4 倍・8 倍・16 倍に伸ばし、伸ばした音をピアノで 4 分音符ごとに打ち直す — ♩=60、1 秒に 1 打、止まらない) を 4 つの楽章の骨組みにし、
  伸ばしている長い音の中で、提出された曲 (mp4 の音) が次々に鳴る。曲の調が楽章の調と違うときは、テープのように調を合わせる。
  楽章は切れ目なく続く (アタッカ):
    I.   Introduzione e Allegro ×4 (ニ短調 → イ短調の答え): symphony.mp4 の始まり → 主題 I ×4 (requiem_fuga_drill・tablet62) → ×4 イ短調 (requiem_fuga_small・symphony)
    II.  Adagio ×4 (ホ短調): acceptance → 主題 I ×4 (tablet46inst・tablet48inst) → 主題 I ×4 (tablet6・tablet49inst) → tablet61
    III. Scherzo luminoso ×8 (ハ長調): 主題 I の長調の形 ×8 (cp14_C_G_uplift・piano_solo_8x・cp14_C_G_uplift) — 合い間はピアノの 1 倍の主題
    IV.  Finale ×16 con Fuga (ニ短調): 主題 I ×16 の中に requiem_fuga_embrace・tablet (全音下げ)・cp14_x8_part3・tablet60 (短 3 度下げ)・LXV (同じ ×16 の所)、
         最後の 16 小節の主音の保続の中で主題 I・II・III の三重フーガをピアノで 2 回
    Coda (ニ長調): symphony.mp4 の終わりのニ長調 → Amen
  新しく足した音はすべて録音から切り出したピアノの実音 (bank61)。提出された曲はもとの音のまま (シンセ・ドラムを新しく足していない)。
  使い方: python compose_tablet66.py <bank61.json> <素材の wav があるフォルダ> [score_tablet66.json]
"""
import sys, os, json
import numpy as np, soundfile as sf
from compose import *
import compose
import compose_tablet as CT
import compose_tablet48 as K
import compose_tablet61 as LXI
import compose_tablet62 as LXII
import compose_tablet63 as LXIII
import compose_tablet65 as LXV

add = CT.add
BPM = 60
SRC = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else '.'
VOICE_SRC, DYNK = LXI.VOICE_SRC, LXI.DYNK
H1 = [c for bar in H_S1 for c in bar]
# 主題 I の長調の形 (エンジンのニ長調で書き、楽章の移調でハ長調へ): レ・ミ・ファ#・ソ・ラ・シ・ラ・ソ・ファ#・ミ・ド#・レ
S1M = mat(('D4', 3), ('E4', 1), ('F#4', 2), ('G4', 1), ('A4', 1), ('B4', 2), ('A4', 1), ('G4', 1), ('F#4', 2), ('E4', 1), ('C#4', 1), ('D4', 4))
H1M = sum([[c] * int(d) for c, (d, m) in zip(['D', 'A', 'D', 'G', 'D', 'G', 'D', 'Em', 'D', 'A', 'A7', 'D'], S1M)], [])
SWELL, AUD = [], []
_RMS = {}

def ex_gain(src, off, dur, semis=0):
    """抜粋がその曲全体よりどれだけ大きい / 小さいかで、どの抜粋も同じくらいの大きさに聞こえる倍率"""
    if src not in _RMS:
        y, sr = sf.read(os.path.join(SRC, src), dtype='float32'); _RMS[src] = (y, sr, float(np.sqrt((y ** 2).mean())) + 1e-9)
    y, sr, full = _RMS[src]; ratio = 2 ** (semis / 12.0)
    ex = y[int(off * sr):int((off + dur * ratio) * sr)]
    return float(np.clip(full / (np.sqrt((ex ** 2).mean()) + 1e-9), 0.5, 2.0))

def aug(P, f, k, subj, hl, label, skip=()):
    """主題を k 倍に: テノールは 4 分音符ごとに打ち直し、バスは小節の頭だけ (2 オクターヴ下)。和声も k 倍に伸ばす"""
    for i, c in enumerate(hl):
        for q in range(k): P.harm[f * BPB + i * k + q] = c
    t, tq, bq = 0, [], []
    for d, m in subj:
        for j in range(int(round(d * k))):
            if not any(a <= f * BPB + t + j < b for a, b in skip): tq.append((t + j, m - 12))
        for j in range(0, int(round(d * k)), BPB): bq.append((t + j, m - 24))
        t += int(round(d * k))
    for v, notes, dur, lab in (('T', tq, 1, label), ('B', bq, 4, '×%d (深い鐘)' % k)):
        n0 = len(P.entries)
        for s_, m in notes: P.place(v, f, [(dur, m)], 0, lab, beat=s_)
        del P.entries[n0 + 1:]
        cov = {int(s_ + x) for s_, m in notes for x in range(int(dur))}
        for bt in range(t):
            if bt not in cov: P.rest[v].add(f * BPB + bt)
    SWELL.append((f, f + t // BPB))
    return t // BPB

def build():
    total = (8 + 20 + 20) + (8 + 20 + 20 + 8) + 40 + 80 + (10 + 3)
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def lay(b0, n_, semis): CT.LAYOUT.append((b0, b0 + n_, semis, VOICE_SRC, {}))
    def audio(bars, title, sub, src, off, semis, tag, key_semis, fout=4.0, g=0.5):
        nonlocal b
        P.section(b, title, sub); AUD.append((b, bars, src, off, semis, g * ex_gain(src, off, bars * 4.0, semis), tag, fout))
        for v in VOICES: P.rest_bars(v, b, b + bars)
        P.set_harms(b, [['Dm'] * 4] * bars); lay(b, bars, key_semis); b += bars
    def inner(f, windows, key_semis):
        for b0, n_, src, off, semis, tag in windows:
            AUD.append((f + b0, n_, src, off, semis, 0.5 * ex_gain(src, off, n_ * 4.0, semis), tag, 3.0))
            for v in 'SA': P.rest_bars(v, f + b0, f + b0 + n_)
    def movement_aug(title, sub, k, subj, hl, semis, label, windows, dyn0, dyn1, arp=(), skip=()):
        nonlocal b
        f = b; P.section(f, title, sub); n_ = aug(P, f, k, subj, hl, label, skip); lay(f, n_, semis)
        for j in range(n_): P.dyn[f + j] = DYNK * (dyn0 + (dyn1 - dyn0) * j / max(1, n_ - 1))
        inner(f, windows, semis)
        for a0, a1 in arp: LXIII.ARP.append((f + a0, f + a1, 0.1, semis))
        b += n_; return f
    # ================= I. Introduzione e Allegro ×4 (ニ短調)
    audio(8, 'I. Introduzione — symphony.mp4 (ニ短調)', '交響曲の始まりの音のまま — ここから主題が 4 倍に伸びていく', 'symphony.wav', 0.0, 0, 'symphony.mp4 — 始まり', 0)
    movement_aug('I. Allegro per augmentationem ×4 (ニ短調)', '主題 I の 4 分音符が全音符に — 伸ばした音の中に requiem_fuga_drill と tablet62', 4, S1, H1, 0, '主題 I ×4',
                 [(0, 8, 'requiem_fuga_drill.wav', 1660.0, 0, 'requiem_fuga_drill.mp4'), (12, 8, 'tablet62.wav', 140.0, 0, 'tablet62.mp4 — LXII')], 0.62, 0.74, arp=[(8, 12)])
    movement_aug('I. ×4 — 答え (イ短調)', 'イ短調で主題 I ×4 — requiem_fuga_small と symphony.mp4 のイ短調の所', 4, S1, H1, 7 - 12, '主題 I ×4 (答え)',
                 [(0, 8, 'requiem_fuga_small.wav', 680.0, 0, 'requiem_fuga_small.mp4'), (12, 8, 'symphony.wav', 400.0, 0, 'symphony.mp4 — イ短調の所')], 0.7, 0.8, arp=[(8, 12)])
    # ================= II. Adagio ×4 (ホ短調)
    audio(8, 'II. Adagio — acceptance.mp4 (ホ短調)', 'BADA 528 Acceptance の音のまま — 涙のアダージョへ', 'acceptance.wav', 80.0, 0, 'acceptance.mp4 — BADA 528 Acceptance', 2)
    movement_aug('II. Adagio per augmentationem ×4 (ホ短調)', 'ホ短調で主題 I ×4 — 伸ばした音の中に tablet46inst と tablet48inst', 4, S1, H1, 2, '主題 I ×4 (ホ短調)',
                 [(0, 8, 'tablet46inst.wav', 60.0, 0, 'tablet46inst.mp4 — XLVI'), (12, 8, 'tablet48inst.wav', 80.0, 0, 'tablet48inst.mp4 — XLVIII')], 0.6, 0.66, arp=[(8, 12)])
    movement_aug('II. Adagio ×4 — 二度目 (ホ短調)', '主題 I ×4 をもう一度 — tablet6 と tablet49inst', 4, S1, H1, 2, '主題 I ×4 (ホ短調, 二度目)',
                 [(0, 8, 'tablet6.wav', 440.0, 0, 'tablet6.mp4 — Tablet Sessions VI'), (12, 8, 'tablet49inst.wav', 80.0, 0, 'tablet49inst.mp4 — XLIX')], 0.62, 0.7, arp=[(8, 12)])
    audio(8, 'II. Lacrimosa — tablet61.mp4 (ホ短調)', 'LXI のホ短調の所 — 打鍵がひととき止まる', 'tablet61.wav', 140.0, 0, 'tablet61.mp4 — LXI', 2)
    # ================= III. Scherzo luminoso ×8 (ハ長調)
    f = movement_aug('III. Scherzo luminoso per augmentationem ×8 (ハ長調)', '主題 I の長調の形を 8 倍に — 中に cp14_C_G_uplift・piano_solo_8x、合い間はピアノの 1 倍の主題', 8, S1M, H1M, -2,
                     '主題 I (長調) ×8',
                     [(0, 8, 'cp14_C_G_uplift.wav', 600.0, 0, 'cp14_C_G_uplift.mp4'), (16, 8, 'piano_solo_8x.wav', 1320.0, 0, 'piano_solo_8x.mp4'),
                      (32, 8, 'cp14_C_G_uplift.wav', 1740.0, 0, 'cp14_C_G_uplift.mp4 — 終わり近く')], 0.66, 0.78, arp=[(8, 16), (24, 32)])
    for w0 in (8, 24):                              # 合い間: ソプラノが 1 倍の主題 (長調) を歌い、アルトは休む
        P.place('S', f + w0, S1M, 12, '主題 I (長調) ×1' if w0 == 8 else None); P.rest_bars('A', f + w0, f + w0 + 8); P.rest_bars('S', f + w0 + 5, f + w0 + 8)
    # ================= IV. Finale ×16 con Fuga (ニ短調)
    f = b
    tri = [((f + 66) * BPB, (f + 69) * BPB), ((f + 73) * BPB, (f + 76) * BPB)]
    movement_aug('IV. Finale per augmentationem ×16 con Fuga (ニ短調)', '主題 I の 4 分音符を 16 倍 (4 小節) に — 中に requiem_fuga_embrace・tablet・cp14_x8_part3・tablet60・LXV、最後は三重フーガ', 16, S1, H1, 0,
                 '主題 I ×16 — 4 分音符を 16 倍に伸ばす',
                 [(0, 12, 'requiem_fuga_embrace.wav', 1040.0, 0, 'requiem_fuga_embrace.mp4 (レの中で)'), (12, 12, 'tablet.wav', 320.0, -2, 'tablet.mp4 — Tablet Sessions I (全音下げ)'),
                  (32, 8, 'cp14_x8_part3.wav', 1120.0, 0, 'cp14_x8_part3.mp4 (ラの保続の中で)'), (40, 8, 'tablet60.wav', 140.0, -3, 'tablet60.mp4 — LX (短 3 度下げ)'),
                  (56, 8, 'tablet65.wav', 360.0, 0, 'tablet65 — LXV の同じ ×16 の所 (レ・ド#)')], 0.66, 0.86, arp=[(24, 32), (48, 56)], skip=tri)
    for r0, (vs1, vs2, vs3, t1, t2, t3) in ((f + 64, ('A', 'S', 'T', 0, 12, -12)), (f + 71, ('S', 'A', 'T', 12, 0, -12))):
        P.set_harms(r0, H_TRIPLE)
        P.place(vs1, r0, S1, t1, '主題 I (三重フーガ)'); P.place(vs2, r0, S2, t2, '主題 II'); P.place(vs3, r0 + 2, S3, t3, '主題 III B-A-D-A')
    P.set_harms(f + 78, [['Dm'] * 4] * 2)
    # ================= Coda (ニ長調)
    audio(10, 'Coda — symphony.mp4 の終わり (ニ長調)', '交響曲の終わりのニ長調の音のまま', 'symphony.wav', 456.0, 0, 'symphony.mp4 — 終わり (ニ長調)', 0, fout=3.0)
    f = b; P.section(f, 'Amen — 変格終止 (ニ長調の和音で)', 'iv → I: 打鍵が止まり、ニ長調の和音だけが残る'); lay(f, 3, 0); b += 3
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

META = {k: v for k, v in LXI.META.items()}
META.update(
    rec_order=LXIII.ORDER,
    title='Requiem BADA — LXVI · Symphonia per augmentationem',
    subtitle='提出した 16 曲を LXV に合わせて — 主題を 4 倍・8 倍・16 倍に伸ばす洗脳的な交響曲 (4 楽章、♩=60)',
    legend=['PF'], vname={'PF': '分散和音'},
    footer=['I. ニ短調 ×4 → II. Adagio ホ短調 ×4 → III. Scherzo ハ長調 ×8 → IV. Finale ニ短調 ×16 con Fuga → Coda ニ長調',
            '伸ばした音を 1 拍ごとに打ち直す骨組みの中で、提出した曲が鳴る。新しい音はすべて録音から切り出したピアノの実音。'])

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet66.json'
    compose.main(out, seed=166, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * 1.25, 4)
    LXV.SWELL[:] = SWELL; LXV.swell(d); LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:22]) for s in d['sections']])
