#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXI · Requiem e Fuga con la band (プロのバンドの楽曲の雰囲気に、9/29・9/25 の録音を合わせたレクイエムとフーガ)
  参考にしたプロの楽曲 (LUNA SEA「MOTHER」ほか、アルバムのトラック 4・8・14・17・18) は、音そのものも旋律も使っていない。
  解析で得た「雰囲気」だけを借りる (analysis: 調・速さ・音量の山・音の厚み):
    - MOTHER: ホ短調、♩≈68 のバラード、低音が厚く、曲の 8 割の所でいちばん大きくなり、最後は静かに消える
      → この曲の調 (ホ短調)・速さ (♩=68)・音量の山 (Fuga II のストレッタが山、Amen で静まる) に
    - トラック 4: ホ長調、♩≈136 の長く静かな曲 → フーガの 8 ビートは ♩=136 で数え、最後の Amen はホ長調の和音で
  録音 (主題・音はすべてここから): 9/29 15:12 (変ロ短調)、15:16 (変ロ短調)、15:20 (ホ短調)、9/25 12:46 (ヘ短調)、12:50 (ロ短調)、13:04 (変ホ短調)。
  4 声は録音から切り出したピアノの 1 音 (実音) を鳴らすサンプラー。シンセ・心臓の鼓動・弦・オルガンなし。
  ドラム (synth.py の acoustic_drum): ドラマーが叩くロックのビート — バスドラムの役は大太鼓 (響きを短く止める)、スネア、暗く小さいハイハット、タムのフィル。
    バラード (Requiem) はハーフタイム、フーガは 8 ビート、Introitus・Lacrimosa・Amen の終わりはドラムなし (Amen の頭に一打だけ)。
  形式 (♩=68):
    Introitus (15:20 の実音, ホ短調) → Requiem aeternam (バラード: 12:50・13:04 の主題を 2 倍の長さでコラールに, ホ短調)
    → Fuga I (15:12 の主題, 変ロ短調) → Lacrimosa (15:16 の実音, 変ロ短調) → Fuga II (15:20 の主題, ホ短調, ストレッタが曲の山)
    → Amen (変格終止 → ホ長調)
  使い方: python compose_tablet61.py <bank61.json> [score_tablet61.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11
import compose_tablet48 as K                       # fix_voices (自動の声部の半音のぶつかり・連続 8 度 / 5 度を直す)

add, hm = CT.add, T3.hm
BPM = 68
R12, R16, R20 = '20260929_151249', '20260929_151602', '20260929_152002'
Q46, Q50, Q04 = '20260925_124643', '20260925_125053', '20260925_130431'
KEYS = {R12: -4, R16: -4, R20: 2, Q46: 3, Q50: -3, Q04: 1}          # ニ短調からの移調 (録音の調)
T7.KEYS.update(KEYS)
ORDER = [R20, R12, R16, Q50, Q04, Q46]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥')))
VOICE_SRC = {'S': Q04, 'A': R16, 'T': R12, 'B': Q46}
DYNK = 1.3
ROCK, FILL, HITS = [], [], []                      # ROCK: (b0, b1, 大きさ, 'full' / 'half')

def bass(t, g): add('AD', t, 0.5, 36, g, None, kind='odaiko', damp=0.45)
def post(P, events, extras):
    for b0, b1, lvl, mode in ROCK:
        for bar in range(b0, b1):
            if bar in FILL: continue
            B = bar * BPB
            for h in range(2):                     # ♩=136 の 1 小節 = ♩=68 の 2 拍
                o = B + 2 * h
                if mode == 'full':
                    bass(o, lvl); bass(o + 1.0, lvl * 0.9)
                    if h == 1: bass(o + 1.25, lvl * 0.7)
                    for t in (0.5, 1.5): add('AD', o + t, 0.3, 38, lvl * 0.8, None, kind='snare')
                else:                              # ハーフタイム (バラード): 大太鼓は 1 拍目、スネアは 3 拍目だけ
                    bass(o, lvl)
                    add('AD', o + 1.0, 0.3, 38, lvl * 0.75, None, kind='snare')
                for k in range(4): add('AD', o + 0.5 * k, 0.05, 42, lvl * (0.16 if k % 2 == 0 else 0.1), None, kind='hat')
            if mode == 'full' and (bar - b0) % 4 == 3 and bar + 1 < b1:     # 4 小節ごとの短いフィル (タム → フロアタム)
                for k, kd in enumerate(('tom', 'tom', 'tom', 'tom', 'floor', 'floor', 'floor', 'floor')):
                    add('AD', B + 2 + 0.25 * k, 0.3, 36, lvl * (0.55 + 0.05 * k), None, kind=kd)
    for bar in FILL:                               # 区間の終わりの長いフィル (8 分 → 16 分)
        B = bar * BPB; lvl = next(l for b0, b1, l, m in ROCK if b0 <= bar < b1)
        seq = [(0, 'snare'), (0.5, 'snare'), (1, 'tom'), (1.5, 'tom')] + [(2 + 0.25 * k, ('tom', 'tom', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor')[k]) for k in range(8)]
        for t, kd in seq: add('AD', B + t, 0.3, 36, lvl * (0.6 + 0.3 * t / 4), None, kind=kd)
        bass(B, lvl)
    for bar, lvl in HITS:                          # 大太鼓とフロアタムの一打
        add('AD', bar * BPB, 1.5, 36, lvl, None, kind='odaiko'); add('AD', bar * BPB, 1.0, 36, lvl * 0.6, None, kind='floor')

def subj(r): return T5.SUBJ[r][0]
def aug(mat_, k=2): return [(d * k, m) for d, m in mat_]
def place(P, bar, mat_, label):
    ms = [m for _, m in mat_ if m is not None]; tr = 0
    while max(ms) + tr > 77: tr -= 12
    while min(ms) + tr < 60: tr += 12
    P.place('S', bar, mat_, tr, label)

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = CT.make_subject(inside, KEYS[r], BPM); T5.SUBJ[r] = (s_, CT.harmonize(s_))
        print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = 4 + 8 + 16 + 4 + 16 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def excerpt(rid, bars, title, sub, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, bpm=BPM, gmul=0.6)
        for v in VOICES: P.rest_bars(v, b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, KEYS[rid], {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, VOICE_SRC, {})); b += bars; return f
    # ================= Introitus (15:20 の実音)
    excerpt(R20, 4, 'Introitus — %s の実音 (ホ短調)' % hm(R20), '9/29 15:20 のピアノの実音 (録音) — バンドの前の静けさ')
    # ================= Requiem aeternam (バラード)
    f = section('Requiem aeternam — バラード (ホ短調)', '%s・%s の主題を 2 倍の長さで、ピアノの 4 声のコラールに — 5 小節目からドラムがハーフタイムで' % (hm(Q50), hm(Q04)), 8, 2)
    for k, r in enumerate([Q50, Q04]):
        place(P, f + 4 * k, aug(subj(r)), 'コラール (%s) · 2 倍' % hm(r))
        T5.harm_from_entries(P, f + 4 * k, f + 4 * k + 4, [((f + 4 * k) * BPB, aug(subj(r)))])
    for k in range(8): P.dyn[f + k] = DYNK * (0.62 if k < 4 else 0.74)
    ROCK.append((f + 4, f + 8, 0.085, 'half')); FILL.append(f + 7)
    # ================= Fuga I (15:12 の主題, 変ロ短調)
    f = section('Fuga I (変ロ短調)', '%s の主題の 4 声フーガ — 2 声目の入りの後から 8 ビート (♩=136 で数えて)' % hm(R12), 16, -4)
    n_ = T11.bach_fugue(P, f, R12, '①')
    for k in range(n_): P.dyn[f + k] = DYNK * 0.74
    ROCK.append((f + 2, f + 16, 0.1, 'full')); FILL.append(f + 15)
    # ================= Lacrimosa (15:16 の実音)
    excerpt(R16, 4, 'Lacrimosa — %s の実音 (変ロ短調)' % hm(R16), '9/29 15:16 のピアノの実音 (録音) — ドラムは止まり、涙の日の静けさ')
    # ================= Fuga II (15:20 の主題, ホ短調)
    f = section('Fuga II (ホ短調)', '%s の主題のフーガ — すぐに 8 ビート、最後のストレッタが曲の山' % hm(R20), 16, 2)
    n_ = T11.bach_fugue(P, f, R20, '②')
    for k in range(n_): P.dyn[f + k] = DYNK * (0.78 if k < 12 else 0.86)
    ROCK.append((f + 1, f + 16, 0.11, 'full')); FILL.append(f + 15)
    # ================= Amen (変格終止 → ホ長調)
    f = section('Amen — 変格終止 (ホ長調の和音で)', 'iv → I: 大太鼓の一打のあと、ピアノだけが長調の和音で静かに閉じる', 3, 2)
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    HITS.append((f, 0.13))
    for k in range(3): P.dyn[f + k] = DYNK * 0.7
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.8, 'reverb': [4.8, 1.7, 0.42],
    'title': 'Requiem BADA — LXI · Requiem e Fuga',
    'subtitle': 'プロのバンドのバラードの雰囲気 (ホ短調 ♩=68) に、9/29・9/25 の録音のピアノの実音で',
    'legend': ['TB', 'AD'], 'vname': {'AD': 'ドラム'},
    'footer': ['Introitus 15:20 → Requiem (バラード) → Fuga I (15:12) → Lacrimosa 15:16 → Fuga II (15:20) → Amen (ホ長調)',
               '4 声は録音から切り出したピアノの実音。プロの楽曲からは調・速さ・音量の山だけを借りた (音と旋律は使っていない)。シンセなし。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet61.json'
    compose.main(out, seed=161, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LX と同じ)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), Counter(e.get('kind') for e in d['extras'] if e['v'] == 'AD'), 'notes', len(d['notes']))
