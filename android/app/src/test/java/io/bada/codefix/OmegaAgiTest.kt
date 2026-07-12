package io.bada.codefix

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Tests for the report-driven generative engine (未知エンジン / AGI). */
class OmegaAgiTest {

    private fun seeded(): OmegaAgi {
        val agi = OmegaAgi(seed = 7L)
        agi.ingest(
            "大域的部分積分多様体 M 上でエントロピー不変量 Ξ は保存される。" +
                "ガンマ関数 Γ(γ) の部分積分により β(p,q) が現れる。" +
                "シャノンのエントロピー H を多様体線素で重み付け積分すると Ξ を得る。",
            "report.txt"
        )
        return agi
    }

    @Test
    fun ingestBuildsCorpus() {
        val agi = seeded()
        assertEquals(1, agi.sourceCount())
        assertTrue(agi.sentenceCount() >= 3)
        assertTrue(!agi.isEmpty())
    }

    @Test
    fun askReturnsCorrelatedMatchesAndGeneration() {
        val a = seeded().ask("ガンマ関数と多様体の不変量")
        assertTrue("must correlate at least one sentence", a.matches.isNotEmpty())
        assertTrue("Xi_q finite", a.questionXi.isFinite())
        assertTrue("entropy non-negative", a.questionEntropy >= 0.0)
        assertTrue("generated non-empty", a.generated.isNotBlank())
        // matches ranked by correlation (descending)
        val corrs = a.matches.map { it.correlation }
        assertEquals(corrs.sortedDescending(), corrs)
        // the gamma-function kernel is a finite positive weight
        assertTrue(a.matches.all { it.kernel > 0.0 && it.kernel.isFinite() })
    }

    @Test
    fun explicitEntropyTargetIsParsed() {
        val a = seeded().ask("H=2.5 に近い記述を返して")
        assertEquals(2.5, a.targetEntropy, 1e-9)
    }

    @Test
    fun emptyCorpusIsReportedEmpty() {
        assertTrue(OmegaAgi().isEmpty())
    }
}
