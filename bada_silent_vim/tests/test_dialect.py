"""The instruction-oriented ("directive object") dialect and the reviser."""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bada import compile_source, run_source, revise


def out_of(src: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(src)
    return buf.getvalue().splitlines()


class TestDialectRuns(unittest.TestCase):
    def test_branch_merge(self):
        out = out_of('-< 6 * 7 <-> 42 { say "yes" } >- { say "no" }')
        self.assertEqual(out, ["yes"])

    def test_branch_no_merge(self):
        self.assertEqual(out_of('-< 1 <-> 2 { say "x" }'), [])

    def test_transition_loop(self):
        out = out_of("n <- 3\nt <- 0\n-> n > 0 { t <- t + 10  n <- n - 1 }\n"
                     "print t")
        self.assertEqual(out, ["30"])

    def test_comparison_object(self):
        self.assertEqual(out_of("print 5 <-> 5"), ["true"])
        self.assertEqual(out_of("print 5 <-> 6"), ["false"])

    def test_dialect_in_function_conditional(self):
        out = out_of(
            "def sgn(x) { -< x > 0 { return 1 } >- { return 0 } }\n"
            "print sgn(7)\nprint sgn(-7)")
        self.assertEqual(out, ["1", "0"])

    def test_line_leading_directive_not_absorbed_as_pipe(self):
        # `7` then a new line starting with `-<` must NOT become `7 -< ...`
        out = out_of('x <- 7\n-< x <-> 7 { say "ok" }')
        self.assertEqual(out, ["ok"])

    def test_expression_pipe_still_works_same_line(self):
        # `-<` / `>-` keep their expression meaning within a line
        self.assertEqual(out_of("print 3 -< 4"), ["[3, 4]"])
        self.assertEqual(out_of('say "a" >- "b"'), ["ab"])


class TestReviser(unittest.TestCase):
    def test_keyword_and_operator_mapping(self):
        src = "if a == b { x = 1 } else { x = 2 }\nwhile a < b { a = a + 1 }"
        r = revise(src)
        self.assertIn("-<", r)
        self.assertIn("<->", r)
        self.assertIn(">-", r)
        self.assertIn("->", r)
        self.assertNotIn("if ", r)
        self.assertNotIn("while ", r)
        self.assertNotIn("else", r)
        self.assertNotIn("==", r)

    def test_preserves_comments_and_strings(self):
        src = '// if a == b else while\nsay "if a == b"'
        r = revise(src)
        self.assertIn("// if a == b else while", r)
        self.assertIn('"if a == b"', r)

    def test_preserves_expression_pipe_operators(self):
        src = "p <- a -< b\nq <- a >- b\nr <- a => b"
        self.assertEqual(revise(src), src)   # nothing to change

    def test_does_not_touch_relational_equalities(self):
        src = "x <- a <= b\ny <- a >= b\nz <- a != b\nm <- a => b"
        self.assertEqual(revise(src), src)

    def test_semantics_preserving(self):
        src = ("t <- 0\nn <- 4\nwhile n > 0 { if n == 2 { t = t + 100 } "
               "else { t = t + 1 }  n = n - 1 }\nprint t")
        self.assertEqual(compile_source(src), compile_source(revise(src)))
        self.assertEqual(out_of(src), out_of(revise(src)))

    def test_idempotent(self):
        src = "if a == b { x = 1 }"
        once = revise(src)
        self.assertEqual(once, revise(once))


if __name__ == "__main__":
    unittest.main()
