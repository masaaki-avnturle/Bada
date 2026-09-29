#!/usr/bin/env python3
"""piano_solo_8x re-made with 8x quarter notes, staggered between the hands so the sound never breaks.

Four voices - RH soprano/alto, LH tenor/bass - each play notes eight quarters long (a quarter stretched x8).
Entries are staggered by two quarters and alternate hands: B (LH) on beat 0, S (RH) on 2, T (LH) on 4, A (RH) on 6
of each 8-beat cycle.  A new key is struck every two quarters and every held note overlaps the next three entries, so there is
never a gap.  Pitches come from the piano_solo_8x material (the transcribed recordings, x8, same staggered
entries): at each entry the voice takes the most salient pitch class of the music sounding under its note,
avoiding harsh clashes with the three notes already held, and moves to the nearest octave in its register.
"""
import json, sys
import numpy as np
import mido

STRETCH = 8.0
Q = 0.2 * STRETCH  # one quarter = 1.6 s
NOTE_Q = 8  # every note lasts eight quarters
VOICES = [  # name, hand, entry offset in quarters, register, velocity  (bass first: low strings ring longest)
    ("B", "LH", 0, (36, 50), 58),
    ("S", "RH", 2, (64, 79), 62),
    ("T", "LH", 4, (48, 62), 50),
    ("A", "RH", 6, (57, 70), 52),
]
CLASH = {1, 2, 6, 11}  # minor/major second, tritone, major seventh (mod 12)


def main(notes_json, mid_out):
    rec = json.load(open(notes_json))
    voices = [[(s * STRETCH, e * STRETCH, p, a) for s, e, p, a in rec[k]] for k in sorted(rec, key=int)]
    lens = [max(e for _, e, _, _ in v) for v in voices]
    step = sum(lens) / len(lens) * 0.25
    mat = [(s + i * step, e + i * step, p, a) for i, v in enumerate(voices) for s, e, p, a in v]
    S = np.array([x[0] for x in mat]); E = np.array([x[1] for x in mat])
    PC = np.array([x[2] % 12 for x in mat]); A = np.array([x[3] for x in mat])
    total = E.max()
    nq = int(total / Q)

    def ranking(t0, t1):
        mask = (S < t1) & (E > t0)
        w = np.bincount(PC[mask], weights=A[mask] * (np.minimum(E[mask], t1) - np.maximum(S[mask], t0)), minlength=12)
        return [int(p) for p in np.argsort(w)[::-1]] if w.sum() > 0 else None

    notes, held, prev = [], {}, {v[0]: None for v in VOICES}
    last_rank = [2, 9, 5, 0, 7, 10, 4, 1, 3, 6, 8, 11]  # D minor-ish fallback
    for q in range(0, nq - NOTE_Q):
        for name, hand, off, (lo, hi), vel in VOICES:
            if q % NOTE_Q != off:
                continue
            t0 = q * Q
            rank = ranking(t0, t0 + NOTE_Q * Q) or last_rank
            last_rank = rank
            others = [p for n, (p, end) in held.items() if n != name and end > t0]
            choice = None
            ok = []
            for pc in rank[:6]:
                cands = [p for p in range(lo, hi + 1) if p % 12 == pc]
                ref = prev[name] if prev[name] is not None else (lo + hi) // 2
                p = min(cands, key=lambda x: abs(x - ref))
                if all(abs(p - o) % 12 not in CLASH for o in others) and p not in others:
                    ok.append(p)
            # keep the line moving: take the best consonant pitch that is not a repeat of this voice's last note
            ok = [p for p in ok if p != prev[name]][:1] or ok[:1]
            choice = ok[0] if ok else None
            if choice is None:  # fall back to doubling a held note an octave away, always consonant
                base = others[0] if others else (lo + hi) // 2
                choice = min((p for p in range(lo, hi + 1) if p % 12 == base % 12), key=lambda x: abs(x - (prev[name] or x)))
            prev[name] = choice
            held[name] = (choice, t0 + NOTE_Q * Q)
            sw = 6 * np.sin(2 * np.pi * q / 128)  # long, slow swell
            jitter = float(np.random.default_rng(q * 7 + choice).normal(0, 0.008))
            notes.append([max(0.0, t0 + jitter), t0 + NOTE_Q * Q + 0.05, choice, int(vel + sw)])
    # close: all four hands together on the last harmony, left to ring
    tq = max(n[0] for n in notes) + 2 * Q  # next slot of the 2-quarter cycle, no gap before the close
    for name, hand, off, (lo, hi), vel in VOICES:
        notes.append([tq, tq + 12 * Q, prev[name], vel - 8])

    notes.sort()
    last = {}
    for n in notes:  # a key struck again is released just before, so the new strike is never cut off
        if n[2] in last and last[n[2]][1] > n[0] - 0.01:
            last[n[2]][1] = n[0] - 0.01
        last[n[2]] = n
    msgs = []
    for t0, t1, p, v in notes:
        msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=v)))
        msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    # legato pedal changed with each entry (every two quarters): keys hold the long notes, the pedal adds resonance
    for q in range(0, nq, 2):
        msgs.append((max(0, q * Q - 0.02), -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((q * Q + 0.12, 2, mido.Message("control_change", control=64, value=127)))
    msgs.append((tq + 12 * Q, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    mf = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=60))
    prevt = 0
    for t, _, m in msgs:
        tick = int(round(t * 960))
        tr.append(m.copy(time=max(0, tick - prevt)))
        prevt = max(prevt, tick)
    mf.save(mid_out)
    print(f"{len(notes)} notes, {(tq + 12 * Q)/60:.1f} min -> {mid_out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
