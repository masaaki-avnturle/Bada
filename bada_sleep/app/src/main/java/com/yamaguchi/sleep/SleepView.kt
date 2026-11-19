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
 * Renders either a breathing orb (sleep mode) or a small moving dot (eye-relax
 * mode). [oddEye] draws it in two different colours left/right (heterochromia).
 * Purely visual.
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
    var dim = 1f
    var oddEye = false

    // eye-relax dot mode
    var dotMode = false
    private var dotX = 0.5f
    private var dotY = 0.5f

    // odd-eye hues
    private val hueL = intArrayOf(0x56, 0xC8, 0xD0)   // teal
    private val hueR = intArrayOf(0xD0, 0x8A, 0x5A)   // amber

    fun update(level: Float, glow: Float) {
        this.level = level.coerceIn(0f, 1f)
        this.glow = glow.coerceIn(0f, 1f)
        invalidate()
    }

    fun updateDot(x: Float, y: Float) {
        dotX = x.coerceIn(0f, 1f); dotY = y.coerceIn(0f, 1f)
        invalidate()
    }

    private fun blend(a: IntArray, b: IntArray, t: Float): IntArray =
        intArrayOf(
            (a[0] + (b[0] - a[0]) * t).toInt(),
            (a[1] + (b[1] - a[1]) * t).toInt(),
            (a[2] + (b[2] - a[2]) * t).toInt()
        )

    /** filled soft circle with a radial gradient of the given rgb, dimmed */
    private fun softCircle(canvas: Canvas, cx: Float, cy: Float, r: Float, rgb: IntArray) {
        val rr = (rgb[0] * dim).toInt().coerceIn(0, 255)
        val gg = (rgb[1] * dim).toInt().coerceIn(0, 255)
        val bb = (rgb[2] * dim).toInt().coerceIn(0, 255)
        val core = Color.argb((235 * dim).toInt().coerceIn(0, 255), rr, gg, bb)
        val edge = Color.argb(0, rr, gg, bb)
        fill.shader = RadialGradient(cx, cy, r, core, edge, Shader.TileMode.CLAMP)
        canvas.drawCircle(cx, cy, r, fill)
        fill.shader = null
    }

    private fun drawDualOrHalf(canvas: Canvas, cx: Float, cy: Float, r: Float, baseGlow: Float) {
        if (oddEye) {
            canvas.save(); canvas.clipRect(cx - r, cy - r, cx, cy + r)
            softCircle(canvas, cx, cy, r, hueL); canvas.restore()
            canvas.save(); canvas.clipRect(cx, cy - r, cx + r, cy + r)
            softCircle(canvas, cx, cy, r, hueR); canvas.restore()
        } else {
            softCircle(canvas, cx, cy, r, blend(hueL, hueR, baseGlow * 0.7f))
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat(); val h = height.toFloat()
        val cx = w / 2f; val cy = h / 2f

        if (dotMode) {
            val r = min(w, h) * 0.045f
            drawDualOrHalf(canvas, dotX * w, dotY * h, r, 0.5f)
            return
        }

        val maxR = min(w, h) / 2f * 0.9f
        val minR = maxR * 0.28f
        val r = minR + (maxR - minR) * level
        canvas.drawCircle(cx, cy, maxR, ring)
        drawDualOrHalf(canvas, cx, cy, r, glow)
    }
}
