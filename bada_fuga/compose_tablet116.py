#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXVI · Canzone 10/03 sopra late_bach_fuga_8x (いつも通りに: 10/03 13:24・13:27 を主題歌に、バックに late_bach_fuga_8x)
  主題歌 (表): 10/03 13:24 (2 分 16 秒) → 13:27 (1 分 43 秒) の録音をそのまま、元の速さ・元の高さで (変ロ短調; dip_breath.py で息のような所だけ下げて)
  バック: late_bach_fuga_8x.mp4 (29 分、ニ短調の ×8 のピアノ) の音声 — 60 秒ごとに調で調べると全体がニ短調なので、ニ短調がいちばん濃い 1260 秒からの窓を
    テープのように −4 (変ロ短調へ、速さは 0.79 倍 = ×10 のピアノに) して敷く。主題歌より約 8 dB 下 (ステムで測って)
  裏の層 (CII と同じ作り): 採譜の骨組みを小さく (2 拍ごとの息をする打ち直し) ／ 13:27 のあいだは、その採譜から作った主題の 4 声フーガ (提示 → 反行 → ストレッタ → 拡大、和音は録音のその時の和音に寄せる)
  Coda: 主題を 4 倍に伸ばして、録音自身の音で 2 拍ごとに打ち直す — バックは消えていく (XCI と同じ)
  音源は CXII と同じ (13:22・13:24 のピアノの 1 音 + bank109)。声なし
  使い方: python compose_tablet116.py <bank112.json> <bank109.json> <score_tablet89.json> <wav のフォルダ (<rid>_clean.wav と late_bach_fuga_8x.wav)> [score_tablet116.json]
"""
import sys, os, json, math
OUT = sys.argv[5] if len(sys.argv) > 5 else 'score_tablet116.json'
sys.argv = sys.argv[:5] + [OUT]
import compose_tablet112 as T
from compose import *
import compose

R24, R27 = T.R24, T.R27; RECS = T.RECS
BACK = os.path.join(T.WDIR, 'late_bach_fuga_8x.wav'); BACK_T0 = 1260.0; BACK_SEMIS = -4; BACK_G = 0.3
T24 = 16.0; E24 = int(math.ceil((T24 + RECS[R24]['dur']) / 4.0))
T27 = (E24 + 2) * 4.0; E27 = int(math.ceil((T27 + RECS[R27]['dur']) / 4.0)); FUGA0 = int(T27 / 4) + 2
CODA = E27 + 1; TOTAL = CODA + 10
SUBJ = T.SUBJ

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = 60; P.dyn[k] = 1.0
    for q in range(TOTAL * BPB):                                                                    # 和音は録音の採譜 (ないところは変ロ短調)
        cur = 'A#m'
        for rid, t0 in ((R24, T24), (R27, T27)):
            rec = RECS[rid]
            if t0 <= q < t0 + rec['dur']:
                cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= q - t0: cur = s['ch']
        T.RH.append(cur); P.harm[q] = cur
    P.section(0, 'Intro — late_bach_fuga_8x だけ', 'バッハの晩年のフーガの ×8 のピアノ (ニ短調) を −4 に下げて (変ロ短調、×10 に) — 5 小節目から主題歌')
    P.section(4, '主題歌 1 — 10/03 13:24 (実音)', '録音そのもの、元の速さ・元の高さで — バックは約 8 dB 下、裏で採譜の骨組みが小さく息をする')
    for v in VOICES: P.rest_bars(v, 0, FUGA0)
    P.section(int(T27 / 4), '主題歌 2 — 10/03 13:27 (実音) と、その主題の 4 声フーガ', '録音そのもの — 裏で採譜の最上声から作った主題 %s の 4 声フーガ: 提示 → 反行 → ストレッタ → 拡大 (和音は録音のその時の和音に寄せて)' % ' '.join(name_of(m) for _, m in SUBJ))
    f = FUGA0; lab = '主題 13:27'; E = []
    for k, v in enumerate('ASBT'):
        T.entry(P, f + 2 * k, v, SUBJ, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    T.harm_fit(P, f, f + 8, E, T.CANDS)
    E = []; T.entry(P, f + 8, 'S', T.invert(SUBJ), 0, lab + ' (反行)', E); T.entry(P, f + 10, 'T', T.invert(SUBJ), 0, lab + ' (反行)', E); T.harm_fit(P, f + 8, f + 12, E, T.CANDS)
    E = []
    for k, v in enumerate('ASTB'): T.entry(P, f + 12 + k, v, SUBJ, 0, lab + ' ストレッタ' if k == 0 else None, E)
    T.harm_fit(P, f + 12, f + 18, E, T.CANDS)
    E = []; T.entry(P, f + 18, 'B', T.augment(SUBJ), 0, lab + ' (拡大 ×2)', E); T.entry(P, f + 20, 'S', SUBJ, 0, lab, E); T.harm_fit(P, f + 18, f + 22, E, T.CANDS)
    for v in VOICES: P.rest_bars(v, f + 22, TOTAL)
    P.section(CODA, 'Coda — 主題を 4 倍に', '主題を 4 倍に伸ばして、録音自身の音で 2 拍ごとに打ち直す — バックは消えていく')
    for b in range(CODA, TOTAL): P.set_harm(b, 'A#m' if b < TOTAL - 2 else 'A#'); P.hold.add(b)
    return P

def post(P, events, ex):
    back_len = (CODA + 4) * BPB
    T.add('REC', 0, back_len, 0, BACK_G, None, src=BACK, off=BACK_T0, fin=3.0, fout=16.0, semis=BACK_SEMIS, rid='late_bach_fuga_8x.wav', tag='late_bach_fuga_8x (−4、バック)')
    for rid, t0, name in ((R24, T24, '13:24'), (R27, T27, '13:27')):
        T.add('REC', t0, RECS[rid]['dur'], 0, 0.85, None, src=os.path.join(T.WDIR, rid + '_clean.wav'), off=0.0, fin=0.02, fout=1.0, rid=rid + '.wav', tag='10/03 %s — 主題歌 (実音)' % name)
        first = True
        for s in RECS[rid]['segs']:                                                                  # 骨組み
            b0 = t0 + s['t']
            for m in s['m']:
                step = 2.0; n_ = max(1, int(round(s['d'] / step)))
                for j in range(n_):
                    amp = 1.0 if j == 0 else 0.55
                    T.add('PF', b0 + j * step, min(step, s['d'] - j * step) + 0.2, m, 0.11 * amp * (1.2 if m < 48 else 1.0), '採譜 (骨組み、小さく)' if (first and rid == R24) else None, rid=rid, rel=0.5, layer='bb'); first = False
    t = CODA * BPB; first = True                                                                    # Coda: 主題 ×4 を 2 拍ごとに打ち直す
    for d, m in T.augment(SUBJ, 4):
        n_ = max(1, int(round(d / 2)))
        for i in range(n_):
            amp = 1.0 if i == 0 else 0.6
            T.add('PF', t + 2 * i, 2.2, m, 0.7 * amp, '主題 13:27 ×4' if first else None, rid=R27, rel=0.7, layer='coda'); T.add('PF', t + 2 * i, 2.2, m - 12, 0.35 * amp, None, rid=R27, rel=0.7, layer='coda'); first = False
        t += d

META = {'style': 'recsampler', 'bank': None, 'rec_order': [R24, R27], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — CXVI · Canzone 10/03 sopra late_bach_fuga_8x',
        'subtitle': '10/03 13:24 → 13:27 の録音を主題歌に (実音)、バックに late_bach_fuga_8x (−4 に下げて変ロ短調に) — 裏で骨組みと 13:27 の主題の 4 声フーガ、Coda は主題を 4 倍に (変ロ短調, ♩=60)',
        'legend': ['PF'], 'vname': {'PF': '裏の層'},
        'footer': ['Intro (バックだけ) → 主題歌 1: 13:24 (5 小節目から) → 主題歌 2: 13:27 + その主題の 4 声フーガ → Coda: 主題 ×4、バックは消えていく',
                   'バック = late_bach_fuga_8x.mp4 (ニ短調) の 1260 秒からの窓を −4 (×10 に)、主題歌より約 8 dB 下。録音は息のような所だけ下げ、ほかは加工なし。声なし。']}

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    compose.main(OUT, seed=116, bpm=60, builder=build, meta=META, extras=T.extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']: n['src'] = R24
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] = d['meta']['subtitle'].replace('♩=60)', '♩=60, %d 分 %d 秒)' % (h, rem + 7)); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'T24 %.0f E24 %d T27 %.0f E27 %d CODA %d' % (T24, E24, T27, E27, CODA), 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
