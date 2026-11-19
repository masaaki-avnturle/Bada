package com.yamaguchi.sleep

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlin.math.log10
import kotlin.math.sqrt

/**
 * "Listen to the silence." Reads the microphone and reports how QUIET the
 * surroundings are: quiet≈1.0 when near-silent, →0 when loud. It only measures
 * ambient loudness (RMS) for a calm meditation meter — it does not record,
 * transcribe, identify sounds, or read thoughts.
 */
class AmbientListener(private val onQuiet: (Float) -> Unit) {

    @Volatile private var running = false
    private var thread: Thread? = null

    fun start() {
        if (running) return
        running = true
        thread = Thread {
            val sr = 16000
            val ch = AudioFormat.CHANNEL_IN_MONO
            val fmt = AudioFormat.ENCODING_PCM_16BIT
            val minBuf = AudioRecord.getMinBufferSize(sr, ch, fmt)
            val bufSize = if (minBuf > 0) maxOf(minBuf, 2048) else 2048
            val rec = try {
                AudioRecord(MediaRecorder.AudioSource.MIC, sr, ch, fmt, bufSize)
            } catch (e: Exception) { null }
            if (rec == null || rec.state != AudioRecord.STATE_INITIALIZED) {
                running = false
                rec?.release()
                return@Thread
            }
            val buf = ShortArray(bufSize)
            var smooth = 0.6f
            try {
                rec.startRecording()
                while (running) {
                    val n = rec.read(buf, 0, buf.size)
                    if (n > 0) {
                        var sum = 0.0
                        for (i in 0 until n) { val v = buf[i].toDouble(); sum += v * v }
                        val rms = sqrt(sum / n)
                        val db = 20.0 * log10(rms + 1.0)          // ~0 (silent) .. ~90 (loud)
                        val quiet = (1.0 - db / 70.0).coerceIn(0.0, 1.0).toFloat()
                        smooth += (quiet - smooth) * 0.2f          // gentle smoothing
                        onQuiet(smooth)
                    }
                }
            } catch (e: Exception) {
                // ignore; just stop
            } finally {
                try { rec.stop() } catch (_: Exception) {}
                rec.release()
            }
        }.also { it.start() }
    }

    fun stop() {
        running = false
        thread = null
    }
}
