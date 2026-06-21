"""Unified input parser for Bada: silent talk AND keyboard.

Both sources are normalised to the same command stream (see
:mod:`badatools.editor_parser`), so a Bada editor can be driven identically by
the keyboard or by silent talk — and silent talk additionally recognises
passphrases (合言葉) that trigger privileged commands.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from silenttalk import SilentTalkDecoder           # noqa: E402

from .editor_parser import EmacsParser, VimParser
from .silent_passphrase import PassphraseParser

# silent-talk command word -> normalized command
_CMD = {
    "INSERT": ("mode", "INSERT"), "ESCAPE": ("mode", "NORMAL"),
    "UP": ("move", "UP"), "DOWN": ("move", "DOWN"),
    "LEFT": ("move", "LEFT"), "RIGHT": ("move", "RIGHT"),
    "NEWLINE": ("open",), "DELETE": ("delete",),
    "SAVE": ("save",), "QUIT": ("quit",), "RUN": ("run",),
}


class UnifiedInputParser:
    def __init__(self, decoder: SilentTalkDecoder | None = None,
                 passphrases: dict | None = None):
        self.decoder = decoder or SilentTalkDecoder()
        self.lex = self.decoder.lex
        self.passphrase = PassphraseParser(passphrases)
        self.vim = VimParser()
        self.emacs = EmacsParser()

    # -- silent talk -------------------------------------------------------
    def from_silent_words(self, words: list[str]) -> dict:
        commands: list[tuple] = []
        for w in words:
            cmd = self.lex["commands"].get(w)
            txt = self.lex["text"].get(w)
            if cmd in _CMD:
                commands.append(_CMD[cmd])
            elif txt is not None:
                commands.append(("text", txt))
        return {
            "source": "silent",
            "passphrases": self.passphrase.parse(words),
            "commands": commands,
        }

    def from_silent_frames(self, frames) -> dict:
        words = [t.visemes for t in self.decoder.decode_frames(frames)]
        result = self.from_silent_words(words)
        result["words"] = words
        return result

    # -- keyboard ----------------------------------------------------------
    def from_keyboard(self, keys: list[str], editor: str = "vim") -> dict:
        parser = self.emacs if editor == "emacs" else self.vim
        return {"source": "keyboard", "editor": editor,
                "commands": parser.parse(keys), "passphrases": []}

    # -- unified -----------------------------------------------------------
    def parse(self, *, silent_words=None, silent_frames=None,
              keys=None, editor="vim") -> dict:
        if silent_frames is not None:
            return self.from_silent_frames(silent_frames)
        if silent_words is not None:
            return self.from_silent_words(silent_words)
        if keys is not None:
            return self.from_keyboard(keys, editor=editor)
        return {"commands": [], "passphrases": []}
