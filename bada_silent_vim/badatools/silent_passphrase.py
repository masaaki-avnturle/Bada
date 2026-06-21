"""Silent-talk passphrase (合言葉) parser.

A *passphrase* is a secret sequence of silent-talk viseme-words that, when
spoken silently in order, triggers a command — so a command is realised only by
the right watchword.  Matching is greedy/longest over the recognised word
stream (non-overlapping).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from silenttalk import SilentTalkDecoder         # noqa: E402

# default watchwords: tuple of viseme-words -> command
DEFAULT_PASSPHRASES = {
    ("AI", "UO"): "UNLOCK",            # insert-then-escape: open the gate
    ("OA", "OA"): "RUN-SECRET",        # run-run: privileged run
    ("AE", "UI"): "SAVE-QUIT",         # save-quit
    ("IO", "UA", "OI", "EU"): "GODMODE",   # up down left right
}


class PassphraseParser:
    def __init__(self, table: dict | None = None):
        self.table = dict(table) if table is not None else dict(
            DEFAULT_PASSPHRASES)
        self._lengths = sorted({len(k) for k in self.table}, reverse=True)

    def parse(self, words: list[str]) -> list[dict]:
        """Detect non-overlapping passphrases in a viseme-word stream."""
        out: list[dict] = []
        i = 0
        n = len(words)
        while i < n:
            matched = None
            for length in self._lengths:
                seq = tuple(words[i:i + length])
                if len(seq) == length and seq in self.table:
                    matched = (seq, self.table[seq])
                    break
            if matched:
                out.append({"passphrase": list(matched[0]),
                            "command": matched[1]})
                i += len(matched[0])
            else:
                i += 1
        return out

    def matches(self, words: list[str]) -> bool:
        return bool(self.parse(words))

    # -- from silent-talk frames ------------------------------------------
    def from_frames(self, frames, decoder: SilentTalkDecoder | None = None):
        decoder = decoder or SilentTalkDecoder()
        words = [t.visemes for t in decoder.decode_frames(frames)]
        return self.parse(words)
