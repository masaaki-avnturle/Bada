#!/usr/bin/env python3
"""Contrapunctus 14 (Bach + completion) in C minor, x16, both hands melody only - slow-motion Baroque ornaments.

No accompaniment: the right hand plays soprano and alto, the left hand tenor and bass, nothing else.
The technique: at x16 every long note is turned into one of Bach's ornaments played in slow motion, inside its
own voice, so each held tone becomes a line circling its main note:
  notes of 1.5 quarters or more  -> turn (main, upper, main, lower, ... back to main) in half-quarter steps (4 s)
  notes of 4 quarters or more    -> slow trill with the upper neighbour, closed by a turn
  quarter notes, only where no other voice moves meanwhile -> inverted mordent (main, upper, main)
Neighbours are the scale steps of C minor (half steps around chromatic notes).
Pedal: only a short touch on each stretched quarter, so the ornament lines stay clear.
"""
import json, sys
import mido

Q = 8.0  # quarter = 0.5 s x16
VEL = {"S": 60, "A": 55, "T": 55, "B": 60}
HAND = {"S": "RH", "A": "RH", "T": "LH", "B": "LH"}
CMIN = [0, 2, 3, 5, 7, 8, 10]


def neighbour(p, up):
    pc = p % 12
    if pc not in CMIN:
        return p + (1 if up else -1)
    q = p + (1 if up else -1)
    while q % 12 not in CMIN:
        q += 1 if up else -1
    return q


def ornament(s, d, p):
    """return [(start_q, dur_q, pitch)] for one written note"""
    if d >= 4:  # trill, then a closing turn
        out, t, k = [], s, 0
        while t < s + d - 2:
            out.append((t, 0.5, p if k % 2 == 0 else neighbour(p, True)))
            t += 0.5; k += 1
        for off in (neighbour(p, True), p, neighbour(p, False), p):
            out.append((t, 0.5, off)); t += 0.5
        return [(a, b, c) for a, b, c in out if a < s + d]
    if d >= 1.5:  # turn, ending on the main note
        n = int(round(d / 0.5))
        pat = [p, neighbour(p, True), p, neighbour(p, False)]
        seq = [pat[i % 4] for i in range(n - 1)] + [p]
        return [(s + 0.5 * i, 0.5, x) for i, x in enumerate(seq)]
    return [(s, d, p)]


def main(src, out):
    raw = json.load(open(src))
    notes = [(s, d, p - 2, v) for s, d, p, v in raw]  # D minor -> C minor
    onsets = sorted(s for s, d, p, v in notes)
    import bisect
    res = []
    orn = 0
    for s, d, p, v in notes:
        if d >= 1.5:
            parts = ornament(s, d, p)
        elif d >= 1:
            i = bisect.bisect_right(onsets, s)
            quiet = i >= len(onsets) or onsets[i] >= s + d  # nobody else moves during this quarter
            parts = [(s, 0.5, p), (s + 0.5, 0.25, neighbour(p, True)), (s + 0.75, d - 0.75, p)] if quiet else [(s, d, p)]
        else:
            parts = [(s, d, p)]
        if len(parts) > 1:
            orn += 1
        for k, (a, b, c) in enumerate(parts):
            res.append([a * Q, (a + b) * Q + 0.06, c, VEL[v] - (0 if k == 0 else 6), v])
    res.sort()
    last = {}
    for n in res:  # a key struck again is released just before, so the new strike is never cut off
        if n[2] in last and last[n[2]][1] > n[0] - 0.02:
            last[n[2]][1] = n[0] - 0.02
        last[n[2]] = n
    end = max(n[1] for n in res)
    msgs = []
    for t0, t1, p, vel, v in res:
        if t1 > t0:
            msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=vel)))
            msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    q = 0
    while q * Q < end:  # pedal: a short touch on each quarter for resonance only
        msgs.append((q * Q + 0.05, 2, mido.Message("control_change", control=64, value=127)))
        msgs.append((q * Q + 1.2, -1, mido.Message("control_change", control=64, value=0)))
        q += 1
    msgs.append((end - 10, 2, mido.Message("control_change", control=64, value=127)))
    msgs.append((end + 4, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    o = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    o.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=58))
    prev = 0
    for tt, _, m in msgs:
        tick = int(round(tt * 960))
        tr.append(m.copy(time=max(0, tick - prev)))
        prev = max(prev, tick)
    o.save(out)
    per_hand = {h: sum(1 for n in res if HAND[n[4]] == h) for h in ("RH", "LH")}
    print(f"{len(notes)} written notes, {orn} ornamented, {len(res)} played; {per_hand}; {end / 60:.1f} min")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
