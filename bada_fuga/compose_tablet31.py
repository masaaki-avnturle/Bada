"""
Requiem BADA — Tablet Sessions XXXI · Kimigayo — Requiem di guerra (戦争の悲哀のレクイエムとフーガ + 君が代)
  XXX (変ロ短調の君が代、9/23・9/24 の実音、ペダルの反響) に、戦争の悲哀を表すレクイエムとフーガを合わせた。
    - 弔鐘: 低い B♭ (ピアノの実音) が小節ごとに鳴り、長く減衰する
    - 葬送の太鼓: 鼓動を葬送行進の型 (強・中・付点の弱) に
    - Dies irae: グレゴリオ聖歌「怒りの日」の冒頭 (公有) を、バスが 2 倍の長さで唱え、その上で「君が代は」の主題がフーガになる (二重フーガ)
    - 黙祷: すべてが止まり、弔鐘とシンセの反響だけが残る 2 小節
    - バッハ風フーガ: 「君が代は」を主題に、提示 → エピソード → 下属調 → ストレッタ → 打ち直す保続低音 (compose_tablet11.bach_fugue)
    - Kimigayo: 哀しみの和声の全旋律 (XXX) に弔鐘、最後は全声部がユニゾンの B♭ → Libera me (08:06 の本当の終わり)
  使い方: python compose_tablet31.py <bank17.json> [score_tablet31.json]
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
T11.hm = lambda r: '君が代' if r == 'KIMI' else T3.hm(r)
T5.hm = T11.hm

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
PAD, COLD, BELL, DRUM = [], [], [], []
DIES = mat(('F4', 2), ('E4', 2), ('F4', 2), ('D4', 2), ('E4', 2), ('C4', 2), ('D4', 2), ('D4', 2))      # 怒りの日 (2 倍の長さ)

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
    for b0, b1, rid, kinds in T2.MANTRA:                                     # 葬送の太鼓: 強・中・付点の弱
        for bar in range(b0, b1):
            if any(a <= bar < z for a, z in DRUM): continue
            for k, g in ((0, 0.13), (2, 0.08), (3.5, 0.05)): add('PK', bar * BPB + k, 0.5, 26, g, None, rid=rid)
    for b0, b1, gain, rid in BELL:                                            # 弔鐘: 低い B♭ (枠では D2) が小節ごとに
        for bar in range(b0, b1):
            add('PF', bar * BPB, 3.8, 38, gain, None, rid=rid, rel=3.5); add('PF', bar * BPB + 0.01, 3.0, 50, gain * 0.45, None, rid=rid, rel=3.0)
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
    T5.SUBJ['KIMI'] = (SUBJ, CT.harmonize(SUBJ))
    end_b1 = REC[B1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(B1, []).append((end_b1, REC[B1]['dur']))
    total = 6 + 8 + 10 + 2 + 6 + 16 + 12 + 5 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    P.section(b, 'Introitus — 9/23 %s の実音 (変ロ短調)' % hm(B1), '弔鐘 (低い B♭ のピアノの実音) が小節ごとに鳴り、葬送の太鼓が始まる — 元から変ロ短調の録音をそのまま')
    b += requiem(P, b, B1, 6, pad=0.12); BELL.append((0, 6, 0.16, B1))
    # ---------------- Kyrie — Lamento
    f = b; E = []
    P.section(b, 'Kyrie — Lamento (嘆きのバスの上の君が代)', '「千代に八千代に」から「苔のむすまで」をアルトが歌い、バスは半音で下がる嘆きの音型 — 高音と低音をシンセが長く反響させる')
    t = 0
    for i_, ph in enumerate(KIMI[1:5]):
        entry(P, f + t, 'A', ph, 0, ['千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    LAM = mat(('D3', 2), ('C#3', 2), ('C3', 2), ('B2', 2), ('Bb2', 2), ('A2', 2))
    for k in range(0, t, 3): P.place('B', f + k, LAM, 0, '嘆きのバス' if k == 0 else None)
    P.set_harms(f, [['Dm', 'Dm', 'A/C#', 'A/C#'], ['F/C', 'F/C', 'G/B', 'G/B'], ['Gm/Bb', 'Gm/Bb', 'A7', 'A7']] * 3)
    P.rest_bars('S', f, f + 2); P.hold.update({f + 6, f + 7})
    for k in range(8): P.dyn[f + k] = 1.1
    COLD.append((f, f + 8, 0.07)); BELL.append((f, f + 8, 0.1, B1))
    T2.MANTRA.append((f, f + 8, B1, ('PK',))); CT.LAYOUT.append((f, f + 8, SEMIS, VOICE_SRC, {})); b = f + 8
    # ---------------- Dies irae — 二重フーガ (君が代は + 怒りの日)
    f = b; E = []
    P.section(b, 'Dies irae — 二重フーガ 〈君が代は · 怒りの日〉', '「怒りの日」の聖歌をバスが 2 倍の長さで唱え、その上で「君が代は」の主題が A → S → T と入り、ストレッタで重なる — 弔鐘と太鼓が強く')
    entry(P, f, 'B', DIES, 0, '怒りの日 (Dies irae)', E, synth=0); entry(P, f + 5, 'B', DIES, 0, None, E, synth=0)
    for k, v in enumerate('AST'): entry(P, f + 2 * k + 1, v, SUBJ, 0, '主題 (君が代)', E, synth=0)
    for v, z in {'A': 1, 'S': 3, 'T': 5}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', SUBJ, 0, '主題 (君が代) ストレッタ', E, beat=2, synth=0); entry(P, f + 8, 'A', SUBJ, 0, None, E, beat=1, synth=0)
    harm_flat(P, f, f + 10, E)
    for k in range(10): P.dyn[f + k] = 1.3
    COLD.append((f, f + 10, 0.06)); BELL.append((f, f + 10, 0.2, B2))
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, SEMIS, VOICE_SRC, {})); b = f + 10
    # ---------------- 黙祷
    P.section(b, '黙祷 — 沈黙', 'すべてが止まり、弔鐘とシンセの反響だけが残る')
    P.set_harms(b, [['Dm']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    DRUM.append((b, b + 2)); BELL.append((b, b + 2, 0.14, B1))
    for k, m in enumerate((38, 50, 62)): add('SP', b * BPB + 0.3 * k, 8.0, m, 0.08, None, rid=SYN, pan=(-0.3, 0.3, 0.0)[k])
    T2.MANTRA.append((b, b + 2, B1, ('PK',))); CT.LAYOUT.append((b, b + 2, SEMIS, VOICE_SRC, {})); b += 2
    # ---------------- Lacrimosa — 11:18
    P.section(b, 'Lacrimosa — 9/24 %s の実音 (変ロ短調)' % hm(B2), '元から変ロ短調の 11:18 をそのまま — 低いシンセの実音と太鼓')
    b += requiem(P, b, B2, 6, pad=0.12)
    # ---------------- Fuga — バッハ風 (君が代は)
    f = b
    P.section(b, 'Fuga — 「君が代は」のバッハ風フーガ (変ロ短調)', '提示 (A → S 答唱 → B → T 答唱) → エピソード → 下属調の入り → ストレッタ → 拍ごとに打ち直す保続低音 — 弔鐘は鳴り続ける')
    n_ = T11.bach_fugue(P, b, 'KIMI', '①')
    for k in range(n_): P.dyn[f + k] = 1.25
    COLD.append((f, f + n_, 0.06)); BELL.append((f + 8, f + n_, 0.12, B1))
    T2.MANTRA.append((f, f + n_, B1, ('PK',))); CT.LAYOUT.append((f, f + n_, SEMIS, VOICE_SRC, {})); b = f + n_
    # ---------------- Kimigayo — 哀しみの全旋律
    f = b; E = []
    P.section(b, 'Kimigayo — 哀しみの全旋律 (変ロ短調)', '全旋律をソプラノに、句の終わりは iv・♭VI へ沈み、ナポリの C♭ が「巌となりて」に影を落とす — 弔鐘、反響、最後は全声部がユニゾンの B♭ に')
    t = 0
    for i_, ph in enumerate(KIMI[:5]):
        entry(P, f + t, 'S', ph, 0, ['君が代は', '千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in 'AT': P.rest_bars(v, f + t, f + 12)
    P.rest_bars('S', f + t + 1, f + 12); P.rest_bars('B', f + t + 1, f + 12)
    harm_flat(P, f, f + 12, E)
    for q in range(BPB): P.harm[f * BPB + q] = 'Dm'; P.harm[(f + t) * BPB + q] = 'Dm'
    for q in range(2): P.harm[(f + 6) * BPB + q] = 'Eb'
    P.hold.update({f + 10, f + 11})
    for k in range(12): P.dyn[f + k] = 1.3
    PAD.append((f, f + t + 1, 0.11)); COLD.append((f, f + 12, 0.075)); BELL.append((f, f + t + 1, 0.14, B1))
    T2.MANTRA.append((f, f + 12, B1, ('PK',))); CT.LAYOUT.append((f, f + 12, SEMIS, VOICE_SRC, {})); b = f + 12
    # ---------------- Libera me — Coda
    P.section(b, 'Libera me — 9/23 %s の本当の終わり' % hm(B1), '08:06 の最後 → ユニゾンの B♭、弔鐘と反響が太鼓とともに消える')
    b += requiem(P, b, B1, 5, t0=end_b1, fin=1.0, fout=2.5, gmul=0.65, pad=0.0)
    P.set_harms(b, [['Dm']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    for k, m in enumerate((38, 50, 62, 74)): add('SP', b * BPB + 0.3 * k, 7.0, m, 0.14, None, rid=SYN, pan=(-0.3, 0.3, -0.15, 0.15)[k])
    BELL.append((b, b + 1, 0.16, B1))
    T2.MANTRA.append((b, b + 2, B1, ('PK',))); CT.LAYOUT.append((b, b + 2, SEMIS, VOICE_SRC, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER + [SYN], 'piano_decay': 2.8, 'src_name': {SYN: '11:21 のシンセ (実音)'},
    'title': 'Requiem BADA — Tablet Sessions XXXI · Requiem di guerra',
    'subtitle': '戦争の悲哀のレクイエムとフーガ + 君が代 (変ロ短調) — 弔鐘、葬送の太鼓、怒りの日との二重フーガ、黙祷 (♩=50)',
    'legend': ['TB', 'SP', 'PK'], 'vname': {'SP': '11:21 のシンセ (反響)', 'PK': '葬送の太鼓'},
    'footer': ['Introitus 08:06 → Kyrie (嘆きのバス) → Dies irae (二重フーガ) → 黙祷 → Lacrimosa 11:18 → Fuga (バッハ風) → Kimigayo (全旋律) → Libera me 08:06 の終わり',
               '旋律: 君が代 (林廣守) と「怒りの日」(聖歌)。和声: B♭m・E♭m・G♭・F7・C♭。弔鐘 = 低い B♭ のピアノの実音。音は 9/23・9/24 の録音のピアノとシンセの実音。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet31.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    d['harm'] = [h.replace('F#', 'Gb').replace('G#', 'Ab') if h[:2] in ('F#', 'G#') else h for h in d['harm']]   # 表示: G♭・A♭
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
    print('harm:', ' '.join(d['harm'][k] for k in range(0, len(d['harm']), 4)))
