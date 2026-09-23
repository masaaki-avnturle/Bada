#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""録音から「実録音の音」のサンプラーを作る。
  各録音を打鍵で区切って採譜し (extract_tablet.transcribe)、1 音だけが鳴っている区間を切り出す。
  音高 (pyin の中央値) と倍音の純度 (基音の倍音列に集まるエネルギーの割合) を測り、録音ごと・音高ごとに
  いちばん純度の高い 1 音を残す。あわせて採譜 (和音・最上声) も書き出す。
  使い方: python build_sampler.py <出力フォルダ> <録音1.mp3> <録音2.mp3> ...
  出力: <出力フォルダ>/bank.json, <出力フォルダ>/<録音 id>/<音名>.wav, <出力フォルダ>/<録音 id>.wav (全体, 44.1 kHz mono)
"""
import sys, os, json, re
import numpy as np, soundfile as sf, librosa
import extract_tablet as X

SR = 44100

def purity(clip, f0, sr=SR):
    a = clip[int(0.08 * sr):int(0.5 * sr)]
    if len(a) < 2048: return 0.0
    spec = np.abs(np.fft.rfft(a * np.hanning(len(a)))) ** 2
    fr = np.fft.rfftfreq(len(a), 1 / sr); tot = spec[(fr > 50) & (fr < 8000)].sum() + 1e-12
    harm = sum(spec[(fr > k * f0 * 0.97) & (fr < k * f0 * 1.03)].sum() for k in range(1, 12) if k * f0 < 8000)
    return float(harm / tot)

def main(out, paths):
    os.makedirs(out, exist_ok=True)
    bank = {'recordings': {}, 'samples': []}
    for p in paths:
        rid = re.search(r'(\d{8}_\d{6})', os.path.basename(p)).group(1)
        y = X.decode(p); sf.write(os.path.join(out, rid + '.wav'), y, SR, subtype='PCM_16')
        segs = X.transcribe(y, SR)
        for s in segs: s['ch'] = X.label(s['m'])
        bank['recordings'][rid] = {'file': os.path.join(out, rid + '.wav'), 'dur': round(len(y) / SR, 3), 'segs': segs}
        best = {}
        for s in segs:
            if len(s['m']) != 1 or s['d'] < 0.45: continue
            t0 = max(0, int((s['t'] - 0.01) * SR)); clip = y[t0:t0 + int(min(s['d'], 2.2) * SR)]
            f0, vf, _ = librosa.pyin(clip[:int(0.6 * SR)], fmin=80, fmax=1200, sr=SR, frame_length=2048)
            f0 = f0[vf] if vf is not None else []
            if len(f0) < 5: continue
            midi = float(np.median(librosa.hz_to_midi(f0)))
            if abs(midi - s['m'][0]) > 0.6: continue
            pu = purity(clip, librosa.midi_to_hz(midi))
            k = int(round(midi))
            if pu > 0.45 and (k not in best or pu > best[k][0]): best[k] = (pu, midi, clip)
        os.makedirs(os.path.join(out, rid), exist_ok=True)
        for k, (pu, midi, clip) in sorted(best.items()):
            clip = clip / (np.sqrt((clip[int(0.05 * SR):int(0.5 * SR)] ** 2).mean()) + 1e-9) * 0.1
            fn = os.path.join(out, rid, '%s.wav' % librosa.midi_to_note(k).replace('♯', 's'))
            sf.write(fn, clip.astype(np.float32), SR, subtype='FLOAT')
            bank['samples'].append({'rid': rid, 'midi': round(midi, 3), 'dur': round(len(clip) / SR, 3), 'purity': round(pu, 3), 'file': fn})
        print(rid, '%.0f s' % (len(y) / SR), len(segs), 'segments,', len(best), 'samples:', ' '.join(librosa.midi_to_note(k) for k in sorted(best)))
    json.dump(bank, open(os.path.join(out, 'bank.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
