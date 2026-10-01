#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXIV · Requiem e Fuga 12:50 — Fuga grande (LXXXIII を、レクイエムを額縁に、主体をフーガに)
  LXXXIII と同じ 9/25 12:50:36 の 8.6 秒の録音・同じ主題 (ロ短調で レ・ファ#・シ・レ・シ・ファ#・ラ#・ファ#・ラ#・シ)。
  レクイエムは初めと終わりの額縁として静かに短く、その間をフーガの技法を順にたどる 86 小節の大きなフーガに:
    Introitus — 録音そのもの (8.6 秒)                                                   3 小節
    I. Requiem ×4 — 録音の 17 の和音を 4 倍に。主題は 2 回だけ、遠くから                    9 小節
    II. Fuga (主体)                                                                     86 小節
       1. 提示 (4 声、下属調の入り、ストレッタ、保続低音)                                16
       2. 間奏 — 録音の和音の進みの上で、主題の頭 (分散和音の 3 音) が受け渡される          8
       3. 転回のフーガ — 主題を音階の上で上下に返した、下りる分散和音の主題 (シ♭… → ソ・ファ#・ミ・レ の形) 16
       4. 二重フーガ — 上る主題と下りる転回を反行で同時に                                 8
       5. 拡大 — バスが主題を 4 倍で (Requiem の伸ばしの記憶)、続いてテノールが 2 倍で — その上で 1 倍の主題がストレッタ 16
       6. ストレッタ — 1 小節半ずつずれて 4 声が次々に (主題と転回)                        12
       7. 属音の保続 → 主音の保続で 2 倍の主題                                           10
    III. Requiem aeternam ×2 — 録音を 2 倍で静かに → Amen (ロ長調の和音)                5 + 3 小節
  高音を抑える: フーガは普通の 4 声の音域で、ソプラノもミ 5 まで (それより上に出る入りは入りごとオクターヴ下へ)。伸ばした録音の音もミ 5 より上をオクターヴ下へ。
  すべてピアノの実音 (録音そのもの・録音から切り出した 1 音)。シンセ・ドラムなし。
  使い方: python compose_tablet84.py <bank82.json> [score_tablet84.json]
"""
import sys, json
import numpy as np
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet63 as LXIII
import compose_tablet83 as T83                     # 録音を伸ばす層 (stretched / entry) をそのまま使う

R = T83.R; RI = R + 'i'
BM, VOICE_SRC = T83.BM, T83.VOICE_SRC
LOW = BM                                           # フーガは普通の 4 声の音域で (LXXXII/LXXXIII の 1 オクターヴ下は濁るので)、上はミ 5 まで
CAPE = T83.CAP - LOW                               # エンジンの座標でのいちばん上 (ソ 5 = 実音ミ 5)
compose.RANGE.update({'S': (60, CAPE), 'A': (55, 74), 'T': (48, 67), 'B': (38, 57)})
DYNK = 1.3
INTRO, REQ, FUGA, REQ2, AMEN = 3, 9, 86, 5, 3
X = T83.X

def dia_inv(subj, axis=62):
    """音階の上での転回 (ニ短調の和声的短音階の度数を、レを軸に上下へ返す)"""
    deg = {pc: i for i, pc in enumerate(CT.DMIN)}
    out = []
    for d, m in subj:
        k = deg[m % 12] + 7 * ((m - 2) // 12) - 7 * ((axis - 2) // 12)
        k2 = -k; o, r = divmod(k2, 7)
        mm = (axis - 2) // 12 * 12 + 2 + 12 * o + (CT.DMIN[r] - 2) % 12
        out.append((d, mm))
    return out

def build():
    segs = CT.REC[R]['segs']
    s_ = LXIII.smooth(CT.make_subject(segs, BM, 60))
    inv = [(d, m + 12) for d, m in dia_inv(s_)]
    T5.SUBJ[R] = (s_, CT.harmonize(s_)); T5.SUBJ[RI] = (inv, CT.harmonize(inv))
    print('subject', ' '.join(name_of(m) for d, m in s_), '| inversion', ' '.join(name_of(m) for d, m in inv))
    total = INTRO + REQ + FUGA + REQ2 + AMEN
    P = Piece(total)
    place0 = P.place
    def place_cap(v, bar, mat, semis=0, label=None, beat=0):
        """いちばん上 (ミ 5) を超える入りは、入りごとオクターヴ下へ"""
        ms = [m + semis for _, m in mat if m is not None]
        while ms and max(ms) > CAPE and min(ms) - 12 >= 36: semis -= 12; ms = [m - 12 for m in ms]
        place0(v, bar, mat, semis, label, beat)
    P.place = place_cap
    for k in range(total): P.tempo[k] = 60; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, LOW, VOICE_SRC, {}))
    def H_at(sec_t):
        cur = segs[0]['ch']
        for s in segs:
            if s['t'] <= sec_t: cur = s['ch']
        return transpose_h([[cur]], -BM)[0][0]
    def pcs_at(sec_t): return set(chord(transpose_h([[H_at(sec_t)]], BM)[0][0])['pcs'])
    b = 0
    def sec(n_, title, sub, dyn):
        nonlocal b
        f = b; P.section(f, title, sub)
        for k in range(n_): P.dyn[f + k] = DYNK * (dyn[0] + (dyn[1] - dyn[0]) * k / max(1, n_ - 1))
        b += n_; return f
    CEN = {'S': 70, 'A': 64, 'T': 57, 'B': 46}
    def fit(v, mat_, tr0=0):
        """tr0 (5 度の答えなど) にオクターヴを足して、その声部の中心にいちばん近い高さへ"""
        mu = np.mean([m for _, m in mat_]) + tr0
        return tr0 + 12 * min(range(-4, 4), key=lambda o: abs(mu + 12 * o - CEN[v]))
    def seq(bar, mat_, tr, k):
        t, out = bar * BPB, []
        for d, m in mat_: out.append((t, t + d * k, m + tr)); t += d * k
        return out
    def rub(bar, mat_, tr, k, ents):
        """ほかの入りと 2 度 (半音・全音) でぶつかる長さ (拍の頭は 2 倍)"""
        me, others, bad = seq(bar, mat_, tr, k), [x for e in ents for x in seq(*e)], 0.0
        for q in np.arange(me[0][0], me[-1][1], 0.5):
            a = [m for t0, t1, m in me if t0 <= q < t1]; o = [m for t0, t1, m in others if t0 <= q < t1]
            if a and any(min((a[0] - m) % 12, (m - a[0]) % 12) in (1, 2) for m in o): bad += 0.5 * (2 if q % 1 == 0 else 1)
        return bad
    def pick(v, bar, mat_, ents, k=1, t5s=(0, 7, 5)):
        """5 度・4 度の移しとオクターヴの中から、ほかの入りといちばんぶつからない高さを"""
        cand = [fit(v, mat_, t5) for t5 in t5s]
        return min(cand, key=lambda tr: rub(bar, mat_, tr, k, ents) * 3 + 0.3 * abs(tr - fit(v, mat_)) % 12)
    def ent(v, bar, mat_, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in mat_], 0, lab)
    def harm_ents(b0, b1, ents): T5.harm_from_entries(P, b0, b1, [(bar * BPB, [(d * k, m + tr) for d, m in mat_]) for bar, mat_, tr, k in ents])
    head = s_[:3]
    def head_fit(v, bar, lab_=None):
        """主題の頭 (分散和音の 3 音) を、その小節の和音に合う高さで"""
        pcs = set(chord(P.harm[bar * BPB] or 'Dm')['pcs'])
        cand = [tr for tr in range(-30, 13) if all((m + tr) % 12 in pcs for _, m in head)] or \
               [tr for tr in range(-30, 13) if (head[-1][1] + tr) % 12 in pcs and all((m + tr) % 12 in pcs | set(CT.DMIN) for _, m in head)]
        tr = min(cand, key=lambda x: abs(np.mean([m for _, m in head]) + x - CEN[v]))
        ent(v, bar, head, tr, lab_)
    lab = '主題 (12:50)'; labi = '転回'

    # Introitus
    f = sec(INTRO, 'Introitus — 9/25 12:50 の実音', '8.6 秒の録音そのもの', (1, 1))
    CT.add('REC', 0, INTRO * BPB, 0, 0.5, None, src=CT.REC[R]['file'], off=0.0, fin=0.02, fout=1.5, rid=R + '.wav', tag='9/25 12:50 — 8.6 秒の録音')
    for q in range(INTRO * BPB): P.harm[q] = H_at(min(8.5, q * 8.6 / (INTRO * BPB)))
    # I. Requiem ×4
    f = sec(REQ, 'I. Requiem ×4 — 録音を 4 倍に (ロ短調)', '17 の和音が 34 秒に — 主題は 2 回だけ、遠くから', (1, 1))
    T0 = f * 4.0; T83.stretched(segs, 4, T0, 'x4', g0=0.3)
    for q in range(REQ * BPB): P.harm[f * BPB + q] = H_at(min(8.5, q / 4.0))
    for rt, cen, rid in ((0.3, 62, VOICE_SRC['A']), (4.2, 66, VOICE_SRC['S'])):
        sb = [(d, m + BM) for d, m in s_]
        def best(r):
            c = [tr for tr in range(-36, 25) if (sb[-1][1] + tr) % 12 in pcs_at(r + 1.6) and max(m for _, m in sb) + tr <= T83.CAP and min(m for _, m in sb) + tr >= 47]
            return min(T83.clash(T0 + r * 4, sb, tr) for tr in c) if c else 99
        rt = min((round(rt + 0.1 * j, 2) for j in range(-6, 7)), key=lambda r: best(r) + 0.2 * abs(r - rt))
        T83.entry(T0 + rt * 4, sb, pcs_at(rt + 1.6), cen, g=0.45, rid=rid)
    for v in VOICES: P.rest_bars(v, 0, INTRO + REQ)

    # II. Fuga
    F0 = b
    f = sec(16, 'II. Fuga  1. 提示 (ロ短調)', '主題の 4 声フーガ — アルト → ソプラノの答え → バス → テノール、下属調、ストレッタ、保続低音', (0.62, 0.76))
    T11.bach_fugue(P, f, R, '12:50')
    f = sec(8, '2. 間奏 — 録音の和音の上で', '12:50 の録音の和音の進みの上で、主題の頭 (分散和音) が声部から声部へ', (0.68, 0.72))
    P.set_harms(f, CT.rec_chords(segs, BM)); P.set_harms(f + 4, CT.rec_chords(segs[8:], BM))
    for k, v in enumerate(('S', 'A', 'T', 'S', 'A', 'T', 'B', 'A')):
        head_fit(v, f + k, '主題の頭' if k == 0 else None)
    f = sec(16, '3. 転回のフーガ', '主題を音階の上で上下に返した、下りる分散和音の主題のフーガ', (0.68, 0.82))
    T11.bach_fugue(P, f, RI, '転回')
    f = sec(8, '4. 二重フーガ — 反行', '上る主題と下りる転回を同時に — 声部を入れ替えて 4 回', (0.78, 0.84))
    for k, (vs, vi) in enumerate((('B', 'S'), ('T', 'A'), ('A', 'B'), ('S', 'T'))):
        bar = f + 2 * k; ts, ti = fit(vs, s_), fit(vi, inv)
        ent(vs, bar, s_, ts, lab + ' (反行で)' if k == 0 else None); ent(vi, bar, inv, ti, labi + ' (反行で)' if k == 0 else None)
        harm_ents(bar, bar + 2, [(bar, s_, ts, 1), (bar, inv, ti, 1)])
    f = sec(16, '5. 拡大 — 主題 ×4 (バス) と ×2 (テノール)', 'Requiem の伸ばしの記憶: バスが主題を 4 倍で、続いてテノールが 2 倍で — その上で 1 倍の主題', (0.76, 0.88))
    ents = [(f, s_, fit('B', s_), 4)]; ent('B', f, s_, fit('B', s_), '主題 ×4 (バス)', k=4)
    for k, v in enumerate(('S', 'A', 'S', 'A')):
        tr = pick(v, f + 2 * k, s_, ents); ent(v, f + 2 * k, s_, tr, lab + ' ×1' if k == 0 else None); ents.append((f + 2 * k, s_, tr, 1))
    harm_ents(f, f + 8, ents)
    ents = [(f + 8, s_, fit('T', s_), 2)]; ent('T', f + 8, s_, fit('T', s_), '主題 ×2 (テノール)', k=2)
    for k, (v, mat_) in enumerate((('S', s_), ('A', inv), ('S', inv), ('B', s_))):
        bar = f + 8 + k + (k // 2) * 2; tr = pick(v, bar, mat_, ents)
        ent(v, bar, mat_, tr, None); ents.append((bar, mat_, tr, 1))
    harm_ents(f + 8, f + 16, ents)
    f = sec(12, '6. ストレッタ', '1 小節半ずつずれて 4 声が次々に入る — 前の入りの終わりに次の入りが重なる (主題と転回)', (0.8, 0.94))
    ents = []
    for k, (v, mat_) in enumerate((('B', s_), ('T', inv), ('A', s_), ('S', inv), ('B', inv), ('T', s_), ('S', s_))):
        bar = f + 1.5 * k                                # 1 小節半ずつ: 前の入りの終わりの主音 (2 拍) に次の入りの分散和音が重なる
        tr = pick(v, bar, mat_, ents) if k else fit(v, mat_); print('  stretto', v, tr, rub(bar, mat_, tr, 1, ents))
        ent(v, bar, mat_, tr, 'ストレッタ' if k == 0 else None); ents.append((bar, mat_, tr, 1))
    for bar in range(f, f + 12): harm_ents(bar, bar + 1, [e for e in ents if e[0] - 2 < bar < e[0] + 2])
    f = sec(10, '7. 属音の保続 → 主音の保続', '属音ファ# の保続の上で主題 → 主音シ の保続の上で 2 倍の主題', (0.9, 0.7))
    P.place('B', f, [(2, n('A2'))] * 8, 0, '属音の保続'); ent('S', f, s_, fit('S', s_), lab + ' (属音の上)'); ent('A', f + 2, s_, fit('A', s_), None)
    harm_ents(f, f + 4, [(f, s_, fit('S', s_), 1), (f + 2, s_, fit('A', s_), 1)])
    P.set_harms(f + 4, [['Dm'] * 4, ['Dm', 'Dm', 'A7', 'A7'], ['A7'] * 4, ['Dm'] * 4, ['Gm', 'Gm', 'A7', 'A7'], ['Dm'] * 4])
    P.place('B', f + 4, [(4, n('D2'))] * 6, 0, '主音の保続'); ent('S', f + 4, s_, fit('S', s_), lab + ' ×2 (最後)', k=2)
    assert b - F0 == FUGA, b - F0

    # III. Requiem aeternam ×2 → Amen
    f = sec(REQ2, 'III. Requiem aeternam ×2', '録音を 2 倍で、静かに — フーガのあとの安息', (1, 1))
    for v in VOICES: P.rest_bars(v, f, f + REQ2)
    T0 = f * 4.0; T83.stretched(segs, 2, T0, 'x2', step_hi=99, step_lo=99, g0=0.3)
    for q in range(REQ2 * BPB): P.harm[f * BPB + q] = H_at(min(8.5, q / 2.0))
    f = sec(AMEN, 'Amen — ロ長調の和音', 'iv → V → I', (0.6, 0.5))
    P.set_harms(f, [['Gm', 'Gm', 'A7', 'A7'], ['D'], ['D']])
    P.place('S', f, [(2, n('Bb4')), (2, n('A4')), (8, n('A4'))], 0, 'Amen')
    LXIII.ARP.append((f, f + 2, 0.08, LOW))
    assert b == total
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [R] + list(VOICE_SRC.values()), 'piano_decay': 2.4, 'reverb': [6.0, 2.3, 0.48],
    'title': 'Requiem BADA — LXXXIV · Requiem e Fuga grande',
    'subtitle': 'LXXXIII を、レクイエムを額縁に、主体をフーガに — 9/25 12:50 (ロ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['Introitus → I. Requiem ×4 → II. Fuga (提示・間奏・転回・二重フーガ・拡大・ストレッタ・保続音) → III. Requiem ×2 → Amen',
               '主題: レ・ファ#・シ・レ・シ・ファ#・ラ#・ファ#・ラ#・シ (録音の最上声)。高音はミ 5 のあたりまで。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet84.json'
    compose.main(out, seed=184, bpm=60, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    K.BPM = 60; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']:
        lab_ = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.35 if lab_ and lab_ not in ('属音の保続', '主音の保続') else 1.2), 4)
    for n_ in d['notes']:
        while n_['v'] == 'B' and n_['m'] < 26: n_['m'] += 12           # バスはレ 1 より下へは行かない
    d['extras'] += X
    d['entries'] += [dict(t=INTRO * 4.0, label='録音 ×4 (17 の和音)', v='B'), dict(t=(INTRO + REQ + FUGA) * 4.0, label='録音 ×2', v='B')]
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']] + [e['m'] for e in d['extras'] if e['v'] == 'PF']
    print('duration', round(d['duration'], 1), 'notes', Counter(x['v'] for x in d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
    print('sections:', [(round(s['t']), s['title'][:16]) for s in d['sections']])
