#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contrapunctus BADA — Fuga a tre soggetti (D minor)
Contrapunctus XIV (BWV 1080/19) 風の三重フーガを、解析した音源から得たモチーフで作曲する。

  主題 I   (S1)  ← MOTHER (LUNA SEA) のサビの輪郭   D E F F# G A G F E D C# D
  主題 II  (S2)  ← トラック18 の反復音+順次進行      F F F G A A G F / D A A A ...
  主題 III (S3)  ← "B-A-D-A" (B♭ A D A) + 録音 090933 の半音隣接音型 (B♭ A G# A)
  エピソード     ← LOVELESS の隣接音型 / トラック17 の音階上行 / トラック8 のため息音型 (F-E) / 録音 090146

出力: score.json (音符イベント + セクション情報) — synth.py / video.py が読む。
"""
import json, math, random, sys, os

PC = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
NAMES = ['C','C#','D','Eb','E','F','F#','G','G#','A','Bb','B']

def n(name):
    return 12 * (int(name[-1]) + 1) + PC[name[:-1]]

def name_of(m):
    return NAMES[m % 12] + str(m // 12 - 1)

QUAL = {'': [0,4,7], 'm': [0,3,7], '7': [0,4,7,10], 'm7': [0,3,7,10], 'maj7': [0,4,7,11],
        'dim': [0,3,6], 'dim7': [0,3,6,9], 'm7b5': [0,3,6,10], 'sus4': [0,5,7]}

_chord_cache = {}
def chord(s):
    if s in _chord_cache:
        return _chord_cache[s]
    bass = None
    core = s
    if '/' in s:
        core, bass = s.split('/')
    i = 2 if len(core) > 1 and core[1] in '#b' else 1
    root = PC[core[:i]]
    q = core[i:]
    pcs = [(root + x) % 12 for x in QUAL[q]]
    c = {'name': s, 'root': root, 'pcs': pcs, 'bass': PC[bass] if bass else root,
         'third': pcs[1], 'fifth': pcs[2], 'seventh': pcs[3] if len(pcs) > 3 else None,
         'major3': QUAL[q][1] == 4, 'slash': bass is not None}
    # scale: D natural minor adjusted to the chord's chromatic tones
    base = {0, 2, 4, 5, 7, 9, 10}
    repl = {1: 0, 8: 7, 6: 5, 3: 4, 11: 10}
    for p in pcs:
        if p not in base and p in repl:
            base.discard(repl[p]); base.add(p)
    c['scale'] = sorted(base)
    _chord_cache[s] = c
    return c

def transpose(mat, semis):
    return [(d, (m + semis) if m is not None else None) for d, m in mat]

def mat(*items):
    """('D4',3) ... -> [(dur, midi)]"""
    return [(d, n(p) if p else None) for p, d in items]

# ---------------------------------------------------------------- material
# 主題 I  (MOTHER) : 5 小節
S1 = mat(('D4',3),('E4',1), ('F4',2),('F#4',1),('G4',1), ('A4',2),('G4',1),('F4',1),
         ('E4',2),('D4',1),('C#4',1), ('D4',4))
H_S1 = [['Dm']*4, ['Dm','Dm','D7','Gm'], ['A','A','Gm','Dm'], ['A7']*4, ['Dm']*4]

# 主題 II (トラック18) : 3 小節 + 1 拍  (S1 と同時開始で結合可能)
S2 = mat(('F4',.5),('F4',.5),('F4',.5),('G4',.5),('A4',.5),('A4',.5),('G4',.5),('F4',.5),
         ('D4',.5),('A3',.5),('A3',.5),('A3',.5),('D4',.5),('A3',.5),('Bb3',.5),('G3',.5),
         ('C#4',.5),('D4',.5),('C#4',.5),('E4',.5),('D4',.5),('Bb3',.5),('F3',.5),('G3',.5))
H_S2 = [['Dm']*4, ['Dm','Dm','D7','Gm'], ['A','A','Gm','Dm'], ['A7']*4]

# 主題 III (B-A-D-A) : 3 小節 + 1 拍  (S1 の 3 小節目から重ねる)
S3 = mat(('Bb4',1),('A4',1),('D5',1),('A4',1),
         ('Bb4',1),('A4',1),('G#4',1),('A4',1),
         ('F4',.5),('G4',.5),('A4',.5),('F4',.5),('E4',.5),('D4',.5),('C#4',.5),('E4',.5))
H_S3 = [['A','A','Gm','Dm'], ['A7','A7','A','A7'], ['Dm','Dm','A7','A7'], ['Dm']*4]

# 三重結合時の和声 (S1 基準, 5 小節 + S3 の余り 2 小節)
H_TRIPLE = [['Dm']*4, ['Dm','Dm','D7','Gm'], ['A','A','Gm','Dm'], ['A7','A7','A','A7'],
            ['Dm','Dm','A7','A7'], ['Dm']*4]

# ---------------------------------------------------------------- sequence lead lines (episodes)
def seq_line(chords, pattern, start_midi, lo, hi):
    """chords: 和音名のリスト (1 つにつき 2 拍). pattern: [(deg, dur)] deg = 0 root,1 third,2 fifth,
    'n+' 上隣接, 'n-' 下隣接 (直前の音基準). 各和音でパターンを 1 回演奏。"""
    out = []
    cur = start_midi
    for cs in chords:
        c = chord(cs)
        for deg, dur in pattern:
            if isinstance(deg, str):
                sc = c['scale']
                if deg == 'n+':
                    m = cur + 1
                    while m % 12 not in sc: m += 1
                else:
                    m = cur - 1
                    while m % 12 not in sc: m -= 1
            else:
                pc = c['pcs'][deg % len(c['pcs'])]
                # nearest instance of pc to cur (prefer within lo..hi)
                cands = [m for m in range(lo, hi + 1) if m % 12 == pc]
                m = min(cands, key=lambda x: (abs(x - cur), x))
            out.append((dur, m)); cur = m
    return out

# ---------------------------------------------------------------- piece container
VOICES = ['S', 'A', 'T', 'B']
RANGE = {'S': (60, 84), 'A': (55, 77), 'T': (48, 69), 'B': (36, 58)}
CENTER = {'S': 71, 'A': 65, 'T': 58, 'B': 46}
BPB = 4  # beats per bar

class Piece:
    def __init__(self, nbars):
        self.nbars = nbars
        self.N = nbars * BPB
        self.harm = ['Dm'] * self.N
        self.fixed = {v: [] for v in VOICES}     # (start, dur, midi, label)
        self.rest = {v: set() for v in VOICES}
        self.hold = set()                        # bars where free voices hold whole notes
        self.entries = []                        # (beat, label, voice)
        self.sections = []                       # (bar, title, subtitle)
        self.dyn = {}                            # bar -> gain (default 1.0)
        self.tempo = {}                          # bar -> bpm (default: main() の bpm)
        self.det = {}                            # bar -> 音の長さの比率 (奏法, default 1.0)
        self.role = {}                           # bar -> 'solo' / 'tutti' / 'both' / 'cadenza' (協奏曲用)

    def dyn_at(self, beat):
        return self.dyn.get(int(beat // BPB), 1.0)

    def set_harm(self, bar, spec):
        if isinstance(spec, str): spec = [spec]
        k = BPB // len(spec)
        for i, cs in enumerate(spec):
            for j in range(k):
                self.harm[bar * BPB + i * k + j] = cs

    def set_harms(self, bar, specs):
        for i, sp in enumerate(specs):
            self.set_harm(bar + i, sp)

    def place(self, voice, bar, material, semis=0, label=None, beat=0):
        t = bar * BPB + beat
        for d, m in material:
            if m is not None:
                self.fixed[voice].append((t, d, m + semis, label))
            t += d
        if label:
            self.entries.append((bar * BPB + beat, label, voice))

    def rest_bars(self, voice, b0, b1, beats=None):
        for bar in range(b0, b1):
            for bt in (range(BPB) if beats is None else beats):
                self.rest[voice].add(bar * BPB + bt)

    def fixed_cover(self, v):
        cov = [None] * self.N
        for s, d, m, lab in self.fixed[v]:
            b = int(math.floor(s)); e = int(math.ceil(s + d - 1e-9))
            for k in range(b, min(e, self.N)):
                if cov[k] is None or s <= k:
                    cov[k] = m
        return cov

    def section(self, bar, title, sub):
        self.sections.append((bar, title, sub))

# ---------------------------------------------------------------- free voice generation
ORDER = {'S': 3, 'A': 2, 'T': 1, 'B': 0}

def melodic_cost(d):
    d = abs(d)
    if d == 0: return 0.9
    if d <= 2: return 0.0
    if d <= 4: return 0.5
    if d == 5: return 1.0
    if d == 6: return 2.5
    if d == 7: return 1.3
    if d <= 9: return 2.4
    if d <= 11: return 4.0
    if d == 12: return 2.0
    return 7.0

def choose_note(v, b, c, now, prev, prev_self, prev_chord, rng, strong):
    lo, hi = RANGE[v]
    cands = [m for m in range(lo, hi + 1) if m % 12 in c['pcs']]
    best, bestc = None, 1e9
    pcs_present = [x % 12 for x in now.values()]
    for m in cands:
        cost = rng.random() * 0.5
        pc = m % 12
        # melodic
        if prev_self is not None:
            cost += melodic_cost(m - prev_self)
            # leading tone / seventh tendencies
            if prev_chord is not None:
                if prev_chord['major3'] and prev_self % 12 == prev_chord['third'] and (prev_chord['root'] - prev_self) % 12 != 0:
                    if (m - prev_self) == 1: cost -= 1.2
                    elif abs(m - prev_self) > 2: cost += 1.0
                if prev_chord['seventh'] is not None and prev_self % 12 == prev_chord['seventh']:
                    if (prev_self - m) in (1, 2): cost -= 1.0
                    elif m > prev_self: cost += 1.5
        else:
            cost += abs(m - CENTER[v]) / 6.0
        # range
        cost += abs(m - CENTER[v]) / 10.0
        if m < lo + 3 or m > hi - 3: cost += 2.0
        # bass: prefer the specified bass note
        if v == 'B':
            if pc == c['bass']: cost -= 0.8
            elif c['slash']: cost += 6.0
            elif pc == c['third']: cost += 1.2
            elif pc == c['fifth']: cost += 3.5
            else: cost += 3.0
        else:
            if c['seventh'] is not None and pc == c['seventh'] and pc in pcs_present: cost += 3.0
            if c['major3'] and pc == c['third'] and pc in pcs_present: cost += 3.5
            if pc not in pcs_present: cost -= 1.3
        # relations to other voices
        for o, om in now.items():
            if om is None: continue
            # crossing
            if (ORDER[o] > ORDER[v] and om <= m) or (ORDER[o] < ORDER[v] and om >= m):
                cost += 40.0
            if om == m: cost += 6.0
            diff = abs(om - m) % 12
            if diff in (1, 11): cost += 8.0 if strong else 3.0
            if diff in (2, 10) and strong and om % 12 not in c['pcs']: cost += 4.0   # 固定声部の非和声音に 2 度でぶつからない
            if diff == 0 and strong and om != m: cost += 1.0
            # spacing between adjacent upper voices
            if abs(ORDER[o] - ORDER[v]) == 1 and 'B' not in (o, v) and abs(om - m) > 12: cost += 2.5
            if abs(ORDER[o] - ORDER[v]) == 1 and 'B' in (o, v) and abs(om - m) > 19: cost += 2.0
            # parallels
            op = prev.get(o)
            if op is not None and prev_self is not None and op != om and prev_self != m:
                i1 = abs(prev_self - op) % 12; i2 = abs(m - om) % 12
                if i1 == i2 and i1 in (0, 7):
                    cost += 30.0
                # hidden 5/8 in outer voices by similar motion with a leap
                if i2 in (0, 7) and (m - prev_self) * (om - op) > 0 and abs(m - prev_self) > 2 and {o, v} == {'S', 'B'}:
                    cost += 4.0
        if cost < bestc:
            best, bestc = m, cost
    return best

def generate(piece, seed=7):
    rng = random.Random(seed)
    cov = {v: piece.fixed_cover(v) for v in VOICES}
    skel = {v: [None] * piece.N for v in VOICES}
    isfree = {v: [cov[v][b] is None and b not in piece.rest[v] for b in range(piece.N)] for v in VOICES}
    prev_note = {v: None for v in VOICES}
    prev_chord = None
    for b in range(piece.N):
        c = chord(piece.harm[b])
        strong = (b % BPB) in (0, 2)
        now = {}
        prev = {}
        for v in VOICES:
            if cov[v][b] is not None:
                now[v] = cov[v][b]
            prev[v] = prev_note[v]
        # bass first, then upward
        for v in sorted(VOICES, key=lambda x: ORDER[x]):
            if isfree[v][b]:
                m = choose_note(v, b, c, now, prev, prev_note[v] if b > 0 and (isfree[v][b-1] or cov[v][b-1] is not None) else None, prev_chord, rng, strong)
                skel[v][b] = m
                now[v] = m
        for v in VOICES:
            if now.get(v) is not None:
                prev_note[v] = now[v]
            elif b in piece.rest[v]:
                prev_note[v] = None
        prev_chord = c
    return skel, cov, isfree

def neighbor(m, c, up):
    sc = c['scale']
    x = m + (1 if up else -1)
    while x % 12 not in sc:
        x += 1 if up else -1
    return x

def realize(piece, v, skel, cov, isfree, rng):
    """skeleton (quarter per beat) -> events with passing/neighbour eighths, holds."""
    ev = []
    N = piece.N
    b = 0
    firsts = {}
    for s, d, m, lab in piece.fixed[v]:
        firsts.setdefault(int(math.floor(s)), m)
    while b < N:
        m = skel[v][b]
        if m is None:
            b += 1; continue
        bar = b // BPB
        c = chord(piece.harm[b])
        if bar in piece.hold:
            # whole-bar hold (coda): sustain until the end of the bar or until not free
            e = b
            while e < N and (e // BPB) == bar and isfree[v][e] and skel[v][e] == m: e += 1
            ev.append((b, e - b, m, None)); b = e; continue
        nxt = None
        if b + 1 < N:
            nxt = skel[v][b + 1] if skel[v][b + 1] is not None else firsts.get(b + 1)
        d = None if nxt is None else nxt - m
        r = rng.random()
        strong = (b % BPB) in (0, 2)
        if d is not None and abs(d) in (3, 4) and r < 0.72:
            step = 1 if d > 0 else -1
            cands = [m + step, m + 2 * step]
            ok = [x for x in cands if x % 12 in c['scale']]
            p = ok[0] if ok else m + 2 * step
            ev += [(b, .5, m, None), (b + .5, .5, p, None)]; b += 1
        elif d == 0 and b + 1 < N and skel[v][b + 1] == m and isfree[v][b + 1]:
            if r < 0.30:
                ev.append((b, 2, m, None)); b += 2
            elif r < 0.75:
                up = m < CENTER[v]
                ev += [(b, .5, m, None), (b + .5, .5, neighbor(m, c, up), None)]; b += 1
            else:
                ev.append((b, 1, m, None)); b += 1
        elif d is not None and 5 <= abs(d) <= 9 and r < 0.5:
            step = 1 if d > 0 else -1
            mids = [x for x in range(min(m, nxt) + 1, max(m, nxt)) if x % 12 in c['pcs']]
            if mids:
                p = mids[-1] if step > 0 else mids[0]
                ev += [(b, .5, m, None), (b + .5, .5, p, None)]
            else:
                ev.append((b, 1, m, None))
            b += 1
        elif d is not None and abs(d) in (1, 2) and not strong and r < 0.22:
            # LOVELESS 風: 隣接音を経由する装飾 (m, 反対側隣接, m) は長いので m + 上隣接
            ev += [(b, .5, m, None), (b + .5, .5, neighbor(m, c, d < 0), None)]; b += 1
        else:
            ev.append((b, 1, m, None)); b += 1
    return ev

# ---------------------------------------------------------------- checker
def check(piece, events):
    """報告: 強拍での不協和 (半音/全音/7 度) と 連続 5 度・8 度 (拍単位)."""
    N = piece.N
    sound = {v: [None] * (N * 2) for v in VOICES}  # half-beat resolution
    for v in VOICES:
        for s, d, m, lab in events[v]:
            i0 = int(round(s * 2)); i1 = int(round((s + d) * 2))
            for k in range(i0, min(i1, N * 2)):
                sound[v][k] = m
    diss = []; par = []
    fixedset = {v: set() for v in VOICES}
    for v in VOICES:
        for s, d, m, lab in piece.fixed[v]:
            for k in range(int(round(s * 2)), int(round((s + d) * 2))): fixedset[v].add(k)
    for k in range(0, N * 2, 2):  # on beats
        b = k // 2
        strong = (b % BPB) in (0, 2)
        ch = chord(piece.harm[b])
        vs = [v for v in VOICES if sound[v][k] is not None]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                a, c2 = sound[vs[i]][k], sound[vs[j]][k]
                iv = abs(a - c2) % 12
                nct = (a % 12 not in ch['pcs']) or (c2 % 12 not in ch['pcs'])
                if (strong and iv in (1, 2, 11, 10, 6) and nct) or iv in (1, 11):
                    ff = 'FF' if (k in fixedset[vs[i]] and k in fixedset[vs[j]]) else ''
                    diss.append((b // BPB + 1, b % BPB + 1, vs[i], name_of(a), vs[j], name_of(c2), piece.harm[b], ff))
                if k >= 2 and sound[vs[i]][k-2] is not None and sound[vs[j]][k-2] is not None:
                    a0, c0 = sound[vs[i]][k-2], sound[vs[j]][k-2]
                    if a0 != a and c0 != c2 and (a0 - c0) % 12 == (a - c2) % 12 and (a - c2) % 12 in (0, 7):
                        par.append((b // BPB + 1, b % BPB + 1, vs[i], vs[j], (a - c2) % 12))
    return diss, par

# ---------------------------------------------------------------- the piece
def build():
    P = Piece(130)
    build_fugue(P, 0)
    return P

def build_fugue(P, off=0, gaps=(0, 0)):
    """フーガ本体 (130 小節) を P の小節 off から書き込む。
    gaps=(g1, g2): 第 II 部 (44 小節目〜) の前に g1 小節、第 III 部 (85 小節目〜) の前に g2 小節の隙間を空ける。"""
    def f(bar):
        return bar + off + (gaps[0] if bar >= 44 else 0) + (gaps[1] if bar >= 85 else 0)
    _place, _set_harms, _rest, _section, _set_harm = P.place, P.set_harms, P.rest_bars, P.section, P.set_harm
    P.place = lambda v, bar, m, semis=0, label=None, beat=0: _place(v, f(bar), m, semis, label, beat)
    P.set_harms = lambda bar, specs: [_set_harm(f(bar + i), sp) for i, sp in enumerate(specs)]
    P.set_harm = lambda bar, spec: _set_harm(f(bar), spec)
    P.rest_bars = lambda v, b0, b1, beats=None: _rest(v, f(b0), f(b0) + (b1 - b0), beats)
    P.section = lambda bar, t, s: _section(f(bar), t, s)
    # ---------- Section I : Soggetto I (MOTHER)
    P.section(0, 'I. Soggetto I 〈MOTHER〉', '主題 I の提示 — 4 声フーガ (ニ短調)')
    P.set_harms(0, H_S1);  P.place('A', 0, S1, 0, 'S1')
    for v in 'STB': P.rest_bars(v, 0, 5)
    P.set_harms(5, [[c2 + '' for c2 in bar] for bar in transpose_h(H_S1, 7)]); P.place('S', 5, S1, 7, 'S1 (答唱)')
    for v in 'TB': P.rest_bars(v, 5, 10)
    P.set_harms(10, [['Am','Am','Dm','Dm'], ['Gm','Gm','A7','A7']])           # episode (2 bars)
    for v in 'TB': P.rest_bars(v, 10, 12)
    P.set_harms(12, H_S1); P.place('B', 12, S1, -12, 'S1')
    P.rest_bars('T', 12, 17)
    P.set_harms(17, transpose_h(H_S1, 7)); P.place('T', 17, S1, 7 - 12, 'S1 (答唱)')
    # episode 1 (22-25): descending fifths, lead in soprano (track 17 figure: scale up + step back)
    EP1 = ['Am','Dm','Gm','C','F','Bb','Em7b5','A7']
    P.set_harms(22, [[EP1[0],EP1[0],EP1[1],EP1[1]], [EP1[2],EP1[2],EP1[3],EP1[3]], [EP1[4],EP1[4],EP1[5],EP1[5]], [EP1[6],EP1[6],EP1[7],EP1[7]]])
    P.place('S', 22, seq_line(EP1, [(0,.5),(1,.5),(2,.5),('n+',.5)], n('E5'), 64, 81), 0, None)
    P.rest_bars('B', 22, 24)
    P.set_harms(26, H_S1); P.place('S', 26, S1, 12, 'S1')
    # episode 2 (31-34): to G minor
    EP2 = ['Dm','Gm','Cm','F7','Bb','Eb','Am7b5','D7']
    P.set_harms(31, [[EP2[0],EP2[0],EP2[1],EP2[1]], [EP2[2],EP2[2],EP2[3],EP2[3]], [EP2[4],EP2[4],EP2[5],EP2[5]], [EP2[6],EP2[6],EP2[7],EP2[7]]])
    P.place('A', 31, seq_line(EP2, [(1,.5),(0,.5),(2,.5),(1,.5)], n('A4'), 57, 74), 0, None)
    P.rest_bars('S', 31, 33)
    P.set_harms(35, transpose_h(H_S1, 5)); P.place('T', 35, S1, 5 - 12, 'S1 (下属調)')
    # episode 3 (40-43): back to D minor, half cadence
    EP3 = ['Gm','C7','F','Bb','Em7b5','A7','Dm','A']
    P.set_harms(40, [[EP3[0],EP3[0],EP3[1],EP3[1]], [EP3[2],EP3[2],EP3[3],EP3[3]], [EP3[4],EP3[4],EP3[5],EP3[5]], [EP3[6],EP3[6],EP3[7],EP3[7]]])
    P.place('B', 40, seq_line(EP3[:6], [(0,1),(2,.5),(1,.5)], n('G3'), 38, 57), 0, None)
    P.rest_bars('A', 40, 42)

    # ---------- Section II : Soggetto II (Track 18)
    P.section(44, 'II. Soggetto II 〈トラック18〉', '主題 II の提示 と 主題 I との二重結合')
    P.set_harms(44, H_S2); P.place('A', 44, S2, 0, 'S2')
    for v in 'ST': P.rest_bars(v, 44, 47)
    P.set_harms(47, transpose_h(H_S2, 7)); P.place('S', 47, S2, 7, 'S2 (答唱)')
    P.rest_bars('T', 47, 50)
    P.set_harms(50, H_S2); P.place('T', 50, S2, -12, 'S2')
    P.rest_bars('B', 50, 53)
    P.set_harms(53, transpose_h(H_S2, 7)); P.place('B', 53, S2, 7 - 24, 'S2 (答唱)')
    EP4 = ['Dm','Gm','C','F','Bb','Em7b5','A7','A7']
    P.set_harms(56, [[EP4[0],EP4[0],EP4[1],EP4[1]], [EP4[2],EP4[2],EP4[3],EP4[3]], [EP4[4],EP4[4],EP4[5],EP4[5]], [EP4[6],EP4[6],EP4[7],EP4[7]]])
    P.place('S', 56, seq_line(EP4[:6], [(1,.5),(1,.5),(1,.5),(2,.5)], n('F5'), 64, 81), 0, None)   # 反復音 (track18)
    P.place('T', 56, seq_line(EP4[:6], [(0,1),('n-',.5),(0,.5)], n('D4'), 50, 66), 0, None)
    # combination I : S1 bass + S2 soprano
    P.set_harms(60, H_S1); P.place('B', 60, S1, -12, 'S1'); P.place('S', 60, S2, 12, 'S2')
    EP5 = ['Dm','G','C','F','Bm7b5','E7','Am','E7']
    P.set_harms(65, [[EP5[0],EP5[0],EP5[1],EP5[1]], [EP5[2],EP5[2],EP5[3],EP5[3]], [EP5[4],EP5[4],EP5[5],EP5[5]], [EP5[6],EP5[6],EP5[7],EP5[7]]])
    P.place('A', 65, seq_line(EP5, [(0,.5),(1,.5),(2,.5),('n+',.5)], n('D4'), 57, 74), 0, None)
    P.rest_bars('S', 65, 67)
    # combination II (A minor, inverted): S1 soprano + S2 tenor
    P.set_harms(69, transpose_h(H_S1, 7)); P.place('S', 69, S1, 7, 'S1 (答唱)'); P.place('T', 69, S2, 7 - 12, 'S2 (答唱)')
    EP6 = ['Am','Dm','Gm','C','F','Bb','Em7b5','A7']
    P.set_harms(74, [[EP6[0],EP6[0],EP6[1],EP6[1]], [EP6[2],EP6[2],EP6[3],EP6[3]], [EP6[4],EP6[4],EP6[5],EP6[5]], [EP6[6],EP6[6],EP6[7],EP6[7]]])
    P.place('S', 74, seq_line(EP6, [(1,.5),('n+',.5),(1,.5),(0,.5)], n('E5'), 64, 81), 0, None)  # LOVELESS 隣接音型
    P.rest_bars('T', 74, 76)
    # combination III : S1 alto + S2 bass
    P.set_harms(78, H_S1); P.place('A', 78, S1, 0, 'S1'); P.place('B', 78, S2, -12, 'S2')
    P.set_harms(83, [['Gm','Gm','Em7b5','A7'], ['Dm','Dm','A','A']])

    # ---------- Section III : Soggetto III (B-A-D-A)
    P.section(85, 'III. Soggetto III 〈B-A-D-A〉', 'B♭-A-D-A の提示 と 三重結合 (Fuga a tre soggetti)')
    P.set_harms(85, H_S3); P.place('A', 85, S3, 0, 'S3 B-A-D-A')
    P.rest_bars('S', 85, 88)
    P.set_harms(88, transpose_h(H_S3, 7)); P.place('S', 88, S3, 7, 'S3 (答唱)')
    P.rest_bars('T', 88, 91)
    P.set_harms(91, H_S3); P.place('B', 91, S3, -24, 'S3 B-A-D-A')
    P.set_harms(94, transpose_h(H_S3, 7)); P.place('T', 94, S3, 7 - 12, 'S3 (答唱)')
    EP7 = ['Am','Dm','Gm','C','F','Bb','Em7b5','A7']
    P.set_harms(97, [[EP7[0],EP7[0],EP7[1],EP7[1]], [EP7[2],EP7[2],EP7[3],EP7[3]], [EP7[4],EP7[4],EP7[5],EP7[5]], [EP7[6],EP7[6],EP7[7],EP7[7]]])
    P.place('S', 97, seq_line(EP7, [('n+',.5),(1,.5),(0,1)], n('C5'), 64, 81), 0, None)     # ため息音型 (track 8)
    P.rest_bars('B', 97, 99)
    # triple I (D minor): S1 bass, S2 soprano, S3 alto (+2 bars)
    P.set_harms(101, H_TRIPLE); P.place('B', 101, S1, -12, 'S1'); P.place('S', 101, S2, 12, 'S2'); P.place('A', 103, S3, 0, 'S3 B-A-D-A')
    EP8 = ['Dm','G','C','F','Bm7b5','E7','Am','E7']
    P.set_harms(107, [[EP8[0],EP8[0],EP8[1],EP8[1]], [EP8[2],EP8[2],EP8[3],EP8[3]], [EP8[4],EP8[4],EP8[5],EP8[5]], [EP8[6],EP8[6],EP8[7],EP8[7]]])
    P.place('T', 107, seq_line(EP8, [(0,.5),(1,.5),(2,.5),('n+',.5)], n('D4'), 50, 66), 0, None)
    P.rest_bars('S', 107, 109)
    # triple II (A minor): S1 tenor, S2 soprano, S3 alto
    P.set_harms(111, transpose_h(H_TRIPLE, 7)); P.place('T', 111, S1, 7 - 12, 'S1 (答唱)'); P.place('S', 111, S2, 7 + 12, 'S2 (答唱)'); P.place('A', 113, S3, 7, 'S3 (答唱)')
    EP9 = ['Am','Dm','Gm','C','F','Bb','Em7b5','A7']
    P.set_harms(117, [[EP9[0],EP9[0],EP9[1],EP9[1]], [EP9[2],EP9[2],EP9[3],EP9[3]], [EP9[4],EP9[4],EP9[5],EP9[5]], [EP9[6],EP9[6],EP9[7],EP9[7]]])
    P.place('S', 117, seq_line(EP9, [(1,.5),('n+',.5),(1,.5),(0,.5)], n('E5'), 64, 81), 0, None)
    P.place('B', 117, seq_line(EP9, [(0,1),(0,.5),(0,.5)], n('A2'), 38, 57), 0, None)
    # triple III (D minor, final): S1 soprano, S2 alto, S3 tenor
    P.section(121, 'III. Fuga a tre soggetti — 終結', '三主題の最終結合 と コーダ (ピカルディ終止)')
    P.set_harms(121, H_TRIPLE); P.place('S', 121, S1, 12, 'S1'); P.place('A', 121, S2, 0, 'S2'); P.place('T', 123, S3, -12, 'S3 B-A-D-A')
    # bar 126: general pause (バッハの自筆譜が途切れる場所へのオマージュ) then coda
    P.set_harms(126, [['Dm','Dm','Dm','Dm'], ['Gm/D','Gm/D','Bb/D','Bb/D'], ['A7/D','A7/D','A7','A7'], ['D','D','D','D']])
    for v in VOICES: P.rest_bars(v, 126, 127, beats=[0, 1])
    P.hold.update({f(127), f(128), f(129)})
    P.set_harm(129, 'D')
    P.place, P.set_harms, P.rest_bars, P.section, P.set_harm = _place, _set_harms, _rest, _section, _set_harm
    return P

def transpose_h(H, semis):
    out = []
    for bar in H:
        row = []
        for cs in bar:
            bass = None
            core = cs
            if '/' in cs: core, bass = cs.split('/')
            i = 2 if len(core) > 1 and core[1] in '#b' else 1
            root = (PC[core[:i]] + semis) % 12
            q = core[i:]
            s = NAMES[root] + q
            if bass: s += '/' + NAMES[(PC[bass] + semis) % 12]
            row.append(s)
        out.append(row)
    return out

def main(out='score.json', seed=7, bpm=96, builder=None, meta=None, extras=None, transpose_semis=0, post=None):
    P = builder() if builder else build()
    rng = random.Random(seed)
    skel, cov, isfree = generate(P, seed)
    events = {}
    for v in VOICES:
        ev = realize(P, v, skel, cov, isfree, rng)
        ev += [(s, d, m, lab) for s, d, m, lab in P.fixed[v]]
        ev.sort()
        events[v] = ev
    if post: post(P, events, extras)          # 生成後の全声部を見て追加 (管弦楽の重ねなど)
    diss, par = check(P, events)
    print('bars', P.nbars, 'beats', P.N)
    print('strong-beat dissonances:', len(diss))
    for d in diss[:60]: print('  ', d)
    print('parallels:', len(par))
    for p in par[:40]: print('  ', p)
    spb = 60.0 / bpm
    # テンポ・マップ: 小節ごとの bpm から各拍の開始時刻を求める
    beat_t = [0.0]
    for bar in range(P.nbars):
        sb = 60.0 / P.tempo.get(bar, bpm)
        for k in range(BPB): beat_t.append(beat_t[-1] + sb)
    def time_of(beat):
        i = int(math.floor(beat)); i = max(0, min(i, len(beat_t) - 2))
        return beat_t[i] + (beat - i) * (beat_t[i + 1] - beat_t[i])
    bar_times = [beat_t[b * BPB] for b in range(P.nbars + 1)]
    notes = []
    for v in VOICES:
        for s, d, m, lab in events[v]:
            t0 = time_of(s)
            notes.append({'v': v, 't': round(t0, 4), 'd': round(time_of(s + d) - t0, 4), 'm': m, 'label': lab, 'beat': s,
                          'dyn': P.dyn_at(s), 'det': P.det.get(int(s // BPB), 1.0), 'role': P.role.get(int(s // BPB), '')})
    if transpose_semis:
        for nt in notes: nt['m'] += transpose_semis
        for e in (extras or []): e['m'] += transpose_semis
        P.harm = [row[0] for row in transpose_h([[h] for h in P.harm], transpose_semis)]
    data = {'bpm': bpm, 'beats_per_bar': BPB, 'nbars': P.nbars, 'duration': bar_times[-1], 'bar_times': [round(x, 4) for x in bar_times],
            'notes': notes,
            'entries': [{'t': time_of(b), 'label': lab, 'v': v, 'bar': b // BPB + 1} for b, lab, v in P.entries],
            'sections': [{'t': bar_times[bar], 'bar': bar + 1, 'title': t, 'sub': s} for bar, t, s in sorted(P.sections)],
            'harm': P.harm, 'meta': meta or {},
            'extras': [dict(e, t=round(time_of(e['beat']), 4), d=round(time_of(e['beat'] + e['dbeats']) - time_of(e['beat']), 4)) for e in (extras or [])]}
    json.dump(data, open(out, 'w'), ensure_ascii=False, indent=0)
    print('wrote', out, len(notes), 'notes')

if __name__ == '__main__':
    main(*(sys.argv[1:2] or ['score.json']))
