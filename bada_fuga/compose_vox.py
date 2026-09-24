#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Vox (わたしの声のレクイエムとフーガ)
  録音から取り出した作曲者の歌声 (extract_voice.py → voice_bank.py) と、タブレットのピアノ録音 (build_sampler.py) をミックスした、
  洗脳的で、安心感のあるレクイエムとフーガ。♩=60 (安静時の心拍) の柔らかい鼓動が最後まで止まらない。鳴る音はすべて実録音:
    - 歌声のフレーズは録音から取り出したそのまま (必要なら速さを変えずに移調して調をそろえる)
    - 4 声のうち下の 2 声 (テノール・バス) は歌声の 1 音のサンプラー = 作曲者の声の合唱、上の 2 声はピアノ録音の 1 音
    - 持続音・オスティナートはピアノ録音の 1 音、鼓動はピアノ録音の低い打鍵
  Introitus — 歌声だけ (持続音と鼓動の上で)
  Kyrie — 歌声と合唱: 歌声の音に合う和音を 1 小節ごとに選び、合唱が全音符で包む
  Mix — タブレットのピアノ録音の実音に歌声が重なる
  Fuga — 歌声から作った主題の 4 声フーガ (テノールとバスは歌声で歌う)
  Agnus Dei — B-A-D-A を唱え、歌声が重なる
  Lux aeterna — 最後の歌声 → 長調の和音で安らかに
  使い方: python compose_vox.py <piano_bank.json> <voice_bank.json> [score_vox.json]
"""
import sys, json, math, os
import numpy as np
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT          # ピアノ録音 (argv[1])、主題づくり、区間ごとの移調
import compose_tablet2 as T2         # 持続音・オスティナート・鼓動 (post)
import compose_tablet5 as T5         # 実音の区間、フーガの提示

add, REC = CT.add, CT.REC
VB = json.load(open(sys.argv[2]))
BPM = 60; BAR_S = 240.0 / BPM
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = 'ハ 嬰ハ ニ 変ホ ホ ヘ 嬰ヘ ト 変イ イ 変ロ ロ'.split()

def key_of(notes):
    """歌声の伸ばした音の分布 → (短調の主音, 長調なら True)。長調なら平行短調の主音を返す"""
    h = np.zeros(12)
    for t, d, m in notes: h[int(round(m)) % 12] += d
    sc = [(np.corrcoef(np.roll(MIN, k), h)[0, 1], k, False) for k in range(12)] + [(np.corrcoef(np.roll(MAJ, k), h)[0, 1], (k + 9) % 12, True) for k in range(12)]
    return max(sc)[1:]

VOICE = [r for r, x in VB['recordings'].items() if len(x['notes']) >= 20]
ALL_NOTES = [n_ for r in VOICE for n_ in VB['recordings'][r]['notes']]
TONIC, MAJOR = key_of(ALL_NOTES)
SEMIS = ((TONIC - 2 + 6) % 12) - 6                          # ニ短調から
PSHIFT = {}
for r in VOICE:                                              # 各録音の調を全体の調にそろえる (速さを変えない移調、±3 半音まで)
    t_r, _ = key_of(VB['recordings'][r]['notes']); sh = ((TONIC - t_r + 6) % 12) - 6
    PSHIFT[r] = sh if abs(sh) <= 3 else 0
VOX_TOP = float(np.percentile([s['midi'] for s in VB['samples']], 90))
PIANO = 'PIANO'                                              # 上 2 声の印 (finish の後でピアノ録音の id に置き換える)
PIANO_RIDS = sorted(REC)

def hmv(rid): return '%d/%d %s:%s' % (int(rid[4:6]), int(rid[6:8]), rid[9:11], rid[11:13])

def pick_phrases():
    """各録音から、よく歌っている (有声が多い・大きい) 2〜7 秒のフレーズを、時間順に"""
    out = {}
    for r in VOICE:
        ph = [p for p in VB['recordings'][r]['phrases'] if p['voiced'] >= 0.6 and 1.8 <= p['d'] <= 7.5 and p['rms'] >= 0.35]
        ph = sorted(sorted(ph, key=lambda p: -p['rms'] * p['voiced'])[:6], key=lambda p: p['t'])
        out[r] = ph
    return out

def voice_notes(r, p):
    return [(t - p['t'], d, m + PSHIFT[r]) for t, d, m in VB['recordings'][r]['notes'] if p['t'] <= t < p['t'] + p['d']]

def place_voice(P, bar, r, p, gain=0.65, harm=True):
    """歌声のフレーズを bar 小節目から (録音のまま)。伸ばした音は表示用、和声は歌声の音に合わせる。占める小節数を返す"""
    nb = max(1, math.ceil((p['d'] + 0.6) / BAR_S))
    add('REC', bar * BPB, (p['d'] + 0.5) * BPM / 60.0, 0, gain, None, src=VB['recordings'][r]['file'], off=max(0, p['t'] - 0.15), rid=r,
        fin=0.1, fout=0.4, pshift=PSHIFT[r], tag='わたしの歌声 %s' % hmv(r))
    vn = voice_notes(r, p)
    for t, d, m in vn: add('TB', bar * BPB + (t + 0.15) * BPM / 60.0, d * BPM / 60.0, m - SEMIS, 0.0, None)
    if harm:
        for k in range(nb):
            a, z = k * BAR_S, (k + 1) * BAR_S
            w = [(min(z, t + d) - max(a, t), m - SEMIS) for t, d, m in vn if min(z, t + d) > max(a, t)]
            cs = max(CT.CANDS, key=lambda c: sum(x * (1 if int(round(m)) % 12 in chord(c)['pcs'] else -0.9) for x, m in w)) if w else 'Dm'
            for q in range(BPB): P.harm[(bar + k) * BPB + q] = cs
    return nb

def voice_subject(r, p):
    """歌声の伸ばした音 → 8 拍の主題 (ニ短調に移す)。1 つのフレーズで音が 6 つに満たなければ、続くフレーズの音をつなぐ"""
    ph = [x for x in VB['recordings'][r]['phrases'] if x['t'] >= p['t']]
    notes, off = [], 0.0
    for x in ph:
        notes += [(t + off, d, m) for t, d, m in voice_notes(r, x)]; off += x['d']
        if len({int(round(m)) for _, _, m in notes}) >= 4 and len(notes) >= 6: break
    segs = [{'m': [int(round(m))], 'd': max(0.3, d), 't': t, 'ch': 'Dm'} for t, d, m in notes]
    return CT.make_subject(segs, SEMIS, 60)

SUBJ_R = []

def build():
    PH = pick_phrases()
    queue = [(r, p) for r in VOICE for p in PH[r]]
    print('key: %s%s (semis %+d), voice recordings %d, phrases %d, pshift %s' % (NAMES[TONIC], '短調' if not MAJOR else '短調 (歌は平行長調)', SEMIS, len(VOICE), len(queue), PSHIFT))
    NB = lambda x: max(1, math.ceil((x[1]['d'] + 0.6) / BAR_S))
    total = 1 + sum(NB(x) for x in queue[:3]) + sum(NB(queue[i % len(queue)]) for i in range(3, 11)) + 10 + 10 + sum(NB(queue[i % len(queue)]) for i in range(13, 19)) + 8 + NB(queue[-1]) + 4
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.7
    pr = PIANO_RIDS[0]
    choir = {'S': PIANO, 'A': PIANO, 'T': 'VOX', 'B': 'VOX'}
    qi = 0
    def nxt():
        nonlocal qi
        x = queue[qi % len(queue)]; qi += 1; return x
    # ---------------- Introitus: 歌声だけ
    b = 0
    P.section(b, 'Introitus — わたしの声', '取り出した歌声だけが、ピアノ録音の持続音と ♩=60 の柔らかい鼓動の上で歌う — 鼓動は最後まで止まらない')
    s0 = b
    P.set_harms(b, [['Dm']]); b += 1
    for _ in range(3):
        r, p = nxt(); b += place_voice(P, b, r, p, harm=False)
        for k in range(s0 + 1, b): P.set_harms(k, [['Dm']])
    for v in VOICES: P.rest_bars(v, s0, b)
    T2.MANTRA.append((s0, b, pr, ('DN', 'PK')))
    CT.LAYOUT.append((s0, b, SEMIS, choir, {}))
    # ---------------- Kyrie: 歌声と合唱
    s0 = b
    P.section(b, 'Kyrie — 声と合唱', '歌声の音に合う和音を 1 小節ごとに選び、合唱 (テノール・バスは同じ歌声のサンプラー) が全音符で包む')
    for _ in range(8):
        r, p = nxt(); st = b; b += place_voice(P, b, r, p)
        P.hold.update(range(st, b))
    for k in range(s0, b): P.dyn[k] = 0.45
    T2.MANTRA.append((s0, b, pr, ('PK',)))
    CT.LAYOUT.append((s0, b, SEMIS, choir, {}))
    # ---------------- Mix: ピアノ録音の実音に歌声が重なる
    s0 = b; mr = PIANO_RIDS[-1]
    P.section(b, 'Mix — ピアノ録音 %s と声' % hmv(mr), 'タブレットのピアノ録音をループせず実音のまま — その上に歌声が重なる')
    T5.passage(P, mr, b, 10, SEMIS, 10, fin=1.5, fout=3.0, bpm=BPM)
    t = b + 1
    for _ in range(2):                                     # 2 フレーズ (各 3 小節以内なので 10 小節に収まる)
        r, p = nxt(); t += place_voice(P, t, r, p, gain=1.2, harm=False) + 1
    T2.MANTRA.append((s0, b + 10, pr, ('PK',)))
    CT.LAYOUT.append((s0, b + 10, SEMIS, choir, {}))
    b += 10
    # ---------------- Fuga: 歌声から作った主題
    r, p = max(queue, key=lambda x: (len({int(round(m)) for _, _, m in voice_notes(*x)}), len(voice_notes(*x))))
    subj = voice_subject(r, p); T5.SUBJ[r] = (subj, CT.harmonize(subj)); SUBJ_R.append(r)
    s0 = b
    P.section(b, 'Fuga — わたしの声の主題', '歌声 %s から作った主題の 4 声フーガ — テノールとバスは作曲者の歌声で歌う。下でオスティナートと持続音' % hmv(r))
    T5.expo(P, b, r, 'Vox')
    P.set_harms(b + 8, [['Gm', 'Gm', 'A7', 'A7'], ['Dm']]); P.hold.add(b + 9)
    for k in range(10): P.dyn[b + k] = 0.8
    T2.MANTRA.append((b, b + 10, pr, ('DN', 'PK', 'OS')))
    CT.LAYOUT.append((s0, b + 10, SEMIS, choir, {}))
    b += 10
    # ---------------- Sanctus: 歌声のフレーズがオスティナートの上で続く (和声は歌声に合わせる)
    s0 = b
    P.section(b, 'Sanctus — 声とオスティナート', '歌声のフレーズが次々に — 下でピアノ録音の音のオスティナートが同じ形を刻み続け、合唱が歌声の和音を支える')
    for _ in range(6):
        r, p = nxt(); st = b; b += place_voice(P, b, r, p)
        P.hold.update(range(st, b))
    for k in range(s0, b): P.dyn[k] = 0.4
    T2.MANTRA.append((s0, b, pr, ('PK', 'OS')))
    CT.LAYOUT.append((s0, b, SEMIS, choir, {}))
    # ---------------- Agnus Dei: B-A-D-A と歌声
    s0 = b
    P.section(b, 'Agnus Dei — B-A-D-A', 'B-A-D-A を 4 回唱える合唱 (下の声は作曲者の歌声) に、歌声のフレーズが重なる')
    for k in range(4):
        bb = b + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, H.DRONE_BAR, 0, None)
        if k % 2 == 0: add('X', bb * BPB, 8, n('D3'), 0.3)
    t = b + 1
    for _ in range(2):
        r, p = nxt(); t += place_voice(P, t, r, p, gain=1.3, harm=False) + 1
    P.hold.update(range(b, b + 8))
    for k in range(8): P.dyn[b + k] = 0.6
    T2.MANTRA.append((s0, b + 8, pr, ('DN', 'PK')))
    CT.LAYOUT.append((s0, b + 8, SEMIS, choir, {}))
    b += 8
    # ---------------- Lux aeterna: 最後の歌声 → 長調の和音
    s0 = b
    P.section(b, 'Lux aeterna — 安らかに', '最後の歌声が持続音の上で歌い、長調 (ピカルディ) の和音で安らかに消えていく')
    r, p = queue[-1]; nb = place_voice(P, b, r, p, harm=False)
    for v in VOICES: P.rest_bars(v, b, b + nb)
    for k in range(nb): P.set_harms(b + k, [['Dm']])
    T2.MANTRA.append((b, b + nb, pr, ('DN', 'PK')))
    b += nb
    P.set_harms(b, [['D']] * 4); P.hold.update(range(b, b + 4))
    P.place('S', b, mat(('F#5', 12)), 0, None); P.place('A', b, mat(('A4', 12)), 0, None); P.place('T', b, mat(('D4', 12)), 0, None); P.place('B', b, mat(('D3', 12)), 0, None)
    for v in VOICES: P.rest_bars(v, b + 3, b + 4)
    for k in range(4): P.dyn[b + k] = 0.55 - 0.08 * k
    T2.MANTRA.append((b, b + 3, pr, ('PK',)))
    CT.LAYOUT.append((s0, b + 4, SEMIS, choir, {}))
    b += 4
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': None, 'tb_label': '歌声 (伸ばした音)',
    'title': 'Requiem BADA — Vox',
    'subtitle': 'わたしの声のレクイエムとフーガ — 録音から取り出した歌声とピアノ録音のミックス、止まらない柔らかな鼓動 (音はすべて録音から)',
    'footer': ['Introitus (声だけ) → Kyrie (声と合唱) → Mix (ピアノ録音と声) → Fuga (声の主題) → Agnus Dei (B-A-D-A) → Lux aeterna (長調で安らかに)',
               '歌声は MDX-Net (Kim_Vocal_2) で取り出したもの。合唱の下 2 声は歌声の 1 音、上 2 声・持続音・オスティナート・鼓動はピアノ録音の 1 音。'],
}

def merged_bank(path):
    """ピアノ録音のサンプルと歌声のサンプルを 1 つのサンプル集に"""
    pb = json.load(open(sys.argv[1]))
    json.dump({'recordings': {}, 'samples': pb['samples'] + VB['samples']}, open(path, 'w'), ensure_ascii=False)
    return path

def fix_sources(path):
    """上 2 声 → ピアノ録音 (区間ごとに順に)、歌声の音域より上すぎる音 (7 半音超) はピアノ録音で"""
    d = json.load(open(path))
    for nt in d['notes']:
        if nt['src'] == PIANO or (nt['src'] == 'VOX' and nt['m'] > VOX_TOP + 7):
            nt['src'] = PIANO_RIDS[int(nt['beat'] // (BPB * 8)) % len(PIANO_RIDS)]
    json.dump(d, open(path, 'w'), ensure_ascii=False, indent=0)

if __name__ == '__main__':
    out = sys.argv[3] if len(sys.argv) > 3 else 'score_vox.json'
    META['bank'] = merged_bank(os.path.join(os.path.dirname(os.path.abspath(out)), 'bank_vox.json'))
    META['rec_order'] = PIANO_RIDS + ['VOX']
    compose.main(out, seed=61, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=T2.post)
    CT.finish(out); fix_sources(out)
    print('subject', SUBJ_R[0], ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[SUBJ_R[0]][0]))
