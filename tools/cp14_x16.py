#!/usr/bin/env python3
"""J.S. Bach, Die Kunst der Fuge BWV 1080, Contrapunctus 14 (Fuga a 3 soggetti, unfinished), every note x16.

Source: Mutopia Project edition (after Breitkopf & Haertel 1885, public domain), converted to MIDI by LilyPond.
Base tempo: quarter = 0.5 s (half note = 60, about 8 minutes for the 239 bars); x16 -> one quarter = 8 s.
Every note is kept exactly as written, only 16 times longer: the keys are held for the full stretched value,
and notes longer than 1.5 stretched quarters are softly re-sounded every quarter so they do not die away.
Pedal: syncopated legato pedal changed on every (stretched) quarter so the long notes ring into each other
without blurring the harmony.  The piece ends where Bach's manuscript breaks off.
"""
import sys
import mido

BASE_Q = 0.5
STRETCH = 16
Q = BASE_Q * STRETCH  # 8 s per quarter
VEL = {1: 60, 2: 56, 3: 56, 4: 62}  # soprano, alto, tenor, bass (track index in the LilyPond MIDI)


def main(src, out):
    mf = mido.MidiFile(src)
    tpb = mf.ticks_per_beat
    notes = []
    for i, tr in enumerate(mf.tracks):
        t, on = 0, {}
        for m in tr:
            t += m.time
            if m.type == "note_on" and m.velocity > 0:
                on[m.note] = t
            elif m.type in ("note_off", "note_on") and m.note in on:
                s = on.pop(m.note)
                notes.append([s / tpb * Q, t / tpb * Q, m.note, VEL.get(i, 58)])
    notes.sort()
    lead = notes[0][0]  # the edition opens with a rest; x16 it would be 16 s of silence
    notes = [[a - lead, b - lead, p, v] for a, b, p, v in notes]
    end_q = max(n[1] for n in notes) / Q
    # a piano tone dies away long before a note stretched x16 ends (a whole note lasts 32 s): notes longer than
    # one and a half stretched quarters are re-sounded softly every quarter, so the written value is heard to the end
    sounded = []
    for t0, t1, p, v in notes:
        t = t0
        first = True
        while t1 - t > 1.5 * Q:
            sounded.append([t, t + Q + 0.05, p, v if first else max(30, v - 16)])
            t += Q
            first = False
        sounded.append([t, t1, p, v if first else max(30, v - 16)])
    notes = sorted(sounded)
    last = {}
    for n in notes:  # a key struck again is released just before, so the new strike is never cut off
        if n[2] in last and last[n[2]][1] > n[0] - 0.02:
            last[n[2]][1] = n[0] - 0.02
        last[n[2]] = n
    msgs = []
    for t0, t1, p, v in notes:
        msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=v)))
        msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    q = 0
    while q < end_q:
        msgs.append((max(0.0, q * Q - 0.03), -1, mido.Message("control_change", control=64, value=0)))
        msgs.append((q * Q + 0.25, 2, mido.Message("control_change", control=64, value=127)))
        q += 1
    msgs.append((end_q * Q + 6, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    o = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    o.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=55))
    prev = 0
    for t, _, m in msgs:
        tick = int(round(t * 960))
        tr.append(m.copy(time=max(0, tick - prev)))
        prev = max(prev, tick)
    o.save(out)
    print(f"{len(notes)} notes, {end_q:.0f} quarters = {end_q / 4:.0f} bars, {end_q * Q / 60:.1f} min -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
