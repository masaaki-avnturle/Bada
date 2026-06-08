package com.bada.biofeedback.lang

/**
 * Target regions that a preset aims to relax ("ほっとする部位").
 * Coordinates are normalised (0..1) over a simple front-facing body
 * silhouette and used only to draw a soft glow — not anatomy-accurate.
 */
enum class BodyRegion(val key: String, val label: String, val nx: Float, val ny: Float) {
    BRAIN("brain", "脳", 0.5f, 0.10f),
    LIMBIC("limbic", "大脳辺縁系", 0.5f, 0.14f),
    BASAL_GANGLIA("basal_ganglia", "大脳基底核", 0.5f, 0.13f),
    CHEST("chest", "胸", 0.5f, 0.42f),
    HEART("heart", "心臓", 0.45f, 0.40f),
    WHOLE_BODY("whole_body", "全身", 0.5f, 0.55f);

    companion object {
        fun of(key: String): BodyRegion =
            entries.firstOrNull { it.key == key } ?: LIMBIC
    }
}
