#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
長い曲 (数時間) を分割して合成・描画する: synth.py / video.py を小節の区間ごとに呼び、音は前の区間の残響 (7 秒) を重ねてつなぎ、動画は ffmpeg で連結する。
  python render_long.py <score.json> <out_dir> [chunk_bars=192] [jobs=3] [max_bars=0 (試し用)]
  できるもの: out_dir/<name>.mp4 (全部つないだもの)、out_dir/<name>.m4a (音だけ)、out_dir/parts/<name>_NN.mp4 (送れる大きさ、30 MiB 以下に)
"""
import sys, os, json, math, subprocess
import numpy as np, soundfile as sf
from multiprocessing import Pool
import synth, video

SCORE, OUT = sys.argv[1], sys.argv[2]
CHUNK = int(sys.argv[3]) if len(sys.argv) > 3 else 192
JOBS = int(sys.argv[4]) if len(sys.argv) > 4 else 3
MAXB = int(sys.argv[5]) if len(sys.argv) > 5 else 0
TAIL = 7.0; SR = 44100
NAME = os.path.splitext(os.path.basename(SCORE))[0].replace('score_', '')

def sub_score(d, b0, b1):
    bt = d['bar_times']; T0, T1 = bt[b0], bt[b1]
    s = dict(d)
    s['notes'] = [dict(n, t=round(n['t'] - T0, 4), beat=round(n['beat'] - b0 * d['beats_per_bar'], 4)) for n in d['notes'] if T0 <= n['t'] < T1]
    s['extras'] = [dict(e, t=round(e['t'] - T0, 4), beat=round(e['beat'] - b0 * d['beats_per_bar'], 4)) for e in d['extras'] if T0 <= e['t'] < T1]
    s['harm'] = d['harm'][b0 * d['beats_per_bar']:b1 * d['beats_per_bar']]
    s['bar_times'] = [round(x - T0, 4) for x in bt[b0:b1 + 1]]; s['nbars'] = b1 - b0; s['duration'] = round(T1 - T0, 4)
    s['entries'] = [dict(e, t=round(e['t'] - T0, 4), bar=e['bar'] - b0) for e in d['entries'] if T0 <= e['t'] < T1]
    secs = [x for x in d['sections'] if x['t'] < T0]
    s['sections'] = ([dict(secs[-1], t=0.0, bar=1)] if secs else []) + [dict(x, t=round(x['t'] - T0, 4), bar=x['bar'] - b0) for x in d['sections'] if T0 <= x['t'] < T1]
    m = dict(d['meta'], fixed_peak=d['meta'].get('fixed_peak', 0.9), no_fade=True, bar_offset=b0, total_bars=d['nbars'], time_offset=T0, total_time=d['duration'])
    pb = d['meta'].get('pause_bar')
    if pb is not None and b0 <= pb < b1: m['pause_bar'] = pb - b0
    else: m.pop('pause_bar', None)
    s['meta'] = m
    return s

def do_synth(args):
    sc, wav = args
    if not os.path.exists(wav): synth.main(sc, wav)
    return wav

def do_video(args):
    sc, wav, mp4 = args
    if not os.path.exists(mp4): video.main(sc, wav, mp4)
    return mp4

if __name__ == '__main__':
    d = json.load(open(SCORE)); os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True)
    nb = min(d['nbars'], MAXB) if MAXB else d['nbars']
    chunks = [(b, min(b + CHUNK, nb)) for b in range(0, nb, CHUNK)]
    jobs = []
    for i, (b0, b1) in enumerate(chunks):
        sc = os.path.join(OUT, 'chunk%02d.json' % i); json.dump(sub_score(d, b0, b1), open(sc, 'w'), ensure_ascii=False)
        jobs.append((sc, os.path.join(OUT, 'chunk%02d.wav' % i)))
    with Pool(JOBS) as p: p.map(do_synth, jobs)
    # 音をつなぐ: 区間 k の音 + 前の区間の残響 (TAIL 秒) → 区間ごとの最終の wav (動画用) と、全体の wav
    full = sf.SoundFile(os.path.join(OUT, NAME + '.wav'), 'w', SR, 2, 'PCM_16'); carry = np.zeros((0, 2), np.float32); vjobs = []
    for i, (b0, b1) in enumerate(chunks):
        y, sr = sf.read(jobs[i][1], dtype='float32'); dur = d['bar_times'][b1] - d['bar_times'][b0]; n = int(round(dur * SR))
        seg = y[:n].copy(); seg[:len(carry)] += carry[:len(seg)]
        carry = y[n:]
        if i == len(chunks) - 1:                                             # 終わり: 残響をつけてフェード
            tail = carry.copy(); tail *= np.linspace(1, 0, len(tail))[:, None]; seg = np.concatenate([seg, tail])
        seg = np.clip(seg, -1, 1)
        vw = os.path.join(OUT, 'seg%02d.wav' % i); sf.write(vw, seg, SR, subtype='PCM_16'); full.write(seg)
        vjobs.append((jobs[i][0], vw, os.path.join(OUT, 'seg%02d.mp4' % i)))
    full.close()
    with Pool(JOBS) as p: p.map(do_video, vjobs)
    ff = video.ffmpeg_exe() if hasattr(video, 'ffmpeg_exe') else __import__('imageio_ffmpeg').get_ffmpeg_exe()
    lst = os.path.join(OUT, 'concat.txt'); open(lst, 'w').write(''.join("file '%s'\n" % os.path.abspath(v[2]) for v in vjobs))
    final = os.path.join(OUT, NAME + '.mp4')
    subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', final], check=True)
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', final, '-vn', '-c:a', 'aac', '-b:a', '96k', os.path.join(OUT, NAME + '.m4a')], check=True)
    # 送れる大きさに分ける (30 MiB 以下): 全体の長さから部の数と速さを決める
    total = sum(d['bar_times'][b1] - d['bar_times'][b0] for b0, b1 in chunks) + TAIL
    nparts = max(1, int(math.ceil(total / 1380.0))); plen = total / nparts
    vb = int(min(900, max(80, (29.0 * 8 * 1024 * 1024 / plen - 56000) / 1000)))     # kbps (音 56k を引いて)
    for k in range(nparts):
        part = os.path.join(OUT, 'parts', '%s_%02d.mp4' % (NAME, k + 1))
        subprocess.run([ff, '-y', '-loglevel', 'error', '-ss', '%.3f' % (k * plen), '-t', '%.3f' % plen, '-i', final, '-vf', 'scale=960:540',
                        '-c:v', 'libx264', '-preset', 'medium', '-b:v', '%dk' % vb, '-maxrate', '%dk' % int(vb * 1.3), '-bufsize', '2M', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '56k', '-movflags', '+faststart', part], check=True)
        print('part', k + 1, '/', nparts, os.path.getsize(part) // 1024, 'KiB', flush=True)
    print('done', final, '%.0f s' % total)
