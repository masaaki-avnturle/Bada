#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXXI · L'aureola sensuale, le due tracce e la fuga (ドエロの光輪様の声の雑音を消して、トラック 18・トラック 8・fuga を重ね合わせ、無い楽器を使わずに、元の楽器を弾いて)
  声: ドエロの光輪様の声から息のノイズ層を外したもの (14:55 の声を 10.5 半音上げ・フォルマント 1.10 倍の少し低めの女声、3 kHz 以上 +4 dB の囁きの成分、250 Hz 以下 +3 dB の近接の低音、柔らかい圧縮、5 度上 0.3 と 1 オクターヴ上 0.25、3.5 秒の残響、rms −22.5 dB)。18:54 は無し
  fuga (オルガンのフーガ、ニ短調) は CXC / CXCVIII と同じく電子音のオルガンを鳴らさず、楽譜の音符を秒のまま 06:42 の実音のピアノで弾き直す (II に提示部、IV に終わり)
  元の楽器 = 実音のピアノだけ: 声・トラック 18・トラック 8 の最上声の音から作った旋律 (各 8 小節) と fuga の楽譜の音符、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フック・鐘は付け加えない
  和音は表の録音 (声・トラック 18・8) の採譜から、fuga が鳴っているところは fuga の楽譜の和音
  使い方: python compose_tablet221.py <bank201.json> <wav のフォルダ (20261108_145525.wav = 雑音を消したドエロの光輪の声, 20261107_180000.wav, 20261107_080000.wav)> <score.json (fuga)> [score_tablet221.json]
"""
import sys, os, json, math
BANKP, WDIR, FUGAP = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]; OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet221.json'
FUGA = json.load(open(FUGAP)); FH = FUGA['harm']; FBPM = FUGA['bpm']
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, RV, R18, R08 = '20261106_064228', '20261108_145525', '20261107_180000', '20261107_080000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 100, 158, 184
FUGA_AT = [(S2 + 1, 0.0, 100.0), (S4 + 1, 232.0, 100.0)]                                           # (小節, fuga の秒, 長さ秒): II に提示部、IV に終わり
NAMES = {RV: '11/08 14:55 の声 (雑音を消したドエロの光輪様の声)', R18: 'トラック 18', R08: 'トラック 8'}
FILE = {RV: RV + '.wav', R18: R18 + '.wav', R08: R08 + '.wav'}
DUR = {RV: 198.5, R18: 149.1, R08: 249.2}
PLAYS = [
         (R08, 2, 0.3, 5, 0.0, 200.0, False), (RV, 2, 0.55, 0, 0.0, None, True),                   # I: 声 (58 小節、表)、トラック 8 (4 度上げて) が裏
         (R18, S2 + 1, 0.5, 0, 0.0, None, True),                                                  # II: トラック 18 (fuga の提示部と)
         (RV, S3 + 2, 0.55, 0, 0.0, None, True), (R08, S3 + 2, 0.4, 5, 100.0, 149.2, False),       # III: 声 (2 回目)、トラック 8 の続きが裏
         (R18, S4 + 2, 0.4, 0, 60.0, 89.0, True)]                                                 # IV: トラック 18 の後半 (fuga の終わりと)
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
TV = tune_from(RV, 0, ends=ENDS_F); T18 = tune_from(R18, 0); T8 = tune_from(R08, 5)
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
    P.section(S1, 'I. 声 (ヘ長調 / ニ短調, ♩=60)', 'ドエロの光輪様の声 (雑音なし)、トラック 8 (4 度上げて) が裏に。元の楽器: 声の旋律を実音のピアノで (アルト → テノール)、トラック 8 の旋律がバスで、低いペダル')
    put('A', 8, TV, '声の旋律 (実音のピアノ)'); put('T', 24, tr(TV, -12), None); put('B', 40, tr(T8, -24), 'トラック 8 の旋律')
    P.section(S2, 'II. トラック 18 — fuga の提示部をグランドピアノで', 'トラック 18。fuga (オルガンのフーガ、ニ短調) の提示部の音符を秒のまま実音のピアノで弾き直す (電子音の書き換え)、トラック 18 の旋律がアルトで')
    put('A', S2 + 28, T18, 'トラック 18 の旋律'); put('T', S2 + 34, tr(T18, -12), None)
    P.section(S3, 'III. 声 (2 回目) — 3 つの旋律', '光輪の声をもう一度、トラック 8 の続きが裏に。声 (ソプラノ) とトラック 18 (テノール) の旋律を同時に、次にトラック 8 (アルト) と声 (バス)')
    put('S', S3 + 6, TV, '3 つの旋律'); put('T', S3 + 8, tr(T18, -12), None); put('A', S3 + 24, T8, None); put('B', S3 + 26, tr(TV, -24), None); put('S', S3 + 40, T18, None)
    P.section(S4, 'IV. トラック 18 の後半 — fuga の終わりをグランドピアノで', 'トラック 18 の後半。fuga の終わり (ストレッタと終止) の音符を実音のピアノで、頭を 2 倍に伸ばして、ペダルだけが残って消える')
    put('T', S4 + 18, aug(tr(TV[:6], -12)), '頭を 2 倍に'); put('B', S4 + 22, aug(tr(T18[:6], -24)), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、雑音を消したドエロの光輪の声' if rid == RV else ('、4 度上げて' + ('、裏に' if not lead else '') if sm else '、そのまま')))
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

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R18, R08], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXI · L\'aureola sensuale, le due tracce e la fuga',
        'subtitle': 'ドエロの光輪様の声 (息のノイズを外して)・トラック 18・トラック 8・fuga を重ね合わせて、無い楽器を使わずに元の楽器を弾いて: 声・トラック 18・8 の旋律と fuga (オルガン) の楽譜の音符を実音のピアノで、低いペダル。アルペジオや元の曲に無い楽器は付け加えない。ヘ長調 / ニ短調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['声 = ドエロの光輪様の声から息のノイズ層を外したもの (10.5 半音上げ・フォルマント 1.10 倍、囁きの成分と近接の低音、5 度上 0.3 + 1 オクターヴ上 0.25、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.55)。トラック 18 (ニ短調) はそのまま 2 回、トラック 8 (ハ長調 / イ短調) は 4 度上げて 2 回 (裏)。fuga (score.json、ニ短調 ♩=96) は音声を使わず楽譜の音符を秒のまま実音のピアノで: II に提示部、IV に終わり',
                   '和音は表の録音の採譜、fuga が鳴るところは fuga の楽譜の和音。楽器は 06:42 の実音のピアノの 1 音のサンプラーと 2 小節ごとの低いペダルだけ。鐘なし、合成の声なし。']}

if __name__ == '__main__':
    print('TV', ' '.join('%s:%g' % (name_of(m), d) for d, m in TV[:6]), '| T18', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18[:6]))
    compose.main(OUT, seed=221, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
