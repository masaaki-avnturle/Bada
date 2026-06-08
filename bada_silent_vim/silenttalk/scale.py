"""The 7-level resonance scale (音階の 7 階層).

From report a23d7ab9: to display speech as text the machine decomposes the
voice into a 7-level musical scale, and resonates it (via the basal ganglia
resonance circuit) with the lip-movement signal.  In the silent-talk setting
there is no audio, so the resonance is *reconstructed* from the lip image:
articulation energy and aperture excite a band on the 7-step scale.

This module turns a :class:`~silenttalk.lipfeatures.LipFeature` into a 7-band
activation vector and reports the dominant band, which the decoder uses to
refine vowel height.
"""

from __future__ import annotations

from .lipfeatures import LipFeature

N_BANDS = 7
# Names of the seven resonance steps (do, re, mi, fa, sol, la, si).
BAND_NAMES = ("do", "re", "mi", "fa", "sol", "la", "si")


def resonance_bands(feat: LipFeature) -> list[float]:
    """Project a lip feature onto 7 resonance bands.

    The drive frequency is governed by aperture (open = lower pitch / lower
    band) and spread (wide = higher formant / higher band); energy sets the
    overall amplitude.  We place a triangular activation around the centre
    band and normalise.
    """
    # Centre band: combine spread (raises) and aperture (lowers) on 0..6.
    centre = (feat.spread * 4.0) + ((1.0 - feat.aperture) * 2.0)
    centre = max(0.0, min(N_BANDS - 1, centre))
    bands = []
    for b in range(N_BANDS):
        act = max(0.0, 1.0 - abs(b - centre)) * (0.2 + feat.energy)
        bands.append(round(act, 4))
    total = sum(bands) or 1.0
    return [round(x / total, 4) for x in bands]


def dominant_band(feat: LipFeature) -> int:
    bands = resonance_bands(feat)
    return max(range(N_BANDS), key=lambda b: bands[b])
