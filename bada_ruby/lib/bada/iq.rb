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
      build_obs(modality, m[:label], m[:rho], z)
    end

    # Build one IQ observation from a standardized reading z at reliability rho.
    #   y   = 100 + 15 z / rho ,   var = 15² (1 − rho²) / rho²
    def build_obs(modality, label, rho, z)
      zf = z.to_f
      y = POP_MEAN + POP_SD * zf / rho
      var = (POP_SD**2) * (1.0 - rho**2) / (rho**2)
      {
        modality: modality,
        label: label,
        rho: rho,
        z: zf,
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
      attr_reader :id, :obs, :mirror, :posterior, :bands, :verdict, :xi, :meta

      # Build an assessment from a subject hash of standardized biosignal
      # readings { id:, fmri:, mri:, topography:, dna:, blood: }.
      def self.from_subject(subject)
        obs = IQ.observations(subject)
        raise ArgumentError, "no biosignal readings given" if obs.empty?
        xi = Bada::Manifold.xi(IQ.signature(obs))
        new(obs, xi: xi, id: subject[:id] || subject["id"])
      end

      # obs: array of observation hashes (see IQ.observe); xi: the TupleSpace
      # invariant used to gate the whispered judge; meta: optional extra context
      # (e.g. the thermal / infrared block) rendered in the report.
      def initialize(obs, xi:, id: nil, meta: {})
        raise ArgumentError, "no observations given" if obs.nil? || obs.empty?
        @obs = obs
        @xi = xi
        @id = id
        @meta = meta
        @mirror    = IQ.mirror_stats(@obs.map { |o| o[:estimate] })
        @posterior = IQ.bayes(@obs)
        @bands     = IQ.band_probabilities(@posterior[:posterior_mean], @posterior[:posterior_sd])
        @verdict   = IQ.whispered(@posterior[:posterior_mean], @posterior[:posterior_sd], xi_gate: @xi)
      end

      # The headline IQ point estimate (Bayesian posterior mean).
      def iq
        @posterior[:posterior_mean]
      end

      def to_h
        {
          id: @id,
          observations: @obs,
          mirror: @mirror,
          posterior: @posterior,
          bands: @bands,
          xi: @xi,
          verdict: @verdict,
          meta: @meta,
          iq: iq
        }
      end

      # Human-readable report (Japanese + English), returned as a String.
      def report
        p = @posterior
        lines = []
        lines << "═══════════════════════════════════════════════════════════════"
        lines << " Bada::IQ  対象者 知能評価レポート / Subject IQ Assessment"
        lines << "  対象者 ID: #{@id}" if @id
        lines << "═══════════════════════════════════════════════════════════════"

        if @meta[:thermal]
          t = @meta[:thermal]
          lines << ""
          lines << "【0】赤外線センサー + 温度計 — ガンマ関数 大域的部分積分多様体"
          lines << format("   赤外線 IR体表温  : %.2f ℃", t[:ir])
          lines << format("   温度計 環境温    : %.2f ℃", t[:temp])
          lines << format("   体表-環境勾配 Δ  : %+.2f ℃", t[:delta])
          lines << format("   多様体不変量 Ξ_T : %.4f  (β(H+1,M+1)/log 3)", t[:xi_t])
        end

        lines << ""
        lines << if @meta[:thermal]
                   "【1】IQ 計測 — 赤外線/温度計 由来 サーマルチャネル"
                 else
                   "【1】生体信号 IQ 計測 — fMRI/MRI/脳トポグラフィ/DNA/血液"
                 end
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
      Assessment.from_subject(subject)
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

    # ── 赤外線センサー + 温度計 モード (thermal / infrared) ───────────────────
    #
    # Estimate IQ from just two physical sensors — an infrared body-surface
    # reading (IR °C) and an ambient thermometer (°C) — by routing them through
    # the GAMMA-FUNCTION global partial integral manifold.
    #
    # The two readings form a 2-point warmth measure p on the manifold; its
    # Shannon entropy H and the global partial integral M = Σ p·(1/(x log x)²)
    # are coupled through the beta/zeta gauge (β = Γ·Γ/Γ) into a thermal manifold
    # invariant
    #
    #   Ξ_T = β(H+1, M+1) / log 3            (N = 2 sensor points, log(N+1)=log 3)
    #
    # Ξ_T then *gauges* the standardized cognitive readouts derived from the
    # body–ambient gradient, and gates the whispered judge. Physiologically this
    # is an educational proxy for cerebral metabolic throughput (a warmer head
    # relative to ambient). NOT a medical measurement.
    THERMAL_CHANNELS = [
      { key: :ir_gradient,     rho: 0.30, ref: 12.0, sd: 3.0,  kind: :gradient,
        label: "IR 体表−環境 温度勾配 Δ" },
      { key: :ir_emissivity,   rho: 0.22, ref: 34.0, sd: 2.5,  kind: :emissivity,
        label: "IR 体表放射(前頭部) 温" },
      { key: :metabolic_ratio, rho: 0.25, ref: 0.5,  sd: 0.15, kind: :ratio,
        label: "代謝比 Δ / T_ambient" }
    ].freeze

    # Thermal manifold invariant Ξ_T from the (ir, temp) sensor pair.
    def thermal_invariant(ir, temp)
      a = [ir.to_f, 1e-6].max
      b = [temp.to_f, 1e-6].max
      s = a + b
      probs = [a / s, b / s]
      h = -probs.sum { |q| q <= 0 ? 0.0 : q * Math.log2(q) }
      m = probs.each_with_index.sum { |q, i| q * Manifold.element(i + 2.0) }
      Special.zeta_gauge(h + 1.0, m + 1.0, 3.0)  # β(H+1,M+1)/log 3  (gamma gauge)
    end

    # Raw feature value for a thermal channel from the (ir, temp) pair.
    def thermal_feature(kind, ir, temp)
      delta = ir.to_f - temp.to_f
      case kind
      when :gradient   then delta
      when :emissivity then ir.to_f
      when :ratio      then delta / [temp.to_f.abs, 1e-6].max
      else 0.0
      end
    end

    # The thermal sub-channel observations from one (ir, temp) reading, each
    # standardized then curved by the manifold gauge Ξ_T / Ξ_ref.
    def thermal_channels(ir, temp)
      xi_t = thermal_invariant(ir, temp)
      xi_ref = thermal_invariant(35.0, 23.0)   # neutral operating point
      gain = xi_ref.abs < 1e-12 ? 1.0 : xi_t / xi_ref
      THERMAL_CHANNELS.map do |c|
        f = thermal_feature(c[:kind], ir, temp)
        z = ((f - c[:ref]) / c[:sd]) * gain     # manifold-gauged cognitive z
        build_obs(c[:key], c[:label], c[:rho], z)
      end
    end

    # Full assessment from the infrared sensor + thermometer alone. Optional
    # `samples` is a list of extra [ir, temp] time-readings whose gradient
    # channel is appended (giving the mirror statistics a richer sample).
    def assess_thermal(ir, temp, samples: [], id: "THERMAL")
      obs = thermal_channels(ir, temp)
      Array(samples).each do |pair|
        sir, stemp = pair
        next if sir.nil? || stemp.nil?
        c = THERMAL_CHANNELS[0] # gradient channel per time-sample
        xi_t = thermal_invariant(sir, stemp)
        gain = xi_t / thermal_invariant(35.0, 23.0)
        z = ((thermal_feature(:gradient, sir, stemp) - c[:ref]) / c[:sd]) * gain
        obs << build_obs(:ir_gradient_t, "IR 勾配(時系列サンプル)", c[:rho], z)
      end
      xi = thermal_invariant(ir, temp)
      Assessment.new(obs, xi: xi, id: id,
                     meta: { thermal: { ir: ir.to_f, temp: temp.to_f,
                                        delta: ir.to_f - temp.to_f, xi_t: xi } })
    end

    # A built-in demo sensor reading (warm forehead vs cool room).
    def demo_thermal
      { ir: 36.4, temp: 23.0 }
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
