# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestQubit2 < Minitest::Test
  def test_bell_prep_matches_analytic_phi_plus
    prepared = Bada::Quantum::Qubit2.prepare_bell
    analytic = Bada::Quantum::Qubit2.bell_phi_plus
    prepared.amp.each_index do |i|
      assert_in_delta analytic.amp[i].real, prepared.amp[i].real, 1e-9
      assert_in_delta analytic.amp[i].imaginary, prepared.amp[i].imaginary, 1e-9
    end
  end

  def test_bell_state_is_normalised
    assert_in_delta 1.0, Bada::Quantum::Qubit2.prepare_bell.norm, 1e-9
  end

  def test_superdense_roundtrip_all_four_symbols
    [[0, 0], [0, 1], [1, 0], [1, 1]].each do |hi, lo|
      pair = Bada::Quantum::Qubit2.prepare_bell
      pair.encode(hi, lo).bell_decode
      assert_equal [hi, lo], pair.readout_bits, "symbol #{hi}#{lo} must round-trip"
    end
  end
end

class TestBell < Minitest::Test
  def test_quantum_chsh_reaches_tsirelson
    s = Bada::Quantum::Bell.chsh_quantum
    assert_in_delta 2.0 * Math.sqrt(2.0), s.abs, 1e-9
  end

  def test_local_model_respects_classical_bound
    s = Bada::Quantum::Bell.chsh_local(trials: 20_000, rng: Random.new(3))
    assert_operator s.abs, :<=, 2.0 + 0.05 # small Monte-Carlo slack
  end

  def test_spooky_action_certified
    e = Bada::Quantum::Bell.experiment(seed: 1)
    assert e[:violates_local_realism]
    assert e[:spooky_action_certified]
  end
end

class TestQuintic < Minitest::Test
  def test_fifth_roots_of_unity_sum_to_zero
    sum = Bada::Quantum::Quintic.roots_of_unity.reduce(Complex(0, 0), :+)
    assert_in_delta 0.0, sum.abs, 1e-9
  end

  def test_durand_kerner_solves_x5_minus_1
    roots = Bada::Quantum::Quintic.solve([0.0, 0.0, 0.0, 0.0, -1.0])
    roots.each do |r|
      assert_in_delta 0.0, (r**5 - 1).abs, 1e-6
    end
  end

  def test_period_is_two_pi_over_five
    assert_in_delta (2 * Math::PI / 5.0), Bada::Quantum::Quintic::PERIOD, 1e-12
  end
end

class TestJones < Minitest::Test
  def test_unknot_bracket_is_one
    b = Bada::Quantum::Jones.bracket([])
    assert_in_delta 1.0, b.eval(1.3), 1e-9
  end

  def test_hopf_bracket_is_minus_A4_minus_A_minus4
    b = Bada::Quantum::Jones.bracket(Bada::Quantum::Jones::HOPF)
    a = 1.7
    assert_in_delta(-(a**4) - (a**-4), b.eval(a), 1e-6)
  end

  def test_hopf_more_correlated_than_unlink
    corr = Bada::Quantum::Jones.correlation(Bada::Quantum::Jones::HOPF)
    assert_operator corr, :>, 0.1
  end
end

class TestUncertainty < Minitest::Test
  def test_robertson_relation_holds
    [[Math::PI / 3, Math::PI / 4], [Math::PI / 5, 1.0], [1.2, 0.3]].each do |th, ph|
      r = Bada::Quantum::Uncertainty.report(th, ph)
      assert r[:satisfied], "uncertainty must hold at θ=#{th}, φ=#{ph}"
      assert_operator r[:product], :>=, r[:bound] - 1e-9
    end
  end

  def test_born_probs_sum_to_one
    b = Bada::Quantum::Uncertainty.born_probs(0.7)
    assert_in_delta 1.0, b[:plus] + b[:minus], 1e-12
  end
end

class TestSemiconductor < Minitest::Test
  def test_fermi_dirac_half_at_mu
    assert_in_delta 0.5, Bada::Quantum::Semiconductor.fermi_dirac(1.0, 1.0, 300), 1e-12
  end

  def test_cold_gaas_is_feasible
    r = Bada::Quantum::Semiconductor.report(material: "GaAs", temp_k: 4.0)
    assert r[:feasible]
    assert_operator r[:bit_flip_prob], :<, 0.1
  end
end

class TestChannel < Minitest::Test
  def test_message_roundtrip_lossless_with_redundancy
    r = Bada::Quantum::Channel.transmit("BADA", material: "GaAs", temp_k: 4.0,
                                                redundancy: 5, seed: 7)
    assert_equal "BADA", r[:recovered]
    assert r[:lossless]
    assert_operator r[:certified_fidelity], :>, 0.9
  end

  def test_bits_roundtrip
    bits = Bada::Quantum::Channel.text_to_bits("Z")
    assert_equal "Z", Bada::Quantum::Channel.bits_to_text(bits)
  end
end

class TestSpaceTelegraph < Minitest::Test
  def test_prove_qed_true
    pf = Bada::Quantum::SpaceTelegraph.new.prove(seed: 1)
    assert pf[:qed], "all certificates must pass: #{pf[:certificates].inspect}"
  end

  def test_transmit_records_to_akashic
    tg = Bada::Quantum::SpaceTelegraph.new
    tg.transmit("HI")
    assert_equal 1, tg.db.size
  end

  def test_render_mentions_all_seven_pillars
    out = Bada::Quantum::SpaceTelegraph.new.render("OK")
    %w[ベル 5次方程式 Jones 不確定性 半導体 証明 電信通信].each do |kw|
      assert_includes out, kw
    end
  end
end
