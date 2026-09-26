# -*- coding: utf-8 -*-
"""midi.py — fugues.json → Standard MIDI File (format 1, 4 tracks = 4 voices)。依存ライブラリなし。"""
import json, os, sys, struct

BPM = 100
TPQ = 480
PROGRAMS = [42, 41, 41, 40]   # cello, viola, viola, violin (GM)

def vlq(n):
    out = [n & 0x7F]; n >>= 7
    while n: out.append((n & 0x7F) | 0x80); n >>= 7
    return bytes(reversed(out))

def track(events):
    """events: list of (tick, bytes) -> chunk"""
    events.sort(key=lambda e: e[0])
    data = b''; last = 0
    for tick, ev in events:
        data += vlq(tick - last) + ev; last = tick
    data += vlq(0) + b'\xff\x2f\x00'
    return b'MTrk' + struct.pack('>I', len(data)) + data

def write_midi(fugue, path):
    chunks = []
    tempo = int(60_000_000 / BPM)
    meta = [(0, b'\xff\x51\x03' + struct.pack('>I', tempo)[1:]),
            (0, b'\xff\x58\x04\x02\x01\x18\x08'),
            (0, b'\xff\x03' + vlq(len(fugue['name'].encode())) + fugue['name'].encode())]
    chunks.append(track(meta))
    for v in range(4):
        ev = [(0, bytes([0xC0 | v, PROGRAMS[v]]))]
        for n in fugue['notes']:
            if n['v'] != v: continue
            t0 = int(round(n['t'] * TPQ)); t1 = int(round((n['t'] + n['dur']) * TPQ)) - 2
            vel = 96 if n['tag'] in ('S1', 'S2', 'S3', 'S4') else 76
            ev.append((t0, bytes([0x90 | v, n['p'], vel]))); ev.append((t1, bytes([0x80 | v, n['p'], 0])))
        chunks.append(track(ev))
    with open(path, 'wb') as f:
        f.write(b'MThd' + struct.pack('>IHHH', 6, 1, len(chunks), TPQ) + b''.join(chunks))

if __name__ == '__main__':
    fugues = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    for f in fugues:
        p = os.path.join(outdir, f"fuga{f['no']:02d}_{f['name'].replace(' — ', '_').replace(' ', '_').replace('#', 's')}.mid")
        write_midi(f, p); print(p)
