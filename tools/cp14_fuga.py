#!/usr/bin/env python3
"""Contrapunctus 14 completed as a piano requiem-fugue on the 2026-09-24 recording (x4, frame notes x16).

Subject I from the recording, subject III B-A-C-H and the Art of Fugue main theme, each in its own section and
then combined; the held bass frame follows Dies irae; hands spread twice as wide; ends in D minor.

piano_solo_8x re-made: a through-composed 4-voice fugue flowing inside held outer notes (quarters x16).

The outer notes (LH below, RH above) are struck once and held down for 16 quarters, staggered by 8, while the fugue
voices move legatissimo between them; the damper pedal only touches the frame onsets.  Fugue construction below.

Late-Bach style 4-voice piano fugue built from the transcribed recordings.

Each recording becomes one voice (A, S, B, T - the entry order of Contrapunctus 1).  Melodies are reduced to one
line, quantised to a quarter-note grid, snapped to D minor, and then corrected by a beam search for
strict counterpoint (consonance on strong beats, suspensions allowed, no parallel 5ths/8ves, no crossing).
Fugal frame: exposition with subject/answer, later entries in inversion and augmentation, final stretto,
pedal point on D and a Picardy-third close.
"""
import itertools, json, sys
import numpy as np
import mido

STRETCH = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
Q = 0.2 * STRETCH  # seconds per quarter: x4 -> 0.8 s (75 bpm), x8 -> 1.6 s (37.5 bpm)
DEG = [0, 2, 3, 5, 7, 8, 10]  # D minor (natural) above D
ALTO, SOP, BASS, TEN = 0, 1, 2, 3
RANGE = {SOP: (64, 79), ALTO: (55, 70), TEN: (45, 60), BASS: (36, 51)}  # hands spread twice as wide
FRAME_LO, FRAME_HI = (24, 36), (79, 91)  # held outer notes: LH below, RH above
FRAME = 16  # quarters: the outer notes are quarter notes stretched x16
CLASH = {1, 2, 6, 11}
DIES_IRAE = [5, 4, 5, 2, 4, 0, 2, 2, 5, 7, 5, 4, 2, 0, 4, 2]  # F E F D E C D D  F G F E D C E D
ORDER = [SOP, ALTO, TEN, BASS]  # top to bottom
VOICE_OF_REC = [ALTO, SOP, BASS, TEN]
SUBJ_RHYTHM = [2, 2, 2, 2, 1, 1, 2, 4]
E = sum(SUBJ_RHYTHM)  # 16 quarters


def m(step):
    return 14 + 12 * (step // 7) + DEG[step % 7]


STEP_OF = {}
for s in range(0, 80):
    STEP_OF.setdefault(m(s), s)


def snap(p):
    return min(range(0, 80), key=lambda s: (abs(m(s) - p), m(s)))


def place(step, prev, voice):
    lo, hi = RANGE[voice]
    opts = [step + 7 * k for k in range(-8, 9) if lo <= m(step + 7 * k) <= hi]
    return min(opts, key=lambda s: abs(s - prev))


def center(voice):
    lo, hi = RANGE[voice]
    return snap((lo + hi) // 2)


def melody(events, voice):
    """one line per quarter slot: list of step|None (None = no sound)"""
    n = int(np.ceil(max(e for _, e, _, _ in events) * STRETCH / Q))
    w = Q / STRETCH
    out, prev_p = [], None
    for k in range(n):
        a0, a1 = k * w, (k + 1) * w
        sal = {}
        for s, e, p, a in events:
            if s < a1 and e > a0:
                bonus = 3.0 if a0 <= s < a1 else 1.0  # new notes win over sustained ones
                sal[p] = sal.get(p, 0) + bonus * a * (min(e, a1) - max(s, a0))
        if not sal:
            out.append(None)
            continue
        best = max(sal, key=sal.get)
        if prev_p in sal and sal[prev_p] >= 0.6 * sal[best]:
            best = prev_p
        out.append(best)
        prev_p = best
    # short gaps are held, long gaps become rests
    res, i = list(out), 0
    while i < len(res):
        if res[i] is None:
            j = i
            while j < len(res) and res[j] is None:
                j += 1
            if i > 0 and j - i <= 8 and res[i - 1] is not None:
                for k in range(i, j):
                    res[k] = res[i - 1]
            i = j
        else:
            i += 1
    steps, prev = [], center(voice)
    for p in res:
        if p is None:
            steps.append(None)
        else:
            prev = place(snap(p), prev, voice)
            steps.append(prev)
    return diminute(steps, voice)


def diminute(steps, voice):
    """Bach-style diminution: long held notes become stepwise quarter motion toward the next skeleton note."""
    out, i = list(steps), 0
    lo, hi = RANGE[voice]
    while i < len(steps):
        a = steps[i]
        j = i
        while j < len(steps) and steps[j] == a:
            j += 1
        L = j - i
        if a is not None and L >= 3:
            b = steps[j] if j < len(steps) else None
            d = (b - a) if b is not None else 0
            for k in range(L):
                p = a + (round(d * k / L) if abs(d) >= 2 else [0, 1, 0, -1][k % 4])
                out[i + k] = p if lo <= m(p) <= hi else a
        i = j
    return out


def expand(pitches, rhythm, voice, start_step=None):
    """subject statement as per-slot cells (step, onset)"""
    cells, prev = [], start_step if start_step is not None else center(voice)
    for st, d in zip(pitches, rhythm):
        prev = place(st, prev, voice)
        cells.append((prev, True))
        cells += [(prev, False)] * (d - 1)
    return cells


def main(notes_json, mid_out):
    rec = json.load(open(notes_json))
    mel = {VOICE_OF_REC[int(k)]: melody(v, VOICE_OF_REC[int(k)]) for k, v in rec.items()}

    # ---- subject: D + six degrees taken from the opening of the first recording + D
    degs, last = [], None
    for st in mel[ALTO]:
        if st is not None and st % 7 != last:
            degs.append(st % 7)
            last = st % 7
        if len(degs) == 6:
            break
    subj = [0] + degs + [0]
    for i in range(len(subj) - 2, 0, -1):  # avoid repeated notes; first and last stay on D
        if subj[i] == subj[i + 1] or subj[i] == subj[i - 1]:
            subj[i] = (subj[i] + 1) % 7
    answer = [(d + 4) for d in subj]  # answer at the fifth (A)
    # Contrapunctus 14 completed: subject I from the recording, subject III B-A-C-H, and the Art of Fugue main
    # theme that Bach meant to combine with them.  (steps above D, rhythm in quarters, chromatic alterations)
    Z = [0] * 8
    SA = (subj, SUBJ_RHYTHM, Z)
    SA_ANS = (answer, SUBJ_RHYTHM, Z)
    SA_INV = ([(-d) % 7 for d in subj], SUBJ_RHYTHM, Z)
    BACH = ([-2, -3, -1, -2, -1, 0], [2, 2, 2, 2, 2, 6], [0, 0, 0, 1, 1, 0])  # Bb A C B-natural C# D
    BACH_ANS = ([d + 4 for d in BACH[0]], BACH[1], BACH[2])
    MAIN = ([0, 4, 2, 0, -1, 0, 1, 2], [2, 2, 2, 2, 2, 1, 1, 4], [0, 0, 0, 0, 1, 0, 0, 0])  # D A F D C# D E F
    MAIN_ANS = ([d + 4 for d in MAIN[0]], MAIN[1], MAIN[2])
    ALT = {}

    def put(v, theme, t, lim, aug=1):
        pit, rh, alts = theme
        rh = [d * aug for d in rh]
        k = 0
        prev = center(v)
        for st, d, al in zip(pit, rh, alts):
            prev = place(st, prev, v)
            for j in range(d):
                if t + k < lim:
                    grid[v][t + k] = (prev, j == 0, True, True)
                    if j == 0 and al:
                        ALT[(v, t + k)] = al
                k += 1
    inv = [(-d) % 7 for d in subj]  # melodic inversion around D
    print("subject degrees:", subj)

    # ---- per-voice grid: cells (step|None, onset, fixed)
    total_body = max((VOICE_OF_REC.index(v) + 1) * E + len(mel[v]) for v in mel)
    grid = {v: [None] * total_body for v in ORDER}
    for idx, v in enumerate(VOICE_OF_REC):
        t = idx * E
        sub = subj if idx % 2 == 0 else answer
        for k, (st, on) in enumerate(expand(sub, SUBJ_RHYTHM, v)):
            grid[v][t + k] = (st, on, True, True)
        t += E
        prev = None
        for k, st in enumerate(mel[v]):
            if t + k < total_body and st is not None:
                grid[v][t + k] = (st, st != prev, False, False)
            prev = st
    # middle entries in three sections, then the three subjects combined (as Bach planned for Contrapunctus 14)
    rot = [SOP, TEN, ALTO, BASS]
    t, i = 4 * E + 16, 0
    while t + 2 * E < total_body:
        frac = t / total_body
        v = rot[i % 4]
        w = rot[(i + 2) % 4]
        x = rot[(i + 1) % 4]
        if frac < 0.3:  # I: subject from the recording, rectus / inversus / answer
            put(v, [SA, SA_INV, SA_ANS][i % 3], t, total_body)
        elif frac < 0.55:  # II: B-A-C-H enters, then joins subject I
            put(v, [BACH, BACH_ANS][i % 2], t, total_body)
            if i % 2:
                put(w, SA, t + 4, total_body)
        elif frac < 0.8:  # III: the main theme, combined with B-A-C-H
            put(v, [MAIN, MAIN_ANS][i % 2], t, total_body)
            put(w, [BACH, BACH_ANS][i % 2], t + 4, total_body)
        else:  # IV: all three subjects at once
            put(v, MAIN, t, total_body)
            put(w, BACH_ANS, t + 2, total_body)
            put(x, SA, t + 4, total_body)
        t += 32
        i += 1
    # ---- final stretto: main theme augmented in the bass, the three subjects above it
    tail = 2 * E + 4 + 16
    for v in ORDER:
        grid[v] += [None] * tail
    s0 = total_body
    end = s0 + 2 * E + 4
    put(BASS, MAIN, s0, end, aug=2)
    put(TEN, SA, s0 + 4, end)
    put(ALTO, BACH_ANS, s0 + 8, end)
    put(SOP, SA_ANS, s0 + 12, end)
    put(TEN, BACH, s0 + 4 + E, end)
    put(SOP, MAIN_ANS, s0 + 12 + E, end)
    for v in ORDER:  # after its last entry a voice holds its note (re-sounded each bar) up to the pedal point
        last_st = None
        for j in range(s0, end):
            if grid[v][j] is not None:
                last_st = grid[v][j][0]
            elif last_st is not None:
                grid[v][j] = (last_st, (j - s0) % 4 == 0, False, False)
    pedal = end
    bass_d = snap(38)  # D2
    for j in range(pedal, pedal + 16):
        grid[BASS][j] = (bass_d, j == pedal, True, False)
    final = {SOP: snap(74), ALTO: snap(65), TEN: snap(57), BASS: bass_d}  # D5 F4 A3 D2: requiem ends in minor
    for v in (SOP, ALTO, TEN):
        for j in range(pedal, pedal + 8):
            prev = grid[v][pedal - 1][0] if grid[v][pedal - 1] else center(v)
            grid[v][j] = (prev, j % 4 == 0, False, False)
        for j in range(pedal + 8, pedal + 16):
            grid[v][j] = (final[v], j == pedal + 8, True, False)
    n = len(grid[SOP])

    # keep the fugue flowing: while fewer than two voices sound, a resting voice carries on from its last note
    # (re-struck every half bar, free for the counterpoint search to move) until the others come back
    carried = 0
    for k in range(1, n):
        if sum(grid[v][k] is not None for v in ORDER) < 2:
            for v in ORDER:
                if grid[v][k] is None and grid[v][k - 1] is not None:
                    grid[v][k] = (grid[v][k - 1][0], k % 2 == 0, False, False)
                    carried += 1
                    break
    print("carried slots:", carried)

    # ---- counterpoint correction (beam search)
    CONS = {0, 3, 4, 7, 8, 9}
    beam = [(0.0, (None,) * 4, [])]
    for k in range(n):
        strong = k % 2 == 0
        new = []
        for cost0, prevs, path in beam:
            cands, dev = [], []
            for vi, v in enumerate(ORDER):
                c = grid[v][k]
                if c is None:
                    cands.append([None]); dev.append([0])
                elif not c[1] and prevs[vi] is not None and not c[2]:
                    cands.append([prevs[vi]]); dev.append([0])  # tie
                elif c[2]:
                    cands.append([c[0]]); dev.append([0])
                else:
                    lo, hi = RANGE[v]
                    opts = [(c[0] + d, abs(d) * 2) for d in (0, -1, 1, -2, 2) if lo <= m(c[0] + d) <= hi]
                    cands.append([o for o, _ in opts]); dev.append([x for _, x in opts])
            for combo in itertools.product(*[list(zip(c, d)) for c, d in zip(cands, dev)]):
                st = [x[0] for x in combo]
                cost = cost0 + sum(x[1] for x in combo)
                mids = [m(s) if s is not None else None for s in st]
                pm = [m(s) if s is not None else None for s in prevs]
                sounding = [i for i in range(4) if mids[i] is not None]
                low = max(sounding) if sounding else None
                for a, b in itertools.combinations(sounding, 2):
                    iv = mids[a] - mids[b]
                    if iv < 0:
                        cost += 5  # crossing
                    ic = abs(iv) % 12
                    diss = ic not in CONS and not (ic == 5 and b != low)
                    if diss:
                        held = st[a] == prevs[a] or st[b] == prevs[b]
                        cost += (1.0 if held else 6.0) if strong else 1.5
                    if iv == 0:
                        cost += 4
                    if pm[a] is not None and pm[b] is not None and st[a] != prevs[a] and st[b] != prevs[b]:
                        pic = abs(pm[a] - pm[b]) % 12
                        if pic == ic and ic in (0, 7) and (mids[a] - pm[a]) * (mids[b] - pm[b]) > 0:
                            cost += 12  # parallel fifths / octaves
                for i in sounding:
                    if pm[i] is not None:
                        leap = abs(mids[i] - pm[i])
                        cost += 3 if leap == 6 else (2 if leap > 7 else 0)
                for a, b in ((0, 1), (1, 2)):
                    if mids[a] is not None and mids[b] is not None and mids[a] - mids[b] > 12:
                        cost += 1
                new.append((cost, tuple(st), path))
        new.sort(key=lambda x: x[0])
        beam, seen = [], set()
        for c, st, path in new:
            if st in seen:
                continue
            seen.add(st)
            beam.append((c, st, path + [st]))
            if len(beam) == 10:
                break
    chosen = beam[0][2]
    print(f"counterpoint cost {beam[0][0]:.0f} over {n} quarters")

    # ---- notes (with passing tones, leading tones, Picardy third)
    msgs, raw, fug = [], [], []
    vel_base = {SOP: 60, ALTO: 54, TEN: 52, BASS: 58}
    for vi, v in enumerate(ORDER):
        notes = []  # [start_q, dur_q, step, subject?]
        for k in range(n):
            st = chosen[k][vi]
            c = grid[v][k]
            if st is None:
                continue
            onset = c is not None and c[1] or not notes or notes[-1][2] != st or notes[-1][0] + notes[-1][1] != k
            if onset:
                notes.append([k, 1, st, bool(c and c[3]), ALT.get((v, k), 0)])
            else:
                notes[-1][1] += 1
        out = []
        for i, (s, d, st, sj, al) in enumerate(notes):
            nxt = notes[i + 1] if i + 1 < len(notes) and notes[i + 1][0] == s + d else None
            if d == 1 and nxt and abs(nxt[2] - st) == 2 and not sj:
                out.append([s, 0.5, st, sj, 0])
                out.append([s + 0.5, 0.5, (st + nxt[2]) // 2, sj, 0])
            else:
                out.append([s, d, st, sj, al])
        for i, (s, d, st, sj, al) in enumerate(out):
            p = m(st) + al  # subjects carry their own chromatic notes (B natural, C#)
            nxt = out[i + 1] if i + 1 < len(out) else None
            if not sj and st % 7 == 6 and nxt and nxt[2] == st + 1:
                p += 1  # C -> C# leading tone
            if not sj and st % 7 == 5 and nxt and nxt[2] == st + 1 and i + 2 < len(out) and out[i + 2][2] == st + 2:
                p += 1  # Bb -> B natural, ascending melodic minor
            vel = vel_base[v] + (10 if sj else 0) + (4 if int(s) % 4 == 0 and s == int(s) else 0)
            vel = int(min(100, vel + 6 * np.sin(2 * np.pi * s / 64)))
            t0 = s * Q + np.random.default_rng(int(s * 8) + vi).normal(0, 0.006)
            # legatissimo: the key is held until just after the next note sounds, joining the line without pedal
            t1 = (s + d) * Q + (1.6 * Q if s >= pedal + 8 else 0.09)
            raw.append([max(0, t0), t1, p, vel])
            fug.append((s, s + d, p))

    # ---- the frame: an outer note below (LH) and above (RH), each a quarter stretched x16, struck once and held
    # down while the fugue flows between them.  Bass on beat 0, top on beat 8 of each span: always one fresh.
    F0 = np.array([f[0] for f in fug]); F1 = np.array([f[1] for f in fug]); FP = np.array([f[2] for f in fug])

    def frame_pick(q, lo, hi, prev, other, prefer_low):
        mask = (F0 < q + FRAME) & (F1 > q)
        over = np.minimum(F1[mask], q + FRAME) - np.maximum(F0[mask], q)
        pits = FP[mask]
        at_on = FP[(F0 <= q) & (F1 > q)]
        best, best_sc = None, 1e9
        for p in range(lo, hi + 1):
            if (p - 2) % 12 not in DEG:
                continue
            sc = 10 * float(sum(o for o, x in zip(over, pits) if abs(p - x) % 12 in CLASH))
            if other is not None and abs(p - other) % 12 in CLASH:
                sc += 20
            if prefer_low and len(at_on):
                sc += 0 if p % 12 == at_on.min() % 12 else 3  # bass: double the lowest fugue note (root)
            sc += 0.3 * abs(p - (prev if prev is not None else (lo + hi) / 2)) + (4 if p == prev else 0)
            if sc < best_sc:
                best, best_sc = p, sc
        return best

    frame_end = pedal + 8
    fb = ft = None
    q = 0
    while q < frame_end:
        di = DIES_IRAE[(q // FRAME) % len(DIES_IRAE)]  # requiem: the held bass follows Dies irae
        fb = min((p for p in range(FRAME_LO[0], FRAME_LO[1] + 1) if p % 12 == di), key=lambda p: abs(p - (fb or 31)))
        raw.append([q * Q, min(q + FRAME, frame_end) * Q + 0.05, fb, 66])
        if q + 8 < frame_end:
            ft = frame_pick(q + 8, *FRAME_HI, ft, fb, False)
            raw.append([(q + 8) * Q, min(q + 8 + FRAME, frame_end) * Q + 0.05, ft, 64])
        # damper pedal only as a touch when an outer note is struck: resonance, then clean fugue lines again
        for fq in (q, q + 8):
            if fq < frame_end:
                msgs.append((fq * Q + 0.05, 2, mido.Message("control_change", control=64, value=127)))
                msgs.append((fq * Q + 0.9 * Q, -1, mido.Message("control_change", control=64, value=0)))
        q += FRAME
    for p, vel in ((26, 58), (38, 60), (86, 50)):  # final frame: D below and D above the closing D-minor chord
        raw.append([frame_end * Q, n * Q + 1.6 * Q, p, vel])

    raw.sort()
    last = {}
    for nt in raw:  # a key struck again is released first, so the new strike is never cut off
        if nt[2] in last and last[nt[2]][1] > nt[0] - 0.01:
            last[nt[2]][1] = nt[0] - 0.01
        last[nt[2]] = nt
    for t0, t1, p, vel in raw:
        if t1 > t0:
            msgs.append((t0, 1, mido.Message("note_on", note=p, velocity=vel)))
            msgs.append((t1, 0, mido.Message("note_off", note=p, velocity=0)))
    msgs.append((frame_end * Q + 0.05, 2, mido.Message("control_change", control=64, value=127)))
    msgs.append((n * Q + 1.6 * Q, -1, mido.Message("control_change", control=64, value=0)))
    msgs.sort(key=lambda x: (x[0], x[1]))
    mf = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
    tr.append(mido.Message("program_change", program=0))
    tr.append(mido.Message("control_change", control=91, value=55))
    prev = 0
    for t, _, msg in msgs:
        tick = int(round(t * 960))
        tr.append(msg.copy(time=max(0, tick - prev)))
        prev = max(prev, tick)
    mf.save(mid_out)
    print(f"{sum(1 for _, _, x in msgs if x.type == 'note_on')} notes, {n*Q/60:.1f} min -> {mid_out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
