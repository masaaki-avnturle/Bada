package com.masaaki.bada.iq

import java.util.Locale
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.log2
import kotlin.math.sqrt

/**
 * Bada::IQ — subject IQ assessment, ported faithfully from the pure-Ruby Bada
 * library (bada_ruby/lib/bada/iq.rb) so the Android app produces the same
 * numbers as `bin/bada iq`.
 *
 *   fMRI / MRI / 脳トポグラフィ(EEG) / DNA解析 / 血液検査
 *        -> [1] IQ measurement   (regress each biosignal onto the IQ scale)
 *           [2] Mirror statistics (reflection-symmetric robust summary)
 *           [3] Bayesian estimate (Gaussian conjugate fusion, prior N(100,15^2))
 *           [4] Whispered judge   (soft band verdict gated by the TupleSpace Xi)
 *
 * SAFETY / 免責: educational model of the Yamaguchi framework — NOT a medical
 * device, NOT a diagnosis. The reliability constants are framework calibration
 * values, not clinical measurements.
 */
object IqEngine {

    const val POP_MEAN = 100.0
    const val POP_SD = 15.0

    data class Modality(val key: String, val rho: Double, val label: String)

    // The five biosignal modalities of the earlier Bada bio-medical apps.
    val MODALITIES: LinkedHashMap<String, Modality> = linkedMapOf(
        "fmri" to Modality("fmri", 0.42, "fMRI 機能的結合効率"),
        "mri" to Modality("mri", 0.40, "MRI 灰白質体積・皮質厚"),
        "topography" to Modality("topography", 0.38, "脳トポグラフィ EEG(神経伝導速度)"),
        "dna" to Modality("dna", 0.30, "DNA 認知ポリジェニックスコア"),
        "blood" to Modality("blood", 0.20, "血液バイオマーカー(BDNF・代謝・炎症)")
    )

    data class Band(val lo: Double, val hi: Double, val ja: String, val en: String)

    // Wechsler (WAIS) classification bands: [lo, hi) on the IQ scale.
    val BANDS: List<Band> = listOf(
        Band(Double.NEGATIVE_INFINITY, 70.0, "知的発達境界域以下", "Extremely Low"),
        Band(70.0, 80.0, "境界域", "Borderline"),
        Band(80.0, 90.0, "平均の下", "Low Average"),
        Band(90.0, 110.0, "平均", "Average"),
        Band(110.0, 120.0, "平均の上", "High Average"),
        Band(120.0, 130.0, "優秀", "Superior"),
        Band(130.0, Double.POSITIVE_INFINITY, "非常に優秀", "Very Superior")
    )

    // ── Special functions (Lanczos gamma / beta / erf / normal cdf) ──────────

    private val LANCZOS_C = doubleArrayOf(
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
    )
    private const val LANCZOS_G = 7

    fun gamma(x: Double): Double {
        if (x == 0.0) return Double.POSITIVE_INFINITY
        if (x < 0.5) {
            return Math.PI / (Math.sin(Math.PI * x) * gamma(1.0 - x))
        }
        val xx = x - 1.0
        var a = LANCZOS_C[0]
        val t = xx + LANCZOS_G + 0.5
        for (i in 1 until LANCZOS_G + 2) a += LANCZOS_C[i] / (xx + i)
        return sqrt(2 * Math.PI) * Math.pow(t, xx + 0.5) * exp(-t) * a
    }

    fun logGamma(x: Double): Double = ln(abs(gamma(x)))

    fun beta(p: Double, q: Double): Double =
        exp(logGamma(p) + logGamma(q) - logGamma(p + q))

    fun xLogX(x: Double): Double = if (x <= 0.0) 0.0 else x * ln(x)

    // Riemann/framework gauge  zeta(s) = beta(p,q) / log x.
    fun zetaGauge(p: Double, q: Double, x: Double): Double {
        val lx = ln(x)
        return if (abs(lx) < 1e-15) Double.POSITIVE_INFINITY else beta(p, q) / lx
    }

    // Gauss error function (Abramowitz & Stegun 7.1.26).
    fun erf(x: Double): Double {
        val sign = if (x < 0) -1.0 else 1.0
        val z = abs(x)
        val t = 1.0 / (1.0 + 0.3275911 * z)
        val poly = t * (0.254829592 +
                t * (-0.284496736 +
                t * (1.421413741 +
                t * (-1.453152027 +
                t * 1.061405429))))
        return sign * (1.0 - poly * exp(-z * z))
    }

    fun normalCdf(x: Double, mean: Double, sd: Double): Double {
        if (sd <= 0.0) return if (x >= mean) 1.0 else 0.0
        return 0.5 * (1.0 + erf((x - mean) / (sd * sqrt(2.0))))
    }

    // ── Entropy + Manifold (the TupleSpace Xi invariant) ─────────────────────

    private val TOKEN_RE =
        Regex("[A-Za-z0-9_]+|[一-鿿぀-ゟ゠-ヿ]")

    fun tokenize(text: String): List<String> =
        TOKEN_RE.findAll(text).map { it.value }.toList()

    fun shannon(tokens: List<String>): Double {
        if (tokens.isEmpty()) return 0.0
        val freq = HashMap<String, Int>()
        for (t in tokens) freq[t] = (freq[t] ?: 0) + 1
        val total = tokens.size.toDouble()
        var h = 0.0
        for (v in freq.values) {
            val p = v / total
            h -= p * log2(p)
        }
        return h
    }

    // sorted (high->low) probability distribution
    fun distribution(tokens: List<String>): List<Double> {
        if (tokens.isEmpty()) return emptyList()
        val freq = HashMap<String, Int>()
        for (t in tokens) freq[t] = (freq[t] ?: 0) + 1
        val total = tokens.size.toDouble()
        return freq.values.map { it / total }.sortedDescending()
    }

    fun manifoldElement(x: Double): Double {
        if (x <= 1.0) return 1.0
        val xl = xLogX(x)
        return if (abs(xl) < 1e-9) 1.0 else 1.0 / (xl * xl)
    }

    fun manifoldIntegral(probs: List<Double>): Double {
        if (probs.isEmpty()) return 0.0
        var sum = 0.0
        probs.forEachIndexed { i, p -> sum += p * manifoldElement(i + 2.0) }
        return sum
    }

    // Global partial integral manifold entropy invariant Xi.
    fun xi(text: String): Double {
        val tokens = tokenize(text)
        val h = shannon(tokens)
        val m = manifoldIntegral(distribution(tokens))
        val n = tokens.size
        return zetaGauge(h + 1.0, m + 1.0, n + 1.0)
    }

    // ── [1] IQ measurement ───────────────────────────────────────────────────

    data class Observation(
        val modality: String, val label: String, val rho: Double, val z: Double,
        val estimate: Double, val variance: Double, val sigma: Double, val precision: Double
    )

    fun observe(modality: String, z: Double): Observation {
        val m = MODALITIES.getValue(modality)
        return buildObs(modality, m.label, m.rho, z)
    }

    // Build one IQ observation from a standardized reading z at reliability rho.
    fun buildObs(modality: String, label: String, rho: Double, z: Double): Observation {
        val y = POP_MEAN + POP_SD * z / rho
        val varc = (POP_SD * POP_SD) * (1.0 - rho * rho) / (rho * rho)
        return Observation(modality, label, rho, z, y, varc, sqrt(varc), 1.0 / varc)
    }

    // subject: modality-key -> z-score; missing keys are skipped.
    fun observations(subject: Map<String, Double>): List<Observation> =
        MODALITIES.keys.mapNotNull { k -> subject[k]?.let { observe(k, it) } }

    // ── [2] Mirror statistics ────────────────────────────────────────────────

    data class Mirror(
        val n: Int, val pivot: Double, val mirrorSd: Double, val mad: Double,
        val asymmetry: Double, val symmetry: Double
    )

    private fun median(xs: List<Double>): Double {
        val s = xs.sorted()
        val n = s.size
        return if (n % 2 == 1) s[n / 2] else 0.5 * (s[n / 2 - 1] + s[n / 2])
    }

    fun mirrorStats(samples: List<Double>): Mirror {
        if (samples.isEmpty()) return Mirror(0, 0.0, 0.0, 0.0, 0.0, 1.0)
        val pivot = median(samples)
        val mirror = samples.map { 2.0 * pivot - it }         // reflection about pivot
        val folded = samples.map { abs(it - pivot) }
        val mean = samples.sum() / samples.size
        val both = samples + mirror
        val mvar = both.sumOf { (it - pivot) * (it - pivot) } / both.size
        val scale = sqrt(mvar)
        val asym = if (scale < 1e-12) 0.0 else (mean - pivot) / scale
        val symmetry = 1.0 / (1.0 + abs(asym))
        return Mirror(samples.size, pivot, scale, median(folded), asym, symmetry)
    }

    // ── [3] Bayesian estimation ──────────────────────────────────────────────

    data class Posterior(
        val mean: Double, val sd: Double, val ci95: Pair<Double, Double>,
        val bitsGained: Double, val pAboveAverage: Double
    )

    fun bayes(
        obs: List<Observation>, priorMean: Double = POP_MEAN, priorSd: Double = POP_SD
    ): Posterior {
        val priorPrec = 1.0 / (priorSd * priorSd)
        val prec = priorPrec + obs.sumOf { it.precision }
        val weighted = priorPrec * priorMean + obs.sumOf { it.estimate * it.precision }
        val mean = weighted / prec
        val sd = sqrt(1.0 / prec)
        return Posterior(
            mean = mean,
            sd = sd,
            ci95 = Pair(mean - 1.96 * sd, mean + 1.96 * sd),
            bitsGained = log2(priorSd / sd),
            pAboveAverage = 1.0 - normalCdf(POP_MEAN, mean, sd)
        )
    }

    data class BandProb(val band: Band, val p: Double)

    fun bandProbabilities(mean: Double, sd: Double): List<BandProb> =
        BANDS.map { b ->
            val lo = if (b.lo == Double.NEGATIVE_INFINITY) 0.0 else normalCdf(b.lo, mean, sd)
            val hi = if (b.hi == Double.POSITIVE_INFINITY) 1.0 else normalCdf(b.hi, mean, sd)
            BandProb(b, (hi - lo).coerceIn(0.0, 1.0))
        }

    // ── [4] Whispered judge ──────────────────────────────────────────────────

    data class Verdict(
        val bandJa: String, val bandEn: String, val probability: Double,
        val confidence: Double, val whisperEntropy: Double, val xiGate: Double,
        val phrase: String, val distribution: List<BandProb>
    )

    fun whispered(mean: Double, sd: Double, xiGate: Double): Verdict {
        val probs = bandProbabilities(mean, sd)
        val top = probs.maxByOrNull { it.p }!!
        val maxP = top.p
        val ent = -probs.sumOf { if (it.p <= 0.0) 0.0 else it.p * log2(it.p) }
        val gate = abs(xiGate) / (1.0 + abs(xiGate))
        val confidence = (maxP * (0.85 + 0.30 * gate)).coerceIn(0.0, 1.0)
        return Verdict(
            bandJa = top.band.ja, bandEn = top.band.en, probability = maxP,
            confidence = confidence, whisperEntropy = ent, xiGate = xiGate,
            phrase = whisperPhrase(top.band, confidence), distribution = probs
        )
    }

    private fun whisperPhrase(band: Band, confidence: Double): String {
        val strength = when {
            confidence >= 0.60 -> "— と、ほぼ確信を込めて囁く"
            confidence >= 0.40 -> "— と囁く"
            confidence >= 0.25 -> "— と、かすかに囁く"
            else -> "— と、判定を保留しながら囁く"
        }
        return "囁き判定器：この対象者は「${band.ja}（${band.en}）」$strength"
    }

    // Locale-independent formatting so output matches the Ruby reference and
    // never emits comma decimals on non-US-locale devices.
    private fun fmt(template: String, vararg args: Any?): String =
        String.format(Locale.US, template, *args)

    private fun signature(obs: List<Observation>): String =
        obs.joinToString(" ") { fmt("%s:%.2f", it.modality, it.z) }

    // ── Assessment facade ────────────────────────────────────────────────────

    // Optional thermal (infrared + thermometer) context rendered in the report.
    data class Thermal(val ir: Double, val temp: Double, val delta: Double, val xiT: Double)

    data class Assessment(
        val id: String?,
        val obs: List<Observation>,
        val mirror: Mirror,
        val posterior: Posterior,
        val bands: List<BandProb>,
        val xi: Double,
        val verdict: Verdict,
        val meta: Thermal? = null
    ) {
        val iq: Double get() = posterior.mean
    }

    // Assemble an assessment from a prebuilt observation list and Xi gate.
    private fun assemble(
        obs: List<Observation>, xi: Double, id: String?, meta: Thermal? = null
    ): Assessment {
        require(obs.isNotEmpty()) { "観測がありません (no observations)" }
        val posterior = bayes(obs)
        return Assessment(
            id = id,
            obs = obs,
            mirror = mirrorStats(obs.map { it.estimate }),
            posterior = posterior,
            bands = bandProbabilities(posterior.mean, posterior.sd),
            xi = xi,
            verdict = whispered(posterior.mean, posterior.sd, xi),
            meta = meta
        )
    }

    fun assess(subject: Map<String, Double>, id: String? = null): Assessment {
        val obs = observations(subject)
        require(obs.isNotEmpty()) { "生体信号の読み値がありません (no biosignal readings)" }
        return assemble(obs, xi(signature(obs)), id)
    }

    // ── 赤外線センサー + 温度計 モード (thermal / infrared) ────────────────────
    //
    // Estimate IQ from an infrared body-surface reading (IR °C) and an ambient
    // thermometer (°C) by routing them through the GAMMA-FUNCTION global partial
    // integral manifold: the two readings form a 2-point warmth measure whose
    // Shannon entropy H and manifold integral M = Σ p·(1/(x log x)²) couple via
    // the beta gauge (β = Γ·Γ/Γ) into  Ξ_T = β(H+1,M+1)/log 3.  Ξ_T gauges the
    // cognitive z-readouts and gates the whispered judge. Educational proxy only.
    data class ThermalChannel(
        val key: String, val rho: Double, val ref: Double, val sd: Double,
        val kind: String, val label: String
    )

    val THERMAL_CHANNELS: List<ThermalChannel> = listOf(
        ThermalChannel("ir_gradient", 0.30, 12.0, 3.0, "gradient", "IR 体表−環境 温度勾配 Δ"),
        ThermalChannel("ir_emissivity", 0.22, 34.0, 2.5, "emissivity", "IR 体表放射(前頭部) 温"),
        ThermalChannel("metabolic_ratio", 0.25, 0.5, 0.15, "ratio", "代謝比 Δ / T_ambient")
    )

    // Thermal manifold invariant Ξ_T from the (ir, temp) sensor pair.
    fun thermalInvariant(ir: Double, temp: Double): Double {
        val a = maxOf(ir, 1e-6)
        val b = maxOf(temp, 1e-6)
        val s = a + b
        val probs = doubleArrayOf(a / s, b / s)
        val h = -probs.sumOf { if (it <= 0.0) 0.0 else it * log2(it) }
        var m = 0.0
        probs.forEachIndexed { i, q -> m += q * manifoldElement(i + 2.0) }
        return zetaGauge(h + 1.0, m + 1.0, 3.0)   // β(H+1,M+1)/log 3  (gamma gauge)
    }

    fun thermalFeature(kind: String, ir: Double, temp: Double): Double {
        val delta = ir - temp
        return when (kind) {
            "gradient" -> delta
            "emissivity" -> ir
            "ratio" -> delta / maxOf(abs(temp), 1e-6)
            else -> 0.0
        }
    }

    fun thermalChannels(ir: Double, temp: Double): List<Observation> {
        val xiT = thermalInvariant(ir, temp)
        val xiRef = thermalInvariant(35.0, 23.0)   // neutral operating point
        val gain = if (abs(xiRef) < 1e-12) 1.0 else xiT / xiRef
        return THERMAL_CHANNELS.map { c ->
            val f = thermalFeature(c.kind, ir, temp)
            val z = ((f - c.ref) / c.sd) * gain
            buildObs(c.key, c.label, c.rho, z)
        }
    }

    // Full assessment from the infrared sensor + thermometer. `samples` is an
    // optional list of extra (ir, temp) time-readings whose gradient channel is
    // appended to enrich the mirror-statistics sample.
    fun assessThermal(
        ir: Double, temp: Double,
        samples: List<Pair<Double, Double>> = emptyList(), id: String? = "THERMAL"
    ): Assessment {
        val obs = thermalChannels(ir, temp).toMutableList()
        val c0 = THERMAL_CHANNELS[0]
        val ref = thermalInvariant(35.0, 23.0)
        for ((sir, stemp) in samples) {
            val gain = thermalInvariant(sir, stemp) / ref
            val z = ((thermalFeature("gradient", sir, stemp) - c0.ref) / c0.sd) * gain
            obs.add(buildObs("ir_gradient_t", "IR 勾配(時系列サンプル)", c0.rho, z))
        }
        val xi = thermalInvariant(ir, temp)
        return assemble(obs, xi, id, Thermal(ir, temp, ir - temp, xi))
    }

    fun demoThermal(): Pair<Double, Double> = Pair(36.4, 23.0)

    // A built-in demo subject (a cognitively above-average profile).
    fun demoSubject(): LinkedHashMap<String, Double> = linkedMapOf(
        "fmri" to 1.4, "mri" to 1.1, "topography" to 1.6, "dna" to 0.8, "blood" to 0.5
    )

    // Human-readable JA/EN report (mirrors Bada::IQ::Assessment#report).
    fun report(a: Assessment): String {
        val p = a.posterior
        val sb = StringBuilder()
        sb.appendLine("═══════════════════════════════════════════════")
        sb.appendLine(" Bada::IQ 対象者 知能評価レポート")
        if (a.id != null) sb.appendLine("  対象者 ID: ${a.id}")
        sb.appendLine("═══════════════════════════════════════════════")
        val t = a.meta
        if (t != null) {
            sb.appendLine()
            sb.appendLine("【0】赤外線センサー + 温度計")
            sb.appendLine("  ガンマ関数 大域的部分積分多様体")
            sb.appendLine(fmt("  赤外線 IR体表温  : %.2f ℃", t.ir))
            sb.appendLine(fmt("  温度計 環境温    : %.2f ℃", t.temp))
            sb.appendLine(fmt("  体表-環境勾配 Δ  : %+.2f ℃", t.delta))
            sb.appendLine(fmt("  多様体不変量 Ξ_T : %.4f  (β(H+1,M+1)/log 3)", t.xiT))
        }
        sb.appendLine()
        if (t != null) {
            sb.appendLine("【1】IQ 計測 — 赤外線/温度計 サーマルチャネル")
        } else {
            sb.appendLine("【1】生体信号 IQ 計測")
            sb.appendLine("  fMRI/MRI/脳トポグラフィ/DNA/血液")
        }
        for (o in a.obs) {
            sb.appendLine(
                fmt("  ・%-22s z=%+.2f ρ=%.2f → IQ %.1f (σ%.1f)",
                    o.label, o.z, o.rho, o.estimate, o.sigma)
            )
        }
        sb.appendLine()
        sb.appendLine("【2】ミラー統計 (mirror statistics)")
        val m = a.mirror
        sb.appendLine(fmt("  中央枢軸 pivot   : %.2f", m.pivot))
        sb.appendLine(fmt("  ミラー標準偏差   : %.2f", m.mirrorSd))
        sb.appendLine(fmt("  MAD ロバスト尺度 : %.2f", m.mad))
        sb.appendLine(fmt("  反射非対称度     : %+.3f", m.asymmetry))
        sb.appendLine(fmt("  対称スコア       : %.3f (1.0=完全対称)", m.symmetry))
        sb.appendLine()
        sb.appendLine("【3】ベイズ推定 (Bayesian) 事前 N(100,15²)")
        sb.appendLine(fmt("  事後平均 IQ      : %.1f", p.mean))
        sb.appendLine(fmt("  事後標準偏差     : %.2f", p.sd))
        sb.appendLine(fmt("  95%%信用区間      : [%.1f, %.1f]", p.ci95.first, p.ci95.second))
        sb.appendLine(fmt("  平均超過確率     : %.1f%%", 100.0 * p.pAboveAverage))
        sb.appendLine(fmt("  事前比 情報利得  : %.2f bits", p.bitsGained))
        sb.appendLine()
        sb.appendLine("【4】ウィスパード判定器 — Ξ 不変量ゲート")
        sb.appendLine(fmt("  TupleSpace Ξ     : %.4f", a.xi))
        sb.appendLine(fmt("  確信度           : %.1f%%", 100.0 * a.verdict.confidence))
        sb.appendLine("  バンド分布:")
        for (b in a.bands) {
            val bar = "█".repeat((b.p * 24).toInt())
            sb.appendLine(
                fmt("   %-20s %5.1f%% %s", "${b.band.ja}(${b.band.en})", 100.0 * b.p, bar)
            )
        }
        sb.appendLine()
        sb.appendLine("  ${a.verdict.phrase}")
        sb.appendLine()
        sb.appendLine("───────────────────────────────────────────────")
        sb.appendLine(
            fmt(" 総合判定 IQ ≈ %.0f  [ %s / %s ]", a.iq, a.verdict.bandJa, a.verdict.bandEn)
        )
        sb.appendLine(" ※ 教育的モデルであり医療診断ではありません")
        sb.appendLine("    (not a medical diagnosis)")
        sb.append("───────────────────────────────────────────────")
        return sb.toString()
    }
}
