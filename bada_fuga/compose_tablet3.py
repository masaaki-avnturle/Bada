#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions III · Mantra of All (全部の録音を合わせた、実録音の洗脳のレクイエムとフーガ)
  作曲者の録音 11 本 (2026-09-20 15:40 / 15:41 の 2 本は動画から音を取り出す) を全部合わせて、
  ♩=56 のまま一度も止まらない鼓動の上で、同じ形が繰り返し回る洗脳的なレクイエムとフーガにする。鳴る音はすべて実録音:
    - 録音の実音の抜粋と、その最初の 1 小節のテープ・ループ
    - 4 声・オスティナート・持続音は録音から切り出した 1 音を移調するサンプラー (build_sampler.py)
    - 鼓動は録音の低い打鍵を 2 オクターヴ下げて低域だけにしたもの (毎拍)
  Introitus: 鼓動と持続音だけ
  Requiem — 11 の祈り (録音順): 各録音ごとに 7 小節 — 実音の抜粋 3 小節 → ループが回る中で抜粋の最上声から作った主題を
    上声が歌い (2 小節)、次に低音が歌う (2 小節)。下ではオスティナートが刻み続ける。調は各録音の調
  Fuga — 11 の主題: 11 の主題が 1 小節おきに 4 声へ次々に入る。各主題は自分の録音の音で (ホ短調)
  Mantra: 11 本の録音のループが 1 小節ずつ回り (テープのように速さごと移調してホ短調へ)、B-A-D-A を 6 回
  Lux aeterna: ピカルディ終止 → 最後の録音 (09-24 08:53) のループが鼓動とともに消えていく
  使い方: python compose_tablet3.py <bank.json> [score_tablet3.json]
"""
import sys
import numpy as np, soundfile as sf
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT          # 抜粋・主題・和声づけ・区間ごとの移調 (同じ bank.json を読む)
import compose_tablet2 as T2         # テープ・ループ、実録音のオスティナート・持続音・鼓動 (post)

add, REC = CT.add, CT.REC
BPM = 56
# 録音 id → 調への移調 (ニ短調から)。これまでの曲で使った録音はそのときの調、新しい録音は音高の分布から推定した短調
KEYS = {'20260920_154001': (3, 'ヘ短調'), '20260920_154118': (3, 'ヘ短調'), '20260922_090146': (2, 'ホ短調'),
        '20260922_174031': (2, 'ホ短調'), '20260922_174820': (-3, 'ロ短調'), '20260922_175717': (-3, 'ロ短調'),
        '20260922_175951': (2, 'ホ短調'), '20260923_080607': (-4, '変ロ短調'), '20260923_080918': (2, 'ホ短調'),
        '20260924_084937': (3, 'ヘ短調'), '20260924_085314': (2, 'ホ短調')}
RIDS = sorted(r for r in REC if r in KEYS)
FINAL_SEMIS = 2
MARK = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫'
VOICE_SRC_FINAL = {'S': '20260923_080918', 'A': '20260922_175951', 'T': '20260922_090146', 'B': '20260923_080607'}

def hm(rid): return '%s/%s %s:%s' % (int(rid[4:6]), int(rid[6:8]), rid[9:11], rid[11:13])

def rec_gain(rid, t0, dur):
    """抜粋が録音全体よりどれだけ大きいか / 小さいかを測って、抜粋がどれも同じくらいの大きさで聞こえる倍率にする"""
    y, sr = sf.read(REC[rid]['file'], dtype='float32')
    ex = y[int(t0 * sr):int((t0 + dur) * sr)]
    ratio = np.sqrt((ex ** 2).mean()) / (np.sqrt((y ** 2).mean()) + 1e-9)
    return float(np.clip(1.2 / (ratio + 1e-9), 0.6, 2.2))

SUBJ = []
GAIN = {}

def build():
    bar_s = 240.0 / BPM; E = 3
    plan = []
    for rid in RIDS:
        semis, kname = KEYS[rid]
        t0, inside = CT.excerpt(rid, semis, E * bar_s)
        T2.FRAG[rid] = t0; GAIN[rid] = rec_gain(rid, t0, E * bar_s)
        subj = CT.make_subject(inside, semis, BPM)
        SUBJ.append((rid, subj, CT.harmonize(subj)))
        plan.append((rid, semis, kname, t0, inside, subj))
    total = 2 + 7 * len(plan) + 13 + 12 + 4
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.75
    # ---------------- Introitus: 鼓動と持続音だけ (最初の録音の調で)
    P.section(0, 'Introitus', '♩=56 の鼓動 (録音の低い打鍵) と持続音 — この鼓動は最後まで一度も止まらない')
    for v in VOICES: P.rest_bars(v, 0, 2)
    P.set_harms(0, [['Dm']] * 2)
    T2.MANTRA.append((0, 2, plan[0][0], ('DN', 'PK')))
    CT.LAYOUT.append((0, 2, plan[0][1], {v: plan[0][0] for v in VOICES}, {}))
    b = 2
    # ---------------- Requiem — 11 の祈り
    uppers = ['A', 'S', 'T']
    for i, (rid, semis, kname, t0, inside, subj) in enumerate(plan):
        s0 = b; g = GAIN[rid]
        P.section(b, '%s 録音 %s — 実音' % (MARK[i], hm(rid)), '%s ／ 録音 %s の実音の抜粋 (%.0f 秒) — 鼓動は止まらない' % (kname, rid, E * bar_s))
        for v in VOICES: P.rest_bars(v, b, b + E)
        add('REC', b * BPB, E * BPB + 1.5, 0, g, None, src=REC[rid]['file'], off=t0, rid=rid)
        for s in inside:
            for m in s['m']: add('TB', b * BPB + (s['t'] - t0) * BPM / 60.0, s['d'] * BPM / 60.0, m - semis, 0.0, None)
        for k in range(E * BPB):
            tt = t0 + k * 60.0 / BPM; cur = None
            for s in inside:
                if s['t'] <= tt + 0.05: cur = s
            if cur: P.harm[b * BPB + k] = transpose_h([[cur['ch']]], -semis)[0][0]
        T2.MANTRA.append((b, b + E, rid, ('PK',)))
        b += E
        H_sub = SUBJ[i][2]; lab = '主題 %s (%s)' % (MARK[i], hm(rid)); up = uppers[i % 3]
        P.section(b, '%s Requiem — 主題 %s 〈録音 %s〉' % (MARK[i], MARK[i], hm(rid)), '録音のループが回る中で、抜粋の最上声から作った主題を上声が、次に低音が歌う — 下で実録音のオスティナート')
        add('X', b * BPB, 8, n('D3'), 0.45)
        P.set_harms(b, H_sub); P.place(up, b, subj, {'S': 12, 'A': 0, 'T': -12}[up] if not (up == 'S' and max(m for _, m in subj) + 12 > 81) else 0, lab)
        P.set_harms(b + 2, H_sub); P.place('B', b + 2, subj, -24 if min(m for _, m in subj) - 24 >= 36 else -12, lab)
        T2.loop(rid, b, 4, BPM, 0.5 * g, fade=[1.0, 0.9, 0.8, 0.6])
        T2.MANTRA.append((b, b + 4, rid, ('DN', 'PK', 'OS')))
        b += 4
        CT.LAYOUT.append((s0, b, semis, {v: rid for v in VOICES}, {}))
    # ---------------- Fuga — 11 の主題 (ホ短調): 1 小節おきに 4 声へ次々に入る
    f0 = b
    P.section(f0, 'Fuga — 11 の主題', '11 の主題が 1 小節おきに次々と入る — 各主題は自分の録音の音で鳴り、全部の録音が 1 つのフーガになる (ホ短調)')
    for k in range(13): P.dyn[f0 + k] = 0.85
    voices = ['A', 'S', 'T', 'B']; octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}
    labmap, entries = {}, []
    for i, (rid, subj, _) in enumerate(SUBJ):
        v = voices[i % 4]; tr = octs[v] + (7 if (i // 4) % 2 else 0)
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
        lab = '主題 %s%s' % (MARK[i], ' 答唱' if (i // 4) % 2 else '')
        P.place(v, f0 + i, subj, tr, lab); labmap[lab] = rid
        entries.append(((f0 + i) * BPB, [(d, m + tr) for d, m in subj]))
    for v, z in {'S': 1, 'T': 2, 'B': 3}.items(): P.rest_bars(v, f0, f0 + z)
    for bar in range(f0, f0 + 11):                        # 和声: その半小節で鳴る主題の音を最も多く含む和音
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            cs = max(CT.CANDS, key=lambda c: sum(w * (1 if m % 12 in chord(c)['pcs'] else -0.8) for w, m in notes)) if notes else 'Dm'
            for j in range(2): P.harm[a + j] = cs
    P.set_harms(f0 + 11, [['Gm', 'Gm', 'A7', 'A7'], ['Dm']]); P.hold.add(f0 + 12)
    T2.MANTRA.append((f0, f0 + 13, RIDS[-1], ('DN', 'PK', 'OS')))
    # ---------------- Mantra: 11 本のループが 1 小節ずつ回る中で B-A-D-A ×6
    m0 = f0 + 13
    P.section(m0, 'Mantra — 11 本のループ', '11 本の録音のループが 1 小節ずつ回り (テープのように速さごと移調してホ短調へ)、B-A-D-A を 6 回唱える')
    for k in range(6):
        bb = m0 + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, H.DRONE_BAR, 0, None)
        if k % 2 == 0: add('X', bb * BPB, 8, n('D3'), 0.45)
    for k in range(12):
        rid = RIDS[k % len(RIDS)]; sh = ((FINAL_SEMIS - KEYS[rid][0] + 7) % 12) - 7
        add('REC', (m0 + k) * BPB, BPB + 1.0, 0, 0.45 * GAIN[rid], None, src=REC[rid]['file'], off=T2.FRAG[rid], rid=rid, loop=True, semis=sh)
    T2.MANTRA.append((m0, m0 + 12, RIDS[-1], ('DN', 'PK')))
    # ---------------- Lux aeterna: ピカルディ終止 → 最後の録音のループが消えていく
    e0 = m0 + 12; last = RIDS[-1]
    P.section(e0, 'Lux aeterna', 'D 長調 (ホ長調) のピカルディ終止 → 最後の録音 %s のループが、鼓動とともに消えていく' % hm(last))
    P.set_harms(e0, [['D']] * 4); P.hold.update(range(m0, e0 + 4))
    P.place('S', e0, mat(('F#5', 8)), 0, None); P.place('A', e0, mat(('A4', 8)), 0, None); P.place('T', e0, mat(('D4', 8)), 0, None); P.place('B', e0, mat(('D3', 8)), 0, None)
    for v in VOICES: P.rest_bars(v, e0 + 2, e0 + 4)
    for k in range(16): P.dyn[m0 + k] = max(0.35, 0.8 - 0.03 * k)
    T2.loop(last, e0 + 1, 3, BPM, 0.6 * GAIN[last], semis=((FINAL_SEMIS - KEYS[last][0] + 7) % 12) - 7, fade=[1.0, 0.7, 0.45])
    T2.MANTRA.append((e0, e0 + 3, last, ('PK',)))
    CT.LAYOUT.append((f0, e0 + 4, FINAL_SEMIS, VOICE_SRC_FINAL, labmap))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1],
    'title': 'Requiem BADA — Tablet Sessions III',
    'subtitle': 'Mantra of All — 録音 11 本を全部合わせた、止まらない鼓動の上の洗脳のレクイエムとフーガ (音はすべて録音から)',
    'footer': ['Introitus → Requiem: 11 の祈り (録音順、各録音の調) → Fuga: 11 の主題 → Mantra: 11 本のループと B-A-D-A ×6 → Lux aeterna (ホ短調)',
               '4 声・オスティナート・持続音は録音の 1 音を移調するサンプラー、鼓動は録音の低い打鍵を 2 オクターヴ下げた音 (♩=56 で最後まで)。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet3.json'
    compose.main(out, seed=41, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=T2.post)
    CT.finish(out)
    for rid, subj, hh in SUBJ: print(rid, 'gain %.2f' % GAIN[rid], 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in subj))
