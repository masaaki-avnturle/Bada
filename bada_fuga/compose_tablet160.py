#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLX · Fuga doppia sotto le mattine (2026/11/06 の 2 曲をメインにして、バックはトラック 8 と 18 をバッハのフーガに、レクイエムを醸す)
  メイン (表) = 11/06 06:42 と 06:39 の実音、そのまま (06:42 ヘ長調 → 06:39 ト長調 → 06:42 の後半 → 06:39 の終わり)。和音は表の録音の採譜を優先
  バック = バッハ風の二重フーガ (4 声、06:42 の実音のピアノの 1 音のサンプラー): 主題 A = トラック 8 の音から作った旋律 (8 小節)、主題 B = トラック 18 の音から作った旋律 (8 小節、短調)。トラック 8・18 の録音そのものは鳴らさず、主題だけ
    I. 06:42 (ヘ長調): 主題 A の提示部 (アルト → ソプラノ (属調の応答) → テノール → バス、4 小節ごと) → 頭のストレッタ → 主題 B (ニ短調) の提示
    II. 06:39 (ト長調): 主題 B (ホ短調) の提示部 (バスから上へ) → 主題 A と B を同時に → 頭のストレッタ
    III. 06:42 の後半 (ヘ長調): 二重フーガの頂点 — A と B を対で、2 小節遅れのストレッタ、バスに B の拡大 (2 倍)
    IV. 06:39 の終わり (ト長調): 主題の頭を拡大して、鐘と高い共鳴だけが残って消える
  レクイエム: 低い鐘 (段落の頭と頂点の 8 小節ごと)、低いペダルの音、頂点から消えていく強弱
  使い方: python compose_tablet160.py <bank150.json> <wav のフォルダ (20261106_064228_clean.wav, 20261106_063938_clean.wav)> [score_tablet160.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet160.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R18, R08 = '20261106_063938', '20261106_064228', '20261107_180000', '20261107_080000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 102, 150, 170
NAMES = {R39: '11/06 06:39', R42: '11/06 06:42'}
FILE = {R39: R39 + '_clean.wav', R42: R42 + '_clean.wav'}
PLAYS = [(R42, 1, 0.6, 0, 0.0, None, True),                                                       # I: 06:42 全部 (227 秒 = 57 小節)
         (R39, S2 + 1, 0.6, 0, 0.0, None, True),                                                  # II: 06:39 全部 (160 秒 = 40 小節)
         (R42, S3 + 1, 0.55, 0, 50.0, 180.0, True),                                               # III: 06:42 の後半 (50 秒から 180 秒)
         (R39, S4 + 1, 0.5, 0, 100.0, 60.0, True)]                                                # IV: 06:39 の終わり (100 秒から 60 秒)
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
KEY = {1: 'F', 2: 'G', 3: 'F', 4: 'G'}
SCALE = {'F': [5, 7, 9, 10, 0, 2, 4], 'G': [7, 9, 11, 0, 2, 4, 6]}
LOOP = {'F': ['F', 'Dm7', 'Bb', 'C7'], 'G': ['G', 'Em7', 'C', 'D7']}
CANDS = {'F': ['F', 'Fmaj7', 'Dm', 'Dm7', 'Bb', 'Bbmaj7', 'C', 'C7', 'Gm', 'Gm7', 'Am', 'Am7', 'A7', 'F/A', 'Bb/D', 'C/E', 'Dm/F'],
         'G': ['G', 'Gmaj7', 'Em', 'Em7', 'C', 'Cmaj7', 'D', 'D7', 'Am', 'Am7', 'Bm', 'Bm7', 'B7', 'G/B', 'C/E', 'D/F#', 'Em/G']}
TR = {R08: {'F': 5, 'G': 7}, R18: {'F': 0, 'G': 2}}                                               # トラック 8 (ハ長調) → ヘ / ト、トラック 18 (ニ短調) → ニ短調 (ヘ長調の平行調) / ホ短調
ENDS = {(R08, 'F'): ((72, 77), (69, 65), (72, 77), (65, 65)), (R08, 'G'): ((74, 79), (71, 67), (74, 79), (67, 67)),
        (R18, 'F'): ((69, 74), (65, 62), (69, 74), (62, 62)), (R18, 'G'): ((71, 76), (67, 64), (71, 76), (64, 64))}
def tune_from(rid, key, sm_extra=0, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), n=4):
    """録音の最上声の音を調の音階に寄せて、8 小節の主題に (句の終わりは主音 / 属音へ)"""
    sm = TR[rid][key] + sm_extra; sc = SCALE[key]; tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + sm
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in sc), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    ends = ENDS[(rid, key)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph % len(ends)], key=lambda x: abs(x - out[i][1])))
    return out
SUBJ = {(r, k): tune_from(r, k) for r in (R08, R18) for k in ('F', 'G')}
ANS = {(r, k): tune_from(r, k, 7) for r in (R08, R18) for k in ('F', 'G')}                         # 属調の応答 (5 度上、音階に寄せて)
def tr(mat, oct_): return [(d, m + oct_) for d, m in mat]
def head(mat): return mat[:6]                                                                     # 第 1 句 (2 小節)
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
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
def clip(mat, max_beats):
    out = []; t = 0.0
    for d, m in mat:
        if t >= max_beats: break
        out.append((min(d, max_beats - t), m)); t += d
    return out

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm, off, dur, lead in PLAYS:
            if not lead: continue
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: b = q // BPB; cur = LOOP[KEY[sec_of(b)]][b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = min(0.62, 0.42 + 0.006 * k) if k < S2 else 0.68 if k < S3 else (0.9 if k < S3 + 34 else 0.75) if k < S4 else max(0.08, 0.62 - 0.028 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    OCT = {'S': 0, 'A': 0, 'T': -12, 'B': -24}
    def expo(b0, subj, ans, order, gap=4, label=None):
        for i, v in enumerate(order):
            mat = subj if i % 2 == 0 else ans; top = max(m for _, m in mat)
            put(v, b0 + gap * i, tr(mat, OCT[v] + ((12 if top <= 72 else 0 if top <= 82 else -12) if v == 'S' else 0)), label if i == 0 else None)
    def stretto(b0, mat, order, gap=2, label=None):
        for i, v in enumerate(order): put(v, b0 + gap * i, tr(mat, OCT[v]), label if i == 0 else None)
    A_F, A_G, B_F, B_G = SUBJ[(R08, 'F')], SUBJ[(R08, 'G')], SUBJ[(R18, 'F')], SUBJ[(R18, 'G')]
    P.section(S1, 'I. 06:42 が表 — 主題 A の提示部 (ヘ長調, ♩=60)', '11/06 06:42 の実音 (表)。バックにフーガ: 主題 A (トラック 8 の音から) がアルト → ソプラノ (属調の応答) → テノール → バスと 4 小節ごとに入り、頭のストレッタ、続いて主題 B (トラック 18 の音から、ニ短調) がテノールから')
    expo(4, A_F, ANS[(R08, 'F')], ('A', 'S', 'T', 'B'), 4, '主題 A (トラック 8 の音から、ヘ長調)')
    stretto(26, head(A_F), ('S', 'A', 'T', 'B'), 2, '頭のストレッタ')
    expo(36, B_F, ANS[(R18, 'F')], ('T', 'A', 'S', 'B'), 4, '主題 B (トラック 18 の音から、ニ短調)')
    P.section(S2, 'II. 06:39 が表 — 主題 B の提示部 (ト長調〜ホ短調)', '11/06 06:39 の実音 (表)。主題 B (ホ短調) がバスから上へ 4 小節ごとに、次に主題 A (ト長調) と B を同時に、頭のストレッタ')
    expo(S2 + 2, B_G, ANS[(R18, 'G')], ('B', 'T', 'A', 'S'), 4, '主題 B (ホ短調)、バスから')
    put('S', S2 + 24, A_G, '主題 A (ト長調) と B を同時に'); put('T', S2 + 24, tr(B_G, -12), None)
    stretto(S2 + 33, head(A_G), ('A', 'S', 'T', 'B'), 2, None)
    P.section(S3, 'III. 06:42 の後半が表 — 二重フーガの頂点 (ヘ長調)', '06:42 の実音の後半 (50 秒から、表)。主題 A と B を対で (ソプラノ + テノール、アルト + バス)、2 小節遅れのストレッタ、バスに B の拡大 (2 倍)、鐘が 8 小節ごと')
    put('S', S3 + 2, A_F, '二重フーガ (頂点): A と B を対で'); put('T', S3 + 2, tr(B_F, -12), None)
    put('A', S3 + 10, ANS[(R08, 'F')], None); put('B', S3 + 12, tr(B_F, -24), None)
    put('S', S3 + 20, tr(A_F, 12 if max(m for _, m in A_F) <= 72 else 0), 'ストレッタ (2 小節遅れ)'); put('A', S3 + 22, B_F, None); put('T', S3 + 24, tr(A_F, -12), None); put('B', S3 + 26, tr(B_F, -24), None)
    put('B', S3 + 34, aug(tr(B_F, -24)), 'B の拡大 (2 倍、バス)')
    for k in range(6): put('S' if k % 2 == 0 else 'A', S3 + 36 + 2 * k, head(A_F) if k % 2 == 0 else head(B_F), None)
    P.section(S4, 'IV. 06:39 の終わりが表 — 消える (ト長調)', '06:39 の実音の終わり (100 秒から、表)。主題の頭を拡大して (ソプラノ A、バス B、アルト A)、鐘と高い共鳴だけが残って消える')
    put('S', S4 + 2, aug(head(A_G)), '頭の拡大'); put('B', S4 + 6, aug(tr(head(B_G), -24)), None); put('A', S4 + 10, aug(head(A_G)), None); put('T', S4 + 14, aug(tr(head(A_G), -12)), None)
    for sec, (b0, b1) in {1: (S1, S2), 2: (S2, S3), 3: (S3, S4), 4: (S4, TOTAL)}.items(): harm_fit(P, b0 + 1, min(b1, TOTAL - 3), [e for e in E if b0 * BPB <= e[0] < b1 * BPB], CANDS[KEY[sec]])
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 1 else 0.02, fout=6.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (表%s)' % (NAMES[rid], '、抜粋' if dur else ''))
    first = True
    for b in range(S1 + 4, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.13 * P.dyn.get(b, 0.7) / 0.7, '低いペダルの音 (2 小節ごと)' if first else None); first = False
    first = True
    for b, g in [(S1 + 2, 0.22), (S2 + 1, 0.22), (S3 + 1, 0.26), (S4 + 1, 0.22), (TOTAL - 4, 0.2)] + [(S3 + 9 + 8 * k, 0.14) for k in range(4)]:
        add('X', b * BPB, 14, 41 if KEY[sec_of(b)] == 'F' else 43, g, '鐘 (レクイエム)' if first else None); first = False
    first = True
    for b0, mat in ((S4 + 2, aug(head(SUBJ[(R08, 'G')]))), (S4 + 10, aug(head(SUBJ[(R08, 'G')]))), (S3 + 20, SUBJ[(R08, 'F')])):
        t = b0 * BPB + 1
        for d, m in mat: add('H', t, d, m + 12, 0.08 * P.dyn.get(int(t // BPB), 0.7) / 0.7, '高い共鳴 (反響、pp)' if first else None); first = False; t += d

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R42, R39], 'piano_decay': 2.6, 'reverb': [6.0, 2.5, 0.45],
        'title': 'Requiem BADA — CLX · Fuga doppia sotto le mattine',
        'subtitle': '11/06 06:42・06:39 をメインに (実音、表)、バックはトラック 8・18 の音から作った 2 つの主題でバッハ風の二重フーガ (06:42 の実音のピアノの 1 音のサンプラー)、レクイエムを醸す: I 主題 A の提示部 (ヘ長調) → II 主題 B の提示部 (ホ短調) → III 二重フーガの頂点 → IV 消える。♩=60',
        'legend': ['PF', 'H', 'L', 'X'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル', 'X': '鐘'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['主題 A = トラック 8 の最上声の音 (調の音階に寄せて 8 小節)、主題 B = トラック 18 の最上声の音 (短調、8 小節)。応答は 5 度上 (属調)。トラック 8・18 の録音そのものは鳴らさない。和音は表の録音の採譜を優先しつつ主題の音を含む和音を半小節ごとに',
                   '06:42・06:39 は実音、そのまま (06:42 → 06:39 → 06:42 の後半 → 06:39 の終わり)。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘は段落の頭と頂点の 8 小節ごと。声なし。']}

if __name__ == '__main__':
    for (r, k), mat in SUBJ.items(): print('subj', 'A' if r == R08 else 'B', k, ' '.join('%s:%g' % (name_of(m), d) for d, m in mat[:12]))
    compose.main(OUT, seed=160, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
