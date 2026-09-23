#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA · Cor — Rock (ニ短調)
  Requiem BADA · Cor の心臓の鼓動を、ロックバンドのドラムとシンセサイザーのビートに作り換える。
  曲 (合唱 + オルガンのレクイエムとフーガ)、テンポ・マップ (心拍 56 → 72 → 58 → 84 → 44)、総休止はそのまま。
    - 鼓動がキックになる: 「ドッ・クン」はキックの 2 連打 (本打 + 収縮期ぶん後の弱い打) として、ビートの中に残る
    - ドラム: スネアのバックビート、ハイハット (8 分 / 16 分)、クラッシュ、区切りの前のタム回し
    - シンセ: キックで沈むシンセ・ベース (8 分)、16 分のアルペジオ、パッド。三重フーガでは歪んだギターのパワーコード
    - 流れ: Introitus はキックの鼓動だけ → バンドが入る / Fuga I はロックのビート / Lamento はハーフタイム /
            三重フーガは 8 分のキックとギターで疾走し、総休止で全員止まる / Lux aeterna でドラムは減り、キックの鼓動だけに戻る
"""
import sys
from compose import *
import compose
import compose_heart as H

extras = H.extras
TOTAL, PAUSE_BAR = H.TOTAL, H.PAUSE_BAR
B_F1, B_RIT, B_F2, B_CODA = H.B_F1, H.B_RIT, H.B_F2, H.B_CODA

def add(v, beat, dbeats, midi, gain, label=None, **kw): H.add(v, beat, dbeats, midi, gain, label, **kw)
def dr(beat, kind, g, pan=0.0): add('DR', beat, 0.25, 60, g, None, kind=kind, pan=pan)
def tom(beat, which, g):                                 # 音高は m: G3 / D3 / A2
    add('DR', beat, 0.3, {'t1': 55, 't2': 50, 't3': 45}[which], g, None, kind='tom', pan={'t1': -0.3, 't2': 0.0, 't3': 0.3}[which])

def section(bar):
    if bar < B_F1: return 'intro'
    if bar < B_RIT: return 'f1'
    if bar < B_F2: return 'lam'
    if bar < B_CODA: return 'f2'
    return 'coda'

def post(P, events, ex):
    def heart_kick(b, hr, g, label=None):
        """鼓動のキック: 本打 + 収縮期ぶん後の弱い打 (ドッ・クン)"""
        add('DR', b, 0.25, 36, g, label, kind='kick')
        add('DR', b + max(0.24, 0.32 - 0.0012 * (hr - 60)) * hr / 60.0, 0.25, 36, g * 0.55, None, kind='kick')
    def fill(bar, g):
        """小節の後半 2 拍のタム回し (16 分)"""
        seq = ['snare', 'snare', 't1', 't1', 't2', 't2', 't3', 't3']
        for i, k in enumerate(seq):
            b = bar * BPB + 2 + i * 0.25
            if k == 'snare': dr(b, 'snare', g * 0.7)
            else: tom(b, k, g * (0.8 + 0.05 * i))
    for bar in range(TOTAL):
        s = section(bar); hr = P.tempo.get(bar, 60); b0 = bar * BPB; k = bar - {'intro': 0, 'f1': B_F1, 'lam': B_RIT, 'f2': B_F2, 'coda': B_CODA}[s]
        dyn = P.dyn.get(bar, 1.0); g = 0.55 + 0.45 * min(1.0, dyn)
        c0 = chord(P.harm[b0]); c2 = chord(P.harm[b0 + 2])
        fill_here = bar + 1 in (B_F1, B_RIT, B_F2, B_F2 + 16, B_CODA) or bar == B_F1 + 21
        pause = bar == PAUSE_BAR
        # ---------- ドラム
        if s == 'intro':
            for beat in range(4): heart_kick(b0 + beat, hr, 0.85 if beat == 0 else 0.7, 'キック = 鼓動' if bar == 0 and beat == 0 else None)
            if bar >= 4:
                for i in range(8): dr(b0 + i * 0.5, 'hatc', 0.22 if i % 2 == 0 else 0.14, 0.25)
            if bar >= 6: dr(b0 + 1, 'snare', 0.35); dr(b0 + 3, 'snare', 0.4)
        elif s == 'f1' or (s == 'f2' and k < 16):
            heart_kick(b0, hr, 0.9 * g); heart_kick(b0 + 2, hr, 0.8 * g); dr(b0 + 2.5, 'kick', 0.55 * g)
            dr(b0 + 1, 'snare', 0.75 * g); dr(b0 + 3, 'snare', 0.8 * g)
            for i in range(8):
                if fill_here and i >= 4: break
                dr(b0 + i * 0.5, 'hatc', (0.3 if i % 2 == 0 else 0.18) * g, 0.25)
            if k % 8 == 0: dr(b0, 'crash', 0.55 * g, -0.3)
        elif s == 'lam':
            heart_kick(b0, hr, 0.85); dr(b0 + 2, 'snare', 0.8)
            for i in range(4):
                if fill_here and i >= 2: break
                dr(b0 + i, 'ride', 0.28, 0.35)
            if k == 0: dr(b0, 'crash', 0.5, -0.3)
        elif s == 'f2' and bar < PAUSE_BAR:
            for i in range(8):
                if fill_here and i >= 4: break
                if i in (0, 4): heart_kick(b0 + i * 0.5, hr, 0.95 * g)
                else: dr(b0 + i * 0.5, 'kick', 0.6 * g)
            dr(b0 + 1, 'snare', 0.85 * g); dr(b0 + 3, 'snare', 0.9 * g)
            for i in range(16):
                if fill_here and i >= 8: break
                dr(b0 + i * 0.25, 'hatc', (0.26 if i % 4 == 0 else (0.18 if i % 2 == 0 else 0.1)) * g, 0.25)
            if not fill_here: dr(b0 + 3.5, 'hato', 0.25 * g, 0.25)
            dr(b0, 'crash', 0.6 * g, -0.3 if bar % 2 else 0.3)
        elif pause:
            dr(b0 + 2, 'crash', 0.9, -0.3); dr(b0 + 2, 'crash', 0.7, 0.3); heart_kick(b0 + 2, hr, 1.0, '総休止 → 全員で打ち直す'); dr(b0 + 3, 'snare', 0.9)
        elif s == 'f2':                                                   # 総休止の後のピカルディ終止: ハーフタイムの大きな打撃
            heart_kick(b0, hr, 0.95); dr(b0, 'crash', 0.7, 0.3); dr(b0 + 2, 'snare', 0.9)
            for i in range(4): dr(b0 + i, 'ride', 0.3, 0.35)
        else:                                                             # coda: ドラムは減り、鼓動のキックだけに戻る
            if k < 8:
                heart_kick(b0, hr, 0.8 * g); heart_kick(b0 + 2, hr, 0.6 * g); dr(b0 + 2, 'snare', (0.55 - 0.05 * k) * g)
                for i in range(4): dr(b0 + i, 'ride', (0.24 - 0.02 * k) * g, 0.35)
            elif k < CODA_LAST:
                for beat in range(4): heart_kick(b0 + beat, hr, (0.75 if beat == 0 else 0.6) * g)
            else:
                heart_kick(b0, hr, 0.6 * g)
                if bar < TOTAL - 1: heart_kick(b0 + 2, hr, 0.45 * g)
        if fill_here: fill(bar, 0.8 * g)
        # ---------- シンセ・ベース (8 分でキックに沈む、ハーフタイムは 2 分音符)
        if s != 'intro' or bar >= 4:
            if pause:
                add('SB', b0 + 2, 2, 36 + (c2['bass'] - 36) % 12, 0.8)
            elif s in ('lam',) or (s == 'f2' and bar > PAUSE_BAR) or (s == 'coda' and k >= 8):
                for half, c in ((0, c0), (2, c2)):
                    add('SB', b0 + half, 1.9, 36 + (c['bass'] - 36) % 12, 0.55 * g * (0.6 if s == 'coda' else 1.0))
            else:
                for i in range(8):
                    c = c0 if i < 4 else c2
                    root = 36 + (c['bass'] - 36) % 12
                    add('SB', b0 + i * 0.5, 0.45, root + (12 if (s == 'f2' and i % 2 == 1 and k >= 16) else 0), (0.6 if i % 2 == 0 else 0.45) * g)
        # ---------- アルペジオ (16 分) とパッド
        arp_on = (s == 'f1' and k >= 8) or (s == 'f2' and not pause and bar < PAUSE_BAR) or s == 'intro' and bar >= 6
        if arp_on:
            for i in range(16):
                c = c0 if i < 8 else c2
                tones = [m for m in range(62, 82) if m % 12 in c['pcs']][:4]
                order = [0, 1, 2, 3, 2, 1, 0, 1]
                m = tones[order[i % 8] % len(tones)] + (12 if i % 8 == 3 else 0)
                add('AR', b0 + i * 0.25, 0.25, m, (0.24 if i % 4 == 0 else 0.16) * g * (1.2 if s == 'f2' else 1.0), None, pan=(-0.5 if i % 2 else 0.5))
        if s in ('intro', 'lam', 'coda') or (s == 'f2' and bar > PAUSE_BAR):
            for half, c in ((0, c0), (2, c2)):
                for m in [x for x in range(50, 66) if x % 12 in c['pcs']][:3]:
                    add('PD', b0 + half, 2.4, m, 0.07 * (1.0 if s != 'coda' else max(0.4, 1 - 0.04 * k)))
        # ---------- 歪んだギター (三重結合から)
        if s == 'f2' and k >= 16 and not pause and bar < PAUSE_BAR:
            for i in range(8):
                if fill_here and i >= 4: break
                c = c0 if i < 4 else c2
                add('GT', b0 + i * 0.5, 0.45, 40 + (c['bass'] - 40) % 12, (0.42 if i % 2 == 0 else 0.32) * g, None, pan=(-0.6 if i % 2 == 0 else 0.6), mute=True)
        if pause or (s == 'f2' and bar > PAUSE_BAR):
            c = c2 if pause else c0
            add('GT', b0 + (2 if pause else 0), 2 if pause else 4, 40 + (c['bass'] - 40) % 12, 0.45, None, pan=-0.5, mute=False)
            add('GT', b0 + (2 if pause else 0) + 0.01, 2 if pause else 4, 40 + (c['bass'] - 40) % 12, 0.4, None, pan=0.5, mute=False)

CODA_LAST = 12

META = dict(H.META)
META.update({
    'style': 'rock', 'band_gain': 2.1,
    'title': 'Requiem BADA · Cor — Rock',
    'subtitle': '心臓のレクイエム ロック版 — ニ短調 ／ 鼓動をロックバンドのドラムとシンセのビートに: キックが「ドッ・クン」と打つ',
    'footer': ['鼓動 → キックの 2 連打 (ドッ・クン) ／ スネアのバックビート · ハイハット · クラッシュ · タム回し ／ シンセ・ベース · 16 分のアルペジオ · パッド ／ 三重フーガで歪んだギター',
               '主題 I ← MOTHER ／ 主題 II ← トラック18 ／ 主題 III ← B♭-A-D-A ／ 嘆きのバス ／ 聖歌 Requiem aeternam    ｜  合唱 (オ)+オルガン · ロックバンド · シンセ · 弔鐘',
               'Introitus: キックの鼓動だけ → バンド ／ Lamento: ハーフタイム ／ 三重フーガ: 8 分のキックで疾走、総休止で全員止まる ／ Lux aeterna: キックの鼓動だけに戻る'],
})
META.pop('heart_gain', None)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'score_rock.json'
    compose.main(out, seed=11, bpm=60, builder=H.build, meta=META, extras=extras, post=post)
