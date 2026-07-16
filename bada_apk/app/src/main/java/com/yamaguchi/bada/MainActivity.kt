package com.yamaguchi.bada

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.provider.Settings
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.yamaguchi.bada.engine.Precog
import java.io.BufferedReader
import java.io.InputStreamReader

/**
 * 未知事前予知エンジン (Bada Precog) — the ChatGPT-evolution Unknown-Prior
 * Precognition Engine as an Android app, with MULTIPLE-FILE upload.
 *
 * Upload any number of text files (reports, notes, corpora); each is ingested
 * into the engine's knowledge base. Ask a question and the engine foresees the
 * unknown prior, runs the reviser learning loop and quantum foresight, and
 * analyses the question across the seven Millennium problems.
 */
class MainActivity : AppCompatActivity() {

    private var precog = Precog(seed = 42L)
    private val uploaded = ArrayList<String>()

    private lateinit var fileList: TextView
    private lateinit var status: TextView
    private lateinit var question: EditText
    private lateinit var output: TextView
    private lateinit var foreseeBtn: Button

    // Multiple-file picker via the Storage Access Framework.
    private val pickFiles =
        registerForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
            if (!uris.isNullOrEmpty()) ingestUris(uris)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        fileList = findViewById(R.id.fileList)
        status = findViewById(R.id.status)
        question = findViewById(R.id.question)
        output = findViewById(R.id.output)
        foreseeBtn = findViewById(R.id.foreseeBtn)

        findViewById<Button>(R.id.uploadBtn).setOnClickListener {
            // text/* plus a wildcard so .md/.csv/.bada/etc. are selectable too.
            pickFiles.launch(arrayOf("text/*", "application/octet-stream", "*/*"))
        }

        findViewById<Button>(R.id.clearBtn).setOnClickListener {
            precog = Precog(seed = 42L)
            uploaded.clear()
            refreshStatus()
            output.text = ""
        }

        foreseeBtn.setOnClickListener { runForesee() }

        findViewById<Button>(R.id.enableKbBtn).setOnClickListener {
            // Open system IME settings to enable "NoemaKey", then show the picker.
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
            (getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager)?.showInputMethodPicker()
        }

        // Quantum-crypto credit protection badge (BB84 + HMAC-SHA256).
        findViewById<TextView>(R.id.creditLabel).text =
            "${com.yamaguchi.bada.engine.CreditGuard.badge()}\n${com.yamaguchi.bada.engine.CreditGuard.notice()}"

        refreshStatus()
    }

    private fun ingestUris(uris: List<Uri>) {
        status.text = getString(R.string.reading)
        Thread {
            var added = 0
            for (uri in uris) {
                try {
                    val name = displayName(uri)
                    val text = readText(uri)
                    if (text.isNotBlank()) {
                        precog.learn(text, name)
                        uploaded.add("$name (${text.length} 文字)")
                        added++
                    }
                } catch (e: Exception) {
                    uploaded.add("読み込み失敗: ${e.message}")
                }
            }
            runOnUiThread {
                refreshStatus()
                status.text = getString(R.string.ingested, added, precog.knowledge.size)
            }
        }.start()
    }

    private fun runForesee() {
        val q = question.text.toString().trim()
        if (q.isEmpty()) {
            output.text = getString(R.string.enter_question)
            return
        }
        foreseeBtn.isEnabled = false
        status.text = getString(R.string.foreseeing)
        Thread {
            val result = try {
                precog.ask(q)
            } catch (e: Exception) {
                "エラー: ${e.message}"
            }
            runOnUiThread {
                output.text = result
                foreseeBtn.isEnabled = true
                refreshStatus()
            }
        }.start()
    }

    private fun refreshStatus() {
        fileList.text = if (uploaded.isEmpty()) getString(R.string.no_files)
        else uploaded.joinToString("\n") { "• $it" }
        status.text = getString(R.string.corpus_status, uploaded.size, precog.knowledge.size, precog.rules.size)
    }

    private fun displayName(uri: Uri): String {
        var name = uri.lastPathSegment ?: "file"
        try {
            contentResolver.query(uri, null, null, null, null)?.use { c ->
                val idx = c.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (idx >= 0 && c.moveToFirst()) name = c.getString(idx) ?: name
            }
        } catch (_: Exception) { }
        return name
    }

    private fun readText(uri: Uri): String {
        contentResolver.openInputStream(uri).use { input ->
            if (input == null) return ""
            BufferedReader(InputStreamReader(input, Charsets.UTF_8)).use { return it.readText() }
        }
    }
}
