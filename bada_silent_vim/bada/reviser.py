"""The Bada reviser: rewrite classic Bada source into the instruction-oriented
("directive object") dialect, and back-compatibly run it.

Mapping (指示指向オブジェクト):

    assignment object   =   ->  <-
    comparison object   ==  ->  <->
    branch object       if  ->  -<
    merge object        else->  >-
    transition object   while-> ->

Comments and string literals are preserved verbatim; only real keywords and
operators in code are rewritten.  The transform is semantics-preserving: the
revised source parses to the same AST and runs identically.
"""

from __future__ import annotations

import os

# keyword -> directive operator
_KEYWORDS = {"if": "-<", "else": ">-", "while": "->"}

# operators tried longest-first so multi-char ops aren't split.  Most map to
# themselves; only `==` and a lone `=` are rewritten.
_OPS = ["<->", "::", "<-", "-<", "->", ">-", ">>", "=>",
        "==", "!=", "<=", ">=", "<", ">", "="]
_OP_MAP = {"==": "<->", "=": "<-"}


def revise(src: str) -> str:
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]

        # line comment — copy verbatim to end of line
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = i
            while j < n and src[j] != "\n":
                j += 1
            out.append(src[i:j])
            i = j
            continue

        # string literal — copy verbatim (respecting escapes)
        if c in "\"'":
            quote = c
            j = i + 1
            buf = [c]
            while j < n and src[j] != quote:
                if src[j] == "\\" and j + 1 < n:
                    buf.append(src[j:j + 2])
                    j += 2
                else:
                    buf.append(src[j])
                    j += 1
            if j < n:
                buf.append(src[j])
                j += 1
            out.append("".join(buf))
            i = j
            continue

        # identifier / keyword
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            out.append(_KEYWORDS.get(word, word))
            i = j
            continue

        # operator (greedy longest match)
        matched = None
        for op in _OPS:
            if src.startswith(op, i):
                matched = op
                break
        if matched:
            out.append(_OP_MAP.get(matched, matched))
            i += len(matched)
            continue

        # any other character (whitespace, +,-,*,/,%, punctuation, #) verbatim
        out.append(c)
        i += 1
    return "".join(out)


def revise_file(path: str, write: bool = False) -> str:
    with open(path) as f:
        revised = revise(f.read())
    if write:
        with open(path, "w") as f:
            f.write(revised)
    return revised


def _equivalent(path: str) -> bool:
    """Check that classic and revised source compile to the same bytecode."""
    from .loader import load_program
    from .compiler import compile_source
    with open(path) as f:
        original = f.read()
    base = os.path.dirname(path)

    def _resolve(text):                 # inline includes for compilation
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#include"):
                inc = s[len("#include"):].strip().strip('"<>')
                lines.append(load_program(os.path.join(base, inc)))
            else:
                lines.append(line)
        return "\n".join(lines)

    return (compile_source(_resolve(original))
            == compile_source(_resolve(revise(original))))


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        prog="bada-reviser",
        description="Rewrite Bada into the instruction-oriented dialect.")
    p.add_argument("files", nargs="+")
    p.add_argument("--write", action="store_true", help="rewrite in place")
    p.add_argument("--check", action="store_true",
                   help="verify revised source is equivalent to the original")
    args = p.parse_args(argv)
    for path in args.files:
        if args.check:
            ok = _equivalent(path)
            print(f"{'OK ' if ok else 'DIFF'}  {path}")
        elif args.write:
            revise_file(path, write=True)
            print(f"revised  {path}")
        else:
            print(revise_file(path))


if __name__ == "__main__":
    main()
