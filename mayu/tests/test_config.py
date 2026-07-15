import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mayu.config import ConfigError, OutputAction, parse_string


def test_simple_keymap():
    cfg = parse_string("keymap Global\n  key C-b = Left\n")
    assert "Global" in cfg.keymaps
    entries = cfg.keymaps["Global"].entries
    assert len(entries) == 1
    pat, action = entries[0]
    assert pat.key == "b"
    assert isinstance(action, OutputAction)
    assert action.strokes[0].key == "Left"


def test_mod_assignment_default_and_add():
    cfg = parse_string("mod control += CapsLock\nkeymap Global\n")
    assert "CapsLock" in cfg.mod_assign["C"]
    assert "LeftControl" in cfg.mod_assign["C"]


def test_mod_replace():
    cfg = parse_string("mod control = CapsLock\n")
    assert cfg.mod_assign["C"] == {"CapsLock"}


def test_mod_remove():
    cfg = parse_string("mod control -= LeftControl\n")
    assert "LeftControl" not in cfg.mod_assign["C"]


def test_def_key():
    cfg = parse_string("def key MyKey = 0x1ff\nkeymap Global\n  key MyKey = a\n")
    assert cfg.keys.code("MyKey") == 0x1FF


def test_def_alias():
    cfg = parse_string("def alias Foo = LeftControl\n")
    assert cfg.keys.canonical("Foo") == "LeftControl"


def test_keymap_parent_chain():
    src = "keymap Base\n  key a = b\nkeymap Derived : Base\n  key c = d\n"
    cfg = parse_string(src)
    chain = [k.name for k in cfg.keymap_chain("Derived")]
    assert chain == ["Derived", "Base"]


def test_function_action():
    cfg = parse_string("keymap Global\n  key CapsLock = &Ignore\n")
    _, action = cfg.keymaps["Global"].entries[0]
    assert action.name == "Ignore"


def test_sequence_output():
    cfg = parse_string("keymap Global\n  key C-k = S-End Delete\n")
    _, action = cfg.keymaps["Global"].entries[0]
    assert len(action.strokes) == 2
    assert action.strokes[0].key == "End"
    assert action.strokes[1].key == "Delete"


def test_error_reports_line_number():
    with pytest.raises(ConfigError) as ei:
        parse_string("keymap Global\n  key = Left\n")
    assert "2 行目" in str(ei.value)


def test_unknown_directive():
    with pytest.raises(ConfigError):
        parse_string("frobnicate foo\n")


def test_include(tmp_path):
    inc = tmp_path / "base.mayu"
    inc.write_text("keymap Global\n  key a = b\n", encoding="utf-8")
    main = tmp_path / "main.mayu"
    main.write_text('include "base.mayu"\nkeymap Global\n  key c = d\n', encoding="utf-8")
    from mayu.config import parse_file
    cfg = parse_file(str(main))
    assert len(cfg.keymaps["Global"].entries) == 2
