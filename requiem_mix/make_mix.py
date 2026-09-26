#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bada Requiem — 「requiem と fuga の曲調で、ミックスで、requiem の曲を作り換える」

提出された 8 本の録音(source/*.mp3 — Android 録音 / モノラル AAC)だけを素材に、
  * requiem 側(遅く・暗い・低い録音)を主題として、
  * fuga 側 (音数が多く・明るい録音)を対旋律として、
フーガの提示部の形(主題 → 完全 5 度上の応答 → 1 オクターブ下の第 3 声)で
時間差をつけて重ね、聖堂風の残響とオルガン風ドローン(F・B♭・E♭・C♯)を
足して 1 本のレクイエムに作り換え、MP4(H.264 + AAC, ビジュアライザ付き)
として書き出します。ドローンの音も録音の解析(主題の調 = F 短調)から取ります。

使い方:
    python3 requiem_mix/make_mix.py                       # source/ の録音から output/ へ
    python3 requiem_mix/make_mix.py --src <録音フォルダ>  # 別の場所の録音を使う

必要なもの: ffmpeg(rubberband フィルタ入り)・numpy・scipy
"""
import argparse
import glob
import os
import subprocess
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100

# ---------------------------------------------------------------- 素材の割り当て
# 録音名(タイムスタンプ)→ 役割。解析(鍵・テンポ・音の密度・スペクトル重心)から決めた。
REQUIEM = {  # 遅く・暗い・低い(スペクトル重心 ≈ 500–600 Hz、0.5 音/秒)
    "A": "20260925_124643",  # F / B♭ 系、静かな導入と終結を持つ
    "B": "20260924_084937",  # F 短調が中心、いちばん重い
    "C": "20260924_085314",  # B 短調 / D 長調、旋律的
}
FUGA = {  # 音数が多く・明るい(スペクトル重心 ≈ 1000–1500 Hz、1.1 音/秒)
    "X": "20260924_112131",  # いちばん明るい、F 系
    "Y": "20260924_111846",  # 動きの多い中声域
    "Z": "20260925_125053",  # 長い、G / D 系
}

# ドローン — 録音の解析から: 主題(requiem B)は F 短調、導入(requiem A)は F / B♭。
#   F 短調の主音 F・属音 C・下属音 B♭・第 3 音 A♭・第 7 音 E♭ を楽章ごとに使う。
DRONE_NOTES = {"F2": 87.31, "Ab2": 103.83, "Bb2": 116.54, "C3": 130.81, "Eb3": 155.56}


# ---------------------------------------------------------------- 低レベル
def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd)}")


def find_source(src_dir, stamp):
    hits = sorted(glob.glob(os.path.join(src_dir, f"*{stamp}*")))
    if not hits:
        raise SystemExit(f"録音が見つかりません: {stamp} (in {src_dir})")
    return hits[0]


def clip(src, start, dur, cache, semitones=0.0, tempo=1.0):
    """ffmpeg で切り出し + rubberband(ピッチ / テンポ) → float32 モノラル."""
    key = f"{os.path.basename(src)}_{start}_{dur}_{semitones}_{tempo}.wav"
    path = os.path.join(cache, key)
    if not os.path.exists(path):
        af = ["aformat=channel_layouts=mono"]
        if semitones or tempo != 1.0:
            af.append(f"rubberband=pitch={2 ** (semitones / 12.0):.6f}:tempo={tempo}:pitchq=quality")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", src,
             "-af", ",".join(af), "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", path])
    sr, x = wavfile.read(path)
    assert sr == SR
    return x.astype(np.float32) / 32768.0


def db(g):
    return 10 ** (g / 20.0)


def fade(x, fin, fout):
    x = x.copy()
    n = len(x)
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a, dtype=np.float32) ** 1.5
    if b:
        x[n - b:] *= np.linspace(1, 0, b, dtype=np.float32) ** 1.5
    return x


def hp(x, fc):
    return sosfilt(butter(2, fc, "highpass", fs=SR, output="sos"), x).astype(np.float32)


def lp(x, fc):
    return sosfilt(butter(2, fc, "lowpass", fs=SR, output="sos"), x).astype(np.float32)


def drone(notes, dur, gain_db, attack=8.0, release=10.0):
    """オルガン風ドローン(倍音 4 つ・ゆっくりした揺れ)."""
    t = np.arange(int(dur * SR), dtype=np.float32) / SR
    y = np.zeros_like(t)
    for i, f0 in enumerate(notes):
        vib = 1 + 0.002 * np.sin(2 * np.pi * (0.13 + 0.05 * i) * t)
        for h, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.10)):
            y += a * np.sin(2 * np.pi * f0 * h * vib * t + i)
    y /= np.abs(y).max() + 1e-9
    return fade(y * db(gain_db), attack, release)


def cathedral_ir(rt60=3.6, predelay=0.025):
    """聖堂風インパルス応答(左右で別の雑音 → 広がりのあるステレオ残響)."""
    rng = np.random.default_rng(7)
    n = int((rt60 + 0.5) * SR)
    t = np.arange(n) / SR
    env = np.exp(-6.908 * t / rt60).astype(np.float32)
    irs = []
    for _ in range(2):
        noise = rng.standard_normal(n).astype(np.float32)
        noise = lp(noise, 3800)
        ir = noise * env
        pre = np.zeros(int(predelay * SR), dtype=np.float32)
        irs.append(np.concatenate([pre, ir]))
    ir = np.stack(irs, axis=1)
    # チャンネルごとにエネルギー正規化(定常音に対して wet ≈ dry × send 量になる)
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))


class Mixer:
    def __init__(self, total):
        n = int(total * SR)
        self.dry = np.zeros((n, 2), np.float32)
        self.send = np.zeros((n, 2), np.float32)

    def place(self, x, at, gain_db=0.0, pan=0.0, send_db=-12.0):
        """pan: -1(左)〜+1(右)."""
        s = int(at * SR)
        e = min(s + len(x), len(self.dry))
        x = x[: e - s] * db(gain_db)
        th = (pan + 1) * np.pi / 4
        l, r = np.cos(th), np.sin(th)
        self.dry[s:e, 0] += x * l
        self.dry[s:e, 1] += x * r
        w = db(send_db)
        self.send[s:e, 0] += x * l * w
        self.send[s:e, 1] += x * r * w

    def render(self):
        ir = cathedral_ir()
        wet = np.stack([fftconvolve(self.send[:, c], ir[:, c])[: len(self.dry)] for c in range(2)], axis=1)
        y = self.dry + wet.astype(np.float32)
        # ゆるいソフトリミッタ
        y = np.tanh(y * 1.2) / np.tanh(1.2)
        return y / (np.abs(y).max() + 1e-9) * db(-1.0)


# ---------------------------------------------------------------- 構成
SECTIONS = [  # (開始秒, 表示名)
    (0, "I.  Introitus — 入祭唱"),
    (52, "II.  Fuga — 主題・応答・第三声"),
    (120, "III.  Dies irae — ストレッタ"),
    (184, "IV.  Lacrimosa — 涙の日"),
    (242, "V.  Lux aeterna — 永遠の光"),
]
TOTAL = 296.0


def build(src_dir, cache):
    S = {k: find_source(src_dir, v) for k, v in {**REQUIEM, **FUGA}.items()}
    m = Mixer(TOTAL)

    # I. Introitus (0–52): requiem A の静かな導入 + ドローン F・B♭
    m.place(drone([DRONE_NOTES["F2"], DRONE_NOTES["Bb2"]], 60, -20), 0, send_db=-9)
    m.place(fade(clip(S["A"], 30, 52, cache), 5, 6), 2, gain_db=-1, send_db=-7)

    # II. Fuga (52–120): requiem B(F 短調)の主題 →
    #   応答 = 完全 5 度上(+7)を 8 秒遅れ / 第三声 = 1 オクターブ下(−12)を 16 秒遅れ
    subj = fade(clip(S["B"], 60, 66, cache), 3, 6)
    ans = fade(hp(clip(S["B"], 60, 66, cache, semitones=+7), 250), 3, 6)
    bass = fade(lp(clip(S["B"], 60, 66, cache, semitones=-12), 900), 3, 6)
    m.place(subj, 50, gain_db=-1, pan=0.0, send_db=-12)
    m.place(ans, 58, gain_db=-7, pan=-0.6, send_db=-11)
    m.place(bass, 66, gain_db=-5, pan=+0.6, send_db=-13)
    m.place(drone([DRONE_NOTES["F2"], DRONE_NOTES["C3"]], 80, -26, attack=12, release=12), 50, send_db=-9)

    # III. Dies irae (120–186): fuga 側 X・Y を近い間隔で重ね(ストレッタ)、
    #   requiem C を下支えに。X はテンポを 1.08 倍に。
    x = fade(clip(S["X"], 6, 66, cache, tempo=1.08), 4, 6)
    y = fade(hp(clip(S["Y"], 34, 62, cache, semitones=-5), 180), 4, 6)
    c = fade(lp(clip(S["C"], 120, 70, cache), 1600), 6, 8)
    m.place(x, 118, gain_db=-2, pan=-0.35, send_db=-16)
    m.place(y, 122, gain_db=-7, pan=+0.35, send_db=-14)
    m.place(c, 120, gain_db=-7, pan=0.0, send_db=-10)

    # IV. Lacrimosa (184–242): requiem A を 0.85 倍に引き延ばし、深い残響 +
    #   F 短調の主和音 F・A♭ と第 7 音 E♭ のドローン
    lac = fade(clip(S["A"], 150, 55, cache, tempo=0.85), 5, 7)  # ≈ 64.7 秒
    m.place(lac, 182, gain_db=-2, pan=0.0, send_db=-5)
    m.place(drone([DRONE_NOTES["F2"], DRONE_NOTES["Ab2"], DRONE_NOTES["Eb3"]], 66, -24, 10, 12), 182, send_db=-8)

    # V. Lux aeterna (242–296): fuga Z の明るい高声(+12)を遠くに、requiem B の
    #   冒頭を 0.8 倍で下に敷き、ドローン F・C で閉じる
    lux_hi = fade(hp(clip(S["Z"], 240, 24, cache, semitones=+12), 600), 6, 8)  # 24 秒
    lux_lo = fade(clip(S["B"], 30, 42, cache, tempo=0.8), 6, 14)  # ≈ 52.5 秒
    m.place(lux_hi, 238, gain_db=-14, pan=+0.5, send_db=-6)
    m.place(lux_lo, 238, gain_db=-3, pan=0.0, send_db=-6)
    m.place(drone([DRONE_NOTES["F2"], DRONE_NOTES["C3"]], 56, -22, 10, 16), 238, send_db=-8)
    return m.render()


def write_video(master_wav, out_mp4, font):
    """showcqt ビジュアライザ + 楽章名の字幕 → MP4."""
    def esc(s):
        return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    draw = []
    for i, (t0, name) in enumerate(SECTIONS):
        t1 = SECTIONS[i + 1][0] if i + 1 < len(SECTIONS) else TOTAL
        draw.append(
            f"drawtext=fontfile={font}:text='{esc(name)}':x=(w-text_w)/2:y=h-58:fontsize=30:"
            f"fontcolor=white@0.85:enable='between(t,{t0},{t1})'"
        )
    title = (f"drawtext=fontfile={font}:text='Bada Requiem  —  requiem × fuga mix':"
             f"x=(w-text_w)/2:y=26:fontsize=40:fontcolor=0xE9DDB8@0.95")
    fc = (
        "[0:a]showcqt=s=1280x560:fps=25:count=6:bar_g=2.5:sono_g=4:axis=0:"
        "cscheme=0.9|0.55|0.2|0.75|0.85|1[cq];"
        "color=c=0x07070D:s=1280x720:r=25[bg];"
        "[bg][cq]overlay=0:84:shortest=1[v0];"
        "[v0]" + ",".join([title] + draw) + "[v]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", master_wav, "-filter_complex", fc,
         "-map", "[v]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "28", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_mp4])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--src", default=os.path.join(here, "source"), help="提出された録音(*.mp3)のフォルダ")
    ap.add_argument("--out", default=os.path.join(here, "output"), help="出力フォルダ")
    ap.add_argument("--cache", default=None, help="切り出し済み素材のキャッシュ(既定: <out>/cache)")
    ap.add_argument("--font", default="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf")
    ap.add_argument("--name", default="requiem_fuga_mix")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cache = a.cache or os.path.join(a.out, "cache")
    os.makedirs(cache, exist_ok=True)

    y = build(a.src, cache)
    wav = os.path.join(cache, a.name + ".wav")
    wavfile.write(wav, SR, (y * 32767).astype(np.int16))
    mp4 = os.path.join(a.out, a.name + ".mp4")
    write_video(wav, mp4, a.font)
    print("wrote", mp4, f"({os.path.getsize(mp4) / 1e6:.1f} MB, {len(y) / SR:.0f} s)")


if __name__ == "__main__":
    main()
