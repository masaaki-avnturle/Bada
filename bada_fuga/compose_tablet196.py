#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXCVI · La voce giovane sul 89 (2026/11/08 13:51 の声を 18 歳の女性の声らしくして tablet89 に重ね合わせ、元の楽器を演奏させて — アルペジオや元の曲に無い楽器は付け加えない)
  声: 11/08 13:51 の録音 (3 分 54 秒、男声 f0 中央値 107 Hz、ヘ長調 / ニ短調) を feminize_voice.py (WORLD ボコーダー) で 13 半音上げ、フォルマントを 1.15 倍にして若い女性の声に (変換後の f0 中央値 228 Hz)、rms −22 dB に揃える。調は tablet89 (ニ短調) と同じなのでそのまま
  テープ: tablet89 (LXXXIX) を全曲 (0.45) と後半 (0.4)、変換した声を 2 回 (0.55、表)
  元の楽器 = tablet89 の中にある楽器 (実音のピアノ) だけ: tablet89 の旋律と声の旋律 (最上声の採譜から各 8 小節) を実音のピアノ (06:42 の 1 音のサンプラー) で、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フックは付け加えない
  和音は声の採譜から (ないところは tablet89)
  使い方: python compose_tablet196.py <bank196.json (bank195 + 声の採譜)> <wav のフォルダ (20261107_089000.wav, 20261108_135116.wav = 変換した声)> [score_tablet196.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet196.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R89, RV = '20261106_064228', '20261107_089000', '20261108_135116'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 100, 160, 176
NAMES = {R89: 'tablet89', RV: '11/08 13:51 の声 (若い女性の声に)'}
FILE = {R89: R89 + '.wav', RV: RV + '.wav'}
DUR = {R89: 391.0, RV: 234.2}
PLAYS = [(R89, 0, 0.45, 0, 0.0, None, True), (R89, S3, 0.4, 0, 90.0, 300.0, True),                 # tablet89 全曲と後半
         (RV, 2, 0.55, 0, 0.0, None, True),                                                       # I〜II: 声 (58 小節、表)
         (RV, S3 + 2, 0.55, 0, 0.0, None, True)]                                                  # III〜IV: 声 (2 回目)
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
T89 = tune_from(R89, 0); TV = tune_from(RV, 0)                                                      # tablet89 の旋律と声の旋律 (ヘ長調 / ニ短調)
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
    P.section(S1, 'I. 声 (ヘ長調 / ニ短調, ♩=60)', 'tablet89 の始まり (レクイエム) に若い女性の声 (13:51 を変換)。元の楽器: 声の旋律を実音のピアノで (アルト → テノール)、tablet89 の旋律がバスで、低いペダル')
    put('A', 10, TV, '声の旋律 (実音のピアノ)'); put('T', 26, tr(TV, -12), None); put('B', 40, tr(T89, -24), 'tablet89 の旋律')
    P.section(S2, 'II. 声の終わりとフーガ', 'tablet89 のフーガ、声の終わり。tablet89 の旋律 (ソプラノ → アルト)、声の旋律の頭を 2 倍にバスで')
    put('S', S2 + 2, T89, 'tablet89 の旋律 (実音のピアノ)'); put('A', S2 + 16, T89, None); put('B', S2 + 28, aug(tr(TV[:6], -24)), None)
    P.section(S3, 'III. 声 (2 回目) と tablet89 の後半', 'tablet89 の後半 (90 秒から) に声をもう一度。声の旋律 (ソプラノ) と tablet89 の旋律 (テノール) を同時に (2 小節遅れ)、もう一度アルトとバスで')
    put('S', S3 + 6, TV, '2 つの旋律を同時に'); put('T', S3 + 8, tr(T89, -12), None); put('A', S3 + 26, TV, None); put('B', S3 + 28, tr(T89, -24), None); put('S', S3 + 44, T89, None)
    P.section(S4, 'IV. 消える', 'tablet89 の終わりと声の終わり。旋律の頭を 2 倍に伸ばして、ペダルだけが残って消える')
    put('T', S4 + 2, aug(tr(TV[:6], -12)), '頭を 2 倍に'); put('B', S4 + 8, aug(tr(T89[:6], -24)), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], ('、変換して (13 半音上げ、フォルマント 1.15 倍)' if rid == RV else ('、全曲そのまま' if dur is None else '、後半 (90 秒から)'))))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R89], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXCVI · La voce giovane sul 89',
        'subtitle': '11/08 13:51 の声を 18 歳の女性の声らしく変換して (WORLD ボコーダーで 13 半音上げ、フォルマント 1.15 倍、f0 中央値 107 → 228 Hz) tablet89 に重ね合わせ、元の楽器 (tablet89 と声の旋律を実音のピアノで、低いペダル) を演奏させて。アルペジオや元の曲に無い楽器は付け加えない。ヘ長調 / ニ短調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['声 = 11/08 13:51 (3 分 54 秒、男声) を feminize_voice.py で若い女性の声に (13 半音上げ、フォルマント 1.15 倍、音高をヘ長調に 0.6 で寄せる)、rms −22 dB に揃えて 2 回 (0.55)。tablet89 (LXXXIX) は全曲 0.45 と後半 0.4。和音は声の採譜 (build_sampler) を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '楽器 = tablet89 と声の最上声の音から作った旋律 (各 8 小節) を 06:42 の実音のピアノの 1 音のサンプラーで、2 小節ごとの低いペダル。鐘なし、合成の声なし、他の楽器なし。']}

if __name__ == '__main__':
    print('TV', ' '.join('%s:%g' % (name_of(m), d) for d, m in TV[:12]))
    compose.main(OUT, seed=196, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
