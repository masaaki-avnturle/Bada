#!/usr/bin/env python3
"""requiem_video.py — レクイエム調ピアノ曲のための動画を生成する。

暗い聖堂のような背景・ろうそくの灯り・舞い上がる灰・演奏に合わせて光る 88 鍵の鍵盤に、
写真(任意・複数可)をゆっくり動かしながら重ねる。

使い方:
  python3 requiem_video.py --audio requiem.wav --events requiem.wav.events.json \
      --photo photo1.jpg photo2.jpg --out requiem.mp4 [--size 1280x720] [--fps 24] [--ffmpeg /path/ffmpeg]

写真を渡さないときは、ぼかしたろうそくの灯り(ボケ)だけの背景になる。
依存: numpy, pillow, ffmpeg(PATH か --ffmpeg で指定)
"""
import argparse, json, math, os, random, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts", "C:/Windows/Fonts", "/Library/Fonts"]


def find_font(names, size):
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def audio_duration(ffmpeg, path):
    out = subprocess.run([ffmpeg, "-i", path], capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise SystemExit("音声の長さが読めません: " + path)


def radial(W, H, cx, cy, r, color, power=1.6):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** power
    return a[:, :, None] * np.array(color, np.float32)[None, None, :]


def vignette(W, H, strength=0.85):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return (1 - strength * np.clip(d - 0.35, 0, 1) ** 1.5)[:, :, None]


class Keyboard:
    """88 鍵の鍵盤。演奏イベントに合わせて鍵が金色に灯る。"""
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.kw = int(W * 0.78) // 52
        self.x0 = (W - self.kw * 52) // 2
        self.y0 = H - int(H * 0.115)
        self.wh, self.bh = int(H * 0.095), int(H * 0.058)
        self.white, self.black = [], []
        wi = 0
        for m in range(21, 109):
            pc = m % 12
            if pc in (1, 3, 6, 8, 10):
                self.black.append((m, self.x0 + wi * self.kw - int(self.kw * 0.3)))
            else:
                self.white.append((m, self.x0 + wi * self.kw)); wi += 1

    def draw(self, draw, glow):
        for m, x in self.white:
            g = glow.get(m, 0.0)
            c = (int(52 + 190 * g), int(50 + 150 * g), int(56 + 70 * g))
            draw.rectangle([x + 1, self.y0, x + self.kw - 1, self.y0 + self.wh], fill=c, outline=(20, 20, 24))
        bw = int(self.kw * 0.62)
        for m, x in self.black:
            g = glow.get(m, 0.0)
            c = (int(14 + 210 * g), int(13 + 150 * g), int(16 + 50 * g))
            draw.rectangle([x, self.y0, x + bw, self.y0 + self.bh], fill=c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--photo", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--title", default="Requiem")
    ap.add_argument("--subtitle", default="in F minor  ·  for grand piano")
    ap.add_argument("--ending", default="Requiem aeternam dona eis")
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()
    random.seed(args.seed); rng = np.random.default_rng(args.seed)

    W, H = map(int, args.size.lower().split("x"))
    fps = args.fps
    dur = audio_duration(args.ffmpeg, args.audio)
    n_frames = int(math.ceil(dur * fps))
    meta = json.load(open(args.events))
    events = meta["events"]
    sections = {s["name"]: s["t"] for s in meta.get("sections", [])}
    coda_t = sections.get("coda", dur - 30)

    # ---- 背景(暗い石壁のグラデーション + ろうそくの灯り)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    base = (np.array([10, 9, 14], np.float32) * (1 - y) + np.array([26, 20, 22], np.float32) * y)
    base = np.broadcast_to(base, (H, W, 3)).copy()
    glow_img = radial(W, H, W / 2, H * 1.05, W * 0.62, (120, 66, 22), 2.2)
    glow_top = radial(W, H, W / 2, -H * 0.2, W * 0.55, (22, 26, 48), 2.0)
    vig = vignette(W, H)

    # ---- ボケ(写真が無いときの主役、あるときは奥で瞬く)
    bokeh = []
    for _ in range(14 if not args.photo else 7):
        r = random.randint(int(H * 0.05), int(H * 0.16))
        disc = Image.new("L", (r * 4, r * 4), 0)
        ImageDraw.Draw(disc).ellipse([r, r, 3 * r, 3 * r], fill=255)
        disc = disc.filter(ImageFilter.GaussianBlur(r * 0.45))
        arr = np.asarray(disc, np.float32) / 255.0
        col = np.array(random.choice([(255, 178, 92), (255, 208, 140), (230, 150, 70), (200, 190, 210)]), np.float32)
        bokeh.append(dict(x=random.uniform(0, W), y=random.uniform(H * 0.1, H * 0.85), vx=random.uniform(-4, 4),
                          vy=random.uniform(-6, -1), ph=random.uniform(0, 6.3), sp=random.uniform(0.15, 0.5),
                          arr=arr, col=col * random.uniform(0.10, 0.22)))

    # ---- 灰・埃の粒子
    NP = 160
    px = rng.uniform(0, W, NP); py = rng.uniform(0, H, NP)
    pv = rng.uniform(6, 26, NP); pr = rng.uniform(0.8, 2.6, NP); pb = rng.uniform(0.25, 1.0, NP); pph = rng.uniform(0, 6.3, NP)

    # ---- 写真(ケン・バーンズ効果)
    photos = []
    for p in args.photo:
        im = Image.open(p).convert("RGB")
        s = max(W * 1.25 / im.width, H * 1.25 / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        photos.append(im)
    per_photo = dur / len(photos) if photos else 0
    xfade = 3.0

    def photo_frame(t):
        """時刻 t の写真レイヤー(float RGB)と不透明度"""
        i = min(len(photos) - 1, int(t / per_photo))
        u = (t - i * per_photo) / per_photo
        im = photos[i]
        z = 1.0 + 0.16 * u if i % 2 == 0 else 1.16 - 0.16 * u
        cw, ch = int(W * 1.0 * (1.25 / z)), int(H * 1.0 * (1.25 / z))
        cw, ch = min(cw, im.width), min(ch, im.height)
        cx = (im.width - cw) * (0.5 + 0.25 * math.sin(i * 1.7 + u * 1.2))
        cy = (im.height - ch) * (0.5 + 0.2 * math.cos(i * 0.9 + u * 0.8))
        crop = im.crop((int(cx), int(cy), int(cx) + cw, int(cy) + ch)).resize((W, H), Image.BILINEAR)
        arr = np.asarray(crop, np.float32)
        gray = arr.mean(2, keepdims=True)
        arr = arr * 0.55 + gray * 0.45                        # 色を薄く
        arr = arr * np.array([1.0, 0.92, 0.80], np.float32)   # セピア寄り
        a = 0.72
        if u * per_photo < xfade and i > 0: a *= (u * per_photo) / xfade
        if (1 - u) * per_photo < xfade and i < len(photos) - 1: a *= ((1 - u) * per_photo) / xfade
        return arr, a

    # ---- 鍵盤の点灯スケジュール(フレームごとの残光)
    kb = Keyboard(W, H)
    onsets = [(int(e["t"] * fps), e["p"], min(1.0, e["v"] / 100.0), max(0.15, min(e["d"], 1.4))) for e in events]
    onsets.sort()
    glow = {}

    # ---- 文字
    f_title = find_font(["DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf"], int(H * 0.11))
    f_sub = find_font(["DejaVuSerif-Italic.ttf", "DejaVuSerif.ttf"], int(H * 0.034))
    f_end = find_font(["DejaVuSerif-Italic.ttf", "DejaVuSerif.ttf"], int(H * 0.045))

    def fade(t, a, b, c, d):
        if t < a or t > d: return 0.0
        if t < b: return (t - a) / (b - a)
        if t > c: return (d - t) / (d - c)
        return 1.0

    def text_center(draw, txt, font, cy, alpha, color=(232, 214, 176)):
        if alpha <= 0.01: return
        bb = draw.textbbox((0, 0), txt, font=font)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        col = tuple(int(c * alpha) for c in color)
        draw.text((x + 2, cy + 2), txt, font=font, fill=tuple(int(c * alpha * 0.25) for c in (0, 0, 0)))
        draw.text((x, cy), txt, font=font, fill=col)

    cmd = [args.ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(fps), "-i", "-", "-i", args.audio, "-c:v", "libx264", "-preset", "medium", "-crf", "22",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    oi = 0
    for fi in range(n_frames):
        t = fi / fps
        # 鍵盤の残光を更新
        while oi < len(onsets) and onsets[oi][0] <= fi:
            _, p, v, d = onsets[oi]; glow[p] = max(glow.get(p, 0.0), 0.35 + 0.65 * v); oi += 1
        for p in list(glow):
            glow[p] *= 0.90
            if glow[p] < 0.02: del glow[p]
        energy = min(1.0, sum(glow.values()) / 6.0)

        flick = 0.82 + 0.10 * math.sin(t * 7.3) * math.sin(t * 2.1) + 0.08 * math.sin(t * 13.7 + 1.0) + 0.12 * energy
        img = base + glow_img * flick + glow_top
        # ボケ
        for b in bokeh:
            b["x"] += b["vx"] / fps; b["y"] += b["vy"] / fps
            if b["y"] < -H * 0.2: b["y"] = H * 1.1; b["x"] = random.uniform(0, W)
            tw = 0.6 + 0.4 * math.sin(t * b["sp"] + b["ph"])
            arr = b["arr"]; h, w = arr.shape
            x0, y0 = int(b["x"] - w / 2), int(b["y"] - h / 2)
            xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
            if xb > xa and yb > ya:
                img[ya:yb, xa:xb] += arr[ya - y0:yb - y0, xa - x0:xb - x0, None] * b["col"] * tw
        # 写真
        if photos:
            parr, pa = photo_frame(t)
            img = img * (1 - pa * 0.85) + parr * vig * pa
        img *= vig
        frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        draw = ImageDraw.Draw(frame, "RGBA")
        # 粒子
        py_now = (py - pv * t) % (H + 20) - 10
        px_now = px + 18 * np.sin(t * 0.35 + pph)
        for k in range(NP):
            a = int(140 * pb[k] * (0.6 + 0.4 * math.sin(t * 1.3 + pph[k])))
            r = pr[k]
            draw.ellipse([px_now[k] - r, py_now[k] - r, px_now[k] + r, py_now[k] + r], fill=(255, 220, 170, a))
        # 鍵盤
        kb.draw(draw, glow)
        # 文字
        a_t = fade(t, 2.0, 6.0, 24.0, 30.0)
        text_center(draw, args.title, f_title, int(H * 0.30), a_t)
        text_center(draw, args.subtitle, f_sub, int(H * 0.46), fade(t, 4.0, 8.0, 24.0, 30.0), (190, 176, 150))
        text_center(draw, args.ending, f_end, int(H * 0.40), fade(t, coda_t + 6, coda_t + 12, dur - 4, dur - 0.5), (200, 186, 158))
        # 全体のフェード
        g = min(1.0, t / 2.0, max(0.0, (dur - t) / 3.0))
        if g < 1.0:
            frame = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), frame, g)
        proc.stdin.write(frame.tobytes())
        if fi % (fps * 30) == 0:
            print("  %5.1f%%  t=%.0fs" % (100.0 * fi / n_frames, t), flush=True)
    proc.stdin.close(); proc.wait()
    if proc.returncode != 0:
        raise SystemExit("ffmpeg failed")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
