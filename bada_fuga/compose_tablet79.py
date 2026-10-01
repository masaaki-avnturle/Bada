#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXXIX · Impossibile XVI (LXXVIII を折りたたんで重低音の土台に、9/24 08:53 を主題に、9/29 の 2 曲を伴奏に — 16 倍の、弾くことのできない洗脳的な曲)
  土台 (重低音): LXXVIII を折りたたむ — 第 1 部 (ホ短調) と第 2 部 (ヘ短調 → 1 半音下げてホ短調) を重ね、1 オクターヴ下げて、低い音 (ソ 3 まで) だけを残す。
    これを 2 回 (192 秒 × 2)。重ねた重低音の根音・16 倍の主題・8 倍の共鳴が、暗く深い土台になる。
  主題: 9/24 08:53 (ミ・ファ#・シ・ミ・ミ) を 1 倍・4 倍・8 倍・16 倍で同時に — 1 人のピアニストには弾けない (不可能な) 重なり:
    ×16 (ミ 4〜ミ 5、4 拍ごとに打ち直す、2 分 8 秒で 1 回り、3 回) / ×8 (ミ 3〜ミ 4、4 拍ごと) / ×4 (上の音域、打ち直さない) / ×1 (上の音域、32 秒に 1 回、遠く)
  伴奏: 9/29 15:12 と 15:16 の録音の一節 (16 秒) を採譜し、6 半音下げて (変ロ短調 → ホ短調)、リズムを 2 倍に伸ばし、音を間引いて (同時に 3 音まで) ループする —
    前半は 15:12、後半は 15:16。
  雰囲気は piano_solo_8x のように: 1 秒に 1〜2 打ほどのまばらな打鍵、暗い音域 (いちばん上はシ 5)、長い響き (残響 7.5 秒・ピアノの減衰を長く)。
  形式 (♩=60, ホ短調): Introitus (08:53 の実音) → 土台 1 回目 (伴奏 15:12) → 土台 2 回目 (伴奏 15:16) → 終わり (ミの重低音とホ長調の和音)
  すべてピアノの実音。シンセ・ドラムなし。
  使い方: python compose_tablet79.py <bank74.json> <score_tablet78.json> <録音の wav フォルダ (bank74)> [score_tablet79.json]
"""
import sys, os, json
import numpy as np, soundfile as sf
from compose import name_of

BANK, SRC78, WAV = sys.argv[1], json.load(open(sys.argv[2])), os.path.abspath(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet79.json'
import compose_tablet as CT                         # (sys.argv[1] の bank を読む)
import compose_tablet63 as LXIII
R53, R12, R16 = '20260924_085314', '20260929_151249', '20260929_151602'
INTRO, FOLD = 24.0, 192.0
P1, P2 = (32.0, 224.0, 0), (248.0, 440.0, -1)       # LXXVIII の第 1 部・第 2 部 (と移調)
ACC = [(R12, 67.0), (R16, 7.7)]                     # 伴奏にする一節の開始秒
ACCG = {R12: 0.11, R16: 0.06}                       # 伴奏の大きさ (15:16 の一節は音が多いので小さく)

def pf(t, d, m, g, rid, layer, rel=1.0):
    return dict(v='PF', t=round(t, 3), d=round(d, 3), m=int(m), gain=round(g, 5), rid=rid, rel=rel, beat=round(t, 3), dbeats=round(d, 3), label=None, layer=layer)

def fold(T0):
    """LXXVIII の 2 つの部を重ねて 1 オクターヴ下げ、低い音だけ (ソ 3 まで) — 同じ時刻・同じ音は 1 つに"""
    out, seen = [], set()
    for a0, a1, semis in (P1, P2):
        for e in SRC78['extras']:
            if e['v'] != 'PF' or not (a0 - 1e-3 <= e['t'] < a1 - 1e-3): continue
            m = e['m'] + semis - 12
            if m > 55 or m < 24: continue
            t = round(e['t'] - a0 + T0, 2); key = (t, m)
            if key in seen: continue
            seen.add(key); out.append(pf(t, e['d'] * 1.3, m, e['gain'] * 0.44, e.get('rid', ''), 'fold', rel=1.4))
    return out

def subject(rid, semis):
    t0, inside = CT.excerpt(rid, semis, 13.0)
    return LXIII.smooth(CT.make_subject(inside, semis, 60))

def place_theme(out, T0, s_, k, lo, g, step, layer, rid=R53, cap=83):
    """主題を k 倍で: 主題全体をオクターヴで動かして、いちばん低い音を lo〜lo+11 に (形はそのまま、上はシ 5 まで)。step 拍ごとに打ち直す (None なら 1 打)"""
    sh = 12 * int(np.ceil((lo - min(m for _, m in s_)) / 12.0))
    while max(m for _, m in s_) + sh > cap: sh -= 12
    t = T0
    for d, m in s_:
        L = d * k; n_ = 1 if step is None else max(1, int(round(L / step)))
        for i in range(n_):
            a = t + (0 if step is None else i * step); dd = L if step is None else step
            amp = 1.0 if i == 0 else 0.6 + 0.25 * np.sin(np.pi * i / max(1, n_ - 1))
            out.append(pf(a, dd + 1.0, m + sh, g * amp, rid, layer, rel=1.2))
        t += L

def transcribe(path, s0, s1):
    cache = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bp_cache'); os.makedirs(cache, exist_ok=True)
    key = os.path.join(cache, '%s_%d_%d.json' % (os.path.basename(path), int(s0 * 10), int(s1 * 10)))
    if os.path.exists(key): return json.load(open(key))
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    y, sr = sf.read(path); tmp = key.replace('.json', '.wav'); sf.write(tmp, y[int(s0 * sr):int(s1 * sr)], sr)
    _, _, ev = predict(tmp, os.path.join(os.path.dirname(str(ICASSP_2022_MODEL_PATH)), 'nmp.onnx'), onset_threshold=0.55, frame_threshold=0.35, minimum_note_length=80)
    os.remove(tmp)
    res = [(float(a), float(b - a), int(m), float(v)) for a, b, m, v, *_ in ev if v >= 0.3 and 24 <= m <= 103]
    json.dump(res, open(key, 'w')); return res

def accompaniment(out, T0, L, rid, off):
    """9/29 の一節を 6 半音下げ、リズムを 2 倍に、同時に 3 音まで・0.5 秒より詰めない — ループして L 秒"""
    ev = sorted(transcribe(os.path.join(WAV, rid + '.wav'), off, off + 16.0))
    notes, last_t = [], -9
    groups = {}
    for t, d, m, v in ev: groups.setdefault(round(t / 0.06), []).append((t, d, m, v))
    for k in sorted(groups):
        g = sorted(groups[k], key=lambda x: -x[3])[:3]
        if g[0][0] - last_t < 0.5: continue
        last_t = g[0][0]; notes += g
    loop = 32.0; vmed = float(np.median([n[3] for n in notes])) + 1e-9
    for r in range(int(L // loop)):
        for t, d, m, v in notes:
            mm = m - 6
            while mm > 74: mm -= 12
            while mm < 48: mm += 12
            out.append(pf(T0 + r * loop + t * 2, d * 2 + 0.8, mm, ACCG[rid] * float(np.clip(v / vmed, 0.6, 1.4)), rid, 'acc', rel=1.0))

def main():
    out = dict(bpm=60, beats_per_bar=4, notes=[], extras=[], entries=[], sections=[], harm=[])
    s_ = [(d, m + 2) for d, m in subject(R53, 2)]                                          # ホ短調: ミ・ファ#・シ・ミ・ミ
    print('theme', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    T = 0.0
    out['sections'].append(dict(t=0.0, title='Introitus — 主題曲 9/24 08:53 の実音 (ホ短調)', sub='主題曲 (ピアノの実音) から始まる'))
    out['extras'].append(dict(v='REC', t=0.0, d=INTRO + 1.0, beat=0.0, dbeats=INTRO + 1.0, m=0, gain=0.28, src=os.path.join(WAV, R53 + '.wav'), off=30.0,
                              fin=2.0, fout=4.0, rid=R53 + '.wav', tag='主題曲 9/24 08:53', label=None))
    out['harm'] += ['Em'] * int(INTRO); T = INTRO
    body = 2 * FOLD
    for c, (rid, off) in enumerate(ACC):
        out['sections'].append(dict(t=T + c * FOLD, title='%s — 折りたたんだ重低音の土台 + 主題 ×1・×4・×8・×16 (ホ短調)' % ('I' if c == 0 else 'II'),
                                    sub='LXXVIII を折りたたんだ重低音、9/24 08:53 の主題を 4 つの速さで同時に、伴奏は 9/29 %s:%s の一節 (6 半音下げ・2 倍の長さ)' % (rid[9:11], rid[11:13])))
        out['extras'] += fold(T + c * FOLD)
        accompaniment(out['extras'], T + c * FOLD, FOLD, rid, off)
        out['entries'].append(dict(t=T + c * FOLD + 0.03, label='伴奏 — 9/29 %s:%s' % (rid[9:11], rid[11:13]), v='A'))
    for r in range(3): place_theme(out['extras'], T + r * 128.0, s_, 16, 64, 0.43, 4.0, 'x16')                 # ×16
    for r in range(6): place_theme(out['extras'], T + r * 64.0, s_, 8, 52, 0.22, 4.0, 'x8')                   # ×8
    for r in range(12): place_theme(out['extras'], T + r * 32.0, s_, 4, 76, 0.12, None, 'x4', cap=88)                 # ×4
    for r in range(12): place_theme(out['extras'], T + r * 32.0 + 16.0, s_, 1, 76, 0.1, None, 'x1', cap=88)           # ×1
    out['entries'] += [dict(t=T, label='主題 ×16 (9/24 08:53)', v='S'), dict(t=T + 0.01, label='×8', v='T'), dict(t=T + 0.02, label='×4', v='B'),
                       dict(t=T + 16.0, label='×1', v='S')]
    H = [h for h in SRC78['harm'][int(P1[0]):int(P1[1])]]
    out['harm'] += (H + H)[:int(body)]; T += body
    out['sections'].append(dict(t=T, title='終わり — ミの重低音とホ長調の和音', sub='4 つの速さの主題がそろってミに着き、ホ長調の和音が長く響いて消える'))
    for m, g in ((28, 0.36), (40, 0.26), (52, 0.16), (56, 0.15), (59, 0.14), (64, 0.13)):
        for i in range(4): out['extras'].append(pf(T + 4 * i, 5.0, m, g * (1 - 0.22 * i), R53, 'coda', rel=1.6))
    out['harm'] += ['E'] * 16; T += 16.0
    out['duration'] = round(T, 3); out['nbars'] = int(round(T / 4.0)); out['bar_times'] = [4.0 * i for i in range(out['nbars'] + 1)]
    out['meta'] = {k: v for k, v in SRC78['meta'].items() if k not in ('title', 'subtitle', 'footer', 'bank')}
    out['meta'].update(bank=BANK, piano_decay=3.0, reverb=[7.5, 2.8, 0.55], rec_order=[R53, R12, R16] + [r for r in SRC78['meta'].get('rec_order', []) if r not in (R53, R12, R16)],
        title='Requiem BADA — LXXIX · Impossibile XVI',
        subtitle='折りたたんだ LXXVIII の重低音に、9/24 08:53 の主題を 1・4・8・16 倍で同時に — 弾けない洗脳的な曲',
        legend=['PF'], vname={'PF': 'ピアノ'},
        footer=['Introitus (08:53) → I. 土台 + 主題 ×1・×4・×8・×16 + 伴奏 15:12 → II. 同 + 伴奏 15:16 → 終わり (ホ長調)',
                '雰囲気は piano_solo_8x のように、まばらで暗く長い響き。すべてピアノの実音。'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    pfs = [e for e in out['extras'] if e['v'] == 'PF']; ms = [e['m'] for e in pfs]
    from collections import Counter
    on = len({round(e['t'], 1) for e in pfs}) / T
    print('duration %.0f s (%d:%02d)  range %s..%s (%.1f oct)  onsets/s %.2f  layers %s' % (T, T // 60, T % 60, name_of(min(ms)), name_of(max(ms)),
          (max(ms) - min(ms)) / 12, on, dict(Counter(e.get('layer') for e in pfs))))

if __name__ == '__main__':
    main()
