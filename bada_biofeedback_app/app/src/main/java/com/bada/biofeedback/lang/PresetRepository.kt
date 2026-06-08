package com.bada.biofeedback.lang

import android.content.Context

/** Loads and caches all .bada presets bundled in assets/presets/. */
object PresetRepository {
    private var cache: List<BadaPreset>? = null

    fun load(context: Context): List<BadaPreset> {
        cache?.let { return it }
        val assets = context.assets
        val files = try {
            assets.list("presets")?.filter { it.endsWith(".bada") } ?: emptyList()
        } catch (_: Exception) { emptyList() }

        val all = mutableListOf<BadaPreset>()
        for (name in files) {
            val text = assets.open("presets/$name").bufferedReader().use { it.readText() }
            all += BadaInterpreter.parse(text)
        }
        cache = all
        return all
    }
}
