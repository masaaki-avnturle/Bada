package io.bada.codefix

import kotlin.math.abs

/**
 * CodeFix — source-code error correction as the integrable system of a complex
 * rotational body ("the spinning-top / koma geometry of special relativity").
 *
 * Every source file is a rotational body; its opening/closing delimiters
 * ( ) [ ] { }, quotes, and Ruby def…end are angular markers on the spin orbit.
 * A valid file is one whose orbit *closes* (the integrable closed-orbit
 * condition ∮ e^{-□} d□ = π e). The signed delimiter balance is the conserved
 * quantity of the spin; a syntax error is the top falling off its closed orbit,
 * and correction restores the conserved balance so the orbit closes again.
 *
 * Faithful Kotlin port of bada_ruby/lib/bada/code_fix.rb.
 */
object CodeFixEngine {

    enum class Lang { RUBY, PYTHON, JAVASCRIPT, C, GENERIC }

    private val PAIRS = mapOf('(' to ')', '[' to ']', '{' to '}')
    private val OPENERS = PAIRS.keys
    private val CLOSERS = PAIRS.values.toSet()

    private data class Rules(
        val line: List<String>,
        val block: Pair<String, String>?,
        val quotes: Set<Char>,
        val keywordBlocks: Boolean
    )

    private val RULES = mapOf(
        Lang.RUBY to Rules(listOf("#"), null, setOf('"', '\''), true),
        Lang.PYTHON to Rules(listOf("#"), null, setOf('"', '\''), false),
        Lang.JAVASCRIPT to Rules(listOf("//"), "/*" to "*/", setOf('"', '\'', '`'), false),
        Lang.C to Rules(listOf("//"), "/*" to "*/", setOf('"', '\''), false),
        Lang.GENERIC to Rules(listOf("#", "//"), "/*" to "*/", setOf('"', '\''), false)
    )

    private val EXT = mapOf(
        "rb" to Lang.RUBY, "ru" to Lang.RUBY, "gemspec" to Lang.RUBY, "rake" to Lang.RUBY,
        "py" to Lang.PYTHON, "pyw" to Lang.PYTHON,
        "js" to Lang.JAVASCRIPT, "mjs" to Lang.JAVASCRIPT, "jsx" to Lang.JAVASCRIPT,
        "ts" to Lang.JAVASCRIPT, "tsx" to Lang.JAVASCRIPT,
        "c" to Lang.C, "h" to Lang.C, "cpp" to Lang.C, "cc" to Lang.C, "hpp" to Lang.C,
        "java" to Lang.C, "go" to Lang.C, "rs" to Lang.C, "cs" to Lang.C
    )

    private val RUBY_OPENERS = listOf("def", "class", "module", "do", "begin", "case")
    private val RUBY_LEADING = setOf("if", "unless", "while", "until", "for")

    data class Issue(val line: Int, val kind: String, val severity: String, val message: String)

    data class FixResult(
        val name: String,
        val language: Lang,
        val ok: Boolean,
        val issues: List<Issue>,
        val original: String,
        val fixed: String,
        val changed: Boolean,
        val xiBefore: Double,
        val xiAfter: Double,
        val confidence: Double
    ) {
        fun summary(): String {
            val head = if (ok) "✅ orbit closed (no errors)"
            else "🛠 ${issues.size} correction(s)"
            return "$name [${language.name.lowercase()}] — $head, Ξ-confidence ${"%.3f".format(confidence)}"
        }
    }

    // ---- language detection ---------------------------------------------

    fun detectLanguage(code: String, name: String? = null): Lang {
        if (name != null) {
            val base = name.substringAfterLast('/')
            val ext = if (base.contains('.')) base.substringAfterLast('.').lowercase() else base.lowercase()
            EXT[ext]?.let { return it }
        }
        if (Regex("^\\s*(def|class|module|require|puts)\\b", RegexOption.MULTILINE).containsMatchIn(code) &&
            code.contains("end")
        ) return Lang.RUBY
        if (Regex("^\\s*(def |class |import |print\\()", RegexOption.MULTILINE).containsMatchIn(code) &&
            code.contains(":")
        ) return Lang.PYTHON
        if (Regex("\\b(function|const|let|var|=>)\\b").containsMatchIn(code)) return Lang.JAVASCRIPT
        if (Regex("[;{}]\\s*$", RegexOption.MULTILINE).containsMatchIn(code) &&
            Regex("\\b(int|void|char|double|include)\\b").containsMatchIn(code)
        ) return Lang.C
        return Lang.GENERIC
    }

    // ---- edits -----------------------------------------------------------

    private sealed class Edit {
        abstract val pos: Int
        data class Insert(override val pos: Int, val str: String) : Edit()
        data class Delete(override val pos: Int, val len: Int) : Edit()
    }

    private data class Scan(val edits: List<Edit>, val issues: List<Issue>, val cleaned: String)

    // ---- the scanner -----------------------------------------------------

    private fun scan(code: String, lang: Lang): Scan {
        val rules = RULES[lang] ?: RULES[Lang.GENERIC]!!
        val quotes = rules.quotes
        val lineTokens = rules.line
        val block = rules.block

        val stack = ArrayDeque<Triple<Char, Int, Int>>() // char, index, line
        val issues = ArrayList<Issue>()
        val edits = ArrayList<Edit>()
        val cleaned = code.toCharArray()
        val len = code.length
        var i = 0
        var line = 1

        fun blank(from: Int, to: Int) {
            var k = from
            while (k < to && k < len) {
                if (cleaned[k] != '\n') cleaned[k] = ' '
                k++
            }
        }

        fun countNewlines(from: Int, to: Int): Int {
            var c = 0
            var k = from
            while (k < to && k < len) { if (code[k] == '\n') c++; k++ }
            return c
        }

        while (i < len) {
            val c = code[i]
            if (c == '\n') { line++; i++; continue }

            // block comment
            if (block != null && code.startsWith(block.first, i)) {
                val closeAt = code.indexOf(block.second, i + block.first.length)
                val stop = if (closeAt >= 0) closeAt + block.second.length else len
                line += countNewlines(i, stop)
                blank(i, stop)
                i = stop
                continue
            }

            // line comment
            if (lineTokens.any { code.startsWith(it, i) }) {
                val nl = code.indexOf('\n', i).let { if (it < 0) len else it }
                blank(i, nl)
                i = nl
                continue
            }

            // string literal
            if (quotes.contains(c)) {
                val q = c
                var j = i + 1
                var terminated = false
                while (j < len) {
                    val cj = code[j]
                    if (cj == '\n' && q != '`') break
                    if (cj == '\\') { j += 2; continue }
                    if (cj == q) { terminated = true; break }
                    j++
                }
                if (terminated) {
                    line += countNewlines(i, j + 1)
                    blank(i, j + 1)
                    i = j + 1
                } else {
                    val nl = code.indexOf('\n', i).let { if (it < 0) len else it }
                    val what = if (q == '`') "template" else "string"
                    issues.add(
                        Issue(line, "string", "error",
                            "unterminated $what literal — closing $q inserted")
                    )
                    edits.add(Edit.Insert(nl, q.toString()))
                    blank(i, nl)
                    i = nl
                }
                continue
            }

            // brackets — angular markers of the spin orbit
            if (OPENERS.contains(c)) {
                stack.addLast(Triple(c, i, line))
            } else if (CLOSERS.contains(c)) {
                if (stack.isEmpty() || PAIRS[stack.last().first] != c) {
                    issues.add(
                        Issue(line, "bracket", "error",
                            "stray closing '$c' with no matching opener — removed")
                    )
                    edits.add(Edit.Delete(i, 1))
                } else {
                    stack.removeLast()
                }
            }
            i++
        }

        // Openers that never returned. Inline ( ) and [ ] re-close at the end
        // of their opening line (the common typo); block { } close at EOF.
        if (stack.isNotEmpty()) {
            val braceTail = StringBuilder()
            for (t in stack.reversed()) {
                val (oc, idx, ln) = t
                issues.add(
                    Issue(ln, "bracket", "error",
                        "unclosed '$oc' opened here — '${PAIRS[oc]}' inserted")
                )
                if (oc == '{') {
                    braceTail.append(PAIRS[oc])
                } else {
                    val nl = code.indexOf('\n', idx).let { if (it < 0) len else it }
                    edits.add(Edit.Insert(nl, PAIRS[oc].toString()))
                }
            }
            if (braceTail.isNotEmpty()) {
                val pad = if (code.endsWith("\n")) "" else "\n"
                edits.add(Edit.Insert(len, pad + braceTail + "\n"))
            }
        }

        return Scan(edits, issues, String(cleaned))
    }

    // ---- Ruby block-keyword balance -------------------------------------

    private data class KeywordBalance(val deficit: Int, val issues: List<Issue>)

    private fun rubyKeywordBalance(cleaned: String): KeywordBalance {
        var depth = 0
        val issues = ArrayList<Issue>()
        val openLines = ArrayList<Int>()
        var ln = 0
        for (raw in cleaned.split("\n")) {
            ln++
            val code = raw.replace(Regex("#.*$"), "")
            val stripped = code.trim()
            if (stripped.isEmpty()) continue

            var opens = 0
            val first = Regex("^(\\w+)").find(stripped)?.groupValues?.get(1)
            if (first != null && RUBY_LEADING.contains(first)) opens++
            for (w in RUBY_OPENERS) opens += Regex("\\b$w\\b").findAll(code).count()
            opens += Regex("\\bdo\\b(\\s*\\|[^|]*\\|)?").findAll(code).count()
            val closes = Regex("\\bend\\b").findAll(code).count()

            val net = opens - closes
            depth += net
            if (net > 0) openLines.add(ln)
        }

        if (depth > 0) {
            repeat(depth) {
                issues.add(
                    Issue(openLines.lastOrNull() ?: 0, "keyword", "error",
                        "unbalanced Ruby block — missing `end` appended")
                )
            }
        } else if (depth < 0) {
            repeat(-depth) {
                issues.add(
                    Issue(0, "keyword", "warning",
                        "extra `end` detected — remove it manually (auto-removal is unsafe)")
                )
            }
        }
        return KeywordBalance(depth, issues)
    }

    // ---- apply edits -----------------------------------------------------

    private fun applyEdits(code: String, edits: List<Edit>): String {
        val out = StringBuilder(code)
        for (e in edits.sortedByDescending { it.pos }) {
            when (e) {
                is Edit.Insert -> out.insert(e.pos, e.str)
                is Edit.Delete -> out.delete(e.pos, e.pos + e.len)
            }
        }
        return out.toString()
    }

    // ---- full single-source fix -----------------------------------------

    fun fix(code: String, name: String = "source", language: Lang? = null): FixResult {
        val lang = language ?: detectLanguage(code, name)
        val s = scan(code, lang)
        val issues = ArrayList(s.issues)
        val edits = ArrayList(s.edits)

        if (RULES[lang]?.keywordBlocks == true) {
            val kb = rubyKeywordBalance(s.cleaned)
            issues.addAll(kb.issues)
            if (kb.deficit > 0) {
                val pad = if (code.endsWith("\n")) "" else "\n"
                edits.add(Edit.Insert(code.length, pad + List(kb.deficit) { "end" }.joinToString("\n") + "\n"))
            }
        }

        val fixed = applyEdits(code, edits)
        val changed = fixed != code

        val before = Manifold.invariant(code)
        val after = Manifold.invariant(fixed)
        val denom = abs(before) + abs(after) + 1e-9
        val confidence = if (before.isFinite() && after.isFinite())
            1.0 - (abs(before - after) / denom).coerceIn(0.0, 1.0)
        else 0.0

        val sorted = issues.sortedWith(compareBy({ it.line }, { it.kind }))
        return FixResult(name, lang, issues.isEmpty(), sorted, code, fixed, changed, before, after, confidence)
    }

    // =====================================================================
    // Repository — the submission board (複数投稿). Post many sources, correct
    // them all, and produce a batch report.
    // =====================================================================
    class Repository {
        data class Submission(
            val id: Int, val name: String, val language: Lang,
            val source: String, val result: FixResult
        )

        private val _submissions = ArrayList<Submission>()
        val submissions: List<Submission> get() = _submissions

        fun submit(source: String, name: String? = null, language: Lang? = null): Submission {
            val id = _submissions.size + 1
            val nm = name ?: "submission_$id"
            val result = fix(source, nm, language)
            val sub = Submission(id, nm, result.language, source, result)
            _submissions.add(sub)
            return sub
        }

        fun submitMany(items: List<Pair<String, String>>) =
            items.map { (name, source) -> submit(source, name) }

        fun totalIssues(): Int = _submissions.sumOf { it.result.issues.size }
        fun cleanCount(): Int = _submissions.count { it.result.ok }

        fun report(): String {
            val b = StringBuilder()
            b.appendLine("╔═ Bada CodeFix — 複素回転体・特殊相対性の可積分コマ幾何による多重投稿修正")
            b.appendLine("║  submissions: ${_submissions.size}   clean: ${cleanCount()}   corrections: ${totalIssues()}")
            b.appendLine("╚" + "═".repeat(56))
            for (s in _submissions) {
                val r = s.result
                b.appendLine()
                b.appendLine("▸ #${s.id} ${r.summary()}")
                if (r.issues.isEmpty()) {
                    b.appendLine("    (orbit already closed — conserved balance intact)")
                } else {
                    for (iss in r.issues.take(12)) {
                        val loc = if (iss.line > 0) "L${iss.line}" else "—"
                        val mark = if (iss.severity == "error") "✗" else "!"
                        b.appendLine("    $mark $loc [${iss.kind}] ${iss.message}")
                    }
                    if (r.issues.size > 12) b.appendLine("    … ${r.issues.size - 12} more")
                }
                b.appendLine(
                    "    Ξ before %.6f → after %.6f  (conserved %s)".format(
                        r.xiBefore, r.xiAfter,
                        if (abs(r.xiBefore - r.xiAfter) < 1e-6) "yes" else "no"
                    )
                )
            }
            return b.toString()
        }
    }
}
