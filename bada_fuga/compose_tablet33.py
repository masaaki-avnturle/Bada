"""
Requiem BADA — Tablet Sessions XXXIII · Chiyo ni yachiyo ni (「千代に八千代に」の哀しみのレクイエム、高音のシンセをばら撒いて)
  XXXII (重低音のシンセと実音のピアノ、変ロ短調) をもとに:
    - 「千代に八千代に」(第 2 句 E G A G E G A → C E♭ F E♭ C E♭ F) を中心の旋律に: コラール (Requiem I)、バッハ風フーガ (Fuga I)、
      提出された録音 (9/23 08:06、元から変ロ短調) の主題との二重フーガ (Fuga II)、「怒りの日」との二重フーガ (Fuga III)、
      Finale では全旋律の下で「千代に八千代に」がストレッタで重なる
    - 高音をきれいな響きのシンセ (ガラスのような正弦波、synth.py glass_tone) でばら撒く: 各小節に 2〜4 粒、和音の構成音を C6〜E7 に散らし、
      「千代に八千代に」の旋律には 1 オクターヴ上で寄り添う
    - 重低音のサブベースと弔鐘・葬送の太鼓は XXXII のまま
  使い方: python compose_tablet33.py <bank17.json> [score_tablet33.json]
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
    for b0, b1, rid, kinds in T2.MANTRA:                                     # 葬送の太鼓: 強・中・付点の弱
        for bar in range(b0, b1):
            if any(a <= bar < z for a, z in DRUM): continue
            for k, g in ((0, 0.13), (2, 0.08), (3.5, 0.05)): add('PK', bar * BPB + k, 0.5, 26, g, None, rid=rid)
    for b0, b1, gain, rid in BELL:                                            # 弔鐘: 低い B♭ (枠では D2) が小節ごとに
        for bar in range(b0, b1):
            add('PF', bar * BPB, 3.8, 38, gain, None, rid=rid, rel=3.5); add('PF', bar * BPB + 0.01, 3.0, 50, gain * 0.45, None, rid=rid, rel=3.0)
    for b0, b1, gain in GLB:                                                 # 高音のシンセをばら撒く (和音の構成音を C6〜E7 に)
        for bar in range(b0, b1):
            for k in range(RNG.choice((2, 3, 3, 4))):
                t = bar * BPB + RNG.choice((0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5)); c = chord(P.harm[int(t)])
                m = RNG.choice([x for x in range(84, 101) if x % 12 in c['pcs']])
                add('GL', t, RNG.choice((1.0, 1.5, 2.0)), m, gain * RNG.uniform(0.6, 1.0), None, pan=RNG.uniform(-0.6, 0.6))
    for s_, d, m, lab in events['S']:                                         # 「千代に八千代に」に 1 オクターヴ上で寄り添う
        if lab and '千代' in lab and m is not None: add('GL', s_, d * 1.2, m + 12, 0.07, None, pan=0.2)
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

def build():
    CHIYO = KIMI[1]
    T5.SUBJ['CHIYO'] = (CHIYO, CT.harmonize(CHIYO)); T11.hm = lambda r: '千代に八千代に' if r == 'CHIYO' else ('君が代' if r == 'KIMI' else T3.hm(r)); T5.hm = T11.hm
    t0_, inside = CT.excerpt(B1, KEYS[B1], 13.0); sb = CT.make_subject(inside, KEYS[B1], BPM); T5.SUBJ[B1] = (sb, CT.harmonize(sb))
    total = 8 + 16 + 8 + 10 + 8 + 10 + 12 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    # ---------------- Requiem I — 千代に八千代に のコラール
    f = b; E = []
    P.section(b, 'Requiem I — 「千代に八千代に」のコラール (変ロ短調)', '第 2 句を 2 倍の長さで、4 声の全音符のコラール — 高音のシンセが和音の粒をばら撒き、サブベースが根音を支える')
    t = chorale(P, f, [CHIYO], E, ['千代に八千代に (コラール)'])
    for v in 'ATB': P.rest_bars(v, f, f + 1)
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in VOICES: P.rest_bars(v, f + t + 1, f + 8)
    harm_flat(P, f, f + 8, E); P.hold.update(range(f, f + 8))
    for k in range(8): P.dyn[f + k] = 1.15; SUBG[f + k] = 0.07
    BELL.append((f, f + 8, 0.12, B1)); GLB.append((f, f + 8, 0.07))
    T2.MANTRA.append((f, f + 8, B1, ('PK',))); CT.LAYOUT.append((f, f + 8, SEMIS, VOICE_SRC, {})); b = f + 8
    # ---------------- Fuga I — バッハ風 (千代に八千代に)
    f = b
    P.section(b, 'Fuga I — 「千代に八千代に」のバッハ風フーガ', '提示 (A → S 答唱 → B → T 答唱) → エピソード → 下属調の入り → ストレッタ → 打ち直す保続低音 — 高音のシンセが粒をばら撒く')
    n_ = T11.bach_fugue(P, b, 'CHIYO', '②')
    for k in range(n_): P.dyn[f + k] = 1.25; SUBG[f + k] = 0.055
    GLB.append((f, f + n_, 0.055))
    T2.MANTRA.append((f, f + n_, B1, ('PK',))); CT.LAYOUT.append((f, f + n_, SEMIS, VOICE_SRC, {})); b = f + n_
    # ---------------- Requiem II — さざれ石の
    f = b; E = []
    P.section(b, 'Requiem II — 「さざれ石の」のコラール', '第 3 句を 2 倍の長さで — 句の終わりは iv・♭VI へ沈む')
    t = chorale(P, f, [KIMI[2], KIMI[1]], E, ['さざれ石の', '千代に八千代に'])
    harm_flat(P, f, f + 8, E); P.hold.update(range(f, f + 8))
    for k in range(8): P.dyn[f + k] = 1.15; SUBG[f + k] = 0.07
    BELL.append((f, f + 8, 0.1, B1)); GLB.append((f, f + 8, 0.07))
    T2.MANTRA.append((f, f + 8, B2, ('PK',))); CT.LAYOUT.append((f, f + 8, SEMIS, VOICE_SRC, {})); b = f + 8
    # ---------------- Fuga II — 二重 (千代に八千代に + 9/23 08:06 の主題)
    f = b; E = []
    P.section(b, 'Fuga II — 二重フーガ 〈千代に八千代に · 9/23 %s の主題〉' % hm(B1), '提出された録音 (元から変ロ短調) の主題と「千代に八千代に」が交互に入り、ストレッタで重なる')
    for k, (v, r, lab) in enumerate((('A', 'CHIYO', '主題 ② (千代に)'), ('S', B1, '主題 ④ (08:06)'), ('T', 'CHIYO', '主題 ② (千代に)'), ('B', B1, '主題 ④ (08:06)'))):
        entry(P, f + 2 * k, v, T5.SUBJ[r][0], 0, lab, E, synth=0)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', CHIYO, 0, '主題 ② ストレッタ', E, beat=2, synth=0); entry(P, f + 8, 'A', T5.SUBJ[B1][0], 0, None, E, beat=1, synth=0)
    harm_flat(P, f, f + 10, E)
    for k in range(10): P.dyn[f + k] = 1.25; SUBG[f + k] = 0.055
    GLB.append((f, f + 10, 0.05))
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, SEMIS, VOICE_SRC, {'主題 ④ (08:06)': B1})); b = f + 10
    # ---------------- Requiem III
    f = b; E = []
    P.section(b, 'Requiem III — 「巌となりて」「苔のむすまで」のコラール', '第 4・5 句を 2 倍の長さで — 「巌となりて」にナポリの C♭')
    t = chorale(P, f, [KIMI[3], KIMI[4]], E, ['巌となりて', '苔のむすまで'])
    harm_flat(P, f, f + 8, E); P.hold.update(range(f, f + 8))
    for q in range(2): P.harm[(f + 1) * BPB + q] = 'Eb'
    for k in range(8): P.dyn[f + k] = 1.15; SUBG[f + k] = 0.07
    BELL.append((f, f + 8, 0.1, B1)); GLB.append((f, f + 8, 0.07))
    T2.MANTRA.append((f, f + 8, B1, ('PK',))); CT.LAYOUT.append((f, f + 8, SEMIS, VOICE_SRC, {})); b = f + 8
    # ---------------- Fuga III — 二重 (千代に八千代に + 怒りの日)
    f = b; E = []
    P.section(b, 'Fuga III — 二重フーガ 〈千代に八千代に · 怒りの日〉', '「怒りの日」をバスが 2 倍の長さで唱え、その上で「千代に八千代に」が A → S → T と入り、ストレッタで重なる')
    entry(P, f, 'B', DIES, 0, '怒りの日 (Dies irae)', E, synth=0); entry(P, f + 5, 'B', DIES, 0, None, E, synth=0)
    for k, v in enumerate('AST'): entry(P, f + 2 * k + 1, v, CHIYO, 0, '主題 ② (千代に)', E, synth=0)
    for v, z in {'A': 1, 'S': 3, 'T': 5}.items(): P.rest_bars(v, f, f + z)
    entry(P, f + 7, 'S', CHIYO, 0, '主題 ② ストレッタ', E, beat=2, synth=0); entry(P, f + 8, 'A', CHIYO, 0, None, E, beat=1, synth=0)
    harm_flat(P, f, f + 10, E)
    for k in range(10): P.dyn[f + k] = 1.3; SUBG[f + k] = 0.085
    BELL.append((f, f + 10, 0.16, B2)); GLB.append((f, f + 10, 0.05))
    T2.MANTRA.append((f, f + 10, B2, ('PK',))); CT.LAYOUT.append((f, f + 10, SEMIS, VOICE_SRC, {})); b = f + 10
    # ---------------- Finale
    f = b; E = []
    P.section(b, 'Finale — 全旋律と「千代に八千代に」のストレッタ (変ロ短調)', '全旋律をソプラノに、その下で「千代に八千代に」が A・T・B にストレッタで重なる — 高音のシンセが最も多く散り、最後は全声部がユニゾンの B♭')
    t = 0
    for i_, ph in enumerate(KIMI[:5]):
        entry(P, f + t, 'S', ph, 0, ['君が代は', '千代に八千代に', 'さざれ石の', '巌となりて', '苔のむすまで'][i_], E, synth=0); t += sum(d for d, _ in ph) / BPB
    t = int(round(t))
    for k, (v, bar, beat) in enumerate((('A', 2, 0), ('T', 3, 2), ('B', 5, 0), ('A', 7, 2), ('T', 8, 1))): entry(P, f + bar, v, CHIYO, 0, '主題 ② ストレッタ' if k == 0 else None, E, beat=beat, synth=0)
    for v in VOICES: entry(P, f + t, v, KIMI[5], 0, None, E, synth=0)
    for v in 'AT': P.rest_bars(v, f + t, f + 12)
    P.rest_bars('S', f + t + 1, f + 12); P.rest_bars('B', f + t + 1, f + 12)
    harm_flat(P, f, f + 12, E)
    for q in range(BPB): P.harm[f * BPB + q] = 'Dm'; P.harm[(f + t) * BPB + q] = 'Dm'
    P.hold.update({f + 10, f + 11})
    for k in range(12): P.dyn[f + k] = 1.3; SUBG[f + k] = 0.075
    BELL.append((f, f + t + 1, 0.14, B1)); GLB.append((f, f + 12, 0.085))
    T2.MANTRA.append((f, f + 12, B1, ('PK',))); CT.LAYOUT.append((f, f + 12, SEMIS, VOICE_SRC, {})); b = f + 12
    P.set_harms(b, [['Dm']] * 3)
    for v in VOICES: P.rest_bars(v, b, b + 3)
    for k in range(3): SUBG[b + k] = 0.075 - 0.022 * k
    DRUM.append((b + 1, b + 3)); BELL.append((b, b + 1, 0.14, B1)); GLB.append((b, b + 3, 0.06))
    T2.MANTRA.append((b, b + 3, B1, ('PK',))); CT.LAYOUT.append((b, b + 3, SEMIS, VOICE_SRC, {})); b += 3
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 2.2,
    'title': 'Requiem BADA — Tablet Sessions XXXIII · Chiyo ni yachiyo ni',
    'subtitle': '「千代に八千代に」の哀しみのレクイエムとフーガ — 高音をきれいなシンセでばら撒き、重低音と実音のピアノ (♩=50)',
    'legend': ['GL', 'SUB', 'PK'], 'vname': {'GL': '高音のシンセ', 'SUB': '重低音', 'PK': '太鼓'},
    'footer': ['Requiem I (千代に のコラール) → Fuga I (バッハ風) → Requiem II → Fuga II (千代に + 08:06 の主題) → Requiem III → Fuga III (千代に + 怒りの日) → Finale → B♭',
               '旋律: 君が代 (林廣守) の第 2 句を中心に、9/23 08:06 の主題と「怒りの日」。音は 9/23・9/24 の録音のピアノの実音、ガラスのような高音のシンセ、正弦波のサブベース。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet33.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    d['harm'] = [h.replace('F#', 'Gb').replace('G#', 'Ab') if h[:2] in ('F#', 'G#') else h for h in d['harm']]   # 表示: G♭・A♭
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=0)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
    print('harm:', ' '.join(d['harm'][k] for k in range(0, len(d['harm']), 4)))
