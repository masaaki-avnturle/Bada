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
    'grief': dict(bg=(14, 10, 18), bg2=(30, 20, 36), roll=(8, 6, 12), title='Requiem BADA V', subtitle='', footer=[], pause_bar=68),
    'elegia': dict(bg=(18, 14, 14), bg2=(38, 28, 26), roll=(11, 8, 8), title='Requiem BADA VI', subtitle='', footer=[], pause_bar=68),
    'concerto': dict(bg=(12, 12, 20), bg2=(30, 26, 40), roll=(8, 8, 14), title='Requiem BADA VIII', subtitle='', footer=[], pause_bar=58),
    'symphony': dict(bg=(10, 12, 18), bg2=(26, 30, 44), roll=(6, 8, 14), title='Symphony BADA', subtitle='', footer=[], pause_bar=145),
    'pconcerto': dict(bg=(12, 12, 20), bg2=(30, 26, 40), roll=(8, 8, 14), title='Piano Concerto BADA', subtitle='', footer=[], pause_bar=112),
    'sweet': dict(bg=(16, 12, 20), bg2=(36, 28, 44), roll=(10, 7, 14), title='BADA 528 — Sweet Trio', subtitle='', footer=[], pause_bar=999),
    'arrhythmia': dict(bg=(12, 8, 10), bg2=(36, 16, 20), roll=(8, 5, 7), title='Requiem BADA — Long Distance', subtitle='', footer=[], pause_bar=165),
    'mantra': dict(bg=(6, 8, 16), bg2=(16, 24, 44), roll=(4, 6, 12), title='Requiem BADA · Cor — Mantra', subtitle='', footer=[], pause_bar=99),
    'rock': dict(bg=(10, 8, 14), bg2=(34, 12, 30), roll=(7, 5, 10), title='Requiem BADA · Cor — Rock', subtitle='', footer=[], pause_bar=99),
    'heart': dict(bg=(18, 8, 12), bg2=(42, 14, 22), roll=(12, 5, 8), title='Requiem BADA · Cor', subtitle='', footer=[], pause_bar=99),
    'recsampler': dict(bg=(10, 12, 16), bg2=(30, 30, 40), roll=(6, 8, 11), title='Requiem BADA — Tablet Sessions', subtitle='', footer=[], pause_bar=999),
    'acceptance': dict(bg=(14, 12, 16), bg2=(40, 30, 30), roll=(9, 7, 10), title='BADA 528 — Acceptance', subtitle='', footer=[], pause_bar=999),
}

def main(score='score.json', wav='fuga.wav', out='fuga.mp4'):
    d = json.load(open(score))
    meta = d.get('meta', {})
    th = dict(THEMES[meta.get('style', 'organ')])
    for k in ('title', 'subtitle', 'footer'):
        if meta.get(k): th[k] = meta[k]
    recs = [e for e in d.get('extras', []) if e['v'] == 'REC']
    notes = d['notes'] + [dict(e, label=e.get('label')) for e in d.get('extras', []) if e['v'] != 'REC']
    COL.update({'X': (236, 214, 150), 'D': (120, 70, 140), 'P': (190, 60, 70), 'H': (250, 240, 200), 'W': (170, 150, 120), 'L': (150, 110, 90)})
    VNAME.update({'X': '弔鐘', 'D': 'ドローン', 'P': '心拍', 'H': '鐘のカノン', 'W': '分散和音', 'L': '低音の心拍'})
    if meta.get('style') == 'mallet':
        COL.update({'H': (150, 230, 255), 'W': (110, 180, 210)}); VNAME.update({'H': '木琴シンセ (鐘)', 'W': '木琴シンセ (刻み)', 'L': '低音 (ピアノ)'})
    if meta.get('style') == 'pconcerto':
        COL.update({'H': (250, 240, 200), 'V1': (200, 120, 90), 'V2': (170, 100, 80), 'VA': (150, 90, 110), 'VC': (120, 70, 60), 'CB': (90, 60, 50),
                    'FL': (190, 235, 220), 'WW': (120, 200, 120), 'CL': (110, 170, 200), 'HN': (210, 170, 90), 'TR': (240, 200, 80), 'TB': (170, 120, 60), 'TP': (170, 60, 60)})
        VNAME.update({'S': 'Pf S', 'A': 'Pf A', 'T': 'Pf T', 'B': 'Pf B', 'H': 'Pf 高音', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb',
                      'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'})
    if meta.get('style') == 'symphony':
        COL.update({'S': (235, 180, 120), 'A': (215, 140, 110), 'T': (180, 110, 130), 'B': (130, 90, 100), 'FL': (190, 235, 220), 'WW': (120, 200, 120), 'CL': (110, 170, 200),
                    'HN': (210, 170, 90), 'TR': (240, 200, 80), 'TB': (170, 120, 60), 'TP': (170, 60, 60)})
        VNAME.update({'S': 'Vn I', 'A': 'Vn II', 'T': 'Va', 'B': 'Vc·Cb', 'FL': 'Fl', 'WW': 'Ob', 'CL': 'Cl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'})
    if meta.get('style') == 'concerto':
        COL.update({'H': (250, 240, 200), 'V1': (200, 120, 90), 'V2': (170, 100, 80), 'VA': (150, 90, 110), 'VC': (120, 70, 60), 'CB': (90, 60, 50),
                    'WW': (120, 200, 120), 'FL': (190, 235, 220), 'HN': (210, 170, 90), 'TP': (160, 60, 60)})
        VNAME.update({'S': 'Pf S', 'A': 'Pf A', 'T': 'Pf T', 'B': 'Pf B', 'H': 'Pf 高音', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'WW': 'Ob', 'FL': 'Fl', 'HN': 'Hn', 'TP': 'Timp'})
    if meta.get('style') == 'elegia':
        COL.update({'H': (250, 240, 200), 'L': (150, 110, 90)}); VNAME.update({'H': 'ピアノ高音', 'L': 'ピアノ低音'})
    if meta.get('style') == 'grief':
        COL.update({'H': (250, 240, 200), 'C': (190, 90, 200), 'L': (150, 110, 90)}); VNAME.update({'H': 'ピアノ高音', 'C': 'シンセ不協和音', 'L': 'ピアノ低音'})
    if meta.get('style') == 'sweet':
        COL.update({'EP': (180, 220, 160), 'PD': (140, 120, 200), 'LD': (255, 180, 100), 'DR': (170, 170, 170),
                    'V1': (200, 120, 90), 'V2': (170, 100, 80), 'VA': (150, 90, 110), 'VC': (120, 70, 60),
                    'WW': (120, 200, 120), 'FL': (190, 235, 220)})
        VNAME.update({'S': 'Pf S', 'A': 'Pf A', 'T': 'Pf T', 'B': 'Pf Bass',
                      'EP': 'E.Piano', 'PD': 'Synth Pad', 'LD': 'Synth Lead', 'DR': 'Brushes',
                      'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'WW': 'Ob', 'FL': 'Fl'})
    if meta.get('style') == 'arrhythmia':
        COL.update({'DR': (235, 70, 90), 'SB': (90, 200, 255)}); VNAME.update({'DR': 'ドラム (不整脈)', 'SB': 'シンセ・ベース'})
    if meta.get('style') == 'mantra':
        COL.update({'S': (150, 220, 255), 'A': (120, 180, 255), 'T': (110, 230, 210), 'B': (160, 140, 255), 'DR': (235, 70, 90), 'SB': (90, 200, 255), 'OD': (120, 200, 255)})
        VNAME.update({'S': '倍音シンセ S', 'A': '倍音シンセ A', 'T': '倍音シンセ T', 'B': '倍音シンセ B', 'DR': 'ドラム (キック = 鼓動)', 'SB': 'シンセ・ベース', 'OD': '倍音 (共鳴)'})
    if meta.get('style') == 'rock':
        COL.update({'DR': (235, 70, 90), 'SB': (90, 200, 255), 'AR': (200, 120, 255), 'GT': (255, 150, 60), 'PD': (120, 110, 170)})
        VNAME.update({'S': 'Soprano', 'A': 'Alto', 'T': 'Tenore', 'B': 'Basso', 'DR': 'ドラム (キック = 鼓動)', 'SB': 'シンセ・ベース', 'AR': 'アルペジオ', 'GT': 'ギター', 'PD': 'パッド'})
    if meta.get('style') == 'heart':
        COL.update({'HB': (235, 70, 90)}); VNAME.update({'S': 'Soprano', 'A': 'Alto', 'T': 'Tenore', 'B': 'Basso', 'HB': '鼓動 (ドックン)'})
    if meta.get('style') == 'acceptance':
        COL.update({'H': (250, 240, 200), 'CB': (150, 95, 70), 'CBP': (190, 130, 90), 'TA': (200, 170, 110), 'BN': (160, 230, 190), 'TB': (110, 210, 250),
                    'V1': (200, 120, 90), 'V2': (170, 100, 80), 'VA': (150, 90, 110), 'VC': (120, 70, 60), 'WW': (120, 200, 120), 'FL': (190, 235, 220), 'PD': (120, 110, 170)})
        VNAME.update({'S': 'S', 'A': 'A', 'T': 'T', 'B': 'B', 'H': 'Pf', 'CB': 'Cb', 'CBP': 'Cb pizz', 'TA': 'Tanpura', 'BN': 'Bansuri', 'TB': 'タブレット録音',
                      'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'WW': 'Ob', 'FL': 'Fl', 'PD': 'Pad'})
    RCOL = {}
    if meta.get('style') == 'recsampler':
        COL.update({'TB': (110, 210, 250), 'OS': (200, 200, 215), 'DN': (130, 100, 160), 'PK': (235, 70, 90)})
        VNAME.update({'TB': 'タブレット録音 (実音)', 'OS': 'オスティナート', 'DN': '持続音', 'PK': '鼓動 (録音の低音)'})
        rids = sorted({n['src'] for n in d['notes'] if n.get('src')})
        pal = [(240, 196, 110), (232, 122, 142), (150, 220, 120), (96, 206, 196), (170, 150, 255)]
        if len(rids) > len(pal):                         # 録音が多いときは色相を等分
            import colorsys
            pal = [tuple(int(255 * x) for x in colorsys.hsv_to_rgb((0.08 + k / len(rids)) % 1.0, 0.5, 0.95)) for k in range(len(rids))]
        RCOL = {r: pal[k % len(pal)] for k, r in enumerate(rids)}
    present = {x['v'] for x in notes}
    LEGEND = {'organ': ['S', 'A', 'T', 'B'], 'requiem': ['S', 'A', 'T', 'B', 'X', 'D', 'P'], 'piano': ['S', 'A', 'T', 'B', 'H', 'W', 'L'], 'mallet': ['S', 'A', 'T', 'B', 'H', 'W', 'L'], 'grief': ['S', 'A', 'T', 'B', 'H', 'C', 'L'], 'elegia': ['S', 'A', 'T', 'B', 'H', 'L'], 'concerto': ['S', 'A', 'T', 'B', 'H', 'V1', 'V2', 'VA', 'VC', 'CB', 'WW', 'FL', 'HN', 'TP'], 'symphony': ['S', 'A', 'T', 'B', 'FL', 'WW', 'CL', 'HN', 'TR', 'TB', 'TP'], 'pconcerto': ['S', 'A', 'T', 'B', 'H', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'WW', 'CL', 'HN', 'TR', 'TB', 'TP'], 'sweet': ['S', 'A', 'T', 'B', 'EP', 'PD', 'LD', 'DR', 'WW', 'FL', 'VA', 'VC'], 'heart': ['S', 'A', 'T', 'B', 'HB', 'X', 'D'], 'rock': ['S', 'A', 'T', 'B', 'DR', 'SB', 'AR', 'GT', 'PD', 'X'], 'mantra': ['S', 'A', 'T', 'B', 'OD', 'DR', 'SB', 'X'], 'arrhythmia': ['S', 'A', 'T', 'B', 'DR', 'SB', 'X', 'D'], 'recsampler': ['TB', 'OS', 'DN', 'PK', 'X'], 'acceptance': ['TB', 'CB', 'CBP', 'S', 'A', 'T', 'B', 'H', 'V1', 'V2', 'VA', 'VC', 'WW', 'FL', 'BN', 'TA']}[meta.get('style', 'organ')]
    T = np.array([n['t'] for n in notes]); D = np.array([n['d'] for n in notes]); M = np.array([n['m'] for n in notes])
    V = [n['v'] for n in notes]; LAB = [n['label'] for n in notes]; DET = np.array([n.get('det', 1.0) for n in notes]); ROLE = [n.get('role', '') for n in notes]
    SRC = [n.get('rid') or n.get('src', '') if n['v'] in ('S', 'A', 'T', 'B', 'OS') else '' for n in notes]
    order = np.argsort(T); T, D, M, DET = T[order], D[order], M[order], DET[order]; V = [V[i] for i in order]; LAB = [LAB[i] for i in order]; ROLE = [ROLE[i] for i in order]; SRC = [SRC[i] for i in order]
    STRCOL = {'S': (200, 120, 90), 'A': (170, 100, 80), 'T': (150, 90, 110), 'B': (120, 70, 60)}
    entries = d['entries']; sections = d['sections']
    bpm = d['bpm']; spb = 60.0 / bpm; bpb = d['beats_per_bar']
    harm = d['harm']
    bar_times = d.get('bar_times') or [b * bpb * spb for b in range(d['nbars'] + 1)]
    bt = np.array(bar_times)
    def beat_at(tm):
        b = int(np.searchsorted(bt, tm, side='right') - 1); b = max(0, min(b, len(bt) - 2))
        return b * bpb + (tm - bt[b]) / (bt[b + 1] - bt[b]) * bpb
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
    for v in [x for x in LEGEND if x in present]:
        bd.rectangle([lx, 612, lx + 14, 626], fill=COL[v]); bd.text((lx + 20, 609), VNAME[v], font=f_small, fill=(200, 204, 216))
        lx += {'TB': 190, 'OS': 130, 'DN': 80, 'PK': 160}.get(v, 72) if meta.get('style') == 'recsampler' else (130 if v == 'TB' else 72) if meta.get('style') == 'acceptance' else (72 if meta.get('style') in ('concerto', 'symphony', 'pconcerto', 'sweet') else (110 if v in 'SATB' else (190 if v == 'DR' else (150 if v in ('H', 'W', 'L', 'C', 'HB') or (meta.get('style') == 'mantra' and v in 'SATB') else (125 if v in ('SB', 'AR', 'OD') else 80)))))
    circ = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯'
    many = len(RCOL) > 5                                  # 録音が多いときは録音の凡例を 2 段目に
    if many: lx = 30
    for k, (r, c) in enumerate(RCOL.items()):
        yy = 634 if many else 612
        bd.rectangle([lx, yy, lx + 14, yy + 14], fill=c)
        bd.text((lx + 20, yy - 3), '%s %d/%d %s:%s' % (circ[k], int(r[4:6]), int(r[6:8]), r[9:11], r[11:13]) if many else '%s %s:%s の音' % (circ[k], r[9:11], r[11:13]), font=f_small, fill=(200, 204, 216))
        lx += 112 if many else 132
    for i, line in enumerate(th['footer']):
        bd.text((30, (662 if many else 640) + 22 * i), line, font=f_small, fill=(150, 156, 176) if i < 2 else (120, 126, 146))

    # 鼓動 (心電図と脈打つ心臓) のデータ
    hb = [e for e in d.get('extras', []) if e['v'] == 'HB']
    LUB = np.array([e['t'] for e in hb if e.get('kind') == 'lub']); LUBG = np.array([e['gain'] for e in hb if e.get('kind') == 'lub'])
    DUB = np.array([e['t'] for e in hb if e.get('kind') == 'dub'])
    SNARE = np.array([])
    DRUMS = sorted((e['t'], e.get('kind', 'kick'), e['gain']) for e in d.get('extras', []) if e['v'] == 'DR') if meta.get('style') == 'arrhythmia' else []
    if meta.get('style') in ('rock', 'mantra'):           # 鼓動がキックになった: 心電図はキックで打つ
        kk = [e for e in d.get('extras', []) if e['v'] == 'DR' and e.get('kind') == 'kick']
        LUB = np.array([e['t'] for e in kk]); LUBG = np.array([min(1.0, e['gain'] * 1.1) for e in kk])
        SNARE = np.array([e['t'] for e in d.get('extras', []) if e['v'] == 'DR' and e.get('kind') == 'snare'])
    def heart_poly(cx, cy, s):
        pts = []
        for k in range(40):
            a = 2 * math.pi * k / 40
            pts.append((cx + s * 16 * math.sin(a) ** 3 / 16, cy - s * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 16))
        return pts
    f_bpm = font(SERIF, 22)
    ff = ffmpeg_exe()
    cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
           '-movflags', '+faststart', '-shortest', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ahead = (W - NOW_X) / PPS; back = NOW_X / PPS
    pause_t = bt[min(th['pause_bar'], len(bt) - 1)]
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
        beat = beat_at(now); bar = int(beat // bpb) + 1
        if bar <= d['nbars']:
            dr.text((W - 250, 22), 'Bar %d / %d' % (bar, d['nbars']), font=f_num, fill=(200, 204, 216))
        dr.text((W - 250, 48), '%d:%02d / %d:%02d' % (now // 60, now % 60, total // 60, total % 60), font=f_num, fill=(140, 146, 166))
        # 小節線
        first_bar = int(np.searchsorted(bt, now - back, side='right') - 2)
        for b in range(max(first_bar, 0), len(bt)):
            if bt[b] > now + ahead: break
            x = NOW_X + (bt[b] - now) * PPS
            if 0 <= x <= W:
                dr.line([(x, ROLL_Y0 - 6), (x, ROLL_Y1 + 6)], fill=(34, 38, 56))
                if b + 1 <= d['nbars']:
                    dr.text((x + 3, ROLL_Y0 - 4), str(b + 1), font=f_small, fill=(70, 76, 98))
        # 録音の実音が流れる区間
        for e in recs:
            x0 = NOW_X + (e['t'] - now) * PPS; x1 = NOW_X + (e['t'] + e['d'] - now) * PPS
            if x1 < 0 or x0 > W: continue
            on = e['t'] <= now < e['t'] + e['d']
            dr.rectangle([max(x0, 0), ROLL_Y0 + 2, min(x1, W), ROLL_Y0 + 18], fill=dim(COL.get('TB', (110, 210, 250)), 0.5 if on else 0.25))
            dr.text((max(x0, 0) + 6, ROLL_Y0 + 2), ('♪ タブレット録音 %s (ループ)' if e.get('loop') else '♪ タブレット録音 %s (実音)') % (e.get('rid', '') if '_' in e.get('rid', '') else '20260922_' + e.get('rid', '')), font=f_small, fill=(230, 240, 250) if on else (150, 160, 170))
        # 倍音の共鳴 (mantra): 低い D の倍音列のうち、いま共鳴している倍音を光る線で (synth.py と同じ式・拍に同期)
        if meta.get('style') == 'mantra':
            Lc = math.log2(300.0) + 3.3 * (0.5 - 0.5 * math.cos(2 * math.pi * beat / 8.0)); best = (0, 1)
            for kh in range(1, 91):
                fk = 36.708 * kh; w = math.exp(-((math.log2(fk) - Lc) / 0.17) ** 2)
                if w < 0.06: continue
                if w > best[0]: best = (w, kh)
                mk = 69 + 12 * math.log2(fk / 440.0)
                if mk > M_HI or kh > 24: continue                     # 高い倍音は密集するので中心線だけにする
                yk = y_of(mk); col = (int(40 + 120 * w), int(90 + 150 * w), int(150 + 105 * w))
                dr.line([(0, yk), (W, yk)], fill=col, width=1 + int(2.5 * w))
            yc = y_of(min(M_HI, 69 + 12 * (Lc - math.log2(440.0))))
            dr.line([(0, yc), (W, yc)], fill=(70, 120, 170), width=1)
            fb = 36.708 * best[1]
            dr.text((W - 330, ROLL_Y0 + 6), '共鳴: 第 %d 倍音 (%d Hz)' % (best[1], round(fb)), font=f_lab, fill=(170, 220, 255))
        # 音符
        vis = np.where((T < now + ahead) & (T + D > now - back))[0]
        detach = meta.get('detach', 1.0)
        for i in vis:
            v = V[i]
            dd = D[i] if v in ('C', 'X', 'D', 'P', 'DN', 'PK') else max(0.12, D[i] * detach * DET[i])
            x0 = NOW_X + (T[i] - now) * PPS; x1 = NOW_X + (T[i] + dd - now) * PPS
            y = max(ROLL_Y0 + 2, min(ROLL_Y1 - 2, y_of(M[i]))); c = COL[v]     # 音域外の音はロールの端に寄せる
            if ROLE[i] in ('tutti', 'str') and v in STRCOL: c = STRCOL[v]          # トゥッティ・弦の小節は弦の色
            if SRC[i] in RCOL: c = RCOL[SRC[i]]                                     # サンプラーの音: どの録音の音か
            sounding = T[i] <= now < T[i] + dd
            if v in ('HB', 'DR', 'OD'): continue                                                  # 鼓動は心電図として下に描く
            if v == 'X':
                cx = x0; s = 9 if sounding else 6
                dr.polygon([(cx, y - s), (cx + s, y), (cx, y + s), (cx - s, y)], fill=c if sounding else dim(c, 0.6))
                dr.line([(cx, y), (min(x1, W), y)], fill=dim(c, 0.35)); continue
            if v == 'C':
                dr.rectangle([x0, y - 2, x1 - 1, y + 2], fill=dim(c, 0.75 if sounding else 0.4)); continue
            if v in ('P', 'PK'):
                y = ROLL_Y1 + 2; s = 7 if sounding else 4
                dr.ellipse([x0 - s, y - s, x0 + s, y + s], fill=c if sounding else dim(c, 0.55)); continue
            if v in ('D', 'DN'):
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
        # ドラムの帯 (不整脈): キック = 赤の高い棒、スネア = 白、ハイハット = 灰、タム = 橙、クラッシュ = 金。抜けた脈は空白になる
        if meta.get('style') == 'arrhythmia':
            yb = ROLL_Y1 - 6
            dr.rectangle([0, yb - 44, W, yb + 4], fill=(14, 8, 10))
            for tt, kind, gg in DRUMS:
                if tt < now - back or tt > now + ahead: continue
                x = NOW_X + (tt - now) * PPS; hit = 0 <= now - tt < 0.12
                h, c, wdt = {'kick': (36, (235, 70, 90), 5), 'snare': (26, (240, 236, 226), 4), 'hatc': (9, (130, 126, 130), 2), 'hato': (14, (170, 166, 170), 2),
                             'ride': (12, (150, 150, 170), 2), 'tom': (20, (240, 150, 70), 4), 'crash': (42, (240, 210, 110), 2)}.get(kind, (10, (120, 120, 120), 2))
                h = h * (0.55 + 0.45 * min(1.0, gg / 0.9)) * (1.25 if hit else 1.0)
                dr.rectangle([x - wdt / 2, yb - h, x + wdt / 2, yb], fill=c if (hit or x > NOW_X) else dim(c, 0.6))
        # 心電図 (1 拍 = 1 心拍): QRS の鋭い山が「ドッ」、T 波が「クン」。止まった拍は平らな線になる
        if len(LUB):
            xs = np.arange(0, W, 2, dtype=np.float64); ts = now + (xs - NOW_X) / PPS
            j = np.clip(np.searchsorted(LUB, ts), 1, len(LUB) - 1)
            near = np.where(np.abs(ts - LUB[j - 1]) < np.abs(ts - LUB[j]), j - 1, j)
            dl = ts - LUB[near]; gl = LUBG[near]
            ecg = gl * (np.exp(-(dl / 0.011) ** 2) - 0.28 * np.exp(-((dl - 0.028) / 0.01) ** 2) + 0.1 * np.exp(-((dl + 0.13) / 0.03) ** 2))
            if len(DUB):
                k2 = np.clip(np.searchsorted(DUB, ts), 1, len(DUB) - 1)
                dd = np.minimum(np.abs(ts - DUB[k2 - 1]), np.abs(ts - DUB[k2]))
                ecg = ecg + 0.22 * gl * np.exp(-((dd - 0.04) / 0.05) ** 2)
            base = ROLL_Y1 - 28; ys = base - 34 * ecg
            pts = list(zip(xs.tolist(), ys.tolist()))
            dr.line(pts[:NOW_X // 2 + 1], fill=(235, 70, 90), width=2)
            dr.line(pts[NOW_X // 2:], fill=(120, 40, 52), width=2)
            for st in SNARE[(SNARE > now - back) & (SNARE < now + ahead)]:
                sx = NOW_X + (st - now) * PPS; hit = 0 <= now - st < 0.15
                dr.ellipse([sx - (5 if hit else 3), base + 12 - (5 if hit else 3), sx + (5 if hit else 3), base + 12 + (5 if hit else 3)], fill=(245, 235, 220) if hit else (110, 100, 96))
            last = LUB[LUB <= now]
            if len(last):
                since = now - last[-1]; gnow = LUBG[len(last) - 1]
                sc = 1.0 + 0.45 * gnow * math.exp(-since / 0.11)
                bi2 = int(np.searchsorted(bt, now, side='right') - 1); bi2 = max(0, min(bi2, len(bt) - 2))
                hr = 60.0 * bpb / (bt[bi2 + 1] - bt[bi2])
                dr.polygon(heart_poly(W - 360, 44, 17 * sc), fill=(225, 55, 80) if since < 1.2 else (120, 40, 52))
                dr.text((W - 336, 30), '%d' % round(hr), font=f_bpm, fill=(236, 200, 200))
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
