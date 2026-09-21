#!/usr/bin/env python3
"""Bada Suite — ユーザー自身の素材だけで組曲を編曲して mp4 に書き出す。

構成 (4 秒の等パワー・クロスフェードで接続):
  I.   Ave (SATB MIDI)         … MIDI を合唱シンセ + ピアノ層で新規レンダリング (D-dur)
  II.  Requiem in F minor      … 原音ピアノ + 1 オクターブ下のゴースト層 + ホール残響
  III. Contrapunctus 14        … 同上 (La Japonaise)
  IV.  Coda: 20260920_154001 / 20260920_154118 … 録音 2 本を残響で包む

依存: python3, numpy, scipy, mido, pillow, imageio-ffmpeg (静的 ffmpeg)
使い方: python3 make_suite.py <素材ディレクトリ> <出力ディレクトリ>
"""
import os, sys, subprocess, math
import numpy as np
from scipy.signal import oaconvolve
from scipy.io import wavfile
import mido
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
XF = 4.0          # クロスフェード秒
W, H, FPS = 1280, 720, 30
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
def src(name):
    for f in os.listdir(SRC):
        if f.endswith(name):
            return os.path.join(SRC, f)
    raise FileNotFoundError(name)

# ---------------------------------------------------------------- audio I/O
def load(path, dur=None, af=None):
    cmd = [FF, "-loglevel", "error", "-i", path]
    if dur: cmd += ["-t", str(dur)]
    if af: cmd += ["-af", af]
    cmd += ["-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float32)

def fit(x, n):
    if len(x) >= n: return x[:n]
    return np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])

def save_wav(path, x):
    wavfile.write(path, SR, np.clip(x, -1, 1).astype(np.float32))

# ---------------------------------------------------------------- reverb
def make_ir(rt60=2.6, pre=0.02):
    rng = np.random.default_rng(7)
    n = int(SR * rt60 * 1.1)
    t = np.arange(n) / SR
    env = np.exp(-6.91 * t / rt60)                      # -60 dB at rt60
    ir = rng.standard_normal((n, 2)).astype(np.float32) * env[:, None]
    # 高域を徐々に減衰させる 1 次ローパス
    a = 0.82
    for c in range(2):
        y = np.zeros(n, np.float32); acc = 0.0
        for i in range(n):
            acc = a * acc + (1 - a) * ir[i, c]; y[i] = acc
        ir[:, c] = y
    early = np.zeros((int(SR * pre) + n, 2), np.float32)
    for d, g in ((0.011, 0.5), (0.019, 0.35), (0.031, 0.25)):
        k = int(d * SR); early[k, 0] += g; early[k + 37, 1] += g
    early[int(pre * SR):] += ir
    early /= np.sqrt((early ** 2).sum(0)).max() * 0.5
    return early
IR = make_ir()

def reverb(x, wet=0.22):
    out = np.empty_like(x)
    for c in range(2):
        out[:, c] = oaconvolve(x[:, c], IR[:, c])[:len(x)]
    return x + wet * out

# ---------------------------------------------------------------- utilities
def rms_norm(x, target_db=-20.0):
    r = np.sqrt(np.mean(x ** 2)) + 1e-9
    return x * (10 ** (target_db / 20) / r)

def soft_limit(x, th=0.95):
    y = x.copy(); m = np.abs(y) > th
    y[m] = np.sign(y[m]) * (th + (1 - th) * np.tanh((np.abs(y[m]) - th) / (1 - th)))
    return y

def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    if fin:
        n = int(fin * SR); x[:n] *= np.linspace(0, 1, n)[:, None] ** 2
    if fout:
        n = int(fout * SR); x[-n:] *= np.linspace(1, 0, n)[:, None] ** 2
    return x

def crossfade_concat(parts, xf=XF):
    n = int(xf * SR)
    th = np.linspace(0, np.pi / 2, n, dtype=np.float32)[:, None]
    out = parts[0].copy()
    for p in parts[1:]:
        out[-n:] = out[-n:] * np.cos(th) + p[:n] * np.sin(th)
        out = np.concatenate([out, p[n:]])
    return out

# ---------------------------------------------------------------- I. Ave: MIDI synth
def render_ave(path):
    mid = mido.MidiFile(path)
    tempo = 500000
    for msg in mid.tracks[0]:
        if msg.type == "set_tempo": tempo = msg.tempo
    spt = tempo / 1e6 / mid.ticks_per_beat
    pans = [0.30, 0.42, 0.58, 0.70]           # S A T B の定位 (0=L,1=R)
    total = mid.length + 4.0
    buf = np.zeros((int(total * SR), 2), np.float32)
    formants = [(700, 90), (1150, 110), (2700, 150), (3400, 200)]   # 母音「ア」寄り

    def choir_note(f0, dur, gain):
        n = int((dur + 0.5) * SR); t = np.arange(n) / SR
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.3 * t + 2 * np.pi * np.random.rand()) * np.minimum(1, t / 0.6)
        y = np.zeros(n, np.float32)
        for det in (-7, 0, 7):                # 3 声のデチューン (セント)
            f = f0 * 2 ** (det / 1200)
            for k in range(1, 40):
                fk = f * k
                if fk > 12000: break
                amp = 1.0 / k
                res = sum(g * math.exp(-((fk - fc) / bw) ** 2) for (fc, bw), g in zip(formants, (1.0, 0.7, 0.35, 0.2)))
                amp *= 0.15 + res
                ph = 2 * np.pi * np.random.rand()
                y += (amp * np.sin(2 * np.pi * fk * np.cumsum(vib) / SR + ph)).astype(np.float32)
        env = np.ones(n, np.float32)
        a = int(0.12 * SR); env[:a] = np.linspace(0, 1, a)
        r0 = int(dur * SR); r = n - r0; env[r0:] = np.exp(-np.arange(r) / (0.18 * SR))
        return y * env * gain

    def piano_note(f0, dur, gain):
        n = int(min(dur + 1.5, 6.0) * SR); t = np.arange(n) / SR
        y = np.zeros(n, np.float32)
        for k in range(1, 9):
            fk = f0 * k * (1 + 0.0004 * k * k)
            if fk > 14000: break
            y += ((1 / k ** 1.2) * np.exp(-t * (0.9 + 0.35 * k)) * np.sin(2 * np.pi * fk * t)).astype(np.float32)
        y[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
        return y * gain

    for ti, track in enumerate(mid.tracks):
        tick = 0; on = {}
        for msg in track:
            tick += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on[msg.note] = tick
            elif msg.type in ("note_off", "note_on") and msg.note in on:
                st = on.pop(msg.note) * spt; dur = (tick * spt) - st
                f0 = 440 * 2 ** ((msg.note - 69) / 12)
                c = choir_note(f0, dur, 0.035); p = piano_note(f0, dur, 0.06)
                i0 = int(st * SR); pan = pans[ti]
                for sig, gl, gr in ((c, math.cos(pan * math.pi / 2), math.sin(pan * math.pi / 2)),
                                    (p, math.cos(pan * math.pi / 2), math.sin(pan * math.pi / 2))):
                    j = min(len(sig), len(buf) - i0)
                    buf[i0:i0 + j, 0] += sig[:j] * gl; buf[i0:i0 + j, 1] += sig[:j] * gr
    return buf

# ---------------------------------------------------------------- II/III: ghost octave layer
def ghost(path, dur):
    g = load(path, dur, "rubberband=pitch=0.5:pitchq=quality,lowpass=f=520,adelay=45|45")
    return g

# ---------------------------------------------------------------- build sections
REUSE = os.environ.get("REUSE_AUDIO") == "1" and os.path.exists(os.path.join(OUT, "bada_suite_master.wav"))

def build_audio():
    sec = []
    print("I. Ave")
    ave = fit(render_ave(src("ave_satb.mid")), int(161 * SR))
    ave = rms_norm(reverb(ave, 0.32), -21.0)
    sec.append(("ave", fade(ave, 0.5, 3.0)))

    print("II. Requiem")
    D = 250.0
    req = fit(load(src("requiem_piano.mp3"), D), int(D * SR))
    req = req + 0.16 * fit(ghost(src("requiem_piano.mp3"), D), int(D * SR))
    sec.append(("requiem", fade(rms_norm(reverb(req, 0.20), -20.0), 0.0, 2.0)))

    print("III. Contrapunctus 14")
    D = 141.0
    cp = fit(load(src("La_Japonaise_Contrapunctus14.mp4"), D), int(D * SR))
    cp = cp + 0.14 * fit(ghost(src("La_Japonaise_Contrapunctus14.mp4"), D), int(D * SR))
    sec.append(("contrapunctus", fade(rms_norm(reverb(cp, 0.20), -20.0), 0.0, 2.0)))

    print("IV. Coda")
    for name, D in (("20260920_154001.mp4", 74.0), ("20260920_154118.mp4", 80.5)):
        r = fit(load(src(name), D, "highpass=f=70"), int(D * SR))
        sec.append((name[:-4], fade(rms_norm(reverb(r, 0.26), -21.0), 0.3, 3.0)))

    master = soft_limit(crossfade_concat([x for _, x in sec]))
    master *= 0.97 / (np.abs(master).max() + 1e-9)
    save_wav(os.path.join(OUT, "bada_suite_master.wav"), master)
    save_wav(os.path.join(OUT, "sec_ave.wav"), sec[0][1])
    return master

if REUSE:
    print("reusing audio")
    master = wavfile.read(os.path.join(OUT, "bada_suite_master.wav"))[1]
else:
    master = build_audio()
lens = [161.0, 250.0, 141.0, 74.0, 80.5]
total = len(master) / SR
print("section lengths", lens, "total", total)

# ---------------------------------------------------------------- title cards
def card(path, title, sub="", big=64, alpha_bg=0):
    im = Image.new("RGBA", (W, H), (0, 0, 0, alpha_bg)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, big); f2 = ImageFont.truetype(FONT, 30)
    # 文字の背後に半透明の帯 (明るい映像上でも読めるように)
    top = int(H * 0.40) - 36; bot = int(H * 0.40) + big + (70 if sub else 20)
    d.rectangle([0, top, W, bot], fill=(10, 10, 20, 150))
    w1 = d.textlength(title, font=f1); d.text(((W - w1) / 2, H * 0.40), title, font=f1, fill=(255, 250, 235, 255))
    if sub:
        w2 = d.textlength(sub, font=f2); d.text(((W - w2) / 2, H * 0.40 + big + 24), sub, font=f2, fill=(225, 220, 205, 230))
    im.save(path)

bg = Image.new("RGB", (W, H)); px = bg.load()
for y in range(H):
    for x in range(W):
        v = (x / W) * 0.5 + (y / H) * 0.5
        px[x, y] = (int(14 + 20 * v), int(12 + 16 * v), int(28 + 40 * v))
bg.save(os.path.join(OUT, "bg.png"))

cards = [
    ("card0.png", "Bada Suite", "Ave · Requiem in F minor · Contrapunctus 14 · Coda", 0.0, 7.0),
    ("card1.png", "I. Ave (SATB)", "MIDI から合唱シンセ + ピアノで新規レンダリング", 8.0, 14.0),
    ("card2.png", "II. Requiem in F minor", "ピアノ + オクターブ下のゴースト層 + ホール残響", 0, 0),
    ("card3.png", "III. Contrapunctus 14 — La Japonaise", "同編成", 0, 0),
    ("card4.png", "IV. Coda", "20260920_154001 / 20260920_154118", 0, 0),
    ("card5.png", "Bada Suite", "素材はすべてアップロードされた自作音源・MIDI から編曲", 0, 0),
]
starts = [0]
for L in lens[:-1]: starts.append(starts[-1] + L - XF)
cards[2] = cards[2][:3] + (starts[1] + 1, starts[1] + 7)
cards[3] = cards[3][:3] + (starts[2] + 1, starts[2] + 7)
cards[4] = cards[4][:3] + (starts[3] + 1, starts[3] + 7)
cards[5] = cards[5][:3] + (total - 9, total - 1)
for fn, t, s, a, b in cards:
    card(os.path.join(OUT, fn), t, s, big=(72 if fn in ("card0.png", "card5.png") else 56))

# ---------------------------------------------------------------- video
# 1) 各楽章を個別にレンダリング (タイトルカードは表示時間ぶんだけ読み込む)
# 2) 5 本を xfade で連結してマスター音声を載せる
L = lens
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]

def norm(idx):
    return (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:-1:-1,"
            f"fps={FPS},format=yuv420p")

def card_inputs(cards_local):
    """cards_local: [(png, start, end)] → (inputs, filter parts, first card input index offset needed)"""
    ins, parts = [], []
    for k, (fn, a, b) in enumerate(cards_local):
        d = b - a
        ins += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", os.path.join(OUT, fn)]
        parts.append((k, a, b))
    return ins, parts

def render_section(name, main_inputs, main_filter, dur, cards_local):
    """main_filter は [vmain] を出す。cards_local は楽章内時刻。"""
    ci = len(main_inputs) // 2  # -i の数 (単純な "-i path" 入力のみを想定)
    ci = sum(1 for x in main_inputs if x == "-i")
    cins, parts = card_inputs(cards_local)
    fc = [main_filter + f",trim=duration={dur},setpts=PTS-STARTPTS,fps={FPS}[vmain]"]
    chain = "vmain"
    for k, a, b in parts:
        fc.append(f"[{ci+k}:v]format=rgba,fps={FPS},fade=t=in:st=0:d=1:alpha=1,fade=t=out:st={b-a-1:.2f}:d=1:alpha=1,"
                  f"tpad=start_duration={a:.2f}:start_mode=add:color=black@0.0,setpts=PTS-STARTPTS[c{k}]")
        fc.append(f"[{chain}][c{k}]overlay=0:0:eof_action=pass[o{k}]")
        chain = f"o{k}"
    fc.append(f"[{chain}]format=yuv420p,trim=duration={dur},setpts=PTS-STARTPTS[vout]")
    out = os.path.join(OUT, f"vid_{name}.mp4")
    cmd = [FF, "-y", "-loglevel", "error", "-stats"] + main_inputs + cins + [
        "-filter_complex", ";".join(fc), "-map", "[vout]", "-an", "-t", f"{dur:.3f}"] + ENC + [out]
    print("render", name); subprocess.run(cmd, check=True)
    return out

# I. 背景 + 波形
vA = render_section("ave",
    ["-loop", "1", "-framerate", str(FPS), "-i", os.path.join(OUT, "bg.png"), "-i", os.path.join(OUT, "sec_ave.wav")],
    f"[1:a]showwaves=s={W}x360:mode=cline:rate={FPS}:colors=0xE8D9A0|0x8FB8C8:scale=sqrt,format=rgba,colorchannelmixer=aa=0.85[wv];"
    f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p[bg];[bg][wv]overlay=0:{H-360}:shortest=1,format=yuv420p",
    L[0], [("card0.png", 0.0, 7.0), ("card1.png", 8.0, 14.0)])
# II. SoundFilm → ピアノロール (同じ音源のタイムライン上で切替)
half = 129
vB = render_section("requiem",
    ["-i", src("Requiem_in_F_minor_Grand_Piano.mp4"), "-i", src("requiem_piano.mp4")],
    f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,trim=duration={half},setpts=PTS-STARTPTS,fps={FPS}[vB1];"
    f"[1:v]scale={W}:{H},fps={FPS},format=yuv420p,trim=start={half-XF}:duration={L[1]-half+XF},setpts=PTS-STARTPTS,fps={FPS}[vB2];"
    f"[vB1][vB2]xfade=transition=fade:duration={XF}:offset={half-XF},fps={FPS}",
    L[1], [("card2.png", 1.0, 7.0)])
vC = render_section("contrapunctus", ["-i", src("La_Japonaise_Contrapunctus14.mp4")],
    norm(0) + ",tpad=stop_mode=clone:stop_duration=6", L[2], [("card3.png", 1.0, 7.0)])
vD1 = render_section("coda1", ["-i", src("20260920_154001.mp4")],
    norm(0) + ",tpad=stop_mode=clone:stop_duration=6", L[3], [("card4.png", 1.0, 7.0)])
vD2 = render_section("coda2", ["-i", src("20260920_154118.mp4")],
    norm(0) + ",tpad=stop_mode=clone:stop_duration=6", L[4], [("card5.png", L[4] - 9.0, L[4] - 1.0)])

# 連結
vids = [vA, vB, vC, vD1, vD2]
inputs = []
for v in vids: inputs += ["-i", v]
inputs += ["-i", os.path.join(OUT, "bada_suite_master.wav")]
fc = [f"[{k}:v]fps={FPS},format=yuv420p,setpts=PTS-STARTPTS,fps={FPS}[v{k}]" for k in range(5)]
chain = "v0"; off = 0.0
for k in range(1, 5):
    off += L[k - 1] - XF
    fc.append(f"[{chain}][v{k}]xfade=transition=fade:duration={XF}:offset={off:.3f},fps={FPS}[x{k}]")
    chain = f"x{k}"
fc.append(f"[{chain}]format=yuv420p,trim=duration={total:.3f}[vout]")
out_mp4 = os.path.join(OUT, "Bada_Suite.mp4")
cmd = [FF, "-y", "-loglevel", "error", "-stats"] + inputs + [
    "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "5:a"] + ENC + [
    "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out_mp4]
print("concat + mux ...")
subprocess.run(cmd, check=True)
print("done:", out_mp4)
