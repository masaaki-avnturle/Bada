#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions (実録音のレクイエムとフーガ)
  作曲者のタブレット録音 5 本 (2026-09-22 17:48 / 17:57 / 17:59, 09-23 08:06 / 08:09) を、レクイエムとフーガにしたため、
  実録音の音で再現して、最後に全部の曲を合わせる。
    - 各区間 (録音順に 5 つ): 録音の実音の抜粋 → その抜粋の最上声から作った主題の 4 声フーガ (提示 + 結尾)
      → その抜粋の和音進行による 4 声のレクイエム・コラール。調は録音の調 (ロ短調 / ホ短調 / 変ロ短調)
    - 音はすべて実録音: 4 声は録音から切り出した 1 音 (build_sampler.py) を移調して鳴らすサンプラー。
      各区間はその録音の音で (1 音が少ない録音は近い音高の他の録音の音を借りる)
    - 終曲: 5 つの主題が 1 小節おきに重なって入る「5 つの主題のフーガ」— 各主題は自分の録音の音で鳴る
      → B-A-D-A → ピカルディ終止 → 最初の録音の実音の終わりで閉じる
  使い方: python compose_tablet.py <bank.json> [score_tablet.json]
"""
import sys, json, math
from compose import *
import compose
import compose_heart as H

BANK = json.load(open(sys.argv[1]))
REC = BANK['recordings']
# (録音 id, 調への移調 (ニ短調から), 調の名前, ♩)
SECS = [('20260922_174820', -3, 'ロ短調', 72), ('20260922_175717', -3, 'ロ短調', 66), ('20260922_175951', 2, 'ホ短調 (ト長調の平行調)', 80),
        ('20260923_080607', -4, '変ロ短調', 72), ('20260923_080918', 2, 'ホ短調 (ト長調の平行調)', 76)]
FINAL_SEMIS, FINAL_BPM = -3, 66
VOICE_SRC_FINAL = {'S': '20260923_080918', 'A': '20260922_175951', 'T': '20260922_174820', 'B': '20260923_080607'}
MARK = '①②③④⑤'
DMIN = [2, 4, 5, 7, 9, 10, 1]                       # ニ短調 (和声的短音階)
CANDS = ['Dm', 'Gm', 'A', 'A7', 'F', 'Bb', 'C', 'Em7b5', 'Gm/Bb', 'Dm/F']
extras = []
LAYOUT = []                                          # (開始小節, 終了小節, 移調, 声部→録音, 主題ラベル→録音)

# 抜粋の音量 (実音とサンプラーのフーガが同じくらいの大きさで聞こえるよう、録音ごとに測って合わせた値)
REC_GAIN = {'20260922_174820': 1.2, '20260922_175717': 1.0, '20260922_175951': 1.8, '20260923_080607': 1.35, '20260923_080918': 1.15}

def add(v, beat, dbeats, midi, gain, label=None, **kw):
    e = {'v': v, 'beat': beat, 'dbeats': dbeats, 'm': midi, 'gain': gain, 'label': label}
    e.update(kw); extras.append(e)
def root_pc(lab):
    i = 2 if len(lab) > 1 and lab[1] in '#b' else 1
    return PC[lab[:i]]
def hm(s): return '%s:%s' % (s[9:11], s[11:13])

def excerpt(rid, semis, seconds):
    """抜粋: 3 秒以降で主和音 (またはその sus) から始まる最初の打鍵から seconds 秒 (打鍵の切れ目まで)"""
    segs = REC[rid]['segs']; tonic = (2 + semis) % 12
    start = next((s for s in segs if s['t'] >= 3 and root_pc(s['ch']) == tonic and s['d'] >= 0.4), None)
    if start is None: start = max(segs[:len(segs) // 2], key=lambda s: s['d'])
    t0 = start['t'] - 0.03
    inside = [s for s in segs if t0 <= s['t'] < t0 + seconds]
    return t0, inside

def make_subject(inside, semis, bpm):
    """抜粋の最上声 → 8 拍の主題 (ニ短調に移し、音階に寄せ、主音で終える)"""
    tops = []
    for s in inside:
        m = s['m'][-1] - semis
        if tops and tops[-1][1] % 12 == m % 12: tops[-1][0] += s['d']; continue
        tops.append([s['d'], m])
    out, beats, prev = [], 0.0, 67
    for d, m in tops[:9]:
        q = min((0.5, 1, 1.5, 2, 3), key=lambda x: abs(x - d * bpm / 60.0))
        if beats + q > 8: q = 8 - beats
        if q <= 0: break
        m = min((m + 12 * k for k in range(-3, 4)), key=lambda x: abs(x - prev) + (6 if not 60 <= x <= 76 else 0))
        m = min((x for x in range(m - 2, m + 3) if x % 12 in DMIN), key=lambda x: abs(x - m))
        out.append([q, m]); beats += q; prev = m
    if not out: out = [[8, 62]]
    out[0][1] = min((x for x in range(out[0][1] - 5, out[0][1] + 6) if x % 12 in (2, 5, 9)), key=lambda x: abs(x - out[0][1]))
    if beats < 8: out.append([8 - beats, 62])
    last = out[-1]; last[1] = min((x for x in (62, 74)), key=lambda x: abs(x - last[1]))
    if last[0] < 1 and len(out) > 1:                   # 最後は 1 拍以上の主音に
        out[-2][0] -= 1 - last[0]; last[0] = 1
        if out[-2][0] <= 0: out.pop(-2)
    return [(d, m) for d, m in out]

def harmonize(subj):
    """主題に和声: 半小節ごとに、主題の音を最も多く和音構成音にする候補を選ぶ (はじめは主和音、終わりは主和音へ)"""
    spans, t = [], 0.0
    for d, m in subj: spans.append((t, t + d, m)); t += d
    out = []
    for h in range(4):
        a, b = 2 * h, 2 * h + 2
        def score(cs):
            c = chord(cs); sc = 0.0
            for s0, s1, m in spans:
                ov = min(b, s1) - max(a, s0)
                if ov <= 0: continue
                w = ov * (2.0 if a <= s0 < a + 0.01 or (s0 < a < s1) else 1.0)
                sc += w * (1.0 if m % 12 in c['pcs'] else -0.7)
            return sc + (0.6 if (h in (0, 3) and cs == 'Dm') else 0) + (0.3 if h == 2 and cs in ('A', 'A7') else 0)
        out.append(max(CANDS, key=score))
    return [[out[0], out[0], out[1], out[1]], [out[2], out[2], out[3], out[3]]]

def rec_chords(inside, semis):
    labs = []
    for s in inside:
        lab = transpose_h([[s['ch']]], -semis)[0][0]
        if not labs or labs[-1] != lab: labs.append(lab)
    labs = (labs + ['Dm'] * 8)[:8]
    return [[labs[2 * i], labs[2 * i], labs[2 * i + 1], labs[2 * i + 1]] for i in range(4)]

SUBJ = []

def build():
    plan = []
    for rid, semis, kname, bpm in SECS:
        bar_s = 240.0 / bpm; E = max(5, round(20.0 / bar_s))
        t0, inside = excerpt(rid, semis, E * bar_s)
        subj = make_subject(inside, semis, bpm)
        SUBJ.append((rid, subj, harmonize(subj)))
        plan.append((rid, semis, kname, bpm, E, t0, inside, subj))
    total = sum(p[4] + 14 for p in plan) + 20
    P = Piece(total); b = 0
    for i, (rid, semis, kname, bpm, E, t0, inside, subj) in enumerate(plan):
        s0 = b; bar_s = 240.0 / bpm
        for k in range(E + 14): P.tempo[b + k] = bpm; P.dyn[b + k] = 0.8
        # 録音の実音の抜粋 (4 声は休む。採譜した音は表示用)
        P.section(b, '%s 録音 %s — 実音' % (MARK[i], hm(rid)), '%s · ♩=%d ／ タブレット録音 20260922_%s の実音の抜粋 (%.0f 秒)' % (kname, bpm, rid[9:], E * bar_s) if rid.startswith('20260922') else
                  '%s · ♩=%d ／ タブレット録音 %s の実音の抜粋 (%.0f 秒)' % (kname, bpm, rid, E * bar_s))
        for v in VOICES: P.rest_bars(v, b, b + E)
        add('REC', b * BPB, E * BPB + 1.5, 0, REC_GAIN.get(rid, 1.3), None, src=REC[rid]['file'], off=t0, rid=rid)
        for s in inside:
            for m in s['m']: add('TB', b * BPB + (s['t'] - t0) * bpm / 60.0, s['d'] * bpm / 60.0, m - semis, 0.0, None)
        for k in range(E * BPB):
            tt = t0 + k * 60.0 / bpm; cur = None
            for s in inside:
                if s['t'] <= tt + 0.05: cur = s
            if cur: P.harm[b * BPB + k] = transpose_h([[cur['ch']]], -semis)[0][0]
        b += E
        # 抜粋の最上声から作った主題の 4 声フーガ (提示: A → S 答唱 → B → T 答唱 → 結尾)
        H_sub = SUBJ[i][2]; lab = '主題 %s (%s)' % (MARK[i], hm(rid))
        P.section(b, '%s Fuga — 主題 %s 〈録音 %s〉' % (MARK[i], MARK[i], hm(rid)), '抜粋の最上声から作った主題の 4 声フーガ — 4 声とも録音 %s の実音 (サンプラー)' % hm(rid))
        P.set_harms(b, H_sub); P.place('A', b, subj, 0, lab);
        for v in 'STB': P.rest_bars(v, b, b + 2)
        P.set_harms(b + 2, transpose_h(H_sub, 7)); P.place('S', b + 2, subj, 7 + 12 if max(m for _, m in subj) + 7 < 72 else 7, lab + ' 答唱')
        for v in 'TB': P.rest_bars(v, b + 2, b + 4)
        P.set_harms(b + 4, H_sub); P.place('B', b + 4, subj, -24 if min(m for _, m in subj) - 24 >= 36 else -12, lab)
        P.rest_bars('T', b + 4, b + 6)
        P.set_harms(b + 6, transpose_h(H_sub, 7)); P.place('T', b + 6, subj, 7 - 12, lab + ' 答唱')
        P.set_harms(b + 8, [['Gm', 'Gm', 'A7', 'A7'], ['Dm']]); P.hold.add(b + 9)
        b += 10
        # 抜粋の和音によるレクイエム・コラール
        P.section(b, '%s Requiem — 録音 %s の和音' % (MARK[i], hm(rid)), '抜粋の和音進行 (%s) による 4 声のコラール' % ' → '.join(transpose_h([[x[0]] for x in rec_chords(inside, semis)], semis)[j][0] for j in range(4)))
        P.set_harms(b, rec_chords(inside, semis)); P.hold.add(b + 3)
        for k in range(4): P.dyn[b + k] = 0.7
        b += 4
        LAYOUT.append((s0, b, semis, {v: rid for v in VOICES}, {}))
    # ---------------- 終曲: 5 つの主題のフーガ → B-A-D-A → ピカルディ終止 → 最初の録音の実音で閉じる
    f0 = b
    P.section(f0, 'Finale — Fuga a cinque soggetti', '5 つの主題が 1 小節おきに重なって入る。各主題は自分の録音の実音で、合わせて全部の曲が 1 つになる (ロ短調)')
    for k in range(20): P.tempo[f0 + k] = FINAL_BPM; P.dyn[f0 + k] = 0.9
    voices = ['A', 'S', 'T', 'B', 'A', 'S', 'T', 'B', 'A', 'S']
    octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}
    labmap = {}
    entries = []
    for w in range(2):                                   # 2 巡 (2 巡目は属調で)
        for i in range(5):
            k = w * 5 + i; v = voices[k]; bar = f0 + k
            rid, subj, _ = SUBJ[i]; tr = octs[v] + (7 if w == 1 else 0)
            if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
            lab = '主題 %s%s' % (MARK[i], ' 答唱' if w else '')
            P.place(v, bar, subj, tr, lab); labmap[lab] = rid
            entries.append((bar * BPB, [(d, m + tr) for d, m in subj]))
    for bar in range(f0, f0 + 12):                       # 和声: その小節で鳴る主題の音を最も多く含む和音
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            if notes:
                cs = max(CANDS, key=lambda c: sum(w * (1 if m % 12 in chord(c)['pcs'] else -0.8) for w, m in notes))
                for j in range(2): P.harm[a + j] = cs
    P.section(f0 + 12, 'Lux aeterna — B-A-D-A', 'B-A-D-A を 2 回唱え、D 長調 (ロ長調) のピカルディ終止 → 最初の録音 17:48 の実音の終わりで閉じる')
    for k in range(2):
        bb = f0 + 12 + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for j in range(2): P.place('B', bb + j, H.DRONE_BAR, 0, None)
        add('X', bb * BPB, 8, n('D3'), 0.6)
    P.set_harms(f0 + 16, [['D']] * 4); P.hold.update(range(f0 + 12, f0 + 20))
    P.place('S', f0 + 16, mat(('F#5', 12)), 0, None); P.place('A', f0 + 16, mat(('A4', 12)), 0, None); P.place('B', f0 + 16, mat(('D3', 12)), 0, None)
    for v in 'SAT': P.rest_bars(v, f0 + 19, f0 + 20)
    P.rest_bars('B', f0 + 19, f0 + 20)
    for k in range(8): P.dyn[f0 + 12 + k] = max(0.35, 0.8 - 0.06 * k)
    last = REC[SECS[0][0]]; tail = 14.0
    add('REC', (f0 + 18) * BPB + 2, tail * FINAL_BPM / 60.0, 0, 0.95 * REC_GAIN[SECS[0][0]], None, src=last['file'], off=max(0, last['dur'] - tail), rid=SECS[0][0])
    LAYOUT.append((f0, f0 + 20, FINAL_SEMIS, VOICE_SRC_FINAL, labmap))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1],
    'title': 'Requiem BADA — Tablet Sessions',
    'subtitle': '実録音のレクイエムとフーガ — タブレット録音 5 本をしたため、録音の音そのもので鳴らし、最後に全部を合わせる',
    'footer': ['① 17:48 (ロ短調) → ② 17:57 (ロ短調) → ③ 17:59 (ホ短調) → ④ 08:06 (変ロ短調) → ⑤ 08:09 (ホ短調) → 終曲: 5 つの主題のフーガ (ロ短調)',
               '各区間: 録音の実音の抜粋 → その最上声から作った主題の 4 声フーガ → その和音進行のコラール ／ 4 声は録音から切り出した 1 音を移調するサンプラー',
               '終曲では 5 つの主題が 1 小節おきに重なり、それぞれ自分の録音の音で鳴る。B-A-D-A、ピカルディ終止、最初の録音の実音で閉じる。'],
}

def finish(path):
    """区間ごとに録音の調へ移調し、各音にどの録音の音で鳴らすか (src) を付ける"""
    d = json.load(open(path))
    def lay(beat):
        bar = int(beat // BPB)
        for L in LAYOUT:
            if L[0] <= bar < L[1]: return L
        return LAYOUT[-1]
    for nt in d['notes']:
        L = lay(nt['beat']); nt['m'] += L[2]
        key = (nt['label'] or '').split(' 答唱')[0] + (' 答唱' if nt['label'] and '答唱' in nt['label'] else '')
        nt['src'] = L[4].get(nt['label'] or '', None) or L[4].get(key, None) or L[3][nt['v']]
    for e in d['extras']:
        if e['v'] not in ('REC',): e['m'] += lay(e['beat'])[2]
    d['harm'] = [transpose_h([[h]], lay(b)[2])[0][0] for b, h in enumerate(d['harm'])]
    json.dump(d, open(path, 'w'), ensure_ascii=False, indent=0)
    print('duration %.1f s, sections:' % d['duration'], len(d['sections']))

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet.json'
    compose.main(out, seed=31, bpm=72, builder=build, meta=META, extras=extras)
    finish(out)
    for rid, subj, hh in SUBJ: print(rid, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in subj), '| harm', hh)
