#!/usr/bin/env python3
"""Bach, Contrapunctus 14 (Fuga a 3 soggetti, BWV 1080) x16 for piano four hands, with no break in the sound.

Every written note is kept, 16 times longer (quarter = 8 s).  The four voices are spread over four hands:
  Secondo LH  bass, doubled an octave below (notes of a quarter or longer)
  Secondo RH  tenor  + sustaining chord tones in the lower middle (43-60)
  Primo LH    alto   + sustaining chord tones in the middle (55-72)
  Primo RH    soprano, long notes (a half or longer) doubled an octave above
The sustaining hands: whenever two seconds would pass without a new note, one of the two inner hands (in turn)
softly sounds a tone of the harmony that is held at that moment, cycling through its notes - the long notes
keep speaking while their own keys stay down.  Four hands are needed: the outer hands hold the voices and their
doublings, the inner hands carry a voice and the sustaining tones at the same time.
Pedal: legato pedal changed on every stretched quarter.  Ends where Bach's manuscript breaks off.
"""
import sys
import numpy as np
import mido

Q = 8.0  # seconds per quarter (quarter = 0.5 s, x16)
STEP = 2.0  # longest allowed time without a new note
VOICE = {1: "S", 2: "A", 3: "T", 4: "B"}  # LilyPond MIDI track -> voice
VEL = {"S": 60, "A": 55, "T": 55, "B": 62}
HAND_OF = {"S": "Primo RH", "A": "Primo LH", "T": "Secondo RH", "B": "Secondo LH"}
FILL = [("Secondo RH", 43, 60), ("Primo LH", 55, 72)]


def main(src, out):
    mf = mido.MidiFile(src)
    tpb = mf.ticks_per_beat
    notes = []  # [t0, t1, pitch, vel, hand]
    for i, tr in enumerate(mf.tracks):
        if i not in VOICE:
            continue
        v = VOICE[i]
        t, on = 0, {}
        for m in tr:
            t += m.time
            if m.type == "note_on" and m.velocity > 0:
                on[m.note] = t
            elif m.type in ("note_off", "note_on") and m.note in on:
                s = on.pop(m.note)
                notes.append([s / tpb * Q, t / tpb * Q, m.note, VEL[v], HAND_OF[v]])
    notes.sort()
    lead = notes[0][0]
    notes = [[a - lead, b - lead, p, vel, h] for a, b, p, vel, h in notes]
    end = max(n[1] for n in notes)

    extra = []
    for t0, t1, p, vel, h in notes:
        if h == "Secondo LH" and t1 - t0 >= Q - 0.01 and p - 12 >= 21:
            extra.append([t0, t1, p - 12, vel - 8, h])  # bass octave below
        if h == "Primo RH" and t1 - t0 >= 2 * Q - 0.01 and p + 12 <= 100:
            extra.append([t0, t1, p + 12, vel - 14, h])  # soprano octave above, bell-like
    notes += extra

    written = sorted(notes)
    starts = np.array([n[0] for n in written]); ends = np.array([n[1] for n in written])
    pitches = np.array([n[2] for n in written])
    onsets = sorted(starts.tolist())
    fills, k, last_on = [], 0, -99.0
    oi = 0
    t = 0.0
    while t < end - 0.5:
        while oi < len(onsets) and onsets[oi] <= t + 0.05:
            last_on = max(last_on, onsets[oi]); oi += 1
        if t - last_on >= STEP - 0.05:
            held = sorted(set(pitches[(starts <= t) & (ends > t + 0.5)].tolist()))
            if held:
                hand, lo, hi = FILL[k % 2]
                pc = held[(k // 2) % len(held)] % 12
                cands = [p for p in range(lo, hi + 1) if p % 12 == pc]
                p = cands[len(cands) // 2] if cands else held[0]
                nxt = next((o for o in onsets[oi:] if o > t), end)
                fills.append([t, min(t + STEP + 0.3, max(t + 0.5, nxt + 0.3)), p, 38 + (k % 3) * 2, hand])
                k += 1
                last_on = t
        t = round(t + 0.5, 3)
    notes = sorted(notes + fills)

    last = {}
    for n in notes:  # a key struck again is released just before, so the new strike is never cut off
        if n[2] in last and last[n[2]][1] > n[0] - 0.02:
            last[n[2]][1] = n[0] - 0.02
        last[n[2]] = n
    msgs = []
    for t0, t1, p, vel, h in notes:
        if t1 > t0:
            msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=int(vel))))
            msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    q = 0
    while q * Q < end:
        msgs.append((max(0.0, q * Q - 0.03), -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((q * Q + 0.25, 2, mido.Message("control_change", control=64, value=127)))
        q += 1
    msgs.append((end + 6, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    o = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    o.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=55))
    prev = 0
    for tt, _, m in msgs:
        tick = int(round(tt * 960))
        tr.append(m.copy(time=max(0, tick - prev)))
        prev = max(prev, tick)
    o.save(out)
    by_hand = {}
    for n in notes:
        by_hand[n[4]] = by_hand.get(n[4], 0) + 1
    print(f"{len(written)} written+doubled, {len(fills)} sustaining tones, {end/60:.1f} min; per hand {by_hand}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
