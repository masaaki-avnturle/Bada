#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_sennou.py — 提出された録音の「2 分後半〜3 分」(2:30–3:00) を手本に、
主題メロディーと伴奏を **洗脳的 (一度聴いたら離れない)** に決め直し、曲を作り換える。

  python3 sennou/make_sennou.py a.mp3 b.mp4 ... -o sennou/sennou.mp4 [--each sennou/each]

メロディーは **エントロピー (情報量・意外性) では選ばない**。代わりに「音符の流れのきれいさ」
(flow beauty) という、作曲法の規則だけでできた評価関数で選ぶ:

  順次進行の割合 / 跳躍の後の反行順次 (gap-fill) / 山がひとつのアーチ形と黄金比の頂点 /
  音域 / 強拍の和声音 / 非和声音の解決 / 導音→主音 / 主音への終止 / 音の運動エネルギーの小ささ /
  リズムの流れ (細かい→長い) / 手本区間の音程の語彙との一致

「洗脳的」は反復の設計で作る: 4 和音のループ (終わりが始まりへ吸い込まれる循環) を曲全体で止めず、
主題は  A (フック) – A' (同じ形の反復進行) – A (完全反復) – B (終止)  の 8 小節。
伴奏は 1 小節のオスティナートを候補から評価関数で選び、全曲で反復する。

依存: numpy, scipy, librosa, mido, Pillow, ffmpeg。fluidsynth + GM サウンドフォントがあれば
ピアノ・弦をそれで鳴らし、無ければ内蔵の加算合成で鳴らす。
"""
import argparse
import itertools
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import scipy.signal as sg
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'requiem'))
import make_requiem as rq  # noqa: E402  (reverb / タイトルカード / フォント探索を再利用)

SR = 44100
ASR = 22050  # 解析用
NN = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
MINOR = [0, 2, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
# 和音 (主音からの半音, 構成音)。短調の V は和声的短音階 (導音つき)
CHORDS = {
    'minor': {'i': [0, 3, 7], 'iv': [5, 8, 0], 'V': [7, 11, 2], 'v': [7, 10, 2], 'VI': [8, 0, 3],
              'III': [3, 7, 10], 'VII': [10, 2, 5]},
    'major': {'I': [0, 4, 7], 'ii': [2, 5, 9], 'iii': [4, 7, 11], 'IV': [5, 9, 0], 'V': [7, 11, 2],
              'vi': [9, 0, 4]},
}
TONICS = {'minor': 'i', 'major': 'I'}
WIN = (150.0, 180.0)  # 2:30–3:00


def nm(m):
    return NN[m % 12] + str(m // 12 - 1)


def decode(path, sr):
    raw = subprocess.run([rq.ffmpeg_exe(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


# ============================================================================ 1. 手本区間の解析
class Reference:
    """1 本の録音の 2:30–3:00。短い録音 (3 分未満) は終わり 5 秒手前までの最後の 30 秒を使う。"""

    def __init__(self, path):
        import librosa
        self.path = path
        base = os.path.splitext(os.path.basename(path))[0]
        self.name = base.split('-', 1)[1] if len(base) > 9 and base[8] == '-' else base  # アップロード接頭辞を除く
        x = decode(path, ASR)
        self.dur = len(x) / ASR
        if self.dur >= WIN[1] + 5:
            self.a, self.b = WIN
        else:
            self.b = max(10.0, self.dur - 5)
            self.a = max(0.0, self.b - 30)
        y = x[int(self.a * ASR):int(self.b * ASR)]
        self.y = y
        chroma = librosa.feature.chroma_cqt(y=y, sr=ASR, hop_length=512)
        self.tonic, self.mode, self.key_r = self._key(chroma.mean(1))
        tempo, beats = librosa.beat.beat_track(y=y, sr=ASR, hop_length=512)
        self.tempo = float(np.atleast_1d(tempo)[0])
        self.beat_s = 60.0 / self.tempo if self.tempo > 0 else 0.8
        self.notes = self._transcribe(y)
        self.chords = self._chords(chroma, beats)

    @staticmethod
    def _key(c):
        best = (-2, 0, 'minor')
        for t in range(12):
            for mode, prof in (('major', KK_MAJ), ('minor', KK_MIN)):
                r = np.corrcoef(np.roll(prof, t), c)[0, 1]
                if r > best[0]:
                    best = (r, t, mode)
        return best[1], best[2], best[0]

    def _transcribe(self, y, hop=256):
        """最上声 (skyline) の旋律を取り出す: オンセット毎に倍音和で強い音の中の最高音。"""
        import librosa
        lo = 36
        C = np.abs(librosa.cqt(y, sr=ASR, hop_length=hop, fmin=librosa.midi_to_hz(lo), n_bins=72, bins_per_octave=12))
        S = C.copy()
        for h, w in ((12, .5), (19, .33), (24, .25)):
            S[:-h] += w * C[h:]
        on = librosa.onset.onset_detect(y=y, sr=ASR, hop_length=hop, backtrack=True, delta=0.05)
        on = np.append(on, S.shape[1])
        out = []
        for a, b in zip(on[:-1], on[1:]):
            if b - a < 3:
                continue
            seg = S[:, a:min(b, a + 20)].mean(1)
            mx = seg.max()
            pk = [i for i in range(1, len(seg) - 1) if seg[i] >= seg[i - 1] and seg[i] >= seg[i + 1] and seg[i] > 0.35 * mx]
            hi = [i for i in pk if i + lo >= 55]
            if hi:
                out.append((a * hop / ASR, (b - a) * hop / ASR, max(hi) + lo))
        return out

    def _chords(self, chroma, beats):
        """拍ごとのクロマを、調の和音テンプレートに当てて和音記号列にする (相対度数なので調を超えて比べられる)。"""
        import librosa
        if len(beats) < 4:
            return []
        cs = librosa.util.sync(chroma, beats, aggregate=np.mean)
        seq = []
        for k in range(cs.shape[1]):
            v = np.roll(cs[:, k], -self.tonic)
            best = max(CHORDS[self.mode].items(), key=lambda kv: sum(v[p] for p in kv[1]))
            seq.append(best[0])
        return seq

    # --- 目標の調・旋法に合わせた相対表現 -------------------------------------------
    def rel_offset(self, target_mode):
        """この録音の音を目標の旋法の「主音からの半音」に直すための主音。長調⇔短調は平行調で対応させる。"""
        if self.mode == target_mode:
            return self.tonic
        return (self.tonic + 9) % 12 if target_mode == 'minor' else (self.tonic + 3) % 12

    def chords_in(self, target_mode):
        if self.mode == target_mode:
            return self.chords
        m = ({'I': 'III', 'ii': 'iv', 'iii': 'v', 'IV': 'VI', 'V': 'VII', 'vi': 'i'} if target_mode == 'minor'
             else {'i': 'vi', 'iv': 'ii', 'V': 'iii', 'v': 'iii', 'VI': 'IV', 'III': 'I', 'VII': 'V'})
        return [m[c] for c in self.chords]

    def describe(self):
        return (f'{self.name:18s} {int(self.dur // 60)}:{int(self.dur % 60):02d}  手本 {int(self.a // 60)}:{int(self.a % 60):02d}–'
                f'{int(self.b // 60)}:{int(self.b % 60):02d}  {NN[self.tonic]} {self.mode} (r={self.key_r:.2f})  '
                f'{self.tempo:.0f} bpm  旋律 {len(self.notes)} 音')


def diatonic_index(rel_pc_abs, scale):
    """主音からの半音 (オクターブ込み) → 音階上の段数 (音階外は近い方へ)。"""
    o, pc = divmod(int(rel_pc_abs), 12)
    d = min(range(7), key=lambda i: abs(scale[i] - pc))
    return o * 7 + d


def vocabulary(refs, mode):
    """手本区間の旋律から「音階上の音程 3 連」の語彙 (出現頻度) と、音価 (8 分音符単位) の分布を作る。"""
    scale = MINOR if mode == 'minor' else MAJOR
    tri, ioi = {}, np.zeros(9)
    for r in refs:
        t0 = r.rel_offset(mode)
        # 同じ高さの連続 (伴奏や持続音で分かれたオンセット) は 1 音にまとめ、長さを足す
        merged = []
        for t, d, m in r.notes:
            if merged and merged[-1][1] == m and t - (merged[-1][0] + merged[-1][2]) < 0.05:
                merged[-1][2] += d
            else:
                merged.append([t, m, d])
        steps = [diatonic_index(m - t0, scale) for _, m, _ in merged]
        iv = [b - a for a, b in zip(steps[:-1], steps[1:]) if 0 < abs(b - a) <= 7]
        for g in zip(iv, iv[1:], iv[2:]):
            tri[g] = tri.get(g, 0) + 1
        for _, _, d in merged:
            e = int(round(d / (r.beat_s / 2)))
            if 1 <= e <= 8:
                ioi[e] += 1
    top = max(tri.values()) if tri else 1
    return {k: v / top for k, v in tri.items()}, ioi / max(1, ioi.sum())   # 最頻の音型 = 1.0


# ============================================================================ 2. 和声ループ (洗脳の土台)
def voicing_motion(a, b):
    """2 和音の最小の声部進行量 (半音の合計)。3 声を最良の対応で結ぶ。"""
    best = 99
    for perm in itertools.permutations(b):
        s = sum(min((y - x) % 12, (x - y) % 12) for x, y in zip(a, perm))
        best = min(best, s)
    return best


def choose_loop(refs, mode):
    names = list(CHORDS[mode])
    tonic = TONICS[mode]
    trans, outs = {}, {}
    for r in refs:
        seq = r.chords_in(mode)
        seq = [c for i, c in enumerate(seq) if i == 0 or c != seq[i - 1]]  # 同じ和音の連続は 1 つに
        for a, b in zip(seq, seq[1:]):
            trans[(a, b)] = trans.get((a, b), 0) + 1
            outs[a] = outs.get(a, 0) + 1
    pull = {('V', tonic), ('VII', tonic), ('iv', tonic), ('IV', tonic), ('v', tonic)}
    best = None
    for loop in itertools.product(names, repeat=4):
        if any(loop[i] == loop[(i + 1) % 4] for i in range(4)) or loop[0] != tonic and loop[0] not in ('VI', 'vi'):
            continue
        if tonic not in loop or len(set(loop)) < 4 or {'v', 'V'} <= set(loop):
            continue                     # 4 つとも違う和音で 1 周する (同じ和音に戻ると循環がぼやける)
        motion = sum(voicing_motion(CHORDS[mode][loop[i]], CHORDS[mode][loop[(i + 1) % 4]]) for i in range(4))
        # 手本区間の和音の進み方 (遷移確率) にどれだけ沿っているか
        ref = sum(trans.get((loop[i], loop[(i + 1) % 4]), 0) / max(1, outs.get(loop[i], 0)) for i in range(4)) / 4
        score = {
            'reference': 6.0 * ref,                                   # 手本区間に実際に現れる循環か
            'smooth': -0.25 * motion,                                 # 声部が滑らかに流れるか
            'endless': 1.5 if (loop[3], loop[0]) in pull else 0.0,    # 終わりが始まりへ吸い込まれる (循環が止まらない)
            'variety': 0.9 * len(set(loop)),                         # 4 和音すべて異なる
            'bass_fall': 0.5 if loop[:2] in (('i', 'VI'), ('i', 'VII'), ('I', 'vi'), ('vi', 'IV')) else 0.0,
            'no_v_minor': -1.0 if 'v' in loop else 0.0,               # 短調の v は導音が無く循環の引力が弱い
        }
        tot_s = sum(score.values())
        if best is None or tot_s > best[0]:
            best = (tot_s, loop, score)
    return best[1], best[2]


# ============================================================================ 3. 主題メロディー (流れのきれいさ)
RHYTHMS = [  # 1 小節 (4/4) の 8 分音符単位のリズム
    (2, 2, 2, 2), (3, 1, 2, 2), (2, 1, 1, 2, 2), (1, 1, 2, 2, 2), (3, 1, 4), (2, 2, 4), (4, 2, 2),
    (2, 1, 1, 4), (3, 1, 3, 1), (6, 2), (2, 6), (1, 1, 1, 1, 4), (3, 3, 2),
]


def choose_rhythm(ioi):
    """フック 2 小節のリズム (r1: 動く小節, r2: 息をつく小節)。手本の音価分布に近く、細かい→長いと流れるもの。"""
    best = None
    for r1 in RHYTHMS:
        for r2 in RHYTHMS:
            notes = list(r1) + list(r2)
            hist = np.bincount(notes, minlength=9)[:9] / len(notes)
            sim = 1 - 0.5 * np.abs(hist - ioi).sum()
            flow = (np.mean(r2) - np.mean(r1)) / 4             # 2 小節目の方が長い = 息をつく
            n = len(notes)
            density = -abs(n - 8) * 0.12                      # 2 小節で 8 音前後が口ずさめる
            dotted = 0.15 if 3 in r1 else 0.0                 # 付点のはずみは耳に残る
            ends_long = 0.3 if r2[-1] >= 4 else 0.0
            s = 2.0 * sim + flow + density + dotted + ends_long
            if best is None or s > best[0]:
                best = (s, r1, r2)
    return best[1], best[2]


class Theme:
    """主題 8 小節: A(1–2) A'(3–4, A の反復進行) A(5–6, 完全反復) B(7–8, 終止)。"""

    def __init__(self, mode, tonic_midi, loop, r1, r2, vocab):
        self.mode = mode
        self.scale = MINOR if mode == 'minor' else MAJOR
        self.t = tonic_midi
        self.loop = loop
        self.r1, self.r2 = r1, r2
        self.vocab = vocab
        lo, hi = tonic_midi - 5, tonic_midi + 16
        self.pitches = [m for m in range(lo, hi + 1) if (m - tonic_midi) % 12 in self.scale]

    def chord_at(self, bar):
        return CHORDS[self.mode][self.loop[bar % 4]]

    def allowed(self, m, bar):
        """音階音のみ。短調で V の小節では第 7 音を導音に上げる。"""
        ch = self.loop[bar % 4]
        pc = (m - self.t) % 12
        if self.mode == 'minor' and ch == 'V' and pc == 10:
            return m + 1
        return m

    def layout(self, A, Bnotes, shift):
        """音高の並び → (midi, 開始拍(8分), 長さ(8分), 小節) の列。"""
        out = []

        def bar_notes(rhythm, pitches, bar):
            pos = bar * 8
            for d, m in zip(rhythm, pitches):
                out.append((self.allowed(m, bar), pos, d, bar))
                pos += d
        na = len(self.r1)
        a1, a2 = A[:na], A[na:]
        bar_notes(self.r1, a1, 0)
        bar_notes(self.r2, a2, 1)
        sh = [self.shift(m, shift) for m in A]
        bar_notes(self.r1, sh[:na], 2)
        bar_notes(self.r2, sh[na:], 3)
        bar_notes(self.r1, a1, 4)
        bar_notes(self.r2, a2, 5)
        bar_notes(self.r1, Bnotes[:-1], 6)
        bar_notes((8,), Bnotes[-1:], 7)
        return out

    def shift(self, m, steps):
        i = self.pitches.index(m) if m in self.pitches else 0
        j = max(0, min(len(self.pitches) - 1, i + steps))
        return self.pitches[j]


def flow_beauty(notes, th, detail=False):
    """音符の流れのきれいさ。エントロピーは一切使わない — 作曲法の規則の点数の和。"""
    ms = [n[0] for n in notes]
    iv = [b - a for a, b in zip(ms[:-1], ms[1:])]
    s = {}
    moves = [abs(i) for i in iv if i != 0]
    steps = sum(1 for i in moves if i <= 2)
    s['順次進行'] = -4.0 * abs(steps / max(1, len(moves)) - 0.68)
    gap = 0.0
    for k in range(len(iv) - 1):
        if abs(iv[k]) >= 5:   # 跳躍の後は反対方向へ順次 (gap-fill)
            gap += 0.25 if (iv[k] * iv[k + 1] < 0 and abs(iv[k + 1]) <= 2) else -0.8
        if abs(iv[k]) >= 3 and abs(iv[k + 1]) >= 3 and iv[k] * iv[k + 1] > 0:
            a, b, c = ms[k] % 12, ms[k + 1] % 12, ms[k + 2] % 12
            chord = set(th.chord_at(notes[k][3])) | set(th.chord_at(notes[k + 2][3]))
            if not {(x - th.t) % 12 for x in (a, b, c)} <= chord:
                gap -= 0.7          # 同方向の跳躍の連続 (和音のアルペジオでなければ)
    s['跳躍の解決'] = gap
    bad = sum(1 for i in iv if abs(i) in (6, 10, 11) or abs(i) > 12)
    s['不協和な跳躍'] = -1.2 * bad
    rep3 = sum(1 for k in range(len(ms) - 2) if ms[k] == ms[k + 1] == ms[k + 2])
    rep2 = sum(1 for i in iv if i == 0)
    s['同音の停滞'] = -0.8 * rep3 - 0.25 * rep2
    osc = sum(1 for k in range(len(ms) - 4) if ms[k] == ms[k + 2] == ms[k + 4] and ms[k + 1] == ms[k + 3])
    s['往復の停滞'] = -0.6 * osc            # a-b-a-b-a の揺れ続けは流れが止まる
    top = max(ms)
    pos = [k for k, m in enumerate(ms) if m == top]
    s['頂点の一意性'] = 0.8 if len(set(n[3] // 2 for k, n in enumerate(notes) if ms[k] == top)) == 1 else -0.4
    if pos[-1] == len(ms) - 1:
        s['頂点の一意性'] -= 1.5          # 頂点で終わらない — 頂点の後は終止へ降りてくる
    cpos = notes[pos[0]][1] / (notes[-1][1] + notes[-1][2])
    s['黄金比の頂点'] = 1.2 - 10.0 * max(0.0, abs(cpos - 0.66) - 0.08)   # 頂点は全体の 6〜7 割あたり (黄金分割)
    rng_ = top - min(ms)
    s['音域'] = 1.0 if 9 <= rng_ <= 14 else -0.3 * min(abs(rng_ - 9), abs(rng_ - 14))
    s['歌う音域'] = -0.15 * abs(float(np.mean(ms)) - (th.t + 6))      # 主音の上の 5〜6 度を中心に歌う
    ct = nct = 0.0
    for k, (m, st, d, bar) in enumerate(notes):
        pc = (m - th.t) % 12
        chord = th.chord_at(bar)
        strong = st % 4 == 0
        if pc in chord:
            ct += 0.35 if strong else 0.1
        else:
            prev_ok = k > 0 and abs(m - ms[k - 1]) <= 2
            next_ok = k + 1 < len(ms) and abs(ms[k + 1] - m) <= 2
            if strong:
                nct -= 0.5 if not (next_ok and d <= 2) else 0.1    # 強拍の倚音は短く順次で解決するなら許す
            elif not (prev_ok and next_ok):
                nct -= 0.45                                          # 経過音・刺繍音でない非和声音
    s['強拍の和声音'] = 8.0 * ct / len(notes)
    s['非和声音の解決'] = nct
    lt = 0.0
    for k in range(len(ms) - 1):
        pc = (ms[k] - th.t) % 12
        if pc == 11:
            lt += 0.5 if (ms[k + 1] - ms[k]) == 1 else -1.2          # 導音 → 主音
    s['導音の解決'] = lt
    last, prev = notes[-1], notes[-2]
    cad = 0.0
    # 終わりの和音はループの最後 (主和音ではない)。主題は「開いた終止」で終え、頭へ吸い戻される — 洗脳の循環。
    lpc, lchord = (last[0] - th.t) % 12, th.chord_at(last[3])
    if lpc in lchord:
        cad += 1.5 if lpc in (0, 7) else 0.8
    else:
        cad -= 1.5
    cad += 0.6 if abs(last[0] - prev[0]) <= 2 else -0.3
    cad += 0.4 if last[2] >= 6 else 0.0
    s['終止'] = cad
    s['運動エネルギー'] = -0.012 * sum(i * i for i in iv)          # 曲線が滑らか = 跳躍の二乗和が小さい
    curv = [abs(b - a) for a, b in zip(iv[:-1], iv[1:])]
    s['曲率'] = -0.03 * sum(curv)
    # 手本区間との語彙一致 (音階上の音程 3 連)
    steps_ = [diatonic_index(m - th.t, th.scale) for m in ms]
    div = [b - a for a, b in zip(steps_[:-1], steps_[1:]) if b != a]   # 輪郭 (同音反復を除く)
    hits = sum(th.vocab.get(g, 0) for g in zip(div, div[1:], div[2:]))
    s['手本の語彙'] = 3.5 * hits / max(1, len(div) - 2)
    total = sum(s.values())
    return (total, s) if detail else total


def _local(notes, th):
    """ビームサーチ用の局所評価 (flow_beauty の部分集合)。"""
    if len(notes) < 2:
        return 0.0
    ms = [x[0] for x in notes]
    iv = [b - a for a, b in zip(ms[:-1], ms[1:])]
    sc = -0.012 * sum(i * i for i in iv) - 1.2 * sum(1 for i in iv if abs(i) in (6, 10, 11) or abs(i) > 9)
    for k in range(len(iv) - 1):
        if abs(iv[k]) >= 5:
            sc += 0.6 if (iv[k] * iv[k + 1] < 0 and abs(iv[k + 1]) <= 2) else -0.8
    for m, st, d, bar in notes:
        if st % 4 == 0:
            sc += 0.35 if (m - th.t) % 12 in th.chord_at(bar) else -0.4
    sc -= 0.8 * sum(1 for k in range(len(ms) - 2) if ms[k] == ms[k + 1] == ms[k + 2])
    sc -= 0.25 * sum(1 for i in iv if i == 0)
    sc -= 0.6 * sum(1 for k in range(len(ms) - 4) if ms[k] == ms[k + 2] == ms[k + 4] and ms[k + 1] == ms[k + 3])
    sc -= 0.15 * abs(float(np.mean(ms)) - (th.t + 6))
    st_ = [diatonic_index(m - th.t, th.scale) for m in ms]
    dv = [b - a for a, b in zip(st_[:-1], st_[1:]) if b != a]
    sc += 3.5 * sum(th.vocab.get(g, 0) for g in zip(dv, dv[1:], dv[2:])) / max(4, len(dv) - 2)
    return sc


def _beam(th, rhythm_bars, first_choices, beam, prev=None, final_tonic=False):
    """rhythm_bars = [(bar, rhythm), ...] に音高を割り当てるビームサーチ。"""
    slots = []
    for bar, r in rhythm_bars:
        pos = bar * 8
        for d in r:
            slots.append((pos, d, bar))
            pos += d
    beams = [([], 0.0)]
    for k, (pos, d, bar) in enumerate(slots):
        last = k == len(slots) - 1
        cands = []
        for seq, _ in beams:
            ref = seq[-1] if seq else prev
            pool = first_choices if (not seq and first_choices) else th.pitches
            if last and final_tonic:
                pool = [m for m in th.pitches if (th.allowed(m, bar) - th.t) % 12 in th.chord_at(bar)]
            for m in pool:
                if ref is not None and abs(m - ref) > 9:
                    continue
                s2 = seq + [m]
                notes = [(th.allowed(x, b), p, dd, b) for x, (p, dd, b) in zip(s2, slots)]
                if prev is not None:
                    notes = [(prev, slots[0][0] - 1, 1, slots[0][2])] + notes
                cands.append((s2, _local(notes, th)))
        cands.sort(key=lambda c: -c[1])
        # 多様性: 最後の音ごとに上位だけ残す (局所評価だけだと「動かない旋律」に偏るため)
        per, kept = {}, []
        cap = max(4, beam // len(th.pitches))
        for c in cands:
            key = (c[0][-1], c[0][-2] if len(c[0]) > 1 else None)
            if per.get(key, 0) < cap:
                per[key] = per.get(key, 0) + 1
                kept.append(c)
            if len(kept) >= beam:
                break
        beams = kept
    return [b[0] for b in beams]


def compose_theme(th, beam=300):
    """フック A (2 小節) と終止 B (2 小節) をビームサーチで候補化し、反復進行の幅と組み合わせを総当たりして
    8 小節全体の flow_beauty が最大のものを選ぶ。"""
    start = [m for m in th.pitches if (m - th.t) % 12 in th.chord_at(0)]
    As = _beam(th, [(0, th.r1), (1, th.r2)], start, beam)[:150]
    best = None
    for A in As:
        Bs = _beam(th, [(6, th.r1), (7, (8,))], None, 80, prev=A[-1], final_tonic=True)[:40]
        for shift in (-3, -2, -1, 1, 2, 3):
            for B in Bs:
                notes = th.layout(A, B, shift)
                sc = flow_beauty(notes, th)
                if best is None or sc > best[0]:
                    best = (sc, A, B, shift)
    _, A, B, shift = best
    notes = th.layout(A, B, shift)
    return notes, flow_beauty(notes, th, detail=True), shift


# ============================================================================ 4. 伴奏 (洗脳的オスティナート)
PATTERNS = {  # 1 小節 8 分 ×8。'B' = 低音の根音, 0/1/2 = 和音の 3 声 (下から), 3 = 最下声の 1 オクターブ上
    'rolling (分散和音の波)': ['B', 0, 1, 2, 3, 2, 1, 0],
    'alberti (アルベルティ)': [0, 2, 1, 2, 0, 2, 1, 2],
    'minimal (ミニマル反復)': [0, 1, 2, 1, 0, 1, 2, 1],
    'pendulum (振り子)': ['B', 1, 2, 3, 'B', 1, 2, 3],
    'cascade (下降の滝)': ['B', 3, 2, 1, 0, 1, 2, 3],
    'pulse (拍の脈動)': ['B', 'C', 'B', 'C', 'B', 'C', 'B', 'C'],  # C = 和音の同時打鍵
}


def voice_chords(th, center):
    """ループの各和音を 3 声の密集配置にし、循環全体の声部の動きが最小になる転回を選ぶ。"""
    opts = []
    for name in th.loop:
        pcs = CHORDS[th.mode][name]
        vs = []
        for inv in range(3):
            v = [pcs[(inv + j) % 3] for j in range(3)]
            base = th.t - 12 + v[0]
            while base < center - 6:
                base += 12
            while base >= center + 6:
                base -= 12
            notes = [base]
            for p in v[1:]:
                n = notes[-1] + ((th.t + p - notes[-1]) % 12 or 12)
                notes.append(n)
            vs.append(notes)
        opts.append(vs)
    best = None
    for pick in itertools.product(range(3), repeat=len(opts)):
        vv = [opts[i][p] for i, p in enumerate(pick)]
        mot = sum(sum(abs(a - b) for a, b in zip(vv[i], vv[(i + 1) % len(vv)])) for i in range(len(vv)))
        if best is None or mot < best[0]:
            best = (mot, vv)
    return best[1]


def choose_pattern(th, theme_notes, voicings):
    mel_lo = min(n[0] for n in theme_notes)
    held = np.zeros(64, bool)   # メロディーが音を伸ばしている 8 分の位置
    onset = np.zeros(64, bool)
    for m, st, d, bar in theme_notes:
        onset[st] = True
        held[st + 1:st + d] = True
    results = {}
    for name, pat in PATTERNS.items():
        tops, moves = [], []
        prev = None
        fill = clash = 0
        for bar in range(8):
            v = voicings[bar % 4]
            root = th.t - 24 + CHORDS[th.mode][th.loop[bar % 4]][0]
            for k, sym in enumerate(pat):
                ns = ([root] if sym == 'B' else v if sym == 'C' else [v[sym] if sym < 3 else v[0] + 12])
                tops.append(max(ns))
                if prev is not None:
                    moves.append(abs(max(ns) - prev))
                prev = max(ns)
                i = bar * 8 + k
                fill += held[i]
                clash += onset[i] and max(ns) >= mel_lo - 2
        s = {
            '隙間を埋める': 0.06 * fill,                         # 旋律が伸ばす所で伴奏が動く = 途切れない流れ
            '旋律と衝突しない': -0.08 * clash,
            '滑らかさ': -0.08 * float(np.mean(moves)),          # 伴奏自身の音の流れのきれいさ
            '音域の分離': 0.8 if max(tops) < mel_lo else -0.1 * (max(tops) - mel_lo + 1),
            '反復の催眠性': 0.25 * len(set(pat)) if len(set(pat)) <= 5 else 0.0,  # 少ない要素の反復ほど耳に残る
        }
        results[name] = (sum(s.values()), s)
    best = max(results, key=lambda k: results[k][0])
    return best, results


# ============================================================================ 5. 編曲 (形式) と MIDI
class Arr:
    def __init__(self, bpm):
        self.bpm = bpm
        self.ev = {}  # ch -> list of (start8, dur8, midi, vel)

    def add(self, ch, st, d, m, v):
        self.ev.setdefault(ch, []).append((st, d, int(m), int(max(1, min(127, v)))))


PROGRAMS = {0: 0, 1: 0, 2: 49, 3: 8, 4: 0, 5: 48, 6: 52}  # 旋律 piano / 伴奏 piano / 弦 / チェレスタ / 低音 piano / 対旋律弦 / 合唱


def arrange(th, theme, shift, pattern, voicings, bpm):
    """形式: 序 (4) – A1 – A2 – B (フックの展開) – A3 (頂点) – A4 (静) – 結 (4)。和声ループは一度も止まらない。"""
    arr = Arr(bpm)
    pat = PATTERNS[pattern]
    sections = [('Intro', 4), ('A1', 8), ('A2', 8), ('B', 8), ('A3', 8), ('A4', 8), ('Outro', 4)]
    markers, bar0 = [], 0
    for name, nbars in sections:
        markers.append((name, bar0))
        bar0 += nbars
    total_bars = bar0

    def sec_of(bar):
        for name, b in reversed(markers):
            if bar >= b:
                return name
    climax = max(n[0] for n in theme)
    # --- 伴奏オスティナート / 低音 / 弦パッド (全小節) ---
    for bar in range(total_bars):
        name = sec_of(bar)
        v = voicings[bar % 4]
        root = th.t - 24 + CHORDS[th.mode][th.loop[bar % 4]][0]
        acc_v = {'Intro': 52, 'A1': 50, 'A2': 56, 'B': 58, 'A3': 64, 'A4': 46, 'Outro': 44}[name]
        last = bar == total_bars - 1
        for k, sym in enumerate(pat):
            if last and k > 0:
                break
            ns = [root] if sym == 'B' else v if sym == 'C' else [v[sym] if sym < 3 else v[0] + 12]
            for n in ns:
                acc = 4 if k % 4 == 0 else 0
                arr.add(1, bar * 8 + k, 8 if last else 2, n, acc_v + acc - (6 if sym == 'B' else 0))
        if name != 'Intro' or bar >= 2:
            arr.add(4, bar * 8, 8, root, 58 if name in ('A3', 'B') else 50)
            if name in ('A2', 'B', 'A3'):
                arr.add(4, bar * 8, 8, root - 12, 40)
        if name in ('A2', 'B', 'A3', 'A4') or (name == 'Outro'):
            vel = {'A2': 46, 'B': 54, 'A3': 66, 'A4': 40, 'Outro': 36}[name]
            for n in v:
                arr.add(2, bar * 8, 8, n, vel)
            arr.add(2, bar * 8, 8, root + 12, vel - 6)
        if name == 'A3':
            for n in v:
                arr.add(6, bar * 8, 8, n + 12, 44)
    # --- 主題 ---
    def put_theme(start_bar, ch, vel_base, octave=0, double=False, counter=False, bars=range(8)):
        for m, st, d, bar in theme:
            if bar not in bars:
                continue
            # 頂点へ向かってクレッシェンド、終止へ向かってディミヌエンド (流れの抑揚)
            v = vel_base + 10 * (1 - abs(m - climax) / 12) + (4 if st % 8 == 0 else 0)
            t = start_bar * 8 + st
            arr.add(ch, t, d, m + octave, v)
            if double:
                arr.add(ch, t, d, m + octave - 12, v - 14)
            if counter:
                c = third_below(th, m, bar)
                if c is not None:
                    arr.add(5, t, d, c, v - 18)

    b = dict(markers)
    put_theme(b['A1'], 0, 70)
    put_theme(b['A2'], 0, 74)
    # B: フック A だけを、ループに沿った反復進行で 4 回 (原形 → 下 → 原形 → 上へ開く) — 一番耳に残る部分
    hook = [n for n in theme if n[3] in (0, 1)]
    for rep, sh in enumerate((0, shift, 0, shift)):
        for m, st, d, bar in hook:
            raw = m if m in th.pitches else m - 1           # 導音に上げた音は音階音へ戻してから移す
            mm = th.allowed(th.shift(raw, sh), bar + rep * 2)
            arr.add(0, (b['B'] + rep * 2) * 8 + st, d, mm, 72 + 4 * rep)
            arr.add(3, (b['B'] + rep * 2) * 8 + st, d, mm + 12, 40 + 6 * rep)  # チェレスタの影
    put_theme(b['A3'], 0, 84, octave=12, double=True, counter=True)
    put_theme(b['A4'], 0, 60)
    for m, st, d, bar in hook:   # 結: フックがもう一度だけ、遠くで
        arr.add(3, b['Outro'] * 8 + st, d, m + 12, 46)
        arr.add(0, b['Outro'] * 8 + st, d, m, 52)
    tonic_chord = [th.t - 12, th.t - 5, th.t + (3 if th.mode == 'minor' else 4), th.t + 7]
    for n in tonic_chord:
        arr.add(2, (total_bars - 1) * 8, 12, n, 42)
    arr.add(0, (total_bars - 1) * 8 + 4, 12, th.t + 12, 54)
    return arr, markers, total_bars


def third_below(th, m, bar):
    """対旋律: 旋律の 3 度下 (無ければ 6 度下) の和音音 — 弦で旋律に寄り添う。"""
    chord = th.chord_at(bar)
    for d in (3, 4, 8, 9):
        c = m - d
        if (c - th.t) % 12 in chord:
            return c
    for d in (3, 4):
        if (m - d - th.t) % 12 in th.scale:
            return m - d
    return None


def write_midi(arr, path):
    import mido
    tpb = 480
    mf = mido.MidiFile(ticks_per_beat=tpb)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(arr.bpm), time=0))
    meta.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    mf.tracks.append(meta)
    for ch, evs in sorted(arr.ev.items()):
        tr = mido.MidiTrack()
        tr.append(mido.Message('program_change', channel=ch, program=PROGRAMS[ch], time=0))
        tr.append(mido.Message('control_change', channel=ch, control=91, value=70, time=0))  # reverb send
        tr.append(mido.Message('control_change', channel=ch, control=10, value={0: 70, 1: 54, 2: 64, 3: 84, 4: 60, 5: 44, 6: 64}[ch], time=0))
        msgs = []
        for st, d, m, v in evs:
            on = st * tpb // 2
            off = (st + d) * tpb // 2 - (8 if ch in (0, 3) else 0)
            msgs.append((on, 1, mido.Message('note_on', channel=ch, note=m, velocity=v)))
            msgs.append((off, 0, mido.Message('note_off', channel=ch, note=m, velocity=0)))
        if ch in (1, 4):   # 伴奏はダンパーペダルを小節ごとに踏み替える
            last = max(st + d for st, d, _, _ in evs)
            for bar in range(0, last // 8 + 1):
                msgs.append((bar * 8 * tpb // 2 + 6, 2, mido.Message('control_change', channel=ch, control=64, value=100)))
                msgs.append(((bar + 1) * 8 * tpb // 2 - 4, 0, mido.Message('control_change', channel=ch, control=64, value=0)))
        msgs.sort(key=lambda x: (x[0], x[1]))
        t = 0
        for at, _, msg in msgs:
            tr.append(msg.copy(time=max(0, at - t)))
            t = max(t, at)
        mf.tracks.append(tr)
    mf.save(path)


# ============================================================================ 6. 音にする
def find_sf2():
    for p in ('/usr/share/sounds/sf2/FluidR3_GM.sf2', '/usr/share/sounds/sf2/default-GM.sf2',
              '/usr/share/soundfonts/FluidR3_GM.sf2', '/usr/share/soundfonts/default.sf2'):
        if os.path.exists(p):
            return p
    return None


def render_fluidsynth(mid, sf2, wav):
    subprocess.run(['fluidsynth', '-ni', '-q', '-F', wav, '-r', str(SR), '-g', '0.5',
                    '-o', 'synth.reverb.room-size=0.75', '-o', 'synth.reverb.width=0.9',
                    '-o', 'synth.reverb.level=0.6', '-o', 'synth.chorus.active=0', sf2, mid],
                   check=True, capture_output=True)
    sr, y = wavfile.read(wav)
    y = y.astype(np.float64) / (32768.0 if y.dtype == np.int16 else 1.0)
    return y if y.ndim == 2 else np.stack([y, y], 1)


def render_builtin(arr):
    """fluidsynth が無い時の内蔵音源: 減衰する加算合成のピアノと、ゆっくり立ち上がる弦。"""
    spb = 60.0 / arr.bpm / 2
    end = max(st + d for evs in arr.ev.values() for st, d, _, _ in evs)
    y = np.zeros((int((end * spb + 6) * SR), 2))
    for ch, evs in arr.ev.items():
        p = {0: .7, 1: .4, 2: .55, 3: .85, 4: .5, 5: .3, 6: .6}[ch]
        for st, d, m, v in evs:
            f = 440 * 2 ** ((m - 69) / 12)
            dur = d * spb + (1.5 if ch not in (2, 5, 6) else 0.8)
            t = np.arange(int(dur * SR)) / SR
            if ch in (2, 5, 6):
                env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.8)
                w = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.002 * k)) / k ** 1.5 for k in range(1, 6)) * 0.35
            else:
                env = np.exp(-t * (1.2 + m / 60)) * np.minimum(1, t / 0.004) * np.minimum(1, (dur - t) / 0.3)
                w = sum(np.sin(2 * np.pi * f * k * np.sqrt(1 + 0.0004 * k * k) * t) * np.exp(-t * k * 0.6) / k
                        for k in range(1, 7))
            s = w * env * (v / 127) ** 1.6 * 0.25
            a = int(st * spb * SR)
            y[a:a + len(s), 0] += s * np.cos(p * np.pi / 2)
            y[a:a + len(s), 1] += s * np.sin(p * np.pi / 2)
    return rq_reverb(y, 3.2, 0.35)


def rq_reverb(y, seconds, wet):
    rq.SR = SR
    out = rq.reverb(y, seconds=seconds, wet=wet, dry=1.0, damp_hz=4200, seed=3)
    return out[:len(y)]


def memory_bed(refs, th_tonic_pc, mode, dur_s):
    """手本区間 (2:30–3:00) そのものを目標の調へ移調し、深い残響の「記憶」として薄く敷く。"""
    import librosa
    bed = np.zeros(int(dur_s * SR))
    if not refs:
        return np.stack([bed, bed], 1)
    seg = dur_s / len(refs)
    for i, r in enumerate(refs):
        st = (r.rel_offset(mode) - th_tonic_pc) % 12
        st = -st if st <= 6 else 12 - st
        y = librosa.resample(r.y.astype(np.float32), orig_sr=ASR, target_sr=SR)
        y = librosa.effects.pitch_shift(y, sr=SR, n_steps=-st).astype(np.float64)
        y = librosa.effects.time_stretch(y, rate=0.5).astype(np.float64)   # 2 倍に引き延ばして朧げに
        n = min(len(y), int((seg + 8) * SR))
        y = rq.fade(y[:n], 4.0, 6.0)
        a = int(i * seg * SR)
        m = min(len(bed) - a, n)
        bed[a:a + m] += y[:m] / (np.sqrt(np.mean(y ** 2)) + 1e-9)
    bed = sg.sosfiltfilt(sg.butter(2, [180, 2600], 'band', fs=SR, output='sos'), bed)
    return rq_reverb(np.stack([bed, bed], 1), 6.0, 0.9)


def master(y):
    y = sg.sosfiltfilt(sg.butter(2, 30, 'high', fs=SR, output='sos'), y, axis=0)
    y = np.tanh(y / (np.max(np.abs(y)) + 1e-9) * 1.6) / np.tanh(1.6)
    return rq.normalize(y, -1.0)


def render_video(wav_path, out_path, markers, dur_s, size, fps, crf, title, report):
    """CQT スペクトル映像 (群青〜白金) + 主題と各部のタイトルカード。"""
    ff = rq.ffmpeg_exe()
    w, h = (int(v) for v in size.split('x'))
    latin, jp = rq.find_font(rq.LATIN_FONTS), rq.find_font(rq.JP_FONTS)
    ivory, dim, gold = (236, 232, 222), (178, 186, 200), (160, 200, 236)
    cards = []
    theme_line = ' '.join(t['note'] for t in report['theme'])
    if latin and jp:
        png = out_path + '.card0.png'
        if rq.render_card(png, w, h, [
                (title.upper(), latin, 0.11, 0.30, ivory),
                (f"in {report['key']}  ·  {report['tempo_bpm']} bpm  ·  {' – '.join(report['loop'])}", latin, 0.030, 0.45, gold),
                ('theme chosen by flow beauty, not entropy', latin, 0.026, 0.52, dim),
                ('2:30–3:00 を手本に — 主題と伴奏を洗脳的に作り換え', jp, 0.028, 0.58, dim),
                (theme_line, latin, 0.021, 0.66, dim)]):
            cards.append((png, 0.8, 12.0))
        for i, (at, mt, sub) in enumerate(markers):
            a, b = (sub.split(' — ') + [''])[:2]
            png = out_path + f'.card{i + 1}.png'
            rq.render_card(png, w, h, [(mt, latin, 0.060, 0.76, ivory), (a, latin, 0.026, 0.85, gold), (b, jp, 0.027, 0.90, dim)])
            cards.append((png, max(13.5, at + 0.5), 9.0))
    bar_h = (h * 2 // 3) // 2 * 2
    chain = [f"[0:a]showcqt=s={w}x{h}:r={fps}:axis=0:bar_h={bar_h}:sono_h={h - bar_h}:bar_g=4:sono_g=6:count=4:"
             f"sono_v=10:bar_v=16,colorchannelmixer=rr=0.35:rg=0.25:rb=0.25:gr=0.30:gg=0.55:gb=0.30:br=0.25:bg=0.45:bb=0.85[v0]"]
    cur = 'v0'
    cmd = [ff, '-y', '-v', 'error', '-stats', '-i', wav_path]
    for i, (png, start, d) in enumerate(cards):
        cmd += ['-loop', '1', '-framerate', str(fps), '-t', f'{d:.2f}', '-i', png]
        k = i + 1
        chain.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=1.5:alpha=1,fade=t=out:st={d - 2.5:.2f}:d=2.5:alpha=1,"
                     f"setpts=PTS-STARTPTS+{start:.2f}/TB[c{k}]")
        chain.append(f"[{cur}][c{k}]overlay=0:0:eof_action=pass:enable='between(t\\,{start:.2f}\\,{start + d:.2f})'[v{k}]")
        cur = f'v{k}'
    chain.append(f"[{cur}]fade=t=in:st=0:d=2,fade=t=out:st={dur_s - 5:.2f}:d=5,format=yuv420p[v]")
    cmd += ['-filter_complex', ';'.join(chain), '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'medium',
            '-crf', str(crf), '-pix_fmt', 'yuv420p', '-r', str(fps), '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart', '-t', f'{dur_s:.2f}', out_path]
    try:
        subprocess.run(cmd, check=True)
    finally:
        for png, _, _ in cards:
            if os.path.exists(png):
                os.remove(png)


# ============================================================================ 7. 全体
def choose_key(refs):
    w = {}
    for r in refs:
        k = (r.tonic, r.mode)
        w[k] = w.get(k, 0) + r.key_r
    return max(w, key=w.get)


def choose_tempo(refs):
    ts = []
    for r in refs:
        t = r.tempo
        while t >= 108:
            t /= 2
        while t < 54:
            t *= 2
        ts.append(t)
    return int(round(min(84, max(60, float(np.median(ts))))))


def build(refs, key=None, bpm=None, log=print):
    tonic_pc, mode = key or choose_key(refs)
    bpm = bpm or choose_tempo(refs)
    tonic_midi = 60 + tonic_pc if tonic_pc <= 7 else 48 + tonic_pc
    vocab, ioi = vocabulary(refs, mode)
    loop, loop_score = choose_loop(refs, mode)
    log(f'    調 {NN[tonic_pc]} {mode}   テンポ {bpm}   和声ループ {" – ".join(loop)}  ({_fmt(loop_score)})')
    r1, r2 = choose_rhythm(ioi)
    th = Theme(mode, tonic_midi, loop, r1, r2, vocab)
    theme, (fb, detail), shift = compose_theme(th)
    log(f'    フックのリズム {r1} + {r2}  反復進行 {shift:+d} 度   流れのきれいさ {fb:.2f}')
    log('    主題 ' + ' '.join(nm(n[0]) for n in theme))
    voicings = voice_chords(th, tonic_midi - 11)
    pattern, pat_scores = choose_pattern(th, theme, voicings)
    log(f'    伴奏 {pattern}  ({_fmt(pat_scores[pattern][1])})')
    arr, markers, nbars = arrange(th, theme, shift, pattern, voicings, bpm)
    report = {
        'key': f'{NN[tonic_pc]} {mode}', 'tempo_bpm': bpm,
        'references': [{'name': r.name, 'window': [round(r.a, 1), round(r.b, 1)], 'key': f'{NN[r.tonic]} {r.mode}',
                        'tempo': round(r.tempo, 1), 'melody_notes': len(r.notes)} for r in refs],
        'loop': list(loop), 'loop_score': {k: round(v, 3) for k, v in loop_score.items()},
        'hook_rhythm_eighths': [list(r1), list(r2)], 'sequence_shift_steps': shift,
        'theme': [{'note': nm(m), 'midi': m, 'bar': bar + 1, 'beat': st % 8 / 2 + 1, 'eighths': d} for m, st, d, bar in theme],
        'flow_beauty_total': round(fb, 3), 'flow_beauty': {k: round(v, 3) for k, v in detail.items()},
        'accompaniment': pattern,
        'accompaniment_scores': {k: {'total': round(v[0], 3), **{kk: round(vv, 3) for kk, vv in v[1].items()}}
                                 for k, v in pat_scores.items()},
        'form': [[n, b + 1] for n, b in markers], 'bars': nbars,
    }
    return arr, markers, report, (tonic_pc, mode)


def _fmt(d):
    return ', '.join(f'{k} {v:+.2f}' for k, v in d.items())


def render_audio(arr, refs, key, tmpdir, mid_path):
    write_midi(arr, mid_path)
    sf2 = find_sf2() if shutil.which('fluidsynth') else None
    if sf2:
        y = render_fluidsynth(mid_path, sf2, os.path.join(tmpdir, 'synth.wav'))
    else:
        y = render_builtin(arr)
    y = y / (np.max(np.abs(y)) + 1e-9)
    bed = memory_bed(refs, key[0], key[1], len(y) / SR)[:len(y)]
    if len(bed) < len(y):
        bed = np.concatenate([bed, np.zeros((len(y) - len(bed), 2))])
    bed = bed / (np.sqrt(np.mean(bed ** 2)) + 1e-9) * np.sqrt(np.mean(y ** 2)) * rq.db(-17)
    return master(y + bed)


def main():
    ap = argparse.ArgumentParser(description='録音の 2:30–3:00 を手本に、洗脳的な主題と伴奏で曲を作り換える')
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('-o', '--output', default='sennou.mp4')
    ap.add_argument('--each', default=None, help='入力 1 本ずつの作り換え (MP3) をこのフォルダにも書き出す')
    ap.add_argument('--no-video', action='store_true')
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--crf', type=int, default=30)
    ap.add_argument('--title', default='Sennou')
    args = ap.parse_args()
    rq.SR = SR
    out_dir = os.path.dirname(os.path.abspath(args.output))
    stem = os.path.splitext(args.output)[0]
    tmp = stem + '.tmp'
    os.makedirs(tmp, exist_ok=True)

    print('[1/4] 手本区間 (2:30–3:00) の解析')
    refs = [Reference(p) for p in args.inputs]
    for r in refs:
        print('   ', r.describe())
    print('[2/4] 作曲 (全録音をまとめて 1 曲)')
    arr, markers, report, key = build(refs, log=print)
    with open(stem + '.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print('[3/4] 演奏')
    y = render_audio(arr, refs, key, tmp, stem + '.mid')
    wav = os.path.join(tmp, 'mix.wav')
    wavfile.write(wav, SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    dur = len(y) / SR
    print(f'    {int(dur // 60)}:{int(dur % 60):02d}')
    if not args.no_video:
        print('[4/4] 映像', args.output)
        spbar = 4 * 60.0 / arr.bpm
        names = {'Intro': ('Intro', 'loop — 循環が始まる'), 'A1': ('Theme', '主題 — A A\' A B'),
                 'A2': ('Theme II', '弦と低音が加わる'), 'B': ('Hook', 'フックの反復進行 — 洗脳'),
                 'A3': ('Theme III', '頂点 — オクターブと対旋律'), 'A4': ('Theme IV', '静けさへ'),
                 'Outro': ('Coda', 'フックの残響')}
        mk = [(b * spbar, names[n][0], f'{report["key"]} · {" – ".join(report["loop"])} — {names[n][1]}')
              for n, b in markers if n != 'Intro']
        render_video(wav, args.output, mk, dur, args.size, args.fps, args.crf, args.title, report)
    else:
        subprocess.run([rq.ffmpeg_exe(), '-y', '-v', 'error', '-i', wav, '-b:a', '192k', stem + '.mp3'], check=True)
    if args.each:
        os.makedirs(args.each, exist_ok=True)
        for r in refs:
            print(f'[each] {r.name}')
            a2, _, rep2, k2 = build([r], key=(r.tonic, r.mode), log=lambda s: print('   ', s.strip()))
            base = os.path.join(args.each, r.name)
            with open(base + '.json', 'w', encoding='utf-8') as f:
                json.dump(rep2, f, ensure_ascii=False, indent=1)
            y2 = render_audio(a2, [r], k2, tmp, base + '.mid')
            w2 = os.path.join(tmp, 'each.wav')
            wavfile.write(w2, SR, (np.clip(y2, -1, 1) * 32767).astype(np.int16))
            subprocess.run([rq.ffmpeg_exe(), '-y', '-v', 'error', '-i', w2, '-b:a', '160k', base + '.mp3'], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print('done')


if __name__ == '__main__':
    main()
