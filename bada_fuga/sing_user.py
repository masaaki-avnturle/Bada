#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
その人の声で歌う (WORLD ボコーダー = pyworld で合成)。
  voice_templates.py で話し声から取り出した「母音ごとのスペクトル包絡」(その人の声の響き) を、歌詞の母音の順につなぎ、
  旋律の音高 (ポルタメント、長い音には遅れてビブラート) で WORLD に鳴らす。響き (フォルマント) はそのまま、音高だけが歌の音になる。
  子音: s / sh はその人の録音の無声音から、h・f は次の母音を息で、k・t・p は閉鎖 + 破裂、n・m は鼻にかかった響き、
  r は短いはじき、y / w は い / お からのわたり。
  sing.py と同じ入力 (notes = [(t 秒, d 秒, midi, (子音, 母音) or None)]) で、(波形, 開始秒) を返す。
"""
import numpy as np
import sing

FP = 5.0; FR = FP / 1000.0; SR = 44100
_BANK = {}

def load(path, tilt=34.0, vclar=1.0):
    if path in _BANK: return _BANK[path]
    z = np.load(path); b = {k: z[k] for k in z.files}
    fs = int(b['fft_size']); freqs = np.arange(fs // 2 + 1) * SR / fs
    lp = lambda fc, floor: floor + (1 - floor) / (1 + (freqs / fc) ** 4)
    # こもりの補正: 録音は 500 Hz より上が急に落ちている (こもった電話の録音)。5 つの母音の平均のスペクトルを、
    # ふつうの声の平均 (500 Hz まで平ら、そこからオクターヴごとに -8 dB) に合わせる補正を、半オクターヴでなめらかにしてかける。
    # 母音どうしの違い (フォルマントの山) はそのまま残る。4 kHz より上は補正を増やさず、7 kHz より上は落とす (雑音を持ち上げない)
    lf = np.log2(np.clip(freqs, 60, SR / 2) / 500.0)
    avg = np.mean([10 * np.log10(b['sp_' + v] + 1e-20) for v in 'aiueo'], 0)
    sm = np.array([avg[np.abs(lf - x) < 0.25].mean() for x in lf])
    target = np.where(lf < 0, 0.0, -8.0 * lf) + sm[np.argmin(np.abs(freqs - 250))]
    corr = np.clip(target - sm, 0, tilt)
    corr = np.where(freqs > 4000, corr[np.argmin(np.abs(freqs - 4000))], corr) - 40 * np.log10(1 + (freqs / 7000) ** 2)
    eq = 10 ** (corr / 10.0)
    for v in 'aiueo': b['sp_' + v] = b['sp_' + v] * eq
    # 母音をはっきり: 日本語の男声の標準的なフォルマントの形 (母音どうしの比) を、その人の響きに控えめに重ねる (強さ vclar)
    FM = {'a': (720, 1200, 2550), 'i': (300, 2250, 2950), 'u': (340, 1350, 2400), 'e': (480, 1850, 2550), 'o': (480, 820, 2500)}
    H = {v: np.log(sum(w / (1 + ((freqs - F_) / (bw / 2)) ** 2) for F_, bw, w in zip(FM[v], (110, 140, 200), (1.0, 0.6, 0.25))) + 0.02) for v in FM}
    Hm = np.mean([H[v] for v in FM], 0)
    for v in 'aiueo': b['sp_' + v] = b['sp_' + v] * np.exp(vclar * (H[v] - Hm))
    if 'sp_s' not in b: b['sp_s'] = b['sp_i'] * (freqs > 4000) * 0.02 + 1e-10
    if 'sp_sh' not in b:                                                        # sh: s の帯域を 2〜5 kHz へ寄せる
        w = np.exp(-0.5 * ((freqs - 3200) / 1100) ** 2) + 0.15
        b['sp_sh'] = b['sp_s'] * w / w.mean()
    b['sp_N'] = b['sp_u'] * lp(900, 0.03) * 0.5                                 # 鼻音: 高い帯域を落とす
    b['sp_R'] = b['sp_e'] * 0.35
    b['sp_W'] = b['sp_o'] * lp(1200, 0.2)
    b['freqs'] = freqs; b['lp'] = lp
    _BANK[path] = b
    return b

def _smooth(x, tau):
    from scipy.signal import lfilter
    a = np.exp(-FR / tau)
    return lfilter([1 - a], [1, -a], x, axis=0, zi=(x[:1] * a) if x.ndim > 1 else [x[0] * a])[0]

def render_phrase(notes, bank_path, rng_seed=0, vib_depth=0.3, vib_rate=5.4, attack=0.012, sib=1.0, presence=0.0, formant=1.0, breath=0.0):
    """vib_depth / vib_rate: ビブラートの深さ (半音) と速さ、attack: 立ち上がりのなめらかさ (秒)、sib: s・sh の強さ (倍)、
    presence: 2.4 kHz あたりの明るさ (dB、声の抜け)。あたたかく穏やかな声は 浅く遅いビブラート・やわらかい立ち上がり・控えめな s。
    formant: 声の響き (スペクトル包絡) を周波数の方向に何倍にのばすか — 1.18 くらいで男声の響きが若い女性の響きになる (声道が短くなる)。
    breath: 2.5 kHz より上に息の成分を足す量 (0〜0.3、透きとおった軽い声に)"""
    import pyworld as pw
    b = load(bank_path); rng = np.random.default_rng(rng_seed); freqs = b['freqs']; nb = len(freqs)
    t0 = notes[0][0] - 0.2; t1 = notes[-1][0] + notes[-1][1] + 0.35
    nf = int((t1 - t0) / FR) + 2; ft = t0 + np.arange(nf) * FR
    lf0 = np.zeros(nf); voiced = np.zeros(nf); amp = np.zeros(nf)
    LS = np.zeros((nf, nb)); AP = np.tile(b['ap_v'], (nf, 1)); vib = np.zeros(nf)
    L = {k: np.log(b['sp_' + k] + 1e-12) for k in ('a', 'i', 'u', 'e', 'o', 's', 'sh', 'N', 'R', 'W')}
    L['s'] = L['s'] + np.log(sib); L['sh'] = L['sh'] + np.log(sib)
    if formant != 1.0:                                                          # 響きを高い方へのばす (母音・鼻音は全部、s・sh は半分だけ)
        for k in L:
            a = formant if k not in ('s', 'sh') else 1 + (formant - 1) * 0.5
            L[k] = np.interp(freqs / a, freqs, L[k])
    if breath:
        AP = np.clip(AP + breath * np.clip((freqs - 2500) / 3000, 0, 1)[None, :], 0, 1)
    if presence:
        pr = presence * np.log(10) / 10 * np.exp(-0.5 * ((freqs - 2400) / 900) ** 2)
        for v in ('a', 'i', 'u', 'e', 'o'): L[v] = L[v] + pr
    quiet = L['N'] - 9.0
    cur_v = notes[0][3][1] if notes[0][3] and notes[0][3][1] in 'aiueo' else 'a'
    LS[:] = L[cur_v]; lf0[:] = notes[0][2]
    for i, (t, d, m, ph) in enumerate(notes):
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        gap = (nxt[0] - (t + d)) if nxt else 1.0
        cons = ph[0] if ph else ''
        if ph and ph[1] in 'aiueo': cur_v = ph[1]
        cd = sing._cdur(cons) if ph else 0.0
        ncd = sing._cdur(nxt[3][0]) if (nxt and nxt[3] and nxt[3][0] in sing.UNVOICED) else 0.0
        v_on = t + 0.4 * cd; v_off = t + d - (0.6 * ncd if gap < 0.05 else min(0.06, max(0.0, 0.1 - gap)))
        k0, k1 = int((v_on - t0) / FR), int((v_off - t0) / FR)
        j0, j1 = int((t - t0) / FR), int((t + d - t0) / FR)
        c0 = max(0, int((t - 0.6 * cd - t0) / FR))
        lf0[j0:] = m
        if d > 0.45:
            s_ = j0 + int(0.3 / FR)
            if s_ < j1: vib[s_:j1] = np.linspace(0, 1, j1 - s_) ** 0.5
        V = L[cur_v]
        if ph and cons:
            base = cons[:-1] if (cons.endswith('y') and len(cons) > 1) else cons
            seg = slice(c0, k0)
            if base in ('n', 'm'):   LS[seg] = L['N']; voiced[seg] = 1; amp[seg] = 0.8
            elif base == 'r':        LS[seg] = L['R']; voiced[seg] = 1; amp[seg] = 0.8
            elif base == 'w':        LS[seg] = L['W']; voiced[seg] = 1; amp[seg] = 0.9
            elif base == 'y':        LS[seg] = L['i']; voiced[seg] = 1; amp[seg] = 0.9
            elif base in ('g', 'd', 'b'):
                LS[seg] = L['N'] - 1.5; voiced[seg] = 1; amp[seg] = 0.6
                e = min(k0, c0 + max(1, int(0.7 * (k0 - c0))))
                LS[e:k0] = (L['a'] if base == 'g' else L['s'] if base == 'd' else L['o']) - 2.0; voiced[e:k0] = 0; amp[e:k0] = 1
            elif base in ('z', 'j'):
                LS[seg] = L['s' if base == 'z' else 'sh'] - 0.8; voiced[seg] = 1; amp[seg] = 0.9; AP[seg] = np.clip(b['ap_v'] + 0.5, 0, 1)
            elif base in ('s', 'sh'):  LS[seg] = L[base]; voiced[seg] = 0; amp[seg] = 1
            elif base in ('ch', 'ts'):
                LS[seg] = L['sh' if base == 'ch' else 's']; voiced[seg] = 0; amp[seg] = 1
                LS[c0:c0 + 2] = quiet
            elif base == 'h':        LS[seg] = V - 1.8; voiced[seg] = 0; amp[seg] = 1
            elif base == 'f':        LS[seg] = V + np.log(b['lp'](1500, 0.05)) - 2.2; voiced[seg] = 0; amp[seg] = 1
            elif base in ('k', 't', 'p'):                                       # 閉鎖 → 破裂
                e = min(k0, c0 + max(1, int(0.6 * (k0 - c0))))
                LS[c0:e] = quiet; voiced[c0:e] = 0; amp[c0:e] = 1
                burst = {'k': L['a'] + np.log(np.exp(-0.5 * ((freqs - 2200) / 700) ** 2) + 0.05),
                         't': L['s'], 'p': L['o'] + np.log(b['lp'](1200, 0.05))}[base]
                LS[e:k0] = burst - 0.7; voiced[e:k0] = 0; amp[e:k0] = 1
            if cons.endswith('y') and len(cons) > 1 or cons in ('sh', 'ch', 'j'):   # 拗音: い からわたる
                g0 = max(c0, k0 - int(0.05 / FR)); LS[g0:k0] = L['i']; voiced[g0:k0] = 1; amp[g0:k0] = 0.9
        if ph and ph[0] == 'N':
            LS[k0:k1] = L['N']; voiced[k0:k1] = 1; amp[k0:k1] = 0.85
        else:
            LS[k0:k1] = V; voiced[k0:k1] = 1; amp[k0:k1] = 1.0
        if ph is None and i > 0:
            p0 = int((notes[i - 1][0] + notes[i - 1][1] - t0) / FR)
            lo = max(0, min(p0, j0) - 2); voiced[lo:k0] = 1; amp[lo:k0] = np.maximum(amp[lo:k0], 0.95); LS[lo:k0] = V
        if gap >= 0.05 or not nxt:
            LS[k1:] = V
    lf0 = _smooth(lf0, 0.03)
    vib = vib * (vib_depth * np.sin(2 * np.pi * vib_rate * ft + 0.3) + 0.04 * rng.standard_normal(nf).cumsum() / np.sqrt(np.arange(1, nf + 1)))
    f0 = 440.0 * 2 ** ((lf0 + vib - 69) / 12.0)
    LS = _smooth(LS, 0.02); amp = _smooth(amp, attack)
    vo = voiced > 0.5
    f0 = np.where(vo & (amp > 0.05), f0, 0.0)
    AP = np.where(vo[:, None], AP, 1.0)
    sp = np.exp(LS) * (amp[:, None] ** 2) + 1e-16
    y = pw.synthesize(np.ascontiguousarray(f0), np.ascontiguousarray(sp), np.ascontiguousarray(AP), SR, FP)
    ref = np.sqrt(np.exp(L['a']).sum())                                         # 声の大きさの基準 (母音あ)
    return (y / (ref + 1e-12) * 2.8).astype(np.float32), t0

if __name__ == '__main__':                                                     # 試聴: python sing_user.py bank.npz out.wav
    import sys, soundfile as sf
    words = sing.morae('よるのまちにひかるあめ')
    mel = [50, 52, 54, 57, 57, 59, 57, 54, 52, 50, 50]
    notes = []; t = 0.3
    for (c, v, lab), m in zip(words, mel):
        d = 0.9 if lab == 'め' else 0.38
        notes.append((t, d * 0.97, m, (c, v))); t += d
    y, _ = render_phrase(notes, sys.argv[1])
    sf.write(sys.argv[2], y / np.abs(y).max() * 0.8, SR); print('ok', len(y) / SR, 'peak', np.abs(y).max())
