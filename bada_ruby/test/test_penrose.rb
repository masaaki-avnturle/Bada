# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

include Bada::Penrose

class TestTensorEinsum < Minitest::Test
  def test_matrix_product
    a = Tensor.from_nested("A", [[1, 2], [3, 4]], %w[i k])
    b = Tensor.from_nested("B", [[5, 6], [7, 8]], %w[k j])
    r = Einsum.call([a, b], output: %w[i j])
    assert_equal [[19.0, 22.0], [43.0, 50.0]], r.to_nested
  end

  def test_trace
    a = Tensor.from_nested("A", [[1, 2], [3, 4]], %w[i i])
    assert_in_delta 5.0, Einsum.call([a], output: []).value, 1e-9
  end

  def test_dot_product
    v = Tensor.from_nested("v", [3, 4], %w[i])
    w = Tensor.from_nested("w", [3, 4], %w[i])
    assert_in_delta 25.0, Einsum.call([v, w], output: []).value, 1e-9
  end

  def test_outer_product
    v = Tensor.from_nested("v", [1, 2], %w[i])
    w = Tensor.from_nested("w", [3, 4], %w[j])
    r = Einsum.call([v, w], output: %w[i j])
    assert_equal [[3.0, 4.0], [6.0, 8.0]], r.to_nested
  end
end

class TestCanvas < Minitest::Test
  def test_parse_matrix_product
    d = Canvas.parse("i-[A]-[B]-j")
    assert_equal %w[A B], d.nodes.keys
    assert_equal 1, d.wires.length
    assert_equal 2, d.frees.length
    assert_match(/A_\{i k1\} B_\{k1 j\} → R_\{i j\}/, d.einsum_string)
  end

  def test_parse_and_compute
    d = Canvas.parse("i-[A]-[B]-j", values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] })
    e = Evaluator.evaluate(d)
    assert_equal [[19.0, 22.0], [43.0, 50.0]], e[:result]
  end

  def test_vertical_contraction
    drawing = "i-[A]\n   |\n  [B]-j"
    d = Canvas.parse(drawing, values: { "A" => [[1, 2], [3, 4]], "B" => [[1, 0], [0, 1]] })
    e = Evaluator.evaluate(d)
    # A_{i k} B_{j k} = A · Bᵀ = A · I = A
    assert_equal [[1.0, 2.0], [3.0, 4.0]], e[:result]
  end

  def test_integral_sums_index
    d = Canvas.parse("m-[A]\n(I m)", values: { "A" => [10, 20, 30] })
    e = Evaluator.evaluate(d)
    assert_in_delta 60.0, e[:scalar], 1e-9
  end

  def test_decorator_extraction
    d = Canvas.parse("i-[A]-j\nS{i j}")
    assert(d.decorators.any? { |x| x.type == :sym })
  end
end

class TestSymmetrize < Minitest::Test
  def test_symmetrize_result
    # A_{ij} symmetrised: 0.5(A + Aᵀ)
    d = Diagram.build do
      tensor "A", legs: 2, value: [[1, 2], [3, 4]]
      free ["A", 0], "i"
      free ["A", 1], "j"
      symmetrize "i", "j"
    end
    e = Evaluator.evaluate(d)
    assert_equal [[1.0, 2.5], [2.5, 4.0]], e[:result]
  end

  def test_antisymmetrize_result
    d = Diagram.build do
      tensor "A", legs: 2, value: [[1, 2], [3, 4]]
      free ["A", 0], "i"
      free ["A", 1], "j"
      antisymmetrize "i", "j"
    end
    e = Evaluator.evaluate(d)
    assert_equal [[0.0, -0.5], [0.5, 0.0]], e[:result]
  end
end

class TestPalette < Minitest::Test
  def test_palette_has_penrose_symbols
    s = Palette.render
    assert_match(/共変微分 ∇/, s)
    assert_match(/積分 ∫/, s)
    assert_match(/レヴィ・チヴィタ/, s)
  end
end

class TestDerivative < Minitest::Test
  def test_central_difference
    # f(x)=x^2 sampled at 0,1,2,3,4 (h=1) -> f'(x)=2x ; interior central diff exact
    f = [0, 1, 4, 9, 16]
    d = Evaluator.derivative_1d(f, h: 1.0)
    assert_in_delta 4.0, d[2], 1e-9 # f'(2)=4
    assert_in_delta 6.0, d[3], 1e-9 # f'(3)=6
  end
end

class TestStudioAndGenerators < Minitest::Test
  def setup
    @studio = Studio.new(seed: 1)
    @studio.draw("i-[A]-[B]-j", values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] })
  end

  def test_ask
    s = @studio.ask("これは何を計算している？")
    assert_match(/自動解答/, s)
    assert_match(/19/, s)
  end

  def test_paper_has_sections
    p = @studio.paper(question: "行列積の理論")
    assert_match(/要旨/, p)
    assert_match(/Einstein/, p)
    assert_match(/ミレニアム/, p)
    assert_match(/\$\$/, p) # LaTeX block
  end

  def test_generated_code_is_valid_ruby
    code = @studio.code
    assert_match(/Diagram\.build/, code)
    # must parse as valid Ruby
    assert RubyVM::InstructionSequence.compile(code)
  end

  def test_chat_penrose_integration
    chat = Bada::OmegaChat.new
    out = chat.penrose("i-[A]-[B]-j",
                       values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] },
                       question: "行列積")
    assert_match(/自動計算/, out)
    assert_match(/論文/, out)
    assert_match(/ソースコード/, out)
  end
end
