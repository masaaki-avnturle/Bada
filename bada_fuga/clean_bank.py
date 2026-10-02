#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音源の表 (bank) から、ピアノの打鍵らしくない 1 音を外す — 喘ぎ声 (息) のように聞こえる音を消すために。
  ピアノの 1 音は、立ち上がりが速く (山まで 0.12 秒以内)、そのあと減衰する (0.1〜0.3 秒 → 0.6〜1.0 秒でふくらまない)。
  立ち上がりが遅い・ふくらむ音 (ペダルの響きや、うなり、声の混じった音) は、synth の持続部のループで伸ばすと息を吸うように聞こえる。
  使い方: python clean_bank.py <bank.json> <出力 bank.json> [attack_max=0.12] [decay_max_dB=-0.1] [--recordings=<採譜をとる bank.json>]
"""
import sys, json, numpy as np, soundfile as sf

def measure(path):
    y, sr = sf.read(path); y = y.mean(1) if y.ndim > 1 else y
    hop = int(0.005 * sr); e = np.array([np.sqrt((y[i:i + hop] ** 2).mean()) for i in range(0, len(y) - hop, hop)])
    atk = int(np.argmax(e)) * 0.005
    a = e[20:60].mean(); b = e[120:200].mean() if len(e) > 200 else e[-10:].mean()
    return atk, float(20 * np.log10(b / (a + 1e-9) + 1e-9))

if __name__ == '__main__':
    recs = [a for a in sys.argv if a.startswith('--recordings=')]; sys.argv = [a for a in sys.argv if not a.startswith('--recordings=')]
    src, out = sys.argv[1], sys.argv[2]
    amax = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12; dmax = float(sys.argv[4]) if len(sys.argv) > 4 else -0.1
    d = json.load(open(src)); keep, drop = [], []
    for s in d['samples']:
        if str(s['rid']).startswith('VOX'): drop.append((s, 'voice')); continue
        atk, dec = measure(s['file'])
        (keep if atk <= amax and dec <= dmax else drop).append((s, 'attack %.2f s, decay %+.1f dB' % (atk, dec)))
    recordings = json.load(open(recs[0][13:]))['recordings'] if recs else d.get('recordings', {})   # 採譜 (旋律を採る) は別の表からも
    json.dump(dict(recordings=recordings, samples=[s for s, _ in keep]), open(out, 'w'), ensure_ascii=False)
    print('kept %d / %d samples' % (len(keep), len(d['samples'])))
    for s, why in drop: print('  drop %s %5.1f  %s' % (s['rid'], s['midi'], why))
    from collections import Counter; print('kept per recording', dict(Counter(s['rid'] for s, _ in keep)))
    print('kept midi', sorted(round(s['midi']) for s, _ in keep))
