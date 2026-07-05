package com.masaaki.bada.iq

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.floor
import kotlin.math.ln
import kotlin.math.pow
import kotlin.math.sqrt

// AST node: a list whose [0] is a tag string, e.g. listOf("num", 3.0).
private typealias Node = List<Any?>

/**
 * BadaVM — the Bada language VM, a faithful Kotlin port of bada_ruby's
 * Bada::Lang. It parses and executes the .bada engine libraries
 * (special.bada + iq.bada, shipped as Android assets) so the APK's IQ / thermal
 * mathematics runs on the Bada-language library itself, not on hand-written
 * Kotlin. Values are Double / String / List / Boolean.
 */
object BadaVM {

    class BadaError(msg: String) : RuntimeException(msg)

    // ── Builtins: the Bada standard primitives ────────────────────────────────
    fun defaultBuiltins(): Map<String, (List<Any?>) -> Any?> = mapOf(
        "gamma" to { a -> IqEngine.gamma(d(a[0])) },
        "erf" to { a -> IqEngine.erf(d(a[0])) },
        "ln" to { a -> ln(d(a[0])) },
        "exp" to { a -> exp(d(a[0])) },
        "sqrt" to { a -> sqrt(d(a[0])) },
        "abs" to { a -> abs(d(a[0])) },
        "pow" to { a -> d(a[0]).pow(d(a[1])) },
        "floor" to { a -> floor(d(a[0])) },
        "min" to { a -> minOf(d(a[0]), d(a[1])) },
        "max" to { a -> maxOf(d(a[0]), d(a[1])) },
        "pi" to { _ -> Math.PI },
        "inf" to { _ -> Double.POSITIVE_INFINITY },
        "len" to { a -> (a[0] as List<*>).size.toDouble() },
        "push" to { a -> (a[0] as List<*>) + listOf(a[1]) },
        "sort" to { a -> (a[0] as List<*>).map { d(it) }.sorted() },
        "sum" to { a -> (a[0] as List<*>).sumOf { d(it) } }
    )

    private fun d(v: Any?): Double = when (v) {
        is Double -> v
        is Int -> v.toDouble()
        is Boolean -> if (v) 1.0 else 0.0
        else -> throw BadaError("not a number: $v")
    }

    private class Fn(val params: List<String>, val body: List<Node>)

    class VM(private val builtins: Map<String, (List<Any?>) -> Any?> = defaultBuiltins()) {
        private val functions = HashMap<String, Fn>()

        fun functionNames(): Set<String> = functions.keys

        fun load(source: String): VM {
            val stmts = Parser(source).parseProgram()
            for (s in stmts) execStmt(s, HashMap())
            return this
        }

        fun call(name: String, args: List<Any?> = emptyList()): Any? {
            val fn = functions[name] ?: throw BadaError("no such Bada function: $name")
            return invoke(fn, args)
        }

        fun callNum(name: String, args: List<Any?> = emptyList()): Double = d(call(name, args))

        private class ReturnException(val value: Any?) : RuntimeException()

        private fun invoke(fn: Fn, args: List<Any?>): Any? {
            val env = HashMap<String, Any?>()
            fn.params.forEachIndexed { i, p -> env[p] = args.getOrNull(i) }
            return try {
                for (s in fn.body) execStmt(s, env)
                null
            } catch (r: ReturnException) {
                r.value
            }
        }

        @Suppress("UNCHECKED_CAST")
        private fun execStmt(node: Node, env: HashMap<String, Any?>) {
            when (node[0] as String) {
                "def" -> functions[node[1] as String] =
                    Fn(node[2] as List<String>, node[3] as List<Node>)
                "assign" -> env[node[1] as String] = evalExpr(node[2] as Node, env)
                "return" -> throw ReturnException(
                    if (node[1] == null) null else evalExpr(node[1] as Node, env)
                )
                "print" -> println(evalExpr(node[1] as Node, env))
                "if" -> if (truthy(evalExpr(node[1] as Node, env))) {
                    for (s in node[2] as List<Node>) execStmt(s, env)
                } else {
                    for (s in node[3] as List<Node>) execStmt(s, env)
                }
                "while" -> {
                    var guard = 0
                    while (truthy(evalExpr(node[1] as Node, env))) {
                        for (s in node[2] as List<Node>) execStmt(s, env)
                        if (++guard > 10_000_000) throw BadaError("while loop runaway")
                    }
                }
                "expr" -> evalExpr(node[1] as Node, env)
                else -> throw BadaError("unknown statement: ${node[0]}")
            }
        }

        @Suppress("UNCHECKED_CAST")
        private fun evalExpr(node: Node, env: HashMap<String, Any?>): Any? {
            return when (node[0] as String) {
                "num" -> node[1]
                "str" -> node[1]
                "arr" -> (node[1] as List<Node>).map { evalExpr(it, env) }
                "var" -> {
                    val name = node[1] as String
                    if (!env.containsKey(name)) throw BadaError("undefined variable: $name")
                    env[name]
                }
                "index" -> {
                    val base = evalExpr(node[1] as Node, env) as List<*>
                    base[d(evalExpr(node[2] as Node, env)).toInt()]
                }
                "unary" -> {
                    val v = evalExpr(node[2] as Node, env)
                    if (node[1] == "-") -d(v) else !truthy(v)
                }
                "binop" -> applyBinop(node[1] as String, node[2] as Node, node[3] as Node, env)
                "call" -> callFn(node[1] as String, (node[2] as List<Node>).map { evalExpr(it, env) })
                else -> throw BadaError("unknown expression: ${node[0]}")
            }
        }

        private fun applyBinop(op: String, an: Node, bn: Node, env: HashMap<String, Any?>): Any? {
            if (op == "&&") return if (truthy(evalExpr(an, env))) truthy(evalExpr(bn, env)) else false
            if (op == "||") return if (truthy(evalExpr(an, env))) true else truthy(evalExpr(bn, env))
            val a = evalExpr(an, env)
            val b = evalExpr(bn, env)
            return when (op) {
                "+" -> d(a) + d(b)
                "-" -> d(a) - d(b)
                "*" -> d(a) * d(b)
                "/" -> d(a) / d(b)
                "%" -> d(a).rem(d(b))
                "<" -> d(a) < d(b)
                ">" -> d(a) > d(b)
                "<=" -> d(a) <= d(b)
                ">=" -> d(a) >= d(b)
                "==" -> d(a) == d(b)
                "!=" -> d(a) != d(b)
                else -> throw BadaError("unknown operator: $op")
            }
        }

        private fun callFn(name: String, args: List<Any?>): Any? {
            functions[name]?.let { return invoke(it, args) }
            builtins[name]?.let { return it(args) }
            throw BadaError("call to undefined function: $name")
        }

        private fun truthy(v: Any?): Boolean = when (v) {
            is Boolean -> v
            is Double -> v != 0.0
            null -> false
            else -> true
        }
    }

    // ── Tokenizer ──────────────────────────────────────────────────────────────
    private data class Tok(val type: String, val value: Any?)

    private object Lexer {
        private val TWO = setOf("==", "!=", "<=", ">=", "&&", "||")
        private val ONE = setOf("+", "-", "*", "/", "%", "(", ")", "[", "]", ",", "<", ">", "=", "!")

        fun tokenize(line: String): List<Tok> {
            val toks = ArrayList<Tok>()
            var i = 0
            val n = line.length
            while (i < n) {
                val c = line[i]
                when {
                    c.isWhitespace() -> i++
                    c == '"' -> {
                        var j = i + 1
                        while (j < n && line[j] != '"') j++
                        toks.add(Tok("str", line.substring(i + 1, j)))
                        i = j + 1
                    }
                    c.isDigit() || (c == '.' && i + 1 < n && line[i + 1].isDigit()) -> {
                        var j = i
                        while (j < n && (line[j].isDigit() || line[j] == '.')) j++
                        toks.add(Tok("num", line.substring(i, j).toDouble()))
                        i = j
                    }
                    c.isLetter() || c == '_' -> {
                        var j = i
                        while (j < n && (line[j].isLetterOrDigit() || line[j] == '_')) j++
                        toks.add(Tok("id", line.substring(i, j)))
                        i = j
                    }
                    else -> {
                        val two = if (i + 1 < n) line.substring(i, i + 2) else ""
                        if (two in TWO) {
                            toks.add(Tok("op", two)); i += 2
                        } else if (c.toString() in ONE) {
                            toks.add(Tok("op", c.toString())); i++
                        } else {
                            throw BadaError("unexpected character '$c' in: $line")
                        }
                    }
                }
            }
            return toks
        }
    }

    // ── Parser ───────────────────────────────────────────────────────────────
    private class Parser(source: String) {
        private val lines: List<String> =
            source.lineSequence()
                .map { it.replace(Regex("#.*"), "").trimEnd() }
                .filter { it.trim().isNotEmpty() }
                .toList()
        private var pos = 0

        fun parseProgram(): List<Node> {
            val stmts = ArrayList<Node>()
            while (pos < lines.size) stmts.add(parseStmt())
            return stmts
        }

        private fun peekLine() = lines[pos]
        private fun nextLine() = lines[pos].also { pos++ }
        private fun firstWord(line: String) = line.trim().split(Regex("[\\s(]"), 2)[0]

        private fun parseBlock(terminators: Set<String>): List<Node> {
            val stmts = ArrayList<Node>()
            while (pos < lines.size && firstWord(peekLine()) !in terminators) stmts.add(parseStmt())
            return stmts
        }

        private fun parseStmt(): Node = when (firstWord(peekLine())) {
            "def" -> parseDef()
            "if" -> parseIf()
            "while" -> parseWhile()
            "return" -> parseReturn()
            "set" -> parseSet()
            "print" -> parsePrint()
            else -> parseBare()
        }

        private fun parseDef(): Node {
            val header = nextLine().trim()
            val m = Regex("^def\\s+([A-Za-z_]\\w*)\\s*\\((.*)\\)\\s*$").find(header)
                ?: throw BadaError("bad def: $header")
            val name = m.groupValues[1]
            val paramSrc = m.groupValues[2].trim()
            val params = if (paramSrc.isEmpty()) emptyList() else paramSrc.split(",").map { it.trim() }
            val body = parseBlock(setOf("end"))
            if (pos >= lines.size) throw BadaError("def $name missing end")
            nextLine()
            return listOf("def", name, params, body)
        }

        private fun parseIf(): Node {
            val cond = parseExprStr(nextLine().trim().removePrefix("if"))
            val thenB = parseBlock(setOf("else", "end"))
            var elseB: List<Node> = emptyList()
            if (pos < lines.size && firstWord(peekLine()) == "else") {
                nextLine()
                elseB = parseBlock(setOf("end"))
            }
            if (pos >= lines.size) throw BadaError("if missing end")
            nextLine()
            return listOf("if", cond, thenB, elseB)
        }

        private fun parseWhile(): Node {
            val cond = parseExprStr(nextLine().trim().removePrefix("while"))
            val body = parseBlock(setOf("end"))
            if (pos >= lines.size) throw BadaError("while missing end")
            nextLine()
            return listOf("while", cond, body)
        }

        private fun parseReturn(): Node {
            val src = nextLine().trim().removePrefix("return").trim()
            return listOf("return", if (src.isEmpty()) null else parseExprStr(src))
        }

        private fun parseSet(): Node {
            val src = nextLine().trim().removePrefix("set").trim()
            val idx = src.indexOf('=')
            return listOf("assign", src.substring(0, idx).trim(), parseExprStr(src.substring(idx + 1)))
        }

        private fun parsePrint(): Node =
            listOf("print", parseExprStr(nextLine().trim().removePrefix("print").trim()))

        private fun parseBare(): Node {
            val src = nextLine().trim()
            val m = Regex("^([A-Za-z_]\\w*)\\s*=(?!=)\\s*(.+)$").find(src)
            return if (m != null) {
                listOf("assign", m.groupValues[1], parseExprStr(m.groupValues[2]))
            } else {
                listOf("expr", parseExprStr(src))
            }
        }

        private fun parseExprStr(src: String): Node {
            val ep = ExprParser(Lexer.tokenize(src))
            val node = ep.parse()
            if (!ep.done()) throw BadaError("trailing tokens in: $src")
            return node
        }
    }

    // ── Expression parser (precedence climbing) ────────────────────────────────
    private class ExprParser(private val toks: List<Tok>) {
        private var i = 0
        fun parse(): Node = parseOr()
        fun done(): Boolean = i >= toks.size

        private fun peek(): Tok? = toks.getOrNull(i)
        private fun advance(): Tok = toks[i].also { i++ }
        private fun isOp(v: String): Boolean = peek()?.let { it.type == "op" && it.value == v } ?: false
        private fun eatOp(v: String) { if (!isOp(v)) throw BadaError("expected $v"); advance() }

        private fun parseOr(): Node {
            var node = parseAnd()
            while (isOp("||")) { advance(); node = listOf("binop", "||", node, parseAnd()) }
            return node
        }

        private fun parseAnd(): Node {
            var node = parseEquality()
            while (isOp("&&")) { advance(); node = listOf("binop", "&&", node, parseEquality()) }
            return node
        }

        private fun parseEquality(): Node {
            var node = parseCompare()
            while (isOp("==") || isOp("!=")) {
                val o = advance().value as String
                node = listOf("binop", o, node, parseCompare())
            }
            return node
        }

        private fun parseCompare(): Node {
            var node = parseAdd()
            while (isOp("<") || isOp(">") || isOp("<=") || isOp(">=")) {
                val o = advance().value as String
                node = listOf("binop", o, node, parseAdd())
            }
            return node
        }

        private fun parseAdd(): Node {
            var node = parseMul()
            while (isOp("+") || isOp("-")) {
                val o = advance().value as String
                node = listOf("binop", o, node, parseMul())
            }
            return node
        }

        private fun parseMul(): Node {
            var node = parseUnary()
            while (isOp("*") || isOp("/") || isOp("%")) {
                val o = advance().value as String
                node = listOf("binop", o, node, parseUnary())
            }
            return node
        }

        private fun parseUnary(): Node = when {
            isOp("-") -> { advance(); listOf("unary", "-", parseUnary()) }
            isOp("!") -> { advance(); listOf("unary", "!", parseUnary()) }
            else -> parsePostfix()
        }

        private fun parsePostfix(): Node {
            var node = parsePrimary()
            while (isOp("[")) {
                advance()
                val idx = parseOr()
                eatOp("]")
                node = listOf("index", node, idx)
            }
            return node
        }

        private fun parsePrimary(): Node {
            val t = peek() ?: throw BadaError("unexpected end of expression")
            return when {
                t.type == "num" -> { advance(); listOf("num", t.value) }
                t.type == "str" -> { advance(); listOf("str", t.value) }
                isOp("(") -> { advance(); val node = parseOr(); eatOp(")"); node }
                isOp("[") -> {
                    advance()
                    val elems = ArrayList<Node>()
                    if (!isOp("]")) {
                        elems.add(parseOr())
                        while (isOp(",")) { advance(); elems.add(parseOr()) }
                    }
                    eatOp("]")
                    listOf("arr", elems)
                }
                t.type == "id" -> {
                    val name = advance().value as String
                    if (isOp("(")) {
                        advance()
                        val args = ArrayList<Node>()
                        if (!isOp(")")) {
                            args.add(parseOr())
                            while (isOp(",")) { advance(); args.add(parseOr()) }
                        }
                        eatOp(")")
                        listOf("call", name, args)
                    } else when (name) {
                        "true" -> listOf("num", 1.0)
                        "false" -> listOf("num", 0.0)
                        else -> listOf("var", name)
                    }
                }
                else -> throw BadaError("unexpected token: $t")
            }
        }
    }
}
