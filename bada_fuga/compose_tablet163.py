#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXIII · Requiem e fuga sopra la traccia 3 (2026/11/06 06:39・06:42・tablet162・トラック 3 を合成して、レクイエムとフーガを併せ持つ曲に)
  表 (実音) を段落ごとに: 06:42 (ヘ長調、そのまま) → 06:39 (全音下げてヘ長調に) → tablet162 の頂点の段 (ヘ長調 / ニ短調) → トラック 3 (半音上げてヘ長調に、終わり)。トラック 3 (14 分、ホ長調、静かな録音) は半音上げて全曲の裏にも
  フーガ = トラック 3 の音から作った主題 (8 小節、ヘ長調) の 4 声フーガ (06:42 の実音のピアノの 1 音のサンプラー): 提示部 (I) → ストレッタ (II) → 定旋律と同時に (III) → 拡大 (IV)
  レクイエム = 「Dies irae」の聖歌の冒頭句 (ファ・ミ・ファ・レ・ミ・ド・レ・レ、ニ短調) を定旋律として拡大して (2 倍・4 倍)、低い鐘 (小さく、段落の頭)、低いペダル、2 分音符の心拍 (バス)、頂点から消えていく強弱
  使い方: python compose_tablet163.py <bank163.json (bank150 + トラック 3 の採譜)> <wav のフォルダ> [score_tablet163.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet163.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R03, R162 = '20261106_063938', '20261106_064228', '20261107_030000', '20261107_162000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 106, 154, 184
NAMES = {R39: '11/06 06:39', R42: '11/06 06:42', R03: 'トラック 3', R162: 'tablet162'}
FILE = {R39: R39 + '_clean.wav', R42: R42 + '_clean.wav', R03: R03 + '.wav', R162: R162 + '.wav'}
DUR = {R39: 160.3, R42: 226.7, R03: 863.1, R162: 727.0}
PLAYS = [(R03, 0, 0.5, 1, 0.0, 560.0, False),                                                     # 裏: トラック 3 (半音上げて、0〜560 秒 → 132 小節)
         (R42, 1, 0.6, 0, 0.0, None, True),                                                       # I: 06:42 全部 (57 小節)
         (R39, S2 + 1, 0.6, -2, 0.0, None, True),                                                 # II: 06:39 全音下げて (180 秒 = 45 小節)
         (R162, S3 + 1, 0.55, 0, 352.0, 188.0, True),                                             # III: tablet162 の頂点の段 (352 秒から 188 秒)
         (R03, S4 + 1, 0.7, 1, 640.0, 115.0, True)]                                               # IV: トラック 3 の終わり近く (640 秒から、表)
def play_len(rid, dur): return DUR[rid] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
SCALE = [5, 7, 9, 10, 0, 2, 4]
LOOP = ['Dm', 'Bb', 'F', 'C']
CANDS = ['F', 'Fmaj7', 'Dm', 'Dm7', 'Bb', 'Bbmaj7', 'C', 'C7', 'Gm', 'Gm7', 'Am', 'Am7', 'A7', 'F/A', 'Bb/D', 'C/E', 'Dm/F']
def tune_from(rid, sm, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), ends=((72, 77), (69, 65), (72, 77), (65, 65)), n=4):
    """録音の最上声の音をヘ長調の音階に寄せて 8 小節の主題に"""
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + sm
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in SCALE), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph % 4], key=lambda x: abs(x - out[i][1])))
    return out
SUBJ = tune_from(R03, 1); ANSW = tune_from(R03, 8)
DIES = [(1, 65), (1, 64), (1, 65), (1, 62), (1, 64), (1, 60), (1, 62), (1, 62)]                   # Dies irae の冒頭句 (ニ短調: ファ・ミ・ファ・レ・ミ・ド・レ・レ)
def tr(mat, o): return [(d, m + o) for d, m in mat]
def head(mat): return mat[:6]
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
            if not lead or rid not in RECS: continue
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: b = q // BPB; cur = LOOP[b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = min(0.6, 0.4 + 0.006 * k) if k < S2 else 0.68 if k < S3 else (0.9 if k < S3 + 32 else 0.78) if k < S4 else max(0.08, 0.62 - 0.02 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    OCT = {'S': 0, 'A': 0, 'T': -12, 'B': -24}
    def expo(b0, order, gap=4, label=None):
        for i, v in enumerate(order):
            mat = SUBJ if i % 2 == 0 else ANSW; top = max(m for _, m in mat)
            put(v, b0 + gap * i, tr(mat, OCT[v] + ((12 if top <= 72 else 0 if top <= 82 else -12) if v == 'S' else 0)), label if i == 0 else None)
    def stretto(b0, mat, order, gap=2, label=None):
        for i, v in enumerate(order): put(v, b0 + gap * i, tr(mat, OCT[v]), label if i == 0 else None)
    P.section(S1, 'I. 06:42 — フーガの提示部 (ヘ長調, ♩=60)', '06:42 の実音 (表)、トラック 3 (半音上げて) が裏に。主題 (トラック 3 の音から) がアルト → ソプラノ (属調の応答) → テノール → バスと 4 小節ごとに。低い鐘が小さく')
    expo(4, ('A', 'S', 'T', 'B'), 4, '主題 (トラック 3 の音から、ヘ長調)')
    stretto(28, head(SUBJ), ('S', 'A', 'T', 'B'), 2, '頭のストレッタ')
    put('T', 40, tr(aug(DIES), -12), 'Dies irae (定旋律、2 倍、テノール)'); put('S', 48, SUBJ, None)
    P.section(S2, 'II. 06:39 (全音下げて) — ストレッタと Dies irae', '06:39 を全音下げてヘ長調に (表)。主題のストレッタ (2 小節遅れ、バスから)、Dies irae の定旋律がアルトで (2 倍)、心拍が始まる')
    stretto(S2 + 2, SUBJ, ('B', 'T', 'A', 'S'), 2, 'ストレッタ (2 小節遅れ)')
    put('A', S2 + 16, aug(DIES), 'Dies irae (アルト)'); put('S', S2 + 20, tr(ANSW, 0), None); put('T', S2 + 26, tr(SUBJ, -12), None)
    put('A', S2 + 36, aug(DIES), None); put('B', S2 + 36, tr(aug(DIES), -24), None)
    P.section(S3, 'III. tablet162 の頂点 — 定旋律と主題を同時に (頂点)', 'tablet162 (CLXII) の頂点の段 (表)。Dies irae を 4 倍に伸ばしてソプラノで、その下で主題が 4 声に、心拍 (2 分音符、バス)、鐘が 8 小節ごと')
    put('S', S3 + 2, aug(DIES, 4), 'Dies irae (4 倍、ソプラノ)'); put('A', S3 + 2, SUBJ, None); put('T', S3 + 6, tr(ANSW, -12), None); put('B', S3 + 10, tr(SUBJ, -24), None)
    put('S', S3 + 20, aug(DIES, 4), None); put('A', S3 + 22, ANSW, None); put('T', S3 + 24, tr(SUBJ, -12), None); put('B', S3 + 26, tr(ANSW, -24), None)
    put('A', S3 + 38, aug(DIES), None); put('S', S3 + 40, tr(head(SUBJ), 12 if max(m for _, m in head(SUBJ)) <= 72 else 0), None); put('T', S3 + 42, tr(head(SUBJ), -12), None)
    P.section(S4, 'IV. トラック 3 — 拡大して消える', 'トラック 3 の終わり近く (表、半音上げて)。主題の頭を 2 倍に伸ばしてバスとテノールで、Dies irae がアルトで最後に一度、鐘と低いペダルだけが残って消える')
    put('B', S4 + 2, aug(tr(head(SUBJ), -24)), '主題の頭 (2 倍、バス)'); put('T', S4 + 8, aug(tr(head(SUBJ), -12)), None); put('A', S4 + 12, aug(DIES), 'Dies irae (最後に)'); put('S', S4 + 20, aug(tr(head(SUBJ), 0)), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    # 心拍 (2 分音符、バス) — II の後半から IV の初めまで、バスが空いている小節だけ
    first = True
    for b in range(S2 + 20, S4 + 6):
        if all((b * BPB + j) in P.rest['B'] for j in range(BPB)):
            for k in (0, 2):
                r = tones_of(P.harm[b * BPB + k], 36, 48)[0]; P.rest['B'].difference_update((b * BPB + k, b * BPB + k + 1)); P.place('B', b, [(1.6, r)], 0, '心拍 (2 分音符)' if first else None, beat=k); first = False
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 0 else 0.02, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s%s' % (NAMES[rid], '表' if lead else '裏', {1: '、半音上げて', -2: '、全音下げて', 0: ''}[sm] + ('、抜粋' if dur else '')))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.13 * P.dyn.get(b, 0.7) / 0.7, '低いペダルの音 (2 小節ごと)' if first else None); first = False
    first = True
    for b, g in [(S1 + 2, 0.16), (S2 + 1, 0.16), (S3 + 1, 0.2), (S4 + 1, 0.16), (TOTAL - 4, 0.14)] + [(S3 + 9 + 8 * k, 0.11) for k in range(4)] + [(S4 + 9 + 8 * k, 0.1) for k in range(2)]:
        add('X', b * BPB, 14, 38, g, '低い鐘 (小さく)' if first else None); first = False
    first = True
    for b0, mat in ((S3 + 2, aug(DIES, 4)), (S3 + 20, aug(DIES, 4))):
        t = b0 * BPB + 1
        for d, m in mat: add('H', t, d, m + 12, 0.06 * P.dyn.get(int(t // BPB), 0.7) / 0.7, '定旋律の反響 (pp)' if first else None); first = False; t += d

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R42, R39, R162, R03], 'piano_decay': 2.6, 'reverb': [6.0, 2.5, 0.45],
        'title': 'Requiem BADA — CLXIII · Requiem e fuga sopra la traccia 3',
        'subtitle': '11/06 06:39・06:42・tablet162・トラック 3 を合成して、レクイエムとフーガを併せ持つ曲に: フーガ = トラック 3 の音から作った主題の 4 声 (提示部 → ストレッタ → 定旋律と同時に → 拡大)、レクイエム = Dies irae の冒頭句の定旋律 (2 倍・4 倍)、低い鐘、心拍。表は 06:42 → 06:39 (全音下げて) → tablet162 の頂点 → トラック 3 (半音上げて)。ヘ長調 / ニ短調、♩=60',
        'legend': ['PF', 'H', 'L', 'X'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル', 'X': '低い鐘'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['主題 = トラック 3 (録音、ホ長調) の最上声の音を半音上げてヘ長調の音階に寄せた 8 小節、応答は 5 度上。定旋律 = Dies irae (聖歌) の冒頭句 ファ・ミ・ファ・レ・ミ・ド・レ・レ (ニ短調) を 2 倍・4 倍に。和音は表の録音の採譜を優先しつつ主題と定旋律の音を含む和音を半小節ごとに',
                   'トラック 3 は半音上げて全曲の裏 (0〜560 秒) と終わりの表に。06:39 は全音下げて、06:42 と tablet162 はそのまま。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘は低く小さく。声なし。']}

if __name__ == '__main__':
    print('subj', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ[:12]))
    compose.main(OUT, seed=163, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
