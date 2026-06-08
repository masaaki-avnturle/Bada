package com.bada.biofeedback.lang

/**
 * A single biofeedback "mood" preset, declared in a .bada file.
 *
 * IMPORTANT: a preset represents a *relaxation soundscape and a target
 * body region to relax* — e.g. "リスパダール = 気持ちが安静に". It does NOT
 * reproduce, deliver, or substitute for any pharmaceutical effect.
 */
data class BadaPreset(
    val id: String,
    val label: String,        // display name (e.g. リスパダール)
    val feeling: String,      // intended relaxed feeling
    val region: String,       // target region key (see BodyRegion)
    val baseHz: Double,       // carrier tone frequency
    val beatHz: Double,       // amplitude-modulation / breathing rate
    val waveform: String,     // sine | triangle | soft
    val warmth: Double,       // 0..1 tone softness
    val colorHex: String,     // accent colour
    val narration: String     // short guidance text
)
