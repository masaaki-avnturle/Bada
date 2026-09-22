#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score.json + fuga.wav -> fuga.mp4  (4 声ピアノロール動画, 1280x720 30fps)"""
import json, sys, subprocess, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import soundfile as sf

W, H, FPS = 1280, 720, 30
NOW_X = 360
PPS = 110.0            # pixels per second
ROLL_Y0, ROLL_Y1 = 150, 592
M_LO, M_HI = 24, 100
COL = {'S': (240, 196, 110), 'A': (232, 122, 142), 'T': (96, 206, 196), 'B': (122, 152, 255)}
VNAME = {'S': 'Soprano', 'A': 'Alto', 'T': 'Tenore', 'B': 'Basso'}
JP = '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'
SERIF = '/mnt/skills/examples/canvas-design/canvas-fonts/CrimsonPro-Regular.ttf'
SERIF_I = '/mnt/skills/examples/canvas-design/canvas-fonts/CrimsonPro-Italic.ttf'

def font(path, size):
    try: return ImageFont.truetype(path, size)
    except Exception: return ImageFont.load_default()

def ffmpeg_exe():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'

def y_of(m):
    return ROLL_Y1 - (m - M_LO) * (ROLL_Y1 - ROLL_Y0) / (M_HI - M_LO)

def dim(c, k):
    return tuple(int(x * k) for x in c)

THEMES = {
    'organ': dict(bg=(12, 15, 26), bg2=(22, 23, 42), roll=(9, 11, 20), title='Contrapunctus BADA',
                  subtitle='Fuga a tre soggetti — ニ短調 ／ J.S.バッハ《フーガの技法》コントラプンクトゥス XIV へのオマージュ',
                  footer=['主題 I ← MOTHER (LUNA SEA) の旋律輪郭  ／  主題 II ← トラック18 の反復音型  ／  主題 III ← B♭-A-D-A (BADA) + 録音 090933 の半音隣接音型',
                          'エピソード ← LOVELESS の隣接音型 ／ トラック17 の上行音階 ／ トラック8 のため息音型 ／ 録音 090146    ｜  合成: 加算合成オルガン 4 声',
                          '第 127 小節の休止は、バッハの自筆譜が第 239 小節で途切れることへのオマージュ。その後コーダで完結させた。'],
                  pause_bar=126),
    'requiem': dict(bg=(16, 8, 24), bg2=(34, 14, 44), roll=(10, 5, 16), title='Requiem BADA', subtitle='', footer=[], pause_bar=138),
    'piano': dict(bg=(20, 14, 12), bg2=(40, 28, 22), roll=(12, 8, 7), title='Requiem BADA III', subtitle='', footer=[], pause_bar=86),
    'mallet': dict(bg=(8, 12, 22), bg2=(18, 28, 46), roll=(5, 8, 16), title='Requiem BADA IV', subtitle='', footer=[], pause_bar=68),
}

def main(score='score.json', wav='fuga.wav', out='fuga.mp4'):
    d = json.load(open(score))
    meta = d.get('meta', {})
    th = dict(THEMES[meta.get('style', 'organ')])
    for k in ('title', 'subtitle', 'footer'):
        if meta.get(k): th[k] = meta[k]
    notes = d['notes'] + [dict(e, label=e.get('label')) for e in d.get('extras', [])]
    COL.update({'X': (236, 214, 150), 'D': (120, 70, 140), 'P': (190, 60, 70), 'H': (250, 240, 200), 'W': (170, 150, 120), 'L': (150, 110, 90)})
    VNAME.update({'X': '弔鐘', 'D': 'ドローン', 'P': '心拍', 'H': '鐘のカノン', 'W': '分散和音', 'L': '低音の心拍'})
    if meta.get('style') == 'mallet':
        COL.update({'H': (150, 230, 255), 'W': (110, 180, 210)}); VNAME.update({'H': '木琴シンセ (鐘)', 'W': '木琴シンセ (刻み)', 'L': '低音 (ピアノ)'})
    LEGEND = {'organ': ['S', 'A', 'T', 'B'], 'requiem': ['S', 'A', 'T', 'B', 'X', 'D', 'P'], 'piano': ['S', 'A', 'T', 'B', 'H', 'W', 'L'], 'mallet': ['S', 'A', 'T', 'B', 'H', 'W', 'L']}[meta.get('style', 'organ')]
    T = np.array([n['t'] for n in notes]); D = np.array([n['d'] for n in notes]); M = np.array([n['m'] for n in notes])
    V = [n['v'] for n in notes]; LAB = [n['label'] for n in notes]
    order = np.argsort(T); T, D, M = T[order], D[order], M[order]; V = [V[i] for i in order]; LAB = [LAB[i] for i in order]
    entries = d['entries']; sections = d['sections']
    bpm = d['bpm']; spb = 60.0 / bpm; bpb = d['beats_per_bar']
    harm = d['harm']
    audio, sr = sf.read(wav)
    mono = audio.mean(axis=1) if audio.ndim == 2 else audio
    total = len(mono) / sr
    nframes = int(math.ceil(total * FPS))
    # 音量エンベロープ (フレーム毎)
    win = int(sr / FPS)
    rms = np.array([np.sqrt((mono[i * win:(i + 1) * win] ** 2).mean()) if (i + 1) * win <= len(mono) else 0.0 for i in range(nframes)])
    rms = rms / (rms.max() + 1e-9)

    f_title = font(SERIF, 40); f_sub = font(JP, 17); f_sec = font(JP, 23); f_secsub = font(JP, 15)
    f_small = font(JP, 14); f_lab = font(JP, 15); f_chord = font(SERIF_I, 22); f_num = font(SERIF, 20)

    # 背景 (固定部分) を一度描いて再利用
    bg = Image.new('RGB', (W, H), th['bg'])
    bd = ImageDraw.Draw(bg)
    for y in range(0, H):
        k = y / H
        bd.line([(0, y), (W, y)], fill=tuple(int(th['bg'][i] + (th['bg2'][i] - th['bg'][i]) * k) for i in range(3)))
    bd.rectangle([0, ROLL_Y0 - 6, W, ROLL_Y1 + 6], fill=th['roll'])
    for m in range(M_LO, M_HI + 1):
        y = y_of(m)
        if m % 12 == 0:
            bd.line([(0, y), (W, y)], fill=(40, 46, 66))
            bd.text((8, y - 16), 'C%d' % (m // 12 - 1), font=f_small, fill=(110, 118, 140))
        elif m % 12 in (2, 5, 9):  # D, F, A (ニ短調の主和音)
            bd.line([(0, y), (W, y)], fill=(22, 26, 40))
    bd.text((30, 18), th['title'], font=f_title, fill=(236, 228, 210))
    bd.text((32, 66), th['subtitle'], font=f_sub, fill=(150, 156, 176))
    # 凡例
    lx = 30
    for v in LEGEND:
        bd.rectangle([lx, 612, lx + 14, 626], fill=COL[v]); bd.text((lx + 20, 609), VNAME[v], font=f_small, fill=(200, 204, 216))
        lx += 110 if v in 'SATB' else (150 if v in 'HWL' else 80)
    for i, line in enumerate(th['footer']):
        bd.text((30, 640 + 22 * i), line, font=f_small, fill=(150, 156, 176) if i < 2 else (120, 126, 146))

    ff = ffmpeg_exe()
    cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
           '-movflags', '+faststart', '-shortest', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ahead = (W - NOW_X) / PPS; back = NOW_X / PPS
    pause_t = (th['pause_bar'] * bpb) * spb
    for fi in range(nframes):
        now = fi / FPS
        im = bg.copy(); dr = ImageDraw.Draw(im)
        # セクション
        sec = None
        for s in sections:
            if now >= s['t'] - 0.001: sec = s
        if sec:
            dr.text((30, 100), sec['title'], font=f_sec, fill=(236, 228, 210))
            dr.text((32, 128), sec['sub'], font=f_secsub, fill=(160, 166, 186))
        # 小節番号・時間
        beat = now / spb; bar = int(beat // bpb) + 1
        if bar <= d['nbars']:
            dr.text((W - 250, 22), 'Bar %d / %d' % (bar, d['nbars']), font=f_num, fill=(200, 204, 216))
        dr.text((W - 250, 48), '%d:%02d / %d:%02d' % (now // 60, now % 60, total // 60, total % 60), font=f_num, fill=(140, 146, 166))
        # 小節線
        first_bar = int((now - back) / (spb * bpb)) - 1
        for b in range(max(first_bar, 0), first_bar + int((back + ahead) / (spb * bpb)) + 3):
            x = NOW_X + (b * bpb * spb - now) * PPS
            if 0 <= x <= W:
                dr.line([(x, ROLL_Y0 - 6), (x, ROLL_Y1 + 6)], fill=(34, 38, 56))
                if b + 1 <= d['nbars']:
                    dr.text((x + 3, ROLL_Y0 - 4), str(b + 1), font=f_small, fill=(70, 76, 98))
        # 音符
        vis = np.where((T < now + ahead) & (T + D > now - back))[0]
        for i in vis:
            x0 = NOW_X + (T[i] - now) * PPS; x1 = NOW_X + (T[i] + D[i] - now) * PPS
            y = y_of(M[i]); v = V[i]; c = COL[v]
            sounding = T[i] <= now < T[i] + D[i]
            if v == 'X':
                cx = x0; s = 9 if sounding else 6
                dr.polygon([(cx, y - s), (cx + s, y), (cx, y + s), (cx - s, y)], fill=c if sounding else dim(c, 0.6))
                dr.line([(cx, y), (min(x1, W), y)], fill=dim(c, 0.35)); continue
            if v == 'P':
                y = ROLL_Y1 + 2; s = 7 if sounding else 4
                dr.ellipse([x0 - s, y - s, x0 + s, y + s], fill=c if sounding else dim(c, 0.55)); continue
            if v == 'D':
                y = min(y, ROLL_Y1 + 2)
                dr.rectangle([x0, y - 2, x1 - 1, y + 2], fill=dim(c, 0.9 if sounding else 0.6)); continue
            if LAB[i]:
                fill = c if not sounding else tuple(min(255, int(x * 1.25 + 30)) for x in c)
                if sounding: dr.rectangle([x0 - 2, y - 6, x1 + 2, y + 6], fill=dim(c, 0.35))
                dr.rectangle([x0, y - 4, x1 - 1, y + 4], fill=fill, outline=tuple(min(255, x + 40) for x in c))
            else:
                fill = dim(c, 0.55) if not sounding else c
                dr.rectangle([x0, y - 3, x1 - 1, y + 3], fill=fill)
        # 主題入りのラベル
        for e in entries:
            x = NOW_X + (e['t'] - now) * PPS
            if 0 <= x < W:
                m0 = M[np.searchsorted(T, e['t'] - 1e-6)]  # おおよその音高
                cand = [i for i in vis if abs(T[i] - e['t']) < 1e-3 and V[i] == e['v']]
                if cand: m0 = M[cand[0]]
                y = y_of(m0) - 22
                lab = e['label'].replace('S1', '主題 I').replace('S2', '主題 II').replace('S3', '主題 III') + ' · ' + VNAME[e['v']]
                dr.text((x + 2, y), lab, font=f_lab, fill=tuple(min(255, k + 50) for k in COL[e['v']]))
        # 現在の和音
        bi = min(int(beat), len(harm) - 1)
        dr.text((NOW_X + 8, ROLL_Y1 - 26), harm[bi], font=f_chord, fill=(190, 186, 170))
        # 休止のオマージュ
        if pause_t - 0.2 <= now < pause_t + 1.6:
            dr.text((NOW_X + 20, ROLL_Y0 + 20), '— 休止 —  (自筆譜が途切れる箇所へのオマージュ)', font=f_sec, fill=(210, 200, 170))
        # now 線 + 音量
        dr.line([(NOW_X, ROLL_Y0 - 8), (NOW_X, ROLL_Y1 + 8)], fill=(250, 240, 220), width=2)
        lv = rms[fi]
        dr.rectangle([W - 250, 84, W - 250 + int(220 * lv), 90], fill=(180, 170, 140))
        dr.rectangle([W - 250, 84, W - 30, 90], outline=(60, 64, 84))
        p.stdin.write(im.tobytes())
        if fi % (FPS * 30) == 0:
            print('frame %d/%d (%.0fs)' % (fi, nframes, now), flush=True)
    p.stdin.close(); p.wait()
    print('wrote', out, 'rc', p.returncode)

if __name__ == '__main__':
    main(*sys.argv[1:4])
