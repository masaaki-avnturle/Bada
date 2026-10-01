#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXX · Fuga 08:53 (9/24 08:53 の録音を想像して — くり返さず、LXXIX と同じ長さ (7 分 4 秒) の 1 つのフーガに、高音を抑えて)
  主題: 9/24 08:53 の録音の最上声 — ホ短調で ミ・ファ#・シ・ミ・ミ (8 拍)。録音の和音の進み (rec_chords) も間奏とコラールに使う。
  くり返さない: ループせず、フーガの技法を順にたどって 106 小節 (♩=60、424 秒) を書き通す —
    1. 提示 (4 声、下属調の入り、ストレッタ、保続低音)        16 小節
    2. 間奏 — 録音の和音の進みの上で、主題の頭が受け渡される     8 小節
    3. 転回のフーガ — 主題を上下に返した、オクターヴ下りる線     16 小節
    4. 間奏 — 5 度ずつ下りるゼクエンツ                          8 小節
    5. 二重フーガ — 上る主題と下りる転回を反行で同時に            8 小節
    6. 拡大 — バスの 4 倍の主題 (8 小節)、テノールの 2 倍の主題の上でストレッタ  16 小節
    7. コラール — 録音の和音の進み (レクイエムのように静かに)    8 小節
    8. ストレッタ — 1 小節ずつずれて 4 声が入る (主題と転回)      12 小節
    9. 属音の保続 → 主音の保続で 2 倍の主題 → ホ長調の終止       14 小節
  高音を抑える: 曲全体を 1 オクターヴ下 (ホ短調の主題がミ 3〜ミ 4) で書き、いちばん上でもミ 5 のあたりまで。バスは重く深く (ファ# 1 から)。
  すべて録音から切り出したピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet80.py <bank74.json> [score_tablet80.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet63 as LXIII

R = '20260924_085314'; RI = R + 'i'                # 主題 / 転回 (ラベル用に録音 id の形のまま)
EM_LOW = 2 - 12                                    # ホ短調を 1 オクターヴ下で
VOICE_SRC = {'S': R, 'A': '20260924_084937', 'T': '20260925_124643', 'B': '20260925_130431'}
DYNK = 1.3
compose.RANGE['B'] = (40, 58)                      # バスがミ 1 より下へ行きすぎないように (1 オクターヴ下げた後でファ# 1 から)

def build():
    t0, inside = CT.excerpt(R, 2, 13.0); s_ = LXIII.smooth(CT.make_subject(inside, 2, 60))
    inv = [(d, 2 * 62 - m + 12) for d, m in s_]                                          # レ 4 を軸に上下を返し、オクターヴ上へ: レ 5 から下りる線
    T5.SUBJ[R] = (s_, CT.harmonize(s_)); T5.SUBJ[RI] = (inv, CT.harmonize(inv))
    head = s_[:2]
    print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_), '| inversion', ' '.join('%s:%g' % (name_of(m), d) for d, m in inv))
    segs = CT.REC[R]['segs']
    def recH(at):
        ins = [x for x in segs if at <= x['t'] < at + 13.0]
        return CT.rec_chords(ins, 2)
    plan = [16, 8, 16, 8, 8, 16, 8, 12, 14]; total = sum(plan)
    P = Piece(total)
    for k in range(total): P.tempo[k] = 60; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, EM_LOW, VOICE_SRC, {}))
    b = 0
    def sec(n_, title, sub, dyn):
        nonlocal b
        f = b; P.section(f, title, sub)
        for k in range(n_): P.dyn[f + k] = DYNK * (dyn[0] + (dyn[1] - dyn[0]) * k / max(1, n_ - 1))
        b += n_; return f
    def ent(v, bar, mat_, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in mat_], 0, lab)
    def harm_ents(b0, b1, ents): T5.harm_from_entries(P, b0, b1, [(bar * BPB, [(d * k, m + tr) for d, m in mat_]) for bar, mat_, tr, k in ents])
    lab = '主題 (9/24 08:53)'; labi = '転回 (上下を返した主題)'
    CEN = {'S': 67, 'A': 62, 'T': 55, 'B': 45}
    def head_fit(v, bar, lab_=None):
        """主題の頭 (2 音) を、その小節の和音に合う高さで (長く伸ばす 2 音目が和音の音に、1 音目も和音か音階の音に)"""
        c = chord(P.harm[bar * BPB] or 'Dm'); pcs = set(c['pcs'])
        cand = [tr for tr in range(-30, 13) if (head[1][1] + tr) % 12 in pcs and (head[0][1] + tr) % 12 in pcs | set(CT.DMIN)]
        tr = min(cand, key=lambda x: abs(head[1][1] + x - CEN[v])) if cand else 0
        ent(v, bar, head, tr, lab_)
    # 1. 提示
    f = sec(16, '1. Esposizione 提示 (ホ短調)', '08:53 の主題の 4 声フーガ — アルト → ソプラノの答え → バス → テノール、下属調の入り、ストレッタ、保続低音', (0.6, 0.75))
    T11.bach_fugue(P, f, R, '08:53')
    # 2. 間奏 (録音の和音の進み)
    f = sec(8, '2. Episodio 間奏 — 録音の和音の上で', '08:53 の録音の和音の進みの上で、主題の頭 (ミ・ファ#) が声部から声部へ受け渡される', (0.66, 0.7))
    P.set_harms(f, recH(40.0)); P.set_harms(f + 4, recH(90.0))
    for k, v in enumerate(('S', 'A', 'T', 'S', 'A', 'T', 'B', 'S')):
        head_fit(v, f + k, '主題の頭' if k == 0 else None)
    # 3. 転回のフーガ
    f = sec(16, '3. Fuga per moto contrario 転回のフーガ', '主題を上下に返した、オクターヴ下りる線のフーガ (レクイエムの嘆きのように)', (0.66, 0.8))
    T11.bach_fugue(P, f, RI, '転回')
    # 4. 間奏 (5 度ずつ下りるゼクエンツ)
    f = sec(8, '4. Episodio 間奏 — ゼクエンツ', '和音が 5 度ずつ下りていき、主題の頭が模倣で追いかける', (0.7, 0.66))
    P.set_harms(f, [['Gm', 'Gm', 'C', 'C'], ['F', 'F', 'Bb', 'Bb'], ['Em7b5', 'Em7b5', 'A7', 'A7'], ['Dm', 'Dm', 'Dm', 'Dm'],
                    ['Gm', 'Gm', 'C', 'C'], ['F', 'F', 'Bb', 'Bb'], ['Em7b5', 'Em7b5', 'A7', 'A7'], ['A7', 'A7', 'A7', 'A7']])
    for k in range(6):
        head_fit('S' if k % 2 == 0 else 'T', f + k, 'ゼクエンツ' if k == 0 else None)
    # 5. 二重フーガ (反行)
    f = sec(8, '5. Doppia fuga 二重フーガ — 反行', '上る主題と下りる転回を同時に (反行) — 声部を入れ替えて 4 回', (0.76, 0.82))
    for k, (vs, vi, ts, ti) in enumerate((('B', 'S', -24, 0), ('T', 'A', -12, -12), ('A', 'B', 0, -24), ('S', 'T', 12, -12))):
        bar = f + 2 * k
        ent(vs, bar, s_, ts, lab + ' (反行で)' if k == 0 else None); ent(vi, bar, inv, ti, labi if k == 0 else None)
        harm_ents(bar, bar + 2, [(bar, s_, ts, 1), (bar, inv, ti, 1)])
    # 6. 拡大
    f = sec(16, '6. Per augmentationem 拡大', 'バスが主題を 4 倍で (8 小節)、続いてテノールが 2 倍で — その上で 1 倍の主題がストレッタで入る', (0.74, 0.86))
    ents = [(f, s_, -24, 4)]
    ent('B', f, s_, -24, '主題 ×4 (バス)', k=4)
    for k, (v, tr) in enumerate((('S', 0), ('A', -5), ('S', 7 - 12), ('A', 0))):
        ent(v, f + 2 * k, s_, tr, lab + ' ×1' if k == 0 else None); ents.append((f + 2 * k, s_, tr, 1))
    harm_ents(f, f + 8, ents)
    ents = [(f + 8, s_, -12, 2)]
    ent('T', f + 8, s_, -12, '主題 ×2 (テノール)', k=2)
    for k, (v, tr) in enumerate((('S', 0), ('A', -5), ('S', 12 - 12), ('B', -24))):
        bar = f + 8 + k * 1 + (k // 2) * 2
        mat_, tt = (s_, tr) if k % 2 == 0 else (inv, tr if v == 'B' else tr - 12)       # 転回はレ 5 から下りるので、バス以外はオクターヴ下で
        ent(v, bar, mat_, tt, None); ents.append((bar, mat_, tt, 1))
    harm_ents(f + 8, f + 16, ents)
    # 7. コラール
    f = sec(8, '7. Corale コラール — 録音の和音で (Requiem)', '08:53 の録音の和音の進みを、主題を 2 倍にしたソプラノで静かに', (0.6, 0.55))
    P.set_harms(f, recH(15.3)); P.set_harms(f + 4, recH(130.0))
    ent('S', f, s_, 0, '主題 ×2 (コラール)', k=2); ent('S', f + 4, inv, -12, '転回 ×2 (コラール)', k=2)
    # 8. ストレッタ
    f = sec(12, '8. Stretto ストレッタ', '1 小節ずつずれて 4 声が次々に入る — 主題と転回が重なり合う', (0.78, 0.92))
    ents = []
    for k, (v, mat_, tr) in enumerate((('B', s_, -24), ('T', s_, -12 + 7), ('A', s_, 0), ('S', s_, 7), ('B', inv, -24 - 12 + 12), ('T', inv, -12),
                                       ('A', inv, -12 + 7), ('S', inv, 0), ('B', s_, -24), ('T', s_, -12), ('A', s_, -5))):
        ent(v, f + k, mat_, tr, 'ストレッタ' if k == 0 else None); ents.append((f + k, mat_, tr, 1))
    for bar in range(f, f + 12): harm_ents(bar, bar + 1, [e for e in ents if e[0] <= bar < e[0] + 2])
    # 9. 保続音と終止
    f = sec(14, '9. Pedale e cadenza 保続音と終止 (ホ長調)', '属音シの保続の上で主題 → 主音ミの保続の上で 2 倍の主題 → ホ長調の和音で閉じる', (0.86, 0.6))
    P.set_harms(f, [['A7'] * 4] * 2 + [['A', 'A', 'A7', 'A7']] * 2)
    P.place('B', f, [(2, n('A2'))] * 8, 0, '属音の保続'); ent('S', f, s_, 0, lab + ' (属音の上)'); ent('A', f + 2, s_, -5, None)
    P.set_harms(f + 4, [[c, c, c, c] for c in ['Dm', 'Gm', 'Dm', 'A7', 'Dm', 'Dm']])
    P.place('B', f + 4, [(4, n('D2'))] * 6, 0, '主音の保続'); ent('S', f + 4, s_, 0, lab + ' ×2 (最後)', k=2)
    P.set_harms(f + 10, [['Gm', 'Gm', 'A7', 'A7'], ['D'], ['D'], ['D']])
    P.place('S', f + 10, [(4, n('Bb4')), (12, n('A4'))], 0, 'Amen (ホ長調)')
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [R, '20260924_084937', '20260925_124643', '20260925_130431'], 'piano_decay': 2.6, 'reverb': [6.0, 2.3, 0.48],
    'title': 'Requiem BADA — LXXX · Fuga 08:53',
    'subtitle': '9/24 08:53 の録音を想像して — くり返さず書き通す 1 つのフーガ、高音を抑えて (ホ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': '分散和音'},
    'footer': ['提示 → 間奏 (録音の和音) → 転回のフーガ → ゼクエンツ → 二重フーガ → 拡大 → コラール → ストレッタ → 保続音と終止 (ホ長調)',
               '主題も和音の進みも 9/24 08:53 の録音から。曲全体を 1 オクターヴ低く、いちばん上でもミ 5 のあたり。すべてピアノの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet80.json'
    compose.main(out, seed=180, bpm=60, builder=build, meta=META, extras=CT.extras, post=LXIII.post)
    CT.finish(out)
    K.BPM = 60; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.35 if lab and lab not in ('属音の保続', '主音の保続') else 1.2), 4)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']]
    print('duration', round(d['duration'], 1), 'notes', Counter(x['v'] for x in d['notes']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
    print('sections:', [(round(s['t']), s['title'][:20]) for s in d['sections']])
