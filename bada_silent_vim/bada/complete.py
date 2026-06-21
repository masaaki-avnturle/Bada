"""Word completion for Bada source.

* **functional-word completion** (機能語補完): reserved keywords + builtins.
* **word completion** (単語補完): symbols defined in the buffer — function
  names, parameters and assigned variables — plus the functional words.

Symbols are harvested from the token stream so completion adapts to the buffer.
"""

from __future__ import annotations

from .lexer import tokenize
from .keywords import FUNCTIONAL_WORDS, RESERVED, BUILTIN_FUNCS


class Completer:
    def __init__(self, extra: tuple = ()):
        self.extra = list(extra)

    # -- harvest user symbols from a buffer --------------------------------
    def symbols(self, src: str) -> list[str]:
        try:
            toks = tokenize(src)
        except Exception:
            return []
        syms: set[str] = set()
        for i, t in enumerate(toks):
            if t.kind != "IDENT":
                continue
            prev = toks[i - 1] if i > 0 else None
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            # function name:  def NAME (
            if prev and prev.kind == "KW" and prev.value == "def":
                syms.add(t.value)
            # assigned / parameter / referenced identifier
            syms.add(t.value)
            _ = nxt
        return sorted(syms)

    # -- completion --------------------------------------------------------
    def complete_functional(self, prefix: str) -> list[str]:
        return [w for w in FUNCTIONAL_WORDS if w.startswith(prefix)]

    def complete_words(self, src: str, prefix: str) -> list[str]:
        pool = set(self.symbols(src)) | set(FUNCTIONAL_WORDS) | set(self.extra)
        return sorted(w for w in pool if w.startswith(prefix))

    def complete(self, src: str, prefix: str, kind: str = "all") -> list[str]:
        if kind == "functional":
            return self.complete_functional(prefix)
        if kind == "words":
            user = set(self.symbols(src)) | set(self.extra)
            return sorted(w for w in user if w.startswith(prefix))
        return self.complete_words(src, prefix)


def prefix_at(line: str, col: int) -> str:
    """The identifier prefix ending at column `col` in `line`."""
    j = min(col, len(line))
    i = j
    while i > 0 and (line[i - 1].isalnum() or line[i - 1] == "_"):
        i -= 1
    return line[i:j]
