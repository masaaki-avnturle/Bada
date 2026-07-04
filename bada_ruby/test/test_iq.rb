# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestSpecialGaussian < Minitest::Test
  def test_erf_known_values
    assert_in_delta 0.0, Bada::Special.erf(0.0), 1e-6
    assert_in_delta 0.8427007, Bada::Special.erf(1.0), 1e-5
    assert_in_delta(-0.8427007, Bada::Special.erf(-1.0), 1e-5)
  end

  def test_normal_cdf
    assert_in_delta 0.5, Bada::Special.normal_cdf(100.0, mean: 100.0, sd: 15.0), 1e-6
    # ~97.7% below +2σ
    assert_in_delta 0.9772, Bada::Special.normal_cdf(130.0, mean: 100.0, sd: 15.0), 1e-3
  end

  def test_normal_cdf_degenerate_sd
    assert_equal 1.0, Bada::Special.normal_cdf(5.0, mean: 3.0, sd: 0.0)
    assert_equal 0.0, Bada::Special.normal_cdf(1.0, mean: 3.0, sd: 0.0)
  end
end

class TestIQObserve < Minitest::Test
  def test_zero_z_reads_population_mean
    o = Bada::IQ.observe(:fmri, 0.0)
    assert_in_delta 100.0, o[:estimate], 1e-9
    assert_operator o[:sigma], :>, 0.0
  end

  def test_higher_reliability_is_more_precise
    # fMRI (ρ=0.42) must be a tighter readout than blood (ρ=0.20) at the same z.
    fmri = Bada::IQ.observe(:fmri, 1.0)
    blood = Bada::IQ.observe(:blood, 1.0)
    assert_operator fmri[:sigma], :<, blood[:sigma]
  end

  def test_positive_z_raises_estimate
    assert_operator Bada::IQ.observe(:mri, 2.0)[:estimate], :>, 100.0
    assert_operator Bada::IQ.observe(:mri, -2.0)[:estimate], :<, 100.0
  end

  def test_observations_skips_missing
    obs = Bada::IQ.observations(fmri: 1.0, dna: -0.5)
    assert_equal %i[fmri dna], obs.map { |o| o[:modality] }
  end
end

class TestIQMirror < Minitest::Test
  def test_symmetric_sample_scores_high
    m = Bada::IQ.mirror_stats([90.0, 100.0, 110.0])
    assert_in_delta 100.0, m[:pivot], 1e-9
    assert_in_delta 1.0, m[:symmetry], 1e-9        # mean == pivot
    assert_in_delta 0.0, m[:asymmetry], 1e-9
  end

  def test_skewed_sample_is_asymmetric
    m = Bada::IQ.mirror_stats([100.0, 101.0, 102.0, 140.0])
    assert_operator m[:asymmetry], :>, 0.0          # mean pulled right of median
    assert_operator m[:symmetry], :<, 1.0
  end

  def test_empty_sample
    m = Bada::IQ.mirror_stats([])
    assert_equal 0, m[:n]
  end
end

class TestIQBayes < Minitest::Test
  def test_no_evidence_returns_prior
    p = Bada::IQ.bayes([])
    assert_in_delta 100.0, p[:posterior_mean], 1e-9
    assert_in_delta 15.0, p[:posterior_sd], 1e-9
  end

  def test_evidence_shrinks_posterior_sd
    obs = Bada::IQ.observations(fmri: 2.0, mri: 2.0, topography: 2.0)
    p = Bada::IQ.bayes(obs)
    assert_operator p[:posterior_sd], :<, 15.0       # information gained
    assert_operator p[:posterior_mean], :>, 100.0    # high biosignals raise IQ
    assert_operator p[:bits_gained], :>, 0.0
  end

  def test_credible_interval_brackets_mean
    obs = Bada::IQ.observations(fmri: 1.0)
    p = Bada::IQ.bayes(obs)
    lo, hi = p[:ci95]
    assert_operator lo, :<, p[:posterior_mean]
    assert_operator hi, :>, p[:posterior_mean]
  end

  def test_band_probabilities_sum_to_one
    total = Bada::IQ.band_probabilities(115.0, 10.0).sum { |b| b[:p] }
    assert_in_delta 1.0, total, 1e-6
  end
end

class TestIQWhispered < Minitest::Test
  def test_verdict_picks_a_band
    v = Bada::IQ.whispered(132.0, 8.0, xi_gate: 1.0)
    assert_equal "非常に優秀", v[:band_ja]
    assert_operator v[:confidence], :>=, 0.0
    assert_operator v[:confidence], :<=, 1.0
    assert_includes v[:phrase], "囁"
  end

  def test_narrow_posterior_is_more_confident
    sharp = Bada::IQ.whispered(100.0, 3.0, xi_gate: 1.0)[:confidence]
    diffuse = Bada::IQ.whispered(100.0, 25.0, xi_gate: 1.0)[:confidence]
    assert_operator sharp, :>, diffuse
  end
end

class TestIQAssessment < Minitest::Test
  def test_full_pipeline_report
    a = Bada::IQ.assess(Bada::IQ.demo_subject)
    assert_operator a.iq, :>, 100.0                  # above-average demo profile
    assert a.xi.finite?
    r = a.report
    assert_includes r, "ミラー統計"
    assert_includes r, "ベイズ推定"
    assert_includes r, "ウィスパード判定器"
    assert_includes r, "総合判定"
  end

  def test_requires_at_least_one_reading
    assert_raises(ArgumentError) { Bada::IQ.assess(id: "empty") }
  end

  def test_low_profile_lands_below_average
    a = Bada::IQ.assess(fmri: -2.0, mri: -2.0, topography: -2.0, dna: -1.5)
    assert_operator a.iq, :<, 100.0
  end
end
