#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_mantra_mix.py — 「Requiem BADA — CLVII · Mantra a tre nel 06:39」のピアノ (動画の音声) と
声の録音 (MP3 / AAC) だけを使って、楽器を一切足さずにミックスで 1 曲に仕上げる。

  python3 mantra_mix/make_mantra_mix.py tablet157.mp4 voice.mp3 -o mantra_mix/mantra_mix

出力: <out>.wav (24 bit) / <out>.mp3 (320 kbps) / <out>.mp4 (元の映像 + ミックス音声、--no-video で省略)

方針 — 足すのは「処理」だけで「音源」は足さない
  * ピアノ (動画の音声) は切らず・動かさず・音程も変えない。曲の骨格はそのまま。
  * 声は 32 のフレーズ (息継ぎで区切った発話) に切り分け、録音順のまま、♩=60 (1 小節 = 4 秒) の
    小節頭に置き直す。曲の 4 つの段落 (動画の字幕と同じ区切り) に合わせて距離感を変える:
      I.  0:00–2:48  脈とマントラ   … 8 小節はピアノだけ。その後 4 小節ごとに 1 フレーズ、遠く (残響多め・高域を丸める)
      II. 2:48–5:20  マントラが近づく … 3 小節ごと、残響を減らして近づく
      III.5:20–9:28  頂点 (a tre)   … 同じ声を 2 拍後 (左)・4 拍後 (右) に追いかけさせる 3 声のカノン。
                                     新しい声は足さない ── 同じ録音のディレイ・コピー
      IV. 9:28–11:43 消える        … 最後のフレーズが 1 小節ごとのエコーとなって残響へ溶け、ピアノだけで終わる
  * 声の処理: スペクトル減算によるノイズ除去 → ハイパス → EQ (こもり −、明瞭度 +) → コンプレッサ。
  * 空間: 合成インパルス応答の畳み込みリバーブ (声とピアノを同じ「部屋」に入れるため、ピアノにもごく薄く)。
  * 声が鳴る間だけピアノを数 dB 下げるダッキング (サイドチェイン)。
  * マスター: 2 パス loudnorm で −16 LUFS / −1 dBTP。

依存: numpy, scipy, soundfile, ffmpeg
"""
import argparse
import json
import math
import shutil
import subprocess
import sys

import numpy as np
import scipy.signal as sg
import soundfile as sf

SR = 44100
BAR = 4.0                     # ♩=60, 4/4
SECTIONS = [                  # 動画の字幕の段落 (秒)
    ('I',   0.0, 168.0),
    ('II',  168.0, 320.0),
    ('III', 320.0, 568.0),
    ('IV',  568.0, None),
]


# ----------------------------------------------------------------------------- io
def ffmpeg():
    p = shutil.which('ffmpeg')
    if not p:
        sys.exit('ffmpeg が必要です')
    return p


def decode(path, ch):
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-vn', '-f', 'f32le', '-ac', str(ch),
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x.reshape(-1, ch) if ch > 1 else x


def db(v):
    return 10 ** (v / 20)


# ----------------------------------------------------------------------------- voice cleanup
def denoise(x, floor_db=-14.0):
    """静かな 15% のフレームから雑音スペクトルを推定し、Wiener 風のゲインで差し引く。"""
    f, t, Z = sg.stft(x, SR, nperseg=2048, noverlap=1536)
    P = np.abs(Z) ** 2
    e = P.sum(0)
    quiet = e <= np.percentile(e, 15)
    N = P[:, quiet].mean(1, keepdims=True)
    g = np.maximum(1 - 1.6 * N / (P + 1e-20), db(floor_db))
    g = sg.medfilt2d(g, (3, 5))                       # ミュージカルノイズを抑える
    _, y = sg.istft(Z * g, SR, nperseg=2048, noverlap=1536)
    return y[:len(x)]


def biquad(kind, f0, q=0.707, gain_db=0.0):
    A = 10 ** (gain_db / 40)
    w = 2 * math.pi * f0 / SR
    al = math.sin(w) / (2 * q)
    c = math.cos(w)
    if kind == 'hp':
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'lp':
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'peak':
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'hshelf':
        sq = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * c + sq), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sq)]
        a = [(A + 1) - (A - 1) * c + sq, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sq]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def eq(x, *bands):
    for bd in bands:
        b, a = biquad(*bd)
        x = sg.lfilter(b, a, x, axis=0)
    return x


def envelope(x, att, rel):
    """ピーク追従の包絡 (秒)。"""
    ax = np.abs(x) if x.ndim == 1 else np.abs(x).max(1)
    ka, kr = math.exp(-1 / (att * SR)), math.exp(-1 / (rel * SR))
    # 速度のため 64 サンプルごとに処理して補間
    blk = 64
    n = len(ax) // blk + 1
    pk = np.array([ax[i * blk:(i + 1) * blk].max() if i * blk < len(ax) else 0 for i in range(n)])
    ka, kr = ka ** blk, kr ** blk
    out = np.zeros(n)
    v = 0.0
    for i, p in enumerate(pk):
        v = ka * v + (1 - ka) * p if p > v else kr * v + (1 - kr) * p
        out[i] = v
    return np.interp(np.arange(len(ax)), np.arange(n) * blk, out)


def compress(x, thr_db=-24, ratio=3.0, att=0.008, rel=0.18, makeup_db=0.0):
    env = 20 * np.log10(envelope(x, att, rel) + 1e-9)
    over = np.maximum(env - thr_db, 0)
    g = db(-over * (1 - 1 / ratio) + makeup_db)
    return x * (g if x.ndim == 1 else g[:, None])


# ----------------------------------------------------------------------------- space
def make_ir(rt60, seed, length=None, predelay=0.03, damp_hz=5200):
    rng = np.random.default_rng(seed)
    L = int((length or rt60 * 1.3) * SR)
    t = np.arange(L) / SR
    ir = np.zeros((L, 2))
    for c in range(2):
        n = rng.standard_normal(L) * np.exp(-6.91 * t / rt60)
        # 高域ほど早く減衰: 2 帯域に分け、高域の減衰を速く
        lo = sg.lfilter(*biquad('lp', damp_hz), n)
        hi = (n - lo) * np.exp(-6.91 * t / (rt60 * 0.45))
        ir[:, c] = lo + hi
    pd = int(predelay * SR)
    ir = np.vstack([np.zeros((pd, 2)), ir])
    ir[:int(0.004 * SR)] = 0
    # 初期反射
    for d, g, c in [(0.011, .5, 0), (0.017, .45, 1), (0.023, .35, 0), (0.031, .3, 1), (0.043, .22, 0), (0.051, .2, 1)]:
        ir[int(d * SR), c] += g
    return ir / np.sqrt((ir ** 2).sum(0).mean())


def reverb(x_mono_or_st, ir):
    x = x_mono_or_st
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    out = np.zeros((len(x) + len(ir) - 1, 2))
    for c in range(2):
        out[:, c] = sg.fftconvolve(x[:, c], ir[:, c])
    return out


def pan(x, p):
    """定パワーパン p ∈ [-1, 1]。"""
    a = (p + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], 1)


# ----------------------------------------------------------------------------- phrase segmentation
def phrases(x):
    hop = 441
    n = len(x) // hop
    e = 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, 1)) + 1e-9)
    act = e > np.percentile(e, 10) + 12
    segs, st = [], None
    for i, a in enumerate(act):
        if a and st is None:
            st = i
        if not a and st is not None:
            segs.append([st, i]); st = None
    if st is not None:
        segs.append([st, n])
    m = []
    for s in segs:                        # 0.35 秒未満の隙間は同じ発話
        if m and s[0] - m[-1][1] < 35:
            m[-1][1] = s[1]
        else:
            m.append(s)
    m = [s for s in m if s[1] - s[0] > 15]
    ph = []
    for s in m:                           # 1 秒未満の隙間は同じフレーズ
        if ph and s[0] - ph[-1][1] < 100:
            ph[-1][1] = s[1]
        else:
            ph.append(list(s))
    return [(a * hop / SR, b * hop / SR) for a, b in ph]


def cut(x, a, b, pre=0.12, post=0.30):
    i0, i1 = max(0, int((a - pre) * SR)), min(len(x), int((b + post) * SR))
    y = x[i0:i1].copy()
    fi, fo = int(0.02 * SR), int(0.18 * SR)
    y[:fi] *= np.linspace(0, 1, fi)
    y[-fo:] *= np.linspace(1, 0, fo) ** 2
    return y, a - (i0 / SR)               # 発話の頭がクリップ先頭から何秒後か


# ----------------------------------------------------------------------------- arrangement
def ceil_bar(t):
    return math.ceil(t / BAR - 1e-9) * BAR


def arrange(ph, total):
    """フレーズ (録音順) を小節頭へ割り付ける。戻り値: [(phrase_idx, onset_sec, section)]"""
    n = len(ph)
    lens = [b - a for a, b in ph]
    plan = []
    # I: 8 小節はピアノだけ、以後 4 小節ごと
    i, t = 0, 32.0
    while i < n and t + lens[i] <= 166:
        plan.append((i, t, 'I')); t += 4 * BAR; i += 1
    # II: 3 小節ごと (長いフレーズはそのぶん後ろへ)
    t = 168.0
    while i < n:
        need = max(3 * BAR, ceil_bar(lens[i] + 1.0))
        if t + lens[i] > 318:
            break
        plan.append((i, t, 'II')); t += need; i += 1
    # III: 残り (最後の 1 つを除く) を頂点の 248 秒に均して置く。各フレーズは 3 声のカノンで +4 秒伸びる
    rest = list(range(i, n - 1))
    t0, t1 = 320.0, 556.0
    need = [ceil_bar(lens[k] + 4.0 + 1.0) for k in rest]
    last = t1 - need[-1] if rest else t0
    t = t0
    for j, (k, nd) in enumerate(zip(rest, need)):
        ideal = t0 + (last - t0) * j / max(1, len(rest) - 1)
        t = max(t, round(ideal / BAR) * BAR)
        plan.append((k, t, 'III')); t += nd
    # IV: 最後のフレーズを段落の頭から 2 小節目に置き、エコーで溶かす
    plan.append((n - 1, 568.0 + 2 * BAR, 'IV'))
    return plan


# ----------------------------------------------------------------------------- main
def loudnorm(inp, out_wav, target=-16.0, tp=-1.0):
    af = f'loudnorm=I={target}:TP={tp}:LRA=11:print_format=json'
    r = subprocess.run([ffmpeg(), '-hide_banner', '-i', inp, '-af', af, '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    af2 = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
           f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run([ffmpeg(), '-v', 'error', '-y', '-i', inp, '-af', af2, '-ar', str(SR), '-c:a', 'pcm_s24le', out_wav],
                   check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('piano', help='ピアノ (動画 MP4 か音声)')
    ap.add_argument('voice', help='声の録音')
    ap.add_argument('-o', '--out', default='mantra_mix')
    ap.add_argument('--no-video', action='store_true')
    args = ap.parse_args()

    print('decode …')
    piano = decode(args.piano, 2)
    voice = decode(args.voice, 1)
    voice -= voice.mean()
    total = len(piano) / SR

    print('voice: denoise / eq / compress …')
    v = denoise(voice)
    v = eq(v, ('hp', 85, 0.7), ('peak', 260, 1.0, -2.5), ('peak', 3200, 0.9, 3.0), ('hshelf', 9000, 0.7, -2.0))
    v = v / (np.abs(v).max() + 1e-12) * db(-6)
    v = compress(v, thr_db=-26, ratio=3.0, makeup_db=6)

    ph = phrases(voice)
    plan = arrange(ph, total)
    print(f'{len(ph)} phrases')

    L = len(piano) + int(20 * SR)
    dry = np.zeros((L, 2))       # 声 (ドライ)
    send = np.zeros((L, 2))      # 声 → リバーブへの送り
    key = np.zeros(L)            # ダッキング用キー

    # 段落ごとの距離感: (声の大きさ = その段落のピアノの RMS に対する dB, 残響への送り = ドライに対する dB, lowpass Hz)
    look = {'I': (-4.0, 0.0, 4200), 'II': (-0.5, -5.0, 7000), 'III': (1.5, -8.0, 12000), 'IV': (-2.5, -1.0, 5000)}

    def rms_db(x):
        return 10 * np.log10(np.mean(x ** 2) + 1e-20)
    v_rms = rms_db(np.concatenate([v[int(a * SR):int(b * SR)] for a, b in ph]))
    pm = piano.mean(1)
    sec_rms = {}
    for name, a, b in SECTIONS:
        seg = pm[int(a * SR):int((b or total) * SR)]
        seg = seg[int(2 * SR):-int(2 * SR)] if len(seg) > 8 * SR else seg
        sec_rms[name] = rms_db(seg)

    for k, onset, sec in plan:
        clip, lead = cut(v, *ph[k])
        rel, send_rel, lp = look[sec]
        dry_db = sec_rms[sec] + rel - v_rms
        send_db = dry_db + send_rel
        c = eq(clip, ('lp', lp, 0.7))
        voices = [(0.0, 0.0, 0.0)]                      # (遅れ秒, パン, dB)
        if sec == 'III':
            voices += [(2.0, -0.55, -6.0), (4.0, 0.55, -9.0)]   # a tre: 同じ声の 2 拍後・4 拍後
        if sec == 'IV':
            voices += [(BAR * j, (-0.4 if j % 2 else 0.4), -5.0 * j) for j in range(1, 6)]  # 小節ごとのエコー
        for dly, p, g in voices:
            s = int((onset + dly - lead) * SR)
            cc = c if dly == 0 else eq(c, ('lp', 3500 if sec == 'IV' else 6000, 0.7), ('hp', 180, 0.7))
            st = pan(cc, p) * db(g)
            e = min(L, s + len(cc))
            dry[s:e] += st[:e - s] * db(dry_db) * (1.0 if dly == 0 or sec == 'III' else 0.55)
            send[s:e] += st[:e - s] * db(send_db) * (1.0 if dly == 0 else 1.6)
            if dly == 0:
                key[s:e] += np.abs(cc[:e - s])
        print(f'  {sec:>3}  {onset:6.1f}s  phrase {k + 1:2d}  ({ph[k][1] - ph[k][0]:4.1f}s)')

    print('space …')
    ir_v = make_ir(3.4, 1)
    ir_p = make_ir(2.6, 2, damp_hz=4200)
    vw = reverb(send, ir_v)[:L]
    pw = np.zeros((L, 2))
    r = reverb(piano * db(-14), ir_p)[:L]
    pw[:len(r)] = r              # ピアノもごく薄く同じ部屋へ

    print('ducking …')
    env = envelope(key, 0.03, 0.9)
    env = env / (env.max() + 1e-12)
    duck = db(-3.5 * np.clip(env * 6, 0, 1))             # 声の間だけ最大 −3.5 dB
    P = np.zeros((L, 2))
    P[:len(piano)] = piano
    P = P * duck[:, None] + pw

    mix = P + dry + vw
    mix = eq(mix, ('hp', 30, 0.7))
    # 末尾: ピアノの終わり + 6 秒の残響まで
    end = len(piano) + int(6 * SR)
    mix = mix[:end]
    fo = int(6 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    mix = mix / np.abs(mix).max() * db(-3)

    tmp = args.out + '.pre.wav'
    sf.write(tmp, mix.astype(np.float32), SR, subtype='FLOAT')
    print('master (loudnorm) …')
    loudnorm(tmp, args.out + '.wav')
    subprocess.run([ffmpeg(), '-v', 'error', '-y', '-i', args.out + '.wav', '-c:a', 'libmp3lame', '-b:a', '320k',
                    '-metadata', 'title=Requiem BADA — CLVII · Mantra a tre nel 06:39 (voice mix)', args.out + '.mp3'],
                   check=True)
    if not args.no_video:
        # 映像は元のまま (再エンコードなし)、末尾の残響ぶんは最後のコマを延ばす
        subprocess.run([ffmpeg(), '-v', 'error', '-y', '-i', args.piano, '-i', args.out + '.wav',
                        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                        '-shortest', '-movflags', '+faststart', args.out + '.mp4'], check=True)
    import os
    os.remove(tmp)
    print('done:', args.out + '.{wav,mp3' + ('' if args.no_video else ',mp4') + '}')


if __name__ == '__main__':
    main()
