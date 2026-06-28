"""The vim written in Bada (vimbada/) + its C receiver / class-method binaries.

Covers:
  * the modal editor in Bada (insert + command mode) via the bridge,
  * the bada.vim plugin loading headlessly in Vim (if vim is present),
  * the C *receiver* + *class-method* executables compiling and producing the
    same buffer as the Bada vim for an equivalent edit script.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from vimbada import bridge, cbackend_vim


class TestBadaVim(unittest.TestCase):
    """The modal editor implemented in the Bada language."""

    def test_insert_newline_command(self):
        r = bridge.run(["i", "h", "e", "l", "l", "o", "RET",
                        "w", "o", "r", "l", "d", "ESC", ":wq"])
        self.assertEqual(r["text"], "hello\nworld")
        self.assertEqual(r["mode"], "N")        # back to NORMAL after ESC
        self.assertEqual(r["lastcmd"], "wq")

    def test_type_text_helper(self):
        r = bridge.type_text("abc\ndef")
        self.assertEqual(r["text"], "abc\ndef")
        self.assertEqual(r["mode"], "N")

    def test_normal_mode_delete(self):
        # type "abc", go to col 0, delete -> "bc"
        r = bridge.run(["i", "a", "b", "c", "ESC", "0", "x"])
        self.assertEqual(r["text"], "bc")

    def test_open_line_below(self):
        r = bridge.run(["i", "x", "ESC", "o", "y", "ESC"])
        self.assertEqual(r["text"], "x\ny")

    def test_delete_line(self):
        r = bridge.run(["i", "a", "b", "ESC", "dd"])
        self.assertEqual(r["text"], "")

    def test_backspace_joins_lines(self):
        # two lines "a","b"; re-enter insert at col 0 of line 2; BS joins them
        r = bridge.run(["i", "a", "RET", "b", "ESC", "i", "BS"])
        self.assertEqual(r["text"], "ab")


class TestCBinaries(unittest.TestCase):
    """The C receiver + class-method executables."""

    @classmethod
    def setUpClass(cls):
        if shutil.which("cc") is None and shutil.which("gcc") is None:
            raise unittest.SkipTest("no C compiler available")
        cls.tmp = tempfile.mkdtemp()
        cls.info = cbackend_vim.generate(cls.tmp)
        cls.bins = cbackend_vim.build(cls.tmp)
        cls.bindir = os.path.join(cls.tmp, "bin")
        cls.buf = os.path.join(cls.tmp, "buf.txt")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _recv(self, *args):
        return subprocess.run(
            [os.path.join(self.bindir, "bada_vim"), self.buf, *map(str, args)],
            capture_output=True, text=True)

    def test_all_binaries_built(self):
        expect = set(cbackend_vim.METHODS) | {"bada_vim"}
        self.assertEqual(set(self.bins), expect)

    def test_receiver_rejects_unknown_method(self):
        open(self.buf, "w").close()
        r = self._recv("nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown method", r.stderr)

    def test_receiver_matches_bada_vim(self):
        # build "hello\nworld" through the C receiver dispatching class methods
        open(self.buf, "w").close()
        self._recv("vim_insert", 0, 0, "hello")
        self._recv("vim_appendline", 0)
        self._recv("vim_insert", 1, 0, "world")
        c_text = self._recv("vim_show").stdout.rstrip("\n")

        # the same edit through the vim written in Bada
        b = bridge.run(["i", "h", "e", "l", "l", "o", "RET",
                        "w", "o", "r", "l", "d", "ESC"])
        self.assertEqual(c_text, b["text"])
        self.assertEqual(c_text, "hello\nworld")

    def test_class_methods_edit(self):
        open(self.buf, "w").close()
        self._recv("vim_insert", 0, 0, "orld")
        self._recv("vim_newline", 0, 2)          # split "orld" -> "or","ld"
        self.assertEqual(self._recv("vim_show").stdout.rstrip("\n"), "or\nld")
        self._recv("vim_deleteline", 0)          # remove "or"
        self.assertEqual(self._recv("vim_show").stdout.rstrip("\n"), "ld")
        self._recv("vim_delete", 0, 0)           # "ld" -> "d"
        self.assertEqual(self._recv("vim_show").stdout.rstrip("\n"), "d")


class TestBadaVimPlugin(unittest.TestCase):
    """The bada.vim plugin (filetype / completion) loads in headless Vim."""

    def test_plugin_loads(self):
        if shutil.which("vim") is None:
            self.skipTest("vim not installed")
        plugin = os.path.join(_ROOT, "vimbada", "bada.vim")
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "x.bada")
            open(f, "w").write("def f(x) { return x }\n")
            out = os.path.join(d, "out.txt")
            env = dict(os.environ, BADA_HOME=_ROOT)
            subprocess.run(
                ["vim", "-Nu", "NONE", "-es",
                 "-c", f"source {plugin}",
                 "-c", f"edit {f}",
                 "-c", f"redir! > {out} | echo &filetype | redir END",
                 "-c", "qa!"],
                env=env, capture_output=True, text=True)
            self.assertIn("bada", open(out).read())


if __name__ == "__main__":
    unittest.main()
