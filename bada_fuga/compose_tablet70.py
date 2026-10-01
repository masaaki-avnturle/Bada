#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXX · Requiem 08:06 (2026-09-23 08:06 の録音を主題曲に、主題を 16 倍に伸ばし、LXIX をバックに — フーガを醸すレクイエム)
  主題曲: 9/23 08:06 の録音 (変ロ短調、ピアノの実音)。最上声から主題 — 変ロ短調で シ♭・ソ♭・ファ・ミ♭・ド・シ♭ と下りる嘆きの線 (8 拍)。
  16 倍の伸び: 主題の 4 分音符を 16 倍 (4 小節) に。伸ばした音はテノールがピアノで 4 分音符ごとに打ち直す (♩=60、止まらない)。深い鐘は 2 全音符ごと。
  バック: LXIX (先程の曲、ホ短調) を、伸ばした長い音の中で流す — 調が三全音離れているので、LXIX の音を採譜して (basic-pitch)
    6 半音下げ (ホ短調 → 変ロ短調)、速さは変えずにピアノの実音で弾き直す。LXIX の属音シの保続 → この曲の属音ファの保続に重なる。
  フーガを醸す: 主音の上で主題 → 5 度上の答え、長いドの保続の上でストレッタ、最後の主音の上で 1 倍と 2 倍 (拡大) の主題を同時に。
    II 楽章は 08:06 の主題の 4 声フーガ。IV 楽章ももう一度 ×16 で、LXIX のフーガ (II 楽章) をバックに。
  形式 (♩=60, 変ロ短調):
    Introitus (08:06 の始まり) → I. Requiem ×16 → II. Fuga (08:06 の主題) → III. Lacrimosa (08:06 の実音) → IV. Finale ×16 con Fuga → Amen (変ロ長調)
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet70.py <bank70.json> <素材の wav フォルダ (20260923_080607.wav・tablet69.wav)> [score_tablet70.json]
          python compose_tablet67.py level <score_tablet70.json> <LXIX を弾き直した所だけの wav>   (バックの大きさをそろえる)
"""
import sys, os, json
import numpy as np, soundfile as sf
from compose import *
import compose
import compose_tablet as CT
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet63 as LXIII
import compose_tablet65 as LXV
import compose_tablet69 as LXIX

add = CT.add
BPM = 60
SRC = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else '.'
OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet70.json'
TH = '20260923_080607'                             # 主題曲
BBM = -4                                           # 変ロ短調 (ニ短調から)
BACK_SEMIS = -6                                    # LXIX (ホ短調) → 変ロ短調
VOICE_SRC = {'S': TH, 'A': '20260925_130431', 'T': TH, 'B': '20260925_124643'}
DYNK = 1.3
H8 = ['Dm', 'Gm', 'A7', 'Gm', 'A7', 'A7', 'A7', 'Dm']   # 主題の 1 拍ごとの和音 (エンジンのニ短調、終わりは主和音)
AUD, BACK = [], []                                  # AUD: 主題曲の実音の抜粋 / BACK: LXIX をピアノで弾き直す抜粋

def build():
    t0, inside = CT.excerpt(TH, BBM, 13.0); s_ = LXIII.smooth(CT.make_subject(inside, BBM, BPM))
    H = [H8[:4], H8[4:]]; T5.SUBJ[TH] = (s_, H)
    print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = 8 + 32 + 16 + 8 + 32 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    CT.LAYOUT.append((0, total, BBM, VOICE_SRC, {}))
    b = 0
    rec = os.path.join(SRC, TH + '.wav')
    def window(b0, n_, off, tag):
        AUD.append((b0, n_, rec, off, 0.5 * LXIX.ex_gain(rec, off, n_ * 4.0), tag, 3.0))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def back(b0, n_, off, tag):
        BACK.append((b0, n_, off, tag))
        for v in 'SA': P.rest_bars(v, b0, b0 + n_)
    def audio(n_, title, sub, off, tag):
        nonlocal b
        P.section(b, title, sub); window(b, n_, off, tag)
        for v in VOICES: P.rest_bars(v, b, b + n_)
        P.set_harms(b, [['Dm'] * 4] * n_); b += n_
    def entry(v, bar, tr, lab, k=1): P.place(v, bar, [(d * k, m + tr) for d, m in s_], 0, lab)
    def requiem16(title, sub, label, wins, backs, dyn0, dyn1, final_lab):
        """主題 ×16 (32 小節: シ♭ 4 · ソ♭ 4 · ファ 4 · ミ♭ 4 · ド 12 · シ♭ 4)"""
        nonlocal b
        f = b; P.section(f, title, sub)
        b += LXIX.aug(P, f, 16, s_, H8, label)
        for j in range(32): P.dyn[f + j] = DYNK * (dyn0 + (dyn1 - dyn0) * j / 31)
        P.set_harms(f, H); entry('A', f, 0, '主題 (08:06) ×1 — フーガ'); P.set_harms(f + 2, transpose_h(H, 7)); entry('S', f + 2, 7 - 12, '答え (5 度上)')
        for b0, n_, off, tag in wins: window(f + b0, n_, off, tag)
        for b0, n_, off, tag in backs: back(f + b0, n_, off, tag)
        P.set_harms(f + 24, H + H); entry('S', f + 24, 0, '主題 ストレッタ (ドの保続の上)'); entry('A', f + 25, -12, None)
        P.set_harms(f + 28, [[H8[2 * i]] * 2 + [H8[2 * i + 1]] * 2 for i in range(4)])
        entry('A', f + 28, -12, final_lab, k=2); entry('S', f + 28, 0, None); entry('S', f + 30, 0, None)
        LXIII.ARP.append((f + 24, f + 28, 0.09, BBM))
    # ================= Introitus
    audio(8, 'Introitus — 主題曲 9/23 08:06 の実音 (変ロ短調)', '主題曲の始まり — ピアノの実音のまま', 0.0, '主題曲 9/23 08:06 — 始まり')
    # ================= I. Requiem ×16
    requiem16('I. Requiem per augmentationem ×16 (変ロ短調)', '08:06 の主題を 16 倍に — 伸ばした音の中に、主題曲の実音・LXIX (6 半音下げてピアノで)・主題のフーガ',
              '主題 (08:06) ×16 — 4 分音符を 16 倍に',
              [(4, 4, 40.0, '主題曲 9/23 08:06 (ソ♭の中で)'), (12, 4, 70.0, '主題曲 9/23 08:06 (ミ♭の中で)')],
              [(8, 4, 48.0, 'LXIX — ×16 の属音の保続 (ファの中で)'), (16, 8, 64.0, 'LXIX — ×16 のストレッタのあたり (ドの中で)')], 0.62, 0.8, '主題 ×2 (拡大) + ×1')
    # ================= II. Fuga
    f = b; P.section(f, 'II. Fuga — 08:06 の主題 (変ロ短調)', '主題曲の下りる主題の 4 声フーガ — 提示、下属調、ストレッタ、保続低音')
    T11.bach_fugue(P, f, TH, '①'); b += 16
    for j in range(16): P.dyn[f + j] = DYNK * (0.7 if j < 8 else 0.8)
    LXIII.ARP.append((f + 8, f + 12, 0.08, BBM))
    # ================= III. Lacrimosa
    audio(8, 'III. Lacrimosa — 主題曲の実音 (変ロ短調)', '9/23 08:06 の実音 — 打ち直しが止まる', 100.0, '主題曲 9/23 08:06 — Lacrimosa')
    # ================= IV. Finale ×16 con Fuga
    requiem16('IV. Finale per augmentationem ×16 con Fuga (変ロ短調)', 'もう一度 16 倍に — 長いドの中で LXIX のフーガ、最後は主題の 1 倍と 2 倍',
              '主題 (08:06) ×16 (二度目)',
              [(4, 4, 140.0, '主題曲 9/23 08:06 (ソ♭の中で)'), (12, 4, 160.0, '主題曲 9/23 08:06 (ミ♭の中で)')],
              [(8, 4, 288.0, 'LXIX — Finale の属音の保続 (ファの中で)'), (16, 8, 176.0, 'LXIX — II. Fuga (ドの保続の上で)')], 0.72, 0.9, '主題 ×2 (拡大) + ×1 — 最後')
    # ================= Amen (変ロ長調)
    f = b; P.section(f, 'Amen — 変格終止 (変ロ長調の和音で)', 'iv → I: 打ち直しが止まり、変ロ長調の和音だけが残る'); b += 3
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.62
    LXIII.ARP.append((f, f + 2, 0.09, BBM))
    assert b == total, (b, total)
    return P

def post(P, events, extras):
    LXIII.post(P, events, extras)
    for b0, n_, path, off, g, tag, fout in AUD:
        add('REC', b0 * BPB, n_ * BPB + 1.0, 0, g, None, src=path, off=off, fin=2.0, fout=fout, rid=os.path.basename(path), tag=tag)

def transcribe(path, s0, s1):
    """basic-pitch (ONNX) で採譜: [(秒, 長さ, 音高, 強さ)]"""
    cache = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bp_cache'); os.makedirs(cache, exist_ok=True)
    key = os.path.join(cache, '%s_%d_%d.json' % (os.path.basename(path), int(s0 * 10), int(s1 * 10)))
    if os.path.exists(key): return json.load(open(key))
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    y, sr = sf.read(path); tmp = key.replace('.json', '.wav'); sf.write(tmp, y[int(s0 * sr):int(s1 * sr)], sr)
    _, _, ev = predict(tmp, os.path.join(os.path.dirname(str(ICASSP_2022_MODEL_PATH)), 'nmp.onnx'), onset_threshold=0.55, frame_threshold=0.35, minimum_note_length=80)
    os.remove(tmp)
    out = [(float(a), float(b - a), int(m), float(v)) for a, b, m, v, *_ in ev if v >= 0.3 and 24 <= m <= 103]
    json.dump(out, open(key, 'w')); return out

def playable(notes, poly=7):
    """同じ高さの重なりを 1 つに、同時の打鍵は 7 つまで、強さを抜粋の中でならす"""
    notes = sorted(notes); out, last = [], {}
    for t, dd, m, v in notes:
        j = last.get(m)
        if j is not None and out[j][0] + 0.06 > t: out[j][3] = max(out[j][3], v); continue
        if j is not None and out[j][0] + out[j][1] > t: out[j][1] = max(0.08, t - out[j][0])
        last[m] = len(out); out.append([t, dd, m, v])
    res, i = [], 0
    while i < len(out):
        grp = [out[i]]; i += 1
        while i < len(out) and out[i][0] - grp[0][0] < 0.04: grp.append(out[i]); i += 1
        if len(grp) > poly:
            ms = sorted(grp, key=lambda x: x[2]); grp = [ms[0], ms[-1]] + sorted(ms[1:-1], key=lambda x: -x[3])[:poly - 2]
        res += grp
    medv = float(np.median([x[3] for x in res])) + 1e-9 if res else 1.0
    return [(t, dd, m, float(np.clip(v / medv, 0.55, 1.5))) for t, dd, m, v in res]

def rid_for(m): return VOICE_SRC['S'] if m >= 72 else VOICE_SRC['A'] if m >= 60 else VOICE_SRC['T'] if m >= 48 else VOICE_SRC['B']

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': [TH], 'piano_decay': 1.8, 'reverb': [4.8, 1.7, 0.42],
    'title': 'Requiem BADA — LXX · Requiem 08:06',
    'subtitle': '9/23 08:06 の録音を主題曲に、16 倍に伸ばし、LXIX をバックに — フーガを醸すレクイエム (変ロ短調、♩=60)',
    'legend': ['PF'], 'vname': {'PF': 'ピアノ'},
    'footer': ['Introitus (08:06) → I. Requiem ×16 → II. Fuga (08:06 の主題) → III. Lacrimosa (08:06) → IV. Finale ×16 con Fuga → Amen (変ロ長調)',
               '主題曲は 9/23 08:06 の録音。バックは LXIX を 6 半音下げてピアノで弾き直したもの。すべてピアノの実音。'],
}

if __name__ == '__main__':
    compose.main(OUT, seed=170, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(OUT)
    K.BPM = BPM; K.fix_voices(OUT)
    d = json.load(open(OUT)); from collections import Counter
    for n_ in d['notes']:
        lab = n_.get('label') or ''
        n_['dyn'] = round(n_.get('dyn', 1.0) * (1.4 if n_['v'] in 'SA' and (lab.startswith('主題') or lab.startswith('答え')) else 1.25), 4)
    LXV.SWELL[:] = LXIX.SWELL; LXV.swell(d); LXII.fix_pulse(d)
    bt = d['bar_times']; l69 = os.path.join(SRC, 'tablet69.wav')
    for w, (b0, n_, off, tag) in enumerate(BACK):
        t0 = bt[b0]; dur = n_ * BPB * 60.0 / BPM + 1.0
        notes = playable([(t, dd, m + BACK_SEMIS, v) for t, dd, m, v in transcribe(l69, off, off + dur)])
        d['extras'].append(dict(v='REC', t=t0, d=dur, beat=b0 * BPB, dbeats=dur, m=0, gain=0.0, src=l69, off=off, fin=0.1, fout=0.5,
                                rid='tablet69.wav', tag='%s → 6 半音下げてピアノで' % tag, label=None))
        for t, dd, m, v in notes:
            d['extras'].append(dict(v='PF', t=round(t0 + t, 4), d=round(max(0.12, dd), 4), beat=round(t0 + t, 4), dbeats=round(dd, 4),
                                    m=int(m), gain=round(0.18 * v, 4), rid=rid_for(m), rel=0.45, label=None, win=w))
        print('back %d  %-40s notes %d' % (w, tag[:40], len(notes)))
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', Counter(x['v'] for x in d['notes']), 'duration', round(d['duration'], 1))
    print('sections:', [(round(s['t']), s['title'][:24]) for s in d['sections']])
