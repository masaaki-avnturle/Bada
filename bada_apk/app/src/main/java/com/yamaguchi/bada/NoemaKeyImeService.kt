package com.yamaguchi.bada

import android.graphics.Color
import android.inputmethodservice.InputMethodService
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import com.yamaguchi.bada.engine.Predictor

/**
 * NoemaKey IME — a compact 60% soft keyboard for Android whose suggestion strip
 * is driven by the Unknown-Prior Engine's English/Japanese word-completion +
 * next-word look-ahead (engine.Predictor).
 *
 * The keyboard commits characters through the InputConnection; after each edit
 * it reads the text before the cursor and shows completions (for a partial
 * word) or next-word predictions (after a separator). Tapping a suggestion
 * replaces the partial word and folds the choice back into the model (the
 * append-only reviser learning loop).
 */
class NoemaKeyImeService : InputMethodService() {

    private val predictor = Predictor()
    private var shift = false
    private lateinit var suggestionStrip: LinearLayout

    // Compact 60% US layout (Control at the caps-lock row).
    private val rows = listOf(
        "1 2 3 4 5 6 7 8 9 0",
        "q w e r t y u i o p",
        "a s d f g h j k l",
        "z x c v b n m"
    )

    override fun onCreate() {
        super.onCreate()
        trainFromAssets()
    }

    private fun trainFromAssets() {
        listOf("corpus/seed_en.txt", "corpus/seed_ja.txt").forEach { path ->
            try {
                assets.open(path).use { predictor.train(it.readBytes().toString(Charsets.UTF_8)) }
            } catch (_: Exception) { }
        }
    }

    override fun onCreateInputView(): View {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#04060A"))
            setPadding(dp(4), dp(4), dp(4), dp(6))
        }

        // suggestion strip (horizontally scrollable)
        val scroll = HorizontalScrollView(this).apply {
            isHorizontalScrollBarEnabled = false
            layoutParams = LinearLayout.LayoutParams(MATCH, dp(44))
        }
        suggestionStrip = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        scroll.addView(suggestionStrip)
        root.addView(scroll)

        // keyboard
        for (row in rows) root.addView(keyRow(row.split(" ")))
        root.addView(bottomRow())

        refreshSuggestions()
        return root
    }

    // ---- keyboard rows -----------------------------------------------------

    private fun keyRow(keys: List<String>): LinearLayout {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(MATCH, WRAP)
        }
        for (k in keys) row.addView(key(k, 1f))
        return row
    }

    private fun bottomRow(): LinearLayout {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(MATCH, WRAP)
        }
        row.addView(key("⇧", 1.5f) { toggleShift() })
        row.addView(key("space", 5f, "␣") { onChar(" ") })
        row.addView(key("⌫", 1.5f) { onDelete() })
        row.addView(key("⏎", 1.5f) { onEnter() })
        return row
    }

    private fun key(label: String, weight: Float, display: String = label, onTap: (() -> Unit)? = null): Button {
        val special = label.length > 1 || label in listOf("⇧", "⌫", "⏎")
        return Button(this).apply {
            text = if (label == "space") "␣" else display
            setAllCaps(false)
            setTextColor(if (special) Color.parseColor("#C8A44A") else Color.parseColor("#E6EAF0"))
            setBackgroundColor(if (special) Color.parseColor("#2A2214") else Color.parseColor("#1A1F2A"))
            textSize = 16f
            val lp = LinearLayout.LayoutParams(0, dp(46), weight)
            lp.setMargins(dp(2), dp(2), dp(2), dp(2))
            layoutParams = lp
            setOnClickListener {
                if (onTap != null) onTap()
                else onChar(if (shift) label.uppercase() else label)
            }
        }
    }

    // ---- input handling ----------------------------------------------------

    private fun onChar(ch: String) {
        currentInputConnection?.commitText(ch, 1)
        if (shift && ch.length == 1 && ch[0].isLetter()) { shift = false }
        if (ch == " ") commitWordBeforeCursor()
        refreshSuggestions()
    }

    private fun onDelete() {
        currentInputConnection?.deleteSurroundingText(1, 0)
        refreshSuggestions()
    }

    private fun onEnter() {
        val ic = currentInputConnection ?: return
        commitWordBeforeCursor()
        ic.commitText("\n", 1)
        refreshSuggestions()
    }

    private fun toggleShift() {
        shift = !shift
        refreshSuggestions()
    }

    private fun leftText(): String =
        currentInputConnection?.getTextBeforeCursor(64, 0)?.toString() ?: ""

    private val wordTail =
        Regex("([A-Za-z0-9'\\-]+|[\\u3040-\\u309F\\u30A0-\\u30FF\\u4E00-\\u9FFF\\u3005\\u30FC]+)$")

    private fun commitWordBeforeCursor() {
        wordTail.find(leftText().trimEnd())?.let { predictor.observe(it.value) }
    }

    // ---- suggestions -------------------------------------------------------

    private fun refreshSuggestions() {
        if (!::suggestionStrip.isInitialized) return
        suggestionStrip.removeAllViews()
        val left = leftText()
        val suggestions = predictor.suggest(left, 8)
        if (suggestions.isEmpty()) {
            suggestionStrip.addView(TextView(this).apply {
                text = "  未知事前予知エンジン 予測入力  "
                setTextColor(Color.parseColor("#8A94A4"))
                gravity = Gravity.CENTER_VERTICAL
            })
            return
        }
        for (s in suggestions) {
            suggestionStrip.addView(Button(this).apply {
                text = s.word
                setAllCaps(false)
                setTextColor(Color.parseColor("#C8A44A"))
                setBackgroundColor(Color.parseColor("#0B1018"))
                textSize = 15f
                val lp = LinearLayout.LayoutParams(WRAP, dp(40))
                lp.setMargins(dp(3), dp(2), dp(3), dp(2))
                layoutParams = lp
                setOnClickListener { applySuggestion(left, s.word) }
            })
        }
    }

    private fun applySuggestion(left: String, word: String) {
        val ic = currentInputConnection ?: return
        val m = wordTail.find(left)
        if (m != null) ic.deleteSurroundingText(m.value.length, 0)
        ic.commitText("$word ", 1)
        predictor.observe(word)
        refreshSuggestions()
    }

    private fun dp(v: Int): Int = (v * resources.displayMetrics.density).toInt()

    companion object {
        private const val MATCH = ViewGroup.LayoutParams.MATCH_PARENT
        private const val WRAP = ViewGroup.LayoutParams.WRAP_CONTENT
    }
}
