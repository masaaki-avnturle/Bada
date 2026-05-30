#!/usr/bin/env python3
"""Test suite for the Bada language.

Runs a set of programs through the full pipeline (lex -> parse -> compile ->
VM) and checks captured output or raised errors.  Run with:

    python3 tests/run_tests.py
"""

import io
import os
import sys
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from badalang.compiler import compile_source
from badalang.vm import VM
from badalang.errors import BadaError, BadaImmutableError, BadaTypeError

PASSED = 0
FAILED = 0


def run(src):
    """Compile and run a fresh program, returning its captured stdout."""
    code = compile_source(src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        VM().run_main(code)
    return buf.getvalue()


def expect(src, output, label):
    global PASSED, FAILED
    try:
        got = run(src)
    except Exception as e:  # noqa
        FAILED += 1
        print(f"FAIL  {label}: raised {type(e).__name__}: {e}")
        return
    if got == output:
        PASSED += 1
        print(f"ok    {label}")
    else:
        FAILED += 1
        print(f"FAIL  {label}\n   expected: {output!r}\n   got:      {got!r}")


def expect_error(src, error_type, label):
    global PASSED, FAILED
    try:
        run(src)
    except error_type:
        PASSED += 1
        print(f"ok    {label}")
        return
    except Exception as e:  # noqa
        FAILED += 1
        print(f"FAIL  {label}: raised {type(e).__name__}, expected {error_type.__name__}")
        return
    FAILED += 1
    print(f"FAIL  {label}: no error raised, expected {error_type.__name__}")


# --- arithmetic & variables ------------------------------------------------

expect("print 1 + 2 * 3", "7\n", "arithmetic precedence")
expect("print (1 + 2) * 3", "9\n", "parentheses")
expect("let x <- 10\nx <- x + 5\nprint x", "15\n", "reassignment")
expect("print 10 / 4", "2.5\n", "float division")
expect("print 17 % 5", "2\n", "modulo")
expect("print -5 + 3", "-2\n", "unary minus")
expect('print "a" + "b" + "c"', "abc\n", "string concat")
expect('print "ab" * 3', "ababab\n", "string repeat")

# --- comparison & logic ----------------------------------------------------

expect("print 3 < 5", "true\n", "less than")
expect("print 5 == 5", "true\n", "equality")
expect("print 5 != 5", "false\n", "inequality")
expect("print true and false", "false\n", "and")
expect("print true or false", "true\n", "or")
expect("print not true", "false\n", "not")
expect("print 1 < 2 and 2 < 3", "true\n", "chained logic")

# --- collections -----------------------------------------------------------

expect("let a <- [1, 2, 3]\nprint a[1]", "2\n", "list index")
expect("let a <- [1, 2, 3]\npush(a, 4)\nprint len(a)", "4\n", "list push/len")
expect('let m <- {"a": 1}\nm["b"] <- 2\nprint m["b"]', "2\n", "map set/get")
expect("let a <- [10, 20]\na[0] <- 99\nprint a[0]", "99\n", "list index assign")

# --- control flow ----------------------------------------------------------

expect("if 1 < 2 { print \"yes\" } else { print \"no\" }", "yes\n", "if true")
expect("if 1 > 2 { print \"yes\" } else { print \"no\" }", "no\n", "if false")
expect("let s <- 0\nfor i in range(5) { s <- s + i }\nprint s", "10\n", "for range")
expect("let i <- 0\nwhile i < 3 { i <- i + 1 }\nprint i", "3\n", "while")
expect("for i in range(10) { if i == 3 { break } print i }",
       "0\n1\n2\n", "break")
expect("for i in range(5) { if i % 2 == 0 { continue } print i }",
       "1\n3\n", "continue")

# --- functions & closures --------------------------------------------------

expect("fun sq(x) { return x * x }\nprint sq(7)", "49\n", "function")
expect("fun f(n) { if n <= 1 { return 1 } return n * f(n - 1) }\nprint f(5)",
       "120\n", "recursion")
expect("fun mk(n) { fun add(x) { return x + n } return add }\n"
       "let a <- mk(100)\nprint a(1)", "101\n", "closure")

# --- OOP -------------------------------------------------------------------

expect(
    "class C { field v\n method init(v) { self.v <- v }\n"
    " method get() { return self.v } }\n"
    "let c <- C.new(42)\nprint c.get()",
    "42\n", "class fields/methods")

expect(
    "class A { method who() { return \"A\" } }\n"
    "class B <- A { method who() { return \"B/\" + super.who() } }\n"
    "print B.new().who()",
    "B/A\n", "inheritance + super")

expect(
    "class V { field x\n method init(x) { self.x <- x }\n"
    " operator + (o) { return V.new(self.x + o.x) } }\n"
    "let r <- V.new(2) + V.new(3)\nprint r.x",
    "5\n", "operator overloading")

# --- TupleSpace ------------------------------------------------------------

expect(
    'let db <- TupleSpace.new()\ndb.push("k", 7)\nprint db.get("k")',
    "7\n", "tuplespace push/get")
expect_error(
    'let db <- TupleSpace.new()\ndb.push("k", 1)\ndb.push("k", 2)',
    BadaImmutableError, "tuplespace write-once")
expect(
    'let db <- Omega::DATABASE.new("ak")\ndb.push("a", 1)\nprint db.has("a")',
    "true\n", "Omega::DATABASE namespace")

# --- operator-algebra ------------------------------------------------------

expect("print gamma(5)", "24.0\n", "gamma")
expect("print beta(2, 3)", "0.08333333333333333\n", "beta")
expect("print 2 -< 3", "0.08333333333333333\n", "manifold branch operator")

# --- errors ----------------------------------------------------------------

expect_error("print undefined_var", BadaError, "undefined name")
expect_error("print 1 + \"a\"", BadaError, "type error on bad +")
expect_error("let a <- [1]\nprint a[5]", BadaError, "index out of range")

# --- summary ---------------------------------------------------------------

print(f"\n{PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
