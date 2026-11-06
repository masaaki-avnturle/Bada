#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXVI · BWV 721 nel sonno — tablet117 fra i principali (tablet165 の、tablet117 の静かに流れる曲をメインの仲間に入れて作り換え)
  CLXV と同じ作り (トラック 18 と 8 が表、III で 06:42 + BWV 721、tablet117 は高域を落としてヘ長調の段だけを繰り返す) だが、tablet117 を裏 (0.2) からメインの仲間 (0.42) に上げ、和音も tablet117 の採譜に従う (他の表が鳴っていないところ)。IV では tablet117 が主役 (0.5) でトラック 18 (0.4) が並ぶ
  使い方: python compose_tablet166.py <bank150.json> <wav のフォルダ (20261107_180000.wav, 20261107_080000.wav, 20261106_064228_clean.wav, 20261003_117000.wav = 高域を落としたもの)> [score_tablet166.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet166.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R18, R08, R117 = '20261106_064228', '20261107_180000', '20261107_080000', '20261003_117000'
PSRC = R42
BPM = 54
S1, S2, S3, S4, TOTAL = 0, 36, 82, 136, 174
NAMES = {R42: '11/06 06:42', R18: 'トラック 18', R08: 'トラック 8', R117: 'tablet117'}
FILE = {R42: R42 + '_clean.wav', R18: R18 + '.wav', R08: R08 + '.wav', R117: R117 + '.wav'}
DUR = {R42: 226.7, R18: 149.1, R08: 249.2, R117: 778.6}
SPB = 60.0 / BPM
PLAYS = [(R117, 38 * k, (0.5 if k == 4 else 0.42), 0, 152.0, 168.0, True) for k in range(5)] + [   # メインの仲間: tablet117 のヘ長調の段 (高域を落として) を 5 回 (IV は主役)。和音も tablet117 に従う (他の表がないところ)
         (R18, 1, 0.55, 0, 0.0, None, True),                                                      # I: トラック 18 (33 小節)
         (R08, S2 + 1, 0.55, 5, 0.0, None, True),                                                 # II: トラック 8 を 4 度上げて (42 小節)
         (R42, S3 + 1, 0.58, 0, 0.0, None, True),                                                 # III: 06:42 (51 小節) + BWV 721
         (R18, S4 + 1, 0.4, 0, 0.0, None, False), (R08, S4 + 4, 0.18, 5, 100.0, 149.0, False)]    # IV: トラック 18 が tablet117 に並び、トラック 8 の続きが遠くで
def play_len(rid, dur): return DUR[rid] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
LOOP = ['Dm', 'Bb', 'F', 'C']
CANDS = ['F', 'Fmaj7', 'Dm', 'Dm7', 'Bb', 'Bbmaj7', 'C', 'C7', 'Gm', 'Gm7', 'Am', 'Am7', 'A7', 'F/A', 'Bb/D', 'C/E', 'Dm/F']
ERB = [(d, m) for d, m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erbarm_melody.json')))['notes']]
def cantus(oct_=0, k=2): return [(d * k, m + 5 + oct_) for d, m in ERB]                            # イ短調 → ニ短調 (4 度上)、2 倍に伸ばして (26 小節)
CF_BARS = int(math.ceil(2 * sum(d for d, _ in ERB) / 4.0))
def clip(mat, max_beats):
    out = []; t = 0.0
    for d, m in mat:
        if t >= max_beats: break
        out.append((min(d, max_beats - t), m)); t += d
    return out
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
                frac = (q - t0) * SPB * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: b = q // BPB; cur = LOOP[b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.3 if k < S2 else 0.42 if k < S3 else (0.6 if k < S3 + 36 else 0.5) if k < S4 else max(0.06, 0.4 - 0.012 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. トラック 18 — 眠りに入る (ニ短調, ♩=54)', 'トラック 18 の実音 (表) に tablet117 (高域を落として、ヘ長調の段) がメインの仲間として並ぶ。BWV 721 の脈 (8 分音符の和音、バス) が途中から pp で')
    P.section(S2, 'II. トラック 8 (4 度上げて) — 定旋律が遠くで', 'トラック 8 を 4 度上げてヘ長調 / ニ短調に (表)。脈がバスとテノールに、「Erbarm dich mein」の定旋律 (2 倍) がアルトで一度')
    put('A', S2 + 6, cantus(0), '定旋律「Erbarm dich mein」(ニ短調、2 倍、アルト)')
    P.section(S3, 'III. 06:42 — BWV 721 (ヘ長調 / ニ短調)', '06:42 の実音 (表)、その和音に合わせて BWV 721 の書法: アルト・テノール・バスが 8 分音符で和音を打ち続け (3 声)、ソプラノが定旋律を 2 倍に伸ばして 2 度 (2 度目は 1 オクターヴ下)')
    put('S', S3 + 2, cantus(0), '定旋律 (ソプラノ)'); put('S', S3 + 2 + CF_BARS, cantus(-12), None)
    P.section(S4, 'IV. tablet117 が主役 — 消える脈', 'tablet117 (ヘ長調の段、主役) にトラック 18 が並び、トラック 8 の続きが遠くで。脈が少しずつ消え、定旋律の頭だけがアルトで、tablet117 だけが残る')
    put('A', S4 + 4, cantus(0)[:8], '定旋律の頭'); put('A', S4 + 16, cantus(-12)[:8], None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    # 脈: 8 分音符の和音 (BWV 721) — I の 16 小節目から、バス; II からテノールも; III はアルトも (ソプラノの定旋律が空いているときはアルトは休む); IV で消える (小節ごとに抜く)
    first = True
    for b in range(S1 + 16, TOTAL - 4):
        sec = sec_of(b)
        if sec == 4 and (b - S4) % 3 == 2: continue
        if sec == 4 and b > S4 + 24: continue
        freeT = sec >= 2 and all((b * BPB + j) in P.rest['T'] for j in range(BPB)); freeA = sec == 3 and all((b * BPB + j) in P.rest['A'] for j in range(BPB))
        for k in range(BPB * 2):
            q = b * BPB + k // 2; h = P.harm[q]
            P.rest['B'].discard(q); P.place('B', b, [(0.5, tones_of(h, 40, 52)[0])], 0, ('打ち続ける和音 (BWV 721 の脈、pp)' if first else None), beat=k * 0.5); first = False
            if freeT: tt = tones_of(h, 52, 64); P.place('T', b, [(0.5, tt[len(tt) // 2])], 0, None, beat=k * 0.5); P.rest['T'].discard(q)
            if freeA: aa = tones_of(h, 60, 72); P.place('A', b, [(0.5, aa[-1])], 0, None, beat=k * 0.5); P.rest['A'].discard(q)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 0 else 0.02, fout=10.0, semis=sm, rid=rid + '.wav', tag='%s — %s%s' % (NAMES[rid], ('表、高域を落として' if rid == R117 else '表') if lead else '裏、遠くで', '、4 度上げて' if sm else ''))
    first = True
    for b in range(S2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.1 * P.dyn.get(b, 0.5) / 0.5, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R117, R18, R08, R42], 'piano_decay': 2.8, 'reverb': [6.0, 2.5, 0.45],
        'title': 'Requiem BADA — CLXVI · BWV 721 nel sonno — tablet117 fra i principali',
        'subtitle': 'tablet165 の作り換え: tablet117 (高音の電子音を取り除いた静かな曲) をメインの仲間に。トラック 18 と 8 (4 度上げて) と並び、バッハの BWV 721 (打ち続ける和音と「Erbarm dich mein」の定旋律) を 11/06 06:42 に合わせて: トラック 18 → トラック 8 → 06:42 + BWV 721 → トラック 18 (消える)。ニ短調 / ヘ長調、♩=54',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['定旋律 = コラール「Erbarm dich mein, o Herre Gott」(music21 の bach/bwv305 のソプラノ、イ短調) を 4 度上げてニ短調に、2 倍に伸ばして。BWV 721 からは書法 (8 分音符で打ち続ける和音) を借りる。和音は表の録音 (III は 06:42) の採譜を優先しつつ定旋律の音を含む和音を半小節ごとに',
                   'tablet117 は 1.8 kHz より上を落とし、ヘ長調の段 (152〜320 秒) だけを 0.42 (IV は 0.5、主役) で 5 回、和音も tablet117 の採譜に従う。トラック 18 はそのまま、トラック 8 は 4 度上げて。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘なし、高い共鳴なし、声なし。']}

if __name__ == '__main__':
    print('cantus bars', CF_BARS, 'range', min(m for _, m in cantus()), max(m for _, m in cantus()))
    compose.main(OUT, seed=166, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
