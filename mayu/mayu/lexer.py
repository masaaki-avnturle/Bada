r"""字句解析 / Lexer for the .mayu configuration language.

窓使いの憂鬱 の設定ファイルは行指向で、以下のような構文を持つ:

    include "104.mayu"

    def key Muhenkan = 0x7B

    mod control += CapsLock

    keymap Global
      key C-b = Left
      key C-f = Right
      key *IC-A = Home

行末までがひとつの論理行。``#`` 以降はコメント。``\`` による行継続に対応する。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Line:
    """論理行ひとつ分。空白・コメント除去済みのトークン列を持つ。"""

    number: int          # 元ファイルの行番号 (1 始まり、継続時は先頭行)
    indent: int          # 先頭の空白数 (keymap 配下判定に使う)
    tokens: list[str]    # 空白で区切ったトークン
    raw: str             # 元の行 (エラーメッセージ用)


def _split_tokens(text: str) -> list[str]:
    """1 論理行をトークンへ分解する。

    ダブルクォート文字列はひとつのトークンとして保持する
    (先頭に \\x00 を付けて「文字列トークン」と印を付ける)。
    ``=`` ``+=`` ``-=`` は独立したトークンとして切り出す。
    """
    tokens: list[str] = []
    i = 0
    n = len(text)
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf:
            tokens.append(buf)
            buf = ""

    while i < n:
        c = text[i]
        if c in " \t":
            flush()
            i += 1
            continue
        if c == '"':
            flush()
            j = i + 1
            s = ""
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    s += text[j + 1]
                    j += 2
                    continue
                s += text[j]
                j += 1
            tokens.append("\x00" + s)  # 文字列トークンの印
            i = j + 1
            continue
        # 演算子 += -= = を切り出す
        if c in "+-" and i + 1 < n and text[i + 1] == "=":
            flush()
            tokens.append(text[i : i + 2])
            i += 2
            continue
        if c == "=":
            flush()
            tokens.append("=")
            i += 1
            continue
        buf += c
        i += 1
    flush()
    return tokens


def tokenize(source: str) -> list[Line]:
    """ソース全体を論理行のリストへ変換する。"""
    lines: list[Line] = []
    raw_lines = source.splitlines()
    i = 0
    while i < len(raw_lines):
        start = i
        raw = raw_lines[i]
        # 行継続 (\ が行末) を連結
        acc = raw
        while acc.rstrip().endswith("\\"):
            acc = acc.rstrip()[:-1]
            i += 1
            if i < len(raw_lines):
                acc += raw_lines[i]
            else:
                break

        # コメント除去 (クォート内の # は保持)
        stripped = _strip_comment(acc)
        indent = len(acc) - len(acc.lstrip(" \t"))
        tokens = _split_tokens(stripped)
        if tokens:
            lines.append(Line(number=start + 1, indent=indent, tokens=tokens, raw=raw))
        i += 1
    return lines


def _strip_comment(text: str) -> str:
    out = ""
    in_str = False
    j = 0
    while j < len(text):
        c = text[j]
        if c == '"':
            in_str = not in_str
        elif c == "\\" and in_str and j + 1 < len(text):
            out += c + text[j + 1]
            j += 2
            continue
        elif c == "#" and not in_str:
            break
        out += c
        j += 1
    return out


def is_string_token(tok: str) -> bool:
    return tok.startswith("\x00")


def string_value(tok: str) -> str:
    return tok[1:]
