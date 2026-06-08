package com.bada.biofeedback.audio

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import com.bada.biofeedback.lang.BadaMath
import com.bada.biofeedback.lang.BadaPreset
import kotlin.concurrent.thread
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.sin

/**
 * Real-time soundscape synthesizer.
 *
 * Generates a soft carrier tone (preset.baseHz) whose amplitude breathes at
 * preset.beatHz, the whole session shaped by BadaMath.sessionEnvelope (the
 * gamma-manifold / entropy envelope). "warmth" blends in a one-pole low-pass
 * so higher warmth = rounder, softer tone.
 *
 * This produces relaxation audio only. It is not a medical intervention.
 */
class ToneSynth(private val sampleRate: Int = 44100) {

    @Volatile private var running = false
    private var track: AudioTrack? = null
    private var worker: Thread? = null

    fun start(preset: BadaPreset, sessionSeconds: Double = 180.0) {
        stop()
        running = true

        val minBuf = AudioTrack.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_OUT_STEREO,
            AudioFormat.ENCODING_PCM_FLOAT
        ).coerceAtLeast(4096)

        val at = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(sampleRate)
                    .setEncoding(AudioFormat.ENCODING_PCM_FLOAT)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                    .build()
            )
            .setBufferSizeInBytes(minBuf * 2)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
        track = at
        at.play()

        worker = thread(name = "BadaToneSynth") {
            val frames = 1024
            val buf = FloatArray(frames * 2)
            var phaseCarrier = 0.0
            var phaseBeatL = 0.0
            var phaseBeatR = 0.0
            var lpL = 0.0
            var lpR = 0.0

            val twoPi = 2.0 * PI
            // small binaural offset so left/right breathe slightly apart
            val beatL = preset.beatHz
            val beatR = preset.beatHz * 1.02
            // one-pole low-pass coefficient from warmth (higher warmth -> more smoothing)
            val alpha = (1.0 - preset.warmth * 0.85).coerceIn(0.08, 1.0)

            var sampleIndex = 0L
            while (running) {
                for (f in 0 until frames) {
                    val tSec = sampleIndex.toDouble() / sampleRate
                    val env = BadaMath.sessionEnvelope(tSec, sessionSeconds)

                    val carrier = oscillator(phaseCarrier, preset.waveform)
                    val ampL = 0.5 + 0.5 * sin(phaseBeatL)
                    val ampR = 0.5 + 0.5 * sin(phaseBeatR)

                    val rawL = carrier * ampL * env * 0.28
                    val rawR = carrier * ampR * env * 0.28

                    // warmth low-pass
                    lpL += alpha * (rawL - lpL)
                    lpR += alpha * (rawR - lpR)

                    buf[f * 2] = lpL.toFloat()
                    buf[f * 2 + 1] = lpR.toFloat()

                    phaseCarrier += twoPi * preset.baseHz / sampleRate
                    if (phaseCarrier > twoPi) phaseCarrier -= twoPi
                    phaseBeatL += twoPi * beatL / sampleRate
                    if (phaseBeatL > twoPi) phaseBeatL -= twoPi
                    phaseBeatR += twoPi * beatR / sampleRate
                    if (phaseBeatR > twoPi) phaseBeatR -= twoPi
                    sampleIndex++
                }
                at.write(buf, 0, buf.size, AudioTrack.WRITE_BLOCKING)
            }
        }
    }

    private fun oscillator(phase: Double, waveform: String): Double {
        val p = phase / (2.0 * PI) // 0..1
        return when (waveform) {
            "triangle" -> 2.0 * abs(2.0 * (p - Math.floor(p + 0.5))) - 1.0
            "soft" -> {
                // sine plus a touch of 2nd harmonic, gently rounded
                val s = sin(phase)
                0.85 * s + 0.15 * sin(2.0 * phase) * 0.5
            }
            else -> sin(phase)
        }
    }

    fun stop() {
        running = false
        worker?.let { try { it.join(500) } catch (_: InterruptedException) {} }
        worker = null
        track?.let {
            try { it.stop() } catch (_: IllegalStateException) {}
            it.release()
        }
        track = null
    }

    val isPlaying: Boolean get() = running
}
