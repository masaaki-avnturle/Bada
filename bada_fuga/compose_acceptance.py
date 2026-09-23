#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BADA 528 — Acceptance (E minor)
  BWV 528 (トリオ・ソナタ第 4 番 ホ短調) を、坂本龍一『リトル・ブッダ』の「Acceptance」を思わせる
  哀愁の弦楽 (ゆっくりした和声、掛留、厚い弦、まばらなピアノ、インドの笛とタンプーラ) に作り換える。
  旋律は引用せず、雰囲気と編成だけを参照する。
  - Sweet Trio 冒頭の金属的な「チーン」(エレピの FM 倍音・ブラシのハイハット) をコントラバスの独奏に置き換える
  - 作曲者のタブレット録音 (20260922_090933 / 090146) の実音を 2 か所で流し、採譜した低音・和音を
    コントラバスと弦が追いかけて伴奏する。録音の旋律と和声から「タブレットの主題 T」を作り、Adagio と頂点で歌う
  形式: Prologo (Cb 独奏) → Tablet I (録音 090933) → Adagio (主題 T) → Andante (BWV 528 風トリオ)
        → Lamento (B-A-D-A) → Fugato → 三重結合 → Acceptance (主題 T の頂点) → Tablet II (録音 090146) → Fine
  全体をニ短調で書き、出力時に +2 半音してホ短調にする (録音は実音のまま)。
"""
import sys, json, os
from compose import *
import compose
from compose_piano import copy_bars
import compose_dialogo as D

TRANSPOSE = 2
BPM = 60
extras = D.extras
SEG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples', 'tablet_segments.json')))

# タブレットの主題 T (録音 090146 の 199–241 秒の最上声と和声 Em7–D–Dsus4–A–Gmaj7/F#… から。ニ短調で記譜)
THEME_T = mat(('A4',3),('G4',.5),('F4',.5), ('G4',2),('F4',1),('E4',1), ('D4',2),('E4',1),('F4',1), ('A4',4),
              ('G4',2),('F#4',1),('A4',1), ('C5',2),('D5',1),('C5',1), ('A4',2),('C5',1),('A4',1), ('F4',2),('E4',2))
H_T = [['Dm7'], ['C', 'C', 'Csus4', 'C'], ['G', 'G', 'Fmaj7/E', 'Fmaj7/E'], ['Dm7'],
       ['C/E', 'C/E', 'D7/F#', 'D7/F#'], ['Am', 'Am', 'Bbmaj7', 'Bbmaj7'], ['Dm7/F', 'Dm7/F', 'Fmaj7/A', 'Fmaj7/A'], ['Gm7', 'Gm7', 'A7', 'A7']]
# 主題 T の低音: ゆっくり下行してから上がり、終止の A へ
BASS_T = mat(('D3',4), ('C3',4), ('G2',2),('E2',2), ('D2',4), ('E2',2),('F#2',2), ('A2',2),('Bb2',2), ('F2',2),('A2',2), ('G2',2),('A2',2))
# 2 回目は F から入る (前の終止 A–E からの連続 5 度を避ける)
H_T2 = [['Dm7/F']] + H_T[1:]
BASS_T2 = mat(('F2',4)) + BASS_T[1:]

PRO, REC1, ADA, AND, LAM, FUG, TRI, ACC, REC2, FIN = 3, 8, 8, 12, 12, 17, 6, 16, 12, 3
B_PRO = 0; B_REC1 = B_PRO + PRO; B_ADA = B_REC1 + REC1; B_AND = B_ADA + ADA; B_LAM = B_AND + AND
B_FUG = B_LAM + LAM; B_TRI = B_FUG + FUG; B_ACC = B_TRI + TRI; B_REC2 = B_ACC + ACC; B_FIN = B_REC2 + REC2
TOTAL = B_FIN + FIN

def add(v, bar, beat, dbeats, midi, vel=0.5, label=None, **kw):
    e = {'v': v, 'beat': bar * BPB + beat, 'dbeats': dbeats, 'm': midi, 'gain': vel, 'label': label}
    e.update(kw); extras.append(e)

def set_range(P, b0, b1, role, dyn, det=1.0):
    for b in range(b0, b1): P.role[b] = role; P.dyn[b] = dyn; P.det[b] = det

def rest_all(P, b0, b1):
    for v in VOICES: P.rest_bars(v, b0, b1)

def fold(m, lo, hi):
    while m > hi: m -= 12
    while m < lo: m += 12
    return m

def sustained(segs, key):
    """連続する区間で同じ音が続くあいだを 1 音にまとめる: [(t0, t1, midi)]"""
    out, open_ = [], {}
    for i, s in enumerate(segs):
        cur = set(key(s)); t_end = s['t'] + s['d']
        for m in list(open_):
            if m not in cur: out.append((open_.pop(m), segs[i - 1]['t'] + segs[i - 1]['d'], m))
        for m in cur:
            if m not in open_: open_[m] = s['t']
        last = t_end
    out += [(t0, last, m) for m, t0 in open_.items()]
    return sorted(out)

def tablet(P, rid, bar0, lead, nbars, label):
    """録音の実音を bar0 から流し、採譜した低音をコントラバス、内声を弦で追う (♩=60 なので 1 拍 = 1 秒)。"""
    info = SEG[rid]
    segs = [s for s in info['segs'] if s['t'] >= lead - 0.01]
    b0 = bar0 * BPB - lead                               # 抜粋の 0 秒が置かれる拍
    add('REC', 0, b0, info['dur'] + 0.2, 0, 2.5, None, src=info['file'], off=0.0, rid=rid)
    for k in range(nbars): P.tempo[bar0 + k] = BPM
    # 和声表示 (採譜した和音名を -2 半音してニ短調の記譜にそろえる)
    for beat in range(bar0 * BPB, (bar0 + nbars) * BPB):
        tt = beat - b0; cur = None
        for s in segs:
            if s['t'] <= tt + 0.05: cur = s
        if cur: P.harm[beat] = transpose_h([[cur['ch']]], -TRANSPOSE)[0][0]
    # 低音 → コントラバス (実音 E1–G2)、弦のチェロは 1 オクターヴ上
    for t0, t1, m in sustained(segs, lambda s: [s['m'][0]]):
        cb = fold(m, 28, 43) - TRANSPOSE
        add('CB', 0, b0 + t0, t1 - t0 + 0.15, cb, 0.3)
        add('VC', 0, b0 + t0, t1 - t0 + 0.15, cb + 12, 0.1)
    # 内声 → Vn II / Va (実音 E3–E5 に折り返す)
    for t0, t1, m in sustained(segs, lambda s: sorted({fold(x, 52, 76) for x in s['m'][1:]})[:4]):
        add('V2' if m >= 64 else 'VA', 0, b0 + t0, t1 - t0 + 0.3, m - TRANSPOSE, 0.08)
    # 採譜した音そのもの (表示用・無音)
    first = True
    for s in segs:
        for m in s['m']:
            add('TB', 0, b0 + s['t'], s['d'], m - TRANSPOSE, 0.0, label if first else None); first = False
    return b0 + info['dur']

def tanpura(bar0, bar1, vel=0.12):
    for bar in range(bar0, bar1):
        for k, m in enumerate((n('A2'), n('D3'), n('D3'), n('D2'))):     # 実音 B2 E3 E3 E2 (Pa Sa Sa Sa)
            add('TA', bar, k, 3.5, m, vel * (0.8 if k == 3 else 1.0))

def build():
    T = Piece(130); compose.build_fugue(T, 0)
    P = Piece(TOTAL)
    # ---------- Prologo: コントラバス独奏
    P.section(B_PRO, 'Prologo — Contrabbasso solo', '冒頭の金属的な音 (トライアングルのように聞こえた高音) をコントラバスの独奏に置き換え。タンプーラの E–B が遠くで鳴る')
    rest_all(P, B_PRO, B_REC1); set_range(P, B_PRO, B_REC1, 'rec', 0.6)
    P.set_harms(B_PRO, [['Dm'], ['Dm'], ['Dm', 'Dm', 'F', 'C']])
    for bar, beat, d, name, v in ((0, 0, 4, 'D1', .62), (1, 0, 2, 'A1', .56), (1, 2, 2, 'D2', .58), (2, 0, 2, 'F2', .6), (2, 2, 1, 'E2', .54), (2, 3, 1, 'C2', .5)):
        add('CB', B_PRO + bar, beat, d + 0.1, n(name), v, 'Contrabbasso solo' if bar == 0 else None)
    tanpura(B_PRO + 1, B_REC1, 0.09)
    # ---------- Tablet I: 録音 090933 (実音)
    P.section(B_REC1, 'Tablet I — 録音 20260922_090933', 'あなたのタブレット録音 (Gmaj7–Em–Bm7–F#m7–C–Am7–Em7–Dsus4) を実音で。コントラバスと弦が採譜した低音と和音を追う')
    rest_all(P, B_REC1, B_ADA); set_range(P, B_REC1, B_ADA, 'rec', 0.7)
    tablet(P, '090933', B_REC1, SEG['090933']['segs'][0]['t'], REC1, 'タブレット録音 090933')
    # ---------- Adagio: タブレットの主題 T (弦のコラール)
    P.section(B_ADA, 'Adagio — タブレットの主題', 'BWV 528 第 1 楽章 Adagio の位置。録音の最上声から作った主題 T を弦が歌う (Vn I)、コントラバスが支える')
    P.set_harms(B_ADA, H_T); P.place('S', B_ADA, THEME_T, 0, 'T (タブレットの主題)'); P.place('B', B_ADA, BASS_T)
    set_range(P, B_ADA, B_AND, 'str', 0.62)
    for k in range(ADA): P.dyn[B_ADA + k] = 0.66 + 0.03 * k; P.tempo[B_ADA + k] = 56
    P.tempo[B_AND - 1] = 50
    # ---------- Andante: BWV 528 風トリオ (オーボエ + フルート + ピッツィカートのバス)
    P.section(B_AND, 'Andante — Trio', 'BWV 528 第 2 楽章 Andante 風: ピアノの右手とオーボエが主題 I、フルートが主題 II、コントラバスのピッツィカートが歩く。5 小節後に上下を交換')
    P.set_harms(B_AND, compose.H_S1); P.place('S', B_AND, compose.S1, 12, 'S1 (オーボエ)'); P.place('A', B_AND, compose.S2, 0, 'S2 (フルート)')
    P.set_harms(B_AND + 5, compose.H_S1); P.place('A', B_AND + 5, compose.S1, 0, 'S1 (オーボエ)'); P.place('S', B_AND + 5, compose.S2, 12, 'S2 (フルート)')
    P.set_harms(B_AND + 10, [['Gm', 'Gm', 'Bbmaj7', 'A7'], ['Dm']])
    P.rest_bars('T', B_AND, B_LAM)
    set_range(P, B_AND, B_LAM, 'pno', 0.6, det=0.95)
    for k in range(AND): P.tempo[B_AND + k] = 60
    P.tempo[B_LAM - 1] = 52
    # ---------- Lamento: 嘆きのバス + B-A-D-A のカノン (ピアノ + 弦)
    P.section(B_LAM, 'Lamento — B-A-D-A', '嘆きのバス (E D# D C# C B) の上で、B-A-D-A (C–B–E–B) をバンスリとピアノがカノンで唱える。弦が少しずつ満ちる')
    D.lament(P, B_LAM, 4, label=True, dyn=lambda c: 0.58 + 0.07 * c)
    P.rest_bars('S', B_LAM, B_LAM + 3)
    for k in range(LAM): P.role[B_LAM + k] = 'pno' if k < 3 else 'both'; P.tempo[B_LAM + k] = 58
    # ---------- Fugato
    copy_bars(T, P, 0, FUG, B_FUG)
    P.sections = [(b, t.replace('I. Soggetto I 〈MOTHER〉', 'Fugato — 主題 I 〈MOTHER〉'), s.replace('主題 I の提示 — 4 声フーガ (ニ短調)', '主題 I の 4 声提示 (ホ短調): ピアノ独りで始まり、弦が加わる'))
                  for b, t, s in P.sections]
    for k in range(FUG):
        P.role[B_FUG + k] = 'pno' if k < 5 else 'both'; P.dyn[B_FUG + k] = 0.7 + 0.012 * k; P.tempo[B_FUG + k] = 63
    # ---------- 三重結合
    copy_bars(T, P, 101, 101 + TRI, B_TRI)
    P.section(B_TRI, 'Fuga a tre soggetti — 三重結合', '主題 I + II + III が全楽器で重なる')
    set_range(P, B_TRI, B_ACC, 'both', 0.95)
    for k in range(TRI): P.tempo[B_TRI + k] = 60
    P.tempo[B_ACC - 1] = 50
    # ---------- Acceptance: 主題 T の頂点 (2 回)
    P.section(B_ACC, 'Acceptance — 受容', '主題 T を厚い弦がオクターヴで歌い、ピアノが分散和音でまばらに降らせる。2 回目はバンスリが 1 オクターヴ上で重なる')
    P.set_harms(B_ACC, H_T); P.place('S', B_ACC, THEME_T, 0, 'T (タブレットの主題)'); P.place('B', B_ACC, BASS_T)
    P.set_harms(B_ACC + 8, H_T2); P.place('S', B_ACC + 8, THEME_T, 0, 'T (バンスリと弦)'); P.place('B', B_ACC + 8, BASS_T2)
    for k in range(ACC):
        P.role[B_ACC + k] = 'str' if k < 8 else 'both'; P.tempo[B_ACC + k] = 54
        P.dyn[B_ACC + k] = 0.7 + 0.02 * k if k < 8 else 0.9 - (0.03 * (k - 12) if k >= 12 else 0)
    P.tempo[B_REC2 - 1] = 46
    # ---------- Tablet II: 録音 090146 (実音) → Fine
    P.section(B_REC2, 'Tablet II — 録音 20260922_090146', 'あなたのタブレット録音 (B7–D–Bm–C–Em–F#m7–Am–Bm–D7–Em) を実音で。コントラバスとタンプーラが寄り添い、録音自身の Em で終わる')
    rest_all(P, B_REC2, TOTAL); set_range(P, B_REC2, TOTAL, 'rec', 0.7)
    lead = next(s['t'] for s in SEG['090146']['segs'] if s['d'] >= 0.25)
    tablet(P, '090146', B_REC2, lead, REC2, 'タブレット録音 090146')
    tanpura(B_REC2 + 6, B_FIN + 1, 0.08)
    P.section(B_FIN, 'Fine', 'ホ短調の和音にコントラバスの E が残り、バンスリが B-A-D-A (C–B–E–B) を一度だけ唱えて消える')
    P.set_harms(B_FIN, [['Dm']] * FIN); P.hold.update(range(B_FIN, TOTAL))
    for k in range(FIN): P.tempo[B_FIN + k] = 50; P.dyn[B_FIN + k] = 0.4
    return P

def post(P, events, ex):
    """重ね: トリオの木管とピッツィカート、B-A-D-A のバンスリ、頂点のピアノ分散和音とパッド、終結。"""
    for v in VOICES:
        for s, d, m, lab in events[v]:
            bar = int(s // BPB); role = P.role.get(bar, ''); dyn = P.dyn.get(bar, 1.0)
            if B_AND <= bar < B_LAM:
                if v == 'B': add('CBP', 0, s, min(d, 1.0), fold(m - 12, 26, 45), 0.5 * dyn)
                if lab and lab.startswith('S1'): add('WW', 0, s, d, m, 0.4 * dyn)
                if lab and lab.startswith('S2'): add('FL', 0, s, d, m + (12 if m < 65 else 0), 0.34 * dyn)
            if lab and 'B-A-D-A' in lab and B_LAM <= bar < B_FUG and v == 'A':
                add('BN', 0, s, d, m + 12, 0.3 * dyn)
            if lab and 'バンスリ' in lab:
                add('BN', 0, s, d, m + 12, 0.34 * dyn)
            if B_FUG + 5 <= bar < B_ACC and lab:
                if lab.startswith('S1'): add('WW', 0, s, d, m + (12 if m < 60 else 0), 0.28 * dyn)
                elif lab.startswith('S2'): add('FL', 0, s, d, m + (12 if m < 65 else 0), 0.26 * dyn)
                elif lab.startswith('S3'): add('BN', 0, s, d, m + (12 if m < 62 else 0), 0.28 * dyn)
            if B_ACC <= bar < B_REC2 and v == 'S':
                add('V1', 0, s, d, m + 12, (0.16 if bar < B_ACC + 8 else 0.22) * dyn)       # オクターヴ上の Vn
    # Acceptance: ピアノの分散和音 (8 分音符で上行 → 下行) とパッド
    for bar in range(B_ACC, B_REC2):
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half])
            tones = [m for m in range(62, 86) if m % 12 in c['pcs']]
            seq = tones[:4] + tones[1:4][::-1] + [tones[0]]
            for i, m in enumerate(seq[:4]):
                add('H', bar, half + i * 0.5, 1.2, m, 0.22 * P.dyn.get(bar, 1.0))
            for m in [x for x in range(50, 66) if x % 12 in c['pcs']][:3]:
                add('PD', bar, half, 2.4, m, 0.05)
    # Lamento の後半にもパッドを薄く
    for bar in range(B_LAM + 3, B_FUG):
        c = chord(P.harm[bar * BPB])
        for m in [x for x in range(50, 66) if x % 12 in c['pcs']][:3]: add('PD', bar, 0, 4.2, m, 0.04)
    # Fine: 実音 Em の持続 (Cb E1 + 弦) と B-A-D-A
    add('CB', B_FIN, 0, 12, n('D1'), 0.5)
    for m, v, g in ((n('D3'), 'VC', .14), (n('A3'), 'VA', .12), (n('F4'), 'V2', .1), (n('A4'), 'V1', .08)):
        add(v, B_FIN, 0, 12, m, g)
    for i, (beat, d, m) in enumerate(((0, 2, n('Bb4')), (2, 2, n('A4')), (4, 2, n('D5')), (6, 5, n('A4')))):
        add('BN', B_FIN, beat, d, m, 0.24, 'B-A-D-A (バンスリ)' if i == 0 else None)

META = {
    'style': 'acceptance', 'detach': 0.95, 'humanize': True,
    'title': 'BADA 528 — Acceptance',
    'subtitle': 'Trio Sonata BWV 528 · E minor · ♩=54–63 ／ 「Acceptance」(坂本龍一) の哀愁 × あなたのタブレット録音',
    'footer': ['骨格 ← J.S.バッハ BWV 528 (トリオ・ソナタ第 4 番 ホ短調) ／ 雰囲気 ← 坂本龍一「Acceptance」(『リトル・ブッダ』) の弦・ピアノ・インドの笛 (旋律は引用せず)',
               '録音 ← 090933 / 090146 の実音と採譜 (主題 T) ／ 主題 I ← MOTHER ／ II ← トラック18 ／ B-A-D-A ／ 嘆きのバス  ｜  弦 5 部 · Cb · Pf · Ob · Fl · バンスリ · タンプーラ',
               'Prologo (Cb 独奏) → Tablet I → Adagio → Andante (トリオ) → Lamento → Fugato → 三重結合 → Acceptance → Tablet II → Fine'],
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_acceptance.json'
    compose.main(out, seed=528, bpm=BPM, builder=build, meta=META, extras=extras, transpose_semis=TRANSPOSE, post=post)
