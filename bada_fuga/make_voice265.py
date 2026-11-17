#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ホッと一安心する 20 代の女性の光輪様の声、ちょっとだけセクシィ (CCLXV の声)。
  元: 届いた 20261108_145525_aureola_sensuale_calma.mp3 — 11/08 14:55 の声をすでに作り換えたもの (215 Hz の少し低めの女声、5 度上と
      1 オクターヴ上の声、息と囁き、残響 1.5 秒・0.4)。11/08 14:55 の元の録音は手元に無いので、この音声から作り直す
  読み取り (analyze — WORLD で声を分析し、合成し直す前に手を入れる):
    高さ      Harvest で 120〜450 Hz の中だけを読む (残響の中でも途切れにくい)。合成し直すと基音の整数倍だけが鳴るので、元の 5 度上の声 (基音の 1.5 倍の所) は鳴らなくなる
    読み落とし 母音の形をしていて (低い帯域が強い) 十分に大きいのに高さが読めなかった所のうち、前後に声があって強さが落ち込んでいない所 (多くは 0.1 秒以下) は、
              前後の高さを結んで声として鳴らす。そのままだと、そこだけ囁きになってしまう
    句の終わり 強さが落ちていく穴は、句の後や子音の閉鎖の間に残った残響 (毎秒 20 dB ほどで減る)。声には戻さない。ただ 0.15 秒より長い穴 (句の終わり) は、
              穴に入る前の高さの動きを 0.15 秒だけ続けて、声を息に溶かして終える (ぷつりと息に変わらないように)。残った響きはさらに −8 dB まで下げる
    低い所    元の声は句の終わりで 130〜150 Hz (男声の高さ) まで下がる。E3 = 165 Hz から下は、下がり方を 0.25 倍に抑える (20 代の女性の声の域に保つ)
    息        声に入っている息 (3 kHz から上はほとんどが息) を AIR 倍に減らす — ドエロをやめて、ちょっとだけ。子音 (低い帯域に対して高い帯域が強い所) の息はそのまま残す
    残響      元の残響を、声の響きの形の上で抑える (最大 −8 dB; 弱い音節まで削らないように控えめに)。句の後に残る響きが短くなり、言葉の移り変わりがはっきりする
  作り直し (feminize_voice.py):
    20 代     高さは A3 = 220 Hz を中心に (読んだ高さの中央値から半音数を決める)。フォルマント 1.035 倍 (元の 1.10 倍と合わせて 1.14 倍)
    ホッと    抑揚 0.9 倍 (落ち着き)。伸ばした音はヘ長調 (= ニ短調、トラック 18 と 8 の調) の音階に 0.9 で調律
    光輪      倍音の声を 2 つ: 基音のちょうど 2 倍 (少し左)、ちょうど 3 倍 (少し右)。同じ抑揚から作るので、どの瞬間も 1 : 2 : 3。時間もずらさない。
              光輪の響き (残響 1.6 秒) はごく控えめに
  下ごしらえ: 元の声は静かに話し始める (初めの 40 秒は 5〜7 dB 小さい)。読み取りの前に、6 秒の窓の音量でゆっくり均しておく (+6 / −2 dB まで)
  仕上げ: 11 kHz 以上を落とし、250 Hz 以下 +1.5 dB (近さ — ちょっとだけ)、言葉の帯域と澄んだ高域を少し持ち上げ、70 Hz 以下を半分に、
    柔らかい圧縮で音量を均す。声の無い所を閉じるゲートは低く (強い所の 2%)。rms −24 dB、ステレオ
  使い方: python make_voice265.py <作り換え済みの声.wav (モノラル)> <出力.wav> [層を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf, pyworld as pw
from scipy.signal import butter, sosfiltfilt, fftconvolve
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from feminize_voice import feminize

FR = 0.005                                             # WORLD の枠 (5 ms)
TARGET = 220.0                                         # 基音の中央値をここへ (A3)
SCALE = [5, 7, 9, 10, 0, 2, 4]                         # ヘ長調 = ニ短調の音階 (移調した後の高さで)
DRY, AIR, FLATTEN = 0.22, 0.45, 0.9
F_LOW, LOW_K = 165.0, 0.25                             # 元の声の高さで、ここ (E3) から下は下がり方を LOW_K 倍に
# (名前, 倍音, フォルマント, 音量 dB, 左右 −1〜+1, ここから上を落とす Hz)
VOICES = [('harm1', 1.0, 1.035, 0.0, 0.0, None), ('harm2', 2.0, 1.07, -11.0, -0.3, 7000.0), ('harm3', 3.0, 1.105, -17.0, 0.3, 6000.0)]
WARM_DB, PRES_DB, CLEAR_DB, COMP, REV = 1.5, 1.2, 3.0, 1.7, 0.10

def dry_envelope(sp, amount, decay=27.0, delay=0.05, floor=-8.0):
    """残響を抑える。各周波数で、過去の強さを残響の減り方 (decay dB/秒) でならしたものを「いま残っている響き」と見て、その amount 倍だけ響きの形を下げる。
      いま鳴っている強い声はほとんど変えず、句の後に残る響きと、音の移り変わりに被さる響きを最大 floor dB まで下げる"""
    a = 10 ** (-decay * FR / 10.0); R = np.empty_like(sp); acc = np.zeros(sp.shape[1])
    for i in range(len(sp)): acc = a * acc + (1 - a) * sp[i]; R[i] = acc
    d = int(round(delay / FR)); late = np.zeros_like(sp); late[d:] = R[:-d] * 10 ** (-decay * delay / 10.0)   # delay より手前の響きは声の一部として残す
    G = np.maximum(1.0 - amount * late / (sp + 1e-20), 10 ** (floor / 10.0))
    return sp * uniform_filter1d(uniform_filter1d(G, 5, axis=0), 15, axis=1)                                 # 25 ms・約 160 Hz でならす (細かい凹凸を作らない)

def fill_voicing(f0, e, lfhf, low=F_LOW):
    """高さが読めなかった所 (母音の形で、十分に大きい) を見分けて、声に戻す所に高さを入れる。
      返すもの: 高さ、声に戻した枠、息に溶かす割合 (0〜1; 下がり目を続けた所)、残響として下げる割合 (0〜1)"""
    v = f0 > 0; n = len(f0); out = f0.copy(); filled = np.zeros(n, bool); fade = np.zeros(n); tail = np.zeros(n)
    cand = (uniform_filter1d(((~v) & (e > -28.0) & (lfhf > 10.0)).astype(float), 7) > 0.5) & ~v              # 35 ms の多数決
    i = 0
    while i < n:
        if not cand[i]: i += 1; continue
        j = i
        while j < n and cand[j]: j += 1
        L = j - i; k = np.arange(L)
        pb = np.arange(max(0, i - 12), i); pb = pb[f0[pb] > 0]; pa = np.arange(j, min(n, j + 12)); pa = pa[f0[pa] > 0]
        fb = float(np.median(f0[pb[-8:]])) if len(pb) >= 3 else 0.0; fa = float(np.median(f0[pa[:8]])) if len(pa) >= 3 else 0.0
        if fb and fa and e[i:j].min() >= np.concatenate([e[pb[-8:]], e[pa[:8]]]).mean() - 6.0:               # 読み落とし: 強さが落ち込んでいない → 前後を結ぶ
            out[i:j] = fb * (fa / fb) ** ((k + 1.0) / (L + 1.0)); filled[i:j] = True
        else:                                                                                                # 残響 (句の後、閉鎖の間): 声には戻さない
            if L > 30 and len(pb) >= 8:
                p = np.polyfit(pb * FR, 12 * np.log2(f0[pb]), 1)                                             # 穴に入る前の 60 ms の高さの傾き (半音/秒)
                Lc = 30; kk = np.arange(Lc); m0 = np.clip(np.polyval(p, i * FR), 12 * np.log2(fb) - 1.0, 12 * np.log2(fb) + 1.0)
                mm = m0 + np.clip(p[0], -40.0, -3.0) * 0.12 * (1 - np.exp(-kk * FR / 0.12))                  # 0.15 秒だけ声を続ける。傾きは 0.12 秒でゆるむ (上がっていた所もごくゆるく下げる)
                out[i:i + Lc] = np.maximum(2 ** (mm / 12.0), low * 0.8); filled[i:i + Lc] = True; fade[i:i + Lc] = (kk + 1.0) / Lc
            tail[i:j] = np.clip((k - 20) / 40.0, 0, 1)                                                       # 0.1 秒を過ぎた所から 0.2 秒かけて
        i = j
    return out, filled, fade, tail

def analyze(x, sr, air=AIR, dry=DRY):
    f0, t = pw.harvest(x, sr, f0_floor=120, f0_ceil=450, frame_period=1000 * FR)
    sp0 = pw.cheaptrick(x, f0, t, sr); nb = sp0.shape[1]; fhz = np.arange(nb) * (sr / 2.0) / (nb - 1)
    band = lambda lo, hi: 10 * np.log10(sp0[:, (fhz >= lo) & (fhz < hi)].sum(axis=1) + 1e-20)
    e = 10 * np.log10(sp0.sum(axis=1) + 1e-20); e -= np.percentile(e, 95); lf, hf = band(120, 600), band(3000, 8000)
    f0f, filled, fade, tail = fill_voicing(f0, e, lf - hf)
    m = np.where(f0f > 0, 12 * np.log2(np.maximum(f0f, 1.0) / F_LOW), 0.0); f0f = np.where(f0f > 0, F_LOW * 2 ** (np.where(m < 0, m * LOW_K, m) / 12.0), 0.0)   # 低い所を抑える
    sp = pw.cheaptrick(x, f0f, t, sr); ap = pw.d4c(x, f0f, t, sr)
    # 子音らしさ (0〜1): 低い帯域 (120〜600 Hz) に対して高い帯域 (3〜8 kHz) が強い所 (差が 10 dB で 0、4 dB 以下で 1)。前後 10 ms に広げる。
    #   母音は差が 20 dB ほどある (元の声は暗い)。高い帯域が急に強くなる所、では母音の出だしまで子音と見てしまうので、その枠の中の傾きだけで見る
    c = uniform_filter1d(maximum_filter1d(np.clip((10.0 - (lf - hf)) / 6.0, 0, 1), 5), 5)[:, None]
    soft = np.interp(fhz, [0, 800, 3000, 8000, sr / 2.0], [0.03, 0.2, 0.55, 0.75, 0.9])[None, :]              # 息の少し混ざった柔らかい声 (低い所は声、高い所ほど息)
    ap = ap * (air + (1 - air) * c)                                                                           # 母音の息を air 倍に (子音の所は減らさない)
    ap = np.where(c < 0.5, np.minimum(ap, np.interp(fhz, [0, 800, 3000], [0.1, 0.3, 1.0])[None, :]), ap)      # 母音の低い帯域は声のまま (D4C が読めなかった枠が雑音にならないように)
    lo = np.minimum(ap, soft); ap = np.where(filled[:, None], lo + (0.98 - lo) * (fade[:, None] ** 2), ap)    # 声に戻した所は柔らかい声で、下がり目の続きは息に溶かす
    ap = ap + np.maximum(0.95 - ap, 0) * c * np.clip((fhz - 1500.0) / 1000.0, 0, 1)[None, :]                  # 子音の高い帯域は息のまま
    if dry > 0: sp = dry_envelope(sp, dry)
    sp = sp * (10 ** (-0.8 * tail))[:, None]                                                                  # 句の後に残る響きをさらに −8 dB まで
    info = '有声 %.1f%% → %.1f%% (読み落としを結んだ所 %.1f 秒、句の終わりを息に溶かした所 %.1f 秒)、残響と見た穴 %.1f 秒、子音と見た所 %.1f 秒' % (
        100 * (f0 > 0).mean(), 100 * (f0f > 0).mean(), (filled & (fade == 0)).sum() * FR, (fade > 0).sum() * FR, (tail > 0).sum() * FR, (c[:, 0] > 0.5).sum() * FR)
    return f0f, np.ascontiguousarray(sp), np.ascontiguousarray(np.clip(ap, 0.001, 1.0)), info

def level(m, sr, win=6.0, k=0.8, up=6.0, down=-2.0):
    """話し始めの静かな所をゆっくり持ち上げる: win 秒の窓の音量 (声のある所だけ) と全体の中央値の差の k 倍を、+up / down dB の範囲で補う"""
    hop = int(sr * 0.5); n = len(m) // hop; p = np.array([(m[i * hop:(i + 1) * hop] ** 2).mean() for i in range(n)])
    act = p > np.percentile(p, 90) * 10 ** (-2.5); w = int(win / 0.5)
    num = uniform_filter1d(np.where(act, p, 0.0), w, mode='nearest'); den = uniform_filter1d(act.astype(float), w, mode='nearest')
    db = 10 * np.log10(num / np.maximum(den, 1e-9) + 1e-20); ref = np.median(db[den > 0.3]); g = np.where(den > 0.3, np.clip(k * (ref - db), down, up), 0.0)
    g = uniform_filter1d(g, 5, mode='nearest'); return m * 10 ** (np.interp(np.arange(len(m)), (np.arange(n) + 0.5) * hop, g) / 20.0)

def main(src, out, stems=None):
    x, sr = sf.read(src); x = np.ascontiguousarray(level((x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64), sr))   # 静かな話し始めを均してから読む
    ana = analyze(x, sr); print(ana[3], flush=True)
    med0 = float(np.median(ana[0][ana[0] > 0])); semis = 12 * np.log2(TARGET / med0)
    L = R = 0.0; r1 = None
    for name, harm, formant, lev, pan, top in VOICES:
        v = feminize(x, sr, 0, semis=semis, formant=formant, correct=0.9, flatten=FLATTEN, harm=harm, scale=SCALE, ana=ana[:3], gate=0.02).astype(np.float64)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; v = v / rms * r1 * 10 ** (lev / 20.0)                # 層の音量を基音の声に対して決める
        if top: v = sosfiltfilt(butter(2, top, 'low', fs=sr, output='sos'), v)
        if stems: os.makedirs(stems, exist_ok=True); sf.write(os.path.join(stems, name + '.wav'), v.astype(np.float32), sr)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
    n = len(L); bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    def finish(v, seed):
        v = sosfiltfilt(butter(2, 11000, 'low', fs=sr, output='sos'), v)
        v = v + sosfiltfilt(butter(2, 250, 'low', fs=sr, output='sos'), v) * (10 ** (WARM_DB / 20) - 1)      # 近さ (ちょっとだけ)
        v = v + bp(v, 1200, 5000) * (10 ** (PRES_DB / 20) - 1)                                               # 言葉のはっきりさ
        v = v + bp(v, 5000, 10000) * (10 ** (CLEAR_DB / 20) - 1)                                             # 澄んだ高域 (息を減らした分を補う)
        v = v - sosfiltfilt(butter(2, 70, 'low', fs=sr, output='sos'), v) * 0.5                              # 70 Hz 以下のこもりを半分に
        rng = np.random.default_rng(seed); K = int(sr * 1.6); t = np.arange(K) / sr
        ir = rng.standard_normal(K) * np.exp(-t / 0.45); ir = sosfiltfilt(butter(2, 5000, 'low', fs=sr, output='sos'), ir); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
        return v, ir
    (L, irL), (R, irR) = finish(L, 265), finish(R, 266)
    pk = max(np.abs(L).max(), np.abs(R).max()); L, R = (np.tanh(c / pk * COMP) / COMP * pk for c in (L, R))  # 柔らかい圧縮 (音量を均す)
    y = np.stack([L + fftconvolve(L, irL)[:n] * REV, R + fftconvolve(R, irR)[:n] * REV], axis=1)             # 光輪の響き (ごく控えめ)
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                           # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('読んだ高さの中央値 %.1f Hz → %+.2f 半音、%.1f 秒、rms %.1f dB、peak %.2f' % (med0, semis, n / sr, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
