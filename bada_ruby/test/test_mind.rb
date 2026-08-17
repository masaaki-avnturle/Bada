# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestTransformerTensor < Minitest::Test
  T = Bada::Transformer::Tensor

  def test_matmul
    a = [[1.0, 2.0], [3.0, 4.0]]
    b = [[5.0, 6.0], [7.0, 8.0]]
    assert_equal [[19.0, 22.0], [43.0, 50.0]], T.matmul(a, b)
  end

  def test_softmax_sums_to_one
    s = T.softmax([1.0, 2.0, 3.0, -1.0])
    assert_in_delta 1.0, s.sum, 1e-12
    assert(s.all? { |v| v >= 0 })
  end

  def test_layernorm_zero_mean
    y = T.layernorm([1.0, 2.0, 3.0, 4.0])
    assert_in_delta 0.0, y.sum / y.length, 1e-9
  end

  def test_prng_is_deterministic
    a = Bada::Transformer::Tensor::PRNG.new(42)
    b = Bada::Transformer::Tensor::PRNG.new(42)
    assert_equal a.next_u64, b.next_u64
  end
end

class TestTransformerEncoder < Minitest::Test
  def setup
    @enc = Bada::Transformer::Encoder.new(vocab: 20, d_model: 16, n_heads: 4, n_blocks: 2, seed: 7)
  end

  def test_forward_shape
    h = @enc.forward([1, 2, 3, 4, 5])
    assert_equal 5, h.length
    assert_equal 16, h[0].length
  end

  def test_attention_rows_sum_to_one
    @enc.forward([1, 2, 3, 4])
    @enc.last_attention.each do |row|
      assert_in_delta 1.0, row.sum, 1e-6
    end
  end

  def test_deterministic
    a = Bada::Transformer::Encoder.new(vocab: 20, seed: 9).forward([1, 2, 3])
    b = Bada::Transformer::Encoder.new(vocab: 20, seed: 9).forward([1, 2, 3])
    assert_equal a, b
  end

  def test_logits_shape
    h = @enc.forward([1, 2, 3])
    lg = @enc.logits(h)
    assert_equal 3, lg.length
    assert_equal 20, lg[0].length
  end
end

class TestVision < Minitest::Test
  def test_process_reconstructs_grid_shape
    enc = Bada::Transformer::Encoder.new(vocab: 8, d_model: 16, seed: 3)
    vis = Bada::Transformer::Vision.new(encoder: enc, grid: 8, patch: 2, seed: 5)
    img = Array.new(8) { Array.new(8) { 0.5 } }
    out = vis.process(img)
    assert_equal 8, out.length
    assert_equal 8, out[0].length
    assert(out.flatten.all? { |v| v >= 0.0 && v <= 1.0 })
  end

  def test_ascii_dimensions
    grid = Array.new(4) { Array.new(4, 0.9) }
    ascii = Bada::Transformer::Vision.ascii(grid)
    assert_equal 4, ascii.lines.length
    assert_equal 4, ascii.lines.first.chomp.length
  end
end

class TestMindReader < Minitest::Test
  def setup
    @reader = Bada::Mind::Reader.new
  end

  def test_read_returns_all_parts
    r = @reader.read("光 と 音 の 記憶", subject: "X")
    refute_empty r[:verbalization]
    assert_equal 8, r[:mental_image].length
    assert_includes r[:source], "Omega::push"
    refute_empty r[:source_output]
    assert_operator r[:precision], :>=, 0.90
    assert_operator r[:precision], :<=, 0.995
  end

  def test_quantum_seed_bits_recorded
    r = @reader.read("光 音 波")
    assert_equal 4, r[:quantum_bits].length
    assert(r[:quantum_bits].all? { |b| [0, 1].include?(b) })
  end

  def test_generated_code_runs_in_bada_interpreter
    r = @reader.read("記憶 と 感情")
    # the "app in the mind" must actually execute (no interpreter error line)
    assert(r[:source_output].none? { |line| line.to_s.include?("interpreter error") })
    assert(r[:source_output].any? { |line| line.to_s.include?("Ω::push") })
  end

  def test_deterministic_for_same_signal
    a = @reader.read("静寂 の 中 の 光")[:verbalization]
    b = Bada::Mind::Reader.new.read("静寂 の 中 の 光")[:verbalization]
    assert_equal a, b
  end

  def test_empty_signal_is_handled
    r = @reader.read("")
    refute_empty r[:verbalization]
  end

  def test_exceeds_silent_talk_flag_matches_precision
    r = @reader.read("望み と 恐れ が 交錯 する 意志 の 光")
    assert_equal (r[:precision] > Bada::Mind::SILENT_TALK_BASELINE), r[:exceeds_silent_talk]
  end
end
