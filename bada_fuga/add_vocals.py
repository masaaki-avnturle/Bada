#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽譜 (score_tabletNN.json) の旋律 (S) に、シンセの歌声で歌詞をのせる。
  lyrics_tablet.py の区間ごとの歌詞を、主題 1 つ分 (block 小節) ずつのフレーズに 1 行ずつ割り当てる。
  1 音に 1 モーラ。モーラが多ければ長い音を半分に割って足し、少なければ音をまたいで母音をのばす (メリスマ)。
  歌はフレーズごとに声域 (ラ3〜ミ5 くらい) に収まるようオクターヴを選ぶ。ピアノの旋律は歌の下で少し控えめに (dyn × 0.78)。
  出力: extras に 'VO'、meta に 'lyrics' (動画に歌詞を出す)、題名に「歌入り」。
  使い方: python add_vocals.py tablet40 score_tablet40.json score_tablet40v.json [voice.npz (その人の声で歌う曲だけ)]
"""
import sys, json
import sing
from lyrics_tablet import LYRICS

def main(key, src, dst, voice_bank=None):
    d = json.load(open(src)); spec = LYRICS[key]
    bar_s = 240.0 / d['bpm']; secs = d['sections']
    S = sorted([n for n in d['notes'] if n['v'] == 'S'], key=lambda n: n['t'])
    vo, lyr_meta = [], []; ph_id = 0; report = []
    for si, sec in enumerate(secs):
        t_a = sec['t']; t_b = secs[si + 1]['t'] if si + 1 < len(secs) else 1e9
        hit = [x for x in spec['sections'] if sec['title'].startswith(x[0])]
        if not hit: continue
        lines = hit[0][1]; block = hit[0][2] if len(hit[0]) > 2 and hit[0][2] else spec['block']
        opt = hit[0][3] if len(hit[0]) > 3 else {}
        boost = opt.get('boost', 1.35 if ('horus' in sec['title'] or sec['title'].startswith(('Sequentia', 'Lux aeterna'))) else 1.0)   # サビは伴奏が厚いので歌を前に
        groups = []                                                         # [(声部, その声部の音)] — 1 つが 1 フレーズ
        if opt.get('entries'):                                              # フーガ: 主題が入るたびに、その声部が block 小節を歌う
            for e in d['entries']:
                if t_a - 1e-6 <= e['t'] < t_b - 1e-6 and e['v'] in opt.get('voices', 'S') and e['label'].startswith(opt.get('prefix', '主題')):
                    ns = sorted([n for n in d['notes'] if n['v'] == e['v'] and e['t'] - 1e-6 <= n['t'] < e['t'] + block * bar_s - 1e-6], key=lambda n: n['t'])
                    if ns: groups.append((e['v'], ns))
        else:
            ns = [n for n in S if t_a - 1e-6 <= n['t'] < t_b - 1e-6]
            blocks = {}
            for n in ns: blocks.setdefault(int((n['t'] - t_a + 1e-6) // (block * bar_s)), []).append(n)
            groups = [('S', blocks[k]) for k in sorted(blocks)]
        for bi, (gv, notes) in enumerate(groups):
            line = lines[bi % len(lines)]; mm = sing.morae(line)
            seq = [[n['t'], n['d'], n['m']] for n in notes]
            while len(seq) < len(mm):                                     # モーラが多い: いちばん長い音を半分に
                j = max(range(len(seq)), key=lambda i: seq[i][1])
                if seq[j][1] < 0.36: break
                t, dd, m = seq[j]; seq[j:j + 1] = [[t, dd / 2, m], [t + dd / 2, dd / 2, m]]
            mm = mm[:len(seq)]
            nm, nn = len(mm), len(seq)
            idx = [min(nm - 1, i * nm // nn) for i in range(nn)]           # 少ない: 均等にメリスマ
            mean = sum(m for _, _, m in seq) / nn; sh = 0
            lo_, hi_ = opt.get('ranges', {}).get(gv, spec.get('range', (57, 72)))   # 声域 (フレーズの平均の音高をこの間に)
            while mean + sh > hi_: sh -= 12
            while mean + sh < lo_: sh += 12
            top = opt.get('top', spec.get('top'))                          # いちばん高い音の上限 (耳に刺さる高さを避ける)
            if top and max(m for _, _, m in seq) + sh > top: sh -= 12
            marks = []
            for i, (t, dd, m) in enumerate(seq):
                first = i == 0 or idx[i] != idx[i - 1]
                lab = mm[idx[i]][2] if first else None
                vo.append({'v': 'VO', 't': round(t, 4), 'd': round(dd * 0.98, 4), 'm': m + sh, 'lyr': lab, 'ph': ph_id,
                           'gain': round(spec.get('gain', 0.3) * boost, 3), 'tim': spec.get('timbre', 'hypno'), 'vopts': spec.get('voice_opts') if i == 0 else None,
                           'pan': opt.get('pans', {}).get(gv, 0.0), 'label': None, 'beat': 0, 'dbeats': 0})
                if first: marks.append([round(t, 3), lab])
            lyr_meta.append([round(seq[0][0] - 0.35, 3), round(seq[-1][0] + seq[-1][1] + 0.25, 3), line, marks])
            for n in notes: n['dyn'] = round(n.get('dyn', 1.0) * 0.78, 4)
            report.append('%-22s %2d 音 / %2d モーラ  %s' % (sec['title'][:22], len(notes), len(sing.morae(line)), line))
            ph_id += 1
    # 行の表示が重ならないよう、次の行の始まりで切る (フーガでは声部が重なるので、始まりの順に並べてから)
    lyr_meta.sort(key=lambda x: x[0])
    for a, b in zip(lyr_meta, lyr_meta[1:]): a[1] = min(a[1], b[0])
    d['extras'] = d.get('extras', []) + vo
    m = d['meta']; m['lyrics'] = lyr_meta
    if spec.get('timbre') == 'user':                                    # その人の声の型 (voice_templates.py の npz)
        assert voice_bank, 'この曲は声の型 (npz) が要る: add_vocals.py key src dst voice.npz'
        m['voice_bank'] = voice_bank
    if spec.get('title_suffix', ' · Vocal'): m['title'] = m['title'] + spec.get('title_suffix', ' · Vocal')
    if spec.get('voice_name'): m.setdefault('vname', {})['VO'] = spec['voice_name']
    if 'VO' not in m.get('legend', []): m['legend'] = m.get('legend', []) + ['VO']
    json.dump(d, open(dst, 'w'), ensure_ascii=False)
    print('\n'.join(report)); print('phrases', ph_id, 'VO notes', len(vo))

if __name__ == '__main__':
    main(*sys.argv[1:5])
