"""共通ユーティリティ: 日本語フォント, 配色, ffmpeg への並列フレーム書き出し, 効果音合成."""
import os
import subprocess
import wave
from multiprocessing import Pool

import logging

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

for f in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",):
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["IPAGothic", "DejaVu Sans"]
plt.rcParams["mathtext.fontset"] = "dejavusans"
plt.rcParams["axes.unicode_minus"] = False

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

# 設計図風の配色 (元レポートの濃紺 + シアン系に合わせる)
BG = "#0b2447"
GRID = "#2b4a7a"
FG = "#e8f1ff"
C = {
    "ring": "#f5b942", "pod": "#ffffff", "tower": "#b8c7e0", "j31": "#7fb2ff",
    "j51": "#c28bff", "j41": "#4fd6e0", "axis": "#ff6b5b", "window": "#ffa040",
    "well": "#5a7bb0", "hud": "#9fe8ff", "warn": "#ffd166",
}

W, H, FPS = 1280, 720, 30


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def new_fig():
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
    return fig


def fig_to_rgb(fig):
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    return buf.copy()


def write_wav(path, samples, sr=44100):
    s = np.clip(samples, -1, 1)
    data = (s * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def render_video(path, n_frames, frame_fn, audio_wav=None, workers=None, chunk=8):
    """frame_fn(i) -> HxWx3 uint8. フレームを並列生成し H.264 mp4 に書き出す."""
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio_wav:
        cmd += ["-i", audio_wav, "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium",
            "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(workers or os.cpu_count()) as pool:
        for k, img in enumerate(pool.imap(frame_fn, range(n_frames), chunksize=chunk)):
            proc.stdin.write(img.tobytes())
            if k % 150 == 0:
                print(f"  frame {k}/{n_frames}", flush=True)
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        raise RuntimeError("ffmpeg failed")


class Timeline:
    """シーン名 → (開始秒, 長さ秒)."""

    def __init__(self, scenes):
        self.scenes = []
        t = 0.0
        for name, dur in scenes:
            self.scenes.append((name, t, dur))
            t += dur
        self.total = t

    def at(self, sec):
        for name, t0, dur in self.scenes:
            if sec < t0 + dur:
                return name, (sec - t0) / dur, sec - t0
        name, t0, dur = self.scenes[-1]
        return name, 1.0, dur

    def start(self, name):
        for n, t0, _ in self.scenes:
            if n == name:
                return t0
        raise KeyError(name)
