#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンセサイザーの歌声 (日本語の歌詞をうたう)。
  声は倍音の加算合成: 声帯の音 (倍音列、高い倍音ほど弱く) を、母音のフォルマント (共鳴の山) で整形する。
  フォルマントは 5 ms ごとに目標の母音へなめらかに動き (母音から母音へ、子音から母音へのわたり)、
  音高は音から音へなめらかに移り (ポルタメント)、長い音には遅れてビブラートがかかる。
  子音はノイズ (s・sh・h・f・t・k・p など) と、有声の短いつなぎ (n・m・r・y・w・g・d・b・z・j) で作る。
  少し揺らした 2 本目の声を重ね、シンセサイザーらしい、なめらかな声にする。高い金属的な音は出さない (7 kHz より上の倍音は切る)。
  score の extras の 'VO' (t, d, m, lyr = 1 モーラのかな, ph = フレーズ番号, gain) をフレーズごとにまとめて合成する。
"""
import numpy as np

SR = 44100
FR = 0.005                                                   # 制御の間隔 (秒)

# ---------------------------------------------------------------- かな → (子音, 母音)
_ROWS = {'': 'あいうえお', 'k': 'かきくけこ', 's': 'さしすせそ', 't': 'たちつてと', 'n': 'なにぬねの', 'h': 'はひふへほ', 'm': 'まみむめも',
         'y': 'や_ゆ_よ', 'r': 'らりるれろ', 'w': 'わ___を', 'g': 'がぎぐげご', 'z': 'ざじずぜぞ', 'd': 'だぢづでど', 'b': 'ばびぶべぼ', 'p': 'ぱぴぷぺぽ'}
_SPECIAL = {'し': 'sh', 'ち': 'ch', 'つ': 'ts', 'ふ': 'f', 'じ': 'j', 'ぢ': 'j', 'づ': 'z', 'を': ''}
KANA = {}
for c, row in _ROWS.items():
    for ch, v in zip(row, 'aiueo'):
        if ch != '_': KANA[ch] = (_SPECIAL.get(ch, c), v)
KANA['ん'] = ('N', 'N')
_SMALL = {'ゃ': 'a', 'ゅ': 'u', 'ょ': 'o'}

def to_hira(s): return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)

def morae(text):
    """かなの文字列をモーラ (子音, 母音, 表記) の列に。ゃゅょ は拗音、ー は前の母音をのばす、空白は無視"""
    s = to_hira(text.replace(' ', '').replace('　', '')); out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == 'ー' and out: out.append(('-', out[-1][1], 'ー')); i += 1; continue
        if ch not in KANA: i += 1; continue
        c, v = KANA[ch]; lab = ch
        if i + 1 < len(s) and s[i + 1] in _SMALL:
            v = _SMALL[s[i + 1]]; lab += s[i + 1]
            c = {'sh': 'sh', 'ch': 'ch', 'j': 'j'}.get(c, c + 'y')
            i += 1
        out.append((c, v, lab)); i += 1
    return out

# ---------------------------------------------------------------- 母音のフォルマント (女声寄り、日本語の母音)
VOW = {'a': ([800, 1250, 2800, 3700], [90, 110, 160, 220], [1.0, 0.7, 0.28, 0.1]),
       'i': ([320, 2600, 3200, 3900], [60, 140, 180, 240], [1.0, 0.32, 0.25, 0.08]),
       'u': ([360, 1450, 2600, 3600], [70, 120, 170, 230], [1.0, 0.42, 0.16, 0.06]),
       'e': ([500, 2050, 2800, 3700], [70, 120, 170, 230], [1.0, 0.5, 0.26, 0.09]),
       'o': ([500, 880, 2750, 3600], [80, 100, 170, 230], [1.0, 0.72, 0.14, 0.05]),
       'N': ([270, 1100, 2400, 3500], [60, 200, 250, 300], [1.0, 0.12, 0.05, 0.02]),     # 鼻音 (ん・n・m)
       'W': ([330, 720, 2500, 3500], [70, 100, 180, 240], [1.0, 0.5, 0.1, 0.04]),        # w のはじまり (唇をまるめた u)
       'R': ([420, 1500, 2600, 3600], [80, 140, 200, 240], [1.0, 0.35, 0.12, 0.05])}      # r (舌をはじく)
UNVOICED = {'k', 's', 't', 'h', 'p', 'sh', 'ch', 'ts', 'f', 'ky', 'hy', 'py'}
CDUR = {'': 0.0, 'k': 0.06, 's': 0.1, 't': 0.05, 'n': 0.06, 'h': 0.07, 'm': 0.065, 'y': 0.06, 'r': 0.03, 'w': 0.06, 'g': 0.05, 'z': 0.08,
        'd': 0.04, 'b': 0.045, 'p': 0.05, 'sh': 0.1, 'ch': 0.08, 'ts': 0.08, 'f': 0.08, 'j': 0.07, 'N': 0.0, '-': 0.0}

def _cdur(c): return CDUR.get(c, CDUR.get(c[:-1], 0.06) + (0.03 if c.endswith('y') and len(c) > 1 else 0.0))

def _smooth(x, tau):
    from scipy.signal import lfilter
    a = np.exp(-FR / tau)
    return lfilter([1 - a], [1, -a], x, axis=0, zi=(x[:1] * a) if x.ndim > 1 else [x[0] * a])[0]

def _bp(x, lo, hi, order=2):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(order, [lo, min(hi, SR * 0.45)], 'bandpass', fs=SR, output='sos'), x)

def render_phrase(notes, rng_seed=0, timbre='voice'):
    """notes: [(t 秒, d 秒, midi, (子音, 母音) or None)]。None はメリスマ (前の母音のまま音だけ動く)。 (波形, 開始秒) を返す。
    timbre='hypno': 洗脳のシンセサイザーの声 — デチューンした鋸歯波 3 本 + 1 オクターヴ下 (ボコーダーのように母音で整形)、
    ビブラートなしのまっすぐな音高、共鳴の山が 8 秒周期でゆっくり往復して倍音がうねる (曲の時刻に同期するので、どのフレーズも同じうねりの中)"""
    rng = np.random.default_rng(rng_seed)
    t0 = notes[0][0] - 0.2; t1 = notes[-1][0] + notes[-1][1] + 0.35
    nf = int((t1 - t0) / FR) + 2; ft = t0 + np.arange(nf) * FR
    lf0 = np.zeros(nf); amp = np.zeros(nf); Ft = np.zeros((nf, 4)); Bt = np.zeros((nf, 4)); Wt = np.zeros((nf, 4))
    vib = np.zeros(nf); noise_ev = []
    cur_v = notes[0][3][1] if notes[0][3] else 'a'
    F, B, W = VOW[cur_v if cur_v in VOW else 'a']; Ft[:] = F; Bt[:] = B; Wt[:] = W
    lf0[:] = notes[0][2]
    for i, (t, d, m, ph) in enumerate(notes):
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        gap = (nxt[0] - (t + d)) if nxt else 1.0
        cons = ph[0] if ph else ''
        if ph: cur_v = ph[1]
        cd = _cdur(cons) if ph else 0.0
        # 次の音の子音が無声なら、その閉鎖の前で声を切る
        ncd = _cdur(nxt[3][0]) if (nxt and nxt[3] and nxt[3][0] in UNVOICED) else 0.0
        v_on = t + 0.4 * cd; v_off = t + d - (0.6 * ncd if gap < 0.05 else min(0.06, max(0.0, 0.1 - gap)))
        k0, k1 = int((v_on - t0) / FR), int((v_off - t0) / FR)
        j0, j1 = int((t - t0) / FR), int((t + d - t0) / FR)
        lf0[j0:] = m                                                            # 音高の目標 (あとでなめらかに)
        if d > 0.45:                                                            # 長い音: 0.3 秒遅れてビブラート
            s_ = j0 + int(0.3 / FR)
            if s_ < j1: vib[s_:j1] = np.linspace(0, 1, j1 - s_) ** 0.5
        F, B, W = VOW[cur_v if cur_v in VOW else 'a']
        c0 = int((t - 0.6 * cd - t0) / FR)
        if ph and cons:                                                         # 子音
            base = cons[:-1] if (cons.endswith('y') and len(cons) > 1) else cons
            if cons in ('n', 'm', 'ny', 'my', 'N') or base in ('n', 'm'):
                amp[c0:k0] = 0.55; Ft[c0:k0], Bt[c0:k0], Wt[c0:k0] = VOW['N']
            elif base == 'r':
                amp[c0:k0] = 0.6; Ft[c0:k0], Bt[c0:k0], Wt[c0:k0] = VOW['R']
            elif base == 'w':
                amp[c0:k0] = 0.8; Ft[c0:k0], Bt[c0:k0], Wt[c0:k0] = VOW['W']
            elif base in ('g', 'd', 'b', 'z', 'j'):
                amp[c0:k0] = 0.35; Ft[c0:k0], Bt[c0:k0], Wt[c0:k0] = VOW['N']
            if cons.endswith('y') or cons == 'y' or cons in ('sh', 'ch', 'j'):   # 拗音・y: i からわたる
                g0 = max(c0, k0 - int(0.05 / FR)); Ft[g0:k0], Bt[g0:k0], Wt[g0:k0] = VOW['i']
                if cons == 'y': amp[g0:k0] = 0.8
            noise_ev.append((t - 0.6 * cd, cd, base if base else cons, cur_v))
        if ph and ph[0] == 'N':                                                 # ん: 音全体が鼻音
            amp[k0:k1] = 0.7; Ft[k0:k1], Bt[k0:k1], Wt[k0:k1] = VOW['N']
        else:
            amp[k0:k1] = 1.0; Ft[k0:k1], Bt[k0:k1], Wt[k0:k1] = F, B, W
        if ph is None:                                                          # メリスマ: 前の音からつなぐ
            p0 = int((notes[i - 1][0] + notes[i - 1][1] - t0) / FR)
            amp[min(p0, j0) - 2:k0] = np.maximum(amp[min(p0, j0) - 2:k0], 0.95)
        # 声の後ろ: 余韻の母音を保つ (次の子音まで)
        if gap >= 0.05 or not nxt:
            Ft[k1:], Bt[k1:], Wt[k1:] = F, B, W
    # なめらかに
    lf0 = _smooth(lf0, 0.028)
    amp = _smooth(amp, 0.014)
    Ft = _smooth(Ft, 0.022); Bt = _smooth(Bt, 0.022); Wt = _smooth(Wt, 0.022)
    hyp = timbre == 'hypno'
    if hyp: vib *= 0.0; lf0 = _smooth(lf0, 0.03)                               # まっすぐな音高、少し長いグライド
    vib = vib * (0.38 * np.sin(2 * np.pi * 5.3 * ft + 0.4) + 0.05 * rng.standard_normal(nf).cumsum() / np.sqrt(np.arange(1, nf + 1)))
    f0 = 440.0 * 2 ** ((lf0 + vib - 69) / 12.0)
    # 倍音の加算
    n = int((t1 - t0) * SR); ts = t0 + np.arange(n) / SR
    f0s = np.interp(ts, ft, f0); amps = np.interp(ts, ft, amp)
    out = np.zeros(n)
    fmax = 5500.0 if hyp else 7000.0
    kmax = int(fmax / f0.min())
    if hyp: fc = 400 + 2000 * (0.5 - 0.5 * np.cos(2 * np.pi * 0.125 * ft))     # 共鳴の山 (曲の時刻で往復)
    for det, gv in (((1.0, 0.8), (1.004, 0.6), (0.996, 0.6)) if hyp else ((1.0, 1.0), (1.0045, 0.45))):
        ph_ = 2 * np.pi * np.cumsum(f0s * det) / SR
        for k in range(1, kmax + 1):
            fk = k * f0 * det
            if fk.min() > fmax: break
            H = sum(Wt[:, i] / (1 + ((fk - Ft[:, i]) / (0.5 * Bt[:, i])) ** 2) for i in range(4)) + 0.012
            H = H + 0.1 / (1 + ((fk - 3000) / 450) ** 2)                      # 歌い手のフォルマント (声が伴奏から抜ける)
            if hyp: H = (H + 0.03) * (1 + 1.6 / (1 + ((fk - fc) / (0.14 * fc)) ** 2))   # 鋸歯波の明るさ + うねる共鳴
            a = H * (fk < fmax) * np.clip((fmax - fk) / 1500, 0, 1) / k ** (0.45 if hyp else 0.65)
            out += gv * np.interp(ts, ft, a) * np.sin(k * ph_ + 1.3 * k * (det - 1) * 1000)
    if hyp:                                                                  # 1 オクターヴ下の矩形波のサブ (低い倍音だけ)
        ph2 = np.pi * np.cumsum(f0s) / SR
        out += 0.35 * (np.sin(ph2) + np.sin(3 * ph2) / 3 * 0.5)
        out *= 0.6
    out *= amps
    out += 0.018 * _bp(rng.standard_normal(n), 1500, 6000) * amps                # 息の成分
    # 子音のノイズ
    for (ts0, cd, c, v) in noise_ev:
        i0 = int((ts0 - t0) * SR); ln = max(1, int(cd * SR)); i0 = max(0, i0)
        z = rng.standard_normal(ln); e = np.ones(ln)
        if c in ('s', 'z', 'ts'):   z = _bp(z, 4200, 8500); g = 0.09 if c == 's' else 0.06
        elif c in ('sh', 'j', 'ch'): z = _bp(z, 2200, 5500); g = 0.1 if c == 'sh' else 0.07
        elif c == 'h':              z = _bp(z, 600, 3500); g = 0.06
        elif c == 'f':              z = _bp(z, 500, 3000); g = 0.04
        elif c in ('k', 'g'):       z = _bp(z, 1500, 3200); g = 0.14 if c == 'k' else 0.07; e = np.exp(-np.arange(ln) / (0.012 * SR))
        elif c in ('t', 'd'):       z = _bp(z, 3000, 6000); g = 0.12 if c == 't' else 0.06; e = np.exp(-np.arange(ln) / (0.008 * SR))
        elif c in ('p', 'b'):       z = _bp(z, 400, 1800); g = 0.1 if c == 'p' else 0.05; e = np.exp(-np.arange(ln) / (0.008 * SR))
        else: continue
        if c in ('k', 't', 'p', 'g', 'd', 'b'):                                 # 破裂音: 閉鎖のあとに破裂 (後ろ寄り)
            sh = int(0.55 * ln); z = np.concatenate([np.zeros(sh), z[:ln - sh]]); e = np.concatenate([np.zeros(sh), e[:ln - sh]])
        else:
            e = np.minimum(1, np.minimum(np.arange(ln) / (0.25 * ln), (ln - np.arange(ln)) / (0.35 * ln)))
        seg = out[i0:i0 + ln]; seg += (g * z * e)[:len(seg)]
    return (0.22 * out).astype(np.float32), t0

def phrases(vo):
    """VO の extras をフレーズ番号でまとめ、render_phrase の入力に"""
    from collections import OrderedDict
    groups = OrderedDict()
    for e in sorted(vo, key=lambda e: e['t']): groups.setdefault(e.get('ph', 0), []).append(e)
    out = []
    for k, es in groups.items():
        notes = []
        for e in es:
            ph = None
            if e.get('lyr'):
                mm = morae(e['lyr'])
                ph = (mm[0][0], mm[0][1]) if mm else None
            notes.append((e['t'], e['d'], e['m'], ph))
        out.append((notes, es[0].get('gain', 0.3), es[0].get('pan', 0.0), k, es[0].get('tim', 'voice'), es[0].get('vopts') or {}))
    return out

if __name__ == '__main__':                                                     # 試聴: python sing.py out.wav
    import sys, soundfile as sf
    words = morae('よるのまちにひかるあめ')
    mel = [62, 64, 66, 69, 69, 71, 69, 66, 64, 62, 62]
    notes = []; t = 0.3
    for (c, v, lab), m in zip(words, mel):
        d = 0.9 if lab in ('め',) else 0.38
        notes.append((t, d * 0.97, m, (c, v))); t += d
    y, _ = render_phrase(notes, timbre=sys.argv[2] if len(sys.argv) > 2 else 'voice')
    sf.write(sys.argv[1] if len(sys.argv) > 1 else 'sing_test.wav', y / np.abs(y).max() * 0.8, SR)
    print('ok', len(y) / SR, [w[2] for w in words])
