#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""タブレット録音 (20260922_090933 / 090146) から抜粋を切り出し、和音を採譜する。
  出力: samples/tablet_<id>.flac (44.1 kHz mono) と samples/tablet_segments.json
  使い方: python extract_tablet.py <090933.mp3> <090146.mp3>
"""
import sys, os, json, subprocess
import numpy as np, librosa, soundfile as sf

# (録音 id, 抜粋の開始秒, 終了秒, 最初の和音の打鍵時刻) — いずれもホ短調圏の部分
EXCERPTS = [('090933', 30.62, 59.69, 30.82), ('090146', 407.96, 455.47, 408.16)]
SR = 44100; HOP = 256

def decode(path):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = subprocess.run([ff, '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def transcribe(y, sr):
    """打鍵 (CQT のスペクトル・フラックス) で区切り、各区間の持続音の音高を拾う。"""
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=HOP, fmin=librosa.note_to_hz('C2'), n_bins=72))
    Cdb = librosa.amplitude_to_db(C, ref=np.max)
    flux = np.r_[0, np.maximum(0, np.diff(Cdb, axis=1)).sum(axis=0)]
    on = librosa.onset.onset_detect(onset_envelope=librosa.util.normalize(flux), sr=sr, hop_length=HOP, delta=0.12, wait=int(0.25 * sr / HOP))
    on = np.r_[0, on, C.shape[1]]
    floor = np.percentile(C, 60); segs = []
    for a, b in zip(on[:-1], on[1:]):
        if b - a < int(0.2 * sr / HOP): continue
        spec = C[:, a + int(0.06 * sr / HOP):b].mean(axis=1)
        if spec.max() < floor: continue
        db = librosa.amplitude_to_db(spec, ref=spec.max())
        peaks = [i for i in range(1, 71) if db[i] > -18 and db[i] >= db[i - 1] and db[i] >= db[i + 1]]
        keep = []
        for i in sorted(peaks, key=lambda i: -db[i]):          # 倍音 (オクターヴ・12度・2 オクターヴ上) を除く
            if any(i - k in (12, 19, 24, 28, 31) and db[k] > db[i] - 3 for k in keep): continue
            keep.append(i)
        keep = sorted(keep)[:6]
        if keep: segs.append({'t': round(a * HOP / sr, 3), 'd': round((b - a) * HOP / sr, 3), 'm': [36 + i for i in keep]})
    return segs

def label(midis):
    names = 'C C# D D# E F F# G G# A A# B'.split(); w = np.zeros(12)
    for m in midis: w[m % 12] += 1
    best = None
    for r in range(12):
        for q, iv in (('', (0, 4, 7)), ('m', (0, 3, 7)), ('7', (0, 4, 7, 10)), ('m7', (0, 3, 7, 10)), ('maj7', (0, 4, 7, 11)), ('sus4', (0, 5, 7))):
            tpl = np.zeros(12); tpl[[(r + i) % 12 for i in iv]] = 1
            s = (w * tpl).sum() - 0.5 * (w * (1 - tpl)).sum() - 0.08 * len(iv) + (0.15 if r == midis[0] % 12 else 0)
            if best is None or s > best[0]: best = (s, names[r] + q)
    return best[1]

def main(p933, p146):
    os.makedirs('samples', exist_ok=True)
    src = {'090933': p933, '090146': p146}; out = {}
    for rid, t0, t1, first in EXCERPTS:
        y = decode(src[rid])[int(t0 * SR):int(t1 * SR)]
        fn = 'samples/tablet_%s.flac' % rid
        sf.write(fn, y, SR, subtype='PCM_16')
        segs = transcribe(y, SR)
        for s in segs: s['ch'] = label(s['m'])
        out[rid] = {'file': fn, 'src_t0': t0, 'first': round(first - t0, 3), 'dur': round(len(y) / SR, 3), 'segs': segs}
        print(rid, fn, '%.1fs' % (len(y) / SR), len(segs), 'segments')
        for s in segs: print('  %6.2f %5.2f %-6s %s' % (s['t'], s['d'], s['ch'], ' '.join(librosa.midi_to_note(m) for m in s['m'])))
    json.dump(out, open('samples/tablet_segments.json', 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(*sys.argv[1:3])
