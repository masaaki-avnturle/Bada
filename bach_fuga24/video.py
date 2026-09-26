# -*- coding: utf-8 -*-
"""
video.py — ピアノロール動画 (1280x720, 30fps, H.264 + AAC) を生成。
フレームは numpy で描き、ffmpeg (imageio-ffmpeg 同梱バイナリ) に rawvideo でパイプする。
"""
import json, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
BPM = 100.0; QUARTER = 60.0 / BPM
TOP, BOTTOM = 130, 700          # piano-roll area
PLAYHEAD_X = 420                # px
PX_PER_SEC = 110.0
COLORS = {'S1': (232, 184, 74), 'S2': (96, 200, 120), 'S3': (230, 88, 88), 'S4': (90, 150, 240),
          'ROW': (180, 110, 230), 'free': (120, 135, 160), 'CAD': (240, 220, 180)}
LABEL = {'S1': '主題 I', 'S2': '主題 II', 'S3': 'B-A-C-H (主題 III)', 'S4': 'フーガの技法 主題 (IV)', 'ROW': 'BACH 12音列', 'free': '自由対位', 'CAD': '終止'}
VOICE = ['Bass', 'Tenor', 'Alto', 'Soprano']

def ffmpeg_bin():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception: return 'ffmpeg'

def font(size, jp=False):
    for p in (['/usr/share/fonts/opentype/unifont/unifont_jp.otf'] if jp else []) + \
             ['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make_static(fugue, total_sec):
    """background with title, legend, pitch grid -> numpy uint8 (H,W,3)"""
    img = Image.new('RGB', (W, H), (14, 16, 24))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, TOP - 10], fill=(22, 25, 38))
    d.text((36, 14), f"Fuga {fugue['no']:02d} / 24  ·  {fugue['name']}", font=font(30), fill=(240, 236, 220))
    d.text((36, 56), f"{fugue['name_jp']}", font=font(30, jp=True), fill=(232, 184, 74))
    d.text((760, 18), "J. S. Bach · Contrapunctus XIV (BWV 1080/19)", font=font(20), fill=(200, 200, 210))
    d.text((760, 46), "12音階 · 5度圏 · B♭↔C♯ 鏡映 (音階の秘密の原理)", font=font(18, jp=True), fill=(170, 175, 190))
    d.text((760, 70), "実音源: 16 recordings (sampler)", font=font(18, jp=True), fill=(170, 175, 190))
    # legend
    x = 36
    for tag in ('S1', 'S2', 'S3', 'S4', 'ROW', 'free'):
        d.rectangle([x, 100, x + 16, 112], fill=COLORS[tag]); d.text((x + 22, 96), LABEL[tag], font=font(16, jp=True), fill=(210, 210, 220))
        x += 30 + 16 * (len(LABEL[tag]) if any(ord(c) > 255 for c in LABEL[tag]) else len(LABEL[tag]) * 0.6) + 10
    return np.array(img)

def pitch_y(p):
    return int(BOTTOM - (p - 34) * (BOTTOM - TOP) / 50)

def render_video(fugue, wav, out_mp4, seed=0):
    total_sec = fugue['length'] * QUARTER + 3.0
    static = make_static(fugue, total_sec)
    # pre-compute note rectangles in (x_at_t0, y0, x_w, y1, color)
    notes = []
    for n in fugue['notes']:
        x0 = n['t'] * QUARTER * PX_PER_SEC; x1 = (n['t'] + n['dur']) * QUARTER * PX_PER_SEC - 2
        y0 = pitch_y(n['p'] + 0.5); y1 = pitch_y(n['p'] - 0.5) - 1
        notes.append((x0, x1, y0, y1, COLORS[n['tag']], n['t'] * QUARTER, (n['t'] + n['dur']) * QUARTER))
    # horizontal octave lines
    for p in range(36, 85, 12):
        y = pitch_y(p); static[y, 0:W] = (40, 44, 60)
    nframes = int(total_sec * FPS)
    ff = ffmpeg_bin()
    cmd = [ff, '-hide_banner', '-loglevel', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    f_time = font(22); f_bar = font(18, jp=True)
    sec_label_cache = {}
    for fi in range(nframes):
        tsec = fi / FPS
        frame = static.copy()
        offs = PLAYHEAD_X - tsec * PX_PER_SEC
        for (x0, x1, y0, y1, col, t0, t1) in notes:
            a = int(x0 + offs); b = int(x1 + offs)
            if b < 0 or a > W: continue
            a = max(a, 0); b = min(b, W)
            if t0 <= tsec < t1:
                c = tuple(min(255, int(v * 1.35 + 30)) for v in col)
                frame[y0 - 1:y1 + 1, a:b] = c
            else:
                dim = 1.0 if t0 > tsec else 0.55
                frame[y0:y1, a:b] = tuple(int(v * dim) for v in col)
        # bar lines
        bar_sec = 4 * QUARTER
        first_bar = int(max(0, (tsec - PLAYHEAD_X / PX_PER_SEC)) / bar_sec)
        for bi in range(first_bar, first_bar + 20):
            x = int(bi * bar_sec * PX_PER_SEC + offs)
            if 0 <= x < W: frame[TOP:BOTTOM, x] = (48, 52, 70)
        frame[TOP:BOTTOM, PLAYHEAD_X - 1:PLAYHEAD_X + 1] = (255, 255, 255)
        # time / bar text (only re-rendered each second to save time)
        key = int(tsec)
        if key not in sec_label_cache:
            im = Image.new('RGB', (420, 40), (14, 16, 24)); dd = ImageDraw.Draw(im)
            bar = int(tsec / bar_sec) + 1
            dd.text((0, 6), f"{int(tsec)//60}:{int(tsec)%60:02d} / {int(total_sec)//60}:{int(total_sec)%60:02d}   bar {min(bar, fugue['length']//4)}", font=f_time, fill=(220, 220, 230))
            sec_label_cache[key] = np.array(im)
        frame[H - 44:H - 4, W - 440:W - 20] = sec_label_cache[key]
        proc.stdin.write(frame.tobytes())
    proc.stdin.close(); proc.wait()
    return proc.returncode

if __name__ == '__main__':
    fugues = json.load(open(sys.argv[1])); audiodir = sys.argv[2]; outdir = sys.argv[3]
    sel = [int(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else [f['no'] for f in fugues]
    for f in fugues:
        if f['no'] not in sel: continue
        wav = os.path.join(audiodir, f"fuga{f['no']:02d}.wav")
        out = os.path.join(outdir, f"Fuga{f['no']:02d}_{f['name'].replace(' — ','_').replace(' ','_').replace('#','s')}.mp4")
        rc = render_video(f, wav, out)
        print(f"fuga{f['no']:02d} -> {out} rc={rc}", flush=True)
