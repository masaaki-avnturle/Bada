#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""録音から歌声を取り出す (UVR の MDX-Net ボーカル分離モデル Kim_Vocal_2.onnx を onnxruntime で動かす)。
  モデル: https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/Kim_Vocal_2.onnx
  スペクトログラム (n_fft 7680, hop 1024, 下から 3072 本, 256 フレーム) を 4 チャンネル (左右 × 実部・虚部) で入れ、歌声の
  スペクトログラムを受け取る。区切りの端 (n_fft/2) は捨てて重ねずにつなぐ。
  取り出した歌声から、歌っている区間 (フレーズ) を探し、音高 (pyin) と大きさを測る。
  使い方: python extract_voice.py <model.onnx> <出力フォルダ> <録音...>
  出力: <出力フォルダ>/<id>_voice.wav (歌声, 44.1 kHz mono), <id>_inst.wav (歌声以外), voice.json (フレーズ一覧)
"""
import sys, os, re, json
import numpy as np, soundfile as sf, librosa
import extract_tablet as X

SR = 44100
N_FFT, HOP, DIM_F, DIM_T = 7680, 1024, 3072, 256
CHUNK = HOP * (DIM_T - 1); TRIM = N_FFT // 2; GEN = CHUNK - 2 * TRIM

def decode_stereo(path):
    import subprocess, imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-loglevel', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T.copy()

def separate(sess, y):
    """y: (2, n) → 歌声 (2, n)"""
    n = y.shape[1]; pad = GEN - n % GEN
    mix = np.concatenate([np.zeros((2, TRIM), np.float32), y, np.zeros((2, pad + TRIM), np.float32)], axis=1)
    out = []
    for i in range(0, n + pad, GEN):
        seg = mix[:, i:i + CHUNK]
        S = np.stack([librosa.stft(seg[c], n_fft=N_FFT, hop_length=HOP, window='hann', center=True) for c in range(2)])   # (2, F, T)
        inp = np.stack([S[0].real, S[0].imag, S[1].real, S[1].imag])[:, :DIM_F, :DIM_T][None].astype(np.float32)
        o = sess.run(None, {'input': inp})[0][0]
        F = N_FFT // 2 + 1
        V = np.zeros((2, F, DIM_T), np.complex64)
        V[0, :DIM_F] = o[0] + 1j * o[1]; V[1, :DIM_F] = o[2] + 1j * o[3]
        w = np.stack([librosa.istft(V[c], hop_length=HOP, window='hann', center=True, length=CHUNK) for c in range(2)])
        out.append(w[:, TRIM:TRIM + GEN])
    return np.concatenate(out, axis=1)[:, :n]

def phrases(v, sr=SR):
    """歌っている区間: 歌声の RMS (50 ms) が全体の強い所の 25% を超え、0.35 秒以上の切れ目でつながる、1.2 秒以上の区間"""
    hop = int(0.05 * sr); fr = librosa.util.frame(np.pad(v, (0, hop)), frame_length=2 * hop, hop_length=hop)
    rms = np.sqrt((fr ** 2).mean(axis=0)); ref = np.percentile(rms, 97) + 1e-9
    on = rms > 0.25 * ref; out = []; i = 0
    while i < len(on):
        if not on[i]: i += 1; continue
        j = i
        while j < len(on) and (on[j] or on[j:j + 7].any()): j += 1
        if (j - i) * 0.05 >= 1.2: out.append((i * 0.05, (j - i) * 0.05))
        i = j
    res = []
    for t, d in out:
        seg = v[int(t * sr):int((t + d) * sr)]
        f0, vf, _ = librosa.pyin(seg, fmin=80, fmax=900, sr=sr, frame_length=2048, hop_length=512)
        f0 = f0[vf] if vf is not None else np.array([])
        res.append({'t': round(t, 2), 'd': round(d, 2), 'rms': round(float(np.sqrt((seg ** 2).mean()) / ref), 3),
                    'voiced': round(len(f0) / max(1, len(vf if vf is not None else [])), 2),
                    'midi': round(float(np.median(librosa.hz_to_midi(f0))), 1) if len(f0) > 5 else None})
    return res

def main(model, out, paths):
    import onnxruntime as ort
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
    os.makedirs(out, exist_ok=True)
    jp = os.path.join(out, 'voice.json')
    bank = json.load(open(jp)) if os.path.exists(jp) else {}
    for p in paths:
        m = re.search(r'(\d{4})-?(\d{2})-?(\d{2})[_-](\d{6})', os.path.basename(p))
        rid = '%s%s%s_%s' % m.groups() if m else os.path.splitext(os.path.basename(p))[0]
        y = decode_stereo(p)
        v = separate(sess, y)
        vm, ym = v.mean(axis=0), y.mean(axis=0)
        sf.write(os.path.join(out, rid + '_voice.wav'), vm, SR, subtype='PCM_16')
        sf.write(os.path.join(out, rid + '_inst.wav'), ym - vm, SR, subtype='PCM_16')
        ph = phrases(vm)
        ratio = float(np.sqrt((vm ** 2).mean()) / (np.sqrt((ym ** 2).mean()) + 1e-9))
        bank[rid] = {'src': p, 'dur': round(len(ym) / SR, 2), 'voice_ratio': round(ratio, 3), 'phrases': ph,
                     'voice': os.path.join(out, rid + '_voice.wav'), 'inst': os.path.join(out, rid + '_inst.wav')}
        print(rid, '%.0f s' % (len(ym) / SR), 'voice/mix %.2f' % ratio, len(ph), 'phrases,', sum(x['d'] for x in ph if x['voiced'] > 0.4), 's sung', flush=True)
        json.dump(bank, open(jp, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
