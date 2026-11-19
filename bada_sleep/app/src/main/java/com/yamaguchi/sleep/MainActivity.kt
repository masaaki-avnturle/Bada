package com.yamaguchi.sleep

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat
import androidx.core.content.ContextCompat
import kotlin.math.PI
import kotlin.math.sin

/**
 * BadaSleep — wind-down / sleep-onset guide driven by a quantum state-vector
 * simulator, plus:
 *   • 無を聴く  — a microphone "silence" meter (listen to how quiet it is around
 *                 you). It measures ambient loudness only; it does not record,
 *                 transcribe, identify sounds, or read thoughts.
 *   • オッドアイ — a two-colour (heterochromia) rendering of the orb/dot.
 *   • 目のリラックス — an eye-relaxation routine (follow a slow dot + 20-20-20
 *                 far-gazing). It rests the eyes; it does not correct vision.
 *
 * Relaxation aid only — not a medical device.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var orb: SleepView
    private lateinit var breath: TextView
    private lateinit var status: TextView
    private lateinit var psi: TextView
    private lateinit var quiet: TextView
    private lateinit var oddEye: SwitchCompat
    private lateinit var listen: SwitchCompat
    private lateinit var pulseBtn: Button
    private lateinit var minutesIn: EditText
    private lateinit var startBtn: Button
    private lateinit var stopBtn: Button
    private lateinit var eyeBtn: Button

    private val handler = Handler(Looper.getMainLooper())
    private val fps = 30
    private val dtMs = 1000L / fps

    private val sim = QuantumSim(3)

    private enum class Mode { SLEEP, EYES }
    private var mode = Mode.SLEEP
    private var running = false

    private var elapsedMs = 0L
    private var totalMs = 12 * 60_000L
    private var tick = 0
    private var prevLevel = 0.5f

    private var startBpm = 6.0
    private val endBpm = 4.0

    private val taps = ArrayList<Long>()
    private var pulseBpm = 0

    // ambient "listen to the silence"
    private var ambient: AmbientListener? = null
    @Volatile private var lastQuiet = 0.6f

    private val micPerm = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startListening()
        else { listen.isChecked = false; status.text = "マイク権限がないため「無を聴く」は使えません" }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        orb = findViewById(R.id.orb)
        breath = findViewById(R.id.breath)
        status = findViewById(R.id.status)
        psi = findViewById(R.id.psi)
        quiet = findViewById(R.id.quiet)
        oddEye = findViewById(R.id.oddEye)
        listen = findViewById(R.id.listen)
        pulseBtn = findViewById(R.id.pulseBtn)
        minutesIn = findViewById(R.id.minutes)
        startBtn = findViewById(R.id.startBtn)
        stopBtn = findViewById(R.id.stopBtn)
        eyeBtn = findViewById(R.id.eyeBtn)

        oddEye.setOnCheckedChangeListener { _, c -> orb.oddEye = c; orb.invalidate() }
        listen.setOnCheckedChangeListener { _, c ->
            if (c) {
                if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                    == PackageManager.PERMISSION_GRANTED) startListening()
                else micPerm.launch(Manifest.permission.RECORD_AUDIO)
            } else stopListening()
        }
        pulseBtn.setOnClickListener { onPulseTap() }
        startBtn.setOnClickListener { startSleep() }
        stopBtn.setOnClickListener { stop("停止しました / stopped") }
        eyeBtn.setOnClickListener {
            if (running && mode == Mode.EYES) stop("目のリラックス終了") else startEyes()
        }
    }

    override fun onPause() {
        super.onPause()
        if (running) stop("一時停止 / paused")
        if (listen.isChecked) { listen.isChecked = false } // also stops the listener
    }

    // --- ambient silence meter ------------------------------------------

    private fun startListening() {
        if (ambient == null) {
            ambient = AmbientListener { q -> runOnUiThread { onQuiet(q) } }
        }
        ambient?.start()
        quiet.text = "無を聴く: 計測中…"
    }

    private fun stopListening() {
        ambient?.stop()
        quiet.text = "無を聴く: OFF"
    }

    private fun onQuiet(q: Float) {
        lastQuiet = q
        val n = (q * 12).toInt().coerceIn(0, 12)
        quiet.text = "静けさ [" + "▇".repeat(n) + "·".repeat(12 - n) + "] %.0f%%".format(q * 100)
    }

    // --- manual pulse ---------------------------------------------------

    private fun onPulseTap() {
        val now = System.currentTimeMillis()
        if (taps.isNotEmpty() && now - taps.last() > 3000) taps.clear()
        taps.add(now)
        if (taps.size >= 4) {
            var sum = 0L
            for (i in 1 until taps.size) sum += taps[i] - taps[i - 1]
            val avg = sum.toDouble() / (taps.size - 1)
            if (avg > 250) pulseBpm = (60000.0 / avg).toInt().coerceIn(40, 160)
        }
        status.text = if (pulseBpm > 0)
            "脈拍 ≈ $pulseBpm bpm（タップ${taps.size}回）— 開始でこのペースから誘導"
        else "脈拍タップ中…（${taps.size}回）あと${(4 - taps.size).coerceAtLeast(0)}回"
    }

    private fun startBpmFromPulse(): Double = when {
        pulseBpm <= 0 -> 6.0
        pulseBpm < 65 -> 6.0
        pulseBpm < 80 -> 6.5
        pulseBpm < 95 -> 7.0
        else -> 7.5
    }

    // --- sessions -------------------------------------------------------

    private fun startSleep() {
        stopLoopOnly()
        totalMs = ((minutesIn.text.toString().trim().toIntOrNull() ?: 12)
            .coerceIn(1, 120)) * 60_000L
        startBpm = startBpmFromPulse()
        sim.reset(); sim.hadamard(0); sim.hadamard(1); sim.rz(2, 0.7)
        mode = Mode.SLEEP
        elapsedMs = 0L; tick = 0; prevLevel = 0.5f
        orb.dotMode = false; orb.dim = 1f
        beginRun()
    }

    private fun startEyes() {
        stopLoopOnly()
        sim.reset(); sim.hadamard(0)
        mode = Mode.EYES
        elapsedMs = 0L; tick = 0
        orb.dotMode = true; orb.dim = 1f
        beginRun()
        status.text = "目のリラックス: 点をゆっくり目で追ってください"
    }

    private fun beginRun() {
        running = true
        startBtn.isEnabled = mode != Mode.SLEEP
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        loop()
    }

    /** stop the animation loop without touching the listener or UI messages */
    private fun stopLoopOnly() {
        running = false
        handler.removeCallbacksAndMessages(null)
    }

    private fun stop(msg: String) {
        stopLoopOnly()
        startBtn.isEnabled = true
        orb.dotMode = false
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        breath.text = ""
        status.text = msg
    }

    private fun loop() {
        if (!running) return
        if (mode == Mode.SLEEP) stepSleep() else stepEyes()
        tick++
        elapsedMs += dtMs
        handler.postDelayed({ loop() }, dtMs)
    }

    private fun stepSleep() {
        val progress = (elapsedMs.toDouble() / totalMs).coerceIn(0.0, 1.0)
        val bpm = startBpm + (endBpm - startBpm) * progress
        val periodS = 60.0 / bpm
        val dTheta = 2 * PI / (periodS * fps)

        sim.rx(0, dTheta)
        sim.rz(1, dTheta * 0.6); sim.rx(1, dTheta * 0.3)
        sim.rx(2, dTheta * 0.15)
        if (tick % 24 == 0) { sim.cz(0, 1); sim.cz(1, 2) }
        if (tick % 90 == 0) sim.renormalize()

        val level = sim.probOne(0).toFloat()
        var glow = sim.probOne(2).toFloat()
        if (listen.isChecked) glow = glow * 0.5f + lastQuiet * 0.5f
        orb.update(level, glow)

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

        if (elapsedMs >= totalMs) {
            orb.dim -= 0.02f
            if (orb.dim <= 0f) { orb.dim = 0f; orb.update(level, glow); stop("おやすみなさい / good night") }
        }
    }

    private fun stepEyes() {
        val seg = (elapsedMs / 1000) % 60
        if (seg < 40) {
            val p = tick * 0.03
            val x = 0.5 + 0.42 * sin(p)
            val y = 0.5 + 0.16 * sin(p * 2 + 0.4)
            orb.updateDot(x.toFloat(), y.toFloat())
            breath.text = "点をゆっくり目で追う"
        } else {
            orb.updateDot(0.5f, 0.5f)
            breath.text = "遠くの一点を見る（20秒） 20-20-20"
        }
        val t = elapsedMs / 1000
        status.text = "目のリラックス ・ 経過 %d:%02d（停止で終了）".format(t / 60, t % 60)
        if (tick % 15 == 0) psi.text = formatPsi()
    }

    private fun formatPsi(): String {
        val idx = (0 until sim.size).sortedByDescending { sim.magnitude(it) }.take(4)
        val sb = StringBuilder("|ψ⟩ ")
        for (i in idx) {
            val bits = buildString { for (q in sim.n - 1 downTo 0) append((i shr q) and 1) }
            val pr = sim.magnitude(i) * sim.magnitude(i)
            sb.append("|").append(bits).append("⟩").append("%.2f ".format(pr))
        }
        return sb.toString()
    }
}
