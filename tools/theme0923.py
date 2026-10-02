#!/usr/bin/env python3
"""Themes from the two 2026-09-23 recordings for the C-minor Contrapunctus 14, with voice-like sounds removed.

1. Clean: drop transcribed notes that behave like a voice or breath instead of an instrument -
   pitch wandering more than 100 cents inside the note, or a slow swell (more than 0.15 s to reach full level).
   Unpitched breath / mouth noise never becomes a note in the first place, and the result is played on piano only.
2. Theme: a smooth line through each recording's opening (each note the one nearest the previous, octaves
   folded into G3-A5), one note per 0.5 s (one quarter), snapped to C minor,
   repeated notes merged, cut to 20 quarters (the length of the Contrapunctus 14 subjects), ending on C.
3. Build the full note list (quarters, voices S A T B + X for the theme):
   intro: theme A alone, then theme B answered at the fifth;  then Bach + completion (moved after the intro);
   the theme enters in the high register every 96 quarters (A / B alternately, at the octave or fifth that clashes
   least with the fugue) and once more over the coda.
Pitches of the D-minor fugue stay as they are; uplift_cp14.py --minor moves everything down a whole tone to C minor,
so the themes are stored a whole tone up here.
"""
import json, sys
import numpy as np

CMIN = [0, 2, 3, 5, 7, 8, 10]
DISS = {1, 2, 6, 10, 11}


def clean(feats):
    keep = [f for f in feats if f["glide"] <= 100 and f["rise"] <= 0.15]
    return keep, len(feats) - len(keep)


def theme(notes, start=None):
    if start is None:
        start = min(f["s"] for f in notes)
    seq = []
    for k in range(40):
        a, b = start + 0.5 * k, start + 0.5 * (k + 1)
        act = [f for f in notes if f["s"] < b and f["e"] > a]
        if not act:
            seq.append(seq[-1] if seq else 60)
            continue
        if not seq:
            pick = max(act, key=lambda f: (f["a"], f["p"]))["p"]  # start on the strongest note
        else:  # follow a line: the sounding note nearest the previous one (octaves folded)
            pick = min((f["p"] for f in act), key=lambda q: abs(((q - seq[-1] + 6) % 12) - 6))
        prev = seq[-1] if seq else 67
        pick = min((pick + 12 * k for k in range(-5, 6) if 58 <= pick + 12 * k <= 81), key=lambda q: abs(q - prev))
        seq.append(pick)
    snapped = []
    for p in seq:
        cands = [q for q in range(p - 2, p + 3) if q % 12 in CMIN]
        snapped.append(min(cands, key=lambda q: abs(q - p)))
    mel = []
    for p in snapped:
        if mel and mel[-1][1] == p:
            mel[-1][0] += 1
        else:
            mel.append([1, p])
    out, t = [], 0
    for d, p in mel:
        if t >= 18:
            break
        d = min(d, 18 - t)
        out.append((t, d, p)); t += d
    last = out[-1][2]
    c = min((q for q in range(last - 7, last + 8) if q % 12 == 0), key=lambda q: abs(q - last))
    out.append((t, 20 - t, c))  # close on C
    lo = min(p for _, _, p in out)
    sh = 12 * round((67 - np.mean([p for _, _, p in out])) / 12)  # centre around G4
    return [(s, d, p + sh) for s, d, p in out]


def clash(theme_notes, fugue, base):
    cost = 0.0
    for s, d, p in theme_notes:
        for fs, fd, fp, v in fugue:
            if fs < base + s + d and fs + fd > base + s:
                if abs(p - fp) % 12 in DISS:
                    cost += min(base + s + d, fs + fd) - max(base + s, fs)
    return cost


def main(feat_json, cp14_json, out_json):
    feats = json.load(open(feat_json))
    themes = {}
    for name, key in (("r0923a", "A"), ("r0923b", "B")):
        kept, dropped = clean(feats[name])
        print(f"{name}: {len(feats[name])} notes, {dropped} voice-like removed, {len(kept)} kept")
        themes[key] = theme(kept)
        print(" theme", key, [(s, d, p) for s, d, p in themes[key]])
    up = lambda th, k=0: [(s, d, p + 2 + k) for s, d, p in th]  # stored a tone up (C minor after the -2)
    cp = json.load(open(cp14_json))
    INTRO = 40
    fugue = [(s + INTRO, d, p, v) for s, d, p, v in cp]
    notes = list(fugue)
    notes += [(s, d, p, "X") for s, d, p in up(themes["A"])]
    notes += [(20 + s, d, p, "X") for s, d, p in up(themes["B"], 7)]  # answer at the fifth
    end = max(s + d for s, d, p, v in fugue)
    t, k, entries = INTRO + 48, 0, []
    while t + 20 < end - 20:
        th = themes["A"] if k % 2 == 0 else themes["B"]
        best = min(((clash(up(th, sh), fugue, t), sh) for sh in (0, 7, -5, 12, -12)), key=lambda x: x[0])
        notes += [(t + s, d, p, "X") for s, d, p in up(th, best[1] + 12)]  # high register, above the fugue
        entries.append((t, "A" if k % 2 == 0 else "B", best[1]))
        t += 96; k += 1
    notes += [(end - 24 + s, d, p, "X") for s, d, p in up(themes["A"], 12)]  # over the coda
    json.dump(sorted(notes), open(out_json, "w"))
    print(f"{len(entries)} theme entries inside the fugue + intro + coda; total {end / 4:.0f} bars")


if __name__ == "__main__":
    main(*sys.argv[1:4])
