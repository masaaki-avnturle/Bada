package com.bada.biofeedback.sensor

import android.media.Image
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import kotlin.math.max

/**
 * PpgHeartRate — a REAL (if rough) heart-rate estimator.
 *
 * Photoplethysmography: cover the rear camera + flash with a fingertip; the
 * average brightness pulses with your heartbeat. We track the mean luminance
 * of each frame, smooth it, detect peaks, and convert peak intervals to BPM.
 *
 * This is a consumer-grade demo, not a certified pulse oximeter. Accuracy
 * depends on lighting, finger pressure, and device. Do not use for diagnosis.
 */
class PpgHeartRate(
    private val onSample: (value: Float) -> Unit,
    private val onBpm: (bpm: Int) -> Unit
) : ImageAnalysis.Analyzer {

    private val intervals = ArrayDeque<Long>()
    private var smoothed = 0f
    private var prevSmoothed = 0f
    private var rising = false
    private var lastPeakNs = 0L
    private var baseline = 0f

    override fun analyze(image: ImageProxy) {
        try {
            val mean = meanLuma(image.image)
            // exponential smoothing
            smoothed = if (smoothed == 0f) mean else smoothed + 0.25f * (mean - smoothed)
            baseline = if (baseline == 0f) smoothed else baseline + 0.01f * (smoothed - baseline)
            val centered = smoothed - baseline
            onSample(centered)

            // peak detection on the smoothed signal
            val nowRising = smoothed > prevSmoothed
            if (rising && !nowRising) {
                // local maximum
                val now = System.nanoTime()
                if (lastPeakNs != 0L) {
                    val deltaMs = (now - lastPeakNs) / 1_000_000.0
                    if (deltaMs in 300.0..1500.0) { // 40..200 bpm plausible
                        intervals.addLast((deltaMs).toLong())
                        if (intervals.size > 6) intervals.removeFirst()
                        val avg = intervals.average()
                        if (avg > 0) onBpm((60000.0 / avg).toInt())
                    }
                }
                lastPeakNs = now
            }
            rising = nowRising
            prevSmoothed = smoothed
        } finally {
            image.close()
        }
    }

    private fun meanLuma(image: Image?): Float {
        if (image == null) return 0f
        // Y plane of YUV_420_888 = luminance; sample a sparse grid for speed.
        val y = image.planes[0]
        val buf = y.buffer
        val rowStride = y.rowStride
        val pixelStride = y.pixelStride
        val w = image.width
        val h = image.height
        var sum = 0L
        var count = 0
        val step = max(1, w / 64)
        var row = 0
        while (row < h) {
            var col = 0
            while (col < w) {
                val idx = row * rowStride + col * pixelStride
                if (idx < buf.limit()) {
                    sum += (buf.get(idx).toInt() and 0xFF)
                    count++
                }
                col += step
            }
            row += step
        }
        return if (count == 0) 0f else sum.toFloat() / count
    }
}
