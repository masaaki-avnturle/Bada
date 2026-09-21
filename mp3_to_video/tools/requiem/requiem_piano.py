#!/usr/bin/env python3
"""requiem_piano.py — 録音した旋律を、グランドピアノのレクイエム調ソロに編曲してレンダリングする。

使い方:
  python3 requiem_piano.py --notes a1_notes.json a2_notes.json --samples piano/ --out requiem.wav

  * --notes   : melody_extract.py が出力した音符 JSON(複数可。順に楽章として並ぶ)
  * --samples : 88 鍵ぶんの WAV(A0.wav … C8.wav, 44.1kHz mono)が入ったフォルダ
  * --out     : 出力 WAV(44.1kHz stereo)。あわせて <out>.events.json(音符イベント)も書く

依存: numpy, scipy
"""
import argparse, json, math, os, random
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve

SR = 44100
NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# ---------------------------------------------------------------- 調・和声
KEY = 5                                 # F
SCALE = {5, 7, 8, 10, 0, 1, 3, 4}       # F G Ab Bb C Db Eb (+E: 導音)
CHORDS = {                              # 名前: (ルート pc, 構成音 pc, 長三和音か)
    "i":   (5,  [5, 8, 0],  False),
    "VI":  (1,  [1, 5, 8],  True),
    "iv":  (10, [10, 1, 5], False),
    "V":   (0,  [0, 4, 7],  True),
    "III": (8,  [8, 0, 3],  True),
    "VII": (3,  [3, 7, 10], True),
    "iio": (7,  [7, 10, 1], False),
    "v":   (0,  [0, 3, 7],  False),
}
PREF = ["i", "VI", "iv", "V", "III", "VII", "iio", "v"]


def snap(p):
    """最も近い音階音へ寄せる(同距離なら下へ)。"""
    best = None
    for d in (0, -1, 1, -2, 2):
        if (p + d) % 12 in SCALE:
            best = p + d
            break
    return best if best is not None else p


def name(p):
    return "%s%d" % (NAMES[p % 12], p // 12 - 1)


# ---------------------------------------------------------------- 旋律の整形
def prepare_melody(notes, lo=60, hi=81, grid=0.5, min_d=0.2, max_leap=9):
    """録音から取った音符列 → 音階へ吸着・音域へ折り畳み・グリッドへ量子化。
    戻り値: [(beat, dur_beats, midi, energy 0..1)] (beat は旋律開始からの拍。1拍=1秒として量子化)
    """
    keep = [n for n in notes if n["d"] >= min_d]
    if not keep:
        return []
    t0 = keep[0]["t"]
    emax = max(n["v"] for n in keep) or 1.0
    out, prev = [], None
    for n in keep:
        p = snap(n["p"])
        while p < lo: p += 12
        while p > hi: p -= 12
        if prev is not None:
            while p - prev > max_leap and p - 12 >= lo: p -= 12
            while prev - p > max_leap and p + 12 <= hi: p += 12
        t = round((n["t"] - t0) / grid) * grid
        d = max(grid, round(n["d"] / grid) * grid)
        e = n["v"] / emax
        if out and out[-1][0] == t:          # 同じ拍に重なったら長い方を残す
            if d <= out[-1][1]:
                continue
            out.pop()
        out.append([t, d, p, e])
        prev = p
    for i in range(len(out) - 1):            # 重なりを解消
        out[i][1] = min(out[i][1], out[i + 1][0] - out[i][0])
    return [tuple(o) for o in out]


def harmonize(melody, start_beat, n_beats, seg=4, final="i"):
    """seg 拍ごとに旋律へ最も合う和音を選ぶ。戻り値: [(beat, chord_name)]"""
    result, prev = [], None
    n_seg = int(math.ceil(n_beats / seg))
    for k in range(n_seg):
        b0 = start_beat + k * seg
        w = {}
        for (t, d, p, e) in melody:
            a, b = max(t, b0), min(t + d, b0 + seg)
            if b > a:
                w[p % 12] = w.get(p % 12, 0.0) + (b - a) * (0.5 + e)
        scores = []
        for i, cname in enumerate(PREF):
            root, pcs, _ = CHORDS[cname]
            s = sum(w.get(pc, 0.0) for pc in pcs) * 1.0
            s += 0.6 * w.get(root, 0.0)                      # ルートが旋律にあると強い
            s -= 0.25 * sum(v for pc, v in w.items() if pc not in pcs)
            s -= 0.02 * i                                    # 好みの順
            if cname == prev:
                s -= 0.35                                    # 同じ和音の連続は避けめ
            scores.append((s, cname))
        scores.sort(reverse=True)
        c = scores[0][1]
        if k == n_seg - 1:
            c = final
        elif k == n_seg - 2 and (not w or all(pc in CHORDS["V"][1] for pc in w)):
            c = "V"
        result.append((b0, c))
        prev = c
    return result


# ---------------------------------------------------------------- 伴奏パターン
def bass_of(cname, octave=2):
    root = CHORDS[cname][0]
    p = root + 12 * (octave + 1)
    if p < 36: p += 12
    return p


def chord_tones(cname, base):
    """base(ルートの MIDI)を基準に、ルート・3度・5度・オクターブ"""
    _, pcs, _ = CHORDS[cname]
    root = base
    third = base + ((pcs[1] - pcs[0]) % 12)
    fifth = base + ((pcs[2] - pcs[0]) % 12)
    return root, third, fifth, root + 12


def lh_arpeggio(ev, b0, cname, vel, beats=4):
    """流れるような八分の分散和音(ヘ短調の低〜中音域)"""
    r, t, f, o = chord_tones(cname, bass_of(cname))
    pat = [r, f, o, t + 12, f + 12, t + 12, o, f]
    for i in range(int(beats * 2)):
        p = pat[i % 8]
        v = vel + (6 if i == 0 else 0) - (4 if i % 2 else 0)
        ev.append((b0 + i * 0.5, 0.5, p, v, "L"))
    ev.append((b0, beats, r - 12, vel - 2, "L"))        # オクターブ下の低音を保持


def lh_chorale(ev, b0, cname, vel, beats=4):
    """賛美歌風の重い和音: 1拍目に低音オクターブ+和音、3拍目に和音を静かに"""
    r, t, f, o = chord_tones(cname, bass_of(cname))
    ev.append((b0, beats, r - 12, vel + 4, "L"))
    ev.append((b0, beats, r, vel + 2, "L"))
    for p in (t + 12, f + 12, o + 12):
        ev.append((b0, beats / 2, p, vel - 6, "L"))
    if beats >= 4:
        ev.append((b0 + 2, beats / 2, f, vel - 8, "L"))
        for p in (t + 12, o + 12):
            ev.append((b0 + 2, beats / 2, p, vel - 12, "L"))


def bell(ev, b0, vel, dur=4):
    ev.append((b0, dur, 29, vel, "L"))          # F1
    ev.append((b0, dur, 41, vel - 6, "L"))      # F2


DIES_IRAE = [68, 67, 68, 65, 67, 63, 65, 65]    # Ab G Ab F G Eb F F(ヘ短調へ移した怒りの日の旋律)


def motif(ev, b0, vel, oct_shift=0, step=1.0, part="M"):
    for i, p in enumerate(DIES_IRAE):
        d = step * (2 if i == len(DIES_IRAE) - 1 else 1)
        ev.append((b0 + i * step, d, p + oct_shift, vel - (0 if i in (0, 3) else 6), part))


# ---------------------------------------------------------------- 楽曲の組み立て
def build_score(melodies, seed=7):
    """戻り値: (events [(beat, dur, midi, vel, part)], pedal [(beat)], tempo_map [(beat, bpm)], sections)"""
    random.seed(seed)
    ev, pedal, sections = [], [], []
    b = 0.0

    # --- 序奏: 鐘と「怒りの日」 (8小節)
    sections.append(("intro", b))
    for bar in range(8):
        bell(ev, b + bar * 4, 44 + (bar % 2) * 3)
        pedal.append(b + bar * 4)
    ev.append((b + 0, 8, 77, 30, "M")); ev.append((b + 0, 8, 84, 26, "M"))       # 冷たい光 F5+C6
    motif(ev, b + 8, 46, 0, 1.0, "M")                                              # テノール域
    motif(ev, b + 17, 52, 12, 1.0, "M")                                            # 1オクターブ上で応答
    ev.append((b + 26, 2, 65 + 12, 40, "M")); ev.append((b + 28, 4, 64 + 12, 38, "M"))  # F→E(導音)で止まる
    ev.append((b + 28, 4, 48, 40, "L")); ev.append((b + 28, 4, 36, 40, "L"))       # C の低音(属音)
    pedal.append(b + 28)
    b += 32

    # --- 第1楽章: 録音1の旋律 + 分散和音
    m1 = [(t + b, d, p, e) for (t, d, p, e) in melodies[0]]
    n1 = int(math.ceil((m1[-1][0] + m1[-1][1] - b) / 4.0)) * 4 + 4
    sections.append(("A", b))
    h1 = harmonize(m1, b, n1, seg=4, final="i")
    for k, (b0, c) in enumerate(h1):
        prog = k / max(1, len(h1) - 1)
        base = 46 + int(10 * math.sin(prog * math.pi))             # 中盤で少し膨らむ
        lh_arpeggio(ev, b0, c, base)
        pedal.append(b0)
    for (t, d, p, e) in m1:
        v = int(58 + 30 * e)
        ev.append((t, d, p, v, "M"))
        if d >= 2.0 and p >= 67:                                   # 長い音には下3度(または6度)の内声
            q = snap(p - 3) if (p - 3) % 12 in SCALE else snap(p - 4)
            ev.append((t, d, q, v - 18, "M"))
    b += n1

    # --- 間奏 (4小節): 属和音上で沈む
    sections.append(("interlude", b))
    for k, c in enumerate(["i", "VI", "iio", "V"]):
        lh_arpeggio(ev, b + k * 4, c, 44)
        pedal.append(b + k * 4)
    motif(ev, b + 4, 50, 12, 1.0, "M")
    ev.append((b + 13, 3, 76, 44, "M"))                            # E5 (導音) で待つ
    b += 16

    # --- 第2楽章: 録音2の旋律 + 賛美歌風の和音(クライマックス)
    m2 = [(t + b, d, p, e) for (t, d, p, e) in melodies[1]]
    n2 = int(math.ceil((m2[-1][0] + m2[-1][1] - b) / 4.0)) * 4 + 4
    sections.append(("B", b))
    h2 = harmonize(m2, b, n2, seg=2, final="i")
    peak = max(m2, key=lambda x: x[3])[0]
    for k, (b0, c) in enumerate(h2):
        dist = abs(b0 - peak) / 24.0
        base = int(62 - 16 * min(1.0, dist))                       # クライマックス付近で強く
        if k % 2 == 0:
            lh_chorale(ev, b0, c, base, beats=2)
            ev.append((b0, 2, bass_of(c) - 12, base + 2, "L"))
        else:
            r, t, f, o = chord_tones(c, bass_of(c))
            for p in (f, t + 12, o + 12):
                ev.append((b0, 2, p, base - 10, "L"))
        pedal.append(b0)
    for (t, d, p, e) in m2:
        v = int(64 + 34 * e)
        ev.append((t, d, p, v, "M"))
        if abs(t - peak) < 16:                                     # クライマックス: オクターブ重ね
            ev.append((t, d, p + 12, v - 8, "M"))
            ev.append((t, d, p - 12, v - 14, "M"))
        elif d >= 2.0:
            q = snap(p - 3) if (p - 3) % 12 in SCALE else snap(p - 4)
            ev.append((t, d, q, v - 16, "M"))
    b += n2

    # --- 終結: 鐘が遠ざかり、ピカルディの三度(ヘ長調)で光の中に消える
    sections.append(("coda", b))
    for bar in range(4):
        bell(ev, b + bar * 4, 44 - bar * 6)
        pedal.append(b + bar * 4)
    motif(ev, b + 1, 42, 0, 1.0, "M")
    motif(ev, b + 9, 34, -12, 1.0, "M")
    fin = b + 16
    pedal.append(fin)
    for i, p in enumerate((29, 41, 48, 53, 57, 60, 65, 69, 72)):   # F1 F2 C3 F3 A3 C4 F4 A4 C5 ゆっくり積む
        ev.append((fin + i * 0.35, 12, p, 40 - i, "M" if p >= 60 else "L"))
    end_beat = fin + 12
    tempo_map = [(0, 58), (b - 8, 58), (b, 50), (fin, 44), (end_beat, 40)]
    return ev, sorted(set(pedal)), tempo_map, sections, end_beat


def make_time_fn(tempo_map):
    """拍 → 秒 (テンポマップを線形補間して積分)"""
    beats = [x[0] for x in tempo_map]; bpms = [x[1] for x in tempo_map]
    knots = [0.0]
    for i in range(1, len(beats)):
        nb = beats[i] - beats[i - 1]
        avg = (bpms[i - 1] + bpms[i]) / 2.0
        knots.append(knots[-1] + nb * 60.0 / avg)

    def f(beat):
        if beat <= beats[0]:
            return beat * 60.0 / bpms[0]
        for i in range(1, len(beats)):
            if beat <= beats[i]:
                u = (beat - beats[i - 1]) / (beats[i] - beats[i - 1])
                bpm_here = bpms[i - 1] + u * (bpms[i] - bpms[i - 1])
                avg = (bpms[i - 1] + bpm_here) / 2.0
                return knots[i - 1] + (beat - beats[i - 1]) * 60.0 / avg
        return knots[-1] + (beat - beats[-1]) * 60.0 / bpms[-1]
    return f


# ---------------------------------------------------------------- ピアノ音源
class Piano:
    def __init__(self, folder):
        self.s = {}
        for m in range(21, 109):
            path = os.path.join(folder, name(m) + ".wav")
            sr, x = wavfile.read(path)
            x = x.astype(np.float32) / 32768.0
            if x.ndim > 1: x = x.mean(1)
            x = x / (np.abs(x).max() + 1e-9)
            self.s[m] = self._extend(x, m)

    @staticmethod
    def _extend(x, m, total=9.0):
        """短く切れたサンプルの尾を、音高に応じた減衰時定数でループ延長する。
        0.55〜0.95 秒の区間をその区間自身の減衰で平らにしてから、目標の指数減衰を掛けて繰り返す。"""
        n = len(x)
        tau = 4.5 if m < 48 else (2.8 if m < 72 else (1.2 if m < 84 else 0.5))
        a, b = int(0.55 * SR), int(0.95 * SR)
        if m >= 84 or n < b + SR // 4:
            return x
        seg = x[a:b].astype(np.float64)
        L = len(seg)
        env_a = np.sqrt(np.mean(seg[:4410] ** 2)) + 1e-9
        env_b = np.sqrt(np.mean(seg[-4410:] ** 2)) + 1e-9
        k = math.log(env_a / env_b) / L                  # サンプル固有の減衰率(1サンプルあたり)
        flat = seg * np.exp(k * np.arange(L))            # 平らにした 1 周期ぶん
        flat *= env_b / (np.sqrt(np.mean(flat[-4410:] ** 2)) + 1e-9)
        xf = int(0.08 * SR)
        fade_in = np.linspace(0, 1, xf)
        out = np.zeros(int(total * SR), dtype=np.float64)
        out[:b] = x[:b]
        pos = b - xf
        while pos + L < len(out):
            t_rel = (np.arange(L) + pos - b) / SR
            piece = flat * np.exp(-t_rel / tau)
            out[pos:pos + xf] = out[pos:pos + xf] * (1 - fade_in) + piece[:xf] * fade_in
            out[pos + xf:pos + L] = piece[xf:]
            pos += L - xf
            if np.abs(piece).max() < 0.01: break
        out = out[:pos + xf]
        tail = int(0.05 * SR)
        out[-tail:] *= np.linspace(1, 0, tail)
        return out.astype(np.float32)

    def note(self, m, vel, dur):
        x = self.s[m]
        n = min(len(x), int(dur * SR))
        y = x[:n].copy()
        g = (vel / 127.0) ** 1.6 * 0.9 + 0.05
        # 弱い打鍵ほど丸い音(1次ローパス)
        cutoff = 1500 + (vel / 127.0) ** 2 * 9000
        alpha = math.exp(-2 * math.pi * cutoff / SR)
        y = _onepole(y, alpha)
        rel = min(n, int(0.25 * SR))
        y[-rel:] *= np.linspace(1, 0, rel) ** 0.6
        return y * g


def _onepole(x, a):
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x).astype(np.float32)


def render(events, pedal, tfn, end_beat, piano, seed=7):
    random.seed(seed)
    total = tfn(end_beat) + 6.0
    L = int(total * SR)
    out = np.zeros((L, 2), dtype=np.float32)
    ped = [tfn(p) for p in pedal] + [1e9]
    rendered = []
    for (beat, dur, m, vel, part) in events:
        if m not in piano.s or vel <= 0:
            continue
        t0 = tfn(beat) + random.uniform(-0.012, 0.012) + (0.008 if part == "M" else 0.0)
        t1 = tfn(beat + dur)
        # ダンパーペダル: 次のペダル踏み替えまで鳴り続ける
        nxt = next(p for p in ped if p > t0 + 0.02)
        t_end = max(t1, nxt) + 0.4
        dur_s = min(t_end - t0, 9.0)
        v = int(max(1, min(127, vel + random.randint(-3, 3))))
        y = piano.note(m, v, dur_s)
        pan = max(-0.55, min(0.55, (m - 60) / 36.0))
        gl, gr = math.sqrt(0.5 * (1 - pan)), math.sqrt(0.5 * (1 + pan))
        i0 = int(max(0, t0) * SR)
        n = min(len(y), L - i0)
        if n <= 0: continue
        out[i0:i0 + n, 0] += y[:n] * gl
        out[i0:i0 + n, 1] += y[:n] * gr
        rendered.append({"t": round(t0, 3), "d": round(t1 - t0, 3), "p": m, "v": v, "part": part})
    return out, rendered


def reverb(x, size=2.6, tau=0.95, mix=0.24, predelay=0.02):
    n = int(size * SR)
    rng = np.random.default_rng(3)
    t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1).astype(np.float32)
    ir *= np.exp(-t / tau)[:, None]
    ir = _onepole(ir[:, 0], math.exp(-2 * math.pi * 3800 / SR))[:, None].repeat(2, 1) * 0.5 + \
         np.stack([_onepole(ir[:, 0], math.exp(-2 * math.pi * 5000 / SR)),
                   _onepole(ir[:, 1], math.exp(-2 * math.pi * 5000 / SR))], 1) * 0.5
    ir[: int(predelay * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(0)).max() * 4.0
    wet = np.stack([fftconvolve(x[:, 0], ir[:, 0])[: len(x)], fftconvolve(x[:, 1], ir[:, 1])[: len(x)]], 1)
    return x * (1 - mix * 0.6) + wet * mix


def master(x, peak_db=-1.0):
    x = x - x.mean(0)
    # やわらかいリミッタ
    thr = 0.7
    a = np.abs(x)
    over = a > thr
    x[over] = np.sign(x[over]) * (thr + (a[over] - thr) / (1 + (a[over] - thr) * 6))
    x *= 10 ** (peak_db / 20) / (np.abs(x).max() + 1e-9)
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", nargs="+", required=True)
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    melodies = [prepare_melody(json.load(open(p))) for p in args.notes]
    for i, m in enumerate(melodies):
        print("melody %d: %d notes, %.0f beats" % (i + 1, len(m), m[-1][0] + m[-1][1]))
        print("  " + " ".join(name(p) for (_, _, p, _) in m[:40]) + (" ..." if len(m) > 40 else ""))
    ev, pedal, tempo_map, sections, end_beat = build_score(melodies)
    tfn = make_time_fn(tempo_map)
    print("score: %d events, %.0f beats, %.1f s" % (len(ev), end_beat, tfn(end_beat)))
    for s, b in sections:
        print("  section %-10s beat %4.0f  %6.1f s" % (s, b, tfn(b)))
    piano = Piano(args.samples)
    x, rendered = render(ev, pedal, tfn, end_beat, piano)
    x = reverb(x)
    x = master(x)
    audible = np.where(np.abs(x).max(1) > 10 ** (-60 / 20))[0]
    x = x[: min(len(x), audible[-1] + int(2.5 * SR))]           # 末尾の無音を 2.5 秒に整える
    wavfile.write(args.out, SR, (x * 32767).astype(np.int16))
    meta = {"sr": SR, "duration": len(x) / SR,
            "sections": [{"name": s, "t": round(tfn(b), 3)} for s, b in sections],
            "events": rendered}
    json.dump(meta, open(args.out + ".events.json", "w"))
    print("wrote", args.out, "%.1f s" % (len(x) / SR))


if __name__ == "__main__":
    main()
