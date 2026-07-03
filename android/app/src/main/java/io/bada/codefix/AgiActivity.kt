package io.bada.codefix

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import java.util.concurrent.Executors

/**
 * OmegaAgi screen — the report-driven generative AI (未知エンジン / AGI 分派).
 *
 * Upload reports (source code + PDF), then ask a question. The engine
 * correlates the question with the ingested corpus through the gamma-function
 * global partial integral manifold invariant Ξ and generates an answer
 * (OmegaAgi). No cloud LLM — everything runs on device.
 */
class AgiActivity : AppCompatActivity() {

    private var agi = OmegaAgi()
    private val io = Executors.newSingleThreadExecutor()
    private lateinit var status: TextView
    private lateinit var result: TextView
    private lateinit var questionInput: EditText

    private val pickReports =
        registerForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
            if (!uris.isNullOrEmpty()) ingest(uris)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_agi)
        title = "OmegaAgi — レポート生成AI"

        status = findViewById(R.id.agiStatus)
        result = findViewById(R.id.agiResult)
        questionInput = findViewById(R.id.questionInput)

        findViewById<Button>(R.id.ingestButton).setOnClickListener { pickReports.launch(arrayOf("*/*")) }
        findViewById<Button>(R.id.demoReportButton).setOnClickListener { loadDemoReport() }
        findViewById<Button>(R.id.clearButton).setOnClickListener {
            agi = OmegaAgi(); refreshStatus(); result.text = ""
            Toast.makeText(this, "コーパスをクリアしました", Toast.LENGTH_SHORT).show()
        }
        findViewById<Button>(R.id.generateButton).setOnClickListener { generate() }
        findViewById<Button>(R.id.agiCopyButton).setOnClickListener { copyResult() }

        refreshStatus()
    }

    override fun onDestroy() { io.shutdownNow(); super.onDestroy() }

    private fun refreshStatus() {
        status.text = "コーパス: ${agi.sourceCount()} レポート / ${agi.sentenceCount()} 文"
    }

    private fun ingest(uris: List<Uri>) {
        Toast.makeText(this, "${uris.size} 件を取り込み中…", Toast.LENGTH_SHORT).show()
        io.execute {
            for (uri in uris) {
                val name = FileIntake.displayName(this, uri)
                val text = try {
                    FileIntake.extractText(this, uri, name)
                } catch (e: Exception) { "" }
                if (text.isNotBlank()) agi.ingest(text, name)
            }
            runOnUiThread {
                refreshStatus()
                Toast.makeText(this, "取り込み完了。質問を入力してください", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun generate() {
        val q = questionInput.text.toString().trim()
        if (q.isEmpty()) {
            Toast.makeText(this, "質問を入力してください", Toast.LENGTH_SHORT).show(); return
        }
        if (agi.isEmpty()) {
            Toast.makeText(this, "先にレポートを取り込むか「デモレポート」を押してください", Toast.LENGTH_LONG).show(); return
        }
        result.text = "生成中…"
        io.execute {
            val a = agi.ask(q)
            val text = render(a)
            runOnUiThread { result.text = text }
        }
    }

    private fun render(a: OmegaAgi.Answer): String {
        val sb = StringBuilder()
        sb.appendLine("╔═ OmegaAgi — ガンマ関数・大域的部分積分多様体による相関生成")
        sb.appendLine("║ 質問 H=${"%.4f".format(a.questionEntropy)}  Ξ_q=${"%.6f".format(a.questionXi)}  目標H=${"%.3f".format(a.targetEntropy)}")
        sb.appendLine("║ コーパス: ${a.sourcesCount} レポート / ${a.sentenceCount} 文")
        sb.appendLine("╚" + "═".repeat(52))
        sb.appendLine()
        sb.appendLine("■ 生成された応答（未知エンジン・エントロピー整合）")
        sb.appendLine("  ${a.generated}")
        sb.appendLine("  └ 生成 H=${"%.4f".format(a.generatedEntropy)}  Ξ=${"%.6f".format(a.generatedXi)}")
        sb.appendLine()
        sb.appendLine("■ 相関した根拠（β(H_q+1,H_d+1) × 1/(1+ΔΞ)）")
        if (a.matches.isEmpty()) {
            sb.appendLine("  （相関する文が見つかりませんでした）")
        } else {
            a.matches.forEachIndexed { i, m ->
                sb.appendLine("  ${i + 1}. [${m.sentence.source}] corr=${"%.4f".format(m.correlation)}  kernel β=${"%.4f".format(m.kernel)}  ΔΞ=${"%.5f".format(m.deltaXi)}  kw=${m.keyword}")
                sb.appendLine("     H=${"%.3f".format(m.sentence.entropy)} Ξ=${"%.5f".format(m.sentence.invariant)}: ${trim(m.sentence.text)}")
            }
        }
        return sb.toString()
    }

    private fun trim(text: String, n: Int = 240): String {
        val t = text.replace("\n", " ")
        return if (t.length > n) t.substring(0, n) + "…" else t
    }

    private fun loadDemoReport() {
        agi.ingest(
            """
            大域的部分積分多様体 M 上で、エントロピー不変量 Ξ は複素回転体 e^{iθ} の下で保存される。
            ガンマ関数 Γ(γ) の部分積分により β(p,q) が現れ、これが ζ(s)=x·log x のゲージを与える。
            シャノンのエントロピー H を多様体線素 1/(x·log x)² で重み付け積分すると不変量 Ξ を得る。
            特殊相対性理論のコマ幾何の可積分系がエラーを修正し、Ξ を閉軌道 ∮ 上で安定化させる。
            未知エンジンは質問のエントロピー値 H_q を多様体不変量 Ξ_q に写し、近傍の知識を生成する。
            β(p,q) = Γ(p)Γ(q)/Γ(p+q) は大域的微分多様体上のベータ関数として全体を貫く。
            """.trimIndent(),
            "demo_report.txt"
        )
        refreshStatus()
        Toast.makeText(this, "デモレポートを取り込みました", Toast.LENGTH_SHORT).show()
    }

    private fun copyResult() {
        val text = result.text.toString()
        if (text.isEmpty()) {
            Toast.makeText(this, "コピーする結果がありません", Toast.LENGTH_SHORT).show(); return
        }
        val cm = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("OmegaAgi", text))
        Toast.makeText(this, "コピーしました", Toast.LENGTH_SHORT).show()
    }
}
