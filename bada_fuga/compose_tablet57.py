#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LVII · Klavier & Taiko III (太鼓が実音のピアノの旋律に合わせて打つ)
  楽譜と実音のピアノの 4 声は LV・LVI とまったく同じ。シンセの音はなし (太鼓は和太鼓の鳴り方をまねた acoustic_drum)。
  太鼓の打ち方: 決まった型ではなく、その時に旋律を受け持っている声部の音の頭で打つ —
    フーガ (Fuga I・II) は今いちばん新しい主題の入りの声部 (次の入りまで、長くても 2 小節)、Klang・Kyrie (コラール)・Amen はソプラノ。
    1 拍以上の長い音は大太鼓を長く響かせ (「どー」)、短い音は長胴太鼓を手で押さえて短く (「ど」)。主題の頭の音は少し強く。
    太鼓の音高はその時の和音の根音に張る (ティンパニのように、ピアノの和音と濁らない): 大太鼓はレ#1〜レ 2、長胴太鼓はド 2〜シ 2。
  Introitus (08:49 の録音) は太鼓なし。
  使い方: python compose_tablet57.py <bank37.json> [score_tablet57.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet53 as T                       # LIII: XLVIII の楽譜と、弦・シンセを鳴らさない設定 (実音のピアノの 4 声)
import compose_tablet55 as LV

K = T.K
add = CT.add
FOLLOW = []                                        # (小節 b0, b1, 大きさ, 'entries' = 主題の入りを追う / 'S' = ソプラノ)

def melody_line(P, events, b0, b1, mode):
    """区間の「旋律」: 音の (拍, 長さ, 音高, 主題の頭か) の列"""
    lo, hi = b0 * BPB, b1 * BPB
    if mode == 'S':
        return [(s_, d, m, False) for s_, d, m, lab in events['S'] if lo - 1e-6 <= s_ < hi - 1e-6]
    ents = sorted(e for e in P.entries if lo - 1e-6 <= e[0] < hi - 1e-6 and e[1] and e[1].startswith('主題'))
    line = []
    for k, (eb, lab, v) in enumerate(ents):
        end = min(ents[k + 1][0] if k + 1 < len(ents) else hi, eb + 2 * BPB)
        ns = [(s_, d, m) for s_, d, m, l in events[v] if eb - 1e-6 <= s_ < end - 1e-6]
        line += [(s_, d, m, i == 0) for i, (s_, d, m) in enumerate(ns)]
    return line

def post(P, events, extras):
    for b0, b1, lvl, mode in FOLLOW:
        for s_, d, m, head in melody_line(P, events, b0, b1, mode):
            root = chord(P.harm[min(P.N - 1, int(s_))])['root']
            g = lvl * (1.15 if head else 1.0)
            if d >= 1.0 - 1e-6:                    # 長い音: 大太鼓を長く (どー)
                add('AD', s_, d, 27 + (root - 27) % 12, g, None, kind='odaiko', tuned=True)
            else:                                  # 短い音: 長胴太鼓を短く (ど)
                add('AD', s_, d, 36 + (root - 36) % 12, g * 0.85, None, kind='nagado', tuned=True, damp=max(0.18, min(0.35, d * 60.0 / K.BPM)))

def build():
    P = K.build()
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    FOLLOW.extend([(4, 6, 0.16, 'S'), (6, 22, 0.14, 'entries'), (22, 30, 0.1, 'S'), (30, 32, 0.16, 'S'), (32, 48, 0.14, 'entries'), (48, 51, 0.13, 'S')])
    return P

META = dict(LV.META,
    title='Requiem BADA — LVII · Klavier & Taiko III',
    subtitle='太鼓が実音のピアノの旋律に合わせて打つ — 長い音は大太鼓「どー」、短い音は長胴太鼓「ど」(♩=56)',
    footer=['Introitus 08:49 → Klang I → Fuga I (主題の入りに合わせて) → Kyrie (ソプラノに合わせて) → Klang II → Fuga II → Amen (ヘ長調)',
            '4 声は録音から切り出したピアノの実音。太鼓は旋律の音の頭で打ち、音高は和音の根音に張る (和太鼓の鳴り方をまねたもの)。シンセなし。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet57.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LVI と同じ)
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入り、太鼓がその旋律に合わせて打つ'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノが長調の和音で包む'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), Counter(e.get('kind') for e in d['extras'] if e['v'] == 'AD'))
