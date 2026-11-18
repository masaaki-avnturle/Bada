package com.yamaguchi.bci

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.util.AttributeSet
import android.view.View
import kotlin.math.sin
import kotlin.random.Random

/**
 * A SIMULATED brainwave trace. It is decorative/demonstrative only and is NOT
 * connected to any sensor or device. It animates while [active] is true.
 */
class SignalView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyle: Int = 0
) : View(context, attrs, defStyle) {

    private val line = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#56C8D0")
        style = Paint.Style.STROKE
        strokeWidth = 4f
    }
    private val flat = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#394049")
        style = Paint.Style.STROKE
        strokeWidth = 3f
    }
    private val path = Path()
    private var phase = 0f

    var active: Boolean = false
        set(value) {
            field = value
            if (value) postInvalidateOnAnimation() else invalidate()
        }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        val mid = h / 2f

        if (!active) {
            canvas.drawLine(0f, mid, w, mid, flat)   // flat line when OFF
            return
        }

        // composite of a few sine bands + a little noise => "brainwave"-like
        path.reset()
        var x = 0f
        val step = 4f
        while (x <= w) {
            val t = x / w * 12f + phase
            val y = mid +
                (h * 0.16f) * sin(t) +
                (h * 0.08f) * sin(t * 2.7f + 1.3f) +
                (h * 0.05f) * sin(t * 5.1f) +
                (h * 0.03f) * (Random.nextFloat() - 0.5f)
            if (x == 0f) path.moveTo(x, y) else path.lineTo(x, y)
            x += step
        }
        canvas.drawPath(path, line)

        phase += 0.22f
        postInvalidateOnAnimation()   // keep animating
    }
}
