# -*- coding: utf-8 -*-
"""
compose.py — J.S. Bach, Contrapunctus XIV (BWV 1080/19) を核にした 24 のフーガの作曲エンジン。

音階の秘密の原理 (the secret principle of the scale)
----------------------------------------------------
1. B-A-C-H = {B♭, A, C, B} は半音 4 つの塊 {9,10,11,0}。これを長 3 度 (4 半音) ずつ 3 回並べると
   {B♭ A C B} + {D C♯ E E♭} + {F♯ F A♭ G} = 12 音すべてを一度ずつ — B-A-C-H が 12 音階を敷き詰める。
   この 12 音列 (BACH 列) をエピソードと最終ストレッタの素材に使う。
2. D 短調の和声的音階 D E F G A B♭ C♯ を第 3 音 F を軸に鏡映すると
   D↔A, E↔G, F↔F, **B♭↔C♯**。ユーザーが名指しした 2 音は互いの鏡像である。
   この鏡映が「反行 (inversus)」の定義になる。
3. 完全 5 度 (7 半音) は 12 と互いに素なので 5 度圏をたどれば 12 の調をすべて一周する。
   D から 5 度ずつ上がる 12 調 × {正行, 反行} = 24 曲。

時間の単位: 4 分音符 = 1.0。1 小節 = 4 (alla breve 2/2)。
"""
import random, json

NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
JP = ['ハ', '嬰ハ', 'ニ', '変ホ', 'ホ', 'ヘ', '嬰ヘ', 'ト', '変イ', 'イ', '変ロ', 'ロ']

def P(name, octave):
    """'C#',4 -> midi"""
    return 12 * (octave + 1) + NAMES.index(name)

# ---------------------------------------------------------------- subjects (D minor reference)
# each: list of (midi, duration in quarters)
S1 = [(P('D',3),2),(P('A',3),2),(P('F',3),2),(P('E',3),2),(P('D',3),2),(P('C#',3),2),(P('D',3),1),(P('E',3),1),(P('F',3),2)]
# second subject: running line, designed beat-by-beat to be consonant with S1 (bass) and S3
_S2N = ['F','E','D','E','C#','D','E','F','A','G','F','E','B','A','G','F',
        'D','E','F','G','A','B','E','F','A','G','E','D','F','G','A']
S2 = [(P(n, 3), .5) for n in _S2N[:-1]] + [(P('A', 3), 1)]
# third subject: B-A-C-H, with a tail that fits S1 in the bass
S3 = [(P('Bb',3),2),(P('A',3),2),(P('C',4),2),(P('B',3),2),
      (P('A',3),1),(P('F',3),1),(P('E',3),1),(P('A',3),.5),(P('G',3),.5),(P('F',3),1),(P('G',3),1),(P('D',3),2)]
# fourth subject: the Art of Fugue theme (Contrapunctus I), the presumed missing 4th subject
S4 = [(P('D',3),2),(P('A',3),2),(P('F',3),2),(P('D',3),2),(P('C#',3),2),(P('D',3),1),(P('E',3),1),
      (P('F',3),1.5),(P('G',3),.5),(P('F',3),.5),(P('E',3),.5),(P('D',3),1)]
BACH_ROW = [P('Bb',3),P('A',3),P('C',4),P('B',3), P('D',4),P('C#',4),P('E',4),P('Eb',4), P('F#',3),P('F',3),P('Ab',3),P('G',3)]
assert len(set(p % 12 for p in BACH_ROW)) == 12

def total(seq): return sum(d for _, d in seq)
for s in (S1, S2, S3, S4): assert total(s) == 16, total(s)

# ---------------------------------------------------------------- inversion (mirror around F in D minor)
# pitch-class involution: D<->A, E<->G, F<->F, Bb<->C#, C<->B, Eb<->Ab, F#<->F#
MIRROR = {2:9, 9:2, 4:7, 7:4, 5:5, 10:1, 1:10, 0:11, 11:0, 3:8, 8:3, 6:6}

def invert(seq, anchor=None):
    """tonal inversion: pitch classes mirrored, melodic direction reversed."""
    out = []
    prev_orig = None; prev_new = None
    for p, d in seq:
        pc = MIRROR[p % 12]
        if prev_new is None:
            base = anchor if anchor is not None else p
            # nearest octave placement of pc to base
            cand = [pc + 12 * k for k in range(-1, 9)]
            q = min(cand, key=lambda x: abs(x - base))
        else:
            step = p - prev_orig
            target = prev_new - step
            cand = [pc + 12 * k for k in range(-1, 9)]
            q = min(cand, key=lambda x: abs(x - target))
        out.append((q, d)); prev_orig, prev_new = p, q
    return out

def transpose(seq, k): return [(p + k, d) for p, d in seq]

# ---------------------------------------------------------------- scale helpers (D minor reference)
HARMONIC = {2, 4, 5, 7, 9, 10, 1}         # D E F G A Bb C#
NATURAL  = {2, 4, 5, 7, 9, 10, 0}         # D E F G A Bb C
SCALE = HARMONIC | NATURAL                # allow both 7ths

CONS_ABOVE_BASS = {0, 3, 4, 7, 8, 9}      # unison, 3rds, 5th, 6ths (no 4th vs bass)
CONS_INNER = {0, 3, 4, 5, 7, 8, 9}

RANGES = {0: (36, 58), 1: (43, 65), 2: (50, 72), 3: (57, 80)}  # bass, tenor, alto, soprano
VOICE_NAMES = ['Bass', 'Tenor', 'Alto', 'Soprano']

# ---------------------------------------------------------------- Score container
class Score:
    def __init__(self):
        self.notes = []  # dict(v, t, dur, p, tag)
    def add(self, v, t, seq, tag):
        for p, d in seq:
            self.notes.append(dict(v=v, t=t, dur=d, p=p, tag=tag)); t += d
        return t
    def sounding(self, t, exclude=None):
        out = {}
        for n in self.notes:
            if n['v'] != exclude and n['t'] <= t < n['t'] + n['dur']:
                out[n['v']] = n
        return out
    def last_note(self, v, before_t):
        c = [n for n in self.notes if n['v'] == v and n['t'] + n['dur'] <= before_t + 1e-9]
        return max(c, key=lambda n: n['t']) if c else None
    def busy(self, v, t0, t1):
        return any(n['v'] == v and n['t'] < t1 and n['t'] + n['dur'] > t0 for n in self.notes)
    def end(self): return max(n['t'] + n['dur'] for n in self.notes)

# ---------------------------------------------------------------- free counterpoint generator
def gen_free(score, v, t0, t1, rng, density=1.0, key_shift=0):
    sh = key_shift
    """Fill voice v from t0 to t1 with rule-based free counterpoint (D-minor reference frame)."""
    lo, hi = RANGES[v]
    t = t0
    prev = score.last_note(v, t0)
    cur = prev['p'] if prev else (lo + hi) // 2
    prev_pitch_others = None
    while t < t1 - 1e-9:
        rem = t1 - t
        onbeat = abs(t - round(t)) < 1e-6
        # duration choice
        r = rng.random()
        if rem >= 2 and r < 0.18 * density and onbeat: d = 2
        elif rem >= 1 and (r < 0.62 or not onbeat): d = 1
        else: d = .5
        if d > rem: d = rem
        if not onbeat: d = min(d, .5)
        # occasional rest at phrase boundaries
        if onbeat and rng.random() < 0.06 * density and rem >= 4 and t > t0:
            t += 1; continue
        # every note of another voice that overlaps [t, t+d)
        overl = [n for n in score.notes if n['v'] != v and n['t'] < t + d - 1e-9 and n['t'] + n['dur'] > t + 1e-9]
        snd = {n['v']: n for n in overl if n['t'] <= t}
        cands = []
        for q in range(max(lo, cur - 7), min(hi, cur + 7) + 1):
            if ((q - sh) % 12) not in SCALE: continue
            score_q = 0.0
            iv = abs(q - cur)
            score_q -= {0: 1.2, 1: 0, 2: 0, 3: .4, 4: .5, 5: .7, 6: 3, 7: .9}.get(iv, 1.6 + 0.2 * iv)
            strong = onbeat and (round(t) % 2 == 0)
            for n in overl:
                # weight: overlap length, heavier when the other note starts on a beat inside ours
                o0 = max(t, n['t']); o1 = min(t + d, n['t'] + n['dur']); w = (o1 - o0) / d
                if abs(o0 - round(o0)) < 1e-6: w += .5
                others_low = min(m['p'] for m in overl if m['t'] <= o0 < m['t'] + m['dur'])
                if q < others_low:                      # candidate is the bass
                    ok = (n['p'] - q) % 12 in CONS_ABOVE_BASS
                elif n['p'] == others_low:               # n is the bass
                    ok = (q - n['p']) % 12 in CONS_ABOVE_BASS
                else:
                    ok = (q - n['p']) % 12 in CONS_INNER
                if not ok: score_q -= w * (3.0 if strong else (1.6 if onbeat else 0.5))
                if n['p'] == q: score_q -= 1.0 * w        # unison
                if (u := n['v']) is not None:
                    pn = score.last_note(u, n['t']) if n['t'] <= t else None
                    if pn and prev and pn['p'] != n['p'] and prev['p'] != q:
                        if (q - n['p']) % 12 in (0, 7) and (prev['p'] - pn['p']) % 12 == (q - n['p']) % 12:
                            score_q -= 4
                    if (u < v and q < n['p']) or (u > v and q > n['p']): score_q -= 3 * w   # crossing
            # bass: prefer leaps/roots; upper: stepwise
            if v == 0 and iv in (3, 4, 5, 7): score_q += .5
            # leading tone C# resolves up to D
            if prev and (prev['p'] - sh) % 12 == 1 and q - prev['p'] == 1: score_q += 1.5
            if (q - sh) % 12 == 0 and prev and q > prev['p']: score_q -= 1.0   # C natural only descending
            if (q - sh) % 12 == 1 and prev and q < prev['p'] and (prev['p'] - sh) % 12 == 2: score_q -= .8
            # gravitate to middle of range
            mid = (lo + hi) / 2
            score_q -= abs(q - mid) / 12
            score_q += rng.random() * 0.6
            cands.append((score_q, q))
        if not cands:
            t += d; continue
        cands.sort(reverse=True)
        q = cands[0][1]
        score.notes.append(dict(v=v, t=t, dur=d, p=q, tag='free'))
        prev = score.notes[-1]; cur = q
        t += d

# ---------------------------------------------------------------- the fugue plan (D minor reference frame)
def build_reference(seed=0, inversus=False, shift=0):
    """Build the fugue: subjects are inverted in the D-minor reference frame, then transposed by `shift`."""
    rng = random.Random(seed)
    sc = Score()
    B, T, A, S = 0, 1, 2, 3

    def subj(seq, k=0, inv=False):
        s = invert(seq) if inv else seq
        return transpose(s, k)

    def entries(t, plan, tag_map, fill=True):
        """plan: list of (voice, seq, transposition) all starting at t; then fill free voices until t+16"""
        for v, seq, k, tag in plan:
            s = transpose(seq, k)
            # keep inside voice range
            lo, hi = RANGES[v]
            while min(p for p, _ in s) < lo: s = transpose(s, 12)
            while max(p for p, _ in s) > hi: s = transpose(s, -12)
            sc.add(v, t, s, tag)
        return t + 16

    def fill(t0, t1, voices, density=1.0):
        for v in voices:
            if not sc.busy(v, t0, t1):
                gen_free(sc, v, t0, t1, rng, density, key_shift=shift)

    def addc(v, t, seq, tag):
        """add a line, octave-shifted into the voice's range"""
        lo, hi = RANGES[v]
        while min(p for p, _ in seq) < lo: seq = transpose(seq, 12)
        while max(p for p, _ in seq) > hi: seq = transpose(seq, -12)
        return sc.add(v, t, seq, tag)

    def K(seq): return transpose(seq, shift)

    def clamp(v, seq):
        lo, hi = RANGES[v]
        while min(p for p, _ in seq) < lo: seq = transpose(seq, 12)
        while max(p for p, _ in seq) > hi: seq = transpose(seq, -12)
        return seq

    def dissonance(lines):
        """lines: list of (start, seq). count on-beat dissonances (bass-relative)"""
        grids = []
        for st, seq in lines:
            g = {}
            tt = st
            for p, d in seq:
                q = tt
                while q < tt + d - 1e-9:
                    g[round(q * 2) / 2] = p; q += .5
                tt += d
            grids.append(g)
        bad = 0
        times = sorted(set(k for g in grids for k in g if abs(k - round(k)) < 1e-6))
        for k in times:
            snd = [g[k] for g in grids if k in g]
            if len(snd) < 2: continue
            b = min(snd)
            for p in snd:
                if p != b and (p - b) % 12 not in CONS_ABOVE_BASS: bad += 1
        return bad

    def combine(t, items, tag_of):
        """items: list of (subject_seq, offset_quarters). Try every voice assignment, keep the most consonant."""
        import itertools
        best = None
        for perm in itertools.permutations(range(4), len(items)):
            lines = [(v, t + off, clamp(v, seq)) for v, (seq, off) in zip(perm, items)]
            # voice order must match pitch order (no crossing on average)
            avg = [(v, sum(p for p, _ in s) / len(s)) for v, _, s in lines]
            if any(a[1] > b[1] for a in avg for b in avg if a[0] < b[0]): continue
            d = dissonance([(st, s) for _, st, s in lines])
            if best is None or d < best[0]: best = (d, lines)
        for v, st, s in best[1]:
            sc.add(v, st, s, tag_of[id(s)] if id(s) in tag_of else 'S?')
        return best

    def pair(t, subs, voices):
        """subs: [(seq, tag)], voices: the voices available; best permutation of voices."""
        import itertools
        best = None
        for perm in itertools.permutations(voices, len(subs)):
            lines = [(v, clamp(v, seq), tag) for v, (seq, tag) in zip(perm, subs)]
            avg = [(v, sum(p for p, _ in s) / len(s)) for v, s, _ in lines]
            if any(a[1] > b[1] for a in avg for b in avg if a[0] < b[0]): continue
            d = dissonance([(t, s) for _, s, _ in lines])
            if best is None or d < best[0]: best = (d, lines)
        if best is None:
            best = (0, [(v, clamp(v, seq), tag) for v, (seq, tag) in zip(voices, subs)])
        for v, s, tag in best[1]: sc.add(v, t, s, tag)
        return t + 16

    def quad(t, subs):
        """subs: [(seq, offset, tag)] for all four voices; S4 must land in the bass."""
        import itertools
        best = None
        for perm in itertools.permutations(range(4)):
            lines = [(v, t + off, clamp(v, seq), tag) for v, (seq, off, tag) in zip(perm, subs)]
            if [l for l in lines if l[3] == 'S4'][0][0] != 0: continue
            avg = [(v, sum(p for p, _ in s) / len(s)) for v, _, s, _ in lines]
            if any(a[1] > b[1] for a in avg for b in avg if a[0] < b[0]): continue
            d = dissonance([(st, s) for _, st, s, _ in lines])
            if best is None or d < best[0]: best = (d, lines)
        for v, st, s, tag in best[1]: sc.add(v, st, s, tag)

    inv = inversus
    s1 = invert(S1) if inv else S1
    s2 = invert(S2) if inv else S2
    s3 = invert(S3) if inv else S3
    s4 = invert(S4) if inv else S4
    row = [(p, 1) for p in BACH_ROW]
    if inv: row = invert(row)
    s1, s2, s3, s4, row = K(s1), K(s2), K(s3), K(s4), K(row)
    # In inversus the answer is at the subdominant (Bach: Cp. XII/XIII inversus mirror the tonal plan)
    ANS = -5 if inv else 7

    t = 0
    # ---- Exposition I : S1 -------------------------------------------------
    t = entries(t,  [(B, s1, -12 if not inv else -12, 'S1')], None); fill(0, 16, [])
    t = entries(t,  [(T, s1, ANS, 'S1')], None); fill(16, 32, [B], .8)
    t = entries(t,  [(A, s1, 0 if not inv else 0, 'S1')], None); fill(32, 48, [B, T], .9)
    t = entries(t,  [(S, s1, ANS + 12, 'S1')], None); fill(48, 64, [B, T, A], .9)
    # ---- Episode 1 : BACH row in sequence (2 voices, thin) ------------------
    e0 = t
    addc(A, e0, transpose(row[:8], 0), 'ROW'); addc(T, e0 + 2, transpose(row[:8], -12), 'ROW')
    addc(S, e0 + 8, transpose(row[8:], 12), 'ROW'); addc(B, e0 + 10, transpose(row[8:], -12), 'ROW')
    fill(e0, e0 + 16, [B, S], .6)
    t = e0 + 16
    # ---- Exposition II : S2 (combined with S1) ---------------------------------
    t = entries(t, [(A, s2, 0, 'S2')], None); fill(t - 16, t, [T, B], .7)
    t = pair(t, [(transpose(s2, ANS), 'S2'), (s1, 'S1')], [S, T]); fill(t - 16, t, [B, A], .7)
    t = pair(t, [(s2, 'S2'), (transpose(s1, ANS), 'S1')], [B, A]); fill(t - 16, t, [T, S], .7)
    t = pair(t, [(transpose(s2, -5 if not inv else 0), 'S2'), (s1, 'S1')], [T, S]); fill(t - 16, t, [B, A], .8)
    # ---- Episode 2 : inverted / retrograde row --------------------------------
    e0 = t
    rrow = list(reversed(row))
    addc(S, e0, transpose(rrow[:6], 12), 'ROW'); addc(A, e0 + 1, transpose(row[:6], 0), 'ROW')
    addc(T, e0 + 6, transpose(rrow[6:], 0), 'ROW'); addc(B, e0 + 7, transpose(row[6:], -12), 'ROW')
    fill(e0, e0 + 16, [S, A, T, B], .5)
    t = e0 + 16
    # ---- Exposition III : S3 = B-A-C-H -----------------------------------------
    t = entries(t, [(T, s3, -12, 'S3')], None); fill(t - 16, t, [B], .5)
    t = entries(t, [(A, s3, ANS - 12 if not inv else ANS, 'S3')], None); fill(t - 16, t, [T, B], .6)
    t = pair(t, [(s3, 'S3'), (s1, 'S1')], [S, B]); fill(t - 16, t, [T, A], .7)
    # triple combination (as in the original, bar 233 ff.): best voice assignment by search
    t = pair(t, [(s3, 'S3'), (s2, 'S2'), (s1, 'S1')], [B, A, S]); fill(t - 16, t, [T], .7)
    # ---- Episode 3 : the whole 12-tone row in stretto -------------------------
    e0 = t
    for i, v in enumerate([S, A, T, B]):
        addc(v, e0 + i * 2, transpose(row, 12 if v == S else (0 if v == A else (-12 if v == T else -24))), 'ROW')
    fill(e0, e0 + 20, [S, A, T, B], .4)
    t = e0 + 20
    # ---- Completion : quadruple combination with the Art of Fugue theme -------
    # S1 (tenor) + S3 (alto) + S2 (soprano) begin together; the bass rests two bars and then
    # the Art of Fugue theme (S4) enters — the subject Bach never wrote down in Cp. XIV.
    t0 = t
    quad(t0, [(s1, 0, 'S1'), (s3, 0, 'S3'), (s2, 0, 'S2'), (s4, 8, 'S4')])
    t = t0 + 16
    # final stretto: S1 in the soprano over the tail of S4, inner voices free
    addc(S, t, transpose(s1, 12), 'S1')
    fill(t, t + 8, [T, A], .6)
    fill(t + 8, t + 16, [T, A], .6)
    addc(B, t + 8, K([(P('A', 2), 4), (P('Bb', 2), 2), (P('A', 2), 2)] if not inv else
                       [(P('D', 2), 4), (P('C#', 2), 2), (P('D', 2), 2)]), 'free')
    t += 16
    # cadence (Picardy third): iv - V - I(major)
    if not inv:
        addc(B, t, K([(P('G', 2), 2), (P('A', 2), 2), (P('D', 2), 8)]), 'CAD')
        addc(T, t, K([(P('Bb', 3), 2), (P('C#', 4), 2), (P('D', 4), 8)]), 'CAD')
        addc(A, t, K([(P('D', 4), 2), (P('E', 4), 2), (P('F#', 4), 8)]), 'CAD')
        addc(S, t, K([(P('G', 4), 2), (P('G', 4), 1), (P('E', 4), 1), (P('A', 4), 8)]), 'CAD')
    else:
        addc(B, t, K([(P('G', 2), 2), (P('A', 2), 2), (P('D', 2), 8)]), 'CAD')
        addc(T, t, K([(P('D', 4), 2), (P('E', 4), 2), (P('D', 4), 8)]), 'CAD')
        addc(A, t, K([(P('Bb', 3), 2), (P('C#', 4), 2), (P('F#', 4), 8)]), 'CAD')
        addc(S, t, K([(P('G', 4), 2), (P('A', 4), 1), (P('G', 4), 1), (P('A', 4), 8)]), 'CAD')
    t += 12
    return sc

# ---------------------------------------------------------------- the 24 keys
def keys24():
    """12 keys along the circle of fifths from D, each rectus and inversus."""
    out = []
    k = 2  # D
    for i in range(12):
        for inv in (False, True):
            out.append(dict(tonic=k % 12, inversus=inv))
        k += 7
    return out

def build_all(seed=20260926):
    fugues = []
    for i, key in enumerate(keys24()):
        shift = (key['tonic'] - 2)
        if shift > 6: shift -= 12          # keep transposition within +-6 semitones
        sc = build_reference(seed=seed + i, inversus=key['inversus'], shift=shift)
        fugues.append(dict(no=i + 1, tonic=key['tonic'], inversus=key['inversus'], shift=shift,
                           name=f"{NAMES[key['tonic']]} minor — {'inversus' if key['inversus'] else 'rectus'}",
                           name_jp=f"{JP[key['tonic']]}短調 {'反行' if key['inversus'] else '正行'}",
                           notes=sc.notes, length=sc.end()))
    return fugues

if __name__ == '__main__':
    import sys
    f = build_all()
    for x in f:
        print(x['no'], x['name'], x['name_jp'], 'bars', x['length'] / 4, 'notes', len(x['notes']))
    json.dump(f, open(sys.argv[1] if len(sys.argv) > 1 else 'fugues.json', 'w'), ensure_ascii=False)
