#!/usr/bin/env python3
"""Requiem-Fuga for solo piano: transcribed recordings (x8) in fugal entries + Contrapunctus 14 themes (x8)."""
import json, sys
import mido

STRETCH = 8.0
TPS = 960  # ticks per second (tempo 1 s per beat, 960 ppq)

NOTE = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "Bb": 10, "B": 11}
MAIN = [("D", 2), ("A", 2), ("F", 2), ("D", 2), ("C#", 2), ("D", 1), ("E", 1), ("F", 3), ("G", 1), ("F", 1), ("E", 1), ("D", 2)]
ANSWER = [("A", 2), ("D", 2), ("C", 2), ("A", 2), ("G#", 2), ("A", 1), ("B", 1), ("C", 3), ("D", 1), ("C", 1), ("B", 1), ("A", 2)]
BACH = [("Bb", 2), ("A", 2), ("C", 2), ("B", 2)]


def midi(name, octv):
    return 12 * (octv + 1) + NOTE[name]


def theme_notes(seq, octv, start, beat, vel):
    t, out = start, []
    for n, b in seq:
        out.append((t, t + b * beat, midi(n, octv), vel))
        t += b * beat
    return out, t - start


def main(notes_json, mid_out):
    rec = json.load(open(notes_json))
    voices = []
    for k in sorted(rec, key=int):
        ev = [(s * STRETCH, e * STRETCH, p, a) for s, e, p, a in rec[k]]
        voices.append(ev)
    lens = [max(e for _, e, _, _ in v) for v in voices]
    step = sum(lens) / len(lens) * 0.25
    events = []
    for i, v in enumerate(voices):
        off = i * step
        for s, e, p, a in v:
            vel = int(28 + 50 * min(a, 1.0))  # requiem dynamics: pp .. mf
            events.append((s + off, e + off, p, vel))
    total = max(e for _, e, _, _ in events) + 20

    # Contrapunctus 14 themes at 8x (quarter = 72 bpm, stretched 8x)
    beat = 60 / 72 * STRETCH
    _, tl = theme_notes(MAIN, 3, 0, beat, 0)
    entries = [(MAIN, 3, 0.0, 62), (ANSWER, 4, 0.5, 52), (MAIN, 4, 1.0, 50), (BACH * 3, 4, 1.5, 55), (MAIN, 2, 2.0, 60)]
    t0 = 0.0
    while t0 < total - tl:
        for seq, octv, frac, vel in entries:
            ev, _ = theme_notes(seq, octv, t0 + frac * tl, beat, vel)
            events += [x for x in ev if x[0] < total - 10]
        t0 += tl * 3
    # final D-minor chord, pianissimo, let it ring out
    for p in (38, 50, 53, 57, 62):
        events.append((total - 18, total - 2, p, 40))

    # solo-piano constraints: one key cannot sound twice at once, <=10 simultaneous new keys per 0.3 s
    events.sort()
    playable, window = [], []
    for s, e, p, v in events:
        window = [x for x in window if s - x[0] < 0.3]
        if len(window) >= 10:
            continue
        window.append((s, p))
        playable.append([s, e, p, v])
    last = {}
    for n in playable:
        if n[2] in last and last[n[2]][1] > n[0]:
            last[n[2]][1] = n[0] - 0.02
        last[n[2]] = n

    msgs = []
    for s, e, p, v in playable:
        if e - s > 0.05:
            msgs.append((s, 1, mido.Message("note_on", note=p, velocity=v)))
            msgs.append((e, 0, mido.Message("note_off", note=p, velocity=0)))
    # sustain pedal: re-pedal on every stretched beat of the Contrapunctus (half-beat lift)
    t = 0.0
    while t < total:
        msgs.append((t, -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((t + 0.08, -1, mido.Message("control_change", control=64, value=127)))
        t += beat
    msgs.append((total, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))

    mf = mido.MidiFile(ticks_per_beat=TPS)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))  # Acoustic Grand Piano
    tr.append(mido.Message("control_change", control=91, value=70))  # hall reverb send
    prev = 0
    for t, _, m in msgs:
        tick = int(round(t * TPS))
        tr.append(m.copy(time=tick - prev))
        prev = tick
    mf.save(mid_out)
    print(f"{len(playable)} notes, {total/60:.1f} min -> {mid_out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
