package com.yamaguchi.sleep

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader
import android.util.AttributeSet
import android.view.View
import kotlin.math.min

/**
 * Renders a slow breathing orb whose radius follows [level] (0..1), taken from
 * the quantum wave function. [glow] (0..1) tints it. Purely visual.
 */
class SleepView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyle: Int = 0
) : View(context, attrs, defStyle) {

    private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE; strokeWidth = 3f; color = Color.parseColor("#3348606A")
    }

    private var level = 0.5f
    private var glow = 0.5f
    var dim = 1f   // 1 = full, fades to 0 at session end

    fun update(level: Float, glow: Float) {
        this.level = level.coerceIn(0f, 1f)
        this.glow = glow.coerceIn(0f, 1f)
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val cx = width / 2f
        val cy = height / 2f
        val maxR = min(width, height) / 2f * 0.9f
        val minR = maxR * 0.28f
        val r = minR + (maxR - minR) * level

        // outer guide ring at full-inhale size
        canvas.drawCircle(cx, cy, maxR, ring)

        // colour drifts between cool teal and soft indigo via glow, dimmed over time
        val teal = intArrayOf(0x56, 0xC8, 0xD0)
        val indigo = intArrayOf(0x8A, 0x7A, 0xD0)
        val rr = ((teal[0] + (indigo[0] - teal[0]) * glow) * dim).toInt().coerceIn(0, 255)
        val gg = ((teal[1] + (indigo[1] - teal[1]) * glow) * dim).toInt().coerceIn(0, 255)
        val bb = ((teal[2] + (indigo[2] - teal[2]) * glow) * dim).toInt().coerceIn(0, 255)
        val core = Color.argb((235 * dim).toInt().coerceIn(0, 255), rr, gg, bb)
        val edge = Color.argb(0, rr, gg, bb)

        fill.shader = RadialGradient(cx, cy, r, core, edge, Shader.TileMode.CLAMP)
        canvas.drawCircle(cx, cy, r, fill)
        fill.shader = null
    }
}
