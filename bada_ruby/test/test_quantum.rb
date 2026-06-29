# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestQuantum < Minitest::Test
  # A Hadamard on |0> yields equal probabilities with |psi|^2 = a to ~1e-16.
  def test_hadamard_uniform_superposition
    reg = Bada::Quantum.qubit(1)
    reg.h(0)
    p = reg.probabilities
    assert_in_delta 0.5, p[0], 1e-12
    assert_in_delta 0.5, p[1], 1e-12
    assert_in_delta 1.0, p.sum, 1e-12 # |psi|^2 == a (unitary)
  end

  # A pure-phase gate (Z) preserves a confident zero (no-resurrection).
  def test_phase_step_preserves_forbidden_zero
    reg = Bada::Quantum.qubit(2)
    reg.h(0)             # superpose -> states |00>,|01>; |10>,|11> stay zero
    before = reg.probabilities
    reg.z(0)             # pure phase
    after = reg.probabilities
    assert_in_delta 0.0, after[2], 1e-15
    assert_in_delta 0.0, after[3], 1e-15
    before.each_index { |i| assert_in_delta before[i], after[i], 1e-12 }
  end

  def test_cnot_entangles
    reg = Bada::Quantum.qubit(2)
    reg.h(0)             # (|00> + |01>)/√2   (qubit 0 is the low bit)
    reg.cnot(0, 1)       # control=0, target=1 -> (|00> + |11>)/√2 (Bell state)
    p = reg.probabilities
    assert_in_delta 0.5, p[0], 1e-12 # |00>
    assert_in_delta 0.5, p[3], 1e-12 # |11>
    assert_in_delta 0.0, p[1], 1e-12
    assert_in_delta 0.0, p[2], 1e-12
  end

  def test_measure_commits_to_ledger
    db = Bada::TupleSpace.new
    reg = Bada::Quantum.qubit(1)
    reg.h(0)
    r = Bada::Quantum.measure(reg, ledger: db)
    assert_equal 1, db.size
    assert_in_delta 1.0, r[:norm], 1e-12
    assert_equal 1, r[:committed]
  end

  def test_tomography_from_unknown_prior
    qi = Bada::Quantum::Inference.new(1, seed: 7).prepare_unknown
    reg = Bada::Quantum.qubit(1)
    reg.h(0)
    start_h = qi.entropy
    qi.observe_many(reg, shots: 300)
    est = qi.estimate
    assert_in_delta 0.5, est[0], 0.15
    assert_operator qi.entropy, :<=, start_h + 1e-9
  end
end
