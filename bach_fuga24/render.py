# -*- coding: utf-8 -*-
"""
render.py — 実音源サンプラー。
アップロードされた 16 本の録音から安定した音高の断片 (segments.json) を切り出し、
各音符へピッチシフト (再サンプリング) して 4 声のフーガを WAV に描き出す。
"""
import json, os, sys, wave, random
import numpy as np
from scipy.signal import fftconvolve

SR = 44100
BPM = 100.0
QUARTER = 60.0 / BPM

def load_wav(p):
    w = wave.open(p); sr = w.getframerate(); n = w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    assert sr == SR, (p, sr)
    return x

def f0_estimate(x, sr=SR):
    """median ACF pitch of a clip with sub-harmonic (octave) correction -> midi float or None"""
    N = 4096; hop = 2048; vals = []
    for i in range(0, max(1, len(x) - N), hop):
        fr = x[i:i + N] - x[i:i + N].mean()
        if np.sqrt((fr ** 2).mean()) < 0.01: continue
        ac = np.correlate(fr, fr, 'full')[N - 1:]; ac /= ac[0] + 1e-9
        lo, hi = int(sr / 900), int(sr / 65)
        seg = ac[lo:hi]; L = lo + int(np.argmax(seg)); pk = ac[L]
        # if half the lag is also a strong peak, the true period is L/2 (octave error guard)
        for div in (2, 3):
            L2 = int(round(L / div))
            if L2 >= lo:
                w = ac[max(lo, L2 - 3):L2 + 4]
                if w.size and w.max() > 0.85 * pk:
                    L = max(lo, L2 - 3) + int(np.argmax(w)); break
        if pk > 0.5: vals.append(69 + 12 * np.log2((sr / L) / 440))
    if len(vals) < 2: return None
    return float(np.median(vals))

class Sampler:
    def __init__(self, wavdir, segfile, seed=1):
        self.rng = random.Random(seed)
        self.audio = {}
        segs = json.load(open(segfile))
        self.segs = []
        cache = segfile + '.f0cache.json'
        f0c = json.load(open(cache)) if os.path.exists(cache) else {}
        for i, s in enumerate(segs):
            if s['src'] not in self.audio:
                self.audio[s['src']] = load_wav(os.path.join(wavdir, s['src'] + '.wav'))
            key = f"{s['src']}:{s['start']:.3f}"
            a = int(s['start'] * SR); b = int((s['start'] + s['dur']) * SR)
            if key in f0c: m = f0c[key]
            else:
                m = f0_estimate(self.audio[s['src']][a:b]); f0c[key] = m
            if m is None or abs(m - s['midi']) > 14: continue   # unreliable
            clip = self.audio[s['src']][a:b]
            self.segs.append(dict(src=s['src'], a=a, b=b, midi=m, dur=s['dur'], rms=float(np.sqrt((clip ** 2).mean()) + 1e-6)))
        json.dump(f0c, open(cache, 'w'))
        # assign sources to voices by their median pitch: low sources -> bass, high -> soprano
        srcs = sorted(self.audio, key=lambda k: np.median([s['midi'] for s in self.segs if s['src'] == k] or [60]))
        self.voice_src = {0: set(srcs[0:5]), 1: set(srcs[3:9]), 2: set(srcs[7:13]), 3: set(srcs[11:16])}
        self.midis = np.array([s['midi'] for s in self.segs])
        self.durs = np.array([s['dur'] for s in self.segs])
        self.srcarr = np.array([s['src'] for s in self.segs])

    def pick(self, voice, midi, need_sec):
        d = np.abs(self.midis - midi)
        cost = d * 1.0 + np.where(self.durs < min(need_sec, 1.2) * 0.7, 1.5, 0) \
             + np.where(np.isin(self.srcarr, list(self.voice_src[voice])), 0, 2.5)
        cost = cost + np.random.default_rng(self.rng.randrange(1 << 30)).random(len(cost)) * 1.2
        idx = np.argsort(cost)[:6]
        idx = idx[d[idx] <= 9]
        if len(idx) == 0: idx = np.argsort(d)[:1]
        return self.segs[int(idx[0])]

    def note(self, voice, midi, dur_sec):
        s = self.pick(voice, midi, dur_sec)
        x = self.audio[s['src']][s['a']:s['b']].astype(np.float32)
        ratio = 2 ** ((midi - s['midi']) / 12)          # >1 : raise pitch
        n_out = int(len(x) / ratio)
        idx = np.arange(n_out) * ratio
        y = np.interp(idx, np.arange(len(x)), x)
        n = int(dur_sec * SR)
        if len(y) >= n:
            y = y[:n]
        else:
            # granular loop of the sustained middle part with crossfades
            head = min(int(0.06 * SR), len(y) // 4)
            body = y[head:]
            xf = min(int(0.04 * SR), len(body) // 3)
            out = [y[:head]]; cur = head
            fade_in = np.linspace(0, 1, xf, dtype=np.float32); fade_out = 1 - fade_in
            last = None
            while cur < n:
                seg = body.copy()
                if last is not None and xf > 0:
                    seg[:xf] = seg[:xf] * fade_in + last[-xf:] * fade_out
                    out[-1] = out[-1][:-xf]
                out.append(seg); last = seg; cur = sum(len(o) for o in out)
            y = np.concatenate(out)[:n]
        # envelope
        a = min(int(0.012 * SR), n // 4); r = min(int(0.05 * SR), n // 3)
        env = np.ones(n, dtype=np.float32)
        env[:a] = np.linspace(0, 1, a); env[n - r:] = np.linspace(1, 0, r)
        y = y * env / (s['rms'] * 6)               # loudness normalise per sample
        return y

PAN = {0: 0.42, 1: 0.30, 2: 0.70, 3: 0.55}       # 0 = left, 1 = right
GAIN = {0: 1.0, 1: 0.85, 2: 0.85, 3: 0.95}

def render(fugue, sampler, out_wav):
    total_q = fugue['length']
    n = int((total_q * QUARTER + 3.0) * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    for nt in fugue['notes']:
        dur = nt['dur'] * QUARTER * 0.98
        y = sampler.note(nt['v'], nt['p'], dur) * GAIN[nt['v']]
        if nt['tag'] in ('S1', 'S2', 'S3', 'S4'): y *= 1.15
        st = int(nt['t'] * QUARTER * SR); en = min(n, st + len(y))
        p = PAN[nt['v']]
        L[st:en] += y[:en - st] * np.sqrt(1 - p); R[st:en] += y[:en - st] * np.sqrt(p)
    # reverb: exponentially decaying noise IR, low-passed
    rng = np.random.default_rng(7)
    ir_len = int(1.6 * SR); tt = np.arange(ir_len) / SR
    ir = rng.standard_normal(ir_len) * np.exp(-tt * 4.0)
    ir = np.convolve(ir, np.ones(8) / 8, 'same').astype(np.float32); ir /= np.abs(ir).sum() ** 0.5 * 12
    Lw = fftconvolve(L, ir)[:n]; Rw = fftconvolve(R, ir[::-1] * 0.9 + ir * 0.1)[:n]
    L = L + 0.9 * Lw; R = R + 0.9 * Rw
    peak = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    g = 0.89 / peak
    st = np.stack([L * g, R * g], 1)
    st = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    w = wave.open(out_wav, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(st.tobytes()); w.close()
    return n / SR

if __name__ == '__main__':
    fugues = json.load(open(sys.argv[1])); wavdir = sys.argv[2]; segfile = sys.argv[3]; outdir = sys.argv[4]
    sel = [int(x) for x in sys.argv[5].split(',')] if len(sys.argv) > 5 else [f['no'] for f in fugues]
    smp = Sampler(wavdir, segfile)
    print('usable segments', len(smp.segs))
    for f in fugues:
        if f['no'] not in sel: continue
        out = os.path.join(outdir, f"fuga{f['no']:02d}.wav")
        sec = render(f, smp, out)
        print(f"fuga{f['no']:02d} {f['name']} {sec:.1f}s -> {out}", flush=True)
