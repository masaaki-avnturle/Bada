#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXXIX · Le due mattine, il 18:54 e il 117 — seconda versione (tablet117・2026/11/06 18:54・06:39・06:42 を重ね合わせて、元の楽器を演奏させて、第 2 版 — アルペジオや元の曲に無い楽器は付け加えない)
  CLXXXVI と同じ 4 つの音源で配置を変える: 06:39 を先に、元のト長調のまま (その間は tablet117 のヘ長調の段を全音上げてト長調に)、06:42 はヘ長調のまま (tablet117 はそのまま)。18:54 は途切れなく 3 回半
  元の楽器 = 録音の中にある楽器 (ピアノ) だけ: 06:39 の旋律 (ト長調) と 06:42 の旋律 (ヘ長調) を実音のピアノ (06:42 の 1 音のサンプラー) で、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フックは付け加えない
  和音は表の録音 (06:39・06:42) の採譜から
  使い方: python compose_tablet189.py <bank150.json> <wav のフォルダ (20261106_185402.wav, 20261106_063938_clean.wav, 20261106_064228_clean.wav, 20261003_117000.wav)> [score_tablet189.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet189.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R39, R117, R1854 = '20261106_064228', '20261106_063938', '20261003_117000', '20261106_185402'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 44, 104, 140, 176
NAMES = {R42: '11/06 06:42', R39: '11/06 06:39', R117: 'tablet117', R1854: '11/06 18:54'}
FILE = {R42: R42 + '_clean.wav', R39: R39 + '_clean.wav', R117: R117 + '.wav', R1854: R1854 + '.wav'}
DUR = {R42: 226.7, R39: 160.3, R117: 778.6, R1854: 205.8}
PLAYS = [(R1854, k * 50, 0.5, 0, 0.0, 205.8 if k < 3 else 96.0, False) for k in range(4)] + [           # 18:54 を途切れなく
         (R117, 0, 0.3, 2, 152.0, 168.0, False), (R117, S2, 0.3, 0, 152.0, 168.0, False), (R117, S2 + 38, 0.3, 0, 152.0, 90.0, False), (R117, S3, 0.3, 2, 152.0, 160.0, False), (R117, S4, 0.3, 0, 152.0, 150.0, False),   # tablet117 のヘ長調の段 (ト長調の段落では全音上げて)
         (R39, 1, 0.55, 0, 0.0, None, True),                                                      # I: 06:39 全部 (ト長調、そのまま、40 小節)
         (R42, S2 + 1, 0.55, 0, 0.0, None, True),                                                 # II: 06:42 全部 (ヘ長調、57 小節)
         (R39, S3 + 1, 0.5, 0, 20.0, 140.0, True),                                                # III: 06:39 の後半 (20 秒から、ト長調)
         (R42, S4 + 1, 0.5, 0, 100.0, 126.0, True)]                                               # IV: 06:42 の中から終わりへ (100 秒から)
def play_len(rid, dur): return DUR[rid] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
CANDS = ['F', 'Fmaj7', 'Dm', 'Dm7', 'Bb', 'Bbmaj7', 'C', 'C7', 'Gm', 'Gm7', 'Am', 'Am7', 'A7', 'F/A', 'Bb/D', 'C/E', 'Dm/F']
CANDS_G = ['G', 'Gmaj7', 'Em', 'Em7', 'C', 'Cmaj7', 'D', 'D7', 'Am', 'Am7', 'Bm', 'Bm7', 'B7', 'G/B', 'C/E', 'D/F#', 'Em/G', 'Dm7', 'Fmaj7']
LOOP = ['Dm', 'Bb', 'F', 'C']
SCALE = [5, 7, 9, 10, 0, 2, 4]; SCALE_G = [7, 9, 11, 0, 2, 4, 6]
def tune_from(rid, sm, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), ends=((69, 74), (65, 62), (69, 74), (62, 62)), n=4):
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
T42 = tune_from(R42, 0, ends=((72, 77), (69, 65), (72, 77), (65, 65)))
SCALE_F = SCALE; SCALE = SCALE_G; T39 = tune_from(R39, 0, ends=((74, 79), (71, 67), (74, 79), (67, 67))); SCALE = SCALE_F   # 06:39 の旋律はト長調のまま
def tr(mat, o): return [(d, m + o) for d, m in mat]
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
        if cur is None: b = q // BPB; cur = (['G', 'Em7', 'C', 'D7'] if sec_of(b) in (1, 3) else LOOP)[b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.5 if k < S2 else 0.6 if k < S3 else 0.7 if k < S4 else max(0.1, 0.6 - 0.014 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. 06:39 (ト長調, ♩=60)', '18:54 の実音と 06:39 (そのままの調)、tablet117 のヘ長調の段を全音上げて裏に。元の楽器: 06:39 の旋律を実音のピアノで (アルト → テノール)、低いペダル')
    put('A', 6, T39, '06:39 の旋律 (実音のピアノ、ト長調)'); put('T', 22, tr(T39, -12), None); put('S', 34, T39, None)
    P.section(S2, 'II. 06:42 (ヘ長調)', '18:54 と 06:42 (全部)、tablet117 はそのまま。06:42 の旋律を実音のピアノで (ソプラノ → テノール → アルト)')
    put('S', S2 + 6, T42, '06:42 の旋律 (実音のピアノ、ヘ長調)'); put('T', S2 + 22, tr(T42, -12), None); put('A', S2 + 38, T42, None); put('B', S2 + 48, aug(tr(T42[:6], -24)), None)
    P.section(S3, 'III. 06:39 の後半 (ト長調)', '18:54 と 06:39 の後半 (20 秒から)。06:39 の旋律を 2 声で (ソプラノとテノール、2 小節遅れ)')
    put('S', S3 + 4, T39, '2 声で'); put('T', S3 + 6, tr(T39, -12), None); put('A', S3 + 20, T39, None); put('B', S3 + 22, tr(T39, -24), None)
    P.section(S4, 'IV. 06:42 の終わり — 消える', '18:54 と 06:42 の中から終わりへ (100 秒から)。06:42 の旋律 (アルト)、頭を 2 倍に伸ばして、tablet117 とペダルだけが残って消える')
    put('A', S4 + 4, T42, None); put('T', S4 + 14, aug(tr(T42[:6], -12)), '頭を 2 倍に'); put('B', S4 + 22, aug(tr(T42[:6], -24)), None)
    for sec, (b0, b1) in {1: (S1, S2), 2: (S2, S3), 3: (S3, S4), 4: (S4, TOTAL)}.items(): harm_fit(P, b0 + 1, min(b1, TOTAL - 3), [e for e in E if b0 * BPB <= e[0] < b1 * BPB], CANDS_G if sec in (1, 3) else CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else ('、ヘ長調の段を裏に' + ('、全音上げて' if sm else '') if rid == R117 else '、そのまま')))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R42, R1854, R117], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXXIX · Le due mattine, il 18:54 e il 117 — seconda versione',
        'subtitle': 'tablet117・11/06 18:54・06:39・06:42 を重ね合わせて、元の楽器 (06:39・06:42 の旋律を実音のピアノで、低いペダル) を演奏させて、第 2 版: 06:39 を先にト長調のまま、06:42 はヘ長調のまま、tablet117 のヘ長調の段はト長調の段落では全音上げて。アルペジオや元の曲に無い楽器は付け加えない。♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['18:54 は rms −22 dB に揃えて途切れなく 3 回半 (0.5)。06:39 (ト長調) と 06:42 (ヘ長調) はそのままの調 (0.55 / 0.5)、tablet117 はヘ長調の段 (152〜320 秒) を裏に 0.3、ト長調の段落では全音上げて。和音は表の録音の採譜を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '楽器 = 06:39 (ト長調)・06:42 (ヘ長調) の最上声の音から作った旋律 (各 8 小節) を 06:42 の実音のピアノの 1 音のサンプラーで、2 小節ごとの低いペダル。鐘なし、声なし、他の楽器なし。']}

if __name__ == '__main__':
    print('T42', ' '.join('%s:%g' % (name_of(m), d) for d, m in T42[:6]), '| T39', ' '.join('%s:%g' % (name_of(m), d) for d, m in T39[:6]))
    compose.main(OUT, seed=189, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
