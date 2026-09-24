#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Vox · Rock (わたしの声とタブレットのピアノの、洗脳的なロックのレクイエムとフーガ, イ短調, ♩=80)
  9/23・9/24 のタブレットのピアノ録音 7 本の旋律を、ロックバンド (ドラム・シンセベース・ギター) とシンセサイザーの上の
  レクイエムとフーガにする。作曲者の歌声 (extract_voice.py で取り出し、feminize_voice.py で大げさにせず女性的に・音程を整えたもの) を、
  エコー (残響) をかけずに、乾いたきれいな声で前に置く。後ろのコーラスは同じ歌声の 1 音を正確な音程で 3 声に重ねたもの。
    Intro — タブレットのピアノ録音 11:23 の実音 → 鼓動のようなキックとパッド
    Verse I — 歌声 (乾いた声) とバンド。和音は歌声の音に合わせて 1 小節ごとに
    Chorus I — Fuga: 9/23 08:09 の旋律の 4 声フーガ (タブレットのピアノの音) + ギター + コーラス
    Verse II — 歌声とバンド
    Chorus II — Fuga: 7 本の旋律が 1 小節おきに次々と (上の声はシンセのリードが重なる)
    Bridge — 9/23 08:09 の実音、バンドは鼓動だけ
    Mantra — B-A-D-A ×4 をコーラスと 4 声で、バンド全開、歌声が重なる → イ長調の和音で終わる
  使い方: python compose_rockvox.py <piano_bank.json> <fem_voice_bank.json> [score_rockvox.json]
"""
import sys, json, math, os
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT          # ピアノ録音 (argv[1])、主題、移調
import compose_tablet5 as T5         # 実音の区間、フーガの提示、主題からの和声

add, REC = CT.add, CT.REC
INST = '--instrumental' in sys.argv                          # 声・歌声・コーラスなしの版 (Verse は洗脳的なシンセのリフ)
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
VB = {'recordings': {}, 'samples': []} if INST else json.load(open(ARGS[1]))
BPM = 80; BAR_S = 240.0 / BPM
SEMIS = -5                                                   # イ短調 (ニ短調から)。女性的にした歌はハ長調 = イ短調の平行調
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2,
        '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
PIANO = sorted(r for r in REC if r in KEYS)
MARK = '①②③④⑤⑥⑦'
BAND = []                                                    # (開始小節, 終了小節, 強さ 0〜2)
CHOIR = []                                                   # (開始小節, 終了小節) — 後ろのコーラス
RIFF = []                                                    # (開始小節, 終了小節, 大きさ) — シンセ・リードのリフ
LOOP = [['Dm'], ['Bb'], ['Gm'], ['A7']]                       # リフの 4 小節の和声 (イ短調で Am - F - Dm - E7) を繰り返す
VOICE_SRC = {'S': '20260923_080918', 'A': '20260924_085314', 'T': '20260924_084937', 'B': '20260923_080607'}

def hm(r): return '%d/%d %s:%s' % (int(r[4:6]), int(r[6:8]), r[9:11], r[11:13])

def phrases():
    out = []
    for r, x in VB['recordings'].items():
        ph = [p for p in x['phrases'] if p['voiced'] >= 0.6 and 1.8 <= p['d'] <= 7.5 and p['rms'] >= 0.35]
        out += [(r, p) for p in sorted(sorted(ph, key=lambda p: -p['rms'] * p['voiced'])[:10], key=lambda p: p['t'])]
    return out

def vnotes(r, p):
    return [(t - p['t'], d, m) for t, d, m in VB['recordings'][r]['notes'] if p['t'] <= t < p['t'] + p['d']]

def NB(p): return max(1, math.ceil((p['d'] + 0.4) / BAR_S))

def voice(P, bar, r, p, gain=1.3, harm=True):
    """歌声 (乾いた声、残響なし) を bar 小節目から。伸ばした音は表示用、和音は歌声の音に合わせる"""
    nb = NB(p)
    add('REC', bar * BPB, (p['d'] + 0.3) * BPM / 60.0, 0, gain, None, src=VB['recordings'][r]['file'], off=max(0, p['t'] - 0.1), rid=r,
        fin=0.06, fout=0.25, dry=True, tag='わたしの声 %s (乾いた声)' % hm(r))
    vn = vnotes(r, p)
    for t, d, m in vn: add('TB', bar * BPB + (t + 0.1) * BPM / 60.0, d * BPM / 60.0, m - SEMIS, 0.0, None)
    if harm:
        for k in range(nb):
            a, z = k * BAR_S, (k + 1) * BAR_S
            w = [(min(z, t + d) - max(a, t), m - SEMIS) for t, d, m in vn if min(z, t + d) > max(a, t)]
            cs = max(CT.CANDS, key=lambda c: sum(x * (1 if int(round(m)) % 12 in chord(c)['pcs'] else -0.9) for x, m in w)) if w else 'Dm'
            for q in range(BPB): P.harm[(bar + k) * BPB + q] = cs
    return nb

def near(pc, target):
    return min((x for x in range(24, 100) if x % 12 == pc), key=lambda x: abs(x - target))

def post(P, events, extras):
    """バンド (ドラム・シンセベース・ギター・パッド・タブレットのピアノの分散和音) とコーラスを、和声 (P.harm) に合わせて置く"""
    pr = PIANO[-1]
    for b0, b1, lv in BAND:
        for bar in range(b0, b1):
            B0 = bar * BPB; h = P.harm[B0] or 'Dm'; c = chord(h)
            add('PD', B0, 4.0, near(c['root'], 57), 0.10, None); add('PD', B0, 4.0, near(c['third'], 62), 0.08, None)
            if lv == 0:
                add('DR', B0, 0.5, 36, 0.55, None, kind='kick'); continue
            for q in range(8):                                          # 8 分音符の刻み (同じ形の繰り返し)
                t = B0 + q * 0.5; hq = P.harm[int(t)] or h; cq = chord(hq)
                add('DR', t, 0.25, 42, 0.26 if q % 2 == 0 else 0.18, None, kind='hatc' if not (lv == 2 and q == 7) else 'hato', pan=0.25)
                add('SB', t, 0.45, near(cq['root'], 33), 0.42 if q % 2 == 0 else 0.34, None)
                arp = [cq['root'], cq['fifth'], cq['third'] + 12, cq['fifth']][q % 4]
                add('PF', t, 0.45, near(arp % 12, 62 if q % 4 != 2 else 67), 0.16, None, rid=pr, rel=0.3)
                if lv == 2: add('GT', t, 0.45, near(cq['root'], 40), 0.2, None, mute=True, pan=-0.35)
            for q in (0, 2): add('DR', B0 + q, 0.5, 36, 0.8, None, kind='kick')
            if lv == 2: add('DR', B0 + 2.5, 0.5, 36, 0.6, None, kind='kick')
            for q in (1, 3): add('DR', B0 + q, 0.5, 38, 0.7 if lv == 2 else 0.5, None, kind='snare')
            if lv == 2 and (bar - b0) % 4 == 0: add('DR', B0, 2.0, 49, 0.45, None, kind='crash', pan=-0.2)
    for b0, b1, g in RIFF:                                               # リフ: 8 分音符で 根音・5 度・3 度・5 度 … を毎小節同じ形で
        for bar in range(b0, b1):
            for q in range(8):
                t = bar * BPB + q * 0.5; c = chord(P.harm[int(t)] or 'Dm')
                pc = [c['root'], c['fifth'], c['third'], c['fifth'], c['root'], c['fifth'], c['third'], c['seventh'] if c['seventh'] is not None else c['fifth']][q]
                add('LD', t, 0.42, near(pc, 74 if q % 4 == 0 else 71), g * (1.2 if q % 4 == 0 else 1.0), None)
    for b0, b1 in ([] if INST else CHOIR):                               # 後ろのコーラス: 歌声の 1 音を 3 声で正確に
        for bar in range(b0, b1):
            B0 = bar * BPB
            for half in (0, 2):
                c = chord(P.harm[B0 + half] or 'Dm')
                for k, (pc, tg) in enumerate(((c['root'], 65), (c['third'], 69), (c['fifth'], 72))):
                    add('BV', B0 + half, 2.05, near(pc, tg), 0.13, None, rid='VOXF', pan=(-0.5, 0.0, 0.5)[k])

SUBJ_R = []

def build():
    Q = phrases() or [(None, {'d': 1.0})]; qi = 0
    def nxt():
        nonlocal qi
        x = Q[qi % len(Q)]; qi += 1; return x
    v1 = [Q[i % len(Q)] for i in range(0, 5)]; v2 = [Q[i % len(Q)] for i in range(5, 9)]; last = [Q[i % len(Q)] for i in range(9, 11)]
    for r in PIANO:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 60); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    VL = 8 if INST else None
    total = 8 + (VL if INST else sum(NB(p) for _, p in v1)) + 10 + (VL if INST else sum(NB(p) for _, p in v2)) + 9 + 6 + 8 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.75
    # ---------------- Intro
    ri = '20260924_112313'
    P.section(0, 'Intro — タブレットのピアノ %s の実音' % hm(ri), 'ピアノ録音の実音 → 鼓動のようなキックとシンセのパッド — 同じ刻みが最後まで続く')
    T5.passage(P, ri, 0, 4, KEYS[ri], 4, fin=0.5, fout=2.5, bpm=BPM)
    CT.LAYOUT.append((0, 4, KEYS[ri], {v: ri for v in VOICES}, {}))
    for v in VOICES: P.rest_bars(v, 4, 8)
    P.set_harms(4, [['Dm']] * 2 + [['Gm/D']] + [['A7']])
    BAND.append((4, 6, 0)); BAND.append((6, 8, 1))
    CT.LAYOUT.append((4, 8, SEMIS, VOICE_SRC, {}))
    b = 8
    # ---------------- Verse I
    s0 = b
    if INST:
        P.section(b, 'Verse I — リフ', 'シンセのリフが毎小節同じ形を刻み、Am - F - Dm - E7 の 4 小節が回り続ける')
        for k in range(VL): P.set_harms(b + k, [LOOP[k % 4] * 4])
        RIFF.append((b, b + VL, 0.15)); b += VL
    else:
        P.section(b, 'Verse I — わたしの声', '歌声は残響をかけず乾いたきれいな声で、大げさにせず女性的に — 和音は歌声の音に合わせて 1 小節ごとに')
        for r, p in v1: b += voice(P, b, r, p)
    for v in VOICES: P.rest_bars(v, s0, b)
    BAND.append((s0, b, 1)); CT.LAYOUT.append((s0, b, SEMIS, VOICE_SRC, {}))
    # ---------------- Chorus I — Fuga
    rf = '20260923_080918'; s0 = b
    P.section(b, 'Chorus I — Fuga 〈%s〉' % hm(rf), '9/23 08:09 の旋律の 4 声フーガ (タブレットのピアノの音) — ギター、後ろのコーラス (歌声の 3 声)')
    T5.expo(P, b, rf, '①'); P.set_harms(b + 8, [['Gm', 'Gm', 'A7', 'A7'], ['Dm']])
    for k in range(10): P.dyn[b + k] = 0.8
    BAND.append((b, b + 10, 2)); CHOIR.append((b + 2, b + 10)); RIFF.append((b, b + 10, 0.07)) if INST else None; CT.LAYOUT.append((s0, b + 10, SEMIS, {v: rf for v in VOICES}, {}))
    b += 10
    # ---------------- Verse II
    s0 = b
    if INST:
        P.section(b, 'Verse II — リフ', '同じリフと同じ 4 小節がもう一度 — 刻みは一度も止まらない')
        for k in range(VL): P.set_harms(b + k, [LOOP[k % 4] * 4])
        RIFF.append((b, b + VL, 0.15)); b += VL
    else:
        P.section(b, 'Verse II — わたしの声', '歌声とバンド — 同じ刻みが回り続ける')
        for r, p in v2: b += voice(P, b, r, p)
    for v in VOICES: P.rest_bars(v, s0, b)
    BAND.append((s0, b, 1)); CT.LAYOUT.append((s0, b, SEMIS, VOICE_SRC, {}))
    # ---------------- Chorus II — 7 本の旋律
    f0 = b; octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; vs = ['A', 'S', 'T', 'B', 'S', 'A', 'T']
    P.section(b, 'Chorus II — Fuga: 7 本の旋律', '9/23・9/24 の 7 本のピアノ録音の旋律が 1 小節おきに次々と — 上の声にはシンセのリードが重なる')
    entries, labmap = [], {}
    for k, r in enumerate(PIANO):
        v = vs[k]; subj = T5.SUBJ[r][0]; tr = octs[v]
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
        lab = '旋律 %s (%s)' % (MARK[k], hm(r)); labmap[lab] = r
        P.place(v, f0 + k, subj, tr, lab); entries.append(((f0 + k) * BPB, [(d, m + tr) for d, m in subj]))
        if v in 'SA':
            t = (f0 + k) * BPB
            for d, m in subj: add('LD', t, d * 0.95, m + tr + (12 if v == 'A' else 0), 0.16, None); t += d
    for v, z in {'S': 1, 'T': 2, 'B': 3}.items(): P.rest_bars(v, f0, f0 + z)
    T5.harm_from_entries(P, f0, f0 + 8, entries); P.set_harms(f0 + 8, [['A7']])
    for k in range(9): P.dyn[f0 + k] = 0.85
    BAND.append((f0, f0 + 9, 2)); CHOIR.append((f0 + 1, f0 + 9)); CT.LAYOUT.append((f0, f0 + 9, SEMIS, VOICE_SRC, labmap))
    b = f0 + 9
    # ---------------- Bridge
    rb = '20260923_080918'
    P.section(b, 'Bridge — タブレットのピアノ %s の実音' % hm(rb), 'バンドは鼓動のようなキックだけ — ピアノ録音の実音、後半は 4 声 (ピアノの音) が支える')
    T5.passage(P, rb, b, 6, KEYS[rb], 3, fin=0.5, fout=2.0, bpm=BPM)
    BAND.append((b, b + 6, 0)); CT.LAYOUT.append((b, b + 6, KEYS[rb], {v: rb for v in VOICES}, {}))
    b += 6
    # ---------------- Mantra → イ長調
    m0 = b
    P.section(b, 'Mantra — B-A-D-A', 'B-A-D-A を 4 回、コーラスと 4 声で — バンド全開、歌声が重なる → イ長調の和音で終わる')
    for k in range(4):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, H.DRONE_BAR, 0, None)
    P.hold.update(range(b, b + 8))
    t = b + 1
    if INST: RIFF.append((b, b + 8, 0.11))
    else:
        for r, p in last: t += voice(P, t, r, p, gain=1.3, harm=False) + 1
    BAND.append((b, b + 8, 2)); CHOIR.append((b, b + 8)); CT.LAYOUT.append((m0, b + 8, SEMIS, VOICE_SRC, {}))
    b += 8
    P.set_harms(b, [['D']] * 3); P.hold.update(range(b, b + 3))
    P.place('S', b, mat(('F#5', 8)), 0, None); P.place('A', b, mat(('A4', 8)), 0, None); P.place('T', b, mat(('D4', 8)), 0, None); P.place('B', b, mat(('D3', 8)), 0, None)
    for v in VOICES: P.rest_bars(v, b + 2, b + 3)
    add('DR', b * BPB, 3.0, 49, 0.5, None, kind='crash'); add('DR', b * BPB, 0.5, 36, 0.8, None, kind='kick')
    CHOIR.append((b, b + 2)); CT.LAYOUT.append((b, b + 3, SEMIS, VOICE_SRC, {}))
    b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': None, 'tb_label': '歌声 (伸ばした音)', 'band_gain': 0.5,
    'title': 'Requiem BADA — Vox · Rock',
    'subtitle': 'タブレットのピアノとシンセとロックバンド、乾いたきれいな歌声 — 洗脳的なロックのレクイエムとフーガ',
    'legend': ['TB', 'BV', 'LD', 'PD', 'SB', 'GT'],
    'footer': ['Intro (ピアノ録音 11:23) → Verse I (声) → Chorus I (08:09 のフーガ) → Verse II → Chorus II (7 本の旋律) → Bridge (08:09 の実音) → Mantra → イ長調',
               '歌声は取り出して、大げさにせず女性的に・音程を整え、残響なし。コーラスは同じ歌声の 1 音を 3 声に。4 声とピアノの刻みはタブレットのピアノの 1 音。'],
}

def merged_bank(path):
    pb = json.load(open(sys.argv[1]))
    json.dump({'recordings': {}, 'samples': pb['samples'] + VB['samples']}, open(path, 'w'), ensure_ascii=False)
    return path

if INST:
    META.update({'title': 'Requiem BADA — Rock (Instrumental)', 'tb_label': 'タブレット録音 (実音)',
                 'subtitle': '声を消した版 — タブレットのピアノとシンセとロックバンドの、洗脳的なレクイエムとフーガ',
                 'legend': ['TB', 'LD', 'PD', 'SB', 'GT'],
                 'footer': ['Intro (ピアノ録音 11:23) → Verse I (リフ) → Chorus I (08:09 のフーガ) → Verse II (リフ) → Chorus II (7 本の旋律) → Bridge (08:09 の実音) → Mantra → イ長調',
                            '声・歌声・コーラスはなし。Verse はシンセのリフが毎小節同じ形を刻む。4 声とピアノの刻みはタブレットのピアノの 1 音、ドラム・ベース・ギター・パッドは合成。']})

if __name__ == '__main__':
    out = (ARGS[1] if INST else ARGS[2]) if len(ARGS) > (1 if INST else 2) else 'score_rockvox.json'
    META['bank'] = merged_bank(os.path.join(os.path.dirname(os.path.abspath(out)), 'bank_rockvox.json'))
    META['rec_order'] = PIANO + ([] if INST else ['VOXF'])
    compose.main(out, seed=67, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in PIANO: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
