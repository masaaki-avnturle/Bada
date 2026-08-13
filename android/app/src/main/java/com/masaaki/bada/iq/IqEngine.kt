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

    // The Bada-language VM, loaded with the .bada engine libraries (shipped as
    // Android assets special.bada + iq.bada). The whole numeric core below runs
    // *through this VM*, so the app is built on the Bada-language library.
    private var vm: BadaVM.VM? = null

    fun isVmReady(): Boolean = vm != null

    fun initVm(specialSrc: String, iqSrc: String) {
        vm = BadaVM.VM().load(specialSrc).load(iqSrc)
    }

    private fun requireVm(): BadaVM.VM =
        vm ?: throw IllegalStateException(
            "Bada VM 未初期化: IqEngine.initVm(special.bada, iq.bada) を呼んでください"
        )

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

    // Build one IQ observation — computed by the Bada library (observe_estimate
    // / observe_variance).
    fun buildObs(modality: String, label: String, rho: Double, z: Double): Observation {
        val v = requireVm()
        val y = v.callNum("observe_estimate", listOf(rho, z))
        val varc = v.callNum("observe_variance", listOf(rho))
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

    // Gaussian conjugate fusion — computed by the Bada library (bayes_mean /
    // bayes_sd / bayes_bits over the estimate & precision arrays).
    fun bayes(
        obs: List<Observation>, priorMean: Double = POP_MEAN, priorSd: Double = POP_SD
    ): Posterior {
        val v = requireVm()
        val estimates: List<Any?> = obs.map { it.estimate }
        val precisions: List<Any?> = obs.map { it.precision }
        val mean = v.callNum("bayes_mean", listOf(estimates, precisions))
        val sd = v.callNum("bayes_sd", listOf(precisions))
        return Posterior(
            mean = mean,
            sd = sd,
            ci95 = Pair(mean - 1.96 * sd, mean + 1.96 * sd),
            bitsGained = v.callNum("bayes_bits", listOf(precisions)),
            pAboveAverage = 1.0 - v.callNum("normal_cdf", listOf(POP_MEAN, mean, sd))
        )
    }

    data class BandProb(val band: Band, val p: Double)

    // Posterior mass in each Wechsler band — computed by the Bada band_prob.
    fun bandProbabilities(mean: Double, sd: Double): List<BandProb> {
        val v = requireVm()
        return BANDS.map { b ->
            val lo = if (b.lo == Double.NEGATIVE_INFINITY) -1.0e9 else b.lo
            val hi = if (b.hi == Double.POSITIVE_INFINITY) 1.0e9 else b.hi
            BandProb(b, v.callNum("band_prob", listOf(lo, hi, mean, sd)))
        }
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
        // confidence gated by Ξ — computed by the Bada whisper_confidence.
        val confidence = requireVm().callNum("whisper_confidence", listOf(maxP, xiGate))
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

    // ── [5] エキスパート分野判定 (whispered expert-domain classifier) ──────────
    data class ExpertDomain(val ja: String, val en: String, val w: List<Double>)

    // weight vectors over the feature order [g, ii, fmri, mri, topo, dna, blood].
    val EXPERT_DOMAINS: List<ExpertDomain> = listOf(
        ExpertDomain("放射線科医・画像診断", "Radiology / imaging", listOf(0.6, 1.2, 0.5, 0.3, 0.4, 0.0, 0.0)),
        ExpertDomain("法医・顔認証・鑑識", "Forensics / face-ID", listOf(0.3, 1.5, 0.4, 0.6, 0.2, 0.0, 0.0)),
        ExpertDomain("生物分類学・博物学", "Taxonomy / naturalist", listOf(0.4, 1.1, 0.2, 0.3, 0.3, 0.6, 0.2)),
        ExpertDomain("数学・理論物理", "Mathematics / theory", listOf(1.4, 0.2, 0.9, 0.2, 0.3, 0.1, 0.0)),
        ExpertDomain("音楽・演奏", "Music / performance", listOf(0.4, 0.5, 0.6, 0.2, 1.1, 0.1, 0.3)),
        ExpertDomain("スポーツ・運動", "Athletics / motor", listOf(0.2, 0.3, 0.3, 0.2, 0.9, 0.2, 1.2)),
        ExpertDomain("言語・通訳", "Linguistics / interpreting", listOf(1.0, 0.4, 0.8, 0.2, 0.7, 0.1, 0.1)),
        ExpertDomain("美術・デザイン", "Visual art / design", listOf(0.5, 0.9, 0.6, 0.9, 0.4, 0.0, 0.2))
    )

    private val EXPERT_FEATURES = listOf("fmri", "mri", "topography", "dna", "blood")

    data class DomainProb(val ja: String, val en: String, val p: Double)
    data class Expertise(
        val individuation: Double, val topJa: String, val topEn: String,
        val probability: Double, val confidence: Double, val phrase: String,
        val distribution: List<DomainProb>
    )

    // From the subject's 個体識別能力 + biosignal profile, whisper the most likely
    // expert field. Available only when all five biosignal modalities are present.
    fun expertise(zmap: Map<String, Double>, iq: Double, xi: Double): Expertise {
        val v = requireVm()
        val g = (iq - POP_MEAN) / POP_SD
        val ii = v.callNum(
            "individuation_ability",
            listOf(zmap.getValue("fmri"), zmap.getValue("mri"), zmap.getValue("topography"))
        )
        val f: List<Any?> = listOf(
            g, ii, zmap.getValue("fmri"), zmap.getValue("mri"),
            zmap.getValue("topography"), zmap.getValue("dna"), zmap.getValue("blood")
        )
        val scores: List<Any?> = EXPERT_DOMAINS.map { v.callNum("dot", listOf(it.w, f)) }
        @Suppress("UNCHECKED_CAST")
        val probs = (v.call("softmax", listOf(scores, 0.6)) as List<*>).map { (it as Double) }
        var topI = 0
        for (i in probs.indices) if (probs[i] > probs[topI]) topI = i
        val top = EXPERT_DOMAINS[topI]
        val maxP = probs[topI]
        val conf = v.callNum("whisper_confidence", listOf(maxP, xi))
        return Expertise(
            individuation = ii, topJa = top.ja, topEn = top.en,
            probability = maxP, confidence = conf, phrase = expertPhrase(top, conf),
            distribution = EXPERT_DOMAINS.indices.map {
                DomainProb(EXPERT_DOMAINS[it].ja, EXPERT_DOMAINS[it].en, probs[it])
            }
        )
    }

    private fun expertPhrase(domain: ExpertDomain, confidence: Double): String {
        val strength = when {
            confidence >= 0.60 -> "— のエキスパートである、とほぼ確信を込めて囁く"
            confidence >= 0.40 -> "— のエキスパートである、と囁く"
            confidence >= 0.25 -> "— の適性がある、とかすかに囁く"
            else -> "— の傾向がある、と判定を保留しながら囁く"
        }
        return "囁き判定器：この対象者は「${domain.ja}（${domain.en}）」$strength"
    }

    // ── Assessment facade ────────────────────────────────────────────────────

    // Optional thermal (infrared + thermometer) context rendered in the report.
    // `derived` = the five biosignal modalities were inferred from the basal-
    // ganglia thermal entropy (tablet mode) rather than measured directly.
    data class Thermal(
        val ir: Double, val temp: Double, val delta: Double, val xiT: Double,
        val derived: Boolean = false
    )

    data class Assessment(
        val id: String?,
        val obs: List<Observation>,
        val mirror: Mirror,
        val posterior: Posterior,
        val bands: List<BandProb>,
        val xi: Double,
        val verdict: Verdict,
        val meta: Thermal? = null,
        val expertise: Expertise? = null
    ) {
        val iq: Double get() = posterior.mean
    }

    // Assemble an assessment from a prebuilt observation list and Xi gate.
    private fun assemble(
        obs: List<Observation>, xi: Double, id: String?, meta: Thermal? = null
    ): Assessment {
        require(obs.isNotEmpty()) { "観測がありません (no observations)" }
        val posterior = bayes(obs)
        val zmap = obs.associate { it.modality to it.z }
        val exp = if (EXPERT_FEATURES.all { zmap.containsKey(it) }) {
            expertise(zmap, posterior.mean, xi)
        } else null
        return Assessment(
            id = id,
            obs = obs,
            mirror = mirrorStats(obs.map { it.estimate }),
            posterior = posterior,
            bands = bandProbabilities(posterior.mean, posterior.sd),
            xi = xi,
            verdict = whispered(posterior.mean, posterior.sd, xi),
            meta = meta,
            expertise = exp
        )
    }

    fun assess(subject: Map<String, Double>, id: String? = null): Assessment {
        val obs = observations(subject)
        require(obs.isNotEmpty()) { "生体信号の読み値がありません (no biosignal readings)" }
        return assemble(obs, signatureXi(obs), id)
    }

    // Biosignal TupleSpace invariant Ξ: host tokenizes the signature and measures
    // (H, M, N); the gamma/beta manifold gauge is the Bada manifold_invariant.
    private fun signatureXi(obs: List<Observation>): Double {
        val tokens = tokenize(signature(obs))
        val h = shannon(tokens)
        val m = manifoldIntegral(distribution(tokens))
        return requireVm().callNum("manifold_invariant", listOf(h, m, tokens.size.toDouble()))
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

    // Thermal manifold invariant Ξ_T — computed by the Bada thermal_invariant
    // (the gamma-function global partial integral manifold).
    fun thermalInvariant(ir: Double, temp: Double): Double =
        requireVm().callNum("thermal_invariant", listOf(ir, temp))

    private fun kindIndex(kind: String): Double = when (kind) {
        "gradient" -> 0.0
        "emissivity" -> 1.0
        else -> 2.0
    }

    // Thermal sub-channels; each z is standardized and manifold-gauged inside the
    // Bada thermal_z.
    fun thermalChannels(ir: Double, temp: Double): List<Observation> {
        val v = requireVm()
        return THERMAL_CHANNELS.map { c ->
            val z = v.callNum("thermal_z", listOf(kindIndex(c.kind), ir, temp, c.ref, c.sd))
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
        val v = requireVm()
        val obs = thermalChannels(ir, temp).toMutableList()
        val c0 = THERMAL_CHANNELS[0]
        for ((sir, stemp) in samples) {
            val z = v.callNum("thermal_z", listOf(0.0, sir, stemp, c0.ref, c0.sd))
            obs.add(buildObs("ir_gradient_t", "IR 勾配(時系列サンプル)", c0.rho, z))
        }
        val xi = thermalInvariant(ir, temp)
        return assemble(obs, xi, id, Thermal(ir, temp, ir - temp, xi))
    }

    // Thermal coupling: how strongly the basal-ganglia thermal entropy predicts
    // each biosignal modality (framework calibration constants).
    val DERIVED_COUPLING: LinkedHashMap<String, Double> = linkedMapOf(
        "fmri" to 1.0, "mri" to 0.5, "topography" to 0.8, "dna" to 0.3, "blood" to 0.9
    )

    // Estimate ALL five biosignal modalities (blood / DNA / fMRI / MRI /
    // topography) from just the tablet's IR + thermometer, via the basal-ganglia
    // thermal entropy, then run the full biosignal assessment.
    fun assessThermalDerived(ir: Double, temp: Double, id: String? = "TABLET-THERMAL"): Assessment {
        val v = requireVm()
        val obs = MODALITIES.keys.map { k ->
            val coeff = DERIVED_COUPLING.getValue(k)
            val z = v.callNum("derived_z", listOf(coeff, ir, temp))
            val m = MODALITIES.getValue(k)
            buildObs(k, "${m.label} (推定)", m.rho, z)
        }
        val bg = v.callNum("bg_thermal_entropy", listOf(ir, temp))
        return assemble(obs, bg, id, Thermal(ir, temp, ir - temp, bg, derived = true))
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
            if (t.derived) {
                sb.appendLine("【0】赤外線+温度計 → 大脳基底核 熱エントロピー")
                sb.appendLine("  ガンマ関数 大域的部分積分多様体 (3点測度)")
            } else {
                sb.appendLine("【0】赤外線センサー + 温度計")
                sb.appendLine("  ガンマ関数 大域的部分積分多様体")
            }
            sb.appendLine(fmt("  赤外線 皮膚温度   : %.2f ℃ (体表/体外)", t.ir))
            sb.appendLine(fmt("  温度計 環境温    : %.2f ℃", t.temp))
            sb.appendLine(fmt("  皮膚-環境勾配 Δ  : %+.2f ℃", t.delta))
            if (t.derived) {
                sb.appendLine(fmt("  大脳基底核 熱H_bg: %.4f  (β(H+1,M+1)/log 4)", t.xiT))
            } else {
                sb.appendLine(fmt("  多様体不変量 Ξ_T : %.4f  (β(H+1,M+1)/log 3)", t.xiT))
            }
        }
        sb.appendLine()
        when {
            t?.derived == true -> {
                sb.appendLine("【1】IQ 計測 — 赤外線/温度計から推定した生体信号")
                sb.appendLine("  血液/DNA/fMRI/MRI/脳トポグラフィ (推定)")
            }
            t != null -> sb.appendLine("【1】IQ 計測 — 赤外線/温度計 サーマルチャネル")
            else -> {
                sb.appendLine("【1】生体信号 IQ 計測")
                sb.appendLine("  fMRI/MRI/脳トポグラフィ/DNA/血液")
            }
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

        val e = a.expertise
        if (e != null) {
            sb.appendLine()
            sb.appendLine("【5】ウィスパード エキスパート分野判定 — 個体識別能力から")
            sb.appendLine(fmt("  個体識別能力 II  : %+.2f", e.individuation))
            sb.appendLine(fmt("  確信度           : %.1f%%", 100.0 * e.confidence))
            sb.appendLine("  分野分布:")
            for (d in e.distribution.sortedByDescending { it.p }) {
                val bar = "█".repeat((d.p * 24).toInt())
                sb.appendLine(fmt("   %-24s %5.1f%% %s", "${d.ja}(${d.en})", 100.0 * d.p, bar))
            }
            sb.appendLine()
            sb.appendLine("  ${e.phrase}")
        }

        sb.appendLine()
        sb.appendLine("───────────────────────────────────────────────")
        sb.appendLine(
            fmt(" 総合判定 IQ ≈ %.0f  [ %s / %s ]", a.iq, a.verdict.bandJa, a.verdict.bandEn)
        )
        if (e != null) sb.appendLine(fmt(" 推定エキスパート分野: %s / %s", e.topJa, e.topEn))
        sb.appendLine(" ※ 教育的モデルであり医療診断ではありません")
        sb.appendLine("    (not a medical diagnosis)")
        sb.append("───────────────────────────────────────────────")
        return sb.toString()
    }
}
