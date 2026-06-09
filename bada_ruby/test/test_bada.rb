# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestSpecial < Minitest::Test
  def test_gamma_integers
    assert_in_delta 1.0, Bada::Special.gamma(1), 1e-6
    assert_in_delta 1.0, Bada::Special.gamma(2), 1e-6
    assert_in_delta 24.0, Bada::Special.gamma(5), 1e-4 # 4!
  end

  def test_gamma_half
    assert_in_delta Math.sqrt(Math::PI), Bada::Special.gamma(0.5), 1e-6
  end

  def test_beta_identity
    # B(2,3) = 1!2!/4! = 2/24 = 1/12
    assert_in_delta 1.0 / 12.0, Bada::Special.beta(2, 3), 1e-6
  end

  def test_box_dalanversian_equals_x_pow_x
    # box_dal = cos(ix log x) - i sin(ix log x) = e^{x log x} = x^x
    z = Bada::Special.box_dalanversian(2.0)
    assert_in_delta 2.0**2.0, z.abs, 1e-6 # 2^2 = 4
    assert_in_delta 0.0, z.imaginary, 1e-6 # it is real
  end

  def test_unit_rotation_preserves_magnitude
    # the error corrector relies on e^{iθ} being magnitude-preserving
    assert_in_delta 5.0, Bada::ErrorCorrection.rotate(5.0, 1.234), 1e-9
  end
end

class TestEntropy < Minitest::Test
  def test_uniform_two_tokens
    assert_in_delta 1.0, Bada::Entropy.shannon(%w[a b]), 1e-9
  end

  def test_zero_for_single_token
    assert_in_delta 0.0, Bada::Entropy.shannon(%w[a a a]), 1e-9
  end

  def test_tokenize_mixed
    toks = Bada::Entropy.tokenize("gamma 関数 x2")
    assert_includes toks, "gamma"   # ASCII words stay grouped
    assert_includes toks, "関"       # CJK is per-character
    assert_includes toks, "数"
  end
end

class TestManifold < Minitest::Test
  def test_invariant_keys
    s = Bada::Manifold.invariant("global differential manifold entropy invariant")
    assert s.key?(:entropy)
    assert s.key?(:manifold_integral)
    assert s.key?(:invariant)
    assert s[:invariant].finite?
  end

  def test_xi_is_finite_and_positive
    xi = Bada::Manifold.xi("zeta function beta gamma manifold")
    assert xi.finite?
    assert xi.positive?
  end
end

class TestErrorCorrection < Minitest::Test
  def test_correct_damps_outlier
    res = Bada::ErrorCorrection.correct([3.0, 3.1, 2.9, 30.0])
    # corrected value should sit near the cluster, far from the outlier
    assert_operator res[:value], :<, 10.0
  end

  def test_invariant_conserved_under_rotation
    cert = Bada::ErrorCorrection.certify_invariant("entropy manifold rotation")
    assert cert[:conserved]
  end
end

class TestLanguage < Minitest::Test
  def test_interpreter_runs_demo
    src = <<~BADA
      set g = 2.5
      g <- "manifold entropy"
      g -< 3.0
      g >- g
      Omega::push g as node
      print g
    BADA
    interp = Bada::Interpreter.new
    out = interp.run(src)
    assert_equal 1, interp.db.size
    assert(out.any? { |l| l.include?("Ω::push") })
  end

  def test_node_operators_change_value
    n = Bada::BadaNode.new(1.0)
    n.left_act("hello").manifold_integral(2.0).right_act
    assert_equal 3, n.history.length
  end
end

class TestKnowledgeAndQA < Minitest::Test
  def setup
    @kb = Bada::Knowledge.new
    @kb.ingest(<<~TXT, source: "t")
      ζ(s) = β(p,q)/log x という方程式を示す。
      これは単純な繰り返し繰り返し繰り返しの文である。
      We propose a method and show the result on the global manifold.
    TXT
  end

  def test_ingest_measures_entropy
    refute @kb.empty?
    assert(@kb.sentences.all? { |s| s.entropy >= 0.0 })
  end

  def test_qa_low_entropy
    qa = Bada::QAEngine.new(@kb)
    ans = qa.answer("低エントロピーな記述はどこにあるか？")
    assert_includes ans, "低エントロピー"
  end

  def test_qa_entropy_target
    qa = Bada::QAEngine.new(@kb)
    ans = qa.answer("H=1.5 に近い文")
    assert_includes ans, "H="
  end
end

class TestGeneratorAndChat < Minitest::Test
  def test_generator_targets_entropy
    g = Bada::Generator.new(seed: 42)
    r = g.text(target_h: 3.0, length: 16)
    assert r[:text].is_a?(String)
    assert r[:entropy].finite?
  end

  def test_equation_and_theory
    g = Bada::Generator.new(seed: 1)
    assert g.equation(target_h: 3.0)[:equation].is_a?(String)
    assert g.theory(target_h: 3.5)[:theory].is_a?(String)
  end

  def test_chat_reply_structure
    chat = Bada::OmegaChat.new(seed: 7)
    chat.learn("ζ(s) = β(p,q)/log x。大域的部分積分多様体のエントロピー不変量。", source: "rep")
    r = chat.reply("このレポートから何ができるか？")
    assert r[:question_entropy].finite?
    assert r[:question_invariant].finite?
    assert r[:theory][:theory].is_a?(String)
    assert_operator chat.db.size, :>=, 2
  end
end
