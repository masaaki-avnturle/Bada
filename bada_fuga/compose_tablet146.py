#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLVI · Addio sul sonno (2026/11/06 の 2 曲をメインにして、バックで tablet117 を睡眠導入剤に混ぜて、ショパンとベートーヴェンの別れの曲を雰囲気に合わせて)
  メイン (表): 11/06 06:39 (160 秒、Gmaj7・D7・Dm7 — ト長調〜ニ・ドリア) → 06:42 (227 秒、F・Fmaj7・E・C — ヘ長調) → 06:39 (2 度目) → 06:42 の終わり (76 秒)。喘ぎの区間だけ下げて、そのまま
  バック: tablet117 (CXVII · Ninna nanna 10/03 — 眠りへの曲) を小さく全曲に (睡眠導入剤: 0.22 → 眠りの段階で 0.3)
  別れの曲: ショパン Op. 10-3 の旋律の頭 (記憶からの採譜、2 倍に伸ばして、録音の調に: ト長調 +3 / ヘ長調 +1) をソプラノが静かに、ベートーヴェン「告別」の Lebewohl (ソ・ファ・ミ、角笛の別れ) をアルトとテノールが答えるように — 眠りに合う pp、間を多く
  音源: 4 声は 11/06 06:42 の実音のピアノの 1 音 (bank1106 のサンプラー)、高い共鳴と低いペダルは合成のピアノ。鐘なし、声なし、脈なし
  使い方: python compose_tablet146.py <bank1106.json> <wav のフォルダ (06:39・06:42 の _clean と 20261003_117000)> [score_tablet146.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet146.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
import soundfile as sf
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R117 = '20261106_063938', '20261106_064228', '20261003_117000'
D117 = sf.SoundFile(os.path.join(WDIR, R117 + '.wav')).frames / 44100.0
PSRC = R42
BPM = 60
A1, B1, A2, B2, TOTAL = 0, 42, 100, 142, 164
def key_of(bar): return 'G' if (bar < B1 or A2 <= bar < B2) else 'F'
TRK = {'G': 3, 'F': 1}
CH_A = [(0.5, 68), (0.75, 71), (0.25, 69), (0.5, 68), (0.5, 66), (1.0, 68), (0.5, 66), (0.5, 64), (0.5, 63), (1.5, 64)]                      # ショパン Op. 10-3 の頭 (ホ長調、記憶からの採譜)
CH_B = [(0.5, 68), (0.5, 69), (0.5, 71), (0.5, 73), (0.5, 75), (1.0, 76), (0.5, 75), (0.5, 73), (0.5, 71), (0.5, 69), (0.5, 68), (0.5, 66), (1.0, 64), (0.5, 63), (1.5, 64)]
def chopin(key, part, k=2, oct_=0): return [(d * k, m + TRK[key] + oct_) for d, m in part]
def leb(key, oct_=0, k=2):                                                                         # Lebewohl ソ・ファ・ミ (角笛の別れ): ト長調 レ・ド・シ、ヘ長調 ド・シ♭・ラ
    s = {'G': 74, 'F': 72}[key]; return [(1 * k, s + oct_), (1 * k, s - 2 + oct_), (2 * k, s - 3 + oct_)]
CANDS = {'G': ['G', 'Gmaj7', 'D', 'D7', 'Em', 'Em7', 'C', 'Cmaj7', 'Am', 'Am7', 'Bm', 'Dm7', 'G/B', 'C/E', 'D/F#'],
         'F': ['F', 'Fmaj7', 'C', 'Cmaj7', 'Dm', 'Dm7', 'Bb', 'Gm', 'Gm7', 'Am', 'E', 'C/E', 'F/A', 'Bb/D', 'Csus4']}
PLAYS = [(R39, 1, 0.7, 0, 0.0, None), (R42, B1 + 1, 0.62, 0, 0.0, None), (R39, A2 + 1, 0.66, 0, 0.0, None), (R42, B2 + 1, 0.58, 0, 150.0, 76.0)]
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
        if cur is None: cur = key_of(q // BPB)
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5 if k < B1 else 0.55 if k < A2 else 0.5 if k < B2 else max(0.15, 0.5 - 0.02 * (k - B2))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(A1, 'I. 06:39 — 別れの歌、静かに (ト長調, ♩=60)', '11/06 06:39 の実音 (表)。バックに tablet117 (眠りへの曲) が小さく。ソプラノがショパンの「別れの曲」の頭 (2 倍に伸ばして、ト長調) を 2 度、アルトとテノールが Lebewohl (レ・ド・シ、角笛の別れ) で答える — 実音のピアノの 1 音、間を多く')
    put('S', A1 + 6, chopin('G', CH_A), 'ショパン「別れの曲」の頭 (ト長調、2 倍に)'); put('A', A1 + 14, leb('G', -12), 'Lebewohl (レ・ド・シ)'); put('T', A1 + 18, leb('G', -24))
    put('S', A1 + 24, chopin('G', CH_A + CH_B), '別れの曲 (上る句まで)'); put('A', A1 + 38, leb('G', -12))
    P.section(B1, 'II. 06:42 — ヘ長調で (ヘ長調)', '06:42 の実音 (表)。ショパンの頭をヘ長調で、Lebewohl (ド・シ♭・ラ) がホルンのように低く 2 度、上る句をソプラノが 1 オクターヴ上で pp')
    put('T', B1 + 4, leb('F', -12), 'Lebewohl (ド・シ♭・ラ、低く)'); put('S', B1 + 10, chopin('F', CH_A), 'ショパンの頭 (ヘ長調)'); put('A', B1 + 20, leb('F', 0)); put('T', B1 + 24, leb('F', -24))
    put('S', B1 + 30, chopin('F', CH_B, 2, 12), '上る句 (1 オクターヴ上、pp)'); put('A', B1 + 44, leb('F', -12)); put('S', B1 + 50, chopin('F', CH_A))
    P.section(A2, 'III. 06:39 — 2 度目 (ト長調)', '06:39 の実音 (2 度目)。tablet117 は眠りの段階へ (少し大きく)。別れの曲の頭がアルトに (1 オクターヴ下)、Lebewohl がソプラノに高く、テノールが上る句をゆっくり (4 倍に)')
    put('A', A2 + 4, chopin('G', CH_A, 2, -12), '別れの曲の頭 (アルト)'); put('S', A2 + 14, leb('G', 12), 'Lebewohl (高く)'); put('T', A2 + 18, chopin('G', CH_B, 4, -12), '上る句 (テノール、4 倍に)')
    put('S', A2 + 34, chopin('G', CH_A)); put('A', A2 + 40, leb('G', -12))
    P.section(B2, 'IV. 06:42 の終わり — 眠りへ (ヘ長調)', '06:42 の実音の終わり。Lebewohl だけが遠くで 3 度 (ソ・ファ・ミ、だんだん低く)、高い共鳴が消える')
    put('A', B2 + 3, leb('F', 0), 'Lebewohl — 遠くで'); put('T', B2 + 9, leb('F', -12)); put('B', B2 + 15, leb('F', -24))
    for b0, b1, key in ((A1, B1, 'G'), (B1, A2, 'F'), (A2, B2, 'G'), (B2, TOTAL - 2, 'F')): harm_fit(P, b0 + 1, b1, [e for e in E if b0 * BPB <= e[0] < b1 * BPB], CANDS[key])
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=off, fin=0.5 if bar > 1 else 0.02, fout=6.0, semis=sm, rid=rid + '.wav', tag='11/06 %s — 実音 (メイン%s)' % ('06:39' if rid == R39 else '06:42', '、終わり' if dur else ''))
    add('REC', 0, min(D117, (TOTAL - 1) * BPB), 0, 0.22, None, src=os.path.join(WDIR, R117 + '.wav'), off=0.0, fin=4.0, fout=8.0, semis=0, rid=R117 + '.wav', tag='tablet117 (眠りへの曲) — バックに小さく (睡眠導入剤)')
    for e in extras:                                                                                # tablet117 は III から少し大きく (眠りの段階)
        pass
    first = True
    for b in range(A1 + 4, TOTAL - 4, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.5, r, 0.12 * P.dyn.get(b, 0.5) / 0.5, '低いペダルの音 (2 小節ごと、pp)' if first else None); first = False
    first = True
    for b0, key in ((A1 + 6, 'G'), (B1 + 10, 'F'), (A2 + 34, 'G')):
        t = b0 * BPB + 3
        for d, m in chopin(key, CH_A): add('H', t, d, m + 12, 0.07, '高い共鳴 (別れの曲の反響、pp)' if first else None); first = False; t += d
    for k, b in enumerate(range(B2 + 2, TOTAL - 4, 3)): add('H', b * BPB + 1, 4.0, 86 if k % 2 == 0 else 84, 0.06 * max(0.3, 1 - 0.1 * k), None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R42, R117], 'piano_decay': 2.6, 'reverb': [7.0, 3.0, 0.5],
        'title': 'Requiem BADA — CXLVI · Addio sul sonno',
        'subtitle': '11/06 06:39・06:42 の 2 曲をメインにして、バックで tablet117 (眠りへの曲) を睡眠導入剤に混ぜ、ショパンの「別れの曲」(Op. 10-3 の頭、記憶からの採譜) とベートーヴェンの「告別」(Lebewohl ソ・ファ・ミ) を雰囲気に合わせて: 06:39 (ト長調) → 06:42 (ヘ長調) → 06:39 → 06:42 の終わり (眠りへ)。♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['別れの曲 = ショパン Op. 10-3 の旋律の頭 (記憶からの採譜、細部は原曲と違いうる) を 2 倍に伸ばして録音の調 (ト長調 +3 / ヘ長調 +1) に。告別 = ベートーヴェン Op. 81a の Lebewohl (ソ・ファ・ミ) を各調で。旋律の引用はこの 2 つの動機だけ',
                   '4 声は 11/06 06:42 の実音のピアノの 1 音のサンプラー。tablet117 はバックに 0.22。和音は録音の採譜を優先しつつ主題の音を含む和音を半小節ごとに。鐘なし、声なし、脈なし (眠りのために)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=146, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
