#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CIX · Canzone tre in uno 08:09 senza sospiri (CII から喘ぎ声を消して — 9/29 の録音の 1 音で)
  曲は CII と同じ (compose_tablet102.build): 表 = 9/23 08:09 の録音 ／ 裏 = 採譜の骨組み + 主題 ソ・ファ#・ソ・シ・ミ の 4 声フーガ + 生誕祭。消したもの:
    - 裏の層のピアノの 1 音: 立ち上がりが遅く減衰せずにふくらむ音 (息のように聞こえる) を clean_bank.py で外した表 (bank109 = bank85p + 9/29 15:12・15:16 の 1 音) で、
      1 音は提出された 9/29 15:16 の録音から切り出したものを優先 (立ち上がりの速い 11 音)
    - 表の録音 (08:09): 息のような音 (1〜4 kHz が平らなノイズになる 0.5 秒、7 か所・計 5 秒) の間だけ 1〜6 kHz を 12 dB 下げる (dip_breath.py)。ほかは加工なし
  使い方: python compose_tablet109.py <bank109.json> <rec0809_clean.wav> [score_tablet109.json]
"""
import sys, json
OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet109.json'
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], OUT, '20260929_151602']
import compose_tablet102 as T102
import compose

if __name__ == '__main__':
    META = dict(T102.META, title='Requiem BADA — CIX · Canzone tre in uno 08:09 senza sospiri',
                subtitle='CII から喘ぎ声を消して — 表: 9/23 08:09 の録音 (息の音だけ下げて) ／ 裏: ふくらむ音を外した 9/29 15:16 のピアノの 1 音で、骨組み + フーガ + 生誕祭 (ホ短調 → ホ長調, ♩=60, 4 分 31 秒)',
                footer=['表: 録音 (実音) が 2 小節目から 3 分 37 秒 ／ 裏: 第 1 部 = 採譜の骨組み (小さく)、第 2 部 = 主題の 4 声フーガ、第 3 部 = 鼓動・祝鐘・マントラ → 録音が終わるとホ長調の生誕祭',
                        '音源は bank109 (立ち上がりが速く減衰する 1 音だけ、9/29 15:16 の音を優先)。録音の息のような所 (7 か所) だけ 1〜6 kHz を下げた。声なし。'])
    compose.main(OUT, seed=102, bpm=T102.BPM, builder=T102.build, meta=META, extras=T102.extras, post=T102.post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
