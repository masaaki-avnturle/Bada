#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXVII · Symphonia per augmentationem (Klavier) (LXVI を、すべて実音のピアノで弾いているように)
  楽譜・形式・骨組み (主題を 4 倍・8 倍・16 倍に伸ばして打ち直す) は LXVI とまったく同じ。
  LXVI で mp4 の音のまま流していた 20 の抜粋を、ピアノの実音 (録音から切り出した 1 音、bank61) で弾き直す:
    - このリポジトリで作った曲 (symphony・acceptance・tablet・tablet6・tablet46/48/49inst・tablet60/61/62・LXV …) は、もとの楽譜の音をそのまま使う —
      4 声と、音の高さのある楽器 (弦・管・シンセ・オルガン・ピアノ) をすべてピアノで。ドラム・ティンパニ・心臓の鼓動・808 のベースは外す
    - その曲の中で流れていた「わたしの録音の実音」は、もともとピアノの実音なのでそのまま (調をテープで動かしていた所は、その採譜をピアノで)
    - その曲の中で流れていた別の mp4 の音 (LXV の中の tablet4 など) は、さらにその曲の楽譜までたどってピアノで
    - 楽譜のない 6 曲 (cp14_C_G_uplift・cp14_x8_part3・piano_solo_8x・requiem_fuga_drill/embrace/small) は、音から採譜 (basic-pitch) してピアノで
    - 同じ高さの重なった音は 1 つに、同時に鳴らす音は 7 つまで (両手で弾ける厚さに)、抜粋ごとの大きさをそろえる
  調を合わせるときは、テープのように速さを変えず、音の高さだけを動かす (ピアノで弾き直すので)。
  使い方:
    python compose_tablet67.py <bank61.json> <素材の wav フォルダ> <sources.json> [score_tablet67.json]
      sources.json: {"symphony.wav": {"score": "…/score_symphony.json"}, "cp14_x8_part3.wav": {"transcribe": true}, …}
    python compose_tablet67.py level <score_tablet67.json> <ピアノに直した所だけの wav> <その wav を書いたとき synth.py が表示した peak> [大きさ, 既定 0.07]   (抜粋ごとの大きさをそろえる、2 回目)
"""
import sys, os, re, json
import numpy as np

PITCHED = {'V1', 'V2', 'VA', 'VC', 'CB', 'CBP', 'PF', 'OS', 'DN', 'H', 'W', 'L', 'C', 'FL', 'WW', 'CL', 'HN', 'TR', 'BN', 'EP', 'PD', 'LD',
           'SY', 'SB', 'CG', 'EB', 'LG', 'DG', 'OU', 'GT', 'AR', 'GL', 'RS', 'RL', 'SP', 'VN', 'BV'}
REAL = re.compile(r'\d{8}_\d{6}\.wav$')
TARGET = 0.07                                      # 抜粋の大きさ (LXVI の mp4 の抜粋と同じくらい)

if len(sys.argv) > 1 and sys.argv[1] == 'level':
    import soundfile as sf
    score, stem = sys.argv[2], sys.argv[3]
    d = json.load(open(score)); y, sr = sf.read(stem); y = y.mean(1) if y.ndim > 1 else y
    # synth.py は書き出す前に正規化するので、表示した peak (正規化の前の大きさ) で元に戻す。ない時は書き出した wav の最大値 (相対の比べだけ正しい)
    peak = float(sys.argv[4]) if len(sys.argv) > 4 else float(np.abs(y).max())
    if len(sys.argv) > 5: TARGET = float(sys.argv[5])                 # 抜粋の大きさ (バックとして小さくしたい時など)
    y = np.arctanh(np.clip(y * np.tanh(1.15), -.999, .999)) / 1.15 / .89 * peak
    wins = {}
    for e in d['extras']:
        if 'win' in e: wins.setdefault(e['win'], []).append(e)
    for w, es in sorted(wins.items()):
        t0 = min(e['t'] for e in es); t1 = max(e['t'] + e['d'] for e in es)
        r = float(np.sqrt((y[int(t0 * sr):int(t1 * sr)] ** 2).mean())) + 1e-9
        k = float(np.clip(TARGET / r, 0.25, 4.0))
        for e in es: e['gain'] = round(e['gain'] * k, 5)
        print('window %2d  %5.0f-%5.0f s  rms %.3f  x%.2f' % (w, t0, t1, r, k))
    json.dump(d, open(score, 'w'), ensure_ascii=False)
    sys.exit(0)

import compose
import compose_tablet as CT
import compose_tablet48 as K
import compose_tablet62 as LXII
import compose_tablet65 as LXV
import compose_tablet66 as LXVI
from compose import BPB

SRC = LXVI.SRC
SOURCES = json.load(open(sys.argv[3]))
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet67.json'
CACHE = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bp_cache')
_SC = {}

def score_of(name):
    if name not in _SC: _SC[name] = json.load(open(SOURCES[name]['score']))
    return _SC[name]

def transcribe(name, s0, s1):
    """basic-pitch (ONNX) で抜粋を採譜: [(秒, 長さ, 音高, 強さ)]"""
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, '%s_%d_%d.json' % (name, int(s0 * 10), int(s1 * 10)))
    if os.path.exists(key): return json.load(open(key))
    import soundfile as sf
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    model = os.path.join(os.path.dirname(str(ICASSP_2022_MODEL_PATH)), 'nmp.onnx')
    y, sr = sf.read(os.path.join(SRC, name)); tmp = key.replace('.json', '.wav')
    sf.write(tmp, y[int(s0 * sr):int(s1 * sr)], sr)
    _, _, ev = predict(tmp, model, onset_threshold=0.55, frame_threshold=0.35, minimum_note_length=80)
    os.remove(tmp)
    out = [(float(a), float(b - a), int(m), float(v)) for a, b, m, v, *_ in ev if v >= 0.3 and 24 <= m <= 103]
    json.dump(out, open(key, 'w')); return out

def convert(name, s0, s1, semis, tscale=1.0, keep_real=True):
    """曲 name の [s0, s1) 秒を、ピアノの音 [(出力の秒, 長さ, 音高, 強さ)] と、そのまま流す実音の録音 [REC] に直す (時刻は s0 から、tscale で伸ばす)"""
    notes, recs = [], []
    if SOURCES[name].get('transcribe'):
        for t, dd, m, v in transcribe(name, s0, s1): notes.append((t / tscale, dd / tscale, m + semis, v))
        return notes, recs
    d = score_of(name); style = d['meta'].get('style', '')
    med = {}
    for e in d.get('extras', []): med.setdefault(e['v'], []).append(e.get('gain', 0.3))
    med = {v: float(np.median(g)) + 1e-9 for v, g in med.items()}
    def take(t, dd, m, v):
        if t + dd <= s0 + 0.3 or t >= s1: return
        if t < s0:                                                   # 抜粋の頭より前から鳴っている音は、残りが長いときだけ頭で弾き直す
            if t + dd - s0 < 0.6: return
            dd -= s0 - t; t = s0
        notes.append(((t - s0) / tscale, min(dd, s1 - t) / tscale, m + semis, v))
    for n in d['notes']: take(n['t'], n['d'], n['m'], float(n.get('dyn', 1.0)))
    pitched = PITCHED | ({'TB'} if style != 'recsampler' else set())
    for e in d.get('extras', []):
        if e['v'] in pitched: take(e['t'], e['d'], e['m'], e.get('gain', 0.3) / med[e['v']])
    for e in d.get('extras', []):
        if e['v'] != 'REC': continue
        a, b = max(e['t'], s0), min(e['t'] + e['d'], s1)
        if b - a < 0.5: continue
        base = os.path.basename(e['src']); r2 = 2 ** (e.get('semis', 0) / 12.0)
        if REAL.search(base):
            if keep_real and semis == 0:                             # わたしの録音の実音: そのまま
                recs.append(dict(t=(a - s0) / tscale, d=(b - a) / tscale, src=e['src'], off=e['off'] + (a - e['t']) * r2, gain=e.get('gain', 0.5),
                                 fin=0.3, fout=min(1.5, (b - a) / 4), rid=e.get('rid', ''), **({'semis': e['semis']} if e.get('semis') else {})))
            elif style == 'recsampler':                              # 調を動かす所は、その採譜をピアノで
                for x in d['extras']:
                    if x['v'] == 'TB': take(x['t'], x['d'], x['m'], 0.9) if a <= x['t'] < b else None
        elif base in SOURCES:                                        # 別の mp4 の音: その曲の楽譜 (または採譜) までたどる
            q0 = e['off'] + (a - e['t']) * r2; q1 = e['off'] + (b - e['t']) * r2
            sub, _ = convert(base, q0, q1, semis + e.get('semis', 0), tscale * r2, keep_real=False)
            notes += [((a - s0) / tscale + t, dd, m, v) for t, dd, m, v in sub]
    return notes, recs

def playable(notes, poly=7):
    """同じ高さの重なりを 1 つに、同時の打鍵は 7 つまで (外声と強い音を残す)、強さを抜粋の中でならす"""
    notes = sorted(notes)
    out, last = [], {}
    for t, dd, m, v in notes:
        j = last.get(m)
        if j is not None and out[j][0] + 0.06 > t: out[j][3] = max(out[j][3], v); continue      # ほぼ同時の同じ音
        if j is not None and out[j][0] + out[j][1] > t: out[j][1] = max(0.08, t - out[j][0])   # 前の同じ音は、次の打鍵の前で止める
        last[m] = len(out); out.append([t, dd, m, v])
    res, i = [], 0
    while i < len(out):
        grp = [out[i]]; i += 1
        while i < len(out) and out[i][0] - grp[0][0] < 0.04: grp.append(out[i]); i += 1
        if len(grp) > poly:
            ms = sorted(grp, key=lambda x: x[2]); keep = [ms[0], ms[-1]]
            keep += sorted(ms[1:-1], key=lambda x: -x[3])[:poly - 2]; grp = keep
        res += grp
    vs = np.array([x[3] for x in res]) if res else np.array([1.0])
    medv = float(np.median(vs)) + 1e-9
    return [(t, dd, m, float(np.clip(v / medv, 0.55, 1.5))) for t, dd, m, v in res]

def rid_for(m):
    vs = LXVI.VOICE_SRC
    return vs['S'] if m >= 72 else vs['A'] if m >= 60 else vs['T'] if m >= 48 else vs['B']

META = dict(LXVI.META,
    title='Requiem BADA — LXVII · Symphonia (Klavier)',
    subtitle='LXVI を、すべて実音のピアノで — 提出した 16 曲もピアノで弾き直した洗脳的な交響曲 (4 楽章、♩=60)',
    legend=['PF'], vname={'PF': 'ピアノ'},
    footer=['I. ニ短調 ×4 → II. Adagio ホ短調 ×4 → III. Scherzo ハ長調 ×8 → IV. Finale ニ短調 ×16 con Fuga → Coda ニ長調',
            '提出した曲は、楽譜 (または採譜) の音をピアノの実音で弾き直した。わたしの録音の実音はそのまま。シンセ・ドラムなし。'])

def post(P, events, extras):
    LXVI.LXIII.post(P, events, extras)            # 分散和音 (ピアノ)。mp4 の音は流さない (あとでピアノの音に置き換える)

if __name__ == '__main__':
    compose.main(OUT, seed=166, bpm=LXVI.BPM, builder=LXVI.build, meta=META, extras=CT.extras, post=post)
    CT.finish(OUT)
    K.BPM = LXVI.BPM; K.fix_voices(OUT)
    d = json.load(open(OUT)); from collections import Counter
    for n_ in d['notes']: n_['dyn'] = round(n_.get('dyn', 1.0) * 1.25, 4)
    LXV.SWELL[:] = LXVI.SWELL; LXV.swell(d); LXII.fix_pulse(d)
    bt = d['bar_times']
    for w, (b0, n_, src, off, semis, g, tag, fout) in enumerate(LXVI.AUD):
        t0 = bt[b0]; dur = n_ * BPB * 60.0 / LXVI.BPM + 1.0
        notes, recs = convert(src, off, off + dur, semis)
        notes = playable(notes)
        d['extras'].append(dict(v='REC', t=t0, d=dur, beat=b0 * BPB, dbeats=dur, m=0, gain=0.0, src=os.path.join(SRC, src), off=off, fin=0.1, fout=0.5,
                                rid=src, tag='%s → 実音のピアノで' % tag, label=None))        # 表示だけ (音は鳴らさない)
        for t, dd, m, v in notes:
            d['extras'].append(dict(v='PF', t=round(t0 + t, 4), d=round(max(0.12, dd), 4), beat=round((t0 + t) / 60.0 * LXVI.BPM, 4), dbeats=round(dd, 4),
                                    m=int(m), gain=round(0.22 * v, 4), rid=rid_for(m), rel=0.45, label=None, win=w))
        for r in recs:
            r.update(v='REC', t=round(t0 + r['t'], 4), beat=round((t0 + r['t']) / 60.0 * LXVI.BPM, 4), dbeats=r['d'], m=0, label=None, win=w, tag='%s — わたしの録音の実音' % tag)
            d['extras'].append(r)
        print('window %2d %-28s notes %4d  real recordings %d' % (w, src[:28], len(notes), len(recs)))
    for sec in d['sections']: sec['sub'] = sec['sub'].replace('の音のまま', 'を実音のピアノで')
    json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']), 'duration', round(d['duration'], 1))
