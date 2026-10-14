#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXVIII · Inno americano sinfonico (CXXVII をベースに、アメリカ国歌 The Star-Spangled Banner を交響曲の編成でカバー)
  旋律: The Star-Spangled Banner (John Stafford Smith、1773; パブリックドメイン) — music21 の収録譜 (miscFolk/americanfifeopus.abc、ニ長調、3/4、75 音) をそのまま (ssb_melody.json)。
    ニ長調は CXXVII のロ短調の平行長調なので、LXXXIX の土台 (−3、ロ短調) の上にそのまま乗る
  形 (CXXVII の形に国歌を 2 度): Inno (10/13 06:41、ユニゾン) → The Star-Spangled Banner I (弦だけ: Vn I が旋律、Vn II・Va が和音、Vc・Cb が根音) → Introitus (08:53、讃美歌) → Kyrie (13:03、二重フーガ) → Agnus Dei (13:07、B-A-D-A) →
    The Star-Spangled Banner II (管弦楽の総奏: トランペットとヴァイオリンが旋律、ホルンとトロンボーンが和音、フルートが 1 オクターヴ上、ティンパニが句の終わりに — 10/13 06:42 の実音と LXXXIX の Amen の上で) → ニ長調の和音、深い鐘
  国歌の段落は ♩=72、ほかは ♩=56。和音は旋律の音を含むニ長調の和音を選ぶ (harm_fit)。音源: 管弦楽は synth の合成 (meta orchestra)、ほかは CXXVII と同じ
  使い方: BANK1013=<bank1013.json> SCORE89=<score_tablet89.json> python compose_tablet128.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet128.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet128.json'
sys.argv = sys.argv[:6] + ['/dev/null']
import compose_tablet127 as T
from compose import *
import compose
import compose_heart as H
SSB = [(d, m) for d, m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssb_melody.json')))['notes']]
SSB_BEATS = sum(d for d, _ in SSB)
RECS, R41, R42, R53, R03, R07, WDIR = T.RECS, T.R41, T.R42, T.R53, T.R03, T.R07, T.WDIR
aphrase, phrase, SUBJ, SUBJ27, CANDS_BM, RATE = T.aphrase, T.phrase, T.SUBJ, T.SUBJ27, T.CANDS_G, T.RATE
CANDS_D = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m', 'D/F#', 'G/B', 'A/C#', 'Em7', 'Asus4', 'Bm/D', 'D/A', 'G/D']
INNO, SSB1, INTRO, KYRIE, AGNUS, SSB2, TOTAL = 0, 20, 48, 70, 114, 144, 176
SSB_BARS = int(math.ceil(SSB_BEATS / 4.0))
PLAYS = [(R41, 2, 0.4, 1), (R53, INTRO + 2, 0.65, 0), (R03, KYRIE + 2, 0.5, 1), (R07, AGNUS + 2, 0.5, 1), (R42, SSB2 + 2, 0.3, 1)]
extras = T.extras; add = T.add; entry = T.entry; harm_fit = T.harm_fit; augment = T.augment; rest_others = T.rest_others; invert = T.invert
def tempo_of(bar): return 72.0 if (SSB1 <= bar < INTRO or bar >= SSB2) else 56.0

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = tempo_of(k); P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = rec['dur'] / RATE(sm) * tempo_of(bar) / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / tempo_of(bar) * RATE(sm); cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = 'D' if (SSB1 * BPB <= q < INTRO * BPB or q >= SSB2 * BPB) else 'Bm'
        T.RH.append(cur); P.harm[q] = cur
    # Inno (CXXVII と同じ)
    P.section(INNO, 'Inno — 10/13 06:41 (ロ短調、ユニゾン)', '10/13 06:41 の実音 (半音上げて) の上で、Inno を 4 声のユニゾンで静かに — 1 句目は何も重ねず、2 句目から高い開いた 5 度の共鳴')
    rest_others(P, 0, 2, ''); E = []
    for k in range(4):
        b = 2 + 4 * k + (1 if k >= 2 else 0)
        for v in VOICES: entry(P, b, v, aphrase(k), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Inno 第 %d 句 (ユニゾン)' % (k + 1)) if v == 'S' else None, E)
        for v in VOICES: P.rest_bars(v, b + 3, b + 4 + (1 if k == 1 else 0))
    for v in VOICES: P.rest_bars(v, 19, SSB1)
    for q in range(INNO * BPB, SSB1 * BPB): P.harm[q] = 'Bm'
    # SSB I: 弦だけ (4 声は休む、和音は旋律から)
    P.section(SSB1, 'The Star-Spangled Banner I — 弦だけ (ニ長調, ♩=72)', 'アメリカ国歌 (1773 年の旋律、パブリックドメイン) を弦楽だけで: Vn I が旋律、Vn II・Va が和音、Vc・Cb が根音 — LXXXIX の土台 (ロ短調) の上に、平行長調で')
    for v in VOICES: P.rest_bars(v, SSB1, INTRO)
    harm_fit(P, SSB1 + 1, SSB1 + 1 + SSB_BARS + 1, [((SSB1 + 1) * BPB, SSB)], CANDS_D)
    for q in range((SSB1 + 2 + SSB_BARS) * BPB, INTRO * BPB): P.harm[q] = 'D'
    # Introitus (CXXVII)
    P.section(INTRO, 'I. Introitus — 讃美歌 (ロ短調, ♩=56)', '9/24 08:53 の実音の上で、讃美歌 (13:06 の音、ロ短調の五音音階) を 4 声のユニゾンで、2 回目は開いた 5 度のコラールで')
    rest_others(P, INTRO, INTRO + 2, ''); E = []
    for k in range(4):
        for v in VOICES: entry(P, INTRO + 2 + 2 * k, v, phrase(k), -12 + (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('讃美歌 第 %d 句 (ユニゾン)' % (k + 1)) if v == 'S' else None, E)
    for k in range(4): entry(P, INTRO + 12 + 2 * k, 'S', phrase(k), -12, '讃美歌 (コラール)' if k == 0 else None, E)
    P.hold.update(range(INTRO + 10, KYRIE)); harm_fit(P, INTRO + 2, KYRIE, E, CANDS_BM); rest_others(P, INTRO + 20, KYRIE, '')
    # Kyrie (短く)
    P.section(KYRIE, 'II. Kyrie — 二重フーガ (ロ短調)', '13:03 の実音 (半音上げて) の上で、主題 (讃美歌の第 1 句) の提示 → 10/03 13:27 の主題 → 二重 → ストレッタ')
    f = KYRIE + 2; E = []; rest_others(P, KYRIE, f, '')
    for k, v in enumerate('ASBT'):
        entry(P, f + 3 * k, v, SUBJ, 7 if k % 2 else 0, '主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 3 * k, f + 3 * k + 3)
    harm_fit(P, KYRIE, f + 12, E, CANDS_BM); f += 12; E = []
    for k, v in enumerate('SATB'):
        entry(P, f + 3 * k, v, SUBJ27, 7 if k % 2 else 0, '13:27 の主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'SATB'[k + 1:]: P.rest_bars(w, f + 3 * k, f + 3 * k + 3)
    harm_fit(P, f, f + 12, E, CANDS_BM); f += 12; E = []
    for k in range(2):
        entry(P, f + 4 * k, 'SA'[k], SUBJ27, 0, '二重' if k == 0 else None, E); entry(P, f + 4 * k, 'TB'[k], SUBJ, 0, None, E)
        for w in VOICES:
            if w not in ('SA'[k], 'TB'[k]): P.rest_bars(w, f + 4 * k, f + 4 * k + 4)
    harm_fit(P, f, f + 8, E, CANDS_BM); f += 8; E = []
    for k, v in enumerate('ASTB'): entry(P, f + k, v, SUBJ, 0, 'ストレッタ' if k == 0 else None, E)
    harm_fit(P, f, AGNUS, E, CANDS_BM); rest_others(P, f + 4, AGNUS, '')
    # Agnus Dei
    P.section(AGNUS, 'IV. Agnus Dei — B-A-D-A (ロ短調)', '13:07 の実音 (半音上げて) の上で、B-A-D-A を唱える合唱に、主題が重なる')
    rest_others(P, AGNUS, AGNUS + 2, ''); E = []
    for k in range(7):
        bb = AGNUS + 2 + 4 * k
        P.place('A', bb, H.BADA, 1, 'B-A-D-A' if k == 0 else None); E.append((bb * BPB, [(d, m + 1) for d, m in H.BADA]))
        if k % 2 == 1: entry(P, bb, 'S', SUBJ, 0, None, E)
        else: P.rest_bars('S', bb, bb + 4)
        P.rest_bars('T', bb, bb + 4); P.place('B', bb, [(4, 47)] * 4, 0, None) if k % 2 == 0 else P.rest_bars('B', bb, bb + 4)
    P.hold.update(range(AGNUS + 2, SSB2)); harm_fit(P, AGNUS + 2, SSB2, E, CANDS_BM)
    # SSB II: 総奏
    P.section(SSB2, 'The Star-Spangled Banner II — 管弦楽の総奏 (ニ長調, ♩=72)', '10/13 06:42 の実音 (小さく) と LXXXIX の Amen の上で、国歌を総奏で: トランペットとヴァイオリンが旋律、ホルンとトロンボーンが和音、フルートが 1 オクターヴ上、ティンパニが句の終わりに — ニ長調の和音と深い鐘で閉じる')
    for v in VOICES: P.rest_bars(v, SSB2, TOTAL - 4)
    harm_fit(P, SSB2 + 1, SSB2 + 1 + SSB_BARS + 1, [((SSB2 + 1) * BPB, SSB)], CANDS_D)
    for q in range((SSB2 + 2 + SSB_BARS) * BPB, TOTAL * BPB): P.harm[q] = 'D'
    for b in range(TOTAL - 4, TOTAL): P.set_harm(b, 'D'); P.hold.add(b)
    P.place('S', TOTAL - 4, [(4, 78)] * 4, 0, 'ニ長調 (レ・ラ・ファ#)'); P.place('A', TOTAL - 4, [(4, 74)] * 4, 0, ''); P.place('T', TOTAL - 4, [(4, 69)] * 4, 0, ''); P.place('B', TOTAL - 4, [(4, 50)] * 4, 0, ''); P.rest_bars('S', TOTAL - 1, TOTAL)
    return P

OG = 0.34                                                                                       # 管弦楽の大きさ (ステムで測って: 弦 −17 dB、総奏 −14 dB ほど)
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)
def orchestrate(P, b0, tutti):
    """国歌の旋律を管弦楽で (b0 小節の 1 拍目から)。和音は P.harm (拍ごと)"""
    t = b0 * BPB; first = True; ph_end = {i for i in (11, 20, 29, 38, 53, 62, 74)}                   # 句の終わり (ティンパニ)
    for i, (d, m) in enumerate(SSB):
        g = 0.42 if tutti else 0.32
        oadd('V1', t, d, m, g, 'Vn I — The Star-Spangled Banner' if first else None); oadd('V1', t, d, m, g * 0.6, None)
        if tutti:
            oadd('TR', t, d, m, 0.34, 'トランペット' if first else None); oadd('FL', t, d, m + 12, 0.2, 'フルート (1 オクターヴ上)' if first else None); oadd('V2', t, d, m - 12 if m >= 74 else m, 0.22, None)
        c = chord(P.harm[min(int(t), TOTAL * BPB - 1)]); pcs = sorted(c['pcs'])
        below = max((x for x in range(m - 12, m - 2) if x % 12 in c['pcs']), default=m - 5)
        oadd('V2' if not tutti else 'HN', t, d, below, 0.22 if not tutti else 0.26, ('Vn II' if not tutti else 'ホルン') if first else None)
        va = max((x for x in range(52, 66) if x % 12 in c['pcs']), default=57); oadd('VA', t, d, va, 0.2, 'Va' if first else None)
        if tutti: oadd('HN', t, d, va + 7 if (va + 7) % 12 in c['pcs'] else va + 5, 0.2, None)
        if i % 2 == 0 or d >= 2:
            root = 38 + c['root']; oadd('VC', t, max(d, 1.0), root + 12, 0.22, 'Vc' if first else None); oadd('CB', t, max(d, 1.0), root, 0.26, 'Cb' if first else None)
            if tutti: oadd('TB', t, max(d, 1.0), root + 12, 0.24, 'トロンボーン' if first else None)
        if tutti and i in ph_end: oadd('TP', t, 2.0, 38 if c['root'] == 2 else 45, 0.5, 'ティンパニ' if i == 11 else None)
        first = False; t += d
    if tutti: oadd('TP', t, 3.0, 38, 0.6, None); oadd('TP', t + 0.5, 2.5, 45, 0.45, None)

def post(P, events, ex):
    for rid, bar, g, sm in PLAYS:
        add('REC', bar * BPB, RECS[rid]['dur'] / RATE(sm) * tempo_of(bar) / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 2 else 0.02, fout=4.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % ({R41: '10/13 06:41', R53: '9/24 08:53', R03: '10/12 13:03', R07: '10/12 13:07', R42: '10/13 06:42'}[rid], ' (半音上げてロ短調に)' if sm else ''))
    orchestrate(P, SSB1 + 1, False); orchestrate(P, SSB2 + 1, True)
    add('X', 0, 10, 35, 0.35, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 38, 0.45, None)
    # LXXXIX (−3、中音域) を小さく全曲に (Inno の 1 句目は除く)
    off = 6 * BPB; src_len = 96 * BPB; first = True
    def mid(m): return m + 12 if m < 53 else m
    for rep_ in range(int(math.ceil(((TOTAL - 4) * BPB - off) / float(src_len)))):
        for n in T.S89['notes']:
            b = off + rep_ * src_len + n['beat']
            if b >= (TOTAL - 4) * BPB: continue
            add('PF', b, n.get('dbeats', n['d']), mid(n['m'] - 3), 0.09 * (0.62 * n.get('dyn', 1.0) + 0.08) / 0.5, 'LXXXIX (−3、中音域、小さく)' if first else None, rid=n.get('src'), rel=0.5, layer='base'); first = False
        for e in T.S89['extras']:
            if e['v'] != 'PF': continue
            b = off + rep_ * src_len + e['beat']
            if b >= (TOTAL - 4) * BPB: continue
            add('PF', b, e['dbeats'], mid(e['m'] - 3), e['gain'] * 0.22, None, rid=e.get('rid'), rel=0.5, layer='base')
    q = 0; first = True                                                                             # 共鳴 (13:19 の音)
    while q < TOTAL * BPB:
        h = P.harm[q]; q1 = q
        while q1 < TOTAL * BPB and P.harm[q1] == h: q1 += 1
        for cut in (6 * BPB, SSB1 * BPB, INTRO * BPB, SSB2 * BPB):
            if q < cut < q1: q1 = cut
        bar = q // BPB; d = max(1.0, (q1 - q) + 0.6); c = chord(h)
        if bar < 6: pass
        elif bar < SSB1:
            for i, m in enumerate((83, 90)): add('PF', q + 0.05 * i, d, m, 0.8 * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
        else:
            tones = [min((x for x in range(52, 76) if x % 12 == p), key=lambda x: abs(x - 62)) for p in (c['root'], c['fifth'], c['third'])]
            g = 0.11 if (SSB1 <= bar < INTRO or bar >= SSB2) else 0.11
            for i, m in enumerate(tones): add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.7), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
            add('PF', q, d, tones[0] - 12, g * 0.6, None, rid='VOXRS', rel=1.5, layer='res')
        q = q1

META = dict(T.META, orchestra=True, rec_order=[R41, R53, R03, R07, R42], reverb=[7.0, 3.0, 0.5],
            title='Requiem BADA — CXXVIII · Inno americano sinfonico',
            subtitle='CXXVII をベースに、アメリカ国歌 The Star-Spangled Banner (1773 年の旋律、ニ長調 = ロ短調の平行長調) を交響曲の編成でカバー — Inno (10/13) → 国歌 I (弦だけ) → Introitus → Kyrie (二重フーガ) → Agnus Dei → 国歌 II (総奏: トランペット・ホルン・トロンボーン・フルート・弦・ティンパニ) → ニ長調で閉じる。♩=56 / 72',
            legend=['PF', 'X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'HN', 'TR', 'TB', 'TP'], vname={'PF': '共鳴 / LXXXIX', 'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
            footer=['旋律は music21 の収録譜 (miscFolk/americanfifeopus.abc、75 音) をそのまま。和音は旋律の音を含むニ長調の和音を選ぶ。裏に LXXXIX (−3、中音域) と 13:19 の音の共鳴',
                    '管弦楽は synth の合成 (弦・木管・金管・ティンパニ)。鐘は始めと終わりに深いものがひとつ。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    print('SSB beats', SSB_BEATS, 'bars', SSB_BARS)
    compose.main(OUT, seed=128, bpm=56, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = T.PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0), 4), label=None, rid=T.PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
