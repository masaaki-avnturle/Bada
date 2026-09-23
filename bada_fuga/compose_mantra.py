#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA · Cor — Mantra (ニ短調)
  Cor — Rock から流れるアルペジオ (とギター・パッド) を外し、ドラムを洗脳的に反復するビートにして、
  曲全体をシンセサイザーの倍音が鳴り響く洗脳の曲に作り換える。曲・テンポ・マップ・総休止はそのまま。
    - 倍音シンセ: 4 声 (S A T B) を合唱・オルガンではなく倍音列の加算合成で鳴らし、狭い共鳴が 2 小節ごとに
      300 Hz → 3000 Hz → 300 Hz と往復して、倍音唱法のように倍音を 1 本ずつ鳴らす (共鳴は拍に同期)
    - 倍音ドローン: 低い D (と A) の倍音列が、同じ共鳴に合わせて全曲で鳴り響く
    - 洗脳的なドラム: 毎拍の鼓動キック (ドッ・クン)、2・4 拍のスネア、同じアクセントを繰り返す 16 分のハイハット、
      毎小節同じ位置の低いタムのオスティナート。フィルもタム回しもなく、同じ型だけが続く
    - Lamento はハーフタイム、総休止で全員止まり、Lux aeterna でドラムは 1 つずつ消えて鼓動のキックだけが残る
"""
import sys
from compose import *
import compose
import compose_heart as H

extras = H.extras
TOTAL, PAUSE_BAR = H.TOTAL, H.PAUSE_BAR
B_F1, B_RIT, B_F2, B_CODA = H.B_F1, H.B_RIT, H.B_F2, H.B_CODA
HAT = [0.30, 0.10, 0.20, 0.12]                       # 1 拍の中の 16 分のアクセント (毎拍おなじ)

def add(v, beat, dbeats, midi, gain, label=None, **kw): H.add(v, beat, dbeats, midi, gain, label, **kw)
def dr(beat, kind, g, pan=0.0, m=60): add('DR', beat, 0.25, m, g, None, kind=kind, pan=pan)

def section(bar):
    if bar < B_F1: return 'intro'
    if bar < B_RIT: return 'f1'
    if bar < B_F2: return 'lam'
    if bar < B_CODA: return 'f2'
    return 'coda'

def post(P, events, ex):
    # レクイエムのドローンは倍音ドローンに置き換え、全曲に低い D と A の倍音ドローンを敷く
    for e in ex:
        if e['v'] == 'D': e['v'] = 'OD'; e['gain'] = e['gain'] * 0.5
    add('OD', 0, TOTAL * BPB, n('D1'), 0.55, '倍音ドローン (D)')
    add('OD', 2 * BPB, (TOTAL - 2) * BPB, n('A1'), 0.3)
    def heart_kick(b, hr, g, label=None):
        add('DR', b, 0.25, 36, g, label, kind='kick')
        add('DR', b + max(0.24, 0.32 - 0.0012 * (hr - 60)) * hr / 60.0, 0.25, 36, g * 0.55, None, kind='kick')
    for bar in range(TOTAL):
        s = section(bar); hr = P.tempo.get(bar, 60); b0 = bar * BPB
        k = bar - {'intro': 0, 'f1': B_F1, 'lam': B_RIT, 'f2': B_F2, 'coda': B_CODA}[s]
        g = 0.6 + 0.4 * min(1.0, P.dyn.get(bar, 1.0))
        c0 = chord(P.harm[b0]); c2 = chord(P.harm[b0 + 2])
        pause = bar == PAUSE_BAR
        after = s == 'f2' and bar > PAUSE_BAR
        # どの層が鳴っているか (曲の流れ): 入る順と消える順
        kick = True
        hats = (s == 'intro' and bar >= 4) or s in ('f1', 'f2') or (s == 'lam') or (s == 'coda' and k < 6)
        snare = (s == 'intro' and bar >= 6) or s in ('f1', 'f2', 'lam') or (s == 'coda' and k < 9)
        toms = s in ('f1', 'f2') and not after or (s == 'coda' and k < 3)
        if pause:
            dr(b0 + 2, 'crash', 0.9, -0.3); dr(b0 + 2, 'crash', 0.7, 0.3)
            heart_kick(b0 + 2, hr, 1.0, '総休止 → 打ち直す'); heart_kick(b0 + 3, hr, 0.8); dr(b0 + 3, 'snare', 0.85)
        else:
            for beat in range(4):
                heart_kick(b0 + beat, hr, (0.95 if beat == 0 else 0.8) * g * (1.0 if s != 'coda' else max(0.45, 1 - 0.035 * k)),
                           'キック = 鼓動' if bar == 0 and beat == 0 else None)
            if snare:
                beats = (2,) if s == 'lam' or after else (1, 3)
                for bt in beats: dr(b0 + bt, 'snare', (0.72 if s != 'coda' else max(0.25, 0.6 - 0.05 * k)) * g)
            if hats:
                step = 0.25 if s in ('f1', 'f2') else 0.5
                fade = 1.0 if s != 'coda' else max(0.2, 1 - 0.15 * k)
                for i in range(int(4 / step)):
                    acc = HAT[i % 4] if step == 0.25 else (0.3 if i % 2 == 0 else 0.14)
                    dr(b0 + i * step, 'hatc', acc * g * fade * (0.9 if s == 'intro' else 1.0), 0.25)
                if s == 'f2' and not after: dr(b0 + 3.5, 'hato', 0.18 * g, 0.25)
            if toms:                                           # 毎小節おなじ位置の低いタム (儀式のようなオスティナート)
                for bt, m, gg in ((1.5, 45, 0.5), (2.75, 45, 0.38), (3.5, 50, 0.42)):
                    add('DR', b0 + bt, 0.3, m, gg * g, None, kind='tom', pan=0.15)
            if k == 0 and s in ('f1', 'lam', 'f2'): dr(b0, 'crash', 0.55, -0.3)
            if after and k == PAUSE_BAR + 1 - B_F2: dr(b0, 'crash', 0.7, 0.3)
        # ---------- シンセ・ベース (8 分で鼓動に沈む。Lamento・終止・Lux aeterna の後半は 2 分音符)
        if s == 'intro' and bar < 4: continue
        if pause:
            add('SB', b0 + 2, 2, 36 + (c2['bass'] - 36) % 12, 0.8)
        elif s == 'lam' or after or (s == 'coda' and k >= 6):
            for half, c in ((0, c0), (2, c2)):
                add('SB', b0 + half, 1.9, 36 + (c['bass'] - 36) % 12, 0.55 * g * (1.0 if s != 'coda' else max(0.3, 1 - 0.05 * k)))
        else:
            for i in range(8):
                c = c0 if i < 4 else c2
                add('SB', b0 + i * 0.5, 0.45, 36 + (c['bass'] - 36) % 12, (0.58 if i % 2 == 0 else 0.42) * g)

META = dict(H.META)
META.pop('heart_gain', None)
META.update({
    'style': 'mantra', 'band_gain': 0.8,
    'title': 'Requiem BADA · Cor — Mantra',
    'subtitle': '心臓のレクイエム 洗脳版 — ニ短調 ／ シンセの倍音が鳴り響き、同じビートが続く: 共鳴が 2 小節ごとに倍音列を上下する',
    'footer': ['倍音シンセ ← 4 声を倍音列の加算合成で。狭い共鳴が 300 → 3000 → 300 Hz を 2 小節で往復し、倍音を 1 本ずつ鳴らす (拍に同期)。低い D と A の倍音ドローン',
               '洗脳的なドラム ← 毎拍の鼓動キック (ドッ・クン) · 2・4 拍のスネア · 同じアクセントの 16 分ハイハット · 毎小節同じ低いタム。フィルなし。シンセ・ベースは 8 分',
               '主題 I ← MOTHER ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A ／ 嘆きのバス ／ 聖歌 Requiem aeternam — 総休止で全員止まり、Lux aeterna で鼓動だけが残る'],
})

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_mantra.json'
    compose.main(out, seed=11, bpm=60, builder=H.build, meta=META, extras=extras, post=post)
