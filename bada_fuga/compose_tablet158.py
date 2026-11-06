#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLVIII · Madre e due mattini (11/06 06:42・06:39、MOTHER・LOVELESS、トラック 18 を合成して)
  MOTHER と LOVELESS (LUNA SEA、1994) からは **音も旋律も使わない** — 採譜で読んだ調 (どちらもト長調〜ホ短調)、テンポ (MOTHER ♩≈68、LOVELESS ♩≈80 → 中間の ♩=72)、和音の流れ、ロック・バラードの様式 (アルペジオ、ドラム、ベース、サビの歪んだギターと弦) だけ
  実音 (表) は段落ごとに入れ替える: 序〜A メロ = 06:39 (ト長調、そのまま) → サビ = 06:42 がバック → 間奏 = 06:42 (全音上げてト長調 / ホ短調に) → 2 番 = トラック 18 (全音上げてホ短調に) → 大サビ = 06:39 がバック → 終わり = 06:42 の終わり
  旋律は 06:39 の音から (A メロ、サビの動機)、2 番はトラック 18 の音から。4 声は 06:42 の実音のピアノの 1 音のサンプラー
  使い方: python compose_tablet158.py <bank150.json> <wav のフォルダ> [score_tablet158.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet158.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R18 = '20261106_063938', '20261106_064228', '20261107_180000'
PSRC = R42
BPM = 72
INTRO, A1, SABI1, INTER, A2, SABI2, OUTRO, TOTAL = 0, 16, 48, 72, 96, 128, 160, 184
NAMES = {R39: '11/06 06:39', R42: '11/06 06:42', R18: 'トラック 18'}
FILE = {R39: R39 + '_clean.wav', R42: R42 + '_clean.wav', R18: R18 + '.wav'}
PLAYS = [(R39, 2, 0.55, 0, 0.0, None, True),                                                     # 序〜A メロ: 06:39 (160 秒 = 48 小節)
         (R42, SABI1, 0.22, 2, 0.0, 86.0, False),                                                  # サビ: 06:42 がバックに小さく
         (R42, INTER + 1, 0.5, 2, 0.0, 84.0, True),                                                # 間奏: 06:42 の始まり (表)
         (R18, A2 + 1, 0.5, 2, 0.0, None, True),                                                   # 2 番: トラック 18 (149 秒、全音上げて)
         (R39, SABI2 + 2, 0.22, 0, 50.0, 105.0, False),                                            # 大サビ: 06:39 がバックに小さく
         (R42, OUTRO + 1, 0.5, 2, 130.0, 88.0, True)]                                              # 終わり: 06:42 の終わり (表)
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
LOOP_A = ['Em7', 'Cmaj7', 'G', 'D7']; LOOP_S = ['G', 'D7', 'Em7', 'C']                            # A メロとサビの和音の輪 (LOVELESS の採譜の流れから: vi → IV → I → V / I → V → vi → IV)
LOOP_M = ['G', 'D/F#', 'Em7', 'Cmaj7']                                                            # 序・間奏・終わりの輪 (MOTHER の採譜の流れから: I → V/3 → vi → IV、バスが下る)
GMAJ = [4, 7, 9, 11, 2]                                                                           # ホ短調の五音 (ミ・ソ・ラ・シ・レ)
def tune_from(rid, sm=0, lo=64, hi=79, rhythm=(1, 1, 1, 1, 2, 2), ends=((71, 76), (67, 64), (71, 76), (64, 64)), n=4):
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + sm
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
T39 = tune_from(R39, 0); T18 = tune_from(R18, 2)
def ph(k): return T39[6 * k: 6 * k + 6]
def ph18(k): return T18[6 * k: 6 * k + 6]
HOOK = [(d, m if m >= 69 else m + 12) for d, (_, m) in zip((0.5, 0.5, 1, 0.5, 0.5, 1, 2), T39[6:13])]  # サビの動機 — 06:39 の第 2 句の 7 音をサビのリズムに、1 オクターブ上で (ホ短調の五音)
HOOK[-1] = (2, min((76, 79, 71), key=lambda x: abs(x - HOOK[-1][1])))
CANDS = ['Em', 'Em7', 'G', 'Gmaj7', 'C', 'Cmaj7', 'D', 'D7', 'Am', 'Am7', 'Bm', 'B7', 'Em/G', 'C/E', 'G/B', 'D/F#']
DRUM_G = 0.28
def dr(beat, kind, g, pan=0.0, label=None): add('DR', beat, 0.25, 60, g * DRUM_G, label, kind=kind, pan=pan)
OG = 0.34
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)
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





def sec_of(b): return 'intro' if b < A1 else 'a' if b < SABI1 else 'sabi' if b < INTER else 'inter' if b < A2 else 'a' if b < SABI2 else 'sabi' if b < OUTRO else 'outro'
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
            b = q // BPB; s = sec_of(b); base = {'intro': INTRO, 'a': A1 if b < INTER else A2, 'sabi': SABI1 if b < INTER else SABI2, 'inter': INTER, 'outro': OUTRO}[s]
            cur = (LOOP_S if s == 'sabi' else LOOP_A if s == 'a' else LOOP_M)[(b - base) % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5 if k < A1 else 0.65 if k < SABI1 else 0.9 if k < INTER else 0.55 if k < A2 else 0.7 if k < SABI2 else 0.95 if k < OUTRO else max(0.2, 0.6 - 0.02 * (k - OUTRO))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None, tr=0):
        mat = [(d, m + tr) for d, m in mat]; nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(INTRO, '序 — 06:39 の実音とアルペジオ (ト長調 / ホ短調, ♩=72)', '06:39 の実音 (表、そのままの調) にクリーンなアルペジオと弦のパッド。和音の輪 G → D/F# → Em7 → Cmaj7 (バスが下る)')
    P.section(A1, 'A メロ — 06:39 の実音にドラムとベース', '06:39 の音から作った旋律 (ホ短調の五音) を実音のピアノの 1 音で、06:39 の実音が続く。ドラム (柔らかく) とシンセ・ベース、アルペジオ。輪 Em7 → Cmaj7 → G → D7')
    for k in range(4): put('S', A1 + 2 + 8 * k, ph(k), 'A メロの旋律 (06:42 の音から)' if k == 0 else None)
    P.section(SABI1, 'サビ — 歪んだギターと弦、06:42 がバック', '和音の輪 G → D7 → Em7 → C、歪んだギターのパワーコード、クラッシュとライド、弦のトレモロ、サビの動機 (06:39 の第 2 句の 7 音) を Vn I・フルート・実音のピアノで。06:42 の実音 (全音上げて) がバックに小さく')
    for k in range(6): put('S', SABI1 + 2 + 4 * k, HOOK, 'サビの動機' if k == 0 else None); put('A', SABI1 + 4 + 4 * k, HOOK, None, -12)
    P.section(INTER, '間奏 — 06:42 の実音 (全音上げてト長調 / ホ短調に)', '06:42 の実音の始まり (表)、アルペジオとベースだけが下で、弦のパッド。輪 G → D/F# → Em7 → Cmaj7')
    put('T', INTER + 8, ph(0), None, -12)
    P.section(A2, '2 番 — トラック 18 の実音 (全音上げてホ短調に)', 'トラック 18 の実音 (表) に、その音から作った旋律をホルンと実音のピアノで。ドラムとベース')
    for k in range(4): put('S', A2 + 2 + 8 * k, ph18(k), '2 番の旋律 (トラック 18 の音から)' if k == 0 else None)
    P.section(SABI2, '大サビ — 総奏、06:39 がバック', 'ギター・ドラム・ベース・弦・トランペットの動機、実音のピアノの動機を 3 声で。06:39 の実音 (後半) がバックに小さく')
    for k in range(7): put('S', SABI2 + 2 + 4 * k, HOOK, None, 12); put('A', SABI2 + 3 + 4 * k, HOOK, None); put('T', SABI2 + 4 + 4 * k, HOOK, None, -12)
    P.section(OUTRO, '終わり — 06:42 の実音の終わりとアルペジオ', '06:42 の実音の終わり (表)、アルペジオと高い開いた 5 度だけが残って消える。輪 G → D/F# → Em7 → Cmaj7')
    harm_fit(P, A1, TOTAL - 4, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 0 else 0.02, fout=6.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s%s)' % (NAMES[rid], '表' if lead else 'バック、小さく', '、全音上げて' if sm else ''))
    first = True
    for b in range(1, TOTAL - 3):
        s = sec_of(b); c = chord(P.harm[b * BPB]); r = 50 + c['root']; pat = [r, r + 7, r + 12, r + c['pcs'][1] - c['root'] + 12, r + 7, r + c['pcs'][1] - c['root'] + 12, r + 12, r + 7]
        env = 0.5 if s in ('intro', 'inter') else 0.55 if s == 'a' else 0.6 if s == 'sabi' else max(0.25, 0.5 - 0.012 * (b - OUTRO))
        for k, m in enumerate(pat): add('AR', b * BPB + k * 0.5, 0.45, m, env * (1.0 if k % 2 == 0 else 0.8), 'クリーンなアルペジオ (8 分音符)' if first else None, pan=(-0.3 if k % 2 == 0 else 0.3)); first = False
    def pad(b0, b1, g, label=None):
        q = b0 * BPB; first = True
        while q < b1 * BPB:
            h = P.harm[q]; q1 = q
            while q1 < b1 * BPB and P.harm[q1] == h: q1 += 1
            for v, lo, hi in (('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)):
                for i, m in enumerate(tones_of(h, lo, hi)[:3]): oadd(v, q + 0.03 * i, (q1 - q) + 0.3, m, g * (1.0 if i == 0 else 0.8), label if (first and i == 0) else None); first = False
            q = q1
    def trem(b0, b1, g):
        for b in range(b0, b1):
            for k in range(BPB * 2):
                t = tones_of(P.harm[b * BPB], 62, 76); oadd('V2', b * BPB + k * 0.5, 0.45, t[-1], g * (1.0 if k % 2 == 0 else 0.8)); oadd('VA', b * BPB + k * 0.5, 0.45, t[0], g * 0.9)
    pad(INTRO + 2, A1, 0.1, '弦のパッド'); pad(A1, SABI1, 0.1); pad(INTER, A2, 0.1); pad(A2, SABI2, 0.12); pad(OUTRO, TOTAL - 4, 0.08)
    trem(SABI1 + 4, INTER, 0.14); trem(SABI2 + 4, OUTRO, 0.15)
    for b in list(range(INTRO + 2, A1, 4)) + list(range(OUTRO, TOTAL - 4, 4)): oadd('V1', b * BPB, 4 * BPB + 0.5, 88, 0.08, '高い開いた 5 度' if b == INTRO + 2 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 83, 0.07)
    for k in range(6): line_ = HOOK; t = (SABI1 + 2 + 4 * k) * BPB
    def line(v, bar, mat, tr, g, label=None):
        t = bar * BPB; first = True
        for d, m in mat: oadd(v, t, d, m + tr, g, label if first else None); first = False; t += d
    for k in range(6): line('V1', SABI1 + 2 + 4 * k, HOOK, 12, 0.24, 'Vn I — サビの動機' if k == 0 else None); line('FL', SABI1 + 2 + 4 * k, HOOK, 24, 0.12)
    for k in range(4): line('HN', A2 + 2 + 8 * k, ph18(k), -12, 0.14, 'ホルン (トラック 18 の音から)' if k == 0 else None)
    for k in range(7): line('V1', SABI2 + 2 + 4 * k, HOOK, 12, 0.26, '大サビ — Vn I・トランペット' if k == 0 else None); line('TR', SABI2 + 2 + 4 * k, HOOK, 0, 0.2); line('FL', SABI2 + 2 + 4 * k, HOOK, 24, 0.12)
    first = True
    for b in range(A1, TOTAL - 6):
        s = sec_of(b)
        if s in ('intro',) or b >= OUTRO + 8: continue
        loud = s == 'sabi'; soft = s in ('inter', 'outro')
        g = 0.5 if soft else 0.75 if loud else 0.6
        c = chord(P.harm[b * BPB]); r = 38 + c['root']
        if r > 45: r -= 12
        add('SB', b * BPB, 1.9, r, 0.45 if not loud else 0.55, 'シンセ・ベース (根音)' if first else None); add('SB', b * BPB + 2, 1.4, r, 0.4); add('SB', b * BPB + 3.5, 0.45, r + 7, 0.3)
        if soft: first = False; continue
        dr(b * BPB, 'kick', g, 0, 'ロックのドラム' if first else None); dr(b * BPB + 2, 'kick', g * 0.9)
        if loud: dr(b * BPB + 2.5, 'kick', g * 0.6)
        dr(b * BPB + 1, 'snare', g * 0.8, 0.05); dr(b * BPB + 3, 'snare', g * 0.8, 0.05)
        for k in range(8): dr(b * BPB + k * 0.5, 'ride' if loud else 'hatc', (0.5 if loud else 0.4) * (1.0 if k % 2 == 0 else 0.7), 0.3)
        if loud and (b - SABI1) % 4 == 0: dr(b * BPB, 'crash', 0.6, -0.2)
        if loud and (b - SABI1) % 8 == 7:
            for k, (tm, mm) in enumerate(((3.0, 55), (3.25, 52), (3.5, 50), (3.75, 47))): add('DR', b * BPB + tm, 0.25, mm, 0.6 * DRUM_G, None, kind='tom', pan=-0.3 + 0.2 * k)
        first = False
    first = True
    for b in list(range(SABI1, INTER)) + list(range(SABI2, OUTRO)):
        c = chord(P.harm[b * BPB]); r = 38 + c['root']
        if r > 45: r -= 12
        add('GT', b * BPB, 3.8, r, 0.24, '歪んだギターのパワーコード (サビ)' if first else None, mute=False, pan=-0.5); add('GT', b * BPB + 0.02, 3.8, r + 12, 0.14, None, mute=False, pan=0.5); first = False
    add('X', (TOTAL - 4) * BPB, 14, 40, 0.2, '鐘 (終わりに、小さく)')

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R42, R18], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4], 'band_gain': 1.0, 'orchestra': True,
        'title': 'Requiem BADA — CLVIII · Madre e due mattini',
        'subtitle': '11/06 06:42・06:39、MOTHER・LOVELESS (音も旋律も使わず、調・テンポ・和音の流れ・様式だけ)、トラック 18 を合成して: 序〜A メロ (06:39 の実音) → サビ (06:42 がバック) → 間奏 (06:42、全音上げて) → 2 番 (トラック 18、全音上げて) → 大サビ (06:39 がバック) → 終わり (06:42 の終わり)。ト長調 / ホ短調、♩=72',
        'legend': ['X', 'AR', 'SB', 'DR', 'GT', 'PF', 'V1', 'V2', 'VA', 'VC', 'FL', 'HN', 'TR'], 'vname': {'X': '鐘', 'AR': 'アルペジオ', 'SB': 'ベース', 'DR': 'ドラム', 'GT': 'ギター', 'PF': '実音のピアノ (06:42 の 1 音)', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'FL': 'Fl', 'HN': 'Hn', 'TR': 'Tp'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['MOTHER・LOVELESS (LUNA SEA) からは採譜で読んだ調 (ト長調〜ホ短調)・テンポ (♩≈68 / ♩≈80 → ♩=72)・和音の流れ (G → D/F# → Em7 → Cmaj7 / Em7 → Cmaj7 → G → D7 / G → D7 → Em7 → C) と様式だけ。旋律 = 06:39 の最上声の音 (ホ短調の五音に寄せて)、2 番はトラック 18 の音から、サビの動機は 06:39 の第 2 句の 7 音',
                   '実音は段落ごとに表を入れ替える (06:39 そのまま、06:42 とトラック 18 は全音上げて)。4 声は 06:42 の実音のピアノの 1 音のサンプラー。声なし。']}

if __name__ == '__main__':
    print('tune39', ' '.join('%s:%g' % (name_of(m), d) for d, m in T39[:12])); print('tune18', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18[:12])); print('hook', ' '.join('%s:%g' % (name_of(m), d) for d, m in HOOK))
    compose.main(OUT, seed=158, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
