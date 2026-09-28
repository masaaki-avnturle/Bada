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
    vo, lyr_meta = [], []; ph_id = 0; report = []; quieted = set()
    for si, sec in enumerate(secs):
        t_a = sec['t']; t_b = secs[si + 1]['t'] if si + 1 < len(secs) else 1e9
        hit = [x for x in spec['sections'] if sec['title'].startswith(x[0])]
        if not hit: continue
        lines = hit[0][1]; block = hit[0][2] if len(hit[0]) > 2 and hit[0][2] else spec['block']
        opt = hit[0][3] if len(hit[0]) > 3 else {}
        boost = opt.get('boost', 1.35 if ('horus' in sec['title'] or sec['title'].startswith(('Sequentia', 'Lux aeterna'))) else 1.0)   # サビは伴奏が厚いので歌を前に
        groups = []                                                         # [(歌い手, 声部, その声部の音, 歌詞の行の番号)] — 1 つが 1 フレーズ
        if opt.get('entries'):                                              # フーガ: 主題が入るたびに、その声部が block 小節を歌う
            for e in d['entries']:
                if t_a - 1e-6 <= e['t'] < t_b - 1e-6 and e['v'] in opt.get('voices', 'S') and e['label'].startswith(opt.get('prefix', '主題')):
                    ns = sorted([n for n in d['notes'] if n['v'] == e['v'] and e['t'] - 1e-6 <= n['t'] < e['t'] + block * bar_s - 1e-6], key=lambda n: n['t'])
                    if ns: groups.append((e['v'], e['v'], ns, len(groups)))
        else:                                                               # block 小節ずつ (声部が複数なら同じ行を同時に = 和声で歌う)
            for v in opt.get('voices', 'S'):
                ns = S if v == 'S' else sorted([n for n in d['notes'] if n['v'] == v], key=lambda n: n['t'])
                blocks = {}
                for n in ns:
                    if t_a - 1e-6 <= n['t'] < t_b - 1e-6: blocks.setdefault(int((n['t'] - t_a + 1e-6) // (block * bar_s)), []).append(n)
                groups += [(v, v, blocks[k], k) for k in sorted(blocks)]
        base = list(groups)
        for x in opt.get('extra', []):                                      # 同じ旋律をもう 1 人が重ねる (例: バリトンがテノールの 1 オクターヴ下)
            groups += [(x['name'], gv, ns, li) for (sg, gv, ns, li) in base if gv == x['src']]
        for bi, (singer, gv, notes, li) in enumerate(groups):
            line = lines[li % len(lines)]
            if isinstance(line, (tuple, list)):                               # 英語: (表示の行, 発音) → 音節 (表示, 頭子音, 母音, 末尾子音)
                en = sing.en_line(*line); mm = [(None, None, s_[0], s_[1:]) for s_ in en]; line = line[0].replace('-', '')
            else:
                mm = sing.morae(line)
            seq = [[n['t'], n['d'], n['m']] for n in notes]
            while len(seq) < len(mm):                                     # モーラが多い: いちばん長い音を半分に
                j = max(range(len(seq)), key=lambda i: seq[i][1])
                if seq[j][1] < 0.36: break
                t, dd, m = seq[j]; seq[j:j + 1] = [[t, dd / 2, m], [t + dd / 2, dd / 2, m]]
            mm = mm[:len(seq)]
            nm, nn = len(mm), len(seq)
            idx = [min(nm - 1, i * nm // nn) for i in range(nn)]           # 少ない: 均等にメリスマ
            mean = sum(m for _, _, m in seq) / nn; sh = 0
            lo_, hi_ = opt.get('ranges', {}).get(singer, spec.get('range', (57, 72)))   # 声域 (フレーズの平均の音高をこの間に)
            while mean + sh > hi_: sh -= 12
            while mean + sh < lo_: sh += 12
            top = opt.get('top', spec.get('top'))                          # いちばん高い音の上限 (耳に刺さる高さを避ける)
            if top and max(m for _, _, m in seq) + sh > top: sh -= 12
            marks = []
            for i, (t, dd, m) in enumerate(seq):
                first = i == 0 or idx[i] != idx[i - 1]
                last = i == nn - 1 or idx[i + 1] != idx[i]
                lab = mm[idx[i]][2] if first else None
                e_ = {'v': 'VO', 't': round(t, 4), 'd': round(dd * 0.98, 4), 'm': m + sh, 'lyr': lab, 'ph': ph_id,
                      'gain': round(spec.get('gain', 0.3) * boost * opt.get('gains', {}).get(singer, 1.0), 3), 'tim': spec.get('timbre', 'hypno'),
                      'vopts': opt.get('vopts', {}).get(singer, spec.get('voice_opts')) if i == 0 else None,
                      'pan': opt.get('pans', {}).get(singer, 0.0), 'singer': singer, 'label': None, 'beat': 0, 'dbeats': 0}
                if mm[idx[i]][0] is None:                                     # 英語の音節
                    on, nu, co = mm[idx[i]][3]
                    if first: e_['en'] = {'on': on, 'nu': nu, 'co': co}; e_['last'] = last
                    elif last and co: e_['coda'] = co
                vo.append(e_)
                if first: marks.append([round(t, 3), lab])
            lyr_meta.append([round(seq[0][0] - 0.35, 3), round(seq[-1][0] + seq[-1][1] + 0.25, 3), line, marks])
            for n in notes:
                if id(n) not in quieted: n['dyn'] = round(n.get('dyn', 1.0) * 0.78, 4); quieted.add(id(n))   # ピアノ / オルガンの旋律は歌の下で控えめに (1 度だけ)
            report.append('%-22s %-4s %2d 音 / %2d 音節  %s' % (sec['title'][:22], singer, len(notes), nm, line))
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
    if spec.get('title'): m['title'] = spec['title']                          # 題名・副題をまるごと差し替える (長すぎるとき)
    if spec.get('subtitle'): m['subtitle'] = spec['subtitle']
    if spec.get('voice_name'): m.setdefault('vname', {})['VO'] = spec['voice_name']
    if 'VO' not in m.get('legend', []): m['legend'] = m.get('legend', []) + ['VO']
    json.dump(d, open(dst, 'w'), ensure_ascii=False)
    print('\n'.join(report)); print('phrases', ph_id, 'VO notes', len(vo))

if __name__ == '__main__':
    main(*sys.argv[1:5])
