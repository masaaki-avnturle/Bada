#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""濁らない、鮮明なきれいな声 (CCXCI〜CCXCV の声)。11/08 14:55 の声を、20 代の大人の女性の澄んだ声に。
  元: 届いた 20261108_145525_tsukuyomi_aureola_messia.mp3 は make_voice288.py の出力で、calma の声 (20261108_145525_aureola_sensuale_calma.mp3) から作ったもの。
      3 つの声と残響が混ざった後の音からは、息や響きだけを取り除けないので、その元の calma の声から作り直す (11/08 14:55 の元の録音は手元に無い)。
      読み取りと下ごしらえは make_voice265.py と同じ (Harvest で 120〜450 Hz の中だけを読む、読み落としを結ぶ、句の終わりを息に溶かす、低い所を抑える、
      残響を抑える、静かな話し始めを均す)。合成し直すと基音の整数倍だけが鳴るので、calma の 5 度上の声は鳴らなくなる
  濁らない:
    低い所を軽く 曲の音は 150〜600 Hz に集まっている。声の F_LOW Hz 以下を LOW dB、250〜500 Hz のこもりを MUD dB 下げて、同じ所で声と曲がうなるのを減らす
                (測った「うなりの指数」は、これでいちばん下がる; 倍音の声を重ねるかどうかでは、ほとんど変わらない)
    残響なし   響きを足さない。calma に残っている響きは、読み取りの所で抑える (DRY)
    声は 1 つ   倍音の声 (2 倍・3 倍) も囁きの層も重ねない — 1 人の声として、母音の形がはっきり聞こえるように (L2・L3 を指定すれば重ねられる)
  鮮明:
    息を減らす  母音の息を AIR 倍に (前の声は 0.60)。息だった所が倍音で鳴り、声の芯がはっきりする。子音の息はそのまま。
                3.5 kHz から上は息を少し戻す (HF_AIR; 高い倍音だけが機械のように鳴らないように)
    言葉の帯域  1.5〜5 kHz を PRES dB、5〜9 kHz を AIRDB dB 持ち上げる (低い所に寄った配分を、話し声らしい配分へ)
    弱い音節   音節ごとの山の大きさをそろえる (弱い音節を最大 +6 dB、強い音節を最大 −3 dB; 差の LEV_K 倍)。音節の後に残る音はその音節と同じだけしか動かさないので、言葉の切れ目は浅くならない
    立ち上がり  圧縮はごく軽く (tanh ×COMP)
  きれいな声: 20 代の大人の女性の声。基音の中央値は引数で (曲の調に合わせる)。フォルマント 1.05 倍 (前の声と同じ; calma の 1.10 倍と合わせて 1.155 倍)。
    抑揚 0.92 倍 (前の声と同じ)。伸ばした音は、引数の長調の音階に 0.9 で調律
  使い方: python make_voice291.py <calma の声.wav (モノラル)> <出力.wav> [基音の中央値 Hz (既定 220)] [長調の主音 (0 = C … 11 = B; 既定 5 = F)] [層を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import make_voice265 as M
from feminize_voice import feminize

E = lambda k, v: float(os.environ.get(k, v))
MAJOR = (0, 2, 4, 5, 7, 9, 11)
AIR = E('AIR', '0.30')                                 # 母音の息をここまで減らす
HF_AIR = E('HF_AIR', '0.5')                            # 3.5 kHz から上 (6 kHz で全部) に戻す息の割合
DRY = E('DRY', '0.22')                                 # calma の残響を抑える量 (make_voice265.py と同じ)
FLATTEN = E('FLATTEN', '0.92')                         # 抑揚
FM = E('FM', '1.05')                                   # フォルマント
P = dict(L2=E('L2', '-99'), L3=E('L3', '-99'),         # 倍音の声の大きさ (dB; −99 = 重ねない)
         LOW=E('LOW', '-5.0'), F_LOW=E('F_LOW', '350'), MUD=E('MUD', '-2.5'), PRES=E('PRES', '4.0'), AIRDB=E('AIRDB', '3.0'),
         LEV_K=E('LEV_K', '0.4'), COMP=E('COMP', '1.3'))
# (名前, 倍音, フォルマント, 音量の名前, 左右 −1〜+1, ここから上を落とす Hz)
VOICES = [('harm1', 1.0, FM, None, 0.0, None), ('harm2', 2.0, FM + 0.035, 'L2', -0.3, 7000.0), ('harm3', 3.0, FM + 0.07, 'L3', 0.3, 6000.0)]

def syllables(m, sr, k, up=6.0, down=-3.0):
    """音節ごとの山の大きさをそろえる。50 ms でならした音量の山 (前後 0.12 秒でいちばん大きい所) を音節の芯と見て、芯ごとに、基準 (芯の大きさの上から 25%) との差の
      k 倍をつまみにする。芯と芯の間のつまみは、両隣をまっすぐ結ぶ。音節の後に残る音は、その音節と同じだけしか動かないので、言葉の切れ目は浅くならない"""
    hop = int(0.01 * sr); win = int(0.03 * sr); n = (len(m) - win) // hop
    e = uniform_filter1d(10 * np.log10(np.array([(m[i * hop:i * hop + win] ** 2).mean() for i in range(n)]) + 1e-20), 5)
    nuc = np.where((e >= maximum_filter1d(e, 25)) & (e > np.percentile(e, 95) - 30.0))[0]                  # 音節の芯 (声の無い所の山は数えない)
    ref = np.percentile(e[nuc], 75); g = uniform_filter1d(np.interp(np.arange(n), nuc, np.clip(k * (ref - e[nuc]), down, up)), 11)
    return 10 ** (np.interp(np.arange(len(m)), np.arange(n) * hop + win / 2.0, g) / 20.0)

def finish(lay, sr, p=P):
    """層 (名前 → モノラルの音; 基音の声と同じ rms) を重ねて、仕上げる。返り値はステレオ"""
    L = R = 0.0
    for name, harm, formant, lv, pan, top in VOICES:
        lev = p[lv] if lv else 0.0
        if lev < -90 or name not in lay: continue
        v = lay[name] * 10 ** (lev / 20.0)
        if top: v = sosfiltfilt(butter(2, top, 'low', fs=sr, output='sos'), v)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
    n = len(L); bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v); g = lambda d: 10 ** (d / 20.0) - 1.0
    def eq(v):
        v = sosfiltfilt(butter(2, 11000.0, 'low', fs=sr, output='sos'), v)
        v = sosfiltfilt(butter(2, 90.0, 'high', fs=sr, output='sos'), v)                                   # 90 Hz 以下は声ではない
        v = v + sosfiltfilt(butter(2, p['F_LOW'], 'low', fs=sr, output='sos'), v) * g(p['LOW'])             # 低い所を軽く
        v = v + bp(v, 250.0, 500.0) * g(p['MUD'])                                                          # こもり
        v = v + bp(v, 1500.0, 5000.0) * g(p['PRES'])                                                       # 言葉の帯域
        return v + bp(v, 5000.0, 9000.0) * g(p['AIRDB'])                                                   # 澄んだ高域
    L, R = eq(L), eq(R)
    if p['LEV_K'] > 0: gs = syllables((L + R) * 0.5, sr, p['LEV_K']); L, R = L * gs, R * gs                 # 弱い音節をそろえる
    pk = max(np.abs(L).max(), np.abs(R).max()); y = np.stack([np.tanh(c / pk * p['COMP']) / p['COMP'] * pk for c in (L, R)], axis=1)   # ごく軽い圧縮。残響もエコーも入れない
    hop = int(0.05 * sr); q = np.array([np.sqrt((y[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n // hop)]); on = q > np.percentile(q, 95) * 0.1
    i0 = next(i for i in range(len(on) - 3) if on[i:i + 3].all()); t_on = i0 * 0.05                         # 話し始め (強い所の −20 dB を 0.15 秒続けて超える所)
    a, b = int(max(t_on - 0.6, 0) * sr), int(max(t_on - 0.3, 0) * sr); y[:a] = 0.0; y[a:b] *= np.linspace(0, 1, b - a)[:, None]   # その 0.6 秒前までは無音に (録音の初めの小さな雑音を消す)
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                        # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); return np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1, t_on

def layers(src, target=220.0, tonic=5, names=None):
    """calma の声を読んで、層ごとの音 (名前 → モノラル; どの層も基音の声と同じ rms) を作る"""
    scale = [(tonic + d) % 12 for d in MAJOR]
    x, sr = sf.read(src); x = np.ascontiguousarray(M.level((x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64), sr))   # 静かな話し始めを均してから読む
    f0, sp, ap, info = M.analyze(x, sr, air=AIR, dry=DRY); print(info, flush=True)
    fhz = np.arange(ap.shape[1]) * (sr / 2.0) / (ap.shape[1] - 1)
    ap = np.ascontiguousarray(ap + (1.0 - ap) * (HF_AIR * np.clip((fhz - 3500.0) / 2500.0, 0.0, 1.0))[None, :])   # 高い所に息を少し戻す
    med0 = float(np.median(f0[f0 > 0])); semis = 12 * np.log2(target / med0); lay = {}; r1 = None
    for name, harm, formant, lv, pan, top in VOICES:
        if names is not None and name not in names: continue
        v = feminize(x, sr, 0, semis=semis, formant=formant, correct=0.9, flatten=FLATTEN, harm=harm, scale=scale, ana=(f0, sp, ap), gate=0.02).astype(np.float64)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; lay[name] = v / rms * r1
    return lay, sr, med0, semis

def main(src, out, target=220.0, tonic=5, stems=None):
    want = [v[0] for v in VOICES if v[3] is None or P[v[3]] > -90 or stems]
    lay, sr, med0, semis = layers(src, target, tonic, want)
    if stems:
        os.makedirs(stems, exist_ok=True)
        for k, v in lay.items(): sf.write(os.path.join(stems, k + '.wav'), v.astype(np.float32), sr)
    z, t_on = finish(lay, sr); sf.write(out, z.astype(np.float32), sr)
    print('読んだ高さの中央値 %.1f Hz → %+.2f 半音、%.1f 秒、話し始め %.2f 秒、rms %.1f dB、peak %.2f' % (
        med0, semis, len(z) / sr, t_on, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 220.0, int(sys.argv[4]) if len(sys.argv) > 4 else 5, sys.argv[5] if len(sys.argv) > 5 else None)
