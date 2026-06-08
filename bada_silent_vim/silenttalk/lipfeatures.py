"""Lip-image feature extraction for the silent-talk pipeline.

The brain-interface report (a23d7ab9) recovers speech from two streams: a
7-level resonance scale, and lip-movement data turned into an electric signal.
Here the lip stream is recovered from *images*: each frame is a grayscale PGM
where the mouth is a dark region on a light face.  We measure the dark blob's
bounding box to get the mouth *aperture* (vertical opening) and *spread*
(horizontal opening), then classify the frame into a viseme symbol.

PGM is used because it needs no third-party libraries while still being a real
image format (``P2`` ASCII and ``P5`` binary are both supported).
"""

from __future__ import annotations

from dataclasses import dataclass

# Viseme alphabet (mouth shapes).  'C' = closed/rest.
VISEMES = ("C", "A", "I", "U", "O", "E")


@dataclass
class LipFeature:
    aperture: float   # 0..1  vertical mouth opening
    spread: float     # 0..1  horizontal mouth opening
    energy: float     # 0..1  overall darkness (articulation effort)


# --------------------------------------------------------------------------
# PGM image I/O (stdlib only)
# --------------------------------------------------------------------------
def read_pgm(path: str) -> list[list[int]]:
    with open(path, "rb") as f:
        data = f.read()
    return parse_pgm(data)


def parse_pgm(data: bytes) -> list[list[int]]:
    # Read header tokens, skipping comments.
    pos = 0
    tokens: list[bytes] = []
    magic = None
    while len(tokens) < 4 and pos < len(data):
        # skip whitespace
        while pos < len(data) and data[pos:pos + 1].isspace():
            pos += 1
        if pos < len(data) and data[pos:pos + 1] == b"#":
            while pos < len(data) and data[pos:pos + 1] != b"\n":
                pos += 1
            continue
        start = pos
        while pos < len(data) and not data[pos:pos + 1].isspace():
            pos += 1
        tok = data[start:pos]
        if magic is None:
            magic = tok
            tokens.append(tok)
        else:
            tokens.append(tok)
    magic = tokens[0]
    width = int(tokens[1])
    height = int(tokens[2])
    int(tokens[3])  # maxval, unused
    pos += 1  # single whitespace after maxval

    if magic == b"P2":
        nums = data[pos:].split()
        vals = [int(x) for x in nums[: width * height]]
    elif magic == b"P5":
        vals = list(data[pos: pos + width * height])
    else:
        raise ValueError(f"unsupported PGM magic {magic!r}")
    return [vals[r * width:(r + 1) * width] for r in range(height)]


def write_pgm(path: str, pixels: list[list[int]]):
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    with open(path, "w") as f:
        f.write(f"P2\n{width} {height}\n255\n")
        for row in pixels:
            f.write(" ".join(str(int(v)) for v in row))
            f.write("\n")


# --------------------------------------------------------------------------
# Feature extraction
# --------------------------------------------------------------------------
def lip_features(pixels: list[list[int]], dark_thresh: int = 110) -> LipFeature:
    """Recover mouth aperture/spread from a frame.

    The mouth is the connected dark region; we take the bounding box of all
    pixels darker than ``dark_thresh``.
    """
    h = len(pixels)
    w = len(pixels[0]) if h else 0
    min_r, max_r, min_c, max_c = h, -1, w, -1
    dark = 0
    for r in range(h):
        row = pixels[r]
        for c in range(w):
            if row[c] < dark_thresh:
                dark += 1
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c
    if max_r < 0:  # no dark pixels -> fully closed
        return LipFeature(0.0, 0.0, 0.0)
    aperture = (max_r - min_r + 1) / h
    spread = (max_c - min_c + 1) / w
    energy = dark / (w * h)
    return LipFeature(round(aperture, 3), round(spread, 3), round(energy, 3))


def classify_viseme(feat: LipFeature) -> str:
    """Map a lip feature to one of :data:`VISEMES`.

    Thresholds chosen to be stable against the synthesizer in
    :mod:`silenttalk.synth` while remaining intuitive: tall+wide = A,
    flat+wide = I, tall+narrow = O, small+narrow = U, mid = E.
    """
    a, s = feat.aperture, feat.spread
    if feat.energy < 0.02 or (a < 0.12 and s < 0.20):
        return "C"            # closed / rest
    tall = a >= 0.34
    wide = s >= 0.45
    if tall and wide:
        return "A"
    if not tall and wide:
        return "I"
    if tall and not wide:
        return "O"
    if a < 0.22 and not wide:
        return "U"
    return "E"
