#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXXVI · Fiore dolce senza voce (LXXXV から声を消して — ピアノの音だけで)
  LXXXV では、旋律の音を「その旋律の録音から切り出した 1 音」で鳴らしていたため、歌声や声の混じった録音 (9/28 06:42・17:46 など) の音が混じり、
  Intro の 9/24 11:21 の実音にも声のような音が入っていた。ここでは:
    - 録音そのもの (Intro) をやめ、左手の分散和音から始める
    - すべての音を、ピアノだけの 4 本の録音 (08:09・08:53・08:49・13:04) から切り出した 1 音で鳴らす (旋律は 08:09 の音)
  曲 (旋律・和音・形式) は LXXXV と同じ。以下 LXXXV の説明:
  坂本龍一の 2 曲からは「曲調」だけを借りる (旋律・音源は使わない、引用しない):
    Sweet — ゆっくりした短調のバラード。Em7 → Cmaj7 → Am7 → B7 の 4 小節の循環和音 (7 の和音・9 の響き)、
            左手は根音のあとに 8 分音符で静かに揺れる分散和音。
    Flower — 五音音階 (ミ・ソ・ラ・シ・レ) の東洋的な旋律、空虚 5 度の低音と 4 度を重ねた和音、間 (ま) をとった遅いテンポ。
            和声は Cmaj7 → D → Bm7 → Em (IV → V → iii → vi の、日本の歌によくある進み)。
  旋律はすべてユーザーの 11 曲の録音から: 各録音の採譜の最上声で、いちばん歌う 16 拍 (♩=66 で 14.5 秒) を探し、
    8 分音符に揃え、ホ短調 (長調の録音はト長調) に移して、Sweet ではホ短調の音階、Flower では五音音階に寄せる。
    9/28 17:46 (歌) は採譜が不確かなので、LXXXI で採った代表の節 (ラ♭・シ♭・シ♭・ファ・ソ♭・ラ・シ♭) を 2 倍の長さで。
    小節ごとの和音は、循環和音の型を守りながら、旋律といちばんぶつからない和音を候補から選ぶ。
  形式 (ホ短調):
    Intro      — 左手の分散和音だけで静かに始まる (LXXXV の 11:21 の実音はやめた)                     4 小節
    I. Sweet   — 循環和音の上で 08:53・08:09・13:04・11:18 の旋律が 4 小節ずつ                        16 小節 ♩=66
    II. Flower — 五音音階で 06:42・11:23・12:46・17:46 の旋律が 4 小節ずつ (♩=60、句の終わりで息をつく) 16 小節
    III. Fuga dolce — 08:49・08:06・11:21 の旋律に、前の旋律が 1 小節遅れてオクターヴ下で応える (カノン) 12 小節
    IV. Sweet ritorno — 08:53 の旋律が戻り、2 回目はオクターヴ下を重ねて                               8 小節
    Coda (Flower) — Cmaj7 → D → Bm7 → Em9、最後は Em9 の分散和音で開いたまま                          6 小節
  高音を抑える: 旋律はラ 4 を中心に、いちばん上でもミ 5。すべてピアノの実音 (録音から切り出した 1 音・録音そのもの)。
  使い方: python compose_tablet86.py <bank85.json> [score_tablet86.json]
"""
import sys, os, json
import numpy as np
from compose import name_of

BANK = json.load(open(sys.argv[1])); REC = BANK['recordings']
OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet86.json'
KEY = {  # 録音の調 (key.py の推定): (主音, 'm'|'M')
    '20260928_064235': (8, 'M'), '20260928_174654': (10, 'm'), '20260925_130431': (3, 'm'), '20260924_085314': (11, 'm'),
    '20260924_111846': (5, 'M'), '20260924_112131': (5, 'm'), '20260924_112313': (11, 'm'), '20260925_124643': (5, 'm'),
    '20260923_080918': (7, 'M'), '20260924_084937': (5, 'm'), '20260923_080607': (5, 'm')}
ACC = {'S': '20260923_080918', 'A': '20260924_085314', 'T': '20260924_084937', 'B': '20260925_130431'}   # 伴奏の音を切り出す録音
EMIN = [4, 6, 7, 9, 11, 0, 2]; PENTA = [4, 7, 9, 11, 2]
CAP, FLOOR = 76, 57
CH = {'Em7': [4, 7, 11, 2], 'Em9': [4, 7, 11, 2, 6], 'Gmaj7': [7, 11, 2, 6], 'Cmaj7': [0, 4, 7, 11], 'Cmaj9': [0, 4, 7, 11, 2], 'C6': [0, 4, 7, 9],
      'Am7': [9, 0, 4, 7], 'Am9': [9, 0, 4, 7, 11], 'D': [2, 6, 9], 'Dadd9': [2, 6, 9, 4], 'D6': [2, 6, 9, 11], 'B7': [11, 3, 6, 9], 'Bsus4': [11, 4, 6, 9],
      'B7b9': [11, 3, 6, 9, 0], 'Bm7': [11, 2, 6, 9], 'F#m7b5': [6, 9, 0, 4], 'Em': [4, 7, 11]}
SWEET = [['Em7', 'Em9', 'Gmaj7'], ['Cmaj7', 'Cmaj9', 'Am7', 'C6'], ['Am7', 'Am9', 'F#m7b5', 'D6'], ['B7', 'Bsus4', 'B7b9']]
FLOWER = [['Cmaj7', 'Cmaj9', 'Am9'], ['D', 'Dadd9', 'D6', 'Bsus4'], ['Bm7', 'Em7', 'B7'], ['Em9', 'Em7', 'Am9']]
PLAN = [  # (区切り, 小節数, ♩, 録音)
    ('intro', 4, 66, []),
    ('sweet', 16, 66, ['20260924_085314', '20260923_080918', '20260925_130431', '20260924_111846']),
    ('flower', 16, 60, ['20260928_064235', '20260924_112313', '20260925_124643', '20260928_174654']),
    ('canon', 12, 66, ['20260924_084937', '20260923_080607', '20260924_112131']),
    ('ritorno', 8, 68, ['20260924_085314', '20260924_085314']),
    ('coda', 6, 56, ['20260928_064235']),
]
HM = lambda r: '%s/%s %s:%s' % (r[4:6].lstrip('0'), r[6:8].lstrip('0'), r[9:11], r[11:13])

def phrase(rid, beats=16, bpm=66.0):
    """録音の採譜の最上声から、いちばん歌う 16 拍を探して 8 分音符に揃える → [(拍, 長さ, 音高)] (元の調のまま)"""
    if rid == '20260928_174654':                    # 歌の代表の節 (変ロ短調) を 2 倍に
        th = [(1, 68), (1, 70), (1, 70), (1, 65), (2, 66), (1, 69), (1, 70)]
        out, b = [], 0.0
        for d, m in th: out.append((b, d * 2.0, m)); b += d * 2.0
        return out, 0.0
    segs = REC[rid]['segs']; win = beats * 60.0 / bpm
    tops = []
    for s in segs:                                  # 最上声 (同じ音の打ち直しは 1 つの長い音に)
        if s['d'] < 0.12: continue
        m = max(s['m'])
        if tops and tops[-1][2] == m and s['t'] - (tops[-1][0] + tops[-1][1]) < 0.4: tops[-1] = (tops[-1][0], s['t'] + s['d'] - tops[-1][0], m); continue
        tops.append((s['t'], s['d'], m))
    best = None
    for s0 in np.arange(2.0, max(2.5, REC[rid]['dur'] - win), 0.5):
        w = [x for x in tops if s0 <= x[0] < s0 + win]
        if len(w) < 6: continue
        ms = [x[2] for x in w]; iv = np.abs(np.diff(ms))
        sc = (-abs(len(w) - 11) * 0.4 + 5 * np.mean((iv >= 1) & (iv <= 4)) - 3 * np.mean(iv == 0) + 0.5 * min(7, len(set(m % 12 for m in ms)))
              - max(0, max(ms) - min(ms) - 14) * 0.5 + (1.5 if (w[0][0] - s0) < 0.4 else 0))
        if best is None or sc > best[0]: best = (sc, s0, w)
    _, s0, w = best
    on = {}
    for t, d, m in w:
        q = round((t - s0) * bpm / 60.0 * 2) / 2
        if q >= beats - 0.5: continue
        if q not in on or m > on[q]: on[q] = m
    ks = sorted(on); out = []
    for i, q in enumerate(ks):
        nxt = ks[i + 1] if i + 1 < len(ks) else beats
        out.append((q, nxt - q, on[q]))
    return out, s0

def to_key(ph, rid, scale):
    """ホ短調 (長調はト長調) に移し、音階に寄せ、ラ 4 のあたりに置く"""
    tonic, mode = KEY[rid]; target = 4 if mode == 'm' else 7
    sh = (target - tonic) % 12
    if sh > 6: sh -= 12
    out = []
    for b, d, m in ph:
        m += sh; pc = m % 12
        if scale is not None and pc not in scale and not (scale is EMIN and pc == 3):
            m = min((m + k for k in (-1, 1, -2, 2)), key=lambda x: (x % 12 not in scale, abs(x - m), x > m))
        out.append([b, d, m])
    mu = np.mean([m for _, _, m in out])
    o = min(range(-4, 4), key=lambda o: abs(mu + 12 * o - 68))
    prev = None
    for x in out:                                   # 1 音目はラ 4 のあたり、あとは前の音にいちばん近いオクターヴ (ソ 3〜ミ 5 の中で): 流れる線に
        cand = [x[2] + 12 * k for k in range(-5, 6) if FLOOR <= x[2] + 12 * k <= CAP]
        x[2] = min(cand, key=lambda m: abs(m - (prev if prev is not None else x[2] + 12 * o)))
        prev = x[2]
    return [tuple(x) for x in out]

def fit_chord(mel, b0, cands):
    """その小節で鳴る旋律の音と、いちばんぶつからない和音 (候補の順を少し優先)"""
    def pen(c):
        pcs = CH[c]; p = 0.0
        for b, d, m in mel:
            ov = min(b0 + 4, b + d) - max(b0, b)
            if ov <= 0: continue
            w = ov * (1.6 if b % 2 == 0 else 1.0); pc = m % 12
            if pc in pcs: continue
            p += w * (1.0 if any(min((pc - q) % 12, (q - pc) % 12) == 1 for q in pcs) else 0.25)
        return p
    return min(cands, key=lambda c: pen(c) + 0.3 * cands.index(c))

def build():
    notes, extras, sections, entries, harm, bar_bpm = [], [], [], [], [], []
    def N(v, beat, dur, m, dyn, src, label=None):
        notes.append(dict(v=v, beat=round(beat, 3), dbeats=round(dur, 3), m=int(m), dyn=round(dyn, 3), src=src, label=label, det=1.0, role=''))
    bar = 0
    def sweet_acc(b0, c, dyn=0.42, mel=()):
        pcs = CH[c]; root = pcs[0]
        r = 40 + (root - 40) % 12
        N('B', b0, 2.5, r, dyn * 1.25, ACC['B']); N('B', b0 + 2.5, 1.5, r + 7 if r + 7 <= 52 else r - 5, dyn * 0.9, ACC['B'])
        voi = sorted(52 + (p - 52) % 12 for p in pcs[1:] + pcs[:1])[:4]
        pat = [voi[0], voi[1], voi[2], voi[1], voi[-1], voi[1], voi[2]]
        for i, m in enumerate(pat):
            t = b0 + 0.5 * (i + 1)
            if any(b <= t < b + d and min((m - mm) % 12, (mm - m) % 12) == 1 for b, d, mm in mel): continue
            N('T' if m < 58 else 'A', t, 1.5, m, dyn * (0.9 if i % 2 else 1.0), ACC['T'] if m < 58 else ACC['A'])
    def flower_acc(b0, c, dyn=0.42, mel=()):
        pcs = CH[c]; root = pcs[0]
        r = 36 + (root - 36) % 12
        N('B', b0, 4.0, r, dyn * 1.2, ACC['B']); N('B', b0, 4.0, r + 7, dyn * 0.8, ACC['B'])
        tones = sorted({55 + (p - 55) % 12 for p in pcs})
        quart = [m for m in tones if not any(min((m - mm) % 12, (mm - m) % 12) == 1 for _, _, mm in mel if b0 <= _ < b0 + 4)][:3]
        for k, m in enumerate(quart):
            N('A', b0 + 0.08 * k, 2.4, m, dyn * 0.85, ACC['A'])
            N('A', b0 + 2.5 + 0.06 * k, 1.5, m, dyn * 0.55, ACC['A'])
    for name, nb, bpm, rids in PLAN:
        b0 = bar * 4
        for k in range(nb): bar_bpm.append(bpm if not (name == 'flower' and k % 4 == 3) else 54)
        if name == 'intro':
            sections.append(dict(bar=bar, title='Intro — 左手の分散和音', sub='Em7 → Cmaj7 → Am7 → B7 — ピアノだけで静かに始まる'))
            for k in range(nb):
                c = SWEET[k % 4][0]; harm += [c] * 4
                sweet_acc(b0 + 4 * k, c, dyn=0.26 + 0.05 * k)
        elif name in ('sweet', 'flower', 'ritorno'):
            fl = name == 'flower'
            title = {'sweet': ('I. Sweet — 循環和音 Em7 → Cmaj7 → Am7 → B7', '坂本龍一「Sweet Revenge」の曲調で — 08:53・08:09・13:04・11:18 の旋律が 4 小節ずつ'),
                     'flower': ('II. Flower — 五音音階 (ミ・ソ・ラ・シ・レ)', '「Flower is not a Flower」の曲調で — 06:42・11:23・12:46・17:46 の旋律、空虚 5 度と 4 度の和音'),
                     'ritorno': ('IV. Sweet ritorno — 08:53 の旋律が戻る', '2 回目はオクターヴ下を重ねて')}[name]
            sections.append(dict(bar=bar, title=title[0], sub=title[1]))
            for j, rid in enumerate(rids):
                ph, s0 = phrase(rid)
                mel = [(b0 + 16 * j + b, d, m) for b, d, m in to_key(ph, rid, PENTA if fl and rid != '20260928_174654' else EMIN)]
                src = ACC['S']                      # 声の混じらない、ピアノだけの録音の音で
                for i, (b, d, m) in enumerate(mel):
                    lab = '%s の旋律' % HM(rid) if i == 0 else None
                    N('S', b, d, m, 1.0 if not (name == 'ritorno' and j) else 1.1, src, lab)
                    if name == 'ritorno' and j == 1: N('A', b, d, m - 12, 0.7, src)
                print('  %-8s %s  from %.1fs: %s' % (name, rid, s0, ' '.join(name_of(m) for _, _, m in mel)))
                for k in range(4):
                    bb = b0 + 16 * j + 4 * k
                    c = fit_chord(mel, bb, (FLOWER if fl else SWEET)[k]); harm += [c] * 4
                    (flower_acc if fl else sweet_acc)(bb, c, mel=mel)
        elif name == 'canon':
            sections.append(dict(bar=bar, title='III. Fuga dolce — 旋律と、その 1 小節遅れの応え', sub='08:49・08:06・11:21 の旋律に、同じ旋律が 1 小節遅れてオクターヴ下で応える (カノン)'))
            for j, rid in enumerate(rids):
                ph, s0 = phrase(rid)
                mel = [(b0 + 16 * j + b, d, m) for b, d, m in to_key(ph, rid, EMIN)]
                echo = [(b + 4, d, m - 12) for b, d, m in mel if b + 4 < b0 + 16 * j + 16]
                echo = [(b, d, m) for b, d, m in echo if not any(bb <= b < bb + dd and min((m - mm) % 12, (mm - m) % 12) == 1 for bb, dd, mm in mel)]
                src = ACC['S']                      # 声の混じらない、ピアノだけの録音の音で
                for i, (b, d, m) in enumerate(mel): N('S', b, d, m, 1.0, src, '%s の旋律' % HM(rid) if i == 0 else None)
                for i, (b, d, m) in enumerate(echo): N('T', b, d, m, 0.75, src, '応え (1 小節遅れ)' if i == 0 and j == 0 else None)
                print('  %-8s %s  from %.1fs: %s' % (name, rid, s0, ' '.join(name_of(m) for _, _, m in mel)))
                for k in range(4):
                    bb = b0 + 16 * j + 4 * k
                    c = fit_chord(mel + echo, bb, SWEET[k]); harm += [c] * 4
                    pcs = CH[c]; r = 40 + (pcs[0] - 40) % 12
                    N('B', bb, 2.5, r, 0.5, ACC['B']); N('B', bb + 2.5, 1.5, r + 7 if r + 7 <= 52 else r - 5, 0.4, ACC['B'])
                    for q, m in enumerate(sorted(60 + (p - 60) % 12 for p in pcs[1:3])):
                        if not any(b <= bb + 1 < b + d and min((m - mm) % 12, (mm - m) % 12) == 1 for b, d, mm in mel + echo):
                            N('A', bb + 1 + 0.05 * q, 2.0, m, 0.32, ACC['A'])
        elif name == 'coda':
            sections.append(dict(bar=bar, title='Coda (Flower) — Em9 で開いたまま', sub='Cmaj7 → D → Bm7 → Em9 — 06:42 の旋律の頭が五音音階で、最後は Em9 の分散和音'))
            ph, _ = phrase(rids[0]); mel = [(b0 + b, d, m) for b, d, m in to_key(ph, rids[0], PENTA) if b < 6]
            mel.append((b0 + 6, 10.0, 64))
            for i, (b, d, m) in enumerate(mel): N('S', b, d, m, 0.9, ACC['S'], '%s の旋律 (Coda)' % HM(rids[0]) if i == 0 else None)
            for k, c in enumerate(['Cmaj7', 'D', 'Bm7', 'Em9']):
                harm += [c] * 4; flower_acc(b0 + 4 * k, c, dyn=0.4 - 0.04 * k, mel=mel)
            harm += ['Em9'] * 8
            for k, m in enumerate((40, 47, 54, 55, 59, 62, 66)):     # Em9 の分散和音 (ミ 2 から上へ、ファ# 4 まで — ピアノの録音の 1 音から下げすぎないように)
                N('B' if m < 48 else 'T' if m < 57 else 'A', b0 + 16 + 0.5 * k, 8.0 - 0.5 * k, m, 0.55, ACC['B'] if m < 48 else ACC['T'])
        bar += nb
    # 時間: 小節ごとのテンポ (Flower は句の終わりの小節で息をつく、Coda は少しずつゆるめる)
    bt = [0.0]
    for k, bpm in enumerate(bar_bpm):
        if k >= len(bar_bpm) - 6: bpm = 56 - 1.5 * (k - (len(bar_bpm) - 6))
        bt.append(bt[-1] + 4 * 60.0 / bpm)
    def sec(beat):
        i = min(int(beat // 4), len(bt) - 2); return bt[i] + (beat - 4 * i) / 4.0 * (bt[i + 1] - bt[i])
    for x in notes + extras:
        x['t'] = round(sec(x['beat']), 3); x['d'] = round(sec(x['beat'] + x['dbeats']) - x['t'], 3)
    for x in notes:
        if x.get('label'): entries.append(dict(t=x['t'], label=x['label'], v=x['v'], bar=int(x['beat'] // 4) + 1))
    for s in sections: s['t'] = round(bt[s['bar']], 3)
    nb = len(bar_bpm)
    return dict(bpm=66, beats_per_bar=4, nbars=nb, duration=round(bt[-1], 3), bar_times=[round(x, 3) for x in bt], notes=notes, entries=entries,
                sections=sections, harm=harm, extras=extras)

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': list(ACC.values()), 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.42],
    'title': 'Requiem BADA — LXXXVI · Fiore dolce (piano)',
    'subtitle': 'LXXXV から声を消して — ピアノの音だけで (坂本龍一の 2 曲の曲調 × 11 曲の録音の旋律、ホ短調)',
    'legend': [], 'vname': {},
    'footer': ['Intro (分散和音) → I. Sweet (循環和音) → II. Flower (五音音階) → III. Fuga dolce (カノン) → IV. Sweet ritorno → Coda (Em9)',
               '旋律はすべてユーザーの 11 曲の録音から。声は使わず、ピアノだけの 4 本の録音から切り出した音で。'],
}

if __name__ == '__main__':
    d = build(); d['meta'] = META
    # 音源: シンセは「いちばん近い音高の 1 音」を全部の録音から探すので (低い音は 9/28 の歌声の録音から選ばれていた)、
    # ピアノだけの 4 本の録音の 1 音だけを残した音源の表を書き出して、それで鳴らす
    clean = dict(recordings={}, samples=[x for x in BANK['samples'] if x['rid'] in ACC.values()])
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; json.dump(clean, open(bank_out, 'w'), ensure_ascii=False)
    d['meta'] = dict(META, bank=bank_out)
    print('piano samples', len(clean['samples']), 'from', sorted({x['rid'] for x in clean['samples']}))
    for x in d['notes']:
        if x['v'] != 'S': x['dyn'] = round(x['dyn'] * 1.25, 3)      # 伴奏は旋律より約 6 dB 下
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    ms = [x['m'] for x in d['notes']]
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'range', name_of(min(ms)), '..', name_of(max(ms)))
