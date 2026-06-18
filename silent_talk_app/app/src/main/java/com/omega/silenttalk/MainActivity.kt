package com.omega.silenttalk

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.inputmethod.InputMethodManager
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.omega.silenttalk.databinding.ActivityMainBinding

/**
 * Silent Talk — 無音通信アプリ + サイレント・リスニング。
 *
 * neurothermal のガンマ熱多様体 (T'=∫Γ(γ)'dx_m) を搬送波に、テキストを
 * 「熱・神経パルス列」へ符号化して “言葉を使わず信号で伝える”。
 * 「聞き取り開始/停止」で小声(ささやき)を連続認識し、合言葉でコマンド実行する。
 */
class MainActivity : AppCompatActivity() {

    private lateinit var b: ActivityMainBinding
    private val ui = Handler(Looper.getMainLooper())
    private var lastPulses: List<SilentCodec.Pulse> = emptyList()

    private lateinit var listener: SilentListener
    private var listenerOn = false

    private val sensorTick = object : Runnable {
        override fun run() {
            updateSensors()
            ui.postDelayed(this, 2000)
        }
    }

    private val micPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) startListening()
            else Toast.makeText(this, R.string.mic_needed, Toast.LENGTH_SHORT).show()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)

        listener = SilentListener(
            context = this,
            onPartial = { text -> ui.post { b.listenHeard.text = "… $text" } },
            onFinal = { text -> ui.post { onHeard(text) } },
            onStateChange = { active -> ui.post { reflectListening(active) } },
            onError = { msg -> ui.post { b.listenStatus.text = "状態: $msg" } }
        )

        b.btnEncode.setOnClickListener { doEncode() }
        b.btnDecode.setOnClickListener { doDecode() }
        b.btnClear.setOnClickListener { doClear() }

        b.btnListen.setOnClickListener { toggleListening() }

        // 入力メソッド(キーボード)としての有効化フロー
        b.btnEnableIme.setOnClickListener {
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        }
        b.btnPickIme.setOnClickListener {
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            imm.showInputMethodPicker()
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

    override fun onDestroy() {
        super.onDestroy()
        listener.stop()
    }

    // ---- listening ----

    private fun toggleListening() {
        if (listenerOn) {
            listener.stop()
        } else {
            val granted = ContextCompat.checkSelfPermission(
                this, Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED
            if (granted) startListening() else micPermission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun startListening() {
        if (!listener.isAvailable()) {
            b.listenStatus.text = "状態: 音声認識が利用できません"
            return
        }
        listener.start()
    }

    private fun reflectListening(active: Boolean) {
        listenerOn = active
        b.btnListen.setText(if (active) R.string.listen_stop else R.string.listen_start)
        b.listenStatus.setText(if (active) R.string.listen_active else R.string.listen_idle)
    }

    /** 認識確定テキストの処理: 起動/停止合言葉 → コマンド → 通常入力 */
    private fun onHeard(text: String) {
        b.listenHeard.text = "聞: $text"

        if (CommandRegistry.isSleep(text)) {
            listener.stop()
            return
        }
        if (CommandRegistry.isWake(text)) {
            b.listenStatus.text = "状態: 起動合言葉を確認"
            return
        }

        val cmd = CommandRegistry.match(text)
        if (cmd != null) {
            runCommand(cmd)
        } else {
            // 合言葉でなければ入力欄へ追記し、無音信号化
            val cur = b.inputText.text.toString()
            b.inputText.setText(if (cur.isBlank()) text else "$cur $text")
            doEncode()
        }
    }

    private fun runCommand(cmd: CommandRegistry.Command) {
        b.listenStatus.text = "コマンド実行: ${cmd.description}"
        when (cmd.id) {
            "encode" -> doEncode()
            "decode" -> doDecode()
            "clear" -> doClear()
            "sensor" -> updateSensors()
            "keyboard" -> {
                val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
                imm.showInputMethodPicker()
            }
            "help" -> b.outputPulses.text = CommandRegistry.helpText()
        }
    }

    // ---- core features ----

    private fun doClear() {
        b.inputText.setText("")
        b.outputPulses.text = ""
        lastPulses = emptyList()
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
