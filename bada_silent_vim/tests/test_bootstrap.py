"""Self-hosting: the Reviser written in Bada, and the C backend that emits an
executable per Bada method command."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
from bada import revise
from bada.lexer import tokenize


def _vals(src):
    return [t.value for t in tokenize(src) if t.kind != "EOF"]


class TestBadaReviser(unittest.TestCase):
    def test_token_mapping(self):
        self.assertEqual(
            bootstrap.bada_revise_tokens(["if", "a", "==", "b", "=", "while"]),
            ["-<", "a", "<->", "b", "<-", "->"])

    def test_matches_python_reviser(self):
        for src in ("if a == b { x = 1 } else { x = 2 }",
                    "while n > 0 { n = n - 1 }",
                    "def f(x) { if x == 0 { return 1 } }"):
            with self.subTest(src=src):
                self.assertEqual(bootstrap.bada_revise_tokens(_vals(src)),
                                 _vals(revise(src)))

    def test_unmapped_tokens_unchanged(self):
        self.assertEqual(bootstrap.bada_revise_tokens(["print", "x", "+", "1"]),
                         ["print", "x", "+", "1"])


class TestManifestFromBada(unittest.TestCase):
    def test_manifest_produced_by_bada(self):
        m = bootstrap.command_manifest()
        for w in ("print", "if", "while", "len", "idiv", "add", "eq"):
            self.assertIn(w, m)
        self.assertEqual(len(m), 29)


@unittest.skipIf(shutil.which("cc") is None, "no C compiler")
class TestCBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cbackend import generate, build
        cls.dir = tempfile.mkdtemp(prefix="cbk_")
        cls.manifest = generate(cls.dir)
        cls.bins = build(cls.dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def _run(self, name, *args):
        path = os.path.join(self.dir, "bin", name)
        return subprocess.run([path, *args], capture_output=True,
                              text=True).stdout.strip()

    def test_sources_generated(self):
        for name in self.manifest:
            self.assertTrue(os.path.exists(
                os.path.join(self.dir, f"cmd_{name}.c")))
        self.assertTrue(os.path.exists(os.path.join(self.dir, "Makefile")))

    def test_all_built(self):
        self.assertEqual(sorted(self.bins), sorted(self.manifest))

    def test_arithmetic_commands(self):
        self.assertEqual(self._run("idiv", "17", "5"), "3")
        self.assertEqual(self._run("imod", "17", "5"), "2")
        self.assertEqual(self._run("add", "2", "3"), "5")
        self.assertEqual(self._run("mul", "6", "7"), "42")
        self.assertEqual(self._run("abs", "-4"), "4")
        self.assertEqual(self._run("pow2", "5"), "32")

    def test_compare_commands(self):
        self.assertEqual(self._run("eq", "5", "5"), "true")
        self.assertEqual(self._run("lt", "3", "9"), "true")
        self.assertEqual(self._run("gt", "3", "9"), "false")

    def test_word_commands(self):
        self.assertEqual(self._run("len", "a", "b", "c"), "3")
        self.assertEqual(self._run("print", "hi", "there"), "hi there")
        self.assertEqual(self._run("true"), "true")
        self.assertIn("branch object", self._run("if"))

    def test_division_by_zero_fails(self):
        path = os.path.join(self.dir, "bin", "idiv")
        rc = subprocess.run([path, "1", "0"], capture_output=True).returncode
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
