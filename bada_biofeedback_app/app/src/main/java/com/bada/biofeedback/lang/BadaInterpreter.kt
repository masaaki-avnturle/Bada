package com.bada.biofeedback.lang

/**
 * BadaInterpreter — a tiny interpreter for the Bada preset language.
 *
 * Grammar (line oriented):
 *
 *   // comment
 *   preset "id" {
 *       label     = "リスパダール"
 *       feeling   = "気持ちが安静に"
 *       region    = limbic
 *       base_hz   = 96.0
 *       beat_hz   = 7.5
 *       waveform  = sine
 *       warmth    = 0.7
 *       color     = "#7ec8e3"
 *       narration = "胸と脳がゆっくりほどけていきます。"
 *   }
 *
 * Multiple presets per file are allowed. Unknown keys are ignored so the
 * language can grow without breaking older files.
 */
object BadaInterpreter {

    fun parse(source: String): List<BadaPreset> {
        val presets = mutableListOf<BadaPreset>()
        val lines = source.lines()
        var i = 0
        while (i < lines.size) {
            val line = stripComment(lines[i]).trim()
            val header = PRESET_HEADER.matchEntire(line)
            if (header != null) {
                val id = header.groupValues[1]
                val (preset, next) = parseBody(id, lines, i + 1)
                presets.add(preset)
                i = next
            } else {
                i++
            }
        }
        return presets
    }

    private fun parseBody(id: String, lines: List<String>, start: Int): Pair<BadaPreset, Int> {
        val kv = HashMap<String, String>()
        var i = start
        while (i < lines.size) {
            val raw = stripComment(lines[i]).trim()
            if (raw == "}") { i++; break }
            val m = ASSIGN.matchEntire(raw)
            if (m != null) {
                kv[m.groupValues[1].lowercase()] = unquote(m.groupValues[2].trim())
            }
            i++
        }
        val preset = BadaPreset(
            id = id,
            label = kv["label"] ?: id,
            feeling = kv["feeling"] ?: "",
            region = kv["region"] ?: "limbic",
            baseHz = kv["base_hz"]?.toDoubleOrNull() ?: 100.0,
            beatHz = kv["beat_hz"]?.toDoubleOrNull() ?: 7.0,
            waveform = kv["waveform"] ?: "sine",
            warmth = (kv["warmth"]?.toDoubleOrNull() ?: 0.6).coerceIn(0.0, 1.0),
            colorHex = kv["color"] ?: "#7ec8e3",
            narration = kv["narration"] ?: ""
        )
        return preset to i
    }

    private fun stripComment(s: String): String {
        val idx = s.indexOf("//")
        return if (idx >= 0) s.substring(0, idx) else s
    }

    private fun unquote(s: String): String =
        if (s.length >= 2 && s.startsWith("\"") && s.endsWith("\"")) s.substring(1, s.length - 1) else s

    private val PRESET_HEADER = Regex("""preset\s+"([^"]+)"\s*\{""")
    private val ASSIGN = Regex("""([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)""")
}
