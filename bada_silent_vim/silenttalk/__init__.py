"""Silent-talk: recover Bada editor commands from lip-movement images.

Implements the brain-interface scheme of report a23d7ab9 without audio:
a 7-level resonance scale (:mod:`silenttalk.scale`) is reconstructed from lip
images (:mod:`silenttalk.lipfeatures`), and the two streams are decoded into
tokens (:mod:`silenttalk.decoder`).  :mod:`silenttalk.synth` generates the
canonical lip frames for any word so the pipeline round-trips through files.
"""

from .lipfeatures import (LipFeature, classify_viseme, lip_features, read_pgm,
                          write_pgm, VISEMES)
from .scale import BAND_NAMES, dominant_band, resonance_bands
from .decoder import SilentTalkDecoder, Token, load_lexicon
from .synth import draw_viseme, synth_stream, synth_utterance, write_frames

__all__ = [
    "LipFeature", "classify_viseme", "lip_features", "read_pgm", "write_pgm",
    "VISEMES", "BAND_NAMES", "dominant_band", "resonance_bands",
    "SilentTalkDecoder", "Token", "load_lexicon",
    "draw_viseme", "synth_stream", "synth_utterance", "write_frames",
]
