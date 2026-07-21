"""Lexer (字句解析器) for the Bada language.

Turns raw source text into a flat list of Token objects.
"""

from .errors import BadaSyntaxError


# --- Token types -----------------------------------------------------------

NUMBER = "NUMBER"
STRING = "STRING"
IDENT = "IDENT"
KEYWORD = "KEYWORD"
OP = "OP"
EOF = "EOF"


KEYWORDS = {
    "let", "class", "method", "static", "field", "operator", "fun",
    "if", "else", "while", "for", "in", "return", "break", "continue",
    "print", "import", "as", "and", "or", "not",
    "try", "catch", "finally", "throw",
    "true", "false", "nil", "self", "super",
}

# Multi-character operators, matched longest-first.
MULTI_OPS = [
    "<=", ">=", "==", "!=", "<-", "<~", "~>", "-<", "::", "=>",
]
SINGLE_OPS = set("+-*/%<>().{}[],:;")


class Token:
    __slots__ = ("type", "value", "line", "col")

    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"


class Lexer:
    def __init__(self, source, filename="<bada>"):
        self.src = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def error(self, msg):
        raise BadaSyntaxError(msg, self.line, self.col)

    def peek(self, offset=0):
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def add(self, type_, value, line, col):
        self.tokens.append(Token(type_, value, line, col))

    def tokenize(self):
        while self.pos < len(self.src):
            ch = self.peek()

            # Whitespace
            if ch in " \t\r\n":
                self.advance()
                continue

            # Line comment
            if ch == "/" and self.peek(1) == "/":
                while self.pos < len(self.src) and self.peek() != "\n":
                    self.advance()
                continue

            # Block comment
            if ch == "/" and self.peek(1) == "*":
                self.advance(); self.advance()
                while self.pos < len(self.src) and not (self.peek() == "*" and self.peek(1) == "/"):
                    self.advance()
                if self.pos >= len(self.src):
                    self.error("unterminated block comment")
                self.advance(); self.advance()
                continue

            line, col = self.line, self.col

            # Numbers
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self.read_number(line, col)
                continue

            # Strings
            if ch == '"' or ch == "'":
                self.read_string(ch, line, col)
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == "_":
                self.read_ident(line, col)
                continue

            # Operators (multi then single)
            two = self.src[self.pos:self.pos + 2]
            if two in MULTI_OPS:
                self.advance(); self.advance()
                self.add(OP, two, line, col)
                continue
            if ch in SINGLE_OPS:
                self.advance()
                self.add(OP, ch, line, col)
                continue

            self.error(f"unexpected character {ch!r}")

        self.add(EOF, None, self.line, self.col)
        return self.tokens

    def read_number(self, line, col):
        start = self.pos
        seen_dot = False
        while self.pos < len(self.src):
            c = self.peek()
            if c.isdigit():
                self.advance()
            elif c == "." and not seen_dot and self.peek(1).isdigit():
                seen_dot = True
                self.advance()
            else:
                break
        text = self.src[start:self.pos]
        value = float(text) if seen_dot else int(text)
        self.add(NUMBER, value, line, col)

    def read_string(self, quote, line, col):
        self.advance()  # opening quote
        chars = []
        while self.pos < len(self.src) and self.peek() != quote:
            c = self.advance()
            if c == "\\":
                nxt = self.advance() if self.pos < len(self.src) else ""
                chars.append({
                    "n": "\n", "t": "\t", "r": "\r",
                    "\\": "\\", '"': '"', "'": "'", "0": "\0",
                }.get(nxt, nxt))
            else:
                chars.append(c)
        if self.pos >= len(self.src):
            self.error("unterminated string literal")
        self.advance()  # closing quote
        self.add(STRING, "".join(chars), line, col)

    def read_ident(self, line, col):
        start = self.pos
        while self.pos < len(self.src):
            c = self.peek()
            if c.isalnum() or c == "_":
                self.advance()
            else:
                break
        text = self.src[start:self.pos]
        if text in KEYWORDS:
            self.add(KEYWORD, text, line, col)
        else:
            self.add(IDENT, text, line, col)


def tokenize(source, filename="<bada>"):
    return Lexer(source, filename).tokenize()
