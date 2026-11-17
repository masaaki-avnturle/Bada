#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""録音から、半小節 (既定 2 秒) ごとの和音 (長三和音 / 短三和音) を読む — テープだけの曲の和音の表示用。
  クロマ (CQT) を窓ごとに平均し、24 の三和音の型 (根音 1.0、3 度 0.85、5 度 0.9) とのコサイン類似度に、低音 (C1〜B2) の根音の一致を少し足す。
  和音の変わり目に罰を付けて全体でいちばん良い並びを選ぶ (Viterbi)。静かな窓は前の和音を続ける。
  使い方: python analyze_chords.py <出力.json> <録音1.wav> <録音2.wav> ... [--win 2.0]
  出力: {録音 id (拡張子なしのファイル名): {"win": 秒, "chords": ["Dm", "F", ...], "level_db": [...], "env_dt": 0.05, "env": [0〜1 の音量の包絡 (画面の波形用)]}}
"""
import sys, os, json
import numpy as np, soundfile as sf, librosa

NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']

def templates():
    T, names = [], []
    for r in range(12):
        for q, third in (('', 4), ('m', 3)):
            t = np.zeros(12); t[r] = 1.0; t[(r + third) % 12] = 0.85; t[(r + 7) % 12] = 0.9
            T.append(t / np.linalg.norm(t)); names.append(NAMES[r] + q)
    return np.array(T), names

def analyze(path, win=2.0, switch=0.06, bass_w=0.12):
    x, sr0 = sf.read(path, always_2d=True); x = x.mean(axis=1)
    sr = 22050; y = librosa.resample(x.astype(np.float64), orig_sr=sr0, target_sr=sr); hop = 512; fps = sr / hop
    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    Cb = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop, fmin=librosa.note_to_hz('C1'), n_octaves=2)      # 低音だけ
    n = int(np.ceil(len(y) / sr / win)); T, names = templates()
    emis = np.zeros((n, 24)); lev = np.zeros(n)
    for k in range(n):
        a, b = int(k * win * fps), max(int(k * win * fps) + 1, int((k + 1) * win * fps))
        c = C[:, a:b].mean(axis=1); cb = Cb[:, a:b].mean(axis=1)
        seg = y[int(k * win * sr):int((k + 1) * win * sr)]; lev[k] = 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9) if len(seg) else -90.0
        c = c / (np.linalg.norm(c) + 1e-9); cb = cb / (cb.max() + 1e-9)
        emis[k] = T @ c + bass_w * np.array([cb[i // 2] for i in range(24)])
    quiet = lev < (np.percentile(lev, 90) - 30.0)
    # Viterbi: 和音が変わるたびに switch を引く
    score = emis[0].copy(); back = np.zeros((n, 24), dtype=int)
    for k in range(1, n):
        stay = score; best = score.max() - switch; move = int(score.argmax())
        prev = np.where(stay >= best, np.arange(24), move); base = np.maximum(stay, best)
        back[k] = prev; score = base + (0.0 if quiet[k] else 1.0) * emis[k]
    path_ = [int(score.argmax())]
    for k in range(n - 1, 0, -1): path_.append(int(back[k][path_[-1]]))
    path_ = path_[::-1]
    dt = 0.05; m = int(dt * sr0); e = np.sqrt(np.maximum((x[:len(x) // m * m].reshape(-1, m) ** 2).mean(axis=1), 0.0))        # 0.05 秒ごとの rms
    e = np.sqrt(np.minimum(e / (np.percentile(e, 99.5) + 1e-9), 1.0))                                                       # 0〜1 に、静かな所も見えるように平方根
    return {'win': win, 'chords': [names[i] for i in path_], 'level_db': [round(float(v), 1) for v in lev], 'env_dt': dt, 'env': [round(float(v), 3) for v in e]}

if __name__ == '__main__':
    args = sys.argv[1:]; win = 2.0
    if '--win' in args: i = args.index('--win'); win = float(args[i + 1]); del args[i:i + 2]
    out, paths = args[0], args[1:]; res = {}
    for p in paths:
        rid = os.path.splitext(os.path.basename(p))[0]; res[rid] = analyze(p, win)
        ch = res[rid]['chords']; runs = []
        for c in ch:
            if runs and runs[-1][0] == c: runs[-1][1] += 1
            else: runs.append([c, 1])
        print('%s: %d 窓 (%.0f 秒), 和音の変わり目 %d 回' % (rid, len(ch), len(ch) * win, len(runs) - 1))
        print('   ' + ' '.join('%s×%d' % (c, k) if k > 1 else c for c, k in runs))
    json.dump(res, open(out, 'w'), ensure_ascii=False)
