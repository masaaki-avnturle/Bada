#!/usr/bin/env python3
"""Hypnotic solo-piano version of piano_solo_8x: legato pedalling + a slowly mutating ostinato.

Melody layer: the transcribed recordings, x8, in the same staggered entries as piano_solo_8x.
Ostinato: a steady 8-pulse arpeggio cell whose chord is taken from the melody notes sounding around it and
changes by only one note at a time (a minimalist "gradual process"), with a soft bass pulse on each bar.
Sustain pedal is held and changed only when the harmony changes (at most every 4 bars), so the sound never breaks.
"""
import json, sys
import numpy as np
import mido

STRETCH = 8.0
PULSE = 0.5  # seconds per ostinato note
BAR = 8 * PULSE
CELL = [0, 1, 2, 3, 2, 1, 2, 3]  # indices into (root, a, b, c)


def main(notes_json, mid_out):
    rec = json.load(open(notes_json))
    voices = [[(s * STRETCH, e * STRETCH, p, a) for s, e, p, a in rec[k]] for k in sorted(rec, key=int)]
    lens = [max(e for _, e, _, _ in v) for v in voices]
    step = sum(lens) / len(lens) * 0.25
    mel = []
    for i, v in enumerate(voices):
        for s, e, p, a in v:
            mel.append((s + i * step, e + i * step, p, int(34 + 46 * min(a, 1.0))))
    total = max(e for _, e, _, _ in mel) + 24
    nbars = int((total - 20) / BAR)

    # harmony per bar: salient pitch classes of melody notes around the bar, mutating one note at a time
    starts = np.array([n[0] for n in mel]); ends = np.array([n[1] for n in mel])
    pcs = np.array([n[2] % 12 for n in mel]); w = np.array([n[3] for n in mel], float)
    cur, root, harm, last_change = None, None, [], -99
    for b in range(nbars):
        t0, t1 = b * BAR - 8, b * BAR + BAR + 4
        mask = (starts < t1) & (ends > t0)
        weight = np.bincount(pcs[mask], weights=w[mask] * (np.minimum(ends[mask], t1) - np.maximum(starts[mask], t0)), minlength=12)
        target = list(np.argsort(weight)[::-1][:4]) if weight.sum() > 0 else (cur or [2, 9, 5, 0])
        if cur is None:
            cur = target
        elif b - last_change >= 2 and set(target) != set(cur):
            out_pc = min((p for p in cur if p not in target), key=lambda p: weight[p], default=None)
            in_pc = max((p for p in target if p not in cur), key=lambda p: weight[p], default=None)
            if out_pc is not None and in_pc is not None:
                cur = [in_pc if p == out_pc else p for p in cur]
                last_change = b
        root = max(cur, key=lambda p: weight[p]) if weight.sum() > 0 else cur[0]
        harm.append((root, sorted(p for p in cur if p != root)[:3], b == last_change or b == 0))

    notes = list(mel)
    pedal_points = []
    for b, (root, upper, changed) in enumerate(harm):
        t = b * BAR
        r = 45 + (root - 45) % 12  # root in A2..G#3
        ups = [60 + (p - 60) % 12 for p in upper]
        ups = sorted(ups) + [60 + (upper[0] - 60) % 12 + 12] if len(upper) < 3 else sorted(ups)
        voicing = [r + 12] + ups[:3]
        swell = 0.5 + 0.5 * np.sin(2 * np.pi * b / 32)  # slow tidal dynamics
        for j, idx in enumerate(CELL):
            vel = int(24 + 14 * swell + (6 if j == 0 else 0))
            notes.append((t + j * PULSE, t + (j + 1) * PULSE + 0.05, voicing[idx], vel))
        notes.append((t, t + BAR, r - 12 if r - 12 >= 28 else r, int(30 + 10 * swell)))  # bass heartbeat
        if changed or b % 4 == 0:
            pedal_points.append(t)
    # closing: last chord held under the pedal
    root, upper, _ = harm[-1]
    tend = nbars * BAR
    for p in [45 + (root - 45) % 12 - 12, 45 + (root - 45) % 12] + [60 + (u - 60) % 12 for u in upper]:
        notes.append((tend, total - 2, p, 34))
    pedal_points.append(tend)

    # solo-piano constraints: <=10 new keys per 0.3 s, one key cannot sound twice at once
    notes.sort()
    playable, window = [], []
    for s, e, p, v in notes:
        window = [x for x in window if s - x < 0.3]
        if len(window) >= 10:
            continue
        window.append(s)
        playable.append([s, e, p, v])
    last = {}
    for n in playable:
        if n[2] in last and last[n[2]][1] > n[0]:
            last[n[2]][1] = n[0] - 0.01
        last[n[2]] = n

    msgs = []
    for s, e, p, v in playable:
        if e - s > 0.04:
            msgs.append((s, 1, mido.Message("note_on", note=p, velocity=v)))
            msgs.append((e, 0, mido.Message("note_off", note=p, velocity=0)))
    # legato (syncopated) pedalling: lift right at the new harmony, press again just after it sounds
    msgs.append((0.0, -1, mido.Message("control_change", control=64, value=127)))
    for t in pedal_points[1:]:
        msgs.append((max(0, t - 0.02), -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((t + 0.12, 2, mido.Message("control_change", control=64, value=127)))
    msgs.append((total, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))

    mf = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=60))
    prev = 0
    for t, _, msg in msgs:
        tick = int(round(t * 960))
        tr.append(msg.copy(time=max(0, tick - prev)))
        prev = max(prev, tick)
    mf.save(mid_out)
    changes = sum(1 for h in harm if h[2])
    print(f"{len(playable)} notes, {nbars} bars, {changes} harmony changes, {total/60:.1f} min -> {mid_out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
