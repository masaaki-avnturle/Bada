"""
video.py — 完成した WAV から MP4 を作る。

ffmpeg の overlay/blend には頼らず、numpy で 1 フレームずつ描画して
rawvideo を libx264 にパイプする(依存: numpy / Pillow / ffmpeg)。

  背景  : 静かな藍色のグラデーション + 地平線(鉄路の記憶)
  可視化: 対数周波数 64 本のスペクトラム(楽章ごとに色温度が変わる — 短調は青紫、長調は琥珀)
  文字  : 冒頭のタイトルと各楽章のカード(IPA ゴシック)
"""
import os
import sys
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.io import wavfile

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(__file__), "out"))
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
W, H, FPS = 1280, 720, 30
NBARS = 64

MOVEMENTS = [
    ("prelude", "I. 前奏 — 瞑想", "Prelude · A minor", "ドローンと主題の拡大形。録音の記憶が霧のように。", (120, 130, 220)),
    ("fugue", "II. フーガ", "Fuga a 3 voci · in the manner of J. S. Bach", "主題 → 応答 → 対主題 → 嬉遊部 → 中間部 → ストレッタ → ピカルディ終止", (140, 120, 230)),
    ("requiem", "III. レクイエム — パッサカリア", "Requiem · Passacaglia on a chromatic lament bass", "半音階で下る嘆きのバスの上に、合唱と弦の哀歌", (110, 90, 200)),
    ("chorale", "IV. コラール — ほっと一安心", "Ave verum corpus 様式 · F major", "E7 → F の偽終止。光が差し込む。", (235, 190, 110)),
    ("ballad", "V. バラード — 郷愁", "Ballad · in the manner of Ryuichi Sakamoto (Sweet Revenge / 鉄道員)", "ピアノと弦。鉄路の彼方へ。", (220, 170, 120)),
    ("coda", "VI. コーダ — 受容", "Coda · Acceptance (Little Buddha) 様式の瞑想", "静かに息を吐く。", (200, 180, 150)),
]


def font(size):
    return ImageFont.truetype(FONT, size)


def background():
    y = np.linspace(0, 1, H)[:, None]
    r = 6 + 14 * (1 - y) ** 2
    g = 9 + 20 * (1 - y) ** 1.5
    b = 28 + 56 * (1 - y)
    img = np.concatenate([np.broadcast_to(r, (H, W))[..., None], np.broadcast_to(g, (H, W))[..., None],
                          np.broadcast_to(b, (H, W))[..., None]], axis=2).astype(np.float32)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse([W // 2 - 420, 120, W // 2 + 420, 620], fill=(30, 36, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = np.clip(img + np.asarray(glow).astype(np.float32), 0, 255)
    pil = Image.fromarray(img.astype(np.uint8))
    d = ImageDraw.Draw(pil)
    d.line([(0, 470), (W, 470)], fill=(60, 70, 120), width=1)
    for x in range(0, W, 64):
        d.line([(x, 470), (x + 32, 470)], fill=(110, 120, 170), width=2)
    d.text((40, 24), "Bada Fusion Suite", font=font(26), fill=(200, 190, 150))
    d.text((40, 58), "Fuga · Requiem · Ave Verum · Acceptance", font=font(18), fill=(140, 140, 170))
    return np.asarray(pil).astype(np.float32)


def card(title, sub, note, big=False):
    img = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if big:
        d.text((W // 2, 60), title, font=font(60), fill=(240, 232, 200, 255), anchor="mm")
        d.text((W // 2, 130), sub, font=font(30), fill=(190, 190, 215, 255), anchor="mm")
        d.text((W // 2, 190), note, font=font(22), fill=(150, 150, 180, 255), anchor="mm")
    else:
        d.text((W // 2, 55), title, font=font(46), fill=(240, 232, 200, 255), anchor="mm")
        d.text((W // 2, 115), sub, font=font(26), fill=(190, 190, 215, 255), anchor="mm")
        d.text((W // 2, 165), note, font=font(22), fill=(150, 150, 180, 255), anchor="mm")
    a = np.asarray(img).astype(np.float32)
    return a[..., :3], a[..., 3:4] / 255.0


def spectrum_frames(x, sr, n_frames):
    """各フレームの 64 バンド(対数周波数)振幅。"""
    mono = x.mean(axis=1) if x.ndim == 2 else x
    N = 4096
    win = np.hanning(N).astype(np.float32)
    freqs = np.fft.rfftfreq(N, 1 / sr)
    edges = np.geomspace(40, 8000, NBARS + 1)
    idx = np.searchsorted(freqs, edges)
    bars = np.zeros((n_frames, NBARS), dtype=np.float32)
    for f in range(n_frames):
        c = int(f / FPS * sr)
        seg = mono[max(0, c - N // 2): c + N // 2]
        if len(seg) < N:
            seg = np.pad(seg, (0, N - len(seg)))
        S = np.abs(np.fft.rfft(seg * win))
        for i in range(NBARS):
            a, b = idx[i], max(idx[i + 1], idx[i] + 1)
            bars[f, i] = S[a:b].max()
    bars = np.log1p(bars * 4) / np.log1p(4 * bars.max() + 1e-9)
    # 立ち上がりは速く、減衰はゆっくり(穏やかな見た目)
    out = np.zeros_like(bars)
    prev = np.zeros(NBARS, dtype=np.float32)
    for f in range(n_frames):
        prev = np.maximum(bars[f], prev * 0.90 + bars[f] * 0.10)
        out[f] = prev
    return out


def movement_color(t, marks):
    keys = [m[0] for m in MOVEMENTS]
    starts = [marks[k] for k in keys]
    cols = [np.array(m[4], dtype=np.float32) for m in MOVEMENTS]
    # 楽章の境目 6 秒でクロスフェード
    for i in range(len(keys) - 1, -1, -1):
        if t >= starts[i]:
            c = cols[i]
            if i > 0 and t - starts[i] < 6:
                f = (t - starts[i]) / 6
                c = cols[i - 1] * (1 - f) + c * f
            return c
    return cols[0]


def main(wav, mp4):
    marks = json.load(open(os.path.join(OUT, "marks.json")))
    total = marks["end"]
    n_frames = int(total * FPS)
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32) / 32768
    print("spectrum...")
    bars = spectrum_frames(x, sr, n_frames)
    bg = background()

    cards = []
    rgb, a = card("Bada Fusion Suite", "Fuga · Requiem · Ave Verum · Acceptance",
                  "バッハ / モーツァルト様式 × 坂本龍一様式 × 16 本の録音", big=True)
    cards.append((rgb, a, 0.5, 10.5))
    for key, title, sub, note, _ in MOVEMENTS:
        rgb, a = card(title, sub, note)
        st = marks[key] + (11.5 if key == "prelude" else 0.5)
        cards.append((rgb, a, st, st + 9.0))

    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-map", "0:v", "-map", "1:a", "-t", f"{total:.2f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           "-metadata", "title=Bada Fusion Suite — Fuga · Requiem · Ave Verum · Acceptance", mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    bar_w = W / NBARS
    base_y, max_h = 690, 250
    print("frames...")
    for f in range(n_frames):
        t = f / FPS
        frame = bg.copy()
        col = movement_color(t, marks)
        # スペクトラム(下部)と、地平線上の淡い反射
        for i in range(NBARS):
            h = int(bars[f, i] * max_h)
            if h <= 0:
                continue
            x0 = int(i * bar_w + 3)
            x1 = int((i + 1) * bar_w - 3)
            grad = np.linspace(0.35, 1.0, h, dtype=np.float32)[:, None, None]
            frame[base_y - h:base_y, x0:x1] = frame[base_y - h:base_y, x0:x1] * (1 - 0.85 * grad) + col * 0.85 * grad
            rh = h // 3
            if rh > 0:
                rg = np.linspace(0.25, 0.0, rh, dtype=np.float32)[:, None, None]
                frame[470 - rh:470, x0:x1] = frame[470 - rh:470, x0:x1] * (1 - rg) + col * rg
        # タイトルカード
        for rgb, alpha, st, en in cards:
            if st <= t < en:
                fade = min(1.0, (t - st) / 1.5, (en - t) / 1.5)
                al = alpha * fade
                frame[150:410] = frame[150:410] * (1 - al) + rgb * al
        # 全体フェード
        g = min(1.0, t / 2.0, max(0.0, (total - t) / 4.0))
        if g < 1.0:
            frame *= g
        proc.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if f % (FPS * 30) == 0:
            print(f"  {t:6.1f}s / {total:.1f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", mp4)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
