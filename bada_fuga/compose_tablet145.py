#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLV · Mantra del pilastro (11/06 の 2 曲を雰囲気に、tablet117 と tablet144 をメインテーマにして、洗脳的な曲に)
  雰囲気: 2026/11/06 06:39 (ト長調〜ニ・ドリア: Gmaj7・D7・Dm7) と 06:42 (ヘ長調: F・Fmaj7・E・C) の実音 — 序・中・終わりに敷き、和音はその採譜で追う
  メインテーマ: tablet117 (CXVII) の「大黒柱の主題」(ド・ファ・ソ・ファ・ソ・ファ・ミ・レ、ニ短調に) と、tablet144 (CXLIV) の定旋律「Erbarm dich mein, o Herre Gott」(BWV 721 のコラール、ニ短調に +5)
  洗脳的に: 大黒柱の主題を 4 小節ごと・2 小節ごとに繰り返す (マントラ)、BWV 721 の打ち続ける和音 (8 分音符) が全曲の脈、2 つの主題の重ね (定旋律の上の大黒柱、大黒柱の拡大の下の定旋律)、最後は主題の頭 (ド・ファ) だけが残って消える
  音源: 4 声は 11/06 06:42 の実音のピアノの 1 音 (bank1106 のサンプラー、11 音)、高い共鳴と低いペダルは合成のピアノ。鐘なし、声なし
  使い方: python compose_tablet145.py <bank1106.json> <wav のフォルダ> [score_tablet145.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet145.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42 = '20261106_063938', '20261106_064228'
PSRC = R42                                                                                        # 実音のピアノの 1 音は 06:42 から
BPM = 60
PRE, ERB_S, DOPPIO, FINE, TOTAL = 0, 44, 104, 136, 162
PILLAR = [(1.5, 72), (1.5, 65), (1, 67), (1, 65), (1, 67), (0.5, 65), (0.5, 64), (1, 62)]        # 大黒柱の主題 (CXVII、変ロ短調 → ニ短調 +4)、8 拍
ERB = [(d, m + 5) for d, m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erbarm_melody.json')))['notes']]   # Erbarm dich (イ短調 → ニ短調)
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
def clip(mat, max_beats):
    out = []; t = 0.0
    for d, m in mat:
        if t >= max_beats: break
        out.append((min(d, max_beats - t), m)); t += d
    return out
CANDS = ['Dm', 'F', 'C', 'Bb', 'Gm', 'Am', 'A', 'A7', 'Dm/F', 'Bb/D', 'C/E', 'Gm7', 'Dm/A', 'Fmaj7', 'G', 'Gmaj7', 'D7', 'Em7', 'E', 'Cmaj7']
# (録音, 小節, 大きさ, 移調, 抜粋の始まり, 長さ (秒; None = 全部))
PLAYS = [(R39, 1, 0.65, 0, 0.0, None), (R42, ERB_S + 1, 0.5, 0, 0.0, None), (R39, DOPPIO + 1, 0.42, 0, 0.0, 80.0), (R42, FINE + 1, 0.42, 0, 150.0, 76.0)]
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []; RH = []; RECQ = set()
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def harm_fit(P, b0, b1, entries, cands):
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            rc = set(chord(RH[a])['pcs']); rec = a in RECQ; prev = P.harm[a - 1] if a > 0 else None
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + (1.5 if rec else 0.4) * len(cc & rc) / max(1, len(cc)) + ((1.2 if rec else 0.2) if c == RH[a] else 0) - (0.3 if (c == prev and notes) else 0)
            cs = max(cands, key=score)
            for q in range(2): P.harm[a + q] = cs
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def free(P, v, b0, b1):
    for b in range(b0, b1): P.rest[v].difference_update(range(b * BPB, b * BPB + BPB))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm, off, dur in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: cur = 'Dm'
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.45 if k < 12 else 0.62 if k < ERB_S else 0.6 if k < ERB_S + 30 else 0.75 if k < DOPPIO else 0.9 if k < DOPPIO + 24 else 0.7 if k < FINE else max(0.08, 0.7 - 0.03 * (k - FINE))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    # I. 序: 06:39 の上で、脈と大黒柱のマントラ
    P.section(PRE, 'I. 序 — 06:39 の上で、脈と大黒柱のマントラ (ニ短調, ♩=60)', '11/06 06:39 の実音 (そのまま)。BWV 721 の打ち続ける和音 (8 分音符、実音のピアノ) が pp で始まり、大黒柱の主題 (tablet117) がアルトで 4 小節ごとに繰り返す (マントラ)、途中からテノールが 1 オクターヴ下で重なる')
    for k in range(8):
        b = PRE + 12 + 4 * k; free(P, 'A', b, b + 2); P.place('A', b, PILLAR, 0, '大黒柱の主題 (マントラ)' if k == 0 else None); E.append((b * BPB, PILLAR))
        if k >= 4: free(P, 'T', b, b + 2); P.place('T', b, PILLAR, -12, None); E.append((b * BPB, [(d, m - 12) for d, m in PILLAR]))
    # II. Erbarm dich: 06:42 の上で、定旋律と大黒柱
    P.section(ERB_S, 'II. Erbarm dich — 06:42 の上で、定旋律と大黒柱 (ニ短調)', '11/06 06:42 の実音 (そのまま)。ソプラノが tablet144 の定旋律「Erbarm dich mein」(2 倍に伸ばして) を、途中からテノールが大黒柱の主題を 2 小節ごとに重ねる。2 度目はアルトのマントラと')
    free(P, 'S', ERB_S + 4, ERB_S + 31); P.place('S', ERB_S + 4, aug(ERB), 0, '定旋律「Erbarm dich mein」(tablet144)'); E.append(((ERB_S + 4) * BPB, aug(ERB)))
    for k in range(8):
        b = ERB_S + 16 + 2 * k; free(P, 'T', b, b + 2); P.place('T', b, PILLAR, -12, '大黒柱 (テノール、2 小節ごと)' if k == 0 else None); E.append((b * BPB, [(d, m - 12) for d, m in PILLAR]))
    free(P, 'S', ERB_S + 33, ERB_S + 60); P.place('S', ERB_S + 33, aug(ERB), 0, '定旋律 2 度目'); E.append(((ERB_S + 33) * BPB, aug(ERB)))
    for k in range(13):
        b = ERB_S + 34 + 2 * k; free(P, 'A', b, b + 2); P.place('A', b, PILLAR, 0, 'マントラ (アルト)' if k == 0 else None); E.append((b * BPB, PILLAR))
    # III. 二重: 大黒柱の拡大の下の定旋律、脈の頂点
    P.section(DOPPIO, 'III. 二重 — 大黒柱の拡大と定旋律 (ニ短調)', '06:39 の実音 (始めの 80 秒)。ソプラノが大黒柱の主題を 2 倍に伸ばして 4 度、テノールが定旋律 (そのままの速さ) を 2 度、アルトのマントラ、脈は頂点')
    for k in range(4):
        b = DOPPIO + 2 + 6 * k; free(P, 'S', b, b + 4); P.place('S', b, aug(PILLAR), 12, '大黒柱の拡大 (ソプラノ)' if k == 0 else None); E.append((b * BPB, [(d, m + 12) for d, m in aug(PILLAR)]))
    for k in range(2):
        b = DOPPIO + 2 + 13 * k; free(P, 'T', b, b + 13); P.place('T', b, ERB, -12, '定旋律 (テノール、そのままの速さ)' if k == 0 else None); E.append((b * BPB, [(d, m - 12) for d, m in ERB]))
    for k in range(14):
        b = DOPPIO + 2 + 2 * k; free(P, 'A', b, b + 2); P.place('A', b, PILLAR, 0, None); E.append((b * BPB, PILLAR))
    # IV. 消える: 06:42 の終わりの上で、主題の頭だけ
    P.section(FINE, 'IV. 消える — 06:42 の終わりの上で (ニ短調)', '06:42 の実音の終わり。脈が少しずつ消え、大黒柱の頭 (ド・ファ) だけがアルトで 2 小節ごとに、高い共鳴が反響する')
    for k in range(10):
        b = FINE + 2 + 2 * k; free(P, 'A', b, b + 1); P.place('A', b, PILLAR[:2], 0, '主題の頭 (ド・ファ) だけ' if k == 0 else None); E.append((b * BPB, PILLAR[:2]))
    harm_fit(P, PRE + 6, TOTAL - 4, E, CANDS)
    # 脈: 8 分音符の和音 (テノール・バス、空いている所はアルトも)
    for b in range(PRE + 6, TOTAL - 6):
        for k in range(BPB * 2):
            h = P.harm[b * BPB + k // 2]; q = b * BPB + k // 2
            if q in P.rest['B']: P.rest['B'].discard(q); P.place('B', b, [(0.5, tones_of(h, 40, 52)[0])], 0, ('打ち続ける和音 (BWV 721 の脈)' if (b == PRE + 6 and k == 0) else None), beat=k * 0.5)
            else: P.place('B', b, [(0.5, tones_of(h, 40, 52)[0])], 0, None, beat=k * 0.5)
            tt = tones_of(h, 52, 64)
            if all((b * BPB + j) in P.rest['T'] for j in range(BPB)): P.place('T', b, [(0.5, tt[len(tt) // 2])], 0, None, beat=k * 0.5); P.rest['T'].discard(q)
    for b in range(PRE + 6, TOTAL - 6):
        for k in range(BPB): P.rest['B'].discard(b * BPB + k)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=off, fin=0.5 if bar > 1 else 0.02, fout=6.0, semis=sm, rid=rid + '.wav', tag='11/06 %s — 実音 (そのまま%s)' % ('06:39' if rid == R39 else '06:42', '、抜粋' if dur else ''))
    first = True
    for b in range(ERB_S, TOTAL - 6):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 3.6, r, 0.16 * P.dyn.get(b, 0.7) / 0.7, '低いペダルの音 (小節ごと)' if first else None); first = False
    first = True
    for b0 in (ERB_S + 33, DOPPIO + 2):
        t = b0 * BPB + 2
        for d, m in (aug(ERB) if b0 < DOPPIO else aug(PILLAR) * 4):
            add('H', t, d, m + 12, 0.09 * P.dyn.get(int(t // BPB), 0.7) / 0.7, '高い共鳴 (反響、pp)' if first else None); first = False; t += d
    for k in range(10):
        b = FINE + 2 + 2 * k; add('H', b * BPB + 1, 3.0, 84, 0.08 * max(0.3, 1 - 0.08 * k), None); add('H', b * BPB + 2.5, 3.0, 77, 0.06 * max(0.3, 1 - 0.08 * k), None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R42], 'piano_decay': 2.6, 'reverb': [6.0, 2.5, 0.45],
        'title': 'Requiem BADA — CXLV · Mantra del pilastro',
        'subtitle': '11/06 06:39・06:42 の 2 曲を雰囲気に、tablet117 の大黒柱の主題と tablet144 の定旋律「Erbarm dich mein」をメインテーマにして、洗脳的に: 序 (06:39、脈とマントラ) → Erbarm dich (06:42、定旋律と大黒柱) → 二重 (06:39、大黒柱の拡大と定旋律、脈の頂点) → 消える (06:42 の終わり、主題の頭だけ)。ニ短調、♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['大黒柱の主題 = CXVII (tablet117) の ド・ファ・ソ・ファ・ソ・ファ・ミ・レ (変ロ短調 → ニ短調)。定旋律 = CXLIV (tablet144) の「Erbarm dich mein, o Herre Gott」(イ短調 → ニ短調)。脈 = BWV 721 の打ち続ける和音 (8 分音符)',
                   '4 声は 11/06 06:42 の実音のピアノの 1 音 (11 音のサンプラー)。和音は録音の採譜を優先しつつ主題の音を含む和音を半小節ごとに。鐘なし、声なし。']}

if __name__ == '__main__':
    print('pillar', ' '.join('%s:%g' % (name_of(m), d) for d, m in PILLAR), '| erbarm', ' '.join('%s:%g' % (name_of(m), d) for d, m in ERB[:8]))
    compose.main(OUT, seed=145, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
