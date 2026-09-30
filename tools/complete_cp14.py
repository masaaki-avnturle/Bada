#!/usr/bin/env python3
"""A completion of Bach's unfinished Contrapunctus 14 (Fuga a 3 soggetti, BWV 1080), following Bach's plan
as reconstructed by Nottebohm (1880): after the triple fugue breaks off (bar 239), a quadruple fugue in which
the three subjects are combined with the main theme of the Art of Fugue.

All four subjects are 20 quarters long, so they can sound together:
  S1  subject I  (bass, bar 1)            D A G F G A D
  S2  subject II (running quavers)         as stated by the alto in bars 233-238
  S3  subject III B-A-C-H                  as stated by the tenor from bar 193
  M   main theme of the Art of Fugue       D A F D C# D E F G F E D
Completion (quarters after Bach's last note):
  bar 240-241   bridge to the dominant (free counterpoint)
  2 x 6 bars    quadruple combination, voices exchanged (assignment, octaves and entry offsets of 0-2
                quarters chosen by a clash search)
  10 bars       stretto over the main theme in augmentation in the bass
  3 bars        coda on a D pedal, ending on D major
Free parts are written by a small counterpoint generator (strong-beat consonance, no parallel fifths/octaves,
no voice crossing, mostly stepwise motion).  Output: JSON list of (start_q, dur_q, midi, voice) for the whole
piece, Bach's 239 bars followed by the completion.
"""
import itertools, json, sys

RANGE = {"S": (60, 81), "A": (53, 74), "T": (45, 67), "B": (33, 57)}
ORDER = ["S", "A", "T", "B"]
DISS = {1, 2, 6, 10, 11}
ALLOWED = {2, 4, 5, 7, 9, 10, 0, 1, 11}  # D minor with C# and B natural


def seg(notes, voice, a, b):
    return [(s - a, d, p) for s, d, p, v in notes if v == voice and a <= s < b]


def main(src_json, out_json):
    bach = json.load(open(src_json))  # (start_q, dur_q, midi, voice)
    end_bach = max(s + d for s, d, p, v in bach)
    S1 = [(0, 2, 50), (2, 3, 57), (5, 1, 55), (6, 4, 53), (10, 4, 55), (14, 4, 57), (18, 2, 50)]
    S2 = seg(bach, "A", 930, 951)
    S3 = seg(bach, "T", 768, 786)
    MAIN = []
    t = 0
    for p, d in ((50, 2), (57, 2), (53, 2), (50, 2), (49, 2), (50, 1), (52, 1), (53, 3), (55, 1), (53, 1), (52, 1), (50, 2)):
        MAIN.append((t, d, p)); t += d
    SUBJ = {"S1": S1, "S2": S2, "S3": S3, "M": MAIN}
    for k, v in SUBJ.items():
        print(k, "length", max(s + d for s, d, p in v), "quarters,", len(v), "notes")

    def fit(subj, voice):
        lo, hi = RANGE[voice]
        best = None
        for sh in range(-36, 37, 12):
            ps = [p + sh for _, _, p in subj]
            out = sum(max(0, lo - p) + max(0, p - hi) for p in ps)
            mid = abs(sum(ps) / len(ps) - (lo + hi) / 2)
            key = (out, mid)
            if best is None or key < best[0]:
                best = (key, sh)
        return [(s, d, p + best[1]) for s, d, p in subj]

    def clash_cost(parts):
        """parts: {voice: [(s,d,p)]} over one block; dissonances weighted by metric position and attack"""
        cost = 0.0
        L = max(s + d for v in parts.values() for s, d, p in v)
        t = 0.0
        while t < L:
            snd = []
            for v, ns in parts.items():
                for s, d, p in ns:
                    if s <= t < s + d:
                        snd.append((p, s == t, v))
            low = min(p for p, _, _ in snd) if snd else None
            for (p1, a1, v1), (p2, a2, v2) in itertools.combinations(snd, 2):
                ic = abs(p1 - p2) % 12
                bad = ic in DISS or (ic == 5 and min(p1, p2) == low)
                if bad:
                    w = 2.0 if t % 2 == 0 else (1.0 if t % 1 == 0 else 0.3)
                    cost += w * (1.0 if (a1 or a2) else 0.5)
                if p1 == p2:
                    cost += 1
            t += 0.5
        return cost

    # search the voice assignment for the quadruple combination
    names = list(SUBJ)
    ranked = []
    for perm, offs in itertools.product(itertools.permutations(ORDER), itertools.product((0, 1, 2), repeat=4)):
        if min(offs) != 0:
            continue
        parts = {v: [(s + o, d, p) for s, d, p in fit(SUBJ[n], v)] for n, v, o in zip(names, perm, offs)}
        order_ok = all(sum(p for _, _, p in parts[a]) / len(parts[a]) > sum(p for _, _, p in parts[b]) / len(parts[b])
                       for a, b in zip(ORDER, ORDER[1:]))
        ranked.append((clash_cost(parts) + (0 if order_ok else 50), perm, parts, offs))
    ranked.sort(key=lambda x: x[0])
    c1 = ranked[0]
    c2 = next(r for r in ranked if all(a != b for a, b in zip(r[1], c1[1])))  # every voice takes another subject
    print("combination 1:", dict(zip(names, c1[1])), "entries", dict(zip(names, c1[3])), f"cost {c1[0]:.1f}")
    print("combination 2:", dict(zip(names, c2[1])), "entries", dict(zip(names, c2[3])), f"cost {c2[0]:.1f}")

    fixed = {v: [] for v in ORDER}  # absolute (start, dur, pitch)
    T0 = end_bach  # bar 240
    B1 = T0 + 8  # after a two-bar bridge
    for parts, base in ((c1[2], B1), (c2[2], B1 + 24)):
        for v, ns in parts.items():
            fixed[v] += [(base + s, d, p) for s, d, p in ns]
    # stretto over the augmented main theme in the bass
    ST = B1 + 48
    fixed["B"] += [(ST + 2 * s, 2 * d, p) for s, d, p in fit(MAIN, "B")]
    for v, name, off in (("T", "S1", 0), ("A", "S2", 4), ("S", "S3", 8), ("T", "S3", 22), ("A", "S1", 26), ("S", "M", 20)):
        fixed[v] += [(ST + off + s, d, p) for s, d, p in fit(SUBJ[name], v)]
    CODA = ST + 40
    END = CODA + 12
    fixed["B"] += [(CODA, 12, 38)]  # D pedal
    final = {"S": 74, "A": 66, "T": 57}  # D5, F#4 (Picardy), A3 over D2
    for v, p in final.items():
        fixed[v] += [(CODA + 8, 4, p)]
    # a voice may not have two fixed notes at once: later entries cut earlier ones
    for v in ORDER:
        fixed[v].sort()
        cleaned = []
        for s, d, p in fixed[v]:
            if cleaned and cleaned[-1][0] + cleaned[-1][1] > s:
                ps, pd, pp = cleaned[-1]
                cleaned[-1] = (ps, s - ps, pp)
                if cleaned[-1][1] <= 0:
                    cleaned.pop()
            cleaned.append((s, d, p))
        fixed[v] = cleaned

    # ---- free counterpoint in every quarter slot not covered by a subject
    def sounding(t, notes_by_voice, skip):
        out = {}
        for v, ns in notes_by_voice.items():
            if v == skip:
                continue
            for s, d, p in ns:
                if s <= t < s + d:
                    out[v] = p
        return out

    allv = {v: list(fixed[v]) for v in ORDER}
    # Bach's last notes, for melodic continuity at the join
    last_bach = {v: max((s, p) for s, d, p, vv in bach if vv == v)[1] for v in ORDER}
    prev = dict(last_bach)
    t = T0
    targets = {T0 + 6: {9, 1, 4}, T0 + 7: {9, 1, 4}, CODA + 4: {2, 6, 9, 7, 11}, CODA + 6: {9, 1, 4, 7}}
    while t < END:
        for v in ["B", "T", "A", "S"]:
            if any(s <= t < s + d for s, d, p in allv[v]):
                cur = [p for s, d, p in allv[v] if s <= t < s + d][0]
                prev[v] = cur
                continue
            others = sounding(t, allv, v)
            before = sounding(t - 1, allv, v)
            lo, hi = RANGE[v]
            best, bc = None, 1e9
            for p in range(lo, hi + 1):
                if p % 12 not in ALLOWED:
                    continue
                c = 0.0
                low = min(list(others.values()) + [p])
                for ov, op in others.items():
                    ic = abs(p - op) % 12
                    if ic in DISS or (ic == 5 and min(p, op) == low):
                        c += 8 if t % 2 == 0 else 5
                    if p == op:
                        c += 4
                    if ov in before and prev.get(v) is not None:
                        pic = abs(prev[v] - before[ov]) % 12
                        if pic == ic and ic in (0, 7) and p != prev[v] and op != before[ov]:
                            c += 8
                    iv, io = ORDER.index(v), ORDER.index(ov)
                    if (iv < io and p < op) or (iv > io and p > op):
                        c += 6
                leap = abs(p - prev[v]) if prev.get(v) else 2
                c += {0: 2.5, 1: 0, 2: 0, 3: 0.8, 4: 0.8}.get(leap, 2 if leap <= 7 else 6) + (5 if leap == 6 else 0)
                if p % 12 in (1, 11):
                    c += 1.5
                if t in targets and p % 12 not in targets[t]:
                    c += 6
                if c < bc:
                    best, bc = p, c
            allv[v].append((t, 1, best))
            prev[v] = best
        t += 1
    # merge repeated free quarters into longer notes
    comp = []
    for v in ORDER:
        ns = sorted(allv[v])
        merged = []
        for s, d, p in ns:
            if merged and merged[-1][2] == p and merged[-1][0] + merged[-1][1] == s and d == 1 and merged[-1][1] < 4:
                merged[-1] = (merged[-1][0], merged[-1][1] + d, p)
            else:
                merged.append((s, d, p))
        comp += [(s, d, p, v) for s, d, p in merged]
    full = [tuple(x) for x in bach] + comp
    json.dump(sorted(full), open(out_json, "w"))
    # report
    comp_parts = {v: [(s - T0, d, p) for s, d, p, vv in comp if vv == v] for v in ORDER}
    print(f"completion: {len(comp)} notes, {END - T0} quarters = {(END - T0) / 4:.0f} bars (bars 240-{int(END // 4)}),"
          f" clash score per quarter {clash_cost(comp_parts) / (END - T0):.2f}")
    bach_parts = {v: [(s - 780, d, p) for s, d, p, vv in bach if vv == v and 780 <= s < 956] for v in ORDER}
    print(f"for comparison, Bach bars 196-239 clash score per quarter {clash_cost(bach_parts) / 176:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
