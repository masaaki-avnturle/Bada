#!/usr/bin/env python3
"""Hoist `let` bindings out of `while` loops in bada_c sources.

bada_c's env_define prepends a new binding on every executed `let`, so a `let`
inside a loop body grows the environment each iteration (O(n^2) lookups).
This rewrites `let x = e` inside any while-body into `x = e` and declares
`let x = 0` once at the top of the enclosing function (or before the outermost
top-level loop).
"""
import re
import sys

OPEN = re.compile(r"^\s*(def\s+\w+\s*\(|while\b|if\b)")
LET = re.compile(r"^(\s*)let\s+(\w+)\s*=\s*(.*)$")


def opens(line):
    s = line.strip()
    if s.startswith("#"):
        return False
    if not OPEN.match(line):
        return False
    # single-line forms: `def f(x) return x end`, `if c ... end`
    return not re.search(r"\bend\s*\)?\s*$", s)


def process(src):
    lines = src.split("\n")
    out = []
    stack = []            # entries: ("def"|"while"|"if", index_in_out)
    hoisted = {}          # anchor index -> [names]
    for line in lines:
        s = line.strip()
        m = LET.match(line)
        in_loop = any(k == "while" for k, _ in stack)
        if m and in_loop:
            indent, name, expr = m.groups()
            # anchor: enclosing def, else the outermost while at top level
            anchor = None
            for k, idx in reversed(stack):
                if k == "def":
                    anchor = ("def", idx)
                    break
            if anchor is None:
                anchor = ("top", next(idx for k, idx in stack if k == "while"))
            names = hoisted.setdefault(anchor, [])
            if name not in names:
                names.append(name)
            out.append("%s%s = %s" % (indent, name, expr))
        else:
            out.append(line)
        if s == "end" or s.startswith("end ") or s == "end)":
            if stack:
                stack.pop()
        elif opens(line):
            kind = "def" if s.startswith("def") else ("while" if s.startswith("while") else "if")
            stack.append((kind, len(out) - 1))
    # insert declarations (from the bottom so indices stay valid)
    for (kind, idx) in sorted(hoisted, key=lambda a: -a[1]):
        names = hoisted[(kind, idx)]
        base = out[idx]
        indent = re.match(r"^(\s*)", base).group(1)
        if kind == "def":
            decl = ["%s  let %s = 0" % (indent, n) for n in names]
            out[idx + 1:idx + 1] = decl
        else:
            decl = ["%slet %s = 0" % (indent, n) for n in names]
            out[idx:idx] = decl
    return "\n".join(out)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        src = open(path, encoding="utf-8").read()
        new = process(src)
        if new != src:
            open(path, "w", encoding="utf-8").write(new)
            print("hoisted:", path)
