package com.bada.morpho.lang

/**
 * ProtocolInterpreter — tiny interpreter for the Bada protocol language.
 *
 *   protocol "cardio" {
 *       label          = "心筋細胞 分化"
 *       target         = "心筋細胞"
 *       field_strength = 0.6
 *       cusp_a         = -1.2
 *       cusp_b         = 0.0
 *       branch_prob    = 0.62
 *       feed           = 0.037
 *       kill           = 0.060
 *       drug           = "心筋再生候補 BX-1 (シミュレーション)"
 *       note           = "中胚葉経由の分岐を強める設定。"
 *   }
 */
object ProtocolInterpreter {

    fun parse(source: String): List<BadaProtocol> {
        val out = mutableListOf<BadaProtocol>()
        val lines = source.lines()
        var i = 0
        while (i < lines.size) {
            val line = strip(lines[i]).trim()
            val h = HEADER.matchEntire(line)
            if (h != null) {
                val (proto, next) = body(h.groupValues[1], lines, i + 1)
                out.add(proto); i = next
            } else i++
        }
        return out
    }

    private fun body(id: String, lines: List<String>, start: Int): Pair<BadaProtocol, Int> {
        val kv = HashMap<String, String>()
        var i = start
        while (i < lines.size) {
            val raw = strip(lines[i]).trim()
            if (raw == "}") { i++; break }
            ASSIGN.matchEntire(raw)?.let { kv[it.groupValues[1].lowercase()] = unquote(it.groupValues[2].trim()) }
            i++
        }
        val p = BadaProtocol(
            id = id,
            label = kv["label"] ?: id,
            target = kv["target"] ?: "心筋細胞",
            fieldStrength = kv["field_strength"]?.toDoubleOrNull() ?: 0.5,
            cuspA = kv["cusp_a"]?.toDoubleOrNull() ?: -1.0,
            cuspB = kv["cusp_b"]?.toDoubleOrNull() ?: 0.0,
            branchProb = (kv["branch_prob"]?.toDoubleOrNull() ?: 0.5).coerceIn(0.0, 1.0),
            feed = kv["feed"]?.toDoubleOrNull() ?: 0.037,
            kill = kv["kill"]?.toDoubleOrNull() ?: 0.060,
            drug = kv["drug"] ?: "候補薬 (シミュレーション)",
            note = kv["note"] ?: ""
        )
        return p to i
    }

    private fun strip(s: String) = s.indexOf("//").let { if (it >= 0) s.substring(0, it) else s }
    private fun unquote(s: String) =
        if (s.length >= 2 && s.startsWith("\"") && s.endsWith("\"")) s.substring(1, s.length - 1) else s

    private val HEADER = Regex("""protocol\s+"([^"]+)"\s*\{""")
    private val ASSIGN = Regex("""([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)""")
}
