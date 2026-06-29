# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestReviser < Minitest::Test
  def test_rules_commit_as_append_only_facts
    ledger = Bada::Reviser::RuleLedger.new
    Bada::Reviser.parse_and_commit(<<~G, ledger)
      rule "measure" stmt [ 'Measure' '(' expr ')' ] => commit_measurement(_1)
    G
    assert_equal 1, ledger.size
    assert_equal 1, ledger.db.size # committed to Omega::DATABASE[grammar]
    rule = ledger.rules_for(:stmt).first
    assert_equal "measure", rule.name
    assert_equal "commit_measurement(reg)", rule.elaborate(["reg"])
  end

  def test_priority_latest_wins_but_history_kept
    ledger = Bada::Reviser::RuleLedger.new
    ledger.commit(name: "a", head: :stmt, pattern: [{ lit: "X" }], denotation: "old")
    ledger.commit(name: "b", head: :stmt, pattern: [{ lit: "X" }], denotation: "new")
    rules = ledger.rules_for(:stmt)
    assert_equal "new", rules.first.denotation # latest priority first
    assert_equal 2, ledger.size                # earlier fact still present
  end

  def test_interpreter_learns_quantum_sublanguage
    src = <<~BADA
      @reviser : grammar {
        rule "qubit_n"  expr    [ 'qubit' '(' expr ')' ]   => qubit(_1)
        rule "hadamard" postfix [ 'H' '(' expr ')' ]       => phase_uniform(_1)
        rule "measure"  stmt    [ 'Measure' '(' expr ')' ] => commit_measurement(_1)
      }
      reg := qubit(1)
      reg := H(reg)
      Measure(reg)
    BADA
    interp = Bada::Interpreter.new
    out = interp.run(src)
    assert_equal 3, interp.rules.size
    assert(out.any? { |l| l.include?("learned rule 'hadamard'") })
    assert(out.any? { |l| l.include?("Measure ->") && l.include?("0.50000") })
  end

  def test_unlearned_syntax_is_a_syntax_error
    # without the reviser block, Measure(...) is not in the grammar.
    interp = Bada::Interpreter.new
    assert_raises(RuntimeError) { interp.run("Measure(reg)\n") }
  end
end
