#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXLIV · Erbarm dich mein — BWV 721 al pianoforte (電子音ではなく、グランドピアノの音で、バッハの BWV 721 を共鳴的洗脳の仕上がりに — tablet117・tablet140 を材料に)
  土台: tablet117 (CXVII · Ninna nanna 10/03 — タブレットの実音のピアノ) の音をそのまま、表として (変ロ短調 → ヘ長調 → ヘ短調 → 変ロ長調、♩=60 → 44、12 分 59 秒)。tablet140 からは和音の流れ (採譜) だけを借りる
  被せる: バッハ コラール前奏曲 BWV 721「Erbarm dich mein, o Herre Gott」の書法 — 打ち続ける和音 (8 分音符、3 声) の上にコラールの定旋律を長い音で — を **グランドピアノ (合成、シンセ不使用)** で:
    ソプラノ = 定旋律 (コラール「Erbarm dich mein」、music21 の bach/bwv305 のソプラノ、2 倍に伸ばして 26 小節; 各段階の関係短調 変ロ短調・ニ短調・ヘ短調・ト短調)、アルト・テノール・バス = 8 分音符で打ち続ける和音 (脈)
    低いペダルの音 (L) が小節ごとに、高い共鳴 (H) が定旋律の反響として pp。脈は I で pp、III で頂点、IV で少しずつ消える — 共鳴的洗脳
  使い方: python compose_tablet144.py <bank140.json (和音の流れ)> <wav のフォルダ (20261003_117000.wav)> [score_tablet144.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet144.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
import soundfile as sf
RECS = json.load(open(BANKP))['recordings']; R140 = '20261105_140000'
R117 = '20261003_117000'; DUR = sf.SoundFile(os.path.join(WDIR, R117 + '.wav')).frames / 44100.0
TOTAL = int(math.ceil(DUR / 4.0)) + 1
BPM = 60
S1, S2, S3, S4 = 0, 38, 80, 141
TRK = {1: 1, 2: 5, 3: 8, 4: -2}
KEY = {1: 'Bbm', 2: 'Dm', 3: 'Fm', 4: 'Gm'}
CANDS = {1: ['Bbm', 'Gb', 'Db', 'Ab', 'Ebm', 'Fm', 'F', 'Bbm/Db', 'Gb/Bb', 'B', 'F7'],
         2: ['Dm', 'Bb', 'F', 'C', 'Gm', 'Am', 'A', 'Dm/F', 'Bb/D', 'Eb', 'A7'],
         3: ['Fm', 'Db', 'Ab', 'Eb', 'Bbm', 'Cm', 'C', 'Fm/Ab', 'Db/F', 'Gb', 'C7'],
         4: ['Gm', 'Eb', 'Bb', 'F', 'Cm', 'Dm', 'D', 'Gm/Bb', 'Eb/G', 'Ab', 'D7']}
def stage(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
ERB = [(d, m) for d, m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erbarm_melody.json')))['notes']]
def cantus(st, oct_=0, k=2): return [(d * k, m + TRK[st] + oct_) for d, m in ERB]
def clip(mat, max_beats):
    """曲の終わりを越えないように切る"""
    out = []; t = 0.0
    for d, m in mat:
        if t >= max_beats: break
        out.append((min(d, max_beats - t), m)); t += d
    return out
CF_BARS = int(math.ceil(2 * sum(d for d, _ in ERB) / 4.0))                                         # 26
CF_AT = [(S1 + 6, 1, 0), (S2 + 2, 2, 0), (S3 + 2, 3, 0), (S3 + 31, 3, -12), (S4 + 2, 4, 0), (S4 + 31, 4, 0)]   # (小節, 段階, オクターヴ)
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

def build():
    P = Piece(TOTAL)
    segs = RECS[R140]['segs']
    for q in range(TOTAL * BPB):
        cur = None
        if q < RECS[R140]['dur']:
            cur = segs[0]['ch']
            for s in segs:
                if s['t'] <= q: cur = s['ch']
            RECQ.add(q)
        if cur is None: cur = KEY[stage(q // BPB)]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.5 if k < S2 else 0.65 if k < S3 else (0.85 if k < S3 + 30 else 0.75) if k < S4 else (0.8 if k < S4 + 30 else max(0.25, 0.8 - 0.025 * (k - S4 - 30)))
    # 定旋律 (ソプラノ) と和音
    for b0, st, oc in CF_AT:
        harm_fit(P, b0, min(TOTAL - 2, b0 + CF_BARS + 1), [(b0 * BPB, clip(cantus(st, oc), (TOTAL - 3 - b0) * BPB))], CANDS[st])
    P.section(S1, 'I. 脈と定旋律 (変ロ短調, ♩=60)', 'BWV 721 の書法をグランドピアノで: アルト・テノール・バスが 8 分音符で和音を打ち続け (pp)、ソプラノが「Erbarm dich mein」の定旋律 (2 倍に伸ばして) を — 土台は tablet117 の実音のピアノ')
    P.section(S2, 'II. 脈が近づく (ニ短調)', '定旋律 2 度目、脈が少し強く、低いペダルの音が小節ごとに、高い共鳴が定旋律の反響として')
    P.section(S3, 'III. 頂点 (ヘ短調)', '定旋律 3 度目は脈が強く (頂点) → 4 度目は定旋律が 1 オクターヴ下で、脈が少し引く')
    P.section(S4, 'IV. 消える脈 (ト短調)', '定旋律 5 度目 → 6 度目は脈が少しずつ消えていき、高い共鳴と低いペダルだけが残る')
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    for b0, st, oc in CF_AT:
        for b in range(b0, min(TOTAL - 2, b0 + CF_BARS + 1)): P.rest[ 'S'].difference_update(range(b * BPB, b * BPB + BPB))
        P.place('S', b0, clip(cantus(st, oc), (TOTAL - 3 - b0) * BPB), 0, '定旋律「Erbarm dich mein」(%s)' % KEY[st])
    # 脈: 8 分音符の和音 (A・T・B)
    for b in range(2, TOTAL - 3):
        for v in 'ATB': P.rest[v].difference_update(range(b * BPB, b * BPB + BPB))
        for k in range(BPB * 2):
            h = P.harm[b * BPB + k // 2]
            a_, t_, b_ = tones_of(h, 60, 72), tones_of(h, 52, 64), tones_of(h, 40, 52)
            P.place('A', b, [(0.5, a_[-1])], 0, ('打ち続ける和音 (8 分音符、BWV 721 の脈)' if (b == 2 and k == 0) else None), beat=k * 0.5)
            P.place('T', b, [(0.5, t_[len(t_) // 2])], 0, None, beat=k * 0.5)
            P.place('B', b, [(0.5, b_[0])], 0, None, beat=k * 0.5)
    return P

def post(P, events, ex):
    add('REC', 0, DUR, 0, 0.55, None, src=os.path.join(WDIR, R117 + '.wav'), off=0.0, fin=0.02, fout=6.0, semis=0, rid=R117 + '.wav', tag='CXVII (tablet117、実音のピアノ) — 土台、そのまま')
    first = True
    for b in range(S2, TOTAL - 4):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 3.6, r, 0.18 * P.dyn.get(b, 0.8) / 0.8, '低いペダルの音 (小節ごと)' if first else None); first = False
    first = True
    for b0, st, oc in CF_AT[1:]:
        t = b0 * BPB + 2
        for d, m in clip(cantus(st, oc), (TOTAL - 3 - b0) * BPB - 2):
            add('H', t, d, m + 12, 0.1 * P.dyn.get(int(t // BPB), 0.8) / 0.8, '高い共鳴 (定旋律の反響、pp)' if first else None); first = False; t += d

META = {'style': 'elegia', 'detach': 0.85, 'humanize': True, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXLIV · Erbarm dich mein — BWV 721 al pianoforte',
        'subtitle': '電子音ではなくグランドピアノの音で、バッハの BWV 721「Erbarm dich mein, o Herre Gott」の書法 (打ち続ける和音の上の定旋律) を共鳴的洗脳の仕上がりに — 土台は tablet117 の実音のピアノ、和音の流れは tablet140 から: 脈 pp と定旋律 (変ロ短調) → 脈が近づく (ニ短調) → 頂点 (ヘ短調) → 消える脈 (ト短調)。♩=60',
        'legend': ['S', 'A', 'T', 'B', 'H', 'L'], 'vname': {'S': 'Pf 定旋律', 'A': 'Pf 脈 (上)', 'T': 'Pf 脈 (中)', 'B': 'Pf 脈 (低)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'},
        'footer': ['定旋律 = コラール「Erbarm dich mein, o Herre Gott」(music21 の収録譜 bach/bwv305 のソプラノ、イ短調、52 拍) を 2 倍に伸ばして、各段階の関係短調に (6 度)。BWV 721 からは書法 (8 分音符で打ち続ける和音) を借りる',
                   '合成はグランドピアノだけ (シンセ不使用)。土台は tablet117 の音をそのまま (表)。和音は tablet140 の採譜を優先しつつ定旋律の音を含む和音を選ぶ。鐘なし、声なし。']}

if __name__ == '__main__':
    print('base', round(DUR, 1), 's bars', TOTAL, '| cantus bars', CF_BARS)
    compose.main(OUT, seed=144, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e['v'] for e in d['extras']))
