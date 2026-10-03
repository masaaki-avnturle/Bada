#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXIII · Requiem 10/03 sopra un tema (CXII に大黒柱の主題を決めて — 洗脳的でレクイエムのような主題のメロディーで書き換え)
  大黒柱の主題 (8 拍、変ロ短調): ラ♭・レ♭・ミ♭・レ♭・ミ♭・レ♭・ド・シ♭ — 13:24 (109 秒〜) と 13:27 (33 秒〜) の両方に現れる、最上声の同じ節 (ソ#・ド#・レ#・ド#・レ#・ド#) を、主音に下りて終わるように整えたもの。
    レ♭ と ミ♭ のあいだを揺れ続けて、最後にド → シ♭ へ沈む — レクイエムの唱え (洗脳的: 止まらない 1 拍ごとの低い鼓動の上で、同じ主題だけが回り続ける)
  メロディー (表、13:24 のピアノの 1 音):
    Praeludium  (0〜28)  主題を 2 倍に伸ばして (16 拍)、アルトが 7 回唱える — 2 回目からテノールがオクターヴ下で、5 回目からソプラノがオクターヴ上で重なる
    Interludium (29〜64) 主題 (1 倍) がシャコンヌのように、裏の和音 (録音の採譜) に 2 小節ごとにいちばん合う移調で置かれていく (アルト)。テノールは 2 倍、ソプラノは転回で重なる
    Fuga        (65〜92) 主題の 4 声フーガ: 提示 → 反行 → ストレッタ → 拡大 (和音は録音のその時の和音に寄せる)
    締めくくり  (93〜100) 主題のストレッタ (変ロ長調) と LXXXIX の Amen → 変ロ長調の和音
  裏: CXII と同じ — LXXXIX (変ロ短調に移して小さく)、13:19 の音の共鳴 (その時の和音を保つ)、10/03 13:22・13:24・13:27 の録音の実音 (CXII では表だったものを小さく裏に、0.18)
  鼓動: 13:04 の低い音で 1 拍ごと (止まらない)。音源は CXII と同じ。声なし。100 小節 = 6 分 40 秒 + 残響
  使い方: python compose_tablet113.py <bank112.json> <bank109.json> <score_tablet89.json> <wav のフォルダ> [score_tablet113.json]
"""
import sys, os, json
OUT = sys.argv[5] if len(sys.argv) > 5 else 'score_tablet113.json'
sys.argv = sys.argv[:5] + [OUT]
import compose_tablet112 as T
from compose import *
import compose

THEME = [(1.5, 68), (1.5, 61), (1, 63), (1, 61), (1, 63), (0.5, 61), (0.5, 60), (1, 58)]              # ラ♭・レ♭・ミ♭・レ♭・ミ♭・レ♭・ド・シ♭
R24 = T.R24; LOW = '20260925_130431'
T.SUBJ[:] = THEME
PRAEL1, INTER0, FUGA0, CLOSE, TOTAL = 1, int(T.T24 / 4), T.FUGA0, T.CLOSE, T.TOTAL

def best_tr(P, motif, bar, prev, lo, hi):
    """2 小節の和音に、強拍・長い音が和音の音になる移調 (±7) — 前の置き方に近いほうを少し優先、音域 lo〜hi"""
    def score(tr):
        s, t = 0.0, bar * BPB
        for d, m in motif:
            pcs = chord(P.harm[min(int(t), TOTAL * BPB - 1)])['pcs']; w = d * (2.0 if abs(t - round(t)) < 1e-6 and int(t) % 2 == 0 else 1.0)
            s += w * (1.0 if (m + tr) % 12 in pcs else -1.0); t += d
        return s - 0.06 * abs(tr) - 0.04 * abs(tr - prev)
    cands = [tr for tr in range(-7, 8) if lo <= min(m for _, m in motif) + tr and max(m for _, m in motif) + tr <= hi]
    return max(cands, key=score)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM = 60; P.dyn[k] = 1.3
    for q in range(TOTAL * BPB):                                                                    # 和音は CXII と同じ (録音の採譜 → LXXXIX)
        cur = None
        for rid, t0 in ((T.R22, T.T22), (T.R24, T.T24), (T.R27, T.T27)):
            rec = T.RECS[rid]
            if t0 <= q < t0 + rec['dur']:
                cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= q - t0: cur = s['ch']
        if cur is None:
            qb = int(q - T.BASE0 * BPB); cur = transpose_h([[T.S89['harm'][min(max(qb, 0), len(T.S89['harm']) - 1)]]], T.TR)[0][0]
        T.RH.append(cur); P.harm[q] = cur
    aug = T.augment(THEME)
    P.section(0, 'Praeludium — 大黒柱の主題 (2 倍に伸ばして)', '主題 ラ♭・レ♭・ミ♭・レ♭・ミ♭・レ♭・ド・シ♭ を 2 倍に伸ばして、アルトが 7 回唱える — 2 回目からテノールがオクターヴ下、5 回目からソプラノがオクターヴ上。下で 1 拍ごとの鼓動、裏で LXXXIX と 13:22 の録音が小さく')
    for v in VOICES: P.rest_bars(v, 0, PRAEL1)
    E = []
    for k in range(7):
        b = PRAEL1 + 4 * k
        P.place('A', b, aug, 0, '大黒柱の主題 ×2' if k == 0 else None); E.append((b * BPB, aug))
        if k >= 1: P.place('T', b, aug, -12, None)
        else: P.rest_bars('T', b, b + 4)
        if k >= 4: P.place('S', b, aug, 12, None)
        else: P.rest_bars('S', b, b + 4)
        P.rest_bars('B', b, b + 4)
    T.harm_fit(P, PRAEL1, PRAEL1 + 28, E, T.CANDS)                                               # 前奏曲の和音は主題に寄せる (共鳴が主題を支える)
    P.section(INTER0, 'Interludium — 主題のシャコンヌ', '主題が裏の和音 (13:24 の採譜) に 2 小節ごとにいちばん合う移調で置かれていく (アルト) — テノールは 2 倍に、ソプラノは転回で。鼓動は止まらない')
    prev = 0; inv = T.invert(THEME)
    for k in range((FUGA0 - INTER0) // 2):
        b = INTER0 + 2 * k; tr = best_tr(P, THEME, b, prev, 57, 76); prev = tr
        P.place('A', b, THEME, tr, '大黒柱の主題 (移調 %+d)' % tr if k == 0 else None)
        if k >= 4 and k % 2 == 0: P.place('T', b, aug, tr - 12, None)
        elif k < 4 or k % 2 == 1: P.rest_bars('T', b, b + 2)
        if k >= 10: P.place('S', b, inv, best_tr(P, inv, b, prev, 64, 84), '大黒柱の主題 (転回)' if k == 10 else None)
        else: P.rest_bars('S', b, b + 2)
        P.rest_bars('B', b, b + 2)
    for v in VOICES: P.rest_bars(v, INTER0 + 2 * ((FUGA0 - INTER0) // 2), FUGA0)
    P.section(FUGA0 - 2, 'Fuga — 大黒柱の主題の 4 声フーガ', '提示 → 反行 → ストレッタ → 拡大 — 和音は 13:27 の録音のその時の和音に寄せて (共鳴)。裏で 13:27 の録音が小さく')
    f = FUGA0; lab = '大黒柱の主題'; E = []
    for k, v in enumerate('ASBT'):
        T.entry(P, f + 2 * k, v, THEME, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    T.harm_fit(P, f, f + 8, E, T.CANDS)
    E = []; T.entry(P, f + 8, 'S', inv, 0, lab + ' (反行)', E); T.entry(P, f + 10, 'T', inv, 0, lab + ' (反行)', E); T.harm_fit(P, f + 8, f + 12, E, T.CANDS)
    E = []
    for k, v in enumerate('ASTB'): T.entry(P, f + 12 + k, v, THEME, 0, lab + ' ストレッタ' if k == 0 else None, E)
    T.harm_fit(P, f + 12, f + 18, E, T.CANDS)
    E = []; T.entry(P, f + 18, 'B', aug, 0, lab + ' (拡大 ×2)', E); T.entry(P, f + 20, 'S', THEME, 0, lab, E); T.harm_fit(P, f + 18, f + 22, E, T.CANDS)
    for v in VOICES: P.rest_bars(v, f + 22, CLOSE)
    P.section(CLOSE, '締めくくり — 主題のストレッタ (変ロ長調) と LXXXIX の Amen', '主題が変ロ長調で 4 声のストレッタに — 裏の LXXXIX の Amen と重なって、変ロ長調の和音で閉じる')
    E = []
    for k, v in enumerate('SATB'): T.entry(P, CLOSE + k, v, THEME, 0, lab + ' ストレッタ (長調)' if k == 0 else None, E)
    T.entry(P, CLOSE + 4, 'B', aug, 0, lab + ' (拡大 ×2)', E); T.entry(P, CLOSE + 4, 'S', THEME, 12, None, E)
    T.harm_fit(P, CLOSE, TOTAL - 2, E, T.CANDS_J)
    for b in range(TOTAL - 2, TOTAL): P.set_harm(b, 'A#'); P.hold.add(b)
    P.place('S', TOTAL - 2, [(4, 82)] * 2, 0, 'シ♭ (頂点)'); P.place('B', TOTAL - 2, [(4, 46)] * 2, 0, '')
    for k in range(CLOSE, TOTAL): P.dyn[k] = 1.35 + 0.15 * min(1.0, (k - CLOSE) / 4.0) - (0.25 if k >= TOTAL - 2 else 0)
    return P

def post(P, events, ex):
    for rid, t0, name in ((T.R22, T.T22, '13:22'), (T.R24, T.T24, '13:24'), (T.R27, T.T27, '13:27')):     # 録音は裏に (小さく)
        T.add('REC', t0, T.RECS[rid]['dur'], 0, 0.18, None, src=os.path.join(T.WDIR, rid + '_clean.wav'), off=0.0, fin=0.02, fout=1.0, rid=rid + '.wav', tag='10/03 %s — 裏 (実音、小さく)' % name)
    q = 0; first = True                                                                             # 共鳴 (CXII と同じ)
    while q < TOTAL * BPB:
        h = P.harm[q]; q1 = q
        while q1 < TOTAL * BPB and P.harm[q1] == h: q1 += 1
        d = max(1.0, (q1 - q) + 0.6); c = chord(h); last = q >= (TOTAL - 2) * BPB
        tones = [min((x for x in range(52, 76) if x % 12 == p), key=lambda x: abs(x - 62)) for p in (c['root'], c['fifth'], c['third'])]
        g = 0.13 if not last else 0.18
        for i, m in enumerate(tones):
            if m % 12 in T.MAJ and q >= CLOSE * BPB: m = T.majify(m)
            T.add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.75), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.2, layer='res'); first = False
        T.add('PF', q, d, tones[0] - 12, g * 0.7, None, rid='VOXRS', rel=1.2, layer='res')
        q = q1
    for bar in range(PRAEL1, TOTAL - 2):                                                             # 鼓動: 1 拍ごとに低い根音 (止まらない)
        c = chord(P.harm[bar * BPB]); root = 36 + c['root']
        for i in range(BPB): T.add('PF', bar * BPB + i, 0.6, root, 0.26 if i == 0 else 0.16, '鼓動 (1 拍ごと)' if (bar == PRAEL1 and i == 0) else None, rid=LOW, rel=0.4, layer='pulse')
    for v in VOICES: events[v] = [(s, d, T.majify(m) if s >= CLOSE * BPB else m, lab) for s, d, m, lab in events[v]]

META = dict(T.META, title='Requiem BADA — CXIII · Requiem 10/03 sopra un tema',
            subtitle='CXII に大黒柱の主題 (ラ♭・レ♭・ミ♭・レ♭・ミ♭・レ♭・ド・シ♭ — 13:24 と 13:27 に共通の節) を決めて、洗脳的でレクイエムのような主題のメロディーで書き換え — 前奏曲 (2 倍の唱え) → 間奏曲 (シャコンヌ) → フーガ → 締めくくり (変ロ短調 → 変ロ長調, ♩=60, 6 分 47 秒)',
            vname={'PF': '共鳴 / 鼓動 / 裏 (LXXXIX)'},
            footer=['Praeludium: 主題 ×2 をアルトが 7 回 → Interludium: 主題が和音に合う移調で 2 小節ごと (シャコンヌ) → Fuga: 主題の 4 声フーガ → 締めくくり: ストレッタ (変ロ長調) と LXXXIX の Amen',
                    '裏 = LXXXIX (−4、小さく) + 13:19 の音の共鳴 + 10/03 13:22・13:24・13:27 の録音 (小さく)。鼓動は 13:04 の低い音で 1 拍ごと。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    compose.main(OUT, seed=113, bpm=60, builder=build, meta=META, extras=T.extras, post=post)
    T.merge_base(OUT)
    d = json.load(open(OUT))
    for n in d['notes']:
        if n.get('role') != 'base': n['src'] = R24
        else: n['dyn'] = round(n['dyn'] * 0.62, 4)                                                   # 裏はさらに 4 dB 下 (主題が前に)
    for e in d['extras']:
        if e.get('layer') == 'base': e['gain'] = round(e['gain'] * 0.62, 4)
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
