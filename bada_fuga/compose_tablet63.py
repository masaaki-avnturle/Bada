#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LXIII · Requiem e Fuga cantabile (LXII に、トラック 8 の曲調を取り込んで — 旋律が自然に流れるように、実音のピアノだけで)
  トラック 8 も、音そのもの・旋律は使っていない。解析で得た曲調だけを借りる:
    - イ短調、♩≈99、まっすぐな拍 (跳ねない)、低音があたたかい、静かに始まって少しずつ厚くなり、最後は静かに消える
    - 調の道のり: イ短調 ⇄ ホ短調 (行ったり来たり) → 中ほどでニ長調・ハ長調・ト長調 → イ長調の明るい瞬間 → イ短調・ハ長調で終わる
    → この曲はイ短調、♩=66 (左手の 3 連の分散和音が 1 分に 198 = トラック 8 の 1 拍に 2 つ)
      Introitus (15:20 の実音, ホ短調) → Requiem (アリア, イ短調 ⇄ ホ短調) → Fuga I (イ短調) → Lacrimosa (15:19 の実音, ト長調)
      → Fuga II (ニ短調) → Amen (変格終止 → イ長調)
  旋律が自然に流れるように:
    - 主題をなめらかにする (smooth): 音の高さを前の音のいちばん近いオクターヴに置き直し、4 度より大きい跳躍は、前の音を分けて音階の経過音でつなぐ
    - Requiem はアリア: ソプラノが歌い、左手が 3 連の分散和音 (根音・5 度・10 度と上がって下りる) で流れる。
      旋律は 15:16 → 15:12 (5 度上 = ホ短調の答え) → 15:16 → 13:04 と、2 小節ずつ歌い継ぐ
    - フーガは段のように動く主題を選ぶ: Fuga I は 15:16 の主題 (ラ・シ♭・ラ・ソ・ファ・レのように下りる)、Fuga II は 15:12 の主題
    - 区間のつなぎ目は録音の実音の抜粋で、調をなめらかに渡す (ホ短調 → イ短調、ト長調 → ニ短調)
  シンセ・ドラム・心臓の鼓動・弦・オルガンなし。すべて録音から切り出したピアノの実音。
  使い方: python compose_tablet63.py <bank61.json> [score_tablet63.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet11 as T11
import compose_tablet48 as K
import compose_tablet61 as LXI
import compose_tablet62 as LXII

add, hm = CT.add, T3.hm
BPM = 66
R12, R16, R20, Q46, Q50, Q04 = LXI.R12, LXI.R16, LXI.R20, LXI.Q46, LXI.Q50, LXI.Q04
R19 = '20260929_151919'
KEYS = dict(LXI.KEYS); KEYS[R19] = 2                # 15:19 はト長調 (ホ短調の平行調)
LXI.T7.KEYS.update(KEYS)
ORDER = LXI.ORDER + [R19]
VOICE_SRC, DYNK = LXI.VOICE_SRC, LXI.DYNK
AM, EM, DM = -5, 2, 0                              # ニ短調からの移調: イ短調・ホ短調・ニ短調
ARP = []                                           # (b0, b1, 大きさ, 区間の移調) — 左手の 3 連の分散和音

def post(P, events, extras):
    for b0, b1, g, semis in ARP:                   # 根音・5 度・10 度・オクターヴ上の 5 度・10 度・5 度 (半小節で 1 往復)
        for bar in range(b0, b1):
            for h in range(2):
                c = chord(P.harm[bar * BPB + 2 * h] or 'Dm'); lo = 40 - semis; r = lo + (c['root'] - lo) % 12
                third = 4 if (c['root'] + 4) % 12 in c['pcs'] else 3
                fig = (r, r + 7, r + 12 + third, r + 19, r + 12 + third, r + 7)
                for k, m in enumerate(fig):
                    a = (1.0, 0.7, 0.75, 0.8, 0.7, 0.65)[k]
                    add('PF', bar * BPB + 2 * h + k / 3.0, 0.7, m, g * a, None, rid=VOICE_SRC['B'], rel=0.5)

def smooth(s_):
    """主題をなめらかに: 前の音にいちばん近いオクターヴへ置き直し (ハ 4〜ソ 5)、4 度より大きい跳躍は経過音でつなぐ"""
    out = [list(s_[0])]
    for d, m in s_[1:]:
        prev = out[-1][1]
        m = min((m + 12 * k for k in range(-2, 3) if 60 <= m + 12 * k <= 79), key=lambda x: abs(x - prev))
        out.append([d, m])
    res = []
    for i, (d, m) in enumerate(out):
        nxt = out[i + 1][1] if i + 1 < len(out) else None
        if nxt is not None and abs(nxt - m) > 5 and d >= 1.0:
            step = 1 if nxt > m else -1
            scale = [x for x in range(min(m, nxt) + 1, max(m, nxt)) if x % 12 in CT.DMIN]
            scale = scale if step > 0 else scale[::-1]
            k_ = 2 if (len(scale) >= 4 and d >= 2.0) else 1          # 経過音は 1 つ (長い音なら 2 つ)
            pick = [scale[len(scale) * (j + 1) // (k_ + 1)] for j in range(k_)] if scale else []
            dd = 0.5 * len(pick)
            res.append((d - dd, m)); res += [(0.5, x) for x in pick]
        else:
            res.append((d, m))
    return res

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0); s_ = smooth(CT.make_subject(inside, KEYS[r], BPM)); T5.SUBJ[r] = (s_, CT.harmonize(s_))
        print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s_))
    total = 4 + 8 + 16 + 4 + 16 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = DYNK
    b = 0
    def excerpt(rid, bars, title, sub, fout=3.0):
        nonlocal b
        P.section(b, title, sub)
        T5.passage(P, rid, b, bars, KEYS[rid], bars, fin=1.5, fout=fout, bpm=BPM, gmul=0.6)
        for v in VOICES: P.rest_bars(v, b, b + bars)
        for k in range(bars): P.dyn[b + k] = DYNK
        CT.LAYOUT.append((b, b + bars, KEYS[rid], {v: rid for v in VOICES}, {})); b += bars
    def section(title, sub, bars, semis):
        nonlocal b
        P.section(b, title, sub); f = b; CT.LAYOUT.append((f, f + bars, semis, VOICE_SRC, {})); b += bars; return f
    # ================= Introitus (15:20 の実音, ホ短調 — トラック 8 の静かな始まり)
    excerpt(R20, 4, 'Introitus — %s の実音 (ホ短調)' % hm(R20), '9/29 15:20 のピアノの実音 (録音) — 静かに始まり、イ短調のアリアへ')
    # ================= Requiem aeternam (アリア, イ短調 ⇄ ホ短調)
    f = section('Requiem aeternam — アリア (イ短調)', 'ソプラノが %s → %s (ホ短調の答え) → %s → %s と歌い継ぎ、左手が 3 連の分散和音で流れる' % (hm(R16), hm(R12), hm(R16), hm(Q04)), 8, AM)
    for k, (r, tr) in enumerate([(R16, 0), (R12, 7), (R16, 0), (Q04, 0)]):
        s_, H = T5.SUBJ[r]
        P.set_harms(f + 2 * k, transpose_h(H, tr))
        LXI.place(P, f + 2 * k, [(d, m + tr) for d, m in s_], 'アリア (%s)%s' % (hm(r), ' · ホ短調の答え' if tr else ''))
    for k in range(8): P.dyn[f + k] = DYNK * (0.6 if k < 2 else 0.68)
    ARP.append((f, f + 8, 0.2, AM))
    # ================= Fuga I (15:16 の主題, イ短調)
    f = section('Fuga I (イ短調)', '%s の段のように下りる主題の 4 声フーガ — 声部が歌い継ぐ' % hm(R16), 16, AM)
    n_ = T11.bach_fugue(P, f, R16, '①')
    for k in range(n_): P.dyn[f + k] = DYNK * (0.7 if k < 8 else 0.76)
    # ================= Lacrimosa (15:19 の実音, ト長調 — トラック 8 の中ほどの長調)
    excerpt(R19, 4, 'Lacrimosa — %s の実音 (ト長調)' % hm(R19), '9/29 15:19 のピアノの実音 (録音) — 中ほどの長調の明るさ')
    # ================= Fuga II (15:12 の主題, ニ短調)
    f = section('Fuga II (ニ短調)', '%s の主題のフーガ — 下属調 (ト短調) の入り、ストレッタで山へ' % hm(R12), 16, DM)
    n_ = T11.bach_fugue(P, f, R12, '②')
    for k in range(n_): P.dyn[f + k] = DYNK * (0.74 if k < 12 else 0.84)
    # ================= Amen (変格終止 → イ長調)
    f = section('Amen — 変格終止 (イ長調の和音で)', 'iv → I: トラック 8 の明るい瞬間のように、イ長調の和音で静かに閉じる', 3, AM + 12)
    P.set_harms(f, [['Gm'], ['D'], ['D']])
    P.place('S', f, [(4, n('Bb4')), (8, n('A4'))], 0, 'Amen')
    for k in range(3): P.dyn[f + k] = DYNK * 0.66
    ARP.append((f, f + 2, 0.16, AM + 12))
    assert b == total, (b, total)
    return P

META = {k: v for k, v in LXI.META.items()}
META.update(
    rec_order=ORDER,
    title='Requiem BADA — LXIII · Requiem e Fuga cantabile',
    subtitle='トラック 8 の曲調 (イ短調とホ短調を行き来、まっすぐな拍、あたたかい低音) — 旋律が自然に流れるように (♩=66)',
    legend=['TB', 'PF'], vname={'PF': '分散和音'},
    footer=['Introitus 15:20 → Requiem (アリア, イ短調) → Fuga I (15:16, イ短調) → Lacrimosa 15:19 (ト長調) → Fuga II (15:12, ニ短調) → Amen (イ長調)',
            'すべて録音から切り出したピアノの実音。プロの楽曲からは調・速さ・調の道のり・響きの厚さだけを借りた (音と旋律は使っていない)。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet63.json'
    compose.main(out, seed=163, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.BPM = BPM; K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    aria = next(s for s in d['sections'] if s['title'].startswith('Requiem aeternam')); t_a0 = aria['t']
    t_a1 = next(s['t'] for s in d['sections'] if s['t'] > t_a0 + 1e-3)
    for n_ in d['notes']:
        k = 1.25                                                          # 4 声のピアノの実音を前に (LI〜LXII と同じ)
        lab = n_.get('label') or ''
        if t_a0 - 1e-3 <= n_['t'] < t_a1 - 1e-3: k *= 1.22 if lab.startswith('アリア') else 0.82   # アリア: 歌う旋律を前に、内声は後ろへ
        elif lab.startswith('主題'): k *= 1.12                            # フーガ: 主題の入りがよく聞こえるように
        n_['dyn'] = round(n_.get('dyn', 1.0) * k, 4)
    LXII.fix_pulse(d)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']), 'duration', round(d['duration'], 1))
