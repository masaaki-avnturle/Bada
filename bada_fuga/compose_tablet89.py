#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXIX · Requiem e Fuga, recto e verso (cp14_x4 を伴奏に、9/23・9/24・9/28・9/29 の録音を化学合成して — レクイエムとフーガを表と裏に)
  伴奏: cp14_x4.mp4 (Contrapunctus BADA の 4 分音符を 4 倍に伸ばした 32 分、ニ短調) の音声から、ニ短調の濃い 4 つの窓を切り出して
    (0〜96 秒 / 720〜784 / 840〜936 / 1788〜1917 = 終わりまで)。表に出る楽章では大きく、裏に回る楽章では小さく。
  主題 (6 つ、録音の採譜の最上声から 8 拍、ニ短調に移して):
    9/23 08:06 (ヘ短調)・08:09 (ト長調 → ホ短調として)・9/24 08:53 (ロ短調)・9/28 06:42 (変イ長調 → ヘ短調として、歌 — 旋律だけをピアノで)・9/29 15:12・15:16 (変ロ短調)
  形式 (♩=60、ニ短調、96 小節 = 6 分 24 秒) — レクイエムとフーガが表と裏を入れ替える:
    I.   Requiem (表)   0〜24  主題 08:53・08:06・06:42 を 4 倍に伸ばして前で (2 拍ごとに息をするように打ち直す) ／ 裏: 08:09 の主題 (1 倍) が小さく入る
    II.  Fuga (表)     24〜40  08:09 の主題の 4 声フーガ (提示・下属調・ストレッタ・保続低音) ／ 裏: 06:42 ×4 が低く小さく、cp14_x4 も小さく
    III. Requiem (表)  40〜64  15:12・15:16・08:09 を 4 倍に ／ 裏: 15:12 の主題 (1 倍) が小さく
    IV.  Fuga (表)     64〜80  08:53 の主題の 4 声フーガ ／ 裏: 15:16 ×4 が低く小さく
    V.   Stretto       80〜92  6 つの主題が 2 小節ずつずれて次々に (表も裏も一つに) → Amen (ニ長調)  92〜96
  音源はピアノだけの録音の 1 音 (08:09・08:53・08:49・13:04・15:12・15:16)。高音はミ 5 まで。
  使い方: python compose_tablet89.py <bank89.json> <cp14_x4.wav> [score_tablet89.json]
"""
import sys, os, json
import numpy as np
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet63 as LXIII

CP14 = sys.argv[2]
RIDS = {'08:06': ('20260923_080607', 3), '08:09': ('20260923_080918', 2), '08:53': ('20260924_085314', -3),
        '06:42': ('20260928_064235', 3), '15:12': ('20260929_151249', -4), '15:16': ('20260929_151602', -4)}     # 録音 → (id, ニ短調への移調)
VOICE_SRC = {'S': '20260923_080918', 'A': '20260924_085314', 'T': '20260924_084937', 'B': '20260925_130431'}
DYNK = 1.3; CAP = 76
compose.RANGE.update({'S': (60, CAP), 'A': (55, 74), 'B': (40, 58)})
X = []                                             # 伸ばした主題 (extras)
G_FRONT, G_BACK = 1.0, 0.3                        # 伸ばした主題の表 / 裏
C_FRONT, C_BACK = 0.6, 0.25                        # cp14_x4 の表 / 裏
SUBJ = {}

def stretch(P, name, k, bar, v, front, cen=None):
    """主題を k 倍に伸ばして extras に (2 拍ごとに打ち直し、オクターヴを薄く重ねる)。和音は後で P.harm から見てぶつかる拍は打ち直さない"""
    s_ = SUBJ[name]; cen = cen or {'S': 69, 'A': 63, 'T': 56, 'B': 45}[v]
    oc = 12 * min(range(-3, 3), key=lambda o: abs(np.mean([m for _, m in s_]) + 12 * o - cen))
    X.append(('plan', name, s_, k, bar * BPB, v, oc, front))
    return bar + int(np.ceil(sum(d for d, _ in s_) * k / BPB))

def realize(P):
    out = []
    for _, name, s_, k, b0, v, oc, front in X:
        t = float(b0); first = True
        for d, m in s_:
            L = d * k; n_ = max(1, int(round(L / 2)))
            for i in range(n_):
                beat = t + 2 * i
                if beat >= len(P.harm) - 1: break
                pcs = set(chord(P.harm[int(beat)] or 'Dm')['pcs']); pc = m % 12
                if i and pc not in pcs and any(min((pc - p) % 12, (p - pc) % 12) == 1 for p in pcs): continue
                amp = 1.0 if i == 0 else 0.62 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1))
                mm = m + oc
                while mm > CAP: mm -= 12
                g0 = G_FRONT if front else G_BACK
                for o, g in ((0, 1.0), (-12, 0.4)) if v != 'B' else ((0, 1.0), (12, 0.4)):
                    out.append(dict(v='PF', t=round(beat, 3), d=2.9, m=mm + o, gain=round(g0 * g * amp, 4), rid=VOICE_SRC[v], rel=1.0, beat=round(beat, 3), dbeats=2.0,
                                    label='%s の主題 ×%d%s' % (name, k, '' if front else ' (裏)') if first else None, layer='front' if front else 'back'))
                    first = False
            t += L
    return out

def build():
    for name, (rid, semis) in RIDS.items():
        t0, inside = CT.excerpt(rid, semis, 13.0)
        s_ = LXIII.smooth(CT.make_subject(inside, semis, 60)); SUBJ[name] = s_; T5.SUBJ[rid] = (s_, CT.harmonize(s_))
        print('  %s (%s) from %.1fs: %s' % (name, rid, t0, ' '.join('%s:%g' % (name_of(m), d) for d, m in s_)))
    total = 96
    P = Piece(total)
    place0 = P.place
    def place_cap(v, bar, mat, semis=0, label=None, beat=0):          # ミ 5 を超える入りは、入りごとオクターヴ下へ
        ms = [m + semis for _, m in mat if m is not None]
        while ms and max(ms) > CAP and min(ms) - 12 >= 36: semis -= 12; ms = [m - 12 for m in ms]
        place0(v, bar, mat, semis, label, beat)
    P.place = place_cap
    for k in range(total): P.tempo[k] = 60; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, 0, VOICE_SRC, {}))
    def harm_stretch(b0, name, k):
        s_ = SUBJ[name]; T5.harm_from_entries(P, b0, b0 + int(np.ceil(sum(d for d, _ in s_) * k / BPB)), [(b0 * BPB, [(d * k, m) for d, m in s_])])
    def cp(bar0, bar1, off, gain, tag):
        CT.add('REC', bar0 * BPB, (bar1 - bar0) * BPB, 0, gain, None, src=CP14, off=float(off), fin=3.0, fout=3.0, rid='cp14_x4.wav', tag=tag)
    # I. Requiem (表)
    f = 0; P.section(f, 'I. Requiem (表) — 08:53・08:06・06:42 を 4 倍に', 'cp14_x4 (0 秒〜) の上で、伸ばした主題が前に — 裏で 08:09 の主題が小さく入る')
    for v in VOICES: P.rest_bars(v, 0, 24)
    cp(0, 24, 0.0, C_FRONT, 'cp14_x4 — 始まり (ニ短調)')
    P.set_harms(0, [['Dm'] * 4] * 2)
    harm_stretch(2, '08:53', 4); stretch(P, '08:53', 4, 2, 'S', True)
    harm_stretch(10, '08:06', 4); stretch(P, '08:06', 4, 10, 'T', True)
    harm_stretch(18, '06:42', 4)
    for b in range(18 * BPB, 24 * BPB):
        if P.harm[b] is None: P.harm[b] = 'Dm'
    stretch(P, '06:42', 4, 16, 'S', True)
    for bar, v in ((6, 'A'), (12, 'T'), (20, 'A')): stretch(P, '08:09', 1, bar, v, False)
    for k in range(24): P.dyn[k] = DYNK
    # II. Fuga (表)
    f = 24; P.section(f, 'II. Fuga (表) — 08:09 の主題の 4 声フーガ', '提示 → 下属調 → ストレッタ → 保続低音 ／ 裏: 06:42 ×4 が低く、cp14_x4 も小さく')
    cp(24, 40, 720.0, C_BACK, 'cp14_x4 — 12 分 (裏)')
    T11.bach_fugue(P, f, RIDS['08:09'][0], '08:09')
    stretch(P, '06:42', 4, 26, 'B', False)
    for k in range(16): P.dyn[f + k] = DYNK * (0.85 + 0.15 * k / 15)
    # III. Requiem (表)
    f = 40; P.section(f, 'III. Requiem (表) — 15:12・15:16・08:09 を 4 倍に', 'cp14_x4 (14 分〜) の上で ／ 裏: 15:12 の主題が小さく')
    for v in VOICES: P.rest_bars(v, 40, 64)
    cp(40, 64, 840.0, C_FRONT, 'cp14_x4 — 14 分 (ニ短調)')
    harm_stretch(42, '15:12', 4); stretch(P, '15:12', 4, 42, 'S', True)
    harm_stretch(50, '15:16', 4); stretch(P, '15:16', 4, 50, 'T', True)
    harm_stretch(56, '08:09', 4); stretch(P, '08:09', 4, 56, 'S', True)
    for b in range(40 * BPB, 64 * BPB):
        if P.harm[b] is None: P.harm[b] = 'Dm'
    for bar, v in ((46, 'A'), (54, 'A'), (60, 'T')): stretch(P, '15:12', 1, bar, v, False)
    # IV. Fuga (表)
    f = 64; P.section(f, 'IV. Fuga (表) — 08:53 の主題の 4 声フーガ', '提示 → 下属調 → ストレッタ → 保続低音 ／ 裏: 15:16 ×4 が低く、cp14_x4 (終わりの 2 分) も小さく')
    cp(64, 96, 1788.0, C_BACK, 'cp14_x4 — 終わりの 2 分 (裏 → 表)')
    T11.bach_fugue(P, f, RIDS['08:53'][0], '08:53')
    stretch(P, '15:16', 4, 66, 'B', False)
    for k in range(16): P.dyn[f + k] = DYNK * (0.9 + 0.1 * k / 15)
    # V. Stretto → Amen
    f = 80; P.section(f, 'V. Stretto — 6 つの主題が次々に (表も裏も一つに)', '2 小節ずつずれて 08:06 → 08:09 → 08:53 → 06:42 → 15:12 → 15:16 → Amen (ニ長調)')
    ents = []
    for k, (name, v, tr) in enumerate((('08:06', 'B', -24), ('08:09', 'T', -12), ('08:53', 'A', 0), ('06:42', 'S', 0), ('15:12', 'T', -12), ('15:16', 'S', 0))):
        bar = f + 2 * k; s_ = SUBJ[name]
        P.place(v, bar, [(d, m + tr) for d, m in s_], 0, '%s (ストレッタ)' % name); ents.append((bar * BPB, [(d, m + tr) for d, m in s_]))
    for bar in range(f, f + 12): T5.harm_from_entries(P, bar, bar + 1, [e for e in ents if e[0] - 2 * BPB < bar * BPB < e[0] + 2 * BPB] or ents[-1:])
    for k in range(12): P.dyn[f + k] = DYNK * 1.05
    f = 92; P.section(f, 'Amen — ニ長調', 'iv → V → I')
    P.set_harms(f, [['Gm', 'Gm', 'A7', 'A7'], ['D'], ['D'], ['D']])
    P.place('S', f, [(2, n('Bb4')), (2, n('A4')), (12, n('A4'))], 0, 'Amen')
    for k in range(4): P.dyn[f + k] = DYNK * (0.7 - 0.1 * k)
    LXIII.ARP.append((f, f + 3, 0.08, 0))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': list(VOICE_SRC.values()), 'piano_decay': 2.4, 'reverb': [6.0, 2.3, 0.48],
    'title': 'Requiem BADA — LXXXIX · Requiem e Fuga, recto e verso',
    'subtitle': 'cp14_x4 を伴奏に、9/23・9/24・9/28・9/29 の 6 つの主題を — レクイエムとフーガを表と裏に (ニ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': '主題 ×4'},
    'footer': ['I. Requiem (表: 08:53・08:06・06:42 ×4) → II. Fuga (08:09) → III. Requiem (15:12・15:16・08:09 ×4) → IV. Fuga (08:53) → V. Stretto (6 つ) → Amen',
               '伴奏は cp14_x4 (Contrapunctus BADA ×4) の 4 つの窓。すべてピアノの実音。高音はミ 5 まで。'],
}

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet89.json'
    PP = {}
    def builder():
        P = build(); PP['P'] = P; return P
    compose.main(out, seed=189, bpm=60, builder=builder, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    K.BPM = 60; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * (1.3 if n_.get('label') else 1.1), 4)
    ex = realize(PP['P']); d['extras'] += ex
    d['entries'] += [dict(t=e['t'], label=e['label'], v='S' if e['layer'] == 'front' else 'B') for e in ex if e.get('label')]
    for e in ex: e['label'] = None
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras'] if e['v'] == 'PF']
    print('duration', round(d['duration'], 1), 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
