import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mayu.keyseq import parse_keystroke


def test_plain_key():
    st = parse_keystroke("a")
    assert st.key == "a"
    assert st.mods == frozenset()
    assert not st.dont_care and not st.up


def test_control_modifier():
    st = parse_keystroke("C-b")
    assert st.key == "b"
    assert st.mods == frozenset({"C"})


def test_multiple_modifiers():
    st = parse_keystroke("C-S-A-x")
    assert st.key == "x"
    assert st.mods == frozenset({"C", "S", "A"})


def test_meta_is_alt():
    assert parse_keystroke("M-x").mods == frozenset({"A"})


def test_dont_care_prefix():
    st = parse_keystroke("*C-A")
    assert st.dont_care
    assert st.mods == frozenset({"C"})
    assert st.key == "A"


def test_up_prefix():
    st = parse_keystroke("~S-Space")
    assert st.up
    assert st.mods == frozenset({"S"})
    assert st.key == "Space"


def test_matching_exact():
    st = parse_keystroke("C-b")
    assert st.matches("b", frozenset({"C"}))
    assert not st.matches("b", frozenset({"C", "S"}))
    assert not st.matches("b", frozenset())


def test_matching_dont_care():
    st = parse_keystroke("*C-b")
    assert st.matches("b", frozenset({"C"}))
    assert st.matches("b", frozenset({"C", "S"}))
    assert not st.matches("b", frozenset({"S"}))


def test_str_roundtrip():
    assert str(parse_keystroke("C-b")) == "C-b"
    assert str(parse_keystroke("*S-a")) == "*S-a"
