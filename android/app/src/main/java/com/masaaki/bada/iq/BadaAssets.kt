package com.masaaki.bada.iq

import android.content.Context

/** Loads the bundled Bada-language engine (special.bada + iq.bada) into the VM. */
object BadaAssets {
    fun ensureLoaded(context: Context) {
        if (IqEngine.isVmReady()) return
        val special = context.assets.open("special.bada").bufferedReader().use { it.readText() }
        val iq = context.assets.open("iq.bada").bufferedReader().use { it.readText() }
        IqEngine.initVm(special, iq)
    }
}
