#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXX · Fuga ben temperata, R&B e rock (10/12 の録音をベースに、鼓動をロックバンドのドラムに見立てて — 平均律のフーガを R&B のリズムが中音域で支える、睡眠誘導の洗脳的な曲)
  ベース (裏): 10/12 06:27 (2 分 56 秒) → 06:30 (1 分 9 秒) → 06:27 の録音の実音 (変ロ短調、息の所だけ下げて)、小さく
  表: 平均律クラヴィーア曲集のようなフーガ (ピアノの 1 音、4 声) — 主題 I は 06:27 の最上声から、主題 II は 06:30 の最上声から (compose_tablet.make_subject)
    Fuga I: 提示 (A → S → B → T) → 嬉遊 (R&B の和音が前に) → 反行とストレッタ → 保続低音 ／ Fuga II: 主題 II の提示 → 二重のストレッタ → 拡大の上で 2 つの主題 → 頂点 → Coda
    和音は、主題の音を含み、録音のその時の和音に近いものを選ぶ (harm_fit、共鳴)
  中音域 (R&B): 7th・9th の和音を シンコペーション (1 拍目・2 拍目の裏・3 拍目の 16 分裏・4 拍目の裏) で置き、ベース (13:04 の低い音) は根音を 1 拍目と 3 拍目の裏に、808 の重低音が根音を支える
  裏 (ロックバンドのドラム): キック = 鼓動 (ドッ・クン、1 拍目と 3 拍目)、スネアはハーフタイム (3 拍目)、ハイハットは 8 分 + スウィングする 16 分のゴースト、8 小節ごとにフィル、Fuga II はライド。Coda は鼓動だけに
  ♩=72 (安静より少し速い心拍 — 神経は高まるが平常心)、112 小節 = 6 分 13 秒。弔鐘・祝鐘なし、声なし
  使い方: python compose_tablet120.py <bank1012.json> <bank109.json> <wav のフォルダ> [score_tablet120.json]
"""
import sys, os, json, math
BANK1012, BANK109, WDIR = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3]); OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet120.json'
sys.argv = [sys.argv[0], BANK1012]
import compose_tablet as CT
from compose import *
import compose
from clean_bank import measure

B1012 = json.load(open(BANK1012)); RECS = B1012['recordings']; R1, R2 = '20261012_062753', '20261012_063057'
LOW = '20260925_130431'; PSRC = R1
BPM = 72; BAR_S = 240.0 / BPM; TOTAL = 112
INTRO, F1, EP, MID, PED, F2, DBL, AUG, CLI, CODA = 0, 8, 24, 32, 48, 56, 72, 80, 96, 104
MIN_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4']
CANDS = [transpose_h([[c]], 6)[0][0] for c in MIN_E]                                         # 変ロ短調
TR = -4                                                                                        # ニ短調 → 変ロ短調
_t, _in = CT.excerpt(R1, TR, 13.0); SUBJ1 = [(d, m + TR) for d, m in CT.make_subject(_in, TR, BPM)]
_t, _in = CT.excerpt(R2, TR, 13.0); SUBJ2 = [(d, m + TR) for d, m in CT.make_subject(_in, TR, BPM)]
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
DRUM_G = 0.33                                                                                 # ドラムは裏 (表のフーガより約 6 dB 下、ステムで測って)
def dr(beat, kind, g, pan=0.0, label=None): add('DR', beat, 0.25, 60, g * DRUM_G, label, kind=kind, pan=pan)

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
def rest_others(P, b0, b1, keep):
    for v in VOICES:
        if v not in keep: P.rest_bars(v, b0, b1)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 1.0
    plays = [(R1, 0.0), (R2, 54.0), (R1, 76.0)]
    for q in range(TOTAL * BPB):                                                                    # 和音の土台は録音のその時の和音
        cur = 'A#m'
        for rid, bar in plays:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    P.section(INTRO, 'Intro — 鼓動がドラムに', '10/12 06:27 の録音 (裏) の上で、鼓動のキック (ドッ・クン) が入り、ハイハットと R&B の和音が集まってくる')
    rest_others(P, INTRO, F1, '')
    P.section(F1, 'Fuga I — 提示', '主題 I %s (06:27 の最上声から) の 4 声の提示: A → S 答唱 → B → T 答唱。ハーフタイムのスネア、R&B の和音が中音域で支える' % ' '.join(name_of(m) for _, m in SUBJ1))
    E = []
    for k, v in enumerate('ASBT'):
        entry(P, F1 + 4 * k, v, SUBJ1, 7 if k % 2 else 0, '主題 I' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, F1 + 4 * k, F1 + 4 * k + 4)
        if k > 0: pass
    harm_fit(P, F1, EP, E, CANDS)
    P.section(EP, '嬉遊 — R&B の和音が前に', '主題の頭 (2 拍) がソプラノとアルトで追いかけ合い、R&B の和音とベースが前に出る')
    head = SUBJ1[:3]; E = []
    for k in range(4):
        entry(P, EP + 2 * k, 'S', head, 0, '主題 I の頭' if k == 0 else None, E, beat=0); entry(P, EP + 2 * k, 'A', head, -5, None, E, beat=2)
    rest_others(P, EP, MID, 'SA'); harm_fit(P, EP, MID, E, CANDS)
    P.section(MID, 'Fuga I — 反行とストレッタ', '反行 (S・T) → 4 声のストレッタ (1 小節ずつ) — クラッシュ、フィル')
    E = []; entry(P, MID, 'S', invert(SUBJ1), 0, '主題 I (反行)', E); entry(P, MID + 2, 'T', invert(SUBJ1), 0, '主題 I (反行)', E); entry(P, MID + 4, 'B', SUBJ1, 0, '主題 I', E)
    rest_others(P, MID, MID + 8, 'STB'); P.rest_bars('B', MID, MID + 4); P.rest_bars('S', MID + 4, MID + 8); P.rest_bars('T', MID + 6, MID + 8)
    harm_fit(P, MID, MID + 8, E, CANDS); E = []
    for k, v in enumerate('ASTB'): entry(P, MID + 8 + 2 * k, v, SUBJ1, 0, '主題 I ストレッタ' if k == 0 else None, E)
    harm_fit(P, MID + 8, PED, E, CANDS)
    P.section(PED, '保続低音', 'バスがシ♭を保ち、主題 I が 2 倍に伸びてソプラノに — ドラムはライドへ')
    P.place('B', PED, [(4, 46)] * 8, 0, '保続 (シ♭)'); E = [(PED * BPB, [(32, 46)])]
    entry(P, PED, 'S', augment(SUBJ1), 0, '主題 I (拡大 ×2)', E); entry(P, PED + 4, 'A', SUBJ1, 0, None, E)
    P.rest_bars('T', PED, F2); P.rest_bars('A', PED, PED + 4); harm_fit(P, PED, F2, E, CANDS)
    P.section(F2, 'Fuga II — 主題 II の提示', '主題 II %s (06:30 の最上声から) の 4 声の提示 — ライドのリズム、06:30 の録音が裏に' % ' '.join(name_of(m) for _, m in SUBJ2))
    E = []
    for k, v in enumerate('TABS'):
        entry(P, F2 + 4 * k, v, SUBJ2, 7 if k % 2 else 0, '主題 II' + (' 答唱' if k % 2 else ''), E)
        for w in 'TABS'[k + 1:]: P.rest_bars(w, F2 + 4 * k, F2 + 4 * k + 4)
    harm_fit(P, F2, DBL, E, CANDS)
    P.section(DBL, '二重のストレッタ', '主題 I と主題 II が交互に 1 小節ずつ重なる')
    E = []
    for k, v in enumerate('SATB'): entry(P, DBL + 2 * k, v, SUBJ1 if k % 2 == 0 else SUBJ2, 0, ('主題 I' if k == 0 else '主題 II') if k < 2 else None, E)
    harm_fit(P, DBL, AUG, E, CANDS)
    P.section(AUG, '拡大の上で 2 つの主題', 'バスに主題 I の拡大 (×2)、上で主題 II と主題 I が重なる — ドラムは 16 分のゴーストを増やす')
    E = []; entry(P, AUG, 'B', augment(SUBJ1), 0, '主題 I (拡大 ×2)', E); entry(P, AUG + 8, 'B', augment(SUBJ2), 0, '主題 II (拡大 ×2)', E)
    for k in range(4): entry(P, AUG + 4 * k, 'SATS'[k], SUBJ2 if k % 2 == 0 else SUBJ1, 0, None, E)
    harm_fit(P, AUG, CLI, E, CANDS)
    P.section(CLI, '頂点', '4 声のストレッタ (主題 I と II)、クラッシュ — そして静まる')
    E = []
    for k, v in enumerate('SATB'): entry(P, CLI + k, v, SUBJ1, 0, '主題 I ストレッタ' if k == 0 else None, E)
    for k, v in enumerate('SATB'): entry(P, CLI + 4 + k, v, SUBJ2, 0, '主題 II ストレッタ' if k == 0 else None, E)
    harm_fit(P, CLI, CODA, E, CANDS)
    P.section(CODA, 'Coda — 鼓動だけに', 'ドラムは鼓動のキックだけになり、主題 I が 2 倍に伸びてアルトに、変ロ長調の和音で静かに閉じる')
    E = []; entry(P, CODA, 'A', augment(SUBJ1), 0, '主題 I (拡大 ×2)', E); rest_others(P, CODA, TOTAL, 'A')
    harm_fit(P, CODA, TOTAL - 2, E, CANDS)
    for b in range(TOTAL - 2, TOTAL): P.set_harm(b, 'A#'); P.hold.add(b)
    for v in VOICES: P.rest_bars(v, TOTAL - 2, TOTAL)
    for k in range(TOTAL): P.dyn[k] = 1.1 if k < CLI else (1.25 if k < CODA else 0.9 - 0.3 * (k - CODA) / float(TOTAL - CODA))
    return P

def post(P, events, ex):
    for rid, bar, g in ((R1, 0.0, 0.35), (R2, 54.0, 0.35), (R1, 76.0, 0.25)):
        add('REC', bar * BPB, RECS[rid]['dur'] * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=1.0 if bar else 0.02, fout=4.0, rid=rid + '.wav', tag='10/12 %s — ベース (実音、小さく)' % ('06:27' if rid == R1 else '06:30'))
    def heart(b, g, label=None):
        dr(b, 'kick', g, 0.0, label); dr(b + 0.32 * BPM / 60.0, 'kick', g * 0.5)
    for bar in range(TOTAL):
        b0 = bar * BPB; c = chord(P.harm[b0]); c2 = chord(P.harm[b0 + 2]); coda = bar >= CODA; intro = bar < F1
        g = 1.0 if bar < CLI else 1.15 if bar < CODA else max(0.0, 1.0 - (bar - CODA) / float(TOTAL - CODA - 1))
        ride = PED <= bar < DBL
        # ---- ドラム (キック = 鼓動)
        heart(b0, 0.8 * (g if not coda else max(0.35, g)), 'キック = 鼓動 (ドッ・クン)' if bar == 0 else None); heart(b0 + 2, 0.7 * (g if not coda else max(0.3, g)))
        if not coda:
            if bar >= 6: dr(b0 + 2, 'snare', 0.6 * g, 0.05, 'スネア (ハーフタイム)' if bar == 6 else None)
            if bar >= 4:
                fill = (bar + 1) % 8 == 0 and bar >= F1
                for i in range(8):
                    if fill and i >= 4: break
                    if ride: dr(b0 + i * 0.5, 'ride', (0.3 if i % 2 == 0 else 0.18) * g, 0.35, 'ライド' if (bar == PED and i == 0) else None)
                    else: dr(b0 + i * 0.5, 'hatc', (0.3 if i % 2 == 0 else 0.17) * g, 0.25, 'ハイハット (8 分 + スウィングの 16 分)' if (bar == 4 and i == 0) else None)
                    if not ride and (i % 2 == 1 or bar >= AUG): dr(b0 + i * 0.5 + 0.33, 'hatc', 0.08 * g, 0.25)                # スウィングする 16 分のゴースト
                if fill:
                    for i in range(8): dr(b0 + 2 + i * 0.25, 'snare', (0.3 + 0.05 * i) * g, 0.05 * (i % 2 * 2 - 1))
                if bar in (F1, MID, F2, DBL, AUG, CLI): dr(b0, 'crash', 0.55 * g, -0.3)
            if bar >= AUG: dr(b0 + 3.5, 'hato', 0.22 * g, 0.3)
        # ---- R&B の和音 (中音域) とベース、808
        if bar >= 2:
            cg = (0.24 if intro else 0.4 if bar < CODA else 0.24 * g) * (1.25 if EP <= bar < MID else 1.0)
            def voicing(cc):
                pcs = [cc['root'], cc['third'], cc['fifth'], (cc['root'] + 10) % 12, (cc['root'] + 2) % 12]                 # 7th・9th
                tones = sorted({min((x for x in range(60, 76) if x % 12 == p), key=lambda x: abs(x - 66)) for p in pcs})
                return tones[:4]
            for beat, dur, gm, cc in ((0, 1.2, 1.0, c), (1.5, 0.8, 0.7, c), (2.75, 0.6, 0.8, c2), (3.5, 0.8, 0.6, c2)):
                for i, m in enumerate(voicing(cc)): add('PF', b0 + beat + 0.02 * i, dur, m, cg * gm * (0.9 if i else 1.0), 'R&B の和音 (7th・9th、シンコペーション)' if (bar == 2 and beat == 0 and i == 0) else None, rid=PSRC, rel=0.3, layer='rnb')
            root = 36 + c['root']; root2 = 36 + c2['root']; bg = 0.54 if not coda else 0.54 * g
            add('PF', b0, 1.4, root, bg, 'ベース (根音、1 拍目と 3 拍目の裏)' if bar == 2 else None, rid=LOW, rel=0.3, layer='bass'); add('PF', b0 + 2.5, 1.0, root2, bg * 0.8, None, rid=LOW, rel=0.3, layer='bass'); add('PF', b0 + 3.5, 0.5, root2 + 7, bg * 0.5, None, rid=LOW, rel=0.3, layer='bass')
            if not intro: add('E8', b0, 1.9, root - 12, 0.11 * g, '808 (重低音)' if bar == F1 else None); add('E8', b0 + 2, 1.9, root2 - 12, 0.1 * g, None)
    return

META = {'style': 'recsampler', 'bank': None, 'rec_order': [R1, R2], 'piano_decay': 1.6, 'reverb': [3.5, 1.5, 0.3], 'band_gain': 1.0,
        'title': 'Requiem BADA — CXX · Fuga ben temperata, R&B e rock',
        'subtitle': '10/12 06:27・06:30 の録音をベースに (裏、小さく) — 平均律のような 4 声の二重フーガ (06:27・06:30 の最上声の主題) を表に、R&B の 7th・9th の和音とベースが中音域で支え、鼓動をキックにしたロックのドラムが裏で叩く。睡眠誘導の洗脳的な、神経は高まるが平常心 (変ロ短調, ♩=72, 6 分 13 秒)',
        'legend': ['PF', 'DR', 'E8'], 'vname': {'PF': 'R&B の和音 / ベース', 'DR': 'ドラム (キック = 鼓動)', 'E8': '808'},
        'footer': ['Intro → Fuga I (提示 → 嬉遊 → 反行とストレッタ → 保続) → Fuga II (提示 → 二重のストレッタ → 拡大の上で 2 つの主題 → 頂点) → Coda (鼓動だけに、変ロ長調)',
                   'キック = 鼓動 (ドッ・クン、1・3 拍目)、スネアはハーフタイム、ハイハットは 8 分 + スウィングの 16 分、8 小節ごとにフィル、保続〜Fuga II はライド。弔鐘・祝鐘なし、声なし。']}

def make_bank(path):
    out = []
    for s in B1012['samples']:
        atk, dec = measure(s['file'])
        if atk <= 0.12 and dec <= -0.1: out.append(s)
    out += json.load(open(BANK109))['samples']
    json.dump(dict(recordings={}, samples=out), open(path, 'w'), ensure_ascii=False)
    from collections import Counter; print('bank', Counter(s['rid'] for s in out))

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; make_bank(bank_out); META['bank'] = bank_out
    print('subject I', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ1), '| subject II', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ2))
    compose.main(OUT, seed=120, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.4 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t']); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
