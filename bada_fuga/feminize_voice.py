#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取り出した歌声 (extract_voice.py) を、大げさにせず女性的な声にし、きれいに整える (WORLD ボコーダー = pyworld)。
  - 音高: f0 を semis 半音上げる (既定 12 = 1 オクターヴ)。声の響き (フォルマント) は formant 倍だけ上げる (既定 1.12、控えめ)
  - 音程の補正: 伸ばした音だけ、音階の最も近い音へ 60% だけ寄せる (揺れや滑らかな移り変わりは残す)
  - 息・雑音: 歌っていない所を柔らかく閉じる (ゲート)。エコー (残響) は足さない
  使い方: python feminize_voice.py <voice.json> <出力フォルダ> <音階の主音 (0=C … 9=A)> [semis] [formant] -- <録音 id ...>
  出力: <出力フォルダ>/<id>_fem.wav と <出力フォルダ>/voice.json (extract_voice.py と同じ形 → voice_bank.py にそのまま渡せる)
"""
import sys, os, json
import numpy as np, soundfile as sf, pyworld as pw

SR = 44100
MAJOR = [0, 2, 4, 5, 7, 9, 11]

def feminize(x, sr, tonic_major, semis=12.0, formant=1.12, correct=0.6):
    x = x.astype(np.float64)
    f0, t = pw.dio(x, sr, f0_floor=60, f0_ceil=900, frame_period=5.0)
    f0 = pw.stonemask(x, f0, t, sr)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0
    m = np.where(v, 69 + 12 * np.log2(np.maximum(f0, 1) / 440.0), 0)
    # 伸ばした音 (前後 40 ms で 0.4 半音以内) だけ音階へ寄せる
    scale = np.array([(tonic_major + k) % 12 for k in MAJOR])
    target = np.round(m)
    for i in np.where(v)[0]:
        c = int(round(m[i])); cand = [c + d for d in (-1, 0, 1) if (c + d) % 12 in scale]
        target[i] = min(cand, key=lambda q: abs(q - m[i])) if cand else m[i]
    steady = np.zeros_like(v)
    for i in np.where(v)[0]:
        a, b = max(0, i - 8), min(len(m), i + 9)
        w = m[a:b][v[a:b]]
        steady[i] = len(w) >= 12 and np.ptp(w) < 0.4
    corr = np.where(v & steady, (target - m) * correct, 0.0)
    k = np.ones(15) / 15; corr = np.convolve(corr, k, mode='same')                  # 補正は 75 ms でなめらかに
    f0n = np.where(v, 440.0 * 2 ** ((m + corr + semis - 69) / 12.0), 0.0)
    # フォルマント: 周波数軸を formant 倍に伸ばす (sp_new(f) = sp(f / formant))
    nb = sp.shape[1]; fr = np.arange(nb); src = np.clip(fr / formant, 0, nb - 1)
    lo = np.floor(src).astype(int); hi = np.minimum(lo + 1, nb - 1); w = src - lo
    spn = sp[:, lo] * (1 - w) + sp[:, hi] * w
    y = pw.synthesize(f0n, np.ascontiguousarray(spn), ap, sr, frame_period=5.0)
    # ゲート: 50 ms の RMS が強い所の 8% を下回る所を柔らかく閉じる
    hop = int(0.05 * sr); n = len(y) // hop
    rms = np.array([np.sqrt((y[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
    g = (rms > 0.08 * np.percentile(rms, 97)).astype(float)
    g = np.convolve(g, np.ones(5) / 5, mode='same')
    gain = np.interp(np.arange(len(y)), (np.arange(n) + 0.5) * hop, g)
    return (y * gain).astype(np.float32)

def main(vjson, out, tonic, semis, formant, rids):
    V = json.load(open(vjson)); os.makedirs(out, exist_ok=True); res = {}
    for rid in rids:
        x, sr = sf.read(V[rid]['voice'], dtype='float32')
        y = feminize(x, sr, tonic, semis, formant)
        fn = os.path.join(out, rid + '_fem.wav'); sf.write(fn, y, sr, subtype='PCM_16')
        res[rid] = dict(V[rid], voice=fn)
        print(rid, 'feminized', '%.0f s' % (len(y) / sr), flush=True)
    json.dump(res, open(os.path.join(out, 'voice.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    a = sys.argv[1:]; i = a.index('--')
    opts = a[:i]; rids = a[i + 1:]
    main(opts[0], opts[1], int(opts[2]), float(opts[3]) if len(opts) > 3 else 12.0, float(opts[4]) if len(opts) > 4 else 1.12, rids)
