#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXVIII · Lento ipnotico (2026-09-25 の 3 本の録音から — レクイエムとフーガが交互に雰囲気を変える)
  録音: 12:46:43 (ヘ短調、途中にシンセサイザーの実音)、12:50:53 (ロ短調)、13:04:31 (変ホ短調、ゆっくり)。
  速さは 13:04 のゆっくりに合わせて ♩=42 (Contrapunctus XIV より遅い)。
  雰囲気が交互に変わる:
    Requiem — 実音の抜粋 (録音そのもの) の下で、12:46 の途中から切り出したシンセの持続音 (実音、rid 'VOXSY') が
              録音の和音を 1 小節ずつ静かに支える。鼓動 (ピアノの低い打鍵) は最後まで止まらない。
    Fuga    — その録音の主題を、録音から切り出したピアノの 1 音で 4 声のフーガに。主題の入りにはシンセの実音が 1 オクターヴ上で重なる。
  形式 (Contrapunctus XIV のように 3 つの主題を順に出して最後に重ねる):
    Requiem I 13:04 → Fuga I (13:04 の主題) → Requiem II 12:46 (シンセの部分) → Fuga II (12:46 + 13:04 の二重)
    → Requiem III 12:50 → Fuga III (3 つの主題の三重フーガ、ストレッタ) → Requiem finale: 13:04 の本当の終わり + シンセの和音
  洗脳的: ♩=42 の止まらない鼓動、減衰しないシンセの持続音、同じ主題の重なり。
  使い方: python compose_tablet28.py <bank26.json (9/25 の採譜・1 音・シンセ)> [score_tablet28.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 42; BAR_S = 240.0 / BPM
R1, R2, R3 = '20260925_124643', '20260925_125053', '20260925_130431'       # 12:46 (ヘ短調, シンセ), 12:50 (ロ短調), 13:04 (変ホ短調, ゆっくり)
KEYS = {R1: 3, R2: -3, R3: 1}
T7.KEYS.update(KEYS); T7.MARK.update({R3: '①', R1: '②', R2: '③'})
ORDER = [R3, R1, R2]
SYN = 'VOXSY'
VOICE_SRC = {'S': R3, 'A': R1, 'T': R2, 'B': R3}
octs, TOP = T7.octs, T7.TOP

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:                                     # 鼓動 (ピアノの低い打鍵、pp)
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=rid)
    for b0, b1, gain in PAD:                                                 # シンセの実音が和音を 1 小節ずつ支える
        for bar in range(b0, b1):
            ch = chord(P.harm[bar * BPB]); root = ch['root']
            for j, m in enumerate((38 + (root - 2) % 12, 45 + (root - 2) % 12, 50 + (root - 2) % 12 + (ch['third'] - root) % 12)):
                add('SP', bar * BPB + 0.02 * j, BPB + 0.5, m, gain * (1.0 if j else 1.2), None, rid=SYN, pan=(-0.2, 0.2, 0.0)[j])

PAD = []

def requiem(P, b, rid, bars, t0=None, fin=1.5, fout=3.0, gmul=0.6, pad=0.16):
    T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=fin, fout=fout, t0=t0, bpm=BPM, gmul=gmul)
    for v in VOICES: P.rest_bars(v, b, b + bars)
    for k in range(bars): P.dyn[b + k] = 0.5
    PAD.append((b, b + bars, pad))
    T2.MANTRA.append((b, b + bars, rid, ('PK',))); CT.LAYOUT.append((b, b + bars, KEYS[rid], {v: rid for v in VOICES}, {}))
    return bars

def entry(P, bar, v, rid, entries, labmap, beat=0, tr0=0, synth=True):
    subj = T5.SUBJ[rid][0]; tr = octs[v] + tr0
    if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
    if max(m for _, m in subj) + tr > TOP[v]: tr -= 12
    lab = '主題 %s' % T7.MARK[rid]; labmap[lab] = rid
    P.place(v, bar, subj, tr, lab, beat=beat); entries.append((bar * BPB + beat, [(d, m + tr) for d, m in subj]))
    if synth:
        t = bar * BPB + beat
        for d, m in subj: add('SP', t, d * 0.95, m + tr + (12 if v in 'TB' else 0), 0.11, None, rid=SYN, pan=0.15 if v in 'SA' else -0.15); t += d

def fuga(P, b, plan, bars, semis, rid_key, dyn=1.25):
    """plan: (bar, beat, voice, rid) の入り。各声部は最初の入りまで休む"""
    entries, labmap = [], {}
    first = {}
    for bar, beat, v, rid in plan:
        entry(P, b + bar, v, rid, entries, labmap, beat=beat); first.setdefault(v, (bar, beat))
    for v in VOICES:
        if v in first:
            bar, beat = first[v]; P.rest_bars(v, b, b + bar)
            if beat: P.rest_bars(v, b + bar, b + bar + 1, beats=range(int(beat)))
        else: P.rest_bars(v, b, b + bars)
    T5.harm_from_entries(P, b, b + bars, entries)
    for k in range(bars): P.dyn[b + k] = dyn
    T2.MANTRA.append((b, b + bars, rid_key, ('PK',))); CT.LAYOUT.append((b, b + bars, semis, VOICE_SRC, labmap))
    return bars

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 16.0)
        subj = CT.make_subject(inside, KEYS[r], BPM); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    end3 = REC[R3]['dur'] - 6 * BAR_S - 0.5
    T5.USED.setdefault(R3, []).append((end3, REC[R3]['dur']))
    total = 6 + 8 + 6 + 8 + 6 + 10 + 6 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    P.section(b, 'Requiem I — %s の実音 (変ホ短調)' % hm(R3), 'いちばんゆっくりの録音 — その和音を 12:46 のシンセの実音が 1 小節ずつ支える。♩=42 の鼓動が最後まで止まらない')
    b += requiem(P, b, R3, 6)
    P.section(b, 'Fuga I — 〈%s〉 の主題 (変ホ短調)' % hm(R3), '13:04 の主題の 4 声の提示 (2 小節ごとにオクターヴで) → ストレッタ — 主題の入りにシンセの実音が重なる')
    b += fuga(P, b, ((0, 0, 'A', R3), (2, 0, 'S', R3), (4, 0, 'T', R3), (6, 0, 'B', R3), (7, 0, 'S', R3)), 8, KEYS[R3], R3)
    P.section(b, 'Requiem II — %s の実音、シンセの部分 (ヘ短調)' % hm(R1), '12:46 の途中、シンセサイザーが鳴っている実音 — そのシンセから切り出した持続音が和音を支える')
    b += requiem(P, b, R1, 6, t0=84.0)
    P.section(b, 'Fuga II — 〈%s · %s〉 の二重フーガ (ヘ短調)' % (hm(R1), hm(R3)), '12:46 の主題と 13:04 の主題が重なる')
    b += fuga(P, b, ((0, 0, 'A', R1), (2, 0, 'S', R3), (4, 0, 'T', R1), (6, 0, 'B', R3), (6, 0, 'S', R1)), 8, KEYS[R1], R1)
    P.section(b, 'Requiem III — %s の実音 (ロ短調)' % hm(R2), '12:50 の実音 — シンセの和音と鼓動')
    b += requiem(P, b, R2, 6)
    P.section(b, 'Fuga III — 三重フーガ 〈%s · %s · %s〉 (ロ短調)' % (hm(R3), hm(R1), hm(R2)), '12:50 の主題の提示 → 3 つの主題が同時に重なる (Contrapunctus XIV のように) → ストレッタ')
    b += fuga(P, b, ((0, 0, 'T', R2), (2, 0, 'A', R2), (4, 0, 'S', R3), (4, 0, 'T', R1), (4, 0, 'B', R2), (6, 0, 'A', R2), (6, 0, 'S', R1), (7, 2, 'T', R3), (8, 0, 'B', R3), (8, 0, 'S', R2), (8, 2, 'A', R1)), 10, KEYS[R2], R2, dyn=1.3)
    P.section(b, 'Requiem finale — %s の本当の終わり (変ホ短調)' % hm(R3), '13:04 の最後の 34 秒 → シンセの実音の和音が残り、鼓動とともに消える')
    b += requiem(P, b, R3, 6, t0=end3, fin=1.0, fout=2.5, gmul=0.65)
    P.set_harms(b, [['Dm']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    for k, m in enumerate((38, 45, 50, 53, 57, 62)): add('SP', b * BPB + 0.3 * k, 7.0, m, 0.14, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15, 0.0, 0.1)[k])
    T2.MANTRA.append((b, b + 2, R3, ('PK',))); CT.LAYOUT.append((b, b + 2, KEYS[R3], VOICE_SRC, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER + [SYN], 'piano_decay': 1.5, 'src_name': {SYN: '12:46 のシンセ (実音)'},
    'title': 'Requiem BADA — Tablet Sessions XXVIII · Lento ipnotico',
    'subtitle': '9/25 の 3 本 (12:46・12:50・13:04) — レクイエムとフーガが交互に、13:04 のゆっくりで (♩=42)、12:46 のシンセの実音',
    'legend': ['TB', 'SP', 'PK'], 'vname': {'SP': '12:46 のシンセ (実音)', 'PK': '鼓動'},
    'footer': ['Requiem I 13:04 → Fuga I → Requiem II 12:46 (シンセ) → Fuga II (二重) → Requiem III 12:50 → Fuga III (三重) → Requiem finale 13:04 の終わり',
               '実音の抜粋の下でシンセの実音が和音を支え、フーガは録音から切り出したピアノの 1 音、主題の入りにシンセが重なる。鼓動は最後まで。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet28.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d_) for d_, m in T5.SUBJ[r][0]))
