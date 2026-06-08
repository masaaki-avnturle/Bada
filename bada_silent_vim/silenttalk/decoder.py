"""Silent-talk decoder: lip-frame images -> recognized tokens.

Pipeline (faithful to report a23d7ab9):

1. Each frame image -> :class:`~silenttalk.lipfeatures.LipFeature`.
2. Feature -> viseme symbol (lip-movement stream) AND -> 7-band resonance
   activation (the musical-scale stream).
3. The two streams resonate: consecutive equal visemes are collapsed
   (CTC-style), and runs of rest ('C') segment the stream into utterances.
4. Each utterance's collapsed viseme-word is looked up in the lexicon, giving
   a normal-mode command and/or an insert-mode text token.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .lipfeatures import (LipFeature, classify_viseme, lip_features, parse_pgm,
                          read_pgm)
from .scale import BAND_NAMES, dominant_band, resonance_bands

_LEXICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "silenttalk_lexicon.json")


def load_lexicon(path: str = _LEXICON_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


@dataclass
class Token:
    visemes: str                 # collapsed viseme-word, e.g. "AI"
    command: str | None          # normal-mode meaning, e.g. "INSERT"
    text: str | None             # insert-mode dictation, e.g. "say "
    band: int                    # dominant resonance band (0..6)
    band_name: str = field(default="")

    def __post_init__(self):
        self.band_name = BAND_NAMES[self.band]

    def __repr__(self) -> str:
        return (f"Token({self.visemes!r} -> cmd={self.command} "
                f"text={self.text!r} band={self.band_name})")


class SilentTalkDecoder:
    def __init__(self, lexicon: dict | None = None):
        self.lex = lexicon or load_lexicon()

    # -- low level ---------------------------------------------------------
    def frames_to_visemes(self, frames):
        """Return list of (viseme, LipFeature) per frame."""
        out = []
        for fr in frames:
            feat = lip_features(fr)
            out.append((classify_viseme(feat), feat))
        return out

    def decode_frames(self, frames) -> list[Token]:
        seq = self.frames_to_visemes(frames)

        # collapse consecutive duplicates, keeping a representative feature
        collapsed: list[tuple[str, LipFeature]] = []
        for v, feat in seq:
            if collapsed and collapsed[-1][0] == v:
                continue
            collapsed.append((v, feat))

        # segment on rest 'C'
        tokens: list[Token] = []
        cur: list[tuple[str, LipFeature]] = []

        def flush():
            if not cur:
                return
            word = "".join(v for v, _ in cur)
            # average resonance over the utterance for the dominant band
            avg = LipFeature(
                sum(f.aperture for _, f in cur) / len(cur),
                sum(f.spread for _, f in cur) / len(cur),
                sum(f.energy for _, f in cur) / len(cur))
            band = dominant_band(avg)
            tokens.append(Token(
                visemes=word,
                command=self.lex["commands"].get(word),
                text=self.lex["text"].get(word),
                band=band))
            cur.clear()

        for v, feat in collapsed:
            if v == "C":
                flush()
            else:
                cur.append((v, feat))
        flush()
        return tokens

    # -- file helpers ------------------------------------------------------
    def decode_dir(self, directory: str) -> list[Token]:
        names = sorted(n for n in os.listdir(directory)
                       if n.lower().endswith(".pgm"))
        frames = [read_pgm(os.path.join(directory, n)) for n in names]
        return self.decode_frames(frames)

    def decode_paths(self, paths: list[str]) -> list[Token]:
        frames = [read_pgm(p) for p in paths]
        return self.decode_frames(frames)
