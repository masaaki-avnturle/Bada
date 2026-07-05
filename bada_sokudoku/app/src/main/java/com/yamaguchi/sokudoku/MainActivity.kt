package com.yamaguchi.sokudoku

import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.RadioGroup
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import kotlin.math.max
import kotlin.random.Random

/**
 * BadaSokudoku speed-reading.
 *
 *  - SRS速読 (block flash): the report is split page-by-page and into blocks;
 *    each block is shown centered, then cleared, then the next follows.
 *  - 瞬読 (Shundoku, random flash): the report is split into small word-units
 *    ("ぶ単位") and each is flashed at a RANDOM position in the display area,
 *    very briefly. Both modes accelerate as pages advance.
 *
 * This is a reading-training / wellness tool, not a medical device.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var input: EditText
    private lateinit var cpmIn: EditText
    private lateinit var accelIn: EditText
    private lateinit var sizeIn: EditText
    private lateinit var modeGroup: RadioGroup
    private lateinit var startBtn: Button
    private lateinit var stopBtn: Button
    private lateinit var pdfBtn: Button
    private lateinit var displayArea: FrameLayout
    private lateinit var display: TextView
    private lateinit var status: TextView

    private val handler = Handler(Looper.getMainLooper())
    private var running = false

    // PDF picker: only .pdf documents
    private val pickPdf = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri: Uri? -> if (uri != null) extractPdf(uri) }

    private data class Unit(val text: String, val page: Int)

    private var units: List<Unit> = emptyList()
    private var idx = 0
    private var totalPages = 1
    private var curPage = 1
    private var curCpm = 600
    private var accel = 150
    private var srsMode = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        PDFBoxResourceLoader.init(applicationContext)

        input = findViewById(R.id.input)
        cpmIn = findViewById(R.id.cpm)
        accelIn = findViewById(R.id.accel)
        sizeIn = findViewById(R.id.size)
        modeGroup = findViewById(R.id.modeGroup)
        startBtn = findViewById(R.id.startBtn)
        stopBtn = findViewById(R.id.stopBtn)
        pdfBtn = findViewById(R.id.pdfBtn)
        displayArea = findViewById(R.id.displayArea)
        display = findViewById(R.id.display)
        status = findViewById(R.id.status)

        input.setText(getString(R.string.sample_report))

        modeGroup.setOnCheckedChangeListener { _, id ->
            // sensible default unit size per mode
            if (id == R.id.modeShundoku) {
                if (sizeIn.text.toString() == "40") sizeIn.setText("3")
            } else {
                if (sizeIn.text.toString() == "3") sizeIn.setText("40")
            }
        }

        startBtn.setOnClickListener { start() }
        stopBtn.setOnClickListener { stop("停止しました / stopped") }
        pdfBtn.setOnClickListener { pickPdf.launch(arrayOf("application/pdf")) }
    }

    /** Extract text from a user-picked PDF (off the main thread) and load it. */
    private fun extractPdf(uri: Uri) {
        stop(null)
        pdfBtn.isEnabled = false
        status.text = "PDF読み込み中… / reading PDF…"
        Thread {
            var text = ""
            var pages = 0
            var err: String? = null
            try {
                contentResolver.openInputStream(uri).use { ins ->
                    PDDocument.load(ins).use { doc ->
                        pages = doc.numberOfPages
                        val stripper = PDFTextStripper()
                        val sb = StringBuilder()
                        for (p in 1..pages) {          // per page -> form-feed = SRS page break
                            stripper.startPage = p
                            stripper.endPage = p
                            sb.append(stripper.getText(doc))
                            if (p < pages) sb.append('\u000C')
                        }
                        text = sb.toString()
                    }
                }
            } catch (e: Exception) {
                err = e.message ?: e.javaClass.simpleName
            }
            val finalText = text
            val finalPages = pages
            val finalErr = err
            runOnUiThread {
                pdfBtn.isEnabled = true
                if (finalErr != null) {
                    status.text = "PDF読み込み失敗: $finalErr"
                    Toast.makeText(this, "PDFを読み込めませんでした", Toast.LENGTH_LONG).show()
                    return@runOnUiThread
                }
                if (finalText.isBlank()) {
                    status.text = "テキストを抽出できませんでした（画像PDFの可能性）"
                    Toast.makeText(this, "文字が見つかりません（画像化されたPDFはOCRが必要）",
                        Toast.LENGTH_LONG).show()
                    return@runOnUiThread
                }
                input.setText(finalText)
                val chars = finalText.codePointCount(0, finalText.length)
                status.text = "PDF読込完了: $finalPages ページ / 約 $chars 文字。開始を押してください"
            }
        }.start()
    }

    override fun onPause() {
        super.onPause()
        stop("一時停止 / paused")
    }

    private fun intOr(e: EditText, def: Int, min: Int): Int {
        val v = e.text.toString().trim().toIntOrNull() ?: def
        return if (v < min) min else v
    }

    private fun start() {
        stop(null)
        val text = input.text.toString()
        srsMode = modeGroup.checkedRadioButtonId == R.id.modeSrs
        curCpm = intOr(cpmIn, 600, 60)
        accel = intOr(accelIn, if (srsMode) 150 else 200, 0)
        val size = intOr(sizeIn, if (srsMode) 40 else 3, if (srsMode) 8 else 1)

        units = if (srsMode) buildSrsBlocks(text, size) else buildShundokuUnits(text, size)
        if (units.isEmpty()) {
            status.text = "表示できるテキストがありません"
            return
        }
        totalPages = units.last().page
        idx = 0
        curPage = units.first().page
        running = true
        startBtn.isEnabled = false
        schedule()
    }

    private fun stop(msg: String?) {
        running = false
        handler.removeCallbacksAndMessages(null)
        startBtn.isEnabled = true
        if (msg != null) {
            display.text = ""
            status.text = msg
        }
    }

    private fun schedule() {
        if (!running) return
        if (idx >= units.size) {
            running = false
            startBtn.isEnabled = true
            display.text = "完了 / done"
            display.layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER
            )
            status.text = "全 ${units.size} 単位・$totalPages ページを表示しました"
            return
        }
        val u = units[idx]
        if (u.page != curPage) {
            curPage = u.page
            curCpm += accel               // speed up each page
        }
        showUnit(u)
        status.text = (if (srsMode) "SRS" else "瞬読") +
            "  ページ ${u.page}/$totalPages  単位 ${idx + 1}/${units.size}  $curCpm CPM"

        val cps = u.text.codePointCount(0, u.text.length)
        var ms = cps.toLong() * 60000L / max(1, curCpm)
        val floor = if (srsMode) 120L else 55L
        if (ms < floor) ms = floor
        idx++
        handler.postDelayed({ schedule() }, ms)
    }

    private fun showUnit(u: Unit) {
        display.text = u.text
        if (srsMode) {
            display.layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER
            )
        } else {
            // random flash position: measure after layout, then place
            display.layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.TOP or Gravity.START
            )
            display.post {
                val availW = displayArea.width - display.width
                val availH = displayArea.height - display.height
                display.x = if (availW > 0) Random.nextInt(availW).toFloat() else 0f
                display.y = if (availH > 0) Random.nextInt(availH).toFloat() else 0f
            }
        }
    }

    // ---- text -> units -------------------------------------------------

    private val breakChars = setOf(
        ' ', '\t', '\n', '\r', '.', ',', '!', '?', ';', ':',
        '　', '。', '、', '！', '？', '，', '．', '；', '：'
    )

    /** SRS: page-tagged blocks (form-feed / blank-line boundaries, ~blockChars each). */
    private fun buildSrsBlocks(text: String, blockChars: Int): List<Unit> {
        val out = ArrayList<Unit>()
        val sb = StringBuilder()
        var page = 1
        var seenFF = false
        var count = 0
        var prevNl = false

        fun flush() {
            val t = sb.toString().trim()
            if (t.isNotEmpty()) out.add(Unit(t, page))
            sb.setLength(0); count = 0
        }

        for (ch in text) {
            when {
                ch == '\u000C' -> { seenFF = true; flush(); page++; prevNl = false; continue }
                ch == '\n' && prevNl -> { flush(); prevNl = true; continue }
            }
            prevNl = ch == '\n'
            sb.append(ch); count++
            if (count >= blockChars && (ch in breakChars || count >= blockChars + 24)) flush()
        }
        flush()

        if (!seenFF) {                       // synthesize pages every 6 blocks
            val perPage = 6
            for (i in out.indices) out[i] = out[i].copy(page = i / perPage + 1)
        }
        return out
    }

    /** 瞬読: small word-units; long CJK runs chunked to unitChars; page every 40 units. */
    private fun buildShundokuUnits(text: String, unitChars: Int): List<Unit> {
        val out = ArrayList<Unit>()
        val tokens = text.split(Regex("\\s+")).filter { it.isNotBlank() }
        var page = 1
        var perPage = 0
        val chunk = if (unitChars < 1) 1 else unitChars
        for (tok in tokens) {
            var i = 0
            while (i < tok.length) {
                val end = minOf(i + chunk, tok.length)
                out.add(Unit(tok.substring(i, end), page))
                i = end
                if (++perPage >= 40) { perPage = 0; page++ }
            }
        }
        return out
    }
}
