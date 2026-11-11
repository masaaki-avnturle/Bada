"""The Reviser (リバイザ) — Bada's grammar / syntax rewriting facility.

Inspired by the ``@reviser`` mechanism in the Bada design documents, which
states that "the parser and the lexer can all be rewritten" and that the
rewrite rules live in their own write-once tuplespace.

A program declares rewrite rules in a ``reviser { ... }`` block.  These rules
are applied to the *source text* before the lexer runs, so they genuinely
rewrite the surface grammar of the language (including custom keywords and
brand-new operator symbols).  The collected rules are exposed to the running
program as an immutable ``Reviser`` tuplespace.

Rule forms (both sides are quoted strings)::

    reviser {
        word "関数"  => "fun"      // whole-word (identifier) rewrite
        word "表示"  => "print"
        op   "→"     => "<-"       // operator / symbol rewrite (substring)
        text "なら"  => "if"        // raw substring rewrite
    }

Rules are applied in declaration order.  String literals and comments in the
target program are left untouched.
"""

import re

from .errors import BadaSyntaxError


_RULE_RE = re.compile(
    r'^(word|op|text)\s+"((?:[^"\\]|\\.)*)"\s*=>\s*"((?:[^"\\]|\\.)*)"$'
)


def _unescape(s):
    return (s.replace('\\n', '\n').replace('\\t', '\t')
             .replace('\\"', '"').replace('\\\\', '\\'))


def _is_ident_char(ch):
    return ch.isalnum() or ch == "_"


def _strip_comment(line):
    """Remove a trailing // line comment that is outside any quotes."""
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
            return line[:i]
        i += 1
    return line


class Rule:
    __slots__ = ("kind", "pattern", "replacement")

    def __init__(self, kind, pattern, replacement):
        self.kind = kind                # 'word' | 'op' | 'text'
        self.pattern = pattern
        self.replacement = replacement

    def __repr__(self):
        return f"<reviser {self.kind} {self.pattern!r} => {self.replacement!r}>"


class Reviser:
    """Extracts reviser blocks and rewrites source text accordingly."""

    @staticmethod
    def process(source):
        """Return ``(rewritten_source, rules)`` for a raw program source."""
        stripped, rules = Reviser._extract_blocks(source)
        if not rules:
            return stripped, rules
        rewritten = Reviser._apply(stripped, rules)
        return rewritten, rules

    # --- block extraction (string/comment aware) --------------------------

    @staticmethod
    def _extract_blocks(src):
        out = []
        rules = []
        i, n = 0, len(src)
        while i < n:
            ch = src[i]

            # line comment
            if ch == "/" and i + 1 < n and src[i + 1] == "/":
                j = i
                while j < n and src[j] != "\n":
                    j += 1
                out.append(src[i:j])
                i = j
                continue
            # block comment
            if ch == "/" and i + 1 < n and src[i + 1] == "*":
                j = i + 2
                while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
                    j += 1
                j = min(j + 2, n)
                out.append(src[i:j])
                i = j
                continue
            # string literal
            if ch == '"' or ch == "'":
                j = i + 1
                while j < n and src[j] != ch:
                    if src[j] == "\\":
                        j += 1
                    j += 1
                j = min(j + 1, n)
                out.append(src[i:j])
                i = j
                continue

            # reviser block?
            if (src.startswith("reviser", i)
                    and (i == 0 or not _is_ident_char(src[i - 1]))
                    and not _is_ident_char(src[i + 7] if i + 7 < n else " ")):
                k = i + 7
                while k < n and src[k] in " \t\r\n":
                    k += 1
                if k < n and src[k] == "{":
                    body, end = Reviser._read_block(src, k)
                    rules.extend(Reviser._parse_rules(body))
                    i = end
                    continue

            out.append(ch)
            i += 1

        return "".join(out), rules

    @staticmethod
    def _read_block(src, open_idx):
        """Read a balanced { ... } block starting at open_idx; return (body, end)."""
        n = len(src)
        depth = 0
        i = open_idx
        start_body = open_idx + 1
        while i < n:
            ch = src[i]
            if ch == '"' or ch == "'":
                i += 1
                while i < n and src[i] != ch:
                    if src[i] == "\\":
                        i += 1
                    i += 1
                i += 1
                continue
            if ch == "/" and i + 1 < n and src[i + 1] == "/":
                while i < n and src[i] != "\n":
                    i += 1
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return src[start_body:i], i + 1
            i += 1
        raise BadaSyntaxError("unterminated reviser { ... } block")

    @staticmethod
    def _parse_rules(body):
        rules = []
        # rules are separated by newlines and/or ';'
        for raw in re.split(r"[;\n]", body):
            line = _strip_comment(raw).strip()
            if not line:
                continue
            m = _RULE_RE.match(line)
            if not m:
                raise BadaSyntaxError(f"invalid reviser rule: {line!r}")
            kind, pat, rep = m.group(1), _unescape(m.group(2)), _unescape(m.group(3))
            if not pat:
                raise BadaSyntaxError("reviser rule pattern may not be empty")
            rules.append(Rule(kind, pat, rep))
        return rules

    # --- rule application (string/comment aware) --------------------------

    @staticmethod
    def _apply(src, rules):
        segments = Reviser._segment(src)
        result = []
        for is_code, text in segments:
            if is_code:
                for rule in rules:
                    text = Reviser._apply_one(text, rule)
            result.append(text)
        return "".join(result)

    @staticmethod
    def _apply_one(text, rule):
        if rule.kind == "word":
            return Reviser._replace_word(text, rule.pattern, rule.replacement)
        # 'op' and 'text' are plain substring replacements
        return text.replace(rule.pattern, rule.replacement)

    @staticmethod
    def _replace_word(text, pat, rep):
        out = []
        i, n, m = 0, len(text), len(pat)
        while i < len(text):
            if text[i:i + m] == pat:
                before = text[i - 1] if i > 0 else ""
                after = text[i + m] if i + m < n else ""
                if not _is_ident_char(before) and not _is_ident_char(after):
                    out.append(rep)
                    i += m
                    continue
            out.append(text[i])
            i += 1
        return "".join(out)

    @staticmethod
    def _segment(src):
        """Split into (is_code, text) chunks, isolating strings & comments."""
        segs = []
        buf = []
        i, n = 0, len(src)

        def flush():
            if buf:
                segs.append((True, "".join(buf)))
                buf.clear()

        while i < n:
            ch = src[i]
            if ch == "/" and i + 1 < n and src[i + 1] == "/":
                flush()
                j = i
                while j < n and src[j] != "\n":
                    j += 1
                segs.append((False, src[i:j]))
                i = j
            elif ch == "/" and i + 1 < n and src[i + 1] == "*":
                flush()
                j = i + 2
                while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
                    j += 1
                j = min(j + 2, n)
                segs.append((False, src[i:j]))
                i = j
            elif ch == '"' or ch == "'":
                flush()
                j = i + 1
                while j < n and src[j] != ch:
                    if src[j] == "\\":
                        j += 1
                    j += 1
                j = min(j + 1, n)
                segs.append((False, src[i:j]))
                i = j
            else:
                buf.append(ch)
                i += 1
        flush()
        return segs
