import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mayu.lexer import is_string_token, string_value, tokenize


def test_basic_tokens():
    lines = tokenize("key C-b = Left")
    assert len(lines) == 1
    assert lines[0].tokens == ["key", "C-b", "=", "Left"]


def test_comment_stripped():
    lines = tokenize("key a = b   # これはコメント")
    assert lines[0].tokens == ["key", "a", "=", "b"]


def test_blank_and_comment_only_lines_skipped():
    lines = tokenize("\n# comment only\n   \nkey a = b\n")
    assert len(lines) == 1
    assert lines[0].number == 4


def test_string_token():
    lines = tokenize('include "104.mayu"')
    tok = lines[0].tokens[1]
    assert is_string_token(tok)
    assert string_value(tok) == "104.mayu"


def test_operator_split_without_spaces():
    lines = tokenize("mod control+=CapsLock")
    assert lines[0].tokens == ["mod", "control", "+=", "CapsLock"]


def test_line_continuation():
    lines = tokenize("key a = \\\n   b")
    assert lines[0].tokens == ["key", "a", "=", "b"]


def test_indent_recorded():
    lines = tokenize("keymap Global\n  key a = b")
    assert lines[0].indent == 0
    assert lines[1].indent == 2


def test_hash_in_string_preserved():
    lines = tokenize('def option x = "a#b"')
    assert string_value(lines[0].tokens[-1]) == "a#b"
