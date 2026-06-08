import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bada import compile_source, disassemble, run_source
from bada.vm import BadaRuntimeError


def out_of(src: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        vm = run_source(src)
    return buf.getvalue().splitlines(), vm


class TestBadaLanguage(unittest.TestCase):
    def test_arithmetic_and_assign(self):
        out, _ = out_of("x <- 6\ny = 7\nprint x * y + 0")
        self.assertEqual(out, ["42"])

    def test_string_combine_emit(self):
        out, _ = out_of('say "Bada" >- " language"')
        self.assertEqual(out, ["Bada language"])

    def test_map_transform(self):
        out, _ = out_of("print [1, 2, 3] => 10")
        self.assertEqual(out, ["[10, 20, 30]"])

    def test_manifold_spawn_pair(self):
        out, _ = out_of("print 3 -< 4")
        self.assertEqual(out, ["[3, 4]"])

    def test_stream_forward_records(self):
        _, vm = out_of("[] >> [9]\n5 >> 0")
        self.assertIn(5, vm.stream)

    def test_tuplespace_push_pop(self):
        _, vm = out_of(
            "Omega::DATABASE[a] { push(1) push(2) }")
        self.assertEqual(vm.tuplespace["a"], [1, 2])

    def test_repeat_and_if(self):
        out, _ = out_of(
            "t <- 0\nrepeat 3 { t <- t + 10 }\n"
            "if t >= 30 { say \"ok\" } else { say \"no\" }")
        self.assertEqual(out, ["ok"])

    def test_while(self):
        out, _ = out_of("n <- 3\nwhile n > 0 { print n  n <- n - 1 }")
        self.assertEqual(out, ["3", "2", "1"])

    def test_division_by_zero(self):
        with self.assertRaises(BadaRuntimeError):
            run_source("print 1 / 0")

    def test_undefined_variable(self):
        with self.assertRaises(BadaRuntimeError):
            run_source("print zzz")

    def test_compiler_emits_halt(self):
        code = compile_source("x <- 1")
        self.assertEqual(code[-1][0], "HALT")
        self.assertIn("STORE", disassemble(code))

    def test_example_file_runs(self):
        path = os.path.join(os.path.dirname(__file__),
                            "..", "examples", "hello.bada")
        with open(path) as f:
            out, vm = out_of(f.read())
        self.assertIn("Bada language", out)
        self.assertIn("manifold converged", out)
        self.assertEqual(vm.tuplespace["akashic"], [42, "Bada language"])


if __name__ == "__main__":
    unittest.main()
