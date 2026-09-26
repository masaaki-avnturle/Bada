#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXIX · Kimigayo (君が代 — アステールプラザの国歌斉唱)
  2026-09-25 の 3 本の録音をミックスし、日本国歌「君が代」(林廣守の旋律、公有) を B♭ 版 (主音 C) の高さで、
  ハ短調 (C minor) の上に置く。和声は C minor に E♭・G♭・B♭ の長三和音 (i – ♭III – ♭V – ♭VII):
  旋律の D・F・G が E♭・G♭ と擦れ、荘厳で洗脳的な響きになる。
  情景: 小学校 6 年生の剣道試合、アステールプラザの国歌斉唱。外気が冷たい (高いシンセの実音 E♭6・G♭5・B♭5 が
  細く持続する)、子孫とご先祖様への尊敬の眼差し (ゆっくり ♩=48、鼓動、最後は全声部がユニゾンの C に集まる — 国歌の終わりと同じ)。
  作りは (ニ短調の枠で書いて −2 半音):
    Introitus — 13:04 の実音を C minor に移調 (pshift) → 冷たい外気のシンセ
    Kimigayo I (斉唱) — 第 1 句を 4 声のユニゾン (オクターヴ) で、続きはテノールの定旋律 (cantus firmus) の上に自由声部
    Fuga — 第 1 句 (D D C D E G E D) を主題にしたフーガ: 提示 → ストレッタ (拍をずらして)
    Interludium — 12:46 のシンセの部分の実音 (C minor に)
    Kimigayo II (荘厳) — 全旋律をソプラノに、保続低音と鼓動、シンセの和音 (E♭・G♭・B♭)、最後はユニゾン
    Coda — 13:04 の本当の終わり (C minor に) → ユニゾンの C とシンセの冷たい音が消える
  使い方: python compose_tablet29.py <bank26.json> [score_tablet29.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 48; BAR_S = 240.0 / BPM
R1, R2, R3 = '20260925_124643', '20260925_125053', '20260925_130431'
KEYS = {R1: 3, R2: -3, R3: 1}
T7.KEYS.update(KEYS); T7.MARK.update({R3: '①', R1: '②', R2: '③'})
ORDER = [R3, R1, R2]
SYN = 'VOXSY'; SEMIS = -2                                   # ハ短調 (ニ短調の枠から −2)
VOICE_SRC = {'S': R3, 'A': R1, 'T': R2, 'B': R3}
octs, TOP = T7.octs, T7.TOP
FLAT = ['Dm', 'F', 'Ab', 'C', 'Gm', 'Bb', 'Dm/F']           # ニ短調の枠: → Cm, E♭, G♭, B♭, Fm, A♭, Cm/E♭
# 君が代 (林廣守) — ニ短調の枠 (主音 D、→ −2 で C): 一音一拍、句の終わりを伸ばす
KIMI = [mat(('D4',1),('D4',1),('C4',1),('D4',1),('E4',1),('G4',1),('E4',1),('D4',1)),          # 君が代は
        mat(('E4',1),('G4',1),('A4',1),('G4',1),('E4',1),('G4',1),('A4',2)),                    # 千代に八千代に
        mat(('A4',1),('G4',1),('A4',1),('G4',1),('E4',1),('D4',3)),                             # さざれ石の
        mat(('C4',1),('D4',1),('E4',1),('G4',1),('E4',1),('D4',3)),                             # 巌となりて
        mat(('E4',1),('G4',1),('A4',1),('G4',1),('E4',1),('D4',3)),                             # 苔のむすまで
        mat(('D4',4))]                                                                         # (ユニゾン)
KIMI_ALL = [x for ph in KIMI for x in ph]                     # 44 拍 = 11 小節
SUBJ = KIMI[0]
PAD, COLD = [], []

def harm_flat(P, b0, b1, entries, cold=0.35):
    """半小節ごとに、鳴っている主題・定旋律の音をいちばん多く含む和音を FLAT から選ぶ。主題が鳴っていないところは A♭ (→G♭) を好む"""
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    if m is not None:
                        ov = min(a + 2, t + d) - max(a, t)
                        if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            def score(cs):
                c = chord(cs); s = sum(w * (1 if m % 12 in c['pcs'] else -0.9) for w, m in notes)
                if cs == 'Ab': s += cold * (3.5 if notes else 3)
                if cs == 'F': s += 0.6
                if cs == 'Bb': s -= 0.2
                if cs == 'C': s -= 0.5
                if cs == 'Dm' and (bar - b0) % 4 == 0 and h == 0: s += 0.4
                return s
            cs = max(FLAT, key=score) if notes else ('Ab' if (bar - b0) % 4 in (1, 2) else ('Dm' if (bar - b0) % 4 == 0 else 'C'))
            held = [m for w, m in notes if w >= 2 and m % 12 == 2]                       # 句の終わりに伸ばす D (→C) の後半: G♭ で擦らせる
            if h == 1 and held and len(notes) == len(held): cs = 'Ab'
            for q in range(2): P.harm[a + q] = cs

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=rid)
    for b0, b1, gain in PAD:                                                 # シンセの実音が和音 (E♭・G♭・B♭) を支える
        for bar in range(b0, b1):
            ch = chord(P.harm[bar * BPB]); root = ch['root']
            for j, m in enumerate((38 + (root - 2) % 12, 45 + (root - 2) % 12, 50 + (root - 2) % 12 + (ch['third'] - root) % 12)):
                add('SP', bar * BPB + 0.02 * j, BPB + 0.5, m, gain * (1.0 if j else 1.2), None, rid=SYN, pan=(-0.2, 0.2, 0.0)[j])
    for b0, b1, gain in COLD:                                                # 冷たい外気: 高い E♭6・G♭5・B♭5 (枠では F6・A♭5・C6) が細く持続
        seq = [(89, 6), (80, 5), (84, 7), (80, 4), (89, 5), (84, 6)]; t = b0 * BPB; k = 0
        while t < b1 * BPB:
            m, d = seq[k % len(seq)]; d = min(d, b1 * BPB - t)
            if d <= 0.5: break
            add('SP', t, d, m, gain, None, rid=SYN, pan=0.35 if k % 2 else -0.35); t += max(1.0, d - 0.5); k += 1

def requiem(P, b, rid, bars, t0=None, fin=1.5, fout=3.0, gmul=0.6, pad=0.16, cold=0.0):
    T5.passage(P, rid, b, bars, SEMIS, bars, fin=fin, fout=fout, t0=t0, bpm=BPM, gmul=gmul, pshift=SEMIS - KEYS[rid])
    for v in VOICES: P.rest_bars(v, b, b + bars)
    for k in range(bars): P.dyn[b + k] = 0.5
    if pad: PAD.append((b, b + bars, pad))
    if cold: COLD.append((b, b + bars, cold))
    T2.MANTRA.append((b, b + bars, rid, ('PK',))); CT.LAYOUT.append((b, b + bars, SEMIS, {v: rid for v in VOICES}, {}))
    return bars

def fit(v, mat_, tr):
    if v == 'B' and min(m for _, m in mat_ if m is not None) + tr < 36: tr += 12
    if max(m for _, m in mat_ if m is not None) + tr > TOP[v]: tr -= 12
    return tr

def entry(P, bar, v, mat_, tr0, label, entries, beat=0, synth=0.11):
    tr = fit(v, mat_, octs[v] + tr0)
    P.place(v, bar, mat_, tr, label, beat=beat); entries.append((bar * BPB + beat, [(d, None if m is None else m + tr) for d, m in mat_]))
    if synth:
        t = bar * BPB + beat
        for d, m in mat_:
            if m is not None: add('SP', t, d * 0.95, m + tr + (12 if v in 'TB' else 0), synth, None, rid=SYN, pan=0.15 if v in 'SA' else -0.15)
            t += d

def build():
    end3 = REC[R3]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(R3, []).append((end3, REC[R3]['dur']))
    total = 6 + 12 + 10 + 6 + 12 + 5 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    P.section(b, 'Introitus — %s の実音 (ハ短調に)' % hm(R3), 'アステールプラザ、外気が冷たい — 13:04 の録音を C minor へ。高い E♭・G♭・B♭ のシンセの実音が細く持続し、♩=48 の鼓動が始まる')
    b += requiem(P, b, R3, 6, cold=0.07)
    # ---------------- Kimigayo I — 斉唱 (ユニゾン) → テノールの定旋律
    f = b; E = []
    P.section(b, 'Kimigayo I — 斉唱 (ハ短調, E♭・G♭・B♭)', '「君が代は」を 4 声がオクターヴのユニゾンで — 続きはテノールの定旋律の上に自由声部。和声は Cm・E♭・G♭・B♭、旋律の D・F・G が E♭・G♭ と擦れる')
    for v in VOICES: entry(P, f, v, KIMI[0], 0, '君が代は (斉唱)' if v == 'S' else None, E, synth=0.09 if v == 'S' else 0)
    t = 2
    for i, ph in enumerate(KIMI[1:5]):
        entry(P, f + t, 'T', ph, 0, ['千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i], E, synth=0.1); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    entry(P, f + t, 'B', KIMI[5], 0, None, E, synth=0); entry(P, f + t, 'T', KIMI[5], 0, None, E, synth=0)
    for v in 'SA': P.rest_bars(v, f + t, f + 12)
    harm_flat(P, f, f + 12, E)
    for q in range(BPB): P.harm[f * BPB + q] = 'Dm'
    P.hold.update({f + 10, f + 11})
    for k in range(12): P.dyn[f + k] = 1.15
    PAD.append((f + 2, f + 12, 0.12)); COLD.append((f, f + 12, 0.045))
    T2.MANTRA.append((f, f + 12, R3, ('PK',))); CT.LAYOUT.append((f, f + 12, SEMIS, VOICE_SRC, {})); b = f + 12
    # ---------------- Fuga — 第 1 句の主題
    f = b; E = []
    P.section(b, 'Fuga — 「君が代は」の主題 (ハ短調)', '第 1 句 D D C D E G E D (→ C C B♭ C D F D C) を主題に、A → S → T → B の提示 → 拍をずらしたストレッタ — 和声は E♭・G♭・B♭')
    for k, v in enumerate('ASTB'): entry(P, f + 2 * k, v, SUBJ, 0, '主題 (君が代)', E, synth=0.1 if v in 'SA' else 0.08)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', SUBJ, 0, '主題 (君が代) ストレッタ', E, beat=2, synth=0.1); entry(P, f + 8, 'T', SUBJ, 0, None, E, beat=1, synth=0)
    harm_flat(P, f, f + 10, E, cold=0.5)
    for k in range(10): P.dyn[f + k] = 1.25
    T2.MANTRA.append((f, f + 10, R1, ('PK',))); CT.LAYOUT.append((f, f + 10, SEMIS, VOICE_SRC, {})); b = f + 10
    # ---------------- Interludium — 12:46 のシンセの部分
    P.section(b, 'Interludium — %s のシンセの実音 (ハ短調に)' % hm(R1), '12:46 の途中、シンセサイザーが鳴っている実音を C minor へ — 冷たい外気のシンセと鼓動')
    b += requiem(P, b, R1, 6, t0=84.0, cold=0.06)
    # ---------------- Kimigayo II — 荘厳 (全旋律をソプラノに)
    f = b; E = []
    P.section(b, 'Kimigayo II — 荘厳 (ハ短調, E♭・G♭・B♭)', '全旋律をソプラノに、保続低音の C (拍ごとに打ち直す) と鼓動、シンセの和音 E♭・G♭・B♭ — 子孫とご先祖様への眼差し。最後は全声部がユニゾンの C に集まる')
    t = 0
    for i, ph in enumerate(KIMI[:5]):
        entry(P, f + t, 'S', ph, 0, ['君が代は', '千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i], E, synth=0.12); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0.1 if v == 'S' else 0)
    for k in range(t): P.place('B', f + k, T11.PED, 0, '保続低音 C' if k == 0 else None)
    for v in 'AT': P.rest_bars(v, f + t, f + 12)
    P.rest_bars('S', f + t + 1, f + 12); P.rest_bars('B', f + t + 1, f + 12)
    harm_flat(P, f, f + 12, E)
    for q in range(BPB): P.harm[f * BPB + q] = 'Dm'; P.harm[(f + t) * BPB + q] = 'Dm'
    P.hold.update({f + 10, f + 11})
    for k in range(12): P.dyn[f + k] = 1.3
    PAD.append((f, f + t + 1, 0.15)); COLD.append((f, f + 12, 0.05))
    T2.MANTRA.append((f, f + 12, R2, ('PK',))); CT.LAYOUT.append((f, f + 12, SEMIS, VOICE_SRC, {})); b = f + 12
    # ---------------- Coda — 13:04 の本当の終わり → ユニゾンの C
    P.section(b, 'Coda — %s の本当の終わり (ハ短調に)' % hm(R3), '13:04 の最後 → ユニゾンの C とシンセの冷たい音が、鼓動とともに消える')
    b += requiem(P, b, R3, 5, t0=end3, fin=1.0, fout=2.5, gmul=0.65, pad=0.0, cold=0.05)
    P.set_harms(b, [['Dm']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    for k, m in enumerate((38, 50, 62, 74)): add('SP', b * BPB + 0.3 * k, 7.0, m, 0.14, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15)[k])
    T2.MANTRA.append((b, b + 2, R3, ('PK',))); CT.LAYOUT.append((b, b + 2, SEMIS, VOICE_SRC, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER + [SYN], 'piano_decay': 1.5, 'src_name': {SYN: '12:46 のシンセ (実音)'},
    'title': 'Requiem BADA — Tablet Sessions XXIX · Kimigayo',
    'subtitle': '君が代をハ短調 (E♭・G♭・B♭) で — アステールプラザの国歌斉唱、冷たい外気、ご先祖様と子孫への眼差し (9/25 の実音, ♩=48)',
    'legend': ['TB', 'SP', 'PK'], 'vname': {'SP': '12:46 のシンセ (実音)', 'PK': '鼓動'},
    'footer': ['Introitus 13:04 → Kimigayo I (斉唱 → テノールの定旋律) → Fuga (「君が代は」の主題) → Interludium 12:46 (シンセ) → Kimigayo II (荘厳、保続低音) → Coda 13:04 の終わり → ユニゾンの C',
               '旋律: 君が代 (林廣守)。和声: Cm・E♭・G♭・B♭ (i・♭III・♭V・♭VII)。音は 9/25 の録音から切り出したピアノとシンセの実音、抜粋は C minor に移調。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet29.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    d['harm'] = [h.replace('F#', 'Gb').replace('G#', 'Ab') if h[:2] in ('F#', 'G#') else h for h in d['harm']]   # 表示: G♭・A♭
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
    print('harm:', ' '.join(d['harm'][k] for k in range(0, len(d['harm']), 4)))
