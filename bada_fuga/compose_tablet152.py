#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLII · Due tracce nell'aria del 06:39 (トラック 8 と 18 を合成して、2026/11/06 06:39 を醸す曲に)
  材料: トラック 8 (ハ長調〜イ短調、4 分 9 秒) とトラック 18 (ニ短調、2 分 29 秒) — 実音のまま重ね合わせ (表と裏を入れ替えて)、それぞれの最上声の音から作った旋律を二重フーガのように 4 声で追いかける
  醸すもの: 11/06 06:39 (ト長調〜ニ・ドリア: Gmaj7・D7・Dm7・Fmaj7) — 始めと終わりに実音をそのまま、中では遠くで、和音はその採譜の流れ (06:39 が鳴っていない所も 06:39 の和音の輪 Gmaj7 → D7 → Dm7 → Fmaj7 で)
  音源: 4 声は 11/06 06:42 の実音のピアノの 1 音 (サンプラー)、低いペダルと高い共鳴は合成のピアノ。鐘なし、声なし
  使い方: python compose_tablet152.py <bank150.json> <wav のフォルダ> [score_tablet152.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet152.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R18, R08 = '20261106_063938', '20261106_064228', '20261107_180000', '20261107_080000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 102, 140, 170
NAMES = {R39: '11/06 06:39', R18: 'トラック 18', R08: 'トラック 8'}
FILE = {R39: R39 + '_clean.wav', R18: R18 + '.wav', R08: R08 + '.wav'}
PLAYS = [(R39, 1, 0.6, 0, 0.0, None, True),
         (R08, S2 + 1, 0.5, 0, 0.0, None, True), (R18, S2 + 1, 0.3, 0, 0.0, None, False),
         (R18, S3 + 1, 0.5, 0, 0.0, None, True), (R08, S3 + 1, 0.3, 0, 120.0, 120.0, False), (R39, S3 + 18, 0.3, 0, 80.0, 80.0, False),
         (R39, S4 + 1, 0.55, 0, 0.0, 115.0, True), (R08, S4 + 4, 0.2, 0, 200.0, 49.0, False), (R18, S4 + 10, 0.2, 0, 119.0, 30.0, False)]
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
LOOP39 = ['Gmaj7', 'D7', 'Dm7', 'Fmaj7']
GMAJ = [0, 2, 4, 5, 7, 9, 10]                                                                      # ニ・ドリア / ハ長調 (ド・レ・ミ・ファ・ソ・ラ・シ♭)
def tune_from(rid, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), ends=((67, 72), (69, 64), (67, 72), (62, 62)), n=4):
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
T8 = tune_from(R08); T18 = tune_from(R18, rhythm=(0.5, 0.5, 1, 1, 1, 2), ends=((69, 74), (65, 62), (69, 74), (62, 62)))
def p8(k): return T8[6 * k: 6 * k + 6]
def p18(k): return T18[6 * k: 6 * k + 6]
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
CANDS = ['G', 'Gmaj7', 'D', 'D7', 'Dm', 'Dm7', 'F', 'Fmaj7', 'C', 'Cmaj7', 'Am', 'Am7', 'Em', 'Em7', 'Bb', 'Gm', 'G/B', 'C/E', 'Dm/F', 'Am/C']
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
        if cur is None: cur = LOOP39[(q // (2 * BPB)) % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5 if k < S2 else 0.6 if k < S3 else 0.65 if k < S4 else max(0.2, 0.55 - 0.012 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None, tr=0):
        mat = [(d, m + tr) for d, m in mat]; nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. 06:39 の空気 — 2 つの主題の提示 (ト長調〜ニ・ドリア, ♩=60)', '11/06 06:39 の実音 (表)。トラック 8 の旋律 (主題 I) をソプラノ → アルト、トラック 18 の旋律 (主題 II) をテノール → バスが提示する (実音のピアノの 1 音)')
    put('S', S1 + 6, p8(0), '主題 I (トラック 8 の旋律)'); put('A', S1 + 10, p8(0), None, -12); put('T', S1 + 16, p18(0), '主題 II (トラック 18 の旋律)', -12); put('B', S1 + 20, p18(0), None, -24)
    put('S', S1 + 26, p8(1), None); put('T', S1 + 30, p18(1), None, -12)
    P.section(S2, 'II. トラック 8 が表、18 が裏 — 二重フーガ (ハ長調〜イ短調)', 'トラック 8 (全部、表) とトラック 18 (裏) を重ね合わせて。主題 I と II が 2 小節ごとに重なり合う (S・A に I、T・B に II)、06:39 の和音の輪が下に')
    for k in range(6):
        b = S2 + 3 + 8 * k; put('S', b, p8(k % 4), '二重フーガ — 主題 I' if k == 0 else None); put('T', b + 2, p18(k % 4), '主題 II' if k == 0 else None, -12)
        put('A', b + 4, p8((k + 1) % 4), None, -12); put('B', b + 6, p18((k + 1) % 4), None, -24)
    put('S', S2 + 52, aug(p8(0)), '主題 I の拡大'); put('T', S2 + 52, aug(p18(0)), '主題 II の拡大', -12)
    P.section(S3, 'III. トラック 18 が表、8 が裏 — ストレッタ (ニ短調)', 'トラック 18 (全部、表) とトラック 8 の中 (裏)、18 小節目から 06:39 の中が遠くで戻る。主題 I と II のストレッタ (1 小節ずつ)、ソプラノが主題 II を 1 オクターヴ上で')
    for k in range(4):
        b = S3 + 2 + 6 * k; put('A', b, p8(k % 4), 'ストレッタ' if k == 0 else None, -12); put('T', b + 1, p18(k % 4), None, -12); put('S', b + 2, p18(k % 4), None, 12); put('B', b + 3, p8(k % 4), None, -24)
    put('S', S3 + 28, aug(p18(0)), '主題 II の拡大 (高く)', 12); put('A', S3 + 28, aug(p8(0)), None, -12)
    P.section(S4, 'IV. 06:39 に戻る — 消えていく', '06:39 の実音 (表、始めから)、トラック 8・18 の終わりが遠くで。主題 I の頭がアルトに 4 小節ごと、主題 II の頭がテノールに、だんだん小さく')
    for k in range(6): put('A', S4 + 3 + 4 * k, p8(0)[:3], '主題 I の頭' if k == 0 else None, -12); put('T', S4 + 5 + 4 * k, p18(0)[:4], None, -24)
    harm_fit(P, S1 + 4, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 1 else 0.02, fout=7.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s%s)' % (NAMES[rid], '表' if lead else '裏、小さく', '、抜粋' if dur else ''))
    first = True
    for b in range(S1 + 4, TOTAL - 4, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.5, r, 0.1 * P.dyn.get(b, 0.5) / 0.5, '低いペダルの音 (2 小節ごと、pp)' if first else None); first = False
    first = True
    for b0, mat in ((S2 + 52, aug(p8(0))), (S3 + 28, aug(p18(0)))):
        t = b0 * BPB + 2
        for d, m in mat: add('H', t, d, m + 12, 0.07, '高い共鳴 (拡大の反響、pp)' if first else None); first = False; t += d
    for k, b in enumerate(range(S4 + 4, TOTAL - 4, 4)): add('H', b * BPB + 1, 5.0, 83 if k % 2 == 0 else 79, 0.06 * max(0.3, 1 - 0.12 * k), None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R08, R18], 'piano_decay': 2.6, 'reverb': [7.0, 3.0, 0.5],
        'title': 'Requiem BADA — CLII · Due tracce nell\'aria del 06:39',
        'subtitle': 'トラック 8 と 18 を合成して、11/06 06:39 を醸す曲に: 06:39 の空気で 2 つの主題 (トラック 8・18 の旋律) を提示 → トラック 8 が表で二重フーガ → トラック 18 が表でストレッタ (06:39 が遠くで戻る) → 06:39 に戻って消える。ト長調〜ニ・ドリア / ハ長調 / ニ短調、♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['主題 I = トラック 8 の最上声の音、主題 II = トラック 18 の最上声の音 (ニ・ドリア / ハ長調の音階に寄せて、讃美歌のリズム × 4 句)。和音は表の録音の採譜を優先、録音のない所は 06:39 の和音の輪 (Gmaj7 → D7 → Dm7 → Fmaj7)',
                   '3 つの音源は実音、そのまま。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘なし、声なし。']}

if __name__ == '__main__':
    print('T8', ' '.join('%s:%g' % (name_of(m), d) for d, m in T8[:6]), '| T18', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18[:6]))
    compose.main(OUT, seed=152, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
