#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions II · Mantra lento (実録音の、ゆったりとした洗脳のレクイエムとフーガ)
  作曲者のタブレット録音 2 本 (2026-09-24 08:49 / 08:53) を、ゆったりとした (♩=48〜52)、同じものが繰り返し
  続く洗脳的なレクイエムとフーガにする。鳴る音はすべて実録音:
    - 録音の実音の抜粋と、その主和音の 1 小節を切り出したテープ・ループ (同じ 1 小節が何度も回る)
    - 4 声・オスティナート・持続音は録音から切り出した 1 音を移調するサンプラー (build_sampler.py)
    - 鼓動は録音の低い打鍵を 2 オクターヴ下げて低域だけにしたもの (毎拍、1 拍目を強く)
  各区間: 実音の抜粋 → ループ (ループ + 持続音 + 鼓動) → 抜粋の最上声から作った主題の 4 声フーガ
    (下でオスティナートが根音・5 度・3 度・5 度を刻み続ける) → 抜粋の和音進行のコラールを 2 回 (2 回目はループが戻る)
  終曲 (ホ短調): 2 つの主題の二重フーガ → 2 つの録音のループが交互に回る中で B-A-D-A を 4 回
    → ピカルディ終止 → 2 本目の録音のループが消えていく
  使い方: python compose_tablet2.py <bank.json> [score_tablet2.json]
"""
import sys
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT          # 抜粋・主題・和声づけ・区間ごとの移調 (同じ bank.json を読む)

add, REC, MARK = CT.add, CT.REC, CT.MARK
# (録音 id, 調への移調 (ニ短調から), 調の名前, ♩)
SECS = [('20260924_084937', 3, 'ヘ短調', 52), ('20260924_085314', 2, 'ホ短調', 50)]
FINAL_SEMIS, FINAL_BPM = 2, 48
# 抜粋・ループの音量 (サンプラーのフーガと同じくらいに聞こえるよう録音ごとに合わせた値)
REC_GAIN = {'20260924_084937': 1.3, '20260924_085314': 1.3}
MANTRA = []                          # (開始小節, 終了小節, 録音 id, 何を鳴らすか) — post() がオスティナート等を置く
FRAG = {}                            # 録音 id → テープ・ループにする 1 小節の開始時刻 (秒)

def loop(rid, bar0, bars, bpm, gain, semis=0, fade=None):
    """テープ・ループ: 録音の主和音の 1 小節を小節ごとに繰り返す (つなぎ目は重ねてフェード)"""
    for k in range(bars):
        g = gain * (fade[k] if fade else 1.0)
        add('REC', (bar0 + k) * BPB, BPB + 1.2 * bpm / 60.0, 0, g, None, src=REC[rid]['file'], off=FRAG[rid], rid=rid, loop=True, semis=semis)

def post(P, events, extras):
    """ループ区間・フーガ・終曲に、実録音の音の持続音・鼓動・オスティナートを置く (和声は P.harm を見る)"""
    for b0, b1, rid, kinds in MANTRA:
        for bar in range(b0, b1):
            if 'DN' in kinds and (bar - b0) % 2 == 0:
                for m in (38, 45): add('DN', bar * BPB, 8.6, m, 0.20, None, rid=rid)
            if 'PK' in kinds:
                for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.3 if k == 0 else 0.17, None, rid=rid)
            if 'OS' in kinds:
                for k in range(2 * BPB):                    # 8 分音符で 根音・5 度・3 度・5 度 を繰り返す
                    beat = bar * BPB + k / 2.0; h = P.harm[int(beat)] or 'Dm'; c = chord(h)
                    pc = [c['root'], c['fifth'], c['third'], c['fifth']][k % 4]
                    m = min((x for x in range(57, 70) if x % 12 == pc), key=lambda x: abs(x - (60 if k % 4 == 0 else 64)))
                    add('OS', beat, 0.45, m, 0.28 if k % 4 == 0 else 0.2, None, rid=rid)

SUBJ = []

def build():
    plan = []
    for rid, semis, kname, bpm in SECS:
        bar_s = 240.0 / bpm; E = max(5, round(20.0 / bar_s))
        t0, inside = CT.excerpt(rid, semis, E * bar_s)
        FRAG[rid] = t0
        subj = CT.make_subject(inside, semis, bpm)
        SUBJ.append((rid, subj, CT.harmonize(subj)))
        plan.append((rid, semis, kname, bpm, E, t0, inside, subj))
    total = sum(p[4] + 21 for p in plan) + 22
    P = Piece(total); b = 0
    for i, (rid, semis, kname, bpm, E, t0, inside, subj) in enumerate(plan):
        s0 = b; bar_s = 240.0 / bpm; g = REC_GAIN.get(rid, 1.3)
        for k in range(E + 21): P.tempo[b + k] = bpm; P.dyn[b + k] = 0.75
        # 実音の抜粋 (4 声は休む。採譜した音は表示用)
        P.section(b, '%s 録音 %s — 実音' % (MARK[i], CT.hm(rid)), '%s · ♩=%d ／ タブレット録音 %s の実音の抜粋 (%.0f 秒)' % (kname, bpm, rid, E * bar_s))
        for v in VOICES: P.rest_bars(v, b, b + E)
        add('REC', b * BPB, E * BPB + 1.5, 0, g, None, src=REC[rid]['file'], off=t0, rid=rid)
        for s in inside:
            for m in s['m']: add('TB', b * BPB + (s['t'] - t0) * bpm / 60.0, s['d'] * bpm / 60.0, m - semis, 0.0, None)
        for k in range(E * BPB):
            tt = t0 + k * 60.0 / bpm; cur = None
            for s in inside:
                if s['t'] <= tt + 0.05: cur = s
            if cur: P.harm[b * BPB + k] = transpose_h([[cur['ch']]], -semis)[0][0]
        b += E
        # ループ: 抜粋の最初の 1 小節が回り続け、持続音と鼓動が入る
        P.section(b, '%s Mantra — 録音 %s のループ' % (MARK[i], CT.hm(rid)), '抜粋の最初の 1 小節 (主和音) を繰り返すテープ・ループ ＋ 実録音の持続音 ＋ 録音の低音から作った鼓動')
        for v in VOICES: P.rest_bars(v, b, b + 3)
        P.set_harms(b, [['Dm']] * 3)
        loop(rid, b, 3, bpm, 0.85 * g)
        MANTRA.append((b, b + 3, rid, ('DN', 'PK')))
        b += 3
        # 4 声フーガ (提示: A → S 答唱 → B → T 答唱 → 結尾) の下でオスティナートが回り続ける
        H_sub = SUBJ[i][2]; lab = '主題 %s (%s)' % (MARK[i], CT.hm(rid))
        P.section(b, '%s Fuga — 主題 %s 〈録音 %s〉' % (MARK[i], MARK[i], CT.hm(rid)), '抜粋の最上声から作った主題の 4 声フーガ — 下で実録音のオスティナートが同じ形を刻み続ける')
        P.set_harms(b, H_sub); P.place('A', b, subj, 0, lab)
        for v in 'STB': P.rest_bars(v, b, b + 2)
        P.set_harms(b + 2, transpose_h(H_sub, 7)); P.place('S', b + 2, subj, 7 + 12 if max(m for _, m in subj) + 7 < 72 else 7, lab + ' 答唱')
        for v in 'TB': P.rest_bars(v, b + 2, b + 4)
        P.set_harms(b + 4, H_sub); P.place('B', b + 4, subj, -24 if min(m for _, m in subj) - 24 >= 36 else -12, lab)
        P.rest_bars('T', b + 4, b + 6)
        P.set_harms(b + 6, transpose_h(H_sub, 7)); P.place('T', b + 6, subj, 7 - 12, lab + ' 答唱')
        P.set_harms(b + 8, [['Gm', 'Gm', 'A7', 'A7'], ['Dm']]); P.hold.add(b + 9)
        MANTRA.append((b, b + 10, rid, ('DN', 'PK', 'OS')))
        b += 10
        # 抜粋の和音によるレクイエム・コラールを 2 回 (2 回目はループが戻り、さらに静かに)
        ch = CT.rec_chords(inside, semis)
        P.section(b, '%s Requiem — 録音 %s の和音 (2 回)' % (MARK[i], CT.hm(rid)), '抜粋の和音進行 (%s) による 4 声のコラールを 2 回 — 2 回目は録音のループが戻る' % ' → '.join(transpose_h([[x[0]] for x in ch], semis)[j][0] for j in range(4)))
        P.set_harms(b, ch); P.set_harms(b + 4, ch); P.hold.update({b + 3, b + 7})
        for k in range(8): P.dyn[b + k] = 0.7 if k < 4 else 0.55
        loop(rid, b + 4, 4, bpm, 0.55 * g)
        MANTRA.append((b, b + 8, rid, ('DN', 'PK')))
        b += 8
        CT.LAYOUT.append((s0, b, semis, {v: rid for v in VOICES}, {}))
    # ---------------- 終曲 (ホ短調): 2 つの主題の二重フーガ → B-A-D-A ×4 (ループが交互に) → ピカルディ終止 → ループが消える
    f0 = b; ra, rb = SECS[0][0], SECS[1][0]
    P.section(f0, 'Finale — Fuga doppia', '2 つの主題の二重フーガ — 主題 ① は録音 08:49 の音、主題 ② は 08:53 の音で。最後の 2 小節は 2 つの主題が同時に (ホ短調)')
    for k in range(22): P.tempo[f0 + k] = FINAL_BPM; P.dyn[f0 + k] = 0.85
    octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}
    plan_f = [(0, 'T', 0, 0), (2, 'A', 1, 0), (4, 'S', 0, 7), (6, 'B', 1, 0), (8, 'S', 0, 0), (8, 'T', 1, 0)]
    labmap, entries = {}, []
    for bar, v, si, tr0 in plan_f:
        rid, subj, _ = SUBJ[si]; tr = octs[v] + tr0
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if v == 'S' and max(m for _, m in subj) + tr > 81: tr -= 12
        lab = '主題 %s%s' % (MARK[si], ' 答唱' if tr0 else '')
        P.place(v, f0 + bar, subj, tr, lab); labmap[lab] = rid
        entries.append(((f0 + bar) * BPB, [(d, m + tr) for d, m in subj]))
    for v, (a, z) in {'S': (0, 4), 'A': (0, 2), 'B': (0, 6)}.items(): P.rest_bars(v, f0 + a, f0 + z)
    for bar in range(f0, f0 + 10):                        # 和声: その半小節で鳴る主題の音を最も多く含む和音
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
    MANTRA.append((f0, f0 + 10, rb, ('DN', 'PK', 'OS')))
    m0 = f0 + 10
    P.section(m0, 'Mantra — B-A-D-A ×4', '2 つの録音のループが小節ごとに交互に回り (08:49 はテープのように半音下げて)、B-A-D-A を 4 回唱える')
    for k in range(4):
        bb = m0 + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, H.DRONE_BAR, 0, None)
        if k % 2 == 0: add('X', bb * BPB, 8, n('D3'), 0.5)
    for k in range(8):
        rid = ra if k % 2 == 0 else rb
        add('REC', (m0 + k) * BPB, BPB + 1.0, 0, 0.4 * REC_GAIN[rid], None, src=REC[rid]['file'], off=FRAG[rid], rid=rid, loop=True, semis=(FINAL_SEMIS - SECS[0][1]) if rid == ra else 0)
    MANTRA.append((m0, m0 + 8, rb, ('DN', 'PK')))
    e0 = m0 + 8
    P.section(e0, 'Lux aeterna', 'D 長調 (ホ長調) のピカルディ終止 → 2 本目の録音 08:53 のループが、鼓動とともに静かに消えていく')
    P.set_harms(e0, [['D']] * 4); P.hold.update(range(m0, e0 + 4))
    P.place('S', e0, mat(('F#5', 8)), 0, None); P.place('A', e0, mat(('A4', 8)), 0, None); P.place('T', e0, mat(('D4', 8)), 0, None); P.place('B', e0, mat(('D3', 8)), 0, None)
    for v in VOICES: P.rest_bars(v, e0 + 2, e0 + 4)
    for k in range(12): P.dyn[m0 + k] = max(0.35, 0.8 - 0.04 * k)
    loop(rb, e0 + 1, 3, FINAL_BPM, 0.7 * REC_GAIN[rb], fade=[1.0, 0.7, 0.45])
    MANTRA.append((e0, e0 + 3, rb, ('PK',)))
    CT.LAYOUT.append((f0, e0 + 4, FINAL_SEMIS, {'S': rb, 'A': ra, 'T': rb, 'B': ra}, labmap))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1],
    'title': 'Requiem BADA — Tablet Sessions II',
    'subtitle': 'Mantra lento — タブレット録音 2 本 (09-24 08:49 / 08:53) の、ゆったりとした洗脳のレクイエムとフーガ。鳴るのは録音の音だけ',
    'footer': ['① 08:49 (ヘ短調, ♩=52) → ② 08:53 (ホ短調, ♩=50) → 終曲: 二重フーガ → B-A-D-A ×4 → ピカルディ終止 (ホ短調, ♩=48)',
               '各区間: 実音の抜粋 → 1 小節のテープ・ループ → 4 声フーガ (下で実録音のオスティナート) → 抜粋の和音のコラール ×2',
               '4 声・オスティナート・持続音は録音の 1 音を移調するサンプラー、鼓動は録音の低い打鍵を 2 オクターヴ下げた音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet2.json'
    compose.main(out, seed=37, bpm=52, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for rid, subj, hh in SUBJ: print(rid, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in subj), '| harm', hh)
