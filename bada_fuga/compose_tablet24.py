#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXIV · Attrito (擦れ) — 音と音が合わさるときの擦れの微妙なニュアンス
  XXII (ピアノ一色) / XXIII (11:21 のシンセの実音一色) と同じ形式・同じ主題 (レクイエム、主題はフーガ) を、
  「合わせられた音と音の擦れ」を曲の中で表現するように作り換えた 2 曲。mode で音色を選ぶ:
    synth — 2026-09-24 11:21 の録音から切り出したシンセサイザーの持続音 (実音) 一色  (XXIII と同じ音)
    piano — 2026-09-23 / 09-24 の録音から切り出したピアノの 1 音 (実音) 一色、抜粋は録音そのもの  (XXII と同じ音)
  擦れ (attrito) の表現:
    1. 掛留 (suspension): 自由声部が強拍で 2 度下がるところで、前の音を 1 拍 (短い音なら半拍) 引き伸ばして強拍に持ち越す。
       強拍で他の声部と 2 度・7 度・4 度で擦れ、次の拍で解決する — バッハの対位法の「擦れて、ほどける」。主題の音は変えない。
    2. B-A-D-A の 1 拍遅れのカノン (Agnus Dei): テノールが 1 拍遅れて同じ動機を歌うので、B♭ と A、A と D が常に擦れ合う。
    3. ユニゾンの擦れ (synth.py unison_detune): 1 音ごとに数セントずらした同じ音を重ね、ゆっくりうなる。
       シンセは 7 セント (約 1 Hz のうなり)、ピアノは 3 セント (調律のわずかにずれたユニゾン弦のように)。
  使い方: python compose_tablet24.py <bank.json> <score.json> <synth|piano>
"""
import sys, json
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 56; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
MODE = sys.argv[3] if len(sys.argv) > 3 else 'synth'
SYNTH = MODE == 'synth'
SYN = 'VOXSY'
VOICE_SRC = {v: SYN for v in VOICES} if SYNTH else {'S': E1, 'A': E2, 'T': RF, 'B': B1}
DYN = (0.7, 0.78, 0.76, 0.62, 0.66) if SYNTH else (1.15, 1.3, 1.25, 1.0, 1.1)     # 基本, フーガ, 二重フーガ II, Agnus, 保続低音
SUSP = []

def suspend(P, events):
    """掛留: 強拍で 2 度下がる自由声部の前の音を持ち越し、強拍で擦れて次の拍で解決させる (主題・保続低音の音は動かさない)"""
    sound = {}
    for v in VOICES:
        for s, d, m, lab in events[v]:
            for k in range(int(round(s * 2)), int(round((s + d) * 2))): sound.setdefault(k, {})[v] = m
    taken = set()
    for v in ('S', 'A', 'T'):
        ev = events[v]; out = []; i = 0
        while i < len(ev):
            s, d, m, lab = ev[i]
            if i + 1 < len(ev):
                s2, d2, m2, lab2 = ev[i + 1]
                strong = abs(s2 - round(s2)) < 1e-6 and int(round(s2)) % BPB in (0, 2)
                if strong and lab is None and lab2 is None and abs(s + d - s2) < 1e-6 and m - m2 in (1, 2) and d2 >= 1 and s2 not in taken:
                    ch = chord(P.harm[int(round(s2))]); others = [x for w, x in sound.get(int(round(s2 * 2)), {}).items() if w != v]
                    rub = any(abs(m - x) % 12 in (1, 2, 5, 10, 11) for x in others)
                    if m % 12 not in ch['pcs'] and rub:
                        delay = 1.0 if d2 >= 2 else 0.5
                        out.append((s, d + delay, m, lab)); out.append((s2 + delay, d2 - delay, m2, lab2))
                        taken.add(s2); SUSP.append((v, s2, m, m2)); i += 2; continue
            out.append(ev[i]); i += 1
        events[v] = out
    print('suspensions:', len(SUSP))

def post(P, events, extras):
    suspend(P, events)
    for b0, b1, rid, kinds in T2.MANTRA:                                 # 鼓動 (pp、低い打鍵)
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=(SYN if SYNTH else rid))

def synth_passage(P, rid, bar, bars, semis, gain=0.62, t0=None):
    """録音の採譜 (打鍵ごとの和音・長さ) を 11:21 のシンセの実音で鳴らし直す。和声は録音の和音"""
    if t0 is None: t0, inside = T5.best_window(rid, semis, bars * BAR_S)
    else: inside = [x for x in REC[rid]['segs'] if t0 <= x['t'] < t0 + bars * BAR_S]
    T5.USED.setdefault(rid, []).append((t0, t0 + bars * BAR_S))
    for s_ in inside:
        beat = bar * BPB + (s_['t'] - t0) * BPM / 60.0; dur = max(0.4, s_['d'] * BPM / 60.0)
        for j, m in enumerate(sorted(s_['m'])):
            add('SP', beat + 0.01 * j, dur, m - semis, gain / (1 + 0.35 * (len(s_['m']) - 1)), None, rid=SYN, pan=(-0.25, 0.25, -0.1, 0.1)[j % 4])
    for k in range(bars):
        a, z = t0 + k * BAR_S, t0 + (k + 1) * BAR_S; w = {}
        for s_ in inside:
            ov = min(z, s_['t'] + s_['d']) - max(a, s_['t'])
            if ov > 0: w[s_['ch']] = w.get(s_['ch'], 0) + ov
        prev = None
        for s_ in REC[rid]['segs']:
            if s_['t'] <= a: prev = s_['ch']
        ch = max(w, key=w.get) if w else (prev or transpose_h([['Dm']], semis)[0][0])
        for q in range(BPB): P.harm[(bar + k) * BPB + q] = transpose_h([[ch]], -semis)[0][0]
    for v in VOICES: P.rest_bars(v, bar, bar + bars)
    for k in range(bars): P.dyn[bar + k] = 0.42

def passage(P, rid, bar, bars, semis, t0=None, fin=1.5, fout=3.0, gmul=0.65):
    if SYNTH: synth_passage(P, rid, bar, bars, semis, t0=t0)
    else: T5.passage(P, rid, bar, bars, semis, bars, fin=fin, fout=fout, t0=t0, bpm=BPM, gmul=gmul)

def chain(P, b, rids, semis, bars=10):
    st = b
    for i, r in enumerate(rids):
        if SYNTH:
            synth_passage(P, r, st, bars - (XF if i < len(rids) - 1 else 0), semis)
            CT.LAYOUT.append((st, st + bars, semis, VOICE_SRC, {}))
        else:
            T5.passage(P, r, st, bars, semis, bars, fin=(1.5 if i == 0 else XF * BAR_S), fout=(XF * BAR_S if i < len(rids) - 1 else 3.0), bpm=BPM, gmul=0.65)
            CT.LAYOUT.append((st + (XF if i else 0), st + bars, semis, {v: r for v in VOICES}, {}))
        st += bars - XF
    end = st + XF
    for v in VOICES: P.rest_bars(v, b, end)
    T2.MANTRA.append((b, end, rids[0], ('PK',)))
    return end - b

def arp(P, b, notes, step, dur, gain_s, gain_p, rid):
    for k, m in enumerate(notes):
        if SYNTH: add('SP', b * BPB + k * step, dur, m, gain_s, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, -0.2, 0.2)[k % 7])
        else: add('PF', b * BPB + k * step, dur, m, gain_p, None, rid=rid, rel=1.5 if dur < 3 else 3.0)

def pivot(P, b, rid, semis_next):
    P.set_harms(b, [['A7']])
    for v in VOICES: P.rest_bars(v, b, b + 1)
    arp(P, b, (33, 45, 49, 52, 55), 0.5, 2.5, 0.2, 0.16, rid)
    T2.MANTRA.append((b, b + 1, rid, ('PK',))); CT.LAYOUT.append((b, b + 1, semis_next, VOICE_SRC, {}))

def double_fugue(P, f, ra, rb, ans=7):
    entries, labmap = [], {}
    for bar, v, r, tr0 in ((0, 'A', ra, 0), (2, 'S', rb, 0), (4, 'T', ra, ans), (6, 'B', rb, 0), (8, 'S', ra, 0), (8, 'T', rb, 0)):
        T7.entry(P, f + bar, v, r, tr0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 10, entries)
    return labmap

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end_f = REC[RF]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(RF, []).append((end_f, REC[RF]['dur']))
    total = 18 + 16 + 1 + 18 + 10 + 1 + 10 + 10 + 4 + 14 + 3 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYN[0]
    b = 0
    what = 'シンセの実音' if SYNTH else 'ピアノの実音'
    P.section(b, 'Introitus — 〈%s → %s〉 (ホ短調)' % (hm(E1), hm(E2)), '%s — ♩=56 の柔らかい鼓動が最後まで止まらない。ユニゾンのわずかなずれが 1 音ごとにうなる' % ('録音の採譜を 11:21 のシンセの実音で' if SYNTH else '実音の抜粋 (8 秒のクロスフェード)'))
    b += chain(P, b, [E1, E2], 2)
    f = b
    P.section(b, 'Kyrie — Fuga I 〈%s〉 (ホ短調)' % hm(E2), '08:53 の主題のバッハ風フーガ: 提示 → エピソード → 下属調 → ストレッタ → 保続低音 — 自由声部は強拍で掛留して擦れ、次の拍でほどける')
    n_ = T11.bach_fugue(P, b, E2, '②')
    for k in range(n_): P.dyn[f + k] = DYN[1]
    T2.MANTRA.append((f, f + n_, E2, ('PK',))); CT.LAYOUT.append((f, f + n_, 2, VOICE_SRC, {})); b = f + n_
    pivot(P, b, E2, -4); b += 1
    P.section(b, 'Graduale — 〈%s → %s〉 (変ロ短調)' % (hm(B1), hm(B2)), '9/23 08:06 から 9/24 11:18 へ — %s' % what)
    b += chain(P, b, [B1, B2], -4)
    f = b
    P.section(b, 'Dies irae — Fuga II 〈%s · %s〉 (変ロ短調)' % (hm(E1), hm(B2)), '11:23 と 11:18 の主題の二重フーガ — 掛留の擦れをはさんで荘厳に')
    labmap = double_fugue(P, f, E1, B2)
    for k in range(10): P.dyn[f + k] = DYN[2]
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, -4, VOICE_SRC, labmap)); b = f + 10
    pivot(P, b, RF, 3); b += 1
    P.section(b, 'Offertorium — %s (ヘ短調)' % hm(RF), '08:49 の %s 43 秒' % what)
    passage(P, RF, b, 10, 3)
    T2.MANTRA.append((b, b + 10, RF, ('PK',))); CT.LAYOUT.append((b, b + 10, 3, VOICE_SRC, {})); b += 10
    f = b
    P.section(b, 'Sanctus — Fuga III 〈%s · %s〉 (ヘ短調)' % (hm(B1), hm(E3)), '9/23 の 2 本、08:06 と 08:09 の主題の二重フーガ')
    labmap = double_fugue(P, f, B1, E3, ans=0)
    for k in range(10): P.dyn[f + k] = DYN[1]
    T2.MANTRA.append((f, f + 10, B1, ('PK',))); CT.LAYOUT.append((f, f + 10, 3, VOICE_SRC, labmap)); b = f + 10
    a0 = b
    P.section(b, 'Agnus Dei — B-A-D-A のカノン', 'B-A-D-A を 2 回、テノールが 1 拍遅れて同じ動機を追う — B♭ と A、A と D が常に擦れ合う (保続低音の上で)')
    for k in range(2):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        P.place('T', bb, H.BADA, -12, 'B-A-D-A (1 拍遅れ)' if k == 0 else None, beat=1)
        for j in range(2): P.place('B', bb + j, T11.PED, 0, None)
    P.rest_bars('S', b, b + 4)
    P.hold.update(range(b, b + 4))
    for k in range(4): P.dyn[b + k] = DYN[3]
    T2.MANTRA.append((a0, a0 + 4, RF, ('PK',))); CT.LAYOUT.append((a0, a0 + 4, 3, VOICE_SRC, {})); b = a0 + 4
    f = b; entries, labmap = [], {}
    P.section(b, 'Finale — Stretto a sette soggetti (ヘ短調)', '7 本の録音の主題が次々と入り、最後の 3 つはストレッタで重なる → 拍ごとに打ち直す保続低音')
    for k, bar in enumerate((0, 2, 4, 6, 8, 9, 10)):
        T7.entry(P, f + bar, ['A', 'S', 'T', 'B', 'S', 'A', 'T'][k], ORDER[k], 0, entries, labmap, synth=False)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 14, entries)
    for k in range(14): P.dyn[f + k] = DYN[1]
    T2.MANTRA.append((f, f + 14, RF, ('PK',))); CT.LAYOUT.append((f, f + 14, 3, VOICE_SRC, labmap)); b = f + 14
    P.set_harms(b, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm']])
    for k in range(3): P.place('B', b + k, T11.PED, 0, '保続低音' if k == 0 else None)
    P.hold.update({b + 1, b + 2})
    for k in range(3): P.dyn[b + k] = DYN[4]
    T2.MANTRA.append((b, b + 3, RF, ('PK',))); CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(RF), '08:49 の最後の 21 秒 (属和音で止まる) → ヘ長調の和音を静かに分散して、鼓動とともに消えていく')
    passage(P, RF, b, 5, 3, t0=end_f, fin=1.0, fout=2.5, gmul=0.7)
    T2.MANTRA.append((b, b + 7, RF, ('PK',))); CT.LAYOUT.append((b, b + 5, 3, VOICE_SRC, {})); b += 5
    P.set_harms(b, [['D']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    arp(P, b, (38, 45, 50, 54, 57, 62, 66), 0.4, 8.0 if SYNTH else 3.5, 0.2, 0.18, RF)
    CT.LAYOUT.append((b, b + 3, 3, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'unison_detune': 7.0 if SYNTH else 3.0,
    'title': 'Requiem BADA — Tablet Sessions XXIV · Attrito %s' % ('sintetico' if SYNTH else 'pianistico'),
    'subtitle': '音と音の擦れ — 掛留、1 拍遅れのカノン、うなるユニゾン。%s一色のレクイエムとフーガ (♩=56)' % ('11:21 のシンセの実音' if SYNTH else '実録音のピアノ'),
    'footer': ['Introitus 11:23→08:53 → Kyrie: Fuga I → Graduale 08:06→11:18 → Dies irae: Fuga II → Offertorium 08:49 → Sanctus: Fuga III → Agnus Dei → Finale → In paradisum',
               '擦れ: 自由声部の掛留 (強拍で擦れて次の拍でほどける)、B-A-D-A の 1 拍遅れのカノン、%s セントずらしたユニゾンのうなり。' % (7 if SYNTH else 3)],
}
if SYNTH:
    META.update({'rec_order': [SYN], 'src_name': {SYN: '11:21 のシンセ (実音)'}, 'legend': ['SP', 'PK'], 'vname': {'SP': 'シンセ (採譜の鳴らし直し)', 'PK': '鼓動'}})
else:
    META.update({'rec_order': ORDER, 'piano_decay': 1.5, 'legend': ['TB', 'PK'], 'vname': {'PK': '鼓動 (ピアノの低い打鍵)'}})

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet24.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    if SYNTH:
        d = json.load(open(out))
        for nt in d['notes']: nt['src'] = SYN
        json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    for v, s2, m, m2 in SUSP[:12]: print('  susp', v, 'bar %d beat %d' % (s2 // BPB + 1, s2 % BPB + 1), name_of(m), '->', name_of(m2))
