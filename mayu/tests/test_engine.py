import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mayu.backends.simulate import SimulateBackend, expand_taps, format_taps
from mayu.config import parse_string
from mayu.engine import Engine, InputEvent


def sim(source: str, keys: str, keymap: str = "Global") -> str:
    engine = Engine(parse_string(source), keymap=keymap)
    backend = SimulateBackend(engine)
    return format_taps(backend.translate_spec(keys))


def test_simple_remap():
    out = sim("keymap Global\n  key C-b = Left\n", "C-b")
    assert out == "Left"


def test_multiple_remaps():
    src = ("keymap Global\n"
           "  key C-b = Left\n"
           "  key C-f = Right\n")
    assert sim(src, "C-b C-f") == "Left Right"


def test_unmapped_passthrough():
    # mayu では物理キー 'a' の名前は "A"。未マップなので素通し。
    out = sim("keymap Global\n  key C-b = Left\n", "a")
    assert out == "A"


def test_unmapped_with_modifier_passthrough():
    # C-x はマップされていないので Control 付きで素通し
    out = sim("keymap Global\n  key C-b = Left\n", "C-x")
    assert out == "C-X"


def test_ignore_swallows_key():
    out = sim("keymap Global\n  key CapsLock = &Ignore\n", "CapsLock")
    assert out == ""


def test_sequence_output():
    out = sim("keymap Global\n  key C-k = S-End Delete\n", "C-k")
    assert out == "S-End Delete"


def test_caps_as_control():
    # CapsLock を Control にして CapsLock+b -> Left
    src = ("mod control += CapsLock\n"
           "keymap Global\n"
           "  key CapsLock = &Ignore\n"
           "  key C-b = Left\n")
    engine = Engine(parse_string(src))
    backend = SimulateBackend(engine)
    events = [
        InputEvent("CapsLock", True),
        InputEvent("b", True),
        InputEvent("b", False),
        InputEvent("CapsLock", False),
    ]
    assert format_taps(backend.translate(events)) == "Left"


def test_modifier_hold_reaches_output_key():
    # Shift を押しながら未マップの 'a' -> S-A で素通し
    out = sim("keymap Global\n  key C-b = Left\n", "S-a")
    assert out == "S-A"


def test_remap_output_carries_new_modifier():
    # C-b を S-Left に変換 (down/up が正しく対になること)
    engine = Engine(parse_string("keymap Global\n  key C-b = S-Left\n"))
    backend = SimulateBackend(engine)
    raw = backend.translate_spec("C-b")
    # 生イベントで down/up がバランスすること
    from collections import Counter
    downs = Counter(e.key for e in raw if e.pressed)
    ups = Counter(e.key for e in raw if not e.pressed)
    assert downs == ups


def test_hold_remap_preserves_repeat_key_state():
    # 再割り当てキーは down のとき出力 down、up のとき出力 up
    engine = Engine(parse_string("keymap Global\n  key A = Z\n"))
    backend = SimulateBackend(engine)
    events = [InputEvent("A", True), InputEvent("A", False)]
    raw = backend.translate(events)
    assert [(e.key, e.pressed) for e in raw] == [("Z", True), ("Z", False)]


def test_keymap_selection():
    src = ("keymap Global\n  key a = x\n"
           "keymap Alt\n  key a = y\n")
    assert sim(src, "a", keymap="Global") == "X"
    assert sim(src, "a", keymap="Alt") == "Y"


def test_dont_care_modifier_match():
    # *C-b は他修飾があってもマッチ
    out = sim("keymap Global\n  key *C-b = Left\n", "C-S-b")
    assert out == "Left"


def test_expand_taps_structure():
    events = expand_taps("C-b")
    seq = [(e.key, e.pressed) for e in events]
    assert seq == [
        ("LeftControl", True),
        ("b", True),
        ("b", False),
        ("LeftControl", False),
    ]


def test_all_down_up_balanced_across_examples():
    src = ("mod control += CapsLock\n"
           "keymap Global\n"
           "  key CapsLock = &Ignore\n"
           "  key C-b = Left\n"
           "  key C-f = Right\n"
           "  key C-k = S-End Delete\n")
    engine = Engine(parse_string(src))
    backend = SimulateBackend(engine)
    raw = backend.translate_spec("C-b C-f C-k a S-x")
    from collections import Counter
    downs = Counter(e.key for e in raw if e.pressed)
    ups = Counter(e.key for e in raw if not e.pressed)
    assert downs == ups, f"down/up 不均衡: {downs} vs {ups}"
