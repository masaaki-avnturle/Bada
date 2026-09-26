"""
Requiem BADA — Tablet Sessions XXXIV · Kimigayo — Inno (君が代をレクイエムと讃美歌の哀しみのフーガで、提出した録音を使って)
  XXXIII から高音のシンセを消し、君が代を「讃美歌 (コラール) の哀しみ」と「フーガ」で作り換えた。
    - 讃美歌: 各句を 4 声のコラール (等しい音価、掛留で強拍に擦れて次の拍でほどける、句の終わりは iv → i のアーメン終止)
    - フーガ: 第 1 句のバッハ風フーガ、第 2 句「千代に八千代に」と 9/23 08:06 (元から変ロ短調) の主題との二重フーガ
    - 提出した録音: 9/23 08:06 と 9/24 11:18 の実音の抜粋 (どちらも元から変ロ短調、移調なし) を Introitus と Interludium に、Coda は 08:06 の本当の終わり
    - 音は録音から切り出したピアノの実音、重低音のサブベース、弔鐘。太鼓はやわらかく
  使い方: python compose_tablet34.py <bank17.json> [score_tablet34.json]
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
import compose_tablet24 as T24
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
FLAT = ['Dm', 'Gm', 'Bb', 'A7', 'Eb', 'F', 'Dm/F', 'Gm/Bb', 'A', 'C', 'Em7b5']   # 哀しみ (枠 → −4): B♭m, E♭m, G♭, F7, C♭ (ナポリ), A♭, B♭m/D♭, E♭m/G♭, F
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
SUBG = {}                      # 小節 → サブベースの音量
GLB = []                       # (b0, b1, gain): 高音のシンセをばら撒く区間
import random
RNG = random.Random(33)
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
                if cs == 'C': s -= 0.5
                if cs == 'Em7b5': s -= 0.5
                if cs == 'Dm/F': s += 0.3
                if cs == 'Dm' and (bar - b0) % 4 == 0 and h == 0: s += 0.5
                return s
            cs = max(FLAT, key=score) if notes else (['Gm', 'Bb', 'Eb', 'A7'][(bar - b0) % 4] if h == 1 else ['Dm', 'Gm', 'Bb', 'Dm/F'][(bar - b0) % 4])
            held = [m for w, m in notes if w >= 2 and m % 12 == 2]                       # 句の終わりに伸ばす主音: 後半を iv か ♭VI で哀しく
            if h == 1 and held and len(notes) == len(held): cs = 'Gm' if (bar - b0) % 2 else 'Bb'
            for q in range(2): P.harm[a + q] = cs

def post(P, events, extras):
    T24.suspend(P, events)                                                    # 讃美歌の掛留
    for b0, b1, rid, kinds in T2.MANTRA:                                     # 葬送の太鼓: 強・中・付点の弱
        for bar in range(b0, b1):
            if any(a <= bar < z for a, z in DRUM): continue
            for k, g in ((0, 0.09), (2, 0.055), (3.5, 0.035)): add('PK', bar * BPB + k, 0.5, 26, g, None, rid=rid)
    for b0, b1, gain, rid in BELL:                                            # 弔鐘: 低い B♭ (枠では D2) が小節ごとに
        for bar in range(b0, b1):
            add('PF', bar * BPB, 3.8, 38, gain, None, rid=rid, rel=3.5); add('PF', bar * BPB + 0.01, 3.0, 50, gain * 0.45, None, rid=rid, rel=3.0)
    for b0, b1, gain in GLB:                                                 # 高音のシンセをばら撒く (和音の構成音を C6〜E7 に)
        for bar in range(b0, b1):
            for k in range(RNG.choice((2, 3, 3, 4))):
                t = bar * BPB + RNG.choice((0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5)); c = chord(P.harm[int(t)])
                m = RNG.choice([x for x in range(84, 101) if x % 12 in c['pcs']])
                add('GL', t, RNG.choice((1.0, 1.5, 2.0)), m, gain * RNG.uniform(0.6, 1.0), None, pan=RNG.uniform(-0.6, 0.6))
    last = None                                                              # 重低音: 和声の根音のサブベース (半小節ごと)
    for bar in range(P.nbars):
        for h in range(2):
            a = bar * BPB + 2 * h; root = chord(P.harm[a])['root']; m = 26 + (root - 2) % 12
            g = SUBG.get(bar, 0.2)
            if g <= 0: continue
            if last is not None and last[0] == m and last[1] + last[2] >= a + 2 and h == 1: continue
            add('SUB', a, 2.2 if h == 0 else 2.0, m, g, None); add('SUB', a + 0.01, 2.0, m + 12, g * 0.4, None, pan=0.1)
            last = (m, a, 2.2)

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

def chorale(P, b, phrases, E, label):
    """レクイエム: 句を 2 倍の長さでソプラノに、4 声の全音符のコラール"""
    t = 0
    for i_, ph in enumerate(phrases):
        aug = [(2 * d, m) for d, m in ph]
        entry(P, b + t, 'S', aug, 0, label[i_], E, synth=0); t += sum(d for d, _ in aug) / BPB
    return int(round(t))

def stretto_fuga(P, f, subj, E, lab):
    for k, v in enumerate('ASTB'): entry(P, f + 2 * k, v, subj, 0, lab, E, synth=0)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', subj, 0, lab + ' ストレッタ', E, beat=2, synth=0); entry(P, f + 8, 'T', subj, 0, None, E, beat=1, synth=0)

def hymn(P, b, phrases, E, labels):
    """讃美歌: 句をソプラノに (等しい音価)、4 声のコラール。句の終わりの伸ばす音の後半は iv、次は i (アーメン)"""
    t = 0
    for i_, ph in enumerate(phrases):
        entry(P, b + t, 'S', ph, 0, labels[i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    return int(round(t))

def amen(P, bar):
    for q in range(2): P.harm[bar * BPB + 2 + q] = 'Gm'
    if bar + 1 < P.nbars:
        for q in range(2): P.harm[(bar + 1) * BPB + q] = 'Dm'

def build():
    T5.SUBJ['KIMI'] = (SUBJ, CT.harmonize(SUBJ)); CHIYO = KIMI[1]; T5.SUBJ['CHIYO'] = (CHIYO, CT.harmonize(CHIYO))
    T11.hm = lambda r: '君が代' if r == 'KIMI' else ('千代に八千代に' if r == 'CHIYO' else T3.hm(r)); T5.hm = T11.hm
    t0_, inside = CT.excerpt(B1, KEYS[B1], 13.0); sb = CT.make_subject(inside, KEYS[B1], BPM); T5.SUBJ[B1] = (sb, CT.harmonize(sb))
    end_b1 = REC[B1]['dur'] - 5 * BAR_S - 0.5
    T5.USED.setdefault(B1, []).append((end_b1, REC[B1]['dur']))
    total = 6 + 6 + 16 + 6 + 8 + 10 + 12 + 5 + 2
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    P.section(b, 'Introitus — 9/23 %s の実音 (変ロ短調)' % hm(B1), '提出された録音をそのまま (元から変ロ短調) — 弔鐘とサブベース')
    b += requiem(P, b, B1, 6, pad=0.0); BELL.append((0, 6, 0.12, B1))
    for k in range(6): SUBG[k] = 0.06
    # ---------------- Inno I — 讃美歌 (第 1・2 句)
    f = b; E = []
    P.section(b, 'Inno I — 讃美歌 「君が代は」「千代に八千代に」 (変ロ短調)', '4 声のコラール: 掛留が強拍で擦れて次の拍でほどけ、句の終わりは iv → i のアーメン終止')
    t = hymn(P, f, [KIMI[0], KIMI[1]], E, ['君が代は (讃美歌)', '千代に八千代に'])
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in VOICES: P.rest_bars(v, f + t + 1, f + 6)
    harm_flat(P, f, f + 6, E); amen(P, f + 1); amen(P, f + 3)
    for q in range(BPB): P.harm[(f + t) * BPB + q] = 'Dm'
    for k in range(6): P.dyn[f + k] = 1.15; SUBG[f + k] = 0.06
    BELL.append((f, f + 6, 0.1, B1))
    T2.MANTRA.append((f, f + 6, B1, ('PK',))); CT.LAYOUT.append((f, f + 6, SEMIS, VOICE_SRC, {})); b = f + 6
    # ---------------- Fuga I — バッハ風 (君が代は)
    f = b
    P.section(b, 'Fuga I — 「君が代は」のバッハ風フーガ (変ロ短調)', '提示 (A → S 答唱 → B → T 答唱) → エピソード → 下属調の入り → ストレッタ → 打ち直す保続低音 — 掛留が哀しみを深める')
    n_ = T11.bach_fugue(P, b, 'KIMI', '①')
    for k in range(n_): P.dyn[f + k] = 1.25; SUBG[f + k] = 0.05
    T2.MANTRA.append((f, f + n_, B1, ('PK',))); CT.LAYOUT.append((f, f + n_, SEMIS, VOICE_SRC, {})); b = f + n_
    # ---------------- Interludium — 11:18
    P.section(b, 'Interludium — 9/24 %s の実音 (変ロ短調)' % hm(B2), '提出された録音をそのまま — 弔鐘とサブベース')
    b += requiem(P, b, B2, 6, pad=0.0); BELL.append((b - 6, b, 0.1, B2))
    for k in range(b - 6, b): SUBG[k] = 0.06
    # ---------------- Inno II — 讃美歌 (第 3〜5 句)
    f = b; E = []
    P.section(b, 'Inno II — 讃美歌 「さざれ石の」「巌となりて」「苔のむすまで」', '4 声のコラール、掛留とアーメン終止 — 「巌となりて」にナポリの C♭')
    t = hymn(P, f, [KIMI[2], KIMI[3], KIMI[4]], E, ['さざれ石の', '巌となりて', '苔のむすまで'])
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in VOICES: P.rest_bars(v, f + t + 1, f + 8)
    harm_flat(P, f, f + 8, E); amen(P, f + 1); amen(P, f + 3); amen(P, f + 5)
    for q in range(2): P.harm[(f + 2) * BPB + q] = 'Eb'
    for q in range(BPB): P.harm[(f + t) * BPB + q] = 'Dm'
    for k in range(8): P.dyn[f + k] = 1.15; SUBG[f + k] = 0.06
    BELL.append((f, f + 8, 0.1, B1))
    T2.MANTRA.append((f, f + 8, B1, ('PK',))); CT.LAYOUT.append((f, f + 8, SEMIS, VOICE_SRC, {})); b = f + 8
    # ---------------- Fuga II — 二重 (千代に八千代に + 08:06 の主題)
    f = b; E = []
    P.section(b, 'Fuga II — 二重フーガ 〈千代に八千代に · 9/23 %s の主題〉' % hm(B1), '提出された録音の主題と「千代に八千代に」が交互に入り、ストレッタで重なる')
    for k, (v, r, lab) in enumerate((('A', 'CHIYO', '主題 ② (千代に)'), ('S', B1, '主題 ④ (08:06)'), ('T', 'CHIYO', '主題 ② (千代に)'), ('B', B1, '主題 ④ (08:06)'))):
        entry(P, f + 2 * k, v, T5.SUBJ[r][0], 0, lab, E, synth=0)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', CHIYO, 0, '主題 ② ストレッタ', E, beat=2, synth=0); entry(P, f + 8, 'A', T5.SUBJ[B1][0], 0, None, E, beat=1, synth=0)
    harm_flat(P, f, f + 10, E)
    for k in range(10): P.dyn[f + k] = 1.25; SUBG[f + k] = 0.05
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, SEMIS, VOICE_SRC, {'主題 ④ (08:06)': B1})); b = f + 10
    # ---------------- Finale — 全旋律の讃美歌 + ストレッタ + アーメン
    f = b; E = []
    P.section(b, 'Finale — 全旋律の讃美歌とストレッタ (変ロ短調)', '全旋律をソプラノに、その下で「君が代は」が A・T・B にストレッタで重なる — 最後は全声部がユニゾンの B♭、iv → i のアーメン')
    t = 0
    for i_, ph in enumerate(KIMI[:5]):
        entry(P, f + t, 'S', ph, 0, ['君が代は', '千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    for k, (v, bar, beat) in enumerate((('A', 2, 0), ('T', 3, 2), ('B', 5, 0), ('A', 7, 2), ('T', 8, 1))): entry(P, f + bar, v, SUBJ, 0, '主題 ① ストレッタ' if k == 0 else None, E, beat=beat, synth=0)
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in 'AT': P.rest_bars(v, f + t, f + 12)
    P.rest_bars('S', f + t + 1, f + 12); P.rest_bars('B', f + t + 1, f + 12)
    harm_flat(P, f, f + 12, E)
    for q in range(BPB): P.harm[f * BPB + q] = 'Dm'; P.harm[(f + t) * BPB + q] = 'Dm'
    amen(P, f + t - 1)
    P.hold.update({f + 10, f + 11})
    for k in range(12): P.dyn[f + k] = 1.3; SUBG[f + k] = 0.07
    BELL.append((f, f + t + 1, 0.12, B1))
    T2.MANTRA.append((f, f + 12, B1, ('PK',))); CT.LAYOUT.append((f, f + 12, SEMIS, VOICE_SRC, {})); b = f + 12
    # ---------------- Coda — 08:06 の本当の終わり
    P.section(b, 'Coda — 9/23 %s の本当の終わり' % hm(B1), '08:06 の最後 → ユニゾンの B♭ とサブベースが、弔鐘とともに消える')
    b += requiem(P, b, B1, 5, t0=end_b1, fin=1.0, fout=2.5, gmul=0.65, pad=0.0)
    for k in range(b - 5, b): SUBG[k] = 0.05
    P.set_harms(b, [['Dm']] * 2)
    for v in VOICES: P.rest_bars(v, b, b + 2)
    for k in range(2): SUBG[b + k] = 0.06 - 0.03 * k
    DRUM.append((b, b + 2)); BELL.append((b, b + 1, 0.14, B1))
    T2.MANTRA.append((b, b + 2, B1, ('PK',))); CT.LAYOUT.append((b, b + 2, SEMIS, VOICE_SRC, {})); b += 2
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 2.2,
    'title': 'Requiem BADA — Tablet Sessions XXXIV · Inno',
    'subtitle': '君が代をレクイエムと讃美歌の哀しみのフーガで — 提出した録音の実音、ピアノの実音、重低音、掛留とアーメン終止 (♩=50)',
    'legend': ['TB', 'SUB', 'PK'], 'vname': {'SUB': '重低音', 'PK': '太鼓'},
    'footer': ['Introitus 08:06 → Inno I (讃美歌) → Fuga I (君が代は) → Interludium 11:18 → Inno II → Fuga II (千代に + 08:06) → Finale (讃美歌 + ストレッタ) → Coda 08:06',
               '旋律: 君が代 (林廣守) と 9/23 08:06 の主題。讃美歌: 4 声のコラール、掛留、iv → i のアーメン終止。音は 9/23・9/24 の録音の実音とピアノの実音、正弦波のサブベース。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet34.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    d['harm'] = [h.replace('F#', 'Gb').replace('G#', 'Ab') if h[:2] in ('F#', 'G#') else h for h in d['harm']]   # 表示: G♭・A♭
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
    print('harm:', ' '.join(d['harm'][k] for k in range(0, len(d['harm']), 4)))
