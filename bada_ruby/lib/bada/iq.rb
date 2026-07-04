# frozen_string_literal: true

require_relative "special"
require_relative "entropy"
require_relative "manifold"

module Bada
  # Bada::IQ — subject intelligence (IQ) assessment on the Yamaguchi /
  # TupleSpace framework, built on top of the earlier bio-medical Bada apps.
  #
  #   fMRI / MRI / 脳トポグラフィ(EEG) / DNA解析 / 血液検査
  #        ↓ (per-modality standardized biosignal readings)
  #   [1] IQ measurement      — regress each biosignal onto the IQ scale
  #   [2] Mirror statistics   — reflection-symmetric robust summary (ミラー統計)
  #   [3] Bayesian estimation — Gaussian conjugate fusion with a population
  #                             prior N(100, 15²)  (ベイズ推定)
  #   [4] Whispered judge     — a soft, hedged band verdict gated by the
  #                             TupleSpace Ξ invariant  (ウィスパード判定器)
  #
  # ─────────────────────────────────────────────────────────────────────────
  #  SAFETY / 免責:  This is an educational / theoretical model of the
  #  Yamaguchi framework. It is NOT a medical device, NOT a diagnosis, and the
  #  reliability constants below are framework calibration values — not
  #  clinical measurements. Do not use for any medical decision.
  # ─────────────────────────────────────────────────────────────────────────
  #
  # Everything is pure stdlib Ruby and reuses Bada::Special (β/Γ/Φ),
  # Bada::Entropy and Bada::Manifold (the Ξ invariant).
  module IQ
    module_function

    # Population IQ scale (Wechsler gauge): mean 100, sd 15.
    POP_MEAN = 100.0
    POP_SD   = 15.0

    # The five biosignal modalities of the earlier Bada bio-medical apps, each
    # with a reliability ρ = correlation of that biosignal with general
    # intelligence g. (Framework calibration constants — see SAFETY note.)
    MODALITIES = {
      fmri:       { rho: 0.42, key: :fmri,       label: "fMRI 機能的結合効率" },
      mri:        { rho: 0.40, key: :mri,        label: "MRI 灰白質体積・皮質厚" },
      topography: { rho: 0.38, key: :topography, label: "脳トポグラフィ EEG(神経伝導速度)" },
      dna:        { rho: 0.30, key: :dna,        label: "DNA 認知ポリジェニックスコア" },
      blood:      { rho: 0.20, key: :blood,      label: "血液バイオマーカー(BDNF・代謝・炎症)" }
    }.freeze

    # Wechsler (WAIS) classification bands: [low, high) on the IQ scale.
    BANDS = [
      { lo: -Float::INFINITY, hi:  70.0, ja: "知的発達境界域以下", en: "Extremely Low" },
      { lo:  70.0,            hi:  80.0, ja: "境界域",             en: "Borderline" },
      { lo:  80.0,            hi:  90.0, ja: "平均の下",           en: "Low Average" },
      { lo:  90.0,            hi: 110.0, ja: "平均",               en: "Average" },
      { lo: 110.0,            hi: 120.0, ja: "平均の上",           en: "High Average" },
      { lo: 120.0,            hi: 130.0, ja: "優秀",               en: "Superior" },
      { lo: 130.0,            hi: Float::INFINITY, ja: "非常に優秀", en: "Very Superior" }
    ].freeze

    # ── [1] IQ measurement ──────────────────────────────────────────────────
    #
    # Each modality supplies a *standardized* biosignal reading z (the subject's
    # value in population-sd units, positive = cognitively favourable). Under
    # the bivariate-normal model  (IQ, biosignal) with correlation ρ, an
    # *unbiased* IQ readout from that biosignal and its measurement variance are
    #
    #   y   = 100 + 15 · z / ρ                     (unbiased estimator of θ)
    #   σ²  = 15² · (1 − ρ²) / ρ²                   (its variance, IQ² units)
    #
    # so a high-reliability biosignal (ρ→1) gives a tight, trustworthy readout
    # and a low-reliability one (ρ→0) a wide, near-useless one. Combining them
    # is left to the Bayesian stage (no double counting of the prior here).
    def observe(modality, z)
      m = MODALITIES.fetch(modality)
      rho = m[:rho]
      y = POP_MEAN + POP_SD * z.to_f / rho
      var = (POP_SD**2) * (1.0 - rho**2) / (rho**2)
      {
        modality: modality,
        label: m[:label],
        rho: rho,
        z: z.to_f,
        estimate: y,   # unbiased single-modality IQ readout
        variance: var, # measurement variance (IQ²)
        sigma: Math.sqrt(var),
        precision: 1.0 / var
      }
    end

    # Turn a subject hash {fmri: z, mri: z, ...} into the list of biosignal
    # observations. Missing / nil modalities are skipped.
    def observations(subject)
      MODALITIES.keys.filter_map do |k|
        z = subject[k] || subject[k.to_s]
        z.nil? ? nil : observe(k, z)
      end
    end

    # ── [2] Mirror statistics (ミラー統計) ──────────────────────────────────
    #
    # Reflect the sample about its median pivot p:   x' = 2p − x   (the real-axis
    # conjugation z ↦ z̄ of the framework's complex-rotation symmetry). The
    # mirror statistics summarize the sample together with its reflection, giving
    # a symmetry-aware, outlier-resistant description of the per-modality IQ
    # readouts.
    def mirror_stats(samples)
      xs = Array(samples).map(&:to_f)
      return empty_mirror if xs.empty?

      pivot = median(xs)
      mirror = xs.map { |x| 2.0 * pivot - x }     # reflection about the pivot
      folded = xs.map { |x| (x - pivot).abs }     # |deviation| = fold onto the axis

      mean = xs.sum / xs.length
      # variance of the symmetrized set  xs ∪ mirror  (centered at the pivot):
      both = xs + mirror
      mvar = both.sum { |x| (x - pivot)**2 } / both.length
      scale = Math.sqrt(mvar)

      # signed reflection asymmetry: how far the mean sits from the pivot,
      # in scale units. 0 ⇒ perfectly mirror-symmetric.
      asym = scale < 1e-12 ? 0.0 : (mean - pivot) / scale
      symmetry = 1.0 / (1.0 + asym.abs)           # in (0,1], 1 = symmetric

      {
        n: xs.length,
        pivot: pivot,                 # median (mirror-balanced center)
        mirror_mean: pivot,           # (mean(x)+mean(x'))/2 ≡ pivot by reflection
        mirror_sd: scale,             # sd of the symmetrized sample
        mad: median(folded),          # median absolute deviation (robust scale)
        asymmetry: asym,              # signed reflection skew
        symmetry: symmetry,           # symmetry score in (0,1]
        reflected: mirror
      }
    end

    # ── [3] Bayesian estimation (ベイズ推定) ────────────────────────────────
    #
    # Gaussian conjugate fusion. Prior θ ~ N(μ₀, τ₀²) is the population IQ
    # distribution N(100, 15²); each biosignal observation yₘ ~ N(θ, σₘ²) is an
    # independent noisy measurement. The posterior is N(μ*, σ*²) with
    #
    #   1/σ*² = 1/τ₀² + Σ 1/σₘ²
    #   μ*    = σ*² · ( μ₀/τ₀² + Σ yₘ/σₘ² )
    #
    # Precision adds; the estimate is the precision-weighted mean of the prior
    # and every biosignal readout.
    def bayes(obs, prior_mean: POP_MEAN, prior_sd: POP_SD)
      prior_prec = 1.0 / (prior_sd**2)
      prec = prior_prec + obs.sum { |o| o[:precision] }
      weighted = prior_prec * prior_mean + obs.sum { |o| o[:estimate] * o[:precision] }
      mean = weighted / prec
      var = 1.0 / prec
      sd = Math.sqrt(var)
      {
        prior_mean: prior_mean,
        prior_sd: prior_sd,
        posterior_mean: mean,
        posterior_sd: sd,
        posterior_var: var,
        # 95% credible interval (±1.96σ):
        ci95: [mean - 1.96 * sd, mean + 1.96 * sd],
        # information gained over the prior, in bits (Gaussian KL / entropy drop):
        bits_gained: Math.log2(prior_sd / sd),
        p_above_average: 1.0 - Special.normal_cdf(POP_MEAN, mean: mean, sd: sd)
      }
    end

    # Posterior probability mass in each Wechsler band.
    def band_probabilities(mean, sd)
      BANDS.map do |b|
        lo = b[:lo] == -Float::INFINITY ? 0.0 : Special.normal_cdf(b[:lo], mean: mean, sd: sd)
        hi = b[:hi] ==  Float::INFINITY ? 1.0 : Special.normal_cdf(b[:hi], mean: mean, sd: sd)
        { band: b, p: (hi - lo).clamp(0.0, 1.0) }
      end
    end

    # ── [4] Whispered judge (ウィスパード判定器) ────────────────────────────
    #
    # A *whispered* verdict: soft, hedged, and confidence-gated rather than
    # asserted. It picks the most probable band from the Bayesian posterior,
    # then tempers its own certainty by
    #   • the band-distribution entropy (spread across bands ⇒ less certain), and
    #   • the TupleSpace Ξ invariant of the subject's biosignal signature (the
    #     framework's β(H+1,M+1)/log(N+1) gate).
    # The louder the agreement, the more it "whispers" a definite band.
    def whispered(mean, sd, xi_gate: 1.0)
      probs = band_probabilities(mean, sd)
      top = probs.max_by { |x| x[:p] }
      max_p = top[:p]

      # band-distribution entropy (reported as the spread of the whisper):
      ent = -probs.sum { |x| x[:p] <= 0 ? 0.0 : x[:p] * Math.log2(x[:p]) }

      # confidence is carried mainly by the top band's mass, with the TupleSpace
      # Ξ invariant acting as a small ± modulation (the framework gate). Band
      # granularity (10-pt bands vs an ~11-pt posterior sd) caps a single band
      # near ~0.5, so the whisper stays honestly hedged.
      gate = (xi_gate.abs / (1.0 + xi_gate.abs)) # squash Ξ into (0,1)
      confidence = (max_p * (0.85 + 0.30 * gate)).clamp(0.0, 1.0)

      {
        band_ja: top[:band][:ja],
        band_en: top[:band][:en],
        probability: max_p,
        confidence: confidence,
        whisper_entropy: ent,
        xi_gate: xi_gate,
        phrase: whisper_phrase(top[:band], confidence),
        distribution: probs
      }
    end

    # Map a confidence level to the strength of the whisper (囁きの強さ).
    def whisper_phrase(band, confidence)
      strength =
        if    confidence >= 0.60 then "— と、ほぼ確信を込めて囁く"
        elsif confidence >= 0.40 then "— と囁く"
        elsif confidence >= 0.25 then "— と、かすかに囁く"
        else                          "— と、判定を保留しながら囁く"
        end
      "囁き判定器：この対象者は「#{band[:ja]}（#{band[:en]}）」#{strength}"
    end

    # A short biosignal-signature string whose Ξ invariant gates the whisper.
    def signature(obs)
      obs.map { |o| format("%s:%.2f", o[:modality], o[:z]) }.join(" ")
    end

    # ── Assessment facade ───────────────────────────────────────────────────
    #
    # Runs the full pipeline for a subject and renders a report, in the style of
    # Bada::Thurston / Bada::InfoEngine.
    class Assessment
      attr_reader :subject, :obs, :mirror, :posterior, :bands, :verdict, :xi

      # subject: { id:, fmri:, mri:, topography:, dna:, blood: } — each biosignal
      # value is a standardized (z-score) reading; any modality may be omitted.
      def initialize(subject)
        @subject = subject
        @obs = IQ.observations(subject)
        raise ArgumentError, "no biosignal readings given" if @obs.empty?

        @mirror    = IQ.mirror_stats(@obs.map { |o| o[:estimate] })
        @posterior = IQ.bayes(@obs)
        @bands     = IQ.band_probabilities(@posterior[:posterior_mean], @posterior[:posterior_sd])
        @xi        = Bada::Manifold.xi(IQ.signature(@obs))
        @verdict   = IQ.whispered(@posterior[:posterior_mean], @posterior[:posterior_sd], xi_gate: @xi)
      end

      # The headline IQ point estimate (Bayesian posterior mean).
      def iq
        @posterior[:posterior_mean]
      end

      def to_h
        {
          id: @subject[:id] || @subject["id"],
          observations: @obs,
          mirror: @mirror,
          posterior: @posterior,
          bands: @bands,
          xi: @xi,
          verdict: @verdict,
          iq: iq
        }
      end

      # Human-readable report (Japanese + English), returned as a String.
      def report
        p = @posterior
        lines = []
        lines << "═══════════════════════════════════════════════════════════════"
        lines << " Bada::IQ  対象者 知能評価レポート / Subject IQ Assessment"
        id = @subject[:id] || @subject["id"]
        lines << "  対象者 ID: #{id}" if id
        lines << "═══════════════════════════════════════════════════════════════"

        lines << ""
        lines << "【1】生体信号 IQ 計測 — fMRI/MRI/脳トポグラフィ/DNA/血液"
        lines << format("   %-30s %6s %8s %8s %8s", "modality", "z", "ρ", "IQ推定", "σ")
        @obs.each do |o|
          lines << format("   %-30s %+6.2f %8.2f %8.1f %8.1f",
                          o[:label], o[:z], o[:rho], o[:estimate], o[:sigma])
        end

        lines << ""
        lines << "【2】ミラー統計 (mirror statistics) — 反射対称ロバスト要約"
        m = @mirror
        lines << format("   中央枢軸(pivot)  : %.2f", m[:pivot])
        lines << format("   ミラー標準偏差   : %.2f", m[:mirror_sd])
        lines << format("   MAD(ロバスト尺度): %.2f", m[:mad])
        lines << format("   反射非対称度     : %+.3f", m[:asymmetry])
        lines << format("   対称スコア       : %.3f  (1.0 = 完全対称)", m[:symmetry])

        lines << ""
        lines << "【3】ベイズ推定 (Bayesian estimation) — 母集団事前 N(100,15²)"
        lines << format("   事後平均 IQ      : %.1f", p[:posterior_mean])
        lines << format("   事後標準偏差     : %.2f", p[:posterior_sd])
        lines << format("   95%%信用区間      : [%.1f, %.1f]", p[:ci95][0], p[:ci95][1])
        lines << format("   平均超過確率     : %.1f%%", 100.0 * p[:p_above_average])
        lines << format("   事前比 情報利得  : %.2f bits", p[:bits_gained])

        lines << ""
        lines << "【4】ウィスパード判定器 (whispered judge) — Ξ 不変量ゲート"
        lines << format("   TupleSpace Ξ     : %.4f", @xi)
        lines << format("   確信度(confidence): %.1f%%", 100.0 * @verdict[:confidence])
        lines << "   バンド分布:"
        @bands.each do |b|
          bar = "█" * (b[:p] * 40).round
          lines << format("     %-22s %5.1f%% %s", "#{b[:band][:ja]}(#{b[:band][:en]})",
                          100.0 * b[:p], bar)
        end
        lines << ""
        lines << "   #{@verdict[:phrase]}"

        lines << ""
        lines << "───────────────────────────────────────────────────────────────"
        lines << format(" 総合判定 IQ ≈ %.0f  [ %s / %s ]",
                        iq, @verdict[:band_ja], @verdict[:band_en])
        lines << " ※ 本レポートは山口フレームワークの教育的モデルであり、"
        lines << "    医療診断ではありません (not a medical diagnosis)。"
        lines << "───────────────────────────────────────────────────────────────"
        lines.join("\n")
      end
    end

    # Convenience: assess a subject hash and return the Assessment.
    def assess(subject)
      Assessment.new(subject)
    end

    # A built-in demo subject (a cognitively above-average profile) so the CLI
    # can be run with no data file.
    def demo_subject
      {
        id: "DEMO-0001",
        fmri: 1.4,        # strong functional connectivity
        mri: 1.1,         # above-average gray-matter volume
        topography: 1.6,  # fast neural conduction (EEG)
        dna: 0.8,         # favourable cognitive polygenic score
        blood: 0.5        # healthy metabolic / BDNF profile
      }
    end

    # ── internal helpers ────────────────────────────────────────────────────
    def median(xs)
      s = xs.sort
      n = s.length
      n.odd? ? s[n / 2] : 0.5 * (s[n / 2 - 1] + s[n / 2])
    end

    def empty_mirror
      { n: 0, pivot: 0.0, mirror_mean: 0.0, mirror_sd: 0.0, mad: 0.0,
        asymmetry: 0.0, symmetry: 1.0, reflected: [] }
    end
  end
end
