# frozen_string_literal: true

require_relative "special"
require_relative "entropy"
require_relative "manifold"
require_relative "lang"

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
    # The Bada-language VM, loaded with the .bada engine libraries. The entire
    # numeric core below runs *through this VM* — i.e. the app is built on the
    # Bada-language library (lib/bada_src/*.bada), not on hand-written Ruby math.
    BADA_SRC_DIR = File.expand_path("../bada_src", __dir__)

    def vm
      @vm ||= begin
        v = Bada::Lang::VM.new
        v.load(File.read(File.join(BADA_SRC_DIR, "special.bada"), encoding: "UTF-8"))
        v.load(File.read(File.join(BADA_SRC_DIR, "iq.bada"), encoding: "UTF-8"))
        v
      end
    end

    def observe(modality, z)
      m = MODALITIES.fetch(modality)
      build_obs(modality, m[:label], m[:rho], z)
    end

    # Build one IQ observation from a standardized reading z at reliability rho.
    # Computed by the Bada library:  observe_estimate / observe_variance.
    def build_obs(modality, label, rho, z)
      zf = z.to_f
      y = vm.call("observe_estimate", [rho, zf])
      var = vm.call("observe_variance", [rho])
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
    # Gaussian conjugate fusion — computed by the Bada library (bayes_mean /
    # bayes_sd / bayes_bits over the estimate & precision arrays; prior N(100,15²)).
    def bayes(obs, prior_mean: POP_MEAN, prior_sd: POP_SD)
      estimates = obs.map { |o| o[:estimate] }
      precisions = obs.map { |o| o[:precision] }
      mean = vm.call("bayes_mean", [estimates, precisions])
      sd = vm.call("bayes_sd", [precisions])
      {
        prior_mean: prior_mean,
        prior_sd: prior_sd,
        posterior_mean: mean,
        posterior_sd: sd,
        posterior_var: sd * sd,
        # 95% credible interval (±1.96σ):
        ci95: [mean - 1.96 * sd, mean + 1.96 * sd],
        # information gained over the prior, in bits (Gaussian KL / entropy drop):
        bits_gained: vm.call("bayes_bits", [precisions]),
        p_above_average: 1.0 - vm.call("normal_cdf", [POP_MEAN, mean, sd])
      }
    end

    # Posterior probability mass in each Wechsler band.
    # Posterior mass in each Wechsler band — computed by the Bada band_prob.
    def band_probabilities(mean, sd)
      BANDS.map do |b|
        lo = b[:lo] == -Float::INFINITY ? -1.0e9 : b[:lo]
        hi = b[:hi] ==  Float::INFINITY ?  1.0e9 : b[:hi]
        { band: b, p: vm.call("band_prob", [lo, hi, mean, sd]) }
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
      # confidence carried by the top-band mass, gated by Ξ (Bada whisper_confidence).
      confidence = vm.call("whisper_confidence", [max_p, xi_gate])

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

    # Biosignal TupleSpace invariant Ξ: host tokenizes the signature and measures
    # (H, M, N); the gamma/beta manifold gauge itself is the Bada manifold_invariant.
    def signature_xi(obs)
      tokens = Bada::Entropy.tokenize(signature(obs))
      h = Bada::Entropy.shannon(tokens)
      m = Bada::Manifold.integral(Bada::Entropy.distribution(tokens))
      vm.call("manifold_invariant", [h, m, tokens.length.to_f])
    end

    # ── [5] エキスパート分野判定 (whispered expert-domain classifier) ─────────
    #
    # From the observed subject's 個体識別能力 (individual-identification /
    # perceptual-individuation ability) and the biosignal profile, whisper which
    # field the person is most likely an expert in. Each domain has a weight
    # vector over the feature order  [g, ii, fmri, mri, topo, dna, blood]:
    #   g   = (IQ − 100)/15         general intelligence
    #   ii  = individuation ability (fusiform/temporal perceptual expertise)
    # (Framework calibration constants — an educational model, not a real
    #  aptitude test.)
    EXPERT_DOMAINS = [
      { ja: "放射線科医・画像診断", en: "Radiology / imaging",
        w: [0.6, 1.2, 0.5, 0.3, 0.4, 0.0, 0.0] },
      { ja: "法医・顔認証・鑑識",   en: "Forensics / face-ID",
        w: [0.3, 1.5, 0.4, 0.6, 0.2, 0.0, 0.0] },
      { ja: "生物分類学・博物学",   en: "Taxonomy / naturalist",
        w: [0.4, 1.1, 0.2, 0.3, 0.3, 0.6, 0.2] },
      { ja: "数学・理論物理",       en: "Mathematics / theory",
        w: [1.4, 0.2, 0.9, 0.2, 0.3, 0.1, 0.0] },
      { ja: "音楽・演奏",           en: "Music / performance",
        w: [0.4, 0.5, 0.6, 0.2, 1.1, 0.1, 0.3] },
      { ja: "スポーツ・運動",       en: "Athletics / motor",
        w: [0.2, 0.3, 0.3, 0.2, 0.9, 0.2, 1.2] },
      { ja: "言語・通訳",           en: "Linguistics / interpreting",
        w: [1.0, 0.4, 0.8, 0.2, 0.7, 0.1, 0.1] },
      { ja: "美術・デザイン",       en: "Visual art / design",
        w: [0.5, 0.9, 0.6, 0.9, 0.4, 0.0, 0.2] }
    ].freeze

    EXPERT_FEATURES = %i[fmri mri topography dna blood].freeze

    # zmap: { fmri:, mri:, topography:, dna:, blood: } of z-scores; iq: posterior
    # mean; xi: the TupleSpace invariant that gates the whisper.
    def expertise(zmap, iq, xi)
      g = (iq - POP_MEAN) / POP_SD
      ii = vm.call("individuation_ability", [zmap[:fmri], zmap[:mri], zmap[:topography]])
      f = [g, ii, zmap[:fmri], zmap[:mri], zmap[:topography], zmap[:dna], zmap[:blood]]
      scores = EXPERT_DOMAINS.map { |d| vm.call("dot", [d[:w], f]) }
      probs = vm.call("softmax", [scores, 0.6])
      top_i = probs.each_index.max_by { |i| probs[i] }
      top = EXPERT_DOMAINS[top_i]
      max_p = probs[top_i]
      conf = vm.call("whisper_confidence", [max_p, xi])
      {
        individuation: ii,
        top_ja: top[:ja],
        top_en: top[:en],
        probability: max_p,
        confidence: conf,
        distribution: EXPERT_DOMAINS.each_index.map do |i|
          { ja: EXPERT_DOMAINS[i][:ja], en: EXPERT_DOMAINS[i][:en], p: probs[i] }
        end,
        phrase: expert_phrase(top, conf)
      }
    end

    def expert_phrase(domain, confidence)
      strength =
        if    confidence >= 0.60 then "— のエキスパートである、とほぼ確信を込めて囁く"
        elsif confidence >= 0.40 then "— のエキスパートである、と囁く"
        elsif confidence >= 0.25 then "— の適性がある、とかすかに囁く"
        else                          "— の傾向がある、と判定を保留しながら囁く"
        end
      "囁き判定器：この対象者は「#{domain[:ja]}（#{domain[:en]}）」#{strength}"
    end

    # ── Assessment facade ───────────────────────────────────────────────────
    #
    # Runs the full pipeline for a subject and renders a report, in the style of
    # Bada::Thurston / Bada::InfoEngine.
    class Assessment
      attr_reader :id, :obs, :mirror, :posterior, :bands, :verdict, :xi, :meta, :expertise

      # Build an assessment from a subject hash of standardized biosignal
      # readings { id:, fmri:, mri:, topography:, dna:, blood: }.
      def self.from_subject(subject)
        obs = IQ.observations(subject)
        raise ArgumentError, "no biosignal readings given" if obs.empty?
        xi = IQ.signature_xi(obs)
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
        # Expert-domain judgement is available whenever the full biosignal profile
        # (the five modalities) is present — i.e. biosignal or tablet-derived mode.
        zmap = @obs.each_with_object({}) { |o, h| h[o[:modality]] = o[:z] }
        @expertise = if EXPERT_FEATURES.all? { |k| zmap.key?(k) }
                       IQ.expertise(zmap, iq, @xi)
                     end
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
          derived = t[:mode] == :derived
          lines << ""
          lines << if derived
                     "【0】赤外線+温度計 → 大脳基底核 熱エントロピー (ガンマ関数 多様体)"
                   else
                     "【0】赤外線センサー + 温度計 — ガンマ関数 大域的部分積分多様体"
                   end
          lines << format("   赤外線 皮膚温度   : %.2f ℃ (体表/体外)", t[:ir])
          lines << format("   温度計 環境温    : %.2f ℃", t[:temp])
          lines << format("   皮膚-環境勾配 Δ  : %+.2f ℃", t[:delta])
          if derived
            lines << format("   大脳基底核 熱H_bg: %.4f  (β(H+1,M+1)/log 4, 3点測度)", t[:xi_t])
          else
            lines << format("   多様体不変量 Ξ_T : %.4f  (β(H+1,M+1)/log 3)", t[:xi_t])
          end
        end

        lines << ""
        lines << if @meta[:thermal] && @meta[:thermal][:mode] == :derived
                   "【1】IQ 計測 — 赤外線/温度計から推定した生体信号(血液/DNA/fMRI/MRI/脳トポ)"
                 elsif @meta[:thermal]
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

        if @expertise
          e = @expertise
          lines << ""
          lines << "【5】ウィスパード エキスパート分野判定 — 個体識別能力から"
          lines << format("   個体識別能力 II  : %+.2f  (神経速度+機能統合+視覚構造)", e[:individuation])
          lines << format("   確信度(confidence): %.1f%%", 100.0 * e[:confidence])
          lines << "   分野分布:"
          e[:distribution].sort_by { |d| -d[:p] }.each do |d|
            bar = "█" * (d[:p] * 40).round
            lines << format("     %-26s %5.1f%% %s", "#{d[:ja]}(#{d[:en]})", 100.0 * d[:p], bar)
          end
          lines << ""
          lines << "   #{e[:phrase]}"
        end

        lines << ""
        lines << "───────────────────────────────────────────────────────────────"
        lines << format(" 総合判定 IQ ≈ %.0f  [ %s / %s ]",
                        iq, @verdict[:band_ja], @verdict[:band_en])
        lines << format(" 推定エキスパート分野: %s / %s", @expertise[:top_ja], @expertise[:top_en]) if @expertise
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

    # Thermal manifold invariant Ξ_T — computed by the Bada library
    # (thermal_invariant: the gamma-function global partial integral manifold).
    def thermal_invariant(ir, temp)
      vm.call("thermal_invariant", [ir.to_f, temp.to_f])
    end

    # Kind index for the Bada thermal_z: 0=gradient, 1=emissivity, 2=ratio.
    THERMAL_KIND = { gradient: 0.0, emissivity: 1.0, ratio: 2.0 }.freeze

    # The thermal sub-channel observations from one (ir, temp) reading; each z is
    # standardized and curved by the manifold gauge inside the Bada thermal_z.
    def thermal_channels(ir, temp)
      THERMAL_CHANNELS.map do |c|
        z = vm.call("thermal_z", [THERMAL_KIND[c[:kind]], ir.to_f, temp.to_f, c[:ref], c[:sd]])
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
        z = vm.call("thermal_z", [THERMAL_KIND[:gradient], sir.to_f, stemp.to_f, c[:ref], c[:sd]])
        obs << build_obs(:ir_gradient_t, "IR 勾配(時系列サンプル)", c[:rho], z)
      end
      xi = thermal_invariant(ir, temp)
      Assessment.new(obs, xi: xi, id: id,
                     meta: { thermal: { ir: ir.to_f, temp: temp.to_f, mode: :thermal,
                                        delta: ir.to_f - temp.to_f, xi_t: xi } })
    end

    # Thermal coupling coefficient — how strongly the basal-ganglia thermal
    # entropy predicts each biosignal modality (framework calibration constants).
    DERIVED_COUPLING = {
      fmri: 1.0,        # functional / metabolic — strongly thermal
      blood: 0.9,       # metabolic / BDNF / inflammation markers
      topography: 0.8,  # EEG neural conduction speed
      mri: 0.5,         # structural volume — weakly thermal
      dna: 0.3          # genetic — only indirectly thermal
    }.freeze

    # Estimate ALL five biosignal modalities (blood / DNA / fMRI / MRI /
    # topography) from just the tablet's infrared + thermometer, via the
    # basal-ganglia thermal entropy, then run the full biosignal assessment.
    def assess_thermal_derived(ir, temp, id: "TABLET-THERMAL")
      irf = ir.to_f
      tf = temp.to_f
      obs = MODALITIES.keys.map do |k|
        z = vm.call("derived_z", [DERIVED_COUPLING.fetch(k), irf, tf])
        m = MODALITIES[k]
        build_obs(k, "#{m[:label]} (推定)", m[:rho], z)
      end
      bg = vm.call("bg_thermal_entropy", [irf, tf])
      Assessment.new(obs, xi: bg, id: id,
                     meta: { thermal: { ir: irf, temp: tf, mode: :derived,
                                        delta: irf - tf, xi_t: bg } })
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
