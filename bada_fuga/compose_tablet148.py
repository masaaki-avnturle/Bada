#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLVIII · Mescolanza (tablet117・2026/11/06 の 2 曲・トラック 18 を混ぜて、曲を作る)
  4 つの音源を段落ごとに表と裏を入れ替えながら混ぜる (すべて実音、そのまま; 11/06 は喘ぎの区間だけ下げて):
    I.   06:39 が表 (ト長調〜ニ・ドリア)、tablet117 が裏
    II.  トラック 18 (ニ短調: Dm・Gm・F・A・B♭、2 分 29 秒) が表、06:42 が裏
    III. 06:42 が表 (ヘ長調)、トラック 18 の終わり (Dm) が遠くで戻る、tablet117 が裏
    IV.  tablet117 の眠りの段階が表、06:39 の終わりとトラック 18 の始まりが遠くで — 消えていく
  つなぐもの: トラック 18 の最上声の音から作った旋律 (讃美歌のリズム、ニ短調) を 11/06 06:42 の実音のピアノの 1 音 (サンプラー) で、段落の始めにソプラノが、アルトとテノールが答える。低いペダルと高い共鳴は合成のピアノ。鐘なし、声なし
  使い方: python compose_tablet148.py <bank148.json (3 つの bank を合わせたもの)> <wav のフォルダ> [score_tablet148.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet148.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R18, R117 = '20261106_063938', '20261106_064228', '20261107_180000', '20261003_117000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 78, 135, 166
NAMES = {R39: '11/06 06:39', R42: '11/06 06:42', R18: 'トラック 18', R117: 'tablet117'}
FILE = {R39: R39 + '_clean.wav', R42: R42 + '_clean.wav', R18: R18 + '.wav', R117: R117 + '.wav'}
# (録音, 小節, 大きさ, 移調, 抜粋の始まり (秒), 長さ (秒; None = 全部), 表か)
PLAYS = [(R39, 1, 0.62, 0, 0.0, None, True), (R117, 0, 0.22, 0, 0.0, 160.0, False),
         (R18, S2 + 1, 0.62, 0, 0.0, None, True), (R42, S2 + 1, 0.28, 0, 0.0, 150.0, False),
         (R42, S3 + 1, 0.6, 0, 0.0, None, True), (R18, S3 + 32, 0.3, 0, 119.0, 30.0, False), (R117, S3 + 1, 0.2, 0, 160.0, 227.0, False),
         (R117, S4 + 1, 0.55, 0, 564.0, 120.0, True), (R39, S4 + 1, 0.26, 0, 120.0, 40.0, False), (R18, S4 + 12, 0.26, 0, 0.0, 40.0, False)]
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
GMAJ = [0, 2, 5, 7, 9, 10]                                                                        # ニ短調の五音 (レ・ファ・ソ・ラ・シ♭) + ド
def tune_from(rid, lo=62, hi=77, rhythm=(1, 1, 1, 1, 2, 2), ends=((69, 74), (72, 65), (69, 74), (62, 62)), n=4):
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1]
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph % len(ends)], key=lambda x: abs(x - out[i][1])))
    return out
T18 = tune_from(R18)
def ph(k): return T18[6 * k: 6 * k + 6]
CANDS = ['Dm', 'F', 'C', 'Bb', 'Gm', 'Am', 'A', 'A7', 'Dm/F', 'Bb/D', 'C/E', 'Gm7', 'Dm/A', 'Fmaj7', 'Bbmaj7', 'G', 'Gmaj7', 'D7', 'Dm7', 'C7']
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
        for rid, bar, g, sm, off, dur, lead in PLAYS:
            if not lead: continue
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: cur = 'Dm'
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.55 if k < S4 else max(0.15, 0.55 - 0.015 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None, tr=0):
        mat = [(d, m + tr) for d, m in mat]; nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. 06:39 が表、tablet117 が裏 (♩=60)', '11/06 06:39 の実音 (表)、tablet117 (眠りへの曲) が裏に小さく。トラック 18 の音から作った旋律の第 1・2 句をソプラノが、アルトが答える (実音のピアノの 1 音)')
    put('S', S1 + 6, ph(0), 'トラック 18 の旋律 第 1 句'); put('A', S1 + 12, ph(1), None, -12); put('S', S1 + 22, ph(0) + ph(1), '第 1・2 句'); put('T', S1 + 32, ph(2), None, -24)
    P.section(S2, 'II. トラック 18 が表、06:42 が裏 (ニ短調)', 'トラック 18 (そのまま、2 分 29 秒) が表、06:42 が裏に小さく。旋律の第 3・4 句をアルトとテノールが、ソプラノが全句を 2 倍に伸ばして')
    put('A', S2 + 4, ph(2), '第 3 句 (アルト)'); put('T', S2 + 10, ph(3), None, -12); put('S', S2 + 16, [(d * 2, m) for d, m in T18], '全句 (2 倍に伸ばして)')
    P.section(S3, 'III. 06:42 が表、トラック 18 の終わりが遠くで (ヘ長調)', '06:42 の実音 (表)、tablet117 が裏に。32 小節目からトラック 18 の終わり (Dm) が遠くで戻る。旋律の第 1 句がテノールに低く、全句がソプラノに')
    put('T', S3 + 6, ph(0), '第 1 句 (テノール、低く)', -24); put('S', S3 + 14, T18, '全句'); put('A', S3 + 34, ph(3), None, -12); put('S', S3 + 44, [(d * 2, m) for d, m in ph(0) + ph(1)], '第 1・2 句 (2 倍に)')
    P.section(S4, 'IV. tablet117 の眠り、消えていく', 'tablet117 の眠りの段階 (564 秒から) が表、06:39 の終わりとトラック 18 の始まりが遠くで。旋律の頭だけがアルトに 4 小節ごと、高い共鳴が消える')
    for k in range(5): put('A', S4 + 4 + 4 * k, ph(0)[:3], '旋律の頭だけ' if k == 0 else None, -12)
    harm_fit(P, S1 + 4, TOTAL - 4, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 1 else 0.02, fout=6.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s%s)' % (NAMES[rid], '表' if lead else '裏、小さく', '、抜粋' if dur else ''))
    first = True
    for b in range(S1 + 4, TOTAL - 4, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.5, r, 0.11 * P.dyn.get(b, 0.55) / 0.55, '低いペダルの音 (2 小節ごと、pp)' if first else None); first = False
    first = True
    for b0 in (S1 + 22, S2 + 16, S3 + 14):
        t = b0 * BPB + 2
        for d, m in (T18 if b0 != S2 + 16 else [(d * 2, m) for d, m in T18]): add('H', t, d, m + 12, 0.07, '高い共鳴 (旋律の反響、pp)' if first else None); first = False; t += d
    for k, b in enumerate(range(S4 + 2, TOTAL - 4, 3)): add('H', b * BPB + 1, 4.0, 86 if k % 2 == 0 else 81, 0.06 * max(0.3, 1 - 0.1 * k), None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R117, R18, R42], 'piano_decay': 2.6, 'reverb': [6.5, 2.8, 0.45],
        'title': 'Requiem BADA — CXLVIII · Mescolanza',
        'subtitle': 'tablet117・2026/11/06 06:39・06:42・トラック 18 を混ぜて: 06:39 が表 (tablet117 が裏) → トラック 18 が表 (06:42 が裏) → 06:42 が表 (トラック 18 の終わりが遠くで) → tablet117 の眠りが表で消えていく。つなぐのはトラック 18 の音から作った旋律 (実音のピアノの 1 音)。ニ短調 / ヘ長調、♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['旋律 = トラック 18 の最上声の音 (ニ短調の五音に寄せて) を讃美歌のリズム (♩ ♩ ♩ ♩ 𝅗𝅥 𝅗𝅥 × 4 句) に。和音は表の録音の採譜を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '4 つの音源はすべて実音、そのまま (11/06 は喘ぎの区間だけ下げて)。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘なし、声なし。']}

if __name__ == '__main__':
    print('tune', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18[:12]))
    compose.main(OUT, seed=148, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
