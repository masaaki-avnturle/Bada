#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取り出した歌声 (extract_voice.py) から、歌声の 1 音のサンプル集を作る (synth.py の sampler_tone で 4 声を歌声で鳴らすため)。
  pyin (10 ms) で音高を追い、±0.3 半音以内に 0.35 秒以上とどまる所を「伸ばした 1 音」として切り出す。
  録音ごと・音高ごとに、いちばん長く (同じなら大きく) 伸ばした 1 音を残す。rid は 'VOX' (歌声だけから選ぶ印)。
  使い方: python voice_bank.py <voice.json> <出力フォルダ> [録音 id ...] [--tag=VOXF]
  出力: <出力フォルダ>/bank.json ({'recordings': 歌声のフレーズ, 'samples': [...]}) と <出力フォルダ>/<id>/<音名>.wav
"""
import sys, os, json
import numpy as np, soundfile as sf, librosa

SR = 44100

def held_notes(v, sr=SR):
    y = librosa.resample(v, orig_sr=sr, target_sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=70, fmax=900, sr=16000, frame_length=1024, hop_length=160)
    m = librosa.hz_to_midi(f0); out = []; k = 0
    while k < len(m):
        if not vf[k]: k += 1; continue
        j = k; ref = m[k]
        while j + 1 < len(m) and vf[j + 1] and abs(m[j + 1] - ref) < 0.3:
            j += 1; ref = np.median(m[k:j + 1])
        if (j - k + 1) * 0.01 >= 0.35: out.append((k * 0.01, (j - k + 1) * 0.01, float(np.median(m[k:j + 1]))))
        k = j + 1
    return out

def main(vjson, out, rids, tag='VOX'):
    V = json.load(open(vjson)); os.makedirs(out, exist_ok=True)
    bank = {'recordings': {}, 'samples': []}
    for rid, r in V.items():
        if rids and rid not in rids: continue
        v, sr = sf.read(r['voice'], dtype='float32')
        best = {}; notes = held_notes(v)
        lo, hi = np.percentile([m for _, _, m in notes], [10, 90]) if notes else (0, 127)
        notes = [x for x in notes if lo - 3 <= x[2] <= hi + 3]       # 音高の取り違え (オクターヴ違い) を除く
        for t, d, midi in notes:
            clip = v[max(0, int((t - 0.03) * sr)):int((t + d) * sr)]
            rms = float(np.sqrt((clip ** 2).mean()))
            key = int(round(midi))
            if key not in best or (d, rms) > best[key][:2]: best[key] = (d, rms, midi, clip)
        os.makedirs(os.path.join(out, rid), exist_ok=True)
        for key, (d, rms, midi, clip) in sorted(best.items()):
            clip = clip / (np.sqrt((clip[:int(0.3 * sr)] ** 2).mean()) + 1e-9) * 0.1
            n = int(0.012 * sr); clip[:n] *= np.linspace(0, 1, n); clip[-n:] *= np.linspace(1, 0, n)
            fn = os.path.join(out, rid, '%s.wav' % librosa.midi_to_note(key).replace('♯', 's'))
            sf.write(fn, clip.astype(np.float32), sr, subtype='FLOAT')
            bank['samples'].append({'rid': tag, 'from': rid, 'midi': round(midi, 3), 'dur': round(len(clip) / sr, 3), 'purity': 1.0, 'file': fn})
        bank['recordings'][rid] = {'file': r['voice'], 'dur': r['dur'], 'phrases': r['phrases'],
                                   'notes': [[round(t, 2), round(d, 2), round(m, 2)] for t, d, m in notes]}   # 伸ばした音 (時刻, 長さ, 音高)
        print(rid, len(best), 'held notes:', ' '.join(librosa.midi_to_note(k) for k in sorted(best)))
    json.dump(bank, open(os.path.join(out, 'bank.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    tag = next((a.split('=', 1)[1] for a in sys.argv[3:] if a.startswith('--tag=')), 'VOX')   # 例: --tag=VOXF (女性的にした歌声)
    main(sys.argv[1], sys.argv[2], [a for a in sys.argv[3:] if not a.startswith('--')], tag)
