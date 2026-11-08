#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXC · La fuga d'organo al pianoforte vero (2026/11/06 18:54・06:39・06:42・tablet86・tablet89・fuga を重ね合わせて、元の楽器を演奏させて — アルペジオや元の曲に無い楽器は付け加えない、電子音はグランドピアノの実音で書き換える)
  電子音の書き換え: fuga (Requiem BADA の最初のオルガンのフーガ、ニ短調、130 小節 ♩=96) はオルガン (合成) なので音声は使わず、楽譜 (score.json) の 2,324 音を秒のまま 06:42 の実音のピアノの 1 音のサンプラーで弾き直す (II に提示部、IV に終わり)。tablet89 (LXXXIX) は cp14 の合成の伴奏を含むので音声は使わず、採譜した旋律だけを実音のピアノで。tablet86 (LXXXVI) はもともと実音のピアノの 1 音のサンプラーだけなので、音声を全音下げて (ト長調 → ヘ長調) 裏に
  テープ: 11/06 18:54 の実音 (rms −22 dB に揃えたもの) を途切れなく 3 回半 (0.4)、06:42 (ヘ長調、そのまま) と 06:39 (全音下げてヘ長調に) を表に、tablet86 (全音下げて) を裏に (0.3)
  元の楽器 = 実音のピアノだけ: 06:42・06:39・tablet89・tablet86 の最上声の音から作った旋律 (各 8 小節、ヘ長調に寄せて) と fuga の楽譜の音符、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フックは付け加えない
  和音は表の録音 (06:42・06:39) の採譜から、fuga が鳴っているところは fuga の楽譜の和音
  使い方: python compose_tablet190.py <bank190.json (bank150 + tablet86・89 の採譜)> <wav のフォルダ> <score.json (fuga)> [score_tablet190.json]
"""
import sys, os, json, math
BANKP, WDIR, FUGAP = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]; OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet190.json'
FUGA = json.load(open(FUGAP)); FH = FUGA['harm']; FBPM = FUGA['bpm']
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R39, R86, R89, R1854 = '20261106_064228', '20261106_063938', '20261107_086000', '20261107_089000', '20261106_185402'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 108, 150, 184
FUGA_AT = [(S2 + 2, 0.0, 100.0), (S4 + 2, 232.0, 100.0)]                                           # (小節, fuga の秒, 長さ秒): II に提示部、IV に終わり
NAMES = {R42: '11/06 06:42', R39: '11/06 06:39', R86: 'tablet86', R1854: '11/06 18:54'}
FILE = {R42: R42 + '_clean.wav', R39: R39 + '_clean.wav', R86: R86 + '.wav', R1854: R1854 + '.wav'}
DUR = {R42: 226.7, R39: 160.3, R86: 245.0, R1854: 205.8}
PLAYS = [(R1854, k * 50, 0.4, 0, 0.0, 205.8 if k < 3 else 128.0, False) for k in range(4)] + [(R86, 0, 0.3, -2, 0.0, 245.0, False), (R86, S3, 0.3, -2, 0.0, 245.0, False)] + [   # 18:54 を途切れなく、tablet86 (全音下げて) を裏に
         (R42, 2, 0.55, 0, 0.0, None, True),                                                      # I: 06:42 全部
         (R39, S2 + 1, 0.5, -2, 0.0, None, True),                                                 # II: 06:39 全音下げて (fuga の提示部と)
         (R42, S3 + 1, 0.5, 0, 60.0, 166.0, True),                                                # III: 06:42 の後半
         (R39, S4 + 1, 0.45, -2, 90.0, 70.0, True)]                                               # IV: 06:39 の終わり (fuga の終わりと)
def play_len(rid, dur): return DUR[rid] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
CANDS = ['F', 'Fmaj7', 'Dm', 'Dm7', 'Bb', 'Bbmaj7', 'C', 'C7', 'Gm', 'Gm7', 'Am', 'Am7', 'A7', 'F/A', 'Bb/D', 'C/E', 'Dm/F']
LOOP = ['Dm', 'Bb', 'F', 'C']
SCALE = [5, 7, 9, 10, 0, 2, 4]
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
ENDS_F = ((72, 77), (69, 65), (72, 77), (65, 65))
T42 = tune_from(R42, 0, ends=ENDS_F); T39 = tune_from(R39, -2, ends=ENDS_F); T89 = tune_from(R89, 0, ends=ENDS_F); T86 = tune_from(R86, -2, ends=ENDS_F)
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
        if cur is None:
            cur = None
            for b0, off, L in FUGA_AT:
                if b0 * BPB <= q < b0 * BPB + L:
                    fq = int(((q - b0 * BPB) + off) * FBPM / 60.0); cur = FH[min(fq, len(FH) - 1)]; RECQ.add(q)
            if cur is None: b = q // BPB; cur = LOOP[b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.5 if k < S2 else 0.6 if k < S3 else 0.7 if k < S4 else max(0.1, 0.6 - 0.016 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. 06:42 (ヘ長調, ♩=60)', '18:54 の実音と 06:42、tablet86 (全音下げて、実音のピアノ) が裏に。元の楽器: 06:42 の旋律と tablet86 の旋律を実音のピアノで、低いペダル')
    put('A', 8, T42, '06:42 の旋律 (実音のピアノ)'); put('T', 24, tr(T86, -12), 'tablet86 の旋律'); put('S', 42, T42, None)
    P.section(S2, 'II. 06:39 (全音下げて) — fuga の提示部をグランドピアノで', '18:54 と 06:39 (ヘ長調に)。fuga (オルガンのフーガ、ニ短調) の提示部の音符を秒のまま実音のピアノで弾き直す (電子音の書き換え)、06:39 の旋律がアルトで')
    put('A', S2 + 30, T39, '06:39 の旋律'); put('T', S2 + 40, tr(T89, -12), 'tablet89 の旋律 (実音のピアノ)')
    P.section(S3, 'III. 06:42 の後半 — 4 つの旋律', '18:54 と 06:42 の後半、tablet86 が裏に。06:42 (ソプラノ) と 06:39 (テノール) の旋律を同時に、次に tablet89 (アルト) と tablet86 (バス) を同時に')
    put('S', S3 + 4, T42, '4 つの旋律'); put('T', S3 + 6, tr(T39, -12), None); put('A', S3 + 20, T89, None); put('B', S3 + 22, tr(T86, -24), None); put('S', S3 + 32, T89, None)
    P.section(S4, 'IV. 06:39 の終わり — fuga の終わりをグランドピアノで', '18:54 と 06:39 の終わり。fuga の終わり (ストレッタと終止) の音符を実音のピアノで、頭を 2 倍に伸ばして、ペダルだけが残って消える')
    put('T', S4 + 30, aug(tr(T42[:6], -12)), '頭を 2 倍に'); put('B', S4 + 34, aug(tr(T39[:6], -24)), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else ('、全音下げて、裏に (実音のピアノ)' if rid == R86 else ('、全音下げて' if sm else '、そのまま'))))
    first = True
    for b0, off, L in FUGA_AT:                                                                   # fuga の音符を秒のまま実音のピアノで (PF、rid = 06:42 の 1 音)
        for n in FUGA['notes']:
            if off <= n['t'] < off + L - 0.2:
                t = b0 * BPB + (n['t'] - off); d = min(n['d'], off + L - n['t'])
                add('PF', t, d, n['m'], round(0.36 * (0.85 if n['v'] in 'AT' else 1.0) * (0.6 if (n['t'] - off) > L - 8 else 1.0), 4), 'fuga の音符 (オルガン → 実音のピアノ)' if first else None, rid=PSRC, rel=0.5, layer='fuga'); first = False
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R42, R39, R1854, R86], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXC · La fuga d\'organo al pianoforte vero',
        'subtitle': '11/06 18:54・06:39・06:42・tablet86・tablet89・fuga を重ね合わせて、元の楽器を演奏させて、電子音はグランドピアノの実音で書き換え: fuga (オルガン) の楽譜の音符と tablet89 の旋律を実音のピアノで、tablet86 (実音のピアノ) は全音下げて裏に。アルペジオや元の曲に無い楽器は付け加えない。ヘ長調 / ニ短調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['fuga (score.json、ニ短調 ♩=96) は音声を使わず、楽譜の音符 (4 声) を秒のまま 06:42 の実音のピアノの 1 音のサンプラーで: II に提示部 (0〜100 秒)、IV に終わり (232〜332 秒)。tablet89 は cp14 の合成の伴奏を含むので音声を使わず旋律だけ。tablet86 は実音のピアノの 1 音だけで作った曲なので音声を全音下げて裏に',
                   '18:54 は rms −22 dB に揃えて途切れなく 3 回半 (0.4)。06:42 (ヘ長調) はそのまま、06:39 は全音下げて。和音は表の録音の採譜、fuga が鳴るところは fuga の楽譜の和音。楽器は実音のピアノと 2 小節ごとの低いペダルだけ。鐘なし、声なし。']}

if __name__ == '__main__':
    print('T89', ' '.join('%s:%g' % (name_of(m), d) for d, m in T89[:6]), '| T86', ' '.join('%s:%g' % (name_of(m), d) for d, m in T86[:6]))
    compose.main(OUT, seed=190, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
