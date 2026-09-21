#!/usr/bin/env python3
"""Bada Suite — ユーザー自身の素材だけで組曲を編曲して mp4 に書き出す。

構成 (4 秒の等パワー・クロスフェードで接続, 調性でつなぐ):
  I.   Ave (SATB MIDI, D)      … MIDI を合唱シンセ + ピアノ層で新規レンダリング
  II.  Requiem in F minor      … 原音ピアノ + 1 オクターブ下のゴースト層 + ホール残響
  III. トラック 18 (Fm)         … 同上 (任意: WMA があれば)
  IV.  Contrapunctus 14 (Dm)   … 同上 (La Japonaise)
  V.   トラック 8 (Gm)          … 同上 (任意)
  VI.  MOTHER — LUNA SEA (Gm)  … 原曲の歌声をそのまま, 軽い残響のみ (任意)
  VII. Coda: 20260920_154001 / 20260920_154118 … 録音 2 本を残響で包む

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

# ---------------------------------------------------------------- section table
def has(name):
    try: src(name); return True
    except FileNotFoundError: return False

# (key, 表示名, 副題, 音源, 長さ秒, ghost 量, 残響 wet, 追加 af, 映像種別)
SECTIONS = [
    dict(key="ave", title="I. Ave (SATB)", sub="MIDI から合唱シンセ + ピアノで新規レンダリング", dur=161.0,
         audio="synth", rev=0.32, video="waves"),
    dict(key="requiem", title="II. Requiem in F minor", sub="ピアノ + オクターブ下のゴースト層 + ホール残響", dur=250.0,
         audio="requiem_piano.mp3", ghost=0.16, rev=0.20, video="requiem_pair"),
]
if has("18______18.wma"):
    SECTIONS.append(dict(key="track18", title="III. トラック 18 (F minor)", sub="CD 取り込み音源 + ゴースト層 + 残響", dur=143.5,
                         audio="18______18.wma", ghost=0.14, rev=0.18, video="spectrum:fire"))
SECTIONS.append(dict(key="contrapunctus", title="IV. Contrapunctus 14 — La Japonaise", sub="ピアノ + ゴースト層 + 残響", dur=141.0,
                     audio="La_Japonaise_Contrapunctus14.mp4", ghost=0.14, rev=0.20, video="La_Japonaise_Contrapunctus14.mp4"))
if has("08______8.wma"):
    SECTIONS.append(dict(key="track8", title="V. トラック 8 (G minor)", sub="CD 取り込み音源 + ゴースト層 + 残響", dur=240.0,
                         audio="08______8.wma", ghost=0.12, rev=0.18, video="spectrum:cool"))
if has("10_MOTHER.wma"):
    SECTIONS.append(dict(key="mother", title="VI. MOTHER — LUNA SEA", sub="原曲の歌声をそのまま, 軽い残響のみ", dur=312.0,
                         audio="10_MOTHER.wma", rev=0.10, video="spectrum:magma"))
SECTIONS += [
    dict(key="coda1", title="VII. Coda", sub="20260920_154001 / 20260920_154118", dur=74.0,
         audio="20260920_154001.mp4", rev=0.26, af="highpass=f=70", video="20260920_154001.mp4"),
    dict(key="coda2", title="", sub="", dur=80.5,
         audio="20260920_154118.mp4", rev=0.26, af="highpass=f=70", video="20260920_154118.mp4"),
]
# 番号を実際の順序で振り直す
roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
n = 0
for sd in SECTIONS:
    if sd["title"]:
        n += 1; sd["title"] = f"{roman[n-1]}. " + sd["title"].split(". ", 1)[1]
lens = [sd["dur"] for sd in SECTIONS]
starts = [0.0]
for Lk in lens[:-1]: starts.append(starts[-1] + Lk - XF)
total = sum(lens) - XF * (len(lens) - 1)

REUSE = os.environ.get("REUSE_AUDIO") == "1" and os.path.exists(os.path.join(OUT, "bada_suite_master.wav"))

def build_audio():
    parts = []
    for sd in SECTIONS:
        print("audio:", sd["key"]); D = sd["dur"]; N = int(D * SR)
        if sd["audio"] == "synth":
            x = fit(render_ave(src("ave_satb.mid")), N)
        else:
            x = fit(load(src(sd["audio"]), D, sd.get("af")), N)
            if sd.get("ghost"):
                x = x + sd["ghost"] * fit(ghost(src(sd["audio"]), D), N)
        x = rms_norm(reverb(x, sd["rev"]), -20.5)
        x = fade(x, 0.5 if sd["audio"] == "synth" else 0.3, 3.0)
        save_wav(os.path.join(OUT, f"sec_{sd['key']}.wav"), x)
        parts.append(x)
    master = soft_limit(crossfade_concat(parts))
    master *= 0.97 / (np.abs(master).max() + 1e-9)
    save_wav(os.path.join(OUT, "bada_suite_master.wav"), master)
    return master

if REUSE:
    print("reusing audio")
    master = wavfile.read(os.path.join(OUT, "bada_suite_master.wav"))[1]
else:
    master = build_audio()
assert abs(len(master) / SR - total) < 0.01, (len(master) / SR, total)
print("section lengths", lens, "total", total)

# ---------------------------------------------------------------- title cards
def card(path, title, sub="", big=64):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, big); f2 = ImageFont.truetype(FONT, 30)
    top = int(H * 0.40) - 36; bot = int(H * 0.40) + big + (70 if sub else 20)
    d.rectangle([0, top, W, bot], fill=(10, 10, 20, 150))          # 半透明の帯
    w1 = d.textlength(title, font=f1); d.text(((W - w1) / 2, H * 0.40), title, font=f1, fill=(255, 250, 235, 255))
    if sub:
        size = 30
        while d.textlength(sub, font=f2) > W - 80 and size > 14:
            size -= 1; f2 = ImageFont.truetype(FONT, size)
        w2 = d.textlength(sub, font=f2); d.text(((W - w2) / 2, H * 0.40 + big + 24), sub, font=f2, fill=(225, 220, 205, 230))
    im.save(path)

def make_bg(path, c0, c1):
    bg = Image.new("RGB", (W, H)); px = bg.load()
    for y in range(H):
        for x in range(W):
            v = (x / W) * 0.5 + (y / H) * 0.5
            px[x, y] = tuple(int(a + (b - a) * v) for a, b in zip(c0, c1))
    bg.save(path)
make_bg(os.path.join(OUT, "bg.png"), (14, 12, 28), (34, 28, 68))
make_bg(os.path.join(OUT, "bg_fire.png"), (18, 8, 8), (52, 22, 16))
make_bg(os.path.join(OUT, "bg_cool.png"), (6, 14, 22), (14, 40, 58))
make_bg(os.path.join(OUT, "bg_magma.png"), (12, 6, 16), (48, 14, 40))

sub_all = " · ".join(sd["title"].split(". ", 1)[1].split(" — ")[0] for sd in SECTIONS if sd["title"])
card(os.path.join(OUT, "card_open.png"), "Bada Suite", sub_all, big=72)
card(os.path.join(OUT, "card_end.png"), "Bada Suite", "自作音源・MIDI と手持ちの音源からの編曲 (私的利用)", big=72)
for sd in SECTIONS:
    if sd["title"]:
        card(os.path.join(OUT, f"card_{sd['key']}.png"), sd["title"], sd["sub"], big=56)

# ---------------------------------------------------------------- video
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]

def norm(idx):
    return (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:-1:-1,"
            f"fps={FPS},format=yuv420p")

def render_section(name, main_inputs, main_filter, dur, cards_local):
    """main_filter は最後にラベル無しで終わる。cards_local: [(png, start, end)] 楽章内時刻。"""
    ci = sum(1 for x in main_inputs if x == "-i")
    cins = []
    for fn, a, b in cards_local:
        cins += ["-loop", "1", "-framerate", str(FPS), "-t", f"{b-a:.2f}", "-i", os.path.join(OUT, fn)]
    fc = [main_filter + f",trim=duration={dur},setpts=PTS-STARTPTS,fps={FPS}[vmain]"]
    chain = "vmain"
    for k, (fn, a, b) in enumerate(cards_local):
        fc.append(f"[{ci+k}:v]format=rgba,fps={FPS},fade=t=in:st=0:d=1:alpha=1,fade=t=out:st={b-a-1:.2f}:d=1:alpha=1,"
                  f"tpad=start_duration={a:.2f}:start_mode=add:color=black@0.0,setpts=PTS-STARTPTS[c{k}]")
        fc.append(f"[{chain}][c{k}]overlay=0:0:eof_action=pass[o{k}]")
        chain = f"o{k}"
    fc.append(f"[{chain}]format=yuv420p,trim=duration={dur},setpts=PTS-STARTPTS[vout]")
    out = os.path.join(OUT, f"vid_{name}.mp4")
    rerender = os.environ.get("RERENDER", "").split(",")
    if os.environ.get("SKIP_EXISTING") == "1" and os.path.exists(out) and name not in rerender:
        print("reuse", name); return out
    cmd = [FF, "-y", "-loglevel", "error", "-stats"] + main_inputs + cins + [
        "-filter_complex", ";".join(fc), "-map", "[vout]", "-an", "-t", f"{dur:.3f}"] + ENC + [out]
    print("render", name); subprocess.run(cmd, check=True)
    return out

vids = []
for i, sd in enumerate(SECTIONS):
    D = sd["dur"]; wav = os.path.join(OUT, f"sec_{sd['key']}.wav")
    cards_local = []
    if i == 0: cards_local.append(("card_open.png", 0.0, 7.0))
    if sd["title"]: cards_local.append((f"card_{sd['key']}.png", 8.0 if i == 0 else 1.0, 14.0 if i == 0 else 7.0))
    if i == len(SECTIONS) - 1: cards_local.append(("card_end.png", D - 9.0, D - 1.0))
    v = sd["video"]
    if v == "waves":
        ins = ["-loop", "1", "-framerate", str(FPS), "-i", os.path.join(OUT, "bg.png"), "-i", wav]
        flt = (f"[1:a]showwaves=s={W}x360:mode=cline:rate={FPS}:colors=0xE8D9A0|0x8FB8C8:scale=sqrt,format=rgba,colorchannelmixer=aa=0.85[wv];"
               f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p[bg];[bg][wv]overlay=0:{H-360}:shortest=1,format=yuv420p")
    elif v.startswith("spectrum:"):
        color = v.split(":")[1]
        ins = ["-loop", "1", "-framerate", str(FPS), "-i", os.path.join(OUT, f"bg_{color}.png"), "-i", wav]
        flt = (f"[1:a]showspectrum=s={W}x400:mode=combined:color={color}:slide=scroll:scale=log:fscale=log:overlap=0.8:fps={FPS},"
               f"format=rgba,colorkey=0x000000:0.12:0.25,colorchannelmixer=aa=0.92[sp];"
               f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p[bg];[bg][sp]overlay=0:{H-400}:shortest=1,format=yuv420p")
    elif v == "requiem_pair":
        half = 129
        ins = ["-i", src("Requiem_in_F_minor_Grand_Piano.mp4"), "-i", src("requiem_piano.mp4")]
        flt = (f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,trim=duration={half},setpts=PTS-STARTPTS,fps={FPS}[vB1];"
               f"[1:v]scale={W}:{H},fps={FPS},format=yuv420p,trim=start={half-XF}:duration={D-half+XF},setpts=PTS-STARTPTS,fps={FPS}[vB2];"
               f"[vB1][vB2]xfade=transition=fade:duration={XF}:offset={half-XF},fps={FPS}")
    else:
        ins = ["-i", src(v)]
        flt = norm(0) + ",tpad=stop_mode=clone:stop_duration=6"
    vids.append(render_section(sd["key"], ins, flt, D, cards_local))

# 連結 + マスター音声
inputs = []
for v in vids: inputs += ["-i", v]
inputs += ["-i", os.path.join(OUT, "bada_suite_master.wav")]
A = len(vids)
fc = [f"[{k}:v]fps={FPS},format=yuv420p,setpts=PTS-STARTPTS,fps={FPS}[v{k}]" for k in range(A)]
chain = "v0"
for k in range(1, A):
    fc.append(f"[{chain}][v{k}]xfade=transition=fade:duration={XF}:offset={starts[k]:.3f},fps={FPS}[x{k}]")
    chain = f"x{k}"
fc.append(f"[{chain}]format=yuv420p,trim=duration={total:.3f}[vout]")
out_mp4 = os.path.join(OUT, "Bada_Suite.mp4")
cmd = [FF, "-y", "-loglevel", "error", "-stats"] + inputs + [
    "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", f"{A}:a"] + ENC + [
    "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out_mp4]
print("concat + mux ...")
subprocess.run(cmd, check=True)
print("done:", out_mp4)

# ---------------------------------------------------------------- 配布用: 前半/後半 (540p, 2 パス) と mp3
split_at = os.environ.get("SPLIT_AT")   # 楽章 key を指定するとその楽章の頭で前後に分ける
def small(src_mp4, out, ss, t, vfade_in, afade_in, fade_out):
    vf = f"scale=960:540"
    af = ""
    if vfade_in: vf += ",fade=t=in:d=2"; af = "afade=t=in:d=2"
    if fade_out:
        vf += f",fade=t=out:st={t-3:.2f}:d=3"; af = (af + "," if af else "") + f"afade=t=out:st={t-3:.2f}:d=3"
    base = [FF, "-y", "-loglevel", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", src_mp4, "-vf", vf, "-r", "24",
            "-c:v", "libx264", "-preset", "medium", "-b:v", "225k", "-maxrate", "280k", "-bufsize", "560k", "-passlogfile", os.path.join(OUT, "x264pass")]
    subprocess.run(base + ["-pass", "1", "-an", "-f", "null", "-"], check=True)
    subprocess.run(base + ["-pass", "2"] + (["-af", af] if af else []) + ["-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], check=True)
    print("wrote", out, os.path.getsize(out) / 2 ** 20, "MiB")

if split_at:
    k = [sd["key"] for sd in SECTIONS].index(split_at)
    cut = starts[k] + XF / 2
    small(out_mp4, os.path.join(OUT, "Bada_Suite_part1_540p.mp4"), 0, cut, False, False, True)
    small(out_mp4, os.path.join(OUT, "Bada_Suite_part2_540p.mp4"), cut, total - cut, True, True, False)
else:
    small(out_mp4, os.path.join(OUT, "Bada_Suite_540p.mp4"), 0, total, False, False, False)
subprocess.run([FF, "-y", "-loglevel", "error", "-i", os.path.join(OUT, "bada_suite_master.wav"), "-c:a", "libmp3lame", "-b:a", "160k",
                os.path.join(OUT, "Bada_Suite_audio.mp3")], check=True)
print("all done")
