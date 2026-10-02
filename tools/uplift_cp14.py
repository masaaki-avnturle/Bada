#!/usr/bin/env python3
"""Contrapunctus 14 (Bach + completion) re-made as a hypnotic, rising piece in C major built around C and G
(or, with --minor, as a fugue in C minor over the same C-G pulse; only the final chord turns to C major).

* The whole fugue is moved from D minor to C major: down a whole tone, then the minor third, sixth and seventh
  (E-flat, A-flat, B-flat) are raised to E, A, B.
* Tempo x4 (quarter = 2 s).
* A pulse on C and G (every 0.5 s, low register) runs from beginning to end; where C or G would clash with the
  harmony above, the pulse takes the nearest tone of that harmony instead.  It grows from single notes to
  octaves, and the whole piece rises in dynamics from beginning to end.
* Grand piano only; legato pedal changed on every quarter.
"""
import json, sys
import mido

Q = 2.0
PULSE = 0.5
VEL = {"S": 58, "A": 52, "T": 52, "B": 58, "X": 66}  # X: a theme voice above the fugue (theme0923.py)
DISS = {1, 2, 6, 10, 11}
TO_MAJOR = {3: 4, 8: 9, 10: 11}  # after the transposition to C: Eb->E, Ab->A, Bb->B
MINOR = "--minor" in sys.argv  # keep C minor: a fugue in C minor, pulse a little softer


def main(src, out):
    notes = []
    for s, d, p, v in json.load(open(src)):
        p2 = p - 2
        pc = p2 % 12
        if not MINOR:
            p2 += TO_MAJOR.get(pc, pc) - pc
        notes.append([s * Q, (s + d) * Q, p2, VEL[v]])
    end = max(n[1] for n in notes)

    def ramp(t):  # rising energy: 0 at the start, 1 at the end
        return min(1.0, t / end)

    for n in notes:
        n[3] = int(n[3] - 10 + 26 * ramp(n[0]))

    pulses = []
    t, k = 0.0, 0
    while t < end:
        snd = [p for a, b, p, v in notes if a <= t < b]
        base = [36, 43][k % 2]  # C2, G2
        p = base
        if any(abs(p - x) % 12 in DISS for x in snd):  # clash: take the nearest tone of the harmony
            cands = [q for q in range(31, 50) if any((q - x) % 12 == 0 for x in snd)]
            if cands:
                p = min(cands, key=lambda q: abs(q - base))
        r = ramp(t)
        vel = int(34 + 34 * r + (6 if k % 8 == 0 else 0)) - (8 if MINOR else 0)
        pulses.append([t, t + PULSE * 0.9, p, vel])
        if r > 0.35:
            pulses.append([t, t + PULSE * 0.9, p + 12, int(vel * 0.8)])  # octaves as the energy rises
        if r > 0.7 and k % 2 == 0:
            pulses.append([t, t + PULSE * 0.9, p - 12 if p - 12 >= 24 else p + 24, int(vel * 0.7)])
        t = round(t + PULSE, 3)
        k += 1
    allnotes = sorted(notes + pulses)
    last = {}
    for n in allnotes:  # a key struck again is released just before, so the new strike is never cut off
        if n[2] in last and last[n[2]][1] > n[0] - 0.02:
            last[n[2]][1] = n[0] - 0.02
        last[n[2]] = n
    msgs = []
    for t0, t1, p, v in allnotes:
        if t1 > t0:
            msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=max(1, min(120, v)))))
            msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    q = 0
    while q * Q < end:
        msgs.append((max(0.0, q * Q - 0.03), -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((q * Q + 0.15, 2, mido.Message("control_change", control=64, value=127)))
        q += 1
    msgs.append((end + 5, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    o = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    o.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=50))
    prev = 0
    for tt, _, m in msgs:
        tick = int(round(tt * 960))
        tr.append(m.copy(time=max(0, tick - prev)))
        prev = max(prev, tick)
    o.save(out)
    cg = sum(1 for n in pulses if n[2] % 12 in (0, 7))
    print(f"{len(notes)} fugue notes, {len(pulses)} pulse notes ({100 * cg / len(pulses):.0f}% on C or G), {end / 60:.1f} min")


if __name__ == "__main__":
    main(*[a for a in sys.argv[1:] if not a.startswith("--")][:2])
