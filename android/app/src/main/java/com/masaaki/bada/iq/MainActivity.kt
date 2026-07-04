package com.masaaki.bada.iq

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Bada IQ 判定器 — enter each biosignal reading as a z-score (population-sd
 * units; positive = cognitively favourable), then run the four-stage
 * assessment: IQ measurement, mirror statistics, Bayesian estimation, and the
 * whispered judge.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var fields: Map<String, EditText>
    private lateinit var result: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        fields = mapOf(
            "fmri" to findViewById<EditText>(R.id.inFmri),
            "mri" to findViewById<EditText>(R.id.inMri),
            "topography" to findViewById<EditText>(R.id.inTopo),
            "dna" to findViewById<EditText>(R.id.inDna),
            "blood" to findViewById<EditText>(R.id.inBlood)
        )
        result = findViewById<TextView>(R.id.txtResult)

        findViewById<Button>(R.id.btnAssess).setOnClickListener { runAssessment() }
        findViewById<Button>(R.id.btnDemo).setOnClickListener { fillDemo() }
    }

    private fun fillDemo() {
        val demo = IqEngine.demoSubject()
        fields.forEach { (k, e) -> e.setText(demo[k]?.toString() ?: "") }
        runAssessment()
    }

    private fun runAssessment() {
        val subject = LinkedHashMap<String, Double>()
        for ((k, e) in fields) {
            val v = e.text.toString().trim()
            if (v.isEmpty()) continue
            val d = v.toDoubleOrNull()
            if (d == null) {
                result.text = getString(R.string.err_number, k)
                return
            }
            subject[k] = d
        }
        if (subject.isEmpty()) {
            result.text = getString(R.string.err_empty)
            return
        }
        result.text = try {
            IqEngine.report(IqEngine.assess(subject, id = "INPUT"))
        } catch (ex: Exception) {
            "エラー: ${ex.message}"
        }
    }
}
