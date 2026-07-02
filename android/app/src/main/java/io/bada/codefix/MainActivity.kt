package io.bada.codefix

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

/**
 * The source-code error-fixing application — complex-rotation / special-
 * relativity integrable koma geometry — with multi-submission (複数投稿).
 *
 * Post many sources into the board, tap "すべて修正" (Fix all), and the
 * CodeFixEngine closes each source's spin orbit and prints a batch report
 * plus every corrected source.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var container: LinearLayout
    private lateinit var result: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        container = findViewById(R.id.submissionsContainer)
        result = findViewById(R.id.resultText)

        findViewById<Button>(R.id.addButton).setOnClickListener { addSubmission() }
        findViewById<Button>(R.id.fixButton).setOnClickListener { fixAll() }
        findViewById<Button>(R.id.demoButton).setOnClickListener { loadDemo() }
        findViewById<Button>(R.id.copyButton).setOnClickListener { copyResult() }

        // start with one empty submission card
        addSubmission()
    }

    private fun addSubmission(name: String = "", code: String = "") {
        val card = LayoutInflater.from(this)
            .inflate(R.layout.item_submission, container, false)
        card.findViewById<EditText>(R.id.nameInput).setText(name)
        card.findViewById<EditText>(R.id.codeInput).setText(code)
        card.findViewById<Button>(R.id.removeButton).setOnClickListener {
            container.removeView(card)
        }
        container.addView(card)
    }

    private fun fixAll() {
        val repo = CodeFixEngine.Repository()
        var posted = 0
        for (idx in 0 until container.childCount) {
            val card = container.getChildAt(idx)
            val code = card.findViewById<EditText>(R.id.codeInput).text.toString()
            if (code.isBlank()) continue
            var name = card.findViewById<EditText>(R.id.nameInput).text.toString().trim()
            if (name.isEmpty()) name = "submission_${posted + 1}"
            repo.submit(code, name)
            posted++
        }
        if (posted == 0) {
            Toast.makeText(this, "ソースコードを入力してください", Toast.LENGTH_SHORT).show()
            result.text = ""
            return
        }

        val sb = StringBuilder(repo.report())
        sb.appendLine()
        sb.appendLine("── 修正後ソース（軌道を再び閉じる）───────────────")
        for (s in repo.submissions) {
            if (!s.result.changed) continue
            sb.appendLine()
            sb.appendLine("### ${s.name}")
            sb.appendLine(s.result.fixed.trimEnd())
        }
        result.text = sb.toString()
    }

    private fun loadDemo() {
        container.removeAllViews()
        addSubmission("greeter.rb", "def greet(name\n  puts \"hello, \${name}\nend\n")
        addSubmission("counter.rb", "class Counter\n  def initialize\n    @n = 0\n\n  def tick\n    @n += 1\n  end\nend\n")
        addSubmission("geometry.py", "def top_energy(m, r, omega):\n    I = (m * r ** 2\n    return 0.5 * I * omega ** 2\n")
        addSubmission("already_ok.rb", "def spin(theta)\n  Math.cos(theta)\nend\n")
        Toast.makeText(this, "デモを読み込みました。「すべて修正」を押してください", Toast.LENGTH_SHORT).show()
    }

    private fun copyResult() {
        val text = result.text.toString()
        if (text.isEmpty()) {
            Toast.makeText(this, "コピーする結果がありません", Toast.LENGTH_SHORT).show()
            return
        }
        val cm = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("Bada CodeFix", text))
        Toast.makeText(this, "結果をコピーしました", Toast.LENGTH_SHORT).show()
    }
}
