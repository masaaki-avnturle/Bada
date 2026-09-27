#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽譜 (score_tabletNN.json) の旋律 (S) に、シンセの歌声で歌詞をのせる。
  lyrics_tablet.py の区間ごとの歌詞を、主題 1 つ分 (block 小節) ずつのフレーズに 1 行ずつ割り当てる。
  1 音に 1 モーラ。モーラが多ければ長い音を半分に割って足し、少なければ音をまたいで母音をのばす (メリスマ)。
  歌はフレーズごとに声域 (ラ3〜ミ5 くらい) に収まるようオクターヴを選ぶ。ピアノの旋律は歌の下で少し控えめに (dyn × 0.78)。
  出力: extras に 'VO'、meta に 'lyrics' (動画に歌詞を出す)、題名に「歌入り」。
  使い方: python add_vocals.py tablet40 score_tablet40.json score_tablet40v.json
"""
import sys, json
import sing
from lyrics_tablet import LYRICS

def main(key, src, dst):
    d = json.load(open(src)); spec = LYRICS[key]
    bar_s = 240.0 / d['bpm']; secs = d['sections']
    S = sorted([n for n in d['notes'] if n['v'] == 'S'], key=lambda n: n['t'])
    vo, lyr_meta = [], []; ph_id = 0; report = []
    for si, sec in enumerate(secs):
        t_a = sec['t']; t_b = secs[si + 1]['t'] if si + 1 < len(secs) else 1e9
        hit = [x for x in spec['sections'] if sec['title'].startswith(x[0])]
        if not hit: continue
        lines = hit[0][1]; block = hit[0][2] if len(hit[0]) > 2 else spec['block']
        boost = 1.35 if ('horus' in sec['title'] or sec['title'].startswith(('Sequentia', 'Lux aeterna'))) else 1.0   # サビは伴奏が厚いので歌を前に
        ns = [n for n in S if t_a - 1e-6 <= n['t'] < t_b - 1e-6]
        blocks = {}
        for n in ns: blocks.setdefault(int((n['t'] - t_a + 1e-6) // (block * bar_s)), []).append(n)
        for bi, k in enumerate(sorted(blocks)):
            notes = blocks[k]; line = lines[bi % len(lines)]; mm = sing.morae(line)
            seq = [[n['t'], n['d'], n['m']] for n in notes]
            while len(seq) < len(mm):                                     # モーラが多い: いちばん長い音を半分に
                j = max(range(len(seq)), key=lambda i: seq[i][1])
                if seq[j][1] < 0.36: break
                t, dd, m = seq[j]; seq[j:j + 1] = [[t, dd / 2, m], [t + dd / 2, dd / 2, m]]
            mm = mm[:len(seq)]
            nm, nn = len(mm), len(seq)
            idx = [min(nm - 1, i * nm // nn) for i in range(nn)]           # 少ない: 均等にメリスマ
            mean = sum(m for _, _, m in seq) / nn; sh = 0
            while mean + sh > 72: sh -= 12
            while mean + sh < 57: sh += 12
            marks = []
            for i, (t, dd, m) in enumerate(seq):
                first = i == 0 or idx[i] != idx[i - 1]
                lab = mm[idx[i]][2] if first else None
                vo.append({'v': 'VO', 't': round(t, 4), 'd': round(dd * 0.98, 4), 'm': m + sh, 'lyr': lab, 'ph': ph_id,
                           'gain': round(spec.get('gain', 0.3) * boost, 3), 'label': None, 'beat': 0, 'dbeats': 0})
                if first: marks.append([round(t, 3), lab])
            lyr_meta.append([round(seq[0][0] - 0.35, 3), round(seq[-1][0] + seq[-1][1] + 0.25, 3), line, marks])
            for n in notes: n['dyn'] = round(n.get('dyn', 1.0) * 0.78, 4)
            report.append('%-22s %2d 音 / %2d モーラ  %s' % (sec['title'][:22], len(notes), len(sing.morae(line)), line))
            ph_id += 1
    # 行の表示が重ならないよう、次の行の始まりで切る
    for a, b in zip(lyr_meta, lyr_meta[1:]): a[1] = min(a[1], b[0])
    d['extras'] = d.get('extras', []) + vo
    m = d['meta']; m['lyrics'] = lyr_meta
    m['title'] = m['title'] + ' (歌入り)'
    if 'VO' not in m.get('legend', []): m['legend'] = m.get('legend', []) + ['VO']
    json.dump(d, open(dst, 'w'), ensure_ascii=False)
    print('\n'.join(report)); print('phrases', ph_id, 'VO notes', len(vo))

if __name__ == '__main__':
    main(*sys.argv[1:4])
