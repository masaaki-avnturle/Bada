import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bada import lint, is_valid, Completer, prefix_at, is_reserved, is_builtin
from badatools import (VimParser, EmacsParser, BadaEditorTools,
                       PassphraseParser, UnifiedInputParser)
from silenttalk import synth_stream


class TestKeywords(unittest.TestCase):
    def test_reserved_and_builtin(self):
        self.assertTrue(is_reserved("while"))
        self.assertTrue(is_reserved("def"))
        self.assertFalse(is_reserved("gamma"))
        self.assertTrue(is_builtin("len"))
        self.assertFalse(is_builtin("while"))


class TestGrammarChecker(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(is_valid("x <- 1\nprint x * 2"))
        self.assertTrue(is_valid("-< 1 <-> 1 { say \"ok\" }"))  # dialect

    def test_syntax_error_has_line(self):
        ds = lint("x <- \nprint 1")
        self.assertTrue(ds)
        self.assertEqual(ds[0].severity, "error")
        self.assertEqual(ds[0].line, 2)

    def test_unknown_function(self):
        ds = lint("print nope(1)")
        self.assertTrue(any("unknown function" in d.message for d in ds))


class TestCompletion(unittest.TestCase):
    def setUp(self):
        self.c = Completer()
        self.src = "def gamma_power(s) { return s }\nr <- gamma_power(3)"

    def test_functional_completion(self):
        self.assertIn("return", self.c.complete_functional("re"))
        self.assertIn("repeat", self.c.complete_functional("re"))
        self.assertIn("len", self.c.complete_functional("le"))

    def test_word_completion_from_buffer(self):
        self.assertIn("gamma_power", self.c.complete_words(self.src, "gam"))

    def test_prefix_at(self):
        self.assertEqual(prefix_at("res <- gam", 10), "gam")
        self.assertEqual(prefix_at("res <- gam", 3), "res")


class TestEditorParsers(unittest.TestCase):
    def test_vim_modal(self):
        cmds = VimParser().parse(["i", "x", "ESC", ":wq"])
        self.assertEqual(cmds, [("mode", "INSERT"), ("text", "x"),
                                ("mode", "NORMAL"), ("save",), ("quit",)])

    def test_emacs_chords(self):
        cmds = EmacsParser().parse(["C-e", "z", "C-x C-s", "C-x C-c"])
        self.assertEqual(cmds, [("move", "EOL"), ("text", "z"),
                                ("save",), ("quit",)])

    def test_editor_tools_lint_and_complete(self):
        t = BadaEditorTools()
        lines = ["def f(x) { return x }", "y <- f"]
        self.assertTrue(t.is_valid(lines))
        cands, pre = t.complete(lines, 1, 6, "all")
        self.assertEqual(pre, "f")
        self.assertIn("f", cands)


class TestPassphrase(unittest.TestCase):
    def test_detects_watchwords(self):
        pp = PassphraseParser()
        got = pp.parse(["AI", "UO", "OE", "OA", "OA"])
        cmds = [g["command"] for g in got]
        self.assertEqual(cmds, ["UNLOCK", "RUN-SECRET"])

    def test_no_passphrase(self):
        self.assertFalse(PassphraseParser().matches(["OE", "IA", "IE"]))

    def test_from_frames(self):
        pp = PassphraseParser()
        frames = synth_stream(["AI", "UO"], hold=3)
        got = pp.from_frames(frames)
        self.assertEqual(got[0]["command"], "UNLOCK")

    def test_custom_table(self):
        pp = PassphraseParser({("OE", "OE"): "HELLO-HELLO"})
        self.assertEqual(pp.parse(["OE", "OE"])[0]["command"], "HELLO-HELLO")


class TestUnifiedParser(unittest.TestCase):
    def setUp(self):
        self.u = UnifiedInputParser()

    def test_silent_words_to_commands(self):
        r = self.u.from_silent_words(["AI", "EA", "UO", "OA"])
        self.assertEqual(r["commands"], [("mode", "INSERT"), ("text", "say "),
                                         ("mode", "NORMAL"), ("run",)])

    def test_silent_detects_passphrase(self):
        r = self.u.from_silent_words(["AI", "UO"])
        self.assertEqual(r["passphrases"][0]["command"], "UNLOCK")

    def test_keyboard_matches_silent_shape(self):
        kb = self.u.from_keyboard(["i", "ESC", "!"], "vim")["commands"]
        self.assertEqual(kb, [("mode", "INSERT"), ("mode", "NORMAL"),
                              ("run",)])

    def test_from_silent_frames(self):
        frames = synth_stream(["AI", "EA"], hold=3)
        r = self.u.from_silent_frames(frames)
        self.assertEqual(r["words"], ["AI", "EA"])
        self.assertEqual(r["commands"][0], ("mode", "INSERT"))


if __name__ == "__main__":
    unittest.main()
