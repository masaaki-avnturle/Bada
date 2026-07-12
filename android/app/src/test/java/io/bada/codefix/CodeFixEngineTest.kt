package io.bada.codefix

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Mirrors bada_ruby/test/test_code_fix.rb (balance-level assertions). */
class CodeFixEngineTest {

    @Test
    fun cleanRubyHasNoIssues() {
        val r = CodeFixEngine.fix("def ok(x)\n  x * 2\nend\n", "ok.rb", CodeFixEngine.Lang.RUBY)
        assertTrue(r.ok)
        assertTrue(r.issues.isEmpty())
        assertFalse(r.changed)
    }

    @Test
    fun unclosedParenClosedOnItsLine() {
        val r = CodeFixEngine.fix("def greet(name\n  name\nend\n", "g.rb", CodeFixEngine.Lang.RUBY)
        assertFalse(r.ok)
        assertTrue(r.fixed.contains("greet(name)"))
    }

    @Test
    fun unterminatedStringTerminated() {
        val r = CodeFixEngine.fix("puts \"hello\n", "s.rb", CodeFixEngine.Lang.RUBY)
        assertTrue(r.issues.any { it.kind == "string" })
    }

    @Test
    fun missingRubyEndAppended() {
        val r = CodeFixEngine.fix("def a\n  1\n", "e.rb", CodeFixEngine.Lang.RUBY)
        assertTrue(r.issues.any { it.kind == "keyword" })
        assertTrue(r.fixed.trimEnd().endsWith("end"))
    }

    @Test
    fun strayCloserRemoved() {
        val r = CodeFixEngine.fix("x = (1 + 2))\n", "p.rb", CodeFixEngine.Lang.RUBY)
        assertTrue(r.issues.any { it.message.contains("stray") })
        assertEquals("x = (1 + 2)\n", r.fixed)
    }

    @Test
    fun endInsideStringNotCounted() {
        val r = CodeFixEngine.fix("def a\n  puts \"the end\"\nend\n", "q.rb", CodeFixEngine.Lang.RUBY)
        assertTrue(r.ok)
    }

    @Test
    fun blockBraceLanguage() {
        val r = CodeFixEngine.fix(
            "function f(x) {\n  return [x, x * 2\n}\n", "f.js", CodeFixEngine.Lang.JAVASCRIPT
        )
        assertFalse(r.ok)
        assertTrue(r.fixed.contains("[x, x * 2]"))
    }

    @Test
    fun languageDetectionFromName() {
        assertEquals(CodeFixEngine.Lang.PYTHON, CodeFixEngine.detectLanguage("print(1)", "a.py"))
        assertEquals(CodeFixEngine.Lang.RUBY, CodeFixEngine.detectLanguage("puts 1", "a.rb"))
    }

    @Test
    fun confidenceBoundedAndConserved() {
        val r = CodeFixEngine.fix("def greet(name\n  name\nend\n", "g.rb", CodeFixEngine.Lang.RUBY)
        assertTrue(r.confidence in 0.0..1.0)
        assertTrue("orbit-restoring fix conserves Xi", r.confidence > 0.9)
    }

    @Test
    fun repositoryAcceptsManySubmissions() {
        val repo = CodeFixEngine.Repository()
        repo.submit("def a\n  1\nend\n", "one.rb", CodeFixEngine.Lang.RUBY)
        repo.submit("def b(x\n  x\nend\n", "two.rb", CodeFixEngine.Lang.RUBY)
        repo.submit("print(1)\n", "three.py", CodeFixEngine.Lang.PYTHON)
        assertEquals(3, repo.submissions.size)
        assertEquals(2, repo.cleanCount())
        assertTrue(repo.totalIssues() >= 1)
        assertTrue(repo.report().isNotEmpty())
    }
}
