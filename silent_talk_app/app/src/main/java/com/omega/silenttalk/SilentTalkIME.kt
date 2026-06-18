package com.omega.silenttalk

import android.inputmethodservice.InputMethodService
import android.os.Handler
import android.os.Looper
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.GridLayout
import android.widget.TextView

/**
 * SilentTalkIME — Silent Talk を「他アプリへの文字入力機能」にする
 * カスタム入力メソッド (キーボード)。
 *
 * 任意のアプリのテキスト欄をタップすると、ダイアログ風の小型 GUI パネルが現れる。
 * パネルのキーをタッチすると、その文字が現在編集中のアプリへ入力される。
 * 各キー入力は neurothermal のガンマ熱多様体 (T'=∫Γ(γ)'dx_m) で「無音信号」化され、
 * 上部の赤外線センサー + 温度計バーがライブ更新される（全機能にセンサー付属）。
 */
class SilentTalkIME : InputMethodService() {

    private val ui = Handler(Looper.getMainLooper())
    private var sensorLine: TextView? = null
    private var signalLine: TextView? = null
    private var caps = false

    // コンパクト配列（ダイアログ風の小型キーボード）
    private val rows = arrayOf(
        "1234567890",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm"
    )

    private val sensorTick = object : Runnable {
        override fun run() {
            updateSensor()
            ui.postDelayed(this, 2000)
        }
    }

    override fun onCreateInputView(): View {
        val root = layoutInflater.inflate(R.layout.keyboard_view, null)

        sensorLine = root.findViewById(R.id.kbSensor)
        signalLine = root.findViewById(R.id.kbSignal)
        val grid = root.findViewById<GridLayout>(R.id.kbGrid)

        buildKeys(grid)

        root.findViewById<Button>(R.id.kbShift).setOnClickListener {
            caps = !caps
            refreshKeyCaps(grid)
        }
        root.findViewById<Button>(R.id.kbSpace).setOnClickListener { commit(" ") }
        root.findViewById<Button>(R.id.kbDelete).setOnClickListener {
            currentInputConnection?.deleteSurroundingText(1, 0)
            showSignal("⌫ delete")
        }
        root.findViewById<Button>(R.id.kbEnter).setOnClickListener {
            sendEnter()
        }
        root.findViewById<Button>(R.id.kbHide).setOnClickListener {
            requestHideSelf(0)
        }
        updateSensor()
        return root
    }

    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        ui.removeCallbacks(sensorTick)
        ui.post(sensorTick)
    }

    override fun onFinishInputView(finishingInput: Boolean) {
        super.onFinishInputView(finishingInput)
        ui.removeCallbacks(sensorTick)
    }

    private fun buildKeys(grid: GridLayout) {
        grid.removeAllViews()
        grid.columnCount = 10
        for (row in rows) {
            for (ch in row) {
                val b = Button(this)
                b.text = ch.toString()
                b.tag = ch
                b.textSize = 16f
                b.isAllCaps = false
                val lp = GridLayout.LayoutParams().apply {
                    width = 0
                    height = GridLayout.LayoutParams.WRAP_CONTENT
                    columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1, 1f)
                    setMargins(2, 2, 2, 2)
                }
                b.layoutParams = lp
                b.setOnClickListener { onKey(ch) }
                grid.addView(b)
            }
            // 行末を埋めて10列グリッドの折り返しを保つ
            val pad = 10 - row.length
            repeat(pad) {
                val spacer = View(this)
                val lp = GridLayout.LayoutParams().apply {
                    width = 0
                    height = 1
                    columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1, 1f)
                }
                spacer.layoutParams = lp
                grid.addView(spacer)
            }
        }
    }

    private fun refreshKeyCaps(grid: GridLayout) {
        for (i in 0 until grid.childCount) {
            val v = grid.getChildAt(i)
            if (v is Button) {
                val ch = v.tag as? Char ?: continue
                v.text = if (caps) ch.uppercaseChar().toString() else ch.toString()
            }
        }
    }

    private fun onKey(ch: Char) {
        val out = if (caps && ch.isLetter()) ch.uppercaseChar() else ch
        commit(out.toString())
    }

    /** 文字を編集中アプリへ入力し、無音信号として可視化する */
    private fun commit(text: String) {
        currentInputConnection?.commitText(text, 1)
        val pulses = SilentCodec.encode(text)
        val p = pulses.firstOrNull()
        if (p != null) {
            showSignal("'%s' → γ=%.3f  T=%.4f°C  [%d]".format(text, p.gamma, p.tempC, p.code))
        }
    }

    private fun sendEnter() {
        val ic = currentInputConnection ?: return
        val opts = currentInputEditorInfo?.imeOptions ?: 0
        val action = opts and EditorInfo.IME_MASK_ACTION
        if (action != EditorInfo.IME_ACTION_NONE &&
            (opts and EditorInfo.IME_FLAG_NO_ENTER_ACTION) == 0) {
            ic.performEditorAction(action)
        } else {
            ic.commitText("\n", 1)
        }
        showSignal("⏎ enter")
    }

    private fun updateSensor() {
        val s = NeuroThermal.snapshot()
        sensorLine?.text = "🔴IR %.2f°C  🌡️%.2f°C  ⚖️%.2f°C  T'=%.2f"
            .format(s.ir, s.thermo, s.fused, s.energy)
    }

    private fun showSignal(msg: String) {
        signalLine?.text = msg
    }
}
