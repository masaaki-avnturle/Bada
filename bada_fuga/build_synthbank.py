#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ピアノとシンセサイザーを重ねた録音から、シンセサイザーの持続音の実音を切り出してサンプラーにする。
  pyin (10 ms) で音高を追い、±0.3 半音以内に min_d 秒以上とどまる「伸ばした音」を探す (ピアノは減衰するので、長く一定に
  伸びているのはシンセ)。打鍵から skip 秒あとから切り出す (ピアノのアタックを避け、シンセの持続部だけを残す)。
  音高ごとにいちばん長いものを残す。rid は 'VOXSY' (synth.sampler_tone がこの印のサンプルだけから選び、減衰させない)。
  使い方: python build_synthbank.py <録音> <出力フォルダ> [min_d=0.6] [skip=0.25]
  出力: <出力フォルダ>/bank.json, <出力フォルダ>/<音名>.wav
"""
import sys, os, json
import numpy as np, soundfile as sf, librosa
import extract_tablet as X
from voice_bank import held_notes

SR = 44100

def main(path, out, min_d=0.6, skip=0.25):
    os.makedirs(out, exist_ok=True)
    y = X.decode(path)
    notes = [(t, d, m) for t, d, m in held_notes(y) if d >= min_d + skip]
    best = {}
    for t, d, m in notes:
        k = int(round(m))
        if k not in best or d > best[k][1]: best[k] = (t, d, m)
    samples = []
    for k, (t, d, m) in sorted(best.items()):
        clip = y[int((t + skip) * SR):int((t + d) * SR)].astype(np.float32)
        clip = clip / (np.sqrt((clip ** 2).mean()) + 1e-9) * 0.1
        n = int(0.06 * SR); clip[:n] *= np.linspace(0, 1, n); clip[-n:] *= np.linspace(1, 0, n)
        fn = os.path.join(out, '%s.wav' % librosa.midi_to_note(k).replace('♯', 's'))
        sf.write(fn, clip, SR, subtype='FLOAT')
        samples.append({'rid': 'VOXSY', 'from': os.path.basename(path), 'midi': round(m, 3), 'dur': round(len(clip) / SR, 3), 'purity': 1.0, 'file': fn})
    json.dump({'recordings': {}, 'samples': samples}, open(os.path.join(out, 'bank.json'), 'w'), ensure_ascii=False, indent=1)
    print(len(samples), 'synth samples:', ' '.join('%s(%.1fs)' % (librosa.midi_to_note(k), best[k][1]) for k in sorted(best)))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.6, float(sys.argv[4]) if len(sys.argv) > 4 else 0.25)
