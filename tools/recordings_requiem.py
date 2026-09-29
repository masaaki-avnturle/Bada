#!/usr/bin/env python3
"""Hypnotic Requiem-Fuga for solo piano from the four recordings: their own motifs drilled as fugue subjects,
wrapped by the 16-quarter frame.

The practice-drill melody sits in the middle register and inside each 16-quarter span; the long notes that make
the span (Dies irae bass and tenor below, a halo above) surround it and are chosen to be consonant with it.

* 16-quarter cycle (a quarter = 1.6 s, the x8 stretch).  Long notes of 8+ quarters alternate between the hands
  inside it: LH on beats 0 and 8, RH on beats 4 and 12, so a key is struck every 4 quarters and nothing breaks.
  - LH beat 0: Dies irae (opening of the chant) as a cantus firmus, one note per cycle, doubled at the octave.
  - LH beat 8 / RH beats 4, 12: pitches taken from the piano_solo_8x material, kept inside D minor and
    consonant with what is already held.
* "Piano-lesson victim" drill: the fugue subject (D G A Bb A G F D) practised over and over, subject and answer
  in turn and in different registers, sometimes breaking off after a few notes and starting again.  The
  repetitions overlap, and the number of overlapping layers grows from 1 to 4 and falls back at the end.
* Pedal changed with every long-note strike, so the drill blurs into a continuous wash.
"""
import json, sys
import numpy as np
import mido

STRETCH = 8.0
Q = 0.2 * STRETCH
CYCLE = 16
DEG = [0, 2, 3, 5, 7, 8, 10]  # D natural minor
DM_PCS = {(2 + d) % 12 for d in DEG}
DIES_IRAE = ["F", "E", "F", "D", "E", "C", "D", "D", "F", "G", "F", "E", "D", "C", "E", "D"]
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "Bb": 10}
SUBJ = [0, 3, 4, 5, 4, 3, 2, 0]  # scale degrees above D
SUBJ_R = [1, 1, 1, 1, 0.5, 0.5, 1, 2]  # quarters (8 in all)
CLASH = {1, 2, 6, 11}


def dstep(deg, octave):
    """diatonic degree (may exceed 6) in D minor -> midi, octave = midi octave of the D"""
    return 12 * (octave + 1) + 2 + 12 * (deg // 7) + DEG[deg % 7]


def main(notes_json, mid_out):
    rec = json.load(open(notes_json))
    voices = [[(s * STRETCH, e * STRETCH, p, a) for s, e, p, a in rec[k]] for k in sorted(rec, key=int)]
    lens = [max(e for _, e, _, _ in v) for v in voices]
    step = sum(lens) / len(lens) * 0.25
    mat = [(s + i * step, e + i * step, p, a) for i, v in enumerate(voices) for s, e, p, a in v]
    S = np.array([x[0] for x in mat]); E = np.array([x[1] for x in mat])
    P = np.array([x[2] % 12 for x in mat]); A = np.array([x[3] for x in mat])
    ncyc = int(E.max() / (CYCLE * Q))
    body = ncyc * CYCLE  # quarters

    def ranking(t0, t1):
        mask = (S < t1) & (E > t0)
        w = np.bincount(P[mask], weights=A[mask] * (np.minimum(E[mask], t1) - np.maximum(S[mask], t0)), minlength=12)
        order = [int(p) for p in np.argsort(w)[::-1] if w[p] > 0]
        return [p for p in order if p in DM_PCS] + [p for p in (2, 9, 5, 0, 7, 10, 4) if p not in order]

    notes = []  # [start_s, end_s, midi, vel]

    # 1) the drill (melody) lives INSIDE each 16-quarter span: phrases start on beat 4 or later and end by beat 16
    drill = []  # (start_q, end_q, midi)
    i = 0

    # the practised phrase comes from the recordings themselves: in each span one recording (in rotation, like
    # fugue voices) gives an 8-note motif - its notes sounding in that span, snapped to D minor
    SNAP = {pc: min(range(7), key=lambda d: min(abs((2 + DEG[d]) % 12 - pc), 12 - abs((2 + DEG[d]) % 12 - pc))) for pc in range(12)}
    rec_notes = [sorted((s + ri * step, p) for s, e, p, a in v) for ri, v in enumerate(voices)]

    def motif(c):
        if c % 4 == 3:
            return list(SUBJ), "subject"  # the Bach subject returns every fourth span as a refrain
        t0, t1 = c * CYCLE * Q, (c + 1) * CYCLE * Q
        for r in [(c + k) % len(voices) for k in range(len(voices))]:
            seq = [p for t, p in rec_notes[r] if t0 <= t < t1]
            if len(seq) < 4:
                continue
            degs, prev = [], 0
            for p in seq:
                oct_ = (p - 62) // 12
                d = SNAP[p % 12] + 7 * oct_ + (0 if (p % 12) >= 2 else 7)
                d = min((d + 7 * k for k in range(-3, 4)), key=lambda x: abs(x - prev))  # smooth line
                d = max(-3, min(7, d))  # middle band: A3 .. E5
                if not degs or d != degs[-1]:
                    degs.append(d)
                    prev = d
                if len(degs) == 8:
                    break
            if len(degs) >= 4:
                full = degs + degs[::-1][1:]
                return (full * 3)[:8], f"rec{r}"
        return list(SUBJ), "subject"

    sources = []

    def phrase(s, n_play, degs, tr, layers):
        for k in range(n_play):
            d = SUBJ_R[k]
            deg = degs[k] + tr
            if tr and max(x + tr for x in degs) > 7:
                deg -= 7  # keep the answer inside the middle band
            p = dstep(deg, 4)
            if tr == 4 and deg % 7 == 6:
                p += 1  # C# leading tone in the answer
            vel = int(34 + 8 * layers / 4 + (8 if k == 0 else 0) - (6 if n_play < len(SUBJ) and k == n_play - 1 else 0))
            notes.append([s * Q, (s + d) * Q + 0.03, p, vel])
            drill.append((s, s + d, p))
            s += d
        return s

    for c in range(ncyc):
        base = c * CYCLE
        frac = base / body
        layers = 1 + int(min(3, 3 * min(frac / 0.6, (1 - frac) / 0.15)))  # 1 -> 4 overlapping, back down at the end
        degs, src = motif(c)
        sources.append(src)
        for k in range(layers):
            start = base + 4 + round(k * 4 / layers * 2) / 2
            tr = 0 if k % 2 == 0 else 4  # subject, answer at the fifth, subject, answer ...
            n_play = 3 if i % 5 == 2 else (5 if i % 7 == 4 else len(SUBJ))  # the victim breaks off ...
            end = phrase(start, n_play, degs, tr, layers)
            if n_play < len(SUBJ) and end + sum(SUBJ_R) <= base + CYCLE:
                phrase(end, len(SUBJ), degs, tr, layers)  # ... and starts again from the top
            i += 1
    print("motif sources:", {k: sources.count(k) for k in sorted(set(sources))})
    D0 = np.array([d[0] for d in drill]); D1 = np.array([d[1] for d in drill]); DP = np.array([d[2] for d in drill])

    # 2) the frame: long notes that wrap the melody - bass/tenor below, a halo above - chosen to fit it
    held = []  # (midi, end_s)

    def pick(tq, dur, lo, hi, prev):
        t0 = tq * Q
        others = [p for p, e in held if e > t0 + 0.1]
        mask = (D0 < tq + dur) & (D1 > tq)
        over = np.minimum(D1[mask], tq + dur) - np.maximum(D0[mask], tq)
        best, best_score = None, 1e9
        for rank, pc in enumerate(ranking(t0, t0 + dur * Q)):
            cands = [p for p in range(lo, hi + 1) if p % 12 == pc]
            if not cands:
                continue
            p = min(cands, key=lambda x: abs(x - (prev if prev else (lo + hi) // 2)))
            clash_mel = float(sum(o for o, m in zip(over, DP[mask]) if abs(p - m) % 12 in CLASH))
            clash_held = sum(1 for o in others if abs(p - o) % 12 in CLASH or p == o)
            score = 10 * clash_mel + 20 * clash_held + rank + (2 if p == prev else 0)
            if score < best_score:
                best, best_score = p, score
        return best

    prev = {"H1": None, "T": None, "H2": None}
    for c in range(ncyc):
        base = c * CYCLE
        swell = 0.4 + 0.6 * np.sin(np.pi * c / max(1, ncyc - 1))  # one long arch over the whole piece
        t0 = base * Q
        # LH beat 0: Dies irae cantus firmus, octave-doubled, held through the whole span
        pc = PC[DIES_IRAE[c % len(DIES_IRAE)]]
        low = 36 + (pc - 36) % 12  # C2..B2
        for p in (low, low + 12):
            notes.append([t0, t0 + CYCLE * Q + 0.05, p, int(56 + 8 * swell)])
            held.append((p, t0 + CYCLE * Q))
        # RH beat 4: halo above the melody, held to the end of the span (the melody starts under it)
        # LH beat 8: tenor below the melody;  RH beat 12: second halo, carried over into the next span
        for off, dur, key, (lo, hi), vel in ((4, 12, "H1", (72, 84), 56), (8, 8, "T", (43, 55), 48), (12, 8, "H2", (69, 81), 58)):
            p = pick(base + off, dur, lo, hi, prev[key])
            prev[key] = p
            t = (base + off) * Q
            notes.append([t, t + dur * Q + 0.05, p, int(vel + 6 * swell)])
            held.append((p, t + dur * Q))
        # LH beat 12: the bass is sounded again softly, so halo above and bass below close the span together
        t12 = (base + 12) * Q
        notes.append([t12, t0 + CYCLE * Q + 0.05, low, int(46 + 6 * swell)])
        held[:] = [(p, e) for p, e in held if e > t0 - 1]
    i = len(drill)

    # requiem close: open fifth D-A, both hands, left to ring
    tend = body * Q
    for p in (26, 38, 45, 50, 57, 62):
        notes.append([tend, tend + 14 * Q, p, 52])

    notes.sort()
    last = {}
    for n in notes:  # a key struck again is released just before, so the new strike is never cut off
        if n[2] in last and last[n[2]][1] > n[0] - 0.01:
            last[n[2]][1] = n[0] - 0.01
        last[n[2]] = n
    msgs = []
    for t0, t1, p, v in notes:
        if t1 > t0:
            msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=max(1, min(110, v)))))
            msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    for q in range(0, body + 1, 4):  # pedal changed with every long-note strike (every 4 quarters)
        msgs.append((max(0, q * Q - 0.02), -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((q * Q + 0.12, 2, mido.Message("control_change", control=64, value=127)))
    msgs.append((tend + 14 * Q, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    mf = mido.MidiFile(ticks_per_beat=960)
    tr_ = mido.MidiTrack()
    mf.tracks.append(tr_)
    tr_.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr_.append(mido.Message("program_change", program=0))
    tr_.append(mido.Message("control_change", control=91, value=64))
    prevt = 0
    for tt, _, m in msgs:
        tick = int(round(tt * 960))
        tr_.append(m.copy(time=max(0, tick - prevt)))
        prevt = max(prevt, tick)
    mf.save(mid_out)
    print(f"{sum(1 for _, _, m in msgs if m.type == 'note_on')} notes, {ncyc} cycles, drill notes {i}, "
          f"{(tend + 14 * Q)/60:.1f} min -> {mid_out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
