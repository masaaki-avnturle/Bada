package com.bada.morpho.lang

import android.content.Context

object ProtocolRepository {
    private var cache: List<BadaProtocol>? = null

    fun load(context: Context): List<BadaProtocol> {
        cache?.let { return it }
        val assets = context.assets
        val files = try {
            assets.list("protocols")?.filter { it.endsWith(".bada") } ?: emptyList()
        } catch (_: Exception) { emptyList() }
        val all = mutableListOf<BadaProtocol>()
        for (name in files) {
            val text = assets.open("protocols/$name").bufferedReader().use { it.readText() }
            all += ProtocolInterpreter.parse(text)
        }
        cache = all
        return all
    }
}
