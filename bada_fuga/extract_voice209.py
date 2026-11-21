#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tablet209.mp4 (CCIX: 光輪様の声・トラック 18・トラック 8) から、声だけを拾う。
  声の元の音 (tablet208 の光輪様の声) は手元に無い。曲は「声 + 伴奏」を synth.py で重ねたものなので、伴奏を同じ楽譜から作り直して、曲の音から引く。
  手順:
    1. 伴奏の段     compose_tablet209.py の楽譜から声を外し、仕上げを通さずに書き出す (synth.py の linear_master・no_fade)。トラック 18・トラック 8 は手元の音
    2. 仕上げを戻す  曲の音は、仕上げで柔らかい頭打ち (tanh) を通っている。逆の関数で戻す
    3. 合わせる     声の無い所 (伴奏だけの 222〜400 秒と 620〜690 秒) で、周波数ごとに伴奏の倍率 β(f) を最小二乗で決める。時間のずれは 0 サンプルだった
    4. 引く         曲の音 − β·伴奏。mp4 の音声は AAC 192 kbps → 56 kbps と 2 回圧縮されていて、波形としては 1 kHz 以下で約 10 dB、4 kHz から上はほとんど合わない。
                   引いた後に残る伴奏の雑音の割合 ρ(f) も、声の無い所で測っておく
    5. 2 回を合わせる 声は 2 回鳴る (8 秒からと 408 秒から; 同じ声、同じ倍率、ちょうど 400 秒離れている)。伴奏は 1 回目がトラック 18、2 回目がトラック 8 の続きで、
                   2 回目の後半 (声の 112 秒から) は声だけ。時間と周波数の枠ごとに、伴奏の小さい方の回に重みを掛けて足す (圧縮の雑音も、2 回を足すと半分になる)
    6. 抑える       残った伴奏の雑音の大きさ (ρ·伴奏²) を、枠ごとに引く (Wiener; 下限 −18 dB)
    7. 響きを外す    曲の中の声は、左 = y ∗ (δ + 1.2·irL)、右 = y(9 ms 遅れ) ∗ (δ + 1.2·irR) (synth.py の合成リバーブ; irL・irR は決まった乱数の種で作る 5 秒の響き)。
                   形が分かっているので、響きの付く前の声 y を、左右 2 つの式の最小二乗で解く (周波数ごと; 正則化 λ)。左右のずれも一緒に戻って、声は 1 本になる
    8. 終わり       曲の中では、声の終わりの 6 秒がフェードで小さくなる (初めの 6 秒も)。元の大きさへ戻す (最大 +10 dB)。話し始める前 (声の初めの約 5 秒) は無音にする。話している所の rms を −24 dB に
  書き出すもの: <出力>.wav = 響きを外した声 (左右同じ)。<出力>_nel_brano.wav = 曲の中で鳴っているままの声 (曲の全体の残響 5 秒が付いたまま、右が 9 ms 遅い)。
    どちらも帯域は 60 Hz〜8 kHz (曲の中でそうなっている)。声が元から持っている響き (光輪の 3.5 秒の残響) は声の一部なので、どちらにも残る
  確かめ: 声の分かっている試し (同じ楽譜の声を calma の声に替えて、同じ 2 回の圧縮に通したもの) で、取り出した声と本当の声を比べた (README)
  使い方:
    python extract_voice209.py stem <score_tablet209.json> <score209_M.json>          # 楽譜から声を外した、伴奏だけの楽譜を作る → synth.py で M_stem.wav に
    python extract_voice209.py <曲の音.wav (mp4 から; float)> <M_stem.wav> <出力.wav> [<本当の声の段.wav> [<残響なしの本当の声の段.wav>]]   # 後ろの 2 つは試しの時だけ (比べて SDR を出す)
"""
import sys, json
import numpy as np, soundfile as sf
from scipy.signal import stft, istft, lfilter
from scipy.fft import rfft, irfft, next_fast_len
from scipy.ndimage import uniform_filter1d, uniform_filter

SR = 44100; NF, HOP = 2048, 512
T1, T2, VLEN, TAIL = 8.0, 408.0, 198.5, 9.5                 # 声の 1 回目・2 回目の始まり (曲の秒)、声の長さ、その後の響きの長さ
FADE = 6.0                                                  # 曲の中で声に掛かっている入りと終わりのフェード (秒)
FREE = [(222.0, 400.0), (620.0, 690.0)]                     # 声の無い所 (伴奏だけ)
ALPHA, GMIN_DB, SELFN = 1.5, -18.0, 0.08                    # 抑える強さ、下限、声そのものの圧縮の雑音の見当 (2 回の重みを決める時に使う)
REV_LEN, REV_DECAY, REV_WET, DL = 5.0, 2.0, 0.4 * 3.0, int(0.009 * SR)   # 曲の全体の残響 (meta の reverb [5.0, 2.0, 0.4]; synth.py は wet × 3 で足す) と、右の遅れ (9 ms)
LAM = 0.2                                                   # 響きを外す時の正則化
db = lambda v: 10 * np.log10((np.asarray(v, dtype=np.float64) ** 2).mean() + 1e-20)

def untanh(x):
    """仕上げの柔らかい頭打ち (synth.py: tanh(1.15·x) / tanh(1.15)) を戻す。圧縮で 1 を超えた山は 0.96 で切ってから"""
    return np.arctanh(np.clip(x.astype(np.float64), -0.96, 0.96) * np.tanh(1.15)) / 1.15
def S2(x): return np.stack([stft(x[:, c], SR, nperseg=NF, noverlap=NF - HOP)[2] for c in (0, 1)])      # (2, 周波数, 時間)
def iS2(Z, n): return np.stack([istft(Z[c], SR, nperseg=NF, noverlap=NF - HOP)[1][:n] for c in (0, 1)], axis=1)

def fit(u, M):
    """声の無い所で、周波数ごとに伴奏の倍率 β(f) (最小二乗) と、引いた後に残る割合 ρ(f) = 残り ÷ (β·伴奏)² を決める"""
    num = den = pu = 0.0
    for a, b in FREE:
        U = S2(u[int(a * SR):int(b * SR)]); Mm = S2(M[int(a * SR):int(b * SR)])
        num = num + (U * np.conj(Mm)).real.sum(axis=(0, 2)); den = den + (np.abs(Mm) ** 2).sum(axis=(0, 2)); pu = pu + (np.abs(U) ** 2).sum(axis=(0, 2))
    sm = lambda v: uniform_filter1d(v, 9, mode='nearest'); beta = sm(num) / (sm(den) + 1e-20)
    return beta, np.clip((sm(pu) - beta ** 2 * sm(den)) / (beta ** 2 * sm(den) + 1e-20), 0.0, 50.0)

def passes(u, M, beta):
    """2 回の声の所を切り出して、伴奏を周波数ごとの倍率で引く。返すもの (回ごと): 引いた後、伴奏の大きさ"""
    out = []
    for T in (T1, T2):
        a, b = int(T * SR), int((T + VLEN + TAIL) * SR); Mm = S2(M[a:b]) * beta[None, :, None]; out.append((S2(u[a:b]) - Mm, np.abs(Mm) ** 2))
    return out

def combine(P, rho, alpha=ALPHA, gmin_db=GMIN_DB, selfn=SELFN):
    """2 回ぶんを、伴奏の小さい方に重みを掛けて足し、残った伴奏の雑音の大きさで抑える"""
    sm = lambda v: uniform_filter(v, size=(3, 3), mode='nearest')
    D = [p[0] for p in P]; N = [rho[:, None] * sm(p[1].sum(0)) for p in P]; PD = [sm((np.abs(d) ** 2).sum(0)) for d in D]
    nu = selfn * np.minimum(PD[0], PD[1]) + 1e-12; w = [1.0 / (N[i] + nu) for i in (0, 1)]; ws = w[0] + w[1]
    S = (w[0][None] * D[0] + w[1][None] * D[1]) / ws[None]; Nc = (w[0] ** 2 * N[0] + w[1] ** 2 * N[1]) / ws ** 2
    G = sm(np.sqrt(np.maximum(1.0 - alpha * Nc / (sm((np.abs(S) ** 2).sum(0)) + 1e-20), 10 ** (gmin_db / 10.0))))
    return iS2(S * G[None], int((VLEN + TAIL) * SR)), w[0] / ws

def unfade(v, limit_db=10.0):
    """曲の中で声に掛かっているフェード (入り 6 秒、終わり 6 秒; まっすぐ) を戻す。戻す量は limit_db まで"""
    t = np.arange(len(v)) / SR; g = np.minimum(np.clip(t / FADE, 1e-6, 1.0), np.clip((VLEN - t) / FADE, 1e-6, 1.0)); g = np.where(t >= VLEN, 1.0, g)
    return v / np.maximum(g, 10 ** (-limit_db / 20.0))[:, None]

def make_ir(seed):
    """synth.py の合成リバーブと同じ響き (指数で減る雑音、1 次のローパス、初めの 12 ms は 0、エネルギー 1)"""
    n = int(REV_LEN * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed).standard_normal(n).astype(np.float32); r *= np.exp(-t / REV_DECAY)
    y = lfilter([0.35], [1, -0.65], r).astype(np.float32); y[:int(0.012 * SR)] = 0; return (y / np.sqrt((y ** 2).sum())).astype(np.float64)

def dereverb(v, lam=LAM):
    """曲の全体の残響と左右のずれを外して、響きの付く前の声 (1 本) を返す。Y = (HL*·VL + HR*·VR) / (|HL|² + |HR|² + λ)"""
    n = len(v); N = next_fast_len(n + int(REV_LEN * SR)); f = np.fft.rfftfreq(N, 1 / SR)
    HL = 1.0 + REV_WET * rfft(make_ir(11), N); HR = np.exp(-2j * np.pi * f * DL / SR) * (1.0 + REV_WET * rfft(make_ir(12), N))
    return irfft((np.conj(HL) * rfft(v[:, 0], N) + np.conj(HR) * rfft(v[:, 1], N)) / (np.abs(HL) ** 2 + np.abs(HR) ** 2 + lam), N)[:n]

def sdr(est, ref, a=6.0, b=196.0):
    """試し: 取り出した声と本当の声の比べ (倍率を合わせてから)。波形の SDR (dB)、帯域ごと"""
    e = est[int(a * SR):int(b * SR)].astype(np.float64); r = ref[int(a * SR):int(b * SR)].astype(np.float64); k = (e * r).sum() / (r ** 2).sum(); E = S2(e - k * r); R = S2(k * r)
    f = np.fft.rfftfreq(NF, 1 / SR); pe = (np.abs(E) ** 2).sum(axis=(0, 2)); pr = (np.abs(R) ** 2).sum(axis=(0, 2))
    return db(k * r) - db(e - k * r), [10 * np.log10(pr[(f >= lo) & (f < hi)].sum() / pe[(f >= lo) & (f < hi)].sum()) for lo, hi in ((60, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000))]

def main(mix, stem, out, truth=None):
    X, sr = sf.read(mix, always_2d=True, dtype='float32'); M, _ = sf.read(stem, always_2d=True, dtype='float32'); assert sr == SR
    n = min(len(X), len(M)); u = untanh(X[:n]); M = M[:n].astype(np.float64); beta, rho = fit(u, M); f = np.fft.rfftfreq(NF, 1 / SR)
    bands = ((60, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000))
    print('伴奏の倍率 β (帯域ごとの中央値): ' + ' '.join('%d〜%d:%.3f' % (lo, hi, np.median(beta[(f >= lo) & (f < hi)])) for lo, hi in bands))
    print('引いた後に残る割合 ρ (dB): ' + ' '.join('%d〜%d:%+.1f' % (lo, hi, 10 * np.log10(np.median(rho[(f >= lo) & (f < hi)]) + 1e-9)) for lo, hi in bands))
    P = passes(u, M, beta); v, w1 = combine(P, rho); n_out = len(v)
    e1, e2 = iS2(P[0][0], n_out), iS2(P[1][0], n_out); a, b = int(6 * SR), int(196 * SR)
    print('2 回の声の重なり (伴奏を引いただけの 2 つの相関; 6〜196 秒): %.3f | 1 回目に掛けた重みの平均: 声の 8〜112 秒 %.2f、112〜196 秒 %.2f' % (
        np.corrcoef(e1[a:b].ravel(), e2[a:b].ravel())[0, 1], w1[:, int(8 * SR / HOP):int(112 * SR / HOP)].mean(), w1[:, int(112 * SR / HOP):int(196 * SR / HOP)].mean()))
    if truth:
        Vt = sf.read(truth, always_2d=True, dtype='float32')[0]; ref = Vt[int(T1 * SR):int(T1 * SR) + n_out]
        for name, est in (('伴奏を引くだけ (1 回目)', e1), ('伴奏を引くだけ (2 回目)', e2), ('2 回を合わせて抑える', v)):
            s, sb = sdr(est, ref); print('  試し %-24s SDR %5.1f dB | 帯域ごと %s' % (name, s, ' '.join('%.1f' % q for q in sb)))
        for name, a_, b_ in (('声の 8〜112 秒 (2 回とも伴奏がある)', 8.0, 112.0), ('声の 112〜196 秒 (2 回目は声だけ)', 112.0, 196.0)): print('  試し %s: SDR %.1f dB' % (name, sdr(v, ref, a_, b_)[0]))
    hop = int(0.05 * SR); p = np.array([db(q) for q in np.array_split(unfade(v)[:int(VLEN * SR)], int(VLEN / 0.05))]); act = p > np.percentile(p, 95) - 30
    on = np.where(act[:-2] & act[1:-1] & act[2:])[0][0] * 0.05                                                # 話し始め (曲の中のままの声で測る; 響きを外した声は、その前に逆向きの響きの雑音が −50 dB ほど出る)
    def finish(z, path, name, tail):                                                                        # フェードを戻し、話し始める前は無音に、声の後は tail 秒まで、話している所の rms を −24 dB に
        z = unfade(z)[:int((VLEN + tail) * SR)]; k = int(min(2.0, tail) * SR); z[-k:] *= np.linspace(1, 0, k)[:, None]
        z *= np.clip((np.arange(len(z)) / SR - (on - 0.40)) / 0.25, 0.0, 1.0)[:, None]
        p = np.array([db(z[i * hop:(i + 1) * hop]) for i in range(len(z) // hop)]); act = p > np.percentile(p, 95) - 30
        z = z * 10 ** ((-24.0 - 10 * np.log10(np.mean(10 ** (p[act] / 10)))) / 20.0); sf.write(path, z.astype(np.float32), SR)
        print('書き出し %s (%s): %.1f 秒、話している所の rms −24.0 dB (全体 %.1f dB)、山 %.3f、左右の相関 %.2f | 話しているのは %.1f〜%.1f 秒' % (
            path, name, len(z) / SR, db(z), np.abs(z).max(), np.corrcoef(z[:, 0], z[:, 1])[0, 1], np.where(act)[0][0] * 0.05, (np.where(act)[0][-1] + 1) * 0.05))
    y = dereverb(v)
    if truth and len(sys.argv) > 5:                                                                         # 試し: 響きの付く前の本当の声 (残響なしで書き出した声の段の左) と比べる
        ref = sf.read(sys.argv[5], always_2d=True, dtype='float32')[0][int(T1 * SR):int(T1 * SR) + n_out]; two = lambda z: np.stack([z, z], axis=1)
        yw = 0.5 * (v[:-DL, 0] + v[DL:, 1]); yw = np.concatenate([yw, np.zeros(DL)])
        for name, est in (('曲の中のままの声 (左)', two(v[:, 0])), ('左右のずれを戻して足しただけ', two(yw)), ('響きを外した声', two(y))):
            sv, sb = sdr(est, two(ref[:, 0])); print('  試し、響きの付く前の声と比べて %-22s SDR %5.1f dB | 帯域ごと %s' % (name, sv, ' '.join('%.1f' % q for q in sb)))
    print('話し始め: 声の %.2f 秒 (曲の %.2f 秒と %.2f 秒)' % (on, T1 + on, T2 + on))
    finish(np.stack([y, y], axis=1), out, '響きを外した声', 0.5); finish(v, out[:-4] + '_nel_brano.wav', '曲の中のままの声', 7.0)     # 響きを外した声は、声の終わり (198.5 秒) の後に何も無いので 0.5 秒で閉じる

if __name__ == '__main__':
    if sys.argv[1] == 'stem':
        d = json.load(open(sys.argv[2])); d['extras'] = [e for e in d['extras'] if not e['rid'].startswith('20261108')]       # 声 (20261108_145525.wav) を外す
        d['meta'].update(linear_master=True, fixed_peak=2.0, no_fade=True); json.dump(d, open(sys.argv[3], 'w'), ensure_ascii=False); print('伴奏だけの楽譜:', sys.argv[3], len(d['extras']), '個')
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
