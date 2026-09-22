"""
sampler.py — サウンドフォント(録音された本物の楽器)で楽譜を演奏するミキサー。

synth.Mixer と同じインターフェース(note / place / stereo / render)なので、
compose.Section をそのまま使える。音源は General MIDI サウンドフォント(FluidR3_GM など)、
再生は tinysoundfont(TinySoundFont の Python バインディング)。

  楽器名 → GM プリセット
    piano     0  Yamaha Grand Piano       violin   40   viola    41   cello   42   contrabass 43
    strings  48  Strings(合奏)           strings_slow 49 Slow Strings(パッド)
    harp     46  flute 73  oboe 68  clarinet 71  bassoon 70  horn 60
    choir    52  Ahh Choir   timpani 47   glock 9   bell 14 Tubular Bells   organ 19

パンは音符ごとに 9 段階へ量子化し、段階ごとに MIDI チャンネルを分けて CC10 で定位する。
リバーブは synth.reverb(合成 IR の畳み込み)を送りバスに掛ける。
"""
import os
import numpy as np
import tinysoundfont as tsf
from synth import SR, reverb

SF2 = os.environ.get("SF2", os.path.join(os.path.dirname(__file__), "FluidR3_GM.sf2"))

PRESETS = {
    "piano": 0, "violin": 40, "viola": 41, "cello": 42, "contrabass": 43,
    "strings": 48, "strings_slow": 49, "harp": 46, "flute": 73, "oboe": 68,
    "clarinet": 71, "bassoon": 70, "horn": 60, "choir": 52, "timpani": 47,
    "glock": 9, "bell": 14, "organ": 19,
}
# リバーブ送り量
SEND = {"piano": 0.3, "violin": 0.45, "viola": 0.45, "cello": 0.4, "contrabass": 0.3,
        "strings": 0.5, "strings_slow": 0.6, "harp": 0.45, "flute": 0.5, "oboe": 0.45,
        "clarinet": 0.45, "bassoon": 0.4, "horn": 0.5, "choir": 0.65, "timpani": 0.4,
        "glock": 0.55, "bell": 0.6, "organ": 0.45}
# 楽器ごとの音量補正(サウンドフォントの音量差を揃える)
TRIM = {"piano": 1.8, "violin": 1.0, "viola": 1.0, "cello": 1.0, "contrabass": 1.0,
        "strings": 0.7, "strings_slow": 0.55, "harp": 1.0, "flute": 1.6, "oboe": 1.2,
        "clarinet": 1.2, "bassoon": 1.1, "horn": 0.5, "choir": 0.6, "timpani": 0.9,
        "glock": 1.4, "bell": 0.8, "organ": 0.5}
BLOCK = 256
PAN_STEPS = 9


class SFMixer:
    def __init__(self, total_seconds):
        self.n = int(total_seconds * SR)
        self.dry = np.zeros((self.n, 2), dtype=np.float32)
        self.send = np.zeros((self.n, 2), dtype=np.float32)
        self.events = {}   # inst -> list of (start_sample, end_sample, key, vel127, pan_idx, gain)

    # --- synth.Mixer 互換
    def note(self, inst, start_sec, midi, hold_sec, vel=0.7, pan=0.0, gain=1.0, **kw):
        if inst not in PRESETS:
            raise KeyError(inst)
        i0 = int(start_sec * SR)
        i1 = int((start_sec + max(hold_sec, 0.05)) * SR)
        if i0 >= self.n:
            return
        v = int(np.clip(1 + 126 * vel, 1, 127))
        p = int(round((np.clip(pan, -1, 1) + 1) / 2 * (PAN_STEPS - 1)))
        self.events.setdefault(inst, []).append((i0, min(i1, self.n - 1), int(midi), v, p, gain))

    def place(self, buf, start_sec, pan=0.0, gain=1.0, send=0.0):
        i = int(start_sec * SR)
        buf = buf[: self.n - i]
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        self.dry[i:i + len(buf), 0] += buf * l * gain
        self.dry[i:i + len(buf), 1] += buf * r * gain
        if send > 0:
            self.send[i:i + len(buf), 0] += buf * l * gain * send
            self.send[i:i + len(buf), 1] += buf * r * gain * send

    def stereo(self, buf, start_sec, gain=1.0, send=0.0):
        i = int(start_sec * SR)
        buf = buf[: self.n - i]
        self.dry[i:i + len(buf)] += buf * gain
        if send > 0:
            self.send[i:i + len(buf)] += buf * gain * send

    # --- レンダリング
    def _render_inst(self, inst, evs):
        synth = tsf.Synth(samplerate=SR)
        sfid = synth.sfload(SF2)
        for ch in range(PAN_STEPS):
            synth.program_select(ch, sfid, 0, PRESETS[inst])
            synth.control_change(ch, 10, int(ch * 127 / (PAN_STEPS - 1)))
            synth.control_change(ch, 91, 0)   # 内蔵リバーブは使わない
        # ゲイン別に分けるほどではないので、gain は音量 CC7 の代わりに velocity へ畳み込む
        ons, offs = {}, {}
        for i0, i1, key, v, p, g in evs:
            b0, b1 = i0 // BLOCK, max(i1 // BLOCK, i0 // BLOCK + 1)
            ons.setdefault(b0, []).append((p, key, int(np.clip(v * g, 1, 127))))
            offs.setdefault(b1, []).append((p, key))
        last = max(offs) + int(6 * SR / BLOCK)   # 残響(リリース)分
        n_blocks = min(last, self.n // BLOCK)
        out = np.zeros((n_blocks * BLOCK, 2), dtype=np.float32)
        for b in range(n_blocks):
            for p, key in offs.get(b, ()):
                synth.noteoff(p, key)
            for p, key, v in ons.get(b, ()):
                synth.noteon(p, key, v)
            buf = synth.generate(BLOCK)
            out[b * BLOCK:(b + 1) * BLOCK] = np.frombuffer(buf, dtype=np.float32).reshape(-1, 2)
        synth.sfunload(sfid)
        return out * TRIM[inst]

    def render(self, ir, wet=0.9):
        for inst, evs in self.events.items():
            print(f"  [sampler] {inst:13s} {len(evs):5d} notes", flush=True)
            x = self._render_inst(inst, evs)
            act = x[np.abs(x).max(axis=1) > 1e-4]
            if len(act):
                print(f"             rms={20 * np.log10(np.sqrt((act ** 2).mean()) + 1e-9):6.1f} dBFS peak={np.abs(x).max():.3f}", flush=True)
            self.dry[: len(x)] += x
            self.send[: len(x)] += x * SEND[inst]
        return self.dry + reverb(self.send, ir) * wet
