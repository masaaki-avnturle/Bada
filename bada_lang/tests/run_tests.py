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

# --- reviser ---------------------------------------------------------------

expect(
    'reviser { word "表示" => "print" }\n表示 "hi"',
    "hi\n", "reviser word rewrite")
expect(
    'reviser { op "←" => "<-" }\nlet x ← 9\nprint x',
    "9\n", "reviser operator rewrite")
expect(
    'reviser { word "fun" => "fun" }\nprint "kept literal: 表示"',
    "kept literal: 表示\n", "reviser leaves strings untouched")
expect(
    'reviser { word "F" => "fun" }\nF g() { return 5 }\nprint g()',
    "5\n", "reviser custom keyword")

# --- garbage collection ----------------------------------------------------

expect(
    "class N { method init() {} }\n"
    "let keep <- N.new()\nN.new()\nN.new()\n"
    "print gc_collect() >= 2",
    "true\n", "gc reclaims unreachable instances")
expect(
    "class N { field tag\n method init(t) { self.tag <- t }\n"
    " method __finalize__() { print \"bye\", self.tag } }\n"
    "N.new(7)\ngc_collect()",
    "bye 7\n", "gc runs finalizer")
expect(
    "let a <- [1, 2, 3]\ngc_collect()\nprint a[2]",
    "3\n", "gc keeps reachable list")
expect(
    "gc_disable()\nlet s <- gc_stats()\nprint s[\"enabled\"]",
    "false\n", "gc enable/disable")

# --- exceptions ------------------------------------------------------------

expect(
    'try { throw "x" } catch (e) { print "caught", e }',
    "caught x\n", "throw/catch")
expect(
    'try { print 1 } catch (e) { print 2 } finally { print 3 }',
    "1\n3\n", "finally on normal path")
expect(
    'try { throw "e" } catch (x) { print "c" } finally { print "f" }',
    "c\nf\n", "finally on caught path")
expect(
    'try { let a <- [1]\nprint a[9] } catch (e) { print e["type"] }',
    "RuntimeError\n", "catch builtin error as map")
expect(
    'try { try { throw "boom" } finally { print "inner" } } '
    'catch (e) { print "outer", e }',
    "inner\nouter boom\n", "nested try reraise through finally")
expect(
    'fun f() { try { throw 42 } catch (e) { return e } }\nprint f()',
    "42\n", "throw non-string value")

# --- file I/O --------------------------------------------------------------

expect(
    'let p <- "/tmp/_bada_test_io.txt"\n'
    'write_file(p, "hello")\nappend_file(p, " world")\n'
    'print read_file(p)\ndelete_file(p)',
    "hello world\n", "write/append/read file")
expect(
    'let p <- "/tmp/_bada_test_lines.txt"\n'
    'write_file(p, "a\\nb\\nc")\nprint len(read_lines(p))\ndelete_file(p)',
    "3\n", "read_lines")
expect(
    'let p <- "/tmp/_bada_test_h.txt"\n'
    'let f <- open(p, "w")\nf.write("xyz")\nf.close()\n'
    'let g <- open(p, "r")\nprint g.read()\ng.close()\ndelete_file(p)',
    "xyz\n", "file handle write/read")
expect_error(
    'read_file("/no/such/path/here.txt")',
    BadaError, "read_file missing -> error")

# --- import / libraries ----------------------------------------------------

expect("import mathx\nprint mathx.gcd(12, 18)", "6\n", "import library function")
expect("import collections\n"
       "let s <- collections.Stack.new()\ns.push(5)\nprint s.pop()",
       "5\n", "import library class")
expect("import mathx as M\nprint M.is_prime(13)", "true\n", "import as alias")
expect("import Omega::DATABASE as DB\n"
       "let d <- DB.new()\nd.push(\"k\", 1)\nprint d.get(\"k\")",
       "1\n", "import builtin namespace member")
expect_error("import no_such_library_xyz", BadaError, "missing module -> error")

# --- regular expressions ---------------------------------------------------

expect('let r <- regex("[0-9]+")\nprint r.test("abc123")', "true\n", "regex test")
expect('let r <- regex("[0-9]+")\nprint r.find_all("a1 b22 c3")',
       '["1", "22", "3"]\n', "regex find_all")
expect('let r <- regex("\\\\s+")\nprint r.replace("a b  c", "_")',
       "a_b_c\n", "regex replace")
expect('let r <- regex("(\\\\d+)-(\\\\d+)")\nprint r.match("12-34")[1]',
       "12\n", "regex capture group")
expect('print re_test("^\\\\d+$", "999")', "true\n", "re_test builtin")
expect('print re_replace("[aeiou]", "cat", "*")', "c*t\n", "re_replace builtin")

# --- calculus / differential equations -------------------------------------

expect("fun f(x) { return x * x }\nprint round(derivative(f, 3), 3)",
       "6.0\n", "numerical derivative")
expect("fun f(x) { return x * x }\nprint round(integrate(f, 0, 1, 1000), 4)",
       "0.3333\n", "definite integral (Simpson)")
expect("fun one(x, y) { return 1 }\nprint round(integrate2(one, 0, 2, 0, 3), 4)",
       "6.0\n", "double integral over a patch")
expect("fun g(x) { return x * x - 2 }\nprint round(newton(g, 1), 6)",
       "1.414214\n", "newton root finding")
expect("fun dy(t, y) { return y }\n"
       "let s <- solve_ode(dy, 1, 0, 1, 200)\n"
       "print round(s[len(s)-1][1], 4)",
       "2.7183\n", "ODE solver (RK4) -> e")
expect("fun gg(p) { return p[0]*p[0] + 3*p[1] }\n"
       "let g <- gradient(gg, [2, 5])\nprint round(g[0], 3), round(g[1], 3)",
       "4.0 3.0\n", "gradient (approx)")

# --- threading -------------------------------------------------------------

expect("fun sq(n) { return n * n }\nlet t <- spawn(sq, 7)\nprint t.join()",
       "49\n", "spawn + join returns result")
expect("let ch <- Channel.new()\n"
       "fun send_it(x) { ch.send(x * 2) }\n"
       "spawn(send_it, 21)\nprint ch.receive()",
       "42\n", "channel send/receive across threads")
expect("let lock <- Mutex.new()\nlet box <- {\"n\": 0}\n"
       "fun add(k) { let i <- 0\n while i < k { lock.lock()\n"
       " box[\"n\"] <- box[\"n\"] + 1\n lock.unlock()\n i <- i + 1 } }\n"
       "let a <- spawn(add, 500)\nlet b <- spawn(add, 500)\n"
       "a.join()\nb.join()\nprint box[\"n\"]",
       "1000\n", "mutex protects shared state")

# --- manifolds & topology (advanced math overloading) ----------------------

expect("import manifold\n"
       "let a <- manifold.Vector.new([1,2,2])\nprint a.norm()",
       "3.0\n", "manifold vector norm")
expect("import manifold\n"
       "let a <- manifold.Vector.new([1,2,3])\n"
       "let b <- manifold.Vector.new([4,5,6])\nprint a -< b",
       "32\n", "manifold vector dot via -< operator")
expect("import topology\n"
       "let c <- topology.Complex.new(4, 6, 4)\nprint c.euler()",
       "2\n", "euler characteristic of tetrahedron")
expect("import topology\n"
       "let a <- topology.Loop.new(\"a\")\n"
       "print (a * a.inverse()).is_identity()",
       "true\n", "fundamental group: a * a^-1 = identity")
expect("import topology\n"
       "let a <- topology.Loop.new(\"a\")\nlet b <- topology.Loop.new(\"b\")\n"
       "print (a * b).show()",
       "ab\n", "fundamental group composition")
expect("import topology\n"
       "let p <- topology.Loop.new(\"abB\")\nlet a <- topology.Loop.new(\"a\")\n"
       "print p == a",
       "true\n", "loop homotopy via free reduction")

# --- media: images, gif, x-ray --------------------------------------------

expect('let im <- image(8, 8, "L", 0)\nim.set(3, 3, 200)\nprint im.get(3, 3)',
       "200\n", "image set/get pixel")
expect('let im <- image(4, 4, "L", 0)\nim.fill(99)\nprint im.get(0, 0), im.get(3, 3)',
       "99 99\n", "image fill")
expect('let im <- image(6, 6, "L", 7)\nprint im.save("/tmp/_bada_t.pgm")\n'
       'print read_file("/tmp/_bada_t.pgm")[0]\ndelete_file("/tmp/_bada_t.pgm")',
       "/tmp/_bada_t.pgm\nP\n", "image saves a PGM file")
expect('let g <- gif("/tmp/_bada_t.gif", 8, 8, 5, 0)\n'
       'g.add(image(8, 8, "L", 10))\ng.add(image(8, 8, "L", 250))\n'
       'g.save()\nprint g.frame_count\ndelete_file("/tmp/_bada_t.gif")',
       "2\n", "gif collects frames and saves")
expect("import xray\n"
       "let s <- xray.chest_phantom(40, 48)\ns.expose()\n"
       "let surf <- s.surface()\n"
       "print surf.get(20, 24) > surf.get(7, 24)",
       "true\n", "x-ray: bone attenuates more than lung")
expect("import xray\n"
       "let s <- xray.chest_phantom(30, 30)\n"
       "print round(s.ray_intensity(15, 30), 0) <= 255",
       "true\n", "x-ray Beer-Lambert ray intensity bounded")

# --- brain imaging: thermal entropy & modalities ---------------------------

expect("print round(gamma_entropy(1, 1), 4)", "1.0\n", "gamma entropy at k=1,theta=1")
expect("print gamma_entropy(3, 2) > gamma_entropy(3, 1)", "true\n",
       "entropy grows with theta")
expect("let im <- image(20, 20, \"L\", 0)\n"
       "field_project(im, [[10, 10, 4, 1, 2]], 0, 200, false)\n"
       "print im.get(10, 10) > im.get(0, 0)",
       "true\n", "field_project peaks at the source")
expect("let im <- image(16, 16, \"L\", 0)\n"
       "field_project(im, [[8, 8, 3, 1, 2]], 0, 100, true)\n"
       "let plain <- image(16, 16, \"L\", 0)\n"
       "field_project(plain, [[8, 8, 3, 1, 2]], 0, 100, false)\n"
       "print im.get(8, 8) >= plain.get(8, 8)",
       "true\n", "entropy weighting raises activation")
expect("import neuro\n"
       "let b <- neuro.default_brain(40, 40)\n"
       "b.render_mri(\"/tmp/_bt_mri.pgm\")\n"
       "print file_exists(\"/tmp/_bt_mri.pgm\")\ndelete_file(\"/tmp/_bt_mri.pgm\")",
       "true\n", "neuro MRI renders a file")
expect("import neuro\n"
       "let b <- neuro.default_brain(40, 40)\n"
       "let ch <- b.eeg([[20, 30], [20, 10]], 1, 32)\n"
       "print len(ch), len(ch[0])",
       "2 32\n", "neuro EEG channels and samples")

# --- audio & haptic biofeedback --------------------------------------------

expect("import audio\n"
       "let t <- audio.note(440, 1, 8000, 0.5)\nprint len(t)",
       "8000\n", "audio note sample count")
expect("import audio\n"
       "let s <- audio.relief_soundscape(1, 1, 8000)\n"
       "audio.save(\"/tmp/_bt.wav\", s, 8000)\n"
       "print file_exists(\"/tmp/_bt.wav\")\ndelete_file(\"/tmp/_bt.wav\")",
       "true\n", "audio writes a WAV file")
expect("import haptic\n"
       "let a <- haptic.Actuator.new(\"chest\", 0, 0)\n"
       "a.soothe(1, 1, 100)\nprint a.delivered() > 0",
       "true\n", "haptic soothe delivers signal")
expect("import haptic\n"
       "let a <- haptic.Actuator.new(\"chest\", 0, 0)\n"
       "let hi <- a.soothe(1, 1, 100)\nlet d1 <- a.delivered()\n"
       "a.soothe(0.2, 1, 100)\nprint d1 > a.delivered()",
       "true\n", "haptic intensity scales delivery")

# --- YamaguchiHealth medication biofeedback --------------------------------

expect("import yamaguchi_health as yh\n"
       "let c <- yh.Clinic.new(40, 40)\nc.symptom(\"striatum\", 1)\n"
       "let e <- c.administer(\"risperidone\", 1)\nprint e[\"relief\"] > 0",
       "true\n", "risperidone produces relief")
expect("import yamaguchi_health as yh\n"
       "let c <- yh.Clinic.new(40, 40)\nc.symptom(\"vasomotor\", 1)\n"
       "let e <- c.administer(\"amlodipine\", 1)\nprint e[\"haptic_region\"]",
       "chest\n", "antihypertensive haptic targets the chest")
expect("import yamaguchi_health as yh\n"
       "let c <- yh.Clinic.new(40, 40)\nc.symptom(\"striatum\", 1)\n"
       "let before <- c.total_tension()\nc.administer(\"risperidone\", 1)\n"
       "print c.total_tension() < before",
       "true\n", "treatment lowers total tension")
expect("import yamaguchi_health as yh\n"
       "let c <- yh.Clinic.new(40, 40)\n"
       "try { c.administer(\"aspirin\", 1) } catch (e) { print \"caught\" }",
       "caught\n", "unknown drug throws")
expect("import yamaguchi_health as yh\n"
       "let c <- yh.Clinic.new(40, 40)\nc.symptom(\"gut_myenteric\", 1)\n"
       "let e <- c.administer(\"sennoside\", 1)\nprint e[\"haptic_region\"]",
       "abdomen\n", "sennoside targets the abdomen")

# --- binaural audio & psychotropic biofeedback -----------------------------

expect("import audio\n"
       "let bb <- audio.binaural(200, 10, 1, 8000, 0.5)\n"
       "print len(bb), len(bb[0]), len(bb[1])",
       "2 8000 8000\n", "binaural returns two channels")
expect("import audio\nprint audio.band_beat(\"delta\"), audio.band_beat(\"alpha\")",
       "2.5 10\n", "EEG band beat frequencies")
expect("let s <- binaural_soundscape(180, 6, 0.8, 1, 8000)\n"
       "print len(s[0]) == 8000 and len(s[1]) == 8000",
       "true\n", "native binaural soundscape length")
expect("let s <- binaural_soundscape(180, 6, 0.5, 1, 8000)\n"
       "write_wav_stereo(\"/tmp/_bt2.wav\", s[0], s[1], 8000)\n"
       "print file_exists(\"/tmp/_bt2.wav\")\ndelete_file(\"/tmp/_bt2.wav\")",
       "true\n", "stereo WAV writes a file")
expect("import psychotropic as ps\n"
       "let c <- ps.SoundClinic.new()\nprint len(c.names())",
       "10\n", "psychotropic formulary size")
expect("import psychotropic as ps\n"
       "let c <- ps.SoundClinic.new()\n"
       "let e <- c.dose(\"flunitrazepam\", 1, 1, \"/tmp/_bt3.wav\")\n"
       "print e[\"band\"]\ndelete_file(\"/tmp/_bt3.wav\")",
       "delta\n", "hypnotic targets the delta band")
expect("import psychotropic as ps\n"
       "let c <- ps.SoundClinic.new()\n"
       "let hyp <- c.relief_of(c.drugs[\"flunitrazepam\"], 1)\n"
       "let ad <- c.relief_of(c.drugs[\"snri\"], 1)\n"
       "print hyp > ad",
       "true\n", "hypnotic gives more relief than SNRI")
expect("import psychotropic as ps\n"
       "let c <- ps.SoundClinic.new()\n"
       "try { c.dose(\"aspirin\", 1, 1, \"/tmp/x.wav\") } catch (e) { print \"caught\" }",
       "caught\n", "unknown psychotropic throws")

# --- CT / labtest / genomics / basal ganglia -------------------------------

expect("let im <- image(32,32,\"L\",0)\nim.set(16,16,200)\n"
       "let s <- ct_sinogram(im, 30)\nprint s.height",
       "30\n", "CT sinogram angle count")
expect("let im <- image(24,24,\"L\",0)\nim.fill(50)\n"
       "let r <- ct_reconstruct(im, 40, true)\nprint r.width",
       "24\n", "CT reconstruct size")
expect("import labtest\nlet a <- labtest.Analyzer.new()\n"
       "let e <- a.measure(\"glucose\", 200)\nprint e[\"flag\"]",
       "HIGH\n", "blood panel flags high glucose")
expect("import labtest\nlet a <- labtest.Analyzer.new()\n"
       "a.measure(\"glucose\", 90)\nprint a.results[0][\"flag\"]",
       "normal\n", "blood panel normal in range")
expect("import genomics\nlet g <- genomics.Sequencer.new(\"ATGTGA\")\n"
       "print g.transcribe()",
       "AUGUGA\n", "DNA transcribes to RNA")
expect("import genomics\nlet g <- genomics.Sequencer.new(\"ATGGCCTGA\")\n"
       "print g.translate()",
       "MA\n", "RNA translates and stops at stop codon")
expect("import genomics\nlet g <- genomics.Sequencer.new(\"GGCCGGCC\")\n"
       "print round(g.gc_content()*100, 0)",
       "100.0\n", "GC content")
expect("import basal_ganglia\nlet b <- basal_ganglia.Gate.new(0.8)\n"
       "b.input(\"CT\", 2)\nb.input(\"MRI\", 0.2)\nprint b.select()[0]",
       "CT\n", "basal ganglia selects the most salient")
expect("import ct\nlet s <- ct.body_slice(40, \"thorax\")\n"
       "print s.get(20, 20) >= 0",
       "true\n", "CT body slice phantom builds")
expect("let im <- image(8,8,\"RGB\",0)\nim.set_rgb(1,1,200,100,50)\n"
       "let u <- im.data_uri()\nprint u[0],u[1],u[2],u[3]",
       "d a t a\n", "image data URI for HTML embedding")

# --- GUI toolkit & text rendering ------------------------------------------

expect("import gui\nprint gui.h1(\"Hi\")", "<h1>Hi</h1>\n", "gui element builder")
expect("import gui\nprint gui.button(\"b\", \"Go\", \"f()\")",
       "<button id=\"b\" onclick=\"f()\">Go</button>\n", "gui button")
expect("import gui\n"
       "let a <- gui.App.new(\"T\")\na.add(gui.h1(\"X\"))\n"
       "let h <- a.render()\nprint contains(h, \"<!DOCTYPE html>\"), contains(h, \"<h1>X</h1>\")",
       "true true\n", "gui App renders a document")
expect("import gui\n"
       "let a <- gui.App.new(\"T\")\na.save(\"/tmp/_g.html\")\n"
       "print file_exists(\"/tmp/_g.html\")\ndelete_file(\"/tmp/_g.html\")",
       "true\n", "gui App saves an HTML file")
expect("let im <- image(60, 12, \"L\", 0)\n"
       "text_draw(im, 1, 2, \"AB\", 255, 1)\nprint im.get(3, 2) > 0",
       "true\n", "bitmap text draws pixels")
expect("print text_width(\"ABCD\", 2)", "48\n", "text width measurement")

# --- errors ----------------------------------------------------------------

expect_error("print undefined_var", BadaError, "undefined name")
expect_error("print 1 + \"a\"", BadaError, "type error on bad +")
expect_error("let a <- [1]\nprint a[5]", BadaError, "index out of range")

# --- summary ---------------------------------------------------------------

print(f"\n{PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
