"""Synthesize lip-movement frames (PGM images) for a viseme sequence.

This is the *encoder* side of the silent-talk demo: given a viseme symbol it
draws a frame where the mouth is a dark ellipse whose height encodes aperture
and width encodes spread.  Concatenating per-viseme frames (separated by a
closed 'C' rest) produces an utterance the recognizer can read back from
disk, so the whole pipeline round-trips through real image files.
"""

from __future__ import annotations

import os

from .lipfeatures import write_pgm

# Target (aperture, spread) for each viseme.  Tuned to land in the
# classification buckets of silenttalk.lipfeatures.classify_viseme.
VISEME_SHAPE = {
    "C": (0.04, 0.15),
    "A": (0.46, 0.62),
    "I": (0.18, 0.62),
    "O": (0.46, 0.30),
    "U": (0.15, 0.24),
    "E": (0.28, 0.40),
}

W = H = 32
BG = 255
FG = 40


def draw_viseme(viseme: str, w: int = W, h: int = H) -> list[list[int]]:
    aperture, spread = VISEME_SHAPE[viseme]
    cy, cx = h / 2.0, w / 2.0
    ry = max(0.5, aperture * h / 2.0)
    rx = max(0.5, spread * w / 2.0)
    pixels = [[BG] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            dy = (r - cy) / ry
            dx = (c - cx) / rx
            if dx * dx + dy * dy <= 1.0:
                pixels[r][c] = FG
    return pixels


def synth_utterance(visemes: str, hold: int = 2) -> list[list[list[int]]]:
    """Frames for one command/word: rest, each viseme held, rest."""
    frames = [draw_viseme("C")]
    for v in visemes:
        for _ in range(hold):
            frames.append(draw_viseme(v))
    frames.append(draw_viseme("C"))
    return frames


def synth_stream(words: list[str], hold: int = 2) -> list[list[list[int]]]:
    """Frames for a sequence of utterances separated by rests."""
    frames: list[list[list[int]]] = []
    for w in words:
        frames.extend(synth_utterance(w, hold=hold))
    return frames


def write_frames(frames: list[list[list[int]]], out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, fr in enumerate(frames):
        p = os.path.join(out_dir, f"frame_{i:04d}.pgm")
        write_pgm(p, fr)
        paths.append(p)
    return paths
