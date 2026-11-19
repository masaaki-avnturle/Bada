package com.yamaguchi.sleep

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import kotlin.math.PI

/**
 * BadaSleep — a wind-down / sleep-onset guide.
 *
 * A genuine quantum state-vector simulator ([QuantumSim]) is time-evolved; the
 * breathing orb and pace are read from its wave function |ψ|². The pace starts
 * near your (optional, tapped) pulse and slows toward ~4 breaths/min to help you
 * drift off. Relaxation aid only — not a medical device. "Quantum" here means a
 * classical simulation of a quantum system, used as a smooth signal generator.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var orb: SleepView
    private lateinit var breath: TextView
    private lateinit var status: TextView
    private lateinit var psi: TextView
    private lateinit var pulseBtn: Button
    private lateinit var minutesIn: EditText
    private lateinit var startBtn: Button
    private lateinit var stopBtn: Button

    private val handler = Handler(Looper.getMainLooper())
    private val fps = 30
    private val dtMs = 1000L / fps

    private val sim = QuantumSim(3)
    private var running = false

    private var elapsedMs = 0L
    private var totalMs = 12 * 60_000L
    private var tick = 0
    private var prevLevel = 0.5f

    // pace (breaths per minute)
    private var startBpm = 6.0
    private val endBpm = 4.0

    // manual "biofeedback": tapped pulse
    private val taps = ArrayList<Long>()
    private var pulseBpm = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        orb = findViewById(R.id.orb)
        breath = findViewById(R.id.breath)
        status = findViewById(R.id.status)
        psi = findViewById(R.id.psi)
        pulseBtn = findViewById(R.id.pulseBtn)
        minutesIn = findViewById(R.id.minutes)
        startBtn = findViewById(R.id.startBtn)
        stopBtn = findViewById(R.id.stopBtn)

        pulseBtn.setOnClickListener { onPulseTap() }
        startBtn.setOnClickListener { start() }
        stopBtn.setOnClickListener { stop("停止しました / stopped") }
    }

    override fun onPause() {
        super.onPause()
        if (running) stop("一時停止 / paused")
    }

    // --- manual pulse (tap along with your heartbeat) -------------------

    private fun onPulseTap() {
        val now = System.currentTimeMillis()
        if (taps.isNotEmpty() && now - taps.last() > 3000) taps.clear() // restart if idle
        taps.add(now)
        if (taps.size >= 4) {
            var sum = 0L
            for (i in 1 until taps.size) sum += taps[i] - taps[i - 1]
            val avg = sum.toDouble() / (taps.size - 1)
            if (avg > 250) pulseBpm = (60000.0 / avg).toInt().coerceIn(40, 160)
        }
        status.text = if (pulseBpm > 0)
            "脈拍 ≈ $pulseBpm bpm（タップ${taps.size}回）— 開始でこのペースから誘導"
        else
            "脈拍タップ中…（${taps.size}回）あと${(4 - taps.size).coerceAtLeast(0)}回"
    }

    private fun startBpmFromPulse(): Double = when {
        pulseBpm <= 0 -> 6.0
        pulseBpm < 65 -> 6.0
        pulseBpm < 80 -> 6.5
        pulseBpm < 95 -> 7.0
        else -> 7.5
    }

    // --- session --------------------------------------------------------

    private fun start() {
        if (running) return
        totalMs = ((minutesIn.text.toString().trim().toIntOrNull() ?: 12)
            .coerceIn(1, 120)) * 60_000L
        startBpm = startBpmFromPulse()

        sim.reset()
        sim.hadamard(0); sim.hadamard(1)      // seed a superposition
        sim.rz(2, 0.7)

        elapsedMs = 0L; tick = 0; prevLevel = 0.5f
        running = true
        orb.dim = 1f
        startBtn.isEnabled = false
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        loop()
    }

    private fun stop(msg: String) {
        running = false
        handler.removeCallbacksAndMessages(null)
        startBtn.isEnabled = true
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        breath.text = ""
        status.text = msg
    }

    private fun loop() {
        if (!running) return

        val progress = (elapsedMs.toDouble() / totalMs).coerceIn(0.0, 1.0)
        val bpm = startBpm + (endBpm - startBpm) * progress
        val periodS = 60.0 / bpm
        val dTheta = 2 * PI / (periodS * fps)   // phase added per tick

        // evolve the wave function
        sim.rx(0, dTheta)
        sim.rz(1, dTheta * 0.6); sim.rx(1, dTheta * 0.3)
        sim.rx(2, dTheta * 0.15)
        if (tick % 24 == 0) { sim.cz(0, 1); sim.cz(1, 2) }
        if (tick % 90 == 0) sim.renormalize()

        val level = sim.probOne(0).toFloat()        // breathing amplitude 0..1
        val glow = sim.probOne(2).toFloat()
        orb.update(level, glow)

        // breath phase label from the wave function's slope / height
        val slope = level - prevLevel
        breath.text = when {
            level > 0.92f -> "止める / hold"
            slope >= 0f -> "吸う / inhale"
            else -> "吐く / exhale"
        }
        prevLevel = level

        val remain = ((totalMs - elapsedMs) / 1000).coerceAtLeast(0)
        status.text = "%.1f 呼吸/分 ・ 残り %d:%02d ・ 波動関数ペース".format(
            bpm, remain / 60, remain % 60
        )

        if (tick % 15 == 0) psi.text = formatPsi()

        // end of session: gentle fade then stop
        if (elapsedMs >= totalMs) {
            orb.dim = (orb.dim - 0.02f)
            if (orb.dim <= 0f) {
                orb.dim = 0f; orb.update(level, glow)
                stop("おやすみなさい / good night")
                return
            }
        }

        tick++
        elapsedMs += dtMs
        handler.postDelayed({ loop() }, dtMs)
    }

    /** top basis states of |ψ⟩ as a compact readout */
    private fun formatPsi(): String {
        val idx = (0 until sim.size).sortedByDescending { sim.magnitude(it) }.take(4)
        val sb = StringBuilder("|ψ⟩ ")
        for (i in idx) {
            val bits = buildString { for (q in sim.n - 1 downTo 0) append((i shr q) and 1) }
            val p = sim.magnitude(i) * sim.magnitude(i)
            sb.append("|").append(bits).append("⟩").append("%.2f ".format(p))
        }
        return sb.toString()
    }
}
