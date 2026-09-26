"""
Requiem BADA — Tablet Sessions XXX · Kimigayo patetico (君が代を変ロ短調で — 悲愴を帯びた哀しみ)
  XXIX (ハ短調の君が代) を、2026-09-23 / 09-24 の録音 (7 本 + 11:21 のシンセの実音) で、変ロ短調 (B♭ minor) に作り換えた。
  哀しみの和声: i・iv・♭VI・V7・ナポリの ♭II (B♭m・E♭m・G♭・F7・C♭) — 句の終わりで iv や ♭VI へ沈み、嘆きのバス (半音で下がる) が支える。
  斉唱のユニゾン (童謡のように聞こえる部分) は省き、旋律はフーガの主題と、哀しみの和声の上の全旋律だけで歌う。
  奇麗な実音: 9/23 08:06 と 9/24 11:18 (どちらも元から変ロ短調、移調なし) の抜粋と、録音から切り出したピアノの 1 音。
  ペダルで響かせる: 高音 (S の 1 オクターヴ上) と低音 (B の 1 オクターヴ下) を 11:21 のシンセの実音が長く (2 倍以上) 重ね、
  音が次の音へ溶け込んで反響する。ピアノの減衰も長く (piano_decay 2.8)。
  使い方: python compose_tablet30.py <bank17.json> [score_tablet30.json]
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
BPM = 50; BAR_S = 240.0 / BPM
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
SYN = 'VOXSY'; SEMIS = -4                                   # 変ロ短調 (ニ短調の枠から −4)
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}
octs, TOP = T7.octs, T7.TOP
FLAT = ['Dm', 'Gm', 'Bb', 'A7', 'Eb', 'F', 'Dm/F', 'Gm/Bb', 'A']   # 哀しみ (枠 → −4): B♭m, E♭m, G♭, F7, C♭ (ナポリ), A♭, B♭m/D♭, E♭m/G♭, F
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
                if cs == 'Gm': s += 0.35                                          # iv へ沈む
                if cs == 'Bb': s += 0.6                                            # ♭VI
                if cs == 'Dm' and h == 0: s += 0.45
                if cs == 'Eb': s += 0.2                                            # ナポリ
                if cs == 'A7': s += 0.3 if h == 1 else -0.9                        # 属七は小節の後半だけ (→ 次の i)
                if cs in ('F', 'A'): s -= 0.4
                if cs == 'Dm/F': s += 0.3
                if cs == 'Dm' and (bar - b0) % 4 == 0 and h == 0: s += 0.5
                return s
            cs = max([c_ for c_ in FLAT if h == 1 or c_ not in ('A7', 'A')], key=score) if notes else (['Gm', 'Bb', 'Eb', 'A7'][(bar - b0) % 4] if h == 1 else ['Dm', 'Gm', 'Bb', 'Dm/F'][(bar - b0) % 4])
            held = [m for w, m in notes if w >= 2 and m % 12 == 2]                       # 句の終わりに伸ばす主音: 後半を iv か ♭VI で哀しく
            if h == 1 and held and len(notes) == len(held): cs = 'Gm' if (bar - b0) % 2 else 'Bb'
            for q in range(2): P.harm[a + q] = cs

def post(P, events, extras):
    for b0, b1, rid, kinds in T2.MANTRA:
        for bar in range(b0, b1):
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, 0.11 if k == 0 else 0.06, None, rid=rid)
    for b0, b1, gain in PAD:                                                 # シンセの実音が和音を支える (低く)
        for bar in range(b0, b1):
            ch = chord(P.harm[bar * BPB]); root = ch['root']
            for j, m in enumerate((38 + (root - 2) % 12, 45 + (root - 2) % 12, 50 + (root - 2) % 12 + (ch['third'] - root) % 12)):
                add('SP', bar * BPB + 0.02 * j, BPB + 1.5, m, gain * (1.0 if j else 1.2), None, rid=SYN, pan=(-0.2, 0.2, 0.0)[j])
    for b0, b1, gain in COLD:                                                # ペダルの反響: S の 1 オクターヴ上と B の 1 オクターヴ下をシンセが長く重ねる
        for v, sh, g, mul in (('S', 12, gain, 2.2), ('B', -12, gain * 1.2, 2.6)):
            for s_, d, m, lab in events[v]:
                if b0 * BPB <= s_ < b1 * BPB and m is not None:
                    add('SP', s_, d * mul, m + sh, g, None, rid=SYN, pan=0.3 if v == 'S' else -0.3)

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
    end_b1 = REC[B1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(B1, []).append((end_b1, REC[B1]['dur']))
    total = 6 + 8 + 10 + 6 + 12 + 5 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    P.section(b, 'Introitus — 9/23 %s の実音 (変ロ短調)' % hm(B1), '元から変ロ短調の録音をそのまま — 低いシンセの実音が和音を支え、♩=50 の鼓動が始まる')
    b += requiem(P, b, B1, 6, pad=0.13)
    # ---------------- Lamento — 嘆きのバスの上に、君が代の 2〜5 句をアルトで
    f = b; E = []
    P.section(b, 'Lamento — 嘆きのバスの上の君が代 (変ロ短調)', '「千代に八千代に」から「苔のむすまで」をアルトが歌い、バスは半音で下がる嘆きの音型 (B♭ A A♭ G G♭ F) — 高音と低音をシンセが長く反響させる')
    t = 0
    for i_, ph in enumerate(KIMI[1:5]):
        entry(P, f + t, 'A', ph, 0, ['千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    LAM = mat(('D3', 2), ('C#3', 2), ('C3', 2), ('B2', 2), ('Bb2', 2), ('A2', 2))
    for k in range(0, t, 3): P.place('B', f + k, LAM, 0, '嘆きのバス' if k == 0 else None)
    P.set_harms(f, [['Dm', 'Dm', 'A/C#', 'A/C#'], ['F/C', 'F/C', 'G/B', 'G/B'], ['Gm/Bb', 'Gm/Bb', 'A7', 'A7']] * 3)
    P.rest_bars('S', f, f + 2)
    P.hold.update({f + 6, f + 7})
    for k in range(8): P.dyn[f + k] = 1.1
    COLD.append((f, f + 8, 0.07))
    T2.MANTRA.append((f, f + 8, B1, ('PK',))); CT.LAYOUT.append((f, f + 8, SEMIS, VOICE_SRC, {})); b = f + 8
    # ---------------- Fuga
    f = b; E = []
    P.section(b, 'Fuga — 「君が代は」の主題 (変ロ短調)', '第 1 句 (→ B♭ B♭ A♭ B♭ C E♭ C B♭) を主題に、A → S → T → B の提示 → ストレッタ — 哀しみの和声 (iv・♭VI・ナポリ)')
    for k, v in enumerate('ASTB'): entry(P, f + 2 * k, v, SUBJ, 0, '主題 (君が代)', E, synth=0)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', SUBJ, 0, '主題 (君が代) ストレッタ', E, beat=2, synth=0); entry(P, f + 8, 'T', SUBJ, 0, None, E, beat=1, synth=0)
    harm_flat(P, f, f + 10, E)
    for k in range(10): P.dyn[f + k] = 1.25
    COLD.append((f, f + 10, 0.06))
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, SEMIS, VOICE_SRC, {})); b = f + 10
    # ---------------- Interludium — 11:18
    P.section(b, 'Interludium — 9/24 %s の実音 (変ロ短調)' % hm(B2), '元から変ロ短調の 11:18 をそのまま — 低いシンセの実音と鼓動')
    b += requiem(P, b, B2, 6, pad=0.13)
    # ---------------- Kimigayo — 全旋律、哀しみの和声
    f = b; E = []
    P.section(b, 'Kimigayo — 哀しみの全旋律 (変ロ短調)', '全旋律をソプラノに、句の終わりは iv・♭VI へ沈み、ナポリの C♭ が「巌となりて」に影を落とす — 高音と低音がシンセで反響し、最後は全声部がユニゾンの B♭ に')
    t = 0
    for i_, ph in enumerate(KIMI[:5]):
        entry(P, f + t, 'S', ph, 0, ['君が代は', '千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in 'AT': P.rest_bars(v, f + t, f + 12)
    P.rest_bars('S', f + t + 1, f + 12); P.rest_bars('B', f + t + 1, f + 12)
    harm_flat(P, f, f + 12, E)
    for q in range(BPB): P.harm[f * BPB + q] = 'Dm'; P.harm[(f + t) * BPB + q] = 'Dm'
    for q in range(2): P.harm[(f + 6) * BPB + q] = 'Eb'                                # 巌となりて: ナポリ
    P.hold.update({f + 10, f + 11})
    for k in range(12): P.dyn[f + k] = 1.3
    PAD.append((f, f + t + 1, 0.11)); COLD.append((f, f + 12, 0.075))
    T2.MANTRA.append((f, f + 12, B1, ('PK',))); CT.LAYOUT.append((f, f + 12, SEMIS, VOICE_SRC, {})); b = f + 12
    # ---------------- Coda
    P.section(b, 'Coda — 9/23 %s の本当の終わり' % hm(B1), '08:06 の最後 → ユニゾンの B♭ とシンセの反響が、鼓動とともに消える')
    b += requiem(P, b, B1, 5, t0=end_b1, fin=1.0, fout=2.5, gmul=0.65, pad=0.0)
    P.set_harms(b, [['Dm']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    for k, m in enumerate((38, 50, 62, 74)): add('SP', b * BPB + 0.3 * k, 7.0, m, 0.14, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15)[k])
    T2.MANTRA.append((b, b + 2, B1, ('PK',))); CT.LAYOUT.append((b, b + 2, SEMIS, VOICE_SRC, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER + [SYN], 'piano_decay': 2.8, 'src_name': {SYN: '11:21 のシンセ (実音)'},
    'title': 'Requiem BADA — Tablet Sessions XXX · Kimigayo patetico',
    'subtitle': '君が代を変ロ短調で、悲愴を帯びた哀しみに — 9/23・9/24 の奇麗な実音、高音と低音をシンセがペダルのように反響 (♩=50)',
    'legend': ['TB', 'SP', 'PK'], 'vname': {'SP': '11:21 のシンセ (反響)', 'PK': '鼓動'},
    'footer': ['Introitus 08:06 → Lamento (嘆きのバス + 君が代) → Fuga (「君が代は」) → Interludium 11:18 → Kimigayo (哀しみの全旋律) → Coda 08:06 の終わり → ユニゾンの B♭',
               '旋律: 君が代 (林廣守)。和声: B♭m・E♭m・G♭・F7・C♭ (i・iv・♭VI・V7・ナポリ)。音は 9/23・9/24 の録音のピアノとシンセの実音 (移調なし)。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet30.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    d['harm'] = [h.replace('F#', 'Gb').replace('G#', 'Ab') if h[:2] in ('F#', 'G#') else h for h in d['harm']]   # 表示: G♭・A♭
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
    print('harm:', ' '.join(d['harm'][k] for k in range(0, len(d['harm']), 4)))
