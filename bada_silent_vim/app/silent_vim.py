"""Silent-Vim session: operate the Bada editor by silent talk.

This binds the three subsystems together:

    lip-movement images  --(SilentTalkDecoder)-->  tokens
                         --(BadaVim.feed_token)-->  editor actions / dictation
                         --(BadaVim.run_buffer)-->  Bada compiler + VM

A session can be fed a directory of PGM frames, an explicit list of
viseme-words (which it synthesizes into frames first, so it still goes through
the image pipeline), and reports a transcript of what the silent talk did.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from editor import BadaVim                       # noqa: E402
from silenttalk import SilentTalkDecoder, synth_stream  # noqa: E402


class SilentVimSession:
    def __init__(self, ed: BadaVim | None = None,
                 decoder: SilentTalkDecoder | None = None):
        self.ed = ed or BadaVim()
        self.decoder = decoder or SilentTalkDecoder()
        self.transcript: list[str] = []

    def _apply(self, tokens):
        for tok in tokens:
            mode_before = self.ed.mode
            acted = self.ed.feed_token(tok)
            kind = (tok.command if (self.ed.mode != "INSERT" or
                                    tok.command == "ESCAPE")
                    else f"text {tok.text!r}")
            self.transcript.append(
                f"[{tok.band_name:>3}] {tok.visemes:<3} "
                f"{mode_before:>6} -> {self.ed.mode:<6} "
                f"{'·' if not acted else (kind or '')}")
        return tokens

    def feed_frames_dir(self, directory: str):
        return self._apply(self.decoder.decode_dir(directory))

    def feed_frames(self, frames):
        return self._apply(self.decoder.decode_frames(frames))

    def feed_words(self, words: list[str], hold: int = 3):
        """Synthesize lip frames for viseme-words, then decode + apply them."""
        frames = synth_stream(words, hold=hold)
        return self.feed_frames(frames)

    # convenience
    def buffer_text(self) -> str:
        return self.ed.text()

    def run(self):
        self.ed.run_buffer()
        return self.ed.output
