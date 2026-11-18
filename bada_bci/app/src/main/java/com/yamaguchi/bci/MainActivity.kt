package com.yamaguchi.bci

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * BadaBCI — an ON/OFF control panel for a brain-interface *session*.
 *
 * IMPORTANT / 重要:
 *   This is a SIMULATION and a concept implementation based on the Bada /
 *   Yamaguchi theory in this repository. It does NOT connect to, power, or
 *   switch any real device worn on or implanted in the brain. The waveform is
 *   a simulated trace, not a measurement. To drive real EEG hardware (e.g. a
 *   consumer headset), the ON/OFF would open/close a session through that
 *   device's own certified SDK — see the `connect()` / `disconnect()` seams
 *   below — which cannot be exercised without the real device.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var powerSwitch: SwitchCompat
    private lateinit var stateLabel: TextView
    private lateinit var status: TextView
    private lateinit var signal: SignalView
    private lateinit var log: TextView
    private lateinit var recordBtn: Button
    private lateinit var clearBtn: Button

    private val handler = Handler(Looper.getMainLooper())
    private val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US)

    private enum class State { OFF, CONNECTING, ON }
    private var state = State.OFF

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        powerSwitch = findViewById(R.id.powerSwitch)
        stateLabel = findViewById(R.id.stateLabel)
        status = findViewById(R.id.status)
        signal = findViewById(R.id.signal)
        log = findViewById(R.id.log)
        recordBtn = findViewById(R.id.recordBtn)
        clearBtn = findViewById(R.id.clearBtn)

        powerSwitch.setOnClickListener {
            // react to the user's toggle intent, not to programmatic changes
            if (powerSwitch.isChecked) switchOn() else switchOff()
        }
        recordBtn.setOnClickListener { saveLog() }
        clearBtn.setOnClickListener { log.text = ""; status.text = "記録を消去しました" }
    }

    override fun onPause() {
        super.onPause()
        if (state != State.OFF) switchOff()   // never leave a session "running" in the background
    }

    // --- ON/OFF state machine -------------------------------------------

    private fun switchOn() {
        if (state != State.OFF) return
        state = State.CONNECTING
        setUi(State.CONNECTING)
        append("[${now()}] スイッチ ON 要求 — 接続中…")
        connect()
        // simulate a short handshake, then the session becomes active
        handler.postDelayed({
            if (state != State.CONNECTING) return@postDelayed
            state = State.ON
            setUi(State.ON)
            append("[${now()}] セッション開始 (ON) — 模擬信号を表示")
        }, 1200)
    }

    private fun switchOff() {
        if (state == State.OFF) return
        state = State.OFF
        handler.removeCallbacksAndMessages(null)
        disconnect()
        setUi(State.OFF)
        append("[${now()}] スイッチ OFF — セッション停止")
    }

    private fun setUi(s: State) {
        when (s) {
            State.OFF -> {
                stateLabel.text = "OFF"
                stateLabel.setTextColor(0xFF888888.toInt())
                status.text = "スイッチOFF — セッション停止中 / session stopped"
                signal.active = false
                if (powerSwitch.isChecked) powerSwitch.isChecked = false
                powerSwitch.isEnabled = true
            }
            State.CONNECTING -> {
                stateLabel.text = "…"
                stateLabel.setTextColor(0xFFC8A44A.toInt())
                status.text = "接続中 / connecting…"
                signal.active = false
                powerSwitch.isEnabled = false
            }
            State.ON -> {
                stateLabel.text = "ON"
                stateLabel.setTextColor(0xFF56C8D0.toInt())
                status.text = "セッション作動中 (ON) — ※模擬信号 / simulated"
                signal.active = true
                if (!powerSwitch.isChecked) powerSwitch.isChecked = true
                powerSwitch.isEnabled = true
            }
        }
    }

    // --- hardware seams (no-ops in the simulation) ----------------------
    // Replace the bodies with a real headset SDK's open/close to drive actual
    // hardware. Left intentionally empty so nothing real is ever toggled here.
    private fun connect() { /* e.g. headsetSdk.openSession() */ }
    private fun disconnect() { /* e.g. headsetSdk.closeSession() */ }

    // --- log helpers ----------------------------------------------------

    private fun now(): String = ts.format(Date())

    private fun append(line: String) {
        log.append(if (log.text.isEmpty()) line else "\n$line")
    }

    private fun saveLog() {
        val text = log.text.toString()
        if (text.isBlank()) {
            Toast.makeText(this, "記録がありません", Toast.LENGTH_SHORT).show()
            return
        }
        try {
            val dir = File(filesDir, "bci_logs").apply { mkdirs() }
            val f = File(dir, "session_${System.currentTimeMillis()}.txt")
            f.writeText("# BadaBCI session log (simulated)\n$text\n")
            status.text = "保存しました / saved: ${f.name}"
            Toast.makeText(this, "保存: ${f.absolutePath}", Toast.LENGTH_LONG).show()
        } catch (e: Exception) {
            status.text = "保存失敗: ${e.message}"
        }
    }
}
