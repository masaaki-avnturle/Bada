package com.omega.silenttalk

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.omega.silenttalk.databinding.ActivityMainBinding

/**
 * Silent Talk — 無音通信アプリ。
 *
 * neurothermal のガンマ熱多様体 (T'=∫Γ(γ)'dx_m) を搬送波に、テキストを
 * 「熱・神経パルス列」へ符号化して “言葉を使わず信号で伝える”。
 * 画面上部には赤外線センサーと温度計の常設バーを置き、2秒ごとにライブ更新する。
 */
class MainActivity : AppCompatActivity() {

    private lateinit var b: ActivityMainBinding
    private val ui = Handler(Looper.getMainLooper())
    private var lastPulses: List<SilentCodec.Pulse> = emptyList()

    private val sensorTick = object : Runnable {
        override fun run() {
            updateSensors()
            ui.postDelayed(this, 2000)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)

        b.btnEncode.setOnClickListener { doEncode() }
        b.btnDecode.setOnClickListener { doDecode() }
        b.btnClear.setOnClickListener {
            b.inputText.setText("")
            b.outputPulses.text = ""
            lastPulses = emptyList()
        }

        b.inputText.setText("Silent Talk — 言葉を使わず信号で伝える")
        updateSensors()
    }

    override fun onResume() {
        super.onResume()
        ui.post(sensorTick)
    }

    override fun onPause() {
        super.onPause()
        ui.removeCallbacks(sensorTick)
    }

    /** 全画面共通: 赤外線センサー + 温度計の常設バーを更新 */
    private fun updateSensors() {
        val s = NeuroThermal.snapshot()
        b.valIr.text = "%.2f °C".format(s.ir)
        b.valThermo.text = "%.2f °C".format(s.thermo)
        b.valFused.text = "%.2f °C".format(s.fused)
        b.valEnergy.text = "T' = %.3f".format(s.energy)
        b.barIr.progress = norm(s.ir)
        b.barThermo.progress = norm(s.thermo)
        b.barFused.progress = norm(s.fused)
    }

    private fun norm(c: Double): Int =
        (((c - 34.0) / 7.0).coerceIn(0.0, 1.0) * 100).toInt()

    private fun doEncode() {
        val text = b.inputText.text.toString()
        if (text.isEmpty()) {
            Toast.makeText(this, "テキストを入力してください", Toast.LENGTH_SHORT).show()
            return
        }
        val pulses = SilentCodec.encode(text)
        lastPulses = pulses
        val ok = SilentCodec.verify(text)
        b.outputPulses.text = buildString {
            append("無音パルス列 (%d signals, mean T=%.3f°C, 往復検証=%s)\n\n"
                .format(pulses.size, SilentCodec.meanTemp(pulses), if (ok) "OK" else "NG"))
            append(SilentCodec.serialize(pulses))
        }
    }

    private fun doDecode() {
        if (lastPulses.isEmpty()) {
            Toast.makeText(this, "先にエンコードしてください", Toast.LENGTH_SHORT).show()
            return
        }
        val decoded = SilentCodec.decode(lastPulses)
        b.outputPulses.text = "復号結果:\n\n$decoded"
    }
}
