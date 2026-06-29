# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestEngineCore < Minitest::Test
  def test_softmax_sums_to_one
    s = Bada::Engine.softmax([1.0, 2.0, 3.0])
    assert_in_delta 1.0, s.sum, 1e-12
    assert_operator s[2], :>, s[0]
  end

  def test_unknown_prior_is_uniform_max_entropy
    p = Bada::Engine.unknown_prior(4)
    assert_equal [0.25, 0.25, 0.25, 0.25], p
    # uniform over V maximises Shannon entropy at log2(V)
    assert_in_delta 2.0, Bada::Engine.entropy_of(p), 1e-12
  end

  # Theorem 2: the entropy-phase step changes no probability (|psi|^2 = a).
  def test_theorem_unitary_phase_step
    base = [0.5, 0.2, 0.3]
    mod = Bada::Engine::Module.new(name: "m", dist: [0.6, 0.1, 0.3], gain: 1.3)
    v = Bada::Engine.verify(base, [mod])
    assert_operator v[:max_prob_deviation], :<, 1e-12
    assert v[:unitary]
  end

  # Theorem 1: a confident zero can never be resurrected by any phase.
  def test_theorem_zero_preservation
    base = [0.5, 0.0, 0.5]
    mod = Bada::Engine::Module.new(name: "loud", dist: [0.1, 0.8, 0.1], gain: 5.0)
    r = Bada::Engine.cognitive_system(base, [mod])
    assert_in_delta 0.0, r[:posterior][1], 1e-15
    assert Bada::Engine.verify(base, [mod])[:zeros_preserved]
  end

  def test_inference_prior_sharpens_and_entropy_decreases
    inf = Bada::Engine::Inference.new(4)
    before = inf.entropy
    20.times { inf.observe(2) } # all evidence points at outcome 2
    assert_operator inf.entropy, :<, before
    assert_operator inf.estimate[2], :>, 0.5
    assert_equal 20, inf.total_observations
  end

  def test_inference_forbidden_never_gets_mass
    inf = Bada::Engine::Inference.new(3, forbidden: [1])
    assert_in_delta 0.0, inf.estimate[1], 1e-15
    assert_raises(RuntimeError) { inf.observe(1) }
    assert_equal [1], inf.forbidden
  end
end
