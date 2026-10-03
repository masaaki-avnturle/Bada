#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXII · Praeludium, Interludium e Fuga 10/03 (LXXXIX をベースに、10/03 13:19 の音を共鳴のシンセサイザーに、13:22・13:24・13:27 の実音をメロディーに)
  ベース (裏): LXXXIX (Requiem e Fuga, recto e verso, ニ短調 96 小節) の楽譜を変ロ短調 (−4) に移して 2 小節目から全部 — 伸ばした主題・2 つのフーガ・ストレッタ・Amen (cp14_x4 の音声は使わない)。
    4 声は ×0.14、伸ばした主題のピアノは ×0.12 で小さく (ステムで測って、表の録音より約 7 dB 下)
  共鳴のシンセサイザー: 10/03 13:19 の録音から切り出した 8 音 (rid VOXRS — 減衰させず、持続部をループで伸ばす) で、その時の和音 (根音・5 度・3 度) を鳴らし続ける。和音は表の録音の採譜から (録音のない所は LXXXIX の和音)
  メロディー (表): 10/03 の録音の実音 (dip_breath.py で息のような所だけ下げて、ほかは加工なし)
    Praeludium  — 13:22 (1 分 40 秒、変ロ短調) を 2 小節目から
    Interludium — 13:24 (2 分 16 秒、変ロ短調) を 29 小節目から
    Fuga        — 13:27 (1 分 43 秒、変ロ短調) を 65 小節目から。その採譜の最上声から作った 8 拍の主題の 4 声フーガを裏で (提示 → 反行 → ストレッタ → 拡大、和音は録音のその時の和音に寄せる)
    締めくくり  — 録音が終わる 92 小節目から主題のストレッタ (変ロ長調) と LXXXIX の Amen が重なり、変ロ長調の和音で閉じる。100 小節 = 6 分 40 秒 + 残響
  音源: フーガの 4 声は 13:24・13:22 のピアノの 1 音 (立ち上がりが速く減衰するものだけ) と bank109、共鳴は 13:19 の音。声なし
  使い方: python compose_tablet112.py <bank112.json (build_sampler: 13:19・13:22・13:24・13:27)> <bank109.json> <score_tablet89.json> <wav のフォルダ> [score_tablet112.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK112, BANK109, SCORE89, WDIR = sys.argv[1], sys.argv[2], sys.argv[3], os.path.abspath(sys.argv[4]); OUT = sys.argv[5] if len(sys.argv) > 5 else 'score_tablet112.json'
sys.argv = [sys.argv[0], BANK112]
import compose_tablet as CT
from clean_bank import measure
B112 = json.load(open(BANK112)); RECS = B112['recordings']; S89 = json.load(open(SCORE89))
RS, R22, R24, R27 = '20261003_131932', '20261003_132245', '20261003_132431', '20261003_132703'
BPM = 60; TR = -4                                                                                   # ニ短調 → 変ロ短調
T22 = 8.0; E22 = int(math.ceil((T22 + RECS[R22]['dur']) / 4.0))
T24 = (E22 + 2) * 4.0; E24 = int(math.ceil((T24 + RECS[R24]['dur']) / 4.0))
T27 = (E24 + 2) * 4.0; E27 = int(math.ceil((T27 + RECS[R27]['dur']) / 4.0))
FUGA0 = int(T27 / 4) + 2; CLOSE = E27 + 1; TOTAL = CLOSE + 8; BASE0 = 2
MIN_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4']
MAJ_B = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'B/D#', 'E/G#', 'Emaj7', 'F#sus4']
def tr_list(lst, semis): return [transpose_h([[c]], semis)[0][0] for c in lst]
CANDS = tr_list(MIN_E, 6); CANDS_J = tr_list(MAJ_B, -1)                                           # 変ロ短調 / 変ロ長調
MAJ = {1: 2, 6: 7, 8: 9}                                                                            # 変ロ短調 → 変ロ長調 (レ♭→レ、ソ♭→ソ、ラ♭→ラ)
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []
_t0, _inside = CT.excerpt(R27, TR, 13.0); SUBJ = [(d, m + TR) for d, m in CT.make_subject(_inside, TR, BPM)]

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def majify(m): return (m - m % 12 + MAJ[m % 12]) if m % 12 in MAJ else m

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
            rc = set(chord(RH[a])['pcs'])
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + 1.5 * len(cc & rc) / max(1, len(cc)) + (1.2 if c == RH[a] else 0)
            cs = max(cands, key=score)
            for q in range(2): P.harm[a + q] = cs

def fit(v, mat, tr):
    if v == 'B' and min(m for _, m in mat) + tr < 36: tr += 12
    if max(m for _, m in mat) + tr > TOP[v]: tr -= 12
    if min(m for _, m in mat) + tr < RANGE[v][0]: tr += 12
    return tr
def entry(P, bar, v, mat, tr0, label, E, beat=0):
    tr = fit(v, mat, octs[v] + tr0); P.place(v, bar, mat, tr, label or '', beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def augment(mat, k=2): return [(k * d, m) for d, m in mat]

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 1.0
    for q in range(TOTAL * BPB):                                                                    # 和音: 表の録音の採譜 → なければ LXXXIX (−4)
        cur = None
        for rid, t0 in ((R22, T22), (R24, T24), (R27, T27)):
            rec = RECS[rid]
            if t0 <= q < t0 + rec['dur']:
                cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= q - t0: cur = s['ch']
        if cur is None:
            qb = int(q - BASE0 * BPB); cur = transpose_h([[S89['harm'][min(max(qb, 0), len(S89['harm']) - 1)]]], TR)[0][0]
        RH.append(cur); P.harm[q] = cur
    P.section(0, 'Praeludium — 13:22 の実音', '裏で LXXXIX (変ロ短調に移して) が始まり、13:19 の音の共鳴が和音を保つ — 2 小節目から 10/03 13:22 の録音そのもの')
    for v in VOICES: P.rest_bars(v, 0, int(T24 / 4))
    P.section(int(T24 / 4), 'Interludium — 13:24 の実音', '10/03 13:24 の録音そのもの — 裏では LXXXIX のフーガとレクイエムが続き、共鳴は録音の和音を追う')
    for v in VOICES: P.rest_bars(v, int(T24 / 4), FUGA0)
    P.section(int(T27 / 4), 'Fuga — 13:27 の実音と、その主題の 4 声フーガ', '10/03 13:27 の録音そのもの — 裏でその採譜から作った主題 %s の 4 声フーガ: 提示 → 反行 → ストレッタ → 拡大 (和音は録音のその時の和音に寄せて)' % ' '.join(name_of(m) for _, m in SUBJ))
    f = FUGA0; lab = '主題 13:27'; E = []
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, SUBJ, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_fit(P, f, f + 8, E, CANDS)
    E = []; entry(P, f + 8, 'S', invert(SUBJ), 0, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(SUBJ), 0, lab + ' (反行)', E); harm_fit(P, f + 8, f + 12, E, CANDS)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, SUBJ, 0, lab + ' ストレッタ' if k == 0 else None, E)
    harm_fit(P, f + 12, f + 18, E, CANDS)
    E = []; entry(P, f + 18, 'B', augment(SUBJ), 0, lab + ' (拡大 ×2)', E); entry(P, f + 20, 'S', SUBJ, 0, lab, E); harm_fit(P, f + 18, f + 22, E, CANDS)
    for v in VOICES: P.rest_bars(v, f + 22, CLOSE)
    P.section(CLOSE, '締めくくり — 主題のストレッタ (変ロ長調) と LXXXIX の Amen', '録音が終わると、主題が変ロ長調で 4 声のストレッタに — 裏の LXXXIX の Amen と重なって、変ロ長調の和音で閉じる')
    E = []
    for k, v in enumerate('SATB'): entry(P, CLOSE + k, v, SUBJ, 0, lab + ' ストレッタ (長調)' if k == 0 else None, E)
    entry(P, CLOSE + 4, 'B', augment(SUBJ), 0, lab + ' (拡大 ×2)', E); entry(P, CLOSE + 4, 'S', SUBJ, 12, None, E)
    harm_fit(P, CLOSE, TOTAL - 2, E, CANDS_J)
    for b in range(TOTAL - 2, TOTAL): P.set_harm(b, 'A#'); P.hold.add(b)
    P.place('S', TOTAL - 2, [(4, 82)] * 2, 0, 'シ♭ (頂点)'); P.place('B', TOTAL - 2, [(4, 46)] * 2, 0, '')
    for k in range(CLOSE, TOTAL): P.dyn[k] = 1.05 + 0.15 * min(1.0, (k - CLOSE) / 4.0) - (0.25 if k >= TOTAL - 2 else 0)
    return P

def post(P, events, ex):
    for rid, t0, name in ((R22, T22, '13:22'), (R24, T24, '13:24'), (R27, T27, '13:27')):
        add('REC', t0, RECS[rid]['dur'], 0, 0.85, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.02, fout=1.0, rid=rid + '.wav', tag='10/03 %s — メロディー (実音)' % name)
    # 共鳴のシンセサイザー (13:19 の音、rid VOXRS): 和音が変わるごとに根音・5 度・3 度を保つ
    q = 0; first = True
    while q < TOTAL * BPB:
        h = P.harm[q]; q1 = q
        while q1 < TOTAL * BPB and P.harm[q1] == h: q1 += 1
        d = max(1.0, (q1 - q) + 0.6); c = chord(h); last = q >= (TOTAL - 2) * BPB
        pcs = [c['root'], c['fifth'], c['third']]; tones = [min((x for x in range(52, 76) if x % 12 == p), key=lambda x: abs(x - 62)) for p in pcs]
        g = 0.065 if not last else 0.09
        for i, m in enumerate(tones):
            if m % 12 in MAJ and q >= CLOSE * BPB: m = majify(m)
            add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.75), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.2, layer='res'); first = False
        add('PF', q, d, tones[0] - 12, g * 0.7, None, rid='VOXRS', rel=1.2, layer='res')
        q = q1
    for v in VOICES: events[v] = [(s, d, majify(m) if s >= CLOSE * BPB else m, lab) for s, d, m, lab in events[v]]

def merge_base(path):
    """LXXXIX の楽譜を変ロ短調に移して 2 小節目から裏に (4 声 ×0.35、ピアノ ×0.3、cp14_x4 の音声は使わない)"""
    d = json.load(open(path)); off = BASE0 * BPB
    for n in S89['notes']:
        t = n['t'] + off
        if t >= TOTAL * BPB: continue
        d['notes'].append(dict(n, t=t, beat=n['beat'] + off, m=n['m'] + TR, dyn=round(n.get('dyn', 1.0) * 0.14, 4), label=None, role='base'))
    for e in S89['extras']:
        if e['v'] != 'PF': continue
        t = e['t'] + off
        if t >= TOTAL * BPB: continue
        d['extras'].append(dict(e, t=t, beat=e['beat'] + off, m=e['m'] + TR, gain=round(e['gain'] * 0.12, 4), label=None, layer='base'))
    d['notes'].sort(key=lambda n: n['t']); d['extras'].sort(key=lambda e: e['t'])
    json.dump(d, open(path, 'w'), ensure_ascii=False)

def make_bank(path):
    """音源: 13:22・13:24 のピアノの 1 音 (立ち上がりが速く減衰するもの) + bank109 + 13:19 の音 (rid VOXRS、共鳴用)"""
    out = []
    for s in B112['samples']:
        if s['rid'] == RS: out.append(dict(s, rid='VOXRS')); continue
        atk, dec = measure(s['file'])
        if atk <= 0.12 and dec <= -0.1: out.append(s)
    out += json.load(open(BANK109))['samples']
    json.dump(dict(recordings={}, samples=out), open(path, 'w'), ensure_ascii=False)
    from collections import Counter; print('bank', Counter(s['rid'] for s in out))

META = {'style': 'recsampler', 'bank': None, 'rec_order': [R24, R22], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42], 'src_name': {'VOXRS': '共鳴 (13:19 の音)'},
        'title': 'Requiem BADA — CXII · Praeludium, Interludium e Fuga 10/03',
        'subtitle': 'LXXXIX をベースに (変ロ短調に移して裏に)、13:19 の音を共鳴のシンセサイザーに、13:22・13:24・13:27 の実音をメロディーに — 前奏曲 → 間奏曲 → フーガで締めくくる (変ロ短調 → 変ロ長調, ♩=60, 6 分 47 秒)',
        'legend': ['PF'], 'vname': {'PF': '共鳴 / 裏 (LXXXIX)'},
        'footer': ['Praeludium: 13:22 (2 小節目から) → Interludium: 13:24 (29 小節目から) → Fuga: 13:27 (65 小節目から) + その主題の 4 声フーガ → 締めくくり: 主題のストレッタ (変ロ長調) と LXXXIX の Amen',
                   '裏 = LXXXIX の楽譜を −4 に移して小さく (cp14_x4 の音声は使わない)。共鳴 = 13:19 の録音の 8 音で、その時の和音を保つ (減衰させない)。録音は息のような所だけ下げ、ほかは加工なし。声なし。']}

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; make_bank(bank_out); META['bank'] = bank_out
    print('subject 13:27', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ), '| T22 %.0f E22 %d T24 %.0f E24 %d T27 %.0f E27 %d FUGA0 %d CLOSE %d TOTAL %d' % (T22, E22, T24, E24, T27, E27, FUGA0, CLOSE, TOTAL))
    compose.main(OUT, seed=112, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    merge_base(OUT)
    d = json.load(open(OUT))
    for n in d['notes']:
        if n.get('role') != 'base': n['src'] = R24
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
