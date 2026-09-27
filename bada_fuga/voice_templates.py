#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
話し声の録音から、その人の声の「母音ごとの響き」を取り出す (sing_user.py で歌わせるため)。
  WORLD (pyworld) で 5 ms ごとに f0・スペクトル包絡・非周期成分を分析し、有声のフレームの第 1・第 2 フォルマントを LPC で測る。
  話者ごとに正規化 (Lobanov の z 得点) して日本語の母音 (あ・い・う・え・お) の型にいちばん近いものに分け、
  はっきり分かれて安定しているフレームだけで、母音ごとのスペクトル包絡 (対数の中央値) と非周期成分を作る。
  無声の子音 (s / sh) も、高い帯域にノイズが集まるフレームから同じように取る。
  使い方: python voice_templates.py <voice.wav> <out.npz>
  出力: npz (sp_a … sp_o, sp_s, sp_sh, ap_v, f0_med, fft_size, counts)。録音から作ったデータなのでリポジトリには入れない。
"""
import sys, numpy as np, soundfile as sf, pyworld as pw, librosa

SR = 44100; FP = 5.0
# 日本語の母音のフォルマント (男声の目安) と、その平均・ばらつき (z 得点を作るため)
TMPL = {'a': (750, 1200), 'i': (300, 2200), 'u': (350, 1350), 'e': (480, 1900), 'o': (500, 850)}

def formants(x, sr):
    """25 ms の窓ごとに LPC (11 kHz, 次数 12) で F1・F2 を測る (5 ms 送り)"""
    from scipy.linalg import solve_toeplitz
    y = librosa.resample(x, orig_sr=sr, target_sr=11025); hop = int(11025 * FP / 1000); win = int(0.025 * 11025)
    y = np.append(y[0], y[1:] - 0.94 * y[:-1]); w = np.hamming(win); out = []
    for i in range(0, len(y) - win, hop):
        f = y[i:i + win] * w
        r = np.correlate(f, f, 'full')[win - 1:win + 13]
        if r[0] < 1e-8: out.append((0, 0)); continue
        try: a = np.concatenate([[1], solve_toeplitz(r[:12], -r[1:13])])
        except Exception: out.append((0, 0)); continue
        rt = np.roots(a); rt = rt[np.imag(rt) > 0.01]
        fr = np.angle(rt) * 11025 / (2 * np.pi); bw = -np.log(np.abs(rt)) * 11025 / np.pi
        c = sorted(f_ for f_, b in zip(fr, bw) if 180 < f_ < 3500 and b < 500)
        f1 = next((f_ for f_ in c if f_ < 1000), 0); f2 = next((f_ for f_ in c if f_ > max(f1 + 250, 650)), 0)
        out.append((f1, f2))
    return np.array(out)

def main(src, dst):
    x, sr = sf.read(src); x = x.mean(1) if x.ndim > 1 else x
    if sr != SR: x = librosa.resample(x, orig_sr=sr, target_sr=SR); sr = SR
    x = x.astype(np.float64) / (np.abs(x).max() + 1e-9) * 0.9
    f0, t = pw.harvest(x, sr, f0_floor=60, f0_ceil=500, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    fft_size = (sp.shape[1] - 1) * 2
    F = formants(x, sr); n = min(len(F), len(f0)); F = F[:n]; f0 = f0[:n]; sp = sp[:n]; ap = ap[:n]
    en = 10 * np.log10(sp.sum(1) + 1e-12)
    voiced = (f0 > 0) & (F[:, 0] > 0) & (F[:, 1] > 0) & (en > np.percentile(en, 45))
    # 安定: 前後 2 フレームでフォルマントが大きく動かない
    dF = np.abs(np.gradient(F[:, 0])) + 0.5 * np.abs(np.gradient(F[:, 1]))
    voiced &= dF < 40
    z = lambda a, v: (a - v[voiced].mean()) / (v[voiced].std() + 1e-9)
    Z = np.stack([z(F[:, 0], F[:, 0]), z(F[:, 1], F[:, 1])], 1)
    tm = np.array([TMPL[k] for k in 'aiueo'], float); tz = (tm - tm.mean(0)) / tm.std(0)
    D = np.linalg.norm(Z[:, None, :] - tz[None], axis=2); best = D.argmin(1); srt = np.sort(D, 1)
    conf = voiced & (srt[:, 1] - srt[:, 0] > 0.35) & (srt[:, 0] < 0.9)
    out = {'fft_size': fft_size, 'f0_med': float(np.median(f0[f0 > 0]))}
    counts = {}; lsp = np.log(sp + 1e-12)
    for k, v in enumerate('aiueo'):
        sel = conf & (best == k); counts[v] = int(sel.sum())
        out['sp_' + v] = np.exp(np.median(lsp[sel], 0)) if sel.sum() >= 8 else None
        out['F_' + v] = np.median(F[sel], 0) if sel.sum() >= 8 else np.array(TMPL[v], float)
    # 足りない母音は近い母音から (a↔o、i↔e、u↔o)
    alt = {'a': 'o', 'o': 'a', 'i': 'e', 'e': 'i', 'u': 'o'}
    for v in 'aiueo':
        if out['sp_' + v] is None: out['sp_' + v] = out['sp_' + alt[v]] if out['sp_' + alt[v]] is not None else np.exp(np.median(lsp[voiced], 0))
    out['ap_v'] = np.median(ap[conf], 0)
    # 無声の子音: f0 がなく、高い帯域にエネルギーが集まるフレーム
    freqs = np.arange(sp.shape[1]) * sr / fft_size
    unv = (f0 == 0) & (en > np.percentile(en, 30))
    hi = sp[:, freqs > 4000].sum(1) / (sp.sum(1) + 1e-12); mid = sp[:, (freqs > 2000) & (freqs < 4000)].sum(1) / (sp.sum(1) + 1e-12)
    s_sel = unv & (hi > 0.5); sh_sel = unv & (mid > 0.4) & (hi < 0.5)
    counts['s'], counts['sh'] = int(s_sel.sum()), int(sh_sel.sum())
    out['sp_s'] = np.exp(np.median(lsp[s_sel], 0)) if s_sel.sum() >= 5 else None
    out['sp_sh'] = np.exp(np.median(lsp[sh_sel], 0)) if sh_sel.sum() >= 5 else None
    out['counts'] = np.array([counts[k] for k in ('a', 'i', 'u', 'e', 'o', 's', 'sh')])
    np.savez(dst, **{k: v for k, v in out.items() if v is not None})
    print('f0 median %.1f Hz' % out['f0_med'], 'frames per class', counts)
    for v in 'aiueo': print(v, 'F1/F2', np.round(out['F_' + v]).astype(int))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
