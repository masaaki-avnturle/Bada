#!/usr/bin/env python3
"""Requiem-Fuga: 4 recordings -> fugal mix, 4x paulstretch, + Contrapunctus 14 organ layer at 8x."""
import subprocess, sys, numpy as np
from scipy.signal import oaconvolve, butter, sosfilt

SR = 44100
rng = np.random.default_rng(14)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)


def paulstretch(x, factor, win_s=0.30):
    """Pitch-preserving extreme time stretch (Paul Nasca's algorithm)."""
    win = int(win_s * SR) // 2 * 2
    hop_out = win // 4
    hop_in = hop_out / factor
    w = np.hanning(win) ** 1.0
    n_frames = int((x.shape[1] - win) / hop_in)
    out = np.zeros((2, n_frames * hop_out + win))
    for c in range(2):
        xc = x[c]
        for i in range(n_frames):
            p = int(i * hop_in)
            spec = np.abs(np.fft.rfft(xc[p:p + win] * w))
            ph = rng.uniform(0, 2 * np.pi, spec.shape)
            frame = np.fft.irfft(spec * np.exp(1j * ph), win) * w
            out[c, i * hop_out:i * hop_out + win] += frame
    return out / (np.max(np.abs(out)) + 1e-9)


def reverb(x, seconds=6.0, wet=0.45):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)]) * np.exp(-t * 6.9 / seconds)
    ir = sosfilt(butter(2, 5000, "low", fs=SR, output="sos"), ir)  # dark stone hall
    ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
    y = np.stack([oaconvolve(x[c], ir[c])[:x.shape[1]] for c in range(2)])
    y /= np.max(np.abs(y)) + 1e-9
    return (1 - wet) * x / (np.max(np.abs(x)) + 1e-9) + wet * y


# ---------------- Contrapunctus 14 layer (organ) ----------------
NOTE = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "Bb": 10, "B": 11}


def midi(n):
    name, octv = n[:-1], int(n[-1])
    return 12 * (octv + 1) + NOTE[name]


def organ_voice(notes, beat, total_len, start, amp):
    """notes: list of (note|None, beats). Legato organ with slow swell envelopes."""
    y = np.zeros(total_len)
    pos = int(start * SR)
    for n, b in notes:
        dur = int(b * beat * SR)
        if n is not None and pos < total_len:
            L = min(dur + int(1.5 * SR), total_len - pos)  # overlap = legato tail
            t = np.arange(L) / SR
            f = 440 * 2 ** ((midi(n) - 69) / 12)
            vib = 1 + 0.002 * np.sin(2 * np.pi * 4.8 * t)
            s = sum(a * np.sin(2 * np.pi * f * h * np.cumsum(vib) / SR)
                    for h, a in [(1, 1), (2, .5), (3, .28), (4, .18), (6, .08), (8, .05)] if f * h < 9000)
            att, rel = int(1.2 * SR), int(1.5 * SR)
            env = np.ones(L)
            a = min(att, L)
            env[:a] = np.linspace(0, 1, att)[:a]
            if L > rel:
                env[-rel:] *= np.linspace(1, 0, rel)
            y[pos:pos + L] += amp * s * env
        pos += dur
    return y


# Art of Fugue main theme (Bach planned to combine it with the 3 subjects of Contrapunctus 14)
MAIN = [("D", 2), ("A", 2), ("F", 2), ("D", 2), ("C#", 2), ("D", 1), ("E", 1), ("F", 3), ("G", 1), ("F", 1), ("E", 1), ("D", 2)]
ANSWER = [("A", 2), ("D", 2), ("C", 2), ("A", 2), ("G#", 2), ("A", 1), ("B", 1), ("C", 3), ("D", 1), ("C", 1), ("B", 1), ("A", 2)]
BACH = [("Bb", 2), ("A", 2), ("C", 2), ("B", 2)]  # third subject of Contrapunctus 14: B-A-C-H

def transpose(seq, octv):
    return [(n + str(octv), b) for n, b in seq]


def contrapunctus(total_len):
    beat = 60 / 72 * 8  # quarter at 72 bpm, stretched 8x
    theme_len = sum(b for _, b in MAIN) * beat
    voices = [
        (transpose(MAIN, 3), 0.0, 0.30),  # bass/tenor: dux
        (transpose(ANSWER, 4), theme_len * 0.5, 0.22),  # alto: comes (answer in dominant)
        (transpose(MAIN, 4), theme_len * 1.0, 0.20),  # soprano
        (transpose(BACH * 3, 4), theme_len * 1.5, 0.22),  # B-A-C-H
        (transpose(MAIN, 2), theme_len * 2.0, 0.30),  # pedal
    ]
    out = np.zeros((2, total_len))
    pans = [0.5, 0.25, 0.75, 0.35, 0.5]
    t0 = 0.0
    while t0 * SR < total_len:  # repeat the exposition across the whole requiem
        for (seq, st, amp), p in zip(voices, pans):
            v = organ_voice(seq, beat, total_len, t0 + st, amp)
            out[0] += v * np.cos(p * np.pi / 2)
            out[1] += v * np.sin(p * np.pi / 2)
        t0 += theme_len * 3
    return out / (np.max(np.abs(out)) + 1e-9)


def main(paths, out_wav):
    stretched = []
    for p in paths:
        x = load(p)
        print(f"{p}: {x.shape[1]/SR:.1f}s -> stretching x4", flush=True)
        stretched.append(paulstretch(x, 4.0))
    # fugal entries: each recording enters like a fugue voice, staggered
    lens = [s.shape[1] for s in stretched]
    step = int(np.mean(lens) * 0.25)
    offsets = [i * step for i in range(len(stretched))]
    total = max(o + l for o, l in zip(offsets, lens)) + int(8 * SR)
    mix = np.zeros((2, total))
    for s, o in zip(stretched, offsets):
        fade = int(4 * SR)
        s = s.copy()
        s[:, :fade] *= np.linspace(0, 1, fade)
        s[:, -fade:] *= np.linspace(1, 0, fade)
        mix[:, o:o + s.shape[1]] += s / len(stretched) ** 0.5
    mix /= np.max(np.abs(mix)) + 1e-9
    print(f"mix length {total/SR/60:.1f} min; building Contrapunctus 14 layer", flush=True)
    cp = contrapunctus(total)
    y = 0.62 * mix + 0.38 * cp
    y = reverb(y, 6.5, 0.5)
    # gentle overall fade in/out
    fi, fo = int(6 * SR), int(12 * SR)
    y[:, :fi] *= np.linspace(0, 1, fi)
    y[:, -fo:] *= np.linspace(1, 0, fo)
    y = np.tanh(1.2 * y / np.max(np.abs(y))) * 0.89 / np.tanh(1.2)
    pcm = (y.T * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", out_wav],
                   input=pcm, check=True)
    print("wrote", out_wav, f"{total/SR:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1:-1], sys.argv[-1])
