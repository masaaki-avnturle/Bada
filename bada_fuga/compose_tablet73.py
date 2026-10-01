#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXIII · Requiem a tre soggetti (9/24 08:49・08:53、9/23 08:09 の 3 本を主題曲に、それぞれ 16 倍に伸ばし、LXXII をバックに — 三重フーガのレクイエム)
  主題曲 (ピアノの実音) と、その最上声から作った 3 つの主題 (8 拍):
    主題 A  9/24 08:49 (ヘ短調): ファ・ラ♭・シ♭・レ♭・ファ と上る
    主題 B  9/24 08:53 (ホ短調): ミ・ファ#・シ・ミ・ミ と上る
    主題 C  9/23 08:09 (ホ短調): シ・ラ・シ・ソ・ド・ミ (LXIX の主題)
  16 倍の伸び: I 楽章は A、II 楽章は B、IV 楽章は C を 16 倍 (4 分音符が 4 小節) に。テノールが 4 分音符ごとに打ち直し (♩=60)、深い鐘は 2 全音符ごと。
  バック: LXXII (先程の曲、ヘ短調)。ヘ短調の I 楽章では音をそのまま、ホ短調の II・IV 楽章では採譜して 1 半音下げ、ピアノの実音で弾き直す。
    伸ばした長い音と同じ働きの所 (主音・属音・VI の保続) を LXXII から選んで重ねる。
  フーガを醸す: 各 ×16 の頭で主題 → 5 度上の答え、長い音の上でストレッタ、最後の主音の上で 1 倍と 2 倍 (拡大) の主題。
    III 楽章は三重フーガ (コントラプンクトゥス XIV のように) — A・B・C を順に提示し、最後に 3 つを同時に重ねる。
  形式 (♩=60): Introitus (08:49, ヘ短調) → I. Requiem ×16 (A, ヘ短調) → Interludium (08:53 の実音、半音下のホ短調へ)
    → II. ×16 (B, ホ短調) → III. Fuga a tre soggetti (ホ短調) → IV. Finale ×16 (C, ホ短調) → Amen (ホ長調)
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet73.py <bank73.json> <素材の wav フォルダ (3 本の録音・tablet72.wav)> [score_tablet73.json]
          python compose_tablet67.py level <score_tablet73.json> <LXXII を弾き直した所だけの wav> <peak> 0.055
"""
import sys, os, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet63 as LXIII
import compose_tablet65 as LXV
import compose_tablet69 as LXIX
import compose_tablet70 as LXX

add, hm = CT.add, CT.hm
BPM = 60
SRC, OUT = LXX.SRC, LXX.OUT
RA, RB, RC = '20260924_084937', '20260924_085314', '20260923_080918'
FM, EM = 3, 2
KEY = {RA: FM, RB: EM, RC: EM}
NAME = {RA: 'A (08:49)', RB: 'B (08:53)', RC: 'C (08:09)'}
HB = {RA: ['Dm', 'Dm', 'Gm', 'Gm', 'Bb', 'Dm', 'Dm', 'Dm'],          # 1 拍ごとの和音 (エンジンのニ短調)
      RB: ['Dm', 'A7', 'A7', 'A7', 'A7', 'Dm', 'Dm', 'Dm'],
      RC: ['A7', 'A7', 'Dm', 'Dm', 'Bb', 'Bb', 'Gm', 'Dm']}
VOICE_SRC = {'S': RC, 'A': RB, 'T': RA, 'B': '20260925_124643'}
DYNK = 1.3
AUD, BACK = [], []

def build():
    for r in (RA, RB, RC):
        t0, inside = CT.excerpt(r, KEY[r], 13.0); s_ = LXIII.smooth(CT.make_subject(inside, KEY[r], BPM))
        T5.SUBJ[r] = (s_, [HB[r][:4], HB[r][4:]]); print(NAME[r], ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = 8 + 32 + 6 + 32 + 24 + 32 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    src = lambda r: os.path.join(SRC, r + '.wav'); l72 = os.path.join(SRC, 'tablet72.wav')
    def lay(b0, n_, semis): CT.LAYOUT.append((b0, b0 + n_, semis, VOICE_SRC, {}))
    def window(b0, n_, path, off, tag, g=0.6):
        AUD.append((b0, n_, path, off, g * LXIX.ex_gain(path, off, n_ * 4.0), tag, 3.0))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def back(b0, n_, off, semis, tag):
        if semis == 0: window(b0, n_, l72, off, tag, g=0.32)        # 同じ調: 音をそのまま
        else:
            BACK.append((b0, n_, off, semis, tag))
            for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def audio(n_, title, sub, r, off, tag, semis):
        nonlocal b
        P.section(b, title, sub); window(b, n_, src(r), off, tag)
        for v in VOICES: P.rest_bars(v, b, b + n_)
        P.set_harms(b, [['Dm'] * 4] * n_); lay(b, n_, semis); b += n_
    def entry(r, v, bar, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in T5.SUBJ[r][0]], 0, lab)
    def requiem16(r, title, sub, wins, backs, stretto, dyn0, dyn1, final_extra=None):
        nonlocal b
        s_, H = T5.SUBJ[r]; f = b; P.section(f, title, sub)
        n_ = LXIX.aug(P, f, 16, s_, HB[r], '主題 %s ×16 — 4 分音符を 16 倍に' % NAME[r]); lay(f, n_, KEY[r])
        for j in range(32): P.dyn[f + j] = DYNK * (dyn0 + (dyn1 - dyn0) * j / 31)
        P.set_harms(f, H); entry(r, 'A', f, 0, '主題 %s ×1 — フーガ' % NAME[r]); P.set_harms(f + 2, transpose_h(H, 7)); entry(r, 'S', f + 2, 7 - 12, '答え (5 度上)')
        for b0, nn, path, off, tag in wins: window(f + b0, nn, path, off, tag)
        for b0, nn, off, semis, tag in backs: back(f + b0, nn, off, semis, tag)
        P.set_harms(f + stretto, H); entry(r, 'S', f + stretto, 0, '主題 %s ストレッタ' % NAME[r])
        if stretto + 3 <= 28: entry(r, 'A', f + stretto + 1, -12, None)      # 最後の拡大と重ならない時だけアルトも
        P.set_harms(f + 28, [[HB[r][2 * i]] * 2 + [HB[r][2 * i + 1]] * 2 for i in range(4)])
        entry(r, 'A', f + 28, -12, '主題 %s ×2 (拡大) + ×1' % NAME[r], k=2)
        if final_extra: final_extra(f)
        else: entry(r, 'S', f + 28, 0, None); entry(r, 'S', f + 30, 0, None)
        LXIII.ARP.append((f + stretto, f + stretto + 2, 0.09, KEY[r]))
        b += n_
    # ================= Introitus (08:49, ヘ短調)
    audio(8, 'Introitus — 主題曲 A 9/24 08:49 の実音 (ヘ短調)', '3 本の主題曲の 1 本目 — ピアノの実音のまま', RA, 0.0, '主題曲 A 9/24 08:49 — 始まり', FM)
    # ================= I. ×16 (A, ヘ短調: レ 8 · ファ 2 · ソ 2 · シ♭ 8 · レ 12 → ファ・ラ♭・シ♭・レ♭・ファ)
    requiem16(RA, 'I. Requiem per augmentationem ×16 — 主題 A (ヘ短調)', '08:49 の主題を 16 倍に — 長い音の中に、主題曲 A の実音・LXXII (そのまま)・主題のフーガ',
              [(8, 4, src(RA), 50.0, '主題曲 A 9/24 08:49 (ラ♭・シ♭ の中で)'), (20, 4, src(RA), 90.0, '主題曲 A 9/24 08:49 (主音の中で)')],
              [(4, 4, 80.0, 0, 'LXXII — 主音ファの所 (主音の中で)'), (12, 6, 112.0, 0, 'LXXII — レ♭ の所 (レ♭ の中で)')], 24, 0.62, 0.8)
    # ================= Interludium (08:53, ホ短調へ)
    audio(6, 'Interludium — 主題曲 B 9/24 08:53 の実音 (ホ短調)', '半音下のホ短調へ — 2 本目の主題曲', RB, 30.0, '主題曲 B 9/24 08:53', EM)
    # ================= II. ×16 (B, ホ短調: レ 4 · ミ 12 · ラ 6 · レ 6 · レ 4 → ミ・ファ#・シ・ミ・ミ)
    requiem16(RB, 'II. Adagio per augmentationem ×16 — 主題 B (ホ短調)', '08:53 の主題を 16 倍に — 長い音の中に、主題曲 B・C の実音・LXXII (1 半音下げてピアノで)・主題のフーガ',
              [(4, 4, src(RB), 70.0, '主題曲 B 9/24 08:53 (ファ# の中で)'), (16, 4, src(RC), 100.0, '主題曲 C 9/23 08:09 (属音シの中で)')],
              [(8, 8, 48.0, -1, 'LXXII — 属和音の所 (ファ# の中で)'), (22, 4, 136.0, -1, 'LXXII — 主音の所 (ミの中で)')], 26, 0.64, 0.82)
    # ================= III. Fuga a tre soggetti (ホ短調)
    f = b; P.section(f, 'III. Fuga a tre soggetti (ホ短調)', '主題 A・B・C を順に提示し、最後に 3 つを同時に重ねる三重フーガ (コントラプンクトゥス XIV のように)'); lay(f, 24, EM)
    T5.expo(P, f, RA, 'A'); T5.expo(P, f + 8, RB, 'B')
    s_c, H_c = T5.SUBJ[RC]
    P.set_harms(f + 16, H_c); entry(RC, 'A', f + 16, 0, '主題 C (08:09)'); P.rest_bars('S', f + 16, f + 18)
    P.set_harms(f + 18, transpose_h(H_c, 7)); entry(RC, 'S', f + 18, 7, '主題 C 答唱')
    for k, (va, vb, vc, ta, tb, tc) in enumerate((('B', 'T', 'S', -24, -12, 0), ('S', 'A', 'B', 0, -12, -24))):
        bar = f + 20 + 2 * k
        entry(RA, va, bar, ta, '三重結合: 主題 A' if k == 0 else None); entry(RB, vb, bar, tb, '主題 B' if k == 0 else None); entry(RC, vc, bar, tc, '主題 C' if k == 0 else None)
        ents = [(bar * BPB, [(d, m + t) for d, m in T5.SUBJ[r][0]]) for r, t in ((RA, ta), (RB, tb), (RC, tc))]
        T5.harm_from_entries(P, bar, bar + 2, ents)
    for j in range(24): P.dyn[f + j] = DYNK * (0.7 + 0.15 * j / 23)
    b += 24
    # ================= IV. Finale ×16 (C, ホ短調: ラ 2 · ソ 2 · ラ 12 · ファ 6 · シ♭ 6 · レ 4 → シ・ラ・シ・ソ・ド・ミ)
    def finale_extra(f):                           # 最後の主音の上で、主題 A と C がソプラノに (アルトは C の 2 倍)
        entry(RA, 'S', f + 28, 0, '主題 A (最後)'); entry(RC, 'S', f + 30, 0, '主題 C (最後)')
    requiem16(RC, 'IV. Finale per augmentationem ×16 — 主題 C (ホ短調)', '08:09 の主題を 16 倍に — LXXII (1 半音下げ)・主題曲 C の実音、最後は 3 つの主題が集まる',
              [(16, 6, src(RC), 150.0, '主題曲 C 9/23 08:09 (ソの中で)')],
              [(4, 8, 272.0, -1, 'LXXII — Finale の属和音の所 (属音シの中で)'), (22, 6, 336.0, -1, 'LXXII — Finale のレ♭ の所 (ドの中で)')], 12, 0.72, 0.9, finale_extra)
    # ================= Amen (ホ長調)
    f = b; P.section(f, 'Amen — 変格終止 (ホ長調の和音で)', 'iv → I: 打ち直しが止まり、ホ長調の和音だけが残る'); lay(f, 3, EM); b += 3
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

def rid_for(m): return VOICE_SRC['S'] if m >= 72 else VOICE_SRC['A'] if m >= 60 else VOICE_SRC['T'] if m >= 48 else VOICE_SRC['B']

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [RA, RB, RC], 'piano_decay': 1.8, 'reverb': [4.8, 1.7, 0.42],
    'title': 'Requiem BADA — LXXIII · Requiem a tre soggetti',
    'subtitle': '9/24 08:49・08:53、9/23 08:09 を主題曲に、16 倍に伸ばし、LXXII をバックに — 三重フーガのレクイエム (♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['Introitus (A) → I. ×16 (A, ヘ短調) → Interludium (B) → II. ×16 (B, ホ短調) → III. 三重フーガ → IV. ×16 (C) → Amen (ホ長調)',
               '主題曲は 3 本の録音。バックは LXXII (I 楽章はそのまま、II・IV 楽章は 1 半音下げてピアノで)。すべてピアノの実音。'],
}

if __name__ == '__main__':
    compose.main(OUT, seed=173, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(OUT)
    K.BPM = BPM; K.fix_voices(OUT)
    d = json.load(open(OUT)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if n_['v'] in 'SA' and (lab.startswith('主題') or lab.startswith('答え') or lab.startswith('三重')) else 1.25), 4)
    LXV.SWELL[:] = LXIX.SWELL; LXV.swell(d); LXII.fix_pulse(d)
    bt = d['bar_times']; l72 = os.path.join(SRC, 'tablet72.wav')
    for w, (b0, n_, off, semis, tag) in enumerate(BACK):
        t0 = bt[b0]; dur = n_ * BPB * 60.0 / BPM + 1.0
        notes = LXX.playable([(t, dd, m + semis, v) for t, dd, m, v in LXX.transcribe(l72, off, off + dur)])
        d['extras'].append(dict(v='REC', t=t0, d=dur, beat=b0 * BPB, dbeats=dur, m=0, gain=0.0, src=l72, off=off, fin=0.1, fout=0.5,
                                rid='tablet72.wav', tag='%s → 1 半音下げてピアノで' % tag, label=None))
        for t, dd, m, v in notes:
            d['extras'].append(dict(v='PF', t=round(t0 + t, 4), d=round(max(0.12, dd), 4), beat=round(t0 + t, 4), dbeats=round(dd, 4),
                                    m=int(m), gain=round(0.18 * v, 4), rid=rid_for(m), rel=0.45, label=None, win=w))
        print('back %d  %-40s notes %d' % (w, tag[:40], len(notes)))
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:24]) for s in d['sections']])
